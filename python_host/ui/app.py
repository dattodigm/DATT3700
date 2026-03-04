"""
app.py — Flask control panel for DATT3700 interactive flower installation.

Layout:
  Left:  Live video stream preview with face detection overlay
  Right: Motor/LED sliders, 2D XY pad, Override switch, Tag & Save
"""

import json
import os
import threading
import time

from flask import Flask, render_template, Response, request, jsonify

from python_host.network.node_discovery import (
    discover_mdns_nodes,
    discover_nodes_via_gateway,
    infer_node_type,
    load_registry,
)
from python_host.network.osc_sender import OSCSender
from python_host.vision.face_tracker import FaceTracker

# ── Globals ──────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

tracker = FaceTracker(camera_index=0)
osc = OSCSender()
registry = load_registry()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAMPLES_FILE = os.path.join(DATA_DIR, "training_samples.jsonl")

_devices_lock = threading.Lock()
_devices = {}
_selected_device = None


def _device_label(device):
    known = registry.get("known_devices", {}).get(device["name"], {})
    if known.get("label"):
        return known["label"]
    node_meta = registry.get("node_types", {}).get(device.get("node_type", "unknown"), {})
    return node_meta.get("label", device["name"])


def _register_device(device):
    node_type = infer_node_type(device.get("name", ""), txt_node_type=device.get("node_type"), registry=registry)
    entry = {
        "name": device["name"],
        "ip": device["ip"],
        "port": int(device.get("port") or registry.get("default_osc_port", 8888)),
        "node_type": node_type,
        "source": device.get("source", "manual"),
        "metadata": device.get("metadata", {}),
    }
    entry["label"] = _device_label(entry)
    osc.add_target(entry["name"], entry["ip"], entry["port"])

    with _devices_lock:
        _devices[entry["name"]] = entry
    return entry


def _list_devices():
    with _devices_lock:
        return list(_devices.values())


def _selected_target(fallback=None):
    if fallback:
        return fallback
    with _devices_lock:
        return _selected_device


# ── Routes ───────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── Video streaming ──────────────────────────────────────────


def _generate_frames():
    while True:
        jpeg = tracker.get_frame_jpeg()
        if jpeg is None:
            time.sleep(0.03)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(
        _generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ── Face data API ────────────────────────────────────────────


@app.route("/api/faces")
def api_faces():
    target = tracker.get_primary_target()
    faces = tracker.get_all_faces()
    return jsonify({"primary": target, "faces": faces})


# ── Camera switching ─────────────────────────────────────────


@app.route("/api/cameras")
def api_cameras():
    return jsonify({"cameras": FaceTracker.list_cameras()})


@app.route("/api/camera/switch", methods=["POST"])
def api_camera_switch():
    idx = request.json.get("index", 0)
    tracker.switch_camera(int(idx))
    return jsonify({"status": "ok", "camera": idx})


# ── Device discovery & selection ─────────────────────────────


@app.route("/api/devices/registry")
def api_device_registry():
    return jsonify(registry)


@app.route("/api/devices")
def api_devices():
    return jsonify({"devices": _list_devices(), "selected": _selected_target()})


@app.route("/api/devices/select", methods=["POST"])
def api_devices_select():
    global _selected_device
    name = request.json.get("name")
    with _devices_lock:
        if name not in _devices:
            return jsonify({"status": "error", "message": "device not found"}), 404
        _selected_device = name
    return jsonify({"status": "ok", "selected": _selected_device})


@app.route("/api/devices/scan", methods=["POST"])
def api_devices_scan():
    global _selected_device

    data = request.json or {}
    mode = data.get("mode", "auto")
    timeout_sec = float(data.get("timeout", 1.2))
    gateway_ip = data.get("gateway_ip", "192.168.4.1")
    gateway_port = int(data.get("gateway_port", 8888))

    discovered = []
    if mode in ("mdns", "auto"):
        discovered.extend(discover_mdns_nodes(timeout_sec=timeout_sec, registry=registry))
    if mode in ("gateway", "auto"):
        discovered.extend(
            discover_nodes_via_gateway(
                osc_sender=osc,
                gateway_ip=gateway_ip,
                gateway_port=gateway_port,
                timeout_sec=min(timeout_sec, 0.8),
                registry=registry,
            )
        )

    merged = []
    seen = set()
    for item in discovered:
        key = (item.get("name"), item.get("ip"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(_register_device(item))

    if merged and _selected_device is None:
        _selected_device = merged[0]["name"]

    return jsonify(
        {
            "status": "ok",
            "mode": mode,
            "count": len(merged),
            "selected": _selected_target(),
            "devices": _list_devices(),
        }
    )


# ── OSC control endpoints ────────────────────────────────────


@app.route("/api/osc/targets")
def api_osc_targets():
    return jsonify(osc.list_targets())


@app.route("/api/osc/target", methods=["POST"])
def api_osc_add_target():
    data = request.json
    entry = _register_device(
        {
            "name": data["name"],
            "ip": data["ip"],
            "port": data.get("port", 8888),
            "node_type": data.get("node_type"),
            "source": "manual",
            "metadata": {},
        }
    )
    return jsonify({"status": "ok", "device": entry})


@app.route("/api/osc/raw", methods=["POST"])
def api_osc_raw():
    d = request.json or {}
    target = _selected_target(d.get("target"))
    address = d.get("address", "").strip()
    if not target:
        return jsonify({"status": "error", "message": "no selected target"}), 400
    if not address.startswith("/"):
        return jsonify({"status": "error", "message": "invalid OSC address"}), 400

    sent = osc.send_raw(target, address, d.get("args", []), source=d.get("source", "manual"))
    return jsonify({"status": "ok" if sent else "error", "target": target, "sent": bool(sent)})


@app.route("/api/osc/history")
def api_osc_history():
    limit = int(request.args.get("limit", 80))
    return jsonify({"items": osc.get_history(limit=limit)})


@app.route("/api/osc/motor", methods=["POST"])
def api_osc_motor():
    d = request.json
    target = _selected_target(d.get("target"))
    osc.send_motor(target, d["motor"], d["dir"], d.get("speed", 255), source="manual")
    return jsonify({"status": "ok"})


@app.route("/api/osc/led", methods=["POST"])
def api_osc_led():
    d = request.json
    target = _selected_target(d.get("target"))
    osc.send_led(target, d["led"], d["r"], d["g"], d["b"])
    return jsonify({"status": "ok"})


@app.route("/api/osc/preset", methods=["POST"])
def api_osc_preset():
    d = request.json
    target = _selected_target(d.get("target"))
    osc.send_preset(target, d["preset"])
    return jsonify({"status": "ok"})


@app.route("/api/osc/stop", methods=["POST"])
def api_osc_stop():
    d = request.json or {}
    target = _selected_target(d.get("target"))
    osc.stop_all(target)
    return jsonify({"status": "ok"})


# ── Override toggle ──────────────────────────────────────────


@app.route("/api/override", methods=["GET", "POST"])
def api_override():
    if request.method == "POST":
        osc.override = request.json.get("override", False)
    return jsonify({"override": osc.override})


# ── Tag & Save (data labeling) ───────────────────────────────


@app.route("/api/tag_save", methods=["POST"])
def api_tag_save():
    """Save current vision features + manual control params as a training sample."""
    d = request.json
    sample = {
        "timestamp": time.time(),
        "vision_features": d.get("vision_features", {}),
        "control_params": d.get("control_params", {}),
        "emotion_label": d.get("emotion_label", ""),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SAMPLES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")
    return jsonify({"status": "saved", "sample": sample})


# ── TFT eye animation stub ──────────────────────────────────


@app.route("/api/eye_animation", methods=["POST"])
def api_eye_animation():
    """Reserved endpoint for TFT IPS eye animation commands."""
    d = request.json
    target = _selected_target(d.get("target"))
    osc.send_eye_animation(target, d.get("animation_id", 0))
    return jsonify({"status": "stub_ok"})


# ── ML perception endpoints ─────────────────────────────────


@app.route("/api/perception/status")
def api_perception_status():
    """Check which perception modules are available."""
    modules = {"mediapipe": False, "deepface": False}
    try:
        import mediapipe  # noqa: F401
        modules["mediapipe"] = True
    except ImportError:
        pass
    try:
        from deepface import DeepFace  # noqa: F401
        modules["deepface"] = True
    except ImportError:
        pass
    return jsonify(modules)


# ── Entry point ──────────────────────────────────────────────


def create_app(camera_index=0, esp32_targets=None):
    """Factory for external callers / testing."""
    global tracker, _selected_device
    tracker = FaceTracker(camera_index=camera_index)
    if esp32_targets:
        for name, (ip, port) in esp32_targets.items():
            _register_device({"name": name, "ip": ip, "port": port, "source": "bootstrap"})
        _selected_device = next(iter(esp32_targets.keys()))
    return app


if __name__ == "__main__":
    tracker.start()
    _register_device({"name": "sylvie_1", "ip": "192.168.4.1", "port": 8888, "source": "default"})
    _selected_device = "sylvie_1"
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

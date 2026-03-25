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

from python_host.network.coordinate_publisher import CoordinatePublisher
from python_host.network.serial_sender import SerialCoordinateSender
from python_host.network.node_discovery import (
    discover_mdns_nodes,
    discover_nodes_via_gateway,
    infer_node_type,
    load_registry,
)
from python_host.network.osc_sender import OSCSender
from python_host.vision.face_tracker import FaceTracker
from python_host.vision.perception import PerceptionModule
from python_host.vision.emotion_reactor import EmotionReactor

# ── Globals ──────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

tracker = FaceTracker(camera_index=0)
osc = OSCSender()
serial_sender = SerialCoordinateSender()
registry = load_registry()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAMPLES_FILE = os.path.join(DATA_DIR, "training_samples.jsonl")
SEQUENCES_DIR = os.path.join(DATA_DIR, "sequences")

# Camera lifecycle state: keep camera disabled until user starts it.
_camera_lock = threading.Lock()
_camera_running = False
_camera_index = 0

_devices_lock = threading.Lock()
_devices = {}
_selected_device = None
_known_device_names = set(registry.get("known_devices", {}).keys())

CONTROL_MODE_TRACKING = "face_tracking"
CONTROL_MODE_EMOTION_MANUAL = "emotion_manual"
_control_mode_lock = threading.Lock()
_control_mode = CONTROL_MODE_TRACKING


def _jsonable(obj):
    """Convert numpy-heavy payloads into plain Python values for jsonify."""
    try:
        import numpy as np
    except Exception:
        np = None

    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v) for v in obj]
    if np is not None:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
    return str(obj)

tracking_publisher = CoordinatePublisher(
    get_primary_target=lambda: tracker.get_tracking_target(),
    get_selected_target=lambda: _selected_target(),
    get_selected_node_type=lambda: _selected_node_type(),
    osc_sender=osc,
    serial_sender=serial_sender,
)
perception = PerceptionModule()


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
    explicit_emotion_enabled = device.get("emotion_enabled")
    discovered = entry["source"] in ("mdns", "gateway_self", "gateway_client")
    default_emotion_enabled = discovered and (entry["name"] in _known_device_names)
    entry["label"] = _device_label(entry)
    osc.add_target(entry["name"], entry["ip"], entry["port"])

    with _devices_lock:
        prev = _devices.get(entry["name"])
        if explicit_emotion_enabled is None and prev is not None:
            entry["emotion_enabled"] = bool(prev.get("emotion_enabled", False))
        elif explicit_emotion_enabled is None:
            entry["emotion_enabled"] = bool(default_emotion_enabled)
        else:
            entry["emotion_enabled"] = bool(explicit_emotion_enabled)
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


def _selected_node_type():
    with _devices_lock:
        if _selected_device and _selected_device in _devices:
            return _devices[_selected_device].get("node_type", "unknown")
    return "unknown"


def _emotion_target_devices():
    with _devices_lock:
        items = []
        for dev in _devices.values():
            if not dev.get("emotion_enabled"):
                continue
            items.append(
                {
                    "name": dev.get("name"),
                    "ip": dev.get("ip"),
                    "port": dev.get("port"),
                    "node_type": dev.get("node_type", "unknown"),
                }
            )
    return items


emotion_reactor = EmotionReactor(
    osc_sender=osc,
    get_target_devices=lambda: _emotion_target_devices(),
)


def _set_control_mode(mode: str, *, sync_target=True):
    """Apply automation priority mode and keep target node state in sync."""
    global _control_mode
    candidate = str(mode or "").strip().lower()
    if candidate not in (CONTROL_MODE_TRACKING, CONTROL_MODE_EMOTION_MANUAL):
        candidate = CONTROL_MODE_TRACKING

    with _control_mode_lock:
        _control_mode = candidate

    if candidate == CONTROL_MODE_TRACKING:
        tracking_publisher.update_config(enabled=True)
        emotion_reactor.set_enabled(False)
        if sync_target:
            target = _selected_target()
            if target:
                osc.send_raw(target, "/track/mode", [1], source="manual")
                osc.send_raw(target, "/track/auto", [1], source="manual")
    else:
        tracking_publisher.update_config(enabled=False)
        emotion_reactor.set_enabled(True)
        if sync_target:
            target = _selected_target()
            if target:
                osc.send_raw(target, "/track/mode", [0], source="manual")
                osc.send_raw(target, "/track/auto", [0], source="manual")
    return _control_mode


def _get_control_mode():
    with _control_mode_lock:
        return _control_mode


def _safe_token(value, fallback):
    value = (value or "").strip()
    if not value:
        return fallback
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch in ("_", "-"):
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned) or fallback


def _sequence_path(label, name):
    safe_label = _safe_token(label, "unlabeled")
    safe_name = _safe_token(name, "sequence")
    folder = os.path.join(SEQUENCES_DIR, safe_label)
    return folder, os.path.join(folder, f"{safe_name}.json")


def _set_camera_index(index):
    global tracker, _camera_index
    _camera_index = int(index)
    tracker = FaceTracker(camera_index=_camera_index)


def _start_camera(index=None):
    global _camera_running
    with _camera_lock:
        if index is not None and int(index) != _camera_index:
            _set_camera_index(index)
        if _camera_running:
            return True, "already_running"
        try:
            tracker.start()
            perception.start(tracker)
            emotion_reactor.reset()
            _camera_running = True
            return True, "started"
        except RuntimeError as exc:
            perception.stop()
            _camera_running = False
            return False, str(exc)


def _stop_camera():
    global _camera_running
    with _camera_lock:
        if _camera_running:
            tracker.stop()
        perception.stop()
        emotion_reactor.reset()
        _camera_running = False


# ── Routes ───────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── Video streaming ──────────────────────────────────────────


def _generate_frames():
    while True:
        with _camera_lock:
            running = _camera_running
        if not running:
            break

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
    with _camera_lock:
        if not _camera_running:
            return ("", 204)
    return Response(
        _generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ── Face data API ────────────────────────────────────────────


@app.route("/api/faces")
def api_faces():
    with _camera_lock:
        running = _camera_running
    if not running:
        return jsonify(
            {
                "camera_running": False,
                "primary": None,
                "weighted": None,
                "faces": [],
                "perception": _jsonable(perception.get_results()),
                "reactor": emotion_reactor.snapshot(has_face=False),
            }
        )

    target = tracker.get_primary_target()
    weighted = tracker.get_weighted_target()
    faces = tracker.get_all_faces()
    has_face = bool(faces)
    perception_data = perception.get_results()
    reactor = emotion_reactor.update(perception_data, has_face=has_face)
    return jsonify(
        {
            "camera_running": True,
            "primary": _jsonable(target),
            "weighted": _jsonable(weighted),
            "faces": _jsonable(faces),
            "perception": _jsonable(perception_data),
            "reactor": _jsonable(reactor),
        }
    )


# ── Camera switching ─────────────────────────────────────────


@app.route("/api/cameras")
def api_cameras():
    return jsonify({"cameras": FaceTracker.list_cameras()})
    # """Return camera indices.
    #
    # By default this avoids probing hardware (which can wake camera on macOS).
    # Use /api/cameras?probe=1&max=2 when you explicitly want a scan.
    # """
    # probe = str(request.args.get("probe", "0")).lower() in ("1", "true", "yes")
    # if probe:
    #     max_check = int(request.args.get("max", 2))
    #     cameras = FaceTracker.list_cameras(max_check=max_check)
    #     return jsonify({"cameras": cameras})
    #
    # cameras = sorted(set([0, _camera_index]))
    # return jsonify({"cameras": cameras})


@app.route("/api/camera/state")
def api_camera_state():
    with _camera_lock:
        return jsonify({"running": _camera_running, "index": _camera_index})


@app.route("/api/camera/start", methods=["POST"])
def api_camera_start():
    payload = request.json or {}
    idx = int(payload.get("index", _camera_index))
    ok, detail = _start_camera(index=idx)
    code = 200 if ok else 500
    return jsonify({"status": "ok" if ok else "error", "running": ok, "index": _camera_index, "detail": detail}), code


@app.route("/api/camera/stop", methods=["POST"])
def api_camera_stop():
    _stop_camera()
    return jsonify({"status": "ok", "running": False, "index": _camera_index})


@app.route("/api/camera/switch", methods=["POST"])
def api_camera_switch():
    idx = int((request.json or {}).get("index", 0))
    with _camera_lock:
        was_running = _camera_running
    if was_running:
        _stop_camera()
        ok, detail = _start_camera(index=idx)
        code = 200 if ok else 500
        return jsonify({"status": "ok" if ok else "error", "camera": idx, "running": ok, "detail": detail}), code

    _set_camera_index(idx)
    return jsonify({"status": "ok", "camera": idx, "running": False})


# ── Device discovery & selection ─────────────────────────────


@app.route("/api/devices/registry")
def api_device_registry():
    return jsonify(registry)


@app.route("/api/devices")
def api_devices():
    with _devices_lock:
        emotion_targets = [name for name, dev in _devices.items() if dev.get("emotion_enabled")]
    return jsonify({"devices": _list_devices(), "selected": _selected_target(), "emotion_targets": emotion_targets})


@app.route("/api/devices/emotion_targets", methods=["GET", "POST"])
def api_devices_emotion_targets():
    if request.method == "POST":
        payload = request.json or {}
        names = payload.get("names", [])
        names = set([str(item) for item in names])
        with _devices_lock:
            for name, dev in _devices.items():
                dev["emotion_enabled"] = name in names

    with _devices_lock:
        enabled = [name for name, dev in _devices.items() if dev.get("emotion_enabled")]
        devices = list(_devices.values())
    return jsonify({"status": "ok", "names": enabled, "devices": devices})


@app.route("/api/devices/select", methods=["POST"])
def api_devices_select():
    global _selected_device
    name = request.json.get("name")
    with _devices_lock:
        if name not in _devices:
            return jsonify({"status": "error", "message": "device not found"}), 404
        _selected_device = name
    mode = _get_control_mode()
    if mode == CONTROL_MODE_TRACKING:
        osc.send_raw(_selected_device, "/track/mode", [1], source="manual")
        osc.send_raw(_selected_device, "/track/auto", [1], source="manual")
    else:
        osc.send_raw(_selected_device, "/track/mode", [0], source="manual")
        osc.send_raw(_selected_device, "/track/auto", [0], source="manual")
    return jsonify({"status": "ok", "selected": _selected_device})


def _scan_and_register_devices(mode="auto", timeout_sec=1.2, gateway_ip="192.168.4.1", gateway_port=8888):
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
    return merged


@app.route("/api/devices/scan", methods=["POST"])
def api_devices_scan():
    global _selected_device

    data = request.json or {}
    mode = data.get("mode", "auto")
    timeout_sec = float(data.get("timeout", 1.2))
    gateway_ip = data.get("gateway_ip", "192.168.4.1")
    gateway_port = int(data.get("gateway_port", 8888))

    merged = _scan_and_register_devices(
        mode=mode,
        timeout_sec=timeout_sec,
        gateway_ip=gateway_ip,
        gateway_port=gateway_port,
    )

    if merged and _selected_device is None:
        _selected_device = merged[0]["name"]

    return jsonify(
        {
            "status": "ok",
            "mode": mode,
            "count": len(merged),
            "selected": _selected_target(),
            "devices": _list_devices(),
            "emotion_targets": [d["name"] for d in _emotion_target_devices()],
        }
    )


@app.route("/api/discovery/mdns")
def api_discovery_mdns():
    merged = _scan_and_register_devices(mode="mdns")
    return jsonify({"status": "ok", "mode": "mdns", "count": len(merged), "devices": _list_devices(), "selected": _selected_target(), "emotion_targets": [d["name"] for d in _emotion_target_devices()]})


@app.route("/api/discovery/gateway", methods=["POST"])
def api_discovery_gateway():
    data = request.json or {}
    gateway_ip = data.get("gateway_ip") or data.get("ip") or "192.168.4.1"
    gateway_port = int(data.get("gateway_port") or data.get("port") or 8888)
    merged = _scan_and_register_devices(mode="gateway", gateway_ip=gateway_ip, gateway_port=gateway_port)
    return jsonify({"status": "ok", "mode": "gateway", "count": len(merged), "devices": _list_devices(), "selected": _selected_target(), "emotion_targets": [d["name"] for d in _emotion_target_devices()]})


@app.route("/api/discovery/auto", methods=["POST"])
def api_discovery_auto():
    merged = _scan_and_register_devices(mode="auto")
    return jsonify({"status": "ok", "mode": "auto", "count": len(merged), "devices": _list_devices(), "selected": _selected_target(), "emotion_targets": [d["name"] for d in _emotion_target_devices()]})

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


@app.route("/api/serial/ports")
def api_serial_ports():
    # Only enumerate ports when explicitly requested to avoid unnecessary serial probing.
    do_scan = str(request.args.get("scan", "0")).lower() in ("1", "true", "yes")
    ports = serial_sender.list_ports() if do_scan else []
    return jsonify({"ports": ports, "serial": serial_sender.status(), "scanned": do_scan})


@app.route("/api/serial/raw", methods=["POST"])
def api_serial_raw():
    payload = request.json or {}
    line = str(payload.get("line", "")).strip()
    if not line:
        return jsonify({"status": "error", "message": "empty command"}), 400

    sent = serial_sender.send_line(line)
    return jsonify({"status": "ok" if sent else "error", "sent": bool(sent), "serial": serial_sender.status()})


@app.route("/api/tracking/config", methods=["GET", "POST"])
def api_tracking_config():
    if request.method == "POST":
        payload = request.json or {}

        tracking_publisher.update_config(
            enabled=payload.get("enabled") if "enabled" in payload else None,
            transport=payload.get("transport") if "transport" in payload else None,
            rate_hz=payload.get("rate_hz") if "rate_hz" in payload else None,
            deadband=payload.get("deadband") if "deadband" in payload else None,
            frame_width=payload.get("frame_width") if "frame_width" in payload else None,
            frame_height=payload.get("frame_height") if "frame_height" in payload else None,
        )

        # Keep node-side auto mode aligned with panel toggle.
        if "enabled" in payload:
            target = _selected_target()
            if target:
                flag = 1 if payload.get("enabled") else 0
                osc.send_raw(target, "/track/auto", [flag], source="manual")
                osc.send_raw(target, "/track/mode", [flag], source="manual")

        serial_port = payload.get("serial_port") if "serial_port" in payload else None
        serial_baud = payload.get("serial_baud") if "serial_baud" in payload else None
        if serial_port is not None or serial_baud is not None:
            serial_sender.configure(port=serial_port, baud=serial_baud)

        if payload.get("serial_connect"):
            serial_sender.connect()
        if payload.get("serial_disconnect"):
            serial_sender.disconnect()

    return jsonify(
        {
            "status": "ok",
            "control_mode": _get_control_mode(),
            "tracking": tracking_publisher.snapshot(),
            "serial": serial_sender.status(),
            "selected_target": _selected_target(),
        }
    )


@app.route("/api/control/mode", methods=["GET", "POST"])
def api_control_mode():
    if request.method == "POST":
        payload = request.json or {}
        mode = payload.get("mode", CONTROL_MODE_TRACKING)
        applied = _set_control_mode(mode, sync_target=True)
        return jsonify(
            {
                "status": "ok",
                "mode": applied,
                "tracking": tracking_publisher.snapshot(),
                "reactor_enabled": emotion_reactor.is_enabled(),
                "selected_target": _selected_target(),
            }
        )

    return jsonify(
        {
            "status": "ok",
            "mode": _get_control_mode(),
            "tracking": tracking_publisher.snapshot(),
            "reactor_enabled": emotion_reactor.is_enabled(),
            "selected_target": _selected_target(),
        }
    )


@app.route("/api/reactor/config", methods=["GET", "POST"])
def api_reactor_config():
    if request.method == "POST":
        payload = request.json or {}
        config = emotion_reactor.update_config(payload)
        return jsonify({"status": "ok", "config": config})

    return jsonify({"status": "ok", "config": emotion_reactor.get_config()})


@app.route("/api/reactor/override", methods=["GET", "POST"])
def api_reactor_override():
    if request.method == "POST":
        payload = request.json or {}
        enabled = bool(payload.get("enabled", True))
        emotion_reactor.set_enabled(enabled)
    return jsonify({"status": "ok", "enabled": emotion_reactor.is_enabled()})


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


@app.route("/api/sequences/list")
def api_sequences_list():
    """List saved motion sequences grouped by label."""
    if not os.path.exists(SEQUENCES_DIR):
        return jsonify({"labels": {}, "items": []})

    labels = {}
    items = []
    for label in sorted(os.listdir(SEQUENCES_DIR)):
        label_dir = os.path.join(SEQUENCES_DIR, label)
        if not os.path.isdir(label_dir):
            continue
        names = []
        for fname in sorted(os.listdir(label_dir)):
            if not fname.endswith(".json"):
                continue
            name = os.path.splitext(fname)[0]
            names.append(name)
            items.append({"label": label, "name": name})
        labels[label] = names

    return jsonify({"labels": labels, "items": items})


@app.route("/api/sequences/load")
def api_sequences_load():
    label = request.args.get("label", "unlabeled")
    name = request.args.get("name", "sequence")
    folder, file_path = _sequence_path(label, name)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "sequence not found"}), 404

    with open(file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return jsonify({"status": "ok", "sequence": payload})


@app.route("/api/sequences/save", methods=["POST"])
def api_sequences_save():
    payload = request.json or {}
    label = payload.get("label", "unlabeled")
    name = payload.get("name", "sequence")
    node_type = payload.get("node_type", "unknown")
    events = payload.get("events", [])

    folder, file_path = _sequence_path(label, name)
    os.makedirs(folder, exist_ok=True)

    data = {
        "label": label,
        "name": name,
        "node_type": node_type,
        "created_at": time.time(),
        "events": events,
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)

    return jsonify({"status": "ok", "path": file_path})


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
    modules = {"mediapipe": False, "deepface": False, "vit": False}
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
    try:
        from python_host.vision.vit_emotion import ViTEmotionDetector  # noqa: F401
        modules["vit"] = True
    except ImportError:
        pass
    return jsonify(modules)


# ── Entry point ──────────────────────────────────────────────


def create_app(camera_index=0, esp32_targets=None):
    """Factory for external callers / testing."""
    global tracker, _selected_device, _camera_index, _camera_running
    tracker = FaceTracker(camera_index=camera_index)
    _camera_index = int(camera_index)
    _camera_running = False
    perception.stop()
    emotion_reactor.reset()
    tracking_publisher.update_config(enabled=False, transport="osc")
    _set_control_mode(CONTROL_MODE_EMOTION_MANUAL, sync_target=False)
    serial_sender.disconnect()
    if esp32_targets:
        for name, (ip, port) in esp32_targets.items():
            _register_device({"name": name, "ip": ip, "port": port, "source": "bootstrap"})
        _selected_device = next(iter(esp32_targets.keys()))
    return app


if __name__ == "__main__":
    _register_device({"name": "sylvie_1", "ip": "192.168.4.1", "port": 8888, "source": "default"})
    _selected_device = "sylvie_1"
    _set_control_mode(CONTROL_MODE_EMOTION_MANUAL, sync_target=False)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

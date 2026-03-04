"""
app.py — Flask control panel for DATT3700 interactive flower installation.

Layout:
  Left:  Live video stream preview with face detection overlay
  Right: Motor/LED sliders, 2D XY pad, Override switch, Tag & Save
"""

import json
import os
import time

from flask import Flask, render_template, Response, request, jsonify

from python_host.vision.face_tracker import FaceTracker
from python_host.network.osc_sender import OSCSender

# ── Globals ──────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

tracker = FaceTracker(camera_index=0)
osc = OSCSender()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SAMPLES_FILE = os.path.join(DATA_DIR, "training_samples.jsonl")

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


# ── OSC control endpoints ────────────────────────────────────


@app.route("/api/osc/targets")
def api_osc_targets():
    return jsonify(osc.list_targets())


@app.route("/api/osc/target", methods=["POST"])
def api_osc_add_target():
    data = request.json
    osc.add_target(data["name"], data["ip"], data.get("port", 8888))
    return jsonify({"status": "ok"})


@app.route("/api/osc/motor", methods=["POST"])
def api_osc_motor():
    d = request.json
    osc.send_motor(
        d["target"], d["motor"], d["dir"], d.get("speed", 255), source="manual"
    )
    return jsonify({"status": "ok"})


@app.route("/api/osc/led", methods=["POST"])
def api_osc_led():
    d = request.json
    osc.send_led(d["target"], d["led"], d["r"], d["g"], d["b"])
    return jsonify({"status": "ok"})


@app.route("/api/osc/preset", methods=["POST"])
def api_osc_preset():
    d = request.json
    osc.send_preset(d["target"], d["preset"])
    return jsonify({"status": "ok"})


@app.route("/api/osc/stop", methods=["POST"])
def api_osc_stop():
    d = request.json
    osc.stop_all(d["target"])
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
    with open(SAMPLES_FILE, "a") as f:
        f.write(json.dumps(sample) + "\n")
    return jsonify({"status": "saved", "sample": sample})


# ── TFT eye animation stub ──────────────────────────────────


@app.route("/api/eye_animation", methods=["POST"])
def api_eye_animation():
    """Reserved endpoint for TFT IPS eye animation commands."""
    d = request.json
    osc.send_eye_animation(d.get("target"), d.get("animation_id", 0))
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
    global tracker
    tracker = FaceTracker(camera_index=camera_index)
    if esp32_targets:
        for name, (ip, port) in esp32_targets.items():
            osc.add_target(name, ip, port)
    return app


if __name__ == "__main__":
    tracker.start()
    osc.add_target("sylvie_1", "192.168.4.1", 8888)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

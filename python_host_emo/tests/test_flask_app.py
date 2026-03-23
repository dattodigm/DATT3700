"""Tests for the Flask control panel API endpoints."""
import json
import pytest
from python_host.ui.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestFlaskAPI:
    """Test Flask API endpoints without camera or ESP32."""

    def test_index(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"DATT3700" in resp.data

    def test_api_faces_no_camera(self, client):
        resp = client.get("/api/faces")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "primary" in data
        assert "faces" in data

    def test_api_override_get(self, client):
        resp = client.get("/api/override")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "override" in data

    def test_api_override_post(self, client):
        resp = client.post(
            "/api/override",
            data=json.dumps({"override": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["override"] is True

    def test_api_osc_add_target(self, client):
        resp = client.post(
            "/api/osc/target",
            data=json.dumps({"name": "test", "ip": "127.0.0.1", "port": 8888}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_api_osc_motor(self, client):
        # Add target first
        client.post(
            "/api/osc/target",
            data=json.dumps({"name": "test", "ip": "127.0.0.1", "port": 8888}),
            content_type="application/json",
        )
        resp = client.post(
            "/api/osc/motor",
            data=json.dumps({"target": "test", "motor": 1, "dir": 1, "speed": 128}),
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_api_tag_save(self, client, tmp_path):
        """Test tag & save creates JSONL entry."""
        import python_host.ui.app as app_module
        original_dir = app_module.DATA_DIR
        app_module.DATA_DIR = str(tmp_path)
        app_module.SAMPLES_FILE = str(tmp_path / "test_samples.jsonl")

        resp = client.post(
            "/api/tag_save",
            data=json.dumps({
                "vision_features": {"faces": []},
                "control_params": {"motor1": {"dir": 1, "speed": 128}},
                "emotion_label": "happy",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "saved"

        # Restore
        app_module.DATA_DIR = original_dir

    def test_api_perception_status(self, client):
        resp = client.get("/api/perception/status")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "mediapipe" in data
        assert "deepface" in data

    def test_api_eye_animation_stub(self, client):
        resp = client.post(
            "/api/eye_animation",
            data=json.dumps({"target": "test", "animation_id": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "stub_ok"

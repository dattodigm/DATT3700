"""Tests for the Flask control panel API endpoints."""
import json

import pytest

import python_host.ui.app as app_module
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
        original_dir = app_module.DATA_DIR
        original_samples = app_module.SAMPLES_FILE
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
        app_module.SAMPLES_FILE = original_samples

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

    def test_api_registry_and_devices(self, client):
        reg = client.get("/api/devices/registry")
        assert reg.status_code == 200
        reg_data = json.loads(reg.data)
        assert "node_types" in reg_data

        devices = client.get("/api/devices")
        assert devices.status_code == 200
        data = json.loads(devices.data)
        assert "devices" in data

    def test_api_scan_mdns_with_mock(self, client, monkeypatch):
        monkeypatch.setattr(
            app_module,
            "discover_mdns_nodes",
            lambda timeout_sec, registry: [
                {
                    "name": "F7OWER_00",
                    "ip": "192.168.4.1",
                    "port": 8888,
                    "node_type": "sylvie",
                    "source": "mdns",
                    "metadata": {},
                }
            ],
        )
        monkeypatch.setattr(app_module, "discover_nodes_via_gateway", lambda **kwargs: [])

        resp = client.post(
            "/api/devices/scan",
            data=json.dumps({"mode": "mdns"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        payload = json.loads(resp.data)
        assert payload["count"] >= 1
        assert any(d["name"] == "F7OWER_00" for d in payload["devices"])

    def test_api_select_and_raw(self, client):
        client.post(
            "/api/osc/target",
            data=json.dumps({"name": "raw_test", "ip": "127.0.0.1", "port": 8888}),
            content_type="application/json",
        )
        sel = client.post(
            "/api/devices/select",
            data=json.dumps({"name": "raw_test"}),
            content_type="application/json",
        )
        assert sel.status_code == 200

        raw = client.post(
            "/api/osc/raw",
            data=json.dumps({"address": "/state", "args": ["relax"]}),
            content_type="application/json",
        )
        assert raw.status_code == 200
        raw_data = json.loads(raw.data)
        assert raw_data["target"] == "raw_test"

        history = client.get("/api/osc/history")
        assert history.status_code == 200
        hist_data = json.loads(history.data)
        assert "items" in hist_data

    def test_api_camera_state(self, client):
        resp = client.get("/api/camera/state")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "running" in data
        assert "index" in data

    def test_api_camera_start_stop_mocked(self, client, monkeypatch):
        monkeypatch.setattr(app_module, "_start_camera", lambda index=None: (True, "started"))
        monkeypatch.setattr(app_module, "_stop_camera", lambda: None)

        start = client.post(
            "/api/camera/start",
            data=json.dumps({"index": 0}),
            content_type="application/json",
        )
        assert start.status_code == 200

        stop = client.post(
            "/api/camera/stop",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert stop.status_code == 200

    def test_api_sequences_save_list_load(self, client, tmp_path, monkeypatch):
        original_dir = app_module.SEQUENCES_DIR
        monkeypatch.setattr(app_module, "SEQUENCES_DIR", str(tmp_path))

        payload = {
            "label": "calm",
            "name": "demo",
            "node_type": "sylvie",
            "events": [{"t": 0.0, "address": "/auto", "args": [0]}],
        }
        resp = client.post(
            "/api/sequences/save",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200

        listing = client.get("/api/sequences/list")
        assert listing.status_code == 200
        listing_data = json.loads(listing.data)
        assert "calm" in listing_data.get("labels", {})

        loaded = client.get("/api/sequences/load?label=calm&name=demo")
        assert loaded.status_code == 200
        loaded_data = json.loads(loaded.data)
        assert loaded_data["sequence"]["name"] == "demo"

        monkeypatch.setattr(app_module, "SEQUENCES_DIR", original_dir)

    def test_api_tracking_config_get(self, client):
        resp = client.get("/api/tracking/config")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert "tracking" in data
        assert "serial" in data

    def test_api_tracking_config_post(self, client):
        resp = client.post(
            "/api/tracking/config",
            data=json.dumps({"enabled": True, "transport": "osc", "rate_hz": 15}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["tracking"]["enabled"] is True
        assert data["tracking"]["transport"] == "osc"

    def test_api_serial_ports(self, client):
        resp = client.get("/api/serial/ports")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "ports" in data
        assert "serial" in data

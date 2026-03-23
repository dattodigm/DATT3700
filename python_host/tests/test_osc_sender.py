"""Tests for the OSC sender module."""
from unittest.mock import MagicMock

from python_host.network.osc_sender import OSCSender


class TestOSCSender:
    """Test OSC sender logic without network access."""

    def test_add_and_list_targets(self):
        sender = OSCSender()
        sender.add_target("test", "127.0.0.1", 8888)
        targets = sender.list_targets()
        assert "test" in targets

    def test_remove_target(self):
        sender = OSCSender()
        sender.add_target("test", "127.0.0.1", 8888)
        sender.remove_target("test")
        targets = sender.list_targets()
        assert "test" not in targets

    def test_override_blocks_auto(self):
        sender = OSCSender()
        sender.add_target("test", "127.0.0.1", 8888)
        sender.override = True

        # Mock the internal client to track calls
        mock_client = MagicMock()
        sender._clients["test"] = mock_client

        sent = sender.send("test", "/motor1", 1, 128, source="auto")
        mock_client.send_message.assert_not_called()
        assert sent is False

    def test_override_allows_manual(self):
        sender = OSCSender()
        sender.add_target("test", "127.0.0.1", 8888)
        sender.override = True

        mock_client = MagicMock()
        sender._clients["test"] = mock_client

        sent = sender.send("test", "/motor1", 1, 128, source="manual")
        mock_client.send_message.assert_called_once()
        assert sent is True

    def test_send_motor_formats_address(self):
        sender = OSCSender()
        mock_client = MagicMock()
        sender._clients["test"] = mock_client
        sender._target_info["test"] = ("127.0.0.1", 8888)

        sender.send_motor("test", 1, 1, 128, source="manual")
        mock_client.send_message.assert_called_once_with("/motor1", [1, 128])

    def test_send_to_nonexistent_target_silent(self):
        sender = OSCSender()
        # Should not raise
        sent = sender.send("nonexistent", "/motor1", 1, 128, source="manual")
        assert sent is False

    def test_stop_all_ignores_override(self):
        sender = OSCSender()
        sender.override = True
        mock_client = MagicMock()
        sender._clients["test"] = mock_client
        sender._target_info["test"] = ("127.0.0.1", 8888)

        sender.stop_all("test")
        mock_client.send_message.assert_called_once_with("/preset", [3])

    def test_send_raw_and_history(self):
        sender = OSCSender()
        mock_client = MagicMock()
        sender._clients["test"] = mock_client
        sender._target_info["test"] = ("127.0.0.1", 8888)

        sender.send_raw("test", "/state", ["relax"], source="manual")
        history = sender.get_history(limit=5)

        assert history
        assert history[-1]["address"] == "/state"
        assert history[-1]["args"] == ["relax"]

    def test_query_info_self_parsing(self):
        sender = OSCSender()
        sender._request_reply = MagicMock(
            return_value={
                "address": "/info/self",
                "args": ["F7OWER_00", "AA:BB", "AP", "192.168.4.1"],
                "ip": "192.168.4.1",
                "port": 8888,
            }
        )

        info = sender.query_info_self_ip("192.168.4.1", 8888)
        assert info["name"] == "F7OWER_00"
        assert info["mode"] == "AP"

    def test_query_info_clients_parsing(self):
        sender = OSCSender()
        sender._request_reply = MagicMock(
            return_value={
                "address": "/info/clients",
                "args": [2, "AA:BB", "192.168.4.2", "CC:DD", "192.168.4.3"],
                "ip": "192.168.4.1",
                "port": 8888,
            }
        )

        info = sender.query_info_clients_ip("192.168.4.1", 8888)
        assert info["count"] == 2
        assert len(info["clients"]) == 2
        assert info["clients"][0]["ip"] == "192.168.4.2"

    def test_eye_animation_stub(self):
        sender = OSCSender()
        # Should not raise
        sender.send_eye_animation("test", 0)

    def test_send_track_norm(self):
        sender = OSCSender()
        mock_client = MagicMock()
        sender._clients["test"] = mock_client
        sender._target_info["test"] = ("127.0.0.1", 8888)

        sender.send_track_norm("test", 0.25, 0.75, source="manual")
        mock_client.send_message.assert_called_once_with("/track/norm", [0.25, 0.75])

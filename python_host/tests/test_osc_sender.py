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

        sender.send("test", "/motor1", 1, 128, source="auto")
        mock_client.send_message.assert_not_called()

    def test_override_allows_manual(self):
        sender = OSCSender()
        sender.add_target("test", "127.0.0.1", 8888)
        sender.override = True

        mock_client = MagicMock()
        sender._clients["test"] = mock_client

        sender.send("test", "/motor1", 1, 128, source="manual")
        mock_client.send_message.assert_called_once()

    def test_send_motor_formats_address(self):
        sender = OSCSender()
        mock_client = MagicMock()
        sender._clients["test"] = mock_client

        sender.send_motor("test", 1, 1, 128, source="manual")
        mock_client.send_message.assert_called_once_with("/motor1", [1, 128])

    def test_send_to_nonexistent_target_silent(self):
        sender = OSCSender()
        # Should not raise
        sender.send("nonexistent", "/motor1", 1, 128, source="manual")

    def test_stop_all_ignores_override(self):
        sender = OSCSender()
        sender.override = True
        mock_client = MagicMock()
        sender._clients["test"] = mock_client

        sender.stop_all("test")
        mock_client.send_message.assert_called_once_with("/preset", [3])

    def test_eye_animation_stub(self):
        sender = OSCSender()
        # Should not raise
        sender.send_eye_animation("test", 0)

"""Tests for the perception module (lazy-loading, no hardware required)."""
from python_host.vision.perception import PerceptionModule


class TestPerceptionModule:
    """Test perception module initialization and graceful degradation."""

    def test_init_no_crash(self):
        pm = PerceptionModule()
        assert pm._running is False
        assert pm._results["emotion"] is None

    def test_get_results_empty(self):
        pm = PerceptionModule()
        results = pm.get_results()
        assert results["emotion"] is None
        assert results["pose"] is None
        assert results["face_analysis"] is None

    def test_lazy_load_mediapipe(self):
        """MediaPipe loading should not crash even if not installed."""
        pm = PerceptionModule()
        # This should return True or False without crashing
        result = pm._try_load_mediapipe()
        assert isinstance(result, bool)

    def test_lazy_load_deepface(self):
        """DeepFace loading should not crash even if not installed."""
        pm = PerceptionModule()
        result = pm._try_load_deepface()
        assert isinstance(result, bool)

    def test_stop_before_start(self):
        """Stopping before starting should not crash."""
        pm = PerceptionModule()
        pm.stop()  # Should not raise

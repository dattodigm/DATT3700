"""Tests for the face tracker weighted algorithm."""
import math


class TestWeightAlgorithm:
    """Test the weighted face selection logic without requiring a camera."""

    @staticmethod
    def compute_weight(x, y, fw, fh, frame_w=1280, frame_h=720):
        """Replicate the weight formula from FaceTracker._process_frame."""
        cx_frame = frame_w / 2.0
        cy_frame = frame_h / 2.0
        max_dist = math.hypot(cx_frame, cy_frame)

        area = fw * fh
        cx_face = x + fw / 2.0
        cy_face = y + fh / 2.0
        dist = math.hypot(cx_face - cx_frame, cy_face - cy_frame)
        proximity = 1.0 / (1.0 + dist / max_dist)
        return area * proximity

    def test_center_face_wins(self):
        """A centered face should have higher weight than a corner face of same size."""
        w_center = self.compute_weight(590, 310, 100, 100)
        w_corner = self.compute_weight(10, 10, 100, 100)
        assert w_center > w_corner

    def test_bigger_face_wins(self):
        """A larger face at same position should have higher weight."""
        w_big = self.compute_weight(540, 260, 200, 200)
        w_small = self.compute_weight(590, 310, 100, 100)
        assert w_big > w_small

    def test_normalized_coordinates(self):
        """Normalized coordinates should be in [0, 1]."""
        x, y, fw, fh = 100, 200, 150, 150
        frame_w, frame_h = 1280, 720
        norm_x = (x + fw / 2.0) / frame_w
        norm_y = (y + fh / 2.0) / frame_h
        assert 0.0 <= norm_x <= 1.0
        assert 0.0 <= norm_y <= 1.0

    def test_weight_positive(self):
        """Weight should always be positive for valid bounding boxes."""
        w = self.compute_weight(0, 0, 50, 50)
        assert w > 0

    def test_zero_area_gives_zero_weight(self):
        """A zero-area bounding box should produce zero weight."""
        w = self.compute_weight(100, 100, 0, 0)
        assert w == 0.0

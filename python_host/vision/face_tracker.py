"""
face_tracker.py — Weighted multi-face tracking with multi-camera support.

Selects the primary target using:
    weight = bbox_area × (1 / (1 + center_distance))

Outputs only the primary target's normalized coordinates (0.0-1.0).
No heavy ML dependencies — uses only OpenCV Haar Cascade.
"""

import cv2
import math
import threading
import time
import sys


class FaceTracker:
    """Lightweight face tracker with weighted target selection."""

    def __init__(self, camera_index=0, frame_width=1280, frame_height=720):
        self._camera_index = camera_index
        self._frame_width = frame_width
        self._frame_height = frame_height

        self._cap = None
        self._cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self._lock = threading.Lock()
        self._latest_frame = None
        self._primary_target = None  # (norm_x, norm_y, weight)
        self._all_faces = []
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Open camera and begin capture thread."""
        backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(self._camera_index, backend)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._frame_height)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self._camera_index}")
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Release camera resources."""
        self._running = False
        if self._cap:
            self._cap.release()
            self._cap = None

    def switch_camera(self, camera_index):
        """Hot-switch to another camera (e.g. iPhone Continuity Camera)."""
        self.stop()
        self._camera_index = camera_index
        self.start()

    def get_primary_target(self):
        """Return (norm_x, norm_y, weight) of highest-weight face or None."""
        with self._lock:
            return self._primary_target

    def get_all_faces(self):
        """Return list of face dicts for overlay rendering."""
        with self._lock:
            return list(self._all_faces)

    def get_frame_jpeg(self):
        """Return the latest frame as JPEG bytes (for Flask streaming)."""
        with self._lock:
            frame = self._latest_frame
        if frame is None:
            return None
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return buf.tobytes()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _capture_loop(self):
        while self._running:
            ok, frame = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            self._process_frame(frame)

    def _process_frame(self, frame):
        h, w = frame.shape[:2]
        cx_frame, cy_frame = w / 2.0, h / 2.0
        max_dist = math.hypot(cx_frame, cy_frame)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self._cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )

        faces = []
        best_weight = -1.0
        best_target = None

        for x, y, fw, fh in rects:
            area = fw * fh
            cx_face = x + fw / 2.0
            cy_face = y + fh / 2.0
            dist = math.hypot(cx_face - cx_frame, cy_face - cy_frame)
            proximity = 1.0 / (1.0 + dist / max_dist)
            weight = area * proximity

            norm_x = cx_face / w
            norm_y = cy_face / h

            face_info = {
                "x": int(x), "y": int(y), "w": int(fw), "h": int(fh),
                "norm_x": round(norm_x, 4),
                "norm_y": round(norm_y, 4),
                "weight": round(weight, 2),
            }
            faces.append(face_info)

            if weight > best_weight:
                best_weight = weight
                best_target = (round(norm_x, 4), round(norm_y, 4), round(weight, 2))

            # Draw bounding box on frame for preview
            cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)

        # Highlight primary target
        if best_target and faces:
            primary = max(faces, key=lambda f: f["weight"])
            cv2.rectangle(
                frame,
                (primary["x"], primary["y"]),
                (primary["x"] + primary["w"], primary["y"] + primary["h"]),
                (0, 0, 255), 3,
            )

        with self._lock:
            self._latest_frame = frame
            self._all_faces = faces
            self._primary_target = best_target

    @staticmethod
    def list_cameras(max_check=2):
        """Probe available camera indices.

        Defaults to a small range to avoid noisy AVFoundation warnings.
        """
        available = []
        failures = 0
        backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
        for i in range(max_check):
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                available.append(i)
                cap.release()
                failures = 0
            else:
                failures += 1
                if available and failures >= 1:
                    break
        return available

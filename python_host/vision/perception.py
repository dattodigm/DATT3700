"""
perception.py — Optional ML perception modules (MediaPipe + DeepFace).

Uses lazy imports so the system works without ML dependencies installed.
Thread-safe: runs inference in a background thread, exposes results via
a locked dict.

Best practices followed:
  - mediapipe >= 0.10.14 uses the new Tasks API (not legacy mp.solutions)
  - deepface uses lightweight backends by default
  - No pyav / ffmpeg dependency (pure OpenCV capture)
"""

import threading
import time
import logging

logger = logging.getLogger(__name__)


class PerceptionModule:
    """Runs optional emotion + pose detection on frames from FaceTracker."""

    def __init__(self):
        self._lock = threading.Lock()
        self._results = {
            "emotion": None,       # e.g. {"dominant": "happy", "scores": {...}}
            "pose": None,         # e.g. {"landmarks": [...], "gesture": "..."}
            "face_analysis": None,  # e.g. {"age": 25, "gender": "Man", ...}
        }
        self._running = False
        self._tracker = None

        # Lazy-loaded modules
        self._mp = None
        self._deepface = None
        self._mp_face_mesh = None
        self._mp_pose = None

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def _try_load_mediapipe(self):
        try:
            import mediapipe as mp
            self._mp = mp
            # Use new Tasks API (mediapipe >= 0.10.14)
            self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._mp_pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("MediaPipe loaded successfully")
            return True
        except ImportError:
            logger.warning("MediaPipe not installed — pose/mesh disabled")
            return False

    def _try_load_deepface(self):
        try:
            from deepface import DeepFace
            self._deepface = DeepFace
            logger.info("DeepFace loaded successfully")
            return True
        except ImportError:
            logger.warning("DeepFace not installed — emotion analysis disabled")
            return False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, tracker):
        """Begin perception loop reading frames from a FaceTracker."""
        self._tracker = tracker
        self._try_load_mediapipe()
        self._try_load_deepface()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._mp_face_mesh:
            self._mp_face_mesh.close()
        if self._mp_pose:
            self._mp_pose.close()

    def get_results(self):
        with self._lock:
            return dict(self._results)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _loop(self):
        while self._running:
            if self._tracker is None:
                time.sleep(0.1)
                continue

            # Borrow the latest frame
            frame_jpeg = self._tracker.get_frame_jpeg()
            if frame_jpeg is None:
                time.sleep(0.05)
                continue

            # Decode JPEG back to numpy (avoids holding tracker lock)
            import cv2
            import numpy as np
            arr = np.frombuffer(frame_jpeg, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                time.sleep(0.05)
                continue

            results = {}

            # ── MediaPipe Face Mesh ──
            if self._mp_face_mesh:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mesh_result = self._mp_face_mesh.process(rgb)
                    if mesh_result.multi_face_landmarks:
                        landmarks = []
                        for lm in mesh_result.multi_face_landmarks[0].landmark:
                            landmarks.append({
                                "x": round(lm.x, 4),
                                "y": round(lm.y, 4),
                                "z": round(lm.z, 4),
                            })
                        results["pose"] = {"landmarks_count": len(landmarks)}
                except Exception as e:
                    logger.debug(f"MediaPipe mesh error: {e}")

            # ── MediaPipe Pose ──
            if self._mp_pose:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pose_result = self._mp_pose.process(rgb)
                    if pose_result.pose_landmarks:
                        results["pose_body"] = {
                            "landmarks_count": len(pose_result.pose_landmarks.landmark)
                        }
                except Exception as e:
                    logger.debug(f"MediaPipe pose error: {e}")

            # ── DeepFace emotion analysis (throttled) ──
            if self._deepface:
                try:
                    analysis = self._deepface.analyze(
                        frame,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True,
                    )
                    if analysis and len(analysis) > 0:
                        a = analysis[0]
                        results["emotion"] = {
                            "dominant": a.get("dominant_emotion", "unknown"),
                            "scores": a.get("emotion", {}),
                        }
                        results["face_analysis"] = {
                            "region": a.get("region", {}),
                        }
                except Exception as e:
                    logger.debug(f"DeepFace error: {e}")

            with self._lock:
                self._results.update(results)

            # Throttle to ~5 FPS for ML inference
            time.sleep(0.2)

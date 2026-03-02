"""
Vision Tracking Module
Emotion recognition (DeepFace) + Pose estimation (MediaPipe).
Falls back to Haar cascade if DeepFace/MediaPipe not available.
"""

import cv2
import numpy as np
import math
import configparser
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("[Vision] DeepFace not available, using Haar cascade fallback")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("[Vision] MediaPipe not available, pose estimation disabled")


@dataclass
class EmotionData:
    emotions: Dict[str, float] = field(default_factory=lambda: {
        'angry': 0.0, 'disgust': 0.0, 'fear': 0.0, 'happy': 0.0,
        'sad': 0.0, 'surprise': 0.0, 'neutral': 1.0
    })
    dominant_emotion: str = 'neutral'
    confidence: float = 0.0
    age: int = 0
    gender: str = 'unknown'
    face_area: float = 0.0          # normalized 0-1 relative to frame
    distance_estimate: float = 3.0  # meters
    person_count: int = 0
    pose_openness: float = 0.0      # 0=closed/defensive, 1=open/welcoming
    dominant_color: str = '#808080'


class VisionTracker:
    def __init__(self, config: configparser.ConfigParser):
        vis = config['Vision']
        self.camera_id = config.getint('Vision', 'camera_id', fallback=0)
        self.frame_width = config.getint('Vision', 'frame_width', fallback=640)
        self.frame_height = config.getint('Vision', 'frame_height', fallback=480)
        self.emotion_backend = vis.get('emotion_backend', 'deepface')
        self.deepface_model = vis.get('deepface_model', 'VGG-Face')
        self.enable_pose = config.getboolean('Vision', 'enable_pose', fallback=True)
        self.min_confidence = config.getfloat('Vision', 'min_face_confidence', fallback=0.5)
        
        self._frame_area = self.frame_width * self.frame_height
        
        # Haar cascade fallback
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # MediaPipe pose
        self.pose = None
        if MEDIAPIPE_AVAILABLE and self.enable_pose:
            mp_pose = mp.solutions.pose
            self.pose = mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
        
        # Frame counter to throttle DeepFace (expensive)
        self._frame_count = 0
        self._deepface_interval = 5  # run DeepFace every N frames
        self._last_emotion_data = EmotionData()
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, EmotionData]:
        """Process a frame and return annotated frame + EmotionData."""
        annotated = frame.copy()
        self._frame_count += 1
        
        data = EmotionData()
        
        # --- Pose estimation (every frame, lightweight) ---
        if self.pose is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)
            if results.pose_landmarks:
                self.mp_draw.draw_landmarks(
                    annotated, results.pose_landmarks,
                    mp.solutions.pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_draw.DrawingSpec(color=(0, 255, 128), thickness=1, circle_radius=2)
                )
                data.pose_openness = self.calculate_pose_openness(results.pose_landmarks)
        
        # --- Emotion / face detection ---
        if DEEPFACE_AVAILABLE and self.emotion_backend == 'deepface':
            if self._frame_count % self._deepface_interval == 0:
                try:
                    result_list = DeepFace.analyze(
                        img_path=frame,
                        actions=['emotion', 'age', 'gender'],
                        enforce_detection=False,
                        silent=True
                    )
                    if isinstance(result_list, dict):
                        result_list = [result_list]
                    
                    data.person_count = len(result_list)
                    if result_list:
                        r = result_list[0]
                        raw_emotions = r.get('emotion', {})
                        total = sum(raw_emotions.values()) or 1.0
                        data.emotions = {k: v / total for k, v in raw_emotions.items()}
                        data.dominant_emotion = r.get('dominant_emotion', 'neutral')
                        data.confidence = data.emotions.get(data.dominant_emotion, 0.0)
                        data.age = int(r.get('age', 0))
                        gender_val = r.get('dominant_gender', r.get('gender', 'unknown'))
                        if isinstance(gender_val, dict):
                            data.gender = max(gender_val, key=gender_val.get)
                        else:
                            data.gender = str(gender_val)
                        
                        # Face region
                        region = r.get('region', {})
                        if region:
                            rx, ry, rw, rh = region.get('x',0), region.get('y',0), region.get('w',0), region.get('h',0)
                            face_rect = (rx, ry, rw, rh)
                            area_ratio = (rw * rh) / self._frame_area
                            data.face_area = min(1.0, area_ratio)
                            data.distance_estimate = self.estimate_distance(area_ratio)
                            data.dominant_color = self.get_dominant_color(frame, face_rect)
                            cv2.rectangle(annotated, (rx, ry), (rx+rw, ry+rh), (0, 255, 0), 2)
                            cv2.putText(annotated, f"{data.dominant_emotion} {data.confidence:.2f}",
                                       (rx, ry - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
                    
                    self._last_emotion_data = data
                except Exception as e:
                    data = self._last_emotion_data  # reuse last good result
            else:
                data = self._last_emotion_data
        else:
            # Haar cascade fallback
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            data.person_count = len(faces)
            if len(faces) > 0:
                largest = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest
                area_ratio = (w * h) / self._frame_area
                data.face_area = min(1.0, area_ratio)
                data.distance_estimate = self.estimate_distance(area_ratio)
                data.dominant_color = self.get_dominant_color(frame, (x, y, w, h))
                data.dominant_emotion = 'neutral'
                data.confidence = 0.5
                cv2.rectangle(annotated, (x, y), (x+w, y+h), (200, 200, 0), 2)
        
        return annotated, data
    
    @staticmethod
    def estimate_distance(face_area_ratio: float) -> float:
        if face_area_ratio <= 0:
            return 3.0
        return max(0.3, min(5.0, 0.15 / math.sqrt(face_area_ratio)))
    
    @staticmethod
    def calculate_pose_openness(pose_landmarks) -> float:
        try:
            lm = pose_landmarks.landmark
            # Use shoulder-wrist spread as openness
            ls = lm[11]  # left shoulder
            rs = lm[12]  # right shoulder
            lw = lm[15]  # left wrist
            rw = lm[16]  # right wrist
            shoulder_width = abs(rs.x - ls.x)
            if shoulder_width < 0.01:
                return 0.5
            wrist_spread = abs(rw.x - lw.x)
            openness = min(1.0, wrist_spread / (shoulder_width * 3.0))
            return openness
        except Exception:
            return 0.5
    
    @staticmethod
    def get_dominant_color(frame: np.ndarray, rect=None) -> str:
        try:
            if rect is not None:
                x, y, w, h = rect
                roi = frame[max(0,y):y+h, max(0,x):x+w]
            else:
                roi = frame
            if roi.size == 0:
                return '#808080'
            # Downsample for speed
            small = cv2.resize(roi, (20, 20))
            pixels = small.reshape(-1, 3).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, _, centers = cv2.kmeans(pixels, 1, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
            b, g, r = [int(c) for c in centers[0]]
            return f'#{r:02X}{g:02X}{b:02X}'
        except Exception:
            return '#808080'

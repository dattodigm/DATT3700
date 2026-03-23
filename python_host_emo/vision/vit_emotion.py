"""
vit_emotion.py — Vision Transformer emotion detection using Hugging Face model.

Uses the pre-trained yst007/vit-emotion model for real-time emotion classification.
Thread-safe inference with lazy loading.
"""

import threading
import time
import logging
import os
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ViTEmotionDetector:
    """Real-time emotion detection using ViT from Hugging Face."""

    # Emotion class labels (standard FER-2013 classes)
    EMOTION_CLASSES = [
        "angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"
    ]

    def __init__(self, repo_id="yst007/vit-emotion"):
        self._lock = threading.Lock()
        self._model = None
        self._processor = None
        self._device = None
        self._repo_id = repo_id
        self._loaded = False
        self._load_error = None

    def load_model(self):
        """Lazy-load the ViT model and processor."""
        if self._loaded:
            return self._loaded

        try:
            import torch
            from transformers import ViTForImageClassification, ViTImageProcessor

            # Determine device
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self._device}")

            model_source = self._repo_id
            local_only = os.path.isdir(model_source)

            logger.info(f"Loading ViT model from {model_source} (local_only={local_only})...")
            self._model = ViTForImageClassification.from_pretrained(
                model_source,
                local_files_only=local_only
            ).to(self._device)
            self._processor = ViTImageProcessor.from_pretrained(
                model_source,
                local_files_only=local_only
            )
            self._model.eval()

            self._loaded = True
            logger.info("ViT emotion model loaded successfully")
            return True

        except Exception as e:
            self._load_error = str(e)
            logger.error(f"Failed to load ViT model: {e}")
            return False

    def predict(self, frame_bgr: np.ndarray, face_bbox: tuple = None):
        """
        Predict emotion from a frame or face ROI.

        Args:
            frame_bgr: BGR image (H, W, 3)
            face_bbox: Optional (x, y, w, h) to crop to face region

        Returns:
            dict with 'scores' (list of 7 probabilities) and 'dominant' (string)
        """
        if not self._loaded:
            if not self.load_model():
                return None

        try:
            # Crop to face if bbox provided
            if face_bbox:
                x, y, w, h = face_bbox
                face_roi = frame_bgr[y:y+h, x:x+w]
                if face_roi.size == 0:
                    return None
            else:
                face_roi = frame_bgr

            # Convert BGR to RGB
            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

            # Preprocess
            inputs = self._processor(images=face_rgb, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Inference
            import torch
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

            # Build result dict
            scores = probs.tolist()
            dominant_idx = int(np.argmax(probs))
            dominant_emotion = self.EMOTION_CLASSES[dominant_idx]

            return {
                "scores": scores,
                "dominant": dominant_emotion,
                "confidence": float(probs[dominant_idx]),
            }

        except Exception as e:
            logger.debug(f"ViT prediction error: {e}")
            return None

    def get_emotion_colors(self):
        """Return color mapping for emotions (for visualization)."""
        return {
            "angry": "#FF0000",
            "disgust": "#00FF00",
            "fear": "#800080",
            "happy": "#FFFF00",
            "sad": "#0000FF",
            "surprise": "#FFA500",
            "neutral": "#808080",
        }
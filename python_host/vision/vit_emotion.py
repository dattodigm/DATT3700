"""ViT emotion detection using Hugging Face models with local fallback support."""

import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ViTEmotionDetector:
    """Real-time emotion detector backed by ViTForImageClassification."""

    EMOTION_CLASSES = [
        "angry",
        "disgust",
        "fear",
        "happy",
        "sad",
        "surprise",
        "neutral",
    ]

    def __init__(self, repo_id="yst007/vit-emotion"):
        self._model = None
        self._processor = None
        self._device = None
        self._repo_id = repo_id
        self._loaded = False
        self._load_error = None

    def _resolve_model_source(self):
        if os.path.isdir(self._repo_id):
            return self._repo_id, True

        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "..", "models", "vit-emotion"),
            os.path.join(base_dir, "..", "..", "python_host_emo", "models", "vit-emotion"),
        ]
        for path in candidates:
            if os.path.isdir(path):
                return path, True

        return self._repo_id, False

    def load_model(self):
        if self._loaded:
            return True

        try:
            import torch
            from transformers import ViTForImageClassification, ViTImageProcessor

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            model_source, local_only = self._resolve_model_source()
            logger.info("Loading ViT model from %s (local_only=%s)", model_source, local_only)

            def _load_pair(source, only_local):
                model = ViTForImageClassification.from_pretrained(
                    source,
                    local_files_only=only_local,
                ).to(self._device)
                processor = ViTImageProcessor.from_pretrained(
                    source,
                    local_files_only=only_local,
                )
                return model, processor

            try:
                self._model, self._processor = _load_pair(model_source, local_only)
            except Exception as local_exc:
                # Local model directory exists but is incomplete/corrupt:
                # fallback to remote repo so first-run bootstrap can recover.
                if local_only and model_source != self._repo_id:
                    logger.warning(
                        "Local ViT model load failed (%s). Falling back to repo %s",
                        local_exc,
                        self._repo_id,
                    )
                    self._model, self._processor = _load_pair(self._repo_id, False)
                else:
                    raise

            self._model.eval()

            self._loaded = True
            return True
        except Exception as exc:
            self._load_error = str(exc)
            logger.warning("Failed to load ViT model: %s", exc)
            return False

    def predict(self, frame_bgr: np.ndarray, face_bbox=None):
        if not self._loaded and not self.load_model():
            return None

        try:
            if face_bbox:
                x, y, w, h = [int(v) for v in face_bbox]
                face_roi = frame_bgr[y : y + h, x : x + w]
                if face_roi.size == 0:
                    return None
            else:
                face_roi = frame_bgr

            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
            inputs = self._processor(images=face_rgb, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            import torch

            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].cpu().numpy()

            dominant_idx = int(np.argmax(probs))
            return {
                "scores": probs.tolist(),
                "dominant": self.EMOTION_CLASSES[dominant_idx],
                "confidence": float(probs[dominant_idx]),
            }
        except Exception as exc:
            logger.debug("ViT prediction error: %s", exc)
            return None


"""
ML Trainer — lightweight emotion-to-persona classifier.
Uses scikit-learn RandomForest or SVM.
Saves/loads model to/from file.
"""

import json
import os
import logging
import configparser
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[ML] scikit-learn not available, ML training disabled")


class MLTrainer:
    """Trains and persists an emotion → persona classifier."""

    FEATURE_NAMES = [
        'angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral',
        'distance', 'face_area', 'pose_openness'
    ]

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.model_path = config.get('ML', 'model_path', fallback='ml_model.pkl')
        self.data_path = config.get('ML', 'data_path', fallback='training_data.json')
        self.classifier_type = config.get('ML', 'classifier', fallback='random_forest')
        
        self.model = None
        self.label_encoder = LabelEncoder() if SKLEARN_AVAILABLE else None
        self.training_data: List[dict] = []  # list of {features: [...], label: str}
        
        # Load existing data
        self._load_data()

    def record_sample(self, features: list, persona_label: str):
        """Add one training sample."""
        self.training_data.append({'features': features, 'label': persona_label})
        self._save_data()
        logger.info(f"[ML] Recorded sample: label={persona_label}, total={len(self.training_data)}")

    def train(self) -> Optional[dict]:
        """Train classifier on all recorded data. Returns metrics dict or None."""
        if not SKLEARN_AVAILABLE:
            logger.error("[ML] scikit-learn not available")
            return None
        
        if len(self.training_data) < 10:
            logger.warning(f"[ML] Not enough samples ({len(self.training_data)}), need at least 10")
            return None
        
        X = np.array([d['features'] for d in self.training_data])
        y_raw = [d['label'] for d in self.training_data]
        y = self.label_encoder.fit_transform(y_raw)
        
        if self.classifier_type == 'svm':
            clf = SVC(kernel='rbf', probability=True, C=10)
        else:
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Cross-validation
        if len(X) >= 20:
            scores = cross_val_score(clf, X, y, cv=min(5, len(X) // 4))
            accuracy = float(scores.mean())
        else:
            accuracy = 0.0
        
        clf.fit(X, y)
        self.model = clf
        
        # Save model
        if SKLEARN_AVAILABLE:
            joblib.dump({'model': clf, 'label_encoder': self.label_encoder}, self.model_path)
            logger.info(f"[ML] Model saved to {self.model_path}, accuracy={accuracy:.2f}")
        
        return {'accuracy': accuracy, 'n_samples': len(self.training_data),
                'labels': list(self.label_encoder.classes_)}

    def load_model(self) -> bool:
        """Load previously trained model."""
        if not SKLEARN_AVAILABLE or not os.path.exists(self.model_path):
            return False
        try:
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.label_encoder = data['label_encoder']
            logger.info(f"[ML] Model loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.warning(f"[ML] Failed to load model: {e}")
            return False

    def _save_data(self):
        try:
            with open(self.data_path, 'w') as f:
                json.dump(self.training_data, f, indent=2)
        except Exception as e:
            logger.warning(f"[ML] Failed to save data: {e}")

    def _load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    self.training_data = json.load(f)
                logger.info(f"[ML] Loaded {len(self.training_data)} training samples")
            except Exception as e:
                logger.warning(f"[ML] Failed to load data: {e}")
                self.training_data = []

    def clear_data(self):
        self.training_data = []
        if os.path.exists(self.data_path):
            os.remove(self.data_path)
        logger.info("[ML] Training data cleared")

    @property
    def sample_count(self) -> int:
        return len(self.training_data)

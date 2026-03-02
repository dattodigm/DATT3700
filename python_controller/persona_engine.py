"""
Persona Engine — 3-layer biomorphic system.

Layer 1: ML Brain     — maps messy sensor data → discrete persona label
Layer 2: State Machine — maps persona label → precise motor/LED params
Layer 3: Motion Render — applies EMA smoothing and physical dynamics
"""

import time
import math
import random
import configparser
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from vision_tracker import EmotionData

logger = logging.getLogger(__name__)


# ─── Layer 2: Persona → Hardware params ────────────────────────────────────────

PERSONA_PARAMS: Dict[str, dict] = {
    'Empathy':   {'openness': 1.0,  'jitter': 0.0, 'speed': 0.4, 'led_hue': 120, 'led_sat': 0.8, 'led_bri': 0.8},
    'Defensive': {'openness': 0.1,  'jitter': 0.2, 'speed': 0.2, 'led_hue': 240, 'led_sat': 0.9, 'led_bri': 0.5},
    'Predatory': {'openness': 0.7,  'jitter': 0.1, 'speed': 0.8, 'led_hue':  0,  'led_sat': 1.0, 'led_bri': 0.9},
    'Boredom':   {'openness': 0.3,  'jitter': 0.0, 'speed': 0.1, 'led_hue': 200, 'led_sat': 0.3, 'led_bri': 0.3},
    'Surprise':  {'openness': 1.0,  'jitter': 1.0, 'speed': 1.0, 'led_hue':  60, 'led_sat': 1.0, 'led_bri': 1.0},
    'Jealous':   {'openness': 0.6,  'jitter': 0.5, 'speed': 0.6, 'led_hue':  0,  'led_sat': 1.0, 'led_bri': 0.7},
}


@dataclass
class DeviceState:
    """Rendered state for one physical flower device."""
    name: str
    persona: str = 'Boredom'
    openness: float = 0.3      # 0-1
    led_hue: float = 200.0     # 0-360
    led_sat: float = 0.3
    led_bri: float = 0.3
    jitter_offset: float = 0.0
    override_until: float = 0.0  # epoch time; if > now, state is locked

    def is_overridden(self) -> bool:
        return time.time() < self.override_until


class PersonaEngine:
    """
    Drives all flower devices based on sensor data.
    """

    def __init__(self, config: configparser.ConfigParser, device_names: list):
        self.config = config
        self.ema_alpha = config.getfloat('Personas', 'ema_alpha', fallback=0.3)
        self.jealousy_trigger = config.getfloat('Personas', 'jealousy_trigger_seconds', fallback=5.0)
        self.jealousy_burst = config.getfloat('Personas', 'jealousy_burst_seconds', fallback=8.0)
        
        self.states: Dict[str, DeviceState] = {
            name: DeviceState(name=name) for name in device_names
        }
        
        # Track how long first device has been Empathy
        self._empathy_start: Dict[str, Optional[float]] = {n: None for n in device_names}
        
        # ML model (set by MLTrainer)
        self.ml_model = None
        self.label_encoder = None

    def set_ml_model(self, model, label_encoder):
        self.ml_model = model
        self.label_encoder = label_encoder

    def predict_persona(self, emotion_data: EmotionData) -> str:
        """Layer 1: ML Brain — predict persona from sensor data."""
        if self.ml_model is None:
            # Heuristic fallback
            return self._heuristic_persona(emotion_data)
        
        try:
            features = self._extract_features(emotion_data)
            import numpy as np
            pred = self.ml_model.predict([features])[0]
            if self.label_encoder:
                return self.label_encoder.inverse_transform([pred])[0]
            return str(pred)
        except Exception as e:
            logger.debug(f"ML predict failed: {e}")
            return self._heuristic_persona(emotion_data)

    def _heuristic_persona(self, emotion_data: EmotionData) -> str:
        """Simple rule-based fallback when no ML model is trained."""
        e = emotion_data.emotions
        if e.get('happy', 0) > 0.4:
            return 'Empathy'
        if e.get('surprise', 0) > 0.4:
            return 'Surprise'
        if e.get('angry', 0) > 0.3 or e.get('fear', 0) > 0.3:
            return 'Defensive'
        if emotion_data.distance_estimate < 0.8:
            return 'Predatory'
        if emotion_data.person_count == 0:
            return 'Boredom'
        return 'Empathy'

    @staticmethod
    def _extract_features(emotion_data: EmotionData) -> list:
        e = emotion_data.emotions
        return [
            e.get('angry', 0), e.get('disgust', 0), e.get('fear', 0),
            e.get('happy', 0), e.get('sad', 0), e.get('surprise', 0),
            e.get('neutral', 0),
            emotion_data.distance_estimate,
            emotion_data.face_area,
            emotion_data.pose_openness,
        ]

    def update(self, emotion_data: EmotionData, primary_device: str = None):
        """
        Layer 2: State machine update.
        - Predicts persona for primary device
        - Applies jealousy network to other devices
        - Returns dict of DeviceState
        """
        if not self.states:
            return {}
        
        device_names = list(self.states.keys())
        if primary_device is None:
            primary_device = device_names[0]
        
        # Predict primary persona
        primary_persona = self.predict_persona(emotion_data)
        
        for name, state in self.states.items():
            if state.is_overridden():
                continue  # Locked by override (e.g. Jealous)
            
            if name == primary_device:
                target_persona = primary_persona
            else:
                # Jealousy network: if another device has been Empathy for too long
                target_persona = 'Boredom'
            
            self._apply_persona(state, target_persona)
        
        # Jealousy network
        if primary_persona == 'Empathy':
            if self._empathy_start[primary_device] is None:
                self._empathy_start[primary_device] = time.time()
            elapsed = time.time() - self._empathy_start[primary_device]
            if elapsed >= self.jealousy_trigger:
                for name in device_names:
                    if name != primary_device and not self.states[name].is_overridden():
                        logger.info(f"[Jealousy] Device '{name}' becomes Jealous!")
                        self._apply_persona(self.states[name], 'Jealous')
                        self.states[name].override_until = time.time() + self.jealousy_burst
        else:
            self._empathy_start[primary_device] = None
        
        return self.states

    def _apply_persona(self, state: DeviceState, persona: str):
        """Layer 2 → Layer 3: Apply persona params with EMA smoothing."""
        params = PERSONA_PARAMS.get(persona, PERSONA_PARAMS['Boredom'])
        state.persona = persona
        alpha = self.ema_alpha
        
        # Add jitter (Layer 3 physical render)
        jitter_amount = params['jitter']
        jitter = (random.random() - 0.5) * 2.0 * jitter_amount * 0.2
        
        target_openness = params['openness'] + jitter
        target_openness = max(0.0, min(1.0, target_openness))
        
        # EMA smoothing
        state.openness = state.openness * (1 - alpha) + target_openness * alpha
        state.led_hue   = state.led_hue   * (1 - alpha) + params['led_hue'] * alpha
        state.led_sat   = state.led_sat   * (1 - alpha) + params['led_sat'] * alpha
        state.led_bri   = state.led_bri   * (1 - alpha) + params['led_bri'] * alpha
        state.jitter_offset = jitter

    def manual_override(self, device_name: str, persona: str, duration: float = 0):
        """Manually set a device's persona (from GUI)."""
        if device_name in self.states:
            self._apply_persona(self.states[device_name], persona)
            if duration > 0:
                self.states[device_name].override_until = time.time() + duration

    def apply_to_network(self, flower_network):
        """Send all device states to the FlowerNetwork via OSC."""
        for name, state in self.states.items():
            device = flower_network.get(name)
            if device is None:
                continue
            # Set motor direction from openness
            direction = 1 if state.openness > 0.6 else (-1 if state.openness < 0.3 else 0)
            device.set_motor(1, direction)
            # Set LEDs
            device.set_led_hsv(1, state.led_hue, state.led_sat, state.led_bri)
            device.set_led_hsv(2, (state.led_hue + 30) % 360, state.led_sat * 0.8, state.led_bri * 0.7)

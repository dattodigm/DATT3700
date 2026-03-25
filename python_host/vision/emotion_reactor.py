"""Emotion reactor for mapping face emotion signals to node-safe OSC actions."""

import time
from collections import defaultdict


class EmotionReactor:
    """Smooths emotion detections and dispatches coarse flower-state commands."""

    FLOWER_STATES = ("BLOOM", "ALERT", "SOOTHE", "REST")

    # Human emotion -> flower emotion.
    HUMAN_TO_FLOWER = {
        "happy": "BLOOM",
        "surprise": "BLOOM",
        "angry": "ALERT",
        "fear": "ALERT",
        "disgust": "ALERT",
        "sad": "SOOTHE",
        "neutral": "SOOTHE",
    }

    def __init__(
        self,
        osc_sender,
        get_target_devices=None,
        get_selected_target=None,
        get_selected_node_type=None,
        *,
        enter_th=1.8,
        exit_th=1.0,
        min_hold_ms=1500,
        command_cooldown_ms=1200,
        no_face_timeout_ms=2500,
        decay=0.88,
    ):
        self._osc = osc_sender
        self._get_target_devices = get_target_devices
        self._get_selected_target = get_selected_target
        self._get_selected_node_type = get_selected_node_type

        self._enter_th = float(enter_th)
        self._exit_th = float(exit_th)
        self._min_hold_ms = int(min_hold_ms)
        self._command_cooldown_ms = int(command_cooldown_ms)
        self._no_face_timeout_ms = int(no_face_timeout_ms)
        self._decay = float(decay)
        self._burst_enter_mult = 0.72
        self._burst_confidence = 0.5
        self._shock_scale = 2.2
        self._shock_threshold = 0.35
        self._state_gain = {
            "BLOOM": 1.25,
            "ALERT": 1.35,
            "SOOTHE": 0.75,
        }
        self._state_hold_ms = {
            "BLOOM": int(min_hold_ms * 0.4),
            "ALERT": int(min_hold_ms * 0.25),
            "SOOTHE": int(min_hold_ms * 1.15),
            "REST": int(min_hold_ms * 0.6),
        }

        self._last_face_ts = 0.0
        self._last_update_ts = 0.0
        self._state_since_ts = 0.0

        self._current = "REST"
        self._pending = None
        self._pending_since_ts = 0.0

        self._flower_scores = {"BLOOM": 0.0, "ALERT": 0.0, "SOOTHE": 0.0}
        self._source_emotion = None
        self._source_confidence = 0.0
        self._source_model = None

        self._last_command_ts = 0.0
        self._last_command = None
        self._last_command_ts_by_target = {}
        self._last_command_by_target = {}
        self._option_index = defaultdict(int)
        self._enabled = True

    def reset(self):
        """Reset dynamic state when camera stops."""
        self._last_face_ts = 0.0
        self._last_update_ts = 0.0
        self._state_since_ts = 0.0
        self._current = "REST"
        self._pending = None
        self._pending_since_ts = 0.0
        self._flower_scores = {"BLOOM": 0.0, "ALERT": 0.0, "SOOTHE": 0.0}
        self._source_emotion = None
        self._source_confidence = 0.0
        self._source_model = None
        self._last_command_ts = 0.0
        self._last_command = None
        self._last_command_ts_by_target = {}
        self._last_command_by_target = {}

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)

    def is_enabled(self):
        return bool(self._enabled)

    def _dispatch_targets(self):
        if callable(self._get_target_devices):
            devices = self._get_target_devices() or []
            out = []
            for dev in devices:
                name = str(dev.get("name", "")).strip()
                node_type = str(dev.get("node_type", "unknown")).strip() or "unknown"
                if not name:
                    continue
                out.append({"name": name, "node_type": node_type})
            return out

        # Backward-compatible fallback for tests or legacy wiring.
        target = self._get_selected_target() if callable(self._get_selected_target) else None
        node_type = self._get_selected_node_type() if callable(self._get_selected_node_type) else "unknown"
        if target:
            return [{"name": str(target), "node_type": str(node_type or "unknown")}]
        return []

    def update(self, perception, has_face):
        """Consume latest perception data and advance the reactor state machine."""
        now = time.time()
        if self._last_update_ts <= 0.0:
            self._last_update_ts = now
            self._state_since_ts = now

        dominant, confidence, model = self._extract_human_emotion(perception)

        for key in self._flower_scores:
            self._flower_scores[key] *= self._decay

        if has_face:
            self._last_face_ts = now
            if dominant:
                flower = self.HUMAN_TO_FLOWER.get(dominant)
                if flower:
                    add = self._score_increment(flower, confidence)
                    self._flower_scores[flower] += add
                    if flower in ("BLOOM", "ALERT") and confidence >= 0.35:
                        self._flower_scores["SOOTHE"] *= 0.88
                    self._source_emotion = dominant
                    self._source_confidence = float(confidence)
                    self._source_model = model

        desired = self._decide_state(now=now, has_face=has_face)
        self._maybe_transition(desired, now)
        self._maybe_dispatch(now)
        self._last_update_ts = now

        return self.snapshot(now=now, has_face=has_face)

    def get_config(self):
        return {
            "enabled": self._enabled,
            "enter_th": self._enter_th,
            "exit_th": self._exit_th,
            "decay": self._decay,
            "command_cooldown_ms": self._command_cooldown_ms,
            "no_face_timeout_ms": self._no_face_timeout_ms,
            "burst_enter_mult": self._burst_enter_mult,
            "burst_confidence": self._burst_confidence,
            "shock_scale": self._shock_scale,
            "shock_threshold": self._shock_threshold,
            "bloom_gain": self._state_gain["BLOOM"],
            "alert_gain": self._state_gain["ALERT"],
            "soothe_gain": self._state_gain["SOOTHE"],
            "hold_bloom_ms": self._state_hold_ms["BLOOM"],
            "hold_alert_ms": self._state_hold_ms["ALERT"],
            "hold_soothe_ms": self._state_hold_ms["SOOTHE"],
            "hold_rest_ms": self._state_hold_ms["REST"],
        }

    def update_config(self, payload):
        payload = payload or {}

        def _f(name, low=None, high=None):
            if name not in payload:
                return None
            try:
                value = float(payload[name])
            except (TypeError, ValueError):
                return None
            if low is not None:
                value = max(low, value)
            if high is not None:
                value = min(high, value)
            return value

        def _i(name, low=None, high=None):
            v = _f(name, low=low, high=high)
            return int(v) if v is not None else None

        val = _f("enter_th", low=0.4, high=5.0)
        if val is not None:
            self._enter_th = val
        val = _f("exit_th", low=0.2, high=4.5)
        if val is not None:
            self._exit_th = min(val, self._enter_th)
        val = _f("decay", low=0.5, high=0.995)
        if val is not None:
            self._decay = val
        val = _i("command_cooldown_ms", low=100, high=5000)
        if val is not None:
            self._command_cooldown_ms = val
        val = _i("no_face_timeout_ms", low=500, high=8000)
        if val is not None:
            self._no_face_timeout_ms = val

        val = _f("burst_enter_mult", low=0.2, high=1.2)
        if val is not None:
            self._burst_enter_mult = val
        val = _f("burst_confidence", low=0.1, high=1.0)
        if val is not None:
            self._burst_confidence = val
        val = _f("shock_scale", low=0.0, high=6.0)
        if val is not None:
            self._shock_scale = val
        val = _f("shock_threshold", low=0.0, high=1.0)
        if val is not None:
            self._shock_threshold = val

        val = _f("bloom_gain", low=0.1, high=4.0)
        if val is not None:
            self._state_gain["BLOOM"] = val
        val = _f("alert_gain", low=0.1, high=4.0)
        if val is not None:
            self._state_gain["ALERT"] = val
        val = _f("soothe_gain", low=0.1, high=4.0)
        if val is not None:
            self._state_gain["SOOTHE"] = val

        for state, key in (("BLOOM", "hold_bloom_ms"), ("ALERT", "hold_alert_ms"), ("SOOTHE", "hold_soothe_ms"), ("REST", "hold_rest_ms")):
            val = _i(key, low=0, high=5000)
            if val is not None:
                self._state_hold_ms[state] = val

        return self.get_config()

    def snapshot(self, now=None, has_face=False):
        now = now or time.time()
        age_ms = None
        if self._last_face_ts > 0.0:
            age_ms = int((now - self._last_face_ts) * 1000)

        current_score = self._flower_scores.get(self._current, 0.0)
        if self._current == "REST":
            if has_face:
                stability = 0.0
            elif age_ms is None:
                stability = 100.0
            else:
                stability = min(100.0, (age_ms / float(self._no_face_timeout_ms)) * 100.0)
        else:
            stability = min(100.0, (current_score / max(self._enter_th, 0.001)) * 100.0)

        return {
            "flower_emotion": self._current,
            "source_emotion": self._source_emotion,
            "source_confidence": round(float(self._source_confidence), 4),
            "source_model": self._source_model,
            "stability": round(float(stability), 2),
            "scores": {k: round(float(v), 4) for k, v in self._flower_scores.items()},
            "pending_emotion": self._pending,
            "has_face": bool(has_face),
            "last_face_age_ms": age_ms,
            "thresholds": {
                "enter": self._enter_th,
                "exit": self._exit_th,
                "min_hold_ms": self._min_hold_ms,
                "command_cooldown_ms": self._command_cooldown_ms,
                "no_face_timeout_ms": self._no_face_timeout_ms,
            },
            "config": self.get_config(),
            "last_command": self._last_command,
            "enabled": self._enabled,
            "target_count": len(self._dispatch_targets()),
        }

    def _score_increment(self, flower, confidence):
        conf = max(0.0, min(1.0, float(confidence or 0.0)))
        gain = self._state_gain.get(flower, 1.0)
        add = max(0.03, conf) * gain
        if flower in ("BLOOM", "ALERT"):
            shock = max(0.0, conf - self._shock_threshold)
            add *= 1.0 + (self._shock_scale * shock)
        return add

    def _extract_human_emotion(self, perception):
        if not isinstance(perception, dict):
            return None, 0.0, None

        vit = perception.get("vit_emotion")
        if isinstance(vit, dict) and vit.get("dominant"):
            return str(vit.get("dominant", "")).lower(), float(vit.get("confidence", 0.0) or 0.0), "vit"

        emotion = perception.get("emotion")
        if isinstance(emotion, dict) and emotion.get("dominant"):
            scores = emotion.get("scores") or {}
            dominant = str(emotion.get("dominant", "")).lower()
            confidence = float(scores.get(dominant, 0.5) or 0.5)
            if confidence > 1.0:
                confidence = confidence / 100.0
            return dominant, confidence, "deepface"

        return None, 0.0, None

    def _decide_state(self, now, has_face):
        if not has_face:
            if self._last_face_ts <= 0.0:
                return "REST"
            if (now - self._last_face_ts) * 1000.0 >= self._no_face_timeout_ms:
                return "REST"

        ranked = sorted(self._flower_scores.items(), key=lambda item: item[1], reverse=True)
        best_state, best_score = ranked[0] if ranked else ("SOOTHE", 0.0)
        burst_th = self._enter_th * self._burst_enter_mult

        if self._current == "REST":
            if best_state in ("BLOOM", "ALERT") and best_score >= burst_th:
                return best_state
            return best_state if best_score >= self._enter_th else "REST"

        if best_state in ("BLOOM", "ALERT") and best_score >= burst_th:
            return best_state

        current_score = self._flower_scores.get(self._current, 0.0)
        if current_score >= self._exit_th:
            return self._current

        if best_score >= self._enter_th:
            return best_state

        return "SOOTHE" if has_face else "REST"

    def _maybe_transition(self, desired, now):
        if desired == self._current:
            self._pending = None
            self._pending_since_ts = 0.0
            return

        if self._pending != desired:
            self._pending = desired
            self._pending_since_ts = now
            return

        held_ms = int((now - self._pending_since_ts) * 1000)
        hold_required = self._state_hold_ms.get(desired, self._min_hold_ms)
        if desired in ("BLOOM", "ALERT") and self._source_confidence >= self._burst_confidence:
            hold_required = 0

        if held_ms < hold_required:
            return

        self._current = desired
        self._state_since_ts = now
        self._pending = None
        self._pending_since_ts = 0.0

    def _maybe_dispatch(self, now):
        if not self._enabled:
            return

        targets = self._dispatch_targets()
        if not targets:
            return

        sent_any = False
        for item in targets:
            target = item["name"]
            node_type = item["node_type"]
            command = self._command_for(node_type=node_type, flower_emotion=self._current)
            if command is None:
                continue

            address, args = command
            serialized = {
                "target": target,
                "node_type": node_type,
                "address": address,
                "args": list(args),
                "flower_emotion": self._current,
            }

            if self._last_command_by_target.get(target) == serialized:
                continue

            last_ts = self._last_command_ts_by_target.get(target, 0.0)
            if last_ts > 0.0 and (now - last_ts) * 1000.0 < self._command_cooldown_ms:
                continue

            sent = self._osc.send_raw(target, address, list(args), source="auto")
            if sent:
                sent_any = True
                self._last_command_ts_by_target[target] = now
                self._last_command_by_target[target] = serialized

        if sent_any:
            self._last_command_ts = now
            self._last_command = {
                "flower_emotion": self._current,
                "targets": len(targets),
                "ts": round(now, 3),
            }

    def _command_for(self, node_type, flower_emotion):
        node = str(node_type or "").lower()

        if node == "sue":
            options = {
                "BLOOM": [("/state", ["bloom"]), ("/state", ["relax"])],
                "ALERT": [("/state", ["alert"]), ("/state", ["danger"])],
                "SOOTHE": [("/state", ["soothe"]), ("/state", ["calm"])],
                "REST": [("/state", ["rest"]), ("/state", ["idle"])],
            }
            return self._next_option(node, flower_emotion, options)

        if node == "kait":
            options = {
                "BLOOM": [("/motion", [2]), ("/motion", [6])],
                "ALERT": [("/motion", [3]), ("/motion", [4])],
                "SOOTHE": [("/motion", [1]), ("/motion", [5])],
                "REST": [("/stop", [])],
            }
            return self._next_option(node, flower_emotion, options)

        if node == "sylvie":
            mapping = {
                "BLOOM": ("/preset", [1]),
                "ALERT": ("/preset", [2]),
                "SOOTHE": ("/preset", [4]),
                "REST": ("/preset", [3]),
            }
            return mapping.get(flower_emotion)

        return None

    def _next_option(self, node_type, flower_emotion, options):
        pool = options.get(flower_emotion, [])
        if not pool:
            return None
        key = f"{node_type}:{flower_emotion}"
        idx = self._option_index[key] % len(pool)
        self._option_index[key] += 1
        return pool[idx]


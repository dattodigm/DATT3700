# System Architecture

## Overview

Digital Bloom uses a three-layer biomorphic control architecture:

```
┌────────────────────────────────────────────────────────────────┐
│  PC / Python Controller                                        │
│                                                                │
│  Layer 1: ML Brain         Emotion probabilities (7-dim)       │
│           (scikit-learn)   + distance + pose openness          │
│               │                    │                           │
│               ▼                    │                           │
│           Persona Label ◄──────────┘                          │
│  (Empathy / Defensive / Predatory / Boredom / Surprise / Jealous)│
│               │                                                │
│  Layer 2: State Machine    lookup PERSONA_PARAMS dict          │
│           + Jealousy Network: if flower A held Empathy >5s     │
│             → force flower B/C into 'Jealous' for 8s           │
│               │                                                │
│  Layer 3: Motion Render    EMA smoothing (alpha=0.3)           │
│           discrete params  + Perlin-like jitter                │
│               │                                                │
│          OSC / UDP ─────────────────────────────────────────┐  │
└─────────────────────────────────────────────────────────────┼──┘
                                                              │
                         WiFi (ESP32 AP or existing LAN)      │
                                                              │
┌───────────────────────────────────────────────────────────  ▼  ┐
│  ESP32 Flowers (Sylvie / Sue)                                   │
│                                                                │
│  OSC Server (port 8888) → DC motors + RGB LEDs                 │
│  OR servo + ultrasonic                                         │
└────────────────────────────────────────────────────────────────┘
```

## Layer 1 — ML Brain

**File**: `persona_engine.py` (`PersonaEngine.predict_persona`)

Input features (10-dim):
- 7 emotion probabilities from DeepFace: `angry, disgust, fear, happy, sad, surprise, neutral`
- `distance_estimate` (metres, derived from face bounding box area)
- `face_area` (normalised 0–1)
- `pose_openness` (MediaPipe wrist/shoulder spread, 0–1)

Classifier: `RandomForestClassifier` (default) or `SVC` (configurable in `config.ini`)

When no model is trained, a heuristic rule-set is used (see `_heuristic_persona`).

## Layer 2 — State Machine / Nervous System

**File**: `persona_engine.py` (`PERSONA_PARAMS`, `PersonaEngine.update`)

Each persona maps to hardware parameters:

| Persona   | Openness | Jitter | Speed | LED Hue |
|-----------|----------|--------|-------|---------|
| Empathy   | 1.0      | 0.0    | 0.4   | 120 (green) |
| Defensive | 0.1      | 0.2    | 0.2   | 240 (blue) |
| Predatory | 0.7      | 0.1    | 0.8   | 0 (red) |
| Boredom   | 0.3      | 0.0    | 0.1   | 200 (cool blue) |
| Surprise  | 1.0      | 1.0    | 1.0   | 60 (yellow) |
| Jealous   | 0.6      | 0.5    | 0.6   | 0 (red) |

**Jealousy Network**: If the primary device stays in `Empathy` for >5 seconds, all other devices are force-overridden to `Jealous` for 8 seconds.

## Layer 3 — Physical Rendering

**File**: `persona_engine.py` (`PersonaEngine._apply_persona`)

- **EMA smoothing**: `state = prev * (1 - α) + target * α` — prevents abrupt jumps
- **Jitter**: random noise added to openness proportional to `jitter` param
- Alpha configurable via `config.ini` `[Personas] ema_alpha`

## Vision Pipeline

**File**: `vision_tracker.py`

```
Webcam frame (BGR)
    │
    ├──▶ MediaPipe Pose ──▶ pose_openness (0–1)
    │
    └──▶ DeepFace.analyze ──▶ emotions dict, age, gender, face region
              │
              ├──▶ face_area → distance_estimate
              └──▶ k-means colour → dominant_color hex
```

DeepFace runs every 5 frames (configurable) to keep latency low.
MediaPipe runs every frame (lightweight).

## Communication

Protocol: **OSC over UDP** (python-osc → arduino-osc library)

Actual esp32_sylvie commands:

| OSC Address | Args | Description |
|-------------|------|-------------|
| `/auto` | `[0\|1]` | Switch auto/manual mode |
| `/motor1` | `[1\|-1\|0]` | DC motor A: open/close/stop |
| `/motor2` | `[1\|-1\|0]` | DC motor B |
| `/led1` | `[r, g, b]` | RGB LED 1 (0–255 each) |
| `/led2` | `[r, g, b]` | RGB LED 2 |
| `/preset` | `[1\|2\|3]` | Scene presets |

Default ESP32 AP: `192.168.4.1:8888`

## File Structure

```
python_controller/
├── main.py              # Entry point
├── config.ini           # All configuration
├── vision_tracker.py    # DeepFace + MediaPipe
├── osc_client.py        # Multi-device OSC network
├── persona_engine.py    # 3-layer control engine
├── ml_trainer.py        # sklearn classifier training
├── control_panel.py     # Tkinter GUI
├── pid_controller.py    # PID (retained for servo tuning)
└── requirements.txt

esp32_firmware/
├── eps32_sylvie/        # DC motor + LED firmware (main)
│   ├── esp32_sylvie.ino
│   └── sylvie.ino
└── esp32_sue/           # Servo + ultrasonic firmware
    └── servo.ino
```

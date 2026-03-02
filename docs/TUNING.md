# Tuning Guide

## ML Model Tuning

### Recording Training Data

1. Open the control panel: `python main.py`
2. Stand in front of the webcam and deliberately express each emotion.
3. Select the matching **Persona Label** in the panel and click **⏺ Record Sample**.
4. Aim for **≥15 samples per persona** (at least 6 personas = 90+ total).
5. Include variety: different distances, lighting, partial faces.

### Training

Click **🏋 Train Model**. The panel shows cross-validation accuracy.

Target accuracy ≥ 75%. If lower:
- Add more samples
- Reduce number of persona classes
- Switch to SVM in `config.ini`: `[ML] classifier = svm`

### Retraining

Training data is saved to `training_data.json` automatically.
Model is saved to `ml_model.pkl`.

To start fresh: delete both files, then re-record.

---

## Persona Parameters

Edit `PERSONA_PARAMS` in `persona_engine.py` to tune each persona's physical expression:

```python
PERSONA_PARAMS = {
    'Empathy': {
        'openness': 1.0,   # 0=closed, 1=fully open
        'jitter':   0.0,   # 0=smooth, 1=chaotic
        'speed':    0.4,   # motion speed multiplier
        'led_hue':  120,   # hue 0-360 (green=120)
        'led_sat':  0.8,   # saturation 0-1
        'led_bri':  0.8,   # brightness 0-1
    },
    ...
}
```

---

## EMA Smoothing

Set `ema_alpha` in `config.ini` `[Personas]`:
- `0.1` = very slow/sluggish response
- `0.5` = medium
- `0.9` = fast/snappy (may look jerky)

Default: `0.3`

---

## Jealousy Network

`jealousy_trigger_seconds` (default 5.0): seconds of continuous `Empathy` on the primary flower before siblings become `Jealous`.

Override duration is hardcoded at 8 seconds (`persona_engine.py` line `override_until = time.time() + 8.0`).

---

## Vision Backend

### DeepFace (recommended)
`[Vision] emotion_backend = deepface`

More accurate but ~200 ms per analysis. Runs every 5 frames.

### Haar Cascade (fast fallback)
`[Vision] emotion_backend = haar`

Only detects face presence, no emotion. Useful for testing hardware without GPU.

### Pose Estimation
`[Vision] enable_pose = true/false`

Requires MediaPipe. Adds wrist/shoulder spread as `pose_openness` feature.

---

## Multiple Devices

Add devices to `config.ini`:

```ini
[Devices]
device_list = sylvie,sue2

[Device_sue2]
ip = 192.168.4.3
port = 8888
type = dc_motor
description = Second flower unit
```

Each additional device joins the jealousy network automatically.

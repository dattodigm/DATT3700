# Upgrade Summary Report

Date: 2026-03-16

## Scope
Merged `python_host_emo` emotion capability into `python_host` using a minimal-risk architecture:
- Kept existing camera lifecycle and multi-node panel structure.
- Added perception + reactor pipeline for `human_emotion -> flower_emotion -> node_command`.
- Added concise UI status for live flower emotion state.

## What Changed

### 0) Startup auto-scan
- Updated `python_host/main.py` to run one automatic LAN device discovery pass at startup.
- Discovered devices are registered immediately so no manual scan click is required before emotion routing.

### 1) Backend integration in `python_host`
- Added `PerceptionModule` usage inside `python_host/ui/app.py`.
- Started perception only when camera starts (`_start_camera`).
- Stopped perception when camera stops (`_stop_camera`).
- Extended `/api/faces` response:
  - `perception`: model outputs (including `vit_emotion` when available)
  - `reactor`: smoothed flower state and command telemetry
- Extended `/api/perception/status` to include `vit` availability.

### 2) ViT emotion support
- Added `python_host/vision/vit_emotion.py`.
- Updated `python_host/vision/perception.py` to:
  - load optional ViT detector
  - emit `vit_emotion` payload with `dominant`, `confidence`, `scores`, `classes`

### 3) Emotion reactor
- Added `python_host/vision/emotion_reactor.py` with:
  - score pool + decay smoothing
  - enter threshold = `1.8`
  - exit threshold = `1.0`
  - min hold = `1500 ms`
  - command cooldown = `1200 ms`
  - no-face timeout = `2500 ms`
  - asymmetric dynamics:
    - `BLOOM/ALERT` gain is higher and supports burst-trigger transitions
    - `SOOTHE` gain is lower and defaults to longer hold for recovery
    - shock term amplifies high-confidence `BLOOM/ALERT` detections
  - runtime tuning support via `/api/reactor/config` (GET/POST)
- Flower state set:
  - `BLOOM`, `ALERT`, `SOOTHE`, `REST`
- Human-to-flower mapping:
  - `happy/surprise -> BLOOM`
  - `angry/fear/disgust -> ALERT`
  - `sad/neutral -> SOOTHE`
  - no face timeout -> `REST`

### 4) Node command mapping
Implemented in `EmotionReactor`:
- Sue:
  - `BLOOM -> /state relax`
  - `ALERT -> /state danger`
  - `SOOTHE -> /state calm`
  - `REST -> /state idle`
- Kait:
  - `BLOOM -> /motion 2 or 6` (round-robin)
  - `ALERT -> /motion 3 or 4` (round-robin)
  - `SOOTHE -> /motion 1 or 5` (round-robin)
  - `REST -> /stop`
- Sylvie:
  - `BLOOM -> /preset 1`
  - `ALERT -> /preset 2`
  - `SOOTHE -> /preset 3`
  - `REST -> /preset 3`

### 4.1) Multi-target emotion dispatch mode
- Reactor target source changed from single selected device to current checked device list.
- Added per-device routing selection in backend and UI:
  - `GET/POST /api/devices/emotion_targets`
- Behavior:
  - scanned + known in `device_registry.json` => auto-checked for emotion routing
  - scanned but unknown => not auto-checked
  - manual checkbox controls participation in emotion-driven OSC dispatch

### 4.2) Global emotion scheduling switch
- Added `GET/POST /api/reactor/override`.
- UI switch: `Emotion Override (Manual Takeover)`
  - ON => emotion scheduling active (default)
  - OFF => manual-only mode (emotion routing suspended)

### 4.3) Node Controls manual target binding
- Clicking node-type tabs now auto-selects a matching discovered device (by type, deterministic order by IP/port).
- Manual OSC commands in Node Controls therefore route to the correct selected device automatically.

### 5) UI update
Updated `python_host/ui/templates/index.html` with a compact "Flower Emotion" status block:
- state label + emoji
- source emotion + confidence
- 0-100 stability bar
- color per flower emotion (soothe green, alert red, bloom yellow, rest gray)

Added a full "Real-Time Emotion Analysis Table":
- sorted per-emotion score rows
- score bars for quick reading during demo
- model tag (`vit` or fallback source)

Added live "Emotion Reactor Tuning" sliders:
- enter/exit threshold, decay
- bloom/alert/soothe gains
- shock scale
- soothe hold time
- values sync to backend immediately (runtime only, no restart)

## Dependency updates
Updated `python_host/requirements-ml.txt`:
- `transformers>=4.30,<5.0`
- `torch>=2.0,<3.0`

## Tests updated
- Updated `python_host/tests/test_flask_app.py` to assert merged API keys (`perception`, `reactor`, `vit`).
- Updated `python_host/tests/test_perception.py` for `vit_emotion` and lazy ViT loading.
- Added `python_host/tests/test_emotion_reactor.py` for baseline reactor behavior and mapping coverage.

## Notes for demo
- This iteration prioritizes reliability and explainability over deep nonlinear mapping.
- Reactor is intentionally coarse and deterministic for showcase stability.
- Advanced sequence-conditioned mapping and LCD eye animation are left for post-showcase iteration.


# The Garden's Response - Portfolio Case Study

Chinese version: [PORTFOLIO_ZH.md](./PORTFOLIO_ZH.md)

## Overview

**The Garden's Response** is an interactive kinetic flower installation created for **DATT 3700: Collaborative Project Development** at York University. The project passed the final presentation and was selected for **YES!! - Year End Showcase!!** at InterAccess / Digital Media Year 2026: [Digital Media Gallery - YES!! Year End Showcase](https://dmgallery.apps01.yorku.ca/yes-year-end-showcase/).

The work combines a Python-based perception host, emotion AI, OSC networking, and a distributed network of ESP32 flower nodes. Human faces and expressions are detected by the host computer, translated into pooled "flower emotions", and routed to physical flowers as servo, DC motor, display, and preset motion commands.

> Public showcase description: "The Garden's Response is an interactive kinetic flower installation that integrates computer vision, emotion AI, and distributed hardware nodes. The system utilizes a central Python-based host to track human faces and analyze emotional states, translating these digital perceptions into physical movements across a network of ESP32-powered flower nodes."

## Project Links

- Showcase listing: [The Garden's Response on YES!! Year End Showcase](https://dmgallery.apps01.yorku.ca/yes-year-end-showcase/)
- Main repository: [dattodigm/DATT3700](https://github.com/dattodigm/DATT3700)
- Next-generation portfolio dashboard branch: [v0/kaminodice-06183338](https://github.com/dattodigm/DATT3700/tree/v0/kaminodice-06183338)
- GC9D01/TFT_eSPI display driver fork: [Arduino_GC9D01_Driver_TFT_eSPI_Lvgl](https://github.com/dattodigm/Arduino_GC9D01_Driver_TFT_eSPI_Lvgl)
- RGB565 eye preview/conversion tool: [EyeSeed](https://github.com/dattodigm/EyeSeed)
- ViT implementation reference: [yst002/EmotionDetector_deployment](https://github.com/yst002/EmotionDetector_deployment)
- Hosted ViT weights used by the project: [yst007/vit-emotion](https://huggingface.co/yst007/vit-emotion/tree/main)

## My Role

This was a team installation, but the final integrated software and control architecture were primarily my responsibility.

Collaborator-provided original firmware is preserved under:

- `esp32_firmware/original/esp32_sylvie/sylvie_origin.c`
- `esp32_firmware/original/esp32_kait/esp32_kait.ino`
- `esp32_firmware/original/Face_tracking`
- `esp32_firmware/original/esp32_sue`

My main contributions included:

- Python host application, Flask web dashboard, OSC routing, serial debugging, device discovery, and motion sequence recording.
- OpenCV face tracking and weighted multi-face target pooling.
- DeepFace emotion analysis integration.
- ViT emotion analysis integration, adapted from the referenced implementation and using the hosted `yst007/vit-emotion` weights.
- The "lossy integration" emotion reactor that accumulates, decays, thresholds, and routes human emotions into flower states.
- ESP32 firmware integration for node discovery, OSC command handling, serial fallback/debugging, AP/STA WiFi behavior, mDNS metadata, and physical-safe motion limits.
- Web dashboard UI/UX for node-specific debugging and control, including 2D pads for face tracking servos, Sylvie motor control, Sue bloom/eye control, raw OSC console, and sequence capture/playback.
- GC9D01 display driver porting, Uncanny Eyes/Animated_Eye reverse engineering, RGB565 conversion tooling, and face tracking integration for eye movement.
- Sue display tearing and memory fixes: moving from full-screen redraw to canvas buffering, then to partial sprite redraw after full-screen canvas memory overflow.

## System Architecture

```text
Camera / iPhone Continuity Camera
        |
        v
Python Host (Flask + OpenCV + optional ML)
        |
        |-- FaceTracker: Haar face detection, weighted multi-face centroid
        |-- PerceptionModule: DeepFace, MediaPipe placeholders, ViT emotion model
        |-- EmotionReactor: lossy integration, state transitions, OSC routing
        |-- Web Dashboard: live preview, controls, recorder, OSC console
        |
        v
OSC over WiFi / USB serial fallback
        |
        v
ESP32 Flower Nodes
        |
        |-- Sylvie: AP/gateway, DC motors, RGB LEDs, presets
        |-- Kait: DC motor speed/motion modes
        |-- Sue: servo bloom, GC9A01 eye, blink/breathe/track controls
        |-- Face Tracking Node: 8-servo pan/tilt flower cluster
        |-- Eye Anime Node: GC9D01/TFT_eSPI animated eye tracking
```

## Core Implementation

### Python Host and Dashboard

The main host lives in `python_host/`. It starts with:

```bash
python -m pip install -r python_host/requirements.txt
python -m python_host.main --port 15000
```

The Flask application in `python_host/ui/app.py` provides:

- Camera lifecycle management: start, stop, switch camera, and mirror-aware tracking.
- Device discovery through mDNS (`_datt_flower._tcp`, `_osc._udp`) and a gateway fallback query path.
- Node registry and type inference through `python_host/ui/device_registry.json`.
- Node-type-specific control panels for `sylvie`, `kait`, `sue`, `face_track`, and `eye_anime`.
- Raw OSC console with transmission history and auto-refresh.
- Sequence recorder and playback using `python_host/data/sequences/<label>`.
- OSC and serial transport selection for face tracking output.
- API compatibility routes for debugging, automated discovery, tracking configuration, perception status, and emotion reactor tuning.

### Face Tracking

`python_host/vision/face_tracker.py` uses OpenCV Haar detection as the real-time tracking baseline. It detects all visible faces, chooses the largest face as a primary target, and also computes an area-weighted centroid across all faces. The weighted target gave the installation smoother behavior when several visitors entered the camera view at once.

The tracking publisher in `python_host/network/coordinate_publisher.py` sends normalized coordinates at a configurable rate with deadband filtering. Coordinates can be routed as OSC `/track/norm` messages or as USB serial pixel coordinates for local debugging.

### Emotion AI

`python_host/vision/perception.py` runs optional ML modules in a background thread so the camera stream and UI remain responsive.

Implemented/connected perception paths:

- OpenCV face tracking for stable low-latency target extraction.
- DeepFace emotion inference for conventional facial expression analysis.
- ViT emotion inference through `python_host/vision/vit_emotion.py`, using the `yst007/vit-emotion` Hugging Face model.

Partially implemented or future-facing perception paths:

- MediaPipe face mesh and pose are loaded lazily, but richer gesture mapping was left as roadmap work.
- Eye tracking, VLM reasoning, and video-feedback training loops were intentionally not completed before portfolio freeze.

### Lossy Emotion Integration

The main behavior design is in `python_host/vision/emotion_reactor.py`. Instead of mapping every single emotion frame directly to motors, the reactor treats expression detection as a noisy signal.

The reactor:

- maps human emotions to flower emotions: `BLOOM`, `ALERT`, `SOOTHE`, `REST`;
- accumulates per-state scores using confidence-weighted increments;
- applies continuous decay so old observations fade away;
- uses enter/exit thresholds, hold times, shock scaling, burst transitions, and cooldowns;
- routes stable state changes to node-specific OSC commands.

This "lossy integration" approach made the physical installation feel less twitchy. A brief expression could still produce a dramatic reaction, but random classifier noise would usually be absorbed by decay, thresholds, and command cooldowns.

### ESP32 Firmware Nodes

The production firmware lives under `esp32_firmware/node/`.

Important nodes:

- `esp32_firmware/node/sylvie/sylvie_main/sylvie_main.ino`  
  AP-capable gateway-style node for Sylvie, with OSC, mDNS, client reporting, DC motor control, RGB LEDs, and presets.

- `esp32_firmware/node/sylvie/sylvie_client/sylvie_client.ino`  
  Companion Sylvie client node.

- `esp32_firmware/node/kait/kait_v2_en/kait_v2_en.ino`  
  Kait node firmware for DC motor speed, direction, motion modes, OSC control, and serial debugging.

- `esp32_firmware/node/sue/sue_main/sue_main.ino`  
  Sue node firmware combining servo-driven petal opening, GC9A01 eye drawing, OSC tracking, blink/breathe/pupil behavior, WiFi retry, mDNS, and serial diagnostics.

- `esp32_firmware/node/face_tracking/face_tracking.ino`  
  8-servo pan/tilt tracking firmware for a four-flower cluster, including smoothing, angle limits, manual/auto mode blending, OSC routes, mDNS metadata, and WiFi recovery.

- `esp32_firmware/node/gc9d01_eye/5.Animated_Eye12.ino`  
  GC9D01/TFT_eSPI Animated_Eye-style firmware extended with OSC tracking and animation modes.

The firmware emphasizes practical installation reliability: bounded servo travel, non-blocking updates, network retry behavior, serial command fallbacks, `/info/self` and `/info/servo` diagnostics, mDNS metadata, and raw OSC interoperability.

### Display and RGB565 Tools

The display pipeline was a separate technical track. I ported and tested GC9D01/TFT_eSPI behavior, reverse engineered Animated_Eye-style assets, and created conversion/preview tools to reduce iteration time.

Relevant local tooling:

- `tools/images_to_rgb565_header.py` converts image sequences into RGB565 `PROGMEM` headers.
- `tools/h_to_gif_preview.py` parses RGB565 C headers and previews or exports animated GIFs.

Related public repositories:

- [EyeSeed](https://github.com/dattodigm/EyeSeed): browser previewer for RGB565/Uncanny Eyes-style headers.
- [Arduino_GC9D01_Driver_TFT_eSPI_Lvgl](https://github.com/dattodigm/Arduino_GC9D01_Driver_TFT_eSPI_Lvgl): GC9D01/TFT_eSPI driver work and examples.

## Web Dashboard Design Notes

The live Flask dashboard is intentionally practical rather than decorative. It was built for debugging hardware during installation setup, rehearsal, and final showcase.

Notable UI/UX details:

- Live mirrored camera preview with tracking X inversion, matching how visitors expect camera movement to behave.
- iOS-camera-inspired 2D control panels for horizontal/vertical face tracking servo motion.
- Sylvie controls for signed DC motor speed, jitter-like motion, emergency stop, and 2D drive pad behavior.
- Sue controls for flower open percentage, speed, eye open amount, gaze pad, eye limits, blink/breathe toggles, and pupil automation.
- Kait controls for direct motor speed and preset motion modes.
- Emotion reactor tuning presets for safe, balanced, and dramatic behavior during testing.
- Device discovery UI with mDNS, gateway scanning, manual target add, and per-node emotion routing.
- Raw OSC console and history log for fast command-level debugging.
- Motion sequence recorder for collecting labeled action data and replayable choreography.

The separate Next.js/v0 branch is intended as the polished portfolio-facing dashboard: [v0/kaminodice-06183338](https://github.com/dattodigm/DATT3700/tree/v0/kaminodice-06183338). It is suitable for website presentation, but it was not merged into the production Flask routes because full integration testing would have risked breaking the stable showcase system.

## Showcase Reliability Story

During the public showcase, the hidden laptop workstation overheated inside the display box and shut down on the second day. Because the system used a modular host/node architecture, the installation recovered quickly:

1. A backup MacBook joined the same flower WiFi mesh/network.
2. The Python host and web dashboard were restarted from the backup machine.
3. iPhone Continuity Camera was used as the camera input and hidden among the decorative grass/flower elements.
4. The ESP32 nodes continued to receive OSC commands without firmware changes.

This incident validated one of the most important engineering choices in the project: the "brain" could move to another host computer without reflashing or rewiring the distributed flower nodes.

## Repository Map

```text
DATT3700/
|-- python_host/
|   |-- main.py                         # Host entry point
|   |-- README.md                       # Host setup and API notes
|   |-- ui/
|   |   |-- app.py                      # Flask dashboard and APIs
|   |   |-- templates/index.html        # Control panel UI
|   |   |-- device_registry.json        # Node types and known devices
|   |   `-- static/panel-fallback.css
|   |-- vision/
|   |   |-- face_tracker.py             # OpenCV face tracking
|   |   |-- perception.py               # DeepFace / ViT / MediaPipe hooks
|   |   |-- vit_emotion.py              # Hugging Face ViT detector
|   |   `-- emotion_reactor.py          # Lossy emotion pooling and routing
|   |-- network/
|   |   |-- osc_sender.py               # OSC target management and history
|   |   |-- node_discovery.py           # mDNS and gateway discovery
|   |   |-- coordinate_publisher.py     # Tracking coordinate transport
|   |   `-- serial_sender.py            # USB serial coordinate/debug path
|   `-- tests/
|
|-- esp32_firmware/
|   |-- node/
|   |   |-- sylvie/
|   |   |-- kait/
|   |   |-- sue/
|   |   |-- face_tracking/
|   |   `-- gc9d01_eye/
|   |-- original/                       # Collaborator-provided original sketches
|   `-- refactor_example/               # Earlier abstraction experiments
|
|-- tools/
|   |-- images_to_rgb565_header.py
|   `-- h_to_gif_preview.py
|
`-- docs/
    |-- PORTFOLIO_EN.md
    |-- PORTFOLIO_ZH.md
    `-- deprecated/                     # Earlier course delivery docs
```

## Technical Challenges and Solutions

| Challenge | Solution |
|---|---|
| Emotion inference was noisy and not always semantically stable. | Built a lossy integration reactor with decay, thresholds, hold times, shock scaling, and cooldowns. |
| Multi-face tracking could jump between visitors. | Used weighted centroid pooling and primary-face overlay for stable targeting. |
| ESP32 nodes had different hardware capabilities and command shapes. | Added a node registry, node-type-aware dashboard rendering, and per-node OSC routing. |
| Debugging WiFi devices during exhibition setup was slow. | Added mDNS discovery, gateway fallback scanning, raw OSC history, `/info/self`, `/info/servo`, and serial fallbacks. |
| Display redraw caused tearing on the Sue node. | Reworked drawing through canvas buffering and then partial sprite redraw to fit memory constraints. |
| Full-screen canvas overflowed ESP32 memory. | Reduced the redraw region and used smaller sprite/canvas patches. |
| The hidden host computer overheated during showcase. | Moved the host process to a backup MacBook and reused the same ESP32 network and camera pipeline. |

## Current Status

Stable enough for final presentation and public showcase:

- Face tracking, web dashboard, OSC routing, and serial debugging are working.
- Emotion analysis through DeepFace and ViT is integrated.
- Flower emotion pooling and routing are implemented.
- Sylvie, Kait, Sue, face tracking, and eye animation nodes have usable production sketches.
- Motion sequence recording and replay are implemented in the dashboard.
- Display tooling and RGB565 workflow are functional.

Not merged / intentionally frozen:

- The modern Next.js dashboard branch is portfolio-facing only and has not been fully tested against the Flask backend.
- MediaPipe gesture-to-motion mapping remains a prototype direction.
- Firmware abstraction was explored but not fully consolidated across every node.

## Roadmap

Future work that I would pursue only if turning this from a course installation into a longer-term platform:

- Dual or multi-camera control.
- Group jealousy / swarm affect algorithms for multi-flower social behavior.
- More emotion/action sequence collection for future ML training.
- Firmware abstraction and stronger shared node modules.
- Leaner and more stable mesh/AP networking, potentially ESP-NOW or a lower-latency replacement for the current OSC path.
- MediaPipe pose and gesture mapping for richer body-to-flower interaction.
- Eye-tracking algorithms and gaze-duration-driven behavior.
- Fast/slow brain architecture: real-time tracking plus slower high-level reasoning.
- VLM integration over serialized frame sequences or tiled visual summaries.
- Closed-loop video feedback for autonomous debugging, training, and behavior refinement.
- Full integration of the polished Next.js dashboard with the Python host APIs.

## Resume-Ready Summary

**The Garden's Response - Interactive AI Flower Installation**  
Built the integrated Python/ESP32 control architecture for a public-showcased kinetic flower installation selected for York Digital Media's YES!! Year End Showcase. Implemented a Flask hardware dashboard, OpenCV face tracking, DeepFace/ViT emotion analysis, lossy emotion-state pooling, OSC/WiFi control routing, serial debug tooling, ESP32 firmware integration, and RGB565/GC9D01 display workflows across multiple motorized flower nodes.

Suggested resume bullets:

- Architected a distributed ESP32 + Python control system for a public interactive installation, connecting OpenCV face tracking and emotion AI to servo, DC motor, and TFT display nodes over OSC/WiFi.
- Designed a lossy emotion integration algorithm that pooled noisy DeepFace/ViT predictions into stable flower states (`BLOOM`, `ALERT`, `SOOTHE`, `REST`) with decay, thresholds, hold times, and per-node command routing.
- Built a Flask-based hardware dashboard with live camera preview, mDNS/gateway device discovery, raw OSC console, node-specific 2D control pads, motion sequence recording, and serial fallback debugging.
- Ported and optimized ESP32 display animation workflows for GC9D01/GC9A01 screens, including RGB565 conversion tools, Animated_Eye-style firmware integration, and partial redraw fixes for tearing and memory limits.

## Credits

Team project by Emma Su, Huanrui Cao, Kaitlyn Ly, Sawsan Al Sharafa, and Xiwei Ma.

External references:

- ViT implementation reference: [yst002/EmotionDetector_deployment](https://github.com/yst002/EmotionDetector_deployment)
- ViT weights: [yst007/vit-emotion](https://huggingface.co/yst007/vit-emotion/tree/main)
- Animated eye and TFT display work builds on the broader Adafruit Uncanny Eyes and TFT_eSPI ecosystem, adapted for this project through the local firmware and tooling listed above.

# DATT3700 Project - AI Agent Development Handbook

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Architecture Principles](#core-architecture-principles)
3. [Hardware Topology](#hardware-topology)
4. [Development Constraints](#development-constraints)
5. [Implementation Roadmap](#implementation-roadmap)
6. [API & Communication Protocols](#api--communication-protocols)

---

## Project Overview

**Objective**: Interactive flower installation with computer vision tracking and multi-node ESP32 control system.

**Key Components**:
- 4 Flower nodes (Sylvie - 2 ESP32s to 4 DC motors,each ESP32 connected to 2 DC motors)
- 1 Face tracking node (Pan-tilt servos, 1 ESP32 Connected to 8 servos, 2 servos pair for one  flowers' X/Y)
- 1 Close/open flower node (Sue - 1 esp32 with 1 servo)
- 1 Rotating flower node (Kait - 1 esp32 with 1 servo - not upload the firmware code yet)
- Python host computer with OpenCV/DeepFace/MediaPipe perception stack
- Flask-based web control panel

---

## Core Architecture Principles

### 1. Absolute Decoupling ⭐⭐⭐
**Priority**: CRITICAL

- ESP32 firmware ↔ Python host communication via **UDP/OSC** or **JSON over HTTP** only
- Serial commands reserved for debugging ONLY (wrap as unified interface)
- No direct hardware dependencies between systems

### 2. MVP First ⭐⭐⭐
**Priority**: CRITICAL

- Implement core state machine and hardware drivers first
- NO unnecessary third-party libraries
- NO complex deep learning models unless explicitly requested
- Validate each step before proceeding

### 3. Documentation-Driven ⭐⭐
**Priority**: HIGH

- Update API docs based on working code ONLY
- NO speculative interfaces
- Reserve expansion interfaces (TFT display, etc.)

---

## Hardware Topology

### Ground Truth Reference
The files in `esp32_firmware/` is the **only verified source of truth**:
- `esp32_sue/sue_new.ino, servo.ino`- Close/open flower
- `esp32_sylvie/` - Cluster flowers
- `Face_tracking/Face_tracking.ino` - Pan-tilt tracking

### Node Specifications

| Node Name | ESP32 Count | Actuators | Function | Constraints |
|-----------|-------------|-----------|----------|-------------|
| **Sylvie** (Cluster) | 2 total | 2× DC motors per ESP32 (4 flowers each) | Flower cluster movement | Total: 8 flowers |
| **Face Tracking** (Pan-Tilt) | 1 | 8× Servos (4 pairs X/Y axis) | Flower direction tracking | ⚠️ X/Y axis ≤360° (prevent cable twist) |
| **Sue** (Close/Open) | 1 | 1× Servo | Petal open/close | Single flower |
| **Kait** (Rotation) | 1 | 1× Servo | Flower rotation | Single flower |

**Total ESP32 Nodes**: 5

---

## Development Constraints

### Firmware (ESP32) - MANDATORY

#### ⛔ NON-NEGOTIABLE Rules

1. **NO Blocking Code** ⭐⭐⭐
```cpp
   // FORBIDDEN: delay() anywhere in loop() or logic
   // REQUIRED: millis()-based state machines for all timing
   ```
2. **Object-Oriented Design** ⭐⭐
   - Abstract all hardware nodes as classes
   - Implement common base class (e.g., `FlowerNode`)
   - Unified network receive + hardware update interfaces

3. **Memory Safety** ⭐⭐
   ```cpp
   // FORBIDDEN: String concatenation in loops
   // FORBIDDEN: malloc/new in runtime
   // PREFERRED: Fixed-size char arrays, StaticJsonDocument
   ```
4. **Network Discovery** ⭐⭐
   - Implement mDNS broadcast: `_datt_flower._tcp`
   - Enable automatic host computer discovery

### Python Host Computer - MANDATORY

#### ⛔ NON-NEGOTIABLE Rules

1. **Environment Isolation** ⭐⭐
   - Lock ALL dependency versions in `requirements.txt`
   - No global package assumptions

2. **Thread Safety** ⭐⭐⭐
   ```python
   # REQUIRED SEPARATION:
   # - Vision thread (OpenCV/MediaPipe/DeepFace)
   # - Network thread (OSC/UDP/HTTP)
   # - UI rendering thread (Flask)
   
   # FORBIDDEN: Vision inference blocking UI or network send
   # REQUIRED: Thread-safe data exchange (queue.Queue or locked dict)
   ```
3. **UI Framework** ⭐⭐
   - UI Framework & Aesthetics ⭐⭐ 
     - REQUIRED Core: Flask + pure HTML/JS (Vanilla JS). 
     - FORBIDDEN: React, Vue, npm, node_modules, Webpack, or any build pipelines. 
     - ALLOWED UI Libraries (via CDN ONLY):
       - Tailwind CSS (via play CDN) for modern, clean dashboard styling (rounded corners, shadows, flex/grid layouts). 
       - Chart.js (via CDN) for rendering the live emotion graph. 
       - Custom Vanilla JS for the 2D "Flower Pad" touch area and slider inputs. Make it look professional and sleek.

---

## Implementation Roadmap

### Phase 1: Foundation (MVP) ⭐⭐⭐

#### Firmware Tasks
- [ ] **FW-1.1**: Abstract `WiFiManager` class
  - Configurable AP/STA mode via `config.h`
  - AP mode: Minimal HTTP server OR serial output for topology info
  
- [ ] **FW-1.2**: Motion command abstraction
  - Unified OSC/UDP/WiFi command interface
  - Parameters: angle, speed, jitter, LED color, sequence, pan-tilt coordinates, etc. if the hardware support

#### Host Computer Tasks
- [ ] **HC-1.1**: Extend face tracking MVP
  - Multi-face weighted tracking
  - Weight formula: `area × center_proximity`
  - NO heavy deep learning libraries at this stage

### Phase 2: Perception Stack ⭐⭐

#### Host Computer Tasks
- [ ] **HC-2.1**: Progressive perception modules
  - DeepFace/ViT → emotion, gender, age extraction
  - MediaPipe → pose extraction
  - Color analysis → environment/subject color summary
  
- [ ] **HC-2.2**: Flask control panel
  - **Left panel**: Camera preview + data OSD
  - **Right panel**: iOS-style 2D slider controls
    - Manual override: open/close, lighting, speed, pan-tilt, etc.
    - Data labeling for vision decision training (CV data ↔ Flower Personality ↔ Flower Behavior sequences and attributes)
  
- [ ] **HC-2.3**: Resolve resource conflicts
  - Manual UI control ↔ Auto-tracking priority handling

### Phase 3: Advanced Behavior ⭐

#### Host Computer Tasks
- [ ] **HC-3.1**: Multi-perception data fusion
  - Non-linear mapping to flower emotional output
  
- [ ] **HC-3.2**: "Jealousy" group algorithm
  ```python
  # Example behavior:
  # IF target_A gazed_too_long:
  #   → Other flowers enter "competition" mode (high-frequency movement)
  #   OR "sulking" mode (close + no response)
  ```
### Phase 4: Expansion Interfaces ⭐

#### Reserved Features
- TFT IPS display integration (eye animation control or information displayer)
- Additional sensor inputs
- Extended network protocols

---

## API & Communication Protocols

### Network Commands Structure

All motion commands should follow this pattern (just a example, should be modified according to the real physical hardware)

```json
{
  "node_id": "sylvie_1",
  "command": "move",
  "params": {
    "angle": 45,
    "speed": 0.5,
    "jitter": 0.1,
    "led_color": [255, 0, 0],
    "duration_ms": 1000
  }
}
```
### Command Types (To Be Implemented)  (just a example, should be modified according to the real physical hardware)

| Command Category | Parameters | Target Nodes |
|-----------------|------------|--------------|
| **Open/Close** | angle, speed | Sue, Sylvie |
| **Direction** | pan_angle, tilt_angle | Face Tracking |
| **Rotation** | angle, continuous_flag | Kait |
| **Lighting** | RGB color, brightness | All nodes |
| **Sequence** | order_index, timing | Sylvie cluster |
| **Emotion Macro** | emotion_type, intensity | All nodes |

### mDNS Service Discovery

- **Service Type**: `_datt_flower._tcp`
- **TXT Records**: 
  - `node_type=<sylvie|sue|kait|face_track>`
  - `firmware_version=<semver>`
  - `capabilities=<comma-separated list>`

---

## File Structure Reference

```
esp32_firmware/
├── esp32_sylvie/       # Cluster flower control (×2 ESP32)
├── esp32_sue/          # Close/open flower (×1 ESP32)
├── esp32_kait/         # Rotation flower (×1 ESP32) [TO CREATE]
└── Face_tracking/      # Pan-tilt tracking (×1 ESP32)

[Host Computer - TO CREATE]
python_host/
├── requirements.txt    # Locked dependencies
├── vision/             # Computer vision modules
├── network/            # OSC/UDP/HTTP handlers
├── ui/                 # Flask web interface
└── main.py             # Entry point
```

---

## Quick Reference for AI Agents

### When Generating Code, ALWAYS Check:

1. ✅ Does this violate the **no-blocking** rule?
2. ✅ Is this the **simplest working solution** (MVP)?
3. ✅ Does this match existing **verified firmware** capabilities?
4. ✅ Are threads properly **isolated and synchronized**?
5. ✅ Is the **API documented** based on actual implementation?

### Priority Levels

- ⭐⭐⭐ **CRITICAL**: Never violate these constraints
- ⭐⭐ **HIGH**: Follow unless explicitly overridden
- ⭐ **NORMAL**: Recommended best practices

### Contact Points for Clarification

If hardware capability is uncertain:
1. Check existing firmware in `esp32_firmware/`
2. Verify against physical topology table above
3. Ask user before assuming new features



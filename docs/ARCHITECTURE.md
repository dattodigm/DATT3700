# System Architecture

## Overview

The Vision PID Control System consists of three main components:

1. **Vision Processing** (Python + OpenCV)
2. **Control Algorithm** (PID Controller)
3. **Hardware Control** (ESP32 + OSC)

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Computer System                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         Vision Processing Module                │    │
│  │                                                  │    │
│  │  ┌──────────┐    ┌────────────────────────┐   │    │
│  │  │  Camera  │───→│  OpenCV Processing     │   │    │
│  │  │  Input   │    │  - Face Detection      │   │    │
│  │  └──────────┘    │  - Color Detection     │   │    │
│  │                   │  - Error Calculation   │   │    │
│  │                   └────────────┬───────────┘   │    │
│  └─────────────────────────────────┼──────────────┘    │
│                                     │                    │
│                                     │ (x_error, y_error) │
│                                     ▼                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │          PID Control Module                      │   │
│  │                                                   │   │
│  │  ┌──────────────┐        ┌──────────────┐      │   │
│  │  │  PID Pan     │        │  PID Tilt    │      │   │
│  │  │  Controller  │        │  Controller  │      │   │
│  │  │              │        │              │      │   │
│  │  │  Kp, Ki, Kd  │        │  Kp, Ki, Kd  │      │   │
│  │  └──────┬───────┘        └──────┬───────┘      │   │
│  │         │                        │               │   │
│  │         │ pan_correction        │ tilt_correction│  │
│  │         └────────┬───────────────┘               │   │
│  └──────────────────┼────────────────────────────  │   │
│                      │                                   │
│                      │ (servo_angles, flower_state)      │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │         OSC Communication Module                 │   │
│  │                                                   │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  UDP Client (python-osc)                  │  │   │
│  │  │  - /flower/servo  [pan, tilt]            │  │   │
│  │  │  - /flower/state  [openness]             │  │   │
│  │  │  - /flower/motor  [speed]                │  │   │
│  │  │  - /flower/mode   [tracking]             │  │   │
│  │  └──────────────────┬───────────────────────┘  │   │
│  └─────────────────────┼──────────────────────────┘   │
└─────────────────────────┼────────────────────────────  ┘
                          │
                          │ WiFi/UDP
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     ESP32 System                         │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         WiFi + OSC Server Module                 │   │
│  │                                                   │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  UDP Server (OSC Library)                 │  │   │
│  │  │  Listens on port 8000                     │  │   │
│  │  │  Parses OSC messages                      │  │   │
│  │  └──────────────────┬───────────────────────┘  │   │
│  └─────────────────────┼──────────────────────────┘   │
│                         │                               │
│                         │ (commands)                    │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Hardware Control Module                  │   │
│  │                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ Servo Driver │  │ Motor Driver │            │   │
│  │  │              │  │              │            │   │
│  │  │ GPIO 18, 19  │  │ GPIO 25-27   │            │   │
│  │  └──────┬───────┘  └──────┬───────┘            │   │
│  └─────────┼──────────────────┼────────────────────┘   │
│             │                  │                         │
└─────────────┼──────────────────┼────────────────────────┘
              │                  │
              ▼                  ▼
      ┌──────────────┐   ┌──────────────┐
      │   Servos     │   │   DC Motor   │
      │  (Pan/Tilt)  │   │  (Flower)    │
      └──────────────┘   └──────────────┘
```

## Data Flow

### 1. Vision Processing Flow

```
Camera Frame (640x480 BGR)
        │
        ▼
    Preprocessing
    (flip, grayscale)
        │
        ▼
┌───────┴────────┐
│                │
▼                ▼
Face Detection   Color Detection
(Haar Cascade)   (HSV Masking)
│                │
└───────┬────────┘
        │
        ▼
   Target Center (x, y)
        │
        ▼
   Calculate Error
   error_x = target_x - center_x
   error_y = target_y - center_y
```

### 2. PID Control Flow

```
Error Input
    │
    ▼
┌────────────────┐
│ Calculate:     │
│                │
│ P = Kp × error │
│ I = Ki × ∫error│
│ D = Kd × d/dt  │
└───────┬────────┘
        │
        ▼
    output = P + I + D
        │
        ▼
    Clamp to limits
        │
        ▼
    Correction Value
```

### 3. Communication Flow

```
Python (Client)              ESP32 (Server)
     │                            │
     │  OSC /flower/servo         │
     │  [90, 90]                  │
     ├───────────────────────────→│
     │                            │
     │                      Parse OSC
     │                            │
     │                     Set Servo Angles
     │                        servo.write()
     │                            │
     │  (Next command...)         │
     ├───────────────────────────→│
```

## Module Details

### Python Controller Modules

#### `vision_tracker.py`
- **Purpose**: Object detection and tracking
- **Classes**:
  - `VisionTracker`: Base class
  - `FaceTracker`: Haar Cascade face detection
  - `ColorTracker`: HSV color-based tracking
- **Output**: (x_error, y_error, detected)

#### `pid_controller.py`
- **Purpose**: Error correction algorithm
- **Algorithm**: Proportional-Integral-Derivative control
- **Features**:
  - Anti-windup
  - Output limiting
  - Sample time control
- **Output**: correction value

#### `osc_client.py`
- **Purpose**: Network communication with ESP32
- **Protocol**: OSC over UDP
- **Commands**:
  - Servo control
  - Flower state
  - Motor speed
  - Tracking mode

#### `main.py`
- **Purpose**: Main application loop
- **Responsibilities**:
  - Initialize all modules
  - Run control loop
  - Handle user input
  - Display feedback

### ESP32 Firmware Modules

#### WiFi Module
- Connect to network
- Obtain IP address via DHCP
- Maintain connection

#### OSC Server Module
- Listen on UDP port 8000
- Parse OSC messages
- Route to handlers

#### Servo Control Module
- ESP32Servo library
- PWM generation (50Hz)
- Position control (0-180°)

#### Motor Control Module
- H-bridge driver control
- PWM speed control
- Direction control

## Timing and Performance

### Python Controller

| Component | Rate | Latency |
|-----------|------|---------|
| Camera Capture | 30 FPS | ~33ms |
| Vision Processing | 30 FPS | ~10-30ms |
| PID Update | 33 Hz | <1ms |
| OSC Send | As needed | <5ms |

**Total Loop Time**: ~50-70ms (15-20 FPS effective)

### ESP32 Firmware

| Component | Rate | Response |
|-----------|------|----------|
| WiFi Poll | Continuous | <1ms |
| OSC Parse | On packet | <1ms |
| Servo Update | Immediate | ~20ms (servo) |
| Motor Update | Immediate | <1ms (PWM) |

**Network Latency**: 5-20ms on local WiFi

### End-to-End Latency

```
Camera → Processing → PID → OSC → Network → ESP32 → Servo
 33ms      20ms       1ms    5ms    10ms     1ms     20ms

Total: ~90ms (acceptable for human tracking)
```

## State Management

### Python Controller State

```python
{
    'tracking_active': bool,      # Is tracking enabled?
    'pan_angle': float (0-180),   # Current pan position
    'tilt_angle': float (0-180),  # Current tilt position
    'flower_openness': float (0-1), # Flower open state
    'lost_target_time': float,    # When target was lost
}
```

### ESP32 State

```cpp
{
    currentPanAngle: int (0-180),
    currentTiltAngle: int (0-180),
    currentFlowerState: float (0.0-1.0),
    currentMotorSpeed: int (-100 to 100),
    trackingMode: bool
}
```

## Error Handling

### Python Controller

```
Try:
    Capture frame
    Process vision
    Calculate PID
    Send OSC
Except:
    Camera error → Retry or exit
    Network error → Log and continue
    Keyboard interrupt → Clean shutdown
```

### ESP32

```
If OSC parse error:
    Log to Serial
    Continue (ignore bad packet)

If servo/motor error:
    Log to Serial
    Continue (may need hardware reset)
```

## Configuration Parameters

### PID Tuning Parameters

Located in `config.ini`:

```ini
[PID_Pan]
kp = 0.15          # Responsiveness
ki = 0.01          # Steady-state error correction
kd = 0.05          # Oscillation damping
output_limit = 30  # Max angle change per update

[PID_Tilt]
kp = 0.15
ki = 0.01
kd = 0.05
output_limit = 30
```

### Vision Parameters

```ini
[Tracking]
tracker_type = face  # or 'color'

[ColorTracking]
lower_hsv = 0, 120, 70    # Red color range
upper_hsv = 10, 255, 255
```

### Network Parameters

```ini
[Network]
esp32_ip = 192.168.1.100
esp32_port = 8000
```

## Scalability and Extensions

### Adding New Trackers

Extend `VisionTracker` base class:

```python
class MyTracker(VisionTracker):
    def get_tracking_error(self, frame):
        # Implement custom tracking
        return (x_error, y_error, detected)
```

### Adding New Behaviors

Modify `FlowerControlSystem.run()` in `main.py`:

```python
if detected:
    # Custom behavior here
    if distance < threshold:
        self.flower_openness = 1.0
```

### Multiple Flowers

Create multiple OSC clients:

```python
flower1 = FlowerOSCClient("192.168.1.100", 8000)
flower2 = FlowerOSCClient("192.168.1.101", 8000)
```

### Advanced Vision

Replace trackers with ML models:
- MediaPipe for pose detection
- YOLO for object detection
- OpenPose for body tracking

## Security Considerations

### Network Security

- OSC over UDP is unencrypted
- Use on trusted networks only
- Consider VPN for remote access
- Firewall rules to limit access

### Physical Safety

- Limit servo speed (output_limits)
- Limit servo range (0-180° clamping)
- Emergency stop mechanism
- Physical limit switches

## Performance Optimization

### Python

1. **Reduce resolution**: 320x240 for faster processing
2. **Skip frames**: Process every Nth frame
3. **Optimize detection**: Reduce search region
4. **Multi-threading**: Separate capture and processing

### ESP32

1. **Servo updates**: Only when angle changes
2. **Motor smoothing**: Ramp speed changes
3. **WiFi optimization**: Static IP (faster than DHCP)
4. **Minimize Serial**: Reduce debug output

## Testing Strategy

### Unit Tests

- `test_pid.py`: PID algorithm correctness
- Individual module tests

### Integration Tests

- `test_osc.py`: Network communication
- `test_vision.py`: Camera and tracking

### System Tests

- Full system with manual control
- Live tracking performance
- Stress testing (rapid movements)

## Debugging

### Enable Verbose Logging

Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

ESP32:
```cpp
// In loop(), add:
Serial.print("Pan: ");
Serial.println(currentPanAngle);
```

### Common Debug Points

1. **Vision**: Display detected regions
2. **PID**: Log error and output values
3. **Network**: Monitor packet transmission
4. **Servos**: Verify angle commands
5. **Timing**: Measure loop frequencies

## Performance Metrics

Track these for optimization:

- **Frame Rate**: Target 20+ FPS
- **Detection Rate**: Target 90%+ when object visible
- **Response Time**: Target <100ms end-to-end
- **Tracking Accuracy**: Target ±5 pixels error
- **Servo Smoothness**: No visible jitter

## Future Enhancements

1. **Machine Learning**: Train custom object detector
2. **Multi-target**: Track multiple objects
3. **Predictive Control**: Anticipate movements
4. **Adaptive PID**: Auto-tune based on performance
5. **Web Interface**: Browser-based control panel
6. **Data Logging**: Record and analyze sessions
7. **Voice Control**: Add speech recognition
8. **Mobile App**: Android/iOS control

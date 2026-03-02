# Digital Bloom — Documentation

Interactive flower sculpture installation controlled by emotion recognition and pose estimation.

## Docs Index

| File | Description |
|------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Get running in 5 minutes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design & data flow |
| [WIRING.md](WIRING.md) | ESP32 hardware connections |
| [TUNING.md](TUNING.md) | ML training & persona tuning |

## Hardware Overview

Two types of physical flower sculptures:

- **Sylvie** (`esp32_sylvie`): DC-motor driven petals + RGB LED, WiFi AP mode
- **Sue** (`esp32_sue`): Servo-driven petals + ultrasonic proximity sensor

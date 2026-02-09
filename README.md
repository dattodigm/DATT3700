# DATT3700 - Vision PID Control System for ESP32 Flower

A real-time vision tracking system using OpenCV, PID control, and OSC communication to control an ESP32-driven 3D-printed flower that follows users.

## 🌸 Features

- **Computer Vision Tracking**: Face detection (Haar Cascade) or color-based object tracking
- **PID Control Algorithm**: Smooth, precise servo movements with tunable parameters
- **Wireless Communication**: OSC over UDP for real-time control commands
- **Interactive Flower**: Opens when target detected, closes when target lost
- **Hardware Control**: ESP32-based servo and motor control system

## 🚀 Quick Start

### Python Controller Setup

```bash
cd python_controller
pip install -r requirements.txt
```

### ESP32 Firmware Setup

1. Install Arduino IDE and ESP32 board support
2. Install libraries: `ESP32Servo`, `OSC`
3. Update WiFi credentials in `esp32_firmware/flower_control.ino`
4. Upload to ESP32 and note the IP address

### Run the System

```bash
python python_controller/main.py --tracker face --ip YOUR_ESP32_IP
```

## 📖 Documentation

- **[User Guide](docs/README.md)**: Complete usage instructions and system architecture
- **[Wiring Guide](docs/WIRING.md)**: Hardware connections and assembly
- **[PID Tuning Guide](docs/TUNING.md)**: How to optimize tracking performance

## 🎮 Controls

| Key | Action |
|-----|--------|
| SPACE | Toggle tracking on/off |
| O | Open flower |
| C | Close flower |
| R | Reset servos to center |
| Q | Quit |

## 🔧 Hardware Requirements

- ESP32 development board
- 2× Servo motors (pan/tilt)
- DC motor with driver (L298N or TB6612FNG)
- USB webcam or built-in camera
- 5V and 12V power supplies
- 3D-printed flower mechanism

## 📁 Project Structure

```
DATT3700/
├── python_controller/      # Python vision and control system
│   ├── main.py            # Main application
│   ├── pid_controller.py  # PID algorithm
│   ├── vision_tracker.py  # Face/color tracking
│   ├── osc_client.py      # OSC communication
│   └── requirements.txt   # Dependencies
├── esp32_firmware/        # ESP32 Arduino sketch
│   └── flower_control.ino # Motor and servo control
└── docs/                  # Documentation
    ├── README.md          # User guide
    ├── WIRING.md         # Hardware setup
    └── TUNING.md         # PID tuning
```

## 🎓 Course Project

Built for DATT3700 - Interactive Art and Technology

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

This is a course project for educational purposes.
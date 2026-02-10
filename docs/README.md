# Vision PID Control System for ESP32 Flower

A real-time vision tracking system that uses OpenCV to detect faces or colored objects, applies PID control to calculate corrections, and sends commands to an ESP32-controlled 3D-printed flower via OSC over UDP.

## Features

- **Vision Tracking**: Face detection (Haar Cascade) or color tracking (HSV)
- **PID Control**: Smooth servo movements with tunable PID parameters
- **OSC Communication**: Real-time UDP commands to ESP32
- **Interactive Control**: Keyboard controls for manual operation
- **Flower Behavior**: Opens when target detected, closes when target lost

## System Architecture

```
┌─────────────────────┐
│   Camera Input      │
│   (OpenCV)          │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  Vision Tracker     │
│  (Face/Color)       │
└──────────┬──────────┘
           │ Error (x, y)
           v
┌─────────────────────┐
│  PID Controller     │
│  (Pan & Tilt)       │
└──────────┬──────────┘
           │ Corrections
           v
┌─────────────────────┐
│   OSC Client        │
│   (UDP)             │
└──────────┬──────────┘
           │ Commands
           v
┌─────────────────────┐
│   ESP32             │
│   (WiFi/OSC)        │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  Servos & Motors    │
│  (Flower Control)   │
└─────────────────────┘
```

## Hardware Requirements

### Computer Side
- Computer with USB webcam or built-in camera
- Python 3.7 or higher
- WiFi connection to same network as ESP32

### ESP32 Side
- ESP32 development board
- 2x Servo motors (for pan/tilt)
- 1x DC motor with motor driver (L298N or similar)
- Power supply (5V for servos, appropriate voltage for motor)
- 3D-printed flower mechanism

## Installation

### Python Controller

1. Navigate to the `python_controller` directory:
```bash
cd python_controller
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

### ESP32 Firmware

1. Install Arduino IDE or PlatformIO
2. Install required libraries:
   - ESP32Servo
   - OSC (for ESP32)
   - WiFi (included with ESP32 board)

3. Open `esp32_firmware/flower_control.ino`
4. Update WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

5. Connect hardware according to wiring diagram (see below)
6. Upload to ESP32
7. Note the IP address shown in Serial Monitor

## Hardware Wiring

### ESP32 Pin Connections

```
ESP32 GPIO 18 ──→ Pan Servo Signal
ESP32 GPIO 19 ──→ Tilt Servo Signal
ESP32 GPIO 25 ──→ Motor Driver IN1
ESP32 GPIO 26 ──→ Motor Driver IN2
ESP32 GPIO 27 ──→ Motor Driver ENABLE (PWM)

ESP32 GND ──→ Common Ground
ESP32 5V  ──→ Servo Power (if using ESP32 power)
```

### Motor Driver (L298N Example)

```
IN1 ──→ GPIO 25
IN2 ──→ GPIO 26
ENA ──→ GPIO 27 (PWM)
OUT1, OUT2 ──→ DC Motor
12V+ ──→ Motor power supply
GND ──→ Common ground
```

### Servos

```
Pan Servo:
  - Signal ──→ GPIO 18
  - VCC ──→ 5V
  - GND ──→ GND

Tilt Servo:
  - Signal ──→ GPIO 19
  - VCC ──→ 5V
  - GND ──→ GND
```

## Usage

### Basic Usage

1. Ensure ESP32 is powered on and connected to WiFi
2. Update `config.ini` with your ESP32's IP address
3. Run the controller:

```bash
python main.py --tracker face --ip 192.168.1.100
```

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --tracker {face,color}  Tracking mode (default: face)
  --ip IP_ADDRESS         ESP32 IP address (default: 192.168.1.100)
  --port PORT            ESP32 OSC port (default: 8000)
  --camera CAMERA_ID     Camera device ID (default: 0)
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| SPACE | Toggle tracking on/off |
| 'o' | Open flower manually |
| 'c' | Close flower manually |
| 'r' | Reset servos to center position |
| 'q' | Quit application |

### Examples

**Face tracking:**
```bash
python main.py --tracker face --ip 192.168.1.100
```

**Color tracking (red object):**
```bash
python main.py --tracker color --ip 192.168.1.100
```

## Configuration

Edit `config.ini` to customize:

- **Network**: ESP32 IP and port
- **Camera**: Resolution and device ID
- **PID Parameters**: Tune for your specific hardware
- **Color Tracking**: Adjust HSV range for different colors
- **Behavior**: Flower opening/closing speed and timing

### PID Tuning

The PID controller uses three parameters:
- **Kp (Proportional)**: Immediate response to error (default: 0.15)
- **Ki (Integral)**: Eliminates steady-state error (default: 0.01)
- **Kd (Derivative)**: Dampens oscillations (default: 0.05)

**Tuning tips:**
1. Start with Kp only, adjust until system responds
2. Add Ki to eliminate steady-state offset
3. Add Kd to reduce oscillations
4. Adjust `output_limits` to control max servo speed

### Color Tracking HSV Ranges

Common colors in HSV:
- **Red**: (0, 120, 70) to (10, 255, 255)
- **Blue**: (100, 150, 0) to (140, 255, 255)
- **Green**: (40, 40, 40) to (80, 255, 255)
- **Yellow**: (20, 100, 100) to (30, 255, 255)

Use a color picker tool to find custom HSV ranges.

## OSC Message Protocol

The system sends the following OSC messages:

| Address | Arguments | Description |
|---------|-----------|-------------|
| `/flower/servo` | [pan_angle, tilt_angle] | Set servo positions (0-180°) |
| `/flower/state` | [openness] | Set flower openness (0.0-1.0) |
| `/flower/motor` | [speed] | Set motor speed (-100 to 100) |
| `/flower/mode` | [mode] | Set tracking mode (0=idle, 1=tracking) |

## Troubleshooting

### Camera not working
- Check camera permissions
- Try different camera ID: `--camera 1`
- Verify camera with: `python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`

### Face detection not working
- Ensure good lighting
- Face should be front-facing
- Try adjusting distance from camera
- Check that Haar Cascade file is installed

### Color tracking not working
- Adjust HSV range in `config.ini`
- Use bright, solid-colored objects
- Ensure good lighting conditions
- Object should be larger than 500 pixels

### ESP32 not receiving commands
- Verify ESP32 IP address
- Check that computer and ESP32 are on same network
- Check firewall settings (allow UDP on port 8000)
- Monitor ESP32 Serial output for connection status

### Servos jittering
- Reduce PID gains (especially Kp and Kd)
- Increase `sample_time` in PID controller
- Check servo power supply
- Add capacitor across servo power lines

### Motor not responding
- Check motor driver connections
- Verify power supply voltage
- Test motor driver with simple Arduino sketch
- Check motor driver enable pin (GPIO 27)

## Project Structure

```
DATT3700/
├── python_controller/
│   ├── main.py              # Main application
│   ├── pid_controller.py    # PID control algorithm
│   ├── vision_tracker.py    # Face and color tracking
│   ├── osc_client.py        # OSC communication
│   ├── requirements.txt     # Python dependencies
│   └── config.ini          # Configuration file
├── esp32_firmware/
│   └── flower_control.ino  # ESP32 Arduino sketch
└── docs/
    ├── README.md           # This file
    ├── WIRING.md          # Wiring diagrams
    └── TUNING.md          # PID tuning guide
```

## Development

### Adding Custom Trackers

Create a new tracker class in `vision_tracker.py`:

```python
class MyTracker(VisionTracker):
    def __init__(self, frame_width, frame_height):
        super().__init__(frame_width, frame_height)
        # Initialize your tracker
    
    def get_tracking_error(self, frame):
        # Implement your tracking logic
        x_error = 0
        y_error = 0
        detected = False
        return (x_error, y_error, detected)
```

### Modifying Flower Behavior

Edit the `run()` method in `main.py` to customize:
- Opening/closing logic
- Response to target detection/loss
- Additional OSC commands

## Performance

- **Tracking Rate**: ~30 FPS (depends on camera and processing)
- **PID Update Rate**: ~33 Hz (30ms sample time)
- **OSC Latency**: <10ms on local network
- **Servo Response**: Depends on PID tuning

## Safety Notes

- Start with low PID gains to prevent violent movements
- Ensure adequate power supply for motors and servos
- Add limit switches if flower mechanism can jam
- Keep fingers clear of moving parts during testing
- Use appropriate current limiting for motors

## License

See LICENSE file in repository root.

## Credits

Built for DATT3700 course project using:
- OpenCV for computer vision
- python-osc for OSC protocol
- ESP32Servo library for servo control

## Contributing

This is a course project. For educational use and reference.

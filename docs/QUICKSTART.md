# Quick Start Guide

Get your Vision PID Control System running in 15 minutes!

## Prerequisites

- Python 3.7+ installed
- USB webcam or built-in camera
- ESP32 development board with WiFi
- Arduino IDE (for ESP32 firmware)

## Step 1: Install Python Dependencies (2 minutes)

```bash
cd python_controller
pip install -r requirements.txt
```

This installs:
- `opencv-python` - Computer vision library
- `numpy` - Numerical computing
- `python-osc` - OSC communication

## Step 2: Setup ESP32 Hardware (5 minutes)

### Minimal Test Setup

For initial testing, you only need:
- ESP32 board
- 2× Servo motors
- USB power

**Connections:**
```
ESP32 GPIO 18 → Pan Servo Signal (Orange/Yellow wire)
ESP32 GPIO 19 → Tilt Servo Signal (Orange/Yellow wire)
ESP32 GND → Servo Ground (Brown/Black wires)
ESP32 5V → Servo Power (Red wires)
```

⚠️ **Important**: For testing only 1-2 servos can be powered from ESP32. For production, use external 5V supply!

## Step 3: Flash ESP32 Firmware (5 minutes)

1. **Install Arduino IDE** from https://www.arduino.cc/en/software

2. **Add ESP32 Board Support:**
   - Arduino IDE → Preferences
   - Additional Board URLs: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "ESP32" → Install

3. **Install Libraries:**
   - Sketch → Include Library → Manage Libraries
   - Search and install:
     - `ESP32Servo` by Kevin Harrington
     - `OSC` by Adrian Freed (search for "OSC ESP")

4. **Configure WiFi:**
   - Open `esp32_firmware/flower_control.ino`
   - Update lines 21-22:
   ```cpp
   const char* ssid = "YOUR_WIFI_NAME";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

5. **Upload:**
   - Connect ESP32 via USB
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → (Select your ESP32)
   - Click Upload ↑

6. **Get IP Address:**
   - Open Serial Monitor (Ctrl+Shift+M)
   - Set baud rate to 115200
   - Press ESP32 reset button
   - Note the IP address shown (e.g., `192.168.1.100`)

## Step 4: Test the System (3 minutes)

### Test 1: Hardware Test

```bash
cd python_controller
python test_osc.py 192.168.1.XXX
```

Replace `192.168.1.XXX` with your ESP32's IP address.

You should see servos move through a test sequence. Watch the ESP32 Serial Monitor to confirm it's receiving commands.

### Test 2: Vision Test

```bash
python test_pid.py
```

This tests the PID controller (no hardware needed).

### Test 3: Manual Control

```bash
python example_manual_control.py 192.168.1.XXX
```

Control servos manually with keyboard commands:
- Type `left`, `right`, `up`, `down` to move servos
- Type `r` to reset
- Type `q` to quit

## Step 5: Run Full System

### Face Tracking

```bash
python main.py --tracker face --ip 192.168.1.XXX
```

- Press **SPACE** to enable tracking
- Face the camera - servos should follow you!
- Press **O** to open flower, **C** to close
- Press **Q** to quit

### Color Tracking

```bash
python main.py --tracker color --ip 192.168.1.XXX
```

- Hold a **red object** in front of camera
- Press **SPACE** to enable tracking
- System tracks the colored object

## Troubleshooting Quick Fixes

### "Failed to open camera"
```bash
# Try different camera ID
python main.py --camera 1 --ip 192.168.1.XXX
```

### "OSC commands not working"
1. Check ESP32 Serial Monitor - is it connected to WiFi?
2. Ping ESP32: `ping 192.168.1.XXX`
3. Computer and ESP32 on same WiFi network?

### "No face detected"
- Ensure good lighting
- Face should be 0.5-2 meters from camera
- Face camera directly (not at angle)

### "Servos jittering"
Edit `config.ini`:
```ini
[PID_Pan]
kp = 0.1  # Reduce from 0.15
kd = 0.08 # Increase from 0.05
```

## Configuration

Edit `python_controller/config.ini` to customize:

```ini
[Network]
esp32_ip = 192.168.1.XXX  # Your ESP32 IP

[PID_Pan]
kp = 0.15  # Proportional gain (speed)
ki = 0.01  # Integral gain (steady-state)
kd = 0.05  # Derivative gain (smoothing)
```

## Next Steps

1. **Add the Motor**: Follow [WIRING.md](WIRING.md) to connect DC motor for flower mechanism
2. **Tune PID**: Follow [TUNING.md](TUNING.md) for optimal tracking performance
3. **Build Mechanism**: Design and 3D-print your flower mechanism
4. **Customize**: Modify tracking behavior in `main.py`

## Safety Notes

⚠️ Start with low PID gains to prevent sudden movements
⚠️ Use proper power supply for production use (not ESP32 5V pin)
⚠️ Keep fingers away from moving servos and motors

## Getting Help

**Check the logs:**
- Python: Terminal output
- ESP32: Serial Monitor (115200 baud)

**Common Issues:**
- See [docs/README.md](README.md) for detailed troubleshooting
- Check wiring matches [docs/WIRING.md](WIRING.md)
- Verify Python dependencies installed

## Success Indicators

You know it's working when:
- ✓ ESP32 Serial Monitor shows "WiFi connected!"
- ✓ Servos center on startup (90°)
- ✓ Camera window opens showing video feed
- ✓ Face/object detection draws green box
- ✓ Servos smoothly follow tracked target
- ✓ OSC messages appear in Serial Monitor

## Full System Diagram

```
┌──────────┐         ┌──────────┐
│ Computer │         │  ESP32   │
│ + Camera │◄──WiFi─→│ + Servos │
└──────────┘         └──────────┘
     │                      │
     │ 1. Detects face     │
     │ 2. Calculates PID   │
     │ 3. Sends OSC ──────→│ 4. Moves servos
     │                      │ 5. Controls flower
```

Congratulations! Your Vision PID Control System is now running! 🎉

# Kait Node v2 - Testing Package

## 📦 Package Contents

This is a complete English-language version of the Kait Node v2 firmware and debugging tools, ready to test on your ESP32 board.

### Files Included

| File | Purpose | Language |
|------|---------|----------|
| `kait_v2_eng.ino` | Main firmware for ESP32 | English |
| `kait_osc_debug_en.py` | WiFi remote control script | English |
| `kait_serial_debug_en.py` | USB local debug script | English |
| `KAIT_QUICKSTART_EN.md` | Complete user guide | English |
| `requirements.txt` | Python dependencies | - |
| `README.md` | This file | English |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `python-osc` - For WiFi OSC protocol
- `pyserial` - For USB serial communication

### Step 2: Upload Firmware to ESP32

1. Download Arduino IDE from https://www.arduino.cc/
2. Install ESP32 Board Support:
   - File → Preferences
   - Add this to "Additional Boards Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board Manager → Search "esp32" → Install

3. Load the firmware:
   - Open `kait_v2_eng.ino` in Arduino IDE
   - Edit the WiFi configuration (lines 20-21):
     ```cpp
     const char* STA_SSID     = "Your_WiFi_SSID";
     const char* STA_PASSWORD = "Your_WiFi_Password";
     ```
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → Select COM port
   - Upload (Ctrl+U)

### Step 3: Test the Connection

```bash
# Test WiFi connection
ping F7OWER_kait.local

# Start interactive control
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive

# Or use serial port
python3 kait_serial_debug_en.py --interactive
```

---

## 🎮 Control Options

### Option 1: WiFi Remote (Recommended)

Control from anywhere on your WiFi network:

```bash
# Interactive mode
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive

# Set speed
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 150

# Execute motion
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1

# Run sequence
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
```

### Option 2: USB Serial Debug

For local debugging via USB cable:

```bash
# Find USB port
python3 kait_serial_debug_en.py --list-ports

# Interactive mode
python3 kait_serial_debug_en.py -p /dev/ttyUSB0 --interactive

# Quick test
python3 kait_serial_debug_en.py --motion 1
```

### Option 3: Arduino Serial Monitor

For direct firmware debugging:

1. Arduino IDE → Tools → Serial Monitor
2. Set baud rate to 115200
3. Type commands:
   ```
   motor 100
   motion 1
   stop
   info
   help
   ```

---

## 🎯 6 Motion Modes

| Mode | Name | Effect |
|------|------|--------|
| 1 | Gentle Sway | Slow back-and-forth movement |
| 2 | Fast Spin | Continuous rotation |
| 3 | Pulse Vibrate | Rapid trembling |
| 4 | Accelerate Spin | Gradual acceleration |
| 5 | Smooth Brake | Gradual deceleration |
| 6 | Pulse Start | Burst startup |

Test all modes:
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all
```

---

## 🔧 Hardware Setup

### Pin Configuration

```
ESP32 Pin 22 → Motor PWM (Speed Control)
ESP32 Pin 23 → Motor Direction Control
ESP32 GND   → Motor Driver GND (Common Ground)
```

### Recommended Driver

Use L298N or equivalent H-bridge motor driver:
- IN1 ← GPIO 22 (PWM)
- IN2 ← GPIO 23 (Direction)
- GND ← ESP32 GND
- OUT+/OUT- → DC Motor

---

## 📋 Command Reference

### Motor Speed

Speed range: -255 to 255

```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 100    # Forward
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed -100   # Reverse
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 0      # Stop
```

### Motion Modes

```bash
# Mode 1: Gentle Sway
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1

# Mode 2: Fast Spin
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 2

# Mode 3: Pulse Vibrate
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 3

# ... and so on (1-6)
```

### Preset Sequences

```bash
# Available sequences:
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq gentle_sway
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq excited_spin
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq alert_vibrate
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq smooth_wake
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all
```

---

## 🐛 Troubleshooting

### Motor Won't Move

- Check GPIO 23 connection (direction control)
- Verify power supply to motor driver
- Test with `--motion 1` (gentle sway)

### Can't Connect to WiFi

- Verify SSID and password in firmware
- Check that WiFi is 2.4 GHz (not 5 GHz)
- Re-upload firmware with correct credentials

### Can't Find Device

```bash
# Try using IP address instead of mDNS
# Check your router for connected devices
# Default attempt: 192.168.1.100
python3 kait_osc_debug_en.py -i 192.168.1.100 --speed 100
```

### Serial Port Issues

```bash
# On macOS/Linux:
sudo chmod 666 /dev/ttyUSB*

# Or run with sudo:
sudo python3 kait_serial_debug_en.py -p /dev/ttyUSB0
```

---

## 📖 Full Documentation

For detailed information, see `KAIT_QUICKSTART_EN.md` which includes:

- Complete firmware configuration guide
- Network troubleshooting
- Interactive mode usage
- Custom motion mode creation
- Performance specifications
- And much more!

---

## 🎓 Interactive Mode Example

```
$ python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive

==================================================
Entering Interactive Mode (type 'help' for commands)
==================================================

kait> help
==================================================
Command List:
==================================================
  motor <speed>     - Set motor speed (-255 ~ 255)
  motion <mode>     - Execute motion mode (1-6)
  stop              - Stop motor
  seq <name>        - Execute preset sequence
  seqs              - List all preset sequences
  help              - Show this help
  quit/exit         - Exit program
==================================================

kait> motor 100
🎚️ Motor Set: Forward (Speed: 100)

kait> motion 1
📍 Motion Mode 1: Gentle Sway

kait> seq test_all
🧪 Sequence: Test All Modes
  Testing Mode 1: Gentle Sway...
  ... (continues)

kait> quit
👋 Goodbye!
```

---

## 🔐 WiFi Security

The firmware connects in **Station Mode** (STA), meaning it joins your existing WiFi network:

- **SSID**: Your WiFi network name
- **Password**: Your WiFi password
- **mDNS Name**: F7OWER_kait
- **Access**: Available as `F7OWER_kait.local` on your local network only

For security:
- Only your local WiFi devices can access it
- It does NOT create a public access point
- Connection is local-network-only

---

## 📊 Performance Specs

| Specification | Value |
|---------------|-------|
| **PWM Frequency** | 20 kHz |
| **Speed Range** | 0-255 |
| **Resolution** | 8-bit (256 levels) |
| **Startup Delay** | ~30 ms |
| **Network Latency** | <50 ms (LAN) |
| **OSC Port** | UDP 8888 |

---

## 📞 Getting Help

### Check Status

Open Arduino IDE Serial Monitor (115200 baud) to see:
- WiFi connection status
- Device IP address
- Incoming commands
- Error messages

### Verify Connection

```bash
# Ping the device
ping F7OWER_kait.local

# Check if response:
# - Should see "bytes from" replies
# - If no response, check WiFi settings
```

### Test Functionality

```bash
# Run the test all sequence
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all

# This will execute all 6 motion modes
# Each takes 3-4 seconds
# Total: ~21 seconds
```

---

## 🌸 Features

✅ WiFi network connectivity  
✅ mDNS device discovery  
✅ OSC remote protocol  
✅ Serial debug interface  
✅ 6 built-in motion modes  
✅ Bi-directional motor control  
✅ Speed range 0-255 PWM  
✅ Python debug scripts  
✅ Interactive mode  
✅ Complete documentation  

---

## 📄 File Structure

```
kait_test/
├── kait_v2_eng.ino           # Firmware (upload to ESP32)
├── kait_osc_debug_en.py          # WiFi control script
├── kait_serial_debug_en.py       # Serial control script
├── KAIT_QUICKSTART_EN.md         # Complete user guide
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## ✨ Version Information

- **Version**: 2.0
- **Device**: F7OWER Kait Node
- **Hardware**: ESP32 + L298N Motor Driver
- **Firmware**: Arduino/C++
- **Tools**: Python 3.6+
- **Protocol**: OSC over UDP + Serial UART
- **Status**: ✅ Production Ready

---

## 🎉 You're Ready!

Everything is set up and ready to go. Start with the quick start guide above, and refer to `KAIT_QUICKSTART_EN.md` for detailed information.

**Enjoy your Kait flower node!** 🌸

---

**Last Updated**: March 14, 2026  
**Status**: Ready for Testing  
**License**: MIT


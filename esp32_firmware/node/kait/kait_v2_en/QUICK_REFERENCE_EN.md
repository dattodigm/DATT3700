# Kait Node v2 - Quick Reference Card

## 🚀 30-Second Quick Start

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Upload Firmware
- Arduino IDE → Open `kait_v2_eng.ino`
- Edit WiFi SSID & password (lines 20-21)
- Upload to ESP32

### 3. Start Controlling
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive
```

---

## 🔌 Hardware Wiring (Critical!)

```
┌─────────────────────────────┐
│      ESP32 Dev Board        │
├─────────────────────────────┤
│ GPIO22 ──┬─ PWM (Speed)    │
│ GPIO23 ──┼─ DIR (Direction)│  ← MUST HAVE BOTH!
│ GND ─────┘                 │
└──────────┬──────────────────┘
           │
    ┌──────┴─────────────┐
    │   L298N Driver     │
    ├────────────────────┤
    │ IN1: PWM ← GPIO22  │
    │ IN2: DIR ← GPIO23  │
    │ GND ← ESP32 GND    │
    │                    │
    │ OUT+ → Motor +     │
    │ OUT- → Motor -     │
    └────────────────────┘
```

---

## 🎮 Control Methods

### Method 1: WiFi Remote (Recommended)
```bash
# Interactive mode
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive

# Quick commands
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 150
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
```

### Method 2: Serial Debug
```bash
# Find port
python3 kait_serial_debug_en.py --list-ports

# Connect
python3 kait_serial_debug_en.py -p /dev/ttyUSB0 --interactive
```

### Method 3: Arduino Serial Monitor
```
motion 1
motor 100
stop
info
```

---

## 🎬 Motion Modes (1-6)

| # | Mode | Effect | Time |
|---|------|--------|------|
| 1 | Gentle Sway | Slow back-forth | 4s |
| 2 | Fast Spin | Fast rotation | 2s |
| 3 | Vibrate | Trembling | 1s |
| 4 | Accelerate | Speed up | 3s |
| 5 | Brake | Slow down | 1.5s |
| 6 | Pulse Start | Burst start | 2s |

**Quick Test:**
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all
```

---

## ⚙️ Configuration (Edit in kait_v2_eng.ino)

```cpp
// WiFi Settings
const char* STA_SSID     = "Your_WiFi";       // WiFi name
const char* STA_PASSWORD = "Your_Password";   // WiFi password
const char* MDNS_NAME = "F7OWER_kait";        // Device name

// Motor Settings
const int MOTOR_KICK_START_POWER = 255;       // Startup power (0-255)
const int MOTOR_KICK_START_DELAY = 30;        // Startup time (ms)

// Network Settings
const int OSC_PORT = 8888;                    // OSC port (UDP)
```

---

## 📊 Speed Values Reference

| Speed | Percent | Direction | Use |
|-------|---------|-----------|-----|
| 0 | 0% | - | Stop |
| 50 | 20% | Forward/Reverse | Very slow |
| 100 | 39% | Forward/Reverse | Slow |
| 150 | 59% | Forward/Reverse | Medium |
| 200 | 78% | Forward/Reverse | Fast |
| 255 | 100% | Forward/Reverse | Maximum |

**Negative** = Reverse rotation

---

## 💻 Interactive Mode Commands

```
motor <speed>    Set speed (-255 ~ 255)
motion <mode>    Execute mode (1-6)
stop             Stop motor
seq <name>       Run sequence
seqs             List sequences
help             Show help
quit/exit        Exit
```

---

## 🎬 Preset Sequences

```bash
seq gentle_sway       # 5 cycles of gentle sway
seq excited_spin      # 3 fast spins
seq alert_vibrate     # Rapid trembling
seq smooth_wake       # Slow to fast to slow
seq dance             # Complex rhythm
seq test_all          # All 6 modes in order
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Motor won't move** | Check GPIO 23 connection |
| **WiFi won't connect** | Verify SSID/password |
| **Can't find device** | Use IP instead of mDNS |
| **Serial fails** | Run with sudo or chmod 666 |

---

## 📝 Serial Commands (Arduino IDE)

Type in Serial Monitor (115200 baud):

```
motor 100          Forward at speed 100
motor -80          Reverse at speed 80
motor 0            Stop
motion 1           Gentle Sway
motion 2           Fast Spin
... motion 3-6     Other modes
stop               Emergency stop
info               Show device info
help               Command help
```

---

## 🌐 Network Setup

### Find Device
```bash
ping F7OWER_kait.local
```

### Check Router
Look for "F7OWER_kait" in connected devices list

### Get IP from Serial Monitor
Look for: `✅ WiFi Connected, IP: 192.168.1.xxx`

---

## 📦 What's Included

| File | Purpose |
|------|---------|
| `kait_v2_eng.ino` | Main firmware |
| `kait_osc_debug_en.py` | WiFi control |
| `kait_serial_debug_en.py` | Serial control |
| `KAIT_QUICKSTART_EN.md` | Full guide |
| `requirements.txt` | Dependencies |
| `README.md` | Overview |

---

## ✨ Key Features

✅ WiFi + mDNS  
✅ OSC protocol  
✅ Serial debug  
✅ 6 motion modes  
✅ Bi-directional  
✅ Speed 0-255  
✅ Python scripts  
✅ Interactive mode  

---

## 📞 Quick Diagnostics

### Check Firmware
```
1. Open Serial Monitor (115200)
2. Press ESP32 reset button
3. Should see connection messages
```

### Test Motor
```
kait> motor 100     # Should rotate
kait> motor -100    # Should reverse
kait> stop          # Should stop
```

### Test Modes
```
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all
```

---

## 🎯 Common Workflows

### Simple Speed Control
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 150
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 0
```

### Run Motion Mode
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1
```

### Execute Sequence
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
```

### Interactive Control
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive
# Then type: motor 100, motion 1, seq dance, etc.
```

---

## 🔐 Security Notes

- **Local WiFi Only** - Device connects to YOUR WiFi
- **No Public AP** - Does not broadcast open network
- **mDNS Name** - Device broadcasts as F7OWER_kait.local
- **Default Port** - OSC uses port 8888 (UDP)

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| PWM Frequency | 20 kHz |
| Resolution | 8-bit |
| Startup Time | ~30 ms |
| Network Delay | <50 ms |
| Supported Modes | 6 |
| Speed Steps | 256 |

---

## 🆘 Fast Help

**Can't connect to WiFi?**
- Edit SSID/password in firmware
- Re-upload

**Motor won't move?**
- Check GPIO 23
- Try `motor 100` in serial

**Can't find device?**
- Use IP address directly
- Check router for connected devices

**Python script fails?**
- `pip install -r requirements.txt`

---

## 📚 Learn More

For detailed information, see:
- `KAIT_QUICKSTART_EN.md` - Complete guide
- `README.md` - Overview
- Source code comments in firmware

---

## 🌸 You're All Set!

Follow the **30-Second Quick Start** above and you'll be controlling your Kait node in no time!

**Version**: 2.0  
**Status**: ✅ Ready  
**Updated**: March 14, 2026


# Kait Node v2 - Complete User Guide (English)

## 📋 Quick Overview

This is the enhanced version of the Kait flower node with WiFi connectivity, OSC protocol support, and 6 built-in motion modes. Control your Kait node remotely via WiFi or locally via Serial port.

---

## 🔌 Hardware Wiring

### ESP32 Pin Configuration

| Component | Function | ESP32 Pin |
|-----------|----------|-----------|
| **Motor PWM** | Speed Control | GPIO 22 |
| **Motor Direction** | Direction Control | GPIO 23 |

### Driver Circuit Connection

```
ESP32 GPIO22 → L298N/MOS Driver IN1 (PWM)
ESP32 GPIO23 → L298N/MOS Driver IN2 (Direction)
ESP32 GND ── L298N GND (Common Ground)

L298N Output
├─ OUT+ → Motor Positive (Red)
└─ OUT- → Motor Negative (Black)
```

---

## 🔧 Firmware Upload

### Step 1: Open Arduino IDE
- Install Arduino IDE or PlatformIO

### Step 2: Select Board
- Go to Tools → Board → ESP32 Dev Module

### Step 3: Edit Configuration
Open `kait_v2_eng.ino` and modify:

```cpp
const char* STA_SSID     = "Your_WiFi_SSID";      // Your WiFi name
const char* STA_PASSWORD = "Your_WiFi_Password";  // Your WiFi password
const char* MDNS_NAME = "F7OWER_kait";            // Device name on LAN
```

### Step 4: Upload
- Click Upload button
- Wait for "Done uploading" message

### Step 5: Verify
- Open Serial Monitor (Tools → Serial Monitor)
- Set Baud Rate to 115200
- You should see connection messages

---

## 🌐 Network Connection

### Finding Your Device

After uploading the firmware, the device broadcasts itself on your local network as `F7OWER_kait.local`

#### Method 1: mDNS (Recommended)
```bash
ping F7OWER_kait.local
```

#### Method 2: Router
Check your router's connected devices list for "F7OWER_kait"

#### Method 3: Serial Monitor
- Open Serial Monitor (115200 baud)
- Look for "IP: xxx.xxx.xxx.xxx"

---

## 📡 Control Methods

### Method 1: OSC (WiFi Remote Control) - RECOMMENDED

#### Installation
```bash
pip install python-osc pyserial
```

#### Interactive Control
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive
```

#### Quick Commands
```bash
# Set motor speed
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 150

# Execute motion mode
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1

# Run preset sequence
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance

# Stop motor
python3 kait_osc_debug_en.py -i F7OWER_kait.local --stop
```

### Method 2: Serial Port (Local USB Debug)

#### Find Serial Port
```bash
python3 kait_serial_debug_en.py --list-ports
```

Output:
```
Available Serial Ports:
  /dev/ttyUSB0             - Silicon Labs CP210x USB to UART Bridge
```

#### Interactive Control
```bash
python3 kait_serial_debug_en.py -p /dev/ttyUSB0 --interactive
```

#### Quick Commands
```bash
python3 kait_serial_debug_en.py --speed 100
python3 kait_serial_debug_en.py --motion 1
python3 kait_serial_debug_en.py --info
```

### Method 3: Arduino Serial Monitor (Direct Testing)

1. Open Arduino IDE Serial Monitor (115200 baud)
2. Type commands directly:
   ```
   motor 100      # Set speed to 100
   motion 1       # Execute motion mode 1
   stop           # Stop motor
   info           # Show device info
   help           # Show available commands
   ```

---

## 🎮 Motion Modes

### 6 Built-in Motion Modes

| Mode | Name | Effect | Duration | Use Case |
|------|------|--------|----------|----------|
| 1 | Gentle Sway | 🌿 Gentle back-and-forth | 4 sec | Soothing |
| 2 | Fast Spin | ⚡ Continuous rotation | 2 sec | Happy |
| 3 | Pulse Vibrate | 🚨 Rapid trembling | 1 sec | Alert |
| 4 | Accelerate Spin | 🌪️ Gradual acceleration | 3 sec | Wake-up |
| 5 | Smooth Brake | ⏱️ Gradual deceleration | 1.5 sec | Sleep |
| 6 | Pulse Start | ⚙️ Burst start | 2 sec | Revival |

### How to Execute Modes

**Via OSC:**
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1
```

**Via Serial:**
```bash
python3 kait_serial_debug_en.py --motion 1
```

**Via Arduino Serial Monitor:**
```
motion 1
motion 2
motion 3
... etc
```

---

## 🎬 Preset Sequences

### Available Sequences

| Sequence | Description | Duration |
|----------|-------------|----------|
| `gentle_sway` | 5 slow back-and-forth cycles | ~10 sec |
| `excited_spin` | 3 fast spins with pauses | ~8 sec |
| `alert_vibrate` | 2 cycles of rapid trembling | ~3 sec |
| `smooth_wake` | Gradual acceleration then deceleration | ~8 sec |
| `dance` | Complex rhythmic movements | ~6 sec |
| `test_all` | All 6 modes sequentially | ~21 sec |

### How to Execute Sequences

**Via OSC:**
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
```

**Via Serial:**
```bash
python3 kait_serial_debug_en.py --seq dance
```

**Interactive Mode:**
```
kait> seqs                 # List all sequences
kait> seq gentle_sway      # Execute gentle sway
```

---

## 🎯 Interactive Mode

Both scripts support interactive mode for continuous control.

### Start Interactive Mode

**OSC (WiFi):**
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive
```

**Serial (USB):**
```bash
python3 kait_serial_debug_en.py --interactive
```

### Interactive Commands

```
motor <speed>    - Set speed (-255 ~ 255)
motion <mode>    - Execute mode (1-6)
stop             - Stop motor
seq <name>       - Run preset sequence
seqs             - List all sequences
help             - Show this help
quit/exit        - Exit program
```

### Interactive Example

```
kait> motor 100
🎚️ Motor Set: Forward (Speed: 100)

kait> motion 1
📍 Motion Mode 1: Gentle Sway

kait> seq smooth_wake
🌅 Sequence: Smooth Wake
  [1/5] Speed 50...
  [2/5] Speed 80...
  ... (continues)

kait> stop
⏹️ Motor Stopped

kait> quit
👋 Goodbye!
```

---

## 📊 Speed Reference

### Motor Speed Values

| Speed | PWM % | Effect | Use Case |
|-------|-------|--------|----------|
| 0 | 0% | Stop | Idle |
| ±50 | 20% | Very slow sway | Sleep mode |
| ±100 | 39% | Slow rotation | Gentle display |
| ±150 | 59% | Medium rotation | Interaction |
| ±200 | 78% | Fast rotation | Active state |
| ±255 | 100% | Maximum speed | Alert signal |

### Speed Direction

- **Positive value** → Forward rotation
- **Negative value** → Reverse rotation
- **Zero** → Stop

---

## 🔍 Troubleshooting

### Motor Won't Start

**Problem:** Motor doesn't move even with non-zero speed

**Solution:** Check GPIO 23 connection (direction control pin)

### WiFi Can't Connect

**Problem:** Serial shows "WiFi Connection Failed"

**Solution:** 
- Verify SSID and password in firmware
- Check if WiFi network is 2.4 GHz (some networks only support 5 GHz)
- Re-upload firmware with correct credentials

### Can't Find Device via mDNS

**Problem:** `ping F7OWER_kait.local` fails

**Solution:**
- Check Router's connected devices
- Use IP address instead: `python3 kait_osc_debug_en.py -i 192.168.1.100 --interactive`

### Serial Port Connection Failed

**Problem:** "Serial Connection Failed" error

**Solution:**
```bash
# On Linux/macOS:
sudo chmod 666 /dev/ttyUSB*

# Or use sudo:
sudo python3 kait_serial_debug_en.py -p /dev/ttyUSB0
```

### No Serial Port Detected

**Problem:** `--list-ports` shows no devices

**Solution:**
- Install CH340 driver (search for "CP210x driver" or "CH340 driver")
- Restart computer after driver installation
- Try different USB port on computer

---

## ⚙️ Configuration Parameters

### Firmware Settings (Edit `kait_v2_eng.ino`)

```cpp
// WiFi Configuration
const char* STA_SSID     = "F7OWER";           // WiFi name
const char* STA_PASSWORD = "12345678";         // WiFi password
const char* MDNS_NAME = "F7OWER_kait";         // Device broadcast name

// Motor Configuration
const int MOTOR_KICK_START_POWER = 255;        // Startup kick power (0-255)
const int MOTOR_KICK_START_DELAY = 30;         // Startup kick duration (ms)

// Network Configuration
const int OSC_PORT = 8888;                     // OSC listen port

// Hardware Pins (Do Not Change)
const int MOTOR_PWM_PIN = 22;                  // Speed control pin
const int MOTOR_DIR_PIN = 23;                  // Direction control pin
```

### Adjusting Motor Startup

The firmware includes "kick start" to overcome static friction:

- `KICK_START_POWER`: How hard the initial pulse is (255 = maximum)
- `KICK_START_DELAY`: How long the pulse lasts (milliseconds)

If motor starts too aggressively:
- Reduce `KICK_START_POWER` to 200
- Or reduce `KICK_START_DELAY` to 20

If motor won't start at low speeds:
- Increase `KICK_START_DELAY` to 40

---

## 🎓 Quick Start (5 minutes)

### Step 1: Upload Firmware (2 min)
```bash
# Edit WiFi settings in kait_v2_en.ino
# Upload to ESP32 via Arduino IDE
```

### Step 2: Verify Connection (1 min)
```bash
ping F7OWER_kait.local
```

### Step 3: Run First Test (2 min)
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq test_all
```

Done! 🎉

---

## 📚 Files Included

- `kait_v2_eng.ino` - Main firmware (upload to ESP32)
- `kait_osc_debug_en.py` - WiFi remote control script
- `kait_serial_debug_en.py` - USB local debug script
- `KAIT_QUICKSTART_EN.md` - This quick start guide
- `requirements.txt` - Python dependencies

---

## 📞 Support

### Check Serial Output

Arduino IDE Serial Monitor (115200 baud) shows:
- Connection status
- Received commands
- Error messages

### Common Messages

| Message | Meaning |
|---------|---------|
| ✅ WiFi Connected | Device is online |
| ❌ WiFi Connection Failed | Check SSID/password |
| ✅ mDNS Started | Device discoverable as F7OWER_kait.local |
| 🎚️ Motor Speed Set | Command received |
| ⏹️ Motor Stopped | Motor stopped |

---

## 🎨 Customization

### Add New Motion Mode

Edit `kait_v2_eng.ino` and add a new function:

```cpp
void myCustomMode() {
  setMotorSpeed(150);    // Set speed
  delay(2000);           // Wait 2 seconds
  setMotorSpeed(-100);   // Reverse
  delay(1000);           // Wait 1 second
  stopMotor();           // Stop
}
```

Then add to `executeMotionMode()`:
```cpp
case 7:
  myCustomMode();
  break;
```

### Add New Sequence

Edit Python script and add:

```python
def sequence_my_custom(self):
    """My Custom Sequence"""
    print("🎨 Custom Sequence")
    self.set_motor_speed(150)
    time.sleep(2)
    self.set_motor_speed(-100)
    time.sleep(1)
    self.stop()
    print("Done!\n")
```

---

## 🌸 Version Info

- **Version**: 2.0
- **Device**: F7OWER Kait Node
- **Firmware**: ESP32
- **Protocol**: OSC (UDP) + Serial UART
- **Status**: Production Ready

---

## ✨ Key Features

✅ WiFi network connectivity (STA mode)  
✅ mDNS device auto-discovery (F7OWER_kait.local)  
✅ OSC protocol for remote control  
✅ Serial port for local debugging  
✅ 6 built-in motion modes  
✅ Bidirectional motor control  
✅ Speed control (0-255 PWM)  
✅ Motor startup kick protection  
✅ Interactive Python scripts  
✅ Complete English documentation  

---

**🌸 Happy controlling! Enjoy your Kait flower! 🌸**

For more detailed information, refer to the comments in the source code.


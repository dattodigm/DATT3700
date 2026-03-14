# Kait Node v2 - Complete API & Command Reference

## 📡 OSC Protocol Commands

### Motor Speed Control

**Command**: `/motor <speed>`

**Parameters**: 
- `speed` (integer): -255 to 255
  - Negative: Reverse rotation
  - Zero: Stop
  - Positive: Forward rotation

**Examples**:
```bash
# Forward at half speed
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 128

# Reverse at full speed
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed -255

# Stop
python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed 0
```

**Motor Response**:
- Immediately sets motor to target speed
- Includes automatic kick-start for low speeds
- Returns current speed in logs

---

### Motion Mode Execution

**Command**: `/motion <mode>`

**Parameters**:
- `mode` (integer): 1-6 (see table below)

**Available Modes**:

| Mode | Name | Effect | Duration | Use Case |
|------|------|--------|----------|----------|
| 1 | Gentle Sway | Slow back-and-forth | 4 sec | Peaceful |
| 2 | Fast Spin | Continuous rotation | 2 sec | Happy |
| 3 | Pulse Vibrate | Rapid trembling | 1 sec | Alert |
| 4 | Accelerate Spin | Speed up gradually | 3 sec | Wake-up |
| 5 | Smooth Brake | Slow down gradually | 1.5 sec | Sleep |
| 6 | Pulse Start | Burst startup | 2 sec | Revival |

**Examples**:
```bash
# Execute Gentle Sway
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 1

# Execute Fast Spin
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 2

# Execute Accelerate
python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion 4
```

**Important Notes**:
- Each mode completes its full cycle
- Motor stops automatically after mode completes
- Modes cannot be interrupted (will complete current cycle)
- Typical execution time: 1-4 seconds

---

### Motor Stop

**Command**: `/stop`

**Parameters**: None

**Effect**: 
- Immediately stops motor
- Sets speed to 0
- Clears direction flag

**Example**:
```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --stop
```

---

## 🎬 Preset Motion Sequences

Sequences combine multiple movements into a choreographed routine.

### Available Sequences

```bash
seq gentle_sway       # 5 slow back-and-forth cycles
seq excited_spin      # 3 fast spins with pauses
seq alert_vibrate     # 2 cycles of rapid trembling
seq smooth_wake       # Gradual speed change
seq dance             # Complex rhythmic pattern
seq test_all          # All 6 modes sequentially
```

### Sequence Details

#### gentle_sway
- **Duration**: ~10 seconds
- **Pattern**: Forward 1s → Reverse 1s (repeat 5x)
- **Speed**: ±80 PWM
- **Use**: Soothing, peaceful

#### excited_spin
- **Duration**: ~8 seconds
- **Pattern**: Spin 2s → Pause 0.5s (repeat 3x)
- **Speed**: 220 PWM
- **Use**: Happy, active

#### alert_vibrate
- **Duration**: ~3 seconds
- **Pattern**: Forward 50ms → Reverse 50ms (repeat many)
- **Speed**: ±150 PWM
- **Use**: Alert, warning

#### smooth_wake
- **Duration**: ~8 seconds
- **Pattern**: Accelerate 50→200, then decelerate
- **Speed**: Ramping 50 to 200 to 0
- **Use**: Wake-up, gradual start

#### dance
- **Duration**: ~6 seconds
- **Pattern**: Complex rhythm (2 cycles)
- **Speed**: Varying (120, 200, 180, etc.)
- **Use**: Entertainment, playful

#### test_all
- **Duration**: ~21 seconds
- **Pattern**: Mode 1 → Mode 2 → ... → Mode 6
- **Speed**: Default speeds for each mode
- **Use**: Firmware verification

### Execute Sequence

```bash
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq dance
```

---

## 💻 Serial Port Commands

All commands available over USB serial (115200 baud).

### Command Format

```
<command> [parameters]
```

### Available Commands

#### motor
Set motor speed

**Format**: `motor <speed>`

**Parameters**: -255 to 255

**Examples**:
```
motor 100      # Forward
motor -100     # Reverse
motor 0        # Stop
```

#### motion
Execute motion mode

**Format**: `motion <mode>`

**Parameters**: 1-6

**Examples**:
```
motion 1       # Gentle Sway
motion 2       # Fast Spin
motion 6       # Pulse Start
```

#### stop
Stop motor immediately

**Format**: `stop`

**Example**:
```
stop
```

#### info
Display device information

**Format**: `info`

**Returns**:
```
=== Device Info ===
Device Name: F7OWER_kait
IP Address: 192.168.1.100
MAC Address: AA:BB:CC:DD:EE:FF
OSC Port: 8888
Motor Status: Running (Speed: 100)
==================
```

#### help
Show available commands

**Format**: `help`

**Returns**: List of all commands with descriptions

---

## 🎮 Interactive Mode Commands

When running scripts in interactive mode (`--interactive` flag).

### Available Commands

```
motor <speed>    - Set motor speed (-255 ~ 255)
motion <mode>    - Execute motion mode (1-6)
stop             - Stop motor
seq <name>       - Execute preset sequence
seqs             - List all available sequences
help             - Show this help
quit/exit        - Exit program
```

### Interactive Examples

```bash
$ python3 kait_osc_debug_en.py -i F7OWER_kait.local --interactive

kait> motor 100
🎚️ Motor Set: Forward (Speed: 100)

kait> motion 1
📍 Motion Mode 1: Gentle Sway

kait> seqs
Preset Sequences:
  gentle_sway      - Gentle Sway - Slow back and forth movement
  excited_spin     - Excited Spin - Fast rotation with pauses
  alert_vibrate    - Alert Signal - Rapid trembling
  smooth_wake      - Smooth Wake - Accelerate from slow to fast
  dance            - Dance Rhythm - Complex movement combination
  test_all         - Test All Modes - All modes sequentially

kait> seq dance
💃 Sequence: Dance Rhythm
  [Cycle 1/2]
    Fast sway...
    Pause...
    Fast spin...
    ... (continues)

kait> stop
⏹️ Motor Stopped

kait> quit
👋 Goodbye!
```

---

## 🔧 Firmware API (Source Code)

For developers modifying the firmware:

### Core Functions

#### setMotorSpeed(int speed)
Set motor speed directly

```cpp
void setMotorSpeed(int speed);
```

**Parameters**: 
- `speed`: -255 to 255

**Behavior**:
- Constrains speed to valid range
- Sets direction based on sign
- Applies kick-start for low speeds
- Updates motor state

#### stopMotor()
Stop motor immediately

```cpp
void stopMotor();
```

**Behavior**:
- Sets speed to 0
- Disables motor output
- Clears motor state

#### executeMotionMode(int mode)
Execute preset motion

```cpp
void executeMotionMode(int mode);
```

**Parameters**:
- `mode`: 1-6

**Behavior**:
- Validates mode number
- Executes corresponding motion function
- Returns when motion completes

### Motion Functions

#### void sway(int amplitude, int duration)
Gentle back-and-forth movement

**Parameters**:
- `amplitude`: Speed (default 80, range 0-255)
- `duration`: Total duration in ms (default 3000)

#### void fastSpin(int duration)
Fast continuous rotation

**Parameters**:
- `duration`: Rotation time in ms (default 2000)

#### void vibrate(int intensity, int duration)
Rapid trembling

**Parameters**:
- `intensity`: Vibration speed (default 120, range 0-255)
- `duration`: Duration in ms (default 1000)

#### void accelerateSpin(int maxSpeed, int duration)
Gradual acceleration

**Parameters**:
- `maxSpeed`: Final speed (default 220, range 0-255)
- `duration`: Acceleration time in ms (default 3000)

#### void smoothBrake(int initialSpeed)
Gradual deceleration

**Parameters**:
- `initialSpeed`: Starting speed (default 200, range 0-255)

#### void pulseStart(int targetSpeed, int duration)
Burst startup with pulses

**Parameters**:
- `targetSpeed`: Final stable speed (default 150)
- `duration`: Stable operation time in ms (default 2000)

---

## 🔐 Configuration Parameters

Edit in `kait_v2_eng.ino`:

### WiFi Configuration
```cpp
const char* STA_SSID = "Your_WiFi";           // WiFi network name
const char* STA_PASSWORD = "Your_Password";   // WiFi password
const char* MDNS_NAME = "F7OWER_kait";        // Device name for discovery
```

### Network Configuration
```cpp
const int OSC_PORT = 8888;                    // OSC listening port (UDP)
```

### Hardware Configuration
```cpp
const int MOTOR_PWM_PIN = 22;                 // Speed control pin (do not change)
const int MOTOR_DIR_PIN = 23;                 // Direction control pin (do not change)
```

### Motor Configuration
```cpp
const int MOTOR_KICK_START_POWER = 255;       // Startup pulse power (0-255)
const int MOTOR_KICK_START_DELAY = 30;        // Startup pulse duration (ms)
```

### PWM Configuration
```cpp
const int PWM_FREQ = 20000;                   // PWM frequency in Hz (20kHz)
const int PWM_RESOLUTION = 8;                 // Bit resolution (8-bit = 0-255)
```

---

## 📊 Speed Mapping Table

| Speed Value | PWM % | Motor Effect |
|-------------|-------|--------------|
| 0 | 0% | Stopped |
| ±25 | 10% | Very slow crawl |
| ±50 | 20% | Slow sway |
| ±75 | 29% | Gentle rotation |
| ±100 | 39% | Moderate speed |
| ±125 | 49% | Medium speed |
| ±150 | 59% | Regular speed |
| ±175 | 69% | Faster speed |
| ±200 | 78% | Fast rotation |
| ±225 | 88% | Very fast |
| ±255 | 100% | Maximum speed |

---

## 🔌 Default Pins

Do **NOT** change these without modifying hardware:

```
GPIO 22 → Motor PWM (mandatory)
GPIO 23 → Motor Direction (mandatory)
GND     → Common Ground (mandatory)
```

---

## 📊 Performance Characteristics

| Specification | Value |
|---------------|-------|
| **PWM Frequency** | 20 kHz |
| **PWM Resolution** | 8-bit (256 levels) |
| **Speed Range** | ±255 |
| **Motor Response Time** | ~30-50 ms |
| **Network Latency** | <50 ms (local WiFi) |
| **OSC Port** | UDP 8888 |
| **Serial Baud** | 115200 |
| **Max Connections** | 1 (current) |

---

## 🎯 Common Usage Patterns

### Simple Speed Loop
```bash
# Gradually increase speed
for speed in {0..255..10}; do
  python3 kait_osc_debug_en.py -i F7OWER_kait.local --speed $speed
  sleep 0.5
done
```

### Mode Testing
```bash
# Test each mode
for mode in {1..6}; do
  python3 kait_osc_debug_en.py -i F7OWER_kait.local --motion $mode
  sleep 4
done
```

### Sequence Loop
```bash
# Run sequences in loop
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq gentle_sway
sleep 2
python3 kait_osc_debug_en.py -i F7OWER_kait.local --seq excited_spin
```

---

## 🆘 Troubleshooting by Command

### motor Command Doesn't Work
- Check GPIO 23 connection
- Verify power supply
- Test with motion command

### motion Command Fails
- Verify mode is 1-6
- Check serial monitor for errors
- Try stop command then motor command

### seq Command Unknown
- Make sure sequence name is correct
- Type `seqs` to list available sequences
- Check spelling (case-sensitive)

---

## 📞 Command Reference Summary

| What You Want | Command |
|---------------|---------|
| Move forward slowly | `motor 100` |
| Move backward quickly | `motor -200` |
| Stop | `motor 0` or `stop` |
| Gentle motion | `motion 1` |
| Fast motion | `motion 2` |
| Alert vibration | `motion 3` |
| Wake-up | `motion 4` |
| Sleep/brake | `motion 5` |
| Quick restart | `motion 6` |
| Peaceful sequence | `seq gentle_sway` |
| Test all modes | `seq test_all` |
| Device status | `info` |

---

**Version**: 2.0  
**Last Updated**: March 14, 2026  
**Status**: Complete Reference


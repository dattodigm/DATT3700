# Wiring Diagrams

## Complete System Wiring

```
┌─────────────────────────────────────────────────────────────┐
│                         Power Supply                         │
│                                                              │
│  ┌────────┐         ┌──────────┐         ┌──────────┐      │
│  │ 5V 2A  │────────→│ Servos   │         │ ESP32    │      │
│  │ Supply │         │ (2x)     │         │          │      │
│  └────────┘         └──────────┘         └──────────┘      │
│                                                              │
│  ┌────────┐         ┌──────────┐                           │
│  │ 12V    │────────→│ Motor    │                           │
│  │ Supply │         │ Driver   │                           │
│  └────────┘         └──────────┘                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Detailed ESP32 Connections

```
                    ESP32 Development Board
                    ┌───────────────────┐
                    │                   │
    Pan Servo   ────│ GPIO 18          │
    Tilt Servo  ────│ GPIO 19          │
                    │                   │
    Motor IN1   ────│ GPIO 25          │
    Motor IN2   ────│ GPIO 26          │
    Motor ENA   ────│ GPIO 27 (PWM)    │
                    │                   │
    Common GND  ────│ GND              │
    5V Servo    ────│ 5V (optional)    │
                    │                   │
                    └───────────────────┘
```

## Servo Wiring

### Pan Servo (Horizontal Rotation)
```
Pan Servo                    ESP32
┌─────────┐                  ┌──────┐
│ Red     │─────────────────→│ 5V   │
│ Brown   │─────────────────→│ GND  │
│ Orange  │─────────────────→│ IO18 │
└─────────┘                  └──────┘
```

### Tilt Servo (Vertical Rotation)
```
Tilt Servo                   ESP32
┌─────────┐                  ┌──────┐
│ Red     │─────────────────→│ 5V   │
│ Brown   │─────────────────→│ GND  │
│ Orange  │─────────────────→│ IO19 │
└─────────┘                  └──────┘
```

**Note**: Servo color codes may vary:
- Red/Orange = Power (5V)
- Brown/Black = Ground
- Yellow/White/Orange = Signal

## Motor Driver Wiring (L298N Example)

```
        L298N Motor Driver
        ┌──────────────────────┐
        │                      │
ESP32   │   IN1 ←──────────────│ GPIO 25
        │   IN2 ←──────────────│ GPIO 26
        │   ENA ←──────────────│ GPIO 27 (PWM)
        │                      │
        │   OUT1 ──────────────│ Motor +
Motor   │   OUT2 ──────────────│ Motor -
        │                      │
        │   +12V ←─────────────│ 12V Supply
        │   GND ────────────── │ Common GND
        │                      │
        │   +5V ──────────────→│ (Optional: Power ESP32)
        │                      │
        └──────────────────────┘

Notes:
- Remove ENA jumper if using PWM speed control
- 5V output can power ESP32 (but not through USB simultaneously)
- Use common ground for all components
```

## Alternative Motor Driver (TB6612FNG)

Smaller, more efficient for low-power motors:

```
       TB6612FNG Motor Driver
       ┌──────────────────────┐
       │                      │
ESP32  │   AIN1 ←─────────────│ GPIO 25
       │   AIN2 ←─────────────│ GPIO 26
       │   PWMA ←─────────────│ GPIO 27
       │                      │
       │   AO1 ───────────────│ Motor +
Motor  │   AO2 ───────────────│ Motor -
       │                      │
       │   VM ←───────────────│ Motor Supply (12V)
       │   VCC ←──────────────│ Logic Supply (3.3V from ESP32)
       │   GND ───────────────│ Common GND
       │   STBY ──────────────│ 3.3V (standby disable)
       │                      │
       └──────────────────────┘
```

## Power Supply Recommendations

### Option 1: Separate Supplies
- **ESP32**: USB power (5V 500mA)
- **Servos**: 5V 2A wall adapter
- **Motor**: 12V battery or wall adapter

**Advantages**: Isolated, no noise interference
**Disadvantages**: Multiple power sources needed

### Option 2: Single Supply with Regulator
- **Main Supply**: 12V 3A
- **Buck Converter**: 12V → 5V (for servos and ESP32)

```
12V Supply
    │
    ├─→ Motor Driver (12V)
    │
    └─→ Buck Converter (12V→5V)
            │
            ├─→ Servos (5V)
            └─→ ESP32 (5V via VIN pin)
```

### Option 3: Battery Powered
- **Battery**: 3S LiPo (11.1V) or 3x 18650 cells
- **BEC**: For 5V servo/ESP32 power

## Complete Breadboard Layout

```
          ┌────────────────────────────────────────┐
          │              Breadboard                │
          │                                        │
    ESP32 │  ┌──────┐                             │
    ─────→│──│ IO18 │──────→ Pan Servo Signal     │
    ─────→│──│ IO19 │──────→ Tilt Servo Signal    │
    ─────→│──│ IO25 │──────→ Motor Driver IN1     │
    ─────→│──│ IO26 │──────→ Motor Driver IN2     │
    ─────→│──│ IO27 │──────→ Motor Driver ENA     │
          │  │      │                             │
    ─────→│──│ GND  │──────→ Common Ground Rail   │
    ─────→│──│ 5V   │──────→ 5V Power Rail        │
          │  └──────┘                             │
          │                                        │
          │  Ground Rail ─────────────────────────│
          │    │  │   │   │                       │
          │    │  │   │   └──→ Servo 1 GND        │
          │    │  │   └──────→ Servo 2 GND        │
          │    │  └──────────→ Motor Driver GND   │
          │    └─────────────→ Power Supply GND   │
          │                                        │
          │  5V Rail ─────────────────────────────│
          │    │  │                               │
          │    │  └──────────→ Servo 1 VCC        │
          │    └─────────────→ Servo 2 VCC        │
          │                                        │
          └────────────────────────────────────────┘
```

## PCB Design (Advanced)

For a permanent installation, consider a custom PCB:

### Features:
- ESP32 module socket
- 2x Servo headers (3-pin)
- Motor driver integrated or socket
- Power input terminals
- LED status indicators
- Voltage regulators

### Layout:
```
┌─────────────────────────────────────┐
│  [12V IN] [GND]              [ESP32]│
│                                     │
│   [5V REG]          [Status LEDs]  │
│                                     │
│  [SERVO 1]  [SERVO 2]              │
│   │ │ │      │ │ │                 │
│                                     │
│  [MOTOR DRIVER]    [Motor Out]     │
│   IN1 IN2 ENA      + -             │
│                                     │
└─────────────────────────────────────┘
```

## Mechanical Assembly

### Servo Mounting for Pan/Tilt

```
        Pan Servo (Base)
             │
             │ Servo Horn
             │
             ▼
        ┌────────┐
        │ Tilt   │◄── Tilt Servo
        │ Bracket│
        └────────┘
             │
             │
             ▼
        [Camera or Flower]
```

### Flower Mechanism

```
     Motor with Gear
          │
          │ Drive Belt/Gear
          │
          ▼
    ┌──────────┐
    │  Flower  │
    │  Petals  │◄── Linked to close/open
    │          │
    └──────────┘
         │
         │ Mounted on
         │
    [Pan/Tilt Servos]
```

## Cable Management

### Recommended Wire Gauges:
- **Servo Signal**: 22-24 AWG
- **Servo Power**: 18-20 AWG
- **Motor Power**: 16-18 AWG
- **Logic Signals**: 22-24 AWG

### Cable Lengths:
- Keep servo cables < 30cm for clean signals
- Keep motor power cables as short as possible
- Use twisted pairs for motor power to reduce EMI
- Separate power and signal cables when possible

## Common Wiring Mistakes to Avoid

1. ❌ **Sharing servo power with ESP32 5V pin**
   - ESP32 can't supply enough current for servos
   - Use external 5V supply for servos

2. ❌ **No common ground**
   - All components must share a common ground
   - ESP32, motor driver, servos, power supplies

3. ❌ **Motor driver logic voltage mismatch**
   - Some drivers need 5V logic, ESP32 is 3.3V
   - Use level shifters or compatible driver

4. ❌ **Reversed motor polarity**
   - Check motor direction, swap wires if needed
   - Or invert in software

5. ❌ **No decoupling capacitors**
   - Add 100µF capacitor across motor terminals
   - Add 0.1µF capacitors near ESP32 power pins

## Testing Checklist

- [ ] All grounds connected together
- [ ] ESP32 powered and programming properly
- [ ] Servos centered at 90° on power-up
- [ ] Motor can turn both directions
- [ ] No unusual heat from any component
- [ ] WiFi connects successfully
- [ ] OSC commands received (check Serial Monitor)
- [ ] Servos respond to OSC commands
- [ ] Motor responds to OSC commands
- [ ] No interference between motor and servos

## Safety Features (Recommended)

```
   ┌─────────┐
   │ Fuse    │──→ From 12V Supply
   └─────────┘
   
   ┌─────────┐
   │ E-Stop  │──→ Motor Driver Enable
   └─────────┘
   
   ┌─────────┐
   │ Limit   │──→ GPIO Input (stop on trigger)
   │ Switch  │
   └─────────┘
```

## Troubleshooting Wiring Issues

| Symptom | Possible Cause | Solution |
|---------|----------------|----------|
| Servo jitters | Insufficient power | Use dedicated 5V 2A supply |
| Motor doesn't spin | Wrong wiring | Check IN1/IN2 connections |
| ESP32 resets | Voltage drop | Add capacitors, separate supplies |
| No WiFi | Poor power | Use quality USB cable/supply |
| Erratic behavior | EMI from motor | Add capacitors, separate cables |

## Datasheets and Resources

### ESP32
- [ESP32 Pinout](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/)
- [ESP32 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)

### Motor Drivers
- [L298N Datasheet](https://www.st.com/resource/en/datasheet/l298.pdf)
- [TB6612FNG Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)

### Servos
- [Servo Motor Basics](https://www.electronics-tutorials.ws/io/io_5.html)
- Standard hobby servos: 4.8-6V, 1-2A peak per servo

## Bill of Materials (BOM)

| Component | Quantity | Notes |
|-----------|----------|-------|
| ESP32 Dev Board | 1 | Any ESP32 with WiFi |
| Servo Motor (SG90) | 2 | Or similar 9g servo |
| DC Motor | 1 | 6-12V, appropriate for flower |
| Motor Driver | 1 | L298N or TB6612FNG |
| 5V 2A Power Supply | 1 | For servos |
| 12V Power Supply | 1 | For motor (if needed) |
| Jumper Wires | ~20 | Male-to-male and male-to-female |
| Breadboard | 1 | Full-size recommended |
| Capacitor 100µF | 1 | For motor noise suppression |
| Capacitor 0.1µF | 3 | For decoupling |

**Total estimated cost**: $30-50 USD

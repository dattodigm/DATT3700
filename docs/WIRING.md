# Hardware Wiring Guide

## esp32_sylvie — DC Motor Flower

### Components
- 1× ESP32 development board
- 2× DC motors (flower open/close mechanism)
- 2× RGB LEDs (status & ambient lighting)
- 1× H-bridge motor driver (e.g. L298N or similar)

### Pin Assignments

| Signal | GPIO | Notes |
|--------|------|-------|
| Motor A (+) | 25 | M1_A |
| Motor A (−) | 26 | M1_B |
| Motor B (+) | 18 | M2_A |
| Motor B (−) | 19 | M2_B |
| LED1 Red    | 2  | 220Ω–330Ω resistor in series (adjust for LED Vf) |
| LED1 Green  | 4  | 220Ω–330Ω resistor in series |
| LED1 Blue   | 5  | 220Ω–330Ω resistor in series |
| LED2 Red    | 12 | 220Ω–330Ω resistor in series |
| LED2 Green  | 13 | 220Ω–330Ω resistor in series |
| LED2 Blue   | 14 | 220Ω–330Ω resistor in series |

### WiFi / OSC
- **Mode**: Access Point (AP)
- **SSID**: `ESP32_Sylvie`
- **Password**: `12345678`
- **IP**: `192.168.4.1`
- **OSC Port**: `8888`

---

## esp32_sue — Servo Flower

### Components
- 1× ESP32 development board
- 1× Servo motor (petal mechanism, 60°–120° range)
- 1× HC-SR04 ultrasonic distance sensor

### Pin Assignments

| Signal | GPIO | Notes |
|--------|------|-------|
| Ultrasonic TRIG | 27 | |
| Ultrasonic ECHO | 33 | |
| Servo PWM       | 14 | 50Hz, 500–2400µs pulse |

### Physical Limits
- Closed angle: **60°**
- Open angle: **120°**
- Opens when distance ≤ 20 cm
- Closes when distance ≥ 40 cm

---

## Power Supply Notes

- ESP32: 3.3 V logic, 5 V USB or external
- DC motors: require separate 5–12 V supply via H-bridge
- Servo: 5 V (powered directly from ESP32 5V pin for low-torque servos)
- LEDs: connect 220 Ω–330 Ω resistor from GPIO to LED anode; cathode to GND

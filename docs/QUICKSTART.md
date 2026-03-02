# Quick Start Guide

## 1. Install Python dependencies

```bash
cd python_controller
pip install -r requirements.txt
```

## 2. Flash ESP32 firmware

Open `esp32_firmware/eps32_sylvie/esp32_sylvie.ino` in Arduino IDE and upload to your ESP32 board.

Default WiFi hotspot: **SSID = `ESP32_Sylvie`**, **Password = `12345678`**

## 3. Connect PC to ESP32 hotspot

Connect your laptop to the `ESP32_Sylvie` WiFi network.
The ESP32 will be at `192.168.4.1`.

## 4. Run the control panel

```bash
cd python_controller
python main.py
```

The Tkinter control panel opens. The webcam preview and perception data should update in real time.

## 5. Quick test — manual control

1. In the **Manual Control** section, select `sylvie` from the Device dropdown.
2. Drag **Motor 1** slider to 1.0 and click **Send Manual** — the flower should open.
3. Set Motor 1 to -1.0 and send — the flower should close.

## 6. Record training samples & train ML

1. Stand in front of the camera in different poses/expressions.
2. Select a **Persona Label** (e.g. `Empathy`) and click **⏺ Record Sample**.
3. Record at least 10 samples across different personas.
4. Click **🏋 Train Model**.
5. Click **▶ Auto Mode: ON** — the flowers now respond automatically.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No camera preview | Check `camera_id` in `config.ini` |
| Motor does not move | Verify PC is on `ESP32_Sylvie` WiFi; check IP 192.168.4.1 |
| DeepFace errors | Install: `pip install deepface` or set `emotion_backend = haar` in config.ini |
| MediaPipe errors | Install: `pip install mediapipe` or set `enable_pose = false` |

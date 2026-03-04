# ESP32 Multi-File Firmware Flashing Guide

> **Target audience**: Teammates new to Arduino / ESP32 development  
> **Last updated**: 2026-03-04

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Arduino IDE](#2-install-arduino-ide)
3. [Configure ESP32 Board Support](#3-configure-esp32-board-support)
4. [Install Required Libraries](#4-install-required-libraries)
5. [Understanding Multi-File Arduino Projects](#5-understanding-multi-file-arduino-projects)
6. [Opening the Project](#6-opening-the-project)
7. [Project File Structure](#7-project-file-structure)
8. [Configuring Your Node](#8-configuring-your-node)
9. [Uploading (Flashing) the Firmware](#9-uploading-flashing-the-firmware)
10. [Verifying the Upload](#10-verifying-the-upload)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

You will need:

- **A computer** (Windows / macOS / Linux)
- **A USB cable** (Micro-USB or USB-C, depending on your ESP32 board)
- **An ESP32 development board** (e.g., ESP32-DevKitC, NodeMCU-32S)

---

## 2. Install Arduino IDE

1. Go to [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
2. Download **Arduino IDE 2.x** (recommended) for your operating system
3. Install and open the IDE

---

## 3. Configure ESP32 Board Support

The Arduino IDE does not support ESP32 by default. You need to add it:

1. Open Arduino IDE
2. Go to **File → Preferences** (macOS: **Arduino IDE → Settings**)
3. In the **"Additional boards manager URLs"** field, paste:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for **"esp32"**
7. Install **"esp32 by Espressif Systems"** (latest version)
8. After installation, go to **Tools → Board** and select **"ESP32 Dev Module"**

---

## 4. Install Required Libraries

Our firmware uses several libraries. Install them through the Library Manager:

1. Go to **Sketch → Include Library → Manage Libraries** (or click the library icon in the left sidebar in IDE 2.x)
2. Search for and install each of the following:

| Library Name | Author | What It Does |
|---|---|---|
| **OSC** | Adrian Freed, Yotam Mann | OSC protocol for motor/LED control |
| **ESPAsyncWebServer** | Me-No-Dev (lacamera) | Async HTTP server for `/config` endpoint |
| **AsyncTCP** | Me-No-Dev (dvarrel) | Required dependency for ESPAsyncWebServer |

> **Note**: `WiFi.h`, `ESPmDNS.h`, and `WiFiUdp.h` are **built-in** with the ESP32 board package — no separate installation needed.

### Alternative: Install via .zip

If you cannot find a library in the Library Manager:
1. Download the `.zip` file from GitHub
2. Go to **Sketch → Include Library → Add .ZIP Library**
3. Select the downloaded `.zip` file

---

## 5. Understanding Multi-File Arduino Projects

### How Arduino Handles Multiple Files

Arduino uses a **folder-based** project structure:

- The main `.ino` file **must have the same name as its parent folder**
  - Example: `eps32_sylvie/esp32_sylvie.ino` ✅
  - Example: `my_project/sketch.ino` ❌ (names don't match)
- All `.h` (header) and `.cpp` (source) files **in the same folder** are automatically included in compilation
- You do **not** need to manually add files to a build system

### Our Project Files

```
eps32_sylvie/                    ← Project folder name
├── esp32_sylvie.ino             ← Main sketch (must match folder name)
├── config.h                     ← Configuration (edit this!)
├── NetworkManager.h             ← Network module header
└── NetworkManager.cpp           ← Network module implementation
```

### How It Works

1. `esp32_sylvie.ino` includes `config.h` and `NetworkManager.h` via `#include`
2. Arduino IDE automatically compiles `NetworkManager.cpp` because it's in the same folder
3. `config.h` defines all configurable values (WiFi name, password, mode, etc.)

---

## 6. Opening the Project

1. Clone or download this repository
2. In Arduino IDE, go to **File → Open**
3. Navigate to `esp32_firmware/eps32_sylvie/`
4. Select `esp32_sylvie.ino`
5. The IDE will show **all files in tabs** at the top (`.ino`, `.h`, `.cpp`)

> **Important**: Do NOT move individual files out of the folder. All files must stay together.

---

## 7. Project File Structure

| File | Purpose | Do You Need to Edit? |
|---|---|---|
| `esp32_sylvie.ino` | Main program with `setup()` and `loop()` | Only for motor/LED logic |
| `config.h` | All configuration settings | **Yes** — set your WiFi, node type, etc. |
| `NetworkManager.h` | Network class declaration | No (unless adding features) |
| `NetworkManager.cpp` | Network class implementation | No (unless adding features) |

---

## 8. Configuring Your Node

Before uploading, edit `config.h` to match your setup:

### Choose Network Mode

```cpp
// To use as a WiFi hotspot (default, recommended for testing):
#define NETWORK_MODE NETWORK_MODE_AP

// To connect to an existing WiFi router:
#define NETWORK_MODE NETWORK_MODE_STA
```

### Set WiFi Credentials

**For AP mode** (ESP32 creates its own WiFi):
```cpp
#define AP_SSID     "ESP32_Sylvie"    // Name of the WiFi hotspot
#define AP_PASSWORD "12345678"         // Password (min 8 characters)
```

**For STA mode** (ESP32 connects to your router):
```cpp
#define STA_SSID     "YourWiFiName"       // Your router's WiFi name
#define STA_PASSWORD "YourWiFiPassword"   // Your router's password
```

### Set Node Identity

```cpp
#define NODE_TYPE "sylvie"      // What kind of node: "sylvie", "sue", "kait", "face_track"
#define NODE_ID   "sylvie_1"    // Unique name for this specific ESP32
```

---

## 9. Uploading (Flashing) the Firmware

### Step-by-Step

1. **Connect** your ESP32 to your computer via USB
2. In Arduino IDE, go to **Tools** and set:
   - **Board**: "ESP32 Dev Module"
   - **Port**: Select the COM port that appeared when you plugged in the ESP32
     - Windows: `COM3`, `COM4`, etc.
     - macOS: `/dev/cu.usbserial-xxxx` or `/dev/cu.SLAB_USBtoUART`
     - Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`
   - **Upload Speed**: 115200 (default is fine)
3. Click the **Upload button** (→ arrow icon) or press `Ctrl+U` / `Cmd+U`
4. Wait for compilation and upload to complete
5. You should see "Done uploading" in the output panel

### What Happens During Upload

1. **Compile**: IDE compiles ALL files (`.ino`, `.cpp`, `.h`) together
2. **Link**: Combines compiled code with ESP32 libraries
3. **Flash**: Writes the binary to the ESP32's flash memory
4. **Reset**: ESP32 automatically restarts with new firmware

---

## 10. Verifying the Upload

1. Open **Tools → Serial Monitor** (or click the magnifying glass icon)
2. Set baud rate to **115200** (dropdown in bottom-right)
3. Press the **RST (Reset)** button on your ESP32
4. You should see output like:

```
[NetworkManager] Starting AP mode... / 正在启动热点模式...
[NetworkManager] AP started. SSID: ESP32_Sylvie
[NetworkManager] AP IP address / 热点 IP 地址: 192.168.4.1
[NetworkManager] mDNS started: sylvie_1.local
[NetworkManager] Web server started on port 80
```

### Testing the Network

**In AP mode:**
1. On your phone or laptop, look for WiFi network "ESP32_Sylvie"
2. Connect with password "12345678"
3. Open a browser and go to `http://192.168.4.1/config`
4. You should see JSON data describing the node

**In STA mode:**
1. The Serial Monitor will show the IP address assigned by your router
2. Open a browser on the same network and go to `http://<IP>/config`

---

## 11. Troubleshooting

### "Port not found" / No COM port appears

- **Install USB drivers**: Some ESP32 boards use CH340 or CP2102 chips
  - CH340 driver: [https://www.wch.cn/downloads/CH341SER_ZIP.html](https://www.wch.cn/downloads/CH341SER_ZIP.html)
  - CP2102 driver: [https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- Try a different USB cable (some cables are charge-only, not data cables)
- Try a different USB port

### "Compilation error" / Build fails

- Make sure **ALL files** are in the same folder
- Make sure the folder name matches the `.ino` file name
- Verify all libraries are installed (see [Section 4](#4-install-required-libraries))
- Check that ESP32 board support is installed (see [Section 3](#3-configure-esp32-board-support))

### "Upload failed" / Cannot flash

- Hold the **BOOT** button on the ESP32 while clicking Upload
- Release the BOOT button when you see "Connecting..." in the output
- Try reducing upload speed: **Tools → Upload Speed → 115200**

### WiFi not working

- In AP mode: check that the password is at least 8 characters
- In STA mode: double-check your router's SSID and password in `config.h`
- Open Serial Monitor to see error messages

### "ESPAsyncWebServer not found"

- This library may not appear in the default Library Manager
- Download manually from: [https://github.com/me-no-dev/ESPAsyncWebServer](https://github.com/me-no-dev/ESPAsyncWebServer)
- Also download AsyncTCP: [https://github.com/me-no-dev/AsyncTCP](https://github.com/me-no-dev/AsyncTCP)
- Install both via **Sketch → Include Library → Add .ZIP Library**

---

## Quick Reference Card

| Action | How |
|---|---|
| Open project | File → Open → select `esp32_sylvie.ino` |
| Change WiFi settings | Edit `config.h` |
| Upload to ESP32 | Click → (Upload) button |
| Check output | Tools → Serial Monitor (115200 baud) |
| Test network | Connect to WiFi, browse to IP address |
| Find IP address | Check Serial Monitor after reset |

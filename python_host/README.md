# python_host

Flask control panel for DATT3700 multi-node ESP32 setup.

## Features

- mDNS scan for ESP32 nodes (`_datt_flower._tcp`, `_osc._udp`)
- Gateway fallback scan via OSC (`/info/clients`, `/info/self`)
- Discovery API compatibility routes (`/api/devices/scan` and `/api/discovery/*`)
- Node-type-aware control rendering for `sylvie`, `sue`, `kait`, `face_track`
- `sylvie` manual control UX: signed motor sliders (-255..255), dead-zone snap, and 2D drive pad
- Face-tracking coordinate publisher with transport switch (`OSC / Wi-Fi` or `USB serial`)
- Face-tracking panel actions: auto tracking ON/OFF, transport config, serial port connect
- Optional serial debug command sender (`POST /api/serial/raw`)
- Offline CSS fallback (`ui/static/panel-fallback.css`) when Tailwind CDN is unreachable
- Universal raw OSC console with send/receive history
- Motion sequence recorder with label folders (`data/sequences/<label>`)

## Quick start

```bash
python -m pip install -r python_host/requirements.txt
python -m python_host.main --port 15000
```

Open `http://127.0.0.1:15000`.

## New machine ML bootstrap (ViT + DeepFace)

Use this once per new device to download and cache ML model assets locally:

```bash
python -m pip install -r python_host/requirements-ml.txt
python -m python_host.bootstrap_ml_models --verify-vit-local
```

What this does:
- Downloads `yst007/vit-emotion` into `python_host/models/vit-emotion`
- Warms up DeepFace emotion inference so model weights are cached
- Verifies ViT can load in local-only mode

Recommended offline validation:
1. Disconnect network
2. Start the app: `python -m python_host.main --port 15000`
3. Confirm emotion inference still works for both ViT and DeepFace

## Key API endpoints

- `POST /api/devices/scan` with `{"mode":"mdns|gateway|auto"}`
- `GET /api/discovery/mdns`
- `POST /api/discovery/gateway`
- `POST /api/discovery/auto`
- `GET /api/devices`
- `POST /api/devices/select`
- `POST /api/osc/raw`
- `GET /api/osc/history`
- `POST /api/osc/history/clear`
- `GET /api/serial/ports?scan=1`
- `POST /api/serial/raw`
- `GET|POST /api/tracking/config`
- `POST /api/sequences/save`
- `GET /api/sequences/list`
- `GET /api/sequences/load?label=<label>&name=<name>`

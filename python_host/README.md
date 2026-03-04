# python_host

Flask control panel for DATT3700 multi-node ESP32 setup.

## Features

- mDNS scan for ESP32 nodes (`_datt_flower._tcp`, `_osc._udp`)
- Gateway fallback scan via OSC (`/info/clients`, `/info/self`)
- Node-type-aware control rendering for `sylvie`, `sue`, `face_track`
- Universal raw OSC console with send/receive history

## Quick start

```bash
python -m pip install -r python_host/requirements.txt
python -m python_host.main --port 5000
```

Open `http://127.0.0.1:5000`.

## Key API endpoints

- `POST /api/devices/scan` with `{"mode":"mdns|gateway|auto"}`
- `GET /api/devices`
- `POST /api/devices/select`
- `POST /api/osc/raw`
- `GET /api/osc/history`


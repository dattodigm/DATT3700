"""
main.py — Entry point for the DATT3700 Python host system.

Usage:
    python -m python_host.main --port 15000
    python -m python_host.main --camera 1 --camera-autostart
"""

import argparse

from python_host.ui.app import app


def main():
    parser = argparse.ArgumentParser(description="DATT3700 Flower Control Host")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--no-camera", action="store_true", help="Disable camera")
    parser.add_argument("--camera-autostart", action="store_true", help="Start camera automatically at launch")
    parser.add_argument("--esp", type=str, default="192.168.4.1", help="ESP32 IP")
    parser.add_argument("--port", type=int, default=15000, help="Flask port")
    args = parser.parse_args()

    import python_host.ui.app as app_module

    # Configure default OSC target in the shared device registry.
    app_module._register_device(
        {
            "name": "sylvie_1",
            "ip": args.esp,
            "port": 8888,
            "node_type": "sylvie",
            "source": "startup",
            "metadata": {},
        }
    )
    app_module._selected_device = "sylvie_1"
    app_module._set_control_mode(app_module.CONTROL_MODE_EMOTION_MANUAL, sync_target=False)
    app_module._set_camera_index(args.camera)

    # Auto-discover LAN devices once at startup for showcase flow.
    try:
        discovered = app_module._scan_and_register_devices(mode="auto", timeout_sec=1.2, gateway_ip=args.esp, gateway_port=8888)
        print(f"Startup scan complete: {len(discovered)} device(s) discovered")
    except Exception as exc:
        print(f"Startup scan failed: {exc}")

    # Camera remains OFF by default. Opt-in only.
    if args.camera_autostart and not args.no_camera:
        ok, detail = app_module._start_camera(index=args.camera)
        if not ok:
            print(f"Camera autostart failed: {detail}")

    print(f"Starting DATT3700 control panel on http://0.0.0.0:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()

"""
main.py — Entry point for the DATT3700 Python host system.

Usage:
    python -m python_host.main                    # defaults
    python -m python_host.main --camera 1         # use camera 1
    python -m python_host.main --no-camera        # no camera (UI only)
    python -m python_host.main --esp 192.168.4.1  # ESP32 target IP
"""

import argparse

from python_host.ui.app import app, osc


def main():
    parser = argparse.ArgumentParser(description="DATT3700 Flower Control Host")
    parser.add_argument("--camera", type=int, default=0, help="Camera index")
    parser.add_argument("--no-camera", action="store_true", help="Disable camera")
    parser.add_argument("--esp", type=str, default="192.168.4.1", help="ESP32 IP")
    parser.add_argument("--port", type=int, default=5000, help="Flask port")
    args = parser.parse_args()

    # Configure OSC target
    osc.add_target("sylvie_1", args.esp, 8888)

    # Start camera if enabled
    if not args.no_camera:
        from python_host.ui.app import tracker as app_tracker
        app_tracker.__init__(camera_index=args.camera)
        try:
            app_tracker.start()
        except RuntimeError as e:
            print(f"⚠️ Camera not available: {e}")

    print(f"🌸 Starting DATT3700 control panel on http://0.0.0.0:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()

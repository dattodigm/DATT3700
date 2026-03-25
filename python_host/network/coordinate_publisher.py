"""Background publisher for face-tracking coordinates (OSC or USB serial)."""

from __future__ import annotations

import threading
import time


class CoordinatePublisher:
    """Continuously publishes tracking coordinates using selected transport."""

    def __init__(
        self,
        get_primary_target,
        get_selected_target,
        get_selected_node_type,
        osc_sender,
        serial_sender=None,
        frame_width=1920,
        frame_height=1080,
    ):
        self._get_primary_target = get_primary_target
        self._get_selected_target = get_selected_target
        self._get_selected_node_type = get_selected_node_type
        self._osc = osc_sender
        self._serial = serial_sender

        self._frame_width = int(frame_width)
        self._frame_height = int(frame_height)

        self._enabled = False
        self._transport = "osc"
        self._rate_hz = 20.0
        self._deadband = 0.01

        self._last_norm = None
        self._last_sent_ts = 0.0
        self._last_result = "idle"

        self._lock = threading.Lock()
        self._stop_evt = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def update_config(
        self,
        *,
        enabled=None,
        transport=None,
        rate_hz=None,
        deadband=None,
        frame_width=None,
        frame_height=None,
    ):
        with self._lock:
            if enabled is not None:
                self._enabled = bool(enabled)
            if transport is not None:
                candidate = str(transport).lower().strip()
                if candidate in ("osc", "serial"):
                    self._transport = candidate
            if rate_hz is not None:
                self._rate_hz = max(1.0, float(rate_hz))
            if deadband is not None:
                self._deadband = max(0.0, float(deadband))
            if frame_width is not None:
                self._frame_width = max(1, int(frame_width))
            if frame_height is not None:
                self._frame_height = max(1, int(frame_height))

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "enabled": self._enabled,
                "transport": self._transport,
                "rate_hz": self._rate_hz,
                "deadband": self._deadband,
                "frame_width": self._frame_width,
                "frame_height": self._frame_height,
                "last_sent_ts": self._last_sent_ts,
                "last_result": self._last_result,
            }

    def stop(self):
        self._stop_evt.set()
        self._thread.join(timeout=1.0)

    def _should_send(self, nx, ny, deadband):
        if self._last_norm is None:
            return True
        lx, ly = self._last_norm
        return abs(nx - lx) >= deadband or abs(ny - ly) >= deadband

    def _run(self):
        while not self._stop_evt.is_set():
            cfg = self.snapshot()
            period = 1.0 / max(cfg["rate_hz"], 1.0)

            if not cfg["enabled"]:
                time.sleep(min(period, 0.2))
                continue

            # Target tuple may carry extra metadata (e.g. weighted total area).
            target = self._get_primary_target()
            if not target or len(target) < 2:
                with self._lock:
                    self._last_result = "no_face"
                time.sleep(period)
                continue

            nx = max(0.0, min(1.0, float(target[0])))
            ny = max(0.0, min(1.0, float(target[1])))
            if not self._should_send(nx, ny, cfg["deadband"]):
                time.sleep(period)
                continue

            sent = False
            result = "not_sent"
            if cfg["transport"] == "osc":
                target_name = self._get_selected_target()
                if target_name:
                    node_type = str(self._get_selected_node_type() or "unknown").lower().strip()
                    if node_type in ("sue", "face_track"):
                        sent = self._osc.send_raw(
                            target_name,
                            "/track/norm",
                            [round(nx, 4), round(ny, 4)],
                            source="auto",
                        )
                        result = "osc_ok" if sent else "osc_failed"
                    else:
                        result = f"unsupported_node:{node_type}"
                else:
                    result = "no_target"
            else:
                if self._serial is not None:
                    px = int(nx * cfg["frame_width"])
                    py = int(ny * cfg["frame_height"])
                    sent = self._serial.send_xy(px, py)
                    result = "serial_ok" if sent else "serial_failed"
                else:
                    result = "serial_unavailable"

            if sent:
                self._last_norm = (nx, ny)
                with self._lock:
                    self._last_sent_ts = time.time()
                    self._last_result = result
            else:
                with self._lock:
                    self._last_result = result

            time.sleep(period)


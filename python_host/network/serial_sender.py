"""Minimal serial coordinate sender with optional lazy pyserial loading."""

from __future__ import annotations

import importlib
import threading


class SerialCoordinateSender:
    """Sends face coordinates or raw lines over USB serial to ESP32 firmware."""

    def __init__(self):
        self._lock = threading.Lock()
        self._conn = None
        self._port = ""
        self._baud = 115200
        self._last_error = ""
        self._serial_mod = None
        self._list_ports_mod = None

    def _ensure_pyserial(self) -> bool:
        if self._serial_mod is not None and self._list_ports_mod is not None:
            return True
        try:
            self._serial_mod = importlib.import_module("serial")
            self._list_ports_mod = importlib.import_module("serial.tools.list_ports")
            self._last_error = ""
            return True
        except Exception as exc:  # pragma: no cover - environment dependent
            self._serial_mod = None
            self._list_ports_mod = None
            self._last_error = str(exc)
            return False

    @property
    def available(self) -> bool:
        # Do not import pyserial eagerly during app startup.
        if self._serial_mod is not None:
            return True
        return self._ensure_pyserial()

    def list_ports(self) -> list[dict]:
        if not self._ensure_pyserial():
            return []
        out = []
        for p in self._list_ports_mod.comports():
            out.append({"device": p.device, "description": p.description})
        return out

    def configure(self, port: str | None = None, baud: int | None = None):
        with self._lock:
            if port is not None:
                self._port = str(port).strip()
            if baud is not None:
                self._baud = int(baud)

    def connect(self) -> tuple[bool, str]:
        if not self._ensure_pyserial():
            return False, "pyserial not installed"

        with self._lock:
            if not self._port:
                return False, "serial port not configured"

            # Reuse existing connection if still valid.
            if self._conn and self._conn.is_open:
                if self._conn.port == self._port and int(self._conn.baudrate) == int(self._baud):
                    return True, "already connected"
                self._conn.close()
                self._conn = None

            try:
                self._conn = self._serial_mod.Serial(self._port, self._baud, timeout=0, write_timeout=0)
                self._last_error = ""
                return True, "connected"
            except Exception as exc:  # pragma: no cover - hardware dependent
                self._conn = None
                self._last_error = str(exc)
                return False, self._last_error

    def disconnect(self):
        with self._lock:
            if self._conn and self._conn.is_open:
                self._conn.close()
            self._conn = None

    def status(self) -> dict:
        with self._lock:
            connected = bool(self._conn and self._conn.is_open)
            return {
                "available": bool(self._serial_mod is not None or self._list_ports_mod is not None),
                "connected": connected,
                "port": self._port,
                "baud": int(self._baud),
                "last_error": self._last_error,
            }

    def send_line(self, text: str) -> bool:
        line = str(text or "").strip()
        if not line:
            return False
        if not line.endswith("\n"):
            line += "\n"

        with self._lock:
            conn = self._conn
        if conn is None or not conn.is_open:
            ok, _ = self.connect()
            if not ok:
                return False
            with self._lock:
                conn = self._conn

        try:
            conn.write(line.encode("ascii", errors="ignore"))
            return True
        except Exception as exc:  # pragma: no cover - hardware dependent
            with self._lock:
                self._last_error = str(exc)
            return False

    def send_xy(self, x: int, y: int) -> bool:
        return self.send_line(f"{int(x)},{int(y)}")

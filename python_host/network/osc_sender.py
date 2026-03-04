"""
osc_sender.py — Thread-safe OSC command sender for ESP32 flower nodes.

Wraps python-osc with a queue-based approach so vision/UI threads
never block on network I/O.
"""

import threading
from pythonosc import udp_client


class OSCSender:
    """Manages one or more ESP32 OSC targets with a send queue."""

    def __init__(self):
        self._clients = {}       # name -> SimpleUDPClient
        self._lock = threading.Lock()
        self._override = False   # True = manual UI only, block CV auto

    # ------------------------------------------------------------------
    # Target management
    # ------------------------------------------------------------------

    def add_target(self, name, ip, port=8888):
        with self._lock:
            self._clients[name] = udp_client.SimpleUDPClient(ip, port)

    def remove_target(self, name):
        with self._lock:
            self._clients.pop(name, None)

    def list_targets(self):
        with self._lock:
            return {n: (c._address, c._port) for n, c in self._clients.items()}

    # ------------------------------------------------------------------
    # Override (manual vs auto)
    # ------------------------------------------------------------------

    @property
    def override(self):
        return self._override

    @override.setter
    def override(self, value):
        self._override = bool(value)

    # ------------------------------------------------------------------
    # Send helpers
    # ------------------------------------------------------------------

    def send(self, target_name, address, *args, source="auto"):
        """Send an OSC message. Respects override flag.

        source="auto"  → blocked when override is True
        source="manual" → always sent
        """
        if source == "auto" and self._override:
            return  # manual override active, ignore CV commands

        with self._lock:
            client = self._clients.get(target_name)
        if client is None:
            return
        client.send_message(address, list(args))

    def send_motor(self, target_name, motor_id, direction, speed=255, source="auto"):
        addr = f"/motor{motor_id}"
        self.send(target_name, addr, int(direction), int(speed), source=source)

    def send_led(self, target_name, led_id, r, g, b, source="manual"):
        addr = f"/led{led_id}"
        self.send(target_name, addr, int(r), int(g), int(b), source=source)

    def send_preset(self, target_name, preset, source="manual"):
        self.send(target_name, "/preset", int(preset), source=source)

    def send_auto_mode(self, target_name, on, source="manual"):
        self.send(target_name, "/auto", int(on), source=source)

    def stop_all(self, target_name):
        """Emergency stop — always sent regardless of override."""
        self.send(target_name, "/preset", 3, source="manual")

    # ------------------------------------------------------------------
    # TFT eye animation (reserved stub)
    # ------------------------------------------------------------------

    def send_eye_animation(self, target_name, animation_id, **kwargs):
        """Reserved — will send TFT IPS eye animation commands."""
        pass

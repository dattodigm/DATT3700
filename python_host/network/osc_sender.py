"""
osc_sender.py — Thread-safe OSC command sender for ESP32 flower nodes.

Wraps python-osc with a queue-based approach so vision/UI threads
never block on network I/O.
"""

import socket
import struct
import threading
import time
from collections import deque

from pythonosc import udp_client


def _pad4(data: bytes) -> bytes:
    pad = (4 - (len(data) % 4)) % 4
    return data + (b"\x00" * pad)


def _build_osc_message(address, args=None):
    args = list(args or [])
    address_bin = _pad4(address.encode("utf-8") + b"\x00")

    type_tags = [","]
    payload = b""
    for arg in args:
        if isinstance(arg, int):
            type_tags.append("i")
            payload += struct.pack(">i", int(arg))
        else:
            type_tags.append("s")
            payload += _pad4(str(arg).encode("utf-8") + b"\x00")

    tag_bin = _pad4("".join(type_tags).encode("utf-8") + b"\x00")
    return address_bin + tag_bin + payload


def _read_osc_string(data, offset):
    end = data.find(b"\x00", offset)
    if end < 0:
        return "", len(data)
    value = data[offset:end].decode("utf-8", errors="ignore")
    next_offset = (end + 4) & ~0x03
    return value, next_offset


def _parse_osc_message(data):
    address, offset = _read_osc_string(data, 0)
    type_tags, offset = _read_osc_string(data, offset)

    args = []
    for tag in type_tags[1:]:  # skip leading comma
        if tag == "i":
            if offset + 4 > len(data):
                break
            args.append(struct.unpack(">i", data[offset:offset + 4])[0])
            offset += 4
        elif tag == "s":
            value, offset = _read_osc_string(data, offset)
            args.append(value)
        else:
            break

    return address, args


class OSCSender:
    """Manages one or more ESP32 OSC targets with a send queue."""

    def __init__(self, history_size=500):
        self._clients = {}       # name -> SimpleUDPClient
        self._target_info = {}   # name -> (ip, port)
        self._lock = threading.Lock()
        self._override = False   # True = manual UI only, block CV auto
        size = max(50, int(history_size))
        self._history = deque(maxlen=size)

    # ------------------------------------------------------------------
    # Target management
    # ------------------------------------------------------------------

    def add_target(self, name, ip, port=8888):
        with self._lock:
            self._clients[name] = udp_client.SimpleUDPClient(ip, port)
            self._target_info[name] = (ip, port)

    def remove_target(self, name):
        with self._lock:
            self._clients.pop(name, None)
            self._target_info.pop(name, None)

    def list_targets(self):
        with self._lock:
            return dict(self._target_info)

    # ------------------------------------------------------------------
    # Override (manual vs auto)
    # ------------------------------------------------------------------

    @property
    def override(self):
        return self._override

    @override.setter
    def override(self, value):
        self._override = bool(value)

    def _push_history(
        self,
        direction,
        address,
        args,
        target_name=None,
        ip=None,
        port=None,
        reason=None,
        source=None,
    ):
        item = {
            "ts": time.time(),
            "direction": direction,
            "target": target_name,
            "ip": ip,
            "port": port,
            "address": address,
            "args": list(args or []),
        }
        if reason is not None:
            item["reason"] = str(reason)
        if source is not None:
            item["source"] = str(source)
        with self._lock:
            self._history.append(item)

    def get_history(self, limit=80):
        n = max(1, int(limit))
        with self._lock:
            return list(self._history)[-n:]

    def clear_history(self):
        with self._lock:
            self._history.clear()

    def get_history_capacity(self):
        return int(self._history.maxlen or 0)

    # ------------------------------------------------------------------
    # Send helpers
    # ------------------------------------------------------------------

    def send(self, target_name, address, *args, source="auto"):
        """Send an OSC message. Respects override flag.

        source="auto"  → blocked when override is True
        source="manual" → always sent
        """
        if source == "auto" and self._override:
            self._push_history(
                "drop",
                address,
                args,
                target_name=target_name,
                reason="override_blocked",
                source=source,
            )
            return False  # manual override active, ignore CV commands

        with self._lock:
            client = self._clients.get(target_name)
            target = self._target_info.get(target_name)
        if client is None:
            self._push_history(
                "drop",
                address,
                args,
                target_name=target_name,
                reason="unknown_target",
                source=source,
            )
            return False
        try:
            client.send_message(address, list(args))
        except OSError as exc:
            ip, port = target if target else (None, None)
            self._push_history(
                "drop",
                address,
                args,
                target_name=target_name,
                ip=ip,
                port=port,
                reason=f"send_error:{exc}",
                source=source,
            )
            return False
        ip, port = target if target else (None, None)
        self._push_history(
            "tx",
            address,
            args,
            target_name=target_name,
            ip=ip,
            port=port,
            source=source,
        )
        return True

    def send_raw(self, target_name, address, args=None, source="manual"):
        return self.send(target_name, address, *(args or []), source=source)

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

    def send_track_norm(self, target_name, norm_x, norm_y, source="auto"):
        self.send(target_name, "/track/norm", float(norm_x), float(norm_y), source=source)

    def stop_all(self, target_name):
        """Emergency stop — always sent regardless of override."""
        self.send(target_name, "/preset", 3, source="manual")

    # ------------------------------------------------------------------
    # TFT eye animation (reserved stub)
    # ------------------------------------------------------------------

    def send_eye_animation(self, target_name, animation_id, **kwargs):
        """Reserved — will send TFT IPS eye animation commands."""
        pass

    # ------------------------------------------------------------------
    # Lightweight request/reply helpers for discovery endpoints
    # ------------------------------------------------------------------

    def _request_reply(self, ip, port, address, args=None, timeout=0.8):
        packet = _build_osc_message(address, args=args)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(timeout)
            sock.bind(("0.0.0.0", 0))
            sock.sendto(packet, (ip, int(port)))
            self._push_history("tx", address, args or [], ip=ip, port=port, source="query")
            data, src = sock.recvfrom(2048)
            reply_addr, reply_args = _parse_osc_message(data)
            self._push_history("rx", reply_addr, reply_args, ip=src[0], port=src[1], source="query")
            return {"address": reply_addr, "args": reply_args, "ip": src[0], "port": src[1]}
        except OSError:
            return None
        finally:
            sock.close()

    def query_info_self_ip(self, ip, port=8888, timeout=0.8):
        reply = self._request_reply(ip, port, "/info/self", timeout=timeout)
        if not reply or reply.get("address") != "/info/self":
            return None
        args = reply.get("args", [])
        if len(args) < 4:
            return None
        return {
            "name": str(args[0]),
            "mac": str(args[1]),
            "mode": str(args[2]),
            "ip": str(args[3]),
        }

    def query_info_clients_ip(self, ip, port=8888, timeout=0.8):
        reply = self._request_reply(ip, port, "/info/clients", timeout=timeout)
        if not reply or reply.get("address") != "/info/clients":
            return None

        args = reply.get("args", [])
        count = int(args[0]) if args and isinstance(args[0], int) else 0
        clients = []
        idx = 1
        while idx + 1 < len(args):
            clients.append({"mac": str(args[idx]), "ip": str(args[idx + 1])})
            idx += 2

        return {"count": count, "clients": clients}

    def query_info_self(self, target_name, timeout=0.8):
        with self._lock:
            target = self._target_info.get(target_name)
        if not target:
            return None
        ip, port = target
        return self.query_info_self_ip(ip, port, timeout=timeout)

    def query_info_clients(self, target_name, timeout=0.8):
        with self._lock:
            target = self._target_info.get(target_name)
        if not target:
            return None
        ip, port = target
        return self.query_info_clients_ip(ip, port, timeout=timeout)

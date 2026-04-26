#!/usr/bin/env python3
"""
Keyboard OSC tracker for 5.Animated_Eye12 firmware.

Features:
- Arrow keys / WASD move tracked point
- Sends /track/xy continuously (configurable Hz) in TRACK mode
- One-key center reset
- 1/2/3 switch modes: AUTO / TRACK / ANIM

Usage:
  python osc_track_keyboard.py --host 192.168.1.123
  python osc_track_keyboard.py --host eye_anime_1.local --width 640 --height 480
"""

from __future__ import annotations

import argparse
import curses
import socket
import struct
import time


def _pad4(data: bytes) -> bytes:
    return data + (b"\x00" * ((4 - (len(data) % 4)) % 4))


def _osc_string(text: str) -> bytes:
    return _pad4(text.encode("utf-8") + b"\x00")


def build_osc_message(address: str, args: list[object]) -> bytes:
    if not address.startswith("/"):
        raise ValueError("OSC address must start with '/'")
    tags = ","
    payload = bytearray()
    for arg in args:
        if isinstance(arg, bool):
            # Firmware expects int for /track/auto.
            tags += "i"
            payload.extend(struct.pack(">i", 1 if arg else 0))
        elif isinstance(arg, int):
            tags += "i"
            payload.extend(struct.pack(">i", arg))
        elif isinstance(arg, float):
            tags += "f"
            payload.extend(struct.pack(">f", arg))
        elif isinstance(arg, str):
            tags += "s"
            payload.extend(_osc_string(arg))
        else:
            raise TypeError(f"Unsupported OSC arg type: {type(arg)}")
    return _osc_string(address) + _osc_string(tags) + bytes(payload)


class OscUdpClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, address: str, *args: object) -> None:
        packet = build_osc_message(address, list(args))
        self.sock.sendto(packet, (self.host, self.port))

    def close(self) -> None:
        self.sock.close()


def clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))

MODE_AUTO = 0
MODE_TRACK = 1
MODE_ANIM = 2
MODE_NAME = {
    MODE_AUTO: "AUTO",
    MODE_TRACK: "TRACK",
    MODE_ANIM: "ANIM",
}


def run(stdscr: "curses._CursesWindow", cfg: argparse.Namespace) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(16)  # ~60 Hz UI refresh

    client = OscUdpClient(cfg.host, cfg.port)

    x = cfg.width // 2
    y = cfg.height // 2
    step = cfg.step
    mode = int(cfg.mode)
    track_enabled = True
    last_send = 0.0
    send_interval = 1.0 / max(1.0, float(cfg.hz))
    status = "ready"

    def send_xy() -> None:
        nonlocal last_send
        client.send("/track/xy", int(x), int(y), int(cfg.width), int(cfg.height))
        last_send = time.monotonic()

    try:
        client.send("/mode", mode)
        client.send("/track/auto", 1 if track_enabled else 0)
        if mode == MODE_TRACK:
            send_xy()

        while True:
            now = time.monotonic()
            key = stdscr.getch()
            moved = False

            if key in (ord("q"), ord("Q")):
                status = "quit"
                break
            elif key in (curses.KEY_LEFT, ord("a"), ord("A")):
                x = clamp(x - step, 0, cfg.width - 1)
                moved = True
            elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
                x = clamp(x + step, 0, cfg.width - 1)
                moved = True
            elif key in (curses.KEY_UP, ord("w"), ord("W")):
                y = clamp(y - step, 0, cfg.height - 1)
                moved = True
            elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
                y = clamp(y + step, 0, cfg.height - 1)
                moved = True
            elif key in (ord("c"), ord("C"), ord("0"), ord(" ")):
                x = cfg.width // 2
                y = cfg.height // 2
                client.send("/track/center")
                moved = True
                status = "center"
            elif key == ord("1"):
                mode = MODE_AUTO
                client.send("/mode", mode)
                status = "mode=AUTO"
            elif key == ord("2"):
                mode = MODE_TRACK
                client.send("/mode", mode)
                send_xy()
                status = "mode=TRACK"
            elif key == ord("3"):
                mode = MODE_ANIM
                client.send("/mode", mode)
                status = "mode=ANIM"
            elif key in (ord("+"), ord("=")):
                step = min(200, step + 1)
                status = f"step={step}"
            elif key in (ord("-"), ord("_")):
                step = max(1, step - 1)
                status = f"step={step}"
            elif key in (ord("m"), ord("M")):
                track_enabled = not track_enabled
                client.send("/track/auto", 1 if track_enabled else 0)
                status = f"/track/auto={1 if track_enabled else 0}"
            elif key in (ord("n"), ord("N")):
                nx = x / max(1, (cfg.width - 1))
                ny = y / max(1, (cfg.height - 1))
                client.send("/track/norm", float(nx), float(ny))
                status = "sent /track/norm"

            # Keep-alive sending only for TRACK mode.
            if mode == MODE_TRACK and (moved or (now - last_send >= send_interval)):
                send_xy()

            stdscr.erase()
            stdscr.addstr(0, 0, "OSC Keyboard Tracker")
            stdscr.addstr(1, 0, f"target: {cfg.host}:{cfg.port}")
            stdscr.addstr(2, 0, f"frame : {cfg.width} x {cfg.height}")
            stdscr.addstr(3, 0, f"xy    : ({x}, {y}) step={step}")
            stdscr.addstr(4, 0, f"mode  : {MODE_NAME.get(mode, '?')}")
            stdscr.addstr(5, 0, f"send  : /track/xy @{cfg.hz:.1f}Hz (TRACK only)")
            stdscr.addstr(6, 0, f"track : {'ENABLED' if track_enabled else 'DISABLED'}")
            stdscr.addstr(7, 0, "Arrows/WASD move | C/Space/0 center")
            stdscr.addstr(8, 0, "1=AUTO 2=TRACK 3=ANIM | M toggle /track/auto")
            stdscr.addstr(9, 0, "N send /track/norm once | Q quit")
            stdscr.addstr(11, 0, f"status: {status}")
            stdscr.refresh()

    finally:
        # Leave device in AUTO mode on exit.
        try:
            client.send("/mode", MODE_AUTO)
            client.send("/track/auto", 1)
            client.send("/track/center")
        except OSError:
            pass
        client.close()


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Keyboard OSC sender for eye tracking")
    ap.add_argument("--host", required=True, help="ESP32 hostname or IP (e.g. 192.168.1.50)")
    ap.add_argument("--port", type=int, default=8888, help="OSC UDP port (default: 8888)")
    ap.add_argument("--width", type=int, default=640, help="Input frame width sent to /track/xy")
    ap.add_argument("--height", type=int, default=480, help="Input frame height sent to /track/xy")
    ap.add_argument("--step", type=int, default=12, help="Move step in pixels per keypress")
    ap.add_argument("--hz", type=float, default=20.0, help="Continuous send rate for keep-alive")
    ap.add_argument("--mode", type=int, default=MODE_TRACK, choices=[0, 1, 2], help="Initial mode: 0=AUTO, 1=TRACK, 2=ANIM")
    args = ap.parse_args()
    if args.width < 2 or args.height < 2:
        raise SystemExit("width/height must be >= 2")
    if args.step < 1:
        raise SystemExit("step must be >= 1")
    if args.hz <= 0:
        raise SystemExit("hz must be > 0")
    return args


def main() -> int:
    args = parse_args()
    curses.wrapper(run, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

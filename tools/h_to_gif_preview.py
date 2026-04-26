#!/usr/bin/env python3
"""
Parse RGB565 uint16_t arrays from a C header (e.g. EYEA.h), preview as animation,
and optionally save an animated GIF.

Color notes (GC9D01 / TFT_eSPI):
  - The datasheet "Pixel n" layout (byte1 = R high + G high, byte2 = G low + B) is
    the usual RGB565 word: bits 15..11 R, 10..5 G, 4..0 B — same as this tool.
  - On ESP32, TFT_eSPI sends each pixel via pushPixels; whether the high or low
    byte goes out on MOSI first is controlled by tft.setSwapBytes(true/false).
    Default is false. Many 16-bit SPI panels match setSwapBytes(true) with flash
    images stored as normal 0xRRRR... RGB565 words (see TFT_Flash_Bitmap example).
    If the LCD looks wrong vs this preview, try toggling setSwapBytes in setup()
    before pushImage — do not assume the Python preview is wrong.
  - PC preview also shows ideal decode of 565; the panel maps to ~65k colors and
    may apply its own gamma — gradients will not match an 8-bit/sample source exactly.

Usage:
  python h_to_gif_preview.py path/to/EYEA.h
  python h_to_gif_preview.py EYEA.h --width 160 --height 160 --fps 14
  python h_to_gif_preview.py EYEA.h --out preview.gif --no-window

Drag-and-drop the .h file onto this script on Windows works the same as passing the path.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
    raise

# Matches: const uint16_t gImage_A1 [] PROGMEM {
ARRAY_START = re.compile(
    r"const\s+uint16_t\s+(\w+)\s*\[\s*\]\s*(?:PROGMEM)?\s*\{",
    re.IGNORECASE,
)
HEX_TOKEN = re.compile(r"0x[0-9a-fA-F]+")


def _rgb565_to_rgb(w: int) -> tuple[int, int, int]:
    w &= 0xFFFF
    r5 = (w >> 11) & 0x1F
    g6 = (w >> 5) & 0x3F
    b5 = w & 0x1F
    r = (r5 * 255 + 15) // 31
    g = (g6 * 255 + 31) // 63
    b = (b5 * 255 + 15) // 31
    return r, g, b


def _maybe_swap_bytes(w: int) -> int:
    return ((w & 0xFF) << 8) | ((w >> 8) & 0xFF)


def parse_header(text: str) -> list[tuple[str, list[int]]]:
    """Return [(name, [uint16 values]), ...] in source order."""
    arrays: list[tuple[str, list[int]]] = []
    pos = 0
    while True:
        m = ARRAY_START.search(text, pos)
        if not m:
            break
        name = m.group(1)
        brace = text.find("{", m.end() - 1)
        if brace < 0:
            break
        depth = 0
        i = brace
        end = -1
        while i < len(text):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
            i += 1
        if end < 0:
            break
        chunk = text[brace + 1 : end]
        vals = [int(x, 16) for x in HEX_TOKEN.findall(chunk)]
        arrays.append((name, vals))
        pos = end + 1
    return arrays


def infer_square_size(count: int) -> int | None:
    s = int(math.isqrt(count))
    if s * s == count:
        return s
    return None


def frame_to_image(
    words: list[int],
    width: int,
    height: int,
    swap_bytes: bool,
) -> Image.Image:
    if len(words) != width * height:
        raise ValueError(
            f"Expected {width * height} pixels, got {len(words)} "
            f"(try different --width/--height or check array)"
        )
    rgb = bytearray(width * height * 3)
    o = 0
    for w in words:
        if swap_bytes:
            w = _maybe_swap_bytes(w)
        r, g, b = _rgb565_to_rgb(w)
        rgb[o] = r
        rgb[o + 1] = g
        rgb[o + 2] = b
        o += 3
    return Image.frombytes("RGB", (width, height), bytes(rgb))


def save_animated_gif(frames: list[Image.Image], path: Path, duration_ms: int) -> None:
    if not frames:
        return
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )


def preview_tk(frames: list[Image.Image], fps: float) -> None:
    import tkinter as tk

    delay = max(1, int(1000 / fps))
    root = tk.Tk()
    root.title(f"RGB565 preview ({len(frames)} frames, {fps} fps)")
    label = tk.Label(root)
    label.pack()
    photos: list[ImageTk.PhotoImage] = []
    for im in frames:
        photos.append(ImageTk.PhotoImage(im))
    idx = 0

    def tick() -> None:
        nonlocal idx
        label.configure(image=photos[idx])
        label.image = photos[idx]  # keep ref
        idx = (idx + 1) % len(photos)
        root.after(delay, tick)

    tick()
    root.mainloop()


def main() -> int:
    ap = argparse.ArgumentParser(description="Preview / export GIF from RGB565 .h arrays")
    ap.add_argument("header", type=Path, help="Path to .h file (e.g. EYEA.h)")
    ap.add_argument("--width", type=int, default=None, help="Frame width (default: infer if square)")
    ap.add_argument("--height", type=int, default=None, help="Frame height (default: infer if square)")
    ap.add_argument(
        "--swap-bytes",
        action="store_true",
        help="Swap high/low byte before decoding (if colors look wrong, try this)",
    )
    ap.add_argument("--fps", type=float, default=1000 / 70.0, help="Preview & GIF frame rate (default ~14.3)")
    ap.add_argument("--out", type=Path, default=None, help="Write animated GIF to this path")
    ap.add_argument("--no-window", action="store_true", help="Do not open Tk preview (use with --out)")
    args = ap.parse_args()

    if not args.header.is_file():
        print(f"Not a file: {args.header}", file=sys.stderr)
        return 1

    text = args.header.read_text(encoding="utf-8", errors="replace")
    arrays = parse_header(text)
    if not arrays:
        print("No 'const uint16_t ... [] PROGMEM {' arrays found.", file=sys.stderr)
        return 1

    lens = {len(v) for _, v in arrays}
    if len(lens) != 1:
        print(f"Arrays have differing lengths {sorted(lens)}; cannot decode.", file=sys.stderr)
        return 1

    w = args.width
    h = args.height
    frames: list[Image.Image] = []
    for name, vals in arrays:
        if w is None or h is None:
            side = infer_square_size(len(vals))
            if side is None:
                print(
                    f"Array '{name}' has {len(vals)} values; not a perfect square. "
                    "Set --width and --height explicitly.",
                    file=sys.stderr,
                )
                return 1
            fw = fh = side
        else:
            fw, fh = w, h
        try:
            frames.append(frame_to_image(vals, fw, fh, args.swap_bytes))
        except ValueError as e:
            print(f"{name}: {e}", file=sys.stderr)
            return 1

    duration_ms = max(20, int(1000 / max(0.1, float(args.fps))))

    if args.out:
        save_animated_gif(frames, args.out, duration_ms)
        print(f"Wrote {args.out} ({len(frames)} frames, {duration_ms} ms/frame)")

    if not args.no_window:
        preview_tk(frames, max(0.1, float(args.fps)))

    return 0


if __name__ == "__main__":
    sys.exit(main())

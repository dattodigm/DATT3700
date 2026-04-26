#!/usr/bin/env python3
"""
Convert a folder of images to one C header with RGB565 uint16_t arrays (EYEA.h style).

PNG/JPEG/BMP etc. are read directly with Pillow — no need to convert to BMP first.

Output words are standard RGB565: (R5<<11)|(G6<<5)|B5, matching typical GC9D01
datasheet diagrams (first byte on the wire = high byte of that word when MSB-first).

Firmware (TFT_eSPI):
  - Call tft.setSwapBytes(true) or (false) so the driver sends bytes in the order
    your panel expects; wrong setting causes swapped channels / mud colors.
  - This is independent of #define TFT_RGB_ORDER in User_Setup.h for GC9D01
    (that macro is not used in GC9D01_Defines.h). Fix byte swap in sketch first.

Display vs PC:
  - Reduced to 5/6/5 bits per channel, so banding and hue shift vs original art
    are expected especially in shadows and skin tones.

Usage:
  python images_to_rgb565_header.py ./frames -o MyAnim.h --width 160 --height 160
  python images_to_rgb565_header.py ./frames --prefix gImage_A --start 1
  python images_to_rgb565_header.py ./frames --bg 0,0,0 --swap-bytes-output

Frame order: natural sort by filename (frame_2.png before frame_10.png).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Install dependencies: pip install -r requirements.txt", file=sys.stderr)
    raise

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}

_re_natural = re.compile(r"(\d+)")


def natural_key(s: str) -> list:
    return [int(t) if t.isdigit() else t.lower() for t in _re_natural.split(s)]


def rgb_to_rgb565(r: int, g: int, b: int) -> int:
    r5 = (r * 31 + 127) // 255
    g6 = (g * 63 + 127) // 255
    b5 = (b * 31 + 127) // 255
    return (r5 << 11) | (g6 << 5) | b5


def swap_u16(v: int) -> int:
    return ((v & 0xFF) << 8) | ((v >> 8) & 0xFF)


def parse_rgb_triplet(raw: str) -> tuple[int, int, int]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("RGB color must be like '0,0,0'")
    vals: list[int] = []
    for p in parts:
        try:
            n = int(p)
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"Invalid RGB value: {p}") from e
        if n < 0 or n > 255:
            raise argparse.ArgumentTypeError("RGB values must be 0..255")
        vals.append(n)
    return vals[0], vals[1], vals[2]


def image_to_words(
    im: Image.Image,
    width: int,
    height: int,
    bg_rgb: tuple[int, int, int],
    swap_bytes_output: bool,
) -> list[int]:
    # Normalize orientation before resize (important for phone-exported assets).
    im = ImageOps.exif_transpose(im)
    # Composite alpha onto a known background to avoid transparent pixel artifacts.
    rgba = im.convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
    flat = Image.alpha_composite(Image.new("RGBA", (width, height), (*bg_rgb, 255)), rgba).convert("RGB")
    im = flat
    px = im.load()
    out: list[int] = []
    for y in range(height):
        for x in range(width):
            r, g, b = px[x, y]
            w = rgb_to_rgb565(r, g, b)
            out.append(swap_u16(w) if swap_bytes_output else w)
    return out


def format_array_body(words: list[int], per_line: int) -> str:
    lines: list[str] = []
    for i in range(0, len(words), per_line):
        chunk = words[i : i + per_line]
        lines.append(", ".join(f"0x{v:04x}" for v in chunk) + ",")
    return "\n".join(lines)


def emit_header(
    frames: list[tuple[str, list[int]]],
    per_line: int,
) -> str:
    parts: list[str] = ["#pragma once", ""]
    for name, words in frames:
        parts.append(f"const uint16_t  {name} [] PROGMEM  {{")
        parts.append(format_array_body(words, per_line))
        parts.append("};")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def collect_images(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXT]
    files.sort(key=lambda p: natural_key(p.name))
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Folder of images -> RGB565 PROGMEM header")
    ap.add_argument("folder", type=Path, help="Directory containing image sequence")
    ap.add_argument("-o", "--output", type=Path, default=Path("frames_rgb565.h"))
    ap.add_argument("--width", type=int, required=True, help="Output width (e.g. 160)")
    ap.add_argument("--height", type=int, required=True, help="Output height (e.g. 160)")
    ap.add_argument("--prefix", default="gImage_A", help="Array name prefix (default: gImage_A)")
    ap.add_argument("--start", type=int, default=1, help="First numeric suffix for names (default: 1)")
    ap.add_argument(
        "--bg",
        type=parse_rgb_triplet,
        default=(0, 0, 0),
        help="Background color for alpha compositing as R,G,B (default: 0,0,0)",
    )
    ap.add_argument(
        "--swap-bytes-output",
        action="store_true",
        help="Emit byte-swapped RGB565 words (use if sketch keeps setSwapBytes(false))",
    )
    ap.add_argument(
        "--per-line",
        type=int,
        default=80,
        help="Comma-separated values per line in output (default: 80)",
    )
    args = ap.parse_args()

    if not args.folder.is_dir():
        print(f"Not a directory: {args.folder}", file=sys.stderr)
        return 1

    paths = collect_images(args.folder)
    if not paths:
        print(f"No images found in {args.folder} (extensions: {sorted(IMAGE_EXT)})", file=sys.stderr)
        return 1

    frames: list[tuple[str, list[int]]] = []
    n = args.start
    for p in paths:
        name = f"{args.prefix}{n}"
        n += 1
        try:
            im = Image.open(p)
            im.load()
        except OSError as e:
            print(f"Skip {p}: {e}", file=sys.stderr)
            continue
        words = image_to_words(im, args.width, args.height, args.bg, args.swap_bytes_output)
        frames.append((name, words))

    if not frames:
        print("No usable images.", file=sys.stderr)
        return 1

    text = emit_header(frames, max(1, args.per_line))
    args.output.write_text(text, encoding="utf-8")
    print(f"Wrote {args.output} ({len(frames)} frames, {args.width}x{args.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

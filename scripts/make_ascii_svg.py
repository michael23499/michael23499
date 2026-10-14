"""Convert scripts/source-prepped.png into an animated ASCII-art SVG portrait.

Each text row is revealed by a left-to-right clip wipe (SMIL), staggered from
top to bottom. The animation plays once and freezes on the final frame.

Usage:
    python scripts/make_ascii_svg.py [input.png] [output.svg]

Env overrides: COLS (default 100), ROWS (default 53), WIDTH (default 370),
BG=1 to paint a dark rounded background instead of a transparent one.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "scripts" / "source-prepped.png"
DEFAULT_OUTPUT = ROOT / "assets" / "ascii-portrait.svg"

FONT = "Fira Code, Consolas, Menlo, monospace"
RAMP = " .`:-=+*cs#%@"  # light -> dark (white background becomes blank)
FILL = "#ff8a8a"
BG = "#0a0a0d"
ROW_STAGGER = 0.045  # seconds between rows
WIPE_DURATION = 0.6


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def to_ascii(img: Image.Image, cols: int, rows: int) -> list[str]:
    gray = ImageOps.grayscale(img).resize((cols, rows), Image.LANCZOS)
    lum = np.asarray(gray, dtype=np.float32) / 255.0
    darkness = 1.0 - lum
    idx = np.clip((darkness * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def render(lines: list[str], cols: int, width: int, with_bg: bool) -> str:
    pad = 6
    char_w = (width - 2 * pad) / cols
    font_size = char_w / 0.6  # monospace advance is ~0.6em
    line_h = font_size * 1.15
    height = round(len(lines) * line_h + 2 * pad)

    out: list[str] = []
    w = out.append
    w(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
      f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}" role="img" '
      f'aria-label="Retrato ASCII de Michael Arismendi">')
    w("<defs>")
    for i in range(len(lines)):
        y = pad + i * line_h
        begin = 0.2 + i * ROW_STAGGER
        w(f'<clipPath id="r{i}"><rect x="0" y="{y:.2f}" width="0" '
          f'height="{line_h + 1:.2f}"><animate attributeName="width" from="0" '
          f'to="{width}" begin="{begin:.3f}s" dur="{WIPE_DURATION}s" '
          f'fill="freeze"/></rect></clipPath>')
    w("</defs>")
    if with_bg:
        w(f'<rect width="{width}" height="{height}" rx="14" fill="{BG}"/>')
    w(f'<g font-size="{font_size:.2f}" fill="{FILL}" xml:space="preserve">')
    for i, line in enumerate(lines):
        if not line:
            continue
        y = pad + i * line_h + font_size
        length = len(line) * char_w
        w(f'<text x="{pad}" y="{y:.2f}" clip-path="url(#r{i})" '
          f'textLength="{length:.2f}" lengthAdjust="spacingAndGlyphs">'
          f'{escape(line)}</text>')
    w("</g>")
    w("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    cols = env_int("COLS", 100)
    rows = env_int("ROWS", 53)
    width = env_int("WIDTH", 370)
    with_bg = os.environ.get("BG", "").strip() not in ("", "0", "false")

    lines = to_ascii(Image.open(src), cols, rows)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(lines, cols, width, with_bg), encoding="utf-8")
    print(f"wrote {dst} ({cols}x{rows} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

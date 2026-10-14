"""Render a neofetch-style info card as a self-contained animated SVG.

Output: assets/info-card.svg (~490px wide). Lines fade/slide in one after
another via CSS keyframes and stay on the final frame.

Usage:
    python scripts/make_info_card.py [output.svg]
    STATIC=1 python scripts/make_info_card.py   # frozen final frame, no motion
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "assets" / "info-card.svg"

FONT = "Fira Code, Consolas, Menlo, monospace"
BG = "#0a0a0d"
BAR = "#141416"
MUTED = "#8b8b93"
DIM = "#3a3a42"
TEXT = "#e2e8f0"
PRIMARY = "#ff3131"
ACCENT = "#fbbf24"
SWATCHES = ["#0d0d0d", "#3d1414", "#7a1f1f", "#c92a2a",
            "#ff3131", "#ff6b6b", "#fbbf24", "#e2e8f0"]

USER = "michael"
HOST = "github"
ROWS = [
    ("Name", "Michael Arismendi"),
    ("Role", "Full Stack Developer"),
    ("Focus", "AI & RAG Integration"),
    ("Uptime", "5+ años en producción"),
    ("Location", "Madrid, España"),
    ("Shell", "TypeScript · Go · Python"),
    ("Web", "React · Next.js · Angular · Node.js"),
    ("Backend", "FastAPI · Laravel · Django"),
    ("Data", "PostgreSQL · MongoDB · Supabase · BigQuery"),
    ("Cloud", "AWS Lambda · GCP · Docker · Vercel"),
    ("AI", "Claude · Gemini · Groq · LangChain · Ollama"),
]
QUOTE = "si no sobrevive a usuarios reales, no está terminado"

WIDTH = 490
PAD_X = 24
LABEL_W = 92
LINE_H = 22
FIRST_DELAY = 0.25
STAGGER = 0.11


def render(static: bool) -> str:
    top = 74
    header_h = 2 * LINE_H
    rows_y = top + header_h + 6
    quote_y = rows_y + len(ROWS) * LINE_H + 18
    swatch_y = quote_y + 22
    prompt_y = swatch_y + 50
    height = prompt_y + 22

    out: list[str] = []
    w = out.append
    line_no = 0

    def line_open() -> str:
        nonlocal line_no
        delay = FIRST_DELAY + line_no * STAGGER
        line_no += 1
        if static:
            return "<g>"
        return f'<g class="l" style="animation-delay:{delay:.2f}s">'

    w(f'<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
      f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}" role="img" '
      f'aria-labelledby="t">')
    w(f'<title id="t">{escape(ROWS[0][1])}: {escape(ROWS[1][1])}, '
      f'{escape(ROWS[2][1])}</title>')
    if not static:
        w("<style>")
        w(".l{opacity:0;animation:in .45s ease-out forwards}")
        w("@keyframes in{from{opacity:0;transform:translateX(-10px)}"
          "to{opacity:1;transform:translateX(0)}}")
        w(".cur{animation:blink 1s steps(1) infinite}")
        w("@keyframes blink{50%{opacity:0}}")
        w("@media (prefers-reduced-motion:reduce){.l{animation:none;opacity:1}"
          ".cur{animation:none}}")
        w("</style>")

    # Frame + title bar (matches assets/stack-card.svg)
    w(f'<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="14" '
      f'fill="{BG}" stroke="{PRIMARY}" stroke-opacity="0.25"/>')
    w(f'<rect x="1" y="1" width="{WIDTH - 2}" height="38" rx="14" fill="{BAR}"/>')
    w(f'<rect x="1" y="27" width="{WIDTH - 2}" height="12" fill="{BAR}"/>')
    w(f'<circle cx="26" cy="20" r="6" fill="{PRIMARY}"/>'
      '<circle cx="46" cy="20" r="6" fill="#ffbd2e"/>'
      '<circle cx="66" cy="20" r="6" fill="#27c93f"/>')
    w(f'<text x="{WIDTH // 2 + 20}" y="25" text-anchor="middle" font-size="13" '
      f'fill="{MUTED}">{USER}@{HOST}: ~$ neofetch</text>')

    # user@host + underline
    ident = f"{USER}@{HOST}"
    w(line_open())
    w(f'<text x="{PAD_X}" y="{top}" font-size="15" font-weight="bold">'
      f'<tspan fill="{PRIMARY}">{USER}</tspan><tspan fill="{TEXT}">@</tspan>'
      f'<tspan fill="{PRIMARY}">{HOST}</tspan></text>')
    w(f'<text x="{PAD_X}" y="{top + LINE_H - 2}" font-size="13" fill="{DIM}">'
      f'{"-" * (len(ident) + 2)}</text>')
    w("</g>")

    # key: value rows
    for i, (key, value) in enumerate(ROWS):
        y = rows_y + i * LINE_H
        w(line_open())
        w(f'<text x="{PAD_X}" y="{y}" font-size="12.5" font-weight="bold" '
          f'fill="{PRIMARY}">{escape(key)}<tspan fill="{DIM}" '
          f'font-weight="normal">:</tspan></text>')
        w(f'<text x="{PAD_X + LABEL_W}" y="{y}" font-size="12.5" '
          f'fill="{TEXT}">{escape(value)}</text>')
        w("</g>")

    # quote
    w(line_open())
    w(f'<text x="{PAD_X}" y="{quote_y}" font-size="12.5" font-style="italic" '
      f'fill="{ACCENT}"><tspan fill="{DIM}" font-style="normal"># </tspan>'
      f'"{escape(QUOTE)}"</text>')
    w("</g>")

    # color swatches (two rows like neofetch: base + bright)
    size = 24
    w(line_open())
    for i, color in enumerate(SWATCHES):
        w(f'<rect x="{PAD_X + i * (size + 4)}" y="{swatch_y}" width="{size}" '
          f'height="{size}" rx="4" fill="{color}" stroke="{DIM}" '
          f'stroke-opacity="0.6"/>')
    w("</g>")

    # trailing prompt with cursor
    w(line_open())
    w(f'<text x="{PAD_X}" y="{prompt_y}" font-size="13" fill="{PRIMARY}">$</text>')
    cursor_cls = "" if static else ' class="cur"'
    w(f'<rect{cursor_cls} x="{PAD_X + 16}" y="{prompt_y - 11}" width="8" '
      f'height="14" fill="{TEXT}"/>')
    w("</g>")

    w("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    dst = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    static = os.environ.get("STATIC", "").strip() not in ("", "0", "false")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(static), encoding="utf-8")
    print(f"wrote {dst} ({'static' if static else 'animated'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

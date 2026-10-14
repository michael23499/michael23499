"""Render data/contributions.json as an animated, self-contained SVG heatmap.

Output: assets/contrib-heatmap.svg (860px wide, terminal frame, red palette).
The reveal animation is pure CSS inside the SVG: it plays once on load and
stays on the final frame (no JS, no external fonts, works through <img>).

Usage:
    python scripts/render_heatmap_svg.py [input.json] [output.svg]
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "contributions.json"
DEFAULT_OUTPUT = ROOT / "assets" / "contrib-heatmap.svg"

# Theme (kept in sync with assets/stack-card.svg)
FONT = "Fira Code, Consolas, Menlo, monospace"
BG = "#0a0a0d"
BAR = "#141416"
MUTED = "#8b8b93"
DIM = "#3a3a42"
TEXT = "#e2e8f0"
RULE = "#26262c"
PRIMARY = "#ff3131"
ACCENT = "#fbbf24"
LEVELS = ["#161616", "#3d1414", "#7a1f1f", "#c92a2a", "#ff3131"]

MONTHS_ES = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
WEEKDAYS_ES = {1: "lun", 3: "mié", 5: "vie"}  # rows, Sunday = 0

# Layout
WIDTH = 860
CELL = 11
PITCH = 14
WEEKS = 53
GRID_W = WEEKS * PITCH - (PITCH - CELL)
GRID_X = (WIDTH - GRID_W) // 2 + 14
GRID_Y = 118
GRID_H = 7 * PITCH - (PITCH - CELL)
DIAGONAL_STEP = 0.022  # seconds between diagonals
CELL_DURATION = 0.45


def fmt_day(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS_ES[d.month - 1]} {d.year}"


def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def layout_days(days: list[dict]) -> list[tuple[int, int, dict]]:
    """Place each day at (week column, weekday row); keep the last 53 weeks."""
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    placed = []
    for d in days:
        offset = (date.fromisoformat(d["date"]) - start).days
        placed.append((offset // 7, offset % 7, d))
    last_col = placed[-1][0]
    shift = max(0, last_col - (WEEKS - 1))
    return [(c - shift, r, d) for c, r, d in placed if c - shift >= 0]


def month_labels(placed: list[tuple[int, int, dict]]) -> list[tuple[int, str]]:
    labels: list[tuple[int, str]] = []
    seen = set()
    for col, _row, d in placed:
        key = d["date"][:7]
        if key in seen:
            continue
        seen.add(key)
        if col == 0 and date.fromisoformat(d["date"]).day > 7:
            continue  # partial first month: label would collide with the next
        if labels and col - labels[-1][0] < 3:
            labels.pop()
        labels.append((col, MONTHS_ES[int(key[5:7]) - 1]))
    return labels


def render(data: dict) -> str:
    stats = data["stats"]
    placed = layout_days(data["days"])
    best_date = stats["best_day"]["date"] if stats["best_day"]["count"] else None
    max_diag = max(c + r for c, r, _ in placed)
    grid_done = max_diag * DIAGONAL_STEP + CELL_DURATION

    legend_y = GRID_Y + GRID_H + 26
    rule_y = legend_y + 22
    stats_y = rule_y + 36
    height = stats_y + 40

    out: list[str] = []
    w = out.append
    w(f'<svg width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
      f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}" role="img" '
      f'aria-labelledby="t">')
    w(f'<title id="t">{stats["total"]} contribuciones en el último año. '
      f'Racha actual {plural(stats["current_streak"], "día", "días")}, '
      f'racha más larga {plural(stats["longest_streak"], "día", "días")}.</title>')
    w("<style>")
    w(".c{opacity:0;transform-box:fill-box;transform-origin:center;"
      f"animation:pop {CELL_DURATION}s cubic-bezier(.2,.9,.3,1.3) forwards}}")
    w("@keyframes pop{0%{opacity:0;transform:scale(.3)}"
      "100%{opacity:1;transform:scale(1)}}")
    w(".f{opacity:0;animation:fade .6s ease-out forwards}")
    w("@keyframes fade{from{opacity:0;transform:translateY(6px)}"
      "to{opacity:1;transform:translateY(0)}}")
    w("@media (prefers-reduced-motion:reduce){.c,.f{animation:none;opacity:1}}")
    w("</style>")

    # Frame + title bar
    w(f'<rect x="1" y="1" width="{WIDTH - 2}" height="{height - 2}" rx="14" '
      f'fill="{BG}" stroke="{PRIMARY}" stroke-opacity="0.25"/>')
    w(f'<rect x="1" y="1" width="{WIDTH - 2}" height="38" rx="14" fill="{BAR}"/>')
    w(f'<rect x="1" y="27" width="{WIDTH - 2}" height="12" fill="{BAR}"/>')
    w(f'<circle cx="26" cy="20" r="6" fill="{PRIMARY}"/>'
      '<circle cx="46" cy="20" r="6" fill="#ffbd2e"/>'
      '<circle cx="66" cy="20" r="6" fill="#27c93f"/>')
    w(f'<text x="{WIDTH // 2}" y="25" text-anchor="middle" font-size="13" '
      f'fill="{MUTED}">michael@github: ~$ ./contributions.sh</text>')

    # Header line
    w(f'<text x="28" y="74" font-size="15" fill="{TEXT}">'
      f'<tspan fill="{PRIMARY}">$</tspan> git log --since="1 year ago" '
      f'<tspan fill="{DIM}">|</tspan> heatmap</text>')
    w(f'<text x="28" y="98" font-size="13" fill="{MUTED}">'
      f'<tspan fill="{PRIMARY}" font-weight="bold">{stats["total"]}</tspan> '
      f'contribuciones · {fmt_day(data["range"]["start"])} → '
      f'{fmt_day(data["range"]["end"])}</text>')

    # Month + weekday labels
    for col, label in month_labels(placed):
        w(f'<text x="{GRID_X + col * PITCH}" y="{GRID_Y - 8}" font-size="10" '
          f'fill="{MUTED}">{label}</text>')
    for row, label in WEEKDAYS_ES.items():
        w(f'<text x="{GRID_X - 8}" y="{GRID_Y + row * PITCH + 9}" font-size="10" '
          f'text-anchor="end" fill="{MUTED}">{escape(label)}</text>')

    # Cells (diagonal reveal: delay grows with column + row)
    for col, row, d in placed:
        x = GRID_X + col * PITCH
        y = GRID_Y + row * PITCH
        level = max(0, min(d["level"], len(LEVELS) - 1))
        delay = (col + row) * DIAGONAL_STEP
        extra = ""
        if d["date"] == best_date:
            extra = f' stroke="{ACCENT}" stroke-width="1.2"'
        w(f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" '
          f'width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVELS[level]}"{extra}>'
          f'<title>{d["count"]} · {d["date"]}</title></rect>')

    # Legend (right-aligned under the grid) + best-day marker hint (left)
    right = GRID_X + GRID_W
    lx = right - len(LEVELS) * PITCH
    w(f'<g class="f" style="animation-delay:{grid_done:.2f}s">')
    w(f'<text x="{lx - 8}" y="{legend_y + 9}" font-size="10" text-anchor="end" '
      f'fill="{MUTED}">menos</text>')
    for i, color in enumerate(LEVELS):
        w(f'<rect x="{lx + i * PITCH}" y="{legend_y}" width="{CELL}" '
          f'height="{CELL}" rx="2.5" fill="{color}"/>')
    w(f'<text x="{right + 8}" y="{legend_y + 9}" font-size="10" '
      f'fill="{MUTED}">más</text>')
    if best_date:
        w(f'<rect x="{GRID_X}" y="{legend_y}" width="{CELL}" height="{CELL}" '
          f'rx="2.5" fill="{LEVELS[-1]}" stroke="{ACCENT}" stroke-width="1.2"/>')
        w(f'<text x="{GRID_X + CELL + 8}" y="{legend_y + 9}" font-size="10" '
          f'fill="{MUTED}">mejor día</text>')
    w("</g>")

    # Stats footer
    w(f'<line x1="28" y1="{rule_y}" x2="{WIDTH - 28}" y2="{rule_y}" '
      f'stroke="{RULE}" stroke-width="1"/>')
    items = [
        ("total", f'{stats["total"]}', PRIMARY),
        ("racha actual", plural(stats["current_streak"], "día", "días"), TEXT),
        ("racha más larga", plural(stats["longest_streak"], "día", "días"), TEXT),
        ("mejor día", f'{fmt_day(stats["best_day"]["date"])} '
                      f'({stats["best_day"]["count"]})', ACCENT),
    ]
    col_w = (WIDTH - 56) / len(items)
    for i, (label, value, color) in enumerate(items):
        x = 28 + i * col_w
        delay = grid_done + 0.15 + i * 0.12
        w(f'<g class="f" style="animation-delay:{delay:.2f}s">')
        w(f'<text x="{x:.0f}" y="{stats_y - 8}" font-size="11" fill="{MUTED}">'
          f'<tspan fill="{PRIMARY}">›</tspan> {escape(label)}</text>')
        w(f'<text x="{x:.0f}" y="{stats_y + 14}" font-size="16" font-weight="bold" '
          f'fill="{color}">{escape(value)}</text>')
        w("</g>")

    w("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    data = json.loads(src.read_text(encoding="utf-8"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render(data), encoding="utf-8")
    print(f"wrote {dst.relative_to(ROOT) if dst.is_relative_to(ROOT) else dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

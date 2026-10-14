#!/usr/bin/env python3
"""
Render data/contributions.json (written by fetch_contributions.py) as an
animated GitHub-style contribution graph: squares pop in one by one along a
diagonal sweep (CSS keyframes, play once then hold), with month / weekday
labels, an "N contributions in the last year" line underneath and a
"Less [] [] [] [] [] More" legend on the right. The very top days (level 4 and
above the NEON_PCT percentile of active days) get an extra neon shade.

Adapted from AVIVASHISHTA29/AVIVASHISHTA29 (scripts/generate_streak_svg.py),
recolored to a red palette.

    python scripts/render_heatmap_svg.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "contrib-heatmap.svg")

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)
contribs = data["days"]
total = data["total_contributions"]

# ---- layout ----
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
COLORS = ["#161b22", "#3d1414", "#7a1f1f", "#c92a2a", "#ff3131"]  # GitHub levels 0-4
NEON = "#ff6b6b"        # 6th shade for the very top days
NEON_PCT = 98           # percentile of active-day counts that counts as "very top"
GRAY = "#7d8590"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# the calendar's first column starts on a Sunday; pad if the data does not
sd = datetime.date.fromisoformat(contribs[0]["date"])
lead = (sd.weekday() + 1) % 7          # sunday = 0
week0 = sd - datetime.timedelta(days=lead)

n = len(contribs) + lead
NW = (n + 6) // 7
W = LEFT + NW * (CELL + GAP) + 6
H = TOP + 7 * (CELL + GAP) + 22

# timing (seconds)
REVEAL, DUR = 3.6, 0.55
maxorder = (NW - 1) + 6 * 0.55

active = sorted(c["count"] for c in contribs if c["count"] > 0)
neon_min = active[min(len(active) - 1, int(len(active) * NEON_PCT / 100))] if active else 1 << 30

rects, labels = [], []
last_m = None
for wk in range(NW):
    d = week0 + datetime.timedelta(days=wk * 7)
    if d.month != last_m:
        last_m = d.month
        labels.append(f'<text class="lbl" x="{LEFT + wk * (CELL + GAP)}" y="{TOP - 8}">{MONTHS[d.month - 1]}</text>')
for name, r in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    labels.append(f'<text class="lbl" x="2" y="{TOP + r * (CELL + GAP) + CELL - 2}">{name}</text>')

for j, c in enumerate(contribs):
    i = j + lead
    wk, row, lvl = i // 7, i % 7, min(int(c.get("level", 0)), 4)
    x = LEFT + wk * (CELL + GAP)
    y = TOP + row * (CELL + GAP)
    delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    fill = NEON if lvl == 4 and c["count"] >= neon_min else COLORS[lvl]
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{fill}" style="animation-delay:{delay}s"/>'
    )

# legend, right-aligned with the grid on the total line
LEG = 11
right = LEFT + NW * (CELL + GAP) - GAP
base = H - 6
more_w = 30
x = right - more_w
legend = [f'<text class="lbl leg" x="{right}" y="{base}" text-anchor="end">More</text>']
x -= 6 + len(COLORS) * (LEG + 3) - 3
for k, col in enumerate(COLORS):
    legend.append(f'<rect x="{x + k * (LEG + 3)}" y="{base - LEG + 1}" width="{LEG}" height="{LEG}" '
                  f'rx="2" fill="{col}"/>')
legend.append(f'<text class="lbl leg" x="{x - 6}" y="{base}" text-anchor="end">Less</text>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:15px; font-weight:700; }}
  text.leg {{ font-size:12px; font-weight:400; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR + 0.15:.2f}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{''.join(labels)}
{''.join(rects)}
<text class="total" x="{LEFT}" y="{H - 6}">{total:,} contributions in the last year</text>
{''.join(legend)}
</svg>'''

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {len(contribs)} days, {total:,} contributions, {len(svg) // 1024} KB")

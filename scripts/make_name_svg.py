#!/usr/bin/env python3
"""
Render the name banner (figlet-style ASCII "MICHAEL ARISMENDI") as a
terminal-window SVG, assets/name-banner.svg -- the text alternative to the
photo portrait (scripts/prep_photo.py + make_ascii_svg.py, kept as an option).

Same 840 x 880 window as assets/ascii-portrait.svg / assets/stats.svg so the
panels line up side by side: title bar, one-shot row-by-row reveal (a clip
wipe left -> right with a block cursor riding its edge, top -> bottom), then a
footer prompt with a blinking cursor.

The figlet glyphs are baked into FIGLET below (generated once with pyfiglet),
so neither CI nor this script needs pyfiglet at runtime.

    python scripts/make_name_svg.py [output.svg]
    VARIANT=slant python scripts/make_name_svg.py      # ansi | slant | rebel | combo
    STATIC=1 python scripts/make_name_svg.py           # frozen final frame
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "name-banner.svg")
VARIANT = os.environ.get("VARIANT", "combo")
STATIC = bool(os.environ.get("STATIC"))

# ---- window (matches make_ascii_svg.py) -----------------------------------
CANVAS_W, CANVAS_H = 840, 880
PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = CANVAS_W - PAD * 2
ART_TOP = TITLEBAR_H + PAD
ART_BOT = CANVAS_H - STATUS_H - PAD * 1.4

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
LIGHT = "#e6edf3"
RED_TOP, RED_MID, RED_BOT = "#ff3131", "#c92a2a", "#7a1f1f"
AMBER = "#fbbf24"

CHAR_W = 0.6        # monospace advance, in em
LINE_H = float(os.environ.get("LINE_H", 1.0))  # figlet row pitch in em; 1.0 keeps block glyphs touching
SEAM = float(os.environ.get("SEAM", 0.7))  # thin same-colour stroke that hides hairline seams between block glyphs
MAX_FS = 46         # cap so short words do not get absurdly large
REVEAL = 4.6        # seconds for the whole banner to print

# ---- variants -------------------------------------------------------------
# blocks: ("fig", font, word, width_fraction, fill[, stroke[, stretch]])
#         fill = "red" | "grey" | colour; stroke (px, None = SEAM) thickens thin
#         fonts such as slant; stretch > 1 makes the glyphs taller (vertical scale)
#         ("txt", text, font_size, colour)
#         ("gap", px)
VARIANTS = {
    "ansi": [
        ("txt", "$ ./banner.sh --name", 15, MUTED), ("gap", 18),
        ("fig", "ansi_shadow", "MICH", 0.80, "red"),
        ("fig", "ansi_shadow", "AEL", 0.64, "red"), ("gap", 22),
        ("fig", "ansi_shadow", "ARISMENDI", 0.92, "grey"), ("gap", 26),
        ("txt", "full stack · ai & rag", 17, MUTED),
    ],
    "slant": [
        ("txt", "$ ./banner.sh --name", 15, MUTED), ("gap", 40),
        ("fig", "slant", "MICHAEL", 0.96, "red", 2.2), ("gap", 34),
        ("fig", "slant", "ARISMENDI", 0.96, "grey", 1.8), ("gap", 44),
        ("txt", "full stack developer · ai & rag", 17, LIGHT), ("gap", 4),
        ("txt", "madrid, spain · 5+ years in production", 15, MUTED),
    ],
    "rebel": [
        ("txt", "$ ./banner.sh --name", 15, MUTED), ("gap", 18),
        ("fig", "dos_rebel", "MICH", 0.92, "red"), ("gap", 6),
        ("fig", "dos_rebel", "AEL", 0.70, "red"), ("gap", 24),
        ("fig", "dos_rebel", "ARISMENDI", 0.96, "grey"), ("gap", 26),
        ("txt", "full stack · ai & rag", 17, MUTED),
    ],
    "combo": [
        ("txt", "$ whoami", 18, MUTED), ("gap", 34),
        ("fig", "ansi_shadow", "MICHAEL", 0.97, "red", None, 1.75), ("gap", 40),
        ("fig", "ansi_shadow", "ARISMENDI", 0.88, "grey", None, 1.45), ("gap", 52),
        ("txt", "full stack developer · ai & rag", 21, LIGHT), ("gap", 6),
        ("txt", "madrid, spain · 5+ years in production", 17, MUTED),
    ],
}

# --- BEGIN FIGLET DATA (generated with pyfiglet; do not edit by hand) -------
FIGLET = {
    ('ansi_shadow', 'MICHAEL'): [
        '███╗   ███╗██╗ ██████╗██╗  ██╗ █████╗ ███████╗██╗',
        '████╗ ████║██║██╔════╝██║  ██║██╔══██╗██╔════╝██║',
        '██╔████╔██║██║██║     ███████║███████║█████╗  ██║',
        '██║╚██╔╝██║██║██║     ██╔══██║██╔══██║██╔══╝  ██║',
        '██║ ╚═╝ ██║██║╚██████╗██║  ██║██║  ██║███████╗███████╗',
        '╚═╝     ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝',
    ],
    ('ansi_shadow', 'MICH'): [
        '███╗   ███╗██╗ ██████╗██╗  ██╗',
        '████╗ ████║██║██╔════╝██║  ██║',
        '██╔████╔██║██║██║     ███████║',
        '██║╚██╔╝██║██║██║     ██╔══██║',
        '██║ ╚═╝ ██║██║╚██████╗██║  ██║',
        '╚═╝     ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝',
    ],
    ('ansi_shadow', 'AEL'): [
        ' █████╗ ███████╗██╗',
        '██╔══██╗██╔════╝██║',
        '███████║█████╗  ██║',
        '██╔══██║██╔══╝  ██║',
        '██║  ██║███████╗███████╗',
        '╚═╝  ╚═╝╚══════╝╚══════╝',
    ],
    ('ansi_shadow', 'ARISMENDI'): [
        ' █████╗ ██████╗ ██╗███████╗███╗   ███╗███████╗███╗   ██╗██████╗ ██╗',
        '██╔══██╗██╔══██╗██║██╔════╝████╗ ████║██╔════╝████╗  ██║██╔══██╗██║',
        '███████║██████╔╝██║███████╗██╔████╔██║█████╗  ██╔██╗ ██║██║  ██║██║',
        '██╔══██║██╔══██╗██║╚════██║██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║  ██║██║',
        '██║  ██║██║  ██║██║███████║██║ ╚═╝ ██║███████╗██║ ╚████║██████╔╝██║',
        '╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═╝',
    ],
    ('slant', 'MICHAEL'): [
        '    __  _______________  _____    ________',
        '   /  |/  /  _/ ____/ / / /   |  / ____/ /',
        '  / /|_/ // // /   / /_/ / /| | / __/ / /',
        ' / /  / // // /___/ __  / ___ |/ /___/ /___',
        '/_/  /_/___/\\____/_/ /_/_/  |_/_____/_____/',
    ],
    ('slant', 'MICH'): [
        '    __  _______________  __',
        '   /  |/  /  _/ ____/ / / /',
        '  / /|_/ // // /   / /_/ /',
        ' / /  / // // /___/ __  /',
        '/_/  /_/___/\\____/_/ /_/',
    ],
    ('slant', 'AEL'): [
        '    ___    ________',
        '   /   |  / ____/ /',
        '  / /| | / __/ / /',
        ' / ___ |/ /___/ /___',
        '/_/  |_/_____/_____/',
    ],
    ('slant', 'ARISMENDI'): [
        '    ___    ____  _________ __  __________   ______  ____',
        '   /   |  / __ \\/  _/ ___//  |/  / ____/ | / / __ \\/  _/',
        '  / /| | / /_/ // / \\__ \\/ /|_/ / __/ /  |/ / / / // /',
        ' / ___ |/ _, _// / ___/ / /  / / /___/ /|  / /_/ // /',
        '/_/  |_/_/ |_/___//____/_/  /_/_____/_/ |_/_____/___/',
    ],
    ('small_slant', 'MICHAEL'): [
        '   __  ______________ _____   ______',
        '  /  |/  /  _/ ___/ // / _ | / __/ /',
        ' / /|_/ // // /__/ _  / __ |/ _// /__',
        '/_/  /_/___/\\___/_//_/_/ |_/___/____/',
    ],
    ('small_slant', 'MICH'): [
        '   __  ______________ __',
        '  /  |/  /  _/ ___/ // /',
        ' / /|_/ // // /__/ _  /',
        '/_/  /_/___/\\___/_//_/',
    ],
    ('small_slant', 'AEL'): [
        '   ___   ______',
        '  / _ | / __/ /',
        ' / __ |/ _// /__',
        '/_/ |_/___/____/',
    ],
    ('small_slant', 'ARISMENDI'): [
        '   ___   ___  __________  ________  _____  ____',
        '  / _ | / _ \\/  _/ __/  |/  / __/ |/ / _ \\/  _/',
        ' / __ |/ , _// /_\\ \\/ /|_/ / _//    / // // /',
        '/_/ |_/_/|_/___/___/_/  /_/___/_/|_/____/___/',
    ],
    ('dos_rebel', 'MICHAEL'): [
        ' ██████   ██████ █████   █████████  █████   █████   █████████   ██████████ █████',
        '░░██████ ██████ ░░███   ███░░░░░███░░███   ░░███   ███░░░░░███ ░░███░░░░░█░░███',
        ' ░███░█████░███  ░███  ███     ░░░  ░███    ░███  ░███    ░███  ░███  █ ░  ░███',
        ' ░███░░███ ░███  ░███ ░███          ░███████████  ░███████████  ░██████    ░███',
        ' ░███ ░░░  ░███  ░███ ░███          ░███░░░░░███  ░███░░░░░███  ░███░░█    ░███',
        ' ░███      ░███  ░███ ░░███     ███ ░███    ░███  ░███    ░███  ░███ ░   █ ░███      █',
        ' █████     █████ █████ ░░█████████  █████   █████ █████   █████ ██████████ ███████████',
        '░░░░░     ░░░░░ ░░░░░   ░░░░░░░░░  ░░░░░   ░░░░░ ░░░░░   ░░░░░ ░░░░░░░░░░ ░░░░░░░░░░░',
    ],
    ('dos_rebel', 'MICH'): [
        ' ██████   ██████ █████   █████████  █████   █████',
        '░░██████ ██████ ░░███   ███░░░░░███░░███   ░░███',
        ' ░███░█████░███  ░███  ███     ░░░  ░███    ░███',
        ' ░███░░███ ░███  ░███ ░███          ░███████████',
        ' ░███ ░░░  ░███  ░███ ░███          ░███░░░░░███',
        ' ░███      ░███  ░███ ░░███     ███ ░███    ░███',
        ' █████     █████ █████ ░░█████████  █████   █████',
        '░░░░░     ░░░░░ ░░░░░   ░░░░░░░░░  ░░░░░   ░░░░░',
    ],
    ('dos_rebel', 'AEL'): [
        '   █████████   ██████████ █████',
        '  ███░░░░░███ ░░███░░░░░█░░███',
        ' ░███    ░███  ░███  █ ░  ░███',
        ' ░███████████  ░██████    ░███',
        ' ░███░░░░░███  ░███░░█    ░███',
        ' ░███    ░███  ░███ ░   █ ░███      █',
        ' █████   █████ ██████████ ███████████',
        '░░░░░   ░░░░░ ░░░░░░░░░░ ░░░░░░░░░░░',
    ],
    ('dos_rebel', 'ARISMENDI'): [
        '   █████████   ███████████   █████  █████████  ██████   ██████ ██████████ ██████   █████ ██████████   █████',
        '  ███░░░░░███ ░░███░░░░░███ ░░███  ███░░░░░███░░██████ ██████ ░░███░░░░░█░░██████ ░░███ ░░███░░░░███ ░░███',
        ' ░███    ░███  ░███    ░███  ░███ ░███    ░░░  ░███░█████░███  ░███  █ ░  ░███░███ ░███  ░███   ░░███ ░███',
        ' ░███████████  ░██████████   ░███ ░░█████████  ░███░░███ ░███  ░██████    ░███░░███░███  ░███    ░███ ░███',
        ' ░███░░░░░███  ░███░░░░░███  ░███  ░░░░░░░░███ ░███ ░░░  ░███  ░███░░█    ░███ ░░██████  ░███    ░███ ░███',
        ' ░███    ░███  ░███    ░███  ░███  ███    ░███ ░███      ░███  ░███ ░   █ ░███  ░░█████  ░███    ███  ░███',
        ' █████   █████ █████   █████ █████░░█████████  █████     █████ ██████████ █████  ░░█████ ██████████   █████',
        '░░░░░   ░░░░░ ░░░░░   ░░░░░ ░░░░░  ░░░░░░░░░  ░░░░░     ░░░░░ ░░░░░░░░░░ ░░░░░    ░░░░░ ░░░░░░░░░░   ░░░░░',
    ],
}
# --- END FIGLET DATA -------------------------------------------------------


def layout(blocks):
    """Resolve each block into lines: (text, font_size, fill_id/colour, width?)"""
    items = []        # (kind, payload, height)
    for b in blocks:
        if b[0] == "gap":
            items.append(("gap", None, b[1]))
        elif b[0] == "txt":
            _, text, fs, col = b
            items.append(("txt", (text, fs, col), fs * 1.5))
        else:
            _, font, word, frac, fill = b[:5]
            stroke = b[5] if len(b) > 5 and b[5] is not None else SEAM
            stretch = b[6] if len(b) > 6 else 1.0
            rows = FIGLET[(font, word)]
            cols = max(len(r) for r in rows)
            rows = [r.ljust(cols) for r in rows]
            fs = min(MAX_FS, ART_W * frac / (cols * CHAR_W))
            items.append(("fig", (rows, cols, fs, fill, stroke, stretch), len(rows) * fs * LINE_H * stretch))
    return items


items = layout(VARIANTS[VARIANT])
total_h = sum(h for _, _, h in items)
y = ART_TOP + max(0.0, (ART_BOT - ART_TOP - total_h) / 2)

lines = []          # (y_top, height, x, width, markup)
grads = []
cx = CANVAS_W / 2
for n, (kind, payload, h) in enumerate(items):
    if kind == "gap":
        y += h
        continue
    if kind == "txt":
        text, fs, col = payload
        w = len(text) * CHAR_W * fs
        lines.append((y, h, cx - w / 2, w,
                      f'<text xml:space="preserve" x="{cx:.1f}" y="{y + fs * 1.05:.1f}" font-size="{fs}" '
                      f'fill="{col}" text-anchor="middle">{html.escape(text)}</text>'))
        y += h
        continue
    rows, cols, fs, fill, stroke, stretch = payload
    if fill in ("red", "grey"):
        gid = f"g{n}"
        stops = ([(0, RED_TOP), (0.55, RED_MID), (1, RED_BOT)] if fill == "red"
                 else [(0, LIGHT), (1, "#8b949e")])
        grads.append(
            f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y:.1f}" x2="0" y2="{y + h:.1f}">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops) + "</linearGradient>")
        paint = f"url(#{gid})"
    else:
        paint = fill
    w = cols * CHAR_W * fs
    for r in rows:
        rh = fs * LINE_H * stretch
        glyphs = (f'<text xml:space="preserve" x="{cx - w / 2:.1f}" y="{y + fs * 0.86:.1f}" font-size="{fs:.2f}" '
                  f'fill="{paint}" stroke="{paint}" stroke-width="{stroke:.2f}" textLength="{w:.1f}" '
                  f'lengthAdjust="spacingAndGlyphs">{html.escape(r)}</text>')
        if stretch != 1.0:   # taller glyphs: scale the row vertically about its top edge
            glyphs = f'<g transform="matrix(1 0 0 {stretch:.3f} 0 {y * (1 - stretch):.2f})">{glyphs}</g>'
        lines.append((y, rh, cx - w / 2, w, glyphs))
        y += rh

# ---- assemble -------------------------------------------------------------
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
    + "".join(grads) + '</defs>',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">michael@github: ~$ ./banner.sh</text>')

# grayscale antialiasing (see make_ascii_svg.py): no subpixel colour fringes
parts.append('<g opacity="0.999">')
row_dur = REVEAL / len(lines)
for k, (top, rh, x0, w, markup) in enumerate(lines):
    if STATIC:
        parts.append(markup)
        continue
    t0 = k * row_dur
    parts.append(
        f'<clipPath id="r{k}"><rect x="{x0 - 2:.1f}" y="{top:.1f}" height="{rh + 1:.1f}" width="0">'
        f'<animate attributeName="width" from="0" to="{w + 4:.1f}" begin="{t0:.3f}s" '
        f'dur="{row_dur:.3f}s" fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#r{k})">{markup}</g>'
        f'<rect y="{top + 1:.1f}" width="{max(6.0, rh * 0.5):.1f}" height="{rh - 2:.1f}" fill="{INK}" opacity="0">'
        f'<animate attributeName="x" from="{x0:.1f}" to="{x0 + w:.1f}" begin="{t0:.3f}s" '
        f'dur="{row_dur:.3f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{t0:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{t0 + row_dur:.3f}s"/></rect>'
    )
parts.append('</g>')

# footer prompt + blinking cursor (same as the portrait)
status_line_y = CANVAS_H - STATUS_H - PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="13">'
             f'michael@github:~$ whoami <tspan fill="{INK}">Michael Arismendi</tspan></text>')
status_chars = len("michael@github:~$ whoami Michael Arismendi ")
parts.append(f'<rect x="{PAD + status_chars * 13 * 0.6:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')
parts.append("</svg>")

svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: variant={VARIANT}, {len(lines)} lines, {len(svg) // 1024} KB")

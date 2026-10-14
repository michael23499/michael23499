#!/usr/bin/env python3
"""
Render a neofetch-style info card as a terminal-window SVG
(assets/info-card.svg), styled like assets/stats.svg and
assets/ascii-portrait.svg: GitHub-dark window chrome, monospace text, red keys.

Each line fades and slides in on a short stagger, plays once and holds.
GitHub runs CSS animations inside <img> SVGs (never JS), so this is pure CSS.

The content is static (edit LINES below); CI does not need to re-run it.

    python scripts/make_info_card.py [output.svg]
    STATIC=1 python scripts/make_info_card.py   # frozen final frame, for previews
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
ACCENT = "#ff3131"      # keys, user / host
HIGHLIGHT = "#fbbf24"   # project names in Highlights
SWATCHES = ["#484f58", "#ff3131", "#3fb950", "#fbbf24", "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]

W = 860
PAD = 24
TITLEBAR_H = 30
FONT = 14
LINE_H = 23
CHAR_W = FONT * 0.6            # monospace advance
KEY_COLS = 12                  # value column starts after this many chars
WRAP = 84                      # max value chars per line before wrapping

# timing (seconds)
STAGGER = 0.07
DUR = 0.4

# (key, value) rows. value may be a list of (text, color) runs.
# key "" = continuation line; key "-" = highlight bullet (name, description).
ROWS = [
    ("Now", "Full Stack & AI Developer @ Kynegos (Jun 2026 – present)"),
    ("", "RAG agents for automated public-tender analysis"),
    ("Prev", "Platomico — 4 LLMs in product (GPT, Claude, Gemini, Groq) with real-time streaming"),
    ("Prev", "Full&Fast — serverless AWS platform for BESS & fast chargers (CONNECT®)"),
    ("Prev", "La Mundial de Seguros · Banco Venezolano de Crédito · Alcaldía de Sucre"),
    ("Stack", "React · Next.js · TypeScript · Node.js · Go · Python · AWS Lambda · Supabase · GCP"),
    ("AI", "Claude · GPT · Gemini · Groq · LangChain · Ollama · RAG"),
    ("Highlights", None),
    ("-", ("local-rag-chat", "100% local RAG with source citations (open source)")),
    ("-", ("CONNECT®", "-35% cloud cost, real-time telemetry across sites")),
    ("-", ("Insurance platform", "policy issuance 48h → 2h, +25% conversion")),
    ("-", ("AI scraping pipelines", "50K+ records/day")),
    ("Uptime", "5+ years in production · banking, insurance, energy, public sector"),
    ("Location", "Madrid, Spain · ES (native) / EN (B1)"),
]

esc = html.escape


def text(x, y, runs, size=FONT, weight=None):
    """One <text> line made of (string, color) runs."""
    w = f' font-weight="{weight}"' if weight else ""
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in runs)
    return f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-size="{size}"{w}>{spans}</text>'


# ---- build the lines (each entry = svg markup for one animated line) -------
lines = []
vx = PAD + KEY_COLS * CHAR_W
lines.append(lambda y: text(PAD, y, [("michael", ACCENT), ("@", INK), ("github", ACCENT)], weight=700))
lines.append(lambda y: text(PAD, y, [("-" * len("michael@github"), MUTED)]))
for key, val in ROWS:
    if key == "-":
        name, desc = val
        lines.append(lambda y, n=name, d=desc: text(
            PAD + 2 * CHAR_W, y, [("▸ ", ACCENT), (n, HIGHLIGHT), (" — " + d, INK)]))
    elif key == "":
        lines.append(lambda y, v=val: text(vx, y, [(v, MUTED)]))
    elif val is None:
        lines.append(lambda y, k=key: text(PAD, y, [(k + ":", ACCENT)], weight=700))
    else:
        assert len(val) <= WRAP, f"wrap this value by hand: {val}"
        lines.append(lambda y, k=key, v=val: (
            text(PAD, y, [(k + ":", ACCENT)], weight=700) + text(vx, y, [(v, INK)])))

body_top = TITLEBAR_H + PAD + FONT
n_lines = len(lines) + 3                      # + spacer, swatches, prompt
H = round(body_top + (n_lines - 1) * LINE_H + PAD)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>'
    f'.l{{opacity:0;animation:in {DUR}s ease-out both}}'
    '@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}'
    '.cur{animation:blink 1s steps(1) infinite}'
    '@keyframes blink{50%{opacity:0}}'
    '@media (prefers-reduced-motion: reduce){.l{opacity:1!important;transform:none!important;animation:none!important}}'
    '</style>',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD - 4 + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">michael@github: ~$ neofetch</text>')


def line(i, markup):
    if STATIC:
        return f'<g>{markup}</g>'
    return f'<g class="l" style="animation-delay:{i * STAGGER:.2f}s">{markup}</g>'


y = body_top
for i, make in enumerate(lines):
    parts.append(line(i, make(y)))
    y += LINE_H

# neofetch colour swatches
y += LINE_H
sw = CHAR_W * 3
swatches = "".join(
    f'<rect x="{PAD + k * sw:.1f}" y="{y - FONT + 1:.1f}" width="{sw:.1f}" height="{FONT + 3}" fill="{c}"/>'
    for k, c in enumerate(SWATCHES))
parts.append(line(len(lines), swatches))

# prompt + blinking cursor
y += LINE_H
prompt = "michael@github:~$ "
cursor = (f'<rect class="cur" x="{PAD + len(prompt) * CHAR_W:.1f}" y="{y - FONT + 2:.1f}" '
          f'width="{CHAR_W:.1f}" height="{FONT + 2}" fill="{INK}"/>')
parts.append(line(len(lines) + 1, text(PAD, y, [(prompt, MUTED)]) + cursor))

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg) // 1024} KB")

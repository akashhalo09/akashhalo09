"""Shared look for the profile SVGs: colours, font stack and the terminal-window frame."""
import os
from xml.sax.saxutils import escape

# STATIC=1 renders the final frame with no animation (handy for Quick Look previews).
ANIMATE = os.environ.get("STATIC") != "1"

USER, HOST = "akash", "github"
NAME = "Akash Nigam"

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# The portrait and stats windows share a size, so equal widths in the README
# give equal heights.
WIDTH, HEIGHT = 840, 880
TITLE_H = 30

BORDER = "#30363d"
PANEL = "#161b22"
FG = "#c9d1d9"
BRIGHT = "#e6edf3"
MUTED = "#7d8590"
GREEN = "#26a641"
GREEN_HI = "#39d353"

# GitHub's contribution levels 0-4.
LEVELS = [PANEL, "#0e4429", "#006d32", GREEN, GREEN_HI]


def window(command, body, css="", width=WIDTH, height=HEIGHT):
    """Wrap `body` in a terminal window titled `user@host: ~$ ./command`."""
    w, h = width, height
    style = f"<style>{css}</style>" if css else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">
{style}<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{BORDER}"/>
<line x1="0" y1="{TITLE_H}" x2="{w}" y2="{TITLE_H}" stroke="{BORDER}"/>
<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/><circle cx="52" cy="15" r="5" fill="#27c93f"/>
<text x="{w / 2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">{escape(f"{USER}@{HOST}: ~$ ./{command}")}</text>
{body}
</svg>
"""


def write(path, svg):
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {path} ({len(svg.encode()) // 1024} KB)")

"""Hand-authored link chips for the README's ./links.sh row: link-*.svg.

Each chip is its own image so the README can wrap it in a link. It reads as a shell
command with a blinking caret, and a thin light crosses its bottom edge now and then.
Edit LINKS to change them; the README holds the actual URLs.
"""
from xml.sax.saxutils import escape

import svgkit as kit

LINKS = [  # file, command, caption
    ("link-halo.svg", "open joinhalo.com", "Halo Funding, my day job"),
    ("link-notchie.svg", "open notchie", "Lives in your Mac's notch"),
    ("link-email.svg", "mail akash@joinhalo.com", "Say hello"),
]

W, H = 548, 132  # drawn at 2x; three sit side by side in the README at 32% width each
PAD = 32
CMD_SIZE = 30
CHAR_W = CMD_SIZE * 0.6
SWEEP_W = 180

for i, (path, command, caption) in enumerate(LINKS):
    line = f"$ {command}"
    caret_x = PAD + len(line) * CHAR_W + 8

    blink = sweep = ""
    if kit.ANIMATE:
        # Carets and sweeps are staggered so the three chips don't pulse in unison.
        blink = (
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1.1s" '
            f'begin="{i * 0.37:.2f}s" repeatCount="indefinite"/>'
        )
        sweep = (
            f'<rect class="sweep" x="{-SWEEP_W}" y="{H - 3}" width="{SWEEP_W}" height="3" fill="url(#light)" clip-path="url(#chip)">'
            f'<animate attributeName="x" values="{-SWEEP_W};{W};{W}" keyTimes="0;0.3;1" dur="7s" '
            f'begin="{1 + i * 2.3:.1f}s" repeatCount="indefinite"/></rect>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{kit.FONT}">
<style>@media (prefers-reduced-motion:reduce){{.sweep{{display:none}}}}</style>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient>
<linearGradient id="light"><stop offset="0" stop-color="{kit.GREEN_HI}" stop-opacity="0"/><stop offset=".5" stop-color="{kit.GREEN_HI}"/><stop offset="1" stop-color="{kit.GREEN_HI}" stop-opacity="0"/></linearGradient>
<clipPath id="chip"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="14" fill="none" stroke="{kit.BORDER}" stroke-width="1.5"/>
<text x="{PAD}" y="58" font-size="{CMD_SIZE}" font-weight="600" fill="{kit.BRIGHT}" textLength="{len(line) * CHAR_W:.0f}" lengthAdjust="spacing"><tspan fill="{kit.GREEN_HI}">$</tspan>{escape(line[1:])}</text>
<rect x="{caret_x:.0f}" y="32" width="14" height="32" fill="{kit.FG}">{blink}</rect>
<text x="{PAD + 2 * CHAR_W:.0f}" y="100" font-size="20" fill="{kit.MUTED}">{escape(caption)}</text>
{sweep}
</svg>
"""
    kit.write(path, svg)

"""Turn source-prepped.png into a self-typing ASCII portrait: akash-ascii.svg.

    python scripts/make_ascii_svg.py [--src source-prepped.png] [--levels 30,160]

Rows type in one after another, top to bottom, each revealed left to right by a
growing clip with a block cursor on its edge. Plays once, then holds.
"""
import argparse
from xml.sax.saxutils import escape

from PIL import Image

import svgkit as kit

parser = argparse.ArgumentParser()
parser.add_argument("--src", default="source-prepped.png")
parser.add_argument("--out", default="akash-ascii.svg")
# black,white points: tones at or below `black` get the densest glyph, at or above
# `white` go blank. Lower the white point until skin clears and the features read as lines.
parser.add_argument("--levels", default="30,160")
args = parser.parse_args()

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); the space blanks the white background
COLS, ROWS = 180, 96
X0, Y0 = 20, 37
ART_W, ART_H = kit.WIDTH - 2 * X0, 800
CELL_W, CELL_H = ART_W / COLS, ART_H / ROWS
FONT_SIZE = 7.2
ROW_TIME = 0.06  # seconds each row takes to type
NBSP = "\u00a0"  # renderers collapse runs of plain spaces inside <text>; these they keep

# Centre-crop the photo to the art area's shape, then sample one pixel per glyph.
img = Image.open(args.src).convert("L")
target = ART_W / ART_H
if img.width / img.height > target:
    w = round(img.height * target)
    img = img.crop(((img.width - w) // 2, 0, (img.width - w) // 2 + w, img.height))
else:
    h = round(img.width / target)
    img = img.crop((0, (img.height - h) // 2, img.width, (img.height - h) // 2 + h))
img = img.resize((COLS, ROWS), Image.LANCZOS)
black, white = (int(v) for v in args.levels.split(","))
img = img.point(lambda v: round(255 * min(1, max(0, (v - black) / (white - black)))))
px = img.load()


def glyph(v):
    return RAMP[min(len(RAMP) - 1, (255 - v) * len(RAMP) // 256)]


parts = []
for y in range(ROWS):
    line = "".join(glyph(px[x, y]) for x in range(COLS))
    text = line.strip()
    if not text:
        continue
    lead = len(line) - len(line.lstrip())
    top = Y0 + y * CELL_H
    begin, end = y * ROW_TIME, (y + 1) * ROW_TIME

    clip = ""
    if kit.ANIMATE:
        # The clip rests at full width, so anything that skips SMIL shows the finished
        # portrait. The animation starts at 0s and holds the row hidden until its turn.
        parts.append(
            f'<clipPath id="r{y}"><rect x="{X0}" y="{top:.1f}" width="{ART_W}" height="{CELL_H:.2f}">'
            f'<animate attributeName="width" values="0;0;{ART_W}" keyTimes="0;{begin / end:.4f};1" '
            f'begin="0s" dur="{end:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        clip = f' clip-path="url(#r{y})"'
    parts.append(
        f'<text x="{X0 + lead * CELL_W:.1f}" y="{top + 6.2:.1f}" textLength="{len(text) * CELL_W:.1f}" '
        f'lengthAdjust="spacing"{clip}>{escape(text).replace(" ", NBSP)}</text>'
    )
    if kit.ANIMATE:
        parts.append(
            f'<rect y="{top + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" opacity="0">'
            f'<set attributeName="opacity" to=".85" begin="{begin:.2f}s" dur="{ROW_TIME}s"/>'
            f'<animate attributeName="x" from="{X0}" to="{X0 + ART_W}" begin="{begin:.2f}s" dur="{ROW_TIME}s"/>'
            f"</rect>"
        )

prompt = f"{kit.USER}@{kit.HOST}:~$ whoami "
foot_y = Y0 + ART_H
cursor_x = X0 + len(prompt + kit.NAME) * 13 * 0.6 + 8
blink = (
    '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
    if kit.ANIMATE else ""
)
body = (
    f'<g font-size="{FONT_SIZE}" fill="{kit.FG}">\n' + "\n".join(parts) + "\n</g>\n"
    f'<line x1="0" y1="{foot_y}" x2="{kit.WIDTH}" y2="{foot_y}" stroke="{kit.BORDER}"/>\n'
    f'<text x="{X0}" y="{foot_y + 19}" fill="{kit.MUTED}" font-size="13">{escape(prompt)}'
    f'<tspan fill="{kit.FG}">{escape(kit.NAME)}</tspan></text>\n'
    f'<rect x="{cursor_x:.1f}" y="{foot_y + 7}" width="8" height="14" fill="{kit.FG}">{blink}</rect>'
)
kit.write(args.out, kit.window("portrait.sh", body))

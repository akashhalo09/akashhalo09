"""Turn source-prepped.png into a self-typing ASCII portrait: akash-ascii.svg.

    python scripts/make_ascii_svg.py [--src source-prepped.png] [--levels 10,184] [--gamma 0.65]

The picture is a positive: lit skin gets dense glyphs, dark hair sparse ones. Each
glyph is picked for its shape as well as its tone, and every cell is drawn at one of
five brightness levels, so shading comes from both the character and how bright it is.

Rows type in one after another, top to bottom, each revealed left to right by a
growing clip with a block cursor on its edge. Plays once, then holds.
"""
import argparse
import os
import sys
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import svgkit as kit

parser = argparse.ArgumentParser()
parser.add_argument("--src", default="source-prepped.png")
parser.add_argument("--out", default="akash-ascii.svg")
# black,white points (0-255): tones at or below `black` fall to the floor, at or above
# `white` get the densest, brightest glyphs. Lower `white` to light the skin more.
parser.add_argument("--levels", default="10,184")
# <1 lifts mid-tones, so shadowed skin (eye sockets, under the jaw) still gets drawn
parser.add_argument("--gamma", type=float, default=0.65)
args = parser.parse_args()

COLS, ROWS = 180, 96
X0, Y0 = 20, 37
ART_W, ART_H = kit.WIDTH - 2 * X0, 800
CELL_W, CELL_H = ART_W / COLS, ART_H / ROWS
FONT_SIZE, BASELINE = 7.2, 6.2  # baseline sits this far below the top of a cell
ROW_TIME = 0.06  # seconds each row takes to type
NBSP = "\u00a0"  # renderers collapse runs of plain spaces inside <text>; these they keep

INK = "#f0f6fc"
TIERS = [0.22, 0.38, 0.58, 0.8, 1.0]  # brightness levels, drawn as fill-opacity
FLOOR = 0.06  # the subject never goes fully dark, so black hair still has an outline
# A calm set: line-like glyphs for edges, round ones for tone. The full ASCII range
# matches shapes slightly better but reads as noise (F2J@E...).
CHARS = sorted(set(" .`',-_:;~\"^=+*<>/\\|()!ilcvxzsoaen#%&@8$WM"))
SUB_W, SUB_H = 3, 6  # samples per cell used to compare a glyph's shape with the photo
SHAPE_GAIN = 1.2     # how strongly local contrast in the photo steers the glyph choice

# Bold monospace faces to measure glyph shapes with; viewers' own fonts are close enough.
FONTS = [
    ("/System/Library/Fonts/Menlo.ttc", 1),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 0),
    ("C:/Windows/Fonts/consolab.ttf", 0),
]


def glyph_shapes():
    """Each candidate glyph's ink coverage on a SUB_W x SUB_H grid, laid out as the SVG draws it."""
    path, index = next(((p, i) for p, i in FONTS if os.path.exists(p)), (None, 0))
    if not path:
        sys.exit("no bold monospace font found; add one to FONTS in make_ascii_svg.py")
    size = 48
    font = ImageFont.truetype(path, size, index=index)
    cw, ch = round(size * CELL_W / FONT_SIZE), round(size * CELL_H / FONT_SIZE)
    shapes = []
    for c in CHARS:
        cell = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(cell).text(
            ((cw - font.getlength(c)) / 2, round(ch * BASELINE / CELL_H)), c, fill=255, font=font, anchor="ls"
        )
        shapes.append(np.asarray(cell.resize((SUB_W, SUB_H), Image.BOX), dtype=np.float32).ravel() / 255)
    return np.array(shapes)


# Load the prepped photo, centre-cropped to the art area's shape.
src = Image.open(args.src)
if src.mode not in ("LA", "RGBA"):
    sys.exit(f"{args.src} has no cutout mask; re-run scripts/prep_photo.py")
target = ART_W / ART_H
if src.width / src.height > target:
    w = round(src.height * target)
    src = src.crop(((src.width - w) // 2, 0, (src.width - w) // 2 + w, src.height))
else:
    h = round(src.width / target)
    src = src.crop((0, (src.height - h) // 2, src.width, (src.height - h) // 2 + h))
gray = np.asarray(src.convert("LA"), dtype=np.float32)
tone, mask = gray[..., 0] / 255, gray[..., 1] / 255

black, white = (int(v) / 255 for v in args.levels.split(","))
tone = np.clip((tone - black) / (white - black), 0, 1) ** args.gamma
tone = np.maximum(tone, FLOOR) * mask  # the background fades to nothing

# SUB_W x SUB_H brightness samples per character cell.
samples = cv2.resize(tone, (COLS * SUB_W, ROWS * SUB_H), interpolation=cv2.INTER_AREA)
cells = samples.reshape(ROWS, SUB_H, COLS, SUB_W).transpose(0, 2, 1, 3).reshape(ROWS, COLS, -1)
brightness = cells.mean(2)

# Each cell uses the dimmest level that can still reach its brightness. Levels come from
# a blurred map so they form smooth regions rather than speckle.
smooth = cv2.GaussianBlur(brightness, (0, 0), 1.2)
tier = np.zeros((ROWS, COLS), int)
for i, level in enumerate(TIERS[:-1]):
    tier[smooth > level * 0.92] = i + 1

shapes = glyph_shapes()
coverage = shapes.mean(1)
densest = coverage.max()
shape_detail = shapes - coverage[:, None]

grid = np.full((ROWS, COLS), " ", dtype="<U1")
for y in range(ROWS):
    for x in range(COLS):
        cell = cells[y, x] / TIERS[tier[y, x]]  # what the glyph itself must supply at this level
        mean = cell.mean()
        if mean < 0.012:
            continue
        tone_error = (coverage - mean * densest) ** 2 * cell.size
        shape_error = ((shape_detail - SHAPE_GAIN * densest * (cell - mean)) ** 2).sum(1)
        grid[y, x] = CHARS[int(np.argmin(tone_error + shape_error))]

clips, cursors = [], []
layers = [[] for _ in TIERS]
for y in range(ROWS):
    if not "".join(grid[y]).strip():
        continue
    top = Y0 + y * CELL_H
    begin, end = y * ROW_TIME, (y + 1) * ROW_TIME

    clip = ""
    if kit.ANIMATE:
        # The clip rests at full width, so anything that skips SMIL shows the finished
        # portrait. The animation starts at 0s and holds the row hidden until its turn.
        clips.append(
            f'<clipPath id="r{y}"><rect x="{X0}" y="{top:.1f}" width="{ART_W}" height="{CELL_H:.2f}">'
            f'<animate attributeName="width" values="0;0;{ART_W}" keyTimes="0;{begin / end:.4f};1" '
            f'begin="0s" dur="{end:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        clip = f' clip-path="url(#r{y})"'
        cursors.append(
            f'<rect y="{top + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" opacity="0">'
            f'<set attributeName="opacity" to=".85" begin="{begin:.2f}s" dur="{ROW_TIME}s"/>'
            f'<animate attributeName="x" from="{X0}" to="{X0 + ART_W}" begin="{begin:.2f}s" dur="{ROW_TIME}s"/>'
            f"</rect>"
        )

    # One <text> per brightness level: this row's glyphs at that level, gaps elsewhere.
    for i in range(len(TIERS)):
        line = "".join(g if tier[y, x] == i else " " for x, g in enumerate(grid[y]))
        text = line.strip()
        if not text:
            continue
        lead = len(line) - len(line.lstrip())
        layers[i].append(
            f'<text x="{X0 + lead * CELL_W:.1f}" y="{top + BASELINE:.1f}" textLength="{len(text) * CELL_W:.1f}" '
            f'lengthAdjust="spacing"{clip}>{escape(text).replace(" ", NBSP)}</text>'
        )

art = []
for level, texts in zip(TIERS, layers):
    opacity = f' fill-opacity="{level}"' if level < 1 else ""
    art.append(f"<g{opacity}>\n" + "\n".join(texts) + "\n</g>")

prompt = f"{kit.USER}@{kit.HOST}:~$ whoami "
foot_y = Y0 + ART_H
cursor_x = X0 + len(prompt + kit.NAME) * 13 * 0.6 + 8
blink = (
    '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
    if kit.ANIMATE else ""
)
body = (
    "<defs>" + "".join(clips) + "</defs>\n"
    f'<g font-size="{FONT_SIZE}" font-weight="700" fill="{INK}">\n' + "\n".join(art) + "\n</g>\n"
    f'<g fill="{kit.FG}">' + "".join(cursors) + "</g>\n"
    f'<line x1="0" y1="{foot_y}" x2="{kit.WIDTH}" y2="{foot_y}" stroke="{kit.BORDER}"/>\n'
    f'<text x="{X0}" y="{foot_y + 19}" fill="{kit.MUTED}" font-size="13">{escape(prompt)}'
    f'<tspan fill="{kit.FG}">{escape(kit.NAME)}</tspan></text>\n'
    f'<rect x="{cursor_x:.1f}" y="{foot_y + 7}" width="8" height="14" fill="{kit.FG}">{blink}</rect>'
)
kit.write(args.out, kit.window("portrait.sh", body))

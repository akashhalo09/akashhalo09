"""Hand-authored about panel: about.svg. Edit the text below to change what it says.

A full-width terminal window. Its centrepiece is a career timeline drawn as a track:
on load the track fills and each role lights as a pulse reaches it, then the pulse
keeps circulating. Keep this to personal, public history; nothing about how an
employer's product or process works belongs here.
"""
from xml.sax.saxutils import escape

import svgkit as kit

HEADLINE = "Lead product engineer at Halo Funding."
INTRO = [
    "I lead engineering and own product, take designs from Figma to code myself,",
    "and ship AI features to production.",
]
ROLES = [  # years, company, role (oldest first)
    ("2023 – 24", "Legitt AI", "Full Stack Product Engineer"),
    ("2024 – 25", "Palisades Security", "Founding Engineer"),
    ("2025", "Layup Labs", "Founding Design Engineer"),
    ("2025 – now", "Halo Funding", "Lead Product Engineer"),
]
ROWS = [
    ("focus", "0-to-1 products, design to code with no handoff, AI features"),
    ("stack", "Next.js, React, TypeScript, Node.js, FastAPI, PostgreSQL, AWS"),
    ("ai", "Anthropic and OpenAI models"),
    ("side", "Notchie, a little helper that lives in your Mac's notch"),
]

W, H = 1720, 660  # drawn at 2x; the README shows it 860 wide, like the heatmap
PAD = 48
TRACK_X0, TRACK_X1, TRACK_Y = 230, 1490, 300
START, PASS = 0.6, 3.6  # the pulse leaves after START seconds and crosses in PASS seconds
TRAIL = 220  # length of the comet trail behind the pulse
UNLIT = kit.BORDER

track_len = TRACK_X1 - TRACK_X0
gap = track_len / (len(ROLES) - 1)


def anim(cls, delay=None):
    if not kit.ANIMATE:
        return ""
    style = f' style="animation-delay:{delay:.2f}s"' if delay is not None else ""
    return f' class="{cls}"{style}'


parts = [
    f'<text x="{PAD}" y="110" font-size="40" font-weight="700" fill="{kit.BRIGHT}">{escape(HEADLINE)}</text>',
]
for i, line in enumerate(INTRO):
    parts.append(f'<text x="{PAD}" y="{160 + i * 36}" font-size="26" fill="{kit.FG}">{escape(line)}</text>')

# A faint dot grid behind the track, fading out toward both ends of the window.
parts.append(f'<rect x="0" y="{TRACK_Y - 76}" width="{W}" height="200" fill="url(#dots)" mask="url(#fade)"/>')

# The track: a dim rail, with a lit rail drawn over it as the pulse makes its first pass.
parts.append(f'<line x1="{TRACK_X0}" y1="{TRACK_Y}" x2="{TRACK_X1}" y2="{TRACK_Y}" stroke="{UNLIT}" stroke-width="3"/>')
parts.append(
    f'<line{anim("p")} x1="{TRACK_X0}" y1="{TRACK_Y}" x2="{TRACK_X1}" y2="{TRACK_Y}" stroke="{kit.GREEN}" '
    f'stroke-width="3" stroke-dasharray="{track_len}"/>'
)

for i, (years, company, role) in enumerate(ROLES):
    cx = TRACK_X0 + i * gap
    reached = START + PASS * i / (len(ROLES) - 1)
    parts.append(f'<circle{anim("d", reached)} cx="{cx}" cy="{TRACK_Y}" r="30" fill="{kit.GREEN_HI}" fill-opacity=".22" filter="url(#glow)"/>')
    parts.append(
        f'<circle cx="{cx}" cy="{TRACK_Y}" r="13" fill="{kit.PANEL}" stroke="{kit.GREEN_HI}" stroke-width="3"{anim("n", reached)}/>'
        f'<circle cx="{cx}" cy="{TRACK_Y}" r="5" fill="{kit.GREEN_HI}"{anim("d", reached)}/>'
    )
    parts.append(
        f'<g text-anchor="middle">'
        f'<text x="{cx}" y="{TRACK_Y - 36}" font-size="20" fill="{kit.MUTED}">{escape(years)}</text>'
        f'<text{anim("l", reached)} x="{cx}" y="{TRACK_Y + 54}" font-size="24" font-weight="600" fill="{kit.BRIGHT}">{escape(company)}</text>'
        f'<text x="{cx}" y="{TRACK_Y + 84}" font-size="20" fill="{kit.MUTED}">{escape(role)}</text></g>'
    )

if kit.ANIMATE:
    # After the first pass the pulse keeps crossing, then rests for as long again.
    loop = f'begin="{START}s" dur="{PASS * 2}s" repeatCount="indefinite"'
    parts.append(
        f'<rect class="pulse" y="{TRACK_Y - 2}" width="{TRAIL}" height="4" fill="url(#trail)" clip-path="url(#rail)" opacity="0">'
        f'<animate attributeName="x" values="{TRACK_X0 - TRAIL};{TRACK_X1 - TRAIL};{TRACK_X1 - TRAIL}" keyTimes="0;0.5;1" {loop}/>'
        f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.48;0.5;1" {loop}/>'
        f"</rect>"
    )
    parts.append(
        f'<circle class="pulse" cy="{TRACK_Y}" r="7" fill="#aff5b4" filter="url(#glow)" opacity="0">'
        f'<animate attributeName="cx" values="{TRACK_X0};{TRACK_X1};{TRACK_X1}" keyTimes="0;0.5;1" {loop}/>'
        f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.48;0.5;1" {loop}/>'
        f"</circle>"
    )

for i, (key, value) in enumerate(ROWS):
    y = 470 + i * 46
    parts.append(
        f'<g{anim("t", 0.1 + i * 0.09)} font-size="26">'
        f'<text x="{PAD}" y="{y}" fill="{kit.GREEN}">{escape(key)}</text>'
        f'<text x="{PAD + 150}" y="{y}" fill="{kit.FG}">{escape(value)}</text></g>'
    )

css = ""
if kit.ANIMATE:
    css = (
        # Every rule uses `both` with only a `from` keyframe: elements rest in their lit,
        # visible state, so renderers that skip CSS animation still show the finished panel.
        f".n{{animation:on .5s ease-out both}}@keyframes on{{from{{stroke:{UNLIT}}}}}"
        ".d{animation:core .5s ease-out both}@keyframes core{from{opacity:0}}"
        f".l{{animation:label .5s ease-out both}}@keyframes label{{from{{fill:{kit.MUTED}}}}}"
        f".p{{animation:fill {PASS}s linear {START}s both}}@keyframes fill{{from{{stroke-dashoffset:{track_len}}}}}"
        ".t{animation:in .45s ease-out both}@keyframes in{from{opacity:0;transform:translateY(14px)}}"
        "@media (prefers-reduced-motion:reduce){.n,.d,.l,.p,.t{animation:none}.pulse{display:none}}"
    )

defs = (
    '<defs><filter id="glow" x="-200%" y="-200%" width="500%" height="500%">'
    '<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
    "</filter>"
    f'<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="13" cy="13" r="1.4" fill="{kit.MUTED}" fill-opacity=".45"/></pattern>'
    '<linearGradient id="edges"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff"/>'
    '<stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#edges)"/></mask>'
    '<linearGradient id="trail"><stop offset="0" stop-color="#aff5b4" stop-opacity="0"/><stop offset="1" stop-color="#aff5b4"/></linearGradient>'
    f'<clipPath id="rail"><rect x="{TRACK_X0}" y="{TRACK_Y - 4}" width="{track_len}" height="8"/></clipPath>'
    "</defs>\n"
)
kit.write("about.svg", kit.window("about.sh", defs + "\n".join(parts), css=css, width=W, height=H))

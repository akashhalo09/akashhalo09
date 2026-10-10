"""Render data/contributions.json as contrib-heatmap.svg.

A bare 53-week x 7-day grid (no window; it sits straight on the page) whose cells
pop in column by column, with active days flashing as they land. Runs daily in
GitHub Actions after fetch_contributions.py.
"""
import json
from datetime import date, timedelta

import svgkit as kit

X0, Y0 = 34, 24
STEP, CELL = 16, 13

data = json.load(open("data/contributions.json"))
days, stats = data["days"], data["stats"]


def sunday_index(d):
    return (d.weekday() + 1) % 7  # Sunday = 0, like GitHub's grid


first = date.fromisoformat(days[0]["date"])
first_sunday = first - timedelta(days=sunday_index(first))
cells = []
for d in days:
    day = date.fromisoformat(d["date"])
    cells.append(((day - first_sunday).days // 7, sunday_index(day), day, d))
n_weeks = max(w for w, *_ in cells) + 1
WIDTH, HEIGHT = X0 + n_weeks * STEP + 12, 158

parts = []

# Month labels over the first column of each month.
last_month, last_label_week = None, -9
for week in range(n_weeks):
    col_first = min((day for w, _, day, _ in cells if w == week), default=None)
    if col_first and col_first.month != last_month:
        last_month = col_first.month
        if week - last_label_week >= 3:
            parts.append(f'<text class="lbl" x="{X0 + week * STEP}" y="16">{col_first:%b}</text>')
            last_label_week = week

for dow, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
    parts.append(f'<text class="lbl" x="2" y="{Y0 + dow * STEP + 11}">{label}</text>')


def fill(level):
    if level:
        return f'fill="{kit.LEVELS[level]}"'
    # Empty cells are a translucent grey rather than a fixed colour: it blends to a dark
    # cell on GitHub's dark theme and a light-grey one on light, with no theme detection.
    return f'fill="{kit.MUTED}" fill-opacity=".14"'


for week, dow, day, d in cells:
    level = min(d["level"], 4)
    delay = f' style="animation-delay:{week * 0.065 + dow * 0.036:.3f}s"' if kit.ANIMATE else ""
    parts.append(
        f'<rect class="c{" g" if level else ""}" x="{X0 + week * STEP}" y="{Y0 + dow * STEP}" '
        f'width="{CELL}" height="{CELL}" rx="2.5" {fill(level)}{delay}>'
        f'<title>{d["count"]} on {day:%b} {day.day}</title></rect>'
    )

# Mid-tone text so the caption reads on GitHub's light theme as well as dark.
parts.append(
    f'<text class="total" x="{X0}" y="152"><tspan fill="{kit.GREEN}">{stats["total"]:,}</tspan>'
    f" contributions in the last year</text>"
)

css = (
    f"text.lbl{{fill:{kit.MUTED};font-size:13px;font-weight:600}}"
    f"text.total{{fill:{kit.MUTED};font-size:15px;font-weight:700}}"
)
if kit.ANIMATE:
    css += (
        # `both` applies the hidden first keyframe during each cell's delay, so the grid
        # needs no hidden resting state and shows up even where CSS animation doesn't run.
        ".c{transform-box:fill-box;transform-origin:center;animation:pop .55s ease-out both}"
        ".g{animation:pop .55s ease-out both,flash .7s ease-out both}"
        "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}"
        "@keyframes flash{0%,45%{filter:brightness(2.4)}100%{filter:brightness(1)}}"
        "@media (prefers-reduced-motion:reduce){.c{animation:none}}"
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>{css}</style>
{chr(10).join(parts)}
</svg>
"""
kit.write("contrib-heatmap.svg", svg)

"""Render data/contributions.json as stats.svg: six stat tiles and a per-month bar chart.

Tiles slide in, their numbers count up, then the bars grow. Runs daily in GitHub
Actions after fetch_contributions.py.
"""
import json
from datetime import date

import svgkit as kit

TILE_W, TILE_H = 392, 150
COL_X = [20, 428]
ROW_Y = [54, 220, 386]
CHART = (20, 552, 800, 308)  # x, y, w, h
BASELINE, BAR_MAX, BAR_W = 820, 204, 35.9

COUNT_START, FRAME, STEPS = 0.27, 0.075, 14  # count-up timing, in seconds

data = json.load(open("data/contributions.json"))
days, stats = data["days"], data["stats"]


def day(iso):
    d = date.fromisoformat(iso)
    return f"{d:%b} {d.day}"


def span(streak):
    if not streak["days"]:
        return "no active streak"
    start, end = day(streak["start"]), day(streak["end"])
    return start if start == end else f"{start} – {end}"


def plural(n, word):
    return f" {word}{'' if n == 1 else 's'}"


def count_up(x, y, final, fmt, color, suffix, delay):
    """A number that counts up to `final` and holds, as stacked <text> frames.

    Only the final frame is visible at rest, so renderers that skip SMIL show the
    real value; while the count runs it is hidden and earlier frames flash by.
    """
    attrs = f'x="{x}" y="{y}" font-size="54" font-weight="700" fill="{color}"'
    tail = f'<tspan font-size="24" font-weight="400" fill="{kit.MUTED}">{suffix}</tspan>' if suffix else ""
    if not kit.ANIMATE:
        return f"<text {attrs}>{fmt(final)}{tail}</text>"
    frames = []
    for k in range(1, STEPS + 1):
        label = fmt(final * (1 - (1 - k / STEPS) ** 3))  # ease-out
        if not frames or frames[-1] != label:
            frames.append(label)
    frames[-1] = fmt(final)
    start = delay + COUNT_START
    out = [
        f'<text {attrs} opacity="0">{label}{tail}'
        f'<set attributeName="opacity" to="1" begin="{start + i * FRAME:.3f}s" dur="{FRAME}s"/></text>'
        for i, label in enumerate(frames[:-1])
    ]
    hold = start + (len(frames) - 1) * FRAME
    out.append(f'<text {attrs}>{frames[-1]}{tail}<set attributeName="opacity" to="0" begin="0s" dur="{hold:.3f}s"/></text>')
    return "".join(out)


def whole(v):
    return f"{round(v):,}"


active, total = stats["active_days"], stats["total"]
best = stats["best_day"]
tiles = [
    # label, value, formatter, colour, suffix, caption
    ("current streak", stats["current_streak"]["days"], whole, kit.GREEN_HI,
     plural(stats["current_streak"]["days"], "day"), span(stats["current_streak"])),
    ("longest streak", stats["longest_streak"]["days"], whole, kit.BRIGHT,
     plural(stats["longest_streak"]["days"], "day"), span(stats["longest_streak"])),
    ("contributions", total, whole, kit.BRIGHT, "", "in the last year"),
    ("active days", active, whole, kit.BRIGHT, f" / {len(days)}", f"{round(100 * active / len(days))}% of the year"),
    ("best day", best["count"] if best else 0, whole, kit.BRIGHT, "", day(best["date"]) if best else "—"),
    ("avg / active day", total / active if active else 0, lambda v: f"{v:.1f}", kit.BRIGHT, "", "contributions"),
]

parts = []
for i, (label, value, fmt, color, suffix, caption) in enumerate(tiles):
    x, y = COL_X[i % 2], ROW_Y[i // 2]
    delay = i * 0.09
    anim = f' class="t" style="animation-delay:{delay:.2f}s"' if kit.ANIMATE else ""
    parts.append(
        f"<g{anim}>"
        f'<rect x="{x}" y="{y}" width="{TILE_W}" height="{TILE_H}" rx="10" fill="{kit.PANEL}" stroke="{kit.BORDER}"/>'
        f'<text x="{x + 24}" y="{y + 40}" fill="{kit.MUTED}" font-size="22">$ {label}</text>'
        + count_up(x + 24, y + 100, value, fmt, color, suffix, delay)
        + f'<text x="{x + 24}" y="{y + 132}" fill="{kit.MUTED}" font-size="20">{caption}</text>'
        "</g>"
    )

# Per-month bars, oldest to newest; the best month is highlighted and labelled.
cx, cy, cw, ch = CHART
months = list(stats["months"].items())
peak = max(v for _, v in months)
slot = (cw - 2 * 24) / len(months)
chart_delay = len(tiles) * 0.09
anim = f' class="t" style="animation-delay:{chart_delay:.2f}s"' if kit.ANIMATE else ""
chart = [
    f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="10" fill="{kit.PANEL}" stroke="{kit.BORDER}"/>'
    f'<text x="{cx + 24}" y="{cy + 40}" fill="{kit.MUTED}" font-size="22">$ contributions / month</text>'
]
labelled = False
for i, (month, value) in enumerate(months):
    mid = cx + 24 + slot * (i + 0.5)
    grow = f' class="b" style="animation-delay:{chart_delay + 0.6 + i * 0.06:.2f}s"' if kit.ANIMATE else ""
    is_peak = bool(peak) and value == peak and not labelled
    if value:
        h = max(4, BAR_MAX * value / peak)
        chart.append(
            f'<rect{grow} x="{mid - BAR_W / 2:.1f}" y="{BASELINE - h:.1f}" width="{BAR_W}" height="{h:.1f}" rx="3" '
            f'fill="{kit.GREEN_HI if is_peak else kit.GREEN}"/>'
        )
    else:
        chart.append(f'<rect x="{mid - BAR_W / 2:.1f}" y="{BASELINE - 3}" width="{BAR_W}" height="3" rx="1.5" fill="{kit.BORDER}"/>')
    if is_peak:
        labelled = True
        fade = f' class="t" style="animation-delay:{chart_delay + 1.2 + i * 0.06:.2f}s"' if kit.ANIMATE else ""
        chart.append(
            f'<text{fade} x="{mid:.1f}" y="{BASELINE - BAR_MAX - 10}" fill="{kit.BRIGHT}" font-size="18" '
            f'text-anchor="middle">{value:,}</text>'
        )
    initial = date.fromisoformat(month + "-01").strftime("%b")[0]
    chart.append(f'<text x="{mid:.1f}" y="{BASELINE + 28}" fill="{kit.MUTED}" font-size="18" text-anchor="middle">{initial}</text>')
parts.append(f"<g{anim}>" + "".join(chart) + "</g>")

css = ""
if kit.ANIMATE:
    css = (
        # `both` applies the hidden first keyframe during each delay, so nothing needs a
        # hidden resting state and renderers without CSS animation still show the card.
        ".t{animation:in .45s ease-out both}"
        "@keyframes in{from{opacity:0;transform:translateY(14px)}}"
        ".b{transform-box:fill-box;transform-origin:bottom;animation:grow .6s ease-out both}"
        "@keyframes grow{from{transform:scaleY(0)}}"
        "@media (prefers-reduced-motion:reduce){.t,.b{animation:none}}"
    )

kit.write("stats.svg", kit.window("stats.sh", "\n".join(parts), css=css))

"""Scrape the public contribution calendar into data/contributions.json. No token needed.

Reads https://github.com/users/<user>/contributions, the HTML fragment GitHub's own
profile page loads. Exact daily counts come from each cell's tooltip.
"""
import json
import os
import re
import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "akashhalo09")
URL = f"https://github.com/users/{USER}/contributions"
OUT = "data/contributions.json"

resp = requests.get(URL, timeout=30, headers={"User-Agent": f"{USER}-profile-readme"})
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.select("tool-tip[for]")}

days = []
for td in soup.select("td.ContributionCalendar-day[data-date]"):
    tip = tooltips.get(td.get("id"), "")
    m = re.match(r"(\d[\d,]*) contributions?", tip)
    days.append({
        "date": td["data-date"],
        "level": int(td.get("data-level", 0)),
        "count": int(m.group(1).replace(",", "")) if m else 0,
    })
days.sort(key=lambda d: d["date"])

# A year is ~365 cells. Far fewer means GitHub changed its markup: fail loudly and
# leave the last good data in place rather than committing an empty graph.
if len(days) < 300:
    sys.exit(f"only found {len(days)} day cells at {URL}; markup may have changed")


def streak(run):
    """Summarise a run of consecutive active days."""
    if not run:
        return {"days": 0, "start": None, "end": None}
    return {"days": len(run), "start": run[0]["date"], "end": run[-1]["date"]}


def streaks(days):
    runs, run = [], []
    for d in days:
        if d["count"]:
            run.append(d)
        elif run:
            runs.append(run)
            run = []
    # `run` is now the streak still alive at the end of the data, if any.
    longest = max(runs + [run], key=len)
    # A quiet today doesn't break yesterday's streak until the day is over.
    if not run and runs and runs[-1][-1]["date"] == days[-2]["date"]:
        run = runs[-1]
    return streak(run), streak(longest)


current, longest = streaks(days)
best = max(days, key=lambda d: d["count"])
months = Counter()
for d in days:
    months[d["date"][:7]] += d["count"]

stats = {
    "total": sum(d["count"] for d in days),
    "active_days": sum(1 for d in days if d["count"]),
    "current_streak": current,
    "longest_streak": longest,
    "best_day": {"date": best["date"], "count": best["count"]} if best["count"] else None,
    "months": dict(sorted(months.items())),
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump({"user": USER, "stats": stats, "days": days}, f, indent=1)
print(f"wrote {OUT}: {len(days)} days, {stats['total']} contributions, longest streak {longest['days']}")

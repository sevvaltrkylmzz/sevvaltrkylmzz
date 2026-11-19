"""Scrape the public contribution calendar (no token / GraphQL needed).

usage: python scripts/fetch_contributions.py [github-username]
       (falls back to $GITHUB_USER, then $GITHUB_REPOSITORY_OWNER)
writes: data/contributions.json
"""
import datetime as dt
import json
import os
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

OUT = pathlib.Path(__file__).parent.parent / "data" / "contributions.json"


def fetch(user: str) -> dict:
    r = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.select("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0))
        m = re.match(r"(\d[\d,]*) contribution", tips.get(td.get("id"), ""))
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": date, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found — GitHub markup may have changed")
    return {"user": user, "days": days, **stats(days)}


def stats(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    cur = 0
    for d in reversed(days):
        if d["count"]:
            cur += 1
        elif d is days[-1]:  # today may still be empty — don't break the streak yet
            continue
        else:
            break
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {
        "total": total,
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
        "fetched": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


if __name__ == "__main__":
    user = (sys.argv[1] if len(sys.argv) > 1 else None) or os.environ.get("GITHUB_USER") \
        or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not user:
        raise SystemExit("pass a GitHub username (arg or $GITHUB_USER)")
    OUT.parent.mkdir(exist_ok=True)
    data = fetch(user)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"{user}: {data['total']} contributions, {len(data['days'])} days")

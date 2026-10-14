"""Fetch a user's public GitHub contribution calendar and compute stats.

Scrapes https://github.com/users/<user>/contributions (public, no auth) and
writes data/contributions.json with per-day counts plus summary stats.

Usage:
    python scripts/fetch_contributions.py [username]
    GITHUB_USER=someone python scripts/fetch_contributions.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USER = "michael23499"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"
COUNT_RE = re.compile(r"^\s*([\d,]+)\s+contributions?\b", re.IGNORECASE)


def resolve_user() -> str:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    return os.environ.get("GITHUB_USER", "").strip() or DEFAULT_USER


def fetch_html(user: str) -> str:
    url = f"https://github.com/users/{user}/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "profile-art-bot (+https://github.com/" + user + ")"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_count(text: str) -> int:
    """Turn '5 contributions on ...' / 'No contributions on ...' into an int."""
    match = COUNT_RE.match(text or "")
    return int(match.group(1).replace(",", "")) if match else 0


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tooltips = {
        tip.get("for"): tip.get_text(strip=True)
        for tip in soup.find_all("tool-tip")
        if tip.get("for")
    }
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        day_date = cell["data-date"]
        level = int(cell.get("data-level", 0) or 0)
        count = parse_count(tooltips.get(cell.get("id"), ""))
        days.append({"date": day_date, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise RuntimeError("No contribution cells found; GitHub markup may have changed.")
    return days


def compute_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # Current streak: walk back from the latest day. Today with zero
    # contributions does not break the streak (the day is not over yet).
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for d in tail:
        if d["count"] == 0:
            break
        current += 1

    best = max(days, key=lambda d: (d["count"], d["date"]))
    monthly: "OrderedDict[str, int]" = OrderedDict()
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"] > 0),
        "monthly": monthly,
    }


def main() -> int:
    user = resolve_user()
    days = parse_days(fetch_html(user))
    payload = {
        "user": user,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "stats": compute_stats(days),
        "days": days,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    s = payload["stats"]
    print(
        f"{user}: {len(days)} days, total={s['total']}, "
        f"current={s['current_streak']}, longest={s['longest_streak']}, "
        f"best={s['best_day']['date']} ({s['best_day']['count']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

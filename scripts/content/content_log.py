#!/usr/bin/env python3
"""
Content Publish Logger — Kai Harness

Logs published content for 30-day performance tracking.
Appends to /opt/meetkai-data/content-calendar.md and writes to content_log.json.

Usage:
  python3 content_log.py \
    --url "https://kaicalls.com/blog/law-firm-answering" \
    --keyword "law firm answering service" \
    --platform blog \
    --site kaicalls \
    --format blog \
    [--title "Title here"] \
    [--brief-file /tmp/harness_brief.json] \
    [--four-us 14] \
    [--notes "Optional notes"]
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = "/opt/cmo-analytics/data/content_log.json"
CALENDAR_FILE = "/opt/meetkai-data/content-calendar.md"


def load_log() -> list:
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return []


def save_log(entries: list):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def append_to_calendar(entry: dict):
    try:
        os.makedirs(os.path.dirname(CALENDAR_FILE), exist_ok=True)
        date_str = entry["published_at"][:10]
        line = f"- [{entry['format'].upper()}] [{entry['site']}] {entry.get('title') or entry['keyword']} — {entry['url']} — published {date_str} [done]\n"
        with open(CALENDAR_FILE, "a") as f:
            f.write(line)
    except Exception as e:
        print(f"  Warning: could not append to calendar: {e}")


def schedule_30day_check(entry: dict):
    """Write a pending check file for the performance_check cron to pick up."""
    checks_dir = "/opt/cmo-analytics/data/pending_checks"
    os.makedirs(checks_dir, exist_ok=True)
    check_id = entry["id"]
    check_file = f"{checks_dir}/{check_id}.json"
    check_due = datetime.now(timezone.utc).replace(
        day=datetime.now(timezone.utc).day + 30
    )
    # Approximate +30 days via timestamp
    from datetime import timedelta
    due_dt = datetime.now(timezone.utc) + timedelta(days=30)
    check_data = {
        "id": check_id,
        "url": entry["url"],
        "keyword": entry["keyword"],
        "site": entry["site"],
        "published_at": entry["published_at"],
        "check_due": due_dt.isoformat(),
        "status": "pending",
    }
    with open(check_file, "w") as f:
        json.dump(check_data, f, indent=2)
    print(f"  30-day check scheduled: {check_file}")


def main():
    parser = argparse.ArgumentParser(description="Content Publish Logger")
    parser.add_argument("--url", required=True)
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--site", required=True)
    parser.add_argument("--format", required=True, dest="fmt")
    parser.add_argument("--title")
    parser.add_argument("--brief-file")
    parser.add_argument("--four-us", type=int)
    parser.add_argument("--notes")
    args = parser.parse_args()

    brief = {}
    if args.brief_file and os.path.exists(args.brief_file):
        with open(args.brief_file) as f:
            brief = json.load(f)

    now = datetime.now(timezone.utc).isoformat()
    entry_id = f"{args.site}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    entry = {
        "id": entry_id,
        "url": args.url,
        "keyword": args.keyword,
        "title": args.title or brief.get("angle") or args.keyword,
        "platform": args.platform,
        "site": args.site,
        "format": args.fmt,
        "published_at": now,
        "four_us_score": args.four_us or brief.get("four_us_score"),
        "persona": brief.get("persona"),
        "angle": brief.get("angle"),
        "notes": args.notes,
        "performance_30d": None,  # populated by performance_check.py
    }

    log = load_log()
    log.append(entry)
    save_log(log)
    append_to_calendar(entry)
    schedule_30day_check(entry)

    print(f"\n✅ Logged: {args.url}")
    print(f"   ID: {entry_id}")
    print(f"   Site: {args.site} | Keyword: {args.keyword}")
    print(f"   30-day check: scheduled")


if __name__ == "__main__":
    main()

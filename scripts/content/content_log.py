#!/usr/bin/env python3
"""
Content Publish Logger — Kai Harness

Logs published content for 30-day performance tracking.
Appends to the content calendar (KAI_CONTENT_CALENDAR_PATH, default
<data_dir>/content-calendar.md) and writes to content_log.json.

Entry lifecycle:
  - status "approved_unpublished": passed gates + approval but not yet live
    (url is None; no 30-day check scheduled — checks need a real URL).
  - status "published": live with a REAL url; 30-day check scheduled.
  - Legacy entries predate the status/content_hash fields — readers must
    treat a missing status with a url as published.

Idempotency: entries carry content_hash (sha256 of the draft body) and
log_entry dedupes on (site, content_hash) — re-runs update in place.

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
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.harness_config import get_config, get_content_calendar_path

_CFG = get_config()

LOG_FILE = str(_CFG.content_log)


def _calendar_file() -> str:
    """Resolve the content calendar path at call time (env/config override)."""
    return str(get_content_calendar_path())


def compute_content_hash(body: str) -> str:
    """sha256 of a draft body — the idempotency key for (site, content_hash)."""
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def load_log(log_file: str | None = None) -> list:
    path = log_file or LOG_FILE
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []


def save_log(entries: list, log_file: str | None = None):
    path = log_file or LOG_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def find_entry_by_hash(site: str, content_hash: str, log_file: str | None = None) -> dict | None:
    """Return the log entry matching (site, content_hash), or None.

    Legacy entries have no content_hash and never match.
    """
    if not content_hash:
        return None
    for entry in load_log(log_file):
        if not isinstance(entry, dict):
            continue
        if entry.get("site") == site and entry.get("content_hash") == content_hash:
            return entry
    return None


def log_entry(
    url: str | None,
    keyword: str,
    site: str,
    format: str,
    title: str = "",
    brief: dict | None = None,
    four_us: int = 0,
    notes: str = "",
    source_run: str | None = None,
    proposal_id: str | None = None,
    module_set: list[str] | None = None,
    artifact_refs: dict | None = None,
    content_hash: str | None = None,
    status: str | None = None,
    campaign_id: str | None = None,
    log_file: str | None = None,
) -> dict:
    """Programmatic API to log a content entry.

    url must be the REAL published URL — pass None when the piece is approved
    but not published (status becomes "approved_unpublished"; no 30-day check
    is scheduled; use mark_published() once it goes live).

    Dedupes on (site, content_hash): a matching existing entry is updated in
    place instead of appended, and never downgraded from published.

    campaign_id is the shared join key minted by campaign_planner
    (``cmp-YYYYMMDD-<slug>``); it is carried onto the entry and into the
    30-day pending-check file so performance rolls up per campaign.

    Returns the created (or updated) entry dict.
    """
    brief = brief or {}
    now = datetime.now(timezone.utc).isoformat()

    if status is None:
        status = "published" if url else "approved_unpublished"

    existing = find_entry_by_hash(site, content_hash, log_file) if content_hash else None
    if existing is not None:
        log = load_log(log_file)
        # Re-find inside the list we will save (find_entry_by_hash reloaded).
        entry = next(
            (e for e in log if isinstance(e, dict)
             and e.get("site") == site and e.get("content_hash") == content_hash),
            None,
        )
        if entry is not None:
            url_was_set = bool(entry.get("url"))
            for key, value in (
                ("keyword", keyword),
                ("title", title or brief.get("angle")),
                ("four_us_score", four_us or brief.get("four_us_score")),
                ("persona", brief.get("persona")),
                ("angle", brief.get("angle")),
                ("notes", notes),
                ("source_run", source_run),
                ("proposal_id", proposal_id),
                ("module_set", module_set),
                ("artifact_refs", artifact_refs),
                ("campaign_id", campaign_id),
            ):
                if value:
                    entry[key] = value
            if url and not url_was_set:
                # Only a real URL can move an entry forward; never overwrite
                # an existing URL with None or downgrade published status.
                # Already-published entries keep their original published_at:
                # re-stamping on a re-run (e.g. engine "already_published")
                # would re-count the piece as new and shift the 30-day window.
                entry["url"] = url
                entry["status"] = "published"
                entry["published_at"] = now
            entry["updated_at"] = now
            save_log(log, log_file)
            if url and not url_was_set:
                append_to_calendar(entry)
                schedule_30day_check(entry)
            return entry

    entry_id = f"{site}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    entry = {
        "id": entry_id,
        "url": url,
        "keyword": keyword,
        "title": title or brief.get("angle") or keyword,
        "platform": format,
        "site": site,
        "format": format,
        "published_at": now,
        "four_us_score": four_us or brief.get("four_us_score"),
        "persona": brief.get("persona"),
        "angle": brief.get("angle"),
        "notes": notes,
        "performance_30d": None,
        "source_run": source_run,
        "proposal_id": proposal_id,
        "module_set": module_set or [],
        "artifact_refs": artifact_refs or {},
        "content_hash": content_hash,
        "status": status,
        "campaign_id": campaign_id,
    }

    log = load_log(log_file)
    log.append(entry)
    save_log(log, log_file)
    if url:
        append_to_calendar(entry)
        schedule_30day_check(entry)

    return entry


def mark_published(
    entry_id: str,
    url: str,
    published_at: str | None = None,
    log_file: str | None = None,
) -> dict | None:
    """Backfill the REAL url onto an existing entry once it actually goes live.

    Flips status to "published", appends the calendar line, and schedules the
    30-day pending check (checks only make sense with a real URL). This is the
    hook for humans/skills that publish manually after an
    "approved_unpublished" run.

    Returns the updated entry, or None if entry_id is unknown or url is empty.
    """
    if not url:
        return None
    log = load_log(log_file)
    entry = next(
        (e for e in log if isinstance(e, dict) and e.get("id") == entry_id), None
    )
    if entry is None:
        return None
    entry["url"] = url
    entry["status"] = "published"
    entry["published_at"] = published_at or datetime.now(timezone.utc).isoformat()
    save_log(log, log_file)
    append_to_calendar(entry)
    schedule_30day_check(entry)
    return entry


def append_to_calendar(entry: dict):
    if not entry.get("url"):
        return  # calendar tracks live content only
    try:
        calendar_file = _calendar_file()
        parent = os.path.dirname(calendar_file)
        if parent:
            os.makedirs(parent, exist_ok=True)
        date_str = (entry.get("published_at") or "")[:10]
        line = f"- [{entry['format'].upper()}] [{entry['site']}] {entry.get('title') or entry['keyword']} — {entry['url']} — published {date_str} [done]\n"
        with open(calendar_file, "a") as f:
            f.write(line)
    except Exception as e:
        print(f"  Warning: could not append to calendar: {e}")


def schedule_30day_check(entry: dict):
    """Write a pending check file for the performance_check cron to pick up.

    Skipped when the entry has no real URL — a check without a URL can never
    be measured (and would poison the GSC learning loop).
    """
    if not entry.get("url"):
        return None
    checks_dir = str(_CFG.pending_checks_dir)
    os.makedirs(checks_dir, exist_ok=True)
    check_id = entry["id"]
    check_file = f"{checks_dir}/{check_id}.json"
    # Due +30 days after publish (falls back to now when unparseable)
    published = entry.get("published_at")
    try:
        published_dt = datetime.fromisoformat(published)
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        published_dt = datetime.now(timezone.utc)
    due_dt = published_dt + timedelta(days=30)
    check_data = {
        "id": check_id,
        "url": entry["url"],
        "keyword": entry["keyword"],
        "site": entry["site"],
        "published_at": entry["published_at"],
        "check_due": due_dt.isoformat(),
        "status": "pending",
        "source_run": entry.get("source_run"),
        "proposal_id": entry.get("proposal_id"),
        "module_set": entry.get("module_set", []),
        "artifact_refs": entry.get("artifact_refs", {}),
        "campaign_id": entry.get("campaign_id"),
    }
    with open(check_file, "w") as f:
        json.dump(check_data, f, indent=2)
    print(f"  30-day check scheduled: {check_file}")
    return check_file


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
    parser.add_argument("--source-run")
    parser.add_argument("--proposal-id")
    parser.add_argument("--campaign-id", help="Shared campaign join key (cmp-YYYYMMDD-<slug>)")
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
        "source_run": args.source_run,
        "proposal_id": args.proposal_id,
        "module_set": [],
        "artifact_refs": {},
        "content_hash": None,
        "status": "published",  # CLI path requires --url, so it is live
        "campaign_id": args.campaign_id,
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

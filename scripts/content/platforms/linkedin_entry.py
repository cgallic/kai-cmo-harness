#!/usr/bin/env python3
"""
LinkedIn metric entry.

LinkedIn's public API doesn't expose post-level impressions/reactions without a
Company Page + Marketing Developer Platform approval, so we record metrics
manually. This CLI accepts stats as args or interactively and writes to the
per-article metrics sidecar used by the content report.

Usage (args):
    python -m scripts.content.platforms.linkedin_entry \
        --id connorgallic-20260414-090000 \
        --url https://www.linkedin.com/pulse/... \
        --impressions 1850 --reactions 34 --comments 7 --reshares 2 \
        --profile-views 41 --followers-gained 6

Usage (interactive):
    python -m scripts.content.platforms.linkedin_entry --id <entry_id>

Stats recorded can be pulled multiple times per article — the sidecar appends
history under platforms.linkedin.history so you can watch the curve.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

KAI_DIR = Path.home() / ".kai-marketing"
METRICS_DIR = KAI_DIR / "metrics"
LOG_JSONL = KAI_DIR / "content-log.jsonl"


def _load_log() -> list[dict]:
    if not LOG_JSONL.exists():
        return []
    entries: list[dict] = []
    for line in LOG_JSONL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _find_entry(entry_id: str) -> dict | None:
    for e in _load_log():
        if e.get("id") == entry_id:
            return e
    return None


def _prompt_int(label: str, default: int = 0) -> int:
    raw = input(f"  {label} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return int(raw.replace(",", ""))
    except ValueError:
        print(f"    ! not an integer, using {default}")
        return default


def _prompt_str(label: str, default: str = "") -> str:
    raw = input(f"  {label}" + (f" [{default}]" if default else "") + ": ").strip()
    return raw or default


def record(entry_id: str, snapshot: dict, url: str | None = None) -> Path:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    path = METRICS_DIR / f"{entry_id}.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = {}

    platforms = existing.setdefault("platforms", {})
    linkedin = platforms.setdefault("linkedin", {"history": []})
    linkedin["history"].append(snapshot)
    linkedin["latest"] = snapshot
    if url:
        linkedin["url"] = url
    existing["last_updated"] = snapshot["recorded_at"]
    path.write_text(json.dumps(existing, indent=2))
    return path


def interactive(entry_id: str) -> dict:
    entry = _find_entry(entry_id)
    if entry:
        print(f"Logging LinkedIn stats for: {entry.get('title') or entry.get('keyword')}")
        default_url = entry.get("url", "")
    else:
        print(f"Warning: no content-log entry found for id={entry_id}. Recording anyway.")
        default_url = ""

    url = _prompt_str("LinkedIn URL", default_url)
    impressions = _prompt_int("Impressions")
    reactions = _prompt_int("Reactions")
    comments = _prompt_int("Comments")
    reshares = _prompt_int("Reshares")
    profile_views = _prompt_int("Profile views (post-triggered)")
    followers_gained = _prompt_int("Followers gained since post")
    dms = _prompt_int("DMs received (CTA-driven)")
    notes = _prompt_str("Notes (optional)")

    snapshot = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "impressions": impressions,
        "reactions": reactions,
        "comments": comments,
        "reshares": reshares,
        "profile_views": profile_views,
        "followers_gained": followers_gained,
        "dms": dms,
        "notes": notes,
    }
    path = record(entry_id, snapshot, url=url)
    print(f"\nSaved → {path}")
    print(f"  impressions={impressions}  reactions={reactions}  comments={comments}  reshares={reshares}  dms={dms}")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Record LinkedIn post metrics")
    parser.add_argument("--id", required=True, help="content-log entry id")
    parser.add_argument("--url", help="LinkedIn post URL")
    parser.add_argument("--impressions", type=int)
    parser.add_argument("--reactions", type=int)
    parser.add_argument("--comments", type=int)
    parser.add_argument("--reshares", type=int)
    parser.add_argument("--profile-views", type=int, dest="profile_views")
    parser.add_argument("--followers-gained", type=int, dest="followers_gained")
    parser.add_argument("--dms", type=int)
    parser.add_argument("--notes", default="")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or args.impressions is None:
        interactive(args.id)
        return

    snapshot = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "impressions": args.impressions,
        "reactions": args.reactions or 0,
        "comments": args.comments or 0,
        "reshares": args.reshares or 0,
        "profile_views": args.profile_views or 0,
        "followers_gained": args.followers_gained or 0,
        "dms": args.dms or 0,
        "notes": args.notes,
    }
    path = record(args.id, snapshot, url=args.url)
    print(f"Saved → {path}")


if __name__ == "__main__":
    main()

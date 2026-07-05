#!/usr/bin/env python3
"""
Kai CMO Harness — Editorial Calendar Store
==========================================
First-class structured editorial calendar: "publish X on date D" as data the
scheduler can execute, instead of prose markdown nothing consumes.

Storage: one JSON object per line in ``<calendar_dir>/editorial.jsonl``.
The directory comes from ``scripts.harness_config.get_calendar_dir()``
(default ``data/calendar``, override with ``KAI_CALENDAR_DIR``).

Item schema:
  {
    "id": "cal-1a2b3c4d",
    "campaign_id": null,          # optional link to a tracked campaign
    "site": "kaicalls",           # brand/client key
    "title": "...",               # working title / topic
    "format": "blog",             # blog | linkedin-article | email | ...
    "keyword": "...",             # target keyword ("" if none)
    "persona": null,              # one of the 8 marketing personas, or null
    "publish_at": "2026-07-10T14:00:00+00:00",  # ISO 8601, stored UTC
    "status": "planned",          # planned|generating|ready|published|skipped
    "notes": "",
    "created_at": "...",
    "updated_at": "..."
  }

Status doctrine: this module only tracks state. The scheduler's
``editorial_calendar_tick`` task moves planned -> generating -> ready by
producing DRAFTS that flow through the normal quality-gate + human-approval
pipeline. Nothing in this repo sets ``published`` without an approved,
human-in-the-loop publish.

Usage:
  python scripts/campaigns/calendar.py --add --site kaicalls --title "..." \
      --publish-at 2026-07-10T14:00Z --format blog --keyword "ai receptionist"
  python scripts/campaigns/calendar.py --list [--status planned] [--site kaicalls]
  python scripts/campaigns/calendar.py --due
  python scripts/campaigns/calendar.py --mark cal-1a2b3c4d --status skipped
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.harness_config import get_calendar_dir

VALID_STATUSES = ("planned", "generating", "ready", "published", "skipped")

CALENDAR_FILENAME = "editorial.jsonl"


def calendar_path() -> Path:
    """Full path to the editorial calendar JSONL file."""
    return get_calendar_dir() / CALENDAR_FILENAME


# ── Time helpers (timezone-safe: naive timestamps are treated as UTC) ────────


def _parse_utc(value: Any) -> datetime:
    """Parse an ISO 8601 timestamp into an aware UTC datetime.

    Accepts a trailing 'Z', an explicit offset, or a naive timestamp
    (interpreted as UTC). Raises ValueError on anything unparseable.
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError(f"publish_at must be an ISO 8601 timestamp, got: {value!r}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── Store primitives ─────────────────────────────────────────────────────────


def _load_items() -> List[Dict[str, Any]]:
    path = calendar_path()
    if not path.exists():
        return []
    items: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue  # skip corrupt lines rather than losing the whole store
        if isinstance(item, dict):
            items.append(item)
    return items


def _write_items(items: List[Dict[str, Any]]):
    """Atomically rewrite the whole store (tmp file + os.replace)."""
    path = calendar_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ── Public API ────────────────────────────────────────────────────────────────


def add_item(
    site: str,
    title: str,
    publish_at: Any,
    format: str = "blog",
    keyword: str = "",
    persona: Optional[str] = None,
    campaign_id: Optional[str] = None,
    notes: str = "",
    status: str = "planned",
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Add an item to the editorial calendar and return it.

    ``publish_at`` accepts an ISO 8601 string or datetime; it is normalized
    to UTC before storage. Raises ValueError on a bad timestamp or status.
    """
    if not site:
        raise ValueError("site is required")
    if not title:
        raise ValueError("title is required")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}; must be one of {VALID_STATUSES}")

    now_iso = _now_utc().isoformat()
    item = {
        "id": item_id or f"cal-{uuid.uuid4().hex[:8]}",
        "campaign_id": campaign_id,
        "site": site,
        "title": title,
        "format": format or "blog",
        "keyword": keyword or "",
        "persona": persona,
        "publish_at": _parse_utc(publish_at).isoformat(),
        "status": status,
        "notes": notes or "",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    path = calendar_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def list_items(
    status: Optional[str] = None,
    site: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List calendar items, optionally filtered by status and/or site.

    Sorted by publish_at ascending.
    """
    items = _load_items()
    if status is not None:
        items = [i for i in items if i.get("status") == status]
    if site is not None:
        items = [i for i in items if i.get("site") == site]

    def _sort_key(item: Dict[str, Any]) -> datetime:
        try:
            return _parse_utc(item.get("publish_at"))
        except ValueError:
            return datetime.max.replace(tzinfo=timezone.utc)

    return sorted(items, key=_sort_key)


def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Return the item with the given id, or None."""
    for item in _load_items():
        if item.get("id") == item_id:
            return item
    return None


def due_items(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Return planned items whose publish_at is at or before ``now``.

    ``now`` defaults to the current UTC time; a naive ``now`` is treated
    as UTC. Sorted oldest-due first so backlogs drain in order.
    """
    if now is None:
        now = _now_utc()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    due: List[Dict[str, Any]] = []
    for item in list_items(status="planned"):
        try:
            when = _parse_utc(item.get("publish_at"))
        except ValueError:
            continue  # unparseable schedule — leave it alone, never guess
        if when <= now:
            due.append(item)
    return due


def mark_status(
    item_id: str,
    status: str,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update an item's status (and optionally notes). Returns the updated item.

    Returns None when the id is unknown. Raises ValueError on a bad status.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}; must be one of {VALID_STATUSES}")

    items = _load_items()
    updated: Optional[Dict[str, Any]] = None
    for item in items:
        if item.get("id") == item_id:
            item["status"] = status
            if notes is not None:
                item["notes"] = notes
            item["updated_at"] = _now_utc().isoformat()
            updated = item
            break

    if updated is None:
        return None

    _write_items(items)
    return updated


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Editorial calendar store")
    parser.add_argument("--add", action="store_true", help="Add a calendar item")
    parser.add_argument("--list", action="store_true", help="List calendar items")
    parser.add_argument("--due", action="store_true", help="List due planned items")
    parser.add_argument("--mark", metavar="ITEM_ID", help="Update an item's status")
    parser.add_argument("--site", help="Site/brand key")
    parser.add_argument("--title", help="Working title / topic")
    parser.add_argument("--publish-at", help="ISO 8601 publish time (UTC assumed if naive)")
    parser.add_argument("--format", default="blog", help="Content format (default: blog)")
    parser.add_argument("--keyword", default="", help="Target keyword")
    parser.add_argument("--persona", help="Marketing persona")
    parser.add_argument("--campaign-id", help="Linked campaign id")
    parser.add_argument("--status", help="Status filter (--list) or new status (--mark)")
    parser.add_argument("--notes", help="Notes to attach")
    args = parser.parse_args()

    if args.add:
        if not (args.site and args.title and args.publish_at):
            parser.error("--add requires --site, --title, and --publish-at")
        item = add_item(
            site=args.site,
            title=args.title,
            publish_at=args.publish_at,
            format=args.format,
            keyword=args.keyword,
            persona=args.persona,
            campaign_id=args.campaign_id,
            notes=args.notes or "",
        )
        print(json.dumps(item, indent=2))
        return

    if args.mark:
        if not args.status:
            parser.error("--mark requires --status")
        item = mark_status(args.mark, args.status, notes=args.notes)
        if item is None:
            print(f"Item not found: {args.mark}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(item, indent=2))
        return

    if args.due:
        for item in due_items():
            print(f"{item['id']}  {item['publish_at']}  [{item['site']}] {item['title']}")
        return

    # Default: list
    for item in list_items(status=args.status, site=args.site):
        print(
            f"{item['id']}  {item['publish_at']}  {item['status']:<10}  "
            f"[{item['site']}] {item['title']}"
        )


if __name__ == "__main__":
    main()

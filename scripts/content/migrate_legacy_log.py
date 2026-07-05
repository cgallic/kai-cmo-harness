#!/usr/bin/env python3
"""
Legacy Content Log Migration — Kai Harness

Merges the legacy skill-chain log (``~/.kai-marketing/content-log.jsonl``,
written by the /content-write → /content-gate chain and read by tracker_cli)
into the CANONICAL content log (``data/content_log.json``) that the learning
loop actually consumes (performance_check, pattern_extract, weekly_report).

Why: two logs with different schemas meant winners recorded by the skill
chain never reached the learning loop. ``data/content_log.json`` is canonical;
this script folds the legacy JSONL in and is safe to re-run (idempotent).

Mapping / rules:
  - ``publish_date`` -> ``published_at`` (existing ``published_at`` wins)
  - dedupe by ``id`` first, then by non-empty ``url``
  - performance data (``performance_30d``) is preserved; when the canonical
    entry has none and the legacy entry does, it is backfilled. Legacy
    STRING-form grades are normalized to the canonical dict schema
    (``{"grade": ..., "migrated": True}``, "loser" -> "underperformer") so
    canonical-log readers never crash on a str
  - legacy-only fields (``hook_type``, ``draft_path``) are carried over
  - entries without a url become status "approved_unpublished" (no URL ⇒
    nothing measurable; see content_log.py lifecycle doctrine); entries with
    a url become "published"
  - NO pending checks are written here — run
    ``python -m scripts.self_improvement.performance_check --reconcile-only``
    afterwards; it rebuilds missing check files from the canonical log
    (EC-12) and correctly skips url-less entries.
  - the legacy file is never modified or deleted; the orphaned
    ``~/.kai-marketing/pending/*.json`` files (nothing reads them) can be
    removed by hand once you're satisfied with the merge.

Usage:
  python -m scripts.content.migrate_legacy_log [--legacy PATH] [--log-file PATH]
                                               [--dry-run] [--json]
"""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.content.content_log import load_log, save_log
from scripts.harness_config import get_config
from scripts.self_improvement.grades import get_grade

DEFAULT_LEGACY_PATH = Path.home() / ".kai-marketing" / "content-log.jsonl"

# Legacy fields backfilled onto an existing canonical entry when missing there.
_BACKFILL_FIELDS = (
    "keyword",
    "title",
    "four_us_score",
    "persona",
    "hook_type",
    "draft_path",
    "notes",
)


def load_legacy(path: str | Path) -> list[dict]:
    """Load the legacy JSONL log, skipping blank/corrupt lines."""
    path = Path(path)
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(raw, dict):
            entries.append(raw)
    return entries


def _normalize_perf(perf):
    """Coerce ``performance_30d`` into the canonical DICT schema (or None).

    Legacy JSONL entries sometimes stored a bare string grade; canonical-log
    readers (pattern_extract.is_winner, weekly_report, ceo_deck) expect the
    dict schema and must never see a str here. Routes through
    ``grades.get_grade`` so the legacy "loser" grade lands as
    "underperformer".
    """
    if isinstance(perf, dict):
        return perf
    if isinstance(perf, str):
        grade = get_grade({"performance_30d": perf})
        if grade is None:
            return None
        return {"grade": grade, "migrated": True}
    return None


def normalize_legacy_entry(raw: dict) -> dict | None:
    """Map a legacy JSONL entry onto the canonical content_log schema.

    Returns None when the entry is unusable (no id and no url to key on).
    """
    entry_id = raw.get("id")
    url = raw.get("url") or None
    if not entry_id and not url:
        return None

    published_at = raw.get("published_at") or raw.get("publish_date")
    status = raw.get("status")
    if status not in ("published", "approved_unpublished"):
        status = "published" if url else "approved_unpublished"

    fmt = raw.get("format") or raw.get("platform") or "blog"
    if not entry_id:
        # Deterministic fallback id so re-runs match the same entry.
        entry_id = f"legacy-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}"
    entry = {
        "id": entry_id,
        "url": url,
        "keyword": raw.get("keyword", ""),
        "title": raw.get("title") or raw.get("keyword", ""),
        "platform": raw.get("platform") or fmt,
        "site": raw.get("site", ""),
        "format": fmt,
        "published_at": published_at,
        "four_us_score": raw.get("four_us_score"),
        "persona": raw.get("persona"),
        "angle": raw.get("angle"),
        "notes": raw.get("notes", ""),
        "performance_30d": _normalize_perf(raw.get("performance_30d")),
        "source_run": raw.get("source_run"),
        "proposal_id": raw.get("proposal_id"),
        "module_set": raw.get("module_set") or [],
        "artifact_refs": raw.get("artifact_refs") or {},
        "content_hash": raw.get("content_hash"),
        "status": status,
        "campaign_id": raw.get("campaign_id"),
        "migrated_from": "kai-marketing-jsonl",
    }
    # Legacy-only fields worth keeping (drop empty values to stay tidy).
    for key in ("hook_type", "draft_path"):
        if raw.get(key):
            entry[key] = raw[key]
    return entry


def _backfill(canonical: dict, legacy: dict) -> bool:
    """Copy legacy data into an existing canonical entry without downgrades.

    Never touches url/status/published_at when canonical already has them
    (canonical is the source of truth for the publish lifecycle). Returns
    True when anything changed.
    """
    changed = False
    canon_perf = canonical.get("performance_30d")
    if isinstance(canon_perf, str):
        # Heal string-form grades left in the canonical log by earlier merges
        # — dict schema only, so downstream readers never crash on a str.
        canonical["performance_30d"] = _normalize_perf(canon_perf)
        canon_perf = canonical["performance_30d"]
        changed = True
    legacy_perf = _normalize_perf(legacy.get("performance_30d"))
    if canon_perf is None and legacy_perf is not None:
        canonical["performance_30d"] = legacy_perf
        changed = True
    for key in _BACKFILL_FIELDS:
        if not canonical.get(key) and legacy.get(key):
            canonical[key] = legacy[key]
            changed = True
    if not canonical.get("published_at") and legacy.get("published_at"):
        canonical["published_at"] = legacy["published_at"]
        changed = True
    if changed:
        canonical["migrated_backfill"] = "kai-marketing-jsonl"
    return changed


def migrate(
    legacy_path: str | Path | None = None,
    log_file: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Merge the legacy JSONL into the canonical log. Idempotent.

    Returns a summary dict: {added, updated, unchanged, skipped_invalid,
    legacy_total, canonical_total, log_file, legacy_path}.
    """
    legacy_path = Path(legacy_path or os.environ.get("KAI_LEGACY_CONTENT_LOG", DEFAULT_LEGACY_PATH))
    log_file = log_file or str(get_config().content_log)

    legacy_entries = load_legacy(legacy_path)
    canonical = load_log(log_file)

    by_id = {e.get("id"): e for e in canonical if isinstance(e, dict) and e.get("id")}
    by_url = {e.get("url"): e for e in canonical if isinstance(e, dict) and e.get("url")}

    added = updated = unchanged = skipped_invalid = 0

    for raw in legacy_entries:
        entry = normalize_legacy_entry(raw)
        if entry is None:
            skipped_invalid += 1
            continue

        existing = by_id.get(entry["id"])
        if existing is None and entry.get("url"):
            existing = by_url.get(entry["url"])

        if existing is not None:
            if _backfill(existing, entry):
                updated += 1
            else:
                unchanged += 1
            continue

        entry["migrated_at"] = datetime.now(timezone.utc).isoformat()
        canonical.append(entry)
        by_id[entry["id"]] = entry
        if entry.get("url"):
            by_url[entry["url"]] = entry
        added += 1

    if not dry_run and (added or updated):
        save_log(canonical, log_file)

    return {
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "skipped_invalid": skipped_invalid,
        "legacy_total": len(legacy_entries),
        "canonical_total": len(canonical),
        "log_file": str(log_file),
        "legacy_path": str(legacy_path),
        "dry_run": dry_run,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge the legacy ~/.kai-marketing/content-log.jsonl into the canonical data/content_log.json"
    )
    parser.add_argument("--legacy", help=f"Legacy JSONL path (default: {DEFAULT_LEGACY_PATH})")
    parser.add_argument("--log-file", help="Canonical log path (default: <data_dir>/content_log.json)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    parser.add_argument("--json", action="store_true", help="Print the summary as JSON")
    args = parser.parse_args()

    summary = migrate(legacy_path=args.legacy, log_file=args.log_file, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    prefix = "[dry-run] " if summary["dry_run"] else ""
    print(f"{prefix}Legacy log:    {summary['legacy_path']} ({summary['legacy_total']} entries)")
    print(f"{prefix}Canonical log: {summary['log_file']} ({summary['canonical_total']} entries after merge)")
    print(f"{prefix}  added:           {summary['added']}")
    print(f"{prefix}  updated:         {summary['updated']}")
    print(f"{prefix}  unchanged:       {summary['unchanged']}")
    print(f"{prefix}  skipped_invalid: {summary['skipped_invalid']}")
    if summary["added"] or summary["updated"]:
        print(
            "\nNext: python -m scripts.self_improvement.performance_check --reconcile-only\n"
            "      (rebuilds missing 30-day pending checks from the canonical log; EC-12)"
        )


if __name__ == "__main__":
    main()

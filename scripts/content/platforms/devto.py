#!/usr/bin/env python3
"""
Dev.to metric fetcher.

Pulls page_views_count, public_reactions_count, and comments_count for every
article owned by the authenticated user. Matches each Dev.to article to a
content-log entry by URL and writes a metrics sidecar.

Environment:
    DEVTO_API_KEY   — required. Get one at https://dev.to/settings/extensions

Usage:
    python -m scripts.content.platforms.devto [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KAI_DIR = Path.home() / ".kai-marketing"
METRICS_DIR = KAI_DIR / "metrics"
LOG_JSONL = KAI_DIR / "content-log.jsonl"

DEVTO_API = "https://dev.to/api/articles/me/published"


def _api_key() -> str:
    key = os.environ.get("DEVTO_API_KEY", "").strip()
    if not key:
        sys.exit("DEVTO_API_KEY not set. Get one at https://dev.to/settings/extensions")
    return key


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


def fetch_devto_articles(api_key: str, page_size: int = 1000) -> list[dict]:
    """Fetch all published articles for the authenticated Dev.to user."""
    results: list[dict] = []
    page = 1
    while True:
        url = f"{DEVTO_API}?per_page={page_size}&page={page}"
        req = urllib.request.Request(
            url,
            headers={
                "api-key": api_key,
                "accept": "application/vnd.forem.api-v1+json",
                "user-agent": "kai-harness/1.0 (+https://github.com/cgallic)",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            sys.exit(f"Dev.to API error {e.code}: {e.read().decode('utf-8', errors='replace')}")
        except urllib.error.URLError as e:
            sys.exit(f"Dev.to API unreachable: {e.reason}")
        if not batch:
            break
        results.extend(batch)
        if len(batch) < page_size:
            break
        page += 1
    return results


def _match_log_entry(article: dict, entries: list[dict]) -> dict | None:
    """Find a content-log entry whose URL matches the Dev.to article URL."""
    canonical = (article.get("canonical_url") or "").rstrip("/")
    url = (article.get("url") or "").rstrip("/")
    for e in entries:
        e_url = (e.get("url") or "").rstrip("/")
        if not e_url:
            continue
        if e_url in (canonical, url):
            return e
    return None


def write_metrics_sidecar(entry_id: str, data: dict) -> Path:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    path = METRICS_DIR / f"{entry_id}.json"
    existing: dict = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = {}
    existing.setdefault("platforms", {})
    existing["platforms"]["devto"] = data
    existing["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(existing, indent=2))
    return path


def summarize(article: dict) -> dict:
    return {
        "devto_id": article.get("id"),
        "url": article.get("url"),
        "title": article.get("title"),
        "page_views_count": article.get("page_views_count", 0),
        "public_reactions_count": article.get("public_reactions_count", 0),
        "comments_count": article.get("comments_count", 0),
        "positive_reactions_count": article.get("positive_reactions_count", 0),
        "reading_time_minutes": article.get("reading_time_minutes", 0),
        "published_at": article.get("published_at"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull Dev.to article stats")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without writing sidecars")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    articles = fetch_devto_articles(_api_key())
    entries = _load_log()

    matched: list[dict] = []
    unmatched: list[dict] = []

    for article in articles:
        summary = summarize(article)
        entry = _match_log_entry(article, entries)
        if entry:
            summary["content_log_id"] = entry.get("id")
            matched.append(summary)
            if not args.dry_run:
                write_metrics_sidecar(entry["id"], summary)
        else:
            unmatched.append(summary)

    report = {
        "fetched": len(articles),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "matched_articles": matched,
        "unmatched_articles": unmatched,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2, default=str))
        return

    print(f"Dev.to: {len(articles)} articles fetched, {len(matched)} matched, {len(unmatched)} unmatched")
    for m in matched:
        print(
            f"  [match] {m['content_log_id']}  views={m['page_views_count']}  "
            f"reactions={m['public_reactions_count']}  comments={m['comments_count']}  "
            f"{m['url']}"
        )
    if unmatched:
        print()
        print("Unmatched articles (no entry in ~/.kai-marketing/content-log.jsonl):")
        for u in unmatched:
            print(f"  [--] {u['url']}  (views={u['page_views_count']})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Monitor official social platform policy, API, and recommendation sources.

The script stores lightweight content hashes, not page bodies, so monthly runs can
detect source changes without committing copyrighted policy text into the repo.

Usage:
  python -m scripts.social.platform_change_monitor
  python -m scripts.social.platform_change_monitor --platform x --platform tiktok
  python -m scripts.social.platform_change_monitor --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "harness" / "references" / "social-platform-source-registry.json"
SNAPSHOT = ROOT / "harness" / "references" / "social-platform-source-snapshot.json"
REPORT = ROOT / "harness" / "references" / "social-platform-monitor-report.md"
USER_AGENT = "KaiCMOHarnessPolicyMonitor/1.0 (+https://github.com/cgallic/kai-cmo-harness)"


def _load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_text(raw: bytes, content_type: str) -> str:
    text = raw.decode("utf-8", errors="replace")
    if "html" in content_type.lower() or "<html" in text[:500].lower():
        text = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", text)
        text = re.sub(r"(?is)<!--.*?-->", " ", text)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_source(source: dict[str, Any], timeout: int) -> dict[str, Any]:
    req = Request(
        source["url"],
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.5",
        },
    )
    started = time.monotonic()
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read()
            content_type = response.headers.get("content-type", "")
            cleaned = _clean_text(body, content_type)
            digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            return {
                "ok": True,
                "status_code": getattr(response, "status", None),
                "content_hash": digest,
                "content_length": len(cleaned),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                "etag": response.headers.get("etag"),
                "last_modified": response.headers.get("last-modified"),
                "content_type": content_type,
            }
    except HTTPError as exc:
        return _error_result(exc, getattr(exc, "code", None), started)
    except URLError as exc:
        return _error_result(exc, None, started)
    except TimeoutError as exc:
        return _error_result(exc, None, started)


def _error_result(exc: BaseException, status_code: int | None, started: float) -> dict[str, Any]:
    return {
        "ok": False,
        "status_code": status_code,
        "error": str(exc),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
    }


def _status(previous: dict[str, Any] | None, current: dict[str, Any]) -> str:
    if not current.get("ok"):
        return "error"
    if not previous or not previous.get("content_hash"):
        return "new"
    if previous.get("content_hash") != current.get("content_hash"):
        return "changed"
    return "unchanged"


def check_sources(platforms: set[str] | None, limit: int | None, timeout: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    registry = _load_json(REGISTRY, {"sources": []})
    snapshot = _load_json(SNAPSHOT, {"version": 1, "sources": {}})
    previous_sources = snapshot.get("sources", {})
    selected = registry.get("sources", [])
    if platforms:
        selected = [s for s in selected if s.get("platform") in platforms]
    if limit:
        selected = selected[:limit]

    results: list[dict[str, Any]] = []
    new_sources = dict(previous_sources)

    for source in selected:
        current = _fetch_source(source, timeout=timeout)
        previous = previous_sources.get(source["id"])
        state = _status(previous, current)
        result = {**source, **current, "monitor_status": state}
        if previous:
            result["previous_hash"] = previous.get("content_hash")
            result["previous_checked_at"] = previous.get("checked_at")
        if current.get("ok"):
            new_sources[source["id"]] = {
                "platform": source.get("platform"),
                "category": source.get("category"),
                "title": source.get("title"),
                "url": source.get("url"),
                "owner_file": source.get("owner_file"),
                "content_hash": current.get("content_hash"),
                "content_length": current.get("content_length"),
                "etag": current.get("etag"),
                "last_modified": current.get("last_modified"),
                "status_code": current.get("status_code"),
                "checked_at": current.get("fetched_at"),
            }
        results.append(result)

    updated_snapshot = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": new_sources,
    }
    return results, updated_snapshot


def write_report(results: list[dict[str, Any]], path: Path = REPORT) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    changed = [r for r in results if r["monitor_status"] == "changed"]
    new = [r for r in results if r["monitor_status"] == "new"]
    errors = [r for r in results if r["monitor_status"] == "error"]
    unchanged = [r for r in results if r["monitor_status"] == "unchanged"]

    lines = [
        "# Social Platform Monitor Report",
        "",
        f"Last run: {now}",
        "",
        f"Checked: {len(results)} sources",
        f"Changed: {len(changed)}",
        f"New: {len(new)}",
        f"Errors: {len(errors)}",
        f"Unchanged: {len(unchanged)}",
        "",
    ]

    for label, items in (("Changed", changed), ("New", new), ("Errors", errors)):
        if not items:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for item in items:
            owner = item.get("owner_file", "")
            lines.append(f"- [{item['platform']}] {item['title']}: {item['url']}")
            lines.append(f"  - Category: {item.get('category')}")
            if owner:
                lines.append(f"  - Review file: `{owner}`")
            if item.get("error"):
                lines.append(f"  - Error: {item['error']}")
            if item.get("previous_hash") and item.get("content_hash"):
                lines.append(f"  - Hash: `{item['previous_hash'][:12]}` -> `{item['content_hash'][:12]}`")
        lines.append("")

    lines.append("## Reviewed Sources")
    lines.append("")
    for item in sorted(results, key=lambda r: (r.get("platform", ""), r.get("category", ""), r.get("id", ""))):
        status = item["monitor_status"]
        lines.append(f"- `{status}` [{item['platform']}] {item['title']} - {item['url']}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor social platform source changes")
    parser.add_argument("--platform", action="append", help="Filter to one platform; repeatable")
    parser.add_argument("--limit", type=int, help="Limit checked sources, useful for smoke tests")
    parser.add_argument("--timeout", type=int, default=25, help="HTTP timeout per source in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Do not write snapshot or report")
    parser.add_argument("--json", action="store_true", help="Print results as JSON")
    args = parser.parse_args(argv)

    platforms = set(args.platform) if args.platform else None
    results, snapshot = check_sources(platforms=platforms, limit=args.limit, timeout=args.timeout)

    if not args.dry_run:
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_report(results)

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        counts: dict[str, int] = {}
        for result in results:
            counts[result["monitor_status"]] = counts.get(result["monitor_status"], 0) + 1
        print("Social platform monitor:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no sources")
        for result in results:
            if result["monitor_status"] in {"changed", "new", "error"}:
                print(f"  {result['monitor_status']}: {result['platform']} - {result['title']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

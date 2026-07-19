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
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scripts.autonomy.approval_queue import stage_findings
from scripts.autonomy.impact import build_impact_card
from scripts.autonomy.ledger import LedgerRecord, record_run

WORKFLOW = "scripts.social.platform_change_monitor"

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "harness" / "references" / "social-platform-source-registry.json"
SNAPSHOT = ROOT / "harness" / "references" / "social-platform-source-snapshot.json"
REPORT = ROOT / "harness" / "references" / "social-platform-monitor-report.md"
USER_AGENT = "KaiCMOHarnessPolicyMonitor/1.0 (+https://github.com/cgallic/kai-cmo-harness)"
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)
CUSTOM_UA_HOSTS = {
    "creators.instagram.com",
    "developers.facebook.com",
    "transparency.meta.com",
}


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
    errors: list[dict[str, Any]] = []
    urls = [source["url"], *source.get("fallback_urls", [])]

    for candidate_url in urls:
        req = Request(
            candidate_url,
            headers=_headers_for_url(candidate_url),
        )
        started = time.monotonic()
        try:
            with urlopen(req, timeout=timeout) as response:
                body = response.read()
                content_type = response.headers.get("content-type", "")
                cleaned = _clean_text(body, content_type)
                _validate_source_content(source, cleaned)
                digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
                result = {
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
                if candidate_url != source["url"]:
                    result["resolved_url"] = candidate_url
                return result
        except HTTPError as exc:
            error = _error_result(exc, getattr(exc, "code", None), started)
        except URLError as exc:
            error = _error_result(exc, None, started)
        except TimeoutError as exc:
            error = _error_result(exc, None, started)

        error["attempted_url"] = candidate_url
        errors.append(error)

    final_error = errors[-1] if errors else _error_result(RuntimeError("fetch failed"), None, time.monotonic())
    final_error["attempted_urls"] = urls
    return final_error


def _validate_source_content(source: dict[str, Any], cleaned: str) -> None:
    minimum_length = source.get("minimum_content_length")
    if minimum_length and len(cleaned) < int(minimum_length):
        raise ValueError(
            f"content shorter than minimum_content_length={minimum_length}"
        )


def _headers_for_url(candidate_url: str) -> dict[str, str]:
    host = urlparse(candidate_url).netloc.lower()
    user_agent = USER_AGENT if host in CUSTOM_UA_HOSTS else BROWSER_USER_AGENT
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.5",
        "Accept-Language": "en-US,en;q=0.9",
    }


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
    previous_errors = snapshot.get("errors", {})
    selected = registry.get("sources", [])
    if platforms:
        selected = [s for s in selected if s.get("platform") in platforms]
    if limit:
        selected = selected[:limit]

    results: list[dict[str, Any]] = []
    new_sources = dict(previous_sources)
    new_errors = dict(previous_errors)

    for source in selected:
        current = _fetch_source(source, timeout=timeout)
        previous = previous_sources.get(source["id"])
        state = _status(previous, current)
        was_error = source["id"] in previous_errors
        result = {**source, **current, "monitor_status": state, "previous_error": was_error}
        if previous:
            result["previous_hash"] = previous.get("content_hash")
            result["previous_checked_at"] = previous.get("checked_at")
        if current.get("ok"):
            new_errors.pop(source["id"], None)
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
                "resolved_url": current.get("resolved_url"),
                "checked_at": current.get("fetched_at"),
            }
        else:
            new_errors[source["id"]] = {
                "platform": source.get("platform"),
                "url": source.get("url"),
                "status_code": current.get("status_code"),
                "error": current.get("error"),
                "checked_at": current.get("fetched_at"),
            }
        results.append(result)

    updated_snapshot = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": new_sources,
        "errors": new_errors,
    }
    return results, updated_snapshot


def build_impact_cards(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn raw source results into practical impact cards (issue #27)."""
    return [build_impact_card(result) for result in results]


def write_report(results: list[dict[str, Any]], path: Path = REPORT) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    changed = [r for r in results if r["monitor_status"] == "changed"]
    new = [r for r in results if r["monitor_status"] == "new"]
    errors = [r for r in results if r["monitor_status"] == "error"]
    unchanged = [r for r in results if r["monitor_status"] == "unchanged"]

    cards = build_impact_cards(results)
    # Surface anything that needs a human or moved this run.
    actionable = [
        c
        for c in cards
        if c["monitor_status"] in {"changed", "new", "error"}
        or c["source_status"] in {"fixed", "replaced", "unresolved"}
    ]

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

    if actionable:
        lines.append("## Impact Cards")
        lines.append("")
        for card in actionable:
            lines.append(f"### [{card['platform']}] {card['title']}")
            lines.append("")
            lines.append(f"- **What changed:** {card['what_changed']}")
            lines.append(f"- **Why it matters:** {card['why_it_matters']} (area: {card['impact_area']})")
            lines.append(f"- **Action taken:** {card['action_taken']}")
            lines.append(f"- **Remaining risk:** {card['remaining_risk']}")
            lines.append(f"- **Decision:** `{card['decision']}` ({card['decision_reason']})")
            lines.append(f"- **Risk:** `{card['risk_level']}` · **Confidence:** {card['confidence']}")
            lines.append(f"- **Source:** {card['source_url']}")
            resolved_url = card.get("resolved_url")
            if resolved_url and resolved_url != card["source_url"]:
                lines.append(f"- **Monitor fetch URL:** {resolved_url}")
            if card.get("owner_file"):
                lines.append(f"- **Owner doc:** `{card['owner_file']}`")
            lines.append(f"- **Next step:** {card['next_step']}")
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

    record = LedgerRecord(
        workflow=WORKFLOW,
        inputs={
            "platforms": sorted(args.platform) if args.platform else "all",
            "limit": args.limit,
            "dry_run": args.dry_run,
        },
    )

    platforms = set(args.platform) if args.platform else None
    results, snapshot = check_sources(platforms=platforms, limit=args.limit, timeout=args.timeout)
    cards = build_impact_cards(results)

    record.sources_checked = [r.get("id") for r in results]
    record.findings = [
        c
        for c in cards
        if c["monitor_status"] in {"changed", "new", "error"}
        or c["source_status"] in {"fixed", "replaced", "unresolved"}
    ]
    record.followups = sorted(
        {c["next_step"] for c in record.findings if c["next_step"] not in {"No action needed", ""}}
    )
    record.blockers = [
        f"{c['platform']} {c['title']}: source unresolved ({c['source_url']})"
        for c in record.findings
        if c["source_status"] == "unresolved"
    ]
    if record.blockers:
        record.lessons.append("social source unreachable; registry needs canonical replacement")
    record.validation = {
        "method": "content-hash diff vs snapshot",
        "sources_checked": len(results),
        "errors": sum(1 for r in results if r["monitor_status"] == "error"),
    }

    if not args.dry_run:
        SNAPSHOT.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_report(results)
        record.files_changed = [
            str(SNAPSHOT.relative_to(ROOT)),
            str(REPORT.relative_to(ROOT)),
        ]
        record.actions_taken.append("Updated snapshot and impact report")
        # Any finding the router staged for a human lands in the approval queue.
        staged = stage_findings(record.findings, WORKFLOW)
        if staged:
            record.actions_taken.append(f"Staged {len(staged)} finding(s) for approval")
    else:
        record.actions_taken.append("Dry run; no files written")

    record_run(record)

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

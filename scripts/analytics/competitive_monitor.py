"""
Competitive Monitor — Track competitor changes over time.

Monitors competitor websites for pricing changes, messaging shifts,
new features, and stores snapshots for comparison.

Usage:
    python -m scripts.analytics.competitive_monitor add "https://competitor.com" --name "CompetitorCo"
    python -m scripts.analytics.competitive_monitor check --all
    python -m scripts.analytics.competitive_monitor diff "CompetitorCo"
    python -m scripts.analytics.competitive_monitor report

Cron (daily at 9am):
    0 9 * * * cd /path/to/kai-marketing && python -m scripts.analytics.competitive_monitor check --all
"""

import argparse
import hashlib
import json
import logging
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

KAI_DIR = Path.home() / ".kai-marketing"
COMP_DIR = KAI_DIR / "competitive"
COMPETITORS_FILE = COMP_DIR / "competitors.json"

log = logging.getLogger("competitive-monitor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


def _ensure_dirs():
    COMP_DIR.mkdir(parents=True, exist_ok=True)
    (COMP_DIR / "snapshots").mkdir(exist_ok=True)


def _load_competitors() -> list[dict]:
    if COMPETITORS_FILE.exists():
        return json.loads(COMPETITORS_FILE.read_text())
    return []


def _save_competitors(competitors: list[dict]):
    COMPETITORS_FILE.write_text(json.dumps(competitors, indent=2, default=str))


def _fetch_page(url: str, timeout: int = 15) -> tuple[str, int]:
    """Fetch a page and return (content, status_code)."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; KaiMarketing/1.0; +https://kaicalls.com)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return content, resp.status
    except urllib.error.HTTPError as e:
        return "", e.code
    except Exception as e:
        return "", 0


def _extract_text(html: str) -> str:
    """Basic HTML → text extraction (no external deps)."""
    import re
    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _extract_pricing_signals(text: str) -> list[str]:
    """Extract pricing-related text fragments."""
    import re
    patterns = [
        r"\$\d+[\d,.]*(?:\s*/\s*(?:mo|month|year|yr|user|seat))?",
        r"(?:free|starter|basic|pro|premium|enterprise|business)\s*(?:plan|tier|pricing)?",
        r"(?:per\s+(?:month|year|user|seat))",
        r"(?:billed\s+(?:monthly|annually|yearly))",
        r"(?:free\s+trial|money.?back|guarantee)",
    ]
    signals = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 30)
            context_end = min(len(text), match.end() + 30)
            signals.append(text[context_start:context_end].strip())
    return list(set(signals))[:20]


def add_competitor(name: str, urls: list[str], notes: str = ""):
    """Add a competitor to track."""
    _ensure_dirs()
    competitors = _load_competitors()

    # Check for duplicate
    if any(c["name"].lower() == name.lower() for c in competitors):
        print(f"Competitor '{name}' already exists. Use 'update' to modify.")
        return

    competitor = {
        "name": name,
        "urls": urls,
        "notes": notes,
        "added_at": datetime.now(timezone.utc).isoformat(),
        "last_checked": None,
        "check_count": 0,
    }
    competitors.append(competitor)
    _save_competitors(competitors)
    print(json.dumps({"status": "added", "name": name, "urls": urls}))


def check_competitors(names: list[str] = None):
    """Check competitors for changes. Fetches pages and compares to last snapshot."""
    _ensure_dirs()
    competitors = _load_competitors()
    if not competitors:
        print("No competitors tracked. Run: competitive_monitor add 'https://competitor.com' --name 'CompetitorCo'")
        return []

    if names:
        competitors = [c for c in competitors if c["name"] in names]

    results = []
    for comp in competitors:
        comp_dir = COMP_DIR / "snapshots" / comp["name"].lower().replace(" ", "-")
        comp_dir.mkdir(parents=True, exist_ok=True)

        for url in comp["urls"]:
            log.info("Checking %s: %s", comp["name"], url)
            content, status = _fetch_page(url)

            if status == 0 or not content:
                results.append({
                    "name": comp["name"],
                    "url": url,
                    "status": "error",
                    "error": f"HTTP {status}" if status else "Connection failed",
                })
                continue

            text = _extract_text(content)
            current_hash = _content_hash(text)
            pricing_signals = _extract_pricing_signals(text)

            # Compare to last snapshot
            url_slug = hashlib.md5(url.encode()).hexdigest()[:8]
            snapshot_file = comp_dir / f"{url_slug}-latest.json"

            changed = False
            changes_detected = []
            if snapshot_file.exists():
                prev = json.loads(snapshot_file.read_text())
                if prev.get("content_hash") != current_hash:
                    changed = True
                    # Detect specific changes
                    prev_pricing = set(prev.get("pricing_signals", []))
                    curr_pricing = set(pricing_signals)
                    new_pricing = curr_pricing - prev_pricing
                    removed_pricing = prev_pricing - curr_pricing
                    if new_pricing:
                        changes_detected.append(f"New pricing signals: {list(new_pricing)[:5]}")
                    if removed_pricing:
                        changes_detected.append(f"Removed pricing signals: {list(removed_pricing)[:5]}")
                    if not new_pricing and not removed_pricing:
                        changes_detected.append("Content changed (non-pricing)")

            # Save current snapshot
            snapshot = {
                "url": url,
                "content_hash": current_hash,
                "text_length": len(text),
                "pricing_signals": pricing_signals,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "status_code": status,
            }
            snapshot_file.write_text(json.dumps(snapshot, indent=2))

            # Also save timestamped archive
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            archive_file = comp_dir / f"{url_slug}-{ts}.json"
            if not archive_file.exists():
                archive_file.write_text(json.dumps(snapshot, indent=2))

            results.append({
                "name": comp["name"],
                "url": url,
                "status": "changed" if changed else "no_change",
                "changes": changes_detected if changed else [],
                "pricing_signals": pricing_signals[:5],
                "content_length": len(text),
            })

        # Update check metadata
        comp["last_checked"] = datetime.now(timezone.utc).isoformat()
        comp["check_count"] = comp.get("check_count", 0) + 1

    _save_competitors(_load_competitors())  # save updated check counts

    # Log results
    changes_log = KAI_DIR / "analytics" / "competitive-changes.jsonl"
    changes_log.parent.mkdir(parents=True, exist_ok=True)
    with open(changes_log, "a") as f:
        f.write(json.dumps({
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }, default=str) + "\n")

    return results


def format_results(results: list[dict]) -> str:
    """Format check results as readable report."""
    changed = [r for r in results if r.get("status") == "changed"]
    no_change = [r for r in results if r.get("status") == "no_change"]
    errors = [r for r in results if r.get("status") == "error"]

    lines = [
        "COMPETITIVE MONITOR",
        "=" * 50,
        f"Checked: {len(results)} URLs  |  Changed: {len(changed)}  |  Errors: {len(errors)}",
        "",
    ]

    if changed:
        lines.append("CHANGES DETECTED:")
        for r in changed:
            lines.append(f"  ! {r['name']}: {r['url']}")
            for c in r.get("changes", []):
                lines.append(f"    -> {c}")
        lines.append("")

    if errors:
        lines.append("ERRORS:")
        for r in errors:
            lines.append(f"  X {r['name']}: {r.get('error', 'unknown')}")
        lines.append("")

    if no_change:
        lines.append(f"No changes: {', '.join(set(r['name'] for r in no_change))}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Competitive monitoring")
    subparsers = parser.add_subparsers(dest="command")

    add_p = subparsers.add_parser("add", help="Add a competitor to track")
    add_p.add_argument("url", help="Competitor URL to track")
    add_p.add_argument("--name", required=True, help="Competitor name")
    add_p.add_argument("--notes", default="", help="Notes about this competitor")

    check_p = subparsers.add_parser("check", help="Check competitors for changes")
    check_p.add_argument("--all", action="store_true", help="Check all competitors")
    check_p.add_argument("--name", help="Check specific competitor")
    check_p.add_argument("--format", choices=["text", "json"], default="text")

    list_p = subparsers.add_parser("list", help="List tracked competitors")

    args = parser.parse_args()

    if args.command == "add":
        add_competitor(args.name, [args.url], args.notes)
    elif args.command == "check":
        names = [args.name] if args.name else None
        results = check_competitors(names)
        if hasattr(args, "format") and args.format == "json":
            print(json.dumps(results, indent=2, default=str))
        else:
            print(format_results(results))
    elif args.command == "list":
        competitors = _load_competitors()
        if not competitors:
            print("No competitors tracked.")
        else:
            for c in competitors:
                print(f"  {c['name']}: {', '.join(c['urls'])} (checked {c.get('check_count', 0)}x)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

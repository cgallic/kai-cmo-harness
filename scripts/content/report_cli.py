"""
Report CLI — Pull performance data for published content.

Usage:
    python report_cli.py --all
    python report_cli.py --site kaicalls
    python report_cli.py --format json
"""

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

KAI_DIR = Path.home() / ".kai-marketing"


def _load_content_log() -> list:
    """Load content log from ~/.kai-marketing/ or workspace/."""
    # Try JSONL (skill path)
    jsonl_path = KAI_DIR / "content-log.jsonl"
    if jsonl_path.exists():
        entries = []
        for line in jsonl_path.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    # Fallback to JSON array (legacy path)
    json_path = _ROOT / "workspace" / "content_log.json"
    if json_path.exists():
        try:
            return json.loads(json_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return []


def main():
    parser = argparse.ArgumentParser(description="Pull content performance data")
    parser.add_argument("--all", action="store_true", help="Check all published content")
    parser.add_argument("--site", help="Filter by site key")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    entries = _load_content_log()
    if args.site:
        entries = [e for e in entries if e.get("site") == args.site]

    if not entries:
        print(json.dumps({"message": "No published content found."}) if args.format == "json" else "No published content found.")
        return

    # Try running performance check
    try:
        from scripts.self_improvement.performance_check import evaluate_performance, pull_gsc_data, pull_ga4_data
        results = []
        for e in entries:
            url = e.get("url", "")
            keyword = e.get("keyword", "")
            site = e.get("site", "")
            if url and keyword:
                gsc = pull_gsc_data(url, keyword, site)
                ga4 = pull_ga4_data(url, site)
                ev = evaluate_performance(e, gsc, ga4)
                e["performance_30d"] = ev.get("grade")
            results.append(e)
    except ImportError:
        # If performance_check unavailable, just list content
        results = [{"id": e.get("id", "?"), "site": e.get("site"), "keyword": e.get("keyword"),
                     "format": e.get("format"), "publish_date": e.get("publish_date"),
                     "four_us_score": e.get("four_us_score"), "performance_30d": e.get("performance_30d")}
                    for e in entries]

    if args.format == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        winners = [r for r in results if r.get("performance_30d") == "winner"]
        avg = [r for r in results if r.get("performance_30d") == "average"]
        under = [r for r in results if r.get("performance_30d") == "underperformer"]
        pending = [r for r in results if r.get("performance_30d") is None]

        print(f"Content Report — {len(entries)} pieces")
        print(f"  Winners: {len(winners)}  |  Average: {len(avg)}  |  Under: {len(under)}  |  Pending: {len(pending)}")
        print()
        for r in results[:20]:
            status = r.get("performance_30d", "pending") or "pending"
            icon = {"winner": "+", "average": "~", "underperformer": "-", "pending": "?"}
            print(f"  [{icon.get(status, '?')}] {r.get('id', '?')}  {r.get('keyword', '')}  ({status})")


if __name__ == "__main__":
    main()

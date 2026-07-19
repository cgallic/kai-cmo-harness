#!/usr/bin/env python3
"""Knowledge freshness sweep.

Scans knowledge/ markdown docs for date metadata (``**Created:**`` or
``**Last verified:**`` lines) and flags docs past their shelf life so
volatile claims (roles, prices, benchmarks, platform behavior) get
re-verified instead of silently decaying. Advisory by default — exits 0
unless --strict is passed with stale docs present.

Usage:
    python scripts/knowledge_freshness.py                 # report
    python scripts/knowledge_freshness.py --months 6      # tighter window
    python scripts/knowledge_freshness.py --strict        # exit 1 on stale
    python scripts/knowledge_freshness.py --dir knowledge/people

A doc's freshness date is its ``**Last verified:**`` line when present,
else its ``**Created:**`` line. Docs with neither are reported as
"undated" (index files starting with ``_`` are skipped — they change with
the tree, not with the calendar).
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

DATE_LINE = re.compile(
    r"\*\*(Last verified|Created):\*\*\s*(?:(\w+)\s+)?(\d{4})", re.IGNORECASE
)
MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        start=1,
    )
}


def doc_date(path: Path):
    """Return (date, kind) from metadata, preferring Last verified."""
    found = {}
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        return None, None
    for match in DATE_LINE.finditer(head):
        kind = match.group(1).lower()
        month = MONTHS.get((match.group(2) or "").lower(), 6)
        found[kind] = date(int(match.group(3)), month, 1)
    if "last verified" in found:
        return found["last verified"], "last verified"
    if "created" in found:
        return found["created"], "created"
    return None, None


def months_between(old: date, new: date) -> int:
    return (new.year - old.year) * 12 + new.month - old.month


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag stale knowledge docs")
    parser.add_argument("--dir", default="knowledge", help="directory to scan")
    parser.add_argument("--months", type=int, default=12, help="staleness window")
    parser.add_argument("--strict", action="store_true", help="exit 1 if stale docs found")
    parser.add_argument("--show-all-undated", action="store_true", help="list every undated doc")
    args = parser.parse_args()

    root = Path(args.dir)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    today = date.today()
    stale, undated, fresh = [], [], 0
    for path in sorted(root.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        stamp, kind = doc_date(path)
        if stamp is None:
            undated.append(path)
        elif months_between(stamp, today) >= args.months:
            stale.append((path, stamp, kind))
        else:
            fresh += 1

    print(f"Knowledge freshness sweep — {root}/ (window: {args.months} months)")
    print(f"  fresh: {fresh}   stale: {len(stale)}   undated: {len(undated)}\n")
    if stale:
        print("Stale (re-verify volatile claims — roles, prices, benchmarks):")
        for path, stamp, kind in stale:
            print(f"  {path}  ({kind} {stamp.strftime('%B %Y')})")
        print()
    if undated:
        print("Undated (add a '**Created:**' or '**Last verified:**' line):")
        shown = undated if args.show_all_undated else undated[:15]
        for path in shown:
            print(f"  {path}")
        hidden = len(undated) - len(shown)
        if hidden:
            print(f"  ... and {hidden} more (--show-all-undated to list)")
        print()
    if not stale and not undated:
        print("All dated docs inside the freshness window.")

    return 1 if (args.strict and stale) else 0


if __name__ == "__main__":
    sys.exit(main())

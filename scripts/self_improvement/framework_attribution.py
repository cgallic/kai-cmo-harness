#!/usr/bin/env python3
"""Framework attribution report — grade the frameworks, not just the pieces.

Content-log entries record which knowledge/reference frameworks informed each
draft (``frameworks`` field, written by the engine). The 30-day performance
loop grades entries winner/average/underperformer. This report joins the two:
per-framework grade counts and winner rates, so the knowledge base learns
which frameworks actually work from measured outcomes instead of doctrine.

Entries written before the ``frameworks`` field existed are attributed via
the format -> framework registry (``GENERATION_FRAMEWORK_MAP``) and counted
as "inferred" so exact and inferred attribution stay distinguishable.

Usage:
    python scripts/self_improvement/framework_attribution.py            # table
    python scripts/self_improvement/framework_attribution.py --json     # machine-readable
    python scripts/self_improvement/framework_attribution.py --min-graded 5

Review flag: a framework with >= --min-graded graded pieces and a winner
rate below --flag-below (default 0.34) is listed as a review candidate —
a prompt to re-read the framework doc and diagnose via /kai-retro, never
an automatic edit to the knowledge base.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.content.content_log import load_log  # noqa: E402
from scripts.self_improvement.grades import (  # noqa: E402
    GRADE_AVERAGE,
    GRADE_UNDERPERFORMER,
    GRADE_WINNER,
    get_grade,
)

GRADES = (GRADE_WINNER, GRADE_AVERAGE, GRADE_UNDERPERFORMER)


def _infer_frameworks(entry: dict) -> list[str]:
    """Legacy fallback: map an entry's format to its framework registry paths."""
    fmt = entry.get("format") or entry.get("platform")
    if not fmt:
        return []
    try:
        from kai.runtime.workflows import get_framework_paths
    except Exception:
        return []
    try:
        return list(get_framework_paths(str(fmt)))
    except Exception:
        return []


def aggregate(entries: list) -> dict[str, dict]:
    """Aggregate grade counts per framework path.

    Returns {framework_path: {winner, average, underperformer, ungraded,
    graded, inferred, winner_rate}}. Entries without any attributable
    framework are skipped (they can't inform a framework verdict).
    """
    stats: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        frameworks = entry.get("frameworks")
        inferred = False
        if not frameworks:
            frameworks = _infer_frameworks(entry)
            inferred = True
        if not frameworks:
            continue
        grade = get_grade(entry)
        for fw in frameworks:
            row = stats.setdefault(
                fw,
                {g: 0 for g in GRADES} | {"ungraded": 0, "graded": 0, "inferred": 0},
            )
            if inferred:
                row["inferred"] += 1
            if grade in GRADES:
                row[grade] += 1
                row["graded"] += 1
            else:
                row["ungraded"] += 1
    for row in stats.values():
        row["winner_rate"] = (
            round(row[GRADE_WINNER] / row["graded"], 3) if row["graded"] else None
        )
    return stats


def review_candidates(stats: dict[str, dict], min_graded: int, flag_below: float) -> list[str]:
    return sorted(
        fw
        for fw, row in stats.items()
        if row["graded"] >= min_graded
        and row["winner_rate"] is not None
        and row["winner_rate"] < flag_below
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Per-framework 30-day grade report")
    parser.add_argument("--log-file", default=None, help="content log path override")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    parser.add_argument("--min-graded", type=int, default=3, help="graded pieces before a framework can be flagged")
    parser.add_argument("--flag-below", type=float, default=0.34, help="winner-rate threshold for the review flag")
    args = parser.parse_args()

    entries = load_log(args.log_file)
    stats = aggregate(entries)
    flagged = review_candidates(stats, args.min_graded, args.flag_below)

    if args.json:
        print(json.dumps({"frameworks": stats, "review_candidates": flagged}, indent=2))
        return 0

    if not stats:
        print("No content-log entries with attributable frameworks yet.")
        print("Entries gain a 'frameworks' field as the engine generates content.")
        return 0

    print("Framework attribution — 30-day grades per framework\n")
    header = f"{'framework':60}  {'win':>4} {'avg':>4} {'under':>5} {'ungr':>4}  {'win rate':>8}"
    print(header)
    print("-" * len(header))
    for fw in sorted(stats, key=lambda f: (-(stats[f]['winner_rate'] or 0), f)):
        row = stats[fw]
        rate = f"{row['winner_rate']:.0%}" if row["winner_rate"] is not None else "—"
        inferred = f" ({row['inferred']} inferred)" if row["inferred"] else ""
        print(
            f"{fw[:60]:60}  {row[GRADE_WINNER]:>4} {row[GRADE_AVERAGE]:>4} "
            f"{row[GRADE_UNDERPERFORMER]:>5} {row['ungraded']:>4}  {rate:>8}{inferred}"
        )
    if flagged:
        print(f"\nReview candidates (>= {args.min_graded} graded, winner rate < {args.flag_below:.0%}):")
        for fw in flagged:
            print(f"  {fw}")
        print("Diagnose via /kai-retro before changing any framework doc.")
    else:
        print("\nNo review candidates at current thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

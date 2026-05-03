"""
CLI for recording downstream quality labels on traces.

These labels feed HALO's optimization loop: a `useful` weekly_report
trace is something to amplify; an `ignored` daily_analytics trace is
something to compress or drop.

Usage:

    python -m agent.traces.quality <trace_id> useful --note "Connor reacted 👍"
    python -m agent.traces.quality <trace_id> noisy --source discord
    python -m agent.traces.quality --list <trace_id>
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .models import QualityLabel, trace_store


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent.traces.quality",
        description="Record downstream quality labels on a trace.",
    )
    parser.add_argument("trace_id")
    parser.add_argument(
        "label",
        nargs="?",
        choices=[q.value for q in QualityLabel],
        help="Quality label to record. Omit with --list to inspect existing labels.",
    )
    parser.add_argument("--note", default=None)
    parser.add_argument(
        "--source",
        default=None,
        help="Origin of the label (e.g. discord, manual, classifier).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing labels for the trace and exit.",
    )

    args = parser.parse_args(argv)

    if args.list:
        rows = trace_store.get_quality(args.trace_id)
        json.dump(rows, sys.stdout, default=str, indent=2)
        sys.stdout.write("\n")
        return 0

    if not args.label:
        parser.error("label is required unless --list is passed")

    trace_store.record_quality(
        args.trace_id,
        QualityLabel(args.label),
        note=args.note,
        source=args.source,
    )
    print(f"[traces] recorded label={args.label} on trace_id={args.trace_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

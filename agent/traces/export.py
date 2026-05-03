"""
Export trace spans as HALO-compatible JSONL.

Usage:

    python -m agent.traces.export --since 7d > traces/cmo_traces.jsonl
    python -m agent.traces.export --since 24h --task-id weekly_report
    python -m agent.traces.export --client kai-calls --status error

The output is one JSON object per line: each row is a single span,
fully self-describing with trace_id/parent_span_id so HALO can
reconstruct the trace tree without an additional schema.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import SpanStatus, trace_store


_DURATION_RE = re.compile(r"^(?P<num>\d+)(?P<unit>[smhd])$")


def parse_since(value: Optional[str]) -> Optional[datetime]:
    """
    Accept "7d", "24h", "30m", "120s", or an ISO timestamp.
    """
    if not value:
        return None
    m = _DURATION_RE.match(value.strip())
    if m:
        num = int(m.group("num"))
        unit = m.group("unit")
        delta = {
            "s": timedelta(seconds=num),
            "m": timedelta(minutes=num),
            "h": timedelta(hours=num),
            "d": timedelta(days=num),
        }[unit]
        return datetime.utcnow() - delta
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid --since value: {value!r} ({exc})")


def _emit(rows, out) -> int:
    count = 0
    for span in rows:
        out.write(json.dumps(span.to_halo_dict(), default=str))
        out.write("\n")
        count += 1
    return count


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent.traces.export",
        description="Export CMO harness trace spans as HALO-compatible JSONL.",
    )
    parser.add_argument(
        "--since",
        default="7d",
        help="Window start. Duration like 7d/24h/30m/120s, or ISO timestamp. Default: 7d.",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Optional window end (ISO timestamp). Default: now.",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Filter by task_id (e.g. weekly_report).",
    )
    parser.add_argument(
        "--client",
        default=None,
        help="Filter by client (e.g. kai-calls).",
    )
    parser.add_argument(
        "--status",
        default=None,
        choices=[s.value for s in SpanStatus],
        help="Filter by span status.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit total spans emitted.",
    )
    parser.add_argument(
        "--out",
        default="-",
        help="Output path. Default: stdout (-).",
    )

    args = parser.parse_args(argv)

    since = parse_since(args.since)
    until = parse_since(args.until) if args.until else None

    spans = trace_store.list_spans(
        since=since,
        until=until,
        task_id=args.task_id,
        client=args.client,
        status=SpanStatus(args.status) if args.status else None,
        limit=args.limit,
    )

    if args.out == "-":
        count = _emit(spans, sys.stdout)
    else:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as out:
            count = _emit(spans, out)

    print(f"[traces] exported {count} spans", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
HALO-style trace diagnosis runner.

Builds a structured digest of recent trace activity (failures, retries,
LLM token usage, scheduler health, notification volume) and asks an
LLM to surface concrete harness improvements.

Usage:

    python -m agent.traces.diagnose --since 7d
    python -m agent.traces.diagnose --since 7d --task-id weekly_report \\
        --prompt "Analyze why weekly business reports are low-signal."

Output is markdown-formatted: digest first, then LLM-suggested actions.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .export import parse_since
from .models import QualityLabel, SpanKind, SpanStatus, TraceSpan, trace_store


DEFAULT_PROMPT = (
    "Find recurring task failures, weak prompt/tool boundaries, missing context, "
    "notification spam, and scheduler issues. Suggest concrete harness changes."
)


def build_digest(spans: List[TraceSpan]) -> Dict[str, Any]:
    """
    Aggregate spans into a compact digest suitable for an LLM prompt.

    Keeps cardinality bounded so the digest stays small even over wide
    windows (e.g. 7d of every-5-min tasks).
    """
    if not spans:
        return {"window": "empty", "span_count": 0}

    # Group spans by trace.
    traces: Dict[str, List[TraceSpan]] = defaultdict(list)
    for span in spans:
        traces[span.trace_id].append(span)

    # Per-task aggregates.
    task_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "executions": 0,
        "errors": 0,
        "timeouts": 0,
        "total_duration_ms": 0,
        "llm_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "notifications": 0,
        "external_errors": Counter(),
        "error_signatures": Counter(),
    })

    notification_volume = 0
    scheduler_decisions = 0

    for trace_id, group in traces.items():
        # Find the root span for the trace (kind=task, no parent).
        root = next(
            (s for s in group if s.kind == SpanKind.TASK and not s.parent_span_id),
            group[0],
        )
        task_id = root.task_id or root.name
        stats = task_stats[task_id]
        stats["executions"] += 1
        if root.status == SpanStatus.ERROR:
            stats["errors"] += 1
            sig = (root.error or "").split("\n", 1)[0][:160]
            if sig:
                stats["error_signatures"][sig] += 1

        for span in group:
            if span.duration_ms:
                stats["total_duration_ms"] += span.duration_ms

            if span.kind == SpanKind.LLM:
                stats["llm_calls"] += 1
                stats["input_tokens"] += int(span.attributes.get("input_tokens") or 0)
                stats["output_tokens"] += int(span.attributes.get("output_tokens") or 0)
                cost = span.attributes.get("estimated_cost_usd")
                if isinstance(cost, (int, float)):
                    stats["estimated_cost_usd"] += float(cost)

            if span.kind == SpanKind.NOTIFICATION:
                stats["notifications"] += 1
                notification_volume += 1

            if span.kind == SpanKind.SCHEDULER:
                scheduler_decisions += 1

            if span.kind == SpanKind.EXTERNAL_API and span.status == SpanStatus.ERROR:
                endpoint = span.inputs.get("endpoint") or span.name
                stats["external_errors"][str(endpoint)] += 1

            if span.status == SpanStatus.TIMEOUT:
                stats["timeouts"] += 1

    # Convert counters to top-N lists for compact serialization.
    digest_tasks: Dict[str, Any] = {}
    for task_id, stats in task_stats.items():
        digest_tasks[task_id] = {
            "executions": stats["executions"],
            "errors": stats["errors"],
            "timeouts": stats["timeouts"],
            "error_rate": (
                round(stats["errors"] / stats["executions"], 3)
                if stats["executions"]
                else 0.0
            ),
            "avg_duration_ms": (
                int(stats["total_duration_ms"] / stats["executions"])
                if stats["executions"]
                else 0
            ),
            "llm_calls": stats["llm_calls"],
            "input_tokens": stats["input_tokens"],
            "output_tokens": stats["output_tokens"],
            "estimated_cost_usd": round(stats["estimated_cost_usd"], 4),
            "notifications": stats["notifications"],
            "top_external_errors": stats["external_errors"].most_common(5),
            "top_error_signatures": stats["error_signatures"].most_common(5),
        }

    # Quality-label rollup so HALO can prefer "useful" patterns.
    quality_rollup: Counter = Counter()
    for trace_id in traces.keys():
        for q in trace_store.get_quality(trace_id):
            quality_rollup[q["label"]] += 1

    return {
        "span_count": len(spans),
        "trace_count": len(traces),
        "scheduler_decisions": scheduler_decisions,
        "notification_volume": notification_volume,
        "tasks": digest_tasks,
        "quality_labels": dict(quality_rollup),
    }


def render_digest_markdown(digest: Dict[str, Any]) -> str:
    if digest.get("span_count", 0) == 0:
        return "_No spans found in the requested window._\n"

    lines: List[str] = []
    lines.append(f"- spans: **{digest['span_count']}**, traces: **{digest['trace_count']}**")
    lines.append(f"- scheduler decisions: {digest['scheduler_decisions']}")
    lines.append(f"- notifications sent: {digest['notification_volume']}")
    if digest.get("quality_labels"):
        labels = ", ".join(f"{k}: {v}" for k, v in digest["quality_labels"].items())
        lines.append(f"- quality labels: {labels}")
    lines.append("")
    lines.append("| task | runs | errors | timeouts | err_rate | avg_ms | llm_calls | tokens (in/out) | cost $ |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
    for task_id, t in sorted(digest["tasks"].items()):
        lines.append(
            f"| {task_id} | {t['executions']} | {t['errors']} | {t['timeouts']} | "
            f"{t['error_rate']} | {t['avg_duration_ms']} | {t['llm_calls']} | "
            f"{t['input_tokens']}/{t['output_tokens']} | {t['estimated_cost_usd']} |"
        )
    return "\n".join(lines) + "\n"


def diagnose_spans(spans: List[Any]) -> str:
    """Return a local heuristic diagnosis for lightweight recorder spans."""
    if not spans:
        return "## Trace digest\n_No spans provided._\n"

    error_spans = [span for span in spans if getattr(span, "status", "") == "error"]
    llm_spans = [
        span for span in spans
        if str(getattr(span, "span", getattr(span, "name", ""))).startswith("llm.")
    ]
    missing_prompt_metadata = [
        span for span in llm_spans
        if not (getattr(span, "metadata", {}) or {}).get("prompt_name")
        or not (getattr(span, "metadata", {}) or {}).get("prompt_version")
    ]

    lines = [
        "## Recurring Failures",
        f"- error spans: {len(error_spans)}",
    ]
    for span in error_spans[:5]:
        lines.append(
            f"- {getattr(span, 'span', getattr(span, 'name', '<unknown>'))}: "
            f"{getattr(span, 'error', '') or 'unknown error'}"
        )

    lines.extend(["", "## Prompt/Tool Boundaries"])
    if missing_prompt_metadata:
        lines.append(
            "- LLM spans should pass `prompt_name` and `prompt_version` so trace diagnosis can link failures to prompt templates."
        )
    else:
        lines.append("- LLM prompt metadata is present on recorded spans.")

    lines.extend([
        "",
        "## Next Harness Changes",
        "- Add or repair metadata at the span boundary before changing downstream diagnosis prompts.",
    ])
    return "\n".join(lines) + "\n"


async def diagnose(
    *,
    since: Optional[datetime],
    until: Optional[datetime],
    task_id: Optional[str],
    client: Optional[str],
    prompt: str,
    use_llm: bool,
) -> str:
    spans = trace_store.list_spans(
        since=since, until=until, task_id=task_id, client=client
    )
    digest = build_digest(spans)
    digest_md = render_digest_markdown(digest)

    if not use_llm or digest.get("span_count", 0) == 0:
        return f"## Trace digest\n{digest_md}"

    # Lazy import to avoid pulling OpenRouter into pure-export usage.
    from ..llm import llm_router

    system = (
        "You are HALO, a harness optimization assistant. You read trace digests "
        "from the CMO marketing agent and produce a punch list of concrete harness "
        "changes. Each suggestion must be actionable: name the task, span, or "
        "prompt; say what to change; and explain why. Do not speculate beyond what "
        "the digest supports."
    )

    body = (
        f"{prompt}\n\n"
        f"## Trace digest\n{digest_md}\n"
        f"## Raw digest JSON (for reference)\n```json\n"
        f"{json.dumps(digest, default=str, indent=2)}\n```"
    )

    suggestions = await llm_router.complete(
        prompt=body,
        system=system,
        task_type="weekly_report",
        prompt_name="halo_diagnose",
        prompt_version="v1",
        max_tokens=2048,
        temperature=0.2,
    )

    return (
        f"## Trace digest\n{digest_md}\n"
        f"## HALO suggestions\n{suggestions}\n"
    )


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent.traces.diagnose",
        description="Run HALO-style diagnosis over recent trace spans.",
    )
    parser.add_argument("--since", default="7d", help="Window start (e.g. 7d).")
    parser.add_argument("--until", default=None)
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--client", default=None)
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Diagnosis prompt to send to HALO.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Print the digest only, skip the LLM step.",
    )

    args = parser.parse_args(argv)

    since = parse_since(args.since)
    until = parse_since(args.until) if args.until else None

    output = asyncio.run(
        diagnose(
            since=since,
            until=until,
            task_id=args.task_id,
            client=args.client,
            prompt=args.prompt,
            use_llm=not args.no_llm,
        )
    )
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

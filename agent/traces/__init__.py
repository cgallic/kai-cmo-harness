"""
HALO-style structured tracing for the CMO harness.

Provides span-level capture across scheduler decisions, task execution,
LLM calls, external API fetches, transforms, synthesis, and notifications.
The resulting trace store powers HALO-style diagnosis loops that surface
recurring failures, weak prompt/tool boundaries, low-signal outputs, and
noisy alerts so the harness can be improved over time.

Usage:

    from agent.traces import tracer, SpanKind

    async with tracer.trace(task_id="weekly_report", client="kaicalls") as t:
        async with t.span("fetch_metrics", kind=SpanKind.EXTERNAL_API):
            ...

Trace data is persisted to the agent SQLite database in `task_spans` and
can be exported as HALO-compatible JSONL with:

    python -m agent.traces.export --since 7d > traces/cmo_traces.jsonl
"""

from .models import (
    QualityLabel,
    SpanKind,
    SpanStatus,
    TraceSpan,
    trace_store,
)
from .tracer import Span, Tracer, current_trace_id, tracer

__all__ = [
    "QualityLabel",
    "Span",
    "SpanKind",
    "SpanStatus",
    "TraceSpan",
    "Tracer",
    "current_trace_id",
    "trace_store",
    "tracer",
]

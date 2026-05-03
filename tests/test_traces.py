"""Tests for the HALO-style trace store and tracer."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Force the trace store to use a fresh sqlite file for the test session.
import os
import tempfile

_tmp_db = Path(tempfile.mkdtemp(prefix="cmo-traces-")) / "agent.db"

import agent.config as agent_config_mod  # noqa: E402

agent_config_mod.agent_config._db_path = _tmp_db

# Re-import models to bind to the test DB.
import agent.traces.models as traces_models  # noqa: E402

traces_models.trace_store = traces_models.TraceStore(db_path=_tmp_db)

import agent.traces.tracer as tracer_mod  # noqa: E402

# Rebind the tracer module to the freshly-pathed store.
tracer_mod.trace_store = traces_models.trace_store

from agent.traces import (  # noqa: E402
    QualityLabel,
    SpanKind,
    SpanStatus,
    tracer,
)
from agent.traces.diagnose import build_digest, render_digest_markdown  # noqa: E402
from agent.traces.export import parse_since  # noqa: E402
from agent.traces.redact import redact, summarize_output  # noqa: E402


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_redact_removes_sensitive_keys():
    payload = {
        "api_key": "abc123",
        "Authorization": "Bearer xyz",
        "user": "Connor",
        "nested": {"password": "hunter2", "ok": "value"},
    }
    out = redact(payload)
    assert out["api_key"] == "[REDACTED]"
    assert out["Authorization"] == "[REDACTED]"
    assert out["user"] == "Connor"
    assert out["nested"]["password"] == "[REDACTED]"
    assert out["nested"]["ok"] == "value"


def test_redact_pattern_matches_long_tokens_and_emails():
    text = (
        "key=AKIAABCDEFGHIJKLMNOP "
        "email=connor@example.com "
        "phone=+1 415 555 0199 "
        "ok=hi"
    )
    out = redact(text)
    assert "AKIAABCDEFGHIJKLMNOP" not in out
    assert "connor@example.com" not in out
    assert "+1 415 555 0199" not in out
    assert "ok=hi" in out


def test_summarize_output_prefers_summary_field():
    value = {"summary": "All good", "raw": "x" * 5000}
    assert summarize_output(value).startswith("All good")


def test_summarize_output_truncates_long_strings():
    # Use varied content so the opaque-token redaction regex doesn't fire
    # before truncation has a chance to apply.
    text = "Lorem ipsum dolor sit amet, " * 100
    out = summarize_output(text, max_len=200)
    assert len(out) <= 200
    assert out.endswith("...")


# ---------------------------------------------------------------------------
# Tracer + store
# ---------------------------------------------------------------------------


def test_trace_root_and_child_spans_persist():
    async def run():
        async with tracer.trace(
            task_id="weekly_report",
            execution_id="exec1",
            client="kai-calls",
            root_span_name="task:weekly_report",
        ) as t:
            async with tracer.span(
                "fetch_metrics", kind=SpanKind.EXTERNAL_API
            ) as s:
                s.add_attributes(rows=42)
                s.set_output({"summary": "Sessions: 100"})
            return t.trace_id

    trace_id = asyncio.run(run())
    spans = traces_models.trace_store.get_trace(trace_id)
    assert len(spans) == 2
    by_name = {s.name: s for s in spans}
    assert "task:weekly_report" in by_name
    assert "fetch_metrics" in by_name

    fetch = by_name["fetch_metrics"]
    assert fetch.kind == SpanKind.EXTERNAL_API
    assert fetch.status == SpanStatus.OK
    assert fetch.outputs_summary.startswith("Sessions: 100")
    assert fetch.attributes["rows"] == 42
    assert fetch.parent_span_id == by_name["task:weekly_report"].span_id


def test_trace_captures_errors_with_redaction():
    async def run():
        try:
            async with tracer.trace(
                task_id="daily_analytics",
                execution_id="exec2",
                root_span_name="task:daily_analytics",
            ) as t:
                async with tracer.span("call_api", kind=SpanKind.EXTERNAL_API):
                    # 50-char opaque token triggers the long-token regex.
                    raise RuntimeError(
                        "auth failed token=abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN"
                    )
        except RuntimeError:
            pass
        return t.trace_id

    trace_id = asyncio.run(run())
    spans = traces_models.trace_store.get_trace(trace_id)
    statuses = {s.name: s.status for s in spans}
    assert statuses["call_api"] == SpanStatus.ERROR
    assert statuses["task:daily_analytics"] == SpanStatus.ERROR

    errored = next(s for s in spans if s.name == "call_api")
    assert "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN" not in (
        errored.error or ""
    )
    assert "[REDACTED]" in (errored.error or "")


def test_trace_handles_concurrent_traces():
    """Two concurrent traces must not share trace_id or parent_span_id."""

    async def run_one(task_id: str):
        async with tracer.trace(
            task_id=task_id,
            execution_id=f"exec-{task_id}",
            root_span_name=f"task:{task_id}",
        ) as t:
            await asyncio.sleep(0)
            async with tracer.span("step", kind=SpanKind.TRANSFORM):
                await asyncio.sleep(0)
            return t.trace_id

    async def run_both():
        return await asyncio.gather(run_one("a"), run_one("b"))

    trace_a, trace_b = asyncio.run(run_both())
    assert trace_a != trace_b
    spans_a = traces_models.trace_store.get_trace(trace_a)
    spans_b = traces_models.trace_store.get_trace(trace_b)
    assert {s.task_id for s in spans_a} == {"a"}
    assert {s.task_id for s in spans_b} == {"b"}


# ---------------------------------------------------------------------------
# Quality labels
# ---------------------------------------------------------------------------


def test_record_and_read_quality_labels():
    traces_models.trace_store.record_quality(
        "trace-q1",
        QualityLabel.USEFUL,
        note="Connor reacted",
        source="discord",
    )
    rows = traces_models.trace_store.get_quality("trace-q1")
    assert len(rows) == 1
    assert rows[0]["label"] == "useful"
    assert rows[0]["source"] == "discord"


# ---------------------------------------------------------------------------
# Digest + export
# ---------------------------------------------------------------------------


def test_build_digest_aggregates_by_task():
    async def run():
        async with tracer.trace(
            task_id="weekly_report",
            execution_id="d1",
            root_span_name="task:weekly_report",
        ):
            async with tracer.span("llm.complete:weekly", kind=SpanKind.LLM) as s:
                s.add_attributes(
                    input_tokens=100,
                    output_tokens=200,
                    estimated_cost_usd=0.0123,
                )

    asyncio.run(run())

    spans = traces_models.trace_store.list_spans(
        since=datetime.utcnow() - timedelta(hours=1)
    )
    digest = build_digest(spans)
    assert digest["span_count"] >= 2
    assert "weekly_report" in digest["tasks"]
    md = render_digest_markdown(digest)
    assert "weekly_report" in md


def test_parse_since_handles_durations_and_iso():
    now = datetime.utcnow()
    out = parse_since("1h")
    assert (now - out) < timedelta(hours=1, minutes=1)
    iso = parse_since("2026-05-01T00:00:00")
    assert iso.year == 2026


def test_export_emits_jsonl(tmp_path):
    from agent.traces.export import main

    out = tmp_path / "traces.jsonl"
    rc = main(["--since", "1d", "--out", str(out)])
    assert rc == 0
    # File may be empty if no spans matched, but it must be valid JSONL.
    if out.exists() and out.stat().st_size > 0:
        for line in out.read_text().splitlines():
            row = json.loads(line)
            assert "trace_id" in row
            assert "span_id" in row
            assert "kind" in row

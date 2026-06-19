from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from agent.models import AgentDatabase
import agent.llm.router as router_mod
from agent.traces.diagnose import diagnose_spans
from agent.traces.recorder import (
    export_span_json,
    parse_since,
    redact_value,
    trace_context,
    trace_span,
)


def test_trace_span_records_and_redacts(tmp_path):
    db = AgentDatabase(tmp_path / "agent.db")

    with trace_context(
        trace_id="trace_test",
        execution_id="exec_1",
        task_id="weekly_report",
        client="kaicalls",
    ):
        with trace_span(
            "external.fetch",
            inputs={"url": "https://api.example.com/data?access_token=abc123", "email": "owner@example.com"},
            metadata={"service": "example"},
            db=db,
        ) as span:
            span.set_output({"summary": "Fetched owner@example.com data"})

    spans = db.list_spans(trace_id="trace_test")

    assert len(spans) == 1
    assert spans[0].task_id == "weekly_report"
    assert spans[0].status == "ok"
    assert spans[0].inputs["url"].endswith("access_token=<redacted>")
    assert spans[0].inputs["email"] == "<redacted>"
    assert "<redacted-email>" in spans[0].outputs_summary


def test_export_span_json_is_jsonl_safe(tmp_path):
    db = AgentDatabase(tmp_path / "agent.db")

    with trace_context(trace_id="trace_export", execution_id="exec_2", task_id="ad_management"):
        with trace_span("task.execute", db=db) as span:
            span.set_output("ok")

    line = export_span_json(db.list_spans(trace_id="trace_export")[0])
    payload = json.loads(line)

    assert payload["trace_id"] == "trace_export"
    assert payload["span"] == "task.execute"
    assert payload["status"] == "ok"


def test_parse_since_duration():
    since = parse_since("7d")
    assert since is not None
    assert since.tzinfo is not None
    assert since < datetime.now(timezone.utc)


def test_diagnose_spans_reports_actionable_changes(tmp_path):
    db = AgentDatabase(tmp_path / "agent.db")

    with trace_context(trace_id="trace_diag", execution_id="exec_3", task_id="weekly_report"):
        with trace_span("llm.complete", metadata={"model": "test"}, db=db) as span:
            span.fail("missing context")

    report = diagnose_spans(db.list_spans(trace_id="trace_diag"))

    assert "Recurring Failures" in report
    assert "pass `prompt_name` and `prompt_version`" in report
    assert "Next Harness Changes" in report


def test_llm_router_records_usage(monkeypatch, tmp_path):
    import agent.traces.recorder as recorder
    from agent.llm.router import LLMRouter

    db = AgentDatabase(tmp_path / "agent.db")
    monkeypatch.setattr(recorder, "agent_db", db)

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Useful report"))],
                usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7, total_tokens=18),
            )

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    router = LLMRouter()
    router._client = FakeClient()

    async def run_complete():
        with trace_context(trace_id="trace_llm", execution_id="exec_4", task_id="weekly_report"):
            return await router.complete(
                "Write report",
                task_type="weekly_report",
                prompt_name="weekly_report",
                prompt_version="v1",
            )

    result = asyncio.run(run_complete())
    spans = db.list_spans(trace_id="trace_llm")

    assert result == "Useful report"
    assert spans[0].span == "llm.complete"
    assert spans[0].metadata["prompt_name"] == "weekly_report"
    assert spans[0].metadata["token_usage"]["total_tokens"] == 18


def test_llm_router_missing_openai_dependency_raises_helpful_error(monkeypatch):
    from agent.llm.router import LLMRouter

    monkeypatch.setattr(router_mod, "_OpenAIClient", None)
    monkeypatch.setattr(router_mod, "_google_genai", object())
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    router = LLMRouter()

    with pytest.raises(ImportError, match="openai package is required for OpenRouter/OpenAI agent routing"):
        _ = router.client


def test_llm_router_detects_openai_provider(monkeypatch):
    from agent.llm.router import LLMRouter

    monkeypatch.delenv("AGENT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")

    router = LLMRouter()

    assert router._detect_provider() == "openai"


def test_llm_router_detects_gemini_provider(monkeypatch):
    from agent.llm.router import LLMRouter

    monkeypatch.delenv("AGENT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")

    router = LLMRouter()

    assert router._detect_provider() == "gemini"


def test_redact_value_handles_tokens_and_contacts():
    payload = redact_value({
        "authorization": "Bearer sk-test",
        "url": "https://example.com?token=secret",
        "body": "Email me at person@example.com or call 555-123-4567",
    })

    assert payload["authorization"] == "<redacted>"
    assert payload["url"].endswith("token=<redacted>")
    assert "<redacted-email>" in payload["body"]
    assert "<redacted-phone>" in payload["body"]

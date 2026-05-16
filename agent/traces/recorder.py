"""Span recorder for task-level CMO agent traces."""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterator, Optional
from uuid import uuid4

from ..models import AgentDatabase, TaskSpan, agent_db


_trace_id_var: ContextVar[Optional[str]] = ContextVar("kai_trace_id", default=None)
_execution_id_var: ContextVar[Optional[str]] = ContextVar("kai_execution_id", default=None)
_task_id_var: ContextVar[Optional[str]] = ContextVar("kai_task_id", default=None)
_client_var: ContextVar[Optional[str]] = ContextVar("kai_client", default=None)


SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|token|secret|password|authorization|cookie|set-cookie|phone|email)",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(
    r"(?i)(bearer\s+)[a-z0-9._\-]+|"
    r"(sk-[a-z0-9_\-]{12,})|"
    r"([a-z0-9_\-]{24,}\.[a-z0-9_\-]{24,}\.[a-z0-9_\-]{24,})"
)
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?1[\s.\-]?)?(?:\(?\d{3}\)?[\s.\-]?)\d{3}[\s.\-]?\d{4}(?!\w)")
URL_TOKEN_RE = re.compile(r"(?i)(access_token|api_key|key|token)=([^&\s]+)")


def current_trace_context() -> Dict[str, Optional[str]]:
    """Return the active trace context."""
    return {
        "trace_id": _trace_id_var.get(),
        "execution_id": _execution_id_var.get(),
        "task_id": _task_id_var.get(),
        "client": _client_var.get(),
    }


@contextmanager
def trace_context(
    *,
    trace_id: str,
    task_id: str,
    execution_id: Optional[str] = None,
    client: Optional[str] = None,
) -> Iterator[None]:
    """Set trace context for nested span calls."""
    tokens = [
        (_trace_id_var, _trace_id_var.set(trace_id)),
        (_task_id_var, _task_id_var.set(task_id)),
        (_execution_id_var, _execution_id_var.set(execution_id)),
        (_client_var, _client_var.set(client)),
    ]
    try:
        yield
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)


class TraceScope:
    """Context manager that writes one task span to SQLite."""

    def __init__(
        self,
        span: str,
        *,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[AgentDatabase] = None,
    ):
        self.span = span
        self.inputs = redact_value(inputs or {})
        self.metadata = redact_value(metadata or {})
        self.db = db or agent_db
        self.id = f"spn_{uuid4().hex[:16]}"
        self.started_at: Optional[datetime] = None
        self.outputs_summary: Optional[str] = None
        self.status = "running"
        self.error: Optional[str] = None

    def __enter__(self) -> "TraceScope":
        context = current_trace_context()
        trace_id = context["trace_id"] or f"trace_{uuid4().hex[:16]}"
        task_id = context["task_id"] or "unknown"
        self.started_at = datetime.now(timezone.utc)
        span = TaskSpan(
            id=self.id,
            trace_id=trace_id,
            execution_id=context["execution_id"],
            task_id=task_id,
            client=context["client"],
            span=self.span,
            status=self.status,
            started_at=self.started_at,
            inputs=self.inputs,
            metadata=self.metadata,
        )
        self.db.create_span(span)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc is not None:
            self.status = "error"
            self.error = str(exc)
        elif self.status == "running":
            self.status = "ok"
        self.finish(status=self.status, error=self.error)
        return False

    def set_output(self, output: Any, *, max_length: int = 500) -> None:
        """Set a safe output summary for the span."""
        self.outputs_summary = summarize_output(output, max_length=max_length)

    def add_metadata(self, **metadata: Any) -> None:
        """Merge metadata into the span."""
        merged = dict(self.metadata)
        merged.update(redact_value(metadata))
        self.metadata = merged

    def fail(self, error: str) -> None:
        """Mark span as failed without raising."""
        self.status = "error"
        self.error = redact_value(error)

    def finish(
        self,
        *,
        status: Optional[str] = None,
        output: Any = None,
        outputs_summary: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Finalize the span record."""
        if self.started_at is None:
            return
        ended_at = datetime.now(timezone.utc)
        duration_ms = int((ended_at - self.started_at).total_seconds() * 1000)
        if output is not None:
            self.set_output(output)
        if outputs_summary is not None:
            self.outputs_summary = redact_value(outputs_summary)
        if error is not None:
            self.error = redact_value(error)
        if status is not None:
            self.status = status

        self.db.update_span(
            self.id,
            status=self.status,
            ended_at=ended_at,
            duration_ms=duration_ms,
            inputs=self.inputs,
            outputs_summary=self.outputs_summary,
            error=self.error,
            metadata=self.metadata,
        )


def trace_span(
    span: str,
    *,
    inputs: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[AgentDatabase] = None,
) -> TraceScope:
    """Create a trace span context manager."""
    return TraceScope(span, inputs=inputs, metadata=metadata, db=db)


def redact_value(value: Any, *, max_string: int = 1200) -> Any:
    """Redact sensitive values from nested structures."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_str = str(key)
            key_lower = key_str.lower()
            if key_lower in {"token_usage", "prompt_tokens", "completion_tokens", "total_tokens"}:
                redacted[key_str] = redact_value(item, max_string=max_string)
            elif SENSITIVE_KEY_RE.search(key_str):
                redacted[key_str] = "<redacted>"
            else:
                redacted[key_str] = redact_value(item, max_string=max_string)
        return redacted
    if isinstance(value, list):
        return [redact_value(item, max_string=max_string) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item, max_string=max_string) for item in value]
    if isinstance(value, str):
        text = TOKEN_RE.sub(lambda m: f"{m.group(1) or ''}<redacted-token>", value)
        text = EMAIL_RE.sub("<redacted-email>", text)
        text = PHONE_RE.sub("<redacted-phone>", text)
        text = URL_TOKEN_RE.sub(lambda m: f"{m.group(1)}=<redacted>", text)
        if len(text) > max_string:
            text = f"{text[:max_string]}...<truncated>"
        return text
    return value


def summarize_output(output: Any, *, max_length: int = 500) -> str:
    """Summarize output without storing raw payloads."""
    output = redact_value(output, max_string=max_length)
    if output is None:
        return ""
    if isinstance(output, dict):
        for key in ("summary", "message", "status", "verdict"):
            if output.get(key):
                return str(output[key])[:max_length]
        text = json.dumps(output, default=str, sort_keys=True)
        return text[:max_length]
    if isinstance(output, list):
        return f"list[{len(output)}]: {json.dumps(output[:3], default=str)[:max_length]}"
    return str(output)[:max_length]


def export_span_json(span: TaskSpan) -> str:
    """Serialize a TaskSpan as one HALO-friendly JSONL line."""
    payload = {
        "trace_id": span.trace_id,
        "span_id": span.id,
        "execution_id": span.execution_id,
        "task_id": span.task_id,
        "client": span.client,
        "span": span.span,
        "status": span.status,
        "started_at": span.started_at.isoformat(),
        "ended_at": span.ended_at.isoformat() if span.ended_at else None,
        "duration_ms": span.duration_ms,
        "inputs": redact_value(span.inputs),
        "outputs_summary": redact_value(span.outputs_summary),
        "error": redact_value(span.error),
        "metadata": redact_value(span.metadata),
    }
    return json.dumps(payload, default=str, sort_keys=True)


def parse_since(value: Optional[str]) -> Optional[datetime]:
    """Parse values like 7d, 24h, 30m, or an ISO timestamp."""
    if not value:
        return None
    text = value.strip().lower()
    now = datetime.now(timezone.utc)
    match = re.fullmatch(r"(\d+)([dhm])", text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == "d":
            return now - timedelta(days=amount)
        if unit == "h":
            return now - timedelta(hours=amount)
        return now - timedelta(minutes=amount)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed

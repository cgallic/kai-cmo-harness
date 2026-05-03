"""
Tracer: ergonomic span context managers with implicit propagation.

The tracer captures structured span data via async context managers,
propagates the current trace through `contextvars` so deeply-nested
helpers can attach LLM/external/transform spans without threading a
tracer argument through every call, and writes spans to the trace
store at span exit.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, Optional
from uuid import uuid4

from .models import (
    QualityLabel,
    SpanKind,
    SpanStatus,
    TraceSpan,
    trace_store,
)
from .redact import redact, summarize_output


# Active trace + parent span context. Used so handlers/helpers can open
# child spans without explicitly being passed a tracer instance.
_current_trace_id: ContextVar[Optional[str]] = ContextVar(
    "_current_trace_id", default=None
)
_current_parent_span_id: ContextVar[Optional[str]] = ContextVar(
    "_current_parent_span_id", default=None
)
_current_task_id: ContextVar[Optional[str]] = ContextVar(
    "_current_task_id", default=None
)
_current_execution_id: ContextVar[Optional[str]] = ContextVar(
    "_current_execution_id", default=None
)
_current_client: ContextVar[Optional[str]] = ContextVar(
    "_current_client", default=None
)


def current_trace_id() -> Optional[str]:
    """Return the active trace ID, or None outside a trace."""
    return _current_trace_id.get()


class Span:
    """
    A live span. Use as an async context manager:

        async with tracer.span("fetch_metrics", kind=SpanKind.EXTERNAL_API) as s:
            data = await api.get(...)
            s.add_attributes(rows=len(data))
            s.set_output(data)

    Attributes accumulate freely; output summary is short-form by
    default and is run through redaction before persistence.
    """

    def __init__(
        self,
        *,
        name: str,
        kind: SpanKind = SpanKind.OTHER,
        trace_id: str,
        parent_span_id: Optional[str],
        task_id: Optional[str],
        execution_id: Optional[str],
        client: Optional[str],
        inputs: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.span_id = uuid4().hex[:16]
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.task_id = task_id
        self.execution_id = execution_id
        self.client = client
        self.name = name
        self.kind = kind
        self.inputs: Dict[str, Any] = redact(inputs or {})
        self.attributes: Dict[str, Any] = dict(attributes or {})
        self.outputs_summary: Optional[str] = None
        self.status: SpanStatus = SpanStatus.OK
        self.error: Optional[str] = None
        self.started_at: datetime = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self._t0 = time.monotonic()
        self._closed = False

    # -- mutation API used inside the `with` block ---------------------
    def add_attributes(self, **kwargs: Any) -> None:
        """Add structured metadata (e.g. row counts, status codes)."""
        self.attributes.update(redact(kwargs))

    def set_output(self, value: Any) -> None:
        """Record a redaction-safe summary of the span's output."""
        self.outputs_summary = summarize_output(value)

    def set_status(self, status: SpanStatus) -> None:
        self.status = status

    # -- finalization --------------------------------------------------
    def _finalize(self, *, error: Optional[BaseException] = None) -> None:
        if self._closed:
            return
        self._closed = True

        self.completed_at = datetime.utcnow()
        duration_ms = int((time.monotonic() - self._t0) * 1000)

        if error is not None:
            self.status = SpanStatus.ERROR
            self.error = redact(f"{type(error).__name__}: {error}")

        span = TraceSpan(
            span_id=self.span_id,
            trace_id=self.trace_id,
            parent_span_id=self.parent_span_id,
            task_id=self.task_id,
            execution_id=self.execution_id,
            client=self.client,
            name=self.name,
            kind=self.kind,
            status=self.status,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration_ms=duration_ms,
            inputs=self.inputs,
            outputs_summary=self.outputs_summary,
            attributes=self.attributes,
            error=self.error,
        )
        try:
            trace_store.save_span(span)
        except Exception as exc:  # pragma: no cover - storage best-effort
            # Tracing must never take down the agent loop.
            print(f"[traces] failed to persist span {self.name}: {exc}")


class _TraceHandle:
    """
    Returned by `tracer.trace(...)`. Exposes `.span()` so handlers can
    open child spans that inherit task/client metadata automatically.
    """

    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def span(self, name: str, *, kind: SpanKind = SpanKind.OTHER, **kwargs: Any):
        return tracer.span(name, kind=kind, **kwargs)

    def label(
        self,
        label: QualityLabel,
        *,
        note: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        """Attach a downstream usefulness label to this trace."""
        trace_store.record_quality(self.trace_id, label, note=note, source=source)


class Tracer:
    """
    Front-end facade that opens traces and child spans against the
    process-global trace store.
    """

    @asynccontextmanager
    async def trace(
        self,
        *,
        task_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        client: Optional[str] = None,
        trace_id: Optional[str] = None,
        root_span_name: str = "task",
        root_span_kind: SpanKind = SpanKind.TASK,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[_TraceHandle]:
        """
        Open a new trace with a root span.

        The root span captures the task-level start/end so HALO has a
        single record per execution to cluster against.
        """
        tid = trace_id or uuid4().hex
        token_trace = _current_trace_id.set(tid)
        token_task = _current_task_id.set(task_id)
        token_exec = _current_execution_id.set(execution_id)
        token_client = _current_client.set(client)

        root = Span(
            name=root_span_name,
            kind=root_span_kind,
            trace_id=tid,
            parent_span_id=None,
            task_id=task_id,
            execution_id=execution_id,
            client=client,
            inputs=inputs,
        )
        token_parent = _current_parent_span_id.set(root.span_id)

        try:
            yield _TraceHandle(tid)
            root._finalize()
        except BaseException as exc:
            root._finalize(error=exc)
            raise
        finally:
            _current_parent_span_id.reset(token_parent)
            _current_client.reset(token_client)
            _current_execution_id.reset(token_exec)
            _current_task_id.reset(token_task)
            _current_trace_id.reset(token_trace)

    @asynccontextmanager
    async def span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.OTHER,
        inputs: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Span]:
        """
        Open a child span under the active trace. If no trace is active
        the span is created with a synthetic trace ID so callers don't
        need conditional code paths during partial rollouts.
        """
        trace_id = _current_trace_id.get() or uuid4().hex
        parent = _current_parent_span_id.get()

        s = Span(
            name=name,
            kind=kind,
            trace_id=trace_id,
            parent_span_id=parent,
            task_id=_current_task_id.get(),
            execution_id=_current_execution_id.get(),
            client=_current_client.get(),
            inputs=inputs,
            attributes=attributes,
        )
        token_parent = _current_parent_span_id.set(s.span_id)
        try:
            yield s
            s._finalize()
        except BaseException as exc:
            s._finalize(error=exc)
            raise
        finally:
            _current_parent_span_id.reset(token_parent)

    @contextmanager
    def sync_span(
        self,
        name: str,
        *,
        kind: SpanKind = SpanKind.OTHER,
        inputs: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Iterator[Span]:
        """Sync variant for non-async code paths (CLI tools, scripts)."""
        trace_id = _current_trace_id.get() or uuid4().hex
        parent = _current_parent_span_id.get()

        s = Span(
            name=name,
            kind=kind,
            trace_id=trace_id,
            parent_span_id=parent,
            task_id=_current_task_id.get(),
            execution_id=_current_execution_id.get(),
            client=_current_client.get(),
            inputs=inputs,
            attributes=attributes,
        )
        token_parent = _current_parent_span_id.set(s.span_id)
        try:
            yield s
            s._finalize()
        except BaseException as exc:
            s._finalize(error=exc)
            raise
        finally:
            _current_parent_span_id.reset(token_parent)


# Global tracer instance.
tracer = Tracer()

"""
Trace span model and SQLite-backed trace store.

A trace is the full execution of one scheduled task; spans are the
individual operations inside it (scheduler decisions, external API
fetches, LLM calls, transforms, synthesis, notifications, retries).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from ..config import agent_config


class SpanKind(str, Enum):
    """The kind of operation a span represents."""

    SCHEDULER = "scheduler"
    TASK = "task"
    EXTERNAL_API = "external_api"
    LLM = "llm"
    TRANSFORM = "transform"
    SYNTHESIS = "synthesis"
    NOTIFICATION = "notification"
    RETRY = "retry"
    OTHER = "other"


class SpanStatus(str, Enum):
    """Final status of a span."""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class QualityLabel(str, Enum):
    """
    Downstream usefulness signals for a trace.

    These are recorded after the fact (e.g. by Connor reacting to a
    Discord report, or by an automated useful/noisy classifier) and let
    HALO optimize for business value, not just successful execution.
    """

    SENT = "sent"
    IGNORED = "ignored"
    USEFUL = "useful"
    NOISY = "noisy"
    WRONG = "wrong"
    ACTION_TAKEN = "action_taken"


class TraceSpan(BaseModel):
    """A single span inside a trace."""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    task_id: Optional[str] = None
    execution_id: Optional[str] = None
    client: Optional[str] = None
    name: str
    kind: SpanKind = SpanKind.OTHER
    status: SpanStatus = SpanStatus.OK
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs_summary: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    def to_halo_dict(self) -> Dict[str, Any]:
        """Render as HALO-compatible JSONL row."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "client": self.client,
            "name": self.name,
            "kind": self.kind.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "inputs": self.inputs,
            "outputs_summary": self.outputs_summary,
            "attributes": self.attributes,
            "error": self.error,
        }


class TraceStore:
    """
    SQLite-backed store for trace spans and quality labels.

    Reuses the agent database file so that traces, executions, and
    scheduled tasks live alongside each other and can be cross-joined
    during diagnosis.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or agent_config.db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            self._move_incompatible_legacy_table(conn)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    task_id TEXT,
                    execution_id TEXT,
                    client TEXT,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_ms INTEGER,
                    inputs TEXT,
                    outputs_summary TEXT,
                    attributes TEXT,
                    error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trace_quality (
                    trace_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    note TEXT,
                    source TEXT,
                    recorded_at TEXT NOT NULL,
                    PRIMARY KEY (trace_id, label)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_trace ON task_spans(trace_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_task ON task_spans(task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_started ON task_spans(started_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_status ON task_spans(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_kind ON task_spans(kind)"
            )
            conn.commit()

    @staticmethod
    def _move_incompatible_legacy_table(conn: sqlite3.Connection) -> None:
        existing = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'task_spans'"
        ).fetchone()
        if not existing:
            return

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(task_spans)").fetchall()
        }
        required = {"span_id", "trace_id", "name", "kind", "status", "started_at"}
        if required.issubset(columns):
            return

        suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        legacy_name = f"task_spans_legacy_{suffix}"
        for index_name in (
            "idx_spans_trace",
            "idx_spans_task",
            "idx_spans_started",
            "idx_spans_status",
            "idx_spans_kind",
        ):
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")
        conn.execute(f"ALTER TABLE task_spans RENAME TO {legacy_name}")

    # ------------------------------------------------------------------
    # Span persistence
    # ------------------------------------------------------------------
    def save_span(self, span: TraceSpan) -> None:
        """Insert or replace a span (idempotent on span_id)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO task_spans
                (span_id, trace_id, parent_span_id, task_id, execution_id, client,
                 name, kind, status, started_at, completed_at, duration_ms,
                 inputs, outputs_summary, attributes, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span.span_id,
                    span.trace_id,
                    span.parent_span_id,
                    span.task_id,
                    span.execution_id,
                    span.client,
                    span.name,
                    span.kind.value,
                    span.status.value,
                    span.started_at.isoformat(),
                    span.completed_at.isoformat() if span.completed_at else None,
                    span.duration_ms,
                    json.dumps(span.inputs, default=str),
                    span.outputs_summary,
                    json.dumps(span.attributes, default=str),
                    span.error,
                ),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------
    def list_spans(
        self,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        task_id: Optional[str] = None,
        client: Optional[str] = None,
        status: Optional[SpanStatus] = None,
        limit: Optional[int] = None,
    ) -> List[TraceSpan]:
        clauses: List[str] = []
        params: List[Any] = []

        if since is not None:
            clauses.append("started_at >= ?")
            params.append(since.isoformat())
        if until is not None:
            clauses.append("started_at <= ?")
            params.append(until.isoformat())
        if task_id is not None:
            clauses.append("task_id = ?")
            params.append(task_id)
        if client is not None:
            clauses.append("client = ?")
            params.append(client)
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM task_spans {where} ORDER BY started_at ASC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        return [_row_to_span(row) for row in rows]

    def iter_spans(
        self,
        *,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> Iterable[TraceSpan]:
        # Streamed read for export over large windows.
        for span in self.list_spans(since=since, until=until):
            yield span

    def get_trace(self, trace_id: str) -> List[TraceSpan]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM task_spans WHERE trace_id = ? ORDER BY started_at ASC",
                (trace_id,),
            ).fetchall()
        return [_row_to_span(row) for row in rows]

    # ------------------------------------------------------------------
    # Quality labels
    # ------------------------------------------------------------------
    def record_quality(
        self,
        trace_id: str,
        label: QualityLabel,
        *,
        note: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trace_quality
                (trace_id, label, note, source, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    trace_id,
                    label.value,
                    note,
                    source,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def get_quality(self, trace_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT label, note, source, recorded_at FROM trace_quality WHERE trace_id = ?",
                (trace_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------
    def cleanup(self, *, older_than_days: int = 60) -> int:
        cutoff = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM task_spans WHERE started_at < ?", (cutoff,)
            )
            conn.execute(
                "DELETE FROM trace_quality WHERE recorded_at < ?", (cutoff,)
            )
            conn.commit()
            return cur.rowcount or 0


def _row_to_span(row: sqlite3.Row) -> TraceSpan:
    return TraceSpan(
        span_id=row["span_id"],
        trace_id=row["trace_id"],
        parent_span_id=row["parent_span_id"],
        task_id=row["task_id"],
        execution_id=row["execution_id"],
        client=row["client"],
        name=row["name"],
        kind=SpanKind(row["kind"]),
        status=SpanStatus(row["status"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=(
            datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        ),
        duration_ms=row["duration_ms"],
        inputs=json.loads(row["inputs"]) if row["inputs"] else {},
        outputs_summary=row["outputs_summary"],
        attributes=json.loads(row["attributes"]) if row["attributes"] else {},
        error=row["error"],
    )


# Global trace store instance.
trace_store = TraceStore()

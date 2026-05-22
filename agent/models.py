"""
Database models and Pydantic schemas for the autonomous agent.
"""

import json
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .config import agent_config
from kai.runtime.models import TaskNode, TaskGraph


TASK_SPAN_RECORDS_TABLE = "task_span_records"


# =============================================================================
# Enums
# =============================================================================

class TaskStatus(str, Enum):
    """Status of a scheduled task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"


class MessageType(str, Enum):
    """Type of conversation message."""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    SYSTEM = "system"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Pydantic Models - Scheduled Tasks
# =============================================================================

class ScheduledTaskConfig(BaseModel):
    """Configuration stored with a scheduled task."""
    model: Optional[str] = None  # Override default model
    timeout: Optional[int] = None  # Override default timeout
    retry_on_failure: bool = True
    requires_approval: bool = False
    notify_on_complete: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)


class ScheduledTask(BaseModel):
    """A scheduled task definition."""
    id: str
    name: str
    cron_expression: str  # "0 8 * * *" = 8 AM daily
    task_type: str  # e.g., "daily_analytics", "content_pipeline"
    client: Optional[str] = None
    config: ScheduledTaskConfig = Field(default_factory=ScheduledTaskConfig)
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskExecution(BaseModel):
    """Record of a task execution."""
    id: str
    task_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0


class TaskSpan(BaseModel):
    """Structured span emitted during a task execution."""
    id: str
    trace_id: str
    task_id: str
    span: str
    status: str = "running"
    started_at: datetime
    execution_id: Optional[str] = None
    client: Optional[str] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs_summary: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Pydantic Models - Conversations
# =============================================================================

class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    id: int
    channel: str  # "whatsapp", "telegram", etc.
    phone_number: str
    message_type: MessageType
    content: str
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Conversation state and context."""
    current_command: Optional[str] = None
    awaiting_response: bool = False
    pending_approval_id: Optional[str] = None
    last_client: Optional[str] = None
    session_data: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Pydantic Models - Agent State
# =============================================================================

class AgentState(BaseModel):
    """Global agent state."""
    paused: bool = False
    last_activity: Optional[datetime] = None
    current_tasks: List[str] = Field(default_factory=list)
    stats: Dict[str, int] = Field(default_factory=dict)


# =============================================================================
# Database Manager
# =============================================================================

class AgentDatabase:
    """SQLite database manager for the agent."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or agent_config.db_path
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        """Create a database connection with WAL mode and busy timeout enabled."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self.connect() as conn:
            # Scheduled tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    cron_expression TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    client TEXT,
                    config TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run_at TEXT,
                    next_run_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Task executions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_executions (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
                )
            """)

            # Lightweight recorder spans. The HALO trace store owns task_spans.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_span_records (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    execution_id TEXT,
                    task_id TEXT NOT NULL,
                    client TEXT,
                    span TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_ms INTEGER,
                    inputs TEXT,
                    outputs_summary TEXT,
                    error TEXT,
                    metadata TEXT
                )
            """)

            # Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Agent state table (key-value store)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

            # Task graphs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_graphs (
                    graph_id TEXT PRIMARY KEY,
                    goal_id TEXT,
                    brand_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    edges TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Task nodes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_nodes (
                    graph_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    inputs TEXT,
                    outputs TEXT,
                    error TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    PRIMARY KEY (graph_id, node_id),
                    FOREIGN KEY (graph_id) REFERENCES task_graphs(graph_id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_enabled
                ON scheduled_tasks(enabled)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_next_run
                ON scheduled_tasks(next_run_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_task
                ON task_executions(task_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_executions_status
                ON task_executions(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_span_records_trace
                ON task_span_records(trace_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_span_records_execution
                ON task_span_records(execution_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_span_records_task
                ON task_span_records(task_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_span_records_started
                ON task_span_records(started_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_phone
                ON conversations(phone_number)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_channel
                ON conversations(channel)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_graphs_status
                ON task_graphs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_nodes_status
                ON task_nodes(status)
            """)

            conn.commit()

    # -------------------------------------------------------------------------
    # JSON Helpers
    # -------------------------------------------------------------------------
    def _to_json(self, data: Any) -> Optional[str]:
        if data is None:
            return None
        if isinstance(data, BaseModel):
            return data.model_dump_json()
        return json.dumps(data, default=str)

    def _from_json(self, data: Optional[str]) -> Any:
        if data is None:
            return None
        return json.loads(data)

    # -------------------------------------------------------------------------
    # Scheduled Tasks CRUD
    # -------------------------------------------------------------------------
    def create_scheduled_task(self, task: ScheduledTask) -> str:
        """Create a new scheduled task."""
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO scheduled_tasks
                (id, name, cron_expression, task_type, client, config, enabled,
                 last_run_at, next_run_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.name,
                task.cron_expression,
                task.task_type,
                task.client,
                self._to_json(task.config),
                1 if task.enabled else 0,
                task.last_run_at.isoformat() if task.last_run_at else None,
                task.next_run_at.isoformat() if task.next_run_at else None,
                task.created_at.isoformat()
            ))
            conn.commit()
        return task.id

    def get_scheduled_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a scheduled task by ID."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM scheduled_tasks WHERE id = ?",
                (task_id,)
            ).fetchone()

        if not row:
            return None

        return self._row_to_scheduled_task(row)

    def list_scheduled_tasks(
        self,
        enabled_only: bool = True,
        client: Optional[str] = None
    ) -> List[ScheduledTask]:
        """List scheduled tasks."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM scheduled_tasks WHERE 1=1"
            params = []

            if enabled_only:
                query += " AND enabled = 1"
            if client:
                query += " AND client = ?"
                params.append(client)

            query += " ORDER BY next_run_at ASC"
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_scheduled_task(row) for row in rows]

    def update_scheduled_task(
        self,
        task_id: str,
        enabled: Optional[bool] = None,
        last_run_at: Optional[datetime] = None,
        next_run_at: Optional[datetime] = None,
        config: Optional[ScheduledTaskConfig] = None
    ):
        """Update a scheduled task."""
        updates = []
        params = []

        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if last_run_at is not None:
            updates.append("last_run_at = ?")
            params.append(last_run_at.isoformat())
        if next_run_at is not None:
            updates.append("next_run_at = ?")
            params.append(next_run_at.isoformat())
        if config is not None:
            updates.append("config = ?")
            params.append(self._to_json(config))

        if not updates:
            return

        params.append(task_id)

        with self.connect() as conn:
            conn.execute(
                f"UPDATE scheduled_tasks SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

    def delete_scheduled_task(self, task_id: str):
        """Delete a scheduled task."""
        with self.connect() as conn:
            conn.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
            conn.commit()

    def _row_to_scheduled_task(self, row: sqlite3.Row) -> ScheduledTask:
        """Convert a database row to a ScheduledTask."""
        config_data = self._from_json(row["config"])
        config = ScheduledTaskConfig(**config_data) if config_data else ScheduledTaskConfig()

        return ScheduledTask(
            id=row["id"],
            name=row["name"],
            cron_expression=row["cron_expression"],
            task_type=row["task_type"],
            client=row["client"],
            config=config,
            enabled=bool(row["enabled"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
            next_run_at=datetime.fromisoformat(row["next_run_at"]) if row["next_run_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"])
        )

    # -------------------------------------------------------------------------
    # Task Executions CRUD
    # -------------------------------------------------------------------------
    def create_execution(self, execution: TaskExecution) -> str:
        """Create a new task execution record."""
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO task_executions
                (id, task_id, status, started_at, completed_at, result, error, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution.id,
                execution.task_id,
                execution.status.value,
                execution.started_at.isoformat(),
                execution.completed_at.isoformat() if execution.completed_at else None,
                self._to_json(execution.result),
                execution.error,
                execution.retry_count
            ))
            conn.commit()
        return execution.id

    def update_execution(
        self,
        execution_id: str,
        status: Optional[TaskStatus] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        retry_count: Optional[int] = None
    ):
        """Update a task execution record."""
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())
        if result is not None:
            updates.append("result = ?")
            params.append(self._to_json(result))
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        if retry_count is not None:
            updates.append("retry_count = ?")
            params.append(retry_count)

        if not updates:
            return

        params.append(execution_id)

        with self.connect() as conn:
            conn.execute(
                f"UPDATE task_executions SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

    def get_recent_executions(
        self,
        task_id: Optional[str] = None,
        limit: int = 50
    ) -> List[TaskExecution]:
        """Get recent task executions."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row

            if task_id:
                rows = conn.execute("""
                    SELECT * FROM task_executions
                    WHERE task_id = ?
                    ORDER BY started_at DESC LIMIT ?
                """, (task_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM task_executions
                    ORDER BY started_at DESC LIMIT ?
                """, (limit,)).fetchall()

        return [
            TaskExecution(
                id=row["id"],
                task_id=row["task_id"],
                status=TaskStatus(row["status"]),
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                result=self._from_json(row["result"]),
                error=row["error"],
                retry_count=row["retry_count"]
            )
            for row in rows
        ]

    # -------------------------------------------------------------------------
    # Task Spans CRUD
    # -------------------------------------------------------------------------
    def create_span(self, span: TaskSpan) -> str:
        """Create a new trace span record."""
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO task_span_records
                (id, trace_id, execution_id, task_id, client, span, status,
                 started_at, ended_at, duration_ms, inputs, outputs_summary,
                 error, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                span.id,
                span.trace_id,
                span.execution_id,
                span.task_id,
                span.client,
                span.span,
                span.status,
                span.started_at.isoformat(),
                span.ended_at.isoformat() if span.ended_at else None,
                span.duration_ms,
                self._to_json(span.inputs),
                span.outputs_summary,
                span.error,
                self._to_json(span.metadata),
            ))
            conn.commit()
        return span.id

    def update_span(
        self,
        span_id: str,
        *,
        status: Optional[str] = None,
        ended_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        inputs: Optional[Dict[str, Any]] = None,
        outputs_summary: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update a trace span record."""
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if ended_at is not None:
            updates.append("ended_at = ?")
            params.append(ended_at.isoformat())
        if duration_ms is not None:
            updates.append("duration_ms = ?")
            params.append(duration_ms)
        if inputs is not None:
            updates.append("inputs = ?")
            params.append(self._to_json(inputs))
        if outputs_summary is not None:
            updates.append("outputs_summary = ?")
            params.append(outputs_summary)
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(self._to_json(metadata))

        if not updates:
            return

        params.append(span_id)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE {TASK_SPAN_RECORDS_TABLE} SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

    def list_spans(
        self,
        *,
        since: Optional[datetime] = None,
        task_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        client: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000,
    ) -> List[TaskSpan]:
        """List trace spans with optional filters."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            query = f"SELECT * FROM {TASK_SPAN_RECORDS_TABLE} WHERE 1=1"
            params: List[Any] = []

            if since is not None:
                query += " AND started_at >= ?"
                params.append(since.isoformat())
            if task_id is not None:
                query += " AND task_id = ?"
                params.append(task_id)
            if trace_id is not None:
                query += " AND trace_id = ?"
                params.append(trace_id)
            if execution_id is not None:
                query += " AND execution_id = ?"
                params.append(execution_id)
            if client is not None:
                query += " AND client = ?"
                params.append(client)
            if status is not None:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY started_at ASC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_task_span(row) for row in rows]

    def _row_to_task_span(self, row: sqlite3.Row) -> TaskSpan:
        """Convert a database row to a TaskSpan."""
        return TaskSpan(
            id=row["id"],
            trace_id=row["trace_id"],
            execution_id=row["execution_id"],
            task_id=row["task_id"],
            client=row["client"],
            span=row["span"],
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            duration_ms=row["duration_ms"],
            inputs=self._from_json(row["inputs"]) or {},
            outputs_summary=row["outputs_summary"],
            error=row["error"],
            metadata=self._from_json(row["metadata"]) or {},
        )

    # -------------------------------------------------------------------------
    # Conversations CRUD
    # -------------------------------------------------------------------------
    def save_message(self, message: ConversationMessage) -> int:
        """Save a conversation message."""
        with self.connect() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations
                (channel, phone_number, message_type, content, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                message.channel,
                message.phone_number,
                message.message_type.value,
                message.content,
                self._to_json(message.context),
                message.created_at.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(
        self,
        phone_number: str,
        channel: str = "whatsapp",
        limit: int = 20
    ) -> List[ConversationMessage]:
        """Get recent conversation history for a phone number."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM conversations
                WHERE phone_number = ? AND channel = ?
                ORDER BY created_at DESC LIMIT ?
            """, (phone_number, channel, limit)).fetchall()

        return [
            ConversationMessage(
                id=row["id"],
                channel=row["channel"],
                phone_number=row["phone_number"],
                message_type=MessageType(row["message_type"]),
                content=row["content"],
                context=self._from_json(row["context"]) or {},
                created_at=datetime.fromisoformat(row["created_at"])
            )
            for row in reversed(rows)  # Return in chronological order
        ]

    # -------------------------------------------------------------------------
    # Agent State CRUD
    # -------------------------------------------------------------------------
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value by key."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT value FROM agent_state WHERE key = ?",
                (key,)
            ).fetchone()

        if not row:
            return default
        return self._from_json(row["value"])

    def set_state(self, key: str, value: Any):
        """Set a state value."""
        with self.connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO agent_state (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, self._to_json(value), datetime.utcnow().isoformat()))
            conn.commit()

    def delete_state(self, key: str):
        """Delete a state value."""
        with self.connect() as conn:
            conn.execute("DELETE FROM agent_state WHERE key = ?", (key,))
            conn.commit()

    def get_all_state(self) -> Dict[str, Any]:
        """Get all state values."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT key, value FROM agent_state").fetchall()

        return {row["key"]: self._from_json(row["value"]) for row in rows}

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------
    def cleanup_old_records(self, days: int = 30):
        """Clean up old execution records and conversations."""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self.connect() as conn:
            conn.execute(
                "DELETE FROM task_executions WHERE started_at < ?",
                (cutoff,)
            )
            conn.execute(
                f"DELETE FROM {TASK_SPAN_RECORDS_TABLE} WHERE started_at < ?",
                (cutoff,)
            )
            conn.execute(
                "DELETE FROM conversations WHERE created_at < ?",
                (cutoff,)
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Task Graphs and Nodes CRUD
    # -------------------------------------------------------------------------
    def create_task_graph(self, graph: TaskGraph) -> str:
        """Create and persist a new task graph and its nodes."""
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO task_graphs (graph_id, goal_id, brand_id, status, edges, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                graph.graph_id,
                graph.goal_id,
                graph.brand_id,
                graph.status,
                self._to_json(graph.edges),
                graph.created_at,
                graph.updated_at
            ))
            for node_id, node in graph.nodes.items():
                conn.execute("""
                    INSERT INTO task_nodes (graph_id, node_id, task_type, status, inputs, outputs, error, started_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    graph.graph_id,
                    node.node_id,
                    node.task_type,
                    node.status,
                    self._to_json(node.inputs),
                    self._to_json(node.outputs),
                    node.error,
                    node.started_at,
                    node.completed_at
                ))
            conn.commit()
        return graph.graph_id

    def get_task_graph(self, graph_id: str) -> Optional[TaskGraph]:
        """Retrieve a task graph and its nodes by ID."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM task_graphs WHERE graph_id = ?", (graph_id,)).fetchone()
            if not row:
                return None
            
            nodes = self.get_task_nodes(graph_id)
            edges = self._from_json(row["edges"]) or []
            
            return TaskGraph(
                graph_id=row["graph_id"],
                goal_id=row["goal_id"],
                brand_id=row["brand_id"],
                status=row["status"],  # type: ignore
                nodes=nodes,
                edges=edges,
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def update_task_graph_status(self, graph_id: str, status: str):
        """Update the status of a task graph."""
        with self.connect() as conn:
            conn.execute("""
                UPDATE task_graphs 
                SET status = ?, updated_at = ? 
                WHERE graph_id = ?
            """, (status, datetime.utcnow().isoformat(), graph_id))
            conn.commit()

    def update_task_node(
        self,
        graph_id: str,
        node_id: str,
        status: str,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ):
        """Update a task node's execution progress."""
        updates = ["status = ?"]
        params: List[Any] = [status]
        
        if outputs is not None:
            updates.append("outputs = ?")
            params.append(self._to_json(outputs))
        if error is not None:
            updates.append("error = ?")
            params.append(error)
        if started_at is not None:
            updates.append("started_at = ?")
            params.append(started_at.isoformat())
        if completed_at is not None:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())
            
        params.extend([graph_id, node_id])
        with self.connect() as conn:
            conn.execute(
                f"UPDATE task_nodes SET {', '.join(updates)} WHERE graph_id = ? AND node_id = ?",
                params
            )
            conn.commit()

    def list_active_task_graphs(self) -> List[TaskGraph]:
        """List active task graphs (status pending or running)."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT graph_id FROM task_graphs WHERE status IN ('pending', 'running') ORDER BY created_at ASC"
            ).fetchall()
            
        graphs = []
        for r in rows:
            g = self.get_task_graph(r["graph_id"])
            if g:
                graphs.append(g)
        return graphs

    def get_task_nodes(self, graph_id: str) -> Dict[str, TaskNode]:
        """Get all nodes for a specific graph."""
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM task_nodes WHERE graph_id = ?", (graph_id,)).fetchall()
            
        nodes = {}
        for row in rows:
            nodes[row["node_id"]] = TaskNode(
                node_id=row["node_id"],
                task_type=row["task_type"],
                status=row["status"],  # type: ignore
                inputs=self._from_json(row["inputs"]) or {},
                outputs=self._from_json(row["outputs"]) or {},
                error=row["error"],
                started_at=row["started_at"],
                completed_at=row["completed_at"]
            )
        return nodes


# Global database instance
agent_db = AgentDatabase()

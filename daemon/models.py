"""Pydantic models for daemon communication."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RuntimeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DRAINING = "draining"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(str, Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    ERROR = "error"
    STATUS = "status"


class Runtime(BaseModel):
    """A registered daemon runtime."""
    name: str
    cmd: str
    version: str = ""
    capabilities: List[str] = Field(default_factory=lambda: [
        "content-gen", "audit", "analysis", "code-gen",
    ])


class AgentTask(BaseModel):
    """A task claimed from Supabase."""
    id: str
    brand_id: str
    task_type: str
    skill: Optional[str] = None
    trigger: str = "daemon"
    status: str = "pending"
    input: Optional[Dict[str, Any]] = None
    risk_tier: str = "low"
    prior_session_id: Optional[str] = None
    schedule_id: Optional[str] = None


class AgentMessage(BaseModel):
    """A single message in the execution transcript."""
    run_id: str
    brand_id: str
    seq: int
    msg_type: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result of a completed task."""
    status: TaskStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    work_dir: Optional[str] = None
    cost_usd: float = 0.0
    num_turns: int = 0

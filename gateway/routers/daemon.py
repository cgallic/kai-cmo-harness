"""Daemon API router — endpoints for the MeetKai daemon process.

The daemon communicates with the gateway for:
- Runtime registration and heartbeat
- Task messages (execution transcript streaming)
- Schedule management

Task claiming and lifecycle updates go directly to Supabase
via the daemon's service_role client. These endpoints handle
the parts that benefit from gateway-mediated access.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# ---------------------------------------------------------------------------
# Supabase client (lazy init, service_role key)
# ---------------------------------------------------------------------------

_supabase = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
            _supabase = create_client(url, key)
        except ImportError:
            raise HTTPException(500, "supabase-py not installed")
    return _supabase


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    daemon_id: str
    name: str
    host_info: Dict[str, Any] = {}


class RegisterResponse(BaseModel):
    runtime_id: str
    status: str = "online"


class HeartbeatResponse(BaseModel):
    ok: bool = True
    commands: List[str] = []  # Future: drain, shutdown


class MessageBatch(BaseModel):
    messages: List[Dict[str, Any]]


class TaskCompleteRequest(BaseModel):
    output: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    work_dir: Optional[str] = None


class TaskFailRequest(BaseModel):
    error: str


class CreateTaskRequest(BaseModel):
    brand_id: str
    task_type: str
    skill: Optional[str] = None
    trigger: str = "manual"
    input: Optional[Dict[str, Any]] = None
    risk_tier: str = "low"


# ---------------------------------------------------------------------------
# Runtime Registration
# ---------------------------------------------------------------------------

@router.post("/register", response_model=RegisterResponse)
async def register_runtime(req: RegisterRequest):
    """Register a daemon runtime. Upserts on daemon_id."""
    sb = _get_supabase()

    result = sb.table("runtimes").upsert({
        "daemon_id": req.daemon_id,
        "name": req.name,
        "host_info": req.host_info,
        "status": "online",
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="daemon_id").execute()

    if not result.data:
        raise HTTPException(500, "Failed to register runtime")

    return RegisterResponse(runtime_id=result.data[0]["id"])


@router.patch("/heartbeat/{runtime_id}", response_model=HeartbeatResponse)
async def heartbeat(runtime_id: str):
    """Update heartbeat timestamp for a runtime."""
    sb = _get_supabase()

    sb.table("runtimes").update({
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "status": "online",
    }).eq("id", runtime_id).execute()

    return HeartbeatResponse()


# ---------------------------------------------------------------------------
# Task Messages (execution transcript)
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/messages")
async def post_task_messages(task_id: str, batch: MessageBatch):
    """Batch insert execution transcript messages.

    The daemon streams these in real-time so the dashboard can show
    live progress via Supabase Realtime.
    """
    sb = _get_supabase()

    # Validate and insert
    rows = []
    for msg in batch.messages:
        rows.append({
            "run_id": task_id,
            "brand_id": msg.get("brand_id", ""),
            "seq": msg.get("seq", 0),
            "msg_type": msg.get("msg_type", "text"),
            "content": msg.get("content", ""),
            "metadata": msg.get("metadata", {}),
        })

    if rows:
        sb.table("agent_messages").insert(rows).execute()

    return {"inserted": len(rows)}


# ---------------------------------------------------------------------------
# Task Lifecycle
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, req: TaskCompleteRequest):
    """Mark a task as completed."""
    sb = _get_supabase()

    sb.table("agent_runs").update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "output": req.output,
        "session_id": req.session_id,
        "work_dir": req.work_dir,
    }).eq("id", task_id).execute()

    return {"status": "completed"}


@router.post("/tasks/{task_id}/fail")
async def fail_task(task_id: str, req: TaskFailRequest):
    """Mark a task as failed."""
    sb = _get_supabase()

    sb.table("agent_runs").update({
        "status": "failed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "error": req.error,
    }).eq("id", task_id).execute()

    return {"status": "failed"}


@router.post("/tasks/{task_id}/progress")
async def update_progress(task_id: str, progress: Dict[str, Any]):
    """Update task progress (step/total/summary)."""
    sb = _get_supabase()

    sb.table("agent_runs").update({
        "progress": progress,
    }).eq("id", task_id).execute()

    return {"ok": True}


# ---------------------------------------------------------------------------
# Task Creation (dashboard or API can queue tasks for daemon)
# ---------------------------------------------------------------------------

@router.post("/tasks/create")
async def create_task(req: CreateTaskRequest):
    """Create a new pending task for the daemon to pick up."""
    sb = _get_supabase()

    result = sb.table("agent_runs").insert({
        "brand_id": req.brand_id,
        "task_type": req.task_type,
        "skill": req.skill,
        "trigger": req.trigger,
        "status": "pending",
        "input": req.input,
        "risk_tier": req.risk_tier,
    }).execute()

    if not result.data:
        raise HTTPException(500, "Failed to create task")

    return {"task_id": result.data[0]["id"], "status": "pending"}


# ---------------------------------------------------------------------------
# Runtime Status
# ---------------------------------------------------------------------------

@router.get("/runtimes")
async def list_runtimes():
    """List all registered runtimes."""
    sb = _get_supabase()

    result = sb.table("runtimes").select("*").order(
        "last_heartbeat", desc=True
    ).execute()

    # Mark stale runtimes (no heartbeat in 60s)
    now = datetime.now(timezone.utc)
    runtimes = []
    for r in result.data or []:
        last_hb = r.get("last_heartbeat")
        if last_hb:
            from datetime import datetime as dt
            hb_time = dt.fromisoformat(last_hb.replace("Z", "+00:00"))
            stale = (now - hb_time).total_seconds() > 60
        else:
            stale = True

        runtimes.append({
            **r,
            "is_stale": stale,
        })

    return {"runtimes": runtimes}


@router.get("/tasks/pending")
async def list_pending_tasks():
    """List pending tasks waiting for daemon execution."""
    sb = _get_supabase()

    result = sb.table("agent_runs").select("*").eq(
        "status", "pending"
    ).is_("claimed_at", "null").order(
        "created_at", desc=False
    ).limit(20).execute()

    return {"tasks": result.data or [], "count": len(result.data or [])}

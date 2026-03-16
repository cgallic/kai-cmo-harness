"""
Agent management router for the CMO Gateway.

Provides endpoints for managing the autonomous agent.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.config import agent_config
from agent.models import agent_db
from agent.scheduler import scheduler
from agent.state import state_manager


router = APIRouter()


@router.get("/status")
async def get_agent_status():
    """
    Get the current agent status.

    Returns:
        Agent state including running status, current tasks, and statistics.
    """
    agent_state = state_manager.get_agent_state()

    return {
        "status": "paused" if agent_state.paused else "running",
        "last_activity": agent_state.last_activity.isoformat() if agent_state.last_activity else None,
        "current_tasks": agent_state.current_tasks,
        "statistics": agent_state.stats,
        "config": {
            "polling_interval": agent_config.polling_interval,
            "max_concurrent_tasks": agent_config.max_concurrent_tasks,
            "whatsapp_enabled": agent_config.whatsapp_enabled,
            "scheduler_enabled": agent_config.scheduler_enabled
        }
    }


@router.post("/pause")
async def pause_agent():
    """Pause the agent (stops scheduled task execution)."""
    state_manager.pause()
    return {"status": "paused", "message": "Agent paused successfully"}


@router.post("/resume")
async def resume_agent():
    """Resume the agent."""
    state_manager.resume()
    return {"status": "running", "message": "Agent resumed successfully"}


@router.get("/tasks")
async def list_scheduled_tasks(
    enabled_only: bool = True,
    client: Optional[str] = None
):
    """
    List scheduled tasks.

    Args:
        enabled_only: Only return enabled tasks
        client: Filter by client ID
    """
    tasks = agent_db.list_scheduled_tasks(
        enabled_only=enabled_only,
        client=client
    )

    return {
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "cron_expression": t.cron_expression,
                "task_type": t.task_type,
                "client": t.client,
                "enabled": t.enabled,
                "last_run_at": t.last_run_at.isoformat() if t.last_run_at else None,
                "next_run_at": t.next_run_at.isoformat() if t.next_run_at else None
            }
            for t in tasks
        ],
        "count": len(tasks)
    }


@router.get("/tasks/{task_id}")
async def get_scheduled_task(task_id: str):
    """Get details for a specific scheduled task."""
    task = agent_db.get_scheduled_task(task_id)

    if not task:
        return {"error": f"Task not found: {task_id}"}

    # Get recent executions
    executions = agent_db.get_recent_executions(task_id=task_id, limit=10)

    return {
        "task": {
            "id": task.id,
            "name": task.name,
            "cron_expression": task.cron_expression,
            "task_type": task.task_type,
            "client": task.client,
            "config": task.config.model_dump(),
            "enabled": task.enabled,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
            "created_at": task.created_at.isoformat()
        },
        "recent_executions": [
            {
                "id": e.id,
                "status": e.status.value,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error": e.error
            }
            for e in executions
        ]
    }


@router.post("/tasks/{task_id}/enable")
async def enable_task(task_id: str):
    """Enable a scheduled task."""
    task = agent_db.get_scheduled_task(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}

    # Calculate next run time
    next_run = scheduler.get_next_run_time(task.cron_expression)
    agent_db.update_scheduled_task(task_id, enabled=True, next_run_at=next_run)

    return {"success": True, "message": f"Task {task_id} enabled"}


@router.post("/tasks/{task_id}/disable")
async def disable_task(task_id: str):
    """Disable a scheduled task."""
    task = agent_db.get_scheduled_task(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}

    agent_db.update_scheduled_task(task_id, enabled=False)
    return {"success": True, "message": f"Task {task_id} disabled"}


@router.get("/executions")
async def list_executions(
    task_id: Optional[str] = None,
    limit: int = 50
):
    """
    List recent task executions.

    Args:
        task_id: Filter by task ID
        limit: Maximum number of results
    """
    executions = agent_db.get_recent_executions(task_id=task_id, limit=limit)

    return {
        "executions": [
            {
                "id": e.id,
                "task_id": e.task_id,
                "status": e.status.value,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error": e.error,
                "retry_count": e.retry_count
            }
            for e in executions
        ],
        "count": len(executions)
    }


@router.get("/upcoming")
async def list_upcoming_tasks(limit: int = 10):
    """
    List upcoming scheduled tasks.

    Returns tasks sorted by next run time.
    """
    upcoming = scheduler.list_upcoming_tasks(limit=limit)

    return {
        "upcoming": [
            {
                "id": task.id,
                "name": task.name,
                "task_type": task.task_type,
                "client": task.client,
                "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
                "time_until": time_str
            }
            for task, time_str in upcoming
        ]
    }


@router.post("/init")
async def initialize_default_tasks():
    """Initialize default scheduled tasks."""
    scheduler.create_default_tasks()
    return {"success": True, "message": "Default tasks initialized"}


@router.get("/statistics")
async def get_statistics():
    """Get agent statistics."""
    stats = state_manager.get_stats()

    return {
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/run/{task_type}")
async def run_task_now(
    task_type: str,
    client: Optional[str] = None,
    config: Optional[dict] = None
):
    """
    Run a task immediately (one-off execution).

    Available task types:
    - daily_analytics
    - content_pipeline
    - lead_outreach
    - ad_management
    - seo_optimization
    - weekly_report
    - creative_assets / og_image

    Args:
        task_type: Type of task to run
        client: Optional client ID
        config: Optional task configuration

    Example for OG image:
        POST /agent/run/og_image?client=kaicalls
        or
        POST /agent/run/og_image
        {"brand": "My Brand", "headline": "Build Better"}
    """
    from agent.tasks import get_task_handler
    from agent.models import ScheduledTask, ScheduledTaskConfig
    from uuid import uuid4

    handler = get_task_handler(task_type)
    if handler is None:
        return {"success": False, "error": f"Unknown task type: {task_type}"}

    # Create a temporary task object
    task = ScheduledTask(
        id=f"adhoc-{uuid4().hex[:8]}",
        name=f"Ad-hoc {task_type}",
        cron_expression="* * * * *",  # Dummy cron
        task_type=task_type,
        client=client,
        config=ScheduledTaskConfig(config=config or {})
    )

    try:
        result = await handler.execute(task)
        return {
            "success": True,
            "task_type": task_type,
            "client": client,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "task_type": task_type,
            "error": str(e)
        }

"""
Task Board — internal to-do tracking for Kai Calls operations.

Schedule: Daily 9 AM (0 9 * * *)

Manages a persistent to-do list in agent state.
Tasks are added/completed via WhatsApp commands.
Daily reminder of open P1/P2 tasks.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager


STATE_KEY = "kai_task_board"


class TaskBoardTask(BaseTask):
    """Manages internal task tracking and sends daily reminders."""

    @property
    def task_type(self) -> str:
        return "kai_task_board"

    @property
    def description(self) -> str:
        return "Kai Calls: Daily task board reminder"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        """Send daily reminder of open tasks."""
        try:
            board = _get_board()
            open_tasks = [t for t in board.get("tasks", []) if t["status"] == "open"]

            if not open_tasks:
                return {
                    "success": True,
                    "summary": "Task board: No open tasks",
                    "data": {"open_count": 0},
                }

            # Sort by priority
            priority_order = {"P1": 0, "P2": 1, "P3": 2}
            open_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "P3"), 3))

            # Format message
            lines = ["*KaiCalls Task Board*", ""]

            p1_tasks = [t for t in open_tasks if t.get("priority") == "P1"]
            p2_tasks = [t for t in open_tasks if t.get("priority") == "P2"]
            p3_tasks = [t for t in open_tasks if t.get("priority") == "P3"]

            if p1_tasks:
                lines.append(f"*P1 — Urgent ({len(p1_tasks)})*")
                for t in p1_tasks:
                    age = _days_since(t.get("created_at", ""))
                    lines.append(f"  [{t['id'][:6]}] {t['title']} ({age}d)")
                lines.append("")

            if p2_tasks:
                lines.append(f"*P2 — Normal ({len(p2_tasks)})*")
                for t in p2_tasks:
                    lines.append(f"  [{t['id'][:6]}] {t['title']}")
                lines.append("")

            if p3_tasks:
                lines.append(f"*P3 — Low ({len(p3_tasks)})*")
                for t in p3_tasks[:3]:
                    lines.append(f"  [{t['id'][:6]}] {t['title']}")
                if len(p3_tasks) > 3:
                    lines.append(f"  ... and {len(p3_tasks) - 3} more")

            lines.append("")
            lines.append("_'done:<id>' to complete, 'todo:<text>' to add_")

            await self.send_notification("\n".join(lines))

            return {
                "success": True,
                "summary": f"Task board: {len(open_tasks)} open tasks reminded",
                "data": {"open_count": len(open_tasks)},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


# =========================================================================
# Task Board CRUD — used by WhatsApp commands
# =========================================================================

def add_task(title: str, priority: str = "P2") -> Dict[str, Any]:
    """Add a new task to the board."""
    board = _get_board()
    task = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "priority": priority,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    board.setdefault("tasks", []).append(task)
    _save_board(board)
    return task


def complete_task(task_id_prefix: str) -> Optional[Dict[str, Any]]:
    """Mark a task as done by ID prefix match."""
    board = _get_board()
    for task in board.get("tasks", []):
        if task["id"].startswith(task_id_prefix) and task["status"] == "open":
            task["status"] = "done"
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            _save_board(board)
            return task
    return None


def list_tasks(status: str = "open") -> List[Dict[str, Any]]:
    """List tasks by status."""
    board = _get_board()
    return [t for t in board.get("tasks", []) if t["status"] == status]


def get_stats() -> Dict[str, int]:
    """Get task board statistics."""
    board = _get_board()
    tasks = board.get("tasks", [])
    return {
        "total": len(tasks),
        "open": sum(1 for t in tasks if t["status"] == "open"),
        "done": sum(1 for t in tasks if t["status"] == "done"),
        "p1_open": sum(1 for t in tasks if t["status"] == "open" and t.get("priority") == "P1"),
    }


# =========================================================================
# Helpers
# =========================================================================

def _get_board() -> Dict[str, Any]:
    return state_manager.get(STATE_KEY) or {"tasks": []}


def _save_board(board: Dict[str, Any]):
    state_manager.set(STATE_KEY, board)


def _days_since(iso_timestamp: str) -> int:
    if not iso_timestamp:
        return 0
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return max(0, int(delta.total_seconds() / 86400))
    except (ValueError, TypeError):
        return 0

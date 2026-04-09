"""Claude Agent task handler — uses Claude Agent SDK for autonomous execution.

This task handler integrates with the existing AgentLoop. When scheduled
or triggered, it spawns Claude Code via the SDK with the appropriate
Kai skills injected into an isolated workdir.

Register this handler for task types that need LLM-powered execution
(content generation, audits, competitive analysis, etc.)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from .base import BaseTask

logger = logging.getLogger(__name__)


class ClaudeAgentTask(BaseTask):
    """Execute marketing tasks via Claude Code Agent SDK."""

    @property
    def task_type(self) -> str:
        return "claude_agent"

    @property
    def description(self) -> str:
        return "Execute marketing task via Claude Code agent"

    async def execute(self, task, **kwargs) -> Optional[Dict[str, Any]]:
        """Execute a task using the Claude Agent SDK.

        The task.config.extra dict should contain:
        - skill: str — which Kai skill to use (e.g. "kai-write")
        - task_type_override: str — override task_type for skill routing
        - brand_id: str — brand context
        - input: dict — task input parameters
        - risk_tier: str — low/medium/high (controls permissions)
        """
        try:
            from daemon.executor import execute_task as daemon_execute
            from daemon.config import DaemonConfig
            from daemon.models import AgentTask
        except ImportError as e:
            logger.warning("Daemon module not available: %s", e)
            return {"success": False, "error": f"Import error: {e}"}

        extra = task.config.extra if task.config else {}

        # Build an AgentTask from the scheduled task config
        agent_task = AgentTask(
            id=task.id,
            brand_id=extra.get("brand_id", "unknown"),
            task_type=extra.get("task_type_override", task.task_type),
            skill=extra.get("skill"),
            trigger="scheduled",
            input=extra.get("input", {}),
            risk_tier=extra.get("risk_tier", "low"),
        )

        config = DaemonConfig.from_env()

        # Get Supabase client for message streaming (optional)
        supabase_client = None
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                supabase_client = create_client(supabase_url, supabase_key)
            except ImportError:
                logger.warning("supabase-py not installed, messages won't stream")

        try:
            result = await daemon_execute(agent_task, config, supabase_client)

            return {
                "success": result.status.value == "completed",
                "status": result.status.value,
                "summary": f"Task {result.status.value} (cost=${result.cost_usd:.4f}, turns={result.num_turns})",
                "output": result.output,
                "session_id": result.session_id,
                "cost_usd": result.cost_usd,
                "error": result.error,
            }

        except Exception as e:
            logger.exception("Claude agent task failed")
            return {"success": False, "error": str(e)}

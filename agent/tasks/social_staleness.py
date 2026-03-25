"""
Social data staleness check task handler.

Monitors freshness of social media CSV imports and alerts when
platform data goes stale, preventing the learning loop from
running on outdated social signals.
"""

from typing import Any, Dict, Optional

from ..models import ScheduledTask
from .base import BaseTask


class SocialStalenessTask(BaseTask):
    """Check social data import freshness and alert on staleness."""

    @property
    def task_type(self) -> str:
        return "social_staleness_check"

    @property
    def description(self) -> str:
        return "Check social media data import freshness"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Run staleness check and notify if actionable results found."""
        from scripts.self_improvement.social_staleness import (
            check_staleness,
            format_reminder_message,
        )

        results = check_staleness()

        # Filter to critical-only if configured
        extra = {}
        if task.config and hasattr(task.config, "extra") and task.config.extra:
            extra = task.config.extra
        if extra.get("critical_only"):
            results = [r for r in results if r["severity"] == "critical"]

        actionable = [r for r in results if r["severity"] in ("warning", "critical", "never")]

        if actionable:
            message = format_reminder_message(results)
            if message:
                await self.send_notification(message, task=task)

        return {
            "success": True,
            "summary": f"Checked {len(results)} platforms, {len(actionable)} need attention",
            "data": {
                "platforms_checked": len(results),
                "actionable": len(actionable),
                "details": results,
            },
        }

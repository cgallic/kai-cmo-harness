"""
Weekly HALO-style harness review.

Aggregates trace data from the last 7 days, asks an LLM to propose
concrete harness improvements, and writes the result to
`workspace/harness-reviews/` so changes can be cherry-picked.

Add to the scheduler with task_type="harness_review".
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ..models import ScheduledTask
from ..traces.diagnose import diagnose
from .base import BaseTask


class HarnessReviewTask(BaseTask):
    """Recurring harness review task driven by the trace store."""

    @property
    def task_type(self) -> str:
        return "harness_review"

    @property
    def description(self) -> str:
        return "Diagnose recent trace activity and propose harness improvements"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        days = int(task.config.extra.get("window_days", 7))
        since = datetime.utcnow() - timedelta(days=days)
        prompt = task.config.extra.get("prompt") or (
            "Find recurring task failures, weak prompt/tool boundaries, missing "
            "context, notification spam, and scheduler issues. Suggest concrete "
            "harness changes. Cite the task or span by name."
        )

        report = await diagnose(
            since=since,
            until=None,
            task_id=task.config.extra.get("task_id"),
            client=task.client,
            prompt=prompt,
            use_llm=True,
        )

        review_dir = Path(__file__).parent.parent.parent / "workspace" / "harness-reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        suffix = f"-{task.client}" if task.client else ""
        review_path = review_dir / f"harness-review-{date_str}{suffix}.md"
        review_path.write_text(
            f"# Harness review — {date_str} (last {days}d)\n\n{report}"
        )

        # Build a short summary for notifications.
        summary_lines = []
        for line in report.splitlines():
            if line.startswith("## HALO suggestions"):
                continue
            if line.strip().startswith(("- ", "* ", "1.", "2.", "3.")):
                summary_lines.append(line.strip())
            if len(summary_lines) >= 5:
                break

        return {
            "success": True,
            "summary": (
                f"Harness review ({days}d) saved to {review_path.name}.\n"
                + "\n".join(summary_lines[:5])
            ),
            "data": {
                "report_path": str(review_path),
                "window_days": days,
            },
        }

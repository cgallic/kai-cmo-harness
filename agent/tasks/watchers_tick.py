"""Watchers tick task handler.

Bridges the ``kai.watchers`` framework into the agent cron loop: registers
every concrete watcher, runs the ones due for each configured business
through ``WatcherScheduler``, routes findings through ``NotificationSystem``,
and delivers immediate-routed findings over the agent notification channel
(Discord/WhatsApp).

Businesses come from the task config, e.g. in the scheduler task entry::

    "config": {"extra": {"businesses": [
        {"id": "mysite", "archetype": "local_service",
         "website_url": "https://mysite.com", "phone": "+1 555 010 0000"}
    ]}}

Suppression state lives inside the framework per process run; the daily
cadence plus the framework's per-run dedup keeps alert fatigue bounded.
"""

from typing import Any, Dict, List, Optional

from ..models import ScheduledTask
from .base import BaseTask


class WatchersTickTask(BaseTask):
    """Run due marketing watchers and notify on immediate findings."""

    @property
    def task_type(self) -> str:
        return "watchers_tick"

    @property
    def description(self) -> str:
        return "Run marketing watchers and route findings"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        from datetime import datetime, timezone

        from kai.watchers import (
            NotificationPreference,
            NotificationSystem,
            SuppressionManager,
            WatcherScheduler,
            create_default_registry,
        )

        extra: Dict[str, Any] = {}
        if task.config and hasattr(task.config, "extra") and task.config.extra:
            extra = task.config.extra
        businesses: List[Dict[str, Any]] = extra.get("businesses") or []

        if not businesses:
            return {
                "success": True,
                "summary": (
                    "No businesses configured for watchers — add "
                    "config.extra.businesses to the watchers_tick task"
                ),
                "data": {"businesses_checked": 0, "findings": 0},
            }

        scheduler = WatcherScheduler(create_default_registry(), SuppressionManager())
        notifier = NotificationSystem()
        now = datetime.now(timezone.utc).isoformat()

        total_findings = 0
        immediate = 0
        digested = 0
        messages: List[str] = []
        per_business: Dict[str, int] = {}

        for biz in businesses:
            business_id = str(biz.get("id", "default"))
            archetype = str(biz.get("archetype", "local_service"))
            preference = NotificationPreference(business_id=business_id)

            outputs = scheduler.run_all_due(business_id, archetype, biz, {}, now)
            count = 0
            for output in outputs:
                for finding in output.findings:
                    count += 1
                    route = notifier.dispatch_finding(
                        finding, preference, messages.append
                    )
                    if route == "immediate":
                        immediate += 1
                    else:
                        digested += 1
            per_business[business_id] = count
            total_findings += count

        for message in messages:
            await self.send_notification(message, task=task)

        return {
            "success": True,
            "summary": (
                f"Ran watchers for {len(businesses)} business(es): "
                f"{total_findings} findings ({immediate} immediate, {digested} digest)"
            ),
            "data": {
                "businesses_checked": len(businesses),
                "findings": total_findings,
                "immediate": immediate,
                "digest": digested,
                "per_business": per_business,
            },
        }

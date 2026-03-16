"""
Generation Monitor — catches stuck/failed product generations.

Schedule: Every 10 minutes (*/10 * * * *)

Each tick:
1. Check for generations stuck >30min in processing
2. Check error rate over last hour — alert if >25%
3. Track generation throughput for trending
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import bwk_client


class GenerationMonitorTask(BaseTask):
    """Monitors product generation health for BuildWithKai."""

    @property
    def task_type(self) -> str:
        return "bwk_generation_monitor"

    @property
    def description(self) -> str:
        return "BWK: Monitor product generations, alert on stuck/failed jobs"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            alerts: List[str] = []

            # 1. Check stuck generations (>30min)
            stuck = await bwk_client.get_stuck_generations(minutes=30)
            if stuck:
                alerts.append(
                    f"{len(stuck)} generation(s) stuck >30min"
                )
                for s in stuck[:3]:
                    alerts.append(
                        f"  - {s['id'][:8]}: status={s.get('status')}, "
                        f"progress={s.get('progress')}"
                    )

            # 2. Check error rate (last 2 hours)
            stats = await bwk_client.get_generation_stats(hours=2)
            error_rate = stats.get("error_rate", 0)
            if error_rate > 25:
                alerts.append(
                    f"High error rate: {error_rate}% "
                    f"({stats.get('failed', 0)}/{stats.get('total', 0)} in last 2h)"
                )

            # 3. Get failed jobs for detail
            failed = await bwk_client.get_failed_generations(hours=2)
            error_messages: Dict[str, int] = {}
            for f in failed:
                msg = (f.get("error_message") or "Unknown error")[:80]
                error_messages[msg] = error_messages.get(msg, 0) + 1

            if error_messages and len(failed) >= 3:
                alerts.append("Top errors:")
                for msg, count in sorted(error_messages.items(), key=lambda x: -x[1])[:3]:
                    alerts.append(f"  - ({count}x) {msg}")

            # 4. Send alerts
            if alerts:
                msg = "*BWK Generation Alert*\n\n" + "\n".join(alerts)
                await self.send_notification(msg)
                await bwk_client.log_action(
                    "generation_alert",
                    reason=f"{len(stuck)} stuck, {error_rate}% error rate"
                )

            # 5. Store stats for trending
            state_manager.set_task_context("bwk_gen_stats", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_2h": stats.get("total", 0),
                "completed_2h": stats.get("completed", 0),
                "failed_2h": stats.get("failed", 0),
                "stuck": len(stuck),
                "error_rate": error_rate,
            })

            summary = f"Gens: {stats.get('total', 0)} (2h), "
            summary += f"{len(stuck)} stuck, {error_rate}% error rate"

            return {
                "success": True,
                "summary": summary,
                "data": {"stats": stats, "stuck": len(stuck), "alerts": alerts},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

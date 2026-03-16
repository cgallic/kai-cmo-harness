"""
Onboarding Tracker — monitors new business setup progress.

Schedule: Every 6 hours (0 */6 * * *)

Checks businesses signed up in last 14 days:
- Business profile complete
- Agent created with phone number
- Email account connected
- First call received

Alerts if stuck >24h on any step.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import kai_client


class OnboardingTrackerTask(BaseTask):
    """Tracks new business onboarding progress."""

    @property
    def task_type(self) -> str:
        return "kai_onboarding"

    @property
    def description(self) -> str:
        return "Kai Calls: Track new business onboarding, alert on stuck businesses"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            statuses = await kai_client.get_onboarding_status()

            if not statuses:
                return {
                    "success": True,
                    "summary": "Onboarding: No new businesses in last 14 days",
                    "data": {"count": 0},
                }

            alerts = []
            funnel = {
                "signed_up": len(statuses),
                "profile_complete": 0,
                "has_agent": 0,
                "has_phone": 0,
                "has_email": 0,
                "has_calls": 0,
            }

            for biz in statuses:
                steps = self._get_incomplete_steps(biz)
                age_hours = _hours_since(biz.get("created_at", ""))

                # Update funnel
                if biz["profile_complete"]:
                    funnel["profile_complete"] += 1
                if biz["has_agent"]:
                    funnel["has_agent"] += 1
                if biz["has_phone"]:
                    funnel["has_phone"] += 1
                if biz["has_email_account"]:
                    funnel["has_email"] += 1
                if biz["has_calls"]:
                    funnel["has_calls"] += 1

                # Alert if stuck >24h
                if steps and age_hours > 24:
                    alerts.append(
                        f"*{biz['business_name']}* stuck for {age_hours:.0f}h — "
                        f"missing: {', '.join(steps)}"
                    )

            # Send alerts if any
            if alerts:
                msg = "*KaiCalls Onboarding Alerts*\n\n" + "\n".join(alerts[:5])
                msg += f"\n\n_Funnel: {funnel['signed_up']} signed up → "
                msg += f"{funnel['has_agent']} with agent → "
                msg += f"{funnel['has_calls']} active_"
                await self.send_notification(msg)

            # Store funnel data
            state_manager.set_task_context("kai_onboarding_funnel", {
                "date": datetime.now(timezone.utc).isoformat(),
                "funnel": funnel,
                "stuck_count": len(alerts),
            })

            return {
                "success": True,
                "summary": f"Onboarding: {len(statuses)} businesses tracked, {len(alerts)} stuck",
                "data": {"funnel": funnel, "alerts": alerts, "statuses": statuses},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_incomplete_steps(self, biz: Dict[str, Any]) -> List[str]:
        """Get list of incomplete onboarding steps."""
        steps = []
        if not biz.get("profile_complete"):
            steps.append("profile")
        if not biz.get("has_agent"):
            steps.append("agent")
        if not biz.get("has_phone"):
            steps.append("phone number")
        if not biz.get("has_email_account"):
            steps.append("email account")
        if not biz.get("has_calls"):
            steps.append("first call")
        return steps


def _hours_since(iso_timestamp: str) -> float:
    """Calculate hours since an ISO timestamp."""
    if not iso_timestamp:
        return 0
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return delta.total_seconds() / 3600
    except (ValueError, TypeError):
        return 0

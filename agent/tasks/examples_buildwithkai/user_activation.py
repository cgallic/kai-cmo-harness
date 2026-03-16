"""
User Activation Tracker — monitors signup-to-revenue funnel.

Schedule: Every 6 hours (0 */6 * * *)

Funnel: signup -> business plan -> first product -> published -> revenue
Alerts:
- Users stuck >48h at any step
- Users inactive >7d (churn risk)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import bwk_client


class UserActivationTask(BaseTask):
    """Tracks user activation funnel for BuildWithKai."""

    @property
    def task_type(self) -> str:
        return "bwk_user_activation"

    @property
    def description(self) -> str:
        return "BWK: Track user activation funnel, flag stuck/churning users"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            alerts: List[str] = []

            # 1. Get funnel data
            funnel = await bwk_client.get_user_funnel_data()

            # 2. Check stuck users (signed up >48h, no product)
            stuck = await bwk_client.get_stuck_users(hours=48)
            if stuck:
                alerts.append(f"{len(stuck)} user(s) stuck in onboarding >48h")
                for u in stuck[:3]:
                    step = u.get("onboarding_step", "unknown")
                    alerts.append(f"  - {u['id'][:8]}: step={step}")

            # 3. Check inactive users (no activity in 7d)
            inactive = await bwk_client.get_inactive_users(days=7)
            if inactive:
                # Only alert on users who had some engagement
                churning = [
                    u for u in inactive
                    if u.get("engagement_level") not in (None, "none", "low")
                ]
                if churning:
                    alerts.append(f"{len(churning)} engaged user(s) inactive >7d (churn risk)")

            # 4. Funnel summary
            funnel_msg = (
                f"Funnel: {funnel['total_users']} users → "
                f"{funnel['users_with_plans']} plans → "
                f"{funnel['users_with_products']} products → "
                f"{funnel['users_with_published']} published"
            )

            # Calculate conversion rates
            rates = {}
            if funnel["total_users"] > 0:
                rates["signup_to_plan"] = round(
                    (funnel["users_with_plans"] / funnel["total_users"]) * 100
                )
                rates["plan_to_product"] = round(
                    (funnel["users_with_products"] / max(funnel["users_with_plans"], 1)) * 100
                )
                rates["product_to_published"] = round(
                    (funnel["users_with_published"] / max(funnel["users_with_products"], 1)) * 100
                )

            # 5. Send alerts if any
            if alerts:
                msg = "*BWK User Activation*\n\n"
                msg += funnel_msg + "\n\n"
                msg += "\n".join(alerts)
                await self.send_notification(msg)

            # 6. Store funnel data for trending
            state_manager.set_task_context("bwk_funnel", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "funnel": funnel,
                "rates": rates,
                "stuck_count": len(stuck),
                "inactive_count": len(inactive),
            })

            return {
                "success": True,
                "summary": funnel_msg,
                "data": {
                    "funnel": funnel,
                    "rates": rates,
                    "stuck": len(stuck),
                    "inactive": len(inactive),
                    "alerts": alerts,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

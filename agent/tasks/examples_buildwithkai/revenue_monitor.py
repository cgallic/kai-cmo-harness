"""
Revenue Monitor — tracks published products, downloads, and revenue.

Schedule: Daily 7 AM (0 7 * * *)

Key alerts:
- Products with downloads but no Stripe product (missed money)
- Revenue milestones
- Published product count changes
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import bwk_client


class RevenueMonitorTask(BaseTask):
    """Monitors revenue and product publishing for BuildWithKai."""

    @property
    def task_type(self) -> str:
        return "bwk_revenue_monitor"

    @property
    def description(self) -> str:
        return "BWK: Track published products, downloads, revenue, missed opportunities"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            revenue = await bwk_client.get_revenue_stats(days=7)
            alerts: List[str] = []

            # 1. Missed revenue — downloads but no Stripe
            if revenue["missed_revenue_products"] > 0:
                alerts.append(
                    f"{revenue['missed_revenue_products']} published product(s) have downloads "
                    f"but no Stripe setup (missed revenue)"
                )

            # 2. Compare to previous day
            prev = state_manager.get_task_context("bwk_revenue_prev")
            if prev:
                prev_published = prev.get("total_published", 0)
                new_published = revenue["total_published"] - prev_published
                if new_published > 0:
                    alerts.append(f"{new_published} new product(s) published since last check")

                prev_revenue = prev.get("total_revenue", 0)
                new_revenue = revenue["total_revenue"] - prev_revenue
                if new_revenue > 0:
                    alerts.append(f"${new_revenue:.2f} new revenue")

            # 3. Build report
            lines = [
                "*BWK Revenue Report*",
                "───────────────────",
                f"Published products: {revenue['total_published']}",
                f"With Stripe: {revenue['products_with_stripe']}",
                f"Without Stripe: {revenue['products_without_stripe']}",
                f"Total revenue: ${revenue['total_revenue']:.2f}",
                f"Downloads (7d): {revenue['recent_downloads']}",
                f"Sales (7d): {revenue['recent_sales']}",
            ]

            if alerts:
                lines.append("───────────────────")
                lines.append("Alerts:")
                lines.extend(f"- {a}" for a in alerts)

            report = "\n".join(lines)
            await self.send_notification(report)

            # 4. Store for next comparison
            state_manager.set_task_context("bwk_revenue_prev", {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "total_published": revenue["total_published"],
                "total_revenue": revenue["total_revenue"],
                "recent_downloads": revenue["recent_downloads"],
                "recent_sales": revenue["recent_sales"],
            })

            return {
                "success": True,
                "summary": f"Revenue: ${revenue['total_revenue']:.2f}, {revenue['total_published']} published",
                "data": {"revenue": revenue, "alerts": alerts, "report": report},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

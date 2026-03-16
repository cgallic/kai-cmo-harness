"""
BWK Business Ops — daily/weekly summary reports.

Schedule:
- Daily 8 AM: 0 8 * * *
- Weekly Sunday 9 AM: 0 9 * * 0
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import bwk_client


class BWKBusinessOpsTask(BaseTask):
    """Generates daily/weekly BWK operations reports."""

    @property
    def task_type(self) -> str:
        return "bwk_business_ops"

    @property
    def description(self) -> str:
        return "BWK: Daily/weekly business operations report"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            is_weekly = task.config.extra.get("weekly", False)

            if is_weekly:
                report = await self._generate_weekly_report()
            else:
                report = await self._generate_daily_report()

            await self.send_notification(report)

            return {
                "success": True,
                "summary": f"{'Weekly' if is_weekly else 'Daily'} BWK ops report sent",
                "data": {"report": report},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_daily_report(self) -> str:
        """Generate the daily operations report."""
        today = datetime.now(timezone.utc).strftime("%b %d")

        gen_stats = await bwk_client.get_generation_stats(hours=24)
        plan_stats = await bwk_client.get_business_plan_stats(hours=24)
        funnel = await bwk_client.get_user_funnel_data()
        revenue = await bwk_client.get_revenue_stats(days=1)
        stuck = await bwk_client.get_stuck_generations(minutes=30)
        conversations = await bwk_client.get_recent_conversations(hours=24)

        lines = [
            f"*BWK Daily ({today})*",
            "───────────────────",
            f"Signups: {funnel['total_users']} total",
            f"Business plans (24h): {plan_stats['total']}",
            f"Generations (24h): {gen_stats['total']} "
            f"({gen_stats['completed']} ok, {gen_stats['failed']} failed)",
            f"Error rate: {gen_stats['error_rate']}%",
            f"Published: {revenue['total_published']} total",
            f"Revenue: ${revenue['total_revenue']:.2f}",
            f"Chat sessions (24h): {len(conversations)}",
            "───────────────────",
        ]

        # Alerts
        alert_lines = []
        if len(stuck) > 0:
            alert_lines.append(f"- {len(stuck)} generation(s) stuck >30min")
        if gen_stats["error_rate"] > 20:
            alert_lines.append(f"- High error rate: {gen_stats['error_rate']}%")
        if revenue["missed_revenue_products"] > 0:
            alert_lines.append(
                f"- {revenue['missed_revenue_products']} products with downloads but no Stripe"
            )

        if alert_lines:
            lines.append("Alerts:")
            lines.extend(alert_lines)
        else:
            lines.append("No alerts")

        # Funnel snapshot
        lines.append("")
        lines.append(
            f"_Funnel: {funnel['total_users']} users → "
            f"{funnel['users_with_plans']} plans → "
            f"{funnel['users_with_products']} products → "
            f"{funnel['users_with_published']} published_"
        )

        # Store for comparison
        state_manager.set_task_context("bwk_daily_prev", {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "generations": gen_stats["total"],
            "failed": gen_stats["failed"],
            "published": revenue["total_published"],
        })

        return "\n".join(lines)

    async def _generate_weekly_report(self) -> str:
        """Generate the weekly strategic report."""
        gen_stats = await bwk_client.get_generation_stats(hours=168)  # 7 days
        funnel = await bwk_client.get_user_funnel_data()
        revenue = await bwk_client.get_revenue_stats(days=7)
        funnel_stats = await bwk_client.get_funnel_stats()

        lines = [
            "*BWK Weekly Report*",
            "═══════════════════",
            "",
            "*Generations (7d)*",
            f"  Total: {gen_stats['total']}",
            f"  Completed: {gen_stats['completed']}",
            f"  Failed: {gen_stats['failed']}",
            f"  Error rate: {gen_stats['error_rate']}%",
            "",
            "*User Funnel*",
            f"  Total users: {funnel['total_users']}",
            f"  With plans: {funnel['users_with_plans']}",
            f"  With products: {funnel['users_with_products']}",
            f"  Published: {funnel['users_with_published']}",
            "",
            "*Revenue*",
            f"  Total: ${revenue['total_revenue']:.2f}",
            f"  Published products: {revenue['total_published']}",
            f"  Sales (7d): {revenue['recent_sales']}",
            f"  Downloads (7d): {revenue['recent_downloads']}",
            "",
            "*Funnels*",
            f"  Total: {funnel_stats['total']}",
        ]

        if funnel_stats.get("by_status"):
            for status, count in funnel_stats["by_status"].items():
                lines.append(f"  {status}: {count}")

        lines.extend([
            "",
            "───────────────────",
            "_Reply 'bwkstatus' for live snapshot_",
        ])

        return "\n".join(lines)

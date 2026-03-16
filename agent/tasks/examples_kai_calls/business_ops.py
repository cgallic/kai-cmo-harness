"""
Business Ops Dashboard — daily/weekly metrics and anomaly alerts.

Schedule:
- Daily 8 AM: 0 8 * * *
- Weekly Sunday 9 AM: 0 9 * * 0
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import kai_client


class BusinessOpsTask(BaseTask):
    """Generates daily/weekly business operations reports."""

    @property
    def task_type(self) -> str:
        return "kai_business_ops"

    @property
    def description(self) -> str:
        return "Kai Calls: Daily/weekly business operations report"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            # Determine if this is a daily or weekly run
            is_weekly = task.config.extra.get("weekly", False)

            if is_weekly:
                report = await self._generate_weekly_report()
            else:
                report = await self._generate_daily_report()

            # Send via WhatsApp
            await self.send_notification(report)

            return {
                "success": True,
                "summary": f"{'Weekly' if is_weekly else 'Daily'} ops report sent",
                "data": {"report": report},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_daily_report(self) -> str:
        """Generate the daily operations report."""
        today = datetime.now(timezone.utc).strftime("%b %d")

        # Gather metrics in parallel-style (sequential here but fast)
        call_stats = await kai_client.get_call_stats(days=7)
        email_stats = await kai_client.get_email_stats(days=1)
        new_leads = await kai_client.get_new_leads(hours=24)
        businesses = await kai_client.get_businesses()
        stale_emails = await kai_client.get_stale_emails(minutes=120)
        failed_emails = await kai_client.get_failed_emails(hours=24)

        # Today's calls
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_calls = call_stats.get("calls_per_day", {}).get(today_str, 0)
        avg_calls = call_stats.get("daily_average", 0)

        # Calculate change vs average
        if avg_calls > 0:
            change = ((today_calls - avg_calls) / avg_calls) * 100
            change_str = f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"
        else:
            change_str = "N/A"

        active_businesses = sum(1 for b in businesses if b.get("is_active", True))
        total_businesses = len(businesses)

        # Lead capture rate
        capture_rate = 0
        if today_calls > 0:
            capture_rate = round((len(new_leads) / today_calls) * 100)

        lines = [
            f"*KaiCalls Daily ({today})*",
            "───────────────────",
            f"Calls: {today_calls} ({change_str} vs 7d avg)",
            f"New leads: {len(new_leads)} ({capture_rate}% capture rate)",
            f"Emails: {email_stats.get('sent', 0)} sent, {email_stats.get('pending', 0)} pending, {email_stats.get('failed', 0)} failed",
            f"Active businesses: {active_businesses}/{total_businesses}",
            "───────────────────",
        ]

        # Alerts
        alert_lines = []
        if stale_emails:
            biz_counts: Dict[str, int] = {}
            for e in stale_emails:
                biz_name = e.get("businesses", {}).get("name", "Unknown")
                biz_counts[biz_name] = biz_counts.get(biz_name, 0) + 1
            for biz, count in list(biz_counts.items())[:3]:
                alert_lines.append(f"- \"{biz}\" has {count} stale emails (>2h)")

        if failed_emails:
            alert_lines.append(f"- {len(failed_emails)} emails failed in last 24h")

        # Check for low-volume businesses
        prev_stats = state_manager.get_task_context("kai_business_ops_prev")
        if prev_stats:
            pass  # Future: compare daily volumes per business

        if alert_lines:
            lines.append("Alerts:")
            lines.extend(alert_lines)
        else:
            lines.append("No alerts")

        # Store today's stats for comparison
        state_manager.set_task_context("kai_business_ops_prev", {
            "date": today_str,
            "calls": today_calls,
            "leads": len(new_leads),
            "emails_sent": email_stats.get("sent", 0),
        })

        return "\n".join(lines)

    async def _generate_weekly_report(self) -> str:
        """Generate the weekly strategic report."""
        call_stats = await kai_client.get_call_stats(days=7)
        email_stats = await kai_client.get_email_stats(days=7)
        businesses = await kai_client.get_businesses()
        new_leads = await kai_client.get_new_leads(hours=168)  # 7 days

        total_calls = call_stats.get("total_calls", 0)
        avg_duration = call_stats.get("avg_duration_seconds", 0)

        lines = [
            "*KaiCalls Weekly Report*",
            "═══════════════════════",
            "",
            "*Call Volume*",
            f"  Total: {total_calls}",
            f"  Daily avg: {call_stats.get('daily_average', 0)}",
            f"  Avg duration: {avg_duration:.0f}s",
            "",
            "*Lead Pipeline*",
            f"  New leads: {len(new_leads)}",
            f"  Capture rate: {round((len(new_leads) / max(total_calls, 1)) * 100)}%",
            "",
            "*Email Follow-Ups*",
            f"  Sent: {email_stats.get('sent', 0)}",
            f"  Failed: {email_stats.get('failed', 0)}",
            f"  Pending: {email_stats.get('pending', 0)}",
            f"  Rejected: {email_stats.get('rejected', 0)}",
            "",
            "*Businesses*",
            f"  Total: {len(businesses)}",
            f"  Active: {sum(1 for b in businesses if b.get('is_active', True))}",
            "",
            "───────────────────",
            "_Reply 'kaistatus' for live snapshot_",
        ]

        return "\n".join(lines)

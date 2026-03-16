"""
ABP Business Ops — daily/weekly summary reports.

Schedule:
- Daily 8 AM: 0 8 * * *
- Weekly Sunday 9 AM: 0 9 * * 0
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import abp_client


class ABPBusinessOpsTask(BaseTask):
    """Generates daily/weekly ABP operations reports."""

    @property
    def task_type(self) -> str:
        return "abp_business_ops"

    @property
    def description(self) -> str:
        return "ABP: Daily/weekly business operations report"

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
                "summary": f"{'Weekly' if is_weekly else 'Daily'} ABP ops report sent",
                "data": {"report": report},
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_daily_report(self) -> str:
        """Generate the daily operations report."""
        today = datetime.now(timezone.utc).strftime("%b %d")

        lead_stats = await abp_client.get_lead_stats(days=1)
        vendors = await abp_client.get_vendors()
        coverage = await abp_client.get_vendor_coverage()
        funnel = await abp_client.get_vendor_funnel()
        high_value = await abp_client.get_high_value_leads(hours=24)
        seo = await abp_client.get_seo_stats()

        # Compare to previous
        prev = state_manager.get_task_context("abp_daily_prev")
        today_leads = lead_stats["total"]
        change_str = "N/A"
        if prev:
            prev_avg = prev.get("daily_avg", 0)
            if prev_avg > 0:
                change = ((today_leads - prev_avg) / prev_avg) * 100
                change_str = f"+{change:.0f}%" if change >= 0 else f"{change:.0f}%"

        lines = [
            f"*ABP Daily ({today})*",
            "───────────────────",
            f"Leads (24h): {today_leads} ({change_str} vs avg)",
            f"Match rate: {lead_stats['match_rate']}%",
            f"Unmatched: {lead_stats['unmatched']}",
            f"High-value: {len(high_value)}",
            "",
            f"Active vendors: {len(vendors)}",
            f"Coverage: {coverage['total_covered_zips']} ZIPs",
            f"Gaps: {coverage['gap_count']} ZIPs with demand, no vendor",
            "",
            f"Vendor pipeline: {funnel['pending_invite']} to invite, {funnel['pending_signup']} awaiting signup",
            "",
            f"SEO: {seo['total_clicks']} clicks, {seo['total_impressions']} impressions, "
            f"avg pos {seo['avg_position']}",
            "───────────────────",
        ]

        # Alerts
        alert_lines = []
        if coverage["gap_count"] > 5:
            alert_lines.append(f"- {coverage['gap_count']} ZIP coverage gaps")
        if lead_stats["match_rate"] < 50:
            alert_lines.append(f"- Low match rate: {lead_stats['match_rate']}%")
        if len(high_value) > 0:
            for hv in high_value[:2]:
                name = hv.get("name") or hv.get("email") or "?"
                reasons = hv.get("_high_value_reasons", [])
                alert_lines.append(f"- Hot lead: {name} ({', '.join(reasons)})")

        if alert_lines:
            lines.append("Alerts:")
            lines.extend(alert_lines)
        else:
            lines.append("No alerts")

        # Store for comparison
        state_manager.set_task_context("abp_daily_prev", {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "leads": today_leads,
            "daily_avg": lead_stats.get("daily_average", 0),
            "vendors": len(vendors),
            "match_rate": lead_stats["match_rate"],
        })

        return "\n".join(lines)

    async def _generate_weekly_report(self) -> str:
        """Generate the weekly strategic report."""
        lead_stats = await abp_client.get_lead_stats(days=7)
        vendors = await abp_client.get_vendors()
        coverage = await abp_client.get_vendor_coverage()
        funnel = await abp_client.get_vendor_funnel()
        seo = await abp_client.get_seo_stats()

        lines = [
            "*ABP Weekly Report*",
            "═══════════════════",
            "",
            "*Leads (7d)*",
            f"  Total: {lead_stats['total']}",
            f"  Daily avg: {lead_stats['daily_average']}",
            f"  Match rate: {lead_stats['match_rate']}%",
            f"  Unmatched: {lead_stats['unmatched']}",
        ]

        if lead_stats.get("by_event_type"):
            lines.append("  By event type:")
            for et, count in sorted(lead_stats["by_event_type"].items(), key=lambda x: -x[1])[:5]:
                lines.append(f"    {et}: {count}")

        lines.extend([
            "",
            "*Vendors*",
            f"  Active: {len(vendors)}",
            f"  ZIP coverage: {coverage['total_covered_zips']}",
            f"  Coverage gaps: {coverage['gap_count']}",
            "",
            "*Vendor Pipeline*",
            f"  Discovered: {funnel['discovered']}",
            f"  Invited: {funnel['invited']} ({funnel['invite_rate']}%)",
            f"  Signed up: {funnel['signed_up']} ({funnel['signup_rate']}%)",
            "",
            "*SEO*",
            f"  Clicks: {seo['total_clicks']}",
            f"  Impressions: {seo['total_impressions']}",
            f"  Avg CTR: {seo['avg_ctr']}%",
            f"  Avg position: {seo['avg_position']}",
            "",
            "───────────────────",
            "_Reply 'abpstatus' for live snapshot_",
        ])

        return "\n".join(lines)

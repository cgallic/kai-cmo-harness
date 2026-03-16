"""
Follow-Up Manager — monitors email queue, detects gaps, alerts on failures.

Schedule: Every 10 minutes (*/10 * * * *)

Each tick:
1. Check pending emails older than 10 min → auto-send if business allows
2. Check completed calls with no email queued → alert gap
3. Check failed sends → alert with error details
4. Daily digest at end of day
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import kai_client


class FollowUpManagerTask(BaseTask):
    """Monitors and fixes the email follow-up chain."""

    @property
    def task_type(self) -> str:
        return "kai_followup"

    @property
    def description(self) -> str:
        return "Kai Calls: Monitor email follow-ups, auto-send, detect gaps"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        alerts: List[str] = []
        actions_taken: List[str] = []

        try:
            # 1. Handle pending emails
            pending_result = await self._handle_pending_emails()
            actions_taken.extend(pending_result.get("actions", []))
            alerts.extend(pending_result.get("alerts", []))

            # 2. Check for follow-up gaps
            gap_alerts = await self._check_followup_gaps()
            alerts.extend(gap_alerts)

            # 3. Check failed emails
            failed_alerts = await self._check_failed_emails()
            alerts.extend(failed_alerts)

            # 4. Update daily stats
            await self._update_daily_stats(actions_taken, alerts)

            # 5. Send alerts if any
            if alerts:
                alert_msg = "*KaiCalls Follow-Up Alerts*\n\n" + "\n\n".join(alerts)
                await self.send_notification(alert_msg)

            summary_parts = []
            if actions_taken:
                summary_parts.append(f"{len(actions_taken)} actions taken")
            if alerts:
                summary_parts.append(f"{len(alerts)} alerts")
            if not summary_parts:
                summary_parts.append("All clear")

            return {
                "success": True,
                "summary": f"Follow-up check: {', '.join(summary_parts)}",
                "data": {
                    "actions": actions_taken,
                    "alerts": alerts,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def _handle_pending_emails(self) -> Dict[str, Any]:
        """Process pending emails — auto-send or track stale ones."""
        actions = []
        alerts = []

        # Get pending emails older than 10 minutes
        stale = await kai_client.get_stale_emails(minutes=10)

        if not stale:
            return {"actions": actions, "alerts": alerts}

        # Try auto-send for auto-approve businesses
        try:
            result = await kai_client.auto_send_queue()
            sent = result.get("sent", 0)
            if sent > 0:
                actions.append(f"Auto-sent {sent} emails")
        except Exception as e:
            alerts.append(f"Auto-send failed: {str(e)}")

        # Re-check for still-pending stale emails (>1h = alert)
        very_stale = await kai_client.get_stale_emails(minutes=60)
        if very_stale:
            for email in very_stale[:5]:  # Cap at 5 alerts
                biz_name = email.get("businesses", {}).get("name", "Unknown")
                lead_name = email.get("leads", {}).get("name", "Unknown")
                age_min = _age_minutes(email.get("created_at", ""))
                alerts.append(
                    f"Stale email ({age_min}min): {biz_name} → {lead_name}\n"
                    f"Subject: {email.get('subject', 'N/A')[:60]}"
                )

        return {"actions": actions, "alerts": alerts}

    async def _check_followup_gaps(self) -> List[str]:
        """Find completed calls with no follow-up email queued."""
        alerts = []

        # Get calls from last 2 hours with duration > 10s
        calls = await kai_client.get_recent_calls(hours=2)
        completed_calls = [
            c for c in calls
            if (c.get("duration") or 0) > 10
            and c.get("status") in (None, "completed", "ended")
        ]

        if not completed_calls:
            return alerts

        # Get all email queue entries for these calls
        call_ids = [c["id"] for c in completed_calls]
        emails_result = (
            kai_client.supabase.table("email_approval_queue")
            .select("trigger_call_id")
            .in_("trigger_call_id", call_ids)
            .execute()
        )
        emailed_call_ids = {e["trigger_call_id"] for e in (emails_result.data or [])}

        # Find gaps — calls with no email
        for call in completed_calls:
            if call["id"] not in emailed_call_ids:
                age = _age_minutes(call.get("created_at", ""))
                if age > 20:  # Only alert if >20min old (give pipeline time)
                    alerts.append(
                        f"Follow-up gap: Call {call['id'][:8]}... ended {age}min ago, no email queued"
                    )

        return alerts[:5]  # Cap alerts

    async def _check_failed_emails(self) -> List[str]:
        """Check for recently failed email sends."""
        alerts = []

        failed = await kai_client.get_failed_emails(hours=4)
        for email in failed[:3]:  # Cap at 3
            biz_name = email.get("businesses", {}).get("name", "Unknown")
            error = email.get("error_message", "Unknown error")
            alerts.append(
                f"Failed email for {biz_name}: {error[:100]}"
            )

        return alerts

    async def _update_daily_stats(self, actions: List[str], alerts: List[str]):
        """Track daily cumulative stats for end-of-day digest."""
        ctx = state_manager.get_task_context("kai_followup_daily")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Reset if new day
        if ctx.get("date") != today:
            ctx = {
                "date": today,
                "auto_sent": 0,
                "alerts_total": 0,
                "gaps_found": 0,
                "ticks": 0,
            }

        ctx["ticks"] = ctx.get("ticks", 0) + 1
        ctx["alerts_total"] = ctx.get("alerts_total", 0) + len(alerts)

        for action in actions:
            if "Auto-sent" in action:
                try:
                    count = int(action.split("Auto-sent ")[1].split(" ")[0])
                    ctx["auto_sent"] = ctx.get("auto_sent", 0) + count
                except (IndexError, ValueError):
                    pass

        gap_count = sum(1 for a in alerts if "Follow-up gap" in a)
        ctx["gaps_found"] = ctx.get("gaps_found", 0) + gap_count

        state_manager.set_task_context("kai_followup_daily", ctx)


def _age_minutes(iso_timestamp: str) -> int:
    """Calculate minutes since an ISO timestamp."""
    if not iso_timestamp:
        return 0
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return int(delta.total_seconds() / 60)
    except (ValueError, TypeError):
        return 0

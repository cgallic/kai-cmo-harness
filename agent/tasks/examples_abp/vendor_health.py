"""
Vendor Health Monitor — tracks coverage gaps, discovered vendor funnel.

Schedule: Every 6 hours (0 */6 * * *)

Checks:
1. ZIP code coverage gaps (leads with no vendors)
2. Discovered vendors pending signup >48h
3. Vendor discovery-to-signup conversion funnel
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import abp_client


class VendorHealthTask(BaseTask):
    """Monitors vendor health and coverage for ABP."""

    @property
    def task_type(self) -> str:
        return "abp_vendor_health"

    @property
    def description(self) -> str:
        return "ABP: Monitor vendor coverage gaps, discovery funnel, pending signups"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            alerts: List[str] = []

            # 1. Coverage analysis
            coverage = await abp_client.get_vendor_coverage()
            if coverage["gap_count"] > 0:
                top_gaps = list(coverage["gap_zips"].items())[:5]
                gap_lines = [f"  - ZIP {zc}: {count} leads, 0 vendors" for zc, count in top_gaps]
                alerts.append(
                    f"{coverage['gap_count']} ZIP(s) with leads but no vendors:\n"
                    + "\n".join(gap_lines)
                )

            # 2. Vendor discovery funnel
            funnel = await abp_client.get_vendor_funnel()

            # 3. Pending signups (invited >48h ago, not signed up)
            pending = await abp_client.get_pending_vendor_signups(hours=48)
            if pending:
                alerts.append(
                    f"{len(pending)} discovered vendor(s) invited >48h ago, not signed up"
                )

            # 4. Vendors list for count
            vendors = await abp_client.get_vendors()

            # 5. Send alerts
            if alerts:
                msg = "*ABP Vendor Health*\n\n"
                msg += f"Active vendors: {len(vendors)}\n"
                msg += f"Covered ZIPs: {coverage['total_covered_zips']}\n"
                msg += f"Demand ZIPs: {coverage['total_demand_zips']}\n"
                msg += f"Gap ZIPs: {coverage['gap_count']}\n\n"
                msg += f"Discovery funnel: {funnel['discovered']} found → "
                msg += f"{funnel['invited']} invited → "
                msg += f"{funnel['signed_up']} signed up\n\n"
                msg += "Alerts:\n" + "\n".join(f"- {a}" for a in alerts)
                await self.send_notification(msg)

            # 6. Store for trending
            state_manager.set_task_context("abp_vendor_health", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_vendors": len(vendors),
                "covered_zips": coverage["total_covered_zips"],
                "gap_zips": coverage["gap_count"],
                "funnel": funnel,
                "pending_signups": len(pending),
            })

            return {
                "success": True,
                "summary": (
                    f"Vendors: {len(vendors)}, "
                    f"Coverage gaps: {coverage['gap_count']}, "
                    f"Pending signups: {len(pending)}"
                ),
                "data": {
                    "vendors": len(vendors),
                    "coverage": coverage,
                    "funnel": funnel,
                    "alerts": alerts,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

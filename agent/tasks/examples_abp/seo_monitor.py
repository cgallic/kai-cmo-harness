"""
SEO Monitor — tracks page performance changes from GSC data.

Schedule: Daily 6 AM (0 6 * * *)

Checks:
1. Position drops (pages that lost >3 positions)
2. CTR anomalies (pages with impressions but very low CTR)
3. Top growing pages (biggest click gains)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTask
from ...models import ScheduledTask
from ...state import state_manager
from .client import abp_client


class SEOMonitorTask(BaseTask):
    """Monitors SEO performance for ABP."""

    @property
    def task_type(self) -> str:
        return "abp_seo_monitor"

    @property
    def description(self) -> str:
        return "ABP: Monitor page performance, position drops, CTR anomalies"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            alerts: List[str] = []

            # Get current performance
            pages = await abp_client.get_page_performance(days=7)
            seo_stats = await abp_client.get_seo_stats()

            if not pages:
                return {
                    "success": True,
                    "summary": "SEO: No page performance data available",
                    "data": {"pages": 0},
                }

            # Compare to previous snapshot
            prev_snapshot = state_manager.get_task_context("abp_seo_snapshot") or {}
            prev_pages = prev_snapshot.get("pages", {})

            # Build current snapshot
            current_pages = {}
            position_drops = []
            ctr_anomalies = []
            growing = []

            for page in pages:
                url = page.get("url", "")
                clicks = page.get("clicks") or 0
                impressions = page.get("impressions") or 0
                position = page.get("position") or 0
                ctr = page.get("ctr") or 0

                current_pages[url] = {
                    "clicks": clicks,
                    "impressions": impressions,
                    "position": position,
                    "ctr": ctr,
                }

                # Check previous data
                if url in prev_pages:
                    prev = prev_pages[url]
                    prev_pos = prev.get("position", 0)
                    prev_clicks = prev.get("clicks", 0)

                    # Position drop >3
                    if position > 0 and prev_pos > 0:
                        pos_change = position - prev_pos
                        if pos_change > 3:
                            position_drops.append({
                                "url": url,
                                "prev_position": prev_pos,
                                "current_position": position,
                                "change": pos_change,
                            })

                    # Click growth
                    click_change = clicks - prev_clicks
                    if click_change > 5:
                        growing.append({
                            "url": url,
                            "prev_clicks": prev_clicks,
                            "current_clicks": clicks,
                            "change": click_change,
                        })

                # CTR anomaly: lots of impressions, very low CTR
                if impressions > 100 and ctr < 0.01:
                    ctr_anomalies.append({
                        "url": url,
                        "impressions": impressions,
                        "ctr": round(ctr * 100, 2),
                        "clicks": clicks,
                    })

            # Build alerts
            if position_drops:
                drops_sorted = sorted(position_drops, key=lambda x: -x["change"])[:5]
                lines = ["Position drops:"]
                for d in drops_sorted:
                    short_url = d["url"].split("/")[-1] or d["url"][-40:]
                    lines.append(
                        f"  - {short_url}: {d['prev_position']:.0f} → {d['current_position']:.0f} "
                        f"(-{d['change']:.0f})"
                    )
                alerts.append("\n".join(lines))

            if ctr_anomalies:
                anomalies_sorted = sorted(ctr_anomalies, key=lambda x: -x["impressions"])[:3]
                lines = ["Low CTR (high impressions):"]
                for a in anomalies_sorted:
                    short_url = a["url"].split("/")[-1] or a["url"][-40:]
                    lines.append(
                        f"  - {short_url}: {a['impressions']} imp, {a['ctr']}% CTR"
                    )
                alerts.append("\n".join(lines))

            if growing:
                growing_sorted = sorted(growing, key=lambda x: -x["change"])[:3]
                lines = ["Growing pages:"]
                for g in growing_sorted:
                    short_url = g["url"].split("/")[-1] or g["url"][-40:]
                    lines.append(
                        f"  - {short_url}: {g['prev_clicks']} → {g['current_clicks']} clicks "
                        f"(+{g['change']})"
                    )
                alerts.append("\n".join(lines))

            # Send report
            if alerts:
                msg = "*ABP SEO Report*\n\n"
                msg += f"Total: {seo_stats['total_clicks']} clicks, "
                msg += f"{seo_stats['total_impressions']} impressions\n"
                msg += f"Avg position: {seo_stats['avg_position']}\n\n"
                msg += "\n\n".join(alerts)
                await self.send_notification(msg)

            # Store snapshot for next comparison
            state_manager.set_task_context("abp_seo_snapshot", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pages": current_pages,
                "stats": seo_stats,
            })

            return {
                "success": True,
                "summary": (
                    f"SEO: {seo_stats['total_clicks']} clicks, "
                    f"{len(position_drops)} drops, {len(growing)} growing"
                ),
                "data": {
                    "stats": seo_stats,
                    "drops": len(position_drops),
                    "anomalies": len(ctr_anomalies),
                    "growing": len(growing),
                    "alerts": alerts,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

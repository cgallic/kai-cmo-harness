"""
Weekly report task - comprehensive strategy analysis.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from .base import BaseTask

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class WeeklyReportTask(BaseTask):
    """
    Weekly strategy report task.

    Generates comprehensive weekly marketing reports using Opus
    for complex reasoning and strategic insights.
    """

    @property
    def task_type(self) -> str:
        return "weekly_report"

    @property
    def description(self) -> str:
        return "Generate comprehensive weekly marketing report"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the weekly report task."""
        client_id = task.client
        if not client_id:
            return {"success": False, "error": "Client ID required for weekly report"}

        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        # Collect data from all sources
        traffic_data = await self._collect_traffic_data(client)
        campaign_data = await self._collect_campaign_data(client)
        content_data = await self._collect_content_data(client)
        lead_data = await self._collect_lead_data(client)
        goals_data = await self._collect_goals_data(client)

        # Generate report using Opus
        report = await self._generate_report(
            client,
            traffic_data,
            campaign_data,
            content_data,
            lead_data,
            goals_data
        )

        # Save report
        report_path = self._save_report(client_id, report)

        return {
            "success": True,
            "summary": f"Weekly report for {client_id} generated:\n{report.get('summary', '')}",
            "data": {
                "report": report,
                "saved_path": report_path
            }
        }

    async def _collect_traffic_data(self, client: Dict) -> str:
        """Collect traffic data for the week."""
        ga_property = client.get("ga_property")
        gsc_site = client.get("gsc_site")

        data_lines = []

        if ga_property:
            try:
                from scripts.analytics.google_analytics import GoogleAnalytics
                ga = GoogleAnalytics()

                overview = ga.get_overview(ga_property, days=7)
                if overview:
                    data_lines.append(f"Sessions: {overview.get('sessions', 'N/A')}")
                    data_lines.append(f"Users: {overview.get('users', 'N/A')}")
                    data_lines.append(f"Page Views: {overview.get('pageviews', 'N/A')}")
                    data_lines.append(f"Bounce Rate: {overview.get('bounce_rate', 'N/A')}%")

                sources = ga.get_traffic_sources(ga_property, days=7)
                if sources:
                    data_lines.append("\nTop Sources:")
                    for src in sources[:5]:
                        data_lines.append(f"  - {src.get('source', 'N/A')}: {src.get('sessions', 0)}")
            except Exception as e:
                data_lines.append(f"GA Error: {e}")

        if gsc_site:
            try:
                from scripts.analytics.search_console import SearchConsole
                gsc = SearchConsole()

                queries = gsc.get_top_queries(gsc_site, days=7, limit=10)
                if queries:
                    data_lines.append("\nTop Search Queries:")
                    for q in queries[:5]:
                        data_lines.append(
                            f"  - {q.get('query', 'N/A')}: "
                            f"pos {q.get('position', 0):.1f}, "
                            f"{q.get('clicks', 0)} clicks"
                        )
            except Exception as e:
                data_lines.append(f"GSC Error: {e}")

        return "\n".join(data_lines) if data_lines else "No traffic data available"

    async def _collect_campaign_data(self, client: Dict) -> str:
        """Collect campaign performance data."""
        try:
            import os
            from scripts.analytics.facebook_ads import FacebookAdsAnalytics

            access_token = os.getenv("META_ACCESS_TOKEN")
            ad_account_id = client.get("meta_ad_account_id") or os.getenv("META_AD_ACCOUNT_ID")

            if not access_token or not ad_account_id:
                return "Meta Ads not configured"

            fb = FacebookAdsAnalytics(access_token, ad_account_id)
            summary = fb.get_account_summary(days=7)

            if summary:
                return (
                    f"Spend: ${summary.get('spend', 0):.2f}\n"
                    f"Results: {summary.get('results', 0)}\n"
                    f"Cost/Result: ${summary.get('cost_per_result', 0):.2f}\n"
                    f"ROAS: {summary.get('roas', 0):.2f}x"
                )
            return "No campaign data available"
        except Exception as e:
            return f"Campaign data error: {e}"

    async def _collect_content_data(self, client: Dict) -> str:
        """Collect content performance data."""
        client_id = client.get("id")
        client_dir = Path(__file__).parent.parent.parent / "clients" / client_id
        outputs_dir = client_dir / "outputs"

        if not outputs_dir.exists():
            return "No content outputs tracked"

        # Count content created this week
        week_ago = datetime.now() - timedelta(days=7)
        content_count = 0

        for content_file in outputs_dir.glob("**/*.md"):
            try:
                mtime = datetime.fromtimestamp(content_file.stat().st_mtime)
                if mtime > week_ago:
                    content_count += 1
            except Exception:
                pass

        return f"Content pieces created this week: {content_count}"

    async def _collect_lead_data(self, client: Dict) -> str:
        """Collect lead generation data."""
        # Check Supabase for lead counts if configured
        supabase_config = client.get("supabase")
        if supabase_config:
            try:
                from scripts.analytics.supabase_analytics import SupabaseAnalytics
                sb = SupabaseAnalytics(
                    url=supabase_config.get("url"),
                    key=supabase_config.get("key")
                )
                overview = sb.get_overview()
                if overview:
                    return f"Total leads: {overview.get('total_leads', 'N/A')}"
            except Exception:
                pass

        return "Lead data not available"

    async def _collect_goals_data(self, client: Dict) -> str:
        """Collect goals progress data."""
        from ..state import state_manager

        client_state = state_manager.get_client_state(client.get("id"))
        goals = client_state.get("goals", {})

        if not goals:
            return "No goals configured"

        lines = []
        for goal_name, goal_data in goals.items():
            target = goal_data.get("target", "N/A")
            current = goal_data.get("current", "N/A")
            lines.append(f"- {goal_name}: {current} / {target}")

        return "\n".join(lines) if lines else "No goals configured"

    async def _generate_report(
        self,
        client: Dict,
        traffic_data: str,
        campaign_data: str,
        content_data: str,
        lead_data: str,
        goals_data: str
    ) -> Dict[str, Any]:
        """Generate the weekly report using Opus."""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"

        system, template = TaskPrompts.get_prompt("weekly_report")
        prompt = template.format(
            client=client.get("name", client.get("id")),
            date_range=date_range,
            traffic_data=traffic_data,
            campaign_data=campaign_data,
            content_data=content_data,
            lead_data=lead_data,
            goals_data=goals_data
        )

        try:
            # Use Opus for weekly reports (complex reasoning)
            report_text = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                system=system,
                max_tokens=4096
            )

            # Extract executive summary
            summary_lines = []
            in_summary = False
            for line in report_text.split("\n"):
                if "executive summary" in line.lower():
                    in_summary = True
                    continue
                if in_summary:
                    if line.strip() and not line.startswith("#"):
                        summary_lines.append(line.strip())
                    elif summary_lines and line.startswith("#"):
                        break

            summary = " ".join(summary_lines[:3]) if summary_lines else report_text[:200]

            return {
                "full_report": report_text,
                "summary": summary,
                "date_range": date_range
            }
        except Exception as e:
            return {"error": str(e)}

    def _save_report(self, client_id: str, report: Dict) -> str:
        """Save the weekly report to file."""
        if "error" in report:
            return ""

        client_dir = Path(__file__).parent.parent.parent / "clients" / client_id
        reports_dir = client_dir / "outputs" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"weekly-report-{date_str}.md"
        filepath = reports_dir / filename

        try:
            content = f"""# Weekly Marketing Report
## {report.get('date_range', 'Week')}

{report.get('full_report', '')}

---
*Generated by CMO Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            filepath.write_text(content)
            return str(filepath)
        except Exception:
            return ""

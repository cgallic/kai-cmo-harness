"""
Daily analytics task - generates morning briefings.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from .base import BaseTask

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class DailyAnalyticsTask(BaseTask):
    """
    Daily analytics briefing task.

    Pulls GA4 and GSC data, generates insights summary.
    """

    @property
    def task_type(self) -> str:
        return "daily_analytics"

    @property
    def description(self) -> str:
        return "Generate daily analytics briefing"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the daily analytics task."""
        client_id = task.client
        if not client_id:
            # Run for all configured clients
            return await self._run_all_clients(task)

        return await self._run_for_client(task, client_id)

    async def _run_all_clients(
        self,
        task: ScheduledTask
    ) -> Dict[str, Any]:
        """Run analytics for all configured clients."""
        from gateway.config import config

        clients = config.get_all_clients()
        results = {}

        for client in clients:
            if client.get("ga_property"):
                try:
                    result = await self._run_for_client(task, client["id"])
                    results[client["id"]] = result
                except Exception as e:
                    results[client["id"]] = {"error": str(e)}

        return {
            "success": True,
            "summary": f"Generated analytics for {len(results)} clients",
            "data": results
        }

    async def _run_for_client(
        self,
        task: ScheduledTask,
        client_id: str
    ) -> Dict[str, Any]:
        """Run analytics for a specific client."""
        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        # Fetch GA4 data
        ga_data = await self._fetch_ga_data(client)

        # Fetch GSC data
        gsc_data = await self._fetch_gsc_data(client)

        # Fetch business data if available
        business_data = await self._fetch_business_data(client)

        # Fetch Stripe MRR data
        stripe_data = await self._fetch_stripe_data()

        # Fetch cold email stats
        cold_email_data = await self._fetch_cold_email_data()

        # Generate analysis using LLM
        system, template = TaskPrompts.get_prompt("daily_analytics")
        prompt = template.format(
            client=client_id,
            ga_data=self._format_ga_data(ga_data),
            gsc_data=self._format_gsc_data(gsc_data),
            business_data=self._format_business_data(business_data),
            stripe_data=self._format_stripe_data(stripe_data),
            cold_email_data=self._format_cold_email_data(cold_email_data)
        )

        analysis = await llm_router.complete(
            prompt=prompt,
            task_type=self.task_type,
            system=system,
            max_tokens=2048
        )

        return {
            "success": True,
            "summary": f"Daily analytics for {client_id}:\n\n{analysis[:500]}...",
            "data": {
                "client": client_id,
                "analysis": analysis,
                "ga_data": ga_data,
                "gsc_data": gsc_data,
                "stripe_data": stripe_data,
                "cold_email_data": cold_email_data,
            }
        }

    async def _fetch_ga_data(self, client: Dict) -> Dict[str, Any]:
        """Fetch Google Analytics data."""
        ga_property = client.get("ga_property")
        if not ga_property:
            return {}

        try:
            from scripts.analytics.google_analytics import GoogleAnalytics
            ga = GoogleAnalytics()
            return {
                "overview": ga.get_overview(ga_property, days=7),
                "sources": ga.get_traffic_sources(ga_property, days=7),
                "pages": ga.get_top_pages(ga_property, days=7, limit=10),
            }
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_gsc_data(self, client: Dict) -> Dict[str, Any]:
        """Fetch Google Search Console data."""
        gsc_site = client.get("gsc_site")
        if not gsc_site:
            return {}

        try:
            from scripts.analytics.search_console import SearchConsole
            gsc = SearchConsole()
            return {
                "queries": gsc.get_top_queries(gsc_site, days=7, limit=20),
                "pages": gsc.get_top_pages(gsc_site, days=7, limit=10),
            }
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_business_data(self, client: Dict) -> Dict[str, Any]:
        """Fetch business metrics from Supabase if configured."""
        supabase_config = client.get("supabase")
        if not supabase_config:
            return {}

        try:
            from scripts.analytics.supabase_analytics import SupabaseAnalytics
            sb = SupabaseAnalytics(
                url=supabase_config.get("url"),
                key=supabase_config.get("key")
            )
            return sb.get_overview()
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_stripe_data(self) -> Dict[str, Any]:
        """Fetch Stripe MRR and subscription data."""
        try:
            from scripts.analytics.stripe_analytics import StripeAnalytics
            stripe = StripeAnalytics()
            return stripe.get_mrr()
        except Exception as e:
            return {"error": str(e)}

    async def _fetch_cold_email_data(self) -> Dict[str, Any]:
        """Fetch cold email campaign analytics."""
        try:
            from gateway.adapters.cold_email_adapter import ColdEmailAdapter
            adapter = ColdEmailAdapter()
            return adapter.get_analytics_summary()
        except Exception as e:
            return {"error": str(e)}

    def _format_ga_data(self, data: Dict) -> str:
        """Format GA data for the prompt."""
        if not data or "error" in data:
            return "No GA data available"

        lines = []
        if "overview" in data and data["overview"]:
            o = data["overview"]
            lines.append(f"Sessions: {o.get('sessions', 'N/A')}")
            lines.append(f"Users: {o.get('users', 'N/A')}")
            lines.append(f"Page Views: {o.get('pageviews', 'N/A')}")
            lines.append(f"Avg Session Duration: {o.get('avg_session_duration', 'N/A')}")
            lines.append(f"Bounce Rate: {o.get('bounce_rate', 'N/A')}%")

        if "sources" in data and data["sources"]:
            lines.append("\nTop Traffic Sources:")
            for source in data["sources"][:5]:
                lines.append(f"  - {source.get('source', 'Unknown')}: {source.get('sessions', 0)} sessions")

        return "\n".join(lines)

    def _format_gsc_data(self, data: Dict) -> str:
        """Format GSC data for the prompt."""
        if not data or "error" in data:
            return "No GSC data available"

        lines = []
        if "queries" in data and data["queries"]:
            lines.append("Top Queries:")
            for query in data["queries"][:10]:
                lines.append(
                    f"  - {query.get('query', 'N/A')}: "
                    f"pos {query.get('position', 0):.1f}, "
                    f"{query.get('clicks', 0)} clicks, "
                    f"{query.get('impressions', 0)} impr"
                )

        return "\n".join(lines)

    def _format_business_data(self, data: Dict) -> str:
        """Format business data for the prompt."""
        if not data or "error" in data:
            return "No business data available"

        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def _format_stripe_data(self, data: Dict) -> str:
        """Format Stripe MRR data for the prompt."""
        if not data or "error" in data:
            return "No Stripe data available"

        lines = [
            f"MRR: ${data.get('mrr', 0):,.2f}",
            f"Active Subscriptions: {data.get('active_subscriptions', 0)}",
        ]

        # At-risk info
        at_risk = data.get("at_risk", {})
        if at_risk.get("count", 0) > 0:
            lines.append(f"At-Risk MRR: ${at_risk.get('mrr', 0):,.2f} ({at_risk.get('count', 0)} subs)")

        # By plan breakdown
        by_plan = data.get("by_plan", {})
        if by_plan:
            lines.append("\nBy Plan:")
            for plan, info in list(by_plan.items())[:5]:
                lines.append(f"  - {plan}: {info.get('count', 0)} subs, ${info.get('mrr', 0):,.2f}/mo")

        return "\n".join(lines)

    def _format_cold_email_data(self, data: Dict) -> str:
        """Format cold email analytics for the prompt."""
        if not data or "error" in data:
            return "No cold email data available"

        lines = []

        # Account stats
        accounts = data.get("accounts", {})
        if accounts:
            lines.append(f"Email Accounts: {accounts.get('total', 0)} total, {accounts.get('warming', 0)} warming, {accounts.get('ready_to_send', 0)} ready")

        # Campaign stats
        campaigns = data.get("campaigns", {})
        if campaigns:
            lines.append(f"Campaigns: {campaigns.get('total', 0)} total, {campaigns.get('active', 0)} active")

        # Totals
        totals = data.get("totals", {})
        if totals:
            lines.append(f"Sent: {totals.get('sent', 0)}, Opened: {totals.get('opened', 0)}, Replied: {totals.get('replied', 0)}")

        # Rates
        rates = data.get("rates", {})
        if rates:
            lines.append(f"Open Rate: {rates.get('open_rate', 0)}%, Reply Rate: {rates.get('reply_rate', 0)}%, Bounce Rate: {rates.get('bounce_rate', 0)}%")

        # Health
        health = data.get("health", {})
        if health:
            lines.append(f"Deliverability: {health.get('deliverability', 0)}% ({health.get('status', 'unknown')})")

        return "\n".join(lines) if lines else "No cold email data available"

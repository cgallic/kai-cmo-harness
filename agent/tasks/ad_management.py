"""
Ad management task - monitors and optimizes paid campaigns.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from .base import BaseTask

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AdManagementTask(BaseTask):
    """
    Ad campaign management task.

    Monitors Meta (Facebook/Instagram) ad performance and provides
    optimization recommendations.
    """

    @property
    def task_type(self) -> str:
        return "ad_management"

    @property
    def description(self) -> str:
        return "Monitor and optimize ad campaigns"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the ad management task."""
        client_id = task.client
        if not client_id:
            return {"success": False, "error": "Client ID required for ad management"}

        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        # Fetch ad data
        ad_data = await self._fetch_ad_data(client)

        if not ad_data or "error" in ad_data:
            return {
                "success": False,
                "error": ad_data.get("error", "Failed to fetch ad data")
            }

        # Analyze performance
        analysis = await self._analyze_performance(client, ad_data)

        return {
            "success": True,
            "summary": f"Ad analysis for {client_id}:\n{analysis.get('summary', '')}",
            "data": {
                "ad_data": ad_data,
                "analysis": analysis
            }
        }

    async def _fetch_ad_data(self, client: Dict) -> Dict[str, Any]:
        """Fetch ad performance data from Meta."""
        try:
            from scripts.analytics.facebook_ads import FacebookAdsAnalytics

            # Check for Meta credentials
            import os
            access_token = os.getenv("META_ACCESS_TOKEN")
            ad_account_id = client.get("meta_ad_account_id") or os.getenv("META_AD_ACCOUNT_ID")

            if not access_token or not ad_account_id:
                return {"error": "Meta Ads credentials not configured"}

            fb = FacebookAdsAnalytics(
                access_token=access_token,
                ad_account_id=ad_account_id
            )

            return {
                "campaigns": fb.get_campaigns(days=7),
                "adsets": fb.get_adsets(days=7),
                "ads": fb.get_ads(days=7),
                "summary": fb.get_account_summary(days=7)
            }
        except ImportError:
            return {"error": "Facebook Ads module not available"}
        except Exception as e:
            return {"error": str(e)}

    async def _analyze_performance(
        self,
        client: Dict,
        ad_data: Dict
    ) -> Dict[str, Any]:
        """Analyze ad performance using LLM."""
        # Format data for prompt
        campaign_summary = self._format_campaigns(ad_data.get("campaigns", []))
        adset_summary = self._format_adsets(ad_data.get("adsets", []))
        creative_summary = self._format_ads(ad_data.get("ads", []))
        budget_summary = self._format_budget(ad_data.get("summary", {}))

        system, template = TaskPrompts.get_prompt("ad_management")
        prompt = template.format(
            client=client.get("name", client.get("id")),
            campaign_data=campaign_summary,
            adset_data=adset_summary,
            creative_data=creative_summary,
            budget_data=budget_summary
        )

        try:
            analysis = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                system=system,
                max_tokens=2048
            )

            # Extract summary for notification
            summary_lines = analysis.split("\n")[:5]
            summary = "\n".join(summary_lines)

            return {
                "full_analysis": analysis,
                "summary": summary,
                "recommendations": self._extract_recommendations(analysis)
            }
        except Exception as e:
            return {"error": str(e)}

    def _format_campaigns(self, campaigns: List[Dict]) -> str:
        """Format campaign data for the prompt."""
        if not campaigns:
            return "No campaign data available"

        lines = []
        for c in campaigns[:10]:
            lines.append(
                f"- {c.get('name', 'Unknown')}: "
                f"Spend ${c.get('spend', 0):.2f}, "
                f"ROAS {c.get('roas', 0):.2f}x, "
                f"Status: {c.get('status', 'unknown')}"
            )
        return "\n".join(lines)

    def _format_adsets(self, adsets: List[Dict]) -> str:
        """Format adset data for the prompt."""
        if not adsets:
            return "No adset data available"

        lines = []
        for a in adsets[:15]:
            lines.append(
                f"- {a.get('name', 'Unknown')}: "
                f"Spend ${a.get('spend', 0):.2f}, "
                f"CPC ${a.get('cpc', 0):.2f}, "
                f"CTR {a.get('ctr', 0):.2f}%"
            )
        return "\n".join(lines)

    def _format_ads(self, ads: List[Dict]) -> str:
        """Format ad creative data for the prompt."""
        if not ads:
            return "No ad creative data available"

        lines = []
        for a in ads[:20]:
            lines.append(
                f"- {a.get('name', 'Unknown')}: "
                f"Impressions {a.get('impressions', 0)}, "
                f"Clicks {a.get('clicks', 0)}, "
                f"CTR {a.get('ctr', 0):.2f}%"
            )
        return "\n".join(lines)

    def _format_budget(self, summary: Dict) -> str:
        """Format budget data for the prompt."""
        if not summary:
            return "No budget data available"

        return (
            f"Total Spend: ${summary.get('spend', 0):.2f}\n"
            f"Daily Budget: ${summary.get('daily_budget', 0):.2f}\n"
            f"Total Results: {summary.get('results', 0)}\n"
            f"Cost Per Result: ${summary.get('cost_per_result', 0):.2f}"
        )

    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract actionable recommendations from analysis."""
        recommendations = []

        # Look for recommendation sections
        lines = analysis.split("\n")
        in_recommendations = False

        for line in lines:
            lower = line.lower()
            if "recommendation" in lower or "action" in lower or "optimize" in lower:
                in_recommendations = True
                continue

            if in_recommendations and line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.strip().lstrip("-•*0123456789. ")
                if rec and len(rec) > 10:
                    recommendations.append(rec)

        return recommendations[:5]

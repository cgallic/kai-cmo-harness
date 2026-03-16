"""
SEO optimization task - identifies and acts on ranking opportunities.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from .base import BaseTask

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class SEOOptimizationTask(BaseTask):
    """
    SEO optimization task.

    Analyzes Search Console data to identify:
    - Quick wins (position 4-20 with high impressions)
    - Content gaps
    - Technical issues
    """

    @property
    def task_type(self) -> str:
        return "seo_optimization"

    @property
    def description(self) -> str:
        return "Identify and prioritize SEO opportunities"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the SEO optimization task."""
        client_id = task.client
        if not client_id:
            return await self._run_all_clients(task)

        return await self._run_for_client(task, client_id)

    async def _run_all_clients(self, task: ScheduledTask) -> Dict[str, Any]:
        """Run SEO analysis for all configured clients."""
        from gateway.config import config

        clients = config.get_all_clients()
        results = {}

        for client in clients:
            if client.get("gsc_site"):
                try:
                    result = await self._run_for_client(task, client["id"])
                    results[client["id"]] = result
                except Exception as e:
                    results[client["id"]] = {"error": str(e)}

        total_opportunities = sum(
            len(r.get("data", {}).get("opportunities", []))
            for r in results.values()
            if isinstance(r, dict) and "data" in r
        )

        return {
            "success": True,
            "summary": f"Found {total_opportunities} SEO opportunities across {len(results)} clients",
            "data": results
        }

    async def _run_for_client(
        self,
        task: ScheduledTask,
        client_id: str
    ) -> Dict[str, Any]:
        """Run SEO analysis for a specific client."""
        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        gsc_site = client.get("gsc_site")
        if not gsc_site:
            return {"success": False, "error": "No GSC site configured"}

        # Fetch ranking opportunities
        opportunities = await self._fetch_opportunities(gsc_site)

        # Fetch technical issues (if we have access)
        technical_issues = await self._fetch_technical_issues(client)

        # Analyze and prioritize
        analysis = await self._analyze_opportunities(
            client, opportunities, technical_issues
        )

        return {
            "success": True,
            "summary": f"SEO analysis for {client_id}:\n{analysis.get('summary', '')}",
            "data": {
                "opportunities": opportunities,
                "technical_issues": technical_issues,
                "analysis": analysis
            }
        }

    async def _fetch_opportunities(self, gsc_site: str) -> List[Dict]:
        """Fetch ranking opportunities from GSC."""
        try:
            from scripts.analytics.search_console import SearchConsole
            gsc = SearchConsole()

            # Get queries in positions 4-20 with good impressions
            queries = gsc.get_opportunities(gsc_site, days=30)
            return queries
        except Exception as e:
            return [{"error": str(e)}]

    async def _fetch_technical_issues(self, client: Dict) -> List[Dict]:
        """Fetch technical SEO issues."""
        # This would integrate with a crawler or GSC coverage API
        # For now, return empty list
        return []

    async def _analyze_opportunities(
        self,
        client: Dict,
        opportunities: List[Dict],
        technical_issues: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze SEO opportunities using LLM."""
        # Format data for prompt
        ranking_opps = self._format_opportunities(opportunities)
        tech_issues = self._format_technical_issues(technical_issues)

        system, template = TaskPrompts.get_prompt("seo_optimization")
        prompt = template.format(
            client=client.get("name", client.get("id")),
            ranking_opportunities=ranking_opps,
            technical_issues=tech_issues,
            content_gaps="See ranking opportunities for content gap analysis",
            competitor_data="Not available"
        )

        try:
            analysis = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                system=system,
                max_tokens=2048
            )

            # Extract quick wins for summary
            quick_wins = self._extract_quick_wins(analysis)
            summary = "Quick wins:\n" + "\n".join(f"• {w}" for w in quick_wins[:3])

            return {
                "full_analysis": analysis,
                "summary": summary,
                "quick_wins": quick_wins,
                "content_priorities": self._extract_content_priorities(analysis)
            }
        except Exception as e:
            return {"error": str(e)}

    def _format_opportunities(self, opportunities: List[Dict]) -> str:
        """Format ranking opportunities for the prompt."""
        if not opportunities or "error" in opportunities[0]:
            return "No ranking data available"

        lines = []
        for opp in opportunities[:20]:
            lines.append(
                f"- Query: \"{opp.get('query', 'N/A')}\"\n"
                f"  Position: {opp.get('position', 0):.1f}, "
                f"Impressions: {opp.get('impressions', 0)}, "
                f"Clicks: {opp.get('clicks', 0)}, "
                f"CTR: {opp.get('ctr', 0):.2f}%"
            )
        return "\n".join(lines)

    def _format_technical_issues(self, issues: List[Dict]) -> str:
        """Format technical issues for the prompt."""
        if not issues:
            return "No technical issues detected"

        lines = []
        for issue in issues[:10]:
            lines.append(
                f"- {issue.get('type', 'Unknown')}: "
                f"{issue.get('description', 'No description')}"
            )
        return "\n".join(lines)

    def _extract_quick_wins(self, analysis: str) -> List[str]:
        """Extract quick wins from the analysis."""
        quick_wins = []
        lines = analysis.split("\n")
        in_quick_wins = False

        for line in lines:
            lower = line.lower()
            if "quick win" in lower:
                in_quick_wins = True
                continue

            if in_quick_wins:
                if line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                    win = line.strip().lstrip("-•*0123456789. ")
                    if win and len(win) > 10:
                        quick_wins.append(win)
                elif quick_wins and not line.strip():
                    break

        return quick_wins[:5]

    def _extract_content_priorities(self, analysis: str) -> List[str]:
        """Extract content priorities from the analysis."""
        priorities = []
        lines = analysis.split("\n")
        in_content = False

        for line in lines:
            lower = line.lower()
            if "content" in lower and ("priorit" in lower or "recommend" in lower):
                in_content = True
                continue

            if in_content:
                if line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                    priority = line.strip().lstrip("-•*0123456789. ")
                    if priority and len(priority) > 10:
                        priorities.append(priority)
                elif priorities and not line.strip():
                    break

        return priorities[:5]

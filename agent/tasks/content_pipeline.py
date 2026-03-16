"""
Content pipeline task - generates content drafts.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..llm import llm_router, TaskPrompts
from ..models import ScheduledTask
from ..state import state_manager
from .base import BaseTask

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ContentPipelineTask(BaseTask):
    """
    Content generation pipeline task.

    Generates content based on:
    - SEO opportunities from GSC
    - Trending topics
    - Content calendar
    """

    @property
    def task_type(self) -> str:
        return "content_pipeline"

    @property
    def description(self) -> str:
        return "Generate content drafts"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the content pipeline task."""
        client_id = task.client
        if not client_id:
            return {"success": False, "error": "Client ID required for content generation"}

        from gateway.config import config
        client = config.get_client(client_id)

        if not client:
            return {"success": False, "error": f"Unknown client: {client_id}"}

        # Get content opportunities
        opportunities = await self._identify_opportunities(client)

        if not opportunities:
            return {
                "success": True,
                "summary": "No content opportunities identified",
                "data": {"opportunities": []}
            }

        # Generate content for top opportunities
        drafts = []
        for opp in opportunities[:3]:  # Limit to 3 pieces per run
            draft = await self._generate_draft(client, opp)
            if draft:
                drafts.append(draft)

        # Save drafts
        saved_paths = self._save_drafts(client_id, drafts)

        return {
            "success": True,
            "summary": f"Generated {len(drafts)} content drafts for {client_id}",
            "data": {
                "drafts": drafts,
                "saved_paths": saved_paths
            }
        }

    async def _identify_opportunities(self, client: Dict) -> List[Dict]:
        """Identify content opportunities from various sources."""
        opportunities = []

        # GSC ranking opportunities (position 4-20)
        gsc_site = client.get("gsc_site")
        if gsc_site:
            try:
                from scripts.analytics.search_console import SearchConsole
                gsc = SearchConsole()
                queries = gsc.get_opportunities(gsc_site, days=30)
                for q in queries[:5]:
                    opportunities.append({
                        "type": "seo",
                        "topic": q.get("query"),
                        "keywords": [q.get("query")],
                        "priority": "high" if q.get("position", 0) < 10 else "medium",
                        "metrics": {
                            "position": q.get("position"),
                            "impressions": q.get("impressions"),
                            "clicks": q.get("clicks")
                        }
                    })
            except Exception:
                pass

        # Content gaps from task context
        task_context = state_manager.get_task_context(f"content_{client.get('id')}")
        if "content_gaps" in task_context:
            for gap in task_context["content_gaps"][:3]:
                opportunities.append({
                    "type": "gap",
                    "topic": gap,
                    "keywords": [],
                    "priority": "medium"
                })

        return opportunities

    async def _generate_draft(
        self,
        client: Dict,
        opportunity: Dict
    ) -> Optional[Dict]:
        """Generate a content draft for an opportunity."""
        topic = opportunity.get("topic", "")
        keywords = opportunity.get("keywords", [])
        content_type = opportunity.get("type", "blog")

        # Get brand voice if available
        brand_voice = self._get_brand_voice(client)

        # Get previous high-performing content
        previous_content = self._get_previous_content(client)

        system, template = TaskPrompts.get_prompt("content_pipeline")
        prompt = template.format(
            client=client.get("name", client.get("id")),
            content_type=content_type,
            topic=topic,
            keywords=", ".join(keywords) if keywords else "N/A",
            brand_voice=brand_voice,
            previous_content=previous_content
        )

        try:
            content = await llm_router.complete(
                prompt=prompt,
                task_type=self.task_type,
                system=system,
                max_tokens=4096
            )

            return {
                "topic": topic,
                "type": content_type,
                "content": content,
                "keywords": keywords,
                "status": "draft"
            }
        except Exception as e:
            return {"topic": topic, "error": str(e)}

    def _get_brand_voice(self, client: Dict) -> str:
        """Get brand voice guidelines for the client."""
        # Check for brand voice in client config
        brand_voice = client.get("brand_voice")
        if brand_voice:
            return brand_voice

        # Default guidelines
        return """
- Professional but approachable tone
- Use active voice
- Be specific with examples
- Avoid jargon unless necessary
- Focus on reader benefits
"""

    def _get_previous_content(self, client: Dict) -> str:
        """Get examples of previous high-performing content."""
        client_id = client.get("id")
        client_dir = Path(__file__).parent.parent.parent / "clients" / client_id

        # Check for outputs directory
        outputs_dir = client_dir / "outputs"
        if not outputs_dir.exists():
            return "No previous content available"

        # Find recent content files
        content_files = list(outputs_dir.glob("**/*.md"))[:3]
        if not content_files:
            return "No previous content available"

        examples = []
        for f in content_files:
            try:
                content = f.read_text()[:500]
                examples.append(f"### {f.stem}\n{content}...")
            except Exception:
                pass

        return "\n\n".join(examples) if examples else "No previous content available"

    def _save_drafts(self, client_id: str, drafts: List[Dict]) -> List[str]:
        """Save content drafts to the client's outputs directory."""
        from datetime import datetime

        client_dir = Path(__file__).parent.parent.parent / "clients" / client_id
        outputs_dir = client_dir / "outputs" / "content"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        saved = []
        timestamp = datetime.now().strftime("%Y%m%d")

        for i, draft in enumerate(drafts):
            if "error" in draft:
                continue

            # Sanitize topic for filename
            topic_slug = draft.get("topic", "untitled")[:50]
            topic_slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in topic_slug)
            filename = f"{timestamp}-{topic_slug}-draft.md"

            filepath = outputs_dir / filename
            try:
                filepath.write_text(draft.get("content", ""))
                saved.append(str(filepath))
            except Exception:
                pass

        return saved

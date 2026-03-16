"""
Creative assets task - generates OG images, social graphics, etc.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from ..llm import llm_router
from ..models import ScheduledTask
from .base import BaseTask

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CreativeAssetsTask(BaseTask):
    """
    Creative assets generation task.

    Generates OG images, social graphics, and marketing visuals.
    """

    @property
    def task_type(self) -> str:
        return "creative_assets"

    @property
    def description(self) -> str:
        return "Generate creative marketing assets"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute the creative assets task."""
        from agent.templates.og_image import OGImagePrompt, BRAND_CONFIGS, get_og_prompt

        client_id = task.client
        asset_type = task.config.config.get("asset_type", "og_image") if task.config.config else "og_image"

        if asset_type == "og_image":
            return await self._generate_og_image(task, client_id)
        else:
            return {"success": False, "error": f"Unknown asset type: {asset_type}"}

    async def _generate_og_image(
        self,
        task: ScheduledTask,
        client_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate OG image prompt for a client."""
        from agent.templates.og_image import BRAND_CONFIGS, get_og_prompt, OGImagePrompt

        # Get config from task
        config = task.config.config or {} if task.config else {}

        # Try to get preset for known brand
        if client_id and client_id.lower() in BRAND_CONFIGS:
            custom_headline = config.get("headline")
            prompt = get_og_prompt(client_id.lower(), custom_headline=custom_headline)
            brand_config = BRAND_CONFIGS[client_id.lower()]
            brand_name = brand_config.name
            headline = custom_headline or brand_config.headline
        else:
            # Custom brand
            brand_name = config.get("brand", client_id or "Brand")
            headline = config.get("headline", "Build Something Amazing")
            colors = config.get("colors")
            style = config.get("style")
            prompt = OGImagePrompt.generate(
                brand=brand_name,
                headline=headline,
                colors=colors,
                style=style
            )

        return {
            "success": True,
            "summary": f"Generated OG image prompt for {brand_name}: \"{headline}\"",
            "data": {
                "brand": brand_name,
                "headline": headline,
                "prompt": prompt,
                "usage": "Copy this prompt into Nano Banana Pro or similar AI image generator"
            }
        }

    async def generate_og_for_all_brands(self) -> Dict[str, Any]:
        """Generate OG image prompts for all configured brands."""
        from agent.templates.og_image import BRAND_CONFIGS, get_og_prompt

        results = {}
        for brand_id, config in BRAND_CONFIGS.items():
            prompt = get_og_prompt(brand_id)
            results[brand_id] = {
                "brand": config.name,
                "headline": config.headline,
                "prompt": prompt
            }

        return {
            "success": True,
            "summary": f"Generated OG prompts for {len(results)} brands",
            "data": results
        }

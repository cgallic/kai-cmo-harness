"""
Creative assets router - OG images, social graphics, etc.
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.templates.og_image import OGImagePrompt, BRAND_CONFIGS, get_og_prompt


router = APIRouter()


class OGImageRequest(BaseModel):
    """Request for OG image prompt generation."""
    brand: str  # Brand name or brand_id from BRAND_CONFIGS
    headline: str  # Short headline, 3-6 words
    colors: Optional[str] = None  # e.g., "blue and white"
    style: Optional[str] = None   # e.g., "minimal", "tech-forward"


class OGImageResponse(BaseModel):
    """Response with generated prompt."""
    success: bool
    brand: str
    headline: str
    prompt: str
    usage: str = "Copy this prompt into Nano Banana Pro or similar AI image generator"


@router.post("/og-image/prompt", response_model=OGImageResponse)
async def generate_og_prompt(request: OGImageRequest):
    """
    Generate an OG image prompt for Nano Banana Pro.

    Returns a ready-to-use prompt for generating premium 16:9 open-graph images.

    Example:
        POST /webhooks/creative/og-image/prompt
        {
            "brand": "Kai Calls",
            "headline": "AI Voice Agents for Business",
            "colors": "deep blue and white",
            "style": "tech-forward"
        }
    """
    try:
        prompt = OGImagePrompt.generate(
            brand=request.brand,
            headline=request.headline,
            colors=request.colors,
            style=request.style
        )

        return OGImageResponse(
            success=True,
            brand=request.brand,
            headline=request.headline,
            prompt=prompt
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/og-image/brands")
async def list_brand_configs():
    """
    List pre-configured brand settings for OG images.

    Returns available brand_ids that can be used with /og-image/preset endpoint.
    """
    return {
        "brands": {
            brand_id: {
                "name": config.name,
                "headline": config.headline,
                "colors": config.colors,
                "style": config.style
            }
            for brand_id, config in BRAND_CONFIGS.items()
        }
    }


@router.get("/og-image/preset/{brand_id}")
async def get_preset_prompt(brand_id: str, headline: Optional[str] = None):
    """
    Get OG image prompt for a pre-configured brand.

    Args:
        brand_id: One of kaicalls, indexify, vocalscribe, buildwithkai, kompete
        headline: Optional custom headline (overrides default)

    Returns:
        Ready-to-use prompt for Nano Banana Pro
    """
    try:
        prompt = get_og_prompt(brand_id, custom_headline=headline)
        config = BRAND_CONFIGS[brand_id]

        return OGImageResponse(
            success=True,
            brand=config.name,
            headline=headline or config.headline,
            prompt=prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

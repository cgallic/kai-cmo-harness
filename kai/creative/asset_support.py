"""Creative asset support for the Kai Marketing OS.

Defines structured models for visual and video asset specifications,
an asset request workflow, and status tracking.  These models describe
*what* to produce with enough detail that a designer, Canva user, or
automated design tool can execute without follow-up questions.

Design principles
-----------------
1. **Specification, not production.**  This module produces precise
   specs -- it does not generate images or video.
2. **Platform-aware.**  Dimensions and aspect ratios are pre-computed
   for every major platform/content-type combination.
3. **Lifecycle tracking.**  ``AssetRequest`` follows the full workflow
   from ``requested`` through ``approved`` or ``rejected``.
4. **Brand-consistent.**  Every spec can reference brand colors, logos,
   and style guidelines from the business profile.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json
            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Enums
# ============================================================================


class AssetType(str, Enum):
    """Category of creative asset."""

    IMAGE = "image"
    BEFORE_AFTER = "before_after"
    TESTIMONIAL_GRAPHIC = "testimonial_graphic"
    OFFER_GRAPHIC = "offer_graphic"
    VIDEO_REEL = "video_reel"
    VIDEO_LONG = "video_long"
    CAROUSEL = "carousel"
    INFOGRAPHIC = "infographic"
    LOGO_VARIANT = "logo_variant"
    SOCIAL_COVER = "social_cover"


class AssetStatus(str, Enum):
    """Lifecycle status of an asset request."""

    REQUESTED = "requested"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


# ============================================================================
# Constants
# ============================================================================


PLATFORM_DIMENSIONS: Dict[Tuple[str, str], Dict[str, str]] = {
    ("instagram", "post"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
    ("instagram", "story"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
    ("instagram", "reel"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
    ("instagram", "carousel"): {"dimensions": "1080x1350", "aspect_ratio": "4:5"},
    ("facebook", "post"): {"dimensions": "1200x630", "aspect_ratio": "1.91:1"},
    ("facebook", "story"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
    ("facebook", "ad"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
    ("linkedin", "post"): {"dimensions": "1200x627", "aspect_ratio": "1.91:1"},
    ("linkedin", "carousel"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
    ("tiktok", "video"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
    ("youtube", "thumbnail"): {"dimensions": "1280x720", "aspect_ratio": "16:9"},
    ("youtube", "short"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
    ("twitter", "post"): {"dimensions": "1200x675", "aspect_ratio": "16:9"},
    ("pinterest", "pin"): {"dimensions": "1000x1500", "aspect_ratio": "2:3"},
    ("google_ads", "display"): {"dimensions": "1200x628", "aspect_ratio": "1.91:1"},
    ("website", "hero"): {"dimensions": "1920x1080", "aspect_ratio": "16:9"},
    ("website", "section"): {"dimensions": "1200x800", "aspect_ratio": "3:2"},
    ("email", "header"): {"dimensions": "600x200", "aspect_ratio": "3:1"},
}

# Default dimensions when platform/content_type combo is not found.
_DEFAULT_DIMENSIONS = {"dimensions": "1080x1080", "aspect_ratio": "1:1"}


# ============================================================================
# ID Generators
# ============================================================================


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ============================================================================
# Data Models
# ============================================================================


class ImageConcept(BaseModel):
    """Detailed specification for a static image asset."""

    id: str = Field(default_factory=lambda: _gen_id("img"))
    description: str = ""
    dimensions: str = "1080x1080"
    aspect_ratio: str = "1:1"
    style_notes: str = "clean and modern"
    color_palette: List[str] = Field(default_factory=list)
    text_overlay: Optional[str] = None
    text_overlay_position: Optional[str] = None
    font_guidance: Optional[str] = None
    brand_elements: List[str] = Field(default_factory=list)
    reference_images: List[str] = Field(default_factory=list)
    platform: str = "website"
    file_format: str = "png"
    background: Optional[str] = None
    mood: Optional[str] = None
    subjects: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BeforeAfterLayout(BaseModel):
    """Specification for a before/after comparison graphic."""

    id: str = Field(default_factory=lambda: _gen_id("ba"))
    before_description: str = ""
    before_image_source: Optional[str] = None
    after_description: str = ""
    after_image_source: Optional[str] = None
    caption: str = ""
    format: str = "side_by_side"
    dimensions: str = "1080x1080"
    platform: str = "website"
    brand_overlay: bool = True
    logo_position: Optional[str] = None
    call_to_action: Optional[str] = None
    project_details: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestimonialGraphic(BaseModel):
    """Specification for a branded testimonial card."""

    id: str = Field(default_factory=lambda: _gen_id("tst"))
    quote: str = ""
    quote_max_words: int = 40
    attribution: str = ""
    star_rating: Optional[int] = None
    review_platform: Optional[str] = None
    customer_photo: Optional[str] = None
    brand_overlay: bool = True
    dimensions: str = "1080x1080"
    platform: str = "website"
    background_style: str = "solid_brand"
    accent_color: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OfferGraphic(BaseModel):
    """Specification for a promotional offer graphic."""

    id: str = Field(default_factory=lambda: _gen_id("ofr"))
    headline: str = ""
    offer_details: str = ""
    cta: str = ""
    urgency_element: Optional[str] = None
    brand_elements: List[str] = Field(default_factory=lambda: ["logo", "brand_colors"])
    dimensions: str = "1080x1080"
    platform: str = "website"
    background_style: str = "bold_color"
    disclaimer: Optional[str] = None
    promo_code: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VideoReelBrief(BaseModel):
    """Specification for a short-form video reel."""

    id: str = Field(default_factory=lambda: _gen_id("vid"))
    hook: str = ""
    hook_text_overlay: str = ""
    main_content: List[Dict[str, Any]] = Field(default_factory=list)
    cta: str = ""
    cta_visual: str = ""
    duration_target: int = 30
    platform: str = "instagram"
    aspect_ratio: str = "9:16"
    music_notes: Optional[str] = None
    text_overlays: List[Dict[str, str]] = Field(default_factory=list)
    b_roll_suggestions: List[str] = Field(default_factory=list)
    filming_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CarouselBrief(BaseModel):
    """Specification for a multi-slide carousel."""

    id: str = Field(default_factory=lambda: _gen_id("car"))
    title: str = ""
    slides: List[Dict[str, Any]] = Field(default_factory=list)
    total_slides: int = 5
    dimensions: str = "1080x1350"
    platform: str = "instagram"
    brand_consistent: bool = True
    swipe_cta: str = "Swipe for more"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetRequest(BaseModel):
    """Tracks an asset through its full lifecycle: requested -> approved."""

    id: str = Field(default_factory=lambda: _gen_id("asr"))
    source_action_id: str = ""
    source_brief_id: str = ""
    asset_type: str = AssetType.IMAGE.value
    asset_spec: Dict[str, Any] = Field(default_factory=dict)
    status: str = AssetStatus.REQUESTED.value
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    delivered_url: Optional[str] = None
    revision_notes: List[str] = Field(default_factory=list)
    approval_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Functions
# ============================================================================


def get_dimensions_for_platform(
    platform: str,
    content_type: str,
) -> Dict[str, str]:
    """Return recommended dimensions for a platform/content-type combo.

    Falls back to 1080x1080 / 1:1 when the combination is not found.
    """
    key = (platform.lower(), content_type.lower())
    return dict(PLATFORM_DIMENSIONS.get(key, _DEFAULT_DIMENSIONS))


def _extract_brand_elements(
    business_profile: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Pull brand colors, logo, and style from a business profile."""
    if not business_profile:
        return {
            "color_palette": [],
            "brand_elements": ["logo", "brand_colors"],
            "style_notes": "clean and modern",
        }

    brand_voice = business_profile.get("brand_voice") or {}
    trust_profile = business_profile.get("trust_profile") or {}
    brand_assets = business_profile.get("brand_assets") or {}

    colors = (
        brand_assets.get("color_palette")
        or brand_assets.get("colors")
        or []
    )
    if isinstance(colors, str):
        colors = [colors]

    elements = ["logo", "brand_colors"]
    if brand_assets.get("tagline"):
        elements.append("tagline")

    tone_descriptors = brand_voice.get("tone_descriptors") or []
    style = "clean and modern"
    if isinstance(tone_descriptors, list):
        if "playful" in tone_descriptors:
            style = "bold and energetic"
        elif "formal" in tone_descriptors or "authoritative" in tone_descriptors:
            style = "professional and refined"
        elif "warm" in tone_descriptors or "friendly" in tone_descriptors:
            style = "warm and inviting"

    return {
        "color_palette": colors,
        "brand_elements": elements,
        "style_notes": style,
    }


def _build_testimonial_spec(
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a TestimonialGraphic spec from a brief."""
    brand = _extract_brand_elements(business_profile)
    platform = brief.get("channel", "website")
    dims = get_dimensions_for_platform(platform, "post")

    spec = TestimonialGraphic(
        quote=brief.get("key_message", "[Customer testimonial quote]"),
        attribution="[Customer Name, City]",
        star_rating=5,
        review_platform="google",
        brand_overlay=True,
        dimensions=dims["dimensions"],
        platform=platform,
        background_style="solid_brand",
        accent_color=brand["color_palette"][0] if brand["color_palette"] else None,
    )
    return spec.model_dump()


def _build_offer_spec(
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build an OfferGraphic spec from a brief."""
    brand = _extract_brand_elements(business_profile)
    platform = brief.get("channel", "website")
    dims = get_dimensions_for_platform(platform, "post")

    spec = OfferGraphic(
        headline=brief.get("offer", "[Offer Headline]"),
        offer_details=brief.get("offer_details", "[Offer details and terms]"),
        cta=brief.get("cta", "Get Started"),
        urgency_element=brief.get("metadata", {}).get("urgency"),
        brand_elements=brand["brand_elements"],
        dimensions=dims["dimensions"],
        platform=platform,
        background_style="bold_color",
        disclaimer=brief.get("compliance_notes", [""])[0] if brief.get("compliance_notes") else None,
        promo_code=brief.get("metadata", {}).get("promo_code"),
    )
    return spec.model_dump()


def _build_before_after_spec(
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a BeforeAfterLayout spec from a brief."""
    platform = brief.get("channel", "website")
    dims = get_dimensions_for_platform(platform, "post")
    payload_meta = brief.get("metadata") or {}

    spec = BeforeAfterLayout(
        before_description=payload_meta.get("before_description", "[Before state description]"),
        before_image_source=payload_meta.get("before_image"),
        after_description=payload_meta.get("after_description", "[After state description]"),
        after_image_source=payload_meta.get("after_image"),
        caption=brief.get("key_message", "[Before & After caption]"),
        format="side_by_side",
        dimensions=dims["dimensions"],
        platform=platform,
        brand_overlay=True,
        call_to_action=brief.get("cta"),
        project_details=payload_meta.get("project_details"),
    )
    return spec.model_dump()


def _build_video_reel_spec(
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a VideoReelBrief spec from a brief."""
    platform = brief.get("channel", "instagram")
    dims = get_dimensions_for_platform(platform, "reel")
    if not dims or dims == _DEFAULT_DIMENSIONS:
        dims = get_dimensions_for_platform(platform, "video")

    # Parse duration.
    duration_str = brief.get("duration_target", "30 seconds")
    try:
        if isinstance(duration_str, str):
            duration = int(duration_str.split()[0])
        elif isinstance(duration_str, (int, float)):
            duration = int(duration_str)
        else:
            duration = 30
    except (ValueError, IndexError):
        duration = 30

    persona_pain = brief.get("persona_pain_point", "")
    key_message = brief.get("key_message", "")
    cta = brief.get("cta", "")

    main_content = [
        {
            "timestamp_start": "0:00",
            "timestamp_end": "0:03",
            "visual_description": "[Hook visual: face-to-camera or striking image]",
            "narration": f"[Hook line based on pain: {persona_pain[:40]}]",
            "text_overlay": "[Bold text overlay for hook]",
            "transition": "cut",
        },
        {
            "timestamp_start": "0:03",
            "timestamp_end": "0:10",
            "visual_description": "[Problem visual: show the frustration or challenge]",
            "narration": f"[Problem statement: {persona_pain[:40]}]",
            "text_overlay": "[Problem text overlay]",
            "transition": "swipe",
        },
        {
            "timestamp_start": "0:10",
            "timestamp_end": "0:20",
            "visual_description": "[Solution visual: show your service/product in action]",
            "narration": f"[Solution: {key_message[:40]}]",
            "text_overlay": "[Solution text overlay]",
            "transition": "zoom",
        },
        {
            "timestamp_start": "0:20",
            "timestamp_end": f"0:{duration - 5}",
            "visual_description": "[Proof: results, testimonials, before/after]",
            "narration": "[Social proof or specific result]",
            "text_overlay": "[Result stat or quote]",
            "transition": "cut",
        },
        {
            "timestamp_start": f"0:{duration - 5}",
            "timestamp_end": f"0:{duration}",
            "visual_description": "[CTA card with brand elements]",
            "narration": f"[CTA: {cta}]",
            "text_overlay": f"[CTA: {cta}]",
            "transition": "fade",
        },
    ]

    spec = VideoReelBrief(
        hook=f"[3-second hook targeting: {persona_pain[:40]}]",
        hook_text_overlay="[Bold text that stops scrolling]",
        main_content=main_content,
        cta=cta,
        cta_visual="[Branded end card with CTA button graphic]",
        duration_target=duration,
        platform=platform,
        aspect_ratio=dims.get("aspect_ratio", "9:16"),
        music_notes="[Upbeat, trending audio that matches brand tone]",
        text_overlays=[
            {"text": "[Hook text]", "timestamp": "0:00", "style": "bold, large"},
            {"text": f"[CTA: {cta}]", "timestamp": f"0:{duration - 5}", "style": "bold, branded"},
        ],
        b_roll_suggestions=[
            "[Service in progress footage]",
            "[Happy customer reaction]",
            "[Before/after reveal]",
        ],
        filming_notes="Natural lighting preferred. Vertical orientation (9:16). Shoot in 4K for crop flexibility.",
    )
    return spec.model_dump()


def create_asset_request(
    action: Dict[str, Any],
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create an AssetRequest from a ProposedAction and CreativeBrief.

    Determines the asset type from the brief's format and populates
    the full asset specification.

    Parameters
    ----------
    action:
        A ProposedAction dict.
    brief:
        A CreativeBrief dict.
    business_profile:
        Optional BusinessProfile dict for brand information.

    Returns
    -------
    Dict[str, Any]
        An AssetRequest dict with the full asset_spec populated.
    """
    content_format = brief.get("format", "")

    # Map brief format to asset type and spec builder.
    format_to_asset = {
        "testimonial_graphic": (AssetType.TESTIMONIAL_GRAPHIC.value, _build_testimonial_spec),
        "offer_graphic": (AssetType.OFFER_GRAPHIC.value, _build_offer_spec),
        "before_after_graphic": (AssetType.BEFORE_AFTER.value, _build_before_after_spec),
        "social_reel": (AssetType.VIDEO_REEL.value, _build_video_reel_spec),
    }

    if content_format in format_to_asset:
        asset_type, spec_builder = format_to_asset[content_format]
        asset_spec = spec_builder(brief, business_profile)
    else:
        # Default to generic image spec.
        asset_type = AssetType.IMAGE.value
        brand = _extract_brand_elements(business_profile)
        platform = brief.get("channel", "website")
        dims = get_dimensions_for_platform(platform, "post")
        asset_spec = ImageConcept(
            description=brief.get("key_message", "[Image description]"),
            dimensions=dims["dimensions"],
            aspect_ratio=dims["aspect_ratio"],
            style_notes=brand["style_notes"],
            color_palette=brand["color_palette"],
            text_overlay=brief.get("key_message", ""),
            text_overlay_position="center",
            brand_elements=brand["brand_elements"],
            platform=platform,
        ).model_dump()

    now = datetime.now(timezone.utc).isoformat()

    request = AssetRequest(
        source_action_id=action.get("id", ""),
        source_brief_id=brief.get("id", ""),
        asset_type=asset_type,
        asset_spec=asset_spec,
        status=AssetStatus.REQUESTED.value,
        created_at=now,
        updated_at=now,
    )
    return request.model_dump()


def generate_image_specs_for_action(
    action: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate ImageConcept specs for all visual needs of an action.

    For social posts, generates image specs per platform (different
    dimensions).  For website updates, generates specs for the updated
    section.  For ad campaigns, generates ad creative specs per platform.

    Parameters
    ----------
    action:
        A ProposedAction dict.
    business_profile:
        Optional BusinessProfile dict.

    Returns
    -------
    List[Dict[str, Any]]
        A list of ImageConcept dicts with platform-appropriate dimensions.
    """
    action_type = action.get("action_type", "")
    channel = action.get("channel", "website")
    payload = action.get("suggested_payload") or {}
    brand = _extract_brand_elements(business_profile)

    key_message = payload.get("key_message") or action.get("description", "")
    cta = payload.get("cta") or "Learn More"

    specs: List[Dict[str, Any]] = []

    if action_type == "social_post":
        # Generate specs for each target platform.
        platforms = payload.get("platforms") or [channel]
        if isinstance(platforms, str):
            platforms = [platforms]

        for platform in platforms:
            content_type = "post"
            if platform.lower() in ("tiktok", "youtube"):
                content_type = "video"
            elif platform.lower() == "pinterest":
                content_type = "pin"

            dims = get_dimensions_for_platform(platform, content_type)

            spec = ImageConcept(
                description=f"[Social post image for {platform}: {key_message[:60]}]",
                dimensions=dims["dimensions"],
                aspect_ratio=dims["aspect_ratio"],
                style_notes=brand["style_notes"],
                color_palette=brand["color_palette"],
                text_overlay=key_message[:80] if key_message else None,
                text_overlay_position="center",
                brand_elements=brand["brand_elements"],
                platform=platform,
                mood="engaging",
                subjects=[f"[Relevant to: {key_message[:40]}]"],
                avoid=["stock photo look", "clip art", "text-heavy"],
            )
            specs.append(spec.model_dump())

    elif action_type == "website_update":
        page_type = payload.get("page_type", "section")
        content_type = "hero" if page_type in ("homepage", "landing_page") else "section"
        dims = get_dimensions_for_platform("website", content_type)

        spec = ImageConcept(
            description=f"[Website {page_type} image: {key_message[:60]}]",
            dimensions=dims["dimensions"],
            aspect_ratio=dims["aspect_ratio"],
            style_notes=brand["style_notes"],
            color_palette=brand["color_palette"],
            brand_elements=brand["brand_elements"],
            platform="website",
            background="transparent" if page_type == "section" else "photo",
            mood="professional",
            subjects=[f"[Relevant to: {key_message[:40]}]"],
            avoid=["stock photo look", "clip art"],
        )
        specs.append(spec.model_dump())

    elif action_type == "ad_campaign":
        # Generate specs for each ad platform.
        ad_platforms = payload.get("platforms") or [channel]
        if isinstance(ad_platforms, str):
            ad_platforms = [ad_platforms]

        for platform in ad_platforms:
            content_type = "ad" if platform.lower() in ("facebook", "meta") else "display"
            if platform.lower() == "instagram":
                content_type = "post"
            dims = get_dimensions_for_platform(platform, content_type)

            spec = ImageConcept(
                description=f"[Ad creative for {platform}: {key_message[:60]}]",
                dimensions=dims["dimensions"],
                aspect_ratio=dims["aspect_ratio"],
                style_notes=brand["style_notes"],
                color_palette=brand["color_palette"],
                text_overlay=f"[Ad headline + CTA: {cta}]",
                text_overlay_position="center",
                brand_elements=brand["brand_elements"],
                platform=platform,
                mood="bold and attention-grabbing",
                subjects=[f"[Relevant to: {key_message[:40]}]"],
                avoid=["stock photo look", "text-heavy (20% text rule for Meta)"],
            )
            specs.append(spec.model_dump())

    elif action_type == "content_creation":
        # Generic content image.
        content_type_val = payload.get("content_type", "blog_post")
        if content_type_val in ("blog_post", "linkedin_article", "case_study"):
            dims = get_dimensions_for_platform("website", "hero")
            spec = ImageConcept(
                description=f"[Featured image for {content_type_val}: {key_message[:60]}]",
                dimensions=dims["dimensions"],
                aspect_ratio=dims["aspect_ratio"],
                style_notes=brand["style_notes"],
                color_palette=brand["color_palette"],
                brand_elements=brand["brand_elements"],
                platform="website",
                mood="professional",
                file_format="webp",
                subjects=[f"[Relevant to: {key_message[:40]}]"],
                avoid=["stock photo look", "generic imagery"],
            )
            specs.append(spec.model_dump())

    else:
        # Fallback: single generic image.
        dims = get_dimensions_for_platform(channel, "post")
        spec = ImageConcept(
            description=f"[Image for {action_type}: {key_message[:60]}]",
            dimensions=dims["dimensions"],
            aspect_ratio=dims["aspect_ratio"],
            style_notes=brand["style_notes"],
            color_palette=brand["color_palette"],
            brand_elements=brand["brand_elements"],
            platform=channel,
        )
        specs.append(spec.model_dump())

    return specs


def update_asset_status(
    asset_request: Dict[str, Any],
    new_status: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Update the status of an AssetRequest.

    Parameters
    ----------
    asset_request:
        An AssetRequest dict.
    new_status:
        The new AssetStatus value.
    notes:
        Required when ``new_status`` is ``revision_requested`` (added
        to ``revision_notes``).  When ``new_status`` is ``delivered``,
        this should be the delivered asset URL/path (set as
        ``delivered_url``).

    Returns
    -------
    Dict[str, Any]
        The updated AssetRequest dict.

    Raises
    ------
    ValueError
        If ``new_status`` is ``revision_requested`` and ``notes`` is not
        provided.
    """
    # Validate the new status.
    valid_statuses = {s.value for s in AssetStatus}
    if new_status not in valid_statuses:
        raise ValueError(
            f"Invalid status '{new_status}'. Must be one of: {sorted(valid_statuses)}"
        )

    if new_status == AssetStatus.REVISION_REQUESTED.value and not notes:
        raise ValueError(
            "notes parameter is required when setting status to 'revision_requested'. "
            "Provide specific revision instructions."
        )

    # Create a shallow copy to avoid mutating the original.
    updated = dict(asset_request)
    updated["status"] = new_status
    updated["updated_at"] = datetime.now(timezone.utc).isoformat()

    if new_status == AssetStatus.REVISION_REQUESTED.value and notes:
        revision_notes = list(updated.get("revision_notes") or [])
        revision_notes.append(notes)
        updated["revision_notes"] = revision_notes

    if new_status == AssetStatus.DELIVERED.value and notes:
        updated["delivered_url"] = notes

    if new_status in (AssetStatus.APPROVED.value, AssetStatus.REJECTED.value) and notes:
        updated["approval_notes"] = notes

    return updated

"""Creative brief system for the Kai Marketing OS.

Translates ProposedActions into structured CreativeBriefs that specify
persona, tone, format constraints, quality thresholds, and platform
requirements.  The CreativeBrief is the contract between the proposal
layer and the creative execution layer.

Design principles
-----------------
1. **Action-to-brief bridge.**  Every CreativeBrief links back to the
   ProposedAction that generated it via ``source_action_id``.
2. **Format-aware.**  Briefs carry word-count targets, platform
   constraints, and quality-gate thresholds that vary by content format.
3. **Profile-enriched.**  Persona, tone, and CTA are extracted from the
   BusinessProfile when available, with graceful fallbacks.
4. **Harness-compatible.**  ``brief_to_harness_format`` produces output
   matching ``harness/brief-schema.md``.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
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


class BriefType(str, Enum):
    """The broad category of creative output."""

    COPY = "copy"       # Text-based content (articles, emails, ad copy, scripts)
    VISUAL = "visual"   # Image or graphic design assets
    VIDEO = "video"     # Video content (scripts, reels, ads)
    AUDIO = "audio"     # Podcast scripts, voicemail scripts, hold music scripts


class ContentFormat(str, Enum):
    """Specific content format for the brief."""

    BLOG_POST = "blog_post"
    LINKEDIN_ARTICLE = "linkedin_article"
    SOCIAL_POST = "social_post"
    AD_COPY = "ad_copy"
    EMAIL_WELCOME = "email_welcome"
    EMAIL_NURTURE = "email_nurture"
    EMAIL_COLD_OUTREACH = "email_cold_outreach"
    EMAIL_REVIEW_REQUEST = "email_review_request"
    EMAIL_REACTIVATION = "email_reactivation"
    LANDING_PAGE = "landing_page"
    SERVICE_PAGE = "service_page"
    SERVICE_AREA_PAGE = "service_area_page"
    CASE_STUDY = "case_study"
    PRESS_RELEASE = "press_release"
    VIDEO_SCRIPT = "video_script"
    CALL_SCRIPT = "call_script"
    VOICEMAIL_SCRIPT = "voicemail_script"
    TESTIMONIAL_GRAPHIC = "testimonial_graphic"
    OFFER_GRAPHIC = "offer_graphic"
    BEFORE_AFTER_GRAPHIC = "before_after_graphic"
    SOCIAL_REEL = "social_reel"
    FAQ_SECTION = "faq_section"
    HOMEPAGE_SECTION = "homepage_section"
    WEB_SECTION = "web_section"


# ============================================================================
# Constants
# ============================================================================


WORD_COUNT_TARGETS: Dict[str, Dict[str, Any]] = {
    "blog_post": {"target": 1400, "range": "1200-1800"},
    "linkedin_article": {"target": 800, "range": "700-1000"},
    "social_post": {"target": 150, "range": "50-280"},
    "ad_copy": {"target": 50, "range": "25-90"},
    "email_welcome": {"target": 200, "range": "150-300"},
    "email_nurture": {"target": 300, "range": "200-500"},
    "email_cold_outreach": {"target": 100, "range": "75-150"},
    "email_review_request": {"target": 100, "range": "75-150"},
    "email_reactivation": {"target": 150, "range": "100-250"},
    "landing_page": {"target": 1500, "range": "800-2500"},
    "service_page": {"target": 1200, "range": "800-1500"},
    "service_area_page": {"target": 800, "range": "600-1000"},
    "case_study": {"target": 1000, "range": "800-1500"},
    "press_release": {"target": 500, "range": "400-700"},
    "video_script": {"target": 200, "range": "100-500"},
    "call_script": {"target": 300, "range": "200-500"},
    "voicemail_script": {"target": 50, "range": "30-60"},
    "faq_section": {"target": 500, "range": "300-800"},
    "homepage_section": {"target": 200, "range": "100-400"},
    "web_section": {"target": 200, "range": "100-400"},
}


PLATFORM_CONSTRAINTS: Dict[str, Dict[str, Any]] = {
    "google_ads": {
        "headline_max_chars": 30,
        "description_max_chars": 90,
        "headlines_needed": 15,
        "descriptions_needed": 4,
    },
    "meta_ads": {
        "primary_text_max_chars": 125,
        "headline_max_chars": 40,
        "description_max_chars": 30,
    },
    "linkedin_ads": {
        "intro_text_max_chars": 600,
        "headline_max_chars": 200,
    },
    "tiktok_ads": {
        "caption_max_chars": 100,
        "video_max_seconds": 60,
    },
    "instagram_post": {
        "caption_max_chars": 2200,
        "hashtag_max": 30,
    },
    "linkedin_post": {
        "post_max_chars": 3000,
        "hashtag_max": 5,
    },
    "facebook_post": {
        "post_max_chars": 63206,
    },
    "twitter_post": {
        "post_max_chars": 280,
    },
    "tiktok_post": {
        "caption_max_chars": 2200,
    },
    "email": {
        "subject_max_chars": 60,
        "preview_max_chars": 90,
    },
}

# Action types that require creative briefs.  Analytics, tracking, and
# internal configuration do not.
_CREATIVE_ACTION_TYPES = frozenset({
    "content_creation",
    "social_post",
    "ad_campaign",
    "email_sequence",
    "website_update",
    "review_request",
    "follow_up_sequence",
    "reputation_action",
})

# Formats that require SEO lint during quality gate checks.
_SEO_FORMATS = frozenset({
    "blog_post",
    "linkedin_article",
    "landing_page",
    "service_page",
    "service_area_page",
    "case_study",
    "faq_section",
    "homepage_section",
    "web_section",
})

# Formats with a relaxed four-U's threshold (10 instead of 12).
_RELAXED_THRESHOLD_FORMATS = frozenset({
    "ad_copy",
    "email_welcome",
    "email_nurture",
    "email_cold_outreach",
    "email_review_request",
    "email_reactivation",
    "social_post",
    "voicemail_script",
    "call_script",
    "video_script",
})


# ============================================================================
# Data Models
# ============================================================================


class CreativeBrief(BaseModel):
    """Structured specification for a single piece of creative work.

    Every field needed by the creative execution layer is captured here
    so that downstream generators never need to look up business-profile
    or action data on their own.
    """

    id: str = Field(default_factory=lambda: generate_brief_id())
    source_action_id: str = ""
    brief_type: str = BriefType.COPY.value
    channel: str = "website"
    format: str = ContentFormat.BLOG_POST.value

    # Persona targeting
    persona_target: Optional[str] = None
    persona_pain_point: Optional[str] = None

    # Messaging
    key_message: str = ""
    supporting_messages: List[str] = Field(default_factory=list)
    tone_notes: str = ""
    brand_voice_reference: Optional[str] = None

    # Offer / CTA
    offer: Optional[str] = None
    offer_details: Optional[str] = None
    cta: str = ""
    cta_url: Optional[str] = None

    # Length / dimension constraints
    word_count_target: Optional[int] = None
    word_count_range: Optional[str] = None
    dimensions: Optional[str] = None
    duration_target: Optional[str] = None

    # Platform
    platform_constraints: Dict[str, Any] = Field(default_factory=dict)
    compliance_notes: List[str] = Field(default_factory=list)
    reference_assets: List[str] = Field(default_factory=list)

    # SEO
    target_keyword: Optional[str] = None
    secondary_keywords: List[str] = Field(default_factory=list)
    internal_links: List[str] = Field(default_factory=list)

    # Quality gates
    quality_gate_thresholds: Dict[str, Any] = Field(
        default_factory=lambda: {
            "four_us_min": 12,
            "banned_words_check": True,
            "seo_lint": False,
        }
    )

    # Competitive angle
    competitor_url: Optional[str] = None
    competitor_weakness: Optional[str] = None

    # Creative angle
    angle: Optional[str] = None
    hook_options: List[str] = Field(default_factory=list)
    proof_available: Optional[str] = None

    # Timestamps / metadata
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# ID Generation
# ============================================================================


def generate_brief_id() -> str:
    """Return a unique brief ID in the form ``brf_{12-hex-chars}``."""
    return f"brf_{uuid.uuid4().hex[:12]}"


# ============================================================================
# Brief Generation
# ============================================================================


def _determine_brief_type_and_format(
    action_type: str,
    payload: Dict[str, Any],
) -> tuple:
    """Map an action_type + payload to (BriefType value, ContentFormat value).

    Returns a ``(brief_type, content_format)`` tuple of string values.
    """
    if action_type == "social_post":
        return BriefType.COPY.value, ContentFormat.SOCIAL_POST.value

    if action_type == "ad_campaign":
        return BriefType.COPY.value, ContentFormat.AD_COPY.value

    if action_type == "review_request":
        return BriefType.COPY.value, ContentFormat.EMAIL_REVIEW_REQUEST.value

    if action_type == "reputation_action":
        # Review responses are copy work.
        return BriefType.COPY.value, ContentFormat.WEB_SECTION.value

    if action_type == "email_sequence":
        email_type = payload.get("email_type", "nurture")
        email_format_map = {
            "welcome": ContentFormat.EMAIL_WELCOME.value,
            "nurture": ContentFormat.EMAIL_NURTURE.value,
            "cold_outreach": ContentFormat.EMAIL_COLD_OUTREACH.value,
            "review_request": ContentFormat.EMAIL_REVIEW_REQUEST.value,
            "reactivation": ContentFormat.EMAIL_REACTIVATION.value,
        }
        return BriefType.COPY.value, email_format_map.get(
            email_type, ContentFormat.EMAIL_NURTURE.value
        )

    if action_type == "follow_up_sequence":
        seq_type = payload.get("sequence_type", "quote_followup")
        if seq_type in ("welcome", "onboarding"):
            return BriefType.COPY.value, ContentFormat.EMAIL_WELCOME.value
        if seq_type in ("reactivation", "win_back"):
            return BriefType.COPY.value, ContentFormat.EMAIL_REACTIVATION.value
        return BriefType.COPY.value, ContentFormat.EMAIL_NURTURE.value

    if action_type == "content_creation":
        content_type = payload.get("content_type", "blog_post")
        # Check for visual content types.
        visual_types = {
            "testimonial_graphic", "offer_graphic",
            "before_after_graphic", "infographic",
        }
        if content_type in visual_types:
            return BriefType.VISUAL.value, content_type
        video_types = {"social_reel", "video_script"}
        if content_type in video_types:
            return BriefType.VIDEO.value, content_type
        audio_types = {"voicemail_script", "podcast_script"}
        if content_type in audio_types:
            return BriefType.AUDIO.value, content_type
        # Default to copy.  Try to match a known ContentFormat.
        try:
            ContentFormat(content_type)
            return BriefType.COPY.value, content_type
        except ValueError:
            return BriefType.COPY.value, ContentFormat.BLOG_POST.value

    if action_type in ("website_update", "seo_fix"):
        # Determine specific format from payload.
        page_type = payload.get("page_type", "web_section")
        page_format_map = {
            "landing_page": ContentFormat.LANDING_PAGE.value,
            "service_page": ContentFormat.SERVICE_PAGE.value,
            "service_area_page": ContentFormat.SERVICE_AREA_PAGE.value,
            "homepage": ContentFormat.HOMEPAGE_SECTION.value,
            "faq": ContentFormat.FAQ_SECTION.value,
            "case_study": ContentFormat.CASE_STUDY.value,
        }
        return BriefType.COPY.value, page_format_map.get(
            page_type, ContentFormat.WEB_SECTION.value
        )

    # Fallback.
    return BriefType.COPY.value, ContentFormat.WEB_SECTION.value


def _extract_persona(
    business_profile: Optional[Dict[str, Any]],
) -> tuple:
    """Extract primary persona name and pain point from a business profile.

    Returns ``(persona_name, pain_point)`` or ``(None, None)``.
    """
    if not business_profile:
        return None, None
    personas = business_profile.get("personas") or []
    if not personas:
        return None, None

    # Prefer the first persona marked primary; otherwise take the first one.
    primary = None
    for p in personas:
        if isinstance(p, dict):
            if p.get("primary") or p.get("is_primary"):
                primary = p
                break
        elif isinstance(p, str):
            return p, None
    if primary is None and personas:
        primary = personas[0]
    if isinstance(primary, dict):
        return primary.get("name"), primary.get("pain_point")
    if isinstance(primary, str):
        return primary, None
    return None, None


def _extract_tone(
    business_profile: Optional[Dict[str, Any]],
) -> str:
    """Extract tone guidance from a business profile's brand_voice.

    Returns a human-readable tone string or a sensible default.
    """
    if not business_profile:
        return "professional but approachable, avoid corporate jargon"
    brand_voice = business_profile.get("brand_voice") or {}
    if isinstance(brand_voice, str):
        return brand_voice
    descriptors = brand_voice.get("tone_descriptors") or brand_voice.get("tone") or []
    if isinstance(descriptors, list) and descriptors:
        return ", ".join(str(d) for d in descriptors)
    if isinstance(descriptors, str) and descriptors:
        return descriptors
    return "professional but approachable, avoid corporate jargon"


def _extract_cta(
    action: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]],
) -> str:
    """Extract the best CTA from the action payload or business profile."""
    # First, check the action's suggested_payload.
    payload = action.get("suggested_payload") or {}
    cta = payload.get("cta") or payload.get("primary_cta") or ""
    if cta:
        return cta

    # Fall back to business profile offers.
    if business_profile:
        offers = business_profile.get("offers") or []
        for offer in offers:
            if isinstance(offer, dict):
                offer_cta = offer.get("primary_cta") or offer.get("cta") or ""
                if offer_cta:
                    return offer_cta
        # Check for a top-level default CTA.
        default_cta = business_profile.get("default_cta") or ""
        if default_cta:
            return default_cta

    return "Get Started"


def _build_quality_thresholds(content_format: str) -> Dict[str, Any]:
    """Determine quality gate thresholds based on content format.

    SEO-oriented formats get ``seo_lint: True`` and ``four_us_min: 12``.
    Ads, email, and social get ``four_us_min: 10``.
    """
    is_seo = content_format in _SEO_FORMATS
    is_relaxed = content_format in _RELAXED_THRESHOLD_FORMATS
    return {
        "four_us_min": 10 if is_relaxed else 12,
        "banned_words_check": True,
        "seo_lint": is_seo,
    }


def _extract_platform_constraints(
    channel: str,
    content_format: str,
) -> Dict[str, Any]:
    """Return platform-specific constraints for the given channel/format."""
    # Map channel names to PLATFORM_CONSTRAINTS keys.
    channel_key_map = {
        "google_ads": "google_ads",
        "google": "google_ads",
        "meta": "meta_ads",
        "meta_ads": "meta_ads",
        "facebook": "meta_ads",
        "instagram": "instagram_post",
        "linkedin": "linkedin_post",
        "linkedin_ads": "linkedin_ads",
        "tiktok": "tiktok_post",
        "tiktok_ads": "tiktok_ads",
        "twitter": "twitter_post",
        "x": "twitter_post",
        "email": "email",
    }

    # Try direct channel lookup first.
    key = channel_key_map.get(channel, "")
    if key and key in PLATFORM_CONSTRAINTS:
        return dict(PLATFORM_CONSTRAINTS[key])

    # For ad-copy formats, infer platform from channel.
    if content_format == ContentFormat.AD_COPY.value:
        if "google" in channel.lower():
            return dict(PLATFORM_CONSTRAINTS.get("google_ads", {}))
        if "meta" in channel.lower() or "facebook" in channel.lower():
            return dict(PLATFORM_CONSTRAINTS.get("meta_ads", {}))
        if "linkedin" in channel.lower():
            return dict(PLATFORM_CONSTRAINTS.get("linkedin_ads", {}))
        if "tiktok" in channel.lower():
            return dict(PLATFORM_CONSTRAINTS.get("tiktok_ads", {}))

    # For email formats, return email constraints.
    if content_format.startswith("email_"):
        return dict(PLATFORM_CONSTRAINTS.get("email", {}))

    return {}


def generate_brief(
    action: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a CreativeBrief from a ProposedAction dict.

    Parameters
    ----------
    action:
        A ProposedAction dict (or model_dump() output).  Must contain at
        minimum ``action_type`` and ``title``.
    business_profile:
        Optional BusinessProfile dict with ``personas``, ``brand_voice``,
        ``offers``, etc.

    Returns
    -------
    Dict[str, Any]
        A CreativeBrief serialized as a dict.
    """
    action_type = action.get("action_type", "content_creation")
    payload = action.get("suggested_payload") or {}
    channel = action.get("channel", "website")

    brief_type, content_format = _determine_brief_type_and_format(
        action_type, payload,
    )

    persona_name, persona_pain = _extract_persona(business_profile)
    tone = _extract_tone(business_profile)
    cta = _extract_cta(action, business_profile)
    thresholds = _build_quality_thresholds(content_format)
    constraints = _extract_platform_constraints(channel, content_format)

    # Word-count targets.
    wc_info = WORD_COUNT_TARGETS.get(content_format, {})
    word_count_target = wc_info.get("target")
    word_count_range = wc_info.get("range")

    # Key message: prefer payload description, fall back to action title.
    key_message = (
        payload.get("key_message")
        or payload.get("description")
        or action.get("description", "")
        or action.get("title", "")
    )

    # Supporting messages from payload.
    supporting = payload.get("supporting_messages") or []
    if isinstance(supporting, str):
        supporting = [supporting]

    # Offer extraction.
    offer = payload.get("offer") or payload.get("offer_name")
    offer_details = payload.get("offer_details") or payload.get("offer_terms")
    if not offer and business_profile:
        offers_list = business_profile.get("offers") or []
        for o in offers_list:
            if isinstance(o, dict) and (o.get("primary") or o.get("is_primary")):
                offer = o.get("name") or o.get("offer_name")
                offer_details = o.get("details") or o.get("terms")
                break

    # SEO fields.
    target_keyword = payload.get("target_keyword") or payload.get("keyword")
    secondary_keywords = payload.get("secondary_keywords") or []
    if isinstance(secondary_keywords, str):
        secondary_keywords = [secondary_keywords]
    internal_links = payload.get("internal_links") or []
    if isinstance(internal_links, str):
        internal_links = [internal_links]

    # Competitive angle.
    competitor_url = payload.get("competitor_url")
    competitor_weakness = payload.get("competitor_weakness")

    # Creative angle.
    angle = payload.get("angle")
    hook_options = payload.get("hook_options") or []
    proof_available = payload.get("proof_available")

    # Brand voice reference.
    brand_voice_ref = None
    if business_profile:
        bv = business_profile.get("brand_voice") or {}
        if isinstance(bv, dict):
            brand_voice_ref = bv.get("reference") or bv.get("name")

    # Compliance notes from payload or business profile.
    compliance_notes = payload.get("compliance_notes") or []
    if isinstance(compliance_notes, str):
        compliance_notes = [compliance_notes]
    if business_profile:
        profile_compliance = business_profile.get("compliance_notes") or []
        if isinstance(profile_compliance, list):
            compliance_notes = compliance_notes + profile_compliance

    brief = CreativeBrief(
        source_action_id=action.get("id", ""),
        brief_type=brief_type,
        channel=channel,
        format=content_format,
        persona_target=persona_name,
        persona_pain_point=persona_pain,
        key_message=key_message,
        supporting_messages=supporting,
        tone_notes=tone,
        brand_voice_reference=brand_voice_ref,
        offer=offer,
        offer_details=offer_details,
        cta=cta,
        cta_url=payload.get("cta_url"),
        word_count_target=word_count_target,
        word_count_range=word_count_range,
        dimensions=payload.get("dimensions"),
        duration_target=payload.get("duration_target"),
        platform_constraints=constraints,
        compliance_notes=compliance_notes,
        reference_assets=payload.get("reference_assets") or [],
        target_keyword=target_keyword,
        secondary_keywords=secondary_keywords,
        internal_links=internal_links,
        quality_gate_thresholds=thresholds,
        competitor_url=competitor_url,
        competitor_weakness=competitor_weakness,
        angle=angle,
        hook_options=hook_options,
        proof_available=proof_available,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=payload.get("metadata") or {},
    )

    return brief.model_dump()


def generate_briefs_for_bundle(
    bundle: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate CreativeBriefs for every action in a ProposalBundle that
    requires creative work.

    Actions whose ``action_type`` is not in ``_CREATIVE_ACTION_TYPES``
    (e.g., ``analytics_fix``, ``kaicalls_setup``) are silently skipped.

    For ``website_update`` actions, a brief is only generated when the
    payload indicates a copy change (``copy_change`` flag or the
    presence of ``page_type``).

    Parameters
    ----------
    bundle:
        A ProposalBundle dict containing an ``actions`` list.
    business_profile:
        Optional BusinessProfile dict.

    Returns
    -------
    List[Dict[str, Any]]
        A list of CreativeBrief dicts, one per qualifying action.
    """
    actions = bundle.get("actions") or []
    briefs: List[Dict[str, Any]] = []

    for action in actions:
        if isinstance(action, dict):
            action_dict = action
        elif hasattr(action, "model_dump"):
            action_dict = action.model_dump()
        else:
            continue

        action_type = action_dict.get("action_type", "")

        # Skip non-creative action types.
        if action_type not in _CREATIVE_ACTION_TYPES:
            continue

        # For website_update, only generate a brief when copy work is needed.
        if action_type == "website_update":
            payload = action_dict.get("suggested_payload") or {}
            needs_copy = (
                payload.get("copy_change")
                or payload.get("page_type")
                or payload.get("content_type")
                or payload.get("key_message")
            )
            if not needs_copy:
                continue

        briefs.append(generate_brief(action_dict, business_profile))

    return briefs


def brief_to_harness_format(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a CreativeBrief dict to the format expected by
    ``harness/brief-schema.md``.

    The harness brief schema expects a flat JSON object with specific
    field names.  This function maps CreativeBrief fields to the
    harness schema.

    Parameters
    ----------
    brief:
        A CreativeBrief dict (from ``generate_brief`` or ``model_dump``).

    Returns
    -------
    Dict[str, Any]
        A dict matching the harness brief JSON schema.
    """
    # Map format to the harness's simpler format taxonomy.
    format_value = brief.get("format", "blog_post")
    harness_format_map = {
        "blog_post": "blog",
        "linkedin_article": "linkedin",
        "email_welcome": "email",
        "email_nurture": "email",
        "email_cold_outreach": "email",
        "email_review_request": "email",
        "email_reactivation": "email",
        "ad_copy": "ad",
        "social_post": "tiktok",  # harness default; overridden by channel
        "press_release": "press",
        "video_script": "tiktok",
        "landing_page": "blog",
        "service_page": "blog",
        "service_area_page": "blog",
        "case_study": "blog",
        "faq_section": "blog",
        "homepage_section": "blog",
        "web_section": "blog",
    }
    harness_format = harness_format_map.get(format_value, "blog")

    # Determine target_site (harness field) -- not always available.
    target_site = brief.get("metadata", {}).get("target_site", "")

    harness_brief: Dict[str, Any] = {
        "target_site": target_site,
        "target_keyword": brief.get("target_keyword") or "",
        "secondary_keywords": brief.get("secondary_keywords") or [],
        "format": harness_format,
        "persona": brief.get("persona_target") or "",
        "current_rank": brief.get("metadata", {}).get("current_rank", "not ranking"),
        "monthly_impressions": brief.get("metadata", {}).get("monthly_impressions", 0),
        "current_ctr": brief.get("metadata", {}).get("current_ctr", 0.0),
        "competitor_url": brief.get("competitor_url") or "",
        "competitor_weakness": brief.get("competitor_weakness") or "",
        "angle": brief.get("angle") or "",
        "hook_options": brief.get("hook_options") or [],
        "audience_pain": brief.get("persona_pain_point") or "",
        "proof_available": brief.get("proof_available") or "",
        "cta": brief.get("cta") or "",
        "word_count_target": brief.get("word_count_target") or 1400,
        "publish_date": brief.get("metadata", {}).get("publish_date", ""),
        "internal_links": brief.get("internal_links") or [],
    }

    # Pad hook_options to 3 if fewer are present (harness validation requires 3).
    hooks = harness_brief["hook_options"]
    while len(hooks) < 3:
        hooks.append("")

    return harness_brief

"""Ad creative variant generation and cross-channel content adaptation.

Generates structured variations of every creative element (headlines,
descriptions, CTAs, visuals, audiences) from a single base creative, and
adapts content across channels with platform-specific character limits,
tone adjustments, and format compliance.

Together, a single creative brief can produce dozens of ready-to-deploy
assets across all channels.

Uses the ``dataclass`` + ``SerializableModel`` pattern from
``kai/runtime/models.py``.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ============================================================================
# Enums
# ============================================================================


class VariantType(str, Enum):
    """Canonical creative variant type identifiers."""

    headline_benefit = "headline_benefit"
    headline_feature = "headline_feature"
    headline_social_proof = "headline_social_proof"
    headline_urgency = "headline_urgency"
    headline_question = "headline_question"
    headline_statistic = "headline_statistic"
    description_short = "description_short"
    description_medium = "description_medium"
    description_long = "description_long"
    cta_action = "cta_action"
    cta_value = "cta_value"
    cta_urgency = "cta_urgency"
    visual_product = "visual_product"
    visual_lifestyle = "visual_lifestyle"
    visual_social_proof = "visual_social_proof"
    audience_persona_a = "audience_persona_a"
    audience_persona_b = "audience_persona_b"


# Grouped sets for convenience
HEADLINE_TYPES = [
    VariantType.headline_benefit,
    VariantType.headline_feature,
    VariantType.headline_social_proof,
    VariantType.headline_urgency,
    VariantType.headline_question,
    VariantType.headline_statistic,
]

DESCRIPTION_TYPES = [
    VariantType.description_short,
    VariantType.description_medium,
    VariantType.description_long,
]

CTA_TYPES = [
    VariantType.cta_action,
    VariantType.cta_value,
    VariantType.cta_urgency,
]

VISUAL_TYPES = [
    VariantType.visual_product,
    VariantType.visual_lifestyle,
    VariantType.visual_social_proof,
]


# ============================================================================
# Data models
# ============================================================================


@dataclass
class BaseCreative(SerializableModel):
    """Source creative from which variants are generated."""

    id: str = ""
    headline: str = ""
    description: str = ""
    cta: str = ""
    image_concept: Optional[str] = None
    target_audience: Optional[str] = None
    channel: str = "general"
    offer: Optional[str] = None
    proof_point: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"base_{uuid.uuid4().hex[:8]}"


@dataclass
class CreativeVariant(SerializableModel):
    """A single variant derived from a BaseCreative."""

    id: str = ""
    base_id: str = ""
    variant_type: str = ""
    variant_number: int = 1
    headline: str = ""
    description: str = ""
    cta: str = ""
    image_concept: Optional[str] = None
    target_audience: Optional[str] = None
    channel: str = "general"
    changes_from_base: List[str] = field(default_factory=list)
    rationale: str = ""
    character_counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id and self.base_id and self.variant_type:
            self.id = (
                f"{self.base_id}_{self.variant_type}_{self.variant_number:02d}"
            )
        if not self.character_counts:
            self.character_counts = {
                "headline": len(self.headline),
                "description": len(self.description),
                "cta": len(self.cta),
            }


@dataclass
class ChannelSpec(SerializableModel):
    """Platform-specific creative constraints."""

    channel: str = ""
    headline_max_chars: int = 0
    description_max_chars: int = 0
    cta_max_chars: Optional[int] = None
    hashtags_allowed: bool = False
    hashtag_limit: Optional[int] = None
    mentions_allowed: bool = False
    emoji_allowed: bool = False
    link_allowed: bool = True
    image_required: bool = False
    video_allowed: bool = False
    tone_adjustment: Optional[str] = None
    special_format: Optional[str] = None


# ============================================================================
# Channel specification registry
# ============================================================================


def get_channel_specs() -> Dict[str, ChannelSpec]:
    """Return platform-specific creative specs for every supported channel."""

    return {
        "google_ads_search": ChannelSpec(
            channel="google_ads_search",
            headline_max_chars=30,
            description_max_chars=90,
            cta_max_chars=None,
            hashtags_allowed=False,
            emoji_allowed=False,
            link_allowed=True,
            image_required=False,
            video_allowed=False,
            tone_adjustment="direct, benefit-led, no filler words",
            special_format=None,
        ),
        "google_ads_display": ChannelSpec(
            channel="google_ads_display",
            headline_max_chars=30,
            description_max_chars=90,
            cta_max_chars=None,
            hashtags_allowed=False,
            emoji_allowed=False,
            link_allowed=True,
            image_required=True,
            video_allowed=True,
            tone_adjustment="direct, benefit-led, concise",
            special_format=None,
        ),
        "meta_ads_feed": ChannelSpec(
            channel="meta_ads_feed",
            headline_max_chars=40,
            description_max_chars=125,
            cta_max_chars=25,
            hashtags_allowed=True,
            hashtag_limit=5,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=True,
            video_allowed=True,
            tone_adjustment="conversational, scroll-stopping hook first",
            special_format="feed",
        ),
        "meta_ads_stories": ChannelSpec(
            channel="meta_ads_stories",
            headline_max_chars=40,
            description_max_chars=90,
            cta_max_chars=25,
            hashtags_allowed=False,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=True,
            video_allowed=True,
            tone_adjustment="urgent, visual-first, minimal text",
            special_format="story",
        ),
        "linkedin_ads": ChannelSpec(
            channel="linkedin_ads",
            headline_max_chars=70,
            description_max_chars=150,
            cta_max_chars=None,
            hashtags_allowed=False,
            emoji_allowed=False,
            link_allowed=True,
            image_required=True,
            video_allowed=True,
            tone_adjustment="professional, outcome-focused, data-backed",
            special_format=None,
        ),
        "tiktok_ads": ChannelSpec(
            channel="tiktok_ads",
            headline_max_chars=100,
            description_max_chars=100,
            cta_max_chars=None,
            hashtags_allowed=True,
            hashtag_limit=5,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=False,
            video_allowed=True,
            tone_adjustment="casual, native-feeling, hook in first 2 seconds",
            special_format="video",
        ),
        "instagram_organic": ChannelSpec(
            channel="instagram_organic",
            headline_max_chars=2200,
            description_max_chars=2200,
            cta_max_chars=None,
            hashtags_allowed=True,
            hashtag_limit=30,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=False,
            image_required=True,
            video_allowed=True,
            tone_adjustment="visual storytelling, relatable, emoji-friendly",
            special_format=None,
        ),
        "facebook_organic": ChannelSpec(
            channel="facebook_organic",
            headline_max_chars=500,
            description_max_chars=500,
            cta_max_chars=None,
            hashtags_allowed=True,
            hashtag_limit=3,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=False,
            video_allowed=True,
            tone_adjustment="conversational, community-oriented, question-driven",
            special_format=None,
        ),
        "linkedin_organic": ChannelSpec(
            channel="linkedin_organic",
            headline_max_chars=1300,
            description_max_chars=1300,
            cta_max_chars=None,
            hashtags_allowed=True,
            hashtag_limit=5,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=False,
            video_allowed=True,
            tone_adjustment="professional thought leadership, personal anecdotes OK",
            special_format=None,
        ),
        "twitter_organic": ChannelSpec(
            channel="twitter_organic",
            headline_max_chars=280,
            description_max_chars=280,
            cta_max_chars=None,
            hashtags_allowed=True,
            hashtag_limit=3,
            mentions_allowed=True,
            emoji_allowed=True,
            link_allowed=True,
            image_required=False,
            video_allowed=True,
            tone_adjustment="punchy, opinionated, thread-friendly",
            special_format=None,
        ),
        "email_subject": ChannelSpec(
            channel="email_subject",
            headline_max_chars=50,
            description_max_chars=100,
            cta_max_chars=None,
            hashtags_allowed=False,
            emoji_allowed=False,
            link_allowed=False,
            image_required=False,
            video_allowed=False,
            tone_adjustment="curiosity-driven, personal, value-first",
            special_format=None,
        ),
        "email_body": ChannelSpec(
            channel="email_body",
            headline_max_chars=9999,
            description_max_chars=9999,
            cta_max_chars=None,
            hashtags_allowed=False,
            emoji_allowed=False,
            link_allowed=True,
            image_required=False,
            video_allowed=False,
            tone_adjustment="professional, scannable, one CTA per email",
            special_format=None,
        ),
    }


# ============================================================================
# Headline variant templates
# ============================================================================

# Each entry maps a VariantType to a list of template patterns.
# Templates use {offer}, {proof_point}, {audience} placeholders drawn from
# the BaseCreative.  If a placeholder value is unavailable, the generator
# fills in a sensible default from the base headline or description.

_HEADLINE_TEMPLATES: Dict[str, List[str]] = {
    VariantType.headline_benefit.value: [
        "Save Time With {offer}",
        "Get {offer} Without the Hassle",
        "Stop Wasting Money on {offer}",
        "The Faster Way to {offer}",
        "{offer} That Pays for Itself",
        "Finally, {offer} That Works",
    ],
    VariantType.headline_feature.value: [
        "AI-Powered {offer}",
        "24/7 {offer} Built for You",
        "Automated {offer} in Seconds",
        "All-in-One {offer} Platform",
        "{offer} With Real-Time Reporting",
        "Enterprise-Grade {offer}",
    ],
    VariantType.headline_social_proof.value: [
        "Join {proof_point} Who Trust {offer}",
        "{proof_point} and Counting",
        "Rated 5 Stars by {proof_point}",
        "The {offer} {proof_point} Recommend",
        "See Why {proof_point} Switched",
        "Trusted by {proof_point} Nationwide",
    ],
    VariantType.headline_urgency.value: [
        "Limited Spots Available This Month",
        "Offer Ends Soon - {offer}",
        "Don't Wait - {offer} Today",
        "Only a Few Slots Left for {offer}",
        "This Week Only: {offer}",
        "Last Chance for {offer}",
    ],
    VariantType.headline_question.value: [
        "Still Struggling With {offer}?",
        "What If {offer} Were Easier?",
        "Tired of Overcomplicating {offer}?",
        "Ready to Fix Your {offer}?",
        "Why Settle for Less With {offer}?",
        "Is Your {offer} Costing You Customers?",
    ],
    VariantType.headline_statistic.value: [
        "78% of Businesses Fail at {offer}",
        "3x Faster {offer} in 30 Days",
        "Reduce {offer} Costs by 47%",
        "93% Satisfaction Rate for {offer}",
        "Saved 10+ Hours Per Week on {offer}",
        "500+ Businesses Chose {offer} Last Year",
    ],
}


# ============================================================================
# CTA variant templates
# ============================================================================

_CTA_TEMPLATES: Dict[str, List[str]] = {
    VariantType.cta_action.value: [
        "Get Your Free Quote",
        "Start Now",
        "Book Today",
        "Try It Free",
        "Sign Up",
        "Get Started",
    ],
    VariantType.cta_value.value: [
        "See Pricing",
        "Compare Plans",
        "Calculate Your Savings",
        "See the ROI",
        "View Demo",
        "Explore Features",
    ],
    VariantType.cta_urgency.value: [
        "Claim Your Spot",
        "Don't Miss Out",
        "Limited Time Offer",
        "Reserve Now",
        "Lock In Your Rate",
        "Grab It Before It's Gone",
    ],
}

# Soft CTAs are used as an additional pool when more variety is needed.
_CTA_SOFT: List[str] = [
    "Learn More",
    "See How It Works",
    "Watch Demo",
    "Read the Case Study",
    "Take the Tour",
    "Talk to an Expert",
]


# ============================================================================
# VariantGenerator
# ============================================================================


class VariantGenerator:
    """Produce structured creative variants from a single BaseCreative.

    Generates headline, description, CTA, visual, and audience variants
    that follow a deterministic naming convention and include change
    tracking and rationale for each variant.
    """

    def __init__(self) -> None:
        self._channel_specs = get_channel_specs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_variants(
        self,
        base: BaseCreative,
        variant_types: Optional[List[str]] = None,
        variants_per_type: int = 2,
    ) -> List[CreativeVariant]:
        """Generate variants for each requested type (or all if *None*).

        Returns a flat list of ``CreativeVariant`` objects with the naming
        convention applied to every variant id.
        """
        all_types = variant_types or [vt.value for vt in VariantType]
        results: List[CreativeVariant] = []

        for vt_value in all_types:
            try:
                vt = VariantType(vt_value)
            except ValueError:
                continue

            if vt in HEADLINE_TYPES:
                results.extend(
                    self._generate_from_headline_type(base, vt, variants_per_type)
                )
            elif vt in DESCRIPTION_TYPES:
                results.extend(
                    self._generate_from_description_type(base, vt, variants_per_type)
                )
            elif vt in CTA_TYPES:
                results.extend(
                    self._generate_from_cta_type(base, vt, variants_per_type)
                )
            elif vt in VISUAL_TYPES:
                results.extend(
                    self._generate_visual_variant(base, vt, variants_per_type)
                )
            elif vt in (VariantType.audience_persona_a, VariantType.audience_persona_b):
                label = "Persona A" if vt == VariantType.audience_persona_a else "Persona B"
                results.extend(
                    self._generate_audience_variant(base, vt, label, variants_per_type)
                )

        return results

    def generate_headline_variants(
        self, base: BaseCreative, count: int = 6
    ) -> List[CreativeVariant]:
        """Generate headline variants across all six headline types.

        Cycles through benefit, feature, social_proof, urgency, question,
        and statistic types distributing *count* variants as evenly as
        possible.
        """
        results: List[CreativeVariant] = []
        per_type = max(1, count // len(HEADLINE_TYPES))
        remainder = count - per_type * len(HEADLINE_TYPES)

        for idx, vt in enumerate(HEADLINE_TYPES):
            n = per_type + (1 if idx < remainder else 0)
            results.extend(self._generate_from_headline_type(base, vt, n))

        return results[:count]

    def generate_description_variants(
        self, base: BaseCreative, count: int = 3
    ) -> List[CreativeVariant]:
        """Produce short, medium, and long description variants."""
        results: List[CreativeVariant] = []
        per_type = max(1, count // len(DESCRIPTION_TYPES))
        remainder = count - per_type * len(DESCRIPTION_TYPES)

        for idx, vt in enumerate(DESCRIPTION_TYPES):
            n = per_type + (1 if idx < remainder else 0)
            results.extend(self._generate_from_description_type(base, vt, n))

        return results[:count]

    def generate_cta_variants(
        self, base: BaseCreative, count: int = 4
    ) -> List[CreativeVariant]:
        """Produce action, value, urgency, and soft CTA variants."""
        results: List[CreativeVariant] = []

        # Distribute count across action, value, urgency, soft
        cta_pools = list(CTA_TYPES)  # 3 types
        per_type = max(1, count // (len(cta_pools) + 1))  # +1 for soft
        remainder = count - per_type * (len(cta_pools) + 1)

        for idx, vt in enumerate(cta_pools):
            n = per_type + (1 if idx < remainder else 0)
            results.extend(self._generate_from_cta_type(base, vt, n))

        # Soft CTAs
        soft_count = per_type
        for i in range(soft_count):
            cta_text = _CTA_SOFT[i % len(_CTA_SOFT)]
            variant = CreativeVariant(
                base_id=base.id,
                variant_type="cta_soft",
                variant_number=i + 1,
                headline=base.headline,
                description=base.description,
                cta=cta_text,
                image_concept=base.image_concept,
                target_audience=base.target_audience,
                channel=base.channel,
                changes_from_base=[
                    f"CTA changed from '{base.cta}' to soft CTA '{cta_text}'"
                ],
                rationale=(
                    "Soft CTAs reduce commitment anxiety and work well for "
                    "top-of-funnel audiences who are not ready to buy."
                ),
            )
            variant.id = f"{base.id}_cta_soft_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results[:count]

    def generate_visual_variants(
        self, base: BaseCreative, count: int = 3
    ) -> List[CreativeVariant]:
        """Produce product, lifestyle, and social proof visual variants."""
        results: List[CreativeVariant] = []
        per_type = max(1, count // len(VISUAL_TYPES))
        remainder = count - per_type * len(VISUAL_TYPES)

        for idx, vt in enumerate(VISUAL_TYPES):
            n = per_type + (1 if idx < remainder else 0)
            results.extend(self._generate_visual_variant(base, vt, n))

        return results[:count]

    def generate_audience_variants(
        self, base: BaseCreative, personas: List[str]
    ) -> List[CreativeVariant]:
        """Adapt the base creative for each persona in *personas*."""
        results: List[CreativeVariant] = []
        for idx, persona in enumerate(personas):
            vt = (
                VariantType.audience_persona_a
                if idx % 2 == 0
                else VariantType.audience_persona_b
            )
            results.extend(
                self._generate_audience_variant(base, vt, persona, count=1)
            )
        return results

    # ------------------------------------------------------------------
    # Private generators
    # ------------------------------------------------------------------

    def _fill_template(self, template: str, base: BaseCreative) -> str:
        """Replace placeholders in a template with BaseCreative values."""
        offer = base.offer or base.headline
        proof = base.proof_point or "happy customers"
        audience = base.target_audience or "businesses"
        return (
            template.replace("{offer}", offer)
            .replace("{proof_point}", proof)
            .replace("{audience}", audience)
        )

    def _generate_from_headline_type(
        self, base: BaseCreative, vt: VariantType, count: int
    ) -> List[CreativeVariant]:
        templates = _HEADLINE_TEMPLATES.get(vt.value, [])
        results: List[CreativeVariant] = []

        rationale_map = {
            VariantType.headline_benefit: (
                "Benefit-led headlines connect the offer to the customer's desired "
                "outcome, increasing click-through by making value immediately obvious."
            ),
            VariantType.headline_feature: (
                "Feature-led headlines appeal to solution-aware audiences who are "
                "comparing options and want to know what the product actually does."
            ),
            VariantType.headline_social_proof: (
                "Social proof headlines reduce perceived risk by showing that others "
                "have already made the same decision successfully."
            ),
            VariantType.headline_urgency: (
                "Urgency headlines create time pressure that moves prospects from "
                "consideration to action by implying scarcity or a deadline."
            ),
            VariantType.headline_question: (
                "Question headlines engage the reader by triggering an internal "
                "answer, creating a curiosity loop that drives clicks."
            ),
            VariantType.headline_statistic: (
                "Statistic headlines lead with a specific number to establish "
                "credibility and pattern-interrupt scrolling behaviour."
            ),
        }

        for i in range(min(count, len(templates))):
            new_headline = self._fill_template(templates[i], base)
            variant = CreativeVariant(
                base_id=base.id,
                variant_type=vt.value,
                variant_number=i + 1,
                headline=new_headline,
                description=base.description,
                cta=base.cta,
                image_concept=base.image_concept,
                target_audience=base.target_audience,
                channel=base.channel,
                changes_from_base=[
                    f"Headline rewritten with {vt.value.replace('headline_', '')} angle"
                ],
                rationale=rationale_map.get(vt, "Variant provides an alternative angle."),
            )
            variant.id = f"{base.id}_{vt.value}_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results

    def _generate_from_description_type(
        self, base: BaseCreative, vt: VariantType, count: int
    ) -> List[CreativeVariant]:
        results: List[CreativeVariant] = []
        offer = base.offer or base.headline
        proof = base.proof_point or "proven results"

        target_ranges = {
            VariantType.description_short: (0, 90),
            VariantType.description_medium: (90, 150),
            VariantType.description_long: (150, 300),
        }

        description_builders = {
            VariantType.description_short: [
                f"{offer}. Results you can measure.",
                f"Fast, reliable {offer} that delivers.",
                f"Get {offer} done right the first time.",
                f"Professional {offer} in minutes.",
            ],
            VariantType.description_medium: [
                f"{offer} backed by {proof}. See the difference in your first week.",
                f"Stop wasting time. Get {offer} with {proof} and measurable ROI.",
                f"Our {offer} combines speed with quality. {proof} proves it works.",
                f"Join thousands who rely on {offer}. {proof} shows real outcomes.",
            ],
            VariantType.description_long: [
                (
                    f"Most businesses waste hours on {offer} without seeing results. "
                    f"Our approach is different: {proof}, and every action is tracked "
                    f"so you know exactly what is working and what needs to change."
                ),
                (
                    f"We built {offer} for teams that need results, not excuses. "
                    f"With {proof} behind every recommendation, you get a system "
                    f"that adapts to your goals and delivers measurable outcomes."
                ),
                (
                    f"Finding the right {offer} solution used to take weeks of research. "
                    f"Now you can rely on {proof} and a platform that handles "
                    f"the complexity so you can focus on growing your business."
                ),
            ],
        }

        templates = description_builders.get(vt, [])
        min_chars, max_chars = target_ranges.get(vt, (0, 300))

        for i in range(min(count, len(templates))):
            desc = templates[i]
            # Enforce range: truncate long descriptions, pad short ones
            if len(desc) > max_chars:
                desc = _truncate_to_limit(desc, max_chars, preserve_words=True)

            length_label = vt.value.replace("description_", "")
            variant = CreativeVariant(
                base_id=base.id,
                variant_type=vt.value,
                variant_number=i + 1,
                headline=base.headline,
                description=desc,
                cta=base.cta,
                image_concept=base.image_concept,
                target_audience=base.target_audience,
                channel=base.channel,
                changes_from_base=[
                    f"Description rewritten as {length_label} variant ({min_chars}-{max_chars} chars)"
                ],
                rationale=(
                    f"A {length_label} description suits platforms with "
                    f"{'tight' if length_label == 'short' else 'generous'} character "
                    f"limits and audiences who prefer "
                    f"{'scannable' if length_label == 'short' else 'detailed'} copy."
                ),
            )
            variant.id = f"{base.id}_{vt.value}_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results

    def _generate_from_cta_type(
        self, base: BaseCreative, vt: VariantType, count: int
    ) -> List[CreativeVariant]:
        templates = _CTA_TEMPLATES.get(vt.value, [])
        results: List[CreativeVariant] = []

        rationale_map = {
            VariantType.cta_action: (
                "Action CTAs drive direct response by telling the reader exactly "
                "what to do next, reducing decision friction."
            ),
            VariantType.cta_value: (
                "Value CTAs appeal to research-phase prospects who want to "
                "evaluate before committing, increasing qualified clicks."
            ),
            VariantType.cta_urgency: (
                "Urgency CTAs create fear of missing out that accelerates "
                "decision-making for prospects already considering the offer."
            ),
        }

        for i in range(min(count, len(templates))):
            cta_text = templates[i]
            variant = CreativeVariant(
                base_id=base.id,
                variant_type=vt.value,
                variant_number=i + 1,
                headline=base.headline,
                description=base.description,
                cta=cta_text,
                image_concept=base.image_concept,
                target_audience=base.target_audience,
                channel=base.channel,
                changes_from_base=[
                    f"CTA changed from '{base.cta}' to {vt.value.replace('cta_', '')} CTA '{cta_text}'"
                ],
                rationale=rationale_map.get(vt, "Variant provides an alternative CTA approach."),
            )
            variant.id = f"{base.id}_{vt.value}_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results

    def _generate_visual_variant(
        self, base: BaseCreative, vt: VariantType, count: int
    ) -> List[CreativeVariant]:
        results: List[CreativeVariant] = []
        offer = base.offer or base.headline
        proof = base.proof_point or "happy customers"

        concept_builders = {
            VariantType.visual_product: [
                f"Product shot: {offer} in action, clean background, studio lighting",
                f"UI screenshot: {offer} dashboard with key metrics visible",
                f"Close-up: hands using the {offer} product, natural environment",
            ],
            VariantType.visual_lifestyle: [
                f"Customer smiling while using {offer}, bright modern workspace",
                f"Business owner relaxing because {offer} handles the work, lifestyle setting",
                f"Team celebrating results from {offer}, candid office moment",
            ],
            VariantType.visual_social_proof: [
                f"5-star review overlay: \"{proof}\" with customer photo and name",
                f"Before/after comparison showing impact of {offer}",
                f"Customer testimonial video thumbnail: {proof}, play button overlay",
            ],
        }

        rationale_map = {
            VariantType.visual_product: (
                "Product-focused visuals work best for solution-aware audiences "
                "who want to see what they are buying before committing."
            ),
            VariantType.visual_lifestyle: (
                "Lifestyle visuals create emotional resonance by showing the "
                "outcome the customer wants rather than the product itself."
            ),
            VariantType.visual_social_proof: (
                "Social proof visuals combine credibility with visual impact, "
                "increasing trust and reducing perceived risk simultaneously."
            ),
        }

        templates = concept_builders.get(vt, [])
        for i in range(min(count, len(templates))):
            variant = CreativeVariant(
                base_id=base.id,
                variant_type=vt.value,
                variant_number=i + 1,
                headline=base.headline,
                description=base.description,
                cta=base.cta,
                image_concept=templates[i],
                target_audience=base.target_audience,
                channel=base.channel,
                changes_from_base=[
                    f"Visual concept changed to {vt.value.replace('visual_', '')} style"
                ],
                rationale=rationale_map.get(vt, "Variant uses an alternative visual approach."),
            )
            variant.id = f"{base.id}_{vt.value}_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results

    def _generate_audience_variant(
        self,
        base: BaseCreative,
        vt: VariantType,
        persona_label: str,
        count: int = 1,
    ) -> List[CreativeVariant]:
        results: List[CreativeVariant] = []
        offer = base.offer or base.headline

        # Build persona-adapted copy for each requested variant
        persona_adaptations = [
            {
                "headline": f"{offer} Built for {persona_label}",
                "description": (
                    f"Designed specifically for {persona_label}, "
                    f"our {offer} solves the problems that matter most "
                    f"to your team."
                ),
                "cta": f"See How It Works for {persona_label}",
            },
            {
                "headline": f"Why {persona_label} Choose {offer}",
                "description": (
                    f"{persona_label} professionals need {offer} that "
                    f"fits their workflow. See why thousands made the switch."
                ),
                "cta": f"Get the {persona_label} Guide",
            },
            {
                "headline": f"{persona_label}: Stop Settling for Generic {offer}",
                "description": (
                    f"Generic solutions waste your budget. {offer} is "
                    f"configured for {persona_label} from day one."
                ),
                "cta": "See Your Custom Plan",
            },
        ]

        for i in range(min(count, len(persona_adaptations))):
            adaptation = persona_adaptations[i]
            variant = CreativeVariant(
                base_id=base.id,
                variant_type=vt.value,
                variant_number=i + 1,
                headline=adaptation["headline"],
                description=adaptation["description"],
                cta=adaptation["cta"],
                image_concept=base.image_concept,
                target_audience=persona_label,
                channel=base.channel,
                changes_from_base=[
                    f"Headline adapted for {persona_label} persona",
                    f"Description rewritten to address {persona_label} pain points",
                    f"CTA personalized for {persona_label}",
                ],
                rationale=(
                    f"Persona-specific messaging for {persona_label} increases "
                    f"relevance and click-through by speaking directly to the "
                    f"audience's identity and needs."
                ),
            )
            variant.id = f"{base.id}_{vt.value}_{variant.variant_number:02d}"
            variant.character_counts = {
                "headline": len(variant.headline),
                "description": len(variant.description),
                "cta": len(variant.cta),
            }
            results.append(variant)

        return results


# ============================================================================
# CrossChannelAdapter
# ============================================================================


def _truncate_to_limit(
    text: str, max_chars: int, preserve_words: bool = True
) -> str:
    """Truncate *text* to *max_chars*.

    When *preserve_words* is ``True``, the text is cut at the last word
    boundary that fits and ``...`` is appended.  Otherwise a hard cut is
    applied.
    """
    if len(text) <= max_chars:
        return text

    if not preserve_words:
        return text[: max_chars - 3].rstrip() + "..."

    # Leave room for the ellipsis
    truncated = text[: max_chars - 3]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated.rstrip() + "..."


def _adjust_tone(text: str, target_tone: str) -> str:
    """Return *text* with a tone-adjustment annotation.

    In a full implementation this would rewrite the copy to match the
    target tone.  Here it appends a structured note describing the
    intended adjustment so downstream humans or LLM passes can apply it.
    """
    return f"{text} [Tone: {target_tone}]"


def _add_hashtags(text: str, topic: str, platform: str, limit: int) -> str:
    """Append platform-appropriate hashtags for *topic*.

    Generates relevant hashtag suggestions based on the topic and
    platform conventions, respecting the per-platform *limit*.
    """
    # Build base hashtags from the topic
    tag_base = topic.strip().lower().replace(" ", "")
    candidates = [
        f"#{tag_base}",
        f"#{tag_base}tips",
        f"#marketing",
        f"#{platform.replace('_', '')}",
        f"#business",
        f"#{tag_base}strategy",
        f"#growth",
    ]

    # Platform-specific adjustments
    if "linkedin" in platform:
        candidates = [
            f"#{tag_base}",
            "#leadership",
            "#businessgrowth",
            f"#{tag_base}strategy",
            "#marketing",
        ]
    elif "tiktok" in platform:
        candidates = [
            f"#{tag_base}",
            "#fyp",
            "#businesstok",
            f"#{tag_base}hack",
            "#learnontiktok",
        ]
    elif "instagram" in platform:
        candidates = [
            f"#{tag_base}",
            f"#{tag_base}tips",
            "#marketing",
            "#smallbusiness",
            "#entrepreneur",
            f"#{tag_base}life",
            "#growthhacking",
        ]

    selected = candidates[:limit]
    hashtag_str = " ".join(selected)

    if text:
        return f"{text}\n\n{hashtag_str}"
    return hashtag_str


class CrossChannelAdapter:
    """Adapt creative content from one channel format to another.

    Applies character limits, tone adjustments, hashtag conventions, and
    format-specific restructuring when moving content between platforms.
    """

    def __init__(self) -> None:
        self._specs = get_channel_specs()

    # ------------------------------------------------------------------
    # Core adaptation
    # ------------------------------------------------------------------

    def adapt(
        self,
        source_content: Dict[str, Any],
        source_channel: str,
        target_channel: str,
    ) -> Dict[str, Any]:
        """Adapt *source_content* from *source_channel* to *target_channel*.

        Returns a new dict with character-limited, tone-adjusted, and
        format-compliant content for the target channel.
        """
        spec = self._specs.get(target_channel)
        if spec is None:
            return dict(source_content)

        headline = source_content.get("headline", "")
        description = source_content.get("description", "")
        cta = source_content.get("cta", "")
        topic = source_content.get("topic", headline)

        adapted_headline = _truncate_to_limit(headline, spec.headline_max_chars)
        adapted_description = _truncate_to_limit(description, spec.description_max_chars)
        adapted_cta = cta
        if spec.cta_max_chars:
            adapted_cta = _truncate_to_limit(cta, spec.cta_max_chars)

        if spec.tone_adjustment:
            adapted_headline = _adjust_tone(adapted_headline, spec.tone_adjustment)
            adapted_description = _adjust_tone(adapted_description, spec.tone_adjustment)

        result: Dict[str, Any] = {
            "headline": adapted_headline,
            "description": adapted_description,
            "cta": adapted_cta,
            "channel": target_channel,
            "source_channel": source_channel,
            "character_counts": {
                "headline": len(adapted_headline),
                "description": len(adapted_description),
                "cta": len(adapted_cta),
            },
        }

        if spec.hashtags_allowed and spec.hashtag_limit:
            result["hashtags"] = _add_hashtags("", topic, target_channel, spec.hashtag_limit)

        if spec.image_required:
            result["image_required"] = True
            result["image_concept"] = source_content.get(
                "image_concept", "Visual needed for this channel"
            )

        if spec.special_format:
            result["format"] = spec.special_format

        return result

    # ------------------------------------------------------------------
    # Blog -> Social
    # ------------------------------------------------------------------

    def adapt_blog_to_social(
        self, blog_content: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Convert a blog post into platform-native social posts.

        Accepts a dict with ``title``, ``body`` (or ``key_points``), and
        optional ``topic``.  Returns ``{platform: [post_dicts]}``.
        """
        title = blog_content.get("title", "")
        body = blog_content.get("body", "")
        key_points = blog_content.get("key_points", [])
        topic = blog_content.get("topic", title)

        # Extract usable takeaways from key points or body
        if not key_points and body:
            sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 20]
            key_points = sentences[:5]

        output: Dict[str, List[Dict[str, Any]]] = {}

        # -- LinkedIn posts (3): thought leadership angle --
        li_spec = self._specs["linkedin_organic"]
        linkedin_posts: List[Dict[str, Any]] = []

        linkedin_angles = [
            {
                "hook": f"Most people get {topic} wrong. Here is what actually works:",
                "style": "contrarian take",
            },
            {
                "hook": f"I spent years learning this lesson about {topic}:",
                "style": "personal story + lesson",
            },
            {
                "hook": f"3 things I wish someone told me about {topic} sooner:",
                "style": "listicle with depth",
            },
        ]

        for i, angle in enumerate(linkedin_angles):
            points_text = "\n".join(
                f"- {kp}" for kp in key_points[: 3]
            ) if key_points else f"Key insight from: {title}"

            post_body = f"{angle['hook']}\n\n{points_text}\n\nThe takeaway: {title}"
            post_body = _truncate_to_limit(post_body, li_spec.description_max_chars)
            post_body = _add_hashtags(post_body, topic, "linkedin_organic", 5)

            linkedin_posts.append({
                "platform": "linkedin",
                "post_number": i + 1,
                "style": angle["style"],
                "body": post_body,
                "image_suggestion": f"Quote card or data visual related to {topic}",
            })

        output["linkedin"] = linkedin_posts

        # -- Twitter/X posts (3): punchy takeaways --
        tw_spec = self._specs["twitter_organic"]
        twitter_posts: List[Dict[str, Any]] = []

        twitter_hooks = [
            f"{topic} in one sentence:",
            f"Hot take: {topic} is broken.",
            f"Thread: What nobody tells you about {topic}",
        ]

        for i, hook in enumerate(twitter_hooks):
            takeaway = key_points[i] if i < len(key_points) else title
            tweet = f"{hook}\n\n{takeaway}"
            tweet = _truncate_to_limit(tweet, tw_spec.description_max_chars)
            tweet = _add_hashtags(tweet, topic, "twitter_organic", 3)

            twitter_posts.append({
                "platform": "twitter",
                "post_number": i + 1,
                "body": tweet,
            })

        output["twitter"] = twitter_posts

        # -- Instagram captions (3): visual + caption --
        ig_spec = self._specs["instagram_organic"]
        instagram_posts: List[Dict[str, Any]] = []

        ig_hooks = [
            f"Save this for later. Here is the truth about {topic}.",
            f"Stop scrolling. This changes how you think about {topic}.",
            f"We broke down {topic} into 3 simple steps.",
        ]

        for i, hook in enumerate(ig_hooks):
            points_text = "\n".join(
                f"{j+1}. {kp}" for j, kp in enumerate(key_points[:3])
            ) if key_points else title
            caption = f"{hook}\n\n{points_text}\n\nLink in bio for the full breakdown."
            caption = _truncate_to_limit(caption, ig_spec.description_max_chars)
            caption = _add_hashtags(caption, topic, "instagram_organic", 15)

            instagram_posts.append({
                "platform": "instagram",
                "post_number": i + 1,
                "body": caption,
                "image_suggestion": f"Carousel slide or infographic about {topic}",
                "format": "carousel",
            })

        output["instagram"] = instagram_posts

        # -- Facebook posts (2): engagement-focused --
        fb_spec = self._specs["facebook_organic"]
        facebook_posts: List[Dict[str, Any]] = []

        fb_hooks = [
            f"Quick question: What is your biggest challenge with {topic}?",
            f"We just published our take on {topic}. The response has been wild.",
        ]

        for i, hook in enumerate(fb_hooks):
            body_text = key_points[0] if key_points else title
            post = f"{hook}\n\n{body_text}\n\nDrop a comment with your thoughts."
            post = _truncate_to_limit(post, fb_spec.description_max_chars)

            facebook_posts.append({
                "platform": "facebook",
                "post_number": i + 1,
                "body": post,
                "engagement_prompt": "Comment-focused CTA for algorithm boost",
            })

        output["facebook"] = facebook_posts

        # -- TikTok script concepts (2): hook + teach --
        tiktok_scripts: List[Dict[str, Any]] = []

        tiktok_hooks = [
            {
                "hook": f"Nobody talks about this {topic} mistake",
                "teach": key_points[0] if key_points else title,
                "cta": "Follow for more marketing breakdowns",
            },
            {
                "hook": f"3 things about {topic} that changed my business",
                "teach": "\n".join(key_points[:3]) if key_points else title,
                "cta": "Save this and share it with your team",
            },
        ]

        for i, concept in enumerate(tiktok_hooks):
            tiktok_scripts.append({
                "platform": "tiktok",
                "script_number": i + 1,
                "hook": concept["hook"],
                "teach_segment": concept["teach"],
                "cta": concept["cta"],
                "format": "talking_head_or_text_overlay",
                "target_duration_seconds": 30,
            })

        output["tiktok"] = tiktok_scripts

        return output

    # ------------------------------------------------------------------
    # Landing Page -> Ads
    # ------------------------------------------------------------------

    def adapt_landing_page_to_ads(
        self, landing_page: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Convert landing page copy into platform-ready ad sets.

        Accepts a dict with ``hero_headline``, ``value_props`` (list of
        strings), ``proof_point``, ``offer``, and ``cta``.
        Returns ``{platform: [ad_dicts]}``.
        """
        hero = landing_page.get("hero_headline", "")
        value_props = landing_page.get("value_props", [])
        proof = landing_page.get("proof_point", "")
        offer = landing_page.get("offer", hero)
        cta = landing_page.get("cta", "Learn More")

        output: Dict[str, List[Dict[str, Any]]] = {}

        # -- Google Search Ads (3 sets) --
        g_spec = self._specs["google_ads_search"]
        google_ads: List[Dict[str, Any]] = []

        google_headlines_pool = [
            _truncate_to_limit(hero, g_spec.headline_max_chars),
            _truncate_to_limit(offer, g_spec.headline_max_chars),
            _truncate_to_limit(proof, g_spec.headline_max_chars) if proof else "Proven Results",
        ]
        vp_headlines = [
            _truncate_to_limit(vp, g_spec.headline_max_chars) for vp in value_props[:3]
        ]
        google_headlines_pool.extend(vp_headlines)

        for i in range(3):
            h1_idx = i % len(google_headlines_pool)
            h2_idx = (i + 1) % len(google_headlines_pool)
            h3_idx = (i + 2) % len(google_headlines_pool)

            desc = ""
            if value_props:
                desc = ". ".join(value_props[:2])
            elif proof:
                desc = f"{offer}. {proof}"
            else:
                desc = offer

            google_ads.append({
                "platform": "google_search",
                "ad_number": i + 1,
                "headline_1": google_headlines_pool[h1_idx],
                "headline_2": google_headlines_pool[h2_idx],
                "headline_3": google_headlines_pool[h3_idx],
                "description_1": _truncate_to_limit(desc, g_spec.description_max_chars),
                "description_2": _truncate_to_limit(
                    f"{cta}. {proof}" if proof else cta,
                    g_spec.description_max_chars,
                ),
                "character_counts": {
                    "headline_1": len(google_headlines_pool[h1_idx]),
                    "headline_2": len(google_headlines_pool[h2_idx]),
                    "headline_3": len(google_headlines_pool[h3_idx]),
                },
            })

        output["google_search"] = google_ads

        # -- Meta Feed Ads (2 sets) --
        m_spec = self._specs["meta_ads_feed"]
        meta_ads: List[Dict[str, Any]] = []

        meta_angles = [
            {
                "primary_text": (
                    f"{proof}\n\n" if proof else ""
                ) + (
                    "\n".join(f"- {vp}" for vp in value_props[:3])
                    if value_props
                    else hero
                ) + f"\n\n{cta}",
                "headline": hero,
            },
            {
                "primary_text": (
                    f"Stop doing it the old way.\n\n{offer} gives you "
                    + (f"{value_props[0].lower()}" if value_props else "better results")
                    + f".\n\n{cta}"
                ),
                "headline": offer,
            },
        ]

        for i, angle in enumerate(meta_angles):
            meta_ads.append({
                "platform": "meta_feed",
                "ad_number": i + 1,
                "primary_text": _truncate_to_limit(
                    angle["primary_text"], m_spec.description_max_chars
                ),
                "headline": _truncate_to_limit(angle["headline"], m_spec.headline_max_chars),
                "cta_button": _truncate_to_limit(cta, m_spec.cta_max_chars or 25),
                "image_required": True,
            })

        output["meta_feed"] = meta_ads

        # -- LinkedIn Ads (2 sets) --
        li_spec = self._specs["linkedin_ads"]
        linkedin_ads: List[Dict[str, Any]] = []

        li_angles = [
            {
                "intro_text": (
                    f"{proof}. " if proof else ""
                ) + f"See how {offer} delivers results.",
                "headline": hero,
            },
            {
                "intro_text": (
                    f"Your team deserves better tools. {offer} "
                    + (f"provides {value_props[0].lower()}" if value_props else "drives ROI")
                    + "."
                ),
                "headline": offer,
            },
        ]

        for i, angle in enumerate(li_angles):
            linkedin_ads.append({
                "platform": "linkedin",
                "ad_number": i + 1,
                "intro_text": _truncate_to_limit(
                    angle["intro_text"], li_spec.description_max_chars
                ),
                "headline": _truncate_to_limit(angle["headline"], li_spec.headline_max_chars),
                "cta_button": cta,
            })

        output["linkedin"] = linkedin_ads

        return output

    # ------------------------------------------------------------------
    # Email -> Social
    # ------------------------------------------------------------------

    def adapt_email_to_social(
        self, email_content: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Convert email content into social posts.

        Accepts a dict with ``subject``, ``body``, and ``cta``.
        Returns ``{platform: [post_dicts]}``.
        """
        subject = email_content.get("subject", "")
        body = email_content.get("body", "")
        cta = email_content.get("cta", "")
        topic = email_content.get("topic", subject)

        # Extract key sentences from body
        sentences = [s.strip() for s in body.split(".") if len(s.strip()) > 15]
        key_points = sentences[:5]

        output: Dict[str, List[Dict[str, Any]]] = {}

        # LinkedIn (2 posts)
        li_spec = self._specs["linkedin_organic"]
        linkedin_posts: List[Dict[str, Any]] = []

        for i in range(2):
            hook = subject if i == 0 else f"Here is something most people miss about {topic}:"
            body_text = key_points[i] if i < len(key_points) else subject
            post = f"{hook}\n\n{body_text}\n\n{cta}"
            post = _truncate_to_limit(post, li_spec.description_max_chars)
            post = _add_hashtags(post, topic, "linkedin_organic", 5)
            linkedin_posts.append({
                "platform": "linkedin",
                "post_number": i + 1,
                "body": post,
            })

        output["linkedin"] = linkedin_posts

        # Twitter (2 posts)
        tw_spec = self._specs["twitter_organic"]
        twitter_posts: List[Dict[str, Any]] = []

        for i in range(2):
            takeaway = key_points[i] if i < len(key_points) else subject
            tweet = f"{takeaway}"
            if cta:
                tweet += f"\n\n{cta}"
            tweet = _truncate_to_limit(tweet, tw_spec.description_max_chars)
            tweet = _add_hashtags(tweet, topic, "twitter_organic", 2)
            twitter_posts.append({
                "platform": "twitter",
                "post_number": i + 1,
                "body": tweet,
            })

        output["twitter"] = twitter_posts

        # Facebook (1 post)
        fb_spec = self._specs["facebook_organic"]
        fb_body = f"{subject}\n\n"
        fb_body += "\n".join(f"- {kp}" for kp in key_points[:3])
        fb_body += f"\n\n{cta}"
        fb_body = _truncate_to_limit(fb_body, fb_spec.description_max_chars)

        output["facebook"] = [{
            "platform": "facebook",
            "post_number": 1,
            "body": fb_body,
        }]

        return output

    # ------------------------------------------------------------------
    # Video -> Shorts
    # ------------------------------------------------------------------

    def adapt_video_to_shorts(
        self, video_script: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify short-form clip opportunities from a long-form video.

        Accepts a dict with ``title``, ``sections`` (list of
        ``{timestamp, topic, script_text}``), and optional ``cta``.
        Returns a list of short-form clip specifications.
        """
        title = video_script.get("title", "")
        sections = video_script.get("sections", [])
        cta = video_script.get("cta", "Follow for more")

        if not sections:
            # If no sections provided, generate generic clip concepts
            return [
                {
                    "clip_number": 1,
                    "start_time_concept": "Opening hook",
                    "hook": f"You need to hear this about {title}",
                    "key_message": title,
                    "cta": cta,
                    "target_duration_seconds": 30,
                    "platform_targets": ["tiktok", "instagram_reels", "youtube_shorts"],
                },
                {
                    "clip_number": 2,
                    "start_time_concept": "Key insight moment",
                    "hook": f"Nobody talks about this part of {title}",
                    "key_message": f"Core insight from {title}",
                    "cta": cta,
                    "target_duration_seconds": 45,
                    "platform_targets": ["tiktok", "instagram_reels", "youtube_shorts"],
                },
                {
                    "clip_number": 3,
                    "start_time_concept": "Closing takeaway",
                    "hook": f"One thing to remember about {title}",
                    "key_message": f"Main takeaway from {title}",
                    "cta": cta,
                    "target_duration_seconds": 15,
                    "platform_targets": ["tiktok", "instagram_reels", "youtube_shorts"],
                },
            ]

        clips: List[Dict[str, Any]] = []

        # Score each section for short-form potential
        for idx, section in enumerate(sections):
            timestamp = section.get("timestamp", f"{idx * 5}:00")
            topic = section.get("topic", "")
            script_text = section.get("script_text", "")

            # Every section with script text > 30 chars is a candidate
            if len(script_text) < 30:
                continue

            # Build hook from the topic
            hook_options = [
                f"Wait until you hear this about {topic}",
                f"This {topic} hack changed everything",
                f"The truth about {topic} nobody shares",
            ]

            clip = {
                "clip_number": len(clips) + 1,
                "start_time_concept": f"Section '{topic}' starting at {timestamp}",
                "hook": hook_options[idx % len(hook_options)],
                "key_message": _truncate_to_limit(script_text, 200, preserve_words=True),
                "cta": cta,
                "target_duration_seconds": min(60, max(15, len(script_text) // 10)),
                "platform_targets": ["tiktok", "instagram_reels", "youtube_shorts"],
                "source_timestamp": timestamp,
            }
            clips.append(clip)

            if len(clips) >= 5:
                break

        return clips if clips else [
            {
                "clip_number": 1,
                "start_time_concept": "Opening hook",
                "hook": f"Watch this breakdown of {title}",
                "key_message": title,
                "cta": cta,
                "target_duration_seconds": 30,
                "platform_targets": ["tiktok", "instagram_reels", "youtube_shorts"],
            }
        ]

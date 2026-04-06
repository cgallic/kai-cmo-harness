"""Base models for archetype-specific messaging frameworks.

Every archetype (local service, ecommerce, professional services,
multi-location) assembles a ``MessagingFramework`` from these building
blocks.  Downstream systems -- copy generation, creative variant
engine, and landing page generator -- consume the framework to produce
on-brand, archetype-appropriate content.

Uses the ``dataclass`` + ``SerializableModel`` pattern from
``kai/runtime/models.py`` so the module works without pydantic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Serialization mixin (mirrors kai/runtime/models.py)
# ---------------------------------------------------------------------------

class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# MessageAngle
# ---------------------------------------------------------------------------

@dataclass
class MessageAngle(SerializableModel):
    """A single persuasion angle with ready-to-use copy templates.

    ``headline_templates`` and ``subheadline_templates`` use
    ``{placeholder}`` tokens for business-specific customization at
    render time.
    """

    angle_name: str
    description: str
    headline_templates: List[str]
    subheadline_templates: List[str]
    value_props: List[str]
    tone: str  # "confident" | "empathetic" | "urgent" | "authoritative" | "conversational"
    best_for: List[str]  # e.g. ["landing_page", "ad", "email"]


# ---------------------------------------------------------------------------
# ObjectionHandler
# ---------------------------------------------------------------------------

@dataclass
class ObjectionHandler(SerializableModel):
    """A customer objection paired with a reframe and response copy.

    ``proof_type`` indicates the most effective evidence:
    ``"testimonial"``, ``"statistic"``, ``"case_study"``,
    ``"guarantee"``, or ``"comparison"``.
    """

    objection: str
    reframe: str
    response_templates: List[str]
    proof_type: str  # "testimonial" | "statistic" | "case_study" | "guarantee" | "comparison"


# ---------------------------------------------------------------------------
# SeasonalHook
# ---------------------------------------------------------------------------

@dataclass
class SeasonalHook(SerializableModel):
    """Connects a calendar season or event to the business with
    urgency-driven copy templates and offer ideas.

    ``relevance_months`` uses 1-12 (January = 1).
    """

    season_or_event: str
    relevance_months: List[int]
    hook_angle: str
    headline_templates: List[str]
    offer_suggestions: List[str]
    urgency_element: str


# ---------------------------------------------------------------------------
# CTATemplate
# ---------------------------------------------------------------------------

@dataclass
class CTATemplate(SerializableModel):
    """A call-to-action template with funnel-stage alignment.

    ``cta_type``: ``"primary"`` | ``"secondary"`` | ``"soft"``
    ``funnel_stage``: ``"awareness"`` | ``"consideration"`` | ``"decision"``
    """

    cta_text: str
    cta_type: str  # "primary" | "secondary" | "soft"
    funnel_stage: str  # "awareness" | "consideration" | "decision"
    best_for: List[str]
    supporting_text: Optional[str] = None


# ---------------------------------------------------------------------------
# MessagingFramework
# ---------------------------------------------------------------------------

@dataclass
class MessagingFramework(SerializableModel):
    """Complete messaging toolkit for a single business archetype.

    Aggregates message angles, objection handlers, seasonal hooks,
    CTA templates, tone guidelines, forbidden phrases, and proof-type
    priorities into one portable structure that downstream generators
    consume.
    """

    archetype: str
    core_message: str
    message_angles: List[MessageAngle]
    objection_handlers: List[ObjectionHandler]
    seasonal_hooks: List[SeasonalHook]
    cta_library: List[CTATemplate]
    tone_guidelines: Dict[str, str]
    forbidden_phrases: List[str]
    proof_priorities: List[str]

    # -- convenience helpers ------------------------------------------------

    def get_angles_for(self, content_type: str) -> List[MessageAngle]:
        """Return message angles whose ``best_for`` includes *content_type*."""
        return [a for a in self.message_angles if content_type in a.best_for]

    def get_ctas_for(
        self,
        content_type: str,
        funnel_stage: Optional[str] = None,
    ) -> List[CTATemplate]:
        """Return CTAs that match *content_type* and optional *funnel_stage*."""
        results = [c for c in self.cta_library if content_type in c.best_for]
        if funnel_stage is not None:
            results = [c for c in results if c.funnel_stage == funnel_stage]
        return results

    def get_hooks_for_month(self, month: int) -> List[SeasonalHook]:
        """Return seasonal hooks active during *month* (1-12)."""
        return [h for h in self.seasonal_hooks if month in h.relevance_months]

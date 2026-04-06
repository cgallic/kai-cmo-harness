"""Landing page block generation and visual request workflow.

Generates landing pages as composable blocks (hero, value props, social
proof, process, objections, offer, CTA, comparison, FAQ, trust bar),
manages visual asset requests through a complete lifecycle, and assembles
blocks into optimal page structures with combined schema markup.

Uses the ``dataclass`` + ``SerializableModel`` pattern from
``kai/runtime/models.py``.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel

# ---------------------------------------------------------------------------
# Optional YAML support — graceful fallback
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _yaml = None  # type: ignore[assignment]


# ============================================================================
# Enums
# ============================================================================


class BlockType(str, Enum):
    """Canonical landing page block types."""

    hero = "hero"
    value_prop = "value_prop"
    social_proof = "social_proof"
    process = "process"
    objection_handler = "objection_handler"
    offer = "offer"
    cta = "cta"
    comparison = "comparison"
    faq = "faq"
    trust_bar = "trust_bar"


class VisualRequestStatus(str, Enum):
    """Lifecycle states for a visual asset request."""

    requested = "requested"
    in_progress = "in_progress"
    delivered = "delivered"
    approved = "approved"
    deployed = "deployed"


# ============================================================================
# Data models
# ============================================================================


@dataclass
class LandingPageBlock(SerializableModel):
    """A single composable landing page block."""

    id: str = ""
    block_type: str = ""
    position: int = 1
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    body_copy: Optional[str] = None
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    supporting_elements: List[Dict[str, Any]] = field(default_factory=list)
    visual_requirements: List[str] = field(default_factory=list)
    html_structure_suggestion: str = ""
    schema_markup: Optional[str] = None
    data_requirements: List[str] = field(default_factory=list)
    archetype_notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"block_{uuid.uuid4().hex[:8]}"


@dataclass
class VisualRequest(SerializableModel):
    """A request for a visual asset tied to a landing page block."""

    id: str = ""
    block_id: str = ""
    description: str = ""
    dimensions: str = "1920x1080"
    format: str = "photo"
    style_reference: Optional[str] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    priority: str = "medium"
    deadline: Optional[str] = None
    status: str = VisualRequestStatus.requested.value
    delivered_asset_url: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"vr_{uuid.uuid4().hex[:8]}"


@dataclass
class PageStructure(SerializableModel):
    """A complete assembled landing page."""

    page_id: str = ""
    page_type: str = "landing_page"
    title: str = ""
    meta_description: str = ""
    blocks: List[LandingPageBlock] = field(default_factory=list)
    visual_requests: List[VisualRequest] = field(default_factory=list)
    schema_markup: str = ""
    estimated_word_count: int = 0
    archetype: str = "local_service"

    def __post_init__(self) -> None:
        if not self.page_id:
            self.page_id = f"page_{uuid.uuid4().hex[:8]}"


# ============================================================================
# LandingPageBlockGenerator
# ============================================================================


class LandingPageBlockGenerator:
    """Generate individual landing page blocks with structured copy,
    semantic HTML suggestions, and schema markup."""

    def __init__(self, business_profile: Any = None) -> None:
        self.business_profile = business_profile

    # ------------------------------------------------------------------
    # Hero
    # ------------------------------------------------------------------

    def generate_hero_block(
        self,
        headline: str,
        subheadline: str,
        primary_cta: str,
        cta_url: str,
        trust_badges: Optional[List[str]] = None,
        background_image_concept: Optional[str] = None,
    ) -> LandingPageBlock:
        """Full-width hero section -- always position 1.

        Includes headline, subheadline, primary CTA, optional trust
        badges (rendered as small icons/text below the CTA), and an
        optional background image concept for the visual request.
        """
        badges = trust_badges or []

        supporting: List[Dict[str, Any]] = []
        if badges:
            supporting.append({
                "type": "trust_badges",
                "items": badges,
                "placement": "below_cta",
            })

        visual_reqs: List[str] = []
        if background_image_concept:
            visual_reqs.append(
                f"Hero background image: {background_image_concept}"
            )

        badge_html = ""
        if badges:
            badge_items = "\n      ".join(
                f'<span class="trust-badge">{b}</span>' for b in badges
            )
            badge_html = (
                f'\n    <div class="trust-badges">\n'
                f"      {badge_items}\n"
                f"    </div>"
            )

        html = (
            '<section class="hero" role="banner">\n'
            '  <div class="hero-content">\n'
            f"    <h1>{headline}</h1>\n"
            f"    <p class=\"hero-sub\">{subheadline}</p>\n"
            f'    <a href="{cta_url}" class="cta-primary">{primary_cta}</a>'
            f"{badge_html}\n"
            "  </div>\n"
        )
        if background_image_concept:
            html += (
                f'  <div class="hero-bg" style="background-image: url(\'{{hero_bg_url}}\')">'
                f"<!-- {background_image_concept} --></div>\n"
            )
        html += "</section>"

        schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": headline,
            "description": subheadline,
            "mainEntity": {
                "@type": "WebPage",
                "name": headline,
            },
        }, indent=2)

        return LandingPageBlock(
            block_type=BlockType.hero.value,
            position=1,
            headline=headline,
            subheadline=subheadline,
            cta_text=primary_cta,
            cta_url=cta_url,
            supporting_elements=supporting,
            visual_requirements=visual_reqs,
            html_structure_suggestion=html,
            schema_markup=schema,
            data_requirements=["business_name", "primary_offer", "hero_image"],
            archetype_notes=(
                "Local service: emphasize speed, trust badges, and phone CTA. "
                "Ecommerce: lead with offer and social proof count. "
                "Professional services: lead with credibility and outcome."
            ),
        )

    # ------------------------------------------------------------------
    # Value props
    # ------------------------------------------------------------------

    def generate_value_prop_block(
        self,
        value_props: List[Dict[str, str]],
        section_headline: Optional[str] = None,
    ) -> LandingPageBlock:
        """Grid of value proposition cards, each with icon concept, title,
        and description.

        *value_props*: list of ``{icon_concept, title, description}``.
        Typically 3-4 items.
        """
        section_headline = section_headline or "Why Choose Us"

        supporting: List[Dict[str, Any]] = []
        for vp in value_props:
            supporting.append({
                "type": "value_prop_card",
                "icon_concept": vp.get("icon_concept", ""),
                "title": vp.get("title", ""),
                "description": vp.get("description", ""),
            })

        card_html_items = "\n    ".join(
            (
                f'<div class="vp-card">\n'
                f'      <div class="vp-icon"><!-- {vp.get("icon_concept", "icon")} --></div>\n'
                f'      <h3>{vp.get("title", "")}</h3>\n'
                f'      <p>{vp.get("description", "")}</p>\n'
                f"    </div>"
            )
            for vp in value_props
        )

        html = (
            '<section class="value-props">\n'
            f"  <h2>{section_headline}</h2>\n"
            f'  <div class="vp-grid">\n'
            f"    {card_html_items}\n"
            "  </div>\n"
            "</section>"
        )

        body_copy = "; ".join(
            f"{vp.get('title', '')}: {vp.get('description', '')}"
            for vp in value_props
        )

        return LandingPageBlock(
            block_type=BlockType.value_prop.value,
            position=2,
            headline=section_headline,
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=[],  # Icons are conceptual, no real images
            html_structure_suggestion=html,
            data_requirements=["value_propositions", "differentiators"],
            archetype_notes=(
                "Local service: use concrete benefits (fast response, licensed, "
                "guaranteed). Ecommerce: focus on shipping, returns, quality. "
                "Professional services: emphasize expertise and process."
            ),
        )

    # ------------------------------------------------------------------
    # Social proof
    # ------------------------------------------------------------------

    def generate_social_proof_block(
        self,
        testimonials: List[Dict[str, Any]],
        review_aggregate: Optional[Dict[str, Any]] = None,
    ) -> LandingPageBlock:
        """Testimonial carousel or grid with optional aggregate badge.

        *testimonials*: list of ``{quote, customer_name, rating, service_type}``.
        *review_aggregate*: ``{count, avg_rating, platform}``.
        """
        supporting: List[Dict[str, Any]] = []
        for t in testimonials:
            supporting.append({
                "type": "testimonial",
                "quote": t.get("quote", ""),
                "customer_name": t.get("customer_name", ""),
                "rating": t.get("rating", 5),
                "service_type": t.get("service_type", ""),
            })

        if review_aggregate:
            supporting.append({
                "type": "review_aggregate",
                "count": review_aggregate.get("count", 0),
                "avg_rating": review_aggregate.get("avg_rating", 0.0),
                "platform": review_aggregate.get("platform", "google"),
            })

        # Build testimonial cards HTML
        testimonial_cards = "\n    ".join(
            (
                f'<div class="testimonial-card">\n'
                f'      <div class="stars">{"*" * t.get("rating", 5)}</div>\n'
                f'      <blockquote>"{t.get("quote", "")}"</blockquote>\n'
                f'      <cite>{t.get("customer_name", "")}'
                f'{", " + t.get("service_type") if t.get("service_type") else ""}'
                f"</cite>\n"
                f"    </div>"
            )
            for t in testimonials
        )

        aggregate_html = ""
        if review_aggregate:
            aggregate_html = (
                f'\n  <div class="review-aggregate">\n'
                f'    <span class="stars">{review_aggregate.get("avg_rating", "")}</span>\n'
                f'    <span>{review_aggregate.get("count", 0)} '
                f'{review_aggregate.get("platform", "Google")} reviews</span>\n'
                f"  </div>"
            )

        html = (
            '<section class="social-proof">\n'
            '  <h2>What Our Customers Say</h2>\n'
            f'  <div class="testimonial-grid">\n'
            f"    {testimonial_cards}\n"
            f"  </div>{aggregate_html}\n"
            "</section>"
        )

        # Schema: Review + AggregateRating
        schema_obj: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "review": [],
        }

        for t in testimonials:
            schema_obj["review"].append({
                "@type": "Review",
                "author": {
                    "@type": "Person",
                    "name": t.get("customer_name", ""),
                },
                "reviewBody": t.get("quote", ""),
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": str(t.get("rating", 5)),
                    "bestRating": "5",
                },
            })

        if review_aggregate:
            schema_obj["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(review_aggregate.get("avg_rating", "")),
                "reviewCount": str(review_aggregate.get("count", "")),
                "bestRating": "5",
                "worstRating": "1",
            }

        visual_reqs = []
        for t in testimonials:
            if t.get("customer_name"):
                visual_reqs.append(
                    f"Customer photo: headshot of {t['customer_name']} for testimonial card"
                )

        return LandingPageBlock(
            block_type=BlockType.social_proof.value,
            position=3,
            headline="What Our Customers Say",
            supporting_elements=supporting,
            visual_requirements=visual_reqs,
            html_structure_suggestion=html,
            schema_markup=json.dumps(schema_obj, indent=2),
            data_requirements=[
                "testimonials",
                "review_count",
                "average_rating",
                "review_platform",
            ],
            archetype_notes=(
                "Local service: use real customer names and service types. "
                "Include city for local trust. Ecommerce: emphasize product "
                "quality and shipping speed. Professional services: use "
                "titles and company names for credibility."
            ),
        )

    # ------------------------------------------------------------------
    # Process
    # ------------------------------------------------------------------

    def generate_process_block(
        self,
        steps: List[Dict[str, str]],
        section_headline: Optional[str] = None,
    ) -> LandingPageBlock:
        """Numbered steps showing the customer journey.

        *steps*: list of ``{step_number, title, description}``.
        Typically 3-5 steps.
        """
        section_headline = section_headline or "How It Works"

        supporting: List[Dict[str, Any]] = []
        for s in steps:
            supporting.append({
                "type": "process_step",
                "step_number": s.get("step_number", ""),
                "title": s.get("title", ""),
                "description": s.get("description", ""),
                "icon_concept": f"Step {s.get('step_number', '')} icon: {s.get('title', '')}",
            })

        step_html_items = "\n    ".join(
            (
                f'<div class="process-step">\n'
                f'      <span class="step-number">{s.get("step_number", "")}</span>\n'
                f'      <h3>{s.get("title", "")}</h3>\n'
                f'      <p>{s.get("description", "")}</p>\n'
                f"    </div>"
            )
            for s in steps
        )

        html = (
            '<section class="process">\n'
            f"  <h2>{section_headline}</h2>\n"
            f'  <div class="process-steps">\n'
            f"    {step_html_items}\n"
            "  </div>\n"
            "</section>"
        )

        body_copy = " ".join(
            f"Step {s.get('step_number', '')}: {s.get('title', '')} - {s.get('description', '')}."
            for s in steps
        )

        return LandingPageBlock(
            block_type=BlockType.process.value,
            position=4,
            headline=section_headline,
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=[],
            html_structure_suggestion=html,
            data_requirements=["process_steps", "service_workflow"],
            archetype_notes=(
                "Keep to 3-5 steps. Fewer steps reduce perceived friction. "
                "Local service: emphasize 'call, schedule, done' simplicity. "
                "Professional services: show discovery, strategy, execution phases."
            ),
        )

    # ------------------------------------------------------------------
    # Objection handler
    # ------------------------------------------------------------------

    def generate_objection_handler_block(
        self,
        objections: List[Dict[str, str]],
        format_type: str = "faq",
    ) -> LandingPageBlock:
        """FAQ accordion or myth-busting cards.

        *objections*: list of ``{question, answer}`` (FAQ format) or
        ``{myth, truth}`` (myth-busting format).
        *format_type*: ``"faq"`` or ``"myths"``.
        """
        supporting: List[Dict[str, Any]] = []
        for obj in objections:
            if format_type == "myths":
                supporting.append({
                    "type": "myth_truth",
                    "myth": obj.get("myth", ""),
                    "truth": obj.get("truth", ""),
                })
            else:
                supporting.append({
                    "type": "faq_item",
                    "question": obj.get("question", ""),
                    "answer": obj.get("answer", ""),
                })

        if format_type == "myths":
            items_html = "\n    ".join(
                (
                    f'<div class="myth-card">\n'
                    f'      <div class="myth"><strong>Myth:</strong> {obj.get("myth", "")}</div>\n'
                    f'      <div class="truth"><strong>Truth:</strong> {obj.get("truth", "")}</div>\n'
                    f"    </div>"
                )
                for obj in objections
            )
            html = (
                '<section class="objection-handler myth-busters">\n'
                "  <h2>Common Myths vs. Reality</h2>\n"
                f'  <div class="myths-grid">\n'
                f"    {items_html}\n"
                "  </div>\n"
                "</section>"
            )
            schema_markup = None
            headline = "Common Myths vs. Reality"
        else:
            items_html = "\n    ".join(
                (
                    f'<details class="faq-item">\n'
                    f'      <summary>{obj.get("question", "")}</summary>\n'
                    f'      <p>{obj.get("answer", "")}</p>\n'
                    f"    </details>"
                )
                for obj in objections
            )
            html = (
                '<section class="objection-handler faq">\n'
                "  <h2>Frequently Asked Questions</h2>\n"
                f'  <div class="faq-list">\n'
                f"    {items_html}\n"
                "  </div>\n"
                "</section>"
            )
            # FAQPage schema
            faq_entities = []
            for obj in objections:
                faq_entities.append({
                    "@type": "Question",
                    "name": obj.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": obj.get("answer", ""),
                    },
                })
            schema_markup = json.dumps({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": faq_entities,
            }, indent=2)
            headline = "Frequently Asked Questions"

        body_copy = " ".join(
            f"Q: {obj.get('question', obj.get('myth', ''))} "
            f"A: {obj.get('answer', obj.get('truth', ''))}"
            for obj in objections
        )

        return LandingPageBlock(
            block_type=BlockType.objection_handler.value,
            position=5,
            headline=headline,
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=[],
            html_structure_suggestion=html,
            schema_markup=schema_markup,
            data_requirements=["common_objections", "faq_pairs"],
            archetype_notes=(
                "Address the top 5-7 objections. Local service: price, "
                "timeline, insurance, guarantees. Ecommerce: shipping, returns, "
                "sizing. Professional services: process, pricing model, timeline."
            ),
        )

    # ------------------------------------------------------------------
    # Offer
    # ------------------------------------------------------------------

    def generate_offer_block(
        self,
        offer_headline: str,
        offer_details: str,
        price_display: Optional[str] = None,
        urgency_element: Optional[str] = None,
        guarantee: Optional[str] = None,
    ) -> LandingPageBlock:
        """Centered offer section with pricing, urgency, and guarantee."""

        supporting: List[Dict[str, Any]] = [
            {"type": "offer_details", "text": offer_details},
        ]
        if price_display:
            supporting.append({"type": "pricing", "text": price_display})
        if urgency_element:
            supporting.append({"type": "urgency", "text": urgency_element})
        if guarantee:
            supporting.append({"type": "guarantee", "text": guarantee})

        visual_reqs: List[str] = []
        if price_display:
            visual_reqs.append(
                f"Offer graphic: visual representation of {offer_headline} with pricing"
            )

        price_html = ""
        if price_display:
            price_html = f'\n    <div class="price-display">{price_display}</div>'

        urgency_html = ""
        if urgency_element:
            urgency_html = f'\n    <div class="urgency">{urgency_element}</div>'

        guarantee_html = ""
        if guarantee:
            guarantee_html = (
                f'\n    <div class="guarantee-badge">'
                f'{guarantee}</div>'
            )

        html = (
            '<section class="offer">\n'
            f"  <h2>{offer_headline}</h2>\n"
            f"  <p>{offer_details}</p>\n"
            f"  <div class=\"offer-details\">"
            f"{price_html}{urgency_html}{guarantee_html}\n"
            "  </div>\n"
            "</section>"
        )

        body_copy = offer_details
        if price_display:
            body_copy += f" {price_display}."
        if guarantee:
            body_copy += f" {guarantee}."

        return LandingPageBlock(
            block_type=BlockType.offer.value,
            position=6,
            headline=offer_headline,
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=visual_reqs,
            html_structure_suggestion=html,
            data_requirements=["offer_details", "pricing", "guarantee_terms"],
            archetype_notes=(
                "Make the offer irresistible: combine price anchor, urgency, "
                "and risk reversal (guarantee). Local service: free estimate "
                "or first-visit discount. Ecommerce: limited-time pricing."
            ),
        )

    # ------------------------------------------------------------------
    # CTA
    # ------------------------------------------------------------------

    def generate_cta_block(
        self,
        headline: str,
        cta_text: str,
        cta_url: str,
        reassurance_text: Optional[str] = None,
        secondary_cta: Optional[Dict[str, str]] = None,
    ) -> LandingPageBlock:
        """Final CTA section near the bottom of the page.

        Includes reassurance text and an optional secondary CTA (e.g.,
        phone number for local service businesses).
        """
        supporting: List[Dict[str, Any]] = []
        if reassurance_text:
            supporting.append({
                "type": "reassurance",
                "text": reassurance_text,
            })
        if secondary_cta:
            supporting.append({
                "type": "secondary_cta",
                "text": secondary_cta.get("text", ""),
                "url": secondary_cta.get("url", ""),
            })

        reassurance_html = ""
        if reassurance_text:
            reassurance_html = (
                f'\n    <p class="reassurance">{reassurance_text}</p>'
            )

        secondary_html = ""
        if secondary_cta:
            secondary_html = (
                f'\n    <a href="{secondary_cta.get("url", "")}" '
                f'class="cta-secondary">{secondary_cta.get("text", "")}</a>'
            )

        html = (
            '<section class="final-cta">\n'
            f"  <h2>{headline}</h2>\n"
            f'  <div class="cta-container">\n'
            f'    <a href="{cta_url}" class="cta-primary cta-large">{cta_text}</a>'
            f"{reassurance_html}{secondary_html}\n"
            "  </div>\n"
            "</section>"
        )

        body_copy = headline
        if reassurance_text:
            body_copy += f" {reassurance_text}"

        return LandingPageBlock(
            block_type=BlockType.cta.value,
            position=7,
            headline=headline,
            body_copy=body_copy,
            cta_text=cta_text,
            cta_url=cta_url,
            supporting_elements=supporting,
            visual_requirements=[],
            html_structure_suggestion=html,
            data_requirements=["primary_cta_url", "phone_number"],
            archetype_notes=(
                "Local service: ALWAYS include a phone number as secondary "
                "CTA (e.g., 'Call Us Instead: (555) 123-4567'). This is critical "
                "for local businesses where phone leads convert at 2-3x web forms. "
                "Ecommerce: single strong CTA, no distractions. "
                "Professional services: 'Schedule a Consultation' with calendar link."
            ),
        )

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def generate_comparison_block(
        self,
        comparison_items: List[Dict[str, Any]],
        us_label: str = "Us",
        them_label: str = "Others",
    ) -> LandingPageBlock:
        """Feature comparison table with checkmarks and X marks.

        *comparison_items*: list of ``{feature, us_value, them_value}``.
        """
        supporting: List[Dict[str, Any]] = []
        for item in comparison_items:
            supporting.append({
                "type": "comparison_row",
                "feature": item.get("feature", ""),
                "us_value": item.get("us_value", ""),
                "them_value": item.get("them_value", ""),
            })

        rows_html = "\n      ".join(
            (
                f"<tr>\n"
                f'        <td>{item.get("feature", "")}</td>\n'
                f'        <td class="us">{item.get("us_value", "")}</td>\n'
                f'        <td class="them">{item.get("them_value", "")}</td>\n'
                f"      </tr>"
            )
            for item in comparison_items
        )

        html = (
            '<section class="comparison">\n'
            '  <h2>How We Compare</h2>\n'
            '  <table class="comparison-table">\n'
            "    <thead>\n"
            "      <tr>\n"
            "        <th>Feature</th>\n"
            f"        <th>{us_label}</th>\n"
            f"        <th>{them_label}</th>\n"
            "      </tr>\n"
            "    </thead>\n"
            "    <tbody>\n"
            f"      {rows_html}\n"
            "    </tbody>\n"
            "  </table>\n"
            "  <!-- NOTE: Follow brand competitor_mention_policy. "
            "Never name competitors directly unless explicitly allowed. -->\n"
            "</section>"
        )

        body_copy = "; ".join(
            f"{item.get('feature', '')}: {us_label} = {item.get('us_value', '')}, "
            f"{them_label} = {item.get('them_value', '')}"
            for item in comparison_items
        )

        return LandingPageBlock(
            block_type=BlockType.comparison.value,
            position=5,
            headline="How We Compare",
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=[],
            html_structure_suggestion=html,
            data_requirements=["competitive_advantages", "feature_list"],
            archetype_notes=(
                "IMPORTANT: Follow competitor_mention_policy from brand "
                "constraints. Never name competitors directly unless the brand "
                "explicitly allows it. Use generic labels like 'Others', "
                "'Traditional providers', or 'Industry average' instead."
            ),
        )

    # ------------------------------------------------------------------
    # FAQ (standalone, separate from objection_handler)
    # ------------------------------------------------------------------

    def generate_faq_block(
        self,
        questions: List[Dict[str, str]],
        section_headline: Optional[str] = None,
    ) -> LandingPageBlock:
        """Standalone FAQ accordion block.

        *questions*: list of ``{question, answer}``.
        """
        section_headline = section_headline or "Frequently Asked Questions"

        supporting: List[Dict[str, Any]] = []
        for q in questions:
            supporting.append({
                "type": "faq_item",
                "question": q.get("question", ""),
                "answer": q.get("answer", ""),
            })

        items_html = "\n    ".join(
            (
                f'<details class="faq-item">\n'
                f'      <summary>{q.get("question", "")}</summary>\n'
                f'      <p>{q.get("answer", "")}</p>\n'
                f"    </details>"
            )
            for q in questions
        )

        html = (
            '<section class="faq">\n'
            f"  <h2>{section_headline}</h2>\n"
            f'  <div class="faq-list">\n'
            f"    {items_html}\n"
            "  </div>\n"
            "</section>"
        )

        faq_entities = []
        for q in questions:
            faq_entities.append({
                "@type": "Question",
                "name": q.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": q.get("answer", ""),
                },
            })

        schema_markup = json.dumps({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_entities,
        }, indent=2)

        body_copy = " ".join(
            f"Q: {q.get('question', '')} A: {q.get('answer', '')}"
            for q in questions
        )

        return LandingPageBlock(
            block_type=BlockType.faq.value,
            position=8,
            headline=section_headline,
            body_copy=body_copy,
            supporting_elements=supporting,
            visual_requirements=[],
            html_structure_suggestion=html,
            schema_markup=schema_markup,
            data_requirements=["faq_pairs"],
            archetype_notes=(
                "Target 5-8 questions. Include questions that map to "
                "long-tail search queries for SEO value."
            ),
        )

    # ------------------------------------------------------------------
    # Trust bar
    # ------------------------------------------------------------------

    def generate_trust_bar_block(
        self,
        trust_items: List[Dict[str, str]],
        section_headline: Optional[str] = None,
    ) -> LandingPageBlock:
        """Horizontal bar of trust signals (certifications, logos, stats).

        *trust_items*: list of ``{icon_concept, label, value}``.
        """
        section_headline = section_headline or ""

        supporting: List[Dict[str, Any]] = []
        for item in trust_items:
            supporting.append({
                "type": "trust_item",
                "icon_concept": item.get("icon_concept", ""),
                "label": item.get("label", ""),
                "value": item.get("value", ""),
            })

        items_html = "\n    ".join(
            (
                f'<div class="trust-item">\n'
                f'      <div class="trust-icon"><!-- {item.get("icon_concept", "")} --></div>\n'
                f'      <span class="trust-value">{item.get("value", "")}</span>\n'
                f'      <span class="trust-label">{item.get("label", "")}</span>\n'
                f"    </div>"
            )
            for item in trust_items
        )

        html = (
            '<section class="trust-bar">\n'
        )
        if section_headline:
            html += f"  <h2>{section_headline}</h2>\n"
        html += (
            f'  <div class="trust-items">\n'
            f"    {items_html}\n"
            "  </div>\n"
            "</section>"
        )

        visual_reqs = []
        for item in trust_items:
            if item.get("icon_concept"):
                visual_reqs.append(
                    f"Trust icon: {item['icon_concept']} for '{item.get('label', '')}'"
                )

        return LandingPageBlock(
            block_type=BlockType.trust_bar.value,
            position=2,
            headline=section_headline if section_headline else None,
            supporting_elements=supporting,
            visual_requirements=visual_reqs,
            html_structure_suggestion=html,
            data_requirements=["certifications", "awards", "stats"],
            archetype_notes=(
                "Local service: license number, insurance, BBB, years in business. "
                "Ecommerce: secure checkout, money-back guarantee, shipping partners. "
                "Professional services: certifications, client count, case studies."
            ),
        )


# ============================================================================
# VisualRequestWorkflow
# ============================================================================


class VisualRequestWorkflow:
    """Manage the lifecycle of visual asset requests from creation
    through delivery, approval, and deployment.

    Requests are persisted as YAML files in ``workspace/visual_requests/``
    within the provided *workspace_dir*.
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self._requests_dir = os.path.join(workspace_dir, "visual_requests")
        self._requests: Dict[str, VisualRequest] = {}

    def _ensure_dir(self) -> None:
        """Create the visual requests directory if it does not exist."""
        os.makedirs(self._requests_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_request(
        self,
        block_id: str,
        description: str,
        dimensions: str,
        format: str,
        priority: str = "medium",
        style_reference: Optional[str] = None,
        brand_guidelines: Optional[Dict[str, Any]] = None,
        deadline: Optional[str] = None,
    ) -> VisualRequest:
        """Create and persist a new visual request."""
        request = VisualRequest(
            block_id=block_id,
            description=description,
            dimensions=dimensions,
            format=format,
            priority=priority,
            style_reference=style_reference,
            brand_guidelines=brand_guidelines,
            deadline=deadline,
            status=VisualRequestStatus.requested.value,
        )
        self._requests[request.id] = request
        self._persist_request(request)
        return request

    def update_status(
        self, request_id: str, new_status: str, **kwargs: Any
    ) -> bool:
        """Update a request's status with lifecycle enforcement.

        When transitioning to ``delivered``, ``delivered_asset_url`` must
        be provided in *kwargs*.  When transitioning to ``approved``,
        ``approved_by`` must be provided.
        """
        request = self._requests.get(request_id)
        if request is None:
            return False

        # Validate required fields for certain transitions
        if new_status == VisualRequestStatus.delivered.value:
            asset_url = kwargs.get("delivered_asset_url")
            if not asset_url:
                return False
            request.delivered_asset_url = asset_url

        if new_status == VisualRequestStatus.approved.value:
            approved_by = kwargs.get("approved_by")
            if not approved_by:
                return False
            request.approved_by = approved_by

        request.status = new_status

        # Apply any additional kwargs as attributes
        if kwargs.get("notes"):
            request.notes = kwargs["notes"]

        self._persist_request(request)
        return True

    def get_pending_requests(
        self, business_id: Optional[str] = None
    ) -> List[VisualRequest]:
        """Return all requests that have not been delivered yet.

        Pending means status is ``requested`` or ``in_progress``.
        """
        pending_statuses = {
            VisualRequestStatus.requested.value,
            VisualRequestStatus.in_progress.value,
        }
        results = [
            r for r in self._requests.values()
            if r.status in pending_statuses
        ]
        return results

    def get_request_status(self, request_id: str) -> Optional[VisualRequest]:
        """Return a specific request by id, or ``None``."""
        return self._requests.get(request_id)

    def link_asset_to_block(
        self, request_id: str, block_id: str, asset_url: str
    ) -> bool:
        """Connect a delivered visual to its originating page block.

        Updates the request's ``delivered_asset_url`` and ``block_id``,
        and transitions to ``delivered`` if still pending.
        """
        request = self._requests.get(request_id)
        if request is None:
            return False

        request.block_id = block_id
        request.delivered_asset_url = asset_url

        if request.status in (
            VisualRequestStatus.requested.value,
            VisualRequestStatus.in_progress.value,
        ):
            request.status = VisualRequestStatus.delivered.value

        self._persist_request(request)
        return True

    def get_requests_for_page(
        self, block_ids: List[str]
    ) -> List[VisualRequest]:
        """Return all visual requests associated with the given block IDs."""
        block_id_set = set(block_ids)
        return [
            r for r in self._requests.values()
            if r.block_id in block_id_set
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_request(self, request: VisualRequest) -> None:
        """Save a request to ``workspace/visual_requests/`` as YAML."""
        self._ensure_dir()
        data = request.model_dump()
        filepath = os.path.join(self._requests_dir, f"{request.id}.yaml")

        if _yaml is not None:
            with open(filepath, "w", encoding="utf-8") as fh:
                _yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
        else:
            # Fallback: write as JSON if YAML is not available
            filepath = os.path.join(self._requests_dir, f"{request.id}.json")
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)


# ============================================================================
# PageAssembler
# ============================================================================


# Optimal block orderings by page type and archetype
_BLOCK_ORDERS: Dict[str, Dict[str, List[str]]] = {
    "landing_page": {
        "local_service": [
            BlockType.hero.value,
            BlockType.value_prop.value,
            BlockType.social_proof.value,
            BlockType.process.value,
            BlockType.objection_handler.value,
            BlockType.offer.value,
            BlockType.cta.value,
            BlockType.trust_bar.value,
        ],
        "ecommerce": [
            BlockType.hero.value,
            BlockType.social_proof.value,
            BlockType.value_prop.value,
            BlockType.comparison.value,
            BlockType.offer.value,
            BlockType.objection_handler.value,
            BlockType.cta.value,
        ],
        "professional_services": [
            BlockType.hero.value,
            BlockType.value_prop.value,
            BlockType.social_proof.value,
            BlockType.process.value,
            BlockType.social_proof.value,
            BlockType.offer.value,
            BlockType.cta.value,
        ],
    },
    "service_page": {
        "_default": [
            BlockType.hero.value,
            BlockType.value_prop.value,
            BlockType.process.value,
            BlockType.social_proof.value,
            BlockType.objection_handler.value,
            BlockType.cta.value,
        ],
    },
    "location_page": {
        "_default": [
            BlockType.hero.value,
            BlockType.trust_bar.value,
            BlockType.value_prop.value,
            BlockType.social_proof.value,
            BlockType.process.value,
            BlockType.cta.value,
        ],
    },
    "offer_page": {
        "_default": [
            BlockType.hero.value,
            BlockType.offer.value,
            BlockType.value_prop.value,
            BlockType.social_proof.value,
            BlockType.objection_handler.value,
            BlockType.cta.value,
        ],
    },
}


class PageAssembler:
    """Assemble individual blocks into a complete landing page structure.

    Generates all appropriate blocks in optimal order, compiles visual
    requests, builds page-level schema markup, and calculates word
    counts.
    """

    def __init__(self, block_generator: LandingPageBlockGenerator) -> None:
        self.gen = block_generator

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble_landing_page(
        self, page_config: Dict[str, Any]
    ) -> PageStructure:
        """Build a complete page from a configuration dict.

        Expected keys in *page_config*:

        - ``page_type`` (str): landing_page | service_page | location_page | offer_page
        - ``archetype`` (str): local_service | ecommerce | professional_services
        - ``title`` (str): page title / H1
        - ``meta_description`` (str): meta description for SEO
        - ``headline`` (str): hero headline
        - ``subheadline`` (str): hero subheadline
        - ``primary_cta`` (str): CTA button text
        - ``cta_url`` (str): CTA destination URL
        - ``trust_badges`` (List[str]): hero trust badges
        - ``background_image_concept`` (str): hero background image concept
        - ``value_props`` (List[Dict]): {icon_concept, title, description}
        - ``testimonials`` (List[Dict]): {quote, customer_name, rating, service_type}
        - ``review_aggregate`` (Dict): {count, avg_rating, platform}
        - ``process_steps`` (List[Dict]): {step_number, title, description}
        - ``objections`` (List[Dict]): {question, answer} or {myth, truth}
        - ``objection_format`` (str): faq | myths
        - ``offer_headline`` (str)
        - ``offer_details`` (str)
        - ``price_display`` (str)
        - ``urgency_element`` (str)
        - ``guarantee`` (str)
        - ``cta_headline`` (str): final CTA section headline
        - ``reassurance_text`` (str)
        - ``secondary_cta`` (Dict): {text, url}
        - ``comparison_items`` (List[Dict]): {feature, us_value, them_value}
        - ``trust_items`` (List[Dict]): {icon_concept, label, value}
        - ``faq_questions`` (List[Dict]): {question, answer}
        """
        page_type = page_config.get("page_type", "landing_page")
        archetype = page_config.get("archetype", "local_service")
        title = page_config.get("title", "")
        meta_desc = page_config.get("meta_description", "")

        block_order = self.get_optimal_block_order(page_type, archetype)
        blocks: List[LandingPageBlock] = []
        all_visual_requests: List[VisualRequest] = []
        seen_block_types: set = set()

        for position, block_type in enumerate(block_order, start=1):
            # Skip duplicates unless this is social_proof (can appear twice)
            if block_type in seen_block_types and block_type != BlockType.social_proof.value:
                continue
            seen_block_types.add(block_type)

            block = self._build_block(block_type, page_config, position)
            if block is not None:
                block.position = position
                blocks.append(block)

                # Create visual requests from visual_requirements
                for vr_desc in block.visual_requirements:
                    vr = VisualRequest(
                        block_id=block.id,
                        description=vr_desc,
                        dimensions="1920x1080",
                        format="photo",
                        priority="medium",
                    )
                    all_visual_requests.append(vr)

        word_count = self._calculate_word_count(blocks)

        page = PageStructure(
            page_type=page_type,
            title=title,
            meta_description=meta_desc,
            blocks=blocks,
            visual_requests=all_visual_requests,
            estimated_word_count=word_count,
            archetype=archetype,
        )

        page.schema_markup = self._generate_page_schema(page)
        return page

    def get_optimal_block_order(
        self, page_type: str, archetype: str
    ) -> List[str]:
        """Return the optimal block type ordering for the given page
        type and archetype combination.

        Falls back to ``_default`` archetype, then to a generic
        landing_page / local_service order.
        """
        page_orders = _BLOCK_ORDERS.get(page_type, {})

        order = page_orders.get(archetype)
        if order is not None:
            return list(order)

        default_order = page_orders.get("_default")
        if default_order is not None:
            return list(default_order)

        # Ultimate fallback: local service landing page
        return list(_BLOCK_ORDERS["landing_page"]["local_service"])

    # ------------------------------------------------------------------
    # Schema generation
    # ------------------------------------------------------------------

    def _generate_page_schema(self, page: PageStructure) -> str:
        """Combine block-level schemas into a single page-level JSON-LD."""
        schema: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@graph": [],
        }

        # Page-level WebPage schema
        webpage: Dict[str, Any] = {
            "@type": "WebPage",
            "name": page.title,
            "description": page.meta_description,
            "breadcrumb": {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": "/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": page.title,
                    },
                ],
            },
        }
        schema["@graph"].append(webpage)

        # Merge block-level schemas into the graph
        for block in page.blocks:
            if block.schema_markup:
                try:
                    block_schema = json.loads(block.schema_markup)
                    # Strip @context from block schemas (page-level provides it)
                    block_schema.pop("@context", None)
                    schema["@graph"].append(block_schema)
                except (json.JSONDecodeError, TypeError):
                    pass

        return json.dumps(schema, indent=2)

    # ------------------------------------------------------------------
    # Word count
    # ------------------------------------------------------------------

    def _calculate_word_count(self, blocks: List[LandingPageBlock]) -> int:
        """Sum word counts across all text fields of all blocks."""
        total = 0

        for block in blocks:
            if block.headline:
                total += len(block.headline.split())
            if block.subheadline:
                total += len(block.subheadline.split())
            if block.body_copy:
                total += len(block.body_copy.split())
            if block.cta_text:
                total += len(block.cta_text.split())

            for elem in block.supporting_elements:
                for key, value in elem.items():
                    if isinstance(value, str) and key != "type":
                        total += len(value.split())
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                total += len(item.split())
                            elif isinstance(item, dict):
                                for v in item.values():
                                    if isinstance(v, str):
                                        total += len(v.split())

        return total

    # ------------------------------------------------------------------
    # Block builder dispatch
    # ------------------------------------------------------------------

    def _build_block(
        self,
        block_type: str,
        config: Dict[str, Any],
        position: int,
    ) -> Optional[LandingPageBlock]:
        """Dispatch to the correct block generator method."""

        if block_type == BlockType.hero.value:
            headline = config.get("headline", config.get("title", ""))
            subheadline = config.get("subheadline", "")
            cta_text = config.get("primary_cta", "Get Started")
            cta_url = config.get("cta_url", "#")
            if not headline:
                return None
            return self.gen.generate_hero_block(
                headline=headline,
                subheadline=subheadline,
                primary_cta=cta_text,
                cta_url=cta_url,
                trust_badges=config.get("trust_badges"),
                background_image_concept=config.get("background_image_concept"),
            )

        if block_type == BlockType.value_prop.value:
            value_props = config.get("value_props", [])
            if not value_props:
                return None
            return self.gen.generate_value_prop_block(
                value_props=value_props,
                section_headline=config.get("value_prop_headline"),
            )

        if block_type == BlockType.social_proof.value:
            testimonials = config.get("testimonials", [])
            if not testimonials:
                return None
            return self.gen.generate_social_proof_block(
                testimonials=testimonials,
                review_aggregate=config.get("review_aggregate"),
            )

        if block_type == BlockType.process.value:
            steps = config.get("process_steps", [])
            if not steps:
                return None
            return self.gen.generate_process_block(
                steps=steps,
                section_headline=config.get("process_headline"),
            )

        if block_type == BlockType.objection_handler.value:
            objections = config.get("objections", [])
            if not objections:
                return None
            return self.gen.generate_objection_handler_block(
                objections=objections,
                format_type=config.get("objection_format", "faq"),
            )

        if block_type == BlockType.offer.value:
            offer_headline = config.get("offer_headline", "")
            offer_details = config.get("offer_details", "")
            if not offer_headline:
                return None
            return self.gen.generate_offer_block(
                offer_headline=offer_headline,
                offer_details=offer_details,
                price_display=config.get("price_display"),
                urgency_element=config.get("urgency_element"),
                guarantee=config.get("guarantee"),
            )

        if block_type == BlockType.cta.value:
            cta_headline = config.get("cta_headline", config.get("headline", ""))
            cta_text = config.get("primary_cta", "Get Started")
            cta_url = config.get("cta_url", "#")
            if not cta_headline:
                return None
            return self.gen.generate_cta_block(
                headline=cta_headline,
                cta_text=cta_text,
                cta_url=cta_url,
                reassurance_text=config.get("reassurance_text"),
                secondary_cta=config.get("secondary_cta"),
            )

        if block_type == BlockType.comparison.value:
            items = config.get("comparison_items", [])
            if not items:
                return None
            return self.gen.generate_comparison_block(
                comparison_items=items,
                us_label=config.get("us_label", "Us"),
                them_label=config.get("them_label", "Others"),
            )

        if block_type == BlockType.faq.value:
            questions = config.get("faq_questions", [])
            if not questions:
                return None
            return self.gen.generate_faq_block(
                questions=questions,
                section_headline=config.get("faq_headline"),
            )

        if block_type == BlockType.trust_bar.value:
            items = config.get("trust_items", [])
            if not items:
                return None
            return self.gen.generate_trust_bar_block(
                trust_items=items,
                section_headline=config.get("trust_bar_headline"),
            )

        return None

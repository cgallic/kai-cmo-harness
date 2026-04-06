"""Copy generation engine for the Kai Marketing OS.

Given a CreativeBrief, this module produces structured content templates,
prompts, and output schemas for every marketing format -- web sections,
landing pages, ad copy, social posts, emails, and scripts.

Design principles
-----------------
1. **Recipe generator, not LLM caller.**  Functions produce structured
   dicts that specify what content is needed, including section order,
   character limits, and framework instructions.  An LLM fills them.
2. **Framework-aware.**  Each generator embeds the correct framework
   rules (algorithmic authorship for SEO, perception engineering for
   landing pages, CAN-SPAM for cold outreach).
3. **Quality-gate integrated.**  ``check_quality`` returns a check *plan*
   (script paths + thresholds) without executing anything.
4. **Pure functions.**  No file I/O, no network calls, no script execution.

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
# Data Models
# ============================================================================


class CopyOutput(BaseModel):
    """Structured output from a copy generation run."""

    id: str = Field(default_factory=lambda: f"cpy_{uuid.uuid4().hex[:12]}")
    brief_id: str = ""
    format: str = ""
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    full_text: str = ""
    word_count: int = 0
    quality_scores: Dict[str, Any] = Field(default_factory=dict)
    quality_status: str = "pending"
    revision_notes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


# ============================================================================
# Helpers
# ============================================================================


def _apply_algorithmic_authorship(text: str) -> str:
    """Return *text* unchanged -- the actual rewrite is done by the LLM.

    This function exists as a documented reference point.  The rules
    below are injected as instructions for the LLM to follow during
    content generation.

    Algorithmic Authorship -- Top 10 Rules
    ----------------------------------------
    1. Conditions AFTER main clause: "Do X if Y" not "If Y, do X".
    2. Instructions start with verbs: "Whip lightly" not "Lightly whip".
    3. Short sentences -- break complex sentences apart (under 20 words).
    4. Numeric lists for steps/methods, bulleted lists for types/categories.
    5. Name entities twice before switching to attributes or pronouns.
    6. Anchor words connect sequential sentences (repeat a key term).
    7. Examples follow every declaration or claim.
    8. Bold the ANSWER, not query-matching terms.
    9. No links in the first sentence of paragraphs.
    10. Same part of speech across all list items.

    Full framework: knowledge/frameworks/content-copywriting/algorithmic-authorship.md
    """
    return text


def _apply_perception_engineering(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Return perception-engineering layer instructions for the brief.

    These instructions tell the LLM which persuasion levers to pull.
    They are NOT executed here -- the LLM uses them as creative direction.

    Perception Engineering -- 3 Layers
    ------------------------------------
    Layer 1 (Perception): Destabilize cached beliefs.
        Re-index "virtues" as "vices".  Example: "Your thoroughness is
        costing you customers" for a business that prides itself on
        being detail-oriented but is slow to respond to leads.

    Layer 2 (Context): Shift what feels allowed.
        Genre-shift the reader's frame.  Move from "Exam" (judgment,
        fear of mistakes) to "Lab" (experimentation, curiosity).

    Layer 3 (Permission): Remove consequences.
        Future-pace the outcome.  Use double-binds and risk-reversal
        ("free consultation", "money-back guarantee") so the reader
        feels they can act without downside.

    Full framework: knowledge/frameworks/content-copywriting/perception-engineering.md
    """
    key_message = brief.get("key_message", "")
    persona_pain = brief.get("persona_pain_point", "")
    offer = brief.get("offer", "")
    cta = brief.get("cta", "")
    proof = brief.get("proof_available", "")

    return {
        "layer_1_perception": {
            "goal": "Destabilize the reader's cached belief about their current approach",
            "instruction": (
                f"Reframe the reader's status quo as the actual problem. "
                f"Their pain point is: '{persona_pain}'. "
                f"Show them that what they consider a virtue (e.g., being careful, "
                f"doing it themselves) is actually the cause of their problem."
            ),
            "key_message": key_message,
        },
        "layer_2_context": {
            "goal": "Shift the reader from evaluation mode to exploration mode",
            "instruction": (
                "Move the reader from 'Am I making the right choice?' (Exam frame) "
                "to 'What would this look like for my business?' (Lab frame). "
                "Use specific examples, case studies, and scenarios rather than "
                "abstract claims."
            ),
            "proof_to_use": proof or "Use social proof, specific numbers, or named examples",
        },
        "layer_3_permission": {
            "goal": "Remove all perceived risk from taking action",
            "instruction": (
                f"Make the CTA ('{cta}') feel like it has zero downside. "
                f"Use the offer ('{offer}') as risk-reversal. "
                "Future-pace: describe what life looks like after they take action. "
                "Double-bind: frame inaction as the risky choice."
            ),
            "cta": cta,
            "offer": offer,
        },
    }


def _sections_to_full_text(sections: List[Dict[str, Any]]) -> str:
    """Concatenate section contents into a single text string."""
    parts: List[str] = []
    for section in sections:
        content = section.get("content", "")
        if content:
            parts.append(content)
        # For sections with sub-items, try common nested structures.
        for key in ("headline", "subheadline", "heading", "body", "intro"):
            val = section.get(key, "")
            if val and val not in parts:
                parts.append(val)
    return "\n\n".join(parts)


def _count_words(text: str) -> int:
    """Count words in *text*."""
    return len(text.split()) if text else 0


# ============================================================================
# Web Section Generators
# ============================================================================


def generate_hero_section(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a hero section specification.

    The hero is the first thing visitors see.  It must convey the
    primary benefit in under 10 words, expand via a subheadline, and
    include a trust indicator and friction-free CTA.
    """
    cta = brief.get("cta", "Get Started")
    cta_url = brief.get("cta_url", "#")
    key_message = brief.get("key_message", "")
    proof = brief.get("proof_available", "")

    return {
        "section_type": "hero",
        "headline": f"[Max 10 words, action-oriented] {key_message[:80]}",
        "subheadline": (
            f"[Max 20 words, expand headline with specificity] "
            f"Supporting: {key_message[:120]}"
        ),
        "cta_text": cta,
        "cta_url": cta_url or "#",
        "supporting_text": (
            "Brief supporting sentence that addresses the primary objection "
            "or adds a specific detail (e.g., 'Serving [City] since [Year]')."
        ),
        "trust_indicator": proof or "Years in business, review count, or certification",
        "instructions": {
            "perception_engineering": (
                "Apply Layer 3 (Permission): CTA must feel zero-risk. "
                "Use language like 'free', 'no obligation', 'see how' to "
                "remove friction."
            ),
            "max_headline_words": 10,
            "max_subheadline_words": 20,
        },
    }


def generate_value_prop_section(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a value propositions section specification.

    3-4 props, each with a short title (3-5 words) and 1-2 sentence
    description.  Props must be specific to the business, not generic.
    """
    key_message = brief.get("key_message", "")
    supporting = brief.get("supporting_messages") or []

    props_template = []
    for i in range(min(4, max(3, len(supporting) + 1))):
        msg = supporting[i] if i < len(supporting) else f"Value proposition {i + 1}"
        props_template.append({
            "icon_suggestion": "[Relevant icon name, e.g., 'clock', 'shield', 'star']",
            "title": f"[3-5 word title for prop {i + 1}]",
            "description": (
                f"[1-2 sentences, specific to the business] Based on: {msg}"
            ),
        })

    return {
        "section_type": "value_props",
        "heading": f"Why Choose Us — {key_message[:60]}",
        "props": props_template,
        "layout": "3-column" if len(props_template) == 3 else "4-column",
        "instructions": {
            "specificity": (
                "Each prop MUST include a specific number, timeframe, or named "
                "benefit. 'Fast service' is rejected; '2-hour response time' passes."
            ),
        },
    }


def generate_testimonial_block(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a testimonials section specification.

    Uses trust signals from the business profile.  If no testimonials
    are available, outputs a placeholder with collection instructions.
    """
    proof = brief.get("proof_available", "")
    has_testimonials = bool(proof and "testimonial" in proof.lower())

    if has_testimonials:
        testimonials = [
            {
                "quote": "[Actual customer quote from proof_available]",
                "name": "[Customer Name]",
                "title": "[Customer Title or City]",
                "rating": 5,
                "photo_placeholder": "[customer-photo.jpg or initials avatar]",
            },
            {
                "quote": "[Second customer quote]",
                "name": "[Customer Name]",
                "title": "[Customer Title or City]",
                "rating": 5,
                "photo_placeholder": "[customer-photo.jpg or initials avatar]",
            },
            {
                "quote": "[Third customer quote]",
                "name": "[Customer Name]",
                "title": "[Customer Title or City]",
                "rating": 5,
                "photo_placeholder": "[customer-photo.jpg or initials avatar]",
            },
        ]
    else:
        testimonials = [
            {
                "quote": "[PLACEHOLDER: Collect testimonials by sending review requests. "
                         "Use kai/creative/brief.py format 'email_review_request' to generate.]",
                "name": "[Pending]",
                "title": "",
                "rating": 5,
                "photo_placeholder": "",
            },
        ]

    return {
        "section_type": "testimonials",
        "heading": "What Our Customers Say",
        "testimonials": testimonials,
        "layout": "cards" if len(testimonials) <= 3 else "carousel",
        "instructions": {
            "collection_note": (
                "If no real testimonials are available, prioritize collecting them. "
                "Generate a review request email brief as the first action."
            ),
        },
    }


def generate_cta_block(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a call-to-action block specification.

    Includes urgency and trust elements for maximum conversion.
    """
    cta = brief.get("cta", "Get Started")
    cta_url = brief.get("cta_url", "#")
    offer = brief.get("offer", "")
    offer_details = brief.get("offer_details", "")
    proof = brief.get("proof_available", "")

    urgency = ""
    if offer_details:
        urgency = f"[Time-limited element based on offer: {offer_details}]"
    else:
        urgency = "[Create urgency: limited availability, seasonal pricing, or consequence of waiting]"

    trust = ""
    if proof:
        trust = f"[Trust element from proof: {proof}]"
    else:
        trust = "[Guarantee, review count, or certification badge]"

    return {
        "section_type": "cta_block",
        "heading": f"[Action-oriented heading reinforcing offer: {offer or cta}]",
        "body": (
            "[2-3 sentences that future-pace the outcome. "
            "Describe what life looks like after taking action.]"
        ),
        "cta_text": cta,
        "cta_url": cta_url or "#",
        "urgency_element": urgency,
        "trust_element": trust,
        "instructions": {
            "perception_engineering": (
                "Apply Layer 3 (Permission): remove all perceived consequences. "
                "Double-bind: frame inaction as the risky choice. "
                "Future-pace: paint the after-state vividly."
            ),
        },
    }


def generate_faq_section(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an FAQ section specification.

    5-8 FAQs derived from persona objections and common questions.
    Answers follow algorithmic authorship rules.
    """
    persona_pain = brief.get("persona_pain_point", "")
    key_message = brief.get("key_message", "")
    target_keyword = brief.get("target_keyword", "")

    faqs = [
        {
            "question": f"[FAQ about primary service related to: {key_message[:60]}]",
            "answer": "[Answer following algorithmic authorship: conditions after main clause, start with verb, under 20 words per sentence]",
        },
        {
            "question": f"[FAQ addressing persona pain point: {persona_pain[:60]}]",
            "answer": "[Answer with specific numbers, examples, or named tools]",
        },
        {
            "question": "[FAQ about pricing or process]",
            "answer": "[Transparent answer with specific ranges or steps]",
        },
        {
            "question": "[FAQ about timeline or availability]",
            "answer": "[Specific timeframes, not vague promises]",
        },
        {
            "question": "[FAQ about guarantees or risk-reversal]",
            "answer": "[Clear guarantee language that removes risk]",
        },
    ]

    # Add keyword-targeted FAQs for SEO content.
    if target_keyword:
        faqs.extend([
            {
                "question": f"[FAQ containing '{target_keyword}' naturally]",
                "answer": f"[Answer targeting '{target_keyword}' with specific information]",
            },
            {
                "question": f"[Comparison/alternative FAQ related to '{target_keyword}']",
                "answer": "[Answer positioning the business as the clear choice]",
            },
            {
                "question": f"[How-to FAQ related to '{target_keyword}']",
                "answer": "[Step-by-step answer using numeric list]",
            },
        ])

    schema_markup = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                },
            }
            for faq in faqs
        ],
    }

    return {
        "section_type": "faq",
        "heading": "Frequently Asked Questions",
        "faqs": faqs,
        "schema_markup": schema_markup,
        "instructions": {
            "algorithmic_authorship": (
                "Every answer must follow algorithmic authorship rules: "
                "conditions after main clause, instructions start with verbs, "
                "sentences under 20 words, bold the answer not the query terms."
            ),
        },
    }


def generate_service_description(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a service description section specification.

    Includes intro, feature list, process steps, and a CTA.
    """
    key_message = brief.get("key_message", "")
    cta = brief.get("cta", "Get Started")
    supporting = brief.get("supporting_messages") or []

    features = []
    for i, msg in enumerate(supporting[:5]):
        features.append({
            "name": f"[Feature {i + 1} title]",
            "description": f"[1-2 sentences based on: {msg}]",
        })
    if len(features) < 3:
        for i in range(len(features), 3):
            features.append({
                "name": f"[Feature {i + 1} title]",
                "description": "[Specific feature description with measurable benefit]",
            })

    return {
        "section_type": "service_description",
        "heading": f"[Service name based on: {key_message[:60]}]",
        "intro": (
            "[2-3 sentences introducing the service. Lead with the outcome "
            "the customer gets, not a description of what you do.]"
        ),
        "features": features,
        "process_steps": [
            {"step": 1, "title": "[First step]", "description": "[What happens and what the customer needs to do]"},
            {"step": 2, "title": "[Second step]", "description": "[What happens next]"},
            {"step": 3, "title": "[Third step]", "description": "[Final step and outcome]"},
        ],
        "cta": cta,
        "instructions": {
            "algorithmic_authorship": (
                "Process steps use numeric list (rule 4). "
                "Features use bulleted list. "
                "Name the service at least twice before using pronouns (rule 5)."
            ),
        },
    }


# ============================================================================
# Landing Page Generator
# ============================================================================


def generate_landing_page(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble a full landing page by composing section generators.

    Section order follows proven conversion patterns:
    hero -> social proof bar -> problem statement -> value props ->
    how it works -> testimonials -> offer section -> FAQ -> final CTA.
    """
    pe_layers = _apply_perception_engineering(brief)

    key_message = brief.get("key_message", "")
    offer = brief.get("offer", "")
    offer_details = brief.get("offer_details", "")
    persona_pain = brief.get("persona_pain_point", "")
    proof = brief.get("proof_available", "")
    target_keyword = brief.get("target_keyword", "")

    sections: List[Dict[str, Any]] = []

    # 1. Hero
    sections.append(generate_hero_section(brief))

    # 2. Social proof bar
    sections.append({
        "section_type": "social_proof_bar",
        "content": (
            "[Single-line trust bar: '500+ Happy Customers | 15 Years Experience | "
            "4.9 Google Rating | Licensed & Insured']"
        ),
        "elements": [
            {"type": "stat", "value": "[Number]", "label": "[Happy Customers / Projects Completed]"},
            {"type": "stat", "value": "[Number]", "label": "[Years in Business]"},
            {"type": "rating", "value": "[4.8+]", "label": "[Google / Yelp Rating]"},
            {"type": "badge", "value": "", "label": "[Licensed & Insured / BBB Accredited]"},
        ],
        "instructions": {
            "source": f"Pull real numbers from proof: {proof}" if proof else "Request real numbers from operator",
        },
    })

    # 3. Problem statement (Perception Engineering Layer 1)
    sections.append({
        "section_type": "problem_statement",
        "heading": "[Problem heading that reframes the status quo as the problem]",
        "body": (
            f"[3-4 sentences applying Perception Engineering Layer 1. "
            f"Destabilize the reader's cached belief. Pain point: '{persona_pain}'. "
            f"Re-index their 'virtue' as a 'vice'.]"
        ),
        "perception_engineering": pe_layers["layer_1_perception"],
        "instructions": {
            "tone": "Empathetic but direct. Acknowledge their situation, then reveal the hidden cost.",
        },
    })

    # 4. Value props
    sections.append(generate_value_prop_section(brief))

    # 5. How it works (3-step process)
    sections.append({
        "section_type": "how_it_works",
        "heading": "How It Works",
        "steps": [
            {"step": 1, "title": "[Step 1 title]", "description": "[What the customer does]", "icon": "[icon]"},
            {"step": 2, "title": "[Step 2 title]", "description": "[What happens next]", "icon": "[icon]"},
            {"step": 3, "title": "[Step 3 title]", "description": "[Outcome they receive]", "icon": "[icon]"},
        ],
        "perception_engineering": pe_layers["layer_2_context"],
        "instructions": {
            "context_shift": (
                "Apply Layer 2 (Context): shift from Exam frame to Lab frame. "
                "Make each step feel easy, concrete, and low-risk. "
                "Use specific details, not abstract promises."
            ),
        },
    })

    # 6. Testimonials
    sections.append(generate_testimonial_block(brief))

    # 7. Offer section (if applicable)
    if offer or offer_details:
        sections.append({
            "section_type": "offer",
            "heading": f"[Offer heading: {offer or 'Special Offer'}]",
            "offer_name": offer or "",
            "offer_details": offer_details or "",
            "urgency": "[Time-limited or scarcity element]",
            "fine_print": "[Terms, conditions, expiration]",
            "cta_text": brief.get("cta", "Get Started"),
            "cta_url": brief.get("cta_url", "#"),
        })

    # 8. FAQ
    sections.append(generate_faq_section(brief))

    # 9. Final CTA block
    sections.append(generate_cta_block(brief))

    # Meta information for the page.
    meta_title = f"[Page title containing '{target_keyword}' | Brand Name]" if target_keyword else "[Page Title | Brand Name]"
    meta_description = (
        f"[155 chars max. Include '{target_keyword}' and primary benefit. "
        f"End with CTA.]"
    ) if target_keyword else "[155 chars max. Primary benefit + CTA.]"

    return {
        "format": "landing_page",
        "sections": sections,
        "meta": {
            "title": meta_title,
            "description": meta_description,
        },
        "schema_markup": {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta_title,
            "description": meta_description,
        },
        "perception_engineering_layers": pe_layers,
        "instructions": {
            "overall": (
                "Apply perception engineering throughout: "
                "Layer 1 in problem statement, Layer 2 in how-it-works, "
                "Layer 3 in hero and final CTA. "
                "Algorithmic authorship rules apply to all text."
            ),
        },
    }


# ============================================================================
# Ad Copy Generators
# ============================================================================


def generate_google_ads_copy(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Google Ads copy specification.

    15 headlines (max 30 chars each), 4 descriptions (max 90 chars each),
    sitelinks, and callouts.
    """
    keyword = brief.get("target_keyword", "[primary keyword]")
    cta = brief.get("cta", "Get Started")
    offer = brief.get("offer", "")
    key_message = brief.get("key_message", "")
    proof = brief.get("proof_available", "")

    headlines = [
        f"[H1: PIN. Include '{keyword}', max 30 chars]",
        f"[H2: PIN. CTA: '{cta}', max 30 chars]",
        f"[H3: Primary benefit, max 30 chars]",
        f"[H4: Social proof element, max 30 chars]",
        f"[H5: Urgency/offer, max 30 chars]",
        f"[H6: Location + service, max 30 chars]",
        f"[H7: Trust signal (years/reviews), max 30 chars]",
        f"[H8: Question hook, max 30 chars]",
        f"[H9: Benefit-driven variant, max 30 chars]",
        f"[H10: Competitive advantage, max 30 chars]",
        f"[H11: Price/value proposition, max 30 chars]",
        f"[H12: Process simplicity, max 30 chars]",
        f"[H13: Guarantee/risk-reversal, max 30 chars]",
        f"[H14: Brand name + keyword, max 30 chars]",
        f"[H15: Seasonal/timely hook, max 30 chars]",
    ]

    descriptions = [
        f"[D1: Primary value prop + CTA. Based on: {key_message[:50]}. Max 90 chars]",
        f"[D2: Social proof + urgency. Proof: {proof[:40]}. Max 90 chars]",
        f"[D3: Service details + differentiator. Max 90 chars]",
        f"[D4: Offer details + trust signal. Offer: {offer[:30]}. Max 90 chars]",
    ]

    sitelinks = [
        {"title": "[Sitelink 1: Key service page]", "description": "[2 lines, 25 chars each]", "url": "[/service-1]"},
        {"title": "[Sitelink 2: About/trust page]", "description": "[2 lines, 25 chars each]", "url": "[/about]"},
        {"title": "[Sitelink 3: Reviews/testimonials]", "description": "[2 lines, 25 chars each]", "url": "[/reviews]"},
        {"title": "[Sitelink 4: Contact/quote]", "description": "[2 lines, 25 chars each]", "url": "[/contact]"},
    ]

    callouts = [
        "[Callout 1: e.g., 'Free Estimates']",
        "[Callout 2: e.g., 'Licensed & Insured']",
        "[Callout 3: e.g., 'Same-Day Service']",
        "[Callout 4: e.g., '5-Star Rated']",
    ]

    return {
        "format": "google_ads",
        "headlines": headlines,
        "descriptions": descriptions,
        "sitelinks": sitelinks,
        "callouts": callouts,
        "compliance_note": (
            "Check all copy against harness/references/google-ads-policy-reference.md. "
            "Key restrictions: no superlatives without proof, healthcare certs required, "
            "financial disclosures needed."
        ),
        "instructions": {
            "headline_rules": "H1 pinned: must contain primary keyword. H2 pinned: must contain CTA.",
            "max_headline_chars": 30,
            "max_description_chars": 90,
            "total_headlines": 15,
            "total_descriptions": 4,
        },
    }


def generate_meta_ads_copy(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Meta (Facebook/Instagram) ads copy specification.

    3 variants with different angles: benefit, social proof, urgency.
    Primary text max 125 chars for above-fold visibility.
    """
    cta = brief.get("cta", "Learn More")
    key_message = brief.get("key_message", "")
    proof = brief.get("proof_available", "")
    offer = brief.get("offer", "")
    persona_pain = brief.get("persona_pain_point", "")

    # Determine if Special Ad Category applies.
    compliance = brief.get("compliance_notes") or []
    special_category_note = ""
    for note in compliance:
        if isinstance(note, str):
            lower = note.lower()
            if any(kw in lower for kw in ("housing", "employment", "credit", "lending")):
                special_category_note = (
                    "SPECIAL AD CATEGORY REQUIRED. This ad falls under Meta's Special Ad "
                    "Categories. Targeting restrictions apply: no age, gender, zip code, "
                    "or interest-based targeting."
                )
                break

    variants = [
        {
            "angle": "benefit",
            "primary_text": f"[Max 125 chars. Lead with primary benefit: {key_message[:60]}]",
            "headline": f"[Max 40 chars. Benefit-driven headline]",
            "description": f"[Max 30 chars. Supporting detail]",
            "cta_button": cta,
        },
        {
            "angle": "social_proof",
            "primary_text": f"[Max 125 chars. Social proof lead: {proof[:60]}]",
            "headline": f"[Max 40 chars. Trust-driven headline]",
            "description": f"[Max 30 chars. Credibility detail]",
            "cta_button": cta,
        },
        {
            "angle": "urgency",
            "primary_text": f"[Max 125 chars. Urgency/offer lead: {offer or persona_pain[:40]}]",
            "headline": f"[Max 40 chars. Action-driven headline]",
            "description": f"[Max 30 chars. Scarcity/time element]",
            "cta_button": cta,
        },
    ]

    result: Dict[str, Any] = {
        "format": "meta_ads",
        "variants": variants,
        "compliance_note": (
            "Check all copy against harness/references/meta-ads-rules.md. "
            "Key restrictions: no before/after images, no personal attributes "
            "('You are...'), Special Ad Categories for housing/employment/credit."
        ),
        "instructions": {
            "primary_text_max_chars": 125,
            "headline_max_chars": 40,
            "description_max_chars": 30,
            "above_fold": "Primary text must deliver the message in 125 chars. Longer text is hidden behind 'See more'.",
        },
    }

    if special_category_note:
        result["special_ad_category_notice"] = special_category_note

    return result


def generate_social_ad_copy(
    brief: Dict[str, Any],
    platform: str,
) -> Dict[str, Any]:
    """Generate platform-aware ad copy for LinkedIn, TikTok, Pinterest, etc.

    Respects PLATFORM_CONSTRAINTS from brief.py for character limits.
    """
    from kai.creative.brief import PLATFORM_CONSTRAINTS

    cta = brief.get("cta", "Learn More")
    key_message = brief.get("key_message", "")
    proof = brief.get("proof_available", "")

    platform_key = f"{platform}_ads"
    constraints = PLATFORM_CONSTRAINTS.get(platform_key, {})

    if platform.lower() == "linkedin":
        return {
            "format": "social_ad",
            "platform": "linkedin",
            "intro_text": f"[Max {constraints.get('intro_text_max_chars', 600)} chars. Professional tone. Lead with insight: {key_message[:60]}]",
            "headline": f"[Max {constraints.get('headline_max_chars', 200)} chars. Thought-leadership angle]",
            "cta": cta,
            "compliance_note": "Check against harness/references/linkedin-ads-rules.md",
            "constraints": constraints,
        }

    if platform.lower() == "tiktok":
        return {
            "format": "social_ad",
            "platform": "tiktok",
            "caption": f"[Max {constraints.get('caption_max_chars', 100)} chars. Hook first. Trending language.]",
            "hook": "[First 3 seconds: attention-grabbing visual + text overlay]",
            "cta": cta,
            "video_max_seconds": constraints.get("video_max_seconds", 60),
            "compliance_note": (
                "Check against harness/references/tiktok-ads-policy-reference.md. "
                "AI content disclosure required. No political ads."
            ),
            "constraints": constraints,
        }

    if platform.lower() == "pinterest":
        return {
            "format": "social_ad",
            "platform": "pinterest",
            "title": f"[Pin title, max 100 chars: {key_message[:50]}]",
            "description": f"[Pin description, max 500 chars. Aspirational, search-friendly.]",
            "cta": cta,
            "compliance_note": (
                "Check against harness/references/pinterest-ads-rules.md. "
                "All weight loss ads banned (narrow GLP-1 exception). "
                "Strict body image rules."
            ),
            "constraints": constraints,
        }

    if platform.lower() == "snapchat":
        return {
            "format": "social_ad",
            "platform": "snapchat",
            "headline": f"[Max 34 chars. Mobile-first, punchy.]",
            "brand_name": "[Brand name, max 25 chars]",
            "cta": cta,
            "compliance_note": (
                "Check against harness/references/snapchat-ads-policy-reference.md. "
                "Young audience protections. EU political ad ban."
            ),
            "constraints": constraints,
        }

    if platform.lower() in ("x", "twitter"):
        return {
            "format": "social_ad",
            "platform": "x",
            "tweet_text": f"[Max 280 chars. Concise, punchy. Key message: {key_message[:40]}]",
            "card_title": "[Max 70 chars]",
            "card_description": "[Max 200 chars]",
            "cta": cta,
            "compliance_note": "Check against harness/references/x-ads-policy-reference.md",
            "constraints": constraints,
        }

    if platform.lower() == "amazon":
        return {
            "format": "social_ad",
            "platform": "amazon",
            "headline": f"[Product-focused headline: {key_message[:50]}]",
            "custom_text": "[Max 50 chars. Key differentiator.]",
            "cta": cta,
            "compliance_note": (
                "Check against harness/references/amazon-ads-policy-reference.md. "
                "18-month claim evidence rule. No competitor disparagement."
            ),
            "constraints": constraints,
        }

    if platform.lower() == "microsoft":
        return {
            "format": "social_ad",
            "platform": "microsoft",
            "headlines": [f"[H{i}: Max 30 chars]" for i in range(1, 16)],
            "descriptions": [f"[D{i}: Max 90 chars]" for i in range(1, 5)],
            "cta": cta,
            "compliance_note": "Check against harness/references/microsoft-ads-rules.md",
            "constraints": constraints,
        }

    # Generic fallback.
    return {
        "format": "social_ad",
        "platform": platform,
        "primary_text": f"[Primary ad text: {key_message[:80]}]",
        "headline": "[Ad headline]",
        "cta": cta,
        "constraints": constraints,
    }


# ============================================================================
# Social Post Generators
# ============================================================================


def generate_social_post(
    brief: Dict[str, Any],
    platform: str,
) -> Dict[str, Any]:
    """Generate a social media post specification for the given platform.

    Platform-specific formatting rules:
    - Instagram: emoji-friendly, hashtag-heavy (up to 30), visual-first
    - LinkedIn: professional, thought leadership, 3-5 hashtags
    - Facebook: conversational, community-oriented, question hooks
    - TikTok: hook in first line, trending language, minimal hashtags
    - X/Twitter: concise, punchy, max 280 chars
    """
    key_message = brief.get("key_message", "")
    cta = brief.get("cta", "")
    persona_pain = brief.get("persona_pain_point", "")

    platform_lower = platform.lower()

    if platform_lower == "instagram":
        return {
            "format": "social_post",
            "platform": "instagram",
            "caption": (
                f"[Hook in first line -- stop the scroll. Max 2200 chars total.]\n\n"
                f"[Body: 3-5 short paragraphs. Emoji-friendly. Key message: {key_message[:60]}]\n\n"
                f"[CTA: {cta}]\n\n"
                f"[Hashtags: up to 30, mix of broad + niche]"
            ),
            "hashtags": ["[#broad1]", "[#broad2]", "[#niche1]", "[#niche2]", "[#branded]"],
            "cta": cta,
            "post_type": "image",
            "instructions": {
                "tone": "Visual-first language. Use emojis naturally. Line breaks between ideas.",
                "hashtag_count": "15-30 hashtags. Mix of broad (100K+), niche (10K-100K), and branded.",
                "hook": "First line must stop the scroll. Use a bold statement, question, or surprising stat.",
            },
        }

    if platform_lower == "linkedin":
        return {
            "format": "social_post",
            "platform": "linkedin",
            "caption": (
                f"[Hook: Professional insight or contrarian take, max 3000 chars total.]\n\n"
                f"[Body: Thought leadership content. Key message: {key_message[:60]}. "
                f"Pain point: {persona_pain[:40]}]\n\n"
                f"[CTA: {cta}]"
            ),
            "hashtags": ["[#industry1]", "[#topic1]", "[#branded]"],
            "cta": cta,
            "post_type": "text",
            "instructions": {
                "tone": "Professional but not corporate. Share insights, not sales pitches. First person.",
                "hashtag_count": "3-5 hashtags max. Industry-relevant only.",
                "hook": "First line is everything on LinkedIn. Use insight, data point, or contrarian opinion.",
                "formatting": "Short paragraphs. One idea per line. Use line breaks generously.",
            },
        }

    if platform_lower == "facebook":
        return {
            "format": "social_post",
            "platform": "facebook",
            "caption": (
                f"[Hook: Question or community-oriented opening.]\n\n"
                f"[Body: Conversational tone. Key message: {key_message[:60]}]\n\n"
                f"[CTA: {cta}]"
            ),
            "hashtags": [],
            "cta": cta,
            "post_type": "text",
            "instructions": {
                "tone": "Conversational, community-oriented. Ask questions. Encourage comments.",
                "hashtag_count": "0-3 hashtags. Facebook de-prioritizes hashtag-heavy posts.",
                "hook": "Open with a question or relatable situation. 'Have you ever...', 'Who else...'",
            },
        }

    if platform_lower == "tiktok":
        return {
            "format": "social_post",
            "platform": "tiktok",
            "caption": (
                f"[Hook first line -- grab in 1 second. Max 2200 chars.]\n"
                f"[Key message: {key_message[:60]}]\n"
                f"[CTA: {cta}]"
            ),
            "hashtags": ["[#trending1]", "[#niche1]", "[#fyp]"],
            "cta": cta,
            "post_type": "reel",
            "instructions": {
                "tone": "Trending language. Raw/authentic feel. No corporate polish.",
                "hashtag_count": "3-5 hashtags. Include #fyp or trending tags.",
                "hook": "First line/visual must create curiosity gap. 'Nobody talks about...' or 'The reason your...'",
                "video_note": "If video: hook in first 3 seconds, face-to-camera, text overlays throughout.",
            },
        }

    if platform_lower in ("twitter", "x"):
        return {
            "format": "social_post",
            "platform": "x",
            "caption": f"[Max 280 chars. Punchy, no filler. Key message: {key_message[:40]}]",
            "hashtags": ["[#relevant1]"],
            "cta": cta,
            "post_type": "text",
            "instructions": {
                "tone": "Concise and sharp. Every word must earn its place. Max 280 characters.",
                "hashtag_count": "0-2 hashtags. X penalizes hashtag-heavy posts.",
                "hook": "Lead with the punchline, not the buildup.",
            },
        }

    # Generic fallback for other platforms.
    return {
        "format": "social_post",
        "platform": platform,
        "caption": f"[Platform-appropriate caption. Key message: {key_message[:60]}]",
        "hashtags": [],
        "cta": cta,
        "post_type": "text",
        "instructions": {
            "note": f"No platform-specific rules defined for '{platform}'. Apply general best practices.",
        },
    }


# ============================================================================
# Email Generators
# ============================================================================


def generate_email(
    brief: Dict[str, Any],
    email_type: str,
) -> Dict[str, Any]:
    """Generate an email specification for the given type.

    Supported email_type values: welcome, nurture, cold_outreach,
    review_request, reactivation, quote_followup.
    """
    cta = brief.get("cta", "Learn More")
    cta_url = brief.get("cta_url", "#")
    key_message = brief.get("key_message", "")
    offer = brief.get("offer", "")
    persona_pain = brief.get("persona_pain_point", "")

    type_configs = {
        "welcome": {
            "subject_line": "[Max 60 chars. Warm, sets expectations. Personalization token: {first_name}]",
            "preview_text": "[Max 90 chars. Complement (don't repeat) subject. Deliver promised value hint.]",
            "body_sections": [
                {"type": "greeting", "content": "[Warm greeting with {first_name}. Thank them for signing up.]"},
                {"type": "body", "content": f"[Set expectations: what they'll receive, how often. Key message: {key_message[:60]}. 150-300 words total.]"},
                {"type": "body", "content": "[Deliver the promised value immediately: link to resource, tip, or quick win.]"},
                {"type": "cta", "content": f"[Primary CTA: {cta}]"},
                {"type": "signature", "content": "[Personal sign-off from a named person, not 'The Team']"},
            ],
            "word_range": "150-300",
            "tone": "Warm, enthusiastic, value-delivering",
        },
        "nurture": {
            "subject_line": f"[Max 60 chars. Educational hook related to: {persona_pain[:30]}]",
            "preview_text": "[Max 90 chars. Tease the insight without giving it away.]",
            "body_sections": [
                {"type": "greeting", "content": "[Brief, conversational greeting]"},
                {"type": "body", "content": f"[Educational content that builds trust. Position expertise. Key message: {key_message[:60]}. 200-500 words total.]"},
                {"type": "body", "content": "[Specific actionable tip or insight the reader can use immediately.]"},
                {"type": "cta", "content": f"[Soft CTA: {cta}. Frame as 'learn more' not 'buy now'.]"},
                {"type": "signature", "content": "[Personal sign-off]"},
            ],
            "word_range": "200-500",
            "tone": "Educational, trustworthy, expert but approachable",
        },
        "cold_outreach": {
            "subject_line": "[Max 60 chars. Personalized, no spam triggers. Reference their business by name.]",
            "preview_text": "[Max 90 chars. Specific to their situation.]",
            "body_sections": [
                {"type": "greeting", "content": "[Personalized first line referencing something specific about their business -- NOT generic.]"},
                {"type": "body", "content": f"[Ultra-concise pitch. One clear value prop. Key message: {key_message[:60]}. 75-150 words total.]"},
                {"type": "cta", "content": f"[Clear, low-friction ask: {cta}. One question, not a paragraph.]"},
                {"type": "signature", "content": "[Full name, title, company, phone number]"},
            ],
            "word_range": "75-150",
            "tone": "Concise, personalized, respectful of their time",
            "compliance": (
                "MUST follow CAN-SPAM rules from harness/references/cold-email-rules.md: "
                "physical address required, unsubscribe mechanism, accurate subject line, "
                "no deceptive headers."
            ),
        },
        "review_request": {
            "subject_line": "[Max 60 chars. Grateful, specific. '{first_name}, how was your [service]?']",
            "preview_text": "[Max 90 chars. Make it easy: 'Takes 30 seconds'.]",
            "body_sections": [
                {"type": "greeting", "content": "[Grateful greeting. Reference the specific service they received.]"},
                {"type": "body", "content": "[Brief ask: 1-2 sentences explaining how much reviews help. 75-150 words total.]"},
                {"type": "cta", "content": "[Direct link to Google/Yelp review page. Make it one-click.]"},
                {"type": "signature", "content": "[Personal sign-off from the person who served them]"},
            ],
            "word_range": "75-150",
            "tone": "Grateful, specific, easy",
        },
        "reactivation": {
            "subject_line": "[Max 60 chars. 'We miss you' angle OR new value announcement. {first_name} works.]",
            "preview_text": "[Max 90 chars. Special offer or 'what's new' tease.]",
            "body_sections": [
                {"type": "greeting", "content": "[Warm, non-guilting re-engagement. Acknowledge the gap.]"},
                {"type": "body", "content": f"[Remind them of the value. What's new or improved. Offer: {offer or 'special incentive'}. 100-250 words total.]"},
                {"type": "cta", "content": f"[Low-pressure CTA: {cta}. 'Come back and see' not 'Buy now'.]"},
                {"type": "signature", "content": "[Personal sign-off]"},
            ],
            "word_range": "100-250",
            "tone": "Warm, non-pressuring, value-reminding",
        },
        "quote_followup": {
            "subject_line": "[Max 60 chars. Helpful, addresses concerns. 'Your [service] quote + a quick question']",
            "preview_text": "[Max 90 chars. Additional value or reassurance.]",
            "body_sections": [
                {"type": "greeting", "content": "[Reference the quote they received. Be specific about the service.]"},
                {"type": "body", "content": f"[Helpful content: address common concerns, provide additional value. Key message: {key_message[:60]}. 100-200 words total.]"},
                {"type": "body", "content": "[Answer the #1 objection they likely have without them asking.]"},
                {"type": "cta", "content": f"[Helpful CTA: {cta}. Frame as 'happy to answer questions'.]"},
                {"type": "signature", "content": "[Personal sign-off with direct phone number]"},
            ],
            "word_range": "100-200",
            "tone": "Helpful, consultative, addressing concerns proactively",
        },
    }

    config = type_configs.get(email_type, type_configs["nurture"])

    result: Dict[str, Any] = {
        "format": "email",
        "email_type": email_type,
        "subject_line": config["subject_line"],
        "preview_text": config["preview_text"],
        "body_sections": config["body_sections"],
        "cta_text": cta,
        "cta_url": cta_url or "#",
        "instructions": {
            "subject_rules": "Max 60 chars. No spam trigger words (FREE, ACT NOW, URGENT). Personalization token where possible.",
            "preview_rules": "Max 90 chars. Complement subject line -- never repeat it.",
            "word_range": config["word_range"],
            "tone": config["tone"],
        },
    }

    if "compliance" in config:
        result["compliance"] = config["compliance"]

    return result


def generate_email_sequence(
    brief: Dict[str, Any],
    sequence_type: str,
) -> Dict[str, Any]:
    """Generate a full email sequence specification.

    Supported sequence_type values: welcome, review_request,
    reactivation, quote_followup.
    """
    cta = brief.get("cta", "Learn More")
    key_message = brief.get("key_message", "")
    offer = brief.get("offer", "")

    sequences = {
        "welcome": [
            {
                "email_number": 1,
                "delay_hours": 0,
                "subject": "[Immediate: Welcome + deliver promised value]",
                "preview": "[Set expectations for the relationship]",
                "body": f"[Welcome, deliver lead magnet or promised value, set expectations. Key: {key_message[:40]}]",
                "cta": cta,
                "purpose": "Deliver value immediately. Build trust. Set expectations.",
            },
            {
                "email_number": 2,
                "delay_hours": 48,
                "subject": "[Day 2: Educational content + quick win]",
                "preview": "[Tease an actionable tip]",
                "body": "[Share a specific, actionable tip they can implement today. Position expertise.]",
                "cta": cta,
                "purpose": "Establish expertise. Deliver a quick win.",
            },
            {
                "email_number": 3,
                "delay_hours": 120,
                "subject": "[Day 5: Social proof + soft sell]",
                "preview": "[Customer story or case study tease]",
                "body": f"[Share a customer story or result. Introduce offer: {offer or 'primary service'}. Soft CTA.]",
                "cta": cta,
                "purpose": "Build desire through social proof. Introduce the offer naturally.",
            },
        ],
        "review_request": [
            {
                "email_number": 1,
                "delay_hours": 24,
                "subject": "[Day after service: 'How was your experience?']",
                "preview": "[Takes 30 seconds]",
                "body": "[Grateful ask + direct review link. Reference the specific service.]",
                "cta": "Leave a Review",
                "purpose": "Primary review request. Strike while satisfaction is high.",
            },
            {
                "email_number": 2,
                "delay_hours": 168,
                "subject": "[1 week later: Gentle follow-up for non-responders]",
                "preview": "[Your feedback helps us improve]",
                "body": "[Softer ask. Explain how reviews help other customers find you.]",
                "cta": "Share Your Experience",
                "purpose": "Follow-up for non-responders only. Do not send if review was left.",
            },
        ],
        "reactivation": [
            {
                "email_number": 1,
                "delay_hours": 0,
                "subject": "[We miss you + what's new]",
                "preview": "[Something new since you last visited]",
                "body": f"[Acknowledge absence. Share what's new or improved. Key: {key_message[:40]}]",
                "cta": cta,
                "purpose": "Re-establish connection. Show value they're missing.",
            },
            {
                "email_number": 2,
                "delay_hours": 72,
                "subject": "[Special offer for returning customers]",
                "preview": f"[Exclusive: {offer or 'special incentive'}]",
                "body": f"[Offer incentive to return: {offer or 'exclusive discount'}. Time-limited.]",
                "cta": cta,
                "purpose": "Create urgency with a time-limited incentive.",
            },
            {
                "email_number": 3,
                "delay_hours": 168,
                "subject": "[Last chance / final reminder]",
                "preview": "[Offer expires soon]",
                "body": "[Final nudge. Restate value + expiring offer. Low-pressure close.]",
                "cta": cta,
                "purpose": "Last contact. If no response, move to suppression list.",
            },
        ],
        "quote_followup": [
            {
                "email_number": 1,
                "delay_hours": 4,
                "subject": "[Same day: Quote confirmation + additional value]",
                "preview": "[Your quote details + a helpful tip]",
                "body": "[Confirm quote details. Add value: answer the #1 objection. Include direct contact info.]",
                "cta": "Schedule Your Service",
                "purpose": "Reinforce the quote. Address concerns proactively.",
            },
            {
                "email_number": 2,
                "delay_hours": 72,
                "subject": "[Day 3: Social proof + address hesitation]",
                "preview": "[See what others are saying]",
                "body": "[Share a relevant testimonial or case study. Address common reasons people hesitate.]",
                "cta": "Ready to Get Started?",
                "purpose": "Overcome objections with social proof.",
            },
            {
                "email_number": 3,
                "delay_hours": 168,
                "subject": "[Day 7: Helpful check-in, not hard sell]",
                "preview": "[Still have questions?]",
                "body": "[Helpful check-in. Offer to update the quote. Mention availability or seasonal timing.]",
                "cta": "Let's Chat",
                "purpose": "Final touchpoint. Consultative, not pushy.",
            },
        ],
    }

    emails = sequences.get(sequence_type, sequences["welcome"])

    return {
        "format": "email_sequence",
        "sequence_type": sequence_type,
        "emails": emails,
        "instructions": {
            "personalization": "Use {first_name}, {company_name}, {service_type} tokens where available.",
            "subject_rules": "Max 60 chars per subject. No spam triggers. Each subject must be unique.",
            "overall_arc": f"Sequence arc: value -> trust -> conversion. Key message thread: {key_message[:60]}",
        },
    }


# ============================================================================
# Script Generators
# ============================================================================


def generate_call_script(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a phone call script specification.

    Includes greeting, qualification questions, pitch, objection
    handlers, close, and a voicemail script.
    """
    cta = brief.get("cta", "schedule a free consultation")
    key_message = brief.get("key_message", "")
    persona_pain = brief.get("persona_pain_point", "")
    offer = brief.get("offer", "")

    return {
        "format": "call_script",
        "greeting": (
            "[Professional greeting: 'Hi, this is [Name] from [Company]. "
            "Thanks for calling / Thanks for your interest in [service]. "
            "How can I help you today?']"
        ),
        "qualification_questions": [
            f"[Q1: Understand their need] 'What [service area] are you looking for help with?'",
            f"[Q2: Urgency/timeline] 'When are you looking to get this done?'",
            f"[Q3: Scope] 'Can you tell me a bit more about [specific detail]?'",
            f"[Q4: Budget awareness] 'Do you have a budget range in mind?'",
            f"[Q5: Decision process] 'Is there anyone else involved in making this decision?'",
        ],
        "pitch": (
            f"[2-3 sentence pitch based on: {key_message[:80]}. "
            f"Lead with their pain point: {persona_pain[:60]}. "
            f"Bridge to how you solve it. "
            f"End with the offer: {offer or 'free estimate / consultation'}.]"
        ),
        "objection_handlers": [
            {
                "objection": "Too expensive / need to think about it",
                "response": (
                    "[Acknowledge: 'I completely understand.' Reframe: compare cost "
                    "of inaction vs. investment. Offer: smaller first step or payment plan.]"
                ),
            },
            {
                "objection": "Need to talk to spouse/partner",
                "response": (
                    "[Respect: 'Absolutely, important decisions together.' "
                    "Equip: 'Want me to send a summary to share?' "
                    "Schedule: 'When's a good time for a follow-up?']"
                ),
            },
            {
                "objection": "Getting other quotes",
                "response": (
                    "[Encourage: 'Smart approach.' Differentiate: share 1-2 specific "
                    "advantages. Confidence: 'We're happy to be compared.']"
                ),
            },
            {
                "objection": "Not ready yet / just researching",
                "response": (
                    "[Respect timeline. Add value: answer a question or share a tip. "
                    "Stay connected: 'Mind if I follow up in [timeframe]?']"
                ),
            },
            {
                "objection": "Had a bad experience before",
                "response": (
                    "[Empathize: 'That's frustrating.' Differentiate: explain specific "
                    "process that prevents that issue. Proof: reference reviews or guarantee.]"
                ),
            },
        ],
        "close": (
            f"[Summarize what they need. Confirm next step: '{cta}'. "
            f"Get commitment: date, time, or action. "
            f"'I'll send a confirmation to your email. Is [date/time] still good?']"
        ),
        "voicemail_script": (
            "[30 seconds max, ~80 words] "
            "'Hi [Name], this is [Your Name] from [Company]. "
            "I'm calling about [specific reason -- reference their inquiry or need]. "
            "[One sentence value prop]. "
            "Give me a call back at [phone number] -- that's [phone number]. "
            "Or you can [alternative: text, visit website, reply to email]. "
            "Looking forward to hearing from you!'"
        ),
        "instructions": {
            "tone": "Professional, warm, consultative. Never pushy.",
            "voicemail_max_words": 80,
            "voicemail_max_seconds": 30,
            "qualification_first": "Always qualify before pitching. Listen more than talk.",
        },
    }


def generate_video_script(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a video script specification.

    Structure: hook (3s) -> problem -> solution -> proof -> CTA.
    Includes text overlay suggestions for each segment.
    """
    key_message = brief.get("key_message", "")
    persona_pain = brief.get("persona_pain_point", "")
    cta = brief.get("cta", "")
    proof = brief.get("proof_available", "")
    duration = brief.get("duration_target", "30 seconds")

    # Parse duration to seconds.
    try:
        if isinstance(duration, str):
            if "minute" in duration:
                total_seconds = int(duration.split()[0]) * 60
            else:
                total_seconds = int(duration.split()[0])
        elif isinstance(duration, (int, float)):
            total_seconds = int(duration)
        else:
            total_seconds = 30
    except (ValueError, IndexError):
        total_seconds = 30

    return {
        "format": "video_script",
        "hook": (
            f"[FIRST 3 SECONDS: Attention grab. Visual + text that stops scrolling. "
            f"Related to pain point: {persona_pain[:60]}]"
        ),
        "hook_duration_seconds": 3,
        "main_content": [
            {
                "timestamp": "0:00-0:03",
                "visual": "[Face-to-camera or striking visual]",
                "narration": "[Hook line: bold statement, question, or surprising stat]",
                "text_overlay": f"[Bold text overlay summarizing hook. Pain: {persona_pain[:40]}]",
            },
            {
                "timestamp": "0:03-0:10",
                "visual": "[Show the problem visually or describe it]",
                "narration": f"[Describe the problem. Pain point: {persona_pain[:50]}]",
                "text_overlay": "[Problem statement in 5-7 words]",
            },
            {
                "timestamp": "0:10-0:20",
                "visual": "[Show the solution / your service in action]",
                "narration": f"[Present the solution. Key message: {key_message[:50]}]",
                "text_overlay": "[Solution headline in 5-7 words]",
            },
            {
                "timestamp": f"0:20-0:{total_seconds - 5}",
                "visual": "[Show proof: results, testimonials, before/after]",
                "narration": f"[Social proof or specific result. Proof: {proof[:50]}]",
                "text_overlay": "[Specific number or result]",
            },
            {
                "timestamp": f"0:{total_seconds - 5}-0:{total_seconds}",
                "visual": "[CTA card or branded end screen]",
                "narration": f"[Clear CTA: {cta}]",
                "text_overlay": f"[CTA text: {cta}]",
            },
        ],
        "cta": cta,
        "total_duration_seconds": total_seconds,
        "instructions": {
            "hook_rule": "Hook MUST grab attention in first 3 seconds. If shooting face-to-camera, start mid-sentence.",
            "structure": "Hook -> Problem -> Solution -> Proof -> CTA. Do not deviate.",
            "text_overlays": "Every segment needs a text overlay. Many viewers watch without sound.",
            "pacing": f"Target {total_seconds} seconds total. Cut anything that doesn't serve the message.",
        },
    }


# ============================================================================
# Quality Gate Integration
# ============================================================================


def check_quality(
    output: Dict[str, Any],
    brief: Dict[str, Any],
) -> Dict[str, Any]:
    """Return a quality check plan for the given CopyOutput.

    This function does NOT execute scripts.  It returns the check plan
    (script paths + thresholds) for the execution layer to run.
    """
    thresholds = brief.get("quality_gate_thresholds") or {}
    four_us_min = thresholds.get("four_us_min", 12)
    banned_words = thresholds.get("banned_words_check", True)
    seo_lint = thresholds.get("seo_lint", False)
    has_keyword = bool(brief.get("target_keyword"))

    checks: List[Dict[str, Any]] = [
        {
            "name": "four_us",
            "threshold": four_us_min,
            "script": "scripts/quality_gates/four_us_score.py",
            "description": (
                f"Four U's score must be >= {four_us_min}/16. "
                "Scores Unique, Useful, Ultra-specific, Urgent (1-4 each)."
            ),
        },
    ]

    if banned_words:
        checks.append({
            "name": "banned_words",
            "threshold": 0,
            "script": "scripts/quality_gates/banned_word_check.py",
            "description": "Zero Tier 1 banned words allowed.",
        })

    if seo_lint or has_keyword:
        checks.append({
            "name": "seo_lint",
            "threshold": None,
            "script": "scripts/quality_gates/seo_lint.py",
            "description": (
                "Algorithmic authorship rule compliance. "
                "Conditions after main clause, instructions start with verbs, "
                "sentences under 20 words."
            ),
        })

    return {
        "checks": checks,
        "applies_seo_lint": seo_lint or has_keyword,
        "content_id": output.get("id", ""),
        "brief_id": brief.get("id", ""),
    }


def plan_revision(
    output: Dict[str, Any],
    quality_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Produce revision instructions from quality gate results.

    Parameters
    ----------
    output:
        A CopyOutput dict with current content.
    quality_results:
        Quality gate results dict with keys like ``four_us_score``,
        ``banned_words_found``, ``seo_lint_failures``.

    Returns
    -------
    Dict[str, Any]
        Revision plan with specific fix instructions.
    """
    instructions: List[str] = []
    revision_needed = False

    # Current retry state.
    current_status = output.get("quality_status", "pending")
    retry_map = {"pending": 1, "retry_1": 2, "retry_2": 3}
    retry_number = retry_map.get(current_status, 1)

    # Four U's failures.
    four_us = quality_results.get("four_us", {})
    if isinstance(four_us, dict):
        score = four_us.get("score", 0)
        threshold = four_us.get("threshold", 12)
        if score < threshold:
            revision_needed = True
            subscores = four_us.get("subscores", {})
            lowest = sorted(subscores.items(), key=lambda x: x[1]) if subscores else []

            instruction = f"Four U's score {score}/{threshold} -- below threshold."
            if lowest:
                weakest = lowest[0]
                u_improvements = {
                    "unique": "Add proprietary data, a named methodology, or a personal experience only you can share.",
                    "useful": "Add a specific, actionable step the reader can take immediately after reading.",
                    "ultra_specific": "Replace vague claims with specific numbers, named tools, or concrete examples.",
                    "urgent": "Add a time-sensitive element: deadline, seasonal relevance, or consequence of waiting.",
                }
                fix = u_improvements.get(weakest[0], "Improve this dimension with more specificity.")
                instruction += f" Weakest: '{weakest[0]}' ({weakest[1]}/4). Fix: {fix}"
            instructions.append(instruction)

    # Banned words.
    banned = quality_results.get("banned_words_found") or []
    if banned:
        revision_needed = True
        replacements = {
            "leverage": "use",
            "utilize": "use",
            "synergy": "collaboration",
            "innovative": "new, specific description of what's new",
            "deep dive": "detailed look, thorough analysis",
            "circle back": "follow up, revisit",
            "touch base": "check in, connect",
            "moving forward": "next, from here",
            "at the end of the day": "ultimately, in practice",
        }
        for word in banned:
            replacement = replacements.get(word.lower(), "[replace with specific language]")
            instructions.append(f"Remove banned word '{word}'. Replace with: {replacement}")

    # SEO lint failures.
    seo_failures = quality_results.get("seo_lint_failures") or []
    if seo_failures:
        revision_needed = True
        for failure in seo_failures:
            if isinstance(failure, dict):
                rule = failure.get("rule", "unknown")
                location = failure.get("location", "")
                fix = failure.get("fix", "Review algorithmic authorship rules")
                instructions.append(f"SEO lint: {rule} at {location}. Fix: {fix}")
            elif isinstance(failure, str):
                instructions.append(f"SEO lint failure: {failure}")

    return {
        "revision_needed": revision_needed,
        "revision_instructions": instructions,
        "retry_number": retry_number,
        "max_retries": 2,
        "should_escalate": retry_number > 2,
        "escalation_note": (
            "Max retries exceeded. Surface to human with these failures: "
            + "; ".join(instructions[:3])
        ) if retry_number > 2 else "",
    }


# ============================================================================
# Main Orchestrator
# ============================================================================


def generate_copy(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch to the correct generator based on ``brief.format``.

    Returns a CopyOutput dict wrapping the generated content with
    a quality check plan attached.
    """
    content_format = brief.get("format", "blog_post")
    channel = brief.get("channel", "website")

    # Dispatch to the appropriate generator.
    generated: Dict[str, Any] = {}
    sections: List[Dict[str, Any]] = []

    if content_format == "landing_page":
        generated = generate_landing_page(brief)
        sections = generated.get("sections", [])

    elif content_format in ("service_page", "service_area_page"):
        hero = generate_hero_section(brief)
        service = generate_service_description(brief)
        testimonials = generate_testimonial_block(brief)
        faq = generate_faq_section(brief)
        cta_block = generate_cta_block(brief)
        sections = [hero, service, testimonials, faq, cta_block]
        generated = {"format": content_format, "sections": sections}

    elif content_format == "homepage_section":
        hero = generate_hero_section(brief)
        value_props = generate_value_prop_section(brief)
        sections = [hero, value_props]
        generated = {"format": content_format, "sections": sections}

    elif content_format in ("web_section", "faq_section"):
        if content_format == "faq_section":
            section = generate_faq_section(brief)
        else:
            section = generate_service_description(brief)
        sections = [section]
        generated = {"format": content_format, "sections": sections}

    elif content_format == "ad_copy":
        # Determine ad platform from channel.
        if "google" in channel.lower():
            generated = generate_google_ads_copy(brief)
        elif "meta" in channel.lower() or "facebook" in channel.lower() or "instagram" in channel.lower():
            generated = generate_meta_ads_copy(brief)
        else:
            generated = generate_social_ad_copy(brief, channel)
        sections = [generated]

    elif content_format == "social_post":
        platform = channel if channel != "website" else "instagram"
        generated = generate_social_post(brief, platform)
        sections = [generated]

    elif content_format.startswith("email_"):
        email_type = content_format.replace("email_", "")
        generated = generate_email(brief, email_type)
        sections = generated.get("body_sections", [])

    elif content_format == "call_script":
        generated = generate_call_script(brief)
        sections = [generated]

    elif content_format == "video_script":
        generated = generate_video_script(brief)
        sections = generated.get("main_content", [])

    elif content_format == "social_reel":
        generated = generate_video_script(brief)
        sections = generated.get("main_content", [])

    elif content_format == "case_study":
        hero = generate_hero_section(brief)
        service = generate_service_description(brief)
        testimonials = generate_testimonial_block(brief)
        cta_block = generate_cta_block(brief)
        sections = [hero, service, testimonials, cta_block]
        generated = {"format": content_format, "sections": sections}

    elif content_format == "press_release":
        sections = [
            {
                "section_type": "press_headline",
                "content": f"[FOR IMMEDIATE RELEASE headline based on: {brief.get('key_message', '')[:60]}]",
            },
            {
                "section_type": "press_subheadline",
                "content": "[Subheadline expanding on the news with specific details]",
            },
            {
                "section_type": "press_dateline",
                "content": "[CITY, State -- Date --]",
            },
            {
                "section_type": "press_body",
                "content": (
                    "[Lead paragraph: who, what, when, where, why in 2-3 sentences. "
                    f"Key message: {brief.get('key_message', '')[:80]}]"
                ),
            },
            {
                "section_type": "press_quote",
                "content": "[Quote from company spokesperson with name and title]",
            },
            {
                "section_type": "press_boilerplate",
                "content": "[Company boilerplate: 2-3 sentences about the company]",
            },
            {
                "section_type": "press_contact",
                "content": "[Media contact: name, email, phone]",
            },
        ]
        generated = {"format": content_format, "sections": sections}

    elif content_format in ("blog_post", "linkedin_article"):
        sections = [
            {
                "section_type": "headline",
                "content": f"[Headline targeting '{brief.get('target_keyword', '')}'. Max 60 chars for search display.]",
            },
            {
                "section_type": "hook",
                "content": (
                    "[Opening paragraph: hook the reader in 2-3 sentences. "
                    f"Pain point: {brief.get('persona_pain_point', '')[:60]}. "
                    "Algorithmic authorship: conditions after main clause.]"
                ),
            },
            {
                "section_type": "body",
                "content": (
                    f"[Main content. Key message: {brief.get('key_message', '')[:60]}. "
                    f"Word count target: {brief.get('word_count_target', 1400)}. "
                    "Apply all algorithmic authorship rules.]"
                ),
            },
            {
                "section_type": "cta",
                "content": f"[Closing CTA: {brief.get('cta', 'Learn more')}]",
            },
        ]
        generated = {"format": content_format, "sections": sections}

    else:
        # Generic fallback.
        sections = [
            {
                "section_type": "content",
                "content": f"[Content for format '{content_format}'. Key message: {brief.get('key_message', '')[:80]}]",
            },
        ]
        generated = {"format": content_format, "sections": sections}

    # Build full text from sections.
    full_text = _sections_to_full_text(sections)
    word_count = _count_words(full_text)

    # Build CopyOutput.
    output_dict = CopyOutput(
        brief_id=brief.get("id", ""),
        format=content_format,
        sections=sections,
        full_text=full_text,
        word_count=word_count,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata={"generated_content": generated},
    ).model_dump()

    # Attach quality check plan.
    output_dict["quality_check_plan"] = check_quality(output_dict, brief)

    return output_dict

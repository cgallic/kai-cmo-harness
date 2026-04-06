"""Reusable creative libraries — CTAs, offers, and approved message blocks.

Provides curated default entries organized by archetype and channel, plus
functions to load, extend, query, and merge libraries.  The library system
acts as an "ingredient pantry" for the copy engine: instead of generating
CTAs and trust statements from scratch every time, it pulls from proven
defaults and business-specific customizations.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import os
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# YAML import — graceful degradation to a stripped-down parser
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    _yaml = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
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
# Library Entry Models
# ============================================================================


class CTAEntry(BaseModel):
    """A single call-to-action entry in the creative library."""

    id: str
    text: str
    short_text: Optional[str] = None
    archetype_tags: List[str] = Field(default_factory=list)
    channel_tags: List[str] = Field(default_factory=list)
    intent: str = "learn_more"
    urgency_level: str = "none"
    compliance_notes: Optional[str] = None
    quality_score: float = 0.5
    source: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OfferEntry(BaseModel):
    """A single offer template in the creative library."""

    id: str
    name: str
    description: str = ""
    offer_type: str = "free_consultation"
    archetype_tags: List[str] = Field(default_factory=list)
    channel_tags: List[str] = Field(default_factory=list)
    typical_value: Optional[str] = None
    urgency_type: Optional[str] = "none"
    terms_template: Optional[str] = None
    compliance_notes: Optional[str] = None
    quality_score: float = 0.5
    source: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageBlockEntry(BaseModel):
    """A pre-approved, reusable copy block with variable placeholders."""

    id: str
    content: str
    block_type: str = "value_prop"
    archetype_tags: List[str] = Field(default_factory=list)
    channel_tags: List[str] = Field(default_factory=list)
    compliance_notes: Optional[str] = None
    quality_score: float = 0.5
    variables: List[str] = Field(default_factory=list)
    source: str = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreativeLibrary(BaseModel):
    """Top-level container holding all creative library entries."""

    ctas: List[CTAEntry] = Field(default_factory=list)
    offers: List[OfferEntry] = Field(default_factory=list)
    message_blocks: List[MessageBlockEntry] = Field(default_factory=list)
    business_id: Optional[str] = None
    last_updated: Optional[str] = None


# ============================================================================
# Internal helpers
# ============================================================================

_DATA_DIR = os.path.join(os.path.dirname(__file__), "library_data")

_PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")


def _parse_cta(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw CTA dict into a CTAEntry-compatible dict."""
    return {
        "id": raw.get("id", ""),
        "text": raw.get("text", ""),
        "short_text": raw.get("short_text"),
        "archetype_tags": raw.get("archetype_tags", []),
        "channel_tags": raw.get("channel_tags", []),
        "intent": raw.get("intent", "learn_more"),
        "urgency_level": raw.get("urgency_level", "none"),
        "compliance_notes": raw.get("compliance_notes"),
        "quality_score": float(raw.get("quality_score", 0.5)),
        "source": raw.get("source", "default"),
        "metadata": raw.get("metadata", {}),
    }


def _parse_offer(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw offer dict into an OfferEntry-compatible dict."""
    return {
        "id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "description": raw.get("description", ""),
        "offer_type": raw.get("offer_type", "free_consultation"),
        "archetype_tags": raw.get("archetype_tags", []),
        "channel_tags": raw.get("channel_tags", []),
        "typical_value": raw.get("typical_value"),
        "urgency_type": raw.get("urgency_type", "none"),
        "terms_template": raw.get("terms_template"),
        "compliance_notes": raw.get("compliance_notes"),
        "quality_score": float(raw.get("quality_score", 0.5)),
        "source": raw.get("source", "default"),
        "metadata": raw.get("metadata", {}),
    }


def _parse_message_block(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw message block dict into a MessageBlockEntry-compatible dict."""
    # Auto-detect variables from content if not explicitly listed
    content = raw.get("content", "")
    declared_vars = raw.get("variables", [])
    if not declared_vars and content:
        declared_vars = _PLACEHOLDER_RE.findall(content)

    return {
        "id": raw.get("id", ""),
        "content": content,
        "block_type": raw.get("block_type", "value_prop"),
        "archetype_tags": raw.get("archetype_tags", []),
        "channel_tags": raw.get("channel_tags", []),
        "compliance_notes": raw.get("compliance_notes"),
        "quality_score": float(raw.get("quality_score", 0.5)),
        "variables": declared_vars,
        "source": raw.get("source", "default"),
        "metadata": raw.get("metadata", {}),
    }


def _load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Raises ``RuntimeError`` if the ``yaml`` package is not installed.
    Returns an empty dict if the file does not exist or is empty.
    """
    if _yaml is None:
        raise RuntimeError(
            "PyYAML is required to load YAML library files. "
            "Install it with: pip install pyyaml"
        )

    if not os.path.isfile(file_path):
        return {}

    with open(file_path, "r", encoding="utf-8") as fh:
        data = _yaml.safe_load(fh)

    return data if isinstance(data, dict) else {}


def _library_to_dict(lib: CreativeLibrary) -> Dict[str, Any]:
    """Convert a CreativeLibrary instance to a plain dict."""
    if hasattr(lib, "model_dump"):
        return lib.model_dump()
    # Fallback for the minimal shim
    return {
        "ctas": [c.model_dump() if hasattr(c, "model_dump") else c for c in lib.ctas],
        "offers": [o.model_dump() if hasattr(o, "model_dump") else o for o in lib.offers],
        "message_blocks": [
            m.model_dump() if hasattr(m, "model_dump") else m for m in lib.message_blocks
        ],
        "business_id": lib.business_id,
        "last_updated": lib.last_updated,
    }


# ============================================================================
# Default library data (hardcoded fallback)
# ============================================================================

# These mirror the YAML files in library_data/ and serve as an in-memory
# fallback when YAML loading is unavailable (no PyYAML installed, or the
# YAML files are missing from a deployment).

_DEFAULT_CTAS: List[Dict[str, Any]] = [
    # --- Local-service (1-7) ---
    _parse_cta({
        "id": "cta-local-001", "text": "Call Now for a Free Quote",
        "short_text": "Call Now", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads"], "intent": "call",
        "urgency_level": "medium", "quality_score": 0.85,
    }),
    _parse_cta({
        "id": "cta-local-002", "text": "Schedule Your Free Estimate",
        "short_text": "Schedule Now", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "email"], "intent": "schedule",
        "urgency_level": "low", "quality_score": 0.80,
    }),
    _parse_cta({
        "id": "cta-local-003", "text": "Get a Free Quote in 60 Seconds",
        "short_text": "Free Quote", "archetype_tags": ["local-service"],
        "channel_tags": ["website"], "intent": "form_submit",
        "urgency_level": "medium", "quality_score": 0.82,
    }),
    _parse_cta({
        "id": "cta-local-004", "text": "Book Your Appointment",
        "short_text": "Book Now", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "social"], "intent": "schedule",
        "urgency_level": "low", "quality_score": 0.75,
    }),
    _parse_cta({
        "id": "cta-local-005", "text": "Call {phone} — Available 24/7",
        "short_text": "Call 24/7", "archetype_tags": ["local-service"],
        "channel_tags": ["website"], "intent": "call",
        "urgency_level": "high", "quality_score": 0.88,
        "compliance_notes": "Ensure 24/7 availability claim is accurate.",
    }),
    _parse_cta({
        "id": "cta-local-006", "text": "See Our Work",
        "short_text": "Our Work", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "social"], "intent": "learn_more",
        "urgency_level": "none", "quality_score": 0.65,
    }),
    _parse_cta({
        "id": "cta-local-007", "text": "Request a Callback",
        "short_text": "Callback", "archetype_tags": ["local-service"],
        "channel_tags": ["website"], "intent": "form_submit",
        "urgency_level": "low", "quality_score": 0.72,
    }),
    # --- Ecommerce (8-14) ---
    _parse_cta({
        "id": "cta-ecom-001", "text": "Add to Cart",
        "short_text": "Add", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website"], "intent": "purchase",
        "urgency_level": "none", "quality_score": 0.90,
    }),
    _parse_cta({
        "id": "cta-ecom-002", "text": "Shop Now",
        "short_text": "Shop", "archetype_tags": ["ecommerce"],
        "channel_tags": ["ads", "social", "email"], "intent": "purchase",
        "urgency_level": "low", "quality_score": 0.88,
    }),
    _parse_cta({
        "id": "cta-ecom-003", "text": "Claim Your Discount",
        "short_text": "Claim Discount", "archetype_tags": ["ecommerce"],
        "channel_tags": ["email", "ads"], "intent": "purchase",
        "urgency_level": "high", "quality_score": 0.84,
        "compliance_notes": "Discount must be currently active and valid.",
    }),
    _parse_cta({
        "id": "cta-ecom-004", "text": "Buy Now — Free Shipping Over $50",
        "short_text": "Buy Now", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website"], "intent": "purchase",
        "urgency_level": "medium", "quality_score": 0.83,
        "compliance_notes": "Free shipping threshold must be accurate.",
    }),
    _parse_cta({
        "id": "cta-ecom-005", "text": "Get 20% Off Your First Order",
        "short_text": "20% Off", "archetype_tags": ["ecommerce"],
        "channel_tags": ["ads", "email"], "intent": "purchase",
        "urgency_level": "high", "quality_score": 0.86,
        "compliance_notes": "First-order discount must be honored. Specify terms.",
    }),
    _parse_cta({
        "id": "cta-ecom-006", "text": "Shop the Collection",
        "short_text": "Shop Collection", "archetype_tags": ["ecommerce"],
        "channel_tags": ["social"], "intent": "learn_more",
        "urgency_level": "none", "quality_score": 0.70,
    }),
    _parse_cta({
        "id": "cta-ecom-007", "text": "Join the Waitlist",
        "short_text": "Join Waitlist", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "social"], "intent": "subscribe",
        "urgency_level": "medium", "quality_score": 0.76,
    }),
    # --- Professional-services (15-19) ---
    _parse_cta({
        "id": "cta-prof-001", "text": "Schedule a Consultation",
        "short_text": "Schedule", "archetype_tags": ["professional-services"],
        "channel_tags": ["website"], "intent": "schedule",
        "urgency_level": "low", "quality_score": 0.82,
    }),
    _parse_cta({
        "id": "cta-prof-002", "text": "Book Your Free Strategy Session",
        "short_text": "Free Strategy Session", "archetype_tags": ["professional-services"],
        "channel_tags": ["website", "ads"], "intent": "schedule",
        "urgency_level": "medium", "quality_score": 0.85,
    }),
    _parse_cta({
        "id": "cta-prof-003", "text": "Get Started Today",
        "short_text": "Get Started", "archetype_tags": ["professional-services"],
        "channel_tags": ["website", "email"], "intent": "form_submit",
        "urgency_level": "medium", "quality_score": 0.78,
    }),
    _parse_cta({
        "id": "cta-prof-004", "text": "Download the Guide",
        "short_text": "Download", "archetype_tags": ["professional-services"],
        "channel_tags": ["website", "email"], "intent": "download",
        "urgency_level": "low", "quality_score": 0.74,
    }),
    _parse_cta({
        "id": "cta-prof-005", "text": "Request a Proposal",
        "short_text": "Request Proposal", "archetype_tags": ["professional-services"],
        "channel_tags": ["website"], "intent": "form_submit",
        "urgency_level": "low", "quality_score": 0.77,
    }),
    # --- Multi-location (20-22) ---
    _parse_cta({
        "id": "cta-multi-001", "text": "Find Your Nearest Location",
        "short_text": "Find Location", "archetype_tags": ["multi-location"],
        "channel_tags": ["website"], "intent": "learn_more",
        "urgency_level": "low", "quality_score": 0.80,
    }),
    _parse_cta({
        "id": "cta-multi-002", "text": "Check Availability in Your Area",
        "short_text": "Check Availability", "archetype_tags": ["multi-location"],
        "channel_tags": ["website", "ads"], "intent": "form_submit",
        "urgency_level": "low", "quality_score": 0.78,
    }),
    _parse_cta({
        "id": "cta-multi-003", "text": "Visit Us Today",
        "short_text": "Visit Us", "archetype_tags": ["multi-location"],
        "channel_tags": ["ads", "social"], "intent": "learn_more",
        "urgency_level": "medium", "quality_score": 0.75,
    }),
    # --- Universal (23-25) ---
    _parse_cta({
        "id": "cta-univ-001", "text": "Learn More",
        "short_text": "Learn More",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["all"], "intent": "learn_more",
        "urgency_level": "none", "quality_score": 0.60,
    }),
    _parse_cta({
        "id": "cta-univ-002", "text": "Subscribe for Updates",
        "short_text": "Subscribe",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website", "email"], "intent": "subscribe",
        "urgency_level": "none", "quality_score": 0.62,
    }),
    _parse_cta({
        "id": "cta-univ-003", "text": "Contact Us",
        "short_text": "Contact",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website"], "intent": "form_submit",
        "urgency_level": "none", "quality_score": 0.58,
    }),
]


_DEFAULT_OFFERS: List[Dict[str, Any]] = [
    # --- Local-service (1-5) ---
    _parse_offer({
        "id": "offer-local-001", "name": "Free Estimate",
        "description": "No-obligation, free on-site or virtual estimate for any service.",
        "offer_type": "free_consultation", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "social"], "typical_value": "Free ($0)",
        "urgency_type": "none",
        "terms_template": "Free estimate with no obligation. Service area restrictions may apply.",
        "quality_score": 0.85,
    }),
    _parse_offer({
        "id": "offer-local-002", "name": "10% Off First Service",
        "description": "New customers receive 10% off their first service booking.",
        "offer_type": "percentage_off", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "email"], "typical_value": "10% off",
        "urgency_type": "first_time_only",
        "terms_template": "Valid for new customers only. Cannot be combined with other offers. Mention this offer when booking.",
        "compliance_notes": "Ensure discount is applied at checkout or invoicing.",
        "quality_score": 0.80,
    }),
    _parse_offer({
        "id": "offer-local-003", "name": "$50 Off Any Service Over $300",
        "description": "Save $50 on any service totaling $300 or more.",
        "offer_type": "dollar_off", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads"], "typical_value": "$50 off",
        "urgency_type": "none",
        "terms_template": "Valid on services totaling $300 or more before tax. One per customer per transaction.",
        "quality_score": 0.78,
    }),
    _parse_offer({
        "id": "offer-local-004", "name": "Free Safety Inspection",
        "description": "Complimentary safety inspection of your system or equipment.",
        "offer_type": "free_consultation", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "email", "social"], "typical_value": "Free ($0)",
        "urgency_type": "none",
        "terms_template": "Free safety inspection for residential properties. Commercial properties quoted separately.",
        "quality_score": 0.76,
    }),
    _parse_offer({
        "id": "offer-local-005", "name": "Seasonal Tune-Up Special",
        "description": "Discounted seasonal maintenance tune-up to keep your systems running efficiently.",
        "offer_type": "seasonal", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "email", "ads"], "typical_value": "15-25% off",
        "urgency_type": "seasonal",
        "terms_template": "Available during {season} season only. Schedule by {end_date} to lock in pricing.",
        "compliance_notes": "Update season and end date before publishing.",
        "quality_score": 0.82,
    }),
    # --- Ecommerce (6-10) ---
    _parse_offer({
        "id": "offer-ecom-001", "name": "Free Shipping on Orders Over $50",
        "description": "All orders over $50 ship free within the continental US.",
        "offer_type": "free_shipping", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "email", "ads"], "typical_value": "Free shipping",
        "urgency_type": "none",
        "terms_template": "Free standard shipping on orders over $50 within the continental US. Excludes Alaska, Hawaii, and international.",
        "compliance_notes": "Shipping threshold and exclusions must be accurate.",
        "quality_score": 0.88,
    }),
    _parse_offer({
        "id": "offer-ecom-002", "name": "Buy 2 Get 1 Free",
        "description": "Purchase any two items and receive the third (of equal or lesser value) free.",
        "offer_type": "bogo", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "ads", "social"], "typical_value": "33% savings",
        "urgency_type": "time_limited",
        "terms_template": "Buy 2 get 1 free on select items. Free item must be of equal or lesser value. Offer ends {end_date}.",
        "compliance_notes": "Specify which items are eligible. State end date clearly.",
        "quality_score": 0.84,
    }),
    _parse_offer({
        "id": "offer-ecom-003", "name": "20% Off First Purchase",
        "description": "New customers get 20% off their first order with code.",
        "offer_type": "percentage_off", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "email", "ads"], "typical_value": "20% off",
        "urgency_type": "first_time_only",
        "terms_template": "20% off your first order. Use code {code} at checkout. Cannot be combined with other discounts.",
        "compliance_notes": "Promo code must be active and working before running ads.",
        "quality_score": 0.86,
    }),
    _parse_offer({
        "id": "offer-ecom-004", "name": "Holiday Sale — Up to 40% Off",
        "description": "Seasonal holiday sale with discounts up to 40% on select items.",
        "offer_type": "seasonal", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "email", "ads", "social"], "typical_value": "Up to 40% off",
        "urgency_type": "seasonal",
        "terms_template": "Holiday sale runs {start_date} through {end_date}. Discounts vary by product. While supplies last.",
        "compliance_notes": "Up to language requires that at least some items are discounted at the maximum stated.",
        "quality_score": 0.83,
    }),
    _parse_offer({
        "id": "offer-ecom-005", "name": "Free Returns Within 30 Days",
        "description": "Try it risk-free — return any item within 30 days for a full refund.",
        "offer_type": "trial", "archetype_tags": ["ecommerce"],
        "channel_tags": ["website", "email"], "typical_value": "Risk-free purchase",
        "urgency_type": "none",
        "terms_template": "Items must be in original condition with tags attached. Return shipping is free for US orders.",
        "compliance_notes": "Return policy must match actual business policy.",
        "quality_score": 0.80,
    }),
    # --- Professional-services (11-14) ---
    _parse_offer({
        "id": "offer-prof-001", "name": "Free 30-Minute Consultation",
        "description": "Complimentary 30-minute phone or video consultation to discuss your needs.",
        "offer_type": "free_consultation", "archetype_tags": ["professional-services"],
        "channel_tags": ["website", "ads", "email"], "typical_value": "Free ($0)",
        "urgency_type": "none",
        "terms_template": "Free 30-minute consultation by phone or video. No obligation. One per prospect.",
        "quality_score": 0.84,
    }),
    _parse_offer({
        "id": "offer-prof-002", "name": "Free Audit Report",
        "description": "Receive a complimentary audit report identifying key opportunities.",
        "offer_type": "free_consultation", "archetype_tags": ["professional-services"],
        "channel_tags": ["website", "email", "ads"], "typical_value": "Free ($0)",
        "urgency_type": "none",
        "terms_template": "Free audit report delivered within {delivery_days} business days. No obligation.",
        "quality_score": 0.82,
    }),
    _parse_offer({
        "id": "offer-prof-003", "name": "10% Off Annual Plans",
        "description": "Save 10% when you commit to an annual engagement.",
        "offer_type": "percentage_off", "archetype_tags": ["professional-services", "saas"],
        "channel_tags": ["website", "email"], "typical_value": "10% off annual",
        "urgency_type": "none",
        "terms_template": "10% discount applied to annual plan pricing. Must commit to a 12-month agreement.",
        "quality_score": 0.78,
    }),
    _parse_offer({
        "id": "offer-prof-004", "name": "Refer a Friend, Get $100 Credit",
        "description": "Earn $100 service credit for every successful referral.",
        "offer_type": "referral", "archetype_tags": ["professional-services"],
        "channel_tags": ["email", "website"], "typical_value": "$100 credit",
        "urgency_type": "none",
        "terms_template": "Referral must become an active client. Credit applied to your next invoice. No limit on referrals.",
        "compliance_notes": "Check state regulations on referral incentives for regulated industries.",
        "quality_score": 0.76,
    }),
    # --- Universal (15) ---
    _parse_offer({
        "id": "offer-univ-001", "name": "Money-Back Guarantee",
        "description": "100% satisfaction guaranteed or your money back.",
        "offer_type": "trial",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website", "email", "ads"], "typical_value": "Full refund",
        "urgency_type": "none",
        "terms_template": "If you are not completely satisfied, contact us within {days} days for a full refund.",
        "compliance_notes": "Money-back guarantee must be honored as stated. Specify the refund window.",
        "quality_score": 0.90,
    }),
]


_DEFAULT_MESSAGE_BLOCKS: List[Dict[str, Any]] = [
    # --- Trust statements (1-4) ---
    _parse_message_block({
        "id": "msg-trust-001",
        "content": "Serving {city} for over {years} years with {review_count}+ five-star reviews.",
        "block_type": "trust_statement", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Review count and years must be accurate and current.",
        "quality_score": 0.88,
        "variables": ["{city}", "{years}", "{review_count}"],
    }),
    _parse_message_block({
        "id": "msg-trust-002",
        "content": "Trusted by {client_count}+ businesses to deliver measurable results.",
        "block_type": "trust_statement", "archetype_tags": ["professional-services", "saas"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Client count must be verifiable.",
        "quality_score": 0.85,
        "variables": ["{client_count}"],
    }),
    _parse_message_block({
        "id": "msg-trust-003",
        "content": "Licensed, bonded, and insured for your protection.",
        "block_type": "trust_statement", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads"],
        "compliance_notes": "Only use if the business actually holds current license, bond, and insurance.",
        "quality_score": 0.82,
    }),
    _parse_message_block({
        "id": "msg-trust-004",
        "content": "{review_count}+ happy customers and counting.",
        "block_type": "trust_statement",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website", "social", "email"],
        "compliance_notes": "Customer count must be accurate.",
        "quality_score": 0.78,
        "variables": ["{review_count}"],
    }),
    # --- Guarantee blocks (5-7) ---
    _parse_message_block({
        "id": "msg-guarantee-001",
        "content": "100% Satisfaction Guarantee — If you're not happy, we'll make it right.",
        "block_type": "guarantee", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Guarantee must be honored as stated.",
        "quality_score": 0.86,
    }),
    _parse_message_block({
        "id": "msg-guarantee-002",
        "content": "30-Day Money-Back Guarantee — No questions asked.",
        "block_type": "guarantee", "archetype_tags": ["ecommerce", "saas"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Refund window must match actual policy. 'No questions asked' means no conditions on refund.",
        "quality_score": 0.88,
    }),
    _parse_message_block({
        "id": "msg-guarantee-003",
        "content": "Free revisions until you're satisfied.",
        "block_type": "guarantee", "archetype_tags": ["professional-services", "creator"],
        "channel_tags": ["website", "email"],
        "compliance_notes": "Define what 'revisions' covers in the service agreement.",
        "quality_score": 0.80,
    }),
    # --- Urgency blocks (8-10) ---
    _parse_message_block({
        "id": "msg-urgency-001",
        "content": "Limited availability — book your spot before we're fully scheduled.",
        "block_type": "urgency", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Only use when capacity is genuinely limited.",
        "quality_score": 0.82,
    }),
    _parse_message_block({
        "id": "msg-urgency-002",
        "content": "Offer ends {date}. Don't miss out.",
        "block_type": "urgency",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website", "ads", "email", "social"],
        "compliance_notes": "Date must be accurate. Do not use evergreen fake deadlines.",
        "quality_score": 0.84,
        "variables": ["{date}"],
    }),
    _parse_message_block({
        "id": "msg-urgency-003",
        "content": "Only {count} spots remaining this month.",
        "block_type": "urgency", "archetype_tags": ["professional-services", "creator"],
        "channel_tags": ["website", "email"],
        "compliance_notes": "Count must reflect actual remaining capacity. FTC prohibits false scarcity.",
        "quality_score": 0.80,
        "variables": ["{count}"],
    }),
    # --- Social proof blocks (11-13) ---
    _parse_message_block({
        "id": "msg-social-001",
        "content": "Rated {rating}/5 on Google with {review_count} reviews.",
        "block_type": "social_proof",
        "archetype_tags": ["local-service", "ecommerce", "professional-services",
                           "multi-location", "creator", "saas"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Rating and review count must be current. Update at least monthly.",
        "quality_score": 0.90,
        "variables": ["{rating}", "{review_count}"],
    }),
    _parse_message_block({
        "id": "msg-social-002",
        "content": "Featured in {publication} as a top {industry} provider.",
        "block_type": "social_proof", "archetype_tags": ["professional-services", "saas"],
        "channel_tags": ["website", "email"],
        "compliance_notes": "Must have verifiable publication mention. Include date of feature.",
        "quality_score": 0.86,
        "variables": ["{publication}", "{industry}"],
    }),
    _parse_message_block({
        "id": "msg-social-003",
        "content": "Join {subscriber_count}+ professionals who trust our insights.",
        "block_type": "social_proof",
        "archetype_tags": ["saas", "creator", "professional-services"],
        "channel_tags": ["website", "email", "social"],
        "compliance_notes": "Subscriber count must be accurate.",
        "quality_score": 0.82,
        "variables": ["{subscriber_count}"],
    }),
    # --- Value prop blocks (14-15) ---
    _parse_message_block({
        "id": "msg-value-001",
        "content": "Same-day service available for emergencies.",
        "block_type": "value_prop", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads"],
        "compliance_notes": "Only use if the business actually offers same-day emergency service.",
        "quality_score": 0.85,
    }),
    _parse_message_block({
        "id": "msg-value-002",
        "content": "No hidden fees. The price we quote is the price you pay.",
        "block_type": "value_prop", "archetype_tags": ["local-service"],
        "channel_tags": ["website", "ads", "email"],
        "compliance_notes": "Pricing transparency claim must be accurate. No surprise charges allowed.",
        "quality_score": 0.87,
    }),
]


# ============================================================================
# Public API — Loading
# ============================================================================


def load_default_library() -> Dict[str, Any]:
    """Return the default creative library as a plain dict.

    Attempts to load from YAML data files first.  Falls back to the
    hardcoded in-memory defaults if YAML loading is unavailable.
    """
    yaml_ctas_path = os.path.join(_DATA_DIR, "default_ctas.yaml")
    yaml_offers_path = os.path.join(_DATA_DIR, "default_offers.yaml")
    yaml_blocks_path = os.path.join(_DATA_DIR, "default_message_blocks.yaml")

    ctas: List[Dict[str, Any]] = []
    offers: List[Dict[str, Any]] = []
    message_blocks: List[Dict[str, Any]] = []

    # Try YAML first, fall back to hardcoded defaults
    try:
        ctas_data = _load_yaml_file(yaml_ctas_path)
        offers_data = _load_yaml_file(yaml_offers_path)
        blocks_data = _load_yaml_file(yaml_blocks_path)

        ctas = [_parse_cta(c) for c in ctas_data.get("ctas", [])]
        offers = [_parse_offer(o) for o in offers_data.get("offers", [])]
        message_blocks = [
            _parse_message_block(m) for m in blocks_data.get("message_blocks", [])
        ]
    except (RuntimeError, OSError):
        # YAML unavailable or files missing — use hardcoded defaults
        ctas = copy.deepcopy(_DEFAULT_CTAS)
        offers = copy.deepcopy(_DEFAULT_OFFERS)
        message_blocks = copy.deepcopy(_DEFAULT_MESSAGE_BLOCKS)

    # If YAML files were empty or partially loaded, backfill from hardcoded
    if not ctas:
        ctas = copy.deepcopy(_DEFAULT_CTAS)
    if not offers:
        offers = copy.deepcopy(_DEFAULT_OFFERS)
    if not message_blocks:
        message_blocks = copy.deepcopy(_DEFAULT_MESSAGE_BLOCKS)

    return {
        "ctas": ctas,
        "offers": offers,
        "message_blocks": message_blocks,
        "business_id": None,
        "last_updated": None,
    }


def load_library_from_yaml(file_path: str) -> Dict[str, Any]:
    """Load a YAML file containing library entries and return as a dict.

    Expected YAML structure::

        ctas:
          - text: "Call Now"
            archetype_tags: ["local-service"]
            channel_tags: ["website", "ads"]
            intent: "call"
            ...
        offers:
          - name: "Free Estimate"
            ...
        message_blocks:
          - content: "Trusted by ..."
            ...

    Parameters
    ----------
    file_path:
        Path to the YAML file.

    Returns
    -------
    dict:
        A CreativeLibrary-shaped dict with ``ctas``, ``offers``, and
        ``message_blocks`` lists.

    Raises
    ------
    RuntimeError:
        If PyYAML is not installed.
    FileNotFoundError:
        If *file_path* does not exist.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Library YAML file not found: {file_path}")

    data = _load_yaml_file(file_path)

    ctas = [_parse_cta(c) for c in data.get("ctas", [])]
    offers = [_parse_offer(o) for o in data.get("offers", [])]
    message_blocks = [
        _parse_message_block(m) for m in data.get("message_blocks", [])
    ]

    return {
        "ctas": ctas,
        "offers": offers,
        "message_blocks": message_blocks,
        "business_id": data.get("business_id"),
        "last_updated": data.get("last_updated"),
    }


# ============================================================================
# Public API — Merging
# ============================================================================


def merge_libraries(
    default_lib: Dict[str, Any],
    custom_lib: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge a custom (business-specific) library with the default library.

    - Custom entries with the same ``id`` as a default entry **replace** the
      default entry (custom takes precedence).
    - Custom entries with new IDs **extend** the list (they do not replace
      the entire default list).

    Parameters
    ----------
    default_lib:
        The base / default library dict.
    custom_lib:
        A business-specific library dict to merge in.

    Returns
    -------
    dict:
        The merged library dict.
    """
    merged = copy.deepcopy(default_lib)

    for key in ("ctas", "offers", "message_blocks"):
        default_items = merged.get(key, [])
        custom_items = custom_lib.get(key, [])

        if not custom_items:
            continue

        # Index default entries by id for O(1) replacement lookup
        by_id: Dict[str, int] = {}
        for idx, item in enumerate(default_items):
            item_id = item.get("id", "")
            if item_id:
                by_id[item_id] = idx

        for custom_item in custom_items:
            custom_id = custom_item.get("id", "")
            if custom_id and custom_id in by_id:
                # Replace existing entry
                default_items[by_id[custom_id]] = custom_item
            else:
                # Extend with new entry
                default_items.append(custom_item)

        merged[key] = default_items

    # Carry over business_id and last_updated from custom if present
    if custom_lib.get("business_id"):
        merged["business_id"] = custom_lib["business_id"]
    if custom_lib.get("last_updated"):
        merged["last_updated"] = custom_lib["last_updated"]

    return merged


# ============================================================================
# Public API — Querying
# ============================================================================


def _matches_tag(
    entry_tags: List[str],
    query_value: Optional[str],
) -> bool:
    """Return True if the entry's tags match the query value.

    A tag list containing ``"all"`` matches any query.  If *query_value* is
    ``None`` the check is skipped (always matches).
    """
    if query_value is None:
        return True
    if "all" in entry_tags:
        return True
    return query_value in entry_tags


def query_ctas(
    library: Dict[str, Any],
    archetype: Optional[str] = None,
    channel: Optional[str] = None,
    intent: Optional[str] = None,
    urgency_level: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter CTAs from *library* by any combination of criteria.

    Unset criteria (``None``) are not filtered on.  Results are sorted by
    ``quality_score`` descending.
    """
    results: List[Dict[str, Any]] = []

    for cta in library.get("ctas", []):
        if not _matches_tag(cta.get("archetype_tags", []), archetype):
            continue
        if not _matches_tag(cta.get("channel_tags", []), channel):
            continue
        if intent is not None and cta.get("intent") != intent:
            continue
        if urgency_level is not None and cta.get("urgency_level") != urgency_level:
            continue
        results.append(cta)

    results.sort(key=lambda c: c.get("quality_score", 0.0), reverse=True)
    return results


def query_offers(
    library: Dict[str, Any],
    archetype: Optional[str] = None,
    channel: Optional[str] = None,
    offer_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter offers from *library* by any combination of criteria.

    Unset criteria (``None``) are not filtered on.  Results are sorted by
    ``quality_score`` descending.
    """
    results: List[Dict[str, Any]] = []

    for offer in library.get("offers", []):
        if not _matches_tag(offer.get("archetype_tags", []), archetype):
            continue
        if not _matches_tag(offer.get("channel_tags", []), channel):
            continue
        if offer_type is not None and offer.get("offer_type") != offer_type:
            continue
        results.append(offer)

    results.sort(key=lambda o: o.get("quality_score", 0.0), reverse=True)
    return results


def query_message_blocks(
    library: Dict[str, Any],
    archetype: Optional[str] = None,
    channel: Optional[str] = None,
    block_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter message blocks from *library* by any combination of criteria.

    Unset criteria (``None``) are not filtered on.  Results are sorted by
    ``quality_score`` descending.
    """
    results: List[Dict[str, Any]] = []

    for block in library.get("message_blocks", []):
        if not _matches_tag(block.get("archetype_tags", []), archetype):
            continue
        if not _matches_tag(block.get("channel_tags", []), channel):
            continue
        if block_type is not None and block.get("block_type") != block_type:
            continue
        results.append(block)

    results.sort(key=lambda b: b.get("quality_score", 0.0), reverse=True)
    return results


# ============================================================================
# Public API — Variable Filling
# ============================================================================


def fill_variables(
    block: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Replace ``{variable_name}`` placeholders in a message block's content.

    If a variable listed in the block's ``variables`` field is not present in
    *context*, its placeholder is left intact so downstream systems can see
    which variables still need filling.

    Parameters
    ----------
    block:
        A message block dict (or any dict with a ``content`` key).
    context:
        A mapping of variable names to replacement values.  Keys should be
        plain names **without** braces, e.g. ``{"city": "Austin"}``.

    Returns
    -------
    dict:
        A **copy** of *block* with placeholders replaced in ``content``.
    """
    filled = copy.deepcopy(block)
    content = filled.get("content", "")

    if not content:
        return filled

    for key, value in context.items():
        # Support both "{key}" and "key" lookup styles
        placeholder = f"{{{key}}}" if not key.startswith("{") else key
        content = content.replace(placeholder, str(value))

    filled["content"] = content
    return filled


# ============================================================================
# Public API — High-level Orchestration
# ============================================================================


def get_library_for_business(
    business_profile: Dict[str, Any],
    custom_yaml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a complete creative library for a specific business.

    1. Load the default library (YAML with hardcoded fallback).
    2. If *custom_yaml_path* is provided, load the custom library from YAML
       and merge it with the defaults.
    3. Return the merged library.

    The *business_profile* dict is expected to follow the
    ``BusinessProfile`` schema from ``kai.models.business_profile``.  The
    archetype is extracted from ``business_profile.classification.archetype``
    and stored in the library's metadata so downstream callers know which
    archetype defaults are most relevant.

    Parameters
    ----------
    business_profile:
        A dict (or ``BusinessProfile.model_dump()`` output) describing the
        business.
    custom_yaml_path:
        Optional path to a YAML file with business-specific library entries.

    Returns
    -------
    dict:
        A fully assembled creative library dict.
    """
    library = load_default_library()

    # Extract business metadata
    classification = business_profile.get("classification", {})
    if isinstance(classification, dict):
        archetype = classification.get("archetype")
    elif hasattr(classification, "archetype"):
        archetype = classification.archetype
    else:
        archetype = None

    business_id = business_profile.get("id")

    # Merge custom library if provided
    if custom_yaml_path:
        custom_lib = load_library_from_yaml(custom_yaml_path)
        library = merge_libraries(library, custom_lib)

    # Stamp the library with business context
    library["business_id"] = business_id
    if archetype:
        library.setdefault("metadata", {})
        if isinstance(library.get("metadata"), dict):
            library["metadata"]["primary_archetype"] = archetype

    return library

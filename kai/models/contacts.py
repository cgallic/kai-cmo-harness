"""Contact, segment, and lead-scoring models for the Kai Marketing OS.

Canonical internal representation of contacts, segments, segment rules, and
lead scoring.  Every lifecycle action, sequence template, and sequence builder
operates on these models.  The segment system supports both static lists and
dynamic segments with filter rules, plus pre-built segments for common
business archetypes (local-service, ecommerce, professional-services).

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

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
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

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"

else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Enums
# ============================================================================


class LifecycleStage(str, Enum):
    """Where a contact sits in the customer lifecycle."""

    subscriber = "subscriber"
    """Opted in / signed up, no expressed purchase intent."""

    lead = "lead"
    """Expressed interest (form fill, inquiry, chat)."""

    qualified_lead = "qualified_lead"
    """Meets ICP criteria, has budget/need/timeline."""

    prospect = "prospect"
    """Actively in a sales conversation or quote process."""

    customer = "customer"
    """Completed first purchase/service."""

    repeat_customer = "repeat_customer"
    """Completed 2+ purchases/services."""

    advocate = "advocate"
    """Actively refers others or leaves reviews."""

    dormant = "dormant"
    """No engagement in 90+ days."""

    churned = "churned"
    """Explicitly cancelled or 180+ days no activity."""


class ConsentStatus(str, Enum):
    """Marketing consent state for a contact."""

    opted_in = "opted_in"
    """Explicitly opted in to marketing communications."""

    opted_out = "opted_out"
    """Explicitly opted out."""

    transactional_only = "transactional_only"
    """Opted out of marketing but can receive transactional emails."""

    unknown = "unknown"
    """Consent status not determined (treat as opted_out for marketing, allow transactional)."""

    pending = "pending"
    """Double opt-in pending confirmation."""


class ContactSource(str, Enum):
    """How a contact was acquired."""

    website_form = "website_form"
    """Filled out a website form."""

    phone_call = "phone_call"
    """Called the business."""

    chat = "chat"
    """Used website chat."""

    referral = "referral"
    """Referred by another customer."""

    ad_click = "ad_click"
    """Came from a paid ad."""

    organic_search = "organic_search"
    """Found via search engine."""

    social_media = "social_media"
    """Came from social media."""

    email_reply = "email_reply"
    """Replied to an email."""

    walk_in = "walk_in"
    """Walked into physical location."""

    event = "event"
    """Met at event/webinar."""

    manual = "manual"
    """Manually added by operator."""

    import_ = "import"
    """Bulk imported from file/CRM."""

    api = "api"
    """Created via API integration."""

    kaicalls = "kaicalls"
    """Captured by KaiCalls AI receptionist."""


class SegmentOperator(str, Enum):
    """Comparison operators for segment filter rules."""

    equals = "equals"
    not_equals = "not_equals"
    contains = "contains"
    not_contains = "not_contains"
    starts_with = "starts_with"
    ends_with = "ends_with"
    greater_than = "greater_than"
    less_than = "less_than"
    greater_than_or_equal = "greater_than_or_equal"
    less_than_or_equal = "less_than_or_equal"
    in_list = "in_list"
    not_in_list = "not_in_list"
    is_empty = "is_empty"
    is_not_empty = "is_not_empty"
    before = "before"
    after = "after"
    between = "between"
    days_ago_more_than = "days_ago_more_than"
    days_ago_less_than = "days_ago_less_than"


# ============================================================================
# Data Models
# ============================================================================


class Contact(BaseModel):
    """A single contact / lead / customer in the Kai system.

    This is the canonical internal representation, independent of any specific
    lifecycle provider.  Provider-specific IDs are stored in ``provider_ids``.
    """

    id: str = Field(default_factory=lambda: f"con_{uuid.uuid4().hex[:12]}")
    email: str = Field(..., description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    full_name: Optional[str] = Field(None, description="Computed or manually set")
    company: Optional[str] = Field(None, description="For B2B contacts")
    job_title: Optional[str] = Field(None, description="For B2B contacts")

    # Acquisition
    source: str = Field("manual", description="ContactSource value")
    source_detail: Optional[str] = Field(
        None,
        description="Additional source info (e.g. 'Google Ads - Spring HVAC campaign')",
    )
    source_url: Optional[str] = Field(
        None, description="URL where they converted (landing page, form URL)"
    )

    # Timestamps
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp",
    )
    updated_at: Optional[str] = Field(None, description="ISO timestamp")
    first_contacted_at: Optional[str] = Field(
        None, description="When we first reached out"
    )
    last_contacted_at: Optional[str] = Field(
        None, description="When we last sent them a message"
    )
    last_engaged_at: Optional[str] = Field(
        None,
        description="When they last engaged (opened email, clicked, replied, called)",
    )

    # Contact frequency
    contact_frequency_7d: int = Field(0, description="Emails sent in last 7 days")
    contact_frequency_30d: int = Field(0, description="Emails sent in last 30 days")

    # Lifecycle & consent
    lifecycle_stage: str = Field("lead", description="LifecycleStage value")
    consent_status: str = Field("unknown", description="ConsentStatus value")
    opt_in_date: Optional[str] = Field(None, description="ISO timestamp")
    opt_out_date: Optional[str] = Field(None, description="ISO timestamp")
    opt_in_source: Optional[str] = Field(
        None,
        description="Where they opted in (e.g. 'website footer form', 'checkout checkbox')",
    )

    # Grouping
    tags: List[str] = Field(default_factory=list, description="Freeform tags")
    lists: List[str] = Field(
        default_factory=list,
        description="Segment/list IDs this contact belongs to",
    )
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Dynamic fields"
    )

    # Lead scoring
    lead_score: float = Field(0.0, description="Computed lead score (0-100)")
    lead_score_factors: Dict[str, float] = Field(
        default_factory=dict, description="Breakdown of score factors"
    )

    # Revenue & purchases
    total_purchases: int = Field(0)
    total_revenue: float = Field(0.0, description="Lifetime revenue from this contact")
    average_order_value: float = Field(0.0)
    last_purchase_date: Optional[str] = Field(None, description="ISO timestamp")
    last_service_date: Optional[str] = Field(None, description="ISO timestamp")

    # Referral & reviews
    referral_count: int = Field(0, description="How many referrals this contact has made")
    review_status: Optional[str] = Field(
        None, description="none | requested | left_review | declined"
    )
    review_platform: Optional[str] = Field(
        None, description="Where they left a review (google, yelp, etc.)"
    )

    # Operator
    notes: Optional[str] = Field(None, description="Operator notes")
    business_id: Optional[str] = Field(
        None, description="Link to BusinessProfile"
    )

    # Provider mapping
    provider_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of provider -> provider contact ID (e.g. {'loops': 'xxx'})",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SegmentRule(BaseModel):
    """A single filter rule within a segment definition."""

    field: str = Field(
        ...,
        description="Contact field to filter on (e.g. 'lifecycle_stage', 'tags', 'lead_score')",
    )
    operator: str = Field(..., description="SegmentOperator value")
    value: Any = Field(
        None, description="Comparison value (type depends on operator and field)"
    )
    value_type: str = Field(
        "string",
        description="Type hint: 'string', 'number', 'date', 'boolean', 'list'",
    )


class Segment(BaseModel):
    """A contact segment -- either dynamic (rule-based) or static (manual list)."""

    id: str = Field(default_factory=lambda: f"seg_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Human-readable segment name")
    description: Optional[str] = Field(
        None, description="What this segment represents"
    )
    rules: List[SegmentRule] = Field(
        default_factory=list, description="Filter rules (combined via rule_logic)"
    )
    rule_logic: str = Field(
        "and",
        description="'and' (all rules must match) or 'or' (any rule matches)",
    )
    is_dynamic: bool = Field(
        True,
        description="If True, contact list refreshes automatically based on rules",
    )
    static_contact_ids: List[str] = Field(
        default_factory=list,
        description="Manually added contact IDs (for static segments)",
    )
    contact_count: int = Field(0, description="Cached count of matching contacts")
    last_refreshed: Optional[str] = Field(None, description="ISO timestamp")
    archetype: Optional[str] = Field(
        None, description="Which business archetype this segment is designed for"
    )
    created_at: Optional[str] = Field(None, description="ISO timestamp")
    updated_at: Optional[str] = Field(None, description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Pre-built Segments
# ============================================================================


LOCAL_SERVICE_SEGMENTS: List[Dict[str, Any]] = [
    {
        "id": "seg_new_leads",
        "name": "New leads (last 7 days)",
        "description": (
            "Contacts who inquired in the last 7 days and haven't been "
            "converted yet"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["lead", "qualified_lead"],
                "value_type": "list",
            },
            {
                "field": "created_at",
                "operator": "days_ago_less_than",
                "value": 7,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_quoted_not_booked",
        "name": "Quoted but not booked",
        "description": (
            "Contacts who received a quote but haven't booked yet"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "equals",
                "value": "prospect",
                "value_type": "string",
            },
            {
                "field": "custom_fields.quote_sent",
                "operator": "equals",
                "value": True,
                "value_type": "boolean",
            },
            {
                "field": "lifecycle_stage",
                "operator": "not_equals",
                "value": "customer",
                "value_type": "string",
            },
        ],
    },
    {
        "id": "seg_past_customers_90d",
        "name": "Recent customers (last 90 days)",
        "description": (
            "Customers who had service in the last 90 days -- prime for "
            "review requests and referrals"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["customer", "repeat_customer"],
                "value_type": "list",
            },
            {
                "field": "last_service_date",
                "operator": "days_ago_less_than",
                "value": 90,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_past_customers_1yr",
        "name": "Customers from last year",
        "description": (
            "Customers who had service 3-12 months ago -- good for seasonal "
            "reminders and reactivation"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["customer", "repeat_customer"],
                "value_type": "list",
            },
            {
                "field": "last_service_date",
                "operator": "days_ago_more_than",
                "value": 90,
                "value_type": "number",
            },
            {
                "field": "last_service_date",
                "operator": "days_ago_less_than",
                "value": 365,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_dormant_12mo",
        "name": "Dormant 12+ months",
        "description": (
            "Contacts with no engagement in 12+ months -- candidates for "
            "reactivation or list cleanup"
        ),
        "archetype": "local-service",
        "rule_logic": "or",
        "is_dynamic": True,
        "rules": [
            {
                "field": "last_engaged_at",
                "operator": "days_ago_more_than",
                "value": 365,
                "value_type": "number",
            },
            {
                "field": "last_service_date",
                "operator": "days_ago_more_than",
                "value": 365,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_high_value_customers",
        "name": "High-value customers",
        "description": (
            "Customers with high lifetime value -- prioritize for VIP "
            "treatment, referral asks, and retention"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "total_revenue",
                "operator": "greater_than",
                "value": 1000,
                "value_type": "number",
            },
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["customer", "repeat_customer"],
                "value_type": "list",
            },
        ],
    },
    {
        "id": "seg_referral_sources",
        "name": "Active referrers",
        "description": (
            "Customers who have referred others -- nurture the relationship "
            "and incentivize more referrals"
        ),
        "archetype": "local-service",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "referral_count",
                "operator": "greater_than",
                "value": 0,
                "value_type": "number",
            },
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["customer", "repeat_customer", "advocate"],
                "value_type": "list",
            },
        ],
    },
]


ECOMMERCE_SEGMENTS: List[Dict[str, Any]] = [
    {
        "id": "seg_new_subscribers",
        "name": "New subscribers (last 14 days)",
        "description": "Subscribers who signed up in the last 14 days",
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "equals",
                "value": "subscriber",
                "value_type": "string",
            },
            {
                "field": "created_at",
                "operator": "days_ago_less_than",
                "value": 14,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_first_purchase",
        "name": "First-time buyers",
        "description": (
            "Customers who have made exactly one purchase -- critical "
            "conversion to repeat"
        ),
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "total_purchases",
                "operator": "equals",
                "value": 1,
                "value_type": "number",
            },
            {
                "field": "lifecycle_stage",
                "operator": "equals",
                "value": "customer",
                "value_type": "string",
            },
        ],
    },
    {
        "id": "seg_repeat_buyers",
        "name": "Repeat buyers (2+ orders)",
        "description": "Customers with two or more purchases",
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "total_purchases",
                "operator": "greater_than_or_equal",
                "value": 2,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_cart_abandoners",
        "name": "Cart abandoners",
        "description": "Contacts who abandoned a cart in the last 7 days",
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "custom_fields.cart_abandoned",
                "operator": "equals",
                "value": True,
                "value_type": "boolean",
            },
            {
                "field": "custom_fields.cart_abandoned_at",
                "operator": "days_ago_less_than",
                "value": 7,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_dormant_90d",
        "name": "Dormant 90+ days",
        "description": "Contacts with no engagement in 90+ days who have not churned",
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "last_engaged_at",
                "operator": "days_ago_more_than",
                "value": 90,
                "value_type": "number",
            },
            {
                "field": "lifecycle_stage",
                "operator": "not_equals",
                "value": "churned",
                "value_type": "string",
            },
        ],
    },
    {
        "id": "seg_vip_customers",
        "name": "VIP customers (top 10% by revenue)",
        "description": (
            "High-value repeat customers who deserve VIP treatment"
        ),
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "total_revenue",
                "operator": "greater_than",
                "value": 500,
                "value_type": "number",
            },
            {
                "field": "total_purchases",
                "operator": "greater_than_or_equal",
                "value": 3,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_browse_abandoners",
        "name": "Browse abandoners",
        "description": "Contacts who browsed recently but never purchased",
        "archetype": "ecommerce",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "custom_fields.last_browse_date",
                "operator": "days_ago_less_than",
                "value": 3,
                "value_type": "number",
            },
            {
                "field": "total_purchases",
                "operator": "equals",
                "value": 0,
                "value_type": "number",
            },
        ],
    },
]


PROFESSIONAL_SERVICES_SEGMENTS: List[Dict[str, Any]] = [
    {
        "id": "seg_active_inquiries",
        "name": "Active inquiries",
        "description": "Leads and qualified leads from the last 30 days",
        "archetype": "professional-services",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["lead", "qualified_lead"],
                "value_type": "list",
            },
            {
                "field": "created_at",
                "operator": "days_ago_less_than",
                "value": 30,
                "value_type": "number",
            },
        ],
    },
    {
        "id": "seg_consultation_scheduled",
        "name": "Consultation scheduled",
        "description": "Prospects with a consultation date set",
        "archetype": "professional-services",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "custom_fields.consultation_date",
                "operator": "is_not_empty",
                "value": None,
                "value_type": "string",
            },
            {
                "field": "lifecycle_stage",
                "operator": "equals",
                "value": "prospect",
                "value_type": "string",
            },
        ],
    },
    {
        "id": "seg_past_clients",
        "name": "Past clients",
        "description": "Customers and repeat customers who have a service date on file",
        "archetype": "professional-services",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "in_list",
                "value": ["customer", "repeat_customer"],
                "value_type": "list",
            },
            {
                "field": "last_service_date",
                "operator": "is_not_empty",
                "value": None,
                "value_type": "string",
            },
        ],
    },
    {
        "id": "seg_nurture_leads",
        "name": "Long-term nurture",
        "description": (
            "Leads who haven't converted after 30 days -- move to "
            "long-term nurture"
        ),
        "archetype": "professional-services",
        "rule_logic": "and",
        "is_dynamic": True,
        "rules": [
            {
                "field": "lifecycle_stage",
                "operator": "equals",
                "value": "lead",
                "value_type": "string",
            },
            {
                "field": "created_at",
                "operator": "days_ago_more_than",
                "value": 30,
                "value_type": "number",
            },
        ],
    },
]


# ============================================================================
# Scoring Configuration
# ============================================================================


DEFAULT_SCORING_CONFIG: Dict[str, Any] = {
    "recency_weight": 1.0,
    "frequency_weight": 1.0,
    "engagement_weight": 1.0,
    "fit_weight": 1.0,
    "value_weight": 1.0,
    "recency_thresholds": {"hot": 7, "warm": 14, "cool": 30, "cold": 90},
    "frequency_thresholds": {"high": 5, "medium": 3, "low": 1},
    "value_thresholds": {"high": 1000, "medium": 500, "low": 100},
}


# ============================================================================
# LeadScorer
# ============================================================================


class LeadScorer:
    """Score contacts on five dimensions: recency, frequency, engagement, fit, value.

    Each factor yields 0-20 points.  Total score is clamped to 0-100.
    """

    def __init__(self, scoring_config: Optional[Dict[str, float]] = None) -> None:
        self.config: Dict[str, Any] = scoring_config or copy.deepcopy(
            DEFAULT_SCORING_CONFIG
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a lead score for *contact*.

        Returns::

            {
                "total_score": float,  # 0-100
                "factors": {
                    "recency": float,
                    "frequency": float,
                    "engagement": float,
                    "fit": float,
                    "value": float,
                }
            }
        """
        recency = self._score_recency(contact) * self.config.get("recency_weight", 1.0)
        frequency = self._score_frequency(contact) * self.config.get("frequency_weight", 1.0)
        engagement = self._score_engagement(contact) * self.config.get("engagement_weight", 1.0)
        fit = self._score_fit(contact) * self.config.get("fit_weight", 1.0)
        value = self._score_value(contact) * self.config.get("value_weight", 1.0)

        # Clamp each weighted factor to [0, 20]
        recency = max(0.0, min(20.0, recency))
        frequency = max(0.0, min(20.0, frequency))
        engagement = max(0.0, min(20.0, engagement))
        fit = max(0.0, min(20.0, fit))
        value = max(0.0, min(20.0, value))

        total = max(0.0, min(100.0, recency + frequency + engagement + fit + value))

        return {
            "total_score": round(total, 2),
            "factors": {
                "recency": round(recency, 2),
                "frequency": round(frequency, 2),
                "engagement": round(engagement, 2),
                "fit": round(fit, 2),
                "value": round(value, 2),
            },
        }

    # ------------------------------------------------------------------
    # Factor scorers (each returns 0-20 before weighting)
    # ------------------------------------------------------------------

    def _score_recency(self, contact: Dict[str, Any]) -> float:
        """Recency: how recently the contact was created or last engaged."""
        thresholds = self.config.get(
            "recency_thresholds", {"hot": 7, "warm": 14, "cool": 30, "cold": 90}
        )

        # Pick the most recent date available
        date_str = contact.get("last_engaged_at") or contact.get("created_at")
        if not date_str:
            return 0.0

        days = calculate_days_since(date_str)
        if days < 0:
            # Future date -- treat as very recent
            return 20.0

        if days <= thresholds.get("hot", 7):
            return 20.0
        if days <= thresholds.get("warm", 14):
            return 15.0
        if days <= thresholds.get("cool", 30):
            return 10.0
        if days <= thresholds.get("cold", 90):
            return 5.0
        return 0.0

    def _score_frequency(self, contact: Dict[str, Any]) -> float:
        """Frequency: how often they engage (based on contact_frequency_30d)."""
        thresholds = self.config.get(
            "frequency_thresholds", {"high": 5, "medium": 3, "low": 1}
        )
        freq = contact.get("contact_frequency_30d", 0)

        if freq >= thresholds.get("high", 5):
            return 20.0
        if freq >= thresholds.get("medium", 3):
            return 15.0
        if freq >= thresholds.get("low", 1):
            return 10.0
        return 0.0

    def _score_engagement(self, contact: Dict[str, Any]) -> float:
        """Engagement: depth of engagement signals."""
        score = 0.0
        custom = contact.get("custom_fields", {})

        # Email engagement signals
        if custom.get("has_replied") or custom.get("email_replied"):
            score += 10.0
        if custom.get("has_opened") or custom.get("email_opened"):
            score += 5.0
        if custom.get("has_clicked") or custom.get("email_clicked"):
            score += 5.0

        # High-value source signals
        source = contact.get("source", "")
        if source == "referral":
            score += 5.0
        elif source == "phone_call":
            score += 5.0

        return min(20.0, score)

    def _score_fit(self, contact: Dict[str, Any]) -> float:
        """Fit: how well they match the ideal customer profile."""
        score = 0.0
        stage = contact.get("lifecycle_stage", "")

        if stage == "qualified_lead":
            score += 20.0
        elif stage == "lead":
            score += 10.0
        elif stage == "subscriber":
            score += 5.0

        # Bonus signals (capped so total stays <= 20)
        if contact.get("phone"):
            score += 5.0
        if contact.get("company"):
            score += 5.0

        return min(20.0, score)

    def _score_value(self, contact: Dict[str, Any]) -> float:
        """Value: monetary potential based on revenue history."""
        thresholds = self.config.get(
            "value_thresholds", {"high": 1000, "medium": 500, "low": 100}
        )
        revenue = contact.get("total_revenue", 0.0)

        if revenue > thresholds.get("high", 1000):
            return 20.0
        if revenue > thresholds.get("medium", 500):
            return 15.0
        if revenue > thresholds.get("low", 100):
            return 10.0
        if revenue > 0:
            return 5.0
        return 0.0


# ============================================================================
# SegmentEngine
# ============================================================================


class SegmentEngine:
    """Evaluate contacts against segment rules.

    Supports both ``and`` (all rules match) and ``or`` (any rule matches)
    logic, dynamic segments with filter rules, and static segments with
    explicit contact ID lists.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_contact(
        self, contact: Dict[str, Any], segment: Dict[str, Any]
    ) -> bool:
        """Return True if *contact* matches *segment*'s rules.

        For static segments (``is_dynamic`` is False), checks whether the
        contact's ``id`` is in ``static_contact_ids``.  For dynamic segments,
        evaluates each rule against the contact and combines results using
        ``rule_logic``.
        """
        # Static segment shortcut
        if not segment.get("is_dynamic", True):
            static_ids = segment.get("static_contact_ids", [])
            return contact.get("id", "") in static_ids

        rules = segment.get("rules", [])
        if not rules:
            # No rules means the segment matches everything
            return True

        logic = segment.get("rule_logic", "and")

        if logic == "or":
            return any(self._evaluate_rule(contact, rule) for rule in rules)
        else:
            # Default to "and"
            return all(self._evaluate_rule(contact, rule) for rule in rules)

    def filter_contacts(
        self,
        contacts: List[Dict[str, Any]],
        segment: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Return the subset of *contacts* that match *segment*."""
        return [c for c in contacts if self.evaluate_contact(c, segment)]

    def refresh_segment_count(
        self,
        segment: Dict[str, Any],
        contacts: List[Dict[str, Any]],
    ) -> int:
        """Count matching contacts, update segment metadata, and return count."""
        matching = self.filter_contacts(contacts, segment)
        count = len(matching)
        segment["contact_count"] = count
        segment["last_refreshed"] = datetime.now(timezone.utc).isoformat()
        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evaluate_rule(
        self, contact: Dict[str, Any], rule: Dict[str, Any]
    ) -> bool:
        """Evaluate a single rule against a contact."""
        field_path = rule.get("field", "")
        operator = rule.get("operator", "")
        rule_value = rule.get("value")
        value_type = rule.get("value_type", "string")

        contact_value = self._get_nested_field(contact, field_path)

        # --- Emptiness operators (work regardless of value) ---
        if operator == "is_empty":
            return self._is_empty(contact_value)
        if operator == "is_not_empty":
            return not self._is_empty(contact_value)

        # If contact_value is None for non-emptiness operators, rule does not match
        if contact_value is None:
            return False

        # --- Type coercion ---
        contact_value = self._coerce(contact_value, value_type)
        rule_value = self._coerce(rule_value, value_type)

        # --- Equality ---
        if operator == "equals":
            return contact_value == rule_value

        if operator == "not_equals":
            return contact_value != rule_value

        # --- String operators ---
        if operator == "contains":
            if isinstance(contact_value, (list, tuple)):
                return rule_value in contact_value
            return str(rule_value) in str(contact_value)

        if operator == "not_contains":
            if isinstance(contact_value, (list, tuple)):
                return rule_value not in contact_value
            return str(rule_value) not in str(contact_value)

        if operator == "starts_with":
            return str(contact_value).startswith(str(rule_value))

        if operator == "ends_with":
            return str(contact_value).endswith(str(rule_value))

        # --- Numeric comparison ---
        if operator == "greater_than":
            return self._to_number(contact_value) > self._to_number(rule_value)

        if operator == "less_than":
            return self._to_number(contact_value) < self._to_number(rule_value)

        if operator == "greater_than_or_equal":
            return self._to_number(contact_value) >= self._to_number(rule_value)

        if operator == "less_than_or_equal":
            return self._to_number(contact_value) <= self._to_number(rule_value)

        # --- List membership ---
        if operator == "in_list":
            if isinstance(rule_value, (list, tuple)):
                return contact_value in rule_value
            return False

        if operator == "not_in_list":
            if isinstance(rule_value, (list, tuple)):
                return contact_value not in rule_value
            return True

        # --- Date comparison ---
        if operator == "before":
            return self._parse_date(contact_value) < self._parse_date(rule_value)

        if operator == "after":
            return self._parse_date(contact_value) > self._parse_date(rule_value)

        if operator == "between":
            # rule_value should be [start, end] as ISO strings or numbers
            if isinstance(rule_value, (list, tuple)) and len(rule_value) == 2:
                cv = self._to_number(contact_value)
                low = self._to_number(rule_value[0])
                high = self._to_number(rule_value[1])
                return low <= cv <= high
            return False

        # --- Days-ago operators ---
        if operator == "days_ago_more_than":
            days = calculate_days_since(str(contact_value))
            return days > self._to_number(rule_value)

        if operator == "days_ago_less_than":
            days = calculate_days_since(str(contact_value))
            return days < self._to_number(rule_value)

        # Unknown operator -- fail closed
        return False

    def _get_nested_field(self, obj: Dict[str, Any], field_path: str) -> Any:
        """Resolve a dot-notated field path.

        ``"custom_fields.quote_sent"`` resolves to
        ``obj["custom_fields"]["quote_sent"]``.  Returns ``None`` if any
        segment of the path is missing.
        """
        parts = field_path.split(".")
        current: Any = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    # ------------------------------------------------------------------
    # Type helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """Check if a value is None, empty string, or empty collection."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
            return True
        return False

    @staticmethod
    def _coerce(value: Any, value_type: str) -> Any:
        """Best-effort coercion to the declared value_type."""
        if value is None:
            return value

        if value_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return value

        if value_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)

        # "string", "date", "list" -- return as-is
        return value

    @staticmethod
    def _to_number(value: Any) -> float:
        """Convert a value to float for numeric comparison."""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _parse_date(value: Any) -> datetime:
        """Parse an ISO date string into a datetime for comparison."""
        if isinstance(value, datetime):
            return value
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return dt
        except (ValueError, TypeError):
            return datetime.min


# ============================================================================
# Module-level helper functions
# ============================================================================


def generate_contact_id() -> str:
    """Generate a unique contact ID with ``con_`` prefix."""
    return f"con_{uuid.uuid4().hex[:12]}"


def generate_segment_id() -> str:
    """Generate a unique segment ID with ``seg_`` prefix."""
    return f"seg_{uuid.uuid4().hex[:12]}"


def get_prebuilt_segments(archetype: str) -> List[Dict[str, Any]]:
    """Return pre-built segment definitions for the given business archetype.

    Recognized archetypes:
    - ``"local-service"`` -- window cleaners, HVAC, plumbers, etc.
    - ``"ecommerce"`` -- online stores
    - ``"professional-services"`` -- law firms, consultants, agencies

    Unknown archetypes default to ``LOCAL_SERVICE_SEGMENTS`` (most common).
    """
    mapping: Dict[str, List[Dict[str, Any]]] = {
        "local-service": LOCAL_SERVICE_SEGMENTS,
        "ecommerce": ECOMMERCE_SEGMENTS,
        "professional-services": PROFESSIONAL_SERVICES_SEGMENTS,
    }
    return copy.deepcopy(mapping.get(archetype, LOCAL_SERVICE_SEGMENTS))


def calculate_days_since(date_str: str) -> int:
    """Return the number of whole days between *date_str* (ISO format) and now.

    Returns ``0`` if *date_str* cannot be parsed.
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Ensure timezone-aware comparison
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = now - dt
        return delta.days
    except (ValueError, TypeError, AttributeError):
        return 0


def merge_contacts(
    contact_a: Dict[str, Any], contact_b: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge two contact records into one.

    Strategy:
    - For scalar fields: prefer non-None values; when both are set, prefer
      ``contact_a`` (treated as the "primary" record).
    - ``tags`` and ``lists``: union of both, deduplicated.
    - ``custom_fields``, ``provider_ids``, ``metadata``: shallow merge with
      ``contact_a`` values winning on key conflicts.
    - ``lead_score_factors``: merge with ``contact_a`` winning on conflicts.
    - Numeric accumulators (``total_purchases``, ``total_revenue``,
      ``referral_count``): summed.
    - ``average_order_value``: recomputed from merged totals.
    - Timestamps: keep the earliest ``created_at`` and latest activity dates.
    """
    merged: Dict[str, Any] = {}

    # Collect all keys from both records
    all_keys = set(contact_a.keys()) | set(contact_b.keys())

    # Keys that should be summed
    sum_keys = {"total_purchases", "total_revenue", "referral_count"}

    # Keys that should be merged as lists (union, deduplicated)
    list_union_keys = {"tags", "lists"}

    # Keys that should be shallow-merged as dicts (a wins on conflict)
    dict_merge_keys = {
        "custom_fields",
        "provider_ids",
        "metadata",
        "lead_score_factors",
    }

    # Date keys where we want the earliest value
    earliest_date_keys = {"created_at"}

    # Date keys where we want the latest value
    latest_date_keys = {
        "last_contacted_at",
        "last_engaged_at",
        "last_purchase_date",
        "last_service_date",
        "updated_at",
    }

    for key in all_keys:
        val_a = contact_a.get(key)
        val_b = contact_b.get(key)

        if key in sum_keys:
            merged[key] = (val_a or 0) + (val_b or 0)

        elif key in list_union_keys:
            combined = list(val_a or []) + list(val_b or [])
            # Deduplicate while preserving order
            seen: set = set()
            deduped: List[Any] = []
            for item in combined:
                if item not in seen:
                    seen.add(item)
                    deduped.append(item)
            merged[key] = deduped

        elif key in dict_merge_keys:
            base = dict(val_b or {})
            base.update(val_a or {})
            merged[key] = base

        elif key in earliest_date_keys:
            merged[key] = _pick_date(val_a, val_b, earliest=True)

        elif key in latest_date_keys:
            merged[key] = _pick_date(val_a, val_b, earliest=False)

        else:
            # Scalar: prefer A's non-None value
            merged[key] = val_a if val_a is not None else val_b

    # Recompute average_order_value from merged totals
    total_purchases = merged.get("total_purchases", 0)
    total_revenue = merged.get("total_revenue", 0.0)
    if total_purchases > 0:
        merged["average_order_value"] = round(total_revenue / total_purchases, 2)
    else:
        merged["average_order_value"] = 0.0

    # Sum contact frequencies
    merged["contact_frequency_7d"] = (
        contact_a.get("contact_frequency_7d", 0)
        + contact_b.get("contact_frequency_7d", 0)
    )
    merged["contact_frequency_30d"] = (
        contact_a.get("contact_frequency_30d", 0)
        + contact_b.get("contact_frequency_30d", 0)
    )

    return merged


# ============================================================================
# Internal helpers
# ============================================================================


def _pick_date(
    date_a: Optional[str],
    date_b: Optional[str],
    *,
    earliest: bool = True,
) -> Optional[str]:
    """Return the earliest (or latest) of two ISO date strings.

    Returns ``None`` only when both inputs are ``None``.
    """
    if date_a is None:
        return date_b
    if date_b is None:
        return date_a
    try:
        dt_a = datetime.fromisoformat(date_a.replace("Z", "+00:00"))
        dt_b = datetime.fromisoformat(date_b.replace("Z", "+00:00"))
        if earliest:
            return date_a if dt_a <= dt_b else date_b
        return date_a if dt_a >= dt_b else date_b
    except (ValueError, TypeError):
        return date_a

"""Canonical proposal data models for the Kai Marketing OS.

This module defines the ProposedAction and ProposalBundle schemas that
translate audit findings into concrete, executable marketing actions.
ProposedAction is the central currency of the entire proposal layer --
every downstream system (bundling, ranking, creative generation,
execution, approval) consumes these objects.

Design principles
-----------------
1. **Finding-to-action bridge.**  Every ProposedAction links back to the
   AuditFinding that generated it via ``source_finding_id``.
2. **Risk-aware.**  Actions carry a risk tier that determines approval
   requirements.  Higher-risk actions need explicit operator approval.
3. **Composable.**  ProposalBundles group related actions into coherent
   plans that operators can review and approve as a unit.
4. **Self-contained.**  This module does **not** import anything from
   ``kai/runtime/``.  It is standalone in ``kai/models/``.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

Migration note
--------------
The older prototype at ``kai/runtime/actions.py`` uses stdlib dataclasses +
``SerializableModel``.  The two can coexist during the migration period.
This module does **not** import anything from ``kai/runtime/``.
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


class ActionType(str, Enum):
    """The kind of marketing action to execute.

    Each value maps to a distinct execution pathway in the downstream
    action runner.
    """

    WEBSITE_UPDATE = "website_update"           # Modify existing website content, layout, or elements
    SOCIAL_POST = "social_post"                 # Create and publish social media content
    AD_CAMPAIGN = "ad_campaign"                 # Create, modify, or launch a paid advertising campaign
    EMAIL_SEQUENCE = "email_sequence"           # Create or modify an automated email sequence
    REVIEW_REQUEST = "review_request"           # Initiate a review solicitation campaign
    GBP_UPDATE = "gbp_update"                   # Update Google Business Profile listing
    SEO_FIX = "seo_fix"                         # Technical or on-page SEO correction
    ANALYTICS_FIX = "analytics_fix"             # Fix or set up tracking, attribution, or analytics
    CONTENT_CREATION = "content_creation"       # Create a new content asset (blog, case study, video script, etc.)
    FOLLOW_UP_SEQUENCE = "follow_up_sequence"   # Create or modify a lead follow-up workflow
    REPUTATION_ACTION = "reputation_action"     # Respond to reviews, manage reputation signals
    KAICALLS_SETUP = "kaicalls_setup"           # Set up or configure KaiCalls AI receptionist for phone lead capture


class RiskTier(str, Enum):
    """How risky is this action?

    Risk tier determines the approval gate.  Higher tiers require
    explicit human sign-off before execution.
    """

    AUTO = "auto"           # No spend, no public-facing change (e.g., internal analytics fix, tracking setup)
    LOW = "low"             # Small copy update, internal change, metadata update (e.g., update meta description, fix broken link)
    MEDIUM = "medium"       # New content publishing, small spend (e.g., publish blog post, launch $10/day ad test)
    HIGH = "high"           # Campaign launch, significant spend (e.g., launch full ad campaign, major website restructure)
    CRITICAL = "critical"   # Brand-level changes, large spend (e.g., rebrand elements, $1000+ campaign launch, homepage redesign)


class ApprovalRequirement(str, Enum):
    """What level of human review is needed before execution?"""

    AUTO_APPROVE = "auto_approve"           # System can execute without human review
    OPERATOR_REVIEW = "operator_review"     # Operator should review but can batch-approve
    OPERATOR_APPROVAL = "operator_approval" # Operator must explicitly approve this specific action


# Valid status values for ProposedAction
_VALID_ACTION_STATUSES = frozenset({
    "proposed",
    "approved",
    "rejected",
    "in_progress",
    "completed",
    "cancelled",
})

# Valid bundle type values for ProposalBundle
_VALID_BUNDLE_TYPES = frozenset({
    "7_day",
    "30_day",
    "campaign",
    "monthly_operating",
})


# ============================================================================
# Data Models
# ============================================================================


class ProposedAction(BaseModel):
    """A single concrete, executable marketing action.

    Every ProposedAction links back to the ``AuditFinding`` that
    generated it via ``source_finding_id``.  Downstream systems --
    bundling, ranking, creative generation, execution, approval --
    consume this model directly.

    A ``ProposedAction`` can be instantiated with just
    ``source_finding_id``, ``action_type``, ``title``, and
    ``description``.  Everything else has sensible defaults.
    """

    id: str = Field(default_factory=lambda: generate_action_id())
    source_finding_id: str                                                  # Links back to the AuditFinding that generated this action
    action_type: str                                                        # ActionType enum value
    channel: str = "website"                                                # Target channel: website, social, paid_media, email, sms, phone, gbp, analytics, offline
    title: str                                                              # Short operator-readable title
    description: str                                                        # 2-3 sentence explanation of what this action entails
    reason: str = ""                                                        # Why this action matters for the business
    business_impact: str = ""                                               # Narrative description of expected business impact
    expected_outcome: str = ""                                              # Measurable expected outcome
    risk_tier: str = RiskTier.LOW.value                                     # RiskTier enum value
    approval_requirement: str = ApprovalRequirement.OPERATOR_REVIEW.value   # ApprovalRequirement enum value
    suggested_payload: Dict[str, Any] = Field(default_factory=dict)         # Content, configuration, or parameters needed for execution
    estimated_effort: Optional[str] = None                                  # Human-readable effort estimate, e.g. "30 minutes", "2 hours"
    estimated_effort_hours: Optional[float] = None                          # Numeric effort in hours for capacity math
    estimated_cost: Optional[float] = 0.0                                   # Estimated USD cost (ad spend, tool subscription, etc.)
    priority_score: float = 50.0                                            # Computed priority score (0-100)
    archetype_relevance: List[str] = Field(default_factory=list)            # Which archetypes this action is especially relevant for
    tags: List[str] = Field(default_factory=list)                           # Freeform tags for filtering and grouping
    depends_on: List[str] = Field(default_factory=list)                     # List of other ProposedAction IDs that must complete first
    status: str = "proposed"                                                # proposed, approved, rejected, in_progress, completed, cancelled
    created_at: Optional[str] = None                                        # ISO timestamp
    metadata: Dict[str, Any] = Field(default_factory=dict)                  # Catch-all for extra data


class ProposalBundle(BaseModel):
    """A coherent group of related ProposedActions.

    Bundles let operators review and approve a set of related actions
    as a unit rather than dealing with dozens of individual actions.
    Each bundle targets a specific time horizon or campaign goal.
    """

    id: str = Field(default_factory=lambda: generate_bundle_id())
    business_id: str                                                            # Links to the BusinessProfile this bundle is for
    bundle_type: str                                                            # One of: 7_day, 30_day, campaign, monthly_operating
    bundle_name: str                                                            # Human-readable name, e.g. "Week 1 Quick Wins"
    actions: List[ProposedAction] = Field(default_factory=list)                 # The actions in this bundle
    total_estimated_cost: float = 0.0                                           # Sum of all action estimated_cost values
    total_estimated_effort_hours: float = 0.0                                   # Sum of all action estimated_effort_hours values
    executive_summary: str = ""                                                 # 3-5 sentence summary of what this bundle accomplishes
    expected_outcomes: List[str] = Field(default_factory=list)                  # List of measurable expected outcomes
    weekly_milestones: Dict[str, List[str]] = Field(default_factory=dict)       # Week number to list of milestone descriptions (for 30-day bundles)
    created_at: Optional[str] = None                                            # ISO timestamp
    metadata: Dict[str, Any] = Field(default_factory=dict)                      # Catch-all


# ============================================================================
# ID Generation
# ============================================================================


def generate_action_id() -> str:
    """Generate a unique action ID.

    Format: ``act_{12-hex-chars}``

    Returns
    -------
    str
        A unique action identifier like ``act_a1b2c3d4e5f6``.
    """
    return f"act_{uuid.uuid4().hex[:12]}"


def generate_bundle_id() -> str:
    """Generate a unique bundle ID.

    Format: ``bnd_{12-hex-chars}``

    Returns
    -------
    str
        A unique bundle identifier like ``bnd_a1b2c3d4e5f6``.
    """
    return f"bnd_{uuid.uuid4().hex[:12]}"


# ============================================================================
# Generation Rule Functions
# ============================================================================


def assign_risk_tier(
    action_type: str,
    estimated_cost: float,
    channel: str,
    is_public_facing: bool,
) -> str:
    """Assign a risk tier to an action based on its attributes.

    The risk tier determines the approval gate.  This function
    encodes the business rules that map action characteristics to
    the appropriate level of human oversight.

    Parameters
    ----------
    action_type:
        ActionType enum value (e.g., "website_update", "ad_campaign").
    estimated_cost:
        Estimated USD cost of this action (ad spend, tool cost, etc.).
    channel:
        Target channel (e.g., "website", "paid_media", "analytics").
    is_public_facing:
        Whether this action produces externally visible changes.

    Returns
    -------
    str
        A RiskTier enum value.
    """
    # Rule 1: Zero-cost, internal-only actions are safe to auto-execute.
    # Examples: setting up analytics tags, configuring internal tracking,
    # adding UTM parameters to internal documentation.
    if estimated_cost == 0 and not is_public_facing:
        return RiskTier.AUTO.value

    # Rule 2: Zero-cost technical fixes that are public-facing but low-impact.
    # SEO fixes (meta tag updates, canonical corrections) and analytics fixes
    # (adding tracking pixels, fixing tag manager configs) are routine and
    # rarely cause visible harm even if imperfect.
    if (
        estimated_cost == 0
        and is_public_facing
        and action_type in (ActionType.SEO_FIX.value, ActionType.ANALYTICS_FIX.value)
    ):
        return RiskTier.LOW.value

    # Rule 3: Website updates on the homepage are high risk because the
    # homepage is the highest-traffic page and most visible brand surface.
    # Inner page updates are medium risk (visible but lower traffic), and
    # non-public website changes (e.g., backend config) are low risk.
    if action_type == ActionType.WEBSITE_UPDATE.value and channel == "website":
        if is_public_facing:
            # Homepage changes are high risk -- the homepage is the #1 brand
            # impression and drives the most traffic.  Getting it wrong is
            # expensive.  We can't detect "homepage" vs "inner page" from
            # the type/channel alone, so we use cost as a proxy: higher-cost
            # website updates tend to be more significant structural changes.
            if estimated_cost > 50:
                return RiskTier.HIGH.value
            # Non-trivial inner page updates with some cost attached
            if estimated_cost > 0:
                return RiskTier.MEDIUM.value
            # Free public-facing website updates (copy tweaks, metadata)
            return RiskTier.LOW.value
        # Internal website changes (not public-facing) are low risk
        return RiskTier.LOW.value

    # Rule 4: Ad campaigns with significant spend are high risk.
    # Ad campaigns burn real money, and mistakes are expensive to correct
    # because platforms may have already served impressions by the time
    # the operator notices.  Threshold is $100 because smaller test budgets
    # ($10-50/day) are acceptable at medium risk.
    if action_type == ActionType.AD_CAMPAIGN.value and estimated_cost > 100:
        return RiskTier.HIGH.value

    # Rule 5: Very large spend (>$500) is critical regardless of action type.
    # This catches large ad campaigns, expensive tool purchases, and any
    # other high-dollar commitment.
    if estimated_cost > 500:
        return RiskTier.CRITICAL.value

    # Rule 6: Significant spend ($50-$500) is high risk.
    # This range covers most paid campaigns and non-trivial purchases.
    if estimated_cost > 50:
        return RiskTier.HIGH.value

    # Rule 7: Small spend (>$0 up to $50) is medium risk.
    # Small test budgets, minor tool costs, and similar low-dollar items.
    if estimated_cost > 0:
        return RiskTier.MEDIUM.value

    # Rule 8: Zero-cost, public-facing actions that didn't match earlier
    # rules (not SEO/analytics fix, not website update).  These include
    # social posts, review requests, GBP updates, etc.  They carry some
    # reputational risk but no financial risk.
    if is_public_facing:
        return RiskTier.LOW.value

    # Default: low risk for anything that didn't match above.
    return RiskTier.LOW.value


def derive_approval_requirement(
    risk_tier: str,
    auto_execution_enabled: bool,
) -> str:
    """Derive the approval requirement from risk tier and operator config.

    The ``auto_execution_enabled`` flag comes from the operator's
    ``BudgetAndRisk.auto_execution_enabled`` setting in their
    BusinessProfile.  When enabled, lower-risk actions can proceed
    without human review.

    Parameters
    ----------
    risk_tier:
        RiskTier enum value (e.g., "auto", "low", "medium").
    auto_execution_enabled:
        Whether the operator has enabled automatic execution for
        low-risk actions.

    Returns
    -------
    str
        An ApprovalRequirement enum value.
    """
    # Auto-tier actions are designed to be safe for automatic execution.
    # If the operator has enabled auto-execution, let them through.
    if risk_tier == RiskTier.AUTO.value and auto_execution_enabled:
        return ApprovalRequirement.AUTO_APPROVE.value

    # Low-risk actions can also auto-execute when the operator trusts the
    # system.  This covers small copy tweaks, metadata updates, and other
    # routine maintenance.
    if risk_tier == RiskTier.LOW.value and auto_execution_enabled:
        return ApprovalRequirement.AUTO_APPROVE.value

    # Low-risk actions without auto-execution enabled still only need a
    # lightweight review -- the operator can batch-approve these.
    if risk_tier == RiskTier.LOW.value and not auto_execution_enabled:
        return ApprovalRequirement.OPERATOR_REVIEW.value

    # Medium-risk actions always need review.  The operator should see
    # them but can batch-approve multiple at once.
    if risk_tier == RiskTier.MEDIUM.value:
        return ApprovalRequirement.OPERATOR_REVIEW.value

    # High and critical actions require explicit approval.  These involve
    # significant spend, brand-level changes, or high-visibility actions
    # where a mistake is costly.
    if risk_tier in (RiskTier.HIGH.value, RiskTier.CRITICAL.value):
        return ApprovalRequirement.OPERATOR_APPROVAL.value

    # Default: require operator review for any unrecognized tier.
    return ApprovalRequirement.OPERATOR_REVIEW.value


def compute_priority_score(
    severity: str,
    finding_priority: str,
    estimated_effort_hours: float,
    estimated_cost: float,
    archetype_match: bool,
) -> float:
    """Compute a 0-100 priority score for a proposed action.

    The score combines five factors to produce a single ranking value
    that determines execution order within a bundle.  Higher scores
    mean the action should be executed sooner.

    Factors
    -------
    1. **Severity base** -- the most important signal.  Critical findings
       start at 90, high at 70, medium at 50, low at 30.
    2. **Priority boost** -- adjusts for explicit timeline urgency.
       P0 adds 10, P1 adds 5, P2 is neutral, P3 subtracts 5.
    3. **Effort penalty** -- large efforts are harder to execute and may
       block other work.  Quick tasks get a bonus.
    4. **Cost penalty** -- expensive actions carry financial risk and may
       need budget approval.  Free actions get a bonus.
    5. **Archetype match bonus** -- actions that align with the business
       archetype are more likely to be impactful.

    Parameters
    ----------
    severity:
        FindingSeverity value from the source finding.
    finding_priority:
        FindingPriority value from the source finding.
    estimated_effort_hours:
        Numeric effort estimate in hours.
    estimated_cost:
        Estimated USD cost of this action.
    archetype_match:
        Whether the action aligns with the business archetype.

    Returns
    -------
    float
        A priority score clamped to the range [0, 100].
    """
    # Factor 1: Base score from severity.
    # Critical issues are the most impactful and should be addressed first.
    severity_base_map = {
        "critical": 90.0,
        "high": 70.0,
        "medium": 50.0,
        "low": 30.0,
        "info": 10.0,
    }
    score = severity_base_map.get(severity, 50.0)

    # Factor 2: Priority boost.
    # Explicit priority overrides nudge the score up or down relative to
    # the severity baseline.
    priority_boost_map = {
        "P0": 10.0,
        "P1": 5.0,
        "P2": 0.0,
        "P3": -5.0,
    }
    score += priority_boost_map.get(finding_priority, 0.0)

    # Factor 3: Effort penalty.
    # Quick tasks are preferred because they deliver value faster and
    # don't block the operator's calendar.  Large tasks get penalized.
    if estimated_effort_hours > 8:
        score -= 10.0
    elif estimated_effort_hours > 4:
        score -= 5.0
    elif estimated_effort_hours <= 1:
        score += 10.0

    # Factor 4: Cost penalty.
    # Free actions are preferred because they carry no financial risk.
    # Expensive actions need budget sign-off and may be deferred.
    if estimated_cost > 500:
        score -= 10.0
    elif estimated_cost > 100:
        score -= 5.0
    elif estimated_cost == 0:
        score += 5.0

    # Factor 5: Archetype match bonus.
    # Actions that fit the business's archetype are more likely to move
    # the needle.  A local service business benefits more from GBP
    # optimization than an e-commerce brand, for example.
    if archetype_match:
        score += 5.0

    # Clamp to [0, 100]
    return max(0.0, min(100.0, score))

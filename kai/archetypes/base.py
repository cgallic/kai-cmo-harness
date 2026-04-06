"""Base classes for Kai Marketing OS archetype definitions.

An **archetype** encodes everything the Kai system needs to know about a
particular *type* of business in order to audit, prioritise, recommend
channels, score KPIs, and allocate budget intelligently.

Every concrete archetype (``local_service``, ``ecommerce``,
``professional_services``, ``multi_location``, etc.) instantiates
``ArchetypeDefinition`` with its own data.  Downstream systems never
hard-code business-type logic — they read it from the archetype.

The sub-models are intentionally simple value objects so they serialise
cleanly to YAML / JSON and can be stored alongside workspace state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================================
# Sub-models
# ============================================================================


@dataclass(frozen=True)
class KPIDefinition:
    """A single Key Performance Indicator relevant to an archetype.

    Parameters
    ----------
    id:
        Machine-readable identifier, e.g. ``"leads_per_month"``.
    name:
        Human-readable display name.
    description:
        What this KPI measures and why it matters.
    unit:
        Measurement unit — ``"count"``, ``"dollars"``, ``"percentage"``,
        ``"seconds"``, ``"rating"``, or a free-form string.
    direction:
        ``"higher_is_better"`` or ``"lower_is_better"``.
    priority:
        ``"primary"``, ``"secondary"``, or ``"tertiary"``.
    benchmark_range:
        Typical range for this archetype as a human-readable string,
        e.g. ``"20-80"`` or ``"$25-150"``.  ``None`` when the range
        is highly variable.
    """

    id: str
    name: str
    description: str
    unit: str
    direction: str  # "higher_is_better" | "lower_is_better"
    priority: str  # "primary" | "secondary" | "tertiary"
    benchmark_range: Optional[str] = None


@dataclass(frozen=True)
class ChannelRecommendation:
    """A recommended marketing channel for an archetype.

    Parameters
    ----------
    channel:
        Canonical channel name (matches ``ChannelPresence.platform``
        in ``BusinessProfile``).
    priority:
        Integer priority where 1 is highest.
    stage_relevance:
        Business stages where this channel is appropriate, e.g.
        ``["early-pmf", "growth", "scale"]``.  ``"all"`` is a
        shorthand accepted in the list.
    rationale:
        Why this channel matters for this archetype.
    budget_minimum:
        Minimum effective monthly spend in USD.  ``None`` for free
        channels.
    prerequisites:
        What must be in place before this channel is useful.
    """

    channel: str
    priority: int
    stage_relevance: List[str]
    rationale: str
    budget_minimum: Optional[float] = None
    prerequisites: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionFamily:
    """A group of related marketing actions.

    Parameters
    ----------
    id:
        Machine-readable identifier, e.g. ``"review_generation"``.
    name:
        Human-readable display name.
    description:
        What this family of actions accomplishes.
    actions:
        Ordered list of specific action IDs within the family.
    priority:
        ``"high"``, ``"medium"``, or ``"low"``.
    typical_timeline:
        Rough time estimate, e.g. ``"1-2 weeks"``, ``"ongoing"``.
    """

    id: str
    name: str
    description: str
    actions: List[str]
    priority: str  # "high" | "medium" | "low"
    typical_timeline: Optional[str] = None


@dataclass(frozen=True)
class CreativeFormat:
    """A recommended creative format for an archetype.

    Parameters
    ----------
    id:
        Machine-readable identifier, e.g. ``"before_after"``.
    name:
        Human-readable display name.
    description:
        When and how to use this format.
    platforms:
        Which channels/platforms this format is effective on.
    requirements:
        Assets or inputs needed to produce this format.
    """

    id: str
    name: str
    description: str
    platforms: List[str]
    requirements: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BudgetRange:
    """Budget heuristic for a specific business stage.

    Parameters
    ----------
    stage:
        Business stage label (matches
        ``BusinessClassification.stage``).
    min_monthly:
        Minimum recommended USD per month.
    max_monthly:
        Maximum recommended USD per month.
    allocation_notes:
        How to split the budget across channels.
    """

    stage: str
    min_monthly: float
    max_monthly: float
    allocation_notes: str


# ============================================================================
# Top-level archetype container
# ============================================================================


@dataclass(frozen=True)
class ArchetypeDefinition:
    """Complete archetype definition for a business type.

    Every field is populated by a concrete archetype module (e.g.
    ``local_service.py``, ``multi_location.py``).  Downstream systems
    read these fields to drive audits, proposals, action plans, and
    budget allocation without any business-type-specific branching.
    """

    id: str
    name: str
    description: str
    audit_categories: List[str]
    priority_defaults: List[str]
    kpi_schema: Dict[str, KPIDefinition]
    channel_mix: List[ChannelRecommendation]
    action_families: List[ActionFamily]
    compliance_sensitivities: List[str]
    creative_formats: List[CreativeFormat]
    budget_heuristics: Dict[str, BudgetRange]
    minimum_viable_channels: List[str]
    archetype_specific_rules: List[str]


__all__ = [
    "ArchetypeDefinition",
    "KPIDefinition",
    "ChannelRecommendation",
    "ActionFamily",
    "CreativeFormat",
    "BudgetRange",
]

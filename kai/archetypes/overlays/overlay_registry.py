"""Overlay registry and merge logic for the Kai Marketing OS.

An **overlay** is a modifier that layers industry-specific constraints,
KPIs, compliance requirements, and creative rules on top of a base
archetype.  A healthcare business that uses the ``local-service``
archetype gets HIPAA considerations applied.  A creator selling products
gets audience-first metrics layered onto ``ecommerce``.

The core function is ``apply_overlay`` which produces a *new*
``ArchetypeDefinition`` with the overlay's additions merged in, without
mutating the original.

Usage::

    from kai.archetypes.overlays import (
        apply_overlay,
        HEALTHCARE_OVERLAY,
    )
    from kai.archetypes import LOCAL_SERVICE_ARCHETYPE

    modified = apply_overlay(LOCAL_SERVICE_ARCHETYPE, HEALTHCARE_OVERLAY)
    assert "hipaa_compliance" in modified.audit_categories
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kai.archetypes.base import (
    ActionFamily,
    ArchetypeDefinition,
    KPIDefinition,
)


# ============================================================================
# Data model
# ============================================================================


@dataclass(frozen=True)
class OverlayDefinition:
    """Industry overlay that modifies a base archetype.

    Parameters
    ----------
    id:
        Unique overlay identifier, e.g. ``"healthcare"``.
    name:
        Human-readable display name, e.g. ``"Healthcare / Medical"``.
    description:
        What this overlay does and when it applies.
    compatible_archetypes:
        Which archetype IDs this overlay can be applied to.  An empty
        list means *all* archetypes are compatible.
    additional_audit_categories:
        Audit categories added by this overlay.
    additional_kpis:
        Extra KPIs introduced by the overlay.  If an ID collides with
        an existing KPI on the archetype, the overlay version wins.
    additional_compliance:
        Extra compliance sensitivity statements.
    restricted_actions:
        Action IDs from the base archetype that require extra compliance
        review when this overlay is active.
    restricted_claims:
        Marketing claims that are restricted under this overlay.
    required_disclaimers:
        Disclaimers that must appear in marketing materials.
    modified_priorities:
        Adjustments to ``priority_defaults``.  Keys are action-family
        IDs and values are the new priority string (e.g. ``"high"``).
    additional_creative_rules:
        Extra rules for creative production.
    metadata:
        Overlay-specific extra data for downstream consumers.
    """

    id: str
    name: str
    description: str
    compatible_archetypes: List[str] = field(default_factory=list)
    additional_audit_categories: List[str] = field(default_factory=list)
    additional_kpis: Dict[str, KPIDefinition] = field(default_factory=dict)
    additional_compliance: List[str] = field(default_factory=list)
    restricted_actions: List[str] = field(default_factory=list)
    restricted_claims: List[str] = field(default_factory=list)
    required_disclaimers: List[str] = field(default_factory=list)
    modified_priorities: Dict[str, str] = field(default_factory=dict)
    additional_creative_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Merge helpers
# ============================================================================


def _deduplicated_list(base: List[str], additions: List[str]) -> List[str]:
    """Return *base* extended by *additions* with duplicates removed,
    preserving original order."""
    seen: set[str] = set(base)
    result = list(base)
    for item in additions:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _merge_kpis(
    base: Dict[str, KPIDefinition],
    additions: Dict[str, KPIDefinition],
) -> Dict[str, KPIDefinition]:
    """Merge KPI dicts.  Overlay KPIs override on collision."""
    merged = dict(base)
    merged.update(additions)
    return merged


def _annotate_restricted_actions(
    families: List[ActionFamily],
    restricted: List[str],
) -> List[ActionFamily]:
    """Return a new list of ``ActionFamily`` instances where any family
    containing a restricted action gets a compliance-review note
    appended to its description."""
    if not restricted:
        return list(families)

    restricted_set = set(restricted)
    result: List[ActionFamily] = []

    for fam in families:
        overlapping = restricted_set.intersection(fam.actions)
        if overlapping:
            names = ", ".join(sorted(overlapping))
            note = (
                f" [COMPLIANCE REVIEW REQUIRED for: {names}]"
            )
            new_fam = ActionFamily(
                id=fam.id,
                name=fam.name,
                description=fam.description + note,
                actions=list(fam.actions),
                priority=fam.priority,
                typical_timeline=fam.typical_timeline,
            )
            result.append(new_fam)
        else:
            result.append(fam)

    return result


def _apply_priority_overrides(
    families: List[ActionFamily],
    overrides: Dict[str, str],
) -> List[ActionFamily]:
    """Return a new list of ``ActionFamily`` instances with priorities
    adjusted according to *overrides*."""
    if not overrides:
        return list(families)

    result: List[ActionFamily] = []
    for fam in families:
        if fam.id in overrides:
            new_fam = ActionFamily(
                id=fam.id,
                name=fam.name,
                description=fam.description,
                actions=list(fam.actions),
                priority=overrides[fam.id],
                typical_timeline=fam.typical_timeline,
            )
            result.append(new_fam)
        else:
            result.append(fam)
    return result


# ============================================================================
# Public API
# ============================================================================


def apply_overlay(
    archetype: ArchetypeDefinition,
    overlay: OverlayDefinition,
) -> ArchetypeDefinition:
    """Merge *overlay* onto *archetype* and return a new definition.

    The original ``archetype`` is never mutated.

    Raises
    ------
    ValueError
        If the overlay declares ``compatible_archetypes`` and the
        archetype's ``id`` is not in that list.
    """
    # ---- compatibility guard ----
    if (
        overlay.compatible_archetypes
        and archetype.id not in overlay.compatible_archetypes
    ):
        raise ValueError(
            f"Overlay '{overlay.id}' ({overlay.name}) is not compatible "
            f"with archetype '{archetype.id}' ({archetype.name}). "
            f"Compatible archetypes: {overlay.compatible_archetypes}"
        )

    # ---- track applied overlays via metadata ----
    # We store applied overlay IDs in archetype_specific_rules as a
    # readable annotation so downstream consumers can see it, and also
    # propagate through the frozen dataclass cleanly.
    existing_overlay_ids: List[str] = []
    overlay_marker_prefix = "[APPLIED OVERLAYS: "
    existing_rules = list(archetype.archetype_specific_rules)

    # Extract any prior overlay-tracking rule so we can update it
    non_marker_rules: List[str] = []
    for rule in existing_rules:
        if rule.startswith(overlay_marker_prefix):
            # Parse out the previously applied overlay IDs
            inner = rule[len(overlay_marker_prefix):-1]  # strip trailing "]"
            existing_overlay_ids = [
                s.strip() for s in inner.split(",") if s.strip()
            ]
        else:
            non_marker_rules.append(rule)

    applied_overlay_ids = existing_overlay_ids + [overlay.id]

    # ---- build merged rules ----
    merged_rules = list(non_marker_rules)

    # Add required disclaimers as rules
    for disclaimer in overlay.required_disclaimers:
        rule = f"Required disclaimer: {disclaimer}"
        if rule not in merged_rules:
            merged_rules.append(rule)

    # Add creative rules
    for creative_rule in overlay.additional_creative_rules:
        if creative_rule not in merged_rules:
            merged_rules.append(creative_rule)

    # Add restricted claims as rules
    if overlay.restricted_claims:
        claims_str = "; ".join(overlay.restricted_claims)
        rule = f"Restricted claims (do not use without evidence/approval): {claims_str}"
        if rule not in merged_rules:
            merged_rules.append(rule)

    # Re-add the overlay tracking marker
    merged_rules.append(
        f"{overlay_marker_prefix}{', '.join(applied_overlay_ids)}]"
    )

    # ---- merge action families ----
    merged_families = _annotate_restricted_actions(
        list(archetype.action_families),
        overlay.restricted_actions,
    )
    merged_families = _apply_priority_overrides(
        merged_families,
        overlay.modified_priorities,
    )

    # ---- deep-copy mutable containers from the original ----
    merged_kpis = _merge_kpis(
        copy.deepcopy(archetype.kpi_schema),
        copy.deepcopy(overlay.additional_kpis),
    )

    # ---- assemble the new archetype ----
    return ArchetypeDefinition(
        id=archetype.id,
        name=archetype.name,
        description=archetype.description,
        audit_categories=_deduplicated_list(
            archetype.audit_categories,
            overlay.additional_audit_categories,
        ),
        priority_defaults=list(archetype.priority_defaults),
        kpi_schema=merged_kpis,
        channel_mix=list(archetype.channel_mix),
        action_families=merged_families,
        compliance_sensitivities=_deduplicated_list(
            archetype.compliance_sensitivities,
            overlay.additional_compliance,
        ),
        creative_formats=list(archetype.creative_formats),
        budget_heuristics=dict(archetype.budget_heuristics),
        minimum_viable_channels=list(archetype.minimum_viable_channels),
        archetype_specific_rules=merged_rules,
    )


def apply_overlays(
    archetype: ArchetypeDefinition,
    overlays: List[OverlayDefinition],
) -> ArchetypeDefinition:
    """Apply multiple overlays in sequence.

    Order matters -- later overlays can further restrict actions and
    override priorities set by earlier ones.
    """
    result = archetype
    for overlay in overlays:
        result = apply_overlay(result, overlay)
    return result


# ============================================================================
# Registry
# ============================================================================

# Populated at import time by the package __init__.py after all overlay
# modules are loaded.  Consumers should use ``get_overlay`` /
# ``list_overlays`` rather than accessing this dict directly.
OVERLAY_REGISTRY: Dict[str, OverlayDefinition] = {}


def get_overlay(overlay_id: str) -> Optional[OverlayDefinition]:
    """Look up an overlay by its ID.

    Returns ``None`` if no overlay with that ID is registered.
    """
    return OVERLAY_REGISTRY.get(overlay_id)


def list_overlays() -> List[str]:
    """Return all registered overlay IDs."""
    return list(OVERLAY_REGISTRY.keys())


__all__ = [
    "OverlayDefinition",
    "apply_overlay",
    "apply_overlays",
    "OVERLAY_REGISTRY",
    "get_overlay",
    "list_overlays",
]

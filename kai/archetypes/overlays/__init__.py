"""Overlay package for the Kai Marketing OS archetype system.

Overlays are modifiers that layer industry-specific constraints, KPIs,
compliance requirements, and creative rules on top of base archetypes.
A healthcare business using the ``local-service`` archetype gets HIPAA
considerations applied.  A creator selling products gets audience-first
metrics layered onto ``ecommerce`` defaults.

Usage::

    from kai.archetypes.overlays import (
        apply_overlay,
        apply_overlays,
        get_overlay,
        list_overlays,
        HEALTHCARE_OVERLAY,
        CREATOR_OVERLAY,
        FRANCHISE_OVERLAY,
        SAAS_OVERLAY,
        OVERLAY_REGISTRY,
    )
    from kai.archetypes import LOCAL_SERVICE_ARCHETYPE

    # Apply a single overlay
    healthcare_local = apply_overlay(
        LOCAL_SERVICE_ARCHETYPE, HEALTHCARE_OVERLAY
    )

    # Apply multiple overlays (order matters)
    franchise_healthcare = apply_overlays(
        LOCAL_SERVICE_ARCHETYPE,
        [FRANCHISE_OVERLAY, HEALTHCARE_OVERLAY],
    )

    # Look up by ID
    overlay = get_overlay("saas")
"""

from .creator import CREATOR_OVERLAY
from .franchise import FRANCHISE_OVERLAY
from .healthcare import HEALTHCARE_OVERLAY
from .overlay_registry import (
    OVERLAY_REGISTRY,
    OverlayDefinition,
    apply_overlay,
    apply_overlays,
    get_overlay,
    list_overlays,
)
from .saas import SAAS_OVERLAY

# ---------------------------------------------------------------------------
# Populate the registry now that all overlay modules are imported.
# ---------------------------------------------------------------------------

OVERLAY_REGISTRY[HEALTHCARE_OVERLAY.id] = HEALTHCARE_OVERLAY
OVERLAY_REGISTRY[CREATOR_OVERLAY.id] = CREATOR_OVERLAY
OVERLAY_REGISTRY[FRANCHISE_OVERLAY.id] = FRANCHISE_OVERLAY
OVERLAY_REGISTRY[SAAS_OVERLAY.id] = SAAS_OVERLAY

__all__ = [
    # Data model
    "OverlayDefinition",
    # Functions
    "apply_overlay",
    "apply_overlays",
    "get_overlay",
    "list_overlays",
    # Registry
    "OVERLAY_REGISTRY",
    # Concrete overlays
    "HEALTHCARE_OVERLAY",
    "CREATOR_OVERLAY",
    "FRANCHISE_OVERLAY",
    "SAAS_OVERLAY",
]

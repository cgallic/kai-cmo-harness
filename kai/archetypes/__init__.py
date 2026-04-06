"""Archetype package for the Kai Marketing OS.

Archetypes encode everything the system needs to know about a *type* of
business: what to audit, which KPIs matter, which channels to prioritise,
what actions to take, what creative formats work, and how to allocate budget.

Usage::

    from kai.archetypes import LOCAL_SERVICE_ARCHETYPE, ArchetypeDefinition

    # Look up the archetype by ID
    archetype = ARCHETYPE_REGISTRY["local-service"]
    print(archetype.audit_categories)
"""

from .base import (
    ActionFamily,
    ArchetypeDefinition,
    BudgetRange,
    ChannelRecommendation,
    CreativeFormat,
    KPIDefinition,
)
from .ecommerce import ECOMMERCE_ARCHETYPE
from .local_service import LOCAL_SERVICE_ARCHETYPE
from .multi_location import MULTI_LOCATION_ARCHETYPE
from .overlays import (
    CREATOR_OVERLAY,
    FRANCHISE_OVERLAY,
    HEALTHCARE_OVERLAY,
    OVERLAY_REGISTRY,
    SAAS_OVERLAY,
    OverlayDefinition,
    apply_overlay,
    apply_overlays,
    get_overlay,
    list_overlays,
)
from .professional_services import PROFESSIONAL_SERVICES_ARCHETYPE

# Activation logic
from .activation import (
    ActivationResult,
    ModuleDefinition,
    MODULE_REGISTRY,
    activate,
    determine_archetype,
    determine_overlays,
    determine_active_modules,
    get_module,
    list_modules,
)

# ---------------------------------------------------------------------------
# Registry — maps archetype ID to its definition.  New archetypes should be
# added here as they are built.
# ---------------------------------------------------------------------------

ARCHETYPE_REGISTRY = {
    LOCAL_SERVICE_ARCHETYPE.id: LOCAL_SERVICE_ARCHETYPE,
    ECOMMERCE_ARCHETYPE.id: ECOMMERCE_ARCHETYPE,
    MULTI_LOCATION_ARCHETYPE.id: MULTI_LOCATION_ARCHETYPE,
    PROFESSIONAL_SERVICES_ARCHETYPE.id: PROFESSIONAL_SERVICES_ARCHETYPE,
}

__all__ = [
    # Base class and sub-models
    "ArchetypeDefinition",
    "KPIDefinition",
    "ChannelRecommendation",
    "ActionFamily",
    "CreativeFormat",
    "BudgetRange",
    # Concrete archetypes
    "LOCAL_SERVICE_ARCHETYPE",
    "ECOMMERCE_ARCHETYPE",
    "MULTI_LOCATION_ARCHETYPE",
    "PROFESSIONAL_SERVICES_ARCHETYPE",
    # Registry
    "ARCHETYPE_REGISTRY",
    # Overlay system
    "OverlayDefinition",
    "apply_overlay",
    "apply_overlays",
    "get_overlay",
    "list_overlays",
    "OVERLAY_REGISTRY",
    "HEALTHCARE_OVERLAY",
    "CREATOR_OVERLAY",
    "FRANCHISE_OVERLAY",
    "SAAS_OVERLAY",
    # Activation logic
    "ActivationResult",
    "ModuleDefinition",
    "MODULE_REGISTRY",
    "activate",
    "determine_archetype",
    "determine_overlays",
    "determine_active_modules",
    "get_module",
    "list_modules",
]

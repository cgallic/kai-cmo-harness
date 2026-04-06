"""Archetype-specific messaging frameworks for the Kai creative engine.

Each archetype (local service, ecommerce, professional services,
multi-location) has a dedicated builder function that returns a
``MessagingFramework`` containing message angles, objection handlers,
seasonal hooks, CTA templates, tone guidelines, forbidden phrases, and
proof-type priorities.

Quick start::

    from kai.creative.messaging_frameworks import get_messaging_framework

    fw = get_messaging_framework("local_service")
    print(fw.core_message)
    print(fw.get_angles_for("landing_page"))
"""

from kai.creative.messaging_frameworks.base import (  # noqa: F401
    CTATemplate,
    MessageAngle,
    MessagingFramework,
    ObjectionHandler,
    SeasonalHook,
)
from kai.creative.messaging_frameworks.ecommerce import (  # noqa: F401
    build_ecommerce_messaging,
)
from kai.creative.messaging_frameworks.local_service import (  # noqa: F401
    build_local_service_messaging,
)
from kai.creative.messaging_frameworks.multi_location import (  # noqa: F401
    LOCATION_PERSONALIZATION_RULES,
    build_multi_location_messaging,
)
from kai.creative.messaging_frameworks.professional_services import (  # noqa: F401
    build_professional_services_messaging,
)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

_BUILDERS = {
    "local_service": build_local_service_messaging,
    "ecommerce": build_ecommerce_messaging,
    "professional_services": build_professional_services_messaging,
    "multi_location": build_multi_location_messaging,
}


def get_messaging_framework(archetype: str) -> MessagingFramework:
    """Return the messaging framework for *archetype*.

    Parameters
    ----------
    archetype:
        One of ``"local_service"``, ``"ecommerce"``,
        ``"professional_services"``, or ``"multi_location"``.

    Raises
    ------
    ValueError
        If *archetype* is not a recognized archetype string.
    """
    builder = _BUILDERS.get(archetype)
    if builder is None:
        supported = ", ".join(sorted(_BUILDERS))
        raise ValueError(
            f"Unknown archetype {archetype!r}. "
            f"Supported archetypes: {supported}"
        )
    return builder()

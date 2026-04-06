"""Kai compliance policy packs.

Structured, code-queryable rule sets for website, social media, paid media,
email marketing, and analytics/tracking compliance.  Each pack is built by
a factory function and registered in the global :class:`PolicyRegistry`.

Quick start::

    from kai.compliance.policy_packs import default_registry

    # Get all rules that apply to a landing page in the EU
    rules = default_registry.get_applicable_rules(
        content_type="landing_page",
        region="EU",
    )
"""

from .base import ContentType, PolicyPack, PolicyRegistry, PolicyRule, RuleSeverity
from .analytics import build_analytics_policy_pack
from .email import build_email_policy_pack
from .paid_media import build_paid_media_policy_pack
from .social import build_social_policy_pack
from .website import build_website_policy_pack

__all__ = [
    # Core models
    "ContentType",
    "PolicyPack",
    "PolicyRegistry",
    "PolicyRule",
    "RuleSeverity",
    # Pack builders
    "build_analytics_policy_pack",
    "build_email_policy_pack",
    "build_paid_media_policy_pack",
    "build_social_policy_pack",
    "build_website_policy_pack",
    # Pre-built registry
    "default_registry",
]


def _build_default_registry() -> PolicyRegistry:
    """Construct a registry pre-loaded with every built-in policy pack."""
    registry = PolicyRegistry()
    registry.register(build_website_policy_pack())
    registry.register(build_social_policy_pack())
    registry.register(build_paid_media_policy_pack())
    registry.register(build_email_policy_pack())
    registry.register(build_analytics_policy_pack())
    return registry


default_registry: PolicyRegistry = _build_default_registry()
"""Singleton registry containing all five built-in policy packs."""

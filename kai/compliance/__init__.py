"""Kai compliance layer.

Provides structured, programmatic policy packs that encode legal, platform,
and regulatory compliance rules for marketing content.  The compliance engine
(Task 062) uses these packs to automatically check content before it ships,
preventing costly ad disapprovals, legal violations, and brand reputation
damage.

Submodules
----------
policy_packs
    Five domain-specific policy packs (website, social, paid_media, email,
    analytics) plus the base :class:`PolicyRule` model and
    :class:`PolicyRegistry` for querying rules across packs.

Quick start::

    from kai.compliance import PolicyRegistry, PolicyRule, default_registry

    # All rules for a paid ad in the US healthcare industry
    rules = default_registry.get_applicable_rules(
        content_type="paid_ad",
        region="US",
        industry="healthcare",
    )

    for rule in rules:
        print(f"[{rule.severity}] {rule.rule_id}: {rule.description}")
"""

from .policy_packs import (
    ContentType,
    PolicyPack,
    PolicyRegistry,
    PolicyRule,
    RuleSeverity,
    default_registry,
)

__all__ = [
    "ContentType",
    "PolicyPack",
    "PolicyRegistry",
    "PolicyRule",
    "RuleSeverity",
    "default_registry",
]

"""
Content Quality Scorer — Rule registry.
"""

from typing import Dict, List, Type

from scripts.quality.rules.base import BaseRule
from scripts.quality.types import Category

# All rules register here
_REGISTRY: List[Type[BaseRule]] = []


def register(cls: Type[BaseRule]) -> Type[BaseRule]:
    """Decorator to register a rule class."""
    _REGISTRY.append(cls)
    return cls


def get_all_rules() -> List[Type[BaseRule]]:
    """Return all registered rule classes."""
    return list(_REGISTRY)


def get_rules_by_category(category: Category) -> List[Type[BaseRule]]:
    """Return rules for a specific category."""
    return [r for r in _REGISTRY if r.CATEGORY == category]


def get_rule_by_id(rule_id: str) -> Type[BaseRule] | None:
    """Look up a rule class by its ID."""
    for r in _REGISTRY:
        if r.RULE_ID == rule_id:
            return r
    return None


def get_rules_for_sets(rule_sets: List[str]) -> List[Type[BaseRule]]:
    """Return rules matching the given rule set names.

    Valid set names: 'aa', 'geo', 'structure', 'four_us'
    """
    set_map = {
        "aa": Category.ALGORITHMIC_AUTHORSHIP,
        "geo": Category.GEO_SIGNALS,
        "structure": Category.CONTENT_STRUCTURE,
        "four_us": Category.FOUR_US,
    }
    categories = {set_map[s] for s in rule_sets if s in set_map}
    return [r for r in _REGISTRY if r.CATEGORY in categories]

"""Profile loaders for the Kai Marketing OS.

This package converts external data sources -- YAML config files, markdown
onboarding notes, gateway brand configs, operator overrides, and form
submissions -- into canonical ``BusinessProfile`` instances.

Usage::

    from kai.loaders import load_from_yaml, merge_profiles, build_profile

    yaml_data = load_from_yaml("config.yaml")
    overrides = load_from_overrides({"identity.business_name": "Acme Inc"})
    profile = build_profile([yaml_data, overrides])
"""

from .profile_loader import (
    build_profile,
    deep_merge,
    flatten_dotted_keys,
    load_from_brand_config,
    load_from_form,
    load_from_markdown,
    load_from_overrides,
    load_from_yaml,
    merge_profiles,
)

__all__ = [
    "load_from_yaml",
    "load_from_markdown",
    "load_from_brand_config",
    "load_from_overrides",
    "load_from_form",
    "merge_profiles",
    "build_profile",
    "flatten_dotted_keys",
    "deep_merge",
]

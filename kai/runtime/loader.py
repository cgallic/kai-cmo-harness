"""Workspace and module loaders for the Kai runtime."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Dict, Iterable, List

import yaml

from scripts.harness_config import get_config

from .models import KaiBrandProfile, KaiModuleManifest, KaiWorkspaceProfile


_MODULE_DIR = Path(__file__).resolve().parent / "modules"

_ARCHETYPE_CHANNELS = {
    "local-service": ["local-seo", "reviews", "calls", "paid-search", "referrals"],
    "ecommerce": ["paid-social", "email", "creative", "cro", "retention"],
    "professional-services": ["thought-leadership", "email", "referrals", "linkedin", "cro"],
    "multi-location": ["location-seo", "reviews", "paid-search", "reporting"],
    "software": ["content", "seo", "email", "paid-acquisition", "analytics"],
}

_ARCHETYPE_KEYWORDS = {
    "local-service": [
        "plumber", "cleaner", "hvac", "roofer", "electrician", "landscaper",
        "law firm", "dentist", "service area", "same-day", "phone calls",
    ],
    "ecommerce": [
        "shopify", "e-commerce", "ecommerce", "dtc", "cart", "aov",
        "skincare", "shipping", "product page", "collection",
    ],
    "professional-services": [
        "law", "legal", "accounting", "consulting", "agency", "advisor",
        "architect", "engineering", "financial", "free consultation",
    ],
    "multi-location": [
        "locations", "offices", "franchise", "network", "clinic network",
        "multi-location", "branches",
    ],
    "software": [
        "saas", "software", "dashboard", "platform", "api", "subscription",
        "developer", "analytics", "alerts",
    ],
}


def _split_bullets(value: str | Iterable[str] | None) -> List[str]:
    """Normalize proof points and list-like config values."""
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    items = []
    for line in str(value).splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned:
            items.append(cleaned)
    return items


def _score_archetype(text: str, archetype: str) -> int:
    """Simple keyword score for archetype inference."""
    lowered = text.lower()
    return sum(1 for token in _ARCHETYPE_KEYWORDS.get(archetype, []) if token in lowered)


def _infer_primary_archetype(product: dict) -> str | None:
    """Infer the closest archetype from product config."""
    explicit = product.get("archetype")
    if explicit:
        return str(explicit)

    text = " ".join(
        str(part)
        for part in (
            product.get("name", ""),
            product.get("description", ""),
            product.get("proof_points", ""),
        )
    )
    scores = {
        archetype: _score_archetype(text, archetype)
        for archetype in _ARCHETYPE_KEYWORDS
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def _infer_overlays(product: dict, primary: str | None) -> List[str]:
    """Infer overlay modules from product config."""
    explicit = product.get("archetype_overlays", [])
    overlays = {str(value) for value in explicit}

    text = " ".join(
        str(part)
        for part in (
            product.get("name", ""),
            product.get("description", ""),
            product.get("proof_points", ""),
        )
    ).lower()

    if "office" in text or "locations" in text or "franchise" in text:
        overlays.add("multi-location")
    if primary != "professional-services" and any(token in text for token in ["law", "accounting", "consulting", "advisor"]):
        overlays.add("professional-services")
    if primary != "local-service" and any(token in text for token in ["service area", "same-day", "phone calls", "emergency service"]):
        overlays.add("local-service")

    overlays.discard(primary)
    return sorted(overlays)


@lru_cache(maxsize=1)
def load_module_manifests() -> Dict[str, KaiModuleManifest]:
    """Load all module manifests from disk."""
    manifests: Dict[str, KaiModuleManifest] = {}
    for path in sorted(_MODULE_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        manifest = KaiModuleManifest(**raw)
        manifests[manifest.id] = manifest
    return manifests


def _build_brand(product: dict, cfg) -> KaiBrandProfile:
    """Build a canonical brand profile from product config."""
    brand_id = product.get("id")
    primary = _infer_primary_archetype(product)
    overlays = _infer_overlays(product, primary)
    module_ids = [module_id for module_id in [primary, *overlays] if module_id]
    active_channels = list(product.get("active_channels", []))
    if not active_channels and primary:
        active_channels = _ARCHETYPE_CHANNELS.get(primary, []).copy()

    persona_defaults = cfg.site_persona_defaults.get(brand_id, {})

    return KaiBrandProfile(
        id=brand_id,
        name=product.get("name", brand_id),
        description=product.get("description", ""),
        url=product.get("url"),
        primary_archetype=primary,
        archetype_overlays=overlays,
        module_ids=module_ids,
        active_channels=active_channels,
        proof_points=_split_bullets(product.get("proof_points")),
        persona_defaults=persona_defaults,
        ga_property=cfg.sites.ga4_properties.get(brand_id),
        gsc_site=cfg.sites.gsc_urls.get(brand_id),
        metadata={
            "product_type": product.get("type"),
            "runtime_source": "config.yaml",
        },
    )


@lru_cache(maxsize=1)
def load_workspace_profile() -> KaiWorkspaceProfile:
    """Build the canonical Kai workspace profile from config."""
    cfg = get_config()
    config_path = Path(os.environ.get("CMO_CONFIG_PATH", str(cfg.repo_root / "config.yaml")))
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    raw = raw or {}
    workspace_raw = raw.get("workspace", {})

    products = raw.get("products", [])
    brands = [_build_brand(product, cfg) for product in products if product.get("id")]

    if not brands:
        for brand_id, persona_defaults in (cfg.site_persona_defaults or {}).items():
            brands.append(
                KaiBrandProfile(
                    id=brand_id,
                    name=brand_id,
                    persona_defaults=persona_defaults,
                    ga_property=cfg.sites.ga4_properties.get(brand_id),
                    gsc_site=cfg.sites.gsc_urls.get(brand_id),
                    metadata={"runtime_source": "site_persona_defaults"},
                )
            )

    return KaiWorkspaceProfile(
        workspace_id=workspace_raw.get("id", "kai-marketing-os"),
        name=workspace_raw.get("name", "Kai Marketing OS"),
        description=workspace_raw.get(
            "description",
            "Marketing-native Claude Code-style runtime with local and remote execution.",
        ),
        primary_user=workspace_raw.get("primary_user", "operator_saas"),
        product_mode=workspace_raw.get("product_mode", "clone"),
        surfaces=workspace_raw.get("surfaces", ["local", "remote"]),
        brands=brands,
        enabled_plugins=workspace_raw.get("enabled_plugins", ["kai-marketing"]),
        metadata={
            "module_count": len(load_module_manifests()),
            "brand_count": len(brands),
        },
    )

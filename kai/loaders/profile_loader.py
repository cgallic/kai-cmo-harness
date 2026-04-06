"""Profile loaders for the Kai Marketing OS.

Each loader converts a specific external source -- YAML config files, markdown
onboarding notes, gateway brand configs, operator overrides, or form
submissions -- into a partial ``Dict[str, Any]`` that maps onto the canonical
``BusinessProfile`` schema.  The ``merge_profiles`` function combines multiple
partials with explicit priority ordering, and ``build_profile`` instantiates the
final Pydantic (or fallback) model.

All loaders follow the same contract:
    - Accept one source of data.
    - Return a *partial* dict: only the keys that were actually present.
    - Never infer, hallucinate, or fill in missing data.
    - On I/O or parse errors, return ``{}`` with an ``_errors`` metadata list.

Dependencies:
    - ``yaml`` (PyYAML) for YAML parsing -- imported with try/except.
    - ``re`` (stdlib) for markdown parsing.
    - ``kai.models.business_profile.BusinessProfile`` for final instantiation.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Optional PyYAML import
# ---------------------------------------------------------------------------

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# ============================================================================
# Utility functions
# ============================================================================


def flatten_dotted_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dot-notation flat keys into a nested dict.

    Parameters
    ----------
    d:
        A dictionary that may contain dot-separated keys such as
        ``{"identity.business_name": "Acme"}``.

    Returns
    -------
    Dict[str, Any]
        Nested structure: ``{"identity": {"business_name": "Acme"}}``.
        Keys without dots pass through unchanged.  Arbitrary nesting
        depth is supported (e.g. ``"a.b.c.d"``).

    Examples
    --------
    >>> flatten_dotted_keys({"identity.business_name": "Acme", "id": "1"})
    {'identity': {'business_name': 'Acme'}, 'id': '1'}
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(".")
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        # If the target slot already has a non-dict value we cannot nest
        # further -- overwrite it.  This matches "highest priority wins"
        # semantics for operator overrides.
        target[parts[-1]] = value
    return result


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into *base* and return a new dict.

    Merge rules:
        - **Dicts** are merged recursively.
        - **Lists** are concatenated (override items appended to base).
        - **None** values in *override* do **not** replace existing values.
          To explicitly remove a field use the sentinel string
          ``"__DELETE__"``.
        - Scalar conflicts: *override* wins.

    Neither *base* nor *override* are mutated.

    Parameters
    ----------
    base:
        The lower-priority dict.
    override:
        The higher-priority dict whose values take precedence.

    Returns
    -------
    Dict[str, Any]
        A new merged dictionary.
    """
    merged = copy.deepcopy(base)
    for key, over_val in override.items():
        if over_val is None:
            # None in override does NOT erase base values.
            continue
        if over_val == "__DELETE__":
            merged.pop(key, None)
            continue
        base_val = merged.get(key)
        if isinstance(base_val, dict) and isinstance(over_val, dict):
            merged[key] = deep_merge(base_val, over_val)
        elif isinstance(base_val, list) and isinstance(over_val, list):
            merged[key] = base_val + over_val
        else:
            merged[key] = copy.deepcopy(over_val)
    return merged


# ============================================================================
# List deduplication helper
# ============================================================================


def _dedupe_list(items: list) -> list:
    """Deduplicate a list, preserving order.

    - For dicts with a ``name`` key: dedupe by ``name`` (last wins).
    - For scalars: dedupe by value (first occurrence kept).
    """
    if not items:
        return items

    # Check if the list contains dicts with 'name' keys.
    if items and isinstance(items[0], dict) and "name" in items[0]:
        seen: Dict[str, int] = {}
        result: list = []
        for item in items:
            name = item.get("name", "")
            if name in seen:
                # Replace earlier occurrence with later (higher-priority) one.
                result[seen[name]] = item
            else:
                seen[name] = len(result)
                result.append(item)
        return result

    # Scalar dedup -- preserve first occurrence.
    seen_scalars: set = set()
    deduped: list = []
    for item in items:
        hashable = item if isinstance(item, (str, int, float, bool)) else id(item)
        if hashable not in seen_scalars:
            seen_scalars.add(hashable)
            deduped.append(item)
    return deduped


# ============================================================================
# Loader: YAML config files
# ============================================================================


def load_from_yaml(file_path: str) -> Dict[str, Any]:
    """Parse a YAML file and return a partial BusinessProfile dict.

    Supports two primary YAML layouts:

    1. **Direct profile key** -- the YAML has a ``business_profile:``
       top-level key whose children map directly to BusinessProfile fields.
    2. **Products array** -- the YAML has ``products:`` with one or more
       product entries (as in ``config.example.yaml``).  The first product
       is extracted and mapped to profile fields.
    3. **Workspace / brand config** -- nested ``workspace:`` with name,
       description, and product metadata.

    Only fields actually present in the YAML are returned.  Missing data
    stays missing.

    Parameters
    ----------
    file_path:
        Absolute or relative path to a ``.yaml`` / ``.yml`` file.

    Returns
    -------
    Dict[str, Any]
        Partial profile dict with ``_source: "yaml"`` metadata.
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required for YAML loading.  Install it with: "
            "pip install pyyaml"
        )

    path = Path(file_path)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, IOError) as exc:
        return {"_source": "yaml", "_errors": [f"File read error: {exc}"]}

    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        return {
            "_source": "yaml",
            "_errors": [f"YAML parse error in {file_path}: {exc}"],
        }

    if not isinstance(raw, dict):
        return {"_source": "yaml", "_errors": ["YAML root is not a mapping"]}

    result: Dict[str, Any] = {"_source": "yaml"}

    # ----- Strategy 1: direct business_profile key --------------------------
    if "business_profile" in raw:
        bp = raw["business_profile"]
        if isinstance(bp, dict):
            result.update(bp)
        return result

    # ----- Strategy 2: products array ---------------------------------------
    products = raw.get("products")
    if isinstance(products, list) and products:
        product = products[0]
        if isinstance(product, dict):
            result.update(_map_product_to_profile(product, raw))
            return result

    # ----- Strategy 3: workspace / brand config -----------------------------
    workspace = raw.get("workspace")
    if isinstance(workspace, dict):
        result.update(_map_workspace_to_profile(workspace, raw))
        return result

    # ----- Fallback: map any recognized top-level keys ----------------------
    result.update(_map_toplevel_keys(raw))
    return result


def _map_product_to_profile(
    product: Dict[str, Any], raw: Dict[str, Any]
) -> Dict[str, Any]:
    """Map a products[] entry from config.example.yaml to profile fields."""
    partial: Dict[str, Any] = {}

    # Identity
    identity: Dict[str, Any] = {}
    if product.get("name"):
        identity["business_name"] = product["name"]
    if product.get("url"):
        identity["website_url"] = product["url"]
    if product.get("description"):
        identity["elevator_pitch"] = product["description"]
    if identity:
        partial["identity"] = identity

    # ID
    if product.get("id"):
        partial["id"] = product["id"]

    # Classification
    classification: Dict[str, Any] = {}
    if product.get("archetype"):
        classification["archetype"] = product["archetype"]
    if product.get("industry"):
        classification["industry"] = product["industry"]
    if product.get("vertical"):
        classification["vertical"] = product["vertical"]
    if product.get("business_model"):
        classification["business_model"] = product["business_model"]
    if product.get("stage"):
        classification["stage"] = product["stage"]
    if classification:
        partial["classification"] = classification

    # Channels from active_channels
    if product.get("active_channels"):
        partial["channels"] = [
            {"platform": ch, "is_active": True}
            for ch in product["active_channels"]
        ]

    # Trust from proof_points
    if product.get("proof_points"):
        pp = product["proof_points"]
        items = pp if isinstance(pp, list) else _split_proof_points(str(pp))
        partial["trust"] = {
            "testimonials": [
                {"signal_type": "statistic", "content": point}
                for point in items
            ],
        }

    # Metadata
    metadata: Dict[str, Any] = {}
    if product.get("archetype_overlays"):
        metadata["archetype_overlays"] = product["archetype_overlays"]
    # Merge GA / GSC from sites block
    sites = raw.get("sites", {})
    pid = product.get("id")
    if pid:
        ga = (sites.get("ga4_properties") or {}).get(pid)
        if ga:
            metadata["ga_property"] = ga
        gsc = (sites.get("gsc_urls") or {}).get(pid)
        if gsc:
            metadata["gsc_site"] = gsc
    if metadata:
        partial["metadata"] = metadata

    return partial


def _map_workspace_to_profile(
    workspace: Dict[str, Any], raw: Dict[str, Any]
) -> Dict[str, Any]:
    """Map a workspace: block to partial profile fields."""
    partial: Dict[str, Any] = {}

    if workspace.get("id"):
        partial["id"] = workspace["id"]

    identity: Dict[str, Any] = {}
    if workspace.get("name"):
        identity["business_name"] = workspace["name"]
    if workspace.get("description"):
        identity["elevator_pitch"] = workspace["description"]
    if identity:
        partial["identity"] = identity

    return partial


def _map_toplevel_keys(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map any recognized top-level YAML keys to profile fields."""
    partial: Dict[str, Any] = {}

    # Direct field names that match BusinessProfile
    direct_keys = [
        "id", "identity", "classification", "offers", "geography",
        "personas", "trust", "goals", "channels", "constraints",
        "budget", "sales_cycle", "brand_voice", "operator", "raw_notes",
        "metadata",
    ]
    for key in direct_keys:
        if key in raw:
            partial[key] = raw[key]

    return partial


def _split_proof_points(text: str) -> List[str]:
    """Split a proof-points string on newlines or semicolons."""
    items: List[str] = []
    for line in re.split(r"[;\n]", text):
        cleaned = line.strip().lstrip("-").strip()
        if cleaned:
            items.append(cleaned)
    return items


# ============================================================================
# Loader: Markdown onboarding / interview notes
# ============================================================================

# Regex patterns for extracting structured data from markdown.
_KV_PATTERN = re.compile(
    r"^\s*\*{0,2}"           # optional bold markers
    r"([\w\s/]+?)"           # key (words, spaces, slashes)
    r"\*{0,2}\s*:\s*"        # colon separator with optional bold
    r"(.+)$",                # value (rest of line)
    re.MULTILINE,
)

_BULLET_PATTERN = re.compile(r"^\s*[-*+]\s+(.+)$", re.MULTILINE)
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

# Canonical key aliases -> (profile_section, field_name)
_MD_KEY_MAP: Dict[str, tuple] = {
    "business name": ("identity", "business_name"),
    "company": ("identity", "business_name"),
    "company name": ("identity", "business_name"),
    "name": ("identity", "business_name"),
    "website": ("identity", "website_url"),
    "url": ("identity", "website_url"),
    "website url": ("identity", "website_url"),
    "phone": ("identity", "phone"),
    "email": ("identity", "email"),
    "tagline": ("identity", "tagline"),
    "elevator pitch": ("identity", "elevator_pitch"),
    "description": ("identity", "elevator_pitch"),
    "logo": ("identity", "logo_url"),
    "logo url": ("identity", "logo_url"),
    "industry": ("classification", "industry"),
    "vertical": ("classification", "vertical"),
    "business model": ("classification", "business_model"),
    "archetype": ("classification", "archetype"),
    "stage": ("classification", "stage"),
    "growth stage": ("classification", "stage"),
    "location": ("geography", "_location_text"),
    "service area": ("geography", "_service_area_text"),
    "service areas": ("geography", "_service_area_text"),
    "geo scope": ("geography", "geo_scope"),
    "geographic scope": ("geography", "geo_scope"),
    "buyer type": ("sales_cycle", "buyer_type"),
    "sales cycle": ("sales_cycle", "sales_cycle_length"),
    "sales cycle length": ("sales_cycle", "sales_cycle_length"),
    "average deal size": ("sales_cycle", "average_deal_size"),
    "deal size": ("sales_cycle", "average_deal_size"),
    "monthly budget": ("budget", "monthly_marketing_budget"),
    "marketing budget": ("budget", "monthly_marketing_budget"),
    "risk tolerance": ("budget", "risk_tolerance"),
    "years in business": ("trust", "years_in_business"),
    "team size": ("trust", "team_size"),
    "north star metric": ("goals", "north_star_metric"),
    "north star": ("goals", "north_star_metric"),
    "timeframe": ("goals", "timeframe"),
    "brand voice": ("brand_voice", "_voice_text"),
    "tone": ("brand_voice", "_tone_text"),
    "competitor differentiation": ("brand_voice", "competitor_differentiation"),
}

# Heading aliases that trigger list-collection mode.
_MD_HEADING_LIST_MAP: Dict[str, str] = {
    "offers": "offers",
    "services": "offers",
    "products": "offers",
    "target audience": "personas",
    "target customers": "personas",
    "personas": "personas",
    "audience": "personas",
    "goals": "goals",
    "primary goals": "goals",
    "kpis": "goals",
    "channels": "channels",
    "marketing channels": "channels",
    "certifications": "trust_certifications",
    "awards": "trust_awards",
    "licenses": "trust_licenses",
    "constraints": "constraints",
    "compliance": "constraints",
    "topics to avoid": "constraints_avoid",
    "pain points": "persona_pain_points",
    "objections": "persona_objections",
}


def load_from_markdown(file_path: str) -> Dict[str, Any]:
    """Parse a markdown file and extract structured BusinessProfile fields.

    Extracts data from:
        - ``**Key:** Value`` patterns (mapped via ``_MD_KEY_MAP``).
        - H2/H3 headings followed by bullet lists (mapped via
          ``_MD_HEADING_LIST_MAP``).
        - Inline key-value lines like ``Business name: XYZ``.

    Only clearly stated information is extracted.  Ambiguous or
    unrecognized content is silently skipped.

    Parameters
    ----------
    file_path:
        Path to a ``.md`` file containing onboarding notes, interview
        transcripts, or brand documentation.

    Returns
    -------
    Dict[str, Any]
        Partial profile dict with ``_source: "markdown"`` metadata.
    """
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, IOError) as exc:
        return {"_source": "markdown", "_errors": [f"File read error: {exc}"]}

    result: Dict[str, Any] = {"_source": "markdown"}

    # --- Pass 1: extract key-value pairs ------------------------------------
    for match in _KV_PATTERN.finditer(text):
        raw_key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if not value:
            continue
        mapping = _MD_KEY_MAP.get(raw_key)
        if mapping is None:
            continue
        section, field = mapping
        result.setdefault(section, {})[field] = value

    # --- Pass 2: extract heading -> bullet list blocks ----------------------
    sections = _split_by_headings(text)
    for heading, body in sections:
        heading_lower = heading.strip().lower()
        list_key = _MD_HEADING_LIST_MAP.get(heading_lower)
        if list_key is None:
            continue
        bullets = _BULLET_PATTERN.findall(body)
        bullets = [b.strip() for b in bullets if b.strip()]
        if not bullets:
            continue
        _assign_heading_list(result, list_key, bullets)

    # --- Post-process special fields ----------------------------------------
    _postprocess_markdown_fields(result)

    return result


def _split_by_headings(text: str) -> List[tuple]:
    """Split markdown into (heading_text, body_text) pairs.

    Returns a list of tuples.  The body is everything between one heading
    and the next heading of equal or lesser depth (or end of file).
    """
    headings = list(_HEADING_PATTERN.finditer(text))
    if not headings:
        return []

    sections: List[tuple] = []
    for i, match in enumerate(headings):
        heading_text = match.group(2).strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        sections.append((heading_text, body))
    return sections


def _assign_heading_list(
    result: Dict[str, Any], list_key: str, bullets: List[str]
) -> None:
    """Place extracted bullet items into the correct profile location."""
    if list_key == "offers":
        result.setdefault("offers", []).extend(
            {"name": b} for b in bullets
        )
    elif list_key == "personas":
        result.setdefault("personas", []).extend(
            {"name": b} for b in bullets
        )
    elif list_key == "goals":
        result.setdefault("goals", {}).setdefault("primary_goals", []).extend(bullets)
    elif list_key == "channels":
        result.setdefault("channels", []).extend(
            {"platform": b, "is_active": True} for b in bullets
        )
    elif list_key == "trust_certifications":
        result.setdefault("trust", {}).setdefault("certifications", []).extend(bullets)
    elif list_key == "trust_awards":
        result.setdefault("trust", {}).setdefault("awards", []).extend(bullets)
    elif list_key == "trust_licenses":
        result.setdefault("trust", {}).setdefault("licenses", []).extend(bullets)
    elif list_key == "constraints":
        result.setdefault("constraints", {}).setdefault(
            "compliance_notes", []
        ).extend(bullets)
    elif list_key == "constraints_avoid":
        result.setdefault("constraints", {}).setdefault(
            "topics_to_avoid", []
        ).extend(bullets)
    elif list_key == "persona_pain_points":
        # Attach to the last persona if one exists, otherwise store raw.
        personas = result.get("personas", [])
        if personas and isinstance(personas[-1], dict):
            personas[-1].setdefault("pain_points", []).extend(bullets)
        else:
            result.setdefault("_raw_pain_points", []).extend(bullets)
    elif list_key == "persona_objections":
        personas = result.get("personas", [])
        if personas and isinstance(personas[-1], dict):
            personas[-1].setdefault("objections", []).extend(bullets)
        else:
            result.setdefault("_raw_objections", []).extend(bullets)


def _postprocess_markdown_fields(result: Dict[str, Any]) -> None:
    """Convert intermediate markdown-specific fields into profile-native ones."""
    # Geography: _location_text -> locations list
    geo = result.get("geography", {})
    if isinstance(geo, dict):
        loc_text = geo.pop("_location_text", None)
        if loc_text:
            geo.setdefault("locations", []).append({"name": loc_text})

        sa_text = geo.pop("_service_area_text", None)
        if sa_text:
            # Split on commas or semicolons.
            areas = [a.strip() for a in re.split(r"[,;]", sa_text) if a.strip()]
            geo.setdefault("service_areas", []).extend(areas)

    # Brand voice intermediate fields.
    bv = result.get("brand_voice", {})
    if isinstance(bv, dict):
        voice_text = bv.pop("_voice_text", None)
        if voice_text:
            bv.setdefault("tone_descriptors", []).append(voice_text)
        tone_text = bv.pop("_tone_text", None)
        if tone_text:
            # Split comma-separated tone words.
            tones = [t.strip() for t in re.split(r"[,;]", tone_text) if t.strip()]
            bv.setdefault("tone_descriptors", []).extend(tones)

    # Numeric coercions.
    _try_coerce_numeric(result, ("sales_cycle", "average_deal_size"), float)
    _try_coerce_numeric(result, ("budget", "monthly_marketing_budget"), float)
    _try_coerce_numeric(result, ("trust", "years_in_business"), int)


def _try_coerce_numeric(
    data: Dict[str, Any], path: tuple, target_type: type
) -> None:
    """Attempt to coerce a nested field to a numeric type in-place."""
    current = data
    for part in path[:-1]:
        current = current.get(part, {})
        if not isinstance(current, dict):
            return
    field = path[-1]
    val = current.get(field)
    if val is None:
        return
    try:
        # Strip common prefixes like $ and commas.
        cleaned = re.sub(r"[$,]", "", str(val).strip())
        current[field] = target_type(cleaned)
    except (ValueError, TypeError):
        pass  # Leave as-is if conversion fails.


# ============================================================================
# Loader: Gateway brand config
# ============================================================================


def load_from_brand_config(brand_config: Dict[str, Any]) -> Dict[str, Any]:
    """Map a gateway-style ``KaiBrandProfile`` dict to profile fields.

    Expected input keys (see ``kai/runtime/models.py`` ``KaiBrandProfile``):
        ``id``, ``name``, ``url``, ``description``, ``primary_archetype``,
        ``archetype_overlays``, ``active_channels``, ``proof_points``,
        ``ga_property``, ``gsc_site``, ``persona_defaults``, ``metadata``.

    Parameters
    ----------
    brand_config:
        A dict matching the ``KaiBrandProfile`` dataclass fields.

    Returns
    -------
    Dict[str, Any]
        Partial profile dict with ``_source: "brand_config"`` metadata.
    """
    if not isinstance(brand_config, dict):
        return {"_source": "brand_config", "_errors": ["brand_config is not a dict"]}

    result: Dict[str, Any] = {"_source": "brand_config"}

    # ID
    if brand_config.get("id"):
        result["id"] = brand_config["id"]

    # Identity
    identity: Dict[str, Any] = {}
    if brand_config.get("name"):
        identity["business_name"] = brand_config["name"]
    if brand_config.get("url"):
        identity["website_url"] = brand_config["url"]
    if brand_config.get("description"):
        identity["elevator_pitch"] = brand_config["description"]
    if identity:
        result["identity"] = identity

    # Classification
    classification: Dict[str, Any] = {}
    if brand_config.get("primary_archetype"):
        classification["archetype"] = brand_config["primary_archetype"]
    if classification:
        result["classification"] = classification

    # Channels from active_channels
    active_channels = brand_config.get("active_channels")
    if active_channels and isinstance(active_channels, list):
        result["channels"] = [
            {"platform": ch, "is_active": True}
            for ch in active_channels
        ]

    # Trust from proof_points
    proof_points = brand_config.get("proof_points")
    if proof_points:
        items = proof_points if isinstance(proof_points, list) else [str(proof_points)]
        result["trust"] = {
            "testimonials": [
                {"signal_type": "statistic", "content": point}
                for point in items
            ],
        }

    # Metadata
    metadata: Dict[str, Any] = {}
    if brand_config.get("archetype_overlays"):
        metadata["archetype_overlays"] = brand_config["archetype_overlays"]
    if brand_config.get("ga_property"):
        metadata["ga_property"] = brand_config["ga_property"]
    if brand_config.get("gsc_site"):
        metadata["gsc_site"] = brand_config["gsc_site"]
    # Merge in any existing metadata from the brand config.
    existing_meta = brand_config.get("metadata")
    if isinstance(existing_meta, dict):
        metadata.update(existing_meta)
    if metadata:
        result["metadata"] = metadata

    return result


# ============================================================================
# Loader: Operator overrides
# ============================================================================


def load_from_overrides(overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Accept a flat or nested dict of override values.

    Supports both direct nested dicts and dot-notation keys such as
    ``"identity.business_name"``.  This is the highest-priority source --
    the operator explicitly declaring "this field is X".

    Parameters
    ----------
    overrides:
        A dictionary of field paths to values.  Dot-notation keys are
        expanded into nested dicts.  Direct nested dicts are passed
        through as-is.

    Returns
    -------
    Dict[str, Any]
        Partial profile dict with ``_source: "overrides"`` metadata.
    """
    if not isinstance(overrides, dict):
        return {"_source": "overrides", "_errors": ["overrides is not a dict"]}

    # Separate dotted keys from nested keys.
    dotted: Dict[str, Any] = {}
    nested: Dict[str, Any] = {}
    for key, value in overrides.items():
        if "." in key:
            dotted[key] = value
        else:
            nested[key] = value

    # Expand dotted keys.
    expanded = flatten_dotted_keys(dotted)

    # Merge expanded dotted keys with direct nested keys.  Nested keys
    # take precedence (they are more explicit).
    result = deep_merge(expanded, nested)
    result["_source"] = "overrides"
    return result


# ============================================================================
# Loader: Form data (stub for future UI)
# ============================================================================


def load_from_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Map UI / form field names to BusinessProfile fields.

    This is a stub interface for future form-based onboarding flows.
    Currently implements mapping for the following form fields:

    Expected form field schema::

        {
            "business_name": str,         -> identity.business_name
            "website": str,               -> identity.website_url
            "phone": str,                 -> identity.phone
            "email": str,                 -> identity.email
            "industry": str,              -> classification.industry
            "business_model": str,        -> classification.business_model
            "archetype": str,             -> classification.archetype
            "stage": str,                 -> classification.stage
            "service_areas": str | list,  -> geography.service_areas
            "location_city": str,         -> geography.locations[0].city
            "location_state": str,        -> geography.locations[0].state
            "primary_offer": str,         -> offers[0].name (is_primary=True)
            "monthly_budget": float,      -> budget.monthly_marketing_budget
            "primary_goal": str,          -> goals.primary_goals[0]
            "buyer_type": str,            -> sales_cycle.buyer_type
            "tone": str | list,           -> brand_voice.tone_descriptors
        }

    Fields not in this mapping are stored in ``metadata.unmapped_form_fields``
    for future processing.

    Parameters
    ----------
    form_data:
        A dictionary of form field names to values.

    Returns
    -------
    Dict[str, Any]
        Partial profile dict with ``_source: "form"`` metadata.
    """
    if not isinstance(form_data, dict):
        return {"_source": "form", "_errors": ["form_data is not a dict"]}

    result: Dict[str, Any] = {"_source": "form"}
    unmapped: Dict[str, Any] = {}

    _FORM_MAP = {
        "business_name": ("identity", "business_name"),
        "website": ("identity", "website_url"),
        "phone": ("identity", "phone"),
        "email": ("identity", "email"),
        "tagline": ("identity", "tagline"),
        "elevator_pitch": ("identity", "elevator_pitch"),
        "industry": ("classification", "industry"),
        "business_model": ("classification", "business_model"),
        "archetype": ("classification", "archetype"),
        "stage": ("classification", "stage"),
        "vertical": ("classification", "vertical"),
        "monthly_budget": ("budget", "monthly_marketing_budget"),
        "risk_tolerance": ("budget", "risk_tolerance"),
        "buyer_type": ("sales_cycle", "buyer_type"),
        "sales_cycle_length": ("sales_cycle", "sales_cycle_length"),
        "competitor_differentiation": ("brand_voice", "competitor_differentiation"),
        "north_star_metric": ("goals", "north_star_metric"),
        "timeframe": ("goals", "timeframe"),
        "years_in_business": ("trust", "years_in_business"),
        "team_size": ("trust", "team_size"),
        "geo_scope": ("geography", "geo_scope"),
    }

    for field_name, value in form_data.items():
        if value is None or value == "":
            continue

        mapping = _FORM_MAP.get(field_name)
        if mapping:
            section, key = mapping
            result.setdefault(section, {})[key] = value
            continue

        # Special multi-value fields.
        if field_name == "service_areas":
            areas = value if isinstance(value, list) else [
                a.strip() for a in str(value).split(",") if a.strip()
            ]
            result.setdefault("geography", {}).setdefault(
                "service_areas", []
            ).extend(areas)
        elif field_name == "location_city":
            result.setdefault("geography", {}).setdefault(
                "locations", [{}]
            )[0]["city"] = value
        elif field_name == "location_state":
            result.setdefault("geography", {}).setdefault(
                "locations", [{}]
            )[0]["state"] = value
        elif field_name == "primary_offer":
            result.setdefault("offers", []).append(
                {"name": value, "is_primary": True}
            )
        elif field_name == "primary_goal":
            result.setdefault("goals", {}).setdefault(
                "primary_goals", []
            ).append(value)
        elif field_name == "tone":
            tones = value if isinstance(value, list) else [
                t.strip() for t in str(value).split(",") if t.strip()
            ]
            result.setdefault("brand_voice", {}).setdefault(
                "tone_descriptors", []
            ).extend(tones)
        elif field_name == "id":
            result["id"] = value
        else:
            unmapped[field_name] = value

    if unmapped:
        result.setdefault("metadata", {})["unmapped_form_fields"] = unmapped

    return result


# ============================================================================
# Merge function
# ============================================================================

# Default priority ordering (index 0 = lowest priority).
_DEFAULT_PRIORITY = ["yaml", "markdown", "brand_config", "form", "overrides"]


def merge_profiles(
    *partials: Dict[str, Any],
    priority_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Merge multiple partial profile dicts into one combined dict.

    Merge rules:
        - **Scalar fields**: higher priority wins.
        - **List fields**: concatenated and deduplicated (by ``name`` key
          for object lists, by value for string lists).
        - **Dict fields**: deep-merged with higher priority overriding
          conflicting scalar keys.
        - Fields prefixed with ``_`` (metadata like ``_source``) are
          collected separately and not merged into profile data.
        - A field that no source provides stays absent in the result.

    Parameters
    ----------
    *partials:
        One or more partial profile dicts.  Each should have a ``_source``
        key indicating its origin (``"yaml"``, ``"markdown"``, etc.).
    priority_order:
        Optional list of source names from lowest to highest priority.
        Defaults to ``["yaml", "markdown", "brand_config", "form",
        "overrides"]``.

    Returns
    -------
    Dict[str, Any]
        A single merged profile dict ready for ``build_profile``.
        Includes ``_merge_metadata`` with source tracking and warnings.
    """
    order = priority_order or _DEFAULT_PRIORITY

    def _priority(partial: Dict[str, Any]) -> int:
        source = partial.get("_source", "")
        try:
            return order.index(source)
        except ValueError:
            return -1  # Unknown sources get lowest priority.

    # Sort partials by priority (lowest first so higher-priority merges last).
    sorted_partials = sorted(partials, key=_priority)

    merged: Dict[str, Any] = {}
    source_map: Dict[str, str] = {}  # field -> source that set it
    warnings: List[str] = []

    for partial in sorted_partials:
        source = partial.get("_source", "unknown")
        clean = {
            k: v for k, v in partial.items() if not k.startswith("_")
        }
        for key, value in clean.items():
            if value is None:
                continue
            old_val = merged.get(key)
            if old_val is not None and old_val != value:
                old_source = source_map.get(key, "unknown")
                # Record the conflict for diagnostics.
                if isinstance(old_val, dict) and isinstance(value, dict):
                    merged[key] = deep_merge(old_val, value)
                elif isinstance(old_val, list) and isinstance(value, list):
                    merged[key] = _dedupe_list(old_val + value)
                else:
                    warnings.append(
                        f"Field '{key}' conflict: '{old_source}' -> "
                        f"'{source}' (higher priority wins)"
                    )
                    merged[key] = copy.deepcopy(value)
            elif old_val is None:
                merged[key] = copy.deepcopy(value)
            # If values are equal, no action needed.
            source_map[key] = source

    # Recursively dedupe all list fields in the merged result.
    _dedupe_all_lists(merged)

    # Attach merge metadata.
    merged["_merge_metadata"] = {
        "sources": [p.get("_source", "unknown") for p in sorted_partials],
        "source_map": source_map,
        "warnings": warnings,
    }

    return merged


def _dedupe_all_lists(d: Dict[str, Any]) -> None:
    """Walk a nested dict and deduplicate all list values in-place."""
    for key, value in d.items():
        if isinstance(value, list):
            d[key] = _dedupe_list(value)
        elif isinstance(value, dict):
            _dedupe_all_lists(value)


# ============================================================================
# Build function
# ============================================================================


def build_profile(
    sources: List[Dict[str, Any]],
    priority_order: Optional[List[str]] = None,
) -> "BusinessProfile":
    """Merge source dicts and instantiate a canonical ``BusinessProfile``.

    This is the high-level entry point: hand it a list of partial dicts
    (from any combination of loaders) and get back a fully validated
    ``BusinessProfile`` instance.

    Parameters
    ----------
    sources:
        A list of partial profile dicts, each produced by one of the
        ``load_from_*`` functions.
    priority_order:
        Optional priority ordering passed through to ``merge_profiles``.

    Returns
    -------
    BusinessProfile
        A fully constructed ``BusinessProfile`` model instance.

    Raises
    ------
    ValueError
        If a required field (``id``, ``identity.business_name``) is
        missing from the merged result.
    TypeError
        If Pydantic validation fails on the merged data.
    """
    from kai.models.business_profile import (
        BusinessClassification,
        BusinessConstraints,
        BusinessGeography,
        BrandVoice,
        BudgetAndRisk,
        BusinessIdentity,
        BusinessProfile,
        BuyerSalesCycle,
        ChannelPresence,
        GoalsAndKPIs,
        Location,
        Offer,
        OperatorCapacity,
        PersonaProfile,
        TrustProfile,
        TrustSignal,
    )

    merged = merge_profiles(*sources, priority_order=priority_order)

    # Strip internal metadata keys before instantiation.
    clean = {k: v for k, v in merged.items() if not k.startswith("_")}

    # --- Validate required fields ------------------------------------------
    if "id" not in clean:
        raise ValueError(
            "Missing required field 'id'.  At least one source must provide "
            "a business identifier."
        )

    identity_raw = clean.get("identity")
    if not identity_raw or not isinstance(identity_raw, dict):
        raise ValueError(
            "Missing required field 'identity'.  At least one source must "
            "provide identity data (business_name at minimum)."
        )
    if "business_name" not in identity_raw:
        raise ValueError(
            "Missing required field 'identity.business_name'.  At least one "
            "source must provide the business name."
        )

    # --- Construct sub-models -----------------------------------------------
    try:
        identity = BusinessIdentity(**identity_raw)
    except TypeError as exc:
        raise TypeError(f"Failed to build BusinessIdentity: {exc}") from exc

    classification = _build_submodel(
        BusinessClassification, clean.get("classification"), "classification"
    )

    offers = _build_list_submodel(Offer, clean.get("offers"), "offers")

    geography = _build_geography(
        BusinessGeography, Location, clean.get("geography")
    )

    personas = _build_list_submodel(
        PersonaProfile, clean.get("personas"), "personas"
    )

    trust = _build_trust(TrustProfile, TrustSignal, clean.get("trust"))

    goals = _build_submodel(GoalsAndKPIs, clean.get("goals"), "goals")

    channels = _build_list_submodel(
        ChannelPresence, clean.get("channels"), "channels"
    )

    constraints = _build_submodel(
        BusinessConstraints, clean.get("constraints"), "constraints"
    )

    budget = _build_submodel(
        BudgetAndRisk, clean.get("budget"), "budget"
    )

    sales_cycle = _build_submodel(
        BuyerSalesCycle, clean.get("sales_cycle"), "sales_cycle"
    )

    brand_voice = _build_submodel(
        BrandVoice, clean.get("brand_voice"), "brand_voice"
    )

    operator = _build_submodel(
        OperatorCapacity, clean.get("operator"), "operator"
    )

    # --- Instantiate the top-level model ------------------------------------
    try:
        profile = BusinessProfile(
            id=clean["id"],
            identity=identity,
            classification=classification,
            offers=offers,
            geography=geography,
            personas=personas,
            trust=trust,
            goals=goals,
            channels=channels,
            constraints=constraints,
            budget=budget,
            sales_cycle=sales_cycle,
            brand_voice=brand_voice,
            operator=operator,
            raw_notes=clean.get("raw_notes"),
            created_at=clean.get("created_at"),
            updated_at=clean.get("updated_at"),
            profile_version=clean.get("profile_version", "1.0.0"),
            metadata=clean.get("metadata", {}),
        )
    except TypeError as exc:
        raise TypeError(f"Failed to build BusinessProfile: {exc}") from exc

    return profile


# ---------------------------------------------------------------------------
# Sub-model construction helpers
# ---------------------------------------------------------------------------


def _build_submodel(model_cls: type, data: Any, field_name: str) -> Any:
    """Construct a sub-model from raw dict data, or return a default instance."""
    if data is None or not isinstance(data, dict):
        return model_cls()
    try:
        return model_cls(**data)
    except TypeError as exc:
        raise TypeError(
            f"Failed to build {model_cls.__name__} for '{field_name}': {exc}"
        ) from exc


def _build_list_submodel(
    model_cls: type, data: Any, field_name: str
) -> list:
    """Construct a list of sub-models from a list of dicts."""
    if data is None or not isinstance(data, list):
        return []
    result = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            try:
                result.append(model_cls(**item))
            except TypeError as exc:
                raise TypeError(
                    f"Failed to build {model_cls.__name__} at "
                    f"'{field_name}[{i}]': {exc}"
                ) from exc
        elif isinstance(item, str):
            # Some lists may contain plain strings from markdown extraction.
            # Try to construct with just a name field.
            try:
                result.append(model_cls(name=item))
            except TypeError:
                pass  # Skip items that cannot be constructed.
    return result


def _build_geography(
    geo_cls: type, location_cls: type, data: Any
) -> Any:
    """Construct BusinessGeography, handling nested Location objects."""
    if data is None or not isinstance(data, dict):
        return geo_cls()
    data = copy.deepcopy(data)
    raw_locations = data.pop("locations", [])
    locations = []
    for loc in raw_locations:
        if isinstance(loc, dict):
            try:
                locations.append(location_cls(**loc))
            except TypeError:
                pass
    try:
        return geo_cls(locations=locations, **data)
    except TypeError as exc:
        raise TypeError(f"Failed to build geography: {exc}") from exc


def _build_trust(
    trust_cls: type, signal_cls: type, data: Any
) -> Any:
    """Construct TrustProfile, handling nested TrustSignal objects."""
    if data is None or not isinstance(data, dict):
        return trust_cls()
    data = copy.deepcopy(data)

    # Convert signal lists.
    for signal_field in ("testimonials", "case_studies"):
        raw_signals = data.get(signal_field)
        if isinstance(raw_signals, list):
            built = []
            for item in raw_signals:
                if isinstance(item, dict):
                    try:
                        built.append(signal_cls(**item))
                    except TypeError:
                        pass
            data[signal_field] = built

    try:
        return trust_cls(**data)
    except TypeError as exc:
        raise TypeError(f"Failed to build trust profile: {exc}") from exc

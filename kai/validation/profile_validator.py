"""Profile validation for the Kai Marketing OS.

Validates a ``BusinessProfile`` against universal requirements and
archetype-specific rules.  Returns structured ``ValidationResult`` objects
that tell downstream consumers exactly what is known, what is missing, and
whether the profile is sufficient for a given operation.

Design principles
-----------------
* **Unknowns preserved** -- missing fields are flagged but NEVER filled with
  defaults, guesses, or hallucinated values.
* **Severity is meaningful** -- ``CRITICAL`` truly blocks meaningful operation;
  ``WARNING`` degrades but does not block; ``INFO`` is nice-to-have.
* **Transparency** -- every validation decision is traceable in the returned
  data structure.
* **Archetype stacking** -- archetype-specific rules ADD to universal rules,
  never override them.

Uses the same Pydantic / stdlib-fallback pattern as ``gateway/models.py``
so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kai.models.business_profile import BusinessProfile

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json
            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Enums
# ============================================================================


class FieldValidationStatus(str, Enum):
    """Status of a single field after validation."""

    PRESENT = "present"
    MISSING = "missing"
    INVALID = "invalid"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class ValidationSeverity(str, Enum):
    """How important a validation finding is."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ============================================================================
# Data Models
# ============================================================================


class FieldValidation(BaseModel):
    """Result of validating a single field."""

    field_path: str
    status: FieldValidationStatus
    severity: ValidationSeverity
    message: str
    value_summary: Optional[str] = None


class ValidationResult(BaseModel):
    """Aggregate result of validating a full BusinessProfile."""

    profile_id: str
    archetype: Optional[str] = None
    timestamp: str
    is_sufficient: bool
    total_fields_checked: int
    present_count: int
    missing_count: int
    invalid_count: int
    critical_issues: List[FieldValidation] = Field(default_factory=list)
    warnings: List[FieldValidation] = Field(default_factory=list)
    info_items: List[FieldValidation] = Field(default_factory=list)
    all_validations: List[FieldValidation] = Field(default_factory=list)
    completeness_score: float = 0.0
    readiness_summary: str = ""


# ============================================================================
# Archetype registry
# ============================================================================

# Maps archetype slugs to their validation functions.  Populated after the
# functions are defined below.
_ARCHETYPE_VALIDATORS: Dict[str, Callable[["BusinessProfile"], List[FieldValidation]]] = {}

# Maps archetype slugs to their requirement dicts.  Populated alongside.
_ARCHETYPE_REQUIREMENTS: Dict[str, Dict[str, ValidationSeverity]] = {}


# ============================================================================
# Internal helpers
# ============================================================================


def _resolve_path(obj: Any, path: str) -> Any:
    """Walk a dot-notation *path* on *obj*, returning the leaf value.

    Returns ``_SENTINEL`` when any segment along the path is ``None`` or
    otherwise missing.  Never raises.
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        if current is None:
            return _SENTINEL
        # Try attribute access first (Pydantic / dataclass), then dict.
        if hasattr(current, part):
            current = getattr(current, part, _SENTINEL)
        elif isinstance(current, dict):
            current = current.get(part, _SENTINEL)
        else:
            return _SENTINEL
        if current is _SENTINEL:
            return _SENTINEL
    return current


class _SentinelType:
    """Unique object used to distinguish 'not found' from ``None``."""

    def __repr__(self) -> str:
        return "<SENTINEL>"


_SENTINEL = _SentinelType()


def _is_empty(value: Any) -> bool:
    """Return ``True`` when *value* should be considered missing/empty.

    * ``None`` -> empty
    * ``_SENTINEL`` -> empty
    * ``""`` (empty string) -> empty
    * ``[]`` (empty list) -> empty
    * ``{}`` (empty dict) -> empty
    * ``0`` (zero numeric) -> NOT empty (zero is a valid value)
    * ``False`` (bool) -> NOT empty (explicit False is a valid value)
    """
    if value is _SENTINEL or value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _summarize_value(value: Any) -> Optional[str]:
    """Return a short human-readable summary of *value* for diagnostics."""
    if value is _SENTINEL or value is None:
        return None
    if isinstance(value, str):
        if len(value) <= 80:
            return value
        return value[:77] + "..."
    if isinstance(value, list):
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return str(value)
    return str(value)[:80]


# ============================================================================
# Core field-check helper
# ============================================================================


def _check_field(
    profile: "BusinessProfile",
    field_path: str,
    severity: ValidationSeverity,
    message: str,
) -> FieldValidation:
    """Check a single field on *profile* using dot-notation *field_path*.

    Navigates the path safely -- if any intermediate object is ``None``,
    all child fields are treated as ``MISSING``.

    Rules:
    * List fields: empty list -> MISSING.
    * String fields: ``None`` or ``""`` -> MISSING.
    * Numeric fields: ``None`` -> MISSING; ``0`` is a valid PRESENT value.
    * Bool fields: PRESENT as long as the attribute exists (even if ``False``).
    * Dict fields: empty dict -> MISSING.

    Returns a ``FieldValidation`` with the appropriate status.
    """
    value = _resolve_path(profile, field_path)

    if _is_empty(value):
        return FieldValidation(
            field_path=field_path,
            status=FieldValidationStatus.MISSING,
            severity=severity,
            message=message,
            value_summary=None,
        )

    return FieldValidation(
        field_path=field_path,
        status=FieldValidationStatus.PRESENT,
        severity=severity,
        message=f"{field_path} is present",
        value_summary=_summarize_value(value),
    )


def _check_either(
    profile: "BusinessProfile",
    paths: List[str],
    severity: ValidationSeverity,
    message: str,
    combined_path: Optional[str] = None,
) -> FieldValidation:
    """Check that at least one of several *paths* is non-empty.

    Returns a PRESENT validation if any path resolves to a non-empty value,
    or a MISSING validation if all are empty.  The ``combined_path`` is used
    as the ``field_path`` in the result; if not supplied it defaults to the
    paths joined with ``" | "``.
    """
    display_path = combined_path or " | ".join(paths)

    for path in paths:
        value = _resolve_path(profile, path)
        if not _is_empty(value):
            return FieldValidation(
                field_path=display_path,
                status=FieldValidationStatus.PRESENT,
                severity=severity,
                message=f"At least one of [{', '.join(paths)}] is present",
                value_summary=_summarize_value(value),
            )

    return FieldValidation(
        field_path=display_path,
        status=FieldValidationStatus.MISSING,
        severity=severity,
        message=message,
        value_summary=None,
    )


# ============================================================================
# Universal validation
# ============================================================================


def _validate_universal(profile: "BusinessProfile") -> List[FieldValidation]:
    """Validate fields required for ANY business, regardless of archetype.

    Returns a list of ``FieldValidation`` items covering:

    * CRITICAL -- ``identity.business_name``
    * CRITICAL -- at least one of ``classification.industry`` /
      ``classification.vertical``
    * WARNING -- ``identity.website_url``
    * WARNING -- at least one of ``identity.phone`` / ``identity.email``
    * WARNING -- at least one offer
    * WARNING -- at least one persona
    * INFO -- ``identity.tagline``
    * INFO -- ``identity.elevator_pitch``
    * INFO -- ``brand_voice.tone_descriptors``
    * INFO -- ``goals.primary_goals``
    * INFO -- ``budget.monthly_marketing_budget``
    """
    results: List[FieldValidation] = []

    # -- CRITICAL --------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "identity.business_name",
            ValidationSeverity.CRITICAL,
            "Business name is required -- every downstream operation depends on it",
        )
    )

    results.append(
        _check_either(
            profile,
            ["classification.industry", "classification.vertical"],
            ValidationSeverity.CRITICAL,
            "At least one of industry or vertical must be set to classify the business",
            combined_path="classification.industry | classification.vertical",
        )
    )

    # -- WARNING ---------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "identity.website_url",
            ValidationSeverity.WARNING,
            "Website URL is needed for most marketing operations (audits, SEO, landing pages)",
        )
    )

    results.append(
        _check_either(
            profile,
            ["identity.phone", "identity.email"],
            ValidationSeverity.WARNING,
            "At least one contact method (phone or email) should be set",
            combined_path="identity.phone | identity.email",
        )
    )

    results.append(
        _check_field(
            profile,
            "offers",
            ValidationSeverity.WARNING,
            "At least one offer (product/service) should be listed for content and ad copy",
        )
    )

    results.append(
        _check_field(
            profile,
            "personas",
            ValidationSeverity.WARNING,
            "At least one target persona should be defined for audience-focused marketing",
        )
    )

    # -- INFO ------------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "identity.tagline",
            ValidationSeverity.INFO,
            "A tagline improves brand consistency across content",
        )
    )

    results.append(
        _check_field(
            profile,
            "identity.elevator_pitch",
            ValidationSeverity.INFO,
            "An elevator pitch helps generate sharper introductions and cold outreach",
        )
    )

    results.append(
        _check_field(
            profile,
            "brand_voice.tone_descriptors",
            ValidationSeverity.INFO,
            "Tone descriptors guide the writing style of all generated content",
        )
    )

    results.append(
        _check_field(
            profile,
            "goals.primary_goals",
            ValidationSeverity.INFO,
            "Primary goals help prioritize recommendations and channel allocation",
        )
    )

    results.append(
        _check_field(
            profile,
            "budget.monthly_marketing_budget",
            ValidationSeverity.INFO,
            "Monthly budget helps scope campaign recommendations and ad spend planning",
        )
    )

    return results


# ============================================================================
# Archetype: local-service
# ============================================================================


def _validate_local_service(profile: "BusinessProfile") -> List[FieldValidation]:
    """Validate fields specific to the ``local-service`` archetype.

    Local service businesses have hard requirements around geography and
    phone-based lead capture.
    """
    results: List[FieldValidation] = []

    # -- CRITICAL --------------------------------------------------------

    results.append(
        _check_either(
            profile,
            ["geography.service_areas", "geography.locations"],
            ValidationSeverity.CRITICAL,
            "Local service businesses must define service areas or physical locations",
            combined_path="geography.service_areas | geography.locations",
        )
    )

    results.append(
        _check_field(
            profile,
            "identity.phone",
            ValidationSeverity.CRITICAL,
            "A phone number is critical for local service businesses -- most leads call",
        )
    )

    # -- WARNING ---------------------------------------------------------

    # At least one location with an address
    locations = _resolve_path(profile, "geography.locations")
    if not _is_empty(locations) and isinstance(locations, list):
        has_address = any(
            not _is_empty(_resolve_path(loc, "address"))
            for loc in locations
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].address",
                status=FieldValidationStatus.PRESENT if has_address else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "At least one location has an address"
                    if has_address
                    else "At least one location should have a full address for local SEO"
                ),
                value_summary=f"[{sum(1 for loc in locations if not _is_empty(_resolve_path(loc, 'address')))} of {len(locations)} with address]" if has_address else None,
            )
        )

        # At least one location with gbp_url
        has_gbp = any(
            not _is_empty(_resolve_path(loc, "gbp_url"))
            for loc in locations
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].gbp_url",
                status=FieldValidationStatus.PRESENT if has_gbp else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "At least one location has a Google Business Profile URL"
                    if has_gbp
                    else "A Google Business Profile URL is important for local visibility"
                ),
                value_summary=f"[{sum(1 for loc in locations if not _is_empty(_resolve_path(loc, 'gbp_url')))} of {len(locations)} with GBP]" if has_gbp else None,
            )
        )
    else:
        results.append(
            FieldValidation(
                field_path="geography.locations[].address",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No locations defined -- cannot check for addresses",
                value_summary=None,
            )
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].gbp_url",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No locations defined -- cannot check for Google Business Profile URLs",
                value_summary=None,
            )
        )

    results.append(
        _check_field(
            profile,
            "trust.years_in_business",
            ValidationSeverity.WARNING,
            "Years in business builds trust for local service providers",
        )
    )

    results.append(
        _check_field(
            profile,
            "trust.licenses",
            ValidationSeverity.WARNING,
            "Licensing information is often required and always trust-building for local services",
        )
    )

    # -- INFO ------------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "trust.insurance_details",
            ValidationSeverity.INFO,
            "Insurance details strengthen trust for in-home or on-site service providers",
        )
    )

    # geography.is_mobile -- check that it was explicitly set (not just default False)
    # Since we cannot distinguish "user set False" from "default False" without metadata,
    # we flag it as INFO suggesting the operator confirm the value.
    is_mobile_value = _resolve_path(profile, "geography.is_mobile")
    results.append(
        FieldValidation(
            field_path="geography.is_mobile",
            status=FieldValidationStatus.PRESENT if is_mobile_value is not _SENTINEL else FieldValidationStatus.MISSING,
            severity=ValidationSeverity.INFO,
            message=(
                f"Mobile service flag is set to {is_mobile_value}"
                if is_mobile_value is not _SENTINEL
                else "Confirm whether this is a mobile service (travels to customer) or storefront"
            ),
            value_summary=str(is_mobile_value) if is_mobile_value is not _SENTINEL else None,
        )
    )

    # At least one offer with price_range
    offers = _resolve_path(profile, "offers")
    if not _is_empty(offers) and isinstance(offers, list):
        has_price = any(
            not _is_empty(_resolve_path(offer, "price_range"))
            for offer in offers
        )
        results.append(
            FieldValidation(
                field_path="offers[].price_range",
                status=FieldValidationStatus.PRESENT if has_price else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.INFO,
                message=(
                    "At least one offer has a price range"
                    if has_price
                    else "Adding price ranges to offers helps generate more specific ad copy and proposals"
                ),
                value_summary=f"[{sum(1 for o in offers if not _is_empty(_resolve_path(o, 'price_range')))} of {len(offers)} with price]" if has_price else None,
            )
        )
    else:
        results.append(
            FieldValidation(
                field_path="offers[].price_range",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.INFO,
                message="No offers defined -- cannot check for price ranges",
                value_summary=None,
            )
        )

    return results


_ARCHETYPE_VALIDATORS["local-service"] = _validate_local_service
_ARCHETYPE_REQUIREMENTS["local-service"] = {
    "geography.service_areas | geography.locations": ValidationSeverity.CRITICAL,
    "identity.phone": ValidationSeverity.CRITICAL,
    "geography.locations[].address": ValidationSeverity.WARNING,
    "geography.locations[].gbp_url": ValidationSeverity.WARNING,
    "trust.years_in_business": ValidationSeverity.WARNING,
    "trust.licenses": ValidationSeverity.WARNING,
    "trust.insurance_details": ValidationSeverity.INFO,
    "geography.is_mobile": ValidationSeverity.INFO,
    "offers[].price_range": ValidationSeverity.INFO,
}


# ============================================================================
# Archetype: ecommerce
# ============================================================================


def _validate_ecommerce(profile: "BusinessProfile") -> List[FieldValidation]:
    """Validate fields specific to the ``ecommerce`` archetype.

    Ecommerce businesses need product offers, a website, and platform
    presence to operate effectively.
    """
    results: List[FieldValidation] = []

    # -- CRITICAL --------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "offers",
            ValidationSeverity.CRITICAL,
            "Ecommerce businesses must have at least one product/offer listed",
        )
    )

    results.append(
        _check_field(
            profile,
            "identity.website_url",
            ValidationSeverity.CRITICAL,
            "A website URL is essential for ecommerce operations",
        )
    )

    # -- WARNING ---------------------------------------------------------

    # At least one offer with price_range
    offers = _resolve_path(profile, "offers")
    if not _is_empty(offers) and isinstance(offers, list):
        has_price = any(
            not _is_empty(_resolve_path(offer, "price_range"))
            for offer in offers
        )
        results.append(
            FieldValidation(
                field_path="offers[].price_range",
                status=FieldValidationStatus.PRESENT if has_price else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "At least one offer has a price range"
                    if has_price
                    else "Price ranges are important for ecommerce ad copy and shopping feed optimization"
                ),
                value_summary=f"[{sum(1 for o in offers if not _is_empty(_resolve_path(o, 'price_range')))} of {len(offers)} with price]" if has_price else None,
            )
        )
    else:
        results.append(
            FieldValidation(
                field_path="offers[].price_range",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No offers defined -- cannot check for price ranges",
                value_summary=None,
            )
        )

    results.append(
        _check_field(
            profile,
            "sales_cycle.buyer_type",
            ValidationSeverity.WARNING,
            "Buyer type (B2C, D2C, etc.) shapes ad targeting and messaging strategy",
        )
    )

    # At least one channel is an ecommerce platform
    _ECOMMERCE_PLATFORMS = {
        "shopify", "woocommerce", "bigcommerce", "magento", "squarespace",
        "amazon", "ebay", "etsy", "walmart", "tiktok shop", "instagram shop",
        "facebook shop", "google shopping",
    }
    channels = _resolve_path(profile, "channels")
    if not _is_empty(channels) and isinstance(channels, list):
        has_ecommerce_channel = any(
            getattr(ch, "platform", "").lower().strip() in _ECOMMERCE_PLATFORMS
            or (isinstance(ch, dict) and ch.get("platform", "").lower().strip() in _ECOMMERCE_PLATFORMS)
            for ch in channels
        )
        results.append(
            FieldValidation(
                field_path="channels[].platform",
                status=FieldValidationStatus.PRESENT if has_ecommerce_channel else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "At least one ecommerce platform channel is connected"
                    if has_ecommerce_channel
                    else "No ecommerce platform channel found -- consider adding Shopify, Amazon, etc."
                ),
                value_summary=None,
            )
        )
    else:
        results.append(
            FieldValidation(
                field_path="channels[].platform",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No channels defined -- cannot check for ecommerce platform presence",
                value_summary=None,
            )
        )

    results.append(
        _check_field(
            profile,
            "goals.target_kpis",
            ValidationSeverity.WARNING,
            "Target KPIs (ROAS, AOV, conversion rate) are needed for ecommerce optimization",
        )
    )

    # -- INFO ------------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "brand_voice.tone_descriptors",
            ValidationSeverity.INFO,
            "Tone descriptors help maintain brand consistency across product listings and ads",
        )
    )

    results.append(
        _check_field(
            profile,
            "trust.testimonials",
            ValidationSeverity.INFO,
            "Customer testimonials strengthen product pages and ad social proof",
        )
    )

    return results


_ARCHETYPE_VALIDATORS["ecommerce"] = _validate_ecommerce
_ARCHETYPE_REQUIREMENTS["ecommerce"] = {
    "offers": ValidationSeverity.CRITICAL,
    "identity.website_url": ValidationSeverity.CRITICAL,
    "offers[].price_range": ValidationSeverity.WARNING,
    "sales_cycle.buyer_type": ValidationSeverity.WARNING,
    "channels[].platform": ValidationSeverity.WARNING,
    "goals.target_kpis": ValidationSeverity.WARNING,
    "brand_voice.tone_descriptors": ValidationSeverity.INFO,
    "trust.testimonials": ValidationSeverity.INFO,
}


# ============================================================================
# Archetype: professional-services
# ============================================================================


def _validate_professional_services(profile: "BusinessProfile") -> List[FieldValidation]:
    """Validate fields specific to the ``professional-services`` archetype.

    Professional services rely on credibility signals, case studies, and
    a clear understanding of the buyer's decision process.
    """
    results: List[FieldValidation] = []

    # -- CRITICAL --------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "offers",
            ValidationSeverity.CRITICAL,
            "Professional services businesses must describe at least one service offering",
        )
    )

    # -- WARNING ---------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "trust.case_studies",
            ValidationSeverity.WARNING,
            "Case studies are the strongest trust signal for professional services",
        )
    )

    results.append(
        _check_field(
            profile,
            "trust.certifications",
            ValidationSeverity.WARNING,
            "Certifications validate expertise and are often decision-making factors",
        )
    )

    # At least one persona with decision_makers info
    # decision_makers lives on BuyerSalesCycle, not PersonaProfile -- but the
    # task spec asks for "personas has at least one item with decision_makers
    # info".  We interpret this as: the profile has personas AND the sales_cycle
    # has decision_makers defined, since PersonaProfile does not carry a
    # decision_makers field.
    personas = _resolve_path(profile, "personas")
    decision_makers = _resolve_path(profile, "sales_cycle.decision_makers")
    has_personas_and_dm = (
        not _is_empty(personas) and not _is_empty(decision_makers)
    )
    results.append(
        FieldValidation(
            field_path="personas + sales_cycle.decision_makers",
            status=FieldValidationStatus.PRESENT if has_personas_and_dm else FieldValidationStatus.MISSING,
            severity=ValidationSeverity.WARNING,
            message=(
                "Target personas and decision-maker roles are defined"
                if has_personas_and_dm
                else "Define target personas AND decision-maker roles for effective B2B messaging"
            ),
            value_summary=None,
        )
    )

    results.append(
        _check_field(
            profile,
            "sales_cycle.sales_cycle_length",
            ValidationSeverity.WARNING,
            "Sales cycle length determines nurture sequence depth and follow-up cadence",
        )
    )

    # -- INFO ------------------------------------------------------------

    results.append(
        _check_field(
            profile,
            "trust.notable_clients",
            ValidationSeverity.INFO,
            "Notable clients serve as powerful social proof on proposals and landing pages",
        )
    )

    results.append(
        _check_field(
            profile,
            "brand_voice.competitor_differentiation",
            ValidationSeverity.INFO,
            "Competitor differentiation sharpens positioning and ad copy",
        )
    )

    return results


_ARCHETYPE_VALIDATORS["professional-services"] = _validate_professional_services
_ARCHETYPE_REQUIREMENTS["professional-services"] = {
    "offers": ValidationSeverity.CRITICAL,
    "trust.case_studies": ValidationSeverity.WARNING,
    "trust.certifications": ValidationSeverity.WARNING,
    "personas + sales_cycle.decision_makers": ValidationSeverity.WARNING,
    "sales_cycle.sales_cycle_length": ValidationSeverity.WARNING,
    "trust.notable_clients": ValidationSeverity.INFO,
    "brand_voice.competitor_differentiation": ValidationSeverity.INFO,
}


# ============================================================================
# Archetype: multi-location
# ============================================================================


def _validate_multi_location(profile: "BusinessProfile") -> List[FieldValidation]:
    """Validate fields specific to the ``multi-location`` archetype.

    Multi-location businesses need at least 2 locations with complete data
    for each, plus brand consistency controls.
    """
    results: List[FieldValidation] = []

    # -- CRITICAL --------------------------------------------------------

    locations = _resolve_path(profile, "geography.locations")
    location_count = len(locations) if isinstance(locations, list) else 0
    results.append(
        FieldValidation(
            field_path="geography.locations",
            status=FieldValidationStatus.PRESENT if location_count >= 2 else FieldValidationStatus.MISSING,
            severity=ValidationSeverity.CRITICAL,
            message=(
                f"{location_count} locations defined"
                if location_count >= 2
                else f"Multi-location archetype requires at least 2 locations (found {location_count})"
            ),
            value_summary=f"[{location_count} locations]" if location_count > 0 else None,
        )
    )

    # -- WARNING ---------------------------------------------------------

    if isinstance(locations, list) and location_count > 0:
        # Every location should have address and phone
        locs_with_address = sum(
            1 for loc in locations if not _is_empty(_resolve_path(loc, "address"))
        )
        locs_with_phone = sum(
            1 for loc in locations if not _is_empty(_resolve_path(loc, "phone"))
        )
        all_have_address_phone = (
            locs_with_address == location_count and locs_with_phone == location_count
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].address + phone",
                status=FieldValidationStatus.PRESENT if all_have_address_phone else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "All locations have address and phone"
                    if all_have_address_phone
                    else f"Not all locations have address and phone ({locs_with_address}/{location_count} addresses, {locs_with_phone}/{location_count} phones)"
                ),
                value_summary=f"[{locs_with_address} addresses, {locs_with_phone} phones out of {location_count}]",
            )
        )

        # Every location should have gbp_url
        locs_with_gbp = sum(
            1 for loc in locations if not _is_empty(_resolve_path(loc, "gbp_url"))
        )
        all_have_gbp = locs_with_gbp == location_count
        results.append(
            FieldValidation(
                field_path="geography.locations[].gbp_url",
                status=FieldValidationStatus.PRESENT if all_have_gbp else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message=(
                    "All locations have a Google Business Profile URL"
                    if all_have_gbp
                    else f"Only {locs_with_gbp}/{location_count} locations have a Google Business Profile URL"
                ),
                value_summary=f"[{locs_with_gbp}/{location_count} with GBP]",
            )
        )

        # Each location should have hours (INFO)
        locs_with_hours = sum(
            1 for loc in locations if not _is_empty(_resolve_path(loc, "hours"))
        )
        all_have_hours = locs_with_hours == location_count
        results.append(
            FieldValidation(
                field_path="geography.locations[].hours",
                status=FieldValidationStatus.PRESENT if all_have_hours else FieldValidationStatus.MISSING,
                severity=ValidationSeverity.INFO,
                message=(
                    "All locations have hours set"
                    if all_have_hours
                    else f"Only {locs_with_hours}/{location_count} locations have hours defined"
                ),
                value_summary=f"[{locs_with_hours}/{location_count} with hours]",
            )
        )
    else:
        results.append(
            FieldValidation(
                field_path="geography.locations[].address + phone",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No locations defined -- cannot verify address and phone per location",
                value_summary=None,
            )
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].gbp_url",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.WARNING,
                message="No locations defined -- cannot verify GBP URLs per location",
                value_summary=None,
            )
        )
        results.append(
            FieldValidation(
                field_path="geography.locations[].hours",
                status=FieldValidationStatus.MISSING,
                severity=ValidationSeverity.INFO,
                message="No locations defined -- cannot verify hours per location",
                value_summary=None,
            )
        )

    results.append(
        _check_field(
            profile,
            "brand_voice.tone_descriptors",
            ValidationSeverity.WARNING,
            "Brand voice tone descriptors ensure consistency across multiple locations",
        )
    )

    return results


_ARCHETYPE_VALIDATORS["multi-location"] = _validate_multi_location
_ARCHETYPE_REQUIREMENTS["multi-location"] = {
    "geography.locations": ValidationSeverity.CRITICAL,
    "geography.locations[].address + phone": ValidationSeverity.WARNING,
    "geography.locations[].gbp_url": ValidationSeverity.WARNING,
    "brand_voice.tone_descriptors": ValidationSeverity.WARNING,
    "geography.locations[].hours": ValidationSeverity.INFO,
}


# ============================================================================
# Archetype requirement lookup
# ============================================================================


def get_archetype_requirements(archetype: str) -> Dict[str, ValidationSeverity]:
    """Return a dict mapping field paths to their severity for *archetype*.

    Useful for UIs that want to show which fields are most important to
    fill for a given archetype.

    If the archetype is not recognized, returns an empty dict.
    """
    return dict(_ARCHETYPE_REQUIREMENTS.get(archetype, {}))


# ============================================================================
# Main entry point
# ============================================================================


def _generate_readiness_summary(
    is_sufficient: bool,
    completeness_score: float,
    critical_count: int,
    warning_count: int,
    info_count: int,
    archetype: Optional[str],
) -> str:
    """Build a one-sentence human-readable readiness summary."""
    archetype_label = f" for the {archetype} archetype" if archetype else ""

    if not is_sufficient:
        return (
            f"Profile is NOT ready{archetype_label}: "
            f"{critical_count} critical issue{'s' if critical_count != 1 else ''} "
            f"must be resolved before the system can operate meaningfully "
            f"({completeness_score:.0%} complete)."
        )

    if warning_count == 0 and info_count == 0:
        return (
            f"Profile is fully ready{archetype_label} with no issues "
            f"({completeness_score:.0%} complete)."
        )

    parts: List[str] = []
    if warning_count > 0:
        parts.append(
            f"{warning_count} warning{'s' if warning_count != 1 else ''} that may degrade output quality"
        )
    if info_count > 0:
        parts.append(
            f"{info_count} optional field{'s' if info_count != 1 else ''} that would improve results"
        )

    return (
        f"Profile is ready{archetype_label} but has {' and '.join(parts)} "
        f"({completeness_score:.0%} complete)."
    )


def validate_profile(
    profile: "BusinessProfile",
    archetype: Optional[str] = None,
) -> ValidationResult:
    """Validate a ``BusinessProfile`` and return a structured ``ValidationResult``.

    Parameters
    ----------
    profile:
        The profile to validate.  If ``None``, returns a result with a single
        CRITICAL issue.
    archetype:
        The archetype to validate against.  If ``None``, the function
        attempts to read ``profile.classification.archetype``.  If that is
        also ``None``, only universal rules are applied.

    Returns
    -------
    ValidationResult
        A complete validation report including per-field status, severity
        breakdown, completeness score, and a human-readable readiness summary.
    """
    now = datetime.now(timezone.utc).isoformat()

    # -- Handle None profile ---------------------------------------------
    if profile is None:
        null_issue = FieldValidation(
            field_path="<profile>",
            status=FieldValidationStatus.MISSING,
            severity=ValidationSeverity.CRITICAL,
            message="The profile object itself is None -- nothing can be validated",
            value_summary=None,
        )
        return ValidationResult(
            profile_id="<unknown>",
            archetype=archetype,
            timestamp=now,
            is_sufficient=False,
            total_fields_checked=1,
            present_count=0,
            missing_count=1,
            invalid_count=0,
            critical_issues=[null_issue],
            warnings=[],
            info_items=[],
            all_validations=[null_issue],
            completeness_score=0.0,
            readiness_summary="Profile is None -- no validation possible.",
        )

    # -- Resolve archetype -----------------------------------------------
    resolved_archetype = archetype
    if resolved_archetype is None:
        classification_archetype = _resolve_path(profile, "classification.archetype")
        if not _is_empty(classification_archetype):
            resolved_archetype = str(classification_archetype)

    # -- Run universal validation ----------------------------------------
    all_validations: List[FieldValidation] = _validate_universal(profile)

    # -- Run archetype-specific validation -------------------------------
    unrecognized_archetype = False
    if resolved_archetype is not None:
        validator = _ARCHETYPE_VALIDATORS.get(resolved_archetype)
        if validator is not None:
            all_validations.extend(validator(profile))
        else:
            unrecognized_archetype = True
            all_validations.append(
                FieldValidation(
                    field_path="classification.archetype",
                    status=FieldValidationStatus.PRESENT,
                    severity=ValidationSeverity.INFO,
                    message=f"Archetype '{resolved_archetype}' is not recognized -- only universal rules were applied",
                    value_summary=resolved_archetype,
                )
            )

    # -- Compute aggregates -----------------------------------------------
    total = len(all_validations)
    present = sum(1 for v in all_validations if v.status == FieldValidationStatus.PRESENT)
    missing = sum(1 for v in all_validations if v.status == FieldValidationStatus.MISSING)
    invalid = sum(1 for v in all_validations if v.status == FieldValidationStatus.INVALID)

    critical_issues = [
        v for v in all_validations
        if v.severity == ValidationSeverity.CRITICAL and v.status != FieldValidationStatus.PRESENT
    ]
    warnings = [
        v for v in all_validations
        if v.severity == ValidationSeverity.WARNING and v.status != FieldValidationStatus.PRESENT
    ]
    info_items = [
        v for v in all_validations
        if v.severity == ValidationSeverity.INFO and v.status != FieldValidationStatus.PRESENT
    ]

    completeness = present / total if total > 0 else 0.0
    is_sufficient = len(critical_issues) == 0

    # -- Profile ID ------------------------------------------------------
    profile_id = str(_resolve_path(profile, "id"))
    if profile_id == repr(_SENTINEL):
        profile_id = "<unknown>"

    readiness_summary = _generate_readiness_summary(
        is_sufficient=is_sufficient,
        completeness_score=completeness,
        critical_count=len(critical_issues),
        warning_count=len(warnings),
        info_count=len(info_items),
        archetype=resolved_archetype if not unrecognized_archetype else None,
    )

    return ValidationResult(
        profile_id=profile_id,
        archetype=resolved_archetype,
        timestamp=now,
        is_sufficient=is_sufficient,
        total_fields_checked=total,
        present_count=present,
        missing_count=missing,
        invalid_count=invalid,
        critical_issues=critical_issues,
        warnings=warnings,
        info_items=info_items,
        all_validations=all_validations,
        completeness_score=completeness,
        readiness_summary=readiness_summary,
    )

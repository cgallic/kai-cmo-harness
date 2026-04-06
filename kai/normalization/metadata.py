"""Business metadata normalization for the Kai Marketing OS.

Normalizes industry verticals, business models, archetypes, and growth
stages into canonical identifiers that the archetype-activation and
audit systems consume.

Examples
--------
>>> normalize_industry("home improvement")
'home_services'
>>> normalize_business_model("services")
'service'
>>> normalize_archetype("ecom")
'ecommerce'
>>> normalize_stage("startup")
'early-pmf'
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Industry aliases  (lowercased variant -> canonical)
# ---------------------------------------------------------------------------

INDUSTRY_ALIASES: dict[str, str] = {
    # Home services
    "home services": "home_services",
    "home improvement": "home_services",
    "residential services": "home_services",
    "home service": "home_services",
    "hvac": "home_services",
    "plumbing": "home_services",
    "electrical": "home_services",
    "roofing": "home_services",
    "landscaping": "home_services",
    "cleaning": "home_services",
    "pest control": "home_services",
    # Legal
    "legal": "legal",
    "law": "legal",
    "law firm": "legal",
    "attorney": "legal",
    "legal services": "legal",
    "lawyer": "legal",
    # Healthcare
    "healthcare": "healthcare",
    "medical": "healthcare",
    "health": "healthcare",
    "health care": "healthcare",
    "dental": "healthcare",
    "dentist": "healthcare",
    "chiropractic": "healthcare",
    "veterinary": "healthcare",
    "optometry": "healthcare",
    # Real estate
    "real estate": "real_estate",
    "realty": "real_estate",
    "property": "real_estate",
    "real-estate": "real_estate",
    "property management": "real_estate",
    # Restaurant / Food & Beverage
    "restaurant": "restaurant",
    "food service": "restaurant",
    "food & beverage": "restaurant",
    "f&b": "restaurant",
    "food and beverage": "restaurant",
    "cafe": "restaurant",
    "bar": "restaurant",
    "catering": "restaurant",
    # Ecommerce
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "online retail": "ecommerce",
    "dtc": "ecommerce",
    "d2c": "ecommerce",
    "retail": "ecommerce",
    "ecom": "ecommerce",
    # SaaS / Software
    "saas": "saas",
    "software": "saas",
    "tech": "saas",
    "technology": "saas",
    # Fitness / Wellness
    "fitness": "fitness",
    "gym": "fitness",
    "wellness": "fitness",
    "health & fitness": "fitness",
    "health and fitness": "fitness",
    "personal training": "fitness",
    "yoga": "fitness",
    # Beauty
    "beauty": "beauty",
    "salon": "beauty",
    "spa": "beauty",
    "aesthetics": "beauty",
    "cosmetics": "beauty",
    "barbershop": "beauty",
    # Automotive
    "automotive": "automotive",
    "auto": "automotive",
    "car dealership": "automotive",
    "auto repair": "automotive",
    "auto body": "automotive",
    "car wash": "automotive",
    # Financial services
    "financial services": "financial_services",
    "finance": "financial_services",
    "fintech": "financial_services",
    "banking": "financial_services",
    "insurance": "financial_services",
    "accounting": "financial_services",
    "tax": "financial_services",
    # Education
    "education": "education",
    "edtech": "education",
    "training": "education",
    "tutoring": "education",
    "online courses": "education",
    # Construction
    "construction": "construction",
    "contracting": "construction",
    "general contractor": "construction",
    "builder": "construction",
    # Professional services
    "professional services": "professional_services",
    "consulting": "professional_services",
    "consultancy": "professional_services",
    "advisory": "professional_services",
    # Agency
    "agency": "agency",
    "marketing agency": "agency",
    "digital agency": "agency",
    "creative agency": "agency",
    "ad agency": "agency",
    # Nonprofit
    "nonprofit": "nonprofit",
    "non-profit": "nonprofit",
    "ngo": "nonprofit",
    "not-for-profit": "nonprofit",
    "charity": "nonprofit",
}

# ---------------------------------------------------------------------------
# Business model aliases
# ---------------------------------------------------------------------------

BUSINESS_MODEL_ALIASES: dict[str, str] = {
    "service": "service",
    "services": "service",
    "service-based": "service",
    "service based": "service",
    "product": "product",
    "products": "product",
    "product-based": "product",
    "product based": "product",
    "hybrid": "hybrid",
    "mixed": "hybrid",
    "marketplace": "marketplace",
    "platform": "marketplace",
    "saas": "saas",
    "software": "saas",
    "subscription": "saas",
    "agency": "agency",
    "agencies": "agency",
}

# ---------------------------------------------------------------------------
# Archetype aliases
# ---------------------------------------------------------------------------

ARCHETYPE_ALIASES: dict[str, str] = {
    "local-service": "local-service",
    "local service": "local-service",
    "local": "local-service",
    "local-services": "local-service",
    "ecommerce": "ecommerce",
    "e-commerce": "ecommerce",
    "ecom": "ecommerce",
    "online store": "ecommerce",
    "professional-services": "professional-services",
    "professional services": "professional-services",
    "professional": "professional-services",
    "b2b services": "professional-services",
    "multi-location": "multi-location",
    "multi location": "multi-location",
    "multiple locations": "multi-location",
    "franchise": "multi-location",
    "creator": "creator",
    "personal brand": "creator",
    "influencer": "creator",
    "content creator": "creator",
    "saas": "saas",
    "software": "saas",
}

# ---------------------------------------------------------------------------
# Stage aliases
# ---------------------------------------------------------------------------

STAGE_ALIASES: dict[str, str] = {
    "pre-launch": "pre-launch",
    "pre launch": "pre-launch",
    "prelaunch": "pre-launch",
    "idea": "pre-launch",
    "new": "pre-launch",
    "early-pmf": "early-pmf",
    "early pmf": "early-pmf",
    "startup": "early-pmf",
    "start-up": "early-pmf",
    "early": "early-pmf",
    "early stage": "early-pmf",
    "seed": "early-pmf",
    "growth": "growth",
    "growing": "growth",
    "expansion": "growth",
    "series a": "growth",
    "scale": "scale",
    "scaling": "scale",
    "series b": "scale",
    "series c": "scale",
    "mature": "mature",
    "established": "mature",
    "enterprise": "mature",
    "legacy": "mature",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_industry(raw: Optional[str]) -> Optional[str]:
    """Map a raw industry name to its canonical identifier.

    Case-insensitive matching.  Returns the input lowercased with spaces
    replaced by underscores if no alias matches.

    Parameters
    ----------
    raw : str or None
        Industry name as entered by the user.

    Returns
    -------
    str or None
        Canonical industry identifier, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_industry("home improvement")
    'home_services'
    >>> normalize_industry("Law Firm")
    'legal'
    >>> normalize_industry("SaaS")
    'saas'
    >>> normalize_industry("Widgets")
    'widgets'
    >>> normalize_industry(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = INDUSTRY_ALIASES.get(key)
    if canonical is not None:
        return canonical

    return key.replace(" ", "_")


def normalize_business_model(raw: Optional[str]) -> Optional[str]:
    """Normalize a business model string to one of the canonical values:
    ``"service"``, ``"product"``, ``"hybrid"``, ``"marketplace"``,
    ``"saas"``, ``"agency"``.

    Parameters
    ----------
    raw : str or None
        Business model description.

    Returns
    -------
    str or None
        Canonical business model, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_business_model("services")
    'service'
    >>> normalize_business_model("SaaS")
    'saas'
    >>> normalize_business_model("Products")
    'product'
    >>> normalize_business_model(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = BUSINESS_MODEL_ALIASES.get(key)
    if canonical is not None:
        return canonical

    return key.replace(" ", "_")


def normalize_archetype(raw: Optional[str]) -> Optional[str]:
    """Normalize a business archetype to one of the canonical values:
    ``"local-service"``, ``"ecommerce"``, ``"professional-services"``,
    ``"multi-location"``, ``"creator"``, ``"saas"``.

    Parameters
    ----------
    raw : str or None
        Archetype description.

    Returns
    -------
    str or None
        Canonical archetype, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_archetype("local service")
    'local-service'
    >>> normalize_archetype("e-commerce")
    'ecommerce'
    >>> normalize_archetype("franchise")
    'multi-location'
    >>> normalize_archetype(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = ARCHETYPE_ALIASES.get(key)
    if canonical is not None:
        return canonical

    return key.replace(" ", "_")


def normalize_stage(raw: Optional[str]) -> Optional[str]:
    """Normalize a growth stage to one of the canonical values:
    ``"pre-launch"``, ``"early-pmf"``, ``"growth"``, ``"scale"``,
    ``"mature"``.

    Parameters
    ----------
    raw : str or None
        Growth stage description.

    Returns
    -------
    str or None
        Canonical stage, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_stage("startup")
    'early-pmf'
    >>> normalize_stage("scaling")
    'scale'
    >>> normalize_stage("established")
    'mature'
    >>> normalize_stage("new")
    'pre-launch'
    >>> normalize_stage(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = STAGE_ALIASES.get(key)
    if canonical is not None:
        return canonical

    return key.replace(" ", "_")

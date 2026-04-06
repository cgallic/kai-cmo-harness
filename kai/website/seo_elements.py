"""On-page SEO, schema markup, trust-block, and internal-linking generators.

Generates title tags, meta descriptions, Open Graph tags, JSON-LD schema
markup (7 types), HTML-ready trust blocks, and internal linking
recommendations from BusinessProfile data.  All output is structured and
ready for injection into pages via CMS connectors.

No external dependencies beyond the Python standard library.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


# ===================================================================
# Constants
# ===================================================================

TITLE_MAX_CHARS = 60
TITLE_MIN_CHARS = 30

META_DESC_MAX_CHARS = 160
META_DESC_MIN_CHARS = 120

SCHEMA_CONTEXT = "https://schema.org"

PAGE_TYPES = [
    "homepage",
    "service_page",
    "service_area_page",
    "contact_page",
    "about_page",
    "blog_post",
    "product_page",
    "faq_page",
    "testimonials_page",
    "gallery_page",
    "team_page",
]


# ===================================================================
# Internal helpers
# ===================================================================

def _safe_get(d: Any, *keys: str, default: Any = "") -> Any:
    """Drill into nested dicts safely, returning *default* on any miss."""
    current = d
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current if current is not None else default


def _truncate(text: str, max_chars: int) -> tuple:
    """Truncate *text* to at most *max_chars*, breaking at a word boundary.

    Returns ``(truncated_text, was_truncated)``.
    """
    if len(text) <= max_chars:
        return text, False
    cut = text[:max_chars]
    # Step back to the last space so we do not break mid-word
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:
        cut = cut[:last_space]
    return cut.rstrip(" .,;:-"), True


def _strip_html(text: str) -> str:
    """Remove HTML tags from *text*."""
    return re.sub(r"<[^>]+>", "", text).strip()


def _keyword_position(title: str, keyword: str) -> Optional[int]:
    """Return the character index of *keyword* in *title*, case-insensitive."""
    if not keyword:
        return None
    idx = title.lower().find(keyword.lower())
    return idx if idx >= 0 else None


# ===================================================================
# Title / Meta generators
# ===================================================================

def generate_title_tag(
    page_type: str,
    profile: Dict[str, Any],
    target_keyword: Optional[str] = None,
    service: Optional[Dict[str, Any]] = None,
    area: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an SEO-optimized title tag.

    Uses page-type-specific patterns, places the target keyword near the
    beginning, appends the business name, and enforces the 60-char limit
    with intelligent truncation.

    Parameters
    ----------
    page_type:
        One of :data:`PAGE_TYPES`.
    profile:
        BusinessProfile dict (identity, geography, trust, offers, channels).
    target_keyword:
        Primary keyword to target.  Overrides the default pattern when set.
    service:
        Optional service dict with ``name``, ``description``, ``category``.
    area:
        Optional geographic area name.

    Returns
    -------
    dict
        ``{"title", "char_count", "keyword_position", "truncated"}``
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or "Business"
    city = _safe_get(profile, "geography", "primary_city") or _safe_get(profile, "identity", "city") or ""
    primary_service = _safe_get(profile, "identity", "primary_service") or _safe_get(profile, "primary_service") or ""
    year_founded = _safe_get(profile, "identity", "year_founded") or _safe_get(profile, "year_founded") or ""
    service_name = _safe_get(service, "name") if service else primary_service
    area_name = area or city

    # Build the raw title based on page type
    ptype = (page_type or "homepage").lower().replace("-", "_").replace(" ", "_")

    if target_keyword:
        # When a keyword is explicitly provided, lead with it
        raw = f"{target_keyword} | {biz_name}"
    elif ptype == "homepage":
        if primary_service and city:
            raw = f"{primary_service} in {city} | {biz_name}"
        elif primary_service:
            raw = f"{primary_service} | {biz_name}"
        else:
            raw = biz_name
    elif ptype == "service_page":
        if service_name and city:
            raw = f"{service_name} \u2014 {city} | {biz_name}"
        elif service_name:
            raw = f"{service_name} | {biz_name}"
        else:
            raw = f"Services | {biz_name}"
    elif ptype == "service_area_page":
        if service_name and area_name:
            raw = f"{service_name} in {area_name} \u2014 {biz_name}"
        elif area_name:
            raw = f"{area_name} | {biz_name}"
        else:
            raw = f"Service Area | {biz_name}"
    elif ptype == "contact_page":
        quote_service = service_name or "Service"
        raw = f"Contact {biz_name} | Free {quote_service} Quote"
    elif ptype == "about_page":
        since = f" Since {year_founded}" if year_founded else ""
        service_label = f" {primary_service}" if primary_service else ""
        raw = f"About {biz_name} \u2014 {city}{service_label}{since}"
    elif ptype == "blog_post":
        keyword = target_keyword or "Blog"
        raw = f"{keyword} \u2014 {biz_name}"
    elif ptype == "product_page":
        product_name = _safe_get(service, "name") if service else "Product"
        category = _safe_get(service, "category") if service else ""
        if category:
            raw = f"{product_name} | {category} | {biz_name}"
        else:
            raw = f"{product_name} | {biz_name}"
    elif ptype == "faq_page":
        svc = service_name or primary_service or "Our"
        raw = f"{svc} FAQs \u2014 Answers from {biz_name}"
    else:
        raw = f"{biz_name}"

    # Enforce max length
    title, truncated = _truncate(raw, TITLE_MAX_CHARS)

    return {
        "title": title,
        "char_count": len(title),
        "keyword_position": _keyword_position(title, target_keyword or service_name or primary_service),
        "truncated": truncated,
    }


def generate_meta_description(
    page_type: str,
    profile: Dict[str, Any],
    target_keyword: Optional[str] = None,
    service: Optional[Dict[str, Any]] = None,
    area: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an SEO-optimized meta description (120-160 chars).

    Includes a call to action, trust signal, and phone number for local
    service businesses when available.

    Parameters
    ----------
    page_type:
        One of :data:`PAGE_TYPES`.
    profile:
        BusinessProfile dict.
    target_keyword:
        Primary keyword to include naturally.
    service:
        Optional service dict.
    area:
        Optional geographic area name.

    Returns
    -------
    dict
        ``{"description", "char_count", "includes_keyword", "includes_cta",
        "includes_phone"}``
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or "Business"
    city = _safe_get(profile, "geography", "primary_city") or _safe_get(profile, "identity", "city") or ""
    phone = _safe_get(profile, "identity", "phone") or _safe_get(profile, "phone") or ""
    primary_service = _safe_get(profile, "identity", "primary_service") or _safe_get(profile, "primary_service") or ""
    service_name = _safe_get(service, "name") if service else primary_service
    area_name = area or city
    elevator_pitch = _safe_get(profile, "identity", "elevator_pitch") or ""

    # Trust signals
    years = _safe_get(profile, "trust", "years_in_business") or ""
    review_count = _safe_get(profile, "trust", "review_count") or ""
    rating = _safe_get(profile, "trust", "average_rating") or ""
    trust_signal = ""
    if years and int(str(years)) >= 5:
        trust_signal = f"{years}+ years of experience."
    elif review_count and rating:
        trust_signal = f"Rated {rating}/5 from {review_count} reviews."
    elif review_count:
        trust_signal = f"{review_count}+ five-star reviews."

    phone_cta = f" Call {phone}" if phone else ""
    phone_suffix = f"{phone_cta} for a free estimate." if phone else " Request a free quote online."

    ptype = (page_type or "homepage").lower().replace("-", "_").replace(" ", "_")

    if ptype == "homepage":
        svc = service_name or "services"
        raw = f"Looking for {svc} in {city}? {biz_name} offers expert {svc}."
        if trust_signal:
            raw += f" {trust_signal}"
        raw += phone_suffix
    elif ptype == "service_page":
        svc = service_name or "service"
        raw = f"Professional {svc} in {city}. {trust_signal}".rstrip()
        raw += f" Free estimates \u2014{phone_cta} or request a quote online."
    elif ptype == "service_area_page":
        svc = service_name or "service"
        raw = f"Need {svc} in {area_name}? {biz_name} serves {area_name} and surrounding communities."
        if trust_signal:
            raw += f" {trust_signal}"
        raw += phone_suffix
    elif ptype == "contact_page":
        svc = service_name or "service"
        raw = f"Get a free {svc} quote from {biz_name}.{phone_cta}, email, or fill out our form. We respond fast."
    elif ptype == "about_page":
        years_text = f"{years}+ years of" if years else ""
        svc = service_name or "service"
        raw = f"Learn about {biz_name}"
        if years_text:
            raw += f" \u2014 {years_text} {svc} in {city}."
        else:
            raw += f" \u2014 your trusted {svc} provider in {city}."
    elif ptype == "blog_post":
        kw = target_keyword or "tips"
        raw = f"Read about {kw} from {biz_name}. Practical advice you can use today."
        if trust_signal:
            raw += f" {trust_signal}"
    elif ptype == "product_page":
        product_name = _safe_get(service, "name") if service else "our products"
        raw = f"Shop {product_name} from {biz_name}. Quality guaranteed."
        if phone:
            raw += f" Questions? Call {phone}."
    elif ptype == "faq_page":
        svc = service_name or "service"
        raw = f"Get answers to common {svc} questions from {biz_name}. Expert guidance from a team you can trust."
    elif ptype == "testimonials_page":
        raw = f"See what customers say about {biz_name}. {trust_signal}" if trust_signal else f"See what customers say about {biz_name}."
    else:
        raw = elevator_pitch if elevator_pitch else f"{biz_name} \u2014 your trusted partner."

    # Enforce length range
    desc, _ = _truncate(raw, META_DESC_MAX_CHARS)

    includes_keyword = bool(target_keyword and target_keyword.lower() in desc.lower())
    includes_cta = bool(re.search(r"(?:call|visit|learn|request|shop|get|see|read|fill|email)", desc, re.IGNORECASE))
    includes_phone = bool(phone and phone in desc)

    return {
        "description": desc,
        "char_count": len(desc),
        "includes_keyword": includes_keyword,
        "includes_cta": includes_cta,
        "includes_phone": includes_phone,
    }


def generate_og_tags(
    page_type: str,
    profile: Dict[str, Any],
    title: str,
    description: str,
    page_url: Optional[str] = None,
    image_url: Optional[str] = None,
) -> Dict[str, str]:
    """Generate Open Graph tags for social sharing.

    Parameters
    ----------
    page_type:
        Page type string.
    profile:
        BusinessProfile dict.
    title:
        Pre-computed title string.
    description:
        Pre-computed meta description string.
    page_url:
        Canonical URL of the page.
    image_url:
        URL of the hero/social image. Falls back to logo.

    Returns
    -------
    dict
        Keys: ``og:title``, ``og:description``, ``og:type``, ``og:url``,
        ``og:image``, ``og:site_name``, ``og:locale``.
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or ""
    logo = _safe_get(profile, "identity", "logo_url") or ""
    website = _safe_get(profile, "identity", "website_url") or ""

    ptype = (page_type or "").lower().replace("-", "_").replace(" ", "_")
    og_type_map = {
        "blog_post": "article",
        "product_page": "product",
    }
    og_type = og_type_map.get(ptype, "website")

    og_image = image_url or logo or ""

    return {
        "og:title": title,
        "og:description": description,
        "og:type": og_type,
        "og:url": page_url or website or "",
        "og:image": og_image,
        "og:site_name": biz_name,
        "og:locale": "en_US",
    }


# ===================================================================
# Schema markup generators
# ===================================================================

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BUSINESS_SUBTYPE_MAP = {
    "plumbing": "Plumber",
    "plumber": "Plumber",
    "electrical": "Electrician",
    "electrician": "Electrician",
    "hvac": "HVACBusiness",
    "heating": "HVACBusiness",
    "cooling": "HVACBusiness",
    "dental": "Dentist",
    "dentist": "Dentist",
    "legal": "Attorney",
    "lawyer": "Attorney",
    "attorney": "Attorney",
    "law firm": "Attorney",
    "restaurant": "Restaurant",
    "food": "Restaurant",
    "cafe": "Restaurant",
    "real estate": "RealEstateAgent",
    "realtor": "RealEstateAgent",
    "roofing": "RoofingContractor",
    "roofer": "RoofingContractor",
    "locksmith": "Locksmith",
    "auto": "AutoRepair",
    "mechanic": "AutoRepair",
    "auto repair": "AutoRepair",
    "insurance": "InsuranceAgency",
    "accounting": "AccountingService",
    "accountant": "AccountingService",
    "beauty": "BeautySalon",
    "salon": "BeautySalon",
    "spa": "DaySpa",
    "veterinary": "VeterinaryCare",
    "vet": "VeterinaryCare",
    "fitness": "HealthClub",
    "gym": "HealthClub",
    "moving": "MovingCompany",
    "mover": "MovingCompany",
    "cleaning": "HousePainter",
    "painting": "HousePainter",
    "pest control": "PestControlService",
    "exterminator": "PestControlService",
    "photography": "Photographer",
    "photographer": "Photographer",
}


def _determine_business_subtype(profile: Dict[str, Any]) -> str:
    """Map business vertical/industry to a schema.org LocalBusiness subtype.

    Inspects ``profile.identity.industry``, ``profile.identity.vertical``,
    ``profile.identity.primary_service``, and ``profile.identity.category``
    for keyword matches against known schema.org subtypes.

    Returns ``"LocalBusiness"`` if no specific match is found.
    """
    candidates = [
        _safe_get(profile, "identity", "industry"),
        _safe_get(profile, "identity", "vertical"),
        _safe_get(profile, "identity", "primary_service"),
        _safe_get(profile, "identity", "category"),
        _safe_get(profile, "industry"),
        _safe_get(profile, "vertical"),
        _safe_get(profile, "primary_service"),
    ]
    combined = " ".join(str(c).lower() for c in candidates if c)

    for keyword, subtype in _BUSINESS_SUBTYPE_MAP.items():
        if keyword in combined:
            return subtype

    return "LocalBusiness"


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_TIME_RE = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?",
)


def _parse_time(time_str: str) -> str:
    """Normalise a human time string to HH:MM (24-h) for schema.org."""
    m = _TIME_RE.search(time_str)
    if not m:
        return time_str.strip()
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def _format_opening_hours(hours: Dict[str, str]) -> List[Dict[str, Any]]:
    """Convert a human-readable hours dict to schema.org openingHoursSpecification.

    Input example::

        {"Monday": "8am-5pm", "Tuesday": "8:00 AM - 5:00 PM", "Sunday": "Closed"}

    Returns a list of ``OpeningHoursSpecification`` dicts.
    """
    specs: List[Dict[str, Any]] = []
    for day, value in hours.items():
        day_title = day.strip().title()
        if day_title not in _DAY_NAMES:
            continue
        val_lower = value.strip().lower()

        if val_lower in ("closed", ""):
            continue

        if "24" in val_lower and "hour" in val_lower:
            specs.append({
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": day_title,
                "opens": "00:00",
                "closes": "23:59",
            })
            continue

        # Try to split on common delimiters
        parts = re.split(r"\s*[-\u2013\u2014to]+\s*", value.strip(), maxsplit=1)
        if len(parts) == 2:
            specs.append({
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": day_title,
                "opens": _parse_time(parts[0]),
                "closes": _parse_time(parts[1]),
            })
        else:
            # Cannot parse -- skip gracefully
            pass

    return specs


def _validate_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Check a schema dict for required fields and return a report.

    Returns ``{"valid": bool, "missing_fields": [...], "warnings": [...]}``
    """
    missing: List[str] = []
    warnings: List[str] = []

    if "@context" not in schema:
        missing.append("@context")
    if "@type" not in schema:
        missing.append("@type")
    if not schema.get("name"):
        missing.append("name")

    schema_type = schema.get("@type", "")
    if schema_type in ("LocalBusiness", "Organization") and not schema.get("address"):
        warnings.append("Missing 'address' field (recommended for LocalBusiness/Organization).")
    if schema_type == "LocalBusiness" and not schema.get("telephone"):
        warnings.append("Missing 'telephone' field (recommended for LocalBusiness).")
    if schema_type == "Product" and not schema.get("offers"):
        warnings.append("Missing 'offers' field (recommended for Product).")

    return {
        "valid": len(missing) == 0,
        "missing_fields": missing,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Schema generators
# ---------------------------------------------------------------------------

def generate_local_business_schema(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a complete LocalBusiness JSON-LD schema from a BusinessProfile.

    Populates all available fields: name, url, telephone, email, logo,
    image, description, address, geo, openingHoursSpecification,
    areaServed, aggregateRating, review, sameAs, priceRange,
    paymentAccepted, and hasMap.

    Parameters
    ----------
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        Valid JSON-LD dict ready for ``<script type="application/ld+json">``.
    """
    biz_type = _determine_business_subtype(profile)

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": biz_type,
        "name": _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or "",
    }

    # Basic identity
    url = _safe_get(profile, "identity", "website_url") or _safe_get(profile, "website_url")
    if url:
        schema["url"] = url
        schema["@id"] = url

    phone = _safe_get(profile, "identity", "phone") or _safe_get(profile, "phone")
    if phone:
        schema["telephone"] = phone

    email = _safe_get(profile, "identity", "email") or _safe_get(profile, "email")
    if email:
        schema["email"] = email

    logo = _safe_get(profile, "identity", "logo_url") or _safe_get(profile, "logo_url")
    if logo:
        schema["logo"] = logo
        schema["image"] = logo

    hero_image = _safe_get(profile, "identity", "hero_image_url")
    if hero_image:
        schema["image"] = hero_image

    pitch = _safe_get(profile, "identity", "elevator_pitch") or _safe_get(profile, "description")
    if pitch:
        schema["description"] = pitch

    # Address
    location = _safe_get(profile, "geography", "primary_location") or _safe_get(profile, "location") or {}
    if not isinstance(location, dict):
        location = {}
    address_parts: Dict[str, Any] = {"@type": "PostalAddress"}
    street = location.get("street") or location.get("address") or _safe_get(profile, "identity", "address")
    city = location.get("city") or _safe_get(profile, "geography", "primary_city") or _safe_get(profile, "identity", "city")
    state = location.get("state") or _safe_get(profile, "geography", "state") or _safe_get(profile, "identity", "state")
    zipcode = location.get("zip") or location.get("postal_code") or _safe_get(profile, "identity", "zip")
    country = location.get("country") or "US"

    if street:
        address_parts["streetAddress"] = street
    if city:
        address_parts["addressLocality"] = city
    if state:
        address_parts["addressRegion"] = state
    if zipcode:
        address_parts["postalCode"] = str(zipcode)
    address_parts["addressCountry"] = country

    if any(k in address_parts for k in ("streetAddress", "addressLocality")):
        schema["address"] = address_parts

    # Geo coordinates
    lat = location.get("lat") or location.get("latitude")
    lng = location.get("lng") or location.get("longitude")
    if lat and lng:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": float(lat),
            "longitude": float(lng),
        }

    # Opening hours
    hours = location.get("hours") or _safe_get(profile, "identity", "hours")
    if isinstance(hours, dict) and hours:
        specs = _format_opening_hours(hours)
        if specs:
            schema["openingHoursSpecification"] = specs

    # Area served
    service_areas = _safe_get(profile, "geography", "service_areas")
    if isinstance(service_areas, list) and service_areas:
        schema["areaServed"] = [
            {"@type": "City", "name": a} if isinstance(a, str) else a
            for a in service_areas
        ]

    # Aggregate rating from testimonials
    testimonials = _safe_get(profile, "trust", "testimonials")
    if isinstance(testimonials, list) and testimonials:
        ratings = []
        for t in testimonials:
            r = t.get("rating")
            if r is not None:
                try:
                    ratings.append(float(r))
                except (ValueError, TypeError):
                    pass
        if ratings:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": round(sum(ratings) / len(ratings), 1),
                "reviewCount": len(ratings),
                "bestRating": 5,
                "worstRating": 1,
            }

        # Include first 5 reviews
        reviews_out: List[Dict[str, Any]] = []
        for t in testimonials[:5]:
            review: Dict[str, Any] = {"@type": "Review"}
            author = t.get("author") or t.get("name") or "Customer"
            review["author"] = {"@type": "Person", "name": author}
            body = t.get("text") or t.get("body") or t.get("review") or ""
            if body:
                review["reviewBody"] = _strip_html(str(body))
            if t.get("rating") is not None:
                review["reviewRating"] = {
                    "@type": "Rating",
                    "ratingValue": t["rating"],
                    "bestRating": 5,
                    "worstRating": 1,
                }
            if t.get("date"):
                review["datePublished"] = str(t["date"])
            reviews_out.append(review)
        if reviews_out:
            schema["review"] = reviews_out

    # Social profiles
    channels = _safe_get(profile, "channels") or {}
    if isinstance(channels, dict):
        same_as: List[str] = []
        for key in ("facebook", "instagram", "twitter", "linkedin", "youtube",
                     "tiktok", "pinterest", "yelp", "google_business"):
            val = channels.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                same_as.append(val)
        if same_as:
            schema["sameAs"] = same_as

    # Price range
    offers = _safe_get(profile, "offers")
    if isinstance(offers, list) and offers:
        price_range = offers[0].get("price_range") if isinstance(offers[0], dict) else None
        if price_range:
            schema["priceRange"] = str(price_range)
    elif isinstance(offers, dict):
        pr = offers.get("price_range")
        if pr:
            schema["priceRange"] = str(pr)

    # Payment accepted
    payment = _safe_get(profile, "identity", "payment_accepted") or _safe_get(profile, "payment_accepted")
    if payment:
        schema["paymentAccepted"] = payment

    # Map link
    maps_url = _safe_get(profile, "identity", "google_maps_url") or location.get("maps_url")
    if maps_url:
        schema["hasMap"] = maps_url

    return schema


def generate_service_schema(
    service: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a Service JSON-LD schema.

    Parameters
    ----------
    service:
        Service dict with ``name``, ``description``, ``category``, ``price_range``.
    profile:
        BusinessProfile dict for provider information.

    Returns
    -------
    dict
        JSON-LD dict.
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or ""
    url = _safe_get(profile, "identity", "website_url") or _safe_get(profile, "website_url") or ""

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Service",
        "name": service.get("name", ""),
    }

    desc = service.get("description", "")
    if desc:
        schema["description"] = _strip_html(str(desc))

    schema["provider"] = {
        "@type": _determine_business_subtype(profile),
        "name": biz_name,
    }
    if url:
        schema["provider"]["@id"] = url

    service_areas = _safe_get(profile, "geography", "service_areas")
    if isinstance(service_areas, list) and service_areas:
        schema["areaServed"] = [
            {"@type": "City", "name": a} if isinstance(a, str) else a
            for a in service_areas
        ]

    # Offers
    price_range = service.get("price_range") or service.get("priceRange")
    if price_range:
        schema["offers"] = {
            "@type": "Offer",
            "priceSpecification": {
                "@type": "PriceSpecification",
                "priceCurrency": "USD",
            },
            "description": str(price_range),
        }

    svc_type = service.get("category") or service.get("serviceType") or service.get("name", "")
    if svc_type:
        schema["serviceType"] = svc_type

    return schema


def generate_product_schema(
    product: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a Product JSON-LD schema.

    Parameters
    ----------
    product:
        Product dict with ``name``, ``description``, ``image``, ``sku``,
        ``price``, ``currency``, ``availability``, ``url``, ``reviews``.
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        JSON-LD dict.
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or ""

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Product",
        "name": product.get("name", ""),
    }

    desc = product.get("description", "")
    if desc:
        schema["description"] = _strip_html(str(desc))

    image = product.get("image") or product.get("image_url")
    if image:
        schema["image"] = image

    sku = product.get("sku")
    if sku:
        schema["sku"] = str(sku)

    # Offers
    price = product.get("price")
    if price is not None:
        offer: Dict[str, Any] = {
            "@type": "Offer",
            "price": str(price),
            "priceCurrency": product.get("currency", "USD"),
        }
        availability = product.get("availability", "InStock")
        offer["availability"] = f"https://schema.org/{availability}"
        prod_url = product.get("url")
        if prod_url:
            offer["url"] = prod_url
        schema["offers"] = offer

    # Aggregate rating
    reviews = product.get("reviews")
    if isinstance(reviews, list) and reviews:
        ratings = [float(r.get("rating", 0)) for r in reviews if r.get("rating")]
        if ratings:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": round(sum(ratings) / len(ratings), 1),
                "reviewCount": len(ratings),
                "bestRating": 5,
                "worstRating": 1,
            }

    # Brand
    if biz_name:
        schema["brand"] = {
            "@type": "Organization",
            "name": biz_name,
        }

    return schema


def generate_faq_schema(faqs: List[Dict[str, str]]) -> Dict[str, Any]:
    """Generate a FAQPage JSON-LD schema.

    Parameters
    ----------
    faqs:
        List of ``{"question": str, "answer": str}`` dicts.

    Returns
    -------
    dict
        JSON-LD dict following the FAQPage specification.
    """
    entities: List[Dict[str, Any]] = []
    for faq in faqs:
        q = faq.get("question", "")
        a = faq.get("answer", "")
        if not q:
            continue
        entities.append({
            "@type": "Question",
            "name": _strip_html(q),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": _strip_html(a),
            },
        })

    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "FAQPage",
        "mainEntity": entities,
    }


def generate_howto_schema(
    title: str,
    steps: List[Dict[str, str]],
    total_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a HowTo JSON-LD schema.

    Parameters
    ----------
    title:
        Title of the how-to guide.
    steps:
        List of ``{"name": str, "text": str, "image": Optional[str]}`` dicts.
    total_time:
        ISO 8601 duration (e.g. ``"PT30M"``).

    Returns
    -------
    dict
        JSON-LD dict.
    """
    step_objects: List[Dict[str, Any]] = []
    for idx, step in enumerate(steps, 1):
        s: Dict[str, Any] = {
            "@type": "HowToStep",
            "position": idx,
            "name": step.get("name", f"Step {idx}"),
            "text": _strip_html(step.get("text", "")),
        }
        image = step.get("image")
        if image:
            s["image"] = image
        step_objects.append(s)

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "HowTo",
        "name": title,
        "step": step_objects,
    }

    if total_time:
        schema["totalTime"] = total_time

    return schema


def generate_organization_schema(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an Organization JSON-LD schema for about pages.

    Parameters
    ----------
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        JSON-LD dict.
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or ""
    url = _safe_get(profile, "identity", "website_url") or _safe_get(profile, "website_url") or ""
    logo = _safe_get(profile, "identity", "logo_url") or _safe_get(profile, "logo_url") or ""
    pitch = _safe_get(profile, "identity", "elevator_pitch") or _safe_get(profile, "description") or ""

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Organization",
        "name": biz_name,
    }

    if url:
        schema["url"] = url
    if logo:
        schema["logo"] = logo
    if pitch:
        schema["description"] = pitch

    # Founding date
    year_founded = _safe_get(profile, "identity", "year_founded") or _safe_get(profile, "year_founded")
    if year_founded:
        schema["foundingDate"] = str(year_founded)

    # Founders
    founders = _safe_get(profile, "identity", "founders") or _safe_get(profile, "founders")
    if isinstance(founders, list) and founders:
        schema["founder"] = [
            {"@type": "Person", "name": f} if isinstance(f, str) else f
            for f in founders
        ]
    elif isinstance(founders, str) and founders:
        schema["founder"] = {"@type": "Person", "name": founders}

    # Team size
    team_size = _safe_get(profile, "identity", "team_size") or _safe_get(profile, "team_size")
    if team_size:
        schema["numberOfEmployees"] = {
            "@type": "QuantitativeValue",
            "value": team_size,
        }

    # Address (reuse logic)
    location = _safe_get(profile, "geography", "primary_location") or _safe_get(profile, "location") or {}
    if isinstance(location, dict):
        address_parts: Dict[str, Any] = {"@type": "PostalAddress"}
        if location.get("city"):
            address_parts["addressLocality"] = location["city"]
        if location.get("state"):
            address_parts["addressRegion"] = location["state"]
        if location.get("street") or location.get("address"):
            address_parts["streetAddress"] = location.get("street") or location.get("address")
        if len(address_parts) > 1:
            schema["address"] = address_parts

    # Contact point
    phone = _safe_get(profile, "identity", "phone") or _safe_get(profile, "phone")
    email_addr = _safe_get(profile, "identity", "email") or _safe_get(profile, "email")
    if phone or email_addr:
        cp: Dict[str, Any] = {"@type": "ContactPoint", "contactType": "customer service"}
        if phone:
            cp["telephone"] = phone
        if email_addr:
            cp["email"] = email_addr
        schema["contactPoint"] = cp

    # Social profiles
    channels = _safe_get(profile, "channels") or {}
    if isinstance(channels, dict):
        same_as: List[str] = []
        for key in ("facebook", "instagram", "twitter", "linkedin", "youtube",
                     "tiktok", "pinterest", "yelp"):
            val = channels.get(key)
            if val and isinstance(val, str) and val.startswith("http"):
                same_as.append(val)
        if same_as:
            schema["sameAs"] = same_as

    return schema


def generate_review_schema(
    testimonials: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate AggregateRating + Review JSON-LD.

    Computes the average rating from testimonials and includes up to 5
    individual Review objects.

    Parameters
    ----------
    testimonials:
        List of testimonial dicts with ``author``/``name``, ``rating``,
        ``text``/``body``, and optional ``date``.
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        JSON-LD dict with AggregateRating and Review objects.
    """
    biz_name = _safe_get(profile, "identity", "business_name") or _safe_get(profile, "business_name") or ""
    url = _safe_get(profile, "identity", "website_url") or _safe_get(profile, "website_url") or ""

    ratings: List[float] = []
    for t in testimonials:
        r = t.get("rating")
        if r is not None:
            try:
                ratings.append(float(r))
            except (ValueError, TypeError):
                pass

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": _determine_business_subtype(profile),
        "name": biz_name,
    }
    if url:
        schema["url"] = url

    if ratings:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": round(sum(ratings) / len(ratings), 1),
            "reviewCount": len(ratings),
            "bestRating": 5,
            "worstRating": 1,
        }

    reviews_out: List[Dict[str, Any]] = []
    for t in testimonials[:5]:
        review: Dict[str, Any] = {"@type": "Review"}
        author = t.get("author") or t.get("name") or "Customer"
        review["author"] = {"@type": "Person", "name": author}
        body = t.get("text") or t.get("body") or t.get("review") or ""
        if body:
            review["reviewBody"] = _strip_html(str(body))
        if t.get("rating") is not None:
            review["reviewRating"] = {
                "@type": "Rating",
                "ratingValue": t["rating"],
                "bestRating": 5,
                "worstRating": 1,
            }
        if t.get("date"):
            review["datePublished"] = str(t["date"])
        reviews_out.append(review)

    if reviews_out:
        schema["review"] = reviews_out

    return schema


# ===================================================================
# Trust block generators
# ===================================================================

def generate_trust_block(
    profile: Dict[str, Any],
    block_style: str = "horizontal",
) -> Dict[str, Any]:
    """Generate an HTML-ready trust block from BusinessProfile trust signals.

    Selects up to 5 trust items in priority order: years in business,
    review count + rating, projects completed, certifications, licenses,
    guarantee, response time, and team size.

    Parameters
    ----------
    profile:
        BusinessProfile dict.
    block_style:
        ``"horizontal"`` (single row), ``"grid"`` (2x2 or 2x3),
        ``"vertical"`` (stacked).

    Returns
    -------
    dict
        ``{"items", "block_style", "html_suggestion", "css_class"}``
    """
    items: List[Dict[str, Any]] = []
    trust = _safe_get(profile, "trust") or {}
    if not isinstance(trust, dict):
        trust = {}
    identity = _safe_get(profile, "identity") or {}
    if not isinstance(identity, dict):
        identity = {}

    # 1. Years in business
    years = trust.get("years_in_business") or identity.get("years_in_business")
    if years:
        try:
            y = int(years)
            if y >= 5:
                items.append({
                    "icon_suggestion": "clock",
                    "text": f"{y}+ Years of Experience",
                    "value": str(y),
                    "source": "trust.years_in_business",
                })
        except (ValueError, TypeError):
            pass

    # 2. Review count + rating
    review_count = trust.get("review_count") or trust.get("total_reviews")
    avg_rating = trust.get("average_rating") or trust.get("rating")
    if review_count:
        text = f"{review_count} Five-Star Reviews"
        if avg_rating:
            text = f"{review_count} Reviews ({avg_rating}/5)"
        items.append({
            "icon_suggestion": "star",
            "text": text,
            "value": str(review_count),
            "source": "trust.review_count",
        })

    # 3. Projects completed
    projects = trust.get("projects_completed") or trust.get("jobs_completed")
    if projects:
        items.append({
            "icon_suggestion": "check",
            "text": f"{projects}+ Projects Completed",
            "value": str(projects),
            "source": "trust.projects_completed",
        })

    # 4. Certifications
    certs = trust.get("certifications") or trust.get("certificates") or []
    if isinstance(certs, list):
        for cert in certs[:2]:
            cert_name = cert if isinstance(cert, str) else cert.get("name", "")
            if cert_name:
                items.append({
                    "icon_suggestion": "award",
                    "text": f"{cert_name} Certified",
                    "value": None,
                    "source": "trust.certifications",
                })

    # 5. Licensed & insured
    licensed = trust.get("licensed") or trust.get("insured")
    if licensed:
        items.append({
            "icon_suggestion": "shield",
            "text": "Licensed & Insured",
            "value": None,
            "source": "trust.licensed",
        })

    # 6. Guarantee
    guarantee = trust.get("guarantee") or trust.get("satisfaction_guarantee")
    if guarantee:
        guar_text = guarantee if isinstance(guarantee, str) else "Satisfaction Guaranteed"
        items.append({
            "icon_suggestion": "shield",
            "text": guar_text,
            "value": None,
            "source": "trust.guarantee",
        })

    # 7. Response time
    response_time = trust.get("response_time") or identity.get("response_time")
    if response_time:
        items.append({
            "icon_suggestion": "clock",
            "text": f"We Respond Within {response_time}",
            "value": str(response_time),
            "source": "trust.response_time",
        })

    # 8. Team size
    team_size = identity.get("team_size") or trust.get("team_size")
    if team_size:
        items.append({
            "icon_suggestion": "users",
            "text": f"{team_size}-Person Team",
            "value": str(team_size),
            "source": "identity.team_size",
        })

    # Cap at 5 items
    items = items[:5]

    # CSS class
    style_lower = block_style.lower()
    css_class_map = {
        "horizontal": "trust-bar trust-bar--horizontal",
        "grid": "trust-bar trust-bar--grid",
        "vertical": "trust-bar trust-bar--vertical",
    }
    css_class = css_class_map.get(style_lower, "trust-bar")

    # Build HTML suggestion
    item_html_parts: List[str] = []
    for item in items:
        icon = item.get("icon_suggestion", "check")
        text = item.get("text", "")
        item_html_parts.append(
            f'  <div class="trust-item">'
            f'<span class="trust-icon">{icon}</span>'
            f'<span class="trust-text">{text}</span>'
            f'</div>'
        )
    inner = "\n".join(item_html_parts)
    html_suggestion = f'<div class="{css_class}">\n{inner}\n</div>' if items else ""

    return {
        "items": items,
        "block_style": block_style,
        "html_suggestion": html_suggestion,
        "css_class": css_class,
    }


def generate_credentials_section(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a credentials/certifications section.

    Includes certifications, licenses, awards, insurance details, and
    professional memberships drawn from the BusinessProfile trust data.

    Parameters
    ----------
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        ``{"heading", "items", "html_suggestion"}``
    """
    trust = _safe_get(profile, "trust") or {}
    if not isinstance(trust, dict):
        trust = {}

    cred_items: List[Dict[str, Any]] = []

    # Certifications
    certs = trust.get("certifications") or []
    if isinstance(certs, list):
        for c in certs:
            name = c if isinstance(c, str) else c.get("name", "")
            if name:
                cred_items.append({"type": "certification", "text": name, "icon": "award"})

    # Licenses
    licenses = trust.get("licenses") or []
    if isinstance(licenses, list):
        for lic in licenses:
            name = lic if isinstance(lic, str) else lic.get("name", "")
            if name:
                cred_items.append({"type": "license", "text": name, "icon": "shield"})
    elif trust.get("licensed"):
        cred_items.append({"type": "license", "text": "Licensed Professional", "icon": "shield"})

    # Awards
    awards = trust.get("awards") or []
    if isinstance(awards, list):
        for a in awards:
            name = a if isinstance(a, str) else a.get("name", "")
            if name:
                cred_items.append({"type": "award", "text": name, "icon": "award"})

    # Insurance
    insurance = trust.get("insurance") or trust.get("insured")
    if insurance:
        ins_text = insurance if isinstance(insurance, str) else "Fully Insured"
        cred_items.append({"type": "insurance", "text": ins_text, "icon": "shield"})

    # Professional memberships
    memberships = trust.get("memberships") or trust.get("professional_memberships") or []
    if isinstance(memberships, list):
        for m in memberships:
            name = m if isinstance(m, str) else m.get("name", "")
            if name:
                cred_items.append({"type": "membership", "text": name, "icon": "users"})

    # Build HTML
    li_parts: List[str] = []
    for item in cred_items:
        li_parts.append(
            f'  <li class="credential-item credential-item--{item["type"]}">'
            f'<span class="credential-icon">{item["icon"]}</span> '
            f'{item["text"]}</li>'
        )
    inner = "\n".join(li_parts)
    html_suggestion = (
        '<section class="credentials-section">\n'
        '  <h2>Our Credentials</h2>\n'
        f'  <ul class="credentials-list">\n{inner}\n  </ul>\n'
        '</section>'
    ) if cred_items else ""

    return {
        "heading": "Our Credentials",
        "items": cred_items,
        "html_suggestion": html_suggestion,
    }


def generate_social_proof_bar(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a compact social proof bar highlighting review-platform ratings.

    Focuses on Google, Yelp, Facebook, and BBB ratings.

    Parameters
    ----------
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        ``{"items", "html_suggestion"}``
    """
    trust = _safe_get(profile, "trust") or {}
    if not isinstance(trust, dict):
        trust = {}
    platforms_data = trust.get("platforms") or trust.get("review_platforms") or {}
    if not isinstance(platforms_data, dict):
        platforms_data = {}

    platform_icons = {
        "google": "star",
        "yelp": "star",
        "facebook": "star",
        "bbb": "shield",
    }

    items: List[Dict[str, Any]] = []
    for platform in ("google", "yelp", "facebook", "bbb"):
        pdata = platforms_data.get(platform) or {}
        if not isinstance(pdata, dict):
            continue
        rating = pdata.get("rating")
        count = pdata.get("count") or pdata.get("review_count")
        if rating is not None:
            items.append({
                "platform": platform.title(),
                "rating": float(rating),
                "count": int(count) if count else 0,
                "icon": platform_icons.get(platform, "star"),
            })

    # Also check top-level fields as fallback
    if not items:
        google_rating = trust.get("google_rating")
        google_count = trust.get("google_review_count")
        if google_rating:
            items.append({
                "platform": "Google",
                "rating": float(google_rating),
                "count": int(google_count) if google_count else 0,
                "icon": "star",
            })

    # Build HTML
    span_parts: List[str] = []
    for item in items:
        count_text = f" ({item['count']} reviews)" if item["count"] else ""
        span_parts.append(
            f'  <span class="social-proof-item social-proof-item--{item["platform"].lower()}">'
            f'{item["platform"]}: {item["rating"]}/5{count_text}'
            f'</span>'
        )
    inner = "\n".join(span_parts)
    html_suggestion = f'<div class="social-proof-bar">\n{inner}\n</div>' if items else ""

    return {
        "items": items,
        "html_suggestion": html_suggestion,
    }


# ===================================================================
# Internal linking
# ===================================================================

def recommend_internal_links(
    current_page: Dict[str, Any],
    site_pages: List[Dict[str, Any]],
    max_links: int = 5,
) -> List[Dict[str, Any]]:
    """Recommend internal links from the current page to other site pages.

    Follows algorithmic authorship rules: no link in the first sentence
    of a paragraph, max 1 link per heading section, and context before link.

    Parameters
    ----------
    current_page:
        Dict with at least ``page_id``, ``page_type``, ``url``, and
        optionally ``services``, ``area``, ``topics``.
    site_pages:
        List of page dicts with the same structure.
    max_links:
        Maximum number of links to recommend.

    Returns
    -------
    list of dict
        Each: ``{"target_page_id", "target_url", "anchor_text", "context",
        "placement_suggestion"}``
    """
    current_id = current_page.get("page_id", "")
    current_type = (current_page.get("page_type", "") or "").lower()
    current_services = set(_coerce_list(current_page.get("services", [])))
    current_area = (current_page.get("area", "") or "").lower()
    current_topics = set(_coerce_list(current_page.get("topics", [])))

    recommendations: List[Dict[str, Any]] = []

    # Score each candidate page
    scored: List[tuple] = []
    for page in site_pages:
        pid = page.get("page_id", "")
        if pid == current_id:
            continue  # never link to self

        ptype = (page.get("page_type", "") or "").lower()
        p_services = set(_coerce_list(page.get("services", [])))
        p_area = (page.get("area", "") or "").lower()
        p_topics = set(_coerce_list(page.get("topics", [])))

        score = 0.0
        reasons: List[str] = []

        # Contact page gets a boost from everywhere
        if ptype == "contact_page":
            score += 3.0
            reasons.append("Contact page should be linked from every page.")

        # Service overlap
        shared_services = current_services & p_services
        if shared_services:
            score += 2.0 * len(shared_services)
            reasons.append(f"Shared service topics: {', '.join(shared_services)}.")

        # Area overlap
        if current_area and p_area and current_area == p_area:
            score += 1.5
            reasons.append(f"Same service area: {p_area}.")

        # Topic overlap
        shared_topics = current_topics & p_topics
        if shared_topics:
            score += 1.0 * len(shared_topics)
            reasons.append(f"Shared topics: {', '.join(shared_topics)}.")

        # Type-based affinity rules
        if current_type == "service_page" and ptype == "service_area_page":
            score += 1.5
            reasons.append("Service pages should link to their area pages.")
        if current_type == "service_area_page" and ptype == "service_page":
            score += 1.5
            reasons.append("Area pages should link to relevant service pages.")
        if current_type == "blog_post" and ptype == "service_page":
            score += 2.0
            reasons.append("Blog posts should link to relevant service pages.")
        if current_type == "blog_post" and ptype == "blog_post":
            if shared_topics:
                score += 1.0
                reasons.append("Related blog post.")
        if current_type == "homepage" and ptype == "service_page":
            score += 2.5
            reasons.append("Homepage should link to top service pages.")

        if score > 0:
            scored.append((score, page, reasons))

    # Sort by score descending and take top N
    scored.sort(key=lambda x: x[0], reverse=True)

    for score, page, reasons in scored[:max_links]:
        ptype = (page.get("page_type", "") or "").lower()
        title = page.get("title", page.get("name", ""))
        p_url = page.get("url", "")

        # Generate anchor text
        anchor = title or page.get("page_id", "")
        if ptype == "contact_page":
            anchor = "Contact us" if not title else f"Contact {title}"
        elif ptype == "service_page":
            svc = page.get("services", [])
            if svc:
                svc_name = svc[0] if isinstance(svc, list) and svc else str(svc)
                anchor = f"{svc_name} services" if isinstance(svc_name, str) else anchor

        # Placement suggestion
        if current_type == "blog_post":
            placement = "After the second or third paragraph of the body content."
        elif current_type == "homepage":
            placement = "Within the services overview section."
        elif current_type == "service_page":
            placement = "In the related services section, or after the main description."
        elif current_type == "service_area_page":
            placement = "After the area description mentioning local services."
        else:
            placement = "In a contextually relevant paragraph (not the first sentence)."

        recommendations.append({
            "target_page_id": page.get("page_id", ""),
            "target_url": p_url,
            "anchor_text": anchor,
            "context": " ".join(reasons),
            "placement_suggestion": placement,
        })

    return recommendations


def _coerce_list(val: Any) -> List[str]:
    """Coerce a value to a list of lowercase strings."""
    if isinstance(val, list):
        return [str(v).lower() for v in val if v]
    if isinstance(val, str) and val:
        return [val.lower()]
    return []


def analyze_site_linking_opportunities(
    pages: List[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Analyze the full site structure and identify internal linking gaps.

    Parameters
    ----------
    pages:
        List of page dicts (``page_id``, ``page_type``, ``url``,
        ``internal_links_to``, ``services``, ``area``, ``topics``).
    profile:
        BusinessProfile dict.

    Returns
    -------
    dict
        ``{"total_pages", "orphan_pages", "over_linked_pages",
        "under_linked_pages", "missing_contact_links",
        "recommendations", "hub_pages"}``
    """
    total = len(pages)
    page_index = {p.get("page_id", ""): p for p in pages}

    # Build inbound link counts
    inbound_counts: Dict[str, int] = {p.get("page_id", ""): 0 for p in pages}
    outbound_counts: Dict[str, int] = {p.get("page_id", ""): 0 for p in pages}

    for p in pages:
        links_to = p.get("internal_links_to") or []
        if isinstance(links_to, list):
            outbound_counts[p.get("page_id", "")] = len(links_to)
            for target_id in links_to:
                if target_id in inbound_counts:
                    inbound_counts[target_id] += 1

    # Orphan pages: 0 inbound links (excluding homepage)
    orphan_pages = [
        pid for pid, count in inbound_counts.items()
        if count == 0 and page_index.get(pid, {}).get("page_type", "").lower() != "homepage"
    ]

    # Over-linked pages: > 10 inbound links
    over_linked = [pid for pid, count in inbound_counts.items() if count > 10]

    # Under-linked pages: < 2 outbound links
    under_linked = [pid for pid, count in outbound_counts.items() if count < 2]

    # Pages missing link to contact page
    contact_ids = [
        p.get("page_id", "") for p in pages
        if (p.get("page_type", "") or "").lower() == "contact_page"
    ]
    missing_contact: List[str] = []
    if contact_ids:
        for p in pages:
            pid = p.get("page_id", "")
            ptype = (p.get("page_type", "") or "").lower()
            if ptype == "contact_page":
                continue
            links_to = p.get("internal_links_to") or []
            if not any(cid in links_to for cid in contact_ids):
                missing_contact.append(pid)

    # Hub pages: service category overview pages and homepage
    hub_pages: List[str] = []
    for p in pages:
        ptype = (p.get("page_type", "") or "").lower()
        if ptype in ("homepage", "service_page"):
            hub_pages.append(p.get("page_id", ""))

    # Build recommendations
    recs: List[Dict[str, Any]] = []
    for pid in orphan_pages[:10]:
        page = page_index.get(pid, {})
        recs.append({
            "type": "orphan_fix",
            "page_id": pid,
            "suggestion": f"Page '{page.get('title', pid)}' has no inbound links. Add links from related pages.",
        })
    for pid in missing_contact[:10]:
        page = page_index.get(pid, {})
        recs.append({
            "type": "missing_contact_link",
            "page_id": pid,
            "suggestion": f"Page '{page.get('title', pid)}' does not link to the contact page. Add a CTA link.",
        })
    for pid in under_linked[:10]:
        page = page_index.get(pid, {})
        recs.append({
            "type": "under_linked",
            "page_id": pid,
            "suggestion": f"Page '{page.get('title', pid)}' has fewer than 2 outbound internal links. Add contextual links.",
        })

    return {
        "total_pages": total,
        "orphan_pages": orphan_pages,
        "over_linked_pages": over_linked,
        "under_linked_pages": under_linked,
        "missing_contact_links": missing_contact,
        "recommendations": recs,
        "hub_pages": hub_pages,
    }

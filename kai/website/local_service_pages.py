"""Local-service page type builders for the Kai Marketing OS.

Generates complete, structured page blueprints for the four core page types
every local service business needs: homepage, service pages, service area
pages, and contact/quote pages.

Each builder outputs a ``PageStructure`` with ordered ``PageSection`` items,
JSON-LD schema markup, meta tags, and internal linking suggestions.  All
content is derived from the ``BusinessProfile`` dict -- nothing is hardcoded.

No external dependencies beyond the Python standard library and the
Pydantic-or-fallback pattern shared across the project.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional, Tuple

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
            import json as _json

            return _json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[misc,assignment]
    Field = _PydanticField  # type: ignore[misc,assignment]


# ===================================================================
# Constants
# ===================================================================

TITLE_MAX_CHARS = 60
META_DESC_MAX_CHARS = 160
SCHEMA_CONTEXT = "https://schema.org"

VALID_SECTION_TYPES = [
    "hero",
    "trust_bar",
    "services_overview",
    "service_detail",
    "process_steps",
    "testimonials",
    "before_after",
    "faq",
    "cta_block",
    "about_snippet",
    "service_area_map",
    "contact_info",
    "pricing_indicators",
    "credentials",
    "recent_work",
    "related_services",
    "area_content",
    "driving_directions",
    "area_offers",
    "form_section",
    "hours_map",
    "what_to_expect",
    "schema_markup",
]


# ===================================================================
# Data models
# ===================================================================


class PageSection(BaseModel):
    """A single section within a local-service page."""

    section_id: str
    section_type: str
    position: int
    heading: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    schema_markup: Optional[Dict[str, Any]] = None
    css_class_suggestion: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PageStructure(BaseModel):
    """Complete page blueprint for a local-service business page."""

    page_type: str
    title: str
    meta_description: str
    slug: str
    sections: List[PageSection] = Field(default_factory=list)
    page_schema: List[Dict[str, Any]] = Field(default_factory=list)
    internal_links: List[Dict[str, str]] = Field(default_factory=list)
    canonical_url: Optional[str] = None
    og_tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ===================================================================
# Internal helpers — safe data extraction
# ===================================================================


def _safe_get(d: Any, *keys: str, default: Any = "") -> Any:
    """Drill into nested dicts/objects, returning *default* on any miss."""
    current = d
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif hasattr(current, key):
            current = getattr(current, key, default)
        else:
            return default
    return current if current is not None else default


def _truncate(text: str, max_chars: int) -> str:
    """Truncate *text* to *max_chars*, breaking at a word boundary."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:
        cut = cut[:last_space]
    return cut.rstrip(" .,;:-")


def _slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def _to_dict(obj: Any) -> Any:
    """Recursively convert Pydantic-like objects to plain dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return obj


# ===================================================================
# Profile data extractors
# ===================================================================


def _extract_phone(profile: Dict[str, Any]) -> str:
    """Extract primary phone number from profile.

    Checks ``identity.phone`` first, then falls back to the primary
    location's phone.
    """
    phone = _safe_get(profile, "identity", "phone")
    if phone:
        return str(phone)

    locations = _safe_get(profile, "geography", "locations", default=[])
    if isinstance(locations, list):
        for loc in locations:
            loc_d = _to_dict(loc)
            if _safe_get(loc_d, "is_primary"):
                p = _safe_get(loc_d, "phone")
                if p:
                    return str(p)
        # Fall back to first location
        if locations:
            p = _safe_get(_to_dict(locations[0]), "phone")
            if p:
                return str(p)
    return ""


def _extract_primary_location(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the primary location dict from profile.geography.locations.

    Returns the location marked ``is_primary=True``, or the first location,
    or an empty dict.
    """
    locations = _safe_get(profile, "geography", "locations", default=[])
    if not isinstance(locations, list) or not locations:
        return {}
    for loc in locations:
        loc_d = _to_dict(loc)
        if _safe_get(loc_d, "is_primary"):
            return loc_d
    return _to_dict(locations[0])


def _extract_city(profile: Dict[str, Any]) -> str:
    """Extract the primary city from the profile."""
    loc = _extract_primary_location(profile)
    city = _safe_get(loc, "city")
    if city:
        return str(city)
    # Fall back to first service area
    areas = _safe_get(profile, "geography", "service_areas", default=[])
    if isinstance(areas, list) and areas:
        return str(areas[0])
    return ""


def _extract_business_name(profile: Dict[str, Any]) -> str:
    """Extract business name from profile."""
    name = _safe_get(profile, "identity", "business_name")
    return str(name) if name else "Our Business"


def _extract_primary_service(profile: Dict[str, Any]) -> str:
    """Extract the primary service name from profile.offers."""
    offers = _safe_get(profile, "offers", default=[])
    if isinstance(offers, list):
        for offer in offers:
            od = _to_dict(offer)
            if _safe_get(od, "is_primary"):
                return str(_safe_get(od, "name", default=""))
        if offers:
            return str(_safe_get(_to_dict(offers[0]), "name", default=""))
    return ""


def _extract_website_url(profile: Dict[str, Any]) -> str:
    """Extract website URL from profile."""
    url = _safe_get(profile, "identity", "website_url")
    return str(url) if url else ""


def _extract_trust_indicators(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract 4-5 trust indicators from profile.trust.

    Returns a list of ``{"icon": "...", "text": "..."}`` dicts.
    """
    trust = _safe_get(profile, "trust", default={})
    if not isinstance(trust, dict) and hasattr(trust, "model_dump"):
        trust = trust.model_dump()
    elif not isinstance(trust, dict):
        trust = {}

    indicators: List[Dict[str, str]] = []

    years = _safe_get(trust, "years_in_business")
    if years:
        indicators.append({
            "icon": "clock",
            "text": f"{years}+ Years of Experience",
        })

    testimonials = _safe_get(trust, "testimonials", default=[])
    if isinstance(testimonials, list) and testimonials:
        count = len(testimonials)
        indicators.append({
            "icon": "star",
            "text": f"{count}+ Five-Star Reviews",
        })

    certifications = _safe_get(trust, "certifications", default=[])
    if isinstance(certifications, list) and certifications:
        cert = certifications[0]
        indicators.append({
            "icon": "badge",
            "text": f"{cert} Certified",
        })

    licenses = _safe_get(trust, "licenses", default=[])
    if isinstance(licenses, list) and licenses:
        indicators.append({
            "icon": "shield",
            "text": "Licensed & Insured",
        })

    team_size = _safe_get(trust, "team_size")
    if team_size:
        indicators.append({
            "icon": "users",
            "text": f"{team_size}-Person Team",
        })

    insurance = _safe_get(trust, "insurance_details")
    if insurance and not any("Licensed" in i["text"] for i in indicators):
        indicators.append({
            "icon": "shield-check",
            "text": "Fully Insured",
        })

    # Return up to 5
    return indicators[:5]


def _extract_testimonials(
    profile: Dict[str, Any],
    *,
    max_count: int = 5,
    service_filter: Optional[str] = None,
    area_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Extract formatted testimonials from profile.trust.testimonials.

    Optionally filters by service category or customer area.
    """
    trust = _safe_get(profile, "trust", default={})
    if not isinstance(trust, dict) and hasattr(trust, "model_dump"):
        trust = trust.model_dump()
    elif not isinstance(trust, dict):
        trust = {}

    raw_testimonials = _safe_get(trust, "testimonials", default=[])
    if not isinstance(raw_testimonials, list):
        return []

    results: List[Dict[str, Any]] = []
    for t in raw_testimonials:
        td = _to_dict(t)
        # Apply service filter
        if service_filter:
            t_source = str(_safe_get(td, "source", default="")).lower()
            t_title = str(_safe_get(td, "title", default="")).lower()
            t_content = str(_safe_get(td, "content", default="")).lower()
            sf_lower = service_filter.lower()
            if sf_lower not in t_source and sf_lower not in t_title and sf_lower not in t_content:
                continue
        # Apply area filter
        if area_filter:
            t_content = str(_safe_get(td, "content", default="")).lower()
            t_source = str(_safe_get(td, "source", default="")).lower()
            af_lower = area_filter.lower()
            if af_lower not in t_content and af_lower not in t_source:
                continue

        results.append({
            "quote": str(_safe_get(td, "content", default="")),
            "name": str(_safe_get(td, "source", default="A Happy Customer")),
            "rating": 5,
            "service": str(_safe_get(td, "title", default="")),
        })
        if len(results) >= max_count:
            break

    return results


def _extract_offers(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all offers as plain dicts."""
    offers = _safe_get(profile, "offers", default=[])
    if not isinstance(offers, list):
        return []
    return [_to_dict(o) for o in offers]


def _extract_service_areas(profile: Dict[str, Any]) -> List[str]:
    """Extract service areas as a list of strings."""
    areas = _safe_get(profile, "geography", "service_areas", default=[])
    if isinstance(areas, list):
        return [str(a) for a in areas]
    return []


def _extract_email(profile: Dict[str, Any]) -> str:
    """Extract business email."""
    email = _safe_get(profile, "identity", "email")
    return str(email) if email else ""


def _extract_address_string(profile: Dict[str, Any]) -> str:
    """Build a human-readable address from the primary location."""
    loc = _extract_primary_location(profile)
    if not loc:
        return ""
    parts = []
    for key in ("address", "city", "state", "zip_code"):
        val = _safe_get(loc, key)
        if val:
            parts.append(str(val))
    return ", ".join(parts)


# ===================================================================
# Schema markup generators
# ===================================================================


def _generate_local_business_schema(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a complete LocalBusiness JSON-LD schema from profile data."""
    biz_name = _extract_business_name(profile)
    phone = _extract_phone(profile)
    url = _extract_website_url(profile)
    loc = _extract_primary_location(profile)
    trust = _safe_get(profile, "trust", default={})
    if hasattr(trust, "model_dump"):
        trust = trust.model_dump()
    elif not isinstance(trust, dict):
        trust = {}

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "LocalBusiness",
        "name": biz_name,
    }

    if url:
        schema["url"] = url
    if phone:
        schema["telephone"] = phone

    # Address
    address_parts: Dict[str, str] = {}
    if _safe_get(loc, "address"):
        address_parts["streetAddress"] = str(_safe_get(loc, "address"))
    if _safe_get(loc, "city"):
        address_parts["addressLocality"] = str(_safe_get(loc, "city"))
    if _safe_get(loc, "state"):
        address_parts["addressRegion"] = str(_safe_get(loc, "state"))
    if _safe_get(loc, "zip_code"):
        address_parts["postalCode"] = str(_safe_get(loc, "zip_code"))
    country = _safe_get(loc, "country", default="US")
    if country:
        address_parts["addressCountry"] = str(country)
    if address_parts:
        schema["address"] = {"@type": "PostalAddress", **address_parts}

    # Opening hours
    hours = _safe_get(loc, "hours", default={})
    if isinstance(hours, dict) and hours:
        specs = []
        for day, time_str in hours.items():
            if time_str and str(time_str).lower() not in ("closed", ""):
                parts = str(time_str).split("-")
                spec: Dict[str, Any] = {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": day.capitalize(),
                }
                if len(parts) == 2:
                    spec["opens"] = parts[0].strip()
                    spec["closes"] = parts[1].strip()
                specs.append(spec)
        if specs:
            schema["openingHoursSpecification"] = specs

    # Aggregate rating from testimonials
    testimonials = _safe_get(trust, "testimonials", default=[])
    if isinstance(testimonials, list) and testimonials:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": "5.0",
            "reviewCount": str(len(testimonials)),
        }

    # Area served
    areas = _extract_service_areas(profile)
    if areas:
        schema["areaServed"] = [
            {"@type": "City", "name": area} for area in areas
        ]

    # Image
    logo = _safe_get(profile, "identity", "logo_url")
    if logo:
        schema["image"] = str(logo)

    # Social profiles
    channels = _safe_get(profile, "channels", default=[])
    if isinstance(channels, list):
        same_as = []
        for ch in channels:
            ch_d = _to_dict(ch)
            ch_url = _safe_get(ch_d, "url")
            if ch_url:
                same_as.append(str(ch_url))
        if same_as:
            schema["sameAs"] = same_as

    return schema


def _generate_service_schema(
    service: Dict[str, Any],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a Service JSON-LD schema."""
    svc = _to_dict(service)
    biz_name = _extract_business_name(profile)
    url = _extract_website_url(profile)

    schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Service",
        "name": str(_safe_get(svc, "name", default="")),
    }

    desc = _safe_get(svc, "description")
    if desc:
        schema["description"] = str(desc)

    schema["provider"] = {
        "@type": "LocalBusiness",
        "name": biz_name,
    }
    if url:
        schema["provider"]["url"] = url

    areas = _extract_service_areas(profile)
    if areas:
        schema["areaServed"] = [
            {"@type": "City", "name": area} for area in areas
        ]

    price_range = _safe_get(svc, "price_range")
    if price_range:
        schema["offers"] = {
            "@type": "Offer",
            "priceSpecification": {
                "@type": "PriceSpecification",
                "price": str(price_range),
                "priceCurrency": "USD",
            },
        }

    return schema


def _generate_faq_schema(faqs: List[Dict[str, str]]) -> Dict[str, Any]:
    """Generate a FAQPage JSON-LD schema from question/answer dicts."""
    if not faqs:
        return {}
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.get("question", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.get("answer", ""),
                },
            }
            for faq in faqs
            if faq.get("question")
        ],
    }


def _generate_review_schema(
    testimonials: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate Review JSON-LD schema for each testimonial."""
    reviews: List[Dict[str, Any]] = []
    for t in testimonials:
        review: Dict[str, Any] = {
            "@type": "Review",
            "reviewBody": t.get("quote", ""),
            "author": {
                "@type": "Person",
                "name": t.get("name", "Customer"),
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": str(t.get("rating", 5)),
                "bestRating": "5",
            },
        }
        date_pub = t.get("date") or t.get("datePublished")
        if date_pub:
            review["datePublished"] = str(date_pub)
        reviews.append(review)
    return reviews


# ===================================================================
# Meta tag builders
# ===================================================================


def _build_meta_title(
    page_type: str,
    profile: Dict[str, Any],
    service: Optional[Dict[str, Any]] = None,
    area: Optional[str] = None,
) -> str:
    """Generate an SEO-optimized ``<title>`` tag (under 60 chars)."""
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    primary_svc = _extract_primary_service(profile)

    svc_name = ""
    if service:
        svc_name = str(_safe_get(_to_dict(service), "name", default=""))
    svc_name = svc_name or primary_svc

    trust_indicators = _extract_trust_indicators(profile)
    trust_text = trust_indicators[0]["text"] if trust_indicators else ""

    ptype = page_type.lower().replace("-", "_").replace(" ", "_")

    if ptype == "homepage":
        if svc_name and city:
            raw = f"{biz_name} — {svc_name} in {city}"
            if trust_text and len(raw) + len(trust_text) + 3 <= TITLE_MAX_CHARS:
                raw = f"{raw} | {trust_text}"
        elif svc_name:
            raw = f"{biz_name} — {svc_name}"
        else:
            raw = biz_name
    elif ptype == "service_page":
        if svc_name and city:
            raw = f"{svc_name} in {city} | {biz_name}"
        elif svc_name:
            raw = f"{svc_name} | {biz_name}"
        else:
            raw = f"Services | {biz_name}"
    elif ptype == "service_area_page":
        area_name = area or city
        if svc_name and area_name:
            raw = f"{svc_name} in {area_name} | {biz_name}"
        elif area_name:
            raw = f"Services in {area_name} | {biz_name}"
        else:
            raw = f"Service Area | {biz_name}"
    elif ptype == "contact_page":
        if phone:
            raw = f"Contact {biz_name} | Free Quote | {phone}"
        else:
            raw = f"Contact {biz_name} | Free Quote"
    else:
        raw = biz_name

    return _truncate(raw, TITLE_MAX_CHARS)


def _build_meta_description(
    page_type: str,
    profile: Dict[str, Any],
    service: Optional[Dict[str, Any]] = None,
    area: Optional[str] = None,
) -> str:
    """Generate a meta description (under 160 chars)."""
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    primary_svc = _extract_primary_service(profile)

    svc_name = ""
    if service:
        svc_name = str(_safe_get(_to_dict(service), "name", default=""))
    svc_name = svc_name or primary_svc or "services"

    trust_indicators = _extract_trust_indicators(profile)
    trust_text = trust_indicators[0]["text"] if trust_indicators else ""

    phone_cta = f" Call {phone}." if phone else ""

    ptype = page_type.lower().replace("-", "_").replace(" ", "_")

    if ptype == "homepage":
        core = f"{biz_name} offers professional {svc_name} in {city}."
        if trust_text:
            core += f" {trust_text}."
        core += f"{phone_cta} Free estimates."
    elif ptype == "service_page":
        core = f"Professional {svc_name} services in {city}."
        desc = ""
        if service:
            desc = str(_safe_get(_to_dict(service), "description", default=""))
        if desc:
            # Use first sentence of description as benefit
            first_sentence = desc.split(".")[0].strip()
            if first_sentence and len(first_sentence) < 80:
                core += f" {first_sentence}."
        core += f" Free estimates.{phone_cta}"
    elif ptype == "service_area_page":
        area_name = area or city
        core = f"Need {svc_name} in {area_name}? {biz_name} serves {area_name}"
        if trust_text:
            core += f" with {trust_text}."
        else:
            core += "."
        core += phone_cta
    elif ptype == "contact_page":
        core = f"Contact {biz_name} for a free {svc_name} quote."
        core += phone_cta or ""
        core += " We respond within 1 hour."
    else:
        core = f"{biz_name} — {svc_name} in {city}.{phone_cta}"

    return _truncate(core, META_DESC_MAX_CHARS)


def _build_og_tags(
    page_type: str,
    title: str,
    description: str,
    profile: Dict[str, Any],
    slug: str,
) -> Dict[str, str]:
    """Build Open Graph tags for a page."""
    url = _extract_website_url(profile)
    biz_name = _extract_business_name(profile)
    logo = _safe_get(profile, "identity", "logo_url", default="")

    tags: Dict[str, str] = {
        "og:type": "website",
        "og:title": title,
        "og:description": description,
        "og:site_name": biz_name,
    }
    if url:
        full_url = url.rstrip("/") + "/" + slug.lstrip("/")
        tags["og:url"] = full_url
    if logo:
        tags["og:image"] = str(logo)

    return tags


# ===================================================================
# Internal link builders
# ===================================================================


def _build_service_page_links(
    profile: Dict[str, Any],
    exclude_service: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Build internal links to all service pages except *exclude_service*."""
    offers = _extract_offers(profile)
    links: List[Dict[str, str]] = []
    for offer in offers:
        name = str(_safe_get(offer, "name", default=""))
        if not name or (exclude_service and name.lower() == exclude_service.lower()):
            continue
        links.append({
            "text": name,
            "url": f"/services/{_slugify(name)}",
            "context": "service_page",
        })
    return links


def _build_area_page_links(profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build internal links to service area pages."""
    areas = _extract_service_areas(profile)
    primary_svc = _extract_primary_service(profile)
    links: List[Dict[str, str]] = []
    for area in areas:
        links.append({
            "text": f"{primary_svc} in {area}" if primary_svc else area,
            "url": f"/service-areas/{_slugify(area)}",
            "context": "service_area_page",
        })
    return links


# ===================================================================
# FAQ generator helper
# ===================================================================


def _generate_service_faqs(
    service: Dict[str, Any],
    profile: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Generate 5-8 common FAQs for a service type.

    Builds questions dynamically from the service and profile data rather
    than using static templates.
    """
    svc = _to_dict(service)
    svc_name = str(_safe_get(svc, "name", default="service"))
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    price_range = _safe_get(svc, "price_range")
    areas = _extract_service_areas(profile)
    trust = _safe_get(profile, "trust", default={})
    if hasattr(trust, "model_dump"):
        trust = trust.model_dump()
    elif not isinstance(trust, dict):
        trust = {}

    faqs: List[Dict[str, str]] = []

    # Cost question
    cost_answer = f"The cost of {svc_name} varies based on the scope of work, materials, and specific requirements."
    if price_range:
        cost_answer += f" Our typical range is {price_range}."
    cost_answer += f" Contact {biz_name} for a free, no-obligation estimate."
    faqs.append({
        "question": f"How much does {svc_name} cost?",
        "answer": cost_answer,
    })

    # Booking question
    booking_answer = f"Schedule your {svc_name} appointment by calling {phone}" if phone else f"Schedule your {svc_name} appointment by contacting us"
    booking_answer += f" or filling out our online form. We respond within 1 hour during business hours."
    faqs.append({
        "question": f"How do I schedule {svc_name}?",
        "answer": booking_answer,
    })

    # Service area question
    if areas:
        area_list = ", ".join(areas[:5])
        faqs.append({
            "question": f"What areas do you serve for {svc_name}?",
            "answer": f"We provide {svc_name} throughout {area_list} and surrounding communities. Contact us to confirm service in your area.",
        })

    # Timeline question
    faqs.append({
        "question": f"How long does {svc_name} take?",
        "answer": f"The timeline for {svc_name} depends on the project scope. We provide a detailed timeline during your free estimate so you know what to expect before work begins.",
    })

    # Credentials question
    licenses = _safe_get(trust, "licenses", default=[])
    certs = _safe_get(trust, "certifications", default=[])
    cred_parts = []
    if isinstance(licenses, list) and licenses:
        cred_parts.append("fully licensed")
    if _safe_get(trust, "insurance_details"):
        cred_parts.append("insured")
    if isinstance(certs, list) and certs:
        cred_parts.append(f"certified ({', '.join(str(c) for c in certs[:2])})")
    if cred_parts:
        cred_text = ", ".join(cred_parts)
        faqs.append({
            "question": f"Is {biz_name} licensed and insured?",
            "answer": f"Yes. {biz_name} is {cred_text}. We carry all required credentials for {svc_name} work in {city}." if city else f"Yes. {biz_name} is {cred_text}.",
        })

    # Guarantee question
    faqs.append({
        "question": f"Do you offer a guarantee on {svc_name}?",
        "answer": f"We stand behind every job. Contact us to learn about our satisfaction guarantee and warranty coverage for {svc_name}.",
    })

    # Emergency question
    faqs.append({
        "question": f"Do you offer emergency {svc_name}?",
        "answer": f"Call {phone} for emergency service availability." if phone else f"Contact us to ask about emergency {svc_name} availability.",
    })

    # Quote question
    faqs.append({
        "question": f"Is the {svc_name} estimate free?",
        "answer": f"Yes. {biz_name} provides free, no-obligation estimates for all {svc_name} projects. Call {phone} or request a quote online." if phone else f"Yes. {biz_name} provides free, no-obligation estimates for all {svc_name} projects.",
    })

    return faqs[:8]


# ===================================================================
# Page builders
# ===================================================================


def build_homepage(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a complete homepage structure for a local service business.

    Parameters
    ----------
    profile:
        A BusinessProfile dict (or model_dump() output).

    Returns
    -------
    dict
        Serialized ``PageStructure`` ready for CMS injection.
    """
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    primary_svc = _extract_primary_service(profile)
    offers = _extract_offers(profile)
    areas = _extract_service_areas(profile)
    trust_indicators = _extract_trust_indicators(profile)
    testimonials = _extract_testimonials(profile, max_count=5)
    loc = _extract_primary_location(profile)
    elevator_pitch = _safe_get(profile, "identity", "elevator_pitch", default="")

    trust_raw = _safe_get(profile, "trust", default={})
    if hasattr(trust_raw, "model_dump"):
        trust_raw = trust_raw.model_dump()
    elif not isinstance(trust_raw, dict):
        trust_raw = {}

    years = _safe_get(trust_raw, "years_in_business", default="")
    review_count = len(_safe_get(trust_raw, "testimonials", default=[]) if isinstance(_safe_get(trust_raw, "testimonials", default=[]), list) else [])

    # -- Section 1: Hero --
    hero_headline = f"{city}'s Trusted {primary_svc} — Call for a Free Quote" if city and primary_svc else f"{biz_name} — Call for a Free Quote"
    hero_sub_parts = []
    if years:
        hero_sub_parts.append(f"Serving {city} for {years}+ years" if city else f"{years}+ years of experience")
    trust_creds = []
    licenses = _safe_get(trust_raw, "licenses", default=[])
    if isinstance(licenses, list) and licenses:
        trust_creds.append("Licensed")
    if _safe_get(trust_raw, "insurance_details"):
        trust_creds.extend(["bonded", "insured"])
    if trust_creds:
        hero_sub_parts.insert(0, ", ".join(trust_creds).capitalize())
    hero_subheadline = ". ".join(hero_sub_parts) + "." if hero_sub_parts else f"Professional {primary_svc} services you can trust."

    trust_indicator_text = f"{review_count}+ Five-Star Reviews on Google" if review_count > 0 else ""

    hero = PageSection(
        section_id="hero",
        section_type="hero",
        position=1,
        heading=hero_headline,
        content={
            "headline": hero_headline,
            "subheadline": hero_subheadline,
            "primary_cta": {
                "text": f"Call Now: {phone}" if phone else "Call Now",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone",
            },
            "secondary_cta": {
                "text": "Get a Free Quote",
                "url": "/contact",
                "type": "form",
            },
            "trust_indicator": trust_indicator_text,
            "background_image_suggestion": f"Professional photo of {biz_name} team at work, ideally on-site in {city}" if city else f"Professional photo of {biz_name} team at work",
        },
        css_class_suggestion="hero-section",
        notes="Phone number must be prominent and click-to-call on mobile",
    )

    # -- Section 2: Trust bar --
    trust_bar = PageSection(
        section_id="trust_bar",
        section_type="trust_bar",
        position=2,
        content={"items": trust_indicators},
        css_class_suggestion="trust-bar",
        notes="Single horizontal row, no heading, badges/icons preferred",
    )

    # -- Section 3: Services overview --
    services_list = []
    for offer in offers:
        od = _to_dict(offer)
        svc_name_str = str(_safe_get(od, "name", default=""))
        desc = str(_safe_get(od, "description", default=""))
        # Truncate description to 2 sentences
        sentences = desc.split(".")
        short_desc = ". ".join(s.strip() for s in sentences[:2] if s.strip())
        if short_desc and not short_desc.endswith("."):
            short_desc += "."
        services_list.append({
            "name": svc_name_str,
            "description": short_desc,
            "icon_suggestion": f"Icon representing {svc_name_str.lower()}",
            "link": f"/services/{_slugify(svc_name_str)}",
        })

    services_heading = f"{primary_svc} Services in {city}" if primary_svc and city else "Our Services"
    services_overview = PageSection(
        section_id="services_overview",
        section_type="services_overview",
        position=3,
        heading=services_heading,
        content={
            "heading": services_heading,
            "services": services_list,
        },
        css_class_suggestion="services-grid",
        notes="Grid layout (3 or 4 columns), each service links to its dedicated page",
    )

    # -- Section 4: About snippet --
    differentiators: List[str] = []
    if years:
        differentiators.append(f"{years}+ years of proven experience")
    if isinstance(licenses, list) and licenses:
        differentiators.append("Fully licensed and insured")
    if review_count > 0:
        differentiators.append(f"{review_count}+ five-star reviews from real customers")
    if not differentiators:
        differentiators = [
            "Locally owned and operated",
            "Honest, upfront pricing",
            "100% satisfaction guarantee",
        ]

    about_body = str(elevator_pitch) if elevator_pitch else f"{biz_name} provides professional {primary_svc} services to homeowners and businesses in {city} and surrounding areas."

    about_snippet = PageSection(
        section_id="about_snippet",
        section_type="about_snippet",
        position=4,
        heading=f"Why Choose {biz_name}",
        content={
            "heading": f"Why Choose {biz_name}",
            "body": about_body,
            "differentiators": differentiators[:4],
            "team_photo_suggestion": f"Photo of {biz_name} owner or team in branded uniforms",
        },
        css_class_suggestion="about-section",
        notes="Include photo of owner/team if available",
    )

    # -- Section 5: Testimonials --
    testimonials_section = PageSection(
        section_id="testimonials",
        section_type="testimonials",
        position=5,
        heading="What Our Customers Say",
        content={
            "heading": "What Our Customers Say",
            "testimonials": testimonials,
            "google_review_link": None,
        },
        schema_markup=_generate_review_schema(testimonials)[0] if testimonials else None,
        css_class_suggestion="testimonials-section",
        notes="Star ratings displayed, Google icon for verified reviews",
    )

    # -- Section 6: Recent work / Before-After --
    projects: List[Dict[str, str]] = []
    for i, offer in enumerate(offers[:3]):
        od = _to_dict(offer)
        svc_name_str = str(_safe_get(od, "name", default=f"Project {i+1}"))
        projects.append({
            "title": f"Recent {svc_name_str} Project",
            "description": f"A recent {svc_name_str.lower()} project completed for a client in {city}." if city else f"A recent {svc_name_str.lower()} project.",
            "before_image_suggestion": f"Before photo of {svc_name_str.lower()} project",
            "after_image_suggestion": f"After photo of completed {svc_name_str.lower()} project",
        })

    recent_work = PageSection(
        section_id="recent_work",
        section_type="before_after",
        position=6,
        heading="Our Recent Work",
        content={
            "heading": "Our Recent Work",
            "projects": projects,
            "view_all_link": "/gallery" if projects else None,
        },
        css_class_suggestion="recent-work-section",
        notes="Carousel or grid layout, before/after slider if possible",
    )

    # -- Section 7: Service area --
    area_links = _build_area_page_links(profile)
    service_area_section = PageSection(
        section_id="service_area_map",
        section_type="service_area_map",
        position=7,
        heading=f"Serving {city} and Surrounding Areas" if city else "Our Service Area",
        content={
            "heading": f"Serving {city} and Surrounding Areas" if city else "Our Service Area",
            "areas": areas,
            "map_embed_suggestion": f"Embed Google Map centered on {city}" if city else "Embed Google Map centered on primary service area",
            "area_page_links": area_links,
        },
        css_class_suggestion="service-area-section",
        notes="Include map if possible, list all service areas with links",
    )

    # -- Section 8: CTA block --
    cta_block = PageSection(
        section_id="cta_bottom",
        section_type="cta_block",
        position=8,
        heading="Ready to Get Started?",
        content={
            "heading": "Ready to Get Started?",
            "body": f"Get a free, no-obligation estimate from {biz_name} today. Same-day responses, honest pricing, and work you can trust.",
            "cta": {
                "text": f"Call {phone}" if phone else "Call Now",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone",
            },
            "secondary_cta": {
                "text": "Request a Quote Online",
                "url": "/contact",
                "type": "form",
            },
            "trust_element": "Free estimates. No obligation.",
        },
        css_class_suggestion="cta-block",
        notes="Full-width section with contrasting background",
    )

    sections = [hero, trust_bar, services_overview, about_snippet, testimonials_section, recent_work, service_area_section, cta_block]

    # Page-level schema
    local_biz_schema = _generate_local_business_schema(profile)
    service_schemas = [_generate_service_schema(_to_dict(o), profile) for o in offers]
    review_schemas = _generate_review_schema(testimonials)

    page_schema: List[Dict[str, Any]] = [local_biz_schema]
    page_schema.extend(service_schemas)
    page_schema.extend(review_schemas)

    # Internal links
    internal_links: List[Dict[str, str]] = []
    internal_links.extend(_build_service_page_links(profile))
    internal_links.extend(_build_area_page_links(profile))
    internal_links.append({"text": "Contact Us", "url": "/contact", "context": "contact_page"})

    title = _build_meta_title("homepage", profile)
    meta_desc = _build_meta_description("homepage", profile)
    slug = "/"

    og_tags = _build_og_tags("homepage", title, meta_desc, profile, slug)

    page = PageStructure(
        page_type="homepage",
        title=title,
        meta_description=meta_desc,
        slug=slug,
        sections=sections,
        page_schema=page_schema,
        internal_links=internal_links,
        canonical_url=_extract_website_url(profile) or None,
        og_tags=og_tags,
    )

    return page.model_dump()


def build_service_page(
    profile: Dict[str, Any],
    service: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a dedicated service page for a local service business.

    Parameters
    ----------
    profile:
        A BusinessProfile dict.
    service:
        An Offer dict from ``profile.offers``.

    Returns
    -------
    dict
        Serialized ``PageStructure``.
    """
    svc = _to_dict(service)
    svc_name = str(_safe_get(svc, "name", default="Our Service"))
    svc_desc = str(_safe_get(svc, "description", default=""))
    price_range = _safe_get(svc, "price_range")

    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    trust_indicators = _extract_trust_indicators(profile)
    testimonials = _extract_testimonials(profile, max_count=3, service_filter=svc_name)
    offers = _extract_offers(profile)

    # If no service-specific testimonials, use general ones
    if not testimonials:
        testimonials = _extract_testimonials(profile, max_count=3)

    # -- Section 1: Hero/intro --
    hero_headline = f"{svc_name} in {city}" if city else f"Professional {svc_name} Services"
    hero_sub = svc_desc.split(".")[0].strip() + "." if svc_desc else f"Trusted {svc_name.lower()} from a team you can count on."
    trust_text = trust_indicators[0]["text"] if trust_indicators else ""

    hero = PageSection(
        section_id="hero",
        section_type="hero",
        position=1,
        heading=hero_headline,
        content={
            "headline": hero_headline,
            "subheadline": hero_sub,
            "primary_cta": {
                "text": f"Call Now: {phone}" if phone else "Get a Quote",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone" if phone else "form",
            },
            "secondary_cta": {
                "text": "Get a Free Quote",
                "url": "/contact",
                "type": "form",
            },
            "trust_indicator": trust_text,
        },
        css_class_suggestion="hero-section",
        notes="Phone number must be click-to-call on mobile",
    )

    # -- Section 2: Service description --
    detail_body = svc_desc if svc_desc else f"{biz_name} provides professional {svc_name.lower()} services in {city} and surrounding areas."
    service_detail = PageSection(
        section_id="service_detail",
        section_type="service_detail",
        position=2,
        heading=f"About Our {svc_name} Services",
        content={
            "heading": f"About Our {svc_name} Services",
            "description": detail_body,
            "whats_included": f"Full-service {svc_name.lower()} including assessment, planning, execution, and follow-up.",
            "what_to_expect": f"When you choose {biz_name} for {svc_name.lower()}, expect clear communication, on-time arrival, clean work areas, and results that exceed expectations.",
        },
        css_class_suggestion="service-detail",
        notes="Expand from offer description with specifics",
    )

    # -- Section 3: Process steps --
    process = PageSection(
        section_id="process_steps",
        section_type="process_steps",
        position=3,
        heading=f"How Our {svc_name} Works",
        content={
            "heading": f"How Our {svc_name} Works",
            "steps": [
                {
                    "number": 1,
                    "title": "Contact Us",
                    "description": f"Call {phone} or fill out our online form to request a free {svc_name.lower()} estimate." if phone else f"Fill out our online form to request a free {svc_name.lower()} estimate.",
                },
                {
                    "number": 2,
                    "title": "Free Assessment",
                    "description": f"A {biz_name} specialist evaluates your needs on-site and provides a detailed, no-obligation quote.",
                },
                {
                    "number": 3,
                    "title": "Expert Service",
                    "description": f"Our trained team completes your {svc_name.lower()} project on schedule and to the highest standards.",
                },
                {
                    "number": 4,
                    "title": "Follow-Up",
                    "description": "We follow up to confirm your satisfaction and address any questions. Your happiness is our priority.",
                },
            ],
        },
        css_class_suggestion="process-steps",
        notes="Numbered steps with icons, visual timeline preferred",
    )

    # -- Section 4: Pricing indicators --
    pricing_factors = [
        f"Scope and complexity of the {svc_name.lower()} project",
        "Materials and equipment required",
        "Accessibility and location specifics",
        "Timeline and scheduling preferences",
    ]
    pricing_content: Dict[str, Any] = {
        "heading": f"{svc_name} Pricing",
        "pricing_note": f"Every {svc_name.lower()} project is unique. We provide transparent, upfront pricing with no hidden fees.",
        "factors_affecting_price": pricing_factors,
        "cta": {
            "text": "Get an Exact Quote",
            "url": "/contact",
            "type": "form",
        },
    }
    if price_range:
        pricing_content["price_range"] = str(price_range)

    pricing = PageSection(
        section_id="pricing_indicators",
        section_type="pricing_indicators",
        position=4,
        heading=f"{svc_name} Pricing",
        content=pricing_content,
        css_class_suggestion="pricing-section",
        notes="Display range or 'starting at' indicators, not exact pricing",
    )

    # -- Section 5: FAQ --
    faqs = _generate_service_faqs(svc, profile)
    faq_schema = _generate_faq_schema(faqs)

    faq_section = PageSection(
        section_id="faq",
        section_type="faq",
        position=5,
        heading=f"{svc_name} — Frequently Asked Questions",
        content={
            "heading": f"{svc_name} — Frequently Asked Questions",
            "faqs": faqs,
        },
        schema_markup=faq_schema if faq_schema else None,
        css_class_suggestion="faq-section",
        notes="Expandable accordion, FAQ schema markup applied at page level",
    )

    # -- Section 6: Testimonials --
    testimonials_section = PageSection(
        section_id="testimonials",
        section_type="testimonials",
        position=6,
        heading=f"What Customers Say About Our {svc_name}",
        content={
            "heading": f"What Customers Say About Our {svc_name}",
            "testimonials": testimonials,
        },
        css_class_suggestion="testimonials-section",
        notes="Service-specific testimonials preferred, star ratings visible",
    )

    # -- Section 7: Related services --
    other_services = _build_service_page_links(profile, exclude_service=svc_name)
    related_section = PageSection(
        section_id="related_services",
        section_type="related_services",
        position=7,
        heading="You Might Also Need",
        content={
            "heading": "You Might Also Need",
            "services": other_services,
        },
        css_class_suggestion="related-services",
        notes="Links to other service pages, 3-4 items max",
    )

    # -- Section 8: CTA block --
    cta_block = PageSection(
        section_id="cta_bottom",
        section_type="cta_block",
        position=8,
        heading=f"Need {svc_name}? Get a Free Quote Today",
        content={
            "heading": f"Need {svc_name}? Get a Free Quote Today",
            "body": f"Schedule your free {svc_name.lower()} estimate from {biz_name}. No obligation, no pressure.",
            "cta": {
                "text": f"Call {phone}" if phone else "Call Now",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone",
            },
            "secondary_cta": {
                "text": "Request a Quote Online",
                "url": "/contact",
                "type": "form",
            },
            "trust_element": "Free estimates. No obligation.",
        },
        css_class_suggestion="cta-block",
        notes="Full-width section with contrasting background",
    )

    sections = [hero, service_detail, process, pricing, faq_section, testimonials_section, related_section, cta_block]

    # Schema
    svc_schema = _generate_service_schema(svc, profile)
    review_schemas = _generate_review_schema(testimonials)

    page_schema: List[Dict[str, Any]] = [svc_schema]
    if faq_schema:
        page_schema.append(faq_schema)
    page_schema.extend(review_schemas)

    # Internal links
    internal_links: List[Dict[str, str]] = []
    internal_links.extend(other_services[:4])
    internal_links.extend(_build_area_page_links(profile)[:3])
    internal_links.append({"text": "Contact Us", "url": "/contact", "context": "contact_page"})
    internal_links.append({"text": "Back to Home", "url": "/", "context": "homepage"})

    slug = f"services/{_slugify(svc_name)}"
    title = _build_meta_title("service_page", profile, service=svc)
    meta_desc = _build_meta_description("service_page", profile, service=svc)
    og_tags = _build_og_tags("service_page", title, meta_desc, profile, slug)

    base_url = _extract_website_url(profile)
    canonical = f"{base_url.rstrip('/')}/{slug}" if base_url else None

    page = PageStructure(
        page_type="service_page",
        title=title,
        meta_description=meta_desc,
        slug=slug,
        sections=sections,
        page_schema=page_schema,
        internal_links=internal_links,
        canonical_url=canonical,
        og_tags=og_tags,
    )

    return page.model_dump()


def build_service_area_page(
    profile: Dict[str, Any],
    area: str,
    services: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generate a service area page for a specific geographic area.

    Parameters
    ----------
    profile:
        A BusinessProfile dict.
    area:
        The geographic area name (e.g. "North Houston", "Westchester County").
    services:
        Optional list of service/offer dicts available in this area.
        Falls back to ``profile.offers`` when ``None``.

    Returns
    -------
    dict
        Serialized ``PageStructure``.
    """
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    primary_svc = _extract_primary_service(profile)
    all_offers = _extract_offers(profile)
    area_services = [_to_dict(s) for s in services] if services else all_offers
    testimonials = _extract_testimonials(profile, max_count=3, area_filter=area)
    loc = _extract_primary_location(profile)

    trust_raw = _safe_get(profile, "trust", default={})
    if hasattr(trust_raw, "model_dump"):
        trust_raw = trust_raw.model_dump()
    elif not isinstance(trust_raw, dict):
        trust_raw = {}
    years = _safe_get(trust_raw, "years_in_business", default="")

    svc_type = primary_svc or "professional services"

    # -- Section 1: Area hero --
    hero_headline = f"{svc_type} Services in {area}"
    hero_sub = f"Serving {area} with trusted {svc_type.lower()} since {years}" if years else f"Your trusted {svc_type.lower()} provider in {area}"

    hero = PageSection(
        section_id="hero",
        section_type="hero",
        position=1,
        heading=hero_headline,
        content={
            "headline": hero_headline,
            "subheadline": hero_sub,
            "primary_cta": {
                "text": f"Call Now: {phone}" if phone else "Get a Quote",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone" if phone else "form",
            },
        },
        css_class_suggestion="hero-section area-hero",
        notes="Area-specific hero with phone CTA",
    )

    # -- Section 2: Area content --
    area_body = (
        f"{biz_name} proudly serves the {area} community with reliable, professional {svc_type.lower()}. "
        f"Our team knows {area} well — from the neighborhoods and infrastructure to the specific "
        f"challenges homeowners and businesses face in this area.\n\n"
        f"Whether you are in the heart of {area} or the surrounding neighborhoods, we deliver "
        f"the same high-quality workmanship and responsive service that has earned us the trust "
        f"of customers across the region."
    )

    area_content = PageSection(
        section_id="area_content",
        section_type="area_content",
        position=2,
        heading=f"{svc_type} in {area}",
        content={
            "heading": f"{svc_type} in {area}",
            "body": area_body,
            "area_specific_note": f"Content must reference real characteristics of {area} — do not use generic copy with the city name swapped in.",
        },
        css_class_suggestion="area-content",
        notes="Content must be genuinely area-specific, not generic copy with city name swapped",
    )

    # -- Section 3: Services available --
    area_svc_list = []
    for svc in area_services:
        sd = _to_dict(svc)
        name = str(_safe_get(sd, "name", default=""))
        if not name:
            continue
        area_svc_list.append({
            "name": name,
            "description": str(_safe_get(sd, "description", default="")),
            "link": f"/services/{_slugify(name)}?area={_slugify(area)}",
        })

    services_section = PageSection(
        section_id="services_available",
        section_type="services_overview",
        position=3,
        heading=f"Services Available in {area}",
        content={
            "heading": f"Services Available in {area}",
            "services": area_svc_list,
        },
        css_class_suggestion="services-list area-services",
        notes="Each service links to its dedicated page with area context",
    )

    # -- Section 4: Local testimonials --
    # If no area-specific testimonials, fall back to general
    if not testimonials:
        testimonials = _extract_testimonials(profile, max_count=3)

    testimonials_section = PageSection(
        section_id="testimonials",
        section_type="testimonials",
        position=4,
        heading=f"What {area} Customers Say",
        content={
            "heading": f"What {area} Customers Say",
            "testimonials": testimonials,
        },
        css_class_suggestion="testimonials-section",
        notes="Prefer testimonials from customers in this area",
    )

    # -- Section 5: Driving directions --
    loc_address = _extract_address_string(profile)
    directions_content: Dict[str, Any] = {
        "heading": f"How to Reach Us from {area}",
    }
    if loc_address:
        directions_content["business_address"] = loc_address
        directions_content["directions_note"] = f"We are conveniently located to serve {area}. Call for specific directions or visit our office."
        directions_content["estimated_drive_time"] = f"Contact us for estimated drive time from {area}"
    else:
        directions_content["directions_note"] = f"We are a mobile service — we come to you in {area}. No need to visit our office."

    directions = PageSection(
        section_id="driving_directions",
        section_type="driving_directions",
        position=5,
        heading=f"How to Reach Us from {area}",
        content=directions_content,
        css_class_suggestion="directions-section",
        notes="Include Google Maps directions link if business has a physical location",
    )

    # -- Section 6: Area-specific offers --
    area_offers = PageSection(
        section_id="area_offers",
        section_type="area_offers",
        position=6,
        heading=f"Special Offer for {area} Residents",
        content={
            "heading": f"Special Offer for {area} Residents",
            "offer_note": f"Ask about our current promotions available to {area} customers.",
            "cta": {
                "text": f"Call {phone} for Details" if phone else "Contact Us for Details",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone" if phone else "form",
            },
        },
        css_class_suggestion="area-offers",
        notes="Include area-specific promotions if available",
    )

    # -- Section 7: CTA block --
    cta_block = PageSection(
        section_id="cta_bottom",
        section_type="cta_block",
        position=7,
        heading=f"Call Your {area} {svc_type} Experts",
        content={
            "heading": f"Call Your {area} {svc_type} Experts",
            "body": f"Get a free estimate for {svc_type.lower()} in {area}. {biz_name} delivers reliable results, guaranteed.",
            "cta": {
                "text": f"Call {phone}" if phone else "Contact Us",
                "url": f"tel:{phone}" if phone else "/contact",
                "type": "phone",
            },
            "secondary_cta": {
                "text": "Request a Quote Online",
                "url": "/contact",
                "type": "form",
            },
            "trust_element": "Free estimates. No obligation.",
        },
        css_class_suggestion="cta-block",
        notes="Full-width section with contrasting background",
    )

    sections = [hero, area_content, services_section, testimonials_section, directions, area_offers, cta_block]

    # Schema
    local_biz_schema = _generate_local_business_schema(profile)
    # Override areaServed to this specific area
    local_biz_schema["areaServed"] = [{"@type": "City", "name": area}]
    svc_schemas = [_generate_service_schema(_to_dict(s), profile) for s in area_services]

    page_schema: List[Dict[str, Any]] = [local_biz_schema]
    page_schema.extend(svc_schemas)

    # Internal links
    internal_links: List[Dict[str, str]] = []
    internal_links.extend(_build_service_page_links(profile)[:4])
    # Link to other area pages
    for other_area in _extract_service_areas(profile):
        if other_area.lower() != area.lower():
            internal_links.append({
                "text": f"{svc_type} in {other_area}",
                "url": f"/service-areas/{_slugify(other_area)}",
                "context": "service_area_page",
            })
    internal_links.append({"text": "Contact Us", "url": "/contact", "context": "contact_page"})
    internal_links.append({"text": "Back to Home", "url": "/", "context": "homepage"})

    slug = f"service-areas/{_slugify(area)}"
    title = _build_meta_title("service_area_page", profile, area=area)
    meta_desc = _build_meta_description("service_area_page", profile, area=area)
    og_tags = _build_og_tags("service_area_page", title, meta_desc, profile, slug)

    base_url = _extract_website_url(profile)
    canonical = f"{base_url.rstrip('/')}/{slug}" if base_url else None

    page = PageStructure(
        page_type="service_area_page",
        title=title,
        meta_description=meta_desc,
        slug=slug,
        sections=sections,
        page_schema=page_schema,
        internal_links=internal_links,
        canonical_url=canonical,
        og_tags=og_tags,
    )

    return page.model_dump()


def build_contact_page(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a contact/quote request page for a local service business.

    Parameters
    ----------
    profile:
        A BusinessProfile dict.

    Returns
    -------
    dict
        Serialized ``PageStructure``.
    """
    biz_name = _extract_business_name(profile)
    city = _extract_city(profile)
    phone = _extract_phone(profile)
    email = _extract_email(profile)
    address = _extract_address_string(profile)
    loc = _extract_primary_location(profile)
    offers = _extract_offers(profile)
    trust_indicators = _extract_trust_indicators(profile)
    primary_svc = _extract_primary_service(profile)

    trust_raw = _safe_get(profile, "trust", default={})
    if hasattr(trust_raw, "model_dump"):
        trust_raw = trust_raw.model_dump()
    elif not isinstance(trust_raw, dict):
        trust_raw = {}

    # -- Section 1: Contact hero --
    hero = PageSection(
        section_id="hero",
        section_type="hero",
        position=1,
        heading=f"Contact {biz_name}",
        content={
            "headline": "Get Your Free Quote",
            "subheadline": f"Call {phone} or fill out the form below" if phone else "Fill out the form below to get started",
            "phone_prominent": phone or "",
        },
        css_class_suggestion="hero-section contact-hero",
        notes="Phone number must be the most prominent element",
    )

    # -- Section 2: Form section --
    service_options = [str(_safe_get(_to_dict(o), "name", default="")) for o in offers if _safe_get(_to_dict(o), "name")]

    form_section = PageSection(
        section_id="form_section",
        section_type="form_section",
        position=2,
        heading="Request a Free Quote",
        content={
            "heading": "Request a Free Quote",
            "fields": [
                {"name": "full_name", "label": "Your Name", "type": "text", "required": True},
                {"name": "phone", "label": "Phone Number", "type": "tel", "required": True},
                {"name": "email", "label": "Email Address", "type": "email", "required": False},
                {"name": "service_needed", "label": "Service Needed", "type": "select", "required": True, "options": service_options},
                {"name": "message", "label": "Tell Us About Your Project", "type": "textarea", "required": False},
                {"name": "preferred_contact", "label": "Preferred Contact Method", "type": "select", "required": False, "options": ["Phone", "Email", "Text"]},
            ],
            "submit_text": "Request a Free Quote",
            "privacy_note": "We respect your privacy. Your information is never shared.",
        },
        css_class_suggestion="form-section",
        notes="Minimal required fields (name, phone or email, service). Form must be above the fold on desktop.",
    )

    # -- Section 3: Contact info --
    contact_info_content: Dict[str, Any] = {
        "heading": "Contact Information",
    }
    if phone:
        contact_info_content["phone"] = phone
    if email:
        contact_info_content["email"] = email
    if address:
        contact_info_content["address"] = address
    contact_info_content["response_time"] = "We respond within 1 hour during business hours"

    contact_info = PageSection(
        section_id="contact_info",
        section_type="contact_info",
        position=3,
        heading="Contact Information",
        content=contact_info_content,
        css_class_suggestion="contact-info",
        notes="Phone, email, address, and response time commitment",
    )

    # -- Section 4: Hours and map --
    hours = _safe_get(loc, "hours", default={})
    if isinstance(hours, dict):
        hours_dict = dict(hours)
    else:
        hours_dict = {}

    hours_map = PageSection(
        section_id="hours_map",
        section_type="hours_map",
        position=4,
        heading="Hours & Location",
        content={
            "heading": "Hours & Location",
            "hours": hours_dict,
            "map_embed_suggestion": f"Embed Google Map for {address}" if address else f"Embed Google Map centered on {city}" if city else "Embed Google Map for business location",
            "directions_note": f"We are conveniently located in {city}." if city else "",
            "after_hours_note": (
                "After-hours calls are handled by our KaiCalls AI receptionist. "
                "Leave a message any time and we will return your call during the next business day."
            ),
        },
        css_class_suggestion="hours-map-section",
        notes="Business hours + Google Maps embed. Mention after-hours AI receptionist availability.",
    )

    # -- Section 5: Trust signals --
    credentials: List[str] = []
    certs = _safe_get(trust_raw, "certifications", default=[])
    if isinstance(certs, list):
        credentials.extend(str(c) for c in certs)
    licenses_list = _safe_get(trust_raw, "licenses", default=[])
    if isinstance(licenses_list, list):
        credentials.extend(str(lic) for lic in licenses_list)
    if _safe_get(trust_raw, "insurance_details"):
        credentials.append("Fully Insured")

    why_choose = [ind["text"] for ind in trust_indicators]
    if not why_choose:
        why_choose = ["Locally owned and operated", "Honest upfront pricing", "100% satisfaction guarantee"]

    trust_section = PageSection(
        section_id="credentials",
        section_type="credentials",
        position=5,
        heading=f"Why Customers Choose {biz_name}",
        content={
            "heading": f"Why Customers Choose {biz_name}",
            "credentials": credentials,
            "why_choose_us": why_choose,
        },
        css_class_suggestion="trust-section",
        notes="Credentials, certifications, and trust bullet list",
    )

    # -- Section 6: What to expect --
    what_to_expect = PageSection(
        section_id="what_to_expect",
        section_type="what_to_expect",
        position=6,
        heading="What Happens After You Reach Out",
        content={
            "heading": "What Happens After You Reach Out",
            "steps": [
                {
                    "number": 1,
                    "title": "We Respond Quickly",
                    "description": f"A {biz_name} team member will call you within 1 hour during business hours to discuss your project.",
                },
                {
                    "number": 2,
                    "title": "Free On-Site Assessment",
                    "description": f"We schedule a convenient time to evaluate your {primary_svc.lower() if primary_svc else 'project'} needs in person.",
                },
                {
                    "number": 3,
                    "title": "Detailed Quote — No Obligation",
                    "description": "You receive a transparent, itemized quote. No hidden fees, no pressure. Take the time you need to decide.",
                },
            ],
        },
        css_class_suggestion="what-to-expect",
        notes="Set expectations for form submission follow-up process",
    )

    sections = [hero, form_section, contact_info, hours_map, trust_section, what_to_expect]

    # Schema
    local_biz_schema = _generate_local_business_schema(profile)
    contact_point_schema: Dict[str, Any] = {
        "@context": SCHEMA_CONTEXT,
        "@type": "ContactPoint",
        "contactType": "customer service",
    }
    if phone:
        contact_point_schema["telephone"] = phone
    if email:
        contact_point_schema["email"] = email

    page_schema: List[Dict[str, Any]] = [local_biz_schema, contact_point_schema]

    # Internal links
    internal_links: List[Dict[str, str]] = []
    internal_links.extend(_build_service_page_links(profile)[:4])
    internal_links.extend(_build_area_page_links(profile)[:3])
    internal_links.append({"text": "Back to Home", "url": "/", "context": "homepage"})

    slug = "contact"
    title = _build_meta_title("contact_page", profile)
    meta_desc = _build_meta_description("contact_page", profile)
    og_tags = _build_og_tags("contact_page", title, meta_desc, profile, slug)

    base_url = _extract_website_url(profile)
    canonical = f"{base_url.rstrip('/')}/{slug}" if base_url else None

    page = PageStructure(
        page_type="contact_page",
        title=title,
        meta_description=meta_desc,
        slug=slug,
        sections=sections,
        page_schema=page_schema,
        internal_links=internal_links,
        canonical_url=canonical,
        og_tags=og_tags,
    )

    return page.model_dump()


# ===================================================================
# Public API
# ===================================================================

__all__ = [
    # Models
    "PageSection",
    "PageStructure",
    # Builders
    "build_homepage",
    "build_service_page",
    "build_service_area_page",
    "build_contact_page",
    # Helpers (exposed for testing / reuse)
    "VALID_SECTION_TYPES",
]

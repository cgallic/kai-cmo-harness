"""Enrichment layer — Google Places (signal-only) + Apollo (stored phone).

Both are gated on env-var keys. If no key is set, the function returns None
and the pipeline emits records without that enrichment.

PLACES ToS reminder (https://developers.google.com/maps/documentation/places/web-service/policies):
  Only `place_id` is exempt from the no-caching rule. Phone, website, types,
  rating, etc. must NOT be warehoused. Here we fetch them at scoring time
  and persist ONLY: place_id + our derived booleans (has_listed_phone,
  has_website, is_operational, category_bucket, review_count_bucket).
  For the dialable phone the human-call leg needs, use Apollo (license
  permits storage) or a storage-permitted scraper (Outscraper/Apify).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

import requests

PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.nationalPhoneNumber,"
    "places.websiteUri,places.businessStatus,places.types,"
    "places.userRatingCount"
)


@dataclass
class PlacesSignal:
    place_id: Optional[str]
    has_listed_phone: bool
    has_website: bool
    is_operational: bool
    category_bucket: str
    review_count_bucket: str

    @property
    def found(self) -> bool:
        return self.place_id is not None


# Phone-dependent local-service Google categories (ICP target).
_CATEGORY_BUCKETS: dict[str, set[str]] = {
    "ICP_HOME_SERVICES": {
        "plumber", "electrician", "roofing_contractor", "general_contractor",
        "hvac_contractor", "moving_company", "locksmith",
        "pest_control_service", "house_cleaning_service",
        "landscaping_service", "tree_service", "painter",
        "appliance_repair_service",
    },
    "ICP_HEALTH": {
        "dentist", "doctor", "physiotherapist", "chiropractor",
        "medical_clinic", "veterinary_care",
    },
    "ICP_PROFESSIONAL": {
        "lawyer", "accounting", "real_estate_agency",
        "insurance_agency", "tax_consultant",
    },
    "ICP_PERSONAL": {
        "beauty_salon", "hair_care", "spa", "gym", "yoga_studio",
    },
    "ICP_HOSPITALITY": {
        "restaurant", "cafe", "bakery", "bar",
    },
}


def _bucket_for(types: list[str]) -> str:
    t = set(types or [])
    for bucket, members in _CATEGORY_BUCKETS.items():
        if t & members:
            return bucket
    return "OTHER"


def _review_bucket(count: Optional[int]) -> str:
    if count is None or count == 0:
        return "none"
    if count < 10:
        return "few"
    return "many"


def places_lookup(name: str, city: str, state: str, *, api_key: Optional[str] = None) -> Optional[PlacesSignal]:
    """Text Search → first match → ToS-safe derived booleans.

    Returns None when no API key is set (signals caller to skip).
    Returns PlacesSignal with .found=False when the API ran but no match was found.
    """
    key = api_key or PLACES_API_KEY
    if not key:
        return None
    query = f"{name} {city} {state}".strip()
    try:
        resp = requests.post(
            PLACES_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": PLACES_FIELD_MASK,
            },
            data=json.dumps({"textQuery": query, "pageSize": 1}),
            timeout=15,
        )
    except requests.RequestException:
        return PlacesSignal(None, False, False, False, "OTHER", "none")
    if resp.status_code != 200:
        return PlacesSignal(None, False, False, False, "OTHER", "none")
    places = (resp.json() or {}).get("places") or []
    if not places:
        return PlacesSignal(None, False, False, False, "OTHER", "none")
    p = places[0]
    return PlacesSignal(
        place_id=p.get("id"),
        has_listed_phone=bool(p.get("nationalPhoneNumber")),
        has_website=bool(p.get("websiteUri")),
        is_operational=(p.get("businessStatus") == "OPERATIONAL"),
        category_bucket=_bucket_for(p.get("types") or []),
        review_count_bucket=_review_bucket(p.get("userRatingCount")),
    )


@dataclass
class ApolloSignal:
    owner_first_name: Optional[str]
    owner_last_name: Optional[str]
    business_phone: Optional[str]
    phone_is_mobile: Optional[bool]
    business_email: Optional[str]
    website: Optional[str]


def apollo_lookup(name: str, city: str, state: str, *, api_key: Optional[str] = None) -> Optional[ApolloSignal]:
    """Apollo enrichment by company name + location.

    Stub: returns None when no key, otherwise returns an empty ApolloSignal.
    Full implementation: POST /api/v1/organizations/search by domain or name,
    then /api/v1/people/search for the owner contact. Left as TODO so the
    pipeline runs end-to-end without Apollo credentials.
    """
    key = api_key or APOLLO_API_KEY
    if not key:
        return None
    # TODO: implement Apollo organizations/search + people/search.
    return ApolloSignal(None, None, None, None, None, None)


def score_priority(places: Optional[PlacesSignal], apollo: Optional[ApolloSignal]) -> str:
    """P1 (hottest, no phone/site) → P3 (has phone). P_unknown when no enrichment ran."""
    if places is None and apollo is None:
        return "P_unknown"
    has_phone = False
    has_site = False
    if places and places.found:
        has_phone = has_phone or places.has_listed_phone
        has_site = has_site or places.has_website
    if apollo and apollo.business_phone:
        has_phone = True
    if apollo and apollo.website:
        has_site = True
    if not has_phone and not has_site:
        return "P1"
    if has_site and not has_phone:
        return "P2"
    if has_phone:
        return "P3"
    return "P_unknown"

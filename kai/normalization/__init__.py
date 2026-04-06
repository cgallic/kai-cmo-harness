"""Normalization layer for the Kai Marketing OS.

Provides pure functions that convert messy, inconsistent business data
into canonical identifiers.  Every downstream system -- audits,
archetypes, channel matching, proposals -- consumes normalized output
from this package.

Submodules
----------
channels
    Marketing channel name normalization (``"FB"`` -> ``"facebook"``).
locations
    US address, state, city, and ZIP normalization.
metadata
    Industry, business model, archetype, and stage normalization.
offers
    Offer name, price range, CTA, and margin tier normalization.

Quick Usage
-----------
>>> from kai.normalization import normalize_channel, normalize_state
>>> normalize_channel("Google My Business")
'gbp'
>>> normalize_state("California")
'CA'
"""

from __future__ import annotations

from kai.normalization.channels import (
    CHANNEL_ALIASES,
    get_canonical_channels,
    normalize_channel,
    normalize_channel_list,
)
from kai.normalization.locations import (
    format_full_address,
    normalize_city,
    normalize_service_area,
    normalize_state,
    normalize_zip,
)
from kai.normalization.metadata import (
    normalize_archetype,
    normalize_business_model,
    normalize_industry,
    normalize_stage,
)
from kai.normalization.offers import (
    normalize_cta,
    normalize_margin_tier,
    normalize_offer_name,
    normalize_price_range,
)

__all__ = [
    # channels
    "CHANNEL_ALIASES",
    "get_canonical_channels",
    "normalize_channel",
    "normalize_channel_list",
    # locations
    "format_full_address",
    "normalize_city",
    "normalize_service_area",
    "normalize_state",
    "normalize_zip",
    # metadata
    "normalize_archetype",
    "normalize_business_model",
    "normalize_industry",
    "normalize_stage",
    # offers
    "normalize_cta",
    "normalize_margin_tier",
    "normalize_offer_name",
    "normalize_price_range",
]

"""Offer and product/service normalization for the Kai Marketing OS.

Normalizes offer names, price ranges, CTAs, and margin tiers into
consistent formats consumed by the offer-matching and proposal systems.

Examples
--------
>>> normalize_offer_name("  a/c repair  ")
'AC Repair'
>>> normalize_price_range("200 to 500")
'$200-500'
>>> normalize_cta("book now")
'Book Now'
>>> normalize_margin_tier("thin")
'low'
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Offer name patterns
# ---------------------------------------------------------------------------

# Common abbreviation expansions applied to offer names
_OFFER_ABBREVIATIONS: dict[str, str] = {
    "a/c": "AC",
    "ac": "AC",
    "hvac": "HVAC",
    "diy": "DIY",
    "seo": "SEO",
    "ppc": "PPC",
    "pr": "PR",
    "crm": "CRM",
    "roi": "ROI",
    "ui": "UI",
    "ux": "UX",
    "api": "API",
    "it": "IT",
    "hr": "HR",
    "vip": "VIP",
    "cpa": "CPA",
    "cfo": "CFO",
    "ceo": "CEO",
    "llc": "LLC",
}

# ---------------------------------------------------------------------------
# CTA aliases
# ---------------------------------------------------------------------------

CTA_ALIASES: dict[str, str] = {
    "book now": "Book Now",
    "book": "Book Now",
    "book a call": "Book Now",
    "book appointment": "Book Now",
    "get a quote": "Get Quote",
    "get quote": "Get Quote",
    "request a quote": "Get Quote",
    "request quote": "Get Quote",
    "free quote": "Get Quote",
    "call us": "Call Now",
    "call now": "Call Now",
    "call": "Call Now",
    "call today": "Call Now",
    "free estimate": "Get Free Estimate",
    "get free estimate": "Get Free Estimate",
    "free consultation": "Get Free Estimate",
    "schedule": "Schedule Now",
    "schedule now": "Schedule Now",
    "schedule a call": "Schedule Now",
    "schedule appointment": "Schedule Now",
    "learn more": "Learn More",
    "find out more": "Learn More",
    "read more": "Learn More",
    "buy now": "Buy Now",
    "buy": "Buy Now",
    "purchase": "Buy Now",
    "order now": "Buy Now",
    "shop now": "Buy Now",
    "start free trial": "Start Free Trial",
    "free trial": "Start Free Trial",
    "try free": "Start Free Trial",
    "try it free": "Start Free Trial",
    "get started": "Get Started",
    "start now": "Get Started",
    "sign up": "Sign Up",
    "signup": "Sign Up",
    "register": "Sign Up",
    "subscribe": "Subscribe",
    "download": "Download Now",
    "download now": "Download Now",
    "contact us": "Contact Us",
    "contact": "Contact Us",
    "get in touch": "Contact Us",
    "request demo": "Request Demo",
    "request a demo": "Request Demo",
    "see demo": "Request Demo",
    "book demo": "Request Demo",
}

# ---------------------------------------------------------------------------
# Margin tier aliases
# ---------------------------------------------------------------------------

MARGIN_TIER_ALIASES: dict[str, str] = {
    "low": "low",
    "thin": "low",
    "slim": "low",
    "tight": "low",
    "narrow": "low",
    "medium": "medium",
    "moderate": "medium",
    "mid": "medium",
    "average": "medium",
    "normal": "medium",
    "high": "high",
    "fat": "high",
    "good": "high",
    "strong": "high",
    "healthy": "high",
    "premium": "premium",
    "luxury": "premium",
    "ultra": "premium",
    "very high": "premium",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_offer_name(raw: Optional[str]) -> Optional[str]:
    """Normalize an offer/service name: title-case, expand known
    abbreviations, strip trailing punctuation, and collapse whitespace.

    Parameters
    ----------
    raw : str or None
        Raw offer name.

    Returns
    -------
    str or None
        Cleaned offer name, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_offer_name("  a/c repair  ")
    'AC Repair'
    >>> normalize_offer_name("window cleaning!!!")
    'Window Cleaning'
    >>> normalize_offer_name("hvac installation")
    'HVAC Installation'
    >>> normalize_offer_name(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Strip trailing punctuation (but not periods that are part of abbreviations)
    cleaned = re.sub(r"[!?,;:]+$", "", cleaned).strip()

    # Collapse whitespace
    cleaned = " ".join(cleaned.split())

    # Title-case
    titled = cleaned.title()

    # Expand known abbreviations — replace words that match known abbreviation keys
    words = titled.split()
    result_words: list[str] = []
    for word in words:
        lower_word = word.lower().rstrip(".")
        if lower_word in _OFFER_ABBREVIATIONS:
            result_words.append(_OFFER_ABBREVIATIONS[lower_word])
        else:
            result_words.append(word)

    return " ".join(result_words)


def normalize_price_range(raw: Optional[str]) -> Optional[str]:
    """Normalize a price range into a consistent format.

    Standardizes to ``"$X-Y"`` for ranges, ``"$X/mo"`` for subscriptions,
    or ``"Free"`` for free offerings.

    Parameters
    ----------
    raw : str or None
        Raw price string.

    Returns
    -------
    str or None
        Normalized price string, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_price_range("200 to 500")
    '$200-500'
    >>> normalize_price_range("200-500 dollars")
    '$200-500'
    >>> normalize_price_range("$49 per month")
    '$49/mo'
    >>> normalize_price_range("49.99/mo")
    '$49.99/mo'
    >>> normalize_price_range("free")
    'Free'
    >>> normalize_price_range(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Free
    if cleaned.lower() in ("free", "$0", "0", "no cost", "complimentary"):
        return "Free"

    # Subscription pattern: number + per/slash + period
    # Match: "$49 per month", "49.99/mo", "$99/year", "29 per month"
    sub_match = re.match(
        r"^\$?(\d+(?:\.\d{1,2})?)\s*(?:per|/)\s*"
        r"(month|mo|yr|year|week|wk|day|annual|annually)",
        cleaned,
        re.IGNORECASE,
    )
    if sub_match:
        amount = sub_match.group(1)
        period = sub_match.group(2).lower()
        # Normalize period abbreviation
        period_map: dict[str, str] = {
            "month": "mo",
            "mo": "mo",
            "year": "yr",
            "yr": "yr",
            "annual": "yr",
            "annually": "yr",
            "week": "wk",
            "wk": "wk",
            "day": "day",
        }
        norm_period = period_map.get(period, period)
        return f"${amount}/{norm_period}"

    # Range pattern: number to/- number  (with optional $ and "dollars")
    range_match = re.match(
        r"^\$?(\d+(?:\.\d{1,2})?)\s*(?:to|-|–|—)\s*\$?(\d+(?:\.\d{1,2})?)"
        r"(?:\s*(?:dollars|usd|\$))?",
        cleaned,
        re.IGNORECASE,
    )
    if range_match:
        low = range_match.group(1)
        high = range_match.group(2)
        return f"${low}-{high}"

    # Single price: "$X" or "X dollars"
    single_match = re.match(
        r"^\$?(\d+(?:\.\d{1,2})?)(?:\s*(?:dollars|usd))?$",
        cleaned,
        re.IGNORECASE,
    )
    if single_match:
        amount = single_match.group(1)
        return f"${amount}"

    # Already formatted with $ — return as-is after stripping
    if cleaned.startswith("$"):
        return cleaned

    # No pattern match — return stripped input
    return cleaned


def normalize_cta(raw: Optional[str]) -> Optional[str]:
    """Normalize a call-to-action string to a standard form.

    Maps known CTA variants to their canonical phrasing and title-cases
    unrecognized CTAs.

    Parameters
    ----------
    raw : str or None
        Raw CTA text.

    Returns
    -------
    str or None
        Normalized CTA, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_cta("book now")
    'Book Now'
    >>> normalize_cta("get a quote")
    'Get Quote'
    >>> normalize_cta("call us")
    'Call Now'
    >>> normalize_cta("free estimate")
    'Get Free Estimate'
    >>> normalize_cta("schedule")
    'Schedule Now'
    >>> normalize_cta("learn more")
    'Learn More'
    >>> normalize_cta("buy now")
    'Buy Now'
    >>> normalize_cta("start free trial")
    'Start Free Trial'
    >>> normalize_cta(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    key = cleaned.lower()
    canonical = CTA_ALIASES.get(key)
    if canonical is not None:
        return canonical

    # Fallback: title-case
    return cleaned.title()


def normalize_margin_tier(raw: Optional[str]) -> Optional[str]:
    """Normalize a margin tier to one of: ``"low"``, ``"medium"``,
    ``"high"``, ``"premium"``.

    Parameters
    ----------
    raw : str or None
        Margin tier description.

    Returns
    -------
    str or None
        Canonical margin tier, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_margin_tier("thin")
    'low'
    >>> normalize_margin_tier("moderate")
    'medium'
    >>> normalize_margin_tier("fat")
    'high'
    >>> normalize_margin_tier("luxury")
    'premium'
    >>> normalize_margin_tier(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = MARGIN_TIER_ALIASES.get(key)
    if canonical is not None:
        return canonical

    return key

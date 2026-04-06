"""Channel name normalization for the Kai Marketing OS.

Converts any variant of a marketing channel name to a canonical lowercase
identifier.  Downstream systems (audits, archetype matching, channel presence)
always receive consistent keys regardless of how the operator typed them in.

Examples
--------
>>> normalize_channel("FB")
'facebook'
>>> normalize_channel("Google My Business")
'gbp'
>>> normalize_channel("  TikTok Shop  ")
'tiktok_shop'
"""

from __future__ import annotations

from typing import List, Optional

# ---------------------------------------------------------------------------
# Canonical channel identifiers
# ---------------------------------------------------------------------------

_CANONICAL_CHANNELS: List[str] = sorted([
    "amazon",
    "amazon_ads",
    "email",
    "facebook",
    "ga4",
    "gbp",
    "google_ads",
    "gsc",
    "instagram",
    "linkedin",
    "linkedin_ads",
    "meta_ads",
    "microsoft_ads",
    "nextdoor",
    "pinterest",
    "podcast",
    "pr",
    "seo",
    "sms",
    "snapchat",
    "tiktok",
    "tiktok_shop",
    "website",
    "x_twitter",
    "yelp",
    "youtube",
])

# ---------------------------------------------------------------------------
# Alias lookup table  (lowercased variant -> canonical)
# ---------------------------------------------------------------------------

CHANNEL_ALIASES: dict[str, str] = {
    # Facebook / Meta (social)
    "fb": "facebook",
    "facebook": "facebook",
    "meta": "facebook",
    # Instagram
    "ig": "instagram",
    "instagram": "instagram",
    "insta": "instagram",
    # Google Business Profile
    "google my business": "gbp",
    "gmb": "gbp",
    "gbp": "gbp",
    "google business profile": "gbp",
    "google business": "gbp",
    # Google Ads
    "google ads": "google_ads",
    "google adwords": "google_ads",
    "adwords": "google_ads",
    "gads": "google_ads",
    # Meta Ads (paid)
    "meta ads": "meta_ads",
    "facebook ads": "meta_ads",
    "fb ads": "meta_ads",
    "instagram ads": "meta_ads",
    # LinkedIn
    "linkedin": "linkedin",
    "li": "linkedin",
    # LinkedIn Ads
    "linkedin ads": "linkedin_ads",
    # TikTok
    "tiktok": "tiktok",
    "tik tok": "tiktok",
    "tt": "tiktok",
    # TikTok Shop
    "tiktok shop": "tiktok_shop",
    # X / Twitter
    "x": "x_twitter",
    "twitter": "x_twitter",
    "x.com": "x_twitter",
    # YouTube
    "youtube": "youtube",
    "yt": "youtube",
    # Pinterest
    "pinterest": "pinterest",
    # Snapchat
    "snapchat": "snapchat",
    "snap": "snapchat",
    # Email
    "email": "email",
    "email marketing": "email",
    # SMS
    "sms": "sms",
    "text": "sms",
    "text marketing": "sms",
    # SEO
    "seo": "seo",
    "organic search": "seo",
    # Website
    "website": "website",
    "site": "website",
    "web": "website",
    # Google Search Console
    "google search console": "gsc",
    "gsc": "gsc",
    # Google Analytics
    "google analytics": "ga4",
    "ga4": "ga4",
    "ga": "ga4",
    # Nextdoor
    "nextdoor": "nextdoor",
    # Yelp
    "yelp": "yelp",
    # Amazon
    "amazon": "amazon",
    # Amazon Ads
    "amazon ads": "amazon_ads",
    # Microsoft / Bing Ads
    "microsoft ads": "microsoft_ads",
    "bing ads": "microsoft_ads",
    # Podcast
    "podcast": "podcast",
    "podcasting": "podcast",
    # PR / Press
    "pr": "pr",
    "press": "pr",
    "press releases": "pr",
    "public relations": "pr",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_channel(raw: Optional[str]) -> Optional[str]:
    """Return the canonical channel identifier for *raw*.

    Matching is case-insensitive and ignores leading/trailing whitespace.
    If no alias matches, the input is lowercased with spaces replaced by
    underscores so it still forms a usable key.

    Parameters
    ----------
    raw : str or None
        The raw channel name as entered by the user.

    Returns
    -------
    str or None
        Canonical channel identifier, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_channel("FB")
    'facebook'
    >>> normalize_channel("Google My Business")
    'gbp'
    >>> normalize_channel("  TikTok Shop  ")
    'tiktok_shop'
    >>> normalize_channel("Some New Platform")
    'some_new_platform'
    >>> normalize_channel(None) is None
    True
    """
    if raw is None:
        return None

    key = raw.strip().lower()
    if not key:
        return ""

    canonical = CHANNEL_ALIASES.get(key)
    if canonical is not None:
        return canonical

    # Fallback: lowercase with underscores
    return key.replace(" ", "_")


def normalize_channel_list(raw_list: Optional[List[str]]) -> List[str]:
    """Normalize each channel name, deduplicate, and return sorted.

    Parameters
    ----------
    raw_list : list of str, or None
        Raw channel names.

    Returns
    -------
    list of str
        Sorted, deduplicated list of canonical channel identifiers.

    Examples
    --------
    >>> normalize_channel_list(["FB", "facebook", "Instagram", "IG"])
    ['facebook', 'instagram']
    >>> normalize_channel_list(None)
    []
    >>> normalize_channel_list([])
    []
    """
    if not raw_list:
        return []

    seen: set[str] = set()
    result: List[str] = []
    for raw in raw_list:
        normalized = normalize_channel(raw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)

    return sorted(result)


def get_canonical_channels() -> List[str]:
    """Return the full sorted list of canonical channel identifiers.

    Examples
    --------
    >>> 'facebook' in get_canonical_channels()
    True
    >>> 'gbp' in get_canonical_channels()
    True
    """
    return list(_CANONICAL_CHANNELS)

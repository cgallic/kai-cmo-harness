"""Location normalization for the Kai Marketing OS.

Normalizes US addresses, states, cities, ZIP codes, and service areas into
consistent formats so downstream systems (geography matching, local SEO
audits, GBP management) work with clean data.

Examples
--------
>>> normalize_state("California")
'CA'
>>> normalize_city("NYC")
'New York City'
>>> normalize_zip("90210-1234")
'90210'
"""

from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# US States + DC + Territories  (name/abbreviation/common variant -> code)
# ---------------------------------------------------------------------------

STATE_ALIASES: dict[str, str] = {
    # Alabama
    "alabama": "AL", "al": "AL", "ala": "AL",
    # Alaska
    "alaska": "AK", "ak": "AK",
    # Arizona
    "arizona": "AZ", "az": "AZ", "ariz": "AZ",
    # Arkansas
    "arkansas": "AR", "ar": "AR", "ark": "AR",
    # California
    "california": "CA", "ca": "CA", "calif": "CA", "cal": "CA", "cal.": "CA",
    # Colorado
    "colorado": "CO", "co": "CO", "colo": "CO",
    # Connecticut
    "connecticut": "CT", "ct": "CT", "conn": "CT",
    # Delaware
    "delaware": "DE", "de": "DE", "del": "DE",
    # Florida
    "florida": "FL", "fl": "FL", "fla": "FL",
    # Georgia
    "georgia": "GA", "ga": "GA",
    # Hawaii
    "hawaii": "HI", "hi": "HI",
    # Idaho
    "idaho": "ID", "id": "ID",
    # Illinois
    "illinois": "IL", "il": "IL", "ill": "IL",
    # Indiana
    "indiana": "IN", "in": "IN", "ind": "IN",
    # Iowa
    "iowa": "IA", "ia": "IA",
    # Kansas
    "kansas": "KS", "ks": "KS", "kan": "KS", "kans": "KS",
    # Kentucky
    "kentucky": "KY", "ky": "KY",
    # Louisiana
    "louisiana": "LA", "la": "LA",
    # Maine
    "maine": "ME", "me": "ME",
    # Maryland
    "maryland": "MD", "md": "MD",
    # Massachusetts
    "massachusetts": "MA", "ma": "MA", "mass": "MA",
    # Michigan
    "michigan": "MI", "mi": "MI", "mich": "MI",
    # Minnesota
    "minnesota": "MN", "mn": "MN", "minn": "MN",
    # Mississippi
    "mississippi": "MS", "ms": "MS", "miss": "MS",
    # Missouri
    "missouri": "MO", "mo": "MO",
    # Montana
    "montana": "MT", "mt": "MT", "mont": "MT",
    # Nebraska
    "nebraska": "NE", "ne": "NE", "neb": "NE", "nebr": "NE",
    # Nevada
    "nevada": "NV", "nv": "NV", "nev": "NV",
    # New Hampshire
    "new hampshire": "NH", "nh": "NH",
    # New Jersey
    "new jersey": "NJ", "nj": "NJ",
    # New Mexico
    "new mexico": "NM", "nm": "NM",
    # New York
    "new york": "NY", "ny": "NY",
    # North Carolina
    "north carolina": "NC", "nc": "NC",
    # North Dakota
    "north dakota": "ND", "nd": "ND",
    # Ohio
    "ohio": "OH", "oh": "OH",
    # Oklahoma
    "oklahoma": "OK", "ok": "OK", "okla": "OK",
    # Oregon
    "oregon": "OR", "or": "OR", "ore": "OR",
    # Pennsylvania
    "pennsylvania": "PA", "pa": "PA", "penn": "PA", "penna": "PA",
    # Rhode Island
    "rhode island": "RI", "ri": "RI",
    # South Carolina
    "south carolina": "SC", "sc": "SC",
    # South Dakota
    "south dakota": "SD", "sd": "SD",
    # Tennessee
    "tennessee": "TN", "tn": "TN", "tenn": "TN",
    # Texas
    "texas": "TX", "tx": "TX", "tex": "TX",
    # Utah
    "utah": "UT", "ut": "UT",
    # Vermont
    "vermont": "VT", "vt": "VT",
    # Virginia
    "virginia": "VA", "va": "VA",
    # Washington
    "washington": "WA", "wa": "WA", "wash": "WA",
    # West Virginia
    "west virginia": "WV", "wv": "WV",
    # Wisconsin
    "wisconsin": "WI", "wi": "WI", "wis": "WI", "wisc": "WI",
    # Wyoming
    "wyoming": "WY", "wy": "WY", "wyo": "WY",
    # DC
    "district of columbia": "DC", "dc": "DC", "d.c.": "DC", "washington dc": "DC",
    "washington d.c.": "DC", "washington, dc": "DC", "washington, d.c.": "DC",
    # Territories
    "puerto rico": "PR", "pr": "PR",
    "guam": "GU", "gu": "GU",
    "u.s. virgin islands": "VI", "us virgin islands": "VI",
    "virgin islands": "VI", "vi": "VI",
    "american samoa": "AS", "as": "AS",
    "northern mariana islands": "MP", "mp": "MP",
}

# ---------------------------------------------------------------------------
# City abbreviation lookup (top 20 US city aliases)
# ---------------------------------------------------------------------------

CITY_ALIASES: dict[str, str] = {
    "nyc": "New York City",
    "new york city": "New York City",
    "la": "Los Angeles",
    "los angeles": "Los Angeles",
    "chi": "Chicago",
    "chicago": "Chicago",
    "philly": "Philadelphia",
    "philadelphia": "Philadelphia",
    "sf": "San Francisco",
    "san francisco": "San Francisco",
    "san fran": "San Francisco",
    "dc": "Washington",
    "atl": "Atlanta",
    "atlanta": "Atlanta",
    "dal": "Dallas",
    "dallas": "Dallas",
    "hou": "Houston",
    "houston": "Houston",
    "phx": "Phoenix",
    "phoenix": "Phoenix",
    "sa": "San Antonio",
    "san antonio": "San Antonio",
    "sd": "San Diego",
    "san diego": "San Diego",
    "sj": "San Jose",
    "san jose": "San Jose",
    "jax": "Jacksonville",
    "jacksonville": "Jacksonville",
    "clt": "Charlotte",
    "charlotte": "Charlotte",
    "indy": "Indianapolis",
    "indianapolis": "Indianapolis",
    "sea": "Seattle",
    "seattle": "Seattle",
    "den": "Denver",
    "denver": "Denver",
    "bos": "Boston",
    "boston": "Boston",
    "lv": "Las Vegas",
    "vegas": "Las Vegas",
    "las vegas": "Las Vegas",
}

# Prefix abbreviation expansion for cities
_CITY_PREFIX_MAP: dict[str, str] = {
    "st.": "Saint",
    "st ": "Saint ",
    "ft.": "Fort",
    "ft ": "Fort ",
    "mt.": "Mount",
    "mt ": "Mount ",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_state(raw: Optional[str]) -> Optional[str]:
    """Convert a US state name, abbreviation, or common variant to the
    two-letter uppercase USPS code.

    Returns the input unchanged (stripped) if not recognized.

    Parameters
    ----------
    raw : str or None
        State name or abbreviation.

    Returns
    -------
    str or None
        Two-letter state code, the stripped input if unrecognized, or
        ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_state("California")
    'CA'
    >>> normalize_state("ca")
    'CA'
    >>> normalize_state("calif")
    'CA'
    >>> normalize_state("Cal.")
    'CA'
    >>> normalize_state(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Remove trailing period for abbreviations like "Cal."
    key = cleaned.rstrip(".").lower()
    # Also try the original lowered form (handles "cal." -> "cal." in table)
    for attempt in (key, cleaned.lower()):
        code = STATE_ALIASES.get(attempt)
        if code is not None:
            return code

    # Return stripped original if not found
    return cleaned


def normalize_city(raw: Optional[str]) -> Optional[str]:
    """Normalize a city name: expand abbreviations, title-case, and clean
    whitespace.

    Handles common city abbreviations (NYC, LA, SF, etc.) and prefix
    abbreviations (St. -> Saint, Ft. -> Fort, Mt. -> Mount).

    Parameters
    ----------
    raw : str or None
        City name or abbreviation.

    Returns
    -------
    str or None
        Normalized city name, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_city("NYC")
    'New York City'
    >>> normalize_city("LA")
    'Los Angeles'
    >>> normalize_city("new york city")
    'New York City'
    >>> normalize_city("st. louis")
    'Saint Louis'
    >>> normalize_city(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Check alias table first (case-insensitive)
    alias_result = CITY_ALIASES.get(cleaned.lower())
    if alias_result is not None:
        return alias_result

    # Expand prefix abbreviations
    lower = cleaned.lower()
    for prefix, expansion in _CITY_PREFIX_MAP.items():
        if lower.startswith(prefix):
            rest = cleaned[len(prefix):]
            cleaned = expansion + rest
            break

    # Collapse extra whitespace and title-case
    normalized = " ".join(cleaned.split())
    return normalized.title()


def normalize_zip(raw: Optional[str]) -> Optional[str]:
    """Normalize a US ZIP code to a 5-digit string.

    Strips non-digit characters, handles ZIP+4 format, and pads with
    leading zeros.

    Parameters
    ----------
    raw : str or None
        ZIP code in any common format.

    Returns
    -------
    str or None
        Five-digit ZIP string, empty string if invalid, or ``None`` if
        *raw* is ``None``.

    Examples
    --------
    >>> normalize_zip("90210")
    '90210'
    >>> normalize_zip("90210-1234")
    '90210'
    >>> normalize_zip("7032")
    '07032'
    >>> normalize_zip("abc")
    ''
    >>> normalize_zip(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Handle ZIP+4: take the part before the dash
    base = cleaned.split("-")[0].strip()

    # Strip to digits only
    digits = re.sub(r"\D", "", base)

    if not digits:
        return ""

    # Pad to 5 digits
    padded = digits.zfill(5)

    # Must be exactly 5 digits after padding
    if len(padded) != 5:
        return ""

    return padded


def normalize_service_area(raw: Optional[str]) -> Optional[str]:
    """Clean up a freeform service-area string.

    Normalizes embedded state names/abbreviations, standardizes
    formatting (e.g. "los angeles, ca" becomes "Los Angeles, CA"),
    and trims excessive whitespace.

    Parameters
    ----------
    raw : str or None
        Freeform service area description.

    Returns
    -------
    str or None
        Normalized service area string, or ``None`` if *raw* is ``None``.

    Examples
    --------
    >>> normalize_service_area("los angeles, ca")
    'Los Angeles, CA'
    >>> normalize_service_area("  dallas ,  texas  ")
    'Dallas, TX'
    >>> normalize_service_area(None) is None
    True
    """
    if raw is None:
        return None

    cleaned = raw.strip()
    if not cleaned:
        return ""

    # Collapse whitespace
    cleaned = " ".join(cleaned.split())

    # Try to split on comma to find "City, State" pattern
    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        city_part = normalize_city(parts[0]) or parts[0]
        if len(parts) > 1 and parts[1]:
            state_part = normalize_state(parts[1])
            if state_part is not None:
                return f"{city_part}, {state_part}"
            return f"{city_part}, {parts[1].title()}"
        return city_part

    # No comma — try to see if the last word is a state
    tokens = cleaned.split()
    if len(tokens) >= 2:
        # Try last token as state
        candidate = tokens[-1]
        state_result = normalize_state(candidate)
        if state_result is not None and state_result != candidate.strip():
            city_tokens = tokens[:-1]
            city_raw = " ".join(city_tokens)
            city_normalized = normalize_city(city_raw) or city_raw.title()
            return f"{city_normalized}, {state_result}"

        # Try last two tokens as state (e.g. "New York")
        if len(tokens) >= 3:
            candidate_two = " ".join(tokens[-2:])
            state_result_two = normalize_state(candidate_two)
            if state_result_two is not None and state_result_two != candidate_two.strip():
                city_tokens = tokens[:-2]
                city_raw = " ".join(city_tokens)
                city_normalized = normalize_city(city_raw) or city_raw.title()
                return f"{city_normalized}, {state_result_two}"

    # Fallback: title-case the whole thing
    return cleaned.title()


def format_full_address(
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
) -> str:
    """Combine address components into a standard US address string.

    Skips ``None`` or empty components and normalizes each part.

    Parameters
    ----------
    address : str or None
        Street address line.
    city : str or None
        City name.
    state : str or None
        State name or abbreviation.
    zip_code : str or None
        ZIP code.

    Returns
    -------
    str
        Formatted address string. May be empty if all inputs are empty.

    Examples
    --------
    >>> format_full_address("123 Main St", "new york city", "ny", "10001")
    '123 Main St, New York City, NY 10001'
    >>> format_full_address(None, "la", "california", "90001")
    'Los Angeles, CA 90001'
    >>> format_full_address(None, None, None, None)
    ''
    """
    parts: list[str] = []

    # Address line — light cleanup only (preserve street formatting)
    if address and address.strip():
        parts.append(" ".join(address.strip().split()))

    # City
    normalized_city = normalize_city(city) if city else None
    if normalized_city:
        parts.append(normalized_city)

    # State + ZIP combined
    normalized_state = normalize_state(state) if state else None
    normalized_zip = normalize_zip(zip_code) if zip_code else None

    if normalized_state and normalized_zip:
        parts.append(f"{normalized_state} {normalized_zip}")
    elif normalized_state:
        parts.append(normalized_state)
    elif normalized_zip:
        parts.append(normalized_zip)

    return ", ".join(parts)

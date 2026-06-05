"""Registered-agent / formation-service blocklist.

If the filed RA name matches one of these (case-insensitive substring),
the address on file is the formation service's office, not the real
business — drop the record (the "RA-trap" — 30–50% of US LLC filings).

Add new aliases as you spot them in the data.
"""
from __future__ import annotations

# Lowercase substrings.
RA_BLOCKLIST: tuple[str, ...] = (
    "legalzoom",
    "northwest registered agent",
    "zenbusiness",
    "registered agents inc",
    "registered agent solutions",
    "harbor compliance",
    "corporation service company",
    "c t corporation",
    "ct corporation",
    "cogency global",
    "incorp services",
    "incorp ",                       # trailing space avoids "incorporated"
    "inc authority",
    "bizee",
    "incfile",
    "swyft filings",
    "rocket lawyer",
    "mycorporation",
    "usa corporate services",
    "the corporation trust company",
    "the company corporation",
    "national registered agents",
    "spiegel & utrera",
    "stripe atlas",
    "firstbase",
    "doola",
    "tailor brands",
    "paracorp",
    "vcorp services",
    "united states corporation agents",
)


def is_blocklisted_ra(ra_name: str) -> bool:
    if not ra_name:
        return False
    n = ra_name.lower()
    return any(b in n for b in RA_BLOCKLIST)

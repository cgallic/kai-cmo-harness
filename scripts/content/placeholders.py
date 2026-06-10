#!/usr/bin/env python3
"""
Placeholder detection — nothing template-shaped ships in final copy.

Promoted from memory/edge-cases.md EC-06: the original check only caught
bracketed tokens like [company], so natural-language placeholders ("insert
your company name here", "Pricing: TBD") shipped. This module catches both.

Stdlib only, no config import, so it is testable and reusable outside the
engine (gates, skills, hooks).
"""

from __future__ import annotations

import re

# Terms that make a bracketed/braced token a template field rather than prose.
PLACEHOLDER_TERMS = re.compile(
    r"\b(company|business|brand|service|city|location|page|title|keyword|name|"
    r"cta|url|date|number|proof|review|offer|headline|subheadline|insert|"
    r"placeholder|example)\b",
    re.IGNORECASE,
)

# High-precision natural-language placeholder patterns. False positives block
# publishes, so every pattern here must be something that genuinely never
# belongs in final copy.
NL_PLACEHOLDER_PATTERNS = [
    # "insert your company name", "add the client logo", "fill in a date"
    re.compile(
        r"\b(?:insert|enter|fill in|replace with|swap in)\s+(?:your|the|a|an)\s+"
        r"(?:company|business|brand|client|product|service|city|location|name|"
        r"logo|url|link|date|number|phone|cta|headline|testimonial|stat|statistic|keyword)\b",
        re.IGNORECASE,
    ),
    # "your company name here", "your city here"
    re.compile(
        r"\byour\s+(?:company|business|brand|client|product|service|city|location)"
        r"(?:\s+name)?\s+here\b",
        re.IGNORECASE,
    ),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
    re.compile(r"\b(?:TODO|TBD|FIXME)\b"),
    # "<your company>", "<insert testimonial>"
    re.compile(r"<(?:your|insert)\s+[^>\n]{2,40}>", re.IGNORECASE),
    # "{{company_name}}" template syntax
    re.compile(r"\{\{[^}\n]{2,60}\}\}"),
]


def find_bracket_placeholders(content: str) -> list[str]:
    """Find bracketed template placeholders like [company name]."""
    placeholders = []
    content = content or ""
    for match in re.finditer(r"\[([^\]\n]{2,80})\]", content):
        # Skip markdown links: [text](url)
        if match.end() < len(content) and content[match.end()] == "(":
            continue
        value = match.group(1).strip()
        if PLACEHOLDER_TERMS.search(value):
            placeholders.append(match.group(0))
    return placeholders


def find_natural_language_placeholders(content: str) -> list[str]:
    """Find prose-form placeholders the bracket regex misses."""
    placeholders = []
    content = content or ""
    # Single-brace template fields like {company_name}
    for match in re.finditer(r"\{([a-z][a-z0-9_ ]{1,40})\}", content, re.IGNORECASE):
        # Underscores defeat \b word boundaries, so normalize before matching
        if PLACEHOLDER_TERMS.search(match.group(1).replace("_", " ")):
            placeholders.append(match.group(0))
    for pattern in NL_PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(content):
            placeholders.append(match.group(0))
    return placeholders


def find_placeholders(content: str, limit: int = 10) -> list[str]:
    """All template placeholders (bracketed + natural-language), deduped."""
    seen = set()
    results = []
    for hit in find_bracket_placeholders(content) + find_natural_language_placeholders(content):
        if hit not in seen:
            seen.add(hit)
            results.append(hit)
    return results[:limit]

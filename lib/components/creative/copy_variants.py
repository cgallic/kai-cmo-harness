"""
Copy Variants Generator — Generate N variants of any copy block.

Takes a base copy string and generates variations using different
angles, tones, or structures. Useful for A/B testing.

Usage:
    variants = generate_variants("Stop losing calls to voicemail", n=3, style="hooks")
"""

import re
from typing import Optional


# Hook variant transformations
_HOOK_TRANSFORMS = [
    # Pain → Question
    lambda text: f"What if you could {_extract_benefit(text).lower()}?" if _extract_benefit(text) else text,
    # Pain → Data
    lambda text: re.sub(r'^(.*)', r'73% of businesses \1 Here\'s the fix.', text) if len(text) < 80 else text,
    # Pain → Direct
    lambda text: f"You're {_extract_pain(text).lower()}. There's a better way." if _extract_pain(text) else text,
    # Pain → Social proof
    lambda text: f"500+ companies fixed this: {text.lower()}" if len(text) < 60 else text,
    # Pain → Contrarian
    lambda text: f"Everyone says {_extract_topic(text).lower()} is hard. It's not." if _extract_topic(text) else text,
]


def generate_variants(
    base_copy: str,
    n: int = 3,
    style: str = "hooks",  # hooks, ctas, headlines, descriptions
    context: dict = None,
) -> list[str]:
    """
    Generate N copy variants from a base string.
    Returns a list of variant strings (including the original).
    """
    variants = [base_copy]

    if style == "hooks":
        for transform in _HOOK_TRANSFORMS[:n - 1]:
            try:
                variant = transform(base_copy)
                if variant != base_copy and variant not in variants:
                    variants.append(variant)
            except Exception:
                continue

    elif style == "ctas":
        cta_variants = _generate_cta_variants(base_copy, n)
        variants.extend(cta_variants[:n - 1])

    elif style == "headlines":
        headline_variants = _generate_headline_variants(base_copy, n)
        variants.extend(headline_variants[:n - 1])

    # Pad with minor rewrites if we don't have enough
    while len(variants) < n:
        variants.append(base_copy)

    return variants[:n]


def _generate_cta_variants(base: str, n: int) -> list[str]:
    """Generate CTA variants."""
    variants = []
    # First-person version
    if "your" in base.lower():
        variants.append(base.replace("Your", "My").replace("your", "my"))
    elif "my" in base.lower():
        variants.append(base.replace("My", "Your").replace("my", "your"))

    # Add urgency
    if "now" not in base.lower() and "today" not in base.lower():
        variants.append(f"{base} Now")
        variants.append(f"{base} — Free")

    # Remove unnecessary words
    short = re.sub(r'\b(just|simply|easily|quickly)\b', '', base, flags=re.IGNORECASE).strip()
    if short != base:
        variants.append(short)

    return variants


def _generate_headline_variants(base: str, n: int) -> list[str]:
    """Generate headline variants."""
    variants = []
    # Number prefix
    variants.append(f"3 Ways to {base}")
    # Question form
    variants.append(f"Why {base}?")
    # How-to form
    variants.append(f"How to {base} (Without {_extract_pain(base) or 'Breaking the Bank'})")
    return variants


def _extract_benefit(text: str) -> str:
    """Extract the implied benefit from copy."""
    # Look for positive outcome words
    match = re.search(r'(never miss|always|every|save|earn|grow|double|triple|increase)', text, re.IGNORECASE)
    if match:
        return text[match.start():]
    return ""


def _extract_pain(text: str) -> str:
    """Extract the pain point from copy."""
    match = re.search(r'(losing|missing|struggling|failing|broken|slow|expensive|frustrat)', text, re.IGNORECASE)
    if match:
        return text[match.start():match.end() + 20].strip().rstrip(".")
    return ""


def _extract_topic(text: str) -> str:
    """Extract the main topic from copy."""
    # Take the first noun phrase (rough heuristic)
    words = text.split()[:5]
    return " ".join(words).rstrip(".,!?")

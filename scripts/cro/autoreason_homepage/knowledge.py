"""Knowledge layer for the homepage AutoReason CRO loop.

Two jobs:
1. Brand-lock + banned-phrase validators (adapted from scripts/ads/autoreason/).
2. The current KaiCalls homepage incumbent + PRD-derived context bundle.
"""

from __future__ import annotations

import re
from typing import Any

from .trace import HomepageZones

# ---------------------------------------------------------------------------
# Brand lock — adapted from scripts/ads/autoreason/knowledge.py
# ---------------------------------------------------------------------------

# Drift phrases that pull KaiCalls back to framing the PRD explicitly rejects.
# Note "digital secretary" is on this list — the current homepage uses it, so
# the incumbent itself is expected to fail brand-lock. That's the point.
DRIFT_PHRASES = [
    "ai receptionist",
    "virtual receptionist",
    "answering service",
    "call answering service",
    "auto attendant",
    "virtual assistant",
    "phone bot",
    "robo-receptionist",
    "digital secretary",
]

_SENTENCE_SPLIT = re.compile(r"(?:[.!?]+|\n+|\s+\|\s+|\s+•\s+|\s+-\s+)")
_KAI = r"(?:kaicalls?|kai\s+calls|kai)"
_CONTRAST_CUES = [
    r"\bvs\b", r"\bversus\b", r"\bthan\b", r"\binstead of\b", r"\brather than\b",
    r"\bunlike\b", r"\bcompared to\b", r"\bnot (?:a|an|just|the|your|our)\b",
    r"\bmost\b", r"\bthose\b", r"\bevery\b", r"\ball (?:other|the)\b",
    r"\btried\b", r"\bused to\b",
    r"\btheir\b", r"\bcompetitors?\b",
    r"\bother\b",
    r"\$\s*\d", r"/\s*mo\b", r"per minute\b", r"per month\b", r"/\s*month\b",
]
_CONTRAST_RE = re.compile("|".join(_CONTRAST_CUES))


def _is_comparison_usage(sentences: list[str], idx: int, phrase: str) -> bool:
    """A drift phrase is fine when it's anchoring a contrast (vs / than /
    instead of / $price), not describing KaiCalls's identity."""
    sentence = sentences[idx]
    if phrase not in sentence:
        return False
    has_kai = bool(re.search(rf"\b{_KAI}\b", sentence))
    has_contrast = bool(_CONTRAST_RE.search(sentence))
    if has_contrast:
        return True
    if has_kai:
        return False
    neighbours = []
    if idx > 0:
        neighbours.append(sentences[idx - 1])
    if idx + 1 < len(sentences):
        neighbours.append(sentences[idx + 1])
    for n in neighbours:
        n_has_kai = bool(re.search(rf"\b{_KAI}\b", n))
        n_has_contrast = bool(_CONTRAST_RE.search(n))
        if n_has_kai and n_has_contrast:
            return True
        if n_has_kai and re.search(r"\$\s*\d|/\s*mo\b|/\s*month\b", n):
            return True
    return False


def validate_brand_lock(zones: HomepageZones) -> list[str]:
    blob = " ".join(
        [zones.hero_headline, zones.sub_hero, zones.primary_cta, zones.feature_frame]
    ).lower()
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(blob) if s.strip()]
    hits: list[str] = []
    for phrase in DRIFT_PHRASES:
        if phrase not in blob:
            continue
        phrase_idxs = [i for i, s in enumerate(sentences) if phrase in s]
        if not phrase_idxs:
            hits.append(phrase)
            continue
        if all(_is_comparison_usage(sentences, i, phrase) for i in phrase_idxs):
            continue
        hits.append(phrase)
    return hits


# ---------------------------------------------------------------------------
# Banned phrases — Tier 1 from scripts/quality_gates/banned_word_check.py
# ---------------------------------------------------------------------------

BANNED_PHRASES_TIER1 = [
    "leverage", "utilize", "utilise", "synergy", "synergies",
    "innovative", "innovation", "seamless", "robust", "scalable",
    "holistic", "empower", "empowering", "transformative", "revolutionize",
    "ecosystem", "game-changer", "game changer", "paradigm shift",
    "thought leader", "best practices", "cutting-edge", "cutting edge",
    "state-of-the-art", "value proposition", "value-add", "pain points",
    "key takeaway", "actionable insights", "next level", "move the needle",
]


def validate_banned_phrases(zones: HomepageZones) -> list[str]:
    blob = " ".join(
        [zones.hero_headline, zones.sub_hero, zones.primary_cta, zones.feature_frame]
    ).lower()
    return [p for p in BANNED_PHRASES_TIER1 if p in blob]


# ---------------------------------------------------------------------------
# Live homepage incumbent (from www.kaicalls.com, captured 2026-05-13)
# ---------------------------------------------------------------------------

def live_incumbent() -> HomepageZones:
    """The current homepage zones as they appear on www.kaicalls.com.

    Captured 2026-05-13 via WebFetch. Update by hand when the homepage ships
    new copy — the loop has no live scraper.
    """
    return HomepageZones(
        hero_headline="Your Digital Secretary",
        sub_hero=(
            "He answers your business calls, captures leads, books appointments, "
            "and gives you a briefing when you call in. No app. No dashboard. "
            "Just call Kai."
        ),
        primary_cta="Get Your Secretary",
        feature_frame="What Kai Does",
    )


# ---------------------------------------------------------------------------
# PRD-derived context — replaces the ads loop's Meta perf snapshot
# ---------------------------------------------------------------------------

PRD_CONTEXT = {
    "positioning_lock": (
        "KaiCalls is the new business phone number with AI built in — an "
        "intelligent business number for small businesses where every missed "
        "call costs money."
    ),
    "anti_positioning": [
        "AI receptionist",
        "virtual receptionist",
        "answering service",
        "auto attendant",
        "digital secretary",
        "bolt-on app",
        "Kai-as-a-person",
    ],
    "tagline_candidate": (
        "Stop losing calls. Your number answers, follows up, and shows what it "
        "recovered."
    ),
    "core_promise": (
        "The number itself answers, qualifies, books, follows up, and shows "
        "recovered revenue. No app, no dashboard required."
    ),
    "target_icp": {
        "primary": [
            "solo operators",
            "local service businesses",
            "home services (plumbing, electrical, HVAC, roofing)",
            "legal intake",
            "clinics, med spas, dental",
            "any SMB where missed calls = lost revenue",
        ],
        "secondary": [
            "multi-location SMBs",
            "agencies running phone for clients",
            "vertical SaaS embedding phone agents",
        ],
        "non_buyer_traits": [
            "not technical",
            "does not care about SIP / CPaaS / IVR",
            "phone-heavy daily ops",
            "hands-full operator (in a truck, in surgery, in court)",
        ],
    },
    "rubric_axes": [
        "Clarity (5-second stranger test)",
        "Specificity (concrete outcome, numbers, named situations)",
        "Mechanism (number is intelligent — how/why, not just what)",
        "Pain-targeting (missed calls = lost jobs/leads/$)",
        "Differentiation (NOT another AI receptionist)",
        "Believability (survives 5-second BS-detector)",
    ],
    "positioning_seeds": [
        "Digital Secretary (current incumbent — Kai-as-a-person frame)",
        "AI Receptionist (the framing the PRD explicitly rejects — for contrast only)",
        "AI Phone System (closer to truth: phone-system-level capability)",
        "Business phone number with AI built in (PRD-locked positioning)",
        "AI-powered revenue system / intelligent business number (PRD long-term framing)",
    ],
    "high_conversion_patterns": [
        # Reference patterns from the ad loop's fixture top-3 — these
        # converted on the same audience.
        "Your phone answers itself",
        "$3k/mo lost to missed calls?",
        "Stop missing calls. Start booking jobs.",
    ],
}


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------

def live_bundle() -> dict:
    """The real KaiCalls homepage + PRD-derived context."""
    return {
        "incumbent": live_incumbent(),
        "context": PRD_CONTEXT,
        "is_fixture": False,
        "source_label": "live www.kaicalls.com (captured 2026-05-13)",
    }


def fixture_bundle() -> dict:
    """A deliberately weak fixture for dry-run validation.

    Models a homepage that's even more off-positioning than the live page so
    the loop has obvious targets to push on.
    """
    incumbent = HomepageZones(
        hero_headline="The Future of Phone Answering",
        sub_hero=(
            "Our innovative AI receptionist leverages cutting-edge technology to "
            "empower your business with seamless call handling. Revolutionize "
            "your customer experience today."
        ),
        primary_cta="Learn More",
        feature_frame="Discover the Power of AI Communication",
    )
    return {
        "incumbent": incumbent,
        "context": PRD_CONTEXT,
        "is_fixture": True,
        "source_label": "FIXTURE — slop-y homepage for dry-run validation",
    }

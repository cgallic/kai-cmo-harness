"""Knowledge layer for the AutoReason ad loop.

Three jobs:
1. Brand-lock + banned-phrase validators (pure, no API).
2. Live Meta loaders (Insights, ad-set perf, top/bottom comps).
3. A fixture path for dry-runs and CI.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

from .trace import AdCopy

# ---------------------------------------------------------------------------
# Brand lock
# ---------------------------------------------------------------------------

KAICALLS_BRAND_LOCK = (
    "the new business phone number with AI built in"
)

# Phrases that signal the draft has drifted off positioning. These map KaiCalls
# back to the framing it explicitly rejects (see memory/kaicalls_positioning.md).
RECEPTIONIST_DRIFT_PHRASES = [
    "ai receptionist",
    "virtual receptionist",
    "answering service",
    "call answering service",
    "auto attendant",
    "virtual assistant",
    "phone bot",
    "robo-receptionist",
]

# Splits a blob of ad copy into sentence-ish chunks. Ad copy is rarely well
# punctuated, so we also break on newlines and bullet/dash list separators.
_SENTENCE_SPLIT = re.compile(r"(?:[.!?]+|\n+|\s+\|\s+|\s+•\s+|\s+-\s+)")

# Matches the brand subject as a whole word: "kai", "kaicalls", "kai calls".
_KAI = r"(?:kaicalls?|kai\s+calls|kai)"

# Words that signal a sentence is contrasting the drift phrase against
# something else (typically Kai or "us"), rather than claiming Kai *is* it.
# Presence of any of these in the same sentence as the drift phrase flips
# the default-reject into an allow.
_CONTRAST_CUES = [
    r"\bvs\b", r"\bversus\b", r"\bthan\b", r"\binstead of\b", r"\brather than\b",
    r"\bunlike\b", r"\bcompared to\b", r"\bnot (?:a|an|just|the|your|our)\b",
    r"\bmost\b", r"\bthose\b", r"\bevery\b", r"\ball (?:other|the)\b",
    r"\btried\b", r"\bused to\b",
    r"\btheir\b", r"\bcompetitors?\b",
    r"\bother\b",
    # Pricing comparison: a $-number or per-month/per-minute token is a strong
    # signal of "X costs Y, Kai costs Z" anchoring.
    r"\$\s*\d", r"/\s*mo\b", r"per minute\b", r"per month\b", r"/\s*month\b",
]
_CONTRAST_RE = re.compile("|".join(_CONTRAST_CUES))


def _is_comparison_usage(
    sentences: list[str], idx: int, phrase: str
) -> bool:
    """True iff the drift phrase in `sentences[idx]` is being used as a
    competitor/category anchor rather than as a description of Kai's identity.

    Decision (in order):
      1. If the sentence itself contains a contrast cue (vs / than /
         instead of / $price / /mo / "tried" / "most" / etc.) → comparison.
      2. If the sentence mentions both the phrase AND Kai with no contrast
         cue → identity drift (e.g. "Kai is an AI receptionist").
      3. If the sentence mentions only the phrase (no Kai), check the
         neighbour sentences (idx-1 and idx+1) for either Kai with a
         contrast cue, or a contrast cue near a price token. That's the
         "Tried answering services. Then I tried Kai." cross-sentence
         contrast pattern, or the "Receptionist: $3,500/mo." line in a
         multi-line price block.
      4. Otherwise → identity drift. Default-reject is the safer policy,
         which matches the fixture-incumbent regression case.
    """
    sentence = sentences[idx]
    if phrase not in sentence:
        return False

    has_kai = bool(re.search(rf"\b{_KAI}\b", sentence))
    has_contrast = bool(_CONTRAST_RE.search(sentence))

    # Rule 1: same-sentence contrast cue
    if has_contrast:
        return True

    # Rule 2: Kai in the same sentence with no contrast → identity drift
    if has_kai:
        return False

    # Rule 3: cross-sentence contrast — look at the immediate neighbours
    neighbours = []
    if idx > 0:
        neighbours.append(sentences[idx - 1])
    if idx + 1 < len(sentences):
        neighbours.append(sentences[idx + 1])
    for n in neighbours:
        n_has_kai = bool(re.search(rf"\b{_KAI}\b", n))
        n_has_contrast = bool(_CONTRAST_RE.search(n))
        # Either Kai-with-contrast next door (e.g. "Then I tried Kai.") or
        # a contrast-with-price next door (e.g. "Kai: $69" on the next row of
        # a price-comparison list).
        if n_has_kai and n_has_contrast:
            return True
        if n_has_kai and re.search(r"\$\s*\d|/\s*mo\b|/\s*month\b", n):
            return True

    # Rule 4: default-reject
    return False


def validate_brand_lock(ad: AdCopy) -> list[str]:
    """Return a list of brand-lock violations. Empty list = clean.

    Default policy: a drift phrase in the copy is identity drift and should be
    rejected. A drift phrase escapes rejection only when it's clearly being
    used as a competitor or category anchor — either via a same-sentence
    contrast cue (vs / than / instead of / $price / /mo / "tried" / etc.) or
    via cross-sentence contrast (a neighbour sentence has Kai + a contrast
    cue or a price). See `_is_comparison_usage` for the full rule set, and
    `test_brand_lock.py` for the canonical examples.
    """
    blob = " ".join([ad.headline, ad.primary_text, ad.description]).lower()
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(blob) if s.strip()]

    hits: list[str] = []
    for phrase in RECEPTIONIST_DRIFT_PHRASES:
        if phrase not in blob:
            continue
        phrase_idxs = [i for i, s in enumerate(sentences) if phrase in s]
        if not phrase_idxs:
            # Phrase straddled a sentence break — be conservative and flag it.
            hits.append(phrase)
            continue
        # If every occurrence is comparison usage it's clean, else it's drift.
        if all(_is_comparison_usage(sentences, i, phrase) for i in phrase_idxs):
            continue
        hits.append(phrase)
    return hits


# ---------------------------------------------------------------------------
# Banned phrases — mirror Tier 1 from scripts/quality_gates/banned_word_check.py
# ---------------------------------------------------------------------------

# Subset focused on ad copy. The full Tier 1 list lives in the quality gate;
# this is the slice that shows up in paid-social drafts.
BANNED_PHRASES_TIER1 = [
    "leverage", "utilize", "utilise", "synergy", "synergies",
    "innovative", "innovation", "seamless", "robust", "scalable",
    "holistic", "empower", "empowering", "transformative", "revolutionize",
    "ecosystem", "game-changer", "game changer", "paradigm shift",
    "thought leader", "best practices", "cutting-edge", "cutting edge",
    "state-of-the-art", "value proposition", "value-add", "pain points",
    "key takeaway", "actionable insights", "next level", "move the needle",
]


def validate_banned_phrases(ad: AdCopy) -> list[str]:
    blob = " ".join([ad.headline, ad.primary_text, ad.description]).lower()
    return [p for p in BANNED_PHRASES_TIER1 if p in blob]


# ---------------------------------------------------------------------------
# Live Meta loaders (require ads_read scope on token)
# ---------------------------------------------------------------------------

BASE = "https://graph.facebook.com/v21.0"


def _token() -> str:
    return os.environ["META_ACCESS_TOKEN"]


def _account() -> str:
    raw = os.environ["META_AD_ACCOUNT_ID"]
    return raw if raw.startswith("act_") else f"act_{raw}"


def _ads_read_ok() -> bool:
    """Probe the token's scopes. Returns False if ads_read isn't granted."""
    r = requests.get(
        f"{BASE}/debug_token",
        params={"input_token": _token(), "access_token": _token()},
        timeout=10,
    )
    if r.status_code != 200:
        return False
    scopes = r.json().get("data", {}).get("scopes", [])
    return "ads_read" in scopes or "ads_management" in scopes


def list_kaicalls_ad_sets() -> list[dict]:
    """Active KaiCalls ad sets in the account, with last 30d insights."""
    r = requests.get(
        f"{BASE}/{_account()}/adsets",
        params={
            "fields": "id,name,campaign{name},effective_status,daily_budget,targeting,insights.date_preset(last_30d){ctr,cpc,cpm,spend,impressions,clicks,reach,frequency}",
            "filtering": '[{"field":"effective_status","operator":"IN","value":["ACTIVE"]}]',
            "limit": "100",
            "access_token": _token(),
        },
        timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("data", [])
    # Filter to KaiCalls campaigns by name match
    return [
        a for a in items
        if "kaicall" in (a.get("name", "") + a.get("campaign", {}).get("name", "")).lower()
    ]


def lowest_ctr_ad_set(ad_sets: list[dict]) -> dict | None:
    """Pick the ad set with the lowest CTR (must have non-zero impressions)."""
    scored = []
    for a in ad_sets:
        ins = (a.get("insights", {}).get("data") or [{}])[0]
        impressions = int(ins.get("impressions") or 0)
        if impressions < 100:  # too little signal
            continue
        ctr = float(ins.get("ctr") or 0)
        scored.append((ctr, a))
    if not scored:
        return None
    scored.sort(key=lambda kv: kv[0])
    return scored[0][1]


def load_incumbent(ad_set_id: str) -> AdCopy | None:
    """Pull the first active ad in an ad set as the incumbent."""
    r = requests.get(
        f"{BASE}/{ad_set_id}/ads",
        params={
            "fields": "id,name,creative{object_story_spec,effective_object_story_id,title,body,description,call_to_action_type,link_url}",
            "filtering": '[{"field":"effective_status","operator":"IN","value":["ACTIVE"]}]',
            "limit": "5",
            "access_token": _token(),
        },
        timeout=30,
    )
    r.raise_for_status()
    ads = r.json().get("data", [])
    if not ads:
        return None
    creative = ads[0].get("creative", {})
    spec = creative.get("object_story_spec", {})
    link_data = spec.get("link_data", {}) if isinstance(spec, dict) else {}
    return AdCopy(
        headline=creative.get("title") or link_data.get("name", "") or "",
        primary_text=creative.get("body") or link_data.get("message", "") or "",
        description=creative.get("description") or link_data.get("description", "") or "",
        cta=creative.get("call_to_action_type") or "LEARN_MORE",
        link=creative.get("link_url") or link_data.get("link", "https://kaicalls.com"),
    )


def load_perf(ad_set_id: str) -> dict:
    r = requests.get(
        f"{BASE}/{ad_set_id}/insights",
        params={
            "fields": "ctr,cpc,cpm,spend,impressions,clicks,reach,frequency,actions",
            "date_preset": "last_30d",
            "access_token": _token(),
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json().get("data", [])
    return data[0] if data else {}


# ---------------------------------------------------------------------------
# Fixture (clearly labeled in trace)
# ---------------------------------------------------------------------------

def fixture_bundle() -> dict:
    """A stand-in KaiCalls ad and grounding pack for dry-run validation.

    Models a real underperforming ad shape so the loop has something to push
    on. Switch to `live_bundle()` for live runs.
    """
    incumbent = AdCopy(
        headline="Never Miss a Call Again",
        primary_text=(
            "Innovative AI receptionist for small business. Our seamless platform "
            "leverages cutting-edge technology to revolutionize how you handle "
            "missed calls. Start your free trial today!"
        ),
        description="AI Phone Answering",
        cta="LEARN_MORE",
        link="https://kaicalls.com",
    )
    perf = {
        "date_preset": "last_30d",
        "ctr": 0.43,            # %
        "cpc": 4.82,            # $
        "cpl": 89.50,           # $
        "spend": 612.00,        # $
        "impressions": 18420,
        "clicks": 79,
        "reach": 14010,
        "frequency": 1.31,
        "audience": "broad — US SMB owners interested in business phone systems",
    }
    top_ads = [
        {
            "headline": "Your phone answers itself",
            "primary_text": "Plumber, contractor, lawyer — your business number now picks up, qualifies, and books while you're on the job. Set up in 4 minutes.",
            "ctr": 1.81, "cpl": 28.40,
        },
        {
            "headline": "$3k/mo lost to missed calls?",
            "primary_text": "Average SMB misses 27% of inbound calls. KaiCalls gives you a number that answers, screens, and texts you the qualified ones. Try free.",
            "ctr": 1.62, "cpl": 31.10,
        },
        {
            "headline": "Stop missing calls. Start booking jobs.",
            "primary_text": "Your new business number talks like you do, knows your prices, books on your calendar. Forwards the rest to your cell. From $79/mo.",
            "ctr": 1.44, "cpl": 35.80,
        },
    ]
    bottom_ads = [
        {
            "headline": "Discover the Power of AI Communication",
            "primary_text": "Our innovative platform empowers your business to leverage seamless communication solutions for the modern era.",
            "ctr": 0.21, "cpl": 142.00,
        },
        {
            "headline": "Revolutionize Your Customer Experience",
            "primary_text": "Transformative AI-powered receptionist services that scale with your growing business needs.",
            "ctr": 0.27, "cpl": 118.50,
        },
        {
            "headline": "The Future of Phone Answering",
            "primary_text": "Robust, state-of-the-art virtual receptionist designed for forward-thinking businesses.",
            "ctr": 0.31, "cpl": 104.20,
        },
    ]
    return {
        "ad_set_id": "FIXTURE_ad_set_001",
        "ad_set_name": "FIXTURE — KaiCalls Broad SMB Owners (lowest CTR)",
        "incumbent": incumbent,
        "perf": perf,
        "top_ads": top_ads,
        "bottom_ads": bottom_ads,
        "is_fixture": True,
    }


def live_bundle() -> dict:
    """Pull the lowest-CTR active KaiCalls ad set + comps from Meta."""
    if not _ads_read_ok():
        raise RuntimeError(
            "Meta token cannot read ad insights. Use fixture_bundle() instead."
        )
    ad_sets = list_kaicalls_ad_sets()
    if not ad_sets:
        raise RuntimeError("No active KaiCalls ad sets found in the account.")
    target = lowest_ctr_ad_set(ad_sets)
    if not target:
        raise RuntimeError("No KaiCalls ad set has enough impressions to score.")
    incumbent = load_incumbent(target["id"])
    if not incumbent:
        raise RuntimeError(f"No active ad found in ad set {target['id']}.")
    perf = load_perf(target["id"])
    # Top/bottom comps: pull all kaicalls ads, rank by CTR, take top-3 / bottom-3
    # excluding the incumbent's ad set.
    top_ads, bottom_ads = _comp_ads(exclude_ad_set_id=target["id"])
    return {
        "ad_set_id": target["id"],
        "ad_set_name": target.get("name", target["id"]),
        "incumbent": incumbent,
        "perf": perf,
        "top_ads": top_ads,
        "bottom_ads": bottom_ads,
        "is_fixture": False,
    }


def _comp_ads(exclude_ad_set_id: str) -> tuple[list[dict], list[dict]]:
    r = requests.get(
        f"{BASE}/{_account()}/ads",
        params={
            "fields": "id,name,adset_id,creative{title,body,description},insights.date_preset(last_90d){ctr,cpc,actions,impressions}",
            "filtering": '[{"field":"effective_status","operator":"IN","value":["ACTIVE","PAUSED"]}]',
            "limit": "100",
            "access_token": _token(),
        },
        timeout=30,
    )
    r.raise_for_status()
    items = []
    for a in r.json().get("data", []):
        if a.get("adset_id") == exclude_ad_set_id:
            continue
        ins = (a.get("insights", {}).get("data") or [{}])[0]
        impressions = int(ins.get("impressions") or 0)
        if impressions < 200:
            continue
        creative = a.get("creative", {})
        items.append({
            "headline": creative.get("title", ""),
            "primary_text": creative.get("body", ""),
            "ctr": float(ins.get("ctr") or 0),
            "cpc": float(ins.get("cpc") or 0),
        })
    items.sort(key=lambda d: -d["ctr"])
    return items[:3], items[-3:][::-1]

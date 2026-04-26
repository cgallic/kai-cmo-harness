"""Knowledge layer for the AutoReason ad loop.

Three jobs:
1. Brand-lock + banned-phrase validators (pure, no API).
2. Live Meta loaders (Insights, ad-set perf, top/bottom comps).
3. A fixture path for dry-runs when the Meta token lacks `ads_read` scope
   (current state — see README).
"""

from __future__ import annotations

import os
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


def validate_brand_lock(ad: AdCopy) -> list[str]:
    """Return a list of brand-lock violations. Empty list = clean."""
    blob = " ".join([ad.headline, ad.primary_text, ad.description]).lower()
    return [p for p in RECEPTIONIST_DRIFT_PHRASES if p in blob]


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
# Fixture (used while Meta token lacks ads_read; clearly labeled in trace)
# ---------------------------------------------------------------------------

def fixture_bundle() -> dict:
    """A stand-in KaiCalls ad and grounding pack for dry-run validation.

    Models a real underperforming ad shape so the loop has something to push
    on. Replace with `live_bundle()` once the Meta token has `ads_read`.
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
            "Meta token lacks ads_read scope. "
            "Use fixture_bundle() or refresh the token in Business Manager."
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

#!/usr/bin/env python3
"""
Kai CMO Harness — Google Ads Optimizer
========================================
AI-powered optimization suggestions for Google Ads campaigns.

Usage:
  python scripts/ads/google_ads_optimize.py --analyze              # Full analysis
  python scripts/ads/google_ads_optimize.py --negatives            # Suggest negative keywords
  python scripts/ads/google_ads_optimize.py --budget               # Budget reallocation
  python scripts/ads/google_ads_optimize.py --pause                # Suggest keywords to pause
  python scripts/ads/google_ads_optimize.py --opportunities        # New keyword opportunities

Uses Google Ads data + Gemini for strategic recommendations.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _gemini(prompt: str) -> str:
    from google.genai import Client as GenaiClient
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "[Set GEMINI_API_KEY for optimization suggestions]"
    client = GenaiClient(api_key=api_key)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()


def _load_ads_data() -> dict:
    """Load Google Ads data (tries API first, falls back to cached)."""
    try:
        from scripts.ads.google_ads import get_campaigns, get_keywords, get_search_terms
        return {
            "campaigns": get_campaigns(30),
            "keywords": get_keywords(days=30),
            "search_terms": get_search_terms(days=30),
        }
    except Exception as e:
        # Try cached data
        cache_path = REPO_ROOT / "data" / "ads" / "google_ads_cache.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text())
        return {"error": str(e), "campaigns": [], "keywords": [], "search_terms": []}


def suggest_negatives(data: dict) -> str:
    """Suggest negative keywords from search terms report."""
    search_terms = data.get("search_terms", [])
    if not search_terms:
        return "No search terms data available."

    # Find search terms with high impressions but low/no conversions
    wasteful = [
        st for st in search_terms
        if st.get("impressions", 0) > 50
        and st.get("conversions", 0) == 0
        and st.get("cost", 0) > 5
    ]

    if not wasteful:
        return "No obvious negative keyword candidates found."

    wasteful_summary = "\n".join(
        f"- \"{st['search_term']}\" — {st['clicks']} clicks, ${st['cost']:.2f} spend, 0 conversions"
        for st in sorted(wasteful, key=lambda x: x.get("cost", 0), reverse=True)[:20]
    )

    return _gemini(f"""Analyze these Google Ads search terms that have spend but zero conversions.
Suggest which should be added as negative keywords and why.

Search terms with zero conversions:
{wasteful_summary}

For each suggestion, explain:
1. The search term to negate
2. Match type (exact, phrase, or broad)
3. Why it's irrelevant (wrong intent, wrong audience, etc.)
4. Estimated monthly savings

Format as a prioritized list. Be specific about match types.""")


def suggest_pauses(data: dict) -> str:
    """Suggest keywords to pause based on performance."""
    keywords = data.get("keywords", [])
    if not keywords:
        return "No keyword data available."

    underperformers = [
        kw for kw in keywords
        if kw.get("clicks", 0) > 20
        and kw.get("conversions", 0) < 1
        and kw.get("quality_score", 10) < 5
    ]

    if not underperformers:
        return "No obvious keywords to pause."

    kw_summary = "\n".join(
        f"- \"{kw['keyword']}\" ({kw['match_type']}) — QS: {kw['quality_score']}, "
        f"{kw['clicks']} clicks, ${kw['cost']:.2f}, {kw['conversions']} conv"
        for kw in sorted(underperformers, key=lambda x: x.get("cost", 0), reverse=True)[:15]
    )

    return _gemini(f"""These Google Ads keywords have low Quality Scores and no conversions despite spend.

Underperforming keywords:
{kw_summary}

For each keyword, recommend:
1. PAUSE — remove entirely (explain why)
2. RESTRUCTURE — move to different ad group with better ad copy
3. RESTRICT — change match type to reduce waste

Prioritize by cost savings. Be specific.""")


def suggest_budget_reallocation(data: dict) -> str:
    """Suggest budget reallocation across campaigns."""
    campaigns = data.get("campaigns", [])
    if not campaigns:
        return "No campaign data available."

    campaign_summary = "\n".join(
        f"- {c['name']}: ${c['cost']:.2f} spend, {c['conversions']:.1f} conv, "
        f"{c['roas']:.2f}x ROAS, {c['ctr']:.1f}% CTR"
        for c in campaigns
    )

    total_spend = sum(c["cost"] for c in campaigns)

    return _gemini(f"""Analyze these Google Ads campaigns and recommend budget reallocation.

Current campaigns (total spend: ${total_spend:.2f}):
{campaign_summary}

Recommend:
1. Which campaigns should get MORE budget (and how much)
2. Which campaigns should get LESS budget (and how much)
3. Any campaigns that should be paused entirely
4. Optimal daily budget for each active campaign

Base recommendations on ROAS, conversion volume, and growth potential.
Show specific dollar amounts, not just percentages.""")


def find_opportunities(data: dict) -> str:
    """Find new keyword opportunities from search terms."""
    search_terms = data.get("search_terms", [])
    keywords = data.get("keywords", [])

    if not search_terms:
        return "No search terms data available."

    # Find high-performing search terms not yet added as keywords
    existing_kws = {kw.get("keyword", "").lower() for kw in keywords}

    opportunities = [
        st for st in search_terms
        if st.get("conversions", 0) > 0
        and st["search_term"].lower() not in existing_kws
    ]

    if not opportunities:
        # Look for high-CTR terms instead
        opportunities = [
            st for st in search_terms
            if st.get("ctr", 0) > 0.05
            and st.get("clicks", 0) > 5
            and st["search_term"].lower() not in existing_kws
        ]

    if not opportunities:
        return "No clear keyword opportunities found in search terms."

    opp_summary = "\n".join(
        f"- \"{st['search_term']}\" — {st['clicks']} clicks, {st['conversions']:.1f} conv, "
        f"{st['ctr']*100:.1f}% CTR, ${st['cost']:.2f}"
        for st in sorted(opportunities, key=lambda x: x.get("conversions", 0), reverse=True)[:15]
    )

    return _gemini(f"""These search terms are converting but aren't yet added as keywords in Google Ads.

High-performing search terms not in keyword lists:
{opp_summary}

For each opportunity:
1. Recommended match type (exact, phrase, or broad)
2. Suggested ad group (new or existing)
3. Recommended bid strategy
4. Expected impact (based on current performance)

Prioritize by conversion potential.""")


def full_analysis(data: dict) -> str:
    """Run full optimization analysis."""
    sections = ["# Google Ads Optimization Report\n"]

    print("  Analyzing negative keywords...")
    sections.append("## Negative Keyword Suggestions\n")
    sections.append(suggest_negatives(data))

    print("  Analyzing underperformers...")
    sections.append("\n## Keywords to Pause/Restructure\n")
    sections.append(suggest_pauses(data))

    print("  Analyzing budget allocation...")
    sections.append("\n## Budget Reallocation\n")
    sections.append(suggest_budget_reallocation(data))

    print("  Finding opportunities...")
    sections.append("\n## New Keyword Opportunities\n")
    sections.append(find_opportunities(data))

    return "\n\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Google Ads optimization suggestions")
    parser.add_argument("--analyze", action="store_true", help="Full optimization analysis")
    parser.add_argument("--negatives", action="store_true", help="Suggest negative keywords")
    parser.add_argument("--pause", action="store_true", help="Suggest keywords to pause")
    parser.add_argument("--budget", action="store_true", help="Budget reallocation suggestions")
    parser.add_argument("--opportunities", action="store_true", help="New keyword opportunities")
    parser.add_argument("--save", help="Save report to file")
    args = parser.parse_args()

    print("Loading Google Ads data...")
    data = _load_ads_data()

    if "error" in data:
        print(f"Warning: Could not load live data: {data['error']}")
        print("Using cached data if available.\n")

    if args.analyze:
        result = full_analysis(data)
    elif args.negatives:
        result = suggest_negatives(data)
    elif args.pause:
        result = suggest_pauses(data)
    elif args.budget:
        result = suggest_budget_reallocation(data)
    elif args.opportunities:
        result = find_opportunities(data)
    else:
        parser.print_help()
        return

    if args.save:
        Path(args.save).write_text(result)
        print(f"\nSaved to {args.save}")
    else:
        print(result)


if __name__ == "__main__":
    main()

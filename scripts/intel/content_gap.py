#!/usr/bin/env python3
"""
Kai CMO Harness — Content Gap Analysis
========================================
Compare your site's keywords (GSC) against competitor keywords.
Output: "They rank for X, you don't."

Usage:
  python scripts/intel/content_gap.py --site myproduct
  python scripts/intel/content_gap.py --site myproduct --competitor "competitor1.com"
  python scripts/intel/content_gap.py --site myproduct --min-volume 100

Data sources:
  - Your keywords: Google Search Console
  - Competitor keywords: Gemini analysis (free) or DataForSEO API (paid, more accurate)
"""

import argparse
import json
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.yaml.example"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _get_your_keywords(site_key: str) -> set[str]:
    """Get your keywords from GSC."""
    config = _load_config()
    products = {p["id"]: p for p in config.get("products", [])}
    product = products.get(site_key, {})
    gsc_env = product.get("gsc_url_env", "")
    gsc_url = os.environ.get(gsc_env, "")

    if not gsc_url:
        print(f"  No GSC configured for {site_key}")
        return set()

    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from analytics.search_console import SearchConsoleAnalytics
        gsc = SearchConsoleAnalytics(gsc_url)
        data = gsc.get_queries(days=30, limit=500)
        return {row["query"].lower() for row in data if row.get("query")}
    except Exception as e:
        print(f"  GSC error: {e}")
        return set()


def _get_competitor_keywords_gemini(competitor_url: str) -> list[dict]:
    """Estimate competitor keywords using Gemini (free, less accurate)."""
    try:
        from google.genai import Client as GenaiClient
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return []

        client = GenaiClient(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Analyze {competitor_url} and estimate the top 50 keywords they likely rank for.
Consider their content topics, page titles, meta descriptions, and industry.

Return ONLY a valid JSON array of objects:
[
  {{"keyword": "example keyword", "estimated_position": 5, "estimated_volume": 500, "page": "/blog/example"}},
  ...
]"""
        )
        raw = response.text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return []


def analyze_gaps(site_key: str, competitor_filter: str | None = None):
    """Find content gaps — keywords competitors rank for that you don't."""
    config = _load_config()
    competitors = config.get("competitors", [])

    if competitor_filter:
        competitors = [c for c in competitors if competitor_filter.lower() in c.get("url", "").lower()
                       or competitor_filter.lower() in c.get("name", "").lower()]

    if not competitors:
        print("No competitors configured. Add to config.yaml.")
        return []

    # Get your keywords
    print(f"Fetching your keywords ({site_key})...")
    your_keywords = _get_your_keywords(site_key)
    print(f"  Found {len(your_keywords)} keywords you rank for")

    all_gaps = []

    for comp in competitors:
        print(f"\nAnalyzing: {comp['name']} ({comp['url']})")

        comp_keywords = _get_competitor_keywords_gemini(comp["url"])
        print(f"  Estimated {len(comp_keywords)} competitor keywords")

        # Find gaps
        gaps = []
        for kw_data in comp_keywords:
            kw = kw_data.get("keyword", "").lower()
            if kw and kw not in your_keywords:
                gaps.append({
                    "keyword": kw,
                    "competitor": comp["name"],
                    "competitor_position": kw_data.get("estimated_position", "?"),
                    "estimated_volume": kw_data.get("estimated_volume", 0),
                    "competitor_page": kw_data.get("page", ""),
                })

        # Sort by estimated volume
        gaps.sort(key=lambda x: x.get("estimated_volume", 0), reverse=True)
        all_gaps.extend(gaps)

        print(f"  Content gaps found: {len(gaps)}")
        for gap in gaps[:10]:
            vol = gap.get("estimated_volume", "?")
            print(f"    {gap['keyword']:<40} vol: {vol:>5}  pos: {gap['competitor_position']}")

    return all_gaps


def main():
    parser = argparse.ArgumentParser(description="Content gap analysis")
    parser.add_argument("--site", required=True, help="Your site key (from config.yaml)")
    parser.add_argument("--competitor", help="Filter specific competitor")
    parser.add_argument("--min-volume", type=int, default=0, help="Minimum estimated volume")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--save", help="Save report to file")
    args = parser.parse_args()

    gaps = analyze_gaps(args.site, args.competitor)

    if args.min_volume:
        gaps = [g for g in gaps if g.get("estimated_volume", 0) >= args.min_volume]

    if args.json:
        print(json.dumps(gaps, indent=2))
    elif args.save:
        out = Path(args.save)
        report = f"# Content Gap Analysis — {args.site}\n"
        report += f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"| Keyword | Competitor | Est. Volume | Their Position |\n"
        report += f"|---------|-----------|-------------|----------------|\n"
        for g in gaps:
            report += f"| {g['keyword']} | {g['competitor']} | {g.get('estimated_volume', '?')} | {g.get('competitor_position', '?')} |\n"
        out.write_text(report)
        print(f"Saved {len(gaps)} gaps to {out}")


if __name__ == "__main__":
    main()

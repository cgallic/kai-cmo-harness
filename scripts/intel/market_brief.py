#!/usr/bin/env python3
"""
Kai CMO Harness — Weekly Market Brief
=======================================
Synthesize competitor activity into actionable intelligence.

Usage:
  python scripts/intel/market_brief.py                    # Generate this week's brief
  python scripts/intel/market_brief.py --save weekly.md   # Save to file
  python scripts/intel/market_brief.py --days 14          # Look back 14 days

Uses Gemini to synthesize raw competitor data into strategic recommendations.
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "intel"
COMP_DB = DATA_DIR / "competitors.db"
SERP_DB = DATA_DIR / "serp_tracker.db"


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.yaml.example"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _gather_competitor_data(days: int = 7) -> str:
    """Gather raw competitor data from SQLite databases."""
    sections = []

    # Competitor blog posts
    if COMP_DB.exists():
        conn = sqlite3.connect(str(COMP_DB))
        conn.row_factory = sqlite3.Row

        posts = conn.execute(
            f"SELECT competitor, title, url, published FROM rss_entries "
            f"WHERE discovered_at > datetime('now', '-{days} days') ORDER BY discovered_at DESC"
        ).fetchall()
        if posts:
            sections.append("## New Competitor Blog Posts")
            for p in posts:
                sections.append(f"- [{p['competitor']}] {p['title']} — {p['url']}")

        new_pages = conn.execute(
            f"SELECT competitor, url, first_seen FROM sitemap_pages "
            f"WHERE first_seen > datetime('now', '-{days} days') ORDER BY first_seen DESC LIMIT 20"
        ).fetchall()
        if new_pages:
            sections.append("\n## New Competitor Pages")
            for p in new_pages:
                sections.append(f"- [{p['competitor']}] {p['url']} (found {p['first_seen'][:10]})")

        conn.close()

    # Ranking changes
    if SERP_DB.exists():
        conn = sqlite3.connect(str(SERP_DB))
        conn.row_factory = sqlite3.Row

        alerts = conn.execute(
            f"SELECT keyword, domain, old_position, new_position, change, alert_type "
            f"FROM alerts WHERE created_at > datetime('now', '-{days} days') ORDER BY ABS(change) DESC"
        ).fetchall()
        if alerts:
            sections.append("\n## Ranking Changes")
            for a in alerts:
                direction = "up" if a["alert_type"] == "improved" else "down"
                sections.append(
                    f"- {a['keyword']}: {a['old_position']:.1f} → {a['new_position']:.1f} "
                    f"({direction} {abs(a['change']):.1f} positions) [{a['domain']}]"
                )

        conn.close()

    if not sections:
        return "No competitor data collected yet. Run competitor_monitor.py --check and serp_tracker.py --track first."

    return "\n".join(sections)


def generate_brief(days: int = 7) -> str:
    """Generate a market brief using Gemini to synthesize raw data."""
    config = _load_config()
    products = config.get("products", [])
    product_names = ", ".join(p.get("name", p.get("id", "")) for p in products) or "your products"

    raw_data = _gather_competitor_data(days)

    if "No competitor data" in raw_data:
        return raw_data

    try:
        from google.genai import Client as GenaiClient
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return f"# Raw Competitor Data (Last {days} Days)\n\n{raw_data}\n\n(Set GEMINI_API_KEY for AI-synthesized brief)"

        client = GenaiClient(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""You are a competitive intelligence analyst for {product_names}.
Synthesize this raw competitor data into a weekly market brief.

{raw_data}

Write a market brief with these sections:

# Weekly Market Brief — {datetime.now(timezone.utc).strftime('%B %d, %Y')}

## Key Moves
- What did competitors DO this week? (new content, new pages, messaging shifts)
- What topics are they investing in?

## Ranking Shifts
- Summarize significant ranking changes
- What keywords are competitive right now?

## Opportunities
- What gaps or weaknesses can we exploit?
- What topics should we create content for?

## Threats
- What should we watch out for?
- Any competitive encroachment on our keywords?

## Recommended Actions (This Week)
- 3-5 specific, actionable items with clear deliverables

Be specific and data-driven. Reference actual URLs and keywords from the data."""
        )
        return response.text.strip()
    except Exception as e:
        return f"# Raw Competitor Data (Last {days} Days)\n\n{raw_data}\n\n(Gemini synthesis failed: {e})"


def main():
    parser = argparse.ArgumentParser(description="Generate weekly market brief")
    parser.add_argument("--days", type=int, default=7, help="Lookback period in days")
    parser.add_argument("--save", help="Save brief to file")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    brief = generate_brief(args.days)

    if args.save:
        Path(args.save).write_text(brief)
        print(f"Brief saved to {args.save}")
    elif args.json:
        print(json.dumps({"brief": brief, "days": args.days}))
    else:
        print(brief)


if __name__ == "__main__":
    main()

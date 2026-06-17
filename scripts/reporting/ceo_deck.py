#!/usr/bin/env python3
"""
Kai CMO Harness — CEO Deck Generator
=======================================
Generate a 5-slide marketing deck in markdown format.

Usage:
  python scripts/reporting/ceo_deck.py                          # Generate deck
  python scripts/reporting/ceo_deck.py --save decks/march.md    # Save to file
  python scripts/reporting/ceo_deck.py --site myproduct         # Single product

Output: Markdown slides compatible with Marp, Slidev, or Deckset.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _gemini(prompt: str) -> str:
    from google.genai import Client as GenaiClient
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "[Set GEMINI_API_KEY for AI-generated slides]"
    client = GenaiClient(api_key=api_key)
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()


def _gather_data(site_key: str) -> dict:
    """Gather all available data for the deck."""
    data = {}
    config = _load_config()

    # Content log
    content_log = REPO_ROOT / "data" / "content_log.json"
    if content_log.exists():
        log = json.loads(content_log.read_text())
        data["content_total"] = len(log)
        data["content_winners"] = len([e for e in log if e.get("performance_30d", {}).get("grade") == "winner"])
    else:
        data["content_total"] = 0
        data["content_winners"] = 0

    # Products
    data["products"] = config.get("products", [])
    data["owner"] = config.get("owner", {})

    return data


def generate_deck(site_key: str = "all") -> str:
    """Generate a 5-slide CEO marketing deck."""
    config = _load_config()
    data = _gather_data(site_key)
    now = datetime.now(timezone.utc)
    company = config.get("owner", {}).get("company", "Our Company")

    deck = _gemini(f"""Create a 5-slide marketing deck for a CEO presentation.
Company: {company}
Date: {now.strftime('%B %Y')}
Products: {json.dumps([p.get('name', p.get('id')) for p in data.get('products', [])])}
Content pieces tracked: {data.get('content_total', 0)}
Content winners: {data.get('content_winners', 0)}

Format each slide with "---" separators (Marp/Slidev compatible).
Use this EXACT structure:

---
marp: true
theme: default
---

# Marketing Update — {now.strftime('%B %Y')}
{company}

---

## Slide 1: Key Metrics
Present 4-6 key metrics in a clean table:
- Traffic (sessions, users)
- Leads (new, conversion rate)
- Content (pieces published, quality score)
- Revenue impact

Use placeholder numbers that look realistic. Mark with [DATA] where real data would go.

---

## Slide 2: Channel Performance
Heatmap-style table showing channel health:
| Channel | Status | Trend | Key Metric |
Red/Yellow/Green status for each channel (SEO, Paid, Social, Email, Content)

---

## Slide 3: Content Pipeline
- Published this period
- In review
- In progress
- Planned
- Quality score trend
- Top performing pieces

---

## Slide 4: Competitive Landscape
- Key competitor moves
- Our positioning
- Threats and opportunities
- Share of voice

---

## Slide 5: Next Week's Priorities
- 3-5 specific, measurable priorities
- Resource needs
- Blockers to flag
- Key decision needed from leadership

Make it concise. CEOs want numbers, trends, and decisions — not explanations.
Each slide should be readable in 30 seconds.""")

    return deck


def main():
    parser = argparse.ArgumentParser(description="Generate CEO marketing deck")
    parser.add_argument("--site", default="all", help="Site key or 'all'")
    parser.add_argument("--save", help="Save deck to file")
    args = parser.parse_args()

    deck = generate_deck(site_key=args.site)

    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text(deck)
        print(f"Deck saved to {args.save}")
    else:
        print(deck)


if __name__ == "__main__":
    main()

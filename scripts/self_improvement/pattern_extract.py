#!/usr/bin/env python3
"""
Pattern Extractor — Kai Harness Self-Improvement Loop

When content wins (position ≤5, CTR ≥5%, time on page ≥90s):
  1. Extracts what made it work (hook type, persona, format, length)
  2. Appends to knowledge/playbooks/what-works.md
  3. Appends site-specific patterns to knowledge/playbooks/<site>-patterns.md
  4. Runs weekly aggregation to surface statistical patterns

Usage:
  python3 pattern_extract.py --url "https://..."
  python3 pattern_extract.py --weekly --site all
  python3 pattern_extract.py --weekly --site kaicalls
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

from google import genai as google_genai

CONTENT_LOG = "/opt/cmo-analytics/data/content_log.json"
KNOWLEDGE_BASE = "/root/.openclaw/workspace/knowledge/playbooks"
WHAT_WORKS_FILE = f"{KNOWLEDGE_BASE}/what-works.md"

WIN_POSITION = 5
WIN_CTR = 0.05
WIN_TIME_ON_PAGE = 90


def load_log() -> list:
    if not os.path.exists(CONTENT_LOG):
        return []
    with open(CONTENT_LOG) as f:
        return json.load(f)


def is_winner(entry: dict) -> bool:
    perf = entry.get("performance_30d")
    if not perf:
        return False
    gsc = perf.get("gsc", {})
    ga4 = perf.get("ga4", {})
    position = gsc.get("position")
    ctr = gsc.get("ctr", 0)
    duration = ga4.get("avg_session_duration", 0)
    return (
        position is not None
        and position <= WIN_POSITION
        and ctr >= WIN_CTR
        and duration >= WIN_TIME_ON_PAGE
    )


def analyze_winner(entry: dict) -> str:
    """Use Claude to extract what made this piece win."""
    client = google_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    perf = entry.get("performance_30d", {})
    gsc = perf.get("gsc", {})
    ga4 = perf.get("ga4", {})

    prompt = f"""A piece of content performed well. Analyze what made it win.

Content Details:
- Title/Angle: {entry.get("title") or entry.get("keyword")}
- Target Keyword: {entry.get("keyword")}
- Site: {entry.get("site")}
- Format: {entry.get("format")}
- Persona: {entry.get("persona", "unknown")}
- Angle Used: {entry.get("angle", "unknown")}
- Four U's Score: {entry.get("four_us_score", "unknown")}/16

Performance (30-day):
- GSC Position: {gsc.get("position", "N/A")}
- CTR: {(gsc.get("ctr", 0) * 100):.1f}%
- Impressions: {gsc.get("impressions", 0):,}
- Sessions: {ga4.get("sessions", 0):,}
- Avg Duration: {ga4.get("avg_session_duration", 0):.0f}s

Write a concise 3-5 sentence analysis of what likely made this content win.
Focus on: hook type effectiveness, specificity of angle, persona match, format choice.
Be concrete — what specifically worked and why? What can be replicated?
Output ONLY the analysis text, no headers or JSON."""

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()


def append_to_what_works(entry: dict, analysis: str):
    os.makedirs(KNOWLEDGE_BASE, exist_ok=True)

    perf = entry.get("performance_30d", {})
    gsc = perf.get("gsc", {})
    ga4 = perf.get("ga4", {})
    date = entry.get("published_at", "")[:10]
    checked = perf.get("checked_at", "")[:10]

    block = f"""
## {entry.get("title") or entry.get("keyword")} — {entry.get("site")} — {date}
**URL:** {entry.get("url")}
**Keyword:** {entry.get("keyword")}
**Format:** {entry.get("format")} | **Persona:** {entry.get("persona", "N/A")} | **Four U's:** {entry.get("four_us_score", "N/A")}/16
**Angle:** {entry.get("angle", "N/A")}

**30-Day Results (checked {checked}):**
- Position: #{gsc.get("position", "N/A")} | CTR: {(gsc.get("ctr", 0) * 100):.1f}% | Sessions: {ga4.get("sessions", 0):,}
- Avg Duration: {ga4.get("avg_session_duration", 0):.0f}s

**Why it worked:**
{analysis}

---"""

    # Init file if it doesn't exist
    if not os.path.exists(WHAT_WORKS_FILE):
        with open(WHAT_WORKS_FILE, "w") as f:
            f.write("# What Works — Kai Harness Pattern Library\n\n")
            f.write("Auto-updated by pattern_extract.py. Do not edit manually.\n\n")

    with open(WHAT_WORKS_FILE, "a") as f:
        f.write(block + "\n")

    # Also append to site-specific file
    site = entry.get("site", "general")
    site_file = f"{KNOWLEDGE_BASE}/{site}-patterns.md"
    if not os.path.exists(site_file):
        with open(site_file, "w") as f:
            f.write(f"# {site.title()} — Content Patterns\n\n")
    with open(site_file, "a") as f:
        f.write(block + "\n")

    print(f"  Appended to: {WHAT_WORKS_FILE}")
    print(f"  Appended to: {site_file}")


def run_weekly_aggregation(site: str = "all") -> str:
    """Analyze all winners to surface statistical patterns."""
    log = load_log()

    winners = [e for e in log if is_winner(e)]
    if site != "all":
        winners = [e for e in winners if e.get("site") == site]

    if len(winners) < 3:
        return f"Not enough winners yet ({len(winners)}/3 minimum). Keep publishing."

    # Build summary for Claude to analyze
    summary_lines = []
    for w in winners:
        perf = w.get("performance_30d", {})
        gsc = perf.get("gsc", {})
        ga4 = perf.get("ga4", {})
        summary_lines.append(
            f"- [{w.get('site')}] [{w.get('format')}] [{w.get('persona', 'N/A')}] "
            f"Keyword: {w.get('keyword')} | "
            f"Position: {gsc.get('position', 'N/A')} | CTR: {(gsc.get('ctr', 0)*100):.1f}% | "
            f"Duration: {ga4.get('avg_session_duration', 0):.0f}s | "
            f"Four U's: {w.get('four_us_score', 'N/A')}"
        )

    client = google_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = f"""You are analyzing content performance patterns from the Kai Harness system.

Winners ({len(winners)} total):
{chr(10).join(summary_lines)}

Identify 3-5 concrete, statistically-grounded patterns. Examples of good pattern statements:
- "Solo attorney persona outperforms generic 'law firm' angle by 2.4x on sessions"
- "Curiosity gap hooks average CTR 6.2% vs 3.1% for direct-answer hooks"
- "Posts published Tuesday average 23% more first-week impressions than Thursday"

Only state patterns supported by at least 3 data points. Flag sample size.
Format each pattern as: [PATTERN] | [data backing it] | [recommendation]

Output as plain text, one pattern per line."""

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    patterns_text = response.text.strip()

    # Save patterns
    patterns_file = f"{KNOWLEDGE_BASE}/weekly-patterns.md"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(patterns_file, "a") as f:
        scope = site if site != "all" else "all sites"
        f.write(f"\n\n## Pattern Report — {date_str} ({scope})\n\n{patterns_text}\n")

    return patterns_text


def main():
    parser = argparse.ArgumentParser(description="Pattern Extractor")
    parser.add_argument("--url", help="Extract patterns for a specific URL")
    parser.add_argument("--weekly", action="store_true", help="Run weekly aggregation")
    parser.add_argument("--site", default="all", help="Site filter for weekly run")
    args = parser.parse_args()

    if args.url:
        log = load_log()
        entry = next((e for e in log if e["url"] == args.url), None)
        if not entry:
            print(f"URL not in log: {args.url}")
            return
        if not is_winner(entry):
            print(f"Not a winner (no 30-day data or below thresholds): {args.url}")
            return
        print(f"Extracting patterns for: {args.url}")
        analysis = analyze_winner(entry)
        append_to_what_works(entry, analysis)
        print(f"\nAnalysis:\n{analysis}")
        return

    if args.weekly:
        print(f"Running weekly pattern aggregation (site={args.site})...")
        patterns = run_weekly_aggregation(args.site)
        print(f"\nPatterns surfaced:\n{patterns}")
        return

    # Default: process all unprocessed winners
    log = load_log()
    processed = 0
    for entry in log:
        if is_winner(entry) and not entry.get("patterns_extracted"):
            print(f"Processing winner: {entry['url']}")
            analysis = analyze_winner(entry)
            append_to_what_works(entry, analysis)
            entry["patterns_extracted"] = True
            processed += 1

    if processed:
        # Save updated log
        with open(CONTENT_LOG, "w") as f:
            json.dump(log, f, indent=2)
        print(f"\n{processed} winner(s) processed.")
    else:
        print("No unprocessed winners found.")


if __name__ == "__main__":
    main()

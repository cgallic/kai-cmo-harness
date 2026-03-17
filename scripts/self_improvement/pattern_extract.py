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
import logging
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

from google import genai as google_genai

# Use centralized config
from scripts.harness_config import get_config

_CFG = get_config()

CONTENT_LOG = str(_CFG.content_log)
KNOWLEDGE_BASE = str(_CFG.knowledge_base)
WHAT_WORKS_FILE = f"{KNOWLEDGE_BASE}/what-works.md"

WIN_POSITION = _CFG.thresholds.win_position
WIN_CTR = _CFG.thresholds.win_ctr
WIN_TIME_ON_PAGE = _CFG.thresholds.win_time_on_page

log = logging.getLogger("pattern-extract")
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
)


# ── Gemini client with timeout ───────────────────────────────────────────
_CONSECUTIVE_FAILURES = 0

def _gemini(prompt: str) -> str:
    """Call Gemini with timeout and circuit breaker."""
    global _CONSECUTIVE_FAILURES
    if _CONSECUTIVE_FAILURES >= _CFG.api_max_retries:
        raise RuntimeError(
            f"Circuit breaker open: {_CONSECUTIVE_FAILURES} consecutive API failures."
        )
    try:
        client = google_genai.Client(
            api_key=_CFG.gemini_api_key,
            http_options={"timeout": _CFG.api_timeout * 1000},
        )
        response = client.models.generate_content(
            model=_CFG.gemini_model, contents=prompt,
        )
        _CONSECUTIVE_FAILURES = 0
        return response.text.strip()
    except Exception as e:
        _CONSECUTIVE_FAILURES += 1
        log.error("Gemini call failed (attempt %d/%d): %s",
                  _CONSECUTIVE_FAILURES, _CFG.api_max_retries, e)
        raise


def load_log() -> list:
    if not os.path.exists(CONTENT_LOG):
        return []
    with open(CONTENT_LOG) as f:
        return json.load(f)


def is_winner(entry: dict) -> bool:
    platform = entry.get("platform", "web")

    # Social content: check social_metrics directly
    if platform in ("tiktok", "instagram") and entry.get("social_metrics"):
        perf = entry.get("performance_30d", {})
        return perf.get("grade") == "winner"

    # Web content: check GSC/GA4
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
    """Use Gemini to extract what made this piece win."""
    platform = entry.get("platform", "web")
    perf = entry.get("performance_30d", {})

    # Build performance section based on platform type
    if platform in ("tiktok", "instagram") and entry.get("social_metrics"):
        metrics = entry["social_metrics"]
        if platform == "tiktok":
            perf_text = f"""Performance (Social — TikTok):
- Views: {metrics.get("views", 0):,}
- Completion Rate: {(metrics.get("completion_rate", 0) * 100):.1f}%
- Engagement Rate: {(metrics.get("engagement_rate", 0) * 100):.1f}%
- Likes: {metrics.get("likes", 0):,} | Comments: {metrics.get("comments", 0):,}
- Shares: {metrics.get("shares", 0):,} | Saves: {metrics.get("saves", 0):,}
- Avg Watch Time: {metrics.get("avg_watch_time", 0):.1f}s"""
        else:
            perf_text = f"""Performance (Social — Instagram):
- Reach: {metrics.get("reach", 0):,}
- Impressions: {metrics.get("impressions", 0):,}
- Engagement Rate: {(metrics.get("engagement_rate", 0) * 100):.1f}%
- Likes: {metrics.get("likes", 0):,} | Comments: {metrics.get("comments", 0):,}
- Shares: {metrics.get("shares", 0):,} | Saves: {metrics.get("saves", 0):,}
- Profile Visits: {metrics.get("profile_visits", 0):,} | Follows: {metrics.get("follows", 0):,}"""
    else:
        gsc = perf.get("gsc", {})
        ga4 = perf.get("ga4", {})
        perf_text = f"""Performance (30-day):
- GSC Position: {gsc.get("position", "N/A")}
- CTR: {(gsc.get("ctr", 0) * 100):.1f}%
- Impressions: {gsc.get("impressions", 0):,}
- Sessions: {ga4.get("sessions", 0):,}
- Avg Duration: {ga4.get("avg_session_duration", 0):.0f}s"""

    prompt = f"""A piece of content performed well. Analyze what made it win.

Content Details:
- Platform: {platform}
- Title/Angle: {entry.get("title") or entry.get("keyword") or entry.get("description", "")[:100]}
- Description: {entry.get("description", "")[:200]}
- Target Keyword: {entry.get("keyword")}
- Site: {entry.get("site")}
- Format: {entry.get("format")}
- Persona: {entry.get("persona", "unknown")}
- Angle Used: {entry.get("angle", "unknown")}
- Four U's Score: {entry.get("four_us_score", "unknown")}/16

{perf_text}

Write a concise 3-5 sentence analysis of what likely made this content win.
Focus on: hook type effectiveness, specificity of angle, persona match, format choice.
{"For TikTok/Instagram: also consider hook timing, visual style, trending sounds/hashtags." if platform in ("tiktok", "instagram") else ""}
Be concrete — what specifically worked and why? What can be replicated?
Output ONLY the analysis text, no headers or JSON."""

    return _gemini(prompt)


def append_to_what_works(entry: dict, analysis: str):
    os.makedirs(KNOWLEDGE_BASE, exist_ok=True)

    platform = entry.get("platform", "web")
    perf = entry.get("performance_30d", {})
    date = entry.get("published_at", "")[:10]
    checked = perf.get("checked_at", "")[:10]

    title = entry.get("title") or entry.get("keyword") or entry.get("description", "")[:80]

    # Build results section based on platform
    if platform in ("tiktok", "instagram") and entry.get("social_metrics"):
        metrics = entry["social_metrics"]
        if platform == "tiktok":
            results = (
                f"- Views: {metrics.get('views', 0):,} | "
                f"Completion: {(metrics.get('completion_rate', 0) * 100):.1f}% | "
                f"Engagement: {(metrics.get('engagement_rate', 0) * 100):.1f}%\n"
                f"- Likes: {metrics.get('likes', 0):,} | "
                f"Shares: {metrics.get('shares', 0):,} | "
                f"Saves: {metrics.get('saves', 0):,}"
            )
        else:
            results = (
                f"- Reach: {metrics.get('reach', 0):,} | "
                f"Impressions: {metrics.get('impressions', 0):,} | "
                f"Engagement: {(metrics.get('engagement_rate', 0) * 100):.1f}%\n"
                f"- Likes: {metrics.get('likes', 0):,} | "
                f"Saves: {metrics.get('saves', 0):,} | "
                f"Follows: {metrics.get('follows', 0):,}"
            )
    else:
        gsc = perf.get("gsc", {})
        ga4 = perf.get("ga4", {})
        results = (
            f"- Position: #{gsc.get('position', 'N/A')} | "
            f"CTR: {(gsc.get('ctr', 0) * 100):.1f}% | "
            f"Sessions: {ga4.get('sessions', 0):,}\n"
            f"- Avg Duration: {ga4.get('avg_session_duration', 0):.0f}s"
        )

    block = f"""
## {title} — {entry.get("site")} — {date}
**Platform:** {platform} | **URL:** {entry.get("url") or entry.get("post_id", "N/A")}
**Keyword:** {entry.get("keyword")}
**Format:** {entry.get("format")} | **Persona:** {entry.get("persona", "N/A")} | **Four U's:** {entry.get("four_us_score", "N/A")}/16
**Angle:** {entry.get("angle", "N/A")}

**Results (checked {checked}):**
{results}

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
        platform = w.get("platform", "web")
        perf = w.get("performance_30d", {})

        if platform in ("tiktok", "instagram") and w.get("social_metrics"):
            metrics = w["social_metrics"]
            if platform == "tiktok":
                perf_str = (
                    f"Views: {metrics.get('views', 0):,} | "
                    f"Completion: {(metrics.get('completion_rate', 0)*100):.1f}% | "
                    f"Engagement: {(metrics.get('engagement_rate', 0)*100):.1f}%"
                )
            else:
                perf_str = (
                    f"Reach: {metrics.get('reach', 0):,} | "
                    f"Engagement: {(metrics.get('engagement_rate', 0)*100):.1f}% | "
                    f"Saves: {metrics.get('saves', 0):,}"
                )
        else:
            gsc = perf.get("gsc", {})
            ga4 = perf.get("ga4", {})
            perf_str = (
                f"Position: {gsc.get('position', 'N/A')} | "
                f"CTR: {(gsc.get('ctr', 0)*100):.1f}% | "
                f"Duration: {ga4.get('avg_session_duration', 0):.0f}s"
            )

        summary_lines.append(
            f"- [{platform}] [{w.get('site')}] [{w.get('format')}] [{w.get('persona', 'N/A')}] "
            f"Keyword: {w.get('keyword')} | {perf_str} | "
            f"Four U's: {w.get('four_us_score', 'N/A')}"
        )

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

    patterns_text = _gemini(prompt)

    # Save patterns
    patterns_file = f"{KNOWLEDGE_BASE}/weekly-patterns.md"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(patterns_file, "a") as f:
        scope = site if site != "all" else "all sites"
        f.write(f"\n\n## Pattern Report — {date_str} ({scope})\n\n{patterns_text}\n")

    return patterns_text


def correlate_rules_with_performance(site: str = "all") -> dict:
    """Correlate quality rule scores with winner/loser classification.

    Returns dict of rule_id → {winner_avg, loser_avg, delta_pct, n_winners, n_losers}
    for rules where delta >= 15% and n >= 5.
    """
    log = load_log()
    if site != "all":
        log = [e for e in log if e.get("site") == site]

    # Split into winners and losers that have quality_retro data
    winners = [e for e in log if is_winner(e) and e.get("quality_retro", {}).get("rule_scores")]
    losers = [
        e for e in log
        if not is_winner(e)
        and e.get("performance_30d")  # has been checked
        and e.get("quality_retro", {}).get("rule_scores")
    ]

    if len(winners) < 3 or len(losers) < 3:
        return {"insufficient_data": True, "n_winners": len(winners), "n_losers": len(losers)}

    # Collect per-rule scores for winners vs losers
    winner_rules: dict[str, list[float]] = defaultdict(list)
    loser_rules: dict[str, list[float]] = defaultdict(list)

    for entry in winners:
        for rule_id, data in entry["quality_retro"]["rule_scores"].items():
            winner_rules[rule_id].append(data["score"])

    for entry in losers:
        for rule_id, data in entry["quality_retro"]["rule_scores"].items():
            loser_rules[rule_id].append(data["score"])

    # Find rules with significant delta
    correlations = {}
    for rule_id in set(winner_rules) & set(loser_rules):
        w_scores = winner_rules[rule_id]
        l_scores = loser_rules[rule_id]
        if len(w_scores) < 3 or len(l_scores) < 3:
            continue

        w_avg = sum(w_scores) / len(w_scores)
        l_avg = sum(l_scores) / len(l_scores)
        if l_avg > 0:
            delta = (w_avg - l_avg) / l_avg
        else:
            delta = 1.0 if w_avg > 0 else 0.0

        if abs(delta) >= 0.15:  # 15% threshold
            correlations[rule_id] = {
                "winner_avg": round(w_avg, 3),
                "loser_avg": round(l_avg, 3),
                "delta_pct": round(delta * 100, 1),
                "n_winners": len(w_scores),
                "n_losers": len(l_scores),
            }

    return correlations


def post_weekly_summary():
    """Weekly Discord summary: avg quality score trend."""
    entries = load_log()
    scored = [e for e in entries if e.get("quality_retro")]
    if not scored:
        print("No quality-scored entries yet.")
        return

    scores = [e["quality_retro"]["overall_score"] for e in scored]
    avg = sum(scores) / len(scores)

    # Compare to last week's scores (entries scored >7 days ago)
    now = datetime.now(timezone.utc)
    old = []
    for e in scored:
        scored_at = e["quality_retro"].get("scored_at", "")
        if scored_at:
            dt = datetime.fromisoformat(scored_at)
            if (now - dt).days > 7:
                old.append(e["quality_retro"]["overall_score"])

    msg_lines = [
        "**📊 Weekly Quality Report**",
        f"Avg score: {avg:.0f}/100 across {len(scored)} pieces",
    ]
    if old:
        old_avg = sum(old) / len(old)
        delta = avg - old_avg
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        msg_lines.append(f"Trend: {old_avg:.0f} → {avg:.0f} ({arrow}{abs(delta):.0f} pts)")

    # Add top correlations
    correlations = correlate_rules_with_performance()
    if not correlations.get("insufficient_data") and correlations:
        msg_lines.append("\n**Rules that correlate with winners:**")
        sorted_rules = sorted(correlations.items(), key=lambda x: x[1]["delta_pct"], reverse=True)
        for rule_id, data in sorted_rules[:5]:
            msg_lines.append(
                f"  {rule_id}: winners avg {data['winner_avg']:.2f} vs losers {data['loser_avg']:.2f} "
                f"(+{data['delta_pct']:.0f}%, n={data['n_winners']}+{data['n_losers']})"
            )

    msg = "\n".join(msg_lines)
    channel = _CFG.discord.get("meetkai")
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--channel", "discord",
             "--target", channel, "--message", msg],
            check=True, timeout=30,
        )
    except FileNotFoundError:
        log.warning("openclaw CLI not found — skipping Discord post")
    except subprocess.TimeoutExpired:
        log.warning("openclaw message send timed out after 30s")
    print(msg)


def main():
    parser = argparse.ArgumentParser(description="Pattern Extractor")
    parser.add_argument("--url", help="Extract patterns for a specific URL")
    parser.add_argument("--weekly", action="store_true", help="Run weekly aggregation")
    parser.add_argument("--correlate", action="store_true", help="Correlate quality rules with performance")
    parser.add_argument("--weekly-summary", action="store_true", help="Post weekly quality summary to Discord")
    parser.add_argument("--site", default="all", help="Site filter for weekly run")
    args = parser.parse_args()

    if args.correlate:
        print(f"Correlating quality rules with performance (site={args.site})...")
        correlations = correlate_rules_with_performance(args.site)
        if correlations.get("insufficient_data"):
            print(f"Insufficient data: {correlations['n_winners']} winners, {correlations['n_losers']} losers (need 3+ each)")
        else:
            print(f"\nRules correlated with winners ({len(correlations)} rules with delta >= 15%):")
            for rule_id, data in sorted(correlations.items(), key=lambda x: x[1]["delta_pct"], reverse=True):
                print(f"  {rule_id}: winners={data['winner_avg']:.3f} losers={data['loser_avg']:.3f} "
                      f"delta=+{data['delta_pct']:.1f}% (n={data['n_winners']}w/{data['n_losers']}l)")
        return

    if args.weekly_summary:
        post_weekly_summary()
        return

    if args.url:
        entries = load_log()
        entry = next((e for e in entries if e["url"] == args.url), None)
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
    entries = load_log()
    processed = 0
    for entry in entries:
        if is_winner(entry) and not entry.get("patterns_extracted"):
            print(f"Processing winner: {entry['url']}")
            analysis = analyze_winner(entry)
            append_to_what_works(entry, analysis)
            entry["patterns_extracted"] = True
            processed += 1

    if processed:
        # Save updated log
        with open(CONTENT_LOG, "w") as f:
            json.dump(entries, f, indent=2)
        print(f"\n{processed} winner(s) processed.")
    else:
        print("No unprocessed winners found.")


if __name__ == "__main__":
    main()

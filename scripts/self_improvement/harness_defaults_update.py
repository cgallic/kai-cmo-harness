#!/usr/bin/env python3
"""
Harness Defaults Auto-Updater — Kai Harness Self-Improvement

When patterns reach statistical significance (n≥5 with consistent delta),
updates MARKETING.md with new defaults and posts a digest to Discord.

Tracks:
  - Best performing persona per site
  - Best hook type per platform
  - Best word count range per format
  - Best publish day/time per platform

Usage:
  python3 harness_defaults_update.py             # check and update if thresholds met
  python3 harness_defaults_update.py --dry-run   # print proposed updates without writing
  python3 harness_defaults_update.py --force     # update regardless of n threshold
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Use centralized config
from scripts.harness_config import get_config

_CFG = get_config()

CONTENT_LOG = str(_CFG.content_log)
MARKETING_MD = str(_CFG.marketing_md)
DEFAULTS_FILE = str(_CFG.defaults_file)
POLICY_DIR = str(_CFG.policy_dir)

MIN_N = _CFG.thresholds.min_n
MIN_DELTA = _CFG.thresholds.min_delta

log = logging.getLogger("harness-defaults")
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def load_log() -> list:
    if not os.path.exists(CONTENT_LOG):
        return []
    with open(CONTENT_LOG) as f:
        return json.load(f)


def load_current_defaults() -> dict:
    if os.path.exists(DEFAULTS_FILE):
        with open(DEFAULTS_FILE) as f:
            return json.load(f)
    return {}


def save_defaults(defaults: dict):
    os.makedirs(os.path.dirname(DEFAULTS_FILE), exist_ok=True)
    with open(DEFAULTS_FILE, "w") as f:
        json.dump(defaults, f, indent=2)


def get_metric(entry: dict) -> float | None:
    """Get the best available engagement metric from a log entry."""
    perf = entry.get("performance_30d")
    if not perf:
        return None
    gsc = perf.get("gsc", {})
    ga4 = perf.get("ga4", {})
    # Composite: CTR * (1 + session_duration/300) as a single signal
    ctr = gsc.get("ctr", 0)
    duration = ga4.get("avg_session_duration", 0)
    if ctr == 0 and duration == 0:
        return None
    return ctr * (1 + duration / 300)


def analyze_patterns(log: list) -> dict:
    """Extract statistical patterns from log entries with performance data."""
    measured = [e for e in log if get_metric(e) is not None]
    if len(measured) < MIN_N:
        return {"insufficient_data": True, "n": len(measured), "required": MIN_N}

    patterns = {}

    # ── Persona performance by site ──────────────────────────────────────────
    persona_by_site: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for e in measured:
        site = e.get("site")
        persona = e.get("persona")
        metric = get_metric(e)
        if site and persona and metric:
            persona_by_site[site][persona].append(metric)

    persona_winners = {}
    for site, personas in persona_by_site.items():
        qualified = {p: scores for p, scores in personas.items() if len(scores) >= 3}
        if not qualified:
            continue
        ranked = sorted(qualified.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        best, second = ranked[0], ranked[1] if len(ranked) > 1 else (None, None)
        if second:
            best_avg = sum(best[1]) / len(best[1])
            second_avg = sum(second[1]) / len(second[1])
            delta = (best_avg - second_avg) / max(second_avg, 0.0001)
            if delta >= MIN_DELTA:
                persona_winners[site] = {
                    "persona": best[0],
                    "avg_metric": round(best_avg, 4),
                    "delta_pct": round(delta * 100, 1),
                    "n": len(best[1]),
                }
    if persona_winners:
        patterns["best_persona_by_site"] = persona_winners

    # ── Word count performance ────────────────────────────────────────────────
    # Bucket by word count: short (<1000), mid (1000-1600), long (>1600)
    wc_buckets: dict[str, list[float]] = defaultdict(list)
    for e in measured:
        text_len = len((e.get("title") or "").split()) * 10  # rough proxy
        metric = get_metric(e)
        if not metric:
            continue
        bucket = "short" if text_len < 800 else "mid" if text_len <= 1600 else "long"
        wc_buckets[bucket].append(metric)

    qualified_wc = {b: scores for b, scores in wc_buckets.items() if len(scores) >= 3}
    if len(qualified_wc) >= 2:
        ranked_wc = sorted(qualified_wc.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        best_wc = ranked_wc[0]
        second_wc = ranked_wc[1]
        best_avg = sum(best_wc[1]) / len(best_wc[1])
        second_avg = sum(second_wc[1]) / len(second_wc[1])
        delta = (best_avg - second_avg) / max(second_avg, 0.0001)
        if delta >= MIN_DELTA:
            patterns["best_word_count"] = {
                "bucket": best_wc[0],
                "delta_pct": round(delta * 100, 1),
                "n": len(best_wc[1]),
            }

    # ── Publish day performance ───────────────────────────────────────────────
    day_metrics: dict[str, list[float]] = defaultdict(list)
    for e in measured:
        published = e.get("published_at")
        metric = get_metric(e)
        if not published or not metric:
            continue
        day = datetime.fromisoformat(published).strftime("%A")
        day_metrics[day].append(metric)

    qualified_days = {d: scores for d, scores in day_metrics.items() if len(scores) >= 3}
    if len(qualified_days) >= 2:
        ranked_days = sorted(qualified_days.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        best_day = ranked_days[0]
        second_day = ranked_days[1]
        best_avg = sum(best_day[1]) / len(best_day[1])
        second_avg = sum(second_day[1]) / len(second_day[1])
        delta = (best_avg - second_avg) / max(second_avg, 0.0001)
        if delta >= MIN_DELTA:
            patterns["best_publish_day"] = {
                "day": best_day[0],
                "delta_pct": round(delta * 100, 1),
                "n": len(best_day[1]),
            }

    return patterns


def update_marketing_md(patterns: dict, dry_run: bool = False) -> list[str]:
    """Append a Learned Defaults section to MARKETING.md based on patterns."""
    if not os.path.exists(MARKETING_MD):
        return []

    content = Path(MARKETING_MD).read_text()
    updates = []

    # Remove old learned defaults block if present
    content = re.sub(
        r"\n---\n## Learned Defaults.*?(?=\n---\n|\Z)",
        "",
        content,
        flags=re.DOTALL,
    ).strip()

    # Build new block
    lines = ["\n\n---\n## Learned Defaults (auto-updated by harness)\n"]
    lines.append(f"*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*\n")

    if "best_persona_by_site" in patterns:
        lines.append("\n**Best persona by site:**")
        for site, data in patterns["best_persona_by_site"].items():
            line = f"- `{site}`: `{data['persona']}` (+{data['delta_pct']}% vs next best, n={data['n']})"
            lines.append(line)
            updates.append(line)

    if "best_word_count" in patterns:
        wc = patterns["best_word_count"]
        line = f"\n**Best word count:** `{wc['bucket']}` (+{wc['delta_pct']}% vs alternatives, n={wc['n']})"
        lines.append(line)
        updates.append(line)

    if "best_publish_day" in patterns:
        day = patterns["best_publish_day"]
        line = f"\n**Best publish day:** `{day['day']}` (+{day['delta_pct']}% vs alternatives, n={day['n']})"
        lines.append(line)
        updates.append(line)

    new_content = content + "\n".join(lines)

    if not dry_run:
        # Create backup before overwriting
        backup = MARKETING_MD + ".bak"
        shutil.copy2(MARKETING_MD, backup)
        log.info("Backed up MARKETING.md to %s", backup)
        Path(MARKETING_MD).write_text(new_content)

    return updates


def update_policy_thresholds(patterns: dict, dry_run: bool = False) -> list[str]:
    """Auto-update gate policy YAML thresholds when winner patterns emerge.

    When n>=5 winners consistently score above/below a threshold with delta>=15%,
    adjust the auto_approve_above / reject_below values to match reality.
    """
    if not yaml:
        return ["Skipped policy update: PyYAML not installed"]

    updates = []
    measured = [e for e in load_log() if e.get("quality_retro") and e.get("performance_30d")]
    winners = [e for e in measured if e.get("performance_30d", {}).get("grade") == "winner"]
    losers = [e for e in measured if e.get("performance_30d", {}).get("grade") == "underperformer"]

    if len(winners) < MIN_N:
        return []

    # Calculate winner quality score distribution
    winner_scores = [e["quality_retro"]["overall_score"] for e in winners]
    loser_scores = [e["quality_retro"]["overall_score"] for e in losers] if losers else []

    if not winner_scores:
        return []

    winner_p10 = sorted(winner_scores)[max(0, len(winner_scores) // 10)]  # 10th percentile of winners
    loser_p90 = sorted(loser_scores)[min(len(loser_scores) - 1, len(loser_scores) * 9 // 10)] if loser_scores else 50

    # Update each policy file
    policy_dir = Path(POLICY_DIR)
    if not policy_dir.exists():
        return []

    for policy_file in policy_dir.glob("*.yaml"):
        try:
            content = policy_file.read_text()
            policy = yaml.safe_load(content)
            if not policy:
                continue

            old_approve = policy.get("auto_approve_above", 85)
            old_reject = policy.get("reject_below", 60)

            # New thresholds: approve above 10th percentile of winners, reject below 90th percentile of losers
            new_approve = max(int(winner_p10) - 5, 60)  # Don't go below 60
            new_reject = min(int(loser_p90) + 5, new_approve - 10)  # Keep at least 10pt gap

            if abs(new_approve - old_approve) < 5 and abs(new_reject - old_reject) < 5:
                continue  # No significant change

            policy["auto_approve_above"] = new_approve
            policy["reject_below"] = new_reject
            policy["hold_between"] = [new_reject, new_approve]

            if not dry_run:
                # Backup policy file before overwriting
                shutil.copy2(policy_file, str(policy_file) + ".bak")
                with open(policy_file, "w") as f:
                    yaml.dump(policy, f, default_flow_style=False, sort_keys=False)

            update_msg = (
                f"- `{policy_file.name}`: approve {old_approve}→{new_approve}, "
                f"reject {old_reject}→{new_reject} "
                f"(based on {len(winner_scores)} winners, {len(loser_scores)} losers)"
            )
            updates.append(update_msg)
        except Exception as e:
            updates.append(f"- `{policy_file.name}`: error — {e}")

    return updates


def post_discord(updates: list[str], patterns: dict):
    if not updates:
        return
    channel = _CFG.discord.get("meetkai")
    if not channel:
        log.info("No Discord channel configured — skipping post")
        return
    lines = ["**🧠 Harness Defaults Updated**", "Patterns reached statistical significance (n≥5, Δ≥15%):", ""]
    lines.extend(updates)
    lines.append("\nMARKETING.md updated. Next run will use these defaults.")
    msg = "\n".join(lines)
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "discord",
             "--target", channel, "--message", msg],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            log.warning("Discord post failed (exit %d): %s", result.returncode, result.stderr[:200])
    except FileNotFoundError:
        log.warning("openclaw not found — skipping Discord post")
    except subprocess.TimeoutExpired:
        log.warning("Discord post timed out")


def main():
    parser = argparse.ArgumentParser(description="Harness Defaults Auto-Updater")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Update regardless of n threshold")
    args = parser.parse_args()

    log = load_log()
    print(f"Log entries: {len(log)}")

    patterns = analyze_patterns(log)

    if patterns.get("insufficient_data") and not args.force:
        n = patterns.get("n", 0)
        required = patterns.get("required", MIN_N)
        print(f"Insufficient data: {n}/{required} measured entries. Publish more content.")
        return

    print(f"Patterns found: {list(patterns.keys())}")

    updates = update_marketing_md(patterns, dry_run=args.dry_run)

    # Also update policy YAML thresholds
    policy_updates = update_policy_thresholds(patterns, dry_run=args.dry_run)

    all_updates = updates + policy_updates

    if args.dry_run:
        print("\n[DRY RUN] Proposed updates:")
        for u in all_updates:
            print(f"  {u}")
    else:
        if all_updates:
            save_defaults(patterns)
            post_discord(all_updates, patterns)
            print(f"\n{len(updates)} MARKETING.md default(s) updated")
            if policy_updates:
                print(f"{len(policy_updates)} policy threshold(s) updated")
        else:
            print("No significant patterns found above threshold yet.")


if __name__ == "__main__":
    main()

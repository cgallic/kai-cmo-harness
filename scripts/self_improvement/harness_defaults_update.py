#!/usr/bin/env python3
"""
Harness Defaults Auto-Updater — Kai Harness Self-Improvement

When patterns reach statistical significance (Welch's t-test, p < threshold),
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
from scripts.self_improvement.stats_utils import (
    is_seasonal,
    welch_ttest,
)

_CFG = get_config()

CONTENT_LOG = str(_CFG.content_log)
MARKETING_MD = str(_CFG.marketing_md)
DEFAULTS_FILE = str(_CFG.defaults_file)
POLICY_DIR = str(_CFG.policy_dir)
BASELINE_FILE = str(_CFG.data_dir / "baseline_thresholds.json")

MIN_N = _CFG.thresholds.min_n
MIN_DELTA = _CFG.thresholds.min_delta
P_VALUE_THRESHOLD = _CFG.thresholds.p_value_threshold
DRIFT_MAX_PCT = _CFG.thresholds.drift_max_pct

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


def analyze_patterns(log_entries: list) -> dict:
    """Extract statistical patterns from log entries with performance data.

    Uses Welch's t-test for significance testing. Patterns must pass both
    statistical significance (p < threshold) AND practical significance
    (delta >= MIN_DELTA) to be accepted.
    """
    measured = [e for e in log_entries if get_metric(e) is not None]
    if len(measured) < MIN_N:
        return {"insufficient_data": True, "n": len(measured), "required": MIN_N}

    patterns = {}

    # ── Persona performance by site ──────────────────────────────────────────
    persona_by_site: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    persona_entries: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for e in measured:
        site = e.get("site")
        persona = e.get("persona")
        metric = get_metric(e)
        if site and persona and metric:
            persona_by_site[site][persona].append(metric)
            persona_entries[site][persona].append(e)

    persona_winners = {}
    for site, personas in persona_by_site.items():
        qualified = {p: scores for p, scores in personas.items() if len(scores) >= 3}
        if not qualified:
            continue
        ranked = sorted(qualified.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        if len(ranked) < 2:
            continue
        best = ranked[0]
        second = ranked[1]
        if best and second:
            best_avg = sum(best[1]) / len(best[1])
            second_avg = sum(second[1]) / len(second[1])
            delta = (best_avg - second_avg) / max(second_avg, 0.0001)

            # Require both practical AND statistical significance
            if delta < MIN_DELTA:
                continue

            stat = welch_ttest(best[1], second[1])
            if stat["significant"] and stat["p_value"] < P_VALUE_THRESHOLD:
                seasonal_flag = is_seasonal(persona_entries[site][best[0]])
                persona_winners[site] = {
                    "persona": best[0],
                    "avg_metric": round(best_avg, 4),
                    "delta_pct": round(delta * 100, 1),
                    "n": len(best[1]),
                    "p_value": stat["p_value"],
                    "ci_low": stat["ci_low"],
                    "ci_high": stat["ci_high"],
                    "seasonal_flag": seasonal_flag,
                }
    if persona_winners:
        patterns["best_persona_by_site"] = persona_winners

    # ── Word count performance ────────────────────────────────────────────────
    # Bucket by word count: short (<1000), mid (1000-1600), long (>1600)
    wc_buckets: dict[str, list[float]] = defaultdict(list)
    wc_entries: dict[str, list[dict]] = defaultdict(list)
    for e in measured:
        text_len = len((e.get("title") or "").split()) * 10  # rough proxy
        metric = get_metric(e)
        if not metric:
            continue
        bucket = "short" if text_len < 800 else "mid" if text_len <= 1600 else "long"
        wc_buckets[bucket].append(metric)
        wc_entries[bucket].append(e)

    qualified_wc = {b: scores for b, scores in wc_buckets.items() if len(scores) >= 3}
    if len(qualified_wc) >= 2:
        ranked_wc = sorted(qualified_wc.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        best_wc = ranked_wc[0]
        second_wc = ranked_wc[1]
        best_avg = sum(best_wc[1]) / len(best_wc[1])
        second_avg = sum(second_wc[1]) / len(second_wc[1])
        delta = (best_avg - second_avg) / max(second_avg, 0.0001)

        if delta >= MIN_DELTA:
            stat = welch_ttest(best_wc[1], second_wc[1])
            if stat["significant"] and stat["p_value"] < P_VALUE_THRESHOLD:
                seasonal_flag = is_seasonal(wc_entries[best_wc[0]])
                patterns["best_word_count"] = {
                    "bucket": best_wc[0],
                    "delta_pct": round(delta * 100, 1),
                    "n": len(best_wc[1]),
                    "p_value": stat["p_value"],
                    "ci_low": stat["ci_low"],
                    "ci_high": stat["ci_high"],
                    "seasonal_flag": seasonal_flag,
                }

    # ── Publish day performance ───────────────────────────────────────────────
    day_metrics: dict[str, list[float]] = defaultdict(list)
    day_entries: dict[str, list[dict]] = defaultdict(list)
    for e in measured:
        published = e.get("published_at")
        metric = get_metric(e)
        if not published or not metric:
            continue
        day = datetime.fromisoformat(published).strftime("%A")
        day_metrics[day].append(metric)
        day_entries[day].append(e)

    qualified_days = {d: scores for d, scores in day_metrics.items() if len(scores) >= 3}
    if len(qualified_days) >= 2:
        ranked_days = sorted(qualified_days.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
        best_day = ranked_days[0]
        second_day = ranked_days[1]
        best_avg = sum(best_day[1]) / len(best_day[1])
        second_avg = sum(second_day[1]) / len(second_day[1])
        delta = (best_avg - second_avg) / max(second_avg, 0.0001)

        if delta >= MIN_DELTA:
            stat = welch_ttest(best_day[1], second_day[1])
            if stat["significant"] and stat["p_value"] < P_VALUE_THRESHOLD:
                seasonal_flag = is_seasonal(day_entries[best_day[0]])
                patterns["best_publish_day"] = {
                    "day": best_day[0],
                    "delta_pct": round(delta * 100, 1),
                    "n": len(best_day[1]),
                    "p_value": stat["p_value"],
                    "ci_low": stat["ci_low"],
                    "ci_high": stat["ci_high"],
                    "seasonal_flag": seasonal_flag,
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
            seasonal = " [SEASONAL?]" if data.get("seasonal_flag") else ""
            line = (
                f"- `{site}`: `{data['persona']}` "
                f"(+{data['delta_pct']}% "
                f"[CI: {data.get('ci_low', 0):.0f}%-{data.get('ci_high', 0):.0f}%, "
                f"p={data.get('p_value', 'N/A')}, n={data['n']}]){seasonal}"
            )
            lines.append(line)
            updates.append(line)

    if "best_word_count" in patterns:
        wc = patterns["best_word_count"]
        seasonal = " [SEASONAL?]" if wc.get("seasonal_flag") else ""
        line = (
            f"\n**Best word count:** `{wc['bucket']}` "
            f"(+{wc['delta_pct']}% "
            f"[CI: {wc.get('ci_low', 0):.0f}%-{wc.get('ci_high', 0):.0f}%, "
            f"p={wc.get('p_value', 'N/A')}, n={wc['n']}]){seasonal}"
        )
        lines.append(line)
        updates.append(line)

    if "best_publish_day" in patterns:
        day = patterns["best_publish_day"]
        seasonal = " [SEASONAL?]" if day.get("seasonal_flag") else ""
        line = (
            f"\n**Best publish day:** `{day['day']}` "
            f"(+{day['delta_pct']}% "
            f"[CI: {day.get('ci_low', 0):.0f}%-{day.get('ci_high', 0):.0f}%, "
            f"p={day.get('p_value', 'N/A')}, n={day['n']}]){seasonal}"
        )
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


# ── Baseline storage + drift detection ───────────────────────────────────────


def load_baseline_thresholds() -> dict:
    """Load or create baseline threshold snapshot for drift detection.

    On first run, captures current policy YAML values as the baseline.
    Returns dict of {policy_filename: {auto_approve_above, reject_below}}.
    """
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE) as f:
            return json.load(f)

    # First run: capture current policy values as baseline
    baseline = {"created_at": datetime.now(timezone.utc).isoformat()}
    policy_dir = Path(POLICY_DIR)
    if policy_dir.exists() and yaml:
        for policy_file in policy_dir.glob("*.yaml"):
            try:
                policy = yaml.safe_load(policy_file.read_text())
                if policy:
                    baseline[policy_file.name] = {
                        "auto_approve_above": policy.get("auto_approve_above", 85),
                        "reject_below": policy.get("reject_below", 60),
                    }
            except Exception:
                continue

    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)
    log.info("Created baseline thresholds at %s", BASELINE_FILE)

    return baseline


def check_drift(proposed_thresholds: dict) -> list[str]:
    """Compare proposed thresholds against baseline. Flag shifts > DRIFT_MAX_PCT.

    Args:
        proposed_thresholds: dict of {policy_filename: {auto_approve_above, reject_below}}

    Returns:
        List of drift alert strings. Empty list if no drift detected.
    """
    baseline = load_baseline_thresholds()
    alerts = []

    for policy_name, proposed in proposed_thresholds.items():
        if policy_name not in baseline or policy_name == "created_at":
            continue
        base = baseline[policy_name]

        for field in ("auto_approve_above", "reject_below"):
            old_val = base.get(field)
            new_val = proposed.get(field)
            if old_val is None or new_val is None or old_val == 0:
                continue

            shift = abs(new_val - old_val) / old_val
            if shift > DRIFT_MAX_PCT:
                alerts.append(
                    f"DRIFT: `{policy_name}` {field}: {old_val}→{new_val} "
                    f"({shift:.0%} shift, max allowed {DRIFT_MAX_PCT:.0%})"
                )

    return alerts


def update_policy_thresholds(patterns: dict, dry_run: bool = False) -> dict:
    """Auto-update gate policy YAML thresholds when winner patterns emerge.

    Returns dict with keys:
      - "updates": list of update message strings
      - "drift_alerts": list of drift alert strings (empty if no drift)
    """
    result = {"updates": [], "drift_alerts": []}

    if not yaml:
        result["updates"] = ["Skipped policy update: PyYAML not installed"]
        return result

    updates = []
    measured = [e for e in load_log() if e.get("quality_retro") and e.get("performance_30d")]
    winners = [e for e in measured if e.get("performance_30d", {}).get("grade") == "winner"]
    losers = [e for e in measured if e.get("performance_30d", {}).get("grade") == "underperformer"]

    if len(winners) < MIN_N:
        return result

    # Calculate winner quality score distribution
    winner_scores = [e["quality_retro"]["overall_score"] for e in winners]
    loser_scores = [e["quality_retro"]["overall_score"] for e in losers] if losers else []

    if not winner_scores:
        return result

    winner_p10 = sorted(winner_scores)[max(0, len(winner_scores) // 10)]
    loser_p90 = sorted(loser_scores)[min(len(loser_scores) - 1, len(loser_scores) * 9 // 10)] if loser_scores else 50

    # Update each policy file
    policy_dir = Path(POLICY_DIR)
    if not policy_dir.exists():
        return result

    # Collect all proposed changes first for drift detection
    proposed = {}
    policy_changes = []

    for policy_file in policy_dir.glob("*.yaml"):
        try:
            content = policy_file.read_text()
            policy = yaml.safe_load(content)
            if not policy:
                continue

            old_approve = policy.get("auto_approve_above", 85)
            old_reject = policy.get("reject_below", 60)

            new_approve = max(int(winner_p10) - 5, 60)
            new_reject = min(int(loser_p90) + 5, new_approve - 10)

            if abs(new_approve - old_approve) < 5 and abs(new_reject - old_reject) < 5:
                continue

            proposed[policy_file.name] = {
                "auto_approve_above": new_approve,
                "reject_below": new_reject,
            }
            policy_changes.append((policy_file, policy, old_approve, old_reject, new_approve, new_reject))
        except Exception as e:
            updates.append(f"- `{policy_file.name}`: error — {e}")

    # Check drift before writing any files
    if proposed:
        drift_alerts = check_drift(proposed)
        if drift_alerts:
            result["drift_alerts"] = drift_alerts
            result["updates"] = updates
            log.warning("Drift detected — halting policy threshold updates")
            return result

    # No drift — proceed with writes
    for policy_file, policy, old_approve, old_reject, new_approve, new_reject in policy_changes:
        policy["auto_approve_above"] = new_approve
        policy["reject_below"] = new_reject
        policy["hold_between"] = [new_reject, new_approve]

        if not dry_run:
            shutil.copy2(policy_file, str(policy_file) + ".bak")
            with open(policy_file, "w") as f:
                yaml.dump(policy, f, default_flow_style=False, sort_keys=False)

        update_msg = (
            f"- `{policy_file.name}`: approve {old_approve}→{new_approve}, "
            f"reject {old_reject}→{new_reject} "
            f"(based on {len(winner_scores)} winners, {len(loser_scores)} losers)"
        )
        updates.append(update_msg)

    result["updates"] = updates
    return result


def post_discord(updates: list[str], patterns: dict):
    """Post update digest to Discord."""
    if not updates:
        return
    channel = _CFG.discord.get("meetkai")
    if not channel:
        log.info("No Discord channel configured — skipping post")
        return

    lines = [
        "**\U0001f9e0 Harness Defaults Updated**",
        f"Patterns reached statistical significance (n\u2265{MIN_N}, p<{P_VALUE_THRESHOLD}):",
        "",
    ]
    lines.extend(updates)

    # Add seasonal warnings if any pattern flagged
    seasonal_warnings = []
    for key in ("best_persona_by_site", "best_word_count", "best_publish_day"):
        data = patterns.get(key)
        if not data:
            continue
        if isinstance(data, dict) and not any(k in data for k in ("persona", "bucket", "day")):
            # It's a nested dict (persona by site)
            for site, site_data in data.items():
                if site_data.get("seasonal_flag"):
                    seasonal_warnings.append(f"  - {key}/{site}: data clustered in narrow window")
        elif isinstance(data, dict) and data.get("seasonal_flag"):
            seasonal_warnings.append(f"  - {key}: data clustered in narrow window")

    if seasonal_warnings:
        lines.append("\n\u26a0\ufe0f **Seasonal warnings** (pattern may not be durable):")
        lines.extend(seasonal_warnings)

    lines.append("\nMARKETING.md updated. Next run will use these defaults.")
    msg = "\n".join(lines)
    _send_discord(channel, msg)


def post_drift_alert(drift_alerts: list[str]):
    """Post a dedicated drift alert to Discord."""
    channel = _CFG.discord.get("meetkai")
    if not channel:
        log.info("No Discord channel configured — skipping drift alert")
        return

    lines = [
        "**\U0001f6a8 DRIFT ALERT — Policy Updates Halted**",
        f"Proposed threshold changes exceed {DRIFT_MAX_PCT:.0%} drift limit:",
        "",
    ]
    lines.extend(drift_alerts)
    lines.append("\nPolicy files were NOT updated. Review and adjust baseline if intentional.")
    msg = "\n".join(lines)
    _send_discord(channel, msg)


def _send_discord(channel: str, msg: str):
    """Send a message to Discord via openclaw CLI."""
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

    content_log = load_log()
    print(f"Log entries: {len(content_log)}")

    patterns = analyze_patterns(content_log)

    if patterns.get("insufficient_data") and not args.force:
        n = patterns.get("n", 0)
        required = patterns.get("required", MIN_N)
        print(f"Insufficient data: {n}/{required} measured entries. Publish more content.")
        return

    print(f"Patterns found: {list(patterns.keys())}")

    updates = update_marketing_md(patterns, dry_run=args.dry_run)

    # Also update policy YAML thresholds (with drift detection)
    policy_result = update_policy_thresholds(patterns, dry_run=args.dry_run)
    policy_updates = policy_result["updates"]
    drift_alerts = policy_result["drift_alerts"]

    all_updates = updates + policy_updates

    if args.dry_run:
        print("\n[DRY RUN] Proposed updates:")
        for u in all_updates:
            print(f"  {u}")
        if drift_alerts:
            print("\n[DRY RUN] Drift alerts (would halt policy updates):")
            for a in drift_alerts:
                print(f"  {a}")
    else:
        if drift_alerts:
            print("\n\u26a0 DRIFT DETECTED — policy updates halted:")
            for a in drift_alerts:
                print(f"  {a}")
            post_drift_alert(drift_alerts)

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

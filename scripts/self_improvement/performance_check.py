#!/usr/bin/env python3
"""
30-Day Performance Checker — Kai Harness

Pulls GA4 + GSC data for tracked URLs, evaluates against thresholds,
extracts patterns from winners, and posts digest to Discord.

Usage:
  python3 performance_check.py --days 30
  python3 performance_check.py --url "https://kaicalls.com/blog/..."
  python3 performance_check.py --all         # Check all pending
  python3 performance_check.py --dry-run     # Print without posting
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Use centralized config
from scripts.harness_config import get_config

_CFG = get_config()

CONTENT_LOG = str(_CFG.content_log)
PENDING_CHECKS_DIR = str(_CFG.pending_checks_dir)

# Win thresholds from config
WIN_POSITION = _CFG.thresholds.win_position
WIN_CTR = _CFG.thresholds.win_ctr
WIN_TIME_ON_PAGE = _CFG.thresholds.win_time_on_page

SITE_URLS = _CFG.sites.gsc_urls
GA4_PROPERTY_IDS = _CFG.sites.ga4_properties
DISCORD_CHANNEL_IDS = _CFG.discord.channels

log = logging.getLogger("perf-check")
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


def save_log(entries: list):
    with open(CONTENT_LOG, "w") as f:
        json.dump(entries, f, indent=2)


def get_pending_checks() -> list:
    if not os.path.exists(PENDING_CHECKS_DIR):
        return []
    checks = []
    now = datetime.now(timezone.utc)
    for f in Path(PENDING_CHECKS_DIR).glob("*.json"):
        with open(f) as fh:
            check = json.load(fh)
        due = datetime.fromisoformat(check["check_due"])
        if check["status"] == "pending" and due <= now:
            checks.append((f, check))
    return checks


def pull_gsc_data(url: str, keyword: str, site: str) -> dict:
    """Pull GSC performance for a specific URL + keyword."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
        if not creds_path or not os.path.exists(creds_path):
            return {"error": "No GSC credentials"}

        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        service = build("searchconsole", "v1", credentials=creds)
        site_url = SITE_URLS.get(site)
        if not site_url:
            return {"error": f"Unknown site: {site}"}

        response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": "2024-01-01",
                "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "dimensions": ["query", "page"],
                "dimensionFilterGroups": [
                    {
                        "filters": [
                            {"dimension": "page", "operator": "contains", "expression": url},
                            {"dimension": "query", "operator": "contains", "expression": keyword},
                        ]
                    }
                ],
                "rowLimit": 10,
            },
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            return {"impressions": 0, "clicks": 0, "ctr": 0.0, "position": None}

        # Aggregate across all matching rows
        total_impressions = sum(r.get("impressions", 0) for r in rows)
        total_clicks = sum(r.get("clicks", 0) for r in rows)
        # Weighted average position (weighted by impressions)
        weighted_pos = sum(
            r.get("position", 0) * r.get("impressions", 0) for r in rows
        )
        avg_position = weighted_pos / max(total_impressions, 1)
        overall_ctr = total_clicks / max(total_impressions, 1)

        return {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "ctr": round(overall_ctr, 4),
            "position": round(avg_position, 1),
            "rows_aggregated": len(rows),
        }
    except Exception as e:
        return {"error": str(e)}


def pull_ga4_data(url: str, site: str) -> dict:
    """Pull GA4 sessions + engagement for a specific page URL."""
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            DimensionFilter,
            FilterExpression,
            Metric,
            RunReportRequest,
            StringFilter,
        )

        property_id = GA4_PROPERTY_IDS.get(site)
        if not property_id:
            return {"error": f"No GA4 property ID for site: {site}"}

        creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
        client = BetaAnalyticsDataClient()

        # Extract path from URL
        from urllib.parse import urlparse
        path = urlparse(url).path

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            dimension_filter=FilterExpression(
                filter=DimensionFilter(
                    field_name="pagePath",
                    string_filter=StringFilter(
                        match_type="CONTAINS",
                        value=path,
                    ),
                )
            ),
        )

        response = client.run_report(request)
        if not response.rows:
            return {"sessions": 0, "bounce_rate": 0.0, "avg_session_duration": 0}

        row = response.rows[0]
        return {
            "sessions": int(row.metric_values[0].value),
            "bounce_rate": round(float(row.metric_values[1].value), 4),
            "avg_session_duration": round(float(row.metric_values[2].value), 1),
        }
    except Exception as e:
        return {"error": str(e)}


def evaluate_performance(entry: dict, gsc: dict, ga4: dict) -> dict:
    """Determine if content is a winner, average, or underperformer."""
    position = gsc.get("position")
    ctr = gsc.get("ctr", 0)
    avg_duration = ga4.get("avg_session_duration", 0)

    is_winner = (
        position is not None
        and position <= WIN_POSITION
        and ctr >= WIN_CTR
        and avg_duration >= WIN_TIME_ON_PAGE
    )

    is_underperformer = (
        position is None
        or position > 20
        or (ctr < 0.01 and gsc.get("impressions", 0) > 100)
    )

    return {
        "is_winner": is_winner,
        "is_underperformer": is_underperformer,
        "grade": "winner" if is_winner else ("underperformer" if is_underperformer else "average"),
    }


def retro_score_content(url: str, site: str) -> dict | None:
    """Run quality scorer on published content retroactively by fetching URL."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "KaiHarness/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract article body text (strip HTML tags)
        import re
        # Remove script/style tags
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 200:
            return None

        # Run through quality scorer
        from scripts.quality.engine import QualityEngine
        engine = QualityEngine(use_llm=False)  # No LLM for batch scoring
        report = asyncio.run(engine.score_content(text, file_path=url))

        # Extract per-rule scores
        rule_scores = {}
        for cat in report.categories:
            for rule in cat.rules:
                rule_scores[rule.rule_id] = {
                    "score": round(rule.score, 3),
                    "passed": rule.passed,
                    "violations": len(rule.violations),
                }

        return {
            "overall_score": round(report.overall_score, 1),
            "grade": report.overall_grade,
            "rule_scores": rule_scores,
            "scored_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"  Retro-score failed for {url}: {e}")
        return None


def format_discord_message(entry: dict, gsc: dict, ga4: dict, evaluation: dict) -> str:
    grade_emoji = {"winner": "🏆", "average": "📊", "underperformer": "⚠️"}
    emoji = grade_emoji.get(evaluation["grade"], "📊")

    lines = [
        f"{emoji} **30-Day Check: {entry.get('title') or entry['keyword']}**",
        f"URL: {entry['url']}",
        "",
        f"**GSC (Search):**",
        f"  Position: {gsc.get('position', 'N/A')} | CTR: {(gsc.get('ctr', 0) * 100):.1f}% | "
        f"Impressions: {gsc.get('impressions', 0):,} | Clicks: {gsc.get('clicks', 0):,}",
        "",
        f"**GA4 (Traffic):**",
        f"  Sessions: {ga4.get('sessions', 0):,} | "
        f"Avg duration: {ga4.get('avg_session_duration', 0):.0f}s | "
        f"Bounce: {(ga4.get('bounce_rate', 0) * 100):.0f}%",
        "",
        f"**Grade: {evaluation['grade'].upper()}**",
    ]

    # Include quality score if available
    entry_quality = entry.get("quality_retro")
    if entry_quality:
        lines.append("")
        lines.append(f"**Quality Score:** {entry_quality.get('overall_score', 'N/A')}/100 "
                     f"(grade {entry_quality.get('grade', '?')})")

    if evaluation["is_winner"]:
        lines.append("→ Pattern extracted to knowledge base.")
    elif evaluation["is_underperformer"]:
        lines.append("→ Consider: update angle, add more specifics, or target a less competitive keyword.")

    return "\n".join(lines)


def post_to_discord(message: str, site: str):
    channel_id = DISCORD_CHANNEL_IDS.get(site, _CFG.discord.fallback_channel)
    if not channel_id:
        log.info("No Discord channel for site %s — skipping post", site)
        return
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "discord",
             "--target", channel_id, "--message", message],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            log.warning("Discord post failed (exit %d): %s", result.returncode, result.stderr[:200])
    except FileNotFoundError:
        log.warning("openclaw not found — skipping Discord post")
    except subprocess.TimeoutExpired:
        log.warning("Discord post timed out")


def run_check(check_file: Path, check: dict, dry_run: bool = False) -> dict:
    entry_id = check["id"]
    url = check["url"]
    keyword = check["keyword"]
    site = check["site"]

    print(f"\nChecking: {url}")
    print(f"  Keyword: {keyword}")

    gsc = pull_gsc_data(url, keyword, site)
    ga4 = pull_ga4_data(url, site)
    evaluation = evaluate_performance({"url": url, "keyword": keyword}, gsc, ga4)

    # Retro-score with quality scorer
    quality = retro_score_content(url, site)

    print(f"  GSC: {gsc}")
    print(f"  GA4: {ga4}")
    print(f"  Grade: {evaluation['grade']}")
    if quality:
        print(f"  Quality: {quality['overall_score']}/100 (grade {quality['grade']})")

    # Update log
    log = load_log()
    for e in log:
        if e["id"] == entry_id:
            e["performance_30d"] = {
                "gsc": gsc,
                "ga4": ga4,
                "grade": evaluation["grade"],
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            if quality:
                e["quality_retro"] = quality
            break
    if not dry_run:
        save_log(log)

    # Format and post
    entry = next((e for e in log if e["id"] == entry_id), {"title": keyword, "url": url})
    msg = format_discord_message(entry, gsc, ga4, evaluation)

    if dry_run:
        print(f"\n[DRY RUN] Discord message:\n{msg}")
    else:
        post_to_discord(msg, site)
        # Mark check as done
        check["status"] = "done"
        check["checked_at"] = datetime.now(timezone.utc).isoformat()
        with open(check_file, "w") as f:
            json.dump(check, f, indent=2)

    return {
        "entry_id": entry_id,
        "url": url,
        "gsc": gsc,
        "ga4": ga4,
        "evaluation": evaluation,
    }


def batch_score_all(dry_run: bool = False):
    """Nightly cron: batch score all published content, append trend to content_log.json."""
    log = load_log()
    scored = 0
    total = len(log)

    print(f"Batch scoring {total} entries...")
    for i, entry in enumerate(log):
        url = entry.get("url")
        site = entry.get("site")
        if not url:
            continue

        # Skip if already scored within last 7 days
        existing = entry.get("quality_retro", {})
        if existing.get("scored_at"):
            from datetime import timedelta
            scored_at = datetime.fromisoformat(existing["scored_at"])
            if datetime.now(timezone.utc) - scored_at < timedelta(days=7):
                continue

        print(f"  [{i+1}/{total}] {url[:80]}...")
        quality = retro_score_content(url, site)
        if quality:
            entry["quality_retro"] = quality
            scored += 1

    if not dry_run and scored > 0:
        save_log(log)

    print(f"\nBatch scoring complete: {scored}/{total} entries scored.")

    # Post weekly summary if enough data
    scored_entries = [e for e in log if e.get("quality_retro")]
    if scored_entries:
        scores = [e["quality_retro"]["overall_score"] for e in scored_entries]
        avg = sum(scores) / len(scores)
        print(f"Average quality score: {avg:.1f}/100 across {len(scored_entries)} pieces")


def main():
    parser = argparse.ArgumentParser(description="30-Day Performance Checker")
    parser.add_argument("--all", action="store_true", help="Check all pending")
    parser.add_argument("--url", help="Check specific URL")
    parser.add_argument("--batch-score", action="store_true", help="Batch score all published content (nightly cron)")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.batch_score:
        batch_score_all(dry_run=args.dry_run)
        return

    if args.url:
        log = load_log()
        entry = next((e for e in log if e["url"] == args.url), None)
        if not entry:
            print(f"URL not found in log: {args.url}", file=sys.stderr)
            sys.exit(1)
        gsc = pull_gsc_data(args.url, entry["keyword"], entry["site"])
        ga4 = pull_ga4_data(args.url, entry["site"])
        evaluation = evaluate_performance(entry, gsc, ga4)
        msg = format_discord_message(entry, gsc, ga4, evaluation)
        print(msg)
        return

    checks = get_pending_checks()
    if not checks:
        print("No pending performance checks due.")
        return

    print(f"Running {len(checks)} pending check(s)...")
    results = []
    for check_file, check in checks:
        result = run_check(check_file, check, dry_run=args.dry_run)
        results.append(result)

    winners = [r for r in results if r["evaluation"]["is_winner"]]
    print(f"\n{len(results)} check(s) complete. {len(winners)} winner(s) detected.")

    if winners:
        print("Winners — running pattern extraction...")
        pattern_script = str(_CFG.scripts_dir / "self_improvement" / "pattern_extract.py")
        for w in winners:
            try:
                subprocess.run(
                    [_CFG.venv_python, pattern_script, "--url", w["url"]],
                    capture_output=True, text=True, timeout=120,
                )
            except Exception as e:
                log.warning("Pattern extraction failed for %s: %s", w["url"], e)


if __name__ == "__main__":
    main()

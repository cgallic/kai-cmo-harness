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
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Load env
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

CONTENT_LOG = "/opt/cmo-analytics/data/content_log.json"
PENDING_CHECKS_DIR = "/opt/cmo-analytics/data/pending_checks"

# Win thresholds
WIN_POSITION = 5
WIN_CTR = 0.05        # 5%
WIN_TIME_ON_PAGE = 90 # seconds

SITE_URLS = {
    "kaicalls": "sc-domain:kaicalls.com",
    "buildwithkai": "sc-domain:buildwithkai.com",
    "abp": "sc-domain:awesomebackyardparties.com",
    "meetkai": "sc-domain:meetkai.xyz",
    "connorgallic": "sc-domain:connorgallic.com",
    "vocalscribe": "sc-domain:vocalscribe.xyz",
}

GA4_PROPERTY_IDS = {
    "kaicalls": os.environ.get("GA4_PROPERTY_KAICALLS", ""),
    "buildwithkai": os.environ.get("GA4_PROPERTY_BWK", ""),
    "abp": os.environ.get("GA4_PROPERTY_ABP", ""),
    "meetkai": os.environ.get("GA4_PROPERTY_MEETKAI", ""),
    "connorgallic": os.environ.get("GA4_PROPERTY_CONNORGALLIC", ""),
}

DISCORD_CHANNEL_IDS = {
    "kaicalls": "1469307381103198382",
    "buildwithkai": "1469307544454566020",
    "abp": "1469310748290191441",
    "meetkai": "1471889734841270332",
    "connorgallic": "1471889734841270332",
}


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
                "rowLimit": 1,
            },
        ).execute()

        rows = response.get("rows", [])
        if not rows:
            return {"impressions": 0, "clicks": 0, "ctr": 0.0, "position": None}

        row = rows[0]
        return {
            "impressions": row.get("impressions", 0),
            "clicks": row.get("clicks", 0),
            "ctr": round(row.get("ctr", 0.0), 4),
            "position": round(row.get("position", 0.0), 1),
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

    if evaluation["is_winner"]:
        lines.append("→ Pattern extracted to knowledge base.")
    elif evaluation["is_underperformer"]:
        lines.append("→ Consider: update angle, add more specifics, or target a less competitive keyword.")

    return "\n".join(lines)


def post_to_discord(message: str, site: str):
    channel_id = DISCORD_CHANNEL_IDS.get(site, DISCORD_CHANNEL_IDS["meetkai"])
    os.system(
        f'openclaw message send --channel discord --target {channel_id} --message "{message.replace(chr(34), chr(39))}"'
    )


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

    print(f"  GSC: {gsc}")
    print(f"  GA4: {ga4}")
    print(f"  Grade: {evaluation['grade']}")

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


def main():
    parser = argparse.ArgumentParser(description="30-Day Performance Checker")
    parser.add_argument("--all", action="store_true", help="Check all pending")
    parser.add_argument("--url", help="Check specific URL")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

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
        for w in winners:
            os.system(f'python3 /opt/cmo-analytics/scripts/pattern_extract.py --url "{w["url"]}"')


if __name__ == "__main__":
    main()

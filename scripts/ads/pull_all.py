#!/usr/bin/env python3
"""Unified ad platform pull — runs Meta, Google, and LinkedIn pulls.

Auto-detects which platforms have credentials configured and pulls from
all available. Writes a cross-platform summary to summary.json.

Usage:
    python scripts/ads/pull_all.py [--platforms meta,google,linkedin] [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from _pull_common import (
    env,
    has_creds,
    log,
    log_section,
    read_pull,
    today_str,
    write_pull,
)

# ---------------------------------------------------------------------------
# Platform registry
# ---------------------------------------------------------------------------

PLATFORMS = {
    "meta": {
        "script": "meta.py",
        "creds": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
        "label": "Meta (Facebook/Instagram)",
    },
    "google": {
        "script": "google.py",
        "creds": ["GOOGLE_CREDENTIALS_PATH", "GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_DEVELOPER_TOKEN"],
        "label": "Google Ads",
    },
    "linkedin": {
        "script": "linkedin.py",
        "creds": ["LINKEDINADS_ACCESS_TOKEN", "LINKEDINADS_ACCOUNT_ID"],
        "label": "LinkedIn Ads",
    },
}


def detect_platforms() -> List[str]:
    """Return list of platform names that have credentials configured."""
    available = []
    for name, info in PLATFORMS.items():
        if has_creds(*info["creds"]):
            available.append(name)
        else:
            missing = [k for k in info["creds"] if not env(k)]
            log(f"  {info['label']}: SKIP (missing: {', '.join(missing)})")
    return available


def run_platform(name: str, date: str) -> bool:
    """Run a single platform pull script. Returns True on success."""
    info = PLATFORMS[name]
    script_path = SCRIPT_DIR / info["script"]

    if not script_path.exists():
        log(f"  ERROR: Script not found: {script_path}")
        return False

    log(f"\n  Running {info['label']} pull...")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "pull", "--date", date],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per platform
            cwd=str(SCRIPT_DIR.parent.parent),  # repo root
        )

        # Forward stderr (progress logs)
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                log(f"    [{name}] {line}")

        if result.returncode == 0:
            output_path = result.stdout.strip()
            log(f"  {info['label']}: OK → {output_path}")
            return True
        else:
            log(f"  {info['label']}: FAILED (exit code {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        log(f"  {info['label']}: FAILED (timeout after 5 minutes)")
        return False
    except Exception as e:
        log(f"  {info['label']}: FAILED ({e})")
        return False


def build_summary(date: str, platforms_run: List[str]) -> Dict[str, Any]:
    """Build a cross-platform summary from individual pull files."""
    summary: Dict[str, Any] = {
        "date": date,
        "platforms_pulled": [],
        "platforms_failed": [],
        "totals": {
            "spend": 0.0,
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
        },
        "per_platform": {},
    }

    for name in platforms_run:
        data = read_pull(name, date)
        if data is None:
            summary["platforms_failed"].append(name)
            continue

        summary["platforms_pulled"].append(name)

        # Extract high-level metrics per platform
        platform_summary = _extract_platform_summary(name, data)
        summary["per_platform"][name] = platform_summary

        # Accumulate totals
        summary["totals"]["spend"] += platform_summary.get("spend_7d", 0)
        summary["totals"]["impressions"] += platform_summary.get("impressions_7d", 0)
        summary["totals"]["clicks"] += platform_summary.get("clicks_7d", 0)
        summary["totals"]["conversions"] += platform_summary.get("conversions_7d", 0)

    return summary


def _extract_platform_summary(name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from a platform's pull data."""
    result: Dict[str, Any] = {
        "spend_7d": 0.0,
        "impressions_7d": 0,
        "clicks_7d": 0,
        "conversions_7d": 0,
        "active_campaigns": 0,
        "active_ads": 0,
    }

    if name == "meta":
        # Account-level 7d insights
        insights = data.get("account_insights", {}).get("last_7d", {})
        result["spend_7d"] = _safe_float(insights.get("spend", 0))
        result["impressions_7d"] = _safe_int(insights.get("impressions", 0))
        result["clicks_7d"] = _safe_int(insights.get("clicks", 0))
        result["frequency_7d"] = _safe_float(insights.get("frequency", 0))
        result["reach_7d"] = _safe_int(insights.get("reach", 0))

        # Count conversions from actions
        for action in insights.get("actions", []):
            if action.get("action_type") in ("lead", "offsite_conversion.fb_pixel_lead"):
                result["conversions_7d"] += _safe_int(action.get("value", 0))

        # Count active entities
        campaigns = data.get("campaigns", [])
        result["active_campaigns"] = sum(
            1 for c in campaigns if c.get("effective_status") == "ACTIVE"
        )
        ads = data.get("ads", [])
        result["active_ads"] = sum(
            1 for a in ads if a.get("effective_status") == "ACTIVE"
        )

        # Audience breakdown
        adsets = data.get("adsets", [])
        audience_types = {}
        for adset in adsets:
            at = adset.get("audience_type", "unknown")
            audience_types[at] = audience_types.get(at, 0) + 1
        result["audience_types"] = audience_types

    elif name == "google":
        campaigns = data.get("campaigns", [])
        result["active_campaigns"] = len(campaigns)
        for c in campaigns:
            rollup = c.get("insights_14d", {})
            result["spend_7d"] += _safe_float(rollup.get("spend_usd", 0))
            result["impressions_7d"] += _safe_int(rollup.get("impressions", 0))
            result["clicks_7d"] += _safe_int(rollup.get("clicks", 0))
            result["conversions_7d"] += _safe_int(rollup.get("conversions", 0))

        ads = data.get("ads", [])
        result["active_ads"] = len(ads)

    elif name == "linkedin":
        campaigns = data.get("campaigns", [])
        result["active_campaigns"] = len(campaigns)
        for c in campaigns:
            insights = c.get("insights_7d", {})
            result["spend_7d"] += _safe_float(insights.get("costInLocalCurrency", 0))
            result["impressions_7d"] += _safe_int(insights.get("impressions", 0))
            result["clicks_7d"] += _safe_int(insights.get("clicks", 0))
            result["conversions_7d"] += _safe_int(
                insights.get("externalWebsiteConversions", 0)
            )

        creatives = data.get("creatives", [])
        result["active_ads"] = len(creatives)

    return result


def _safe_float(val: Any) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(val: Any) -> int:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def print_human_summary(summary: Dict[str, Any]) -> None:
    """Print a human-readable summary to stderr."""
    log_section("Ad Pull Summary")
    log(f"  Date: {summary['date']}")
    log(f"  Platforms pulled: {', '.join(summary['platforms_pulled']) or 'none'}")
    if summary["platforms_failed"]:
        log(f"  Platforms failed: {', '.join(summary['platforms_failed'])}")

    totals = summary["totals"]
    log(f"\n  Cross-Platform Totals (7d):")
    log(f"    Spend:       ${totals['spend']:,.2f}")
    log(f"    Impressions: {totals['impressions']:,}")
    log(f"    Clicks:      {totals['clicks']:,}")
    log(f"    Conversions: {totals['conversions']:,}")

    if totals["clicks"] > 0:
        ctr = (totals["clicks"] / totals["impressions"] * 100) if totals["impressions"] > 0 else 0
        cpc = totals["spend"] / totals["clicks"] if totals["clicks"] > 0 else 0
        cpl = totals["spend"] / totals["conversions"] if totals["conversions"] > 0 else 0
        log(f"    CTR:         {ctr:.2f}%")
        log(f"    CPC:         ${cpc:.2f}")
        if totals["conversions"] > 0:
            log(f"    CPL:         ${cpl:.2f}")

    for name, platform_data in summary.get("per_platform", {}).items():
        info = PLATFORMS.get(name, {})
        log(f"\n  {info.get('label', name)}:")
        log(f"    Campaigns: {platform_data.get('active_campaigns', 0)}")
        log(f"    Ads:       {platform_data.get('active_ads', 0)}")
        log(f"    Spend:     ${platform_data.get('spend_7d', 0):,.2f}")
        if "frequency_7d" in platform_data:
            log(f"    Frequency: {platform_data['frequency_7d']:.2f}")
        if "audience_types" in platform_data:
            log(f"    Audiences: {platform_data['audience_types']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull ad data from all configured platforms")
    parser.add_argument("--date", default=today_str(), help="Output date (YYYY-MM-DD)")
    parser.add_argument(
        "--platforms",
        default=None,
        help="Comma-separated list of platforms to pull (default: auto-detect)",
    )
    args = parser.parse_args()

    date = args.date

    log_section("Ad Platform Pull")
    log(f"  Date: {date}")

    # Determine which platforms to run
    if args.platforms:
        requested = [p.strip().lower() for p in args.platforms.split(",")]
        invalid = [p for p in requested if p not in PLATFORMS]
        if invalid:
            log(f"  ERROR: Unknown platforms: {', '.join(invalid)}")
            log(f"  Available: {', '.join(PLATFORMS.keys())}")
            return 1
        platforms = requested
    else:
        log("\n  Detecting configured platforms...")
        platforms = detect_platforms()

    if not platforms:
        log("\n  No ad platforms configured. Add credentials to .env.local:")
        for name, info in PLATFORMS.items():
            log(f"    {info['label']}: {', '.join(info['creds'])}")
        return 1

    log(f"\n  Will pull from: {', '.join(platforms)}")

    # Run each platform
    results: Dict[str, bool] = {}
    for name in platforms:
        results[name] = run_platform(name, date)

    succeeded = [name for name, ok in results.items() if ok]
    failed = [name for name, ok in results.items() if not ok]

    # Build and write summary
    if succeeded:
        summary = build_summary(date, succeeded)
        summary["platforms_failed"] = failed
        summary_path = write_pull("summary", summary, date)
        print_human_summary(summary)
        log(f"\n  Summary written to: {summary_path}")
        # Print summary path to stdout
        print(str(summary_path))

    if failed and not succeeded:
        log("\n  All platforms failed. Check credentials and API access.")
        return 1

    if failed:
        log(f"\n  Warning: {len(failed)} platform(s) failed: {', '.join(failed)}")
        return 0  # Partial success is still exit 0

    log(f"\n  All {len(succeeded)} platform(s) pulled successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

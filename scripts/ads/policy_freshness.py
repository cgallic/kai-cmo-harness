"""
Ad Policy Freshness Checker — Detects stale platform policies.

Checks each policy reference file's git commit date against known
platform policy update URLs. Flags policies older than configurable
threshold (default: 90 days) and provides update instructions.

Usage:
    python -m scripts.ads.policy_freshness check
    python -m scripts.ads.policy_freshness check --threshold 60
    python -m scripts.ads.policy_freshness report --format json
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

POLICY_DIR = _ROOT / "harness" / "references"
KAI_DIR = Path.home() / ".kai-marketing"
FRESHNESS_DB = KAI_DIR / "analytics" / "policy-freshness.jsonl"

log = logging.getLogger("policy-freshness")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


# Platform policy source URLs — where to check for updates
POLICY_SOURCES = {
    "google-ads-policy-reference.md": {
        "platform": "Google Ads",
        "policy_url": "https://support.google.com/adspolicy/answer/6008942",
        "changelog_url": "https://support.google.com/adspolicy/answer/9683793",
        "update_frequency": "Monthly",
    },
    "meta-ads-rules.md": {
        "platform": "Meta (Facebook/Instagram)",
        "policy_url": "https://www.facebook.com/policies/ads/",
        "changelog_url": "https://www.facebook.com/policies/ads/change-log",
        "update_frequency": "Quarterly",
    },
    "tiktok-ads-policy-reference.md": {
        "platform": "TikTok",
        "policy_url": "https://ads.tiktok.com/help/article/tiktok-advertising-policies-ad-creatives-landing-page",
        "changelog_url": "https://ads.tiktok.com/help/article/advertising-policies-change-log",
        "update_frequency": "Quarterly",
    },
    "linkedin-ads-rules.md": {
        "platform": "LinkedIn",
        "policy_url": "https://www.linkedin.com/legal/ads-policy",
        "changelog_url": None,
        "update_frequency": "Semi-annual",
    },
    "microsoft-ads-rules.md": {
        "platform": "Microsoft/Bing",
        "policy_url": "https://about.ads.microsoft.com/en-us/policies/ad-content-policies",
        "changelog_url": None,
        "update_frequency": "Quarterly",
    },
    "pinterest-ads-rules.md": {
        "platform": "Pinterest",
        "policy_url": "https://policy.pinterest.com/en/advertising-guidelines",
        "changelog_url": None,
        "update_frequency": "Semi-annual",
    },
    "snapchat-ads-policy-reference.md": {
        "platform": "Snapchat",
        "policy_url": "https://www.snap.com/en-US/ad-policies",
        "changelog_url": None,
        "update_frequency": "Semi-annual",
    },
    "amazon-ads-policy-reference.md": {
        "platform": "Amazon",
        "policy_url": "https://advertising.amazon.com/resources/ad-policy",
        "changelog_url": None,
        "update_frequency": "Quarterly",
    },
    "x-ads-policy-reference.md": {
        "platform": "X/Twitter",
        "policy_url": "https://business.x.com/en/help/ads-policies",
        "changelog_url": None,
        "update_frequency": "Quarterly",
    },
    "advertising-compliance.md": {
        "platform": "Cross-Platform (FTC/GDPR/CAN-SPAM)",
        "policy_url": "https://www.ftc.gov/business-guidance/advertising-marketing",
        "changelog_url": None,
        "update_frequency": "Annual (regulations change slowly)",
    },
}


def _get_file_age(filepath: Path) -> tuple[int, str]:
    """Get file age in days. Try git first, fall back to mtime."""
    # Try git log for last commit date
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            capture_output=True, text=True, cwd=str(_ROOT), timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            commit_date = datetime.fromisoformat(result.stdout.strip().replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - commit_date).days
            return age, commit_date.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback to file modification time
    if filepath.exists():
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
        age = (datetime.now(timezone.utc) - mtime).days
        return age, mtime.strftime("%Y-%m-%d")

    return -1, "unknown"


def _get_file_hash(filepath: Path) -> str:
    """Get SHA-256 hash of file content for change detection."""
    if filepath.exists():
        return hashlib.sha256(filepath.read_bytes()).hexdigest()[:12]
    return "missing"


def check_freshness(threshold_days: int = 90) -> list[dict]:
    """Check all policy files for freshness."""
    results = []

    for filename, source in POLICY_SOURCES.items():
        filepath = POLICY_DIR / filename
        exists = filepath.exists()
        age_days, last_updated = _get_file_age(filepath)
        content_hash = _get_file_hash(filepath)
        line_count = len(filepath.read_text().splitlines()) if exists else 0

        status = "ok"
        if not exists:
            status = "missing"
        elif age_days > threshold_days:
            status = "stale"
        elif age_days > threshold_days // 2:
            status = "aging"

        results.append({
            "file": filename,
            "platform": source["platform"],
            "exists": exists,
            "age_days": age_days,
            "last_updated": last_updated,
            "status": status,
            "line_count": line_count,
            "content_hash": content_hash,
            "policy_url": source["policy_url"],
            "changelog_url": source.get("changelog_url"),
            "update_frequency": source["update_frequency"],
            "threshold_days": threshold_days,
        })

    return results


def format_report(results: list[dict]) -> str:
    """Format freshness check as readable report."""
    stale = [r for r in results if r["status"] == "stale"]
    aging = [r for r in results if r["status"] == "aging"]
    ok = [r for r in results if r["status"] == "ok"]
    missing = [r for r in results if r["status"] == "missing"]

    lines = [
        "AD POLICY FRESHNESS REPORT",
        "=" * 60,
        f"Threshold: {results[0]['threshold_days']} days",
        f"Checked: {len(results)} policies",
        f"  Fresh: {len(ok)}  |  Aging: {len(aging)}  |  Stale: {len(stale)}  |  Missing: {len(missing)}",
        "",
    ]

    if stale:
        lines.append("STALE (needs update):")
        for r in stale:
            lines.append(f"  ! {r['platform']:<30} {r['age_days']:>4}d old (last: {r['last_updated']})")
            lines.append(f"    Check: {r['policy_url']}")
            if r.get("changelog_url"):
                lines.append(f"    Changelog: {r['changelog_url']}")
        lines.append("")

    if aging:
        lines.append("AGING (update soon):")
        for r in aging:
            lines.append(f"  ~ {r['platform']:<30} {r['age_days']:>4}d old (last: {r['last_updated']})")
        lines.append("")

    if ok:
        lines.append("FRESH:")
        for r in ok:
            lines.append(f"  + {r['platform']:<30} {r['age_days']:>4}d old ({r['line_count']} lines)")

    if missing:
        lines.append("\nMISSING:")
        for r in missing:
            lines.append(f"  X {r['platform']:<30} File not found: {r['file']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check ad policy freshness")
    subparsers = parser.add_subparsers(dest="command")

    check_p = subparsers.add_parser("check", help="Check all policies for freshness")
    check_p.add_argument("--threshold", type=int, default=90, help="Days before a policy is considered stale")

    report_p = subparsers.add_parser("report", help="Generate freshness report")
    report_p.add_argument("--format", choices=["text", "json"], default="text")
    report_p.add_argument("--threshold", type=int, default=90)

    args = parser.parse_args()

    if not args.command:
        args.command = "check"
        args.threshold = 90

    results = check_freshness(threshold_days=args.threshold)

    # Save to JSONL log
    KAI_DIR.mkdir(parents=True, exist_ok=True)
    (KAI_DIR / "analytics").mkdir(parents=True, exist_ok=True)
    with open(FRESHNESS_DB, "a") as f:
        f.write(json.dumps({
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "threshold": args.threshold,
            "stale": sum(1 for r in results if r["status"] == "stale"),
            "aging": sum(1 for r in results if r["status"] == "aging"),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "policies": [{k: v for k, v in r.items() if k not in ("policy_url", "changelog_url")} for r in results],
        }, default=str) + "\n")

    if hasattr(args, "format") and args.format == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_report(results))


if __name__ == "__main__":
    main()

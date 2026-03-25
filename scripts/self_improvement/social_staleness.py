#!/usr/bin/env python3
"""
Social Export Staleness Checker — Kai Harness Self-Improvement

Monitors freshness of social media CSV imports. Alerts when platform
data goes stale (>7 days warning, >14 days critical), since the learning
loop runs blind on social signals without fresh data.

Usage:
  python3 social_staleness.py              # check all platforms
  python3 social_staleness.py --critical   # only show critical (14+ days)
"""

import argparse
import json
from datetime import datetime, timezone
from typing import Optional

from scripts.harness_config import get_config

_CFG = get_config()

PLATFORMS = ["tiktok", "instagram", "youtube", "linkedin", "twitter"]
STALE_DAYS_WARNING = 7
STALE_DAYS_CRITICAL = 14


def get_last_import_per_platform() -> dict[str, Optional[datetime]]:
    """Detect the most recent import timestamp per platform.

    Primary: scan data/social_imports/processed/ file timestamps and detect
    platform from filename content.
    Secondary: scan content_log.json for source == "social_import", group by
    platform, and find max imported_at.

    Returns the more recent of the two per platform; None if never imported.
    """
    results: dict[str, Optional[datetime]] = {p: None for p in PLATFORMS}

    # Primary: file-based detection from processed directory
    processed_dir = _CFG.data_dir / "social_imports" / "processed"
    if processed_dir.exists():
        for fpath in processed_dir.iterdir():
            if not fpath.is_file():
                continue
            fname_lower = fpath.name.lower()
            for platform in PLATFORMS:
                if platform in fname_lower:
                    mtime = datetime.fromtimestamp(
                        fpath.stat().st_mtime, tz=timezone.utc
                    )
                    existing = results[platform]
                    if existing is None or mtime > existing:
                        results[platform] = mtime
                    break

    # Secondary: content_log.json entries with social_import source
    content_log_path = _CFG.content_log
    if content_log_path.exists():
        try:
            with open(content_log_path) as f:
                log_entries = json.load(f)
            for entry in log_entries:
                if entry.get("source") != "social_import":
                    continue
                platform = entry.get("platform", "").lower()
                if platform not in results:
                    continue
                imported_at = entry.get("imported_at")
                if not imported_at:
                    continue
                try:
                    ts = datetime.fromisoformat(str(imported_at))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    existing = results[platform]
                    if existing is None or ts > existing:
                        results[platform] = ts
                except (ValueError, TypeError):
                    continue
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    return results


def check_staleness() -> list[dict]:
    """Check each platform for data staleness.

    Returns list of dicts with: platform, days_since, severity, message.
    Severity: "ok" | "warning" | "critical" | "never"
    """
    last_imports = get_last_import_per_platform()
    now = datetime.now(timezone.utc)
    results = []

    for platform in PLATFORMS:
        last = last_imports.get(platform)

        if last is None:
            results.append({
                "platform": platform,
                "days_since": None,
                "severity": "never",
                "message": f"{platform.title()} has never been imported.",
            })
            continue

        days_since = (now - last).days

        if days_since >= STALE_DAYS_CRITICAL:
            severity = "critical"
            msg = (
                f"{platform.title()} data is {days_since} days old. "
                f"Learning loop is running blind on social."
            )
        elif days_since >= STALE_DAYS_WARNING:
            severity = "warning"
            msg = f"{platform.title()} data is {days_since} days since last import."
        else:
            severity = "ok"
            msg = f"{platform.title()} data is fresh ({days_since} days old)."

        results.append({
            "platform": platform,
            "days_since": days_since,
            "severity": severity,
            "message": msg,
        })

    return results


def format_reminder_message(stale_platforms: list[dict]) -> str:
    """Format a Discord-ready reminder message for stale platforms.

    Only includes warning/critical/never severity items.
    """
    actionable = [
        p for p in stale_platforms if p["severity"] in ("warning", "critical", "never")
    ]
    if not actionable:
        return ""

    drop_folder = str(_CFG.data_dir / "social_imports")

    lines = ["**\U0001f4c9 Social Data Staleness Report**\n"]

    critical = [p for p in actionable if p["severity"] == "critical"]
    warning = [p for p in actionable if p["severity"] == "warning"]
    never = [p for p in actionable if p["severity"] == "never"]

    if critical:
        lines.append("\U0001f534 **Critical:**")
        for p in critical:
            lines.append(f"  - {p['message']}")

    if never:
        lines.append("\u26ab **Never imported:**")
        for p in never:
            lines.append(f"  - {p['message']}")

    if warning:
        lines.append("\U0001f7e1 **Warning:**")
        for p in warning:
            lines.append(f"  - {p['message']}")

    lines.append(f"\nDrop CSV exports in: `{drop_folder}`")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Social Export Staleness Checker")
    parser.add_argument("--critical", action="store_true", help="Only show critical alerts")
    args = parser.parse_args()

    results = check_staleness()

    if args.critical:
        results = [r for r in results if r["severity"] == "critical"]

    if not results:
        print("No staleness issues detected.")
        return

    # Print individual results
    for r in results:
        icon = {
            "ok": "\u2705",
            "warning": "\U0001f7e1",
            "critical": "\U0001f534",
            "never": "\u26ab",
        }.get(r["severity"], "?")
        print(f"  {icon} {r['message']}")

    # Print formatted reminder if actionable items exist
    reminder = format_reminder_message(results)
    if reminder:
        print(f"\n--- Discord message ---\n{reminder}")


if __name__ == "__main__":
    main()

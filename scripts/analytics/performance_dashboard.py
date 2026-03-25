"""
Performance Dashboard — Persistent tracking with trend analysis.

Reads analytics snapshots over time and generates trend reports:
- Content quality trends (gate scores over time)
- SEO performance trends (GSC position, CTR over time)
- Content volume trends (pieces published per week)
- Winner/underperformer ratios over time
- Degrading content alerts (ranking drops)

Usage:
    python -m scripts.analytics.performance_dashboard weekly
    python -m scripts.analytics.performance_dashboard trends --weeks 12
    python -m scripts.analytics.performance_dashboard alerts
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

KAI_DIR = Path.home() / ".kai-marketing"
SNAPSHOT_DIR = KAI_DIR / "analytics" / "snapshots"
CONTENT_LOG = KAI_DIR / "content-log.jsonl"
QUALITY_LOG = KAI_DIR / "analytics" / "content-quality.jsonl"

log = logging.getLogger("dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file into a list of dicts."""
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _load_content_log() -> list[dict]:
    """Load content log from JSONL or fallback JSON."""
    entries = _load_jsonl(CONTENT_LOG)
    if entries:
        return entries

    # Fallback: legacy JSON array format
    legacy = _ROOT / "workspace" / "content_log.json"
    if legacy.exists():
        try:
            return json.loads(legacy.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return []


def weekly_summary() -> dict:
    """Generate a weekly summary of content and performance."""
    entries = _load_content_log()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # This week's content
    this_week = []
    for e in entries:
        pub_date = e.get("publish_date", "")
        if pub_date:
            try:
                pd = datetime.fromisoformat(pub_date).replace(tzinfo=timezone.utc)
                if pd >= week_ago:
                    this_week.append(e)
            except (ValueError, TypeError):
                pass

    # Performance breakdown
    graded = [e for e in entries if e.get("performance_30d")]
    winners = [e for e in graded if e["performance_30d"] == "winner"]
    average = [e for e in graded if e["performance_30d"] == "average"]
    under = [e for e in graded if e["performance_30d"] == "underperformer"]
    pending = [e for e in entries if not e.get("performance_30d")]

    # Quality scores
    quality_entries = _load_jsonl(QUALITY_LOG)
    this_week_quality = [
        q for q in quality_entries
        if q.get("scored_at", "")[:10] >= week_ago.strftime("%Y-%m-%d")
    ]
    avg_score = (
        sum(q.get("score", 0) for q in this_week_quality) / len(this_week_quality)
        if this_week_quality else 0
    )

    return {
        "period": f"{week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        "content_published_this_week": len(this_week),
        "total_content": len(entries),
        "performance": {
            "winners": len(winners),
            "average": len(average),
            "underperformers": len(under),
            "pending": len(pending),
            "win_rate": f"{len(winners)/len(graded)*100:.0f}%" if graded else "N/A",
        },
        "quality": {
            "pieces_scored_this_week": len(this_week_quality),
            "avg_score": round(avg_score, 1),
        },
    }


def trend_analysis(weeks: int = 12) -> dict:
    """Analyze trends over N weeks."""
    entries = _load_content_log()
    now = datetime.now(timezone.utc)

    weekly_data = defaultdict(lambda: {"published": 0, "winners": 0, "graded": 0})

    for e in entries:
        pub_date = e.get("publish_date", "")
        if not pub_date:
            continue
        try:
            pd = datetime.fromisoformat(pub_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        week_key = pd.strftime("%Y-W%U")
        weekly_data[week_key]["published"] += 1
        if e.get("performance_30d"):
            weekly_data[week_key]["graded"] += 1
            if e["performance_30d"] == "winner":
                weekly_data[week_key]["winners"] += 1

    # Sort by week and take last N
    sorted_weeks = sorted(weekly_data.items())[-weeks:]

    return {
        "weeks_analyzed": len(sorted_weeks),
        "weekly_trend": [
            {
                "week": week,
                "published": data["published"],
                "winners": data["winners"],
                "graded": data["graded"],
                "win_rate": f"{data['winners']/data['graded']*100:.0f}%" if data["graded"] > 0 else "N/A",
            }
            for week, data in sorted_weeks
        ],
        "total_published": sum(d["published"] for _, d in sorted_weeks),
        "total_winners": sum(d["winners"] for _, d in sorted_weeks),
        "avg_weekly_output": round(sum(d["published"] for _, d in sorted_weeks) / max(len(sorted_weeks), 1), 1),
    }


def degradation_alerts() -> list[dict]:
    """Find content that's degrading (ranking drops, CTR drops)."""
    snapshots = []
    if SNAPSHOT_DIR.exists():
        for f in SNAPSHOT_DIR.glob("*-gsc-*.jsonl"):
            snapshots.extend(_load_jsonl(f))

    if len(snapshots) < 2:
        return [{"alert": "info", "message": "Need 2+ GSC snapshots for degradation detection. Run analytics pull weekly."}]

    # Compare latest vs previous snapshot per site
    by_site = defaultdict(list)
    for s in snapshots:
        if s.get("status") == "ok":
            by_site[s.get("site", "unknown")].append(s)

    alerts = []
    for site, site_snapshots in by_site.items():
        if len(site_snapshots) < 2:
            continue

        # Sort by pulled_at
        site_snapshots.sort(key=lambda s: s.get("pulled_at", ""))
        latest = site_snapshots[-1]
        previous = site_snapshots[-2]

        # Compare top queries
        latest_queries = {q["query"]: q for q in latest.get("top_queries", [])}
        previous_queries = {q["query"]: q for q in previous.get("top_queries", [])}

        for query, curr in latest_queries.items():
            prev = previous_queries.get(query)
            if not prev:
                continue

            # Position degradation
            pos_change = curr.get("position", 0) - prev.get("position", 0)
            if pos_change > 3:  # dropped 3+ positions
                alerts.append({
                    "alert": "position_drop",
                    "site": site,
                    "query": query,
                    "previous_position": prev["position"],
                    "current_position": curr["position"],
                    "change": f"+{pos_change:.1f} positions (worse)",
                    "severity": "high" if pos_change > 5 else "medium",
                })

            # CTR degradation
            ctr_change = curr.get("ctr", 0) - prev.get("ctr", 0)
            if ctr_change < -1.0:  # dropped 1%+ CTR
                alerts.append({
                    "alert": "ctr_drop",
                    "site": site,
                    "query": query,
                    "previous_ctr": f"{prev['ctr']}%",
                    "current_ctr": f"{curr['ctr']}%",
                    "change": f"{ctr_change:+.1f}%",
                    "severity": "high" if ctr_change < -2.0 else "medium",
                })

    if not alerts:
        alerts.append({"alert": "info", "message": "No degradation detected. All content holding steady."})

    return alerts


def format_weekly(summary: dict) -> str:
    perf = summary["performance"]
    qual = summary["quality"]
    lines = [
        "WEEKLY CONTENT DASHBOARD",
        "=" * 50,
        f"Period: {summary['period']}",
        "",
        f"Published this week:   {summary['content_published_this_week']}",
        f"Total content:         {summary['total_content']}",
        "",
        "PERFORMANCE (graded content):",
        f"  Winners:         {perf['winners']}",
        f"  Average:         {perf['average']}",
        f"  Underperformers: {perf['underperformers']}",
        f"  Pending:         {perf['pending']}",
        f"  Win rate:        {perf['win_rate']}",
        "",
        "QUALITY:",
        f"  Pieces scored:   {qual['pieces_scored_this_week']}",
        f"  Avg score:       {qual['avg_score']}/100",
    ]
    return "\n".join(lines)


def format_trends(trends: dict) -> str:
    lines = [
        "CONTENT TREND ANALYSIS",
        "=" * 50,
        f"Weeks analyzed: {trends['weeks_analyzed']}",
        f"Avg weekly output: {trends['avg_weekly_output']} pieces",
        "",
        f"{'Week':<12} {'Published':>10} {'Winners':>10} {'Win Rate':>10}",
        "-" * 45,
    ]
    for w in trends["weekly_trend"]:
        lines.append(f"{w['week']:<12} {w['published']:>10} {w['winners']:>10} {w['win_rate']:>10}")
    lines.extend([
        "-" * 45,
        f"{'TOTAL':<12} {trends['total_published']:>10} {trends['total_winners']:>10}",
    ])
    return "\n".join(lines)


def format_alerts(alerts: list[dict]) -> str:
    lines = ["DEGRADATION ALERTS", "=" * 50]
    high = [a for a in alerts if a.get("severity") == "high"]
    med = [a for a in alerts if a.get("severity") == "medium"]
    info = [a for a in alerts if a.get("alert") == "info"]

    if high:
        lines.append("\nHIGH PRIORITY:")
        for a in high:
            lines.append(f"  ! [{a['alert']}] {a['site']}: '{a['query']}' — {a['change']}")
    if med:
        lines.append("\nMEDIUM:")
        for a in med:
            lines.append(f"  ~ [{a['alert']}] {a['site']}: '{a['query']}' — {a['change']}")
    if info:
        for a in info:
            lines.append(f"  {a['message']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Content Performance Dashboard")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("weekly", help="Weekly summary")
    trends_p = subparsers.add_parser("trends", help="Trend analysis")
    trends_p.add_argument("--weeks", type=int, default=12)
    subparsers.add_parser("alerts", help="Degradation alerts")

    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    if args.command == "weekly":
        data = weekly_summary()
        print(format_weekly(data) if args.format == "text" else json.dumps(data, indent=2))
    elif args.command == "trends":
        data = trend_analysis(args.weeks)
        print(format_trends(data) if args.format == "text" else json.dumps(data, indent=2))
    elif args.command == "alerts":
        data = degradation_alerts()
        print(format_alerts(data) if args.format == "text" else json.dumps(data, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

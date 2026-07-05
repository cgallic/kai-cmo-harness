#!/usr/bin/env python3
"""
Kai CMO Harness — Weekly Marketing Report
============================================
Generate a formatted weekly marketing report pulling from all data sources.

Usage:
  python scripts/reporting/weekly_report.py                          # Generate report
  python scripts/reporting/weekly_report.py --site myproduct         # Single site
  python scripts/reporting/weekly_report.py --save reports/weekly.md  # Save to file
  python scripts/reporting/weekly_report.py --format html            # HTML output

Data sources: GA4, GSC, Supabase, content_log.json, competitor intel, Gemini (recommendations)
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"
INTEL_DIR = DATA_DIR / "intel"
CONTENT_LOG = DATA_DIR / "content_log.json"

# Allow direct invocation (python3 scripts/reporting/weekly_report.py) from any cwd.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# performance_30d drifted across writers (dict | legacy str | None) — always
# read grades through this helper (see scripts/self_improvement/grades.py).
from scripts.self_improvement.grades import get_grade  # noqa: E402


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _safe_import(module_path: str):
    """Try importing analytics modules."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        return __import__(module_path, fromlist=[""])
    except Exception:
        return None


def gather_traffic_data(site_key: str) -> dict:
    """Pull GA4 traffic data."""
    config = _load_config()
    products = {p["id"]: p for p in config.get("products", [])}
    product = products.get(site_key, {})
    ga4_env = product.get("ga4_property_env", "")
    property_id = os.environ.get(ga4_env, "")

    if not property_id:
        return {"available": False, "reason": f"No GA4 property for {site_key}"}

    try:
        mod = _safe_import("analytics.google_analytics")
        if not mod:
            return {"available": False, "reason": "GA4 module not found"}
        ga = mod.GoogleAnalytics(property_id)
        overview = ga.get_overview(days=7)
        return {"available": True, "data": overview}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def gather_seo_data(site_key: str) -> dict:
    """Pull GSC SEO data."""
    config = _load_config()
    products = {p["id"]: p for p in config.get("products", [])}
    product = products.get(site_key, {})
    gsc_env = product.get("gsc_url_env", "")
    gsc_url = os.environ.get(gsc_env, "")

    if not gsc_url:
        return {"available": False, "reason": f"No GSC for {site_key}"}

    try:
        mod = _safe_import("analytics.search_console")
        if not mod:
            return {"available": False, "reason": "GSC module not found"}
        gsc = mod.SearchConsoleAnalytics(gsc_url)
        queries = gsc.get_queries(days=7, limit=20)
        return {"available": True, "data": {"queries": queries}}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def gather_content_data() -> dict:
    """Pull content pipeline data."""
    if not CONTENT_LOG.exists():
        return {"available": False, "total": 0, "this_week": 0}

    log = json.loads(CONTENT_LOG.read_text())
    this_week = [e for e in log if e.get("created", "") > datetime.now(timezone.utc).strftime("%Y-%m-%d")]
    winners = [e for e in log if get_grade(e) == "winner"]

    return {
        "available": True,
        "total": len(log),
        "this_week": len(this_week),
        "winners": len(winners),
        "avg_four_us": sum(e.get("four_us_score", 0) for e in log) / max(len(log), 1),
    }


def gather_competitor_data() -> dict:
    """Pull competitor intel."""
    comp_db = INTEL_DIR / "competitors.db"
    if not comp_db.exists():
        return {"available": False}

    conn = sqlite3.connect(str(comp_db))
    new_posts = conn.execute(
        "SELECT COUNT(*) FROM rss_entries WHERE discovered_at > datetime('now', '-7 days')"
    ).fetchone()[0]
    new_pages = conn.execute(
        "SELECT COUNT(*) FROM sitemap_pages WHERE first_seen > datetime('now', '-7 days')"
    ).fetchone()[0]
    conn.close()

    return {"available": True, "new_posts": new_posts, "new_pages": new_pages}


def generate_recommendations(report_data: dict) -> str:
    """Use Gemini to generate strategic recommendations."""
    try:
        from google.genai import Client as GenaiClient
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return "Set GEMINI_API_KEY for AI-generated recommendations."

        client = GenaiClient(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Based on this marketing data, provide 5 specific, actionable recommendations for next week.

Data:
{json.dumps(report_data, indent=2, default=str)[:3000]}

Format as numbered list. Each recommendation should be:
- Specific (name the keyword, channel, or action)
- Measurable (what metric to watch)
- Achievable in one week

No preamble. Just the 5 recommendations."""
        )
        return response.text.strip()
    except Exception as e:
        return f"Recommendations unavailable: {e}"


def generate_report(site_key: str = "all", output_format: str = "markdown") -> str:
    """Generate the weekly marketing report."""
    config = _load_config()
    products = config.get("products", [])
    if site_key != "all":
        products = [p for p in products if p.get("id") == site_key]

    now = datetime.now(timezone.utc)
    report_data = {}

    report = f"# Weekly Marketing Report\n"
    report += f"Period: {now.strftime('%B %d, %Y')} (Last 7 Days)\n\n"

    # ── Traffic ───────────────────────────────────────────────────────────
    report += "## Traffic\n\n"
    for product in products:
        pid = product["id"]
        traffic = gather_traffic_data(pid)
        report_data[f"traffic_{pid}"] = traffic

        if traffic.get("available"):
            data = traffic["data"]
            report += f"### {product.get('name', pid)}\n"
            report += f"| Metric | Value |\n|--------|-------|\n"
            for key, val in (data if isinstance(data, dict) else {}).items():
                report += f"| {key} | {val} |\n"
            report += "\n"
        else:
            report += f"### {product.get('name', pid)}\n{traffic.get('reason', 'No data')}\n\n"

    # ── SEO ───────────────────────────────────────────────────────────────
    report += "## SEO\n\n"
    for product in products:
        pid = product["id"]
        seo = gather_seo_data(pid)
        report_data[f"seo_{pid}"] = seo

        if seo.get("available"):
            queries = seo["data"].get("queries", [])[:10]
            report += f"### {product.get('name', pid)} — Top Queries\n"
            report += "| Query | Position | Clicks | Impressions |\n"
            report += "|-------|----------|--------|-------------|\n"
            for q in queries:
                report += f"| {q.get('query', '')} | {q.get('position', 0):.1f} | {q.get('clicks', 0)} | {q.get('impressions', 0)} |\n"
            report += "\n"
        else:
            report += f"### {product.get('name', pid)}\n{seo.get('reason', 'No data')}\n\n"

    # ── Content Pipeline ──────────────────────────────────────────────────
    content = gather_content_data()
    report_data["content"] = content
    report += "## Content Pipeline\n\n"
    report += f"| Metric | Value |\n|--------|-------|\n"
    report += f"| Total tracked pieces | {content.get('total', 0)} |\n"
    report += f"| Published this week | {content.get('this_week', 0)} |\n"
    report += f"| Winners (30d) | {content.get('winners', 0)} |\n"
    report += f"| Avg Four U's score | {content.get('avg_four_us', 0):.1f}/16 |\n\n"

    # ── Competitive Intel ─────────────────────────────────────────────────
    comp = gather_competitor_data()
    report_data["competitive"] = comp
    report += "## Competitive Intelligence\n\n"
    if comp.get("available"):
        report += f"| Metric | Value |\n|--------|-------|\n"
        report += f"| New competitor blog posts | {comp.get('new_posts', 0)} |\n"
        report += f"| New competitor pages | {comp.get('new_pages', 0)} |\n\n"
    else:
        report += "No competitor data. Run `python scripts/intel/competitor_monitor.py --check`\n\n"

    # ── Recommendations ───────────────────────────────────────────────────
    report += "## Recommendations\n\n"
    recommendations = generate_recommendations(report_data)
    report += recommendations + "\n\n"

    # ── Footer ────────────────────────────────────────────────────────────
    report += f"\n---\nGenerated by Kai CMO Harness — {now.strftime('%Y-%m-%d %H:%M UTC')}\n"

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate weekly marketing report")
    parser.add_argument("--site", default="all", help="Site key or 'all'")
    parser.add_argument("--save", help="Save report to file")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"])
    args = parser.parse_args()

    report = generate_report(site_key=args.site, output_format=args.format)

    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text(report)
        print(f"Report saved to {args.save}")
    else:
        print(report)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Kai CMO Harness — SERP Tracker
================================
Track keyword rankings for your site AND competitors daily.
Stores in SQLite, alerts on position changes > 3.

Usage:
  python scripts/intel/serp_tracker.py --track                    # Track all configured keywords
  python scripts/intel/serp_tracker.py --track --keyword "crm"    # Track specific keyword
  python scripts/intel/serp_tracker.py --report                   # Show ranking report
  python scripts/intel/serp_tracker.py --alerts                   # Show position changes > 3

Data source: Google Search Console (GSC) for your sites, Gemini estimation for competitors.
For more accurate competitor data, add DATAFORSEO_API_KEY to .env.
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
DATA_DIR = REPO_ROOT / "data" / "intel"
DB_PATH = DATA_DIR / "serp_tracker.db"


def _init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rankings (
            keyword TEXT NOT NULL,
            domain TEXT NOT NULL,
            position REAL,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            ctr REAL DEFAULT 0,
            tracked_at TEXT DEFAULT (datetime('now')),
            source TEXT DEFAULT 'gsc'
        );
        CREATE TABLE IF NOT EXISTS alerts (
            keyword TEXT NOT NULL,
            domain TEXT NOT NULL,
            old_position REAL,
            new_position REAL,
            change REAL,
            alert_type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_rank_kw ON rankings(keyword, domain);
        CREATE INDEX IF NOT EXISTS idx_rank_date ON rankings(tracked_at);
    """)
    conn.close()


def _load_config() -> dict:
    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.yaml.example"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text()) or {}
    return {}


def _get_gsc_rankings(site_url: str, keywords: list[str] | None = None) -> list[dict]:
    """Pull rankings from Google Search Console."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from analytics.search_console import SearchConsoleAnalytics
        gsc = SearchConsoleAnalytics(site_url)
        data = gsc.get_queries(days=3, limit=100)

        results = []
        for row in data:
            query = row.get("query", "")
            if keywords and not any(kw.lower() in query.lower() for kw in keywords):
                continue
            results.append({
                "keyword": query,
                "position": row.get("position", 0),
                "impressions": row.get("impressions", 0),
                "clicks": row.get("clicks", 0),
                "ctr": row.get("ctr", 0),
            })
        return results
    except Exception as e:
        print(f"  GSC unavailable: {e}")
        return []


def track_rankings(keyword_filter: str | None = None):
    """Track rankings for all configured sites and keywords."""
    _init_db()
    config = _load_config()
    conn = sqlite3.connect(str(DB_PATH))

    products = config.get("products", [])
    tracked_keywords = config.get("tracked_keywords", [])

    keywords = [keyword_filter] if keyword_filter else (tracked_keywords or None)

    for product in products:
        site_url = product.get("url", "")
        gsc_env = product.get("gsc_url_env", "")
        gsc_url = os.environ.get(gsc_env, "")

        if not gsc_url:
            print(f"  Skipping {product['name']} — no GSC configured")
            continue

        print(f"\nTracking: {product['name']} ({gsc_url})")
        rankings = _get_gsc_rankings(gsc_url, keywords)

        for r in rankings:
            # Store ranking
            conn.execute(
                "INSERT INTO rankings (keyword, domain, position, impressions, clicks, ctr, source) "
                "VALUES (?, ?, ?, ?, ?, ?, 'gsc')",
                (r["keyword"], site_url, r["position"], r["impressions"], r["clicks"], r["ctr"]),
            )

            # Check for position changes
            prev = conn.execute(
                "SELECT position FROM rankings WHERE keyword = ? AND domain = ? "
                "AND tracked_at < datetime('now') ORDER BY tracked_at DESC LIMIT 1",
                (r["keyword"], site_url),
            ).fetchone()

            if prev and prev[0]:
                change = prev[0] - r["position"]  # Positive = improved
                if abs(change) >= 3:
                    alert_type = "improved" if change > 0 else "dropped"
                    conn.execute(
                        "INSERT INTO alerts (keyword, domain, old_position, new_position, change, alert_type) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (r["keyword"], site_url, prev[0], r["position"], change, alert_type),
                    )
                    icon = "📈" if change > 0 else "📉"
                    print(f"  {icon} {r['keyword']}: {prev[0]:.1f} → {r['position']:.1f} ({change:+.1f})")

        print(f"  Tracked {len(rankings)} keywords")

    conn.commit()
    conn.close()


def show_report():
    """Show current ranking report."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Latest rankings grouped by domain
    rows = conn.execute("""
        SELECT keyword, domain, position, impressions, clicks, ctr, tracked_at
        FROM rankings
        WHERE tracked_at > datetime('now', '-7 days')
        ORDER BY domain, position ASC
    """).fetchall()
    conn.close()

    if not rows:
        print("No ranking data yet. Run: python scripts/intel/serp_tracker.py --track")
        return

    print(f"\n{'═'*70}")
    print(f"  SERP Ranking Report")
    print(f"{'═'*70}")

    current_domain = ""
    for row in rows:
        if row["domain"] != current_domain:
            current_domain = row["domain"]
            print(f"\n  {current_domain}")
            print(f"  {'Keyword':<40} {'Pos':>5} {'Impr':>7} {'Clicks':>7} {'CTR':>6}")
            print(f"  {'─'*65}")
        ctr_str = f"{row['ctr']*100:.1f}%" if row["ctr"] else "N/A"
        print(f"  {row['keyword'][:40]:<40} {row['position']:>5.1f} {row['impressions']:>7} {row['clicks']:>7} {ctr_str:>6}")


def show_alerts():
    """Show recent ranking alerts (position changes > 3)."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT keyword, domain, old_position, new_position, change, alert_type, created_at
        FROM alerts
        WHERE created_at > datetime('now', '-7 days')
        ORDER BY ABS(change) DESC
    """).fetchall()
    conn.close()

    if not rows:
        print("No ranking alerts in the last 7 days.")
        return

    print(f"\n{'═'*70}")
    print(f"  Ranking Alerts (Last 7 Days)")
    print(f"{'═'*70}")

    for row in rows:
        icon = "📈" if row["alert_type"] == "improved" else "📉"
        print(f"  {icon} {row['keyword'][:35]}")
        print(f"    {row['domain']} — {row['old_position']:.1f} → {row['new_position']:.1f} ({row['change']:+.1f})")
        print()


def main():
    parser = argparse.ArgumentParser(description="Track keyword rankings")
    parser.add_argument("--track", action="store_true", help="Track rankings for all configured sites")
    parser.add_argument("--keyword", help="Filter by specific keyword")
    parser.add_argument("--report", action="store_true", help="Show ranking report")
    parser.add_argument("--alerts", action="store_true", help="Show position change alerts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.track:
        track_rankings(args.keyword)
    elif args.report:
        show_report()
    elif args.alerts:
        show_alerts()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

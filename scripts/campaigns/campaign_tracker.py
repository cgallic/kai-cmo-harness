#!/usr/bin/env python3
"""
Kai CMO Harness — Campaign Tracker
=====================================
Track campaign performance across channels.

Usage:
  python scripts/campaigns/campaign_tracker.py --create "Q1 Launch" --dir campaigns/q1-launch/
  python scripts/campaigns/campaign_tracker.py --update "Q1 Launch" --channel email --metric opens --value 2450
  python scripts/campaigns/campaign_tracker.py --report "Q1 Launch"
  python scripts/campaigns/campaign_tracker.py --list

Stores campaign metrics in SQLite for trend tracking.
"""

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "campaigns"
DB_PATH = DATA_DIR / "campaigns.db"


def _init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            campaign_id TEXT,
            campaign_type TEXT,
            goal TEXT,
            product TEXT,
            keyword TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            assets_dir TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            channel TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            recorded_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (campaign_name) REFERENCES campaigns(name)
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_campaign ON metrics(campaign_name);
        CREATE INDEX IF NOT EXISTS idx_metrics_channel ON metrics(campaign_name, channel);
    """)
    # Migrate pre-campaign_id databases in place (ALTER is a no-op after the
    # first run; CREATE TABLE IF NOT EXISTS never adds columns to old DBs).
    cols = [row[1] for row in conn.execute("PRAGMA table_info(campaigns)")]
    if "campaign_id" not in cols:
        conn.execute("ALTER TABLE campaigns ADD COLUMN campaign_id TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_id ON campaigns(campaign_id)"
    )
    conn.commit()
    conn.close()


def create_campaign(name: str, assets_dir: str = "", campaign_type: str = "", goal: str = "",
                    product: str = "", keyword: str = "", campaign_id: str = ""):
    """Register a new campaign for tracking.

    ``campaign_id`` is the shared join key minted by campaign_planner
    (``cmp-YYYYMMDD-<slug>``). It is read from the manifest.json in
    ``assets_dir`` when not passed explicitly.
    """
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))

    # Load manifest if assets_dir provided
    if assets_dir:
        manifest_path = Path(assets_dir) / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            campaign_type = campaign_type or manifest.get("campaign_type", "")
            goal = goal or manifest.get("goal", "")
            product = product or manifest.get("product", "")
            keyword = keyword or manifest.get("keyword", "")
            campaign_id = campaign_id or manifest.get("campaign_id", "")

    try:
        conn.execute(
            "INSERT INTO campaigns (name, campaign_id, campaign_type, goal, product, keyword, assets_dir, start_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, campaign_id or None, campaign_type, goal, product, keyword, assets_dir,
             datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        )
        conn.commit()
        print(f"Campaign '{name}' created.")
    except sqlite3.IntegrityError:
        # Row exists — backfill campaign_id if we now have one and it is empty.
        if campaign_id:
            conn.execute(
                "UPDATE campaigns SET campaign_id = ? WHERE name = ? "
                "AND (campaign_id IS NULL OR campaign_id = '')",
                (campaign_id, name),
            )
            conn.commit()
        print(f"Campaign '{name}' already exists.")
    conn.close()


def find_campaign(campaign_id: str) -> dict | None:
    """Look up a tracked campaign by its shared campaign_id join key."""
    if not campaign_id:
        return None
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM campaigns WHERE campaign_id = ?", (campaign_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_metric(campaign_name: str, channel: str, metric: str, value: float):
    """Record a campaign metric."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO metrics (campaign_name, channel, metric, value) VALUES (?, ?, ?, ?)",
        (campaign_name, channel, metric, value),
    )
    conn.commit()
    conn.close()
    print(f"Recorded: {campaign_name} / {channel} / {metric} = {value}")


def show_report(campaign_name: str):
    """Show campaign performance report."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    campaign = conn.execute("SELECT * FROM campaigns WHERE name = ?", (campaign_name,)).fetchone()
    if not campaign:
        print(f"Campaign '{campaign_name}' not found.")
        return

    print(f"\n{'═'*60}")
    print(f"  Campaign: {campaign['name']}")
    if campaign["campaign_id"]:
        print(f"  Campaign ID: {campaign['campaign_id']}")
    print(f"  Type: {campaign['campaign_type']} | Goal: {campaign['goal']}")
    print(f"  Product: {campaign['product']} | Keyword: {campaign['keyword']}")
    print(f"  Status: {campaign['status']} | Started: {campaign['start_date']}")
    print(f"{'═'*60}")

    # Get metrics grouped by channel
    channels = conn.execute(
        "SELECT DISTINCT channel FROM metrics WHERE campaign_name = ?", (campaign_name,)
    ).fetchall()

    for ch in channels:
        channel = ch["channel"]
        print(f"\n  {channel.upper()}")
        print(f"  {'─'*40}")

        metrics = conn.execute(
            "SELECT metric, value, recorded_at FROM metrics "
            "WHERE campaign_name = ? AND channel = ? ORDER BY recorded_at DESC",
            (campaign_name, channel),
        ).fetchall()

        # Show latest value for each metric
        seen = set()
        for m in metrics:
            if m["metric"] not in seen:
                seen.add(m["metric"])
                print(f"    {m['metric']:<25} {m['value']:>10,.1f}  ({m['recorded_at'][:10]})")

    conn.close()


def list_campaigns():
    """List all campaigns."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    campaigns = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    conn.close()

    if not campaigns:
        print("No campaigns tracked yet.")
        return

    print(f"\n{'═'*60}")
    print(f"  Campaigns")
    print(f"{'═'*60}")

    for c in campaigns:
        status_icon = {"active": "🟢", "paused": "🟡", "completed": "✅"}.get(c["status"], "⚪")
        print(f"  {status_icon} {c['name']}")
        print(f"    Type: {c['campaign_type']} | Product: {c['product']} | Started: {c['start_date']}")


def main():
    parser = argparse.ArgumentParser(description="Track campaign performance")
    parser.add_argument("--create", metavar="NAME", help="Create a new campaign")
    parser.add_argument("--dir", help="Campaign assets directory (for --create)")
    parser.add_argument("--campaign-id", help="Shared campaign id (cmp-YYYYMMDD-<slug>; read from manifest.json if omitted)")
    parser.add_argument("--update", metavar="NAME", help="Update campaign metric")
    parser.add_argument("--channel", help="Channel (email, social, ads, landing_page, etc.)")
    parser.add_argument("--metric", help="Metric name (opens, clicks, spend, conversions, etc.)")
    parser.add_argument("--value", type=float, help="Metric value")
    parser.add_argument("--report", metavar="NAME", help="Show campaign report")
    parser.add_argument("--list", action="store_true", help="List all campaigns")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.create:
        create_campaign(args.create, assets_dir=args.dir or "", campaign_id=args.campaign_id or "")
    elif args.update:
        if not all([args.channel, args.metric, args.value is not None]):
            print("--update requires --channel, --metric, and --value")
            return
        update_metric(args.update, args.channel, args.metric, args.value)
    elif args.report:
        show_report(args.report)
    elif args.list:
        list_campaigns()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

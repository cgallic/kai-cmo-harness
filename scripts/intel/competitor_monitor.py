#!/usr/bin/env python3
"""
Kai CMO Harness — Competitor Monitor
======================================
Track competitor activity: blog posts, new pages, social frequency, domain metrics.

Usage:
  python scripts/intel/competitor_monitor.py --check
  python scripts/intel/competitor_monitor.py --check --competitor "Competitor 1"
  python scripts/intel/competitor_monitor.py --diff              # Sitemap diff since last run
  python scripts/intel/competitor_monitor.py --report            # Full competitor report

Config: Add competitors to config.yaml:
  competitors:
    - url: "https://competitor1.com"
      name: "Competitor 1"
      rss_feed: "https://competitor1.com/blog/feed"
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "intel"
DB_PATH = DATA_DIR / "competitors.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KaiCMO/1.0; +https://github.com/cgallic/kai-cmo-harness)"
}


def _init_db():
    """Initialize SQLite database for competitor tracking."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rss_entries (
            id TEXT PRIMARY KEY,
            competitor TEXT NOT NULL,
            title TEXT,
            url TEXT,
            published TEXT,
            discovered_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sitemap_pages (
            url TEXT NOT NULL,
            competitor TEXT NOT NULL,
            first_seen TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (url, competitor)
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            competitor TEXT NOT NULL,
            check_type TEXT NOT NULL,
            data TEXT,
            checked_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_rss_comp ON rss_entries(competitor);
        CREATE INDEX IF NOT EXISTS idx_sitemap_comp ON sitemap_pages(competitor);
    """)
    conn.close()


def _load_competitors() -> list[dict]:
    """Load competitor list from config.yaml."""
    import yaml
    config_path = REPO_ROOT / "config.yaml"
    if not config_path.exists():
        config_path = REPO_ROOT / "config.yaml.example"
    if not config_path.exists():
        return []
    try:
        cfg = yaml.safe_load(config_path.read_text()) or {}
        return cfg.get("competitors", [])
    except Exception:
        return []


def check_rss(competitor: dict) -> list[dict]:
    """Check competitor RSS feed for new posts."""
    rss_url = competitor.get("rss_feed", "")
    if not rss_url:
        # Try common RSS paths
        base = competitor["url"].rstrip("/")
        for path in ["/feed", "/blog/feed", "/rss", "/blog/rss.xml", "/feed.xml"]:
            try:
                resp = requests.get(base + path, headers=HEADERS, timeout=10)
                if resp.ok and ("xml" in resp.headers.get("content-type", "") or "<rss" in resp.text[:200]):
                    rss_url = base + path
                    break
            except Exception:
                continue
    if not rss_url:
        return []

    try:
        resp = requests.get(rss_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    entries = []
    try:
        root = ET.fromstring(resp.text)
        # Handle both RSS and Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for item in items[:20]:
            title = item.findtext("title") or item.findtext("atom:title", namespaces=ns) or ""
            link = ""
            link_el = item.find("link")
            if link_el is not None:
                link = link_el.text or link_el.get("href", "")
            pub = item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or ""

            entry_id = hashlib.sha256(f"{competitor['name']}:{link}".encode()).hexdigest()[:16]
            entries.append({
                "id": entry_id,
                "competitor": competitor["name"],
                "title": title.strip(),
                "url": link.strip(),
                "published": pub.strip(),
            })
    except ET.ParseError:
        pass

    return entries


def check_sitemap(competitor: dict) -> list[str]:
    """Fetch and parse competitor sitemap for new pages."""
    base = competitor["url"].rstrip("/")
    sitemap_urls = [f"{base}/sitemap.xml", f"{base}/sitemap_index.xml"]

    pages = set()

    for sitemap_url in sitemap_urls:
        try:
            resp = requests.get(sitemap_url, headers=HEADERS, timeout=10)
            if not resp.ok:
                continue
            root = ET.fromstring(resp.text)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Check for sitemap index
            sub_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
            if sub_sitemaps:
                for sub in sub_sitemaps[:5]:  # Limit to 5 sub-sitemaps
                    try:
                        sub_resp = requests.get(sub.text, headers=HEADERS, timeout=10)
                        sub_root = ET.fromstring(sub_resp.text)
                        for url_el in sub_root.findall(".//sm:url/sm:loc", ns):
                            if url_el.text:
                                pages.add(url_el.text.strip())
                    except Exception:
                        continue
            else:
                for url_el in root.findall(".//sm:url/sm:loc", ns):
                    if url_el.text:
                        pages.add(url_el.text.strip())
            break
        except Exception:
            continue

    return sorted(pages)


def store_rss_entries(entries: list[dict]) -> list[dict]:
    """Store RSS entries, return only NEW ones."""
    conn = sqlite3.connect(str(DB_PATH))
    new_entries = []
    for entry in entries:
        try:
            conn.execute(
                "INSERT INTO rss_entries (id, competitor, title, url, published) VALUES (?, ?, ?, ?, ?)",
                (entry["id"], entry["competitor"], entry["title"], entry["url"], entry["published"]),
            )
            new_entries.append(entry)
        except sqlite3.IntegrityError:
            pass  # Already seen
    conn.commit()
    conn.close()
    return new_entries


def store_sitemap_pages(competitor_name: str, pages: list[str]) -> list[str]:
    """Store sitemap pages, return NEW pages since last check."""
    conn = sqlite3.connect(str(DB_PATH))
    now = datetime.now(timezone.utc).isoformat()
    new_pages = []

    for page in pages:
        cursor = conn.execute(
            "SELECT url FROM sitemap_pages WHERE url = ? AND competitor = ?",
            (page, competitor_name),
        )
        if cursor.fetchone():
            conn.execute(
                "UPDATE sitemap_pages SET last_seen = ? WHERE url = ? AND competitor = ?",
                (now, page, competitor_name),
            )
        else:
            conn.execute(
                "INSERT INTO sitemap_pages (url, competitor, first_seen, last_seen) VALUES (?, ?, ?, ?)",
                (page, competitor_name, now, now),
            )
            new_pages.append(page)

    conn.commit()
    conn.close()
    return new_pages


def run_check(competitor_filter: str | None = None):
    """Run a full competitor check."""
    _init_db()
    competitors = _load_competitors()

    if not competitors:
        print("No competitors configured. Add to config.yaml under 'competitors:'")
        return

    if competitor_filter:
        competitors = [c for c in competitors if competitor_filter.lower() in c["name"].lower()]

    results = []
    for comp in competitors:
        print(f"\nChecking: {comp['name']} ({comp['url']})")

        # RSS check
        entries = check_rss(comp)
        new_entries = store_rss_entries(entries)
        print(f"  RSS: {len(entries)} total, {len(new_entries)} new")
        for entry in new_entries[:3]:
            print(f"    NEW: {entry['title']}")

        # Sitemap check
        pages = check_sitemap(comp)
        new_pages = store_sitemap_pages(comp["name"], pages)
        print(f"  Sitemap: {len(pages)} total pages, {len(new_pages)} new")
        for page in new_pages[:5]:
            print(f"    NEW: {page}")

        results.append({
            "competitor": comp["name"],
            "url": comp["url"],
            "rss_total": len(entries),
            "rss_new": len(new_entries),
            "new_posts": [{"title": e["title"], "url": e["url"]} for e in new_entries],
            "sitemap_total": len(pages),
            "sitemap_new": len(new_pages),
            "new_pages": new_pages[:10],
        })

    return results


def run_diff():
    """Show sitemap changes since last run."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Pages seen for the first time in the last 7 days
    rows = conn.execute("""
        SELECT competitor, url, first_seen
        FROM sitemap_pages
        WHERE first_seen > datetime('now', '-7 days')
        ORDER BY first_seen DESC
    """).fetchall()
    conn.close()

    if not rows:
        print("No new pages detected in the last 7 days.")
        return

    print(f"\nNew competitor pages (last 7 days): {len(rows)}")
    current_comp = ""
    for row in rows:
        if row["competitor"] != current_comp:
            current_comp = row["competitor"]
            print(f"\n  {current_comp}:")
        print(f"    {row['first_seen'][:10]} — {row['url']}")


def run_report():
    """Generate a full competitor activity report."""
    _init_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    competitors = _load_competitors()
    report_lines = ["# Competitor Activity Report", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", ""]

    for comp in competitors:
        name = comp["name"]
        report_lines.append(f"## {name}")
        report_lines.append(f"URL: {comp['url']}")

        # Recent posts
        posts = conn.execute(
            "SELECT title, url, published FROM rss_entries WHERE competitor = ? ORDER BY discovered_at DESC LIMIT 5",
            (name,),
        ).fetchall()
        if posts:
            report_lines.append("\n### Recent Blog Posts")
            for p in posts:
                report_lines.append(f"- [{p['title']}]({p['url']}) — {p['published'][:10] if p['published'] else 'N/A'}")

        # New pages
        new_pages = conn.execute(
            "SELECT url, first_seen FROM sitemap_pages WHERE competitor = ? AND first_seen > datetime('now', '-30 days') ORDER BY first_seen DESC LIMIT 10",
            (name,),
        ).fetchall()
        if new_pages:
            report_lines.append("\n### New Pages (Last 30 Days)")
            for p in new_pages:
                report_lines.append(f"- {p['first_seen'][:10]} — {p['url']}")

        # Total pages
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM sitemap_pages WHERE competitor = ?", (name,)
        ).fetchone()
        report_lines.append(f"\nTotal tracked pages: {total['cnt']}")
        report_lines.append("")

    conn.close()

    report = "\n".join(report_lines)
    report_path = DATA_DIR / f"report-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    report_path.write_text(report)
    print(report)
    print(f"\nSaved to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Monitor competitor activity")
    parser.add_argument("--check", action="store_true", help="Run full competitor check")
    parser.add_argument("--diff", action="store_true", help="Show sitemap changes since last run")
    parser.add_argument("--report", action="store_true", help="Generate competitor report")
    parser.add_argument("--competitor", help="Filter by competitor name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.check:
        results = run_check(args.competitor)
        if args.json and results:
            print(json.dumps(results, indent=2))
    elif args.diff:
        run_diff()
    elif args.report:
        run_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

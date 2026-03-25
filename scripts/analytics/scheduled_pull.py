"""
Scheduled Analytics Pull — Cron-compatible script that pulls fresh data weekly.

Pulls from GSC, GA4, and Meta Ads (if configured), stores snapshots
in ~/.kai-marketing/analytics/snapshots/ as timestamped JSONL.

Usage:
    python -m scripts.analytics.scheduled_pull --all
    python -m scripts.analytics.scheduled_pull --source gsc --site kaicalls
    python -m scripts.analytics.scheduled_pull --source meta --site kaicalls

Cron (run weekly on Monday at 8am):
    0 8 * * 1 cd /path/to/kai-marketing && python -m scripts.analytics.scheduled_pull --all
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

KAI_DIR = Path.home() / ".kai-marketing"
SNAPSHOT_DIR = KAI_DIR / "analytics" / "snapshots"

log = logging.getLogger("analytics-pull")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


def _ensure_dirs():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _snapshot_path(source: str, site: str) -> Path:
    """Generate timestamped snapshot filename."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return SNAPSHOT_DIR / f"{ts}-{source}-{site}.jsonl"


def pull_gsc(site: str) -> dict:
    """Pull Google Search Console data for a site."""
    try:
        from scripts.analytics.search_console import SearchConsole
        from scripts.analytics.sites_config import get_site_config

        site_cfg = get_site_config(site)
        if not site_cfg:
            return {"source": "gsc", "site": site, "status": "error", "error": "Site not configured"}

        sc = SearchConsole(
            site_url=site_cfg.get("gsc_property", ""),
            credentials_path=site_cfg.get("gsc_credentials_path", ""),
        )

        # Pull last 30 days of keyword data
        end_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=33)).strftime("%Y-%m-%d")

        # Top queries
        queries = sc._query(start_date, end_date, ["query"], row_limit=100)

        # Top pages
        pages = sc._query(start_date, end_date, ["page"], row_limit=50)

        return {
            "source": "gsc",
            "site": site,
            "status": "ok",
            "period": f"{start_date} to {end_date}",
            "top_queries": [
                {
                    "query": row.get("keys", [""])[0],
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": round(row.get("ctr", 0) * 100, 2),
                    "position": round(row.get("position", 0), 1),
                }
                for row in queries[:50]
            ],
            "top_pages": [
                {
                    "page": row.get("keys", [""])[0],
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": round(row.get("ctr", 0) * 100, 2),
                    "position": round(row.get("position", 0), 1),
                }
                for row in pages[:20]
            ],
            "pulled_at": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError as e:
        return {"source": "gsc", "site": site, "status": "error", "error": f"Missing dependency: {e}"}
    except Exception as e:
        return {"source": "gsc", "site": site, "status": "error", "error": str(e)}


def pull_ga4(site: str) -> dict:
    """Pull Google Analytics 4 data for a site."""
    try:
        from scripts.analytics.google_analytics import GoogleAnalytics
        from scripts.analytics.sites_config import get_site_config

        site_cfg = get_site_config(site)
        if not site_cfg:
            return {"source": "ga4", "site": site, "status": "error", "error": "Site not configured"}

        ga = GoogleAnalytics(
            property_id=site_cfg.get("ga4_property", ""),
            credentials_path=site_cfg.get("ga4_credentials_path", ""),
        )

        # Pull last 30 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        summary = ga.get_summary(start_date, end_date)
        top_pages = ga.get_top_pages(start_date, end_date, limit=20)

        return {
            "source": "ga4",
            "site": site,
            "status": "ok",
            "period": f"{start_date} to {end_date}",
            "summary": summary,
            "top_pages": top_pages,
            "pulled_at": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError as e:
        return {"source": "ga4", "site": site, "status": "error", "error": f"Missing dependency: {e}"}
    except Exception as e:
        return {"source": "ga4", "site": site, "status": "error", "error": str(e)}


def pull_meta_ads(site: str) -> dict:
    """Pull Meta Ads performance data."""
    try:
        from scripts.analytics.facebook_ads import MetaAds
        from scripts.analytics.sites_config import get_site_config

        site_cfg = get_site_config(site)
        if not site_cfg:
            return {"source": "meta", "site": site, "status": "error", "error": "Site not configured"}

        meta = MetaAds(
            access_token=site_cfg.get("meta_access_token", ""),
            ad_account_id=site_cfg.get("meta_ad_account_id", ""),
        )

        # Pull last 30 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        campaigns = meta.get_campaign_insights(start_date, end_date)

        return {
            "source": "meta",
            "site": site,
            "status": "ok",
            "period": f"{start_date} to {end_date}",
            "campaigns": campaigns,
            "pulled_at": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError as e:
        return {"source": "meta", "site": site, "status": "error", "error": f"Missing dependency: {e}"}
    except Exception as e:
        return {"source": "meta", "site": site, "status": "error", "error": str(e)}


def _get_configured_sites() -> list[str]:
    """Get all configured site keys from config."""
    config_path = KAI_DIR / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            cfg = yaml.safe_load(config_path.read_text()) or {}
            sites = cfg.get("sites", {})
            if isinstance(sites, dict):
                return list(sites.keys())
        except Exception:
            pass

    # Fallback: try harness config
    try:
        from scripts.harness_config import get_config
        cfg = get_config()
        return list(cfg.sites.gsc_urls.keys())
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Pull analytics data from configured sources")
    parser.add_argument("--all", action="store_true", help="Pull all sources for all sites")
    parser.add_argument("--source", choices=["gsc", "ga4", "meta"], help="Pull specific source")
    parser.add_argument("--site", help="Pull for specific site")
    parser.add_argument("--format", choices=["json", "summary"], default="summary")
    args = parser.parse_args()

    _ensure_dirs()

    sites = [args.site] if args.site else _get_configured_sites()
    if not sites:
        print("No sites configured. Run: kai-config set sites.mysite.gsc_property 'sc-domain:mysite.com'")
        sys.exit(1)

    sources = ["gsc", "ga4", "meta"] if args.all else ([args.source] if args.source else ["gsc", "ga4"])
    results = []

    for site in sites:
        for source in sources:
            log.info("Pulling %s for %s...", source, site)
            if source == "gsc":
                data = pull_gsc(site)
            elif source == "ga4":
                data = pull_ga4(site)
            elif source == "meta":
                data = pull_meta_ads(site)
            else:
                continue

            # Save snapshot
            path = _snapshot_path(source, site)
            with open(path, "a") as f:
                f.write(json.dumps(data, default=str) + "\n")

            results.append(data)

            if data.get("status") == "ok":
                log.info("  ✓ %s/%s pulled successfully", source, site)
            else:
                log.warning("  ✗ %s/%s failed: %s", source, site, data.get("error", "unknown"))

    # Summary
    ok = sum(1 for r in results if r.get("status") == "ok")
    fail = sum(1 for r in results if r.get("status") == "error")

    if args.format == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"\nAnalytics Pull Complete: {ok} succeeded, {fail} failed")
        for r in results:
            status_icon = "✓" if r.get("status") == "ok" else "✗"
            print(f"  {status_icon} {r['source']}/{r['site']}: {r.get('status')} {r.get('error', '')}")

        if ok > 0:
            print(f"\nSnapshots saved to {SNAPSHOT_DIR}/")


if __name__ == "__main__":
    main()

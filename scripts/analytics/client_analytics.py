#!/usr/bin/env python3
"""
Unified Client Analytics CLI
Pull analytics from all configured sources for any client.

Usage:
    python client_analytics.py clawdbot --days 30
    python client_analytics.py mdi --source ga4
    python client_analytics.py --list  # List all clients
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "clients" / "clients_config.json"
CLIENTS_DIR = PROJECT_ROOT / "clients"
ANALYTICS_DIR = Path(__file__).resolve().parent

# Add analytics dir to path for local imports
sys.path.insert(0, str(ANALYTICS_DIR))

# Colors for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def c(color: str, text: str) -> str:
    return f"{getattr(Colors, color.upper(), '')}{text}{Colors.RESET}"


def header(title: str, icon: str = ""):
    print()
    print(c("cyan", "=" * 70))
    print(c("bold", f" {icon} {title}"))
    print(c("cyan", "=" * 70))


def subheader(title: str):
    print()
    print(c("yellow", f">> {title}"))
    print(c("dim", "-" * 60))


def metric(label: str, value: Any, change: str = None):
    change_str = ""
    if change:
        is_positive = str(change).startswith("+")
        change_str = f" ({c('green' if is_positive else 'red', change)})"
    print(f"  {c('dim', label + ':')} {c('bold', str(value))}{change_str}")


def table(data: List[Dict], columns: List[str] = None, max_rows: int = 20):
    if not data:
        print(c("dim", "  No data available"))
        return

    if columns is None:
        columns = list(data[0].keys())

    # Calculate column widths
    widths = {}
    for col in columns:
        max_len = len(str(col))
        for row in data[:max_rows]:
            val_len = len(str(row.get(col, "")))
            max_len = max(max_len, min(val_len, 40))
        widths[col] = max_len + 2

    # Print header
    header_line = "".join(c("cyan", str(col).ljust(widths[col])) for col in columns)
    print(f"  {header_line}")
    print(f"  {''.join('-' * widths[col] for col in columns)}")

    # Print rows
    for row in data[:max_rows]:
        row_line = "".join(str(row.get(col, ""))[:40].ljust(widths[col]) for col in columns)
        print(f"  {row_line}")


def load_config() -> Dict:
    """Load client configuration"""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def find_client(config: Dict, key: str) -> Optional[Dict]:
    """Find client in any category"""
    key_lower = key.lower()
    for category in ["products", "clients", "leadgen", "personal", "internal"]:
        for client_key, client_data in config.get(category, {}).items():
            if client_key.lower() == key_lower:
                client_data["_key"] = client_key
                client_data["_category"] = category
                return client_data
    return None


def list_clients(config: Dict):
    """List all configured clients"""
    header("Configured Clients", "📋")

    for category in ["products", "clients", "leadgen", "personal"]:
        clients = config.get(category, {})
        if not clients:
            continue

        subheader(category.title())
        for key, data in clients.items():
            sources = []
            if data.get("ga_property"):
                sources.append("GA4")
            if data.get("gsc_site"):
                sources.append("GSC")
            if data.get("supabase"):
                sources.append("Supabase")

            sources_str = f"[{', '.join(sources)}]" if sources else "[No analytics]"
            status = data.get("status", "unknown")
            print(f"  {c('bold', key)}: {data.get('name', key)} - {status} {c('dim', sources_str)}")


def load_dotenv(env_path: Path):
    """Simple .env loader"""
    if not env_path.exists():
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def pull_meta_ads(days: int = 30) -> Dict:
    """Pull Meta/Facebook Ads data"""
    try:
        from facebook_ads import FacebookAds, fb_ads_config

        if not fb_ads_config.is_configured:
            return {"error": "META_ACCESS_TOKEN or META_AD_ACCOUNT_ID not configured"}

        fb = FacebookAds()

        account = fb.get_account_info()
        stats = fb.get_quick_stats(days=days)
        campaigns = fb.get_campaign_insights(days=days)
        daily = fb.get_daily_spend(days=min(days, 14))

        return {
            "account": {
                "name": account.get("name"),
                "currency": account.get("currency"),
            },
            "summary": {
                "spend": stats.get("total_spend", "$0"),
                "impressions": stats.get("impressions", 0),
                "clicks": stats.get("clicks", 0),
                "ctr": stats.get("ctr", "0%"),
                "cpm": stats.get("cpm", "$0"),
                "cpc": stats.get("cpc", "$0"),
                "leads": stats.get("leads", 0),
                "cost_per_lead": stats.get("cost_per_lead", "N/A"),
            },
            "today_vs_yesterday": stats.get("today_vs_yesterday", {}),
            "campaigns": campaigns[:10],
            "daily_trend": daily,
        }

    except ImportError:
        return {"error": "facebook_ads module not available"}
    except Exception as e:
        return {"error": str(e)}


def pull_ga4(property_id: str, days: int = 30) -> Dict:
    """Pull Google Analytics 4 data"""
    try:
        from google_analytics import GoogleAnalytics

        ga = GoogleAnalytics(property_id=property_id)

        start_date = f"{days}daysAgo"
        end_date = "today"

        overview = ga.get_overview(start_date, end_date)
        sources = ga.get_traffic_sources(start_date, end_date, limit=15)
        channels = ga.get_channel_grouping(start_date, end_date)
        pages = ga.get_top_pages(start_date, end_date, limit=10)

        # Try Facebook traffic
        try:
            fb_traffic = ga.get_facebook_traffic(start_date=start_date)
        except:
            fb_traffic = {}

        return {
            "overview": overview,
            "sources": sources,
            "channels": channels,
            "top_pages": pages,
            "facebook_traffic": fb_traffic.get("summary", {}),
        }

    except ImportError:
        return {"error": "google_analytics module not available"}
    except Exception as e:
        return {"error": str(e)}


def pull_gsc(site_url: str, days: int = 30) -> Dict:
    """Pull Google Search Console data"""
    try:
        from search_console import SearchConsole

        gsc = SearchConsole(site_url=site_url)

        queries = gsc.get_top_queries(limit=20)
        pages = gsc.get_top_pages(limit=10)
        opportunities = gsc.get_keyword_opportunities()

        return {
            "top_queries": queries,
            "top_pages": pages,
            "opportunities": opportunities.get("opportunities", [])[:10],
            "quick_wins": opportunities.get("quick_wins", [])[:5],
        }

    except ImportError:
        return {"error": "search_console module not available"}
    except Exception as e:
        return {"error": str(e)}


def pull_supabase(client_key: str, supabase_config: Dict, days: int = 30) -> Dict:
    """Pull Supabase business data using client CLI"""
    import subprocess

    try:
        # Find the client analytics directory
        client_analytics_dir = None
        for possible_name in [client_key, client_key.title(), client_key.lower(), "Kai_calls"]:
            test_path = CLIENTS_DIR / possible_name / "scripts" / "analytics"
            if test_path.exists() and (test_path / "cli.py").exists():
                client_analytics_dir = test_path
                break

        if not client_analytics_dir:
            return {"error": "No client analytics CLI found"}

        # Run the client's executive command to get JSON data
        result = subprocess.run(
            ["python3", "cli.py", "executive"],
            cwd=str(client_analytics_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            # Try running overview command and parse text output
            result = subprocess.run(
                ["python3", "cli.py", "overview"],
                cwd=str(client_analytics_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return {"overview_text": result.stdout, "format": "text"}
            else:
                return {"error": f"CLI error: {result.stderr}"}

        # Parse JSON output
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            return {"overview_text": result.stdout, "format": "text"}

    except subprocess.TimeoutExpired:
        return {"error": "CLI timed out"}
    except Exception as e:
        return {"error": str(e)}


def generate_report(client_key: str, client_data: Dict, days: int = 30, source: str = "all"):
    """Generate comprehensive analytics report"""
    header(f"{client_data.get('name', client_key)} Analytics Report", "📊")
    print(f"  Period: Last {days} days | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  URL: {client_data.get('url', 'N/A')}")

    results = {}
    warnings = []

    # Meta Ads
    if source in ["all", "fb-ads", "meta"]:
        subheader("Meta/Facebook Ads")
        fb_data = pull_meta_ads(days)
        results["meta_ads"] = fb_data

        if "error" in fb_data:
            print(f"  {c('yellow', 'WARNING:')} {fb_data['error']}")
            warnings.append(f"Meta Ads: {fb_data['error']}")
        else:
            metric("Account", fb_data["account"]["name"])
            metric("Total Spend", fb_data["summary"]["spend"])
            metric("Impressions", f"{fb_data['summary']['impressions']:,}")
            metric("Clicks", f"{fb_data['summary']['clicks']:,}")
            metric("CTR", fb_data["summary"]["ctr"])
            metric("Leads", fb_data["summary"]["leads"])
            metric("Cost/Lead", fb_data["summary"]["cost_per_lead"])

            tvsy = fb_data.get("today_vs_yesterday", {})
            if tvsy:
                print()
                metric("Today", tvsy.get("today_spend", "$0"))
                metric("Yesterday", tvsy.get("yesterday_spend", "$0"))
                metric("Change", tvsy.get("change", "0%"))

            if fb_data.get("campaigns"):
                print()
                print(c("dim", "  Campaign Performance:"))
                table(fb_data["campaigns"][:5], ["campaign_name", "spend", "clicks", "ctr", "leads", "cost_per_lead"])

    # Google Analytics 4
    if source in ["all", "ga4", "ga"]:
        ga_property = client_data.get("ga_property")
        if ga_property:
            subheader("Google Analytics 4")
            ga_data = pull_ga4(ga_property, days)
            results["ga4"] = ga_data

            if "error" in ga_data:
                print(f"  {c('yellow', 'WARNING:')} {ga_data['error']}")
                warnings.append(f"GA4: {ga_data['error']}")
            else:
                overview = ga_data.get("overview", {})
                metric("Active Users", overview.get("active_users", "N/A"))
                metric("Sessions", overview.get("sessions", "N/A"))
                metric("Page Views", overview.get("page_views", "N/A"))
                metric("Bounce Rate", overview.get("bounce_rate", "N/A"))
                metric("Engagement Rate", overview.get("engagement_rate", "N/A"))

                fb_traffic = ga_data.get("facebook_traffic", {})
                if fb_traffic:
                    print()
                    print(c("dim", "  Facebook Traffic:"))
                    metric("FB Sessions", fb_traffic.get("total_sessions", 0))
                    metric("FB Conversions", fb_traffic.get("total_conversions", 0))

                if ga_data.get("sources"):
                    print()
                    print(c("dim", "  Top Traffic Sources:"))
                    table(ga_data["sources"][:7], ["source", "medium", "sessions", "users"])
        else:
            if source == "ga4":
                print(f"  {c('yellow', 'No GA4 property configured for this client')}")

    # Google Search Console
    if source in ["all", "gsc", "search"]:
        gsc_site = client_data.get("gsc_site")
        if gsc_site:
            subheader("Google Search Console (SEO)")
            gsc_data = pull_gsc(gsc_site, days)
            results["gsc"] = gsc_data

            if "error" in gsc_data:
                print(f"  {c('yellow', 'WARNING:')} {gsc_data['error']}")
                warnings.append(f"GSC: {gsc_data['error']}")
            else:
                if gsc_data.get("top_queries"):
                    print(c("dim", "  Top Search Queries:"))
                    table(gsc_data["top_queries"][:10], ["query", "clicks", "impressions", "ctr", "position"])

                if gsc_data.get("opportunities"):
                    print()
                    print(c("dim", "  SEO Opportunities (high impressions, poor position):"))
                    table(gsc_data["opportunities"][:5], ["query", "impressions", "position"])

                if gsc_data.get("quick_wins"):
                    print()
                    print(c("dim", "  Quick Wins (good position, low CTR):"))
                    table(gsc_data["quick_wins"][:5], ["query", "ctr", "impressions"])
        else:
            if source == "gsc":
                print(f"  {c('yellow', 'No GSC site configured for this client')}")

    # Supabase Business Data
    if source in ["all", "supabase", "db"]:
        supabase_config = client_data.get("supabase")
        if supabase_config:
            subheader("Business Metrics (Database)")
            db_data = pull_supabase(client_key, supabase_config, days)
            results["supabase"] = db_data

            if "error" in db_data:
                print(f"  {c('yellow', 'WARNING:')} {db_data['error']}")
                warnings.append(f"Supabase: {db_data['error']}")
            else:
                # Handle text output from CLI
                if db_data.get("format") == "text":
                    print(db_data.get("overview_text", "No data"))
                # Handle Kai Calls executive JSON format
                elif db_data.get("metrics"):
                    metrics = db_data["metrics"]
                    metric("Total Users", metrics.get("total_users", 0))
                    metric("Total Businesses", metrics.get("total_businesses", 0))
                    metric("Active Subscriptions", metrics.get("active_subscriptions", 0))
                    metric("Total Calls", f"{metrics.get('total_calls', 0):,}")
                    metric("Total Leads", f"{metrics.get('total_leads', 0):,}")
                    metric("Avg Call Duration", metrics.get("avg_call_duration", "N/A"))

                    # Trends
                    if db_data.get("trends"):
                        print()
                        trends = db_data["trends"]
                        metric("This Week Calls", trends.get("this_week_calls", 0))
                        metric("Last Week Calls", trends.get("last_week_calls", 0))
                        metric("Call Growth", trends.get("call_growth_pct", "N/A"))
                        metric("This Week Leads", trends.get("this_week_leads", 0))

                    # Subscriptions
                    if db_data.get("subscriptions"):
                        print()
                        subs = db_data["subscriptions"]
                        metric("Active", subs.get("active", 0))
                        metric("Inactive", subs.get("inactive", 0))
                        metric("Trialing", subs.get("trialing_active", 0))
                else:
                    # Generic format
                    if db_data.get("overview"):
                        overview = db_data["overview"]
                        for key, value in overview.items():
                            metric(key.replace("_", " ").title(), value)

                    # Generic table counts
                    if db_data.get("table_counts"):
                        print()
                        print(c("dim", "  Table Counts:"))
                        for table_name, count in db_data["table_counts"].items():
                            print(f"    {table_name}: {count}")
        else:
            if source == "supabase":
                print(f"  {c('yellow', 'No Supabase configured for this client')}")

    # Summary
    if warnings:
        subheader("Warnings")
        for w in warnings:
            print(f"  {c('yellow', '!')} {w}")

    print()
    print(c("cyan", "=" * 70))
    print(c("dim", f"  Report generated for {client_data.get('name', client_key)}"))
    print(c("dim", f"  Data sources queried: {source}"))
    print(c("cyan", "=" * 70))

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Pull analytics for any configured client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python client_analytics.py clawdbot
  python client_analytics.py mdi --days 7
  python client_analytics.py snapped_ai_collective --source fb-ads
  python client_analytics.py --list
        """,
    )

    parser.add_argument("client", nargs="?", help="Client key (e.g., clawdbot, mdi, snapped_ai_collective)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Lookback period (default: 30)")
    parser.add_argument(
        "--source",
        "-s",
        choices=["all", "fb-ads", "ga4", "gsc", "supabase"],
        default="all",
        help="Data source to pull",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all configured clients")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    if not config:
        print(f"Error: Could not load {CONFIG_PATH}")
        sys.exit(1)

    # List clients
    if args.list or not args.client:
        list_clients(config)
        sys.exit(0)

    # Find client
    client = find_client(config, args.client)
    if not client:
        print(f"Error: Client '{args.client}' not found in configuration")
        print("\nAvailable clients:")
        for cat in ["products", "clients", "leadgen", "personal"]:
            for key in config.get(cat, {}).keys():
                print(f"  - {key}")
        sys.exit(1)

    # Load any .env files
    load_dotenv(ANALYTICS_DIR / ".env")

    # Check for client-specific .env
    client_key = client["_key"]
    for possible_name in [client_key, client_key.title(), "Kai_calls"]:
        client_env = CLIENTS_DIR / possible_name / "scripts" / "analytics" / ".env"
        if client_env.exists():
            load_dotenv(client_env)
            break

    # Generate report
    results = generate_report(client_key, client, args.days, args.source)

    if args.json:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()

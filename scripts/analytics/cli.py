#!/usr/bin/env python3
"""
CMO Analytics System CLI
Unified analytics with Google Analytics, Search Console, and Supabase

Usage: python -m analytics.cli <command> [subcommand] [options]
"""

import argparse
import sys
from typing import List, Dict, Any

# Rich terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def c(color: str, text: str) -> str:
    """Apply color to text"""
    return f"{getattr(Colors, color.upper(), '')}{text}{Colors.RESET}"


def header(title: str, icon: str = ""):
    """Print a header"""
    line = "=" * 60
    print()
    print(c("cyan", line))
    print(c("bold", f" {icon} {title}"))
    print(c("cyan", line))


def subheader(title: str):
    """Print a subheader"""
    print()
    print(c("yellow", f">> {title}"))
    print(c("dim", "-" * 50))


def metric(label: str, value: Any, change: str = None):
    """Print a metric"""
    change_str = ""
    if change:
        is_positive = str(change).startswith("+")
        change_str = f" ({c('green' if is_positive else 'red', change)})"
    print(f"  {c('dim', label + ':')} {c('bold', str(value))}{change_str}")


def table(data: List[Dict], columns: List[str] = None, max_rows: int = 30):
    """Print a formatted table"""
    if not data:
        print(c("dim", "  No data available"))
        return

    if columns is None:
        columns = list(data[0].keys())

    # Calculate column widths
    widths = {}
    for col in columns:
        max_len = len(col)
        for row in data[:max_rows]:
            val_len = len(str(row.get(col, "")))
            max_len = max(max_len, val_len)
        widths[col] = min(max_len + 2, 50)

    # Print header
    header_line = "".join(c("cyan", col.ljust(widths[col])) for col in columns)
    print(f"  {header_line}")
    print(f"  {''.join('-' * widths[col] for col in columns)}")

    # Print rows
    for i, row in enumerate(data[:max_rows]):
        row_line = "".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        print(f"  {row_line if i % 2 == 0 else c('dim', row_line)}")

    if len(data) > max_rows:
        print(c("dim", f"  ... and {len(data) - max_rows} more rows"))


def bar_chart(data: List[Dict], label_key: str, value_key: str, max_width: int = 40):
    """Print a simple bar chart"""
    if not data:
        return

    max_val = max(d[value_key] for d in data)
    max_label_len = max(len(str(d[label_key])) for d in data)

    for item in data[:15]:
        label = str(item[label_key]).ljust(max_label_len)
        bar_width = int((item[value_key] / max_val) * max_width) if max_val > 0 else 0
        bar = "█" * bar_width
        print(f"  {c('dim', label)} {c('blue', bar)} {item[value_key]}")


def funnel(stages: List[Dict]):
    """Print a funnel visualization"""
    if not stages:
        return

    print()
    max_count = max(s["count"] for s in stages)

    for i, stage in enumerate(stages):
        bar_width = int((stage["count"] / max_count) * 40) if max_count > 0 else 0
        bar = "█" * bar_width
        arrow = " ↓" if i < len(stages) - 1 else ""
        print(f"  {c('cyan', stage['stage'].ljust(12))} {c('green', bar)} {stage['count']} ({stage['rate']}){arrow}")
    print()


# ============ COMMANDS ============

def cmd_summary(args):
    """Executive summary"""
    from .dashboard import Dashboard

    header("Executive Summary", "📊")
    print("\nLoading data...")

    dashboard = Dashboard()
    data = dashboard.get_executive_summary(args.start, args.end)

    # Website metrics
    if data.get("website"):
        subheader("Website Performance")
        w = data["website"]
        metric("Active Users", w.get("users", "N/A"))
        metric("Sessions", w.get("sessions", "N/A"))
        metric("Page Views", w.get("page_views", "N/A"))
        metric("Bounce Rate", w.get("bounce_rate", "N/A"))
        metric("Engagement", w.get("engagement_rate", "N/A"))

    # Search metrics
    if data.get("search"):
        subheader("Search Performance (SEO)")
        s = data["search"]
        metric("Clicks", s.get("clicks", "N/A"))
        metric("Impressions", s.get("impressions", "N/A"))
        metric("Avg CTR", s.get("avg_ctr", "N/A"))

    # Business metrics
    if data.get("business"):
        subheader("Business Metrics")
        b = data["business"]
        metric("Total Leads", b.get("total_leads", "N/A"))
        metric("Total Calls", b.get("total_calls", "N/A"))
        metric("Total Proposals", b.get("total_proposals", "N/A"))

        if b.get("leads_by_status"):
            print()
            print(c("dim", "  Leads by Status:"))
            for status, count in b["leads_by_status"].items():
                print(f"    {status}: {count}")

    # Funnel
    if data.get("funnel") and data["funnel"].get("stages"):
        subheader("Conversion Funnel")
        funnel(data["funnel"]["stages"])
        print(f"  {c('bold', 'Overall Conversion:')} {c('green', data['funnel'].get('overall_conversion', 'N/A'))}")


def cmd_ga(args):
    """Google Analytics commands"""
    from .google_analytics import GoogleAnalytics

    ga = GoogleAnalytics()
    subcmd = args.subcommand or "overview"

    if subcmd == "overview":
        header("Google Analytics Overview", "📈")
        data = ga.get_overview(args.start, args.end)
        for key, val in data.items():
            metric(key.replace("_", " ").title(), val)

    elif subcmd == "pages":
        header("Top Pages", "📄")
        data = ga.get_top_pages(args.start, args.end, args.limit)
        table(data, ["page", "page_views", "users", "bounce_rate"])

    elif subcmd == "sources":
        header("Traffic Sources", "🔗")
        data = ga.get_traffic_sources(args.start, args.end, args.limit)
        table(data, ["source", "medium", "sessions", "users", "engagement_rate"])

    elif subcmd == "channels":
        header("Channel Breakdown", "📊")
        data = ga.get_channel_grouping(args.start, args.end)
        table(data, ["channel", "sessions", "users", "engagement_rate"])

    elif subcmd == "events":
        header("Events", "🎯")
        data = ga.get_events(args.start, args.end, args.limit)
        table(data, ["event", "count", "users"])

    elif subcmd == "users":
        header("User Demographics", "👥")
        data = ga.get_user_demographics(args.start, args.end)

        subheader("By Country")
        table(data.get("countries", []))

        subheader("By Device")
        table(data.get("devices", []))

        subheader("By Browser")
        table(data.get("browsers", []))

    elif subcmd == "daily":
        header("Daily Metrics", "📅")
        data = ga.get_daily_metrics(args.start, args.end)
        table(data[-14:], ["date", "active_users", "sessions", "page_views"])

    elif subcmd == "realtime":
        header("Realtime", "⚡")
        data = ga.get_realtime()
        metric("Active Users Now", data.get("total_active", 0))
        if data.get("by_country"):
            subheader("By Country")
            table(data["by_country"])

    else:
        print(f"""
Google Analytics Commands:
  ga overview    - Overall metrics summary
  ga pages       - Top pages by views
  ga sources     - Traffic sources breakdown
  ga channels    - Channel grouping
  ga events      - Event tracking data
  ga users       - User demographics
  ga daily       - Daily metrics trend
  ga realtime    - Current active users
        """)


def cmd_gsc(args):
    """Search Console commands"""
    from .search_console import SearchConsole

    gsc = SearchConsole()
    subcmd = args.subcommand or "queries"

    if subcmd == "queries":
        header("Top Search Queries", "🔍")
        data = gsc.get_top_queries(limit=args.limit)
        table(data, ["query", "clicks", "impressions", "ctr", "position"])

    elif subcmd == "pages":
        header("Top Pages (Search)", "📄")
        data = gsc.get_top_pages(limit=args.limit)
        table(data, ["page", "clicks", "impressions", "ctr", "position"])

    elif subcmd == "daily":
        header("Daily Search Performance", "📅")
        data = gsc.get_daily_performance()
        table(data[-14:], ["date", "clicks", "impressions", "ctr", "position"])

    elif subcmd == "devices":
        header("Device Breakdown", "📱")
        data = gsc.get_device_breakdown()
        table(data)

    elif subcmd == "countries":
        header("Country Breakdown", "🌍")
        data = gsc.get_country_breakdown(limit=args.limit)
        table(data, ["country", "clicks", "impressions", "ctr"])

    elif subcmd == "opportunities":
        header("SEO Opportunities", "🎯")
        data = gsc.get_keyword_opportunities()

        subheader("High Impression Keywords (Improvable Position)")
        table(data.get("opportunities", [])[:15], ["query", "impressions", "position"])

        if data.get("quick_wins"):
            subheader("Quick Wins (Good Position, Low CTR)")
            table(data["quick_wins"][:10], ["query", "ctr", "impressions"])

    elif subcmd == "branded":
        header("Branded vs Non-Branded", "🏷️")
        brand_terms = args.brand.split(",") if args.brand else None
        data = gsc.get_branded_vs_non_branded(brand_terms)

        subheader("Branded Traffic")
        b = data.get("branded", {})
        metric("Queries", b.get("queries", 0))
        metric("Clicks", b.get("clicks", 0))
        metric("Impressions", b.get("impressions", 0))

        subheader("Non-Branded Traffic")
        nb = data.get("non_branded", {})
        metric("Queries", nb.get("queries", 0))
        metric("Clicks", nb.get("clicks", 0))
        metric("Impressions", nb.get("impressions", 0))

        if nb.get("top_queries"):
            subheader("Top Non-Branded Queries")
            table(nb["top_queries"], ["query", "clicks"])

    else:
        print(f"""
Google Search Console Commands:
  gsc queries       - Top search queries
  gsc pages         - Top pages in search
  gsc daily         - Daily search performance
  gsc devices       - Performance by device
  gsc countries     - Performance by country
  gsc opportunities - SEO improvement opportunities
  gsc branded       - Branded vs non-branded traffic
        """)


def cmd_db(args):
    """Database commands"""
    from .supabase_analytics import SupabaseAnalytics

    db = SupabaseAnalytics()
    subcmd = args.subcommand or "stats"

    if subcmd == "stats":
        header("Database Statistics", "🗄️")
        data = db.get_table_counts()
        table([{"table": k, "count": v} for k, v in data.items()], ["table", "count"])

    elif subcmd == "users":
        header("Users", "👥")
        data = db.get_users(limit=args.limit)
        table([{
            "id": u.get("id", "")[:8] + "...",
            "email": u.get("email", "N/A"),
            "created": u.get("created_at", "")[:10] if u.get("created_at") else "N/A"
        } for u in data], ["id", "email", "created"])

    elif subcmd == "leads":
        header("Recent Leads", "📋")
        data = db.get_leads(limit=args.limit, status=args.status)
        table([{
            "name": l.get("name") or l.get("first_name", "N/A"),
            "email": l.get("email", "N/A"),
            "status": l.get("status", "N/A"),
            "business": l.get("businesses", {}).get("name", "N/A") if l.get("businesses") else "N/A",
            "created": l.get("created_at", "")[:10] if l.get("created_at") else "N/A"
        } for l in data], ["name", "email", "status", "business", "created"])

    elif subcmd == "calls":
        header("Recent Calls", "📞")
        data = db.get_calls(limit=args.limit)
        table([{
            "id": c.get("id", "")[:8] + "...",
            "status": c.get("status", "N/A"),
            "duration": c.get("duration", "N/A"),
            "created": c.get("created_at", "")[:10] if c.get("created_at") else "N/A"
        } for c in data], ["id", "status", "duration", "created"])

    elif subcmd == "agents":
        header("Agents", "🤖")
        data = db.get_agents()
        table([{
            "name": a.get("name", "N/A"),
            "type": a.get("type", "N/A"),
            "active": "Yes" if a.get("is_active") else "No"
        } for a in data], ["name", "type", "active"])

    elif subcmd == "funnel":
        header("Conversion Funnel", "📊")
        data = db.get_conversion_funnel()
        funnel(data.get("stages", []))
        print(f"  Overall Conversion: {data.get('overall_conversion', 'N/A')}")

    elif subcmd == "trend":
        trend_type = args.type or "leads"
        header(f"{trend_type.title()} Trend", "📈")

        if trend_type == "leads":
            data = db.get_daily_lead_trend(args.days)
            table(data[-14:], ["date", "leads"])
        else:
            data = db.get_daily_call_trend(args.days)
            table(data[-14:], ["date", "calls"])

    elif subcmd == "performance":
        header("Agent Performance", "🎯")
        data = db.get_agent_performance()
        table(data, ["name", "total_calls", "completed_calls", "completion_rate", "avg_duration"])

    else:
        print(f"""
Database Commands:
  db stats       - Table counts
  db users       - List users
  db leads       - Recent leads
  db calls       - Recent calls
  db agents      - List agents
  db funnel      - Conversion funnel
  db trend       - Lead/call trends
  db performance - Agent performance
        """)


def cmd_report(args):
    """Generate reports"""
    from .dashboard import Dashboard

    dashboard = Dashboard()
    report_type = args.subcommand or "full"

    if report_type == "traffic":
        header("Traffic Report", "🚦")
        data = dashboard.get_traffic_report(args.start, args.end)

        if data.get("channels"):
            subheader("Channel Breakdown")
            table(data["channels"], ["channel", "sessions", "users", "engagement_rate"])

        if data.get("sources"):
            subheader("Top Traffic Sources")
            table(data["sources"][:15], ["source", "medium", "sessions", "users"])

    elif report_type == "seo":
        header("SEO Report", "🔍")
        data = dashboard.get_seo_report()

        if data.get("top_queries"):
            subheader("Top Search Queries")
            table(data["top_queries"][:20], ["query", "clicks", "impressions", "ctr", "position"])

        if data.get("opportunities"):
            subheader("Keyword Opportunities")
            table(data["opportunities"][:10], ["query", "impressions", "position"])

        if data.get("quick_wins"):
            subheader("Quick Wins")
            table(data["quick_wins"][:10], ["query", "ctr", "impressions"])

    elif report_type == "content":
        header("Content Report", "📄")
        data = dashboard.get_content_report(args.start, args.end)

        if data.get("ga_pages"):
            subheader("Top Content (GA)")
            table(data["ga_pages"][:15], ["page", "page_views", "users", "bounce_rate"])

        if data.get("landing_pages"):
            subheader("Landing Pages")
            table(data["landing_pages"][:10], ["landing_page", "sessions", "bounce_rate"])

    elif report_type == "leads":
        header("Leads & Sales Report", "💼")
        data = dashboard.get_leads_sales_report(30)

        if data.get("funnel") and data["funnel"].get("stages"):
            subheader("Conversion Funnel")
            funnel(data["funnel"]["stages"])

        if data.get("leads_by_status"):
            subheader("Leads by Status")
            bar_chart([{"status": k, "count": v} for k, v in data["leads_by_status"].items()], "status", "count")

        if data.get("recent_leads"):
            subheader("Recent Leads")
            table([{
                "name": l.get("name") or l.get("first_name", "N/A"),
                "email": l.get("email", "N/A"),
                "status": l.get("status", "N/A"),
            } for l in data["recent_leads"][:10]], ["name", "email", "status"])

    else:
        # Full report
        print("\nGenerating full report...")
        cmd_summary(args)


def cmd_help(args):
    """Show help"""
    print(f"""
{c('cyan', '=' * 60)}
{c('bold', ' CMO Analytics System')}
{c('cyan', '=' * 60)}

{c('yellow', 'Dashboard Commands:')}
  summary              Executive summary of all metrics
  report [type]        Generate reports (traffic|seo|content|leads|full)

{c('yellow', 'Google Analytics:')}
  ga overview          Overall metrics summary
  ga pages             Top pages by views
  ga sources           Traffic sources breakdown
  ga channels          Channel grouping
  ga events            Event tracking data
  ga users             User demographics
  ga daily             Daily metrics trend
  ga realtime          Current active users

{c('yellow', 'Google Search Console:')}
  gsc queries          Top search queries
  gsc pages            Top pages in search
  gsc daily            Daily search performance
  gsc devices          Performance by device
  gsc countries        Performance by country
  gsc opportunities    SEO improvement opportunities
  gsc branded          Branded vs non-branded traffic

{c('yellow', 'Database (Supabase):')}
  db stats             Table counts
  db users             List users
  db leads             Recent leads
  db calls             Recent calls
  db agents            List agents
  db funnel            Conversion funnel
  db trend             Lead/call trends
  db performance       Agent performance

{c('yellow', 'Global Options:')}
  --start DATE         Start date (e.g., 2024-01-01 or 30daysAgo)
  --end DATE           End date (default: today)
  --limit N            Limit results
  --status STATUS      Filter by status (for leads)
  --type TYPE          Type for trend (leads|calls)
  --days N             Days for trends (default: 30)
  --brand TERMS        Comma-separated brand terms

{c('dim', 'Examples:')}
  python -m analytics.cli summary
  python -m analytics.cli ga pages --limit 20
  python -m analytics.cli gsc opportunities
  python -m analytics.cli db leads --status qualified
  python -m analytics.cli report seo
    """)


def main():
    parser = argparse.ArgumentParser(description="CMO Analytics System")
    parser.add_argument("command", nargs="?", default="help", help="Command to run")
    parser.add_argument("subcommand", nargs="?", help="Subcommand")
    parser.add_argument("--start", default="30daysAgo", help="Start date")
    parser.add_argument("--end", default="today", help="End date")
    parser.add_argument("--limit", type=int, default=30, help="Result limit")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--type", help="Type (leads|calls)")
    parser.add_argument("--days", type=int, default=30, help="Days for trends")
    parser.add_argument("--brand", help="Brand terms (comma-separated)")

    args = parser.parse_args()

    commands = {
        "help": cmd_help,
        "summary": cmd_summary,
        "ga": cmd_ga,
        "gsc": cmd_gsc,
        "db": cmd_db,
        "report": cmd_report,
    }

    try:
        if args.command in commands:
            commands[args.command](args)
        else:
            print(f"Unknown command: {args.command}")
            print("Run 'python -m analytics.cli help' for available commands")
    except ImportError as e:
        print(f"\nMissing dependency: {e}")
        print("\nInstall required packages:")
        print("  pip install google-analytics-data google-api-python-client google-auth supabase")
    except Exception as e:
        print(f"\nError: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

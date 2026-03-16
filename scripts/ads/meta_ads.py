#!/usr/bin/env python3
"""Meta/Facebook Ads CLI - campaigns, spend, performance, ad sets."""
import sys, os, json

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")
from analytics.facebook_ads import FacebookAds

fb = FacebookAds(
    access_token=os.getenv("META_ACCESS_TOKEN"),
    ad_account_id=os.getenv("META_AD_ACCOUNT_ID"),
)

def cmd_campaigns(args):
    """All campaigns with status and spend."""
    return fb.get_campaigns()

def cmd_spend(args):
    """Spend summary — today, last 7d, last 30d."""
    days = int(args.get("days", 30))
    return fb.get_spend_summary(days=days)

def cmd_adsets(args):
    """Ad sets for a campaign."""
    campaign_id = args.get("campaign_id")
    if not campaign_id:
        return {"error": "Provide --campaign_id=<id>"}
    return fb.get_ad_sets(campaign_id=campaign_id)

def cmd_performance(args):
    """Campaign performance — impressions, CTR, CPL, ROAS."""
    days = int(args.get("days", 7))
    campaign_id = args.get("campaign_id")
    return fb.get_campaign_insights(campaign_id=campaign_id, days=days)

def cmd_dashboard(args):
    """Full Meta ads dashboard."""
    days = int(args.get("days", 7))
    try:
        campaigns = fb.get_campaigns()
        spend = fb.get_spend_summary(days=days)
        return {"campaigns": campaigns, "spend_summary": spend}
    except Exception as e:
        return {"error": str(e)}

def cmd_flag(args):
    """Flag underperforming ads."""
    import subprocess
    days = args.get("days", 7)
    r = subprocess.run([sys.executable, "/opt/cmo-analytics/scripts/ad_flag.py", f"--days={days}"],
                       capture_output=False)
    return {}

def cmd_loop(args):
    """Full ad iteration loop: flag → generate → render → queue → Discord."""
    import subprocess
    site = args.get("site", "kaicalls")
    days = args.get("days", 7)
    channel = args.get("channel", "")
    dry = "--dry-run" if args.get("dry_run") else ""
    cmd = [sys.executable, "/opt/cmo-analytics/scripts/ad_loop.py",
           f"--site={site}", f"--days={days}"]
    if channel: cmd.append(f"--channel={channel}")
    if dry: cmd.append(dry)
    subprocess.run(cmd, capture_output=False)
    return {}

COMMANDS = {
    "campaigns": cmd_campaigns,
    "spend": cmd_spend,
    "adsets": cmd_adsets,
    "performance": cmd_performance,
    "dashboard": cmd_dashboard,
    "flag": cmd_flag,
    "loop": cmd_loop,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dashboard"
    args = {}
    for arg in sys.argv[2:]:
        if arg.startswith("--") and "=" in arg:
            k, v = arg[2:].split("=", 1)
            args[k] = v

    if cmd not in COMMANDS:
        print(json.dumps({"error": f"Unknown command: {cmd}. Available: {list(COMMANDS)}"}))
        sys.exit(1)

    try:
        result = COMMANDS[cmd](args)
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

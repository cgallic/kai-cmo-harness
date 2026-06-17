#!/usr/bin/env python3
"""OpenAI Ads CLI — ad_account, campaigns, ad groups, ads, insights.

Auth: Bearer $OPENAI_ADS_API_KEY
Base: https://api.ads.openai.com/v1
Budgets/bids are in micros (1,000,000 = $1.00).
"""
import sys, os, json
import requests

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

TOKEN = os.getenv("OPENAI_ADS_API_KEY")
BASE = "https://api.ads.openai.com/v1"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}


def _get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params or {})
    r.raise_for_status()
    return r.json()


def cmd_account(args):
    """Ad account summary."""
    return _get("/ad_account")


def cmd_campaigns(args):
    """List all campaigns."""
    return _get("/campaigns", params={"limit": int(args.get("limit", 100))})


def cmd_campaign(args):
    """Get one campaign by id."""
    cid = args.get("campaign_id")
    if not cid:
        return {"error": "Provide --campaign_id=<id>"}
    return _get(f"/campaigns/{cid}")


def cmd_adgroups(args):
    """Ad groups for a campaign."""
    cid = args.get("campaign_id")
    if not cid:
        return {"error": "Provide --campaign_id=<id>"}
    return _get("/ad_groups", params={"campaign_id": cid, "limit": int(args.get("limit", 100))})


def cmd_ads(args):
    """Ads in an ad group."""
    gid = args.get("ad_group_id")
    if not gid:
        return {"error": "Provide --ad_group_id=<id>"}
    return _get("/ads", params={"ad_group_id": gid, "limit": int(args.get("limit", 100))})


def _insights_path(args):
    if args.get("ad_id"):
        return f"/ads/{args['ad_id']}/insights"
    if args.get("ad_group_id"):
        return f"/ad_groups/{args['ad_group_id']}/insights"
    if args.get("campaign_id"):
        return f"/campaigns/{args['campaign_id']}/insights"
    return "/ad_account/insights"


def cmd_insights(args):
    """Performance insights — scope by --ad_id / --ad_group_id / --campaign_id or omit for account."""
    params = {
        "time_granularity": args.get("granularity", "daily"),
        "fields": args.get("fields", "impressions,clicks,spend,ctr,cpc,cpm"),
        "limit": int(args.get("limit", 100)),
    }
    if args.get("aggregation_level"):
        params["aggregation_level"] = args["aggregation_level"]
    if args.get("time_ranges"):
        params["time_ranges"] = args["time_ranges"]
    return _get(_insights_path(args), params=params)


def cmd_spend(args):
    """Spend rollup for the ad account over last N days (default 30)."""
    days = int(args.get("days", 30))
    params = {
        "time_granularity": "none",
        "fields": "spend,impressions,clicks,ctr,cpc",
        "time_ranges": json.dumps([{"relative": f"last_{days}_days"}]),
    }
    return _get("/ad_account/insights", params=params)


def cmd_dashboard(args):
    """Full read-only snapshot: account + campaigns + recent spend."""
    days = int(args.get("days", 7))
    try:
        return {
            "account": _get("/ad_account"),
            "campaigns": _get("/campaigns", params={"limit": 50}),
            "spend": _get("/ad_account/insights", params={
                "time_granularity": "none",
                "fields": "spend,impressions,clicks,ctr,cpc",
                "time_ranges": json.dumps([{"relative": f"last_{days}_days"}]),
            }),
        }
    except Exception as e:
        return {"error": str(e)}


COMMANDS = {
    "account": cmd_account,
    "campaigns": cmd_campaigns,
    "campaign": cmd_campaign,
    "adgroups": cmd_adgroups,
    "ads": cmd_ads,
    "insights": cmd_insights,
    "spend": cmd_spend,
    "dashboard": cmd_dashboard,
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
    except requests.HTTPError as e:
        print(json.dumps({"error": str(e), "body": e.response.text if e.response is not None else None}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

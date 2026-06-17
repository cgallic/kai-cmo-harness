#!/usr/bin/env python3
"""
OpenAI Ads — Create, upload, and publish ads via the Advertiser API.

Auth: Bearer $OPENAI_ADS_API_KEY
Base: https://api.ads.openai.com/v1
Budgets/bids are micros (1,000,000 = $1.00). Helpers below accept dollars
via --budget-usd / --bid-usd flags and convert for you.

Usage:
  python3 openai_ads_create.py upload-image --file=/path/to/img.png
  python3 openai_ads_create.py upload-url --image-url=https://...
  python3 openai_ads_create.py create-campaign --name="..." --budget-usd=50 [--status=paused]
  python3 openai_ads_create.py create-adgroup --campaign-id=X --name="..." --bid-usd=2.00 \
      [--context-hints="kaicalls,ai receptionist"] [--status=paused]
  python3 openai_ads_create.py create-ad --ad-group-id=Y --name="..." \
      --headline="..." --description="..." --link=https://... --file-id=file_xxx
  python3 openai_ads_create.py activate --type=campaign|adgroup|ad --id=X
  python3 openai_ads_create.py pause    --type=campaign|adgroup|ad --id=X
  python3 openai_ads_create.py archive  --type=campaign|adgroup|ad --id=X
"""

import argparse, json, os, sys
import requests

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

TOKEN = os.getenv("OPENAI_ADS_API_KEY")
BASE = "https://api.ads.openai.com/v1"


def _headers(extra=None):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    if extra:
        h.update(extra)
    return h


def _post_json(path, body):
    r = requests.post(f"{BASE}{path}", headers=_headers({"Content-Type": "application/json"}), json=body)
    r.raise_for_status()
    return r.json()


def _post_multipart(path, files, data=None):
    r = requests.post(f"{BASE}{path}", headers=_headers(), files=files, data=data or {})
    r.raise_for_status()
    return r.json()


def _to_micros(usd):
    return int(round(float(usd) * 1_000_000))


_TYPE_PATHS = {"campaign": "campaigns", "adgroup": "ad_groups", "ad": "ads"}


def cmd_upload_image(args):
    """Multipart upload — returns {file_id}."""
    if not args.file or not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    with open(args.file, "rb") as f:
        result = _post_multipart("/upload", files={"file": (os.path.basename(args.file), f)})

    print(json.dumps(result, indent=2))
    return result.get("file_id")


def cmd_upload_url(args):
    """Upload by remote URL — returns {file_id}."""
    if not args.image_url:
        print("Required: --image-url")
        sys.exit(1)
    result = _post_json("/upload", {"image_url": args.image_url})
    print(json.dumps(result, indent=2))
    return result.get("file_id")


def cmd_create_campaign(args):
    if not args.name or args.budget_usd is None:
        print("Required: --name --budget-usd")
        sys.exit(1)
    body = {
        "name": args.name,
        "status": args.status or "paused",
        "budget": {"lifetime_spend_limit_micros": _to_micros(args.budget_usd)},
    }
    result = _post_json("/campaigns", body)
    print(json.dumps(result, indent=2))
    return result.get("id")


def cmd_create_adgroup(args):
    if not args.campaign_id or not args.name or args.bid_usd is None:
        print("Required: --campaign-id --name --bid-usd")
        sys.exit(1)
    body = {
        "campaign_id": args.campaign_id,
        "name": args.name,
        "status": args.status or "paused",
        "bidding_config": {"bid_micros": _to_micros(args.bid_usd)},
    }
    if args.context_hints:
        body["context_hints"] = [h.strip() for h in args.context_hints.split(",") if h.strip()]
    result = _post_json("/ad_groups", body)
    print(json.dumps(result, indent=2))
    return result.get("id")


def cmd_create_ad(args):
    if not (args.ad_group_id and args.name and args.headline and args.description and args.link and args.file_id):
        print("Required: --ad-group-id --name --headline --description --link --file-id")
        sys.exit(1)
    if not (3 <= len(args.headline) <= 50):
        print(f"Headline must be 3-50 chars (got {len(args.headline)}).")
        sys.exit(1)
    if len(args.description) > 100:
        print(f"Description must be ≤100 chars (got {len(args.description)}).")
        sys.exit(1)

    body = {
        "ad_group_id": args.ad_group_id,
        "name": args.name,
        "status": args.status or "paused",
        "creative": {
            "type": "chat_card",
            "title": args.headline,
            "body": args.description,
            "target_url": args.link,
            "file_id": args.file_id,
        },
    }
    result = _post_json("/ads", body)
    print(json.dumps(result, indent=2))
    return result.get("id")


def _state_action(args, action):
    if not args.type or args.type not in _TYPE_PATHS:
        print("Required: --type=campaign|adgroup|ad")
        sys.exit(1)
    if not args.id:
        print("Required: --id")
        sys.exit(1)
    path = f"/{_TYPE_PATHS[args.type]}/{args.id}/{action}"
    result = _post_json(path, {})
    print(json.dumps(result, indent=2))
    return result


def cmd_activate(args): return _state_action(args, "activate")
def cmd_pause(args):    return _state_action(args, "pause")
def cmd_archive(args):  return _state_action(args, "archive")


COMMANDS = {
    "upload-image":   cmd_upload_image,
    "upload-url":     cmd_upload_url,
    "create-campaign": cmd_create_campaign,
    "create-adgroup":  cmd_create_adgroup,
    "create-ad":      cmd_create_ad,
    "activate":       cmd_activate,
    "pause":          cmd_pause,
    "archive":        cmd_archive,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenAI Ads create/manage")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--file")
    parser.add_argument("--image-url")
    parser.add_argument("--name")
    parser.add_argument("--status", help="paused|active (defaults to paused)")
    parser.add_argument("--budget-usd", type=float)
    parser.add_argument("--bid-usd", type=float)
    parser.add_argument("--campaign-id")
    parser.add_argument("--ad-group-id")
    parser.add_argument("--context-hints", help="comma-separated keywords/audiences")
    parser.add_argument("--headline")
    parser.add_argument("--description")
    parser.add_argument("--link")
    parser.add_argument("--file-id")
    parser.add_argument("--type", choices=list(_TYPE_PATHS))
    parser.add_argument("--id")
    args = parser.parse_args()

    try:
        COMMANDS[args.command](args)
    except requests.HTTPError as e:
        body = e.response.text if e.response is not None else ""
        print(json.dumps({"error": str(e), "body": body}, indent=2))
        sys.exit(1)

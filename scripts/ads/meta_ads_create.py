#!/usr/bin/env python3
"""
Meta Ads — Create, upload, and publish ads via Marketing API.

Usage:
  python3 meta_ads_create.py upload-image --file=/path/to/img.png
  python3 meta_ads_create.py upload-video --file=/path/to/vid.mp4
  python3 meta_ads_create.py create-creative --name="Ad Name" --image-hash=X --headline="..." --description="..." --link=https://...
  python3 meta_ads_create.py create-ad --creative-id=X --campaign-id=Y --adset-id=Z --name="Ad Name"
  python3 meta_ads_create.py publish --ad-id=X
  python3 meta_ads_create.py pause --ad-id=X
  python3 meta_ads_create.py list-adsets --campaign-id=X
"""

import argparse
import json
import os
import sys
import requests
sys.path.insert(0, "/opt/cmo-analytics")

from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

TOKEN = os.getenv("META_ACCESS_TOKEN")
AD_ACCOUNT = os.getenv("META_AD_ACCOUNT_ID")  # format: act_XXXXXXXXX
API_VERSION = os.getenv("META_API_VERSION", "v18.0")
BASE = f"https://graph.facebook.com/{API_VERSION}"


def _get(endpoint, params=None):
    r = requests.get(f"{BASE}/{endpoint}", params={**(params or {}), "access_token": TOKEN})
    r.raise_for_status()
    return r.json()


def _post(endpoint, data=None, files=None):
    if files:
        r = requests.post(f"{BASE}/{endpoint}", data={**(data or {}), "access_token": TOKEN}, files=files)
    else:
        r = requests.post(f"{BASE}/{endpoint}", json={**(data or {}), "access_token": TOKEN})
    r.raise_for_status()
    return r.json()


def cmd_upload_image(args):
    """Upload image to ad account, returns image_hash."""
    if not args.file or not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    with open(args.file, "rb") as f:
        result = _post(f"{AD_ACCOUNT}/adimages", files={"filename": f})

    images = result.get("images", {})
    for fname, data in images.items():
        print(f"Uploaded: {fname}")
        print(f"Hash: {data['hash']}")
        print(f"URL: {data.get('url', 'N/A')}")
        return data["hash"]


def cmd_upload_video(args):
    """Upload video to ad account, returns video_id."""
    if not args.file or not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)

    with open(args.file, "rb") as f:
        result = _post(f"{AD_ACCOUNT}/advideos",
                      data={"name": os.path.basename(args.file)},
                      files={"source": f})

    video_id = result.get("id")
    print(f"Video ID: {video_id}")
    return video_id


def cmd_create_creative(args):
    """Create AdCreative from image hash or video ID."""
    if not args.name or not args.headline or not args.description or not args.link:
        print("Required: --name --headline --description --link")
        sys.exit(1)

    object_story_spec = {
        "page_id": os.getenv("META_PAGE_ID"),
        "link_data": {
            "message": args.description,
            "link": args.link,
            "name": args.headline,
            "call_to_action": {
                "type": args.cta or "LEARN_MORE",
                "value": {"link": args.link}
            }
        }
    }

    if args.image_hash:
        object_story_spec["link_data"]["image_hash"] = args.image_hash
    elif args.video_id:
        object_story_spec["link_data"]["video_id"] = args.video_id
        del object_story_spec["link_data"]["image_hash"]

    result = _post(f"{AD_ACCOUNT}/adcreatives", data={
        "name": args.name,
        "object_story_spec": json.dumps(object_story_spec),
    })

    creative_id = result.get("id")
    print(f"Creative ID: {creative_id}")
    return creative_id


def cmd_create_ad(args):
    """Create a PAUSED ad in an ad set with a creative."""
    if not args.creative_id or not args.adset_id or not args.name:
        print("Required: --creative-id --adset-id --name")
        sys.exit(1)

    result = _post(f"{AD_ACCOUNT}/ads", data={
        "name": args.name,
        "adset_id": args.adset_id,
        "creative": json.dumps({"creative_id": args.creative_id}),
        "status": "PAUSED",
    })

    ad_id = result.get("id")
    print(f"Ad ID: {ad_id}  (status: PAUSED — approve to publish)")
    return ad_id


def cmd_publish(args):
    """Set ad status to ACTIVE (publish)."""
    if not args.ad_id:
        print("Required: --ad-id")
        sys.exit(1)

    result = _post(f"{args.ad_id}", data={"status": "ACTIVE"})
    print(f"Ad {args.ad_id} → ACTIVE")
    return result


def cmd_pause(args):
    """Pause an active ad."""
    if not args.ad_id:
        print("Required: --ad-id")
        sys.exit(1)

    result = _post(f"{args.ad_id}", data={"status": "PAUSED"})
    print(f"Ad {args.ad_id} → PAUSED")
    return result


def cmd_list_adsets(args):
    """List ad sets for a campaign."""
    if not args.campaign_id:
        print("Required: --campaign-id")
        sys.exit(1)

    result = _get(f"{args.campaign_id}/adsets",
                 params={"fields": "id,name,status,daily_budget,lifetime_budget"})
    adsets = result.get("data", [])
    print(f"\nAd Sets for campaign {args.campaign_id}:\n")
    for a in adsets:
        budget = a.get("daily_budget") or a.get("lifetime_budget") or "N/A"
        print(f"  {a['id']}  {a['name']}  [{a['status']}]  budget: {budget}")
    return adsets


COMMANDS = {
    "upload-image": cmd_upload_image,
    "upload-video": cmd_upload_video,
    "create-creative": cmd_create_creative,
    "create-ad": cmd_create_ad,
    "publish": cmd_publish,
    "pause": cmd_pause,
    "list-adsets": cmd_list_adsets,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta Ads create/manage")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--file")
    parser.add_argument("--name")
    parser.add_argument("--headline")
    parser.add_argument("--description")
    parser.add_argument("--link")
    parser.add_argument("--cta", default="LEARN_MORE")
    parser.add_argument("--image-hash")
    parser.add_argument("--video-id")
    parser.add_argument("--creative-id")
    parser.add_argument("--adset-id")
    parser.add_argument("--campaign-id")
    parser.add_argument("--ad-id")
    args = parser.parse_args()
    COMMANDS[args.command](args)

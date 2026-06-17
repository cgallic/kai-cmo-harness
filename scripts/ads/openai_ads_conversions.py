#!/usr/bin/env python3
"""
OpenAI Ads — Conversions API (server-side events).

Different host + different key than the Advertiser API:
  Host:   https://bzr.openai.com/v1/events?pid=<PIXEL-ID>
  Auth:   Bearer $OPENAI_ADS_CONVERSIONS_TOKEN
  Pixel:  $OPENAI_ADS_PIXEL_ID
  Dedup:  send the *same* event id from pixel + server.

Usage:
  python3 openai_ads_conversions.py send \
      --event-id=signup_42 --type=registration_completed --amount=0 [--currency=USD] \
      [--source-url=https://kaicalls.com/signup/confirm]

  python3 openai_ads_conversions.py validate ... (sets validate_only=true)

  python3 openai_ads_conversions.py batch --file=events.json  # array of event objects

Event shape (per docs):
  { "id": "...", "type": "...", "timestamp_ms": 1773892800000,
    "source_url": "...", "action_source": "web",
    "data": {"type": "contents", "amount": 2599, "currency": "USD"} }
"""

import argparse, json, os, sys, time
import requests

sys.path.insert(0, "/opt/cmo-analytics")
from dotenv import load_dotenv
load_dotenv("/opt/cmo-analytics/.env")

TOKEN = os.getenv("OPENAI_ADS_CONVERSIONS_TOKEN") or os.getenv("OPENAI_ADS_CONVERSION_KEY")
PIXEL = os.getenv("OPENAI_ADS_PIXEL_ID")
ENDPOINT = "https://bzr.openai.com/v1/events"


def _send(events, validate_only=False):
    if not TOKEN:
        return {"error": "OPENAI_ADS_CONVERSIONS_TOKEN not set"}
    if not PIXEL:
        return {"error": "OPENAI_ADS_PIXEL_ID not set"}

    body = {"validate_only": bool(validate_only), "events": events}
    r = requests.post(
        ENDPOINT,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        params={"pid": PIXEL},
        json=body,
    )
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        return {"error": str(e), "body": r.text}
    return r.json()


def _build_event(args):
    return {
        "id": args.event_id,
        "type": args.type,
        "timestamp_ms": args.timestamp_ms or int(time.time() * 1000),
        "source_url": args.source_url or "",
        "action_source": args.action_source or "web",
        "data": {
            "type": args.data_type or "contents",
            "amount": int(args.amount or 0),
            "currency": (args.currency or "USD").upper(),
        },
    }


def cmd_send(args):
    if not (args.event_id and args.type):
        print("Required: --event-id --type")
        sys.exit(1)
    return _send([_build_event(args)], validate_only=False)


def cmd_validate(args):
    if not (args.event_id and args.type):
        print("Required: --event-id --type")
        sys.exit(1)
    return _send([_build_event(args)], validate_only=True)


def cmd_batch(args):
    if not args.file or not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        sys.exit(1)
    with open(args.file) as fh:
        events = json.load(fh)
    if not isinstance(events, list):
        print("Batch file must be a JSON array of event objects.")
        sys.exit(1)
    if len(events) > 1000:
        print(f"Batch capped at 1000 events per call (got {len(events)}).")
        sys.exit(1)
    return _send(events, validate_only=args.validate_only)


COMMANDS = {"send": cmd_send, "validate": cmd_validate, "batch": cmd_batch}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenAI Ads Conversions API")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--event-id")
    parser.add_argument("--type", help="e.g. registration_completed, order_created, lead")
    parser.add_argument("--timestamp-ms", type=int, dest="timestamp_ms")
    parser.add_argument("--source-url")
    parser.add_argument("--action-source", default="web")
    parser.add_argument("--data-type", default="contents")
    parser.add_argument("--amount", type=int, default=0, help="minor units (cents)")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--file", help="batch JSON file (array of events)")
    parser.add_argument("--validate-only", action="store_true", dest="validate_only")
    args = parser.parse_args()

    result = COMMANDS[args.command](args)
    print(json.dumps(result, indent=2, default=str))

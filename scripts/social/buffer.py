#!/usr/bin/env python3
"""
Kai CMO Harness — Buffer Publisher
=====================================
Schedule posts via Buffer API (covers LinkedIn, Twitter, Instagram, Facebook, etc.).

Environment:
  BUFFER_ACCESS_TOKEN=your-access-token

Setup: https://buffer.com/developers → Create app → Get access token
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

BUFFER_API = "https://api.bufferapp.com/1"


def _get_token() -> str:
    token = os.environ.get("BUFFER_ACCESS_TOKEN", "")
    if not token:
        raise ValueError("Missing BUFFER_ACCESS_TOKEN")
    return token


def _get_profiles(token: str) -> list[dict]:
    """List connected Buffer profiles."""
    resp = requests.get(
        f"{BUFFER_API}/profiles.json",
        params={"access_token": token},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def post(
    content: str = "",
    platforms: list[str] | None = None,
    schedule_time: str = "",
    link: str = "",
    image_url: str = "",
    **_kwargs,
) -> dict:
    """
    Create/schedule a Buffer post.

    Args:
        content: Post text
        platforms: Filter profiles by service name (e.g. ["linkedin", "twitter"])
        schedule_time: ISO datetime for scheduling (empty = add to queue)
        link: URL to share
        image_url: Image to attach
    """
    try:
        token = _get_token()
    except ValueError as e:
        return {"success": False, "platform": "buffer", "message": str(e)}

    try:
        profiles = _get_profiles(token)
    except Exception as e:
        return {"success": False, "platform": "buffer", "message": f"Cannot fetch profiles: {e}"}

    # Filter profiles by platform
    if platforms:
        platform_set = {p.lower() for p in platforms}
        profiles = [p for p in profiles if p.get("service", "").lower() in platform_set]

    if not profiles:
        return {
            "success": False,
            "platform": "buffer",
            "message": f"No Buffer profiles found for: {platforms or 'any'}. Connect accounts at buffer.com.",
        }

    profile_ids = [p["id"] for p in profiles]

    # Build post data
    post_data: dict = {
        "access_token": token,
        "text": content,
        "profile_ids[]": profile_ids,
        "now": not schedule_time,
    }

    if schedule_time:
        post_data["scheduled_at"] = schedule_time
    if link:
        post_data["media[link]"] = link
    if image_url:
        post_data["media[photo]"] = image_url

    try:
        resp = requests.post(
            f"{BUFFER_API}/updates/create.json",
            data=post_data,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        if not result.get("success"):
            return {
                "success": False,
                "platform": "buffer",
                "message": result.get("message", "Buffer returned failure"),
            }

        updates = result.get("updates", [])
        posted_to = [u.get("profile_service", "unknown") for u in updates]

        return {
            "success": True,
            "platform": "buffer",
            "id": result.get("updates", [{}])[0].get("id", ""),
            "url": "",
            "posted_to": posted_to,
            "message": f"Queued to Buffer: {', '.join(posted_to)}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = str(e.response.json())
        except Exception:
            pass
        return {
            "success": False,
            "platform": "buffer",
            "message": f"Buffer API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {"success": False, "platform": "buffer", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Post/schedule via Buffer")
    parser.add_argument("--content", required=True, help="Post text")
    parser.add_argument("--platforms", nargs="*", help="Platform filter (linkedin, twitter, etc.)")
    parser.add_argument("--schedule", help="Schedule time (ISO datetime)")
    parser.add_argument("--link", help="URL to share")
    parser.add_argument("--image", help="Image URL")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = post(
        content=args.content,
        platforms=args.platforms,
        schedule_time=args.schedule or "",
        link=args.link or "",
        image_url=args.image or "",
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'Queued' if result['success'] else 'Failed'}: {result['message']}")
        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()

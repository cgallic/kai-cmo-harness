#!/usr/bin/env python3
"""
Kai CMO Harness — LinkedIn Publisher
======================================
Post updates and articles via LinkedIn API v2.

Environment:
  LINKEDIN_ACCESS_TOKEN=your-oauth-access-token
  LINKEDIN_PERSON_ID=urn:li:person:xxxxx  (your LinkedIn member URN)

Setup: Create a LinkedIn app at https://www.linkedin.com/developers/
Required scopes: w_member_social, r_liteprofile
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def _get_credentials() -> tuple[str, str]:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    person_id = os.environ.get("LINKEDIN_PERSON_ID", "")

    if not token:
        raise ValueError("Missing LINKEDIN_ACCESS_TOKEN")

    # Auto-fetch person ID if not set
    if not person_id:
        resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.ok:
            sub = resp.json().get("sub", "")
            if sub:
                person_id = f"urn:li:person:{sub}"

    if not person_id:
        raise ValueError("Missing LINKEDIN_PERSON_ID and could not auto-detect")

    return token, person_id


def post(
    content: str = "",
    title: str = "",
    link: str = "",
    image_url: str = "",
    visibility: str = "PUBLIC",
    **_kwargs,
) -> dict:
    """
    Post to LinkedIn.

    Args:
        content: Post text
        title: Article title (for link shares)
        link: URL to share
        image_url: Image URL (uploaded as media)
        visibility: PUBLIC or CONNECTIONS
    """
    try:
        token, person_id = _get_credentials()
    except ValueError as e:
        return {"success": False, "platform": "linkedin", "message": str(e)}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Build post payload
    post_data: dict = {
        "author": person_id,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility,
        },
    }

    # Add link share if provided
    if link:
        share_content = post_data["specificContent"]["com.linkedin.ugc.ShareContent"]
        share_content["shareMediaCategory"] = "ARTICLE"
        share_content["media"] = [{
            "status": "READY",
            "originalUrl": link,
            "title": {"text": title or content[:100]},
        }]

    try:
        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_data,
            timeout=30,
        )
        resp.raise_for_status()
        post_id = resp.headers.get("X-RestLi-Id", resp.json().get("id", ""))

        return {
            "success": True,
            "platform": "linkedin",
            "id": post_id,
            "url": f"https://www.linkedin.com/feed/update/{post_id}/",
            "message": f"Posted to LinkedIn — {post_id}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = str(e.response.json())
        except Exception:
            pass
        return {
            "success": False,
            "platform": "linkedin",
            "message": f"LinkedIn API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {"success": False, "platform": "linkedin", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Post to LinkedIn")
    parser.add_argument("--content", required=True, help="Post text")
    parser.add_argument("--title", help="Article/link title")
    parser.add_argument("--link", help="URL to share")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = post(content=args.content, title=args.title or "", link=args.link or "")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'Posted' if result['success'] else 'Failed'}: {result['message']}")
        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()

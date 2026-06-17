#!/usr/bin/env python3
"""
Kai CMO Harness — X/Twitter Publisher
=======================================
Post via X/Twitter API v2 (OAuth 1.0a User Context).

Environment:
  TWITTER_API_KEY=your-api-key
  TWITTER_API_SECRET=your-api-secret
  TWITTER_ACCESS_TOKEN=your-access-token
  TWITTER_ACCESS_SECRET=your-access-token-secret

Setup: https://developer.twitter.com/en/portal → Create project + app → Keys & Tokens
"""

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

load_dotenv()

TWITTER_API_BASE = "https://api.twitter.com/2"


def _get_auth() -> OAuth1:
    api_key = os.environ.get("TWITTER_API_KEY", "")
    api_secret = os.environ.get("TWITTER_API_SECRET", "")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET", "")

    missing = [v for v, val in [
        ("TWITTER_API_KEY", api_key),
        ("TWITTER_API_SECRET", api_secret),
        ("TWITTER_ACCESS_TOKEN", access_token),
        ("TWITTER_ACCESS_SECRET", access_secret),
    ] if not val]

    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return OAuth1(api_key, api_secret, access_token, access_secret)


def post(
    content: str = "",
    reply_to: str = "",
    **_kwargs,
) -> dict:
    """
    Post a tweet.

    Args:
        content: Tweet text (max 280 chars)
        reply_to: Tweet ID to reply to (for threads)
    """
    try:
        auth = _get_auth()
    except ValueError as e:
        return {"success": False, "platform": "twitter", "message": str(e)}

    if len(content) > 280:
        return {
            "success": False,
            "platform": "twitter",
            "message": f"Tweet exceeds 280 chars ({len(content)} chars). Trim or split into thread.",
        }

    payload: dict = {"text": content}
    if reply_to:
        payload["reply"] = {"in_reply_to_tweet_id": reply_to}

    try:
        resp = requests.post(
            f"{TWITTER_API_BASE}/tweets",
            json=payload,
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        tweet_id = data.get("id", "")

        return {
            "success": True,
            "platform": "twitter",
            "id": tweet_id,
            "url": f"https://x.com/i/web/status/{tweet_id}",
            "message": f"Posted tweet — {tweet_id}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = str(e.response.json())
        except Exception:
            pass
        return {
            "success": False,
            "platform": "twitter",
            "message": f"Twitter API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {"success": False, "platform": "twitter", "message": str(e)}


def post_thread(tweets: list[str]) -> list[dict]:
    """Post a thread of tweets. Returns list of results."""
    results = []
    reply_to = ""
    for tweet_text in tweets:
        result = post(content=tweet_text, reply_to=reply_to)
        results.append(result)
        if result["success"]:
            reply_to = result["id"]
        else:
            break
    return results


def main():
    parser = argparse.ArgumentParser(description="Post to X/Twitter")
    parser.add_argument("--content", required=True, help="Tweet text (max 280 chars)")
    parser.add_argument("--reply-to", help="Tweet ID to reply to")
    parser.add_argument("--thread", action="store_true", help="Split long content into thread")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.thread and len(args.content) > 280:
        # Split into 280-char chunks at word boundaries
        words = args.content.split()
        tweets = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if len(test) <= 275:  # Leave room for thread numbering
                current = test
            else:
                if current:
                    tweets.append(current)
                current = word
        if current:
            tweets.append(current)

        results = post_thread(tweets)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for i, r in enumerate(results):
                print(f"  [{i+1}/{len(results)}] {'OK' if r['success'] else 'FAIL'}: {r['message']}")
    else:
        result = post(content=args.content, reply_to=args.reply_to or "")
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"{'Posted' if result['success'] else 'Failed'}: {result['message']}")
            if not result["success"]:
                sys.exit(1)


if __name__ == "__main__":
    main()

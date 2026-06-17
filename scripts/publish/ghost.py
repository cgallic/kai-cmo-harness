#!/usr/bin/env python3
"""
Kai CMO Harness — Ghost CMS Publisher
=======================================
Publish content to Ghost via Admin API.

Usage:
  python scripts/publish/ghost.py --draft path/to/draft.md --status draft

Environment:
  GHOST_URL=https://mysite.com
  GHOST_ADMIN_KEY=your-admin-api-key

Get admin key: Ghost Admin → Settings → Integrations → Add custom integration
The key format is: {id}:{secret}
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def _make_jwt(admin_key: str) -> str:
    """Create a JWT token from Ghost Admin API key."""
    try:
        import jwt as pyjwt
    except ImportError:
        raise ImportError("Install PyJWT: pip install PyJWT")

    key_id, secret = admin_key.split(":")
    iat = int(time.time())

    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    payload = {
        "iat": iat,
        "exp": iat + 300,  # 5 min
        "aud": "/admin/",
    }

    return pyjwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers=header)


def _get_credentials() -> tuple[str, str]:
    """Load Ghost credentials from environment."""
    url = os.environ.get("GHOST_URL", "").rstrip("/")
    admin_key = os.environ.get("GHOST_ADMIN_KEY", "")

    if not url or not admin_key:
        missing = []
        if not url:
            missing.append("GHOST_URL")
        if not admin_key:
            missing.append("GHOST_ADMIN_KEY")
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return url, admin_key


def _markdown_to_mobiledoc(md: str) -> str:
    """Convert markdown to Ghost's mobiledoc format (using HTML card)."""
    # Convert markdown to HTML first
    try:
        import markdown as md_lib
        html = md_lib.markdown(md, extensions=["extra", "codehilite", "toc"])
    except ImportError:
        # Basic fallback
        html = md
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    mobiledoc = {
        "version": "0.3.1",
        "atoms": [],
        "cards": [["html", {"html": html}]],
        "markups": [],
        "sections": [[10, 0]],
    }
    return json.dumps(mobiledoc)


def publish(
    title: str = "",
    body: str = "",
    status: str = "draft",
    tags: list[str] | None = None,
    slug: str = "",
    meta_description: str = "",
    featured_image_url: str = "",
    excerpt: str = "",
    **_kwargs,
) -> dict:
    """Publish content to Ghost CMS."""
    try:
        site_url, admin_key = _get_credentials()
    except ValueError as e:
        return {"success": False, "platform": "ghost", "message": str(e)}

    try:
        token = _make_jwt(admin_key)
    except Exception as e:
        return {"success": False, "platform": "ghost", "message": f"JWT creation failed: {e}"}

    headers = {"Authorization": f"Ghost {token}"}

    # Build post data
    post_data: dict = {
        "title": title,
        "mobiledoc": _markdown_to_mobiledoc(body),
        "status": status,
    }

    if slug:
        post_data["slug"] = slug
    if meta_description:
        post_data["meta_description"] = meta_description
        post_data["custom_excerpt"] = excerpt or meta_description
    if featured_image_url:
        post_data["feature_image"] = featured_image_url
    if tags:
        post_data["tags"] = [{"name": t} for t in tags]

    try:
        resp = requests.post(
            f"{site_url}/ghost/api/admin/posts/",
            json={"posts": [post_data]},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()["posts"][0]
        return {
            "success": True,
            "platform": "ghost",
            "id": result.get("id"),
            "url": result.get("url", ""),
            "status": result.get("status"),
            "message": f"Published as {result.get('status')} — {result.get('url', '')}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = json.dumps(e.response.json().get("errors", []))
        except Exception:
            pass
        return {
            "success": False,
            "platform": "ghost",
            "message": f"Ghost API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {"success": False, "platform": "ghost", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Publish to Ghost CMS")
    parser.add_argument("--draft", help="Path to markdown draft file")
    parser.add_argument("--title", help="Post title")
    parser.add_argument("--body", help="Post body")
    parser.add_argument("--status", default="draft", choices=["draft", "published", "scheduled"])
    parser.add_argument("--tags", nargs="*", help="Tag names")
    parser.add_argument("--slug", help="URL slug")
    parser.add_argument("--meta-description", help="SEO meta description")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    title = args.title or ""
    body = args.body or ""

    if args.draft:
        content = Path(args.draft).read_text()
        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1 and not title:
            title = h1.group(1).strip()
        body = content

    result = publish(title=title, body=body, status=args.status, tags=args.tags,
                     slug=args.slug, meta_description=args.meta_description or "")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'Published' if result['success'] else 'Failed'}: {result['message']}")
        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()

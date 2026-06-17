#!/usr/bin/env python3
"""
Kai CMO Harness — Webflow CMS Publisher
=========================================
Publish content to Webflow CMS via API v2.

Environment:
  WEBFLOW_API_TOKEN=your-api-token
  WEBFLOW_SITE_ID=your-site-id
  WEBFLOW_COLLECTION_ID=your-blog-collection-id

Get token: Webflow Dashboard → Site Settings → Integrations → API Access
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def _get_credentials() -> tuple[str, str, str]:
    token = os.environ.get("WEBFLOW_API_TOKEN", "")
    site_id = os.environ.get("WEBFLOW_SITE_ID", "")
    collection_id = os.environ.get("WEBFLOW_COLLECTION_ID", "")
    if not all([token, site_id, collection_id]):
        missing = [v for v, val in [
            ("WEBFLOW_API_TOKEN", token),
            ("WEBFLOW_SITE_ID", site_id),
            ("WEBFLOW_COLLECTION_ID", collection_id),
        ] if not val]
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    return token, site_id, collection_id


def _markdown_to_html(md: str) -> str:
    try:
        import markdown
        return markdown.markdown(md, extensions=["extra"])
    except ImportError:
        html = md
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        return html


def publish(
    title: str = "",
    body: str = "",
    status: str = "draft",
    slug: str = "",
    meta_description: str = "",
    featured_image_url: str = "",
    **_kwargs,
) -> dict:
    """Publish content to Webflow CMS collection."""
    try:
        token, site_id, collection_id = _get_credentials()
    except ValueError as e:
        return {"success": False, "platform": "webflow", "message": str(e)}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    # Convert markdown to HTML
    if body.startswith("#") or "##" in body[:500]:
        body = _markdown_to_html(body)

    # Webflow collection item fields (standard blog collection)
    field_data = {
        "name": title,
        "slug": slug or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"),
        "post-body": body,
    }

    if meta_description:
        field_data["post-summary"] = meta_description
    if featured_image_url:
        field_data["main-image"] = {"url": featured_image_url}

    is_live = status == "publish"

    try:
        resp = requests.post(
            f"https://api.webflow.com/v2/collections/{collection_id}/items",
            headers=headers,
            json={"fieldData": field_data, "isArchived": False, "isDraft": not is_live},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        # Publish if requested
        if is_live:
            item_id = result.get("id")
            requests.post(
                f"https://api.webflow.com/v2/collections/{collection_id}/items/publish",
                headers=headers,
                json={"itemIds": [item_id]},
                timeout=30,
            )

        return {
            "success": True,
            "platform": "webflow",
            "id": result.get("id"),
            "url": f"https://webflow.com/design/{site_id}",
            "status": "published" if is_live else "draft",
            "message": f"Created in Webflow collection — {'published' if is_live else 'draft'}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = str(e.response.json())
        except Exception:
            pass
        return {
            "success": False,
            "platform": "webflow",
            "message": f"Webflow API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {"success": False, "platform": "webflow", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Publish to Webflow CMS")
    parser.add_argument("--draft", help="Path to markdown draft file")
    parser.add_argument("--title", help="Post title")
    parser.add_argument("--status", default="draft", choices=["draft", "publish"])
    parser.add_argument("--slug", help="URL slug")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    title = args.title or ""
    body = ""
    if args.draft:
        content = Path(args.draft).read_text()
        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1 and not title:
            title = h1.group(1).strip()
        body = content

    result = publish(title=title, body=body, status=args.status, slug=args.slug)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'Published' if result['success'] else 'Failed'}: {result['message']}")
        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Kai CMO Harness — WordPress Publisher
=======================================
Publish content to WordPress via REST API (wp-json/wp/v2/posts).

Usage:
  python scripts/publish/wordpress.py --draft path/to/draft.md --status draft
  python scripts/publish/wordpress.py --title "My Post" --body "<p>Content</p>" --publish

Environment:
  WP_URL=https://mysite.com
  WP_USERNAME=admin
  WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  (Application Password, not login password)

Generate an Application Password: WP Admin → Users → Your Profile → Application Passwords
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
    """Load WordPress credentials from environment."""
    url = os.environ.get("WP_URL", "").rstrip("/")
    username = os.environ.get("WP_USERNAME", "")
    password = os.environ.get("WP_APP_PASSWORD", "")

    if not all([url, username, password]):
        missing = []
        if not url:
            missing.append("WP_URL")
        if not username:
            missing.append("WP_USERNAME")
        if not password:
            missing.append("WP_APP_PASSWORD")
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    return url, username, password


def _markdown_to_html(md: str) -> str:
    """Convert markdown to basic HTML for WordPress."""
    try:
        import markdown
        return markdown.markdown(md, extensions=["extra", "codehilite", "toc"])
    except ImportError:
        # Fallback: basic conversion
        html = md
        # Headers
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        # Bold/italic
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        # Paragraphs
        paragraphs = html.split("\n\n")
        result = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith("<h"):
                result.append(f"<p>{p}</p>")
            else:
                result.append(p)
        return "\n".join(result)


def _resolve_categories(site_url: str, auth: tuple, names: list[str]) -> list[int]:
    """Resolve category names to IDs, creating if needed."""
    ids = []
    for name in names:
        # Search existing
        resp = requests.get(
            f"{site_url}/wp-json/wp/v2/categories",
            params={"search": name},
            auth=auth,
            timeout=10,
        )
        if resp.ok and resp.json():
            ids.append(resp.json()[0]["id"])
        else:
            # Create
            resp = requests.post(
                f"{site_url}/wp-json/wp/v2/categories",
                json={"name": name},
                auth=auth,
                timeout=10,
            )
            if resp.ok:
                ids.append(resp.json()["id"])
    return ids


def _resolve_tags(site_url: str, auth: tuple, names: list[str]) -> list[int]:
    """Resolve tag names to IDs, creating if needed."""
    ids = []
    for name in names:
        resp = requests.get(
            f"{site_url}/wp-json/wp/v2/tags",
            params={"search": name},
            auth=auth,
            timeout=10,
        )
        if resp.ok and resp.json():
            ids.append(resp.json()[0]["id"])
        else:
            resp = requests.post(
                f"{site_url}/wp-json/wp/v2/tags",
                json={"name": name},
                auth=auth,
                timeout=10,
            )
            if resp.ok:
                ids.append(resp.json()["id"])
    return ids


def publish(
    title: str = "",
    body: str = "",
    status: str = "draft",
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    slug: str = "",
    meta_description: str = "",
    featured_image_url: str = "",
    excerpt: str = "",
    **_kwargs,
) -> dict:
    """
    Publish content to WordPress.

    Returns:
        dict with: success, url, id, platform, message
    """
    try:
        site_url, username, password = _get_credentials()
    except ValueError as e:
        return {"success": False, "platform": "wordpress", "message": str(e)}

    auth = (username, password)

    # Convert markdown body to HTML if needed
    if body.startswith("#") or "##" in body[:500]:
        body = _markdown_to_html(body)

    # Build post data
    post_data: dict = {
        "title": title,
        "content": body,
        "status": status,
    }

    if slug:
        post_data["slug"] = slug
    if excerpt or meta_description:
        post_data["excerpt"] = excerpt or meta_description

    # Resolve categories and tags
    if categories:
        cat_ids = _resolve_categories(site_url, auth, categories)
        if cat_ids:
            post_data["categories"] = cat_ids

    if tags:
        tag_ids = _resolve_tags(site_url, auth, tags)
        if tag_ids:
            post_data["tags"] = tag_ids

    # Set featured image if provided
    if featured_image_url:
        # Download and upload to media library
        try:
            img_resp = requests.get(featured_image_url, timeout=15)
            img_resp.raise_for_status()
            content_type = img_resp.headers.get("content-type", "image/jpeg")
            ext = content_type.split("/")[-1].split(";")[0]
            filename = f"featured-{slug or 'image'}.{ext}"

            media_resp = requests.post(
                f"{site_url}/wp-json/wp/v2/media",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Type": content_type,
                },
                data=img_resp.content,
                auth=auth,
                timeout=30,
            )
            if media_resp.ok:
                post_data["featured_media"] = media_resp.json()["id"]
        except Exception:
            pass  # Non-critical — proceed without featured image

    # Idempotency: if a post with this slug already exists, update it in
    # place instead of creating a duplicate on re-runs.
    existing_id = None
    existing_status = None
    existing_link = ""
    if slug:
        try:
            lookup = requests.get(
                f"{site_url}/wp-json/wp/v2/posts",
                params={"slug": slug, "status": "any"},
                auth=auth,
                timeout=10,
            )
            if lookup.ok:
                matches = lookup.json()
                if isinstance(matches, list) and matches:
                    existing_id = matches[0].get("id")
                    existing_status = matches[0].get("status")
                    existing_link = matches[0].get("link", "")
        except Exception:
            existing_id = None  # lookup failure falls back to create

    # Create (or update) post
    endpoint = f"{site_url}/wp-json/wp/v2/posts"
    if existing_id:
        # Approval doctrine: a human may have published (and edited) this post
        # in WP admin since the draft was created. Overwriting a LIVE post's
        # content — or demoting it back to draft via the status field — is a
        # live-channel mutation without approval. Refuse unless the caller
        # explicitly asked for status=publish (that explicit ask IS the
        # human approval, e.g. the CLI --publish path).
        if existing_status == "publish" and status != "publish":
            return {
                "success": True,
                "platform": "wordpress",
                "id": existing_id,
                "url": existing_link,
                "edit_url": f"{site_url}/wp-admin/post.php?post={existing_id}&action=edit",
                "status": "publish",
                "updated": False,
                "skipped": "existing_live_post",
                "message": (
                    f"Post with slug '{slug}' is already live — left untouched. "
                    "Edit or unpublish it in WP admin if you need changes."
                ),
            }
        endpoint = f"{site_url}/wp-json/wp/v2/posts/{existing_id}"
        if status != "publish":
            # Preserve the existing post's status on re-runs: never let the
            # engine's default status=draft demote a post whose status we
            # could not confirm from the lookup.
            post_data.pop("status", None)

    try:
        resp = requests.post(
            endpoint,
            json=post_data,
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        action = "Updated existing" if existing_id else "Published as"
        return {
            "success": True,
            "platform": "wordpress",
            "id": result.get("id"),
            "url": result.get("link", ""),
            "edit_url": f"{site_url}/wp-admin/post.php?post={result.get('id')}&action=edit",
            "status": result.get("status"),
            "updated": bool(existing_id),
            "message": f"{action} {result.get('status')} — {result.get('link', '')}",
        }
    except requests.HTTPError as e:
        error_body = ""
        try:
            error_body = e.response.json().get("message", "")
        except Exception:
            pass
        return {
            "success": False,
            "platform": "wordpress",
            "message": f"WordPress API error: {e.response.status_code} — {error_body or str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "platform": "wordpress",
            "message": f"Request failed: {e}",
        }


def main():
    parser = argparse.ArgumentParser(description="Publish to WordPress")
    parser.add_argument("--draft", help="Path to markdown draft file")
    parser.add_argument("--title", help="Post title (extracted from H1 if --draft used)")
    parser.add_argument("--body", help="Post body HTML")
    parser.add_argument("--status", default="draft", choices=["draft", "publish", "pending", "private"])
    parser.add_argument("--categories", nargs="*", help="Category names")
    parser.add_argument("--tags", nargs="*", help="Tag names")
    parser.add_argument("--slug", help="URL slug")
    parser.add_argument("--meta-description", help="SEO meta description")
    parser.add_argument("--featured-image", help="Featured image URL")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    title = args.title or ""
    body = args.body or ""

    meta_desc = ""
    if args.draft:
        content = Path(args.draft).read_text()
        # Extract title from H1
        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1 and not title:
            title = h1.group(1).strip()
        # Extract meta description
        meta_match = re.search(r"^Meta:\s*(.+)$", content, re.MULTILINE)
        meta_desc = meta_match.group(1).strip() if meta_match else ""
        body = content

    result = publish(
        title=title,
        body=body,
        status=args.status,
        categories=args.categories,
        tags=args.tags,
        slug=args.slug,
        meta_description=args.meta_description or meta_desc,
        featured_image_url=args.featured_image or "",
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"Published: {result['url']}")
            print(f"Edit: {result.get('edit_url', '')}")
            print(f"Status: {result['status']}")
        else:
            print(f"Failed: {result['message']}")
            sys.exit(1)


if __name__ == "__main__":
    main()

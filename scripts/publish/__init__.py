"""
Kai CMO Harness — Publishing Module
=====================================
Unified interface for publishing content to any CMS.

Usage:
  from scripts.publish import publish
  result = publish("wordpress", title="My Post", body="<p>Content</p>", status="draft")
  result = publish("ghost", title="My Post", body="<p>Content</p>")
  result = publish("markdown", title="My Post", body="# Content", output_dir="./blog/")

Supported platforms: wordpress, ghost, webflow, markdown
"""

import importlib
from typing import Any


PLATFORMS = {
    "wordpress": "scripts.publish.wordpress",
    "ghost": "scripts.publish.ghost",
    "webflow": "scripts.publish.webflow",
    "markdown": "scripts.publish.markdown_to_site",
}


def publish(platform: str, **kwargs: Any) -> dict:
    """
    Publish content to a CMS platform.

    Args:
        platform: One of: wordpress, ghost, webflow, markdown
        **kwargs: Platform-specific arguments. Common ones:
            title: str — Post title
            body: str — Post body (HTML or markdown)
            status: str — "draft" or "publish" (default: "draft")
            categories: list[str] — Category names/slugs
            tags: list[str] — Tag names/slugs
            featured_image_url: str — URL for featured image
            slug: str — URL slug
            meta_description: str — SEO meta description
            author: str — Author name/ID

    Returns:
        dict with keys: success, url, id, platform, message
    """
    if platform not in PLATFORMS:
        return {
            "success": False,
            "platform": platform,
            "message": f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORMS.keys())}",
        }

    try:
        module = importlib.import_module(PLATFORMS[platform])
        return module.publish(**kwargs)
    except ImportError as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"Missing dependency for {platform}: {e}. Check requirements.txt.",
        }
    except Exception as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"Publishing failed: {e}",
        }

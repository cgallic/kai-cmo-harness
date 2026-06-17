"""
Kai CMO Harness — Social Media Module
=======================================
Unified interface for posting to social media platforms.

Usage:
  from scripts.social import post
  result = post("linkedin", content="My update", title="Optional article title")
  result = post("twitter", content="Tweet text")
  result = post("buffer", content="Scheduled post", platforms=["linkedin", "twitter"])

Supported: linkedin, twitter, buffer
"""

import importlib
from typing import Any


PLATFORMS = {
    "linkedin": "scripts.social.linkedin",
    "twitter": "scripts.social.twitter",
    "buffer": "scripts.social.buffer",
}


def post(platform: str, **kwargs: Any) -> dict:
    """
    Post content to a social media platform.

    Args:
        platform: One of: linkedin, twitter, buffer
        **kwargs: Platform-specific arguments. Common ones:
            content: str — Post text
            title: str — Article title (LinkedIn articles)
            image_url: str — Image to attach
            link: str — URL to share
            schedule_time: str — ISO datetime for scheduling (Buffer)

    Returns:
        dict with keys: success, id, url, platform, message
    """
    if platform not in PLATFORMS:
        return {
            "success": False,
            "platform": platform,
            "message": f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORMS.keys())}",
        }

    try:
        module = importlib.import_module(PLATFORMS[platform])
        return module.post(**kwargs)
    except ImportError as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"Missing dependency for {platform}: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "platform": platform,
            "message": f"Posting failed: {e}",
        }

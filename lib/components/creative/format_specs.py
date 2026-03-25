"""
Platform Format Specs — Character limits, dimensions, durations for all ad platforms.

Single source of truth for platform constraints. Used by /ad-copy, /ad-render, /creative-brief.

Usage:
    spec = get_platform_spec("meta", "feed")
    print(spec.image_size)   # "1080x1080"
    print(spec.char_limits)  # {"primary": 125, "headline": 40, "description": 30}
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FormatSpec:
    """Specification for a single ad format on a platform."""
    platform: str
    placement: str
    image_size: str = ""
    video_ratio: str = ""
    video_max_duration: int = 0  # seconds
    video_recommended_duration: str = ""
    video_max_file_mb: int = 0
    char_limits: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# META (Facebook / Instagram)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

META_FEED = FormatSpec(
    platform="meta", placement="feed",
    image_size="1080x1080",
    video_ratio="1:1 or 4:5",
    video_max_duration=14400, video_recommended_duration="15-30s", video_max_file_mb=4096,
    char_limits={"primary_text": 125, "primary_max": 2200, "headline": 40, "description": 30},
    notes=["Primary truncates at 125 chars on mobile", "Less than 20% text on image (soft rule)"],
)

META_STORIES = FormatSpec(
    platform="meta", placement="stories",
    image_size="1080x1920",
    video_ratio="9:16",
    video_max_duration=120, video_recommended_duration="5-15s", video_max_file_mb=4096,
    char_limits={"primary_text": 125, "headline": 40},
    notes=["Full-screen vertical", "Sound-on opportunity (unlike feed)"],
)

META_REELS = FormatSpec(
    platform="meta", placement="reels",
    image_size="1080x1920",
    video_ratio="9:16",
    video_max_duration=90, video_recommended_duration="15-30s", video_max_file_mb=4096,
    char_limits={"primary_text": 72, "headline": 40},
    notes=["Native Reels style outperforms polished ads", "Music/trending audio recommended"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GOOGLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOOGLE_SEARCH = FormatSpec(
    platform="google", placement="search",
    char_limits={"headline": 30, "headlines_max": 15, "description": 90, "descriptions_max": 4, "display_path": 15},
    notes=["Include keyword in headline 1", "Pin best headline to position 1"],
)

GOOGLE_DISPLAY = FormatSpec(
    platform="google", placement="display",
    image_size="1200x628 (landscape), 300x300 (square)",
    char_limits={"short_headline": 25, "long_headline": 90, "description": 90},
    notes=["Responsive display ads outperform uploaded images", "Provide 5+ headlines, 5+ images"],
)

GOOGLE_YOUTUBE = FormatSpec(
    platform="google", placement="youtube",
    video_ratio="16:9",
    video_max_duration=360, video_recommended_duration="15-30s", video_max_file_mb=262144,
    char_limits={"headline": 40, "description": 90, "companion_banner": "300x60"},
    notes=["First 5 seconds = hook (skippable after 5s)", "Companion banner shows throughout"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIKTOK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIKTOK_INFEED = FormatSpec(
    platform="tiktok", placement="in-feed",
    image_size="1080x1920",
    video_ratio="9:16",
    video_max_duration=60, video_recommended_duration="9-15s", video_max_file_mb=500,
    char_limits={"ad_text": 100, "brand_name": 20},
    notes=["Native style outperforms polished 3-5x", "AI content disclosure required", "First 2s = hook"],
)

TIKTOK_TOPVIEW = FormatSpec(
    platform="tiktok", placement="topview",
    video_ratio="9:16",
    video_max_duration=60, video_recommended_duration="9-15s", video_max_file_mb=500,
    char_limits={"ad_text": 100},
    notes=["First ad user sees on app open", "Premium placement, highest CPM"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LINKEDIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LINKEDIN_SPONSORED = FormatSpec(
    platform="linkedin", placement="sponsored-content",
    image_size="1200x627",
    video_ratio="16:9 or 1:1",
    video_max_duration=1800, video_recommended_duration="15-60s", video_max_file_mb=200,
    char_limits={"intro_text": 150, "intro_max": 600, "headline": 70, "description": 100},
    notes=["Professional context required", "B2B claims need substantiation", "Truncates at 150 on mobile"],
)

LINKEDIN_MESSAGE = FormatSpec(
    platform="linkedin", placement="message-ad",
    char_limits={"subject": 60, "body": 500, "cta_button": 20},
    notes=["Max 1 message per 45 days to same user", "Real person as sender (not company page)"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PINTEREST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PINTEREST_STANDARD = FormatSpec(
    platform="pinterest", placement="standard-pin",
    image_size="1000x1500 (2:3)",
    char_limits={"title": 100, "description": 500},
    notes=["All weight loss ads banned (narrow GLP-1 exception)", "Strict body image rules"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SNAPCHAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SNAPCHAT_SNAP = FormatSpec(
    platform="snapchat", placement="snap-ad",
    video_ratio="9:16",
    video_max_duration=180, video_recommended_duration="3-5s", video_max_file_mb=1024,
    char_limits={"brand_name": 25, "headline": 34, "cta": 20},
    notes=["Young audience protections", "EU political ad ban"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_ALL_SPECS = {
    ("meta", "feed"): META_FEED,
    ("meta", "stories"): META_STORIES,
    ("meta", "reels"): META_REELS,
    ("google", "search"): GOOGLE_SEARCH,
    ("google", "display"): GOOGLE_DISPLAY,
    ("google", "youtube"): GOOGLE_YOUTUBE,
    ("tiktok", "in-feed"): TIKTOK_INFEED,
    ("tiktok", "topview"): TIKTOK_TOPVIEW,
    ("linkedin", "sponsored"): LINKEDIN_SPONSORED,
    ("linkedin", "message"): LINKEDIN_MESSAGE,
    ("pinterest", "standard"): PINTEREST_STANDARD,
    ("snapchat", "snap"): SNAPCHAT_SNAP,
}


def get_platform_spec(platform: str, placement: str) -> Optional[FormatSpec]:
    """Get spec for a platform + placement combo."""
    return _ALL_SPECS.get((platform.lower(), placement.lower()))


def get_all_placements(platform: str) -> list[FormatSpec]:
    """Get all format specs for a platform."""
    return [spec for (p, _), spec in _ALL_SPECS.items() if p == platform.lower()]


def get_all_platforms() -> list[str]:
    """Get all supported platform names."""
    return sorted(set(p for p, _ in _ALL_SPECS.keys()))


def format_char_check(text: str, field: str, spec: FormatSpec) -> dict:
    """Check text against character limit for a field. Returns {ok, chars, limit, overflow}."""
    limit = spec.char_limits.get(field, 0)
    if not limit or not isinstance(limit, int):
        return {"ok": True, "chars": len(text), "limit": None, "overflow": 0}
    chars = len(text)
    return {
        "ok": chars <= limit,
        "chars": chars,
        "limit": limit,
        "overflow": max(0, chars - limit),
    }

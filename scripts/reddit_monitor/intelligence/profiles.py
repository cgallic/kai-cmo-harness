from __future__ import annotations

import json
from pathlib import Path


def validate_profile(profile: dict) -> dict:
    profile = dict(profile)
    required = {"id", "brand", "sources", "keyword_groups", "scoring", "alerts"}
    missing = sorted(required - profile.keys())
    if missing:
        raise ValueError(f"profile missing required keys: {', '.join(missing)}")
    if not isinstance(profile["keyword_groups"], list) or not profile["keyword_groups"]:
        raise ValueError("keyword_groups must be a non-empty list")
    rss = profile["sources"].get("reddit_rss", {})
    if rss.get("enabled") and not rss.get("subreddits"):
        raise ValueError("enabled reddit_rss source requires subreddits")
    profile.setdefault("schema_version", 1)
    profile.setdefault("statuses", ["New", "Approved", "Assigned", "Answered", "Rejected", "Published"])
    profile.setdefault("content_brief_threshold", 8)
    return profile


def load_profile(path: str | Path) -> dict:
    source = Path(path)
    return validate_profile(json.loads(source.read_text(encoding="utf-8")))


def save_profile(path: str | Path, profile: dict) -> dict:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_profile(profile)
    target.write_text(json.dumps(validated, indent=2, ensure_ascii=False), encoding="utf-8")
    return load_profile(target)

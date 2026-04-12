"""Shared utilities for ad platform pull scripts.

Provides env loading, HTTP helpers with retry, JSON output writer,
and standardized date range configuration. Zero external dependencies
beyond `requests`.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PULLS_DIR = REPO_ROOT / "workspace" / "ads" / "pulls"

# ---------------------------------------------------------------------------
# Environment loading (Windows-safe, no dotenv dependency)
# ---------------------------------------------------------------------------

_env_cache: Dict[str, str] = {}


def _load_env_file() -> Dict[str, str]:
    """Parse .env.local (or .env) into a dict. No shell expansion."""
    if _env_cache:
        return _env_cache

    for name in (".env.local", ".env"):
        path = REPO_ROOT / name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Strip surrounding quotes
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    _env_cache[key] = value
            break
    return _env_cache


def env(key: str, default: str = "") -> str:
    """Get an env var: .env.local first, then os.environ, then default."""
    loaded = _load_env_file()
    return loaded.get(key, os.environ.get(key, default))


def has_creds(*keys: str) -> bool:
    """Check if ALL listed env vars have non-empty values."""
    return all(env(k) for k in keys)


# ---------------------------------------------------------------------------
# HTTP helpers with retry
# ---------------------------------------------------------------------------

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 2.0  # seconds, doubles each retry


def api_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    label: str = "",
) -> Dict[str, Any]:
    """GET request with exponential backoff retry. Returns parsed JSON."""
    return _request("GET", url, headers=headers, params=params,
                    retries=retries, backoff=backoff, label=label)


def api_post(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    label: str = "",
) -> Dict[str, Any]:
    """POST request with exponential backoff retry. Returns parsed JSON."""
    return _request("POST", url, headers=headers, json_body=json_body,
                    data=data, retries=retries, backoff=backoff, label=label)


def _request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    label: str = "",
) -> Dict[str, Any]:
    """HTTP request with retry logic."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            resp = requests.request(
                method, url,
                headers=headers,
                params=params,
                json=json_body,
                data=data,
                timeout=30,
            )

            # Rate limit handling
            if resp.status_code == 429:
                wait = backoff * (2 ** attempt)
                log(f"  Rate limited{' (' + label + ')' if label else ''}, waiting {wait:.0f}s...")
                time.sleep(wait)
                continue

            # Server errors: retry
            if resp.status_code >= 500:
                wait = backoff * (2 ** attempt)
                log(f"  Server error {resp.status_code}{' (' + label + ')' if label else ''}, retrying in {wait:.0f}s...")
                time.sleep(wait)
                continue

            # Parse JSON
            body = resp.json()

            # Meta API error format
            if "error" in body and isinstance(body["error"], dict):
                err = body["error"]
                # Transient errors: retry
                if err.get("is_transient") or err.get("code") in (1, 2, 4, 17):
                    wait = backoff * (2 ** attempt)
                    log(f"  Transient API error{' (' + label + ')' if label else ''}: {err.get('message', '')[:80]}, retrying in {wait:.0f}s...")
                    time.sleep(wait)
                    continue
                # Permanent error: raise
                raise APIError(
                    f"API error{' (' + label + ')' if label else ''}: "
                    f"[{err.get('code', '?')}] {err.get('message', 'Unknown error')}"
                )

            return body

        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < retries:
                wait = backoff * (2 ** attempt)
                log(f"  Request failed{' (' + label + ')' if label else ''}: {e}, retrying in {wait:.0f}s...")
                time.sleep(wait)
            continue

    raise APIError(f"All {retries + 1} attempts failed{' (' + label + ')' if label else ''}: {last_error}")


class APIError(Exception):
    """Raised when an API call fails after retries."""
    pass


# ---------------------------------------------------------------------------
# JSON output writer
# ---------------------------------------------------------------------------

def today_str() -> str:
    """YYYY-MM-DD in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_pull(platform: str, data: Dict[str, Any], date: Optional[str] = None) -> Path:
    """Write pull data to workspace/ads/pulls/YYYY-MM-DD/<platform>.json."""
    date = date or today_str()
    out_dir = PULLS_DIR / date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{platform}.json"

    # Add metadata
    data["_meta"] = {
        "platform": platform,
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "pull_date": date,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    return out_path


def read_pull(platform: str, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read a previous pull from disk. Returns None if not found."""
    date = date or today_str()
    path = PULLS_DIR / date / f"{platform}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    """Print to stderr (stdout reserved for JSON output)."""
    print(msg, file=sys.stderr)


def log_section(title: str) -> None:
    """Print a section header."""
    log(f"\n{'='*60}")
    log(f"  {title}")
    log(f"{'='*60}")


# ---------------------------------------------------------------------------
# Meta API date presets (used by pull_meta.py)
# ---------------------------------------------------------------------------

META_DATE_PRESETS = ["today", "yesterday", "last_7d", "last_14d", "last_28d"]

# Meta insight fields — the comprehensive set
META_INSIGHT_FIELDS = [
    # Delivery
    "impressions", "reach", "frequency", "spend",
    # Engagement
    "clicks", "inline_link_clicks", "unique_clicks",
    "ctr", "unique_ctr", "cpc", "cpm", "cpp",
    # Conversions
    "actions", "action_values", "cost_per_action_type",
    "conversions", "cost_per_conversion",
    "conversion_values", "cost_per_unique_action_type",
    # Video
    "video_p25_watched_actions", "video_p50_watched_actions",
    "video_p75_watched_actions", "video_p100_watched_actions",
    "video_avg_time_watched_actions", "video_thruplay_watched_actions",
    # Quality diagnostics
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking",
]

META_INSIGHT_FIELDS_STR = ",".join(META_INSIGHT_FIELDS)

# Meta breakdown combos (must be queried separately — combining them errors)
META_BREAKDOWNS = [
    "age,gender",
    "publisher_platform,platform_position",
    "device_platform",
]

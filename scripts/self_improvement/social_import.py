#!/usr/bin/env python3
"""
Social Data Importer — Kai Harness Self-Learning Loop

Imports social media metrics from ANY CSV export into content_log.json
so the learning loop can classify social content and extract patterns.

Uses LLM to auto-detect platform and map arbitrary column names to our
schema. Works with TikTok, Instagram, YouTube, LinkedIn, X/Twitter,
email platforms, or any data source with performance metrics.

Usage:
  python3 social_import.py                          # Import all CSVs in drop folder
  python3 social_import.py --file export.csv        # Import a specific file
  python3 social_import.py --platform tiktok        # Force platform detection
  python3 social_import.py --dry-run                # Preview without saving
"""

import argparse
import csv
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from google import genai as google_genai

from scripts.harness_config import get_config

_CFG = get_config()

IMPORT_DIR = _CFG.data_dir / "social_imports"
PROCESSED_DIR = IMPORT_DIR / "processed"
CONTENT_LOG = str(_CFG.content_log)

log = logging.getLogger("social-import")
logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
)


# ── LLM column mapping ───────────────────────────────────────────────

# Cache mappings per file so we only call the LLM once per CSV
_mapping_cache: dict[str, dict] = {}


def _call_gemini(prompt: str) -> str:
    """Call Gemini API."""
    if not _CFG.gemini_api_key:
        raise RuntimeError("No Gemini API key configured")
    client = google_genai.Client(
        api_key=_CFG.gemini_api_key,
        http_options={"timeout": _CFG.api_timeout * 1000},
    )
    response = client.models.generate_content(
        model=_CFG.gemini_model, contents=prompt,
    )
    return response.text.strip()


# ── Fast heuristic detection (no LLM needed) ─────────────────────────

# Known column signatures per platform
_PLATFORM_SIGNATURES: dict[str, set[str]] = {
    "tiktok": {"video views", "views", "completion rate", "watched full video",
               "average watch time", "avg watch time", "play count"},
    "instagram": {"reach", "impressions", "profile visits", "follows",
                  "accounts reached", "profile activity"},
    "youtube": {"watch time", "subscribers", "avg view duration",
                "click-through rate", "youtube"},
    "linkedin": {"linkedin", "connection", "follower"},
    "twitter": {"tweet", "retweet", "quote tweet"},
    "email": {"open rate", "bounce rate", "unsubscribe", "delivered"},
}

# Common column name -> our metric name (case-insensitive)
_COMMON_METRICS: dict[str, str] = {
    "video views": "views", "views": "views", "total views": "views",
    "play count": "views", "plays": "views",
    "reach": "reach", "accounts reached": "reach",
    "impressions": "impressions", "total impressions": "impressions",
    "likes": "likes", "like count": "likes", "total likes": "likes",
    "comments": "comments", "comment count": "comments",
    "shares": "shares", "share count": "shares", "sends": "shares",
    "reposts": "shares", "retweets": "shares",
    "saves": "saves", "save count": "saves", "bookmarks": "saves",
    "completion rate": "completion_rate",
    "watched full video": "completion_rate",
    "full video watched rate": "completion_rate",
    "average watch time": "avg_watch_time",
    "avg watch time": "avg_watch_time",
    "avg watch time (s)": "avg_watch_time",
    "average watch time (s)": "avg_watch_time",
    "profile visits": "profile_visits", "profile views": "profile_visits",
    "follows": "follows", "new followers": "follows",
    "followers gained": "follows",
    "clicks": "clicks", "link clicks": "clicks",
    "ctr": "ctr", "click-through rate": "ctr",
    "engagement rate": "engagement_rate", "engagement_rate": "engagement_rate",
    "open rate": "open_rate", "bounce rate": "bounce_rate",
    "reply rate": "reply_rate", "unsubscribe rate": "unsubscribe_rate",
    "conversions": "conversions", "revenue": "revenue",
}

_COMMON_FIELDS: dict[str, str] = {
    "video id": "post_id", "post id": "post_id", "post_id": "post_id", "id": "post_id",
    "video link": "post_id", "link": "url", "permalink": "url", "url": "url",
    "description": "description", "caption": "description",
    "title": "description", "video description": "description",
    "date": "published_at", "date posted": "published_at",
    "post date": "published_at", "published": "published_at",
    "date published": "published_at", "creation date": "published_at",
    "posted": "published_at",
    "type": "post_type", "post type": "post_type",
    "content type": "post_type", "media type": "post_type",
    "platform": "platform",
    "site": "site",
    "keyword": "keyword",
    "persona": "persona",
    "angle": "angle",
}


def heuristic_detect(headers: list[str]) -> Optional[dict]:
    """Fast column mapping without LLM. Returns mapping dict or None."""
    lower_headers = [h.strip().lower() for h in headers]
    lower_set = set(lower_headers)

    # If CSV has a "platform" column, it's a multi-platform CSV
    if "platform" in lower_set:
        platform = "multi"
        best_score = 99
    else:
        # Detect platform from column signatures
        platform = None
        best_score = 0
        for plat, sigs in _PLATFORM_SIGNATURES.items():
            score = len(lower_set & sigs)
            if score > best_score:
                best_score = score
                platform = plat

        if best_score < 2:
            return None

    # Build column mappings
    col_map = {}
    metrics_map = {}

    for header in headers:
        lower = header.strip().lower()
        if lower in _COMMON_FIELDS:
            col_map[_COMMON_FIELDS[lower]] = header
        if lower in _COMMON_METRICS:
            metrics_map[_COMMON_METRICS[lower]] = header

    if not metrics_map:
        return None

    return {
        "platform": platform,
        "column_map": col_map,
        "metrics_columns": metrics_map,
        "notes": f"Heuristic detection ({best_score} signature matches)",
    }


def llm_detect_and_map(headers: list[str], sample_rows: list[dict]) -> dict:
    """Use LLM to detect platform and map columns to our schema.

    Returns:
        {
            "platform": "tiktok|instagram|youtube|linkedin|twitter|email|other",
            "column_map": {
                "post_id": "original_column_name",
                "description": "original_column_name",
                "published_at": "original_column_name",
                "post_type": "original_column_name",  # optional
                ...metric mappings...
            },
            "metrics_columns": {
                "our_metric_name": "original_column_name",
                ...
            }
        }
    """
    # Format sample data for the prompt
    sample_text = ""
    for i, row in enumerate(sample_rows[:3]):
        sample_text += f"\nRow {i+1}: {json.dumps(row, default=str)}"

    prompt = f"""You are analyzing a CSV export of social media or marketing performance data.

CSV Headers: {json.dumps(headers)}
{sample_text}

Analyze the headers and sample data. Return a JSON object with:

1. "platform" — which platform this data is from. One of:
   tiktok, instagram, youtube, linkedin, twitter, facebook, email, google_ads, meta_ads, snapchat, pinterest, or "other"

2. "column_map" — maps our standard field names to the actual CSV column names.
   Standard fields (map whichever exist in the CSV):
   - "post_id": unique identifier for the post/video/content
   - "description": caption, title, or description text
   - "published_at": date the content was published/posted
   - "post_type": type of content (reel, carousel, story, video, etc.)
   - "url": link to the content

3. "metrics_columns" — maps our standard metric names to CSV column names.
   Standard metrics (map whichever exist):
   - "views" or "plays": view/play count
   - "reach": unique accounts reached
   - "impressions": total impressions
   - "likes": like count
   - "comments": comment count
   - "shares": share/repost count
   - "saves": save/bookmark count
   - "completion_rate": video completion/watch-through rate
   - "avg_watch_time": average watch time in seconds
   - "engagement_rate": overall engagement rate
   - "profile_visits": profile views from this content
   - "follows": followers gained from this content
   - "clicks": link clicks
   - "ctr": click-through rate
   - "conversions": conversion count
   - "revenue": revenue/ROAS
   - "open_rate": email open rate
   - "bounce_rate": email bounce rate
   - "reply_rate": email reply rate
   Map any other numeric performance columns to descriptive metric names too.

4. "notes" — brief note about what this data appears to be (1 sentence)

Return ONLY valid JSON, no markdown fences, no explanation.
Example:
{{"platform":"tiktok","column_map":{{"post_id":"Video ID","description":"Description","published_at":"Date Posted"}},"metrics_columns":{{"views":"Video Views","likes":"Likes","completion_rate":"Watched full video"}},"notes":"TikTok Creator Center analytics export"}}"""

    raw = _call_gemini(prompt)

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.error("LLM returned invalid JSON: %s", raw[:500])
        raise ValueError(f"Could not parse LLM response as JSON")


# ── Value parsing ─────────────────────────────────────────────────────

def _parse_number(val: str) -> int:
    """Parse numbers with commas, K/M suffixes, or % signs."""
    if not val or val.strip() in ("", "-", "N/A", "n/a", "null", "None"):
        return 0
    val = val.strip().replace(",", "").replace("%", "").replace("$", "")
    if val.lower().endswith("k"):
        return int(float(val[:-1]) * 1000)
    if val.lower().endswith("m"):
        return int(float(val[:-1]) * 1_000_000)
    try:
        return int(float(val))
    except ValueError:
        return 0


def _parse_float(val: str) -> float:
    """Parse float values, handling percentages."""
    if not val or val.strip() in ("", "-", "N/A", "n/a", "null", "None"):
        return 0.0
    val = val.strip().replace(",", "").replace("$", "")
    is_pct = "%" in val
    val = val.replace("%", "")
    try:
        result = float(val)
        if is_pct and result > 1:
            result = result / 100
        return result
    except ValueError:
        return 0.0


def _parse_date(val: str) -> str:
    """Try to parse various date formats into ISO format."""
    if not val or val.strip() in ("", "-"):
        return datetime.now(timezone.utc).isoformat()

    val = val.strip()
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return val


# Rate-like metrics that should be stored as floats (0-1 range)
RATE_METRICS = {
    "completion_rate", "engagement_rate", "ctr", "click_through_rate",
    "open_rate", "bounce_rate", "reply_rate", "conversion_rate",
    "watch_through_rate",
}


def normalize_with_mapping(row: dict, mapping: dict) -> dict:
    """Normalize a CSV row using the LLM-generated column mapping."""
    col_map = mapping.get("column_map", {})
    metrics_map = mapping.get("metrics_columns", {})
    platform = mapping.get("platform", "other")

    # Extract standard fields
    def _get(field: str) -> str:
        csv_col = col_map.get(field, "")
        if csv_col and csv_col in row:
            return row[csv_col].strip()
        return ""

    # For multi-platform CSVs, read platform from the row
    if platform == "multi":
        row_platform = _get("platform").lower().strip()
        if row_platform:
            platform = row_platform

    post_id = _get("post_id") or f"{platform}_{uuid.uuid4().hex[:8]}"
    description = _get("description")[:200]
    published = _get("published_at")
    post_type = _get("post_type").lower() or "post"
    url = _get("url")

    # Extract metrics
    metrics = {}
    for our_name, csv_col in metrics_map.items():
        if csv_col not in row:
            continue
        raw_val = row[csv_col]
        if not raw_val or raw_val.strip() in ("", "-", "N/A"):
            continue

        # Use float for rate metrics, int for counts
        clean_name = our_name.lower().replace(" ", "_")
        if clean_name in RATE_METRICS:
            metrics[clean_name] = round(_parse_float(raw_val), 4)
        else:
            parsed_int = _parse_number(raw_val)
            parsed_float = _parse_float(raw_val)
            # If value has a decimal component, keep as float
            if parsed_float != 0 and parsed_float != float(parsed_int):
                metrics[clean_name] = round(parsed_float, 4)
            else:
                metrics[clean_name] = parsed_int

    # Calculate engagement_rate if we have the data and it's missing
    if "engagement_rate" not in metrics:
        interactions = sum(metrics.get(k, 0) for k in ("likes", "comments", "shares", "saves"))
        denominator = metrics.get("views") or metrics.get("reach") or metrics.get("impressions") or 0
        if interactions > 0 and denominator > 0:
            metrics["engagement_rate"] = round(interactions / denominator, 4)

    return {
        "platform": platform,
        "post_id": post_id,
        "description": description,
        "post_type": post_type,
        "url": url,
        "published_at": _parse_date(published),
        "metrics": metrics,
        # Harness-specific fields (passed through if present)
        "site": _get("site") or None,
        "keyword": _get("keyword") or None,
        "persona": _get("persona") or None,
        "angle": _get("angle") or None,
    }


# ── Import pipeline ──────────────────────────────────────────────────

def import_csv(
    filepath: Path,
    force_platform: Optional[str] = None,
) -> list[dict]:
    """Import a single CSV file using LLM-based column detection."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            log.warning("Empty CSV: %s", filepath)
            return []

        headers = list(reader.fieldnames)
        rows = list(reader)

    if not rows:
        log.warning("No data rows in %s", filepath)
        return []

    # Get or create column mapping for this file
    cache_key = filepath.name
    if cache_key in _mapping_cache:
        mapping = _mapping_cache[cache_key]
    else:
        # Try fast heuristic first
        mapping = heuristic_detect(headers)
        if mapping:
            log.info("Heuristic detection succeeded for %s", filepath.name)
        else:
            # Fall back to LLM
            log.info("Heuristic failed, analyzing %s with LLM (%d headers, %d rows)...",
                     filepath.name, len(headers), len(rows))
            try:
                mapping = llm_detect_and_map(headers, rows[:3])
            except Exception as e:
                log.error("LLM detection failed for %s: %s", filepath.name, e)
                return []
        _mapping_cache[cache_key] = mapping

    if force_platform:
        mapping["platform"] = force_platform

    platform = mapping.get("platform", "other")
    notes = mapping.get("notes", "")
    log.info("Detected: platform=%s | %s", platform, notes)
    log.info("Column map: %s", json.dumps(mapping.get("column_map", {})))
    log.info("Metrics map: %s", json.dumps(mapping.get("metrics_columns", {})))

    # Normalize all rows
    entries = []
    for i, row in enumerate(rows):
        try:
            entry = normalize_with_mapping(row, mapping)
            entry["source_file"] = filepath.name
            entry["imported_at"] = datetime.now(timezone.utc).isoformat()
            entries.append(entry)
        except Exception as e:
            log.warning("Row %d in %s failed: %s", i + 1, filepath.name, e)

    log.info("Imported %d entries from %s (platform=%s)",
             len(entries), filepath.name, platform)
    return entries


def merge_into_content_log(new_entries: list[dict], dry_run: bool = False) -> dict:
    """Merge imported social entries into content_log.json.

    Matches by post_id to avoid duplicates. Updates metrics if entry exists.
    """
    if os.path.exists(CONTENT_LOG):
        with open(CONTENT_LOG) as f:
            content_log = json.load(f)
    else:
        os.makedirs(os.path.dirname(CONTENT_LOG), exist_ok=True)
        content_log = []

    # Build index of existing entries by platform+post_id
    existing = {}
    for i, entry in enumerate(content_log):
        key = f"{entry.get('platform', 'web')}:{entry.get('post_id', entry.get('id', ''))}"
        existing[key] = i

    added = 0
    updated = 0

    for new in new_entries:
        key = f"{new['platform']}:{new['post_id']}"

        if key in existing:
            idx = existing[key]
            content_log[idx]["social_metrics"] = new["metrics"]
            content_log[idx]["social_metrics"]["fetched_at"] = new["imported_at"]
            updated += 1
        else:
            entry = {
                "id": f"social_{new['platform']}_{uuid.uuid4().hex[:8]}",
                "platform": new["platform"],
                "post_id": new["post_id"],
                "title": new.get("description", "")[:100],
                "description": new.get("description", ""),
                "keyword": new.get("keyword", ""),
                "site": new.get("site", new["platform"]),
                "format": new.get("post_type", "social_post"),
                "persona": new.get("persona"),
                "angle": new.get("angle"),
                "url": new.get("url", ""),
                "published_at": new["published_at"],
                "social_metrics": new["metrics"],
                "source": "social_import",
                "imported_at": new["imported_at"],
            }
            content_log.append(entry)
            existing[key] = len(content_log) - 1
            added += 1

    if not dry_run and (added or updated):
        with open(CONTENT_LOG, "w") as f:
            json.dump(content_log, f, indent=2)

    return {"added": added, "updated": updated, "total_log": len(content_log)}


def process_drop_folder(
    platform_filter: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Process all CSVs in the drop folder."""
    if not IMPORT_DIR.exists():
        IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        log.info("Created import dir: %s", IMPORT_DIR)
        return {"files": 0, "entries": 0, "added": 0, "updated": 0}

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = list(IMPORT_DIR.glob("*.csv"))
    if not csv_files:
        log.info("No CSV files in %s", IMPORT_DIR)
        return {"files": 0, "entries": 0, "added": 0, "updated": 0}

    all_entries = []
    files_processed = 0

    for csv_file in csv_files:
        entries = import_csv(csv_file, force_platform=platform_filter)
        if entries:
            all_entries.extend(entries)
            files_processed += 1

            if not dry_run:
                dest = PROCESSED_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{csv_file.name}"
                shutil.move(str(csv_file), str(dest))
                log.info("Moved %s -> %s", csv_file.name, dest.name)

    stats = merge_into_content_log(all_entries, dry_run=dry_run)
    stats["files"] = files_processed
    stats["entries"] = len(all_entries)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Social Data Importer (LLM-powered)")
    parser.add_argument("--file", help="Import a specific CSV file")
    parser.add_argument("--platform",
                        help="Force platform (skip auto-detection)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview import without saving")
    parser.add_argument("--list", action="store_true",
                        help="List files in drop folder")
    args = parser.parse_args()

    if args.list:
        csv_files = list(IMPORT_DIR.glob("*.csv")) if IMPORT_DIR.exists() else []
        if not csv_files:
            print(f"No CSV files in {IMPORT_DIR}")
        else:
            print(f"CSV files in {IMPORT_DIR}:")
            for f in csv_files:
                size = f.stat().st_size
                print(f"  {f.name} ({size:,} bytes)")
        return

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return
        entries = import_csv(filepath, force_platform=args.platform)
        if entries:
            stats = merge_into_content_log(entries, dry_run=args.dry_run)
            print(f"\nImported {len(entries)} entries: {stats['added']} new, {stats['updated']} updated")
            if args.dry_run:
                print("[DRY RUN] No changes saved")
                for e in entries[:5]:
                    print(f"  {e['platform']} | {e['post_id']} | {e['metrics']}")
        else:
            print("No entries imported (check format or API key)")
        return

    # Default: process drop folder
    stats = process_drop_folder(platform_filter=args.platform, dry_run=args.dry_run)
    print(f"Import complete: {stats['files']} files, {stats['entries']} entries")
    print(f"  Added: {stats['added']} | Updated: {stats['updated']} | Total log: {stats['total_log']}")
    if args.dry_run:
        print("[DRY RUN] No changes saved, no files moved")


if __name__ == "__main__":
    main()

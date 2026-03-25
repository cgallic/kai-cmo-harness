"""
Knowledge Cloner — Phase 1: Source Discovery.

Uses yt-dlp for YouTube channel listing, feedparser for podcasts,
and manual URL addition for articles/X Spaces/etc.
"""

import asyncio
import shutil
import re
from pathlib import Path
from typing import Optional

from .types import ExpertConfig, Source
from .utils import slugify, make_source_id, log, write_file


async def discover_youtube(config: ExpertConfig, channel_url: str, limit: int = 0) -> ExpertConfig:
    """Discover videos from a YouTube channel using yt-dlp."""
    if not shutil.which("yt-dlp"):
        log("ERROR: yt-dlp not found. Install it: pip install yt-dlp")
        return config

    # Normalize channel URL to get all videos
    url = channel_url.rstrip("/")
    if "/videos" not in url:
        url += "/videos"

    cmd = [
        "yt-dlp", "--flat-playlist", "--no-warnings",
        "--print", "%(id)s\t%(title)s\t%(upload_date)s\t%(duration)s\t%(view_count)s",
        url,
    ]

    log(f"Running yt-dlp to list channel videos...")
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip()
        log(f"yt-dlp error: {err}")
        return config

    lines = stdout.decode("utf-8", errors="replace").strip().split("\n")
    existing_ids = {s.id for s in config.sources}
    added = 0

    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue

        video_id, title, upload_date, duration_str, view_count_str = parts[:5]
        source_id = f"yt_{video_id}"

        if source_id in existing_ids:
            continue

        # Parse duration for priority
        try:
            duration = int(duration_str) if duration_str and duration_str != "NA" else 0
        except (ValueError, TypeError):
            duration = 0

        try:
            view_count = int(view_count_str) if view_count_str and view_count_str != "NA" else 0
        except (ValueError, TypeError):
            view_count = 0

        # Priority: long-form (>20min) = HIGH, medium (5-20min) = MEDIUM, short = LOW
        if duration > 1200:
            priority = "HIGH"
        elif duration > 300:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Format duration
        if duration:
            mins, secs = divmod(duration, 60)
            hours, mins = divmod(mins, 60)
            dur_str = f"{hours}h {mins}m" if hours else f"{mins}m {secs}s"
        else:
            dur_str = ""

        # Format date
        date_str = ""
        if upload_date and upload_date != "NA":
            try:
                date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            except (IndexError, ValueError):
                date_str = upload_date

        source = Source(
            id=source_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
            source_type="youtube",
            title=title.strip() if title != "NA" else "",
            date=date_str,
            duration=dur_str,
            priority=priority,
            status="discovered",
            view_count=view_count,
        )
        config.sources.append(source)
        existing_ids.add(source_id)
        added += 1

        if limit and added >= limit:
            break

    # Sort by priority then view count
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    config.sources.sort(key=lambda s: (priority_order.get(s.priority, 1), -s.view_count))

    log(f"Discovered {added} new videos ({len(config.sources)} total sources)")
    return config


def add_source(
    config: ExpertConfig,
    url: str,
    source_type: str = "article",
    title: str = "",
    priority: str = "MEDIUM",
) -> ExpertConfig:
    """Manually add a URL as a source."""
    source_id = make_source_id(source_type, url)

    # Check for duplicates
    if config.get_source(source_id):
        log(f"Source already exists: {source_id}")
        return config

    source = Source(
        id=source_id,
        url=url,
        source_type=source_type,
        title=title,
        priority=priority,
        status="discovered",
    )
    config.sources.append(source)
    log(f"Added source: {source_id} ({source_type})")
    return config


async def add_podcast_feed(config: ExpertConfig, rss_url: str) -> ExpertConfig:
    """Parse a podcast RSS feed and add episodes as sources."""
    try:
        import feedparser
    except ImportError:
        log("ERROR: feedparser not installed. Run: pip install feedparser")
        return config

    feed = feedparser.parse(rss_url)
    if not feed.entries:
        log(f"No episodes found in feed: {rss_url}")
        return config

    existing_ids = {s.id for s in config.sources}
    added = 0

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", "")

        # Try to get audio URL from enclosures
        audio_url = ""
        for enc in entry.get("enclosures", []):
            if "audio" in enc.get("type", ""):
                audio_url = enc.get("href", "")
                break

        source_id = make_source_id("podcast", link or title)
        if source_id in existing_ids:
            continue

        # Get duration if available
        duration = entry.get("itunes_duration", "")

        source = Source(
            id=source_id,
            url=audio_url or link,
            source_type="podcast",
            title=title,
            date=published[:10] if published else "",
            duration=duration,
            priority="HIGH",  # Podcasts are long-form, usually high value
            status="discovered",
        )
        config.sources.append(source)
        existing_ids.add(source_id)
        added += 1

    log(f"Discovered {added} podcast episodes ({len(config.sources)} total sources)")
    return config


async def discover_github_repo(
    config: ExpertConfig,
    repo_url: str,
    priority: str = "HIGH",
) -> ExpertConfig:
    """Add a GitHub repository as a source for procedural knowledge extraction.

    Supports formats: https://github.com/owner/repo, owner/repo
    """
    # Normalize URL
    url = repo_url.strip().rstrip("/")
    if not url.startswith("http"):
        # Assume owner/repo format
        url = f"https://github.com/{url}"

    # Extract owner/repo for ID
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)", url)
    if not match:
        log(f"Invalid GitHub URL: {repo_url}")
        return config

    owner_repo = match.group(1).rstrip("/")
    source_id = f"repo_{slugify(owner_repo)}"

    if config.get_source(source_id):
        log(f"Source already exists: {source_id}")
        return config

    # Try to get repo metadata via GitHub API (no auth needed for public repos)
    title = owner_repo
    date = ""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner_repo}",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("full_name", owner_repo)
                desc = data.get("description", "")
                if desc:
                    title = f"{title} — {desc}"
                date = (data.get("pushed_at") or data.get("updated_at") or "")[:10]
    except Exception:
        pass  # Metadata is optional — URL is enough

    source = Source(
        id=source_id,
        url=url,
        source_type="repo",
        title=title,
        date=date,
        priority=priority,
        status="discovered",
    )
    config.sources.append(source)
    log(f"Added repo source: {source_id} ({title})")
    return config


def import_local_file(
    config: ExpertConfig,
    file_path: str,
    source_type: str,
    expert_dir: Path,
) -> ExpertConfig:
    """Import a local file directly into the pipeline as a transcribed source."""
    src_path = Path(file_path)
    if not src_path.exists():
        log(f"File not found: {file_path}")
        return config

    source_id = make_source_id(source_type, src_path.stem)

    if config.get_source(source_id):
        log(f"Source already exists: {source_id}")
        return config

    # Copy file to raw/transcripts/
    dest_path = expert_dir / "raw" / "transcripts" / f"{source_id}.md"
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    content = src_path.read_text(encoding="utf-8")
    header = f"---\nsource_id: {source_id}\nsource_type: {source_type}\noriginal_file: {src_path.name}\n---\n\n"
    write_file(dest_path, header + content)

    source = Source(
        id=source_id,
        url=str(src_path),
        source_type=source_type,
        title=src_path.stem,
        priority="HIGH",
        status="transcribed",  # Skip transcription — already text
        transcript_path=str(dest_path.relative_to(expert_dir)),
    )
    config.sources.append(source)
    log(f"Imported {src_path.name} as {source_id} (status: transcribed)")
    return config

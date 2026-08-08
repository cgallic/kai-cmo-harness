from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def indexed_public(query: str, timeout: int = 20) -> list[dict]:
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote(query)
    request = urllib.request.Request(url, headers={"User-Agent": "KaiCommunityMonitor/2.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        root = ElementTree.fromstring(response.read())
    return [{
        "title": _clean(item.findtext("title") or ""),
        "original_text": _clean(item.findtext("description") or ""),
        "original_text_is_full": False,
        "url": (item.findtext("link") or "").strip(),
    } for item in root.findall("./channel/item")]


def youtube_comments(query: str, api_key: str, timeout: int = 20) -> list[dict]:
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY is required for direct comment monitoring")
    search_url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode({
        "part": "snippet", "type": "video", "maxResults": 10, "q": query, "key": api_key,
    })
    with urllib.request.urlopen(search_url, timeout=timeout) as response:
        videos = json.loads(response.read().decode("utf-8")).get("items", [])
    rows = []
    for video in videos:
        video_id = (video.get("id") or {}).get("videoId")
        if not video_id:
            continue
        comments_url = "https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode({
            "part": "snippet", "videoId": video_id, "maxResults": 100, "order": "time", "textFormat": "plainText", "key": api_key,
        })
        try:
            with urllib.request.urlopen(comments_url, timeout=timeout) as response:
                comments = json.loads(response.read().decode("utf-8")).get("items", [])
        except Exception:
            continue
        for comment in comments:
            snippet = (((comment.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {})
            comment_id = ((comment.get("snippet") or {}).get("topLevelComment") or {}).get("id") or ""
            text = snippet.get("textDisplay") or ""
            rows.append({
                "title": (video.get("snippet") or {}).get("title") or "YouTube comment",
                "original_text": text,
                "original_text_is_full": True,
                "url": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                "author": snippet.get("authorDisplayName") or "",
                "published_at": snippet.get("publishedAt") or "",
            })
    return rows


def file_drop(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("*.jsonl")) if directory.exists() else []:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("url") and row.get("original_text"):
                rows.append(row)
    return rows


def collect(profile: dict, *, env: dict[str, str], indexed_fetcher: Callable[[str], list[dict]] = indexed_public) -> tuple[list[dict], dict]:
    keywords = [str(x).casefold() for x in profile.get("keywords", [])]
    rows, status = [], {}
    for source in profile.get("sources", []):
        if not source.get("enabled"):
            status[source["id"]] = {"enabled": False, "items": 0, "errors": []}
            continue
        source_id, mode = source["id"], source["access_mode"]
        found, errors = [], []
        try:
            if source_id == "youtube_comments" and mode == "direct_api":
                for query in source.get("queries") or profile.get("keywords", [])[:3]:
                    found.extend(youtube_comments(str(query), env.get(source.get("env", "YOUTUBE_API_KEY"), "")))
            elif mode in {"authenticated_file_drop", "aeo_citation"}:
                found.extend(file_drop(Path(source.get("import_dir") or "")))
            elif mode == "indexed_public":
                for query in source.get("queries", []):
                    found.extend(indexed_fetcher(str(query)))
            else:
                status[source_id] = {"enabled": True, "delegated": True, "items": 0, "errors": []}
                continue
        except Exception as exc:
            errors.append(type(exc).__name__)
        for row in found:
            text = f"{row.get('title', '')} {row.get('original_text', '')}".casefold()
            if keywords and not any(term in text for term in keywords):
                continue
            row.update({"source": source_id, "source_mode": mode})
            rows.append(row)
        status[source_id] = {"enabled": True, "items": len(found), "accepted": sum(r.get("source") == source_id for r in rows), "errors": errors, "access_mode": mode}
    deduped = {row["url"]: row for row in rows if str(row.get("url", "")).startswith(("http://", "https://"))}
    return list(deduped.values()), status

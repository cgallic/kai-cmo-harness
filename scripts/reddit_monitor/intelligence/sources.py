from __future__ import annotations

import hashlib
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ATOM = {"a": "http://www.w3.org/2005/Atom"}


def _text(entry: ElementTree.Element, name: str) -> str:
    node = entry.find(f"a:{name}", ATOM)
    return "" if node is None or node.text is None else node.text.strip()


def collect_reddit_rss(profile: dict, *, timeout: int = 20) -> list[dict]:
    """Collect public submission RSS declared by a validated profile.

    This source is intentionally read-only and submission-only. It does not
    authenticate, fetch comments, or expose any Reddit write capability.
    """
    source = profile.get("sources", {}).get("reddit_rss", {})
    if not source.get("enabled", False):
        return []
    limit = min(max(int(source.get("posts_per_sub", 25)), 1), 100)
    items: list[dict] = []
    for subreddit in source.get("subreddits", []):
        clean = re.sub(r"^r/", "", str(subreddit).strip(), flags=re.IGNORECASE)
        if not clean or not re.fullmatch(r"[A-Za-z0-9_]+", clean):
            raise ValueError(f"invalid subreddit name: {subreddit}")
        url = f"https://www.reddit.com/r/{clean}/new.rss?limit={limit}"
        request = Request(url, headers={"User-Agent": "kai-reddit-intelligence/1.0 (read-only RSS)"})
        with urlopen(request, timeout=timeout) as response:
            root = ElementTree.fromstring(response.read())
        for entry in root.findall("a:entry", ATOM)[:limit]:
            link = entry.find("a:link", ATOM)
            item_url = "" if link is None else str(link.attrib.get("href", ""))
            stable_id = _text(entry, "id") or item_url
            items.append({
                "id": stable_id or hashlib.sha256(item_url.encode()).hexdigest(),
                "title": _text(entry, "title"),
                "body": _text(entry, "content"),
                "url": item_url,
                "subreddit": clean,
                "author": _text(entry, "author"),
                "published_at": _text(entry, "published") or _text(entry, "updated"),
            })
    return items

"""Pure helpers for local audits. No network, no filesystem — unit tested."""

from __future__ import annotations

import re
import struct
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

# Typical organic click-through rate by position, used only to weight
# visibility. It is a modeling assumption and must be labeled as one wherever
# "share of estimated clicks" is published.
CTR_BY_POSITION = {1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.07, 6: 0.05, 7: 0.04, 8: 0.03, 9: 0.03, 10: 0.025}

# A keyword with no Google Ads volume still gets a small weight so that
# zero-volume local phrases are not silently dropped from share of voice.
DEFAULT_VOLUME = 10

INSTAGRAM_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
INSTAGRAM_EPOCH_MS = 1314220021721


def normalize_domain(domain: str | None) -> str:
    d = (domain or "").strip().lower()
    return d[4:] if d.startswith("www.") else d


def share_of_clicks(serps: Iterable[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Estimated click share by domain, per group and overall.

    Each serp dict: ``keyword``, ``group``, ``volume`` (int|None), and
    ``organic`` — a list of ``(rank, domain)``. A keyword searched from several
    vantage points splits its volume evenly across those observations.
    """
    serps = list(serps)
    per_kw = Counter((s["keyword"], s.get("group", "all")) for s in serps)
    totals: dict[str, Counter] = defaultdict(Counter)
    for s in serps:
        group = s.get("group", "all")
        volume = s.get("volume") or DEFAULT_VOLUME
        weight = volume / per_kw[(s["keyword"], group)]
        for rank, domain in s.get("organic", [])[:10]:
            ctr = CTR_BY_POSITION.get(int(rank), 0.0)
            if not ctr:
                continue
            d = normalize_domain(domain)
            totals[group][d] += weight * ctr
            totals["ALL"][d] += weight * ctr
    out: dict[str, dict[str, float]] = {}
    for group, counter in totals.items():
        total = sum(counter.values())
        out[group] = {d: round(100 * v / total, 1) for d, v in counter.most_common()} if total else {}
    return out


def local_pack_counts(serps: Iterable[dict[str, Any]]) -> Counter:
    counter: Counter = Counter()
    for s in serps:
        for title in s.get("local_pack", []):
            counter[title] += 1
    return counter


def brand_rank(organic: Iterable[tuple[int, str]], brand_domain: str) -> int | None:
    target = normalize_domain(brand_domain)
    for rank, domain in organic:
        d = normalize_domain(domain)
        if d == target or d.endswith("." + target):
            return int(rank)
    return None


def webp_animation(data: bytes) -> dict[str, Any]:
    """Frame count, duration and canvas of a WebP. Non-animated → frames 0."""
    if len(data) < 16 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a WebP file")
    info: dict[str, Any] = {"bytes": len(data), "frames": 0, "duration_s": 0.0, "width": None, "height": None, "loop": None}
    i = 12
    duration_ms = 0
    while i + 8 <= len(data):
        chunk = data[i:i + 4]
        size = struct.unpack("<I", data[i + 4:i + 8])[0]
        body = i + 8
        if chunk == b"VP8X" and body + 10 <= len(data):
            info["width"] = int.from_bytes(data[body + 4:body + 7], "little") + 1
            info["height"] = int.from_bytes(data[body + 7:body + 10], "little") + 1
        elif chunk == b"ANIM" and body + 6 <= len(data):
            info["loop"] = struct.unpack("<H", data[body + 4:body + 6])[0]
        elif chunk == b"ANMF" and body + 15 <= len(data):
            info["frames"] += 1
            duration_ms += int.from_bytes(data[body + 12:body + 15], "little")
        i = body + size + (size & 1)
    info["duration_s"] = round(duration_ms / 1000, 2)
    return info


def email_auth_status(txt_root: list[str], txt_dmarc: list[str], txt_dkim: list[str]) -> dict[str, str]:
    spf = [t for t in txt_root if t.strip('"').lower().startswith("v=spf1")]
    dmarc = [t for t in txt_dmarc if t.strip('"').lower().startswith("v=dmarc1")]
    policy = ""
    if dmarc:
        m = re.search(r"p=([a-z]+)", dmarc[0].lower())
        policy = m.group(1) if m else ""
    return {
        "spf": "present" if spf else "missing",
        "dkim": "present" if any("p=" in t for t in txt_dkim) else "missing",
        "dmarc": f"p={policy}" if dmarc else "missing",
    }


def instagram_post_date(shortcode: str) -> str:
    n = 0
    for ch in shortcode:
        n = n * 64 + INSTAGRAM_ALPHABET.index(ch)
    ms = (n >> 23) + INSTAGRAM_EPOCH_MS
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def brand_mentions(text: str, patterns: dict[str, str]) -> dict[str, bool]:
    return {name: bool(re.search(p, text or "", re.IGNORECASE)) for name, p in patterns.items()}


def slug(text: str, limit: int = 60) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")[:limit] or "item"

#!/usr/bin/env python3
"""Expert-drift monitor — cloned experts keep publishing; their docs must not rot.

Every knowledge clone in ``knowledge/people/*-knowledge.md`` cites its sources.
This monitor derives a source registry from those citations, discovers RSS/Atom
feeds on the cited domains, and on each check reports items published since the
last run — candidate updates for the expert's doc. It NEVER edits knowledge
docs; it queues evidence for a human/agent to triage (same doctrine as
``competitor_monitor.py`` and the retro loop).

Workflow:
    python scripts/intel/expert_drift.py --init      # build/refresh registry from doc Sources sections
    python scripts/intel/expert_drift.py --discover  # probe cited domains for real feeds (network)
    python scripts/intel/expert_drift.py --check     # diff feeds vs state, write drift report (network)

Files:
    knowledge/people/_expert-sources.json   registry (committed; feeds only added when verified)
    data/intel/expert_drift_state.json      last-seen item ids per feed (runtime state)
    data/intel/expert-drift-report.md       latest check report

Run --check on whatever cadence fits (weekly cron is plenty). New items mean:
re-read, decide if the framework changed, update the doc's **Last verified:**
line either way.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = REPO_ROOT / "knowledge" / "people" / "_expert-sources.json"
STATE_FILE = REPO_ROOT / "data" / "intel" / "expert_drift_state.json"
REPORT_FILE = REPO_ROOT / "data" / "intel" / "expert-drift-report.md"

URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
# Domains that are citation infrastructure, not the expert's own publishing surface.
SKIP_DOMAINS = {
    "google.com", "www.google.com", "web.archive.org", "en.wikipedia.org",
    "www.amazon.com", "amazon.com", "hbr.org", "www.linkedin.com", "linkedin.com",
    "twitter.com", "x.com", "www.facebook.com", "podcasts.apple.com",
    "open.spotify.com", "www.nytimes.com", "nytimes.com",
}
FEED_CANDIDATES = ("/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/index.xml")
MAX_DOMAINS_PER_EXPERT = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return default
    return default


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


# ---------------------------------------------------------------- registry

def extract_source_domains(doc_text: str) -> list[str]:
    """Rank cited domains from a doc's ## Sources section, most-cited first."""
    match = re.search(r"^## Sources\b(.*)\Z", doc_text, re.MULTILINE | re.DOTALL)
    section = match.group(1) if match else ""
    counts: dict[str, int] = {}
    for url in URL_RE.findall(section):
        domain = urlparse(url).netloc.lower()
        if not domain or domain in SKIP_DOMAINS:
            continue
        counts[domain] = counts.get(domain, 0) + 1
    ranked = sorted(counts, key=lambda d: (-counts[d], d))
    return ranked[:MAX_DOMAINS_PER_EXPERT]


def build_registry(people_dir: Path, existing: dict | None = None) -> dict:
    """Build the registry from *-knowledge.md docs, preserving verified feeds."""
    existing = existing or {}
    registry: dict[str, dict] = {}
    for doc in sorted(people_dir.glob("*-knowledge.md")):
        slug = doc.name.removesuffix("-knowledge.md")
        domains = extract_source_domains(doc.read_text(errors="replace"))
        prior = existing.get(slug, {})
        registry[slug] = {
            "doc": f"knowledge/people/{doc.name}",
            "domains": domains,
            # feeds are only ever written by --discover after verification
            "feeds": prior.get("feeds", []),
        }
    return registry


# ---------------------------------------------------------------- feeds

def parse_feed(xml_text: str) -> list[dict]:
    """Parse RSS 2.0 or Atom into [{id, title, link, published}]. Empty on junk."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = []
    for node in root.iter("item"):  # RSS
        link = (node.findtext("link") or "").strip()
        guid = (node.findtext("guid") or link).strip()
        if not guid:
            continue
        items.append({
            "id": guid,
            "title": (node.findtext("title") or "").strip(),
            "link": link,
            "published": (node.findtext("pubDate") or "").strip(),
        })
    for node in root.iter("{http://www.w3.org/2005/Atom}entry"):  # Atom
        link_el = node.find("atom:link", ns)
        link = (link_el.get("href") if link_el is not None else "") or ""
        guid = (node.findtext("atom:id", default="", namespaces=ns) or link).strip()
        if not guid:
            continue
        items.append({
            "id": guid,
            "title": (node.findtext("atom:title", default="", namespaces=ns) or "").strip(),
            "link": link.strip(),
            "published": (node.findtext("atom:updated", default="", namespaces=ns) or "").strip(),
        })
    return items


def _http_get(url: str, timeout: int = 15) -> str | None:
    try:
        import requests

        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "kai-expert-drift/1.0"})
        if resp.status_code == 200 and resp.text:
            return resp.text
    except Exception:
        return None
    return None


def discover_feeds(registry: dict, fetch=_http_get) -> dict:
    """Probe each expert's domains for working feeds; keep only verified ones."""
    for slug, info in registry.items():
        verified: list[str] = []
        for domain in info.get("domains", []):
            for suffix in FEED_CANDIDATES:
                url = f"https://{domain}{suffix}"
                body = fetch(url)
                if body and parse_feed(body):
                    verified.append(url)
                    break  # one feed per domain is enough
        if verified:
            info["feeds"] = sorted(set(info.get("feeds", [])) | set(verified))
        info["last_discovered"] = _now()
    return registry


def check_drift(registry: dict, state: dict, fetch=_http_get) -> tuple[dict, dict]:
    """Fetch feeds, diff against state. Returns (new_items_by_slug, new_state).

    First sighting of a feed seeds state without reporting (everything is
    "new" on day one — that is backfill, not drift).
    """
    new_by_slug: dict[str, list[dict]] = {}
    for slug, info in registry.items():
        for feed_url in info.get("feeds", []):
            body = fetch(feed_url)
            if not body:
                continue
            items = parse_feed(body)
            if not items:
                continue
            seen = set(state.get(feed_url, {}).get("seen_ids", []))
            first_sighting = feed_url not in state
            fresh = [it for it in items if it["id"] not in seen]
            if fresh and not first_sighting:
                new_by_slug.setdefault(slug, []).extend(
                    {**it, "feed": feed_url} for it in fresh
                )
            state[feed_url] = {
                "seen_ids": sorted(seen | {it["id"] for it in items})[-500:],
                "last_checked": _now(),
            }
    return new_by_slug, state


def write_report(new_by_slug: dict, registry: dict, report_file: Path) -> str:
    lines = [
        "# Expert Drift Report",
        "",
        f"Generated: {_now()}",
        "",
    ]
    if not new_by_slug:
        lines.append("No new items since the last check. All monitored experts quiet.")
    for slug in sorted(new_by_slug):
        doc = registry.get(slug, {}).get("doc", "")
        lines.append(f"## {slug}")
        lines.append("")
        lines.append(f"Doc to re-verify: `{doc}`")
        lines.append("")
        for item in new_by_slug[slug]:
            title = item["title"] or item["link"] or item["id"]
            lines.append(f"- {title} — {item['link'] or item['id']} ({item['published'] or 'no date'})")
        lines.append("")
    lines.append(
        "Triage: re-read new items; if a framework changed, update the doc and "
        "its `**Last verified:**` line, then log a lesson if the old doctrine "
        "was wrong. Never bulk-rewrite from headlines alone."
    )
    report = "\n".join(lines) + "\n"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report)
    return report


# ---------------------------------------------------------------- CLI

def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor cloned experts' sources for new material")
    parser.add_argument("--init", action="store_true", help="build/refresh the source registry from knowledge docs")
    parser.add_argument("--discover", action="store_true", help="probe cited domains for working feeds (network)")
    parser.add_argument("--check", action="store_true", help="diff feeds against state and write the drift report (network)")
    args = parser.parse_args()
    if not (args.init or args.discover or args.check):
        parser.print_help()
        return 2

    registry = _load_json(REGISTRY_FILE, {})

    if args.init:
        registry = build_registry(REPO_ROOT / "knowledge" / "people", registry)
        _save_json(REGISTRY_FILE, registry)
        with_feeds = sum(1 for i in registry.values() if i.get("feeds"))
        print(f"Registry: {len(registry)} experts, {with_feeds} with verified feeds -> {REGISTRY_FILE}")

    if args.discover:
        if not registry:
            print("Registry empty — run --init first.", file=sys.stderr)
            return 1
        registry = discover_feeds(registry)
        _save_json(REGISTRY_FILE, registry)
        total = sum(len(i.get("feeds", [])) for i in registry.values())
        print(f"Discovery done: {total} verified feeds across {len(registry)} experts.")

    if args.check:
        if not registry:
            print("Registry empty — run --init (and --discover) first.", file=sys.stderr)
            return 1
        state = _load_json(STATE_FILE, {})
        new_by_slug, state = check_drift(registry, state)
        _save_json(STATE_FILE, state)
        write_report(new_by_slug, registry, REPORT_FILE)
        count = sum(len(v) for v in new_by_slug.values())
        print(f"Drift check: {count} new items across {len(new_by_slug)} experts -> {REPORT_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

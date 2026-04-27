#!/usr/bin/env python3
"""
Content gap audit.

Reads _global_*.jsonl citation events, filters to cited=false, aggregates per
(entity, tier, query), and writes a prioritized content-brief backlog to
~/.kai-marketing/gap-audit/YYYY-MM-DD.md.

Usage:
    python -m scripts.content.citations.gap_audit
    python -m scripts.content.citations.gap_audit --entity _global_kaicalls
    python -m scripts.content.citations.gap_audit --stdout
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

KAI_DIR = Path.home() / ".kai-marketing"
CITATIONS_DIR = KAI_DIR / "citations"
TARGETS_FILE = KAI_DIR / "citations-targets.json"
OUT_DIR = KAI_DIR / "gap-audit"

# Priority tiers for backlog sorting. Lower number = higher priority.
TIER_PRIORITY = {
    "comparison": 1,      # competitor-aware buyers
    "vertical": 1,        # high-intent SMB segment queries
    "pain": 1,            # problem-aware, purchase-intent
    "brand": 2,           # defensive — should already be cited
    "category": 2,        # generic, harder
    "legacy": 2,          # incumbent category queries
    "default": 3,
    "thought_leadership": 3,
}

PRIORITY_LABEL = {1: "P1", 2: "P2", 3: "P3"}

# Page-format hints per tier — advisory, not prescriptive.
TIER_PAGE_HINT = {
    "comparison": "Comparison page (e.g. /compare/{competitor}) with schema'd ProductComparison table.",
    "vertical": "Vertical landing page (e.g. /solutions/{industry}) with first sentence restating the query.",
    "pain": "Blog post or landing page answering the pain in its first 40 words.",
    "category": "Category hub page with atomic facts and a definition block in the lede.",
    "legacy": "Alternatives/replacement page targeting the incumbent by name.",
    "brand": "Brand audit needed — should already be cited. Check schema, homepage canonical, sitemaps.",
    "thought_leadership": "Thought-leadership article with original framework or data point.",
    "default": "Review tier assignment in citations-targets.json.",
}


def load_events(entity_filter: str | None = None) -> list[dict]:
    """Load all uncited events from _global_*.jsonl (or one file)."""
    events: list[dict] = []
    pattern = f"{entity_filter}.jsonl" if entity_filter else "_global_*.jsonl"
    for fp in sorted(CITATIONS_DIR.glob(pattern)):
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            if not e.get("cited"):
                events.append(e)
    return events


def load_own_domains() -> dict[str, set[str]]:
    """Map entity_id -> set of own match_domains (so we can strip them from source lists)."""
    own: dict[str, set[str]] = defaultdict(set)
    if not TARGETS_FILE.exists():
        return own
    targets = json.loads(TARGETS_FILE.read_text(encoding="utf-8"))
    for entity_id, cfg in targets.items():
        if not isinstance(cfg, dict):
            continue
        for dom in cfg.get("match_domains") or []:
            own[entity_id].add(dom.lower())
    # union all own domains — if any tracked article owns a domain, exclude
    # it from competitor counts regardless of which entity the event is from.
    universal: set[str] = set()
    for domains in own.values():
        universal |= domains
    own["_universal"] = universal
    return own


def load_sov_map() -> dict[str, dict[str, list[str]]]:
    """Map entity_id -> {bucket: [domains]} so we can recompute SOV against the
    live config instead of trusting the frozen sov_hits field on each event."""
    sov: dict[str, dict[str, list[str]]] = {}
    if not TARGETS_FILE.exists():
        return sov
    targets = json.loads(TARGETS_FILE.read_text(encoding="utf-8"))
    for entity_id, cfg in targets.items():
        if not isinstance(cfg, dict):
            continue
        sov[entity_id] = cfg.get("sov_domains") or {}
    return sov


def compute_sov(sources: list[str], sov_domains: dict[str, list[str]]) -> dict[str, int]:
    """Count SOV hits in a sources list against a {bucket: [domains]} map."""
    hits: Counter[str] = Counter()
    for url in sources:
        dom = extract_domain(url)
        if not dom:
            continue
        for bucket, domains in sov_domains.items():
            for sd in domains:
                if dom == sd or dom.endswith("." + sd):
                    hits[bucket] += 1
                    break
    return dict(hits)


def extract_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host.lstrip("www.") if host.startswith("www.") else host
    except Exception:
        return ""


def is_own(domain: str, url: str, own_domains: set[str]) -> bool:
    """Match either exact domain or path-prefixed domain (e.g. 'linkedin.com/in/cgallic')."""
    url_low = url.lower()
    for od in own_domains:
        if "/" in od:
            if od in url_low:
                return True
        elif domain == od or domain == od.lstrip("www."):
            return True
    return False


def aggregate(
    events: list[dict],
    own_domains: set[str],
    sov_map: dict[str, dict[str, list[str]]],
) -> list[dict]:
    """
    Group events by (entity_id, tier, query). Across providers, pick the richest
    event. Aggregate competitor domain counts across all events in the group.
    SOV is recomputed against live config, not the frozen sov_hits in the event.
    """
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for e in events:
        key = (e["entry_id"], e["tier"], e["query"])
        groups[key].append(e)

    backlog: list[dict] = []
    for (entity, tier, query), evs in groups.items():
        # Pick richest event (longest answer excerpt) for display.
        primary = max(evs, key=lambda x: len(x.get("answer_excerpt") or ""))

        sov_domains = sov_map.get(entity, {})

        # Aggregate competitor domains across every event for this query.
        domain_counter: Counter[str] = Counter()
        sov_counter: Counter[str] = Counter()
        for ev in evs:
            sources = ev.get("sources", []) or []
            for url in sources:
                dom = extract_domain(url)
                if not dom or is_own(dom, url, own_domains):
                    continue
                domain_counter[dom] += 1
            for bucket, n in compute_sov(sources, sov_domains).items():
                sov_counter[bucket] += n

        providers = sorted({ev["provider"] for ev in evs})

        backlog.append({
            "entity": entity,
            "tier": tier,
            "query": query,
            "providers": providers,
            "answer_excerpt": (primary.get("answer_excerpt") or "").strip(),
            "top_domains": domain_counter.most_common(5),
            "sov_hits": dict(sov_counter),
            "priority_bucket": TIER_PRIORITY.get(tier, 3),
        })
    return backlog


def sort_backlog(backlog: list[dict]) -> list[dict]:
    """Sort by priority bucket, then sov-hit count desc, then domain-count desc."""
    def sort_key(item: dict):
        sov_total = sum(item["sov_hits"].values())
        domain_total = sum(c for _, c in item["top_domains"])
        # ascending priority; descending competitor signal
        return (item["priority_bucket"], -sov_total, -domain_total, item["query"])
    return sorted(backlog, key=sort_key)


def group_by_priority(backlog: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for item in backlog:
        grouped[item["priority_bucket"]].append(item)
    return grouped


def render_markdown(backlog: list[dict], stats: dict) -> str:
    today = date.today().isoformat()
    lines: list[str] = []
    lines.append(f"# Content Gap Audit — {today}")
    lines.append("")
    lines.append(f"**Input:** {stats['total_events']} uncited events across "
                 f"{stats['entities']} entities (_global_*.jsonl).")
    lines.append(f"**Unique gaps:** {len(backlog)} (entity, tier, query) combos.")
    lines.append(f"**By priority:** P1={stats['p1']} · P2={stats['p2']} · P3={stats['p3']}")
    lines.append("")
    lines.append("Each gap lists what AI search is already answering, who they cite, "
                 "and a page-format suggestion. Review before handing to `/content-write`.")
    lines.append("")

    grouped = group_by_priority(backlog)
    for bucket in sorted(grouped.keys()):
        label = PRIORITY_LABEL[bucket]
        lines.append(f"## {label} — {len(grouped[bucket])} gaps")
        lines.append("")

        # Sub-group by entity for readability.
        by_entity: dict[str, list[dict]] = defaultdict(list)
        for item in grouped[bucket]:
            by_entity[item["entity"]].append(item)

        for entity, items in sorted(by_entity.items()):
            lines.append(f"### {entity}")
            lines.append("")
            for item in items:
                query = item["query"]
                tier = item["tier"]
                providers = ", ".join(item["providers"])
                lines.append(f"#### [{tier}] \"{query}\"")
                lines.append("")
                lines.append(f"- **Uncited by:** {providers}")

                if item["top_domains"]:
                    top = ", ".join(f"{d} ({n})" for d, n in item["top_domains"][:3])
                    lines.append(f"- **Who is cited:** {top}")
                else:
                    lines.append(f"- **Who is cited:** (no sources returned)")

                if item["sov_hits"]:
                    sov = ", ".join(f"{b}:{n}" for b, n in sorted(
                        item["sov_hits"].items(), key=lambda x: -x[1]))
                    lines.append(f"- **Tracked competitors present:** {sov}")

                hint = TIER_PAGE_HINT.get(tier, "")
                if hint:
                    lines.append(f"- **Build suggestion:** {hint}")

                excerpt = item["answer_excerpt"]
                if excerpt:
                    excerpt_snip = excerpt[:400].replace("\n", " ").strip()
                    if len(excerpt) > 400:
                        excerpt_snip += "…"
                    lines.append("")
                    lines.append(f"  > {excerpt_snip}")
                lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a prioritized content-brief backlog from uncited citation events."
    )
    parser.add_argument("--entity", help="Restrict to one global entity file "
                        "(e.g. _global_kaicalls).")
    parser.add_argument("--stdout", action="store_true",
                        help="Print to stdout instead of writing to file.")
    args = parser.parse_args()

    events = load_events(args.entity)
    if not events:
        print("No uncited events found. Run `kai-tracker citations --global` first.")
        return

    own_map = load_own_domains()
    own_domains = own_map["_universal"]
    sov_map = load_sov_map()

    entities = sorted({e["entry_id"] for e in events})
    stats = {"total_events": len(events), "entities": len(entities)}

    backlog = aggregate(events, own_domains, sov_map)
    backlog = sort_backlog(backlog)

    # Count priorities after aggregation (unique gaps, not raw events).
    pri_counts = Counter(item["priority_bucket"] for item in backlog)
    stats["p1"] = pri_counts.get(1, 0)
    stats["p2"] = pri_counts.get(2, 0)
    stats["p3"] = pri_counts.get(3, 0)

    md = render_markdown(backlog, stats)

    if args.stdout:
        print(md)
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{date.today().isoformat()}.md"
    out_file.write_text(md, encoding="utf-8")
    print(f"Gap audit written: {out_file}")
    print(f"  {len(events)} uncited events -> {len(backlog)} unique gaps "
          f"(P1={stats['p1']} P2={stats['p2']} P3={stats['p3']})")


if __name__ == "__main__":
    main()

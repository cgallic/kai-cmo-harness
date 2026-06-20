#!/usr/bin/env python3
"""
Kai CMO Harness - Brand Pulse
=============================
Multi-platform brand intelligence collector for /kai-brand-pulse.

The runner builds a platform-specific search plan, fetches search evidence
through SerpAPI when configured, archives raw responses, writes evidence
packets, and records deltas in SQLite.

Usage:
  python scripts/intel/brand_pulse.py "KaiCalls" --domain https://kaicalls.com
  python scripts/intel/brand_pulse.py "KaiCalls" --competitor Smith.ai --competitor Ruby
  python scripts/intel/brand_pulse.py "KaiCalls" --skip-fetch
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data" / "intel"
DEFAULT_DB_PATH = DATA_DIR / "brand_pulse.db"
USER_AGENT = "KaiCMOBrandPulse/1.0 (+https://github.com/cgallic/kai-cmo-harness)"

PLATFORM_WEIGHTS = {
    "web": 2,
    "news": 5,
    "youtube": 3,
    "x": 1,
    "linkedin": 2,
    "reddit": 2,
    "reviews": 4,
}

PLATFORM_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "web": [
        ("brand_footprint", '"{brand}"'),
        ("reviews", '"{brand}" review'),
        ("alternatives", '"{brand}" alternative'),
        ("pricing_objections", '"{brand}" pricing OR cost'),
    ],
    "news": [
        ("news_mentions", '"{brand}"'),
        ("category_news", '"{brand}" "{category}"'),
    ],
    "youtube": [
        ("youtube_mentions", 'site:youtube.com "{brand}"'),
        ("youtube_reviews", 'site:youtube.com "{brand}" review'),
    ],
    "x": [
        ("x_mentions", '(site:x.com OR site:twitter.com) "{brand}"'),
        ("x_objections", '(site:x.com OR site:twitter.com) "{brand}" (review OR alternative OR pricing)'),
    ],
    "linkedin": [
        ("linkedin_posts", 'site:linkedin.com/posts "{brand}"'),
        ("linkedin_company", 'site:linkedin.com/company "{brand}"'),
    ],
    "reddit": [
        ("reddit_mentions", 'site:reddit.com "{brand}"'),
        ("reddit_objections", 'site:reddit.com "{brand}" (review OR alternative OR pricing OR worth it)'),
    ],
    "reviews": [
        ("g2", 'site:g2.com "{brand}"'),
        ("capterra", 'site:capterra.com "{brand}"'),
        ("trustpilot", 'site:trustpilot.com "{brand}"'),
        ("clutch", 'site:clutch.co "{brand}"'),
        ("yelp", 'site:yelp.com "{brand}"'),
    ],
}

COMPETITOR_TEMPLATES: list[tuple[str, str, str]] = [
    ("web", "comparison", '"{brand}" vs "{competitor}"'),
    ("web", "competitor_alternative", '"{competitor}" alternative "{category}"'),
    ("reddit", "competitor_reddit", 'site:reddit.com "{competitor}" "{category}"'),
    ("reviews", "competitor_reviews", '"{competitor}" review'),
]

OWN_DOMAIN_TEMPLATES: list[tuple[str, str]] = [
    ("own_domain_entity", 'site:{domain} "{brand}"'),
    ("own_domain_category", 'site:{domain} "{category}"'),
]

POSITIVE_TERMS = {
    "best",
    "recommend",
    "recommended",
    "love",
    "loved",
    "great",
    "strong",
    "reliable",
    "solved",
    "easy",
    "useful",
    "fast",
}
NEGATIVE_TERMS = {
    "avoid",
    "bad",
    "broken",
    "complaint",
    "complaints",
    "expensive",
    "hate",
    "issue",
    "issues",
    "problem",
    "problems",
    "scam",
    "slow",
    "worse",
}
OBJECTION_TERMS = {
    "pricing": ("price", "pricing", "cost", "expensive", "cheap"),
    "support": ("support", "service", "help", "response"),
    "reliability": ("bug", "broken", "downtime", "slow", "latency", "issue"),
    "trust": ("scam", "legit", "worth it", "review", "complaint"),
    "alternatives": ("alternative", "vs", "versus", "competitor", "compare"),
}


@dataclass(frozen=True)
class BrandPulseQuery:
    platform: str
    intent: str
    entity: str
    query: str


@dataclass
class EvidenceItem:
    citation_id: str
    platform: str
    intent: str
    entity: str
    query: str
    title: str
    source_url: str
    snippet: str
    source_name: str
    position: int | None
    sentiment: str
    objection_tags: list[str]
    raw_artifact: str
    first_seen: bool = False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "brand"


def normalize_domain(domain: str) -> str:
    if not domain:
        return ""
    parsed = urllib.parse.urlparse(domain if "://" in domain else f"https://{domain}")
    return parsed.netloc.lower().removeprefix("www.")


def format_query(template: str, *, brand: str, category: str, competitor: str = "", domain: str = "") -> str:
    category_value = category or "category"
    return template.format(
        brand=brand,
        category=category_value,
        competitor=competitor,
        domain=domain,
    ).replace('"category"', category_value if category else '"category"')


def build_query_plan(
    brand: str,
    competitors: list[str] | None = None,
    *,
    category: str = "",
    domain: str = "",
) -> list[BrandPulseQuery]:
    """Build the multi-platform query plan for one brand pulse run."""
    competitors = competitors or []
    queries: list[BrandPulseQuery] = []

    for platform, templates in PLATFORM_TEMPLATES.items():
        for intent, template in templates:
            if "{category}" in template and not category:
                continue
            queries.append(
                BrandPulseQuery(
                    platform=platform,
                    intent=intent,
                    entity=brand,
                    query=format_query(template, brand=brand, category=category),
                )
            )

    normalized_domain = normalize_domain(domain)
    if normalized_domain:
        for intent, template in OWN_DOMAIN_TEMPLATES:
            if "{category}" in template and not category:
                continue
            queries.append(
                BrandPulseQuery(
                    platform="web",
                    intent=intent,
                    entity=brand,
                    query=format_query(
                        template,
                        brand=brand,
                        category=category,
                        domain=normalized_domain,
                    ),
                )
            )

    for competitor in competitors:
        for platform, intent, template in COMPETITOR_TEMPLATES:
            if "{category}" in template and not category:
                continue
            queries.append(
                BrandPulseQuery(
                    platform=platform,
                    intent=intent,
                    entity=competitor,
                    query=format_query(
                        template,
                        brand=brand,
                        category=category,
                        competitor=competitor,
                    ),
                )
            )

    return queries


def query_hash(query: BrandPulseQuery) -> str:
    raw = f"{query.platform}:{query.intent}:{query.entity}:{query.query}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def artifact_name(query: BrandPulseQuery) -> str:
    return f"{query.platform}-{query.intent}-{query_hash(query)}.json"


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_serpapi(query: BrandPulseQuery, api_key: str, *, limit: int = 10, timeout: int = 30) -> dict[str, Any]:
    params = {
        "engine": "google",
        "q": query.query,
        "api_key": api_key,
        "num": str(limit),
    }
    if query.platform == "news":
        params["tbm"] = "nws"

    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body)
            payload.setdefault("_request", {"query": query.query, "platform": query.platform})
            return payload
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return {
            "error": f"http_{exc.code}",
            "body": body[:2000],
            "_request": {"query": query.query, "platform": query.platform},
        }
    except Exception as exc:
        return {
            "error": str(exc),
            "_request": {"query": query.query, "platform": query.platform},
        }


def candidate_result_blocks(raw: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for key in ("organic_results", "news_results", "video_results", "top_stories", "inline_videos"):
        value = raw.get(key)
        if isinstance(value, list):
            blocks.extend(item for item in value if isinstance(item, dict))
    return blocks


def classify_sentiment(text: str) -> str:
    haystack = text.lower()
    positive = sum(1 for term in POSITIVE_TERMS if term in haystack)
    negative = sum(1 for term in NEGATIVE_TERMS if term in haystack)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    if positive and negative:
        return "mixed"
    return "neutral"


def classify_objections(text: str) -> list[str]:
    haystack = text.lower()
    tags = [
        tag
        for tag, terms in OBJECTION_TERMS.items()
        if any(term in haystack for term in terms)
    ]
    return sorted(set(tags))


def citation_id(platform: str, source_url: str, title: str) -> str:
    digest = hashlib.sha1(f"{source_url}:{title}".encode("utf-8")).hexdigest()[:10]
    return f"{platform}-{digest}"


def normalize_search_items(
    query: BrandPulseQuery,
    raw: dict[str, Any],
    raw_artifact: str,
    *,
    limit: int = 10,
) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for index, block in enumerate(candidate_result_blocks(raw)[:limit], start=1):
        title = str(block.get("title") or block.get("name") or "").strip()
        source_url = str(
            block.get("link")
            or block.get("source", {}).get("link")
            or block.get("url")
            or ""
        ).strip()
        snippet = str(
            block.get("snippet")
            or block.get("description")
            or block.get("summary")
            or ""
        ).strip()
        source_name = str(
            block.get("source")
            if isinstance(block.get("source"), str)
            else block.get("displayed_link")
            or urllib.parse.urlparse(source_url).netloc
            or ""
        ).strip()

        if not source_url and not title:
            continue

        combined = f"{title} {snippet}"
        items.append(
            EvidenceItem(
                citation_id=citation_id(query.platform, source_url or title, title),
                platform=query.platform,
                intent=query.intent,
                entity=query.entity,
                query=query.query,
                title=title or "(untitled result)",
                source_url=source_url,
                snippet=snippet,
                source_name=source_name,
                position=int(block.get("position") or index),
                sentiment=classify_sentiment(combined),
                objection_tags=classify_objections(combined),
                raw_artifact=raw_artifact,
            )
        )
    return items


def _init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS brand_pulse_mentions (
            mention_key TEXT PRIMARY KEY,
            brand_slug TEXT NOT NULL,
            platform TEXT NOT NULL,
            source_url TEXT,
            title TEXT,
            snippet TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            last_run_id TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_brand_pulse_brand
            ON brand_pulse_mentions(brand_slug, platform);
        """
    )
    conn.close()


def mention_key(item: EvidenceItem) -> str:
    base = item.source_url or item.title
    return hashlib.sha1(f"{item.platform}:{base}:{item.title}".encode("utf-8")).hexdigest()


def record_deltas(
    evidence: list[EvidenceItem],
    *,
    brand_slug: str,
    run_id: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    """Store seen mentions and mark evidence items that are new this run."""
    _init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    now = utc_now_iso()
    new_count = 0
    by_platform: dict[str, int] = {}

    for item in evidence:
        key = mention_key(item)
        existing = conn.execute(
            "SELECT mention_key FROM brand_pulse_mentions WHERE mention_key = ?",
            (key,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE brand_pulse_mentions
                SET last_seen = ?, last_run_id = ?, snippet = ?
                WHERE mention_key = ?
                """,
                (now, run_id, item.snippet, key),
            )
            item.first_seen = False
        else:
            conn.execute(
                """
                INSERT INTO brand_pulse_mentions
                (mention_key, brand_slug, platform, source_url, title, snippet, first_seen, last_seen, last_run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    brand_slug,
                    item.platform,
                    item.source_url,
                    item.title,
                    item.snippet,
                    now,
                    now,
                    run_id,
                ),
            )
            item.first_seen = True
            new_count += 1
            by_platform[item.platform] = by_platform.get(item.platform, 0) + 1

    conn.commit()
    conn.close()
    return {"new_mentions": new_count, "new_by_platform": by_platform}


def platform_stats(evidence: list[EvidenceItem]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for item in evidence:
        row = stats.setdefault(
            item.platform,
            {
                "count": 0,
                "new": 0,
                "positive": 0,
                "neutral": 0,
                "mixed": 0,
                "negative": 0,
                "objection_tags": {},
                "pulse_score": 0,
            },
        )
        row["count"] += 1
        row["new"] += 1 if item.first_seen else 0
        row[item.sentiment] = row.get(item.sentiment, 0) + 1
        row["pulse_score"] += PLATFORM_WEIGHTS.get(item.platform, 1)
        for tag in item.objection_tags:
            row["objection_tags"][tag] = row["objection_tags"].get(tag, 0) + 1
    return stats


def top_citations(evidence: list[EvidenceItem], *, limit: int = 5) -> list[EvidenceItem]:
    weighted = sorted(
        evidence,
        key=lambda item: (
            item.first_seen,
            PLATFORM_WEIGHTS.get(item.platform, 1),
            -(item.position or 99),
        ),
        reverse=True,
    )
    return weighted[:limit]


def generate_content_angles(
    brand: str,
    competitors: list[str],
    evidence: list[EvidenceItem],
) -> list[dict[str, Any]]:
    angles: list[dict[str, Any]] = []
    objection_to_items: dict[str, list[EvidenceItem]] = {}
    for item in evidence:
        for tag in item.objection_tags:
            objection_to_items.setdefault(tag, []).append(item)

    for tag, items in sorted(objection_to_items.items(), key=lambda pair: len(pair[1]), reverse=True):
        angles.append(
            {
                "angle": f"Answer {tag} objections with proof",
                "why": f"{len(items)} evidence item(s) mentioned {tag}-related language.",
                "citations": [item.citation_id for item in items[:3]],
            }
        )

    for competitor in competitors:
        cited = [
            item
            for item in evidence
            if competitor.lower() in f"{item.title} {item.snippet} {item.query}".lower()
        ]
        angles.append(
            {
                "angle": f"Publish {brand} vs {competitor} comparison",
                "why": "Comparison demand is worth owning when public results already connect the two brands.",
                "citations": [item.citation_id for item in cited[:3]],
            }
        )

    if not angles:
        angles.append(
            {
                "angle": f"Create a source-backed {brand} proof page",
                "why": "The pulse found too little public evidence to mine objections confidently.",
                "citations": [],
            }
        )

    return angles[:10]


def generate_surround_sound_actions(
    evidence: list[EvidenceItem],
    stats: dict[str, dict[str, Any]],
) -> list[str]:
    actions: list[str] = []
    missing = [platform for platform in PLATFORM_TEMPLATES if stats.get(platform, {}).get("count", 0) == 0]
    if missing:
        actions.append(
            "Create citation targets on missing surfaces: " + ", ".join(missing[:6]) + "."
        )
    if any(item.platform == "reviews" and item.sentiment == "negative" for item in evidence):
        actions.append("Build a review-response and proof refresh queue for negative review-site results.")
    if any(item.platform == "reddit" and item.objection_tags for item in evidence):
        actions.append("Feed Reddit objections into /kai-reddit-listen keywords and reply guardrails.")
    if any(item.platform in {"news", "web"} for item in evidence):
        actions.append("Turn third-party mentions into AEO citations for /kai-surround-sound.")
    if not actions:
        actions.append("Run a live search pass before recommending off-site placement work.")
    return actions


def write_platform_packet(path: Path, platform: str, items: list[EvidenceItem]) -> None:
    lines = [
        f"# {platform.title()} Evidence Packet",
        "",
        "Use this packet as the source material for the platform analyzer. Do not add claims that are not cited here.",
        "",
        "| Citation | Sentiment | Title | Source | Objections |",
        "|----------|-----------|-------|--------|------------|",
    ]
    for item in items:
        source = f"[{item.source_name or item.source_url}]({item.source_url})" if item.source_url else item.source_name
        objections = ", ".join(item.objection_tags) if item.objection_tags else "-"
        lines.append(
            f"| {item.citation_id} | {item.sentiment} | {item.title} | {source} | {objections} |"
        )
        if item.snippet:
            lines.append(f"| | | {item.snippet} | | |")

    lines.extend(
        [
            "",
            "## Analyzer Prompt",
            "",
            "Summarize only this platform. Extract repeated claims, objections, proof gaps, and content angles. Cite every claim with citation ids from this packet.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_outputs(
    out_dir: Path,
    *,
    brand: str,
    competitors: list[str],
    domain: str,
    run_id: str,
    generated_at: str,
    evidence: list[EvidenceItem],
    query_plan: list[BrandPulseQuery],
    data_gaps: list[dict[str, str]],
    delta_summary: dict[str, Any],
) -> dict[str, Any]:
    stats = platform_stats(evidence)
    angles = generate_content_angles(brand, competitors, evidence)
    actions = generate_surround_sound_actions(evidence, stats)
    pulse_score = sum(row["pulse_score"] for row in stats.values())

    platforms_dir = out_dir / "platforms"
    by_platform: dict[str, list[EvidenceItem]] = {}
    for item in evidence:
        by_platform.setdefault(item.platform, []).append(item)
    for platform in PLATFORM_TEMPLATES:
        write_platform_packet(platforms_dir / f"{platform}.md", platform, by_platform.get(platform, []))

    summary_lines = [
        f"# Brand Pulse - {brand}",
        "",
        f"Generated: {generated_at}",
        f"Run ID: {run_id}",
        f"Domain: {domain or 'not provided'}",
        f"Competitors: {', '.join(competitors) if competitors else 'none provided'}",
        "",
        "## Topline",
        "",
        f"- Evidence items: {len(evidence)}",
        f"- New mentions since last tracked run: {delta_summary.get('new_mentions', 0)}",
        f"- Weighted pulse score: {pulse_score}",
        f"- Query count: {len(query_plan)}",
        f"- Data gaps: {len(data_gaps)}",
        "",
        "## Platform Summary",
        "",
        "| Platform | Evidence | New | Tone | Top Objections | Pulse |",
        "|----------|----------|-----|------|----------------|-------|",
    ]
    for platform in PLATFORM_TEMPLATES:
        row = stats.get(platform, {})
        tone = f"+{row.get('positive', 0)} / ~{row.get('neutral', 0)} / -{row.get('negative', 0)}"
        objections = row.get("objection_tags", {})
        top_objections = ", ".join(
            tag for tag, _ in sorted(objections.items(), key=lambda pair: pair[1], reverse=True)[:3]
        ) or "-"
        summary_lines.append(
            f"| {platform} | {row.get('count', 0)} | {row.get('new', 0)} | {tone} | {top_objections} | {row.get('pulse_score', 0)} |"
        )

    summary_lines.extend(["", "## Highest-Signal Citations", ""])
    for item in top_citations(evidence):
        link = f"[{item.title}]({item.source_url})" if item.source_url else item.title
        summary_lines.append(f"- {item.citation_id}: {link} ({item.platform}, {item.sentiment})")

    summary_lines.extend(["", "## Recommended Actions", ""])
    for action in actions:
        summary_lines.append(f"- {action}")

    summary_lines.extend(
        [
            "",
            "## Next Kai Moves",
            "",
            "- Feed objection tags into `/kai-write`, `/kai-social`, and `/kai-cold-outreach` briefs.",
            "- Feed third-party citation gaps into `/kai-surround-sound` after own-domain agent readiness passes.",
            "- Feed Reddit-specific patterns into `/kai-reddit-listen` profiles.",
            "- Re-run weekly with the same brand slug to track new mentions.",
            "",
        ]
    )
    (out_dir / "_brand-pulse.md").write_text("\n".join(summary_lines), encoding="utf-8")

    angles_lines = [
        f"# Content Angles - {brand}",
        "",
        "| Angle | Why | Citations |",
        "|-------|-----|-----------|",
    ]
    for angle in angles:
        citations = ", ".join(angle["citations"]) if angle["citations"] else "-"
        angles_lines.append(f"| {angle['angle']} | {angle['why']} | {citations} |")
    (out_dir / "_content-angles.md").write_text("\n".join(angles_lines), encoding="utf-8")

    objections_lines = [
        f"# Objection Mining - {brand}",
        "",
        "| Citation | Platform | Tags | Evidence |",
        "|----------|----------|------|----------|",
    ]
    objection_items = [item for item in evidence if item.objection_tags]
    for item in objection_items:
        link = f"[{item.title}]({item.source_url})" if item.source_url else item.title
        objections_lines.append(
            f"| {item.citation_id} | {item.platform} | {', '.join(item.objection_tags)} | {link} |"
        )
    if not objection_items:
        objections_lines.append("| - | - | - | No objection-tagged evidence found in this run. |")
    (out_dir / "_objection-mining.md").write_text("\n".join(objections_lines), encoding="utf-8")

    surround_lines = [f"# Surround-Sound Actions - {brand}", ""]
    for action in actions:
        surround_lines.append(f"- {action}")
    (out_dir / "_surround-sound-actions.md").write_text("\n".join(surround_lines), encoding="utf-8")

    monitoring_lines = [
        f"# Weekly Delta Monitoring - {brand}",
        "",
        "Run the same command weekly. The SQLite store marks first-seen mentions and keeps last-seen timestamps.",
        "",
        "```bash",
        f"python scripts/intel/brand_pulse.py \"{brand}\" --out \"{out_dir.as_posix()}\"",
        "```",
        "",
        "For cron, point output to a dated folder and keep the default database at `data/intel/brand_pulse.db`.",
        "",
    ]
    (out_dir / "_monitoring-plan.md").write_text("\n".join(monitoring_lines), encoding="utf-8")

    gaps_lines = [
        f"# Data Gaps - {brand}",
        "",
        "| Source | Blocks | Handling |",
        "|--------|--------|----------|",
    ]
    for gap in data_gaps:
        gaps_lines.append(f"| {gap['source']} | {gap['blocks']} | {gap['handling']} |")
    if not data_gaps:
        gaps_lines.append("| - | - | No collection gaps recorded. |")
    (out_dir / "_data-gaps.md").write_text("\n".join(gaps_lines), encoding="utf-8")

    return {
        "stats": stats,
        "content_angles": angles,
        "surround_sound_actions": actions,
        "pulse_score": pulse_score,
    }


def write_wiki_update(wiki_dir: Path, *, brand_slug: str, summary_path: Path) -> Path:
    wiki_dir.mkdir(parents=True, exist_ok=True)
    target = wiki_dir / f"brand-pulse-{brand_slug}.md"
    body = [
        f"# Brand Pulse - {brand_slug}",
        "",
        f"Latest packet: {summary_path}",
        f"Updated: {utc_now_iso()}",
        "",
        "Use the linked packet as the citation-backed source of truth for brand intelligence updates.",
        "",
    ]
    target.write_text("\n".join(body), encoding="utf-8")
    return target


def data_gap(source: str, blocks: str, handling: str) -> dict[str, str]:
    return {"source": source, "blocks": blocks, "handling": handling}


def run_brand_pulse(
    brand: str,
    *,
    competitors: list[str] | None = None,
    category: str = "",
    domain: str = "",
    out_dir: Path | None = None,
    db_path: Path = DEFAULT_DB_PATH,
    limit_per_query: int = 10,
    max_queries: int = 60,
    skip_fetch: bool = False,
    wiki_dir: Path | None = None,
) -> dict[str, Any]:
    competitors = competitors or []
    brand_slug = slugify(brand)
    generated_at = utc_now_iso()
    run_id = f"{brand_slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    out_dir = out_dir or (REPO_ROOT / "workspace" / "brand-pulse" / run_id)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    query_plan = build_query_plan(brand, competitors, category=category, domain=domain)
    if max_queries and len(query_plan) > max_queries:
        query_plan = query_plan[:max_queries]

    save_json(raw_dir / "query-plan.json", [asdict(query) for query in query_plan])

    data_gaps: list[dict[str, str]] = []
    evidence: list[EvidenceItem] = []
    api_key = os.getenv("SERPAPI_API_KEY", "")

    if skip_fetch:
        data_gaps.append(
            data_gap(
                "search_provider",
                "Live web, news, social, Reddit, and review evidence",
                "Query plan was archived only because --skip-fetch was used.",
            )
        )
    elif not api_key:
        for platform in PLATFORM_TEMPLATES:
            data_gaps.append(
                data_gap(
                    f"serpapi:{platform}",
                    f"Live {platform} search evidence",
                    "Set SERPAPI_API_KEY or import a source export before making platform claims.",
                )
            )
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, max(1, len(query_plan)))) as executor:
            future_map = {
                executor.submit(fetch_serpapi, query, api_key, limit=limit_per_query): query
                for query in query_plan
            }
            for future in concurrent.futures.as_completed(future_map):
                query = future_map[future]
                raw_path = raw_dir / artifact_name(query)
                try:
                    raw = future.result()
                except Exception as exc:
                    raw = {"error": str(exc), "_request": asdict(query)}
                save_json(raw_path, raw)

                if raw.get("error"):
                    data_gaps.append(
                        data_gap(
                            f"serpapi:{query.platform}:{query.intent}",
                            query.query,
                            f"Fetch failed: {raw.get('error')}. Do not infer results for this query.",
                        )
                    )
                    continue
                items = normalize_search_items(
                    query,
                    raw,
                    str(raw_path.relative_to(REPO_ROOT) if raw_path.is_relative_to(REPO_ROOT) else raw_path),
                    limit=limit_per_query,
                )
                evidence.extend(items)
                if not items:
                    data_gaps.append(
                        data_gap(
                            f"serpapi:{query.platform}:{query.intent}",
                            query.query,
                            "No usable result items returned. Treat as absence of observed evidence, not proof of absence.",
                        )
                    )

    delta_summary = record_deltas(
        evidence,
        brand_slug=brand_slug,
        run_id=run_id,
        db_path=db_path,
    )

    analysis = write_markdown_outputs(
        out_dir,
        brand=brand,
        competitors=competitors,
        domain=domain,
        run_id=run_id,
        generated_at=generated_at,
        evidence=evidence,
        query_plan=query_plan,
        data_gaps=data_gaps,
        delta_summary=delta_summary,
    )

    dataset = {
        "run_id": run_id,
        "generated_at": generated_at,
        "brand": brand,
        "brand_slug": brand_slug,
        "domain": domain,
        "category": category,
        "competitors": competitors,
        "query_plan": [asdict(query) for query in query_plan],
        "evidence": [asdict(item) for item in evidence],
        "data_gaps": data_gaps,
        "delta_summary": delta_summary,
        "analysis": analysis,
        "artifacts": {
            "summary": str(out_dir / "_brand-pulse.md"),
            "platform_packets": str(out_dir / "platforms"),
            "raw": str(raw_dir),
        },
    }
    save_json(out_dir / "brand-pulse-data.json", dataset)

    if wiki_dir:
        wiki_path = write_wiki_update(
            wiki_dir,
            brand_slug=brand_slug,
            summary_path=out_dir / "_brand-pulse.md",
        )
        dataset["artifacts"]["wiki_update"] = str(wiki_path)
        save_json(out_dir / "brand-pulse-data.json", dataset)

    return dataset


def parse_competitors(values: list[str] | None, csv_value: str = "") -> list[str]:
    competitors: list[str] = []
    for value in values or []:
        competitors.extend(part.strip() for part in value.split(",") if part.strip())
    if csv_value:
        competitors.extend(part.strip() for part in csv_value.split(",") if part.strip())
    seen: set[str] = set()
    unique: list[str] = []
    for competitor in competitors:
        key = competitor.lower()
        if key not in seen:
            seen.add(key)
            unique.append(competitor)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a multi-platform brand pulse")
    parser.add_argument("brand", nargs="?", help="Brand to monitor")
    parser.add_argument("--brand", dest="brand_flag", help="Brand to monitor")
    parser.add_argument("--domain", default="", help="Canonical brand domain")
    parser.add_argument("--category", default="", help="Category or buying query to monitor")
    parser.add_argument("--competitor", action="append", help="Competitor name. Repeat or comma-separate.")
    parser.add_argument("--competitors", default="", help="Comma-separated competitors")
    parser.add_argument("--out", help="Output folder")
    parser.add_argument("--db", help="SQLite delta database path")
    parser.add_argument("--limit-per-query", type=int, default=10)
    parser.add_argument("--max-queries", type=int, default=60)
    parser.add_argument("--skip-fetch", action="store_true", help="Archive query plan without live search fetches")
    parser.add_argument("--wiki-dir", help="Optional wiki folder to update with latest packet pointer")
    parser.add_argument("--json", action="store_true", help="Print machine-readable run summary")
    args = parser.parse_args()

    brand = args.brand_flag or args.brand
    if not brand:
        parser.error("brand is required")

    dataset = run_brand_pulse(
        brand,
        competitors=parse_competitors(args.competitor, args.competitors),
        category=args.category,
        domain=args.domain,
        out_dir=Path(args.out) if args.out else None,
        db_path=Path(args.db) if args.db else DEFAULT_DB_PATH,
        limit_per_query=args.limit_per_query,
        max_queries=args.max_queries,
        skip_fetch=args.skip_fetch,
        wiki_dir=Path(args.wiki_dir) if args.wiki_dir else None,
    )

    if args.json:
        print(json.dumps({
            "run_id": dataset["run_id"],
            "summary": dataset["artifacts"]["summary"],
            "evidence_count": len(dataset["evidence"]),
            "data_gap_count": len(dataset["data_gaps"]),
            "new_mentions": dataset["delta_summary"].get("new_mentions", 0),
        }, indent=2))
    else:
        print(f"Brand pulse written: {dataset['artifacts']['summary']}")
        print(f"Evidence: {len(dataset['evidence'])}   Gaps: {len(dataset['data_gaps'])}")
        print(f"New mentions: {dataset['delta_summary'].get('new_mentions', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

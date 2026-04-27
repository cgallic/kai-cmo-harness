#!/usr/bin/env python3
"""One-shot seeder: backfill this week's published content into ~/.kai-marketing/content-log.jsonl."""
from __future__ import annotations

import json
from pathlib import Path

KAI_DIR = Path.home() / ".kai-marketing"
LOG = KAI_DIR / "content-log.jsonl"
KAI_DIR.mkdir(parents=True, exist_ok=True)


def entry(
    entry_id: str,
    url: str,
    title: str,
    keyword: str,
    site: str,
    fmt: str,
    published_at: str,
    angle: str,
    persona: str,
    four_us: int,
    notes: str = "",
) -> dict:
    return {
        "id": entry_id,
        "url": url,
        "keyword": keyword,
        "title": title,
        "platform": fmt,
        "site": site,
        "format": fmt,
        "published_at": published_at,
        "four_us_score": four_us,
        "persona": persona,
        "angle": angle,
        "notes": notes,
        "performance_30d": None,
        "source_run": "manual_seed_2026-04-14",
        "proposal_id": None,
        "module_set": [],
        "artifact_refs": {},
    }


entries = [
    entry(
        entry_id="kaicalls-20260415-100000-linkedin",
        url="https://www.linkedin.com/pulse/your-answering-service-costs-more-than-phone-bill-heres-connor-gallic-in2he/",
        title="Your Answering Service Costs More Than Your Phone Bill. Here's What Replaced It.",
        keyword="AI answering service replaces human answering service",
        site="kaicalls",
        fmt="linkedin",
        published_at="2026-04-15T14:00:00+00:00",
        angle="Pain-to-solution — small-business owner paying $1,500-3K/mo for a human service that still drops calls; KaiCalls at $69/mo + phone-first admin",
        persona="Overwhelmed Owner",
        four_us=16,
        notes="First-comment CTA: 'DM me TRIAL' — 7-day free trial walkthrough offer",
    ),
    entry(
        entry_id="connorgallic-20260415-120000-devto",
        url="https://dev.to/connor_gallic/your-ai-isnt-personal-mine-has-156926-memories-of-me-582g",
        title="Your AI Isn't Personal. Mine Has 156,926 Memories of Me.",
        keyword="personal AI data layer architecture",
        site="connorgallic",
        fmt="devto",
        published_at="2026-04-15T16:00:00+00:00",
        angle="Reframe — personal AI is a data-layer problem, not a model problem; backed by live-DB numbers from the brain event log",
        persona="Builder / AI engineer",
        four_us=16,
        notes="Scheduled to publish Apr 15 12 PM ET. Written for Dev.to; extends the X thread about brain architecture.",
    ),
    entry(
        entry_id="connorgallic-20260414-120000-linkedin-perplexity",
        url="https://www.linkedin.com/pulse/linkedin-gets-structural-priority-perplexitys-ranking-connor-gallic-9cd3e/",
        title="LinkedIn Gets Structural Priority in Perplexity's Ranking",
        keyword="LinkedIn Perplexity trust pool hardcoded",
        site="connorgallic",
        fmt="linkedin",
        published_at="2026-04-14T16:00:00+00:00",
        angle="Industry piece — Perplexity's Trust Pool, L3 Reranker, and why LinkedIn posts are structurally advantaged in AI search",
        persona="Content creator / GEO-curious founder",
        four_us=15,
        notes="Posted on LinkedIn instead of X — doubled as its own GEO experiment (LinkedIn hardcoded Tier 1 per the piece's thesis)",
    ),
    entry(
        entry_id="connorgallic-20260414-150000-x-brain",
        url="https://x.com/connorgallic/status/2043570662493598201",
        title="I Built a Personal Intelligence System That Ingests Everything I Do Across 3 Machines. Here's the Architecture.",
        keyword="personal intelligence system architecture brain",
        site="connorgallic",
        fmt="x",
        published_at="2026-04-14T19:00:00+00:00",
        angle="Architecture-first X long-form — the 80-line write gate, 30 ingestion scripts, 18 MCP tools, local embeddings on the 3090",
        persona="Builder / AI engineer",
        four_us=16,
        notes="Technical deep dive — Dev.to piece 'Your AI Isn't Personal' is the higher-order thesis; this X thread is the implementation proof",
    ),
    entry(
        entry_id="connorgallic-20260412-devto-13of14",
        url="https://dev.to/connor_gallic/i-asked-claude-to-audit-my-dashboard-13-of-14-integrations-were-fake-1c2o",
        title="I Asked Claude to Audit My Dashboard. 13 of 14 Integrations Were Fake.",
        keyword="codebase audit AI Claude MeetKai integrations",
        site="connorgallic",
        fmt="devto",
        published_at="2026-04-12T14:00:00+00:00",
        angle="Technical walkthrough — MeetKai dashboard codebase audit, 25-30% complete finding, gateway-first architecture decision",
        persona="Builder / founder",
        four_us=15,
        notes="Published Apr 12. Monday LinkedIn 'A Feature That Succeeds and Does Nothing' is the founder-angle companion piece.",
    ),
]

if LOG.exists():
    existing_ids = {json.loads(l)["id"] for l in LOG.read_text().splitlines() if l.strip()}
else:
    existing_ids = set()

with open(LOG, "a", encoding="utf-8") as f:
    for e in entries:
        if e["id"] in existing_ids:
            print(f"[skip] {e['id']} already in log")
            continue
        f.write(json.dumps(e) + "\n")
        print(f"[seed] {e['id']}  {e['site']}/{e['format']}  {e['title'][:50]}...")

print()
print(f"Content log: {LOG}")
print(f"Total entries now: {sum(1 for _ in LOG.read_text().splitlines() if _.strip())}")

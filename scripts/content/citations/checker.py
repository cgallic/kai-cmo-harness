#!/usr/bin/env python3
"""
AI citation checker.

Runs target queries against AI search engines (Perplexity Sonar, Anthropic web
search, OpenAI web search) and checks whether a tracked article is cited as a
source. Writes citation events to the per-article citations sidecar.

Environment (any subset):
    PERPLEXITY_API_KEY  — pplx-... from https://www.perplexity.ai/settings/api
    ANTHROPIC_API_KEY   — sk-ant-... (web-search tool requires claude-3-5-sonnet
                          or newer)
    OPENAI_API_KEY      — sk-... (Responses API with web_search_preview)

Usage:
    # Check all tracked articles against their configured queries
    python -m scripts.content.citations.checker

    # Check a single article
    python -m scripts.content.citations.checker --id connorgallic-20260414-...

    # Pass queries inline
    python -m scripts.content.citations.checker --id <id> \
        --query "best AI answering service" --query "Smith.ai alternatives"

Configuration:
    Each tracked article can declare target_queries + match_domains in
    ~/.kai-marketing/citations-targets.json, keyed by content-log entry id:

    {
      "connorgallic-20260414-...": {
        "queries": ["what replaces an answering service", "AI receptionist cost"],
        "match_domains": ["kaicalls.com", "connorgallic.com", "linkedin.com/in/connor"],
        "match_terms": ["Connor Gallic", "KaiCalls"]
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

KAI_DIR = Path.home() / ".kai-marketing"
CITATIONS_DIR = KAI_DIR / "citations"
TARGETS_FILE = KAI_DIR / "citations-targets.json"
LOG_JSONL = KAI_DIR / "content-log.jsonl"

PPLX_URL = "https://api.perplexity.ai/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/responses"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _post_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={**headers, "content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned {e.code}: {body_text}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"{url} unreachable: {e.reason}") from None


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _contains_match(text: str, terms: list[str]) -> list[str]:
    haystack = (text or "").lower()
    hits = []
    for t in terms:
        if t and t.lower() in haystack:
            hits.append(t)
    return hits


def _url_matches_domains(url: str, domains: list[str]) -> bool:
    host = _domain(url)
    if not host:
        return False
    for d in domains:
        dn = d.lower().strip().removeprefix("www.")
        if not dn:
            continue
        if dn in host or host in dn:
            return True
    return False


# ── Search providers ────────────────────────────────────────────────────────


def query_perplexity(query: str, api_key: str) -> dict:
    """Ask Perplexity Sonar. Returns {answer, sources: [urls]}."""
    body = {
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
        "return_citations": True,
    }
    resp = _post_json(PPLX_URL, {"authorization": f"Bearer {api_key}"}, body)
    answer = ""
    try:
        answer = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        answer = ""
    # Perplexity returns sources in `citations` (list of URLs) or in search_results.
    sources: list[str] = []
    if isinstance(resp.get("citations"), list):
        sources.extend(str(u) for u in resp["citations"])
    if isinstance(resp.get("search_results"), list):
        for r in resp["search_results"]:
            if isinstance(r, dict) and r.get("url"):
                sources.append(r["url"])
    return {"answer": answer, "sources": sources, "raw": resp}


def query_anthropic(query: str, api_key: str) -> dict:
    """Ask Claude with the web_search tool. Returns {answer, sources: [urls]}."""
    body = {
        "model": "claude-3-5-sonnet-latest",
        "max_tokens": 1024,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        "messages": [{"role": "user", "content": query}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    resp = _post_json(ANTHROPIC_URL, headers, body, timeout=90)
    answer_parts: list[str] = []
    sources: list[str] = []
    for block in resp.get("content", []):
        t = block.get("type")
        if t == "text":
            answer_parts.append(block.get("text", ""))
        elif t == "tool_use" and block.get("name") == "web_search":
            # tool_use input is the query sent; not useful for citations
            pass
        elif t == "web_search_tool_result":
            for r in block.get("content", []) or []:
                if isinstance(r, dict) and r.get("url"):
                    sources.append(r["url"])
    # Claude also emits citation annotations inside text blocks
    for block in resp.get("content", []):
        for cit in block.get("citations", []) or []:
            if isinstance(cit, dict) and cit.get("url"):
                sources.append(cit["url"])
    return {"answer": "\n".join(answer_parts), "sources": sources, "raw": resp}


def query_openai(query: str, api_key: str) -> dict:
    """Ask OpenAI with web_search_preview. Returns {answer, sources: [urls]}."""
    body = {
        "model": "gpt-4o-mini",
        "tools": [{"type": "web_search_preview"}],
        "input": query,
    }
    headers = {"authorization": f"Bearer {api_key}"}
    resp = _post_json(OPENAI_URL, headers, body, timeout=90)
    answer_parts: list[str] = []
    sources: list[str] = []
    for item in resp.get("output", []) or []:
        t = item.get("type")
        if t == "message":
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text":
                    answer_parts.append(c.get("text", ""))
                    for ann in c.get("annotations", []) or []:
                        if ann.get("type") == "url_citation" and ann.get("url"):
                            sources.append(ann["url"])
        elif t == "web_search_call":
            # The actual search call; sources appear in annotations above
            pass
    return {"answer": "\n".join(answer_parts), "sources": sources, "raw": resp}


# ── Orchestration ───────────────────────────────────────────────────────────


def _load_targets() -> dict:
    if not TARGETS_FILE.exists():
        return {}
    try:
        return json.loads(TARGETS_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _load_log() -> list[dict]:
    if not LOG_JSONL.exists():
        return []
    entries: list[dict] = []
    for line in LOG_JSONL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _append_event(entry_id: str, event: dict) -> Path:
    CITATIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = CITATIONS_DIR / f"{entry_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
    return path


def _flatten_queries(queries: list | dict) -> list[tuple[str, str]]:
    """Return [(tier, query), ...]. Supports both flat list and tiered dict."""
    out: list[tuple[str, str]] = []
    if isinstance(queries, list):
        for q in queries:
            if isinstance(q, str) and q.strip():
                out.append(("default", q.strip()))
    elif isinstance(queries, dict):
        for tier, qlist in queries.items():
            if isinstance(qlist, list):
                for q in qlist:
                    if isinstance(q, str) and q.strip():
                        out.append((str(tier), q.strip()))
    return out


def _score_sov(sources: list[str], sov_domains: dict[str, list[str]]) -> dict[str, int]:
    """For each competitor bucket, count matching sources."""
    hits: dict[str, int] = {}
    for bucket, domains in (sov_domains or {}).items():
        count = 0
        for src in sources:
            if _url_matches_domains(src, domains):
                count += 1
        if count:
            hits[bucket] = count
    return hits


def check_target(
    entry_id: str,
    queries: list | dict,
    match_domains: list[str],
    match_terms: list[str],
    providers: list[str],
    keys: dict,
    entry_url: str = "",
    sov_domains: dict[str, list[str]] | None = None,
    tier_filter: list[str] | None = None,
) -> list[dict]:
    """Run every query against every provider. Record per-query citation events.

    Handles both flat query lists (per-article) and tiered query dicts (global brand).
    Adds share-of-voice (SOV) tracking when sov_domains is provided.
    """
    events: list[dict] = []
    sov_domains = sov_domains or {}
    flat = _flatten_queries(queries)
    if tier_filter:
        flat = [(t, q) for (t, q) in flat if t in tier_filter]

    for tier, query in flat:
        for provider in providers:
            fn = {"perplexity": query_perplexity, "anthropic": query_anthropic, "openai": query_openai}.get(provider)
            if fn is None:
                continue
            key = keys.get(provider)
            if not key:
                print(f"  [{provider}] skipped — no API key", file=sys.stderr)
                continue
            try:
                result = fn(query, key)
            except RuntimeError as e:
                print(f"  [{provider}] error: {e}", file=sys.stderr)
                continue

            sources = [s for s in (result.get("sources") or []) if isinstance(s, str)]
            answer = result.get("answer", "") or ""

            url_hit = any(
                entry_url and (s.rstrip("/") == entry_url.rstrip("/") or _domain(s) == _domain(entry_url))
                for s in sources
            )
            domain_hits = [s for s in sources if _url_matches_domains(s, match_domains)]
            term_hits = _contains_match(answer, match_terms)
            sov_hits = _score_sov(sources, sov_domains)

            cited = bool(url_hit or domain_hits or term_hits)

            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "entry_id": entry_id,
                "tier": tier,
                "provider": provider,
                "query": query,
                "cited": cited,
                "url_match": url_hit,
                "domain_match_count": len(domain_hits),
                "term_match_count": len(term_hits),
                "domain_matches": domain_hits,
                "term_matches": term_hits,
                "sov_hits": sov_hits,
                "sources": sources[:20],
                "answer_excerpt": answer[:400],
            }
            _append_event(entry_id, event)
            events.append(event)

            marker = "[CITED]" if cited else "[ --- ]"
            sov_str = " sov=" + ",".join(f"{k}:{v}" for k, v in sov_hits.items()) if sov_hits else ""
            print(
                f"  {marker} {provider:<11} [{tier:<14}] {query!r:<55}  "
                f"srcs={len(sources):>2} dom={len(domain_hits)} term={len(term_hits)}{sov_str}"
            )
    return events


# Kept for backwards compatibility with any callers still using the old name.
def check_article(
    entry_id: str,
    entry_url: str,
    queries: list[str],
    match_domains: list[str],
    match_terms: list[str],
    providers: list[str],
    keys: dict,
) -> list[dict]:
    return check_target(
        entry_id=entry_id,
        queries=queries,
        match_domains=match_domains,
        match_terms=match_terms,
        providers=providers,
        keys=keys,
        entry_url=entry_url,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI citation checks against tracked content")
    parser.add_argument("--id", help="Restrict to a single entry id (article or _global_*)")
    parser.add_argument("--global", dest="global_only", action="store_true",
                        help="Only run _global_* brand entities (skip per-article entries)")
    parser.add_argument("--entity", action="append", default=[],
                        help="Run a specific entity by key, e.g. _global_kaicalls (repeatable)")
    parser.add_argument("--tier", action="append", default=[],
                        help="Filter tiered queries to one or more tiers (brand, comparison, category, pain, vertical, legacy, ...)")
    parser.add_argument("--query", action="append", default=[], help="Inline query (repeatable). Uses configured targets if omitted")
    parser.add_argument(
        "--providers",
        default="perplexity,anthropic,openai",
        help="Comma-separated providers to run (default: all configured)",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    keys = {
        "perplexity": os.environ.get("PERPLEXITY_API_KEY", "").strip(),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        "openai": os.environ.get("OPENAI_API_KEY", "").strip(),
    }
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    if not any(keys.get(p) for p in providers):
        sys.exit("No API keys available for requested providers. Set PERPLEXITY_API_KEY, ANTHROPIC_API_KEY, and/or OPENAI_API_KEY.")

    targets = _load_targets()
    # Strip internal meta keys
    target_keys = [k for k in targets.keys() if not k.startswith("_meta")]
    global_keys = [k for k in target_keys if k.startswith("_global_")]

    entries = _load_log()
    entries_by_id = {e.get("id"): e for e in entries if e.get("id")}

    # Figure out which ids to run
    if args.entity:
        ids = list(args.entity)
    elif args.id:
        ids = [args.id]
    elif args.global_only:
        ids = global_keys
    else:
        ids = global_keys + [k for k in entries_by_id.keys() if k]

    if not ids:
        sys.exit("No entities to check. Configure targets in ~/.kai-marketing/citations-targets.json or publish content.")

    all_events: list[dict] = []
    for entry_id in ids:
        target = targets.get(entry_id, {})
        is_global = entry_id.startswith("_global_")
        entry = entries_by_id.get(entry_id, {})

        if args.query:
            queries: list | dict = list(args.query)
        else:
            queries = target.get("queries") or []

        if not queries:
            print(f"[skip] {entry_id} — no queries defined (configure in {TARGETS_FILE} or pass --query)")
            continue

        match_domains = list(target.get("match_domains") or [])
        match_terms = list(target.get("match_terms") or [])
        sov_domains = target.get("sov_domains") or {}
        entry_url = "" if is_global else (entry.get("url", "") or "")

        if not match_domains and entry_url:
            match_domains = [_domain(entry_url)]

        label = target.get("label") or entry_id
        url_note = "" if is_global else f"  url={entry_url or '?'}"
        print(f"-> {entry_id}  [{label}]{url_note}")

        events = check_target(
            entry_id=entry_id,
            queries=queries,
            match_domains=match_domains,
            match_terms=match_terms,
            providers=providers,
            keys=keys,
            entry_url=entry_url,
            sov_domains=sov_domains,
            tier_filter=args.tier or None,
        )
        all_events.extend(events)

    if args.format == "json":
        print(json.dumps(all_events, indent=2, default=str))
        return

    cited = [e for e in all_events if e["cited"]]
    print()
    print(f"Ran {len(all_events)} checks. Citations detected: {len(cited)}")

    # SOV rollup across all events
    sov_totals: dict[str, int] = {}
    for e in all_events:
        for k, v in (e.get("sov_hits") or {}).items():
            sov_totals[k] = sov_totals.get(k, 0) + v
    if sov_totals:
        print()
        print("Share-of-voice (sources seen across all queries):")
        for bucket, count in sorted(sov_totals.items(), key=lambda kv: -kv[1]):
            print(f"  {bucket:<20} {count}")

    if cited:
        print()
        print("Positive citations:")
        for e in cited:
            print(f"  {e['provider']:<11} {e['entry_id']:<26} [{e.get('tier', 'default'):<14}] q={e['query']!r}")


if __name__ == "__main__":
    main()

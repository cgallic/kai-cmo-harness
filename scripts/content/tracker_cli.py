#!/usr/bin/env python3
"""
kai-tracker — unified content performance tracker.

Subcommands:
    pull-devto                Fetch Dev.to stats for every matching content-log entry
    linkedin --id <id>        Record LinkedIn metrics (interactive if no stats passed)
    citations [--id <id>]     Run AI citation checks (Perplexity / Anthropic / OpenAI)
    report                    Enriched performance report (GSC + GA4 + Dev.to + LinkedIn + citations)
    targets --id <id> ...     Manage citation targets for a tracked article

Data locations:
    ~/.kai-marketing/content-log.jsonl           — append-only publish log
    ~/.kai-marketing/metrics/{id}.json           — per-article platform metrics
    ~/.kai-marketing/citations/{id}.jsonl        — per-article citation events
    ~/.kai-marketing/citations-targets.json      — queries + match rules per article
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.self_improvement.grades import get_grade  # noqa: E402

KAI_DIR = Path.home() / ".kai-marketing"
METRICS_DIR = KAI_DIR / "metrics"
CITATIONS_DIR = KAI_DIR / "citations"
TARGETS_FILE = KAI_DIR / "citations-targets.json"
LOG_JSONL = KAI_DIR / "content-log.jsonl"


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


def _load_metrics(entry_id: str) -> dict:
    p = METRICS_DIR / f"{entry_id}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {}


def _load_citations(entry_id: str) -> list[dict]:
    p = CITATIONS_DIR / f"{entry_id}.jsonl"
    if not p.exists():
        return []
    out: list[dict] = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _load_targets() -> dict:
    if not TARGETS_FILE.exists():
        return {}
    try:
        return json.loads(TARGETS_FILE.read_text())
    except json.JSONDecodeError:
        return {}


def _save_targets(targets: dict) -> None:
    TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TARGETS_FILE.write_text(json.dumps(targets, indent=2))


# ── Subcommands ─────────────────────────────────────────────────────────────


def cmd_pull_devto(args: argparse.Namespace) -> int:
    forwarded = ["--format", args.format]
    if args.dry_run:
        forwarded.append("--dry-run")
    return subprocess.call([sys.executable, "-m", "scripts.content.platforms.devto", *forwarded])


def cmd_linkedin(args: argparse.Namespace) -> int:
    forwarded = ["--id", args.id]
    if args.url:
        forwarded += ["--url", args.url]
    for flag, value in [
        ("--impressions", args.impressions),
        ("--reactions", args.reactions),
        ("--comments", args.comments),
        ("--reshares", args.reshares),
        ("--profile-views", args.profile_views),
        ("--followers-gained", args.followers_gained),
        ("--dms", args.dms),
    ]:
        if value is not None:
            forwarded += [flag, str(value)]
    if args.notes:
        forwarded += ["--notes", args.notes]
    if args.interactive:
        forwarded.append("--interactive")
    return subprocess.call([sys.executable, "-m", "scripts.content.platforms.linkedin_entry", *forwarded])


def cmd_citations(args: argparse.Namespace) -> int:
    forwarded: list[str] = []
    if args.id:
        forwarded += ["--id", args.id]
    if args.global_only:
        forwarded.append("--global")
    for ent in args.entity or []:
        forwarded += ["--entity", ent]
    for tier in args.tier or []:
        forwarded += ["--tier", tier]
    for q in args.query or []:
        forwarded += ["--query", q]
    if args.providers:
        forwarded += ["--providers", args.providers]
    forwarded += ["--format", args.format]
    return subprocess.call([sys.executable, "-m", "scripts.content.citations.checker", *forwarded])


def cmd_targets(args: argparse.Namespace) -> int:
    targets = _load_targets()
    if args.list:
        print(json.dumps(targets, indent=2))
        return 0

    if not args.id:
        print("--id is required (or use --list)", file=sys.stderr)
        return 2

    t = targets.setdefault(args.id, {"queries": [], "match_domains": [], "match_terms": []})
    if args.query:
        t["queries"] = args.query
    if args.add_query:
        t["queries"] = list({*t.get("queries", []), *args.add_query})
    if args.domain:
        t["match_domains"] = args.domain
    if args.add_domain:
        t["match_domains"] = list({*t.get("match_domains", []), *args.add_domain})
    if args.term:
        t["match_terms"] = args.term
    if args.add_term:
        t["match_terms"] = list({*t.get("match_terms", []), *args.add_term})

    _save_targets(targets)
    print(json.dumps({args.id: t}, indent=2))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    entries = _load_log()
    if args.site:
        entries = [e for e in entries if e.get("site") == args.site]
    if not entries:
        print(json.dumps({"message": "No published content found."}) if args.format == "json" else "No published content found.")
        return 0

    # Enrich with performance_check (GSC + GA4) when available
    pull_gsc_data = pull_ga4_data = evaluate_performance = None
    try:
        from scripts.self_improvement.performance_check import (  # type: ignore[import-not-found]
            evaluate_performance as _evp,
            pull_gsc_data as _gsc,
            pull_ga4_data as _ga4,
        )
        pull_gsc_data, pull_ga4_data, evaluate_performance = _gsc, _ga4, _evp
    except Exception:
        pass

    results: list[dict] = []
    for e in entries:
        row = dict(e)
        entry_id = e.get("id") or ""
        url = e.get("url") or ""
        keyword = e.get("keyword") or ""
        site = e.get("site") or ""

        if pull_gsc_data and pull_ga4_data and evaluate_performance and url and keyword:
            try:
                gsc = pull_gsc_data(url, keyword, site)
                ga4 = pull_ga4_data(url, site)
                ev = evaluate_performance(e, gsc, ga4)
                row["performance_30d"] = ev.get("grade")
                row["gsc"] = gsc
                row["ga4"] = ga4
            except Exception as err:
                row["performance_error"] = str(err)

        metrics = _load_metrics(entry_id)
        if metrics:
            row["platforms"] = metrics.get("platforms", {})
            row["metrics_updated"] = metrics.get("last_updated")

        citations = _load_citations(entry_id)
        if citations:
            cited = [c for c in citations if c.get("cited")]
            provider_set: set[str] = set()
            for c in citations:
                prov = c.get("provider")
                if prov:
                    provider_set.add(str(prov))
            providers = sorted(provider_set)
            row["citations"] = {
                "checks": len(citations),
                "cited_count": len(cited),
                "providers_seen": providers,
                "latest": citations[-1] if citations else None,
            }

        results.append(row)

    if args.format == "json":
        print(json.dumps(results, indent=2, default=str))
        return 0

    # get_grade tolerates performance_30d as dict, legacy string, or None
    winners = [r for r in results if get_grade(r) == "winner"]
    avg = [r for r in results if get_grade(r) == "average"]
    under = [r for r in results if get_grade(r) == "underperformer"]
    pending = [r for r in results if get_grade(r) is None]

    print(f"Content Performance Report — {len(results)} pieces")
    print(f"  Winners: {len(winners)}  |  Average: {len(avg)}  |  Under: {len(under)}  |  Pending: {len(pending)}")
    print()
    for r in results[-20:]:
        icon_map = {"winner": "+", "average": "~", "underperformer": "-"}
        icon = icon_map.get(get_grade(r) or "", "?")
        plat = r.get("platforms", {})
        devto = plat.get("devto") or {}
        li = (plat.get("linkedin") or {}).get("latest") or {}
        cits = r.get("citations") or {}

        parts = []
        if devto.get("page_views_count"):
            parts.append(f"devto={devto['page_views_count']}v/{devto.get('public_reactions_count', 0)}r")
        if li.get("impressions"):
            parts.append(f"li={li['impressions']}imp/{li.get('reactions', 0)}r/{li.get('dms', 0)}dm")
        if cits.get("cited_count") is not None:
            parts.append(f"cits={cits['cited_count']}/{cits['checks']}")
        extras = "  ".join(parts)
        print(f"  [{icon}] {r.get('id', '?'):<38} {r.get('keyword', ''):<40}  {extras}")

    return 0


# ── Entrypoint ──────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kai-tracker", description="Unified content performance tracker")
    sub = p.add_subparsers(dest="command", required=True)

    dt = sub.add_parser("pull-devto", help="Fetch Dev.to stats for matching content-log entries")
    dt.add_argument("--dry-run", action="store_true")
    dt.add_argument("--format", choices=["text", "json"], default="text")
    dt.set_defaults(func=cmd_pull_devto)

    li = sub.add_parser("linkedin", help="Record LinkedIn metrics for a content-log entry")
    li.add_argument("--id", required=True)
    li.add_argument("--url")
    li.add_argument("--impressions", type=int)
    li.add_argument("--reactions", type=int)
    li.add_argument("--comments", type=int)
    li.add_argument("--reshares", type=int)
    li.add_argument("--profile-views", type=int, dest="profile_views")
    li.add_argument("--followers-gained", type=int, dest="followers_gained")
    li.add_argument("--dms", type=int)
    li.add_argument("--notes", default="")
    li.add_argument("--interactive", action="store_true")
    li.set_defaults(func=cmd_linkedin)

    ci = sub.add_parser("citations", help="Run AI citation checks")
    ci.add_argument("--id")
    ci.add_argument("--global", dest="global_only", action="store_true",
                    help="Only run _global_* brand entities")
    ci.add_argument("--entity", action="append", default=[],
                    help="Run a specific entity key (e.g. _global_kaicalls)")
    ci.add_argument("--tier", action="append", default=[],
                    help="Filter to specific tier(s): brand, comparison, category, pain, vertical, legacy, thought_leadership")
    ci.add_argument("--query", action="append", default=[])
    ci.add_argument("--providers", default="perplexity,anthropic,openai")
    ci.add_argument("--format", choices=["text", "json"], default="text")
    ci.set_defaults(func=cmd_citations)

    tg = sub.add_parser("targets", help="Manage citation targets (queries, match domains, match terms)")
    tg.add_argument("--id")
    tg.add_argument("--list", action="store_true")
    tg.add_argument("--query", action="append", default=[], help="Replace query list")
    tg.add_argument("--add-query", action="append", default=[], help="Append to query list")
    tg.add_argument("--domain", action="append", default=[], help="Replace match_domains")
    tg.add_argument("--add-domain", action="append", default=[], help="Append to match_domains")
    tg.add_argument("--term", action="append", default=[], help="Replace match_terms")
    tg.add_argument("--add-term", action="append", default=[], help="Append to match_terms")
    tg.set_defaults(func=cmd_targets)

    rp = sub.add_parser("report", help="Enriched performance report")
    rp.add_argument("--site")
    rp.add_argument("--format", choices=["text", "json"], default="text")
    rp.set_defaults(func=cmd_report)

    return p


def main() -> None:
    args = build_parser().parse_args()
    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()

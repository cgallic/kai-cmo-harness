#!/usr/bin/env python3
"""Refresh queue: which existing pages to fix first, and how.

Reads a Search Console query x page export and ranks pages by estimated click
upside from two fixable patterns:

  ctr_gap            ranks 1-7 but earns far less than the site's own CTR at
                     that position -> rewrite title and meta description
  striking_distance  ranks 8-20 with real impressions -> align the title,
                     add the missing sections, add internal links

Brand queries are split out first (they inflate CTR and are not winnable by
editing a page). The expected-CTR curve is calibrated on the site's own
non-brand data where a position bucket has enough impressions, and falls back
to a labeled heuristic elsewhere. Upside is an estimate, never a forecast:
the queue orders work, and ``refresh_tracker`` measures what it actually did.

    python -m scripts.seo.striking_distance --data data/seo/example-q3.json \
        --brand "example,example co" --site example.com \
        --out workspace/seo-refresh/example

Writes ``refresh-queue.json`` and ``refresh-queue.md`` to --out.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from scripts.seo.gsc_data import is_brand, load_rows, parse_brand_terms
except ImportError:  # executed as a file from inside scripts/seo/
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.seo.gsc_data import is_brand, load_rows, parse_brand_terms

# Heuristic non-brand organic CTR by rounded position. Used only where the site
# lacks enough of its own impressions at that position. Deliberately
# conservative; reported as "heuristic" wherever it is used.
HEURISTIC_CTR = {
    1: 0.25, 2: 0.14, 3: 0.09, 4: 0.065, 5: 0.05, 6: 0.04, 7: 0.032,
    8: 0.026, 9: 0.022, 10: 0.019,
    **{p: 0.012 for p in range(11, 16)},
    **{p: 0.007 for p in range(16, 21)},
}
CALIBRATION_MIN_IMPRESSIONS = 1000
CTR_GAP_RATIO = 0.5          # earning under half the expected CTR = title/snippet problem
CTR_GAP_MAX_POSITION = 7.5
STRIKING_MAX_POSITION = 20.5

STOPWORDS = {
    "a", "an", "and", "the", "for", "of", "in", "on", "to", "near", "me", "my",
    "how", "what", "is", "are", "best", "with", "do", "does", "you", "your", "vs",
}


def _bucket(position: float) -> int:
    return max(1, min(20, int(round(position))))


def calibrate_ctr_curve(rows: Iterable[Dict[str, Any]],
                        min_impressions: int = CALIBRATION_MIN_IMPRESSIONS) -> Dict[int, Dict[str, Any]]:
    """Expected CTR per position 1-20 from the site's own non-brand rows.

    A bucket is trusted only when it has enough impressions spread over at
    least three pages, none holding more than half of them; otherwise one
    under-performing page would set its own benchmark and hide its own gap.
    The curve is then made non-increasing from the bottom up, so a weak bucket
    never drags the expectation for higher positions down.
    """
    clicks: Dict[int, float] = defaultdict(float)
    imps: Dict[int, float] = defaultdict(float)
    by_page: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if 0 < r["position"] <= STRIKING_MAX_POSITION:
            b = _bucket(r["position"])
            clicks[b] += r["clicks"]
            imps[b] += r["impressions"]
            by_page[b][r["page"]] += r["impressions"]
    raw: Dict[int, tuple] = {}
    for pos in range(1, 21):
        pages = by_page[pos]
        spread = len(pages) >= 3 and max(pages.values()) <= 0.5 * imps[pos] if pages else False
        if imps[pos] >= min_impressions and spread:
            raw[pos] = (clicks[pos] / imps[pos], "site")
        else:
            raw[pos] = (HEURISTIC_CTR[pos], "heuristic")
    curve: Dict[int, Dict[str, Any]] = {}
    floor = 0.0
    for pos in range(20, 0, -1):
        ctr, source = raw[pos]
        ctr = max(ctr, floor)
        floor = ctr
        curve[pos] = {"ctr": round(ctr, 5), "source": source, "impressions": int(imps[pos])}
    return dict(sorted(curve.items()))


def target_position(position: float) -> int:
    """A realistic next rung, not #1: 8-12 -> 5, 13-20 -> 8."""
    return 5 if position <= 12.5 else 8


def classify(row: Dict[str, Any], curve: Dict[int, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    pos, ctr, imps = row["position"], row["ctr"], row["impressions"]
    if pos <= 0:
        return None
    if pos <= CTR_GAP_MAX_POSITION:
        expected = curve[_bucket(pos)]["ctr"]
        if ctr < expected * CTR_GAP_RATIO:
            return {"type": "ctr_gap", "expected_ctr": expected,
                    "upside_clicks": imps * (expected - ctr)}
        return None
    if pos <= STRIKING_MAX_POSITION:
        tgt = target_position(pos)
        expected = curve[tgt]["ctr"]
        return {"type": "striking_distance", "target_position": tgt, "expected_ctr": expected,
                "upside_clicks": max(0.0, imps * (expected - ctr))}
    return None


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1}


def missing_from_title(query: str, title: Optional[str]) -> List[str]:
    if not title:
        return []
    return sorted(_tokens(query) - _tokens(title))


def find_cannibalization(rows: List[Dict[str, Any]], min_share: float = 0.2,
                         min_impressions: int = 50) -> List[Dict[str, Any]]:
    """Queries where two or more pages each take a real share of impressions."""
    by_query: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_query[r["query"]].append(r)
    out = []
    for q, rs in by_query.items():
        total = sum(r["impressions"] for r in rs)
        if total < min_impressions or len(rs) < 2:
            continue
        splits = [r for r in rs if r["impressions"] / total >= min_share]
        if len(splits) >= 2:
            out.append({
                "query": q,
                "impressions": int(total),
                "pages": [{"page": r["page"], "impressions": int(r["impressions"]),
                           "position": round(r["position"], 1)} for r in
                          sorted(splits, key=lambda r: -r["impressions"])],
            })
    return sorted(out, key=lambda c: -c["impressions"])


def load_titles(path: Optional[str]) -> Dict[str, str]:
    """Optional page,title CSV (a crawl export) for title-alignment checks."""
    if not path:
        return {}
    titles: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            lower = {k.strip().lower(): v for k, v in raw.items() if k}
            page = lower.get("page") or lower.get("url") or lower.get("address")
            title = lower.get("title") or lower.get("title 1")
            if page and title:
                titles[page.strip()] = title.strip()
    return titles


def _primary_action(page: Dict[str, Any], title: Optional[str]) -> str:
    gap_up = sum(q["upside_clicks"] for q in page["queries"] if q["type"] == "ctr_gap")
    if gap_up >= 0.5 * page["upside_clicks"]:
        return "rewrite_title_meta"
    top = page["queries"][0]
    if title and len(missing_from_title(top["query"], title)) >= 1:
        return "align_title_to_query"
    if len({q["query"] for q in page["queries"] if q["type"] == "striking_distance"}) >= 5:
        return "expand_depth"
    return "internal_links"


ACTION_TEXT = {
    "rewrite_title_meta": "Rewrite the title and meta description around the top queries; the page already ranks but is not chosen.",
    "align_title_to_query": "Put the top query's missing words in the title and H1; Google is ranking the page for a term it does not lead with.",
    "expand_depth": "Add sections that answer the page-two queries directly (one H2 or table per cluster).",
    "internal_links": "Add internal links to this page from the site's strongest pages, with the query as anchor text.",
}


def build_queue(rows: List[Dict[str, Any]], *, brand_terms: List[str], min_impressions: int = 50,
                titles: Optional[Dict[str, str]] = None, top_link_sources: int = 5) -> Dict[str, Any]:
    titles = titles or {}
    brand = [r for r in rows if is_brand(r["query"], brand_terms)]
    non_brand = [r for r in rows if not is_brand(r["query"], brand_terms)]
    curve = calibrate_ctr_curve(non_brand)

    pages: Dict[str, Dict[str, Any]] = {}
    for r in non_brand:
        if r["impressions"] < min_impressions:
            continue
        c = classify(r, curve)
        if not c or c["upside_clicks"] <= 0:
            continue
        pg = pages.setdefault(r["page"], {"page": r["page"], "queries": [], "upside_clicks": 0.0,
                                         "impressions": 0.0, "clicks": 0.0})
        pg["queries"].append({
            "query": r["query"], "type": c["type"], "impressions": int(r["impressions"]),
            "clicks": int(r["clicks"]), "ctr": round(r["ctr"], 4), "position": round(r["position"], 1),
            "expected_ctr": c["expected_ctr"], "target_position": c.get("target_position"),
            "upside_clicks": round(c["upside_clicks"], 1),
        })
        pg["upside_clicks"] += c["upside_clicks"]
        pg["impressions"] += r["impressions"]
        pg["clicks"] += r["clicks"]

    # Strongest pages by non-brand clicks are the internal-link sources.
    page_clicks: Dict[str, float] = defaultdict(float)
    for r in non_brand:
        page_clicks[r["page"]] += r["clicks"]
    strongest = [p for p, _ in sorted(page_clicks.items(), key=lambda kv: -kv[1]) if page_clicks[p] > 0]

    ranked = sorted(pages.values(), key=lambda p: -p["upside_clicks"])
    for pg in ranked:
        pg["queries"].sort(key=lambda q: -q["upside_clicks"])
        title = titles.get(pg["page"])
        pg["title"] = title
        pg["upside_clicks"] = round(pg["upside_clicks"], 1)
        pg["impressions"] = int(pg["impressions"])
        pg["clicks"] = int(pg["clicks"])
        pg["weighted_position"] = round(
            sum(q["position"] * q["impressions"] for q in pg["queries"]) / max(1, pg["impressions"]), 1)
        pg["primary_action"] = _primary_action(pg, title)
        pg["action_text"] = ACTION_TEXT[pg["primary_action"]]
        if title:
            pg["title_missing_terms"] = missing_from_title(pg["queries"][0]["query"], title)
        if any(q["type"] == "striking_distance" for q in pg["queries"]):
            pg["link_from"] = [p for p in strongest if p != pg["page"]][:top_link_sources]

    def _sum(rs: List[Dict[str, Any]], k: str) -> int:
        return int(sum(r[k] for r in rs))

    return {
        "schema": "kai.seo.refresh-queue.v1",
        "totals": {
            "rows": len(rows),
            "brand": {"clicks": _sum(brand, "clicks"), "impressions": _sum(brand, "impressions")},
            "non_brand": {"clicks": _sum(non_brand, "clicks"), "impressions": _sum(non_brand, "impressions")},
            "pages_in_queue": len(ranked),
            "estimated_upside_clicks": round(sum(p["upside_clicks"] for p in ranked), 1),
        },
        "params": {"min_impressions": min_impressions, "brand_terms": brand_terms,
                   "ctr_gap_ratio": CTR_GAP_RATIO, "calibration_min_impressions": CALIBRATION_MIN_IMPRESSIONS},
        "ctr_curve": curve,
        "pages": ranked,
        "cannibalization": find_cannibalization(non_brand)[:25],
    }


def render_markdown(queue: Dict[str, Any], limit: int = 20) -> str:
    meta = queue.get("meta", {})
    t = queue["totals"]
    site_curve = sum(1 for v in queue["ctr_curve"].values() if v["source"] == "site")
    lines = [
        f"# Refresh queue: {meta.get('site', 'site')}",
        "",
        f"Source: {meta.get('source', 'google_search_console')} · window {meta.get('start', '?')} to "
        f"{meta.get('end', '?')} · file `{meta.get('source_file', '?')}`",
        "",
        f"- Non-brand: {t['non_brand']['clicks']} clicks / {t['non_brand']['impressions']} impressions. "
        f"Brand (excluded): {t['brand']['clicks']} clicks / {t['brand']['impressions']} impressions.",
        f"- {t['pages_in_queue']} pages have fixable queries. Estimated upside if each reaches its next rung: "
        f"~{t['estimated_upside_clicks']:.0f} clicks per window (estimate, not a forecast).",
        f"- Expected CTR is calibrated on this site's data at {site_curve}/20 positions; the rest use a heuristic.",
        "",
        "| # | Page | Fix | Top queries (pos, impressions) | Upside |",
        "|---|------|-----|-------------------------------|-------:|",
    ]
    for i, pg in enumerate(queue["pages"][:limit], 1):
        qs = "; ".join(f"{q['query']} ({q['position']}, {q['impressions']})" for q in pg["queries"][:3])
        lines.append(f"| {i} | {pg['page']} | {pg['primary_action']} | {qs} | {pg['upside_clicks']:.0f} |")
    lines += ["", "## What to do on each page", ""]
    for i, pg in enumerate(queue["pages"][:limit], 1):
        lines.append(f"{i}. **{pg['page']}**: {pg['action_text']}")
        if pg.get("title_missing_terms"):
            lines.append(f"   Title is missing: {', '.join(pg['title_missing_terms'])}.")
        if pg.get("link_from"):
            lines.append(f"   Link from: {', '.join(pg['link_from'][:3])}.")
    if queue["cannibalization"]:
        lines += ["", "## Queries split across pages", "",
                  "Pick one page per query; point the other at it with a link or merge it.", ""]
        for c in queue["cannibalization"][:10]:
            pages = ", ".join(f"{p['page']} (pos {p['position']})" for p in c["pages"])
            lines.append(f"- {c['query']} ({c['impressions']} impressions): {pages}")
    lines += ["", "Record every shipped fix before it goes live so it gets graded:",
              "`python -m scripts.seo.refresh_tracker record --queue <this folder>/refresh-queue.json "
              "--page <url> --change <fix> --shipped-on <YYYY-MM-DD>`", ""]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="Query x page export (JSON from gsc_data pull, or CSV)")
    ap.add_argument("--brand", default="", help="Comma-separated brand terms to exclude")
    ap.add_argument("--site", help="Site label for the report (default: from the data file)")
    ap.add_argument("--start", help="Window start, if the data file does not carry it")
    ap.add_argument("--end", help="Window end, if the data file does not carry it")
    ap.add_argument("--titles", help="Optional CSV of page,title (crawl export) for title checks")
    ap.add_argument("--min-impressions", type=int, default=50)
    ap.add_argument("--limit", type=int, default=20, help="Pages shown in the markdown")
    ap.add_argument("--out", required=True, help="Output folder")
    args = ap.parse_args(argv)

    rows, meta = load_rows(args.data)
    for k in ("site", "start", "end"):
        if getattr(args, k):
            meta[k] = getattr(args, k)
    if not meta.get("start") or not meta.get("end"):
        print("  The data file has no window. Pass --start and --end so later grading knows the baseline period.",
              file=sys.stderr)
        return 2
    queue = build_queue(rows, brand_terms=parse_brand_terms(args.brand),
                        min_impressions=args.min_impressions, titles=load_titles(args.titles))
    queue["meta"] = meta
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "refresh-queue.json").write_text(json.dumps(queue, indent=1), encoding="utf-8")
    (out / "refresh-queue.md").write_text(render_markdown(queue, args.limit), encoding="utf-8")
    t = queue["totals"]
    print(f"{t['pages_in_queue']} pages queued, ~{t['estimated_upside_clicks']:.0f} clicks estimated upside -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

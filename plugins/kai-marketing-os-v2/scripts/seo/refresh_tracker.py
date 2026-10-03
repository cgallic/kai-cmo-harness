#!/usr/bin/env python3
"""Grade every fix to an existing page against Search Console.

A page refresh (new title, added section, internal links) is only worth
repeating if it moved clicks. This tracker records the fix with a baseline
taken from data that ends before the fix shipped, then grades it from a
later export of the same queries, normalized against the rest of the site
so a seasonal swing is not mistaken for a win.

    # before (or the day) the fix ships
    python -m scripts.seo.refresh_tracker record \
        --queue workspace/seo-refresh/example/refresh-queue.json \
        --page https://example.com/tent-sizes --change expand_depth \
        --shipped-on 2026-10-05 --owner connor

    # 28+ days later, with a fresh export that starts on/after the ship date
    python -m scripts.seo.refresh_tracker check --data data/seo/example-nov.json

    # which kinds of fixes actually work
    python -m scripts.seo.refresh_tracker report

Records live in ``<data_dir>/seo/refreshes/<id>.json``. Checks are appended,
never rewritten. Grades: won / flat / lost / insufficient_data.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from scripts.seo.gsc_data import is_brand, load_rows, parse_brand_terms
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.seo.gsc_data import is_brand, load_rows, parse_brand_terms

CHANGE_TYPES = ("rewrite_title_meta", "align_title_to_query", "expand_depth", "internal_links",
                "consolidate", "other")
DEFAULT_WINDOW_DAYS = 28
DEFAULT_THRESHOLD_PCT = 20.0
POSITION_GAIN = 2.0
MIN_IMPRESSIONS = 100


def _store_dir(override: Optional[str]) -> Path:
    if override:
        return Path(override)
    try:
        from scripts.harness_config import get_config
        return get_config().data_dir / "seo" / "refreshes"
    except Exception:
        return Path(__file__).resolve().parents[2] / "data" / "seo" / "refreshes"


def _days(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


def _slug(url: str) -> str:
    s = re.sub(r"^https?://", "", url).strip("/")
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "page"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def snapshot(rows: List[Dict[str, Any]], *, page: str, queries: List[str], brand_terms: List[str],
             start: str, end: str, conversions: Optional[float] = None) -> Dict[str, Any]:
    """Per-day page, tracked-query, and site-control metrics for one window."""
    days = _days(start, end)
    nb = [r for r in rows if not is_brand(r["query"], brand_terms)]
    on_page = [r for r in nb if r["page"] == page]
    control = [r for r in nb if r["page"] != page]
    tracked = {}
    for r in on_page:
        if r["query"] in queries:
            tracked[r["query"]] = {"clicks": r["clicks"], "impressions": r["impressions"],
                                   "position": round(r["position"], 2)}
    clicks = sum(r["clicks"] for r in on_page)
    imps = sum(r["impressions"] for r in on_page)
    return {
        "start": start, "end": end, "days": days,
        "page": {
            "clicks": clicks, "impressions": imps,
            "clicks_per_day": round(clicks / days, 4), "impressions_per_day": round(imps / days, 4),
            "ctr": round(clicks / imps, 4) if imps else 0.0,
            "conversions": conversions,
        },
        "queries": tracked,
        "site_control": {
            "clicks_per_day": round(sum(r["clicks"] for r in control) / days, 4),
            "impressions_per_day": round(sum(r["impressions"] for r in control) / days, 4),
        },
    }


def _weighted_position(qs: Dict[str, Dict[str, Any]], keys: List[str]) -> Optional[float]:
    num = sum(qs[k]["position"] * qs[k]["impressions"] for k in keys)
    den = sum(qs[k]["impressions"] for k in keys)
    return num / den if den else None


def grade(baseline: Dict[str, Any], post: Dict[str, Any], threshold_pct: float = DEFAULT_THRESHOLD_PCT) -> Dict[str, Any]:
    b, p = baseline["page"], post["page"]
    b_ctl = baseline["site_control"]["clicks_per_day"]
    p_ctl = post["site_control"]["clicks_per_day"]
    control_ratio = (p_ctl / b_ctl) if b_ctl > 0 else 1.0
    expected = b["clicks_per_day"] * control_ratio
    lift_pct = ((p["clicks_per_day"] / expected) - 1) * 100 if expected > 0 else None

    shared = [q for q in baseline["queries"] if q in post["queries"]]
    b_pos = _weighted_position(baseline["queries"], shared)
    p_pos = _weighted_position(post["queries"], shared)
    position_gain = round(b_pos - p_pos, 2) if b_pos is not None and p_pos is not None else None

    if b["impressions"] < MIN_IMPRESSIONS and p["impressions"] < MIN_IMPRESSIONS:
        verdict = "insufficient_data"
    elif lift_pct is None:
        # No baseline clicks: a page that starts earning is a win only with real volume.
        post_clicks_month = p["clicks_per_day"] * 28
        verdict = "won" if post_clicks_month >= 5 else (
            "lost" if (position_gain or 0) <= -POSITION_GAIN else "flat")
    elif lift_pct >= threshold_pct or ((position_gain or 0) >= POSITION_GAIN and lift_pct >= 0):
        verdict = "won"
    elif lift_pct <= -threshold_pct or (position_gain or 0) <= -POSITION_GAIN:
        verdict = "lost"
    else:
        verdict = "flat"
    return {
        "verdict": verdict,
        "clicks_lift_pct_vs_control": round(lift_pct, 1) if lift_pct is not None else None,
        "control_ratio": round(control_ratio, 3),
        "expected_clicks_per_day": round(expected, 4),
        "observed_clicks_per_day": p["clicks_per_day"],
        "tracked_position_before": round(b_pos, 2) if b_pos is not None else None,
        "tracked_position_after": round(p_pos, 2) if p_pos is not None else None,
        "position_gain": position_gain,
        "ctr_before": b["ctr"], "ctr_after": p["ctr"],
        "conversions_before": b.get("conversions"), "conversions_after": p.get("conversions"),
    }


def _load_records(store: Path) -> List[Dict[str, Any]]:
    if not store.is_dir():
        return []
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted(store.glob("*.json"))]


def _write_record(store: Path, record: Dict[str, Any]) -> Path:
    store.mkdir(parents=True, exist_ok=True)
    path = store / f"{record['id']}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=1), encoding="utf-8")
    tmp.replace(path)
    return path


def _write_evidence(path: Optional[str], entries: List[Dict[str, Any]]) -> None:
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps({"evidence": entries}, indent=1), encoding="utf-8")
        print(f"  ECO evidence -> {path}")


# ---------------------------------------------------------------- commands

def cmd_record(args) -> int:
    queue = json.loads(Path(args.queue).read_text(encoding="utf-8")) if args.queue else None
    meta = dict((queue or {}).get("meta") or {})
    data_path = args.data or meta.get("source_file")
    if not data_path:
        print("  Pass --data (the baseline export) or --queue from striking_distance.", file=sys.stderr)
        return 2
    rows, file_meta = load_rows(data_path)
    for k, v in file_meta.items():
        meta.setdefault(k, v)
    start, end = args.start or meta.get("start"), args.end or meta.get("end")
    if not start or not end:
        print("  Baseline window unknown. Pass --start and --end.", file=sys.stderr)
        return 2
    shipped = date.fromisoformat(args.shipped_on)
    if date.fromisoformat(end) >= shipped:
        print(f"  Baseline window ends {end}, on or after the ship date {shipped}. "
              "A baseline must predate the change; pull a window that ends before it.", file=sys.stderr)
        return 2
    brand_terms = parse_brand_terms(args.brand) if args.brand else list((queue or {}).get("params", {}).get("brand_terms") or [])

    queries: List[str] = []
    if queue:
        for pg in queue.get("pages", []):
            if pg["page"] == args.page:
                queries = [q["query"] for q in pg["queries"]]
                break
    if not queries:
        on_page = sorted((r for r in rows if r["page"] == args.page and not is_brand(r["query"], brand_terms)),
                         key=lambda r: -r["impressions"])
        queries = [r["query"] for r in on_page[:10]]
    if not queries:
        print(f"  No non-brand rows for {args.page} in the baseline data. Check the URL matches the export.",
              file=sys.stderr)
        return 2

    base = snapshot(rows, page=args.page, queries=queries, brand_terms=brand_terms,
                    start=start, end=end, conversions=args.conversions)
    record_id = f"refresh-{shipped.isoformat()}-{_slug(args.page)}"
    record = {
        "schema": "kai.seo.refresh-record.v1",
        "id": record_id,
        "site": meta.get("site"),
        "page": args.page,
        "change": args.change,
        "note": args.note,
        "owner": args.owner,
        "shipped_on": shipped.isoformat(),
        "check_after": (shipped + timedelta(days=args.window_days)).isoformat(),
        "window_days": args.window_days,
        "threshold": {"clicks_lift_pct_vs_control": args.threshold_pct, "or_position_gain": POSITION_GAIN},
        "brand_terms": brand_terms,
        "tracked_queries": queries,
        "baseline": base,
        "baseline_source": {"source": meta.get("source", "google_search_console"), "file": str(data_path),
                            "retrieved_at": meta.get("retrieved_at")},
        "recorded_at": _now(),
        "recorded_after_ship": date.today() > shipped,
        "checks": [],
        "status": "awaiting_check",
    }
    path = _write_record(_store_dir(args.store), record)
    print(f"Recorded {record_id}: {base['page']['clicks_per_day'] * 28:.1f} clicks / 28d baseline, "
          f"{len(queries)} tracked queries. Grade after {record['check_after']}. -> {path}")
    if record["recorded_after_ship"]:
        print("  Note: recorded after the ship date. The baseline data predates the change, "
              "but ECO treats a late-written baseline as no baseline.")
    _write_evidence(args.eco_evidence, [{
        "kind": "outcome_baseline",
        "metric": "non_brand_clicks_per_day (page, vs site control)",
        "source": "google_search_console",
        "baseline": base["page"]["clicks_per_day"],
        "threshold": f"+{args.threshold_pct:g}% vs site control, or tracked position +{POSITION_GAIN:g}",
        "window": f"{args.window_days} days after {shipped.isoformat()}",
        "owner": args.owner,
        "locator": str(path),
    }])
    return 0


def cmd_check(args) -> int:
    rows, meta = load_rows(args.data)
    start, end = args.start or meta.get("start"), args.end or meta.get("end")
    if not start or not end:
        print("  Post window unknown. Pass --start and --end.", file=sys.stderr)
        return 2
    if args.conversions is not None and not args.page:
        print("  --conversions is one page's number; pass --page with it.", file=sys.stderr)
        return 2
    today = date.fromisoformat(args.today) if args.today else date.today()
    pages_in_data = {r["page"] for r in rows}
    store = _store_dir(args.store)
    graded, skipped, evidence = 0, [], []
    for rec in _load_records(store):
        if rec.get("status") != "awaiting_check" and not args.regrade:
            continue
        if rec["page"] not in pages_in_data or (args.page and rec["page"] != args.page):
            continue
        if today < date.fromisoformat(rec["check_after"]) and not args.force:
            skipped.append((rec["id"], f"not due until {rec['check_after']}"))
            continue
        if date.fromisoformat(start) < date.fromisoformat(rec["shipped_on"]):
            skipped.append((rec["id"], f"post window starts {start}, before ship {rec['shipped_on']}"))
            continue
        if _days(start, end) < 14:
            skipped.append((rec["id"], "post window shorter than 14 days"))
            continue
        post = snapshot(rows, page=rec["page"], queries=rec["tracked_queries"], brand_terms=rec["brand_terms"],
                        start=start, end=end, conversions=args.conversions)
        result = grade(rec["baseline"], post, rec["threshold"]["clicks_lift_pct_vs_control"])
        rec["checks"].append({"checked_at": _now(), "post": post, "result": result,
                              "source_file": str(args.data)})
        rec["status"] = "graded"
        rec["verdict"] = result["verdict"]
        _write_record(store, rec)
        graded += 1
        lift = result["clicks_lift_pct_vs_control"]
        print(f"  {result['verdict']:>17}  {rec['page']}  ({rec['change']}): "
              f"lift {lift if lift is not None else 'n/a'}% vs control, position gain {result['position_gain']}")
        observed = f"{post['page']['clicks_per_day']} clicks/day; lift {lift}% vs control"
        evidence.append({"kind": "outcome_observation", "verifier": "google_search_console",
                         "observed": observed, "locator": rec["id"]})
        if result["verdict"] == "won":
            evidence.append({"kind": "outcome_threshold_met", "verifier": "google_search_console",
                             "observed": observed,
                             "threshold": f"+{rec['threshold']['clicks_lift_pct_vs_control']:g}% vs site control",
                             "locator": rec["id"]})
    for rid, why in skipped:
        print(f"  skipped {rid}: {why}")
    print(f"Graded {graded} refresh(es).")
    _write_evidence(args.eco_evidence, evidence)
    return 0


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_change: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        c = by_change.setdefault(rec["change"], {"won": 0, "flat": 0, "lost": 0, "insufficient_data": 0,
                                                 "awaiting": 0, "lifts": []})
        if rec.get("status") != "graded":
            c["awaiting"] += 1
            continue
        res = rec["checks"][-1]["result"]
        c[res["verdict"]] += 1
        if res["clicks_lift_pct_vs_control"] is not None:
            c["lifts"].append(res["clicks_lift_pct_vs_control"])
    for c in by_change.values():
        decided = c["won"] + c["flat"] + c["lost"]
        c["win_rate"] = round(c["won"] / decided, 2) if decided else None
        c["median_lift_pct"] = round(statistics.median(c["lifts"]), 1) if c["lifts"] else None
        del c["lifts"]
    return by_change


def cmd_report(args) -> int:
    records = _load_records(_store_dir(args.store))
    if not records:
        print("No refreshes recorded yet. Record one with: refresh_tracker record ...")
        return 0
    summary = summarize(records)
    lines = ["# Page refresh outcomes", "",
             "| Fix | Won | Flat | Lost | Too little data | Awaiting | Win rate | Median lift vs control |",
             "|-----|---:|---:|---:|---:|---:|---:|---:|"]
    for change, c in sorted(summary.items()):
        wr = f"{c['win_rate']:.0%}" if c["win_rate"] is not None else "n/a"
        ml = f"{c['median_lift_pct']}%" if c["median_lift_pct"] is not None else "n/a"
        lines.append(f"| {change} | {c['won']} | {c['flat']} | {c['lost']} | {c['insufficient_data']} | "
                     f"{c['awaiting']} | {wr} | {ml} |")
    lines += ["", "Winners feed knowledge/playbooks/what-works.md and losers memory/what-doesnt-work.md "
              "through /kai-retro; this report never edits them.", ""]
    text = "\n".join(lines)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"-> {args.out}")
    print(text)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", help="Record folder (default: <data_dir>/seo/refreshes)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="Record a fix with its pre-ship baseline")
    r.add_argument("--page", required=True, help="Exact page URL as it appears in the export")
    r.add_argument("--change", required=True, choices=CHANGE_TYPES)
    r.add_argument("--shipped-on", required=True, help="YYYY-MM-DD the change went live")
    r.add_argument("--queue", help="refresh-queue.json from striking_distance (supplies queries, brand, data)")
    r.add_argument("--data", help="Baseline export (default: the queue's source file)")
    r.add_argument("--start")
    r.add_argument("--end")
    r.add_argument("--brand", help="Comma-separated brand terms (default: the queue's)")
    r.add_argument("--conversions", type=float, help="Page conversions in the baseline window (GA4), if tracked")
    r.add_argument("--window-days", type=int, default=DEFAULT_WINDOW_DAYS)
    r.add_argument("--threshold-pct", type=float, default=DEFAULT_THRESHOLD_PCT)
    r.add_argument("--owner", default="unassigned")
    r.add_argument("--note")
    r.add_argument("--eco-evidence", help="Also write an ECO outcome_baseline evidence file here")
    r.set_defaults(func=cmd_record)

    c = sub.add_parser("check", help="Grade due refreshes from a post-ship export")
    c.add_argument("--data", required=True)
    c.add_argument("--start")
    c.add_argument("--end")
    c.add_argument("--page", help="Grade only this page")
    c.add_argument("--conversions", type=float, help="That page's conversions in the post window (GA4); needs --page")
    c.add_argument("--today", help=argparse.SUPPRESS)
    c.add_argument("--force", action="store_true", help="Grade even if the window has not elapsed")
    c.add_argument("--regrade", action="store_true", help="Re-grade records already graded")
    c.add_argument("--eco-evidence", help="Also write ECO outcome evidence here")
    c.set_defaults(func=cmd_check)

    rp = sub.add_parser("report", help="Win rate by fix type")
    rp.add_argument("--out")
    rp.set_defaults(func=cmd_report)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

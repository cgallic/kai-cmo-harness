"""Existing-page SEO loop: refresh queue, portfolio triage, refresh grading.

Doctrine: knowledge/playbooks/page-refresh-loop.md
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.seo import gsc_data, portfolio, refresh_tracker, striking_distance as sd


def row(query, page, clicks, impressions, position):
    return {"query": query, "page": page, "clicks": float(clicks), "impressions": float(impressions),
            "ctr": clicks / impressions if impressions else 0.0, "position": float(position)}


SITE = "https://ex.com"
ROWS = [
    # strong page, ranks 2, healthy CTR -> no work, but is the best link source
    row("party tent rental", f"{SITE}/tents", 300, 2000, 2.0),
    # ranks 3 with almost no clicks -> ctr_gap
    row("wedding band cost", f"{SITE}/band-cost", 2, 3600, 3.1),
    # page two cluster -> striking_distance, expand_depth (5+ queries)
    *[row(f"tent size for {n} guests", f"{SITE}/tent-guide", 1, 400, 11.0) for n in (50, 75, 100, 150, 200)],
    # brand query -> excluded
    row("starrs party rentals", f"{SITE}/", 500, 900, 1.0),
    # below min impressions -> ignored
    row("tiny query", f"{SITE}/tent-guide", 0, 10, 9.0),
    # off page two -> ignored
    row("far away", f"{SITE}/tent-guide", 0, 900, 35.0),
]


def test_loader_reads_loose_csv_headers(tmp_path: Path):
    p = tmp_path / "gsc.csv"
    with p.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Top queries", "Landing Page", "Clicks", "Impressions", "CTR", "Position"])
        w.writerow(["tent sizes", "https://ex.com/a", "3", "1,200", "0.25%", "9.4"])
    rows, meta = gsc_data.load_rows(p)
    assert rows == [{"query": "tent sizes", "page": "https://ex.com/a", "clicks": 3.0,
                     "impressions": 1200.0, "ctr": 0.0025, "position": 9.4}]
    assert meta["source"] == "google_search_console"


def test_loader_reads_raw_api_json(tmp_path: Path):
    p = tmp_path / "gsc.json"
    p.write_text(json.dumps({"meta": {"site": "ex.com", "start": "2026-07-01", "end": "2026-09-28"},
                             "rows": [{"keys": ["q", "https://ex.com/a"], "clicks": 1, "impressions": 10,
                                       "ctr": 0.1, "position": 4.2}]}))
    rows, meta = gsc_data.load_rows(p)
    assert rows[0]["query"] == "q" and rows[0]["page"] == "https://ex.com/a"
    assert meta["start"] == "2026-07-01"


def test_brand_match_ignores_spacing():
    assert gsc_data.is_brand("kai calls pricing", ["kaicalls"])
    assert gsc_data.is_brand("KaiCalls login", ["kai calls"])
    assert not gsc_data.is_brand("ai receptionist", ["kaicalls"])


def test_ctr_curve_is_non_increasing_and_labels_its_source():
    curve = sd.calibrate_ctr_curve(ROWS)
    ctrs = [curve[p]["ctr"] for p in range(1, 21)]
    assert ctrs == sorted(ctrs, reverse=True)
    assert curve[2]["source"] == "heuristic"      # one page holds the bucket: not a benchmark
    assert curve[15]["source"] == "heuristic"


def test_queue_finds_ctr_gap_and_striking_distance_and_excludes_brand():
    q = sd.build_queue(ROWS, brand_terms=["starrs"])
    pages = {p["page"]: p for p in q["pages"]}
    assert set(pages) == {f"{SITE}/band-cost", f"{SITE}/tent-guide"}
    assert pages[f"{SITE}/band-cost"]["primary_action"] == "rewrite_title_meta"
    assert pages[f"{SITE}/tent-guide"]["primary_action"] == "expand_depth"
    # strongest non-brand page is offered as the internal-link source
    assert pages[f"{SITE}/tent-guide"]["link_from"][0] == f"{SITE}/tents"
    assert q["totals"]["brand"]["clicks"] == 500
    assert all("starrs" not in qq["query"] for p in q["pages"] for qq in p["queries"])
    # ordered by upside
    ups = [p["upside_clicks"] for p in q["pages"]]
    assert ups == sorted(ups, reverse=True)


def test_title_alignment_wins_when_title_misses_the_query():
    rows = [row("tent rental prices", f"{SITE}/pricing", 1, 800, 9.0)]
    q = sd.build_queue(rows, brand_terms=[], titles={f"{SITE}/pricing": "Our Rates | Starrs"})
    pg = q["pages"][0]
    assert pg["primary_action"] == "align_title_to_query"
    assert "tent" in pg["title_missing_terms"]


def test_cannibalization_flags_split_queries():
    rows = [row("tent sizes", f"{SITE}/a", 1, 300, 9.0), row("tent sizes", f"{SITE}/b", 1, 250, 12.0)]
    c = sd.find_cannibalization(rows)
    assert c and {p["page"] for p in c[0]["pages"]} == {f"{SITE}/a", f"{SITE}/b"}


def test_cli_requires_a_window(tmp_path: Path):
    p = tmp_path / "gsc.csv"
    p.write_text("query,page,clicks,impressions,position\nq,https://ex.com/a,1,100,9\n")
    assert sd.main(["--data", str(p), "--out", str(tmp_path / "out")]) == 2
    assert sd.main(["--data", str(p), "--start", "2026-07-01", "--end", "2026-09-28",
                    "--out", str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "refresh-queue.md").exists()


def test_portfolio_concentrates_investment(tmp_path: Path):
    p = tmp_path / "portfolio.csv"
    p.write_text("site,clicks,impressions,brand_clicks,days\n"
                 "gfa.com,912,30000,12,90\nstarrs.com,387,15000,0,90\nkaicalls.com,297,9000,250,90\n"
                 "satellite-1.com,3,900,0,90\nsatellite-2.com,0,40,0,90\n")
    res = portfolio.triage(portfolio.load_portfolio(str(p)))
    tiers = {x["site"]: x["tier"] for x in res["properties"]}
    assert tiers["gfa.com"] == "invest" and tiers["starrs.com"] == "invest"
    assert tiers["satellite-1.com"] == "freeze" and tiers["satellite-2.com"] == "freeze"
    # kaicalls is mostly brand: real clicks, but not where refresh work pays
    assert tiers["kaicalls.com"] == "maintain"


# ------------------------------------------------------------ refresh tracker

def _export(path: Path, rows, start, end):
    path.write_text(json.dumps({"meta": {"site": "ex.com", "start": start, "end": end}, "rows": rows}))
    return path


def test_record_refuses_a_baseline_that_overlaps_the_ship_date(tmp_path: Path):
    data = _export(tmp_path / "base.json", ROWS, "2026-07-01", "2026-09-28")
    rc = refresh_tracker.main(["--store", str(tmp_path / "s"), "record", "--data", str(data),
                               "--page", f"{SITE}/tent-guide", "--change", "expand_depth",
                               "--shipped-on", "2026-09-20"])
    assert rc == 2
    assert not (tmp_path / "s").exists()


def _record(tmp_path: Path, page: str, change: str):
    data = _export(tmp_path / "base.json", ROWS, "2026-09-01", "2026-09-28")
    rc = refresh_tracker.main(["--store", str(tmp_path / "s"), "record", "--data", str(data),
                               "--page", page, "--change", change, "--shipped-on", "2026-10-01",
                               "--brand", "starrs", "--eco-evidence", str(tmp_path / "ev.json")])
    assert rc == 0
    ev = json.loads((tmp_path / "ev.json").read_text())["evidence"][0]
    assert ev["kind"] == "outcome_baseline"
    for field in ("metric", "source", "baseline", "threshold", "window", "owner"):
        assert field in ev


def _check(tmp_path: Path, rows, today="2026-11-05"):
    data = _export(tmp_path / "post.json", rows, "2026-10-04", "2026-10-31")
    return refresh_tracker.main(["--store", str(tmp_path / "s"), "check", "--data", str(data),
                                 "--today", today])


def _records(tmp_path: Path):
    return [json.loads(f.read_text()) for f in (tmp_path / "s").glob("*.json")]


def test_refresh_that_climbs_is_graded_won(tmp_path: Path):
    _record(tmp_path, f"{SITE}/tent-guide", "expand_depth")
    post = [r for r in ROWS if r["page"] != f"{SITE}/tent-guide"] + [
        row(f"tent size for {n} guests", f"{SITE}/tent-guide", 20, 450, 5.0) for n in (50, 75, 100, 150, 200)]
    assert _check(tmp_path, post) == 0
    rec = _records(tmp_path)[0]
    assert rec["verdict"] == "won"
    assert rec["checks"][0]["result"]["position_gain"] == pytest.approx(6.0)


def test_sitewide_swing_is_not_credited_to_the_page(tmp_path: Path):
    """Page clicks double, but so does the whole site: that is seasonality, not the fix."""
    _record(tmp_path, f"{SITE}/band-cost", "rewrite_title_meta")
    post = []
    for r in ROWS:
        r2 = dict(r)
        r2["clicks"] = r["clicks"] * 2
        post.append(r2)
    _check(tmp_path, post)
    rec = _records(tmp_path)[0]
    assert rec["checks"][0]["result"]["control_ratio"] == pytest.approx(2.0, rel=0.01)
    assert rec["verdict"] == "flat"


def test_check_waits_for_the_window(tmp_path: Path):
    _record(tmp_path, f"{SITE}/tent-guide", "expand_depth")
    _check(tmp_path, ROWS, today="2026-10-10")
    assert _records(tmp_path)[0]["status"] == "awaiting_check"


def test_report_counts_by_fix_type(tmp_path: Path, capsys):
    _record(tmp_path, f"{SITE}/tent-guide", "expand_depth")
    post = [r for r in ROWS if r["page"] != f"{SITE}/tent-guide"] + [
        row(f"tent size for {n} guests", f"{SITE}/tent-guide", 20, 450, 5.0) for n in (50, 75, 100, 150, 200)]
    _check(tmp_path, post)
    summary = refresh_tracker.summarize(_records(tmp_path))
    assert summary["expand_depth"]["won"] == 1
    assert summary["expand_depth"]["win_rate"] == 1.0


def test_curve_trusts_a_bucket_spread_across_pages():
    rows = [row(f"q{i}", f"{SITE}/p{i}", 40, 400, 4.0) for i in range(4)]
    curve = sd.calibrate_ctr_curve(rows)
    assert curve[4]["source"] == "site"
    assert curve[4]["ctr"] == pytest.approx(0.1)
    assert curve[1]["ctr"] >= curve[4]["ctr"]

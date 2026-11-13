"""Ad Library survival scan: collect -> Jev tags -> survival lifts -> brief scores.

Offline only: Jev answers come from ``answer_fn`` fakes or the decision_log mock backend,
and Apify calls are monkeypatched. Doctrine: knowledge/playbooks/ad-library-survival-scan.md
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from scripts.ads.ad_library import budget as bd
from scripts.ads.ad_library import collect_ads as ca
from scripts.ads.ad_library import jev
from scripts.ads.ad_library import score_briefs as sb
from scripts.ads.ad_library import survival_report as sr
from scripts.ads.ad_library import tag_ads as ta

APIFY_REC = {
    "ad_archive_id": "123", "page_id": "9", "page_name": "Budgetly",
    "start_date": 1735689600, "end_date": 0, "is_active": True,  # 2025-01-01, active (end 0)
    "publisher_platform": ["FACEBOOK", "INSTAGRAM"],
    "snapshot": {"body": {"text": "Save $200 a month. Try Budgetly free."}, "title": "Budget in 5 min",
                 "link_description": "Free 30-day trial", "cta_text": "Sign Up", "link_url": "https://b.example",
                 "display_format": "VIDEO", "videos": [{}]},
    "url": "https://www.facebook.com/ads/library/?id=123",
}
GRAPH_REC = {
    "id": "456", "page_id": "77", "page_name": "Cashwise",
    "ad_creation_time": "2026-01-01", "ad_delivery_start_time": "2026-01-02",
    "ad_delivery_stop_time": "2026-03-15",
    "ad_creative_bodies": ["Tired of overdraft fees?"], "ad_creative_link_titles": ["Cashwise"],
    "ad_creative_link_descriptions": ["No fees"], "ad_creative_link_captions": ["cashwise.example"],
    "publisher_platforms": ["facebook"],
    "ad_snapshot_url": "https://www.facebook.com/ads/archive/render_ad/?id=456&access_token=SECRET",
}


def test_normalize_apify_record():
    r = ca.normalize_library_record(APIFY_REC, "apify")
    assert r["ad_id"] == "123" and r["page_name"] == "Budgetly"
    assert r["start_date"] == "2025-01-01" and r["end_date"] is None and r["is_active"] is True
    assert r["body"].startswith("Save $200") and r["cta"] == "Sign Up"
    assert r["display_format"] == "video" and r["platforms"] == ["facebook", "instagram"]
    # camelCase variant, ms timestamps, inactive
    alt = {"adArchiveID": 5, "pageName": "X", "startDate": 1735689600000, "endDate": 1738368000000,
           "isActive": False, "snapshot": {"cards": [{"body": "card text"}, {"body": "two"}]}}
    r2 = ca.normalize_library_record(alt)
    assert r2["ad_id"] == "5" and r2["end_date"] == "2025-02-01" and not r2["is_active"]
    assert r2["body"] == "card text" and r2["display_format"] == "carousel"


def test_normalize_scrapecreators_strings():
    rec = {"ad_archive_id": "7", "page_name": "Y", "start_date_string": "2025-03-01T08:00:00.000Z",
           "end_date_string": "2025-03-10T08:00:00.000Z", "is_active": False, "snapshot": {"body": {"text": "hi"}}}
    r = ca.normalize_library_record(rec, "scrapecreators")
    assert (r["start_date"], r["end_date"], r["source"]) == ("2025-03-01", "2025-03-10", "scrapecreators")


def test_normalize_graph_record_drops_token_url():
    r = ca.normalize_graph_record(GRAPH_REC)
    assert r["ad_id"] == "456" and r["start_date"] == "2026-01-02" and r["end_date"] == "2026-03-15"
    assert r["is_active"] is False and r["body"] == "Tired of overdraft fees?"
    assert "SECRET" not in json.dumps(r)
    assert ca._redact("x?access_token=SECRET&y", "SECRET") == "x?access_token=[redacted]&y"


def test_days_running():
    today = date(2026, 3, 1)
    assert ta.days_running({"start_date": "2026-01-01", "is_active": True}, today) == 59
    assert ta.days_running({"start_date": "2026-01-01", "end_date": "2026-01-11", "is_active": False}, today) == 10
    assert ta.days_running({"start_date": None}, today) is None


def test_companion_turns_choice_into_other():
    raw = {"hook_type": {"type": "choice", "choice": "news", "probabilities": {"news": 0.9, "question": 0.1}},
           "hook_type_fits": {"type": "noul", "noul": 0.2}}
    assert ta.apply_labels(raw)["hook_type"] == "other"
    raw["hook_type_fits"]["noul"] = 0.9
    assert ta.apply_labels(raw)["hook_type"] == "news"


def _ad(i, adv, days, active, hook):
    return {"ad_id": str(i), "page_id": adv, "page_name": adv, "days_running": days, "is_active": active,
            "body": f"ad {i}", "labels": {"hook_type": hook}}


def test_survival_weights_each_advertiser_equally():
    rows = [_ad(i, "big", 5, False, "offer_first") for i in range(300)]          # 300 short ads, one advertiser
    rows += [_ad(1000 + i, f"a{i}", 90, True, "question") for i in range(3)]       # 3 survivors, 3 advertisers
    rows += [_ad(2000, "a0", 10, False, "question")]                               # a0 also has a short ad
    rows += [_ad(3000, "mid", 40, True, "question")]                               # undecided, excluded
    assert sr.bucket(rows[-1]) == "middle" and sr.bucket(rows[0]) == "short"
    res = sr.analyze(rows, min_n=3, min_advertisers=3)
    assert res["decided"] == 304 and res["counts"]["middle"] == 1
    # advertiser weights: big=1 (0 surv), a0 = 0.5+0.5 (0.5 surv), a1=1, a2=1 -> 2.5/4
    assert res["overall_survivor_rate"] == 0.625
    assert res["overall_survivor_rate_unweighted"] == round(3 / 304, 4)
    cell = {(p["question"], p["value"]): p for p in res["patterns"]}
    q = cell[("hook_type", "question")]
    assert q["n"] == 4 and q["advertisers"] == 3 and q["survivor_rate"] == round(2.5 / 3, 4)
    assert q["lift"] == round((2.5 / 3) / 0.625, 3) and q["trusted"]
    assert cell[("hook_type", "offer_first")]["trusted"] is False  # 300 ads but one advertiser
    assert "Top surviving patterns" in sr.report(res)


def test_brief_ranking_uses_lifts_and_brand():
    patterns = {"patterns": [
        {"question": "hook_type", "value": "question", "source": "jev", "lift": 1.6, "n": 40, "trusted": True},
        {"question": "hook_type", "value": "offer_first", "source": "jev", "lift": 0.5, "n": 40, "trusted": True},
        {"question": "price_shown", "value": "yes", "source": "jev", "lift": 1.3, "n": 30, "trusted": True},
        {"question": "display_format", "value": "video", "source": "code", "lift": 1.2, "n": 50, "trusted": True},
        {"question": "angle", "value": "comparison", "source": "jev", "lift": 3.0, "n": 4, "trusted": False},
    ]}
    briefs = [{"id": "weak", "hook": "50% off today", "body": "", "format": "image", "offer": "50% off"},
              {"id": "strong", "hook": "Still paying overdraft fees?", "body": "$0 fees.", "format": "video"},
              {"id": "mid", "hook": "Meet Cashwise", "body": "", "format": "video"}]

    def answers(state, qs):
        assert "p_angle__comparison" not in qs  # untrusted cells are not asked
        strong, weak = "overdraft" in state, "50% off" in state
        yes = lambda b: {"type": "noul", "noul": 0.95 if b else 0.05}
        return {"answers": {
            "p_hook_type__question": yes(strong), "p_hook_type__offer_first": yes(weak),
            "p_price_shown": yes(strong),
            "brand_fit": {"type": "score", "score": 3 if strong else 1, "confidence": 0.9},  # no distribution
            "brand_audience": yes(strong), "brand_avoid": yes(weak)}}

    ranked, pats = sb.score_briefs(briefs, patterns, brand="Plain talk. Avoid discounts.", answer_fn=answers,
                                   workers=1)
    assert [r["id"] for r in ranked] == ["strong", "mid", "weak"]
    top = ranked[0]
    assert top["score"] == 100.0 and any("hook_type=question" in x for x in top["reasons"])
    assert any("avoid" in x for x in ranked[-1]["reasons"])
    assert "# Brief ranking" in sb.report(ranked, pats)


def test_mock_chain_end_to_end(tmp_path):
    src = tmp_path / "apify.json"
    recs = []
    for i in range(60):
        r = json.loads(json.dumps(APIFY_REC))
        r["ad_archive_id"] = str(i)
        r["page_id"] = f"p{i % 6}"
        r["snapshot"]["body"]["text"] = f"Ad {i}: save ${i * 10} with our app."
        r["start_date"] = 1735689600 + i * 86400 * 5
        r["is_active"] = i % 3 == 0
        r["end_date"] = 0 if r["is_active"] else r["start_date"] + 86400 * (5 + i * 3)
        recs.append(r)
    src.write_text(json.dumps(recs))
    ads, tagged = tmp_path / "ads.jsonl", tmp_path / "tagged.jsonl"
    ca.main(["--from-apify", str(src), "--out", str(ads)])
    ta.main(["--mock", "--in", str(ads), "--out", str(tagged)])
    rows = [json.loads(l) for l in tagged.read_text().splitlines()]
    assert len(rows) == 60 and all(r["days_running"] is not None for r in rows)
    assert set(rows[0]["labels"]) == set(ta.LABEL_KEYS)
    pj, rep = tmp_path / "patterns.json", tmp_path / "survival.md"
    sr.main(["--in", str(tagged), "--report", str(rep), "--patterns", str(pj), "--min-n", "3"])
    briefs = tmp_path / "briefs.jsonl"
    briefs.write_text("\n".join(json.dumps({"id": i, "hook": f"hook {i}?", "body": "b", "format": "video"})
                                for i in range(4)))
    out, rrep = tmp_path / "ranked.jsonl", tmp_path / "ranked.md"
    sb.main(["--mock", "--briefs", str(briefs), "--patterns", str(pj), "--out", str(out), "--report", str(rrep)])
    ranked = [json.loads(l) for l in out.read_text().splitlines()]
    assert [r["rank"] for r in ranked] == [1, 2, 3, 4]
    assert all(0 <= r["score"] <= 100 for r in ranked)


def test_template_placeholders_fall_back_to_card_copy():
    rec = {"ad_archive_id": "1", "page_name": "Shop", "start_date": 1700000000, "is_active": True,
           "categories": ["UNKNOWN"],
           "snapshot": {"body": {"text": "{{product.brand}}"}, "title": "{{product.name}}",
                        "cards": [{"body": "Find the [categoryOne1] maker", "title": "Wood bat drop 3"},
                                  {"body": "Real swing trainer copy", "title": "Trainer"}]}}
    row = ca.normalize_library_record(rec)
    assert row["body"] == "Real swing trainer copy"
    assert row["title"] == "Wood bat drop 3"
    assert row["categories"] == ["UNKNOWN"]


def test_filter_drops_political_and_off_category():
    rows = [
        {"ad_id": "1", "page_name": "Bat Co", "body": "New baseball bat", "categories": ["UNKNOWN"]},
        {"ad_id": "2", "page_name": "Mayor", "body": "Youth baseball fields matter", "categories": ["POLITICAL"]},
        {"ad_id": "3", "page_name": "Reels", "body": "She married a monster", "categories": ["UNKNOWN"]},
    ]
    kept, dropped = ca.filter_rows(rows, require="baseball")
    assert [r["ad_id"] for r in kept] == ["1"]
    assert dropped == {"political": 1, "off_category": 1}


def test_category_question_added_and_off_category_dropped(tmp_path):
    seen = {}

    def fake(state, qs):
        seen.update(qs)
        on = "bat" in state
        return {"answers": {"in_category": {"type": "noul", "noul": 0.9 if on else 0.05}}, "usage": {}}

    rows = [{"ad_id": "1", "page_name": "Bat Co", "body": "New bat", "start_date": "2026-01-01", "is_active": True},
            {"ad_id": "2", "page_name": "Novels", "body": "She married a monster", "start_date": "2026-01-01",
             "is_active": True}]
    tagged = ta.tag_rows(rows, answer_fn=fake, category="baseball", workers=1)
    assert "in_category" in seen
    assert [r["labels"]["in_category"] for r in tagged] == ["yes", "no"]
    inp = tmp_path / "t.jsonl"
    inp.write_text("".join(json.dumps(r) + "\n" for r in tagged))
    sr.main(["--in", str(inp), "--report", str(tmp_path / "r.md"), "--patterns", str(tmp_path / "p.json")])
    res = json.loads((tmp_path / "p.json").read_text())
    assert res["ads"] == 1 and res["dropped_off_category"] == 1


def test_unsure_brand_avoid_fails_closed():
    pats = [{"question": "display_format", "value": "carousel", "source": "code", "lift": 1.4, "n": 50,
             "advertisers": 20, "trusted": True}]
    _, how = sb.pattern_questions(pats)
    brief = {"format": "carousel"}
    clean, _ = sb.score_brief(brief, {"brand_avoid": "no", "brand_fit": "3", "brand_audience": "yes"}, pats, how, True)
    unsure, reasons = sb.score_brief(brief, {"brand_avoid": "unsure", "brand_fit": "3", "brand_audience": "yes"},
                                     pats, how, True)
    assert clean == 100.0 and unsure == 70.0
    assert any("check by hand" in r for r in reasons)


def test_gate_uses_the_harness_confidence_gate():
    yn = {"type": "noul", "instructions": "Does the ad text show a price?"}
    assert jev.gate("q", yn, {"type": "noul", "noul": 0.71}) == "yes"
    assert jev.gate("q", yn, {"type": "noul", "noul": 0.29}) == "no"
    assert jev.gate("q", yn, {"type": "noul", "noul": 0.5}) == "unsure"
    assert jev.gate("q", yn, {"type": "noul"}) == "unsure"  # malformed -> unsure, never a guess
    ch = {"type": "choice", "instructions": "x", "criteria": {"a": "A", "b": "B"}}
    assert jev.gate("c", ch, {"choice": "a", "probabilities": {"a": 0.7, "b": 0.3}}) == "a"
    assert jev.gate("c", ch, {"choice": "a", "probabilities": {"a": 0.55, "b": 0.45}}) == "unsure"  # margin < 0.20


def test_mock_backend_goes_through_decision_log_client():
    resp = jev.ask("Ad text:\nSave $200 a month.", ta.QUESTIONS, backend="mock")
    assert resp["model"] == "jev-1.14" and set(resp["answers"]) == set(ta.QUESTIONS)
    assert resp == jev.ask("Ad text:\nSave $200 a month.", ta.QUESTIONS, backend="mock")  # deterministic


def test_budget_refuses_over_cap_and_settles_actual(tmp_path):
    b = bd.ApifyBudget(db_path=tmp_path / "ledger.db", cap_usd=1.0)
    with b.reserve(ca.APIFY_ACTOR, est_usd=0.6) as res:
        res.settle(0.4)
    assert b.spent_usd() == 0.4
    with pytest.raises(bd.BudgetExceeded):
        with b.reserve(ca.APIFY_ACTOR, est_usd=0.7):
            pass
    with pytest.raises(RuntimeError):
        with b.reserve(ca.APIFY_ACTOR, est_usd=0.5):
            raise RuntimeError("run failed")
    assert b.spent_usd() == 0.4  # a failed run releases its reservation
    assert bd.estimate_usd(ca.APIFY_ACTOR, 1000) == 0.75
    with pytest.raises(bd.BudgetUnavailable):
        bd.estimate_usd("someone/unpriced-actor", 10)


def test_budget_fails_closed_when_ledger_unusable(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(bd.BudgetUnavailable):
        bd.ApifyBudget(db_path=blocker / "ledger.db", cap_usd=5)


def test_apify_run_requires_a_spend_ceiling(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "t")
    with pytest.raises(SystemExit) as exc:
        ca.main(["--apify-run", "--search-terms", "baseball", "--countries", "US", "--out", str(tmp_path / "a.jsonl")])
    assert "--max-usd" in str(exc.value)


def test_apify_run_caps_charge_and_settles_usage(monkeypatch, tmp_path):
    calls = []

    def fake(url, token, data=None, timeout=60):
        calls.append(url)
        if "/runs?" in url:
            return {"data": {"id": "r1", "status": "SUCCEEDED", "defaultDatasetId": "d1", "usageTotalUsd": 0.31}}
        return [APIFY_REC]

    monkeypatch.setattr(ca, "_apify_json", fake)
    b = bd.ApifyBudget(db_path=tmp_path / "ledger.db", cap_usd=10)
    items = ca.run_apify("t", "budget app", ["US"], max_ads=1000, max_usd=0.5, budget=b)
    assert items == [APIFY_REC]
    assert "maxTotalChargeUsd=0.5" in calls[0]  # the smaller of list estimate (0.76) and --max-usd
    assert b.spent_usd() == 0.31

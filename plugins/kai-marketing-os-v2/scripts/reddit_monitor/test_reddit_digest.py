from __future__ import annotations

import json
from pathlib import Path

import reddit_digest as digest


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "status_code": 20000,
            "status_message": "Ok.",
            "tasks": [{
                "status_code": 20000,
                "status_message": "Ok.",
                "cost": 0.01,
                "result": [{
                    "items": [{
                        "type": "organic",
                        "title": "Need a receptionist for after-hours calls",
                        "url": "https://www.facebook.com/groups/hvacowners/posts/123",
                        "description": "We keep missing calls while the team is out.",
                        "timestamp": "2026-07-24 12:00:00 +00:00",
                        "rank_group": 1,
                    }],
                }],
            }],
        }


def test_fetch_google_search_normalizes_public_facebook_result(monkeypatch):
    monkeypatch.setenv("DATAFORSEO_AUTH_B64", "dGVzdDp0ZXN0")
    monkeypatch.setattr(digest.requests, "post", lambda *args, **kwargs: _Response())

    rows, cost = digest.fetch_google_search(
        'site:facebook.com/groups "need a receptionist"', 10
    )

    assert rows == [{
        "id": "search:https://www.facebook.com/groups/hvacowners/posts/123",
        "title": "Need a receptionist for after-hours calls",
        "url": "https://www.facebook.com/groups/hvacowners/posts/123",
        "source": "facebook_group",
        "source_context": "Facebook Group via Google",
        "subreddit": "",
        "content": "We keep missing calls while the team is out.",
        "published_at": "2026-07-24 12:00:00 +00:00",
        "search_query": 'site:facebook.com/groups "need a receptionist"',
        "search_rank": 1,
    }]
    assert cost == 0.01


def test_collect_candidates_dedupes_same_url_across_queries(tmp_path, monkeypatch):
    row = {
        "id": "search:https://www.facebook.com/groups/hvacowners/posts/123",
        "title": "Need a receptionist",
        "url": "https://www.facebook.com/groups/hvacowners/posts/123",
        "source": "facebook_group",
        "source_context": "Facebook Group via Google",
        "subreddit": "",
        "content": "We keep getting missed calls.",
        "published_at": "",
        "search_query": "query",
    }
    monkeypatch.setattr(digest, "fetch_subreddit", lambda *args: [])
    monkeypatch.setattr(
        digest, "fetch_google_search", lambda *args: ([dict(row)], 0.01)
    )
    seen_path = tmp_path / "seen.json"
    profile = {
        "subreddits": [],
        "posts_per_sub": 10,
        "search_queries": ["one", "two"],
        "search_results_per_query": 10,
        "search_daily_query_cap": 8,
        "trigger_keywords": ["missed calls"],
        "seen_limit": 100,
    }

    rows = digest.collect_candidates(profile, seen_path)

    assert len(rows) == 1
    assert rows[0]["matched_keywords"] == ["missed calls"]
    state = json.loads(seen_path.read_text(encoding="utf-8"))
    assert state["posts"] == []
    assert list(state["pending_candidates"]) == [row["id"]]
    assert state["search_cost_usd_by_date"][digest.date.today().isoformat()] == 0.02

    digest.finalize_candidates(seen_path, [row["id"]], 100)
    state = json.loads(seen_path.read_text(encoding="utf-8"))
    assert state["posts"] == [row["id"]]
    assert state["pending_candidates"] == {}


def test_collect_candidates_runs_each_paid_query_once_per_day(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(digest, "fetch_subreddit", lambda *args: [])
    monkeypatch.setattr(
        digest,
        "fetch_google_search",
        lambda query, *args: (calls.append(query) or [], 0.01),
    )
    seen_path = tmp_path / "seen.json"
    profile = {
        "subreddits": [],
        "posts_per_sub": 10,
        "search_queries": ["one"],
        "search_results_per_query": 10,
        "search_daily_query_cap": 8,
        "trigger_keywords": ["missed calls"],
        "seen_limit": 100,
    }

    digest.collect_candidates(profile, seen_path)
    digest.collect_candidates(profile, seen_path)

    assert calls == ["one"]


def test_collect_candidates_claims_failed_paid_query_before_call(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(digest, "fetch_subreddit", lambda *args: [])

    def fail(query, *args):
        calls.append(query)
        raise TimeoutError("provider timeout after request")

    monkeypatch.setattr(digest, "fetch_google_search", fail)
    seen_path = tmp_path / "seen.json"
    profile = {
        "subreddits": [],
        "posts_per_sub": 10,
        "search_queries": ["one"],
        "search_results_per_query": 10,
        "search_daily_query_cap": 8,
        "search_max_daily_cost_usd": 1.0,
        "search_cost_guard_per_query_usd": 0.02,
        "trigger_keywords": ["missed calls"],
        "seen_limit": 100,
    }

    digest.collect_candidates(profile, seen_path)
    digest.collect_candidates(profile, seen_path)

    assert calls == ["one"]
    state = json.loads(seen_path.read_text(encoding="utf-8"))
    assert state["search_reserved_cost_usd_by_date"][
        digest.date.today().isoformat()
    ] == 0.02


def test_collect_candidates_stops_before_daily_budget(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(digest, "fetch_subreddit", lambda *args: [])
    monkeypatch.setattr(
        digest,
        "fetch_google_search",
        lambda query, *args: (calls.append(query) or [], 0.01),
    )
    profile = {
        "subreddits": [],
        "posts_per_sub": 10,
        "search_queries": ["one", "two", "three"],
        "search_results_per_query": 10,
        "search_daily_query_cap": 8,
        "search_max_daily_cost_usd": 0.04,
        "search_cost_guard_per_query_usd": 0.02,
        "trigger_keywords": ["missed calls"],
        "seen_limit": 100,
    }

    digest.collect_candidates(profile, tmp_path / "seen.json")

    assert calls == ["one", "two"]


def test_expanded_search_queries_dedupes_and_expands_verticals():
    queries = digest.expanded_search_queries({
        "search_queries": ["fixed", "fixed"],
        "search_verticals": ["HVAC"],
        "search_query_templates": ["{vertical} missed calls", "fixed"],
    })

    assert queries == ["fixed", "HVAC missed calls"]


def test_validate_public_decision_requires_exact_buyer_evidence():
    post = {
        "title": "Anyone recommend a virtual receptionist?",
        "content": "We keep missing calls while our HVAC techs are out.",
    }
    result = digest.validate_public_decision({
        "score": 92,
        "reason": "Direct operational pain.",
        "angle": "Share measured inbound-call capture.",
        "actor_role": "buyer",
        "intent_type": "operational_pain",
        "confidence": 0.94,
        "evidence_quote": "We keep missing calls while our HVAC techs are out.",
    }, post)

    assert result["score"] == 92
    assert result["evidence_valid"] is True


def test_validate_public_decision_caps_vendor_with_buyer_language():
    post = {
        "title": "Receptionist available for Cheyenne businesses",
        "content": "We can help if you keep missing calls after hours.",
    }
    result = digest.validate_public_decision({
        "score": 90,
        "reason": "The topic matches.",
        "angle": "Pitch KaiCalls.",
        "actor_role": "vendor",
        "intent_type": "operational_pain",
        "confidence": 0.99,
        "evidence_quote": "keep missing calls after hours",
    }, post)

    assert result["score"] == 25
    assert result["angle"] == ""


def test_validate_public_decision_rejects_paraphrased_evidence():
    result = digest.validate_public_decision({
        "score": 90,
        "actor_role": "buyer",
        "intent_type": "direct_need",
        "confidence": 0.95,
        "evidence_quote": "We miss every call after hours.",
    }, {
        "title": "Need some help",
        "content": "Our phone coverage is not great.",
    })

    assert result["score"] == 25
    assert result["evidence_quote"] == ""


def test_render_html_supports_legacy_reddit_rows():
    html = digest.render_html(
        {"page_title": "Opportunities"},
        [{
            "score": 90,
            "reason": "Direct missed-call pain.",
            "angle": "Measured call capture.",
            "subreddit": "smallbusiness",
            "title": "How do you handle missed calls?",
            "url": "https://reddit.com/example",
        }],
        "2026-07-25",
    )

    assert "r/smallbusiness" in html
    assert "How do you handle missed calls?" in html
    assert "Public sources only" in html

from __future__ import annotations

import json
from datetime import date

import review_prospecting as prospecting


def test_pain_reviews_prefilters_phone_and_callback_evidence():
    rows = prospecting.pain_reviews([
        {"text": "Nobody picked up, and they never called back."},
        {"text": "The technician installed the wrong part."},
    ])

    assert len(rows) == 1
    assert "nobody picked up" in rows[0]["matched_pain"]


def test_validate_qualification_requires_exact_quote():
    source = "I called three times and nobody picked up."
    good = prospecting.validate_qualification({
        "is_fit": True,
        "score": 91,
        "confidence": 0.93,
        "pain_type": "unanswered_phone",
        "evidence_quote": "nobody picked up",
        "reason": "Direct phone-answering failure.",
        "angle": "Confirm whether this is still happening.",
    }, source)
    invented = prospecting.validate_qualification({
        "is_fit": True,
        "score": 95,
        "confidence": 0.99,
        "pain_type": "unanswered_phone",
        "evidence_quote": "They never answer after hours.",
    }, source)

    assert good["is_fit"] is True
    assert good["score"] == 91
    assert invented["is_fit"] is False
    assert invented["score"] == 25


def test_select_daily_segments_is_bounded_and_repeatable():
    profile = {
        "prospecting_categories": ["plumber", "electrician"],
        "prospecting_locations": [
            {"name": "Houston", "coordinate": "1,2,25"},
            {"name": "Phoenix", "coordinate": "3,4,25"},
        ],
        "prospecting_daily_listing_cap": 3,
    }

    first = prospecting.select_daily_segments(profile, date(2026, 7, 25))
    second = prospecting.select_daily_segments(profile, date(2026, 7, 25))

    assert first == second
    assert len(first) == 3
    assert len({(row["category"], row["location_name"]) for row in first}) == 3


def test_run_polls_ready_task_and_emits_named_prospect(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({
        "prospecting_listing_days_attempted": ["2026-07-25"],
        "pending_review_tasks": {
            "task-1": {
                "business": {
                    "business_id": "cid-1",
                    "name": "Reliable HVAC",
                    "phone": "+15551212",
                    "website": "https://reliable.example",
                    "maps_url": "https://maps.example/reliable",
                    "market": "Houston, TX",
                    "category": "HVAC contractor",
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(
        prospecting,
        "poll_review_task",
        lambda *args, **kwargs: (
            "ready",
            [{
                "review_id": "r-1",
                "text": "I called twice and nobody picked up.",
                "timestamp": "2026-07-20 10:00:00 +00:00",
                "rating": 2,
                "review_url": "https://reviews.example/r-1",
            }],
            "https://maps.example/check",
        ),
    )

    rows = prospecting.run(
        {},
        state_path,
        "Basic test",
        lambda business, reviews: {
            "is_fit": True,
            "score": 92,
            "confidence": 0.95,
            "pain_type": "unanswered_phone",
            "evidence_quote": "nobody picked up",
            "reason": "A recent customer could not reach the business.",
            "angle": "Verify the present call-handling workflow.",
        },
        lambda path, data: path.write_text(json.dumps(data), encoding="utf-8"),
        today=date(2026, 7, 25),
    )

    assert len(rows) == 1
    assert rows[0]["title"] == "Reliable HVAC"
    assert rows[0]["prospect"]["phone"] == "+15551212"
    assert rows[0]["url"] == "https://reviews.example/r-1"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["pending_review_tasks"] == {}
    assert state["reviewed_business_ids"] == ["cid-1"]
    assert list(state["ready_prospects"]) == ["review-prospect:cid-1"]

    prospecting.finalize_ready(
        state_path,
        ["review-prospect:cid-1"],
        lambda path, data: path.write_text(json.dumps(data), encoding="utf-8"),
    )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["ready_prospects"] == {}


def test_run_reserves_before_paid_listing_and_review_calls(
    tmp_path, monkeypatch
):
    businesses = [
        {
            "business_id": f"cid-{index}",
            "cid": f"{index}",
            "place_id": "",
            "name": f"Business {index}",
        }
        for index in range(10)
    ]
    monkeypatch.setattr(
        prospecting,
        "fetch_business_listings",
        lambda *args, **kwargs: (businesses, 0.02),
    )
    monkeypatch.setattr(
        prospecting,
        "submit_review_tasks",
        lambda auth, rows, depth, **kwargs: (
            [
                {"task_id": f"task-{index}", "business": row}
                for index, row in enumerate(rows)
            ],
            0.015,
        ),
    )
    profile = {
        "prospecting_categories": ["plumber"],
        "prospecting_locations": [
            {"name": "Houston", "coordinate": "1,2,25"},
        ],
        "prospecting_daily_listing_cap": 1,
        "prospecting_listing_limit": 10,
        "prospecting_daily_review_task_cap": 10,
        "prospecting_review_depth": 20,
        "prospecting_max_daily_cost_usd": 0.7,
        "prospecting_listing_cost_guard_usd": 0.03,
        "prospecting_review_task_cost_guard_usd": 0.005,
    }
    state_path = tmp_path / "state.json"

    prospecting.run(
        profile,
        state_path,
        "Basic test",
        lambda *args: {},
        lambda path, data: path.write_text(json.dumps(data), encoding="utf-8"),
        today=date(2026, 7, 25),
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["prospecting_reserved_cost_usd_by_date"]["2026-07-25"] == 0.08
    assert state["prospecting_cost_usd_by_date"]["2026-07-25"] == 0.035
    assert len(state["pending_review_tasks"]) == 10


def test_submit_review_tasks_keeps_businesses_aligned(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status_code": 20000,
                "tasks": [{
                    "id": "task-valid",
                    "status_code": 20100,
                    "cost": 0.001,
                }],
            }

    posted = {}

    def fake_post(*args, **kwargs):
        posted["json"] = kwargs["json"]
        return Response()

    monkeypatch.setattr(prospecting.requests, "post", fake_post)
    invalid = {"business_id": "invalid", "name": "Invalid"}
    valid = {
        "business_id": "cid-valid",
        "cid": "123",
        "name": "Valid",
    }

    submitted, cost = prospecting.submit_review_tasks(
        "Basic test", [invalid, valid], 20
    )

    assert posted["json"][0]["cid"] == "123"
    assert submitted[0]["business"]["business_id"] == "cid-valid"
    assert cost == 0.001


def test_run_expires_abandoned_review_task(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({
        "prospecting_listing_days_attempted": ["2026-07-25"],
        "pending_review_tasks": {
            "stuck-task": {
                "submitted_on": "2026-07-20",
                "business": {
                    "business_id": "cid-stuck",
                    "name": "Stuck HVAC",
                },
            },
        },
    }), encoding="utf-8")

    def fail_if_polled(*args, **kwargs):
        raise AssertionError("expired task should not be polled")

    monkeypatch.setattr(prospecting, "poll_review_task", fail_if_polled)
    prospecting.run(
        {},
        state_path,
        "Basic test",
        lambda *args: {},
        lambda path, data: path.write_text(json.dumps(data), encoding="utf-8"),
        today=date(2026, 7, 25),
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["pending_review_tasks"] == {}
    assert state["expired_review_tasks"][0]["task_id"] == "stuck-task"


def test_run_rechecks_business_after_refresh_window(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({
        "reviewed_business_dates": {"cid-old": "2026-05-01"},
    }), encoding="utf-8")
    submitted_ids = []
    monkeypatch.setattr(
        prospecting,
        "fetch_business_listings",
        lambda *args, **kwargs: ([{
            "business_id": "cid-old",
            "cid": "123",
            "name": "Old HVAC",
        }], 0.01),
    )

    def submit(auth, businesses, depth, **kwargs):
        submitted_ids.extend(row["business_id"] for row in businesses)
        return [], 0.0

    monkeypatch.setattr(prospecting, "submit_review_tasks", submit)
    profile = {
        "prospecting_categories": ["hvac_contractor"],
        "prospecting_locations": [
            {"name": "Houston", "coordinate": "1,2,25"},
        ],
        "prospecting_daily_listing_cap": 1,
        "prospecting_listing_limit": 10,
        "prospecting_daily_review_task_cap": 10,
        "prospecting_review_depth": 20,
        "prospecting_business_refresh_days": 60,
        "prospecting_max_daily_cost_usd": 0.7,
        "prospecting_listing_cost_guard_usd": 0.03,
        "prospecting_review_task_cost_guard_usd": 0.005,
    }

    prospecting.run(
        profile,
        state_path,
        "Basic test",
        lambda *args: {},
        lambda path, data: path.write_text(json.dumps(data), encoding="utf-8"),
        today=date(2026, 7, 25),
    )

    assert submitted_ids == ["cid-old"]

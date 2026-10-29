"""ECO outcome verdicts — tickets, reads, and the four verdicts.

Doctrine under test: "Outcome verdicts" in docs/system/eco-completion-standard.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from kai.runtime.eco import (
    OUTCOME_DIDNT_WORK,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_PARTIAL,
    OUTCOME_WORKED,
    VERDICT_CLOSED,
    VERDICT_SHIPPED,
    EcoError,
    EcoFloors,
    EcoRecordStore,
    outcome_verdict,
)

ACTOR = "content_log"
MEASURE = "kai-measure:gsc"
SHIPPED = "2026-10-01T12:00:00+00:00"


@pytest.fixture(scope="module")
def floors() -> EcoFloors:
    return EcoFloors.load()


@pytest.fixture
def store(tmp_path: Path, floors: EcoFloors) -> EcoRecordStore:
    return EcoRecordStore(base_dir=tmp_path / "eco", floors=floors)


def baseline(**overrides) -> dict:
    base = {
        "metric": "clicks", "source": "google_search_console", "scope": "site",
        "site": "kaicalls", "value": 400, "window_end": "2026-10-01",
        "captured_at": "2026-10-01T12:00:01+00:00",
    }
    base.update(overrides)
    return base


def published_blog_evidence() -> list:
    """E5/C3 evidence for a blog post written by someone other than the gate."""
    def ev(kind, **fields):
        return {"kind": kind, "locator": f"locator/{kind}", "observed_at": "2026-10-01T11:00:00Z", **fields}

    return [
        ev("craft_gate_pass", verifier="kai-quality-gates"),
        ev("craft_independent_review", verifier="Connor"),
        ev("approval_review", sha256="a" * 64, verifier="Connor"),
        ev("provider_receipt", verifier="wordpress-adapter", observed_at="2026-10-01T12:00:00Z"),
        ev("independent_verification", expected="200", observed="200", verifier="content-obligation-check",
           observed_at="2026-10-01T12:05:00Z"),
    ]


def register(store: EcoRecordStore, subject: str = "content:a", **kwargs) -> dict:
    params = dict(subject_id=subject, work_type="blog-post", claimed_by=ACTOR,
                  receipt={"url": "https://kaicalls.com/blog/a"}, baseline=baseline(),
                  brand_id="kaicalls", shipped_at=SHIPPED)
    params.update(kwargs)
    return store.register_shipped(**params)


def read_and_verify(store: EcoRecordStore, record_id: str, pre, post) -> dict:
    store.record_read(record_id, verifier=MEASURE, pre=pre, post=post)
    return store.verify(record_id, verifier=MEASURE)


# ---------------------------------------------------------------------------
# The pure verdict
# ---------------------------------------------------------------------------


def test_worked_when_threshold_cleared():
    result = outcome_verdict(100, 130, 110)
    assert result["verdict"] == OUTCOME_WORKED
    assert result["lift"] == 0.3


def test_partial_when_positive_but_short_of_threshold():
    assert outcome_verdict(100, 105, 110)["verdict"] == OUTCOME_PARTIAL


def test_didnt_work_when_flat_or_negative():
    assert outcome_verdict(100, 100, 110)["verdict"] == OUTCOME_DIDNT_WORK
    assert outcome_verdict(100, 80, 110)["verdict"] == OUTCOME_DIDNT_WORK


def test_inconclusive_below_min_sample():
    result = outcome_verdict(3, 9, 4, min_sample=50)
    assert result["verdict"] == OUTCOME_INCONCLUSIVE
    assert "min_sample" in result["reason"]


def test_inconclusive_on_data_gap_never_zero():
    assert outcome_verdict(None, 130, 110)["verdict"] == OUTCOME_INCONCLUSIVE
    assert outcome_verdict(100, None, 110)["verdict"] == OUTCOME_INCONCLUSIVE


def test_direction_down_rewards_a_lower_number():
    """CPA falling from 40 to 30 against a 36 threshold worked."""
    assert outcome_verdict(40, 30, 36, direction="down")["verdict"] == OUTCOME_WORKED
    assert outcome_verdict(40, 38, 36, direction="down")["verdict"] == OUTCOME_PARTIAL
    assert outcome_verdict(40, 45, 36, direction="down")["verdict"] == OUTCOME_DIDNT_WORK


def test_explicit_sample_overrides_value_magnitude():
    assert outcome_verdict(40, 30, 36, direction="down", min_sample=10, sample=4)["verdict"] == OUTCOME_INCONCLUSIVE


def test_unknown_direction_is_refused():
    with pytest.raises(EcoError):
        outcome_verdict(1, 2, 2, direction="sideways")


# ---------------------------------------------------------------------------
# Floors
# ---------------------------------------------------------------------------


def test_verdict_windows_declared(floors: EcoFloors):
    assert floors.work_type("paid-ad-campaign").verdict_window_days == 3
    assert floors.work_type("paid-ad-campaign").direction == "down"
    for name in ("blog-post", "page-refresh", "landing-page", "social-post"):
        assert floors.work_type(name).verdict_window_days == 7
        assert floors.work_type(name).max_reads == 4
    assert floors.work_type("internal-research").verdict_window_days is None


def test_floors_without_verdict_block_still_load():
    """Backwards compatible: a registry with no outcome_verdicts block parses."""
    floors = EcoFloors({"evidence_kinds": {}, "work_types": {"x": {"outcome": {"window_days": 9}}}})
    work = floors.work_type("x")
    assert work.verdict_window_days is None and work.max_reads == 4 and work.direction == "up"


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------


def test_register_is_idempotent_on_subject(store: EcoRecordStore):
    first = register(store)
    second = register(store, baseline=baseline(value=9999))
    assert first["record_id"] == second["record_id"]
    assert second["ticket"]["baseline"]["value"] == 400
    assert len(store.list_records()) == 1
    assert "computed" not in first  # registering never issues a verdict


def test_register_attaches_to_an_existing_claim(store: EcoRecordStore):
    claimed = store.claim(subject_id="content:a", step_id="blog.publish", work_type="blog-post", claimed_by="writer")
    ticketed = register(store)
    assert ticketed["record_id"] == claimed["record_id"]
    assert ticketed["claimed_by"] == "writer"


def test_baseline_after_ship_is_rejected_not_repaired(store: EcoRecordStore):
    record = register(store, baseline=baseline(window_end="2026-10-05"))
    ticket = record["ticket"]
    assert ticket["baseline"] is None
    assert "outcome_predeclared" in ticket["unmeasurable_reason"]
    with pytest.raises(EcoError, match="unmeasurable"):
        store.record_read(record["record_id"], verifier=MEASURE, pre={"value": 1}, post={"value": 2})


def test_no_baseline_means_unmeasurable(store: EcoRecordStore):
    record = register(store, baseline=None)
    assert record["ticket"]["unmeasurable_reason"] == "no pre-ship baseline captured"
    assert store.due_for_measurement(datetime(2027, 1, 1, tzinfo=timezone.utc)) == []


def test_actor_cannot_smuggle_a_verdict(store: EcoRecordStore):
    with pytest.raises(EcoError, match="verdict"):
        register(store, baseline={**baseline(), "verdict": "worked"})


def test_due_after_window_plus_lag(store: EcoRecordStore):
    register(store)
    # 7-day window + 1 day + GSC 3-day lag => due 2026-10-12T12:00.
    assert store.due_for_measurement(datetime(2026, 10, 12, 11, tzinfo=timezone.utc)) == []
    assert len(store.due_for_measurement(datetime(2026, 10, 12, 13, tzinfo=timezone.utc))) == 1


def test_actor_cannot_take_its_own_read(store: EcoRecordStore):
    record = register(store)
    with pytest.raises(EcoError, match="claiming actor"):
        store.record_read(record["record_id"], verifier=ACTOR, pre={"value": 1}, post={"value": 2})


def test_record_read_does_not_issue_a_verdict(store: EcoRecordStore):
    record = register(store)
    after = store.record_read(record["record_id"], verifier=MEASURE, pre={"value": 400}, post={"value": 500})
    assert "computed" not in after
    assert after["ticket"]["reads"][0]["verifier"] == MEASURE


def test_worked_maps_to_o4(store: EcoRecordStore):
    record = register(store)
    verified = read_and_verify(store, record["record_id"], {"value": 400, "sample": 400}, {"value": 500, "sample": 500})
    outcome = verified["computed"]["outcome"]
    assert outcome["verdict"] == OUTCOME_WORKED
    assert outcome["final"] is True
    assert outcome["verdict_by"] == MEASURE
    assert outcome["window_days"] == 7 and outcome["reads"] == 1 and outcome["source"] == "google_search_console"
    assert verified["computed"]["grade"]["O"] == 4
    assert verified["evidence"] == []  # derived O evidence is computed, never appended to the actor's list


def test_didnt_work_maps_to_o3_and_closed_means_measured_not_won(store: EcoRecordStore):
    """A blog post with E5/C3 evidence that didn't work is still CLOSED (O3 floor)."""
    store.claim(subject_id="content:a", step_id="blog.publish", work_type="blog-post",
                claimed_by=ACTOR, evidence=published_blog_evidence())
    record = register(store)
    verified = read_and_verify(store, record["record_id"], {"value": 400}, {"value": 350})
    assert verified["computed"]["outcome"]["verdict"] == OUTCOME_DIDNT_WORK
    assert verified["computed"]["grade"]["O"] == 3
    assert verified["computed"]["verdict"] == VERDICT_CLOSED


def test_partial_maps_to_o3(store: EcoRecordStore):
    record = register(store)
    verified = read_and_verify(store, record["record_id"], {"value": 400}, {"value": 420})
    assert verified["computed"]["outcome"]["verdict"] == OUTCOME_PARTIAL
    assert verified["computed"]["grade"]["O"] == 3


def test_inconclusive_writes_blocked_failure_and_schedules_next_window(store: EcoRecordStore):
    record = register(store)
    verified = read_and_verify(store, record["record_id"], {"error": "No GSC credentials"}, {"error": "No GSC credentials"})
    outcome = verified["computed"]["outcome"]
    assert outcome["verdict"] == OUTCOME_INCONCLUSIVE
    assert outcome["final"] is False
    assert outcome["next_check_at"].startswith("2026-10-19")  # 2 x 7d + 1 + 3 lag
    assert verified["computed"]["grade"]["O"] == 0
    failures = store.failures()
    assert len(failures) == 1
    assert failures[0]["condition"] == "blocked"
    assert failures[0]["failed_axis"] == ["O"]
    assert failures[0]["retryability"] == "waiting"
    assert failures[0]["next_check_at"] == outcome["next_check_at"]


def test_final_inconclusive_after_max_reads_stays_shipped(store: EcoRecordStore):
    store.claim(subject_id="content:a", step_id="blog.publish", work_type="blog-post",
                claimed_by=ACTOR, evidence=published_blog_evidence())
    record = register(store)
    for _ in range(4):
        verified = read_and_verify(store, record["record_id"], {"value": 3}, {"value": 9})
    outcome = verified["computed"]["outcome"]
    assert outcome["verdict"] == OUTCOME_INCONCLUSIVE and outcome["final"] is True and outcome["reads"] == 4
    assert verified["computed"]["verdict"] == VERDICT_SHIPPED
    assert store.due_for_measurement(datetime(2027, 6, 1, tzinfo=timezone.utc)) == []
    with pytest.raises(EcoError):
        store.record_read(record["record_id"], verifier=MEASURE, pre={"value": 1}, post={"value": 2})
    retry = sorted(f["retryability"] for f in store.failures())
    assert retry == ["abandoned", "waiting", "waiting", "waiting"]  # one record per read, last is final


def test_final_verdict_refuses_further_reads(store: EcoRecordStore):
    record = register(store)
    read_and_verify(store, record["record_id"], {"value": 400}, {"value": 500})
    with pytest.raises(EcoError, match="final"):
        store.record_read(record["record_id"], verifier=MEASURE, pre={"value": 1}, post={"value": 2})


def test_records_without_tickets_verify_exactly_as_before(store: EcoRecordStore):
    record = store.claim(subject_id="wi", step_id="s", work_type="internal-research", claimed_by="a")
    verified = store.verify(record["record_id"], verifier="gate")
    assert "outcome" not in verified["computed"]

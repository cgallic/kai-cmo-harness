"""ECO completion standard — grading, verdicts, and the failure record.

Doctrine under test: docs/system/eco-completion-standard.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from kai.runtime.eco import (
    VERDICT_CLOSED,
    VERDICT_OPEN,
    VERDICT_SHIPPED,
    EcoError,
    EcoFloors,
    EcoRecordStore,
    grade,
)

ACTOR = "writer-agent"
GATE = "kai-eco-gate"


@pytest.fixture(scope="module")
def floors() -> EcoFloors:
    return EcoFloors.load()


@pytest.fixture
def store(tmp_path: Path, floors: EcoFloors) -> EcoRecordStore:
    return EcoRecordStore(base_dir=tmp_path / "eco", floors=floors)


def ev(kind: str, **fields) -> dict:
    base = {"kind": kind, "locator": f"locator/{kind}", "observed_at": "2026-07-20T12:00:00Z"}
    base.update(fields)
    return base


def published_blog_evidence() -> list:
    """A blog post that genuinely reached E5/C3, with an O1 baseline."""
    return [
        ev("artifact_exists", produced_by=ACTOR, observed_at="2026-07-20T10:00:00Z"),
        ev(
            "outcome_baseline",
            metric="organic_clicks",
            source="google_search_console",
            baseline="0",
            threshold="120",
            window="30d",
            owner="Connor",
            observed_at="2026-07-20T10:30:00Z",
        ),
        ev("craft_gate_pass", verifier="kai-quality-gates", verifier_substrate="deterministic"),
        ev("craft_independent_review", verifier="Connor", verifier_substrate="human"),
        ev("approval_review", sha256="a" * 64, verifier="Connor", verifier_substrate="human"),
        ev("provider_receipt", verifier="wordpress-adapter", verifier_substrate="deterministic",
           observed_at="2026-07-20T13:00:00Z"),
        ev(
            "independent_verification",
            expected="200 and approved marker",
            observed="200 and marker matched",
            verifier="content-obligation-check",
            verifier_substrate="deterministic",
            observed_at="2026-07-20T13:05:00Z",
        ),
    ]


# ---------------------------------------------------------------------------
# Floor registry
# ---------------------------------------------------------------------------


def test_floors_load_and_resolve_aliases(floors: EcoFloors):
    assert floors.work_type("blog-post").floor == {"E": 5, "C": 3, "O": 3}
    # `seo-audit` is an alias of `audit-report`
    assert floors.work_type("seo-audit").name == "audit-report"
    assert floors.work_type("google-ads").name == "paid-ad-campaign"


def test_unknown_work_type_is_refused(floors: EcoFloors):
    with pytest.raises(EcoError, match="unknown work type"):
        floors.work_type("vibes")


def test_cold_email_requires_field_standard_craft(floors: EcoFloors):
    """Cold email's residue is legal, not editorial — C4, not C3."""
    assert floors.work_type("cold-email").floor["C"] == 4


def test_paid_media_requires_attribution(floors: EcoFloors):
    paid = floors.work_type("paid-ad-campaign")
    assert paid.attribution_required is True
    assert paid.spend_authority is True


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------


def test_shipped_when_execution_and_craft_met_but_outcome_open(floors: EcoFloors):
    result = grade(
        published_blog_evidence(),
        work_type=floors.work_type("blog-post"),
        claimed_by=ACTOR,
        floors=floors,
    )
    assert result.grade == {"E": 5, "C": 3, "O": 1}
    assert result.verdict == VERDICT_SHIPPED
    assert result.terminal is False
    assert result.unmet == ["O3"]
    assert result.outcome_due_at is not None


def test_closed_only_when_outcome_observed(floors: EcoFloors):
    evidence = published_blog_evidence() + [
        ev(
            "outcome_observation",
            observed="184 clicks",
            verifier="gsc-connector",
            verifier_substrate="deterministic",
            observed_at="2026-08-19T12:00:00Z",
        )
    ]
    result = grade(evidence, work_type=floors.work_type("blog-post"), claimed_by=ACTOR, floors=floors)
    assert result.grade["O"] == 3
    assert result.verdict == VERDICT_CLOSED
    assert result.terminal is True


def test_artifact_alone_is_not_completion(floors: EcoFloors):
    """A draft on disk is E1. The floor is E5. It stays open."""
    result = grade(
        [ev("artifact_exists", produced_by=ACTOR)],
        work_type=floors.work_type("blog-post"),
        claimed_by=ACTOR,
        floors=floors,
    )
    assert result.grade["E"] == 1
    assert result.verdict == VERDICT_OPEN
    assert "E5" in result.unmet


def test_self_verified_evidence_is_discarded(floors: EcoFloors):
    """Honest quorum: the actor cannot be its own verifier."""
    evidence = published_blog_evidence()
    for entry in evidence:
        if entry.get("verifier"):
            entry["verifier"] = ACTOR
    result = grade(evidence, work_type=floors.work_type("blog-post"), claimed_by=ACTOR, floors=floors)
    assert result.grade["E"] == 1  # only artifact_exists survives
    assert result.verdict == VERDICT_OPEN
    assert any("honest quorum" in r["reason"] for r in result.rejected)


def test_unverified_evidence_without_a_named_verifier_is_discarded(floors: EcoFloors):
    result = grade(
        [ev("provider_receipt")],  # no verifier field
        work_type=floors.work_type("social-post"),
        claimed_by=ACTOR,
        floors=floors,
    )
    assert result.grade["E"] == 0
    assert any("no verifier named" in r["reason"] for r in result.rejected)


def test_evidence_missing_required_fields_is_discarded(floors: EcoFloors):
    """An outcome_baseline without a threshold or owner is not a baseline."""
    result = grade(
        [ev("outcome_baseline", metric="clicks", source="gsc", baseline="0")],
        work_type=floors.work_type("blog-post"),
        claimed_by=ACTOR,
        floors=floors,
    )
    assert result.grade["O"] == 0
    reason = result.rejected[0]["reason"]
    assert "threshold" in reason and "owner" in reason


def test_baseline_written_after_ship_is_rejected(floors: EcoFloors):
    """A baseline recorded after the work went live is not a baseline."""
    evidence = published_blog_evidence()
    for entry in evidence:
        if entry["kind"] == "outcome_baseline":
            entry["observed_at"] = "2026-07-25T10:00:00Z"  # after the E4 receipt
    result = grade(evidence, work_type=floors.work_type("blog-post"), claimed_by=ACTOR, floors=floors)
    assert result.grade["O"] == 0
    assert any("outcome_predeclared" in v for v in result.violations)
    assert result.verdict == VERDICT_OPEN


def test_live_channel_without_approval_violates_invariant(floors: EcoFloors):
    """E4+ on a spend or live channel with no hash-pinned approval is never SHIPPED."""
    evidence = [e for e in published_blog_evidence() if e["kind"] != "approval_review"]
    result = grade(evidence, work_type=floors.work_type("blog-post"), claimed_by=ACTOR, floors=floors)
    assert any("spend_and_live_channels" in v for v in result.violations)
    assert result.verdict == VERDICT_OPEN


def test_internal_research_is_shipped_terminal(floors: EcoFloors):
    """Work with no external effect carries no outcome debt."""
    result = grade(
        [
            ev("artifact_exists", produced_by=ACTOR),
            ev("contract_spec_pass", verifier="schema-check", verifier_substrate="deterministic"),
            ev("craft_gate_pass", verifier="kai-quality-gates", verifier_substrate="deterministic"),
        ],
        work_type=floors.work_type("internal-research"),
        claimed_by=ACTOR,
        floors=floors,
    )
    assert result.verdict == VERDICT_SHIPPED
    assert result.terminal is True
    assert result.unmet == []


def test_attribution_required_caps_outcome_at_o4(floors: EcoFloors):
    """Platform-reported results are not a counterfactual."""
    evidence = [
        ev("artifact_exists", produced_by=ACTOR, observed_at="2026-07-20T09:00:00Z"),
        ev(
            "outcome_baseline",
            metric="cac", source="ads_connector", baseline="88", threshold="70",
            window="14d", owner="Connor", observed_at="2026-07-20T09:10:00Z",
        ),
        ev("craft_gate_pass", verifier="kai-quality-gates", verifier_substrate="deterministic"),
        ev("craft_independent_review", verifier="Connor", verifier_substrate="human"),
        ev("craft_field_standard", verifier="policy-review", verifier_substrate="deterministic"),
        ev("approval_review", sha256="b" * 64, verifier="Connor", verifier_substrate="human"),
        ev("provider_receipt", verifier="meta-adapter", verifier_substrate="deterministic",
           observed_at="2026-07-20T13:00:00Z"),
        ev("independent_verification", expected="entity matches bundle", observed="matched",
           verifier="ads-reconciler", verifier_substrate="deterministic"),
        ev("outcome_observation", observed="CAC 64", verifier="ads-connector",
           verifier_substrate="deterministic"),
        ev("outcome_threshold_met", observed="64", threshold="70", verifier="ads-connector",
           verifier_substrate="deterministic"),
    ]
    result = grade(evidence, work_type=floors.work_type("paid-ad-campaign"), claimed_by=ACTOR, floors=floors)
    assert result.grade["O"] == 4
    assert result.verdict == VERDICT_CLOSED  # O4 floor is met

    # Without an attribution design, O5 stays out of reach.
    assert result.grade["O"] < 5


# ---------------------------------------------------------------------------
# Record store — actor/verifier separation
# ---------------------------------------------------------------------------


def test_actor_cannot_submit_a_verdict(store: EcoRecordStore):
    with pytest.raises(EcoError, match="not a verdict"):
        store.claim(
            subject_id="wi-1",
            step_id="blog.publish",
            work_type="blog-post",
            claimed_by=ACTOR,
            payload={"computed": {"verdict": "CLOSED"}},
        )


def test_actor_cannot_verify_its_own_record(store: EcoRecordStore):
    record = store.claim(
        subject_id="wi-1", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=published_blog_evidence(),
    )
    with pytest.raises(EcoError, match="may not issue its own verdict"):
        store.verify(record["record_id"], verifier=ACTOR)


def test_verify_writes_computed_block_and_persists(store: EcoRecordStore):
    record = store.claim(
        subject_id="wi-1", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=published_blog_evidence(),
    )
    assert "computed" not in record

    verified = store.verify(record["record_id"], verifier=GATE)
    assert verified["computed"]["verdict"] == VERDICT_SHIPPED
    assert verified["computed"]["verdict_by"] == GATE

    reloaded = store.get(record["record_id"])
    assert reloaded["computed"]["verdict"] == VERDICT_SHIPPED


def test_evidence_is_append_only(store: EcoRecordStore):
    record = store.claim(
        subject_id="wi-1", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=[ev("artifact_exists", produced_by=ACTOR)],
    )
    before = list(record["evidence"])
    after = store.add_evidence(
        record["record_id"],
        [ev("craft_gate_pass", verifier="kai-quality-gates", verifier_substrate="deterministic")],
    )
    assert after["evidence"][: len(before)] == before
    assert len(after["evidence"]) == len(before) + 1


def test_outcome_debt_lists_shipped_but_unpaid_items(store: EcoRecordStore):
    record = store.claim(
        subject_id="wi-1", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=published_blog_evidence(),
    )
    store.verify(record["record_id"], verifier=GATE)

    debt = store.outcome_debt(now=datetime(2026, 9, 1, tzinfo=timezone.utc))
    assert len(debt) == 1
    assert debt[0]["subject_id"] == "wi-1"
    assert debt[0]["unmet"] == ["O3"]
    assert debt[0]["overdue"] is True


def test_closed_items_carry_no_outcome_debt(store: EcoRecordStore):
    evidence = published_blog_evidence() + [
        ev("outcome_observation", observed="184 clicks", verifier="gsc-connector",
           verifier_substrate="deterministic", observed_at="2026-08-19T12:00:00Z")
    ]
    record = store.claim(
        subject_id="wi-2", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=evidence,
    )
    store.verify(record["record_id"], verifier=GATE)
    assert store.outcome_debt() == []


# ---------------------------------------------------------------------------
# Failure records
# ---------------------------------------------------------------------------


def _failure_kwargs(**overrides) -> dict:
    payload = {
        "subject_id": "wi-3",
        "step_id": "blog.publish",
        "actor": ACTOR,
        "condition": "blocked",
        "failed_axis": ["E"],
        "required_floor": {"E": 5, "C": 3, "O": 3},
        "observed_grade": {"E": 3, "C": 3, "O": 1},
        "next_action": "Wait for WordPress credentials to be reissued",
        "owner": "Connor",
        "verdict_by": GATE,
    }
    payload.update(overrides)
    return payload


def test_failure_record_requires_a_named_axis(store: EcoRecordStore):
    with pytest.raises(EcoError, match="failed_axis is required"):
        store.record_failure(**_failure_kwargs(failed_axis=[]))


def test_failure_record_requires_next_action_and_owner(store: EcoRecordStore):
    with pytest.raises(EcoError, match="next_action is required"):
        store.record_failure(**_failure_kwargs(next_action=""))
    with pytest.raises(EcoError, match="owner is required"):
        store.record_failure(**_failure_kwargs(owner=""))


def test_failure_record_rejects_unknown_condition(store: EcoRecordStore):
    with pytest.raises(EcoError, match="condition must be one of"):
        store.record_failure(**_failure_kwargs(condition="red"))


def test_failure_record_persists_and_is_queryable(store: EcoRecordStore):
    payload = store.record_failure(**_failure_kwargs(authoritative_error="401 invalid_token"))
    assert payload["attempt_id"].startswith("attempt-")

    failures = store.failures()
    assert len(failures) == 1
    assert failures[0]["failed_axis"] == ["E"]
    assert failures[0]["authoritative_error"] == "401 invalid_token"
    assert failures[0]["verdict_by"] == GATE


def test_a_later_success_does_not_overwrite_the_failure(store: EcoRecordStore):
    store.record_failure(**_failure_kwargs())
    record = store.claim(
        subject_id="wi-3", step_id="blog.publish", work_type="blog-post",
        claimed_by=ACTOR, evidence=published_blog_evidence(),
    )
    store.verify(record["record_id"], verifier=GATE)
    assert len(store.failures()) == 1

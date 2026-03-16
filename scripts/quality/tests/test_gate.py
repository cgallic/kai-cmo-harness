"""Tests for the quality gate module."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.gate import GateDB, load_policy, evaluate_proposal, _default_policy
from scripts.quality.types import QualityReport, CategoryScore, RuleResult, Category, Severity, Violation


def _close_db(db):
    """Close the DB connection so the file can be deleted on Windows."""
    if db._conn is not None:
        db._conn.close()
        db._conn = None


def _make_report(score, rules=None):
    """Helper to build a minimal QualityReport with a given overall_score."""
    categories = []
    if rules:
        categories.append(CategoryScore(
            category=Category.ALGORITHMIC_AUTHORSHIP,
            score=score,
            weight=0.4,
            rules=rules,
        ))
    return QualityReport(
        file_path="<test>",
        overall_score=score,
        categories=categories,
        metadata={"word_count": 500, "sentence_count": 25},
    )


# ── 1. GateDB creation and schema ────────────────────────────────────────

def test_gatedb_creation():
    db_path = Path(tempfile.mktemp(suffix=".db"))
    try:
        db = GateDB(db_path)
        # The DB file should exist after creation
        assert db_path.exists(), "DB file was not created"
        # Schema should include the proposals table
        row = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='proposals'"
        ).fetchone()
        assert row is not None, "proposals table not found"
        print("  test_gatedb_creation passed")
    finally:
        _close_db(db)
        db_path.unlink(missing_ok=True)


# ── 2. Proposal insertion and retrieval ──────────────────────────────────

def test_insert_and_get():
    db_path = Path(tempfile.mktemp(suffix=".db"))
    try:
        db = GateDB(db_path)
        proposal = {
            "id": "gp-test0001",
            "content_hash": "abc123",
            "file_path": "test.md",
            "score": 82.5,
            "grade": "B",
            "status": "pending",
            "policy": "default",
            "violations_json": "[]",
            "top_fixes_json": "[]",
            "metadata_json": "{}",
            "decision_reason": "Score 82 in hold range",
            "created_at": 1700000000.0,
        }
        returned_id = db.insert(proposal)
        assert returned_id == "gp-test0001", f"Expected gp-test0001, got {returned_id}"

        retrieved = db.get("gp-test0001")
        assert retrieved is not None, "Proposal not found after insert"
        assert retrieved["score"] == 82.5
        assert retrieved["grade"] == "B"
        assert retrieved["status"] == "pending"
        assert retrieved["file_path"] == "test.md"

        # get() returns None for missing ID
        assert db.get("gp-nonexistent") is None
        print("  test_insert_and_get passed")
    finally:
        _close_db(db)
        db_path.unlink(missing_ok=True)


# ── 3. Status updates (approve, reject) ─────────────────────────────────

def test_update_status():
    db_path = Path(tempfile.mktemp(suffix=".db"))
    try:
        db = GateDB(db_path)
        proposal = {
            "id": "gp-status01",
            "content_hash": "def456",
            "file_path": "draft.md",
            "score": 70.0,
            "grade": "C",
            "status": "pending",
            "policy": "default",
            "violations_json": "[]",
            "top_fixes_json": "[]",
            "metadata_json": "{}",
            "decision_reason": "Score in hold range",
            "created_at": 1700000000.0,
        }
        db.insert(proposal)

        # Approve
        db.update_status("gp-status01", "approved", reviewed_by="tester", reason="Looks good")
        row = db.get("gp-status01")
        assert row["status"] == "approved", f"Expected approved, got {row['status']}"
        assert row["reviewed_by"] == "tester"
        assert row["reviewed_at"] is not None
        assert row["decision_reason"] == "Looks good"

        # Insert another and reject it
        proposal2 = dict(proposal, id="gp-status02", created_at=1700000001.0)
        db.insert(proposal2)
        db.update_status("gp-status02", "rejected", reviewed_by="reviewer", reason="Too many issues")
        row2 = db.get("gp-status02")
        assert row2["status"] == "rejected"
        assert row2["decision_reason"] == "Too many issues"

        # list_by_status should separate them
        approved = db.list_by_status("approved")
        rejected = db.list_by_status("rejected")
        assert len(approved) == 1
        assert len(rejected) == 1
        assert approved[0]["id"] == "gp-status01"
        assert rejected[0]["id"] == "gp-status02"
        print("  test_update_status passed")
    finally:
        _close_db(db)
        db_path.unlink(missing_ok=True)


# ── 4. Policy loading (default policy when file doesn't exist) ───────────

def test_load_policy_default():
    policy = load_policy("nonexistent-policy-name-xyz")
    default = _default_policy()
    assert policy == default, f"Expected default policy, got {policy}"
    assert policy["id"] == "default"
    assert "auto_approve_above" in policy
    assert "reject_below" in policy
    assert "require_rules_pass" in policy
    print("  test_load_policy_default passed")


def test_default_policy_values():
    policy = _default_policy()
    assert policy["auto_approve_above"] == 85
    assert policy["reject_below"] == 60
    assert policy["hold_between"] == [60, 85]
    assert policy["require_rules_pass"] == []
    assert policy["block_if_terms"] == []
    print("  test_default_policy_values passed")


# ── 5. evaluate_proposal with score-based decisions ──────────────────────

def test_evaluate_auto_approve():
    policy = _default_policy()
    report = _make_report(90.0)
    result = evaluate_proposal(report, policy)
    assert result["status"] == "approved", f"Expected approved, got {result['status']}"
    assert "auto-approve" in result["reason"]
    print("  test_evaluate_auto_approve passed")


def test_evaluate_hold_range():
    policy = _default_policy()
    report = _make_report(72.0)
    result = evaluate_proposal(report, policy)
    assert result["status"] == "pending", f"Expected pending, got {result['status']}"
    assert "hold range" in result["reason"]
    print("  test_evaluate_hold_range passed")


def test_evaluate_auto_reject():
    policy = _default_policy()
    report = _make_report(45.0)
    result = evaluate_proposal(report, policy)
    assert result["status"] == "rejected", f"Expected rejected, got {result['status']}"
    assert "auto-reject" in result["reason"]
    print("  test_evaluate_auto_reject passed")


def test_evaluate_boundary_approve():
    """Score exactly at auto_approve_above threshold should be approved."""
    policy = _default_policy()
    report = _make_report(85.0)
    result = evaluate_proposal(report, policy)
    assert result["status"] == "approved", f"Expected approved at boundary, got {result['status']}"
    print("  test_evaluate_boundary_approve passed")


def test_evaluate_boundary_reject():
    """Score exactly at reject_below threshold should be in hold range, not rejected."""
    policy = _default_policy()
    report = _make_report(60.0)
    result = evaluate_proposal(report, policy)
    # 60 is >= reject_below (60) and < auto_approve (85), so it's hold/pending
    assert result["status"] == "pending", f"Expected pending at boundary, got {result['status']}"
    print("  test_evaluate_boundary_reject passed")


# ── 6. evaluate_proposal with required rules that fail ───────────────────

def test_evaluate_required_rules_fail():
    """When a required rule fails, proposal should be rejected regardless of score."""
    policy = _default_policy()
    policy["require_rules_pass"] = ["aa-conditions-after"]

    # Create a rule that fails (has violations)
    failing_rule = RuleResult(
        rule_id="aa-conditions-after",
        rule_name="Conditions After Main Clause",
        category=Category.ALGORITHMIC_AUTHORSHIP,
        severity=Severity.WARNING,
        score=0.5,
        violations=[
            Violation(
                line=3, text="If you want results, do X", fix="Do X if you want results"
            )
        ],
    )

    report = _make_report(92.0, rules=[failing_rule])
    result = evaluate_proposal(report, policy)
    assert result["status"] == "rejected", f"Expected rejected due to required rule, got {result['status']}"
    assert "aa-conditions-after" in result["reason"]
    print("  test_evaluate_required_rules_fail passed")


def test_evaluate_required_rules_pass():
    """When required rules all pass, score-based decision applies."""
    policy = _default_policy()
    policy["require_rules_pass"] = ["aa-conditions-after"]

    passing_rule = RuleResult(
        rule_id="aa-conditions-after",
        rule_name="Conditions After Main Clause",
        category=Category.ALGORITHMIC_AUTHORSHIP,
        severity=Severity.WARNING,
        score=1.0,
        violations=[],  # no violations = passed
    )

    report = _make_report(92.0, rules=[passing_rule])
    result = evaluate_proposal(report, policy)
    assert result["status"] == "approved", f"Expected approved, got {result['status']}"
    print("  test_evaluate_required_rules_pass passed")


# ── Runner ────────────────────────────────────────────────────────────────

def run_all():
    print("Gate tests:")
    test_gatedb_creation()
    test_insert_and_get()
    test_update_status()
    test_load_policy_default()
    test_default_policy_values()
    test_evaluate_auto_approve()
    test_evaluate_hold_range()
    test_evaluate_auto_reject()
    test_evaluate_boundary_approve()
    test_evaluate_boundary_reject()
    test_evaluate_required_rules_fail()
    test_evaluate_required_rules_pass()
    print("All gate tests passed!")


if __name__ == "__main__":
    run_all()

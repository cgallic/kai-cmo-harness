"""Focused tests for the proof-bound Company Autopilot aggregation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from kai.runtime.company_autopilot import CompanyAutopilotService, has_strict_proof
from kai.runtime.models import KaiGoal


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)


class FakeActionStore:
    def __init__(self, actions=None):
        self.actions = list(actions or [])

    def list_actions(self, *, brand_id=None, limit=50, **_filters):
        rows = [row for row in self.actions if brand_id is None or row["brand_id"] == brand_id]
        return rows[:limit]


class FakeRuntimeStore:
    def __init__(self, runs=None):
        self.runs = list(runs or [])

    def list_runs(self, *, brand_id=None, limit=50, **_filters):
        rows = [row for row in self.runs if brand_id is None or row["brand_id"] == brand_id]
        return rows[:limit]


class FakeConnectorHealth:
    def __init__(self, reports=None):
        self.reports = reports or {}

    def brand_health(self, brand_id):
        return self.reports.get(brand_id, {"brand_id": brand_id, "integrations": []})


class FakeGoalRegistry:
    def __init__(self, goals=None):
        self.goals = list(goals or [])

    def list_goals(self, brand_id=None):
        return [goal for goal in self.goals if brand_id is None or goal.brand_id == brand_id]


def _brand(brand_id="acme", **metadata):
    return SimpleNamespace(id=brand_id, name=brand_id.title(), metadata=metadata)


def _run(brand_id="acme", age_days=0):
    return {
        "run_id": f"run-{brand_id}",
        "brand_id": brand_id,
        "status": "completed",
        "updated_at": (NOW - timedelta(days=age_days)).isoformat(),
    }


def _action(
    action_id,
    *,
    brand_id="acme",
    approval="approved",
    execution="completed",
    verification=None,
    result=None,
    updated_offset=0,
):
    return {
        "action_id": action_id,
        "brand_id": brand_id,
        "approval_state": approval,
        "execution_state": execution,
        "verification_result": verification,
        "result_summary": result,
        "metadata": {},
        "evidence": [{"source": f"evidence:{action_id}"}],
        "updated_at": (NOW + timedelta(minutes=updated_offset)).isoformat(),
    }


def _service(*, brands=None, actions=None, runs=None, health=None, goals=None):
    workspace = SimpleNamespace(brands=brands or [_brand()])
    return CompanyAutopilotService(
        workspace_loader=lambda: workspace,
        runtime_store=FakeRuntimeStore(runs if runs is not None else [_run()]),
        action_store=FakeActionStore(actions),
        connector_health=FakeConnectorHealth(health),
        goal_registry=FakeGoalRegistry(goals),
        now=lambda: NOW,
    )


def _strict_verification():
    return {
        "status": "accepted",
        "provider_receipt": {"id": "receipt-1"},
        "independent_readback": {"matched": True},
        "reconciliation_evidence": {"status": "matched"},
    }


def test_strict_proof_requires_all_four_acceptance_elements():
    action = _action("a1", verification={"status": "accepted"})
    assert has_strict_proof(action) is False

    action["verification_result"].update({
        "provider_receipt_id": "receipt-1",
        "independent_read_back": {"matched": True},
        "reconciled": True,
    })
    assert has_strict_proof(action) is True


def test_strict_proof_rejects_failed_readback_or_reconciliation_verdicts():
    action = _action(
        "a1",
        verification={
            "status": "accepted",
            "provider_receipt": {"id": "receipt-1"},
            "independent_readback": {"matched": False},
            "reconciliation_evidence": {"status": "mismatch"},
        },
    )
    assert has_strict_proof(action) is False


def test_failed_action_wins_over_unverified_execution_and_approval():
    actions = [
        _action("pending", approval="pending", execution="pending"),
        _action("unverified", updated_offset=1),
        _action("failed", execution="failed", updated_offset=2),
    ]
    result = _service(actions=actions).command_center()

    assert result["primary_bottleneck"]["type"] == "failed_action"
    assert result["primary_bottleneck"]["subject"] == "failed"
    assert result["coach"]["status"] == "action_required"


def test_completed_connector_response_is_blocked_without_strict_proof():
    action = _action(
        "executed",
        verification={"status": "accepted"},
        result={"response": {"id": "provider-object"}},
    )
    row = _service(actions=[action]).portfolio()["rows"][0]

    assert row["lifecycle"] == "verified"
    assert row["blocked_gate"] == "strict_proof_missing"
    assert row["primary_bottleneck"]["type"] == "unverified_execution"
    assert "provider receipt" in row["next_action"].lower()


def test_connector_health_precedes_pending_approval():
    action = _action("pending", approval="pending", execution="pending")
    health = {
        "acme": {
            "integrations": [{
                "integration_id": "int-1",
                "provider": "meta",
                "status": "connected",
                "stale_sync": True,
            }]
        }
    }
    result = _service(actions=[action], health=health).command_center()

    assert result["primary_bottleneck"]["type"] == "connector_unhealthy"
    assert result["primary_bottleneck"]["evidence_refs"] == ["integration:int-1"]


def test_behind_pace_goal_uses_measured_goal_state_after_verified_action():
    goal = KaiGoal(
        goal_id="goal-1",
        brand_id="acme",
        name="Organic leads",
        kpi_name="leads",
        target_value=100,
        current_value=5,
        target_direction="increase",
        status="active",
        deadline=(NOW + timedelta(days=1)).isoformat(),
        created_at=(NOW - timedelta(days=9)).isoformat(),
        metadata={"baseline_value": 0},
    )
    action = _action("verified", verification=_strict_verification())
    result = _service(actions=[action], goals=[goal]).command_center()

    assert result["primary_bottleneck"]["type"] == "behind_pace_goal"
    assert result["primary_bottleneck"]["evidence_refs"] == ["goal:goal-1"]


def test_portfolio_returns_one_row_per_brand_and_one_global_primary():
    brands = [_brand("beta"), _brand("acme")]
    actions = [
        _action("acme-pending", approval="pending", execution="pending"),
        _action("beta-failed", brand_id="beta", execution="failed"),
    ]
    runs = [_run("acme"), _run("beta")]
    service = _service(brands=brands, actions=actions, runs=runs)

    portfolio = service.portfolio()
    command_center = service.command_center()

    assert [row["brand_id"] for row in portfolio["rows"]] == ["acme", "beta"]
    assert all("priority_rank" not in row for row in portfolio["rows"])
    assert command_center["primary_bottleneck"]["brand_id"] == "beta"
    assert command_center["primary_bottleneck"]["type"] == "failed_action"


def test_no_current_run_is_a_bottleneck_but_current_verified_state_is_clear():
    verified = _action("verified", verification=_strict_verification())
    no_run = _service(actions=[verified], runs=[]).command_center()
    assert no_run["primary_bottleneck"]["type"] == "stale_runtime"

    clear = _service(actions=[verified], runs=[_run()]).command_center()
    assert clear["primary_bottleneck"] is None
    assert clear["coach"]["status"] == "monitor"


def test_mounted_router_handlers_delegate_without_changing_existing_router(monkeypatch):
    from gateway.routers import actions as router

    fake = SimpleNamespace(
        command_center=lambda brand_id=None: {"surface": "command-center", "brand_id": brand_id},
        portfolio=lambda brand_id=None: {"surface": "portfolio", "brand_id": brand_id},
    )
    monkeypatch.setattr(router, "_get_company_autopilot_service", lambda: fake)

    command = asyncio.run(router.company_autopilot_command_center("acme"))
    portfolio = asyncio.run(router.company_autopilot_portfolio("acme"))

    assert command == {"surface": "command-center", "brand_id": "acme"}
    assert portfolio == {"surface": "portfolio", "brand_id": "acme"}

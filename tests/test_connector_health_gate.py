from __future__ import annotations

from datetime import datetime, timedelta, timezone

from kai.runtime.connector_health import evaluate_connector_health_gate


def _connected_integration(**overrides):
    record = {
        "integration_id": "int_123",
        "provider": "wordpress",
        "status": "connected",
        "kill_switch": False,
        "scopes": ["read", "write"],
        "capabilities": ["read", "write"],
        "last_verified_at": datetime.now(timezone.utc).isoformat(),
        "last_sync_at": datetime.now(timezone.utc).isoformat(),
    }
    record.update(overrides)
    return record


def test_health_gate_blocks_missing_connector():
    decision = evaluate_connector_health_gate([], required_scopes=["write"], risk_tier="high")
    assert decision["allowed"] is False
    assert decision["state"] == "missing"
    assert decision["blocked"] is True


def test_health_gate_warns_on_degraded_low_risk():
    decision = evaluate_connector_health_gate(
        [_connected_integration(status="degraded", last_error="token refresh failed")],
        required_scopes=["write"],
        risk_tier="low",
    )
    assert decision["allowed"] is True
    assert decision["state"] == "degraded"
    assert decision["warning"] is not None


def test_health_gate_blocks_degraded_medium_risk():
    decision = evaluate_connector_health_gate(
        [_connected_integration(status="degraded", last_error="token refresh failed")],
        required_scopes=["write"],
        risk_tier="medium",
    )
    assert decision["allowed"] is False
    assert decision["state"] == "degraded"


def test_health_gate_returns_healthy_state():
    decision = evaluate_connector_health_gate(
        [_connected_integration()],
        required_scopes=["write"],
        risk_tier="high",
    )
    assert decision["allowed"] is True
    assert decision["state"] == "healthy"


def test_health_gate_marks_stale_when_health_is_old():
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
    decision = evaluate_connector_health_gate(
        [_connected_integration(last_verified_at=stale_time, last_sync_at=stale_time)],
        required_scopes=["write"],
        risk_tier="high",
    )
    assert decision["allowed"] is False
    assert decision["state"] == "stale"


def test_health_gate_warns_on_stale_medium_risk():
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
    decision = evaluate_connector_health_gate(
        [_connected_integration(last_verified_at=stale_time, last_sync_at=stale_time)],
        required_scopes=["write"],
        risk_tier="medium",
    )
    assert decision["allowed"] is True
    assert decision["state"] == "stale"
    assert decision["warning"] is not None


def test_health_gate_blocks_unverified_high_risk():
    decision = evaluate_connector_health_gate(
        [_connected_integration(last_verified_at=None, last_sync_at=None)],
        required_scopes=["write"],
        risk_tier="high",
    )
    assert decision["allowed"] is False
    assert decision["state"] == "unverified"

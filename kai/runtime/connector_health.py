"""Connector health, observability, and debugging.

Provides operator-readable diagnostics for all connected integrations:
health checks, error classification, execution logs, and brand-level
health summaries.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .integrations import IntegrationRegistry, _ensure_dir, _utc_now, _write_json_atomic

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

ERROR_CATEGORIES = {
    "auth_failure": "Authentication expired or revoked — reconnect required",
    "scope_failure": "Missing permissions — re-authorise with broader scopes",
    "provider_validation": "External API rejected the request payload",
    "rate_limit": "Rate limit exceeded — retry after cooldown",
    "transient": "Temporary upstream error — safe to retry",
    "timeout": "Request timed out (30s Pipedream proxy limit)",
    "not_found": "Resource not found in the external system",
    "unsupported_action": "This action type is not mapped for this provider",
    "unknown": "Unclassified error — check raw details",
}

CONNECTOR_HEALTH_STATES = (
    "missing",
    "unverified",
    "healthy",
    "degraded",
    "stale",
    "error",
)


def classify_integration_error(error_kind: Optional[str]) -> Dict[str, str]:
    """Return a human-readable classification for an error kind."""
    if not error_kind:
        return {"category": "none", "description": "No error"}
    return {
        "category": error_kind,
        "description": ERROR_CATEGORIES.get(error_kind, f"Unknown category: {error_kind}"),
        "action_required": _action_for_error(error_kind),
    }


def _action_for_error(kind: str) -> str:
    actions = {
        "auth_failure": "reconnect",
        "scope_failure": "reconnect_with_scopes",
        "provider_validation": "fix_payload",
        "rate_limit": "wait_and_retry",
        "transient": "retry",
        "timeout": "retry_or_simplify",
        "not_found": "check_resource_exists",
        "unsupported_action": "check_action_mapping",
        "unknown": "investigate",
    }
    return actions.get(kind, "investigate")


# ---------------------------------------------------------------------------
# Health gate
# ---------------------------------------------------------------------------


def evaluate_connector_health_gate(
    integrations: Sequence[Dict[str, Any]],
    *,
    required_scopes: Optional[Sequence[str]] = None,
    risk_tier: str = "high",
    stale_after_hours: int = 24,
) -> Dict[str, Any]:
    """Evaluate whether execution should proceed for a channel integration set.

    Returns a decision dict containing:
    - state: one of CONNECTOR_HEALTH_STATES
    - allowed: bool
    - blocked: bool
    - reason: human-readable explanation
    - warning: optional warning string when execution is allowed with caution
    """
    normalized_scopes = _normalize_required_scopes(required_scopes)
    tier = _normalize_risk_tier(risk_tier)

    if not integrations:
        return {
            "state": "missing",
            "allowed": False,
            "blocked": True,
            "reason": "No integration configured for this channel",
            "warning": None,
            "required_scopes": normalized_scopes,
            "missing_scopes": normalized_scopes,
            "integration_id": None,
            "provider": None,
            "risk_tier": tier,
        }

    assessments = [
        _assess_integration_state(
            integration=record,
            required_scopes=normalized_scopes,
            stale_after_hours=stale_after_hours,
        )
        for record in integrations
    ]
    assessments.sort(key=lambda item: _state_rank(item["state"]))
    best = assessments[0]
    state = best["state"]

    if state in {"healthy"}:
        return {
            **best,
            "allowed": True,
            "blocked": False,
            "warning": None,
            "risk_tier": tier,
        }

    if state in {"missing", "error"}:
        return {
            **best,
            "allowed": False,
            "blocked": True,
            "warning": None,
            "risk_tier": tier,
        }

    should_block = False
    if state == "degraded":
        should_block = tier in {"medium", "high"}
    elif state == "stale":
        should_block = tier in {"high"}
    elif state == "unverified":
        should_block = tier in {"high"}

    warning = None
    if not should_block:
        warning = (
            f"Connector health state '{state}' is allowed with caution for risk tier '{tier}'. "
            f"Reason: {best['reason']}"
        )

    return {
        **best,
        "allowed": not should_block,
        "blocked": should_block,
        "warning": warning,
        "risk_tier": tier,
    }


# ---------------------------------------------------------------------------
# Execution log
# ---------------------------------------------------------------------------


class ExecutionLog:
    """Persistent log of all connector executions for a brand.

    Stored as append-only JSONL files per brand for fast tailing.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            from scripts.harness_config import get_config
            import os
            cfg = get_config()
            base_dir = Path(os.environ.get(
                "KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")
            ))
        self._log_dir = _ensure_dir(base_dir / "execution_logs")

    def append(
        self,
        brand_id: str,
        entry: Dict[str, Any],
    ) -> None:
        """Append an execution log entry for a brand."""
        entry["logged_at"] = _utc_now()
        log_path = self._log_dir / f"{brand_id}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def tail(self, brand_id: str, n: int = 50) -> List[Dict[str, Any]]:
        """Return the last n log entries for a brand."""
        log_path = self._log_dir / f"{brand_id}.jsonl"
        if not log_path.exists():
            return []
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        recent = lines[-n:]
        entries = []
        for line in recent:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def search(
        self,
        brand_id: str,
        *,
        channel: Optional[str] = None,
        action_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search execution logs with filters."""
        all_entries = self.tail(brand_id, n=500)
        results = []
        for entry in reversed(all_entries):
            if channel and entry.get("channel") != channel:
                continue
            if action_type and entry.get("action_type") != action_type:
                continue
            if success is not None and entry.get("success") != success:
                continue
            results.append(entry)
            if len(results) >= limit:
                break
        return results


# ---------------------------------------------------------------------------
# Integration error history
# ---------------------------------------------------------------------------


class IntegrationErrorHistory:
    """Per-integration error history, stored alongside integration records."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            from scripts.harness_config import get_config
            import os
            cfg = get_config()
            base_dir = Path(os.environ.get(
                "KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")
            ))
        self._error_dir = _ensure_dir(base_dir / "integration_errors")

    def record_error(
        self,
        integration_id: str,
        error_kind: str,
        detail: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an error for an integration."""
        entry = {
            "timestamp": _utc_now(),
            "error_kind": error_kind,
            "detail": detail,
            "classification": classify_integration_error(error_kind),
            "context": context or {},
        }
        log_path = self._error_dir / f"{integration_id}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_history(
        self,
        integration_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return recent errors for an integration."""
        log_path = self._error_dir / f"{integration_id}.jsonl"
        if not log_path.exists():
            return []
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in lines[-limit:]:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


# ---------------------------------------------------------------------------
# Brand-level health dashboard
# ---------------------------------------------------------------------------


class ConnectorHealthDashboard:
    """Aggregates health information across all integrations for a brand.

    Produces an operator-readable summary that does not require reading
    stack traces.
    """

    def __init__(
        self,
        registry: Optional[IntegrationRegistry] = None,
        error_history: Optional[IntegrationErrorHistory] = None,
        execution_log: Optional[ExecutionLog] = None,
    ):
        if registry is None:
            from .integrations import get_default_integration_registry
            registry = get_default_integration_registry()
        self._registry = registry
        self._errors = error_history or IntegrationErrorHistory()
        self._exec_log = execution_log or ExecutionLog()

    def brand_health(self, brand_id: str) -> Dict[str, Any]:
        """Full health report for a brand's integrations."""
        integrations = self._registry.list_for_brand(brand_id)
        health_summary = self._registry.get_health_summary(brand_id)
        scope_summary = self._registry.get_scope_summary(brand_id)

        integration_details = []
        for integ in integrations:
            iid = integ.get("integration_id", "")
            errors = self._errors.get_history(iid, limit=5)
            stale = _is_stale(integ.get("last_sync_at"))
            detail = {
                "integration_id": iid,
                "channel": integ.get("channel"),
                "provider": integ.get("provider"),
                "status": integ.get("status"),
                "kill_switch": integ.get("kill_switch", False),
                "last_verified_at": integ.get("last_verified_at"),
                "last_sync_at": integ.get("last_sync_at"),
                "last_error": integ.get("last_error"),
                "stale_sync": stale,
                "recent_errors": errors,
            }
            if integ.get("last_error"):
                detail["error_classification"] = classify_integration_error(
                    _infer_error_kind(errors)
                )
            integration_details.append(detail)

        recent_executions = self._exec_log.tail(brand_id, n=10)

        # Counts
        statuses = {}
        for integ in integrations:
            s = integ.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1

        return {
            "brand_id": brand_id,
            "timestamp": _utc_now(),
            "status_counts": statuses,
            "health_by_channel": health_summary,
            "scope_summary": scope_summary,
            "integrations": integration_details,
            "recent_executions": recent_executions,
        }

    def channel_health(self, brand_id: str, channel: str) -> Dict[str, Any]:
        """Health for a single channel."""
        integrations = self._registry.list_for_brand(brand_id, channel=channel)
        details = []
        for integ in integrations:
            iid = integ.get("integration_id", "")
            details.append({
                "integration_id": iid,
                "provider": integ.get("provider"),
                "status": integ.get("status"),
                "kill_switch": integ.get("kill_switch", False),
                "last_verified_at": integ.get("last_verified_at"),
                "last_sync_at": integ.get("last_sync_at"),
                "last_error": integ.get("last_error"),
                "stale_sync": _is_stale(integ.get("last_sync_at")),
                "recent_errors": self._errors.get_history(iid, limit=3),
            })
        return {
            "brand_id": brand_id,
            "channel": channel,
            "integrations": details,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_stale(last_sync_at: Optional[str], max_age_hours: int = 24) -> bool:
    if not last_sync_at:
        return True
    try:
        last = datetime.fromisoformat(last_sync_at)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - last
        return age.total_seconds() > max_age_hours * 3600
    except (ValueError, TypeError):
        return True


def _infer_error_kind(errors: List[Dict[str, Any]]) -> Optional[str]:
    """Return the error_kind from the most recent error entry."""
    if errors:
        return errors[-1].get("error_kind")
    return None


def _state_rank(state: str) -> int:
    ranking = {
        "healthy": 0,
        "unverified": 1,
        "stale": 2,
        "degraded": 3,
        "error": 4,
        "missing": 5,
    }
    return ranking.get(state, 6)


def _normalize_risk_tier(risk_tier: str) -> str:
    tier = (risk_tier or "").strip().lower()
    if tier not in {"low", "medium", "high"}:
        return "high"
    return tier


def _normalize_required_scopes(required_scopes: Optional[Sequence[str]]) -> List[str]:
    if not required_scopes:
        return []
    deduped: List[str] = []
    seen = set()
    for scope in required_scopes:
        normalized = str(scope).strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        deduped.append(lowered)
        seen.add(lowered)
    return deduped


def _assess_integration_state(
    *,
    integration: Dict[str, Any],
    required_scopes: Sequence[str],
    stale_after_hours: int,
) -> Dict[str, Any]:
    status = str(integration.get("status") or "").lower()
    integration_id = integration.get("integration_id")
    provider = integration.get("provider")
    scopes = {
        str(scope).strip().lower()
        for scope in (integration.get("scopes") or [])
        if str(scope).strip()
    }
    capabilities = {
        str(cap).strip().lower()
        for cap in (integration.get("capabilities") or [])
        if str(cap).strip()
    }

    missing_scopes = sorted(
        scope for scope in required_scopes if scope not in scopes and scope not in capabilities
    )

    if status == "error":
        return {
            "state": "error",
            "reason": integration.get("last_error") or "Integration is in error state",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if status in {"disconnected"}:
        return {
            "state": "missing",
            "reason": "Integration is disconnected",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if status in {"pending_auth"}:
        return {
            "state": "unverified",
            "reason": "Integration is pending authentication",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if integration.get("kill_switch", False):
        return {
            "state": "error",
            "reason": "Integration kill switch is active",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if status == "degraded":
        reason = integration.get("last_error") or "Integration reported degraded health"
        return {
            "state": "degraded",
            "reason": reason,
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if status != "connected":
        return {
            "state": "missing",
            "reason": f"Unsupported integration status '{status or 'unknown'}'",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if missing_scopes:
        return {
            "state": "unverified",
            "reason": f"Missing required scopes/capabilities: {', '.join(missing_scopes)}",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    last_health_at = integration.get("last_verified_at") or integration.get("last_sync_at")
    if not last_health_at:
        return {
            "state": "unverified",
            "reason": "Integration is connected but has not been verified or synced yet",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    if _is_stale(last_health_at, max_age_hours=stale_after_hours):
        return {
            "state": "stale",
            "reason": f"Integration health signal is older than {stale_after_hours}h",
            "required_scopes": list(required_scopes),
            "missing_scopes": missing_scopes,
            "integration_id": integration_id,
            "provider": provider,
        }

    return {
        "state": "healthy",
        "reason": "Integration is connected, scoped, and recently verified",
        "required_scopes": list(required_scopes),
        "missing_scopes": missing_scopes,
        "integration_id": integration_id,
        "provider": provider,
    }

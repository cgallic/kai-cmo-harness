"""Remote operator surface for the Kai Marketing OS.

This module defines the structured JSON response models and the business
logic layer that the FastAPI gateway router calls.  Every response model
uses the Pydantic-with-stdlib-fallback pattern established in
``kai/models/audit.py`` and ``gateway/models.py``.

The :class:`RemoteOperatorSurface` mirrors the capabilities of
:class:`~kai.operator.local_surface.LocalOperatorSurface` but returns
typed response objects instead of formatted strings.  Front-end
dashboards, mobile apps, and third-party integrations consume these
models as JSON.
"""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Response Models
# ============================================================================


class AuditResponse(BaseModel):
    """Structured audit result returned by the API."""

    business_id: str
    audit_type: str = "full"
    run_at: str = ""
    overall_score: float = 0.0
    category_scores: Dict[str, float] = Field(default_factory=dict)
    finding_counts: Dict[str, int] = Field(default_factory=dict)
    top_findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class ProposalListResponse(BaseModel):
    """Paginated list of proposals."""

    business_id: str
    total_count: int = 0
    pending_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    proposals: List[Dict[str, Any]] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class ProposalDetailResponse(BaseModel):
    """Full detail for a single proposal."""

    proposal: Dict[str, Any] = Field(default_factory=dict)
    finding: Optional[Dict[str, Any]] = None
    compliance_result: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None
    routing_decision: Optional[Dict[str, Any]] = None
    revision_history: Optional[Dict[str, Any]] = None
    similar_past_actions: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    """Request body for approving an action."""

    action_id: str
    approved_by: str
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    """Request body for rejecting an action."""

    action_id: str
    rejected_by: str
    reason: str
    category: Optional[str] = None
    specific_issues: List[str] = Field(default_factory=list)
    revision_guidance: Optional[str] = None
    do_not_retry: bool = False


class ApprovalResponse(BaseModel):
    """Response after an approve or reject operation."""

    action_id: str
    status: str = ""
    route: str = ""
    next_action: str = ""
    timestamp: str = ""


class StatusResponse(BaseModel):
    """System-wide status snapshot."""

    business_id: str
    system_status: str = "active"
    pending_actions: Dict[str, int] = Field(default_factory=dict)
    active_campaigns: List[Dict[str, Any]] = Field(default_factory=list)
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)
    active_watchers: int = 0
    watcher_findings_today: int = 0
    critical_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    kill_switches_active: List[Dict[str, Any]] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    """High-level dashboard summary."""

    business_id: str
    business_name: str = ""
    generated_at: str = ""
    overall_health_score: float = 0.0
    overall_health: str = "needs_attention"
    scorecards: List[Dict[str, Any]] = Field(default_factory=list)
    top_wins: List[str] = Field(default_factory=list)
    top_concerns: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    pending_approvals: int = 0
    channel_overview: List[Dict[str, Any]] = Field(default_factory=list)
    trend_data: Optional[Dict[str, Any]] = None


class WatcherResponse(BaseModel):
    """Watcher state and recent findings."""

    business_id: str
    total_watchers: int = 0
    enabled_watchers: int = 0
    recent_findings: List[Dict[str, Any]] = Field(default_factory=list)
    findings_by_severity: Dict[str, int] = Field(default_factory=dict)
    last_run_times: Dict[str, str] = Field(default_factory=dict)


class ProfileResponse(BaseModel):
    """Business profile snapshot."""

    business_id: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    archetype: str = ""
    active_channels: List[str] = Field(default_factory=list)
    last_updated: str = ""


class ProfileUpdateRequest(BaseModel):
    """Request body for updating profile fields."""

    fields: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Internal data-access helpers (mirror local_surface.py)
# ============================================================================


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _list_json_dir(dirpath: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not os.path.isdir(dirpath):
        return results
    for name in sorted(os.listdir(dirpath)):
        if name.endswith(".json"):
            data = _load_json_file(os.path.join(dirpath, name))
            if data is not None:
                results.append(data)
    return results


def _save_json_file(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


def _load_audit(business_id: str, workspace_dir: str, scope: str = "full") -> Optional[Dict[str, Any]]:
    audit_dir = os.path.join(workspace_dir, "audits", business_id)
    if not os.path.isdir(audit_dir):
        return None
    files = sorted(
        [f for f in os.listdir(audit_dir) if f.endswith(".json")],
        reverse=True,
    )
    for fname in files:
        data = _load_json_file(os.path.join(audit_dir, fname))
        if data is not None:
            if scope != "full" and data.get("audit_type", "") != scope:
                continue
            return data
    return None


def _load_proposals(business_id: str, workspace_dir: str) -> List[Dict[str, Any]]:
    return _list_json_dir(os.path.join(workspace_dir, "proposals", business_id))


def _load_action(action_id: str, workspace_dir: str) -> Optional[Dict[str, Any]]:
    proposals_root = os.path.join(workspace_dir, "proposals")
    if not os.path.isdir(proposals_root):
        return None
    for biz_dir in os.listdir(proposals_root):
        biz_path = os.path.join(proposals_root, biz_dir)
        if not os.path.isdir(biz_path):
            continue
        for fname in os.listdir(biz_path):
            if not fname.endswith(".json"):
                continue
            data = _load_json_file(os.path.join(biz_path, fname))
            if data is not None and data.get("id") == action_id:
                return data
    return None


def _save_action(action: Dict[str, Any], workspace_dir: str) -> None:
    biz_id = action.get("business_id", "unknown")
    proposals_dir = os.path.join(workspace_dir, "proposals", biz_id)
    fname = f"{action.get('id', 'unknown')}.json"
    _save_json_file(os.path.join(proposals_dir, fname), action)


def _load_history(
    business_id: str,
    workspace_dir: str,
    days: int = 30,
    channel: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    entries = _list_json_dir(os.path.join(workspace_dir, "history", business_id))
    if channel:
        entries = [e for e in entries if e.get("channel") == channel]
    entries.sort(key=lambda e: e.get("timestamp", e.get("created_at", "")), reverse=True)
    return entries[:limit]


def _load_watchers(business_id: str, workspace_dir: str) -> Dict[str, Any]:
    path = os.path.join(workspace_dir, "watchers", business_id, "state.json")
    return _load_json_file(path) or {"watchers": [], "findings": []}


def _load_profile(business_id: str, workspace_dir: str) -> Optional[Dict[str, Any]]:
    for path in [
        os.path.join(workspace_dir, "profiles", f"{business_id}.json"),
        os.path.join(workspace_dir, "profiles", business_id, "profile.json"),
    ]:
        data = _load_json_file(path)
        if data is not None:
            return data
    return None


def _save_profile(profile: Dict[str, Any], workspace_dir: str) -> None:
    biz_id = profile.get("business_id", "unknown")
    _save_json_file(
        os.path.join(workspace_dir, "profiles", f"{biz_id}.json"),
        profile,
    )


def _health_label(score: float) -> str:
    """Map a 0-100 score to a health label."""
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 50:
        return "needs_attention"
    if score >= 30:
        return "poor"
    return "critical"


# Fields that cannot be updated via ProfileUpdateRequest.
_PROFILE_PROTECTED_FIELDS = frozenset({"business_id", "id", "archetype", "created_at"})


# ============================================================================
# RemoteOperatorSurface
# ============================================================================


class RemoteOperatorSurface:
    """HTTP-oriented operator surface returning structured response models.

    Parameters
    ----------
    workspace_dir : str
        Path to the Kai workspace directory on disk.
    """

    def __init__(self, workspace_dir: str) -> None:
        self._workspace_dir = workspace_dir

    # ---------------------------------------------------------------- audit

    def get_audit(self, business_id: str, scope: str = "full") -> AuditResponse:
        """Run or retrieve the latest audit for *business_id*."""
        raw = _load_audit(business_id, self._workspace_dir, scope=scope)
        if raw is None:
            return AuditResponse(
                business_id=business_id,
                audit_type=scope,
                run_at=datetime.now(timezone.utc).isoformat(),
            )

        # Extract category scores as {name: score_float}
        cat_scores_raw = raw.get("category_scores", {})
        cat_scores: Dict[str, float] = {}
        for cat_id, sc in cat_scores_raw.items():
            if isinstance(sc, dict):
                cat_scores[cat_id] = sc.get("score", 0.0)
            elif hasattr(sc, "score"):
                cat_scores[cat_id] = sc.score
            else:
                cat_scores[cat_id] = float(sc)

        # Finding counts
        finding_counts: Dict[str, int] = {}
        for sev in ("critical", "high", "medium", "low", "info"):
            count = raw.get(f"{sev}_count", 0)
            if count:
                finding_counts[sev] = count

        # Top findings
        findings = raw.get("findings", [])
        top_findings: List[Dict[str, Any]] = []
        for f in findings[:10]:
            if isinstance(f, dict):
                top_findings.append(f)
            elif hasattr(f, "model_dump"):
                top_findings.append(f.model_dump())
            else:
                top_findings.append({"title": str(f)})

        # Recommendations from top priority findings
        recommendations: List[str] = []
        for f in findings[:5]:
            rec = f.get("recommendation", "") if isinstance(f, dict) else getattr(f, "recommendation", "")
            if rec and rec not in recommendations:
                recommendations.append(rec)

        return AuditResponse(
            business_id=business_id,
            audit_type=raw.get("audit_type", scope),
            run_at=raw.get("timestamp", datetime.now(timezone.utc).isoformat()),
            overall_score=raw.get("overall_health_score", 0.0),
            category_scores=cat_scores,
            finding_counts=finding_counts,
            top_findings=top_findings,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------ proposals

    def get_proposals(
        self,
        business_id: str,
        status_filter: str = "pending",
        channel: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProposalListResponse:
        """Return a paginated list of proposals."""
        all_proposals = _load_proposals(business_id, self._workspace_dir)

        # Counts
        pending_count = sum(1 for p in all_proposals if p.get("status") in ("proposed", "pending"))
        approved_count = sum(1 for p in all_proposals if p.get("status") == "approved")
        rejected_count = sum(1 for p in all_proposals if p.get("status") == "rejected")

        # Filter
        if status_filter == "pending":
            filtered = [p for p in all_proposals if p.get("status") in ("proposed", "pending")]
        elif status_filter != "all":
            filtered = [p for p in all_proposals if p.get("status") == status_filter]
        else:
            filtered = list(all_proposals)

        if channel:
            filtered = [p for p in filtered if p.get("channel") == channel]

        total_count = len(filtered)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]
        has_more = end < total_count

        # Slim down each proposal to essential fields
        slim: List[Dict[str, Any]] = []
        for p in page_items:
            slim.append({
                "id": p.get("id", ""),
                "title": p.get("title", ""),
                "channel": p.get("channel", ""),
                "risk_tier": p.get("risk_tier", ""),
                "priority": p.get("priority_score", p.get("priority", "")),
                "status": p.get("status", ""),
                "created_at": p.get("created_at", ""),
                "estimated_spend": p.get("estimated_cost", 0.0),
            })

        return ProposalListResponse(
            business_id=business_id,
            total_count=total_count,
            pending_count=pending_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
            proposals=slim,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    # ------------------------------------------------------ proposal detail

    def get_proposal_detail(self, business_id: str, action_id: str) -> ProposalDetailResponse:
        """Return full detail for a single proposal."""
        action = _load_action(action_id, self._workspace_dir)
        if action is None:
            return ProposalDetailResponse(proposal={})

        # Attempt to load the source finding
        finding: Optional[Dict[str, Any]] = None
        source_finding_id = action.get("source_finding_id")
        if source_finding_id:
            audit = _load_audit(business_id, self._workspace_dir)
            if audit:
                for f in audit.get("findings", []):
                    fid = f.get("id") if isinstance(f, dict) else getattr(f, "id", None)
                    if fid == source_finding_id:
                        finding = f if isinstance(f, dict) else f.model_dump()
                        break

        # Content preview from payload
        preview: Optional[Dict[str, Any]] = None
        payload = action.get("suggested_payload", {})
        if isinstance(payload, dict) and payload:
            preview = {
                "content": payload.get("preview", payload.get("content", "")),
                "format": payload.get("format", "text"),
            }

        # Compliance result if attached
        compliance = action.get("compliance_result") or action.get("policy_result")

        # Routing decision
        routing = action.get("routing_decision")

        # Revision history
        revision = action.get("revision_history")

        # Similar past actions -- look in history
        similar: List[Dict[str, Any]] = []
        history_entries = _load_history(business_id, self._workspace_dir, limit=100)
        action_type = action.get("action_type", "")
        action_channel = action.get("channel", "")
        for h in history_entries:
            if (
                h.get("action_type") == action_type
                and h.get("channel") == action_channel
                and h.get("id") != action_id
            ):
                similar.append({
                    "id": h.get("id", ""),
                    "title": h.get("title", ""),
                    "status": h.get("status", ""),
                    "outcome": h.get("outcome", ""),
                    "timestamp": h.get("timestamp", ""),
                })
                if len(similar) >= 5:
                    break

        return ProposalDetailResponse(
            proposal=action,
            finding=finding,
            compliance_result=compliance,
            preview=preview,
            routing_decision=routing,
            revision_history=revision,
            similar_past_actions=similar,
        )

    # -------------------------------------------------------------- approve

    def approve_action(self, request: ApprovalRequest) -> ApprovalResponse:
        """Approve a proposed action."""
        action = _load_action(request.action_id, self._workspace_dir)
        if action is None:
            return ApprovalResponse(
                action_id=request.action_id,
                status="error",
                route="none",
                next_action="not_found",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        current = action.get("status", "")
        if current not in ("proposed", "pending"):
            return ApprovalResponse(
                action_id=request.action_id,
                status="error",
                route="none",
                next_action=f"invalid_state_{current}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        now = datetime.now(timezone.utc).isoformat()
        action["status"] = "approved"
        action["approved_at"] = now
        action["approved_by"] = request.approved_by
        if request.notes:
            action["approval_notes"] = request.notes
        _save_action(action, self._workspace_dir)

        return ApprovalResponse(
            action_id=request.action_id,
            status="approved",
            route=action.get("approval_requirement", "operator_review"),
            next_action="queued_for_execution",
            timestamp=now,
        )

    # --------------------------------------------------------------- reject

    def reject_action(self, request: RejectionRequest) -> ApprovalResponse:
        """Reject a proposed action with feedback."""
        action = _load_action(request.action_id, self._workspace_dir)
        if action is None:
            return ApprovalResponse(
                action_id=request.action_id,
                status="error",
                route="none",
                next_action="not_found",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        current = action.get("status", "")
        if current not in ("proposed", "pending"):
            return ApprovalResponse(
                action_id=request.action_id,
                status="error",
                route="none",
                next_action=f"invalid_state_{current}",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        now = datetime.now(timezone.utc).isoformat()
        action["status"] = "rejected"
        action["rejected_at"] = now
        action["rejected_by"] = request.rejected_by
        action["rejection_reason"] = request.reason
        if request.category:
            action["rejection_category"] = request.category
        if request.specific_issues:
            action["specific_issues"] = request.specific_issues
        if request.revision_guidance:
            action["revision_guidance"] = request.revision_guidance
        action["do_not_retry"] = request.do_not_retry
        _save_action(action, self._workspace_dir)

        # Determine next action based on do_not_retry
        if request.do_not_retry:
            next_action = "killed"
        else:
            next_action = "revision_in_progress"

        return ApprovalResponse(
            action_id=request.action_id,
            status="rejected",
            route=action.get("approval_requirement", "operator_review"),
            next_action=next_action,
            timestamp=now,
        )

    # -------------------------------------------------------------- execute

    def execute_action(self, business_id: str, action_id: str) -> Dict[str, Any]:
        """Execute an approved action.

        Attempts to use the ActionExecutor for real connector dispatch.
        Falls back to marking "in_progress" if the executor is not configured
        or if any import fails.
        """
        # Try the executor bridge first
        try:
            executor = self._build_executor(business_id)
            if executor is not None:
                result = executor.execute(action_id)
                return {
                    "action_id": action_id,
                    "status": "completed" if result.success else "failed",
                    "executed_at": result.timestamp,
                    "action_type": result.method_called,
                    "channel": result.connector_type,
                    "dry_run": result.dry_run,
                    "result": result.response_data,
                    "error": result.error,
                }
        except Exception:
            pass  # Fall through to legacy behavior

        # Legacy: mark in_progress without calling a connector
        action = _load_action(action_id, self._workspace_dir)
        if action is None:
            return {
                "action_id": action_id,
                "status": "error",
                "error": "Action not found",
            }

        if action.get("status") != "approved":
            return {
                "action_id": action_id,
                "status": "error",
                "error": f"Action not approved (current status: {action.get('status', 'unknown')})",
            }

        now = datetime.now(timezone.utc).isoformat()
        action["status"] = "in_progress"
        action["executed_at"] = now
        _save_action(action, self._workspace_dir)

        return {
            "action_id": action_id,
            "status": "in_progress",
            "executed_at": now,
            "action_type": action.get("action_type", ""),
            "channel": action.get("channel", ""),
            "title": action.get("title", ""),
        }

    def _build_executor(self, business_id: str) -> Optional[Any]:
        """Try to construct an ActionExecutor. Returns None if deps missing."""
        try:
            from kai.execution.executor import ActionExecutor
            from kai.execution.credentials import CredentialStore
            from kai.execution.connector_factory import ConnectorFactory
            from kai.runtime.actions import ActionStore
            from kai.runtime.integrations import IntegrationRegistry
            from kai.runtime.policy import PolicyEngine

            action_store = ActionStore()
            registry = IntegrationRegistry()
            cred_store = CredentialStore()
            factory = ConnectorFactory(cred_store)
            policy = PolicyEngine()

            return ActionExecutor(
                action_store=action_store,
                integration_registry=registry,
                connector_factory=factory,
                policy_engine=policy,
                dry_run=True,  # Safe default
            )
        except Exception:
            return None

    # --------------------------------------------------------------- status

    def get_status(self, business_id: str) -> StatusResponse:
        """Return the system status for a business."""
        proposals = _load_proposals(business_id, self._workspace_dir)
        watcher_state = _load_watchers(business_id, self._workspace_dir)
        history = _load_history(business_id, self._workspace_dir, days=7, limit=10)

        pending = [p for p in proposals if p.get("status") in ("proposed", "pending")]
        pending_by_tier: Dict[str, int] = {}
        for p in pending:
            tier = p.get("risk_tier", "unknown")
            pending_by_tier[tier] = pending_by_tier.get(tier, 0) + 1

        active_campaigns = [
            {
                "name": p.get("title", ""),
                "channel": p.get("channel", ""),
                "status": p.get("status", ""),
                "key_metric": p.get("expected_outcome", ""),
            }
            for p in proposals
            if p.get("status") == "in_progress"
        ]

        recent_actions = [
            {
                "timestamp": h.get("timestamp", h.get("created_at", "")),
                "title": h.get("title", ""),
                "status": h.get("status", ""),
            }
            for h in history[:10]
        ]

        watchers_list = watcher_state.get("watchers", [])
        findings_list = watcher_state.get("findings", [])
        enabled = sum(1 for w in watchers_list if w.get("enabled", True))
        critical_alerts = [
            f for f in findings_list
            if f.get("severity") in ("critical", "high") and f.get("urgency", "") == "immediate"
        ]

        return StatusResponse(
            business_id=business_id,
            system_status="active",
            pending_actions=pending_by_tier,
            active_campaigns=active_campaigns,
            recent_actions=recent_actions,
            active_watchers=enabled,
            watcher_findings_today=len(findings_list),
            critical_alerts=critical_alerts,
            kill_switches_active=[],
        )

    # -------------------------------------------------------------- history

    def get_history(
        self,
        business_id: str,
        days: int = 30,
        channel: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return paginated action history."""
        entries = _load_history(
            business_id,
            self._workspace_dir,
            days=days,
            channel=channel,
            limit=limit,
        )
        return {
            "business_id": business_id,
            "entries": entries,
            "count": len(entries),
            "days": days,
        }

    # ------------------------------------------------------------ dashboard

    def get_dashboard(self, business_id: str) -> DashboardResponse:
        """Return a high-level dashboard summary."""
        profile = _load_profile(business_id, self._workspace_dir) or {}
        audit_data = _load_audit(business_id, self._workspace_dir) or {}
        proposals = _load_proposals(business_id, self._workspace_dir)
        watcher_state = _load_watchers(business_id, self._workspace_dir)

        overall_score = audit_data.get("overall_health_score", 0.0)
        overall_health = _health_label(overall_score)

        # Build scorecards list
        scorecards: List[Dict[str, Any]] = []
        for cat_id, sc in audit_data.get("category_scores", {}).items():
            if isinstance(sc, dict):
                scorecards.append(sc)
            elif hasattr(sc, "model_dump"):
                scorecards.append(sc.model_dump())

        # Top wins (high-score categories)
        top_wins: List[str] = []
        for sc in sorted(scorecards, key=lambda s: s.get("score", 0), reverse=True)[:3]:
            name = sc.get("category_display_name", sc.get("category", ""))
            score = sc.get("score", 0)
            if score >= 70:
                top_wins.append(f"{name}: {score}/100")

        # Top concerns (low-score categories)
        top_concerns: List[str] = []
        for sc in sorted(scorecards, key=lambda s: s.get("score", 0))[:3]:
            name = sc.get("category_display_name", sc.get("category", ""))
            score = sc.get("score", 0)
            if score < 70:
                top_concerns.append(f"{name}: {score}/100")

        # Recommended actions
        recommended: List[str] = []
        findings = audit_data.get("findings", [])
        for f in findings[:5]:
            rec = f.get("recommendation", "") if isinstance(f, dict) else getattr(f, "recommendation", "")
            if rec and rec not in recommended:
                recommended.append(rec)

        pending_count = sum(1 for p in proposals if p.get("status") in ("proposed", "pending"))

        # Channel overview
        channels_seen: Dict[str, Dict[str, Any]] = {}
        for p in proposals:
            ch = p.get("channel", "other")
            if ch not in channels_seen:
                channels_seen[ch] = {"channel": ch, "proposal_count": 0, "status_summary": {}}
            channels_seen[ch]["proposal_count"] += 1
            st = p.get("status", "unknown")
            channels_seen[ch]["status_summary"][st] = channels_seen[ch]["status_summary"].get(st, 0) + 1

        return DashboardResponse(
            business_id=business_id,
            business_name=profile.get("name", business_id),
            generated_at=datetime.now(timezone.utc).isoformat(),
            overall_health_score=overall_score,
            overall_health=overall_health,
            scorecards=scorecards,
            top_wins=top_wins,
            top_concerns=top_concerns,
            recommended_actions=recommended,
            pending_approvals=pending_count,
            channel_overview=list(channels_seen.values()),
            trend_data=None,
        )

    # ------------------------------------------------------------- watchers

    def get_watchers(self, business_id: str) -> WatcherResponse:
        """Return watcher state and recent findings."""
        state = _load_watchers(business_id, self._workspace_dir)
        watchers = state.get("watchers", [])
        findings = state.get("findings", [])

        enabled = sum(1 for w in watchers if w.get("enabled", True))

        by_severity: Dict[str, int] = {}
        for f in findings:
            sev = f.get("severity", "info")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        last_runs: Dict[str, str] = {}
        for w in watchers:
            name = w.get("name", "")
            lr = w.get("last_run", "")
            if name and lr:
                last_runs[name] = lr

        # Enrich findings with auto_eligible flag
        enriched: List[Dict[str, Any]] = []
        for f in findings:
            entry = dict(f) if isinstance(f, dict) else {"title": str(f)}
            entry.setdefault("auto_eligible", False)
            enriched.append(entry)

        return WatcherResponse(
            business_id=business_id,
            total_watchers=len(watchers),
            enabled_watchers=enabled,
            recent_findings=enriched,
            findings_by_severity=by_severity,
            last_run_times=last_runs,
        )

    # -------------------------------------------------------------- profile

    def get_profile(self, business_id: str) -> ProfileResponse:
        """Return the business profile."""
        profile = _load_profile(business_id, self._workspace_dir)
        if profile is None:
            return ProfileResponse(business_id=business_id)

        return ProfileResponse(
            business_id=business_id,
            profile=profile,
            archetype=profile.get("archetype", ""),
            active_channels=profile.get("active_channels", []),
            last_updated=profile.get("last_updated", profile.get("updated_at", "")),
        )

    def update_profile(self, business_id: str, request: ProfileUpdateRequest) -> ProfileResponse:
        """Update safe fields on the business profile."""
        profile = _load_profile(business_id, self._workspace_dir)
        if profile is None:
            return ProfileResponse(business_id=business_id)

        # Only allow updating non-protected fields that already exist.
        for key, value in request.fields.items():
            if key in _PROFILE_PROTECTED_FIELDS:
                continue
            if key in profile:
                profile[key] = value

        profile["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_profile(profile, self._workspace_dir)

        return ProfileResponse(
            business_id=business_id,
            profile=profile,
            archetype=profile.get("archetype", ""),
            active_channels=profile.get("active_channels", []),
            last_updated=profile.get("last_updated", ""),
        )

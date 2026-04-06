"""Approve / Reject / Revise flow -- queue-based operator decision workflow.

Provides a structured approval workflow:

1. Load pending actions into a review queue (sorted by priority and risk)
2. Show full context for the current action (including memory-based
   insights about similar past actions)
3. Approve, reject (with reason and revision guidance), or defer
4. Batch-approve low-risk actions
5. Get a summary of all decisions made in the session

The flow enforces that batch approvals are only allowed for low-risk
actions and tracks all decisions with timestamps and reasons.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------

@dataclass
class ApprovalFlowState:
    """Serializable state for the approval flow."""

    business_id: str = ""
    queue: List[Dict[str, Any]] = field(default_factory=list)
    current_index: int = 0
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    batch_mode: bool = False

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Risk tier ordering
# ---------------------------------------------------------------------------

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
_PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


# ---------------------------------------------------------------------------
# ApproveRejectReviseFlow
# ---------------------------------------------------------------------------

class ApproveRejectReviseFlow:
    """Queue-based approval workflow for pending marketing actions.

    Usage::

        flow = ApproveRejectReviseFlow(workspace_dir="workspace")
        state = flow.start("biz_abc123")
        context = flow.show_current_action(state)
        state = flow.approve(state, notes="Looks good")
        # or
        state = flow.reject(state, reason="Copy too aggressive",
                            category="tone", revision_guidance="Soften the CTA")
        summary = flow.get_summary(state)
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir

    # -- lifecycle -------------------------------------------------------

    def start(
        self,
        business_id: str,
        action_ids: Optional[List[str]] = None,
    ) -> ApprovalFlowState:
        """Load pending actions into the review queue.

        If *action_ids* is provided, only those actions are loaded.
        Otherwise all pending actions for the business are loaded.
        Actions are sorted by priority (urgent first) then risk tier
        (high first within each priority) so the operator sees the
        most important items first.
        """
        actions = self._load_pending_actions(business_id, action_ids)

        # Sort: highest priority first, then highest risk first
        actions.sort(key=lambda a: (
            _PRIORITY_ORDER.get(a.get("priority", "medium"), 2),
            -_RISK_ORDER.get(a.get("risk_tier", "low"), 0),
        ))

        return ApprovalFlowState(
            business_id=business_id,
            queue=actions,
            current_index=0,
        )

    # -- action context --------------------------------------------------

    def show_current_action(self, state: ApprovalFlowState) -> Dict[str, Any]:
        """Return full context for the current action in the queue.

        Includes action details, source finding, impact estimate,
        compliance result, content preview, similar past actions from
        memory, and a routing recommendation.
        """
        if state.current_index >= len(state.queue):
            return {
                "message": "No more actions in the queue.",
                "queue_exhausted": True,
            }

        action = state.queue[state.current_index]

        # Load similar past actions from history for memory-based context
        similar_past = self._find_similar_past_actions(
            state.business_id,
            action.get("action_type", ""),
            action.get("channel", ""),
        )

        # Build routing recommendation
        risk_tier = action.get("risk_tier", "low")
        recommendation = self._build_routing_recommendation(action, similar_past)

        return {
            "position_in_queue": state.current_index + 1,
            "total_in_queue": len(state.queue),
            "action_details": {
                "action_id": action.get("action_id", action.get("id", "")),
                "title": action.get("title", ""),
                "description": action.get("description", ""),
                "channel": action.get("channel", ""),
                "action_type": action.get("action_type", ""),
                "risk_tier": risk_tier,
                "priority": action.get("priority", "medium"),
            },
            "source_finding": action.get("source_finding", {}),
            "impact_estimate": action.get("impact_estimate", {}),
            "compliance_result": action.get("compliance_result", {"passed": True, "checks": []}),
            "content_preview": action.get("content_preview", ""),
            "similar_past_actions": similar_past[:3],
            "routing_recommendation": recommendation,
        }

    # -- decision methods ------------------------------------------------

    def approve(
        self,
        state: ApprovalFlowState,
        notes: Optional[str] = None,
    ) -> ApprovalFlowState:
        """Approve the current action and advance to the next."""
        if state.current_index >= len(state.queue):
            return state

        action = state.queue[state.current_index]
        action_id = action.get("action_id", action.get("id", ""))

        state.decisions.append({
            "action_id": action_id,
            "decision": "approved",
            "reason": notes or "",
            "timestamp": _utc_now(),
        })

        # Mark the action as approved in the queue copy
        action["approval_status"] = "approved"
        action["approved_at"] = _utc_now()

        state.current_index += 1
        return state

    def reject(
        self,
        state: ApprovalFlowState,
        reason: str,
        category: str,
        revision_guidance: Optional[str] = None,
    ) -> ApprovalFlowState:
        """Reject the current action with a reason and optional revision guidance."""
        if state.current_index >= len(state.queue):
            return state

        action = state.queue[state.current_index]
        action_id = action.get("action_id", action.get("id", ""))

        decision_record: Dict[str, Any] = {
            "action_id": action_id,
            "decision": "rejected",
            "reason": reason,
            "rejection_category": category,
            "timestamp": _utc_now(),
        }

        if revision_guidance:
            decision_record["revision_guidance"] = revision_guidance
            decision_record["revision_triggered"] = True
            action["revision_status"] = "revision_requested"
            action["revision_guidance"] = revision_guidance
        else:
            decision_record["revision_triggered"] = False

        state.decisions.append(decision_record)

        action["approval_status"] = "rejected"
        action["rejected_at"] = _utc_now()
        action["rejection_reason"] = reason
        action["rejection_category"] = category

        state.current_index += 1
        return state

    def defer(self, state: ApprovalFlowState) -> ApprovalFlowState:
        """Skip the current action for now (defer to later review)."""
        if state.current_index >= len(state.queue):
            return state

        action = state.queue[state.current_index]
        action_id = action.get("action_id", action.get("id", ""))

        state.decisions.append({
            "action_id": action_id,
            "decision": "deferred",
            "reason": "",
            "timestamp": _utc_now(),
        })

        action["approval_status"] = "deferred"

        state.current_index += 1
        return state

    def batch_approve(
        self,
        state: ApprovalFlowState,
        action_ids: List[str],
    ) -> ApprovalFlowState:
        """Approve multiple actions at once.

        Only allowed for actions with ``risk_tier == "low"``.  Actions
        with higher risk tiers are silently skipped and not approved.

        Returns the updated state with all qualifying actions approved.
        """
        approved_ids: List[str] = []
        skipped_ids: List[str] = []

        for action in state.queue:
            aid = action.get("action_id", action.get("id", ""))
            if aid not in action_ids:
                continue

            risk = action.get("risk_tier", "low")
            if risk != "low":
                skipped_ids.append(aid)
                continue

            action["approval_status"] = "approved"
            action["approved_at"] = _utc_now()
            approved_ids.append(aid)

            state.decisions.append({
                "action_id": aid,
                "decision": "approved",
                "reason": "batch_approved",
                "batch": True,
                "timestamp": _utc_now(),
            })

        # Log skipped actions as a single note for transparency
        if skipped_ids:
            state.decisions.append({
                "action_id": ",".join(skipped_ids),
                "decision": "batch_skipped",
                "reason": "risk_tier above low -- individual review required",
                "timestamp": _utc_now(),
            })

        return state

    # -- summary ---------------------------------------------------------

    def get_summary(self, state: ApprovalFlowState) -> Dict[str, Any]:
        """Return a summary of all decisions made in this session."""
        approved = sum(1 for d in state.decisions if d["decision"] == "approved")
        rejected = sum(1 for d in state.decisions if d["decision"] == "rejected")
        deferred = sum(1 for d in state.decisions if d["decision"] == "deferred")
        batch_skipped = sum(1 for d in state.decisions if d["decision"] == "batch_skipped")
        remaining = max(0, len(state.queue) - state.current_index)

        return {
            "total_reviewed": approved + rejected + deferred,
            "approved_count": approved,
            "rejected_count": rejected,
            "deferred_count": deferred,
            "batch_skipped_count": batch_skipped,
            "remaining": remaining,
            "decisions": state.decisions,
        }

    # -- private helpers -------------------------------------------------

    def _load_pending_actions(
        self,
        business_id: str,
        action_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Load pending actions from the workspace proposals directory."""
        proposals_dir = os.path.join(self.workspace_dir, "proposals", business_id)
        actions: List[Dict[str, Any]] = []

        if not os.path.isdir(proposals_dir):
            return actions

        for fname in os.listdir(proposals_dir):
            if not fname.endswith(".json"):
                continue
            data = _load_json_file(os.path.join(proposals_dir, fname))
            if data is None:
                continue

            # Filter to pending actions
            status = data.get("approval_state", data.get("approval_status", "pending"))
            if status != "pending":
                continue

            aid = data.get("action_id", data.get("id", ""))
            if action_ids is not None and aid not in action_ids:
                continue

            actions.append(data)

        return actions

    def _find_similar_past_actions(
        self,
        business_id: str,
        action_type: str,
        channel: str,
    ) -> List[Dict[str, Any]]:
        """Find past actions of the same type/channel for context.

        Scans the history directory for completed actions that share
        the same action_type or channel.  Returns summary records with
        outcome information.
        """
        history_dir = os.path.join(self.workspace_dir, "history", business_id)
        similar: List[Dict[str, Any]] = []

        if not os.path.isdir(history_dir):
            return similar

        for fname in sorted(os.listdir(history_dir), reverse=True):
            if not fname.endswith(".json"):
                continue
            data = _load_json_file(os.path.join(history_dir, fname))
            if data is None:
                continue

            matches_type = data.get("action_type") == action_type
            matches_channel = data.get("channel") == channel

            if matches_type or matches_channel:
                similar.append({
                    "action_id": data.get("action_id", data.get("id", "")),
                    "title": data.get("title", ""),
                    "action_type": data.get("action_type", ""),
                    "channel": data.get("channel", ""),
                    "outcome": data.get("outcome_summary", data.get("result_summary", "")),
                    "approval_status": data.get("approval_status", ""),
                    "date": data.get("executed_at", data.get("created_at", "")),
                })

            if len(similar) >= 5:
                break

        return similar

    def _build_routing_recommendation(
        self,
        action: Dict[str, Any],
        similar_past: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a routing recommendation based on risk and history.

        Considers the action's risk tier, compliance result, and how
        similar past actions performed to produce a recommendation.
        """
        risk = action.get("risk_tier", "low")
        compliance = action.get("compliance_result", {})
        compliance_passed = compliance.get("passed", True) if isinstance(compliance, dict) else True

        # Count past outcomes
        past_success = sum(
            1 for p in similar_past
            if p.get("approval_status") in ("approved", "auto_approved")
        )
        past_failures = sum(
            1 for p in similar_past
            if p.get("approval_status") == "rejected"
        )

        if not compliance_passed:
            recommendation = "review_carefully"
            reason = "Compliance check flagged issues -- review violations before approving."
        elif risk == "high":
            recommendation = "review_carefully"
            reason = "High-risk action requires careful operator review."
        elif risk == "low" and past_failures == 0 and past_success >= 2:
            recommendation = "safe_to_approve"
            reason = f"Low risk with {past_success} successful similar past actions."
        elif risk == "low":
            recommendation = "likely_safe"
            reason = "Low-risk action with no history of issues."
        else:
            recommendation = "review_recommended"
            reason = "Medium-risk action -- operator review recommended."

        return {
            "recommendation": recommendation,
            "reason": reason,
            "past_success_count": past_success,
            "past_failure_count": past_failures,
        }

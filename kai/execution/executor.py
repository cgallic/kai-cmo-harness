"""Action executor — bridges approved actions to live connector calls.

This is the nerve ending between the nervous system (ActionStore, PolicyEngine,
IntegrationRegistry) and the arms (connectors).  It takes an action_id,
validates it through all safety gates, then dispatches to the appropriate
connector method.

Prefers Pipedream-backed execution when the integration has a
``connected_account_id``.  Falls back to direct connector dispatch
for integrations wired through credential-based connectors.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from kai.runtime.actions import ActionStore
from kai.runtime.connector_health import evaluate_connector_health_gate
from kai.runtime.integrations import IntegrationRegistry
from kai.runtime.mandates import MandateLedger, get_default_mandate_ledger
from kai.runtime.policy import PolicyEngine

from .connector_factory import ConnectorFactory
from .result import ExecutionResult

logger = logging.getLogger(__name__)


def _get_pipedream_executor():
    """Lazy-import PipedreamExecutor to avoid hard SDK dependency."""
    try:
        from gateway.adapters.pipedream.executor import PipedreamExecutor
        return PipedreamExecutor()
    except (ImportError, Exception):
        return None


def _get_execution_log():
    """Lazy-import ExecutionLog for persistent logging."""
    try:
        from kai.runtime.connector_health import ExecutionLog
        return ExecutionLog()
    except (ImportError, Exception):
        return None


# ---------------------------------------------------------------------------
# Dispatch table: (channel, action_type) -> connector method name
# ---------------------------------------------------------------------------

_DISPATCH_TABLE: Dict[tuple, str] = {
    # Website
    ("website", "update_page_copy"): "update_page_section",
    ("website", "update_page_section"): "update_page_section",
    ("website", "update_metadata"): "update_metadata",
    ("website", "update_cta"): "update_page_section",
    ("website", "fix_broken_link"): "update_page_section",
    ("website", "fix_tracking"): "update_page_section",
    ("website", "refresh_approved_section"): "update_page_section",
    # Email / Lifecycle
    ("email", "launch_email_sequence"): "create_sequence",
    ("email", "send_approved_template"): "send_email",
    ("email", "update_nurture_copy"): "update_contact",
    # Social
    ("social", "publish_social_post"): "create_post",
    ("social", "schedule_social_post"): "create_post",
    ("social", "schedule_approved_post"): "create_post",
    # Paid media
    ("paid_media", "create_ad_creative"): "create_ad",
    ("paid_media", "adjust_budget"): "update_campaign",
    ("paid_media", "adjust_bidding"): "update_campaign",
    ("paid_media", "pause_campaign"): "pause_campaign",
    ("paid_media", "launch_campaign"): "create_campaign",
    ("paid_media", "publish_approved_variant"): "create_ad",
    # Analytics
    ("analytics", "fix_tracking"): "get_metrics",
    ("analytics", "update_goals"): "get_metrics",
}

_READ_ACTION_TYPES = {
    ("analytics", "fix_tracking"),
    ("analytics", "update_goals"),
    ("paid_media", "read_performance"),
    ("paid_media", "evaluate_ads"),
    ("paid_media", "generate_recommendations"),
    ("paid_media", "validate_ad_upload"),
}


class ActionExecutor:
    """Dispatches approved actions to the correct connector.

    Parameters
    ----------
    action_store : ActionStore
        Manages action lifecycle state.
    integration_registry : IntegrationRegistry
        Tracks connected integrations per brand.
    connector_factory : ConnectorFactory
        Creates connector instances from integration entries.
    policy_engine : PolicyEngine
        Re-validates policy at execution time.
    dry_run : bool
        When True (default), connectors run in preview mode.
    """

    def __init__(
        self,
        action_store: ActionStore,
        integration_registry: IntegrationRegistry,
        connector_factory: ConnectorFactory,
        policy_engine: Optional[PolicyEngine] = None,
        mandate_ledger: Optional[MandateLedger] = None,
        dry_run: bool = True,
    ) -> None:
        self._store = action_store
        self._integrations = integration_registry
        self._factory = connector_factory
        self._policy = policy_engine or PolicyEngine()
        self._mandates = mandate_ledger or get_default_mandate_ledger()
        self._dry_run = dry_run

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, action_id: str) -> ExecutionResult:
        """Execute a single approved action end-to-end.

        Steps:
            1. Load action from store.
            2. Guard: must be approved or auto_approved.
            3. Guard: integration must exist, be connected, kill_switch off.
            4. Re-run policy evaluation.
            5. Mark executing in ActionStore.
            6. Create connector via factory.
            7. Dispatch to the correct connector method.
            8. Mark completed or failed in ActionStore.
            9. Return ExecutionResult.
        """
        # 1. Load
        action = self._store.get_action(action_id)
        if action is None:
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Action {action_id} not found",
            )

        channel = action.get("channel", "")
        action_type = action.get("action_type", "")
        brand_id = action.get("brand_id", "")

        # 2. Approval guard
        approval = action.get("approval_state", "")
        if approval not in ("approved", "auto_approved"):
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Action not approved (state: {approval})",
            )

        mandate_validation = self._mandates.validate_for_action(action)
        if not mandate_validation.get("allowed", False):
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Mandate validation failed: {mandate_validation.get('reason', 'unknown reason')}",
            )

        # 3. Connector health gate
        integrations = self._integrations.list_for_brand(brand_id, channel=channel)
        risk_tier = self._policy.assess_risk_tier(
            channel,
            action_type,
            action.get("proposed_changes", {}),
        )
        required_scopes = _infer_required_scopes(action)
        health_decision = evaluate_connector_health_gate(
            integrations,
            required_scopes=required_scopes,
            risk_tier=risk_tier,
        )

        if not health_decision.get("allowed", False):
            self._log_blocked_execution(
                brand_id=brand_id,
                channel=channel,
                action_type=action_type,
                action_id=action_id,
                reason=f"Connector health gate blocked execution: state={health_decision.get('state')} reason={health_decision.get('reason')}",
                gate=health_decision,
            )
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=(
                    "Connector health gate blocked execution: "
                    f"state={health_decision.get('state')} reason={health_decision.get('reason')}"
                ),
            )

        integration = _select_integration(
            integrations=integrations,
            preferred_integration_id=health_decision.get("integration_id"),
        )
        if integration is None:
            self._log_blocked_execution(
                brand_id=brand_id,
                channel=channel,
                action_type=action_type,
                action_id=action_id,
                reason="Connector health gate could not resolve an integration",
                gate=health_decision,
            )
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"No active integration for brand={brand_id} channel={channel}",
            )

        warning = health_decision.get("warning")
        if warning:
            logger.warning(
                "Proceeding with connector health warning for action %s: %s",
                action_id,
                warning,
            )

        # Check kill switch explicitly
        if integration.get("kill_switch", False):
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Kill switch active on channel={channel}",
            )

        # 4. Re-run policy
        policy_result = self._policy.evaluate(action)
        if not policy_result.get("passed", False):
            violations = policy_result.get("violations", [])
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Policy violation at execution time: {violations}",
            )

        # 5. Mark executing
        try:
            self._store.mark_executing(action_id)
        except ValueError as e:
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"State transition error: {e}",
            )

        # Resolve dry-run: per-integration config overrides instance default
        effective_dry_run = integration.get("config", {}).get(
            "dry_run", self._dry_run
        )

        # 6+7. Choose execution path:
        #   - Pipedream-backed if integration has a connected_account_id
        #   - Direct connector dispatch otherwise
        start = time.monotonic()
        connected_account_id = integration.get("connected_account_id")

        if connected_account_id:
            result = self._execute_via_pipedream(
                action_id=action_id,
                brand_id=brand_id,
                channel=channel,
                action_type=action_type,
                provider=integration.get("provider", ""),
                connected_account_id=connected_account_id,
                proposed_changes=action.get("proposed_changes", {}),
                dry_run=effective_dry_run,
                start=start,
            )
        else:
            result = self._execute_via_connector(
                action_id=action_id,
                integration=integration,
                channel=channel,
                action_type=action_type,
                proposed_changes=action.get("proposed_changes", {}),
                dry_run=effective_dry_run,
                start=start,
            )

        # Log to persistent execution log
        self._log_execution(brand_id, channel, action_type, result)
        return result

    # ------------------------------------------------------------------
    # Pipedream execution path
    # ------------------------------------------------------------------

    def _execute_via_pipedream(
        self,
        *,
        action_id: str,
        brand_id: str,
        channel: str,
        action_type: str,
        provider: str,
        connected_account_id: str,
        proposed_changes: Dict[str, Any],
        dry_run: bool,
        start: float,
    ) -> ExecutionResult:
        """Execute through Pipedream adapter — preferred for connected accounts."""
        pd_executor = _get_pipedream_executor()
        if pd_executor is None:
            logger.warning(
                "Pipedream executor unavailable for action %s — falling back",
                action_id,
            )
            self._store.mark_failed(
                action_id,
                error="Pipedream executor not available (SDK not installed?)",
            )
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error="Pipedream executor not available",
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            pd_result = pd_executor.execute(
                brand_id=brand_id,
                channel=channel,
                provider=provider,
                action_type=action_type,
                connected_account_id=connected_account_id,
                proposed_changes=proposed_changes,
                dry_run=dry_run,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self._store.mark_failed(action_id, error=str(e))
            logger.exception("Pipedream execution failed for %s", action_id)
            return ExecutionResult(
                action_id=action_id,
                success=False,
                connector_type=provider,
                error=str(e),
                duration_ms=elapsed,
                dry_run=dry_run,
            )

        elapsed = (time.monotonic() - start) * 1000
        success = pd_result.get("success", False)

        if success:
            result_summary = {
                "method": pd_result.get("method_called", ""),
                "dry_run": pd_result.get("dry_run", dry_run),
                "response": pd_result.get("response_data", {}),
                "execution_path": "pipedream",
            }
            self._store.mark_completed(action_id, result_summary=result_summary)
        else:
            self._store.mark_failed(
                action_id, error=pd_result.get("error", "Unknown Pipedream error")
            )

        return ExecutionResult(
            action_id=action_id,
            success=success,
            connector_type=provider,
            method_called=pd_result.get("method_called", ""),
            response_data=pd_result.get("response_data", {}),
            error=pd_result.get("error"),
            duration_ms=elapsed,
            dry_run=pd_result.get("dry_run", dry_run),
        )

    # ------------------------------------------------------------------
    # Direct connector execution path (legacy/fallback)
    # ------------------------------------------------------------------

    def _execute_via_connector(
        self,
        *,
        action_id: str,
        integration: Dict[str, Any],
        channel: str,
        action_type: str,
        proposed_changes: Dict[str, Any],
        dry_run: bool,
        start: float,
    ) -> ExecutionResult:
        """Execute through direct connector factory — for non-Pipedream integrations."""
        try:
            connector = self._factory.create(integration)
        except Exception as e:
            self._store.mark_failed(action_id, error=f"Connector creation failed: {e}")
            return ExecutionResult(
                action_id=action_id,
                success=False,
                error=f"Connector creation failed: {e}",
                duration_ms=(time.monotonic() - start) * 1000,
            )

        try:
            result_data = self._dispatch(
                connector=connector,
                channel=channel,
                action_type=action_type,
                proposed_changes=proposed_changes,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            self._store.mark_failed(action_id, error=str(e))
            logger.exception("Connector execution failed for %s", action_id)
            return ExecutionResult(
                action_id=action_id,
                success=False,
                connector_type=integration.get("provider", ""),
                error=str(e),
                duration_ms=elapsed,
                dry_run=dry_run,
            )

        elapsed = (time.monotonic() - start) * 1000

        result_summary = {
            "method": result_data.get("method", ""),
            "dry_run": dry_run,
            "response": result_data.get("response", {}),
            "execution_path": "direct_connector",
        }
        self._store.mark_completed(action_id, result_summary=result_summary)

        return ExecutionResult(
            action_id=action_id,
            success=True,
            connector_type=integration.get("provider", ""),
            method_called=result_data.get("method", ""),
            response_data=result_data.get("response", {}),
            duration_ms=elapsed,
            dry_run=dry_run,
            before_state=result_data.get("before_state"),
            after_state=result_data.get("after_state"),
        )

    # ------------------------------------------------------------------
    # Execution logging
    # ------------------------------------------------------------------

    @staticmethod
    def _log_execution(
        brand_id: str,
        channel: str,
        action_type: str,
        result: ExecutionResult,
    ) -> None:
        """Persist execution result to the execution log."""
        exec_log = _get_execution_log()
        if exec_log is None:
            return
        try:
            exec_log.append(brand_id, {
                "action_id": result.action_id,
                "channel": channel,
                "action_type": action_type,
                "success": result.success,
                "connector_type": result.connector_type,
                "method_called": result.method_called,
                "error": result.error,
                "duration_ms": result.duration_ms,
                "dry_run": result.dry_run,
            })
        except Exception:
            logger.debug("Failed to write execution log entry", exc_info=True)

    @staticmethod
    def _log_blocked_execution(
        *,
        brand_id: str,
        channel: str,
        action_type: str,
        action_id: str,
        reason: str,
        gate: Optional[Dict[str, Any]] = None,
    ) -> None:
        exec_log = _get_execution_log()
        if exec_log is None:
            return
        try:
            exec_log.append(
                brand_id,
                {
                    "action_id": action_id,
                    "channel": channel,
                    "action_type": action_type,
                    "success": False,
                    "blocked": True,
                    "error": reason,
                    "gate": gate or {},
                },
            )
        except Exception:
            logger.debug("Failed to write blocked execution log entry", exc_info=True)

    def execute_batch(self, action_ids: List[str]) -> List[ExecutionResult]:
        """Execute multiple approved actions sequentially."""
        return [self.execute(aid) for aid in action_ids]

    # ------------------------------------------------------------------
    # Dispatch logic
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        connector: Any,
        channel: str,
        action_type: str,
        proposed_changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route (channel, action_type) to the correct connector method.

        Returns a dict with keys: method, response, before_state (optional),
        after_state (optional).
        """
        key = (channel, action_type)
        method_name = _DISPATCH_TABLE.get(key)

        if method_name is None:
            raise ValueError(
                f"No dispatch handler for ({channel!r}, {action_type!r}). "
                f"Supported: {sorted(_DISPATCH_TABLE.keys())}"
            )

        # Check the connector actually has this method
        if not hasattr(connector, method_name):
            raise AttributeError(
                f"Connector {type(connector).__name__} has no method {method_name!r}"
            )

        # Channel-specific dispatch
        if channel == "website":
            return self._dispatch_website(connector, method_name, proposed_changes)
        if channel == "email":
            return self._dispatch_email(connector, method_name, proposed_changes)
        if channel == "social":
            return self._dispatch_social(connector, method_name, proposed_changes)
        if channel == "paid_media":
            return self._dispatch_paid_media(connector, method_name, proposed_changes)

        # Generic fallback
        method = getattr(connector, method_name)
        response = method(**proposed_changes)
        return {"method": method_name, "response": response}

    # ------------------------------------------------------------------
    # Channel-specific dispatchers
    # ------------------------------------------------------------------

    def _dispatch_website(
        self, connector: Any, method_name: str, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch a website action with before/after snapshots."""
        page_id = changes.get("page_id", "")

        # Capture before-state for rollback
        before_state = None
        if hasattr(connector, "snapshot_page") and page_id:
            try:
                before_state = connector.snapshot_page(page_id)
            except Exception:
                logger.warning("Could not capture before-state for page %s", page_id)

        method = getattr(connector, method_name)
        if method_name == "update_page_section":
            response = method(
                page_id=page_id,
                section_id=changes.get("section_id", ""),
                content=changes.get("new_content", changes.get("content", "")),
                content_type=changes.get("content_type", "html"),
            )
        elif method_name == "update_metadata":
            response = method(
                page_id=page_id,
                meta=changes.get("meta", {}),
            )
        else:
            response = method(**changes)

        # Capture after-state
        after_state = None
        if hasattr(connector, "snapshot_page") and page_id:
            try:
                after_state = connector.snapshot_page(page_id)
            except Exception:
                pass

        return {
            "method": method_name,
            "response": response if isinstance(response, dict) else {"result": str(response)},
            "before_state": before_state,
            "after_state": after_state,
        }

    def _dispatch_email(
        self, connector: Any, method_name: str, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch a lifecycle/email action."""
        method = getattr(connector, method_name)

        if method_name == "create_sequence":
            response = method(changes.get("sequence_config", changes))
        elif method_name == "send_email":
            response = method(changes.get("message", changes))
        else:
            response = method(**changes)

        result = response.model_dump() if hasattr(response, "model_dump") else response
        return {"method": method_name, "response": result if isinstance(result, dict) else {"result": str(result)}}

    def _dispatch_social(
        self, connector: Any, method_name: str, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch a social media action."""
        method = getattr(connector, method_name)

        if method_name == "create_post":
            response = method(changes.get("post", changes))
        else:
            response = method(**changes)

        result = response.model_dump() if hasattr(response, "model_dump") else response
        return {"method": method_name, "response": result if isinstance(result, dict) else {"result": str(result)}}

    def _dispatch_paid_media(
        self, connector: Any, method_name: str, changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatch a paid media action."""
        method = getattr(connector, method_name)

        if method_name == "create_campaign":
            response = method(changes.get("campaign_config", changes))
        elif method_name == "update_campaign":
            response = method(
                campaign_id=changes.get("campaign_id", ""),
                changes=changes.get("changes", changes),
            )
        elif method_name == "pause_campaign":
            response = method(campaign_id=changes.get("campaign_id", ""))
        elif method_name == "create_ad":
            response = method(
                ad_group_id=changes.get("ad_group_id", ""),
                creative=changes.get("creative", changes),
            )
        else:
            response = method(**changes)

        result = response.model_dump() if hasattr(response, "model_dump") else response
        return {"method": method_name, "response": result if isinstance(result, dict) else {"result": str(result)}}


def _infer_required_scopes(action: Dict[str, Any]) -> List[str]:
    metadata = action.get("metadata") or {}
    proposed = action.get("proposed_changes") or {}
    declared = (
        metadata.get("required_scopes")
        or proposed.get("required_scopes")
        or action.get("required_scopes")
    )
    if isinstance(declared, list):
        return [str(scope).strip().lower() for scope in declared if str(scope).strip()]

    channel = action.get("channel", "")
    action_type = action.get("action_type", "")
    if (channel, action_type) in _READ_ACTION_TYPES:
        return ["read"]
    return ["write"]


def _select_integration(
    *,
    integrations: List[Dict[str, Any]],
    preferred_integration_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    if preferred_integration_id:
        for integration in integrations:
            if integration.get("integration_id") == preferred_integration_id:
                return integration
    if integrations:
        return integrations[0]
    return None

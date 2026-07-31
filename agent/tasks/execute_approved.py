"""Execute approved actions through the connector system.

Runs every 5 minutes.  Queries the ActionStore for actions in
approved or auto_approved state that haven't started executing,
then dispatches each through the ActionExecutor.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List, Optional

from .base import BaseTask

logger = logging.getLogger(__name__)

_SOCIAL_READ_BACK_TIMEOUT_SECONDS = 5


def _read_back_outstand(
    *, action: Dict[str, Any], result: Any, registry: Any, factory: Any
) -> Dict[str, Any]:
    """Read back a successfully-created Outstand post within a hard timeout."""
    if (
        action.get("channel") != "social"
        or action.get("action_type") not in {
            "publish_social_post",
            "schedule_social_post",
            "schedule_approved_post",
        }
        or getattr(result, "connector_type", "") != "outstand"
        or getattr(result, "method_called", "") != "create_post"
        or not getattr(result, "success", False)
        or getattr(result, "dry_run", False)
    ):
        return {"status": "skipped"}

    response = getattr(result, "response_data", {}) or {}
    provider_response = response.get("response", response)
    if not isinstance(provider_response, dict):
        return {"status": "unavailable", "reason": "provider response is not an object"}
    post_id = provider_response.get("id") or provider_response.get("post_id")
    if not post_id and isinstance(provider_response.get("data"), dict):
        post_id = provider_response["data"].get("id")
    if not post_id:
        return {"status": "unavailable", "reason": "provider post id missing"}

    integrations = registry.list_for_brand(action.get("brand_id", ""), channel="social")
    integration = next(
        (item for item in integrations if item.get("provider") == "outstand"), None
    )
    if integration is None:
        return {"status": "unavailable", "reason": "outstand integration missing"}

    connector = factory.create_read_only(integration)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(connector.get_post, str(post_id))
        try:
            read_back = future.result(timeout=_SOCIAL_READ_BACK_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            future.cancel()
            return {"status": "timeout", "post_id": str(post_id)}
        except Exception as exc:
            return {"status": "failed", "post_id": str(post_id), "reason": str(exc)}

    receipt = read_back.model_dump() if hasattr(read_back, "model_dump") else read_back
    return {"status": "verified", "post_id": str(post_id), "receipt": receipt}


class ExecuteApprovedActionsTask(BaseTask):
    """Background task: process the approved action queue."""

    @property
    def task_type(self) -> str:
        return "execute_approved_actions"

    @property
    def description(self) -> str:
        return "Process approved marketing actions through connectors"

    async def execute(self, task, **kwargs) -> Optional[Dict[str, Any]]:
        """Find and execute all approved actions.

        Returns a summary dict with counts of processed, succeeded, and
        failed actions.
        """
        try:
            from kai.execution.executor import ActionExecutor
            from kai.execution.credentials import CredentialStore
            from kai.execution.connector_factory import ConnectorFactory
            from kai.runtime.actions import ActionStore
            from kai.runtime.integrations import IntegrationRegistry
            from kai.runtime.policy import PolicyEngine
        except ImportError as e:
            logger.warning("Execution bridge not available: %s", e)
            return {"success": False, "error": f"Import error: {e}"}

        try:
            store = ActionStore()
            registry = IntegrationRegistry()
            cred_store = CredentialStore()
            factory = ConnectorFactory(cred_store)
            policy = PolicyEngine()
            executor = ActionExecutor(
                action_store=store,
                integration_registry=registry,
                connector_factory=factory,
                policy_engine=policy,
                dry_run=False,
            )

            # Claim before executing so multiple long-running workers cannot
            # select the same action between listing and dispatch.
            if store.__class__.__name__ == "ActionStore" and hasattr(store, "claim_ready_actions"):
                ready = store.claim_ready_actions(
                    limit=50,
                    worker_id=f"execute-approved:{getattr(task, 'id', 'unknown')}",
                )
            else:
                # Compatibility for older stores used by downstream products.
                ready = store.list_actions(approval_state="approved", execution_state="pending")
                ready += store.list_actions(approval_state="auto_approved", execution_state="pending")

            if not ready:
                return {"success": True, "processed": 0, "summary": "No actions pending"}

            succeeded = 0
            failed = 0
            errors: List[str] = []

            for action in ready:
                action_id = action.get("action_id", "")
                try:
                    result = executor.execute(action_id)
                except Exception as exc:
                    store.mark_failed(action_id, str(exc))
                    raise
                if result.success:
                    if action.get("channel") == "social" and action.get("action_type") in {
                        "publish_social_post",
                        "schedule_social_post",
                        "schedule_approved_post",
                    }:
                        read_back = _read_back_outstand(
                            action=action, result=result, registry=registry, factory=factory
                        )
                        if read_back.get("status") == "verified":
                            store.mark_verified(action_id, read_back)
                            logger.info("Action %s provider read-back verified", action_id)
                        else:
                            logger.warning("Action %s provider read-back: %s", action_id, read_back)
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(f"{action_id}: {result.error}")
                    logger.warning("Action %s failed: %s", action_id, result.error)

            # Notify on failures
            if failed > 0 and kwargs.get("notify", True):
                summary = f"Executed {succeeded + failed} actions: {succeeded} succeeded, {failed} failed"
                if errors:
                    summary += f"\nErrors: {'; '.join(errors[:3])}"
                try:
                    await self.send_notification(summary)
                except Exception:
                    pass

            return {
                "success": failed == 0,
                "processed": succeeded + failed,
                "succeeded": succeeded,
                "failed": failed,
                "errors": errors,
                "summary": f"{succeeded} succeeded, {failed} failed out of {len(ready)} actions",
            }

        except Exception as e:
            logger.exception("execute_approved_actions task failed")
            return {"success": False, "error": str(e)}

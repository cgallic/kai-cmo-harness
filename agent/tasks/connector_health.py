"""Connector health check — validates all registered integrations.

Runs daily at 7 AM.  Iterates through the IntegrationRegistry, calls
``connector.connect()`` on each, and updates integration status.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import BaseTask

logger = logging.getLogger(__name__)


class ConnectorHealthCheckTask(BaseTask):
    """Background task: health-check all connected integrations."""

    @property
    def task_type(self) -> str:
        return "connector_health_check"

    @property
    def description(self) -> str:
        return "Validate connectivity for all registered integrations"

    async def execute(self, task, **kwargs) -> Optional[Dict[str, Any]]:
        """Check connectivity for each registered integration.

        Updates integration status in the registry and reports any
        disconnected integrations.
        """
        try:
            from kai.execution.credentials import CredentialStore
            from kai.execution.connector_factory import ConnectorFactory
            from kai.runtime.integrations import IntegrationRegistry
        except ImportError as e:
            logger.warning("Execution bridge not available: %s", e)
            return {"success": False, "error": f"Import error: {e}"}

        try:
            registry = IntegrationRegistry()
            cred_store = CredentialStore()
            factory = ConnectorFactory(cred_store)

            # Get all integrations by scanning the directory
            checked = 0
            healthy = 0
            unhealthy = 0
            errors: List[str] = []

            integrations_dir = registry.integrations_dir
            for path in integrations_dir.glob("*.json"):
                import json
                integration = json.loads(path.read_text(encoding="utf-8"))
                integration_id = integration.get("integration_id", "")
                provider = integration.get("provider", "unknown")
                status = integration.get("status", "")

                if status in ("disconnected", "pending_auth"):
                    continue

                checked += 1
                try:
                    connector = factory.create(integration, read_only=True)
                    if hasattr(connector, "connect"):
                        is_healthy = connector.connect()
                    else:
                        is_healthy = True

                    if is_healthy:
                        healthy += 1
                        if status != "connected":
                            registry.update(integration_id, status="connected")
                    else:
                        unhealthy += 1
                        registry.update(integration_id, status="error")
                        errors.append(f"{provider} ({integration_id}): connection failed")

                except Exception as e:
                    unhealthy += 1
                    try:
                        registry.update(integration_id, status="error")
                    except Exception:
                        pass
                    errors.append(f"{provider} ({integration_id}): {e}")
                    logger.warning("Health check failed for %s: %s", integration_id, e)

            # Notify if any integrations went unhealthy
            if unhealthy > 0 and kwargs.get("notify", True):
                msg = f"Connector health: {healthy}/{checked} healthy, {unhealthy} failing"
                if errors:
                    msg += f"\nIssues: {'; '.join(errors[:3])}"
                try:
                    await self.send_notification(msg)
                except Exception:
                    pass

            return {
                "success": unhealthy == 0,
                "checked": checked,
                "healthy": healthy,
                "unhealthy": unhealthy,
                "errors": errors,
                "summary": f"{healthy}/{checked} integrations healthy",
            }

        except Exception as e:
            logger.exception("connector_health_check task failed")
            return {"success": False, "error": str(e)}

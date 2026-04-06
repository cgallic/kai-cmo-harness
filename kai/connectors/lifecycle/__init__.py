"""Lifecycle connectors — email, SMS, and CRM integrations for contact management, sequence execution, and deliverability tracking."""

from __future__ import annotations

import logging
from typing import Dict, Type

from .base import (
    ContactRecord,
    EmailDeliverabilityStats,
    EmailMessage,
    LifecycleConnector,
    LifecycleConnectorConfig,
    SequenceConfig,
    SuppressionEntry,
)
from .crm_base import CRMConnector
from .email_base import EmailProvider
from .generic_smtp import GenericSMTPConnector
from .loops import LoopsConnector
from .mailchimp import MailchimpConnector
from .sendgrid import SendGridConnector
from .sms_base import SMSConnector, SMSMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

LIFECYCLE_REGISTRY: Dict[str, Type[LifecycleConnector]] = {
    "loops": LoopsConnector,
    "mailchimp": MailchimpConnector,
    "sendgrid": SendGridConnector,
    "smtp": GenericSMTPConnector,
}


def get_lifecycle_connector(
    provider: str, config: dict
) -> LifecycleConnector:
    """Factory: instantiate a lifecycle connector by provider name.

    Parameters
    ----------
    provider:
        Provider key — one of ``"loops"``, ``"mailchimp"``, ``"sendgrid"``,
        ``"smtp"``.
    config:
        Dict of kwargs passed to ``LifecycleConnectorConfig``.

    Returns
    -------
    LifecycleConnector
        An instance of the requested connector, ready for ``connect()``.

    Raises
    ------
    ValueError
        If the provider is not found in the registry.
    """
    connector_cls = LIFECYCLE_REGISTRY.get(provider.lower())
    if connector_cls is None:
        available = ", ".join(sorted(LIFECYCLE_REGISTRY.keys()))
        raise ValueError(
            f"Unknown lifecycle provider '{provider}'. "
            f"Available providers: {available}"
        )

    connector_config = LifecycleConnectorConfig(provider=provider.lower(), **config)
    return connector_cls(connector_config)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Data models
    "ContactRecord",
    "EmailDeliverabilityStats",
    "EmailMessage",
    "LifecycleConnectorConfig",
    "SequenceConfig",
    "SMSMessage",
    "SuppressionEntry",
    # Abstract bases
    "CRMConnector",
    "EmailProvider",
    "LifecycleConnector",
    "SMSConnector",
    # Concrete connectors
    "GenericSMTPConnector",
    "LoopsConnector",
    "MailchimpConnector",
    "SendGridConnector",
    # Registry and factory
    "LIFECYCLE_REGISTRY",
    "get_lifecycle_connector",
]

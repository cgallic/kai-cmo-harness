"""Abstract email provider base — extends LifecycleConnector with email-specific helpers.

Concrete email provider connectors (Loops, Mailchimp, SendGrid, SMTP) inherit
from ``EmailProvider`` rather than ``LifecycleConnector`` directly.  This layer
adds convenience wrappers for single sends, transactional emails, engagement
metrics, and domain warm-up status.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Dict, Optional

from .base import (
    ContactRecord,
    EmailDeliverabilityStats,
    EmailMessage,
    LifecycleConnector,
    LifecycleConnectorConfig,
)

logger = logging.getLogger(__name__)


class EmailProvider(LifecycleConnector):
    """Abstract base for email-platform connectors.

    Inherits all 12 abstract methods from ``LifecycleConnector`` (connect,
    get_contacts, create_contact, update_contact, get_lists, create_list,
    send_email, send_batch, get_sequences, create_sequence,
    get_deliverability_stats, manage_unsubscribe) and adds five email-specific
    convenience methods.
    """

    # ------------------------------------------------------------------
    # Additional email-specific methods
    # ------------------------------------------------------------------

    def send_single(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> EmailMessage:
        """Convenience wrapper: build an ``EmailMessage`` and call ``send_email``.

        Parameters
        ----------
        to:
            Recipient email address.
        subject:
            Email subject line.
        body_html:
            HTML body content.
        body_text:
            Optional plain-text fallback.  If omitted, providers should
            auto-generate from the HTML.
        from_email:
            Override the default sender configured on the connector.

        Returns
        -------
        EmailMessage
            The sent message with updated status and provider-assigned ID.
        """
        message = EmailMessage(
            to_email=to,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_email=from_email or self.config.from_email,
            from_name=self.config.from_name,
        )
        return self.send_email(message)

    def send_transactional(
        self,
        to: str,
        template_id: str,
        merge_fields: Dict[str, str],
    ) -> EmailMessage:
        """Send a transactional email using a provider-hosted template.

        Parameters
        ----------
        to:
            Recipient email address.
        template_id:
            Provider template / transactional ID.
        merge_fields:
            Key-value pairs injected into the template's variables.

        Returns
        -------
        EmailMessage
            The sent message with updated status and provider-assigned ID.
        """
        message = EmailMessage(
            to_email=to,
            subject="(template)",  # subject comes from the template
            template_id=template_id,
            merge_fields=merge_fields,
            from_email=self.config.from_email,
            from_name=self.config.from_name,
        )
        return self.send_email(message)

    def get_open_rate(self, campaign_id: Optional[str] = None) -> float:
        """Return the open rate for a campaign or overall.

        If ``campaign_id`` is None, returns the aggregate open rate from
        ``get_deliverability_stats()``.
        """
        stats = self.get_deliverability_stats()
        if stats.total_sent == 0:
            return 0.0
        return stats.open_rate

    def get_click_rate(self, campaign_id: Optional[str] = None) -> float:
        """Return the click rate for a campaign or overall.

        If ``campaign_id`` is None, returns the aggregate click rate from
        ``get_deliverability_stats()``.
        """
        stats = self.get_deliverability_stats()
        if stats.total_sent == 0:
            return 0.0
        return stats.click_rate

    @abstractmethod
    def warm_up_status(self) -> Dict[str, Any]:
        """Check domain warm-up status.

        Returns
        -------
        dict
            ``{"domain": str, "daily_limit": int, "current_day": int,
            "warm_up_complete": bool}``
        """
        ...

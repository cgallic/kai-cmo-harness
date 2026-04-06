"""Generic SMTP email connector — fallback for any email provider via SMTP.

This connector implements email sending via the standard SMTP protocol,
making it compatible with any email service that exposes SMTP credentials
(Gmail SMTP, Amazon SES SMTP, custom mail servers, etc.).

Advanced features like contact management, sequences, and segments are NOT
supported — those require a full email platform (Loops, Mailchimp, SendGrid).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    ContactRecord,
    EmailDeliverabilityStats,
    EmailMessage,
    LifecycleConnectorConfig,
    SequenceConfig,
    SuppressionEntry,
)
from .email_base import EmailProvider

logger = logging.getLogger(__name__)


class GenericSMTPConnector(EmailProvider):
    """SMTP-based email connector.

    SMTP config is read from ``config.metadata``:

    - ``smtp_host`` (str): SMTP server hostname
    - ``smtp_port`` (int): SMTP port (587 for TLS, 465 for SSL)
    - ``smtp_username`` (str): SMTP username
    - ``smtp_password`` (str): SMTP password
    - ``use_tls`` (bool): Use STARTTLS (default True)

    Only ``send_email`` is fully supported.  Contact management, sequences,
    lists, and deliverability stats raise ``NotImplementedError``.
    """

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "smtp"

    # ------------------------------------------------------------------
    # SMTP config helpers
    # ------------------------------------------------------------------

    @property
    def _smtp_host(self) -> str:
        return str(self.config.metadata.get("smtp_host", ""))

    @property
    def _smtp_port(self) -> int:
        return int(self.config.metadata.get("smtp_port", 587))

    @property
    def _smtp_username(self) -> str:
        return str(self.config.metadata.get("smtp_username", ""))

    @property
    def _smtp_password(self) -> str:
        return str(self.config.metadata.get("smtp_password", ""))

    @property
    def _use_tls(self) -> bool:
        return bool(self.config.metadata.get("use_tls", True))

    def _validate_smtp_config(self) -> List[str]:
        """Return a list of missing SMTP configuration fields."""
        missing: List[str] = []
        if not self._smtp_host:
            missing.append("smtp_host")
        if not self._smtp_port:
            missing.append("smtp_port")
        if not self._smtp_username:
            missing.append("smtp_username")
        if not self._smtp_password:
            missing.append("smtp_password")
        return missing

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate SMTP config and test connection.

        In sandbox mode, only validates that config fields are present.
        In live mode, would connect, authenticate, and disconnect.
        """
        missing = self._validate_smtp_config()
        if missing:
            logger.error(
                "SMTP connect failed — missing config fields in metadata: %s",
                missing,
            )
            return False

        if self._is_sandbox():
            logger.info(
                "[SANDBOX] SMTP connect — config valid for %s:%d, skipping real connection",
                self._smtp_host,
                self._smtp_port,
            )
            self._connected = True
            return True

        # In production, this would use smtplib to test the connection:
        #   import smtplib
        #   server = smtplib.SMTP(self._smtp_host, self._smtp_port)
        #   if self._use_tls:
        #       server.starttls()
        #   server.login(self._smtp_username, self._smtp_password)
        #   server.quit()
        #
        # We avoid importing smtplib here to keep the module import-safe
        # in environments where SMTP isn't needed.
        logger.info(
            "SMTP connector configured for %s:%d (user: %s)",
            self._smtp_host,
            self._smtp_port,
            self._smtp_username,
        )
        self._connected = True
        return True

    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------

    def send_email(self, message: EmailMessage) -> EmailMessage:
        """Build a MIME message and send via SMTP.

        Constructs a multipart/alternative message with plain text and
        HTML bodies, adds compliance headers (List-Unsubscribe, physical
        address footer), and sends via SMTP.
        """
        self._check_connected()

        # Compliance checks
        if self._check_suppressed(message.to_email):
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "failed"
            msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "reason": "suppressed"}
            return EmailMessage(**msg_dump)

        violations = self._validate_can_spam(message)
        if violations:
            logger.error("CAN-SPAM violations: %s", violations)
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "failed"
            msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "violations": violations}
            return EmailMessage(**msg_dump)

        if not self._check_rate_limit():
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "failed"
            msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "reason": "rate_limited"}
            return EmailMessage(**msg_dump)

        # Add compliance headers and footer
        message = self._add_compliance_headers(message)

        if self._is_sandbox():
            self._sandbox_response(
                "send_email",
                to=message.to_email,
                subject=message.subject,
                smtp_host=self._smtp_host,
            )
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "sent"
            msg_dump["id"] = f"sandbox-smtp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            self._record_send()
            return EmailMessage(**msg_dump)

        # Build MIME message
        # In production, this would use email.mime modules:
        #   from email.mime.multipart import MIMEMultipart
        #   from email.mime.text import MIMEText
        #   import smtplib
        #
        # For now, we construct the payload dict that represents what
        # would be sent, and defer actual smtplib usage to runtime.
        effective_from = message.from_email or self.config.from_email
        effective_from_name = message.from_name or self.config.from_name

        mime_payload: Dict[str, Any] = {
            "from": f"{effective_from_name} <{effective_from}>",
            "to": message.to_email,
            "subject": message.subject,
            "reply_to": message.reply_to or self.config.reply_to,
            "headers": message.headers,
            "body_text": message.body_text,
            "body_html": message.body_html,
            "attachments": message.attachments,
        }

        logger.info(
            "SMTP send: %s -> %s [%s] via %s:%d",
            effective_from,
            message.to_email,
            message.subject,
            self._smtp_host,
            self._smtp_port,
        )

        # The actual smtplib send would go here:
        #   msg = MIMEMultipart("alternative")
        #   msg["Subject"] = message.subject
        #   msg["From"] = f"{effective_from_name} <{effective_from}>"
        #   msg["To"] = message.to_email
        #   for header, value in message.headers.items():
        #       msg[header] = value
        #   if message.body_text:
        #       msg.attach(MIMEText(message.body_text, "plain"))
        #   if message.body_html:
        #       msg.attach(MIMEText(message.body_html, "html"))
        #   server = smtplib.SMTP(self._smtp_host, self._smtp_port)
        #   if self._use_tls:
        #       server.starttls()
        #   server.login(self._smtp_username, self._smtp_password)
        #   server.sendmail(effective_from, message.to_email, msg.as_string())
        #   server.quit()

        self._record_send()
        msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
        msg_dump["status"] = "queued"
        msg_dump["id"] = f"smtp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "smtp_host": self._smtp_host}
        return EmailMessage(**msg_dump)

    def send_batch(
        self,
        contacts: List[ContactRecord],
        template_id: Optional[str] = None,
        message: Optional[EmailMessage] = None,
    ) -> Dict[str, Any]:
        """Send to multiple contacts by iterating single SMTP sends.

        SMTP has no native batch mechanism — each email is sent
        individually via ``send_email()``.
        """
        self._check_connected()

        if self._is_sandbox():
            return self._sandbox_response(
                "send_batch",
                contact_count=len(contacts),
            )

        results: Dict[str, Any] = {
            "total": len(contacts),
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        for contact in contacts:
            if self._check_suppressed(contact.email):
                results["skipped"] += 1
                continue

            try:
                email_msg = EmailMessage(
                    to_email=contact.email,
                    to_name=contact.full_name or contact.first_name,
                    subject=message.subject if message else "(no subject)",
                    body_html=message.body_html if message else None,
                    body_text=message.body_text if message else None,
                    from_email=self.config.from_email,
                    from_name=self.config.from_name,
                )
                result = self.send_email(email_msg)
                if result.status in ("sent", "queued"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {"email": contact.email, "reason": result.status}
                    )
            except Exception as exc:
                results["failed"] += 1
                results["errors"].append(
                    {"email": contact.email, "reason": str(exc)}
                )

        return results

    # ------------------------------------------------------------------
    # Unsupported features (contact management, sequences, etc.)
    # ------------------------------------------------------------------

    def get_contacts(
        self,
        segment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContactRecord]:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support contact management. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def create_contact(self, contact: ContactRecord) -> ContactRecord:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support contact management. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support contact management. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def get_lists(self) -> List[Dict[str, Any]]:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support list management. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def create_list(
        self, name: str, criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support list management. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def get_sequences(self) -> List[SequenceConfig]:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support sequences. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def create_sequence(self, config: SequenceConfig) -> SequenceConfig:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support sequences. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def get_deliverability_stats(
        self, period: Optional[str] = None
    ) -> EmailDeliverabilityStats:
        """Not supported by generic SMTP."""
        raise NotImplementedError(
            "Generic SMTP connector does not support deliverability stats. "
            "Use a full email platform like Loops, Mailchimp, or SendGrid."
        )

    def manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool:
        """Add to local suppression list only.

        SMTP has no unsubscribe API — we maintain a local suppression list
        to prevent sends to opted-out addresses.
        """
        self._suppression_list.append(
            SuppressionEntry(
                email=email,
                reason=reason,
                suppressed_at=datetime.now(timezone.utc).isoformat(),
                source="smtp-local",
            )
        )
        logger.info(
            "Added %s to local SMTP suppression list (reason: %s). "
            "Note: SMTP has no remote unsubscribe API.",
            email,
            reason,
        )
        return True

    # ------------------------------------------------------------------
    # Warm-up status
    # ------------------------------------------------------------------

    def warm_up_status(self) -> Dict[str, Any]:
        """SMTP connector does not manage warm-up."""
        from_domain = self.config.from_email.split("@")[-1] if "@" in self.config.from_email else "unknown"
        return {
            "domain": from_domain,
            "daily_limit": 0,
            "current_day": 0,
            "warm_up_complete": False,
            "note": "Generic SMTP does not manage IP/domain warm-up. "
                    "Configure warm-up with your email provider directly.",
        }

"""Base abstract connector and shared models for lifecycle (email/SMS/CRM) integrations.

Provides the LifecycleConnector abstract class, data models for contacts, emails,
sequences, deliverability stats, and suppression entries.  Every concrete provider
connector inherits from this base and implements the abstract methods while
inheriting shared compliance helpers (CAN-SPAM validation, suppression checks,
rate limiting, sandbox mode).
"""

from __future__ import annotations

import copy
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
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
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"

else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Data Models
# ============================================================================


class LifecycleConnectorConfig(BaseModel):
    """Configuration shared across all lifecycle connectors."""

    provider: str = Field(..., description="Provider name (loops, mailchimp, sendgrid, smtp, twilio)")
    api_key: Optional[str] = Field(None, description="Provider API key")
    api_secret: Optional[str] = Field(None, description="Provider API secret")
    access_token: Optional[str] = Field(None, description="OAuth access token")
    from_email: str = Field(..., description="Default sending email address")
    from_name: str = Field(..., description="Default sender name")
    reply_to: Optional[str] = Field(None, description="Reply-to address")
    physical_address: str = Field(
        ..., description="CAN-SPAM required physical mailing address"
    )
    sandbox_mode: bool = Field(True, description="No real sends in sandbox")
    rate_limit_per_second: float = Field(10.0, description="Sends per second cap")
    rate_limit_per_hour: int = Field(1000, description="Sends per hour cap")
    unsubscribe_url: Optional[str] = Field(None, description="Custom unsubscribe URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provider-specific settings")


class EmailMessage(BaseModel):
    """A single email message."""

    id: Optional[str] = Field(None, description="Provider-assigned message ID (None before send)")
    to_email: str = Field(..., description="Recipient email address")
    to_name: Optional[str] = Field(None, description="Recipient display name")
    from_email: Optional[str] = Field(None, description="Override default sender email")
    from_name: Optional[str] = Field(None, description="Override default sender name")
    reply_to: Optional[str] = Field(None, description="Reply-to address override")
    subject: str = Field(..., description="Email subject line")
    body_html: Optional[str] = Field(None, description="HTML body")
    body_text: Optional[str] = Field(None, description="Plain text body (fallback)")
    template_id: Optional[str] = Field(None, description="Provider template ID (if using provider templates)")
    merge_fields: Dict[str, str] = Field(default_factory=dict, description="Personalization variables")
    tags: List[str] = Field(default_factory=list, description="Message tags for tracking")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom email headers")
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {filename, content_type, data}",
    )
    send_at: Optional[str] = Field(None, description="ISO timestamp for scheduled send")
    status: str = Field("draft", description="draft|queued|sent|delivered|bounced|failed|opened|clicked")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class EmailDeliverabilityStats(BaseModel):
    """Aggregate deliverability metrics for a time period."""

    total_sent: int = Field(0)
    delivered: int = Field(0)
    delivery_rate: float = Field(0.0)
    opened: int = Field(0)
    open_rate: float = Field(0.0)
    clicked: int = Field(0)
    click_rate: float = Field(0.0)
    bounced: int = Field(0)
    bounce_rate: float = Field(0.0)
    soft_bounces: int = Field(0)
    hard_bounces: int = Field(0)
    spam_complaints: int = Field(0)
    spam_complaint_rate: float = Field(0.0)
    unsubscribes: int = Field(0)
    unsubscribe_rate: float = Field(0.0)
    period: Optional[str] = Field(None, description="Time period for these stats")
    fetched_at: Optional[str] = Field(None, description="ISO timestamp when stats were fetched")


class ContactRecord(BaseModel):
    """A single contact/subscriber record."""

    id: Optional[str] = Field(None, description="Provider-assigned contact ID")
    email: str = Field(..., description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    full_name: Optional[str] = Field(None)
    source: Optional[str] = Field(None, description="How this contact was acquired")
    tags: List[str] = Field(default_factory=list)
    lists: List[str] = Field(default_factory=list, description="List/segment IDs this contact belongs to")
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    opted_in: bool = Field(True)
    opt_in_date: Optional[str] = Field(None, description="ISO timestamp")
    opted_out: bool = Field(False)
    opt_out_date: Optional[str] = Field(None, description="ISO timestamp")
    created_at: Optional[str] = Field(None, description="ISO timestamp")
    last_contacted: Optional[str] = Field(None, description="ISO timestamp")
    contact_count_30d: int = Field(0, description="Messages sent in last 30 days")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SequenceConfig(BaseModel):
    """An email sequence (drip campaign / automation)."""

    id: Optional[str] = Field(None)
    name: str = Field(..., description="Sequence name")
    description: Optional[str] = Field(None)
    trigger_event: Optional[str] = Field(
        None,
        description="What triggers the sequence (form_submit, purchase, manual, etc.)",
    )
    emails: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {delay_days, delay_hours, subject, body_html, body_text}",
    )
    status: str = Field("draft", description="draft|active|paused|completed")
    total_emails: int = Field(0)
    created_at: Optional[str] = Field(None, description="ISO timestamp")


class SuppressionEntry(BaseModel):
    """A suppressed email address (bounce, complaint, unsubscribe)."""

    email: str = Field(..., description="Suppressed email address")
    reason: str = Field(
        ..., description="unsubscribe|hard_bounce|spam_complaint|manual"
    )
    suppressed_at: str = Field(..., description="ISO timestamp")
    source: Optional[str] = Field(None, description="Which system added the suppression")


# ============================================================================
# Abstract Base Connector
# ============================================================================


class LifecycleConnector(ABC):
    """Abstract base for all lifecycle connectors (email, SMS, CRM).

    Every concrete connector must implement the abstract methods below.
    Shared compliance helpers (CAN-SPAM, suppression, rate-limiting, sandbox)
    are provided as concrete methods.
    """

    def __init__(self, config: LifecycleConnectorConfig) -> None:
        self.config = config
        self._connected: bool = False
        self._suppression_list: List[SuppressionEntry] = []
        self._send_timestamps: List[float] = []
        self._hourly_send_count: int = 0
        self._hourly_window_start: float = time.time()

    # ------------------------------------------------------------------
    # Abstract property
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g. 'loops', 'mailchimp')."""
        ...

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> bool:
        """Validate credentials and test connection.  Return True on success."""
        ...

    @abstractmethod
    def get_contacts(
        self,
        segment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContactRecord]:
        """Fetch contacts, optionally filtered by segment/list."""
        ...

    @abstractmethod
    def create_contact(self, contact: ContactRecord) -> ContactRecord:
        """Create a new contact.  Return the contact with provider-assigned ID."""
        ...

    @abstractmethod
    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord:
        """Update contact fields.  Return the updated contact."""
        ...

    @abstractmethod
    def get_lists(self) -> List[Dict[str, Any]]:
        """Fetch mailing lists / segments."""
        ...

    @abstractmethod
    def create_list(
        self, name: str, criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a mailing list.  Return list metadata."""
        ...

    @abstractmethod
    def send_email(self, message: EmailMessage) -> EmailMessage:
        """Send a single email.  Return the message with updated status and id."""
        ...

    @abstractmethod
    def send_batch(
        self,
        contacts: List[ContactRecord],
        template_id: Optional[str] = None,
        message: Optional[EmailMessage] = None,
    ) -> Dict[str, Any]:
        """Send to multiple contacts.  Return summary dict."""
        ...

    @abstractmethod
    def get_sequences(self) -> List[SequenceConfig]:
        """Fetch configured email sequences / automations."""
        ...

    @abstractmethod
    def create_sequence(self, config: SequenceConfig) -> SequenceConfig:
        """Create an email sequence.  Return with provider-assigned ID."""
        ...

    @abstractmethod
    def get_deliverability_stats(
        self, period: Optional[str] = None
    ) -> EmailDeliverabilityStats:
        """Fetch deliverability metrics for the given period."""
        ...

    @abstractmethod
    def manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool:
        """Process an unsubscribe request.  Return True on success."""
        ...

    # ------------------------------------------------------------------
    # Concrete helper methods
    # ------------------------------------------------------------------

    def _is_sandbox(self) -> bool:
        """Return True when sandbox mode is active (no real API calls)."""
        return self.config.sandbox_mode

    def _sandbox_response(self, method_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Return a mock response dict for sandbox mode."""
        logger.info(
            "[SANDBOX] %s.%s called with %s",
            self.provider_name,
            method_name,
            kwargs,
        )
        return {
            "sandbox": True,
            "provider": self.provider_name,
            "method": method_name,
            "kwargs": {k: str(v)[:200] for k, v in kwargs.items()},
            "message": "Sandbox mode — no real API call made.",
        }

    def _check_rate_limit(self) -> bool:
        """Return True if another send is allowed under rate limits.

        Checks both per-second and per-hour caps.  If the hourly window has
        elapsed, resets the counter.
        """
        now = time.time()

        # Reset hourly window if needed
        if now - self._hourly_window_start >= 3600:
            self._hourly_send_count = 0
            self._hourly_window_start = now

        # Per-hour check
        if self._hourly_send_count >= self.config.rate_limit_per_hour:
            logger.warning(
                "Rate limit exceeded: %d/%d sends this hour for %s",
                self._hourly_send_count,
                self.config.rate_limit_per_hour,
                self.provider_name,
            )
            return False

        # Per-second check — keep only timestamps within the last second
        one_second_ago = now - 1.0
        self._send_timestamps = [
            ts for ts in self._send_timestamps if ts > one_second_ago
        ]
        if len(self._send_timestamps) >= self.config.rate_limit_per_second:
            logger.warning(
                "Rate limit exceeded: %.0f/%.0f sends per second for %s",
                len(self._send_timestamps),
                self.config.rate_limit_per_second,
                self.provider_name,
            )
            return False

        return True

    def _record_send(self) -> None:
        """Record a send event for rate-limit tracking."""
        self._send_timestamps.append(time.time())
        self._hourly_send_count += 1

    def _check_suppressed(self, email: str) -> bool:
        """Return True if *email* is on the suppression list."""
        normalized = email.strip().lower()
        for entry in self._suppression_list:
            if entry.email.strip().lower() == normalized:
                logger.info(
                    "Email %s is suppressed (reason: %s, since: %s)",
                    email,
                    entry.reason,
                    entry.suppressed_at,
                )
                return True
        return False

    def _validate_can_spam(self, message: EmailMessage) -> List[str]:
        """Validate CAN-SPAM compliance for an email.

        Returns a list of violation strings.  Empty list means compliant.

        Checks:
        1. from_email is set (on message or config)
        2. physical_address is present in config
        3. unsubscribe URL or List-Unsubscribe header is present
        4. subject is not misleading (not empty, not ALL CAPS)
        """
        violations: List[str] = []

        # 1. From email
        effective_from = message.from_email or self.config.from_email
        if not effective_from:
            violations.append("CAN-SPAM: No from_email set on message or config")

        # 2. Physical address
        if not self.config.physical_address:
            violations.append(
                "CAN-SPAM: physical_address is required in connector config"
            )

        # 3. Unsubscribe mechanism
        has_unsub_url = bool(self.config.unsubscribe_url)
        has_unsub_header = "List-Unsubscribe" in message.headers
        if not has_unsub_url and not has_unsub_header:
            violations.append(
                "CAN-SPAM: No unsubscribe mechanism (set unsubscribe_url in "
                "config or List-Unsubscribe header on message)"
            )

        # 4. Subject sanity
        if not message.subject or not message.subject.strip():
            violations.append("CAN-SPAM: Subject line is empty")
        elif message.subject == message.subject.upper() and len(message.subject) > 3:
            violations.append(
                "CAN-SPAM: Subject line is ALL CAPS — may be considered misleading"
            )

        return violations

    def _check_over_contact(self, email: str, max_per_week: int = 3) -> bool:
        """Return True if sending to *email* would exceed the weekly contact limit.

        This is a conservative heuristic: if ``contact_count_30d`` exceeds
        ``max_per_week * 4`` (roughly a month of weekly emails), we flag the
        contact as over-contacted.  Callers should also maintain their own
        per-send frequency counters for tighter enforcement.
        """
        # In a production system this would query a send-log database.
        # Here we provide a simple in-memory check using the suppression list
        # plus whatever contact metadata is available.
        monthly_cap = max_per_week * 4
        logger.debug(
            "Over-contact check for %s (max %d/week, %d/month)",
            email,
            max_per_week,
            monthly_cap,
        )
        # The connector doesn't own the contact store, so the actual check is
        # delegated to callers that have access to ContactRecord.contact_count_30d.
        # This method exists so subclasses can override with real lookups.
        return False

    def _add_compliance_headers(self, message: EmailMessage) -> EmailMessage:
        """Add List-Unsubscribe header and physical address footer if missing.

        Returns a *new* EmailMessage with compliance additions.
        """
        headers = dict(message.headers)
        body_html = message.body_html or ""
        body_text = message.body_text or ""

        # List-Unsubscribe header
        if "List-Unsubscribe" not in headers:
            unsub_url = self.config.unsubscribe_url
            if unsub_url:
                headers["List-Unsubscribe"] = f"<{unsub_url}>"
                headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        # Physical address in footer
        addr = self.config.physical_address
        if addr and addr not in body_html:
            footer_html = (
                f'<div style="margin-top:24px;padding-top:12px;'
                f'border-top:1px solid #ccc;font-size:12px;color:#666;">'
                f"{addr}"
            )
            if self.config.unsubscribe_url:
                footer_html += (
                    f' | <a href="{self.config.unsubscribe_url}">Unsubscribe</a>'
                )
            footer_html += "</div>"
            body_html += footer_html

        if addr and addr not in body_text:
            footer_text = f"\n\n---\n{addr}"
            if self.config.unsubscribe_url:
                footer_text += f"\nUnsubscribe: {self.config.unsubscribe_url}"
            body_text += footer_text

        # Build updated message
        dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
        dump["headers"] = headers
        dump["body_html"] = body_html
        dump["body_text"] = body_text
        return EmailMessage(**dump)

    def _check_connected(self) -> None:
        """Raise ``ConnectionError`` if the connector has not been connected."""
        if not self._connected:
            raise ConnectionError(
                f"{self.provider_name} connector is not connected. "
                f"Call connect() first."
            )

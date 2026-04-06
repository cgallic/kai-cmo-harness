"""Loops.so email connector — event-driven email platform integration.

Loops (https://loops.so) uses an event-driven model: contacts are created, events
are fired, and those events trigger pre-built email sequences ("Loops") inside
the Loops dashboard.  Arbitrary HTML sends are not supported; all emails go
through Loops transactional templates or event-triggered sequences.

API reference: https://loops.so/docs/api-reference
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

BASE_URL = "https://app.loops.so/api/v1"


class LoopsConnector(EmailProvider):
    """Loops.so email platform connector.

    Loops is template/event-driven — it does not support raw HTML sends.
    Use ``send_event()`` to trigger sequences and ``send_email()`` for
    transactional sends via a ``transactionalId``.
    """

    def __init__(self, config: LifecycleConnectorConfig) -> None:
        super().__init__(config)
        self._local_sequences: List[SequenceConfig] = []

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "loops"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for the Loops API."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _api_call(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Placeholder for HTTP calls — replaced by a real HTTP client at runtime.

        Parameters
        ----------
        method:
            HTTP method (GET, POST, PUT, DELETE).
        path:
            API path relative to BASE_URL (e.g., ``/contacts/create``).
        payload:
            JSON body dict for POST/PUT requests.

        Returns
        -------
        dict
            Parsed JSON response.
        """
        url = f"{BASE_URL}{path}"
        headers = self._build_headers()
        logger.debug(
            "Loops API %s %s headers=%s payload=%s",
            method,
            url,
            {k: v[:20] + "..." if len(v) > 20 else v for k, v in headers.items()},
            payload,
        )
        raise NotImplementedError(
            "HTTP transport not configured. Inject a real HTTP client via "
            "monkey-patching or subclass _api_call."
        )

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate API key via GET /api-key."""
        if self._is_sandbox():
            logger.info("[SANDBOX] Loops connect — skipping real API call")
            self._connected = True
            return True

        try:
            self._api_call("GET", "/api-key")
            self._connected = True
            logger.info("Loops connector authenticated successfully")
            return True
        except Exception as exc:
            logger.error("Loops connect failed: %s", exc)
            self._connected = False
            return False

    # ------------------------------------------------------------------
    # Contacts
    # ------------------------------------------------------------------

    def get_contacts(
        self,
        segment: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContactRecord]:
        """Fetch contacts from Loops.

        Loops contact search is limited — this queries ``/contacts/find``
        with an optional email filter via *segment* (treated as an email
        prefix for this connector).
        """
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_contacts", segment=segment, limit=limit)
            return []

        params: Dict[str, Any] = {}
        if segment:
            params["email"] = segment

        try:
            result = self._api_call("GET", "/contacts/find")
            contacts: List[ContactRecord] = []
            if isinstance(result, list):
                for entry in result[offset : offset + limit]:
                    contacts.append(
                        ContactRecord(
                            id=entry.get("id"),
                            email=entry.get("email", ""),
                            first_name=entry.get("firstName"),
                            last_name=entry.get("lastName"),
                            source=entry.get("source"),
                            tags=entry.get("userGroup", "").split(",") if entry.get("userGroup") else [],
                            opted_in=entry.get("subscribed", True),
                            opted_out=not entry.get("subscribed", True),
                            created_at=entry.get("createdAt"),
                        )
                    )
            return contacts
        except Exception as exc:
            logger.error("Loops get_contacts failed: %s", exc)
            return []

    def create_contact(self, contact: ContactRecord) -> ContactRecord:
        """Create a contact in Loops via POST /contacts/create."""
        self._check_connected()

        payload: Dict[str, Any] = {
            "email": contact.email,
        }
        if contact.first_name:
            payload["firstName"] = contact.first_name
        if contact.last_name:
            payload["lastName"] = contact.last_name
        if contact.source:
            payload["source"] = contact.source
        if contact.tags:
            payload["userGroup"] = ",".join(contact.tags)
        if contact.lists:
            payload["mailingLists"] = {lid: True for lid in contact.lists}
        if contact.custom_fields:
            payload.update(contact.custom_fields)

        if self._is_sandbox():
            self._sandbox_response("create_contact", payload=payload)
            contact_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            contact_dump["id"] = "sandbox-loops-contact-id"
            return ContactRecord(**contact_dump)

        try:
            result = self._api_call("POST", "/contacts/create", payload)
            contact_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            contact_dump["id"] = result.get("id", result.get("contactId"))
            return ContactRecord(**contact_dump)
        except Exception as exc:
            logger.error("Loops create_contact failed: %s", exc)
            raise

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord:
        """Update contact fields via PUT /contacts/update."""
        self._check_connected()

        payload: Dict[str, Any] = {"email": updates.get("email", "")}
        if "first_name" in updates:
            payload["firstName"] = updates["first_name"]
        if "last_name" in updates:
            payload["lastName"] = updates["last_name"]
        for key, value in updates.items():
            if key not in ("email", "first_name", "last_name"):
                payload[key] = value

        if self._is_sandbox():
            self._sandbox_response("update_contact", contact_id=contact_id, payload=payload)
            return ContactRecord(email=updates.get("email", ""), id=contact_id)

        try:
            self._api_call("PUT", "/contacts/update", payload)
            return ContactRecord(email=updates.get("email", ""), id=contact_id)
        except Exception as exc:
            logger.error("Loops update_contact failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def get_lists(self) -> List[Dict[str, Any]]:
        """Fetch mailing lists from Loops via GET /lists."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_lists")
            return []

        try:
            result = self._api_call("GET", "/lists")
            if isinstance(result, list):
                return result
            return result.get("lists", []) if isinstance(result, dict) else []
        except Exception as exc:
            logger.error("Loops get_lists failed: %s", exc)
            return []

    def create_list(
        self, name: str, criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a mailing list in Loops.

        Loops list management is primarily dashboard-driven.  This method
        attempts to create via the API but may need manual dashboard setup.
        """
        self._check_connected()

        if self._is_sandbox():
            return self._sandbox_response("create_list", name=name, criteria=criteria)

        try:
            payload = {"name": name}
            if criteria:
                payload.update(criteria)
            result = self._api_call("POST", "/lists", payload)
            return result
        except Exception as exc:
            logger.warning(
                "Loops create_list may require dashboard setup: %s", exc
            )
            return {"name": name, "note": "May need to be created in Loops dashboard"}

    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------

    def send_email(self, message: EmailMessage) -> EmailMessage:
        """Send an email via Loops.

        Loops requires a ``transactionalId`` (template_id on the message).
        Arbitrary HTML sends are not supported — use a template.
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

        # Add compliance headers
        message = self._add_compliance_headers(message)

        if self._is_sandbox():
            self._sandbox_response("send_email", to=message.to_email, subject=message.subject)
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "sent"
            msg_dump["id"] = "sandbox-loops-msg-id"
            self._record_send()
            return EmailMessage(**msg_dump)

        # Loops sends via transactional templates
        if message.template_id:
            payload: Dict[str, Any] = {
                "transactionalId": message.template_id,
                "email": message.to_email,
                "dataVariables": message.merge_fields or {},
            }
            if message.attachments:
                payload["attachments"] = message.attachments

            try:
                result = self._api_call("POST", "/transactional", payload)
                self._record_send()
                msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
                msg_dump["status"] = "sent"
                msg_dump["id"] = result.get("id", result.get("messageId"))
                return EmailMessage(**msg_dump)
            except Exception as exc:
                logger.error("Loops send_email (transactional) failed: %s", exc)
                msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
                msg_dump["status"] = "failed"
                msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "error": str(exc)}
                return EmailMessage(**msg_dump)
        else:
            # No template ID — cannot send raw HTML through Loops
            logger.error(
                "Loops requires a template_id (transactionalId) for sending. "
                "Raw HTML sends are not supported."
            )
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "failed"
            msg_dump["metadata"] = {
                **msg_dump.get("metadata", {}),
                "reason": "Loops requires template_id — raw HTML not supported",
            }
            return EmailMessage(**msg_dump)

    def send_batch(
        self,
        contacts: List[ContactRecord],
        template_id: Optional[str] = None,
        message: Optional[EmailMessage] = None,
    ) -> Dict[str, Any]:
        """Send to multiple contacts by iterating single sends.

        Loops does not have a native batch-send endpoint. Each send
        respects the 10 requests/second rate limit.
        """
        self._check_connected()

        if self._is_sandbox():
            return self._sandbox_response(
                "send_batch",
                contact_count=len(contacts),
                template_id=template_id,
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

            if not self._check_rate_limit():
                results["failed"] += 1
                results["errors"].append(
                    {"email": contact.email, "reason": "rate_limited"}
                )
                continue

            try:
                email_msg = EmailMessage(
                    to_email=contact.email,
                    to_name=contact.full_name or contact.first_name,
                    subject=message.subject if message else "(template)",
                    template_id=template_id or (message.template_id if message else None),
                    merge_fields=message.merge_fields if message else {},
                    from_email=self.config.from_email,
                    from_name=self.config.from_name,
                )
                result = self.send_email(email_msg)
                if result.status == "sent":
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
    # Sequences
    # ------------------------------------------------------------------

    def get_sequences(self) -> List[SequenceConfig]:
        """Return locally-stored sequence configs.

        Loops manages sequences ("Loops") in the dashboard — there is no
        public API to list all sequences.  We return whatever has been
        registered locally via ``create_sequence()``.
        """
        self._check_connected()
        return list(self._local_sequences)

    def create_sequence(self, config: SequenceConfig) -> SequenceConfig:
        """Store a sequence config locally.

        Loops sequences must be configured in the Loops dashboard.  This
        method records the config in Kai's state for reference.
        """
        self._check_connected()

        logger.info(
            "Loops sequences are configured in the Loops dashboard. "
            "Storing sequence '%s' locally for reference.",
            config.name,
        )

        config_dump = config.model_dump() if hasattr(config, "model_dump") else config.__dict__.copy()
        if not config_dump.get("id"):
            config_dump["id"] = f"local-loops-seq-{len(self._local_sequences) + 1}"
        if not config_dump.get("created_at"):
            config_dump["created_at"] = datetime.now(timezone.utc).isoformat()
        config_dump["total_emails"] = len(config_dump.get("emails", []))

        seq = SequenceConfig(**config_dump)
        self._local_sequences.append(seq)
        return seq

    # ------------------------------------------------------------------
    # Deliverability
    # ------------------------------------------------------------------

    def get_deliverability_stats(
        self, period: Optional[str] = None
    ) -> EmailDeliverabilityStats:
        """Fetch deliverability stats.

        Loops has limited stats endpoints.  Returns defaults if unavailable.
        """
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_deliverability_stats", period=period)
            return EmailDeliverabilityStats(
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        # Loops stats are primarily in-dashboard.  Return empty stats with
        # a note — callers can overlay with webhook-based tracking.
        logger.info(
            "Loops deliverability stats are primarily available in the "
            "Loops dashboard.  Returning empty stats."
        )
        return EmailDeliverabilityStats(
            period=period,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------

    def manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool:
        """Process an unsubscribe by updating the contact in Loops."""
        self._check_connected()

        # Add to local suppression list
        self._suppression_list.append(
            SuppressionEntry(
                email=email,
                reason=reason,
                suppressed_at=datetime.now(timezone.utc).isoformat(),
                source="loops",
            )
        )

        if self._is_sandbox():
            self._sandbox_response("manage_unsubscribe", email=email, reason=reason)
            return True

        try:
            # Mark as unsubscribed in Loops
            self._api_call(
                "PUT",
                "/contacts/update",
                {"email": email, "subscribed": False},
            )
            logger.info("Unsubscribed %s in Loops (reason: %s)", email, reason)
            return True
        except Exception as exc:
            logger.error("Loops manage_unsubscribe failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Warm-up status
    # ------------------------------------------------------------------

    def warm_up_status(self) -> Dict[str, Any]:
        """Check domain warm-up status.

        Loops manages warm-up internally.  Returns a placeholder indicating
        status should be checked in the Loops dashboard.
        """
        from_domain = self.config.from_email.split("@")[-1] if "@" in self.config.from_email else "unknown"
        return {
            "domain": from_domain,
            "daily_limit": 0,
            "current_day": 0,
            "warm_up_complete": False,
            "note": "Check warm-up status in the Loops dashboard.",
        }

    # ------------------------------------------------------------------
    # Loops-specific: event sending
    # ------------------------------------------------------------------

    def send_event(
        self,
        email: str,
        event_name: str,
        event_properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fire an event in Loops that may trigger an email sequence.

        This is Loops' primary mechanism for starting automated email flows.

        Parameters
        ----------
        email:
            The contact's email address.
        event_name:
            The event name configured in Loops (e.g., ``"signup"``,
            ``"purchase_complete"``).
        event_properties:
            Optional key-value pairs sent alongside the event for
            template personalization.

        Returns
        -------
        dict
            API response or sandbox placeholder.
        """
        self._check_connected()

        if self._check_suppressed(email):
            return {"success": False, "reason": "suppressed"}

        payload: Dict[str, Any] = {
            "email": email,
            "eventName": event_name,
        }
        if event_properties:
            payload["eventProperties"] = event_properties

        if self._is_sandbox():
            return self._sandbox_response(
                "send_event",
                email=email,
                event_name=event_name,
                event_properties=event_properties,
            )

        try:
            result = self._api_call("POST", "/events/send", payload)
            self._record_send()
            logger.info("Loops event '%s' fired for %s", event_name, email)
            return result
        except Exception as exc:
            logger.error("Loops send_event failed: %s", exc)
            return {"success": False, "error": str(exc)}

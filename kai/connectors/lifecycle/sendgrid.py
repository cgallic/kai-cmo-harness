"""SendGrid email connector — SendGrid Web API v3 integration.

SendGrid supports both transactional and marketing email workflows.  The v3
API uses API key authentication with Bearer tokens and supports up to 1000
personalizations (recipients) per ``/mail/send`` call.

API reference: https://docs.sendgrid.com/api-reference
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

BASE_URL = "https://api.sendgrid.com/v3"


class SendGridConnector(EmailProvider):
    """SendGrid Web API v3 connector.

    Supports transactional sends (with dynamic templates), contact management
    via the Marketing API, domain authentication checks, and detailed
    deliverability reporting.
    """

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "sendgrid"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for the SendGrid API."""
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
        """Placeholder for HTTP calls — replaced by a real HTTP client at runtime."""
        url = f"{BASE_URL}{path}"
        headers = self._build_headers()
        logger.debug("SendGrid API %s %s payload=%s", method, url, payload)
        raise NotImplementedError(
            "HTTP transport not configured. Inject a real HTTP client via "
            "monkey-patching or subclass _api_call."
        )

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate API key by checking permissions via GET /scopes."""
        if self._is_sandbox():
            logger.info("[SANDBOX] SendGrid connect — skipping real API call")
            self._connected = True
            return True

        try:
            result = self._api_call("GET", "/scopes")
            scopes = result.get("scopes", [])
            logger.info(
                "SendGrid connector authenticated with %d scopes", len(scopes)
            )
            self._connected = True
            return True
        except Exception as exc:
            logger.error("SendGrid connect failed: %s", exc)
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
        """Fetch contacts from the SendGrid Marketing API.

        If *segment* is provided, it is treated as an SGQL query string
        for ``/marketing/contacts/search``.  Otherwise, fetches all
        contacts via ``/marketing/contacts``.
        """
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_contacts", segment=segment, limit=limit)
            return []

        try:
            if segment:
                result = self._api_call(
                    "POST",
                    "/marketing/contacts/search",
                    {"query": segment},
                )
            else:
                result = self._api_call("GET", "/marketing/contacts")

            contacts: List[ContactRecord] = []
            contact_list = result.get("result", result.get("contacts", []))
            if isinstance(contact_list, list):
                for entry in contact_list[offset : offset + limit]:
                    contacts.append(
                        ContactRecord(
                            id=entry.get("id"),
                            email=entry.get("email", ""),
                            first_name=entry.get("first_name"),
                            last_name=entry.get("last_name"),
                            phone=entry.get("phone_number"),
                            source=entry.get("source"),
                            lists=entry.get("list_ids", []),
                            custom_fields=entry.get("custom_fields", {}),
                            created_at=entry.get("created_at"),
                        )
                    )
            return contacts
        except Exception as exc:
            logger.error("SendGrid get_contacts failed: %s", exc)
            return []

    def create_contact(self, contact: ContactRecord) -> ContactRecord:
        """Create (upsert) a contact via PUT /marketing/contacts."""
        self._check_connected()

        contact_data: Dict[str, Any] = {
            "email": contact.email,
        }
        if contact.first_name:
            contact_data["first_name"] = contact.first_name
        if contact.last_name:
            contact_data["last_name"] = contact.last_name
        if contact.phone:
            contact_data["phone_number"] = contact.phone
        if contact.custom_fields:
            contact_data["custom_fields"] = contact.custom_fields

        payload: Dict[str, Any] = {
            "contacts": [contact_data],
        }
        if contact.lists:
            payload["list_ids"] = contact.lists

        if self._is_sandbox():
            self._sandbox_response("create_contact", payload=payload)
            c_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            c_dump["id"] = "sandbox-sg-contact-id"
            return ContactRecord(**c_dump)

        try:
            result = self._api_call("PUT", "/marketing/contacts", payload)
            c_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            c_dump["id"] = result.get("job_id", "pending")
            return ContactRecord(**c_dump)
        except Exception as exc:
            logger.error("SendGrid create_contact failed: %s", exc)
            raise

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord:
        """Update a contact by upserting via PUT /marketing/contacts."""
        self._check_connected()

        contact_data: Dict[str, Any] = {}
        if "email" in updates:
            contact_data["email"] = updates["email"]
        if "first_name" in updates:
            contact_data["first_name"] = updates["first_name"]
        if "last_name" in updates:
            contact_data["last_name"] = updates["last_name"]
        if "phone" in updates:
            contact_data["phone_number"] = updates["phone"]
        custom = {k: v for k, v in updates.items() if k not in ("email", "first_name", "last_name", "phone")}
        if custom:
            contact_data["custom_fields"] = custom

        payload: Dict[str, Any] = {"contacts": [contact_data]}

        if self._is_sandbox():
            self._sandbox_response("update_contact", contact_id=contact_id, payload=payload)
            return ContactRecord(email=updates.get("email", ""), id=contact_id)

        try:
            self._api_call("PUT", "/marketing/contacts", payload)
            return ContactRecord(email=updates.get("email", ""), id=contact_id)
        except Exception as exc:
            logger.error("SendGrid update_contact failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def get_lists(self) -> List[Dict[str, Any]]:
        """Fetch contact lists via GET /marketing/lists."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_lists")
            return []

        try:
            result = self._api_call("GET", "/marketing/lists")
            return result.get("result", [])
        except Exception as exc:
            logger.error("SendGrid get_lists failed: %s", exc)
            return []

    def create_list(
        self, name: str, criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a contact list via POST /marketing/lists."""
        self._check_connected()

        payload: Dict[str, Any] = {"name": name}
        if criteria:
            payload.update(criteria)

        if self._is_sandbox():
            return self._sandbox_response("create_list", name=name)

        try:
            result = self._api_call("POST", "/marketing/lists", payload)
            return result
        except Exception as exc:
            logger.error("SendGrid create_list failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------

    def send_email(self, message: EmailMessage) -> EmailMessage:
        """Send an email via POST /mail/send.

        Supports both direct HTML content and dynamic templates (via
        ``template_id`` and ``merge_fields``).
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

        message = self._add_compliance_headers(message)

        if self._is_sandbox():
            self._sandbox_response("send_email", to=message.to_email, subject=message.subject)
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "sent"
            msg_dump["id"] = "sandbox-sg-msg-id"
            self._record_send()
            return EmailMessage(**msg_dump)

        # Build SendGrid payload
        effective_from = message.from_email or self.config.from_email
        effective_from_name = message.from_name or self.config.from_name

        personalization: Dict[str, Any] = {
            "to": [{"email": message.to_email}],
        }
        if message.to_name:
            personalization["to"][0]["name"] = message.to_name
        if message.merge_fields:
            personalization["dynamic_template_data"] = message.merge_fields
        if message.send_at:
            personalization["send_at"] = message.send_at

        payload: Dict[str, Any] = {
            "personalizations": [personalization],
            "from": {
                "email": effective_from,
                "name": effective_from_name,
            },
            "subject": message.subject,
        }

        # Reply-to
        reply_to = message.reply_to or self.config.reply_to
        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        # Content
        if message.template_id:
            payload["template_id"] = message.template_id
        else:
            content: List[Dict[str, str]] = []
            if message.body_text:
                content.append({"type": "text/plain", "value": message.body_text})
            if message.body_html:
                content.append({"type": "text/html", "value": message.body_html})
            if not content:
                content.append({"type": "text/plain", "value": ""})
            payload["content"] = content

        # Headers (including List-Unsubscribe)
        if message.headers:
            payload["headers"] = message.headers

        # Tags / categories
        if message.tags:
            payload["categories"] = message.tags

        # Attachments
        if message.attachments:
            payload["attachments"] = [
                {
                    "content": att.get("data", ""),
                    "type": att.get("content_type", "application/octet-stream"),
                    "filename": att.get("filename", "attachment"),
                    "disposition": "attachment",
                }
                for att in message.attachments
            ]

        try:
            result = self._api_call("POST", "/mail/send", payload)
            self._record_send()
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "sent"
            msg_dump["id"] = result.get("x-message-id") if isinstance(result, dict) else None
            return EmailMessage(**msg_dump)
        except Exception as exc:
            logger.error("SendGrid send_email failed: %s", exc)
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "failed"
            msg_dump["metadata"] = {**msg_dump.get("metadata", {}), "error": str(exc)}
            return EmailMessage(**msg_dump)

    def send_batch(
        self,
        contacts: List[ContactRecord],
        template_id: Optional[str] = None,
        message: Optional[EmailMessage] = None,
    ) -> Dict[str, Any]:
        """Send to multiple contacts using SendGrid personalizations.

        SendGrid supports up to 1000 personalizations per API call.
        Contacts are batched into groups of 1000 for efficiency.
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
            "batches": 0,
        }

        # Filter out suppressed contacts
        eligible: List[ContactRecord] = []
        for contact in contacts:
            if self._check_suppressed(contact.email):
                results["skipped"] += 1
            else:
                eligible.append(contact)

        # Batch into groups of 1000
        batch_size = 1000
        for i in range(0, len(eligible), batch_size):
            batch = eligible[i : i + batch_size]
            results["batches"] += 1

            if not self._check_rate_limit():
                results["failed"] += len(batch)
                for c in batch:
                    results["errors"].append(
                        {"email": c.email, "reason": "rate_limited"}
                    )
                continue

            personalizations: List[Dict[str, Any]] = []
            for contact in batch:
                p: Dict[str, Any] = {
                    "to": [{"email": contact.email}],
                }
                if contact.full_name or contact.first_name:
                    p["to"][0]["name"] = contact.full_name or contact.first_name
                if message and message.merge_fields:
                    # Inject contact-specific merge fields
                    fields = dict(message.merge_fields)
                    if contact.first_name:
                        fields.setdefault("first_name", contact.first_name)
                    if contact.last_name:
                        fields.setdefault("last_name", contact.last_name)
                    p["dynamic_template_data"] = fields
                personalizations.append(p)

            effective_from = self.config.from_email
            if message and message.from_email:
                effective_from = message.from_email

            payload: Dict[str, Any] = {
                "personalizations": personalizations,
                "from": {
                    "email": effective_from,
                    "name": self.config.from_name,
                },
                "subject": message.subject if message else "(no subject)",
            }

            if template_id or (message and message.template_id):
                payload["template_id"] = template_id or message.template_id
            elif message:
                content: List[Dict[str, str]] = []
                if message.body_text:
                    content.append({"type": "text/plain", "value": message.body_text})
                if message.body_html:
                    content.append({"type": "text/html", "value": message.body_html})
                payload["content"] = content or [{"type": "text/plain", "value": ""}]

            try:
                self._api_call("POST", "/mail/send", payload)
                self._record_send()
                results["sent"] += len(batch)
            except Exception as exc:
                results["failed"] += len(batch)
                results["errors"].append(
                    {"batch": i // batch_size, "reason": str(exc)}
                )

        return results

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------

    def get_sequences(self) -> List[SequenceConfig]:
        """SendGrid automations are configured in the dashboard.

        Returns an empty list — automation management via the API is
        limited in SendGrid v3.
        """
        self._check_connected()
        logger.info(
            "SendGrid automations are managed in the dashboard. "
            "Use the Marketing Campaigns UI to configure sequences."
        )
        return []

    def create_sequence(self, config: SequenceConfig) -> SequenceConfig:
        """Store a sequence config locally.

        SendGrid automations (Single Sends / Automations) are best created
        via the dashboard.  This stores the config for reference.
        """
        self._check_connected()

        logger.info(
            "SendGrid automations should be configured in the dashboard. "
            "Storing sequence '%s' locally for reference.",
            config.name,
        )

        config_dump = config.model_dump() if hasattr(config, "model_dump") else config.__dict__.copy()
        if not config_dump.get("id"):
            config_dump["id"] = f"local-sg-seq-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        if not config_dump.get("created_at"):
            config_dump["created_at"] = datetime.now(timezone.utc).isoformat()
        config_dump["total_emails"] = len(config_dump.get("emails", []))
        return SequenceConfig(**config_dump)

    # ------------------------------------------------------------------
    # Deliverability
    # ------------------------------------------------------------------

    def get_deliverability_stats(
        self, period: Optional[str] = None
    ) -> EmailDeliverabilityStats:
        """Fetch deliverability stats from SendGrid.

        Uses GET /stats for aggregate metrics and suppression endpoints
        for bounce/spam/unsubscribe counts.
        """
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_deliverability_stats", period=period)
            return EmailDeliverabilityStats(
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        try:
            # Get aggregate stats
            stats_path = "/stats"
            if period:
                stats_path += f"?start_date={period}"
            result = self._api_call("GET", stats_path)

            total_sent = 0
            total_delivered = 0
            total_opens = 0
            total_clicks = 0
            total_bounces = 0
            total_spam = 0

            for day in result if isinstance(result, list) else []:
                for metric_set in day.get("stats", []):
                    m = metric_set.get("metrics", {})
                    total_sent += m.get("requests", 0)
                    total_delivered += m.get("delivered", 0)
                    total_opens += m.get("unique_opens", 0)
                    total_clicks += m.get("unique_clicks", 0)
                    total_bounces += m.get("bounces", 0)
                    total_spam += m.get("spam_reports", 0)

            # Get suppression counts
            bounce_count = 0
            spam_count = 0
            unsub_count = 0
            try:
                bounces = self._api_call("GET", "/suppression/bounces")
                bounce_count = len(bounces) if isinstance(bounces, list) else 0
            except Exception:
                pass
            try:
                spams = self._api_call("GET", "/suppression/spam_reports")
                spam_count = len(spams) if isinstance(spams, list) else 0
            except Exception:
                pass
            try:
                unsubs = self._api_call("GET", "/suppression/unsubscribes")
                unsub_count = len(unsubs) if isinstance(unsubs, list) else 0
            except Exception:
                pass

            denom = max(total_sent, 1)
            return EmailDeliverabilityStats(
                total_sent=total_sent,
                delivered=total_delivered,
                delivery_rate=total_delivered / denom,
                opened=total_opens,
                open_rate=total_opens / denom,
                clicked=total_clicks,
                click_rate=total_clicks / denom,
                bounced=total_bounces or bounce_count,
                bounce_rate=(total_bounces or bounce_count) / denom,
                spam_complaints=total_spam or spam_count,
                spam_complaint_rate=(total_spam or spam_count) / denom,
                unsubscribes=unsub_count,
                unsubscribe_rate=unsub_count / denom,
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("SendGrid get_deliverability_stats failed: %s", exc)
            return EmailDeliverabilityStats(
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------

    def manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool:
        """Process an unsubscribe in SendGrid.

        Adds to global suppression via POST /asm/suppressions/global.
        """
        self._check_connected()

        self._suppression_list.append(
            SuppressionEntry(
                email=email,
                reason=reason,
                suppressed_at=datetime.now(timezone.utc).isoformat(),
                source="sendgrid",
            )
        )

        if self._is_sandbox():
            self._sandbox_response("manage_unsubscribe", email=email, reason=reason)
            return True

        try:
            self._api_call(
                "POST",
                "/asm/suppressions/global",
                {"recipient_emails": [email]},
            )
            logger.info("Unsubscribed %s in SendGrid (reason: %s)", email, reason)
            return True
        except Exception as exc:
            logger.error("SendGrid manage_unsubscribe failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Warm-up status
    # ------------------------------------------------------------------

    def warm_up_status(self) -> Dict[str, Any]:
        """Check IP warm-up status via SendGrid API."""
        from_domain = self.config.from_email.split("@")[-1] if "@" in self.config.from_email else "unknown"

        if self._is_sandbox():
            return {
                "domain": from_domain,
                "daily_limit": 0,
                "current_day": 0,
                "warm_up_complete": False,
                "note": "Sandbox mode — check warm-up in SendGrid dashboard.",
            }

        try:
            result = self._api_call("GET", "/ips/warmup")
            if isinstance(result, list) and result:
                ip_info = result[0]
                return {
                    "domain": from_domain,
                    "daily_limit": ip_info.get("daily_limit", 0),
                    "current_day": ip_info.get("warmup_day", 0),
                    "warm_up_complete": not bool(result),
                }
            return {
                "domain": from_domain,
                "daily_limit": 0,
                "current_day": 0,
                "warm_up_complete": True,
                "note": "No IPs currently in warm-up.",
            }
        except Exception as exc:
            logger.warning("Could not fetch warm-up status: %s", exc)
            return {
                "domain": from_domain,
                "daily_limit": 0,
                "current_day": 0,
                "warm_up_complete": False,
                "note": f"Could not determine warm-up status: {exc}",
            }

    # ------------------------------------------------------------------
    # SendGrid-specific methods
    # ------------------------------------------------------------------

    def check_domain_authentication(self) -> Dict[str, Any]:
        """Check SPF, DKIM, and DMARC setup via GET /whitelabel/domains.

        Returns
        -------
        dict
            Domain authentication details including validation status for
            SPF, DKIM, and DMARC records.
        """
        self._check_connected()

        if self._is_sandbox():
            return self._sandbox_response("check_domain_authentication")

        try:
            result = self._api_call("GET", "/whitelabel/domains")
            domains: List[Dict[str, Any]] = result if isinstance(result, list) else []

            authenticated: List[Dict[str, Any]] = []
            for domain in domains:
                authenticated.append({
                    "id": domain.get("id"),
                    "domain": domain.get("domain"),
                    "valid": domain.get("valid", False),
                    "dns": domain.get("dns", {}),
                    "default": domain.get("default", False),
                })

            return {
                "domains": authenticated,
                "total": len(authenticated),
                "all_valid": all(d.get("valid", False) for d in authenticated) if authenticated else False,
            }
        except Exception as exc:
            logger.error("SendGrid check_domain_authentication failed: %s", exc)
            return {"domains": [], "total": 0, "all_valid": False, "error": str(exc)}

    def get_bounce_list(self) -> List[Dict[str, Any]]:
        """Fetch bounced email addresses via GET /suppression/bounces.

        Returns
        -------
        list
            List of bounce entries with email, status, reason, and
            timestamp.
        """
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_bounce_list")
            return []

        try:
            result = self._api_call("GET", "/suppression/bounces")
            return result if isinstance(result, list) else []
        except Exception as exc:
            logger.error("SendGrid get_bounce_list failed: %s", exc)
            return []

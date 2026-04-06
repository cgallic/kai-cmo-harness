"""Mailchimp email connector — Mailchimp Marketing API v3 integration.

Mailchimp organizes data around Audiences (lists), Campaigns, and Automations
(Customer Journeys).  The API key encodes the datacenter
(e.g. ``xxxxxxxxxxxxxxxxxxxx-us21``), so the base URL is derived at connect time.

API reference: https://mailchimp.com/developer/marketing/api/
"""

from __future__ import annotations

import hashlib
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

BASE_URL_TEMPLATE = "https://{dc}.api.mailchimp.com/3.0"


class MailchimpConnector(EmailProvider):
    """Mailchimp Marketing API v3 connector.

    Supports audience/list management, campaign creation and sending,
    automation listing, and deliverability reporting.
    """

    def __init__(self, config: LifecycleConnectorConfig) -> None:
        super().__init__(config)
        self._base_url: Optional[str] = None
        self._default_list_id: Optional[str] = config.metadata.get("list_id")

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "mailchimp"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_datacenter(self) -> str:
        """Extract the datacenter slug from the API key.

        Mailchimp API keys look like ``<hex>-us21``.  The part after the
        dash is the datacenter.
        """
        if not self.config.api_key:
            raise ValueError("Mailchimp API key is required")
        parts = self.config.api_key.rsplit("-", 1)
        if len(parts) != 2:
            raise ValueError(
                "Invalid Mailchimp API key format — expected '<key>-<dc>' "
                f"(e.g. 'xxxx-us21'), got '{self.config.api_key[:12]}...'"
            )
        return parts[1]

    def _build_headers(self) -> Dict[str, str]:
        """Return headers with Basic auth for Mailchimp."""
        import base64

        credentials = base64.b64encode(
            f"anystring:{self.config.api_key}".encode()
        ).decode()
        return {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _subscriber_hash(email: str) -> str:
        """Return the MD5 hash of a lowercased email — Mailchimp's member ID."""
        return hashlib.md5(email.strip().lower().encode()).hexdigest()

    def _api_call(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Placeholder for HTTP calls — replaced by a real HTTP client at runtime."""
        url = f"{self._base_url}{path}"
        headers = self._build_headers()
        logger.debug("Mailchimp API %s %s payload=%s", method, url, payload)
        raise NotImplementedError(
            "HTTP transport not configured. Inject a real HTTP client via "
            "monkey-patching or subclass _api_call."
        )

    def _ensure_list_id(self) -> str:
        """Return the default list ID or raise if not configured."""
        if not self._default_list_id:
            raise ValueError(
                "Mailchimp requires a list_id.  Set it in config.metadata['list_id']."
            )
        return self._default_list_id

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Extract datacenter and validate API key via GET /ping."""
        try:
            dc = self._get_datacenter()
            self._base_url = BASE_URL_TEMPLATE.format(dc=dc)
        except ValueError as exc:
            logger.error("Mailchimp connect failed: %s", exc)
            return False

        if self._is_sandbox():
            logger.info("[SANDBOX] Mailchimp connect — dc=%s, skipping ping", dc)
            self._connected = True
            return True

        try:
            self._api_call("GET", "/ping")
            self._connected = True
            logger.info("Mailchimp connector authenticated (dc=%s)", dc)
            return True
        except Exception as exc:
            logger.error("Mailchimp connect failed: %s", exc)
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
        """Fetch members from the default audience/list.

        Parameters
        ----------
        segment:
            Optional list_id override.  If None, uses default list_id.
        limit:
            Max members to return (Mailchimp max 1000).
        offset:
            Pagination offset.
        """
        self._check_connected()
        list_id = segment or self._ensure_list_id()

        if self._is_sandbox():
            self._sandbox_response("get_contacts", list_id=list_id, limit=limit)
            return []

        try:
            result = self._api_call(
                "GET",
                f"/lists/{list_id}/members?count={min(limit, 1000)}&offset={offset}",
            )
            contacts: List[ContactRecord] = []
            for member in result.get("members", []):
                merge = member.get("merge_fields", {})
                contacts.append(
                    ContactRecord(
                        id=member.get("id"),
                        email=member.get("email_address", ""),
                        first_name=merge.get("FNAME"),
                        last_name=merge.get("LNAME"),
                        full_name=member.get("full_name"),
                        source=member.get("source"),
                        tags=[t["name"] for t in member.get("tags", [])],
                        lists=[list_id],
                        opted_in=member.get("status") == "subscribed",
                        opted_out=member.get("status") in ("unsubscribed", "cleaned"),
                        created_at=member.get("timestamp_signup"),
                        custom_fields=merge,
                    )
                )
            return contacts
        except Exception as exc:
            logger.error("Mailchimp get_contacts failed: %s", exc)
            return []

    def create_contact(self, contact: ContactRecord) -> ContactRecord:
        """Add a member to the default audience via POST /lists/{id}/members."""
        self._check_connected()
        list_id = contact.lists[0] if contact.lists else self._ensure_list_id()

        payload: Dict[str, Any] = {
            "email_address": contact.email,
            "status": "subscribed" if contact.opted_in else "unsubscribed",
            "merge_fields": {},
        }
        if contact.first_name:
            payload["merge_fields"]["FNAME"] = contact.first_name
        if contact.last_name:
            payload["merge_fields"]["LNAME"] = contact.last_name
        if contact.custom_fields:
            payload["merge_fields"].update(contact.custom_fields)
        if contact.tags:
            payload["tags"] = contact.tags

        if self._is_sandbox():
            self._sandbox_response("create_contact", payload=payload)
            c_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            c_dump["id"] = f"sandbox-mc-{self._subscriber_hash(contact.email)}"
            return ContactRecord(**c_dump)

        try:
            result = self._api_call("POST", f"/lists/{list_id}/members", payload)
            c_dump = contact.model_dump() if hasattr(contact, "model_dump") else contact.__dict__.copy()
            c_dump["id"] = result.get("id")
            return ContactRecord(**c_dump)
        except Exception as exc:
            logger.error("Mailchimp create_contact failed: %s", exc)
            raise

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord:
        """Update a member via PATCH /lists/{id}/members/{subscriber_hash}."""
        self._check_connected()
        list_id = updates.pop("list_id", None) or self._ensure_list_id()

        # contact_id may be the subscriber hash or email
        sub_hash = contact_id
        if "@" in contact_id:
            sub_hash = self._subscriber_hash(contact_id)

        payload: Dict[str, Any] = {}
        merge_updates: Dict[str, Any] = {}
        if "first_name" in updates:
            merge_updates["FNAME"] = updates.pop("first_name")
        if "last_name" in updates:
            merge_updates["LNAME"] = updates.pop("last_name")
        if merge_updates:
            payload["merge_fields"] = merge_updates
        if "tags" in updates:
            payload["tags"] = updates.pop("tags")
        if "status" in updates:
            payload["status"] = updates.pop("status")
        # Remaining fields go into merge_fields
        if updates:
            payload.setdefault("merge_fields", {}).update(updates)

        if self._is_sandbox():
            self._sandbox_response("update_contact", contact_id=contact_id, payload=payload)
            return ContactRecord(email=contact_id if "@" in contact_id else "", id=sub_hash)

        try:
            self._api_call("PATCH", f"/lists/{list_id}/members/{sub_hash}", payload)
            return ContactRecord(email=contact_id if "@" in contact_id else "", id=sub_hash)
        except Exception as exc:
            logger.error("Mailchimp update_contact failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------

    def get_lists(self) -> List[Dict[str, Any]]:
        """Fetch audiences via GET /lists."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_lists")
            return []

        try:
            result = self._api_call("GET", "/lists")
            return result.get("lists", [])
        except Exception as exc:
            logger.error("Mailchimp get_lists failed: %s", exc)
            return []

    def create_list(
        self, name: str, criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new audience via POST /lists."""
        self._check_connected()

        payload: Dict[str, Any] = {
            "name": name,
            "contact": {
                "company": self.config.from_name,
                "address1": self.config.physical_address,
                "city": "",
                "state": "",
                "zip": "",
                "country": "US",
            },
            "permission_reminder": "You signed up for updates from us.",
            "campaign_defaults": {
                "from_name": self.config.from_name,
                "from_email": self.config.from_email,
                "subject": "",
                "language": "en",
            },
            "email_type_option": True,
        }
        if criteria:
            payload.update(criteria)

        if self._is_sandbox():
            return self._sandbox_response("create_list", name=name)

        try:
            result = self._api_call("POST", "/lists", payload)
            return result
        except Exception as exc:
            logger.error("Mailchimp create_list failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Email sending
    # ------------------------------------------------------------------

    def send_email(self, message: EmailMessage) -> EmailMessage:
        """Send an email via Mailchimp campaign workflow.

        Mailchimp workflow: create campaign -> set content -> send.
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
            msg_dump["id"] = "sandbox-mc-campaign-id"
            self._record_send()
            return EmailMessage(**msg_dump)

        list_id = self._ensure_list_id()

        try:
            # Step 1: Create campaign
            campaign_payload: Dict[str, Any] = {
                "type": "regular",
                "recipients": {"list_id": list_id},
                "settings": {
                    "subject_line": message.subject,
                    "from_name": message.from_name or self.config.from_name,
                    "reply_to": message.reply_to or self.config.reply_to or self.config.from_email,
                },
            }
            campaign = self._api_call("POST", "/campaigns", campaign_payload)
            campaign_id = campaign.get("id")

            # Step 2: Set content
            content_payload: Dict[str, Any] = {}
            if message.template_id:
                content_payload["template"] = {"id": int(message.template_id)}
            else:
                content_payload["html"] = message.body_html or message.body_text or ""
            self._api_call("PUT", f"/campaigns/{campaign_id}/content", content_payload)

            # Step 3: Send campaign
            self._api_call("POST", f"/campaigns/{campaign_id}/actions/send")

            self._record_send()
            msg_dump = message.model_dump() if hasattr(message, "model_dump") else message.__dict__.copy()
            msg_dump["status"] = "sent"
            msg_dump["id"] = campaign_id
            return EmailMessage(**msg_dump)
        except Exception as exc:
            logger.error("Mailchimp send_email failed: %s", exc)
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
        """Send to a list of contacts using a Mailchimp campaign.

        For batch sends, Mailchimp uses campaigns targeted at list segments.
        This method creates or updates tags on contacts, then triggers a
        campaign to that segment.
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
                    subject=message.subject if message else "(no subject)",
                    body_html=message.body_html if message else None,
                    body_text=message.body_text if message else None,
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
    # Sequences (Automations)
    # ------------------------------------------------------------------

    def get_sequences(self) -> List[SequenceConfig]:
        """Fetch automations via GET /automations."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_sequences")
            return []

        try:
            result = self._api_call("GET", "/automations")
            sequences: List[SequenceConfig] = []
            for auto in result.get("automations", []):
                sequences.append(
                    SequenceConfig(
                        id=auto.get("id"),
                        name=auto.get("settings", {}).get("title", "Untitled"),
                        description=auto.get("settings", {}).get("subject_line"),
                        trigger_event=auto.get("trigger_settings", {}).get("workflow_type"),
                        status=auto.get("status", "draft"),
                        total_emails=auto.get("emails_sent", 0),
                        created_at=auto.get("create_time"),
                    )
                )
            return sequences
        except Exception as exc:
            logger.error("Mailchimp get_sequences failed: %s", exc)
            return []

    def create_sequence(self, config: SequenceConfig) -> SequenceConfig:
        """Create an automation — Mailchimp automations are typically
        created in the dashboard.  This stores locally and logs a note.
        """
        self._check_connected()

        logger.info(
            "Mailchimp automations/Customer Journeys are best configured "
            "in the Mailchimp dashboard.  Storing sequence '%s' locally.",
            config.name,
        )

        config_dump = config.model_dump() if hasattr(config, "model_dump") else config.__dict__.copy()
        if not config_dump.get("id"):
            config_dump["id"] = f"local-mc-seq-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
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
        """Aggregate deliverability stats from campaign reports."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_deliverability_stats", period=period)
            return EmailDeliverabilityStats(
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        try:
            result = self._api_call("GET", "/reports")
            reports = result.get("reports", [])

            total_sent = 0
            total_opens = 0
            total_clicks = 0
            total_bounces = 0
            total_unsubs = 0

            for report in reports:
                total_sent += report.get("emails_sent", 0)
                opens = report.get("opens", {})
                total_opens += opens.get("opens_total", 0)
                clicks = report.get("clicks", {})
                total_clicks += clicks.get("clicks_total", 0)
                bounces = report.get("bounces", {})
                total_bounces += bounces.get("hard_bounces", 0) + bounces.get("soft_bounces", 0)
                total_unsubs += report.get("unsubscribed", 0)

            return EmailDeliverabilityStats(
                total_sent=total_sent,
                delivered=total_sent - total_bounces,
                delivery_rate=(total_sent - total_bounces) / max(total_sent, 1),
                opened=total_opens,
                open_rate=total_opens / max(total_sent, 1),
                clicked=total_clicks,
                click_rate=total_clicks / max(total_sent, 1),
                bounced=total_bounces,
                bounce_rate=total_bounces / max(total_sent, 1),
                unsubscribes=total_unsubs,
                unsubscribe_rate=total_unsubs / max(total_sent, 1),
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("Mailchimp get_deliverability_stats failed: %s", exc)
            return EmailDeliverabilityStats(
                period=period,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------

    def manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool:
        """Unsubscribe a member in Mailchimp."""
        self._check_connected()

        self._suppression_list.append(
            SuppressionEntry(
                email=email,
                reason=reason,
                suppressed_at=datetime.now(timezone.utc).isoformat(),
                source="mailchimp",
            )
        )

        if self._is_sandbox():
            self._sandbox_response("manage_unsubscribe", email=email, reason=reason)
            return True

        list_id = self._ensure_list_id()
        sub_hash = self._subscriber_hash(email)

        try:
            self._api_call(
                "PATCH",
                f"/lists/{list_id}/members/{sub_hash}",
                {"status": "unsubscribed"},
            )
            logger.info("Unsubscribed %s in Mailchimp (reason: %s)", email, reason)
            return True
        except Exception as exc:
            logger.error("Mailchimp manage_unsubscribe failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Warm-up status
    # ------------------------------------------------------------------

    def warm_up_status(self) -> Dict[str, Any]:
        """Mailchimp manages IP and domain reputation internally."""
        from_domain = self.config.from_email.split("@")[-1] if "@" in self.config.from_email else "unknown"
        return {
            "domain": from_domain,
            "daily_limit": 0,
            "current_day": 0,
            "warm_up_complete": False,
            "note": "Mailchimp manages shared IP warm-up automatically. "
                    "Dedicated IP warm-up is configured in the Mailchimp dashboard.",
        }

    # ------------------------------------------------------------------
    # Mailchimp-specific methods
    # ------------------------------------------------------------------

    def get_audiences(self) -> List[Dict[str, Any]]:
        """Fetch all audiences (lists) via GET /lists.

        This is Mailchimp-specific — ``get_lists()`` returns the same data
        but ``get_audiences`` is the Mailchimp-native naming.
        """
        return self.get_lists()

    def get_segments(self, list_id: str) -> List[Dict[str, Any]]:
        """Fetch segments for a specific audience via GET /lists/{id}/segments."""
        self._check_connected()

        if self._is_sandbox():
            self._sandbox_response("get_segments", list_id=list_id)
            return []

        try:
            result = self._api_call("GET", f"/lists/{list_id}/segments")
            return result.get("segments", [])
        except Exception as exc:
            logger.error("Mailchimp get_segments failed: %s", exc)
            return []

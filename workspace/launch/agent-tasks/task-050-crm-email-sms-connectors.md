# Task 050: Build email/SMS/CRM connector layer

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

The Kai Marketing OS needs to send emails, manage contacts, and trigger automated sequences across different email/CRM providers. Before any lifecycle action (Task 051), contact segmentation (Task 052), or sequence building (Task 055) can work, there must be a uniform connector layer that abstracts each email/CRM provider's API into a common interface. This is the foundation of Workstream 9 — it handles the plumbing of actually delivering messages and managing contact data, while upstream modules handle the strategy and content.

The harness references Loops.so as the default email provider, but the system must support Mailchimp, SendGrid, generic SMTP, and stub connectors for SMS and CRM as well. Every connector enforces opt-out handling and CAN-SPAM compliance at the connector level.

## Scope

Create the `kai/connectors/lifecycle/` package with a base abstract connector, email provider implementations (Loops, Mailchimp, SendGrid, generic SMTP), an SMS base connector, and a CRM base connector.

## Detailed Requirements

### File: `kai/connectors/lifecycle/__init__.py`

- Module docstring: "Lifecycle connectors — email, SMS, and CRM integrations for contact management, sequence execution, and deliverability tracking."
- Import and re-export all connector classes
- Export `LIFECYCLE_REGISTRY: Dict[str, Type[LifecycleConnector]]` mapping provider name to connector class
- Export `get_lifecycle_connector(provider: str, config: dict) -> LifecycleConnector` factory function
- `__all__` listing

### File: `kai/connectors/lifecycle/base.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`. Use `abc.ABC` and `abc.abstractmethod`.

**Model: LifecycleConnectorConfig**
- `provider: str` — provider name (loops, mailchimp, sendgrid, smtp, twilio)
- `api_key: Optional[str]`
- `api_secret: Optional[str]`
- `access_token: Optional[str]`
- `from_email: str` — default sending email address
- `from_name: str` — default sender name
- `reply_to: Optional[str]` — reply-to address
- `physical_address: str` — CAN-SPAM required physical mailing address
- `sandbox_mode: bool = True` — no real sends in sandbox
- `rate_limit_per_second: float = 10.0` — sends per second cap
- `rate_limit_per_hour: int = 1000` — sends per hour cap
- `unsubscribe_url: Optional[str]` — custom unsubscribe URL
- `metadata: Dict[str, Any]` — default empty dict

**Model: EmailMessage**
- `id: Optional[str]` — provider-assigned message ID (None before send)
- `to_email: str`
- `to_name: Optional[str]`
- `from_email: Optional[str]` — override default sender
- `from_name: Optional[str]` — override default sender name
- `reply_to: Optional[str]`
- `subject: str`
- `body_html: Optional[str]` — HTML body
- `body_text: Optional[str]` — plain text body (fallback)
- `template_id: Optional[str]` — provider template ID (if using provider templates)
- `merge_fields: Dict[str, str]` — personalization variables, default empty dict
- `tags: List[str]` — message tags for tracking, default empty list
- `headers: Dict[str, str]` — custom email headers, default empty dict
- `attachments: List[Dict[str, Any]]` — list of {filename, content_type, data}, default empty list
- `send_at: Optional[str]` — ISO timestamp for scheduled send
- `status: str` — "draft", "queued", "sent", "delivered", "bounced", "failed", "opened", "clicked", default "draft"
- `metadata: Dict[str, Any]` — default empty dict

**Model: EmailDeliverabilityStats**
- `total_sent: int = 0`
- `delivered: int = 0`
- `delivery_rate: float = 0.0`
- `opened: int = 0`
- `open_rate: float = 0.0`
- `clicked: int = 0`
- `click_rate: float = 0.0`
- `bounced: int = 0`
- `bounce_rate: float = 0.0`
- `soft_bounces: int = 0`
- `hard_bounces: int = 0`
- `spam_complaints: int = 0`
- `spam_complaint_rate: float = 0.0`
- `unsubscribes: int = 0`
- `unsubscribe_rate: float = 0.0`
- `period: Optional[str]` — time period for these stats
- `fetched_at: Optional[str]`

**Model: ContactRecord**
- `id: Optional[str]` — provider-assigned contact ID
- `email: str`
- `phone: Optional[str]`
- `first_name: Optional[str]`
- `last_name: Optional[str]`
- `full_name: Optional[str]`
- `source: Optional[str]` — how this contact was acquired
- `tags: List[str]` — default empty list
- `lists: List[str]` — list/segment IDs this contact belongs to, default empty list
- `custom_fields: Dict[str, Any]` — default empty dict
- `opted_in: bool = True`
- `opt_in_date: Optional[str]`
- `opted_out: bool = False`
- `opt_out_date: Optional[str]`
- `created_at: Optional[str]`
- `last_contacted: Optional[str]`
- `contact_count_30d: int = 0` — how many messages sent in last 30 days
- `metadata: Dict[str, Any]` — default empty dict

**Model: SequenceConfig**
- `id: Optional[str]`
- `name: str`
- `description: Optional[str]`
- `trigger_event: Optional[str]` — what triggers the sequence (e.g., "form_submit", "purchase", "manual")
- `emails: List[Dict[str, Any]]` — list of {delay_days: int, delay_hours: int, subject: str, body_html: str, body_text: str}, default empty list
- `status: str` — "draft", "active", "paused", "completed", default "draft"
- `total_emails: int = 0`
- `created_at: Optional[str]`

**Model: SuppressionEntry**
- `email: str`
- `reason: str` — "unsubscribe", "hard_bounce", "spam_complaint", "manual"
- `suppressed_at: str` — ISO timestamp
- `source: Optional[str]` — which system added the suppression

**Abstract class: LifecycleConnector(ABC)**

- `__init__(self, config: LifecycleConnectorConfig)` — store config, initialize `_connected: bool = False`, `_suppression_list: List[SuppressionEntry]`
- `provider_name: str` — abstract property

Abstract methods:
- `connect(self) -> bool` — validate credentials, test connection
- `get_contacts(self, segment: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[ContactRecord]` — fetch contacts
- `create_contact(self, contact: ContactRecord) -> ContactRecord` — create a new contact
- `update_contact(self, contact_id: str, updates: Dict[str, Any]) -> ContactRecord` — update contact fields
- `get_lists(self) -> List[Dict[str, Any]]` — fetch mailing lists/segments
- `create_list(self, name: str, criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]` — create a mailing list
- `send_email(self, message: EmailMessage) -> EmailMessage` — send a single email, return with updated status and id
- `send_batch(self, contacts: List[ContactRecord], template_id: Optional[str] = None, message: Optional[EmailMessage] = None) -> Dict[str, Any]` — send to multiple contacts
- `get_sequences(self) -> List[SequenceConfig]` — fetch configured sequences
- `create_sequence(self, config: SequenceConfig) -> SequenceConfig` — create an email sequence
- `get_deliverability_stats(self, period: Optional[str] = None) -> EmailDeliverabilityStats` — fetch deliverability metrics
- `manage_unsubscribe(self, email: str, reason: str = "unsubscribe") -> bool` — process an unsubscribe request

Concrete helper methods (not abstract):
- `_is_sandbox(self) -> bool`
- `_sandbox_response(self, method_name: str, **kwargs) -> Dict[str, Any]`
- `_check_rate_limit(self) -> bool`
- `_record_send(self)`
- `_check_suppressed(self, email: str) -> bool` — check if email is on suppression list. Return True if suppressed.
- `_validate_can_spam(self, message: EmailMessage) -> List[str]` — validate CAN-SPAM compliance:
  1. Check from_email is set
  2. Check physical_address is in config
  3. Check unsubscribe URL or header is present
  4. Check subject is not misleading (not empty, not all caps)
  5. Return list of violation strings (empty = compliant)
- `_check_over_contact(self, email: str, max_per_week: int = 3) -> bool` — check if sending to this email would exceed weekly contact limit. Return True if over limit.
- `_add_compliance_headers(self, message: EmailMessage) -> EmailMessage` — add List-Unsubscribe header, add physical address to footer if not present
- `_check_connected(self)` — raise ConnectionError if not connected

### File: `kai/connectors/lifecycle/email_base.py`

**Abstract class: EmailProvider(LifecycleConnector)**

Additional email-specific methods (extending LifecycleConnector):
- `send_single(self, to: str, subject: str, body_html: str, body_text: Optional[str] = None, from_email: Optional[str] = None) -> EmailMessage` — convenience method wrapping send_email
- `send_transactional(self, to: str, template_id: str, merge_fields: Dict[str, str]) -> EmailMessage` — send a transactional email using a provider template
- `get_open_rate(self, campaign_id: Optional[str] = None) -> float` — get open rate for a campaign or overall
- `get_click_rate(self, campaign_id: Optional[str] = None) -> float` — get click rate
- `warm_up_status(self) -> Dict[str, Any]` — check domain warm-up status: `{"domain": str, "daily_limit": int, "current_day": int, "warm_up_complete": bool}`

### File: `kai/connectors/lifecycle/loops.py`

**Class: LoopsConnector(EmailProvider)**

- `provider_name` returns `"loops"`
- API base: `BASE_URL = "https://app.loops.so/api/v1"`
- Loops.so is an event-driven email platform

`connect()`:
- Validate API key via `GET /api-key` endpoint
- Test connection

`create_contact()`:
- POST to `/contacts/create` with email, firstName, lastName, source, userGroup, custom properties
- Loops uses `mailingList` for list management

`send_email()`:
- For transactional: POST to `/transactional` with `transactionalId`, `email`, `dataVariables`
- For event-triggered: POST to `/events/send` with `eventName`, `email`, `eventProperties`
- Loops doesn't support arbitrary HTML sends — it uses templates

`send_batch()`:
- Loops doesn't have native batch send — iterate through contacts
- Respect rate limits (10 requests/second)

`get_sequences()`:
- Loops calls these "Loops" — automated email sequences triggered by events
- No direct API to list all sequences (would need to be managed in Kai's state)

`create_sequence()`:
- Loops sequences are created in the UI — log a note that sequence should be configured in Loops dashboard
- Store the sequence config locally for reference

`manage_unsubscribe()`:
- PUT to `/contacts/update` with `subscribed: false`
- Or POST to `/contacts/delete` for full removal

Additional:
- `send_event(self, email: str, event_name: str, event_properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]` — Loops-specific: trigger an event that may start a sequence
- `_build_headers(self) -> Dict[str, str]` — `{"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}`

### File: `kai/connectors/lifecycle/mailchimp.py`

**Class: MailchimpConnector(EmailProvider)**

- `provider_name` returns `"mailchimp"`
- API base: determined from API key (last part after `-` is the datacenter)
- `BASE_URL_TEMPLATE = "https://{dc}.api.mailchimp.com/3.0"`

`connect()`:
- Extract datacenter from API key (e.g., `xxxx-us21` -> dc = `us21`)
- Test via `GET /ping`

`get_contacts()`:
- GET `/lists/{list_id}/members` with count/offset pagination
- Map status: "subscribed", "unsubscribed", "pending", "cleaned"

`create_contact()`:
- POST to `/lists/{list_id}/members` with email_address, status, merge_fields, tags

`send_email()`:
- Mailchimp: create campaign -> set content -> send campaign
- POST `/campaigns` with type "regular", list_id, subject_line
- PUT `/campaigns/{id}/content` with html body
- POST `/campaigns/{id}/actions/send`

`get_sequences()`:
- Mailchimp calls these "Automations" or "Customer Journeys"
- GET `/automations` — list all automations

`get_deliverability_stats()`:
- GET `/reports` for campaign reports
- Aggregate: emails_sent, opens.opens_total, clicks.clicks_total, bounces, unsubscribed

Additional:
- `get_audiences(self) -> List[Dict[str, Any]]` — GET `/lists` — Mailchimp-specific audience/list management
- `get_segments(self, list_id: str) -> List[Dict[str, Any]]` — GET `/lists/{list_id}/segments`
- `_get_datacenter(self) -> str` — extract DC from API key

### File: `kai/connectors/lifecycle/sendgrid.py`

**Class: SendGridConnector(EmailProvider)**

- `provider_name` returns `"sendgrid"`
- API base: `BASE_URL = "https://api.sendgrid.com/v3"`

`connect()`:
- Validate API key via GET `/scopes` (check permissions)

`send_email()`:
- POST to `/mail/send` with personalizations, from, subject, content array
- Support HTML and plain text content
- Support dynamic template with `template_id` and `dynamic_template_data`
- Include List-Unsubscribe header automatically

`send_batch()`:
- SendGrid supports up to 1000 personalizations per API call
- Batch contacts into groups of 1000

`get_contacts()`:
- GET `/marketing/contacts` or `/marketing/contacts/search` with SGQL query

`create_contact()`:
- PUT `/marketing/contacts` (upsert behavior)

`get_deliverability_stats()`:
- GET `/stats` with start_date/end_date
- GET `/suppression/bounces`, `/suppression/spam_reports`, `/suppression/unsubscribes`

`manage_unsubscribe()`:
- POST to `/asm/groups/{group_id}/suppressions` for group unsubscribe
- Or POST to `/asm/suppressions/global` for global unsubscribe

Additional:
- `check_domain_authentication(self) -> Dict[str, Any]` — GET `/whitelabel/domains` — check SPF, DKIM, DMARC setup
- `get_bounce_list(self) -> List[Dict[str, Any]]` — GET `/suppression/bounces`
- `_build_headers(self) -> Dict[str, str]` — `{"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}`

### File: `kai/connectors/lifecycle/generic_smtp.py`

**Class: GenericSMTPConnector(EmailProvider)**

- `provider_name` returns `"smtp"`
- Fallback connector for any email provider via SMTP

Additional config fields (stored in config.metadata):
- `smtp_host: str` — SMTP server hostname
- `smtp_port: int` — SMTP port (587 for TLS, 465 for SSL)
- `smtp_username: str`
- `smtp_password: str`
- `use_tls: bool = True`

`connect()`:
- Validate SMTP credentials by connecting and authenticating (in sandbox, just validate config is present)

`send_email()`:
- Build MIME message with headers, HTML body, plain text alternative
- Add List-Unsubscribe header
- Add CAN-SPAM physical address to footer
- Connect via SMTP, authenticate, send
- In sandbox: return mock response

Note: SMTP connector doesn't support most advanced features (sequences, contacts, segments). Those methods should return sensible defaults or raise `NotImplementedError("Generic SMTP connector does not support {feature}. Use a full email platform like Loops, Mailchimp, or SendGrid.")`.

### File: `kai/connectors/lifecycle/sms_base.py`

**Abstract class: SMSConnector(ABC)**

Stub for SMS connectivity (future implementation).

- `__init__(self, config: Dict[str, Any])` — store config
- `provider_name: str` — abstract property

**Model: SMSMessage**
- `id: Optional[str]`
- `to_phone: str`
- `from_phone: Optional[str]`
- `body: str` — max 160 chars per segment
- `status: str` — "draft", "queued", "sent", "delivered", "failed", default "draft"
- `segments: int = 1` — number of SMS segments
- `sent_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

Abstract methods:
- `connect(self) -> bool`
- `send_sms(self, message: SMSMessage) -> SMSMessage`
- `send_batch_sms(self, messages: List[SMSMessage]) -> List[SMSMessage]`
- `get_opt_out_list(self) -> List[str]` — phone numbers that opted out
- `check_opt_out(self, phone: str) -> bool` — check if phone has opted out

Note: concrete Twilio implementation left for future task. This defines the interface only.

### File: `kai/connectors/lifecycle/crm_base.py`

**Abstract class: CRMConnector(ABC)**

Stub for lightweight CRM connectivity.

- `__init__(self, config: Dict[str, Any])` — store config
- `provider_name: str` — abstract property

Abstract methods:
- `connect(self) -> bool`
- `get_contacts(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]`
- `create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]`
- `update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]`
- `get_deals(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]` — deal/opportunity tracking
- `create_deal(self, data: Dict[str, Any]) -> Dict[str, Any]`
- `get_activities(self, contact_id: str) -> List[Dict[str, Any]]` — activity log for a contact
- `log_activity(self, contact_id: str, activity: Dict[str, Any]) -> Dict[str, Any]`

Note: concrete HubSpot/Airtable implementations left for future tasks. This defines the interface only.

### General requirements for ALL connector files:

1. Module docstrings on every file
2. `from __future__ import annotations`
3. `import logging; logger = logging.getLogger(__name__)`
4. Sandbox mode checks on all API calls
5. CAN-SPAM compliance validation on every email send
6. Suppression list check before every send
7. Over-contact check before every send
8. Rate limit checks
9. No actual HTTP library imports — use `_api_call` placeholder
10. Type annotations on all methods

## Output Files

- `kai/connectors/lifecycle/__init__.py`
- `kai/connectors/lifecycle/base.py`
- `kai/connectors/lifecycle/email_base.py`
- `kai/connectors/lifecycle/loops.py`
- `kai/connectors/lifecycle/mailchimp.py`
- `kai/connectors/lifecycle/sendgrid.py`
- `kai/connectors/lifecycle/generic_smtp.py`
- `kai/connectors/lifecycle/sms_base.py`
- `kai/connectors/lifecycle/crm_base.py`

## Acceptance Criteria

- [ ] `LifecycleConnectorConfig` has all 13 fields with `sandbox_mode=True` default
- [ ] `EmailMessage` has all 18 fields
- [ ] `EmailDeliverabilityStats` has all 17 fields
- [ ] `ContactRecord` has all 18 fields
- [ ] `SequenceConfig` has all 9 fields
- [ ] `SuppressionEntry` has all 4 fields
- [ ] `LifecycleConnector` abstract class has all 12 abstract methods and 9 concrete helper methods
- [ ] `_validate_can_spam()` checks from_email, physical_address, unsubscribe, and subject
- [ ] `_check_over_contact()` enforces weekly contact limits
- [ ] `_add_compliance_headers()` adds List-Unsubscribe header
- [ ] `EmailProvider` extends LifecycleConnector with 5 additional methods
- [ ] `LoopsConnector` implements all methods with correct Loops.so API endpoints
- [ ] `LoopsConnector.send_event()` Loops-specific method exists
- [ ] `MailchimpConnector` implements all methods with correct Mailchimp API v3 endpoints
- [ ] `MailchimpConnector` extracts datacenter from API key
- [ ] `SendGridConnector` implements all methods with correct SendGrid v3 endpoints
- [ ] `SendGridConnector.check_domain_authentication()` method exists
- [ ] `GenericSMTPConnector` implements send_email via SMTP protocol
- [ ] `GenericSMTPConnector` raises NotImplementedError for unsupported features
- [ ] `SMSConnector` and `CRMConnector` abstract classes define clean interfaces
- [ ] `SMSMessage` model exists with correct fields
- [ ] All connectors check sandbox, rate limits, suppression, and CAN-SPAM before sending
- [ ] No actual HTTP imports
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/connectors/social/base.py` (created by Task 039) — SocialConnector pattern to mirror
- `kai/connectors/ads/base.py` (created by Task 044) — AdPlatformConnector pattern
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/channels/email-lifecycle.md` — email lifecycle channel guidance
- `harness/references/cold-email-rules.md` — CAN-SPAM and deliverability rules
- `harness/references/advertising-compliance.md` — CAN-SPAM compliance requirements
- `knowledge/playbooks/marketing-automation.md` — marketing automation playbook
- `CLAUDE.md` — full project context

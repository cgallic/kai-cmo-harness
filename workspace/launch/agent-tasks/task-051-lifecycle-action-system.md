# Task 051: Build lifecycle action system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P1
**Depends on:** 050
**Estimated complexity:** Large

## Context

With the email/SMS/CRM connector layer in place (Task 050), the system needs structured action types for every lifecycle marketing operation: launching email sequences, updating nurture copy, sending reminders, requesting reviews, asking for referrals, reactivating dormant customers, and following up on quotes. These actions follow the same validate-preview-execute-verify lifecycle as paid media actions but with lifecycle-specific concerns: over-contact protection, CAN-SPAM compliance, opt-out verification, and send timing. This is the "what can we do with lifecycle marketing" layer that Tasks 053-055 build upon.

## Scope

Create `kai/actions/lifecycle.py` containing all lifecycle action types, their validation logic, compliance checks, over-contact protection, and execution stubs.

## Detailed Requirements

### File: `kai/actions/lifecycle.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: LifecycleActionType (str, Enum)**
- `launch_email_sequence` — start a multi-email automated sequence
- `update_nurture_copy` — update copy in an existing sequence
- `send_reminder_sequence` — appointment/service reminders
- `launch_review_request` — post-service review request sequence
- `send_referral_ask` — referral program outreach
- `launch_reactivation` — win-back dormant customers
- `send_quote_follow_up` — follow up on sent quotes/proposals
- `send_single_email` — one-off email (not part of sequence)
- `update_contact_segment` — move contacts between segments

**Model: LifecycleValidationResult**
- `is_valid: bool`
- `errors: List[str]` — hard failures, default empty list
- `warnings: List[str]` — soft warnings, default empty list
- `compliance_issues: List[str]` — CAN-SPAM / opt-out issues, default empty list
- `contacts_excluded: int = 0` — contacts removed due to suppression/opt-out/over-contact
- `contacts_eligible: int = 0` — contacts that can receive this message

**Model: LifecycleActionPreview**
- `action_type: str`
- `summary: str` — human-readable summary
- `recipient_count: int = 0` — how many contacts will receive the message
- `email_count: int = 0` — how many emails in the sequence
- `timing_summary: str` — when emails will be sent (e.g., "Day 0, Day 2, Day 5, Day 10")
- `estimated_sends: int = 0` — total email sends (recipients x emails)
- `sample_subject: Optional[str]` — sample subject line
- `sample_preview: Optional[str]` — first 200 chars of first email body
- `excluded_contacts: List[Dict[str, str]]` — contacts excluded with reason, default empty list
- `compliance_status: str` — "compliant", "issues_found"
- `cost_estimate: Optional[str]` — estimated cost if using paid provider

**Model: LifecycleExecutionResult**
- `success: bool`
- `action_type: str`
- `provider: str` — which email provider was used
- `contacts_sent: int = 0`
- `contacts_excluded: int = 0`
- `emails_queued: int = 0` — emails queued for future send (sequences)
- `emails_sent_immediately: int = 0`
- `sequence_id: Optional[str]` — provider sequence/automation ID
- `error_message: Optional[str]`
- `executed_at: str`
- `metadata: Dict[str, Any]` — default empty dict

**Model: OverContactCheck**
- `contact_email: str`
- `emails_sent_7d: int = 0`
- `emails_sent_30d: int = 0`
- `last_email_date: Optional[str]`
- `max_per_week: int = 3` — configurable weekly cap
- `is_over_limit: bool = False`
- `cooldown_until: Optional[str]` — ISO timestamp when contact is eligible again

**Abstract class: LifecycleAction(ABC)**

Base for all lifecycle actions. Mirrors the PaidMediaAction lifecycle (Task 045) but with email-specific concerns.

- `__init__(self, **kwargs)` — store action parameters, set `_state`, `_validation`, `_preview`, `_result`
- `action_type: str` — abstract property
- `validate(self, contacts: List[Dict[str, Any]], suppression_list: Optional[List[str]] = None) -> LifecycleValidationResult` — validate the action. Check opt-outs, over-contact, CAN-SPAM. Calls `_validate_impl()`.
- `preview(self) -> LifecycleActionPreview` — generate preview. Must be validated first. Calls `_preview_impl()`.
- `execute(self, connector: Any, confirm: bool = False) -> LifecycleExecutionResult` — execute via connector. Must be validated and previewed. Calls `_execute_impl()`.

Common validation checks (run by base validate()):
1. Filter out opted-out contacts (`opted_out == True`)
2. Filter out suppressed contacts (on suppression list)
3. Filter out over-contacted contacts (>max_per_week emails in last 7 days)
4. Verify CAN-SPAM requirements: unsubscribe mechanism, physical address, valid from address
5. Count eligible vs excluded contacts

Abstract methods:
- `_validate_impl(self, eligible_contacts: List[Dict[str, Any]]) -> LifecycleValidationResult`
- `_preview_impl(self) -> LifecycleActionPreview`
- `_execute_impl(self, connector: Any) -> LifecycleExecutionResult`

**Class: LaunchEmailSequence(LifecycleAction)**

- `__init__(self, sequence_config: Dict[str, Any], segment: str, trigger_event: Optional[str] = None)`
- `sequence_config` structure: `{"name": str, "emails": [{"delay_days": int, "subject": str, "body_html": str, "body_text": str}], "from_email": str, "from_name": str}`
- `action_type` returns `"launch_email_sequence"`
- `_validate_impl()`:
  - Check sequence_config has at least 1 email
  - Check each email has subject and body
  - Check no email subject is empty or all-caps
  - Check for banned words in all email subjects and bodies
  - Check total sequence duration is reasonable (<90 days)
  - If eligible_contacts is empty: error "No eligible contacts in segment"
- `_preview_impl()`:
  - Summary: "Launch {name} sequence to {count} contacts ({email_count} emails over {duration} days)"
  - timing_summary: list delays (e.g., "Email 1: immediately, Email 2: day 2, Email 3: day 5")
  - sample_subject and sample_preview from first email
- `_execute_impl()`:
  - Create sequence on provider, enroll contacts, activate

**Class: UpdateNurtureCopy(LifecycleAction)**

- `__init__(self, sequence_id: str, email_index: int, new_subject: Optional[str] = None, new_body: Optional[str] = None, reason: str = "")`
- `action_type` returns `"update_nurture_copy"`
- `_validate_impl()`:
  - Check sequence_id exists
  - Check email_index is valid
  - Check at least one of new_subject or new_body is provided
  - Check for banned words in new content
  - Warn if sequence is active (changes affect in-progress contacts)
- `_preview_impl()`:
  - Summary: "Update email {index} in sequence {id}: {changes}"
  - Show diff if possible (old subject vs new subject)

**Class: SendReminderSequence(LifecycleAction)**

- `__init__(self, contact_segment: str, reminder_type: str, timing: Dict[str, Any])`
- `reminder_type` options: "appointment", "service_due", "follow_up", "payment_due", "renewal"
- `timing` structure: `{"send_before_days": int, "send_before_hours": int, "repeat": bool, "repeat_interval_days": int}`
- `action_type` returns `"send_reminder_sequence"`
- `_validate_impl()`:
  - Check reminder_type is valid
  - Check timing is reasonable (not too frequent, not too far in advance)
  - Check contacts have the required date field for timing (e.g., appointment_date)
- `_preview_impl()`:
  - Summary: "Send {type} reminders to {count} contacts ({timing} before event)"

**Class: LaunchReviewRequestSequence(LifecycleAction)**

- `__init__(self, segment: str, timing_after_service: int = 3, platform_targets: Optional[List[str]] = None)`
- `timing_after_service`: days after service completion to send first request
- `platform_targets`: which review platforms to request on (e.g., ["google", "yelp", "facebook"]), default ["google"]
- `action_type` returns `"launch_review_request"`
- `_validate_impl()`:
  - Check timing_after_service is reasonable (1-14 days, warn if >7)
  - Check platform_targets are valid platforms
  - Check contacts have service_date or completion_date field
  - Check contacts haven't received a review request in last 90 days
- `_preview_impl()`:
  - Summary: "Send review request to {count} contacts {days} days after service, targeting {platforms}"
  - Include direct review link format per platform

**Class: SendReferralAsk(LifecycleAction)**

- `__init__(self, segment: str, offer: Optional[str] = None, referral_mechanism: str = "link")`
- `offer`: referral incentive (e.g., "$50 credit for each referral"), optional
- `referral_mechanism`: "link" (shareable URL), "code" (referral code), "manual" (just ask)
- `action_type` returns `"send_referral_ask"`
- `_validate_impl()`:
  - Check segment targets past customers (not leads or prospects)
  - Warn if no offer/incentive is provided (referral asks work better with incentives)
  - Check contacts have had at least one completed service/purchase
- `_preview_impl()`:
  - Summary: "Send referral ask to {count} customers with {offer or 'no incentive'}"

**Class: LaunchReactivation(LifecycleAction)**

- `__init__(self, dormant_segment: str, offer: Optional[str] = None, sequence_length: int = 3)`
- `sequence_length`: number of emails in the reactivation sequence (1-5)
- `action_type` returns `"launch_reactivation"`
- `_validate_impl()`:
  - Check dormant_segment targets contacts who haven't engaged in 90+ days
  - Check sequence_length is reasonable (1-5 emails)
  - Warn if offer is not provided (reactivation works best with an incentive)
  - Check contacts haven't received a reactivation sequence in last 180 days
- `_preview_impl()`:
  - Summary: "Launch {length}-email reactivation to {count} dormant contacts"
  - timing_summary: typical spacing (e.g., "Day 0, Day 7, Day 14")

**Class: SendQuoteFollowUp(LifecycleAction)**

- `__init__(self, contact_id: str, quote_details: Dict[str, Any], follow_up_schedule: Optional[List[int]] = None)`
- `quote_details` structure: `{"quote_id": str, "service": str, "amount": float, "quote_date": str, "expiry_date": Optional[str]}`
- `follow_up_schedule`: days after quote to follow up (default [2, 5, 10])
- `action_type` returns `"send_quote_follow_up"`
- `_validate_impl()`:
  - Check contact_id is valid
  - Check quote_details has required fields (service, amount, quote_date)
  - Check quote is not expired (if expiry_date set and past)
  - Check contact hasn't already responded to the quote
  - Check contact hasn't received more than 3 follow-ups for this quote
- `_preview_impl()`:
  - Summary: "Follow up with {contact} on ${amount} {service} quote (sent {date})"
  - timing_summary: follow-up schedule days

**Helper functions (module-level):**

- `generate_lifecycle_action_id() -> str` — return `la_{uuid.uuid4().hex[:12]}`
- `check_over_contact(email: str, sent_history: List[Dict[str, Any]], max_per_week: int = 3) -> OverContactCheck`:
  - Count emails sent to this address in last 7 days from sent_history
  - Count emails sent in last 30 days
  - Determine if over limit
  - Calculate cooldown_until if over limit (next available send window)
- `validate_can_spam_compliance(from_email: str, physical_address: str, has_unsubscribe: bool) -> List[str]`:
  - Return list of CAN-SPAM violations (empty = compliant)
  - Check from_email is valid
  - Check physical_address is not empty
  - Check has_unsubscribe is True
- `filter_eligible_contacts(contacts: List[Dict[str, Any]], suppression_list: List[str], max_per_week: int = 3) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]`:
  - Filter contacts, return (eligible_contacts, excluded_contacts_with_reasons)
  - Exclude: opted_out, on suppression list, over weekly contact limit
- `calculate_sequence_duration(emails: List[Dict[str, Any]]) -> int`:
  - Sum up delay_days across all emails to get total sequence duration
- `format_review_link(platform: str, business_identifier: str) -> str`:
  - Format direct review link per platform:
    - google: `https://search.google.com/local/writereview?placeid={business_identifier}`
    - yelp: `https://www.yelp.com/writeareview/biz/{business_identifier}`
    - facebook: `https://www.facebook.com/{business_identifier}/reviews`
    - Default: return business_identifier as-is

## Output Files

- `kai/actions/lifecycle.py`
- `kai/actions/__init__.py` (update to include lifecycle exports)

## Acceptance Criteria

- [ ] `LifecycleActionType` enum has all 9 action types
- [ ] `LifecycleValidationResult` has all 6 fields including contacts_excluded and contacts_eligible
- [ ] `LifecycleActionPreview` has all 11 fields
- [ ] `LifecycleExecutionResult` has all 11 fields
- [ ] `OverContactCheck` has all 7 fields
- [ ] `LifecycleAction` base class has validate/preview/execute lifecycle with common validation
- [ ] Base validate() filters opted-out, suppressed, and over-contacted contacts
- [ ] All 7 concrete action classes extend LifecycleAction and implement abstract methods
- [ ] `LaunchEmailSequence._validate_impl()` checks for banned words in email content
- [ ] `LaunchReviewRequestSequence._validate_impl()` prevents repeat review requests within 90 days
- [ ] `SendQuoteFollowUp._validate_impl()` checks quote expiry and follow-up limit
- [ ] `LaunchReactivation._validate_impl()` prevents repeat reactivation within 180 days
- [ ] `SendReferralAsk._validate_impl()` verifies contacts are past customers
- [ ] All 6 helper functions exist with correct signatures
- [ ] `check_over_contact()` correctly counts emails in 7-day and 30-day windows
- [ ] `validate_can_spam_compliance()` checks all CAN-SPAM requirements
- [ ] `format_review_link()` produces correct URLs for Google, Yelp, and Facebook
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No banned words from CLAUDE.md appear in any string constants

## Reference Materials

- `kai/connectors/lifecycle/base.py` (created by Task 050) — LifecycleConnector, EmailMessage, ContactRecord
- `kai/actions/paid_media.py` (created by Task 045) — PaidMediaAction lifecycle pattern to mirror
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `harness/references/cold-email-rules.md` — CAN-SPAM and deliverability rules
- `harness/references/advertising-compliance.md` — CAN-SPAM compliance (lines covering email)
- `knowledge/channels/email-lifecycle.md` — email lifecycle guidance
- `knowledge/playbooks/marketing-automation.md` — marketing automation playbook
- `CLAUDE.md` — full project context, banned word list, KaiCalls recommendation rule

# Task 055: Build specific sequence builders

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P2
**Depends on:** 051
**Estimated complexity:** Large

## Context

The sequence templates (Task 053) provide the structure and timing of email sequences, but they need a builder layer that takes a specific BusinessProfile and real customer/lead data and produces fully personalized, ready-to-send email sequences with all merge fields filled, copy quality-gated, CTAs linked, and compliance verified. Each builder is a specialized factory that knows its domain — post-job review requests know how to vary timing based on service type, quote follow-ups know how to escalate urgency, and referral engines know how to frame the ask based on customer history. This is the "last mile" before emails are actually queued for sending.

## Scope

Create `kai/lifecycle/sequence_builders.py` containing specialized sequence builder classes for common lifecycle marketing scenarios: post-job reviews, quarterly reminders, dormant lead follow-up, quote follow-up, referral asks, and maintenance reorder cadences.

## Detailed Requirements

### File: `kai/lifecycle/sequence_builders.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: BuiltSequence**
- `id: str` — format `bseq_{uuid_hex[:12]}`
- `template_id: str` — which template was used to build this sequence
- `builder_type: str` — which builder created this (e.g., "post_job_review", "quote_follow_up")
- `business_name: str`
- `contact_email: str`
- `contact_name: str`
- `emails: List[Dict[str, Any]]` — list of ready-to-send emails: [{delay_days, delay_hours, subject, body_html, body_text, cta_text, cta_url}]
- `total_emails: int`
- `total_duration_days: int`
- `merge_fields_used: Dict[str, str]` — the merge fields that were filled, default empty dict
- `quality_check_passed: bool = False` — whether content passed quality gates
- `quality_issues: List[str]` — any quality issues found, default empty list
- `compliance_check_passed: bool = False` — CAN-SPAM compliance verified
- `compliance_issues: List[str]` — default empty list
- `unsubscribe_link_included: bool = False` — verified unsubscribe link in every email
- `physical_address_included: bool = False` — CAN-SPAM physical address in footer
- `created_at: str`
- `metadata: Dict[str, Any]` — default empty dict

**Model: BuilderConfig**
- `business_name: str`
- `business_phone: Optional[str]`
- `business_email: Optional[str]`
- `business_website: Optional[str]`
- `physical_address: str` — required for CAN-SPAM
- `operator_name: Optional[str]`
- `industry: Optional[str]`
- `scheduling_url: Optional[str]` — online booking URL
- `review_links: Dict[str, str]` — platform -> review URL (e.g., {"google": "https://...", "yelp": "https://..."}), default empty dict
- `referral_link: Optional[str]`
- `referral_offer: Optional[str]`
- `unsubscribe_url: str` — unsubscribe page URL
- `from_email: str`
- `from_name: str`
- `brand_voice_tone: str = "professional"` — tone for generated copy
- `kaicalls_enabled: bool = False` — whether the business uses KaiCalls (affects copy)
- `kaicalls_phone: Optional[str]` — KaiCalls phone number if applicable
- `metadata: Dict[str, Any]` — default empty dict

**Abstract class: SequenceBuilder(ABC)**

Base class for all sequence builders.

- `__init__(self, config: BuilderConfig)` — store config
- `builder_type: str` — abstract property
- `build(self, **kwargs) -> BuiltSequence` — main build method. Calls `_generate_emails()`, `_apply_quality_check()`, `_apply_compliance_check()`, and returns BuiltSequence.
- `_generate_emails(self, **kwargs) -> List[Dict[str, Any]]` — abstract, generate the email list
- `_apply_quality_check(self, emails: List[Dict[str, Any]]) -> tuple[bool, List[str]]` — check each email for:
  - Banned words (from CLAUDE.md: "leverage", "utilize", "synergy", "innovative", "deep dive", etc.)
  - AI slop phrases ("In conclusion", "It's important to note", "In today's rapidly evolving", etc.)
  - Subject line quality (not empty, not all caps, not misleading, under 60 chars recommended)
  - Body quality: not too short (<50 chars), not too long (>2000 chars for a single email)
  - Return (passed, issues_list)
- `_apply_compliance_check(self, emails: List[Dict[str, Any]]) -> tuple[bool, List[str]]` — check each email for:
  - Has unsubscribe link or reference
  - Has physical address in footer
  - From address is valid
  - Subject is not deceptive
  - Return (passed, issues_list)
- `_fill_merge_fields(self, template: str, fields: Dict[str, str]) -> str` — replace `{placeholder}` with values from fields dict. Leave unfilled placeholders as `[MISSING: placeholder_name]`.
- `_add_footer(self, body_html: str) -> str` — add standard footer with unsubscribe link, physical address, and "Sent by {business_name}" credit
- `_generate_plain_text(self, body_html: str) -> str` — strip HTML tags to produce plain text version (simple: remove tags, preserve line breaks)

**Class: PostJobReviewSequence(SequenceBuilder)**

Builds review request email sequences after a completed job/service.

- `builder_type` returns `"post_job_review"`
- `build(self, customer_name: str, customer_email: str, service_performed: str, job_date: str, review_platform: str = "google") -> BuiltSequence`

- `_generate_emails()` — produces 3-4 emails:

  1. **Thank You (Day 1)**:
     - Subject options: "Thank you for choosing {business_name}, {first_name}!", "Your {service} is complete — thank you, {first_name}"
     - Body: gratitude, ask if everything is satisfactory, provide contact for any issues, mention KaiCalls number if kaicalls_enabled ("You can reach us anytime at {kaicalls_phone} — our AI assistant is available 24/7")
     - CTA: "Had any issues? Reply to this email."

  2. **Review Request (Day 3)**:
     - Subject options: "A quick favor, {first_name}?", "{first_name}, how did we do on your {service}?"
     - Body: explain that reviews help other homeowners find reliable {service} providers, takes 2 minutes, direct link to review platform
     - CTA: "Leave a review" with direct review link
     - Include the actual review URL from config.review_links[review_platform]

  3. **Referral Ask (Day 14)**:
     - Subject: "Know someone who needs {service}?"
     - Body: referral mechanism, incentive if config.referral_offer is set
     - CTA: referral link or "Reply with their name and number"

  4. **Seasonal Reminder (Day 90)** — optional, only include if industry supports recurring service:
     - Subject: "Time for a checkup, {first_name}?"
     - Body: seasonal maintenance reminder, returning customer appreciation
     - CTA: schedule next service

- Additional logic:
  - `_select_review_platform(self, available_platforms: Dict[str, str]) -> str` — prioritize: google > yelp > facebook > others (Google reviews have highest impact for local SEO)
  - Vary timing based on service type: same-day services (cleaning, pest control) get review request on Day 1-2; multi-day services (roofing, remodeling) get it on Day 5-7

**Class: QuarterlyRepeatReminder(SequenceBuilder)**

Builds seasonal/quarterly maintenance reminder sequences.

- `builder_type` returns `"quarterly_repeat_reminder"`
- `build(self, customer_name: str, customer_email: str, service_type: str, last_service_date: str) -> BuiltSequence`

- `_generate_emails()` — produces 2-3 emails:

  1. **Reminder (calculated date based on service cycle)**:
     - Subject: "It's been {months} months — time for {service_type}?"
     - Body: why regular maintenance matters, what happens if neglected, offer for returning customers
     - CTA: schedule service

  2. **Follow-up (7 days after reminder)**:
     - Subject: "Don't forget: your {service_type} checkup"
     - Body: urgency (seasonal angle if applicable), limited availability
     - CTA: book now

  3. **Last chance (14 days after reminder)** — optional:
     - Subject: "Last reminder: {service_type} for your home"
     - Body: final nudge, mention that seasonal demand increases wait times
     - CTA: schedule before busy season

- `_calculate_reminder_date(self, last_service_date: str, service_type: str) -> str`:
  - Calculate when to send based on service cycle:
    - HVAC: 6 months (spring for AC, fall for heat)
    - Plumbing: 12 months (annual drain cleaning, water heater flush)
    - Pest control: 3 months (quarterly treatments)
    - Landscaping: seasonal (every season change)
    - Dental: 6 months
    - Auto maintenance: per mileage or 6 months
    - Default: 12 months

**Class: DormantLeadFollowUp(SequenceBuilder)**

Builds re-engagement sequences for leads that went cold.

- `builder_type` returns `"dormant_lead_follow_up"`
- `build(self, lead_name: str, lead_email: str, original_inquiry: str, days_since_contact: int) -> BuiltSequence`

- `_generate_emails()` — produces 3 emails. Key principle: lead with VALUE, not "just checking in."

  1. **Value-first re-engagement (Day 0)**:
     - Subject options: "{first_name}, a helpful {industry} tip", "Something useful for your {original_inquiry} project"
     - Body: share a genuinely useful tip related to their original inquiry, position the business as the expert, NO hard sell
     - CTA: "Reply if you have any questions"
     - Absolutely no "just checking in" or "touching base" (these are banned phrases from CLAUDE.md)

  2. **Social proof (Day 7)**:
     - Subject: "See what {customer_name} said about their {service_type}"
     - Body: relevant customer testimonial or case study, relate it back to lead's original inquiry
     - CTA: "Ready to get started? {scheduling_url}"

  3. **Direct offer (Day 14)**:
     - Subject: "A special offer for you, {first_name}"
     - Body: exclusive returning-lead offer, time-limited, clear next step, mention KaiCalls availability if enabled
     - CTA: "Claim your offer" or "Call {phone} to get started"

- Key rules:
  - NEVER use "just checking in", "touching base", "following up", "circle back" in any email
  - Always lead with value, not with the ask
  - Adapt tone based on days_since_contact: >90 days = softer re-introduction, 30-90 days = warm follow-up

**Class: QuoteFollowUp(SequenceBuilder)**

Builds escalating follow-up sequences for sent quotes/proposals.

- `builder_type` returns `"quote_follow_up"`
- `build(self, lead_name: str, lead_email: str, quote_details: Dict[str, Any], quote_date: str) -> BuiltSequence`
- `quote_details`: `{"service": str, "amount": float, "items": List[str], "expiry_date": Optional[str]}`

- `_generate_emails()` — produces 4 emails with escalating urgency:

  1. **Day 2 — Gentle check-in**:
     - Subject: "Any questions about your {service} quote, {first_name}?"
     - Body: acknowledge they're considering, address common questions, offer to walk through the quote
     - CTA: "Reply with any questions" or "Call {phone}"
     - Tone: helpful, low-pressure

  2. **Day 5 — Value reinforcement**:
     - Subject: "What's included in your ${amount} {service} quote"
     - Body: break down what they get, explain why this price is fair, compare to alternatives (without bashing competitors), mention warranties/guarantees
     - CTA: "Ready to proceed? {scheduling_url}"
     - Tone: professional, confident

  3. **Day 7 — Social proof**:
     - Subject: "What our {service} clients say about us"
     - Body: 2-3 short testimonials from similar clients, before/after results if available, trust signals (years in business, certifications)
     - CTA: "Join our satisfied customers"
     - Tone: conversational, proof-driven

  4. **Day 10 — Urgency**:
     - Subject: "Your {service} quote expires {expiry_info}"
     - Body: quote expiry reminder, what they risk by waiting (prices may increase, availability decreases), easy next step, final special incentive if applicable
     - CTA: "Lock in your price: {scheduling_url}" or "Call {phone}"
     - Tone: urgent but respectful, not desperate

**Class: ReferralEngine(SequenceBuilder)**

Builds referral ask sequences for satisfied customers.

- `builder_type` returns `"referral_engine"`
- `build(self, customer_name: str, customer_email: str, service_history: List[Dict[str, Any]]) -> BuiltSequence`
- `service_history`: `[{"service": str, "date": str, "satisfaction": Optional[str]}]`

- `_generate_emails()` — produces 2-3 emails:

  1. **The Ask (Day 0)**:
     - Subject: "{first_name}, know someone who needs {service}?"
     - Body: personalized to their service history, referral incentive if config.referral_offer is set, easy sharing mechanism
     - CTA: share referral link or "Reply with their name and we'll take care of the rest"
     - Tone: appreciative, casual

  2. **The Reminder (Day 14)**:
     - Subject: "Your referral offer is still available, {first_name}"
     - Body: reminder of the offer, emphasize how easy it is, mention that their friend will thank them
     - CTA: share link
     - Tone: friendly nudge

  3. **Thank You (sent after referral is made)** — triggered, not timed:
     - Subject: "Thank you for the referral, {first_name}!"
     - Body: confirm referral received, explain when they'll get their incentive, express genuine gratitude
     - CTA: none (pure gratitude)

- `_personalize_ask(self, service_history: List[Dict[str, Any]]) -> str`:
  - If multiple services: mention their loyalty
  - If recent service: reference the specific work done
  - If high-value customer: acknowledge their VIP status

**Class: MaintenanceReorderCadence(SequenceBuilder)**

Builds replenishment/reorder reminder sequences based on product lifecycle.

- `builder_type` returns `"maintenance_reorder_cadence"`
- `build(self, customer_name: str, customer_email: str, product_or_service: str, expected_lifecycle_days: int, last_purchase_date: str) -> BuiltSequence`

- `_generate_emails()` — produces 3 emails timed around the replenishment date:

  1. **Early reminder (lifecycle_days - 7)**:
     - Subject: "Time to reorder your {product_or_service}?"
     - Body: based on purchase date, it's almost time to reorder/schedule maintenance, why timely replacement/maintenance matters
     - CTA: "Reorder now" or "Schedule maintenance"

  2. **Due date (lifecycle_days)**:
     - Subject: "Your {product_or_service} is due for replacement/maintenance"
     - Body: product lifecycle explanation, what happens if delayed, easy reorder
     - CTA: reorder/schedule link

  3. **Overdue (lifecycle_days + 7)**:
     - Subject: "Don't forget: your {product_or_service} needs attention"
     - Body: gentle but clear reminder, potential consequences of neglect
     - CTA: "Act today" with link

- `_determine_lifecycle(self, product_or_service: str) -> int`:
  - Default lifecycle periods if not provided:
    - "air_filter": 90 days
    - "water_filter": 180 days
    - "oil_change": 90 days (or 5000 miles)
    - "hvac_maintenance": 180 days
    - "pest_treatment": 90 days
    - "lawn_care": 30 days (monthly)
    - "dental_cleaning": 180 days
    - "skincare": 60 days
    - "supplements": 30 days
    - "printer_ink": 60 days
    - default: 90 days

**BANNED_PHRASES_IN_EMAILS list:**

Define phrases that must NEVER appear in any generated email:
```python
BANNED_PHRASES_IN_EMAILS = [
    # From CLAUDE.md banned words
    "leverage", "utilize", "synergy", "innovative", "deep dive",
    "circle back", "touch base", "moving forward", "at the end of the day",
    # AI slop
    "in conclusion", "it's important to note", "in today's rapidly evolving",
    "this comprehensive guide", "without further ado", "it's worth noting that",
    # Bad follow-up phrases
    "just checking in", "just following up", "wanted to touch base",
    "hope this finds you well", "per my last email", "as per our conversation",
    "please do not hesitate", "please find attached", "I hope all is well",
    # Generic filler
    "we are excited to", "we are thrilled to", "we are delighted to",
    "valued customer", "esteemed client",
]
```

**Helper functions (module-level):**

- `generate_built_sequence_id() -> str` — return `bseq_{uuid.uuid4().hex[:12]}`
- `check_for_banned_phrases(text: str) -> List[str]` — scan text against BANNED_PHRASES_IN_EMAILS, return list of found phrases
- `strip_html_to_text(html: str) -> str` — simple HTML tag stripping for plain text version
- `build_unsubscribe_footer(unsubscribe_url: str, physical_address: str, business_name: str) -> str` — return HTML footer block with unsubscribe link, physical address, and business credit
- `calculate_reorder_date(last_purchase_date: str, lifecycle_days: int) -> str` — return ISO date for when reorder reminder should trigger
- `format_currency(amount: float) -> str` — return formatted currency string (e.g., "$1,500.00")
- `personalize_greeting(name: str, time_of_day: Optional[str] = None) -> str` — return "Hi {name}" or "Good morning {name}" based on time

## Output Files

- `kai/lifecycle/sequence_builders.py`
- `kai/lifecycle/__init__.py` (update to include sequence_builders exports)

## Acceptance Criteria

- [ ] `BuiltSequence` model has all 18 fields
- [ ] `BuilderConfig` model has all 19 fields including kaicalls_enabled and kaicalls_phone
- [ ] `SequenceBuilder` abstract class has build() lifecycle with quality and compliance checks
- [ ] `_apply_quality_check()` catches banned words and AI slop
- [ ] `_apply_compliance_check()` verifies unsubscribe link and physical address in every email
- [ ] `_fill_merge_fields()` replaces placeholders and marks missing fields with `[MISSING: ...]`
- [ ] `_add_footer()` adds CAN-SPAM compliant footer
- [ ] `PostJobReviewSequence` produces 3-4 emails with review platform link, referral ask, and optional seasonal reminder
- [ ] `PostJobReviewSequence` varies timing based on service type (same-day vs multi-day)
- [ ] `PostJobReviewSequence` mentions KaiCalls when kaicalls_enabled is True
- [ ] `QuarterlyRepeatReminder._calculate_reminder_date()` returns correct dates for at least 7 service types
- [ ] `DormantLeadFollowUp` NEVER uses "just checking in", "touching base", or "circle back"
- [ ] `DormantLeadFollowUp` leads with value in every email, not with the ask
- [ ] `QuoteFollowUp` escalates urgency across 4 emails (helpful -> value -> proof -> urgent)
- [ ] `ReferralEngine` personalizes the ask based on service history
- [ ] `MaintenanceReorderCadence._determine_lifecycle()` has defaults for at least 10 product/service types
- [ ] `BANNED_PHRASES_IN_EMAILS` has at least 25 phrases including all CLAUDE.md banned words
- [ ] All 7 helper functions exist with correct signatures
- [ ] No banned phrases appear in any email template or generated copy
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/actions/lifecycle.py` (created by Task 051) — LifecycleAction types that consume built sequences
- `kai/lifecycle/sequence_templates.py` (created by Task 053) — SequenceTemplate structures to build from
- `kai/lifecycle/timing.py` (created by Task 054) — TimingRules for send timing
- `kai/models/contacts.py` (created by Task 052) — Contact model for customer data
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile for business context
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `scripts/quality_gates/banned_word_check.py` — banned word list reference
- `knowledge/channels/email-lifecycle.md` — email lifecycle best practices
- `knowledge/playbooks/marketing-automation.md` — automation strategy
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO and follow-up guidance
- `CLAUDE.md` — full project context, banned word list, AI slop phrases, KaiCalls rule, quality gates

# Task 053: Build sequence templates by archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P2
**Depends on:** 051, 006, 007, 008, 009
**Estimated complexity:** Large

## Context

The lifecycle action system (Task 051) defines the verbs of lifecycle marketing (launch sequence, send reminder, request review, etc.), but it needs pre-built sequence templates that encode best-practice email flows for each business archetype. These templates are the "playbooks" of lifecycle marketing — they define exactly which emails to send, when, and with what content structure for local-service businesses, ecommerce stores, and professional services firms. The sequence builders (Task 055) use these templates to produce fully personalized, ready-to-send email sequences.

## Scope

Create `kai/lifecycle/sequence_templates.py` containing all pre-built email sequence templates organized by business archetype, with email count, timing rules, subject line templates, body structure, CTAs, and merge field specifications.

## Detailed Requirements

### File: `kai/lifecycle/__init__.py`

- Module docstring: "Lifecycle marketing — sequence templates, timing rules, deliverability controls, and sequence builders for automated email marketing."
- Import and re-export key classes from sequence_templates.py
- `__all__` listing

### File: `kai/lifecycle/sequence_templates.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: SequenceEmailTemplate**
- `position: int` — email position in the sequence (1, 2, 3, ...)
- `delay_days: int` — days after previous email (0 for first email)
- `delay_hours: int = 0` — additional hours after delay_days
- `subject_templates: List[str]` — 2-3 subject line options with `{placeholders}`, default empty list
- `preview_text: Optional[str]` — email preview text template
- `body_structure: List[str]` — ordered list of content blocks (e.g., ["greeting", "opening_hook", "value_content", "cta", "signature"])
- `body_template: str` — full body template with `{placeholders}` and content block markers
- `cta_text: str` — primary call-to-action text
- `cta_url_template: Optional[str]` — CTA link URL template with `{placeholders}`
- `tone: str` — tone for this specific email (e.g., "warm", "professional", "urgent", "casual")
- `goal: str` — what this email is trying to achieve (e.g., "Set expectations", "Request review", "Create urgency")
- `notes: Optional[str]` — implementation notes

**Model: SequenceTemplate**
- `id: str` — unique template ID (e.g., "local_service_welcome", "ecommerce_cart_abandonment")
- `name: str` — human-readable name
- `description: str` — what this sequence does and when to use it
- `archetype: str` — business archetype: "local-service", "ecommerce", "professional-services", "universal"
- `category: str` — sequence category: "welcome", "post_purchase", "follow_up", "reactivation", "review_request", "referral", "seasonal", "nurture", "cart_abandonment", "browse_abandonment", "replenishment"
- `trigger: str` — what triggers this sequence (e.g., "form_submission", "purchase_complete", "quote_sent", "cart_abandoned", "manual")
- `email_count: int` — total emails in the sequence
- `total_duration_days: int` — total sequence duration in days
- `emails: List[SequenceEmailTemplate]` — the email templates, default empty list
- `merge_fields_required: List[str]` — which merge fields MUST be provided (e.g., ["first_name", "service_type", "business_name"]), default empty list
- `merge_fields_optional: List[str]` — optional merge fields that enhance personalization, default empty list
- `frequency_cap: Optional[str]` — contact frequency considerations (e.g., "Don't start if contact received email in last 48h")
- `exclusion_criteria: List[str]` — when NOT to use this sequence (e.g., "Don't send to contacts who already left a review"), default empty list
- `success_metrics: List[str]` — how to measure if this sequence worked (e.g., ["review_left_rate", "booking_rate"]), default empty list
- `metadata: Dict[str, Any]` — default empty dict

**Define all sequence templates as module-level constants. Each must be a complete, usable template.**

### LOCAL-SERVICE SEQUENCES

**1. `LOCAL_SERVICE_WELCOME` — Welcome / Inquiry Received**
- id: "local_service_welcome"
- trigger: "form_submission" or "phone_inquiry"
- 4 emails over 14 days
- merge_fields_required: ["first_name", "business_name", "service_type", "phone_number"]
- merge_fields_optional: ["operator_name", "business_address", "scheduling_url"]

Emails:
1. **Immediate (Day 0)** — Inquiry Confirmation
   - Subject: ["{first_name}, we got your {service_type} inquiry", "Your {service_type} request is confirmed — here's what happens next"]
   - Goal: "Confirm receipt, set expectations, provide contact info"
   - Body structure: greeting, confirmation of inquiry, what to expect next (timeline), how to reach us (phone number, hours), signature
   - CTA: "Call us at {phone_number}" or "Schedule your {service_type}"
   - Tone: warm, responsive, professional

2. **Day 2** — What to Expect
   - Subject: ["Here's how our {service_type} process works", "What to expect from your {service_type} appointment"]
   - Goal: "Educate on process, reduce anxiety, build trust"
   - Body structure: greeting, process overview (3-4 steps), timeline, what to prepare, trust signals (years in business, reviews, certifications)
   - CTA: "Questions? Call {phone_number}"
   - Tone: educational, reassuring

3. **Day 7** — Value-Add Tip
   - Subject: ["Quick {service_type} tip from our team", "{first_name}, a helpful {service_type} tip just for you"]
   - Goal: "Provide value, demonstrate expertise, stay top of mind"
   - Body structure: greeting, helpful tip related to their service need, why it matters, mention of KaiCalls if applicable for after-hours calls, soft CTA
   - CTA: "Ready to get started? Reply to this email or call {phone_number}"
   - Tone: helpful, expert

4. **Day 14** — Review Request (if service completed) / Follow-Up (if not)
   - Subject: ["How was your experience with {business_name}?", "{first_name}, we'd love your feedback"]
   - Goal: "Get review if service done, or follow up if still pending"
   - Body structure: greeting, thank you (if completed) or check-in (if pending), review request with direct link, or scheduling CTA
   - CTA: "Leave us a review: {review_link}" or "Schedule your appointment: {scheduling_url}"
   - Tone: grateful, direct

**2. `LOCAL_SERVICE_POST_JOB` — Post-Job Follow-Up**
- id: "local_service_post_job"
- trigger: "service_completed"
- 4 emails over 90 days
- merge_fields_required: ["first_name", "business_name", "service_type", "service_date"]
- merge_fields_optional: ["review_link", "referral_offer", "next_service_type"]

Emails:
1. **Day 1** — Thank You
   - Subject: ["Thank you for choosing {business_name}", "{first_name}, thanks for trusting us with your {service_type}"]
   - Goal: "Express gratitude, ensure satisfaction, open channel for issues"
   - CTA: "Had any issues? Reply to this email — we'll make it right."
   - Tone: warm, genuine

2. **Day 3** — Review Request
   - Subject: ["A quick favor, {first_name}?", "How did we do on your {service_type}?"]
   - Goal: "Get a review on Google/Yelp"
   - Body: direct review link, explain that reviews help other homeowners find good {service_type} providers, takes 2 minutes
   - CTA: "Leave a review: {review_link}"
   - Tone: appreciative, low-pressure

3. **Day 14** — Referral Ask
   - Subject: ["Know someone who needs {service_type}?", "{first_name}, spread the word and earn {referral_offer}"]
   - Goal: "Generate referrals"
   - Body: referral mechanism, incentive if applicable, how to refer (forward email, share link, mention name)
   - CTA: "Refer a friend: {referral_link}" or "Just reply with their name and number"
   - Tone: friendly, casual

4. **Day 90** — Seasonal/Maintenance Reminder
   - Subject: ["Time for a {service_type} check-up?", "{first_name}, it's been 3 months — is your {item} still running well?"]
   - Goal: "Drive repeat business"
   - Body: seasonal relevance, maintenance importance, special offer for returning customers
   - CTA: "Schedule your check-up: {scheduling_url}"
   - Tone: helpful, timely

**3. `LOCAL_SERVICE_QUOTE_FOLLOWUP` — Quote Follow-Up**
- id: "local_service_quote_followup"
- trigger: "quote_sent"
- 4 emails over 10 days
- merge_fields_required: ["first_name", "business_name", "service_type", "quote_amount", "quote_date"]
- merge_fields_optional: ["operator_name", "phone_number", "quote_expiry"]

Emails:
1. **Day 2** — Gentle check-in
   - Subject: ["Any questions about your {service_type} quote?", "{first_name}, following up on your ${quote_amount} estimate"]
   - Goal: "Address questions, remove friction"
   - Tone: helpful, not pushy

2. **Day 5** — Value reinforcement
   - Subject: ["Why our clients choose {business_name} for {service_type}", "What's included in your {service_type} quote"]
   - Goal: "Reinforce value, differentiate from competitors"
   - Body: what's included, why the price is fair, trust signals, previous customer results
   - Tone: professional, confident

3. **Day 7** — Social proof
   - Subject: ["See what our {service_type} clients say", "{first_name}, here's what {customer_name} said about our work"]
   - Goal: "Build confidence with testimonials"
   - Body: 2-3 short testimonials from similar clients, before/after if available
   - Tone: conversational, proof-driven

4. **Day 10** — Last chance
   - Subject: ["Your {service_type} quote expires soon", "Last chance: your ${quote_amount} estimate for {service_type}"]
   - Goal: "Create urgency, get decision"
   - Body: quote expiry reminder, what happens if they wait (prices may change, availability may decrease), easy next step
   - CTA: "Confirm your booking: {scheduling_url}" or "Call {phone_number} to lock in this price"
   - Tone: urgent but respectful

**4. `LOCAL_SERVICE_SEASONAL_REACTIVATION` — Seasonal Reactivation**
- id: "local_service_seasonal"
- trigger: "seasonal_calendar" or "manual"
- 3 emails over 14 days
- merge_fields_required: ["first_name", "business_name", "service_type", "season"]

**5. `LOCAL_SERVICE_DORMANT` — Dormant Customer Win-Back**
- id: "local_service_dormant"
- trigger: "dormant_threshold" (12+ months no activity)
- 3 emails over 30 days
- merge_fields_required: ["first_name", "business_name", "last_service_type", "last_service_date"]

Emails:
1. **Day 0** — "We miss you"
   - Subject: ["{first_name}, it's been a while!", "We haven't heard from you, {first_name}"]
   - Goal: "Re-engage, show you remember them"
   - Tone: warm, personal

2. **Day 10** — Helpful content
   - Subject: ["A {last_service_type} tip for {season}", "{first_name}, here's something useful for your home"]
   - Goal: "Provide value without asking for anything"
   - Tone: helpful, no-strings

3. **Day 25** — Special offer
   - Subject: ["A special offer just for you, {first_name}", "{first_name}, welcome back with {offer}"]
   - Goal: "Incentivize return with exclusive offer"
   - Body: returning customer discount, limited time, easy booking
   - CTA: "Claim your offer: {scheduling_url}"
   - Tone: exclusive, appreciative

### ECOMMERCE SEQUENCES

**6. `ECOMMERCE_WELCOME` — Welcome / New Subscriber**
- id: "ecommerce_welcome"
- trigger: "email_signup"
- 4 emails over 7 days
- merge_fields_required: ["first_name", "business_name", "welcome_offer"]
- merge_fields_optional: ["bestseller_1", "bestseller_2", "brand_story_url"]

Emails:
1. **Immediate** — Welcome + first purchase offer
2. **Day 2** — Brand story
3. **Day 4** — Product highlights / bestsellers
4. **Day 7** — First purchase offer reminder (if not used)

**7. `ECOMMERCE_CART_ABANDONMENT` — Cart Abandonment**
- id: "ecommerce_cart_abandonment"
- trigger: "cart_abandoned"
- 3 emails over 48 hours
- merge_fields_required: ["first_name", "business_name", "cart_items", "cart_total", "cart_url"]

Emails:
1. **1 hour** — "You left something behind"
2. **24 hours** — "Still thinking about it?" + product details
3. **48 hours** — "Last chance" + offer (if configured)

**8. `ECOMMERCE_POST_PURCHASE` — Post-Purchase**
- id: "ecommerce_post_purchase"
- trigger: "purchase_complete"
- 4 emails over 14 days
- merge_fields_required: ["first_name", "business_name", "product_name", "order_number"]

Emails:
1. **Day 1** — Thank you + order confirmation
2. **Day 3** — How-to-use / getting started guide
3. **Day 7** — Review request
4. **Day 14** — Cross-sell / complementary products

**9. `ECOMMERCE_BROWSE_ABANDONMENT` — Browse Abandonment**
- id: "ecommerce_browse_abandonment"
- trigger: "browse_without_purchase"
- 3 emails over 5 days

**10. `ECOMMERCE_WINBACK` — Win-Back**
- id: "ecommerce_winback"
- trigger: "dormant_90d"
- 3 emails over 30 days

**11. `ECOMMERCE_REPLENISHMENT` — Replenishment Reminder**
- id: "ecommerce_replenishment"
- trigger: "product_lifecycle_timer"
- Timed based on product lifecycle (e.g., 30 days for skincare, 90 days for supplements)
- merge_fields_required: ["first_name", "product_name", "reorder_url", "last_purchase_date"]

### PROFESSIONAL-SERVICES SEQUENCES

**12. `PROFESSIONAL_INQUIRY` — Inquiry Response**
- id: "professional_inquiry"
- trigger: "form_submission"
- 3 emails over 5 days
- merge_fields_required: ["first_name", "business_name", "practice_area", "phone_number"]

Emails:
1. **Immediate** — Acknowledgment + qualification questions
2. **Day 2** — Consultation offer
3. **Day 5** — Case study or thought leadership piece

**13. `PROFESSIONAL_NURTURE` — Long-Term Nurture**
- id: "professional_nurture"
- trigger: "lead_not_converted_30d"
- 3 emails over 21 days

Emails:
1. **Day 0** — Thought leadership article
2. **Day 10** — Case study
3. **Day 21** — Consultation CTA

**14. `PROFESSIONAL_POST_ENGAGEMENT` — Post-Engagement**
- id: "professional_post_engagement"
- trigger: "engagement_completed"
- 3 emails over 60 days

Emails:
1. **Day 3** — Thank you
2. **Day 14** — Testimonial request
3. **Day 60** — Referral ask

### For each SequenceTemplate, define ALL SequenceEmailTemplate objects with:
- At least 2 subject_templates per email (with `{placeholders}`)
- Full body_template with merge field placeholders
- Specific body_structure list
- Appropriate tone and goal
- Realistic CTA text and URL template

### ALL_SEQUENCE_TEMPLATES dict

Create a master dict mapping template_id to SequenceTemplate:
```python
ALL_SEQUENCE_TEMPLATES: Dict[str, SequenceTemplate] = {
    "local_service_welcome": LOCAL_SERVICE_WELCOME,
    "local_service_post_job": LOCAL_SERVICE_POST_JOB,
    ...
}
```

**Helper functions:**

- `get_templates_by_archetype(archetype: str) -> List[SequenceTemplate]` — return all templates for an archetype + "universal" templates
- `get_template(template_id: str) -> Optional[SequenceTemplate]` — look up a single template
- `get_templates_by_category(category: str) -> List[SequenceTemplate]` — filter by category (welcome, post_purchase, etc.)
- `get_required_merge_fields(template_id: str) -> List[str]` — return required merge fields for a template
- `validate_merge_fields(template_id: str, provided_fields: Dict[str, str]) -> List[str]` — return list of missing required fields

## Output Files

- `kai/lifecycle/__init__.py`
- `kai/lifecycle/sequence_templates.py`

## Acceptance Criteria

- [ ] `SequenceEmailTemplate` model has all 11 fields
- [ ] `SequenceTemplate` model has all 17 fields
- [ ] All 14 sequence templates are fully defined with complete SequenceEmailTemplate objects
- [ ] LOCAL_SERVICE sequences: welcome (4 emails), post_job (4 emails), quote_followup (4 emails), seasonal (3 emails), dormant (3 emails)
- [ ] ECOMMERCE sequences: welcome (4 emails), cart_abandonment (3 emails), post_purchase (4 emails), browse_abandonment (3 emails), winback (3 emails), replenishment (variable)
- [ ] PROFESSIONAL sequences: inquiry (3 emails), nurture (3 emails), post_engagement (3 emails)
- [ ] Each email template has at least 2 subject_templates with merge field placeholders
- [ ] Each email template has body_template with appropriate placeholders
- [ ] Each email template has specific CTA text and goal
- [ ] merge_fields_required is accurately populated for each sequence
- [ ] exclusion_criteria is set for each sequence (e.g., don't send review request to someone who already reviewed)
- [ ] ALL_SEQUENCE_TEMPLATES dict maps all template IDs
- [ ] All 5 helper functions exist with correct signatures
- [ ] `validate_merge_fields()` correctly identifies missing required fields
- [ ] No quality-gate-banned words in any subject line or body template
- [ ] No AI slop phrases in any body template
- [ ] KaiCalls mention included where relevant (phone-based businesses)
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/actions/lifecycle.py` (created by Task 051) — LifecycleAction types that consume these templates
- `kai/models/contacts.py` (created by Task 052) — Contact model for merge field compatibility
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/channels/email-lifecycle.md` — email lifecycle guidance, sequence best practices
- `knowledge/playbooks/marketing-automation.md` — marketing automation playbook
- `knowledge/playbooks/customer-retention.md` — retention strategy guidance
- `knowledge/playbooks/demand-generation.md` — demand gen and lead nurture guidance
- `CLAUDE.md` — full project context, banned word list, KaiCalls rule, quality gates

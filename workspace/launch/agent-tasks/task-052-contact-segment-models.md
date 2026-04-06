# Task 052: Build contact and segment models

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P1
**Depends on:** 050, 001
**Estimated complexity:** Medium

## Context

The lifecycle connector layer (Task 050) handles sending messages, but the system needs rich internal models for contacts, segments, and lead scoring that live independent of any specific provider. These models are the canonical internal representation of "who are our contacts, how do we group them, and which ones should we prioritize." Every lifecycle action (Task 051), sequence template (Task 053), and sequence builder (Task 055) operates on these models. The segment system must support both static lists and dynamic segments with filter rules, plus pre-built segments for common business archetypes.

## Scope

Create `kai/models/contacts.py` containing the Contact, Segment, SegmentRule, pre-built segment definitions by archetype, and a simple lead scoring system.

## Detailed Requirements

### File: `kai/models/contacts.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`. Follow conventions from existing `kai/models/` files.

**Enum: LifecycleStage (str, Enum)**
- `subscriber` — opted in / signed up, no expressed purchase intent
- `lead` — expressed interest (form fill, inquiry, chat)
- `qualified_lead` — meets ICP criteria, has budget/need/timeline
- `prospect` — actively in a sales conversation or quote process
- `customer` — completed first purchase/service
- `repeat_customer` — completed 2+ purchases/services
- `advocate` — actively refers others or leaves reviews
- `dormant` — no engagement in 90+ days
- `churned` — explicitly cancelled or 180+ days no activity

**Enum: ConsentStatus (str, Enum)**
- `opted_in` — explicitly opted in to marketing communications
- `opted_out` — explicitly opted out
- `transactional_only` — opted out of marketing but can receive transactional emails
- `unknown` — consent status not determined (treat as opted_out for marketing, allow transactional)
- `pending` — double opt-in pending confirmation

**Enum: ContactSource (str, Enum)**
- `website_form` — filled out a website form
- `phone_call` — called the business
- `chat` — used website chat
- `referral` — referred by another customer
- `ad_click` — came from a paid ad
- `organic_search` — found via search engine
- `social_media` — came from social media
- `email_reply` — replied to an email
- `walk_in` — walked into physical location
- `event` — met at event/webinar
- `manual` — manually added by operator
- `import` — bulk imported from file/CRM
- `api` — created via API integration
- `kaicalls` — captured by KaiCalls AI receptionist

**Enum: SegmentOperator (str, Enum)**
- `equals`
- `not_equals`
- `contains`
- `not_contains`
- `starts_with`
- `ends_with`
- `greater_than`
- `less_than`
- `greater_than_or_equal`
- `less_than_or_equal`
- `in_list` — value is in a list of values
- `not_in_list`
- `is_empty`
- `is_not_empty`
- `before` — date comparison
- `after` — date comparison
- `between` — date/number range
- `days_ago_more_than` — date is more than X days ago
- `days_ago_less_than` — date is less than X days ago

**Model: Contact**
- `id: str` — unique ID, format `con_{uuid_hex[:12]}`
- `email: str`
- `phone: Optional[str]`
- `first_name: Optional[str]`
- `last_name: Optional[str]`
- `full_name: Optional[str]` — computed or manually set
- `company: Optional[str]` — for B2B contacts
- `job_title: Optional[str]` — for B2B contacts
- `source: str` — ContactSource value, default "manual"
- `source_detail: Optional[str]` — additional source info (e.g., "Google Ads - Spring HVAC campaign", "Referral from John Smith")
- `source_url: Optional[str]` — URL where they converted (landing page, form URL)
- `created_at: str` — ISO timestamp
- `updated_at: Optional[str]`
- `first_contacted_at: Optional[str]` — when we first reached out
- `last_contacted_at: Optional[str]` — when we last sent them a message
- `last_engaged_at: Optional[str]` — when they last engaged (opened email, clicked, replied, called)
- `contact_frequency_7d: int = 0` — emails sent in last 7 days
- `contact_frequency_30d: int = 0` — emails sent in last 30 days
- `lifecycle_stage: str` — LifecycleStage value, default "lead"
- `consent_status: str` — ConsentStatus value, default "unknown"
- `opt_in_date: Optional[str]`
- `opt_out_date: Optional[str]`
- `opt_in_source: Optional[str]` — where they opted in (e.g., "website footer form", "checkout checkbox")
- `tags: List[str]` — freeform tags, default empty list
- `lists: List[str]` — segment/list IDs this contact belongs to, default empty list
- `custom_fields: Dict[str, Any]` — dynamic fields, default empty dict
- `lead_score: float = 0.0` — computed lead score (0-100)
- `lead_score_factors: Dict[str, float]` — breakdown of score factors, default empty dict
- `total_purchases: int = 0`
- `total_revenue: float = 0.0` — lifetime revenue from this contact
- `average_order_value: float = 0.0`
- `last_purchase_date: Optional[str]`
- `last_service_date: Optional[str]`
- `referral_count: int = 0` — how many referrals this contact has made
- `review_status: Optional[str]` — "none", "requested", "left_review", "declined"
- `review_platform: Optional[str]` — where they left a review (google, yelp, etc.)
- `notes: Optional[str]` — operator notes
- `business_id: Optional[str]` — link to BusinessProfile
- `provider_ids: Dict[str, str]` — mapping of provider -> provider contact ID (e.g., {"loops": "xxx", "mailchimp": "yyy"}), default empty dict
- `metadata: Dict[str, Any]` — default empty dict

**Model: SegmentRule**
- `field: str` — the contact field to filter on (e.g., "lifecycle_stage", "last_purchase_date", "tags", "lead_score")
- `operator: str` — SegmentOperator value
- `value: Any` — the comparison value (type depends on operator and field)
- `value_type: str` — "string", "number", "date", "boolean", "list", default "string"

**Model: Segment**
- `id: str` — format `seg_{uuid_hex[:12]}`
- `name: str` — human-readable segment name
- `description: Optional[str]` — what this segment represents
- `rules: List[SegmentRule]` — filter rules (ANDed together), default empty list
- `rule_logic: str` — "and" (all rules must match) or "or" (any rule matches), default "and"
- `is_dynamic: bool = True` — if True, contact list refreshes automatically based on rules; if False, static list
- `static_contact_ids: List[str]` — manually added contact IDs (for static segments), default empty list
- `contact_count: int = 0` — cached count of matching contacts
- `last_refreshed: Optional[str]` — ISO timestamp
- `archetype: Optional[str]` — which business archetype this segment is designed for
- `created_at: Optional[str]`
- `updated_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Pre-built segments: `LOCAL_SERVICE_SEGMENTS: List[Dict[str, Any]]`**

Define segment definitions for local service businesses:

1. **new_leads** — "New leads (last 7 days)"
   - Rules: lifecycle_stage in ["lead", "qualified_lead"] AND created_at days_ago_less_than 7
   - Description: "Contacts who inquired in the last 7 days and haven't been converted yet"

2. **quoted_not_booked** — "Quoted but not booked"
   - Rules: lifecycle_stage equals "prospect" AND custom_fields.quote_sent equals true AND lifecycle_stage not_equals "customer"
   - Description: "Contacts who received a quote but haven't booked yet"

3. **past_customers_90d** — "Recent customers (last 90 days)"
   - Rules: lifecycle_stage in ["customer", "repeat_customer"] AND last_service_date days_ago_less_than 90
   - Description: "Customers who had service in the last 90 days — prime for review requests and referrals"

4. **past_customers_1yr** — "Customers from last year"
   - Rules: lifecycle_stage in ["customer", "repeat_customer"] AND last_service_date days_ago_more_than 90 AND last_service_date days_ago_less_than 365
   - Description: "Customers who had service 3-12 months ago — good for seasonal reminders and reactivation"

5. **dormant_12mo** — "Dormant 12+ months"
   - Rules: last_engaged_at days_ago_more_than 365 OR (last_service_date days_ago_more_than 365 AND lifecycle_stage not_equals "churned")
   - Description: "Contacts with no engagement in 12+ months — candidates for reactivation or list cleanup"

6. **high_value_customers** — "High-value customers"
   - Rules: total_revenue greater_than 1000 AND lifecycle_stage in ["customer", "repeat_customer"]
   - Description: "Customers with high lifetime value — prioritize for VIP treatment, referral asks, and retention"

7. **referral_sources** — "Active referrers"
   - Rules: referral_count greater_than 0 AND lifecycle_stage in ["customer", "repeat_customer", "advocate"]
   - Description: "Customers who have referred others — nurture the relationship and incentivize more referrals"

**Pre-built segments: `ECOMMERCE_SEGMENTS: List[Dict[str, Any]]`**

1. **new_subscribers** — "New subscribers (last 14 days)"
   - Rules: lifecycle_stage equals "subscriber" AND created_at days_ago_less_than 14

2. **first_purchase** — "First-time buyers"
   - Rules: total_purchases equals 1 AND lifecycle_stage equals "customer"
   - Description: "Customers who have made exactly one purchase — critical conversion to repeat"

3. **repeat_buyers** — "Repeat buyers (2+ orders)"
   - Rules: total_purchases greater_than_or_equal 2

4. **cart_abandoners** — "Cart abandoners"
   - Rules: custom_fields.cart_abandoned equals true AND custom_fields.cart_abandoned_at days_ago_less_than 7

5. **dormant_90d** — "Dormant 90+ days"
   - Rules: last_engaged_at days_ago_more_than 90 AND lifecycle_stage not_equals "churned"

6. **vip_customers** — "VIP customers (top 10% by revenue)"
   - Rules: total_revenue greater_than 500 AND total_purchases greater_than_or_equal 3
   - Description: "High-value repeat customers who deserve VIP treatment"

7. **browse_abandoners** — "Browse abandoners"
   - Rules: custom_fields.last_browse_date days_ago_less_than 3 AND total_purchases equals 0

**Pre-built segments: `PROFESSIONAL_SERVICES_SEGMENTS: List[Dict[str, Any]]`**

1. **active_inquiries** — "Active inquiries"
   - Rules: lifecycle_stage in ["lead", "qualified_lead"] AND created_at days_ago_less_than 30

2. **consultation_scheduled** — "Consultation scheduled"
   - Rules: custom_fields.consultation_date is_not_empty AND lifecycle_stage equals "prospect"

3. **past_clients** — "Past clients"
   - Rules: lifecycle_stage in ["customer", "repeat_customer"] AND last_service_date is_not_empty

4. **nurture_leads** — "Long-term nurture"
   - Rules: lifecycle_stage equals "lead" AND created_at days_ago_more_than 30
   - Description: "Leads who haven't converted after 30 days — move to long-term nurture"

**Class: LeadScorer**

Simple lead scoring based on contact attributes and behavior.

Methods:
- `__init__(self, scoring_config: Optional[Dict[str, float]] = None)` — initialize with scoring weights. Use DEFAULT_SCORING_CONFIG if not provided.
- `score_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]`:
  - Calculate lead score based on multiple factors
  - Return: `{"total_score": float, "factors": {"recency": float, "frequency": float, "engagement": float, "fit": float, "value": float}}`
  - Score factors (each 0-20, total 0-100):
    1. **Recency** (0-20): how recently the contact was created or last engaged
       - Last 7 days: 20, Last 14 days: 15, Last 30 days: 10, Last 90 days: 5, 90+ days: 0
    2. **Frequency** (0-20): how often they engage
       - contact_frequency_30d >= 5: 20, >= 3: 15, >= 1: 10, 0: 0
    3. **Engagement** (0-20): depth of engagement
       - Has replied to email: +10, Has opened email: +5, Has clicked: +5
       - Source is referral: +5, Source is phone_call: +5
    4. **Fit** (0-20): how well they match the ICP
       - lifecycle_stage is qualified_lead: 20, lead: 10, subscriber: 5
       - Has phone number: +5, Has company (B2B): +5
    5. **Value** (0-20): monetary potential
       - total_revenue > 1000: 20, > 500: 15, > 100: 10, > 0: 5, 0: 0
       - For leads (no revenue): use average_order_value from business profile as proxy
  - Clamp total to 0-100

**DEFAULT_SCORING_CONFIG dict:**
```python
DEFAULT_SCORING_CONFIG = {
    "recency_weight": 1.0,
    "frequency_weight": 1.0,
    "engagement_weight": 1.0,
    "fit_weight": 1.0,
    "value_weight": 1.0,
    "recency_thresholds": {"hot": 7, "warm": 14, "cool": 30, "cold": 90},
    "frequency_thresholds": {"high": 5, "medium": 3, "low": 1},
    "value_thresholds": {"high": 1000, "medium": 500, "low": 100},
}
```

**Class: SegmentEngine**

Evaluates contacts against segment rules.

Methods:
- `__init__(self)` — initialize
- `evaluate_contact(self, contact: Dict[str, Any], segment: Dict[str, Any]) -> bool`:
  - Evaluate a single contact against a segment's rules
  - If rule_logic is "and": all rules must match
  - If rule_logic is "or": any rule must match
  - For each rule, call `_evaluate_rule()`
  - Return True if contact matches segment

- `filter_contacts(self, contacts: List[Dict[str, Any]], segment: Dict[str, Any]) -> List[Dict[str, Any]]`:
  - Filter a list of contacts through a segment
  - Return matching contacts

- `_evaluate_rule(self, contact: Dict[str, Any], rule: Dict[str, Any]) -> bool`:
  - Get the field value from contact (support nested fields via dot notation: "custom_fields.quote_sent")
  - Apply the operator:
    - `equals`: value == rule_value
    - `not_equals`: value != rule_value
    - `contains`: rule_value in value (for strings/lists)
    - `greater_than`: value > rule_value
    - `less_than`: value < rule_value
    - `in_list`: value in rule_value (rule_value is a list)
    - `is_empty`: value is None or empty
    - `is_not_empty`: value is not None and not empty
    - `before`: parse as date, compare
    - `after`: parse as date, compare
    - `days_ago_more_than`: date is more than X days in the past
    - `days_ago_less_than`: date is less than X days in the past
  - Handle type coercion (string to number, string to date)
  - Return True if rule matches, False otherwise

- `_get_nested_field(self, obj: Dict[str, Any], field_path: str) -> Any`:
  - Support dot notation: "custom_fields.quote_sent" -> obj["custom_fields"]["quote_sent"]
  - Return None if path doesn't exist

- `refresh_segment_count(self, segment: Dict[str, Any], contacts: List[Dict[str, Any]]) -> int`:
  - Count how many contacts match the segment
  - Update segment.contact_count and segment.last_refreshed
  - Return count

**Helper functions (module-level):**

- `generate_contact_id() -> str` — return `con_{uuid.uuid4().hex[:12]}`
- `generate_segment_id() -> str` — return `seg_{uuid.uuid4().hex[:12]}`
- `get_prebuilt_segments(archetype: str) -> List[Dict[str, Any]]`:
  - Return the appropriate pre-built segments for the archetype
  - "local-service" -> LOCAL_SERVICE_SEGMENTS
  - "ecommerce" -> ECOMMERCE_SEGMENTS
  - "professional-services" -> PROFESSIONAL_SERVICES_SEGMENTS
  - Unknown: return LOCAL_SERVICE_SEGMENTS as default (most common)
- `calculate_days_since(date_str: str) -> int` — days between date_str and now
- `merge_contacts(contact_a: Dict[str, Any], contact_b: Dict[str, Any]) -> Dict[str, Any]`:
  - Merge two contact records (e.g., when a lead becomes a customer)
  - Prefer non-None values, combine tags/lists, sum revenue/purchases
  - Return merged contact

### File: `kai/models/__init__.py` (update)

- Add imports for all new model classes and enums from `contacts.py`
- Add them to `__all__`

## Output Files

- `kai/models/contacts.py`
- `kai/models/__init__.py` (update)

## Acceptance Criteria

- [ ] `LifecycleStage` enum has all 9 stages
- [ ] `ConsentStatus` enum has all 5 statuses
- [ ] `ContactSource` enum has all 14 sources including "kaicalls"
- [ ] `SegmentOperator` enum has all 19 operators including date-specific ones
- [ ] `Contact` model has all 38 fields with correct types and defaults
- [ ] `SegmentRule` model has all 4 fields
- [ ] `Segment` model has all 13 fields including is_dynamic and rule_logic
- [ ] `LOCAL_SERVICE_SEGMENTS` has all 7 pre-built segments with valid rules
- [ ] `ECOMMERCE_SEGMENTS` has all 7 pre-built segments with valid rules
- [ ] `PROFESSIONAL_SERVICES_SEGMENTS` has all 4 pre-built segments
- [ ] `LeadScorer` scores contacts on 5 factors (recency, frequency, engagement, fit, value)
- [ ] `LeadScorer.score_contact()` returns total_score 0-100 with factor breakdown
- [ ] `DEFAULT_SCORING_CONFIG` has all scoring weights and thresholds
- [ ] `SegmentEngine.evaluate_contact()` supports "and" and "or" rule logic
- [ ] `SegmentEngine._evaluate_rule()` handles all 19 operators
- [ ] `SegmentEngine._get_nested_field()` supports dot notation for nested access
- [ ] `get_prebuilt_segments()` returns correct segments per archetype
- [ ] `merge_contacts()` correctly combines two contact records
- [ ] All ID generators use correct prefixes (con_, seg_)
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] `kai/models/__init__.py` exports all new classes

## Reference Materials

- `kai/connectors/lifecycle/base.py` (created by Task 050) — ContactRecord for compatibility alignment
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile.classification.archetype for segment selection
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/channels/email-lifecycle.md` — email lifecycle and segmentation guidance
- `knowledge/playbooks/marketing-automation.md` — automation and segment strategy
- `knowledge/playbooks/customer-retention.md` — retention segment definitions
- `CLAUDE.md` — full project context, KaiCalls recommendation rule

# Task 021: Build CRM and data hygiene audit

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P3
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Marketing is only as good as the data it operates on. A 10,000-person email list with 40% bounce rates and no segmentation is worse than a 500-person clean list with proper tags and consent records. This audit engine examines the health of a business's customer data — list quality, segmentation, deliverability indicators, consent compliance, data completeness, and source tracking. Poor data hygiene leads to email deliverability problems, wasted ad spend on bad audiences, and compliance risks (CAN-SPAM, GDPR, CCPA).

## Scope

Build `kai/audits/crm_hygiene.py` with a CRM and data hygiene audit engine that evaluates customer data quality, compliance readiness, and segmentation health.

## Detailed Requirements

### File: `kai/audits/crm_hygiene.py`

**Function: `audit_crm_hygiene(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. `connected_data` may include CRM exports, email platform metrics (Mailchimp, Klaviyo, ActiveCampaign, etc.), and list analytics.

Since CRM data is rarely available in the BusinessProfile alone, this audit will generate many MISSING_DATA findings when `connected_data` is not provided. That's by design — it tells the operator what data to connect.

**Check 1: Contact List Size**
- If connected_data includes list size:
  - Evaluate against business stage and archetype:
    - Local-service startup: < 100 contacts -> INFO (just starting), 100-500 -> good start, 500+ -> strong foundation
    - Ecommerce: < 1000 -> LOW (small list), 1K-10K -> medium, 10K+ -> good, 50K+ -> strong
    - Professional-services: < 50 -> INFO, 50-200 -> good for B2B, 200+ -> strong
  - Generate finding with context on list size relative to business type
- If not available: MISSING_DATA: "Contact list size unknown — connect your email platform or CRM to assess data health"
- Recommendation: "Track your contact list size monthly. Set growth targets: aim for 3-5% monthly list growth through website capture, social, and event collection."

**Check 2: List Segmentation Quality**
- If connected_data includes segment information:
  - If only one segment (the whole list) -> HIGH: "No list segmentation — sending the same message to everyone reduces engagement and increases unsubscribes"
  - If 2-5 segments -> MEDIUM: "Basic segmentation in place — expand with behavioral and purchase-based segments"
  - If 5+ segments with clear criteria -> INFO: "Strong segmentation structure"
- If not available: MISSING_DATA: "List segmentation data not available"
- Recommended segments by archetype:
  - Local-service: "Active customers, past customers (90+ days), leads (never purchased), service type interest, location"
  - Ecommerce: "First-time buyers, repeat buyers, VIPs (top 10%), cart abandoners, browse abandoners, win-back (90+ days)"
  - Professional-services: "Prospects, active clients, past clients, referral partners, newsletter subscribers, event attendees"

**Check 3: Email Deliverability Indicators**
- If connected_data includes deliverability metrics:
  - Bounce rate: < 2% -> INFO, 2-5% -> MEDIUM, > 5% -> HIGH: "Bounce rate above 5% — list needs cleaning to protect sender reputation"
  - Spam complaint rate: < 0.1% -> INFO, 0.1-0.3% -> MEDIUM, > 0.3% -> CRITICAL: "Spam complaint rate above 0.3% — risk of email provider blacklisting"
  - Inbox placement rate: > 95% -> INFO, 85-95% -> MEDIUM, < 85% -> HIGH
- If not available: MISSING_DATA: "Email deliverability metrics not available — connect your email platform"
- Recommendation: "Monitor bounce rate, spam complaint rate, and inbox placement rate monthly. Clean bounced addresses immediately. Investigate spam complaints for opt-in gaps."

**Check 4: Unsubscribe Rate**
- If connected_data includes unsubscribe rate:
  - < 0.5% per campaign -> INFO: "Healthy unsubscribe rate"
  - 0.5-1% per campaign -> MEDIUM: "Unsubscribe rate is elevated — review email frequency and content relevance"
  - > 1% per campaign -> HIGH: "High unsubscribe rate — either sending too frequently, content is irrelevant, or list was acquired without proper consent"
- If not available: MISSING_DATA
- Recommendation: "If unsubscribe rate is high: (1) Reduce send frequency, (2) Improve segmentation, (3) Review content relevance, (4) Add preference center"

**Check 5: Data Completeness**
- If connected_data includes field completeness metrics:
  - Check what percentage of contacts have: email (should be 100%), phone (target 50%+), source/origin (target 80%+), name (target 90%+)
  - If email completeness < 100% -> WARNING: "Some contacts are missing email addresses"
  - If phone completeness < 30% for local-service -> MEDIUM: "Only {n}% of contacts have phone numbers — phone is a primary communication channel for local service"
  - If source tracking < 50% -> MEDIUM: "Over half of contacts have no source attribution — cannot measure which channels drive the best leads"
- If not available: MISSING_DATA: "Contact data completeness metrics not available"
- Recommendation: "Audit your contact records for completeness. Prioritize: email (required), phone (important for service businesses), lead source (essential for attribution), and last contact date."

**Check 6: Duplicate Detection**
- If connected_data includes duplicate analysis:
  - If > 5% duplicates -> MEDIUM: "Duplicate contacts detected ({n}%) — duplicates waste email sends and skew reporting"
  - If < 5% -> INFO: "Low duplicate rate"
- If not available: MISSING_DATA advisory
- Recommendation: "Run a deduplication process: match on email address first, then phone number, then name + address. Merge duplicates, keeping the most complete record."

**Check 7: Last-Contact Recency Distribution**
- If connected_data includes last contact dates:
  - Calculate distribution: contacts engaged in last 30 days, 90 days, 180 days, 365 days, 365+ days
  - If > 40% of contacts haven't been contacted in 365+ days -> HIGH: "Over 40% of your list is dormant (no contact in 12+ months) — these contacts may be invalid and harm deliverability"
  - If 20-40% dormant -> MEDIUM: "Significant portion of list is dormant"
  - If < 20% dormant -> INFO: "Healthy engagement distribution"
- If not available: MISSING_DATA
- Recommendation: "Segment contacts by last activity: Active (0-90 days), Cooling (90-180 days), Dormant (180-365 days), Dead (365+ days). Create win-back campaigns for Cooling/Dormant. Suppress or remove Dead."

**Check 8: Consent and Opt-In Status**
- If connected_data includes consent records:
  - Check for proper opt-in documentation
  - If any contacts lack consent records -> HIGH: "Contacts without consent records pose compliance risk under CAN-SPAM, GDPR, and CCPA"
  - If all contacts have consent -> INFO: "Consent records present"
- If not available: MEDIUM advisory: "Consent and opt-in status should be tracked for every contact — CAN-SPAM requires demonstrable consent for commercial email, GDPR requires explicit opt-in for EU contacts"
- Compliance specifics:
  - CAN-SPAM: "Every commercial email must include physical address, unsubscribe link, and be sent only to contacts who haven't opted out"
  - GDPR: "EU contacts require explicit opt-in consent with documented proof, right to be forgotten, and data portability"
  - CCPA: "California residents have the right to know what data is collected and request deletion"
- Severity: HIGH for compliance gaps

**Check 9: Data Source Tracking**
- If connected_data includes source attribution:
  - Check what percentage of contacts have a known source
  - If > 80% have source -> INFO: "Strong source tracking"
  - If 50-80% -> MEDIUM: "Source tracking gaps — {n}% of contacts have unknown origin"
  - If < 50% -> HIGH: "Most contacts have no source attribution — impossible to measure which channels drive the best leads"
- If not available: MISSING_DATA
- Recommended sources to track: "website form", "phone call", "referral", "event", "social media", "paid ad", "organic search", "manual entry"
- Recommendation: "Tag every new contact with their acquisition source at the point of entry. This data is essential for calculating channel ROI."

**Check 10: Overall Data Health Summary**
- Generate a composite finding summarizing overall CRM health
- Categories: "clean" (low bounce, good segmentation, complete data), "needs attention" (some issues), "poor" (multiple critical issues)
- List the top 3 data hygiene actions to take
- Severity: weighted composite of individual findings

**Scoring Function:**

**`score_crm_hygiene(findings: List[AuditFinding]) -> float`**
- Score 0-100 using standard formula
- Weight consent/compliance findings 2x (compliance is non-negotiable)
- Note: if most findings are MISSING_DATA, score should reflect "unknown" not "bad" — set score to 50 (neutral) when > 70% of checks are MISSING_DATA

**Helper: `assess_list_health_tier(bounce_rate: Optional[float], spam_rate: Optional[float], unsub_rate: Optional[float]) -> str`**
- Return "healthy", "at_risk", or "critical" based on available metrics
- healthy: bounce < 2%, spam < 0.1%, unsub < 0.5%
- at_risk: any metric in warning range
- critical: any metric in critical range
- Return "unknown" if all inputs are None

## Output Files

- `kai/audits/crm_hygiene.py`

## Acceptance Criteria

- [ ] `crm_hygiene.py` implements `audit_crm_hygiene()` with all 10 checks
- [ ] Most checks gracefully handle missing `connected_data` by generating MISSING_DATA findings
- [ ] Bounce rate, spam complaint rate, and unsubscribe rate have clear threshold benchmarks
- [ ] Consent/opt-in check references CAN-SPAM, GDPR, and CCPA specifically
- [ ] List segmentation recommendations are archetype-specific
- [ ] Duplicate detection and last-contact recency checks are included
- [ ] Data source tracking check emphasizes attribution importance
- [ ] `score_crm_hygiene()` handles "mostly unknown" case with neutral score (50)
- [ ] `assess_list_health_tier()` helper function classifies overall health
- [ ] Compliance findings weighted 2x in scoring
- [ ] All findings have complete fields and use category = "crm_hygiene" or "data_quality"
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — channels, constraints fields
- `knowledge/checklists/email-checklist.md` — email marketing checklist
- `knowledge/playbooks/marketing-automation.md` — automation and CRM playbook
- `harness/references/advertising-compliance.md` — CAN-SPAM, GDPR, CCPA, COPPA compliance
- `knowledge/channels/email-lifecycle.md` — email lifecycle management

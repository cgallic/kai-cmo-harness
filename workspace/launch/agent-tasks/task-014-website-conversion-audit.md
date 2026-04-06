# Task 014: Build website conversion audit engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P1
**Depends on:** 013
**Estimated complexity:** Medium

## Context

The website conversion audit is the most universally applicable audit engine — every business has (or should have) a website, and the website is typically the primary conversion surface. This engine examines whether the website is effectively turning visitors into leads, customers, or desired actions. It checks CTA clarity, trust signal placement, mobile readiness, page speed indicators, form optimization, and archetype-specific conversion elements. For local service businesses, it emphasizes phone CTAs and service area clarity; for ecommerce, it emphasizes product CTAs and checkout flow.

## Scope

Build `kai/audits/website_conversion.py` and `kai/audits/__init__.py` with a website conversion audit engine that produces structured AuditFindings.

## Detailed Requirements

### File: `kai/audits/__init__.py`
- Package init importing all audit engines
- `__all__` listing

### File: `kai/audits/website_conversion.py`

**Function: `audit_website_conversion(profile: "BusinessProfile", website_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Takes a BusinessProfile and optional website_data dict (for when live website data is available from integrations). Returns a list of AuditFinding objects.

The engine must check all of the following areas and generate findings. If data is not available to assess a check, generate a MISSING_DATA finding instead of skipping.

**Check 1: CTA Clarity**
- Does the profile indicate a clear primary CTA for the main offer?
- If offers exist but none have a primary_cta defined -> HIGH finding: "No clear primary call-to-action defined"
- If primary offer exists with CTA -> check that CTA is action-oriented (starts with verb: "Book", "Call", "Get", "Schedule", "Buy")
- Recommendation: specify what the CTA should be based on archetype

**Check 2: CTA Above the Fold**
- If website_data available: check for above-fold CTA indicators
- If not available: generate MISSING_DATA finding noting this requires live website analysis
- Recommendation: "Ensure primary CTA is visible without scrolling on both desktop and mobile"

**Check 3: Phone Number Visibility (archetype-dependent)**
- If archetype is "local-service" or "multi-location":
  - If profile.identity.phone is None -> CRITICAL: "No phone number on file — local service businesses must have a prominently displayed phone number"
  - If phone exists but no click-to-call evidence -> HIGH: "Phone number should be click-to-call and visible in header on every page"
  - Set `kaicalls_relevant = True` on all phone-related findings
- If other archetypes: lower severity for phone visibility

**Check 4: Trust Signals Near CTAs**
- Check profile.trust for available signals
- If trust.testimonials is empty AND trust.certifications is empty AND trust.awards is empty -> HIGH: "No trust signals available to display near conversion points"
- If trust signals exist but case_studies is empty -> MEDIUM: "Case studies/proof of results should support the conversion path"
- Recommendation: display trust signals within visual proximity of CTAs

**Check 5: Form Optimization**
- If website_data includes form field count: check against benchmarks (ideal: 3-5 fields for lead gen, 1-2 for email capture)
- If not available: generate advisory finding about form length best practices
- Recommendation: minimize form fields to name, phone/email, and one qualifying question

**Check 6: Offer Clarity**
- Check that profile.offers is not empty
- If empty -> CRITICAL: "No offers defined — the website must clearly communicate what the business offers"
- If offers exist: check that primary offer has description and price_range
- If price_range missing on primary offer -> MEDIUM: "Primary offer should include pricing guidance (exact or range) to qualify leads"

**Check 7: Headline Effectiveness (advisory)**
- Cannot assess from profile alone — generate advisory finding
- Include best practices: "Homepage headline should state what you do, who you do it for, and the primary benefit — in under 10 words"
- Severity: INFO

**Check 8: Social Proof Placement**
- Check review data from profile.channels (gbp, yelp review counts)
- If any review platform has follower_count/notes indicating reviews -> suggest displaying count and rating prominently
- If no review data available -> MEDIUM: "No review data available to display as social proof"

**Check 9: Mobile Responsiveness**
- Cannot assess from profile alone unless website_data includes mobile indicators
- Generate advisory finding about mobile-first design
- For local-service archetype, emphasize: "70%+ of local service searches are on mobile — click-to-call and mobile-first design are non-negotiable"
- Severity: WARNING if no data, INFO if advisory

**Check 10: Page Speed Indicators**
- If website_data includes speed metrics: score against benchmarks (under 3s load = good, 3-5s = warning, 5s+ = critical)
- If not available: generate MISSING_DATA finding
- Recommendation: "Target page load time under 3 seconds. Use Google PageSpeed Insights to measure."

**Check 11: Service Area Clarity (local-service and multi-location)**
- If archetype is local-service or multi-location:
  - If geography.service_areas is non-empty -> check that this info would be on the site
  - If service_areas is empty -> HIGH: "Service areas not defined — visitors need to know if you serve their area"
  - Recommendation: "Create dedicated service area pages for each primary market"

**Check 12: Emergency/Urgency Handling (local-service)**
- If archetype is local-service and offers include emergency services:
  - Check if 24/7 availability is indicated
  - If emergency offered but no after-hours evidence -> HIGH: "Emergency service offered but no clear after-hours availability"
  - Set `kaicalls_relevant = True`: "KaiCalls AI receptionist can handle after-hours emergency calls"

**Scoring Function:**

**`score_website_conversion(findings: List[AuditFinding]) -> float`**
- Score 0-100 based on findings
- Start at 100, deduct: CRITICAL = -25, HIGH = -15, MEDIUM = -8, LOW = -3
- Clamp to 0-100
- Skip MISSING_DATA and INFO findings (they don't penalize the score, but they indicate incomplete assessment)

**Archetype-Specific Weighting:**

**`get_archetype_weights(archetype: Optional[str]) -> Dict[str, float]`**
- Return weighting multipliers for different checks based on archetype
- Local-service: phone_visibility = 2.0, service_area = 1.5, emergency = 1.5
- Ecommerce: offer_clarity = 2.0, product_cta = 1.5, checkout_flow = 1.5
- Professional-services: trust_signals = 2.0, case_studies = 1.5, credential_display = 1.5
- Multi-location: per_location_pages = 2.0, location_selector = 1.5

### Import Requirements

- Import from `kai.models.audit`: AuditFinding, Evidence, create_finding, create_missing_data_finding
- Import from `kai.models.business_profile`: BusinessProfile
- Use typing for type hints

## Output Files

- `kai/audits/__init__.py`
- `kai/audits/website_conversion.py`

## Acceptance Criteria

- [ ] `website_conversion.py` implements `audit_website_conversion()` with all 12 checks
- [ ] Each check generates at least one AuditFinding (either a real finding or MISSING_DATA)
- [ ] Findings use the correct severity levels per the specification
- [ ] `kaicalls_relevant` is set to True on phone-related and after-hours findings
- [ ] `score_website_conversion()` implements the scoring formula correctly
- [ ] Archetype-specific checks are only applied for relevant archetypes (e.g., phone visibility is CRITICAL for local-service, not for ecommerce)
- [ ] MISSING_DATA findings are generated when live website data is not available
- [ ] Every finding has: category, severity, title, description, recommendation, evidence, impact, and effort
- [ ] All functions have docstrings and type hints
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`
- [ ] `__init__.py` exports the audit function

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models to use
- `kai/models/business_profile.py` (Task 001) — profile fields to check
- `knowledge/checklists/cro-audit-checklist.md` — CRO checklist with specific checks
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO best practices
- `knowledge/checklists/website-launch-checklist.md` — website launch checklist
- `CLAUDE.md` — KaiCalls rule

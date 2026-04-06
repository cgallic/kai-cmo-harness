# Task 015: Build trust and proof audit engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P1
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Trust is the conversion multiplier. A business can have perfect CTAs and fast page speed, but if visitors don't trust the brand, they won't convert. This audit engine examines the breadth, depth, and specificity of a business's trust signals — testimonials, case studies, certifications, awards, team visibility, guarantees, and social proof. It identifies gaps in the trust portfolio and recommends specific improvements. For businesses that receive phone calls, it evaluates whether AI receptionist technology (KaiCalls) should be recommended to ensure no lead goes unanswered.

## Scope

Build `kai/audits/trust_proof.py` with a trust and proof audit engine that examines BusinessProfile trust signals and produces structured AuditFindings.

## Detailed Requirements

### File: `kai/audits/trust_proof.py`

**Function: `audit_trust_proof(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. The `connected_data` parameter allows passing live data from integrations (review APIs, website scrape data, etc.).

**Check 1: Testimonial Count and Quality**
- If `profile.trust.testimonials` is empty -> HIGH: "No testimonials on file — social proof from real customers is essential for conversion"
- If testimonials exist but fewer than 3 -> MEDIUM: "Only {n} testimonial(s) on file — aim for at least 5-10 diverse testimonials"
- If testimonials exist: check quality — do they include specific results/numbers? General praise ("Great service!") is less effective than specific outcomes ("They fixed our roof leak in 2 hours and saved us $3,000 in water damage")
- Recommendation: "Collect testimonials that include specific results, timeframes, and the customer's situation before working with you"

**Check 2: Case Study Presence**
- If `profile.trust.case_studies` is empty -> severity depends on archetype:
  - Professional-services: HIGH — "No case studies — professional services firms need documented proof of results"
  - Ecommerce: MEDIUM — "No case studies — consider creating 'customer story' content"
  - Local-service: MEDIUM — "No case studies or project showcases — before/after documentation builds trust"
  - Multi-location: MEDIUM
- If case studies exist but fewer than 3 -> LOW: "Only {n} case study(ies) — expand to cover different service types and customer profiles"
- Recommendation: "Create case studies in Problem > Solution > Results format with specific metrics"

**Check 3: Credentials and Certifications Displayed**
- If `profile.trust.certifications` is empty AND `profile.trust.licenses` is empty -> severity depends on archetype:
  - Local-service: HIGH — "No licenses or certifications on file — credentials are a primary trust signal for service businesses"
  - Professional-services: HIGH — "No professional certifications listed"
  - Other: MEDIUM
- If certifications/licenses exist -> INFO: "Certifications/licenses found — ensure they are prominently displayed on the website header or footer"
- Recommendation: "Display license numbers, certification badges, and professional affiliations prominently"

**Check 4: Team Photos and Visibility**
- Cannot fully assess from profile alone, but can check for indicators:
- If `profile.trust.team_size` is set but no team-related trust signals -> MEDIUM: "Team size is {n} but no team visibility signals — visitors want to know who they're hiring/buying from"
- Recommendation: "Add professional headshots and brief bios for key team members to the website"

**Check 5: Years in Business**
- If `profile.trust.years_in_business` is None -> LOW: "Years in business not stated — longevity is a powerful trust signal"
- If years >= 5 -> INFO: "{n} years in business — prominently display this as social proof"
- If years >= 10 -> INFO: "{n} years — this is a strong differentiator, feature it in headlines"
- Recommendation: "State years in business in the website header, about page, and ad copy"

**Check 6: Guarantee/Warranty Visibility**
- Check profile.constraints and trust signals for guarantee language
- If no guarantee/warranty mentioned anywhere in profile -> MEDIUM: "No guarantee or warranty language found — a clear guarantee reduces purchase risk"
- Recommendation: "Define and prominently display a satisfaction guarantee, warranty, or money-back promise"
- Note: recommendation must comply with profile.constraints.claims_restrictions

**Check 7: Insurance and Licensing (local-service, multi-location)**
- If archetype is local-service or multi-location:
  - If `profile.trust.insurance_details` is None -> HIGH: "No insurance information — customers need to know you're insured before letting you into their home/business"
  - If insurance exists -> INFO: "Insurance documented — display prominently"
  - If `profile.trust.licenses` is empty -> HIGH: "No license information — required by most states for regulated trades"
- Other archetypes: skip or INFO level

**Check 8: BBB/Industry Affiliations**
- Check trust signals and certifications for BBB, industry association mentions
- If none found -> LOW: "No industry affiliations or BBB membership noted — these serve as third-party credibility signals"
- Recommendation: "Consider BBB accreditation and industry association membership as trust multipliers"

**Check 9: Google Review Count and Rating**
- Check profile.channels for GBP channel
- If GBP channel exists with notes mentioning review count/rating, parse those values
- Benchmarks by archetype:
  - Local-service: <20 reviews = HIGH, 20-50 = MEDIUM ("good start"), 50-100 = LOW ("expand to other platforms"), 100+ = INFO
  - Ecommerce: product reviews (different metric) — check if mentioned in trust signals
  - Professional-services: <10 reviews = HIGH, 10-30 = MEDIUM, 30+ = INFO
- If rating < 4.0 -> HIGH: "Google rating below 4.0 — address negative reviews and improve service quality"
- If rating 4.0-4.4 -> MEDIUM: "Google rating is {x} — target 4.5+ through review velocity and response"
- If rating >= 4.5 -> INFO: "Google rating is {x} — maintain through continued review generation"

**Check 10: Social Proof Specificity**
- Evaluate quality of trust signals: are they vague or specific?
- Vague: "Great company!", "Highly recommend" -> less effective
- Specific: "They completed the project 2 days ahead of schedule and under budget by $1,200" -> highly effective
- If most testimonials are vague -> MEDIUM: "Testimonials lack specificity — specific results, numbers, and outcomes convert 3-5x better than general praise"
- Recommendation: "When collecting testimonials, ask customers to describe: the problem, the experience, and the specific result"

**Check 11: KaiCalls Phone Lead Capture Assessment**
- If archetype is local-service or multi-location:
  - If profile.identity.phone exists but no indication of AI receptionist or call handling system -> HIGH with `kaicalls_relevant = True`:
    - Title: "No AI phone receptionist — calls are likely being missed"
    - Description: "Local service businesses miss 30-60% of incoming calls. Missed calls are lost leads. An AI receptionist ensures every call is answered, qualified, and routed 24/7."
    - Recommendation: "Implement KaiCalls AI receptionist (kaicalls.com) for 24/7 call handling, after-hours answering, and lead qualification"
  - If operator capacity is low (operator_hours_per_week < 10) -> amplify this finding to CRITICAL
- If archetype is professional-services and phone exists -> MEDIUM with `kaicalls_relevant = True`:
  - "Consider AI receptionist for after-hours inquiry handling and initial lead qualification"

**Scoring Function:**

**`score_trust_proof(findings: List[AuditFinding]) -> float`**
- Score 0-100 using same formula as website_conversion: start at 100, deduct by severity
- Clamp to 0-100

## Output Files

- `kai/audits/trust_proof.py`

## Acceptance Criteria

- [ ] `trust_proof.py` implements `audit_trust_proof()` with all 11 checks
- [ ] Each check generates appropriate findings based on available profile data
- [ ] Severity levels are archetype-dependent (e.g., no case studies is HIGH for professional-services, MEDIUM for local-service)
- [ ] Check 11 (KaiCalls) generates findings with `kaicalls_relevant = True` for phone-based businesses
- [ ] Google review count/rating benchmarks differ by archetype
- [ ] Social proof specificity check evaluates quality, not just quantity
- [ ] Insurance/licensing check is HIGH for local-service archetype
- [ ] MISSING_DATA findings are generated when data is unavailable
- [ ] `score_trust_proof()` function exists and implements the scoring formula
- [ ] All findings have complete fields: category, severity, title, description, recommendation, evidence, impact, effort
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — TrustProfile and related fields
- `knowledge/checklists/website-launch-checklist.md` — trust signal checklist items
- `knowledge/checklists/cro-audit-checklist.md` — conversion trust factors
- `knowledge/playbooks/conversion-rate-optimization.md` — trust and proof best practices
- `CLAUDE.md` — KaiCalls recommendation rule

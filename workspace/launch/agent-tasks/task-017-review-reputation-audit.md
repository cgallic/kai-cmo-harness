# Task 017: Build review and reputation audit engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P2
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Online reviews are the modern word-of-mouth and a direct ranking factor for local search. This audit engine examines the health of a business's review profile across platforms — not just the count and rating, but the velocity (how often new reviews arrive), recency, response behavior, distribution across platforms, and patterns in negative reviews. A business with 100 reviews but zero in the last 6 months has a stale review profile. A business with great reviews on Google but terrible reviews on Yelp has a platform gap. This engine surfaces those patterns.

## Scope

Build `kai/audits/review_reputation.py` with a review and reputation audit engine that analyzes review data from the BusinessProfile and connected sources.

## Detailed Requirements

### File: `kai/audits/review_reputation.py`

**Function: `audit_review_reputation(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. `connected_data` may include live review data from integrations (Google reviews API, Yelp API, etc.).

**Check 1: Google Review Count**
- Parse review count from profile.channels GBP entry notes or from connected_data
- Benchmarks by archetype:
  - Local-service: <10 -> CRITICAL, 10-20 -> HIGH, 20-50 -> MEDIUM, 50-100 -> LOW, 100+ -> INFO
  - Professional-services: <5 -> HIGH, 5-15 -> MEDIUM, 15-30 -> LOW, 30+ -> INFO
  - Multi-location: assess per location (use same local-service thresholds per location)
  - Ecommerce: N/A for Google reviews (product reviews checked separately)
- If no review data available -> MISSING_DATA: "Google review count not available — connect GBP to assess"
- Recommendation: "Target a minimum of 50 Google reviews with a 4.5+ average rating"

**Check 2: Google Review Rating**
- Parse rating from same sources
- Benchmarks:
  - < 3.5 -> CRITICAL: "Google rating is below 3.5 — this actively repels customers and suppresses local ranking"
  - 3.5-3.9 -> HIGH: "Google rating is below 4.0 — address negative reviews and improve service delivery"
  - 4.0-4.4 -> MEDIUM: "Google rating is {x} — target 4.5+ through consistent review generation from satisfied customers"
  - 4.5-4.8 -> LOW: "Strong Google rating of {x} — maintain through continued review requests"
  - 4.9-5.0 -> INFO: "Excellent Google rating of {x} — consider whether this looks authentic (too-perfect ratings can seem fake)"
- Recommendation specific to the rating range

**Check 3: Review Velocity**
- If connected_data includes review dates or velocity metrics: calculate reviews per month
- Benchmarks:
  - < 1 review/month -> HIGH: "Review velocity is stagnant — you need a systematic review request process"
  - 1-3 reviews/month -> MEDIUM: "Review velocity is adequate but could be stronger"
  - 4-10 reviews/month -> LOW: "Good review velocity — maintain current approach"
  - 10+ reviews/month -> INFO: "Excellent review velocity"
- If velocity data not available: generate MISSING_DATA finding
- Recommendation: "Implement an automated review request system — send a text or email within 24 hours of service completion with a direct Google review link"

**Check 4: Review Recency**
- If connected_data includes latest review date: check how recent
- If last review > 90 days ago -> HIGH: "Most recent review is over 3 months old — stale reviews signal a dormant business"
- If last review > 30 days ago -> MEDIUM: "No reviews in the last 30 days — maintain consistent review generation"
- If last review within 7 days -> INFO: "Recent review activity detected"
- If data not available: MISSING_DATA

**Check 5: Response Rate to Reviews**
- If connected_data includes response data:
  - 0% response rate -> HIGH: "No review responses detected — responding to reviews improves ranking and shows you care"
  - < 50% response rate -> MEDIUM: "Only responding to some reviews — aim to respond to every review, positive and negative"
  - 50-90% response rate -> LOW: "Good response habit — close the gap on remaining unresponded reviews"
  - 90%+ response rate -> INFO: "Excellent review response rate"
- If data not available: advisory MEDIUM: "Review response rate unknown — ensure you're responding to every review"

**Check 6: Response Quality (advisory)**
- Cannot fully assess from profile data alone
- Generate advisory INFO finding with best practices:
  - "Positive review responses should: thank the customer by name, reference the specific service, and be personalized (not template)"
  - "Negative review responses should: acknowledge the concern, take the conversation offline, and offer a resolution"
- Recommendation: "Create review response templates for positive, neutral, and negative reviews — but personalize each response"

**Check 7: Review Distribution Across Platforms**
- Check profile.channels for review platforms: gbp, yelp, facebook, industry-specific
- If reviews only exist on one platform -> MEDIUM: "Reviews concentrated on a single platform — diversify across Google, Yelp, and industry platforms"
- If reviews exist on 2+ platforms -> LOW: "Reviews present on multiple platforms — good distribution"
- If no Yelp presence for local-service -> MEDIUM: "No Yelp presence — Yelp is a significant discovery platform for local services"
- For specific industries, check industry platforms (Avvo for lawyers, Healthgrades for doctors, etc.)

**Check 8: Negative Review Patterns**
- If connected_data includes review text or sentiment analysis:
  - Look for recurring themes in negative reviews (response time, pricing, communication, quality)
  - If pattern found -> HIGH: "Negative review pattern detected: {theme}. This is a systemic issue that marketing alone cannot fix."
- If not available: MISSING_DATA with recommendation to manually review last 20 reviews for patterns
- Recommendation: "Categorize negative reviews by theme. If 3+ reviews mention the same issue, it's an operations problem, not a marketing problem."

**Check 9: Review Generation System**
- Check for evidence of a systematic review request process:
  - If profile mentions review request automation or follow-up system -> INFO: "Review generation system appears to be in place"
  - If no evidence of systematic review requests -> HIGH: "No review generation system detected — reviews don't happen organically at scale"
- Recommendation: "Implement automated review requests: send via text/email within 24 hours of service completion, include a direct link, and make it one-click easy"

**Check 10: Multi-Location Review Distribution (multi-location only)**
- If archetype is multi-location:
  - If connected_data has per-location review data: compare across locations
  - Flag locations with significantly fewer reviews than the average
  - Flag locations with ratings significantly below the average
  - Finding: "Location '{name}' has only {n} reviews vs. fleet average of {avg} — underperforming locations drag down the whole brand"
  - Identify strongest and weakest locations by review profile

**Scoring Function:**

**`score_review_reputation(findings: List[AuditFinding]) -> float`**
- Score 0-100 using standard formula
- Weight: review count and rating checks are weighted 2x vs. other checks

**Helper: `parse_review_metrics(profile: "BusinessProfile") -> Dict[str, Any]`**
- Extract review-related data from profile.channels notes and connected_data
- Return dict with: google_review_count, google_review_rating, yelp_review_count, yelp_rating, total_reviews, platforms_with_reviews
- Use regex to parse numbers from channel notes strings (e.g., "87 reviews, 4.7 rating")

## Output Files

- `kai/audits/review_reputation.py`

## Acceptance Criteria

- [ ] `review_reputation.py` implements `audit_review_reputation()` with all 10 checks
- [ ] Google review count benchmarks differ by archetype
- [ ] Google review rating benchmarks cover all ranges (below 3.5 through 5.0)
- [ ] Review velocity check evaluates reviews per month
- [ ] Review response rate check evaluates engagement with reviewers
- [ ] Multi-location check (10) compares review metrics across locations
- [ ] Review generation system check identifies whether automation exists
- [ ] `parse_review_metrics()` extracts data from profile channel notes
- [ ] MISSING_DATA findings are generated when review data is not available from integrations
- [ ] `score_review_reputation()` weights review count and rating 2x
- [ ] All findings have category = "reviews_reputation" and complete fields
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — channels and trust fields
- `knowledge/checklists/local-service-business-checklist.md` — review-related items
- `knowledge/playbooks/conversion-rate-optimization.md` — review impact on conversion
- `kai/archetypes/local_service.py` (Task 006) — review KPI benchmarks

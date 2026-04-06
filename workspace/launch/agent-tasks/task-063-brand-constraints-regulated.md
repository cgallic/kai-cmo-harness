# Task 063: Build brand-specific constraints and regulated-claims handling

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P2
**Depends on:** 061, 001
**Estimated complexity:** Medium

## Context

Beyond platform and legal compliance (which are universal), each individual business has its own constraints — what claims it can and cannot make, how it talks about competitors, what guarantees it offers, which testimonials it has permission to use. The brand constraints layer captures these per-business rules so the creative engine never produces content that contradicts the business's own policies or makes claims the business cannot substantiate. The regulated-claims handler is a content scanner that flags specific language patterns (superlatives, results claims, certifications, guarantees) that need evidence or disclaimers before publishing.

## Scope

Create `kai/compliance/brand_constraints.py` containing the BrandConstraints model loaded from BusinessProfile data, the RegulatedClaimsHandler for detecting and flagging claims in content, and the ClaimFlag model.

## Detailed Requirements

### File: `kai/compliance/brand_constraints.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: CompetitorMentionPolicy**
- `never` — never mention competitors by name
- `comparison_ok` — factual feature comparisons allowed
- `aggressive` — direct competitive positioning allowed

**Enum: ClaimType**
- `superlative` — "best", "fastest", "#1", "leading"
- `results_claim` — specific outcomes with numbers ("lose 10 lbs", "save $5000")
- `certification_claim` — "certified", "licensed", "accredited", "board-certified"
- `guarantee_claim` — "guaranteed", "risk-free", "money back", "100% satisfaction"
- `comparison_claim` — "better than", "unlike competitors", "more than Brand X"
- `endorsement_claim` — "recommended by", "as seen on", "endorsed by"
- `time_claim` — "same-day", "24-hour", "within 1 hour"
- `award_claim` — "award-winning", "voted best", "top rated"

**Model: ApprovedClaim**
- `claim_text: str` — the specific claim (e.g., "Licensed and insured in all 50 states")
- `evidence_source: str` — where the evidence is (e.g., "State licensing database, license #12345")
- `valid_until: Optional[str]` — ISO date when this claim expires (e.g., license renewal date)
- `approved_by: Optional[str]` — who approved this claim
- `content_types_allowed: List[str]` — where this claim can be used (e.g., ["website_page", "paid_ad", "social_post"])

**Model: ProhibitedClaim**
- `claim_pattern: str` — the pattern to avoid (e.g., "cheapest in town", "guaranteed results")
- `reason: str` — why this is prohibited (e.g., "Cannot substantiate lowest price claim")
- `alternative: Optional[str]` — what to say instead (e.g., "competitive pricing" instead of "cheapest")

**Model: RequiredDisclaimer**
- `trigger: str` — what content triggers this disclaimer (e.g., "any pricing mention", "results testimonial")
- `disclaimer_text: str` — the exact disclaimer text
- `placement: str` — "footer", "inline", "adjacent" (next to the triggering content)
- `applicable_to: List[str]` — content types where this applies

**Model: TestimonialPolicy**
- `can_use_customer_names: bool`
- `require_consent_form: bool`
- `anonymous_allowed: bool`
- `video_testimonials_allowed: bool`
- `must_include_disclaimer: bool` — "Results may vary" type disclaimer
- `disclaimer_text: str`
- `max_age_months: Optional[int]` — testimonials older than this should be refreshed
- `approved_testimonials: List[Dict[str, str]]` — list of {customer_name, quote, date, consent_status}

**Model: BrandConstraints**
- `business_id: str`
- `approved_claims: List[ApprovedClaim]`
- `prohibited_claims: List[ProhibitedClaim]`
- `required_disclaimers: List[RequiredDisclaimer]`
- `competitor_mention_policy: str` — CompetitorMentionPolicy enum value
- `named_competitors: List[str]` — specific competitor names (for detection)
- `pricing_display_rules: Dict[str, Any]` — keys: show_exact_prices (bool), show_ranges (bool), starting_from_allowed (bool), free_consultation_allowed (bool), discount_rules (str)
- `guarantee_language: Dict[str, Any]` — keys: can_offer_guarantee (bool), guarantee_text (str), guarantee_terms_url (str), guarantee_duration (str)
- `testimonial_policy: TestimonialPolicy`
- `tone_constraints: Dict[str, Any]` — keys: formality_level ("casual", "professional", "formal"), humor_allowed (bool), emoji_allowed (bool), slang_allowed (bool)
- `content_restrictions: List[str]` — topics to never discuss (e.g., "competitor lawsuits", "pending litigation")

**Function: load_brand_constraints(business_profile: Any) -> BrandConstraints**
- Extract constraint information from a BusinessProfile object
- Set sensible defaults where data is missing:
  - competitor_mention_policy defaults to "never"
  - testimonial_policy defaults to: require_consent_form=True, must_include_disclaimer=True
  - pricing_display_rules defaults to: show_ranges=True, starting_from_allowed=True
  - guarantee_language defaults to: can_offer_guarantee=False
- Return a fully populated BrandConstraints object

**Model: ClaimFlag**
- `claim_text: str` — the detected claim in the content
- `claim_type: str` — ClaimType enum value
- `location: str` — where in the content (e.g., "headline", "body paragraph 2", "CTA")
- `severity: str` — "block" (cannot publish without resolution), "review" (should be reviewed), "info" (awareness only)
- `required_action: str` — what must happen: "add_disclaimer", "provide_evidence", "remove_claim", "get_approval", "verify_current"
- `suggested_disclaimer: Optional[str]` — suggested disclaimer text if applicable
- `matching_approved_claim: Optional[str]` — if this matches an approved claim, reference it
- `matching_prohibited_claim: Optional[str]` — if this matches a prohibited claim, reference it

**Class: RegulatedClaimsHandler**
- `__init__(self, constraints: BrandConstraints)`
- `scan_content(self, content_text: str, content_type: str) -> List[ClaimFlag]`:
  - Scan the text for all claim types
  - Check each detected claim against approved_claims (OK to use) and prohibited_claims (must remove)
  - Return list of ClaimFlag objects
- `_detect_superlatives(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for: "best", "fastest", "cheapest", "#1", "number one", "leading", "top-rated", "premier", "unmatched", "unrivaled", "unparalleled"
  - Return list of (matched_text, position) tuples
- `_detect_results_claims(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for number + outcome patterns: "save $X", "lose X lbs", "increase X%", "earn $X", "reduce X%", "X% faster", "X times more"
  - Return list of (matched_text, position) tuples
- `_detect_certification_claims(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for: "certified", "licensed", "accredited", "board-certified", "registered", "approved", "authorized"
  - Return list of (matched_text, position) tuples
- `_detect_guarantee_claims(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for: "guaranteed", "risk-free", "money back", "100% satisfaction", "no-risk", "zero risk", "free trial"
  - Return list of (matched_text, position) tuples
- `_detect_comparison_claims(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for: "better than", "unlike", "compared to", "more than [CompetitorName]", "outperforms"
  - Also check against named_competitors list from constraints
- `_detect_endorsement_claims(self, text: str) -> List[Tuple[str, int]]`:
  - Pattern match for: "recommended by", "endorsed by", "as seen on", "featured in", "trusted by"
- `_check_against_approved(self, claim_text: str) -> Optional[ApprovedClaim]`:
  - Fuzzy match the detected claim against approved_claims
  - Return the matching ApprovedClaim if found, None otherwise
- `_check_against_prohibited(self, claim_text: str) -> Optional[ProhibitedClaim]`:
  - Match the detected claim against prohibited_claims
  - Return the matching ProhibitedClaim if found, None otherwise

## Output Files

- `kai/compliance/brand_constraints.py`

## Acceptance Criteria

- File parses as valid Python
- All models are complete dataclasses with SerializableModel mixin
- `RegulatedClaimsHandler.scan_content()` detects all six claim types with reasonable regex patterns
- Detection methods use `re` module for pattern matching (not just simple string `in` checks)
- Each detection method returns (text, position) tuples for precise location reporting
- `_check_against_approved` and `_check_against_prohibited` perform case-insensitive matching
- `load_brand_constraints` sets sensible defaults and handles missing BusinessProfile fields
- ClaimFlag correctly classifies severity: prohibited claims → "block", unsubstantiated claims → "review", matched approved claims → "info"
- Competitor name detection works against the `named_competitors` list
- No external dependencies beyond `re` and stdlib

## Reference Materials

- `kai/compliance/policy_packs/base.py` (Task 061) — PolicyRule, severity levels
- `kai/runtime/business_profile.py` — BusinessProfile structure for load_brand_constraints
- `kai/runtime/models.py` — SerializableModel pattern
- `harness/references/advertising-compliance.md` — FTC endorsement guidelines, claim substantiation
- `harness/references/google-ads-policy-reference.md` — claim requirements for Google Ads
- `harness/references/meta-ads-rules.md` — personal attributes, before/after restrictions

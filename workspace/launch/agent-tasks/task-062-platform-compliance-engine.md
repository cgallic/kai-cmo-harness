# Task 062: Build platform-specific compliance rule engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P1
**Depends on:** 061
**Estimated complexity:** Large

## Context

The policy packs (Task 061) define what rules exist. This compliance engine decides which rules apply to a given piece of content and evaluates them, producing a structured ComplianceResult with pass/fail status, specific violations, and fix suggestions. This engine is the automated gatekeeper that runs before any content is published or any ad is submitted — it catches policy violations before they reach the platform and get rejected (or worse, violate regulations). The compliance engine is invoked by the creative QA pipeline (Task 031), the approval router (Task 064), and the watcher system (Task 067).

## Scope

Create `kai/compliance/engine.py` containing the ComplianceEngine class, ComplianceResult model, Violation model, regulated-industry handling, and rule evaluation logic.

## Detailed Requirements

### File: `kai/compliance/engine.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: ComplianceStatus**
- `pass` — all rules pass, content is safe to publish
- `fail` — one or more violation-severity rules failed
- `warning` — no violations but one or more warnings exist
- `error` — could not evaluate (missing data, engine error)

**Model: Violation**
- `rule_id: str` — which PolicyRule was violated
- `severity: str` — "violation", "warning", "recommendation"
- `description: str` — human-readable description of the violation
- `content_snippet: Optional[str]` — the specific part of the content that triggered the violation (max 200 chars)
- `fix_suggestion: str` — what to do to fix it
- `regulatory_reference: Optional[str]` — e.g., "CAN-SPAM Act, 15 U.S.C. 7701"
- `auto_fixable: bool` — whether the system can attempt to fix this automatically
- `fix_template: Optional[str]` — template for auto-fix if applicable

**Model: RequiredDisclosure**
- `disclosure_type: str` — e.g., "unsubscribe_link", "physical_address", "sponsored_tag", "results_disclaimer"
- `disclosure_text: str` — the actual text that must be included
- `placement: str` — where it must appear: "header", "footer", "inline", "beginning", "end"
- `source_rule_id: str` — which rule requires this

**Model: ComplianceResult**
- `id: str` — format `comp_{uuid_hex[:12]}`
- `status: str` — ComplianceStatus enum value
- `content_type: str` — what was checked
- `platform: Optional[str]` — target platform if applicable
- `industry: Optional[str]` — business industry
- `region: Optional[str]` — target region
- `checked_at: str` — ISO timestamp
- `total_rules_checked: int`
- `violations: List[Violation]` — violation-severity failures
- `warnings: List[Violation]` — warning-severity issues
- `recommendations: List[Violation]` — recommendation-severity suggestions
- `required_disclosures: List[RequiredDisclosure]` — disclosures that must be included
- `required_modifications: List[str]` — specific changes needed before publishing
- `summary: str` — one-sentence summary (e.g., "3 violations found: missing unsubscribe link, prohibited health claim, missing physical address")

**Model: ContentForReview**
- `content_type: str` — ContentType enum value from policy_packs
- `platform: Optional[str]` — target platform (e.g., "google_ads", "meta", "email")
- `headline: Optional[str]`
- `body: str` — main content text
- `cta: Optional[str]`
- `image_description: Optional[str]` — description of visual content if any
- `landing_page_url: Optional[str]`
- `target_audience: Optional[str]` — audience description for audience-restriction checks
- `claims: List[str]` — explicit claims made in the content
- `industry: Optional[str]`
- `region: Optional[str]`
- `metadata: Dict[str, Any]`

**Class: ComplianceEngine**
- `__init__(self, registry: PolicyRegistry)` — takes the policy registry from Task 061
- `check_compliance(self, content: ContentForReview) -> ComplianceResult`:
  - Determine applicable rules from registry based on content.content_type, content.platform, content.region, content.industry
  - Run each rule's check logic (see evaluation methods below)
  - Compile violations, warnings, recommendations
  - Determine required disclosures
  - Set status: "fail" if any violations, "warning" if only warnings, "pass" otherwise
  - Generate summary string
- `_evaluate_rule(self, rule: PolicyRule, content: ContentForReview) -> Optional[Violation]`:
  - Dispatch to the appropriate check method based on rule.check_function_name
  - Return Violation if rule fails, None if it passes
  - If the check_function_name is not implemented, log and skip (do not crash)
- `_get_required_disclosures(self, applicable_rules: List[PolicyRule], content: ContentForReview) -> List[RequiredDisclosure]`:
  - Based on content type and platform, determine which disclosures are needed
  - E.g., email → unsubscribe link + physical address, sponsored social → #ad disclosure

**Check methods** (implement as private methods on ComplianceEngine):
- `_check_banned_words(self, content: ContentForReview) -> Optional[Violation]` — check for prohibited words/phrases per platform
- `_check_claims_substantiation(self, content: ContentForReview) -> Optional[Violation]` — check for superlative or results claims without evidence
- `_check_personal_attributes(self, content: ContentForReview) -> Optional[Violation]` — Meta-specific: check for "Are you..." / "Do you..." personal attribute phrasing
- `_check_before_after(self, content: ContentForReview) -> Optional[Violation]` — check for before/after claims in restricted platforms
- `_check_special_ad_category(self, content: ContentForReview) -> Optional[Violation]` — Meta: check if content falls under housing/employment/credit categories
- `_check_disclosure_present(self, content: ContentForReview, required_disclosure: str) -> Optional[Violation]` — check if required disclosure text is in the content
- `_check_unsubscribe_link(self, content: ContentForReview) -> Optional[Violation]` — email: check for unsubscribe mechanism
- `_check_physical_address(self, content: ContentForReview) -> Optional[Violation]` — email: check for physical address
- `_check_misleading_subject(self, content: ContentForReview) -> Optional[Violation]` — email: check for deceptive subject lines

**Regulated industry handling** (private methods):
- `_get_healthcare_rules(self) -> List[PolicyRule]` — HIPAA considerations, medical claims restrictions, before/after image bans, testimonial restrictions for health products
- `_get_financial_rules(self) -> List[PolicyRule]` — SEC/FINRA disclaimers, APR disclosures, risk warnings, past performance disclaimers
- `_get_legal_rules(self) -> List[PolicyRule]` — bar association rules, no guarantee of outcomes, jurisdiction requirements, prior results disclaimers
- `_get_real_estate_rules(self) -> List[PolicyRule]` — Fair Housing Act, Equal Opportunity logo, MLS compliance, accurate property descriptions
- `_get_alcohol_cannabis_rules(self) -> List[PolicyRule]` — age-gating requirements, jurisdiction restrictions, no health claims, responsible drinking messaging
- Each function returns a list of PolicyRule objects specific to that industry

**Function: get_industry_rules(industry: str) -> List[PolicyRule]**
- Static/module-level function that routes to the correct industry rule set
- Returns empty list for unrecognized industries

## Output Files

- `kai/compliance/engine.py`

## Acceptance Criteria

- File parses as valid Python
- `ComplianceEngine.check_compliance()` correctly filters applicable rules from the registry
- All nine `_check_*` methods are implemented with realistic checking logic (string matching, pattern detection)
- `_check_personal_attributes` catches Meta-prohibited patterns like "Are you struggling with..."
- `_check_claims_substantiation` detects superlatives ("best", "#1", "fastest") and results claims with numbers
- Healthcare, financial, legal, real estate, alcohol/cannabis industry rules each return at least 5 rules
- `ComplianceResult` correctly sets status based on the presence of violations vs warnings
- `_evaluate_rule` gracefully handles unknown check_function_name without crashing
- Required disclosures are correctly determined for email (CAN-SPAM) and social (FTC)
- All models use SerializableModel mixin

## Reference Materials

- `kai/compliance/policy_packs/base.py` (Task 061) — PolicyRule, PolicyPack, PolicyRegistry
- `kai/compliance/policy_packs/paid_media.py` (Task 061) — paid media rules
- `kai/compliance/policy_packs/email.py` (Task 061) — email rules
- `harness/references/advertising-compliance.md` — comprehensive compliance reference
- `harness/references/meta-ads-rules.md` — Meta personal attributes ban, Special Ad Categories
- `harness/references/google-ads-policy-reference.md` — Google Ads claim substantiation
- `kai/runtime/models.py` — SerializableModel pattern

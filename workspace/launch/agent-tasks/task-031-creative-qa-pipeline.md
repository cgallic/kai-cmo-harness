# Task 031: Build creative QA pipeline

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P2
**Depends on:** 028
**Estimated complexity:** Medium

## Context

Every piece of creative output — whether copy, ad, email, or social post — must pass quality checks before it reaches the operator or gets published. The creative QA pipeline orchestrates multiple checks: brand voice consistency, claim safety (no unsubstantiated superlatives, no medical/legal claims without disclaimers), platform fit (character limits, image ratios, policy compliance), offer/message consistency (CTA matches the offer, pricing is consistent), and regulatory compliance (FTC, GDPR, CAN-SPAM, platform-specific TOS).

This module defines the checks as structured rules, not as script executions. It produces a QAResult that tells the operator exactly what passed, what failed, and how to fix each failure. It also serves as the integration point with the existing quality gate scripts in `scripts/quality_gates/`.

## Scope

Build `kai/creative/qa_pipeline.py` containing QA check definitions, a QAResult model, and an orchestrator function that runs all applicable checks on a piece of creative output. All checks are rule-based evaluations — they define what to check and how, but do not execute external scripts.

## Detailed Requirements

### File: `kai/creative/qa_pipeline.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: QACheckType**
- `brand_voice` — does the content match the business's tone and voice?
- `claim_safety` — are there unsubstantiated or legally risky claims?
- `platform_fit` — does content meet platform-specific requirements?
- `message_consistency` — is the CTA, offer, and messaging consistent?
- `compliance` — does content comply with regulatory and platform policies?
- `four_us` — Four U's quality score (Unique, Useful, Ultra-specific, Urgent)
- `banned_words` — check for banned/rejected words
- `seo_lint` — SEO-specific writing rule checks
- `ai_slop` — detect AI-generated filler phrases

**Enum: QAStatus**
- `passed` — all checks passed
- `failed` — one or more checks failed
- `warning` — no hard failures, but some warnings
- `skipped` — check was not applicable

**Model: QACheckResult**
- `check_type: str` — QACheckType value
- `status: str` — QAStatus value
- `score: Optional[float]` — numeric score if applicable (e.g., Four U's score 0-16)
- `threshold: Optional[float]` — required threshold if applicable
- `passed: bool` — simple pass/fail
- `findings: List[Dict[str, Any]]` — specific issues found, each with:
  - `issue: str` — description of the problem
  - `location: Optional[str]` — where in the content (line number, section name, field name)
  - `severity: str` — "error" (must fix), "warning" (should fix), "info" (nice to fix)
  - `suggestion: str` — specific fix recommendation
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: QAResult**
- `id: str` — unique identifier, format `qa_{uuid_hex[:12]}`
- `content_id: str` — ID of the CopyOutput or asset being checked
- `brief_id: str` — ID of the CreativeBrief
- `checks: List[QACheckResult]` — results for each check, default empty list
- `overall_status: str` — QAStatus value (worst status among all checks)
- `total_checks: int` — number of checks run
- `passed_checks: int` — number of checks that passed
- `failed_checks: int` — number of checks that failed
- `fix_suggestions: List[str]` — ordered list of what to fix, most important first, default empty list
- `approved_for_publishing: bool` — True only if all required checks passed, default False
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Brand Voice Check:**

`check_brand_voice(content: str, brand_voice: Dict[str, Any]) -> Dict[str, Any]`
- Takes content text and BrandVoice dict from BusinessProfile
- Checks:
  - Tone alignment: does the content use language consistent with `tone_descriptors`? Define keyword patterns for each common tone descriptor:
    - "professional": avoid slang, emojis, excessive exclamation marks
    - "casual": can use contractions, conversational phrasing
    - "warm": personal pronouns, empathy language ("we understand", "you deserve")
    - "direct": short sentences, imperatives, no hedging language ("might", "perhaps", "maybe")
    - "authoritative": data citations, definitive statements, expert language
    - "approachable": questions, inclusive language ("we", "together")
    - "playful": wordplay allowed, lighter tone, emoji acceptable
    - "formal": no contractions, complete sentences, no slang
  - Personality check: does the content avoid traits NOT in `personality_traits`? (e.g., if "humorous" is not listed, flag jokes)
  - Competitor differentiation: does the content reflect the brand's unique positioning?
- Return QACheckResult dict

**Claim Safety Check:**

`check_claim_safety(content: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
- Scan content for potentially risky claims:
  - **Superlatives without proof**: "best", "fastest", "cheapest", "#1", "leading" — flag unless backed by a specific citation in the content
  - **Medical claims**: "cure", "treat", "diagnose", "prevent", "heal" + disease/condition names — flag always for non-medical businesses
  - **Legal claims**: "guaranteed results", "100% success rate", "never lose" — flag in legal context
  - **Financial claims**: "guaranteed returns", "risk-free investment", "earn $X" — flag always
  - **Absolute claims**: "always", "never", "every time", "zero risk" — flag and suggest qualification
  - **Comparison claims**: "better than [competitor]", "unlike [competitor]" — flag for substantiation
  - **Income/results claims**: specific dollar amounts, percentages — flag unless cited
  - **Testimonial claims**: individual results presented as typical — flag, needs "results may vary" disclaimer
- If `constraints` is provided (from BusinessProfile.constraints):
  - Check against `claims_restrictions` — flag any restricted claims
  - If `regulated_industry` is True, flag all medical/legal/financial claims regardless
- Return QACheckResult dict with each flagged claim as a finding

**Platform Fit Check:**

`check_platform_fit(content: Dict[str, Any], platform: str, content_type: str) -> Dict[str, Any]`
- Check content against platform constraints (from PLATFORM_CONSTRAINTS in brief.py):
  - Character limits: check each text field against the platform's limit
  - Image dimensions: verify dimensions match platform requirements
  - Hashtag limits: check count against platform max
  - Video duration: check against platform limits
  - Policy-specific content rules:
    - Meta: no before/after images for weight loss, no personal attributes ("You are overweight")
    - Google: no superlatives without qualification, healthcare/finance disclosures
    - TikTok: AI content disclosure required, no political ads
    - Pinterest: no weight loss ads (with narrow exceptions)
    - LinkedIn: professional context required
- Return QACheckResult dict with specific over-limit or policy-violation findings

**Message Consistency Check:**

`check_message_consistency(content: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]`
- Verify the content is internally consistent and matches the brief:
  - CTA matches: does the content's CTA match `brief.cta`? Is there only one primary CTA?
  - Offer consistency: if the brief specifies an offer, does the content mention it? Is pricing consistent?
  - Key message presence: does `brief.key_message` appear (or a close paraphrase) in the content?
  - Persona alignment: does the language match the target persona's vocabulary and pain points?
  - Keyword presence: if `brief.target_keyword` is set, does it appear in the content?
- Return QACheckResult dict

**Compliance Check:**

`check_compliance(content: str, platform: str, content_type: str, regulated_industry: bool = False) -> Dict[str, Any]`
- Check against general compliance rules:
  - **FTC**: are material connections disclosed? ("sponsored", "ad", "partner" for paid content). Are testimonials properly attributed?
  - **CAN-SPAM** (email only): is there an unsubscribe mechanism mentioned? Physical address? Accurate subject line?
  - **GDPR** (if targeting EU): consent language, data handling disclosure
  - **COPPA**: flag if content could target children under 13
  - **Click-to-cancel** (FTC rule): if content promotes a subscription, is cancellation mentioned?
- Platform-specific compliance (reference harness/references/ policy files):
  - Return the relevant policy file path for the platform so the execution layer can load and check it
- If `regulated_industry`:
  - Flag any claims that need disclaimers
  - Require disclosure language for healthcare, financial, legal services
- Return QACheckResult dict

**Quality Gate Integration:**

`check_quality_gates(content: str, brief: Dict[str, Any]) -> Dict[str, Any]`
- Define checks against the existing quality gate scripts:
  - **Four U's**: reference `scripts/quality_gates/four_us_score.py`, threshold from `brief.quality_gate_thresholds.four_us_min`
  - **Banned words**: reference `scripts/quality_gates/banned_word_check.py`
  - **SEO lint**: reference `scripts/quality_gates/seo_lint.py`, only if `brief.quality_gate_thresholds.seo_lint` is True
- Return a dict describing which checks to run and their thresholds
- NOTE: This does NOT execute the scripts. It returns the check plan.
- Additionally, perform inline checks that can be done without executing scripts:
  - **Banned word scan**: check content against the BANNED_WORDS list (Tier 1 from CLAUDE.md): "leverage", "utilize", "synergy", "innovative", "deep dive", "circle back", "touch base", "moving forward", "at the end of the day"
  - **AI slop scan**: check for AI filler phrases: "In conclusion", "It's important to note", "In today's rapidly evolving", "This comprehensive guide", "Without further ado", "It's worth noting that"
  - Return inline scan results as QACheckResult dicts

**Main orchestrator:**

`run_qa_pipeline(content: Dict[str, Any], brief: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
- Determine which checks apply based on content format and brief:
  - brand_voice: always (if business_profile has brand_voice)
  - claim_safety: always
  - platform_fit: if content targets a specific platform
  - message_consistency: always
  - compliance: always
  - banned_words: always (inline)
  - ai_slop: always (inline)
  - four_us: always (reference only — returns script path and threshold)
  - seo_lint: only for SEO content (reference only)
- Run all applicable checks
- Aggregate results into QAResult
- Compute overall_status (worst of all check statuses)
- Generate fix_suggestions ordered by severity (errors first, then warnings)
- Set approved_for_publishing = True only if no "error" severity findings
- Return QAResult dict

**Constants:**

```python
BANNED_WORDS_TIER1 = [
    "leverage", "utilize", "synergy", "innovative", "deep dive",
    "circle back", "touch base", "moving forward", "at the end of the day",
]

AI_SLOP_PHRASES = [
    "in conclusion",
    "it's important to note",
    "in today's rapidly evolving",
    "this comprehensive guide",
    "without further ado",
    "it's worth noting that",
    "in the ever-changing landscape",
    "it goes without saying",
    "needless to say",
    "at its core",
]

SUPERLATIVE_PATTERNS = [
    r"\bbest\b", r"\b#1\b", r"\bnumber one\b", r"\bfastest\b",
    r"\bcheapest\b", r"\bleading\b", r"\btop-rated\b", r"\bworld-class\b",
    r"\bunmatched\b", r"\bunparalleled\b", r"\bguaranteed\b",
]
```

## Output Files

- `kai/creative/qa_pipeline.py`

## Acceptance Criteria

- [ ] `qa_pipeline.py` contains QACheckType, QAStatus enums with all listed values
- [ ] QACheckResult and QAResult models have all specified fields
- [ ] check_brand_voice evaluates content against tone_descriptors with keyword patterns for 8+ tones
- [ ] check_claim_safety detects superlatives, medical, legal, financial, absolute, and comparison claims
- [ ] check_platform_fit validates against character limits, dimension requirements, and platform policies
- [ ] check_message_consistency verifies CTA, offer, key message, persona, and keyword alignment
- [ ] check_compliance covers FTC, CAN-SPAM, GDPR, COPPA, and click-to-cancel rules
- [ ] check_quality_gates references quality gate scripts by path without executing them
- [ ] Inline banned word and AI slop scans use regex pattern matching against defined word lists
- [ ] run_qa_pipeline orchestrates all applicable checks and produces aggregated QAResult
- [ ] fix_suggestions are ordered by severity (errors first)
- [ ] approved_for_publishing is False if any error-severity findings exist
- [ ] BANNED_WORDS_TIER1 matches CLAUDE.md banned word list exactly
- [ ] AI_SLOP_PHRASES matches CLAUDE.md AI slop detection list
- [ ] All functions are pure — no script execution, no file I/O, no network calls

## Reference Materials

- `kai/creative/copy_engine.py` (created by Task 028) — CopyOutput schema that this module checks
- `kai/creative/brief.py` (created by Task 027) — CreativeBrief schema with quality_gate_thresholds
- `kai/models/business_profile.py` (created by Task 001) — BrandVoice, BusinessConstraints
- `scripts/quality_gates/four_us_score.py` — Four U's scoring script (reference path only)
- `scripts/quality_gates/banned_word_check.py` — Banned word check script (reference path only)
- `scripts/quality_gates/seo_lint.py` — SEO lint script (reference path only)
- `harness/references/advertising-compliance.md` — FTC, GDPR, CAN-SPAM, COPPA rules
- `harness/references/google-ads-policy-reference.md` — Google Ads policies
- `harness/references/meta-ads-rules.md` — Meta ads policies
- `harness/references/tiktok-ads-policy-reference.md` — TikTok ads policies
- `CLAUDE.md` — banned words list, AI slop phrases, quality gate rules

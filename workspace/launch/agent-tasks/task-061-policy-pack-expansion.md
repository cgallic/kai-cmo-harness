# Task 061: Expand policy packs

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

Kai generates marketing content across multiple channels — websites, social media, paid ads, email, and analytics/tracking. Each channel has specific legal and platform compliance requirements. The policy pack system encodes these rules as structured, programmatic objects so the compliance engine (Task 062) can automatically check content before it ships. This prevents costly ad disapprovals, legal violations, and brand reputation damage. The existing harness references (e.g., `harness/references/advertising-compliance.md`) contain the raw knowledge; this task translates that knowledge into code-queryable rule sets.

## Scope

Create `kai/compliance/policy_packs/` module with five policy pack files (website, social, paid_media, email, analytics) plus a base PolicyRule model and a policy registry. Each pack contains structured rules extracted from the existing harness reference documents.

## Detailed Requirements

### File: `kai/compliance/__init__.py`
- Module docstring explaining the compliance layer
- Export key classes

### File: `kai/compliance/policy_packs/__init__.py`
- Export all policy pack classes and the PolicyRule model
- Export the `PolicyRegistry` class

### File: `kai/compliance/policy_packs/base.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: RuleSeverity**
- `violation` — must be fixed before publishing; failure to comply creates legal/platform risk
- `warning` — should be fixed; creates compliance risk but may not be immediately actionable
- `recommendation` — best practice; suggested but not strictly required

**Enum: ContentType**
- `website_page`, `landing_page`, `blog_post`, `social_post`, `social_story`, `paid_ad`, `email_marketing`, `email_transactional`, `press_release`, `video_script`, `podcast_script`, `case_study`, `testimonial`, `review_response`

**Model: PolicyRule**
- `rule_id: str` — unique identifier (e.g., "website_accessibility_001")
- `pack: str` — which policy pack this belongs to ("website", "social", "paid_media", "email", "analytics")
- `category: str` — grouping within the pack (e.g., "accessibility", "privacy", "disclosure")
- `description: str` — what this rule requires (1-2 sentences)
- `check_function_name: str` — name of the function that would check this rule (e.g., "check_alt_text_present")
- `severity: str` — RuleSeverity enum value
- `applicable_content_types: List[str]` — which ContentType values this rule applies to
- `applicable_regions: List[str]` — ISO country codes where this rule applies (empty list = global)
- `applicable_industries: List[str]` — industry slugs where this rule applies (empty list = all)
- `regulatory_source: Optional[str]` — which law/regulation/policy this comes from (e.g., "ADA", "GDPR", "FTC Act")
- `fix_guidance: str` — what to do if the rule is violated
- `examples: List[Dict[str, str]]` — list of {violation: str, correction: str} examples

**Class: PolicyPack**
- `pack_name: str`
- `description: str`
- `rules: List[PolicyRule]`
- `get_rules_for_content_type(self, content_type: str) -> List[PolicyRule]` — filter rules by content type
- `get_rules_for_region(self, region: str) -> List[PolicyRule]` — filter rules by region (include global rules)
- `get_rules_for_industry(self, industry: str) -> List[PolicyRule]` — filter rules by industry (include universal rules)
- `get_rules_by_severity(self, severity: str) -> List[PolicyRule]` — filter rules by severity

**Class: PolicyRegistry**
- `_packs: Dict[str, PolicyPack]` — registry of all loaded policy packs
- `register(self, pack: PolicyPack)` — add a policy pack
- `get_pack(self, pack_name: str) -> Optional[PolicyPack]` — retrieve by name
- `get_all_rules(self) -> List[PolicyRule]` — all rules across all packs
- `get_applicable_rules(self, content_type: str, platform: Optional[str] = None, region: Optional[str] = None, industry: Optional[str] = None) -> List[PolicyRule]` — filtered rules

### File: `kai/compliance/policy_packs/website.py`

**Function: build_website_policy_pack() -> PolicyPack**
Rules to include (minimum 15 rules):
- **Accessibility** (severity: warning/violation):
  - All images must have alt text (ADA/WCAG)
  - Color contrast must meet WCAG AA (4.5:1 for text)
  - Forms must have labeled inputs
  - Interactive elements must be keyboard-accessible
  - Page must have a logical heading hierarchy (h1 -> h2 -> h3)
- **Privacy** (severity: violation):
  - Privacy policy link must be present on every page with data collection
  - Cookie consent banner required for EU visitors (GDPR)
  - CCPA opt-out link required for California visitors
  - Data collection forms must state what data is used for
- **Content claims** (severity: warning):
  - Superlative claims ("best", "fastest", "#1") must have substantiation
  - Testimonials must be real and attributable
  - Results claims must include typical results disclaimer
  - Pricing must be accurate and current
- **Contact information** (severity: recommendation):
  - Business phone number visible on every page
  - Physical address visible (required for local businesses)
  - Contact form or chat accessible from every page

### File: `kai/compliance/policy_packs/social.py`

**Function: build_social_policy_pack() -> PolicyPack**
Rules (minimum 15 rules):
- **FTC disclosure**: sponsored content must disclose partnership (#ad, #sponsored, paid partnership tag)
- **Contest/sweepstakes**: must include official rules, no purchase necessary, void where prohibited
- **Employee social**: employee posts about the company must disclose employment
- **User content reposting**: must have permission or proper attribution
- **Influencer disclosure**: FTC requires clear disclosure of material connections
- **Platform-specific**: Facebook community standards, Instagram content policy, LinkedIn professional context, TikTok community guidelines, X/Twitter rules
- **Before/after**: restrictions on before/after content (varies by platform)
- **Testimonials on social**: must represent typical results
- **Political/social issue content**: additional rules apply
- **Age-restricted content**: alcohol, gambling content has platform-specific age gating

### File: `kai/compliance/policy_packs/paid_media.py`

**Function: build_paid_media_policy_pack() -> PolicyPack**
Rules (minimum 20 rules, drawing from existing harness references):
- **Google Ads**: healthcare certification requirements, financial disclosures, no superlatives without proof, trademark rules, destination requirements
- **Meta Ads**: Special Ad Categories (housing, employment, credit), no before/after images in health, personal attributes ban ("Are you struggling with..."), lead ad data handling
- **TikTok**: no political ads, weight management restrictions, AI content disclosure required
- **LinkedIn**: professional context required, B2B claim substantiation
- **General**: FTC endorsement guidelines, comparative advertising rules, bait-and-switch prohibition
- **Landing page alignment**: ad claims must match landing page content
- **Prohibited categories**: platform-specific prohibited product/service categories

### File: `kai/compliance/policy_packs/email.py`

**Function: build_email_policy_pack() -> PolicyPack**
Rules (minimum 15 rules):
- **CAN-SPAM** (US): physical address required, unsubscribe link required, unsubscribe honored within 10 days, no misleading subject lines, no misleading "From" name, identify message as ad
- **GDPR** (EU): explicit consent required before sending marketing email, consent must be freely given and specific, right to erasure (remove from list on request), data processing records
- **CCPA** (California): opt-out of sale of personal information, privacy notice at collection
- **CASL** (Canada): express consent required (implied consent for 2 years after purchase), sender identification, unsubscribe mechanism
- **Double opt-in**: required in Germany, recommended elsewhere for GDPR compliance
- **Transactional vs marketing**: clear classification rules (transactional does not need marketing consent but cannot contain marketing content beyond minimal upsell)

### File: `kai/compliance/policy_packs/analytics.py`

**Function: build_analytics_policy_pack() -> PolicyPack**
Rules (minimum 10 rules):
- **GDPR cookie consent**: analytics cookies require consent in EU; must offer reject option
- **Consent mode**: GA4 consent mode must be configured for EU visitors (cookieless measurement as fallback)
- **CCPA do-not-sell**: analytics must respect do-not-sell signals
- **Data retention**: configure appropriate data retention periods (GA4 default 14 months, consider shorter for GDPR)
- **PII handling**: no PII in analytics (email, phone, names must not be sent to GA4/GSC)
- **IP anonymization**: required in EU, recommended globally
- **Third-party tracking disclosure**: disclose all third-party trackers in privacy policy
- **Server-side tracking**: additional consent requirements for server-side tracking setups
- **Cross-device tracking**: additional consent required for cross-device user identification
- **Remarketing audiences**: consent required before adding users to remarketing audiences

## Output Files

- `kai/compliance/__init__.py`
- `kai/compliance/policy_packs/__init__.py`
- `kai/compliance/policy_packs/base.py`
- `kai/compliance/policy_packs/website.py`
- `kai/compliance/policy_packs/social.py`
- `kai/compliance/policy_packs/paid_media.py`
- `kai/compliance/policy_packs/email.py`
- `kai/compliance/policy_packs/analytics.py`

## Acceptance Criteria

- All files parse as valid Python
- `PolicyRule` model has all specified fields with correct types
- Website pack has at least 15 rules with realistic regulatory sources
- Social pack has at least 15 rules covering FTC, platform-specific, and content rules
- Paid media pack has at least 20 rules drawing from actual platform policies
- Email pack has at least 15 rules covering CAN-SPAM, GDPR, CCPA, CASL
- Analytics pack has at least 10 rules covering cookie consent, PII, data retention
- Every rule has a non-empty `fix_guidance` and at least one `examples` entry
- `PolicyRegistry` correctly filters by content_type, region, and industry
- Rules reference actual regulations (ADA, WCAG, GDPR, CAN-SPAM, FTC Act, CCPA, CASL) — not made-up sources
- Paid media rules are consistent with existing files in `harness/references/`

## Reference Materials

- `harness/references/advertising-compliance.md` — comprehensive FTC/GDPR/CAN-SPAM/COPPA/CCPA reference
- `harness/references/google-ads-policy-reference.md` — Google Ads policies
- `harness/references/meta-ads-rules.md` — Meta/Facebook/Instagram policies
- `harness/references/tiktok-ads-policy-reference.md` — TikTok policies
- `harness/references/linkedin-ads-rules.md` — LinkedIn policies
- `harness/references/microsoft-ads-rules.md` — Microsoft/Bing policies
- `harness/references/pinterest-ads-rules.md` — Pinterest policies
- `harness/references/snapchat-ads-policy-reference.md` — Snapchat policies
- `harness/references/amazon-ads-policy-reference.md` — Amazon policies
- `harness/references/x-ads-policy-reference.md` — X/Twitter policies
- `harness/references/cold-email-rules.md` — CAN-SPAM and deliverability
- `kai/runtime/models.py` — SerializableModel pattern

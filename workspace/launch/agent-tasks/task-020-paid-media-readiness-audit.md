# Task 020: Build paid media readiness audit

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P2
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Before spending a single dollar on advertising, a business needs prerequisites in place: conversion tracking, landing pages, creative assets, audience definitions, and compliance readiness. Launching paid campaigns without these prerequisites wastes budget and produces misleading data. This audit engine evaluates whether a business is ready to run paid advertising on each relevant platform, identifies specific gaps that need to be closed first, and provides a platform-by-platform readiness assessment.

## Scope

Build `kai/audits/paid_media_readiness.py` with a paid media readiness audit engine that evaluates the business's readiness for paid advertising across major platforms.

## Detailed Requirements

### File: `kai/audits/paid_media_readiness.py`

**Function: `audit_paid_media_readiness(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. `connected_data` may include ad account status, pixel/tag verification, and campaign performance data.

**Check 1: Conversion Tracking Installed**
- Check if profile.channels includes ga4 or google_ads with connected status
- If no analytics channel -> CRITICAL: "No conversion tracking detected — running paid ads without tracking is burning money blind"
- If analytics exists but is_connected is False -> HIGH: "Analytics exists but is not connected — conversion tracking cannot be verified"
- If connected -> check for conversion event setup indicators
- Recommendation: "Before spending $1 on ads: (1) Install Google Analytics 4, (2) Set up conversion events (form submit, phone click, purchase), (3) Verify events fire correctly, (4) Import conversions into ad platforms"

**Check 2: Landing Pages Exist for Key Offers**
- Check profile.offers for primary offers
- For each primary offer: check if a landing page is indicated (URL in offer or metadata)
- If offers exist but no landing page evidence -> HIGH: "No dedicated landing pages for primary offers — sending ad traffic to the homepage wastes 30-50% of ad spend"
- For local-service: "Each core service needs its own landing page with specific CTA, social proof, and service details"
- For ecommerce: "Product pages and collection pages serve as landing pages — ensure they're conversion-optimized"
- Recommendation: "Create a dedicated landing page for each primary offer. Include: headline matching the ad, specific CTA, trust signals, and no navigation distractions."

**Check 3: Ad Account Status**
- Check profile.channels for ad platform channels (google_ads, meta_ads, linkedin_ads, etc.)
- For each found:
  - If is_connected -> INFO: "{platform} ad account connected"
  - If not connected -> MEDIUM: "{platform} ad account not connected — required before running ads"
  - If not present and archetype recommends this platform -> MEDIUM: "No {platform} account — this is a recommended channel for your archetype"

**Check 4: Pixel/Tag Status**
- If connected_data includes pixel verification: report status
- If not available: generate per-platform advisory:
  - Google Ads: "Verify Google Ads conversion tag and Google Tag Manager are installed"
  - Meta Ads: "Verify Meta Pixel is installed and firing on all key pages"
  - LinkedIn: "Verify LinkedIn Insight Tag is installed"
  - TikTok: "Verify TikTok Pixel is installed"
- Severity: HIGH for platforms with active or planned ad spend, MEDIUM for planned

**Check 5: Audience Definitions**
- Check profile.personas for defined target audiences
- If personas is empty -> HIGH: "No target personas defined — ad targeting requires clear audience definitions"
- If personas exist but lack channels_used -> MEDIUM: "Personas defined but missing channel preferences — this affects platform-specific targeting"
- If personas have demographics, pain_points, and channels_used -> INFO: "Personas are well-defined for ad targeting"
- Recommendation: "Define for each persona: demographics (age, location, income), interests/behaviors (for platform targeting), pain points (for ad copy), and buying triggers (for campaign timing)"

**Check 6: Budget Allocated**
- Check profile.budget.monthly_marketing_budget
- If budget is None -> HIGH: "No marketing budget set — paid media requires a defined budget with daily/monthly caps"
- If budget < $300/mo -> MEDIUM: "Marketing budget of ${budget}/mo is below recommended minimums for most paid channels"
- If budget set and reasonable -> INFO: "Budget of ${budget}/mo allocated — sufficient for {recommended_channels}"
- Platform minimum recommendations:
  - Google Ads: $500/mo minimum to generate meaningful data
  - Meta Ads: $500/mo minimum for learning phase completion
  - LinkedIn Ads: $1,000/mo minimum due to higher CPCs
  - TikTok Ads: $500/mo minimum
- Recommendation based on budget: suggest which platforms are feasible at the given budget

**Check 7: Creative Assets Ready**
- Cross-reference with creative readiness audit findings (Task 019), but focus on ad-specific needs:
  - If no professional photos -> HIGH: "Creative assets not ready for ads — ads need images/video before launching"
  - For Meta Ads: need at least 3-5 ad creative variants for testing
  - For Google Ads: need compelling ad copy and landing pages (visual assets less critical for search)
  - For video platforms (TikTok, YouTube): need video content
- Recommendation: "Before launching ads, prepare: 3-5 image variants per campaign, 2-3 headline variants, 2 description variants, and at least 1 video creative for video platforms"

**Check 8: Offer/CTA Defined**
- Check profile.offers for clear offers with CTAs
- If offers have primary_cta defined -> INFO: "Offers and CTAs defined — ready for ad campaign alignment"
- If offers exist but no CTA -> MEDIUM: "Offers defined but no specific CTA — ads need a clear call to action"
- If no offers -> CRITICAL: "No offers defined — cannot create ads without knowing what to sell"
- Recommendation: "Each ad campaign needs a specific offer and CTA: what the customer gets and what they should do next"

**Check 9: Competitor Ad Landscape (advisory)**
- Cannot assess from profile alone
- Generate advisory finding: "Research competitor ad presence before launching. Check: (1) Google Ads Transparency Center, (2) Meta Ad Library, (3) Search your target keywords and note who's advertising"
- Severity: INFO
- Recommendation: "Use Google Ads Transparency Center and Meta Ad Library to research competitor ad strategies, messaging, and offers before launching"

**Check 10: Compliance Pre-Check for Regulated Industries**
- If profile.constraints.regulated_industry is True OR archetype has compliance overlays:
  - Check which platforms have additional compliance requirements
  - Generate platform-specific compliance findings:
    - Healthcare: "Meta Ads require Special Ad Category designation for health-related advertising"
    - Legal: "Google Ads requires lawyer advertising certification in some jurisdictions"
    - Financial: "Financial service ads require disclosures and may need platform certification"
    - Real estate: "Meta Ads require Special Ad Category for housing-related advertising"
  - Severity: HIGH (compliance violations can get accounts banned)
- If not regulated: INFO: "No special regulatory requirements detected for your industry"
- Recommendation: "Before launching, review platform-specific ad policies for your industry. See harness/references/ for full policy references."

**Check 11: Platform-Specific Readiness Assessment**
- Generate a summary finding per relevant platform:
  - For each platform in the archetype's recommended channel_mix:
    - Assess readiness: account (Y/N), tracking (Y/N), budget (Y/N), creative (Y/N), landing page (Y/N), compliance (Y/N)
    - Ready = all prerequisites met
    - Nearly ready = missing 1-2 items
    - Not ready = missing 3+ items
  - Generate one finding per platform: "Google Ads Readiness: {status} — Missing: {missing_items}"
  - Severity: based on platform priority for the archetype

**Google Ads-specific prerequisites:**
- Account created and billing set up
- Conversion tracking via Google Tag or GA4
- Landing pages with relevant content
- Keyword research completed
- Ad copy drafted (headlines, descriptions)
- Daily budget set
- For LSA (Local Service Ads): background check, license verification, insurance verification

**Meta Ads-specific prerequisites:**
- Business Manager set up
- Ad account created and billing set up
- Meta Pixel installed and verified
- Custom audiences defined (website visitors, email list)
- Ad creative ready (images, video, copy)
- Campaign structure defined (campaign > ad set > ad)
- Special Ad Category designation if applicable

**LSA (Local Service Ads) prerequisites (local-service only):**
- Google Guaranteed or Google Screened badge applied for
- Background check submitted
- License and insurance documentation uploaded
- Service areas defined
- Business hours set
- Budget set

**Scoring Function:**

**`score_paid_media_readiness(findings: List[AuditFinding]) -> float`**
- Score 0-100 using standard formula
- Weight conversion tracking and landing page findings 2x

**Helper: `get_platform_prerequisites(platform: str, archetype: str) -> List[str]`**
- Return list of prerequisites for a specific platform + archetype combination
- Used by Check 11 for the readiness assessment

## Output Files

- `kai/audits/paid_media_readiness.py`

## Acceptance Criteria

- [ ] `paid_media_readiness.py` implements `audit_paid_media_readiness()` with all 11 checks
- [ ] Conversion tracking check is CRITICAL when missing — it's the foundational prerequisite
- [ ] Landing page check emphasizes dedicated pages vs. homepage for ad traffic
- [ ] Budget check provides platform-specific minimum recommendations
- [ ] Compliance pre-check covers healthcare, legal, financial, and real estate regulatory requirements
- [ ] Platform-specific readiness (Check 11) produces per-platform readiness assessments
- [ ] Google Ads prerequisites include LSA requirements for local-service archetype
- [ ] Meta Ads prerequisites include Special Ad Category requirements
- [ ] `get_platform_prerequisites()` helper covers Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads
- [ ] `score_paid_media_readiness()` weights tracking and landing pages 2x
- [ ] All findings have complete fields and appropriate severity levels
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — channels, budget, offers, constraints
- `knowledge/checklists/paid-acquisition-checklist.md` — paid acquisition checklist
- `knowledge/checklists/meta-advertising-checklist.md` — Meta ads checklist
- `knowledge/checklists/google-ads-launch-checklist.md` — Google Ads launch checklist
- `harness/references/google-ads-policy-reference.md` — Google Ads policies
- `harness/references/meta-ads-rules.md` — Meta Ads policies
- `harness/references/advertising-compliance.md` — FTC/compliance reference
- `CLAUDE.md` — ad policy compliance gate

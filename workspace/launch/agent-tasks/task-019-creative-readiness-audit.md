# Task 019: Build creative and asset readiness audit

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P2
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Marketing execution requires creative assets — photos, videos, graphics, testimonial content, case study materials. Many businesses have great services but lack the raw materials needed to run effective campaigns. This audit engine identifies asset gaps that would block or degrade specific channel executions. If a business wants to run Meta Ads but has no product photos, that's a blocker. If they want social media presence but have no team photos or behind-the-scenes content, that's a gap. This engine maps what exists against what each channel and campaign type needs.

## Scope

Build `kai/audits/creative_readiness.py` with a creative and asset readiness audit engine that evaluates available marketing assets against the requirements of the business's active and planned channels.

## Detailed Requirements

### File: `kai/audits/creative_readiness.py`

**Function: `audit_creative_readiness(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. `connected_data` may include asset inventory data from connected platforms.

**Check 1: Professional Photography**
- Assess based on profile data and trust signals:
  - If profile has no logo_url and no photo-related trust signals -> HIGH: "No professional photography indicators — professional images are essential for ads, social media, and website credibility"
  - For local-service: "Before/after project photos, team photos, and equipment/truck photos are the minimum"
  - For ecommerce: "Product photography is non-negotiable — lifestyle and white-background shots needed"
  - For professional-services: "Professional headshots and office/team photos establish authority"
- Recommendation archetype-specific:
  - Local-service: "Invest in: (1) Professional headshots for key team, (2) High-quality before/after project photos, (3) Branded truck/vehicle photos, (4) Action shots of team at work"
  - Ecommerce: "Invest in: (1) White-background product shots, (2) Lifestyle/in-use photography, (3) Package/unboxing photos, (4) Detail/texture close-ups"
  - Professional-services: "Invest in: (1) Professional headshots for all public-facing team, (2) Office/workspace photos, (3) Team collaboration photos, (4) Event/speaking photos"

**Check 2: Logo Quality**
- If profile.identity.logo_url is None -> MEDIUM: "No logo URL on file — the logo is the core brand asset needed across all channels"
- If logo exists -> INFO (advisory): "Ensure logo is available in: high-res PNG (transparent background), square format (for social profiles), horizontal format (for website header), and favicon size"
- Recommendation: "Provide logo in multiple formats: SVG/vector, transparent PNG (1000x1000+), and favicon (32x32, 180x180)"

**Check 3: Brand Colors Defined**
- Check profile.brand_voice and metadata for brand color indicators
- If no brand color information found -> MEDIUM: "Brand colors not defined — consistent color usage across all marketing materials builds recognition"
- Recommendation: "Define: primary brand color, secondary color, accent color, and background color. Provide hex codes."

**Check 4: Testimonial Content Available for Marketing Use**
- Check profile.trust.testimonials
- If testimonials exist: assess whether they have enough detail for marketing use
  - Need: customer name (or first name + last initial), specific outcomes, and ideally a photo
  - If testimonials exist but lack attribution -> MEDIUM: "Testimonials exist but lack attribution — named testimonials are 3x more credible than anonymous ones"
- If no testimonials -> HIGH: "No testimonial content available — this blocks social proof in ads, landing pages, and email"
- Recommendation: "Collect written testimonials with: customer name, location, specific result, and permission to use in marketing"

**Check 5: Case Study Content Available**
- Check profile.trust.case_studies
- If case_studies empty:
  - Professional-services: HIGH: "No case study content — case studies are the primary conversion asset for professional services"
  - Local-service: MEDIUM: "No before/after or project showcase content"
  - Ecommerce: MEDIUM: "No customer success stories documented"
- If case studies exist but < 3 -> LOW: "Only {n} case study(ies) — expand coverage to different service types and customer profiles"

**Check 6: Video Content Available**
- Check for video indicators in profile (channel data, trust signals, metadata)
- If no video content indicators -> severity by archetype:
  - Ecommerce: HIGH: "No video content — video drives 80% higher conversion rates for product pages"
  - Local-service: MEDIUM: "No video content — short project walkthrough and testimonial videos are high-impact"
  - Professional-services: MEDIUM: "No video content — thought leadership and explainer videos build authority"
- Recommendation: "Start with: (1) 60-second brand overview video, (2) Customer testimonial videos, (3) Service/product demo videos"

**Check 7: Before/After Documentation (local-service, ecommerce)**
- If archetype is local-service:
  - If no before/after evidence in trust signals -> MEDIUM: "No before/after project documentation — this is the most powerful social proof format for service businesses"
  - Recommendation: "Photograph every project: (1) Before photo, (2) During work photo, (3) After completion photo. Store in a shared album for marketing use."
- If archetype is ecommerce (transformation products):
  - Advisory based on product type — check constraints for before/after restrictions

**Check 8: Team Headshots**
- If trust.team_size indicates 2+ employees:
  - If no team photo/headshot evidence -> MEDIUM: "Team headshots not available — people buy from people, not faceless companies"
  - For local-service: "Customers want to know who's coming to their home"
  - For professional-services: "Headshots on the website and LinkedIn are essential for credibility"
- Recommendation: "Schedule professional headshots for all customer-facing team members"

**Check 9: Social Media Content Library**
- Check profile.channels for social channels (facebook, instagram, tiktok, linkedin)
- If social channels exist but no content library evidence -> MEDIUM: "Active social channels but no content library — batch-create and organize content for consistent posting"
- If no social channels -> MISSING_DATA/INFO based on archetype
- Recommendation: "Build a content library: 30+ photos organized by category, 10+ testimonial graphics, 5+ video clips, seasonal content templates"

**Check 10: Asset Gap Analysis Summary**
- Generate a summary finding that maps asset gaps to channel blockages:
  - "Missing [asset type] blocks execution on [channels]"
  - Examples:
    - "No product photography blocks: Meta Ads, Instagram, Google Shopping, website PDPs"
    - "No video content blocks: TikTok, YouTube, video ads on Meta"
    - "No headshots blocks: LinkedIn optimization, website team page, about page"
    - "No testimonial content blocks: social proof ads, landing page optimization, email social proof"
- Severity: the highest severity of any individual gap
- This is a composite finding that helps prioritize asset creation

**Scoring Function:**

**`score_creative_readiness(findings: List[AuditFinding]) -> float`**
- Score 0-100 using standard formula

**Helper Function:**

**`map_assets_to_channels(archetype: str) -> Dict[str, List[str]]`**
- Return a mapping of asset types to channels that require them
- Example: {"product_photography": ["meta_ads", "google_shopping", "instagram", "website"], "video": ["tiktok", "youtube", "meta_ads_video"]}
- Archetype-dependent: local-service needs different assets than ecommerce

## Output Files

- `kai/audits/creative_readiness.py`

## Acceptance Criteria

- [ ] `creative_readiness.py` implements `audit_creative_readiness()` with all 10 checks
- [ ] Photography check generates archetype-specific recommendations
- [ ] Logo check recommends multiple format availability
- [ ] Testimonial check evaluates quality (attribution) not just quantity
- [ ] Video content check severity varies by archetype (HIGH for ecommerce)
- [ ] Before/after check applies to local-service archetype
- [ ] Asset gap analysis (Check 10) maps missing assets to blocked channels
- [ ] `map_assets_to_channels()` returns archetype-appropriate mappings
- [ ] `score_creative_readiness()` scoring function exists
- [ ] All findings have category = "creative_readiness" or relevant subcategory
- [ ] Recommendations are specific about what to create, not just "get better photos"
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — trust, brand_voice, channels
- `kai/archetypes/local_service.py` (Task 006) — creative_formats definitions
- `kai/archetypes/ecommerce.py` (Task 007) — creative_formats definitions
- `knowledge/checklists/creative-production-checklist.md` — creative production checklist
- `knowledge/playbooks/ad-creative-best-practices.md` — ad creative best practices

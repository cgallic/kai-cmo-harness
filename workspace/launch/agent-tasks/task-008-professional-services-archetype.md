# Task 008: Define professional-services archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Large

## Context

Professional services businesses (law firms, consultancies, accounting firms, agencies, financial advisors, architects) sell expertise and relationships, not products. Their marketing is built on authority, trust, and long-cycle nurture. Content marketing, thought leadership, case studies, and referral networks are their primary growth levers. The buying process involves multiple stakeholders, high deal values, and extended consideration periods. This archetype defines the unique marketing approach for these businesses.

## Scope

Build `kai/archetypes/professional_services.py` with the full professional-services archetype definition, using the base classes from `kai/archetypes/base.py` (Task 006).

## Detailed Requirements

### File: `kai/archetypes/professional_services.py`

**Constant: `PROFESSIONAL_SERVICES_ARCHETYPE`** — an instance of ArchetypeDefinition.

**id:** `"professional-services"`
**name:** `"Professional Services"`
**description:** "Businesses selling expertise, advice, and specialized skills — law firms, consultancies, accounting firms, agencies, financial advisors, architects, and similar. Revenue comes from engagements, retainers, and project fees. Marketing is built on authority, trust, and long-cycle relationship nurture. The buying process often involves multiple decision-makers and extended evaluation periods."

**audit_categories** (in priority order):
1. `"authority_content"` — Is the firm producing content that demonstrates expertise?
2. `"case_studies"` — Are there proof points showing real client results?
3. `"thought_leadership"` — Is there a personal or firm brand in the industry conversation?
4. `"linkedin_presence"` — Is LinkedIn being used as the primary professional network?
5. `"email_nurture"` — Is there a systematic nurture program for leads?
6. `"seo_topical"` — Does the firm rank for topical expertise queries?
7. `"referral_system"` — Is there a formalized referral engine?
8. `"proposal_pipeline"` — Is the proposal-to-close process optimized?
9. `"trust_credentials"` — Are credentials, certifications, and affiliations prominently displayed?

**priority_defaults:**
1. "Firm has at least 3 detailed case studies published with measurable results"
2. "Key personnel have active, optimized LinkedIn profiles"
3. "Website clearly articulates expertise areas, ideal client profile, and differentiation"
4. "Email nurture sequence exists for leads who aren't ready to buy"
5. "Thought leadership content published at least 2x/month"
6. "Referral request system is formalized (not just 'ask for referrals')"
7. "Proposal template and follow-up sequence are standardized"
8. "Credentials and certifications are prominently displayed on website and profiles"
9. "Topical authority content covers the firm's core expertise areas"
10. "Client testimonials include specific outcomes, not just general praise"

**kpi_schema:**
- `qualified_leads`: count/month, higher_is_better, primary, benchmark "5-30"
- `proposal_rate`: percentage (leads to proposals), higher_is_better, primary, benchmark "30-60%"
- `close_rate`: percentage (proposals to clients), higher_is_better, primary, benchmark "25-50%"
- `average_engagement_value`: dollars, higher_is_better, primary, benchmark varies by industry
- `client_retention_rate`: percentage (annual), higher_is_better, primary, benchmark "80-95%"
- `referral_rate`: percentage of new clients from referrals, higher_is_better, primary, benchmark "30-60%"
- `content_authority_score`: composite (0-100), higher_is_better, secondary, benchmark "40-80"
- `linkedin_engagement_rate`: percentage, higher_is_better, secondary, benchmark "2-5%"
- `email_open_rate`: percentage, higher_is_better, secondary, benchmark "25-40%"
- `time_to_close`: days from first contact to signed engagement, lower_is_better, secondary, benchmark "30-120 days"
- `client_satisfaction_score`: NPS or 1-10, higher_is_better, tertiary, benchmark "8+ or NPS 50+"
- `revenue_per_client`: dollars/year, higher_is_better, tertiary, benchmark varies

**channel_mix:**
1. `website` — P1, all stages, "Authority hub — case studies, service pages, team bios, thought leadership blog"
2. `linkedin` — P1, all stages, "Primary social channel for B2B professional services"
3. `email` — P1, all stages, "Nurture leads through long sales cycles with value-driven content"
4. `seo` — P2, growth+, "Topical authority content ranking for expertise queries"
5. `linkedin_ads` — P2, growth+, min $1000/mo, "Targeted advertising to specific job titles, industries, and company sizes"
6. `google_ads` — P3, growth+, min $500/mo, "Search ads for high-intent queries (e.g., '[city] [practice area] lawyer')"
7. `podcast` — P3, growth+, "Thought leadership via guest appearances or own show"
8. `pr` — P3, scale+, "Media mentions and speaking engagements for credibility"
9. `youtube` — P3, growth+, "Educational video content demonstrating expertise"
10. `referral_network` — P1, all stages, "Formalized referral partner relationships"

**action_families:**
1. `authority_content` — high priority: ["expertise_articles", "industry_analysis", "framework_publications", "whitepaper_creation", "research_reports", "faq_content"]
2. `case_study_program` — high priority: ["case_study_template", "client_interview_process", "results_documentation", "case_study_distribution", "case_study_repurposing"]
3. `thought_leadership` — high priority: ["linkedin_content_calendar", "speaking_engagement_pitches", "podcast_guest_strategy", "industry_commentary", "original_research"]
4. `linkedin_optimization` — medium priority: ["profile_optimization", "content_publishing_cadence", "engagement_strategy", "linkedin_articles", "team_advocacy_program"]
5. `email_nurture` — high priority: ["welcome_sequence", "newsletter_cadence", "case_study_drip", "event_invitation_sequence", "re_engagement_sequence", "proposal_follow_up"]
6. `referral_engine` — high priority: ["referral_partner_identification", "referral_ask_system", "referral_tracking", "referral_reward_program", "strategic_partnership_development"]
7. `proposal_optimization` — medium priority: ["proposal_template_design", "pricing_presentation", "follow_up_sequence", "objection_handling_library", "competitive_positioning"]
8. `credential_display` — medium priority: ["certification_badges", "award_showcase", "team_credential_pages", "speaking_history", "publication_list", "client_logo_wall"]

**compliance_sensitivities:**
- "Legal advertising rules vary by state — bar association restrictions on claims, testimonials, and specialization"
- "Financial advisor marketing is regulated by SEC, FINRA, and state regulations"
- "Accounting firm marketing must comply with AICPA ethics rules"
- "Healthcare consulting near regulated space — avoid medical claims"
- "Testimonials may need disclaimers ('results may vary', 'past results do not guarantee future performance')"
- "Credential claims must be current and verifiable"
- "Confidentiality — case studies may need client approval; anonymize where required"

**creative_formats:**
- `case_study_layouts`: "Structured Problem-Solution-Results format with metrics", platforms: ["website", "email", "linkedin", "pdf"]
- `thought_leadership_articles`: "Long-form expertise pieces demonstrating deep knowledge", platforms: ["website", "linkedin", "email"]
- `credential_displays`: "Visual badges, certification logos, and award graphics", platforms: ["website", "email_signature", "linkedin"]
- `team_bios`: "Professional headshots with expertise narratives", platforms: ["website", "linkedin"]
- `process_explainers`: "Visual workflow showing how engagement works", platforms: ["website", "proposal", "email"]
- `infographics`: "Data-driven visual content from original research", platforms: ["linkedin", "website", "email"]
- `webinar_decks`: "Presentation materials for educational webinars", platforms: ["webinar", "youtube", "linkedin"]
- `client_testimonial_videos`: "Video testimonials from clients with results", platforms: ["website", "youtube", "linkedin"]

**budget_heuristics:**
- `startup` (pre-launch, early-pmf): min $1000/mo, max $3000/mo, "Focus 50% on content creation (case studies, authority articles). 30% on LinkedIn organic optimization. 20% on email setup and nurture sequences."
- `established` (growth): min $3000/mo, max $10000/mo, "Split 30% content/thought leadership, 25% LinkedIn Ads, 20% email/nurture, 15% SEO, 10% events/speaking."
- `scaling` (scale, mature): min $10000/mo, max $50000/mo, "Diversify: content 25%, paid (LinkedIn + Google) 25%, events/PR 20%, SEO 15%, email 10%, referral program 5%."

**minimum_viable_channels:**
- `["website", "linkedin", "email", "referral_network"]` — "A professional services firm must have: an authority website with case studies, active LinkedIn presence, email nurture for long-cycle leads, and a formalized referral network."

**archetype_specific_rules:**
- "Content should demonstrate expertise, not just state it — show the thinking, not just the conclusion"
- "Case studies with specific numbers outperform vague 'we helped them grow' narratives by 3-5x"
- "LinkedIn personal profiles often outperform company pages for professional services — invest in key personnel profiles"
- "Referrals are typically the highest-converting lead source — formalize the ask and the tracking"
- "Long sales cycles require patience in attribution — measure leading indicators (meetings booked, proposals sent) alongside lagging ones (closed deals)"
- "Thought leadership should take a position — neutral 'comprehensive guide' content doesn't build authority"
- "Proposals should be tracked with structured follow-up — most firms lose deals by failing to follow up"
- "B2B buyers do extensive research before contacting a firm — your content IS your sales team"
- "Webinars and educational events convert at 10-20% to qualified lead for professional services"

## Output Files

- `kai/archetypes/professional_services.py`

## Acceptance Criteria

- [ ] `professional_services.py` exports `PROFESSIONAL_SERVICES_ARCHETYPE` of type ArchetypeDefinition
- [ ] All 9 audit categories are defined in priority order
- [ ] All 12 KPIs are defined with units, directions, and benchmarks
- [ ] All 10 channels include priority, stage relevance, and rationale
- [ ] All 8 action families have specific action lists
- [ ] Budget heuristics cover 3 stages with appropriate ranges
- [ ] Compliance sensitivities cover legal advertising rules, financial regulations, and credential requirements
- [ ] Creative formats emphasize case studies, thought leadership, and credential displays
- [ ] Minimum viable channels include website, linkedin, email, referral_network
- [ ] Archetype-specific rules emphasize content authority and referral formalization
- [ ] File imports from `kai.archetypes.base`

## Reference Materials

- `kai/archetypes/base.py` (Task 006) — base classes
- `knowledge/checklists/professional-services-b2b-checklist.md` — B2B services checklist
- `knowledge/playbooks/brand-positioning.md` — positioning playbook
- `knowledge/playbooks/marketing-automation.md` — automation playbook
- `knowledge/channels/linkedin-articles.md` — LinkedIn channel guide
- `knowledge/channels/email-lifecycle.md` — email lifecycle guide
- `CLAUDE.md` — framework map

# Task 009: Define multi-location archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Large

## Context

Multi-location businesses (restaurant chains, dental offices, fitness franchises, retail chains, service company expansions) face a unique marketing challenge: maintaining brand consistency while optimizing for each individual location's local market. They need fleet-level management of GBP listings, location-specific content, distributed review management, and the ability to run both centralized brand campaigns and per-location micro-campaigns. This archetype defines the system for managing marketing across multiple physical locations.

## Scope

Build `kai/archetypes/multi_location.py` with the full multi-location archetype definition, using the base classes from `kai/archetypes/base.py` (Task 006).

## Detailed Requirements

### File: `kai/archetypes/multi_location.py`

**Constant: `MULTI_LOCATION_ARCHETYPE`** — an instance of ArchetypeDefinition.

**id:** `"multi-location"`
**name:** `"Multi-Location Business"`
**description:** "Businesses operating across multiple physical locations — restaurant groups, dental practices, fitness chains, retail chains, franchises, and multi-market service companies. Marketing must balance brand consistency across all locations with local relevance and per-location optimization. Key challenges include GBP fleet management, location page SEO, distributed review management, and centralized-vs-local advertising decisions."

**audit_categories** (in priority order):
1. `"location_consistency"` — Is brand presentation consistent across all locations?
2. `"gbp_fleet"` — Are all GBP listings claimed, complete, and actively managed?
3. `"local_seo_per_location"` — Does each location rank for its local market?
4. `"review_distribution"` — Are reviews healthy across all locations (not just HQ)?
5. `"location_pages"` — Does the website have optimized pages for each location?
6. `"brand_consistency"` — Is messaging, visual identity, and voice consistent?
7. `"local_ads_per_location"` — Are paid campaigns geo-targeted per location?
8. `"centralized_vs_local"` — Is there clear division between corporate and local marketing?
9. `"nap_consistency"` — Are Name, Address, Phone consistent across all directories?

**priority_defaults:**
1. "Every location has a claimed, verified, and complete Google Business Profile"
2. "NAP (Name, Address, Phone) is identical across every directory and citation for each location"
3. "Every location has at least 15 Google reviews with 4.2+ average rating"
4. "Website has a dedicated, optimized page for each location"
5. "Brand voice, visual identity, and messaging are consistent across all location materials"
6. "Review response is happening at every location (not just HQ)"
7. "Each location's GBP has recent photos and posts (within 30 days)"
8. "Geo-targeted ad campaigns are running for at least the top 3 locations"
9. "Location-specific landing pages exist for each paid campaign"
10. "Centralized reporting dashboard tracks per-location KPIs"

**kpi_schema:**
- `per_location_leads`: count/month per location, higher_is_better, primary, benchmark "10-50"
- `location_review_avg`: average Google rating across locations, higher_is_better, primary, benchmark "4.2-4.8"
- `gbp_views_per_location`: count/month, higher_is_better, primary, benchmark "300-3000"
- `brand_consistency_score`: 0-100 composite, higher_is_better, primary, benchmark "70-95"
- `location_page_conversion`: percentage, higher_is_better, primary, benchmark "3-8%"
- `aggregate_cost_per_lead`: dollars (across all locations), lower_is_better, primary, benchmark "$30-150"
- `nap_consistency_score`: percentage of correct listings, higher_is_better, secondary, benchmark "90-100%"
- `review_velocity_per_location`: reviews/month per location, higher_is_better, secondary, benchmark "3-15"
- `location_variance`: standard deviation of KPIs across locations, lower_is_better, secondary, benchmark "low"
- `total_review_count`: sum across all locations, higher_is_better, secondary, benchmark varies
- `worst_location_score`: lowest-performing location's composite score, higher_is_better, secondary, benchmark "50+"
- `best_location_score`: highest-performing location's composite score, higher_is_better, tertiary, benchmark "80+"
- `location_page_organic_traffic`: visits/month per location page, higher_is_better, tertiary, benchmark "100-1000"

**channel_mix:**
1. `website` — P1, all stages, "Central hub with dedicated location pages — each location gets its own optimized page"
2. `gbp` — P1, all stages, "Fleet of GBP listings — the primary local discovery channel for every location"
3. `google_ads` — P1, growth+, min $1000/mo total, "Geo-targeted search and Local Service Ads per location"
4. `email` — P2, all stages, "Centralized email with location-specific segmentation and content"
5. `meta_ads` — P2, growth+, min $500/mo, "Geo-targeted awareness and retargeting per market"
6. `seo` — P2, growth+, "Location pages, local schema markup, per-location content"
7. `yelp` — P3, all stages, "Claim and optimize every location's Yelp listing"
8. `facebook` — P2, all stages, "Per-location Facebook pages or a brand page with location tags"
9. `nextdoor` — P3, growth+, "Per-location neighborhood presence"
10. `sms` — P3, growth+, "Location-specific appointment reminders and promotions"
11. `review_platforms` — P1, all stages, "Systematic review management across Google, Yelp, and industry platforms for all locations"

**action_families:**
1. `gbp_fleet_management` — high priority: ["gbp_claim_all", "gbp_complete_all", "gbp_photos_per_location", "gbp_posts_per_location", "gbp_categories_audit", "gbp_q_and_a_per_location", "gbp_services_per_location"]
2. `location_page_seo` — high priority: ["create_location_pages", "unique_content_per_location", "local_schema_markup", "location_specific_keywords", "internal_linking_between_locations", "location_page_cta_optimization"]
3. `nap_consistency` — high priority: ["nap_audit_all_directories", "citation_correction", "new_citation_building", "duplicate_listing_removal", "nap_monitoring_system"]
4. `review_fleet_management` — high priority: ["review_request_per_location", "review_response_protocol", "negative_review_escalation", "review_distribution_balancing", "review_velocity_targets_per_location"]
5. `brand_consistency` — medium priority: ["brand_asset_library", "approved_templates_per_format", "brand_guideline_enforcement", "location_manager_training", "content_approval_workflow"]
6. `local_ad_management` — medium priority: ["geo_fencing_per_location", "location_specific_landing_pages", "per_location_budget_allocation", "local_ad_creative_variants", "performance_comparison_dashboard"]
7. `centralized_reporting` — medium priority: ["per_location_kpi_dashboard", "cross_location_comparison", "underperforming_location_alerts", "best_practice_sharing", "monthly_location_scorecard"]
8. `franchise_coordination` — low priority (if applicable): ["corporate_brand_compliance", "co_op_advertising_management", "franchisee_marketing_support", "territory_advertising_boundaries", "shared_asset_distribution"]

**compliance_sensitivities:**
- "Each location must have accurate, current hours and contact information"
- "Advertising must not mislead about which location is being represented"
- "Franchise agreements may restrict local advertising autonomy"
- "Review solicitation must comply with platform TOS at every location"
- "Location-specific offers must be honored at the stated location"
- "Territory boundaries in advertising must respect franchise/company agreements"
- "Staff photos and team claims must be current for each specific location"
- "Health and safety claims must be accurate per-location (not aggregated)"

**creative_formats:**
- `location_hero_images`: "Unique hero photos for each location showing the actual facility/team", platforms: ["website", "gbp", "meta_ads"]
- `brand_template_variants`: "Consistent brand templates with per-location customization fields", platforms: ["meta_ads", "email", "social"]
- `local_team_photos`: "Team photos specific to each location", platforms: ["website", "gbp", "facebook"]
- `per_location_offers`: "Location-specific promotional graphics", platforms: ["meta_ads", "email", "gbp"]
- `location_comparison_maps`: "Map showing all locations for customers to find nearest", platforms: ["website"]
- `location_specific_testimonials`: "Reviews and testimonials attributed to specific locations", platforms: ["website", "gbp", "social"]
- `community_involvement`: "Photos/content showing each location's community engagement", platforms: ["facebook", "instagram", "gbp"]

**budget_heuristics:**
- `startup` (2-3 locations): min $2000/mo total, max $6000/mo total, "Focus 40% on GBP optimization + review generation for all locations. 30% on geo-targeted Google Ads for top locations. 20% on location page SEO. 10% on centralized email."
- `established` (4-10 locations): min $5000/mo, max $20000/mo, "Split per-location: $500-1500/location for Google/Meta Ads. Central budget: 25% SEO/content, 20% email, 15% review management, 10% brand consistency."
- `scaling` (10+ locations): min $15000/mo, max $75000+/mo, "Per-location minimums of $750/mo for ads. Central: 20% SEO, 20% content, 15% email, 15% reporting/analytics, 10% brand programs, 20% distributed to per-location budgets."

**minimum_viable_channels:**
- `["website", "gbp", "google_ads", "email", "review_platforms"]` — "A multi-location business must have: a website with per-location pages, complete GBP for every location, geo-targeted paid search, centralized email with location segmentation, and systematic review management across all locations."

**archetype_specific_rules:**
- "The weakest location drags down the whole brand — identify and fix underperformers first"
- "NAP consistency is non-negotiable — a single NAP mismatch can hurt local rankings for that location"
- "Do NOT create one-size-fits-all location pages with only the address swapped — each page needs unique content"
- "Review distribution matters — 500 reviews at HQ and 3 reviews at a new location hurts the new location"
- "Franchise vs company-owned distinction changes what marketing the system can do autonomously"
- "Centralized reporting must show per-location KPIs, not just aggregates — aggregates hide problems"
- "Best practices from top-performing locations should be systematically replicated to underperformers"
- "Local ad budgets should be weighted by location opportunity, not distributed equally"
- "Each location should have its own phone number for attribution and call tracking"
- "KaiCalls AI receptionist (kaicalls.com) can standardize phone handling across all locations"

## Output Files

- `kai/archetypes/multi_location.py`

## Acceptance Criteria

- [ ] `multi_location.py` exports `MULTI_LOCATION_ARCHETYPE` of type ArchetypeDefinition
- [ ] All 9 audit categories prioritize location consistency and GBP fleet management
- [ ] All 13 KPIs include per-location metrics and cross-location comparison metrics
- [ ] Channel mix covers fleet-level management (GBP fleet, review platforms)
- [ ] Action families include gbp_fleet_management and nap_consistency
- [ ] Budget heuristics scale with location count (per-location + central budget)
- [ ] Compliance sensitivities address franchise agreements and per-location accuracy
- [ ] Creative formats include per-location variants from brand templates
- [ ] Archetype-specific rules address weakest-location problem and NAP consistency
- [ ] KaiCalls recommendation is included for standardized phone handling across locations
- [ ] File imports from `kai.archetypes.base`

## Reference Materials

- `kai/archetypes/base.py` (Task 006) — base classes
- `knowledge/checklists/multi-location-checklist.md` — multi-location checklist
- `knowledge/checklists/local-service-business-checklist.md` — local service checklist (applicable per-location)
- `knowledge/playbooks/local-seo-gbp-optimization.md` — GBP optimization playbook
- `CLAUDE.md` — framework map and KaiCalls rule

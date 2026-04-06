"""Multi-Location Business archetype for the Kai Marketing OS.

Covers restaurant groups, dental practices, fitness chains, retail chains,
franchises, and multi-market service companies.  The core tension this
archetype manages is **brand consistency vs. local relevance** -- every
location needs to rank, convert, and collect reviews in its own market
while the brand stays cohesive across the fleet.

Usage::

    from kai.archetypes.multi_location import MULTI_LOCATION_ARCHETYPE

    archetype = MULTI_LOCATION_ARCHETYPE
    print(archetype.audit_categories)
    print(archetype.kpi_schema["per_location_leads"])
"""

from __future__ import annotations

from kai.archetypes.base import (
    ActionFamily,
    ArchetypeDefinition,
    BudgetRange,
    ChannelRecommendation,
    CreativeFormat,
    KPIDefinition,
)

# ============================================================================
# KPI definitions
# ============================================================================

_KPI_SCHEMA = {
    "per_location_leads": KPIDefinition(
        id="per_location_leads",
        name="Per-Location Leads",
        description=(
            "Number of qualified leads generated per location per month. "
            "The primary demand signal at the unit level -- aggregates "
            "hide underperformers."
        ),
        unit="count/month per location",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="10-50",
    ),
    "location_review_avg": KPIDefinition(
        id="location_review_avg",
        name="Average Google Rating Across Locations",
        description=(
            "Mean Google review rating across all locations. A single "
            "low-rated location drags brand perception in its market "
            "and suppresses its GBP visibility."
        ),
        unit="rating",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="4.2-4.8",
    ),
    "gbp_views_per_location": KPIDefinition(
        id="gbp_views_per_location",
        name="GBP Views Per Location",
        description=(
            "Monthly Google Business Profile views (search + maps) per "
            "location. Measures local discovery reach at the unit level."
        ),
        unit="count/month",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="300-3000",
    ),
    "brand_consistency_score": KPIDefinition(
        id="brand_consistency_score",
        name="Brand Consistency Score",
        description=(
            "Composite 0-100 score measuring consistency of brand "
            "presentation across all locations -- visual identity, "
            "messaging, GBP completeness, and content quality."
        ),
        unit="score (0-100)",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="70-95",
    ),
    "location_page_conversion": KPIDefinition(
        id="location_page_conversion",
        name="Location Page Conversion Rate",
        description=(
            "Percentage of location page visitors who convert (call, "
            "form, booking). Each location page should convert at or "
            "above the archetype benchmark."
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="3-8%",
    ),
    "aggregate_cost_per_lead": KPIDefinition(
        id="aggregate_cost_per_lead",
        name="Aggregate Cost Per Lead",
        description=(
            "Blended cost per lead across all locations and channels. "
            "Per-location CPL should also be tracked -- the aggregate "
            "masks variance between strong and weak markets."
        ),
        unit="dollars",
        direction="lower_is_better",
        priority="primary",
        benchmark_range="$30-150",
    ),
    "nap_consistency_score": KPIDefinition(
        id="nap_consistency_score",
        name="NAP Consistency Score",
        description=(
            "Percentage of directory listings with correct Name, Address, "
            "and Phone for each location. A single NAP mismatch can hurt "
            "local rankings for that location."
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="90-100%",
    ),
    "review_velocity_per_location": KPIDefinition(
        id="review_velocity_per_location",
        name="Review Velocity Per Location",
        description=(
            "New Google reviews received per location per month. "
            "Velocity matters more than total count for GBP ranking, "
            "and distribution across locations matters more than "
            "aggregate velocity."
        ),
        unit="reviews/month per location",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="3-15",
    ),
    "location_variance": KPIDefinition(
        id="location_variance",
        name="Location KPI Variance",
        description=(
            "Standard deviation of key performance metrics across "
            "locations. High variance means some locations are "
            "significantly underperforming -- the weakest location "
            "drags down the whole brand."
        ),
        unit="standard deviation",
        direction="lower_is_better",
        priority="secondary",
        benchmark_range="low",
    ),
    "total_review_count": KPIDefinition(
        id="total_review_count",
        name="Total Review Count",
        description=(
            "Sum of Google reviews across all locations. Important for "
            "brand-level social proof, but per-location distribution "
            "is the more actionable metric."
        ),
        unit="count",
        direction="higher_is_better",
        priority="secondary",
    ),
    "worst_location_score": KPIDefinition(
        id="worst_location_score",
        name="Worst Location Composite Score",
        description=(
            "Composite performance score of the lowest-performing "
            "location. The floor matters -- one bad location damages "
            "brand perception in its entire market."
        ),
        unit="score (0-100)",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="50+",
    ),
    "best_location_score": KPIDefinition(
        id="best_location_score",
        name="Best Location Composite Score",
        description=(
            "Composite performance score of the highest-performing "
            "location. Used as a benchmark target for replicating "
            "best practices across the fleet."
        ),
        unit="score (0-100)",
        direction="higher_is_better",
        priority="tertiary",
        benchmark_range="80+",
    ),
    "location_page_organic_traffic": KPIDefinition(
        id="location_page_organic_traffic",
        name="Location Page Organic Traffic",
        description=(
            "Monthly organic search visits per location page. Each "
            "location page should capture local search demand for its "
            "market independently."
        ),
        unit="visits/month per location page",
        direction="higher_is_better",
        priority="tertiary",
        benchmark_range="100-1000",
    ),
}

# ============================================================================
# Channel mix
# ============================================================================

_CHANNEL_MIX = [
    ChannelRecommendation(
        channel="website",
        priority=1,
        stage_relevance=["all"],
        rationale=(
            "Central hub with dedicated location pages -- each location "
            "gets its own optimized page with unique content, local "
            "team photos, and location-specific CTAs."
        ),
        prerequisites=[
            "Domain and hosting",
            "CMS that supports scalable location page templates",
        ],
    ),
    ChannelRecommendation(
        channel="gbp",
        priority=1,
        stage_relevance=["all"],
        rationale=(
            "Fleet of GBP listings -- the primary local discovery channel "
            "for every location. Each listing must be claimed, verified, "
            "complete, and actively managed."
        ),
        prerequisites=[
            "Verified ownership of each location",
            "Location-specific phone numbers",
        ],
    ),
    ChannelRecommendation(
        channel="google_ads",
        priority=1,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=1000.0,
        rationale=(
            "Geo-targeted search and Local Service Ads per location. "
            "Budget should be allocated per-location based on market "
            "opportunity, not distributed equally."
        ),
        prerequisites=[
            "Location pages live",
            "Call tracking per location",
            "Conversion tracking configured",
        ],
    ),
    ChannelRecommendation(
        channel="email",
        priority=2,
        stage_relevance=["all"],
        rationale=(
            "Centralized email with location-specific segmentation and "
            "content. Subscribers tagged by location for relevant offers, "
            "events, and updates."
        ),
        prerequisites=[
            "Email platform with segmentation",
            "Location tagging on subscriber records",
        ],
    ),
    ChannelRecommendation(
        channel="meta_ads",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=500.0,
        rationale=(
            "Geo-targeted awareness and retargeting per market. Effective "
            "for driving local brand recognition and re-engaging website "
            "visitors from each location area."
        ),
        prerequisites=[
            "Meta pixel installed",
            "Location-specific ad creative",
            "Geo-fence definitions per location",
        ],
    ),
    ChannelRecommendation(
        channel="seo",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Location pages, local schema markup, per-location content. "
            "Each location page must have unique, substantive content -- "
            "not a template with the city name swapped."
        ),
        prerequisites=[
            "Location pages created",
            "LocalBusiness schema implemented per location",
            "Citation management tool active",
        ],
    ),
    ChannelRecommendation(
        channel="facebook",
        priority=2,
        stage_relevance=["all"],
        rationale=(
            "Per-location Facebook pages or a brand page with location "
            "tags. Local content, community engagement, and location-"
            "specific promotions build neighborhood trust."
        ),
        prerequisites=[
            "Social media model decision (centralized vs per-location)",
            "Brand guidelines for location managers",
        ],
    ),
    ChannelRecommendation(
        channel="review_platforms",
        priority=1,
        stage_relevance=["all"],
        rationale=(
            "Systematic review management across Google, Yelp, and "
            "industry platforms for all locations. Review distribution "
            "across the fleet is as important as total count."
        ),
        prerequisites=[
            "Review monitoring dashboard",
            "Per-location review response SLA",
            "Review generation process standardized",
        ],
    ),
    ChannelRecommendation(
        channel="yelp",
        priority=3,
        stage_relevance=["all"],
        rationale=(
            "Claim and optimize every location Yelp listing. Important "
            "for industries where Yelp is a primary discovery channel "
            "(restaurants, home services, health/beauty)."
        ),
        prerequisites=[
            "Yelp business account per location",
        ],
    ),
    ChannelRecommendation(
        channel="nextdoor",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Per-location neighborhood presence. Effective for service "
            "businesses and retail where hyperlocal trust drives "
            "purchase decisions."
        ),
        prerequisites=[
            "Nextdoor business page per location",
        ],
    ),
    ChannelRecommendation(
        channel="sms",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Location-specific appointment reminders and promotions. "
            "Messages must originate from or reference the specific "
            "location the customer interacts with."
        ),
        prerequisites=[
            "SMS platform with location segmentation",
            "Opt-in consent per contact",
        ],
    ),
]

# ============================================================================
# Action families
# ============================================================================

_ACTION_FAMILIES = [
    ActionFamily(
        id="gbp_fleet_management",
        name="GBP Fleet Management",
        description=(
            "Claim, verify, complete, and actively manage Google Business "
            "Profiles for every location. The GBP fleet is the single "
            "highest-impact local discovery asset."
        ),
        actions=[
            "gbp_claim_all",
            "gbp_complete_all",
            "gbp_photos_per_location",
            "gbp_posts_per_location",
            "gbp_categories_audit",
            "gbp_q_and_a_per_location",
            "gbp_services_per_location",
        ],
        priority="high",
        typical_timeline="2-4 weeks for initial setup, then ongoing weekly",
    ),
    ActionFamily(
        id="location_page_seo",
        name="Location Page SEO",
        description=(
            "Create and optimise dedicated website pages for each "
            "location with unique content, local schema markup, and "
            "location-specific CTAs."
        ),
        actions=[
            "create_location_pages",
            "unique_content_per_location",
            "local_schema_markup",
            "location_specific_keywords",
            "internal_linking_between_locations",
            "location_page_cta_optimization",
        ],
        priority="high",
        typical_timeline="2-6 weeks for initial build, then ongoing optimization",
    ),
    ActionFamily(
        id="nap_consistency",
        name="NAP Consistency",
        description=(
            "Ensure Name, Address, and Phone are identical across every "
            "directory and citation for every location. A single mismatch "
            "can suppress local rankings."
        ),
        actions=[
            "nap_audit_all_directories",
            "citation_correction",
            "new_citation_building",
            "duplicate_listing_removal",
            "nap_monitoring_system",
        ],
        priority="high",
        typical_timeline="2-4 weeks for audit and correction, then quarterly monitoring",
    ),
    ActionFamily(
        id="review_fleet_management",
        name="Review Fleet Management",
        description=(
            "Standardise review generation, response, and escalation "
            "across all locations. Balance review distribution so new "
            "or underperforming locations are not neglected."
        ),
        actions=[
            "review_request_per_location",
            "review_response_protocol",
            "negative_review_escalation",
            "review_distribution_balancing",
            "review_velocity_targets_per_location",
        ],
        priority="high",
        typical_timeline="1-2 weeks for setup, then ongoing daily",
    ),
    ActionFamily(
        id="brand_consistency",
        name="Brand Consistency",
        description=(
            "Establish and enforce consistent brand presentation across "
            "all locations -- visual identity, messaging, templates, and "
            "content approval workflows."
        ),
        actions=[
            "brand_asset_library",
            "approved_templates_per_format",
            "brand_guideline_enforcement",
            "location_manager_training",
            "content_approval_workflow",
        ],
        priority="medium",
        typical_timeline="3-6 weeks for initial setup, then ongoing quarterly audits",
    ),
    ActionFamily(
        id="local_ad_management",
        name="Local Ad Management",
        description=(
            "Run geo-targeted paid campaigns per location with "
            "location-specific landing pages, budget allocation based "
            "on market opportunity, and cross-location performance "
            "comparison."
        ),
        actions=[
            "geo_fencing_per_location",
            "location_specific_landing_pages",
            "per_location_budget_allocation",
            "local_ad_creative_variants",
            "performance_comparison_dashboard",
        ],
        priority="medium",
        typical_timeline="2-4 weeks for setup, then ongoing weekly optimization",
    ),
    ActionFamily(
        id="centralized_reporting",
        name="Centralized Reporting",
        description=(
            "Build per-location KPI dashboards, cross-location "
            "comparisons, and automated alerts for underperforming "
            "locations. Aggregates hide problems -- always drill down "
            "to location level."
        ),
        actions=[
            "per_location_kpi_dashboard",
            "cross_location_comparison",
            "underperforming_location_alerts",
            "best_practice_sharing",
            "monthly_location_scorecard",
        ],
        priority="medium",
        typical_timeline="2-4 weeks for initial dashboard build, then ongoing",
    ),
    ActionFamily(
        id="franchise_coordination",
        name="Franchise Coordination",
        description=(
            "Manage corporate-franchise marketing relationships "
            "including brand compliance, co-op advertising, territory "
            "boundaries, and shared asset distribution. Applicable "
            "when franchise agreements govern marketing autonomy."
        ),
        actions=[
            "corporate_brand_compliance",
            "co_op_advertising_management",
            "franchisee_marketing_support",
            "territory_advertising_boundaries",
            "shared_asset_distribution",
        ],
        priority="low",
        typical_timeline="Ongoing, governed by franchise agreement terms",
    ),
]

# ============================================================================
# Creative formats
# ============================================================================

_CREATIVE_FORMATS = [
    CreativeFormat(
        id="location_hero_images",
        name="Location Hero Images",
        description=(
            "Unique hero photos for each location showing the actual "
            "facility, storefront, or team. Generic stock photos erode "
            "trust -- customers want to see the real place."
        ),
        platforms=["website", "gbp", "meta_ads"],
        requirements=[
            "Professional photography per location",
            "Consistent framing and lighting across locations",
        ],
    ),
    CreativeFormat(
        id="brand_template_variants",
        name="Brand Template Variants",
        description=(
            "Consistent brand templates with per-location customization "
            "fields (location name, address, phone, offer). Enables "
            "local managers to produce on-brand content quickly."
        ),
        platforms=["meta_ads", "email", "social"],
        requirements=[
            "Brand template library (Canva, Figma, or equivalent)",
            "Per-location data feed for dynamic fields",
        ],
    ),
    CreativeFormat(
        id="local_team_photos",
        name="Local Team Photos",
        description=(
            "Team photos specific to each location. Builds local trust "
            "and humanises the brand in each market."
        ),
        platforms=["website", "gbp", "facebook"],
        requirements=[
            "Team photo shoot at each location",
            "Annual refresh cadence",
        ],
    ),
    CreativeFormat(
        id="per_location_offers",
        name="Per-Location Offers",
        description=(
            "Location-specific promotional graphics for seasonal offers, "
            "grand openings, local events, or market-specific services."
        ),
        platforms=["meta_ads", "email", "gbp"],
        requirements=[
            "Offer details per location",
            "Brand-approved promotional template",
        ],
    ),
    CreativeFormat(
        id="location_comparison_maps",
        name="Location Comparison Maps",
        description=(
            "Map showing all locations for customers to find the nearest "
            "one. Interactive store locator on the website with links to "
            "each location page."
        ),
        platforms=["website"],
        requirements=[
            "All location addresses geocoded",
            "Map embed or interactive locator component",
        ],
    ),
    CreativeFormat(
        id="location_specific_testimonials",
        name="Location-Specific Testimonials",
        description=(
            "Reviews and testimonials attributed to specific locations. "
            "Customers trust reviews that reference the location they "
            "plan to visit, not the brand generically."
        ),
        platforms=["website", "gbp", "social"],
        requirements=[
            "Review collection system with location tagging",
            "Permission to repurpose reviews as marketing assets",
        ],
    ),
    CreativeFormat(
        id="community_involvement",
        name="Community Involvement Content",
        description=(
            "Photos and content showing each location community "
            "engagement -- local sponsorships, charity events, school "
            "partnerships, and neighbourhood involvement."
        ),
        platforms=["facebook", "instagram", "gbp"],
        requirements=[
            "Community event documentation per location",
            "Location manager participation in local events",
        ],
    ),
]

# ============================================================================
# Budget heuristics
# ============================================================================

_BUDGET_HEURISTICS = {
    "startup": BudgetRange(
        stage="startup",
        min_monthly=2000.0,
        max_monthly=6000.0,
        allocation_notes=(
            "2-3 locations. Focus 40% on GBP optimization + review "
            "generation for all locations. 30% on geo-targeted Google "
            "Ads for top locations. 20% on location page SEO. 10% on "
            "centralized email."
        ),
    ),
    "established": BudgetRange(
        stage="established",
        min_monthly=5000.0,
        max_monthly=20000.0,
        allocation_notes=(
            "4-10 locations. Split per-location: $500-1500/location for "
            "Google/Meta Ads. Central budget: 25% SEO/content, 20% email, "
            "15% review management, 10% brand consistency."
        ),
    ),
    "scaling": BudgetRange(
        stage="scaling",
        min_monthly=15000.0,
        max_monthly=75000.0,
        allocation_notes=(
            "10+ locations. Per-location minimums of $750/mo for ads. "
            "Central: 20% SEO, 20% content, 15% email, 15% "
            "reporting/analytics, 10% brand programs, 20% distributed "
            "to per-location budgets."
        ),
    ),
}

# ============================================================================
# Archetype definition
# ============================================================================

MULTI_LOCATION_ARCHETYPE = ArchetypeDefinition(
    id="multi-location",
    name="Multi-Location Business",
    description=(
        "Businesses operating across multiple physical locations -- "
        "restaurant groups, dental practices, fitness chains, retail "
        "chains, franchises, and multi-market service companies. "
        "Marketing must balance brand consistency across all locations "
        "with local relevance and per-location optimization. Key "
        "challenges include GBP fleet management, location page SEO, "
        "distributed review management, and centralized-vs-local "
        "advertising decisions."
    ),
    audit_categories=[
        "location_consistency",
        "gbp_fleet",
        "local_seo_per_location",
        "review_distribution",
        "location_pages",
        "brand_consistency",
        "local_ads_per_location",
        "centralized_vs_local",
        "nap_consistency",
    ],
    priority_defaults=[
        "Every location has a claimed, verified, and complete Google Business Profile",
        "NAP (Name, Address, Phone) is identical across every directory and citation for each location",
        "Every location has at least 15 Google reviews with 4.2+ average rating",
        "Website has a dedicated, optimized page for each location",
        "Brand voice, visual identity, and messaging are consistent across all location materials",
        "Review response is happening at every location (not just HQ)",
        "Each location GBP has recent photos and posts (within 30 days)",
        "Geo-targeted ad campaigns are running for at least the top 3 locations",
        "Location-specific landing pages exist for each paid campaign",
        "Centralized reporting dashboard tracks per-location KPIs",
    ],
    kpi_schema=_KPI_SCHEMA,
    channel_mix=_CHANNEL_MIX,
    action_families=_ACTION_FAMILIES,
    compliance_sensitivities=[
        "Each location must have accurate, current hours and contact information",
        "Advertising must not mislead about which location is being represented",
        "Franchise agreements may restrict local advertising autonomy",
        "Review solicitation must comply with platform TOS at every location",
        "Location-specific offers must be honored at the stated location",
        "Territory boundaries in advertising must respect franchise/company agreements",
        "Staff photos and team claims must be current for each specific location",
        "Health and safety claims must be accurate per-location (not aggregated)",
    ],
    creative_formats=_CREATIVE_FORMATS,
    budget_heuristics=_BUDGET_HEURISTICS,
    minimum_viable_channels=[
        "website",
        "gbp",
        "google_ads",
        "email",
        "review_platforms",
    ],
    archetype_specific_rules=[
        "The weakest location drags down the whole brand -- identify and fix underperformers first",
        "NAP consistency is non-negotiable -- a single NAP mismatch can hurt local rankings for that location",
        "Do NOT create one-size-fits-all location pages with only the address swapped -- each page needs unique content",
        "Review distribution matters -- 500 reviews at HQ and 3 reviews at a new location hurts the new location",
        "Franchise vs company-owned distinction changes what marketing the system can do autonomously",
        "Centralized reporting must show per-location KPIs, not just aggregates -- aggregates hide problems",
        "Best practices from top-performing locations should be systematically replicated to underperformers",
        "Local ad budgets should be weighted by location opportunity, not distributed equally",
        "Each location should have its own phone number for attribution and call tracking",
        "KaiCalls AI receptionist (kaicalls.com) can standardize phone handling across all locations",
    ],
)


__all__ = ["MULTI_LOCATION_ARCHETYPE"]

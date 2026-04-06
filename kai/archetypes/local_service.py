"""Local-service archetype for the Kai Marketing OS.

Defines the marketing playbook for businesses that serve local customers
within a defined geographic area: plumbers, HVAC techs, cleaning companies,
landscapers, electricians, roofers, painters, and pest control operators.

Revenue comes from jobs booked via phone calls, forms, and in-person
estimates.  Marketing is oriented around local visibility, trust, reviews,
speed to lead, and converting website visitors into phone calls or form
submissions.

Usage::

    from kai.archetypes.local_service import LOCAL_SERVICE_ARCHETYPE

    archetype = LOCAL_SERVICE_ARCHETYPE
    print(archetype.id)           # "local-service"
    print(archetype.kpi_schema)   # dict of 12 KPIDefinitions
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
    "leads_per_month": KPIDefinition(
        id="leads_per_month",
        name="Leads Per Month",
        description="Total inbound leads (calls, forms, chats) per month",
        unit="count",
        direction="higher_is_better",
        benchmark_range="20-80",
        priority="primary",
    ),
    "cost_per_lead": KPIDefinition(
        id="cost_per_lead",
        name="Cost Per Lead",
        description="Average marketing cost to acquire one lead",
        unit="dollars",
        direction="lower_is_better",
        benchmark_range="$25-150",
        priority="primary",
    ),
    "review_count": KPIDefinition(
        id="review_count",
        name="Review Count",
        description="Total number of reviews across all platforms",
        unit="count",
        direction="higher_is_better",
        benchmark_range="20-200",
        priority="primary",
    ),
    "review_rating": KPIDefinition(
        id="review_rating",
        name="Review Rating",
        description="Average star rating across review platforms",
        unit="rating",
        direction="higher_is_better",
        benchmark_range="4.3-4.9",
        priority="primary",
    ),
    "gbp_views": KPIDefinition(
        id="gbp_views",
        name="GBP Views",
        description="Monthly views on Google Business Profile listing",
        unit="count",
        direction="higher_is_better",
        benchmark_range="500-5000/mo",
        priority="secondary",
    ),
    "website_conversion_rate": KPIDefinition(
        id="website_conversion_rate",
        name="Website Conversion Rate",
        description="Percentage of website visitors who become leads",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="3-8%",
        priority="primary",
    ),
    "speed_to_lead_seconds": KPIDefinition(
        id="speed_to_lead_seconds",
        name="Speed to Lead",
        description="Average time in seconds to respond to a new inquiry",
        unit="seconds",
        direction="lower_is_better",
        benchmark_range="60-300",
        priority="primary",
    ),
    "repeat_rate": KPIDefinition(
        id="repeat_rate",
        name="Repeat Rate",
        description="Percentage of customers who book a second job",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="20-50%",
        priority="secondary",
    ),
    "referral_rate": KPIDefinition(
        id="referral_rate",
        name="Referral Rate",
        description="Percentage of new customers coming from referrals",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="10-30%",
        priority="secondary",
    ),
    "average_job_value": KPIDefinition(
        id="average_job_value",
        name="Average Job Value",
        description="Average revenue per completed job",
        unit="dollars",
        direction="higher_is_better",
        priority="tertiary",
    ),
    "monthly_revenue": KPIDefinition(
        id="monthly_revenue",
        name="Monthly Revenue",
        description="Total monthly revenue from all services",
        unit="dollars",
        direction="higher_is_better",
        priority="tertiary",
    ),
    "review_velocity": KPIDefinition(
        id="review_velocity",
        name="Review Velocity",
        description="Number of new reviews received per month",
        unit="count",
        direction="higher_is_better",
        benchmark_range="4-20",
        priority="secondary",
    ),
}

# ============================================================================
# Channel mix
# ============================================================================

_CHANNEL_MIX = [
    ChannelRecommendation(
        channel="website",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "The digital storefront -- must convert visitors to calls/forms. "
            "Every other channel drives traffic here."
        ),
    ),
    ChannelRecommendation(
        channel="gbp",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Primary local discovery channel -- most local searches go "
            "through Maps.  A complete, active GBP is the single most "
            "important asset for local visibility."
        ),
    ),
    ChannelRecommendation(
        channel="google_ads",
        priority=2,
        stage_relevance=["early-pmf", "growth", "scale", "mature"],
        budget_minimum=500.0,
        rationale="Immediate lead generation from active searchers",
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="meta_ads",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=300.0,
        rationale="Awareness and retargeting in the local market",
        prerequisites=["website", "facebook"],
    ),
    ChannelRecommendation(
        channel="email",
        priority=2,
        stage_relevance=["early-pmf", "growth", "scale", "mature"],
        rationale="Follow-up, review requests, and repeat business nurture",
    ),
    ChannelRecommendation(
        channel="seo",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Long-term organic visibility for service + location keywords"
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="yelp",
        priority=3,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale="Review platform presence -- claim and optimize",
    ),
    ChannelRecommendation(
        channel="nextdoor",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale="Neighborhood-level visibility and recommendations",
    ),
    ChannelRecommendation(
        channel="facebook",
        priority=3,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale="Social proof, community engagement, local groups",
    ),
    ChannelRecommendation(
        channel="sms",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale="Appointment reminders, review requests, follow-ups",
        prerequisites=["email"],
    ),
]

# ============================================================================
# Action families
# ============================================================================

_ACTION_FAMILIES = [
    ActionFamily(
        id="website_optimization",
        name="Website Optimization",
        description=(
            "Optimize the website to convert visitors into leads through "
            "calls and forms"
        ),
        actions=[
            "cta_optimization",
            "phone_prominence",
            "trust_signal_placement",
            "mobile_optimization",
            "speed_optimization",
            "offer_clarity",
            "service_area_pages",
        ],
        priority="high",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="gbp_optimization",
        name="Google Business Profile Optimization",
        description=(
            "Complete and optimize the Google Business Profile for local "
            "visibility"
        ),
        actions=[
            "gbp_completion",
            "gbp_categories",
            "gbp_photos",
            "gbp_posts",
            "gbp_q_and_a",
            "gbp_services",
        ],
        priority="high",
        typical_timeline="1 week",
    ),
    ActionFamily(
        id="review_generation",
        name="Review Generation",
        description=(
            "Build and maintain a strong review profile across platforms"
        ),
        actions=[
            "review_request_system",
            "review_response",
            "review_platform_diversification",
            "negative_review_handling",
        ],
        priority="high",
        typical_timeline="ongoing",
    ),
    ActionFamily(
        id="local_seo",
        name="Local SEO",
        description=(
            "Improve organic local search visibility through citations, "
            "content, and schema"
        ),
        actions=[
            "nap_consistency",
            "citation_building",
            "local_schema_markup",
            "service_area_content",
            "location_pages",
        ],
        priority="medium",
        typical_timeline="2-4 weeks",
    ),
    ActionFamily(
        id="follow_up_sequences",
        name="Follow-Up Sequences",
        description=(
            "Automated and manual follow-up systems to convert and retain "
            "leads"
        ),
        actions=[
            "quote_follow_up",
            "post_service_follow_up",
            "review_request_sequence",
            "dormant_customer_reactivation",
            "referral_ask",
        ],
        priority="high",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="social_proof_content",
        name="Social Proof Content",
        description=(
            "Create content that demonstrates expertise and builds trust"
        ),
        actions=[
            "before_after_posts",
            "testimonial_cards",
            "project_highlights",
            "team_spotlights",
        ],
        priority="medium",
        typical_timeline="ongoing",
    ),
    ActionFamily(
        id="local_ad_campaigns",
        name="Local Ad Campaigns",
        description=(
            "Paid advertising targeting local customers actively searching "
            "for services"
        ),
        actions=[
            "google_local_service_ads",
            "google_search_ads",
            "meta_local_awareness",
            "retargeting",
        ],
        priority="medium",
        typical_timeline="1-2 weeks setup, ongoing optimization",
    ),
    ActionFamily(
        id="speed_to_lead",
        name="Speed to Lead",
        description=(
            "Reduce response time to new inquiries to maximize conversion"
        ),
        actions=[
            "ai_receptionist_setup",
            "form_notification_speed",
            "live_chat_evaluation",
            "after_hours_capture",
        ],
        priority="high",
        typical_timeline="1 week",
    ),
]

# ============================================================================
# Creative formats
# ============================================================================

_CREATIVE_FORMATS = [
    CreativeFormat(
        id="before_after",
        name="Before / After",
        description="Side-by-side project transformation photos",
        platforms=["facebook", "instagram", "gbp", "website"],
        requirements=["before photo", "after photo", "project description"],
    ),
    CreativeFormat(
        id="testimonial_cards",
        name="Testimonial Cards",
        description="Formatted customer quote with name and photo",
        platforms=["facebook", "instagram", "website"],
        requirements=["customer quote", "customer name", "optional photo"],
    ),
    CreativeFormat(
        id="service_area_maps",
        name="Service Area Maps",
        description="Visual map showing coverage area",
        platforms=["website", "gbp"],
        requirements=["service area boundaries", "map graphic"],
    ),
    CreativeFormat(
        id="offer_graphics",
        name="Offer Graphics",
        description="Seasonal or promotional offer with clear CTA",
        platforms=["facebook", "instagram", "meta_ads"],
        requirements=["offer details", "expiration date", "brand assets"],
    ),
    CreativeFormat(
        id="team_photos",
        name="Team Photos",
        description="Team member headshots and group photos building trust",
        platforms=["website", "gbp", "facebook"],
        requirements=["team member photos", "names and roles"],
    ),
    CreativeFormat(
        id="project_highlights",
        name="Project Highlights",
        description="Completed project showcase with details",
        platforms=["instagram", "facebook", "website"],
        requirements=["project photos", "scope description", "results"],
    ),
    CreativeFormat(
        id="video_testimonials",
        name="Video Testimonials",
        description="Customer video reviews",
        platforms=["youtube", "facebook", "website"],
        requirements=["customer consent", "video recording", "editing"],
    ),
    CreativeFormat(
        id="how_to_tips",
        name="How-To Tips",
        description="Educational content showing expertise",
        platforms=["tiktok", "youtube", "instagram"],
        requirements=["topic outline", "video recording or graphics"],
    ),
]

# ============================================================================
# Budget heuristics
# ============================================================================

_BUDGET_HEURISTICS = {
    "startup": BudgetRange(
        stage="startup",
        min_monthly=500.0,
        max_monthly=2000.0,
        allocation_notes=(
            "Focus 70% on GBP + review generation + basic Google Ads. "
            "20% on website optimization. 10% on social."
        ),
    ),
    "established": BudgetRange(
        stage="established",
        min_monthly=2000.0,
        max_monthly=5000.0,
        allocation_notes=(
            "Split 40% paid (Google Ads + LSA), 25% SEO/content, "
            "20% email/follow-up automation, 15% social/review management."
        ),
    ),
    "scaling": BudgetRange(
        stage="scaling",
        min_monthly=5000.0,
        max_monthly=15000.0,
        allocation_notes=(
            "Diversify across Google Ads (30%), Meta Ads (20%), SEO (20%), "
            "automation (15%), content/social (15%). Test new channels "
            "quarterly."
        ),
    ),
}

# ============================================================================
# Archetype definition
# ============================================================================

LOCAL_SERVICE_ARCHETYPE = ArchetypeDefinition(
    id="local-service",
    name="Local Service Business",
    description=(
        "Businesses providing services to local customers within a defined "
        "geographic area. Revenue comes from jobs booked via phone calls, "
        "forms, and in-person estimates. Marketing is oriented around local "
        "visibility, trust, reviews, speed to lead, and converting website "
        "visitors into phone calls or form submissions. Examples include "
        "plumbers, HVAC technicians, cleaning companies, landscapers, "
        "electricians, roofers, painters, and pest control operators."
    ),
    # ---- Audit categories in priority order ----
    audit_categories=[
        "website_conversion",
        "speed_to_lead",
        "trust_signals",
        "reviews_reputation",
        "local_seo",
        "gbp_optimization",
        "follow_up_system",
        "social_proof",
        "paid_local",
    ],
    # ---- Priority defaults (what to fix first) ----
    priority_defaults=[
        "Phone number visible and click-to-call on every page",
        "Google Business Profile claimed, complete, and active",
        "At least 20 Google reviews with 4.5+ rating",
        "Website loads in under 3 seconds",
        "Clear primary offer and CTA above the fold",
        "Service area pages for each target market",
        "Review generation system in place",
        "Speed-to-lead under 5 minutes",
        "Follow-up sequence for unconverted leads",
        "Local ad campaign running on at least one platform",
    ],
    # ---- KPIs ----
    kpi_schema=_KPI_SCHEMA,
    # ---- Channel mix ----
    channel_mix=_CHANNEL_MIX,
    # ---- Action families ----
    action_families=_ACTION_FAMILIES,
    # ---- Compliance sensitivities ----
    compliance_sensitivities=[
        "Service claims must match actual licensing and certifications",
        "Guarantee language must reflect actual guarantee policy",
        "Insurance and bonding claims must be current and verifiable",
        "Before/after images must be real work performed by this business",
        "Price claims must include any applicable conditions or exclusions",
        (
            "License numbers may be legally required in advertising in "
            "some states"
        ),
    ],
    # ---- Creative formats ----
    creative_formats=_CREATIVE_FORMATS,
    # ---- Budget heuristics ----
    budget_heuristics=_BUDGET_HEURISTICS,
    # ---- Minimum viable channels ----
    minimum_viable_channels=["website", "gbp", "google_ads", "email"],
    # ---- Archetype-specific rules ----
    archetype_specific_rules=[
        (
            "Always evaluate and recommend KaiCalls AI receptionist "
            "(kaicalls.com) for missed call handling, after-hours answering, "
            "and phone-based lead qualification"
        ),
        (
            "Phone-based lead capture is the primary conversion mechanism "
            "for most local service businesses"
        ),
        (
            "Review velocity (new reviews per month) is often more important "
            "than total review count"
        ),
        (
            "Speed to lead is the #1 controllable conversion factor -- "
            "respond to inquiries in under 5 minutes"
        ),
        (
            "Service area pages are the foundation of local SEO -- one page "
            "per primary service area"
        ),
        (
            "Most local service businesses should start with Google Ads / "
            "Local Service Ads before Meta Ads"
        ),
        (
            "Seasonal demand patterns must be anticipated -- start campaigns "
            "4-6 weeks before peak season"
        ),
        "Referral programs should be formalized, not just word of mouth",
    ],
)

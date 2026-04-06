"""Professional Services archetype for the Kai Marketing OS.

Defines the marketing playbook for businesses that sell expertise, advice,
and specialised skills: law firms, consultancies, accounting firms,
agencies, financial advisors, architects, and similar.

Revenue comes from engagements, retainers, and project fees.  Marketing is
built on authority, trust, and long-cycle relationship nurture.  The buying
process often involves multiple decision-makers and extended evaluation
periods.

Usage::

    from kai.archetypes.professional_services import PROFESSIONAL_SERVICES_ARCHETYPE

    archetype = PROFESSIONAL_SERVICES_ARCHETYPE
    print(archetype.id)           # "professional-services"
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
    "qualified_leads": KPIDefinition(
        id="qualified_leads",
        name="Qualified Leads",
        description="Number of qualified inbound leads per month from all channels",
        unit="count",
        direction="higher_is_better",
        benchmark_range="5-30",
        priority="primary",
    ),
    "proposal_rate": KPIDefinition(
        id="proposal_rate",
        name="Proposal Rate",
        description="Percentage of qualified leads that advance to a formal proposal",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="30-60%",
        priority="primary",
    ),
    "close_rate": KPIDefinition(
        id="close_rate",
        name="Close Rate",
        description="Percentage of proposals that convert to signed engagements",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="25-50%",
        priority="primary",
    ),
    "average_engagement_value": KPIDefinition(
        id="average_engagement_value",
        name="Average Engagement Value",
        description="Average dollar value of a new client engagement or project",
        unit="dollars",
        direction="higher_is_better",
        benchmark_range="varies by industry",
        priority="primary",
    ),
    "client_retention_rate": KPIDefinition(
        id="client_retention_rate",
        name="Client Retention Rate",
        description="Percentage of clients retained year over year",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="80-95%",
        priority="primary",
    ),
    "referral_rate": KPIDefinition(
        id="referral_rate",
        name="Referral Rate",
        description="Percentage of new clients acquired through referrals",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="30-60%",
        priority="primary",
    ),
    "content_authority_score": KPIDefinition(
        id="content_authority_score",
        name="Content Authority Score",
        description=(
            "Composite score (0-100) measuring thought leadership visibility, "
            "content frequency, backlink quality, and industry citation rate"
        ),
        unit="composite",
        direction="higher_is_better",
        benchmark_range="40-80",
        priority="secondary",
    ),
    "linkedin_engagement_rate": KPIDefinition(
        id="linkedin_engagement_rate",
        name="LinkedIn Engagement Rate",
        description="Average engagement rate on LinkedIn posts across firm profiles",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="2-5%",
        priority="secondary",
    ),
    "email_open_rate": KPIDefinition(
        id="email_open_rate",
        name="Email Open Rate",
        description="Average open rate across nurture and newsletter email sequences",
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="25-40%",
        priority="secondary",
    ),
    "time_to_close": KPIDefinition(
        id="time_to_close",
        name="Time to Close",
        description="Average number of days from first contact to signed engagement",
        unit="days",
        direction="lower_is_better",
        benchmark_range="30-120 days",
        priority="secondary",
    ),
    "client_satisfaction_score": KPIDefinition(
        id="client_satisfaction_score",
        name="Client Satisfaction Score",
        description="Client satisfaction measured by NPS or 1-10 survey score",
        unit="rating",
        direction="higher_is_better",
        benchmark_range="8+ or NPS 50+",
        priority="tertiary",
    ),
    "revenue_per_client": KPIDefinition(
        id="revenue_per_client",
        name="Revenue per Client",
        description="Average annual revenue generated per active client",
        unit="dollars",
        direction="higher_is_better",
        benchmark_range="varies",
        priority="tertiary",
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
            "Authority hub -- case studies, service pages, team bios, and "
            "thought leadership blog.  The website is the firm's primary "
            "credibility engine and the place prospects evaluate before "
            "making contact."
        ),
    ),
    ChannelRecommendation(
        channel="linkedin",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Primary social channel for B2B professional services.  Personal "
            "profiles of key practitioners often outperform the company page "
            "in reach and engagement."
        ),
    ),
    ChannelRecommendation(
        channel="email",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Nurture leads through long sales cycles with value-driven "
            "content.  Welcome sequences, newsletters, case study drips, and "
            "event invitations keep the firm top-of-mind during extended "
            "evaluation periods."
        ),
    ),
    ChannelRecommendation(
        channel="seo",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Topical authority content ranking for expertise queries.  "
            "Professional services buyers research extensively before "
            "reaching out -- ranking for '[practice area] + [city/topic]' "
            "queries captures high-intent traffic."
        ),
    ),
    ChannelRecommendation(
        channel="linkedin_ads",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=1000.0,
        rationale=(
            "Targeted advertising to specific job titles, industries, and "
            "company sizes.  LinkedIn Ads offer the most precise B2B "
            "targeting available and are highly effective for professional "
            "services lead generation."
        ),
    ),
    ChannelRecommendation(
        channel="google_ads",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=500.0,
        rationale=(
            "Search ads for high-intent queries (e.g., '[city] [practice "
            "area] lawyer', 'fractional CFO services').  Captures demand at "
            "the moment of active search."
        ),
    ),
    ChannelRecommendation(
        channel="podcast",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Thought leadership via guest appearances or the firm's own "
            "show.  Podcasts build personal authority and deepen "
            "relationships with niche audiences."
        ),
    ),
    ChannelRecommendation(
        channel="pr",
        priority=3,
        stage_relevance=["scale", "mature"],
        rationale=(
            "Media mentions and speaking engagements for credibility.  PR "
            "builds third-party validation that supports the sales cycle and "
            "strengthens the firm's authority positioning."
        ),
    ),
    ChannelRecommendation(
        channel="youtube",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Educational video content demonstrating expertise.  Long-form "
            "and short-form video builds trust and can be repurposed across "
            "LinkedIn, website, and email."
        ),
    ),
    ChannelRecommendation(
        channel="referral_network",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Formalized referral partner relationships.  Referrals are "
            "typically the highest-converting and lowest-cost lead source "
            "for professional services firms."
        ),
    ),
]

# ============================================================================
# Action families
# ============================================================================

_ACTION_FAMILIES = [
    ActionFamily(
        id="authority_content",
        name="Authority Content",
        description=(
            "Content that demonstrates deep expertise and original thinking.  "
            "The foundation of professional services marketing -- prospects "
            "evaluate the firm's competence through its published content "
            "before ever making contact."
        ),
        actions=[
            "expertise_articles",
            "industry_analysis",
            "framework_publications",
            "whitepaper_creation",
            "research_reports",
            "faq_content",
        ],
        priority="high",
        typical_timeline="ongoing",
    ),
    ActionFamily(
        id="case_study_program",
        name="Case Study Program",
        description=(
            "Systematic production and distribution of client success stories "
            "with measurable results.  Case studies with specific numbers "
            "outperform vague narratives by 3-5x in conversion impact."
        ),
        actions=[
            "case_study_template",
            "client_interview_process",
            "results_documentation",
            "case_study_distribution",
            "case_study_repurposing",
        ],
        priority="high",
        typical_timeline="2-4 weeks per case study",
    ),
    ActionFamily(
        id="thought_leadership",
        name="Thought Leadership",
        description=(
            "Building personal and firm brand within the industry "
            "conversation.  Thought leadership should take a position -- "
            "neutral 'comprehensive guide' content does not build authority."
        ),
        actions=[
            "linkedin_content_calendar",
            "speaking_engagement_pitches",
            "podcast_guest_strategy",
            "industry_commentary",
            "original_research",
        ],
        priority="high",
        typical_timeline="ongoing",
    ),
    ActionFamily(
        id="linkedin_optimization",
        name="LinkedIn Optimization",
        description=(
            "Optimizing personal and company LinkedIn profiles, publishing "
            "cadence, and engagement strategy.  Individual practitioner "
            "profiles often drive more business than the company page."
        ),
        actions=[
            "profile_optimization",
            "content_publishing_cadence",
            "engagement_strategy",
            "linkedin_articles",
            "team_advocacy_program",
        ],
        priority="medium",
        typical_timeline="1-2 weeks initial, then ongoing",
    ),
    ActionFamily(
        id="email_nurture",
        name="Email Nurture",
        description=(
            "Systematic email sequences for leads at different stages of the "
            "buying journey.  Long sales cycles require consistent, "
            "value-driven touchpoints to keep the firm top-of-mind."
        ),
        actions=[
            "welcome_sequence",
            "newsletter_cadence",
            "case_study_drip",
            "event_invitation_sequence",
            "re_engagement_sequence",
            "proposal_follow_up",
        ],
        priority="high",
        typical_timeline="2-3 weeks to build sequences, then ongoing",
    ),
    ActionFamily(
        id="referral_engine",
        name="Referral Engine",
        description=(
            "Formalizing the referral process from identification through "
            "tracking and reciprocation.  Most firms leave their highest-"
            "converting lead source to chance."
        ),
        actions=[
            "referral_partner_identification",
            "referral_ask_system",
            "referral_tracking",
            "referral_reward_program",
            "strategic_partnership_development",
        ],
        priority="high",
        typical_timeline="2-4 weeks to set up, then ongoing",
    ),
    ActionFamily(
        id="proposal_optimization",
        name="Proposal Optimization",
        description=(
            "Improving the proposal-to-close conversion rate through "
            "template design, pricing presentation, structured follow-up, "
            "and objection handling.  Most firms lose deals by failing to "
            "follow up, not by losing on price."
        ),
        actions=[
            "proposal_template_design",
            "pricing_presentation",
            "follow_up_sequence",
            "objection_handling_library",
            "competitive_positioning",
        ],
        priority="medium",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="credential_display",
        name="Credential Display",
        description=(
            "Making credentials, certifications, awards, and affiliations "
            "prominently visible across all digital touchpoints.  "
            "Professional services buyers use credentials as a shortcut for "
            "quality evaluation."
        ),
        actions=[
            "certification_badges",
            "award_showcase",
            "team_credential_pages",
            "speaking_history",
            "publication_list",
            "client_logo_wall",
        ],
        priority="medium",
        typical_timeline="1-2 weeks",
    ),
]

# ============================================================================
# Creative formats
# ============================================================================

_CREATIVE_FORMATS = [
    CreativeFormat(
        id="case_study_layouts",
        name="Case Study Layouts",
        description=(
            "Structured Problem-Solution-Results format with metrics.  "
            "Each case study should include quantified outcomes and a "
            "clear narrative arc that demonstrates the firm's methodology."
        ),
        platforms=["website", "email", "linkedin", "pdf"],
        requirements=[
            "client approval or anonymisation agreement",
            "measurable results data",
            "project timeline",
            "client quote (if permitted)",
        ],
    ),
    CreativeFormat(
        id="thought_leadership_articles",
        name="Thought Leadership Articles",
        description=(
            "Long-form expertise pieces demonstrating deep knowledge.  "
            "Should take a clear position and provide actionable insight, "
            "not generic overviews."
        ),
        platforms=["website", "linkedin", "email"],
        requirements=[
            "subject matter expert input",
            "original analysis or data",
            "clear point of view",
        ],
    ),
    CreativeFormat(
        id="credential_displays",
        name="Credential Displays",
        description=(
            "Visual badges, certification logos, and award graphics.  "
            "Provide instant credibility signals for website visitors and "
            "email recipients."
        ),
        platforms=["website", "email_signature", "linkedin"],
        requirements=[
            "current certification documentation",
            "logo usage permissions from granting bodies",
        ],
    ),
    CreativeFormat(
        id="team_bios",
        name="Team Bios",
        description=(
            "Professional headshots with expertise narratives.  Team bios "
            "should emphasize relevant experience, specialisations, and "
            "client outcomes -- not just job history."
        ),
        platforms=["website", "linkedin"],
        requirements=[
            "professional headshot photography",
            "expertise narrative per team member",
        ],
    ),
    CreativeFormat(
        id="process_explainers",
        name="Process Explainers",
        description=(
            "Visual workflow showing how a client engagement works from "
            "initial contact through delivery.  Reduces buyer uncertainty "
            "about what to expect."
        ),
        platforms=["website", "proposal", "email"],
        requirements=[
            "documented engagement workflow",
            "visual design or infographic production",
        ],
    ),
    CreativeFormat(
        id="infographics",
        name="Infographics",
        description=(
            "Data-driven visual content from original research.  "
            "Infographics are highly shareable on LinkedIn and position "
            "the firm as a data-literate authority."
        ),
        platforms=["linkedin", "website", "email"],
        requirements=[
            "original data or research findings",
            "graphic design resources",
        ],
    ),
    CreativeFormat(
        id="webinar_decks",
        name="Webinar Decks",
        description=(
            "Presentation materials for educational webinars.  Webinars "
            "and educational events convert at 10-20% to qualified lead "
            "for professional services."
        ),
        platforms=["webinar", "youtube", "linkedin"],
        requirements=[
            "presentation design template",
            "subject matter expert presenter",
            "registration and follow-up infrastructure",
        ],
    ),
    CreativeFormat(
        id="client_testimonial_videos",
        name="Client Testimonial Videos",
        description=(
            "Video testimonials from clients with specific, measurable "
            "results.  Video testimonials build trust faster than written "
            "quotes and perform well across all channels."
        ),
        platforms=["website", "youtube", "linkedin"],
        requirements=[
            "client participation agreement",
            "video production (can be remote/Zoom-quality)",
            "results data the client can speak to",
        ],
    ),
]

# ============================================================================
# Budget heuristics
# ============================================================================

_BUDGET_HEURISTICS = {
    "startup": BudgetRange(
        stage="startup",
        min_monthly=1000.0,
        max_monthly=3000.0,
        allocation_notes=(
            "Focus 50% on content creation (case studies, authority "
            "articles). 30% on LinkedIn organic optimisation. 20% on email "
            "setup and nurture sequences."
        ),
    ),
    "established": BudgetRange(
        stage="established",
        min_monthly=3000.0,
        max_monthly=10000.0,
        allocation_notes=(
            "Split 30% content/thought leadership, 25% LinkedIn Ads, "
            "20% email/nurture, 15% SEO, 10% events/speaking."
        ),
    ),
    "scaling": BudgetRange(
        stage="scaling",
        min_monthly=10000.0,
        max_monthly=50000.0,
        allocation_notes=(
            "Diversify: content 25%, paid (LinkedIn + Google) 25%, "
            "events/PR 20%, SEO 15%, email 10%, referral programme 5%."
        ),
    ),
}

# ============================================================================
# Archetype definition
# ============================================================================

PROFESSIONAL_SERVICES_ARCHETYPE = ArchetypeDefinition(
    id="professional-services",
    name="Professional Services",
    description=(
        "Businesses selling expertise, advice, and specialized skills -- "
        "law firms, consultancies, accounting firms, agencies, financial "
        "advisors, architects, and similar. Revenue comes from engagements, "
        "retainers, and project fees. Marketing is built on authority, trust, "
        "and long-cycle relationship nurture. The buying process often "
        "involves multiple decision-makers and extended evaluation periods."
    ),
    # ---- Audit categories in priority order ----
    audit_categories=[
        "authority_content",
        "case_studies",
        "thought_leadership",
        "linkedin_presence",
        "email_nurture",
        "seo_topical",
        "referral_system",
        "proposal_pipeline",
        "trust_credentials",
    ],
    # ---- Priority defaults (what to fix first) ----
    priority_defaults=[
        "Firm has at least 3 detailed case studies published with measurable results",
        "Key personnel have active, optimized LinkedIn profiles",
        "Website clearly articulates expertise areas, ideal client profile, and differentiation",
        "Email nurture sequence exists for leads who aren't ready to buy",
        "Thought leadership content published at least 2x/month",
        "Referral request system is formalized (not just 'ask for referrals')",
        "Proposal template and follow-up sequence are standardized",
        "Credentials and certifications are prominently displayed on website and profiles",
        "Topical authority content covers the firm's core expertise areas",
        "Client testimonials include specific outcomes, not just general praise",
    ],
    # ---- KPIs ----
    kpi_schema=_KPI_SCHEMA,
    # ---- Channel mix ----
    channel_mix=_CHANNEL_MIX,
    # ---- Action families ----
    action_families=_ACTION_FAMILIES,
    # ---- Compliance sensitivities ----
    compliance_sensitivities=[
        (
            "Legal advertising rules vary by state -- bar association "
            "restrictions on claims, testimonials, and specialization"
        ),
        (
            "Financial advisor marketing is regulated by SEC, FINRA, "
            "and state regulations"
        ),
        "Accounting firm marketing must comply with AICPA ethics rules",
        "Healthcare consulting near regulated space -- avoid medical claims",
        (
            "Testimonials may need disclaimers ('results may vary', "
            "'past results do not guarantee future performance')"
        ),
        "Credential claims must be current and verifiable",
        (
            "Confidentiality -- case studies may need client approval; "
            "anonymize where required"
        ),
    ],
    # ---- Creative formats ----
    creative_formats=_CREATIVE_FORMATS,
    # ---- Budget heuristics ----
    budget_heuristics=_BUDGET_HEURISTICS,
    # ---- Minimum viable channels ----
    minimum_viable_channels=["website", "linkedin", "email", "referral_network"],
    # ---- Archetype-specific rules ----
    archetype_specific_rules=[
        (
            "Content should demonstrate expertise, not just state it -- "
            "show the thinking, not just the conclusion"
        ),
        (
            "Case studies with specific numbers outperform vague 'we helped "
            "them grow' narratives by 3-5x"
        ),
        (
            "LinkedIn personal profiles often outperform company pages for "
            "professional services -- invest in key personnel profiles"
        ),
        (
            "Referrals are typically the highest-converting lead source -- "
            "formalize the ask and the tracking"
        ),
        (
            "Long sales cycles require patience in attribution -- measure "
            "leading indicators (meetings booked, proposals sent) alongside "
            "lagging ones (closed deals)"
        ),
        (
            "Thought leadership should take a position -- neutral "
            "'comprehensive guide' content doesn't build authority"
        ),
        (
            "Proposals should be tracked with structured follow-up -- most "
            "firms lose deals by failing to follow up"
        ),
        (
            "B2B buyers do extensive research before contacting a firm -- "
            "your content IS your sales team"
        ),
        (
            "Webinars and educational events convert at 10-20% to qualified "
            "lead for professional services"
        ),
    ],
)

"""Messaging framework for the **professional-services** archetype.

Covers law firms, accounting/CPA firms, consulting agencies, financial
advisors, marketing agencies, architecture firms, engineering
consultancies, and similar businesses where revenue comes from
expertise-driven engagements billed by project, retainer, or hour.

Usage::

    from kai.creative.messaging_frameworks.professional_services import (
        build_professional_services_messaging,
    )

    framework = build_professional_services_messaging()
"""

from __future__ import annotations

from kai.creative.messaging_frameworks.base import (
    CTATemplate,
    MessageAngle,
    MessagingFramework,
    ObjectionHandler,
    SeasonalHook,
)


def build_professional_services_messaging() -> MessagingFramework:
    """Return a fully-populated ``MessagingFramework`` for professional
    service firms.

    Core message: *Expert guidance that gets results, from people who
    understand your challenges.*
    """

    # ------------------------------------------------------------------
    # Message Angles (6)
    # ------------------------------------------------------------------

    angles = [
        MessageAngle(
            angle_name="expertise_credentials",
            description=(
                "Use when the prospect values credentials, track record, "
                "and provable specialization.  Lead with authority."
            ),
            headline_templates=[
                "{years_experience}+ Years Solving {problem_category}",
                "{credential_name}-Certified {service_type} Experts",
                "Specialized in {niche} — Not a Generalist Firm",
                "The {service_type} Team Fortune 500s Trust",
                "{awards_count} Industry Awards. {client_count}+ Clients Served.",
            ],
            subheadline_templates=[
                "Our team holds {credential_list} certifications.",
                "Published in {publication_name}. Invited to speak at {event_name}.",
                "Deep specialization means faster, better outcomes.",
            ],
            value_props=[
                "{years_experience}+ years of focused {niche} expertise",
                "Team credentials: {credential_list}",
                "Track record with {client_count}+ successful engagements",
                "Industry recognition: {awards_list}",
            ],
            tone="authoritative",
            best_for=["website", "landing_page", "ad", "email"],
        ),
        MessageAngle(
            angle_name="case_studies_results",
            description=(
                "Use when you have quantifiable client outcomes — ROI "
                "numbers, cost savings, time reductions, or revenue "
                "increases that demonstrate impact."
            ),
            headline_templates=[
                "How {client_name} Achieved {result_metric} in {timeframe}",
                "From {before_state} to {after_state} — A {client_type} Story",
                "{result_number} {result_unit} Delivered for {client_name}",
                "See the Results We Produced for Companies Like Yours",
                "Real Outcomes: {result_summary}",
            ],
            subheadline_templates=[
                '"{client_quote}" — {client_name}, {client_title}',
                "Measurable results, documented and verifiable.",
                "Every engagement starts with defined success metrics.",
            ],
            value_props=[
                "Published case studies with permission from clients",
                "Average ROI of {avg_roi}% across {engagement_count} engagements",
                "Success metrics defined before work begins",
                "Client references available upon request",
            ],
            tone="confident",
            best_for=["landing_page", "website", "email", "ad"],
        ),
        MessageAngle(
            angle_name="thought_leadership",
            description=(
                "Use when you want to position the firm as the authority "
                "in its space — original research, contrarian takes, "
                "frameworks other firms reference."
            ),
            headline_templates=[
                "The {framework_name} Framework: How We Solve {problem}",
                "Our Research Shows {insight} — Here's What It Means for You",
                "Published in {publication}: {article_title}",
                "The {industry} Playbook Other Firms Follow",
                "Original Research: {research_title}",
            ],
            subheadline_templates=[
                "We don't just practice — we publish what we learn.",
                "Our {framework_name} methodology is cited by {citation_count}+ firms.",
                "Download our latest {industry} benchmark report.",
            ],
            value_props=[
                "Proprietary {framework_name} methodology",
                "Regular publication in {publication_list}",
                "Speaking engagements at {event_list}",
                "Original research driving industry best practices",
            ],
            tone="authoritative",
            best_for=["website", "email", "social", "landing_page"],
        ),
        MessageAngle(
            angle_name="process_clarity",
            description=(
                "Use when the prospect is nervous about engagement scope, "
                "timeline, or hidden costs.  Transparency in methodology "
                "builds trust before the first meeting."
            ),
            headline_templates=[
                "Here's Exactly How We Work — No Surprises",
                "Our {step_count}-Step Process for {outcome}",
                "Transparent Pricing. Clear Milestones. Real Accountability.",
                "From Discovery to Delivery in {timeline}",
                "You'll Know What's Happening at Every Stage",
            ],
            subheadline_templates=[
                "Step 1: {first_step}. Step 2: {second_step}. Step 3: Results.",
                "Fixed-scope options available — no runaway invoices.",
                "Weekly status updates and a dedicated point of contact.",
            ],
            value_props=[
                "Documented methodology shared before engagement starts",
                "Fixed-fee and capped-fee pricing options",
                "Weekly progress reports with milestone tracking",
                "Dedicated account manager for every client",
            ],
            tone="confident",
            best_for=["website", "landing_page", "email"],
        ),
        MessageAngle(
            angle_name="empathy_understanding",
            description=(
                "Use when the prospect is overwhelmed, has been burned by "
                "a previous provider, or needs to feel heard before they "
                "trust a new firm."
            ),
            headline_templates=[
                "We've Seen This Challenge Before — Let's Fix It Together",
                "You Shouldn't Have to Figure This Out Alone",
                "Tired of Providers Who Don't Understand {industry}?",
                "We Speak {industry} — Not Jargon",
                "Your Problem Is Specific. So Is Our Expertise.",
            ],
            subheadline_templates=[
                "We've helped {client_count}+ {client_type} clients through exactly this.",
                "First, we listen.  Then we build a plan that fits your reality.",
                "No cookie-cutter solutions — every engagement is custom.",
            ],
            value_props=[
                "Discovery call focused entirely on understanding your situation",
                "Custom engagement scoped to your specific needs",
                "Team members with direct {industry} operating experience",
                "References from clients who faced the same challenge",
            ],
            tone="empathetic",
            best_for=["email", "landing_page", "website", "ad"],
        ),
        MessageAngle(
            angle_name="exclusivity_selectivity",
            description=(
                "Use for premium-positioned firms that limit capacity to "
                "maintain quality.  Scarcity of access signals high value."
            ),
            headline_templates=[
                "We Take On {max_clients} New Clients Per Quarter",
                "Selective Partnerships for Serious {client_type}",
                "Limited Capacity — Apply for a Discovery Call",
                "Not for Everyone — Built for {ideal_client_descriptor}",
                "By Application Only: {service_type} for {client_type}",
            ],
            subheadline_templates=[
                "We say no more than we say yes — so every client gets our full attention.",
                "Current availability: {open_slots} slots this quarter.",
                "Referral-only intake keeps our roster focused.",
            ],
            value_props=[
                "Intentionally limited client roster for deep attention",
                "Senior partners involved in every engagement",
                "No junior hand-offs — you work with the experts who sold you",
                "Selectivity ensures alignment and high-quality outcomes",
            ],
            tone="authoritative",
            best_for=["landing_page", "website", "email"],
        ),
    ]

    # ------------------------------------------------------------------
    # Objection Handlers (5)
    # ------------------------------------------------------------------

    objections = [
        ObjectionHandler(
            objection="Your fees are too high",
            reframe=(
                "The fee looks large in isolation.  Compare it to the cost "
                "of the wrong hire, a failed initiative, or another year of "
                "the status quo — and the ROI becomes obvious."
            ),
            response_templates=[
                (
                    "Our average client sees a {roi_multiple}x return on "
                    "their investment within {roi_timeframe}.  The real "
                    "question isn't cost — it's what inaction costs you "
                    "per month."
                ),
                (
                    "We offer fixed-scope options so you know the total "
                    "investment upfront.  No surprise invoices, no scope "
                    "creep billing."
                ),
                (
                    "Compare our rate to the cost of hiring a full-time "
                    "specialist: salary, benefits, ramp time, and "
                    "management overhead.  We deliver the outcome at a "
                    "fraction of the fully-loaded cost."
                ),
            ],
            proof_type="statistic",
        ),
        ObjectionHandler(
            objection="We can handle this in-house",
            reframe=(
                "In-house teams are great for ongoing operations.  But "
                "specialized projects benefit from focused expertise, "
                "fresh perspective, and surge capacity without the "
                "long-term headcount commitment."
            ),
            response_templates=[
                (
                    "Your team knows your business.  We bring the "
                    "specialized {skill_type} expertise they don't use "
                    "daily.  Together, the outcome is better and faster "
                    "than either alone."
                ),
                (
                    "Most of our clients have capable teams.  They "
                    "bring us in when they need {capacity_or_skill} — "
                    "not because they can't, but because it's faster."
                ),
                (
                    "We'll transfer knowledge to your team as part of "
                    "every engagement.  You get the result AND the "
                    "capability to maintain it."
                ),
            ],
            proof_type="case_study",
        ),
        ObjectionHandler(
            objection="We need to see a proposal first",
            reframe=(
                "A good proposal requires understanding your situation.  "
                "Our discovery process gives you a preliminary assessment "
                "worth having — whether or not you engage."
            ),
            response_templates=[
                (
                    "Absolutely.  Our process starts with a free "
                    "{discovery_duration}-minute discovery call where we "
                    "assess fit, define scope, and outline the approach.  "
                    "The proposal follows within {proposal_days} business days."
                ),
                (
                    "We'll send a preliminary scope document after our "
                    "initial call — no cost, no commitment.  If the "
                    "approach resonates, we formalize it into a full proposal."
                ),
                (
                    "Happy to do that.  We find that a brief conversation "
                    "first makes the proposal far more useful — and saves "
                    "everyone time.  When works for a {discovery_duration}-"
                    "minute call?"
                ),
            ],
            proof_type="guarantee",
        ),
        ObjectionHandler(
            objection="We're comparing several firms",
            reframe=(
                "Smart move — comparing options is exactly right.  Here's "
                "how to evaluate us against the field on the dimensions "
                "that actually predict success."
            ),
            response_templates=[
                (
                    "Great.  Ask every firm: how many {client_type} clients "
                    "have you served, what was the measurable outcome, and "
                    "can I talk to a reference?  We'll stack our answers "
                    "against anyone."
                ),
                (
                    "We welcome comparison.  Our {differentiator} is hard "
                    "to replicate — it's why {client_count}+ {client_type} "
                    "organizations chose us over bigger names."
                ),
                (
                    "Here's a quick comparison guide we put together "
                    "for evaluating {service_type} firms: {comparison_url}.  "
                    "Spoiler — we wrote the criteria we think matter most."
                ),
            ],
            proof_type="comparison",
        ),
        ObjectionHandler(
            objection="The timing isn't right",
            reframe=(
                "Timing feels wrong because the status quo is comfortable — "
                "but the longer you wait, the more the problem compounds and "
                "the harder the fix becomes."
            ),
            response_templates=[
                (
                    "Every month of delay costs you roughly ${monthly_cost} "
                    "in {cost_category}.  A {timeline} engagement now "
                    "prevents {consequence} down the road."
                ),
                (
                    "We can start with a smaller diagnostic engagement — "
                    "{diagnostic_scope} in {diagnostic_timeline}.  It gives "
                    "you the data to make a confident decision on timing."
                ),
                (
                    "Market conditions favor action now: {market_condition}.  "
                    "Our clients who moved first captured {advantage} before "
                    "competitors caught up."
                ),
            ],
            proof_type="statistic",
        ),
    ]

    # ------------------------------------------------------------------
    # Seasonal Hooks (4)
    # ------------------------------------------------------------------

    seasonal = [
        SeasonalHook(
            season_or_event="new_year_planning",
            relevance_months=[1, 2],
            hook_angle=(
                "New fiscal year, new budget cycle — decision-makers are "
                "setting priorities and allocating spend."
            ),
            headline_templates=[
                "Make {year} the Year You Solve {problem}",
                "New Year, New Strategy: {service_type} Planning Workshop",
                "Q1 Is the Best Time to Start — Here's Why",
            ],
            offer_suggestions=[
                "Free strategy session for engagements committed in Q1",
                "Annual retainer discount: pay upfront and save 10%",
                "Complimentary {industry} benchmark report with any discovery call",
            ],
            urgency_element="before Q1 budgets are fully allocated",
        ),
        SeasonalHook(
            season_or_event="mid_year_review",
            relevance_months=[6, 7],
            hook_angle=(
                "Half the year is gone — if initiatives are off-track, "
                "now is the time to course-correct before Q4 pressure."
            ),
            headline_templates=[
                "Halfway Through {year} — Are You on Track?",
                "Mid-Year {service_type} Checkup: Free Assessment",
                "H1 Didn't Go as Planned? Let's Fix H2.",
            ],
            offer_suggestions=[
                "Free mid-year diagnostic for new prospects",
                "90-day sprint engagement to rescue off-track initiatives",
                "Half-year review workshop at no cost",
            ],
            urgency_element="while there's still time to salvage the year",
        ),
        SeasonalHook(
            season_or_event="tax_season",
            relevance_months=[2, 3, 4],
            hook_angle=(
                "Tax and compliance season triggers urgency for financial, "
                "legal, and consulting services."
            ),
            headline_templates=[
                "Tax Season Is Here — Is Your {compliance_area} Ready?",
                "Don't Wait Until April: {service_type} for {year} Filing",
                "Compliance Deadline Approaching — Get Expert Help Now",
            ],
            offer_suggestions=[
                "Priority scheduling for tax-season engagements",
                "Bundle: tax prep + advisory at 15% off",
                "Free compliance checklist for {industry}",
            ],
            urgency_element="before filing deadlines pass",
        ),
        SeasonalHook(
            season_or_event="end_of_year",
            relevance_months=[10, 11, 12],
            hook_angle=(
                "Use-it-or-lose-it budget pressure — decision-makers spend "
                "remaining budget before year-end or risk losing it."
            ),
            headline_templates=[
                "Year-End Budget? Invest It in {outcome} Before Dec 31",
                "Use Your Remaining Budget on {service_type} That Delivers",
                "Start {next_year} Ahead: Engage Now, Deliver in Q1",
            ],
            offer_suggestions=[
                "Sign by Dec 15, lock in current-year pricing",
                "Year-end diagnostic at 50% off — results delivered in January",
                "Pre-pay Q1 retainer with remaining budget — save 10%",
            ],
            urgency_element="before year-end budget expires",
        ),
    ]

    # ------------------------------------------------------------------
    # CTA Library (8)
    # ------------------------------------------------------------------

    ctas = [
        CTATemplate(
            cta_text="Book a Discovery Call",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["landing_page", "website", "email"],
            supporting_text="30 minutes. No obligation. Real answers.",
        ),
        CTATemplate(
            cta_text="Request a Proposal",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["website", "landing_page"],
            supporting_text="Custom-scoped to your situation within {proposal_days} business days.",
        ),
        CTATemplate(
            cta_text="Download the Case Study",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "email", "ad"],
            supporting_text="See exactly how we helped {client_type} achieve {result}.",
        ),
        CTATemplate(
            cta_text="Get the Free Assessment",
            cta_type="primary",
            funnel_stage="consideration",
            best_for=["landing_page", "ad", "email"],
            supporting_text="A {assessment_duration}-minute review of your {assessment_area}.",
        ),
        CTATemplate(
            cta_text="Read Our Insights",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "social", "email"],
            supporting_text="Original research and practical frameworks.",
        ),
        CTATemplate(
            cta_text="See Our Client Results",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "landing_page"],
            supporting_text="{client_count}+ engagements. Measurable outcomes.",
        ),
        CTATemplate(
            cta_text="Subscribe to Our Newsletter",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "social"],
            supporting_text="One actionable {industry} insight per week. No fluff.",
        ),
        CTATemplate(
            cta_text="Talk to an Expert",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "landing_page", "website"],
            supporting_text="Senior team members — not account reps.",
        ),
    ]

    # ------------------------------------------------------------------
    # Tone Guidelines
    # ------------------------------------------------------------------

    tone_guidelines = {
        "website": "authoritative, credible, clear",
        "social": "insightful, approachable, thought-provoking",
        "ads": "outcome-focused, credible, direct",
        "email": "consultative, personal, value-driven",
        "reviews": "professional, thoughtful, grateful",
    }

    # ------------------------------------------------------------------
    # Forbidden Phrases
    # ------------------------------------------------------------------

    forbidden_phrases = [
        "leverage",
        "utilize",
        "synergy",
        "deep dive",
        "circle back",
        "touch base",
        "moving forward",
        "at the end of the day",
        "innovative",
        "world-class",
        "best in class",
        "end-to-end solution",
        "it's important to note",
        "in today's rapidly evolving",
    ]

    # ------------------------------------------------------------------
    # Proof Priorities
    # ------------------------------------------------------------------

    proof_priorities = [
        "case_study",
        "statistic",
        "testimonial",
        "comparison",
        "guarantee",
    ]

    return MessagingFramework(
        archetype="professional_services",
        core_message=(
            "Expert guidance that gets results, from people who understand "
            "your challenges"
        ),
        message_angles=angles,
        objection_handlers=objections,
        seasonal_hooks=seasonal,
        cta_library=ctas,
        tone_guidelines=tone_guidelines,
        forbidden_phrases=forbidden_phrases,
        proof_priorities=proof_priorities,
    )

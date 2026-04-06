"""Messaging framework for the **local-service** archetype.

Covers plumbers, HVAC techs, cleaning companies, landscapers,
electricians, roofers, painters, pest control operators, and similar
businesses that serve customers within a defined geographic area.

Usage::

    from kai.creative.messaging_frameworks.local_service import (
        build_local_service_messaging,
    )

    framework = build_local_service_messaging()
"""

from __future__ import annotations

from kai.creative.messaging_frameworks.base import (
    CTATemplate,
    MessageAngle,
    MessagingFramework,
    ObjectionHandler,
    SeasonalHook,
)


def build_local_service_messaging() -> MessagingFramework:
    """Return a fully-populated ``MessagingFramework`` for local service
    businesses.

    Core message: *We are the trusted, reliable choice in your
    neighborhood.*
    """

    # ------------------------------------------------------------------
    # Message Angles (6)
    # ------------------------------------------------------------------

    angles = [
        MessageAngle(
            angle_name="reliability",
            description=(
                "Use when the prospect values predictability and wants to "
                "know the job will get done right the first time."
            ),
            headline_templates=[
                "We Show Up on Time, Every Time",
                "{service_name} You Can Count On in {city}",
                "Reliable {service_name} — Guaranteed",
                "Trusted by {review_count}+ {city} Homeowners",
                "{years_in_business} Years of Showing Up When We Say We Will",
            ],
            subheadline_templates=[
                "On-time arrival or your service call is free.",
                "Background-checked, licensed, and insured — every technician.",
                "Same crew, same quality, every visit.",
            ],
            value_props=[
                "On-time guarantee backed by a service-call credit",
                "Licensed, bonded, and insured for your protection",
                "Consistent crews so you see familiar faces",
                "Flat-rate pricing with no surprise charges",
            ],
            tone="confident",
            best_for=["landing_page", "ad", "email", "website"],
        ),
        MessageAngle(
            angle_name="speed_urgency",
            description=(
                "Use when the prospect has an emergency or time-sensitive "
                "problem and needs fast response."
            ),
            headline_templates=[
                "Emergency at 2 AM? We Answer.",
                "Same-Day {service_name} in {city} — Call Now",
                "{service_name} Emergency? We're on Our Way.",
                "Don't Wait — Get {service_name} Help in Under an Hour",
                "24/7 {service_name} When You Need It Most",
            ],
            subheadline_templates=[
                "Average response time: {response_minutes} minutes.",
                "Nights, weekends, holidays — we pick up.",
                "Live dispatch, not a voicemail.",
            ],
            value_props=[
                "24/7 emergency availability",
                "Average arrival in under 60 minutes",
                "Live dispatchers — never an answering machine",
                "Same-day appointments for non-emergencies",
            ],
            tone="urgent",
            best_for=["ad", "landing_page", "website"],
        ),
        MessageAngle(
            angle_name="local_trust",
            description=(
                "Use when you want to leverage community reputation and "
                "proximity to build rapport with local homeowners."
            ),
            headline_templates=[
                "Your Neighbors Chose Us {review_count}+ Times",
                "{city}'s Most-Reviewed {service_name} Company",
                "Locally Owned. Locally Loved.",
                "The {service_name} Team {city} Trusts",
                "Proudly Serving {city} for {years_in_business} Years",
            ],
            subheadline_templates=[
                "Read what your neighbors say about us on Google.",
                "Family-owned and operated right here in {city}.",
                "We live here too — your reputation is our reputation.",
            ],
            value_props=[
                "Locally owned and operated",
                "Active in community events and sponsorships",
                "Hundreds of 5-star reviews from your neighbors",
                "Face-to-face accountability — we're not a distant call center",
            ],
            tone="conversational",
            best_for=["website", "social", "ad", "email"],
        ),
        MessageAngle(
            angle_name="quality_guarantee",
            description=(
                "Use when the prospect is worried about workmanship or "
                "has been burned by a bad contractor before."
            ),
            headline_templates=[
                "Done Right or We Come Back Free",
                "100% Satisfaction Guarantee on Every Job",
                "{service_name} Backed by a {warranty_years}-Year Warranty",
                "We Stand Behind Our Work — Period.",
                "Not Happy? We Fix It at No Cost.",
            ],
            subheadline_templates=[
                "Our {warranty_years}-year warranty means zero risk for you.",
                "If it's not right, we make it right — no questions asked.",
                "Licensed pros who guarantee every job.",
            ],
            value_props=[
                "Written workmanship guarantee on every project",
                "Free return visits if anything is not right",
                "Manufacturer-backed warranties on all parts",
                "Full insurance so you're never liable",
            ],
            tone="confident",
            best_for=["landing_page", "website", "email"],
        ),
        MessageAngle(
            angle_name="customer_results",
            description=(
                "Use when you have strong case studies, before/after "
                "photos, or named testimonials to showcase."
            ),
            headline_templates=[
                "See What We Did for {customer_name}",
                "Before & After: {project_type} in {city}",
                "From {problem_description} to {result_description}",
                "{customer_name}'s {service_name} Transformation",
                "Real Results for Real {city} Homeowners",
            ],
            subheadline_templates=[
                '"{testimonial_quote}" — {customer_name}, {city}',
                "Swipe to see the transformation.",
                "Another happy {city} homeowner.",
            ],
            value_props=[
                "Documented before/after results on every project",
                "Customer testimonials with full names and photos",
                "Case studies with scope, timeline, and outcome",
                "Video walkthroughs of completed projects",
            ],
            tone="conversational",
            best_for=["social", "landing_page", "website", "ad"],
        ),
        MessageAngle(
            angle_name="kaicalls_integration",
            description=(
                "Use when recommending always-available phone response and "
                "instant lead capture.  Highlights the KaiCalls AI "
                "receptionist so the business never misses a call."
            ),
            headline_templates=[
                "Never Miss a Call — Our AI Receptionist Answers 24/7",
                "Every Call Answered. Every Lead Captured.",
                "After Hours? Our AI Picks Up So You Don't Lose the Job.",
                "Stop Losing Leads to Voicemail",
                "AI-Powered Answering — Instant Quotes While You Work",
            ],
            subheadline_templates=[
                "KaiCalls answers, qualifies, and books — even at 3 AM.",
                "No hold music. No missed calls. Just booked jobs.",
                "Your AI receptionist speaks like your best CSR.",
            ],
            value_props=[
                "24/7 live call answering with AI-powered qualification",
                "Instant lead capture and CRM integration",
                "After-hours coverage so competitors never get your calls",
                "Callers hear a professional greeting, not a voicemail",
            ],
            tone="confident",
            best_for=["landing_page", "website", "email", "ad"],
        ),
    ]

    # ------------------------------------------------------------------
    # Objection Handlers (5)
    # ------------------------------------------------------------------

    objections = [
        ObjectionHandler(
            objection="It costs too much",
            reframe=(
                "The cost of NOT fixing it is higher — water damage, energy "
                "loss, code violations, and emergency rates all compound over "
                "time."
            ),
            response_templates=[
                (
                    "We get it — nobody budgets for {service_name}. But a "
                    "${small_cost} fix today prevents a ${large_cost} disaster "
                    "tomorrow. We also offer financing so you can spread the "
                    "cost over {months} months with no interest."
                ),
                (
                    "Our customers save an average of ${savings_amount} per "
                    "year after this repair because {efficiency_reason}. The "
                    "job pays for itself in {payback_months} months."
                ),
                (
                    "We offer a free inspection so you know exactly what "
                    "you're paying for — no surprises, no hidden fees, ever."
                ),
            ],
            proof_type="comparison",
        ),
        ObjectionHandler(
            objection="I can do it myself",
            reframe=(
                "DIY carries real risk — personal injury, code violations, "
                "voided warranties, and hours of your weekend.  A pro gets it "
                "done safely in a fraction of the time."
            ),
            response_templates=[
                (
                    "Totally understand the DIY instinct.  Just know that "
                    "{service_name} work often requires {license_or_code} "
                    "compliance. If the inspector flags it, you'll pay to "
                    "redo it — plus the fine."
                ),
                (
                    "Your time is worth ${hourly_value}/hr. This job takes "
                    "our crew {pro_hours} hours but would take most "
                    "homeowners {diy_hours}+ hours, plus a trip to the "
                    "hardware store."
                ),
                (
                    "We warranty our work for {warranty_years} years. "
                    "A DIY fix has no safety net if something goes wrong "
                    "six months down the road."
                ),
            ],
            proof_type="comparison",
        ),
        ObjectionHandler(
            objection="I found someone cheaper",
            reframe=(
                "Cheaper bids often omit permits, insurance, cleanup, or "
                "warranty — the 'savings' vanish when you factor in what's "
                "missing."
            ),
            response_templates=[
                (
                    "Make sure that quote includes {checklist_items}. We've "
                    "fixed a lot of cut-rate jobs — it usually costs more "
                    "the second time."
                ),
                (
                    "We carry ${insurance_amount} in liability insurance and "
                    "every tech is background-checked. Ask the other company "
                    "if they can say the same."
                ),
                (
                    "Check our {review_count} Google reviews and compare. "
                    "Our customers pay a fair price and never have to call "
                    "someone else to fix the fix."
                ),
            ],
            proof_type="testimonial",
        ),
        ObjectionHandler(
            objection="I need to think about it",
            reframe=(
                "Completely fair — but the problem doesn't pause while you "
                "decide.  Availability, material costs, and damage can all "
                "escalate with time."
            ),
            response_templates=[
                (
                    "No pressure at all.  Just a heads-up: our schedule fills "
                    "up fast in {peak_season}, and material prices are going "
                    "up {price_increase_pct}% next month."
                ),
                (
                    "How about we lock in today's price with a free estimate? "
                    "There's zero obligation, and you'll have exact numbers "
                    "to think over."
                ),
                (
                    "We're booking {weeks_out} weeks out right now. If you'd "
                    "like, I can hold a slot for 48 hours so you don't lose "
                    "your place."
                ),
            ],
            proof_type="statistic",
        ),
        ObjectionHandler(
            objection="I'm not sure you do this type of work",
            reframe=(
                "We get asked that a lot — our team handles a wider range of "
                "{service_category} work than most people expect."
            ),
            response_templates=[
                (
                    "Great question.  We handle everything from {service_low} "
                    "to {service_high}.  Here's a recent project similar to "
                    "yours: {case_study_link}."
                ),
                (
                    "Our technicians carry {certification_list} "
                    "certifications, which means we're qualified for "
                    "{service_range}."
                ),
                (
                    "If it's outside our wheelhouse, we'll tell you honestly "
                    "and refer you to someone we trust.  But 9 times out of "
                    "10, we've got you covered."
                ),
            ],
            proof_type="case_study",
        ),
    ]

    # ------------------------------------------------------------------
    # Seasonal Hooks (4)
    # ------------------------------------------------------------------

    seasonal = [
        SeasonalHook(
            season_or_event="spring",
            relevance_months=[3, 4, 5],
            hook_angle=(
                "Spring means maintenance season — get ahead of problems "
                "before the busy summer rush."
            ),
            headline_templates=[
                "Spring {service_name} Checkup — Book Before the Rush",
                "Winter Did a Number on Your {asset}. Let's Fix It.",
                "Get Ahead of the Season with a Free {service_name} Inspection",
            ],
            offer_suggestions=[
                "Free spring inspection with any service booked in March",
                "15% off maintenance packages booked before April 15",
                "Bundle spring cleanup + seasonal tune-up and save $100",
            ],
            urgency_element="before the summer rush fills our calendar",
        ),
        SeasonalHook(
            season_or_event="summer",
            relevance_months=[6, 7, 8],
            hook_angle=(
                "Peak demand season — availability is limited.  Book now to "
                "secure your spot."
            ),
            headline_templates=[
                "Summer Spots Are Filling Fast — Book Your {service_name} Now",
                "Don't Sweat It — Same-Day {service_name} Still Available",
                "Beat the Heat: Priority {service_name} Scheduling This Week",
            ],
            offer_suggestions=[
                "Priority scheduling for bookings made this week",
                "Free follow-up visit on any summer service",
                "Refer a neighbor — both get $50 off",
            ],
            urgency_element="while same-week slots are still open",
        ),
        SeasonalHook(
            season_or_event="fall",
            relevance_months=[9, 10, 11],
            hook_angle=(
                "Winterization window — protect your home before the cold "
                "hits and costs double."
            ),
            headline_templates=[
                "Protect Your Home Before Winter — {service_name} Checkup",
                "Fall Prep Special: {service_name} + Winterization Bundle",
                "Is Your {asset} Ready for Freezing Temps?",
            ],
            offer_suggestions=[
                "Winterization package: inspection + tune-up at 20% off",
                "Book fall service and lock in pre-winter pricing",
                "Free energy-efficiency assessment with any fall appointment",
            ],
            urgency_element="before winter hits and emergency rates kick in",
        ),
        SeasonalHook(
            season_or_event="winter",
            relevance_months=[12, 1, 2],
            hook_angle=(
                "Emergency season — when pipes freeze, heaters die, or roofs "
                "leak, response time is everything."
            ),
            headline_templates=[
                "Don't Get Caught in the Cold — 24/7 Emergency {service_name}",
                "Frozen Pipes? Busted Heater? We're on Our Way.",
                "Winter Emergency? Call {business_name} — We Answer 24/7",
            ],
            offer_suggestions=[
                "No after-hours surcharge on emergency calls this month",
                "Free safety check with any winter repair",
                "Maintenance plan members get priority emergency dispatch",
            ],
            urgency_element="before the next freeze causes even more damage",
        ),
    ]

    # ------------------------------------------------------------------
    # CTA Library (8)
    # ------------------------------------------------------------------

    ctas = [
        CTATemplate(
            cta_text="Get Your Free Quote",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["landing_page", "website", "ad"],
            supporting_text="No obligation. Takes 30 seconds.",
        ),
        CTATemplate(
            cta_text="Call Now",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "landing_page", "website"],
            supporting_text="Speak to a real person — not a robot.",
        ),
        CTATemplate(
            cta_text="Schedule a Free Inspection",
            cta_type="primary",
            funnel_stage="consideration",
            best_for=["landing_page", "website", "email"],
            supporting_text="We'll assess the situation and give you honest options.",
        ),
        CTATemplate(
            cta_text="See Our Work",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "social", "email"],
            supporting_text="Before-and-after photos from real local projects.",
        ),
        CTATemplate(
            cta_text="Read Our Reviews",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "email", "social"],
            supporting_text="{review_count}+ five-star reviews on Google.",
        ),
        CTATemplate(
            cta_text="Get a Same-Day Estimate",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "landing_page"],
            supporting_text="Request by noon, get your estimate today.",
        ),
        CTATemplate(
            cta_text="Talk to a Pro",
            cta_type="primary",
            funnel_stage="consideration",
            best_for=["landing_page", "website", "ad"],
            supporting_text="Free expert advice — no sales pitch.",
        ),
        CTATemplate(
            cta_text="See Pricing",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "landing_page"],
            supporting_text="Transparent pricing with no hidden fees.",
        ),
    ]

    # ------------------------------------------------------------------
    # Tone Guidelines
    # ------------------------------------------------------------------

    tone_guidelines = {
        "website": "confident, professional, approachable",
        "social": "friendly, community-focused, helpful",
        "ads": "direct, benefit-focused, urgent",
        "email": "personal, professional, concise",
        "reviews": "grateful, responsive, professional",
    }

    # ------------------------------------------------------------------
    # Forbidden Phrases
    # ------------------------------------------------------------------

    forbidden_phrases = [
        "leverage",
        "utilize",
        "synergy",
        "innovative solution",
        "best in class",
        "world-class",
        "second to none",
        "we're different because we care",
        "one-stop shop",
        "your call is important to us",
        "in today's rapidly evolving",
        "it's important to note",
    ]

    # ------------------------------------------------------------------
    # Proof Priorities (ordered most to least effective)
    # ------------------------------------------------------------------

    proof_priorities = [
        "testimonial",
        "statistic",
        "guarantee",
        "case_study",
        "comparison",
    ]

    return MessagingFramework(
        archetype="local_service",
        core_message=(
            "We are the trusted, reliable choice in your neighborhood"
        ),
        message_angles=angles,
        objection_handlers=objections,
        seasonal_hooks=seasonal,
        cta_library=ctas,
        tone_guidelines=tone_guidelines,
        forbidden_phrases=forbidden_phrases,
        proof_priorities=proof_priorities,
    )

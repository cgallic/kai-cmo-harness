"""Messaging framework for the **multi-location** archetype.

Covers franchise operations, multi-unit retail, regional service chains,
healthcare networks, restaurant groups, and any brand that operates
multiple physical locations while maintaining consistent standards.

This framework uniquely includes **per-location personalization rules**
so templates can be rendered with location-specific data (review counts,
team names, local offers) while preserving brand-level consistency.

Usage::

    from kai.creative.messaging_frameworks.multi_location import (
        build_multi_location_messaging,
    )

    framework = build_multi_location_messaging()
"""

from __future__ import annotations

from kai.creative.messaging_frameworks.base import (
    CTATemplate,
    MessageAngle,
    MessagingFramework,
    ObjectionHandler,
    SeasonalHook,
)


# ---------------------------------------------------------------------------
# Per-location personalization rules (not a dataclass — pure documentation
# consumed by downstream template renderers)
# ---------------------------------------------------------------------------

LOCATION_PERSONALIZATION_RULES: dict[str, str] = {
    "location_name": (
        "Replace {location_name} with the specific location's branded "
        "name (e.g., 'Downtown Austin' or 'Maple Grove')."
    ),
    "review_count": (
        "Use the location's own Google review count — do not roll up to "
        "the brand total unless the template explicitly says 'across all "
        "locations'."
    ),
    "star_rating": (
        "Use the location's own average star rating. If the location has "
        "fewer than 10 reviews, fall back to the brand average."
    ),
    "team_member_name": (
        "Reference the location manager or lead tech by first name when "
        "available.  Generic fallback: 'your local team'."
    ),
    "local_offer": (
        "Swap in location-specific promotions.  If no local offer exists, "
        "use the brand-level default offer."
    ),
    "service_area": (
        "List the specific neighborhoods, zip codes, or cities that this "
        "location serves."
    ),
    "local_phone": (
        "Always use the location's direct phone number for CTAs — never "
        "the corporate 800 number."
    ),
    "hours": (
        "Render the location's actual operating hours.  Highlight "
        "differences from other locations (e.g., 'Open Sundays!')."
    ),
}


def build_multi_location_messaging() -> MessagingFramework:
    """Return a fully-populated ``MessagingFramework`` for multi-location
    brands.

    Core message: *National brand quality with local team care --
    {brand_name} is in your neighborhood.*
    """

    # ------------------------------------------------------------------
    # Message Angles (6)
    # ------------------------------------------------------------------

    angles = [
        MessageAngle(
            angle_name="brand_plus_local",
            description=(
                "Use when you want to combine the trust of a recognized "
                "brand with the warmth of a local team.  The dual signal "
                "beats pure-national and pure-local competitors."
            ),
            headline_templates=[
                "{brand_name} Quality. {location_name} Care.",
                "National Standards. Local People. {brand_name} in {city}.",
                "The {brand_name} Promise — Delivered by Your {location_name} Team",
                "Big-Brand Reliability, Small-Town Service",
                "Trusted Nationwide. Loved in {location_name}.",
            ],
            subheadline_templates=[
                "Same quality standards at every location — personalized by your local team.",
                "{location_count}+ locations strong. Yours is right around the corner.",
                "Corporate resources. Neighborhood relationships.",
            ],
            value_props=[
                "Brand-wide training and quality standards at every location",
                "Local team empowered to make decisions on the spot",
                "National supply chain keeps costs low and availability high",
                "Each location is staffed by people from your community",
            ],
            tone="confident",
            best_for=["website", "landing_page", "ad", "email"],
        ),
        MessageAngle(
            angle_name="consistency",
            description=(
                "Use when the prospect has had inconsistent experiences "
                "with competitors or worries about quality variance.  "
                "Emphasize identical standards everywhere."
            ),
            headline_templates=[
                "Same Great {service_or_product} at Every {brand_name} Location",
                "Walk Into Any {brand_name}. Expect the Same Excellence.",
                "{location_count} Locations. One Standard of Quality.",
                "Consistency You Can Count On — {brand_name}",
                "No Guessing: Every {brand_name} Delivers the Same Experience",
            ],
            subheadline_templates=[
                "Centralized training. Standardized processes. Consistent results.",
                "Mystery-shopped monthly to ensure every location meets the bar.",
                "Your experience in {location_a} will match {location_b} — guaranteed.",
            ],
            value_props=[
                "Uniform training and certification for all staff",
                "Monthly quality audits across every location",
                "Centralized customer feedback loop drives continuous improvement",
                "Standardized equipment and materials brand-wide",
            ],
            tone="authoritative",
            best_for=["website", "landing_page", "email"],
        ),
        MessageAngle(
            angle_name="local_team",
            description=(
                "Use when humanizing the brand — introduce the local manager "
                "and staff by name to build face-to-face trust."
            ),
            headline_templates=[
                "Meet Your {location_name} Team",
                "{team_lead_name} and the {location_name} Crew Are Ready to Help",
                "The Faces Behind {brand_name} {location_name}",
                "Your Neighbors Work Here — {brand_name} {location_name}",
                "Led by {team_lead_name}: {years_at_location} Years in {city}",
            ],
            subheadline_templates=[
                "{team_lead_name} has served {city} for {years_at_location} years.",
                "Our {location_name} team averages {avg_tenure} years of experience.",
                "Locally hired, locally invested.",
            ],
            value_props=[
                "Local team members who live in the community they serve",
                "Named point of contact at your location",
                "Low staff turnover — familiar faces every visit",
                "Team bios and photos on your location's page",
            ],
            tone="conversational",
            best_for=["website", "social", "email"],
        ),
        MessageAngle(
            angle_name="convenience",
            description=(
                "Use when proximity, hours, or multi-location access is a "
                "competitive advantage — make it easy to find and visit."
            ),
            headline_templates=[
                "A {brand_name} Near You — {location_count} Locations",
                "Closer Than You Think: {brand_name} in {neighborhood}",
                "Open {hours_highlight} at {location_name}",
                "{brand_name} Covers {service_area} — Find Your Nearest Location",
                "Walk-Ins Welcome at {brand_name} {location_name}",
            ],
            subheadline_templates=[
                "Find the nearest location in seconds.",
                "{location_count} locations means one is always close.",
                "Extended hours at {location_name}: {extended_hours}.",
            ],
            value_props=[
                "{location_count} locations across {region}",
                "Online booking with real-time availability at each location",
                "Walk-in friendly — no appointment needed",
                "Consistent experience regardless of which location you visit",
            ],
            tone="conversational",
            best_for=["ad", "website", "landing_page"],
        ),
        MessageAngle(
            angle_name="local_reviews",
            description=(
                "Use location-specific review counts and ratings as social "
                "proof.  Hyper-local reviews outperform brand-level "
                "aggregates for conversion."
            ),
            headline_templates=[
                "{review_count}+ Reviews at {brand_name} {location_name}",
                "Rated {star_rating}/5 by Your {city} Neighbors",
                "See Why {location_name} Customers Love {brand_name}",
                '"{customer_quote}" — {customer_name}, {city}',
                "{location_name}'s Most-Reviewed {service_category}",
            ],
            subheadline_templates=[
                "Read {review_count}+ reviews from real {city} customers.",
                "Average {star_rating} stars at this location.",
                "Our {location_name} team has earned every one of those stars.",
            ],
            value_props=[
                "Location-specific reviews from verified local customers",
                "Average {star_rating} stars across {review_platform_count} platforms",
                "Every review gets a personal response from the location team",
                "Photo reviews and video testimonials from real neighbors",
            ],
            tone="conversational",
            best_for=["website", "ad", "social", "landing_page"],
        ),
        MessageAngle(
            angle_name="local_promotions",
            description=(
                "Use when running location-specific offers, community "
                "events, or market-specific campaigns that differ from "
                "the brand-wide promotion."
            ),
            headline_templates=[
                "{location_name} Exclusive: {offer_headline}",
                "Only at {brand_name} {location_name} — {offer_summary}",
                "{city} Special: {discount_pct}% Off {service_or_product}",
                "Community Event at {brand_name} {location_name}: {event_name}",
                "This Week in {location_name}: {promo_details}",
            ],
            subheadline_templates=[
                "This offer is only available at the {location_name} location.",
                "Supporting {community_cause} — {brand_name} {location_name}.",
                "Limited to {units_available} — {location_name} only.",
            ],
            value_props=[
                "Location-specific promotions tailored to local demand",
                "Community sponsorships and local event involvement",
                "Market-specific pricing that reflects local conditions",
                "First-to-know alerts for subscribers at each location",
            ],
            tone="conversational",
            best_for=["ad", "email", "social", "landing_page"],
        ),
    ]

    # ------------------------------------------------------------------
    # Objection Handlers (5)
    # ------------------------------------------------------------------

    objections = [
        ObjectionHandler(
            objection="I prefer a local independent provider",
            reframe=(
                "We ARE local — your {location_name} team lives in this "
                "community.  But they're backed by {brand_name}'s national "
                "resources, training, and guarantees that a solo operator "
                "can't match."
            ),
            response_templates=[
                (
                    "{team_lead_name} has been in {city} for "
                    "{years_at_location} years.  The difference is that "
                    "{team_lead_name} is backed by a brand-wide training "
                    "program and a satisfaction guarantee most independents "
                    "can't offer."
                ),
                (
                    "Our {location_name} team sponsors {community_event} "
                    "and hires locally.  We have the heart of an independent "
                    "with the reliability of a national brand."
                ),
                (
                    "If anything goes wrong, you're not relying on one "
                    "person — you have {brand_name}'s corporate support "
                    "and a {warranty_period} warranty behind every job."
                ),
            ],
            proof_type="testimonial",
        ),
        ObjectionHandler(
            objection="Chain businesses don't give personal attention",
            reframe=(
                "Fair concern.  Our model is built to prevent that — small "
                "local teams with brand-level resources, not a call center "
                "and a revolving door of staff."
            ),
            response_templates=[
                (
                    "You'll work with {team_lead_name} and the same crew "
                    "every time at {location_name}.  They know their "
                    "regulars by name."
                ),
                (
                    "Our average team tenure is {avg_tenure} years — low "
                    "turnover means you see familiar faces, not strangers."
                ),
                (
                    "Read the {location_name} reviews on Google — "
                    "'personal,' 'attentive,' and 'friendly' come up "
                    "more than anything else."
                ),
            ],
            proof_type="testimonial",
        ),
        ObjectionHandler(
            objection="I had a bad experience at another location",
            reframe=(
                "We're sorry that happened.  Each location is managed "
                "independently, and {location_name} takes your feedback "
                "seriously.  Let us show you the difference."
            ),
            response_templates=[
                (
                    "We've flagged that feedback to the other location's "
                    "management.  Your {location_name} team has a "
                    "{star_rating}-star rating from {review_count} reviews "
                    "— we hold ourselves to a higher bar."
                ),
                (
                    "We'd love to earn back your trust.  Visit "
                    "{location_name} and if the experience doesn't exceed "
                    "your expectations, {make_right_offer}."
                ),
                (
                    "Every location runs quality audits monthly.  "
                    "{location_name} scored {audit_score}/100 on the last "
                    "round — well above the network average."
                ),
            ],
            proof_type="guarantee",
        ),
        ObjectionHandler(
            objection="Your pricing isn't competitive locally",
            reframe=(
                "Our pricing reflects brand-level quality, insurance, "
                "training, and guarantees.  When you factor in what's "
                "included, the total value often beats the cheaper quote."
            ),
            response_templates=[
                (
                    "Our price includes {included_items} — make sure the "
                    "other quote covers the same scope.  Hidden add-ons "
                    "are common in this market."
                ),
                (
                    "We offer a price-match guarantee at {location_name} "
                    "for identical scope and quality.  Bring the other "
                    "quote and we'll review it together."
                ),
                (
                    "{brand_name}'s buying power means we use premium "
                    "materials at bulk pricing.  The {location_name} team "
                    "can walk you through exactly what's included."
                ),
            ],
            proof_type="comparison",
        ),
        ObjectionHandler(
            objection="I don't know which location to choose",
            reframe=(
                "All locations meet the same quality standards.  Let us "
                "help you find the most convenient one based on your "
                "location, schedule, and the service you need."
            ),
            response_templates=[
                (
                    "Enter your zip code at {brand_url}/locations and "
                    "we'll show you the closest {brand_name} with "
                    "real-time availability."
                ),
                (
                    "The {location_name} location in {neighborhood} is "
                    "{distance} from you and has {open_slots} openings "
                    "this week."
                ),
                (
                    "Every location shares the same training and standards.  "
                    "Pick the one that fits your schedule — here are the "
                    "three closest: {location_list}."
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
                "Spring kickoff — promote location-specific events, "
                "seasonal services, and community sponsorships."
            ),
            headline_templates=[
                "Spring Into {brand_name} {location_name} — {offer_headline}",
                "{location_name} Spring Special: {offer_summary}",
                "Your {city} {brand_name} Is Ready for Spring — Are You?",
            ],
            offer_suggestions=[
                "Location grand re-opening event with giveaways",
                "Spring service package at 15% off — book at any location",
                "Community cleanup day sponsored by {brand_name} {location_name}",
            ],
            urgency_element="before spring calendars fill up across all locations",
        ),
        SeasonalHook(
            season_or_event="summer",
            relevance_months=[6, 7, 8],
            hook_angle=(
                "Peak traffic season — extended hours, seasonal products, "
                "and family-friendly promotions."
            ),
            headline_templates=[
                "Summer Hours at {brand_name} {location_name}: {extended_hours}",
                "Beat the Heat at {brand_name} — Summer Specials at {location_name}",
                "Family Fun All Summer at {brand_name} {location_name}",
            ],
            offer_suggestions=[
                "Extended summer hours at select locations",
                "Kids-free or family bundle at participating locations",
                "Summer loyalty bonus: double points at all locations in July",
            ],
            urgency_element="while summer scheduling is still open",
        ),
        SeasonalHook(
            season_or_event="back_to_school",
            relevance_months=[8, 9],
            hook_angle=(
                "Back-to-routine season — families resetting schedules "
                "and looking for reliable local providers."
            ),
            headline_templates=[
                "Back to School, Back to {brand_name} {location_name}",
                "{location_name} Fall Schedule Is Live — Book Now",
                "New Season, Same Great Team at {brand_name} {location_name}",
            ],
            offer_suggestions=[
                "Teacher and first-responder discounts at all locations",
                "Fall maintenance packages with priority booking",
                "Referral bonus: bring a neighbor, both save $25",
            ],
            urgency_element="before fall appointment slots fill at your location",
        ),
        SeasonalHook(
            season_or_event="holiday",
            relevance_months=[11, 12],
            hook_angle=(
                "Holiday season — gift cards, community giving, and "
                "year-end promotions drive traffic to individual locations."
            ),
            headline_templates=[
                "Give the Gift of {brand_name} — Gift Cards at {location_name}",
                "Holiday Hours at {brand_name} {location_name}: {holiday_hours}",
                "Wrap Up the Year with {brand_name} {location_name}'s Holiday Special",
            ],
            offer_suggestions=[
                "Gift card promotion: buy $100, get $15 bonus",
                "Holiday toy drive or food bank partnership at each location",
                "Year-end clearance on select services at all locations",
            ],
            urgency_element="order gift cards by Dec 20 for guaranteed holiday delivery",
        ),
    ]

    # ------------------------------------------------------------------
    # CTA Library (10 — brand-level AND location-level)
    # ------------------------------------------------------------------

    ctas = [
        # Brand-level CTAs
        CTATemplate(
            cta_text="Find Your Nearest Location",
            cta_type="primary",
            funnel_stage="consideration",
            best_for=["website", "ad", "email"],
            supporting_text="{location_count}+ locations across {region}.",
        ),
        CTATemplate(
            cta_text="See All Locations",
            cta_type="secondary",
            funnel_stage="awareness",
            best_for=["website", "email"],
            supporting_text="Find the {brand_name} closest to you.",
        ),
        CTATemplate(
            cta_text="Join the {brand_name} Family",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "social"],
            supporting_text="Subscribe for exclusive offers from your local team.",
        ),
        # Location-level CTAs
        CTATemplate(
            cta_text="Book at {location_name}",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["landing_page", "website", "ad"],
            supporting_text="Online booking — instant confirmation.",
        ),
        CTATemplate(
            cta_text="Call {location_name}",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "landing_page", "website"],
            supporting_text="Speak directly with your local team.",
        ),
        CTATemplate(
            cta_text="Get Directions to {location_name}",
            cta_type="secondary",
            funnel_stage="decision",
            best_for=["ad", "website"],
            supporting_text="{distance} from you — {drive_time} drive.",
        ),
        CTATemplate(
            cta_text="Read {location_name} Reviews",
            cta_type="soft",
            funnel_stage="consideration",
            best_for=["website", "landing_page"],
            supporting_text="{review_count}+ reviews from your neighbors.",
        ),
        CTATemplate(
            cta_text="Meet the {location_name} Team",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "email"],
            supporting_text="Real people, not a call center.",
        ),
        CTATemplate(
            cta_text="Claim Your {location_name} Offer",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "email", "landing_page"],
            supporting_text="Exclusive to the {location_name} location.",
        ),
        CTATemplate(
            cta_text="Schedule a Tour at {location_name}",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "landing_page"],
            supporting_text="See the space and meet the team before you commit.",
        ),
    ]

    # ------------------------------------------------------------------
    # Tone Guidelines
    # ------------------------------------------------------------------

    tone_guidelines = {
        "website": "brand-consistent, warm, locally aware",
        "social": "community-focused, personable, location-proud",
        "ads": "benefit-focused, locally targeted, action-driven",
        "email": "personal, location-specific, value-driven",
        "reviews": "grateful, location-manager-voiced, professional",
    }

    # ------------------------------------------------------------------
    # Forbidden Phrases
    # ------------------------------------------------------------------

    forbidden_phrases = [
        "leverage",
        "utilize",
        "synergy",
        "innovative",
        "corporate headquarters",
        "franchise opportunity",
        "unit economics",
        "it's important to note",
        "in today's rapidly evolving",
        "world-class",
        "second to none",
        "best in class",
    ]

    # ------------------------------------------------------------------
    # Proof Priorities
    # ------------------------------------------------------------------

    proof_priorities = [
        "testimonial",
        "statistic",
        "case_study",
        "guarantee",
        "comparison",
    ]

    return MessagingFramework(
        archetype="multi_location",
        core_message=(
            "National brand quality with local team care — "
            "{brand_name} is in your neighborhood"
        ),
        message_angles=angles,
        objection_handlers=objections,
        seasonal_hooks=seasonal,
        cta_library=ctas,
        tone_guidelines=tone_guidelines,
        forbidden_phrases=forbidden_phrases,
        proof_priorities=proof_priorities,
    )

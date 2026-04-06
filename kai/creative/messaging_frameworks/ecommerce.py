"""Messaging framework for the **ecommerce** archetype.

Covers direct-to-consumer brands, online retailers, subscription box
companies, and marketplace sellers.  Revenue comes from product sales
through a website or storefront.  Marketing is oriented around product
quality, social proof, scarcity, lifestyle aspiration, and converting
browsers into buyers.

Usage::

    from kai.creative.messaging_frameworks.ecommerce import (
        build_ecommerce_messaging,
    )

    framework = build_ecommerce_messaging()
"""

from __future__ import annotations

from kai.creative.messaging_frameworks.base import (
    CTATemplate,
    MessageAngle,
    MessagingFramework,
    ObjectionHandler,
    SeasonalHook,
)


def build_ecommerce_messaging() -> MessagingFramework:
    """Return a fully-populated ``MessagingFramework`` for ecommerce
    businesses.

    Core message: *Products you'll love, from a brand you can trust.*
    """

    # ------------------------------------------------------------------
    # Message Angles (6)
    # ------------------------------------------------------------------

    angles = [
        MessageAngle(
            angle_name="product_quality",
            description=(
                "Use when the prospect cares about materials, craftsmanship, "
                "sourcing, or durability and needs reassurance that the "
                "product is worth the price."
            ),
            headline_templates=[
                "Made with {material} — Built to Last",
                "Why {product_count}+ Customers Swear by {product_name}",
                "{product_name}: {quality_descriptor} You Can Feel",
                "Crafted from {origin_material}, Not Factory Filler",
                "The {product_category} That Lasts {durability_claim}",
            ],
            subheadline_templates=[
                "Sourced from {origin}. Finished by hand.",
                "Every unit inspected before it ships.",
                "{return_window}-day returns if you're not obsessed.",
            ],
            value_props=[
                "Premium materials sourced directly from {origin}",
                "Rigorous quality inspection on every unit",
                "Built to outlast competitors by {durability_multiple}x",
                "Rated {star_rating}/5 across {review_count}+ reviews",
            ],
            tone="confident",
            best_for=["landing_page", "ad", "email", "website"],
        ),
        MessageAngle(
            angle_name="value",
            description=(
                "Use when competing on price/quality ratio or when the "
                "prospect is comparing alternatives and needs to see the "
                "total cost-of-ownership picture."
            ),
            headline_templates=[
                "{product_name} — Premium Quality, Honest Price",
                "Why Pay {competitor_price} When {product_name} Is ${price}?",
                "${price_per_use}/Use — The Smartest Buy in {category}",
                "Same Quality. Half the Markup.",
                "Skip the Brand Tax. Get {product_name}.",
            ],
            subheadline_templates=[
                "Compare us side by side — we publish our cost breakdown.",
                "No middlemen. No retail markup. Just a better product.",
                "Free shipping over ${free_ship_threshold}.",
            ],
            value_props=[
                "Direct-to-consumer pricing — no retail markup",
                "Transparent cost breakdown available on every product page",
                "Free shipping and hassle-free returns",
                "Subscription option saves {sub_discount_pct}% automatically",
            ],
            tone="conversational",
            best_for=["ad", "landing_page", "email"],
        ),
        MessageAngle(
            angle_name="uniqueness",
            description=(
                "Use when the product has a genuine differentiator — a "
                "patented feature, exclusive material, or design choice "
                "competitors cannot replicate."
            ),
            headline_templates=[
                "The Only {product_category} with {unique_feature}",
                "You Won't Find This Anywhere Else",
                "{unique_feature}: Why {product_name} Stands Alone",
                "Designed Different — {product_name}",
                "Patent-Pending {unique_feature}. Only from {brand_name}.",
            ],
            subheadline_templates=[
                "We spent {dev_time} developing what nobody else could.",
                "{unique_feature} changes how you {use_case}.",
                "Awarded {award_name} for {unique_feature}.",
            ],
            value_props=[
                "Proprietary {unique_feature} you can't get elsewhere",
                "Designed in-house by {team_description}",
                "Awarded {award_name} for innovation",
                "Protected by {patent_count} patents",
            ],
            tone="authoritative",
            best_for=["landing_page", "website", "ad"],
        ),
        MessageAngle(
            angle_name="social_proof",
            description=(
                "Use when you have strong review data, customer photos, "
                "influencer mentions, or bestseller status to create "
                "bandwagon confidence."
            ),
            headline_templates=[
                "{units_sold}+ Sold — See Why Everyone's Talking",
                "Rated {star_rating}/5 by {review_count}+ Real Customers",
                "As Seen in {media_outlet}",
                "#1 Bestseller in {category} — {review_count} Reviews",
                "Join {customer_count}+ Happy Customers",
            ],
            subheadline_templates=[
                '"{customer_quote}" — {customer_name}',
                "Trending on {platform} with {engagement_count}+ shares.",
                "Featured by {influencer_name} — watch the unboxing.",
            ],
            value_props=[
                "{review_count}+ verified five-star reviews",
                "Featured in {media_outlet_list}",
                "Customer photo gallery with {photo_count}+ real images",
                "Recommended by {influencer_count}+ creators",
            ],
            tone="conversational",
            best_for=["ad", "social", "landing_page", "email"],
        ),
        MessageAngle(
            angle_name="urgency_scarcity",
            description=(
                "Use during flash sales, limited drops, seasonal "
                "availability windows, or whenever genuine scarcity "
                "exists to motivate immediate action."
            ),
            headline_templates=[
                "Only {units_left} Left — Don't Miss Out",
                "{discount_pct}% Off Ends {deadline}",
                "Limited Drop: {product_name} — Once It's Gone, It's Gone",
                "Flash Sale: {hours_remaining} Hours Left",
                "Back in Stock — But Not for Long",
            ],
            subheadline_templates=[
                "Last restock sold out in {sellout_time}.",
                "{cart_count} people have this in their cart right now.",
                "This colorway won't be produced again.",
            ],
            value_props=[
                "Small-batch production — limited quantities per run",
                "Seasonal colorways and editions released quarterly",
                "Early-access pricing for email subscribers",
                "Sold out {sellout_count} times — set a restock alert",
            ],
            tone="urgent",
            best_for=["ad", "email", "landing_page"],
        ),
        MessageAngle(
            angle_name="lifestyle",
            description=(
                "Use when the product fits into an aspirational identity — "
                "show the customer the life they want, with the product "
                "naturally embedded in it."
            ),
            headline_templates=[
                "Designed for the Way You Actually Live",
                "Upgrade Your {routine} with {product_name}",
                "For People Who {lifestyle_descriptor}",
                "Live {adjective}. Choose {product_name}.",
                "The {product_category} for Your {aspirational_moment}",
            ],
            subheadline_templates=[
                "Built for {lifestyle_moment} — not the showroom.",
                "Join a community of {community_descriptor}.",
                "From {morning_routine} to {evening_routine}, it fits.",
            ],
            value_props=[
                "Designed around real daily routines, not lab conditions",
                "Community of {community_count}+ like-minded customers",
                "Pairs with {complementary_products} for a complete setup",
                "Aesthetic that elevates any {space_or_context}",
            ],
            tone="conversational",
            best_for=["social", "ad", "landing_page", "website"],
        ),
    ]

    # ------------------------------------------------------------------
    # Objection Handlers (5)
    # ------------------------------------------------------------------

    objections = [
        ObjectionHandler(
            objection="I can find it cheaper",
            reframe=(
                "A lower sticker price often hides inferior materials, "
                "shorter lifespan, and non-existent customer service.  "
                "Total value — not just price — is what matters."
            ),
            response_templates=[
                (
                    "We publish our materials and sourcing so you can "
                    "compare apples to apples.  The {competitor_name} "
                    "version uses {inferior_material} — ours uses "
                    "{premium_material}, which lasts {durability_multiple}x "
                    "longer."
                ),
                (
                    "At ${price_per_use} per use, {product_name} is actually "
                    "the cheapest option over {timeframe}.  Plus you get "
                    "free shipping and a {warranty_period} warranty."
                ),
                (
                    "Our return rate is {return_rate}% — industry average "
                    "is {industry_avg_return}%.  Fewer returns means "
                    "customers are genuinely satisfied."
                ),
            ],
            proof_type="comparison",
        ),
        ObjectionHandler(
            objection="I'm not sure about the quality",
            reframe=(
                "Healthy skepticism is smart.  Here's how we prove it: "
                "transparent materials, detailed specs, and a return policy "
                "that puts all the risk on us."
            ),
            response_templates=[
                (
                    "Every {product_name} is made from {material_detail} and "
                    "passes a {inspection_step_count}-point inspection.  "
                    "See our factory walkthrough video: {video_url}."
                ),
                (
                    "We have {review_count}+ verified reviews averaging "
                    "{star_rating}/5.  Filter by '{quality_keyword}' and "
                    "read what real buyers say."
                ),
                (
                    "Try it risk-free for {return_window} days.  If it "
                    "doesn't meet your standard, return it — we pay the "
                    "shipping both ways."
                ),
            ],
            proof_type="testimonial",
        ),
        ObjectionHandler(
            objection="I need to see it first",
            reframe=(
                "Totally fair.  We can't put the product in your hands "
                "before purchase, but we can remove every bit of risk "
                "and give you the next best thing."
            ),
            response_templates=[
                (
                    "Our {return_window}-day return policy is dead simple: "
                    "don't love it, send it back for a full refund.  We "
                    "even cover return shipping."
                ),
                (
                    "Check out {photo_count}+ customer photos — real people, "
                    "real lighting, no studio tricks.  Plus our 360-degree "
                    "product view shows every angle."
                ),
                (
                    "Watch the {video_count} unboxing videos from customers "
                    "on {platform}.  First impressions, live and unscripted."
                ),
            ],
            proof_type="case_study",
        ),
        ObjectionHandler(
            objection="I don't need it right now",
            reframe=(
                "No pressure — but the current offer or stock level may "
                "not wait.  Here's what you risk by waiting."
            ),
            response_templates=[
                (
                    "This batch is limited to {units_available} units and "
                    "our last run sold out in {sellout_time}.  We can't "
                    "guarantee availability next week."
                ),
                (
                    "The {discount_pct}% discount expires {deadline}.  "
                    "After that, {product_name} goes back to full price "
                    "— ${full_price}."
                ),
                (
                    "Add it to your wishlist and we'll remind you — but "
                    "fair warning, {product_name} is our fastest seller "
                    "this quarter."
                ),
            ],
            proof_type="statistic",
        ),
        ObjectionHandler(
            objection="I've never heard of this brand",
            reframe=(
                "New to you doesn't mean new.  Here's the quick story "
                "and the proof points that let you buy with confidence."
            ),
            response_templates=[
                (
                    "{brand_name} launched in {founding_year} with one "
                    "mission: {brand_mission}.  Since then, {units_sold}+ "
                    "customers have joined us."
                ),
                (
                    "We've been featured in {media_outlet_list}.  Our "
                    "founders {founder_credentials}.  And we have "
                    "{review_count}+ verified reviews to back it up."
                ),
                (
                    "Follow us at @{social_handle} — {follower_count}+ "
                    "followers and a feed full of real customer stories."
                ),
            ],
            proof_type="testimonial",
        ),
    ]

    # ------------------------------------------------------------------
    # Seasonal Hooks (5)
    # ------------------------------------------------------------------

    seasonal = [
        SeasonalHook(
            season_or_event="new_year",
            relevance_months=[1, 2],
            hook_angle=(
                "New-year reset energy — people are buying to upgrade "
                "routines, refresh wardrobes, and start fresh."
            ),
            headline_templates=[
                "New Year, New {product_category} — Start Fresh",
                "Upgrade Your {routine} in {year}",
                "Resolution-Ready: {product_name} at {discount_pct}% Off",
            ],
            offer_suggestions=[
                "New Year bundle: buy 2, save 20%",
                "Free gift with first purchase of the year",
                "Resolution guarantee — full refund if you don't see results in 30 days",
            ],
            urgency_element="while New Year pricing lasts",
        ),
        SeasonalHook(
            season_or_event="spring",
            relevance_months=[3, 4, 5],
            hook_angle=(
                "Spring refresh — lighter products, seasonal colors, "
                "and the urge to declutter and upgrade."
            ),
            headline_templates=[
                "Spring Refresh: New Arrivals in {category}",
                "Out with the Old — {product_name} Is Here",
                "Fresh Picks for {season} — Shop the Drop",
            ],
            offer_suggestions=[
                "Spring sale: 15% off sitewide",
                "Trade-in program — send back your old one for a discount",
                "Free express shipping on spring collection orders",
            ],
            urgency_element="before the spring collection sells through",
        ),
        SeasonalHook(
            season_or_event="back_to_school",
            relevance_months=[7, 8, 9],
            hook_angle=(
                "Back-to-school spending surge — parents and students "
                "are stocking up and looking for deals."
            ),
            headline_templates=[
                "Back-to-School Essentials — {product_category}",
                "Gear Up for {school_season}: {product_name}",
                "Student-Ready {product_category} Starting at ${price}",
            ],
            offer_suggestions=[
                "Student discount: 20% off with .edu email",
                "Back-to-school bundle with free accessory",
                "Buy now, pay later with {financing_partner}",
            ],
            urgency_element="before school starts and stock runs low",
        ),
        SeasonalHook(
            season_or_event="black_friday",
            relevance_months=[11],
            hook_angle=(
                "Biggest sale of the year — heavy discounts, doorbuster "
                "deals, and extreme urgency."
            ),
            headline_templates=[
                "Black Friday: {discount_pct}% Off Everything",
                "Our Biggest Sale Ever — {product_name} at ${sale_price}",
                "Doorbuster: {product_name} — {units_available} Units Only",
            ],
            offer_suggestions=[
                "Sitewide discount with tiered savings (spend more, save more)",
                "Mystery box with guaranteed value above purchase price",
                "Early access for email subscribers 24 hours before public sale",
            ],
            urgency_element="sale ends Cyber Monday at midnight",
        ),
        SeasonalHook(
            season_or_event="holiday_gifting",
            relevance_months=[11, 12],
            hook_angle=(
                "Gift-giving season — position products as the perfect "
                "present with gift-ready packaging and curated bundles."
            ),
            headline_templates=[
                "The Gift They Actually Want — {product_name}",
                "Holiday Gift Guide: Best {category} Under ${price}",
                "Gift-Ready {product_name} with Free Wrapping",
            ],
            offer_suggestions=[
                "Free gift wrapping on all orders",
                "Holiday bundle: product + accessory at 25% off",
                "Guaranteed delivery by Dec 23 with order before {cutoff_date}",
            ],
            urgency_element="order by {cutoff_date} for guaranteed holiday delivery",
        ),
    ]

    # ------------------------------------------------------------------
    # CTA Library (8)
    # ------------------------------------------------------------------

    ctas = [
        CTATemplate(
            cta_text="Add to Cart",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["landing_page", "website"],
            supporting_text="Free shipping over ${free_ship_threshold}.",
        ),
        CTATemplate(
            cta_text="Shop Now",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "email", "social"],
            supporting_text="{discount_pct}% off — limited time.",
        ),
        CTATemplate(
            cta_text="Claim Your Discount",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["ad", "email", "landing_page"],
            supporting_text="Use code {promo_code} at checkout.",
        ),
        CTATemplate(
            cta_text="See What's New",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["email", "social", "website"],
            supporting_text="Fresh arrivals added this week.",
        ),
        CTATemplate(
            cta_text="Read the Reviews",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "email", "landing_page"],
            supporting_text="{review_count}+ verified buyer reviews.",
        ),
        CTATemplate(
            cta_text="Get Notified When Back in Stock",
            cta_type="secondary",
            funnel_stage="consideration",
            best_for=["website", "landing_page"],
            supporting_text="Be first in line — drops sell fast.",
        ),
        CTATemplate(
            cta_text="Take the Quiz",
            cta_type="soft",
            funnel_stage="awareness",
            best_for=["website", "ad", "social"],
            supporting_text="Find your perfect {product_category} in 60 seconds.",
        ),
        CTATemplate(
            cta_text="Subscribe & Save {sub_discount_pct}%",
            cta_type="primary",
            funnel_stage="decision",
            best_for=["website", "landing_page", "email"],
            supporting_text="Cancel anytime. Free shipping on every delivery.",
        ),
    ]

    # ------------------------------------------------------------------
    # Tone Guidelines
    # ------------------------------------------------------------------

    tone_guidelines = {
        "website": "polished, aspirational, benefit-driven",
        "social": "relatable, visual-first, community-oriented",
        "ads": "concise, benefit-led, urgency when appropriate",
        "email": "personal, exclusive, value-focused",
        "reviews": "appreciative, responsive, customer-centric",
    }

    # ------------------------------------------------------------------
    # Forbidden Phrases
    # ------------------------------------------------------------------

    forbidden_phrases = [
        "leverage",
        "utilize",
        "synergy",
        "innovative",
        "best in class",
        "world-class service",
        "game-changer",
        "disruptive",
        "it's important to note",
        "in today's rapidly evolving",
        "without further ado",
        "this comprehensive guide",
    ]

    # ------------------------------------------------------------------
    # Proof Priorities
    # ------------------------------------------------------------------

    proof_priorities = [
        "testimonial",
        "comparison",
        "statistic",
        "case_study",
        "guarantee",
    ]

    return MessagingFramework(
        archetype="ecommerce",
        core_message="Products you'll love, from a brand you can trust",
        message_angles=angles,
        objection_handlers=objections,
        seasonal_hooks=seasonal,
        cta_library=ctas,
        tone_guidelines=tone_guidelines,
        forbidden_phrases=forbidden_phrases,
        proof_priorities=proof_priorities,
    )

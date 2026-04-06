"""Ecommerce / DTC Brand archetype for the Kai Marketing OS.

Defines the marketing playbook for businesses selling physical or digital
products directly to consumers online.  Revenue comes from product sales
through owned storefronts (Shopify, WooCommerce, etc.) and/or marketplaces
(Amazon, Etsy).  Marketing is oriented around acquisition, conversion,
retention, and maximizing customer lifetime value.

Usage::

    from kai.archetypes.ecommerce import ECOMMERCE_ARCHETYPE

    archetype = ECOMMERCE_ARCHETYPE
    print(archetype.id)           # "ecommerce"
    print(archetype.kpi_schema)   # dict of 14 KPIDefinitions
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
    "revenue": KPIDefinition(
        id="revenue",
        name="Revenue",
        description="Total revenue from product sales across all channels",
        unit="dollars",
        direction="higher_is_better",
        priority="primary",
    ),
    "aov": KPIDefinition(
        id="aov",
        name="Average Order Value",
        description=(
            "Average dollar amount per order, a primary lever for "
            "revenue growth without increasing traffic"
        ),
        unit="dollars",
        direction="higher_is_better",
        benchmark_range="$40-120",
        priority="primary",
    ),
    "conversion_rate": KPIDefinition(
        id="conversion_rate",
        name="Conversion Rate",
        description=(
            "Percentage of site visitors who complete a purchase"
        ),
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="1.5-4%",
        priority="primary",
    ),
    "cart_abandonment_rate": KPIDefinition(
        id="cart_abandonment_rate",
        name="Cart Abandonment Rate",
        description=(
            "Percentage of shoppers who add items to cart but do not "
            "complete checkout"
        ),
        unit="percentage",
        direction="lower_is_better",
        benchmark_range="60-75%",
        priority="primary",
    ),
    "customer_ltv": KPIDefinition(
        id="customer_ltv",
        name="Customer Lifetime Value",
        description=(
            "Total revenue a customer generates over their entire "
            "relationship with the brand"
        ),
        unit="dollars",
        direction="higher_is_better",
        benchmark_range="2-5x AOV",
        priority="primary",
    ),
    "repeat_purchase_rate": KPIDefinition(
        id="repeat_purchase_rate",
        name="Repeat Purchase Rate",
        description=(
            "Percentage of customers who make more than one purchase"
        ),
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="20-40%",
        priority="primary",
    ),
    "roas": KPIDefinition(
        id="roas",
        name="Return on Ad Spend",
        description=(
            "Revenue generated per dollar spent on advertising"
        ),
        unit="ratio",
        direction="higher_is_better",
        benchmark_range="2-5x",
        priority="primary",
    ),
    "cac": KPIDefinition(
        id="cac",
        name="Customer Acquisition Cost",
        description=(
            "Average marketing cost to acquire one new customer"
        ),
        unit="dollars",
        direction="lower_is_better",
        benchmark_range="20-30% of first order",
        priority="primary",
    ),
    "email_revenue_pct": KPIDefinition(
        id="email_revenue_pct",
        name="Email Revenue %",
        description=(
            "Percentage of total revenue attributable to email marketing"
        ),
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="20-40%",
        priority="secondary",
    ),
    "email_list_growth_rate": KPIDefinition(
        id="email_list_growth_rate",
        name="Email List Growth Rate",
        description=(
            "Monthly percentage growth of the email subscriber list"
        ),
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="3-10%",
        priority="secondary",
    ),
    "product_page_conversion_rate": KPIDefinition(
        id="product_page_conversion_rate",
        name="Product Page Conversion Rate",
        description=(
            "Percentage of product detail page visitors who add to cart "
            "or purchase"
        ),
        unit="percentage",
        direction="higher_is_better",
        benchmark_range="2-6%",
        priority="secondary",
    ),
    "review_count_per_product": KPIDefinition(
        id="review_count_per_product",
        name="Review Count per Product",
        description=(
            "Average number of customer reviews per product listing"
        ),
        unit="count",
        direction="higher_is_better",
        benchmark_range="10-100",
        priority="secondary",
    ),
    "time_between_purchases": KPIDefinition(
        id="time_between_purchases",
        name="Time Between Purchases",
        description=(
            "Average number of days between a customer's repeat orders"
        ),
        unit="days",
        direction="lower_is_better",
        priority="secondary",
    ),
    "new_vs_returning_ratio": KPIDefinition(
        id="new_vs_returning_ratio",
        name="New vs Returning Ratio",
        description=(
            "Ratio of new customers to returning customers; context-"
            "dependent -- too skewed in either direction signals a problem"
        ),
        unit="ratio",
        direction="higher_is_better",
        benchmark_range="60/40 to 40/60",
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
            "The store itself -- product pages, checkout, and homepage "
            "are the core conversion surface.  Every optimization here "
            "multiplies the return on all traffic sources."
        ),
    ),
    ChannelRecommendation(
        channel="meta_ads",
        priority=1,
        stage_relevance=["early-pmf", "growth", "scale", "mature"],
        budget_minimum=1000.0,
        rationale=(
            "Primary acquisition channel for DTC -- prospecting and "
            "retargeting.  Meta's targeting and creative testing "
            "capabilities make it the default first paid channel for "
            "ecommerce."
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="email",
        priority=1,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Lifecycle revenue engine -- welcome, abandon cart, "
            "post-purchase, win-back.  Email should drive 20-40% of "
            "total revenue for a healthy ecommerce business."
        ),
    ),
    ChannelRecommendation(
        channel="google_ads",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=500.0,
        rationale=(
            "Shopping ads and search ads for high-intent product queries.  "
            "Captures demand from shoppers actively looking for specific "
            "products or product categories."
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="seo",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Organic product discovery -- category pages, blog content, "
            "product schema.  Long-term traffic source that reduces "
            "dependence on paid acquisition."
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="instagram",
        priority=2,
        stage_relevance=["pre-launch", "early-pmf", "growth", "scale", "mature"],
        rationale=(
            "Visual product showcase, UGC, and shoppable posts.  "
            "Instagram is the primary organic social channel for most "
            "ecommerce brands."
        ),
    ),
    ChannelRecommendation(
        channel="tiktok",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=500.0,
        rationale=(
            "Short-form video for product discovery and viral potential.  "
            "TikTok can drive massive top-of-funnel awareness at low CPMs."
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="tiktok_shop",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "In-app commerce for TikTok-native shopping.  Reduces "
            "friction by allowing purchase without leaving TikTok."
        ),
        prerequisites=["tiktok"],
    ),
    ChannelRecommendation(
        channel="sms",
        priority=2,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Flash sales, back-in-stock alerts, cart recovery complement "
            "to email.  SMS has higher open rates than email and works "
            "well for time-sensitive promotions."
        ),
        prerequisites=["email"],
    ),
    ChannelRecommendation(
        channel="youtube",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Product reviews, tutorials, unboxing, long-form brand "
            "building.  YouTube content has a long shelf life and "
            "supports SEO through video search results."
        ),
    ),
    ChannelRecommendation(
        channel="pinterest",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        budget_minimum=300.0,
        rationale=(
            "Visual discovery for home, fashion, beauty, food products.  "
            "Pinterest users have high purchase intent and pins drive "
            "traffic for months after posting."
        ),
        prerequisites=["website"],
    ),
    ChannelRecommendation(
        channel="amazon",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "Marketplace presence -- Amazon Ads + organic optimization.  "
            "P1 if the business is marketplace-first; P3 if DTC-first "
            "using Amazon as a supplementary channel."
        ),
    ),
    ChannelRecommendation(
        channel="influencer",
        priority=3,
        stage_relevance=["growth", "scale", "mature"],
        rationale=(
            "UGC generation, social proof, and audience access.  "
            "Influencer-produced content often outperforms studio "
            "creative in paid ads."
        ),
    ),
]

# ============================================================================
# Action families
# ============================================================================

_ACTION_FAMILIES = [
    ActionFamily(
        id="pdp_optimization",
        name="Product Detail Page Optimization",
        description=(
            "Optimize product detail pages to convert browsers into "
            "buyers.  PDP conversion rate is the multiplier for all "
            "traffic -- optimize before increasing ad spend."
        ),
        actions=[
            "hero_image_quality",
            "value_prop_clarity",
            "price_display",
            "add_to_cart_prominence",
            "social_proof_on_pdp",
            "cross_sell_upsell",
            "product_schema_markup",
            "size_guide_faq",
        ],
        priority="high",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="checkout_optimization",
        name="Checkout Optimization",
        description=(
            "Reduce checkout friction to maximize the percentage of "
            "carts that convert to orders.  Every unnecessary step or "
            "surprise cost increases abandonment."
        ),
        actions=[
            "guest_checkout_enable",
            "payment_options_expansion",
            "shipping_transparency",
            "trust_badges",
            "checkout_step_reduction",
            "mobile_checkout_ux",
        ],
        priority="high",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="cart_recovery",
        name="Cart Recovery",
        description=(
            "Recover abandoned carts through automated multi-channel "
            "sequences.  Cart abandonment recovery is the highest-ROI "
            "automation for ecommerce."
        ),
        actions=[
            "abandoned_cart_email_1h",
            "abandoned_cart_email_24h",
            "abandoned_cart_email_72h",
            "browse_abandonment_email",
            "sms_cart_reminder",
            "exit_intent_popup",
        ],
        priority="high",
        typical_timeline="1-2 weeks",
    ),
    ActionFamily(
        id="email_lifecycle",
        name="Email Lifecycle",
        description=(
            "Automated email sequences covering the full customer "
            "lifecycle from first visit to loyal repeat buyer.  A "
            "complete email system should drive 20-40% of revenue."
        ),
        actions=[
            "welcome_series",
            "post_purchase_sequence",
            "review_request_email",
            "win_back_sequence",
            "vip_segment",
            "birthday_anniversary",
            "back_in_stock_alerts",
            "price_drop_alerts",
        ],
        priority="high",
        typical_timeline="2-4 weeks",
    ),
    ActionFamily(
        id="paid_acquisition",
        name="Paid Acquisition",
        description=(
            "Paid traffic acquisition across Meta, Google, and other "
            "channels with a focus on ROAS and creative testing."
        ),
        actions=[
            "meta_prospecting_campaigns",
            "meta_retargeting_campaigns",
            "google_shopping_campaigns",
            "google_search_brand",
            "google_search_category",
            "lookalike_audiences",
            "creative_testing_cadence",
        ],
        priority="high",
        typical_timeline="1-2 weeks setup, ongoing optimization",
    ),
    ActionFamily(
        id="social_commerce",
        name="Social Commerce",
        description=(
            "Enable purchasing directly through social platforms and "
            "build a social-first shopping experience."
        ),
        actions=[
            "instagram_shop_setup",
            "tiktok_shop_setup",
            "shoppable_posts",
            "live_shopping_events",
            "ugc_collection_system",
        ],
        priority="medium",
        typical_timeline="2-4 weeks",
    ),
    ActionFamily(
        id="retention_programs",
        name="Retention Programs",
        description=(
            "Programs designed to increase repeat purchase rate and "
            "customer lifetime value.  Retention is typically 5-7x "
            "cheaper than acquisition."
        ),
        actions=[
            "loyalty_program",
            "subscription_option",
            "referral_program",
            "vip_tiers",
            "reorder_reminders",
            "replenishment_emails",
        ],
        priority="medium",
        typical_timeline="2-4 weeks setup, ongoing management",
    ),
    ActionFamily(
        id="ugc_collection",
        name="UGC Collection",
        description=(
            "Systematic collection and deployment of user-generated "
            "content.  UGC consistently outperforms studio creative in "
            "paid ads and builds authentic social proof."
        ),
        actions=[
            "post_purchase_photo_request",
            "review_incentive_program",
            "hashtag_campaign",
            "influencer_seeding",
            "customer_spotlight_series",
        ],
        priority="medium",
        typical_timeline="ongoing",
    ),
]

# ============================================================================
# Creative formats
# ============================================================================

_CREATIVE_FORMATS = [
    CreativeFormat(
        id="product_shots",
        name="Product Shots",
        description=(
            "Clean product photography on white or lifestyle backgrounds.  "
            "The foundation of all ecommerce marketing -- high-quality "
            "product images directly impact conversion rate."
        ),
        platforms=["website", "meta_ads", "google_ads", "instagram", "pinterest"],
        requirements=[
            "professional product photography",
            "white background shots",
            "lifestyle context shots",
            "multiple angles",
        ],
    ),
    CreativeFormat(
        id="lifestyle_imagery",
        name="Lifestyle Imagery",
        description=(
            "Products shown in real-life usage contexts.  Helps "
            "customers visualize ownership and drives higher engagement "
            "than product-only shots."
        ),
        platforms=["instagram", "meta_ads", "pinterest", "website"],
        requirements=[
            "models or styled scenes",
            "product in-use photography",
            "brand-consistent styling",
        ],
    ),
    CreativeFormat(
        id="ugc_reposts",
        name="UGC Reposts",
        description=(
            "Customer photos and videos repurposed for marketing.  "
            "Authentic UGC consistently outperforms polished creative "
            "in conversion metrics."
        ),
        platforms=["instagram", "tiktok", "meta_ads", "website"],
        requirements=[
            "customer content collection system",
            "usage rights/permissions",
            "light editing and branding",
        ],
    ),
    CreativeFormat(
        id="sale_graphics",
        name="Sale Graphics",
        description=(
            "Promotional graphics for flash sales and seasonal events.  "
            "Clear discount messaging with urgency signals."
        ),
        platforms=["email", "meta_ads", "instagram", "website"],
        requirements=[
            "sale pricing and terms",
            "brand-consistent design templates",
            "start/end dates",
        ],
    ),
    CreativeFormat(
        id="unboxing_scripts",
        name="Unboxing Scripts",
        description=(
            "Scripted unboxing experience videos.  Unboxing content "
            "drives product discovery and builds anticipation for "
            "first-time buyers."
        ),
        platforms=["tiktok", "youtube", "instagram"],
        requirements=[
            "product samples",
            "video recording setup",
            "script or shot list",
        ],
    ),
    CreativeFormat(
        id="comparison_charts",
        name="Comparison Charts",
        description=(
            "Product comparison tables vs competitors or product tiers.  "
            "Reduces decision paralysis and positions the product "
            "favorably against alternatives."
        ),
        platforms=["website", "email", "landing_page"],
        requirements=[
            "competitor or tier feature data",
            "design template",
            "substantiated claims",
        ],
    ),
    CreativeFormat(
        id="size_fit_guides",
        name="Size & Fit Guides",
        description=(
            "Visual sizing and fit guides reducing returns.  Clear "
            "sizing information directly reduces return rates and "
            "improves customer satisfaction."
        ),
        platforms=["website", "email"],
        requirements=[
            "accurate measurement data",
            "visual reference graphics",
            "model size reference points",
        ],
    ),
    CreativeFormat(
        id="behind_the_scenes",
        name="Behind the Scenes",
        description=(
            "Manufacturing, sourcing, or team content building brand "
            "story.  Transparency content builds brand affinity and "
            "differentiates from commoditized competitors."
        ),
        platforms=["tiktok", "instagram", "youtube"],
        requirements=[
            "access to production or operations",
            "video recording",
            "brand narrative framework",
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
        max_monthly=5000.0,
        allocation_notes=(
            "Focus 60% on Meta Ads for initial traction. 20% on email "
            "setup (welcome + cart recovery). 10% on organic social "
            "content. 10% on Google Shopping."
        ),
    ),
    "established": BudgetRange(
        stage="established",
        min_monthly=5000.0,
        max_monthly=20000.0,
        allocation_notes=(
            "Split 40% paid acquisition (Meta + Google), 20% email/SMS, "
            "15% SEO/content, 15% social/influencer, 10% retention "
            "programs."
        ),
    ),
    "scaling": BudgetRange(
        stage="scaling",
        min_monthly=20000.0,
        max_monthly=100000.0,
        allocation_notes=(
            "Diversify: Meta 25%, Google 20%, email/SMS 15%, TikTok 10%, "
            "influencer 10%, SEO 10%, retention 10%. Test new channels "
            "with 5% of budget."
        ),
    ),
}

# ============================================================================
# Archetype definition
# ============================================================================

ECOMMERCE_ARCHETYPE = ArchetypeDefinition(
    id="ecommerce",
    name="Ecommerce / DTC Brand",
    description=(
        "Businesses selling physical or digital products directly to "
        "consumers online. Revenue comes from product sales through owned "
        "storefronts (Shopify, WooCommerce, etc.) and/or marketplaces "
        "(Amazon, Etsy). Marketing is oriented around acquisition, "
        "conversion, retention, and maximizing customer lifetime value."
    ),
    # ---- Audit categories in priority order ----
    audit_categories=[
        "product_pages",
        "checkout_funnel",
        "cart_abandonment",
        "email_lifecycle",
        "paid_acquisition",
        "social_commerce",
        "retention_repeat",
        "review_ugc",
        "seo_product",
    ],
    # ---- Priority defaults (what to fix first) ----
    priority_defaults=[
        (
            "Product pages have clear value prop, pricing, and add-to-cart "
            "CTA above the fold"
        ),
        "Checkout is 3 steps or fewer with guest checkout available",
        (
            "Cart abandonment email sequence fires within 1 hour of "
            "abandonment"
        ),
        (
            "Post-purchase email sequence exists (confirmation, shipping, "
            "review request)"
        ),
        (
            "At least one paid acquisition channel is profitable "
            "(ROAS > 2x)"
        ),
        "Welcome email series converts new subscribers at 5%+ rate",
        (
            "Product reviews are visible on PDPs with at least 10 reviews "
            "per hero product"
        ),
        (
            "Retargeting is running on Meta and/or Google for cart "
            "abandoners"
        ),
        "Email drives at least 20% of total revenue",
        "Customer repeat purchase rate exceeds 20%",
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
            "Product claims must be substantiated -- no miracle claims, "
            "unproven health benefits, or misleading before/after"
        ),
        (
            "Pricing must comply with FTC guidelines -- no fake markdowns, "
            "fake urgency timers, or deceptive MSRP"
        ),
        (
            "Testimonials and reviews must be genuine -- no purchased or "
            "fabricated reviews"
        ),
        (
            "Subscribe-and-save pricing must clearly disclose recurring "
            "charges and cancellation terms"
        ),
        (
            "Health/beauty/supplement products have additional FDA and FTC "
            "restrictions"
        ),
        "Children's products have COPPA and CPSIA requirements",
        (
            "Email/SMS marketing must comply with CAN-SPAM and TCPA "
            "respectively"
        ),
        "International shipping claims must be accurate",
    ],
    # ---- Creative formats ----
    creative_formats=_CREATIVE_FORMATS,
    # ---- Budget heuristics ----
    budget_heuristics=_BUDGET_HEURISTICS,
    # ---- Minimum viable channels ----
    minimum_viable_channels=["website", "meta_ads", "email", "google_ads"],
    # ---- Archetype-specific rules ----
    archetype_specific_rules=[
        (
            "ROAS is the primary metric for paid acquisition -- break even "
            "at 2x, target 3-5x"
        ),
        (
            "Email should drive 20-40% of total revenue; if below 20%, "
            "lifecycle email is underinvested"
        ),
        (
            "Cart abandonment recovery is the highest-ROI automation -- "
            "implement before scaling paid"
        ),
        (
            "Product page conversion rate is the multiplier for all "
            "traffic -- optimize PDPs before increasing ad spend"
        ),
        (
            "UGC consistently outperforms studio creative in Meta Ads -- "
            "invest in UGC collection systems"
        ),
        (
            "Customer LTV should be calculated and used to set acquisition "
            "cost targets"
        ),
        (
            "Seasonal planning should start 6-8 weeks before peak periods "
            "(Black Friday, holidays, etc.)"
        ),
        (
            "Review count on PDPs directly correlates with conversion "
            "rate -- automate review requests"
        ),
    ],
)

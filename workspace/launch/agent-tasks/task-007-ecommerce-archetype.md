# Task 007: Define ecommerce archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Large

## Context

Ecommerce businesses (DTC brands, online stores, Shopify merchants, Amazon sellers) have fundamentally different marketing needs from local service businesses. Their conversion happens online, their funnel is measurable end-to-end, and their marketing is heavily oriented around product pages, cart recovery, paid acquisition at scale, and customer lifetime value. This archetype defines the audit categories, KPIs, channel mix, and action playbook for any business selling products online.

## Scope

Build `kai/archetypes/ecommerce.py` with the full ecommerce archetype definition, using the base classes defined in `kai/archetypes/base.py` (Task 006).

## Detailed Requirements

### File: `kai/archetypes/ecommerce.py`

**Constant: `ECOMMERCE_ARCHETYPE`** — an instance of ArchetypeDefinition.

**id:** `"ecommerce"`
**name:** `"Ecommerce / DTC Brand"`
**description:** "Businesses selling physical or digital products directly to consumers online. Revenue comes from product sales through owned storefronts (Shopify, WooCommerce, etc.) and/or marketplaces (Amazon, Etsy). Marketing is oriented around acquisition, conversion, retention, and maximizing customer lifetime value."

**audit_categories** (in priority order):
1. `"product_pages"` — Are PDPs converting browsers to buyers?
2. `"checkout_funnel"` — Is the checkout flow optimized and low-friction?
3. `"cart_abandonment"` — Is there a recovery system for abandoned carts?
4. `"email_lifecycle"` — Are lifecycle emails driving revenue?
5. `"paid_acquisition"` — Is paid traffic profitable at scale?
6. `"social_commerce"` — Is social driving direct sales?
7. `"retention_repeat"` — Are customers coming back?
8. `"review_ugc"` — Is user-generated content being leveraged?
9. `"seo_product"` — Are products discoverable in organic search?

**priority_defaults** (what to fix first):
1. "Product pages have clear value prop, pricing, and add-to-cart CTA above the fold"
2. "Checkout is 3 steps or fewer with guest checkout available"
3. "Cart abandonment email sequence fires within 1 hour of abandonment"
4. "Post-purchase email sequence exists (confirmation, shipping, review request)"
5. "At least one paid acquisition channel is profitable (ROAS > 2x)"
6. "Welcome email series converts new subscribers at 5%+ rate"
7. "Product reviews are visible on PDPs with at least 10 reviews per hero product"
8. "Retargeting is running on Meta and/or Google for cart abandoners"
9. "Email drives at least 20% of total revenue"
10. "Customer repeat purchase rate exceeds 20%"

**kpi_schema:**
- `revenue`: dollars, higher_is_better, primary, benchmark varies by stage
- `aov`: dollars (Average Order Value), higher_is_better, primary, benchmark "$40-120"
- `conversion_rate`: percentage, higher_is_better, primary, benchmark "1.5-4%"
- `cart_abandonment_rate`: percentage, lower_is_better, primary, benchmark "60-75%"
- `customer_ltv`: dollars (Lifetime Value), higher_is_better, primary, benchmark "2-5x AOV"
- `repeat_purchase_rate`: percentage, higher_is_better, primary, benchmark "20-40%"
- `roas`: ratio (Return on Ad Spend), higher_is_better, primary, benchmark "2-5x"
- `cac`: dollars (Customer Acquisition Cost), lower_is_better, primary, benchmark "20-30% of first order"
- `email_revenue_pct`: percentage of total revenue from email, higher_is_better, secondary, benchmark "20-40%"
- `email_list_growth_rate`: percentage monthly, higher_is_better, secondary, benchmark "3-10%"
- `product_page_conversion_rate`: percentage, higher_is_better, secondary, benchmark "2-6%"
- `review_count_per_product`: count, higher_is_better, secondary, benchmark "10-100"
- `time_between_purchases`: days, lower_is_better, secondary, benchmark varies by product type
- `new_vs_returning_ratio`: ratio, context-dependent, tertiary, benchmark "60/40 to 40/60"

**channel_mix:**
1. `website` — P1, all stages, "The store itself — product pages, checkout, and homepage are the core conversion surface"
2. `meta_ads` — P1, early-pmf+, min $1000/mo, "Primary acquisition channel for DTC — prospecting and retargeting"
3. `email` — P1, all stages, "Lifecycle revenue engine — welcome, abandon cart, post-purchase, win-back"
4. `google_ads` — P2, growth+, min $500/mo, "Shopping ads and search ads for high-intent product queries"
5. `seo` — P2, growth+, "Organic product discovery — category pages, blog content, product schema"
6. `instagram` — P2, all stages, "Visual product showcase, UGC, and shoppable posts"
7. `tiktok` — P2, growth+, min $500/mo, "Short-form video for product discovery and viral potential"
8. `tiktok_shop` — P3, growth+, "In-app commerce for TikTok-native shopping"
9. `sms` — P2, growth+, "Flash sales, back-in-stock alerts, cart recovery complement to email"
10. `youtube` — P3, growth+, "Product reviews, tutorials, unboxing, long-form brand building"
11. `pinterest` — P3, growth+, min $300/mo, "Visual discovery for home, fashion, beauty, food products"
12. `amazon` — P3 (or P1 if marketplace-first), "Marketplace presence — Amazon Ads + organic optimization"
13. `influencer` — P3, growth+, "UGC generation, social proof, and audience access"

**action_families:**
1. `pdp_optimization` — high priority: ["hero_image_quality", "value_prop_clarity", "price_display", "add_to_cart_prominence", "social_proof_on_pdp", "cross_sell_upsell", "product_schema_markup", "size_guide_faq"]
2. `checkout_optimization` — high priority: ["guest_checkout_enable", "payment_options_expansion", "shipping_transparency", "trust_badges", "checkout_step_reduction", "mobile_checkout_ux"]
3. `cart_recovery` — high priority: ["abandoned_cart_email_1h", "abandoned_cart_email_24h", "abandoned_cart_email_72h", "browse_abandonment_email", "sms_cart_reminder", "exit_intent_popup"]
4. `email_lifecycle` — high priority: ["welcome_series", "post_purchase_sequence", "review_request_email", "win_back_sequence", "vip_segment", "birthday_anniversary", "back_in_stock_alerts", "price_drop_alerts"]
5. `paid_acquisition` — high priority: ["meta_prospecting_campaigns", "meta_retargeting_campaigns", "google_shopping_campaigns", "google_search_brand", "google_search_category", "lookalike_audiences", "creative_testing_cadence"]
6. `social_commerce` — medium priority: ["instagram_shop_setup", "tiktok_shop_setup", "shoppable_posts", "live_shopping_events", "ugc_collection_system"]
7. `retention_programs` — medium priority: ["loyalty_program", "subscription_option", "referral_program", "vip_tiers", "reorder_reminders", "replenishment_emails"]
8. `ugc_collection` — medium priority: ["post_purchase_photo_request", "review_incentive_program", "hashtag_campaign", "influencer_seeding", "customer_spotlight_series"]

**compliance_sensitivities:**
- "Product claims must be substantiated — no miracle claims, unproven health benefits, or misleading before/after"
- "Pricing must comply with FTC guidelines — no fake markdowns, fake urgency timers, or deceptive MSRP"
- "Testimonials and reviews must be genuine — no purchased or fabricated reviews"
- "Subscribe-and-save pricing must clearly disclose recurring charges and cancellation terms"
- "Health/beauty/supplement products have additional FDA and FTC restrictions"
- "Children's products have COPPA and CPSIA requirements"
- "Email/SMS marketing must comply with CAN-SPAM and TCPA respectively"
- "International shipping claims must be accurate"

**creative_formats:**
- `product_shots`: "Clean product photography on white or lifestyle backgrounds", platforms: ["website", "meta_ads", "google_ads", "instagram", "pinterest"]
- `lifestyle_imagery`: "Products shown in real-life usage contexts", platforms: ["instagram", "meta_ads", "pinterest", "website"]
- `ugc_reposts`: "Customer photos and videos repurposed for marketing", platforms: ["instagram", "tiktok", "meta_ads", "website"]
- `sale_graphics`: "Promotional graphics for flash sales and seasonal events", platforms: ["email", "meta_ads", "instagram", "website"]
- `unboxing_scripts`: "Scripted unboxing experience videos", platforms: ["tiktok", "youtube", "instagram"]
- `comparison_charts`: "Product comparison tables vs competitors or product tiers", platforms: ["website", "email", "landing_page"]
- `size_fit_guides`: "Visual sizing and fit guides reducing returns", platforms: ["website", "email"]
- `behind_the_scenes`: "Manufacturing, sourcing, or team content building brand story", platforms: ["tiktok", "instagram", "youtube"]

**budget_heuristics:**
- `startup` (pre-launch, early-pmf): min $1000/mo, max $5000/mo, "Focus 60% on Meta Ads for initial traction. 20% on email setup (welcome + cart recovery). 10% on organic social content. 10% on Google Shopping."
- `established` (growth): min $5000/mo, max $20000/mo, "Split 40% paid acquisition (Meta + Google), 20% email/SMS, 15% SEO/content, 15% social/influencer, 10% retention programs."
- `scaling` (scale, mature): min $20000/mo, max $100000+/mo, "Diversify: Meta 25%, Google 20%, email/SMS 15%, TikTok 10%, influencer 10%, SEO 10%, retention 10%. Test new channels with 5% of budget."

**minimum_viable_channels:**
- `["website", "meta_ads", "email", "google_ads"]` — "An ecommerce business must have: a converting store, Meta Ads for acquisition, email for lifecycle revenue, and Google Shopping for high-intent traffic."

**archetype_specific_rules:**
- "ROAS is the primary metric for paid acquisition — break even at 2x, target 3-5x"
- "Email should drive 20-40% of total revenue; if below 20%, lifecycle email is underinvested"
- "Cart abandonment recovery is the highest-ROI automation — implement before scaling paid"
- "Product page conversion rate is the multiplier for all traffic — optimize PDPs before increasing ad spend"
- "UGC consistently outperforms studio creative in Meta Ads — invest in UGC collection systems"
- "Customer LTV should be calculated and used to set acquisition cost targets"
- "Seasonal planning should start 6-8 weeks before peak periods (Black Friday, holidays, etc.)"
- "Review count on PDPs directly correlates with conversion rate — automate review requests"

## Output Files

- `kai/archetypes/ecommerce.py`

## Acceptance Criteria

- [ ] `ecommerce.py` exports a `ECOMMERCE_ARCHETYPE` constant of type ArchetypeDefinition
- [ ] All 9 audit categories are listed in priority order
- [ ] All 14 KPIs are defined with correct units, directions, and benchmarks
- [ ] All 13 channels are defined with priorities, stage relevance, budget minimums, and rationale
- [ ] All 8 action families are defined with specific action lists
- [ ] Budget heuristics cover 3 stages with appropriate dollar ranges (higher than local-service)
- [ ] Compliance sensitivities cover FTC pricing, review authenticity, and product claims
- [ ] Creative formats include UGC, product shots, and ecommerce-specific assets
- [ ] Minimum viable channels are website, meta_ads, email, google_ads
- [ ] Archetype-specific rules emphasize ROAS, email revenue %, and cart recovery
- [ ] File imports from `kai.archetypes.base` (ArchetypeDefinition and sub-models)

## Reference Materials

- `kai/archetypes/base.py` (Task 006) — base classes to use
- `knowledge/playbooks/ecommerce-marketing.md` — ecommerce marketing playbook
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO playbook
- `knowledge/playbooks/customer-retention.md` — retention playbook
- `knowledge/playbooks/retargeting-remarketing.md` — retargeting playbook
- `knowledge/checklists/cro-audit-checklist.md` — conversion checklist
- `knowledge/checklists/meta-advertising-checklist.md` — Meta ads checklist
- `knowledge/checklists/paid-acquisition-checklist.md` — paid acquisition checklist
- `CLAUDE.md` — framework map and quality gate rules

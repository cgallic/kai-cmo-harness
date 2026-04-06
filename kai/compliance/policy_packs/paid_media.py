"""Paid media policy pack for the Kai compliance engine.

Covers Google Ads, Meta Ads, TikTok, LinkedIn, and general paid advertising
compliance rules drawn from the platform policy references in
``harness/references/``.
"""

from __future__ import annotations

from .base import PolicyPack, PolicyRule


def build_paid_media_policy_pack() -> PolicyPack:
    """Construct and return the paid media policy pack (24 rules)."""

    rules = [
        # ---------------------------------------------------------------
        # GOOGLE ADS
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="paid_media_google_001",
            pack="paid_media",
            category="google_ads",
            description=(
                "Healthcare-related Google Ads require certification before running. "
                "Ads for pharmaceuticals, clinical trials, addiction services, and "
                "telemedicine must be pre-approved."
            ),
            check_function_name="check_google_healthcare_cert",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=["healthcare", "pharma", "telemedicine", "addiction_services"],
            regulatory_source="Google Ads Healthcare and Medicines Policy",
            fix_guidance=(
                "Apply for Google Ads healthcare certification before launching ads. "
                "Provide required documentation (license, accreditation). Only target "
                "countries where the product/service is legally approved. Remove claims "
                "that require certification until approval is received."
            ),
            examples=[
                {
                    "violation": "Running Google Ads for an online pharmacy without healthcare certification.",
                    "correction": "Complete Google's healthcare advertiser certification, then launch ads only in certified regions with required disclaimers.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_google_002",
            pack="paid_media",
            category="google_ads",
            description=(
                "Google Ads for financial products must include required disclosures "
                "(APR, fees, repayment terms). Ads for loans, credit cards, and "
                "investment products have specific disclosure requirements."
            ),
            check_function_name="check_google_financial_disclosure",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=["finance", "lending", "insurance", "investment"],
            regulatory_source="Google Ads Financial Products Policy / FTC Truth in Lending Act",
            fix_guidance=(
                "Include all required financial disclosures in ad copy and landing page: "
                "APR range, minimum and maximum loan amounts, repayment period, total "
                "cost example, and any fees. Add 'Representative example' with specific "
                "numbers."
            ),
            examples=[
                {
                    "violation": "'Low-interest personal loans! Apply now!' with no rate, term, or fee information.",
                    "correction": "'Personal loans from 5.9% APR representative. Borrow $1,000-$50,000 over 1-7 years. Example: $10,000 over 5 years at 5.9% APR = $193/mo. Total repayable: $11,580.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_google_003",
            pack="paid_media",
            category="google_ads",
            description=(
                "Superlative claims in Google Ads ('best', '#1', 'fastest') must have "
                "third-party substantiation. Unsubstantiated superlatives will trigger "
                "ad disapproval."
            ),
            check_function_name="check_google_superlative_claims",
            severity="warning",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Ads Misrepresentation Policy",
            fix_guidance=(
                "Remove superlatives or add verifiable third-party evidence. "
                "Link to the source on the landing page. Acceptable: 'Rated #1 by "
                "G2 in Winter 2026.' Not acceptable: 'The best CRM' with no citation."
            ),
            examples=[
                {
                    "violation": "Ad headline: 'The Best Project Management Software'",
                    "correction": "Ad headline: 'Top-Rated Project Management Software' with landing page citing G2/Capterra ranking and methodology.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_google_004",
            pack="paid_media",
            category="google_ads",
            description=(
                "Google Ads must use trademarks correctly. Using a competitor's "
                "trademark in ad text is restricted in most countries. Trademark "
                "owners can file complaints to restrict usage."
            ),
            check_function_name="check_google_trademark_usage",
            severity="warning",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Ads Trademark Policy",
            fix_guidance=(
                "Do not use competitor trademarks in ad headlines or descriptions "
                "unless you are an authorized reseller, informational site, or "
                "comparison advertiser with legitimate use. Bidding on competitor "
                "keywords is allowed, but using their name in ad text is restricted."
            ),
            examples=[
                {
                    "violation": "Ad headline: 'Better Than Salesforce -- Switch Today!'",
                    "correction": "Ad headline: 'CRM That Grows With You -- Switch Today!' (bid on competitor keyword but keep ad text generic).",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_google_005",
            pack="paid_media",
            category="google_ads",
            description=(
                "Google Ads destination URLs must be functional, relevant to the ad "
                "content, and provide a good user experience. Broken links, irrelevant "
                "destinations, or pages with excessive pop-ups will cause disapproval."
            ),
            check_function_name="check_google_destination_requirements",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Ads Destination Requirements Policy",
            fix_guidance=(
                "Ensure the landing page: (1) loads correctly with no errors, "
                "(2) matches the ad's promise and keywords, (3) does not auto-redirect, "
                "(4) has no malware, (5) works on mobile, and (6) does not use excessive "
                "pop-ups or interstitials that block the main content."
            ),
            examples=[
                {
                    "violation": "An ad promising 'Free SEO Audit' that links to a generic homepage with no SEO audit mentioned.",
                    "correction": "Ad links directly to a dedicated '/free-seo-audit' landing page with a form to request the audit.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # META ADS (Facebook / Instagram)
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="paid_media_meta_001",
            pack="paid_media",
            category="meta_ads",
            description=(
                "Meta ads about housing, employment, or credit must be set as Special "
                "Ad Categories. These categories restrict targeting by age, gender, "
                "zip code, and interests to prevent discrimination."
            ),
            check_function_name="check_meta_special_ad_category",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=["US"],
            applicable_industries=["real_estate", "employment", "lending", "insurance"],
            regulatory_source="Meta Advertising Standards / Fair Housing Act / Equal Employment Opportunity Act",
            fix_guidance=(
                "When creating ads related to housing, employment, or credit: "
                "(1) select the appropriate Special Ad Category in Ads Manager, "
                "(2) accept the restricted targeting options (no age, gender, or zip "
                "code targeting), (3) use Special Ad Audiences instead of lookalikes. "
                "This applies to ALL ads in these categories, even brand awareness."
            ),
            examples=[
                {
                    "violation": "Running an apartment listing ad on Facebook targeting ages 25-34 without setting the Housing Special Ad Category.",
                    "correction": "Ad set to 'Housing' Special Ad Category with a minimum 15-mile radius targeting and no age/gender restrictions.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_meta_002",
            pack="paid_media",
            category="meta_ads",
            description=(
                "Meta ads must not use before-and-after images for health, weight loss, "
                "or body appearance. This applies to both organic boosted posts and "
                "paid ad placements."
            ),
            check_function_name="check_meta_before_after_images",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=["health", "fitness", "beauty", "weight_loss", "dental", "medical", "cosmetic_surgery"],
            regulatory_source="Meta Advertising Standards (Health and Appearance Section)",
            fix_guidance=(
                "Do not use before/after images in Meta ads for health or appearance "
                "products. Instead, show the product in use, customer testimonials "
                "(text-only), or lifestyle imagery. Before/after content may be used "
                "in organic posts (not boosted) with appropriate disclaimers."
            ),
            examples=[
                {
                    "violation": "A Meta ad for a weight loss supplement showing a split-screen before/after photo.",
                    "correction": "Ad shows a person actively exercising or preparing healthy food, with text: 'Support your wellness journey. See real customer reviews on our site.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_meta_003",
            pack="paid_media",
            category="meta_ads",
            description=(
                "Meta ads must not assert or imply knowledge of a user's personal "
                "attributes (race, ethnicity, religion, sexual orientation, health "
                "conditions, financial status)."
            ),
            check_function_name="check_meta_personal_attributes",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Meta Advertising Standards (Personal Attributes Section)",
            fix_guidance=(
                "Rewrite ad copy to avoid second-person questions or statements about "
                "personal characteristics. Instead of 'Are you struggling with debt?', "
                "use 'Many people face unexpected financial challenges.' Frame around "
                "the solution, not the user's personal situation."
            ),
            examples=[
                {
                    "violation": "'Are you overweight? Try our new supplement!'",
                    "correction": "'Reach your wellness goals with clinically studied ingredients. Learn more.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_meta_004",
            pack="paid_media",
            category="meta_ads",
            description=(
                "Meta lead ads that collect personal data must link to a privacy "
                "policy and comply with Meta's Lead Ads Terms. Data collected through "
                "lead forms must be handled according to stated purposes."
            ),
            check_function_name="check_meta_lead_ad_privacy",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Meta Lead Ads Terms / GDPR Art. 13 / CCPA",
            fix_guidance=(
                "Include a privacy policy link in every lead ad form. Add a data-use "
                "disclosure explaining how the collected information will be used. "
                "Comply with Meta's Lead Ads Terms: do not sell or share collected "
                "data beyond the stated purpose without explicit consent."
            ),
            examples=[
                {
                    "violation": "A Meta lead ad form collecting name, email, and phone with no privacy policy link and no data-use statement.",
                    "correction": "Lead form includes: privacy policy link, disclaimer text ('We use your info to contact you about our services. See our Privacy Policy.'), and only collects fields necessary for the stated purpose.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # TIKTOK
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="paid_media_tiktok_001",
            pack="paid_media",
            category="tiktok_ads",
            description=(
                "Political advertising is completely banned on TikTok. Ads cannot "
                "promote political candidates, parties, legislation, or political "
                "issues."
            ),
            check_function_name="check_tiktok_political_ban",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=["political", "advocacy", "government"],
            regulatory_source="TikTok Advertising Policies (Political Advertising Section)",
            fix_guidance=(
                "Do not run any ads on TikTok that reference political candidates, "
                "parties, elections, legislation, or political issues. This includes "
                "issue advocacy. If the content is political in nature, use a different "
                "platform that permits political advertising (with proper authorization)."
            ),
            examples=[
                {
                    "violation": "A TikTok ad promoting a candidate for local office or advocating for a ballot measure.",
                    "correction": "Political advertising is not possible on TikTok. Use Google Ads or Meta (with political ad authorization) instead.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_tiktok_002",
            pack="paid_media",
            category="tiktok_ads",
            description=(
                "TikTok ads related to weight management face strict restrictions. "
                "No ads promoting unhealthy weight-loss methods, extreme dieting, or "
                "body-shaming content."
            ),
            check_function_name="check_tiktok_weight_restrictions",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=["health", "fitness", "weight_loss", "nutrition"],
            regulatory_source="TikTok Advertising Policies (Weight Management Section)",
            fix_guidance=(
                "Avoid promoting rapid weight loss, extreme calorie restriction, or "
                "body-shaming content. Focus on holistic wellness, balanced nutrition, "
                "and healthy habits. Do not make specific weight-loss amount claims "
                "without clinical evidence."
            ),
            examples=[
                {
                    "violation": "'Lose 30 lbs in 30 days with this one trick!'",
                    "correction": "'Support your wellness journey with balanced nutrition and evidence-based guidance. Consult your healthcare provider.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_tiktok_003",
            pack="paid_media",
            category="tiktok_ads",
            description=(
                "TikTok requires disclosure when ad content is AI-generated or "
                "substantially AI-modified. The AI disclosure label must be applied "
                "to the content."
            ),
            check_function_name="check_tiktok_ai_disclosure",
            severity="violation",
            applicable_content_types=["paid_ad", "video_script"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="TikTok Advertising Policies (AI Content Disclosure) / EU AI Act",
            fix_guidance=(
                "If ad creative was generated or substantially modified by AI "
                "(including AI-generated voices, faces, or imagery), enable TikTok's "
                "AI-generated content label on the post. Clearly disclose AI involvement "
                "in the creative process."
            ),
            examples=[
                {
                    "violation": "An ad using an AI-generated spokesperson without any AI disclosure.",
                    "correction": "Ad uses TikTok's AI content label and includes text: 'Created with AI tools.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # LINKEDIN
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="paid_media_linkedin_001",
            pack="paid_media",
            category="linkedin_ads",
            description=(
                "LinkedIn ads must maintain professional context. Ad creative and "
                "copy must be appropriate for a professional audience and substantiate "
                "all B2B claims."
            ),
            check_function_name="check_linkedin_professional_context",
            severity="warning",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="LinkedIn Advertising Policies (Professional Context)",
            fix_guidance=(
                "Ensure ad copy uses professional language appropriate for LinkedIn's "
                "audience. Substantiate all B2B claims (market share, ROI figures, "
                "industry rankings) with verifiable sources. Avoid clickbait headlines "
                "or sensationalized language."
            ),
            examples=[
                {
                    "violation": "'This INSANE hack will 10X your leads overnight!!!'",
                    "correction": "'How 500+ B2B teams increased qualified leads by 40% in Q1 2026. See the case study.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_linkedin_002",
            pack="paid_media",
            category="linkedin_ads",
            description=(
                "LinkedIn requires substantiation for B2B performance claims. "
                "Statistics, ROI claims, and market position assertions in ads must "
                "be backed by evidence accessible on the landing page."
            ),
            check_function_name="check_linkedin_claim_substantiation",
            severity="warning",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="LinkedIn Advertising Policies (Substantiation)",
            fix_guidance=(
                "For every performance claim in ad copy, include the source, date, "
                "and methodology on the landing page. Use footnotes or a visible "
                "citation. Example: 'Based on a survey of 500 customers conducted by "
                "[firm] in March 2026.'"
            ),
            examples=[
                {
                    "violation": "'Our platform delivers 5X ROI' with no source or methodology on the landing page.",
                    "correction": "'Our platform delivers 5X average ROI*' with landing page footnote: '*Based on analysis of 200 customer accounts over 12 months by [research firm], March 2026.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # GENERAL PAID MEDIA
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="paid_media_general_001",
            pack="paid_media",
            category="general",
            description=(
                "All paid ads must comply with FTC endorsement guidelines. Paid "
                "partnerships, sponsored placements, and affiliate relationships "
                "must be disclosed clearly."
            ),
            check_function_name="check_ftc_endorsement_compliance",
            severity="violation",
            applicable_content_types=["paid_ad", "social_post", "video_script"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255) / FTC Act Section 5",
            fix_guidance=(
                "Ensure all paid placements are disclosed with 'Ad', 'Sponsored', or "
                "the platform's built-in disclosure mechanism. The disclosure must be "
                "clear and conspicuous -- visible without scrolling, clicking, or expanding."
            ),
            examples=[
                {
                    "violation": "A sponsored blog post with 'This post was made possible by our partners' buried in the footer.",
                    "correction": "'ADVERTISEMENT' or 'SPONSORED' label at the top of the content, before the headline, in a visible font size.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_general_002",
            pack="paid_media",
            category="general",
            description=(
                "Comparative advertising must compare on a fair basis using the same "
                "conditions and metrics. Cherry-picking data to create a misleading "
                "impression is prohibited."
            ),
            check_function_name="check_comparative_advertising",
            severity="warning",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Act Section 5 / Lanham Act (15 U.S.C. 1125(a))",
            fix_guidance=(
                "When comparing your product to competitors: (1) use the same time "
                "period, conditions, and methodology, (2) cite the source of comparison "
                "data, (3) do not disparage competitors with unsubstantiated claims, "
                "(4) ensure the comparison is still accurate and current."
            ),
            examples=[
                {
                    "violation": "Comparing your product's best-case scenario against a competitor's worst-case pricing tier.",
                    "correction": "Side-by-side comparison at equivalent pricing tiers, same feature set, with source and date cited.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_general_003",
            pack="paid_media",
            category="general",
            description=(
                "Bait-and-switch advertising is illegal. The advertised offer must be "
                "genuinely available at the stated terms. Ads cannot lure customers "
                "with an offer the advertiser does not intend to honor."
            ),
            check_function_name="check_bait_and_switch",
            severity="violation",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Act Section 5 / FTC Guides Against Bait Advertising (16 CFR Part 238)",
            fix_guidance=(
                "Ensure every advertised offer is genuinely available: (1) maintain "
                "sufficient inventory of advertised items, (2) do not disparage the "
                "advertised product to switch customers, (3) do not refuse to show "
                "or sell the advertised item, (4) if the offer has limitations, "
                "disclose them clearly in the ad."
            ),
            examples=[
                {
                    "violation": "Advertising a '$99 website design' offer but telling all inquiries the $99 option is 'sold out' and upselling to $999.",
                    "correction": "Advertising '$99 website design (limited to first 20 clients per month)' and genuinely honoring the offer for qualifying customers.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_general_004",
            pack="paid_media",
            category="landing_page_alignment",
            description=(
                "Ad claims must match landing page content. The landing page must "
                "deliver on the ad's promise, contain the same offer, and not mislead "
                "users who clicked."
            ),
            check_function_name="check_ad_landing_page_alignment",
            severity="warning",
            applicable_content_types=["paid_ad", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Ads Destination Requirements / Meta Ad Relevance / FTC Act Section 5",
            fix_guidance=(
                "Audit every ad-to-landing-page pair: (1) the headline promise in the "
                "ad must appear on the landing page, (2) pricing and terms must match, "
                "(3) the CTA action must be available immediately, (4) no bait-and-"
                "switch between ad and page content."
            ),
            examples=[
                {
                    "violation": "Ad says 'Download Free Guide' but the landing page requires a paid subscription to access the guide.",
                    "correction": "Ad says 'Download Free Guide' and the landing page offers the guide for free (email-gated or ungated) with no paid requirement.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_general_005",
            pack="paid_media",
            category="prohibited_categories",
            description=(
                "Each ad platform prohibits specific product/service categories. "
                "Advertisers must verify their product is allowed on the target "
                "platform before launching campaigns."
            ),
            check_function_name="check_prohibited_category",
            severity="violation",
            applicable_content_types=["paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Platform-specific prohibited content policies",
            fix_guidance=(
                "Before launching ads, review the target platform's prohibited content "
                "list. Common prohibitions include: illegal products, weapons, tobacco, "
                "recreational drugs, counterfeit goods, surveillance equipment, and "
                "payday loans. Some categories (crypto, gambling, alcohol, pharma) are "
                "restricted but allowed with certification."
            ),
            examples=[
                {
                    "violation": "Running Google Ads for a CBD product without checking Google's policy on cannabis-derived products.",
                    "correction": "Verify Google's current CBD/hemp policy (varies by country), obtain required certifications, and ensure ad copy and landing page comply with all restrictions before launching.",
                }
            ],
        ),
        PolicyRule(
            rule_id="paid_media_general_006",
            pack="paid_media",
            category="general",
            description=(
                "Paid ad landing pages must include the business's legal name, "
                "contact information, and privacy policy. This is required by both "
                "platform policies and regulatory standards."
            ),
            check_function_name="check_landing_page_legal_info",
            severity="warning",
            applicable_content_types=["landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Ads Destination Requirements / Meta Advertising Standards / FTC Act Section 5",
            fix_guidance=(
                "Ensure every ad landing page includes: (1) the business legal name, "
                "(2) a contact method (email, phone, or form), (3) a link to the "
                "privacy policy, and (4) terms of service for any offer on the page."
            ),
            examples=[
                {
                    "violation": "A landing page with no business name, no contact info, and no privacy policy -- just a lead form and a sales pitch.",
                    "correction": "Landing page footer includes: business name, phone/email, privacy policy link, and terms of service link.",
                }
            ],
        ),
    ]

    return PolicyPack(
        pack_name="paid_media",
        description=(
            "Compliance rules for paid advertising across Google Ads, Meta "
            "(Facebook/Instagram), TikTok, LinkedIn, and general advertising "
            "law. Covers platform-specific policies, FTC requirements, "
            "prohibited categories, and landing page alignment."
        ),
        rules=rules,
    )

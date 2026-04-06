"""Social media policy pack for the Kai compliance engine.

Covers FTC disclosure, contest/sweepstakes rules, employee social media,
influencer partnerships, platform-specific content standards, and
age-restricted content rules.
"""

from __future__ import annotations

from .base import PolicyPack, PolicyRule


def build_social_policy_pack() -> PolicyPack:
    """Construct and return the social media policy pack (18 rules)."""

    rules = [
        # ---------------------------------------------------------------
        # FTC DISCLOSURE
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_disclosure_001",
            pack="social",
            category="disclosure",
            description=(
                "Sponsored social media posts must clearly disclose the material "
                "connection between the brand and the poster using #ad, #sponsored, "
                "or the platform's paid partnership tag."
            ),
            check_function_name="check_sponsorship_disclosure",
            severity="violation",
            applicable_content_types=["social_post", "social_story", "video_script"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255)",
            fix_guidance=(
                "Add '#ad' or '#sponsored' at the beginning of the caption -- not "
                "buried among other hashtags. On Instagram and TikTok, also use the "
                "platform's built-in paid partnership label. The disclosure must be "
                "visible without clicking 'See More'."
            ),
            examples=[
                {
                    "violation": "A brand-paid Instagram post with #blessed #partner at the end of 30 hashtags.",
                    "correction": "#ad | Loving this new skincare routine from @BrandName. [rest of caption]",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_disclosure_002",
            pack="social",
            category="disclosure",
            description=(
                "Influencer partnerships must include clear FTC-compliant disclosure "
                "of the material connection. The influencer, the brand, and any "
                "intermediary agency are all liable for non-disclosure."
            ),
            check_function_name="check_influencer_disclosure",
            severity="violation",
            applicable_content_types=["social_post", "social_story", "video_script"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255) / FTC Act Section 5",
            fix_guidance=(
                "Require all influencers to use '#ad' or the platform's paid "
                "partnership tag. Include disclosure requirements in the influencer "
                "contract. Monitor posts to confirm disclosure is present and visible. "
                "Brands must educate influencers and verify compliance."
            ),
            examples=[
                {
                    "violation": "An influencer posts a product review after receiving a free product, with no disclosure anywhere.",
                    "correction": "Post begins with '#ad' or uses Instagram's 'Paid Partnership with @Brand' label, plus '#gifted' if the product was free.",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_disclosure_003",
            pack="social",
            category="disclosure",
            description=(
                "Employee posts about their own company on personal social media must "
                "disclose the employment relationship."
            ),
            check_function_name="check_employee_disclosure",
            severity="warning",
            applicable_content_types=["social_post", "social_story"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255)",
            fix_guidance=(
                "Employees should add a disclosure such as 'I work at [Company]' in "
                "posts about the company's products or services. This can be in the "
                "bio or in individual posts. If the post could be seen as an endorsement, "
                "in-post disclosure is required."
            ),
            examples=[
                {
                    "violation": "A marketing manager posts 'Just tried the new release -- amazing product!' on their personal LinkedIn without mentioning they work for the company.",
                    "correction": "'Just tried our new release -- amazing product! (Full disclosure: I work at Acme Corp as a marketing manager.)'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CONTEST / SWEEPSTAKES
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_contest_001",
            pack="social",
            category="contests",
            description=(
                "Social media contests and sweepstakes must include official rules, "
                "state 'no purchase necessary', list eligibility restrictions, "
                "and note 'void where prohibited'."
            ),
            check_function_name="check_contest_rules",
            severity="violation",
            applicable_content_types=["social_post", "social_story"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="FTC Act Section 5 / State sweepstakes laws (all 50 states)",
            fix_guidance=(
                "Include or link to official rules in every contest post. The rules "
                "must state: no purchase necessary, alternate method of entry, "
                "eligibility (age, geography), odds of winning, prize value, start/end "
                "dates, and 'void where prohibited'. Some states require registration "
                "and bonding for prizes above certain values."
            ),
            examples=[
                {
                    "violation": "'Like and share to win a $500 gift card!' with no rules or disclaimers.",
                    "correction": "'Like and share for a chance to win a $500 gift card! No purchase necessary. Must be 18+ and US resident. See official rules: [link]. Ends 5/31/2026. Void where prohibited.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # USER CONTENT / REPOSTING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_ugc_001",
            pack="social",
            category="user_content",
            description=(
                "Reposting user-generated content (UGC) requires either explicit "
                "permission from the original creator or proper attribution under "
                "the platform's sharing mechanisms."
            ),
            check_function_name="check_ugc_permission",
            severity="warning",
            applicable_content_types=["social_post", "social_story"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Copyright Act (17 U.S.C.) / Platform Terms of Service",
            fix_guidance=(
                "Before reposting UGC: (1) ask the creator for written permission "
                "(DM or email is acceptable), (2) use the platform's native repost/share "
                "function which preserves attribution, or (3) credit the creator with "
                "@mention and written credit in the caption. Keep a record of permissions."
            ),
            examples=[
                {
                    "violation": "Downloading a customer's photo and re-uploading it to the brand account with no credit.",
                    "correction": "Reposting with: 'Photo by @customer_handle. Shared with permission. We love seeing how you use our product!'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # PLATFORM-SPECIFIC RULES
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_platform_facebook_001",
            pack="social",
            category="platform_rules",
            description=(
                "Facebook posts must comply with Community Standards: no misinformation "
                "rated false by third-party fact-checkers, no coordinated inauthentic "
                "behavior, and no engagement bait ('like if you agree')."
            ),
            check_function_name="check_facebook_community_standards",
            severity="warning",
            applicable_content_types=["social_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Meta Community Standards (2026)",
            fix_guidance=(
                "Review content against Meta's Community Standards before posting. "
                "Avoid engagement bait phrases ('tag a friend', 'share if you agree'), "
                "unverifiable health claims, and sensationalized headlines. Cite credible "
                "sources for factual claims."
            ),
            examples=[
                {
                    "violation": "'SHARE this before Facebook DELETES it! This one trick doctors don't want you to know...'",
                    "correction": "'3 evidence-based ways to improve sleep quality, according to the Sleep Foundation. Link in comments.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_platform_instagram_001",
            pack="social",
            category="platform_rules",
            description=(
                "Instagram content must comply with Community Guidelines including "
                "no misleading content, proper use of branded content tools for "
                "partnerships, and compliance with commerce policies for product tags."
            ),
            check_function_name="check_instagram_community_guidelines",
            severity="warning",
            applicable_content_types=["social_post", "social_story"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Instagram Community Guidelines / Meta Branded Content Policies",
            fix_guidance=(
                "Use Instagram's Branded Content tools for paid partnerships. Follow "
                "Instagram's commerce policies when tagging products. Ensure content "
                "is original or properly credited. Avoid misleading captions or "
                "deceptive editing."
            ),
            examples=[
                {
                    "violation": "A paid brand post that does not use Instagram's Paid Partnership label.",
                    "correction": "Post uses 'Paid partnership with @Brand' label toggled on in the branded content settings.",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_platform_linkedin_001",
            pack="social",
            category="platform_rules",
            description=(
                "LinkedIn content must maintain professional context. Posts must comply "
                "with the Professional Community Policies: no misleading professional "
                "claims, no fake engagement pods, and no deceptive content."
            ),
            check_function_name="check_linkedin_professional_standards",
            severity="warning",
            applicable_content_types=["social_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="LinkedIn Professional Community Policies (2026)",
            fix_guidance=(
                "Ensure professional claims (titles, certifications, achievements) "
                "are accurate. Do not use engagement pods or automated engagement tools. "
                "Keep content professional in tone and relevant to the business context."
            ),
            examples=[
                {
                    "violation": "Posting 'Agree?' with a generic motivational image to farm engagement, using a pod to boost initial likes.",
                    "correction": "Sharing a genuine professional insight with original commentary that adds value to the reader's work.",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_platform_tiktok_001",
            pack="social",
            category="platform_rules",
            description=(
                "TikTok content must comply with Community Guidelines: no misleading "
                "information, mandatory AI content disclosure using the AI-generated "
                "content label, and no undisclosed paid promotions."
            ),
            check_function_name="check_tiktok_community_guidelines",
            severity="warning",
            applicable_content_types=["social_post", "social_story", "video_script"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="TikTok Community Guidelines (2026)",
            fix_guidance=(
                "Label AI-generated content using TikTok's built-in AI disclosure tool. "
                "Use the Ad Disclosure toggle for sponsored content. Avoid misleading "
                "information or deceptive editing. Follow TikTok's branded content "
                "toggle requirements."
            ),
            examples=[
                {
                    "violation": "A brand posts an AI-generated video without any AI disclosure label.",
                    "correction": "Video posted with TikTok's 'AI-generated content' label enabled and paid partnership toggle active if sponsored.",
                }
            ],
        ),
        PolicyRule(
            rule_id="social_platform_x_001",
            pack="social",
            category="platform_rules",
            description=(
                "X/Twitter content must follow the platform rules: no manipulation "
                "of trending topics, no coordinated inauthentic behavior, and proper "
                "labeling of automated accounts."
            ),
            check_function_name="check_x_platform_rules",
            severity="warning",
            applicable_content_types=["social_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="X/Twitter Rules (2026)",
            fix_guidance=(
                "Do not use bots, purchased followers, or coordinated accounts to "
                "artificially amplify content. Label automated accounts as bots. "
                "Ensure paid promotions are disclosed. Do not manipulate trending "
                "topics with repetitive or irrelevant hashtags."
            ),
            examples=[
                {
                    "violation": "Using 20 bot accounts to simultaneously retweet a promotional post to trend.",
                    "correction": "Organic promotion with genuine engagement. Sponsored posts use X's ad tools or include '#ad' disclosure.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # BEFORE / AFTER CONTENT
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_beforeafter_001",
            pack="social",
            category="before_after",
            description=(
                "Before-and-after images or videos must not be manipulated, must "
                "represent genuine results, and must comply with platform-specific "
                "restrictions (Meta prohibits before/after in health/weight ads)."
            ),
            check_function_name="check_before_after_content",
            severity="warning",
            applicable_content_types=["social_post", "social_story", "paid_ad"],
            applicable_regions=[],
            applicable_industries=["health", "fitness", "beauty", "weight_loss", "dental", "medical"],
            regulatory_source="FTC Endorsement Guides / Meta Advertising Policies / TikTok Community Guidelines",
            fix_guidance=(
                "Ensure before/after images are unaltered and show genuine results. "
                "Include a disclaimer if results are atypical. On Meta platforms, do NOT "
                "use before/after images in health or weight-related ads. On TikTok, "
                "before/after weight content faces restrictions."
            ),
            examples=[
                {
                    "violation": "A weight-loss before/after photo used in a Meta ad with lighting changes to exaggerate results.",
                    "correction": "Organic post (not ad) with unaltered photos, consistent lighting, and disclaimer: 'Individual results vary. Sarah followed our program for 6 months alongside a balanced diet.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # TESTIMONIALS ON SOCIAL
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_testimonial_001",
            pack="social",
            category="testimonials",
            description=(
                "Testimonials shared on social media must represent typical results. "
                "If the testimonial shows exceptional outcomes, a typical-results "
                "disclosure is required."
            ),
            check_function_name="check_social_testimonial_typicality",
            severity="warning",
            applicable_content_types=["social_post", "social_story", "video_script"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255)",
            fix_guidance=(
                "When sharing customer testimonials on social media, add what the "
                "typical customer experiences. 'Results not typical' alone is NOT "
                "sufficient. State the actual typical outcome. If the customer received "
                "compensation or free product, disclose that too."
            ),
            examples=[
                {
                    "violation": "Reposting a customer's tweet: 'I made $50K in my first month!' without context.",
                    "correction": "Repost with added context: 'Amazing result from @customer! Note: Most new users earn $500-$2,000 in their first month. Individual results vary based on effort and market.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # POLITICAL / SOCIAL ISSUE CONTENT
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_political_001",
            pack="social",
            category="political_content",
            description=(
                "Branded content touching political or social issues may trigger "
                "additional platform rules including ad authorization requirements, "
                "disclaimer mandates, and content restrictions."
            ),
            check_function_name="check_political_content_rules",
            severity="warning",
            applicable_content_types=["social_post", "social_story", "paid_ad"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Platform-specific political ad policies / EU DSA / US state disclosure laws",
            fix_guidance=(
                "If posting about political or social issues as a brand: (1) check "
                "whether the platform requires ad authorization (Meta, Google, TikTok "
                "ban political ads entirely), (2) add required disclaimers ('Paid for "
                "by...'), (3) consider whether the brand position is aligned with "
                "company values and stakeholder expectations."
            ),
            examples=[
                {
                    "violation": "Running a Meta ad that takes a position on a political issue without realizing Meta classifies it as a Special Ad Category.",
                    "correction": "If the content relates to social issues, elections, or politics: verify platform eligibility, get authorized, add 'Paid for by' disclaimer, and use the platform's political ad tools.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # AGE-RESTRICTED CONTENT
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_age_001",
            pack="social",
            category="age_restricted",
            description=(
                "Content promoting alcohol, gambling, or other age-restricted products "
                "must use the platform's age-gating features and comply with applicable "
                "laws on marketing these products to minors."
            ),
            check_function_name="check_age_restricted_content",
            severity="violation",
            applicable_content_types=["social_post", "social_story", "paid_ad", "video_script"],
            applicable_regions=[],
            applicable_industries=["alcohol", "gambling", "cannabis", "tobacco", "firearms"],
            regulatory_source="Platform-specific age-gating policies / TTB (alcohol) / State gambling laws",
            fix_guidance=(
                "Use the platform's age-restriction settings to limit visibility to "
                "users of legal age. On Instagram/Facebook, set the page's age-gate. "
                "On YouTube, mark videos as age-restricted. Never target ads for "
                "age-restricted products to audiences under the legal age. Include "
                "responsible-use messaging where required."
            ),
            examples=[
                {
                    "violation": "A brewery posts a TikTok promoting a new beer with no age restriction set, visible to all users including minors.",
                    "correction": "Post includes age-gate setting, targets 21+ audience, includes 'Must be 21+ to purchase. Drink responsibly.' disclaimer.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # FAKE ENGAGEMENT / SOCIAL PROOF
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_fake_engagement_001",
            pack="social",
            category="fake_engagement",
            description=(
                "Purchasing fake followers, likes, views, comments, or other "
                "artificial social proof is prohibited by FTC rules and platform "
                "terms of service."
            ),
            check_function_name="check_fake_engagement",
            severity="violation",
            applicable_content_types=["social_post", "social_story"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Fake Reviews Rule (2024) / Platform Terms of Service",
            fix_guidance=(
                "Never purchase followers, likes, or engagement. Remove any purchased "
                "fake engagement. Build audience organically through quality content, "
                "community engagement, and legitimate paid promotion via the platform's "
                "ad tools."
            ),
            examples=[
                {
                    "violation": "Buying 10,000 Instagram followers from a third-party service to appear more established.",
                    "correction": "Growing followers organically through consistent posting, engagement with the community, and Instagram's official promotion tools.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # SOCIAL MEDIA REVIEW SOLICITATION
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_reviews_001",
            pack="social",
            category="reviews",
            description=(
                "Review gating -- selectively soliciting reviews only from satisfied "
                "customers while suppressing negative reviews -- is prohibited by FTC "
                "rules."
            ),
            check_function_name="check_review_gating",
            severity="violation",
            applicable_content_types=["social_post", "review_response"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="FTC Fake Reviews Rule (2024)",
            fix_guidance=(
                "Send review requests to ALL customers, not just those who gave "
                "positive feedback. Do not use satisfaction surveys to filter out "
                "unhappy customers before asking for public reviews. Do not use legal "
                "threats or intimidation to suppress negative reviews."
            ),
            examples=[
                {
                    "violation": "Asking customers to rate 1-5 internally, then only sending Google review links to 4-5 star raters.",
                    "correction": "Sending a review request to all customers: 'We'd love your honest feedback on Google. Your review helps other customers make informed decisions.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # NATIVE / SPONSORED CONTENT LABELING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="social_native_001",
            pack="social",
            category="native_advertising",
            description=(
                "Sponsored or native content that resembles organic editorial posts "
                "must be clearly labeled as advertising so consumers can distinguish "
                "paid content from genuine opinions."
            ),
            check_function_name="check_native_ad_labeling",
            severity="violation",
            applicable_content_types=["social_post", "social_story", "blog_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Native Advertising Enforcement Policy (2015) / FTC Act Section 5",
            fix_guidance=(
                "Label all sponsored or paid content clearly. Use 'Ad', 'Sponsored', "
                "or 'Paid Partnership' -- not 'Promoted' or 'Presented by'. The label "
                "must appear BEFORE the content, not buried at the end. Use the platform's "
                "built-in branded content tools where available."
            ),
            examples=[
                {
                    "violation": "A blog-style LinkedIn post that reads like personal experience but was paid for by a brand, with only 'Thanks to @brand' at the very end.",
                    "correction": "Post begins with 'Paid partnership with @Brand' label visible before any content, or uses LinkedIn's branded content toggle.",
                }
            ],
        ),
    ]

    return PolicyPack(
        pack_name="social",
        description=(
            "Compliance rules for social media content covering FTC disclosure "
            "requirements, influencer partnerships, contest/sweepstakes rules, "
            "platform-specific community standards, age-restricted content, and "
            "anti-manipulation policies."
        ),
        rules=rules,
    )

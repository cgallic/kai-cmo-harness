"""Website policy pack for the Kai compliance engine.

Covers accessibility (ADA/WCAG), privacy (GDPR/CCPA), content claims (FTC),
and contact-information best practices for websites and landing pages.
"""

from __future__ import annotations

from .base import PolicyPack, PolicyRule


def build_website_policy_pack() -> PolicyPack:
    """Construct and return the website policy pack (18 rules)."""

    rules = [
        # ---------------------------------------------------------------
        # ACCESSIBILITY
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="website_accessibility_001",
            pack="website",
            category="accessibility",
            description=(
                "All images must have descriptive alt text so screen readers can "
                "convey the content to visually impaired users."
            ),
            check_function_name="check_alt_text_present",
            severity="violation",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="ADA / WCAG 2.1 Level A (1.1.1 Non-text Content)",
            fix_guidance=(
                "Add a meaningful alt attribute to every <img> tag. Decorative images "
                "should use alt=\"\" (empty string) so screen readers skip them."
            ),
            examples=[
                {
                    "violation": '<img src="team.jpg">',
                    "correction": '<img src="team.jpg" alt="The Acme marketing team at the 2025 company retreat">',
                }
            ],
        ),
        PolicyRule(
            rule_id="website_accessibility_002",
            pack="website",
            category="accessibility",
            description=(
                "Text and interactive elements must meet WCAG AA color contrast "
                "ratios: 4.5:1 for normal text and 3:1 for large text."
            ),
            check_function_name="check_color_contrast_ratio",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="ADA / WCAG 2.1 Level AA (1.4.3 Contrast Minimum)",
            fix_guidance=(
                "Use a contrast checker tool to verify foreground/background color pairs. "
                "Increase contrast by darkening text or lightening backgrounds until the "
                "ratio meets 4.5:1 for body text and 3:1 for text 18px+ bold or 24px+ regular."
            ),
            examples=[
                {
                    "violation": "Light gray (#999) text on a white (#fff) background — ratio 2.85:1.",
                    "correction": "Dark gray (#595959) text on a white (#fff) background — ratio 7.0:1.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_accessibility_003",
            pack="website",
            category="accessibility",
            description=(
                "All form inputs must have associated <label> elements or aria-label "
                "attributes so assistive technology can identify the purpose of each field."
            ),
            check_function_name="check_form_labels",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="ADA / WCAG 2.1 Level A (1.3.1 Info and Relationships)",
            fix_guidance=(
                "Wrap each input in a <label> element or add a 'for' attribute on the "
                "label that matches the input's 'id'. Alternatively, use aria-label or "
                "aria-labelledby on the input element."
            ),
            examples=[
                {
                    "violation": '<input type="email" placeholder="Email">',
                    "correction": '<label for="email">Email address</label><input id="email" type="email" placeholder="you@example.com">',
                }
            ],
        ),
        PolicyRule(
            rule_id="website_accessibility_004",
            pack="website",
            category="accessibility",
            description=(
                "All interactive elements (buttons, links, form controls) must be "
                "operable using only a keyboard (Tab, Enter, Space, Arrow keys)."
            ),
            check_function_name="check_keyboard_accessibility",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="ADA / WCAG 2.1 Level A (2.1.1 Keyboard)",
            fix_guidance=(
                "Use native HTML elements (<button>, <a>, <select>) which are keyboard-"
                "accessible by default. If custom elements are required, add tabindex=\"0\" "
                "and handle keydown events for Enter and Space."
            ),
            examples=[
                {
                    "violation": '<div class="btn" onclick="submit()">Submit</div>',
                    "correction": '<button type="submit" class="btn">Submit</button>',
                }
            ],
        ),
        PolicyRule(
            rule_id="website_accessibility_005",
            pack="website",
            category="accessibility",
            description=(
                "Pages must have a logical heading hierarchy starting with a single "
                "h1 and descending through h2, h3, etc. without skipping levels."
            ),
            check_function_name="check_heading_hierarchy",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="ADA / WCAG 2.1 Level A (1.3.1 Info and Relationships)",
            fix_guidance=(
                "Ensure each page has exactly one <h1>. Structure subsections with <h2>, "
                "then <h3> inside those, and so on. Do not skip from h1 to h3 directly."
            ),
            examples=[
                {
                    "violation": "<h1>Services</h1><h3>Web Design</h3><h3>SEO</h3>",
                    "correction": "<h1>Services</h1><h2>Web Design</h2><h2>SEO</h2>",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # PRIVACY
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="website_privacy_001",
            pack="website",
            category="privacy",
            description=(
                "Every page that collects personal data (forms, cookies, tracking) must "
                "include a link to the site's privacy policy."
            ),
            check_function_name="check_privacy_policy_link",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="GDPR Art. 13 / CCPA / FTC Act Section 5",
            fix_guidance=(
                "Add a clearly labeled 'Privacy Policy' link in the page footer and "
                "near any data-collection form. The link must point to an accessible, "
                "up-to-date privacy policy document."
            ),
            examples=[
                {
                    "violation": "A lead-capture form with no privacy policy link anywhere on the page.",
                    "correction": "Add 'By submitting, you agree to our <a href=\"/privacy\">Privacy Policy</a>.' below the form, plus a footer link.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_privacy_002",
            pack="website",
            category="privacy",
            description=(
                "A cookie consent banner must be displayed to EU visitors before any "
                "non-essential cookies are set. The banner must offer a genuine choice "
                "to accept or reject cookies."
            ),
            check_function_name="check_cookie_consent_banner",
            severity="violation",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) / ePrivacy Directive Art. 5(3)",
            fix_guidance=(
                "Implement a cookie consent management platform (CMP) that: (1) blocks "
                "non-essential cookies until consent is given, (2) provides equally "
                "prominent 'Accept' and 'Reject' buttons, (3) allows granular selection "
                "of cookie categories, and (4) stores consent records."
            ),
            examples=[
                {
                    "violation": "A banner with only an 'Accept All' button and no way to decline.",
                    "correction": "A banner with 'Accept All', 'Reject All', and 'Manage Preferences' buttons that blocks tracking scripts until consent is given.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_privacy_003",
            pack="website",
            category="privacy",
            description=(
                "California visitors must be shown a 'Do Not Sell or Share My Personal "
                "Information' link if the site sells or shares personal data for "
                "cross-context behavioral advertising."
            ),
            check_function_name="check_ccpa_opt_out_link",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=["US", "US-CA"],
            applicable_industries=[],
            regulatory_source="CCPA / CPRA (Cal. Civ. Code 1798.120)",
            fix_guidance=(
                "Add a 'Do Not Sell or Share My Personal Information' link in the site "
                "footer. The link must lead to a functional opt-out mechanism. Honor "
                "the Global Privacy Control (GPC) browser signal as a valid opt-out request."
            ),
            examples=[
                {
                    "violation": "No CCPA opt-out link present on the site, despite using retargeting pixels.",
                    "correction": "Footer link 'Do Not Sell or Share My Personal Information' leading to an opt-out form that disables third-party tracking when submitted.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_privacy_004",
            pack="website",
            category="privacy",
            description=(
                "Data-collection forms must include a clear statement of how the "
                "collected data will be used, stored, and shared."
            ),
            check_function_name="check_data_usage_disclosure",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="GDPR Art. 13 / FTC Act Section 5",
            fix_guidance=(
                "Add a short data-use disclosure adjacent to the form (e.g., 'We use "
                "your email to send the requested guide and occasional marketing "
                "updates. You can unsubscribe anytime. See our Privacy Policy.'). "
                "Be specific about the purpose of each data field."
            ),
            examples=[
                {
                    "violation": "A form asking for name, email, phone with no explanation of how the data is used.",
                    "correction": "Below the form: 'We'll use your info to schedule a free consultation. We never sell your data. See our Privacy Policy for details.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CONTENT CLAIMS
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="website_claims_001",
            pack="website",
            category="content_claims",
            description=(
                "Superlative claims ('best', 'fastest', '#1', 'leading') must be "
                "substantiated with verifiable evidence or qualified as opinion."
            ),
            check_function_name="check_superlative_substantiation",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "blog_post", "case_study"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Act Section 5 / NAD Self-Regulatory Standards",
            fix_guidance=(
                "Either remove the superlative, add a verifiable citation (e.g., 'Rated "
                "#1 by G2 in Winter 2026'), or reframe as subjective opinion (e.g., "
                "'We believe we build the best...'). The substantiation must exist "
                "BEFORE the claim is published."
            ),
            examples=[
                {
                    "violation": "We are the #1 CRM for small businesses.",
                    "correction": "Rated #1 CRM for small businesses by G2 (Winter 2026, 500+ reviews).",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_claims_002",
            pack="website",
            category="content_claims",
            description=(
                "Testimonials displayed on the site must be genuine, attributable to "
                "a real person, and reflect their honest experience."
            ),
            check_function_name="check_testimonial_authenticity",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "case_study", "testimonial"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255) / FTC Fake Reviews Rule (2024)",
            fix_guidance=(
                "Verify that every testimonial comes from a real customer. Include the "
                "person's name (or first name + last initial), role, and company where "
                "possible. Do not fabricate, edit for meaning, or use AI-generated "
                "testimonials. If the reviewer received compensation, disclose it."
            ),
            examples=[
                {
                    "violation": "'This product changed my life!' - Anonymous",
                    "correction": "'This product cut our onboarding time by 40%.' - Sarah M., Head of Ops at Acme Corp",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_claims_003",
            pack="website",
            category="content_claims",
            description=(
                "Results claims ('increased revenue 300%', 'lost 20 lbs') must include "
                "a typical-results disclaimer if the result is not what most users achieve."
            ),
            check_function_name="check_results_disclaimer",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "case_study", "testimonial"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Endorsement Guides (16 CFR Part 255)",
            fix_guidance=(
                "Add a clear disclosure of what typical users can expect. 'Results not "
                "typical' alone is NOT sufficient -- state the actual typical outcome. "
                "Example: 'Results vary. The average customer sees a 15-30% improvement "
                "in the first 90 days.'"
            ),
            examples=[
                {
                    "violation": "'We helped Acme grow revenue 300% in 6 months.'",
                    "correction": "'We helped Acme grow revenue 300% in 6 months. Results vary; the average client sees 40-80% growth in the first year.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_claims_004",
            pack="website",
            category="content_claims",
            description=(
                "Pricing shown on the website must be accurate, current, and include "
                "all mandatory fees. Hidden fees or stale pricing is deceptive."
            ),
            check_function_name="check_pricing_accuracy",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="FTC Act Section 5 / FTC Junk Fee Rule (2025)",
            fix_guidance=(
                "Review pricing pages at least monthly. If the price does not include "
                "all mandatory fees, list them prominently. If pricing changes, update "
                "the page immediately. Add a 'last updated' date to pricing sections."
            ),
            examples=[
                {
                    "violation": "'Starting at $29/mo' when there is a mandatory $10/mo platform fee not disclosed until checkout.",
                    "correction": "'Starting at $39/mo (includes $10 platform fee). No hidden charges.' Or list all fees in a breakdown table.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CONTACT INFORMATION
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="website_contact_001",
            pack="website",
            category="contact_information",
            description=(
                "A business phone number should be visible on every page, typically "
                "in the header or footer, so visitors can reach the business directly."
            ),
            check_function_name="check_phone_number_visible",
            severity="recommendation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source=None,
            fix_guidance=(
                "Add the primary business phone number to the site header or footer. "
                "For businesses that receive phone leads, consider a click-to-call link "
                "and KaiCalls AI receptionist integration for after-hours handling."
            ),
            examples=[
                {
                    "violation": "No phone number anywhere on the site. Contact page only shows a form.",
                    "correction": "Phone number in the header: '(555) 123-4567' with a click-to-call <a href=\"tel:+15551234567\"> link.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_contact_002",
            pack="website",
            category="contact_information",
            description=(
                "A physical street address must be visible on the site for local "
                "businesses. This is required for local SEO and may be legally required "
                "depending on jurisdiction."
            ),
            check_function_name="check_physical_address_visible",
            severity="recommendation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=["local_service", "restaurant", "retail", "healthcare", "legal", "real_estate"],
            regulatory_source="Google Business Profile guidelines / CAN-SPAM (for email senders)",
            fix_guidance=(
                "Add the full business address to the footer and the contact page. "
                "Use schema.org LocalBusiness markup so search engines can parse it. "
                "If serving multiple locations, list each location with its address."
            ),
            examples=[
                {
                    "violation": "A local plumbing company's site shows no street address.",
                    "correction": "Footer: '123 Main St, Suite 4, Springfield, IL 62701' with embedded Google Map on the contact page.",
                }
            ],
        ),
        PolicyRule(
            rule_id="website_contact_003",
            pack="website",
            category="contact_information",
            description=(
                "A contact form or live chat widget should be accessible from every "
                "page so visitors always have a low-friction way to get in touch."
            ),
            check_function_name="check_contact_form_accessible",
            severity="recommendation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source=None,
            fix_guidance=(
                "Add a persistent contact element: a footer contact form, a floating "
                "chat widget, or a 'Contact Us' button that is visible on every page. "
                "Ensure the form is keyboard-accessible and has proper labels."
            ),
            examples=[
                {
                    "violation": "Only the 'Contact' page has a way to reach the business. Other pages have no contact path.",
                    "correction": "A sticky chat widget on every page, plus a short contact form in the footer with name, email, and message fields.",
                }
            ],
        ),
    ]

    return PolicyPack(
        pack_name="website",
        description=(
            "Compliance rules for websites and landing pages covering "
            "accessibility (ADA/WCAG), privacy (GDPR/CCPA), content claims "
            "(FTC), and contact-information best practices."
        ),
        rules=rules,
    )

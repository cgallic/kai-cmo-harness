"""Analytics and tracking policy pack for the Kai compliance engine.

Covers GDPR cookie consent, GA4 consent mode, CCPA do-not-sell signals,
data retention, PII handling, IP anonymization, third-party tracking
disclosure, server-side tracking, cross-device tracking, and remarketing
audience consent.
"""

from __future__ import annotations

from .base import PolicyPack, PolicyRule


def build_analytics_policy_pack() -> PolicyPack:
    """Construct and return the analytics policy pack (12 rules)."""

    rules = [
        # ---------------------------------------------------------------
        # COOKIE CONSENT
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_consent_001",
            pack="analytics",
            category="cookie_consent",
            description=(
                "Analytics cookies (GA4, Hotjar, Mixpanel, etc.) require explicit "
                "consent from EU visitors before being set. The consent banner must "
                "offer a genuine reject option that is as easy to use as accept."
            ),
            check_function_name="check_analytics_cookie_consent",
            severity="violation",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) / ePrivacy Directive Art. 5(3)",
            fix_guidance=(
                "Implement a Consent Management Platform (CMP) that: (1) blocks ALL "
                "analytics scripts until consent is given, (2) provides an 'Accept' "
                "and 'Reject' button of equal visual prominence, (3) categorizes "
                "cookies (necessary, analytics, marketing) with individual toggles, "
                "(4) stores proof of consent. Do not load GA4/Hotjar/etc. tags "
                "before the user has accepted."
            ),
            examples=[
                {
                    "violation": "GA4 fires on page load before any consent banner is shown. The banner only has an 'OK' button.",
                    "correction": "GA4 loads only after the user clicks 'Accept Analytics Cookies'. The banner offers 'Accept All', 'Reject All', and 'Manage Preferences' with a link to the cookie policy.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # GA4 CONSENT MODE
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_consent_002",
            pack="analytics",
            category="consent_mode",
            description=(
                "GA4 consent mode must be configured for EU visitors. When consent "
                "is denied, GA4 should use cookieless pings (consent mode v2) as a "
                "privacy-safe fallback rather than dropping data entirely."
            ),
            check_function_name="check_ga4_consent_mode",
            severity="warning",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR / Google EU User Consent Policy",
            fix_guidance=(
                "Configure Google Tag Manager or gtag.js to send consent mode signals: "
                "(1) set default consent state to 'denied' for analytics_storage and "
                "ad_storage for EU visitors, (2) update consent state when the user "
                "accepts, (3) enable consent mode v2 so GA4 collects modeled data "
                "without cookies when consent is denied."
            ),
            examples=[
                {
                    "violation": "GA4 is configured without consent mode. For EU visitors who reject cookies, no analytics data is collected at all.",
                    "correction": "GTM fires with consent mode defaults: analytics_storage='denied', ad_storage='denied'. When user accepts, consent is updated to 'granted'. GA4 uses modeled conversions for denied sessions.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CCPA DO-NOT-SELL
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_ccpa_001",
            pack="analytics",
            category="do_not_sell",
            description=(
                "Analytics and tracking systems must respect CCPA do-not-sell signals, "
                "including the Global Privacy Control (GPC) browser header, for "
                "California visitors."
            ),
            check_function_name="check_ccpa_do_not_sell_signal",
            severity="violation",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=["US", "US-CA"],
            applicable_industries=[],
            regulatory_source="CCPA / CPRA (Cal. Civ. Code 1798.135) / GPC specification",
            fix_guidance=(
                "Detect the GPC header (Sec-GPC: 1) and treat it as a valid opt-out "
                "of sale/sharing. When GPC is detected: (1) suppress third-party "
                "tracking pixels (Meta Pixel, Google Ads tag), (2) set GA4 ad_storage "
                "to 'denied', (3) do not add the user to remarketing audiences. "
                "Also honor manual opt-out via the 'Do Not Sell' page link."
            ),
            examples=[
                {
                    "violation": "A California visitor with GPC enabled still has Meta Pixel, Google Ads tag, and all third-party trackers firing.",
                    "correction": "Server detects Sec-GPC: 1, suppresses all third-party marketing tags, sets GA4 consent mode to deny ad_storage, and logs the opt-out.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # DATA RETENTION
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_retention_001",
            pack="analytics",
            category="data_retention",
            description=(
                "Analytics data retention periods must be configured appropriately. "
                "GA4 defaults to 14 months for user-level data. GDPR compliance may "
                "require shorter periods. Indefinite retention is not acceptable."
            ),
            check_function_name="check_data_retention_period",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="GDPR Art. 5(1)(e) (Storage Limitation)",
            fix_guidance=(
                "Review and configure data retention settings in GA4 (Admin > Data "
                "Settings > Data Retention). Choose 2 months for maximum GDPR safety, "
                "or 14 months if longer analysis is needed and justified. Document "
                "the retention period in your privacy policy and ROPA."
            ),
            examples=[
                {
                    "violation": "GA4 data retention is set to 14 months with no documented justification, and the privacy policy states 'data is retained indefinitely.'",
                    "correction": "GA4 data retention set to 14 months. Privacy policy states: 'Analytics data is retained for 14 months to analyze trends and improve user experience. Aggregated, non-personal reports may be retained longer.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # PII HANDLING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_pii_001",
            pack="analytics",
            category="pii_handling",
            description=(
                "Personally identifiable information (PII) must not be sent to "
                "analytics platforms. Email addresses, phone numbers, full names, "
                "and other PII must be excluded from GA4 events, custom dimensions, "
                "and page URLs."
            ),
            check_function_name="check_no_pii_in_analytics",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Analytics Terms of Service (Section 7) / GDPR Art. 5(1)(c) (Data Minimization)",
            fix_guidance=(
                "Audit all GA4 events, parameters, and custom dimensions for PII. "
                "Check page URLs and query strings for exposed email/phone/name data. "
                "Remove PII from: (1) event parameters, (2) user properties, "
                "(3) URL query strings (redact or hash before sending to GA4), "
                "(4) page titles that include user names."
            ),
            examples=[
                {
                    "violation": "A form submission event sends event parameter 'user_email' with the full email address to GA4.",
                    "correction": "Form submission event sends 'form_name=contact' and 'form_location=homepage' but does NOT include email, phone, or name in any parameter.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # IP ANONYMIZATION
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_ip_001",
            pack="analytics",
            category="ip_anonymization",
            description=(
                "IP addresses must be anonymized in analytics. GA4 does this by "
                "default, but other analytics tools may require manual configuration. "
                "Full IP address storage is prohibited in the EU."
            ),
            check_function_name="check_ip_anonymization",
            severity="violation",
            applicable_content_types=["website_page", "landing_page", "blog_post"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 5(1)(c) (Data Minimization) / CJEU ruling on IP as personal data",
            fix_guidance=(
                "GA4 anonymizes IP by default -- verify this is not overridden. For "
                "other analytics tools (Matomo, Plausible, Mixpanel, Hotjar), enable "
                "IP anonymization in settings. For self-hosted analytics, truncate the "
                "last octet of IPv4 or last 80 bits of IPv6 before storage."
            ),
            examples=[
                {
                    "violation": "A self-hosted Matomo instance stores full IP addresses (192.168.1.100) for EU visitors.",
                    "correction": "Matomo configured with 'Anonymize Visitors' IP: last 2 bytes masked (192.168.0.0). Or use Matomo's built-in 'Anonymize IP' plugin.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # THIRD-PARTY TRACKING DISCLOSURE
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_disclosure_001",
            pack="analytics",
            category="tracking_disclosure",
            description=(
                "All third-party trackers (analytics, advertising, social media "
                "pixels) must be disclosed in the privacy policy. Users must know "
                "what data is collected and by whom."
            ),
            check_function_name="check_third_party_tracker_disclosure",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="GDPR Art. 13(1)(e) / CCPA / ePrivacy Directive",
            fix_guidance=(
                "Audit all third-party scripts loaded on the site (use browser dev "
                "tools or a scanner like BuiltWith). List each tracker in the privacy "
                "policy with: (1) the provider name, (2) the purpose (analytics, "
                "advertising, functionality), (3) what data is collected, (4) a link "
                "to the third party's privacy policy."
            ),
            examples=[
                {
                    "violation": "Site loads GA4, Meta Pixel, Hotjar, and LinkedIn Insight Tag, but the privacy policy only mentions 'we use cookies to improve your experience.'",
                    "correction": "Privacy policy lists: 'Google Analytics 4 (analytics, page views and events), Meta Pixel (advertising, conversion tracking), Hotjar (analytics, session recordings), LinkedIn Insight Tag (advertising, audience matching)' with links to each provider's privacy policy.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # SERVER-SIDE TRACKING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_serverside_001",
            pack="analytics",
            category="server_side_tracking",
            description=(
                "Server-side tracking setups (server-side GTM, CAPI, Conversions API) "
                "still require user consent. Server-side tracking does not bypass "
                "GDPR/ePrivacy consent requirements."
            ),
            check_function_name="check_server_side_tracking_consent",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) / ePrivacy Directive Art. 5(3) / DPA guidance on server-side tracking",
            fix_guidance=(
                "Pass the user's consent state to the server-side container. Only "
                "fire marketing/analytics tags server-side when the user has consented "
                "client-side. Integrate the CMP's consent signal with your server-side "
                "GTM or CAPI implementation. Log consent proof alongside server-side "
                "events."
            ),
            examples=[
                {
                    "violation": "Server-side GTM container fires all tags regardless of user consent because 'the user's browser doesn't set the cookies anyway.'",
                    "correction": "CMP consent signal is forwarded to server-side GTM via a consent parameter. Server-side tags only fire when consent_status='granted' for the relevant category.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CROSS-DEVICE TRACKING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_crossdevice_001",
            pack="analytics",
            category="cross_device_tracking",
            description=(
                "Cross-device user identification (linking a user's activity across "
                "mobile, desktop, and tablet) requires additional consent beyond "
                "basic analytics consent. Users must be informed about cross-device "
                "tracking."
            ),
            check_function_name="check_cross_device_tracking_consent",
            severity="warning",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) / ePrivacy Directive / EDPB guidelines on tracking",
            fix_guidance=(
                "If using GA4 User-ID, CRM-based matching, or device graph services "
                "to link users across devices: (1) disclose cross-device tracking in "
                "the privacy policy, (2) obtain specific consent for cross-device "
                "identification (not just generic analytics consent), (3) allow users "
                "to opt out of cross-device tracking independently."
            ),
            examples=[
                {
                    "violation": "GA4 User-ID is set using the logged-in user's email hash, linking their mobile and desktop sessions, without any disclosure in the privacy policy.",
                    "correction": "Privacy policy discloses: 'When you log in, we link your activity across devices to provide a personalized experience.' CMP includes a 'Cross-device analytics' toggle under advanced preferences.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # REMARKETING AUDIENCES
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_remarketing_001",
            pack="analytics",
            category="remarketing",
            description=(
                "Adding users to remarketing or retargeting audiences requires "
                "specific consent for advertising/marketing cookies. Users who only "
                "consent to analytics may not be added to remarketing lists."
            ),
            check_function_name="check_remarketing_audience_consent",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) / ePrivacy Directive / Google EU User Consent Policy",
            fix_guidance=(
                "Separate analytics consent from advertising/marketing consent in your "
                "CMP. Only fire remarketing tags (Google Ads, Meta Pixel, LinkedIn "
                "Insight Tag) when the user has explicitly accepted 'Marketing' or "
                "'Advertising' cookies. Use GA4 consent mode with ad_storage='denied' "
                "as the default for EU visitors."
            ),
            examples=[
                {
                    "violation": "A user accepts 'Analytics' cookies only, but the Meta Pixel fires anyway and adds them to a remarketing audience.",
                    "correction": "CMP separates 'Analytics' and 'Marketing' consent. Meta Pixel only fires when 'Marketing' consent is granted. GA4 ad_storage defaults to 'denied' and updates only when marketing consent is given.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # ANALYTICS DATA SHARING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_sharing_001",
            pack="analytics",
            category="data_sharing",
            description=(
                "GA4 data sharing settings (Google Signals, Google Ads linking, "
                "benchmarking) should be reviewed and configured to match the "
                "organization's privacy commitments and consent mechanisms."
            ),
            check_function_name="check_analytics_data_sharing_settings",
            severity="recommendation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="Google Analytics Terms of Service / GDPR Art. 5(1)(b) (Purpose Limitation)",
            fix_guidance=(
                "Review GA4 data sharing settings (Admin > Account > Account Settings): "
                "(1) Google Signals -- only enable if you have advertising consent and "
                "disclose cross-device tracking, (2) Ads Personalization -- disable for "
                "EU properties unless ad consent is obtained, (3) Benchmarking -- "
                "optional, review data shared. Document these settings."
            ),
            examples=[
                {
                    "violation": "Google Signals is enabled on a GA4 property serving EU users, but the CMP does not collect advertising consent and the privacy policy does not mention cross-device tracking.",
                    "correction": "Google Signals disabled for EU property (or enabled only when ad consent is granted via consent mode). Privacy policy updated to reflect data sharing with Google for personalization.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CHILD PRIVACY IN ANALYTICS
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="analytics_children_001",
            pack="analytics",
            category="child_privacy",
            description=(
                "Websites directed at children under 13 (COPPA) or under 16 (GDPR) "
                "must not use analytics or tracking tools that collect personal data "
                "from minors without verifiable parental consent."
            ),
            check_function_name="check_child_analytics_restrictions",
            severity="violation",
            applicable_content_types=["website_page", "landing_page"],
            applicable_regions=[],
            applicable_industries=["education", "children", "toys", "gaming"],
            regulatory_source="COPPA (15 U.S.C. 6501-6506) / GDPR Art. 8",
            fix_guidance=(
                "For sites directed at children: (1) do not use GA4 with default "
                "settings (it collects device identifiers), (2) use privacy-focused "
                "analytics (Plausible, Fathom) that do not use cookies or collect PII, "
                "(3) if using GA4, enable COPPA-compliant settings and disable all "
                "advertising features, (4) implement age-gating before any tracking."
            ),
            examples=[
                {
                    "violation": "A children's educational game site runs GA4 with Google Signals, Hotjar session recordings, and Meta Pixel without age verification or parental consent.",
                    "correction": "Site uses Plausible Analytics (cookieless, no PII). GA4 with COPPA setting enabled if needed. Hotjar and Meta Pixel removed entirely. No advertising tracking.",
                }
            ],
        ),
    ]

    return PolicyPack(
        pack_name="analytics",
        description=(
            "Compliance rules for analytics and tracking systems covering "
            "GDPR cookie consent, GA4 consent mode, CCPA do-not-sell signals, "
            "data retention, PII handling, IP anonymization, third-party "
            "tracking disclosure, server-side tracking, cross-device tracking, "
            "and remarketing audience consent."
        ),
        rules=rules,
    )

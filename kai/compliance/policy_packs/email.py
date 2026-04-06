"""Email marketing policy pack for the Kai compliance engine.

Covers CAN-SPAM (US), GDPR (EU), CCPA (California), CASL (Canada),
double opt-in requirements, and transactional vs. marketing classification.
"""

from __future__ import annotations

from .base import PolicyPack, PolicyRule


def build_email_policy_pack() -> PolicyPack:
    """Construct and return the email policy pack (18 rules)."""

    rules = [
        # ---------------------------------------------------------------
        # CAN-SPAM (US)
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_canspam_001",
            pack="email",
            category="can_spam",
            description=(
                "Every commercial email must include a valid physical postal address "
                "of the sender. A P.O. Box or registered commercial mail-receiving "
                "agency address is acceptable."
            ),
            check_function_name="check_physical_address_present",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(5)(A))",
            fix_guidance=(
                "Add the sender's physical postal address to the email footer. "
                "This can be a street address, P.O. Box, or a private mailbox "
                "registered with a commercial mail-receiving agency (CMRA). The "
                "address must be current and valid."
            ),
            examples=[
                {
                    "violation": "A marketing email with no physical address anywhere in the message.",
                    "correction": "Email footer: 'Acme Corp, 123 Main St, Suite 400, San Francisco, CA 94105'",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_canspam_002",
            pack="email",
            category="can_spam",
            description=(
                "Every commercial email must include a clear, conspicuous, and "
                "functioning unsubscribe mechanism. The opt-out must be easy to "
                "find and use."
            ),
            check_function_name="check_unsubscribe_link",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(3))",
            fix_guidance=(
                "Include a clearly labeled 'Unsubscribe' link in the email footer. "
                "The link must work for at least 30 days after the email is sent. "
                "Do not require the recipient to log in, pay a fee, or provide "
                "information beyond their email address to unsubscribe."
            ),
            examples=[
                {
                    "violation": "An unsubscribe link that requires logging into an account and navigating to email preferences.",
                    "correction": "A single-click 'Unsubscribe' link in the footer that immediately removes the recipient from the list.",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_canspam_003",
            pack="email",
            category="can_spam",
            description=(
                "Unsubscribe requests must be honored within 10 business days. "
                "The sender must not send additional marketing emails after the "
                "opt-out is processed."
            ),
            check_function_name="check_unsubscribe_honor_period",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(4))",
            fix_guidance=(
                "Configure the email platform to process unsubscribe requests "
                "immediately (most platforms do this automatically). Verify that "
                "no marketing emails are sent to unsubscribed addresses. Audit "
                "compliance monthly. Never sell or transfer unsubscribed email "
                "addresses to another entity for marketing."
            ),
            examples=[
                {
                    "violation": "A customer unsubscribes but continues receiving promotional emails for 3 weeks.",
                    "correction": "Unsubscribe processed immediately; confirmation page shown; no further marketing emails sent.",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_canspam_004",
            pack="email",
            category="can_spam",
            description=(
                "Email subject lines must accurately reflect the content of the "
                "message. Deceptive or misleading subject lines are illegal under "
                "CAN-SPAM."
            ),
            check_function_name="check_subject_line_accuracy",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(2))",
            fix_guidance=(
                "Ensure the subject line honestly represents the email content. "
                "Do not use 'Re:' or 'Fwd:' to imply an ongoing conversation. "
                "Do not use 'urgent' or 'action required' for marketing emails. "
                "Do not impersonate another person or brand in the subject."
            ),
            examples=[
                {
                    "violation": "Subject: 'Re: Your account statement' for a promotional email about a new product.",
                    "correction": "Subject: 'New from Acme: 3 tools to simplify your workflow'",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_canspam_005",
            pack="email",
            category="can_spam",
            description=(
                "The 'From' name and email address must accurately identify the "
                "sender. Spoofed or misleading sender information is illegal."
            ),
            check_function_name="check_from_name_accuracy",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(1))",
            fix_guidance=(
                "Use a 'From' name that identifies the business (e.g., 'Acme Corp' "
                "or 'Sarah from Acme'). Use a reply-to domain you own. Do not "
                "impersonate another company or person. Do not use a no-reply address "
                "as the visible From name."
            ),
            examples=[
                {
                    "violation": "From: 'Account Security Team <noreply@random-domain.xyz>' for a marketing email.",
                    "correction": "From: 'Acme Marketing <updates@acmecorp.com>'",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_canspam_006",
            pack="email",
            category="can_spam",
            description=(
                "Commercial emails must clearly identify themselves as advertisements "
                "if the recipient has not previously consented to receive marketing."
            ),
            check_function_name="check_ad_identification",
            severity="warning",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US"],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act (15 U.S.C. 7704(a)(5)(A)(iii))",
            fix_guidance=(
                "If the email is sent to recipients who have not opted in, include "
                "a clear statement that the message is an advertisement. This can be "
                "in the header or footer. Opt-in subscribers who explicitly consented "
                "to marketing emails may not need this label."
            ),
            examples=[
                {
                    "violation": "A cold marketing email with no indication that it is an advertisement.",
                    "correction": "Footer includes: 'This is a commercial message from Acme Corp.' along with unsubscribe link and physical address.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # GDPR (EU)
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_gdpr_001",
            pack="email",
            category="gdpr",
            description=(
                "Marketing emails to EU residents require explicit, freely given, "
                "specific, and informed consent before the first email is sent. "
                "Pre-checked opt-in boxes are not valid consent."
            ),
            check_function_name="check_gdpr_explicit_consent",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 6(1)(a) and Art. 7",
            fix_guidance=(
                "Implement a clear opt-in mechanism: (1) use an unchecked checkbox "
                "with specific language about what the user is consenting to, "
                "(2) do not bundle marketing consent with terms-of-service acceptance, "
                "(3) record the timestamp, IP address, and consent text for audit, "
                "(4) make it easy to withdraw consent at any time."
            ),
            examples=[
                {
                    "violation": "A sign-up form with a pre-checked 'Send me marketing emails' box that is bundled with the terms of service agreement.",
                    "correction": "A separate, unchecked checkbox: 'Yes, I want to receive marketing emails about [specific topics] from [Company]. I can unsubscribe at any time.'",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_gdpr_002",
            pack="email",
            category="gdpr",
            description=(
                "GDPR grants the right to erasure. When a data subject requests "
                "deletion, the organization must remove them from all marketing lists "
                "and delete their personal data within 30 days."
            ),
            check_function_name="check_gdpr_right_to_erasure",
            severity="violation",
            applicable_content_types=["email_marketing", "email_transactional"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 17 (Right to Erasure)",
            fix_guidance=(
                "Implement a process to: (1) receive and log erasure requests, "
                "(2) delete the subscriber from all marketing lists and databases "
                "within 30 days, (3) confirm deletion to the requester, (4) retain "
                "only the minimum data needed to prevent re-contact (e.g., a hashed "
                "email on a suppression list)."
            ),
            examples=[
                {
                    "violation": "A subscriber requests deletion, but their email remains in the CRM and they continue receiving newsletters.",
                    "correction": "Upon receiving erasure request: email deleted from all lists within 72 hours, confirmation sent, hashed email added to suppression list to prevent re-addition.",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_gdpr_003",
            pack="email",
            category="gdpr",
            description=(
                "Organizations must maintain records of data processing activities "
                "for email marketing, including what data is collected, the legal "
                "basis, and retention periods."
            ),
            check_function_name="check_gdpr_processing_records",
            severity="warning",
            applicable_content_types=["email_marketing"],
            applicable_regions=["EU", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE", "PL", "IE", "PT", "DK", "FI", "CZ", "RO", "HU", "BG", "HR", "SK", "SI", "LT", "LV", "EE", "CY", "LU", "MT", "GR", "GB"],
            applicable_industries=[],
            regulatory_source="GDPR Art. 30 (Records of Processing Activities)",
            fix_guidance=(
                "Maintain a Record of Processing Activities (ROPA) for email marketing "
                "that documents: (1) purpose of processing, (2) categories of data "
                "subjects and data, (3) recipients of the data, (4) retention periods, "
                "(5) technical and organizational security measures."
            ),
            examples=[
                {
                    "violation": "No documentation exists describing how subscriber data is collected, processed, stored, or shared.",
                    "correction": "A ROPA entry: 'Email Marketing - Purpose: send product updates to opted-in subscribers. Data: email, name, consent timestamp. Retention: until unsubscribe + 30 days. Shared with: ESP (Loops). Security: encrypted in transit and at rest.'",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CCPA (California)
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_ccpa_001",
            pack="email",
            category="ccpa",
            description=(
                "Email marketing operations must honor CCPA opt-out-of-sale requests. "
                "If subscriber data is sold or shared for cross-context behavioral "
                "advertising, a 'Do Not Sell' mechanism must be available."
            ),
            check_function_name="check_ccpa_opt_out_sale",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US", "US-CA"],
            applicable_industries=[],
            regulatory_source="CCPA / CPRA (Cal. Civ. Code 1798.120)",
            fix_guidance=(
                "If subscriber email data is shared with third parties for advertising: "
                "(1) include a 'Do Not Sell or Share My Personal Information' link in "
                "the email footer or on the preference center, (2) honor opt-out "
                "requests within 15 business days, (3) honor the Global Privacy "
                "Control (GPC) signal."
            ),
            examples=[
                {
                    "violation": "Subscriber data is shared with ad partners for retargeting, but no opt-out mechanism is offered.",
                    "correction": "Email preference center includes a 'Do Not Sell or Share My Data' toggle. When activated, subscriber data is excluded from third-party sharing within 15 business days.",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_ccpa_002",
            pack="email",
            category="ccpa",
            description=(
                "At the point of email collection, a privacy notice must be provided "
                "to California residents disclosing what personal information is "
                "collected and for what purpose."
            ),
            check_function_name="check_ccpa_privacy_notice_at_collection",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["US", "US-CA"],
            applicable_industries=[],
            regulatory_source="CCPA / CPRA (Cal. Civ. Code 1798.100(b))",
            fix_guidance=(
                "At every point where email addresses are collected (forms, checkout, "
                "pop-ups), display or link to a notice that: (1) lists categories of "
                "personal information collected, (2) states the purpose of collection, "
                "(3) indicates whether the data is sold or shared, (4) states the "
                "retention period."
            ),
            examples=[
                {
                    "violation": "An email sign-up form with no privacy notice and no link to a privacy policy.",
                    "correction": "Below the form: 'We collect your email to send marketing updates. We do not sell your data. See our Privacy Policy for details.' with a link to the full policy.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # CASL (Canada)
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_casl_001",
            pack="email",
            category="casl",
            description=(
                "CASL requires express consent (opt-in) before sending commercial "
                "electronic messages to Canadian recipients. Implied consent is "
                "allowed only in limited circumstances and is time-bound."
            ),
            check_function_name="check_casl_express_consent",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["CA"],
            applicable_industries=[],
            regulatory_source="CASL (S.C. 2010, c. 23, s. 6)",
            fix_guidance=(
                "Obtain express opt-in consent before sending marketing emails to "
                "Canadian addresses. The consent request must state: (1) the purpose, "
                "(2) the sender's identity, (3) contact information. Implied consent "
                "is valid for 2 years after a purchase and 6 months after an inquiry, "
                "but express consent should be sought to convert implied to express."
            ),
            examples=[
                {
                    "violation": "Adding all Canadian trade show attendees to the marketing list without consent.",
                    "correction": "After the trade show, send a single consent-request email explaining who you are and asking them to opt in. Only add those who explicitly consent.",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_casl_002",
            pack="email",
            category="casl",
            description=(
                "CASL requires sender identification and contact information in every "
                "commercial electronic message: name, mailing address, and at least "
                "one of phone, email, or web address."
            ),
            check_function_name="check_casl_sender_identification",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["CA"],
            applicable_industries=[],
            regulatory_source="CASL (S.C. 2010, c. 23, s. 6(2))",
            fix_guidance=(
                "Include in every email: (1) the name of the person or organization "
                "sending the message, (2) the name of the person on whose behalf it "
                "is sent (if different), (3) mailing address, (4) at least one of: "
                "phone number, email address, or web URL. Contact information must "
                "remain valid for 60 days after sending."
            ),
            examples=[
                {
                    "violation": "A marketing email to Canadian recipients with only a company name and unsubscribe link -- no address or phone/email.",
                    "correction": "Footer: 'Sent by Acme Corp, 456 King St W, Toronto, ON M5V 1K4 | info@acmecorp.ca | (416) 555-0199 | Unsubscribe'",
                }
            ],
        ),
        PolicyRule(
            rule_id="email_casl_003",
            pack="email",
            category="casl",
            description=(
                "CASL requires a functioning unsubscribe mechanism in every commercial "
                "electronic message. The mechanism must remain active for at least "
                "60 days after the message is sent."
            ),
            check_function_name="check_casl_unsubscribe_mechanism",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["CA"],
            applicable_industries=[],
            regulatory_source="CASL (S.C. 2010, c. 23, s. 6(2)(c))",
            fix_guidance=(
                "Include a clear unsubscribe mechanism in every email. The unsubscribe "
                "link must work for at least 60 days after the email is sent. Honor "
                "unsubscribe requests within 10 business days. The unsubscribe process "
                "must be free and must not require information beyond identification."
            ),
            examples=[
                {
                    "violation": "An unsubscribe link that expires after 7 days or returns a 404 error.",
                    "correction": "A persistent 'Unsubscribe' link that processes immediately, confirms the action, and remains functional for at least 60 days.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # DOUBLE OPT-IN
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_optin_001",
            pack="email",
            category="double_opt_in",
            description=(
                "Double opt-in (confirmation email) is legally required in Germany "
                "and strongly recommended in all EU/EEA countries for GDPR compliance. "
                "It provides the strongest proof of consent."
            ),
            check_function_name="check_double_opt_in",
            severity="violation",
            applicable_content_types=["email_marketing"],
            applicable_regions=["DE"],
            applicable_industries=[],
            regulatory_source="German Federal Court of Justice (BGH) rulings on UWG / GDPR Art. 7",
            fix_guidance=(
                "Implement double opt-in: (1) after form submission, send a confirmation "
                "email with a unique link, (2) do NOT send marketing emails until the "
                "link is clicked, (3) record the confirmation timestamp and IP for audit. "
                "Set a 48-hour expiry on the confirmation link."
            ),
            examples=[
                {
                    "violation": "A German subscriber signs up and immediately starts receiving weekly newsletters without confirming their email.",
                    "correction": "After sign-up: 'Please confirm your subscription by clicking the link in the email we just sent.' Marketing emails begin only after confirmation.",
                }
            ],
        ),

        # ---------------------------------------------------------------
        # TRANSACTIONAL vs MARKETING
        # ---------------------------------------------------------------
        PolicyRule(
            rule_id="email_classification_001",
            pack="email",
            category="email_classification",
            description=(
                "Emails must be correctly classified as transactional or marketing. "
                "Transactional emails (order confirmations, shipping updates) do not "
                "require marketing consent but must not contain substantial marketing "
                "content."
            ),
            check_function_name="check_email_classification",
            severity="warning",
            applicable_content_types=["email_marketing", "email_transactional"],
            applicable_regions=[],
            applicable_industries=[],
            regulatory_source="CAN-SPAM Act / GDPR / CASL",
            fix_guidance=(
                "Review each email template to confirm correct classification. "
                "Transactional emails may include a small, incidental mention of "
                "related products (e.g., 'You might also like...') but the PRIMARY "
                "purpose must be transactional. If marketing content is the main focus, "
                "reclassify as marketing and ensure proper consent exists."
            ),
            examples=[
                {
                    "violation": "An order confirmation email where 70% of the content is product promotions and sales offers.",
                    "correction": "Order confirmation email: 90% transaction details (order summary, shipping info, tracking link), plus a small 'Recommended for you' section limited to 2-3 product suggestions at the bottom.",
                }
            ],
        ),
    ]

    return PolicyPack(
        pack_name="email",
        description=(
            "Compliance rules for email marketing covering CAN-SPAM (US), "
            "GDPR (EU), CCPA (California), CASL (Canada), double opt-in "
            "requirements, and transactional vs. marketing classification."
        ),
        rules=rules,
    )

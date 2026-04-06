"""Pre-built email sequence templates organized by business archetype.

Each template defines the emails, timing, merge fields, and content structure
for a common lifecycle marketing scenario.  The sequence builders (Task 055)
consume these templates and produce fully personalised, ready-to-send emails.
"""

from __future__ import annotations

import copy
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Models
# ============================================================================


class SequenceEmailTemplate(BaseModel):
    """A single email within a sequence template."""

    position: int
    delay_days: int
    delay_hours: int = 0
    subject_templates: List[str] = Field(default_factory=list)
    preview_text: Optional[str] = None
    body_structure: List[str] = Field(default_factory=list)
    body_template: str = ""
    cta_text: str = ""
    cta_url_template: Optional[str] = None
    tone: str = "professional"
    goal: str = ""
    notes: Optional[str] = None


class SequenceTemplate(BaseModel):
    """A complete multi-email sequence template for a specific archetype and trigger."""

    id: str
    name: str
    description: str
    archetype: str
    category: str
    trigger: str
    email_count: int
    total_duration_days: int
    emails: List[SequenceEmailTemplate] = Field(default_factory=list)
    merge_fields_required: List[str] = Field(default_factory=list)
    merge_fields_optional: List[str] = Field(default_factory=list)
    frequency_cap: Optional[str] = None
    exclusion_criteria: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# LOCAL-SERVICE Sequences
# ============================================================================

LOCAL_SERVICE_WELCOME = SequenceTemplate(
    id="local_service_welcome",
    name="Local Service Welcome / Inquiry Received",
    description=(
        "Four-email welcome sequence for local-service businesses after a form "
        "submission or phone inquiry.  Confirms receipt, educates on the process, "
        "provides a value-add tip, and requests a review or follows up."
    ),
    archetype="local-service",
    category="welcome",
    trigger="form_submission",
    email_count=4,
    total_duration_days=14,
    merge_fields_required=["first_name", "business_name", "service_type", "phone_number"],
    merge_fields_optional=["operator_name", "business_address", "scheduling_url"],
    frequency_cap="Don't start if contact received email in last 48h",
    exclusion_criteria=[
        "Contact has already booked an appointment",
        "Contact already received this welcome sequence",
    ],
    success_metrics=["booking_rate", "email_open_rate", "reply_rate"],
    emails=[
        # Email 1 -- Inquiry Confirmation (Day 0)
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "{first_name}, we got your {service_type} inquiry",
                "Your {service_type} request is confirmed -- here's what happens next",
            ],
            preview_text="We received your request and here is what to expect.",
            body_structure=["greeting", "confirmation", "what_to_expect", "contact_info", "signature"],
            body_template=(
                "Hi {first_name},\n\n"
                "Thank you for reaching out to {business_name} about {service_type}. "
                "We received your inquiry and wanted to confirm that our team is on it.\n\n"
                "Here is what happens next:\n"
                "1. A member of our team will review your request within one business day.\n"
                "2. We will reach out to schedule a time that works for you.\n"
                "3. You will receive a confirmation with all the details before your appointment.\n\n"
                "If you have any questions before then, you can reach us at {phone_number} during "
                "business hours.  We are here to help.\n\n"
                "Talk soon,\n"
                "{business_name} Team"
            ),
            cta_text="Call us at {phone_number}",
            cta_url_template="tel:{phone_number}",
            tone="warm",
            goal="Confirm receipt, set expectations, provide contact info",
        ),
        # Email 2 -- What to Expect (Day 2)
        SequenceEmailTemplate(
            position=2,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "Here's how our {service_type} process works",
                "What to expect from your {service_type} appointment",
            ],
            preview_text="A quick overview of the process so you know exactly what to expect.",
            body_structure=["greeting", "process_overview", "timeline", "what_to_prepare", "trust_signals", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We know that scheduling {service_type} can feel like a lot, so we put together "
                "a quick overview of how the process works at {business_name}.\n\n"
                "Step 1: We assess your needs and provide a clear, upfront quote with no hidden fees.\n"
                "Step 2: We schedule a time that fits your calendar.\n"
                "Step 3: Our team arrives on time, completes the work, and walks you through everything.\n"
                "Step 4: We follow up to make sure you are 100% satisfied.\n\n"
                "Our customers trust us because we have been serving the community for years, "
                "and we stand behind every job.\n\n"
                "Have a question? Just reply to this email or call {phone_number}.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Questions? Call {phone_number}",
            cta_url_template="tel:{phone_number}",
            tone="educational",
            goal="Educate on process, reduce anxiety, build trust",
        ),
        # Email 3 -- Value-Add Tip (Day 7)
        SequenceEmailTemplate(
            position=3,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "Quick {service_type} tip from our team",
                "{first_name}, a helpful {service_type} tip just for you",
            ],
            preview_text="A tip from our team that can save you time and money.",
            body_structure=["greeting", "tip", "why_it_matters", "kaicalls_mention", "soft_cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Here is a quick tip from our {service_type} team that most people don't know:\n\n"
                "Regular maintenance on your {service_type} can extend its lifespan by up to 30% "
                "and prevent costly emergency repairs.  A simple annual check-up catches small "
                "issues before they become big problems.\n\n"
                "At {business_name}, we see this all the time -- a $150 maintenance visit today "
                "can save $1,500 in repairs down the road.\n\n"
                "Need to reach us after hours? Our team is available around the clock "
                "at {phone_number} to answer questions or schedule your service.\n\n"
                "Ready to get started? Reply to this email or call {phone_number}.\n\n"
                "Cheers,\n"
                "{business_name} Team"
            ),
            cta_text="Ready to get started? Reply or call {phone_number}",
            cta_url_template="tel:{phone_number}",
            tone="helpful",
            goal="Provide value, demonstrate expertise, stay top of mind",
            notes="Mention KaiCalls number if business uses AI receptionist for after-hours calls.",
        ),
        # Email 4 -- Review Request / Follow-Up (Day 14)
        SequenceEmailTemplate(
            position=4,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "How was your experience with {business_name}?",
                "{first_name}, we'd love your feedback",
            ],
            preview_text="Let us know how we did -- it takes less than 2 minutes.",
            body_structure=["greeting", "thank_you_or_check_in", "review_request", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "If your {service_type} is complete, we would love to hear how it went. "
                "A quick review helps other homeowners in our area find reliable "
                "{service_type} providers -- and it means a lot to our team.\n\n"
                "It takes about 2 minutes:\n"
                "{review_link}\n\n"
                "If your appointment hasn't happened yet, no worries. "
                "You can schedule your service at {scheduling_url} or call us at {phone_number}.\n\n"
                "Thank you for choosing {business_name}.\n\n"
                "Warm regards,\n"
                "{business_name} Team"
            ),
            cta_text="Leave us a review",
            cta_url_template="{review_link}",
            tone="grateful",
            goal="Get review if service done, or follow up if still pending",
        ),
    ],
)


LOCAL_SERVICE_POST_JOB = SequenceTemplate(
    id="local_service_post_job",
    name="Local Service Post-Job Follow-Up",
    description=(
        "Four-email post-service sequence: thank you, review request, "
        "referral ask, and seasonal maintenance reminder spread over 90 days."
    ),
    archetype="local-service",
    category="post_purchase",
    trigger="service_completed",
    email_count=4,
    total_duration_days=90,
    merge_fields_required=["first_name", "business_name", "service_type", "service_date"],
    merge_fields_optional=["review_link", "referral_offer", "next_service_type", "scheduling_url", "referral_link", "phone_number"],
    frequency_cap="Don't start if contact received email in last 48h",
    exclusion_criteria=[
        "Contact filed a complaint about the service",
        "Contact already left a review (skip email 2)",
    ],
    success_metrics=["review_left_rate", "referral_rate", "repeat_booking_rate"],
    emails=[
        # Email 1 -- Thank You (Day 1)
        SequenceEmailTemplate(
            position=1,
            delay_days=1,
            delay_hours=0,
            subject_templates=[
                "Thank you for choosing {business_name}",
                "{first_name}, thanks for trusting us with your {service_type}",
            ],
            preview_text="We appreciate your business and want to make sure everything is great.",
            body_structure=["greeting", "thank_you", "satisfaction_check", "issue_channel", "signature"],
            body_template=(
                "Hi {first_name},\n\n"
                "Thank you for choosing {business_name} for your {service_type} on {service_date}. "
                "We truly appreciate your trust and hope everything exceeded your expectations.\n\n"
                "If something is not quite right, please reply to this email and we will "
                "make it right. Your satisfaction is the only outcome we accept.\n\n"
                "Thanks again,\n"
                "{business_name} Team"
            ),
            cta_text="Had any issues? Reply to this email -- we'll make it right.",
            cta_url_template=None,
            tone="warm",
            goal="Express gratitude, ensure satisfaction, open channel for issues",
        ),
        # Email 2 -- Review Request (Day 3)
        SequenceEmailTemplate(
            position=2,
            delay_days=3,
            delay_hours=0,
            subject_templates=[
                "A quick favor, {first_name}?",
                "How did we do on your {service_type}?",
            ],
            preview_text="A 2-minute review helps other homeowners find trustworthy service.",
            body_structure=["greeting", "review_ask", "why_reviews_matter", "direct_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We have a small favor to ask. If you were happy with our {service_type}, "
                "would you take 2 minutes to leave us a review?\n\n"
                "Honest reviews help other homeowners in our area find reliable "
                "{service_type} providers. It makes a real difference for a local business "
                "like ours.\n\n"
                "Here is the link:\n"
                "{review_link}\n\n"
                "Thank you -- we read every review and appreciate the feedback.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Leave a review",
            cta_url_template="{review_link}",
            tone="appreciative",
            goal="Get a review on Google/Yelp",
        ),
        # Email 3 -- Referral Ask (Day 14)
        SequenceEmailTemplate(
            position=3,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "Know someone who needs {service_type}?",
                "{first_name}, spread the word and earn {referral_offer}",
            ],
            preview_text="Know someone who could use our help? We would love an introduction.",
            body_structure=["greeting", "referral_ask", "incentive", "how_to_refer", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "If you know a friend, neighbor, or family member who needs {service_type}, "
                "we would love an introduction.\n\n"
                "As a thank-you, we are offering {referral_offer} for every referral who "
                "books a service. Just forward this email or reply with their name and "
                "phone number -- we will take care of the rest.\n\n"
                "{referral_link}\n\n"
                "Thank you for spreading the word.\n\n"
                "Cheers,\n"
                "{business_name} Team"
            ),
            cta_text="Refer a friend",
            cta_url_template="{referral_link}",
            tone="friendly",
            goal="Generate referrals",
        ),
        # Email 4 -- Seasonal/Maintenance Reminder (Day 90)
        SequenceEmailTemplate(
            position=4,
            delay_days=90,
            delay_hours=0,
            subject_templates=[
                "Time for a {service_type} check-up?",
                "{first_name}, it's been 3 months -- is everything still running well?",
            ],
            preview_text="A quick check-up now can save you from costly repairs later.",
            body_structure=["greeting", "seasonal_relevance", "maintenance_importance", "returning_offer", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "It has been about 3 months since your last {service_type} on {service_date}. "
                "Depending on your setup, it may be time for a maintenance check-up.\n\n"
                "Regular maintenance keeps everything running smoothly and helps you avoid "
                "surprise repairs. As a returning customer, we would like to offer you "
                "priority scheduling and a special rate.\n\n"
                "Book your check-up here:\n"
                "{scheduling_url}\n\n"
                "Or call us at {phone_number}.\n\n"
                "Looking forward to seeing you again,\n"
                "{business_name} Team"
            ),
            cta_text="Schedule your check-up",
            cta_url_template="{scheduling_url}",
            tone="helpful",
            goal="Drive repeat business",
        ),
    ],
)


LOCAL_SERVICE_QUOTE_FOLLOWUP = SequenceTemplate(
    id="local_service_quote_followup",
    name="Local Service Quote Follow-Up",
    description=(
        "Four-email quote follow-up with escalating urgency: gentle check-in, "
        "value reinforcement, social proof, and last-chance deadline."
    ),
    archetype="local-service",
    category="follow_up",
    trigger="quote_sent",
    email_count=4,
    total_duration_days=10,
    merge_fields_required=["first_name", "business_name", "service_type", "quote_amount", "quote_date"],
    merge_fields_optional=["operator_name", "phone_number", "quote_expiry", "scheduling_url", "customer_name"],
    frequency_cap="Don't start if contact received email in last 24h",
    exclusion_criteria=[
        "Contact has already booked or paid",
        "Contact explicitly declined the quote",
    ],
    success_metrics=["quote_acceptance_rate", "response_rate", "booking_rate"],
    emails=[
        # Email 1 -- Gentle Check-In (Day 2)
        SequenceEmailTemplate(
            position=1,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "Any questions about your {service_type} quote?",
                "{first_name}, following up on your ${quote_amount} estimate",
            ],
            preview_text="Happy to walk you through the details or answer any questions.",
            body_structure=["greeting", "check_in", "offer_to_help", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We sent over your {service_type} quote on {quote_date} and wanted to see "
                "if you had any questions.\n\n"
                "We know there is a lot to consider, and we are happy to walk through the "
                "details or adjust the scope to fit your budget. No pressure at all -- "
                "we just want to make sure you have everything you need to make a decision.\n\n"
                "Reply to this email or call {phone_number} anytime.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Reply with any questions",
            cta_url_template=None,
            tone="helpful",
            goal="Address questions, remove friction",
        ),
        # Email 2 -- Value Reinforcement (Day 5)
        SequenceEmailTemplate(
            position=2,
            delay_days=5,
            delay_hours=0,
            subject_templates=[
                "Why our clients choose {business_name} for {service_type}",
                "What's included in your {service_type} quote",
            ],
            preview_text="A breakdown of exactly what you get and why our clients keep coming back.",
            body_structure=["greeting", "whats_included", "value_explanation", "trust_signals", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We wanted to share a bit more about what is included in your "
                "${quote_amount} {service_type} quote so you can see the full picture.\n\n"
                "Your quote covers:\n"
                "- Complete {service_type} performed by our certified team\n"
                "- All materials and labor included -- no surprise add-ons\n"
                "- A satisfaction guarantee: if the work is not right, we come back at no charge\n"
                "- Post-service follow-up to make sure everything holds up\n\n"
                "We have served hundreds of customers in this area, and we stand behind "
                "every job with our reputation.\n\n"
                "Ready to move ahead? Book your appointment here:\n"
                "{scheduling_url}\n\n"
                "Or call {phone_number} to discuss.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Ready to proceed?",
            cta_url_template="{scheduling_url}",
            tone="professional",
            goal="Reinforce value, differentiate from competitors",
        ),
        # Email 3 -- Social Proof (Day 7)
        SequenceEmailTemplate(
            position=3,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "See what our {service_type} clients say",
                "{first_name}, here's what {customer_name} said about our work",
            ],
            preview_text="Real results from real customers in your area.",
            body_structure=["greeting", "testimonial_intro", "testimonials", "relate_back", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "You are not the only one who has been researching {service_type} options. "
                "Here is what a few recent customers had to say:\n\n"
                "\"Showed up on time, did exactly what they promised, and the price matched "
                "the quote. Refreshing.\" -- Recent {service_type} customer\n\n"
                "\"I got three quotes and {business_name} was the most transparent about "
                "what was included. No hidden fees, no surprises.\" -- Homeowner in your area\n\n"
                "\"The team was professional and cleaned up after themselves. "
                "I have already recommended them to my neighbors.\" -- Repeat customer\n\n"
                "We would love to earn the same kind of feedback from you.\n\n"
                "Ready to get started?\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Join our satisfied customers",
            cta_url_template="{scheduling_url}",
            tone="conversational",
            goal="Build confidence with testimonials",
        ),
        # Email 4 -- Last Chance (Day 10)
        SequenceEmailTemplate(
            position=4,
            delay_days=10,
            delay_hours=0,
            subject_templates=[
                "Your {service_type} quote expires soon",
                "Last chance: your ${quote_amount} estimate for {service_type}",
            ],
            preview_text="Your quote is about to expire -- lock in your price today.",
            body_structure=["greeting", "expiry_reminder", "consequences_of_waiting", "easy_next_step", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Your ${quote_amount} {service_type} quote from {quote_date} is expiring soon. "
                "We wanted to give you a heads-up before it does.\n\n"
                "A few things to keep in mind:\n"
                "- Material costs can change, so we may not be able to hold this price.\n"
                "- Our schedule fills up fast, especially during peak season.\n"
                "- Waiting on {service_type} can lead to bigger (and more expensive) issues.\n\n"
                "Locking in your price is easy -- just reply to this email, book at "
                "{scheduling_url}, or call {phone_number}.\n\n"
                "We hope to work with you, {first_name}.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Confirm your booking",
            cta_url_template="{scheduling_url}",
            tone="urgent",
            goal="Create urgency, get decision",
        ),
    ],
)


LOCAL_SERVICE_SEASONAL = SequenceTemplate(
    id="local_service_seasonal",
    name="Local Service Seasonal Reactivation",
    description=(
        "Three-email seasonal reactivation sequence that nudges previous customers "
        "to book seasonal maintenance before the rush."
    ),
    archetype="local-service",
    category="seasonal",
    trigger="seasonal_calendar",
    email_count=3,
    total_duration_days=14,
    merge_fields_required=["first_name", "business_name", "service_type", "season"],
    merge_fields_optional=["scheduling_url", "phone_number", "seasonal_offer"],
    frequency_cap="Don't start if contact received email in last 72h",
    exclusion_criteria=[
        "Contact already booked seasonal service",
        "Contact opted out of promotional emails",
    ],
    success_metrics=["booking_rate", "open_rate", "revenue_from_reactivation"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "{first_name}, {season} is coming -- is your {service_type} ready?",
                "Prepare for {season}: {service_type} tips from {business_name}",
            ],
            preview_text="Get ahead of the season with a quick maintenance check.",
            body_structure=["greeting", "seasonal_hook", "why_now", "offer", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "{season} is right around the corner, and that means it is time to make sure "
                "your {service_type} is ready to handle the change.\n\n"
                "Every year we see customers who wait until the last minute and end up paying "
                "more for emergency service. A quick maintenance visit now can save you "
                "time, money, and headaches later.\n\n"
                "As a returning customer, you get priority scheduling. Book your spot "
                "before the rush:\n"
                "{scheduling_url}\n\n"
                "Or call us at {phone_number}.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Book your seasonal service",
            cta_url_template="{scheduling_url}",
            tone="timely",
            goal="Drive seasonal bookings before peak demand",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "Spots are filling up for {season} {service_type}",
                "{first_name}, don't get caught off guard this {season}",
            ],
            preview_text="Our schedule is filling up fast -- reserve your spot.",
            body_structure=["greeting", "urgency", "social_proof", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Just a quick heads-up: our {season} schedule is already filling up. "
                "We have limited availability for {service_type} appointments this month.\n\n"
                "Last {season}, customers who booked early avoided the 2-3 week wait that "
                "hit during peak season. We want to make sure you are taken care of.\n\n"
                "Reserve your spot:\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Reserve your spot",
            cta_url_template="{scheduling_url}",
            tone="urgent",
            goal="Create scarcity, drive bookings",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "Last call: {season} {service_type} appointments",
                "{first_name}, this is your final reminder for {season} prep",
            ],
            preview_text="Final reminder before our schedule is fully booked.",
            body_structure=["greeting", "final_reminder", "special_offer", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "This is our last reminder about {season} {service_type} service. "
                "Our schedule is nearly full, and we want to make sure you are covered.\n\n"
                "If you have been putting this off, now is the time. "
                "Book today and you still get returning customer priority:\n"
                "{scheduling_url}\n\n"
                "After this week, wait times will increase significantly.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Book now before we're full",
            cta_url_template="{scheduling_url}",
            tone="urgent",
            goal="Final push for seasonal booking",
        ),
    ],
)


LOCAL_SERVICE_DORMANT = SequenceTemplate(
    id="local_service_dormant",
    name="Local Service Dormant Customer Win-Back",
    description=(
        "Three-email win-back sequence for customers who haven't engaged in 12+ months. "
        "Starts soft, provides value, then offers a returning-customer incentive."
    ),
    archetype="local-service",
    category="reactivation",
    trigger="dormant_threshold",
    email_count=3,
    total_duration_days=25,
    merge_fields_required=["first_name", "business_name", "last_service_type", "last_service_date"],
    merge_fields_optional=["season", "offer", "scheduling_url", "phone_number"],
    frequency_cap="Don't start if contact received email in last 7 days",
    exclusion_criteria=[
        "Contact has opted out of marketing emails",
        "Contact has a pending complaint or refund",
    ],
    success_metrics=["reactivation_rate", "booking_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "{first_name}, it's been a while!",
                "We haven't heard from you, {first_name}",
            ],
            preview_text="We noticed it has been a while since your last visit. We miss you!",
            body_structure=["greeting", "personal_acknowledgment", "we_remember_you", "soft_cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "It has been a while since your last {last_service_type} on "
                "{last_service_date}, and we wanted to check in.\n\n"
                "At {business_name}, we remember every customer -- and we remember you. "
                "We hope everything has been going well.\n\n"
                "If there is anything we can help with, we are just a reply away.\n\n"
                "Warm regards,\n"
                "{business_name} Team"
            ),
            cta_text="Reply if there's anything we can help with",
            cta_url_template=None,
            tone="warm",
            goal="Re-engage, show you remember them",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=10,
            delay_hours=0,
            subject_templates=[
                "A {last_service_type} tip for {season}",
                "{first_name}, here's something useful for your home",
            ],
            preview_text="A quick tip from our team -- no strings attached.",
            body_structure=["greeting", "value_tip", "seasonal_relevance", "soft_cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "With {season} approaching, here is a quick {last_service_type} tip "
                "that can save you time and money:\n\n"
                "Check your system before the season changes. Most common issues "
                "are caused by simple wear that a quick inspection catches early. "
                "Catching it now avoids emergency calls later and keeps costs down.\n\n"
                "If you need a hand, our team is ready to help. No sales pitch -- "
                "just honest advice from people who care about doing good work.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Need a hand? Reply to this email.",
            cta_url_template=None,
            tone="helpful",
            goal="Provide value without asking for anything",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=25,
            delay_hours=0,
            subject_templates=[
                "A special offer just for you, {first_name}",
                "{first_name}, welcome back with {offer}",
            ],
            preview_text="An exclusive returning-customer offer -- limited time only.",
            body_structure=["greeting", "exclusive_offer", "time_limit", "easy_booking", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We would love to welcome you back to {business_name}. As a thank-you "
                "for being a past customer, we are offering you an exclusive deal:\n\n"
                "{offer}\n\n"
                "This offer is valid for the next 14 days. Booking is easy:\n"
                "{scheduling_url}\n\n"
                "Or call {phone_number} and mention this email.\n\n"
                "We look forward to working with you again.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Claim your offer",
            cta_url_template="{scheduling_url}",
            tone="exclusive",
            goal="Incentivize return with exclusive offer",
        ),
    ],
)


# ============================================================================
# ECOMMERCE Sequences
# ============================================================================

ECOMMERCE_WELCOME = SequenceTemplate(
    id="ecommerce_welcome",
    name="Ecommerce Welcome / New Subscriber",
    description=(
        "Four-email welcome series for new email subscribers: welcome offer, "
        "brand story, product highlights, and offer reminder."
    ),
    archetype="ecommerce",
    category="welcome",
    trigger="email_signup",
    email_count=4,
    total_duration_days=7,
    merge_fields_required=["first_name", "business_name", "welcome_offer"],
    merge_fields_optional=["bestseller_1", "bestseller_2", "brand_story_url", "shop_url", "discount_code"],
    frequency_cap="Don't start if contact received email in last 24h",
    exclusion_criteria=[
        "Contact already made a purchase (move to post-purchase sequence instead)",
        "Contact already completed this welcome sequence",
    ],
    success_metrics=["first_purchase_rate", "discount_redemption_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "Welcome to {business_name} -- here's your {welcome_offer}",
                "{first_name}, your {welcome_offer} is waiting inside",
            ],
            preview_text="Your welcome offer is ready to use -- start shopping today.",
            body_structure=["greeting", "welcome", "offer_details", "bestsellers", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Welcome to {business_name}! We are glad to have you.\n\n"
                "To say thanks for signing up, here is your exclusive welcome offer:\n\n"
                "{welcome_offer}\n\n"
                "Use code {discount_code} at checkout.\n\n"
                "Not sure where to start? Our customers love these:\n"
                "- {bestseller_1}\n"
                "- {bestseller_2}\n\n"
                "Start shopping: {shop_url}\n\n"
                "Happy browsing,\n"
                "{business_name} Team"
            ),
            cta_text="Shop now",
            cta_url_template="{shop_url}",
            tone="warm",
            goal="Welcome subscriber and drive first purchase with offer",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "The story behind {business_name}",
                "{first_name}, this is why we started {business_name}",
            ],
            preview_text="We built this because we saw something missing. Here is our story.",
            body_structure=["greeting", "brand_story", "mission", "values", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We started {business_name} because we believed there was a better way.\n\n"
                "Too many products in our space are overpriced, under-delivered, or made "
                "without care. We set out to change that by focusing on quality materials, "
                "fair pricing, and a customer experience worth talking about.\n\n"
                "Every product we make reflects that mission. No shortcuts, no compromises.\n\n"
                "Want to learn more? Read our full story:\n"
                "{brand_story_url}\n\n"
                "Thanks for being part of our journey.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Read our story",
            cta_url_template="{brand_story_url}",
            tone="authentic",
            goal="Build brand connection and trust through storytelling",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=4,
            delay_hours=0,
            subject_templates=[
                "Our bestsellers -- picked by real customers",
                "{first_name}, these are our most-loved products",
            ],
            preview_text="See what our customers are raving about.",
            body_structure=["greeting", "product_highlights", "reviews_snippet", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Here are the products our customers can't stop talking about:\n\n"
                "1. {bestseller_1} -- our top seller for a reason.\n"
                "2. {bestseller_2} -- a customer favourite since day one.\n\n"
                "These are real picks from real people. See why they are so popular:\n"
                "{shop_url}\n\n"
                "And remember, your {welcome_offer} is still active!\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Shop bestsellers",
            cta_url_template="{shop_url}",
            tone="casual",
            goal="Showcase popular products and drive discovery",
        ),
        SequenceEmailTemplate(
            position=4,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "Your {welcome_offer} expires soon, {first_name}",
                "Last chance to use your welcome offer",
            ],
            preview_text="Your welcome discount is about to expire. Don't miss out.",
            body_structure=["greeting", "offer_reminder", "urgency", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Just a heads-up: your {welcome_offer} with code {discount_code} "
                "is expiring soon.\n\n"
                "If you have been browsing but haven't pulled the trigger, now is the time. "
                "This offer won't come around again.\n\n"
                "Use your discount before it's gone:\n"
                "{shop_url}\n\n"
                "See you soon,\n"
                "{business_name} Team"
            ),
            cta_text="Use your discount",
            cta_url_template="{shop_url}",
            tone="urgent",
            goal="Create urgency to redeem first-purchase offer",
        ),
    ],
)


ECOMMERCE_CART_ABANDONMENT = SequenceTemplate(
    id="ecommerce_cart_abandonment",
    name="Ecommerce Cart Abandonment",
    description=(
        "Three-email cart recovery sequence over 48 hours: gentle reminder, "
        "product details with social proof, and last-chance offer."
    ),
    archetype="ecommerce",
    category="cart_abandonment",
    trigger="cart_abandoned",
    email_count=3,
    total_duration_days=2,
    merge_fields_required=["first_name", "business_name", "cart_items", "cart_total", "cart_url"],
    merge_fields_optional=["cart_discount", "discount_code", "product_image_url"],
    frequency_cap="Don't start if contact received a cart abandonment email in last 7 days",
    exclusion_criteria=[
        "Contact completed purchase after cart was created",
        "Cart total is under $10 (not worth the sequence)",
    ],
    success_metrics=["cart_recovery_rate", "revenue_recovered", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=1,
            subject_templates=[
                "You left something behind, {first_name}",
                "{first_name}, your cart is waiting for you",
            ],
            preview_text="Your items are still in your cart. Complete your order before they sell out.",
            body_structure=["greeting", "cart_reminder", "cart_items_list", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Looks like you left a few things in your cart:\n\n"
                "{cart_items}\n\n"
                "Total: {cart_total}\n\n"
                "Your items are saved, but we can't guarantee they will stay in stock. "
                "Complete your order here:\n"
                "{cart_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Complete your order",
            cta_url_template="{cart_url}",
            tone="casual",
            goal="Remind about abandoned cart, recover purchase",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=1,
            delay_hours=0,
            subject_templates=[
                "Still thinking about it, {first_name}?",
                "Your {business_name} cart -- a closer look",
            ],
            preview_text="Here is why our customers love these products.",
            body_structure=["greeting", "product_details", "social_proof", "cart_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We noticed you are still thinking about your cart. Here is a bit more "
                "about what you picked:\n\n"
                "{cart_items}\n\n"
                "Our customers consistently rate these products 4.5+ stars. "
                "They are some of our most popular items, and for good reason.\n\n"
                "Your total: {cart_total}\n\n"
                "Finish your order:\n"
                "{cart_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Finish your order",
            cta_url_template="{cart_url}",
            tone="helpful",
            goal="Provide product details and social proof to overcome hesitation",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "Last chance, {first_name} -- your cart expires soon",
                "Final reminder: your {business_name} cart",
            ],
            preview_text="Your saved cart is about to expire. Here is a little incentive.",
            body_structure=["greeting", "final_reminder", "incentive", "cart_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "This is your last reminder -- your cart is about to expire.\n\n"
                "{cart_items}\n\n"
                "Total: {cart_total}\n\n"
                "To help you decide, here is a little something extra: "
                "use code {discount_code} for {cart_discount} off your order.\n\n"
                "Grab your items before they are gone:\n"
                "{cart_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Claim your discount and check out",
            cta_url_template="{cart_url}",
            tone="urgent",
            goal="Final recovery attempt with incentive",
        ),
    ],
)


ECOMMERCE_POST_PURCHASE = SequenceTemplate(
    id="ecommerce_post_purchase",
    name="Ecommerce Post-Purchase",
    description=(
        "Four-email post-purchase nurture: order confirmation, how-to guide, "
        "review request, and cross-sell recommendation."
    ),
    archetype="ecommerce",
    category="post_purchase",
    trigger="purchase_complete",
    email_count=4,
    total_duration_days=14,
    merge_fields_required=["first_name", "business_name", "product_name", "order_number"],
    merge_fields_optional=["how_to_url", "review_link", "cross_sell_product", "cross_sell_url", "shop_url"],
    frequency_cap="Don't start if contact received email in last 24h",
    exclusion_criteria=[
        "Contact requested a return or refund",
        "Order was cancelled",
    ],
    success_metrics=["review_rate", "cross_sell_conversion_rate", "repeat_purchase_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=1,
            delay_hours=0,
            subject_templates=[
                "Thank you for your order, {first_name}!",
                "Order #{order_number} confirmed -- what's next",
            ],
            preview_text="Your order is confirmed. Here is what to expect.",
            body_structure=["greeting", "thank_you", "order_details", "whats_next", "signature"],
            body_template=(
                "Hi {first_name},\n\n"
                "Thank you for ordering {product_name} from {business_name}! "
                "Your order #{order_number} is confirmed.\n\n"
                "Here is what happens next:\n"
                "1. We prepare your order with care.\n"
                "2. You will receive a shipping notification with tracking info.\n"
                "3. Your order arrives at your door.\n\n"
                "If you have any questions about your order, just reply to this email.\n\n"
                "Thanks for choosing us,\n"
                "{business_name} Team"
            ),
            cta_text="Track your order",
            cta_url_template=None,
            tone="warm",
            goal="Confirm order, set expectations, build excitement",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=3,
            delay_hours=0,
            subject_templates=[
                "Getting started with your {product_name}",
                "{first_name}, here's how to get the most out of your {product_name}",
            ],
            preview_text="A few tips to help you get the most out of your new purchase.",
            body_structure=["greeting", "getting_started", "tips", "how_to_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Your {product_name} should be arriving soon (or maybe it already has!). "
                "Here are a few tips to get the most out of it:\n\n"
                "Tip 1: Start with the basics. Follow the included guide for initial setup.\n"
                "Tip 2: Take care of it properly. A little maintenance goes a long way.\n"
                "Tip 3: Check out our how-to page for advanced tips and tricks:\n"
                "{how_to_url}\n\n"
                "Have questions? We are here to help -- just reply.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Read the full guide",
            cta_url_template="{how_to_url}",
            tone="helpful",
            goal="Help customer get value from purchase, reduce returns",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "How's your {product_name} working out, {first_name}?",
                "A quick favor: share your {product_name} experience",
            ],
            preview_text="Tell us how you like it -- your review helps other shoppers.",
            body_structure=["greeting", "review_ask", "why_it_matters", "review_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "You have had your {product_name} for about a week now. "
                "How is it working out?\n\n"
                "If you are enjoying it, we would love for you to share your experience. "
                "A quick review helps other shoppers make confident decisions -- and it "
                "takes less than 2 minutes:\n"
                "{review_link}\n\n"
                "If something is not right, reply to this email and our team will "
                "sort it out.\n\n"
                "Thank you,\n"
                "{business_name} Team"
            ),
            cta_text="Leave a review",
            cta_url_template="{review_link}",
            tone="appreciative",
            goal="Collect product reviews",
        ),
        SequenceEmailTemplate(
            position=4,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "You might also like this, {first_name}",
                "A perfect match for your {product_name}",
            ],
            preview_text="Based on your recent purchase, we think you will love this.",
            body_structure=["greeting", "recommendation_intro", "cross_sell_product", "why_it_pairs", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Based on your {product_name} purchase, we think you will love:\n\n"
                "{cross_sell_product}\n\n"
                "Customers who bought {product_name} often pair it with {cross_sell_product} "
                "for an even better experience.\n\n"
                "Check it out:\n"
                "{cross_sell_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Shop now",
            cta_url_template="{cross_sell_url}",
            tone="casual",
            goal="Drive cross-sell and increase average order value",
        ),
    ],
)


ECOMMERCE_BROWSE_ABANDONMENT = SequenceTemplate(
    id="ecommerce_browse_abandonment",
    name="Ecommerce Browse Abandonment",
    description=(
        "Three-email browse abandonment sequence for visitors who viewed products "
        "but did not add to cart."
    ),
    archetype="ecommerce",
    category="browse_abandonment",
    trigger="browse_without_purchase",
    email_count=3,
    total_duration_days=5,
    merge_fields_required=["first_name", "business_name", "browsed_product", "product_url"],
    merge_fields_optional=["product_category", "related_products", "shop_url", "discount_code"],
    frequency_cap="Don't start if contact received email in last 48h",
    exclusion_criteria=[
        "Contact made a purchase since browsing",
        "Contact already in a cart abandonment sequence",
    ],
    success_metrics=["browse_to_cart_rate", "purchase_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=4,
            subject_templates=[
                "Still interested in {browsed_product}, {first_name}?",
                "{first_name}, take another look at {browsed_product}",
            ],
            preview_text="The product you were looking at is still available.",
            body_structure=["greeting", "product_reminder", "product_highlight", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We noticed you were checking out {browsed_product}. Great taste!\n\n"
                "In case you want to take another look, here is the link:\n"
                "{product_url}\n\n"
                "If you have any questions about the product, our team is happy to help. "
                "Just reply to this email.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="View product",
            cta_url_template="{product_url}",
            tone="casual",
            goal="Bring visitor back to viewed product",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "Customers love {browsed_product} -- here's why",
                "{first_name}, see why {browsed_product} is a customer favourite",
            ],
            preview_text="See what other customers are saying about this product.",
            body_structure=["greeting", "social_proof", "product_link", "related_products", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "You were looking at {browsed_product}, and we thought you might like "
                "to know what our customers think:\n\n"
                "This product is one of our most popular items, consistently rated "
                "highly by real customers.\n\n"
                "See it here: {product_url}\n\n"
                "You might also like: {related_products}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Shop now",
            cta_url_template="{product_url}",
            tone="helpful",
            goal="Social proof to build confidence",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=5,
            delay_hours=0,
            subject_templates=[
                "A little something for you, {first_name}",
                "{first_name}, here's an exclusive offer on {browsed_product}",
            ],
            preview_text="An exclusive offer to help you decide.",
            body_structure=["greeting", "offer", "product_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We know {browsed_product} caught your eye, so we are sending you "
                "a little incentive to help you decide:\n\n"
                "Use code {discount_code} for a special discount on your order.\n\n"
                "Grab it here: {product_url}\n\n"
                "This offer expires in 48 hours.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Claim your discount",
            cta_url_template="{product_url}",
            tone="casual",
            goal="Final incentive to convert browser into buyer",
        ),
    ],
)


ECOMMERCE_WINBACK = SequenceTemplate(
    id="ecommerce_winback",
    name="Ecommerce Win-Back",
    description=(
        "Three-email win-back sequence for customers who haven't purchased in 90+ days."
    ),
    archetype="ecommerce",
    category="reactivation",
    trigger="dormant_90d",
    email_count=3,
    total_duration_days=30,
    merge_fields_required=["first_name", "business_name", "last_product", "last_purchase_date"],
    merge_fields_optional=["winback_offer", "discount_code", "shop_url", "new_arrivals_url"],
    frequency_cap="Don't start if contact received email in last 7 days",
    exclusion_criteria=[
        "Contact purchased since becoming dormant",
        "Contact has opted out of marketing emails",
    ],
    success_metrics=["reactivation_rate", "purchase_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "We miss you, {first_name}!",
                "{first_name}, it's been a while -- come see what's new",
            ],
            preview_text="It has been a while and we have been busy. Come see what is new.",
            body_structure=["greeting", "personal_touch", "whats_new", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "It has been a while since your last order ({last_product} on "
                "{last_purchase_date}), and we have missed you!\n\n"
                "A lot has changed since then. We have new products, updated favourites, "
                "and a few surprises we think you will love.\n\n"
                "Come take a look: {new_arrivals_url}\n\n"
                "We hope to see you soon.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="See what's new",
            cta_url_template="{new_arrivals_url}",
            tone="warm",
            goal="Re-engage dormant customer with what is new",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=10,
            delay_hours=0,
            subject_templates=[
                "A special offer for a special customer",
                "{first_name}, we saved this for you",
            ],
            preview_text="An exclusive offer just for returning customers like you.",
            body_structure=["greeting", "exclusive_offer", "urgency", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We wanted to do something special for you as a past customer of "
                "{business_name}.\n\n"
                "Here is an exclusive offer just for you:\n\n"
                "{winback_offer}\n\n"
                "Use code {discount_code} at checkout. This offer is valid for the "
                "next 7 days.\n\n"
                "Shop now: {shop_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Shop with your discount",
            cta_url_template="{shop_url}",
            tone="exclusive",
            goal="Incentivize return purchase with exclusive offer",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=30,
            delay_hours=0,
            subject_templates=[
                "Last chance: your exclusive offer expires tomorrow",
                "{first_name}, your {winback_offer} is almost gone",
            ],
            preview_text="Your returning-customer discount expires tomorrow.",
            body_structure=["greeting", "final_reminder", "offer_expiry", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "This is our last reminder -- your exclusive returning-customer offer "
                "is expiring soon.\n\n"
                "{winback_offer} with code {discount_code}.\n\n"
                "After this, the offer is gone for good. If you have been thinking about "
                "it, now is the time.\n\n"
                "Shop here: {shop_url}\n\n"
                "We hope to welcome you back,\n"
                "{business_name} Team"
            ),
            cta_text="Use your discount before it expires",
            cta_url_template="{shop_url}",
            tone="urgent",
            goal="Final push with expiring offer",
        ),
    ],
)


ECOMMERCE_REPLENISHMENT = SequenceTemplate(
    id="ecommerce_replenishment",
    name="Ecommerce Replenishment Reminder",
    description=(
        "Three-email replenishment reminder timed to the product lifecycle. "
        "Reminds customers to reorder consumable products before they run out."
    ),
    archetype="ecommerce",
    category="replenishment",
    trigger="product_lifecycle_timer",
    email_count=3,
    total_duration_days=14,
    merge_fields_required=["first_name", "product_name", "reorder_url", "last_purchase_date"],
    merge_fields_optional=["business_name", "discount_code", "product_image_url"],
    frequency_cap="Don't start if contact received email in last 48h",
    exclusion_criteria=[
        "Contact already reordered the product",
        "Contact returned the original order",
    ],
    success_metrics=["reorder_rate", "open_rate", "revenue_from_replenishment"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "Running low on {product_name}, {first_name}?",
                "Time to restock your {product_name}",
            ],
            preview_text="Based on your last order, you might be running low. Reorder in one click.",
            body_structure=["greeting", "reminder", "why_timely", "reorder_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Based on your last order, you might be running low on {product_name}. "
                "Most of our customers reorder around this time.\n\n"
                "Restock with one click:\n"
                "{reorder_url}\n\n"
                "Running out means a gap in your routine, and we want to make sure "
                "you stay on track.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Reorder now",
            cta_url_template="{reorder_url}",
            tone="helpful",
            goal="Early reminder before customer runs out",
            notes="Sent lifecycle_days - 7 days after purchase.",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=7,
            delay_hours=0,
            subject_templates=[
                "Your {product_name} is due for reorder",
                "{first_name}, don't run out of {product_name}",
            ],
            preview_text="It is time to reorder. Keep your routine on track.",
            body_structure=["greeting", "due_date_reminder", "consequences", "reorder_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Your {product_name} should be running out right about now. "
                "Reordering today means no gap in your routine.\n\n"
                "Restock here: {reorder_url}\n\n"
                "We ship fast so you will have it before you run out.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Reorder today",
            cta_url_template="{reorder_url}",
            tone="direct",
            goal="Reorder on the due date",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "Don't forget: your {product_name} needs reordering",
                "{first_name}, your {product_name} supply is overdue",
            ],
            preview_text="You are past due for a reorder. Act today to avoid a gap.",
            body_structure=["greeting", "overdue_reminder", "gentle_nudge", "reorder_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "You are past the typical reorder window for {product_name}. "
                "If you haven't restocked yet, now is a good time.\n\n"
                "Skipping can mean inconsistent results and having to restart your "
                "routine from scratch. A quick reorder keeps things on track:\n"
                "{reorder_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            cta_text="Reorder now",
            cta_url_template="{reorder_url}",
            tone="direct",
            goal="Final nudge for overdue reorder",
        ),
    ],
)


# ============================================================================
# PROFESSIONAL-SERVICES Sequences
# ============================================================================

PROFESSIONAL_INQUIRY = SequenceTemplate(
    id="professional_inquiry",
    name="Professional Services Inquiry Response",
    description=(
        "Three-email inquiry response sequence for professional-services firms "
        "(law, accounting, consulting): acknowledgment, consultation offer, "
        "and thought leadership."
    ),
    archetype="professional-services",
    category="welcome",
    trigger="form_submission",
    email_count=3,
    total_duration_days=5,
    merge_fields_required=["first_name", "business_name", "practice_area", "phone_number"],
    merge_fields_optional=["consultant_name", "consultation_url", "case_study_url", "scheduling_url"],
    frequency_cap="Don't start if contact received email in last 48h",
    exclusion_criteria=[
        "Contact already scheduled a consultation",
        "Contact is an existing client",
    ],
    success_metrics=["consultation_booking_rate", "reply_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "{first_name}, we received your {practice_area} inquiry",
                "Your {practice_area} inquiry -- next steps from {business_name}",
            ],
            preview_text="We received your inquiry and are reviewing the details now.",
            body_structure=["greeting", "acknowledgment", "what_we_need", "consultation_offer", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Thank you for reaching out to {business_name} about {practice_area}. "
                "We received your inquiry and are reviewing the details.\n\n"
                "To give you the most accurate guidance, it would help to understand:\n"
                "- The timeline for your matter\n"
                "- Any specific outcomes you are looking for\n"
                "- Whether you have spoken with other firms\n\n"
                "If you would like to discuss your situation in more detail, we offer "
                "a free initial consultation:\n"
                "{consultation_url}\n\n"
                "Or call us directly at {phone_number}.\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Schedule a free consultation",
            cta_url_template="{consultation_url}",
            tone="professional",
            goal="Acknowledge inquiry, qualify lead with questions, offer consultation",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=2,
            delay_hours=0,
            subject_templates=[
                "Let's discuss your {practice_area} needs, {first_name}",
                "{first_name}, a 15-minute call could clarify your options",
            ],
            preview_text="A brief conversation can help us point you in the right direction.",
            body_structure=["greeting", "consultation_pitch", "what_you_get", "scheduling_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We wanted to follow up on your {practice_area} inquiry. "
                "Our team has reviewed the information you provided, and we believe "
                "a brief consultation would be the most productive next step.\n\n"
                "In a 15-minute call, we can:\n"
                "- Assess your situation and outline your options\n"
                "- Identify the best approach for your specific circumstances\n"
                "- Answer any immediate questions you have\n\n"
                "No obligation -- just clarity on where you stand.\n\n"
                "Schedule your consultation: {consultation_url}\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Book your 15-minute call",
            cta_url_template="{consultation_url}",
            tone="professional",
            goal="Convert inquiry into consultation booking",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=5,
            delay_hours=0,
            subject_templates=[
                "How {business_name} helped a client with {practice_area}",
                "{first_name}, a {practice_area} case study you might find useful",
            ],
            preview_text="See how we helped a client in a situation similar to yours.",
            body_structure=["greeting", "case_study_intro", "results", "relate_to_lead", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We thought you might find this useful -- here is a recent {practice_area} "
                "engagement where we helped a client in a situation similar to yours.\n\n"
                "The challenge: The client was dealing with a complex {practice_area} matter "
                "that required a clear strategy and fast action.\n\n"
                "What we did: Our team developed a targeted approach that addressed the "
                "core issues while minimizing risk and cost.\n\n"
                "The result: The client achieved a favourable outcome within the expected "
                "timeline, and the approach saved them significant resources.\n\n"
                "Read the full case study: {case_study_url}\n\n"
                "Every situation is different, but the principles apply. "
                "If you would like to discuss your options, we are here:\n"
                "{consultation_url}\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Read the full case study",
            cta_url_template="{case_study_url}",
            tone="authoritative",
            goal="Build credibility with relevant case study, drive consultation",
        ),
    ],
)


PROFESSIONAL_NURTURE = SequenceTemplate(
    id="professional_nurture",
    name="Professional Services Long-Term Nurture",
    description=(
        "Three-email nurture sequence for leads who didn't convert within 30 days. "
        "Thought leadership, case study, and consultation CTA."
    ),
    archetype="professional-services",
    category="nurture",
    trigger="lead_not_converted_30d",
    email_count=3,
    total_duration_days=21,
    merge_fields_required=["first_name", "business_name", "practice_area"],
    merge_fields_optional=["article_url", "case_study_url", "consultation_url", "phone_number"],
    frequency_cap="Don't start if contact received email in last 7 days",
    exclusion_criteria=[
        "Contact has converted to client",
        "Contact explicitly said they are not interested",
    ],
    success_metrics=["consultation_booking_rate", "content_engagement_rate", "open_rate"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=0,
            delay_hours=0,
            subject_templates=[
                "New insights on {practice_area} from {business_name}",
                "{first_name}, a thought piece on {practice_area} you'll want to read",
            ],
            preview_text="New thinking on {practice_area} from our team -- no sales pitch, just expertise.",
            body_structure=["greeting", "article_intro", "key_insight", "read_more", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Our {practice_area} team recently published a piece that we think "
                "you will find valuable.\n\n"
                "The key insight: Most people in your situation underestimate how much "
                "early action can change the outcome. The data is clear -- the sooner "
                "you have a plan, the better your position.\n\n"
                "Read the full article: {article_url}\n\n"
                "No strings attached -- just sharing what we know.\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Read the article",
            cta_url_template="{article_url}",
            tone="authoritative",
            goal="Provide thought leadership to stay top of mind",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=10,
            delay_hours=0,
            subject_templates=[
                "How we helped a client with a {practice_area} challenge",
                "{first_name}, a relevant {practice_area} success story",
            ],
            preview_text="A real-world example of how we handle {practice_area} cases.",
            body_structure=["greeting", "case_study_intro", "summary", "read_more", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Here is a recent case study from our {practice_area} practice that "
                "might be relevant to your situation:\n\n"
                "A client came to us facing a complex challenge with tight deadlines "
                "and limited options. Our team built a tailored strategy that delivered "
                "results within the expected window while keeping costs reasonable.\n\n"
                "Read the full case study: {case_study_url}\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Read the case study",
            cta_url_template="{case_study_url}",
            tone="authoritative",
            goal="Build credibility with case study",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=21,
            delay_hours=0,
            subject_templates=[
                "Ready to discuss your {practice_area} options, {first_name}?",
                "{first_name}, let's find the right path for your {practice_area} needs",
            ],
            preview_text="A no-obligation conversation about where you stand and what comes next.",
            body_structure=["greeting", "soft_ask", "what_you_get", "scheduling_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We have shared some insights and case studies with you over the "
                "past few weeks, and we hope they were useful.\n\n"
                "If you are ready to take the next step -- or even if you just want "
                "to understand your options better -- we would be happy to connect.\n\n"
                "A 15-minute consultation is all it takes to get clarity on your "
                "{practice_area} situation. No obligation, no pressure.\n\n"
                "Book your consultation: {consultation_url}\n"
                "Or call us at {phone_number}.\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Schedule a consultation",
            cta_url_template="{consultation_url}",
            tone="professional",
            goal="Convert nurtured lead into consultation",
        ),
    ],
)


PROFESSIONAL_POST_ENGAGEMENT = SequenceTemplate(
    id="professional_post_engagement",
    name="Professional Services Post-Engagement",
    description=(
        "Three-email post-engagement sequence: thank you, testimonial request, "
        "and referral ask over 60 days."
    ),
    archetype="professional-services",
    category="post_purchase",
    trigger="engagement_completed",
    email_count=3,
    total_duration_days=60,
    merge_fields_required=["first_name", "business_name", "practice_area", "engagement_type"],
    merge_fields_optional=["review_link", "referral_link", "referral_offer", "consultant_name"],
    frequency_cap="Don't start if contact received email in last 72h",
    exclusion_criteria=[
        "Client filed a complaint about the engagement",
        "Client has outstanding unpaid invoices",
    ],
    success_metrics=["testimonial_rate", "referral_rate", "nps_score"],
    emails=[
        SequenceEmailTemplate(
            position=1,
            delay_days=3,
            delay_hours=0,
            subject_templates=[
                "Thank you for trusting {business_name}, {first_name}",
                "{first_name}, it was a pleasure working with you",
            ],
            preview_text="A sincere thank you from our team.",
            body_structure=["greeting", "thank_you", "recap", "future_support", "signature"],
            body_template=(
                "Hi {first_name},\n\n"
                "With your {engagement_type} engagement wrapping up, we wanted to take "
                "a moment to say thank you. It was a pleasure working with you.\n\n"
                "We take pride in every client relationship, and yours was no exception. "
                "If you ever need support on {practice_area} matters in the future, "
                "our team is always here.\n\n"
                "Thank you for placing your trust in {business_name}.\n\n"
                "Warm regards,\n"
                "{business_name} Team"
            ),
            cta_text="Reply if you need anything",
            cta_url_template=None,
            tone="warm",
            goal="Express genuine gratitude and reinforce relationship",
        ),
        SequenceEmailTemplate(
            position=2,
            delay_days=14,
            delay_hours=0,
            subject_templates=[
                "Would you share your experience with {business_name}?",
                "{first_name}, your feedback means a lot to us",
            ],
            preview_text="A testimonial from you helps other people in similar situations.",
            body_structure=["greeting", "testimonial_ask", "how_it_helps", "review_link", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "Now that your {engagement_type} engagement is complete, would you "
                "be willing to share a brief testimonial about your experience?\n\n"
                "Your words help people in similar situations find the right guidance. "
                "It can be as simple as a sentence or two about what the process "
                "was like and whether you would recommend us.\n\n"
                "You can leave your feedback here: {review_link}\n\n"
                "We read every testimonial and appreciate the feedback more than you know.\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Share your experience",
            cta_url_template="{review_link}",
            tone="appreciative",
            goal="Collect client testimonials for credibility",
        ),
        SequenceEmailTemplate(
            position=3,
            delay_days=60,
            delay_hours=0,
            subject_templates=[
                "Know someone who could use {practice_area} guidance?",
                "{first_name}, we welcome referrals from trusted clients like you",
            ],
            preview_text="If you know someone who needs help, we would love an introduction.",
            body_structure=["greeting", "referral_ask", "how_to_refer", "incentive", "cta"],
            body_template=(
                "Hi {first_name},\n\n"
                "We hope everything has been going well since our work together.\n\n"
                "If you know a colleague, friend, or family member who could use "
                "guidance on {practice_area}, we would be grateful for an introduction. "
                "The best compliment we receive is a referral from someone we have served.\n\n"
                "You can forward this email, have them mention your name when they call, "
                "or reply with their details and we will reach out directly.\n\n"
                "Thank you for your continued trust.\n\n"
                "Best regards,\n"
                "{business_name} Team"
            ),
            cta_text="Reply with a referral",
            cta_url_template=None,
            tone="professional",
            goal="Generate referrals from satisfied clients",
        ),
    ],
)


# ============================================================================
# Master Template Registry
# ============================================================================

ALL_SEQUENCE_TEMPLATES: Dict[str, SequenceTemplate] = {
    "local_service_welcome": LOCAL_SERVICE_WELCOME,
    "local_service_post_job": LOCAL_SERVICE_POST_JOB,
    "local_service_quote_followup": LOCAL_SERVICE_QUOTE_FOLLOWUP,
    "local_service_seasonal": LOCAL_SERVICE_SEASONAL,
    "local_service_dormant": LOCAL_SERVICE_DORMANT,
    "ecommerce_welcome": ECOMMERCE_WELCOME,
    "ecommerce_cart_abandonment": ECOMMERCE_CART_ABANDONMENT,
    "ecommerce_post_purchase": ECOMMERCE_POST_PURCHASE,
    "ecommerce_browse_abandonment": ECOMMERCE_BROWSE_ABANDONMENT,
    "ecommerce_winback": ECOMMERCE_WINBACK,
    "ecommerce_replenishment": ECOMMERCE_REPLENISHMENT,
    "professional_inquiry": PROFESSIONAL_INQUIRY,
    "professional_nurture": PROFESSIONAL_NURTURE,
    "professional_post_engagement": PROFESSIONAL_POST_ENGAGEMENT,
}


# ============================================================================
# Helper Functions
# ============================================================================


def get_templates_by_archetype(archetype: str) -> List[SequenceTemplate]:
    """Return all templates for the given archetype plus any 'universal' templates."""
    return [
        tpl
        for tpl in ALL_SEQUENCE_TEMPLATES.values()
        if tpl.archetype == archetype or tpl.archetype == "universal"
    ]


def get_template(template_id: str) -> Optional[SequenceTemplate]:
    """Look up a single template by its ID."""
    return ALL_SEQUENCE_TEMPLATES.get(template_id)


def get_templates_by_category(category: str) -> List[SequenceTemplate]:
    """Return all templates matching the given category (welcome, post_purchase, etc.)."""
    return [
        tpl
        for tpl in ALL_SEQUENCE_TEMPLATES.values()
        if tpl.category == category
    ]


def get_required_merge_fields(template_id: str) -> List[str]:
    """Return the required merge fields for a template.

    Returns an empty list if the template is not found.
    """
    tpl = ALL_SEQUENCE_TEMPLATES.get(template_id)
    if tpl is None:
        return []
    return list(tpl.merge_fields_required)


def validate_merge_fields(template_id: str, provided_fields: Dict[str, str]) -> List[str]:
    """Return the list of required merge fields that are missing from *provided_fields*.

    An empty return list means all required fields are present.
    """
    required = get_required_merge_fields(template_id)
    return [field for field in required if field not in provided_fields]

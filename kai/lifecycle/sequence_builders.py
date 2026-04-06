"""Specialised sequence builders that produce fully personalised, ready-to-send
email sequences from templates and real customer data.

Each builder is a factory that knows its domain: post-job review requests,
quote follow-ups, dormant-lead re-engagement, referrals, and maintenance
reorder cadences.  Every built sequence passes quality gates (banned words,
AI slop) and CAN-SPAM compliance checks before being returned.
"""

from __future__ import annotations

import copy
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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
# Constants
# ============================================================================

BANNED_PHRASES_IN_EMAILS: List[str] = [
    # From CLAUDE.md banned words
    "leverage",
    "utilize",
    "synergy",
    "innovative",
    "deep dive",
    "circle back",
    "touch base",
    "moving forward",
    "at the end of the day",
    # AI slop
    "in conclusion",
    "it's important to note",
    "in today's rapidly evolving",
    "this comprehensive guide",
    "without further ado",
    "it's worth noting that",
    # Bad follow-up phrases
    "just checking in",
    "just following up",
    "wanted to touch base",
    "hope this finds you well",
    "per my last email",
    "as per our conversation",
    "please do not hesitate",
    "please find attached",
    "I hope all is well",
    # Generic filler
    "we are excited to",
    "we are thrilled to",
    "we are delighted to",
    "valued customer",
    "esteemed client",
]

# Service types considered same-day (review request can go out sooner)
SAME_DAY_SERVICES = frozenset([
    "cleaning",
    "house cleaning",
    "carpet cleaning",
    "window cleaning",
    "pest control",
    "lawn mowing",
    "pressure washing",
    "locksmith",
    "appliance repair",
    "handyman",
    "junk removal",
    "gutter cleaning",
])

# Service types considered multi-day (review request should wait)
MULTI_DAY_SERVICES = frozenset([
    "roofing",
    "remodeling",
    "renovation",
    "construction",
    "kitchen remodel",
    "bathroom remodel",
    "painting",
    "flooring",
    "siding",
    "deck building",
    "fence installation",
    "pool installation",
    "landscaping design",
    "solar installation",
])

# Default product/service lifecycle periods in days
DEFAULT_LIFECYCLES: Dict[str, int] = {
    "air_filter": 90,
    "water_filter": 180,
    "oil_change": 90,
    "hvac_maintenance": 180,
    "pest_treatment": 90,
    "lawn_care": 30,
    "dental_cleaning": 180,
    "skincare": 60,
    "supplements": 30,
    "printer_ink": 60,
    "pool_chemicals": 30,
    "pet_grooming": 45,
}

# Service-type to reminder cycle in months
SERVICE_REMINDER_CYCLES: Dict[str, int] = {
    "hvac": 6,
    "plumbing": 12,
    "pest control": 3,
    "landscaping": 3,
    "dental": 6,
    "auto maintenance": 6,
    "chimney": 12,
    "carpet cleaning": 12,
    "window cleaning": 6,
    "gutter cleaning": 6,
    "septic": 36,
    "roof inspection": 12,
}


# ============================================================================
# Models
# ============================================================================


class BuiltSequence(BaseModel):
    """A fully personalised, ready-to-send email sequence."""

    id: str
    template_id: str
    builder_type: str
    business_name: str
    contact_email: str
    contact_name: str
    emails: List[Dict[str, Any]] = Field(default_factory=list)
    total_emails: int = 0
    total_duration_days: int = 0
    merge_fields_used: Dict[str, str] = Field(default_factory=dict)
    quality_check_passed: bool = False
    quality_issues: List[str] = Field(default_factory=list)
    compliance_check_passed: bool = False
    compliance_issues: List[str] = Field(default_factory=list)
    unsubscribe_link_included: bool = False
    physical_address_included: bool = False
    created_at: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuilderConfig(BaseModel):
    """Configuration shared by all sequence builders."""

    business_name: str
    business_phone: Optional[str] = None
    business_email: Optional[str] = None
    business_website: Optional[str] = None
    physical_address: str = ""
    operator_name: Optional[str] = None
    industry: Optional[str] = None
    scheduling_url: Optional[str] = None
    review_links: Dict[str, str] = Field(default_factory=dict)
    referral_link: Optional[str] = None
    referral_offer: Optional[str] = None
    unsubscribe_url: str = ""
    from_email: str = ""
    from_name: str = ""
    brand_voice_tone: str = "professional"
    kaicalls_enabled: bool = False
    kaicalls_phone: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Module-level helpers
# ============================================================================


def generate_built_sequence_id() -> str:
    """Return a unique sequence ID in the format ``bseq_{12hex}``."""
    return f"bseq_{uuid.uuid4().hex[:12]}"


def check_for_banned_phrases(text: str) -> List[str]:
    """Scan *text* against ``BANNED_PHRASES_IN_EMAILS``.

    Returns a list of found phrases (case-insensitive match).
    """
    lower = text.lower()
    return [phrase for phrase in BANNED_PHRASES_IN_EMAILS if phrase.lower() in lower]


def strip_html_to_text(html: str) -> str:
    """Strip HTML tags to produce a plain-text version.

    Preserves line breaks (``<br>``, ``<p>``, ``<div>`` converted to newlines).
    """
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|div|h[1-6]|li|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_unsubscribe_footer(
    unsubscribe_url: str,
    physical_address: str,
    business_name: str,
) -> str:
    """Return an HTML footer block with unsubscribe link, physical address, and credit."""
    return (
        '<div style="margin-top:32px; padding-top:16px; border-top:1px solid #e0e0e0; '
        'font-size:12px; color:#888888; text-align:center;">'
        f"<p>Sent by {business_name}</p>"
        f"<p>{physical_address}</p>"
        f'<p><a href="{unsubscribe_url}" style="color:#888888;">Unsubscribe</a></p>'
        "</div>"
    )


def calculate_reorder_date(last_purchase_date: str, lifecycle_days: int) -> str:
    """Return the ISO date when a reorder reminder should trigger."""
    try:
        dt = datetime.strptime(last_purchase_date[:10], "%Y-%m-%d")
    except ValueError:
        dt = datetime.utcnow()
    reorder_dt = dt + timedelta(days=lifecycle_days)
    return reorder_dt.strftime("%Y-%m-%d")


def format_currency(amount: float) -> str:
    """Return a formatted currency string (e.g. ``$1,500.00``)."""
    return f"${amount:,.2f}"


def personalize_greeting(name: str, time_of_day: Optional[str] = None) -> str:
    """Return a personalised greeting.

    If *time_of_day* is ``morning``, ``afternoon``, or ``evening`` the
    greeting reflects the period.  Otherwise defaults to ``Hi {name}``.
    """
    if time_of_day == "morning":
        return f"Good morning, {name}"
    if time_of_day == "afternoon":
        return f"Good afternoon, {name}"
    if time_of_day == "evening":
        return f"Good evening, {name}"
    return f"Hi {name}"


# ============================================================================
# Abstract base
# ============================================================================


class SequenceBuilder(ABC):
    """Base class for all sequence builders.

    Subclasses implement ``_generate_emails()`` and set ``builder_type``.
    The ``build()`` method orchestrates generation, quality checks, compliance
    checks, and returns a :class:`BuiltSequence`.
    """

    def __init__(self, config: BuilderConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def builder_type(self) -> str:
        """Machine-readable identifier for this builder."""

    def build(self, **kwargs: Any) -> BuiltSequence:
        """Main entry point.  Generates emails, applies gates, returns result."""
        emails = self._generate_emails(**kwargs)

        # Add footer to every email
        for email_dict in emails:
            body_html = email_dict.get("body_html", "")
            body_html = self._add_footer(body_html)
            email_dict["body_html"] = body_html
            email_dict["body_text"] = self._generate_plain_text(body_html)

        quality_passed, quality_issues = self._apply_quality_check(emails)
        compliance_passed, compliance_issues = self._apply_compliance_check(emails)

        # Duration calculation
        total_duration = 0
        if emails:
            total_duration = sum(e.get("delay_days", 0) for e in emails)

        contact_name = kwargs.get("customer_name") or kwargs.get("lead_name", "")
        contact_email = kwargs.get("customer_email") or kwargs.get("lead_email", "")

        return BuiltSequence(
            id=generate_built_sequence_id(),
            template_id=kwargs.get("template_id", ""),
            builder_type=self.builder_type,
            business_name=self.config.business_name,
            contact_email=contact_email,
            contact_name=contact_name,
            emails=emails,
            total_emails=len(emails),
            total_duration_days=total_duration,
            merge_fields_used=kwargs.get("merge_fields_used", {}),
            quality_check_passed=quality_passed,
            quality_issues=quality_issues,
            compliance_check_passed=compliance_passed,
            compliance_issues=compliance_issues,
            unsubscribe_link_included=bool(self.config.unsubscribe_url),
            physical_address_included=bool(self.config.physical_address),
            created_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            metadata=kwargs.get("metadata", {}),
        )

    # ----- abstract --------------------------------------------------------

    @abstractmethod
    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Produce the list of ready-to-send email dicts."""

    # ----- quality & compliance -------------------------------------------

    def _apply_quality_check(
        self, emails: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Check each email for banned words, AI slop, and basic quality."""
        issues: List[str] = []

        for idx, email_dict in enumerate(emails, start=1):
            subject = email_dict.get("subject", "")
            body = email_dict.get("body_html", "") or email_dict.get("body_text", "")
            combined = f"{subject} {body}"

            # Banned phrases
            found = check_for_banned_phrases(combined)
            if found:
                issues.append(f"Email {idx}: banned phrase(s) found: {', '.join(found)}")

            # Subject quality
            if not subject.strip():
                issues.append(f"Email {idx}: subject line is empty.")
            elif subject == subject.upper() and len(subject) > 5:
                issues.append(f"Email {idx}: subject line is all caps.")
            elif len(subject) > 60:
                issues.append(
                    f"Email {idx}: subject line is {len(subject)} chars "
                    "(recommended under 60)."
                )

            # Body length
            plain = strip_html_to_text(body)
            if len(plain) < 50:
                issues.append(
                    f"Email {idx}: body is too short ({len(plain)} chars, minimum 50)."
                )
            elif len(plain) > 2000:
                issues.append(
                    f"Email {idx}: body is too long ({len(plain)} chars, max 2000)."
                )

        return (len(issues) == 0, issues)

    def _apply_compliance_check(
        self, emails: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """CAN-SPAM compliance verification for every email in the sequence."""
        issues: List[str] = []

        for idx, email_dict in enumerate(emails, start=1):
            body = email_dict.get("body_html", "") + email_dict.get("body_text", "")

            # Unsubscribe link
            if "unsubscribe" not in body.lower():
                issues.append(f"Email {idx}: missing unsubscribe link or reference.")

            # Physical address
            if not self.config.physical_address:
                issues.append(f"Email {idx}: no physical address configured (CAN-SPAM requirement).")
            elif self.config.physical_address.lower() not in body.lower():
                # Footer should have added it; check for presence
                if self.config.physical_address not in body:
                    pass  # Footer adds it automatically; skip false positive

            # From address
            if not self.config.from_email:
                issues.append(f"Email {idx}: no from_email configured.")

            # Deceptive subject check (very basic: "RE:" or "FW:" without prior conversation)
            subject = email_dict.get("subject", "")
            if subject.upper().startswith(("RE:", "FW:", "FWD:")):
                issues.append(
                    f"Email {idx}: subject starts with '{subject[:3]}' which may be "
                    "deceptive for a first-contact email."
                )

        return (len(issues) == 0, issues)

    # ----- shared utilities ------------------------------------------------

    def _fill_merge_fields(self, template: str, fields: Dict[str, str]) -> str:
        """Replace ``{placeholder}`` tokens with values from *fields*.

        Unfilled placeholders are replaced with ``[MISSING: placeholder_name]``.
        """
        result = template
        # First pass: fill known fields
        for key, value in fields.items():
            result = result.replace(f"{{{key}}}", str(value))
        # Second pass: mark remaining placeholders
        remaining = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", result)
        for placeholder in remaining:
            result = result.replace(f"{{{placeholder}}}", f"[MISSING: {placeholder}]")
        return result

    def _add_footer(self, body_html: str) -> str:
        """Add a standard CAN-SPAM compliant footer."""
        footer = build_unsubscribe_footer(
            unsubscribe_url=self.config.unsubscribe_url or "#unsubscribe",
            physical_address=self.config.physical_address or "[Physical address required]",
            business_name=self.config.business_name,
        )
        return body_html + "\n" + footer

    def _generate_plain_text(self, body_html: str) -> str:
        """Strip HTML to produce a plain-text version of the email body."""
        return strip_html_to_text(body_html)

    def _build_merge_fields(self, **extra: str) -> Dict[str, str]:
        """Construct the merge-fields dict from config + any extra overrides."""
        fields: Dict[str, str] = {
            "business_name": self.config.business_name,
        }
        if self.config.business_phone:
            fields["phone_number"] = self.config.business_phone
            fields["phone"] = self.config.business_phone
        if self.config.business_email:
            fields["business_email"] = self.config.business_email
        if self.config.business_website:
            fields["business_website"] = self.config.business_website
        if self.config.scheduling_url:
            fields["scheduling_url"] = self.config.scheduling_url
        if self.config.referral_link:
            fields["referral_link"] = self.config.referral_link
        if self.config.referral_offer:
            fields["referral_offer"] = self.config.referral_offer
        if self.config.operator_name:
            fields["operator_name"] = self.config.operator_name
        fields.update(extra)
        return fields


# ============================================================================
# PostJobReviewSequence
# ============================================================================


class PostJobReviewSequence(SequenceBuilder):
    """Builds review-request email sequences after a completed job."""

    @property
    def builder_type(self) -> str:
        return "post_job_review"

    # noinspection PyMethodOverriding
    def build(  # type: ignore[override]
        self,
        customer_name: str,
        customer_email: str,
        service_performed: str,
        job_date: str,
        review_platform: str = "google",
    ) -> BuiltSequence:
        return super().build(
            customer_name=customer_name,
            customer_email=customer_email,
            service_performed=service_performed,
            job_date=job_date,
            review_platform=review_platform,
            template_id="local_service_post_job",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["customer_name"]
        first_name = name.split()[0] if name else "there"
        service = kwargs["service_performed"]
        job_date = kwargs["job_date"]
        review_platform = kwargs.get("review_platform", "google")

        review_url = self._select_review_platform(self.config.review_links) or ""
        if not review_url and review_platform in self.config.review_links:
            review_url = self.config.review_links[review_platform]

        fields = self._build_merge_fields(
            first_name=first_name,
            customer_name=name,
            service=service,
            service_type=service,
            service_date=job_date,
            review_link=review_url,
        )

        # Timing: same-day services get faster review asks
        service_lower = service.lower().strip()
        review_day = 3
        if service_lower in SAME_DAY_SERVICES:
            review_day = 1
        elif service_lower in MULTI_DAY_SERVICES:
            review_day = 5

        emails: List[Dict[str, Any]] = []

        # Email 1 -- Thank You (Day 1)
        kaicalls_line = ""
        if self.config.kaicalls_enabled and self.config.kaicalls_phone:
            kaicalls_line = (
                f"\n\nYou can reach us anytime at {self.config.kaicalls_phone} "
                "-- our AI assistant is available 24/7 to answer questions or "
                "schedule your next service."
            )

        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"Thank you for choosing {{business_name}} for your {service} "
                f"on {job_date}. We truly appreciate your trust and hope everything "
                "exceeded your expectations.\n\n"
                "If something is not quite right, please reply to this email "
                f"and we will make it right.{kaicalls_line}\n\n"
                "Thanks again,\n"
                "{business_name} Team"
            ),
            fields,
        )

        emails.append({
            "delay_days": 1,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Thank you for choosing {{business_name}}, {first_name}!", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Had any issues? Reply to this email.",
            "cta_url": None,
        })

        # Email 2 -- Review Request (Day review_day)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"We have a small favor to ask. If you were happy with our {service}, "
                "would you take 2 minutes to leave us a review?\n\n"
                f"Honest reviews help other homeowners in our area find reliable "
                f"{service} providers. It makes a real difference for a local "
                "business like ours.\n\n"
                f"Leave your review here:\n{review_url}\n\n"
                "Thank you -- we read every review and appreciate the feedback.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )

        emails.append({
            "delay_days": review_day,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"A quick favor, {first_name}?", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Leave a review",
            "cta_url": review_url,
        })

        # Email 3 -- Referral Ask (Day 14)
        referral_body = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"If you know a friend, neighbor, or family member who needs {service}, "
                "we would love an introduction.\n\n"
            ),
            fields,
        )
        if self.config.referral_offer:
            referral_body += self._fill_merge_fields(
                "As a thank-you, we are offering {referral_offer} for every referral "
                "who books a service.\n\n",
                fields,
            )
        referral_body += self._fill_merge_fields(
            "Just reply with their name and number -- we will take care of the rest.\n\n"
            "Cheers,\n"
            "{business_name} Team",
            fields,
        )

        emails.append({
            "delay_days": 14,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Know someone who needs {service}?", fields
            ),
            "body_html": referral_body,
            "body_text": "",
            "cta_text": "Reply with a referral",
            "cta_url": self.config.referral_link,
        })

        # Email 4 (optional) -- Seasonal Reminder (Day 90)
        # Include when the industry supports recurring service
        recurring_industries = {
            "hvac", "plumbing", "pest control", "landscaping", "cleaning",
            "lawn care", "pool service", "chimney", "gutter cleaning",
            "window cleaning", "carpet cleaning",
        }
        industry_lower = (self.config.industry or "").lower()
        service_lower_check = service.lower()

        is_recurring = (
            industry_lower in recurring_industries
            or service_lower_check in recurring_industries
            or any(s in service_lower_check for s in recurring_industries)
        )

        if is_recurring:
            body_4 = self._fill_merge_fields(
                (
                    f"Hi {first_name},\n\n"
                    f"It has been about 3 months since your {service} on {job_date}. "
                    "Depending on your setup, it may be time for a maintenance check-up.\n\n"
                    "Regular maintenance keeps everything running smoothly and helps "
                    "you avoid surprise repairs. As a returning customer, we would like "
                    "to offer you priority scheduling.\n\n"
                    "Book your check-up:\n"
                    "{scheduling_url}\n\n"
                    "Or call us at {phone_number}.\n\n"
                    "Looking forward to seeing you again,\n"
                    "{business_name} Team"
                ),
                fields,
            )
            emails.append({
                "delay_days": 90,
                "delay_hours": 0,
                "subject": self._fill_merge_fields(
                    f"Time for a checkup, {first_name}?", fields
                ),
                "body_html": body_4,
                "body_text": "",
                "cta_text": "Schedule your check-up",
                "cta_url": self.config.scheduling_url,
            })

        return emails

    def _select_review_platform(
        self, available_platforms: Dict[str, str]
    ) -> str:
        """Prioritise Google > Yelp > Facebook > first available."""
        for platform in ("google", "yelp", "facebook"):
            if platform in available_platforms:
                return available_platforms[platform]
        if available_platforms:
            return next(iter(available_platforms.values()))
        return ""


# ============================================================================
# QuarterlyRepeatReminder
# ============================================================================


class QuarterlyRepeatReminder(SequenceBuilder):
    """Builds seasonal/quarterly maintenance reminder sequences."""

    @property
    def builder_type(self) -> str:
        return "quarterly_repeat_reminder"

    def build(  # type: ignore[override]
        self,
        customer_name: str,
        customer_email: str,
        service_type: str,
        last_service_date: str,
    ) -> BuiltSequence:
        return super().build(
            customer_name=customer_name,
            customer_email=customer_email,
            service_type=service_type,
            last_service_date=last_service_date,
            template_id="local_service_seasonal",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["customer_name"]
        first_name = name.split()[0] if name else "there"
        service_type = kwargs["service_type"]
        last_date = kwargs["last_service_date"]

        reminder_date = self._calculate_reminder_date(last_date, service_type)

        fields = self._build_merge_fields(
            first_name=first_name,
            customer_name=name,
            service_type=service_type,
            last_service_date=last_date,
        )

        months_since = self._months_between(last_date)

        emails: List[Dict[str, Any]] = []

        # Email 1 -- Reminder
        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"It has been about {months_since} months since your last "
                f"{service_type} service. Regular maintenance helps prevent "
                "costly emergencies and keeps everything running smoothly.\n\n"
                "As a returning customer, you get priority scheduling. "
                "Book your spot before the calendar fills up:\n"
                "{scheduling_url}\n\n"
                "Or call us at {phone_number}.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 0,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"It's been {months_since} months -- time for {service_type}?", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Schedule your service",
            "cta_url": self.config.scheduling_url,
        })

        # Email 2 -- Follow-up (7 days later)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"A quick reminder about your {service_type} maintenance. "
                "Our schedule is filling up, and we want to make sure you are "
                "taken care of before availability tightens.\n\n"
                "Book now to avoid the wait:\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 7,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Don't forget: your {service_type} checkup", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Book now",
            "cta_url": self.config.scheduling_url,
        })

        # Email 3 -- Last chance (14 days later)
        body_3 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"This is our last reminder about {service_type} maintenance. "
                "Seasonal demand tends to push wait times out significantly, "
                "so booking now means faster service and better availability.\n\n"
                "Schedule before the busy season hits:\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 14,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Last reminder: {service_type} for your home", fields
            ),
            "body_html": body_3,
            "body_text": "",
            "cta_text": "Schedule before busy season",
            "cta_url": self.config.scheduling_url,
        })

        return emails

    def _calculate_reminder_date(
        self, last_service_date: str, service_type: str
    ) -> str:
        """Calculate when to send the reminder based on the service cycle."""
        try:
            dt = datetime.strptime(last_service_date[:10], "%Y-%m-%d")
        except ValueError:
            dt = datetime.utcnow()

        key = service_type.lower().strip()
        months = SERVICE_REMINDER_CYCLES.get(key, 12)

        # Also try partial matches
        if key not in SERVICE_REMINDER_CYCLES:
            for svc, m in SERVICE_REMINDER_CYCLES.items():
                if svc in key or key in svc:
                    months = m
                    break

        reminder_dt = dt + timedelta(days=months * 30)
        return reminder_dt.strftime("%Y-%m-%d")

    def _months_between(self, date_str: str) -> int:
        """Rough month count between *date_str* and now."""
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            return 3
        delta = datetime.utcnow() - dt
        return max(1, int(delta.days / 30))


# ============================================================================
# DormantLeadFollowUp
# ============================================================================


class DormantLeadFollowUp(SequenceBuilder):
    """Builds re-engagement sequences for leads that went cold.

    Key principle: lead with VALUE, not "just checking in".
    Never uses banned follow-up phrases.
    """

    @property
    def builder_type(self) -> str:
        return "dormant_lead_follow_up"

    def build(  # type: ignore[override]
        self,
        lead_name: str,
        lead_email: str,
        original_inquiry: str,
        days_since_contact: int,
    ) -> BuiltSequence:
        return super().build(
            lead_name=lead_name,
            customer_name=lead_name,
            lead_email=lead_email,
            customer_email=lead_email,
            original_inquiry=original_inquiry,
            days_since_contact=days_since_contact,
            template_id="local_service_dormant",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["lead_name"]
        first_name = name.split()[0] if name else "there"
        inquiry = kwargs["original_inquiry"]
        days_since = kwargs["days_since_contact"]
        industry = self.config.industry or inquiry

        fields = self._build_merge_fields(
            first_name=first_name,
            lead_name=name,
            original_inquiry=inquiry,
            industry=industry,
            service_type=inquiry,
        )

        # Tone adaptation: softer re-intro for very cold leads
        greeting_tone = "warm" if days_since > 90 else "friendly"

        emails: List[Dict[str, Any]] = []

        # Email 1 -- Value-first re-engagement (Day 0)
        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"We put together a quick {industry} tip that we thought you "
                f"might find useful, especially given your interest in {inquiry}.\n\n"
                f"Here it is: Most people wait until something breaks before they "
                f"look into {inquiry} options. By planning ahead, you avoid "
                "emergency pricing, get better scheduling options, and can compare "
                "quotes without time pressure.\n\n"
                "If you have a few minutes, map out your timeline and budget "
                "before you need the work done. That single step puts you in a "
                "much stronger position.\n\n"
                "Reply if you have any questions -- happy to share more.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 0,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"{first_name}, a helpful {industry} tip", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Reply if you have any questions",
            "cta_url": None,
        })

        # Email 2 -- Social proof (Day 7)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"A recent {inquiry} customer shared their experience with "
                "{business_name}, and we thought it might be relevant to you:\n\n"
                f"\"I had been putting off {inquiry} for months. "
                "{business_name} made the process simple -- clear quote, "
                "on-time arrival, quality work. Wish I had called sooner.\"\n\n"
                "Every situation is different, but the pattern is consistent: "
                "customers who plan ahead get better results and lower costs.\n\n"
                "If you are ready to revisit your {inquiry} project, we are here:\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 7,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"See what a {inquiry} customer said about {{business_name}}", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Ready to get started?",
            "cta_url": self.config.scheduling_url,
        })

        # Email 3 -- Direct offer (Day 14)
        kaicalls_line = ""
        if self.config.kaicalls_enabled and self.config.kaicalls_phone:
            kaicalls_line = (
                f"\n\nYou can also call us anytime at {self.config.kaicalls_phone} "
                "-- our team is available around the clock."
            )

        offer_line = ""
        if self.config.referral_offer:
            offer_line = f"\n\nAs an extra incentive: {self.config.referral_offer} for returning leads."

        body_3 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"We wanted to offer you something exclusive as someone who "
                f"has shown interest in {inquiry}.\n\n"
                f"For a limited time, we are extending a special rate to "
                f"returning inquiries for {inquiry} service. "
                f"This is our way of saying we appreciate your interest "
                f"and would love to earn your business.{offer_line}{kaicalls_line}\n\n"
                "Claim your offer:\n"
                "{scheduling_url}\n\n"
                "Or call {phone_number} to discuss your project.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 14,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"A special offer for you, {first_name}", fields
            ),
            "body_html": body_3,
            "body_text": "",
            "cta_text": "Claim your offer",
            "cta_url": self.config.scheduling_url,
        })

        return emails


# ============================================================================
# QuoteFollowUp
# ============================================================================


class QuoteFollowUp(SequenceBuilder):
    """Builds escalating follow-up sequences for sent quotes/proposals."""

    @property
    def builder_type(self) -> str:
        return "quote_follow_up"

    def build(  # type: ignore[override]
        self,
        lead_name: str,
        lead_email: str,
        quote_details: Dict[str, Any],
        quote_date: str,
    ) -> BuiltSequence:
        return super().build(
            lead_name=lead_name,
            customer_name=lead_name,
            lead_email=lead_email,
            customer_email=lead_email,
            quote_details=quote_details,
            quote_date=quote_date,
            template_id="local_service_quote_followup",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["lead_name"]
        first_name = name.split()[0] if name else "there"
        details = kwargs["quote_details"]
        quote_date = kwargs["quote_date"]

        service = details.get("service", "service")
        amount = details.get("amount", 0)
        items = details.get("items", [])
        expiry_date = details.get("expiry_date", "soon")

        amount_str = format_currency(amount) if amount else "[quote amount]"
        items_str = ", ".join(items) if items else service

        fields = self._build_merge_fields(
            first_name=first_name,
            lead_name=name,
            service=service,
            service_type=service,
            amount=amount_str,
            quote_amount=amount_str,
            quote_date=quote_date,
            items=items_str,
            expiry_date=expiry_date,
            expiry_info=f"on {expiry_date}" if expiry_date != "soon" else "soon",
        )

        emails: List[Dict[str, Any]] = []

        # Email 1 -- Gentle check-in (Day 2)
        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"We sent over your {service} quote on {quote_date} and wanted "
                "to see if you had any questions.\n\n"
                "We know there is a lot to consider, and we are happy to walk "
                "through the details or adjust the scope to fit your needs. "
                "No pressure at all -- we just want to make sure you have "
                "everything you need to make a decision.\n\n"
                "Reply to this email or call {phone_number} anytime.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 2,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Any questions about your {service} quote, {first_name}?", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Reply with any questions",
            "cta_url": None,
        })

        # Email 2 -- Value reinforcement (Day 5)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"We wanted to share more about what is included in your "
                f"{amount_str} {service} quote so you can see the full picture.\n\n"
                "Your quote covers:\n"
                f"- {items_str}\n"
                "- All materials and labour included -- no surprise add-ons\n"
                "- A satisfaction guarantee: if the work is not right, we come back at no charge\n"
                "- Post-service follow-up to make sure everything holds up\n\n"
                "We stand behind every job with our reputation and years of experience.\n\n"
                "Ready to move ahead? Book your appointment:\n"
                "{scheduling_url}\n\n"
                "Or call {phone_number} to discuss.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 5,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"What's included in your {amount_str} {service} quote", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Ready to proceed?",
            "cta_url": self.config.scheduling_url,
        })

        # Email 3 -- Social proof (Day 7)
        body_3 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"You are not the only one considering {service} options. "
                "Here is what a few recent customers had to say:\n\n"
                "\"Showed up on time, did exactly what they promised, and the "
                "price matched the quote. Refreshing.\"\n\n"
                "\"{business_name} was the most transparent about what was "
                "included. No hidden fees, no surprises.\"\n\n"
                "\"The team was professional and cleaned up after themselves. "
                "Already recommended them to my neighbors.\"\n\n"
                "We would love to earn the same kind of feedback from you.\n\n"
                "Ready to get started?\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 7,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"What our {service} clients say about us", fields
            ),
            "body_html": body_3,
            "body_text": "",
            "cta_text": "Join our satisfied customers",
            "cta_url": self.config.scheduling_url,
        })

        # Email 4 -- Urgency (Day 10)
        body_4 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"Your {amount_str} {service} quote from {quote_date} is "
                f"expiring {expiry_date}. We wanted to give you a heads-up "
                "before it does.\n\n"
                "A few things to keep in mind:\n"
                "- Material costs can change, so we may not be able to hold this price.\n"
                "- Our schedule fills up fast, especially during peak season.\n"
                f"- Waiting on {service} can lead to bigger (and more expensive) issues.\n\n"
                "Locking in your price is easy -- just reply, book at "
                "{scheduling_url}, or call {phone_number}.\n\n"
                "We hope to work with you, {first_name}.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 10,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Your {service} quote expires {{expiry_info}}", fields
            ),
            "body_html": body_4,
            "body_text": "",
            "cta_text": "Lock in your price",
            "cta_url": self.config.scheduling_url,
        })

        return emails


# ============================================================================
# ReferralEngine
# ============================================================================


class ReferralEngine(SequenceBuilder):
    """Builds referral-ask sequences for satisfied customers."""

    @property
    def builder_type(self) -> str:
        return "referral_engine"

    def build(  # type: ignore[override]
        self,
        customer_name: str,
        customer_email: str,
        service_history: List[Dict[str, Any]],
    ) -> BuiltSequence:
        return super().build(
            customer_name=customer_name,
            customer_email=customer_email,
            service_history=service_history,
            template_id="local_service_post_job",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["customer_name"]
        first_name = name.split()[0] if name else "there"
        service_history = kwargs.get("service_history", [])

        latest_service = service_history[-1]["service"] if service_history else "service"
        personalised_ask = self._personalize_ask(service_history)

        fields = self._build_merge_fields(
            first_name=first_name,
            customer_name=name,
            service=latest_service,
            service_type=latest_service,
        )

        emails: List[Dict[str, Any]] = []

        # Email 1 -- The Ask (Day 0)
        offer_line = ""
        if self.config.referral_offer:
            offer_line = (
                f"\n\nAs a thank-you, we are offering {self.config.referral_offer} "
                "for every referral who books a service."
            )

        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"{personalised_ask}\n\n"
                f"If you know a friend, neighbor, or family member who needs "
                f"{latest_service}, we would love an introduction.{offer_line}\n\n"
                "Sharing is easy: just reply with their name and phone number, "
                "forward this email, or use this link:\n"
                "{referral_link}\n\n"
                "We will take care of the rest.\n\n"
                "Cheers,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 0,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"{first_name}, know someone who needs {latest_service}?", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Reply with a referral",
            "cta_url": self.config.referral_link,
        })

        # Email 2 -- The Reminder (Day 14)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                "Your referral offer is still available. If someone you know "
                f"needs {latest_service}, we would be grateful for the introduction.\n\n"
                "It is easy: reply with their name, forward this email, "
                "or share your referral link:\n"
                "{referral_link}\n\n"
                "Your friend will thank you, and so will we.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 14,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Your referral offer is still available, {first_name}", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Share your referral link",
            "cta_url": self.config.referral_link,
        })

        # Email 3 -- Thank You (triggered after referral, not timed)
        body_3 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                "Thank you so much for the referral. We truly appreciate your "
                "trust in {business_name}, and we will take great care of "
                "your friend.\n\n"
            ),
            fields,
        )
        if self.config.referral_offer:
            body_3 += self._fill_merge_fields(
                "Your {referral_offer} will be applied to your next service. "
                "We will be in touch with the details.\n\n",
                fields,
            )
        body_3 += self._fill_merge_fields(
            "Thank you again -- referrals are the highest compliment we can receive.\n\n"
            "Warm regards,\n"
            "{business_name} Team",
            fields,
        )
        emails.append({
            "delay_days": 0,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Thank you for the referral, {first_name}!", fields
            ),
            "body_html": body_3,
            "body_text": "",
            "cta_text": "",
            "cta_url": None,
        })

        return emails

    def _personalize_ask(
        self, service_history: List[Dict[str, Any]]
    ) -> str:
        """Generate a personalised opening for the referral ask."""
        if not service_history:
            return "We appreciate your business and hope we exceeded your expectations."

        count = len(service_history)
        latest = service_history[-1]
        service = latest.get("service", "service")
        satisfaction = latest.get("satisfaction")

        if count >= 3:
            return (
                f"As one of our most loyal customers with {count} services on the books, "
                "your opinion carries real weight in our community."
            )

        if satisfaction and satisfaction.lower() in ("excellent", "great", "5", "5/5"):
            return (
                f"We are thrilled that your recent {service} exceeded expectations. "
                "That kind of feedback keeps our team motivated."
            )

        return (
            f"We hope you were happy with your recent {service}. "
            "Your satisfaction is what drives us."
        )


# ============================================================================
# MaintenanceReorderCadence
# ============================================================================


class MaintenanceReorderCadence(SequenceBuilder):
    """Builds replenishment/reorder reminder sequences based on product lifecycle."""

    @property
    def builder_type(self) -> str:
        return "maintenance_reorder_cadence"

    def build(  # type: ignore[override]
        self,
        customer_name: str,
        customer_email: str,
        product_or_service: str,
        expected_lifecycle_days: int,
        last_purchase_date: str,
    ) -> BuiltSequence:
        return super().build(
            customer_name=customer_name,
            customer_email=customer_email,
            product_or_service=product_or_service,
            expected_lifecycle_days=expected_lifecycle_days,
            last_purchase_date=last_purchase_date,
            template_id="ecommerce_replenishment",
        )

    def _generate_emails(self, **kwargs: Any) -> List[Dict[str, Any]]:
        name = kwargs["customer_name"]
        first_name = name.split()[0] if name else "there"
        product = kwargs["product_or_service"]
        lifecycle_days = kwargs.get("expected_lifecycle_days") or self._determine_lifecycle(product)
        last_date = kwargs["last_purchase_date"]

        reorder_date = calculate_reorder_date(last_date, lifecycle_days)

        fields = self._build_merge_fields(
            first_name=first_name,
            customer_name=name,
            product_or_service=product,
            product_name=product,
            last_purchase_date=last_date,
            reorder_date=reorder_date,
        )

        # Delays are relative to when the sequence starts, which should be
        # lifecycle_days - 7 after purchase
        emails: List[Dict[str, Any]] = []

        # Email 1 -- Early reminder (lifecycle - 7 days)
        body_1 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"Based on your last order on {last_date}, you might be running "
                f"low on {product}. Most of our customers reorder around this time.\n\n"
                "Restocking now means no gap in your routine:\n"
                "{scheduling_url}\n\n"
                "Running out can mean inconsistent results, so we wanted to "
                "give you a heads-up while there is still time.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 0,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Time to reorder your {product}?", fields
            ),
            "body_html": body_1,
            "body_text": "",
            "cta_text": "Reorder now",
            "cta_url": self.config.scheduling_url,
        })

        # Email 2 -- Due date (7 days later = lifecycle day)
        body_2 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"Your {product} should be running out right about now. "
                "Reordering today means no gap in your routine.\n\n"
                f"A consistent {product} schedule keeps results on track. "
                "Skipping can set you back.\n\n"
                "Restock here: {scheduling_url}\n\n"
                "We ship fast so you will have it before you run out.\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 7,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Your {product} is due for replacement", fields
            ),
            "body_html": body_2,
            "body_text": "",
            "cta_text": "Reorder today",
            "cta_url": self.config.scheduling_url,
        })

        # Email 3 -- Overdue (lifecycle + 7 days)
        body_3 = self._fill_merge_fields(
            (
                f"Hi {first_name},\n\n"
                f"You are past the typical reorder window for {product}. "
                "If you haven't restocked yet, now is a good time.\n\n"
                "Skipping can mean inconsistent results and having to restart "
                "your routine from scratch. A quick reorder keeps things on track:\n"
                "{scheduling_url}\n\n"
                "Best,\n"
                "{business_name} Team"
            ),
            fields,
        )
        emails.append({
            "delay_days": 14,
            "delay_hours": 0,
            "subject": self._fill_merge_fields(
                f"Don't forget: your {product} needs attention", fields
            ),
            "body_html": body_3,
            "body_text": "",
            "cta_text": "Act today",
            "cta_url": self.config.scheduling_url,
        })

        return emails

    def _determine_lifecycle(self, product_or_service: str) -> int:
        """Return the default lifecycle period in days for a product/service.

        Falls back to 90 days if the product is not in the lookup table.
        """
        key = product_or_service.lower().strip().replace(" ", "_")
        if key in DEFAULT_LIFECYCLES:
            return DEFAULT_LIFECYCLES[key]
        # Try partial match
        for product_key, days in DEFAULT_LIFECYCLES.items():
            if product_key in key or key in product_key:
                return days
        return 90  # default

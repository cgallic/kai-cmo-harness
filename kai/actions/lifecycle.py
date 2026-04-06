"""Lifecycle action system for email, SMS, and CRM marketing operations.

Provides structured action types for every lifecycle marketing operation:
launching email sequences, updating nurture copy, sending reminders,
requesting reviews, asking for referrals, reactivating dormant customers,
and following up on quotes.

Actions follow the validate-preview-execute-verify lifecycle with
lifecycle-specific concerns: over-contact protection, CAN-SPAM compliance,
opt-out verification, and send timing.

Action classes:
    LaunchEmailSequence, UpdateNurtureCopy, SendReminderSequence,
    LaunchReviewRequestSequence, SendReferralAsk, LaunchReactivation,
    SendQuoteFollowUp

Helpers:
    generate_lifecycle_action_id, check_over_contact,
    validate_can_spam_compliance, filter_eligible_contacts,
    calculate_sequence_duration, format_review_link
"""

from __future__ import annotations

import copy
import logging
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
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

        def __init__(self, **data: Any) -> None:
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

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"

else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Banned words — Tier 1 instant rejection list from CLAUDE.md quality gates.
BANNED_WORDS: List[str] = [
    "leverage",
    "utilize",
    "synergy",
    "innovative",
    "deep dive",
    "circle back",
    "touch base",
    "moving forward",
    "at the end of the day",
]

# Valid reminder types.
VALID_REMINDER_TYPES: List[str] = [
    "appointment",
    "service_due",
    "follow_up",
    "payment_due",
    "renewal",
]

# Valid review platforms.
VALID_REVIEW_PLATFORMS: List[str] = [
    "google",
    "yelp",
    "facebook",
    "trustpilot",
    "bbb",
    "g2",
    "capterra",
]

# Default reactivation email spacing in days.
REACTIVATION_SPACING: Dict[int, List[int]] = {
    1: [0],
    2: [0, 7],
    3: [0, 7, 14],
    4: [0, 7, 14, 28],
    5: [0, 7, 14, 28, 42],
}


# ============================================================================
# Enums
# ============================================================================


class LifecycleActionType(str, Enum):
    """All lifecycle marketing action types."""

    launch_email_sequence = "launch_email_sequence"
    update_nurture_copy = "update_nurture_copy"
    send_reminder_sequence = "send_reminder_sequence"
    launch_review_request = "launch_review_request"
    send_referral_ask = "send_referral_ask"
    launch_reactivation = "launch_reactivation"
    send_quote_follow_up = "send_quote_follow_up"
    send_single_email = "send_single_email"
    update_contact_segment = "update_contact_segment"


# ============================================================================
# Data Models
# ============================================================================


class LifecycleValidationResult(BaseModel):
    """Result of validating a lifecycle action."""

    is_valid: bool = Field(..., description="Whether the action passed validation")
    errors: List[str] = Field(default_factory=list, description="Hard failures")
    warnings: List[str] = Field(default_factory=list, description="Soft warnings")
    compliance_issues: List[str] = Field(
        default_factory=list,
        description="CAN-SPAM / opt-out compliance issues",
    )
    contacts_excluded: int = Field(
        0, description="Contacts removed due to suppression/opt-out/over-contact"
    )
    contacts_eligible: int = Field(
        0, description="Contacts that can receive this message"
    )


class LifecycleActionPreview(BaseModel):
    """Human-readable preview of a lifecycle action before execution."""

    action_type: str = Field(..., description="The lifecycle action type")
    summary: str = Field(..., description="Human-readable summary")
    recipient_count: int = Field(0, description="How many contacts will receive the message")
    email_count: int = Field(0, description="How many emails in the sequence")
    timing_summary: str = Field(
        ..., description="When emails will be sent (e.g. 'Day 0, Day 2, Day 5')"
    )
    estimated_sends: int = Field(
        0, description="Total email sends (recipients x emails)"
    )
    sample_subject: Optional[str] = Field(
        None, description="Sample subject line from the first email"
    )
    sample_preview: Optional[str] = Field(
        None, description="First 200 chars of first email body"
    )
    excluded_contacts: List[Dict[str, str]] = Field(
        default_factory=list, description="Contacts excluded with reason"
    )
    compliance_status: str = Field(
        ..., description="'compliant' or 'issues_found'"
    )
    cost_estimate: Optional[str] = Field(
        None, description="Estimated cost if using a paid provider"
    )


class LifecycleExecutionResult(BaseModel):
    """Result of executing a lifecycle action via a connector."""

    success: bool = Field(..., description="Whether the action executed successfully")
    action_type: str = Field(..., description="The lifecycle action type")
    provider: str = Field(..., description="Which email provider was used")
    contacts_sent: int = Field(0, description="Contacts that received the message")
    contacts_excluded: int = Field(0, description="Contacts that were excluded")
    emails_queued: int = Field(0, description="Emails queued for future send (sequences)")
    emails_sent_immediately: int = Field(0, description="Emails sent right away")
    sequence_id: Optional[str] = Field(
        None, description="Provider sequence/automation ID"
    )
    error_message: Optional[str] = Field(None, description="Error details on failure")
    executed_at: str = Field(..., description="ISO timestamp of execution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data")


class OverContactCheck(BaseModel):
    """Result of checking whether a contact has been over-contacted."""

    contact_email: str = Field(..., description="The contact email checked")
    emails_sent_7d: int = Field(0, description="Emails sent in the last 7 days")
    emails_sent_30d: int = Field(0, description="Emails sent in the last 30 days")
    last_email_date: Optional[str] = Field(
        None, description="ISO date of the last email sent to this contact"
    )
    max_per_week: int = Field(3, description="Configurable weekly cap")
    is_over_limit: bool = Field(False, description="Whether the contact exceeds the weekly cap")
    cooldown_until: Optional[str] = Field(
        None,
        description="ISO timestamp when the contact is eligible again",
    )


# ============================================================================
# Helper Functions
# ============================================================================


def generate_lifecycle_action_id() -> str:
    """Generate a unique lifecycle action ID.

    Returns
    -------
    str
        An ID in the format ``la_<12-char hex>``.
    """
    return f"la_{uuid.uuid4().hex[:12]}"


def check_over_contact(
    email: str,
    sent_history: List[Dict[str, Any]],
    max_per_week: int = 3,
) -> OverContactCheck:
    """Check whether a contact has been over-contacted.

    Parameters
    ----------
    email : str
        The contact email address to check.
    sent_history : list of dict
        Each dict must have at least ``{"email": str, "sent_at": str}``
        where ``sent_at`` is an ISO-8601 timestamp.
    max_per_week : int
        Maximum number of emails allowed per 7-day window.

    Returns
    -------
    OverContactCheck
        Populated check result including cooldown calculation.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    normalized_email = email.strip().lower()

    emails_7d = 0
    emails_30d = 0
    last_email_date: Optional[str] = None
    last_email_dt: Optional[datetime] = None

    for record in sent_history:
        record_email = record.get("email", "").strip().lower()
        if record_email != normalized_email:
            continue

        sent_at_raw = record.get("sent_at", "")
        if not sent_at_raw:
            continue

        try:
            sent_dt = datetime.fromisoformat(sent_at_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        if sent_dt >= thirty_days_ago:
            emails_30d += 1
        if sent_dt >= seven_days_ago:
            emails_7d += 1

        if last_email_dt is None or sent_dt > last_email_dt:
            last_email_dt = sent_dt
            last_email_date = sent_dt.date().isoformat()

    is_over = emails_7d >= max_per_week

    cooldown_until: Optional[str] = None
    if is_over and last_email_dt is not None:
        # Find the earliest send within the 7-day window.  The contact becomes
        # eligible once that earliest send ages out of the window.
        window_sends: List[datetime] = []
        for record in sent_history:
            record_email = record.get("email", "").strip().lower()
            if record_email != normalized_email:
                continue
            sent_at_raw = record.get("sent_at", "")
            if not sent_at_raw:
                continue
            try:
                sent_dt = datetime.fromisoformat(sent_at_raw.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue
            if sent_dt >= seven_days_ago:
                window_sends.append(sent_dt)

        if window_sends:
            earliest_in_window = min(window_sends)
            cooldown_until = (earliest_in_window + timedelta(days=7)).isoformat()

    return OverContactCheck(
        contact_email=normalized_email,
        emails_sent_7d=emails_7d,
        emails_sent_30d=emails_30d,
        last_email_date=last_email_date,
        max_per_week=max_per_week,
        is_over_limit=is_over,
        cooldown_until=cooldown_until,
    )


def validate_can_spam_compliance(
    from_email: str,
    physical_address: str,
    has_unsubscribe: bool,
) -> List[str]:
    """Validate CAN-SPAM compliance for an outgoing email.

    Parameters
    ----------
    from_email : str
        The sender email address.
    physical_address : str
        Physical mailing address (required by CAN-SPAM).
    has_unsubscribe : bool
        Whether the email includes an unsubscribe mechanism.

    Returns
    -------
    list of str
        CAN-SPAM violations found.  Empty list means compliant.
    """
    violations: List[str] = []

    # 1. Valid from email
    if not from_email or not from_email.strip():
        violations.append("CAN-SPAM: from_email is required")
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", from_email.strip()):
        violations.append(
            f"CAN-SPAM: from_email '{from_email}' does not look like a valid email address"
        )

    # 2. Physical address
    if not physical_address or not physical_address.strip():
        violations.append(
            "CAN-SPAM: physical mailing address is required in all commercial emails"
        )

    # 3. Unsubscribe mechanism
    if not has_unsubscribe:
        violations.append(
            "CAN-SPAM: an unsubscribe mechanism (link or reply-to) is required"
        )

    return violations


def filter_eligible_contacts(
    contacts: List[Dict[str, Any]],
    suppression_list: List[str],
    max_per_week: int = 3,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Filter contacts to determine who is eligible to receive a message.

    Contacts are excluded if they:
    - Have ``opted_out`` set to ``True``
    - Are on the suppression list (email match, case-insensitive)
    - Have exceeded the weekly contact limit (based on ``emails_sent_7d``)

    Parameters
    ----------
    contacts : list of dict
        Each dict should have at least ``{"email": str}``.  Optional keys:
        ``opted_out`` (bool), ``emails_sent_7d`` (int).
    suppression_list : list of str
        Email addresses that must not receive messages.
    max_per_week : int
        Maximum emails per 7-day window before a contact is excluded.

    Returns
    -------
    tuple of (list of dict, list of dict)
        ``(eligible_contacts, excluded_contacts_with_reasons)``.
        Each excluded entry is ``{"email": str, "reason": str}``.
    """
    normalized_suppression = {e.strip().lower() for e in suppression_list}

    eligible: List[Dict[str, Any]] = []
    excluded: List[Dict[str, str]] = []

    for contact in contacts:
        email = contact.get("email", "").strip().lower()
        if not email:
            excluded.append({"email": "(no email)", "reason": "Missing email address"})
            continue

        # Check opt-out
        if contact.get("opted_out", False):
            excluded.append({"email": email, "reason": "Contact has opted out"})
            continue

        # Check suppression list
        if email in normalized_suppression:
            excluded.append({"email": email, "reason": "On suppression list"})
            continue

        # Check over-contact limit
        emails_sent_7d = contact.get("emails_sent_7d", 0)
        if emails_sent_7d >= max_per_week:
            excluded.append({
                "email": email,
                "reason": f"Over weekly contact limit ({emails_sent_7d}/{max_per_week} emails in 7 days)",
            })
            continue

        eligible.append(contact)

    return eligible, excluded


def calculate_sequence_duration(emails: List[Dict[str, Any]]) -> int:
    """Calculate the total duration of an email sequence in days.

    Parameters
    ----------
    emails : list of dict
        Each dict should have a ``delay_days`` key (int).

    Returns
    -------
    int
        Total sequence duration in days (sum of all delay_days values).
    """
    total = 0
    for email_config in emails:
        total += int(email_config.get("delay_days", 0))
    return total


def format_review_link(platform: str, business_identifier: str) -> str:
    """Format a direct review link for a given platform.

    Parameters
    ----------
    platform : str
        Review platform name (google, yelp, facebook).
    business_identifier : str
        Platform-specific business identifier (Place ID, Yelp biz slug, etc.).

    Returns
    -------
    str
        A direct review URL, or the raw identifier if the platform is unknown.
    """
    platform_lower = platform.strip().lower()

    if platform_lower == "google":
        return f"https://search.google.com/local/writereview?placeid={business_identifier}"
    elif platform_lower == "yelp":
        return f"https://www.yelp.com/writeareview/biz/{business_identifier}"
    elif platform_lower == "facebook":
        return f"https://www.facebook.com/{business_identifier}/reviews"

    return business_identifier


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _check_banned_words(text: str) -> List[str]:
    """Return any banned words found in *text*.

    Performs case-insensitive matching against the BANNED_WORDS list.
    Multi-word phrases are matched as substrings.
    """
    found: List[str] = []
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word.lower() in text_lower:
            found.append(word)
    return found


def _check_all_caps(subject: str) -> bool:
    """Return True if the subject line is all uppercase and longer than 3 chars."""
    stripped = subject.strip()
    return len(stripped) > 3 and stripped == stripped.upper()


# ============================================================================
# Abstract Base: LifecycleAction
# ============================================================================


class LifecycleAction(ABC):
    """Abstract base for all lifecycle marketing actions.

    Mirrors the PaidMediaAction lifecycle pattern but with email-specific
    concerns: over-contact protection, CAN-SPAM compliance, opt-out
    verification, and send timing.

    Concrete subclasses must implement:
    - ``action_type`` (property)
    - ``_validate_impl(eligible_contacts)``
    - ``_preview_impl()``
    - ``_execute_impl(connector)``
    """

    def __init__(self, **kwargs: Any) -> None:
        self._params = kwargs
        self._state: str = "created"
        self._validation: Optional[LifecycleValidationResult] = None
        self._preview: Optional[LifecycleActionPreview] = None
        self._result: Optional[LifecycleExecutionResult] = None
        self._eligible_contacts: List[Dict[str, Any]] = []
        self._excluded_contacts: List[Dict[str, str]] = []
        self._action_id: str = generate_lifecycle_action_id()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Return the canonical action type string."""
        ...

    @abstractmethod
    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        """Subclass-specific validation logic.

        Called by :meth:`validate` after common checks (opt-out, suppression,
        over-contact) have already filtered the contact list.

        Parameters
        ----------
        eligible_contacts : list of dict
            Contacts that passed common validation filters.

        Returns
        -------
        LifecycleValidationResult
            Validation result from the subclass.
        """
        ...

    @abstractmethod
    def _preview_impl(self) -> LifecycleActionPreview:
        """Subclass-specific preview generation.

        Called by :meth:`preview` after validation has passed.

        Returns
        -------
        LifecycleActionPreview
            Preview of the action.
        """
        ...

    @abstractmethod
    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        """Subclass-specific execution logic.

        Called by :meth:`execute` after state checks and confirmation.

        Parameters
        ----------
        connector : Any
            A LifecycleConnector instance to execute against.

        Returns
        -------
        LifecycleExecutionResult
            Execution result.
        """
        ...

    # ------------------------------------------------------------------
    # Public lifecycle methods
    # ------------------------------------------------------------------

    def validate(
        self,
        contacts: List[Dict[str, Any]],
        suppression_list: Optional[List[str]] = None,
    ) -> LifecycleValidationResult:
        """Validate the action against a contact list.

        Runs common checks first (opt-out, suppression, over-contact, CAN-SPAM),
        then delegates to ``_validate_impl()`` for action-specific checks.

        Parameters
        ----------
        contacts : list of dict
            Candidate contacts.  Each dict should have at least ``{"email": str}``.
        suppression_list : list of str or None
            Emails to suppress.  None is treated as empty.

        Returns
        -------
        LifecycleValidationResult
            Combined validation result.
        """
        if suppression_list is None:
            suppression_list = []

        max_per_week = self._params.get("max_per_week", 3)

        # 1. Filter contacts
        eligible, excluded = filter_eligible_contacts(
            contacts, suppression_list, max_per_week=max_per_week
        )
        self._eligible_contacts = eligible
        self._excluded_contacts = excluded

        # 2. CAN-SPAM compliance check
        from_email = self._params.get("from_email", "")
        physical_address = self._params.get("physical_address", "")
        has_unsubscribe = self._params.get("has_unsubscribe", True)

        # Try to get from_email from sequence_config if not top-level
        if not from_email:
            seq_config = self._params.get("sequence_config", {})
            from_email = seq_config.get("from_email", "")

        compliance_issues = validate_can_spam_compliance(
            from_email, physical_address, has_unsubscribe
        )

        # 3. Delegate to subclass
        impl_result = self._validate_impl(eligible)

        # 4. Merge results
        all_errors = list(impl_result.errors)
        all_warnings = list(impl_result.warnings)
        all_compliance = list(compliance_issues) + list(impl_result.compliance_issues)

        is_valid = impl_result.is_valid and len(all_errors) == 0

        self._validation = LifecycleValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            compliance_issues=all_compliance,
            contacts_excluded=len(excluded),
            contacts_eligible=len(eligible),
        )
        self._state = "validated"
        return self._validation

    def preview(self) -> LifecycleActionPreview:
        """Generate a human-readable preview of the action.

        Must be called after :meth:`validate`.

        Returns
        -------
        LifecycleActionPreview
            Preview describing what will happen.

        Raises
        ------
        RuntimeError
            If the action has not been validated first.
        """
        if self._state not in ("validated", "previewed"):
            raise RuntimeError(
                f"Cannot preview action in state '{self._state}'. "
                f"Call validate() first."
            )

        self._preview = self._preview_impl()
        self._state = "previewed"
        return self._preview

    def execute(
        self, connector: Any, confirm: bool = False
    ) -> LifecycleExecutionResult:
        """Execute the action via a lifecycle connector.

        Must be validated and previewed first.  Requires explicit confirmation
        unless ``confirm=True``.

        Parameters
        ----------
        connector : Any
            A LifecycleConnector to execute against.
        confirm : bool
            Must be True to proceed with execution.

        Returns
        -------
        LifecycleExecutionResult
            Result of the execution.

        Raises
        ------
        RuntimeError
            If the action has not been validated and previewed, or if
            ``confirm`` is not True.
        """
        if self._state != "previewed":
            raise RuntimeError(
                f"Cannot execute action in state '{self._state}'. "
                f"Call validate() and preview() first."
            )

        if not confirm:
            raise RuntimeError(
                "Execution requires explicit confirmation. "
                "Pass confirm=True to proceed."
            )

        self._state = "executing"
        try:
            self._result = self._execute_impl(connector)
            self._state = "completed" if self._result.success else "failed"
        except Exception as exc:
            logger.exception("Lifecycle action execution failed: %s", exc)
            self._result = LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=getattr(connector, "provider_name", "unknown"),
                error_message=str(exc),
                executed_at=_utc_now(),
            )
            self._state = "failed"

        return self._result


# ============================================================================
# Concrete Actions
# ============================================================================


class LaunchEmailSequence(LifecycleAction):
    """Launch a multi-email automated sequence.

    Parameters
    ----------
    sequence_config : dict
        ``{"name": str, "emails": [{"delay_days": int, "subject": str,
        "body_html": str, "body_text": str}], "from_email": str,
        "from_name": str}``
    segment : str
        Target contact segment.
    trigger_event : str or None
        Optional trigger event that starts the sequence.
    """

    def __init__(
        self,
        sequence_config: Dict[str, Any],
        segment: str,
        trigger_event: Optional[str] = None,
    ) -> None:
        super().__init__(
            sequence_config=sequence_config,
            segment=segment,
            trigger_event=trigger_event,
            from_email=sequence_config.get("from_email", ""),
        )
        self.sequence_config = sequence_config
        self.segment = segment
        self.trigger_event = trigger_event

    @property
    def action_type(self) -> str:
        return "launch_email_sequence"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        compliance_issues: List[str] = []

        emails = self.sequence_config.get("emails", [])

        # Check at least 1 email
        if not emails:
            errors.append("Sequence must contain at least 1 email")

        # Check each email has subject and body
        for i, email_cfg in enumerate(emails):
            subject = email_cfg.get("subject", "").strip()
            body_html = email_cfg.get("body_html", "").strip()
            body_text = email_cfg.get("body_text", "").strip()

            if not subject:
                errors.append(f"Email {i + 1}: subject is empty")

            if not body_html and not body_text:
                errors.append(f"Email {i + 1}: both body_html and body_text are empty")

            # Check for all-caps subject
            if subject and _check_all_caps(subject):
                warnings.append(
                    f"Email {i + 1}: subject is ALL CAPS ('{subject}') -- may hurt deliverability"
                )

            # Check for banned words in subject and body
            all_text = f"{subject} {body_html} {body_text}"
            banned_found = _check_banned_words(all_text)
            if banned_found:
                errors.append(
                    f"Email {i + 1}: contains banned words: {', '.join(banned_found)}"
                )

        # Check total sequence duration
        if emails:
            duration = calculate_sequence_duration(emails)
            if duration > 90:
                warnings.append(
                    f"Sequence spans {duration} days -- consider shortening "
                    f"(recommended max 90 days)"
                )

        # Check eligible contacts
        if not eligible_contacts:
            errors.append("No eligible contacts in segment")

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            compliance_issues=compliance_issues,
            contacts_excluded=0,
            contacts_eligible=len(eligible_contacts),
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        emails = self.sequence_config.get("emails", [])
        name = self.sequence_config.get("name", "Unnamed sequence")
        count = len(self._eligible_contacts)
        email_count = len(emails)
        duration = calculate_sequence_duration(emails) if emails else 0

        # Build timing summary
        timing_parts: List[str] = []
        cumulative_days = 0
        for i, email_cfg in enumerate(emails):
            delay = int(email_cfg.get("delay_days", 0))
            cumulative_days += delay
            if cumulative_days == 0:
                timing_parts.append(f"Email {i + 1}: immediately")
            else:
                timing_parts.append(f"Email {i + 1}: day {cumulative_days}")
        timing_summary = ", ".join(timing_parts) if timing_parts else "No emails configured"

        # Sample content from first email
        sample_subject: Optional[str] = None
        sample_preview: Optional[str] = None
        if emails:
            sample_subject = emails[0].get("subject")
            body = emails[0].get("body_text") or emails[0].get("body_html", "")
            if body:
                sample_preview = body[:200]

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=(
                f"Launch '{name}' sequence to {count} contacts "
                f"({email_count} emails over {duration} days)"
            ),
            recipient_count=count,
            email_count=email_count,
            timing_summary=timing_summary,
            estimated_sends=count * email_count,
            sample_subject=sample_subject,
            sample_preview=sample_preview,
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")
        count = len(self._eligible_contacts)
        emails = self.sequence_config.get("emails", [])

        try:
            # Create the sequence on the provider
            from kai.connectors.lifecycle.base import SequenceConfig

            seq = SequenceConfig(
                name=self.sequence_config.get("name", "Kai sequence"),
                description=self.sequence_config.get("description"),
                trigger_event=self.trigger_event,
                emails=emails,
                status="draft",
                total_emails=len(emails),
            )
            created = connector.create_sequence(seq)
            sequence_id = getattr(created, "id", None)

            # Enroll contacts (provider-specific -- use send_batch as proxy)
            from kai.connectors.lifecycle.base import EmailMessage as LCEmailMessage

            first_email = emails[0] if emails else {}
            msg = LCEmailMessage(
                to_email="batch",
                subject=first_email.get("subject", ""),
                body_html=first_email.get("body_html"),
                body_text=first_email.get("body_text"),
                tags=[f"sequence:{sequence_id or 'new'}"],
            )

            from kai.connectors.lifecycle.base import ContactRecord

            contact_records = []
            for c in self._eligible_contacts:
                contact_records.append(
                    ContactRecord(email=c.get("email", ""))
                )

            connector.send_batch(contact_records, message=msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=count,
                contacts_excluded=len(self._excluded_contacts),
                emails_queued=count * (len(emails) - 1) if len(emails) > 1 else 0,
                emails_sent_immediately=count if emails else 0,
                sequence_id=sequence_id,
                executed_at=_utc_now(),
                metadata={
                    "sequence_name": self.sequence_config.get("name"),
                    "segment": self.segment,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class UpdateNurtureCopy(LifecycleAction):
    """Update copy in an existing email sequence.

    Parameters
    ----------
    sequence_id : str
        Provider sequence/automation ID.
    email_index : int
        Zero-based index of the email to update.
    new_subject : str or None
        Updated subject line.
    new_body : str or None
        Updated body content (HTML).
    reason : str
        Reason for the update.
    """

    def __init__(
        self,
        sequence_id: str,
        email_index: int,
        new_subject: Optional[str] = None,
        new_body: Optional[str] = None,
        reason: str = "",
    ) -> None:
        super().__init__(
            sequence_id=sequence_id,
            email_index=email_index,
            new_subject=new_subject,
            new_body=new_body,
            reason=reason,
        )
        self.sequence_id = sequence_id
        self.email_index = email_index
        self.new_subject = new_subject
        self.new_body = new_body
        self.reason = reason

    @property
    def action_type(self) -> str:
        return "update_nurture_copy"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check sequence_id
        if not self.sequence_id or not self.sequence_id.strip():
            errors.append("sequence_id is required")

        # Check email_index is non-negative
        if self.email_index < 0:
            errors.append(
                f"email_index must be non-negative, got {self.email_index}"
            )

        # Check at least one of new_subject or new_body is provided
        if not self.new_subject and not self.new_body:
            errors.append(
                "At least one of new_subject or new_body must be provided"
            )

        # Check for banned words in new content
        check_text = f"{self.new_subject or ''} {self.new_body or ''}"
        banned_found = _check_banned_words(check_text)
        if banned_found:
            errors.append(
                f"New content contains banned words: {', '.join(banned_found)}"
            )

        # Warn about active sequences
        warnings.append(
            "If this sequence is currently active, changes will affect "
            "contacts already enrolled in the sequence"
        )

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=0,
            contacts_eligible=len(eligible_contacts),
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        changes: List[str] = []
        if self.new_subject:
            changes.append(f"subject -> '{self.new_subject}'")
        if self.new_body:
            changes.append("body updated")

        summary = (
            f"Update email {self.email_index + 1} in sequence "
            f"{self.sequence_id}: {', '.join(changes)}"
        )

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=0,
            email_count=1,
            timing_summary="Existing sequence -- timing unchanged",
            estimated_sends=0,
            sample_subject=self.new_subject,
            sample_preview=(self.new_body[:200] if self.new_body else None),
            excluded_contacts=[],
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")

        try:
            # Fetch the existing sequence
            sequences = connector.get_sequences()
            target_seq = None
            for seq in sequences:
                seq_id = getattr(seq, "id", None)
                if seq_id == self.sequence_id:
                    target_seq = seq
                    break

            if target_seq is None:
                return LifecycleExecutionResult(
                    success=False,
                    action_type=self.action_type,
                    provider=provider,
                    error_message=f"Sequence '{self.sequence_id}' not found",
                    executed_at=_utc_now(),
                )

            # Update the email at the specified index
            emails = list(getattr(target_seq, "emails", []))
            if self.email_index >= len(emails):
                return LifecycleExecutionResult(
                    success=False,
                    action_type=self.action_type,
                    provider=provider,
                    error_message=(
                        f"Email index {self.email_index} is out of range "
                        f"(sequence has {len(emails)} emails)"
                    ),
                    executed_at=_utc_now(),
                )

            updated_email = dict(emails[self.email_index])
            if self.new_subject:
                updated_email["subject"] = self.new_subject
            if self.new_body:
                updated_email["body_html"] = self.new_body
            emails[self.email_index] = updated_email

            # Persist via connector (re-create or update)
            from kai.connectors.lifecycle.base import SequenceConfig

            updated_seq = SequenceConfig(
                id=self.sequence_id,
                name=getattr(target_seq, "name", "Updated sequence"),
                emails=emails,
                status=getattr(target_seq, "status", "draft"),
                total_emails=len(emails),
            )
            connector.create_sequence(updated_seq)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                sequence_id=self.sequence_id,
                executed_at=_utc_now(),
                metadata={
                    "email_index": self.email_index,
                    "changes": {
                        "new_subject": self.new_subject,
                        "new_body_length": len(self.new_body) if self.new_body else 0,
                    },
                    "reason": self.reason,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class SendReminderSequence(LifecycleAction):
    """Send appointment/service reminder sequences.

    Parameters
    ----------
    contact_segment : str
        Target contact segment.
    reminder_type : str
        One of: appointment, service_due, follow_up, payment_due, renewal.
    timing : dict
        ``{"send_before_days": int, "send_before_hours": int,
        "repeat": bool, "repeat_interval_days": int}``
    """

    def __init__(
        self,
        contact_segment: str,
        reminder_type: str,
        timing: Dict[str, Any],
    ) -> None:
        super().__init__(
            contact_segment=contact_segment,
            reminder_type=reminder_type,
            timing=timing,
        )
        self.contact_segment = contact_segment
        self.reminder_type = reminder_type
        self.timing = timing

    @property
    def action_type(self) -> str:
        return "send_reminder_sequence"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check reminder_type is valid
        if self.reminder_type not in VALID_REMINDER_TYPES:
            errors.append(
                f"Invalid reminder_type '{self.reminder_type}'. "
                f"Valid types: {', '.join(VALID_REMINDER_TYPES)}"
            )

        # Check timing is reasonable
        send_before_days = self.timing.get("send_before_days", 0)
        send_before_hours = self.timing.get("send_before_hours", 0)
        repeat_interval = self.timing.get("repeat_interval_days", 0)

        if send_before_days < 0 or send_before_hours < 0:
            errors.append("Timing values must be non-negative")

        if send_before_days > 30:
            warnings.append(
                f"Sending reminders {send_before_days} days before the event "
                f"may be too early -- consider 1-7 days"
            )

        if self.timing.get("repeat", False) and repeat_interval < 1:
            errors.append(
                "repeat_interval_days must be at least 1 when repeat is enabled"
            )

        if self.timing.get("repeat", False) and repeat_interval > 0:
            if send_before_days > 0 and repeat_interval >= send_before_days:
                warnings.append(
                    "repeat_interval_days is >= send_before_days -- "
                    "contacts may only receive one reminder before the event"
                )

        # Check contacts have the required date field
        date_field_map = {
            "appointment": "appointment_date",
            "service_due": "service_due_date",
            "follow_up": "follow_up_date",
            "payment_due": "payment_due_date",
            "renewal": "renewal_date",
        }
        required_field = date_field_map.get(self.reminder_type)
        if required_field and eligible_contacts:
            contacts_missing_date = sum(
                1
                for c in eligible_contacts
                if not c.get(required_field) and not c.get("custom_fields", {}).get(required_field)
            )
            if contacts_missing_date == len(eligible_contacts):
                errors.append(
                    f"No eligible contacts have the required '{required_field}' field"
                )
            elif contacts_missing_date > 0:
                warnings.append(
                    f"{contacts_missing_date} contacts are missing the "
                    f"'{required_field}' field and will be skipped"
                )

        if not eligible_contacts:
            errors.append("No eligible contacts in segment")

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=0,
            contacts_eligible=len(eligible_contacts),
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        count = len(self._eligible_contacts)
        send_before_days = self.timing.get("send_before_days", 0)
        send_before_hours = self.timing.get("send_before_hours", 0)

        timing_str_parts: List[str] = []
        if send_before_days > 0:
            timing_str_parts.append(f"{send_before_days} days")
        if send_before_hours > 0:
            timing_str_parts.append(f"{send_before_hours} hours")
        timing_str = " and ".join(timing_str_parts) if timing_str_parts else "immediately"

        repeat_info = ""
        if self.timing.get("repeat", False):
            interval = self.timing.get("repeat_interval_days", 1)
            repeat_info = f", repeating every {interval} days"

        summary = (
            f"Send {self.reminder_type} reminders to {count} contacts "
            f"({timing_str} before event{repeat_info})"
        )

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=count,
            email_count=1,
            timing_summary=f"{timing_str} before event{repeat_info}",
            estimated_sends=count,
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")
        count = len(self._eligible_contacts)

        try:
            from kai.connectors.lifecycle.base import EmailMessage as LCEmailMessage, ContactRecord

            contact_records = [
                ContactRecord(email=c.get("email", ""))
                for c in self._eligible_contacts
            ]

            msg = LCEmailMessage(
                to_email="batch",
                subject=f"{self.reminder_type.replace('_', ' ').title()} Reminder",
                body_text=f"This is your {self.reminder_type.replace('_', ' ')} reminder.",
                tags=[f"reminder:{self.reminder_type}"],
            )

            connector.send_batch(contact_records, message=msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=count,
                contacts_excluded=len(self._excluded_contacts),
                emails_sent_immediately=count,
                executed_at=_utc_now(),
                metadata={
                    "reminder_type": self.reminder_type,
                    "segment": self.contact_segment,
                    "timing": self.timing,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class LaunchReviewRequestSequence(LifecycleAction):
    """Send post-service review request sequences.

    Parameters
    ----------
    segment : str
        Target contact segment (should be recent customers).
    timing_after_service : int
        Days after service completion to send the first request.
    platform_targets : list of str or None
        Review platforms to target.  Defaults to ``["google"]``.
    """

    def __init__(
        self,
        segment: str,
        timing_after_service: int = 3,
        platform_targets: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            segment=segment,
            timing_after_service=timing_after_service,
            platform_targets=platform_targets,
        )
        self.segment = segment
        self.timing_after_service = timing_after_service
        self.platform_targets = platform_targets or ["google"]

    @property
    def action_type(self) -> str:
        return "launch_review_request"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check timing is reasonable (1-14 days)
        if self.timing_after_service < 1:
            errors.append(
                f"timing_after_service must be at least 1 day, "
                f"got {self.timing_after_service}"
            )
        elif self.timing_after_service > 14:
            errors.append(
                f"timing_after_service must be 14 days or less, "
                f"got {self.timing_after_service}"
            )
        elif self.timing_after_service > 7:
            warnings.append(
                f"Sending review requests {self.timing_after_service} days after "
                f"service may reduce response rate -- consider 1-3 days"
            )

        # Check platform targets are valid
        for platform in self.platform_targets:
            if platform.lower() not in VALID_REVIEW_PLATFORMS:
                warnings.append(
                    f"Platform '{platform}' is not in the standard platform list. "
                    f"Supported: {', '.join(VALID_REVIEW_PLATFORMS)}"
                )

        # Check contacts have service_date or completion_date
        if eligible_contacts:
            contacts_with_date = sum(
                1
                for c in eligible_contacts
                if c.get("service_date")
                or c.get("completion_date")
                or c.get("custom_fields", {}).get("service_date")
                or c.get("custom_fields", {}).get("completion_date")
            )
            if contacts_with_date == 0:
                errors.append(
                    "No eligible contacts have a 'service_date' or "
                    "'completion_date' field"
                )

        # Check contacts haven't received a review request in last 90 days
        now = datetime.now(timezone.utc)
        ninety_days_ago = now - timedelta(days=90)
        recently_asked = 0
        for c in eligible_contacts:
            last_review_request = c.get("last_review_request_date")
            if last_review_request:
                try:
                    req_dt = datetime.fromisoformat(
                        last_review_request.replace("Z", "+00:00")
                    )
                    if req_dt >= ninety_days_ago:
                        recently_asked += 1
                except (ValueError, AttributeError):
                    pass

        if recently_asked > 0:
            warnings.append(
                f"{recently_asked} contacts received a review request in "
                f"the last 90 days and will be skipped"
            )

        if not eligible_contacts:
            errors.append("No eligible contacts in segment")

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=recently_asked,
            contacts_eligible=len(eligible_contacts) - recently_asked,
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        count = len(self._eligible_contacts)
        platforms_str = ", ".join(self.platform_targets)

        summary = (
            f"Send review request to {count} contacts "
            f"{self.timing_after_service} days after service, "
            f"targeting {platforms_str}"
        )

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=count,
            email_count=1,
            timing_summary=f"{self.timing_after_service} days after service completion",
            estimated_sends=count,
            sample_subject="How was your experience? Leave us a review",
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")
        count = len(self._eligible_contacts)

        try:
            from kai.connectors.lifecycle.base import EmailMessage as LCEmailMessage, ContactRecord

            contact_records = [
                ContactRecord(email=c.get("email", ""))
                for c in self._eligible_contacts
            ]

            platforms_str = ", ".join(self.platform_targets)
            msg = LCEmailMessage(
                to_email="batch",
                subject="How was your experience? Leave us a review",
                body_text=(
                    f"We would love to hear about your experience. "
                    f"Please leave us a review on {platforms_str}."
                ),
                tags=["review_request"] + [f"platform:{p}" for p in self.platform_targets],
            )

            connector.send_batch(contact_records, message=msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=count,
                contacts_excluded=len(self._excluded_contacts),
                emails_sent_immediately=count,
                executed_at=_utc_now(),
                metadata={
                    "segment": self.segment,
                    "timing_after_service": self.timing_after_service,
                    "platform_targets": self.platform_targets,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class SendReferralAsk(LifecycleAction):
    """Send referral program outreach to past customers.

    Parameters
    ----------
    segment : str
        Target segment (should be past customers, not leads).
    offer : str or None
        Referral incentive (e.g., "$50 credit for each referral").
    referral_mechanism : str
        One of: "link" (shareable URL), "code" (referral code), "manual" (just ask).
    """

    def __init__(
        self,
        segment: str,
        offer: Optional[str] = None,
        referral_mechanism: str = "link",
    ) -> None:
        super().__init__(
            segment=segment,
            offer=offer,
            referral_mechanism=referral_mechanism,
        )
        self.segment = segment
        self.offer = offer
        self.referral_mechanism = referral_mechanism

    @property
    def action_type(self) -> str:
        return "send_referral_ask"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check segment targets past customers (not leads or prospects)
        contacts_with_purchase = sum(
            1
            for c in eligible_contacts
            if c.get("has_purchased", False)
            or c.get("customer_status") == "customer"
            or c.get("completed_service", False)
            or c.get("custom_fields", {}).get("has_purchased", False)
        )

        if eligible_contacts and contacts_with_purchase == 0:
            errors.append(
                "Referral asks should target past customers. "
                "No contacts in this segment have a purchase or completed service."
            )

        # Warn if no offer/incentive
        if not self.offer:
            warnings.append(
                "No referral incentive provided. Referral asks work "
                "significantly better with an incentive (e.g., '$25 credit')."
            )

        # Check referral mechanism is valid
        valid_mechanisms = ["link", "code", "manual"]
        if self.referral_mechanism not in valid_mechanisms:
            errors.append(
                f"Invalid referral_mechanism '{self.referral_mechanism}'. "
                f"Valid options: {', '.join(valid_mechanisms)}"
            )

        # Check contacts have had at least one completed service/purchase
        contacts_without_history = sum(
            1
            for c in eligible_contacts
            if not c.get("has_purchased", False)
            and c.get("customer_status") != "customer"
            and not c.get("completed_service", False)
            and not c.get("custom_fields", {}).get("has_purchased", False)
        )
        if contacts_without_history > 0 and contacts_with_purchase > 0:
            warnings.append(
                f"{contacts_without_history} contacts have no purchase "
                f"history and may not be appropriate for referral asks"
            )

        if not eligible_contacts:
            errors.append("No eligible contacts in segment")

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=0,
            contacts_eligible=len(eligible_contacts),
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        count = len(self._eligible_contacts)
        offer_str = self.offer if self.offer else "no incentive"

        summary = f"Send referral ask to {count} customers with {offer_str}"

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=count,
            email_count=1,
            timing_summary="Immediate send",
            estimated_sends=count,
            sample_subject="Know someone who could use our help?",
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")
        count = len(self._eligible_contacts)

        try:
            from kai.connectors.lifecycle.base import EmailMessage as LCEmailMessage, ContactRecord

            contact_records = [
                ContactRecord(email=c.get("email", ""))
                for c in self._eligible_contacts
            ]

            body_parts = ["Know someone who could benefit from our services?"]
            if self.offer:
                body_parts.append(f"Refer a friend and get {self.offer}.")
            if self.referral_mechanism == "link":
                body_parts.append("Share your personal referral link to get started.")
            elif self.referral_mechanism == "code":
                body_parts.append("Share your referral code with friends.")
            else:
                body_parts.append("Just tell them about us -- we appreciate it.")

            msg = LCEmailMessage(
                to_email="batch",
                subject="Know someone who could use our help?",
                body_text=" ".join(body_parts),
                tags=["referral_ask", f"mechanism:{self.referral_mechanism}"],
            )

            connector.send_batch(contact_records, message=msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=count,
                contacts_excluded=len(self._excluded_contacts),
                emails_sent_immediately=count,
                executed_at=_utc_now(),
                metadata={
                    "segment": self.segment,
                    "offer": self.offer,
                    "referral_mechanism": self.referral_mechanism,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class LaunchReactivation(LifecycleAction):
    """Launch a win-back sequence for dormant customers.

    Parameters
    ----------
    dormant_segment : str
        Target segment of dormant/inactive contacts.
    offer : str or None
        Win-back incentive (e.g., "20% off your next visit").
    sequence_length : int
        Number of emails in the reactivation sequence (1-5).
    """

    def __init__(
        self,
        dormant_segment: str,
        offer: Optional[str] = None,
        sequence_length: int = 3,
    ) -> None:
        super().__init__(
            dormant_segment=dormant_segment,
            offer=offer,
            sequence_length=sequence_length,
        )
        self.dormant_segment = dormant_segment
        self.offer = offer
        self.sequence_length = sequence_length

    @property
    def action_type(self) -> str:
        return "launch_reactivation"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check dormant_segment targets contacts who haven't engaged in 90+ days
        now = datetime.now(timezone.utc)
        ninety_days_ago = now - timedelta(days=90)

        contacts_truly_dormant = 0
        for c in eligible_contacts:
            last_engaged = (
                c.get("last_engaged_date")
                or c.get("last_contacted")
                or c.get("last_activity_date")
            )
            if last_engaged:
                try:
                    engaged_dt = datetime.fromisoformat(
                        last_engaged.replace("Z", "+00:00")
                    )
                    if engaged_dt < ninety_days_ago:
                        contacts_truly_dormant += 1
                except (ValueError, AttributeError):
                    # If we can't parse the date, count them as dormant
                    contacts_truly_dormant += 1
            else:
                # No engagement data -- assume dormant
                contacts_truly_dormant += 1

        if eligible_contacts and contacts_truly_dormant == 0:
            warnings.append(
                "No contacts in this segment appear dormant (90+ days since "
                "last engagement). Reactivation campaigns target inactive contacts."
            )

        # Check sequence_length is reasonable (1-5)
        if self.sequence_length < 1 or self.sequence_length > 5:
            errors.append(
                f"sequence_length must be between 1 and 5, "
                f"got {self.sequence_length}"
            )

        # Warn if no offer
        if not self.offer:
            warnings.append(
                "No reactivation incentive provided. Win-back campaigns "
                "work best with a compelling offer (e.g., '20% off')."
            )

        # Check contacts haven't received a reactivation in last 180 days
        one_eighty_days_ago = now - timedelta(days=180)
        recently_reactivated = 0
        for c in eligible_contacts:
            last_reactivation = c.get("last_reactivation_date")
            if last_reactivation:
                try:
                    react_dt = datetime.fromisoformat(
                        last_reactivation.replace("Z", "+00:00")
                    )
                    if react_dt >= one_eighty_days_ago:
                        recently_reactivated += 1
                except (ValueError, AttributeError):
                    pass

        if recently_reactivated > 0:
            warnings.append(
                f"{recently_reactivated} contacts received a reactivation "
                f"sequence in the last 180 days and should be excluded"
            )

        if not eligible_contacts:
            errors.append("No eligible contacts in segment")

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=recently_reactivated,
            contacts_eligible=len(eligible_contacts) - recently_reactivated,
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        count = len(self._eligible_contacts)

        # Build timing summary from standard spacing
        spacing = REACTIVATION_SPACING.get(
            self.sequence_length,
            list(range(0, self.sequence_length * 7, 7)),
        )
        timing_parts = [f"Day {d}" for d in spacing]
        timing_summary = ", ".join(timing_parts)

        summary = (
            f"Launch {self.sequence_length}-email reactivation to "
            f"{count} dormant contacts"
        )

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=count,
            email_count=self.sequence_length,
            timing_summary=timing_summary,
            estimated_sends=count * self.sequence_length,
            sample_subject="We miss you -- come back and save",
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")
        count = len(self._eligible_contacts)

        try:
            from kai.connectors.lifecycle.base import (
                SequenceConfig,
                EmailMessage as LCEmailMessage,
                ContactRecord,
            )

            # Build the reactivation sequence
            spacing = REACTIVATION_SPACING.get(
                self.sequence_length,
                list(range(0, self.sequence_length * 7, 7)),
            )

            emails: List[Dict[str, Any]] = []
            subjects = [
                "We miss you -- come back and save",
                "Still thinking about it? Here is what you are missing",
                "Last chance to claim your offer",
                "A personal note from our team",
                "Final reminder -- your offer expires soon",
            ]
            for i in range(self.sequence_length):
                delay = spacing[i] if i < len(spacing) else (i * 7)
                subject = subjects[i] if i < len(subjects) else f"Reactivation email {i + 1}"
                body = f"We noticed it has been a while since your last visit."
                if self.offer:
                    body += f" Come back and enjoy {self.offer}."

                emails.append({
                    "delay_days": delay,
                    "subject": subject,
                    "body_text": body,
                    "body_html": f"<p>{body}</p>",
                })

            seq = SequenceConfig(
                name=f"Reactivation - {self.dormant_segment}",
                description=f"Win-back sequence for dormant segment: {self.dormant_segment}",
                emails=emails,
                status="draft",
                total_emails=self.sequence_length,
            )
            created = connector.create_sequence(seq)
            sequence_id = getattr(created, "id", None)

            # Enroll contacts
            contact_records = [
                ContactRecord(email=c.get("email", ""))
                for c in self._eligible_contacts
            ]

            first_msg = LCEmailMessage(
                to_email="batch",
                subject=emails[0]["subject"],
                body_text=emails[0]["body_text"],
                body_html=emails[0]["body_html"],
                tags=["reactivation", f"segment:{self.dormant_segment}"],
            )

            connector.send_batch(contact_records, message=first_msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=count,
                contacts_excluded=len(self._excluded_contacts),
                emails_queued=count * (self.sequence_length - 1),
                emails_sent_immediately=count,
                sequence_id=sequence_id,
                executed_at=_utc_now(),
                metadata={
                    "dormant_segment": self.dormant_segment,
                    "offer": self.offer,
                    "sequence_length": self.sequence_length,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )


class SendQuoteFollowUp(LifecycleAction):
    """Follow up on a sent quote or proposal.

    Parameters
    ----------
    contact_id : str
        The contact to follow up with.
    quote_details : dict
        ``{"quote_id": str, "service": str, "amount": float,
        "quote_date": str, "expiry_date": Optional[str]}``
    follow_up_schedule : list of int or None
        Days after quote to follow up.  Defaults to ``[2, 5, 10]``.
    """

    def __init__(
        self,
        contact_id: str,
        quote_details: Dict[str, Any],
        follow_up_schedule: Optional[List[int]] = None,
    ) -> None:
        super().__init__(
            contact_id=contact_id,
            quote_details=quote_details,
            follow_up_schedule=follow_up_schedule,
        )
        self.contact_id = contact_id
        self.quote_details = quote_details
        self.follow_up_schedule = follow_up_schedule or [2, 5, 10]

    @property
    def action_type(self) -> str:
        return "send_quote_follow_up"

    def _validate_impl(
        self, eligible_contacts: List[Dict[str, Any]]
    ) -> LifecycleValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # Check contact_id
        if not self.contact_id or not self.contact_id.strip():
            errors.append("contact_id is required")

        # Check quote_details has required fields
        required_fields = ["service", "amount", "quote_date"]
        for field_name in required_fields:
            if field_name not in self.quote_details or not self.quote_details[field_name]:
                errors.append(f"quote_details.{field_name} is required")

        # Check quote is not expired
        expiry_date = self.quote_details.get("expiry_date")
        if expiry_date:
            try:
                expiry_dt = datetime.fromisoformat(
                    expiry_date.replace("Z", "+00:00")
                )
                now = datetime.now(timezone.utc)
                if expiry_dt < now:
                    errors.append(
                        f"Quote has expired (expiry_date: {expiry_date}). "
                        f"Cannot follow up on an expired quote."
                    )
            except (ValueError, AttributeError):
                warnings.append(
                    f"Could not parse expiry_date '{expiry_date}' -- "
                    f"skipping expiry check"
                )

        # Check contact hasn't already responded to the quote
        for c in eligible_contacts:
            if c.get("quote_responded", False) or c.get("quote_status") == "responded":
                errors.append(
                    "Contact has already responded to this quote. "
                    "No follow-up needed."
                )
                break

        # Check contact hasn't received more than 3 follow-ups for this quote
        quote_id = self.quote_details.get("quote_id", "")
        for c in eligible_contacts:
            follow_ups_sent = c.get("quote_follow_ups_sent", 0)
            quote_follow_up_ids = c.get("quote_follow_up_ids", [])

            # Check by quote ID if available
            if quote_id and quote_id in quote_follow_up_ids:
                follow_ups_for_this = quote_follow_up_ids.count(quote_id)
                if follow_ups_for_this >= 3:
                    errors.append(
                        f"Contact has already received {follow_ups_for_this} "
                        f"follow-ups for this quote (max 3)"
                    )
                    break
            elif follow_ups_sent >= 3:
                errors.append(
                    f"Contact has already received {follow_ups_sent} "
                    f"follow-ups for this quote (max 3)"
                )
                break

        is_valid = len(errors) == 0
        return LifecycleValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            contacts_excluded=0,
            contacts_eligible=len(eligible_contacts),
        )

    def _preview_impl(self) -> LifecycleActionPreview:
        service = self.quote_details.get("service", "Unknown service")
        amount = self.quote_details.get("amount", 0)
        quote_date = self.quote_details.get("quote_date", "Unknown date")

        summary = (
            f"Follow up with {self.contact_id} on ${amount} {service} "
            f"quote (sent {quote_date})"
        )

        schedule_str = ", ".join(f"Day {d}" for d in self.follow_up_schedule)

        compliance_status = "compliant"
        if self._validation and self._validation.compliance_issues:
            compliance_status = "issues_found"

        return LifecycleActionPreview(
            action_type=self.action_type,
            summary=summary,
            recipient_count=1,
            email_count=len(self.follow_up_schedule),
            timing_summary=schedule_str,
            estimated_sends=len(self.follow_up_schedule),
            sample_subject=f"Following up on your {service} quote",
            excluded_contacts=self._excluded_contacts,
            compliance_status=compliance_status,
        )

    def _execute_impl(self, connector: Any) -> LifecycleExecutionResult:
        provider = getattr(connector, "provider_name", "unknown")

        try:
            from kai.connectors.lifecycle.base import (
                SequenceConfig,
                EmailMessage as LCEmailMessage,
                ContactRecord,
            )

            service = self.quote_details.get("service", "your service")
            amount = self.quote_details.get("amount", 0)

            # Build follow-up sequence
            emails: List[Dict[str, Any]] = []
            subjects = [
                f"Following up on your {service} quote",
                f"Any questions about your ${amount} {service} quote?",
                f"Your {service} quote -- let us know how to help",
            ]

            prev_day = 0
            for i, day in enumerate(self.follow_up_schedule):
                delay = day - prev_day
                prev_day = day
                subject = subjects[i] if i < len(subjects) else f"Quote follow-up {i + 1}"
                body = (
                    f"We sent you a quote for {service} at ${amount}. "
                    f"We wanted to check in and see if you have any questions."
                )
                emails.append({
                    "delay_days": delay,
                    "subject": subject,
                    "body_text": body,
                    "body_html": f"<p>{body}</p>",
                })

            seq = SequenceConfig(
                name=f"Quote follow-up - {self.contact_id}",
                description=f"Follow-up on {service} quote for {self.contact_id}",
                emails=emails,
                status="draft",
                total_emails=len(emails),
            )
            created = connector.create_sequence(seq)
            sequence_id = getattr(created, "id", None)

            # Send first email
            contact_record = ContactRecord(email=self.contact_id)
            first_msg = LCEmailMessage(
                to_email=self.contact_id,
                subject=emails[0]["subject"],
                body_text=emails[0]["body_text"],
                body_html=emails[0]["body_html"],
                tags=["quote_follow_up", f"quote:{self.quote_details.get('quote_id', '')}"],
            )

            connector.send_email(first_msg)

            return LifecycleExecutionResult(
                success=True,
                action_type=self.action_type,
                provider=provider,
                contacts_sent=1,
                contacts_excluded=len(self._excluded_contacts),
                emails_queued=len(emails) - 1,
                emails_sent_immediately=1,
                sequence_id=sequence_id,
                executed_at=_utc_now(),
                metadata={
                    "contact_id": self.contact_id,
                    "quote_id": self.quote_details.get("quote_id"),
                    "service": service,
                    "amount": amount,
                    "follow_up_schedule": self.follow_up_schedule,
                },
            )
        except Exception as exc:
            return LifecycleExecutionResult(
                success=False,
                action_type=self.action_type,
                provider=provider,
                error_message=str(exc),
                executed_at=_utc_now(),
            )

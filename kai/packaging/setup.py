"""Kai Marketing OS — Setup Wizard.

Interactive guided setup that walks an operator through creating their
first business profile, selecting an archetype, configuring channels,
and setting approval preferences.  Produces a structured config dict and
workspace state without requiring the operator to edit YAML by hand.

Eight sections (some conditional, some optional):

1. Business Information (required)
2. Services & Offerings (required)
3. Service Area (conditional — required for local/multi-location)
4. Archetype Selection (required)
5. Channel Configuration (required)
6. Budget & Risk Preferences (optional)
7. Approval Preferences (optional)
8. Watcher Configuration (optional)

Usage::

    from kai.packaging.setup import SetupWizard

    wizard = SetupWizard("/path/to/workspace")
    sections = wizard.get_sections()
    # Collect answers from operator (CLI, web form, etc.)
    result = wizard.complete_setup(all_answers)
"""

from __future__ import annotations

import copy
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass
class SetupQuestion:
    """A single question presented to the operator."""

    id: str = ""
    prompt: str = ""
    field_name: str = ""
    input_type: str = "text"  # text | select | multiselect | boolean | number
    options: Optional[List[str]] = None
    default: Optional[Any] = None
    required: bool = False
    validation: Optional[str] = None
    help_text: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SetupSection:
    """A group of related questions."""

    title: str = ""
    description: str = ""
    questions: List[SetupQuestion] = field(default_factory=list)
    required: bool = True

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SetupResult:
    """Output of a completed setup wizard run."""

    business_profile: Dict[str, Any] = field(default_factory=dict)
    archetype: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    workspace_state: Dict[str, Any] = field(default_factory=dict)
    completed_sections: List[str] = field(default_factory=list)
    skipped_sections: List[str] = field(default_factory=list)

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_URL_RE = re.compile(
    r"^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*"
    r"(/[^\s]*)?$"
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_PHONE_RE = re.compile(r"^[\d\s\-\+\(\)\.]{7,20}$")

_QUIET_HOURS_RE = re.compile(r"^\d{2}:\d{2}\-\d{2}:\d{2}$")


def _validate_url(value: str) -> Optional[str]:
    if value and not _URL_RE.match(value.strip()):
        return "Must be a valid URL starting with http:// or https://"
    return None


def _validate_email(value: str) -> Optional[str]:
    if value and not _EMAIL_RE.match(value.strip()):
        return "Must be a valid email address"
    return None


def _validate_phone(value: str) -> Optional[str]:
    if value and not _PHONE_RE.match(value.strip()):
        return "Must be a valid phone number"
    return None


def _validate_quiet_hours(value: str) -> Optional[str]:
    if value and not _QUIET_HOURS_RE.match(value.strip()):
        return "Must be in HH:MM-HH:MM format (e.g. 22:00-07:00)"
    return None


_VALIDATORS = {
    "url": _validate_url,
    "email": _validate_email,
    "phone": _validate_phone,
    "quiet_hours": _validate_quiet_hours,
}


def _run_validation(rule: Optional[str], value: Any) -> Optional[str]:
    """Run a named validation rule. Returns error message or None."""
    if rule is None or value is None or value == "":
        return None
    validator = _VALIDATORS.get(rule)
    if validator is None:
        return None
    return validator(str(value))


# ---------------------------------------------------------------------------
# Section definitions
# ---------------------------------------------------------------------------

def _section_business_information() -> SetupSection:
    return SetupSection(
        title="Business Information",
        description="Basic details about the business. This powers everything Kai does.",
        required=True,
        questions=[
            SetupQuestion(
                id="biz_name",
                prompt="What is the business name?",
                field_name="business_name",
                input_type="text",
                required=True,
                help_text="The name customers see (e.g. 'TrueNorth HVAC').",
            ),
            SetupQuestion(
                id="biz_url",
                prompt="Website URL (if you have one)",
                field_name="website_url",
                input_type="text",
                required=False,
                validation="url",
                help_text="Full URL including https:// — leave blank if no site exists yet.",
            ),
            SetupQuestion(
                id="biz_phone",
                prompt="Business phone number",
                field_name="business_phone",
                input_type="text",
                required=False,
                validation="phone",
                help_text="Primary phone number customers call. Required for local service businesses.",
            ),
            SetupQuestion(
                id="biz_description",
                prompt="Describe the business in 1-2 sentences",
                field_name="business_description",
                input_type="text",
                required=True,
                help_text="What does the business do and who does it serve?",
            ),
            SetupQuestion(
                id="biz_year_founded",
                prompt="Year founded (approximate is fine)",
                field_name="year_founded",
                input_type="number",
                required=False,
                help_text="Helps Kai calibrate trust signals and messaging maturity.",
            ),
            SetupQuestion(
                id="biz_employee_count",
                prompt="How many employees?",
                field_name="employee_count_range",
                input_type="select",
                options=["1-5", "6-20", "21-50", "51-200", "200+"],
                required=False,
                help_text="Approximate team size. Affects which tactics Kai recommends.",
            ),
        ],
    )


def _section_services_offerings() -> SetupSection:
    return SetupSection(
        title="Services & Offerings",
        description="What the business sells and how it prices.",
        required=True,
        questions=[
            SetupQuestion(
                id="primary_service",
                prompt="What is the primary service or product?",
                field_name="primary_service",
                input_type="text",
                required=True,
                help_text="The single thing the business is best known for.",
            ),
            SetupQuestion(
                id="service_list",
                prompt="List all services/products (comma-separated)",
                field_name="service_list",
                input_type="text",
                required=False,
                help_text="E.g. 'AC repair, AC installation, duct cleaning, maintenance plans'.",
            ),
            SetupQuestion(
                id="pricing_model",
                prompt="How does the business charge?",
                field_name="pricing_model",
                input_type="select",
                options=[
                    "per-job",
                    "hourly",
                    "subscription",
                    "project",
                    "retainer",
                    "product-based",
                ],
                required=False,
                help_text="Primary pricing model. Pick the closest fit.",
            ),
            SetupQuestion(
                id="avg_deal_value",
                prompt="Average deal/order value (optional)",
                field_name="average_deal_value",
                input_type="text",
                required=False,
                help_text="E.g. '$350', '$2,000-$5,000'. Helps Kai estimate ROI.",
            ),
        ],
    )


def _section_service_area() -> SetupSection:
    return SetupSection(
        title="Service Area",
        description=(
            "Where the business operates geographically. "
            "Required for local service and multi-location businesses."
        ),
        required=False,  # Conditional — toggled to True for local/multi-location
        questions=[
            SetupQuestion(
                id="primary_city",
                prompt="Primary city",
                field_name="primary_city",
                input_type="text",
                required=False,
                help_text="Main city the business operates in.",
            ),
            SetupQuestion(
                id="state_province",
                prompt="State or province",
                field_name="state_province",
                input_type="text",
                required=False,
                help_text="Two-letter abbreviation or full name.",
            ),
            SetupQuestion(
                id="service_radius",
                prompt="Service radius in miles",
                field_name="service_radius_miles",
                input_type="number",
                required=False,
                help_text="How far from the primary city the business serves.",
            ),
            SetupQuestion(
                id="additional_areas",
                prompt="Additional service areas (comma-separated cities)",
                field_name="additional_service_areas",
                input_type="text",
                required=False,
                help_text="E.g. 'Plano, Frisco, McKinney'.",
            ),
        ],
    )


def _section_archetype_selection() -> SetupSection:
    return SetupSection(
        title="Archetype Selection",
        description=(
            "The business archetype determines which modules, watchers, "
            "checklists, and default KPIs Kai activates."
        ),
        required=True,
        questions=[
            SetupQuestion(
                id="business_type",
                prompt="What type of business is this?",
                field_name="business_type",
                input_type="select",
                options=[
                    "Local Service Business",
                    "Ecommerce/Online Store",
                    "Professional Services/B2B",
                    "Multi-Location Business",
                ],
                required=True,
                help_text="Pick the closest match. Kai can refine later.",
            ),
            SetupQuestion(
                id="auto_detect",
                prompt="Let Kai determine the best archetype automatically?",
                field_name="auto_detect_archetype",
                input_type="boolean",
                default=True,
                required=False,
                help_text="Kai will analyze your answers and pick the optimal archetype.",
            ),
        ],
    )


def _section_channel_configuration() -> SetupSection:
    return SetupSection(
        title="Channel Configuration",
        description="Which marketing channels the business uses or plans to use.",
        required=True,
        questions=[
            SetupQuestion(
                id="social_platforms",
                prompt="Active social media platforms",
                field_name="social_platforms",
                input_type="multiselect",
                options=[
                    "Facebook",
                    "Instagram",
                    "LinkedIn",
                    "TikTok",
                    "X/Twitter",
                    "YouTube",
                    "Pinterest",
                ],
                required=False,
                help_text="Select all platforms the business currently posts on.",
            ),
            SetupQuestion(
                id="ad_platforms",
                prompt="Active advertising platforms",
                field_name="ad_platforms",
                input_type="multiselect",
                options=[
                    "Google Ads",
                    "Meta Ads",
                    "LinkedIn Ads",
                    "TikTok Ads",
                    "Microsoft Ads",
                ],
                required=False,
                help_text="Select all platforms with active or planned ad spend.",
            ),
            SetupQuestion(
                id="email_platform",
                prompt="Email marketing platform",
                field_name="email_platform",
                input_type="select",
                options=[
                    "None",
                    "Mailchimp",
                    "Klaviyo",
                    "Loops",
                    "ActiveCampaign",
                    "Other",
                ],
                default="None",
                required=False,
                help_text="Which email service the business uses.",
            ),
            SetupQuestion(
                id="crm",
                prompt="CRM system",
                field_name="crm",
                input_type="select",
                options=[
                    "None",
                    "HubSpot",
                    "Salesforce",
                    "Pipedrive",
                    "Jobber",
                    "ServiceTitan",
                    "Other",
                ],
                default="None",
                required=False,
                help_text="Customer relationship management tool in use.",
            ),
        ],
    )


def _section_budget_risk() -> SetupSection:
    return SetupSection(
        title="Budget & Risk Preferences",
        description="Financial guardrails and risk tolerance for marketing actions.",
        required=False,
        questions=[
            SetupQuestion(
                id="monthly_budget",
                prompt="Monthly marketing budget (USD)",
                field_name="monthly_marketing_budget",
                input_type="number",
                required=False,
                help_text="Total monthly spend across all channels. Leave blank if unsure.",
            ),
            SetupQuestion(
                id="max_daily_spend",
                prompt="Maximum daily ad spend (USD)",
                field_name="max_daily_ad_spend",
                input_type="number",
                required=False,
                help_text="Hard cap on daily ad spend across all platforms.",
            ),
            SetupQuestion(
                id="risk_tolerance",
                prompt="Risk tolerance for marketing experiments",
                field_name="risk_tolerance",
                input_type="select",
                options=["Conservative", "Moderate", "Aggressive"],
                default="Moderate",
                required=False,
                help_text=(
                    "Conservative = only proven tactics. "
                    "Moderate = some experimentation. "
                    "Aggressive = test-heavy, higher variance."
                ),
            ),
            SetupQuestion(
                id="auto_approve_low_risk",
                prompt="Auto-approve low-risk actions without asking?",
                field_name="auto_approve_low_risk",
                input_type="boolean",
                default=True,
                required=False,
                help_text="When True, Kai can execute safe optimizations automatically.",
            ),
        ],
    )


def _section_approval_preferences() -> SetupSection:
    return SetupSection(
        title="Approval Preferences",
        description="Controls how Kai requests operator sign-off before publishing.",
        required=False,
        questions=[
            SetupQuestion(
                id="require_content_approval",
                prompt="Require approval for all public content?",
                field_name="require_content_approval",
                input_type="boolean",
                default=True,
                required=False,
                help_text="When True, nothing goes live without your explicit OK.",
            ),
            SetupQuestion(
                id="notification_pref",
                prompt="How should Kai notify you?",
                field_name="notification_preference",
                input_type="select",
                options=["in-app only", "email", "email + slack"],
                default="in-app only",
                required=False,
                help_text="Where notifications and approval requests are sent.",
            ),
            SetupQuestion(
                id="operator_email",
                prompt="Email address for notifications (optional)",
                field_name="operator_email",
                input_type="text",
                required=False,
                validation="email",
                help_text="Receives approval requests and digest summaries.",
            ),
        ],
    )


def _section_watcher_configuration() -> SetupSection:
    return SetupSection(
        title="Watcher Configuration",
        description="Background monitoring that watches for problems and opportunities.",
        required=False,
        questions=[
            SetupQuestion(
                id="enable_watchers",
                prompt="Enable background monitoring?",
                field_name="enable_watchers",
                input_type="boolean",
                default=True,
                required=False,
                help_text="Watchers monitor rankings, reviews, competitors, and performance.",
            ),
            SetupQuestion(
                id="monitoring_freq",
                prompt="Monitoring frequency",
                field_name="monitoring_frequency",
                input_type="select",
                options=["Minimal", "Standard", "Comprehensive"],
                default="Standard",
                required=False,
                help_text=(
                    "Minimal = weekly checks. "
                    "Standard = daily checks. "
                    "Comprehensive = continuous monitoring."
                ),
            ),
            SetupQuestion(
                id="quiet_hours",
                prompt="Quiet hours (no alerts)",
                field_name="quiet_hours",
                input_type="text",
                default="22:00-07:00",
                required=False,
                validation="quiet_hours",
                help_text="Time window when Kai suppresses non-critical alerts. Format: HH:MM-HH:MM.",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Archetype mapping
# ---------------------------------------------------------------------------

_ARCHETYPE_MAP: Dict[str, str] = {
    "Local Service Business": "local-service",
    "Ecommerce/Online Store": "ecommerce",
    "Professional Services/B2B": "professional-services",
    "Multi-Location Business": "multi-location",
}

_LOCAL_ARCHETYPES = {"local-service", "multi-location"}


def _resolve_archetype(answers: Dict[str, Any]) -> str:
    """Determine the archetype from wizard answers."""
    auto_detect = answers.get("auto_detect_archetype", True)
    business_type = answers.get("business_type", "")
    explicit = _ARCHETYPE_MAP.get(business_type, "")

    if not auto_detect and explicit:
        return explicit

    # Auto-detect heuristics
    if explicit:
        archetype = explicit
    else:
        archetype = "local-service"

    # Refine: if service areas mention multiple cities, consider multi-location
    additional = answers.get("additional_service_areas", "")
    if additional:
        cities = [c.strip() for c in additional.split(",") if c.strip()]
        if len(cities) >= 3 and archetype == "local-service":
            archetype = "multi-location"

    return archetype


# ---------------------------------------------------------------------------
# SetupWizard
# ---------------------------------------------------------------------------

class SetupWizard:
    """Guided setup that builds a business profile and workspace config.

    Parameters
    ----------
    workspace_dir:
        Path to the workspace root. Config and profile files are written
        here.
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()

    # ------------------------------------------------------------------
    # Section definitions
    # ------------------------------------------------------------------

    def get_sections(self) -> List[SetupSection]:
        """Return all eight setup sections in order."""
        return [
            _section_business_information(),
            _section_services_offerings(),
            _section_service_area(),
            _section_archetype_selection(),
            _section_channel_configuration(),
            _section_budget_risk(),
            _section_approval_preferences(),
            _section_watcher_configuration(),
        ]

    # ------------------------------------------------------------------
    # Per-section processing
    # ------------------------------------------------------------------

    def process_section(
        self, section_index: int, answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize answers for a single section.

        Parameters
        ----------
        section_index:
            Zero-based index into the list returned by :meth:`get_sections`.
        answers:
            Mapping of ``field_name -> value`` for questions in this section.

        Returns
        -------
        dict:
            Processed answers with validation errors under ``"_errors"``
            (empty list when all valid).
        """
        sections = self.get_sections()
        if section_index < 0 or section_index >= len(sections):
            return {"_errors": [f"Invalid section index: {section_index}"]}

        section = sections[section_index]
        processed: Dict[str, Any] = {}
        errors: List[str] = []

        for question in section.questions:
            value = answers.get(question.field_name, question.default)

            # Required check
            if question.required and (value is None or value == "" or value == []):
                errors.append(f"'{question.prompt}' is required")
                continue

            # Type coercion
            if value is not None and value != "":
                if question.input_type == "number":
                    try:
                        value = int(value) if isinstance(value, str) and "." not in value else float(value)
                    except (ValueError, TypeError):
                        errors.append(f"'{question.prompt}' must be a number")
                        continue
                elif question.input_type == "boolean":
                    if isinstance(value, str):
                        value = value.lower() in ("true", "yes", "1", "y")
                elif question.input_type == "select":
                    if question.options and value not in question.options:
                        errors.append(
                            f"'{question.prompt}' must be one of: "
                            f"{', '.join(question.options)}"
                        )
                        continue
                elif question.input_type == "multiselect":
                    if isinstance(value, str):
                        value = [v.strip() for v in value.split(",") if v.strip()]
                    if question.options:
                        invalid = [v for v in value if v not in question.options]
                        if invalid:
                            errors.append(
                                f"'{question.prompt}' — invalid selections: "
                                f"{', '.join(invalid)}"
                            )
                            continue

            # Named validation rule
            val_error = _run_validation(question.validation, value)
            if val_error:
                errors.append(f"'{question.prompt}': {val_error}")
                continue

            processed[question.field_name] = value

        processed["_errors"] = errors
        return processed

    # ------------------------------------------------------------------
    # Profile builder
    # ------------------------------------------------------------------

    def build_business_profile(self, all_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all section answers into a BusinessProfile-compatible dict.

        The returned dict matches the schema consumed by
        ``kai.runtime.business_profile.build_business_profile()``.
        """
        archetype = _resolve_archetype(all_answers)
        name = all_answers.get("business_name", "")
        brand_id = name.lower().replace(" ", "-").replace("'", "") if name else "default"

        # Identity
        identity: Dict[str, Any] = {
            "name": name,
            "url": all_answers.get("website_url") or None,
            "description": all_answers.get("business_description", ""),
            "year_founded": all_answers.get("year_founded"),
            "employee_count_range": all_answers.get("employee_count_range"),
        }

        # Offers
        service_list_raw = all_answers.get("service_list", "")
        offer_list: List[Dict[str, Any]] = []
        if service_list_raw:
            items = [s.strip() for s in service_list_raw.split(",") if s.strip()]
            primary = all_answers.get("primary_service", "")
            for item in items:
                offer_list.append({
                    "name": item,
                    "is_primary": item.lower() == primary.lower(),
                })

        offers: Dict[str, Any] = {
            "primary_offer": all_answers.get("primary_service", ""),
            "offer_list": offer_list,
            "pricing_model": all_answers.get("pricing_model"),
            "average_deal_value": all_answers.get("average_deal_value"),
        }

        # Geography
        geography: Dict[str, Any] = {}
        primary_city = all_answers.get("primary_city")
        if primary_city:
            geography["primary_location"] = {
                "city": primary_city,
                "state": all_answers.get("state_province"),
                "radius_miles": all_answers.get("service_radius_miles"),
            }
        additional_raw = all_answers.get("additional_service_areas", "")
        if additional_raw:
            state = all_answers.get("state_province")
            areas = []
            for city_name in additional_raw.split(","):
                city_name = city_name.strip()
                if city_name:
                    areas.append({"city": city_name, "state": state})
            geography["service_areas"] = areas
        geography["is_mobile"] = archetype in _LOCAL_ARCHETYPES
        geography["has_storefront"] = archetype not in _LOCAL_ARCHETYPES

        # Channels
        social_platforms = all_answers.get("social_platforms") or []
        ad_platforms = all_answers.get("ad_platforms") or []
        channels_list: List[Dict[str, str]] = []

        # Phone is always a channel for local businesses
        if archetype in _LOCAL_ARCHETYPES:
            channels_list.append({"channel": "calls", "status": "active"})

        for platform in social_platforms:
            channels_list.append({
                "channel": platform.lower().replace("/", "-"),
                "status": "active",
            })
        for platform in ad_platforms:
            channels_list.append({
                "channel": platform.lower().replace(" ", "-"),
                "status": "active",
            })

        email_platform = all_answers.get("email_platform", "None")
        if email_platform and email_platform != "None":
            channels_list.append({
                "channel": "email",
                "status": "active",
                "notes": f"Platform: {email_platform}",
            })

        channels: Dict[str, Any] = {
            "channels": channels_list,
            "phone_number": all_answers.get("business_phone"),
        }

        # Build the profile dict
        profile: Dict[str, Any] = {
            "brand_id": brand_id,
            "archetype": archetype,
            "identity": identity,
            "offers": offers,
            "geography": geography,
            "channels": channels,
            "metadata": {
                "crm": all_answers.get("crm", "None"),
                "email_platform": email_platform,
                "setup_completed_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        return profile

    # ------------------------------------------------------------------
    # Config builder
    # ------------------------------------------------------------------

    def build_config(self, all_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a config.yaml-compatible dict from wizard answers.

        Includes business profile, channel config, budget settings,
        approval settings, and watcher settings.
        """
        archetype = _resolve_archetype(all_answers)
        name = all_answers.get("business_name", "")
        brand_id = name.lower().replace(" ", "-").replace("'", "") if name else "default"

        config: Dict[str, Any] = {
            "workspace": {
                "id": brand_id,
                "name": name or "My Business",
                "description": all_answers.get("business_description", ""),
                "primary_user": "operator",
                "product_mode": "clone",
                "surfaces": ["local"],
            },
            "archetype": archetype,
            "business": {
                "name": name,
                "url": all_answers.get("website_url"),
                "phone": all_answers.get("business_phone"),
                "description": all_answers.get("business_description", ""),
                "primary_service": all_answers.get("primary_service", ""),
            },
            "channels": {
                "social_platforms": all_answers.get("social_platforms", []),
                "ad_platforms": all_answers.get("ad_platforms", []),
                "email_platform": all_answers.get("email_platform", "None"),
                "crm": all_answers.get("crm", "None"),
            },
            "budget": {
                "monthly_marketing_budget": all_answers.get("monthly_marketing_budget"),
                "max_daily_ad_spend": all_answers.get("max_daily_ad_spend"),
                "risk_tolerance": all_answers.get("risk_tolerance", "Moderate"),
                "auto_approve_low_risk": all_answers.get("auto_approve_low_risk", True),
            },
            "approval": {
                "require_content_approval": all_answers.get(
                    "require_content_approval", True
                ),
                "notification_preference": all_answers.get(
                    "notification_preference", "in-app only"
                ),
                "operator_email": all_answers.get("operator_email"),
            },
            "watchers": {
                "enabled": all_answers.get("enable_watchers", True),
                "monitoring_frequency": all_answers.get(
                    "monitoring_frequency", "Standard"
                ),
                "quiet_hours": all_answers.get("quiet_hours", "22:00-07:00"),
            },
        }

        return config

    # ------------------------------------------------------------------
    # Workspace state builder
    # ------------------------------------------------------------------

    def build_workspace_state(self, all_answers: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize workspace state with defaults based on archetype.

        The workspace state tracks what has been completed, what is
        pending, and the current operational status.
        """
        archetype = _resolve_archetype(all_answers)
        name = all_answers.get("business_name", "")
        brand_id = name.lower().replace(" ", "-").replace("'", "") if name else "default"

        now = datetime.now(timezone.utc).isoformat()

        # Archetype-specific module defaults
        module_defaults: Dict[str, List[str]] = {
            "local-service": [
                "local-seo",
                "gbp-optimization",
                "review-management",
                "call-tracking",
                "paid-search-local",
            ],
            "ecommerce": [
                "product-seo",
                "email-lifecycle",
                "paid-social",
                "conversion-optimization",
                "retention",
            ],
            "professional-services": [
                "content-marketing",
                "linkedin-strategy",
                "email-lifecycle",
                "thought-leadership",
                "abm",
            ],
            "multi-location": [
                "local-seo",
                "gbp-optimization",
                "review-management",
                "multi-location-management",
                "paid-search-local",
                "call-tracking",
            ],
        }

        # Watcher frequency mapping
        frequency_map: Dict[str, str] = {
            "Minimal": "weekly",
            "Standard": "daily",
            "Comprehensive": "continuous",
        }

        monitoring_freq = all_answers.get("monitoring_frequency", "Standard")

        state: Dict[str, Any] = {
            "workspace_id": brand_id,
            "brand_id": brand_id,
            "archetype": archetype,
            "created_at": now,
            "updated_at": now,
            "status": "initialized",
            "onboarding": {
                "setup_completed": True,
                "initial_audit_completed": False,
                "first_action_approved": False,
            },
            "active_modules": module_defaults.get(archetype, module_defaults["local-service"]),
            "watchers": {
                "enabled": all_answers.get("enable_watchers", True),
                "frequency": frequency_map.get(monitoring_freq, "daily"),
                "quiet_hours": all_answers.get("quiet_hours", "22:00-07:00"),
            },
            "approval": {
                "require_content_approval": all_answers.get(
                    "require_content_approval", True
                ),
                "auto_approve_low_risk": all_answers.get("auto_approve_low_risk", True),
                "risk_tolerance": all_answers.get("risk_tolerance", "Moderate"),
            },
            "stats": {
                "total_runs": 0,
                "total_approvals": 0,
                "total_rejections": 0,
                "content_pieces_published": 0,
            },
        }

        return state

    # ------------------------------------------------------------------
    # Complete setup
    # ------------------------------------------------------------------

    def complete_setup(self, all_answers: Dict[str, Any]) -> SetupResult:
        """Run the full setup flow and persist results to disk.

        Parameters
        ----------
        all_answers:
            Flat dictionary mapping ``field_name -> value`` for all
            questions across all sections.

        Returns
        -------
        SetupResult
            The compiled profile, config, and workspace state.
        """
        # Track which sections were completed vs skipped
        sections = self.get_sections()
        completed: List[str] = []
        skipped: List[str] = []

        for i, section in enumerate(sections):
            section_fields = [q.field_name for q in section.questions]
            has_answers = any(
                all_answers.get(f) is not None and all_answers.get(f) != ""
                for f in section_fields
            )
            if has_answers:
                completed.append(section.title)
            else:
                skipped.append(section.title)

        # Build outputs
        profile = self.build_business_profile(all_answers)
        config = self.build_config(all_answers)
        workspace_state = self.build_workspace_state(all_answers)
        archetype = _resolve_archetype(all_answers)

        # Persist to disk
        self._write_config(config)
        self._write_profile(profile)
        self._write_workspace_state(workspace_state)

        return SetupResult(
            business_profile=profile,
            archetype=archetype,
            config=config,
            workspace_state=workspace_state,
            completed_sections=completed,
            skipped_sections=skipped,
        )

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_config(self, config: Dict[str, Any]) -> None:
        """Write config.yaml to the workspace directory."""
        config_path = self.workspace_dir / "config.yaml"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            import yaml  # type: ignore[import-untyped]
            text = yaml.dump(
                config,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        except ImportError:
            # Fallback: write as JSON (valid YAML superset)
            import json
            text = json.dumps(config, indent=2, sort_keys=False)

        config_path.write_text(text, encoding="utf-8")

    def _write_profile(self, profile: Dict[str, Any]) -> None:
        """Write business_profile.json to the workspace directory."""
        import json

        brand_id = profile.get("brand_id", "default")
        profile_dir = self.workspace_dir / brand_id / "config"
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_path = profile_dir / "business_profile.json"
        profile_path.write_text(
            json.dumps(profile, indent=2, sort_keys=False),
            encoding="utf-8",
        )

    def _write_workspace_state(self, state: Dict[str, Any]) -> None:
        """Write workspace_state.json to the workspace directory."""
        import json

        brand_id = state.get("brand_id", "default")
        state_dir = self.workspace_dir / brand_id
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "workspace_state.json"
        state_path.write_text(
            json.dumps(state, indent=2, sort_keys=False),
            encoding="utf-8",
        )

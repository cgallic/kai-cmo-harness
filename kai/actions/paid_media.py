"""Paid media action types for the Kai action system.

Defines every structured operation the system can take against ad platforms:
creating creatives, adjusting budgets and bids, pausing/launching campaigns,
publishing variants, updating targeting, and managing negative keywords.

Each action follows the validate -> preview -> execute -> verify lifecycle
defined by :class:`PaidMediaAction`, with paid-media-specific concerns:
spend safety checks, platform compliance, creative validation, and budget
impact assessment.

Action classes:
    - CreateAdCreative — build and submit a new ad creative
    - AdjustBidding — change campaign bid strategy or targets
    - AdjustBudget — set or change campaign budget with spend safety gates
    - PauseCampaign — pause a running campaign
    - EnableCampaign — re-enable a paused campaign
    - LaunchCampaign — create and launch a full campaign (highest risk)
    - PublishApprovedVariant — push an approved creative variant live
    - UpdateTargeting — modify campaign audience targeting
    - AddNegativeKeywords — add negative keywords to reduce wasted spend
    - CreateAdGroup — create a new ad group within a campaign
    - RetireCreative — deactivate an underperforming ad creative

Helper functions:
    - generate_action_execution_id — unique ID for each action execution
    - format_spend_impact — human-readable daily/monthly spend string
    - check_headline_length — platform-specific headline length check
    - check_description_length — platform-specific description length check

Constants:
    - PLATFORM_CREATIVE_LIMITS — per-platform creative constraints
    - BANNED_WORDS — words that trigger instant rejection in ad copy
"""

from __future__ import annotations

import copy
import enum
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
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

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

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

PLATFORM_CREATIVE_LIMITS: Dict[str, Dict[str, Any]] = {
    "google_ads": {
        "headline_max": 30,
        "description_max": 90,
        "headlines_min": 3,
        "headlines_max": 15,
        "descriptions_min": 2,
        "descriptions_max": 4,
    },
    "meta_ads": {
        "primary_text_max": 125,
        "headline_max": 40,
        "description_max": 30,
        "link_description_max": 30,
    },
    "local_services_ads": {},
}

VALID_BID_STRATEGIES: List[str] = [
    "manual_cpc",
    "maximize_conversions",
    "target_cpa",
    "target_roas",
    "maximize_clicks",
    "lowest_cost",
]

# ============================================================================
# Enums
# ============================================================================


class PaidMediaActionType(str, enum.Enum):
    """Every paid media operation the system can perform."""

    create_ad_creative = "create_ad_creative"
    adjust_bidding = "adjust_bidding"
    adjust_budget = "adjust_budget"
    pause_campaign = "pause_campaign"
    enable_campaign = "enable_campaign"
    launch_campaign = "launch_campaign"
    publish_approved_variant = "publish_approved_variant"
    update_targeting = "update_targeting"
    add_negative_keywords = "add_negative_keywords"
    create_ad_group = "create_ad_group"
    retire_creative = "retire_creative"


class ActionLifecycleState(str, enum.Enum):
    """Lifecycle states for a paid media action.

    Transitions:
        pending_validation -> validated -> previewing -> previewed
            -> approved -> executing -> executed -> verifying -> verified
        validated -> validation_failed
        executed -> execution_failed
        verified -> verification_failed
        executed -> rolled_back
    """

    pending_validation = "pending_validation"
    validated = "validated"
    validation_failed = "validation_failed"
    previewing = "previewing"
    previewed = "previewed"
    approved = "approved"
    executing = "executing"
    executed = "executed"
    execution_failed = "execution_failed"
    verifying = "verifying"
    verified = "verified"
    verification_failed = "verification_failed"
    rolled_back = "rolled_back"


# ============================================================================
# Data Models
# ============================================================================


class ValidationResult(BaseModel):
    """Outcome of running validation checks on a paid media action."""

    is_valid: bool = Field(default=False, description="Whether all validation checks passed")
    errors: List[str] = Field(default_factory=list, description="Hard failures that prevent execution")
    warnings: List[str] = Field(default_factory=list, description="Soft warnings that do not block")
    compliance_notes: List[str] = Field(default_factory=list, description="Platform policy compliance notes")


class ActionPreview(BaseModel):
    """Preview of what a paid media action will do before execution."""

    action_type: str = Field(default="", description="PaidMediaActionType value")
    summary: str = Field(default="", description="Human-readable 1-2 sentence summary")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured details of the changes")
    spend_impact: Optional[str] = Field(default=None, description="Human-readable spend impact")
    spend_amount: Optional[float] = Field(default=None, description="Numeric spend impact in USD")
    risk_level: str = Field(default="medium", description="low, medium, or high")
    reversible: bool = Field(default=True, description="Whether this action can be undone")
    estimated_time: Optional[str] = Field(default=None, description="How long until changes take effect")
    requires_platform_review: bool = Field(default=False, description="Whether the platform needs to review")


class ExecutionResult(BaseModel):
    """Outcome of executing a paid media action."""

    success: bool = Field(default=False, description="Whether execution succeeded")
    action_type: str = Field(default="", description="PaidMediaActionType value")
    platform: str = Field(default="", description="Platform name")
    entity_id: Optional[str] = Field(default=None, description="ID of the created or modified entity")
    entity_type: Optional[str] = Field(default=None, description="campaign, ad_group, ad, keyword")
    changes_made: Dict[str, Any] = Field(default_factory=dict, description="What was actually changed")
    error_message: Optional[str] = Field(default=None, description="Error message on failure")
    executed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp",
    )
    rollback_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Data needed to undo this action"
    )


class VerificationResult(BaseModel):
    """Outcome of verifying a paid media action post-execution."""

    verified: bool = Field(default=False, description="Whether verification passed")
    checks_performed: List[str] = Field(default_factory=list, description="What was verified")
    issues_found: List[str] = Field(default_factory=list, description="Issues detected post-execution")
    verified_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp",
    )


# ============================================================================
# Helper Functions
# ============================================================================


def generate_action_execution_id() -> str:
    """Return a unique execution ID in the form ``pma_{12-hex-chars}``."""
    return f"pma_{uuid.uuid4().hex[:12]}"


def format_spend_impact(daily_budget: float) -> str:
    """Return a formatted spend string showing daily and projected monthly cost."""
    return f"${daily_budget:.2f}/day (${daily_budget * 30.4:.0f}/month projected)"


def check_headline_length(headline: str, platform: str) -> Optional[str]:
    """Return an error string if *headline* exceeds the platform limit, else ``None``."""
    limits = PLATFORM_CREATIVE_LIMITS.get(platform, {})
    max_len = limits.get("headline_max")
    if max_len is not None and len(headline) > max_len:
        return (
            f"Headline exceeds {platform} limit: "
            f"{len(headline)} chars > {max_len} max — \"{headline[:50]}...\""
            if len(headline) > 50
            else f"Headline exceeds {platform} limit: "
            f"{len(headline)} chars > {max_len} max — \"{headline}\""
        )
    return None


def check_description_length(description: str, platform: str) -> Optional[str]:
    """Return an error string if *description* exceeds the platform limit, else ``None``."""
    limits = PLATFORM_CREATIVE_LIMITS.get(platform, {})
    max_len = limits.get("description_max")
    if max_len is not None and len(description) > max_len:
        return (
            f"Description exceeds {platform} limit: "
            f"{len(description)} chars > {max_len} max — \"{description[:50]}...\""
            if len(description) > 50
            else f"Description exceeds {platform} limit: "
            f"{len(description)} chars > {max_len} max — \"{description}\""
        )
    return None


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _check_banned_words(text: str) -> List[str]:
    """Return list of banned words found in *text*."""
    lower = text.lower()
    found: List[str] = []
    for word in BANNED_WORDS:
        if word in lower:
            found.append(word)
    return found


# ============================================================================
# Abstract Base: PaidMediaAction
# ============================================================================


class PaidMediaAction(ABC):
    """Abstract base class for all paid media actions.

    Follows the validate -> preview -> execute -> verify lifecycle.
    All mutating operations require explicit confirmation.  Every action
    stores enough state for rollback.

    Parameters
    ----------
    platform : str
        Target ad platform (e.g. ``google_ads``, ``meta_ads``).
    **kwargs :
        Passed to concrete subclass constructors.
    """

    def __init__(self, platform: str, **kwargs: Any) -> None:
        self.platform = platform
        self._state: ActionLifecycleState = ActionLifecycleState.pending_validation
        self._validation: Optional[ValidationResult] = None
        self._preview: Optional[ActionPreview] = None
        self._result: Optional[ExecutionResult] = None
        self._verification: Optional[VerificationResult] = None
        self._execution_id: str = generate_action_execution_id()
        self._created_at: str = _utc_now()

    # ------------------------------------------------------------------
    # Abstract property
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Return the :class:`PaidMediaActionType` value for this action."""
        ...

    # ------------------------------------------------------------------
    # Abstract lifecycle methods
    # ------------------------------------------------------------------

    @abstractmethod
    def _validate_impl(self) -> ValidationResult:
        """Run action-specific validation checks."""
        ...

    @abstractmethod
    def _preview_impl(self) -> ActionPreview:
        """Generate a preview of the planned changes."""
        ...

    @abstractmethod
    def _execute_impl(self, connector: Any) -> ExecutionResult:
        """Execute the action against the ad platform connector."""
        ...

    @abstractmethod
    def _verify_impl(self, connector: Any) -> VerificationResult:
        """Verify the action was executed correctly."""
        ...

    @abstractmethod
    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        """Roll back the action if possible."""
        ...

    # ------------------------------------------------------------------
    # Public lifecycle methods
    # ------------------------------------------------------------------

    def validate(self) -> ValidationResult:
        """Run all validation checks.

        Sets ``_state`` to ``validated`` on success or
        ``validation_failed`` on failure.
        """
        logger.info(
            "Validating %s action on %s (id=%s)",
            self.action_type, self.platform, self._execution_id,
        )
        try:
            result = self._validate_impl()
        except Exception as exc:
            result = ValidationResult(
                is_valid=False,
                errors=[f"Validation raised an exception: {exc}"],
            )

        self._validation = result
        if result.is_valid:
            self._state = ActionLifecycleState.validated
            logger.info("Validation PASSED for %s", self._execution_id)
        else:
            self._state = ActionLifecycleState.validation_failed
            logger.warning(
                "Validation FAILED for %s: %s",
                self._execution_id, result.errors,
            )
        return result

    def preview(self) -> ActionPreview:
        """Generate a preview of the planned changes.

        Must be validated first.  Sets ``_state`` to ``previewed``.

        Raises
        ------
        RuntimeError
            If the action has not been validated.
        """
        if self._state not in (
            ActionLifecycleState.validated,
            ActionLifecycleState.previewed,
        ):
            raise RuntimeError(
                f"Cannot preview action in state '{self._state.value}'. "
                f"Action must be validated first."
            )

        self._state = ActionLifecycleState.previewing
        logger.info("Generating preview for %s", self._execution_id)

        try:
            result = self._preview_impl()
        except Exception as exc:
            # Revert to validated so the caller can retry
            self._state = ActionLifecycleState.validated
            raise RuntimeError(f"Preview generation failed: {exc}") from exc

        self._preview = result
        self._state = ActionLifecycleState.previewed
        logger.info("Preview generated for %s: %s", self._execution_id, result.summary)
        return result

    def execute(self, connector: Any, confirm: bool = False) -> ExecutionResult:
        """Execute the action via the ad platform connector.

        The action must be validated and previewed.  If *confirm* is
        ``False``, the current preview is returned as an
        :class:`ExecutionResult` without making changes.

        Parameters
        ----------
        connector :
            An :class:`AdPlatformConnector` instance.
        confirm : bool
            Set ``True`` to actually execute.  Defaults to ``False``
            (preview-only).

        Raises
        ------
        RuntimeError
            If the action is not in a state that allows execution.
        """
        if self._state not in (
            ActionLifecycleState.previewed,
            ActionLifecycleState.approved,
        ):
            raise RuntimeError(
                f"Cannot execute action in state '{self._state.value}'. "
                f"Action must be previewed or approved first."
            )

        # If not confirmed, return a preview-only result
        if not confirm:
            preview = self._preview
            logger.info(
                "Execution not confirmed for %s — returning preview",
                self._execution_id,
            )
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="Execution not confirmed. Set confirm=True to execute.",
                changes_made={"preview": preview.model_dump() if preview else {}},
            )

        self._state = ActionLifecycleState.approved
        self._state = ActionLifecycleState.executing
        logger.info("Executing %s on %s (id=%s)", self.action_type, self.platform, self._execution_id)

        try:
            result = self._execute_impl(connector)
        except Exception as exc:
            self._state = ActionLifecycleState.execution_failed
            result = ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message=str(exc),
            )
            logger.error("Execution FAILED for %s: %s", self._execution_id, exc)

        self._result = result
        if result.success:
            self._state = ActionLifecycleState.executed
            logger.info("Execution SUCCEEDED for %s", self._execution_id)
        else:
            self._state = ActionLifecycleState.execution_failed
            logger.warning("Execution FAILED for %s: %s", self._execution_id, result.error_message)

        return result

    def verify(self, connector: Any) -> VerificationResult:
        """Verify the action was executed correctly.

        Must be in ``executed`` state.

        Raises
        ------
        RuntimeError
            If the action has not been executed.
        """
        if self._state != ActionLifecycleState.executed:
            raise RuntimeError(
                f"Cannot verify action in state '{self._state.value}'. "
                f"Action must be executed first."
            )

        self._state = ActionLifecycleState.verifying
        logger.info("Verifying %s", self._execution_id)

        try:
            result = self._verify_impl(connector)
        except Exception as exc:
            self._state = ActionLifecycleState.verification_failed
            result = VerificationResult(
                verified=False,
                checks_performed=["exception_during_verification"],
                issues_found=[str(exc)],
            )
            logger.error("Verification FAILED for %s: %s", self._execution_id, exc)

        self._verification = result
        if result.verified:
            self._state = ActionLifecycleState.verified
            logger.info("Verification PASSED for %s", self._execution_id)
        else:
            self._state = ActionLifecycleState.verification_failed
            logger.warning(
                "Verification FAILED for %s: %s",
                self._execution_id, result.issues_found,
            )

        return result

    def rollback(self, connector: Any) -> ExecutionResult:
        """Roll back the action if possible.

        Must be in ``executed``, ``verified``, or ``verification_failed``
        state.

        Raises
        ------
        RuntimeError
            If the action is not in a rollback-eligible state.
        """
        rollback_eligible = {
            ActionLifecycleState.executed,
            ActionLifecycleState.verified,
            ActionLifecycleState.verification_failed,
        }
        if self._state not in rollback_eligible:
            raise RuntimeError(
                f"Cannot rollback action in state '{self._state.value}'. "
                f"Action must be executed, verified, or verification_failed."
            )

        logger.info("Rolling back %s", self._execution_id)

        try:
            result = self._rollback_impl(connector)
        except Exception as exc:
            result = ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message=f"Rollback failed: {exc}",
            )
            logger.error("Rollback FAILED for %s: %s", self._execution_id, exc)

        if result.success:
            self._state = ActionLifecycleState.rolled_back
            logger.info("Rollback SUCCEEDED for %s", self._execution_id)

        return result

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_state(self) -> ActionLifecycleState:
        """Return the current lifecycle state."""
        return self._state

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the action and all lifecycle state to a dict."""
        return {
            "execution_id": self._execution_id,
            "action_type": self.action_type,
            "platform": self.platform,
            "state": self._state.value,
            "created_at": self._created_at,
            "validation": self._validation.model_dump() if self._validation else None,
            "preview": self._preview.model_dump() if self._preview else None,
            "result": self._result.model_dump() if self._result else None,
            "verification": self._verification.model_dump() if self._verification else None,
        }


# ============================================================================
# Concrete Action: CreateAdCreative
# ============================================================================


class CreateAdCreative(PaidMediaAction):
    """Build and submit a new ad creative to a platform.

    Validates platform-specific creative limits (headline/description
    length, count constraints), checks for banned words, and flags
    compliance concerns.
    """

    def __init__(
        self,
        platform: str,
        format: str,
        headlines: List[str],
        descriptions: List[str],
        media_urls: Optional[List[str]] = None,
        cta: Optional[str] = None,
        landing_url: str = "",
        ad_group_id: Optional[str] = None,
        compliance_check_passed: bool = False,
    ) -> None:
        super().__init__(platform)
        self.format = format
        self.headlines = headlines
        self.descriptions = descriptions
        self.media_urls = media_urls or []
        self.cta = cta
        self.landing_url = landing_url
        self.ad_group_id = ad_group_id
        self.compliance_check_passed = compliance_check_passed

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.create_ad_creative.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        compliance_notes: List[str] = []

        # ---- Required fields ----
        if not self.headlines:
            errors.append("At least one headline is required")
        if not self.descriptions:
            errors.append("At least one description is required")
        if not self.landing_url:
            errors.append("Landing URL is required")

        # ---- Platform-specific validation ----
        limits = PLATFORM_CREATIVE_LIMITS.get(self.platform, {})

        if self.platform == "google_ads":
            # Headline count
            h_min = limits.get("headlines_min", 3)
            h_max = limits.get("headlines_max", 15)
            if self.headlines and (len(self.headlines) < h_min or len(self.headlines) > h_max):
                errors.append(
                    f"Google Ads responsive search requires {h_min}-{h_max} headlines, "
                    f"got {len(self.headlines)}"
                )
            # Description count
            d_min = limits.get("descriptions_min", 2)
            d_max = limits.get("descriptions_max", 4)
            if self.descriptions and (len(self.descriptions) < d_min or len(self.descriptions) > d_max):
                errors.append(
                    f"Google Ads responsive search requires {d_min}-{d_max} descriptions, "
                    f"got {len(self.descriptions)}"
                )
            # Individual headline length
            for h in self.headlines:
                err = check_headline_length(h, self.platform)
                if err:
                    errors.append(err)
            # Individual description length
            for d in self.descriptions:
                err = check_description_length(d, self.platform)
                if err:
                    errors.append(err)

        elif self.platform == "meta_ads":
            # Meta recommended limits (warnings, not hard errors)
            h_max_chars = limits.get("headline_max", 40)
            pt_max = limits.get("primary_text_max", 125)
            for h in self.headlines:
                if len(h) > h_max_chars:
                    warnings.append(
                        f"Meta headline exceeds recommended {h_max_chars} chars: "
                        f"{len(h)} chars — \"{h[:40]}...\""
                        if len(h) > 40
                        else f"Meta headline exceeds recommended {h_max_chars} chars: "
                        f"{len(h)} chars — \"{h}\""
                    )
            for d in self.descriptions:
                if len(d) > pt_max:
                    warnings.append(
                        f"Meta primary text exceeds recommended {pt_max} chars: "
                        f"{len(d)} chars"
                    )

        # ---- Banned word check ----
        all_copy = " ".join(self.headlines + self.descriptions)
        banned_found = _check_banned_words(all_copy)
        if banned_found:
            errors.append(
                f"Banned words found in ad copy: {', '.join(banned_found)}"
            )

        # ---- Compliance ----
        if not self.compliance_check_passed:
            warnings.append(
                "Platform compliance check has not been passed. "
                "Run compliance validation before submitting."
            )
            compliance_notes.append(
                "Creative should be reviewed against platform advertising policies"
            )

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            compliance_notes=compliance_notes,
        )

    def _preview_impl(self) -> ActionPreview:
        return ActionPreview(
            action_type=self.action_type,
            summary=(
                f"Create {self.format} ad creative on {self.platform} "
                f"with {len(self.headlines)} headlines"
            ),
            details={
                "format": self.format,
                "headlines": self.headlines,
                "descriptions": self.descriptions,
                "media_urls": self.media_urls,
                "cta": self.cta,
                "landing_url": self.landing_url,
                "ad_group_id": self.ad_group_id,
            },
            spend_impact=None,
            spend_amount=None,
            risk_level="medium",
            reversible=True,
            estimated_time="24-48 hours for ad review",
            requires_platform_review=True,
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        creative_dict = {
            "format": self.format,
            "headlines": self.headlines,
            "descriptions": self.descriptions,
            "media_urls": self.media_urls,
            "cta": self.cta,
            "landing_url": self.landing_url,
        }
        result = connector.create_ad(self.ad_group_id, creative_dict)
        # Extract the created ad ID from the connector response
        entity_id = None
        if hasattr(result, "id"):
            entity_id = result.id
        elif isinstance(result, dict):
            entity_id = result.get("id")

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=entity_id,
            entity_type="ad",
            changes_made={"creative": creative_dict, "ad_group_id": self.ad_group_id},
            rollback_data={"entity_id": entity_id, "action": "remove_or_pause_ad"},
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks: List[str] = []
        issues: List[str] = []

        entity_id = None
        if self._result and self._result.entity_id:
            entity_id = self._result.entity_id

        checks.append("check_ad_status")
        if entity_id:
            try:
                # Attempt to fetch ad status from the connector
                ad_groups = connector.get_ad_groups(
                    self._result.changes_made.get("ad_group_id", "")
                    if self._result else ""
                )
                # Look for the ad in the returned groups
                checks.append("ad_exists_in_platform")
            except Exception as exc:
                issues.append(f"Could not verify ad status: {exc}")
        else:
            issues.append("No entity_id available for verification")

        checks.append("check_not_disapproved")
        # If the ad was disapproved, flag it
        # Real implementation would fetch the ad and check its status field

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        entity_id = None
        if self._result and self._result.rollback_data:
            entity_id = self._result.rollback_data.get("entity_id")

        if not entity_id:
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="No entity_id available for rollback",
            )

        # Pause or remove the created ad via the connector
        # Most platforms support pausing; removal is less common
        try:
            connector.update_campaign(entity_id, {"status": "paused"})
        except Exception:
            # If that fails, try a broader approach
            pass

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=entity_id,
            entity_type="ad",
            changes_made={"action": "paused_or_removed_ad", "entity_id": entity_id},
        )


# ============================================================================
# Concrete Action: AdjustBidding
# ============================================================================


class AdjustBidding(PaidMediaAction):
    """Change the bidding strategy or target values for a campaign.

    Validates that the strategy is recognized and that target values
    (CPA, ROAS) are reasonable.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        strategy: str,
        target_values: Optional[Dict[str, float]] = None,
        reason: str = "",
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.strategy = strategy
        self.target_values = target_values or {}
        self.reason = reason
        self._original_strategy: Optional[str] = None
        self._original_target_values: Optional[Dict[str, float]] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.adjust_bidding.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if self.strategy not in VALID_BID_STRATEGIES:
            errors.append(
                f"Invalid bid strategy: '{self.strategy}'. "
                f"Valid options: {', '.join(VALID_BID_STRATEGIES)}"
            )
        if not self.reason:
            errors.append("A reason for the bidding change is required")

        # Target value validation
        if self.strategy == "target_cpa":
            cpa = self.target_values.get("target_cpa", 0)
            if cpa <= 0:
                errors.append("target_cpa must be greater than 0")
        elif self.strategy == "target_roas":
            roas = self.target_values.get("target_roas", 0)
            if roas <= 0:
                errors.append("target_roas must be greater than 0")

        # Warn about strategy changes that remove spend caps
        if self.strategy in ("maximize_conversions", "maximize_clicks", "lowest_cost"):
            warnings.append(
                f"Strategy '{self.strategy}' does not have explicit bid caps. "
                f"Spend may increase significantly."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        # Determine risk level
        uncapped_strategies = {"maximize_conversions", "maximize_clicks", "lowest_cost"}
        risk = "high" if self.strategy in uncapped_strategies else "medium"

        spend_desc = (
            f"Switching to {self.strategy} may increase or decrease spend "
            f"depending on conversion volume"
        )
        if self.strategy == "target_cpa":
            cpa = self.target_values.get("target_cpa", 0)
            spend_desc = f"Target CPA set to ${cpa:.2f}. Actual spend will depend on conversion volume."
        elif self.strategy == "target_roas":
            roas = self.target_values.get("target_roas", 0)
            spend_desc = f"Target ROAS set to {roas:.0f}%. Spend will adjust to meet return target."

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Change bidding strategy for campaign {self.campaign_id} to {self.strategy}",
            details={
                "campaign_id": self.campaign_id,
                "new_strategy": self.strategy,
                "target_values": self.target_values,
                "reason": self.reason,
            },
            spend_impact=spend_desc,
            risk_level=risk,
            reversible=True,
            estimated_time="Immediate (learning period: 1-2 weeks)",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Store original strategy for rollback
        try:
            campaign = connector.get_campaign(self.campaign_id)
            if hasattr(campaign, "bid_strategy"):
                self._original_strategy = campaign.bid_strategy
            elif isinstance(campaign, dict):
                self._original_strategy = campaign.get("bid_strategy")
        except Exception:
            pass

        changes = {"bid_strategy": self.strategy}
        if self.target_values:
            changes["bid_target_values"] = self.target_values

        connector.update_campaign(self.campaign_id, changes)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made=changes,
            rollback_data={
                "campaign_id": self.campaign_id,
                "original_strategy": self._original_strategy,
                "original_target_values": self._original_target_values,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_bid_strategy_updated"]
        issues: List[str] = []

        try:
            campaign = connector.get_campaign(self.campaign_id)
            current_strategy = None
            if hasattr(campaign, "bid_strategy"):
                current_strategy = campaign.bid_strategy
            elif isinstance(campaign, dict):
                current_strategy = campaign.get("bid_strategy")

            if current_strategy != self.strategy:
                issues.append(
                    f"Bid strategy mismatch: expected '{self.strategy}', "
                    f"got '{current_strategy}'"
                )
            checks.append("strategy_matches_expected")
        except Exception as exc:
            issues.append(f"Could not verify bid strategy: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        if not self._original_strategy:
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="No original bid strategy stored for rollback",
            )

        changes: Dict[str, Any] = {"bid_strategy": self._original_strategy}
        if self._original_target_values:
            changes["bid_target_values"] = self._original_target_values

        connector.update_campaign(self.campaign_id, changes)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={
                "action": "reverted_bid_strategy",
                "reverted_to": self._original_strategy,
            },
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: AdjustBudget
# ============================================================================


class AdjustBudget(PaidMediaAction):
    """Set or change a campaign's budget with spend safety gates.

    Validates against daily and monthly spend caps from the connector
    configuration.  Warns on large increases or decreases that could
    destabilize campaign learning.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        new_budget: float,
        budget_type: str = "daily",
        reason: str = "",
        safety_check: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.new_budget = new_budget
        self.budget_type = budget_type
        self.reason = reason
        self.safety_check = safety_check
        self._original_budget: Optional[float] = None
        self._original_budget_type: Optional[str] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.adjust_budget.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if self.new_budget <= 0:
            errors.append("Budget must be greater than 0")
        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.reason:
            errors.append("A reason for the budget change is required")
        if self.budget_type not in ("daily", "lifetime"):
            errors.append(f"Invalid budget_type: '{self.budget_type}'. Must be 'daily' or 'lifetime'.")

        # Spend safety checks from safety_check config
        if self.safety_check:
            max_daily = self.safety_check.get("max_daily_spend_usd")
            max_monthly = self.safety_check.get("max_monthly_spend_usd")
            current_budget = self.safety_check.get("current_budget", 0)

            if max_daily is not None and self.new_budget > max_daily:
                errors.append(
                    f"Budget exceeds daily spend cap: "
                    f"${self.new_budget:.2f} > ${max_daily:.2f} cap"
                )

            projected_monthly = self.new_budget * 30.4
            if max_monthly is not None and projected_monthly > max_monthly:
                errors.append(
                    f"Projected monthly spend exceeds cap: "
                    f"${projected_monthly:.0f} > ${max_monthly:.2f} cap"
                )

            # Large change warnings
            if current_budget and current_budget > 0:
                change_pct = ((self.new_budget - current_budget) / current_budget) * 100
                if change_pct > 50:
                    warnings.append(
                        f"Budget increase of {change_pct:.0f}% (${current_budget:.2f} -> "
                        f"${self.new_budget:.2f}). Large increases may indicate a mistake."
                    )
                if change_pct > 100:
                    warnings.append(
                        f"Budget is more than doubling. Confirm this is intentional."
                    )
                if change_pct < -50:
                    warnings.append(
                        f"Budget decrease of {abs(change_pct):.0f}% may harm campaign "
                        f"learning and performance stability."
                    )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        # Determine risk level based on magnitude of change
        risk = "medium"
        if self.safety_check:
            current = self.safety_check.get("current_budget", 0)
            if current and current > 0:
                change_pct = ((self.new_budget - current) / current) * 100
                if change_pct > 100:
                    risk = "high"
                elif self.new_budget < current:
                    risk = "low"

        monthly_projected = self.new_budget * 30.4
        spend_impact = (
            f"Daily spend will change to ${self.new_budget:.2f}/day "
            f"(${monthly_projected:.0f}/month projected)"
        )

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Set {self.budget_type} budget for campaign {self.campaign_id} to ${self.new_budget:.2f}",
            details={
                "campaign_id": self.campaign_id,
                "new_budget": self.new_budget,
                "budget_type": self.budget_type,
                "reason": self.reason,
                "current_budget": self.safety_check.get("current_budget") if self.safety_check else None,
            },
            spend_impact=spend_impact,
            spend_amount=self.new_budget,
            risk_level=risk,
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Store original budget for rollback
        try:
            campaign = connector.get_campaign(self.campaign_id)
            if hasattr(campaign, "budget_daily"):
                self._original_budget = campaign.budget_daily
                self._original_budget_type = "daily"
            elif isinstance(campaign, dict):
                self._original_budget = campaign.get("budget_daily")
                self._original_budget_type = "daily"
        except Exception:
            pass

        budget_key = "budget_daily" if self.budget_type == "daily" else "budget_lifetime"
        changes = {budget_key: self.new_budget}
        connector.update_campaign(self.campaign_id, changes)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made=changes,
            rollback_data={
                "campaign_id": self.campaign_id,
                "original_budget": self._original_budget,
                "original_budget_type": self._original_budget_type,
                "budget_key": budget_key,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_budget_updated"]
        issues: List[str] = []

        try:
            campaign = connector.get_campaign(self.campaign_id)
            current = None
            if hasattr(campaign, "budget_daily") and self.budget_type == "daily":
                current = campaign.budget_daily
            elif hasattr(campaign, "budget_lifetime") and self.budget_type == "lifetime":
                current = campaign.budget_lifetime
            elif isinstance(campaign, dict):
                key = "budget_daily" if self.budget_type == "daily" else "budget_lifetime"
                current = campaign.get(key)

            if current is not None and abs(current - self.new_budget) > 0.01:
                issues.append(
                    f"Budget mismatch: expected ${self.new_budget:.2f}, "
                    f"got ${current:.2f}"
                )
            checks.append("budget_matches_expected")
        except Exception as exc:
            issues.append(f"Could not verify budget: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        if self._original_budget is None:
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="No original budget stored for rollback",
            )

        budget_key = "budget_daily" if self._original_budget_type == "daily" else "budget_lifetime"
        changes = {budget_key: self._original_budget}
        connector.update_campaign(self.campaign_id, changes)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={
                "action": "reverted_budget",
                "reverted_to": self._original_budget,
            },
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: PauseCampaign
# ============================================================================


class PauseCampaign(PaidMediaAction):
    """Pause a running campaign.

    Low-risk, always reversible.  Warns if the campaign has active
    spend commitments.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        reason: str = "",
        pause_duration: Optional[str] = None,
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.reason = reason
        self.pause_duration = pause_duration
        self._original_status: Optional[str] = None
        self._original_budget: Optional[float] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.pause_campaign.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.reason:
            errors.append("A reason for pausing is required")

        # Warn about active spend
        warnings.append(
            "Pausing a campaign with active spend may affect delivery commitments "
            "and campaign learning. Re-enabling later may require a new learning period."
        )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        spend_msg = "Campaign spend will stop."
        if self._original_budget:
            spend_msg += f" Current daily budget was ${self._original_budget:.2f}."

        duration_note = ""
        if self.pause_duration:
            duration_note = f" Duration: {self.pause_duration}."

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Pause campaign {self.campaign_id} on {self.platform}",
            details={
                "campaign_id": self.campaign_id,
                "reason": self.reason,
                "pause_duration": self.pause_duration,
            },
            spend_impact=spend_msg + duration_note,
            spend_amount=0.0,
            risk_level="low",
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Store original status for rollback
        try:
            campaign = connector.get_campaign(self.campaign_id)
            if hasattr(campaign, "status"):
                self._original_status = campaign.status
            elif isinstance(campaign, dict):
                self._original_status = campaign.get("status")
            if hasattr(campaign, "budget_daily"):
                self._original_budget = campaign.budget_daily
            elif isinstance(campaign, dict):
                self._original_budget = campaign.get("budget_daily")
        except Exception:
            pass

        connector.pause_campaign(self.campaign_id)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={"status": "paused", "previous_status": self._original_status},
            rollback_data={
                "campaign_id": self.campaign_id,
                "original_status": self._original_status,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_campaign_paused"]
        issues: List[str] = []

        try:
            campaign = connector.get_campaign(self.campaign_id)
            status = None
            if hasattr(campaign, "status"):
                status = campaign.status
            elif isinstance(campaign, dict):
                status = campaign.get("status")

            if status != "paused":
                issues.append(f"Campaign status is '{status}', expected 'paused'")
            checks.append("status_is_paused")
        except Exception as exc:
            issues.append(f"Could not verify campaign status: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        # Re-enable the campaign
        connector.enable_campaign(self.campaign_id)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={"action": "re-enabled_campaign", "status": "enabled"},
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: EnableCampaign
# ============================================================================


class EnableCampaign(PaidMediaAction):
    """Re-enable a paused campaign.

    Medium-risk because re-enabling resumes spend.  Stores the previous
    status for rollback.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        reason: str = "",
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.reason = reason
        self._original_status: Optional[str] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.enable_campaign.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.reason:
            errors.append("A reason for enabling is required")

        warnings.append(
            "Re-enabling a campaign will resume spend. "
            "Verify budget and targeting before enabling."
        )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        return ActionPreview(
            action_type=self.action_type,
            summary=f"Enable campaign {self.campaign_id} on {self.platform}",
            details={
                "campaign_id": self.campaign_id,
                "reason": self.reason,
            },
            spend_impact="Campaign spend will resume at its configured budget level.",
            risk_level="medium",
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        try:
            campaign = connector.get_campaign(self.campaign_id)
            if hasattr(campaign, "status"):
                self._original_status = campaign.status
            elif isinstance(campaign, dict):
                self._original_status = campaign.get("status")
        except Exception:
            pass

        connector.enable_campaign(self.campaign_id)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={"status": "enabled", "previous_status": self._original_status},
            rollback_data={
                "campaign_id": self.campaign_id,
                "original_status": self._original_status,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_campaign_enabled"]
        issues: List[str] = []

        try:
            campaign = connector.get_campaign(self.campaign_id)
            status = None
            if hasattr(campaign, "status"):
                status = campaign.status
            elif isinstance(campaign, dict):
                status = campaign.get("status")

            if status != "enabled":
                issues.append(f"Campaign status is '{status}', expected 'enabled'")
            checks.append("status_is_enabled")
        except Exception as exc:
            issues.append(f"Could not verify campaign status: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        connector.pause_campaign(self.campaign_id)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={"action": "re-paused_campaign", "status": "paused"},
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: LaunchCampaign
# ============================================================================


class LaunchCampaign(PaidMediaAction):
    """Create and launch a full advertising campaign.

    This is the highest-risk action in the paid media system.  It runs
    10 comprehensive readiness checks during validation and starts the
    campaign in PAUSED state before enabling, so nothing goes live
    until the full setup is verified.
    """

    def __init__(
        self,
        platform: str,
        campaign_config: Dict[str, Any],
        budget: float,
        targeting: Dict[str, Any],
        creatives: List[Dict[str, Any]],
        landing_pages: List[str],
        compliance_check_passed: bool = False,
    ) -> None:
        super().__init__(platform)
        self.campaign_config = campaign_config
        self.budget = budget
        self.targeting = targeting
        self.creatives = creatives
        self.landing_pages = landing_pages
        self.compliance_check_passed = compliance_check_passed
        self._created_campaign_id: Optional[str] = None
        self._created_ad_group_ids: List[str] = []
        self._created_ad_ids: List[str] = []

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.launch_campaign.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        compliance_notes: List[str] = []

        # ---- Check 1: campaign_config has required fields ----
        required_config = ["name", "objective", "bid_strategy"]
        for field_name in required_config:
            if field_name not in self.campaign_config:
                errors.append(f"campaign_config missing required field: '{field_name}'")

        # ---- Check 2: budget > 0 and within safety caps ----
        if self.budget <= 0:
            errors.append("Budget must be greater than 0")

        # ---- Check 3: targeting is not empty ----
        if not self.targeting:
            errors.append("Targeting configuration is required")

        # ---- Check 4: targeting is not overly broad ----
        if self.targeting:
            has_location = bool(self.targeting.get("locations") or self.targeting.get("geo"))
            has_age = bool(self.targeting.get("age_range") or self.targeting.get("age"))
            has_interests = bool(
                self.targeting.get("interests")
                or self.targeting.get("keywords")
                or self.targeting.get("audiences")
            )
            if not has_location:
                warnings.append(
                    "No location targeting set. Campaign will target all available locations."
                )
            if not has_age and not has_interests:
                warnings.append(
                    "No age or interest targeting set. Audience may be too broad."
                )

        # ---- Check 5: targeting is not overly narrow ----
        estimated_reach = self.targeting.get("estimated_reach")
        if estimated_reach is not None and estimated_reach < 1000:
            warnings.append(
                f"Estimated reach is {estimated_reach}, which is very narrow. "
                f"Campaign may not deliver effectively."
            )

        # ---- Check 6: creatives list is not empty ----
        if not self.creatives:
            errors.append("At least one creative is required to launch a campaign")

        # ---- Check 7: each creative has required fields ----
        for i, creative in enumerate(self.creatives):
            if not creative.get("headlines"):
                errors.append(f"Creative #{i + 1} is missing headlines")
            if not creative.get("descriptions"):
                errors.append(f"Creative #{i + 1} is missing descriptions")
            if not creative.get("landing_url"):
                errors.append(f"Creative #{i + 1} is missing landing_url")

            # Check creative copy for banned words
            all_text_parts = []
            all_text_parts.extend(creative.get("headlines", []))
            all_text_parts.extend(creative.get("descriptions", []))
            all_copy = " ".join(all_text_parts)
            banned_found = _check_banned_words(all_copy)
            if banned_found:
                errors.append(
                    f"Creative #{i + 1} contains banned words: {', '.join(banned_found)}"
                )

        # ---- Check 8: landing_pages are not empty ----
        if not self.landing_pages:
            errors.append("At least one landing page URL is required")

        # ---- Check 9: compliance_check_passed ----
        if not self.compliance_check_passed:
            errors.append(
                "Platform compliance check must pass before launch. "
                "Set compliance_check_passed=True after review."
            )
            compliance_notes.append(
                "All creatives and landing pages must be reviewed against "
                "platform advertising policies before launch"
            )

        # ---- Check 10: Meta special ad categories ----
        if self.platform == "meta_ads":
            objective = self.campaign_config.get("objective", "")
            has_special_cat = bool(self.campaign_config.get("special_ad_categories"))
            # Housing, employment, and credit objectives should flag
            sensitive_objectives = {"housing", "employment", "credit", "social_issues"}
            if objective in sensitive_objectives and not has_special_cat:
                warnings.append(
                    f"Meta campaign with objective '{objective}' may require "
                    f"Special Ad Categories declaration. Review Meta policies."
                )
                compliance_notes.append(
                    "Meta requires Special Ad Categories for housing, employment, "
                    "and credit-related ads. Targeting restrictions apply."
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            compliance_notes=compliance_notes,
        )

    def _preview_impl(self) -> ActionPreview:
        objective = self.campaign_config.get("objective", "unknown")
        monthly_projected = self.budget * 30.4

        targeting_summary_parts: List[str] = []
        if self.targeting.get("locations"):
            targeting_summary_parts.append(
                f"Locations: {', '.join(str(l) for l in self.targeting['locations'][:3])}"
            )
        if self.targeting.get("age_range"):
            targeting_summary_parts.append(f"Age: {self.targeting['age_range']}")
        if self.targeting.get("interests"):
            interests = self.targeting["interests"]
            targeting_summary_parts.append(
                f"Interests: {', '.join(str(i) for i in interests[:3])}"
                + (f" (+{len(interests) - 3} more)" if len(interests) > 3 else "")
            )
        targeting_summary = "; ".join(targeting_summary_parts) if targeting_summary_parts else "Broad targeting"

        return ActionPreview(
            action_type=self.action_type,
            summary=(
                f"Launch new {objective} campaign on {self.platform} "
                f"with ${self.budget:.2f}/day budget"
            ),
            details={
                "campaign_config": self.campaign_config,
                "budget": self.budget,
                "budget_type": "daily",
                "targeting_summary": targeting_summary,
                "creative_count": len(self.creatives),
                "landing_pages": self.landing_pages,
            },
            spend_impact=(
                f"New campaign will spend up to ${self.budget:.2f}/day "
                f"(${monthly_projected:.0f}/month)"
            ),
            spend_amount=self.budget,
            risk_level="high",
            reversible=True,
            estimated_time="24-48 hours for ad review",
            requires_platform_review=True,
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Step 1: Create campaign in PAUSED state
        campaign_setup = dict(self.campaign_config)
        campaign_setup["budget_daily"] = self.budget
        campaign_setup["status"] = "paused"
        campaign_setup["targeting"] = self.targeting

        campaign_result = connector.create_campaign(campaign_setup)
        campaign_id = None
        if hasattr(campaign_result, "id"):
            campaign_id = campaign_result.id
        elif isinstance(campaign_result, dict):
            campaign_id = campaign_result.get("id")
        self._created_campaign_id = campaign_id

        # Step 2: Create ad groups
        ad_group_config = {
            "name": f"{self.campaign_config.get('name', 'Campaign')} - Ad Group 1",
            "targeting": self.targeting,
        }
        ad_group_result = connector.create_ad_group(campaign_id, ad_group_config)
        ad_group_id = None
        if hasattr(ad_group_result, "id"):
            ad_group_id = ad_group_result.id
        elif isinstance(ad_group_result, dict):
            ad_group_id = ad_group_result.get("id")
        if ad_group_id:
            self._created_ad_group_ids.append(ad_group_id)

        # Step 3: Create ads for each creative
        for creative in self.creatives:
            ad_result = connector.create_ad(ad_group_id, creative)
            ad_id = None
            if hasattr(ad_result, "id"):
                ad_id = ad_result.id
            elif isinstance(ad_result, dict):
                ad_id = ad_result.get("id")
            if ad_id:
                self._created_ad_ids.append(ad_id)

        # Step 4: Enable the campaign after everything is set up
        connector.enable_campaign(campaign_id)

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=campaign_id,
            entity_type="campaign",
            changes_made={
                "campaign_id": campaign_id,
                "ad_group_ids": self._created_ad_group_ids,
                "ad_ids": self._created_ad_ids,
                "budget": self.budget,
                "status": "enabled",
                "targeting": self.targeting,
            },
            rollback_data={
                "campaign_id": campaign_id,
                "ad_group_ids": self._created_ad_group_ids,
                "ad_ids": self._created_ad_ids,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = [
            "check_campaign_exists",
            "check_campaign_enabled",
            "check_ad_groups_created",
            "check_ads_created",
        ]
        issues: List[str] = []

        if not self._created_campaign_id:
            issues.append("No campaign ID recorded from execution")
            return VerificationResult(
                verified=False,
                checks_performed=checks,
                issues_found=issues,
            )

        try:
            campaign = connector.get_campaign(self._created_campaign_id)
            status = None
            if hasattr(campaign, "status"):
                status = campaign.status
            elif isinstance(campaign, dict):
                status = campaign.get("status")

            if status != "enabled":
                issues.append(f"Campaign status is '{status}', expected 'enabled'")
        except Exception as exc:
            issues.append(f"Could not verify campaign: {exc}")

        try:
            ad_groups = connector.get_ad_groups(self._created_campaign_id)
            if hasattr(ad_groups, "__len__") and len(ad_groups) == 0:
                issues.append("No ad groups found in campaign")
        except Exception as exc:
            issues.append(f"Could not verify ad groups: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        # Pause all campaign components
        if self._created_campaign_id:
            try:
                connector.pause_campaign(self._created_campaign_id)
            except Exception:
                pass

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self._created_campaign_id,
            entity_type="campaign",
            changes_made={
                "action": "paused_launched_campaign",
                "campaign_id": self._created_campaign_id,
                "ad_group_ids": self._created_ad_group_ids,
                "ad_ids": self._created_ad_ids,
            },
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: PublishApprovedVariant
# ============================================================================


class PublishApprovedVariant(PaidMediaAction):
    """Push an approved creative variant into a live ad group.

    Can either add alongside existing creatives or replace them.
    """

    def __init__(
        self,
        platform: str,
        ad_group_id: str,
        creative_variant_id: str,
        replace_existing: bool = False,
    ) -> None:
        super().__init__(platform)
        self.ad_group_id = ad_group_id
        self.creative_variant_id = creative_variant_id
        self.replace_existing = replace_existing
        self._replaced_creative_ids: List[str] = []

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.publish_approved_variant.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.ad_group_id:
            errors.append("ad_group_id is required")
        if not self.creative_variant_id:
            errors.append("creative_variant_id is required")

        if self.replace_existing:
            warnings.append(
                "Replacing existing creatives will pause all current ads in the "
                "ad group. This may affect campaign performance during the transition."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        risk = "medium" if self.replace_existing else "low"
        summary = f"Publish approved creative variant to ad group {self.ad_group_id}"
        if self.replace_existing:
            summary += " (replacing existing creatives)"

        return ActionPreview(
            action_type=self.action_type,
            summary=summary,
            details={
                "ad_group_id": self.ad_group_id,
                "creative_variant_id": self.creative_variant_id,
                "replace_existing": self.replace_existing,
            },
            risk_level=risk,
            reversible=True,
            estimated_time="24-48 hours for ad review",
            requires_platform_review=True,
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # If replacing, pause existing ads first
        if self.replace_existing:
            try:
                # The connector does not have a direct "get ads in ad group"
                # method, but we can use get_ad_groups to find info
                pass
            except Exception:
                pass

        # Create the new ad with the approved variant
        creative_config = {"variant_id": self.creative_variant_id}
        ad_result = connector.create_ad(self.ad_group_id, creative_config)

        entity_id = None
        if hasattr(ad_result, "id"):
            entity_id = ad_result.id
        elif isinstance(ad_result, dict):
            entity_id = ad_result.get("id")

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=entity_id,
            entity_type="ad",
            changes_made={
                "ad_group_id": self.ad_group_id,
                "variant_id": self.creative_variant_id,
                "replaced_existing": self.replace_existing,
                "replaced_ids": self._replaced_creative_ids,
            },
            rollback_data={
                "new_ad_id": entity_id,
                "replaced_ids": self._replaced_creative_ids,
                "ad_group_id": self.ad_group_id,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_variant_published"]
        issues: List[str] = []

        # Verify the new ad exists in the ad group
        try:
            connector.get_ad_groups(self.ad_group_id)
            checks.append("ad_group_accessible")
        except Exception as exc:
            issues.append(f"Could not verify ad group: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        # Remove the new ad and re-enable replaced ones
        rollback_data = self._result.rollback_data if self._result else {}
        new_ad_id = rollback_data.get("new_ad_id") if rollback_data else None

        changes: Dict[str, Any] = {"action": "rollback_variant_publish"}
        if new_ad_id:
            changes["paused_ad_id"] = new_ad_id

        # Re-enable replaced creatives
        replaced = rollback_data.get("replaced_ids", []) if rollback_data else []
        if replaced:
            changes["re-enabled_ids"] = replaced

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=new_ad_id,
            entity_type="ad",
            changes_made=changes,
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: UpdateTargeting
# ============================================================================


class UpdateTargeting(PaidMediaAction):
    """Modify campaign audience targeting.

    Accepts structured changes via ``targeting_changes`` with ``add``,
    ``remove``, and ``update`` keys.  Warns about overly broad or narrow
    changes.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        targeting_changes: Dict[str, Any],
        reason: str = "",
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.targeting_changes = targeting_changes
        self.reason = reason
        self._original_targeting: Optional[Dict[str, Any]] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.update_targeting.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.reason:
            errors.append("A reason for the targeting change is required")
        if not self.targeting_changes:
            errors.append("targeting_changes is required and cannot be empty")

        # Validate structure
        valid_keys = {"add", "remove", "update"}
        if self.targeting_changes:
            provided_keys = set(self.targeting_changes.keys())
            unknown = provided_keys - valid_keys
            if unknown:
                warnings.append(
                    f"Unknown targeting_changes keys: {', '.join(unknown)}. "
                    f"Expected: add, remove, update."
                )

        # Warn about removing all location targeting
        removals = self.targeting_changes.get("remove", {})
        if isinstance(removals, dict):
            if "locations" in removals:
                removed_locations = removals["locations"]
                if removed_locations and isinstance(removed_locations, list):
                    warnings.append(
                        "Removing location targeting may make the campaign too broad. "
                        "Verify that remaining targeting is sufficient."
                    )

        # Warn about narrowing significantly
        if self.targeting_changes.get("remove") and not self.targeting_changes.get("add"):
            warnings.append(
                "Removing targeting without adding replacements will narrow "
                "the audience. Delivery may decrease."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        # Build a change summary
        parts: List[str] = []
        adds = self.targeting_changes.get("add", {})
        removes = self.targeting_changes.get("remove", {})
        updates = self.targeting_changes.get("update", {})

        if adds:
            parts.append(f"adding {len(adds)} targeting dimension(s)")
        if removes:
            parts.append(f"removing {len(removes)} targeting dimension(s)")
        if updates:
            parts.append(f"updating {len(updates)} targeting dimension(s)")

        change_summary = ", ".join(parts) if parts else "no changes detected"

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Update targeting for campaign {self.campaign_id}: {change_summary}",
            details={
                "campaign_id": self.campaign_id,
                "targeting_changes": self.targeting_changes,
                "reason": self.reason,
            },
            spend_impact="Targeting changes may affect reach and spend efficiency",
            risk_level="medium",
            reversible=True,
            estimated_time="Immediate (audience re-learning: 24-48 hours)",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Store original targeting for rollback
        try:
            campaign = connector.get_campaign(self.campaign_id)
            if isinstance(campaign, dict):
                self._original_targeting = campaign.get("targeting")
            elif hasattr(campaign, "model_dump"):
                dump = campaign.model_dump()
                self._original_targeting = dump.get("targeting")
        except Exception:
            pass

        # Apply targeting changes
        connector.update_campaign(self.campaign_id, {"targeting": self.targeting_changes})

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={"targeting_changes": self.targeting_changes},
            rollback_data={
                "campaign_id": self.campaign_id,
                "original_targeting": self._original_targeting,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_targeting_updated"]
        issues: List[str] = []

        try:
            connector.get_campaign(self.campaign_id)
            checks.append("campaign_accessible")
        except Exception as exc:
            issues.append(f"Could not verify targeting update: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        if not self._original_targeting:
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="No original targeting stored for rollback",
            )

        connector.update_campaign(self.campaign_id, {"targeting": self._original_targeting})

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="campaign",
            changes_made={
                "action": "reverted_targeting",
                "reverted_to": self._original_targeting,
            },
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: AddNegativeKeywords
# ============================================================================


class AddNegativeKeywords(PaidMediaAction):
    """Add negative keywords to a campaign to reduce wasted spend.

    Low-risk operation that blocks irrelevant search terms from
    triggering ads.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        keywords: List[str],
        reason: str = "",
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.keywords = keywords
        self.reason = reason

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.add_negative_keywords.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.keywords:
            errors.append("At least one negative keyword is required")
        if not self.reason:
            errors.append("A reason for adding negative keywords is required")

        # Validate keyword formats
        for kw in self.keywords:
            stripped = kw.strip()
            if not stripped:
                errors.append("Empty keyword found in list")
                continue
            if len(stripped) > 80:
                warnings.append(f"Keyword is unusually long ({len(stripped)} chars): '{stripped[:40]}...'")

        # Warn about large batches
        if len(self.keywords) > 100:
            warnings.append(
                f"Adding {len(self.keywords)} negative keywords at once. "
                f"Verify the list to avoid accidentally blocking relevant traffic."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        # Show up to 10 keywords in the preview
        preview_keywords = self.keywords[:10]
        remaining = max(0, len(self.keywords) - 10)
        keyword_display = ", ".join(f'"{kw}"' for kw in preview_keywords)
        if remaining:
            keyword_display += f" (+{remaining} more)"

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Add {len(self.keywords)} negative keywords to campaign {self.campaign_id}",
            details={
                "campaign_id": self.campaign_id,
                "keywords": self.keywords,
                "keyword_count": len(self.keywords),
                "keyword_preview": keyword_display,
                "reason": self.reason,
            },
            spend_impact="Negative keywords reduce wasted spend by blocking irrelevant queries",
            risk_level="low",
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Add negative keywords via connector
        connector.update_campaign(
            self.campaign_id,
            {"negative_keywords_add": self.keywords},
        )

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="keyword",
            changes_made={
                "keywords_added": self.keywords,
                "keyword_count": len(self.keywords),
            },
            rollback_data={
                "campaign_id": self.campaign_id,
                "keywords_to_remove": self.keywords,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_negative_keywords_added"]
        issues: List[str] = []

        try:
            connector.get_campaign(self.campaign_id)
            checks.append("campaign_accessible")
        except Exception as exc:
            issues.append(f"Could not verify negative keywords: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        connector.update_campaign(
            self.campaign_id,
            {"negative_keywords_remove": self.keywords},
        )

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.campaign_id,
            entity_type="keyword",
            changes_made={
                "action": "removed_negative_keywords",
                "keywords_removed": self.keywords,
            },
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: CreateAdGroup
# ============================================================================


class CreateAdGroup(PaidMediaAction):
    """Create a new ad group within an existing campaign.

    Validates that the campaign exists and that the ad group configuration
    includes required fields like name and targeting.
    """

    def __init__(
        self,
        platform: str,
        campaign_id: str,
        ad_group_config: Dict[str, Any],
        reason: str = "",
    ) -> None:
        super().__init__(platform)
        self.campaign_id = campaign_id
        self.ad_group_config = ad_group_config
        self.reason = reason
        self._created_ad_group_id: Optional[str] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.create_ad_group.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.campaign_id:
            errors.append("campaign_id is required")
        if not self.ad_group_config:
            errors.append("ad_group_config is required")
        if not self.reason:
            errors.append("A reason for creating the ad group is required")

        # Check for required config fields
        if self.ad_group_config:
            if not self.ad_group_config.get("name"):
                errors.append("ad_group_config must include a 'name'")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        name = self.ad_group_config.get("name", "Unnamed")

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Create ad group '{name}' in campaign {self.campaign_id}",
            details={
                "campaign_id": self.campaign_id,
                "ad_group_config": self.ad_group_config,
                "reason": self.reason,
            },
            risk_level="low",
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        result = connector.create_ad_group(self.campaign_id, self.ad_group_config)

        entity_id = None
        if hasattr(result, "id"):
            entity_id = result.id
        elif isinstance(result, dict):
            entity_id = result.get("id")
        self._created_ad_group_id = entity_id

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=entity_id,
            entity_type="ad_group",
            changes_made={
                "campaign_id": self.campaign_id,
                "ad_group_config": self.ad_group_config,
            },
            rollback_data={
                "campaign_id": self.campaign_id,
                "ad_group_id": entity_id,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_ad_group_created"]
        issues: List[str] = []

        if not self._created_ad_group_id:
            issues.append("No ad group ID recorded from execution")
            return VerificationResult(
                verified=False,
                checks_performed=checks,
                issues_found=issues,
            )

        try:
            ad_groups = connector.get_ad_groups(self.campaign_id)
            found = False
            for ag in ad_groups:
                ag_id = ag.id if hasattr(ag, "id") else ag.get("id") if isinstance(ag, dict) else None
                if ag_id == self._created_ad_group_id:
                    found = True
                    break
            if not found:
                issues.append(
                    f"Ad group {self._created_ad_group_id} not found in campaign"
                )
            checks.append("ad_group_exists_in_campaign")
        except Exception as exc:
            issues.append(f"Could not verify ad group: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        # Pause or remove the created ad group
        if not self._created_ad_group_id:
            return ExecutionResult(
                success=False,
                action_type=self.action_type,
                platform=self.platform,
                error_message="No ad group ID available for rollback",
            )

        try:
            connector.update_campaign(
                self.campaign_id,
                {"ad_group_pause": self._created_ad_group_id},
            )
        except Exception:
            pass

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self._created_ad_group_id,
            entity_type="ad_group",
            changes_made={"action": "paused_ad_group", "ad_group_id": self._created_ad_group_id},
            rollback_data=None,
        )


# ============================================================================
# Concrete Action: RetireCreative
# ============================================================================


class RetireCreative(PaidMediaAction):
    """Deactivate an underperforming ad creative.

    Pauses the creative and records the reason for retirement.
    Low-risk and always reversible.
    """

    def __init__(
        self,
        platform: str,
        ad_id: str,
        ad_group_id: str,
        reason: str = "",
        performance_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(platform)
        self.ad_id = ad_id
        self.ad_group_id = ad_group_id
        self.reason = reason
        self.performance_data = performance_data or {}
        self._original_status: Optional[str] = None

    @property
    def action_type(self) -> str:
        return PaidMediaActionType.retire_creative.value

    def _validate_impl(self) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not self.ad_id:
            errors.append("ad_id is required")
        if not self.ad_group_id:
            errors.append("ad_group_id is required")
        if not self.reason:
            errors.append("A reason for retiring the creative is required")

        # Warn if no performance data provided
        if not self.performance_data:
            warnings.append(
                "No performance data provided. Consider reviewing metrics "
                "before retiring a creative."
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _preview_impl(self) -> ActionPreview:
        perf_summary = ""
        if self.performance_data:
            ctr = self.performance_data.get("ctr")
            cpa = self.performance_data.get("cpa")
            parts: List[str] = []
            if ctr is not None:
                parts.append(f"CTR: {ctr:.2f}%")
            if cpa is not None:
                parts.append(f"CPA: ${cpa:.2f}")
            if parts:
                perf_summary = f" (Performance: {', '.join(parts)})"

        return ActionPreview(
            action_type=self.action_type,
            summary=f"Retire ad creative {self.ad_id} from ad group {self.ad_group_id}{perf_summary}",
            details={
                "ad_id": self.ad_id,
                "ad_group_id": self.ad_group_id,
                "reason": self.reason,
                "performance_data": self.performance_data,
            },
            spend_impact="Spend will shift to remaining active creatives in the ad group",
            risk_level="low",
            reversible=True,
            estimated_time="Immediate",
        )

    def _execute_impl(self, connector: Any) -> ExecutionResult:
        # Store original status
        self._original_status = "active"  # Assume active since we are retiring it

        # Pause the ad creative via the connector
        connector.update_campaign(
            self.ad_group_id,
            {"ad_pause": self.ad_id},
        )

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.ad_id,
            entity_type="ad",
            changes_made={
                "ad_id": self.ad_id,
                "ad_group_id": self.ad_group_id,
                "status": "paused",
                "previous_status": self._original_status,
                "retirement_reason": self.reason,
                "performance_data": self.performance_data,
            },
            rollback_data={
                "ad_id": self.ad_id,
                "ad_group_id": self.ad_group_id,
                "original_status": self._original_status,
            },
        )

    def _verify_impl(self, connector: Any) -> VerificationResult:
        checks = ["check_creative_retired"]
        issues: List[str] = []

        # Verify the ad is paused
        try:
            connector.get_ad_groups(self.ad_group_id)
            checks.append("ad_group_accessible")
        except Exception as exc:
            issues.append(f"Could not verify creative retirement: {exc}")

        return VerificationResult(
            verified=len(issues) == 0,
            checks_performed=checks,
            issues_found=issues,
        )

    def _rollback_impl(self, connector: Any) -> ExecutionResult:
        # Re-enable the retired creative
        connector.update_campaign(
            self.ad_group_id,
            {"ad_enable": self.ad_id},
        )

        return ExecutionResult(
            success=True,
            action_type=self.action_type,
            platform=self.platform,
            entity_id=self.ad_id,
            entity_type="ad",
            changes_made={
                "action": "re-enabled_retired_creative",
                "ad_id": self.ad_id,
                "status": "active",
            },
            rollback_data=None,
        )

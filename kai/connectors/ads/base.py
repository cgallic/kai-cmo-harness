"""Base abstract connector and shared models for ad platform integrations.

Provides the ``AdPlatformConnector`` abstract base class and Pydantic data
models used by every ad-platform connector (Google Ads, Meta Ads, Google
Local Services Ads).  All mutating operations default to **dry-run** and
**sandbox** modes so that no real money is spent until the operator
explicitly opts in.
"""

from __future__ import annotations

import copy
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

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
# Configuration
# ============================================================================


class AdConnectorConfig(BaseModel):
    """Configuration for an ad platform connector.

    Both ``sandbox_mode`` and ``dry_run`` default to ``True`` so that no
    real API calls or mutating operations occur unless the operator
    explicitly opts in.
    """

    platform: str = Field(default="", description="Platform name: google_ads, meta_ads, local_services_ads")
    api_key: Optional[str] = Field(default=None, description="API key")
    api_secret: Optional[str] = Field(default=None, description="API secret / app secret")
    access_token: Optional[str] = Field(default=None, description="OAuth access token")
    refresh_token: Optional[str] = Field(default=None, description="OAuth refresh token")
    token_expiry: Optional[str] = Field(default=None, description="ISO timestamp of token expiry")
    account_id: str = Field(default="", description="Ad account ID (Google customer ID, Meta act_XXX, etc.)")
    manager_account_id: Optional[str] = Field(default=None, description="MCC / manager account ID if applicable")
    sandbox_mode: bool = Field(default=True, description="When True, no real API calls are made. DEFAULT IS TRUE.")
    dry_run: bool = Field(default=True, description="When True, mutating operations return preview without executing. DEFAULT IS TRUE.")
    rate_limit_rpm: int = Field(default=60, description="Maximum requests per minute")
    max_daily_spend_usd: Optional[float] = Field(default=None, description="Hard cap on daily spend this connector can set")
    max_monthly_spend_usd: Optional[float] = Field(default=None, description="Hard cap on monthly spend")
    spend_alert_threshold_pct: float = Field(default=80.0, description="Alert when this percentage of budget is consumed")
    currency: str = Field(default="USD", description="Account currency")
    timezone: str = Field(default="America/New_York", description="Account timezone")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional platform-specific configuration")


# ============================================================================
# Data Models
# ============================================================================


class CampaignSummary(BaseModel):
    """Summary of a single advertising campaign."""

    id: str = Field(default="", description="Platform campaign ID")
    name: str = Field(default="", description="Campaign name")
    platform: str = Field(default="", description="Platform name")
    status: str = Field(default="draft", description="enabled, paused, removed, ended, draft")
    objective: Optional[str] = Field(default=None, description="Campaign objective: awareness, traffic, leads, sales, app_installs")
    budget_daily: Optional[float] = Field(default=None, description="Daily budget in account currency")
    budget_lifetime: Optional[float] = Field(default=None, description="Lifetime budget")
    budget_remaining: Optional[float] = Field(default=None, description="Remaining budget (if lifetime)")
    spend_today: float = Field(default=0.0, description="Amount spent today")
    spend_total: float = Field(default=0.0, description="Total amount spent")
    start_date: Optional[str] = Field(default=None, description="Campaign start date")
    end_date: Optional[str] = Field(default=None, description="Campaign end date")
    bid_strategy: Optional[str] = Field(
        default=None,
        description="Bid strategy: manual_cpc, maximize_conversions, target_cpa, target_roas, maximize_clicks, lowest_cost",
    )
    ad_group_count: int = Field(default=0, description="Number of ad groups")
    ad_count: int = Field(default=0, description="Number of ads")


class AdGroupSummary(BaseModel):
    """Summary of a single ad group within a campaign."""

    id: str = Field(default="", description="Ad group ID")
    campaign_id: str = Field(default="", description="Parent campaign ID")
    name: str = Field(default="", description="Ad group name")
    status: str = Field(default="enabled", description="enabled, paused, removed")
    bid_amount: Optional[float] = Field(default=None, description="Default bid amount")
    ad_count: int = Field(default=0, description="Number of ads in group")
    targeting_summary: Optional[str] = Field(default=None, description="Human-readable targeting description")


class AdCreativeSummary(BaseModel):
    """Summary of a single ad creative."""

    id: str = Field(default="", description="Ad creative ID")
    ad_group_id: str = Field(default="", description="Parent ad group ID")
    campaign_id: str = Field(default="", description="Parent campaign ID")
    format: str = Field(
        default="single_image",
        description=(
            "Ad format: search_responsive, display_responsive, video, carousel, "
            "collection, single_image, single_video, local_services"
        ),
    )
    headlines: List[str] = Field(default_factory=list, description="Ad headlines")
    descriptions: List[str] = Field(default_factory=list, description="Ad descriptions")
    media_urls: List[str] = Field(default_factory=list, description="Media asset URLs")
    landing_url: Optional[str] = Field(default=None, description="Landing page URL")
    cta: Optional[str] = Field(default=None, description="Call to action")
    status: str = Field(default="under_review", description="active, paused, disapproved, under_review, removed")
    disapproval_reasons: List[str] = Field(default_factory=list, description="Reasons for disapproval")
    quality_score: Optional[float] = Field(default=None, description="Quality score (platform-specific)")
    relevance_score: Optional[float] = Field(default=None, description="Relevance / engagement score")


class AdMetrics(BaseModel):
    """Performance metrics for a campaign, ad group, or individual ad."""

    entity_id: str = Field(default="", description="Campaign, ad group, or ad ID")
    entity_type: str = Field(default="campaign", description="campaign, ad_group, ad")
    date_range: str = Field(default="", description="Date range, e.g. 2026-03-01:2026-03-31")
    impressions: int = Field(default=0)
    clicks: int = Field(default=0)
    ctr: float = Field(default=0.0, description="Click-through rate")
    conversions: float = Field(default=0.0)
    conversion_rate: float = Field(default=0.0)
    cost: float = Field(default=0.0, description="Total cost in account currency")
    cpc: float = Field(default=0.0, description="Cost per click")
    cpa: float = Field(default=0.0, description="Cost per acquisition")
    roas: float = Field(default=0.0, description="Return on ad spend")
    frequency: float = Field(default=0.0, description="Average times ad was shown per user")
    quality_score: Optional[float] = Field(default=None)
    relevance_score: Optional[float] = Field(default=None)
    impression_share: Optional[float] = Field(default=None, description="Share of eligible impressions captured")


class BudgetStatus(BaseModel):
    """Account-level budget and spend status."""

    account_id: str = Field(default="", description="Ad account ID")
    platform: str = Field(default="", description="Platform name")
    daily_budget_total: float = Field(default=0.0, description="Sum of all campaign daily budgets")
    daily_spend_today: float = Field(default=0.0, description="Total spent today across all campaigns")
    monthly_spend: float = Field(default=0.0, description="Total spend this month")
    monthly_budget_cap: Optional[float] = Field(default=None, description="Monthly budget cap from config")
    budget_utilization_pct: float = Field(default=0.0, description="monthly_spend / monthly_budget_cap * 100")
    projected_monthly_spend: float = Field(default=0.0, description="Extrapolated from daily spend pace")
    is_over_pace: bool = Field(default=False, description="True if projected > cap")
    alert_triggered: bool = Field(default=False, description="True if utilization > threshold")
    campaigns_active: int = Field(default=0)
    campaigns_paused: int = Field(default=0)


class SpendSafetyCheck(BaseModel):
    """Result of a spend safety check before a mutating budget operation."""

    operation: str = Field(default="", description="Operation being attempted")
    requested_amount: Optional[float] = Field(default=None, description="Budget being set or changed")
    current_daily_total: float = Field(default=0.0, description="Current total daily spend across campaigns")
    new_daily_total_if_approved: float = Field(default=0.0, description="Projected daily total after operation")
    monthly_cap: Optional[float] = Field(default=None, description="Monthly budget cap from config")
    projected_monthly_if_approved: float = Field(default=0.0, description="Projected monthly spend if approved")
    is_safe: bool = Field(default=True, description="True if no blocking issues")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    blocks: List[str] = Field(default_factory=list, description="Hard blocks that prevent the operation")


class RateLimitState(BaseModel):
    """Tracks rate limiting state for API calls."""

    requests_made: int = Field(default=0, description="Requests made in current window")
    requests_remaining: int = Field(default=60, description="Requests remaining in current window")
    window_reset_at: Optional[str] = Field(default=None, description="ISO timestamp when window resets")
    is_throttled: bool = Field(default=False, description="True if rate limit is exceeded")


# ============================================================================
# Abstract Base Connector
# ============================================================================


class AdPlatformConnector(ABC):
    """Abstract base class for ad platform connectors.

    Every ad connector enforces:
    - ``sandbox_mode=True`` by default (no real API calls)
    - ``dry_run=True`` by default (mutating ops return previews)
    - Spend safety checks before budget mutations
    - Rate limiting
    - Confirmation requirements for live mutations
    """

    def __init__(self, config: AdConnectorConfig) -> None:
        self.config = config
        self._rate_limit = RateLimitState(
            requests_remaining=config.rate_limit_rpm,
        )
        self._connected: bool = False
        logger.info(
            "Initialized %s connector for account %s (sandbox=%s, dry_run=%s)",
            self.platform_name,
            config.account_id,
            config.sandbox_mode,
            config.dry_run,
        )

    # ------------------------------------------------------------------
    # Abstract property
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the canonical platform name (e.g. 'google_ads')."""
        ...

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> bool:
        """Validate credentials and establish a connection to the platform.

        Returns ``True`` on success, ``False`` or raises on failure.
        """
        ...

    @abstractmethod
    def refresh_auth(self) -> bool:
        """Refresh OAuth tokens.  Returns ``True`` on success."""
        ...

    @abstractmethod
    def get_campaigns(self, status_filter: Optional[str] = None) -> List[CampaignSummary]:
        """List all campaigns, optionally filtered by status."""
        ...

    @abstractmethod
    def get_campaign(self, campaign_id: str) -> CampaignSummary:
        """Retrieve a single campaign by ID."""
        ...

    @abstractmethod
    def create_campaign(self, config: Dict[str, Any]) -> CampaignSummary:
        """Create a new campaign.  Requires ``dry_run=False`` to execute."""
        ...

    @abstractmethod
    def update_campaign(self, campaign_id: str, changes: Dict[str, Any]) -> CampaignSummary:
        """Update an existing campaign's settings."""
        ...

    @abstractmethod
    def pause_campaign(self, campaign_id: str) -> CampaignSummary:
        """Pause a running campaign."""
        ...

    @abstractmethod
    def enable_campaign(self, campaign_id: str) -> CampaignSummary:
        """Re-enable a paused campaign."""
        ...

    @abstractmethod
    def get_ad_groups(self, campaign_id: str) -> List[AdGroupSummary]:
        """List ad groups within a campaign."""
        ...

    @abstractmethod
    def create_ad_group(self, campaign_id: str, config: Dict[str, Any]) -> AdGroupSummary:
        """Create a new ad group within a campaign."""
        ...

    @abstractmethod
    def create_ad(self, ad_group_id: str, creative: Dict[str, Any]) -> AdCreativeSummary:
        """Create an ad creative within an ad group."""
        ...

    @abstractmethod
    def get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics:
        """Fetch performance metrics for a campaign, ad group, or ad."""
        ...

    @abstractmethod
    def get_budget_status(self) -> BudgetStatus:
        """Get current budget and spend status across the account."""
        ...

    # ------------------------------------------------------------------
    # Concrete helper methods
    # ------------------------------------------------------------------

    def _check_rate_limit(self) -> bool:
        """Check if we are within the rate limit window.

        Returns ``True`` if a request can proceed, ``False`` if throttled.
        """
        now = datetime.now(timezone.utc)

        # Reset window if expired
        if self._rate_limit.window_reset_at:
            try:
                reset_at = datetime.fromisoformat(self._rate_limit.window_reset_at)
                if reset_at.tzinfo is None:
                    reset_at = reset_at.replace(tzinfo=timezone.utc)
                if now >= reset_at:
                    self._rate_limit.requests_made = 0
                    self._rate_limit.requests_remaining = self.config.rate_limit_rpm
                    self._rate_limit.is_throttled = False
                    self._rate_limit.window_reset_at = None
            except (ValueError, TypeError):
                pass

        if self._rate_limit.requests_remaining <= 0:
            self._rate_limit.is_throttled = True
            logger.warning(
                "Rate limit exceeded for %s (account %s). Reset at %s",
                self.platform_name,
                self.config.account_id,
                self._rate_limit.window_reset_at,
            )
            return False

        return True

    def _record_request(self) -> None:
        """Increment the request counter and initialize the window if needed."""
        now = datetime.now(timezone.utc)
        self._rate_limit.requests_made += 1
        self._rate_limit.requests_remaining = max(
            0,
            self.config.rate_limit_rpm - self._rate_limit.requests_made,
        )

        # Start a new 60-second window on the first request
        if self._rate_limit.window_reset_at is None:
            from datetime import timedelta
            reset_at = now + timedelta(seconds=60)
            self._rate_limit.window_reset_at = reset_at.isoformat()

    def _is_sandbox(self) -> bool:
        """Return ``True`` if the connector is in sandbox mode."""
        return self.config.sandbox_mode

    def _is_dry_run(self) -> bool:
        """Return ``True`` if the connector is in dry-run mode."""
        return self.config.dry_run

    def _sandbox_response(self, method_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate a mock response for sandbox mode.

        Returns a dict tagged with ``_sandbox=True`` so callers can
        distinguish sandbox results from live data.
        """
        return {
            "_sandbox": True,
            "_method": method_name,
            "_platform": self.platform_name,
            "_account_id": self.config.account_id,
            "_timestamp": datetime.now(timezone.utc).isoformat(),
            "_kwargs": {k: v for k, v in kwargs.items() if not k.startswith("_")},
            "message": f"Sandbox mode — no live API call made for {method_name}",
        }

    def _spend_safety_check(
        self,
        operation: str,
        requested_amount: Optional[float] = None,
    ) -> SpendSafetyCheck:
        """Check whether a spend-related operation is safe.

        Validates against ``max_daily_spend_usd`` and
        ``max_monthly_spend_usd`` from the connector config.
        """
        warnings: List[str] = []
        blocks: List[str] = []

        # Live budget writes must be based on a real account snapshot. Fail
        # closed if the read-side evidence cannot be fetched.
        try:
            budget_status = self.get_budget_status()
        except Exception as exc:  # pragma: no cover - concrete connectors vary
            blocks.append(
                f"Unable to fetch current budget status before {operation}: {exc}"
            )
            return SpendSafetyCheck(
                operation=operation,
                requested_amount=requested_amount,
                current_daily_total=0.0,
                new_daily_total_if_approved=0.0,
                monthly_cap=self.config.max_monthly_spend_usd,
                projected_monthly_if_approved=0.0,
                is_safe=False,
                warnings=warnings,
                blocks=blocks,
            )

        current_daily_total = float(getattr(budget_status, "daily_budget_total", 0.0) or 0.0)
        new_daily_total = current_daily_total

        if requested_amount is not None:
            new_daily_total = current_daily_total + requested_amount

        # Daily cap check
        if self.config.max_daily_spend_usd is not None and requested_amount is not None:
            if new_daily_total > self.config.max_daily_spend_usd:
                blocks.append(
                    f"Daily spend cap would be exceeded: "
                    f"${new_daily_total:.2f} > ${self.config.max_daily_spend_usd:.2f} cap"
                )

        # Monthly projection (rough: daily * 30.4)
        projected_monthly = new_daily_total * 30.4

        # Monthly cap check
        if self.config.max_monthly_spend_usd is not None:
            if projected_monthly > self.config.max_monthly_spend_usd:
                blocks.append(
                    f"Monthly spend cap would be exceeded: "
                    f"projected ${projected_monthly:.2f} > ${self.config.max_monthly_spend_usd:.2f} cap"
                )

            # Alert threshold check (over threshold but under cap)
            if len(blocks) == 0 and self.config.max_monthly_spend_usd > 0:
                utilization_pct = (projected_monthly / self.config.max_monthly_spend_usd) * 100
                if utilization_pct >= self.config.spend_alert_threshold_pct:
                    warnings.append(
                        f"Spend is at {utilization_pct:.1f}% of monthly cap "
                        f"(${projected_monthly:.2f} / ${self.config.max_monthly_spend_usd:.2f})"
                    )

        is_safe = len(blocks) == 0

        return SpendSafetyCheck(
            operation=operation,
            requested_amount=requested_amount,
            current_daily_total=current_daily_total,
            new_daily_total_if_approved=new_daily_total,
            monthly_cap=self.config.max_monthly_spend_usd,
            projected_monthly_if_approved=projected_monthly,
            is_safe=is_safe,
            warnings=warnings,
            blocks=blocks,
        )

    def _require_confirmation(
        self,
        operation: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return a confirmation-required response for live mutations.

        When ``dry_run=False``, mutating operations should call this
        method first.  The caller must set ``confirm=True`` in a
        subsequent call to actually execute.
        """
        return {
            "requires_confirmation": True,
            "operation": operation,
            "platform": self.platform_name,
            "account_id": self.config.account_id,
            "details": details,
            "message": (
                "This operation will make live changes. "
                "Set confirm=True to proceed."
            ),
        }

    def _check_connected(self) -> None:
        """Raise ``ConnectionError`` if the connector is not connected."""
        if not self._connected:
            raise ConnectionError(
                f"{self.platform_name} connector is not connected. "
                f"Call connect() first."
            )

    def _check_mutating_allowed(self, operation: str) -> SpendSafetyCheck:
        """Combined gate for mutating operations.

        Checks sandbox mode, dry-run mode, connection status, and spend
        safety.  Returns a ``SpendSafetyCheck`` — if sandbox or dry-run
        are active the check passes with a mock result but the caller
        should return a preview instead of executing.
        """
        # Sandbox check — return a safe mock result
        if self._is_sandbox():
            logger.info(
                "Sandbox mode: %s on %s (account %s) — returning mock",
                operation,
                self.platform_name,
                self.config.account_id,
            )
            return SpendSafetyCheck(
                operation=operation,
                is_safe=True,
                warnings=["Sandbox mode — no real operation will be performed"],
            )

        # Dry-run check — return a safe mock result
        if self._is_dry_run():
            logger.info(
                "Dry-run mode: %s on %s (account %s) — returning preview",
                operation,
                self.platform_name,
                self.config.account_id,
            )
            return SpendSafetyCheck(
                operation=operation,
                is_safe=True,
                warnings=["Dry-run mode — operation will not be executed"],
            )

        # Connection check — will raise if not connected
        self._check_connected()

        # Spend safety check
        safety = self._spend_safety_check(operation)
        if not safety.is_safe:
            logger.warning(
                "Spend safety BLOCKED %s on %s: %s",
                operation,
                self.platform_name,
                safety.blocks,
            )
        elif safety.warnings:
            logger.warning(
                "Spend safety WARNING for %s on %s: %s",
                operation,
                self.platform_name,
                safety.warnings,
            )

        return safety

    def _api_call(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Placeholder for live HTTP API calls.

        Raises ``NotImplementedError`` when not in sandbox mode — real
        HTTP transport must be wired up before going live.
        """
        if self._is_sandbox():
            return self._sandbox_response(f"{method} {url}", **kwargs)

        raise NotImplementedError(
            "Live API calls not yet implemented — use sandbox mode"
        )

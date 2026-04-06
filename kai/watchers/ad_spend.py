"""Ad fatigue, spend anomaly, and ROAS watchers.

Task 070 — Monitors paid advertising performance, budget compliance, and
return on ad spend.  Catches creative fatigue, runaway spend, and
underperforming campaigns before they waste budget.

Watchers
--------
- **AdFatigueWatcher** (daily) — frequency, CTR decline, creative age.
- **SpendAnomalyWatcher** (daily) — budget overages, zero-spend, CPC/CPA spikes.
- **ROASWatcher** (weekly) — ROAS vs target, negative ROI, diminishing returns.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .framework import (
    FindingUrgency,
    Watcher,
    WatcherConfig,
    WatcherFinding,
    WatcherScheduleType,
    create_watcher_finding,
)

logger = logging.getLogger(__name__)


# ============================================================================
# AdFatigueWatcher
# ============================================================================


class AdFatigueWatcher(Watcher):
    """Monitors ad creative fatigue indicators: frequency, CTR decline, and creative age.

    Runs daily at 07:00 UTC.  Relevant for any archetype running paid ads.
    Catches the moment creative starts losing effectiveness so the operator
    can refresh before performance collapses.
    """

    name = "ad_fatigue"
    description = (
        "Monitors ad creative fatigue indicators: frequency, CTR decline, "
        "and creative age"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance: List[str] = []  # Any archetype running ads

    FATIGUE_THRESHOLDS = {
        "frequency_warning": 3.0,
        "frequency_critical": 5.0,
        "ctr_decline_warning": 0.20,
        "ctr_decline_critical": 0.40,
        "creative_age_warning": 21,   # days
        "creative_age_critical": 45,  # days
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """For each active ad campaign, check fatigue indicators.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and optionally ``ad_accounts``.
        workspace_state:
            Workspace state with ``active_campaigns`` list, each containing
            ``campaign_id``, ``campaign_name``, ``frequency``,
            ``current_ctr``, ``initial_ctr``, ``creative_launch_date``,
            and ``platform``.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        campaigns = _get_field(workspace_state, "active_campaigns", [])

        for campaign in campaigns:
            cid = campaign.get("campaign_id", "unknown")
            cname = campaign.get("campaign_name", "Unnamed Campaign")
            platform = campaign.get("platform", "unknown")

            # Frequency check
            freq = campaign.get("frequency")
            if freq is not None:
                finding = self._check_frequency(
                    cid, cname, freq, platform, business_id
                )
                if finding is not None:
                    findings.append(finding)

            # CTR decline check
            current_ctr = campaign.get("current_ctr")
            initial_ctr = campaign.get("initial_ctr")
            if current_ctr is not None and initial_ctr is not None:
                finding = self._check_ctr_decline(
                    cid, cname, current_ctr, initial_ctr, business_id
                )
                if finding is not None:
                    findings.append(finding)

            # Creative age check
            launch_date = campaign.get("creative_launch_date")
            if launch_date is not None:
                finding = self._check_creative_age(
                    cid, cname, launch_date, business_id
                )
                if finding is not None:
                    findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_frequency(
        self,
        campaign_id: str,
        campaign_name: str,
        frequency: float,
        platform: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Compare ad frequency against thresholds.

        Frequency is the average number of times each person in the target
        audience has seen the ad.  In production this metric comes from the
        ad platform's reporting API (e.g., Meta Ads frequency metric,
        Google Ads impression share data).
        """
        if frequency >= self.FATIGUE_THRESHOLDS["frequency_critical"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif frequency >= self.FATIGUE_THRESHOLDS["frequency_warning"]:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=f"Ad frequency too high on '{campaign_name}' ({frequency:.1f}x)",
            description=(
                f"Users in the target audience have seen the ad an average of "
                f"{frequency:.1f} times. High frequency causes ad blindness and "
                "negative brand sentiment. Consider expanding the audience, "
                "refreshing the creative, or adjusting frequency caps."
            ),
            suppression_key=f"ad_freq_{campaign_id}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="ad_performance",
            auto_eligible=False,
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "current_frequency": frequency,
                "threshold": (
                    self.FATIGUE_THRESHOLDS["frequency_critical"]
                    if severity == "high"
                    else self.FATIGUE_THRESHOLDS["frequency_warning"]
                ),
                "platform": platform,
            },
            proposed_action={
                "action_type": "creative_refresh",
                "description": (
                    "Audience expansion, creative refresh, or frequency cap "
                    "adjustment. Requires creative decision — not auto-eligible."
                ),
                "auto_eligible": False,
            },
        )

    def _check_ctr_decline(
        self,
        campaign_id: str,
        campaign_name: str,
        current_ctr: float,
        initial_ctr: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate CTR decline percentage from launch performance.

        CTR is click-through rate.  The initial CTR is the rate during the
        first 7 days of the campaign (honeymoon period).  Declining CTR
        is the strongest signal of creative fatigue.
        """
        if initial_ctr <= 0:
            return None

        decline_pct = (initial_ctr - current_ctr) / initial_ctr

        if decline_pct >= self.FATIGUE_THRESHOLDS["ctr_decline_critical"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif decline_pct >= self.FATIGUE_THRESHOLDS["ctr_decline_warning"]:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"CTR declining on '{campaign_name}' "
                f"(down {decline_pct * 100:.0f}% from launch)"
            ),
            description=(
                f"CTR on '{campaign_name}' dropped from {initial_ctr:.2%} at "
                f"launch to {current_ctr:.2%} now (a {decline_pct * 100:.0f}% "
                "decline). This signals creative fatigue. Consider new creative "
                "variants, audience refresh, or bid adjustment."
            ),
            suppression_key=f"ctr_decline_{campaign_id}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="ad_performance",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "current_ctr": current_ctr,
                "initial_ctr": initial_ctr,
                "decline_pct": round(decline_pct * 100, 1),
            },
            proposed_action={
                "action_type": "creative_variant",
                "description": (
                    "Generate new creative variants, test different ad formats, "
                    "or refresh the audience targeting."
                ),
                "auto_eligible": False,
            },
        )

    def _check_creative_age(
        self,
        campaign_id: str,
        campaign_name: str,
        creative_launch_date: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate days since creative launched and flag aging creative.

        Even if frequency and CTR look acceptable, long-running creative
        becomes stale.  The launch date comes from the ad platform's
        creative metadata.
        """
        try:
            launch_dt = datetime.fromisoformat(creative_launch_date)
            if launch_dt.tzinfo is None:
                launch_dt = launch_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

        days_running = (datetime.now(timezone.utc) - launch_dt).days

        if days_running >= self.FATIGUE_THRESHOLDS["creative_age_critical"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif days_running >= self.FATIGUE_THRESHOLDS["creative_age_warning"]:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Same creative running for {days_running} days "
                f"on '{campaign_name}'"
            ),
            description=(
                f"The creative for '{campaign_name}' has been running since "
                f"{creative_launch_date} ({days_running} days). Even with "
                "stable metrics, refreshing creative prevents fatigue buildup."
            ),
            suppression_key=f"creative_age_{campaign_id}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="ad_performance",
            auto_eligible=True,
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "creative_launch_date": creative_launch_date,
                "days_running": days_running,
            },
            proposed_action={
                "action_type": "generate_creative_variants",
                "description": (
                    "Generate new creative variants for review using the "
                    "variant engine. The system can auto-produce variants "
                    "for operator approval."
                ),
                "auto_eligible": True,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.DAILY.value,
            schedule_time="07:00",
            archetype_relevance=[],
            max_findings_per_run=15,
            suppression_window_days=3,
            cooldown_after_action_days=7,
        )


# ============================================================================
# SpendAnomalyWatcher
# ============================================================================


class SpendAnomalyWatcher(Watcher):
    """Monitors daily ad spend against budgets and flags overspend, underspend, and cost spikes.

    Runs daily at 08:00 UTC.  For local service businesses with tight
    budgets, catching a $50/day overspend early can mean the difference
    between profitable and unprofitable marketing.
    """

    name = "spend_anomaly"
    description = (
        "Monitors daily ad spend against budgets and flags overspend, "
        "underspend, and cost spikes"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance: List[str] = []  # Any archetype with ad spend

    SPEND_THRESHOLDS = {
        "overspend_warning": 1.2,
        "overspend_critical": 1.5,
        "projected_monthly_warning": 1.1,
        "zero_spend_check": True,
        "cpc_spike_threshold": 2.0,
        "cpa_spike_threshold": 2.0,
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check daily spend vs budget, projected monthly, zero-spend, and cost spikes.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``monthly_ad_budget_cap``.
        workspace_state:
            Workspace state with ``active_campaigns``, ``monthly_spend``,
            and ``days_remaining_in_month``.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        campaigns = _get_field(workspace_state, "active_campaigns", [])

        for campaign in campaigns:
            cid = campaign.get("campaign_id", "unknown")
            cname = campaign.get("campaign_name", "Unnamed Campaign")
            platform = campaign.get("platform", "unknown")

            # Daily spend vs budget
            daily_spend = campaign.get("daily_spend")
            daily_budget = campaign.get("daily_budget")
            if daily_spend is not None and daily_budget is not None and daily_budget > 0:
                finding = self._check_daily_spend(
                    cid, cname, daily_spend, daily_budget, platform, business_id
                )
                if finding is not None:
                    findings.append(finding)

            # Zero spend check
            status = campaign.get("status", "")
            if (
                self.SPEND_THRESHOLDS["zero_spend_check"]
                and daily_spend is not None
                and daily_spend == 0
                and status.lower() in ("active", "enabled")
            ):
                finding = self._check_zero_spend(
                    cid, cname, status, campaign.get("days_zero_spend", 1),
                    business_id,
                )
                if finding is not None:
                    findings.append(finding)

            # CPC spike check
            current_cpc = campaign.get("current_cpc")
            avg_cpc = campaign.get("avg_cpc_7day")
            if current_cpc is not None and avg_cpc is not None and avg_cpc > 0:
                finding = self._check_cost_spikes(
                    cid, cname, "CPC", current_cpc, avg_cpc, business_id
                )
                if finding is not None:
                    findings.append(finding)

            # CPA spike check
            current_cpa = campaign.get("current_cpa")
            avg_cpa = campaign.get("avg_cpa_7day")
            if current_cpa is not None and avg_cpa is not None and avg_cpa > 0:
                finding = self._check_cost_spikes(
                    cid, cname, "CPA", current_cpa, avg_cpa, business_id
                )
                if finding is not None:
                    findings.append(finding)

        # Projected monthly check
        monthly_spend = _get_field(workspace_state, "monthly_spend")
        monthly_cap = _get_field(business_profile, "monthly_ad_budget_cap")
        days_remaining = _get_field(workspace_state, "days_remaining_in_month")
        if (
            monthly_spend is not None
            and monthly_cap is not None
            and days_remaining is not None
            and monthly_cap > 0
        ):
            finding = self._check_projected_monthly(
                monthly_spend, monthly_cap, days_remaining, business_id
            )
            if finding is not None:
                findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_daily_spend(
        self,
        campaign_id: str,
        campaign_name: str,
        daily_spend: float,
        daily_budget: float,
        platform: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Compare daily spend to daily budget.

        In production the daily spend and budget come from the ad platform's
        reporting API.  Google Ads can exceed daily budgets by up to 2x on
        individual days (but averages over the month), so the thresholds
        account for normal variance.
        """
        spend_ratio = daily_spend / daily_budget

        if spend_ratio >= self.SPEND_THRESHOLDS["overspend_critical"]:
            severity = "critical"
            urgency = FindingUrgency.IMMEDIATE.value
        elif spend_ratio >= self.SPEND_THRESHOLDS["overspend_warning"]:
            severity = "warning"
            urgency = FindingUrgency.SOON.value
        else:
            return None

        overspend_pct = round((spend_ratio - 1.0) * 100, 1)

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Overspend alert: '{campaign_name}' spent "
                f"${daily_spend:.2f} vs ${daily_budget:.2f} budget"
            ),
            description=(
                f"Campaign '{campaign_name}' spent {overspend_pct}% over its "
                f"daily budget (${daily_spend:.2f} vs ${daily_budget:.2f}). "
                + (
                    "This is a critical overrun — consider pausing the campaign."
                    if severity == "critical"
                    else "Monitor closely and consider reducing the daily budget."
                )
            ),
            suppression_key=f"overspend_{campaign_id}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="ad_spend",
            auto_eligible=severity == "critical",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "daily_spend": daily_spend,
                "daily_budget": daily_budget,
                "overspend_pct": overspend_pct,
                "platform": platform,
            },
            proposed_action={
                "action_type": "reduce_budget" if severity == "warning" else "pause_campaign",
                "description": (
                    "Reduce daily budget to prevent further overspend."
                    if severity == "warning"
                    else "Pause campaign immediately and investigate the spend anomaly."
                ),
                "auto_eligible": True,
            },
        )

    def _check_projected_monthly(
        self,
        total_monthly_spend: float,
        monthly_cap: float,
        days_remaining: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate projected monthly spend based on daily run rate.

        Extrapolates the current daily run rate over the remaining days
        in the month and compares the projected total against the monthly
        budget cap.
        """
        if days_remaining <= 0:
            return None

        # Calculate days elapsed from spend
        now = datetime.now(timezone.utc)
        day_of_month = now.day
        days_elapsed = max(day_of_month, 1)
        daily_run_rate = total_monthly_spend / days_elapsed
        projected = total_monthly_spend + (daily_run_rate * days_remaining)

        threshold = monthly_cap * self.SPEND_THRESHOLDS["projected_monthly_warning"]

        if projected < threshold:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Projected monthly spend ${projected:.2f} exceeds "
                f"cap ${monthly_cap:.2f}"
            ),
            description=(
                f"At the current daily run rate of ${daily_run_rate:.2f}/day, "
                f"projected monthly spend is ${projected:.2f} against a "
                f"${monthly_cap:.2f} cap. Reduce daily budgets proportionally "
                "to stay within the cap."
            ),
            suppression_key=f"monthly_overspend_{business_id}",
            urgency=FindingUrgency.SOON.value,
            severity="warning",
            category="ad_spend",
            evidence={
                "current_monthly_spend": total_monthly_spend,
                "daily_run_rate": round(daily_run_rate, 2),
                "projected_monthly": round(projected, 2),
                "monthly_cap": monthly_cap,
                "days_remaining": days_remaining,
            },
            proposed_action={
                "action_type": "reduce_budgets",
                "description": (
                    "Reduce daily budgets proportionally across campaigns "
                    "to stay within the monthly cap."
                ),
                "auto_eligible": True,
            },
        )

    def _check_zero_spend(
        self,
        campaign_id: str,
        campaign_name: str,
        status: str,
        days_zero_spend: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag campaigns that are active but have zero spend.

        An active campaign with zero spend typically means ads have been
        disapproved by the platform, the payment method failed, or the
        targeting is too narrow to generate impressions.
        """
        possible_reasons = [
            "Ad disapproved by platform",
            "Payment method declined",
            "Targeting too narrow for impressions",
            "Campaign recently paused then re-enabled",
        ]

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Zero spend on active campaign '{campaign_name}' "
                "-- possible ad disapproval"
            ),
            description=(
                f"Campaign '{campaign_name}' is marked as {status} but has "
                f"had $0 spend for {days_zero_spend} day(s). This often "
                "indicates ad disapproval or a payment issue. Check the "
                "platform dashboard for disapproval notices."
            ),
            suppression_key=f"zero_spend_{campaign_id}_{business_id}",
            urgency=FindingUrgency.SOON.value,
            severity="warning",
            category="ad_spend",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "status": status,
                "days_zero_spend": days_zero_spend,
                "possible_reason": possible_reasons,
            },
            proposed_action={
                "action_type": "check_disapproval",
                "description": (
                    "Check the ad platform dashboard for disapproval notices. "
                    "Review ad copy for policy violations."
                ),
                "auto_eligible": False,
            },
        )

    def _check_cost_spikes(
        self,
        campaign_id: str,
        campaign_name: str,
        metric_name: str,
        current_value: float,
        average_value: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check CPC and CPA against 7-day averages.

        A spike above 2x the 7-day average often indicates increased
        competition, audience saturation, or a quality score drop.
        """
        threshold_key = (
            "cpc_spike_threshold"
            if metric_name == "CPC"
            else "cpa_spike_threshold"
        )
        threshold = self.SPEND_THRESHOLDS[threshold_key]
        spike_multiplier = current_value / average_value

        if spike_multiplier < threshold:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{metric_name} spike on '{campaign_name}': "
                f"${current_value:.2f} vs ${average_value:.2f} avg"
            ),
            description=(
                f"{metric_name} on '{campaign_name}' is "
                f"{spike_multiplier:.1f}x the 7-day average "
                f"(${current_value:.2f} vs ${average_value:.2f}). This may "
                "indicate increased competition, audience saturation, or a "
                "quality score drop."
            ),
            suppression_key=f"{metric_name.lower()}_spike_{campaign_id}_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="warning",
            category="ad_spend",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "metric_name": metric_name,
                "current_value": current_value,
                "average_value": average_value,
                "spike_multiplier": round(spike_multiplier, 2),
            },
            proposed_action={
                "action_type": "bid_adjustment",
                "description": (
                    "Review bid strategy, check audience overlap, and assess "
                    "the competitive landscape."
                ),
                "auto_eligible": False,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.DAILY.value,
            schedule_time="08:00",
            archetype_relevance=[],
            max_findings_per_run=20,
            suppression_window_days=1,
        )


# ============================================================================
# ROASWatcher
# ============================================================================


class ROASWatcher(Watcher):
    """Monitors return on ad spend and flags underperforming campaigns and diminishing returns.

    Runs weekly on Mondays at 09:00 UTC.  Relevant for all archetypes with
    ad spend.  ROAS is the ultimate measure of whether ad dollars are
    generating revenue.
    """

    name = "roas_monitor"
    description = (
        "Monitors return on ad spend and flags underperforming campaigns "
        "and diminishing returns"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance: List[str] = []  # Any archetype with ad spend

    ROAS_THRESHOLDS = {
        "below_target_days": 14,
        "negative_roi_days": 7,
        "diminishing_returns_pct": 0.20,
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check per-campaign ROAS, negative ROI, and diminishing returns.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``target_roas``.
        workspace_state:
            Workspace state with ``campaign_roas_data`` list containing
            per-campaign ROAS metrics, spend, revenue, and trend data.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        target_roas = _get_field(business_profile, "target_roas", 3.0)
        campaigns = _get_field(workspace_state, "campaign_roas_data", [])

        for campaign in campaigns:
            cid = campaign.get("campaign_id", "unknown")
            cname = campaign.get("campaign_name", "Unnamed Campaign")

            # ROAS below target
            current_roas = campaign.get("current_roas")
            days_below = campaign.get("days_below_target", 0)
            if current_roas is not None:
                finding = self._check_roas_below_target(
                    cid, cname, current_roas, target_roas, days_below,
                    campaign.get("total_spend_in_period", 0), business_id,
                )
                if finding is not None:
                    findings.append(finding)

            # Negative ROI
            spend = campaign.get("spend", 0)
            revenue = campaign.get("revenue", 0)
            days_negative = campaign.get("days_negative_roi", 0)
            if spend > 0 and revenue < spend:
                finding = self._check_negative_roi(
                    cid, cname, spend, revenue, days_negative, business_id
                )
                if finding is not None:
                    findings.append(finding)

            # Diminishing returns
            spend_trend = campaign.get("spend_trend", [])
            roas_trend = campaign.get("roas_trend", [])
            if len(spend_trend) >= 3 and len(roas_trend) >= 3:
                finding = self._check_diminishing_returns(
                    cid, cname, spend_trend, roas_trend, business_id
                )
                if finding is not None:
                    findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_roas_below_target(
        self,
        campaign_id: str,
        campaign_name: str,
        current_roas: float,
        target_roas: float,
        days_below: int,
        total_spend_in_period: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag campaigns with ROAS below target for an extended period.

        ROAS (Return On Ad Spend) = revenue / spend.  A target of 3.0x
        means $3 revenue per $1 spent.  Persistent underperformance beyond
        the threshold indicates the campaign is not profitable.
        """
        if current_roas >= target_roas:
            return None
        if days_below < self.ROAS_THRESHOLDS["below_target_days"]:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"ROAS below target on '{campaign_name}' for {days_below} "
                f"days ({current_roas:.1f}x vs {target_roas:.1f}x target)"
            ),
            description=(
                f"'{campaign_name}' has been below the {target_roas:.1f}x ROAS "
                f"target for {days_below} days (current: {current_roas:.1f}x). "
                f"Total spend in this period: ${total_spend_in_period:.2f}. "
                "Consider pausing, reallocating budget to better performers, "
                "or refreshing creative."
            ),
            suppression_key=f"roas_below_{campaign_id}_{business_id}",
            urgency=FindingUrgency.SOON.value,
            severity="high",
            category="ad_performance",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "current_roas": current_roas,
                "target_roas": target_roas,
                "days_below": days_below,
                "total_spend_in_period": total_spend_in_period,
            },
            proposed_action={
                "action_type": "pause_or_reallocate",
                "description": (
                    "Pause the campaign and reallocate budget to better "
                    "performing campaigns, or refresh creative and audience."
                ),
                "auto_eligible": False,
            },
        )

    def _check_negative_roi(
        self,
        campaign_id: str,
        campaign_name: str,
        spend: float,
        revenue: float,
        days_negative: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag campaigns with negative ROI (spend exceeds revenue) for extended periods.

        A campaign with negative ROI is actively losing money.  Higher-spend
        campaigns get critical severity; lower-spend get high.
        """
        if days_negative < self.ROAS_THRESHOLDS["negative_roi_days"]:
            return None

        roi = ((revenue - spend) / spend) * 100 if spend > 0 else 0
        daily_spend = spend / max(days_negative, 1)

        # Critical if spending more than $100/day with negative ROI
        severity = "critical" if daily_spend > 100 else "high"
        urgency = (
            FindingUrgency.IMMEDIATE.value
            if severity == "critical"
            else FindingUrgency.SOON.value
        )
        auto_eligible = severity == "critical"

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Negative ROI on '{campaign_name}' for {days_negative} days "
                f"(spent ${spend:.2f}, earned ${revenue:.2f})"
            ),
            description=(
                f"'{campaign_name}' has a {roi:.0f}% ROI — spending more than "
                f"it earns — for {days_negative} consecutive days. "
                + (
                    "At over $100/day spend, this is burning through budget quickly. "
                    "Pause immediately."
                    if severity == "critical"
                    else "Reduce budget or pause until the root cause is identified."
                )
            ),
            suppression_key=f"negative_roi_{campaign_id}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="ad_performance",
            auto_eligible=auto_eligible,
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "spend": spend,
                "revenue": revenue,
                "roi": round(roi, 1),
                "days_negative": days_negative,
            },
            proposed_action={
                "action_type": "pause_campaign" if severity == "critical" else "reduce_budget",
                "description": (
                    "Pause campaign immediately to stop losses."
                    if severity == "critical"
                    else "Reduce budget significantly until performance improves."
                ),
                "auto_eligible": auto_eligible,
            },
        )

    def _check_diminishing_returns(
        self,
        campaign_id: str,
        campaign_name: str,
        spend_trend: List[float],
        roas_trend: List[float],
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Detect pattern: spend increasing while ROAS decreasing.

        Diminishing returns means pushing more budget into a campaign that
        is becoming less efficient.  The optimal spend level is roughly
        where the ROAS trend started declining.

        Both trends are lists of weekly values (most recent last).
        """
        if len(spend_trend) < 3 or len(roas_trend) < 3:
            return None

        # Determine trend direction using simple linear comparison
        spend_increasing = spend_trend[-1] > spend_trend[0]
        roas_decreasing = roas_trend[-1] < roas_trend[0]

        if not (spend_increasing and roas_decreasing):
            return None

        # Calculate ROAS decline percentage
        if roas_trend[0] <= 0:
            return None
        roas_decline_pct = (roas_trend[0] - roas_trend[-1]) / roas_trend[0]

        if roas_decline_pct < self.ROAS_THRESHOLDS["diminishing_returns_pct"]:
            return None

        # Estimate optimal spend: the spend level when ROAS was highest
        best_roas_idx = roas_trend.index(max(roas_trend))
        optimal_spend_estimate = (
            spend_trend[best_roas_idx]
            if best_roas_idx < len(spend_trend)
            else spend_trend[0]
        )

        spend_direction = "increasing" if spend_increasing else "stable"
        roas_direction = "decreasing" if roas_decreasing else "stable"

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Diminishing returns on '{campaign_name}': "
                "spend up but ROAS declining"
            ),
            description=(
                f"Spend on '{campaign_name}' has been increasing while ROAS "
                f"has declined by {roas_decline_pct * 100:.0f}%. The campaign "
                f"is hitting diminishing returns. Estimated optimal weekly "
                f"spend is around ${optimal_spend_estimate:.2f}."
            ),
            suppression_key=f"diminishing_{campaign_id}_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="medium",
            category="ad_performance",
            evidence={
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "spend_trend_direction": spend_direction,
                "roas_trend_direction": roas_direction,
                "optimal_spend_estimate": round(optimal_spend_estimate, 2),
                "roas_decline_pct": round(roas_decline_pct * 100, 1),
                "spend_trend": spend_trend,
                "roas_trend": roas_trend,
            },
            proposed_action={
                "action_type": "reduce_to_optimal",
                "description": (
                    f"Reduce weekly spend to ~${optimal_spend_estimate:.2f} "
                    "and test new audiences to find fresh pockets of efficiency."
                ),
                "auto_eligible": False,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="monday_09:00",
            archetype_relevance=[],
            max_findings_per_run=10,
            suppression_window_days=7,
        )


# ============================================================================
# Helpers
# ============================================================================


def _get_business_id(profile: Any) -> str:
    if hasattr(profile, "id"):
        return str(profile.id)
    if isinstance(profile, dict):
        return str(profile.get("id", "unknown"))
    return "unknown"


def _get_field(obj: Any, field: str, default: Any = None) -> Any:
    if hasattr(obj, field):
        return getattr(obj, field)
    if isinstance(obj, dict):
        return obj.get(field, default)
    return default

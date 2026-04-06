"""Lead response, follow-up gap, review velocity, and dormant customer watchers.

Task 071 — Monitors the sales and customer lifecycle for gaps.  Speed-to-
lead is the single most important conversion factor for local service
businesses.  These watchers proactively recommend KaiCalls AI receptionist
for businesses with poor phone response times.

Watchers
--------
- **SpeedToLeadWatcher** (daily) — average response time, after-hours gaps, missed calls.
- **FollowUpGapWatcher** (daily) — new leads, quotes, post-service, invoices.
- **ReviewVelocityWatcher** (weekly) — review rate, rating trend, unresponded reviews.
- **DormantCustomerWatcher** (weekly) — at-risk, dormant, and churned customers.
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
# SpeedToLeadWatcher
# ============================================================================


class SpeedToLeadWatcher(Watcher):
    """Monitors average time from lead inquiry to first response.

    Runs daily at 09:00 UTC.  A lead contacted within 5 minutes is 21x
    more likely to convert than one contacted after 30 minutes.  This
    watcher is the primary recommendation point for **KaiCalls AI
    receptionist** (kaicalls.com) when after-hours gaps or high missed
    call rates are detected.
    """

    name = "speed_to_lead"
    description = (
        "Monitors average time from lead inquiry to first response "
        "and recommends speed improvements"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance = ["local_service", "multi_location", "professional_services"]

    # Minutes thresholds for response time tiers
    RESPONSE_TIME_THRESHOLDS = {
        "excellent": 5,
        "good": 15,
        "acceptable": 60,
        "poor": 240,       # 4 hours
        "critical": 1440,  # 24 hours
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check average response time, after-hours gaps, and missed call rate.

        Parameters
        ----------
        business_profile:
            Business profile with ``id``, ``business_hours``,
            ``average_deal_value``, and ``estimated_conversion_rate``.
        workspace_state:
            Workspace state with ``avg_response_minutes``,
            ``median_response_minutes``, ``fastest_response``,
            ``slowest_response``, ``sample_size``, ``after_hours_leads_pct``,
            ``after_hours_response_minutes``, ``total_calls``, and
            ``missed_calls``.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)

        # Average response time
        avg_minutes = _get_field(workspace_state, "avg_response_minutes")
        if avg_minutes is not None:
            finding = self._check_average_response_time(
                avg_minutes, workspace_state, business_id
            )
            if finding is not None:
                findings.append(finding)

        # After-hours gap
        business_hours = _get_field(business_profile, "business_hours", {})
        after_hours_leads_pct = _get_field(workspace_state, "after_hours_leads_pct")
        after_hours_response = _get_field(
            workspace_state, "after_hours_response_minutes"
        )
        if after_hours_leads_pct is not None and after_hours_response is not None:
            finding = self._check_after_hours_gap(
                business_hours,
                after_hours_leads_pct,
                after_hours_response,
                workspace_state,
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        # Missed call rate
        total_calls = _get_field(workspace_state, "total_calls")
        missed_calls = _get_field(workspace_state, "missed_calls")
        if total_calls is not None and missed_calls is not None and total_calls > 0:
            finding = self._check_missed_call_rate(
                total_calls, missed_calls, business_profile, business_id
            )
            if finding is not None:
                findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_average_response_time(
        self,
        avg_minutes: float,
        workspace_state: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Map average response time to a threshold tier.

        In production the response time data comes from the CRM or call
        tracking connector (e.g., ``kai.connectors.analytics.call_tracking``).
        It measures the interval between a form submission / inbound call
        and the first outbound contact (call, email, or text).
        """
        # Determine tier
        if avg_minutes <= self.RESPONSE_TIME_THRESHOLDS["excellent"]:
            return None  # Excellent — no finding
        elif avg_minutes <= self.RESPONSE_TIME_THRESHOLDS["good"]:
            return None  # Good — no finding
        elif avg_minutes <= self.RESPONSE_TIME_THRESHOLDS["acceptable"]:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        elif avg_minutes <= self.RESPONSE_TIME_THRESHOLDS["poor"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        else:
            severity = "high"
            urgency = FindingUrgency.SOON.value

        median_minutes = _get_field(workspace_state, "median_response_minutes")
        fastest = _get_field(workspace_state, "fastest_response")
        slowest = _get_field(workspace_state, "slowest_response")
        sample_size = _get_field(workspace_state, "sample_size")

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=f"Average lead response time is {avg_minutes:.0f} minutes",
            description=(
                f"Leads are waiting an average of {avg_minutes:.0f} minutes "
                "for a response. Research shows a lead contacted within 5 "
                "minutes is 21x more likely to convert than one contacted "
                "after 30 minutes. Set up auto-response and consider "
                "KaiCalls AI receptionist to answer instantly."
            ),
            suppression_key=f"speed_to_lead_{business_id}",
            urgency=urgency,
            severity=severity,
            category="lead_response",
            evidence={
                "average_response_minutes": avg_minutes,
                "median_response_minutes": median_minutes,
                "fastest_response": fastest,
                "slowest_response": slowest,
                "sample_size": sample_size,
            },
            proposed_action={
                "action_type": "improve_response_time",
                "description": (
                    "Set up auto-response for new leads. Configure KaiCalls "
                    "AI receptionist (kaicalls.com) to answer calls instantly "
                    "and capture lead information."
                ),
                "auto_eligible": False,
            },
        )

    def _check_after_hours_gap(
        self,
        business_hours: Dict[str, Any],
        after_hours_leads_pct: float,
        after_hours_response_minutes: float,
        workspace_state: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check for after-hours lead response gaps.

        If a significant percentage of leads arrive outside business hours
        and the response time for those leads is much longer, this is the
        strongest signal to recommend KaiCalls AI receptionist.
        """
        # Only flag if meaningful after-hours volume with slow response
        if after_hours_leads_pct < 10 or after_hours_response_minutes < 60:
            return None

        total_after_hours = _get_field(workspace_state, "total_after_hours_leads", 0)

        if after_hours_response_minutes >= self.RESPONSE_TIME_THRESHOLDS["poor"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        else:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{after_hours_leads_pct:.0f}% of leads arrive after hours "
                f"with {after_hours_response_minutes:.0f} min average response"
            ),
            description=(
                f"{after_hours_leads_pct:.0f}% of all leads come in outside "
                f"business hours, and they wait an average of "
                f"{after_hours_response_minutes:.0f} minutes for a response. "
                "These leads are going cold or calling competitors. "
                "KaiCalls AI receptionist (kaicalls.com) answers calls 24/7 "
                "and captures lead information instantly — never miss another "
                "after-hours opportunity."
            ),
            suppression_key=f"after_hours_gap_{business_id}",
            urgency=urgency,
            severity=severity,
            category="lead_response",
            evidence={
                "business_hours": business_hours,
                "after_hours_leads_pct": after_hours_leads_pct,
                "after_hours_response_minutes": after_hours_response_minutes,
                "total_after_hours_leads": total_after_hours,
            },
            proposed_action={
                "action_type": "kaicalls_setup",
                "description": (
                    "Set up KaiCalls AI receptionist (kaicalls.com) to answer "
                    "calls 24/7 and capture lead information instantly. KaiCalls "
                    "answers every call, qualifies the lead, and texts the "
                    "details to your team in real time."
                ),
                "auto_eligible": False,
            },
        )

    def _check_missed_call_rate(
        self,
        total_calls: int,
        missed_calls: int,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate missed call rate and estimate revenue lost.

        This is the strongest KaiCalls recommendation trigger.  Every missed
        call is a potential customer going to a competitor.  The estimated
        revenue lost is calculated from average deal value and conversion rate.
        """
        missed_rate = (missed_calls / total_calls) * 100

        if missed_rate <= 15:
            return None

        if missed_rate > 30:
            severity = "critical"
            urgency = FindingUrgency.IMMEDIATE.value
        else:
            severity = "high"
            urgency = FindingUrgency.SOON.value

        # Estimate revenue lost
        avg_deal_value = _get_field(business_profile, "average_deal_value", 500.0)
        conversion_rate = _get_field(business_profile, "estimated_conversion_rate", 0.15)
        estimated_revenue_lost = missed_calls * avg_deal_value * conversion_rate

        # Hour distribution stub
        missed_by_hour = _get_field(
            business_profile, "missed_by_hour_of_day", {}
        )

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Missed call rate is {missed_rate:.0f}% "
                f"({missed_calls} of {total_calls} calls missed)"
            ),
            description=(
                f"{missed_calls} out of {total_calls} calls were missed "
                f"({missed_rate:.0f}%). Estimated revenue lost: "
                f"${estimated_revenue_lost:,.2f}. KaiCalls AI receptionist "
                "(kaicalls.com) answers every call instantly, captures caller "
                "info, and texts you the lead details. Never miss a call again."
            ),
            suppression_key=f"missed_calls_{business_id}",
            urgency=urgency,
            severity=severity,
            category="lead_response",
            auto_eligible=False,
            evidence={
                "total_calls": total_calls,
                "missed_calls": missed_calls,
                "missed_rate": round(missed_rate, 1),
                "missed_by_hour_of_day": missed_by_hour,
                "estimated_revenue_lost": round(estimated_revenue_lost, 2),
                "avg_deal_value": avg_deal_value,
                "conversion_rate": conversion_rate,
            },
            proposed_action={
                "action_type": "kaicalls_setup",
                "description": (
                    "KaiCalls AI receptionist (kaicalls.com) answers every call "
                    "instantly, captures caller info, and texts you the lead "
                    "details. Never miss a call again. Estimated monthly "
                    f"revenue recovery: ${estimated_revenue_lost:,.2f}."
                ),
                "auto_eligible": False,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.DAILY.value,
            schedule_time="09:00",
            archetype_relevance=list(self.archetype_relevance),
            max_findings_per_run=10,
            suppression_window_days=7,
            cooldown_after_action_days=30,
        )


# ============================================================================
# FollowUpGapWatcher
# ============================================================================


class FollowUpGapWatcher(Watcher):
    """Monitors leads and customers that have not received timely follow-up.

    Runs daily at 08:00 UTC.  Covers four follow-up categories: new leads,
    sent quotes, post-service contact, and overdue invoices.  Each has a
    configurable threshold for how many days is "too long."
    """

    name = "followup_gaps"
    description = (
        "Monitors leads and customers that haven't received timely follow-up"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance = ["local_service", "multi_location", "professional_services"]

    FOLLOWUP_THRESHOLDS = {
        "new_lead_max_days": 3,
        "quote_followup_max_days": 5,
        "post_service_max_days": 7,
        "invoice_followup_max_days": 14,
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check each follow-up gap category.

        Parameters
        ----------
        business_profile:
            Business profile with ``id``.
        workspace_state:
            Workspace state with lead, quote, job, and invoice data from
            CRM/service management connector.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)

        # New lead follow-up
        leads_data = _get_field(workspace_state, "lead_followup_data", {})
        if leads_data:
            finding = self._check_new_lead_followup(
                leads_data.get("without_followup", 0),
                leads_data.get("total_new", 0),
                leads_data.get("oldest_unfollowed_days", 0),
                leads_data.get("unfollowed_sources", []),
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        # Quote follow-up
        quotes_data = _get_field(workspace_state, "quote_followup_data", {})
        if quotes_data:
            finding = self._check_quote_followup(
                quotes_data.get("without_followup", 0),
                quotes_data.get("total_sent", 0),
                quotes_data.get("oldest_unfollowed_days", 0),
                quotes_data.get("total_value", 0),
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        # Post-service follow-up
        jobs_data = _get_field(workspace_state, "completed_jobs_data", {})
        if jobs_data:
            finding = self._check_post_service_contact(
                jobs_data.get("no_contact", 0),
                jobs_data.get("total_completed", 0),
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        # Invoice follow-up
        invoice_data = _get_field(workspace_state, "overdue_invoice_data", {})
        if invoice_data:
            finding = self._check_invoice_followup(
                invoice_data.get("overdue_count", 0),
                invoice_data.get("total_overdue_value", 0),
                invoice_data.get("oldest_overdue_days", 0),
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_new_lead_followup(
        self,
        leads_without_followup: int,
        total_new_leads: int,
        oldest_unfollowed_days: int,
        unfollowed_lead_sources: List[str],
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag new leads that have not received follow-up within threshold.

        In production the lead data comes from the CRM connector.  A "lead
        without follow-up" is one where no outbound contact (call, email,
        text) has been recorded after the initial inquiry.
        """
        if leads_without_followup == 0:
            return None

        if oldest_unfollowed_days > 7:
            severity = "critical"
            urgency = FindingUrgency.IMMEDIATE.value
        elif oldest_unfollowed_days > self.FOLLOWUP_THRESHOLDS["new_lead_max_days"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        else:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{leads_without_followup} new leads without follow-up "
                f"(oldest: {oldest_unfollowed_days} days)"
            ),
            description=(
                f"{leads_without_followup} out of {total_new_leads} new leads "
                f"have not received any follow-up. The oldest unfollowed lead "
                f"is {oldest_unfollowed_days} days old. Every day without "
                "contact dramatically reduces conversion probability."
            ),
            suppression_key=f"lead_followup_{business_id}",
            urgency=urgency,
            severity=severity,
            category="lead_response",
            auto_eligible=True,
            evidence={
                "leads_without_followup": leads_without_followup,
                "total_new_leads": total_new_leads,
                "oldest_unfollowed_days": oldest_unfollowed_days,
                "unfollowed_lead_sources": unfollowed_lead_sources,
            },
            proposed_action={
                "action_type": "follow_up_outreach",
                "description": (
                    "Send immediate follow-up to all unfollowed leads. "
                    "Set up an automated follow-up sequence to prevent "
                    "future gaps."
                ),
                "auto_eligible": True,
            },
        )

    def _check_quote_followup(
        self,
        quotes_without_followup: int,
        total_quotes_sent: int,
        oldest_unfollowed_days: int,
        total_quote_value: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag sent quotes that have not received follow-up.

        In production the quote data comes from the CRM or invoicing
        connector.  A quote without follow-up is one where no check-in
        call, email, or text was sent after the quote was delivered.
        """
        if quotes_without_followup == 0:
            return None
        if oldest_unfollowed_days < self.FOLLOWUP_THRESHOLDS["quote_followup_max_days"]:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=f"{quotes_without_followup} sent quotes without follow-up",
            description=(
                f"{quotes_without_followup} of {total_quotes_sent} quotes "
                f"sent have not been followed up on (total value: "
                f"${total_quote_value:,.2f}). The oldest has been waiting "
                f"{oldest_unfollowed_days} days. A simple follow-up call or "
                "email can recover a significant portion of these."
            ),
            suppression_key=f"quote_followup_{business_id}",
            urgency=FindingUrgency.SOON.value,
            severity="high",
            category="lead_response",
            evidence={
                "quotes_without_followup": quotes_without_followup,
                "total_quotes_sent": total_quotes_sent,
                "oldest_unfollowed_days": oldest_unfollowed_days,
                "total_quote_value": total_quote_value,
            },
            proposed_action={
                "action_type": "quote_followup_sequence",
                "description": (
                    "Send a follow-up email or call prompt for each open quote. "
                    "Template: 'Just checking in on the quote we sent for [service]. "
                    "Happy to answer any questions.'"
                ),
                "auto_eligible": True,
            },
        )

    def _check_post_service_contact(
        self,
        completed_jobs_no_contact: int,
        total_completed: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag completed jobs without post-service follow-up.

        Post-service follow-up is the single best opportunity to generate
        reviews.  In production this data comes from the service management
        connector.
        """
        if completed_jobs_no_contact == 0:
            return None

        estimated_review_opportunity = int(completed_jobs_no_contact * 0.30)

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{completed_jobs_no_contact} completed jobs without "
                "post-service follow-up"
            ),
            description=(
                f"{completed_jobs_no_contact} of {total_completed} completed "
                "jobs have not received a post-service thank-you or review "
                f"request. Estimated review opportunity: "
                f"~{estimated_review_opportunity} new reviews. Sending a "
                "thank-you message with a review link is the highest-ROI "
                "action for building online reputation."
            ),
            suppression_key=f"post_service_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="medium",
            category="lead_response",
            auto_eligible=True,
            evidence={
                "completed_jobs_no_contact": completed_jobs_no_contact,
                "total_completed": total_completed,
                "estimated_review_opportunity": estimated_review_opportunity,
            },
            proposed_action={
                "action_type": "thank_you_review_request",
                "description": (
                    "Send a thank-you message to each customer followed by a "
                    "review request 24 hours later. Include a direct link to "
                    "the Google review page."
                ),
                "auto_eligible": True,
            },
        )

    def _check_invoice_followup(
        self,
        overdue_invoices: int,
        total_overdue_value: float,
        oldest_overdue_days: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag overdue invoices without follow-up.

        In production this data comes from the invoicing/accounting
        connector.  Overdue means past the payment due date with no
        recorded follow-up communication.
        """
        if overdue_invoices == 0:
            return None
        if oldest_overdue_days < self.FOLLOWUP_THRESHOLDS["invoice_followup_max_days"]:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{overdue_invoices} overdue invoices "
                f"(${total_overdue_value:,.2f}) without follow-up"
            ),
            description=(
                f"{overdue_invoices} invoices totaling ${total_overdue_value:,.2f} "
                f"are overdue (oldest: {oldest_overdue_days} days). A polite "
                "payment reminder sequence can recover a large portion of "
                "outstanding balances."
            ),
            suppression_key=f"invoice_followup_{business_id}",
            urgency=FindingUrgency.SOON.value,
            severity="high",
            category="lead_response",
            evidence={
                "overdue_invoices": overdue_invoices,
                "total_overdue_value": total_overdue_value,
                "oldest_overdue_days": oldest_overdue_days,
            },
            proposed_action={
                "action_type": "payment_reminder",
                "description": (
                    "Send a payment reminder sequence: friendly reminder -> "
                    "follow-up call -> formal notice. Tone should be polite "
                    "and professional."
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
            archetype_relevance=list(self.archetype_relevance),
            max_findings_per_run=10,
            suppression_window_days=3,
        )


# ============================================================================
# ReviewVelocityWatcher
# ============================================================================


class ReviewVelocityWatcher(Watcher):
    """Monitors review generation rate, rating trends, and unresponded reviews.

    Runs weekly.  Relevant for ``local_service`` and ``multi_location``
    archetypes where reviews directly affect local search rankings and
    conversion rates.
    """

    name = "review_velocity"
    description = (
        "Monitors review generation rate, rating trends, and unresponded reviews"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance = ["local_service", "multi_location"]

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check review count vs target, rating trend, unresponded reviews, negative patterns.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``monthly_review_target``.
        workspace_state:
            Workspace state with review metrics from GBP/review connectors.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        review_data = _get_field(workspace_state, "review_data", {})

        # Review rate vs target
        reviews_this_month = review_data.get("reviews_this_month")
        monthly_target = _get_field(business_profile, "monthly_review_target")
        if reviews_this_month is not None and monthly_target is not None:
            finding = self._check_review_rate(
                reviews_this_month, monthly_target, business_id
            )
            if finding is not None:
                findings.append(finding)

        # Rating trend
        current_avg = review_data.get("current_avg_rating")
        previous_avg = review_data.get("previous_avg_rating")
        period_days = review_data.get("period_days", 30)
        if current_avg is not None and previous_avg is not None:
            finding = self._check_rating_trend(
                current_avg, previous_avg, period_days, business_id
            )
            if finding is not None:
                findings.append(finding)

        # Unresponded reviews
        unresponded = review_data.get("unresponded_count")
        oldest_unresponded_days = review_data.get("oldest_unresponded_days")
        if unresponded is not None and unresponded > 0:
            finding = self._check_unresponded_reviews(
                unresponded,
                oldest_unresponded_days or 0,
                business_id,
            )
            if finding is not None:
                findings.append(finding)

        # Negative patterns
        negative_reviews = review_data.get("negative_reviews", [])
        total_reviews = review_data.get("total_reviews", 0)
        if negative_reviews:
            finding = self._check_negative_patterns(
                negative_reviews, total_reviews, business_id
            )
            if finding is not None:
                findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_review_rate(
        self,
        reviews_this_month: int,
        monthly_target: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag when review generation is below target.

        In production the review count comes from the GBP connector or
        aggregated review platform data.
        """
        if monthly_target <= 0 or reviews_this_month >= monthly_target:
            return None

        ratio = reviews_this_month / monthly_target
        if ratio < 0.50:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif ratio < 0.75:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Review generation below target: {reviews_this_month} "
                f"of {monthly_target} target"
            ),
            description=(
                f"Only {reviews_this_month} reviews received this month against "
                f"a target of {monthly_target} ({ratio * 100:.0f}% of target). "
                "Activate the review request sequence and remind staff to ask "
                "happy customers for reviews."
            ),
            suppression_key=f"review_rate_{business_id}",
            urgency=urgency,
            severity=severity,
            category="reviews",
            evidence={
                "reviews_this_month": reviews_this_month,
                "monthly_target": monthly_target,
                "achievement_pct": round(ratio * 100, 1),
            },
            proposed_action={
                "action_type": "review_request_campaign",
                "description": (
                    "Activate the review request sequence. Send review "
                    "request emails/texts to recent customers. Remind "
                    "frontline staff to ask for reviews after service."
                ),
                "auto_eligible": True,
            },
        )

    def _check_rating_trend(
        self,
        current_avg: float,
        previous_avg: float,
        period_days: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag declining review ratings.

        A declining average rating is an early warning of service quality
        issues or a targeted negative review campaign.
        """
        change = current_avg - previous_avg

        if change >= 0:
            return None

        drop = abs(change)
        if drop > 0.2:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif drop > 0.0:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Review rating declining: {previous_avg:.1f} -> "
                f"{current_avg:.1f} over {period_days} days"
            ),
            description=(
                f"The average review rating dropped from {previous_avg:.1f} to "
                f"{current_avg:.1f} over the past {period_days} days (change: "
                f"{change:+.2f}). Investigate recent negative reviews for "
                "recurring themes."
            ),
            suppression_key=f"rating_trend_{business_id}",
            urgency=urgency,
            severity=severity,
            category="reviews",
            evidence={
                "current_avg": current_avg,
                "previous_avg": previous_avg,
                "change": round(change, 2),
                "period_days": period_days,
            },
        )

    def _check_unresponded_reviews(
        self,
        unresponded_count: int,
        oldest_unresponded_days: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Flag reviews awaiting response for more than 48 hours.

        Responding to reviews (positive and negative) is a ranking signal
        for Google's local algorithm and shows customers the business cares.
        """
        if oldest_unresponded_days < 2:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{unresponded_count} reviews awaiting response "
                f"(oldest: {oldest_unresponded_days} days)"
            ),
            description=(
                f"{unresponded_count} reviews have not been responded to. "
                f"The oldest unresponded review is {oldest_unresponded_days} "
                "days old. Responding to reviews improves local search "
                "rankings and demonstrates customer care."
            ),
            suppression_key=f"unresponded_reviews_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="medium",
            category="reviews",
            auto_eligible=True,
            evidence={
                "unresponded_count": unresponded_count,
                "oldest_unresponded_days": oldest_unresponded_days,
            },
            proposed_action={
                "action_type": "draft_review_responses",
                "description": (
                    "Generate response drafts for all unresponded reviews. "
                    "Positive reviews get a personalized thank-you. Negative "
                    "reviews get an empathetic, solution-oriented response."
                ),
                "auto_eligible": True,
            },
        )

    def _check_negative_patterns(
        self,
        negative_reviews: List[Dict[str, Any]],
        total_reviews: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Analyze negative reviews for common complaint themes.

        In production this would use NLP or keyword extraction to cluster
        negative review text into themes.  For the stub, it groups by a
        ``complaint_theme`` field if present in each review dict.
        """
        if not negative_reviews:
            return None

        # Cluster complaints by theme
        complaint_themes: Dict[str, int] = {}
        example_reviews: List[str] = []

        for review in negative_reviews:
            theme = review.get("complaint_theme", "general")
            complaint_themes[theme] = complaint_themes.get(theme, 0) + 1
            if len(example_reviews) < 3:
                snippet = review.get("text", "")[:100]
                if snippet:
                    example_reviews.append(snippet)

        if not complaint_themes:
            return None

        top_complaint = max(complaint_themes, key=complaint_themes.get)  # type: ignore[arg-type]
        top_count = complaint_themes[top_complaint]

        # Only flag if a pattern emerges (2+ reviews with same theme)
        if top_count < 2:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"Recurring complaint detected in negative reviews: "
                f"{top_complaint}"
            ),
            description=(
                f"'{top_complaint}' has been mentioned in {top_count} of "
                f"{len(negative_reviews)} negative reviews (out of "
                f"{total_reviews} total). This pattern suggests a systemic "
                "issue worth addressing at the operational level."
            ),
            suppression_key=f"negative_pattern_{business_id}_{top_complaint}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="medium",
            category="reviews",
            evidence={
                "complaint_themes": complaint_themes,
                "total_negative": len(negative_reviews),
                "total_reviews": total_reviews,
                "example_reviews": example_reviews,
            },
            proposed_action={
                "action_type": "address_complaint",
                "description": (
                    f"Address the root cause of '{top_complaint}' complaints. "
                    "Prepare a response template for this specific complaint "
                    "type to ensure consistent, professional responses."
                ),
                "auto_eligible": False,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="monday_08:00",
            archetype_relevance=list(self.archetype_relevance),
            max_findings_per_run=10,
            suppression_window_days=7,
        )


# ============================================================================
# DormantCustomerWatcher
# ============================================================================


class DormantCustomerWatcher(Watcher):
    """Identifies customers who have not engaged or purchased in extended periods.

    Runs weekly on Wednesdays at 09:00 UTC.  Segments customers into three
    dormancy tiers (at-risk, dormant, churned) with decreasing reactivation
    success rates and progressively stronger offers.
    """

    name = "dormant_customers"
    description = (
        "Identifies customers who haven't engaged or purchased "
        "in extended periods"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance = ["local_service", "ecommerce", "multi_location"]

    DORMANCY_TIERS = {
        "at_risk": {
            "days": 90,
            "reactivation_rate": 0.30,
            "message_theme": "We haven't seen you in a while",
            "offer_level": "gentle reminder + small incentive",
        },
        "dormant": {
            "days": 180,
            "reactivation_rate": 0.15,
            "message_theme": "We miss you",
            "offer_level": "significant incentive (e.g., 15-20% off)",
        },
        "churned": {
            "days": 365,
            "reactivation_rate": 0.05,
            "message_theme": "Win-back campaign",
            "offer_level": "strong offer (e.g., 25-30% off or free service)",
        },
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check customer activity tiers.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``average_customer_value``.
        workspace_state:
            Workspace state with ``customer_dormancy_data`` containing
            per-tier counts and total customer count.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        dormancy_data = _get_field(workspace_state, "customer_dormancy_data", {})
        total_customers = dormancy_data.get("total_customers", 0)
        avg_value = _get_field(business_profile, "average_customer_value", 500.0)

        for tier_name, tier_config in self.DORMANCY_TIERS.items():
            tier_data = dormancy_data.get(tier_name, {})
            customer_count = tier_data.get("count", 0)

            if customer_count > 0 and total_customers > 0:
                finding = self._check_dormancy_tier(
                    tier_name,
                    customer_count,
                    total_customers,
                    avg_value,
                    tier_config,
                    business_id,
                )
                if finding is not None:
                    findings.append(finding)

        return findings

    def _check_dormancy_tier(
        self,
        tier_name: str,
        customer_count: int,
        total_customers: int,
        avg_value: float,
        tier_config: Dict[str, Any],
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Generate a finding for a specific dormancy tier.

        Calculates estimated reactivation value using the tier-specific
        reactivation rate multiplied by customer count and average value.
        """
        pct_of_base = (customer_count / total_customers) * 100
        reactivation_rate = tier_config["reactivation_rate"]
        estimated_reactivation_value = customer_count * avg_value * reactivation_rate
        message_theme = tier_config["message_theme"]
        offer_level = tier_config["offer_level"]
        days_threshold = tier_config["days"]

        # Severity escalates with tier
        severity_map = {
            "at_risk": "medium",
            "dormant": "high",
            "churned": "low",  # Lower severity because ROI is lower
        }
        severity = severity_map.get(tier_name, "medium")

        # Only at_risk is safe for auto-send (gentle nudge)
        auto_eligible = tier_name == "at_risk"

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{customer_count} customers are {tier_name} "
                f"({pct_of_base:.0f}% of customer base)"
            ),
            description=(
                f"{customer_count} customers have not engaged in {days_threshold}+ "
                f"days ({pct_of_base:.0f}% of the {total_customers} total "
                f"customer base). Estimated reactivation value: "
                f"${estimated_reactivation_value:,.2f} (at "
                f"{reactivation_rate * 100:.0f}% reactivation rate). "
                f"Recommended approach: '{message_theme}' with {offer_level}."
            ),
            suppression_key=f"dormant_{tier_name}_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity=severity,
            category="customer_retention",
            auto_eligible=auto_eligible,
            evidence={
                "tier_name": tier_name,
                "customer_count": customer_count,
                "total_customers": total_customers,
                "pct_of_base": round(pct_of_base, 1),
                "estimated_reactivation_value": round(
                    estimated_reactivation_value, 2
                ),
                "reactivation_rate": reactivation_rate,
                "days_threshold": days_threshold,
            },
            proposed_action={
                "action_type": "reactivation_campaign",
                "description": (
                    f"Launch a '{message_theme}' reactivation sequence with "
                    f"{offer_level}. Target the {customer_count} {tier_name} "
                    "customers with personalized outreach."
                ),
                "auto_eligible": auto_eligible,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="wednesday_09:00",
            archetype_relevance=list(self.archetype_relevance),
            max_findings_per_run=5,
            suppression_window_days=30,
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

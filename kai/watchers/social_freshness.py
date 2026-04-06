"""Social staleness, content freshness, and engagement decline watchers.

Task 069 — Monitors the "freshness" of a business's content across all
channels and flags when something needs a refresh.  Particularly valuable
for local service businesses that often let their social and content
presence go dormant between busy seasons.

Watchers
--------
- **SocialStalenessWatcher** (daily) — days since last post per platform.
- **ContentFreshnessWatcher** (weekly) — stale pages, old testimonials.
- **EngagementDeclineWatcher** (weekly) — engagement/follower/reach trends.
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
# SocialStalenessWatcher
# ============================================================================


class SocialStalenessWatcher(Watcher):
    """Monitors days since last post on each social platform and flags dormant accounts.

    Runs daily.  Relevant for all archetypes — any business with active
    social accounts needs to post consistently or the algorithm penalises
    them and customers assume the business is closed.
    """

    name = "social_staleness"
    description = (
        "Monitors days since last post on each social platform "
        "and flags dormant accounts"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance: List[str] = []  # All archetypes

    # Days-since-last-post -> severity mapping
    STALENESS_THRESHOLDS = {
        "info": 7,
        "warning": 14,
        "critical": 30,
    }

    # Recommended posting cadence per platform
    PLATFORM_EXPECTATIONS: Dict[str, str] = {
        "facebook": "every 3-5 days",
        "instagram": "every 2-3 days",
        "linkedin": "every 3-5 days",
        "tiktok": "every 1-2 days",
        "x_twitter": "daily",
        "youtube": "weekly",
        "google_business": "weekly",
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """For each active social platform, check days since last post.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``social_accounts`` dict
            mapping platform name to account metadata.
        workspace_state:
            Workspace state with recent post timestamps per platform.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        social_accounts = _get_field(business_profile, "social_accounts", {})
        post_dates = _get_field(workspace_state, "last_post_dates", {})

        for platform in social_accounts:
            last_post_date = post_dates.get(platform)
            finding = self._check_platform_staleness(
                platform, last_post_date, business_profile
            )
            if finding is not None:
                findings.append(finding)

        return findings

    def _check_platform_staleness(
        self,
        platform: str,
        last_post_date: Optional[str],
        business_profile: Any,
    ) -> Optional[WatcherFinding]:
        """Compare last_post_date to current date and evaluate staleness.

        In production the last post date would come from the platform's
        connector (e.g., Meta Graph API, LinkedIn API, TikTok API) or from
        workspace state populated by a previous sync.
        """
        business_id = _get_business_id(business_profile)
        recommended = self.PLATFORM_EXPECTATIONS.get(platform, "regularly")

        if last_post_date is None:
            # Unknown last post — treat as potentially stale
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=f"{platform} has no recorded post history",
                description=(
                    f"No post date found for {platform}. Either the account "
                    "is new, inactive, or the connector has not synced yet. "
                    f"Recommended posting frequency: {recommended}."
                ),
                suppression_key=f"social_stale_{platform}_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="low",
                category="social_freshness",
                evidence={
                    "platform": platform,
                    "last_post_date": None,
                    "days_dormant": None,
                    "recommended_frequency": recommended,
                },
            )

        try:
            last_dt = datetime.fromisoformat(last_post_date)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None

        now = datetime.now(timezone.utc)
        days_dormant = (now - last_dt).days

        if days_dormant >= self.STALENESS_THRESHOLDS["critical"]:
            severity = "critical"
            urgency = FindingUrgency.SOON.value
        elif days_dormant >= self.STALENESS_THRESHOLDS["warning"]:
            severity = "warning"
            urgency = FindingUrgency.SCHEDULED.value
        elif days_dormant >= self.STALENESS_THRESHOLDS["info"]:
            severity = "low"
            urgency = FindingUrgency.INFORMATIONAL.value
        else:
            return None  # Active enough

        # Build proposed action for critical staleness
        proposed_action = None
        auto_eligible = False
        if severity == "critical":
            content_suggestions = self._suggest_proof_of_life_content(
                platform, business_profile
            )
            proposed_action = {
                "action_type": "social_post",
                "description": (
                    f"Publish a proof-of-life post on {platform} to maintain presence"
                ),
                "auto_eligible": True,
                "suggestions": content_suggestions,
            }
            auto_eligible = True

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=f"{platform} account dormant for {days_dormant} days",
            description=(
                f"No posts on {platform} since {last_post_date}. "
                f"Recommended frequency: {recommended}. "
                "Dormant social accounts signal to customers and algorithms "
                "that the business is inactive."
            ),
            suppression_key=f"social_stale_{platform}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="social_freshness",
            auto_eligible=auto_eligible,
            evidence={
                "platform": platform,
                "last_post_date": last_post_date,
                "days_dormant": days_dormant,
                "recommended_frequency": recommended,
            },
            proposed_action=proposed_action,
        )

    def _suggest_proof_of_life_content(
        self,
        platform: str,
        business_profile: Any,
    ) -> Dict[str, Any]:
        """Return proof-of-life content ideas tailored to the platform.

        Picks a content type based on what typically performs best on each
        platform.  These are concrete suggestions the operator or auto-poster
        can act on immediately.
        """
        business_name = _get_field(business_profile, "name", "the business")
        service = _get_field(business_profile, "primary_service", "services")

        ideas: Dict[str, List[str]] = {
            "facebook": [
                f"Behind-the-scenes photo of the {business_name} team at work",
                f"Highlight a recent 5-star customer review about {service}",
                f"Seasonal tip: how to maintain/prepare for {service} this season",
                f"Team spotlight: introduce a team member and their role at {business_name}",
            ],
            "instagram": [
                f"Before/after photo from a recent {service} project",
                f"Carousel: 3 tips for choosing the right {service} provider",
                f"Reel: 30-second day-in-the-life at {business_name}",
                f"Story poll: ask followers about their biggest {service} challenge",
            ],
            "linkedin": [
                f"Industry insight: recent trend affecting {service}",
                f"Case study snippet from a recent {business_name} client win",
                f"Team achievement or certification update",
                f"Lesson learned from a recent project",
            ],
            "tiktok": [
                f"Quick tip: common {service} mistake and how to avoid it",
                f"Satisfying transformation/completion video from recent work",
                f"Day-in-the-life format showing real {business_name} work",
                f"Respond to a common customer question about {service}",
            ],
            "x_twitter": [
                f"Quick {service} tip in 280 characters",
                f"Share a customer win or positive review",
                f"Respond to a trending topic related to {service}",
                f"Ask a question to engage the audience about {service}",
            ],
            "youtube": [
                f"How-to video: common {service} question answered",
                f"Project walkthrough: start to finish on a recent job",
                f"FAQ compilation: top 5 questions about {service}",
                f"Meet the team behind {business_name}",
            ],
            "google_business": [
                f"GBP post: current season special offer for {service}",
                f"GBP update: recent project completed by {business_name}",
                f"GBP post: highlight a recent 5-star review",
                f"GBP event: upcoming availability or promotion",
            ],
        }

        return {
            "platform": platform,
            "suggested_content_types": ideas.get(platform, ideas["facebook"]),
            "recommended_next_step": (
                f"Pick one idea and draft the post. For {platform}, prioritize "
                f"{ideas.get(platform, ideas['facebook'])[0].lower()}."
            ),
        }

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.DAILY.value,
            schedule_time="07:00",
            archetype_relevance=[],
            max_findings_per_run=10,
            suppression_window_days=7,
        )


# ============================================================================
# ContentFreshnessWatcher
# ============================================================================


class ContentFreshnessWatcher(Watcher):
    """Monitors content age across website and flags stale pages, outdated testimonials, and unchanged copy.

    Runs weekly.  Relevant for all archetypes.  Different content types have
    different freshness expectations:

    - Blog posts: 12 months without update
    - Landing pages: 6 months without copy change
    - Testimonials: 24 months old
    - Team page: change in staff not reflected
    - Pricing/offers: 3 months without verification
    """

    name = "content_freshness"
    description = (
        "Monitors content age across website and flags stale pages, "
        "outdated testimonials, and unchanged copy"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance: List[str] = []  # All archetypes

    FRESHNESS_THRESHOLDS = {
        "blog_posts": 12,         # months
        "landing_pages": 6,       # months
        "testimonials": 24,       # months
        "team_page": 0,           # any known change triggers flag
        "pricing_offers": 3,      # months
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check each content category against freshness thresholds.

        Parameters
        ----------
        business_profile:
            Business profile with site and content metadata.
        workspace_state:
            Workspace state with content inventory and timestamps.
        """
        findings: List[WatcherFinding] = []

        findings.extend(self._check_blog_freshness(workspace_state))

        findings.extend(self._check_landing_page_freshness(workspace_state))

        finding = self._check_testimonial_freshness(business_profile)
        if finding is not None:
            findings.append(finding)

        finding = self._check_team_page_accuracy(business_profile)
        if finding is not None:
            findings.append(finding)

        finding = self._check_pricing_accuracy(business_profile, workspace_state)
        if finding is not None:
            findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_blog_freshness(
        self,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Scan blog post dates from CMS or sitemap and flag stale posts.

        In production this would parse the sitemap or query the CMS API to
        get each blog post's ``published_date`` and ``last_modified_date``,
        then compare against the 12-month threshold.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_field(workspace_state, "business_id", "unknown")
        threshold_months = self.FRESHNESS_THRESHOLDS["blog_posts"]

        # --- Stub: retrieve blog post inventory from CMS/sitemap ---
        # posts: List[Dict] = [{"url": ..., "title": ..., "published": ..., "modified": ...}]
        posts: List[Dict[str, Any]] = []

        for post in posts:
            post_url = post.get("url", "")
            post_title = post.get("title", "Untitled")
            last_modified = post.get("last_modified_date") or post.get("published_date")
            months_since_update = post.get("months_since_update", 0)

            if months_since_update >= threshold_months:
                findings.append(
                    create_watcher_finding(
                        watcher_name=self.name,
                        business_id=business_id,
                        title=(
                            f"Blog post '{post_title}' hasn't been updated "
                            f"in {months_since_update} months"
                        ),
                        description=(
                            f"The blog post at {post_url} was last modified "
                            f"{months_since_update} months ago. Stale content "
                            "hurts SEO rankings and visitor trust. Refresh with "
                            "updated statistics, new examples, and a revised intro."
                        ),
                        suppression_key=f"blog_stale_{business_id}_{_slug(post_url)}",
                        urgency=FindingUrgency.SCHEDULED.value,
                        severity="low",
                        category="content_freshness",
                        evidence={
                            "post_url": post_url,
                            "published_date": post.get("published_date"),
                            "last_modified_date": last_modified,
                            "months_since_update": months_since_update,
                        },
                        proposed_action={
                            "action_type": "content_refresh",
                            "description": (
                                "Update statistics, add new examples, refresh "
                                "the intro paragraph, and update the published date."
                            ),
                            "auto_eligible": True,
                        },
                    )
                )
        return findings

    def _check_landing_page_freshness(
        self,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Check landing page last-modified dates.

        In production this would compare cached page hashes or CMS
        modification timestamps to detect unchanged copy.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_field(workspace_state, "business_id", "unknown")
        threshold_months = self.FRESHNESS_THRESHOLDS["landing_pages"]

        # --- Stub: retrieve landing page modification data ---
        pages: List[Dict[str, Any]] = []

        for page in pages:
            page_url = page.get("url", "")
            months_unchanged = page.get("months_unchanged", 0)

            if months_unchanged >= threshold_months:
                findings.append(
                    create_watcher_finding(
                        watcher_name=self.name,
                        business_id=business_id,
                        title=(
                            f"Landing page unchanged for {months_unchanged} months"
                        ),
                        description=(
                            f"The landing page at {page_url} has not had a copy "
                            f"change in {months_unchanged} months. Fresh copy and "
                            "updated CTAs can improve conversion rates."
                        ),
                        suppression_key=f"landing_stale_{business_id}_{_slug(page_url)}",
                        urgency=FindingUrgency.SCHEDULED.value,
                        severity="low",
                        category="content_freshness",
                        evidence={
                            "page_url": page_url,
                            "last_modified": page.get("last_modified"),
                            "months_unchanged": months_unchanged,
                        },
                        proposed_action={
                            "action_type": "copy_refresh",
                            "description": (
                                "Refresh headline and CTA copy. Consider an A/B "
                                "test with a new headline variant."
                            ),
                            "auto_eligible": True,
                        },
                    )
                )
        return findings

    def _check_testimonial_freshness(
        self,
        business_profile: Any,
    ) -> Optional[WatcherFinding]:
        """Check whether displayed testimonials/reviews are outdated.

        In production this would extract testimonial dates from the website
        or CMS and compare against the 24-month threshold.
        """
        business_id = _get_business_id(business_profile)
        threshold_months = self.FRESHNESS_THRESHOLDS["testimonials"]

        # --- Stub: retrieve testimonial dates ---
        oldest_testimonial_date: Optional[str] = None
        average_testimonial_age_months: Optional[float] = None
        total_testimonials: int = 0

        if (
            average_testimonial_age_months is not None
            and average_testimonial_age_months >= threshold_months
        ):
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=(
                    f"Displayed testimonials average {average_testimonial_age_months:.0f} "
                    "months old"
                ),
                description=(
                    f"The {total_testimonials} testimonials on the website are "
                    f"on average {average_testimonial_age_months:.0f} months old. "
                    "Fresh social proof increases conversion rates. Launch a "
                    "review request campaign to generate recent testimonials."
                ),
                suppression_key=f"testimonials_stale_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="low",
                category="content_freshness",
                evidence={
                    "oldest_testimonial_date": oldest_testimonial_date,
                    "average_testimonial_age_months": average_testimonial_age_months,
                    "total_testimonials": total_testimonials,
                },
                proposed_action={
                    "action_type": "review_request_campaign",
                    "description": (
                        "Launch a review request campaign targeting recent "
                        "customers to generate fresh testimonials."
                    ),
                    "auto_eligible": True,
                },
            )
        return None

    def _check_team_page_accuracy(
        self,
        business_profile: Any,
    ) -> Optional[WatcherFinding]:
        """Compare team page content against known employee data.

        In production this would scrape the team/about page and compare
        listed names against an internal employee roster or CRM contact
        list to detect departed employees still listed or new hires not
        yet added.
        """
        business_id = _get_business_id(business_profile)

        # --- Stub: compare team page content with employee data ---
        team_page_url: Optional[str] = None
        potential_issues: List[str] = []

        if potential_issues:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Team page may be outdated",
                description=(
                    f"Potential issues detected with the team page at "
                    f"{team_page_url}: {'; '.join(potential_issues)}. "
                    "An outdated team page erodes trust."
                ),
                suppression_key=f"team_page_stale_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="low",
                category="content_freshness",
                evidence={
                    "team_page_url": team_page_url,
                    "potential_issues": potential_issues,
                },
                proposed_action={
                    "action_type": "update_team_page",
                    "description": "Review and update the team page with current staff.",
                    "auto_eligible": False,
                },
            )
        return None

    def _check_pricing_accuracy(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> Optional[WatcherFinding]:
        """Check when pricing information was last verified.

        In production this would check the workspace state for the last
        date pricing was confirmed by the business owner and flag when
        that date exceeds the 3-month threshold.
        """
        business_id = _get_business_id(business_profile)
        threshold_months = self.FRESHNESS_THRESHOLDS["pricing_offers"]

        # --- Stub: check pricing verification date ---
        last_verified_date: Optional[str] = None
        months_since_verification: Optional[int] = None
        pricing_pages: List[str] = []

        if (
            months_since_verification is not None
            and months_since_verification >= threshold_months
        ):
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=(
                    f"Pricing not verified in {months_since_verification} months"
                ),
                description=(
                    "Pricing information was last verified on "
                    f"{last_verified_date}. Outdated pricing causes customer "
                    "frustration and can lead to disputes."
                ),
                suppression_key=f"pricing_stale_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="medium",
                category="content_freshness",
                evidence={
                    "last_verified_date": last_verified_date,
                    "months_since_verification": months_since_verification,
                    "pricing_pages": pricing_pages,
                },
                proposed_action={
                    "action_type": "verify_pricing",
                    "description": (
                        "Contact the business owner to verify current pricing "
                        "and update any changed rates on the website."
                    ),
                    "auto_eligible": False,
                },
            )
        return None

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="wednesday_06:00",
            archetype_relevance=[],
            max_findings_per_run=15,
            suppression_window_days=14,
        )


# ============================================================================
# EngagementDeclineWatcher
# ============================================================================


class EngagementDeclineWatcher(Watcher):
    """Monitors engagement rate trends across social platforms and flags declining performance.

    Runs weekly.  Relevant for all archetypes.  Tracks engagement rate,
    follower growth, and reach changes over rolling 30-day windows.
    """

    name = "engagement_decline"
    description = (
        "Monitors engagement rate trends across social platforms "
        "and flags declining performance"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance: List[str] = []  # All archetypes

    DECLINE_THRESHOLDS = {
        "warning": 0.20,   # 20% decline in engagement rate over 30 days
        "critical": 0.40,  # 40% decline
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """For each active social platform, check engagement metrics.

        Parameters
        ----------
        business_profile:
            Business profile with ``social_accounts``.
        workspace_state:
            Workspace state with engagement metrics per platform, including
            ``engagement_rates``, ``follower_counts``, and ``reach_data``.
        """
        findings: List[WatcherFinding] = []
        business_id = _get_business_id(business_profile)
        social_accounts = _get_field(business_profile, "social_accounts", {})
        engagement_data = _get_field(workspace_state, "engagement_rates", {})
        follower_data = _get_field(workspace_state, "follower_counts", {})
        reach_data = _get_field(workspace_state, "reach_data", {})

        for platform in social_accounts:
            # Engagement rate check
            eng = engagement_data.get(platform, {})
            if eng.get("current") is not None and eng.get("previous") is not None:
                finding = self._check_engagement_rate(
                    platform, eng["current"], eng["previous"], business_id
                )
                if finding is not None:
                    findings.append(finding)

            # Follower growth check
            fol = follower_data.get(platform, {})
            if fol.get("current") is not None and fol.get("previous") is not None:
                finding = self._check_follower_growth(
                    platform,
                    fol["current"],
                    fol["previous"],
                    fol.get("days", 30),
                    business_id,
                )
                if finding is not None:
                    findings.append(finding)

            # Reach check
            rch = reach_data.get(platform, {})
            if rch.get("current") is not None and rch.get("previous") is not None:
                finding = self._check_reach_decline(
                    platform, rch["current"], rch["previous"], business_id
                )
                if finding is not None:
                    findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_engagement_rate(
        self,
        platform: str,
        current_rate: float,
        previous_rate: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate percent change in engagement rate and flag declines.

        Engagement rate is typically (likes + comments + shares) / followers
        or (likes + comments + shares) / impressions depending on the
        platform.  The data would come from the platform's analytics API.
        """
        if previous_rate <= 0:
            return None

        pct_change = (current_rate - previous_rate) / previous_rate

        if pct_change >= 0:
            return None  # Not declining

        decline_pct = abs(pct_change)

        if decline_pct >= self.DECLINE_THRESHOLDS["critical"]:
            severity = "high"
            urgency = FindingUrgency.SOON.value
        elif decline_pct >= self.DECLINE_THRESHOLDS["warning"]:
            severity = "medium"
            urgency = FindingUrgency.SCHEDULED.value
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{platform} engagement rate declined "
                f"{decline_pct * 100:.0f}% over 30 days"
            ),
            description=(
                f"Engagement rate on {platform} dropped from "
                f"{previous_rate:.2%} to {current_rate:.2%} over the past "
                "30 days. Possible causes: algorithm changes, lower content "
                "quality, reduced posting frequency, or audience mismatch."
            ),
            suppression_key=f"engagement_decline_{platform}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="social_freshness",
            evidence={
                "platform": platform,
                "current_rate": current_rate,
                "previous_rate": previous_rate,
                "pct_change": round(pct_change * 100, 1),
                "period": "30_days",
            },
        )

    def _check_follower_growth(
        self,
        platform: str,
        current_followers: int,
        previous_followers: int,
        days: int,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Calculate follower growth rate and flag negative or flat growth.

        The follower counts would come from the platform's analytics API,
        comparing the current count against the count from *days* ago.
        """
        net_change = current_followers - previous_followers
        daily_growth_rate = net_change / max(days, 1)

        if net_change < 0:
            severity = "warning"
            urgency = FindingUrgency.SCHEDULED.value
            title = (
                f"{platform} lost {abs(net_change)} followers "
                f"over {days} days"
            )
            description = (
                f"The {platform} account went from {previous_followers:,} to "
                f"{current_followers:,} followers ({net_change:+,}). Losing "
                "followers may indicate content misalignment or audience issues."
            )
        elif net_change == 0 and days >= 30:
            severity = "low"
            urgency = FindingUrgency.INFORMATIONAL.value
            title = (
                f"{platform} follower count flat for {days} days"
            )
            description = (
                f"The {platform} account has stayed at {current_followers:,} "
                f"followers for {days} days. Flat growth may indicate the "
                "content is not reaching new audiences."
            )
        else:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=title,
            description=description,
            suppression_key=f"follower_growth_{platform}_{business_id}",
            urgency=urgency,
            severity=severity,
            category="social_freshness",
            evidence={
                "platform": platform,
                "current_followers": current_followers,
                "previous_followers": previous_followers,
                "net_change": net_change,
                "daily_growth_rate": round(daily_growth_rate, 2),
            },
        )

    def _check_reach_decline(
        self,
        platform: str,
        current_reach: float,
        previous_reach: float,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Compare 30-day reach to previous 30-day reach.

        Reach data would come from platform analytics APIs — total unique
        users who saw any content from the account in the period.
        A >30% decline may indicate an algorithm penalty or shadow-ban.
        """
        if previous_reach <= 0:
            return None

        pct_change = (current_reach - previous_reach) / previous_reach

        if pct_change >= 0:
            return None

        decline_pct = abs(pct_change)

        if decline_pct < 0.30:
            return None

        return create_watcher_finding(
            watcher_name=self.name,
            business_id=business_id,
            title=(
                f"{platform} reach declined {decline_pct * 100:.0f}% "
                "over 30 days"
            ),
            description=(
                f"Reach on {platform} dropped from {previous_reach:,.0f} to "
                f"{current_reach:,.0f} (down {decline_pct * 100:.0f}%). A "
                "decline this large may indicate an algorithm penalty, reduced "
                "content distribution, or audience mismatch. Review content "
                "strategy and consider format diversification."
            ),
            suppression_key=f"reach_decline_{platform}_{business_id}",
            urgency=FindingUrgency.SCHEDULED.value,
            severity="medium",
            category="social_freshness",
            evidence={
                "platform": platform,
                "current_reach": current_reach,
                "previous_reach": previous_reach,
                "pct_change": round(pct_change * 100, 1),
            },
            proposed_action={
                "action_type": "content_strategy_review",
                "description": (
                    "Review content strategy for this platform. Consider "
                    "format diversification (Reels, carousels, polls), "
                    "adjusted posting times, and audience re-targeting."
                ),
                "auto_eligible": False,
            },
        )

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="thursday_07:00",
            archetype_relevance=[],
            max_findings_per_run=15,
            suppression_window_days=14,
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


def _slug(url: str) -> str:
    """Convert a URL to a safe suppression-key component."""
    cleaned = url.replace("https://", "").replace("http://", "")
    return cleaned.replace("/", "_").replace(".", "_").rstrip("_")

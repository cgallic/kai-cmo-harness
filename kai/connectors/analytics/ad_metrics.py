"""Cross-platform ad metrics aggregator.

Normalizes ad performance data from multiple platforms (Google Ads,
Meta Ads, LinkedIn Ads, Microsoft Ads, TikTok Ads, etc.) into a
unified ``MetricPoint`` format.  This is not a subclass of
``AnalyticsConnector`` — it is a wrapper that orchestrates multiple
platform-specific connectors and merges their output.

The ``METRIC_MAPPING`` constant defines how each platform's proprietary
metric names translate to the canonical Kai vocabulary.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import DateRange, MetricPoint


# ---------------------------------------------------------------------------
# Canonical metric mapping
# ---------------------------------------------------------------------------

METRIC_MAPPING: Dict[str, Dict[str, str]] = {
    "google_ads": {
        "cost": "ad_spend",
        "cost_micros": "ad_spend_micros",
        "clicks": "ad_clicks",
        "impressions": "ad_impressions",
        "conversions": "ad_conversions",
        "conversions_value": "ad_conversion_value",
        "ctr": "ad_ctr",
        "average_cpc": "ad_cpc",
        "average_cpm": "ad_cpm",
        "interaction_rate": "ad_engagement_rate",
        "video_views": "ad_video_views",
        "video_quartile_p100_rate": "ad_video_completion_rate",
    },
    "meta_ads": {
        "spend": "ad_spend",
        "link_clicks": "ad_clicks",
        "clicks": "ad_clicks_all",
        "impressions": "ad_impressions",
        "actions": "ad_conversions",
        "action_values": "ad_conversion_value",
        "ctr": "ad_ctr",
        "cpc": "ad_cpc",
        "cpm": "ad_cpm",
        "reach": "ad_reach",
        "frequency": "ad_frequency",
        "video_thruplay_watched_actions": "ad_video_views",
        "video_p100_watched_actions": "ad_video_completion_rate",
    },
    "linkedin_ads": {
        "costInLocalCurrency": "ad_spend",
        "clicks": "ad_clicks",
        "impressions": "ad_impressions",
        "externalWebsiteConversions": "ad_conversions",
        "conversionValueInLocalCurrency": "ad_conversion_value",
        "clickThroughRate": "ad_ctr",
        "costPerClick": "ad_cpc",
        "costPer1000Impressions": "ad_cpm",
        "totalEngagements": "ad_engagements",
        "videoViews": "ad_video_views",
        "videoCompletions": "ad_video_completion_rate",
    },
    "microsoft_ads": {
        "Spend": "ad_spend",
        "Clicks": "ad_clicks",
        "Impressions": "ad_impressions",
        "Conversions": "ad_conversions",
        "Revenue": "ad_conversion_value",
        "Ctr": "ad_ctr",
        "AverageCpc": "ad_cpc",
        "AverageCpm": "ad_cpm",
    },
    "tiktok_ads": {
        "spend": "ad_spend",
        "clicks": "ad_clicks",
        "impressions": "ad_impressions",
        "conversions": "ad_conversions",
        "total_complete_payment_value": "ad_conversion_value",
        "ctr": "ad_ctr",
        "cpc": "ad_cpc",
        "cpm": "ad_cpm",
        "reach": "ad_reach",
        "frequency": "ad_frequency",
        "video_views_p100": "ad_video_completion_rate",
        "video_play_actions": "ad_video_views",
    },
    "pinterest_ads": {
        "SPEND_IN_DOLLAR": "ad_spend",
        "CLICKTHROUGH_1": "ad_clicks",
        "IMPRESSION_1": "ad_impressions",
        "TOTAL_CONVERSIONS": "ad_conversions",
        "TOTAL_CONVERSIONS_VALUE_IN_MICRO_DOLLAR": "ad_conversion_value",
        "CTR_1": "ad_ctr",
        "ECPC_IN_DOLLAR": "ad_cpc",
        "ECPM_IN_DOLLAR": "ad_cpm",
        "TOTAL_ENGAGEMENT": "ad_engagements",
        "VIDEO_MRC_VIEWS": "ad_video_views",
        "VIDEO_V100_COMPLETE_2S_COMBINED": "ad_video_completion_rate",
    },
}
"""Maps platform-specific metric names to canonical Kai metric names.

Keys are platform identifiers matching the connector dict keys passed
to ``AdMetricsAggregator.__init__``.  Values are dicts mapping the
platform's API metric name to the canonical name used in MetricPoint.
"""


# ---------------------------------------------------------------------------
# AdMetricsAggregator
# ---------------------------------------------------------------------------


class AdMetricsAggregator:
    """Cross-platform ad metrics aggregator.

    Accepts a dict of platform connectors and provides unified methods
    to query ad performance across all of them.  Handles metric name
    normalization so downstream consumers see a single vocabulary
    regardless of which ad platforms are active.

    This is NOT a subclass of ``AnalyticsConnector``.  It wraps
    platform-specific connector instances and merges their output.

    Usage::

        aggregator = AdMetricsAggregator({
            "google_ads": google_ads_connector,
            "meta_ads": meta_ads_connector,
        })
        metrics = aggregator.get_unified_ad_metrics(date_range)
    """

    def __init__(self, connectors: Dict[str, Any]) -> None:
        """Initialize with platform connectors.

        Args:
            connectors: Dict mapping platform name to connector instance.
                Keys should match METRIC_MAPPING keys (e.g., "google_ads",
                "meta_ads", "linkedin_ads").  Values are objects that
                expose a ``get_metrics(date_range, dimensions, metrics)``
                method returning platform-native data.
        """
        self.connectors = connectors

    def _normalize_metric_name(
        self,
        platform: str,
        raw_name: str,
    ) -> str:
        """Map a platform-specific metric name to its canonical equivalent.

        Falls back to ``"{platform}_{raw_name}"`` if no mapping exists.

        Args:
            platform: Platform key (e.g., "google_ads").
            raw_name: Raw metric name from the platform API.

        Returns:
            Canonical metric name string.
        """
        platform_map = METRIC_MAPPING.get(platform, {})
        return platform_map.get(raw_name, f"{platform}_{raw_name}")

    def _build_metric_point(
        self,
        platform: str,
        metric_name: str,
        value: float,
        date: str,
        dimension: str | None = None,
        dimension_name: str | None = None,
        extra_metadata: Dict[str, Any] | None = None,
    ) -> MetricPoint:
        """Create a MetricPoint with normalized naming and platform tag.

        Args:
            platform: Platform identifier.
            metric_name: Raw platform metric name (will be normalized).
            value: Metric value.
            date: ISO date string.
            dimension: Optional dimension value.
            dimension_name: Optional dimension key.
            extra_metadata: Additional metadata to merge.

        Returns:
            A MetricPoint with canonical metric name and source set to
            the platform name.
        """
        canonical_name = self._normalize_metric_name(platform, metric_name)
        metadata: Dict[str, Any] = {
            "platform": platform,
            "raw_metric_name": metric_name,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return MetricPoint(
            metric_name=canonical_name,
            value=value,
            date=date,
            dimension=dimension,
            dimension_name=dimension_name,
            source=platform,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Unified query methods
    # ------------------------------------------------------------------

    def get_unified_ad_metrics(
        self,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Pull metrics from all configured ad platform connectors.

        Production implementation would:
        1. Iterate over ``self.connectors``.
        2. For each platform, call the connector's ``get_metrics()``
           method with the date range and default dimensions/metrics.
        3. Normalize each returned data point's metric name using
           ``METRIC_MAPPING``.
        4. Tag each MetricPoint with ``source=platform_name``.
        5. Return the merged list sorted by date then platform.

        This gives downstream systems a single stream of MetricPoint
        objects covering all ad platforms, with consistent metric names.

        Args:
            date_range: Query period.

        Returns:
            Empty list (stub).  In production, one MetricPoint per
            (platform, metric, dimension, date) combination.
        """
        return []

    def get_spend_summary(
        self,
        date_range: DateRange,
    ) -> Dict[str, Any]:
        """Summarize ad spend across all platforms.

        Production implementation would:
        1. For each platform, fetch the ``ad_spend`` metric daily.
        2. Sum for total spend.
        3. Group by platform for per-platform breakdown.
        4. Group by campaign for per-campaign breakdown (requires
           campaign dimension).
        5. Build a daily trend list.

        Used by budget tracking watchers and marketing scorecards.

        Args:
            date_range: Query period.

        Returns:
            Dict with spend summary:
                - ``total_spend`` (float): Sum of all ad spend across
                  platforms.
                - ``spend_by_platform`` (Dict[str, float]): Spend per
                  platform.
                - ``spend_by_campaign`` (Dict[str, float]): Spend per
                  campaign (campaign names as keys).
                - ``daily_spend_trend`` (List[Dict]): List of
                  ``{"date": str, "spend": float, "platform": str}``
                  sorted by date.
        """
        spend_by_platform: Dict[str, float] = {
            platform: 0.0 for platform in self.connectors
        }
        return {
            "total_spend": 0.0,
            "spend_by_platform": spend_by_platform,
            "spend_by_campaign": {},
            "daily_spend_trend": [],
        }

    def get_roas_by_platform(
        self,
        date_range: DateRange,
    ) -> Dict[str, Any]:
        """Calculate return on ad spend per platform.

        Production implementation would:
        1. For each platform, fetch ``ad_spend`` and
           ``ad_conversion_value`` for the date range.
        2. Compute ROAS = conversion_value / spend for each platform.
        3. Handle zero-spend platforms gracefully (ROAS = 0.0).

        ROAS is the primary efficiency metric for paid media.  A ROAS
        below 1.0 means the platform is spending more than it earns;
        above 3.0 is generally considered strong for most industries.

        Args:
            date_range: Query period.

        Returns:
            Dict mapping platform name to ROAS data:
                ``{platform: {"spend": float, "revenue": float,
                              "roas": float}}``
        """
        result: Dict[str, Any] = {}
        for platform in self.connectors:
            result[platform] = {
                "spend": 0.0,
                "revenue": 0.0,
                "roas": 0.0,
            }
        return result

    def get_roas_by_campaign(
        self,
        date_range: DateRange,
    ) -> Dict[str, Any]:
        """Calculate return on ad spend per campaign across all platforms.

        Production implementation would:
        1. For each platform, fetch ``ad_spend`` and
           ``ad_conversion_value`` with the ``campaign`` dimension.
        2. Merge campaigns across platforms (prefix with platform name
           to avoid collisions if the same campaign name exists on
           multiple platforms).
        3. Compute ROAS = conversion_value / spend per campaign.

        Used to identify top-performing and underperforming campaigns
        for budget reallocation.

        Args:
            date_range: Query period.

        Returns:
            Dict mapping campaign identifier to ROAS data:
                ``{campaign_key: {"platform": str, "campaign_name": str,
                                  "spend": float, "revenue": float,
                                  "roas": float}}``

            Campaign keys are formatted as ``"{platform}::{campaign_name}"``
            to avoid collisions.
        """
        return {}

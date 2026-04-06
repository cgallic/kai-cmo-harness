"""Google Business Profile connector.

Wraps the Google Business Profile Performance API and exposes local
listing metrics as ``MetricPoint`` objects.  All methods are stubs that
document the exact API endpoints and parameters a production
implementation would use.

Google Business Profile API reference:
    https://developers.google.com/my-business/reference/performance/rest
    https://developers.google.com/my-business/reference/businessinformation/rest
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base import AnalyticsConnector, ConnectorConfig, DateRange, MetricPoint


class GBPConnector(AnalyticsConnector):
    """Google Business Profile connector.

    Expects ``config.property_id`` to contain the GBP location ID
    (e.g., ``"locations/123456789"`` or the full resource name
    ``"accounts/123/locations/456"``).  Credentials should include
    a service account or OAuth2 token with Business Profile API access.
    """

    connector_type = "gbp"

    # ------------------------------------------------------------------
    # Available metrics and dimensions
    # ------------------------------------------------------------------

    _METRICS: List[str] = sorted([
        "direction_requests",
        "maps_views",
        "phone_calls",
        "photo_count",
        "photo_views",
        "review_count",
        "review_rating",
        "search_views",
        "website_clicks",
    ])

    _DIMENSIONS: List[str] = sorted([
        "action_type",
        "date",
        "search_type",
    ])

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._location_id = config.property_id or ""

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def available_metrics(self) -> List[str]:
        """Return GBP metrics this connector can retrieve."""
        return list(self._METRICS)

    def available_dimensions(self) -> List[str]:
        """Return GBP dimensions this connector supports."""
        return list(self._DIMENSIONS)

    def get_metrics(
        self,
        date_range: DateRange,
        dimensions: List[str],
        metrics: List[str],
    ) -> List[MetricPoint]:
        """Fetch GBP performance metrics.

        Production implementation would call the Business Profile
        Performance API ``fetchMultiDailyMetricsTimeSeries`` endpoint:

            GET https://businessprofileperformance.googleapis.com/v1/{location}:fetchMultiDailyMetricsTimeSeries
                ?dailyMetrics=WEBSITE_CLICKS,CALL_CLICKS,BUSINESS_DIRECTION_REQUESTS,...
                &dailyRange.startDate.year=YYYY&dailyRange.startDate.month=M&dailyRange.startDate.day=D
                &dailyRange.endDate.year=YYYY&dailyRange.endDate.month=M&dailyRange.endDate.day=D

        The response contains daily time series for each requested
        metric.  Each data point is converted to a MetricPoint with
        ``source="gbp"`` and the date and metric name populated.

        For search impression metrics, use ``getDailyMetricsTimeSeries``
        with ``dailyMetric=BUSINESS_IMPRESSIONS_DESKTOP_SEARCH`` etc.

        Args:
            date_range: Query period.
            dimensions: Dimension keys (limited to date, search_type,
                action_type for GBP).
            metrics: Metric names to retrieve.

        Returns:
            Empty list (stub).
        """
        return []

    def get_events(
        self,
        event_name: str,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """GBP does not support custom event-level data.

        Google Business Profile tracks predefined actions (calls,
        direction requests, website clicks) but does not expose a
        custom event API.

        Returns:
            Empty list (always).
        """
        return []

    def get_real_time(self) -> List[MetricPoint]:
        """GBP does not support real-time data.

        Business Profile metrics are aggregated daily and typically
        delayed by 2-5 days.  There is no real-time reporting endpoint.

        Returns:
            Empty list (always).
        """
        return []

    def get_conversion_data(
        self,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Fetch GBP action metrics (direction requests, calls, clicks).

        Production implementation would call the Performance API to
        retrieve the action-oriented metrics:

            dailyMetrics: CALL_CLICKS, BUSINESS_DIRECTION_REQUESTS,
                          WEBSITE_CLICKS

        These represent the primary conversion actions from a GBP
        listing — a user clicking to call, requesting directions, or
        visiting the website.

        Args:
            date_range: Query period.

        Returns:
            Empty list (stub).  Each MetricPoint would have
            ``dimension_name="action_type"`` and ``metric_name`` set
            to ``"phone_calls"``, ``"direction_requests"``, or
            ``"website_clicks"``.
        """
        return []

    # ------------------------------------------------------------------
    # GBP-specific helpers
    # ------------------------------------------------------------------

    def get_review_metrics(
        self,
        date_range: DateRange,
    ) -> Dict[str, Any]:
        """Fetch review metrics for the listing.

        Production implementation would call the Business Information
        API ``accounts.locations.reviews.list`` endpoint:

            GET https://mybusiness.googleapis.com/v4/{parent=accounts/*/locations/*}/reviews
                ?pageSize=200
                &orderBy=updateTime desc

        Then aggregate the results to produce summary statistics.
        For new reviews in the period, filter by ``createTime`` within
        the date_range.

        Used by reputation monitoring watchers and audit scoring to
        evaluate the business's review health.

        Args:
            date_range: Period to evaluate for new reviews.

        Returns:
            Dict with review metrics:
                - ``total_reviews`` (int): Total review count on the
                  listing.
                - ``average_rating`` (float): Average star rating
                  (1.0-5.0).
                - ``new_reviews_in_period`` (int): Reviews created within
                  the date range.
                - ``rating_distribution`` (Dict[int, int]): Count of
                  reviews per star rating (keys 1-5).
                - ``unresponded_count`` (int): Reviews without an owner
                  response.
        """
        return {
            "total_reviews": 0,
            "average_rating": 0.0,
            "new_reviews_in_period": 0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            "unresponded_count": 0,
        }

    def get_listing_health(self) -> Dict[str, Any]:
        """Evaluate the completeness and health of the GBP listing.

        Production implementation would call the Business Information
        API ``accounts.locations.get`` endpoint:

            GET https://mybusiness.googleapis.com/v4/{name=accounts/*/locations/*}

        Then check each field for presence and quality:
        - Verification status
        - Suspension status
        - Photo count and presence
        - Business hours set
        - Description present and length
        - Primary and additional categories
        - Attributes filled out

        Used by the local SEO audit to score listing completeness and
        identify optimization opportunities.

        Returns:
            Dict with listing health indicators:
                - ``is_verified`` (bool): Whether the listing is verified.
                - ``is_suspended`` (bool): Whether the listing is
                  currently suspended.
                - ``has_photos`` (bool): Whether photos are uploaded.
                - ``photo_count`` (int): Number of photos on the listing.
                - ``has_hours`` (bool): Whether business hours are set.
                - ``has_description`` (bool): Whether a business
                  description is present.
                - ``has_categories`` (bool): Whether categories are set.
                - ``category_list`` (List[str]): Primary and additional
                  category names.
                - ``completeness_score`` (int): Overall listing
                  completeness from 0-100, based on how many recommended
                  fields are populated.
        """
        return {
            "is_verified": False,
            "is_suspended": False,
            "has_photos": False,
            "photo_count": 0,
            "has_hours": False,
            "has_description": False,
            "has_categories": False,
            "category_list": [],
            "completeness_score": 0,
        }

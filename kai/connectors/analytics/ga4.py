"""Google Analytics 4 connector.

Wraps the GA4 Data API v1 and exposes website analytics data as
``MetricPoint`` objects.  Uses the ``google-analytics-data`` SDK
(already in requirements).

Google Analytics Data API reference:
    https://developers.google.com/analytics/devguides/reporting/data/v1
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from .base import AnalyticsConnector, ConnectorConfig, DateRange, MetricPoint

logger = logging.getLogger(__name__)


class GA4Connector(AnalyticsConnector):
    """Google Analytics 4 connector using the GA4 Data API v1.

    Expects ``config.property_id`` to contain the GA4 property ID
    (e.g., ``"properties/123456789"`` or just ``"123456789"``).
    Credentials should include a ``type`` of ``"service_account_file"``
    and a ``path`` to the JSON key file.
    """

    connector_type = "ga4"

    # ------------------------------------------------------------------
    # Available metrics and dimensions
    # ------------------------------------------------------------------

    _METRICS: List[str] = sorted([
        "active_users",
        "average_session_duration",
        "bounce_rate",
        "conversions",
        "engaged_sessions",
        "engagement_rate",
        "event_count",
        "new_users",
        "page_views",
        "screen_page_views",
        "session_conversion_rate",
        "sessions",
        "user_engagement",
    ])

    _DIMENSIONS: List[str] = sorted([
        "city",
        "country",
        "date",
        "device_category",
        "event_name",
        "landing_page",
        "page_path",
        "page_title",
        "session_campaign",
        "session_medium",
        "session_source",
        "traffic_source",
    ])

    # Map from our snake_case names to GA4 API camelCase names
    _METRIC_API_MAP = {
        "active_users": "activeUsers",
        "average_session_duration": "averageSessionDuration",
        "bounce_rate": "bounceRate",
        "conversions": "conversions",
        "engaged_sessions": "engagedSessions",
        "engagement_rate": "engagementRate",
        "event_count": "eventCount",
        "new_users": "newUsers",
        "page_views": "screenPageViews",
        "screen_page_views": "screenPageViews",
        "session_conversion_rate": "sessionConversionRate",
        "sessions": "sessions",
        "user_engagement": "userEngagement",
    }

    _DIMENSION_API_MAP = {
        "city": "city",
        "country": "country",
        "date": "date",
        "device_category": "deviceCategory",
        "event_name": "eventName",
        "landing_page": "landingPage",
        "page_path": "pagePath",
        "page_title": "pageTitle",
        "session_campaign": "sessionCampaign",
        "session_medium": "sessionMedium",
        "session_source": "sessionSource",
        "traffic_source": "sessionDefaultChannelGroup",
    }

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        prop = config.property_id or ""
        # Normalize: ensure "properties/" prefix
        if prop and not prop.startswith("properties/"):
            prop = f"properties/{prop}"
        self._property_id = prop
        self._client: Any = None

    # ------------------------------------------------------------------
    # SDK client
    # ------------------------------------------------------------------

    def _get_client(self) -> Any:
        """Lazy-load the GA4 Data API client from credentials."""
        if self._client is not None:
            return self._client

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account
        except ImportError:
            raise ImportError(
                "GA4 connector requires google-analytics-data. "
                "Install: pip install google-analytics-data"
            )

        creds = self.config.credentials
        cred_type = creds.get("type", "service_account_file")

        if cred_type == "service_account_file":
            path = creds.get("path", "")
            if not path:
                raise ValueError("GA4 credentials missing 'path' to service account JSON")
            credentials = service_account.Credentials.from_service_account_file(
                path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
        else:
            raise ValueError(f"Unsupported GA4 credential type: {cred_type}")

        self._client = BetaAnalyticsDataClient(credentials=credentials)
        return self._client

    def _run_report(self, **kwargs: Any) -> Any:
        """Execute a GA4 runReport request and return the raw response.

        Accepts pre-built SDK objects (DateRange, Metric, Dimension, etc.)
        in kwargs.  The client's ``run_report`` method handles serialization.
        """
        client = self._get_client()
        # Build a simple namespace with property + kwargs for the client
        # The client accepts either a RunReportRequest or keyword args
        return client.run_report({"property": self._property_id, **kwargs})

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(
        self,
        response: Any,
        metric_names: List[str],
        dimension_names: List[str],
    ) -> List[MetricPoint]:
        """Convert GA4 API response rows to MetricPoint objects."""
        points: List[MetricPoint] = []
        if not hasattr(response, "rows") or not response.rows:
            return points

        for row in response.rows:
            # Extract dimensions
            date_val = ""
            dims = {}
            for i, dim_val in enumerate(row.dimension_values):
                name = dimension_names[i] if i < len(dimension_names) else f"dim_{i}"
                val = dim_val.value
                if name == "date" and len(val) == 8:
                    date_val = f"{val[:4]}-{val[4:6]}-{val[6:8]}"
                else:
                    dims[name] = val

            # Extract metrics — one MetricPoint per metric
            for j, metric_val in enumerate(row.metric_values):
                m_name = metric_names[j] if j < len(metric_names) else f"metric_{j}"
                try:
                    value = float(metric_val.value)
                except (ValueError, TypeError):
                    value = 0.0

                # Pick the first non-date dimension for the dimension field
                first_dim_name = next(iter(dims.keys()), None)
                first_dim_val = next(iter(dims.values()), None)

                points.append(MetricPoint(
                    metric_name=m_name,
                    value=value,
                    date=date_val,
                    dimension=first_dim_val,
                    dimension_name=first_dim_name,
                    source="ga4",
                    metadata=dict(dims) if len(dims) > 1 else {},
                ))

        return points

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by running a minimal report."""
        try:
            from google.analytics.data_v1beta.types import (
                DateRange as GA4DateRange, Metric,
            )
            self._run_report(
                date_ranges=[GA4DateRange(start_date="yesterday", end_date="today")],
                metrics=[Metric(name="sessions")],
            )
            return True
        except Exception as e:
            logger.warning("GA4 connect failed: %s", e)
            return False

    def available_metrics(self) -> List[str]:
        return list(self._METRICS)

    def available_dimensions(self) -> List[str]:
        return list(self._DIMENSIONS)

    def get_metrics(
        self,
        date_range: DateRange,
        dimensions: List[str],
        metrics: List[str],
    ) -> List[MetricPoint]:
        """Fetch GA4 metric data via the Data API v1 runReport endpoint."""
        from google.analytics.data_v1beta.types import (
            DateRange as GA4DateRange, Dimension, Metric,
        )

        ga4_dims = [
            Dimension(name=self._DIMENSION_API_MAP.get(d, d))
            for d in dimensions
        ]
        ga4_metrics = [
            Metric(name=self._METRIC_API_MAP.get(m, m))
            for m in metrics
        ]

        response = self._run_report(
            date_ranges=[GA4DateRange(
                start_date=date_range.start_date,
                end_date=date_range.end_date,
            )],
            dimensions=ga4_dims,
            metrics=ga4_metrics,
        )

        return self._parse_response(response, metrics, dimensions)

    def get_events(
        self,
        event_name: str,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Fetch event-level GA4 data filtered by event name."""
        from google.analytics.data_v1beta.types import (
            DateRange as GA4DateRange, Dimension, Metric, FilterExpression, Filter,
        )

        response = self._run_report(
            date_ranges=[GA4DateRange(
                start_date=date_range.start_date,
                end_date=date_range.end_date,
            )],
            dimensions=[
                Dimension(name="date"),
                Dimension(name="eventName"),
            ],
            metrics=[Metric(name="eventCount")],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(value=event_name),
                )
            ),
        )

        return self._parse_response(response, ["event_count"], ["date", "event_name"])

    def get_real_time(self) -> List[MetricPoint]:
        """Fetch GA4 real-time data."""
        from google.analytics.data_v1beta.types import (
            RunRealtimeReportRequest, Dimension, Metric,
        )

        client = self._get_client()
        request = RunRealtimeReportRequest(
            property=self._property_id,
            dimensions=[Dimension(name="unifiedScreenName")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="screenPageViews"),
            ],
        )
        response = client.run_realtime_report(request)
        return self._parse_response(response, ["active_users", "screen_page_views"], ["page_title"])

    def get_conversion_data(
        self,
        date_range: DateRange,
    ) -> List[MetricPoint]:
        """Fetch GA4 conversion metrics."""
        from google.analytics.data_v1beta.types import (
            DateRange as GA4DateRange, Dimension, Metric, FilterExpression, Filter,
        )

        response = self._run_report(
            date_ranges=[GA4DateRange(
                start_date=date_range.start_date,
                end_date=date_range.end_date,
            )],
            dimensions=[
                Dimension(name="date"),
                Dimension(name="eventName"),
            ],
            metrics=[
                Metric(name="conversions"),
                Metric(name="sessionConversionRate"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="isConversionEvent",
                    string_filter=Filter.StringFilter(value="true"),
                )
            ),
        )

        return self._parse_response(
            response, ["conversions", "session_conversion_rate"], ["date", "event_name"]
        )

    # ------------------------------------------------------------------
    # GA4-specific helpers
    # ------------------------------------------------------------------

    def get_landing_page_performance(self, date_range: DateRange) -> List[MetricPoint]:
        """Fetch per-landing-page sessions, conversions, and bounce rate."""
        return self.get_metrics(
            date_range,
            dimensions=["landing_page", "date"],
            metrics=["sessions", "conversions", "bounce_rate", "engagement_rate"],
        )

    def get_traffic_sources(self, date_range: DateRange) -> List[MetricPoint]:
        """Fetch sessions, users, and conversions per source/medium."""
        return self.get_metrics(
            date_range,
            dimensions=["session_source", "session_medium", "date"],
            metrics=["sessions", "active_users", "new_users", "conversions", "engagement_rate"],
        )

    def get_user_demographics(self, date_range: DateRange) -> List[MetricPoint]:
        """Fetch country, city, and device breakdowns."""
        points: List[MetricPoint] = []
        for dim in ["country", "city", "device_category"]:
            points.extend(self.get_metrics(
                date_range,
                dimensions=[dim],
                metrics=["active_users", "sessions"],
            ))
        return points

"""
Google Analytics 4 Module
Comprehensive GA4 reporting via Data API
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Handle both package and direct imports
try:
    from .config import config
except ImportError:
    from config import config


class GoogleAnalytics:
    """Google Analytics 4 Data API client"""

    def __init__(self, property_id: str = None, credentials_path: str = None):
        self.property_id = property_id or config.ga_property_id
        self.credentials_path = credentials_path or config.ga_credentials_path
        self._client = None

    def _get_client(self):
        """Lazy load the analytics client"""
        if self._client is None:
            try:
                from google.analytics.data_v1beta import BetaAnalyticsDataClient
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
                )
                self._client = BetaAnalyticsDataClient(credentials=credentials)
            except ImportError:
                raise ImportError("Install: pip install google-analytics-data")
        return self._client

    def _run_report(self, **kwargs) -> Dict:
        """Execute a GA4 report request"""
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric, OrderBy
        )

        client = self._get_client()

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            **kwargs
        )

        response = client.run_report(request)
        return response

    # ============ CORE REPORTS ============

    def get_overview(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get overall metrics summary"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="newUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate"),
            ]
        )

        if not response.rows:
            return {}

        row = response.rows[0]
        return {
            "active_users": int(row.metric_values[0].value),
            "new_users": int(row.metric_values[1].value),
            "sessions": int(row.metric_values[2].value),
            "page_views": int(row.metric_values[3].value),
            "avg_session_duration": f"{float(row.metric_values[4].value):.1f}s",
            "bounce_rate": f"{float(row.metric_values[5].value) * 100:.1f}%",
            "engagement_rate": f"{float(row.metric_values[6].value) * 100:.1f}%",
        }

    def get_daily_metrics(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get daily metrics trend"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
                Metric(name="newUsers"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
        )

        return [
            {
                "date": row.dimension_values[0].value,
                "active_users": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "page_views": int(row.metric_values[2].value),
                "new_users": int(row.metric_values[3].value),
            }
            for row in response.rows
        ] if response.rows else []

    # ============ TRAFFIC ANALYSIS ============

    def get_traffic_sources(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get traffic sources breakdown"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="newUsers"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "source": row.dimension_values[0].value,
                "medium": row.dimension_values[1].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "new_users": int(row.metric_values[2].value),
                "engagement_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    def get_channel_grouping(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get channel grouping breakdown"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="engagementRate"),
                Metric(name="averageSessionDuration"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)]
        )

        return [
            {
                "channel": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[3].value):.0f}s",
            }
            for row in response.rows
        ] if response.rows else []

    # ============ PAGE ANALYSIS ============

    def get_top_pages(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 30) -> List[Dict]:
        """Get top pages by views"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
            limit=limit
        )

        return [
            {
                "page": row.dimension_values[0].value,
                "page_views": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "avg_duration": f"{float(row.metric_values[2].value):.0f}s",
                "bounce_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    def get_landing_pages(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get landing pages performance"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="landingPage")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "landing_page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "bounce_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[3].value):.0f}s",
            }
            for row in response.rows
        ] if response.rows else []

    # ============ USER ANALYSIS ============

    def get_user_demographics(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get user demographics breakdown"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        # Countries
        country_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="country")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
            limit=10
        )

        # Devices
        device_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)]
        )

        # Browsers
        browser_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="browser")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
            limit=10
        )

        return {
            "countries": [
                {"country": r.dimension_values[0].value, "users": int(r.metric_values[0].value)}
                for r in country_response.rows
            ] if country_response.rows else [],
            "devices": [
                {"device": r.dimension_values[0].value, "users": int(r.metric_values[0].value)}
                for r in device_response.rows
            ] if device_response.rows else [],
            "browsers": [
                {"browser": r.dimension_values[0].value, "users": int(r.metric_values[0].value)}
                for r in browser_response.rows
            ] if browser_response.rows else [],
        }

    def get_new_vs_returning(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get new vs returning user breakdown"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="newVsReturning")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="engagementRate"),
            ]
        )

        return [
            {
                "type": row.dimension_values[0].value,
                "users": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    # ============ EVENTS ============

    def get_events(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 30) -> List[Dict]:
        """Get event tracking data"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="eventName")],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="totalUsers"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
            limit=limit
        )

        return [
            {
                "event": row.dimension_values[0].value,
                "count": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            }
            for row in response.rows
        ] if response.rows else []

    # ============ CONVERSIONS & GOALS ============

    def get_conversions(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get conversion events (key events in GA4)"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="eventName")],
            metrics=[
                Metric(name="conversions"),
                Metric(name="totalUsers"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=limit
        )

        return [
            {
                "event": row.dimension_values[0].value,
                "conversions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "value": float(row.metric_values[2].value),
                "conversion_rate": f"{(int(row.metric_values[0].value) / max(int(row.metric_values[1].value), 1)) * 100:.2f}%"
            }
            for row in response.rows
        ] if response.rows else []

    def get_conversion_paths(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get conversion paths by source/medium"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
            ],
            metrics=[
                Metric(name="conversions"),
                Metric(name="sessions"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=20
        )

        return [
            {
                "source": row.dimension_values[0].value,
                "medium": row.dimension_values[1].value,
                "conversions": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "value": float(row.metric_values[2].value),
                "conversion_rate": f"{(int(row.metric_values[0].value) / max(int(row.metric_values[1].value), 1)) * 100:.2f}%"
            }
            for row in response.rows
        ] if response.rows else []

    # ============ CAMPAIGN TRACKING (UTM) ============

    def get_campaign_performance(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get campaign performance (UTM campaigns)"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionCampaignName"),
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "campaign": row.dimension_values[0].value,
                "source": row.dimension_values[1].value,
                "medium": row.dimension_values[2].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
                "engagement_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    # ============ SEO SPECIFIC METRICS ============

    def get_organic_search_performance(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get organic search specific metrics"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter

        # Filter for organic traffic only
        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="landingPage")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="conversions"),
            ],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="sessionMedium",
                    string_filter=Filter.StringFilter(value="organic")
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=30
        )

        pages = [
            {
                "page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "bounce_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[3].value):.0f}s",
                "conversions": int(row.metric_values[4].value),
            }
            for row in response.rows
        ] if response.rows else []

        total_organic_sessions = sum(p["sessions"] for p in pages)
        total_organic_conversions = sum(p["conversions"] for p in pages)

        return {
            "total_organic_sessions": total_organic_sessions,
            "total_organic_conversions": total_organic_conversions,
            "organic_conversion_rate": f"{(total_organic_conversions / max(total_organic_sessions, 1)) * 100:.2f}%",
            "top_landing_pages": pages
        }

    def get_content_performance(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 30) -> List[Dict]:
        """Get content performance by page title"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="pageTitle"),
                Dimension(name="pagePath"),
            ],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="averageSessionDuration"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
            limit=limit
        )

        return [
            {
                "title": row.dimension_values[0].value,
                "path": row.dimension_values[1].value,
                "page_views": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "avg_duration": f"{float(row.metric_values[2].value):.0f}s",
                "engagement_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    def get_exit_pages(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get exit pages - where users leave the site"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="bounceRate"), desc=True)],
            limit=limit
        )

        return [
            {
                "page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "exit_rate": f"{float(row.metric_values[1].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    # ============ E-COMMERCE METRICS ============

    def get_ecommerce_overview(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get e-commerce metrics (if enabled)"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        try:
            response = self._run_report(
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                metrics=[
                    Metric(name="ecommercePurchases"),
                    Metric(name="purchaseRevenue"),
                    Metric(name="purchaseToViewRate"),
                    Metric(name="averagePurchaseRevenue"),
                    Metric(name="itemsViewed"),
                    Metric(name="itemsAddedToCart"),
                    Metric(name="cartToViewRate"),
                ]
            )

            if not response.rows:
                return {"enabled": False}

            row = response.rows[0]
            return {
                "enabled": True,
                "purchases": int(row.metric_values[0].value),
                "revenue": float(row.metric_values[1].value),
                "purchase_to_view_rate": f"{float(row.metric_values[2].value) * 100:.2f}%",
                "avg_order_value": float(row.metric_values[3].value),
                "items_viewed": int(row.metric_values[4].value),
                "items_added_to_cart": int(row.metric_values[5].value),
                "cart_to_view_rate": f"{float(row.metric_values[6].value) * 100:.2f}%",
            }
        except Exception:
            return {"enabled": False}

    def get_product_performance(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get product performance (e-commerce)"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        try:
            response = self._run_report(
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name="itemName")],
                metrics=[
                    Metric(name="itemsViewed"),
                    Metric(name="itemsAddedToCart"),
                    Metric(name="itemsPurchased"),
                    Metric(name="itemRevenue"),
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="itemRevenue"), desc=True)],
                limit=limit
            )

            return [
                {
                    "product": row.dimension_values[0].value,
                    "views": int(row.metric_values[0].value),
                    "add_to_cart": int(row.metric_values[1].value),
                    "purchases": int(row.metric_values[2].value),
                    "revenue": float(row.metric_values[3].value),
                }
                for row in response.rows
            ] if response.rows else []
        except Exception:
            return []

    # ============ USER ACQUISITION ANALYSIS ============

    def get_first_user_source(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get first user acquisition source"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="firstUserSource"),
                Dimension(name="firstUserMedium"),
            ],
            metrics=[
                Metric(name="newUsers"),
                Metric(name="sessions"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="newUsers"), desc=True)],
            limit=limit
        )

        return [
            {
                "source": row.dimension_values[0].value,
                "medium": row.dimension_values[1].value,
                "new_users": int(row.metric_values[0].value),
                "sessions": int(row.metric_values[1].value),
                "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
            }
            for row in response.rows
        ] if response.rows else []

    def get_user_lifetime_value(self, start_date: str = "90daysAgo", end_date: str = "today") -> Dict:
        """Get user lifetime metrics"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="newVsReturning")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="engagementRate"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
            ]
        )

        results = {
            "new": {"users": 0, "sessions": 0, "engagement_rate": "0%", "conversions": 0, "value": 0},
            "returning": {"users": 0, "sessions": 0, "engagement_rate": "0%", "conversions": 0, "value": 0},
        }

        for row in (response.rows or []):
            user_type = row.dimension_values[0].value.lower()
            if user_type in results:
                results[user_type] = {
                    "users": int(row.metric_values[0].value),
                    "sessions": int(row.metric_values[1].value),
                    "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                    "conversions": int(row.metric_values[3].value),
                    "value": float(row.metric_values[4].value),
                }

        return results

    # ============ ENGAGEMENT DEEP DIVE ============

    def get_engagement_metrics(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get detailed engagement metrics"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[
                Metric(name="engagedSessions"),
                Metric(name="engagementRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="screenPageViewsPerSession"),
                Metric(name="userEngagementDuration"),
                Metric(name="scrolledUsers"),
            ]
        )

        if not response.rows:
            return {}

        row = response.rows[0]
        return {
            "engaged_sessions": int(row.metric_values[0].value),
            "engagement_rate": f"{float(row.metric_values[1].value) * 100:.1f}%",
            "avg_session_duration": f"{float(row.metric_values[2].value):.1f}s",
            "pages_per_session": f"{float(row.metric_values[3].value):.2f}",
            "total_engagement_time": f"{float(row.metric_values[4].value) / 60:.0f} min",
            "scroll_users": int(row.metric_values[5].value),
        }

    def get_session_duration_distribution(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get session duration distribution"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionDurationBucket")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="sessionDurationBucket"))]
        )

        return [
            {
                "duration_bucket": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            }
            for row in response.rows
        ] if response.rows else []

    # ============ MARKETING AGENCY REPORTS ============

    def get_seo_agency_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Generate comprehensive SEO agency report"""
        return {
            "overview": self.get_overview(start_date, end_date),
            "organic_performance": self.get_organic_search_performance(start_date, end_date),
            "top_landing_pages": self.get_landing_pages(start_date, end_date, limit=15),
            "content_performance": self.get_content_performance(start_date, end_date, limit=15),
            "engagement": self.get_engagement_metrics(start_date, end_date),
            "conversions": self.get_conversions(start_date, end_date, limit=10),
            "user_acquisition": self.get_first_user_source(start_date, end_date, limit=10),
        }

    def get_ppc_agency_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Generate comprehensive PPC agency report"""
        return {
            "overview": self.get_overview(start_date, end_date),
            "campaigns": self.get_campaign_performance(start_date, end_date),
            "traffic_sources": self.get_traffic_sources(start_date, end_date),
            "channels": self.get_channel_grouping(start_date, end_date),
            "conversions": self.get_conversions(start_date, end_date),
            "conversion_paths": self.get_conversion_paths(start_date, end_date),
            "landing_pages": self.get_landing_pages(start_date, end_date, limit=10),
        }

    def get_full_marketing_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Generate complete marketing report"""
        return {
            "period": {"start": start_date, "end": end_date},
            "overview": self.get_overview(start_date, end_date),
            "engagement": self.get_engagement_metrics(start_date, end_date),
            "traffic": {
                "sources": self.get_traffic_sources(start_date, end_date),
                "channels": self.get_channel_grouping(start_date, end_date),
                "campaigns": self.get_campaign_performance(start_date, end_date),
            },
            "content": {
                "top_pages": self.get_top_pages(start_date, end_date),
                "landing_pages": self.get_landing_pages(start_date, end_date),
                "content_performance": self.get_content_performance(start_date, end_date),
            },
            "conversions": {
                "events": self.get_conversions(start_date, end_date),
                "paths": self.get_conversion_paths(start_date, end_date),
            },
            "audience": {
                "demographics": self.get_user_demographics(start_date, end_date),
                "new_vs_returning": self.get_new_vs_returning(start_date, end_date),
                "acquisition": self.get_first_user_source(start_date, end_date),
            },
            "seo": self.get_organic_search_performance(start_date, end_date),
            "ecommerce": self.get_ecommerce_overview(start_date, end_date),
            "events": self.get_events(start_date, end_date),
        }

    # ============ FUNNEL ANALYSIS ============

    def get_funnel_analysis(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Analyze user funnel from landing to conversion"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[
                Metric(name="sessions"),
                Metric(name="engagedSessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="userEngagementDuration"),
            ]
        )

        if not response.rows:
            return {}

        row = response.rows[0]
        sessions = int(row.metric_values[0].value)
        engaged = int(row.metric_values[1].value)
        users = int(row.metric_values[2].value)
        conversions = int(row.metric_values[3].value)

        return {
            "sessions": sessions,
            "engaged_sessions": engaged,
            "engagement_rate": f"{(engaged / max(sessions, 1)) * 100:.1f}%",
            "users": users,
            "conversions": conversions,
            "session_to_conversion_rate": f"{(conversions / max(sessions, 1)) * 100:.2f}%",
            "user_to_conversion_rate": f"{(conversions / max(users, 1)) * 100:.2f}%",
            "funnel_stages": [
                {"stage": "Sessions", "count": sessions, "drop_off": "0%"},
                {"stage": "Engaged", "count": engaged, "drop_off": f"{((sessions - engaged) / max(sessions, 1)) * 100:.1f}%"},
                {"stage": "Conversions", "count": conversions, "drop_off": f"{((engaged - conversions) / max(engaged, 1)) * 100:.1f}%"},
            ]
        }

    def get_page_funnel(self, funnel_pages: List[str], start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Track users through a specific page sequence funnel"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, FilterExpression, Filter

        results = []
        for i, page in enumerate(funnel_pages):
            response = self._run_report(
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="sessions"),
                ],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="pagePath",
                        string_filter=Filter.StringFilter(
                            value=page,
                            match_type=Filter.StringFilter.MatchType.CONTAINS
                        )
                    )
                )
            )

            users = sum(int(r.metric_values[0].value) for r in (response.rows or []))
            sessions = sum(int(r.metric_values[1].value) for r in (response.rows or []))

            prev_users = results[i-1]["users"] if i > 0 else users
            drop_off = ((prev_users - users) / max(prev_users, 1)) * 100

            results.append({
                "step": i + 1,
                "page": page,
                "users": users,
                "sessions": sessions,
                "drop_off_rate": f"{drop_off:.1f}%" if i > 0 else "N/A",
                "continuation_rate": f"{(users / max(prev_users, 1)) * 100:.1f}%" if i > 0 else "100%"
            })

        return results

    # ============ ATTRIBUTION ANALYSIS ============

    def get_attribution_comparison(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Compare first-touch vs last-touch attribution"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        # First-touch attribution
        first_touch = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="firstUserSource"),
                Dimension(name="firstUserMedium"),
            ],
            metrics=[
                Metric(name="conversions"),
                Metric(name="totalUsers"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=10
        )

        # Last-touch attribution (session-based)
        last_touch = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
            ],
            metrics=[
                Metric(name="conversions"),
                Metric(name="totalUsers"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=10
        )

        return {
            "first_touch": [
                {
                    "source": r.dimension_values[0].value,
                    "medium": r.dimension_values[1].value,
                    "conversions": int(r.metric_values[0].value),
                    "users": int(r.metric_values[1].value),
                    "value": float(r.metric_values[2].value),
                }
                for r in (first_touch.rows or [])
            ],
            "last_touch": [
                {
                    "source": r.dimension_values[0].value,
                    "medium": r.dimension_values[1].value,
                    "conversions": int(r.metric_values[0].value),
                    "users": int(r.metric_values[1].value),
                    "value": float(r.metric_values[2].value),
                }
                for r in (last_touch.rows or [])
            ]
        }

    def get_assisted_conversions(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get channels that assist conversions (not last-click)"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        # Get all touchpoints
        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionDefaultChannelGroup"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="engagedSessions"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)]
        )

        results = []
        for r in (response.rows or []):
            sessions = int(r.metric_values[0].value)
            engaged = int(r.metric_values[1].value)
            conversions = int(r.metric_values[2].value)
            value = float(r.metric_values[3].value)

            # Assisted = engaged sessions that didn't directly convert
            assisted = engaged - conversions if engaged > conversions else 0

            results.append({
                "channel": r.dimension_values[0].value,
                "sessions": sessions,
                "engaged_sessions": engaged,
                "direct_conversions": conversions,
                "assisted_sessions": assisted,
                "conversion_rate": f"{(conversions / max(sessions, 1)) * 100:.2f}%",
                "value": value,
                "value_per_session": f"${value / max(sessions, 1):.2f}",
            })

        return results

    # ============ COHORT ANALYSIS ============

    def get_cohort_retention(self, start_date: str = "90daysAgo", end_date: str = "today") -> Dict:
        """Get user cohort retention data"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        # Weekly cohorts
        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="firstSessionDate"),
                Dimension(name="nthDay"),
            ],
            metrics=[
                Metric(name="activeUsers"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="firstSessionDate"))],
            limit=1000
        )

        # Group by cohort week
        cohorts = {}
        for r in (response.rows or []):
            cohort_date = r.dimension_values[0].value
            nth_day = int(r.dimension_values[1].value)
            users = int(r.metric_values[0].value)

            if cohort_date not in cohorts:
                cohorts[cohort_date] = {"date": cohort_date, "day_0": 0, "retention": {}}

            if nth_day == 0:
                cohorts[cohort_date]["day_0"] = users
            cohorts[cohort_date]["retention"][nth_day] = users

        # Calculate retention rates
        for cohort in cohorts.values():
            day_0 = cohort["day_0"]
            for day, users in cohort["retention"].items():
                cohort["retention"][day] = {
                    "users": users,
                    "rate": f"{(users / max(day_0, 1)) * 100:.1f}%"
                }

        return {
            "cohorts": list(cohorts.values())[-10:],  # Last 10 cohorts
            "summary": {
                "total_cohorts": len(cohorts),
                "avg_day_7_retention": self._calc_avg_retention(cohorts, 7),
                "avg_day_14_retention": self._calc_avg_retention(cohorts, 14),
                "avg_day_30_retention": self._calc_avg_retention(cohorts, 30),
            }
        }

    def _calc_avg_retention(self, cohorts: Dict, day: int) -> str:
        """Helper to calculate average retention for a specific day"""
        rates = []
        for c in cohorts.values():
            if day in c.get("retention", {}) and c.get("day_0", 0) > 0:
                users = c["retention"][day].get("users", c["retention"][day]) if isinstance(c["retention"][day], dict) else c["retention"][day]
                rates.append(users / c["day_0"])
        return f"{(sum(rates) / max(len(rates), 1)) * 100:.1f}%" if rates else "N/A"

    def get_user_stickiness(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Calculate DAU/WAU/MAU stickiness ratios"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        # Get different time period metrics
        dau_response = self._run_report(
            date_ranges=[DateRange(start_date="1daysAgo", end_date="today")],
            metrics=[Metric(name="activeUsers")]
        )

        wau_response = self._run_report(
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            metrics=[Metric(name="activeUsers")]
        )

        mau_response = self._run_report(
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            metrics=[Metric(name="activeUsers")]
        )

        dau = int(dau_response.rows[0].metric_values[0].value) if dau_response.rows else 0
        wau = int(wau_response.rows[0].metric_values[0].value) if wau_response.rows else 0
        mau = int(mau_response.rows[0].metric_values[0].value) if mau_response.rows else 0

        return {
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "dau_wau_ratio": f"{(dau / max(wau, 1)) * 100:.1f}%",
            "dau_mau_ratio": f"{(dau / max(mau, 1)) * 100:.1f}%",
            "wau_mau_ratio": f"{(wau / max(mau, 1)) * 100:.1f}%",
            "interpretation": {
                "dau_mau": "Daily engagement" if (dau / max(mau, 1)) > 0.2 else "Weekly/occasional use",
                "health": "Strong" if (dau / max(mau, 1)) > 0.25 else "Moderate" if (dau / max(mau, 1)) > 0.1 else "Low engagement"
            }
        }

    # ============ REVENUE & ROI ANALYSIS ============

    def get_revenue_by_channel(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get revenue attribution by marketing channel"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionDefaultChannelGroup")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="purchaseRevenue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventValue"), desc=True)]
        )

        total_revenue = sum(float(r.metric_values[2].value) for r in (response.rows or []))

        return [
            {
                "channel": r.dimension_values[0].value,
                "sessions": int(r.metric_values[0].value),
                "conversions": int(r.metric_values[1].value),
                "revenue": float(r.metric_values[2].value),
                "purchase_revenue": float(r.metric_values[3].value),
                "revenue_share": f"{(float(r.metric_values[2].value) / max(total_revenue, 1)) * 100:.1f}%",
                "revenue_per_session": f"${float(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1):.2f}",
                "conversion_value": f"${float(r.metric_values[2].value) / max(int(r.metric_values[1].value), 1):.2f}" if int(r.metric_values[1].value) > 0 else "$0",
            }
            for r in (response.rows or [])
        ]

    def get_revenue_by_campaign(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get revenue attribution by campaign"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionCampaignName"),
                Dimension(name="sessionSource"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventValue"), desc=True)],
            limit=20
        )

        return [
            {
                "campaign": r.dimension_values[0].value,
                "source": r.dimension_values[1].value,
                "sessions": int(r.metric_values[0].value),
                "conversions": int(r.metric_values[1].value),
                "revenue": float(r.metric_values[2].value),
                "roas": f"{float(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1):.2f}",
                "cost_per_conversion": "N/A (connect ad spend)",
            }
            for r in (response.rows or [])
        ]

    def get_content_roi(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get content performance with conversion/revenue impact"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="landingPage"),
                Dimension(name="pageTitle"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="engagementRate"),
                Metric(name="bounceRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=limit
        )

        return [
            {
                "page": r.dimension_values[0].value,
                "title": r.dimension_values[1].value[:50],
                "sessions": int(r.metric_values[0].value),
                "users": int(r.metric_values[1].value),
                "conversions": int(r.metric_values[2].value),
                "revenue": float(r.metric_values[3].value),
                "conversion_rate": f"{(int(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1)) * 100:.2f}%",
                "engagement_rate": f"{float(r.metric_values[4].value) * 100:.1f}%",
                "bounce_rate": f"{float(r.metric_values[5].value) * 100:.1f}%",
                "revenue_per_session": f"${float(r.metric_values[3].value) / max(int(r.metric_values[0].value), 1):.2f}",
            }
            for r in (response.rows or [])
        ]

    # ============ USER JOURNEY ANALYSIS ============

    def get_user_paths(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get common user navigation paths"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="landingPage"),
                Dimension(name="pagePath"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "entry_page": r.dimension_values[0].value,
                "page_visited": r.dimension_values[1].value,
                "sessions": int(r.metric_values[0].value),
                "conversions": int(r.metric_values[1].value),
                "path_conversion_rate": f"{(int(r.metric_values[1].value) / max(int(r.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for r in (response.rows or [])
        ]

    def get_entry_exit_analysis(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 15) -> Dict:
        """Analyze entry and exit points"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        # Entry pages
        entry_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="landingPage")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
                Metric(name="conversions"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        # High bounce pages (likely exit points)
        exit_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="bounceRate"), desc=True)],
            limit=limit
        )

        return {
            "top_entry_pages": [
                {
                    "page": r.dimension_values[0].value,
                    "sessions": int(r.metric_values[0].value),
                    "bounce_rate": f"{float(r.metric_values[1].value) * 100:.1f}%",
                    "conversions": int(r.metric_values[2].value),
                }
                for r in (entry_response.rows or [])
            ],
            "top_exit_pages": [
                {
                    "page": r.dimension_values[0].value,
                    "sessions": int(r.metric_values[0].value),
                    "exit_rate": f"{float(r.metric_values[1].value) * 100:.1f}%",
                }
                for r in (exit_response.rows or []) if int(r.metric_values[0].value) > 10
            ]
        }

    # ============ SEGMENT ANALYSIS ============

    def get_device_performance(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get performance breakdown by device type"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)]
        )

        total_sessions = sum(int(r.metric_values[0].value) for r in (response.rows or []))

        return [
            {
                "device": r.dimension_values[0].value,
                "sessions": int(r.metric_values[0].value),
                "users": int(r.metric_values[1].value),
                "conversions": int(r.metric_values[2].value),
                "revenue": float(r.metric_values[3].value),
                "bounce_rate": f"{float(r.metric_values[4].value) * 100:.1f}%",
                "avg_duration": f"{float(r.metric_values[5].value):.0f}s",
                "traffic_share": f"{(int(r.metric_values[0].value) / max(total_sessions, 1)) * 100:.1f}%",
                "conversion_rate": f"{(int(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for r in (response.rows or [])
        ]

    def get_geo_performance(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 15) -> List[Dict]:
        """Get performance by geographic location"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="country"),
                Dimension(name="region"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "country": r.dimension_values[0].value,
                "region": r.dimension_values[1].value,
                "sessions": int(r.metric_values[0].value),
                "users": int(r.metric_values[1].value),
                "conversions": int(r.metric_values[2].value),
                "revenue": float(r.metric_values[3].value),
                "engagement_rate": f"{float(r.metric_values[4].value) * 100:.1f}%",
                "conversion_rate": f"{(int(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for r in (response.rows or [])
        ]

    def get_audience_segments(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get key audience segment breakdowns"""
        return {
            "by_device": self.get_device_performance(start_date, end_date),
            "by_geo": self.get_geo_performance(start_date, end_date),
            "new_vs_returning": self.get_new_vs_returning(start_date, end_date),
            "by_channel": self.get_channel_grouping(start_date, end_date),
        }

    # ============ TREND ANALYSIS ============

    def get_period_comparison(self, days: int = 30) -> Dict:
        """Compare current period to previous period"""
        from google.analytics.data_v1beta.types import DateRange, Metric

        current_start = f"{days}daysAgo"
        previous_start = f"{days * 2}daysAgo"
        previous_end = f"{days + 1}daysAgo"

        # Current period
        current = self._run_report(
            date_ranges=[DateRange(start_date=current_start, end_date="today")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate"),
            ]
        )

        # Previous period
        previous = self._run_report(
            date_ranges=[DateRange(start_date=previous_start, end_date=previous_end)],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="eventValue"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate"),
            ]
        )

        def calc_change(current_val, prev_val):
            if prev_val == 0:
                return "+100%" if current_val > 0 else "0%"
            change = ((current_val - prev_val) / prev_val) * 100
            return f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"

        curr_row = current.rows[0] if current.rows else None
        prev_row = previous.rows[0] if previous.rows else None

        if not curr_row or not prev_row:
            return {"error": "Insufficient data"}

        return {
            "period": f"Last {days} days vs previous {days} days",
            "users": {
                "current": int(curr_row.metric_values[0].value),
                "previous": int(prev_row.metric_values[0].value),
                "change": calc_change(int(curr_row.metric_values[0].value), int(prev_row.metric_values[0].value)),
            },
            "sessions": {
                "current": int(curr_row.metric_values[1].value),
                "previous": int(prev_row.metric_values[1].value),
                "change": calc_change(int(curr_row.metric_values[1].value), int(prev_row.metric_values[1].value)),
            },
            "conversions": {
                "current": int(curr_row.metric_values[2].value),
                "previous": int(prev_row.metric_values[2].value),
                "change": calc_change(int(curr_row.metric_values[2].value), int(prev_row.metric_values[2].value)),
            },
            "revenue": {
                "current": float(curr_row.metric_values[3].value),
                "previous": float(prev_row.metric_values[3].value),
                "change": calc_change(float(curr_row.metric_values[3].value), float(prev_row.metric_values[3].value)),
            },
            "bounce_rate": {
                "current": f"{float(curr_row.metric_values[4].value) * 100:.1f}%",
                "previous": f"{float(prev_row.metric_values[4].value) * 100:.1f}%",
                "change": calc_change(float(curr_row.metric_values[4].value), float(prev_row.metric_values[4].value)),
            },
            "engagement_rate": {
                "current": f"{float(curr_row.metric_values[5].value) * 100:.1f}%",
                "previous": f"{float(prev_row.metric_values[5].value) * 100:.1f}%",
                "change": calc_change(float(curr_row.metric_values[5].value), float(prev_row.metric_values[5].value)),
            },
        }

    def get_weekly_trends(self, weeks: int = 12) -> List[Dict]:
        """Get weekly trends for key metrics"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=f"{weeks * 7}daysAgo", end_date="today")],
            dimensions=[Dimension(name="dateHourMinute")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="conversions"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="dateHourMinute"))]
        )

        # Aggregate by week
        weekly_data = {}
        for r in (response.rows or []):
            date_str = r.dimension_values[0].value[:8]  # YYYYMMDD
            week = f"{date_str[:4]}-W{int(date_str[4:6]) // 7 + 1:02d}"

            if week not in weekly_data:
                weekly_data[week] = {"week": week, "users": 0, "sessions": 0, "conversions": 0}

            weekly_data[week]["users"] += int(r.metric_values[0].value)
            weekly_data[week]["sessions"] += int(r.metric_values[1].value)
            weekly_data[week]["conversions"] += int(r.metric_values[2].value)

        return list(weekly_data.values())

    def get_day_of_week_patterns(self, start_date: str = "90daysAgo", end_date: str = "today") -> List[Dict]:
        """Analyze performance patterns by day of week"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="dayOfWeek")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="dayOfWeek"))]
        )

        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

        return [
            {
                "day": day_names[int(r.dimension_values[0].value)],
                "day_number": int(r.dimension_values[0].value),
                "sessions": int(r.metric_values[0].value),
                "users": int(r.metric_values[1].value),
                "conversions": int(r.metric_values[2].value),
                "engagement_rate": f"{float(r.metric_values[3].value) * 100:.1f}%",
                "conversion_rate": f"{(int(r.metric_values[2].value) / max(int(r.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for r in (response.rows or [])
        ]

    def get_hour_of_day_patterns(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Analyze performance patterns by hour of day"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="hour")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
            ],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"))]
        )

        return [
            {
                "hour": int(r.dimension_values[0].value),
                "hour_label": f"{int(r.dimension_values[0].value):02d}:00",
                "sessions": int(r.metric_values[0].value),
                "users": int(r.metric_values[1].value),
                "conversions": int(r.metric_values[2].value),
            }
            for r in (response.rows or [])
        ]

    # ============ SITE HEALTH & TECHNICAL ============

    def get_page_speed_metrics(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get Core Web Vitals and page speed metrics"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy

        try:
            response = self._run_report(
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name="pagePath")],
                metrics=[
                    Metric(name="sessions"),
                ],
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
                limit=10
            )

            return {
                "note": "Core Web Vitals require Search Console API - see search_console.py",
                "top_pages_by_traffic": [
                    {"page": r.dimension_values[0].value, "sessions": int(r.metric_values[0].value)}
                    for r in (response.rows or [])
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    def get_error_pages(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get pages with high bounce rates (potential errors)"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="bounceRate"), desc=True)],
            limit=20
        )

        # Filter for pages with very high bounce and very low duration (likely errors)
        problem_pages = []
        for r in (response.rows or []):
            sessions = int(r.metric_values[0].value)
            bounce = float(r.metric_values[1].value)
            duration = float(r.metric_values[2].value)

            if sessions >= 10 and bounce > 0.8 and duration < 10:
                problem_pages.append({
                    "page": r.dimension_values[0].value,
                    "sessions": sessions,
                    "bounce_rate": f"{bounce * 100:.1f}%",
                    "avg_duration": f"{duration:.1f}s",
                    "issue": "Likely error page or broken content"
                })

        return problem_pages

    # ============ CMO EXECUTIVE REPORTS ============

    def get_cmo_executive_summary(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Executive summary for CMO - key metrics and insights"""
        overview = self.get_overview(start_date, end_date)
        comparison = self.get_period_comparison(30)
        funnel = self.get_funnel_analysis(start_date, end_date)
        revenue_by_channel = self.get_revenue_by_channel(start_date, end_date)
        stickiness = self.get_user_stickiness(start_date, end_date)

        # Calculate top performing channel
        top_channel = revenue_by_channel[0] if revenue_by_channel else {"channel": "N/A", "revenue": 0}

        return {
            "executive_summary": {
                "total_users": overview.get("active_users", 0),
                "total_sessions": overview.get("sessions", 0),
                "conversion_rate": funnel.get("session_to_conversion_rate", "0%"),
                "engagement_rate": overview.get("engagement_rate", "0%"),
                "user_growth": comparison.get("users", {}).get("change", "0%"),
                "revenue_growth": comparison.get("revenue", {}).get("change", "0%"),
            },
            "key_metrics_vs_previous_period": comparison,
            "funnel_performance": funnel,
            "top_revenue_channel": {
                "channel": top_channel.get("channel"),
                "revenue": top_channel.get("revenue"),
                "share": top_channel.get("revenue_share"),
            },
            "user_engagement_health": stickiness,
            "action_items": self._generate_action_items(overview, comparison, funnel, revenue_by_channel),
        }

    def _generate_action_items(self, overview: Dict, comparison: Dict, funnel: Dict, revenue_by_channel: List) -> List[str]:
        """Generate actionable insights based on data"""
        actions = []

        # Check bounce rate
        bounce = float(overview.get("bounce_rate", "0%").replace("%", ""))
        if bounce > 60:
            actions.append(f"High bounce rate ({bounce:.0f}%) - Review landing page experience and content relevance")

        # Check conversion trend
        conv_change = comparison.get("conversions", {}).get("change", "0%")
        if conv_change.startswith("-"):
            actions.append(f"Conversions declining ({conv_change}) - Audit conversion funnel and CTAs")

        # Check engagement
        eng = float(overview.get("engagement_rate", "0%").replace("%", ""))
        if eng < 50:
            actions.append(f"Low engagement ({eng:.0f}%) - Improve content quality and user experience")

        # Check channel diversification
        if revenue_by_channel and len(revenue_by_channel) > 0:
            top_share = float(revenue_by_channel[0].get("revenue_share", "0%").replace("%", ""))
            if top_share > 70:
                actions.append(f"Over-reliance on {revenue_by_channel[0]['channel']} ({top_share:.0f}% of revenue) - Diversify channels")

        if not actions:
            actions.append("Metrics look healthy - focus on scaling successful channels")

        return actions

    def get_marketing_manager_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Comprehensive report for marketing managers"""
        return {
            "period": {"start": start_date, "end": end_date},
            "overview": self.get_overview(start_date, end_date),
            "period_comparison": self.get_period_comparison(30),
            "funnel_analysis": self.get_funnel_analysis(start_date, end_date),
            "attribution": self.get_attribution_comparison(start_date, end_date),
            "channel_performance": {
                "by_revenue": self.get_revenue_by_channel(start_date, end_date),
                "by_channel_group": self.get_channel_grouping(start_date, end_date),
                "assisted_conversions": self.get_assisted_conversions(start_date, end_date),
            },
            "content_performance": {
                "content_roi": self.get_content_roi(start_date, end_date),
                "entry_exit": self.get_entry_exit_analysis(start_date, end_date),
            },
            "audience_insights": {
                "segments": self.get_audience_segments(start_date, end_date),
                "stickiness": self.get_user_stickiness(start_date, end_date),
            },
            "timing_insights": {
                "day_of_week": self.get_day_of_week_patterns(),
                "hour_of_day": self.get_hour_of_day_patterns(start_date, end_date),
            },
            "campaigns": self.get_campaign_performance(start_date, end_date),
            "issues": self.get_error_pages(start_date, end_date),
        }

    def get_weekly_standup_metrics(self) -> Dict:
        """Quick metrics for weekly marketing standup"""
        comparison = self.get_period_comparison(7)
        realtime = self.get_realtime()

        return {
            "right_now": {
                "active_users": realtime.get("total_active", 0),
            },
            "this_week_vs_last": {
                "users": comparison.get("users", {}),
                "sessions": comparison.get("sessions", {}),
                "conversions": comparison.get("conversions", {}),
                "revenue": comparison.get("revenue", {}),
            },
            "quick_wins": self._identify_quick_wins(),
        }

    def _identify_quick_wins(self) -> List[str]:
        """Identify quick win opportunities"""
        wins = []

        # Check for high-traffic low-converting pages
        content_roi = self.get_content_roi(limit=10)
        for page in content_roi:
            sessions = page.get("sessions", 0)
            conv_rate = float(page.get("conversion_rate", "0%").replace("%", ""))
            if sessions > 100 and conv_rate < 1:
                wins.append(f"Optimize {page['page'][:30]}... ({sessions} sessions, {conv_rate:.1f}% conv)")
                break

        # Check for day/time opportunities
        day_patterns = self.get_day_of_week_patterns()
        if day_patterns:
            best_day = max(day_patterns, key=lambda x: float(x.get("conversion_rate", "0%").replace("%", "")))
            wins.append(f"Best converting day: {best_day['day']} - schedule campaigns accordingly")

        return wins if wins else ["No immediate quick wins identified - review full report"]

    # ============ FACEBOOK/META ADS TRACKING ============

    def get_facebook_traffic(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get all Facebook/Meta traffic with detailed breakdown"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        # Filter for facebook source (covers fb, facebook, meta, instagram)
        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
                Dimension(name="sessionCampaignName"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="newUsers"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="meta", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="instagram", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="ig", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=50
        )

        campaigns = []
        total_sessions = 0
        total_conversions = 0
        total_users = 0

        for row in (response.rows or []):
            sessions = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            conversions = int(row.metric_values[3].value)

            total_sessions += sessions
            total_conversions += conversions
            total_users += users

            campaigns.append({
                "source": row.dimension_values[0].value,
                "medium": row.dimension_values[1].value,
                "campaign": row.dimension_values[2].value,
                "sessions": sessions,
                "users": users,
                "new_users": int(row.metric_values[2].value),
                "conversions": conversions,
                "engagement_rate": f"{float(row.metric_values[4].value) * 100:.1f}%",
                "bounce_rate": f"{float(row.metric_values[5].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[6].value):.0f}s",
                "conversion_rate": f"{(conversions / max(sessions, 1)) * 100:.2f}%",
            })

        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_users": total_users,
                "total_conversions": total_conversions,
                "overall_conversion_rate": f"{(total_conversions / max(total_sessions, 1)) * 100:.2f}%",
            },
            "campaigns": campaigns,
        }

    def get_facebook_daily_trend(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get daily Facebook traffic trend"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="meta", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
        )

        return [
            {
                "date": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
                "engagement_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
            }
            for row in (response.rows or [])
        ]

    def get_facebook_landing_pages(self, start_date: str = "30daysAgo", end_date: str = "today", limit: int = 20) -> List[Dict]:
        """Get landing page performance for Facebook traffic"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="landingPage")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
                Metric(name="conversions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="engagementRate"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="meta", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=limit
        )

        return [
            {
                "landing_page": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "conversions": int(row.metric_values[2].value),
                "bounce_rate": f"{float(row.metric_values[3].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[4].value):.0f}s",
                "engagement_rate": f"{float(row.metric_values[5].value) * 100:.1f}%",
                "conversion_rate": f"{(int(row.metric_values[2].value) / max(int(row.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for row in (response.rows or [])
        ]

    def get_facebook_conversions(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get conversion events from Facebook traffic"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="eventName")],
            metrics=[
                Metric(name="conversions"),
                Metric(name="totalUsers"),
                Metric(name="eventValue"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="meta", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="conversions"), desc=True)],
            limit=20
        )

        return [
            {
                "event": row.dimension_values[0].value,
                "conversions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "value": float(row.metric_values[2].value),
            }
            for row in (response.rows or [])
        ]

    def get_facebook_utm_breakdown(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get detailed UTM parameter breakdown for Facebook campaigns"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        # By campaign
        campaign_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionCampaignName")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=20
        )

        # By content (ad creative)
        content_response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="sessionManualAdContent")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="engagementRate"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
            limit=20
        )

        return {
            "by_campaign": [
                {
                    "campaign": row.dimension_values[0].value,
                    "sessions": int(row.metric_values[0].value),
                    "conversions": int(row.metric_values[1].value),
                    "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                    "conversion_rate": f"{(int(row.metric_values[1].value) / max(int(row.metric_values[0].value), 1)) * 100:.2f}%",
                }
                for row in (campaign_response.rows or [])
            ],
            "by_ad_content": [
                {
                    "content": row.dimension_values[0].value,
                    "sessions": int(row.metric_values[0].value),
                    "conversions": int(row.metric_values[1].value),
                    "engagement_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                    "conversion_rate": f"{(int(row.metric_values[1].value) / max(int(row.metric_values[0].value), 1)) * 100:.2f}%",
                }
                for row in (content_response.rows or [])
            ],
        }

    def get_facebook_device_breakdown(self, start_date: str = "30daysAgo", end_date: str = "today") -> List[Dict]:
        """Get device breakdown for Facebook traffic"""
        from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter, FilterExpressionList

        response = self._run_report(
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="conversions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
            ],
            dimension_filter=FilterExpression(
                or_group=FilterExpressionList(
                    expressions=[
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="facebook", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="fb", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                        FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(value="meta", match_type=Filter.StringFilter.MatchType.CONTAINS))),
                    ]
                )
            ),
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)]
        )

        total_sessions = sum(int(r.metric_values[0].value) for r in (response.rows or []))

        return [
            {
                "device": row.dimension_values[0].value,
                "sessions": int(row.metric_values[0].value),
                "conversions": int(row.metric_values[1].value),
                "bounce_rate": f"{float(row.metric_values[2].value) * 100:.1f}%",
                "avg_duration": f"{float(row.metric_values[3].value):.0f}s",
                "share": f"{(int(row.metric_values[0].value) / max(total_sessions, 1)) * 100:.1f}%",
                "conversion_rate": f"{(int(row.metric_values[1].value) / max(int(row.metric_values[0].value), 1)) * 100:.2f}%",
            }
            for row in (response.rows or [])
        ]

    def get_facebook_ads_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Comprehensive Facebook/Meta ads report from GA4"""
        return {
            "period": {"start": start_date, "end": end_date},
            "traffic_summary": self.get_facebook_traffic(start_date, end_date),
            "daily_trend": self.get_facebook_daily_trend(start_date, end_date),
            "landing_pages": self.get_facebook_landing_pages(start_date, end_date),
            "conversions": self.get_facebook_conversions(start_date, end_date),
            "utm_breakdown": self.get_facebook_utm_breakdown(start_date, end_date),
            "device_breakdown": self.get_facebook_device_breakdown(start_date, end_date),
        }

    # ============ REALTIME ============

    def get_realtime(self) -> Dict:
        """Get realtime active users"""
        try:
            from google.analytics.data_v1beta.types import (
                RunRealtimeReportRequest, Dimension, Metric
            )

            client = self._get_client()

            request = RunRealtimeReportRequest(
                property=f"properties/{self.property_id}",
                dimensions=[Dimension(name="country")],
                metrics=[Metric(name="activeUsers")]
            )

            response = client.run_realtime_report(request)

            total = sum(int(r.metric_values[0].value) for r in response.rows) if response.rows else 0

            return {
                "total_active": total,
                "by_country": [
                    {"country": r.dimension_values[0].value, "users": int(r.metric_values[0].value)}
                    for r in (response.rows or [])[:10]
                ]
            }
        except Exception as e:
            return {"total_active": 0, "by_country": [], "error": str(e)}

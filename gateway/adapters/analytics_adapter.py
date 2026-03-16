"""
Analytics adapter.

Wraps scripts/analytics modules for programmatic access.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure scripts path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from gateway.config import config


class AnalyticsAdapter:
    """Adapter for analytics CLI commands."""

    def __init__(self):
        self._ga = None
        self._gsc = None
        self._db = None
        self._dashboard = None

    def _get_ga(self, client: Optional[str] = None):
        """Get Google Analytics client, optionally for a specific client."""
        from scripts.analytics.google_analytics import GoogleAnalytics

        # If client specified, we could configure the GA property
        # For now, uses default from environment
        return GoogleAnalytics()

    def _get_gsc(self, client: Optional[str] = None):
        """Get Search Console client."""
        from scripts.analytics.search_console import SearchConsole
        return SearchConsole()

    def _get_db(self, client: Optional[str] = None):
        """Get Supabase analytics client."""
        from scripts.analytics.supabase_analytics import SupabaseAnalytics
        return SupabaseAnalytics()

    def _get_dashboard(self, client: Optional[str] = None):
        """Get dashboard client."""
        from scripts.analytics.dashboard import Dashboard
        return Dashboard()

    def get_summary(
        self,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> Dict[str, Any]:
        """Get executive summary."""
        dashboard = self._get_dashboard(client)
        return dashboard.get_executive_summary(start_date, end_date)

    def get_ga_overview(
        self,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> Dict[str, Any]:
        """Get Google Analytics overview."""
        ga = self._get_ga(client)
        return ga.get_overview(start_date, end_date)

    def get_ga_pages(
        self,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top pages from Google Analytics."""
        ga = self._get_ga(client)
        return ga.get_top_pages(start_date, end_date, limit)

    def get_ga_sources(
        self,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get traffic sources from Google Analytics."""
        ga = self._get_ga(client)
        return ga.get_traffic_sources(start_date, end_date, limit)

    def get_ga_channels(
        self,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> List[Dict[str, Any]]:
        """Get channel breakdown from Google Analytics."""
        ga = self._get_ga(client)
        return ga.get_channel_grouping(start_date, end_date)

    def get_gsc_queries(
        self,
        client: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top search queries from Search Console."""
        gsc = self._get_gsc(client)
        return gsc.get_top_queries(limit=limit)

    def get_gsc_opportunities(
        self,
        client: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get SEO keyword opportunities."""
        gsc = self._get_gsc(client)
        return gsc.get_keyword_opportunities()

    def get_db_leads(
        self,
        client: Optional[str] = None,
        limit: int = 30,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent leads from database."""
        db = self._get_db(client)
        return db.get_leads(limit=limit, status=status)

    def get_db_calls(
        self,
        client: Optional[str] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get recent calls from database."""
        db = self._get_db(client)
        return db.get_calls(limit=limit)

    def get_db_funnel(
        self,
        client: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get conversion funnel from database."""
        db = self._get_db(client)
        return db.get_conversion_funnel()

    def generate_report(
        self,
        report_type: str,
        client: Optional[str] = None,
        start_date: str = "30daysAgo",
        end_date: str = "today"
    ) -> Dict[str, Any]:
        """Generate a specific report type."""
        dashboard = self._get_dashboard(client)

        if report_type == "traffic":
            return dashboard.get_traffic_report(start_date, end_date)
        elif report_type == "seo":
            return dashboard.get_seo_report()
        elif report_type == "content":
            return dashboard.get_content_report(start_date, end_date)
        elif report_type == "leads":
            return dashboard.get_leads_sales_report(30)
        else:  # full
            return dashboard.get_executive_summary(start_date, end_date)

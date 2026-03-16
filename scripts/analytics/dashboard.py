"""
Unified Dashboard Module
Aggregates data from all sources for comprehensive reporting
"""

from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .google_analytics import GoogleAnalytics
from .search_console import SearchConsole
from .supabase_analytics import SupabaseAnalytics


class Dashboard:
    """Unified analytics dashboard"""

    def __init__(self):
        self.ga = GoogleAnalytics()
        self.gsc = SearchConsole()
        self.db = SupabaseAnalytics()

    def _safe_call(self, func, *args, **kwargs) -> Any:
        """Safely call a function and return None on error"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {"error": str(e)}

    # ============ EXECUTIVE SUMMARY ============

    def get_executive_summary(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get executive summary of all metrics"""
        results = {}

        # Run queries in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._safe_call, self.ga.get_overview, start_date, end_date): "ga_overview",
                executor.submit(self._safe_call, self.gsc.get_daily_performance): "gsc_daily",
                executor.submit(self._safe_call, self.db.get_table_counts): "db_stats",
                executor.submit(self._safe_call, self.db.get_leads_by_status): "leads_by_status",
                executor.submit(self._safe_call, self.db.get_conversion_funnel): "funnel",
            }

            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result()

        # Calculate GSC totals
        gsc_totals = {"clicks": 0, "impressions": 0}
        if results.get("gsc_daily") and not isinstance(results["gsc_daily"], dict):
            for day in results["gsc_daily"]:
                gsc_totals["clicks"] += day.get("clicks", 0)
                gsc_totals["impressions"] += day.get("impressions", 0)

        ga_data = results.get("ga_overview", {})
        db_stats = results.get("db_stats", {})
        leads_status = results.get("leads_by_status", {})
        funnel = results.get("funnel", {})

        return {
            "website": {
                "title": "Website Performance",
                "users": ga_data.get("active_users", "N/A"),
                "sessions": ga_data.get("sessions", "N/A"),
                "page_views": ga_data.get("page_views", "N/A"),
                "bounce_rate": ga_data.get("bounce_rate", "N/A"),
                "engagement_rate": ga_data.get("engagement_rate", "N/A"),
            },
            "search": {
                "title": "Search Performance (SEO)",
                "clicks": gsc_totals["clicks"],
                "impressions": gsc_totals["impressions"],
                "avg_ctr": f"{(gsc_totals['clicks'] / gsc_totals['impressions']) * 100:.2f}%"
                          if gsc_totals["impressions"] > 0 else "N/A",
            },
            "business": {
                "title": "Business Metrics",
                "total_leads": db_stats.get("leads", "N/A"),
                "total_calls": db_stats.get("calls", "N/A"),
                "total_proposals": db_stats.get("proposals", "N/A"),
                "active_agents": db_stats.get("agents", "N/A"),
                "leads_by_status": leads_status if not isinstance(leads_status, dict) or "error" not in leads_status else {},
            },
            "funnel": funnel if not isinstance(funnel, dict) or "error" not in funnel else None,
        }

    # ============ TRAFFIC REPORT ============

    def get_traffic_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get comprehensive traffic report"""
        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._safe_call, self.ga.get_channel_grouping, start_date, end_date): "channels",
                executor.submit(self._safe_call, self.ga.get_traffic_sources, start_date, end_date): "sources",
                executor.submit(self._safe_call, self.ga.get_daily_metrics, start_date, end_date): "daily",
                executor.submit(self._safe_call, self.ga.get_user_demographics, start_date, end_date): "demographics",
            }

            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result()

        return results

    # ============ SEO REPORT ============

    def get_seo_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get comprehensive SEO report"""
        results = {}

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self._safe_call, self.gsc.get_top_queries, start_date, end_date, 30): "top_queries",
                executor.submit(self._safe_call, self.gsc.get_top_pages, start_date, end_date, 30): "top_pages",
                executor.submit(self._safe_call, self.gsc.get_daily_performance, start_date, end_date): "daily",
                executor.submit(self._safe_call, self.gsc.get_device_breakdown, start_date, end_date): "devices",
                executor.submit(self._safe_call, self.gsc.get_country_breakdown, start_date, end_date, 15): "countries",
                executor.submit(self._safe_call, self.gsc.get_keyword_opportunities, start_date, end_date): "opportunities",
            }

            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result()

        # Extract opportunities
        opps = results.get("opportunities", {})
        if isinstance(opps, dict) and "error" not in opps:
            results["opportunities"] = opps.get("opportunities", [])
            results["quick_wins"] = opps.get("quick_wins", [])
        else:
            results["opportunities"] = []
            results["quick_wins"] = []

        return results

    # ============ CONTENT REPORT ============

    def get_content_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Get content performance report"""
        results = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._safe_call, self.ga.get_top_pages, start_date, end_date, 30): "ga_pages",
                executor.submit(self._safe_call, self.ga.get_landing_pages, start_date, end_date, 20): "landing_pages",
                executor.submit(self._safe_call, self.gsc.get_top_pages, None, None, 30): "gsc_pages",
                executor.submit(self._safe_call, self.gsc.get_content_gaps): "content_gaps",
            }

            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result()

        return results

    # ============ LEADS & SALES REPORT ============

    def get_leads_sales_report(self, days: int = 30) -> Dict:
        """Get leads and sales pipeline report"""
        results = {}

        with ThreadPoolExecutor(max_workers=9) as executor:
            futures = {
                executor.submit(self._safe_call, self.db.get_leads, 50): "recent_leads",
                executor.submit(self._safe_call, self.db.get_calls, 50): "recent_calls",
                executor.submit(self._safe_call, self.db.get_leads_by_status): "leads_by_status",
                executor.submit(self._safe_call, self.db.get_leads_by_source): "leads_by_source",
                executor.submit(self._safe_call, self.db.get_calls_by_status): "calls_by_status",
                executor.submit(self._safe_call, self.db.get_daily_lead_trend, days): "lead_trend",
                executor.submit(self._safe_call, self.db.get_daily_call_trend, days): "call_trend",
                executor.submit(self._safe_call, self.db.get_conversion_funnel): "funnel",
                executor.submit(self._safe_call, self.db.get_proposals, 20): "recent_proposals",
            }

            for future in as_completed(futures):
                key = futures[future]
                results[key] = future.result()

        return results

    # ============ REALTIME ============

    def get_realtime(self) -> Dict:
        """Get realtime data"""
        return self._safe_call(self.ga.get_realtime)

    # ============ FULL REPORT ============

    def generate_full_report(self, start_date: str = "30daysAgo", end_date: str = "today") -> Dict:
        """Generate comprehensive report"""
        from datetime import datetime

        results = {}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.get_executive_summary, start_date, end_date): "executive",
                executor.submit(self.get_traffic_report, start_date, end_date): "traffic",
                executor.submit(self.get_seo_report): "seo",
                executor.submit(self.get_content_report, start_date, end_date): "content",
                executor.submit(self.get_leads_sales_report, 30): "leads",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    results[key] = {"error": str(e)}

        return {
            "generated_at": datetime.now().isoformat(),
            "period": {"start_date": start_date, "end_date": end_date},
            **results
        }

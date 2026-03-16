"""
Multi-Site Analytics
Query all connected GA and Search Console properties at once
"""

from typing import Dict, List, Any
from .google_analytics import GoogleAnalytics
from .search_console import SearchConsole
from .sites_config import GA_PROPERTIES, GSC_SITES, CREDENTIALS_PATH


class MultiSiteAnalytics:
    """Analytics across all connected sites"""

    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or CREDENTIALS_PATH

    # ============ SEARCH CONSOLE ============

    def get_all_gsc_overview(self, days: int = 30) -> Dict[str, Dict]:
        """Get Search Console overview for all sites"""
        results = {}

        for key, site_info in GSC_SITES.items():
            try:
                gsc = SearchConsole(
                    site_url=site_info["site_url"],
                    credentials_path=self.credentials_path
                )
                queries = gsc.get_top_queries(limit=100)

                total_clicks = sum(q["clicks"] for q in queries)
                total_impressions = sum(q["impressions"] for q in queries)

                results[key] = {
                    "name": site_info["name"],
                    "site_url": site_info["site_url"],
                    "total_clicks": total_clicks,
                    "total_impressions": total_impressions,
                    "top_queries": queries[:5],
                    "status": "ok",
                }
            except Exception as e:
                results[key] = {
                    "name": site_info["name"],
                    "status": "error",
                    "error": str(e)[:100],
                }

        return results

    def get_gsc_summary(self) -> str:
        """Get formatted Search Console summary for all sites"""
        data = self.get_all_gsc_overview()

        report = "SEARCH CONSOLE SUMMARY (Last 30 Days)\n"
        report += "=" * 50 + "\n\n"

        for key, info in data.items():
            if info.get("status") == "ok":
                report += f"{info['name']}\n"
                report += f"  Clicks: {info['total_clicks']}\n"
                report += f"  Impressions: {info['total_impressions']}\n"
                if info.get("top_queries"):
                    report += "  Top Queries:\n"
                    for q in info["top_queries"][:3]:
                        report += f"    - {q['query']}: {q['clicks']} clicks\n"
                report += "\n"
            else:
                report += f"{info['name']}: ERROR - {info.get('error', 'Unknown')}\n\n"

        return report

    def get_site_gsc(self, site_key: str) -> SearchConsole:
        """Get SearchConsole client for a specific site"""
        if site_key not in GSC_SITES:
            raise ValueError(f"Unknown site: {site_key}. Available: {list(GSC_SITES.keys())}")

        return SearchConsole(
            site_url=GSC_SITES[site_key]["site_url"],
            credentials_path=self.credentials_path
        )

    # ============ GOOGLE ANALYTICS ============

    def get_all_ga_overview(self, days: int = 30) -> Dict[str, Dict]:
        """Get Google Analytics overview for all properties"""
        results = {}
        start_date = f"{days}daysAgo"

        for key, prop_info in GA_PROPERTIES.items():
            try:
                ga = GoogleAnalytics(
                    property_id=prop_info["property_id"],
                    credentials_path=self.credentials_path
                )
                overview = ga.get_overview(start_date=start_date)

                results[key] = {
                    "name": prop_info["name"],
                    "property_id": prop_info["property_id"],
                    **overview,
                    "status": "ok",
                }
            except Exception as e:
                results[key] = {
                    "name": prop_info["name"],
                    "status": "error",
                    "error": str(e)[:100],
                }

        return results

    def get_ga_summary(self) -> str:
        """Get formatted GA summary for all properties"""
        data = self.get_all_ga_overview()

        report = "GOOGLE ANALYTICS SUMMARY (Last 30 Days)\n"
        report += "=" * 50 + "\n\n"

        for key, info in data.items():
            if info.get("status") == "ok":
                report += f"{info['name']}\n"
                report += f"  Active Users: {info.get('active_users', 'N/A')}\n"
                report += f"  Sessions: {info.get('sessions', 'N/A')}\n"
                report += f"  Page Views: {info.get('page_views', 'N/A')}\n"
                report += f"  Bounce Rate: {info.get('bounce_rate', 'N/A')}\n"
                report += "\n"
            else:
                report += f"{info['name']}: ERROR - {info.get('error', 'Unknown')}\n\n"

        return report

    def get_site_ga(self, site_key: str) -> GoogleAnalytics:
        """Get GoogleAnalytics client for a specific site"""
        if site_key not in GA_PROPERTIES:
            raise ValueError(f"Unknown site: {site_key}. Available: {list(GA_PROPERTIES.keys())}")

        return GoogleAnalytics(
            property_id=GA_PROPERTIES[site_key]["property_id"],
            credentials_path=self.credentials_path
        )

    # ============ COMBINED REPORTS ============

    def get_full_report(self) -> str:
        """Get complete analytics report for all sites"""
        report = "=" * 60 + "\n"
        report += "           MULTI-SITE ANALYTICS REPORT\n"
        report += "=" * 60 + "\n\n"

        report += self.get_ga_summary()
        report += "\n"
        report += self.get_gsc_summary()

        return report


# Quick test
if __name__ == "__main__":
    multi = MultiSiteAnalytics()
    print(multi.get_gsc_summary())

"""
Google Search Console Module
SEO performance data and search analytics
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Handle both package and direct imports
try:
    from .config import config
except ImportError:
    from config import config


class SearchConsole:
    """Google Search Console API client"""

    def __init__(self, site_url: str = None, credentials_path: str = None):
        self.site_url = site_url or config.gsc_site_url
        self.credentials_path = credentials_path or config.gsc_credentials_path
        self._service = None

    def _get_service(self):
        """Lazy load the Search Console service"""
        if self._service is None:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build

                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
                )
                self._service = build("searchconsole", "v1", credentials=credentials)
            except ImportError:
                raise ImportError("Install: pip install google-api-python-client google-auth")
        return self._service

    def _get_date_string(self, days_offset: int) -> str:
        """Get date string for N days ago"""
        date = datetime.now() + timedelta(days=days_offset)
        return date.strftime("%Y-%m-%d")

    def _query(self, start_date: str, end_date: str, dimensions: List[str], row_limit: int = 100) -> List[Dict]:
        """Execute a Search Console query"""
        service = self._get_service()

        request = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit
        }

        response = service.searchanalytics().query(
            siteUrl=self.site_url,
            body=request
        ).execute()

        return response.get("rows", [])

    # ============ SEARCH PERFORMANCE ============

    def get_top_queries(self, start_date: str = None, end_date: str = None, limit: int = 50) -> List[Dict]:
        """Get top search queries"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["query"], limit)

        return [
            {
                "query": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ]

    def get_top_pages(self, start_date: str = None, end_date: str = None, limit: int = 50) -> List[Dict]:
        """Get top pages in search"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["page"], limit)

        return [
            {
                "page": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ]

    def get_query_page_combinations(self, start_date: str = None, end_date: str = None, limit: int = 100) -> List[Dict]:
        """Get query-page combinations"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["query", "page"], limit)

        return [
            {
                "query": row["keys"][0],
                "page": row["keys"][1],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ]

    def get_daily_performance(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get daily search performance"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["date"], 365)

        return sorted([
            {
                "date": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ], key=lambda x: x["date"])

    # ============ DEVICE & COUNTRY ANALYSIS ============

    def get_device_breakdown(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get performance by device"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["device"], 10)

        return [
            {
                "device": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ]

    def get_country_breakdown(self, start_date: str = None, end_date: str = None, limit: int = 20) -> List[Dict]:
        """Get performance by country"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["country"], limit)

        return [
            {
                "country": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
        ]

    # ============ KEYWORD OPPORTUNITIES ============

    def get_keyword_opportunities(self, start_date: str = None, end_date: str = None) -> Dict:
        """Find SEO improvement opportunities"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["query"], 500)

        # High impressions but improvable position (5-20)
        opportunities = [
            {
                "query": row["keys"][0],
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "position": f"{row['position']:.1f}",
            }
            for row in rows
            if row["impressions"] > 50 and 5 < row["position"] < 20
        ]
        opportunities.sort(key=lambda x: x["impressions"], reverse=True)

        # Quick wins: good position but low CTR
        quick_wins = [
            {
                "query": row["keys"][0],
                "impressions": row["impressions"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
            if row["position"] < 5 and row["ctr"] < 0.05
        ]
        quick_wins.sort(key=lambda x: x["impressions"], reverse=True)

        return {
            "opportunities": opportunities[:30],
            "quick_wins": quick_wins[:20]
        }

    def get_branded_vs_non_branded(self, brand_terms: List[str] = None) -> Dict:
        """Analyze branded vs non-branded traffic"""
        brand_terms = brand_terms or ["your_brand", "your_product"]
        brand_terms_lower = [t.lower() for t in brand_terms]

        start = self._get_date_string(-30)
        end = self._get_date_string(-1)

        rows = self._query(start, end, ["query"], 500)

        branded = []
        non_branded = []

        for row in rows:
            query = row["keys"][0].lower()
            data = {
                "query": row["keys"][0],
                "clicks": row["clicks"],
                "impressions": row["impressions"],
            }

            if any(term in query for term in brand_terms_lower):
                branded.append(data)
            else:
                non_branded.append(data)

        sum_metrics = lambda items: {
            "queries": len(items),
            "clicks": sum(i["clicks"] for i in items),
            "impressions": sum(i["impressions"] for i in items),
        }

        return {
            "branded": {
                **sum_metrics(branded),
                "top_queries": branded[:10]
            },
            "non_branded": {
                **sum_metrics(non_branded),
                "top_queries": non_branded[:10]
            }
        }

    # ============ CONTENT GAPS ============

    def get_content_gaps(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Find pages with high impressions but low CTR"""
        start = start_date or self._get_date_string(-30)
        end = end_date or self._get_date_string(-1)

        rows = self._query(start, end, ["page"], 200)

        gaps = [
            {
                "page": row["keys"][0],
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "ctr": f"{row['ctr'] * 100:.2f}%",
                "position": f"{row['position']:.1f}",
            }
            for row in rows
            if row["impressions"] > 100 and row["ctr"] < 0.02
        ]

        return sorted(gaps, key=lambda x: x["impressions"], reverse=True)[:20]

    # ============ COMPARISON ============

    def compare_periods(self, current_start: str, current_end: str,
                       previous_start: str, previous_end: str) -> Dict:
        """Compare two time periods"""
        current_rows = self._query(current_start, current_end, ["date"], 365)
        previous_rows = self._query(previous_start, previous_end, ["date"], 365)

        sum_metrics = lambda rows: {
            "clicks": sum(r["clicks"] for r in rows),
            "impressions": sum(r["impressions"] for r in rows),
        }

        current = sum_metrics(current_rows)
        previous = sum_metrics(previous_rows)

        def calc_change(curr, prev):
            if prev == 0:
                return "+100%" if curr > 0 else "0%"
            change = ((curr - prev) / prev) * 100
            return f"+{change:.1f}%" if change > 0 else f"{change:.1f}%"

        return {
            "current": current,
            "previous": previous,
            "changes": {
                "clicks": calc_change(current["clicks"], previous["clicks"]),
                "impressions": calc_change(current["impressions"], previous["impressions"]),
            }
        }

    # ============ SITEMAPS ============

    def get_sitemaps(self) -> List[Dict]:
        """Get sitemap status"""
        try:
            service = self._get_service()
            response = service.sitemaps().list(siteUrl=self.site_url).execute()

            return [
                {
                    "path": sm.get("path"),
                    "last_submitted": sm.get("lastSubmitted"),
                    "last_downloaded": sm.get("lastDownloaded"),
                    "warnings": sm.get("warnings", 0),
                    "errors": sm.get("errors", 0),
                }
                for sm in response.get("sitemap", [])
            ]
        except Exception as e:
            return [{"error": str(e)}]

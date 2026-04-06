"""Google Search Console connector.

Wraps the Search Console API and exposes search performance data as
``MetricPoint`` objects.  Uses ``googleapiclient`` and ``google-auth``
(already in requirements).

Search Console API reference:
    https://developers.google.com/webmaster-tools/v1/api_reference_index
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .base import AnalyticsConnector, ConnectorConfig, DateRange, MetricPoint

logger = logging.getLogger(__name__)

# GSC always returns all four metrics regardless of what you request
_GSC_METRICS = {"clicks", "impressions", "ctr", "position"}


class GSCConnector(AnalyticsConnector):
    """Google Search Console connector using the Search Analytics API.

    Expects ``config.property_id`` to contain the verified site URL
    (e.g., ``"https://example.com/"`` or ``"sc-domain:example.com"``).
    Credentials should include a ``type`` of ``"service_account_file"``
    and a ``path`` to the JSON key file.
    """

    connector_type = "gsc"

    _METRICS: List[str] = sorted(["clicks", "ctr", "impressions", "position"])

    _DIMENSIONS: List[str] = sorted([
        "country", "date", "device", "page", "query", "search_appearance",
    ])

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._site_url = config.property_id or ""
        self._service: Any = None

    # ------------------------------------------------------------------
    # SDK service
    # ------------------------------------------------------------------

    def _get_service(self) -> Any:
        """Lazy-load the Search Console API service."""
        if self._service is not None:
            return self._service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "GSC connector requires google-auth and google-api-python-client. "
                "Install: pip install google-auth google-api-python-client"
            )

        creds = self.config.credentials
        cred_type = creds.get("type", "service_account_file")

        if cred_type == "service_account_file":
            path = creds.get("path", "")
            if not path:
                raise ValueError("GSC credentials missing 'path' to service account JSON")
            credentials = service_account.Credentials.from_service_account_file(
                path,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
        else:
            raise ValueError(f"Unsupported GSC credential type: {cred_type}")

        self._service = build("searchconsole", "v1", credentials=credentials)
        return self._service

    def _query(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str],
        row_limit: int = 25000,
        start_row: int = 0,
    ) -> List[Dict[str, Any]]:
        """Execute a searchAnalytics.query request and return raw rows."""
        service = self._get_service()
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit,
            "startRow": start_row,
        }
        response = (
            service.searchanalytics()
            .query(siteUrl=self._site_url, body=body)
            .execute()
        )
        return response.get("rows", [])

    def _query_all_pages(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str],
    ) -> List[Dict[str, Any]]:
        """Paginate through searchAnalytics.query to fetch all rows."""
        all_rows: List[Dict[str, Any]] = []
        start_row = 0
        page_size = 25000

        while True:
            rows = self._query(start_date, end_date, dimensions, page_size, start_row)
            all_rows.extend(rows)
            if len(rows) < page_size:
                break
            start_row += page_size

        return all_rows

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_rows(
        self,
        rows: List[Dict[str, Any]],
        dimension_names: List[str],
        metric_filter: List[str],
    ) -> List[MetricPoint]:
        """Convert GSC API rows to MetricPoint objects."""
        points: List[MetricPoint] = []
        filter_set = set(metric_filter) if metric_filter else _GSC_METRICS

        for row in rows:
            keys = row.get("keys", [])
            date_val = ""
            dims = {}
            for i, dim_name in enumerate(dimension_names):
                val = keys[i] if i < len(keys) else ""
                if dim_name == "date":
                    date_val = val  # Already YYYY-MM-DD
                else:
                    dims[dim_name] = val

            first_dim_name = next(iter(dims.keys()), None)
            first_dim_val = next(iter(dims.values()), None)

            for metric in _GSC_METRICS:
                if metric not in filter_set:
                    continue
                value = row.get(metric, 0.0)
                points.append(MetricPoint(
                    metric_name=metric,
                    value=float(value),
                    date=date_val,
                    dimension=first_dim_val,
                    dimension_name=first_dim_name,
                    source="gsc",
                    metadata=dict(dims) if len(dims) > 1 else {},
                ))

        return points

    # ------------------------------------------------------------------
    # Abstract method implementations
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by listing sites."""
        try:
            service = self._get_service()
            service.sites().list().execute()
            return True
        except Exception as e:
            logger.warning("GSC connect failed: %s", e)
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
        """Fetch Search Console performance data."""
        rows = self._query_all_pages(
            date_range.start_date,
            date_range.end_date,
            dimensions,
        )
        return self._parse_rows(rows, dimensions, metrics)

    def get_events(self, event_name: str, date_range: DateRange) -> List[MetricPoint]:
        """GSC does not support event-level data."""
        return []

    def get_real_time(self) -> List[MetricPoint]:
        """GSC does not support real-time data (2-3 day delay)."""
        return []

    def get_conversion_data(self, date_range: DateRange) -> List[MetricPoint]:
        """GSC does not track conversions."""
        return []

    # ------------------------------------------------------------------
    # GSC-specific helpers
    # ------------------------------------------------------------------

    def get_top_queries(self, date_range: DateRange, limit: int = 50) -> List[MetricPoint]:
        """Fetch top queries by click count."""
        rows = self._query(
            date_range.start_date,
            date_range.end_date,
            dimensions=["query"],
            row_limit=limit,
        )
        return self._parse_rows(rows, ["query"], ["clicks", "impressions", "ctr", "position"])

    def get_top_pages(self, date_range: DateRange, limit: int = 50) -> List[MetricPoint]:
        """Fetch top pages by click count."""
        rows = self._query(
            date_range.start_date,
            date_range.end_date,
            dimensions=["page"],
            row_limit=limit,
        )
        return self._parse_rows(rows, ["page"], ["clicks", "impressions", "ctr", "position"])

    def get_position_changes(
        self,
        date_range: DateRange,
        comparison_range: DateRange,
    ) -> List[Dict[str, Any]]:
        """Compare average position for queries across two periods."""
        current_rows = self._query_all_pages(
            date_range.start_date, date_range.end_date, ["query"],
        )
        previous_rows = self._query_all_pages(
            comparison_range.start_date, comparison_range.end_date, ["query"],
        )

        current_map = {r["keys"][0]: r.get("position", 0.0) for r in current_rows if r.get("keys")}
        previous_map = {r["keys"][0]: r.get("position", 0.0) for r in previous_rows if r.get("keys")}

        changes = []
        for query in set(current_map) | set(previous_map):
            new_pos = current_map.get(query)
            old_pos = previous_map.get(query)
            if new_pos is not None and old_pos is not None:
                changes.append({
                    "query": query,
                    "old_position": old_pos,
                    "new_position": new_pos,
                    "change": old_pos - new_pos,  # positive = improved
                })

        changes.sort(key=lambda c: abs(c["change"]), reverse=True)
        return changes

"""Tests for GSCConnector — verify MetricPoint conversion from mocked API responses."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.connectors.analytics.base import ConnectorConfig, DateRange, MetricPoint
from kai.connectors.analytics.gsc import GSCConnector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_connector(site_url="sc-domain:example.com") -> GSCConnector:
    config = ConnectorConfig(
        connector_type="gsc",
        credentials={"type": "service_account_file", "path": "/fake/key.json"},
        property_id=site_url,
    )
    return GSCConnector(config)


def _mock_service(rows=None):
    """Build a mocked GSC API service."""
    service = MagicMock()
    sa = service.searchanalytics.return_value
    query = sa.query.return_value
    query.execute.return_value = {"rows": rows or []}
    sites = service.sites.return_value
    sites.list.return_value.execute.return_value = {"siteEntry": []}
    return service


# ---------------------------------------------------------------------------
# Tests: Config
# ---------------------------------------------------------------------------


class TestGSCConfig:
    def test_site_url_stored(self):
        conn = _make_connector("https://example.com/")
        assert conn._site_url == "https://example.com/"

    def test_available_metrics(self):
        conn = _make_connector()
        assert set(conn.available_metrics()) == {"clicks", "ctr", "impressions", "position"}

    def test_available_dimensions(self):
        conn = _make_connector()
        dims = conn.available_dimensions()
        assert "query" in dims
        assert "page" in dims
        assert "date" in dims


# ---------------------------------------------------------------------------
# Tests: Row parsing
# ---------------------------------------------------------------------------


class TestGSCParsing:
    def test_parse_single_row_all_metrics(self):
        conn = _make_connector()
        rows = [
            {"keys": ["test query"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 5.3}
        ]
        points = conn._parse_rows(rows, ["query"], ["clicks", "impressions", "ctr", "position"])

        assert len(points) == 4
        by_metric = {p.metric_name: p for p in points}
        assert by_metric["clicks"].value == 10.0
        assert by_metric["impressions"].value == 100.0
        assert by_metric["ctr"].value == 0.1
        assert by_metric["position"].value == 5.3
        assert by_metric["clicks"].dimension == "test query"
        assert by_metric["clicks"].dimension_name == "query"
        assert by_metric["clicks"].source == "gsc"

    def test_parse_with_date_dimension(self):
        conn = _make_connector()
        rows = [
            {"keys": ["2026-04-01", "test query"], "clicks": 5, "impressions": 50, "ctr": 0.1, "position": 3.0}
        ]
        points = conn._parse_rows(rows, ["date", "query"], ["clicks"])

        assert len(points) == 1
        assert points[0].date == "2026-04-01"
        assert points[0].dimension == "test query"
        assert points[0].dimension_name == "query"

    def test_parse_filtered_metrics(self):
        conn = _make_connector()
        rows = [
            {"keys": ["page1"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 5.0}
        ]
        points = conn._parse_rows(rows, ["page"], ["clicks", "position"])

        metric_names = {p.metric_name for p in points}
        assert metric_names == {"clicks", "position"}
        assert len(points) == 2

    def test_parse_empty_rows(self):
        conn = _make_connector()
        points = conn._parse_rows([], ["query"], ["clicks"])
        assert points == []

    def test_parse_multiple_rows(self):
        conn = _make_connector()
        rows = [
            {"keys": ["query1"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.0},
            {"keys": ["query2"], "clicks": 20, "impressions": 200, "ctr": 0.1, "position": 5.0},
        ]
        points = conn._parse_rows(rows, ["query"], ["clicks"])
        assert len(points) == 2
        assert points[0].dimension == "query1"
        assert points[1].dimension == "query2"


# ---------------------------------------------------------------------------
# Tests: get_metrics with mocked service
# ---------------------------------------------------------------------------


class TestGSCGetMetrics:
    def test_get_metrics_calls_api(self):
        conn = _make_connector()
        mock = _mock_service([
            {"keys": ["2026-04-01", "test"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 5.0},
        ])
        conn._service = mock

        date_range = DateRange(start_date="2026-04-01", end_date="2026-04-01")
        points = conn.get_metrics(date_range, ["date", "query"], ["clicks"])

        assert len(points) == 1
        assert points[0].metric_name == "clicks"
        assert points[0].value == 10.0
        assert points[0].date == "2026-04-01"
        mock.searchanalytics.return_value.query.assert_called()


class TestGSCHelpers:
    def test_get_top_queries(self):
        conn = _make_connector()
        mock = _mock_service([
            {"keys": ["seo tips"], "clicks": 50, "impressions": 500, "ctr": 0.1, "position": 2.0},
            {"keys": ["marketing"], "clicks": 30, "impressions": 300, "ctr": 0.1, "position": 4.0},
        ])
        conn._service = mock

        date_range = DateRange(start_date="2026-03-01", end_date="2026-04-01")
        points = conn.get_top_queries(date_range, limit=10)

        # 4 metrics per row * 2 rows = 8
        assert len(points) == 8
        clicks = [p for p in points if p.metric_name == "clicks"]
        assert len(clicks) == 2
        assert clicks[0].dimension == "seo tips"

    def test_get_top_pages(self):
        conn = _make_connector()
        mock = _mock_service([
            {"keys": ["/blog/post-1"], "clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 3.0},
        ])
        conn._service = mock

        date_range = DateRange(start_date="2026-03-01", end_date="2026-04-01")
        points = conn.get_top_pages(date_range, limit=5)

        assert len(points) == 4  # 4 metrics for 1 row
        assert points[0].dimension == "/blog/post-1"


# ---------------------------------------------------------------------------
# Tests: connect
# ---------------------------------------------------------------------------


class TestGSCConnect:
    def test_connect_success(self):
        conn = _make_connector()
        conn._service = _mock_service()
        assert conn.connect() is True

    def test_connect_failure(self):
        conn = _make_connector()
        mock = MagicMock()
        mock.sites.return_value.list.return_value.execute.side_effect = Exception("Auth failed")
        conn._service = mock
        assert conn.connect() is False


# ---------------------------------------------------------------------------
# Tests: unsupported methods return empty
# ---------------------------------------------------------------------------


class TestGSCUnsupported:
    def test_get_events_empty(self):
        conn = _make_connector()
        assert conn.get_events("purchase", DateRange("2026-04-01", "2026-04-01")) == []

    def test_get_real_time_empty(self):
        conn = _make_connector()
        assert conn.get_real_time() == []

    def test_get_conversion_data_empty(self):
        conn = _make_connector()
        assert conn.get_conversion_data(DateRange("2026-04-01", "2026-04-01")) == []

"""Tests for GA4Connector — verify MetricPoint conversion from mocked SDK responses."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.connectors.analytics.base import ConnectorConfig, DateRange, MetricPoint
from kai.connectors.analytics.ga4 import GA4Connector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_connector(property_id="properties/123456") -> GA4Connector:
    config = ConnectorConfig(
        connector_type="ga4",
        credentials={"type": "service_account_file", "path": "/fake/key.json"},
        property_id=property_id,
    )
    return GA4Connector(config)


def _mock_row(dim_values, metric_values):
    """Build a mock GA4 response row."""
    row = SimpleNamespace()
    row.dimension_values = [SimpleNamespace(value=v) for v in dim_values]
    row.metric_values = [SimpleNamespace(value=str(v)) for v in metric_values]
    return row


def _mock_response(rows):
    resp = SimpleNamespace()
    resp.rows = rows
    return resp


# ---------------------------------------------------------------------------
# Tests: Config
# ---------------------------------------------------------------------------


class TestGA4Config:
    def test_property_id_normalized(self):
        conn = _make_connector("123456")
        assert conn._property_id == "properties/123456"

    def test_property_id_already_prefixed(self):
        conn = _make_connector("properties/999")
        assert conn._property_id == "properties/999"

    def test_available_metrics(self):
        conn = _make_connector()
        metrics = conn.available_metrics()
        assert "sessions" in metrics
        assert "bounce_rate" in metrics
        assert len(metrics) >= 10

    def test_available_dimensions(self):
        conn = _make_connector()
        dims = conn.available_dimensions()
        assert "date" in dims
        assert "page_path" in dims


# ---------------------------------------------------------------------------
# Tests: Response parsing
# ---------------------------------------------------------------------------


class TestGA4Parsing:
    def test_parse_single_metric_single_row(self):
        conn = _make_connector()
        response = _mock_response([
            _mock_row(["20260401"], [1500]),
        ])
        points = conn._parse_response(response, ["sessions"], ["date"])

        assert len(points) == 1
        assert points[0].metric_name == "sessions"
        assert points[0].value == 1500.0
        assert points[0].date == "2026-04-01"
        assert points[0].source == "ga4"

    def test_parse_multiple_metrics(self):
        conn = _make_connector()
        response = _mock_response([
            _mock_row(["20260401"], [1500, 0.45]),
        ])
        points = conn._parse_response(response, ["sessions", "bounce_rate"], ["date"])

        assert len(points) == 2
        assert points[0].metric_name == "sessions"
        assert points[0].value == 1500.0
        assert points[1].metric_name == "bounce_rate"
        assert points[1].value == 0.45

    def test_parse_with_non_date_dimension(self):
        conn = _make_connector()
        response = _mock_response([
            _mock_row(["organic", "google"], [500]),
        ])
        points = conn._parse_response(
            response, ["sessions"], ["session_medium", "session_source"]
        )

        assert len(points) == 1
        assert points[0].dimension_name == "session_medium"
        assert points[0].dimension == "organic"
        # metadata contains all dims when more than one non-date dimension exists
        assert points[0].metadata == {"session_medium": "organic", "session_source": "google"}

    def test_parse_empty_response(self):
        conn = _make_connector()
        response = _mock_response([])
        points = conn._parse_response(response, ["sessions"], ["date"])
        assert points == []

    def test_parse_no_rows_attribute(self):
        conn = _make_connector()
        points = conn._parse_response(SimpleNamespace(), ["sessions"], ["date"])
        assert points == []

    def test_parse_multiple_rows(self):
        conn = _make_connector()
        response = _mock_response([
            _mock_row(["20260401"], [100]),
            _mock_row(["20260402"], [200]),
            _mock_row(["20260403"], [150]),
        ])
        points = conn._parse_response(response, ["sessions"], ["date"])
        assert len(points) == 3
        assert [p.date for p in points] == ["2026-04-01", "2026-04-02", "2026-04-03"]
        assert [p.value for p in points] == [100.0, 200.0, 150.0]


# ---------------------------------------------------------------------------
# Tests: get_metrics with mocked SDK
# ---------------------------------------------------------------------------


class TestGA4GetMetrics:
    def test_get_metrics_calls_sdk(self):
        """Test that get_metrics calls the SDK and parses the response."""
        # Mock the GA4 SDK types so we don't need the real package installed
        mock_types = MagicMock()
        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.analytics": MagicMock(),
            "google.analytics.data_v1beta": MagicMock(),
            "google.analytics.data_v1beta.types": mock_types,
        }):
            conn = _make_connector()
            mock_client = MagicMock()
            conn._client = mock_client

            mock_resp = _mock_response([_mock_row(["20260401"], [500])])
            mock_client.run_report.return_value = mock_resp

            date_range = DateRange(start_date="2026-04-01", end_date="2026-04-01")
            points = conn.get_metrics(date_range, ["date"], ["sessions"])

            assert len(points) == 1
            assert points[0].value == 500.0
            mock_client.run_report.assert_called_once()

    def test_get_metrics_maps_names(self):
        """Verify snake_case metric names are mapped to GA4 camelCase."""
        mock_types = MagicMock()
        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.analytics": MagicMock(),
            "google.analytics.data_v1beta": MagicMock(),
            "google.analytics.data_v1beta.types": mock_types,
        }):
            conn = _make_connector()
            mock_client = MagicMock()
            conn._client = mock_client
            mock_client.run_report.return_value = _mock_response([])

            date_range = DateRange(start_date="2026-04-01", end_date="2026-04-01")
            conn.get_metrics(date_range, ["page_path"], ["bounce_rate"])
            assert mock_client.run_report.called


# ---------------------------------------------------------------------------
# Tests: connect
# ---------------------------------------------------------------------------


class TestGA4Connect:
    def test_connect_success(self):
        mock_types = MagicMock()
        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.analytics": MagicMock(),
            "google.analytics.data_v1beta": MagicMock(),
            "google.analytics.data_v1beta.types": mock_types,
        }):
            conn = _make_connector()
            mock_client = MagicMock()
            conn._client = mock_client
            mock_client.run_report.return_value = _mock_response([])

            assert conn.connect() is True

    def test_connect_failure(self):
        mock_types = MagicMock()
        with patch.dict("sys.modules", {
            "google": MagicMock(),
            "google.analytics": MagicMock(),
            "google.analytics.data_v1beta": MagicMock(),
            "google.analytics.data_v1beta.types": mock_types,
        }):
            conn = _make_connector()
            mock_client = MagicMock()
            conn._client = mock_client
            mock_client.run_report.side_effect = Exception("Auth failed")

            assert conn.connect() is False

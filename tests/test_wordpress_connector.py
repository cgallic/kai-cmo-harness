"""Tests for WordPressConnector — mock httpx responses for all methods."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from kai.connectors.cms.wordpress import WordPressConnector
from kai.connectors.cms.base import (
    CMSAuthError,
    CMSNotFoundError,
    CMSRateLimitError,
    CMSUpdateError,
    ReadOnlyError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_connector(read_only=False):
    return WordPressConnector(
        {
            "site_url": "https://test.example.com",
            "username": "admin",
            "password": "app-password-here",
        },
        read_only=read_only,
    )


def _mock_httpx_response(status_code=200, json_data=None, text=""):
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# Tests: _request method
# ---------------------------------------------------------------------------


class TestWordPressRequest:
    @patch("httpx.request")
    def test_successful_get(self, mock_request):
        mock_request.return_value = _mock_httpx_response(
            200, {"namespace": "wp/v2", "routes": {}}
        )
        conn = _make_connector()
        result = conn._request("GET", "/")
        assert result["namespace"] == "wp/v2"
        mock_request.assert_called_once()

    @patch("httpx.request")
    def test_401_raises_auth_error(self, mock_request):
        mock_request.return_value = _mock_httpx_response(401)
        conn = _make_connector()
        with pytest.raises(CMSAuthError, match="Invalid WordPress credentials"):
            conn._request("GET", "/")

    @patch("httpx.request")
    def test_404_raises_not_found(self, mock_request):
        mock_request.return_value = _mock_httpx_response(404)
        conn = _make_connector()
        with pytest.raises(CMSNotFoundError, match="not found"):
            conn._request("GET", "pages/999")

    @patch("httpx.request")
    def test_429_raises_rate_limit(self, mock_request):
        mock_request.return_value = _mock_httpx_response(429)
        conn = _make_connector()
        with pytest.raises(CMSRateLimitError):
            conn._request("GET", "pages")

    @patch("httpx.request")
    def test_500_raises_update_error(self, mock_request):
        mock_request.return_value = _mock_httpx_response(
            500, text="Internal Server Error"
        )
        conn = _make_connector()
        with pytest.raises(CMSUpdateError, match="500"):
            conn._request("GET", "pages")


# ---------------------------------------------------------------------------
# Tests: connect
# ---------------------------------------------------------------------------


class TestWordPressConnect:
    @patch("httpx.request")
    def test_connect_success(self, mock_request):
        mock_request.return_value = _mock_httpx_response(
            200, {"namespace": "wp/v2", "description": "WordPress 6.5"}
        )
        conn = _make_connector()
        result = conn.connect()
        assert result["connected"] is True
        assert result["platform"] == "wordpress"
        assert result["version"] == "WordPress 6.5"
        assert conn._connected is True

    @patch("httpx.request")
    def test_connect_bad_credentials(self, mock_request):
        mock_request.return_value = _mock_httpx_response(401)
        conn = _make_connector()
        with pytest.raises(CMSAuthError):
            conn.connect()


# ---------------------------------------------------------------------------
# Tests: get_pages
# ---------------------------------------------------------------------------


class TestWordPressGetPages:
    @patch("httpx.request")
    def test_get_pages_returns_list(self, mock_request):
        mock_request.return_value = _mock_httpx_response(200, [
            {
                "id": 1,
                "title": {"rendered": "Home"},
                "slug": "home",
                "link": "https://test.example.com/",
                "status": "publish",
                "modified": "2026-04-01T10:00:00",
                "author": 1,
                "featured_media": 0,
            },
            {
                "id": 2,
                "title": {"rendered": "About"},
                "slug": "about",
                "link": "https://test.example.com/about/",
                "status": "publish",
                "modified": "2026-04-01T11:00:00",
                "author": 1,
                "featured_media": 0,
            },
        ])
        conn = _make_connector()
        pages = conn.get_pages()
        assert len(pages) == 2
        assert pages[0]["title"] == "Home"
        assert pages[1]["slug"] == "about"


# ---------------------------------------------------------------------------
# Tests: get_page
# ---------------------------------------------------------------------------


class TestWordPressGetPage:
    @patch("httpx.request")
    def test_get_page_returns_content(self, mock_request):
        mock_request.return_value = _mock_httpx_response(200, {
            "id": 42,
            "title": {"rendered": "Services"},
            "slug": "services",
            "link": "https://test.example.com/services/",
            "content": {
                "rendered": "<h2>Our Services</h2><p>We do things.</p>",
                "raw": "<h2>Our Services</h2><p>We do things.</p>",
            },
            "status": "publish",
            "modified": "2026-04-01T10:00:00",
        })
        conn = _make_connector()
        page = conn.get_page("42")
        assert page["id"] == "42"
        assert page["title"] == "Services"
        assert "Our Services" in page["content_html"]
        assert len(page["sections"]) >= 1


# ---------------------------------------------------------------------------
# Tests: update_page_section
# ---------------------------------------------------------------------------


class TestWordPressUpdateSection:
    @patch("httpx.request")
    def test_update_section_success(self, mock_request):
        # First call: get_page (via _request)
        get_response = _mock_httpx_response(200, {
            "id": 42,
            "title": {"rendered": "Services"},
            "slug": "services",
            "link": "https://test.example.com/services/",
            "content": {
                "rendered": "<h2>Old Heading</h2><p>Old content.</p>",
                "raw": "<h2>Old Heading</h2><p>Old content.</p>",
            },
            "status": "publish",
            "modified": "2026-04-01T10:00:00",
        })
        post_response = _mock_httpx_response(200, {"id": 42})

        mock_request.side_effect = [get_response, post_response]

        conn = _make_connector()
        result = conn.update_page_section("42", "section_0", "<h2>New Heading</h2>")
        assert result["success"] is True
        assert result["page_id"] == "42"

    def test_update_section_read_only_raises(self):
        conn = _make_connector(read_only=True)
        with pytest.raises(ReadOnlyError):
            conn.update_page_section("42", "section_0", "new content")


# ---------------------------------------------------------------------------
# Tests: metadata
# ---------------------------------------------------------------------------


class TestWordPressMetadata:
    @patch("httpx.request")
    def test_get_metadata_with_yoast(self, mock_request):
        mock_request.return_value = _mock_httpx_response(200, {
            "title": {"rendered": "Services"},
            "yoast_head_json": {
                "title": "Services | Example",
                "description": "We provide great services.",
                "og_title": "Services",
                "og_description": "Great services.",
                "canonical": "https://test.example.com/services/",
            },
        })
        conn = _make_connector()
        meta = conn.get_metadata("42")
        assert meta["title"] == "Services | Example"
        assert meta["meta_description"] == "We provide great services."

    @patch("httpx.request")
    def test_update_metadata_success(self, mock_request):
        mock_request.return_value = _mock_httpx_response(200, {"id": 42})
        conn = _make_connector()
        result = conn.update_metadata("42", {
            "title": "New Title",
            "meta_description": "New desc",
        })
        assert result["success"] is True
        assert "title" in result["updated_fields"]
        assert "meta_description" in result["updated_fields"]


# ---------------------------------------------------------------------------
# Tests: auth headers
# ---------------------------------------------------------------------------


class TestWordPressAuth:
    def test_basic_auth_headers(self):
        conn = _make_connector()
        headers = conn._auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_jwt_auth_headers(self):
        conn = WordPressConnector({
            "site_url": "https://test.example.com",
            "username": "admin",
            "password": "jwt-token-here",
            "auth_type": "jwt",
        })
        headers = conn._auth_headers()
        assert headers["Authorization"] == "Bearer jwt-token-here"


# ---------------------------------------------------------------------------
# Tests: section parsing
# ---------------------------------------------------------------------------


class TestWordPressSectionParsing:
    def test_parse_h2_sections(self):
        html = "<p>Hero content</p><h2>About</h2><p>About content</p><h2>Services</h2><p>Service content</p>"
        sections = WordPressConnector._parse_sections(html)
        assert len(sections) == 3
        assert sections[0]["type"] == "hero"
        assert sections[1]["heading"] == "About"
        assert sections[2]["heading"] == "Services"

    def test_parse_empty_html(self):
        assert WordPressConnector._parse_sections("") == []
        assert WordPressConnector._parse_sections("   ") == []

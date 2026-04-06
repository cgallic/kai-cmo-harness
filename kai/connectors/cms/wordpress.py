"""WordPress CMS connector — interfaces with the WP REST API v2.

This connector communicates with WordPress sites using the REST API v2
(``/wp-json/wp/v2/``). It supports Application Password and JWT
authentication, reads/writes pages, posts, and media, and extracts SEO
metadata from Yoast SEO fields when available.

No external HTTP libraries are imported at module level. All HTTP calls
are documented as stubs with comments describing the real request. In
production, replace stubs with ``httpx`` or ``aiohttp`` calls.

WordPress REST API reference:
    https://developer.wordpress.org/rest-api/reference/
"""

from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    CMSAuthError,
    CMSConnectionError,
    CMSConnector,
    CMSNotFoundError,
    CMSRateLimitError,
    CMSUpdateError,
    RateLimiter,
    ReadOnlyError,
)


class WordPressConnector(CMSConnector):
    """CMS connector for WordPress sites using the WP REST API v2.

    Config
    ------
    The ``config`` dict must contain:

    - ``site_url`` (str): WordPress site URL, e.g. ``"https://example.com"``.
      Trailing slashes are stripped automatically.
    - ``username`` (str): WP username or application password username.
    - ``password`` (str): Application password (NOT the user's login
      password). Generate one at WP Admin > Users > Application Passwords.
    - ``api_base`` (str, optional): REST API root path. Default
      ``"/wp-json/wp/v2"``.
    - ``auth_type`` (str, optional): ``"application_password"`` (default)
      or ``"jwt"``.
    - ``verify_ssl`` (bool, optional): Whether to verify TLS certificates.
      Default ``True``.

    Example::

        connector = WordPressConnector({
            "site_url": "https://plumber-example.com",
            "username": "kai-bot",
            "password": "xxxx xxxx xxxx xxxx xxxx xxxx",
        })
        info = connector.connect()
    """

    PLATFORM = "wordpress"

    # WordPress REST API default: ~100 requests/minute
    DEFAULT_RATE_LIMIT = 100
    DEFAULT_RATE_WINDOW = 60

    # Capabilities offered by a standard WordPress + Yoast install
    CAPABILITIES = [
        "read_pages",
        "write_pages",
        "read_media",
        "write_media",
        "read_metadata",
        "write_metadata",
        "custom_fields",
    ]

    def __init__(self, config: Dict[str, Any], read_only: bool = False) -> None:
        super().__init__(config, read_only)

        self.site_url: str = config["site_url"].rstrip("/")
        self.username: str = config["username"]
        self.password: str = config["password"]
        self.api_base: str = config.get("api_base", "/wp-json/wp/v2")
        self.auth_type: str = config.get("auth_type", "application_password")
        self.verify_ssl: bool = config.get("verify_ssl", True)

        self._base_url = f"{self.site_url}{self.api_base}"
        self._rate_limiter = RateLimiter(
            max_requests=self.DEFAULT_RATE_LIMIT,
            window_seconds=self.DEFAULT_RATE_WINDOW,
        )

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        """Build authentication headers for the configured auth type.

        For ``application_password``, uses HTTP Basic Auth with the
        username and application password encoded as base64.

        For ``jwt``, includes a Bearer token (the password field is
        expected to contain the JWT).
        """
        if self.auth_type == "jwt":
            return {"Authorization": f"Bearer {self.password}"}

        # Default: application_password → Basic auth
        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}

    def _check_rate_limit(self) -> None:
        """Record a request and raise if the rate limit is exceeded."""
        if not self._rate_limiter.check():
            wait = self._rate_limiter.wait_time()
            raise CMSRateLimitError(
                f"WordPress rate limit exceeded ({self.DEFAULT_RATE_LIMIT} "
                f"req/{self.DEFAULT_RATE_WINDOW}s). Retry in {wait:.1f}s."
            )
        self._rate_limiter.record()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        content: Optional[bytes] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30,
    ) -> Any:
        """Make an authenticated HTTP request to the WP REST API.

        Uses ``httpx`` for HTTP transport.  Handles common error codes
        with connector-specific exceptions.

        Returns the parsed JSON response body.
        """
        import httpx

        self._check_rate_limit()
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = {**self._auth_headers()}
        if extra_headers:
            headers.update(extra_headers)
        if json_body is not None:
            headers.setdefault("Content-Type", "application/json")

        response = httpx.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            content=content,
            verify=self.verify_ssl,
            timeout=timeout,
        )

        if response.status_code == 401:
            raise CMSAuthError("Invalid WordPress credentials")
        if response.status_code == 404:
            raise CMSNotFoundError(f"Resource not found: {path}")
        if response.status_code == 429:
            raise CMSRateLimitError("WordPress rate limit exceeded")
        if response.status_code >= 400:
            raise CMSUpdateError(
                f"WordPress API error {response.status_code}: "
                f"{response.text[:300]}"
            )

        return response.json()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> Dict[str, Any]:
        """Validate credentials by requesting the WP REST API root.

        HTTP: GET {site_url}/wp-json/wp/v2/
        Headers: Authorization (Basic or Bearer)
        Expected 200 response: JSON object with ``namespace``, ``routes``.
        A 401 response indicates invalid credentials.
        """
        data = self._request("GET", "/", timeout=15)
        self._connected = True
        return {
            "connected": True,
            "platform": self.PLATFORM,
            "site_url": self.site_url,
            "capabilities": list(self.CAPABILITIES),
            "version": data.get("description", "") if isinstance(data, dict) else None,
        }

    def disconnect(self) -> None:
        """Release connection state.

        WordPress REST API is stateless — this simply resets the internal
        connected flag.
        """
        self._connected = False

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def get_pages(
        self,
        page_type: str = "page",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List published pages or posts.

        HTTP: GET {base_url}/pages?per_page={limit}&offset={offset}&status=publish
        For posts: GET {base_url}/posts?per_page={limit}&offset={offset}&status=publish

        ``page_type`` mapping:
        - ``"page"`` → ``/pages``
        - ``"post"`` → ``/posts``
        - ``"product"`` → ``/product`` (WooCommerce custom post type)
        - ``"landing_page"`` → ``/pages?categories=landing-page`` (convention)
        - ``"collection"`` → not natively supported, falls back to ``/pages``
        """
        self._check_rate_limit()

        endpoint_map = {
            "page": "pages",
            "post": "posts",
            "product": "product",
            "landing_page": "pages",
            "collection": "pages",
        }
        endpoint = endpoint_map.get(page_type, "pages")

        params: Dict[str, Any] = {
            "per_page": min(limit, 100),
            "offset": offset,
            "status": "publish",
        }
        if page_type == "landing_page":
            params["categories"] = "landing-page"

        items = self._request("GET", endpoint, params=params)

        pages: List[Dict[str, Any]] = []
        for item in items:
            pages.append(self._normalize_page_list_item(item, page_type))
        return pages

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Fetch full page content with embedded resources.

        HTTP: GET {base_url}/pages/{page_id}?_embed
        The ``_embed`` parameter inlines featured image, author, and terms.

        For posts: GET {base_url}/posts/{page_id}?_embed
        """
        data = self._request("GET", f"pages/{page_id}", params={"_embed": ""})

        content_html = data.get("content", {}).get("rendered", "")
        content_raw = data.get("content", {}).get("raw", content_html)
        sections = self._parse_sections(content_html)

        return {
            "id": str(data.get("id", page_id)),
            "title": data.get("title", {}).get("rendered", ""),
            "slug": data.get("slug", ""),
            "url": data.get("link", f"{self.site_url}/?p={page_id}"),
            "content_html": content_html,
            "content_raw": content_raw,
            "sections": sections,
            "metadata": self._extract_metadata_from_page(data),
            "status": data.get("status", "unknown"),
            "modified_date": data.get("modified", ""),
        }

    # ------------------------------------------------------------------
    # Section updates
    # ------------------------------------------------------------------

    def update_page_section(
        self,
        page_id: str,
        section_id: str,
        content: str,
        content_type: str = "html",
    ) -> Dict[str, Any]:
        """Update a specific section of a WordPress page.

        Workflow:
        1. GET the current page content.
        2. Locate the target section by ``section_id`` (index or heading text).
        3. Replace the section content.
        4. POST the full updated content back.

        HTTP: POST {base_url}/pages/{page_id}
        Body (JSON): {"content": "<updated full HTML>"}
        Headers: Content-Type: application/json + Auth

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # Fetch current content to find and replace the target section
        current_page = self.get_page(page_id)
        current_html = current_page["content_html"]

        # Locate the section and capture previous content
        previous_content = ""
        updated_html = current_html
        sections = current_page.get("sections", [])

        for section in sections:
            if section.get("id") == section_id:
                previous_content = section.get("content", "")
                break

        if not previous_content and sections:
            # Try matching by index (section_id as "section_0", "section_1", etc.)
            try:
                idx = int(section_id.replace("section_", ""))
                if 0 <= idx < len(sections):
                    previous_content = sections[idx].get("content", "")
            except (ValueError, IndexError):
                pass

        # Build the new content with the section replaced
        if previous_content:
            updated_html = current_html.replace(previous_content, content, 1)

        self._request("POST", f"pages/{page_id}", json_body={"content": updated_html})

        return {
            "success": True,
            "page_id": str(page_id),
            "section_id": section_id,
            "previous_content": previous_content,
            "new_content": content,
        }

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, page_id: str) -> Dict[str, Any]:
        """Extract SEO metadata for a page.

        Uses Yoast SEO ``yoast_head_json`` field if the Yoast REST API
        extension is active. Falls back to parsing raw ``<head>`` content.

        HTTP: GET {base_url}/pages/{page_id}?_fields=yoast_head_json,meta,title
        """
        data = self._request(
            "GET", f"pages/{page_id}",
            params={"_fields": "yoast_head_json,meta,title,acf"},
        )
        return self._extract_metadata_from_page(data)

    def update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Update SEO metadata fields for a page.

        Maps metadata keys to Yoast SEO custom fields or standard WP
        meta fields and sends a POST request.

        HTTP: POST {base_url}/pages/{page_id}
        Body (JSON): {"title": "...", "meta": {"yoast_wpseo_metadesc": "..."}}

        Only fields present in ``meta`` are sent — unmentioned fields are
        not cleared.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # Map Kai metadata keys to WordPress/Yoast field names
        field_map = {
            "title": "title",
            "meta_description": "yoast_wpseo_metadesc",
            "og_title": "yoast_wpseo_opengraph-title",
            "og_description": "yoast_wpseo_opengraph-description",
            "og_image": "yoast_wpseo_opengraph-image",
            "canonical_url": "yoast_wpseo_canonical",
        }

        wp_body: Dict[str, Any] = {}
        wp_meta: Dict[str, str] = {}
        updated_fields: List[str] = []

        for kai_key, value in meta.items():
            if kai_key in field_map:
                wp_field = field_map[kai_key]
                if kai_key == "title":
                    wp_body["title"] = value
                else:
                    wp_meta[wp_field] = value
                updated_fields.append(kai_key)

        if wp_meta:
            wp_body["meta"] = wp_meta

        self._request("POST", f"pages/{page_id}", json_body=wp_body)

        return {
            "success": True,
            "page_id": str(page_id),
            "updated_fields": updated_fields,
        }

    # ------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------

    def get_media(
        self,
        limit: int = 50,
        offset: int = 0,
        media_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List media library items.

        HTTP: GET {base_url}/media?per_page={limit}&offset={offset}
        Optional filter: &media_type=image (image, video, application)

        WordPress media_type values: ``image``, ``video``, ``audio``,
        ``application`` (documents).
        """
        wp_type_map = {
            "image": "image",
            "video": "video",
            "document": "application",
        }
        params: Dict[str, Any] = {
            "per_page": min(limit, 100),
            "offset": offset,
        }
        if media_type and media_type in wp_type_map:
            params["media_type"] = wp_type_map[media_type]

        items = self._request("GET", "media", params=params)

        media_list: List[Dict[str, Any]] = []
        for item in items:
            media_list.append(self._normalize_media_item(item))
        return media_list

    def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to the WordPress media library.

        HTTP: POST {base_url}/media
        Headers: Content-Disposition: attachment; filename="photo.jpg"
        Body: multipart/form-data with file data

        After upload, if ``alt_text`` is provided, a second request
        updates the ``alt_text`` meta field:
        HTTP: POST {base_url}/media/{media_id}
        Body (JSON): {"alt_text": "..."}

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()

        filename = os.path.basename(file_path)
        media_title = title or os.path.splitext(filename)[0]

        with open(file_path, "rb") as fh:
            file_content = fh.read()

        data = self._request(
            "POST", "media",
            content=file_content,
            extra_headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            timeout=120,
        )

        media_id = str(data.get("id", ""))
        media_url = data.get("source_url", "")

        if alt_text and media_id:
            self._request("POST", f"media/{media_id}", json_body={"alt_text": alt_text})

        return {
            "success": True,
            "media_id": media_id,
            "url": media_url,
            "title": media_title,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_page_list_item(
        self, item: Dict[str, Any], page_type: str
    ) -> Dict[str, Any]:
        """Convert a WP REST API page/post object to the Kai page list format."""
        return {
            "id": str(item.get("id", "")),
            "title": item.get("title", {}).get("rendered", ""),
            "slug": item.get("slug", ""),
            "url": item.get("link", ""),
            "status": item.get("status", "unknown"),
            "page_type": page_type,
            "modified_date": item.get("modified", ""),
            "metadata": {
                "author": item.get("author", None),
                "featured_media": item.get("featured_media", None),
            },
        }

    def _normalize_media_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a WP REST API media object to the Kai media format."""
        mime = item.get("mime_type", "")
        if mime.startswith("image/"):
            media_type = "image"
        elif mime.startswith("video/"):
            media_type = "video"
        else:
            media_type = "document"

        details = item.get("media_details", {})
        sizes = details.get("sizes", {})
        width = details.get("width", 0)
        height = details.get("height", 0)
        dimensions = f"{width}x{height}" if width and height else None

        return {
            "id": str(item.get("id", "")),
            "title": item.get("title", {}).get("rendered", ""),
            "url": item.get("source_url", ""),
            "type": media_type,
            "mime_type": mime,
            "size_bytes": details.get("filesize", 0),
            "dimensions": dimensions,
            "alt_text": item.get("alt_text", None) or None,
            "uploaded_date": item.get("date", ""),
        }

    def _extract_metadata_from_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SEO metadata from a WP page response.

        Prefers Yoast SEO ``yoast_head_json`` fields. Falls back to
        standard WP fields.
        """
        yoast = data.get("yoast_head_json", {})
        acf = data.get("acf", {})

        if yoast:
            return {
                "title": yoast.get("title", ""),
                "meta_description": yoast.get("description", ""),
                "og_title": yoast.get("og_title", ""),
                "og_description": yoast.get("og_description", ""),
                "og_image": (
                    yoast.get("og_image", [{}])[0].get("url", "")
                    if yoast.get("og_image")
                    else ""
                ),
                "canonical_url": yoast.get("canonical", ""),
                "schema_markup": yoast.get("schema", {}).get("@graph", []),
                "custom_fields": acf,
            }

        # Fallback: extract from title and raw meta if Yoast is unavailable
        return {
            "title": data.get("title", {}).get("rendered", ""),
            "meta_description": "",
            "og_title": "",
            "og_description": "",
            "og_image": "",
            "canonical_url": data.get("link", ""),
            "schema_markup": [],
            "custom_fields": acf,
        }

    @staticmethod
    def _parse_sections(html: str) -> List[Dict[str, Any]]:
        """Parse WordPress page HTML into logical sections.

        Splits on Gutenberg block comments (``<!-- wp:heading -->``) or
        ``<h2>``/``<h3>`` tags when Gutenberg markers are absent.

        Returns a list of section dicts with ``id``, ``type``, ``heading``,
        and ``content`` keys.
        """
        if not html or not html.strip():
            return []

        sections: List[Dict[str, Any]] = []

        # Strategy 1: Gutenberg block comments
        # Pattern: <!-- wp:heading --> ... <!-- /wp:heading -->
        gutenberg_pattern = re.compile(
            r'<!-- wp:heading\s*(?:\{[^}]*\})?\s*-->(.*?)<!-- /wp:heading -->',
            re.DOTALL,
        )
        gutenberg_blocks = gutenberg_pattern.findall(html)

        if gutenberg_blocks:
            # Split content by heading blocks
            parts = gutenberg_pattern.split(html)
            section_idx = 0

            # First part (before any heading) is the hero/intro
            if parts and parts[0].strip():
                sections.append({
                    "id": f"section_{section_idx}",
                    "type": "hero",
                    "heading": "",
                    "content": parts[0].strip(),
                })
                section_idx += 1

            # Remaining parts alternate: heading content, between-heading content
            for i in range(1, len(parts), 2):
                heading_html = parts[i].strip() if i < len(parts) else ""
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""

                # Extract plain heading text
                heading_text = re.sub(r"<[^>]+>", "", heading_html).strip()

                sections.append({
                    "id": f"section_{section_idx}",
                    "type": "body",
                    "heading": heading_text,
                    "content": heading_html + "\n" + body if body else heading_html,
                })
                section_idx += 1

            return sections

        # Strategy 2: Fall back to <h2>/<h3> splitting
        heading_pattern = re.compile(
            r'(<h[23][^>]*>.*?</h[23]>)', re.DOTALL | re.IGNORECASE
        )
        parts = heading_pattern.split(html)
        section_idx = 0

        if parts and parts[0].strip():
            sections.append({
                "id": f"section_{section_idx}",
                "type": "hero",
                "heading": "",
                "content": parts[0].strip(),
            })
            section_idx += 1

        for i in range(1, len(parts), 2):
            heading_html = parts[i] if i < len(parts) else ""
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            heading_text = re.sub(r"<[^>]+>", "", heading_html).strip()

            sections.append({
                "id": f"section_{section_idx}",
                "type": "body",
                "heading": heading_text,
                "content": heading_html + "\n" + body if body else heading_html,
            })
            section_idx += 1

        # If no headings found, treat the whole content as one section
        if not sections and html.strip():
            sections.append({
                "id": "section_0",
                "type": "body",
                "heading": "",
                "content": html.strip(),
            })

        return sections

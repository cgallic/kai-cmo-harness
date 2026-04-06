"""Webflow CMS connector — interfaces with the Webflow API v2.

This connector communicates with Webflow sites using the API v2
(``https://api.webflow.com/v2``). It uses bearer token authentication
and supports reading/writing pages, collection items, and assets.

Webflow's content model differs from WordPress: static pages are
distinct from CMS collection items. This connector maps both to the
Kai page interface. Changes made via the API are staged — they require
an explicit publish call to go live.

No external HTTP libraries are imported at module level. All HTTP calls
are documented as stubs with comments describing the real request.

Webflow API v2 reference:
    https://developers.webflow.com/data/reference
"""

from __future__ import annotations

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


class WebflowConnector(CMSConnector):
    """CMS connector for Webflow sites using the Webflow API v2.

    Config
    ------
    The ``config`` dict must contain:

    - ``api_token`` (str): Webflow API v2 bearer token. Generate one at
      Webflow Dashboard > Site Settings > Integrations > API Access.
    - ``site_id`` (str): Webflow site ID (visible in site settings or
      the URL bar when editing).
    - ``api_base`` (str, optional): API base URL. Default
      ``"https://api.webflow.com/v2"``.

    Example::

        connector = WebflowConnector({
            "api_token": "wf_live_xxxxxxxxxxxx",
            "site_id": "63a1b2c3d4e5f6a7b8c9d0e1",
        })
        info = connector.connect()
    """

    PLATFORM = "webflow"

    # Webflow API v2: 60 requests/minute
    DEFAULT_RATE_LIMIT = 60
    DEFAULT_RATE_WINDOW = 60

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

        self.api_token: str = config["api_token"]
        self.site_id: str = config["site_id"]
        self.api_base: str = config.get("api_base", "https://api.webflow.com/v2")

        self._rate_limiter = RateLimiter(
            max_requests=self.DEFAULT_RATE_LIMIT,
            window_seconds=self.DEFAULT_RATE_WINDOW,
        )
        self._site_url: str = ""  # populated on connect
        self._collections_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        """Build authorization headers with the Webflow bearer token."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "accept": "application/json",
            "content-type": "application/json",
        }

    def _check_rate_limit(self) -> None:
        """Record a request and raise if the rate limit is exceeded."""
        if not self._rate_limiter.check():
            wait = self._rate_limiter.wait_time()
            raise CMSRateLimitError(
                f"Webflow rate limit exceeded ({self.DEFAULT_RATE_LIMIT} "
                f"req/{self.DEFAULT_RATE_WINDOW}s). Retry in {wait:.1f}s."
            )
        self._rate_limiter.record()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> Dict[str, Any]:
        """Validate the API token and retrieve site information.

        HTTP: GET {api_base}/sites/{site_id}
        Headers: Authorization: Bearer {api_token}
        Expected 200 response: JSON with ``displayName``, ``shortName``,
        ``customDomains``, etc.

        A 401 response indicates an invalid token.
        A 404 response indicates the site_id is wrong or the token lacks
        access to this site.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/sites/{self.site_id}"
        #   response = httpx.get(
        #       url,
        #       headers=self._auth_headers(),
        #       timeout=15,
        #   )
        #   if response.status_code == 401:
        #       raise CMSAuthError("Invalid Webflow API token")
        #   if response.status_code == 404:
        #       raise CMSConnectionError(
        #           f"Webflow site {self.site_id} not found or token lacks access"
        #       )
        #   response.raise_for_status()
        #   data = response.json()
        #   domains = data.get("customDomains", [])
        #   self._site_url = (
        #       f"https://{domains[0]['url']}" if domains
        #       else f"https://{data.get('shortName', '')}.webflow.io"
        #   )
        # ----------------------------------------------------------

        self._connected = True
        return {
            "connected": True,
            "platform": self.PLATFORM,
            "site_url": self._site_url,
            "capabilities": list(self.CAPABILITIES),
            "version": "v2",
        }

    def disconnect(self) -> None:
        """Release connection state and clear caches.

        The Webflow API is stateless. This resets internal state.
        """
        self._connected = False
        self._collections_cache.clear()

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def get_pages(
        self,
        page_type: str = "page",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List pages from the Webflow site.

        For static pages:
            HTTP: GET {api_base}/sites/{site_id}/pages
            Returns all static pages. Pagination via offset/limit params.

        For CMS collection items (post, product, collection):
            HTTP: GET {api_base}/sites/{site_id}/collections
            Then:  GET {api_base}/collections/{collection_id}/items
                   ?offset={offset}&limit={limit}

        ``page_type`` mapping:
        - ``"page"`` → static pages endpoint
        - ``"post"`` → CMS collection named "Blog Posts" or similar
        - ``"product"`` → CMS collection named "Products"
        - ``"collection"`` → all CMS collections listed
        - ``"landing_page"`` → static pages (filtered by folder if available)
        """
        self._check_rate_limit()

        if page_type == "page" or page_type == "landing_page":
            return self._get_static_pages(limit, offset, page_type)
        else:
            return self._get_collection_items(page_type, limit, offset)

    def _get_static_pages(
        self, limit: int, offset: int, page_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch static Webflow pages.

        HTTP: GET {api_base}/sites/{site_id}/pages
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/sites/{self.site_id}/pages"
        #   params = {"offset": offset, "limit": min(limit, 100)}
        #   response = httpx.get(
        #       url,
        #       headers=self._auth_headers(),
        #       params=params,
        #       timeout=30,
        #   )
        #   response.raise_for_status()
        #   data = response.json()
        #   items = data.get("pages", [])
        # ----------------------------------------------------------

        items: list = []  # populated from API response

        pages: List[Dict[str, Any]] = []
        for item in items:
            pages.append({
                "id": item.get("_id", ""),
                "title": item.get("title", ""),
                "slug": item.get("slug", ""),
                "url": f"{self._site_url}/{item.get('slug', '')}",
                "status": "publish" if not item.get("draft") else "draft",
                "page_type": page_type,
                "modified_date": item.get("lastUpdated", ""),
                "metadata": {
                    "seo_title": item.get("seoTitle", ""),
                    "seo_description": item.get("seoDescription", ""),
                },
            })
        return pages

    def _get_collection_items(
        self, page_type: str, limit: int, offset: int
    ) -> List[Dict[str, Any]]:
        """Fetch CMS collection items matching the requested page type.

        HTTP: GET {api_base}/sites/{site_id}/collections
        Then: GET {api_base}/collections/{collection_id}/items
        """
        self._check_rate_limit()

        # Map page_type to likely collection display names
        collection_name_hints = {
            "post": ["blog posts", "blog", "posts", "articles"],
            "product": ["products", "product"],
            "collection": [],  # return all collections
        }
        hints = collection_name_hints.get(page_type, [])

        # ----------------------------------------------------------
        # STUB: Fetch collections, then items
        #
        #   # Step 1: list collections
        #   url = f"{self.api_base}/sites/{self.site_id}/collections"
        #   response = httpx.get(url, headers=self._auth_headers(), timeout=30)
        #   response.raise_for_status()
        #   collections = response.json().get("collections", [])
        #
        #   # Step 2: find matching collection
        #   target_collection = None
        #   for coll in collections:
        #       name = coll.get("displayName", "").lower()
        #       if not hints or any(h in name for h in hints):
        #           target_collection = coll
        #           break
        #
        #   if not target_collection:
        #       return []
        #
        #   # Step 3: fetch items
        #   coll_id = target_collection["_id"]
        #   url = f"{self.api_base}/collections/{coll_id}/items"
        #   params = {"offset": offset, "limit": min(limit, 100)}
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), params=params, timeout=30,
        #   )
        #   response.raise_for_status()
        #   items = response.json().get("items", [])
        # ----------------------------------------------------------

        items: list = []  # populated from API response

        pages: List[Dict[str, Any]] = []
        for item in items:
            pages.append({
                "id": item.get("_id", ""),
                "title": item.get("name", ""),
                "slug": item.get("slug", ""),
                "url": f"{self._site_url}/{item.get('slug', '')}",
                "status": (
                    "publish"
                    if not item.get("_draft") and not item.get("_archived")
                    else "draft"
                ),
                "page_type": page_type,
                "modified_date": item.get("lastUpdated", item.get("updated-on", "")),
                "metadata": {},
            })
        return pages

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Fetch full content for a single static page or collection item.

        For static pages:
            HTTP: GET {api_base}/pages/{page_id}
            Returns page DOM structure.

        For collection items:
            HTTP: GET {api_base}/collections/{collection_id}/items/{page_id}
            Returns field data as structured JSON.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   # Try static pages first
        #   url = f"{self.api_base}/pages/{page_id}"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   if response.status_code == 404:
        #       # Try as collection item — need to search across collections
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   response.raise_for_status()
        #   data = response.json()
        # ----------------------------------------------------------

        data: Dict[str, Any] = {}  # populated from API response

        # Webflow pages have structured components
        content_html = data.get("html", "")
        sections = self._parse_sections(content_html, data)

        return {
            "id": data.get("_id", page_id),
            "title": data.get("title", data.get("name", "")),
            "slug": data.get("slug", ""),
            "url": f"{self._site_url}/{data.get('slug', '')}",
            "content_html": content_html,
            "content_raw": str(data),  # Webflow raw is the JSON structure
            "sections": sections,
            "metadata": self._extract_metadata(data),
            "status": "publish" if not data.get("draft") else "draft",
            "modified_date": data.get("lastUpdated", ""),
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
        """Update a section of a Webflow page or collection item field.

        For CMS collection items, ``section_id`` maps to a field slug.
        For static pages, Webflow's API has limited support for modifying
        page DOM nodes — this updates the node matching ``section_id``.

        HTTP: PATCH {api_base}/collections/{collection_id}/items/{page_id}
        Body (JSON): {"fieldData": {section_id: content}}

        Or for static pages:
        HTTP: PUT {api_base}/pages/{page_id}
        Body: DOM update payload

        Changes are staged. Call ``publish_site()`` to push live.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # Fetch current state for the diff
        current_page = self.get_page(page_id)
        previous_content = ""
        for section in current_page.get("sections", []):
            if section.get("id") == section_id:
                previous_content = section.get("content", "")
                break

        # ----------------------------------------------------------
        # STUB: HTTP PATCH (collection item)
        #
        #   url = f"{self.api_base}/collections/{collection_id}/items/{page_id}"
        #   body = {"fieldData": {section_id: content}}
        #   response = httpx.patch(
        #       url,
        #       headers=self._auth_headers(),
        #       json=body,
        #       timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   if response.status_code not in (200, 202):
        #       raise CMSUpdateError(
        #           f"Failed to update section {section_id}: {response.status_code}"
        #       )
        # ----------------------------------------------------------

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
        """Extract SEO metadata for a Webflow page.

        HTTP: GET {api_base}/pages/{page_id}
        Metadata is in the ``seoTitle``, ``seoDescription``, and
        ``openGraph`` fields of the response.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/pages/{page_id}"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   response.raise_for_status()
        #   data = response.json()
        # ----------------------------------------------------------

        data: Dict[str, Any] = {}  # populated from API response
        return self._extract_metadata(data)

    def update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Update SEO metadata for a Webflow page.

        HTTP: PUT {api_base}/pages/{page_id}
        Body (JSON): {"seoTitle": "...", "seoDescription": "...", "openGraph": {...}}

        Only fields present in ``meta`` are sent.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # Map Kai keys to Webflow API fields
        field_map = {
            "title": "seoTitle",
            "meta_description": "seoDescription",
            "og_title": "openGraphTitle",
            "og_description": "openGraphDescription",
            "og_image": "openGraphImage",
        }

        webflow_body: Dict[str, Any] = {}
        updated_fields: List[str] = []

        for kai_key, value in meta.items():
            if kai_key in field_map:
                webflow_body[field_map[kai_key]] = value
                updated_fields.append(kai_key)
            elif kai_key == "canonical_url":
                # Webflow doesn't have a direct canonical field — it is
                # inferred from the page URL. Log but skip.
                updated_fields.append(kai_key)

        # ----------------------------------------------------------
        # STUB: HTTP PUT
        #
        #   url = f"{self.api_base}/pages/{page_id}"
        #   response = httpx.put(
        #       url,
        #       headers=self._auth_headers(),
        #       json=webflow_body,
        #       timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   if response.status_code not in (200, 202):
        #       raise CMSUpdateError(
        #           f"Failed to update metadata for page {page_id}: "
        #           f"{response.status_code}"
        #       )
        # ----------------------------------------------------------

        return {
            "success": True,
            "page_id": str(page_id),
            "updated_fields": updated_fields,
        }

    # ------------------------------------------------------------------
    # Media / Assets
    # ------------------------------------------------------------------

    def get_media(
        self,
        limit: int = 50,
        offset: int = 0,
        media_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List assets uploaded to the Webflow site.

        HTTP: GET {api_base}/sites/{site_id}/assets
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/sites/{self.site_id}/assets"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   response.raise_for_status()
        #   all_assets = response.json().get("assets", [])
        #
        #   # Apply local pagination (Webflow may not support offset/limit)
        #   assets = all_assets[offset:offset + limit]
        # ----------------------------------------------------------

        assets: list = []  # populated from API response

        media_list: List[Dict[str, Any]] = []
        for asset in assets:
            item = self._normalize_asset(asset)
            if media_type and item["type"] != media_type:
                continue
            media_list.append(item)
        return media_list

    def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file to Webflow's asset manager.

        Webflow asset uploads are a two-step process:
        1. Request an upload URL:
           HTTP: POST {api_base}/sites/{site_id}/assets
           Body (JSON): {"fileName": "photo.jpg", "fileHash": "..."}
           Response: {"uploadUrl": "...", "uploadDetails": {...}}

        2. Upload the file to the returned S3 presigned URL:
           HTTP: POST {uploadUrl}
           Body: multipart/form-data with fields from uploadDetails + file

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        filename = os.path.basename(file_path)
        media_title = title or os.path.splitext(filename)[0]

        # ----------------------------------------------------------
        # STUB: Two-step upload
        #
        #   # Step 1: Get upload URL
        #   url = f"{self.api_base}/sites/{self.site_id}/assets"
        #   body = {"fileName": filename, "fileHash": "<md5 hash>"}
        #   response = httpx.post(
        #       url, headers=self._auth_headers(), json=body, timeout=30,
        #   )
        #   if response.status_code not in (200, 201):
        #       raise CMSUpdateError(f"Upload init failed: {response.status_code}")
        #   upload_data = response.json()
        #   upload_url = upload_data["uploadUrl"]
        #   upload_details = upload_data.get("uploadDetails", {})
        #
        #   # Step 2: Upload file to S3
        #   with open(file_path, "rb") as fh:
        #       files = {"file": (filename, fh)}
        #       data = upload_details
        #       response = httpx.post(upload_url, data=data, files=files, timeout=120)
        #   if response.status_code not in (200, 201, 204):
        #       raise CMSUpdateError(f"File upload failed: {response.status_code}")
        #
        #   # Step 3: Optionally update alt text
        #   asset_id = upload_data.get("_id", "")
        #   if alt_text:
        #       httpx.put(
        #           f"{self.api_base}/assets/{asset_id}",
        #           headers=self._auth_headers(),
        #           json={"displayName": media_title, "altText": alt_text},
        #           timeout=15,
        #       )
        # ----------------------------------------------------------

        return {
            "success": True,
            "media_id": "",  # populated from API response
            "url": "",  # populated from API response
            "title": media_title,
        }

    # ------------------------------------------------------------------
    # Webflow-specific: publish
    # ------------------------------------------------------------------

    def publish_site(self, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """Publish staged changes to the live site.

        HTTP: POST {api_base}/sites/{site_id}/publish
        Body (JSON): {"domains": ["example.com"]}

        This is a Webflow-specific operation not part of the base
        CMSConnector interface. Changes made via update_page_section or
        update_metadata are staged until this method is called.

        Parameters
        ----------
        domains : list of str or None
            Domains to publish to. If None, publishes to all configured
            domains.

        Returns
        -------
        dict
            - ``success`` (bool)
            - ``queued`` (bool): True if the publish was queued

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP POST
        #
        #   url = f"{self.api_base}/sites/{self.site_id}/publish"
        #   body: Dict[str, Any] = {}
        #   if domains:
        #       body["domains"] = domains
        #   response = httpx.post(
        #       url, headers=self._auth_headers(), json=body, timeout=60,
        #   )
        #   if response.status_code not in (200, 202):
        #       raise CMSUpdateError(
        #           f"Publish failed: {response.status_code}"
        #       )
        #   data = response.json()
        # ----------------------------------------------------------

        return {
            "success": True,
            "queued": True,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_asset(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Webflow asset object to the Kai media format."""
        content_type = asset.get("contentType", asset.get("mimeType", ""))
        if content_type.startswith("image/"):
            media_type = "image"
        elif content_type.startswith("video/"):
            media_type = "video"
        else:
            media_type = "document"

        width = asset.get("width")
        height = asset.get("height")
        dimensions = f"{width}x{height}" if width and height else None

        return {
            "id": asset.get("_id", ""),
            "title": asset.get("displayName", asset.get("fileName", "")),
            "url": asset.get("url", asset.get("hostedUrl", "")),
            "type": media_type,
            "mime_type": content_type,
            "size_bytes": asset.get("size", asset.get("fileSize", 0)),
            "dimensions": dimensions,
            "alt_text": asset.get("altText", None) or None,
            "uploaded_date": asset.get("createdOn", asset.get("uploadedOn", "")),
        }

    @staticmethod
    def _extract_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SEO/OG metadata from a Webflow page or collection item."""
        og = data.get("openGraph", {})
        return {
            "title": data.get("seoTitle", data.get("title", "")),
            "meta_description": data.get("seoDescription", ""),
            "og_title": og.get("title", data.get("openGraphTitle", "")),
            "og_description": og.get("description", data.get("openGraphDescription", "")),
            "og_image": og.get("image", data.get("openGraphImage", "")),
            "canonical_url": data.get("canonicalUrl", ""),
            "schema_markup": [],  # Webflow does not expose schema via API
            "custom_fields": {
                k: v for k, v in data.items()
                if k not in {
                    "_id", "title", "slug", "name", "html", "draft",
                    "seoTitle", "seoDescription", "openGraph",
                    "openGraphTitle", "openGraphDescription", "openGraphImage",
                    "canonicalUrl", "lastUpdated", "createdOn",
                }
            },
        }

    @staticmethod
    def _parse_sections(
        html: str, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Parse Webflow page content into logical sections.

        Webflow pages have structured components. When HTML is available,
        sections are split by ``<section>`` tags or ``<div>`` with
        class names suggesting layout roles (hero, features, cta, etc.).

        For CMS collection items, fields are mapped directly to sections.
        """
        sections: List[Dict[str, Any]] = []

        # If the data contains structured field data (collection item),
        # map each rich-text field as a section
        field_data = data.get("fieldData", {})
        if field_data:
            section_idx = 0
            for field_name, field_value in field_data.items():
                if isinstance(field_value, str) and len(field_value) > 20:
                    sections.append({
                        "id": field_name,
                        "type": "field",
                        "heading": field_name.replace("-", " ").replace("_", " ").title(),
                        "content": field_value,
                    })
                    section_idx += 1
            if sections:
                return sections

        if not html or not html.strip():
            return []

        # Try splitting by <section> tags
        section_pattern = re.compile(
            r'<section[^>]*>(.*?)</section>', re.DOTALL | re.IGNORECASE
        )
        section_matches = section_pattern.findall(html)

        if section_matches:
            for idx, content in enumerate(section_matches):
                # Try to infer section type from class names
                section_type = "body"
                if idx == 0:
                    section_type = "hero"
                elif idx == len(section_matches) - 1:
                    section_type = "footer"

                # Extract heading if present
                heading_match = re.search(
                    r'<h[1-3][^>]*>(.*?)</h[1-3]>', content, re.DOTALL | re.IGNORECASE
                )
                heading = re.sub(r'<[^>]+>', '', heading_match.group(1)).strip() if heading_match else ""

                sections.append({
                    "id": f"section_{idx}",
                    "type": section_type,
                    "heading": heading,
                    "content": content.strip(),
                })
            return sections

        # Fallback: split by heading tags
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
            heading_text = re.sub(r'<[^>]+>', '', heading_html).strip()

            sections.append({
                "id": f"section_{section_idx}",
                "type": "body",
                "heading": heading_text,
                "content": heading_html + "\n" + body if body else heading_html,
            })
            section_idx += 1

        if not sections and html.strip():
            sections.append({
                "id": "section_0",
                "type": "body",
                "heading": "",
                "content": html.strip(),
            })

        return sections

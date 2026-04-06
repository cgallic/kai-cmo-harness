"""Shopify CMS connector — interfaces with the Shopify Admin REST API.

This connector communicates with Shopify stores using the Admin REST
API. It supports reading/writing pages, products, blog articles, and
media files (theme assets). Authentication uses the
``X-Shopify-Access-Token`` header with a Shopify Admin API access token.

Shopify's content model includes pages (static content), products
(ecommerce listings), and blog articles. Theme assets are accessed
through the Themes API. Metafields provide custom field storage.

No external HTTP libraries are imported at module level. All HTTP calls
are documented as stubs with comments describing the real request.

Shopify Admin API reference:
    https://shopify.dev/docs/api/admin-rest
"""

from __future__ import annotations

import json
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


class ShopifyConnector(CMSConnector):
    """CMS connector for Shopify stores using the Admin REST API.

    Config
    ------
    The ``config`` dict must contain:

    - ``shop_url`` (str): Shopify store URL, e.g.
      ``"mystore.myshopify.com"``. Do not include ``https://`` or
      trailing slashes.
    - ``access_token`` (str): Shopify Admin API access token. Create one
      at Shopify Admin > Settings > Apps and sales channels > Develop
      apps > API credentials.
    - ``api_version`` (str, optional): API version string. Default
      ``"2024-01"``.
    - ``api_base`` (str, optional): Computed from ``shop_url`` and
      ``api_version`` if not provided. Format:
      ``https://{shop_url}/admin/api/{api_version}``.

    Example::

        connector = ShopifyConnector({
            "shop_url": "cool-brand.myshopify.com",
            "access_token": "shpat_xxxxxxxxxxxxxxxxxxxx",
        })
        info = connector.connect()
    """

    PLATFORM = "shopify"

    # Shopify: 40 requests per app per store per minute (leaky bucket)
    # The actual limit is 2 req/s with a 40-request bucket, but we
    # model it as 40/min for simplicity.
    DEFAULT_RATE_LIMIT = 40
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

        self.shop_url: str = config["shop_url"].rstrip("/")
        self.access_token: str = config["access_token"]
        self.api_version: str = config.get("api_version", "2024-01")
        self.api_base: str = config.get(
            "api_base",
            f"https://{self.shop_url}/admin/api/{self.api_version}",
        )

        self._rate_limiter = RateLimiter(
            max_requests=self.DEFAULT_RATE_LIMIT,
            window_seconds=self.DEFAULT_RATE_WINDOW,
        )
        self._shop_name: str = ""
        self._primary_domain: str = ""
        self._active_theme_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        """Build authentication headers with the Shopify access token."""
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _check_rate_limit(self) -> None:
        """Record a request and raise if the rate limit is exceeded."""
        if not self._rate_limiter.check():
            wait = self._rate_limiter.wait_time()
            raise CMSRateLimitError(
                f"Shopify rate limit exceeded ({self.DEFAULT_RATE_LIMIT} "
                f"req/{self.DEFAULT_RATE_WINDOW}s). Retry in {wait:.1f}s."
            )
        self._rate_limiter.record()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> Dict[str, Any]:
        """Validate the access token by requesting shop info.

        HTTP: GET {api_base}/shop.json
        Headers: X-Shopify-Access-Token: {access_token}
        Expected 200 response: JSON with ``shop`` object containing
        ``name``, ``domain``, ``myshopify_domain``, etc.

        A 401 response indicates an invalid or revoked token.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/shop.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=15,
        #   )
        #   if response.status_code == 401:
        #       raise CMSAuthError("Invalid Shopify access token")
        #   if response.status_code != 200:
        #       raise CMSConnectionError(
        #           f"Shopify API returned {response.status_code}"
        #       )
        #   data = response.json().get("shop", {})
        #   self._shop_name = data.get("name", "")
        #   self._primary_domain = data.get("domain", self.shop_url)
        # ----------------------------------------------------------

        self._connected = True
        return {
            "connected": True,
            "platform": self.PLATFORM,
            "site_url": f"https://{self._primary_domain or self.shop_url}",
            "capabilities": list(self.CAPABILITIES),
            "version": self.api_version,
        }

    def disconnect(self) -> None:
        """Release connection state.

        The Shopify Admin API is stateless. This resets internal state.
        """
        self._connected = False
        self._active_theme_id = None

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def get_pages(
        self,
        page_type: str = "page",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List pages, products, or blog articles.

        ``page_type`` mapping:
        - ``"page"`` → GET {api_base}/pages.json?limit={limit}
        - ``"post"`` → GET {api_base}/blogs.json → GET /blogs/{id}/articles.json
        - ``"product"`` → GET {api_base}/products.json?limit={limit}
        - ``"collection"`` → GET {api_base}/custom_collections.json
        - ``"landing_page"`` → GET {api_base}/pages.json (filtered)

        Shopify uses cursor-based pagination (``page_info``), not offset.
        For this stub, ``offset`` is documented but the real implementation
        would use ``since_id`` or Link header pagination.
        """
        self._check_rate_limit()

        endpoint_map = {
            "page": "pages.json",
            "product": "products.json",
            "collection": "custom_collections.json",
            "landing_page": "pages.json",
        }

        if page_type == "post":
            return self._get_blog_articles(limit)

        endpoint = endpoint_map.get(page_type, "pages.json")

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/{endpoint}"
        #   params = {"limit": min(limit, 250)}  # Shopify max 250
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), params=params, timeout=30,
        #   )
        #   response.raise_for_status()
        #   data = response.json()
        #
        #   # Extract the resource list key
        #   resource_key = endpoint.replace(".json", "")
        #   items = data.get(resource_key, [])
        # ----------------------------------------------------------

        items: list = []  # populated from API response

        pages: List[Dict[str, Any]] = []
        for item in items:
            pages.append(self._normalize_page_list_item(item, page_type))
        return pages

    def _get_blog_articles(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch blog articles across all blogs.

        Step 1: GET {api_base}/blogs.json → list of blogs
        Step 2: For each blog, GET {api_base}/blogs/{blog_id}/articles.json
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET (blogs, then articles)
        #
        #   # Step 1: Get blogs
        #   url = f"{self.api_base}/blogs.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   response.raise_for_status()
        #   blogs = response.json().get("blogs", [])
        #
        #   all_articles = []
        #   for blog in blogs:
        #       blog_id = blog["id"]
        #       url = f"{self.api_base}/blogs/{blog_id}/articles.json"
        #       params = {"limit": min(limit, 250)}
        #       response = httpx.get(
        #           url, headers=self._auth_headers(), params=params, timeout=30,
        #       )
        #       response.raise_for_status()
        #       articles = response.json().get("articles", [])
        #       all_articles.extend(articles)
        # ----------------------------------------------------------

        articles: list = []  # populated from API response

        pages: List[Dict[str, Any]] = []
        for item in articles:
            pages.append(self._normalize_page_list_item(item, "post"))
        return pages

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Fetch a single page by ID.

        HTTP: GET {api_base}/pages/{page_id}.json
        For products: GET {api_base}/products/{page_id}.json

        The response includes ``body_html`` (rendered HTML) as the
        primary content field.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET
        #
        #   url = f"{self.api_base}/pages/{page_id}.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   response.raise_for_status()
        #   data = response.json().get("page", {})
        # ----------------------------------------------------------

        data: Dict[str, Any] = {}  # populated from API response

        body_html = data.get("body_html", "")
        sections = self._parse_sections(body_html)
        handle = data.get("handle", "")
        domain = self._primary_domain or self.shop_url

        return {
            "id": str(data.get("id", page_id)),
            "title": data.get("title", ""),
            "slug": handle,
            "url": f"https://{domain}/pages/{handle}" if handle else "",
            "content_html": body_html,
            "content_raw": body_html,  # Shopify pages use raw HTML
            "sections": sections,
            "metadata": self._extract_metadata_from_page(data),
            "status": (
                "publish" if data.get("published_at") else "draft"
            ),
            "modified_date": data.get("updated_at", ""),
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
        """Update a section of a Shopify page.

        Shopify pages store content as a single ``body_html`` field.
        This method fetches the current HTML, locates the target section,
        replaces it, and writes the full HTML back.

        HTTP: PUT {api_base}/pages/{page_id}.json
        Body (JSON): {"page": {"body_html": "<updated HTML>"}}

        Note: Shopify Liquid templates define sections at the theme level.
        This method operates on the page ``body_html`` content, not
        theme sections. For theme section updates, use the Assets API.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        # Fetch current content
        current_page = self.get_page(page_id)
        current_html = current_page["content_html"]

        previous_content = ""
        sections = current_page.get("sections", [])
        for section in sections:
            if section.get("id") == section_id:
                previous_content = section.get("content", "")
                break

        if not previous_content and sections:
            try:
                idx = int(section_id.replace("section_", ""))
                if 0 <= idx < len(sections):
                    previous_content = sections[idx].get("content", "")
            except (ValueError, IndexError):
                pass

        updated_html = current_html
        if previous_content:
            updated_html = current_html.replace(previous_content, content, 1)

        # ----------------------------------------------------------
        # STUB: HTTP PUT
        #
        #   url = f"{self.api_base}/pages/{page_id}.json"
        #   body = {"page": {"body_html": updated_html}}
        #   response = httpx.put(
        #       url,
        #       headers=self._auth_headers(),
        #       json=body,
        #       timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   if response.status_code != 200:
        #       raise CMSUpdateError(
        #           f"Failed to update page {page_id}: {response.status_code}"
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
        """Extract SEO metadata for a Shopify page.

        Shopify stores SEO data in the page object itself (``title``,
        ``meta_description``) and in metafields for Open Graph overrides.

        HTTP: GET {api_base}/pages/{page_id}.json
        HTTP: GET {api_base}/pages/{page_id}/metafields.json
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET (page + metafields)
        #
        #   # Get page data
        #   url = f"{self.api_base}/pages/{page_id}.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   if response.status_code == 404:
        #       raise CMSNotFoundError(f"Page {page_id} not found")
        #   response.raise_for_status()
        #   page_data = response.json().get("page", {})
        #
        #   # Get metafields
        #   url = f"{self.api_base}/pages/{page_id}/metafields.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   response.raise_for_status()
        #   metafields = response.json().get("metafields", [])
        # ----------------------------------------------------------

        page_data: Dict[str, Any] = {}  # populated from API response
        return self._extract_metadata_from_page(page_data)

    def update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Update SEO metadata for a Shopify page.

        Updates the page's ``title`` and ``metafields_global_description_tag``
        via the Pages API, and writes Open Graph overrides as metafields.

        HTTP: PUT {api_base}/pages/{page_id}.json
        Body (JSON): {"page": {"title": "...", "metafields_global_description_tag": "..."}}

        For metafields:
        HTTP: POST {api_base}/pages/{page_id}/metafields.json
        Body (JSON): {"metafield": {"namespace": "seo", "key": "og_title",
                      "value": "...", "type": "single_line_text_field"}}

        Only fields present in ``meta`` are updated.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        page_body: Dict[str, Any] = {}
        metafields_to_set: List[Dict[str, Any]] = []
        updated_fields: List[str] = []

        for kai_key, value in meta.items():
            if kai_key == "title":
                page_body["title"] = value
                updated_fields.append("title")
            elif kai_key == "meta_description":
                page_body["metafields_global_description_tag"] = value
                updated_fields.append("meta_description")
            elif kai_key in ("og_title", "og_description", "og_image", "canonical_url"):
                metafields_to_set.append({
                    "namespace": "seo",
                    "key": kai_key,
                    "value": value,
                    "type": "single_line_text_field",
                })
                updated_fields.append(kai_key)

        # ----------------------------------------------------------
        # STUB: HTTP PUT (page fields)
        #
        #   if page_body:
        #       url = f"{self.api_base}/pages/{page_id}.json"
        #       response = httpx.put(
        #           url,
        #           headers=self._auth_headers(),
        #           json={"page": page_body},
        #           timeout=30,
        #       )
        #       if response.status_code == 404:
        #           raise CMSNotFoundError(f"Page {page_id} not found")
        #       if response.status_code != 200:
        #           raise CMSUpdateError(
        #               f"Failed to update page {page_id}: {response.status_code}"
        #           )
        #
        #   # Write metafields
        #   for mf in metafields_to_set:
        #       url = f"{self.api_base}/pages/{page_id}/metafields.json"
        #       response = httpx.post(
        #           url,
        #           headers=self._auth_headers(),
        #           json={"metafield": mf},
        #           timeout=15,
        #       )
        #       if response.status_code not in (200, 201):
        #           raise CMSUpdateError(
        #               f"Metafield write failed for {mf['key']}: "
        #               f"{response.status_code}"
        #           )
        # ----------------------------------------------------------

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
        """List media from the Shopify Files API and theme assets.

        Primary media:
            HTTP: GET {api_base}/themes/{theme_id}/assets.json
            Returns theme assets (images, scripts, styles).

        Shopify also has a Files API (GraphQL-only in newer versions).
        This stub documents the REST-accessible theme assets approach.
        """
        self._check_rate_limit()

        # ----------------------------------------------------------
        # STUB: HTTP GET (theme assets)
        #
        #   # First, get the active theme ID if not cached
        #   if not self._active_theme_id:
        #       url = f"{self.api_base}/themes.json"
        #       response = httpx.get(
        #           url, headers=self._auth_headers(), timeout=30,
        #       )
        #       response.raise_for_status()
        #       themes = response.json().get("themes", [])
        #       for theme in themes:
        #           if theme.get("role") == "main":
        #               self._active_theme_id = str(theme["id"])
        #               break
        #
        #   # Get theme assets
        #   url = f"{self.api_base}/themes/{self._active_theme_id}/assets.json"
        #   response = httpx.get(
        #       url, headers=self._auth_headers(), timeout=30,
        #   )
        #   response.raise_for_status()
        #   all_assets = response.json().get("assets", [])
        #
        #   # Filter to media files
        #   media_extensions = {
        #       "image": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"},
        #       "video": {".mp4", ".webm", ".mov"},
        #       "document": {".pdf", ".doc", ".docx"},
        #   }
        # ----------------------------------------------------------

        assets: list = []  # populated from API response

        media_list: List[Dict[str, Any]] = []
        for asset in assets:
            item = self._normalize_asset(asset)
            if media_type and item["type"] != media_type:
                continue
            media_list.append(item)

        # Apply pagination locally since theme assets return all at once
        return media_list[offset:offset + limit]

    def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file as a theme asset.

        HTTP: PUT {api_base}/themes/{theme_id}/assets.json
        Body (JSON): {
            "asset": {
                "key": "assets/{filename}",
                "attachment": "<base64-encoded file>"
            }
        }

        For product images, use the Product Images API instead:
        HTTP: POST {api_base}/products/{product_id}/images.json

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()
        self._check_rate_limit()

        filename = os.path.basename(file_path)
        media_title = title or os.path.splitext(filename)[0]
        asset_key = f"assets/{filename}"

        # ----------------------------------------------------------
        # STUB: HTTP PUT (theme asset upload)
        #
        #   import base64
        #
        #   if not self._active_theme_id:
        #       # Fetch active theme (same pattern as get_media)
        #       ...
        #
        #   with open(file_path, "rb") as fh:
        #       encoded = base64.b64encode(fh.read()).decode()
        #
        #   url = f"{self.api_base}/themes/{self._active_theme_id}/assets.json"
        #   body = {
        #       "asset": {
        #           "key": asset_key,
        #           "attachment": encoded,
        #       }
        #   }
        #   response = httpx.put(
        #       url,
        #       headers=self._auth_headers(),
        #       json=body,
        #       timeout=120,
        #   )
        #   if response.status_code not in (200, 201):
        #       raise CMSUpdateError(
        #           f"Asset upload failed: {response.status_code}"
        #       )
        #   data = response.json().get("asset", {})
        #   asset_url = data.get("public_url", "")
        # ----------------------------------------------------------

        return {
            "success": True,
            "media_id": asset_key,
            "url": "",  # populated from API response (public_url)
            "title": media_title,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_page_list_item(
        self, item: Dict[str, Any], page_type: str
    ) -> Dict[str, Any]:
        """Convert a Shopify page/product/article object to the Kai page list format."""
        handle = item.get("handle", "")
        domain = self._primary_domain or self.shop_url

        # Build URL based on page type
        if page_type == "product":
            url = f"https://{domain}/products/{handle}"
        elif page_type == "post":
            url = f"https://{domain}/blogs/{item.get('blog_id', 'news')}/{handle}"
        elif page_type == "collection":
            url = f"https://{domain}/collections/{handle}"
        else:
            url = f"https://{domain}/pages/{handle}"

        return {
            "id": str(item.get("id", "")),
            "title": item.get("title", ""),
            "slug": handle,
            "url": url,
            "status": "publish" if item.get("published_at") else "draft",
            "page_type": page_type,
            "modified_date": item.get("updated_at", ""),
            "metadata": {
                "tags": item.get("tags", ""),
                "vendor": item.get("vendor", ""),
            },
        }

    def _normalize_asset(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Shopify theme asset to the Kai media format."""
        key = asset.get("key", "")
        content_type = asset.get("content_type", "")

        # Infer type from key extension
        ext = os.path.splitext(key)[1].lower()
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico"}
        video_exts = {".mp4", ".webm", ".mov"}

        if ext in image_exts or content_type.startswith("image/"):
            media_type = "image"
        elif ext in video_exts or content_type.startswith("video/"):
            media_type = "video"
        else:
            media_type = "document"

        return {
            "id": key,
            "title": os.path.basename(key),
            "url": asset.get("public_url", ""),
            "type": media_type,
            "mime_type": content_type,
            "size_bytes": asset.get("size", 0),
            "dimensions": None,  # Theme assets API doesn't return dimensions
            "alt_text": None,  # Not available in theme assets
            "uploaded_date": asset.get("updated_at", asset.get("created_at", "")),
        }

    @staticmethod
    def _extract_metadata_from_page(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SEO metadata from a Shopify page/product response."""
        # Shopify stores SEO fields on the resource itself
        metafields = {}
        for mf in data.get("metafields", []):
            if mf.get("namespace") == "seo":
                metafields[mf.get("key", "")] = mf.get("value", "")

        # For products, the image is the featured image
        featured_image = ""
        images = data.get("images", []) or data.get("image", None)
        if isinstance(images, list) and images:
            featured_image = images[0].get("src", "")
        elif isinstance(images, dict):
            featured_image = images.get("src", "")

        handle = data.get("handle", "")
        return {
            "title": data.get("title", ""),
            "meta_description": data.get(
                "metafields_global_description_tag",
                data.get("meta_description", ""),
            ),
            "og_title": metafields.get("og_title", data.get("title", "")),
            "og_description": metafields.get(
                "og_description",
                data.get("metafields_global_description_tag", ""),
            ),
            "og_image": metafields.get("og_image", featured_image),
            "canonical_url": metafields.get("canonical_url", ""),
            "schema_markup": [],  # Shopify handles schema via theme Liquid
            "custom_fields": {
                "tags": data.get("tags", ""),
                "vendor": data.get("vendor", ""),
                "product_type": data.get("product_type", ""),
                "template_suffix": data.get("template_suffix", ""),
            },
        }

    @staticmethod
    def _parse_sections(html: str) -> List[Dict[str, Any]]:
        """Parse Shopify page body_html into logical sections.

        Shopify page content is typically simpler than WordPress —
        often just HTML without Gutenberg-style block markers. Sections
        are split by heading tags or ``<section>``/``<div>`` elements.

        Note: Shopify Liquid theme sections are separate from page
        content sections. This method parses the ``body_html`` field only.
        """
        if not html or not html.strip():
            return []

        sections: List[Dict[str, Any]] = []

        # Try splitting by <section> tags first
        section_pattern = re.compile(
            r'<section[^>]*>(.*?)</section>', re.DOTALL | re.IGNORECASE
        )
        section_matches = section_pattern.findall(html)

        if section_matches:
            for idx, content in enumerate(section_matches):
                heading_match = re.search(
                    r'<h[1-3][^>]*>(.*?)</h[1-3]>', content,
                    re.DOTALL | re.IGNORECASE,
                )
                heading = (
                    re.sub(r'<[^>]+>', '', heading_match.group(1)).strip()
                    if heading_match else ""
                )
                section_type = "hero" if idx == 0 else "body"

                sections.append({
                    "id": f"section_{idx}",
                    "type": section_type,
                    "heading": heading,
                    "content": content.strip(),
                })
            return sections

        # Fall back to heading-based splitting
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

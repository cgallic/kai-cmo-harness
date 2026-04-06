# Task 033: Build CMS connector layer

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

Kai's website operations system needs to read and write website content across different CMS platforms. A local plumber's site might run on WordPress, an ecommerce brand might use Shopify, a design agency might use Webflow, and some businesses have static HTML sites. The CMS connector layer provides a uniform interface for all website operations — reading pages, updating content sections, managing metadata, and handling media — regardless of the underlying platform.

This is a foundational module with no dependencies. Every website action (update CTA, rewrite hero section, add trust block, fix tracking) flows through a CMS connector. The connectors must be production-aware: they handle authentication, rate limiting, error recovery, and support read-only mode for safe auditing without accidental writes.

## Scope

Build the `kai/connectors/cms/` package with an abstract base class and four concrete connector implementations: WordPress, Webflow, Shopify, and static site. Each connector implements the same interface but uses the platform's native API.

## Detailed Requirements

### File: `kai/connectors/__init__.py`
- Package init, empty or with a docstring

### File: `kai/connectors/cms/__init__.py`
- Package init that imports and re-exports the base class and all connectors
- Include `__all__` listing

### File: `kai/connectors/cms/base.py`

**Abstract class: CMSConnector**

Use Python's `abc` module. This is the interface all connectors must implement.

```python
from abc import ABC, abstractmethod
```

Constructor:
- `__init__(self, config: Dict[str, Any], read_only: bool = False)`
- `config` contains platform-specific auth credentials and settings
- `read_only` prevents any write operations (raises error if write attempted in read-only mode)

Abstract methods (all async-ready — define as regular methods with docstrings noting they should be async in production):

1. `connect(self) -> Dict[str, Any]`
   - Establish connection to the CMS
   - Validate credentials
   - Return connection info: `{"connected": bool, "platform": str, "site_url": str, "capabilities": List[str], "version": Optional[str]}`
   - Capabilities: ["read_pages", "write_pages", "read_media", "write_media", "read_menus", "write_menus", "read_metadata", "write_metadata", "custom_fields"]

2. `disconnect(self) -> None`
   - Clean up connection resources

3. `get_pages(self, page_type: str = "page", limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]`
   - Return list of pages/posts
   - page_type: "page", "post", "product", "collection", "landing_page"
   - Each page dict: `{"id": str, "title": str, "slug": str, "url": str, "status": str, "page_type": str, "modified_date": str, "metadata": {}}`

4. `get_page(self, page_id: str) -> Dict[str, Any]`
   - Return full page content
   - Output: `{"id": str, "title": str, "slug": str, "url": str, "content_html": str, "content_raw": str, "sections": List[Dict], "metadata": Dict, "status": str, "modified_date": str}`
   - `sections`: attempt to parse page into logical sections (hero, body, sidebar, footer, etc.)

5. `update_page_section(self, page_id: str, section_id: str, content: str, content_type: str = "html") -> Dict[str, Any]`
   - Update a specific section of a page
   - content_type: "html", "text", "json", "markdown"
   - If `read_only`, raise `ReadOnlyError`
   - Return: `{"success": bool, "page_id": str, "section_id": str, "previous_content": str, "new_content": str}`

6. `get_metadata(self, page_id: str) -> Dict[str, Any]`
   - Return page metadata: title tag, meta description, og tags, schema markup, canonical URL
   - Output: `{"title": str, "meta_description": str, "og_title": str, "og_description": str, "og_image": str, "canonical_url": str, "schema_markup": List[Dict], "custom_fields": Dict}`

7. `update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]`
   - Update page metadata fields
   - Only update fields present in the `meta` dict (do not clear unmentioned fields)
   - If `read_only`, raise `ReadOnlyError`
   - Return: `{"success": bool, "page_id": str, "updated_fields": List[str]}`

8. `get_media(self, limit: int = 50, offset: int = 0, media_type: Optional[str] = None) -> List[Dict[str, Any]]`
   - Return list of media items
   - media_type filter: "image", "video", "document", None (all)
   - Each media dict: `{"id": str, "title": str, "url": str, "type": str, "mime_type": str, "size_bytes": int, "dimensions": Optional[str], "alt_text": Optional[str], "uploaded_date": str}`

9. `upload_media(self, file_path: str, title: Optional[str] = None, alt_text: Optional[str] = None) -> Dict[str, Any]`
   - Upload a media file to the CMS
   - If `read_only`, raise `ReadOnlyError`
   - Return: `{"success": bool, "media_id": str, "url": str, "title": str}`

Non-abstract utility methods:

10. `validate_connection(self) -> Dict[str, Any]`
    - Call `connect()` and return a health check result
    - Return: `{"healthy": bool, "platform": str, "error": Optional[str], "capabilities": List[str]}`

11. `snapshot_page(self, page_id: str) -> Dict[str, Any]`
    - Get current full state of a page (content + metadata)
    - Used before making changes for rollback
    - Return: `{"page_id": str, "timestamp": str, "content": Dict, "metadata": Dict}`

**Custom exceptions (define in base.py):**
- `CMSConnectionError(Exception)` — connection failure
- `CMSAuthError(Exception)` — authentication failure
- `CMSNotFoundError(Exception)` — page/resource not found
- `CMSRateLimitError(Exception)` — rate limit exceeded
- `ReadOnlyError(Exception)` — write attempted in read-only mode
- `CMSUpdateError(Exception)` — update failed

**Rate limiter (simple implementation):**
- `RateLimiter` class with `__init__(self, max_requests: int = 10, window_seconds: int = 60)`
- `check(self) -> bool` — return True if request is allowed, False if rate limited
- `wait_time(self) -> float` — return seconds until next allowed request
- Uses a simple sliding window counter (list of timestamps)

### File: `kai/connectors/cms/wordpress.py`

**Class: WordPressConnector(CMSConnector)**

Config requirements:
```python
{
    "site_url": str,          # WordPress site URL (e.g., "https://example.com")
    "username": str,          # WP username or application password username
    "password": str,          # Application password (NOT user password)
    "api_base": str,          # Default: "/wp-json/wp/v2"
    "auth_type": str,         # "application_password" (default) or "jwt"
    "verify_ssl": bool,       # Default True
}
```

Implementation notes (document as docstrings and comments, do not actually make HTTP calls):
- API base: `{site_url}/wp-json/wp/v2/`
- Auth: Basic auth with application passwords, or JWT if configured
- Pages endpoint: `GET /pages`, `GET /pages/{id}`, `POST /pages/{id}`
- Posts endpoint: `GET /posts`, `GET /posts/{id}`, `POST /posts/{id}`
- Media endpoint: `GET /media`, `POST /media`
- Custom fields via ACF: `GET /pages/{id}?_fields=acf` if ACF REST API is enabled
- Menus: `GET /menus` (requires menu endpoint plugin or custom endpoint)
- Rate limiting: WordPress REST API typically allows 100 requests/minute
- Section parsing: attempt to split page content by `<!-- wp:heading -->` or `<h2>` tags
- Metadata: use Yoast SEO fields if available (`yoast_head_json`), otherwise raw meta

Implement all abstract methods with WordPress-specific logic:
- `connect()`: make a test request to `{site_url}/wp-json/wp/v2/` and verify response
- `get_pages()`: `GET /pages?per_page={limit}&offset={offset}&status=publish`
- `get_page()`: `GET /pages/{id}?_embed` (embed gets featured image, author)
- `update_page_section()`: `POST /pages/{id}` with content update
- `get_metadata()`: extract from Yoast SEO fields or raw `<head>` parsing
- `update_metadata()`: `POST /pages/{id}` with meta field updates
- `get_media()`: `GET /media?per_page={limit}&offset={offset}`
- `upload_media()`: `POST /media` with multipart file upload

Mark all HTTP calls as stubs — use comments like `# HTTP: GET {url}` to document what the real implementation would do. Define the request/response mapping clearly.

### File: `kai/connectors/cms/webflow.py`

**Class: WebflowConnector(CMSConnector)**

Config requirements:
```python
{
    "api_token": str,         # Webflow API v2 bearer token
    "site_id": str,           # Webflow site ID
    "api_base": str,          # Default: "https://api.webflow.com/v2"
}
```

Implementation notes:
- Webflow API v2: uses bearer token auth
- Collections: `GET /sites/{site_id}/collections` — content collections
- Items: `GET /collections/{collection_id}/items` — items in a collection
- Pages: `GET /sites/{site_id}/pages` — static pages
- Assets: `GET /sites/{site_id}/assets` — uploaded assets
- Publishing: changes require `POST /sites/{site_id}/publish` to go live
- Rate limiting: 60 requests/minute for Webflow API v2
- Section parsing: Webflow pages have structured components, map to sections

Implement all abstract methods with Webflow-specific logic (as stubs with clear HTTP documentation).

### File: `kai/connectors/cms/shopify.py`

**Class: ShopifyConnector(CMSConnector)**

Config requirements:
```python
{
    "shop_url": str,          # Shopify store URL (e.g., "mystore.myshopify.com")
    "access_token": str,      # Shopify Admin API access token
    "api_version": str,       # Default: "2024-01"
    "api_base": str,          # Default: "https://{shop_url}/admin/api/{api_version}"
}
```

Implementation notes:
- Shopify Admin API: uses X-Shopify-Access-Token header
- Pages: `GET /pages.json`, `GET /pages/{id}.json`, `PUT /pages/{id}.json`
- Products: `GET /products.json`, `GET /products/{id}.json`
- Blogs/articles: `GET /blogs.json`, `GET /blogs/{id}/articles.json`
- Assets/themes: `GET /themes.json`, `GET /themes/{id}/assets.json`
- Metafields: `GET /pages/{id}/metafields.json`, `POST /pages/{id}/metafields.json`
- Rate limiting: 40 requests per app per store per minute (leaky bucket)
- Section parsing: Shopify Liquid templates — sections are theme-dependent

Implement all abstract methods with Shopify-specific logic (as stubs with clear HTTP documentation).

### File: `kai/connectors/cms/static_site.py`

**Class: StaticSiteConnector(CMSConnector)**

Config requirements:
```python
{
    "site_root": str,         # Local filesystem path to site root
    "build_tool": str,        # "none", "hugo", "jekyll", "eleventy", "next"
    "output_dir": str,        # Default: "public" or "_site" depending on build_tool
}
```

Implementation notes:
- File-based operations — reads/writes HTML files directly
- `get_pages()`: scan `site_root` for `.html` files, parse basic metadata from `<head>`
- `get_page()`: read file content, parse into sections by `<section>`, `<div>`, or heading tags
- `update_page_section()`: locate section in HTML, replace content, write file
- `get_metadata()`: parse `<title>`, `<meta>` tags from HTML `<head>`
- `update_metadata()`: modify `<head>` tags in HTML file
- `get_media()`: scan for image/video files in common asset directories
- `upload_media()`: copy file to asset directory
- No rate limiting needed for local files
- Support for build tools: know where source files vs. output files live

Implement all abstract methods with file-based logic (using `os.path`, `pathlib`, and basic HTML string parsing — no BeautifulSoup or external HTML parser dependency).

## Output Files

- `kai/connectors/__init__.py`
- `kai/connectors/cms/__init__.py`
- `kai/connectors/cms/base.py`
- `kai/connectors/cms/wordpress.py`
- `kai/connectors/cms/webflow.py`
- `kai/connectors/cms/shopify.py`
- `kai/connectors/cms/static_site.py`

## Acceptance Criteria

- [ ] `base.py` contains abstract CMSConnector class with all 9 abstract methods + 2 utility methods
- [ ] All 6 custom exceptions are defined in `base.py`
- [ ] RateLimiter class is defined with check() and wait_time() methods
- [ ] WordPressConnector implements all abstract methods with WP REST API v2 endpoint documentation
- [ ] WebflowConnector implements all abstract methods with Webflow API v2 endpoint documentation
- [ ] ShopifyConnector implements all abstract methods with Shopify Admin API endpoint documentation
- [ ] StaticSiteConnector implements all abstract methods with file-based operations
- [ ] Each connector's config requirements are documented in docstrings
- [ ] Read-only mode is enforced in all write methods (raises ReadOnlyError)
- [ ] Rate limiting is configured per-platform with correct limits
- [ ] All HTTP calls are stubs with clear comments documenting the real API call
- [ ] `snapshot_page()` is implemented in the base class and works via get_page() + get_metadata()
- [ ] `kai/connectors/cms/__init__.py` exports all connectors via `__all__`
- [ ] No external HTTP libraries are imported at module level (httpx/aiohttp referenced in docstrings only)
- [ ] Each connector can be instantiated with a config dict without making any network calls

## Reference Materials

- WordPress REST API v2: https://developer.wordpress.org/rest-api/reference/
- Webflow API v2: https://developers.webflow.com/data/reference
- Shopify Admin API: https://shopify.dev/docs/api/admin-rest
- `gateway/models.py` — Pydantic import fallback pattern (for any models used)
- `kai/runtime/integrations.py` — existing integration patterns in the runtime

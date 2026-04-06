"""Static site CMS connector — file-based operations for HTML sites.

This connector works with static websites stored on the local filesystem.
It reads and writes HTML files directly, parsing ``<head>`` tags for
metadata and splitting page content into sections by heading or
``<section>`` elements.

Supports static site generators: Hugo, Jekyll, Eleventy, Next.js, or
plain HTML with no build tool. The connector knows where source and
output files live for each generator.

No external dependencies beyond Python's standard library. Uses
``pathlib``, ``os``, ``re``, and basic string parsing — no
BeautifulSoup or lxml.
"""

from __future__ import annotations

import mimetypes
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import (
    CMSConnectionError,
    CMSConnector,
    CMSNotFoundError,
    CMSUpdateError,
    ReadOnlyError,
)


class StaticSiteConnector(CMSConnector):
    """CMS connector for static HTML sites on the local filesystem.

    Config
    ------
    The ``config`` dict must contain:

    - ``site_root`` (str): Absolute path to the site's root directory.
    - ``build_tool`` (str, optional): Static site generator in use.
      One of ``"none"``, ``"hugo"``, ``"jekyll"``, ``"eleventy"``,
      ``"next"``. Default ``"none"`` (plain HTML).
    - ``output_dir`` (str, optional): Subdirectory containing the
      generated output. Defaults are:

      ====== ============
      Tool   Default dir
      ====== ============
      none   ``.`` (root)
      hugo   ``public``
      jekyll ``_site``
      eleventy ``_site``
      next   ``out``
      ====== ============

    Example::

        connector = StaticSiteConnector({
            "site_root": "/var/www/plumber-site",
            "build_tool": "none",
        })
        info = connector.connect()

    The static site connector does not perform any rate limiting since
    all operations are local file I/O.
    """

    PLATFORM = "static_site"

    # Build tool → default output directory
    _DEFAULT_OUTPUT_DIRS = {
        "none": ".",
        "hugo": "public",
        "jekyll": "_site",
        "eleventy": "_site",
        "next": "out",
    }

    # Build tool → typical source content directories
    _SOURCE_DIRS = {
        "none": ".",
        "hugo": "content",
        "jekyll": ".",
        "eleventy": "src",
        "next": "pages",
    }

    # Common asset directories to scan for media
    _ASSET_DIRS = [
        "assets", "images", "img", "media", "static",
        "static/images", "static/img", "public/images",
        "assets/images", "assets/img",
    ]

    # Extensions for media scanning
    _IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".avif"}
    _VIDEO_EXTS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
    _DOCUMENT_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".pptx", ".txt", ".csv"}

    CAPABILITIES = [
        "read_pages",
        "write_pages",
        "read_media",
        "write_media",
        "read_metadata",
        "write_metadata",
    ]

    def __init__(self, config: Dict[str, Any], read_only: bool = False) -> None:
        super().__init__(config, read_only)

        self.site_root = Path(config["site_root"])
        self.build_tool: str = config.get("build_tool", "none")
        self.output_dir: str = config.get(
            "output_dir",
            self._DEFAULT_OUTPUT_DIRS.get(self.build_tool, "."),
        )

        self._output_path = self.site_root / self.output_dir
        self._source_dir = self._SOURCE_DIRS.get(self.build_tool, ".")
        self._source_path = self.site_root / self._source_dir

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> Dict[str, Any]:
        """Verify that the site root directory exists and is readable.

        No network calls — checks the filesystem directly.
        """
        if not self.site_root.exists():
            raise CMSConnectionError(
                f"Site root directory does not exist: {self.site_root}"
            )
        if not self.site_root.is_dir():
            raise CMSConnectionError(
                f"Site root is not a directory: {self.site_root}"
            )

        self._connected = True
        return {
            "connected": True,
            "platform": self.PLATFORM,
            "site_url": f"file://{self.site_root}",
            "capabilities": list(self.CAPABILITIES),
            "version": self.build_tool,
        }

    def disconnect(self) -> None:
        """Release connection state.

        No resources to clean up for local filesystem operations.
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
        """Scan the site directory for HTML files and return page metadata.

        Walks the output directory (or source directory for SSGs) and
        collects ``.html`` files. For Hugo/Jekyll/Eleventy, also scans
        for ``.md`` (Markdown) source files.

        ``page_type`` is accepted for interface compatibility but has no
        effect on static sites — all HTML files are returned.
        """
        search_dir = self._output_path
        if not search_dir.exists():
            search_dir = self.site_root

        extensions = {".html", ".htm"}
        if self.build_tool in ("hugo", "jekyll", "eleventy"):
            extensions.add(".md")

        pages: List[Dict[str, Any]] = []
        for root, _dirs, files in os.walk(str(search_dir)):
            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in extensions:
                    continue

                fpath = Path(root) / fname
                rel_path = fpath.relative_to(search_dir)
                slug = str(rel_path.with_suffix("")).replace(os.sep, "/")
                if slug == "index":
                    slug = ""

                stat = fpath.stat()
                modified = datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat()

                # Parse title from file if possible
                title = self._extract_title_from_file(fpath)

                pages.append({
                    "id": str(rel_path),
                    "title": title or fname,
                    "slug": slug,
                    "url": f"/{rel_path}",
                    "status": "publish",
                    "page_type": page_type,
                    "modified_date": modified,
                    "metadata": {
                        "file_path": str(fpath),
                        "file_size": stat.st_size,
                    },
                })

        # Apply pagination
        return pages[offset:offset + limit]

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Read a single HTML file and parse its content.

        ``page_id`` is the relative path from the site root (as returned
        by ``get_pages()``).
        """
        # Try output path first, then source, then site root
        fpath = self._resolve_file(page_id)
        if fpath is None:
            raise CMSNotFoundError(f"Page not found: {page_id}")

        content = fpath.read_text(encoding="utf-8", errors="replace")
        stat = fpath.stat()
        modified = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()

        # Extract body content (between <body> tags if present)
        body_html = self._extract_body(content)
        sections = self._parse_sections(body_html)
        metadata = self._extract_metadata_from_html(content)

        slug = str(Path(page_id).with_suffix("")).replace(os.sep, "/")
        if slug == "index":
            slug = ""

        return {
            "id": page_id,
            "title": metadata.get("title", Path(page_id).stem),
            "slug": slug,
            "url": f"/{page_id}",
            "content_html": body_html,
            "content_raw": content,
            "sections": sections,
            "metadata": metadata,
            "status": "publish",
            "modified_date": modified,
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
        """Replace a section of an HTML file on disk.

        Reads the full file, locates the section by ``section_id``,
        replaces its content, and writes the file back.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        CMSNotFoundError
            If the file does not exist.
        """
        self._enforce_writable()

        fpath = self._resolve_file(page_id)
        if fpath is None:
            raise CMSNotFoundError(f"Page not found: {page_id}")

        full_content = fpath.read_text(encoding="utf-8", errors="replace")
        body_html = self._extract_body(full_content)
        sections = self._parse_sections(body_html)

        # Find the target section
        previous_content = ""
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

        if not previous_content:
            raise CMSNotFoundError(
                f"Section '{section_id}' not found in page {page_id}"
            )

        # Replace the section content in the full file
        updated_content = full_content.replace(previous_content, content, 1)
        fpath.write_text(updated_content, encoding="utf-8")

        return {
            "success": True,
            "page_id": page_id,
            "section_id": section_id,
            "previous_content": previous_content,
            "new_content": content,
        }

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, page_id: str) -> Dict[str, Any]:
        """Parse ``<head>`` tags from an HTML file to extract metadata."""
        fpath = self._resolve_file(page_id)
        if fpath is None:
            raise CMSNotFoundError(f"Page not found: {page_id}")

        content = fpath.read_text(encoding="utf-8", errors="replace")
        return self._extract_metadata_from_html(content)

    def update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Update ``<head>`` meta tags in an HTML file.

        Modifies ``<title>``, ``<meta name="description">``,
        ``<meta property="og:*">``, and ``<link rel="canonical">`` tags
        in the file's ``<head>`` section.

        Only fields present in ``meta`` are updated. If a tag doesn't
        exist yet, it is inserted before ``</head>``.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        """
        self._enforce_writable()

        fpath = self._resolve_file(page_id)
        if fpath is None:
            raise CMSNotFoundError(f"Page not found: {page_id}")

        content = fpath.read_text(encoding="utf-8", errors="replace")
        updated_fields: List[str] = []

        # Update <title>
        if "title" in meta:
            content = self._replace_or_insert_tag(
                content,
                tag_pattern=r'<title[^>]*>.*?</title>',
                replacement=f'<title>{meta["title"]}</title>',
                insert_before="</head>",
            )
            updated_fields.append("title")

        # Update <meta name="description">
        if "meta_description" in meta:
            content = self._replace_or_insert_tag(
                content,
                tag_pattern=r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\'][^>]*/?>',
                replacement=f'<meta name="description" content="{self._escape_attr(meta["meta_description"])}">',
                insert_before="</head>",
            )
            updated_fields.append("meta_description")

        # Update OG tags
        og_fields = {
            "og_title": "og:title",
            "og_description": "og:description",
            "og_image": "og:image",
        }
        for kai_key, og_property in og_fields.items():
            if kai_key in meta:
                content = self._replace_or_insert_tag(
                    content,
                    tag_pattern=rf'<meta\s+property=["\']{ re.escape(og_property) }["\']\s+content=["\'][^"\']*["\'][^>]*/?>',
                    replacement=f'<meta property="{og_property}" content="{self._escape_attr(meta[kai_key])}">',
                    insert_before="</head>",
                )
                updated_fields.append(kai_key)

        # Update canonical URL
        if "canonical_url" in meta:
            content = self._replace_or_insert_tag(
                content,
                tag_pattern=r'<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']*["\'][^>]*/?>',
                replacement=f'<link rel="canonical" href="{self._escape_attr(meta["canonical_url"])}">',
                insert_before="</head>",
            )
            updated_fields.append("canonical_url")

        fpath.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "page_id": page_id,
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
        """Scan common asset directories for image, video, and document files."""
        all_media = self._IMAGE_EXTS | self._VIDEO_EXTS | self._DOCUMENT_EXTS

        if media_type == "image":
            target_exts = self._IMAGE_EXTS
        elif media_type == "video":
            target_exts = self._VIDEO_EXTS
        elif media_type == "document":
            target_exts = self._DOCUMENT_EXTS
        else:
            target_exts = all_media

        media_list: List[Dict[str, Any]] = []
        scanned_paths: set = set()

        for asset_dir_name in self._ASSET_DIRS:
            asset_dir = self.site_root / asset_dir_name
            if not asset_dir.exists() or not asset_dir.is_dir():
                continue

            for root, _dirs, files in os.walk(str(asset_dir)):
                for fname in sorted(files):
                    fpath = Path(root) / fname
                    if str(fpath) in scanned_paths:
                        continue
                    scanned_paths.add(str(fpath))

                    ext = fpath.suffix.lower()
                    if ext not in target_exts:
                        continue

                    stat = fpath.stat()
                    mime = mimetypes.guess_type(str(fpath))[0] or ""
                    rel_path = fpath.relative_to(self.site_root)

                    if ext in self._IMAGE_EXTS:
                        file_type = "image"
                    elif ext in self._VIDEO_EXTS:
                        file_type = "video"
                    else:
                        file_type = "document"

                    uploaded = datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat()

                    media_list.append({
                        "id": str(rel_path),
                        "title": fname,
                        "url": f"/{rel_path}",
                        "type": file_type,
                        "mime_type": mime,
                        "size_bytes": stat.st_size,
                        "dimensions": None,  # Would require PIL to read
                        "alt_text": None,
                        "uploaded_date": uploaded,
                    })

        return media_list[offset:offset + limit]

    def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Copy a file into the site's asset directory.

        Copies the file to ``{site_root}/assets/`` (or the first
        existing asset directory). Creates ``assets/`` if no asset
        directory exists.

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        CMSUpdateError
            If the source file does not exist.
        """
        self._enforce_writable()

        source = Path(file_path)
        if not source.exists():
            raise CMSUpdateError(f"Source file does not exist: {file_path}")

        filename = source.name
        media_title = title or source.stem

        # Find or create an asset directory
        target_dir: Optional[Path] = None
        for asset_dir_name in self._ASSET_DIRS:
            candidate = self.site_root / asset_dir_name
            if candidate.exists() and candidate.is_dir():
                target_dir = candidate
                break

        if target_dir is None:
            target_dir = self.site_root / "assets"
            target_dir.mkdir(parents=True, exist_ok=True)

        dest = target_dir / filename

        # Avoid overwriting: append a counter if file exists
        counter = 1
        while dest.exists():
            stem = source.stem
            dest = target_dir / f"{stem}_{counter}{source.suffix}"
            counter += 1

        shutil.copy2(str(source), str(dest))
        rel_path = dest.relative_to(self.site_root)

        return {
            "success": True,
            "media_id": str(rel_path),
            "url": f"/{rel_path}",
            "title": media_title,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_file(self, page_id: str) -> Optional[Path]:
        """Locate the file for a given page_id.

        Checks the output directory, source directory, and site root
        in order.
        """
        candidates = [
            self._output_path / page_id,
            self._source_path / page_id,
            self.site_root / page_id,
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _extract_title_from_file(fpath: Path) -> str:
        """Read the first few KB of a file and extract the <title> tag."""
        try:
            # Read only the first 4KB to find the title quickly
            with open(str(fpath), "r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(4096)
            match = re.search(r'<title[^>]*>(.*?)</title>', head, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except (OSError, UnicodeDecodeError):
            pass
        return ""

    @staticmethod
    def _extract_body(html: str) -> str:
        """Extract content between <body> and </body> tags.

        Returns the full content if no <body> tags are found.
        """
        match = re.search(
            r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        return html

    @staticmethod
    def _extract_metadata_from_html(html: str) -> Dict[str, Any]:
        """Parse <head> section for SEO metadata tags.

        Extracts:
        - <title>
        - <meta name="description">
        - <meta property="og:title">
        - <meta property="og:description">
        - <meta property="og:image">
        - <link rel="canonical">
        - <script type="application/ld+json"> (schema markup)
        """
        # Extract <head> section
        head_match = re.search(
            r'<head[^>]*>(.*?)</head>', html, re.DOTALL | re.IGNORECASE
        )
        head = head_match.group(1) if head_match else html

        # Title
        title_match = re.search(
            r'<title[^>]*>(.*?)</title>', head, re.DOTALL | re.IGNORECASE
        )
        title = title_match.group(1).strip() if title_match else ""

        # Meta description
        desc_match = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']',
            head, re.IGNORECASE,
        )
        meta_description = desc_match.group(1).strip() if desc_match else ""

        # OG tags
        def _get_og(prop: str) -> str:
            pattern = rf'<meta\s+property=["\']{ re.escape(prop) }["\']\s+content=["\']([^"\']*)["\']'
            m = re.search(pattern, head, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        og_title = _get_og("og:title")
        og_description = _get_og("og:description")
        og_image = _get_og("og:image")

        # Canonical URL
        canonical_match = re.search(
            r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']*)["\']',
            head, re.IGNORECASE,
        )
        canonical_url = canonical_match.group(1).strip() if canonical_match else ""

        # Schema markup (JSON-LD)
        schema_markup: List[Dict[str, Any]] = []
        schema_pattern = re.compile(
            r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        for schema_match in schema_pattern.finditer(html):
            try:
                import json
                schema_data = json.loads(schema_match.group(1).strip())
                if isinstance(schema_data, dict):
                    schema_markup.append(schema_data)
                elif isinstance(schema_data, list):
                    schema_markup.extend(schema_data)
            except (json.JSONDecodeError, ValueError):
                pass

        return {
            "title": title,
            "meta_description": meta_description,
            "og_title": og_title,
            "og_description": og_description,
            "og_image": og_image,
            "canonical_url": canonical_url,
            "schema_markup": schema_markup,
            "custom_fields": {},
        }

    @staticmethod
    def _replace_or_insert_tag(
        html: str,
        tag_pattern: str,
        replacement: str,
        insert_before: str,
    ) -> str:
        """Replace an existing HTML tag or insert a new one.

        If ``tag_pattern`` matches in the HTML, replaces the first match.
        Otherwise, inserts ``replacement`` just before ``insert_before``.
        """
        if re.search(tag_pattern, html, re.IGNORECASE | re.DOTALL):
            return re.sub(
                tag_pattern, replacement, html, count=1,
                flags=re.IGNORECASE | re.DOTALL,
            )
        else:
            # Insert before the target tag
            insert_pos = html.lower().find(insert_before.lower())
            if insert_pos >= 0:
                return (
                    html[:insert_pos]
                    + "  " + replacement + "\n"
                    + html[insert_pos:]
                )
            # If insert_before not found, append at end
            return html + "\n" + replacement

    @staticmethod
    def _escape_attr(value: str) -> str:
        """Escape a string for use in an HTML attribute value."""
        return (
            value
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _parse_sections(html: str) -> List[Dict[str, Any]]:
        """Parse HTML content into logical sections.

        Splitting strategy (in priority order):
        1. ``<section>`` elements
        2. ``<h2>``/``<h3>`` heading tags
        3. Treat whole content as one section
        """
        if not html or not html.strip():
            return []

        sections: List[Dict[str, Any]] = []

        # Strategy 1: <section> elements
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

        # Strategy 2: heading-based splitting
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

        # Strategy 3: whole content as one section
        if not sections and html.strip():
            sections.append({
                "id": "section_0",
                "type": "body",
                "heading": "",
                "content": html.strip(),
            })

        return sections

"""CMS connector base class, custom exceptions, and rate limiter.

This module defines the abstract interface that all CMS connectors must implement,
plus shared utilities (rate limiting, error types) used across all connectors.

No external HTTP libraries are imported at module level. Concrete connectors
document their HTTP calls as stubs with comments describing the real API request.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class CMSConnectionError(Exception):
    """Raised when the connector cannot establish a connection to the CMS."""


class CMSAuthError(Exception):
    """Raised when authentication credentials are invalid or expired."""


class CMSNotFoundError(Exception):
    """Raised when a requested page, media item, or resource does not exist."""


class CMSRateLimitError(Exception):
    """Raised when the platform's rate limit has been exceeded."""


class ReadOnlyError(Exception):
    """Raised when a write operation is attempted while the connector is in read-only mode."""


class CMSUpdateError(Exception):
    """Raised when a content or metadata update fails on the CMS side."""


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------


class RateLimiter:
    """Simple sliding-window rate limiter.

    Tracks request timestamps in a list and enforces a maximum number of
    requests within a rolling time window.

    Parameters
    ----------
    max_requests : int
        Maximum allowed requests within the window. Default 10.
    window_seconds : int
        Length of the sliding window in seconds. Default 60.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: List[float] = []

    def _prune(self) -> None:
        """Remove timestamps outside the current window."""
        cutoff = time.monotonic() - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]

    def check(self) -> bool:
        """Return True if a request is allowed right now, False if rate-limited."""
        self._prune()
        return len(self._timestamps) < self.max_requests

    def record(self) -> None:
        """Record that a request was just made."""
        self._timestamps.append(time.monotonic())

    def wait_time(self) -> float:
        """Return seconds until the next request slot opens.

        Returns 0.0 if a request is currently allowed.
        """
        self._prune()
        if len(self._timestamps) < self.max_requests:
            return 0.0
        # The oldest timestamp in the window determines when a slot opens
        oldest = self._timestamps[0]
        return max(0.0, (oldest + self.window_seconds) - time.monotonic())


# ---------------------------------------------------------------------------
# Abstract Base Class
# ---------------------------------------------------------------------------


class CMSConnector(ABC):
    """Abstract base class for all CMS connectors.

    Every connector implements the same interface regardless of the underlying
    platform (WordPress, Webflow, Shopify, static files, etc.). This enables
    Kai's website operations to work uniformly across CMS platforms.

    Parameters
    ----------
    config : Dict[str, Any]
        Platform-specific authentication credentials and settings.
    read_only : bool
        When True, all write operations raise ``ReadOnlyError``. Use for
        safe auditing without accidental mutations. Default False.
    """

    def __init__(self, config: Dict[str, Any], read_only: bool = False) -> None:
        self.config = config
        self.read_only = read_only
        self._connected = False

    # ------------------------------------------------------------------
    # Write-guard helper
    # ------------------------------------------------------------------

    def _enforce_writable(self) -> None:
        """Raise ``ReadOnlyError`` if the connector is in read-only mode.

        Every write method must call this before performing any mutation.
        """
        if self.read_only:
            raise ReadOnlyError(
                "Write operation blocked: connector is in read-only mode. "
                "Instantiate with read_only=False to allow writes."
            )

    # ------------------------------------------------------------------
    # Abstract methods — must be implemented by every connector
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        """Establish connection to the CMS and validate credentials.

        Returns
        -------
        dict
            Connection info with keys:
            - ``connected`` (bool): whether the connection succeeded
            - ``platform`` (str): CMS platform name
            - ``site_url`` (str): root URL of the connected site
            - ``capabilities`` (List[str]): supported operations
            - ``version`` (Optional[str]): CMS or API version

        Capabilities may include:
            read_pages, write_pages, read_media, write_media,
            read_menus, write_menus, read_metadata, write_metadata,
            custom_fields

        Raises
        ------
        CMSConnectionError
            If the CMS is unreachable.
        CMSAuthError
            If credentials are invalid.

        Note: should be async in production (using httpx or aiohttp).
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Clean up connection resources and release any held state.

        Note: should be async in production.
        """

    @abstractmethod
    def get_pages(
        self,
        page_type: str = "page",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return a paginated list of pages or posts.

        Parameters
        ----------
        page_type : str
            One of ``"page"``, ``"post"``, ``"product"``, ``"collection"``,
            ``"landing_page"``. Default ``"page"``.
        limit : int
            Maximum number of results. Default 100.
        offset : int
            Number of results to skip (for pagination). Default 0.

        Returns
        -------
        list of dict
            Each dict contains:
            - ``id`` (str)
            - ``title`` (str)
            - ``slug`` (str)
            - ``url`` (str)
            - ``status`` (str): e.g. ``"publish"``, ``"draft"``
            - ``page_type`` (str)
            - ``modified_date`` (str): ISO-8601 timestamp
            - ``metadata`` (dict)

        Note: should be async in production.
        """

    @abstractmethod
    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Return the full content and metadata for a single page.

        Parameters
        ----------
        page_id : str
            Platform-specific page identifier.

        Returns
        -------
        dict
            - ``id`` (str)
            - ``title`` (str)
            - ``slug`` (str)
            - ``url`` (str)
            - ``content_html`` (str): rendered HTML content
            - ``content_raw`` (str): raw/source content (Gutenberg blocks,
              Liquid, Markdown, etc.)
            - ``sections`` (List[Dict]): logical page sections (hero, body,
              sidebar, footer)
            - ``metadata`` (dict): SEO and Open Graph metadata
            - ``status`` (str)
            - ``modified_date`` (str): ISO-8601 timestamp

        Raises
        ------
        CMSNotFoundError
            If the page does not exist.

        Note: should be async in production.
        """

    @abstractmethod
    def update_page_section(
        self,
        page_id: str,
        section_id: str,
        content: str,
        content_type: str = "html",
    ) -> Dict[str, Any]:
        """Update a specific section of a page.

        Parameters
        ----------
        page_id : str
            Platform-specific page identifier.
        section_id : str
            Identifier of the section within the page to update.
        content : str
            The new content to place in the section.
        content_type : str
            Format of ``content``: ``"html"``, ``"text"``, ``"json"``, or
            ``"markdown"``. Default ``"html"``.

        Returns
        -------
        dict
            - ``success`` (bool)
            - ``page_id`` (str)
            - ``section_id`` (str)
            - ``previous_content`` (str): content before the update
            - ``new_content`` (str): content after the update

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        CMSNotFoundError
            If the page or section does not exist.
        CMSUpdateError
            If the update fails.

        Note: should be async in production.
        """

    @abstractmethod
    def get_metadata(self, page_id: str) -> Dict[str, Any]:
        """Return SEO and social metadata for a page.

        Parameters
        ----------
        page_id : str
            Platform-specific page identifier.

        Returns
        -------
        dict
            - ``title`` (str): title tag content
            - ``meta_description`` (str)
            - ``og_title`` (str)
            - ``og_description`` (str)
            - ``og_image`` (str): URL of Open Graph image
            - ``canonical_url`` (str)
            - ``schema_markup`` (List[Dict]): JSON-LD schema objects
            - ``custom_fields`` (dict): platform-specific custom fields

        Raises
        ------
        CMSNotFoundError
            If the page does not exist.

        Note: should be async in production.
        """

    @abstractmethod
    def update_metadata(self, page_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Update metadata fields for a page.

        Only fields present in ``meta`` are updated; unmentioned fields are
        left unchanged.

        Parameters
        ----------
        page_id : str
            Platform-specific page identifier.
        meta : dict
            Key-value pairs of metadata fields to update. Supported keys
            match the output of ``get_metadata()``.

        Returns
        -------
        dict
            - ``success`` (bool)
            - ``page_id`` (str)
            - ``updated_fields`` (List[str]): names of fields that were changed

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        CMSNotFoundError
            If the page does not exist.
        CMSUpdateError
            If the update fails.

        Note: should be async in production.
        """

    @abstractmethod
    def get_media(
        self,
        limit: int = 50,
        offset: int = 0,
        media_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return a paginated list of media items.

        Parameters
        ----------
        limit : int
            Maximum number of results. Default 50.
        offset : int
            Number of results to skip. Default 0.
        media_type : str or None
            Filter by type: ``"image"``, ``"video"``, ``"document"``, or
            ``None`` for all types. Default ``None``.

        Returns
        -------
        list of dict
            Each dict contains:
            - ``id`` (str)
            - ``title`` (str)
            - ``url`` (str)
            - ``type`` (str): ``"image"``, ``"video"``, ``"document"``
            - ``mime_type`` (str): e.g. ``"image/jpeg"``
            - ``size_bytes`` (int)
            - ``dimensions`` (Optional[str]): e.g. ``"1200x800"``
            - ``alt_text`` (Optional[str])
            - ``uploaded_date`` (str): ISO-8601 timestamp

        Note: should be async in production.
        """

    @abstractmethod
    def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a media file to the CMS.

        Parameters
        ----------
        file_path : str
            Local filesystem path to the file to upload.
        title : str or None
            Title/label for the media item. Defaults to the filename.
        alt_text : str or None
            Accessibility alt text for the media item.

        Returns
        -------
        dict
            - ``success`` (bool)
            - ``media_id`` (str)
            - ``url`` (str): public URL of the uploaded file
            - ``title`` (str)

        Raises
        ------
        ReadOnlyError
            If the connector is in read-only mode.
        CMSUpdateError
            If the upload fails.

        Note: should be async in production.
        """

    # ------------------------------------------------------------------
    # Non-abstract utility methods
    # ------------------------------------------------------------------

    def validate_connection(self) -> Dict[str, Any]:
        """Perform a health check by attempting to connect.

        Returns
        -------
        dict
            - ``healthy`` (bool): True if the connection succeeds
            - ``platform`` (str): CMS platform name
            - ``error`` (Optional[str]): error message if unhealthy
            - ``capabilities`` (List[str]): available operations
        """
        try:
            info = self.connect()
            return {
                "healthy": info.get("connected", False),
                "platform": info.get("platform", "unknown"),
                "error": None,
                "capabilities": info.get("capabilities", []),
            }
        except (CMSConnectionError, CMSAuthError) as exc:
            return {
                "healthy": False,
                "platform": self.config.get("platform", "unknown"),
                "error": str(exc),
                "capabilities": [],
            }

    def snapshot_page(self, page_id: str) -> Dict[str, Any]:
        """Capture the full current state of a page for rollback purposes.

        Combines content (from ``get_page``) and metadata (from
        ``get_metadata``) into a single timestamped snapshot.

        Parameters
        ----------
        page_id : str
            Platform-specific page identifier.

        Returns
        -------
        dict
            - ``page_id`` (str)
            - ``timestamp`` (str): ISO-8601 timestamp when the snapshot was taken
            - ``content`` (dict): full page content from ``get_page()``
            - ``metadata`` (dict): full metadata from ``get_metadata()``
        """
        content = self.get_page(page_id)
        metadata = self.get_metadata(page_id)
        return {
            "page_id": page_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": content,
            "metadata": metadata,
        }

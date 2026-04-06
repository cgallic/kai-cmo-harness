"""CMS connector layer — uniform interface for website operations.

Provides a single abstract interface (``CMSConnector``) for reading and
writing website content across platforms, plus four concrete
implementations:

- ``WordPressConnector`` — WP REST API v2
- ``WebflowConnector`` — Webflow API v2
- ``ShopifyConnector`` — Shopify Admin REST API
- ``StaticSiteConnector`` — Local HTML files (Hugo, Jekyll, Eleventy, Next, plain)

Each connector can be instantiated with a config dict and optional
``read_only`` flag without making any network calls.
"""

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
from .shopify import ShopifyConnector
from .static_site import StaticSiteConnector
from .webflow import WebflowConnector
from .wordpress import WordPressConnector

__all__ = [
    # Base class and utilities
    "CMSConnector",
    "RateLimiter",
    # Exceptions
    "CMSAuthError",
    "CMSConnectionError",
    "CMSNotFoundError",
    "CMSRateLimitError",
    "CMSUpdateError",
    "ReadOnlyError",
    # Concrete connectors
    "ShopifyConnector",
    "StaticSiteConnector",
    "WebflowConnector",
    "WordPressConnector",
]

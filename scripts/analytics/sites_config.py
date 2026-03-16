"""
Multi-Site Analytics Configuration

Sites are loaded from environment variables.
Set SITES_CONFIG as JSON, or individual GA_*_PROPERTY_ID and GSC_*_URL variables.

Example .env:
    SITES_CONFIG={"mysite":{"name":"My Site","url":"https://mysite.com","category":"product"}}
    GA_MYSITE_PROPERTY_ID=123456789
    GSC_MYSITE_URL=sc-domain:mysite.com
"""

import os
import json
from pathlib import Path
from .config import load_dotenv

# Ensure env is loaded
load_dotenv()


def get_credentials_path():
    """Get path to Google credentials JSON file"""
    if os.getenv("GOOGLE_CREDENTIALS_PATH"):
        return os.getenv("GOOGLE_CREDENTIALS_PATH")
    paths = [
        Path.home() / ".claude" / "google-analytics-credentials.json",
    ]
    for p in paths:
        if p.exists():
            return str(p)
    return str(Path.home() / ".claude" / "google-analytics-credentials.json")


def load_sites_from_env():
    """Load site configuration from environment variables"""
    # Try to load from JSON config first
    sites_json = os.getenv("SITES_CONFIG", "{}")
    try:
        sites = json.loads(sites_json)
    except json.JSONDecodeError:
        sites = {}

    # Build GA_PROPERTIES from SITES_CONFIG + individual env vars
    ga_properties = {}
    gsc_sites = {}

    for key, site_info in sites.items():
        # Get property ID from env or use empty
        property_id = os.getenv(f"GA_{key.upper()}_PROPERTY_ID", "")
        if property_id:
            ga_properties[key] = {
                "property_id": property_id,
                "name": site_info.get("name", key),
                "url": site_info.get("url", ""),
                "category": site_info.get("category", "other"),
            }

        # Get GSC URL from env
        gsc_url = os.getenv(f"GSC_{key.upper()}_URL", "")
        if gsc_url:
            gsc_sites[key] = {
                "site_url": gsc_url,
                "name": site_info.get("name", key),
            }

    return ga_properties, gsc_sites


# Load sites from environment
GA_PROPERTIES, GSC_SITES = load_sites_from_env()

CREDENTIALS_PATH = get_credentials_path()


def get_all_sites():
    """Get list of all configured site keys"""
    return list(set(list(GA_PROPERTIES.keys()) + list(GSC_SITES.keys())))


def get_sites_by_category(category: str):
    """Get sites filtered by category"""
    return {k: v for k, v in GA_PROPERTIES.items() if v.get("category") == category}


def get_all_gsc_sites():
    """Get list of all GSC site keys"""
    return list(GSC_SITES.keys())


def get_all_ga_sites():
    """Get list of all GA site keys"""
    return list(GA_PROPERTIES.keys())


def get_gsc_site_url(site_key: str) -> str:
    """Get GSC site URL for a site key"""
    return GSC_SITES.get(site_key, {}).get("site_url", "")


def get_ga_property_id(site_key: str) -> str:
    """Get GA property ID for a site key"""
    return GA_PROPERTIES.get(site_key, {}).get("property_id", "")


def add_site(key: str, name: str, url: str, category: str, ga_property_id: str = "", gsc_url: str = ""):
    """Dynamically add a site to the configuration"""
    if ga_property_id:
        GA_PROPERTIES[key] = {
            "property_id": ga_property_id,
            "name": name,
            "url": url,
            "category": category,
        }
    if gsc_url:
        GSC_SITES[key] = {
            "site_url": gsc_url,
            "name": name,
        }

"""
CMO Analytics System
Unified analytics with Google Analytics, Search Console, and Supabase
"""

from .config import Config
from .google_analytics import GoogleAnalytics
from .search_console import SearchConsole
from .supabase_analytics import SupabaseAnalytics
from .dashboard import Dashboard
from .multi_site import MultiSiteAnalytics
from .sites_config import GSC_SITES, GA_PROPERTIES, CREDENTIALS_PATH

__all__ = [
    'Config',
    'GoogleAnalytics',
    'SearchConsole',
    'SupabaseAnalytics',
    'Dashboard',
    'MultiSiteAnalytics',
    'GSC_SITES',
    'GA_PROPERTIES',
    'CREDENTIALS_PATH',
]

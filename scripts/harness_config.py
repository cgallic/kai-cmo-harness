"""
Harness Config — Centralized configuration for Kai Harness.

All hardcoded paths, IDs, and thresholds live here.
Override via environment variables or config.yaml at project root.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import yaml
from dotenv import load_dotenv


_REPO_ROOT = Path(__file__).resolve().parent.parent


def _find_env() -> Path:
    """Find .env file: check CMO_BASE_DIR, then repo root."""
    base = os.environ.get("CMO_BASE_DIR", "")
    if base:
        p = Path(base) / ".env"
        if p.exists():
            return p
    return _REPO_ROOT / ".env"


load_dotenv(_find_env(), override=False)
load_dotenv(_REPO_ROOT / ".env", override=False)


@dataclass
class DiscordConfig:
    """Discord channel IDs by site key."""
    channels: Dict[str, str] = field(default_factory=dict)
    fallback_channel: str = ""

    def get(self, site: str) -> str:
        return self.channels.get(site, self.fallback_channel)


@dataclass
class SiteConfig:
    """Site-to-GSC-property and GA4-property mappings."""
    gsc_urls: Dict[str, str] = field(default_factory=dict)
    ga4_properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class ThresholdConfig:
    """Performance and pattern thresholds."""
    win_position: int = 5
    win_ctr: float = 0.05
    win_time_on_page: int = 90
    min_n: int = 5
    min_delta: float = 0.15


@dataclass
class HarnessConfig:
    """Top-level harness configuration.

    Load order:
      1. config.yaml at repo root (or CMO_CONFIG_PATH env var)
      2. Environment variables override YAML values
      3. Defaults fill in anything missing
    """
    # Paths
    repo_root: Path = field(default_factory=lambda: _REPO_ROOT)
    cmo_base_dir: Path = field(default_factory=lambda: Path(os.environ.get("CMO_BASE_DIR", str(_REPO_ROOT))))
    workspace_dir: Path = field(default_factory=lambda: Path(os.environ.get("WORKSPACE_DIR", str(_REPO_ROOT / "workspace"))))
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("CMO_DATA_DIR", str(_REPO_ROOT / "data"))))
    marketing_md: Path = field(default_factory=lambda: Path(""))
    policy_dir: Path = field(default_factory=lambda: Path(""))
    knowledge_base: Path = field(default_factory=lambda: Path(""))
    venv_python: str = field(default_factory=lambda: os.environ.get("VENV_PYTHON", ""))

    # API
    gemini_api_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", ""))
    gemini_model: str = "gemini-2.0-flash"
    api_timeout: int = 30
    api_max_retries: int = 3

    # Sub-configs
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    sites: SiteConfig = field(default_factory=SiteConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)

    def __post_init__(self):
        # Derive paths that depend on other fields
        if not str(self.marketing_md) or str(self.marketing_md) == ".":
            self.marketing_md = self.workspace_dir / "MARKETING.md"
        if not str(self.policy_dir) or str(self.policy_dir) == ".":
            self.policy_dir = self.repo_root / "scripts" / "quality" / "policies"
        if not str(self.knowledge_base) or str(self.knowledge_base) == ".":
            kb = self.workspace_dir / "knowledge" / "playbooks"
            if not kb.exists():
                kb = self.repo_root / "knowledge" / "playbooks"
            self.knowledge_base = kb
        if not self.venv_python:
            import sys
            self.venv_python = sys.executable

    @property
    def content_log(self) -> Path:
        return self.data_dir / "content_log.json"

    @property
    def pending_checks_dir(self) -> Path:
        return self.data_dir / "pending_checks"

    @property
    def defaults_file(self) -> Path:
        return self.data_dir / "harness_defaults.json"

    @property
    def scripts_dir(self) -> Path:
        return self.cmo_base_dir / "scripts"

    @property
    def knowledge_dir(self) -> Path:
        ws_knowledge = self.workspace_dir / "knowledge"
        if ws_knowledge.exists():
            return ws_knowledge
        return self.repo_root / "knowledge"


def _load_config_yaml() -> dict:
    """Load config.yaml from repo root or CMO_CONFIG_PATH."""
    path_str = os.environ.get("CMO_CONFIG_PATH", str(_REPO_ROOT / "config.yaml"))
    path = Path(path_str)
    if path.exists():
        try:
            return yaml.safe_load(path.read_text()) or {}
        except Exception:
            return {}
    return {}


def load_config() -> HarnessConfig:
    """Load and validate harness configuration.

    Merges config.yaml values with environment variable overrides.
    """
    raw = _load_config_yaml()

    # Build discord config
    discord_raw = raw.get("discord", {})
    discord = DiscordConfig(
        channels=discord_raw.get("channels", {}),
        fallback_channel=discord_raw.get("fallback_channel", ""),
    )

    # Build site config
    sites_raw = raw.get("sites", {})
    gsc_urls = sites_raw.get("gsc_urls", {})
    ga4_props = {}
    for site_key, prop_id in sites_raw.get("ga4_properties", {}).items():
        # Allow env var override per site
        env_key = f"GA4_PROPERTY_{site_key.upper()}"
        ga4_props[site_key] = os.environ.get(env_key, str(prop_id))
    sites = SiteConfig(gsc_urls=gsc_urls, ga4_properties=ga4_props)

    # Build threshold config
    thresh_raw = raw.get("thresholds", {})
    thresholds = ThresholdConfig(
        win_position=thresh_raw.get("win_position", 5),
        win_ctr=thresh_raw.get("win_ctr", 0.05),
        win_time_on_page=thresh_raw.get("win_time_on_page", 90),
        min_n=thresh_raw.get("min_n", 5),
        min_delta=thresh_raw.get("min_delta", 0.15),
    )

    # Build paths — env vars override YAML
    paths_raw = raw.get("paths") or {}

    cfg = HarnessConfig(
        cmo_base_dir=Path(os.environ.get("CMO_BASE_DIR", paths_raw.get("cmo_base_dir", str(_REPO_ROOT)))),
        workspace_dir=Path(os.environ.get("WORKSPACE_DIR", paths_raw.get("workspace_dir", str(_REPO_ROOT / "workspace")))),
        data_dir=Path(os.environ.get("CMO_DATA_DIR", paths_raw.get("data_dir", str(_REPO_ROOT / "data")))),
        marketing_md=Path(os.environ.get("CMO_MARKETING_MD", paths_raw.get("marketing_md", ""))),
        policy_dir=Path(os.environ.get("CMO_POLICY_DIR", paths_raw.get("policy_dir", ""))),
        knowledge_base=Path(os.environ.get("CMO_KNOWLEDGE_BASE", paths_raw.get("knowledge_base", ""))),
        venv_python=os.environ.get("VENV_PYTHON", paths_raw.get("venv_python", "")),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", raw.get("gemini_api_key", "")),
        gemini_model=raw.get("gemini_model", "gemini-2.0-flash"),
        api_timeout=raw.get("api_timeout", 30),
        api_max_retries=raw.get("api_max_retries", 3),
        discord=discord,
        sites=sites,
        thresholds=thresholds,
    )

    return cfg


# Singleton — loaded once, reusable across modules
_config: Optional[HarnessConfig] = None


def get_config() -> HarnessConfig:
    """Get the singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config

"""
Persona Resolver — Maps (site, keyword) to the best-fit marketing persona.

Uses site_persona_defaults from config.yaml. If the keyword contains AI/automation
signals, returns the secondary persona instead of primary.
"""

import re

from scripts.harness_config import get_config

KEYWORD_SIGNALS = re.compile(
    r"\b(AI|automate|replace|future.?proof|obsolete|machine learning|GPT|LLM|bot)\b",
    re.IGNORECASE,
)


def resolve_persona(site: str, keyword: str, override: str | None = None) -> str:
    """Resolve the best persona for a site+keyword pair.

    Args:
        site: Site key (e.g. "kaicalls").
        keyword: Target keyword for the content.
        override: If provided, returned as-is (explicit persona selection).

    Returns:
        Persona archetype name (e.g. "Competent Cog").

    Raises:
        ValueError: If site has no persona defaults configured.
    """
    if override:
        return override

    cfg = get_config()
    defaults = cfg.site_persona_defaults.get(site)
    if not defaults:
        valid = list(cfg.site_persona_defaults.keys())
        raise ValueError(
            f"No persona defaults for site '{site}'. "
            f"Valid sites: {', '.join(valid) or 'none configured'}"
        )

    if KEYWORD_SIGNALS.search(keyword):
        return defaults.get("secondary", defaults["primary"])

    return defaults["primary"]

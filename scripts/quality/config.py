"""
Content Quality Scorer — Configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env — check project root first, then scripts/
_project_root = Path(__file__).parent.parent.parent
_env_candidates = [
    _project_root / ".env",
    Path(__file__).parent.parent / ".env",
]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(_env_path, override=True)

# API Keys (reuse from knowledge_cloner)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Category weights (must sum to 1.0)
CATEGORY_WEIGHTS = {
    "Algorithmic Authorship": 0.30,
    "GEO/AEO Signals": 0.15,
    "Content Structure": 0.20,
    "Four U's": 0.15,
    "Taste": 0.20,
}

# Weights when LLM rules are disabled (redistribute Four U's proportionally)
CATEGORY_WEIGHTS_NO_LLM = {
    "Algorithmic Authorship": 0.4375,  # 0.35 / 0.80
    "GEO/AEO Signals": 0.25,          # 0.20 / 0.80
    "Content Structure": 0.3125,       # 0.25 / 0.80
}

# Grade boundaries
GRADE_BOUNDARIES = {
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 60,
    "F": 0,
}

# GEO signal targets per 1K words
GEO_TARGETS = {
    "citations": 5,
    "quotations": 3,
    "statistics": 5,
    "technical_terms": 10,
}

# GEO visibility boosts (from academic research)
GEO_BOOSTS = {
    "citations": "+115%",
    "quotations": "+40%",
    "statistics": "+37%",
    "technical_terms": "+32.7%",
}

# Content structure targets
STRUCTURE_TARGETS = {
    "max_words_between_headings": 300,
    "min_words_between_headings": 100,
    "min_paragraph_sentences": 2,
    "max_paragraph_sentences": 4,
    "min_avg_sentence_length": 15,
    "max_avg_sentence_length": 20,
    "target_active_voice_pct": 90,
    "target_reading_level_min": 6,
    "target_reading_level_max": 8,
    "you_your_ratio_target": 2.0,  # "you/your" should be 2x "we/our/I"
}

# AI cliche patterns — tiered by severity
# Tier 1 (BLOCKING): Instant-reject filler that screams "AI wrote this"
AI_CLICHES_TIER1 = [
    r"\bit'?s important to note\b",
    r"\bin conclusion\b",
    r"\bin today'?s (?:fast[- ]paced|digital|modern|rapidly evolving) (?:world|landscape|era)\b",
    r"\bthis comprehensive guide\b",
    r"\bwithout further ado\b",
    r"\bit'?s worth noting that\b",
    r"\bin the ever[- ]changing landscape\b",
    r"\bas we navigate\b",
    r"\blet'?s dive in\b",
    r"\bdive into\b",
    r"\blet'?s explore\b",
    r"\bin this article,? (?:we will|we'll|I will|I'll)\b",
    r"\bin this (?:comprehensive|detailed|in-depth) (?:guide|article|post)\b",
    r"\bwelcome to (?:this|our|my) (?:guide|article|post)\b",
]

# Tier 2 (WARNING): Corporate speak / AI-favorite words
AI_CLICHES_TIER2 = [
    r"\bleverage\b",
    r"\butilize\b",
    r"\bsynerg(?:y|ize|istic)\b",
    r"\binnovative\b",
    r"\bdeep dive\b",
    r"\bcircle back\b",
    r"\btouch base\b",
    r"\bmoving forward\b",
    r"\bat the end of the day\b",
    r"\bgame[- ]?changer\b",
    r"\bbest[- ]in[- ]class\b",
    r"\bcutting[- ]edge\b",
    r"\brobust (?:solution|platform|system)\b",
    r"\bseamless(?:ly)?\b",
    r"\bholistic (?:approach|solution|view)\b",
    r"\bparadigm shift\b",
    r"\bthought leader(?:ship)?\b",
    r"\bharness the power\b",
    r"\bunlock the (?:potential|power|full)\b",
    r"\btap into\b",
    r"\bdelve\b",
    r"\bnavigat(?:e|ing) the (?:complex|evolving)\b",
]

# Tier 3 (OPPORTUNITY): Weak hedging / vague AI padding
AI_CLICHES_TIER3 = [
    r"\bit'?s no secret that\b",
    r"\bthere are many ways to\b",
    r"\byou might want to consider\b",
    r"\bit could be argued that\b",
    r"\bsome experts believe\b",
    r"\bone could say\b",
    r"\bit goes without saying\b",
    r"\bneedless to say\b",
    r"\bwhen it comes to\b",
    r"\bin order to\b",
    r"\bthe fact (?:of the matter )?is\b",
]

# Combined flat list for backward compatibility (all tiers)
AI_CLICHES = AI_CLICHES_TIER1 + AI_CLICHES_TIER2 + AI_CLICHES_TIER3

# Filler words to flag (AA-22)
FILLER_WORDS = [
    "also", "actually", "basically", "really", "very",
    "quite", "rather", "somewhat", "simply", "just",
    "literally", "essentially", "obviously", "clearly",
    "definitely", "certainly", "absolutely", "honestly",
]

# Back-reference patterns (AA-23)
BACK_REFERENCES = [
    r"\bas mentioned\b",
    r"\bas (?:shown|discussed|noted|stated|described) (?:above|earlier|previously|before)\b",
    r"\bin the previous section\b",
    r"\bas we (?:saw|discussed|mentioned|noted)\b",
    r"\brecall that\b",
    r"\bas per the above\b",
]

# Vague quantifiers (AA-13)
VAGUE_QUANTIFIERS = [
    r"\bmany\b", r"\bseveral\b", r"\ba lot\b", r"\bnumerous\b",
    r"\bvarious\b", r"\bcountless\b", r"\ba number of\b",
    r"\bsome\b", r"\bfew\b", r"\ba handful\b",
]

# Default LLM model for Four U's scoring
DEFAULT_LLM_MODEL = "qwen-plus"


# ── Agency-configurable getter functions ──────────────────────────────────
# These check harness.yaml overrides first, fall back to the built-in constants above.
# Called at score time (not import time) to support hot-reload.

import logging as _logging
_qlog = _logging.getLogger("quality-config")

def _get_quality_overrides() -> dict:
    """Get quality overrides from harness.yaml via harness_config."""
    try:
        from scripts.harness_config import get_config
        return get_config().quality_overrides or {}
    except Exception:
        return {}


def _remap_weight_keys(raw: dict) -> dict:
    """Map harness.yaml short keys to Category enum values."""
    key_map = {
        "algorithmic_authorship": "Algorithmic Authorship",
        "geo_signals": "GEO/AEO Signals",
        "content_structure": "Content Structure",
        "four_us": "Four U's",
    }
    return {key_map.get(k, k): v for k, v in raw.items()}


def get_category_weights() -> dict:
    """Category weights — checks harness.yaml, falls back to built-in CATEGORY_WEIGHTS."""
    overrides = _get_quality_overrides()
    raw_weights = overrides.get("weights")
    if raw_weights and isinstance(raw_weights, dict):
        remapped = _remap_weight_keys(raw_weights)
        # Validate sum
        total = sum(remapped.values())
        if abs(total - 1.0) > 0.01:
            _qlog.warning("harness.yaml weights sum to %.3f (expected 1.0) — normalizing", total)
            remapped = {k: v / total for k, v in remapped.items()}
        return remapped
    return dict(CATEGORY_WEIGHTS)


def get_category_weights_no_llm() -> dict:
    """Weights when LLM rules disabled — derived from get_category_weights() minus Four U's."""
    weights = get_category_weights()
    no_llm = {k: v for k, v in weights.items() if k != "Four U's"}
    total = sum(no_llm.values())
    if total > 0:
        no_llm = {k: v / total for k, v in no_llm.items()}
    return no_llm if no_llm else dict(CATEGORY_WEIGHTS_NO_LLM)


def get_structure_targets() -> dict:
    """Structure targets — checks harness.yaml, falls back to built-in STRUCTURE_TARGETS."""
    overrides = _get_quality_overrides()
    raw = overrides.get("structure")
    if raw and isinstance(raw, dict):
        # Merge with defaults — agency only needs to override what they change
        merged = dict(STRUCTURE_TARGETS)
        # Map harness.yaml keys to internal keys
        yaml_to_internal = {
            "target_reading_level": None,  # Special handling: [min, max] → two keys
        }
        for k, v in raw.items():
            if k == "target_reading_level" and isinstance(v, list) and len(v) == 2:
                merged["target_reading_level_min"] = v[0]
                merged["target_reading_level_max"] = v[1]
            elif k in merged:
                merged[k] = v
        return merged
    return dict(STRUCTURE_TARGETS)


def get_geo_targets() -> dict:
    """GEO signal targets — checks harness.yaml, falls back to built-in GEO_TARGETS."""
    overrides = _get_quality_overrides()
    raw = overrides.get("geo")
    if raw and isinstance(raw, dict):
        merged = dict(GEO_TARGETS)
        merged.update({k: v for k, v in raw.items() if k in merged})
        return merged
    return dict(GEO_TARGETS)


def _merge_pattern_tier(override, defaults: list) -> list:
    """Merge a single tier of banned patterns with agency overrides.

    override can be:
      "default"              → return defaults unchanged
      []                     → disable this tier
      ["pat1", "pat2"]       → replace defaults entirely
      {remove: [...], add: [...]} → surgical override
    """
    if override == "default" or override is None:
        return list(defaults)
    if isinstance(override, list):
        return override  # Full replacement (empty list = disabled)
    if isinstance(override, dict):
        result = list(defaults)
        for pattern in override.get("remove", []):
            # Remove by substring match (agencies specify the word, not the regex)
            result = [r for r in result if pattern.lower() not in r.lower()]
        for pattern in override.get("add", []):
            # Add as word-boundary regex if it's a plain word
            if not pattern.startswith(r"\b"):
                pattern = rf"\b{pattern}\b"
            result.append(pattern)
        return result
    return list(defaults)


def get_banned_patterns_tier1() -> list:
    """Tier 1 (blocking) banned patterns — merged with harness.yaml overrides."""
    overrides = _get_quality_overrides()
    bp = overrides.get("banned_patterns", {})
    return _merge_pattern_tier(bp.get("tier1", "default"), AI_CLICHES_TIER1)


def get_banned_patterns_tier2() -> list:
    """Tier 2 (warning) banned patterns — merged with harness.yaml overrides."""
    overrides = _get_quality_overrides()
    bp = overrides.get("banned_patterns", {})
    return _merge_pattern_tier(bp.get("tier2", "default"), AI_CLICHES_TIER2)


def get_banned_patterns_tier3() -> list:
    """Tier 3 (opportunity) banned patterns — merged with harness.yaml overrides."""
    overrides = _get_quality_overrides()
    bp = overrides.get("banned_patterns", {})
    return _merge_pattern_tier(bp.get("tier3", "default"), AI_CLICHES_TIER3)


def get_filler_words() -> list:
    """Filler words — checks harness.yaml, falls back to built-in FILLER_WORDS."""
    overrides = _get_quality_overrides()
    raw = overrides.get("filler_words", "default")
    if raw == "default" or raw is None:
        return list(FILLER_WORDS)
    if isinstance(raw, list):
        return raw
    return list(FILLER_WORDS)


def get_back_references() -> list:
    """Back-reference patterns — checks harness.yaml, falls back to built-in."""
    overrides = _get_quality_overrides()
    raw = overrides.get("back_references", "default")
    if raw == "default" or raw is None:
        return list(BACK_REFERENCES)
    if isinstance(raw, list):
        return raw
    return list(BACK_REFERENCES)


def get_vague_quantifiers() -> list:
    """Vague quantifier patterns — checks harness.yaml, falls back to built-in."""
    overrides = _get_quality_overrides()
    raw = overrides.get("vague_quantifiers", "default")
    if raw == "default" or raw is None:
        return list(VAGUE_QUANTIFIERS)
    if isinstance(raw, list):
        return raw
    return list(VAGUE_QUANTIFIERS)

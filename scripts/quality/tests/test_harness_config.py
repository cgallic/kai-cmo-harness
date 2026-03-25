"""Tests for harness.yaml agency configuration overrides."""

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def _with_harness_yaml(yaml_content: str):
    """Context manager that sets HARNESS_CONFIG to a temp file with given content."""
    import contextlib

    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(yaml_content)
            f.flush()
            old = os.environ.get("HARNESS_CONFIG")
            os.environ["HARNESS_CONFIG"] = f.name
            # Reset the singleton so it reloads
            import scripts.harness_config as hc
            hc._config = None
            try:
                yield f.name
            finally:
                if old is None:
                    os.environ.pop("HARNESS_CONFIG", None)
                else:
                    os.environ["HARNESS_CONFIG"] = old
                hc._config = None
                try:
                    os.unlink(f.name)
                except OSError:
                    pass  # Windows file lock — temp dir cleans up later
    return ctx()


def test_no_harness_yaml_returns_defaults():
    """Without harness.yaml, all getters return built-in defaults."""
    old = os.environ.pop("HARNESS_CONFIG", None)
    import scripts.harness_config as hc
    hc._config = None
    try:
        from scripts.quality.config import (
            get_category_weights, get_structure_targets, get_geo_targets,
            get_banned_patterns_tier1, get_filler_words,
            CATEGORY_WEIGHTS, STRUCTURE_TARGETS, GEO_TARGETS, AI_CLICHES_TIER1, FILLER_WORDS,
        )
        assert get_category_weights() == CATEGORY_WEIGHTS
        assert get_structure_targets() == STRUCTURE_TARGETS
        assert get_geo_targets() == GEO_TARGETS
        assert get_banned_patterns_tier1() == AI_CLICHES_TIER1
        assert get_filler_words() == FILLER_WORDS
        print("PASS: No harness.yaml returns defaults")
    finally:
        if old:
            os.environ["HARNESS_CONFIG"] = old
        hc._config = None


def test_category_weights_override():
    """harness.yaml can override category weights."""
    yaml = """
quality:
  weights:
    algorithmic_authorship: 0.50
    geo_signals: 0.10
    content_structure: 0.25
    four_us: 0.15
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_category_weights
        w = get_category_weights()
        assert w["Algorithmic Authorship"] == 0.50
        assert w["GEO/AEO Signals"] == 0.10
        assert w["Content Structure"] == 0.25
        assert w["Four U's"] == 0.15
        print("PASS: Category weights override")


def test_weights_normalization():
    """Weights that don't sum to 1.0 get normalized."""
    yaml = """
quality:
  weights:
    algorithmic_authorship: 2.0
    geo_signals: 1.0
    content_structure: 1.0
    four_us: 1.0
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_category_weights
        w = get_category_weights()
        total = sum(w.values())
        assert abs(total - 1.0) < 0.01, f"Weights should be normalized: {total}"
        assert abs(w["Algorithmic Authorship"] - 0.4) < 0.01
        print("PASS: Weights normalization")


def test_banned_patterns_add_remove():
    """Tier2 add/remove merge works correctly."""
    yaml = """
quality:
  banned_patterns:
    tier2:
      remove: ["leverage"]
      add: ["disrupt", "pivot"]
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_banned_patterns_tier2
        t2 = get_banned_patterns_tier2()
        assert not any("leverage" in p.lower() for p in t2), "leverage should be removed"
        assert any("disrupt" in p.lower() for p in t2), "disrupt should be added"
        assert any("pivot" in p.lower() for p in t2), "pivot should be added"
        print("PASS: Banned patterns add/remove")


def test_banned_patterns_disable_tier():
    """Setting a tier to [] disables it entirely."""
    yaml = """
quality:
  banned_patterns:
    tier3: []
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_banned_patterns_tier3
        t3 = get_banned_patterns_tier3()
        assert len(t3) == 0, f"Tier 3 should be empty: {t3}"
        print("PASS: Disable tier with empty list")


def test_structure_targets_partial_merge():
    """Partial structure override merges with defaults."""
    yaml = """
quality:
  structure:
    max_words_between_headings: 500
    target_reading_level: [4, 10]
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_structure_targets
        st = get_structure_targets()
        assert st["max_words_between_headings"] == 500, "Override should apply"
        assert st["target_reading_level_min"] == 4, "Reading level min from list"
        assert st["target_reading_level_max"] == 10, "Reading level max from list"
        assert st["min_paragraph_sentences"] == 2, "Default should be preserved"
        assert st["you_your_ratio_target"] == 2.0, "Default should be preserved"
        print("PASS: Structure targets partial merge")


def test_geo_targets_override():
    """GEO targets can be partially overridden."""
    yaml = """
quality:
  geo:
    citations: 10
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_geo_targets
        geo = get_geo_targets()
        assert geo["citations"] == 10, "Override should apply"
        assert geo["quotations"] == 3, "Default should be preserved"
        print("PASS: GEO targets override")


def test_malformed_yaml_returns_defaults():
    """Malformed harness.yaml gracefully falls back to defaults."""
    yaml = "quality:\n  weights: [invalid: yaml: structure"
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_category_weights, CATEGORY_WEIGHTS
        w = get_category_weights()
        assert w == CATEGORY_WEIGHTS, "Should fall back to defaults on bad YAML"
        print("PASS: Malformed YAML returns defaults")


def test_env_var_override_path():
    """HARNESS_CONFIG env var points to alternate config file."""
    yaml = """
quality:
  geo:
    statistics: 20
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_geo_targets
        geo = get_geo_targets()
        assert geo["statistics"] == 20, f"Expected 20: {geo}"
        print("PASS: HARNESS_CONFIG env var override")


def test_filler_words_custom_list():
    """Custom filler words list replaces defaults."""
    yaml = """
quality:
  filler_words: ["um", "uh", "like"]
"""
    with _with_harness_yaml(yaml):
        from scripts.quality.config import get_filler_words
        fw = get_filler_words()
        assert fw == ["um", "uh", "like"], f"Expected custom list: {fw}"
        print("PASS: Custom filler words list")


if __name__ == "__main__":
    test_no_harness_yaml_returns_defaults()
    test_category_weights_override()
    test_weights_normalization()
    test_banned_patterns_add_remove()
    test_banned_patterns_disable_tier()
    test_structure_targets_partial_merge()
    test_geo_targets_override()
    test_malformed_yaml_returns_defaults()
    test_env_var_override_path()
    test_filler_words_custom_list()
    print("\nAll harness config tests passed!")

"""Tests for the canonical provider-agnostic LLM client (scripts/llm_client.py).

Doctrine under test (memory/lessons.md): every LLM call site routes through
this client, so any provider key works anywhere — gates, writers, extractors.
Resolution logic only; live calls are exercised by the pipelines themselves.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import llm_client


class TestModelPrecedence:
    def test_kai_llm_model_beats_overrides(self):
        env = {"GEMINI_API_KEY": "g", "KAI_LLM_MODEL": "gemini-2.5-pro"}
        provider, model = llm_client.resolve_provider(
            env=env, model_overrides={"gemini": "gemini-2.0-flash"}
        )
        assert (provider, model) == ("gemini", "gemini-2.5-pro")

    def test_override_beats_default_for_resolved_provider(self):
        env = {"GEMINI_API_KEY": "g"}
        _, model = llm_client.resolve_provider(
            env=env, model_overrides={"gemini": "gemini-2.0-flash-lite"}
        )
        assert model == "gemini-2.0-flash-lite"

    def test_override_for_other_provider_ignored(self):
        env = {"ANTHROPIC_API_KEY": "a"}
        provider, model = llm_client.resolve_provider(
            env=env, model_overrides={"openai": "gpt-4o", "gemini": "gemini-2.0-flash"}
        )
        assert provider == "anthropic"
        assert model == llm_client.DEFAULT_MODELS["anthropic"]

    def test_defaults_when_nothing_set(self):
        for provider, key in llm_client.PROVIDER_KEYS.items():
            _, model = llm_client.resolve_provider(env={key: "x"})
            assert model == llm_client.DEFAULT_MODELS[provider]


class TestJudgeShim:
    """The quality-gate shim must stay a re-export, never a fork."""

    def _load_shim(self):
        spec = importlib.util.spec_from_file_location(
            "llm_judge_shim",
            REPO_ROOT / "scripts" / "quality_gates" / "llm_judge.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_shim_reexports_canonical_objects(self):
        shim = self._load_shim()
        assert shim.complete is llm_client.complete
        assert shim.resolve_provider is llm_client.resolve_provider
        assert shim.JudgeConfigError is llm_client.LLMConfigError

    def test_error_alias(self):
        assert llm_client.JudgeConfigError is llm_client.LLMConfigError


class TestCallSitesRouteThroughClient:
    """No module in the content/learning pipeline may import a vendor SDK directly."""

    PIPELINE_FILES = [
        "scripts/content/engine.py",
        "scripts/content/_writer.py",
        "scripts/content/linkedin_article_writer.py",
        "scripts/content/tiktok_content_generator.py",
        "scripts/self_improvement/pattern_extract.py",
        "scripts/self_improvement/social_import.py",
        "scripts/harness_cli.py",
        "scripts/quality_gates/four_us_score.py",
        "scripts/reddit_monitor/reddit_listener.py",
        "scripts/reddit_monitor/reddit_digest.py",
    ]

    VENDOR_IMPORTS = [
        "from google import genai",
        "import google.genai",
        "from openai import OpenAI",
        "import openai",
        "import anthropic",
        "from anthropic import",
    ]

    @pytest.mark.parametrize("rel_path", PIPELINE_FILES)
    def test_no_direct_vendor_imports(self, rel_path):
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for vendor_import in self.VENDOR_IMPORTS:
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith(vendor_import):
                    pytest.fail(
                        f"{rel_path} imports a vendor SDK directly ({stripped!r}) — "
                        "route through scripts/llm_client.py instead "
                        "(memory/lessons.md, provider-agnostic rule)"
                    )

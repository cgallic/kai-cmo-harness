"""Tests for the provider-agnostic LLM judge client.

Covers provider/model resolution only — actual API calls need credentials and
are exercised by the gates themselves. See memory/lessons.md: LLM-judged gates
must run with whatever provider the operator has, not one hard-coded vendor.
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "llm_judge", REPO_ROOT / "scripts" / "quality_gates" / "llm_judge.py"
)
llm_judge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(llm_judge)


class TestResolveProvider:
    def test_no_keys_raises_with_guidance(self):
        with pytest.raises(llm_judge.JudgeConfigError) as exc:
            llm_judge.resolve_provider(env={})
        msg = str(exc.value)
        assert "GEMINI_API_KEY" in msg and "ANTHROPIC_API_KEY" in msg and "OPENAI_API_KEY" in msg
        assert "offline gates" in msg

    def test_gemini_detected_first_for_backward_compat(self):
        env = {"GEMINI_API_KEY": "g", "ANTHROPIC_API_KEY": "a", "OPENAI_API_KEY": "o"}
        assert llm_judge.resolve_provider(env=env) == ("gemini", "gemini-2.0-flash")

    def test_anthropic_detected_when_only_key(self):
        provider, model = llm_judge.resolve_provider(env={"ANTHROPIC_API_KEY": "a"})
        assert provider == "anthropic"
        assert model == "claude-opus-4-8"

    def test_openai_detected_when_only_key(self):
        provider, model = llm_judge.resolve_provider(env={"OPENAI_API_KEY": "o"})
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_explicit_provider_overrides_detection_order(self):
        env = {
            "KAI_LLM_PROVIDER": "anthropic",
            "GEMINI_API_KEY": "g",
            "ANTHROPIC_API_KEY": "a",
        }
        assert llm_judge.resolve_provider(env=env)[0] == "anthropic"

    def test_explicit_provider_without_its_key_raises(self):
        env = {"KAI_LLM_PROVIDER": "openai", "GEMINI_API_KEY": "g"}
        with pytest.raises(llm_judge.JudgeConfigError) as exc:
            llm_judge.resolve_provider(env=env)
        assert "OPENAI_API_KEY" in str(exc.value)

    def test_unknown_provider_raises(self):
        with pytest.raises(llm_judge.JudgeConfigError):
            llm_judge.resolve_provider(env={"KAI_LLM_PROVIDER": "grok"})

    def test_model_override(self):
        env = {"ANTHROPIC_API_KEY": "a", "KAI_LLM_MODEL": "claude-haiku-4-5"}
        assert llm_judge.resolve_provider(env=env) == ("anthropic", "claude-haiku-4-5")

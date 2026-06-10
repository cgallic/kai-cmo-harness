#!/usr/bin/env python3
"""
LLM judge client — provider-agnostic completion for LLM-judged quality gates.

The Four U's scorer (and any future LLM-judged gate) should run with whatever
LLM provider the operator already has a key for, not require Gemini
specifically. This module picks a provider and returns plain text.

Provider selection:
  1. KAI_LLM_PROVIDER env var if set: "gemini" | "anthropic" | "openai"
  2. Otherwise auto-detect, first key found wins:
     GEMINI_API_KEY -> gemini, ANTHROPIC_API_KEY -> anthropic,
     OPENAI_API_KEY -> openai
     (Gemini first for backward compatibility with existing deployments.)

Model selection: KAI_LLM_MODEL overrides the per-provider default below.

SDKs are imported lazily — only the chosen provider's package is needed.
"""

from __future__ import annotations

import os

DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o-mini",
}

PROVIDER_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

PROVIDER_PACKAGES = {
    "gemini": "google-genai",
    "anthropic": "anthropic",
    "openai": "openai",
}


class JudgeConfigError(Exception):
    """Raised when no usable LLM provider is configured. Message is operator-facing."""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv("/opt/cmo-analytics/.env")
        load_dotenv()
    except ImportError:
        pass


def resolve_provider(env: dict | None = None) -> tuple[str, str]:
    """Return (provider, model) from the environment. Raises JudgeConfigError."""
    env = env if env is not None else os.environ

    provider = env.get("KAI_LLM_PROVIDER", "").strip().lower()
    if provider:
        if provider not in PROVIDER_KEYS:
            raise JudgeConfigError(
                f"KAI_LLM_PROVIDER={provider!r} is not supported. "
                f"Use one of: {', '.join(PROVIDER_KEYS)}."
            )
        if not env.get(PROVIDER_KEYS[provider]):
            raise JudgeConfigError(
                f"KAI_LLM_PROVIDER={provider} but {PROVIDER_KEYS[provider]} is not set."
            )
    else:
        provider = next(
            (p for p, key in PROVIDER_KEYS.items() if env.get(key)), ""
        )
        if not provider:
            raise JudgeConfigError(
                "No LLM provider configured for LLM-judged gates. Set one of "
                "GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY "
                "(optionally pin with KAI_LLM_PROVIDER / KAI_LLM_MODEL). "
                "The offline gates (banned_word_check.py, seo_lint.py) run without any key."
            )

    model = env.get("KAI_LLM_MODEL", "").strip() or DEFAULT_MODELS[provider]
    return provider, model


def complete(prompt: str, max_tokens: int = 2048) -> str:
    """Run a single text completion against the configured provider."""
    _load_dotenv()
    provider, model = resolve_provider()

    try:
        if provider == "gemini":
            return _complete_gemini(prompt, model)
        if provider == "anthropic":
            return _complete_anthropic(prompt, model, max_tokens)
        return _complete_openai(prompt, model, max_tokens)
    except ImportError:
        raise JudgeConfigError(
            f"The {provider!r} provider is selected but its package is not "
            f"installed. Run: pip install {PROVIDER_PACKAGES[provider]}"
        ) from None


def _complete_gemini(prompt: str, model: str) -> str:
    from google import genai as google_genai

    client = google_genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()


def _complete_anthropic(prompt: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()


def _complete_openai(prompt: str, model: str, max_tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return (response.choices[0].message.content or "").strip()

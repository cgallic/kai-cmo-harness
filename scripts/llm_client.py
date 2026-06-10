#!/usr/bin/env python3
"""
LLM client — the single, provider-agnostic gateway for every LLM call in the
harness (gates, writers, pattern extraction, scoring, briefs).

Doctrine (memory/lessons.md): never hard-code a single LLM vendor. Any module
that needs a completion imports this and runs with whatever provider key the
operator has.

Provider selection:
  1. KAI_LLM_PROVIDER env var if set: "gemini" | "anthropic" | "openai"
  2. Otherwise auto-detect, first key found wins:
     GEMINI_API_KEY -> gemini, ANTHROPIC_API_KEY -> anthropic,
     OPENAI_API_KEY -> openai
     (Gemini first for backward compatibility with existing deployments.)

Model selection (first match wins):
  explicit `model` arg > KAI_LLM_MODEL env > caller's `model_overrides` for
  the resolved provider (legacy per-provider config) > per-provider default.

SDKs import lazily — only the chosen provider's package must be installed.

Known exemption: scripts/knowledge_cloner/ stays Gemini-pinned because it
uses Gemini-native audio/video transcription (multimodal), which the other
providers don't expose the same way. See memory/edge-cases.md EC-19.
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

JSON_ONLY_INSTRUCTION = (
    "\n\nReturn ONLY a valid JSON object. No prose, no markdown fences, "
    "no explanation outside the JSON."
)


class LLMConfigError(Exception):
    """Raised when no usable LLM provider is configured. Message is operator-facing."""


# Backward-compatible alias (the judge client raised this name first)
JudgeConfigError = LLMConfigError


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv("/opt/cmo-analytics/.env")
        load_dotenv()
    except ImportError:
        pass


def resolve_provider(
    env: dict | None = None, model_overrides: dict | None = None
) -> tuple[str, str]:
    """Return (provider, model) from the environment. Raises LLMConfigError.

    model_overrides maps provider name -> model id, letting callers carry
    legacy per-provider config (e.g. harness_config.gemini_model) without
    pinning the provider itself.
    """
    env = env if env is not None else os.environ

    provider = env.get("KAI_LLM_PROVIDER", "").strip().lower()
    if provider:
        if provider not in PROVIDER_KEYS:
            raise LLMConfigError(
                f"KAI_LLM_PROVIDER={provider!r} is not supported. "
                f"Use one of: {', '.join(PROVIDER_KEYS)}."
            )
        if not env.get(PROVIDER_KEYS[provider]):
            raise LLMConfigError(
                f"KAI_LLM_PROVIDER={provider} but {PROVIDER_KEYS[provider]} is not set."
            )
    else:
        provider = next(
            (p for p, key in PROVIDER_KEYS.items() if env.get(key)), ""
        )
        if not provider:
            raise LLMConfigError(
                "No LLM provider configured. Set one of "
                "GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY "
                "(optionally pin with KAI_LLM_PROVIDER / KAI_LLM_MODEL). "
                "The offline gates (banned_word_check.py, seo_lint.py) run without any key."
            )

    model = (
        env.get("KAI_LLM_MODEL", "").strip()
        or (model_overrides or {}).get(provider, "")
        or DEFAULT_MODELS[provider]
    )
    return provider, model


def complete(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 2048,
    timeout: float | None = None,
    json_only: bool = False,
    model_overrides: dict | None = None,
) -> str:
    """Run a single text completion against the configured provider.

    timeout is in seconds. max_tokens applies to Anthropic/OpenAI; Gemini
    uses its model default to preserve legacy behavior. There is no
    temperature knob — current frontier models reject sampling params, so
    steer style through the prompt instead.
    """
    _load_dotenv()
    provider, resolved_model = resolve_provider(model_overrides=model_overrides)
    if model:
        resolved_model = model

    try:
        if provider == "gemini":
            return _complete_gemini(prompt, system, resolved_model, timeout, json_only)
        if provider == "anthropic":
            return _complete_anthropic(prompt, system, resolved_model, max_tokens, timeout, json_only)
        return _complete_openai(prompt, system, resolved_model, max_tokens, timeout, json_only)
    except ImportError:
        raise LLMConfigError(
            f"The {provider!r} provider is selected but its package is not "
            f"installed. Run: pip install {PROVIDER_PACKAGES[provider]}"
        ) from None


def make_llm_fn(**defaults):
    """Return a `fn(prompt) -> str` with baked-in defaults.

    This is the injection point for code that takes an LLM callable
    (e.g. scripts/content/_writer.py).
    """

    def call(prompt: str) -> str:
        return complete(prompt, **defaults)

    return call


def _complete_gemini(
    prompt: str, system: str | None, model: str, timeout: float | None, json_only: bool
) -> str:
    from google import genai as google_genai

    http_options = {"timeout": int(timeout * 1000)} if timeout else None
    client = google_genai.Client(
        api_key=os.environ["GEMINI_API_KEY"], http_options=http_options
    )
    config: dict = {}
    if system:
        config["system_instruction"] = system
    if json_only:
        config["response_mime_type"] = "application/json"
    response = client.models.generate_content(
        model=model, contents=prompt, config=config or None
    )
    return response.text.strip()


def _complete_anthropic(
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int,
    timeout: float | None,
    json_only: bool,
) -> str:
    import anthropic

    client = anthropic.Anthropic(timeout=timeout) if timeout else anthropic.Anthropic()
    if json_only:
        prompt = prompt + JSON_ONLY_INSTRUCTION
    kwargs = {}
    if system:
        kwargs["system"] = system
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
    if json_only and text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.strip().startswith("```")
        ).strip()
    return text


def _complete_openai(
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int,
    timeout: float | None,
    json_only: bool,
) -> str:
    from openai import OpenAI

    client = OpenAI(timeout=timeout) if timeout else OpenAI()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs = {}
    if json_only:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=max_tokens,
        messages=messages,
        **kwargs,
    )
    return (response.choices[0].message.content or "").strip()

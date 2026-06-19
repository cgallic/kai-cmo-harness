"""
LLM model router for autonomous agent tasks.

Provider selection order:
- OpenRouter when ``OPENROUTER_API_KEY`` is set
- OpenAI when ``OPENAI_API_KEY`` is set
- Gemini when ``GEMINI_API_KEY`` is set
- Anthropic when ``ANTHROPIC_API_KEY`` is set

The public API stays small: ``complete()`` and ``chat()`` return plain text
and the router normalizes usage metadata across providers where possible.
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import os
from contextlib import nullcontext
import requests

try:
    from openai import OpenAI as _OpenAIClient
except ImportError:  # pragma: no cover - validated by dependency wiring/tests
    _OpenAIClient = None

try:
    from google import genai as _google_genai
except ImportError:  # pragma: no cover - optional provider
    _google_genai = None

if TYPE_CHECKING:
    from openai import OpenAI
else:  # pragma: no cover - typing fallback only
    OpenAI = Any  # type: ignore[misc,assignment]

from ..config import agent_config
from ..traces import SpanKind, tracer
from ..traces import recorder


class ModelTier(str, Enum):
    """Model tiers for different task complexities."""
    CHEAP = "cheap"
    SMART = "smart"


# Task type to model tier mapping
TASK_MODEL_MAP = {
    # Cheap tasks (routine, structured)
    "daily_analytics": ModelTier.CHEAP,
    "warmup_check": ModelTier.CHEAP,
    "lead_outreach": ModelTier.CHEAP,
    "content_pipeline": ModelTier.CHEAP,
    "seo_optimization": ModelTier.CHEAP,
    "ad_management": ModelTier.CHEAP,

    # Smart tasks (complex reasoning)
    "weekly_report": ModelTier.SMART,
    "strategy_analysis": ModelTier.SMART,
    "content_quality_review": ModelTier.SMART,

    # Kai Calls tasks
    "kai_call_processor": ModelTier.SMART,  # Needs reasoning for transcript analysis
    "kai_followup": ModelTier.CHEAP,
    "kai_business_ops": ModelTier.CHEAP,
    "kai_business_ops_weekly": ModelTier.CHEAP,
    "kai_onboarding": ModelTier.CHEAP,
    "kai_task_board": ModelTier.CHEAP,

    # BuildWithKai tasks
    "bwk_generation_monitor": ModelTier.CHEAP,
    "bwk_user_activation": ModelTier.CHEAP,
    "bwk_revenue_monitor": ModelTier.CHEAP,
    "bwk_business_ops": ModelTier.CHEAP,
    "bwk_business_ops_weekly": ModelTier.CHEAP,
    "bwk_quality_auditor": ModelTier.SMART,  # Needs reasoning for content QA

    # Amazing Backyard Parties tasks
    "abp_lead_processor": ModelTier.SMART,  # Needs reasoning for lead analysis
    "abp_vendor_health": ModelTier.CHEAP,
    "abp_business_ops": ModelTier.CHEAP,
    "abp_business_ops_weekly": ModelTier.CHEAP,
    "abp_seo_monitor": ModelTier.CHEAP,
}

OPENAI_COMPATIBLE_PROVIDERS = {"openrouter", "openai"}
PROVIDER_KEY_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
PROVIDER_PRIORITY = ("openrouter", "openai", "gemini", "anthropic")
DEFAULT_MODELS = {
    "openrouter": {
        ModelTier.CHEAP: "google/gemini-2.0-flash-001",
        ModelTier.SMART: "anthropic/claude-3.5-sonnet",
    },
    "openai": {
        ModelTier.CHEAP: "gpt-4.1-mini",
        ModelTier.SMART: "gpt-4.1",
    },
    "gemini": {
        ModelTier.CHEAP: "gemini-2.0-flash-001",
        ModelTier.SMART: "gemini-1.5-pro",
    },
    "anthropic": {
        ModelTier.CHEAP: "claude-3-5-haiku-latest",
        ModelTier.SMART: "claude-3-5-sonnet-latest",
    },
}
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class LLMRouter:
    """
    Routes LLM requests across supported providers.
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._provider: Optional[str] = None
        self._client_provider: Optional[str] = None

    @property
    def client(self) -> OpenAI:
        """Lazy initialization for OpenAI-compatible providers."""
        provider = self._detect_provider()
        if provider not in OPENAI_COMPATIBLE_PROVIDERS:
            raise ValueError(
                f"Provider '{provider}' is not OpenAI-compatible. "
                "Use complete()/chat() instead of client directly."
            )
        if self._client is None or self._client_provider != provider:
            if _OpenAIClient is None:
                raise ImportError(
                    "openai package is required for OpenRouter/OpenAI agent routing. "
                    "Install scripts/requirements.txt."
                )
            api_key = os.getenv(PROVIDER_KEY_ENV[provider], "").strip()
            if not api_key:
                raise ValueError(f"{PROVIDER_KEY_ENV[provider]} not set")

            client_kwargs: Dict[str, Any] = {"api_key": api_key}
            if provider == "openrouter":
                client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            elif os.getenv("OPENAI_BASE_URL"):
                client_kwargs["base_url"] = os.getenv("OPENAI_BASE_URL")

            self._client = _OpenAIClient(**client_kwargs)
            self._client_provider = provider
        return self._client

    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model ID for a task type."""
        tier = TASK_MODEL_MAP.get(task_type, ModelTier.CHEAP)
        return self._tier_to_model(tier)

    def _tier_to_model(self, tier: ModelTier) -> str:
        """Convert model tier to actual model ID."""
        env_var = "AGENT_SMART_MODEL" if tier == ModelTier.SMART else "AGENT_CHEAP_MODEL"
        configured = os.getenv(env_var, "").strip()
        if configured:
            return configured
        provider = self._detect_provider()
        return DEFAULT_MODELS[provider][tier]

    def _default_model(self) -> str:
        """Return the default model when no task-specific tier is requested."""
        configured = os.getenv("AGENT_DEFAULT_MODEL", "").strip()
        if configured:
            return configured
        return self._tier_to_model(ModelTier.CHEAP)

    def _detect_provider(self) -> str:
        """Return the active provider based on env vars or explicit override."""
        if self._provider:
            return self._provider
        if self._client is not None and self._client_provider:
            self._provider = self._client_provider
            return self._provider
        if self._client is not None:
            self._provider = "openrouter"
            self._client_provider = "openrouter"
            return self._provider

        explicit = os.getenv("AGENT_LLM_PROVIDER", "").strip().lower()
        if explicit:
            if explicit not in PROVIDER_KEY_ENV:
                raise ValueError(
                    f"Unsupported AGENT_LLM_PROVIDER '{explicit}'. "
                    f"Expected one of: {', '.join(PROVIDER_KEY_ENV)}"
                )
            key_name = PROVIDER_KEY_ENV[explicit]
            if not os.getenv(key_name, "").strip():
                raise ValueError(f"{key_name} not set for AGENT_LLM_PROVIDER={explicit}")
            self._provider = explicit
            return explicit

        for provider in PROVIDER_PRIORITY:
            if os.getenv(PROVIDER_KEY_ENV[provider], "").strip():
                self._provider = provider
                return provider

        raise ValueError(
            "No LLM provider API key set. Set one of OPENROUTER_API_KEY, "
            "OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY."
        )

    @staticmethod
    def _message_text(messages: List[Dict[str, str]]) -> str:
        """Flatten messages into plain text for providers without chat parity."""
        lines: List[str] = []
        for message in messages:
            role = message.get("role", "user").upper()
            lines.append(f"{role}:\n{message.get('content', '')}")
        return "\n\n".join(lines)

    def _complete_openai_compatible(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        messages: List[Dict[str, str]],
    ) -> tuple[str, Any, Any]:
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        finish_reason = getattr(response.choices[0], "finish_reason", None)
        return content, usage, finish_reason

    def _complete_gemini(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        messages: List[Dict[str, str]],
    ) -> tuple[str, Dict[str, int], Optional[str]]:
        if _google_genai is None:
            raise ImportError(
                "google-genai package is required for Gemini agent routing. "
                "Install scripts/requirements.txt."
            )

        client = _google_genai.Client(api_key=os.getenv("GEMINI_API_KEY", "").strip())
        response = client.models.generate_content(
            model=model,
            contents=self._message_text(messages),
        )
        usage_meta = getattr(response, "usage_metadata", None)
        usage = {
            "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0,
            "completion_tokens": getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0,
            "total_tokens": getattr(usage_meta, "total_token_count", None) if usage_meta else None,
        }
        finish_reason = getattr(response, "finish_reason", None)
        return response.text.strip(), usage, finish_reason

    def _complete_anthropic(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        messages: List[Dict[str, str]],
    ) -> tuple[str, Dict[str, int], Optional[str]]:
        system_parts = [m["content"] for m in messages if m.get("role") == "system"]
        user_messages = [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in messages
            if m.get("role") != "system"
        ]
        if not user_messages:
            user_messages = [{"role": "user", "content": ""}]

        response = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY", "").strip(),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": "\n\n".join(system_parts) if system_parts else None,
                "messages": user_messages,
            },
            timeout=120,
        )
        response.raise_for_status()
        body = response.json()
        content = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        ).strip()
        usage_data = body.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("output_tokens", 0),
            "total_tokens": usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        }
        return content, usage, body.get("stop_reason")

    def _call_provider(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        messages: List[Dict[str, str]],
    ) -> tuple[str, Any, Any]:
        provider = self._detect_provider()
        if provider in OPENAI_COMPATIBLE_PROVIDERS:
            return self._complete_openai_compatible(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
        if provider == "gemini":
            return self._complete_gemini(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
        if provider == "anthropic":
            return self._complete_anthropic(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
        raise ValueError(f"Unsupported provider '{provider}'")

    async def complete(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        model_override: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        prompt_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Complete a prompt using the appropriate model.

        Args:
            prompt: The user prompt
            task_type: Task type for model selection
            model_override: Override automatic model selection
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            prompt_name: Identifier for the prompt template (for HALO).
            prompt_version: Optional version tag for the prompt template.

        Returns:
            Generated text response
        """
        # Select model
        if model_override:
            model = model_override
        elif task_type:
            model = self.get_model_for_task(task_type)
        else:
            model = self._default_model()

        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        recorder_active = recorder.current_trace_context().get("trace_id") is not None
        recorder_scope = (
            recorder.trace_span(
                "llm.complete",
                metadata={
                    "model": model,
                    "task_type": task_type,
                    "prompt_name": prompt_name,
                    "prompt_version": prompt_version,
                },
            )
            if recorder_active
            else nullcontext()
        )

        with recorder_scope as recorded_span:
            async with tracer.span(
                f"llm.complete:{prompt_name or task_type or 'unnamed'}",
                kind=SpanKind.LLM,
                inputs={
                    "model": model,
                    "task_type": task_type,
                    "prompt_name": prompt_name,
                    "prompt_version": prompt_version,
                    "prompt_chars": len(prompt),
                    "system_chars": len(system) if system else 0,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            ) as span:
                content, usage, finish_reason = self._call_provider(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                )
                input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                if isinstance(usage, dict):
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
                else:
                    output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                    total_tokens = (
                        getattr(usage, "total_tokens", input_tokens + output_tokens)
                        if usage
                        else None
                    )

                span.add_attributes(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=self.estimate_cost(input_tokens, output_tokens, model=model),
                    finish_reason=finish_reason,
                )
                span.set_output(content)
                if recorded_span is not None:
                    recorded_span.add_metadata(
                        token_usage={
                            "prompt_tokens": input_tokens,
                            "completion_tokens": output_tokens,
                            "total_tokens": total_tokens,
                        },
                    )
                    recorded_span.set_output(content)
                return content

    async def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: Optional[str] = None,
        model_override: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        prompt_name: Optional[str] = None,
        prompt_version: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Multi-turn conversation.

        Args:
            messages: List of {"role": "user"|"assistant", "content": str}
            task_type: Task type for model selection
            model_override: Override automatic model selection
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            prompt_name: Identifier for the prompt template (for HALO).
            prompt_version: Optional version tag for the prompt template.

        Returns:
            Assistant's response
        """
        # Select model
        if model_override:
            model = model_override
        elif task_type:
            model = self.get_model_for_task(task_type)
        else:
            model = self._default_model()

        # Prepend system message if provided
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        async with tracer.span(
            f"llm.chat:{prompt_name or task_type or 'unnamed'}",
            kind=SpanKind.LLM,
            inputs={
                "model": model,
                "task_type": task_type,
                "prompt_name": prompt_name,
                "prompt_version": prompt_version,
                "message_count": len(messages),
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        ) as span:
            content, usage, finish_reason = self._call_provider(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=full_messages,
            )
            if isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
            else:
                input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens) if usage else None

            span.add_attributes(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=self.estimate_cost(input_tokens, output_tokens, model=model),
                finish_reason=finish_reason,
            )
            span.set_output(content)
            return content

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> float:
        """
        Estimate cost for a request in USD.

        Returns:
            Estimated cost in USD
        """
        if model is None and task_type:
            model = self.get_model_for_task(task_type)
        elif model is None:
            model = self._default_model()

        # OpenRouter prices per million tokens
        prices = {
            "gemini": (0.10, 0.40),      # Very cheap
            "openai": (0.40, 1.60),      # gpt-4.1-mini ballpark
            "claude": (3.00, 15.00),     # Sonnet pricing
        }

        model_lower = model.lower()
        if "gemini" in model_lower:
            input_price, output_price = prices["gemini"]
        elif "gpt" in model_lower or "o4" in model_lower:
            input_price, output_price = prices["openai"]
        else:
            input_price, output_price = prices["claude"]

        cost = (input_tokens * input_price / 1_000_000) + (output_tokens * output_price / 1_000_000)
        return round(cost, 6)


# Global LLM router instance
llm_router = LLMRouter()

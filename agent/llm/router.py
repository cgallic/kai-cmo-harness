"""
LLM model router - uses OpenRouter for cheaper models.

Cost optimization strategy:
- Cheap: Gemini Flash (~$0.10/M input) for routine tasks
- Smart: Claude Sonnet for complex reasoning
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import os

from openai import OpenAI

from ..config import agent_config
from ..traces import SpanKind, tracer


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


class LLMRouter:
    """
    Routes LLM requests via OpenRouter for cost optimization.

    Uses cheap Gemini models by default (~$0.10/M tokens).
    """

    def __init__(self):
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenRouter client."""
        if self._client is None:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not set")
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
        return self._client

    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model ID for a task type."""
        tier = TASK_MODEL_MAP.get(task_type, ModelTier.CHEAP)
        return self._tier_to_model(tier)

    def _tier_to_model(self, tier: ModelTier) -> str:
        """Convert model tier to actual model ID."""
        if tier == ModelTier.SMART:
            return os.getenv("AGENT_SMART_MODEL", "anthropic/claude-3.5-sonnet")
        else:
            return os.getenv("AGENT_CHEAP_MODEL", "google/gemini-2.0-flash-001")

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
            model = os.getenv("AGENT_DEFAULT_MODEL", "google/gemini-2.0-flash-001")

        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

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
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )

            content = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

            span.add_attributes(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=getattr(usage, "total_tokens", input_tokens + output_tokens) if usage else None,
                estimated_cost_usd=self.estimate_cost(input_tokens, output_tokens, model=model),
                finish_reason=getattr(response.choices[0], "finish_reason", None),
            )
            span.set_output(content)
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
            model = os.getenv("AGENT_DEFAULT_MODEL", "google/gemini-2.0-flash-001")

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
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=full_messages,
            )

            content = response.choices[0].message.content
            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

            span.add_attributes(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=getattr(usage, "total_tokens", input_tokens + output_tokens) if usage else None,
                estimated_cost_usd=self.estimate_cost(input_tokens, output_tokens, model=model),
                finish_reason=getattr(response.choices[0], "finish_reason", None),
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
            model = os.getenv("AGENT_DEFAULT_MODEL", "google/gemini-2.0-flash-001")

        # OpenRouter prices per million tokens
        prices = {
            "gemini": (0.10, 0.40),      # Very cheap
            "claude": (3.00, 15.00),     # Sonnet pricing
        }

        model_lower = model.lower()
        if "gemini" in model_lower:
            input_price, output_price = prices["gemini"]
        else:
            input_price, output_price = prices["claude"]

        cost = (input_tokens * input_price / 1_000_000) + (output_tokens * output_price / 1_000_000)
        return round(cost, 6)


# Global LLM router instance
llm_router = LLMRouter()

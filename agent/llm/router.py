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

        # Make API call via OpenRouter
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )

        return response.choices[0].message.content

    async def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: Optional[str] = None,
        model_override: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
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

        # Make API call
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=full_messages
        )

        return response.choices[0].message.content

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

"""Shared provider execution for brief, writing, revision and editorial judging.

Keeps the legacy synchronous callable injection interface. Calls retain a stage,
prompt hash, usage, model and latency. No model output triggers an external write.
"""
from __future__ import annotations

import hashlib
import os
import time

from .router import LLMRouter


class ContentClient:
    def __init__(self, task="content_pipeline", *, model=None, router=None, events=None):
        self.task = task
        self.model = model
        if router is None:
            from scripts.harness_config import get_config
            cfg = get_config()
            router = LLMRouter(timeout=cfg.api_timeout)
            try:
                provider = router._detect_provider()
            except ValueError:
                # Honor existing YAML-only Gemini credentials without exporting
                # secrets or changing the process environment.
                if not cfg.gemini_api_key or os.getenv("AGENT_LLM_PROVIDER"):
                    raise
                router = LLMRouter(provider="gemini", api_key=cfg.gemini_api_key,
                                   timeout=cfg.api_timeout)
                provider = "gemini"
            router.content_default_model = cfg.gemini_model if provider == "gemini" else None
        self.router = router
        self.events = events if events is not None else []

    def for_task(self, task):
        return ContentClient(task, router=self.router, events=self.events)

    def __call__(self, prompt):
        model = self.model or os.getenv("KAI_" + self.task.upper() + "_MODEL", "").strip()
        model = model or os.getenv("AGENT_DEFAULT_MODEL", "").strip()
        model = model or getattr(self.router, "content_default_model", None)
        model = model or self.router.get_model_for_task(self.task)
        event = dict(stage=self.task, model=model,
                     provider=self.router._detect_provider(),
                     prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
                     prompt=prompt)
        started = time.monotonic()
        try:
            text, usage, finish = self.router._call_provider(
                model=model, max_tokens=int(os.getenv("KAI_CONTENT_MAX_TOKENS", "8192")),
                temperature=0.7, messages=[{"role": "user", "content": prompt}],
            )
            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("provider returned no text")
            if finish in {"length", "max_tokens", "MAX_TOKENS"}:
                raise RuntimeError("provider truncated output")
            usage = usage if isinstance(usage, dict) else {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
            }
            estimator = getattr(self.router, "estimate_cost", None)
            estimate = estimator(usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                                 model=model) if estimator else None
            event.update(output=text, usage=usage, estimated_cost_usd=estimate,
                         finish_reason=finish, status="completed")
            return text
        except Exception as exc:
            event.update(status="failed", error_type=type(exc).__name__)
            raise
        finally:
            event["latency_seconds"] = time.monotonic() - started
            self.events.append(event)

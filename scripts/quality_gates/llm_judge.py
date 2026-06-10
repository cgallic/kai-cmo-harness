#!/usr/bin/env python3
"""
LLM judge — compatibility shim for LLM-judged quality gates.

The canonical provider-agnostic client lives in scripts/llm_client.py and is
shared by every LLM call site in the harness (gates, writers, extractors).
This module re-exports it so gate scripts (which run standalone from this
directory) keep a local import path.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.llm_client import (  # noqa: F401,E402
    DEFAULT_MODELS,
    JSON_ONLY_INSTRUCTION,
    JudgeConfigError,
    LLMConfigError,
    PROVIDER_KEYS,
    PROVIDER_PACKAGES,
    complete,
    make_llm_fn,
    resolve_provider,
)

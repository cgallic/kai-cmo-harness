"""
Redaction helpers for trace inputs/outputs/errors.

The trace store may be exported off-host for HALO diagnosis, so any
secret-shaped values (tokens, API keys, phone numbers, emails, customer
identifiers passed as headers/auth) must be scrubbed before they hit
disk or JSONL exports.
"""

from __future__ import annotations

import re
from typing import Any

# Field names that are always redacted regardless of value shape.
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "authorization",
    "bearer",
    "client_secret",
    "cookie",
    "credentials",
    "key",
    "password",
    "private_key",
    "refresh_token",
    "secret",
    "session",
    "set-cookie",
    "token",
    "twilio_auth_token",
    "x-api-key",
}

# Value patterns that look secret-shaped even in non-sensitive keys.
_REDACT_PATTERNS = [
    # Long opaque tokens (Twilio, OpenAI, Anthropic, Discord, etc.)
    re.compile(r"\b(sk-[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\b[A-Za-z0-9_-]{40,}\b"),
    # Email addresses (PII for outbound contacts)
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # E.164-ish phone numbers
    re.compile(r"\+?\d[\d\s\-().]{8,}\d"),
]

REDACTED = "[REDACTED]"
_MAX_STR = 2000


def _redact_str(value: str) -> str:
    """Apply value-shape redaction to a string."""
    redacted = value
    for pat in _REDACT_PATTERNS:
        redacted = pat.sub(REDACTED, redacted)
    if len(redacted) > _MAX_STR:
        redacted = redacted[:_MAX_STR] + f"... [truncated {len(value) - _MAX_STR} chars]"
    return redacted


def redact(value: Any, *, _depth: int = 0) -> Any:
    """
    Recursively redact sensitive values from arbitrary structures.

    - Dict keys matching SENSITIVE_KEYS (case-insensitive) are replaced.
    - Long opaque tokens, emails, and phone numbers are pattern-redacted.
    - Strings longer than 2000 chars are truncated with a marker.
    - Recursion is depth-limited to avoid pathological structures.
    """
    if _depth > 6:
        return REDACTED

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _redact_str(value)

    if isinstance(value, dict):
        out: dict = {}
        for k, v in value.items():
            key = str(k)
            if key.lower() in SENSITIVE_KEYS:
                out[key] = REDACTED
            else:
                out[key] = redact(v, _depth=_depth + 1)
        return out

    if isinstance(value, (list, tuple)):
        return [redact(v, _depth=_depth + 1) for v in value]

    # Fallback: stringify and redact.
    return _redact_str(repr(value))


def summarize_output(value: Any, *, max_len: int = 400) -> str:
    """
    Build a short, redaction-safe summary of a span's output for storage.

    HALO consumes summaries (not full bodies) to keep traces lean and to
    avoid leaking high-cardinality content into diagnosis prompts.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        text = value
    elif isinstance(value, dict):
        # Prefer explicit summary fields if the task already produced one.
        for field in ("summary", "headline", "title", "message"):
            if isinstance(value.get(field), str) and value[field].strip():
                text = value[field]
                break
        else:
            text = repr(redact(value))
    else:
        text = repr(redact(value))

    text = _redact_str(text)
    if len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text

"""
Knowledge Cloner — Utilities: file I/O, cost tracking, rate limiting, confirmations.
"""

import json
import asyncio
import time
import re
import httpx
from pathlib import Path
from typing import Optional

from .types import ExpertConfig, Source, CostEstimate
from .config import (
    OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODELS,
    GEMINI_API_KEY, GEMINI_FLASH_ENDPOINT,
    MODEL_COSTS, DEFAULT_RATE_LIMIT_SECONDS,
    AVG_INPUT_TOKENS_PER_SOURCE, AVG_OUTPUT_TOKENS_PER_EXTRACTION,
)


# ---------------------------------------------------------------------------
# Progress / Expert config persistence
# ---------------------------------------------------------------------------

def load_progress(expert_dir: Path) -> Optional[ExpertConfig]:
    progress_file = expert_dir / "progress.json"
    if not progress_file.exists():
        return None
    with open(progress_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ExpertConfig.from_dict(data)


def save_progress(expert_dir: Path, config: ExpertConfig) -> None:
    progress_file = expert_dir / "progress.json"
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Source map generation
# ---------------------------------------------------------------------------

def generate_source_map(expert_dir: Path, config: ExpertConfig) -> None:
    lines = [
        f"# Source Map: {config.name}",
        f"**Domain**: {config.domain}",
        f"**Last updated**: {time.strftime('%Y-%m-%d')}",
        f"**Total sources**: {len(config.sources)}",
        "",
        "## Sources",
        "",
        "| # | Type | Title | Priority | Status | URL |",
        "|---|------|-------|----------|--------|-----|",
    ]
    for i, src in enumerate(config.sources, 1):
        title = src.title or src.id
        url = src.url if len(src.url) < 80 else src.url[:77] + "..."
        lines.append(f"| {i} | {src.source_type} | {title} | {src.priority} | {src.status} | {url} |")

    lines.append("")

    # Status summary
    statuses = {}
    for s in config.sources:
        statuses[s.status] = statuses.get(s.status, 0) + 1
    lines.append("## Status Summary")
    for status, count in sorted(statuses.items()):
        lines.append(f"- **{status}**: {count}")
    lines.append("")

    source_map_path = expert_dir / "source-map.md"
    source_map_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Cost tracker
# ---------------------------------------------------------------------------

class CostTracker:
    def __init__(self, max_requests: int, max_cost: float):
        self.max_requests = max_requests
        self.max_cost = max_cost
        self.requests_made = 0
        self.estimated_spend = 0.0

    def can_proceed(self) -> bool:
        return self.requests_made < self.max_requests and self.estimated_spend < self.max_cost

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gemini-flash"])
        cost = (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000
        self.requests_made += 1
        self.estimated_spend += cost

    def check_or_abort(self) -> None:
        if self.requests_made >= self.max_requests:
            raise RuntimeError(
                f"Request limit reached ({self.requests_made}/{self.max_requests}). "
                f"Use --max-requests to increase."
            )
        if self.estimated_spend >= self.max_cost:
            raise RuntimeError(
                f"Cost limit reached (${self.estimated_spend:.2f}/${self.max_cost:.2f}). "
                f"Use --max-cost to increase."
            )

    def summary(self) -> str:
        return f"Requests: {self.requests_made}/{self.max_requests} | Spend: ${self.estimated_spend:.2f}/${self.max_cost:.2f}"


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    def __init__(self, min_interval: float = DEFAULT_RATE_LIMIT_SECONDS):
        self.min_interval = min_interval
        self._last_call = 0.0

    async def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_call = time.monotonic()


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------

def confirm_action(message: str, dry_run: bool = False) -> bool:
    if dry_run:
        safe_msg = message.encode("ascii", errors="replace").decode("ascii")
        print(f"[DRY RUN] {safe_msg}")
        return False
    safe_msg = message.encode("ascii", errors="replace").decode("ascii")
    try:
        response = input(f"{safe_msg} Continue? [y/N] ").strip().lower()
    except EOFError:
        return True  # Auto-approve in non-interactive shells
    return response in ("y", "yes")


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

def estimate_phase_cost(phase: str, model: str, num_requests: int) -> CostEstimate:
    costs = MODEL_COSTS.get(model, MODEL_COSTS["gemini-flash"])
    if phase == "extraction":
        per_request = (
            AVG_INPUT_TOKENS_PER_SOURCE * costs["input"]
            + AVG_OUTPUT_TOKENS_PER_EXTRACTION * costs["output"]
        ) / 1_000_000
    elif phase in ("distillation", "operationalization"):
        per_request = (30_000 * costs["input"] + 5_000 * costs["output"]) / 1_000_000
    elif phase in ("synthesis", "quality"):
        per_request = (20_000 * costs["input"] + 5_000 * costs["output"]) / 1_000_000
    else:
        per_request = 0.005

    total = per_request * num_requests
    return CostEstimate(
        phase=phase,
        model=model,
        requests=num_requests,
        estimated_cost=round(total, 4),
    )


# ---------------------------------------------------------------------------
# LLM API calls — OpenRouter (primary) + Gemini direct (audio only)
# ---------------------------------------------------------------------------

async def call_llm(prompt: str, model: str = "qwen-plus", max_tokens: int = 8192, temperature: float = 0.2) -> tuple[str, int, int]:
    """Call any model via OpenRouter. Returns (response_text, input_tokens, output_tokens).

    Supported model keys: qwen-plus, qwen-max, qwen-coder, gemini-flash, claude-sonnet
    Falls back to Gemini direct API if no OpenRouter key is set and model is gemini-flash.
    """
    # Resolve model ID
    model_id = OPENROUTER_MODELS.get(model, model)

    # Try OpenRouter first (works for ALL models)
    if OPENROUTER_API_KEY:
        return await _call_openrouter(prompt, model_id, max_tokens, temperature)

    # Fallback: Gemini direct API (only for gemini-flash)
    if model in ("gemini-flash",) and GEMINI_API_KEY:
        return await _call_gemini_direct(prompt, max_tokens, temperature)

    raise ValueError(
        f"No API key for model '{model}'. "
        f"Set OPENROUTER_API_KEY in .env (recommended) or GEMINI_API_KEY for Gemini-only fallback."
    )


async def _call_openrouter(prompt: str, model_id: str, max_tokens: int, temperature: float) -> tuple[str, int, int]:
    """Call OpenRouter API (OpenAI-compatible)."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/cgallic/cmo_agent",
                "X-Title": "Knowledge Cloner",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        data = response.json()

    # Extract response text
    text = ""
    choices = data.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content", "")

    # Token usage
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", len(prompt) // 4)
    output_tokens = usage.get("completion_tokens", len(text) // 4)

    return text, input_tokens, output_tokens


async def _call_gemini_direct(prompt: str, max_tokens: int, temperature: float) -> tuple[str, int, int]:
    """Fallback: call Gemini Flash directly (no OpenRouter)."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{GEMINI_FLASH_ENDPOINT}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    usage = data.get("usageMetadata", {})
    input_tokens = usage.get("promptTokenCount", len(prompt) // 4)
    output_tokens = usage.get("candidatesTokenCount", len(text) // 4)
    return text, input_tokens, output_tokens


async def call_gemini_with_audio(audio_bytes: bytes, mime_type: str, prompt: str, max_tokens: int = 16384) -> tuple[str, int, int]:
    """Call Gemini Flash with audio input for transcription (direct API only — OpenRouter doesn't support audio inline)."""
    import base64
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Audio transcription requires direct Gemini API access.")

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{GEMINI_FLASH_ENDPOINT}?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": mime_type, "data": audio_b64}},
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    usage = data.get("usageMetadata", {})
    input_tokens = usage.get("promptTokenCount", 0)
    output_tokens = usage.get("candidatesTokenCount", len(text) // 4)
    return text, input_tokens, output_tokens


# Legacy aliases for backward compatibility
async def call_gemini(prompt: str, max_tokens: int = 8192, temperature: float = 0.2) -> tuple[str, int, int]:
    return await call_llm(prompt, model="gemini-flash", max_tokens=max_tokens, temperature=temperature)

async def call_claude(prompt: str, system: str = "", max_tokens: int = 8192) -> tuple[str, int, int]:
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    return await call_llm(full_prompt, model="claude-sonnet", max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def make_source_id(source_type: str, url_or_title: str) -> str:
    """Generate a unique source ID from type and URL/title."""
    if "youtube.com" in url_or_title or "youtu.be" in url_or_title:
        # Extract video ID
        match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url_or_title)
        if match:
            return f"yt_{match.group(1)}"
    return f"{source_type[:3]}_{slugify(url_or_title)[:40]}"


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def log(msg: str) -> None:
    # Sanitize for Windows console encoding (cp1252 can't handle all unicode)
    safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
    print(f"[knowledge-cloner] {safe_msg}")

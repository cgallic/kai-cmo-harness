"""
Knowledge Cloner — Configuration, API keys, model defaults, paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env — check project root first, then scripts/
_project_root = Path(__file__).parent.parent.parent
_env_candidates = [
    _project_root / ".env",
    Path(__file__).parent.parent / ".env",
]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(_env_path, override=True)

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# OpenRouter API (primary — cheapest, best model selection)
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter model IDs
OPENROUTER_MODELS = {
    "qwen-plus": "qwen/qwen3.5-plus-02-15",       # $0.26/$1.56 per 1M — 1M context, great for bulk
    "qwen-max": "qwen/qwen3-max",                   # $1.20/$6.00 per 1M — best quality for synthesis
    "qwen-coder": "qwen/qwen3-coder",               # $0.22/$1.00 per 1M — good for structured extraction
    "gemini-flash": "google/gemini-2.0-flash-001",   # $0.10/$0.40 per 1M — cheapest fallback
    "claude-sonnet": "anthropic/claude-sonnet-4.6",   # $3.00/$15.00 per 1M — highest quality
}

# Default model for the pipeline
DEFAULT_MODEL = "qwen-plus"

# Gemini direct API (fallback for audio transcription)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_FLASH_MODEL = "gemini-2.0-flash"
GEMINI_FLASH_ENDPOINT = f"{GEMINI_API_URL}/{GEMINI_FLASH_MODEL}:generateContent"

# Model costs per 1M tokens (for estimation)
MODEL_COSTS = {
    "qwen-plus": {"input": 0.26, "output": 1.56},
    "qwen-max": {"input": 1.20, "output": 6.00},
    "qwen-coder": {"input": 0.22, "output": 1.00},
    "gemini-flash": {"input": 0.10, "output": 0.40},
    "claude-sonnet": {"input": 3.00, "output": 15.00},
}

# Which model each phase uses by default
PHASE_MODELS = {
    "extraction": "qwen-plus",
    "distillation": "qwen-plus",
    "synthesis": "qwen-max",
    "operationalization": "qwen-plus",
    "quality": "qwen-max",
}

# Default limits
DEFAULT_MAX_REQUESTS = 100
DEFAULT_MAX_COST = 5.00
DEFAULT_RATE_LIMIT_SECONDS = 2.0

# Average tokens per source (for cost estimation)
AVG_INPUT_TOKENS_PER_SOURCE = 8_000
AVG_OUTPUT_TOKENS_PER_EXTRACTION = 4_000
AVG_INPUT_TOKENS_DISTILLATION = 30_000
AVG_OUTPUT_TOKENS_DISTILLATION = 5_000
AVG_INPUT_TOKENS_SYNTHESIS = 20_000
AVG_OUTPUT_TOKENS_SYNTHESIS = 5_000

# Base data directory (override with KNOWLEDGE_CLONER_DATA_DIR env var)
BASE_DATA_DIR = Path(os.getenv(
    "KNOWLEDGE_CLONER_DATA_DIR",
    str(Path(__file__).parent.parent.parent / "clients" / "Connor_Gallic" / "knowledge"),
))


def get_expert_dir(slug: str) -> Path:
    return BASE_DATA_DIR / slug


def validate_api_key(model: str) -> bool:
    if model in ("qwen-plus", "qwen-max", "qwen-coder"):
        return bool(OPENROUTER_API_KEY)
    elif model == "gemini-flash":
        return bool(OPENROUTER_API_KEY or GEMINI_API_KEY)
    elif model == "claude-sonnet":
        return bool(OPENROUTER_API_KEY or ANTHROPIC_API_KEY)
    return False

"""
Content Quality Scorer — Configuration.
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

# API Keys (reuse from knowledge_cloner)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Category weights (must sum to 1.0)
CATEGORY_WEIGHTS = {
    "Algorithmic Authorship": 0.35,
    "GEO/AEO Signals": 0.20,
    "Content Structure": 0.25,
    "Four U's": 0.20,
}

# Weights when LLM rules are disabled (redistribute Four U's proportionally)
CATEGORY_WEIGHTS_NO_LLM = {
    "Algorithmic Authorship": 0.4375,  # 0.35 / 0.80
    "GEO/AEO Signals": 0.25,          # 0.20 / 0.80
    "Content Structure": 0.3125,       # 0.25 / 0.80
}

# Grade boundaries
GRADE_BOUNDARIES = {
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 60,
    "F": 0,
}

# GEO signal targets per 1K words
GEO_TARGETS = {
    "citations": 5,
    "quotations": 3,
    "statistics": 5,
    "technical_terms": 10,
}

# GEO visibility boosts (from academic research)
GEO_BOOSTS = {
    "citations": "+115%",
    "quotations": "+40%",
    "statistics": "+37%",
    "technical_terms": "+32.7%",
}

# Content structure targets
STRUCTURE_TARGETS = {
    "max_words_between_headings": 300,
    "min_words_between_headings": 100,
    "min_paragraph_sentences": 2,
    "max_paragraph_sentences": 4,
    "min_avg_sentence_length": 15,
    "max_avg_sentence_length": 20,
    "target_active_voice_pct": 90,
    "target_reading_level_min": 6,
    "target_reading_level_max": 8,
    "you_your_ratio_target": 2.0,  # "you/your" should be 2x "we/our/I"
}

# AI cliche patterns to flag
AI_CLICHES = [
    r"\bit'?s important to note\b",
    r"\bin conclusion\b",
    r"\bharness the power\b",
    r"\bdive into\b",
    r"\bgame[- ]?changer\b",
    r"\bdelve\b",
    r"\btap into\b",
    r"\bunlock the potential\b",
    r"\bleverage\b",
    r"\bseamless(?:ly)?\b",
    r"\brobust\b",
    r"\bholistic\b",
    r"\bsynerg(?:y|ize|istic)\b",
    r"\bparadigm shift\b",
    r"\bin today'?s (?:fast[- ]paced|digital|modern) (?:world|landscape|era)\b",
    r"\bnavigat(?:e|ing) the (?:complex|evolving)\b",
    r"\blet'?s explore\b",
    r"\bwithout further ado\b",
    r"\bin this article,? (?:we will|we'll|I will|I'll)\b",
]

# Filler words to flag (AA-22)
FILLER_WORDS = [
    "also", "actually", "basically", "really", "very",
    "quite", "rather", "somewhat", "simply", "just",
    "literally", "essentially", "obviously", "clearly",
    "definitely", "certainly", "absolutely", "honestly",
]

# Back-reference patterns (AA-23)
BACK_REFERENCES = [
    r"\bas mentioned\b",
    r"\bas (?:shown|discussed|noted|stated|described) (?:above|earlier|previously|before)\b",
    r"\bin the previous section\b",
    r"\bas we (?:saw|discussed|mentioned|noted)\b",
    r"\brecall that\b",
    r"\bas per the above\b",
]

# Vague quantifiers (AA-13)
VAGUE_QUANTIFIERS = [
    r"\bmany\b", r"\bseveral\b", r"\ba lot\b", r"\bnumerous\b",
    r"\bvarious\b", r"\bcountless\b", r"\ba number of\b",
    r"\bsome\b", r"\bfew\b", r"\ba handful\b",
]

# Default LLM model for Four U's scoring
DEFAULT_LLM_MODEL = "qwen-plus"

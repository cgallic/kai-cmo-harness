"""
Content Quality Scorer — Four U's LLM-based scoring.

Uses LLM to evaluate Unique, Useful, Ultra-specific, Urgent dimensions.
Gracefully skips when no API key is available.
"""

import json
import re

from scripts.quality.parser import Document
from scripts.quality.types import Category, Severity, Violation, RuleResult
from scripts.quality.config import OPENROUTER_API_KEY, DEFAULT_LLM_MODEL
from scripts.quality.prompts import FOUR_US_PROMPT
from scripts.quality.rules import register
from scripts.quality.rules.base import BaseRule


@register
class FourUsScore(BaseRule):
    """FU-01: Four U's content quality scoring (LLM-based)."""
    RULE_ID = "FU-01"
    RULE_NAME = "Four U's (Unique, Useful, Ultra-specific, Urgent)"
    CATEGORY = Category.FOUR_US
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Score content 1-4 on each U dimension. Target: 12+/16 total"

    # This rule requires async evaluation
    _requires_llm = True

    def evaluate(self, doc):
        """Sync placeholder — real evaluation happens in evaluate_async."""
        return self._make_result(
            0.0,
            suggestions=["Four U's scoring requires LLM — use async evaluation"],
        )

    async def evaluate_async(self, doc: Document, model: str = None) -> RuleResult:
        """Async evaluation using LLM."""
        if not OPENROUTER_API_KEY:
            return self._make_result(
                0.0,
                suggestions=["Skipped: OPENROUTER_API_KEY not set. Set it in .env for Four U's scoring."],
                metadata={"skipped": True, "reason": "no_api_key"},
            )

        model = model or DEFAULT_LLM_MODEL

        # Pre-compute signals for context
        all_text = ' '.join(s.text for s in doc.all_sentences)
        stat_count = len(re.findall(r'\d+(?:\.\d+)?%|\$[\d,.]+|\d+x\b', all_text))
        citation_count = len(re.findall(r'according to|cited by|per [A-Z]', all_text, re.IGNORECASE))

        # Truncate content for LLM (keep first 3000 chars)
        content = all_text[:3000]
        if len(all_text) > 3000:
            content += "\n\n[... truncated for scoring ...]"

        prompt = FOUR_US_PROMPT.format(
            stat_count=stat_count,
            citation_count=citation_count,
            word_count=doc.word_count,
            content=content,
        )

        try:
            from scripts.knowledge_cloner.utils import call_llm
            response_text, _, _ = await call_llm(prompt, model=model, max_tokens=1024, temperature=0.1)

            # Parse JSON response
            scores = self._parse_response(response_text)
            if not scores:
                return self._make_result(
                    0.0,
                    suggestions=["LLM response could not be parsed"],
                    metadata={"raw_response": response_text[:500]},
                )

            return self._build_result(scores)

        except Exception as e:
            return self._make_result(
                0.0,
                suggestions=[f"LLM scoring failed: {str(e)}"],
                metadata={"error": str(e)},
            )

    def _parse_response(self, text: str) -> dict | None:
        """Extract JSON from LLM response."""
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code block
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _build_result(self, scores: dict) -> RuleResult:
        """Build RuleResult from parsed LLM scores."""
        dimensions = ["unique", "useful", "ultra_specific", "urgent"]
        total = 0
        violations = []
        suggestions = []
        metadata = {}

        for dim in dimensions:
            data = scores.get(dim, {})
            score = data.get("score", 1)
            score = max(1, min(4, score))  # Clamp 1-4
            total += score

            metadata[dim] = {
                "score": score,
                "evidence": data.get("evidence", ""),
            }

            if score < 3:
                suggestion = data.get("suggestion", "")
                display_dim = dim.replace("_", "-")
                violations.append(Violation(
                    line=0,
                    text=f"{display_dim.title()}: {score}/4",
                    fix=suggestion or f"Improve {display_dim} dimension",
                ))
                if suggestion:
                    suggestions.append(f"{display_dim.title()}: {suggestion}")

        # Normalize: 16 possible, 4 minimum
        normalized = (total - 4) / 12  # 0.0 to 1.0
        metadata["total"] = total
        metadata["max"] = 16

        return self._make_result(normalized, violations, suggestions, metadata)

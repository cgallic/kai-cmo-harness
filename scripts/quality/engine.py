"""
Content Quality Scorer — Engine orchestrator.

Parses documents, runs rule sets, aggregates weighted scores.
"""

import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional

from scripts.quality.parser import parse_markdown
from scripts.quality.types import Category, CategoryScore, QualityReport
from scripts.quality.config import get_category_weights, get_category_weights_no_llm
from scripts.quality.rules import get_all_rules, get_rules_for_sets
from scripts.quality.rules.base import BaseRule

# Import rule modules to trigger @register decorators
import scripts.quality.rules.algorithmic_authorship  # noqa: F401
import scripts.quality.rules.geo_signals  # noqa: F401
import scripts.quality.rules.content_structure  # noqa: F401
import scripts.quality.rules.four_us  # noqa: F401
import scripts.quality.rules.voice_consistency  # noqa: F401
import scripts.quality.rules.taste_specificity  # noqa: F401
import scripts.quality.rules.taste_emotional  # noqa: F401
import scripts.quality.rules.taste_originality  # noqa: F401
import scripts.quality.rules.taste_hook  # noqa: F401
import scripts.quality.rules.taste_cta  # noqa: F401
import scripts.quality.rules.taste_proof  # noqa: F401

# Module-level LRU cache for content scoring
_SCORE_CACHE: "OrderedDict[str, QualityReport]" = OrderedDict()
_CACHE_MAX = 128


def clear_cache() -> None:
    """Clear the content scoring cache."""
    _SCORE_CACHE.clear()


class QualityEngine:
    """Orchestrates content quality scoring."""

    def __init__(
        self,
        rule_sets: Optional[List[str]] = None,
        llm_model: Optional[str] = None,
        use_llm: bool = True,
    ):
        self.llm_model = llm_model
        self.use_llm = use_llm

        # Get rules based on selected sets
        if rule_sets:
            self._rule_classes = get_rules_for_sets(rule_sets)
        else:
            self._rule_classes = get_all_rules()

        # Filter out LLM rules if disabled
        if not use_llm:
            self._rule_classes = [
                r for r in self._rule_classes
                if r.CATEGORY != Category.FOUR_US
            ]

    async def score(self, file_path: str) -> QualityReport:
        """Score a file and return a QualityReport."""
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        return await self.score_content(content, file_path=str(path))

    async def score_content(self, content: str, file_path: str = "<stdin>") -> QualityReport:
        """Score raw content string."""
        # Build cache key from content hash + scoring config
        rule_names = sorted(cls.__name__ for cls in self._rule_classes)
        key_data = content + str(self.use_llm) + str(rule_names)
        cache_key = hashlib.sha256(key_data.encode("utf-8")).hexdigest()

        if cache_key in _SCORE_CACHE:
            # Move to end so it's treated as most-recently-used
            _SCORE_CACHE.move_to_end(cache_key)
            return _SCORE_CACHE[cache_key]

        doc = parse_markdown(content)

        # Instantiate and run rules
        results_by_category = {}
        for rule_cls in self._rule_classes:
            rule: BaseRule = rule_cls()
            category = rule.CATEGORY

            # Use async evaluation for LLM rules
            if hasattr(rule, '_requires_llm') and rule._requires_llm and self.use_llm:
                result = await rule.evaluate_async(doc, model=self.llm_model)
            else:
                result = rule.evaluate(doc)

            results_by_category.setdefault(category, []).append(result)

        # Determine weights (dynamic — reads harness.yaml overrides at score time)
        weights = get_category_weights() if self.use_llm else get_category_weights_no_llm()

        # Build category scores
        categories = []
        for category, results in results_by_category.items():
            cat_name = category.value
            weight = weights.get(cat_name, 0.0)

            # Weighted average of rule scores within category
            if results:
                avg_score = sum(r.score for r in results) / len(results)
            else:
                avg_score = 0.0

            categories.append(CategoryScore(
                category=category,
                score=avg_score * 100,
                weight=weight,
                rules=results,
            ))

        # Overall score: weighted sum
        overall = sum(c.score * c.weight for c in categories)

        # Metadata
        metadata = {
            "word_count": doc.word_count,
            "sentence_count": doc.sentence_count,
            "section_count": len(doc.sections),
            "paragraph_count": len(doc.all_paragraphs),
            "list_count": len(doc.all_lists),
            "llm_enabled": self.use_llm,
        }

        # Add reading level if available
        for cat in categories:
            for rule in cat.rules:
                if rule.rule_id == "CS-05" and "grade_level" in rule.metadata:
                    metadata["reading_level"] = rule.metadata["grade_level"]

        report = QualityReport(
            file_path=file_path,
            overall_score=overall,
            categories=categories,
            metadata=metadata,
        )

        # Store in cache; evict oldest entry if over capacity
        _SCORE_CACHE[cache_key] = report
        if len(_SCORE_CACHE) > _CACHE_MAX:
            _SCORE_CACHE.popitem(last=False)

        return report

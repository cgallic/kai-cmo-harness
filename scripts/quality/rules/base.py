"""
Content Quality Scorer — Base rule class.
"""

from abc import ABC, abstractmethod

from scripts.quality.parser import Document
from scripts.quality.types import Category, RuleResult, Severity


class BaseRule(ABC):
    """Abstract base class for all quality rules."""

    RULE_ID: str = ""
    RULE_NAME: str = ""
    CATEGORY: Category = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY: Severity = Severity.WARNING
    DESCRIPTION: str = ""

    @abstractmethod
    def evaluate(self, doc: Document) -> RuleResult:
        """Evaluate this rule against a parsed document.

        Returns a RuleResult with score 0.0-1.0 and any violations.
        """
        ...

    def _make_result(self, score: float, violations=None, suggestions=None, metadata=None) -> RuleResult:
        """Helper to build a RuleResult with this rule's metadata."""
        return RuleResult(
            rule_id=self.RULE_ID,
            rule_name=self.RULE_NAME,
            category=self.CATEGORY,
            severity=self.SEVERITY,
            score=max(0.0, min(1.0, score)),
            violations=violations or [],
            suggestions=suggestions or [],
            metadata=metadata or {},
        )

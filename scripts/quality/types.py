"""
Content Quality Scorer — Data types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """Severity levels for quality violations."""
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    OPPORTUNITY = "OPPORTUNITY"
    INFO = "INFO"


class Category(str, Enum):
    """Rule categories."""
    ALGORITHMIC_AUTHORSHIP = "Algorithmic Authorship"
    GEO_SIGNALS = "GEO/AEO Signals"
    CONTENT_STRUCTURE = "Content Structure"
    FOUR_US = "Four U's"
    TASTE = "Taste"


@dataclass
class Violation:
    """A single rule violation found in content."""
    line: int
    text: str
    fix: str
    context: str = ""

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "text": self.text,
            "fix": self.fix,
            "context": self.context,
        }


@dataclass
class RuleResult:
    """Result from evaluating a single rule."""
    rule_id: str
    rule_name: str
    category: Category
    severity: Severity
    score: float  # 0.0 - 1.0
    violations: List[Violation] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "score": round(self.score, 3),
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
            "suggestions": self.suggestions,
            "metadata": self.metadata,
        }


@dataclass
class CategoryScore:
    """Aggregated score for a rule category."""
    category: Category
    score: float  # 0-100
    weight: float
    rules: List[RuleResult] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        return "F"

    @property
    def violation_count(self) -> int:
        return sum(len(r.violations) for r in self.rules)

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "score": round(self.score, 1),
            "grade": self.grade,
            "weight": self.weight,
            "violation_count": self.violation_count,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class QualityReport:
    """Complete quality scoring report for a document."""
    file_path: str
    overall_score: float  # 0-100
    categories: List[CategoryScore] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_grade(self) -> str:
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        return "F"

    @property
    def top_fixes(self) -> List[Dict[str, Any]]:
        """Get top 5 highest-impact fixes across all categories."""
        fixes = []
        for cat in self.categories:
            for rule in cat.rules:
                if rule.violations:
                    # Estimate impact: more violations on higher-weighted categories = more points
                    impact = (1.0 - rule.score) * cat.weight * 100
                    fixes.append({
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "impact": round(impact, 1),
                        "violation_count": len(rule.violations),
                        "first_violation": rule.violations[0].to_dict(),
                        "suggestion": rule.suggestions[0] if rule.suggestions else rule.violations[0].fix,
                    })
        fixes.sort(key=lambda f: f["impact"], reverse=True)
        return fixes[:5]

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "overall_score": round(self.overall_score, 1),
            "overall_grade": self.overall_grade,
            "categories": [c.to_dict() for c in self.categories],
            "top_fixes": self.top_fixes,
            "metadata": self.metadata,
        }

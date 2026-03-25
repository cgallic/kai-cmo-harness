"""
Taste Rule: Originality Score (TS-03)

Scores what % of sentences are NOT common AI/marketing clichés.
If an LLM would generate it by default, it's not differentiated.

Detects: overused phrases, generic marketing language, template patterns,
and sentences that could appear in any company's content.
"""

import re

from scripts.quality.parser import Document
from scripts.quality.rules.base import BaseRule
from scripts.quality.rules import register
from scripts.quality.types import Category, RuleResult, Severity, Violation


# Common cliché/template patterns that indicate unoriginal content
_CLICHE_PATTERNS = [
    # Marketing clichés
    (re.compile(r'\b(game.?changer|paradigm shift|best.?in.?class|world.?class|cutting.?edge)\b', re.IGNORECASE), "marketing cliché"),
    (re.compile(r'\b(take\s+your\s+\w+\s+to\s+the\s+next\s+level)\b', re.IGNORECASE), "overused phrase"),
    (re.compile(r'\b(unlock\s+(the\s+)?(power|potential|full\s+potential))\b', re.IGNORECASE), "overused phrase"),
    (re.compile(r'\b(empower|supercharge|turbocharge|revolutionize)\s+(your|the)\b', re.IGNORECASE), "overused verb"),
    (re.compile(r'\b(seamless(ly)?|effortless(ly)?|frictionless)\b', re.IGNORECASE), "empty modifier"),
    (re.compile(r'\b(robust|scalable|enterprise.?grade|state.?of.?the.?art)\b', re.IGNORECASE), "buzzword"),
    (re.compile(r'\b(think\s+about\s+it|let\s+that\s+sink\s+in|here\'?s\s+the\s+thing)\b', re.IGNORECASE), "filler phrase"),

    # AI-generated patterns
    (re.compile(r'\b(in\s+today\'?s\s+(fast|rapidly|ever).?(paced|changing|evolving))\b', re.IGNORECASE), "AI slop opener"),
    (re.compile(r'\b(it\'?s\s+(no\s+secret|clear|obvious|well.?known)\s+that)\b', re.IGNORECASE), "AI slop setup"),
    (re.compile(r'\b(at\s+the\s+end\s+of\s+the\s+day)\b', re.IGNORECASE), "cliché filler"),
    (re.compile(r'\b(first\s+and\s+foremost)\b', re.IGNORECASE), "unnecessary preamble"),
    (re.compile(r'\b(when\s+it\s+comes\s+to)\b', re.IGNORECASE), "weak transition"),
    (re.compile(r'\b(plays?\s+a\s+(crucial|vital|key|important|pivotal)\s+role)\b', re.IGNORECASE), "vague importance claim"),
    (re.compile(r'\b(the\s+landscape\s+(is\s+)?chang(ing|ed))\b', re.IGNORECASE), "generic observation"),
    (re.compile(r'\b(navigate\s+the\s+complex(ities)?)\b', re.IGNORECASE), "consulting-speak"),

    # Template sentences (could be about any product/company)
    (re.compile(r'\b(we\s+are\s+committed\s+to|we\s+strive\s+to|our\s+mission\s+is)\b', re.IGNORECASE), "corporate template"),
    (re.compile(r'\b(whether\s+you\'?re\s+a\s+\w+\s+or\s+a\s+\w+)\b', re.IGNORECASE), "generic audience catch-all"),
    (re.compile(r'\b(in\s+an\s+increasingly\s+\w+\s+world)\b', re.IGNORECASE), "hollow context-setting"),
]


@register
class OriginalityScore(BaseRule):
    """Score originality — penalize clichés, template language, and AI-generated patterns."""

    RULE_ID = "TS-03"
    RULE_NAME = "Originality score"
    CATEGORY = Category.TASTE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Content should say something only YOUR brand would say. Clichés and template language signal generic AI output."

    def evaluate(self, doc: Document) -> RuleResult:
        violations = []
        cliche_count = 0
        cliche_sentences = set()

        for sent in doc.all_sentences:
            text = sent.text
            for pattern, label in _CLICHE_PATTERNS:
                match = pattern.search(text)
                if match:
                    cliche_count += 1
                    cliche_sentences.add(sent.line)
                    violations.append(Violation(
                        line=sent.line,
                        text=match.group(0),
                        fix=f"Replace {label}: rewrite with something specific to YOUR product/experience",
                        context=text[:80],
                    ))
                    break  # One flag per sentence

        total_sentences = max(len(doc.all_sentences), 1)
        cliche_ratio = len(cliche_sentences) / total_sentences

        # Score: 1.0 if 0% clichés, 0.0 if 30%+ are clichés
        score = max(0.0, 1.0 - (cliche_ratio / 0.30))

        return self._make_result(
            score=score,
            violations=violations[:15],  # Cap at 15
            suggestions=[
                f"Clichés found: {cliche_count} in {len(cliche_sentences)}/{total_sentences} sentences ({cliche_ratio:.0%})",
                "Replace generic phrases with specific brand language, data, or unique observations",
                "Test: if a competitor could publish this sentence unchanged, it's not original enough",
            ] if score < 0.8 else [],
            metadata={"cliche_count": cliche_count, "cliche_sentences": len(cliche_sentences), "total_sentences": total_sentences},
        )

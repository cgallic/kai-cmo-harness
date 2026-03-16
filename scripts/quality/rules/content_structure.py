"""
Content Quality Scorer — Content structure rules.

Checks heading frequency, paragraph length, active voice, reading level,
AI cliches, and reader-focused language.
"""

import re
import math

from scripts.quality.parser import Document
from scripts.quality.types import Category, Severity, Violation
from scripts.quality.config import AI_CLICHES, STRUCTURE_TARGETS
from scripts.quality.rules import register
from scripts.quality.rules.base import BaseRule


@register
class HookPresence(BaseRule):
    """CS-01: First paragraph should contain a hook."""
    RULE_ID = "CS-01"
    RULE_NAME = "Opening hook"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "First 2-3 sentences should hook the reader with a question, statistic, or bold claim"

    _HOOK_SIGNALS = [
        re.compile(r'\?'),                           # Question
        re.compile(r'\d+%'),                         # Statistic
        re.compile(r'\$[\d,.]+'),                    # Dollar amount
        re.compile(r'\b(?:imagine|picture this|what if|here\'s the thing)\b', re.IGNORECASE),
        re.compile(r'\b(?:surprising|shocking|most people|nobody tells you)\b', re.IGNORECASE),
    ]

    def evaluate(self, doc):
        if not doc.all_paragraphs:
            return self._make_result(0.5, suggestions=["No content found to evaluate"])

        first_para = doc.all_paragraphs[0]
        # Check first 3 sentences
        hook_sentences = first_para.sentences[:3]
        hook_text = ' '.join(s.text for s in hook_sentences)

        has_hook = any(p.search(hook_text) for p in self._HOOK_SIGNALS)

        if has_hook:
            return self._make_result(1.0)

        return self._make_result(0.3, violations=[Violation(
            line=first_para.line,
            text=hook_text[:120],
            fix="Add a hook: question, statistic, bold claim, or 'imagine...' opener",
        )])


@register
class HeadingFrequency(BaseRule):
    """CS-02: Headers should appear every 200-300 words."""
    RULE_ID = "CS-02"
    RULE_NAME = "Heading frequency"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Add a heading every 200-300 words for scannability"

    def evaluate(self, doc):
        max_gap = STRUCTURE_TARGETS["max_words_between_headings"]
        violations = []

        for section in doc.sections:
            if section.word_count > max_gap and section.level > 0:
                violations.append(Violation(
                    line=section.heading_line,
                    text=f'Section "{section.heading}" has {section.word_count} words',
                    fix=f"Break into subsections (target: {max_gap} words max between headings)",
                ))

        total = max(len([s for s in doc.sections if s.level > 0]), 1)
        compliant = total - len(violations)
        score = compliant / total
        return self._make_result(score, violations)


@register
class ParagraphLength(BaseRule):
    """CS-03: Paragraphs should be 2-4 sentences."""
    RULE_ID = "CS-03"
    RULE_NAME = "Paragraph length"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Keep paragraphs at 2-4 sentences for readability"

    def evaluate(self, doc):
        min_s = STRUCTURE_TARGETS["min_paragraph_sentences"]
        max_s = STRUCTURE_TARGETS["max_paragraph_sentences"]
        violations = []

        for para in doc.all_paragraphs:
            count = len(para.sentences)
            if count > max_s:
                violations.append(Violation(
                    line=para.line,
                    text=para.text[:120],
                    fix=f"Break this {count}-sentence paragraph into smaller ones (target: {min_s}-{max_s})",
                ))
            # Single-sentence paragraphs are okay for emphasis; only flag 0
            # (which shouldn't happen, but safety)

        total = max(len(doc.all_paragraphs), 1)
        compliant = total - len(violations)
        score = compliant / total
        return self._make_result(score, violations)


@register
class ActiveVoice(BaseRule):
    """CS-04: Active voice should be used 90%+ of the time."""
    RULE_ID = "CS-04"
    RULE_NAME = "Active voice"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Use active voice at least 90% of the time"

    _PASSIVE = re.compile(
        r'\b(?:was|were|is|are|been|being|be)\s+'
        r'(?:\w+ly\s+)?'  # optional adverb
        r'(?:\w+ed|written|built|made|done|given|taken|shown|known|seen|found|told|set)\b',
        re.IGNORECASE
    )

    def evaluate(self, doc):
        passive_count = 0
        violations = []
        for s in doc.all_sentences:
            if self._PASSIVE.search(s.text):
                passive_count += 1
                if len(violations) < 5:  # Cap displayed violations
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix="Rewrite in active voice (subject does the action)",
                    ))

        total = max(len(doc.all_sentences), 1)
        active_pct = ((total - passive_count) / total) * 100
        target = STRUCTURE_TARGETS["target_active_voice_pct"]

        score = min(active_pct / target, 1.0)
        return self._make_result(
            score, violations,
            metadata={"active_pct": round(active_pct, 1), "passive_count": passive_count},
        )


@register
class ReadingLevel(BaseRule):
    """CS-05: Reading level should be grade 6-8."""
    RULE_ID = "CS-05"
    RULE_NAME = "Reading level"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Target grade 6-8 reading level for broad accessibility"

    def _count_syllables(self, word: str) -> int:
        """Simple syllable count heuristic."""
        word = word.lower().rstrip('es')
        if len(word) <= 3:
            return 1
        count = 0
        vowels = 'aeiouy'
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        return max(count, 1)

    def _flesch_kincaid_grade(self, doc: Document) -> float:
        """Calculate Flesch-Kincaid Grade Level."""
        if not doc.all_sentences:
            return 0.0

        total_words = sum(s.word_count for s in doc.all_sentences)
        total_sentences = len(doc.all_sentences)
        total_syllables = sum(
            self._count_syllables(w)
            for s in doc.all_sentences
            for w in s.text.split()
            if w.strip()
        )

        if total_words == 0 or total_sentences == 0:
            return 0.0

        asl = total_words / total_sentences  # avg sentence length
        asw = total_syllables / total_words  # avg syllables per word

        grade = 0.39 * asl + 11.8 * asw - 15.59
        return max(0, round(grade, 1))

    def evaluate(self, doc):
        # Try textstat first
        try:
            import textstat
            all_text = ' '.join(s.text for s in doc.all_sentences)
            grade = textstat.flesch_kincaid_grade(all_text)
        except ImportError:
            grade = self._flesch_kincaid_grade(doc)

        min_grade = STRUCTURE_TARGETS["target_reading_level_min"]
        max_grade = STRUCTURE_TARGETS["target_reading_level_max"]

        violations = []
        if grade > max_grade:
            violations.append(Violation(
                line=0,
                text=f"Reading level: grade {grade} (target: {min_grade}-{max_grade})",
                fix="Simplify vocabulary and shorten sentences",
            ))
            # Score degrades as we go further above target
            score = max(0.0, 1.0 - (grade - max_grade) / 6)
        elif grade < min_grade:
            violations.append(Violation(
                line=0,
                text=f"Reading level: grade {grade} (target: {min_grade}-{max_grade})",
                fix="Content may be too simple; add more substance",
            ))
            score = max(0.0, 1.0 - (min_grade - grade) / 4)
        else:
            score = 1.0

        return self._make_result(score, violations, metadata={"grade_level": grade})


@register
class AvgSentenceLength(BaseRule):
    """CS-06: Average sentence length should be 15-20 words."""
    RULE_ID = "CS-06"
    RULE_NAME = "Average sentence length"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.INFO
    DESCRIPTION = "Average sentence length should be 15-20 words"

    def evaluate(self, doc):
        if not doc.all_sentences:
            return self._make_result(0.5, metadata={"avg_length": 0})

        total = sum(s.word_count for s in doc.all_sentences)
        avg = total / len(doc.all_sentences)

        min_len = STRUCTURE_TARGETS["min_avg_sentence_length"]
        max_len = STRUCTURE_TARGETS["max_avg_sentence_length"]

        violations = []
        if avg > max_len:
            score = max(0.3, 1.0 - (avg - max_len) / 15)
            violations.append(Violation(
                line=0,
                text=f"Average sentence length: {avg:.1f} words (target: {min_len}-{max_len})",
                fix="Break long sentences into shorter ones",
            ))
        elif avg < min_len:
            score = max(0.5, 1.0 - (min_len - avg) / 10)
            violations.append(Violation(
                line=0,
                text=f"Average sentence length: {avg:.1f} words (target: {min_len}-{max_len})",
                fix="Combine very short sentences for better flow",
            ))
        else:
            score = 1.0

        return self._make_result(score, violations, metadata={"avg_length": round(avg, 1)})


@register
class NoAICliches(BaseRule):
    """CS-07: Remove AI-generated cliches."""
    RULE_ID = "CS-07"
    RULE_NAME = "No AI cliches"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.WARNING
    DESCRIPTION = 'Remove "it\'s important to note", "in conclusion", "harness the power", etc.'

    _PATTERNS = [re.compile(p, re.IGNORECASE) for p in AI_CLICHES]

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            for pattern in self._PATTERNS:
                m = pattern.search(s.text)
                if m:
                    phrase = m.group(0)
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix=f'Remove AI cliche: "{phrase}"',
                    ))
                    break  # One per sentence

        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class ReaderFocusedLanguage(BaseRule):
    """CS-08: Use reader-focused language (you/your vs we/our/I)."""
    RULE_ID = "CS-08"
    RULE_NAME = "Reader-focused language"
    CATEGORY = Category.CONTENT_STRUCTURE
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = '"you/your" should appear at least 2x as often as "we/our/I"'

    _YOU = re.compile(r'\b(?:you|your|yours|yourself)\b', re.IGNORECASE)
    _WE = re.compile(r'\b(?:we|our|ours|ourselves|I|my|mine|myself)\b', re.IGNORECASE)

    def evaluate(self, doc):
        all_text = ' '.join(s.text for s in doc.all_sentences)

        you_count = len(self._YOU.findall(all_text))
        we_count = len(self._WE.findall(all_text))

        if we_count == 0:
            ratio = float('inf') if you_count > 0 else 1.0
        else:
            ratio = you_count / we_count

        target = STRUCTURE_TARGETS["you_your_ratio_target"]

        violations = []
        if ratio < target and we_count > 0:
            violations.append(Violation(
                line=0,
                text=f'"you/your": {you_count}, "we/our/I": {we_count} (ratio: {ratio:.1f}x, target: {target}x)',
                fix="Replace some we/our/I language with you/your",
            ))
            score = min(ratio / target, 1.0)
        else:
            score = 1.0

        return self._make_result(
            score, violations,
            metadata={"you_count": you_count, "we_count": we_count, "ratio": round(ratio, 2) if ratio != float('inf') else "inf"},
        )

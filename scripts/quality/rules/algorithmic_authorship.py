"""
Content Quality Scorer — Algorithmic Authorship rules (16 automatable rules).

Based on the 31-rule Algorithmic Authorship framework for AI Overview optimization.
These 16 rules can be detected via regex/heuristics without an LLM.
"""

import re

from scripts.quality.parser import Document
from scripts.quality.types import Category, Severity, Violation
from scripts.quality.config import FILLER_WORDS, BACK_REFERENCES, VAGUE_QUANTIFIERS, get_filler_words, get_back_references, get_vague_quantifiers
from scripts.quality.rules import register
from scripts.quality.rules.base import BaseRule


@register
class IfClausePosition(BaseRule):
    """AA-01: Conditions should come AFTER the main clause."""
    RULE_ID = "AA-01"
    RULE_NAME = "If-clause position"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = 'Sentences starting with "If/When/Unless" should be rewritten: "Do X if Y" not "If Y, do X"'

    _PATTERN = re.compile(r'^(If|When|Unless)\s.+,\s', re.IGNORECASE)

    def evaluate(self, doc):
        violations = []
        opportunities = 0
        for s in doc.all_sentences:
            if self._PATTERN.match(s.text):
                opportunities += 1
                # Check it's not a very short clause (those are fine)
                clause = s.text.split(',')[0]
                if len(clause.split()) > 3:
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix=f"Move the condition after the main clause",
                        context=f'Starts with "{s.text.split()[0]}"',
                    ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total) if total else 1.0
        return self._make_result(score, violations)


@register
class BecauseClausePosition(BaseRule):
    """AA-02: Because-clauses should come after the main clause."""
    RULE_ID = "AA-02"
    RULE_NAME = "Because-clause position"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = 'Sentences starting with "Because" should lead with the conclusion'

    _PATTERN = re.compile(r'^Because\s.+,\s', re.IGNORECASE)

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            if self._PATTERN.match(s.text):
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix="Lead with the conclusion, then add 'because...'",
                ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class VerbFirstInstructions(BaseRule):
    """AA-04: Instructions should start with a verb."""
    RULE_ID = "AA-04"
    RULE_NAME = "Verb-first instructions"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = 'Imperative sentences should start with a verb: "Whip lightly" not "Lightly whip"'

    # Common adverbs that shouldn't start imperative sentences
    _ADVERBS = re.compile(
        r'^(Gently|Lightly|Carefully|Quickly|Slowly|Simply|Always|Never|'
        r'Gradually|Thoroughly|Properly|Regularly|Frequently)\s+\w+',
        re.IGNORECASE
    )

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            m = self._ADVERBS.match(s.text)
            if m:
                adverb = m.group(1)
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix=f'Move "{adverb}" after the verb',
                ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class ShortSentences(BaseRule):
    """AA-07: Sentences should be under 30 words."""
    RULE_ID = "AA-07"
    RULE_NAME = "Short sentences"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Sentences over 30 words should be broken apart"

    _MAX_WORDS = 30

    def evaluate(self, doc):
        violations = []
        total_words = 0
        for s in doc.all_sentences:
            total_words += s.word_count
            if s.word_count > self._MAX_WORDS:
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix=f"Break this {s.word_count}-word sentence into shorter ones",
                ))
        avg = total_words / max(len(doc.all_sentences), 1)
        # Score based on % of sentences that are compliant
        compliant = len(doc.all_sentences) - len(violations)
        score = compliant / max(len(doc.all_sentences), 1)
        return self._make_result(
            score, violations,
            metadata={"avg_sentence_length": round(avg, 1)},
        )


@register
class EntityNaming(BaseRule):
    """AA-10: Name entities 2x before using attributes."""
    RULE_ID = "AA-10"
    RULE_NAME = "Entity naming frequency"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = "Named entities should appear at least twice before switching to pronouns/attributes"

    # Detect capitalized multi-word sequences (proper nouns)
    _ENTITY = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
    # Pronouns that might replace entities
    _PRONOUNS = {"it", "they", "them", "its", "their", "this", "that", "these", "those"}

    def evaluate(self, doc):
        # Track entity mentions across all sentences
        entity_counts = {}
        for s in doc.all_sentences:
            for match in self._ENTITY.finditer(s.text):
                entity = match.group(1)
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

        # Entities mentioned only once are at risk of pronoun confusion
        single_mention = [e for e, c in entity_counts.items() if c == 1]
        total_entities = len(entity_counts)
        if total_entities == 0:
            return self._make_result(1.0, metadata={"entities_found": 0})

        violations = []
        for entity in single_mention:
            violations.append(Violation(
                line=0,
                text=f'Entity "{entity}" appears only once',
                fix=f'Mention "{entity}" at least twice before using pronouns',
            ))

        score = 1.0 - (len(single_mention) / max(total_entities, 1))
        return self._make_result(
            score, violations,
            metadata={"entities_found": total_entities, "single_mention": len(single_mention)},
        )


@register
class NoVagueQuantifiers(BaseRule):
    """AA-13: Use numeric values, not vague quantifiers."""
    RULE_ID = "AA-13"
    RULE_NAME = "No vague quantifiers"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = 'Replace "many", "several", "a lot" with specific numbers'

    def evaluate(self, doc):
        violations = []
        patterns = [re.compile(p, re.IGNORECASE) for p in get_vague_quantifiers()]
        for s in doc.all_sentences:
            for pattern in patterns:
                match = pattern.search(s.text)
                if match:
                    word = match.group(0)
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix=f'Replace "{word}" with a specific number',
                    ))
                    break  # One violation per sentence
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class ExamplesAfterDeclarations(BaseRule):
    """AA-15: Assertions should be followed by examples."""
    RULE_ID = "AA-15"
    RULE_NAME = "Examples after declarations"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = 'Claims should be supported with "for example", "such as", "e.g."'

    _EXAMPLE_MARKERS = re.compile(
        r'(?:for example|for instance|such as|e\.g\.|like\s|including\s)',
        re.IGNORECASE
    )
    # Declarative patterns that should have examples
    _ASSERTION = re.compile(
        r'(?:is|are|was|were|will be|should|must|can)\s+(?:the|a|an)\s+',
        re.IGNORECASE
    )

    def evaluate(self, doc):
        # Count paragraphs with assertions but no examples
        violations = []
        for para in doc.all_paragraphs:
            has_assertion = bool(self._ASSERTION.search(para.text))
            has_example = bool(self._EXAMPLE_MARKERS.search(para.text))
            if has_assertion and not has_example and len(para.sentences) >= 2:
                violations.append(Violation(
                    line=para.line,
                    text=para.text[:120],
                    fix='Add an example: "for example...", "such as..."',
                ))
        total = max(len(doc.all_paragraphs), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class AbbreviationsInParentheses(BaseRule):
    """AA-16: Introduce abbreviations in parentheses on first use."""
    RULE_ID = "AA-16"
    RULE_NAME = "Abbreviations defined"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Uppercase abbreviations (3+ chars) should be introduced: Term (ABBR)"

    # Match uppercase sequences of 3+ chars that look like abbreviations
    _ABBR = re.compile(r'\b([A-Z]{3,})\b')
    # Match the introduction pattern: "Full Name (ABBR)"
    _INTRO = re.compile(r'\w+\s+\(([A-Z]{3,})\)')
    # Common abbreviations that don't need introduction
    _SKIP = {"THE", "AND", "FOR", "NOT", "BUT", "ALL", "NEW", "OLD", "GET", "SET",
             "API", "URL", "CSS", "HTML", "JSON", "XML", "SQL", "PDF", "CSV", "CLI",
             "SEO", "ROI", "CTA", "FAQ", "CEO", "CTO", "CFO", "CMO", "COO",
             "USA", "USD", "EUR", "GBP"}

    def evaluate(self, doc):
        # Find all abbreviations and check if they're introduced
        all_text = ' '.join(s.text for s in doc.all_sentences)
        introduced = set(m.group(1) for m in self._INTRO.finditer(all_text))

        abbrs_found = set()
        for m in self._ABBR.finditer(all_text):
            abbr = m.group(1)
            if abbr not in self._SKIP:
                abbrs_found.add(abbr)

        undefined = abbrs_found - introduced
        violations = []
        for abbr in sorted(undefined):
            # Find first occurrence
            for s in doc.all_sentences:
                if abbr in s.text:
                    violations.append(Violation(
                        line=s.line,
                        text=f'"{abbr}" used without introduction',
                        fix=f'On first use, write: "Full Name ({abbr})"',
                    ))
                    break

        total = max(len(abbrs_found), 1)
        score = 1.0 - (len(undefined) / total) if abbrs_found else 1.0
        return self._make_result(score, violations)


@register
class SamePOSInLists(BaseRule):
    """AA-17: List items should start with the same part of speech."""
    RULE_ID = "AA-17"
    RULE_NAME = "Consistent list item POS"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = "All items in a list should start with the same word type (noun, verb, etc.)"

    def _classify_word(self, word: str) -> str:
        """Simple heuristic POS classification of first word."""
        w = word.lower().rstrip(':.,;')
        # Verbs (imperative)
        if w.endswith(('ize', 'ise', 'ate', 'ify', 'ect')) or w in (
            'use', 'add', 'set', 'run', 'get', 'put', 'make', 'take', 'give',
            'find', 'keep', 'create', 'build', 'check', 'test', 'write',
            'read', 'install', 'configure', 'deploy', 'define', 'implement',
            'enable', 'disable', 'start', 'stop', 'open', 'close',
        ):
            return 'verb'
        # Gerunds (-ing)
        if w.endswith('ing'):
            return 'gerund'
        # Adjectives
        if w.endswith(('ful', 'less', 'ous', 'ive', 'able', 'ible', 'ent', 'ant')):
            return 'adjective'
        # Default to noun
        return 'noun'

    def evaluate(self, doc):
        violations = []
        total_lists = 0
        for lst in doc.all_lists:
            if len(lst) < 3:
                continue
            total_lists += 1
            # Classify first word of each item
            pos_types = [self._classify_word(item.first_word) for item in lst]
            # Check if all same
            if len(set(pos_types)) > 1:
                # Find the majority POS
                from collections import Counter
                most_common = Counter(pos_types).most_common(1)[0][0]
                outliers = [(item, pos) for item, pos in zip(lst, pos_types) if pos != most_common]
                for item, pos in outliers[:3]:  # Cap at 3 violations per list
                    violations.append(Violation(
                        line=item.line,
                        text=item.text[:120],
                        fix=f'Starts with {pos}, but most items start with {most_common}',
                    ))

        score = 1.0 - (len(violations) / max(total_lists * 3, 1)) if total_lists else 1.0
        return self._make_result(score, violations, metadata={"lists_checked": total_lists})


@register
class CompleteSentences(BaseRule):
    """AA-19: Sentences should be complete (no trailing colons as sentences)."""
    RULE_ID = "AA-19"
    RULE_NAME = "Complete sentences"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.INFO
    DESCRIPTION = "Avoid sentences that end with colons (incomplete thoughts)"

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            stripped = s.text.rstrip()
            if stripped.endswith(':'):
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix="Complete the sentence or restructure as a heading",
                ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class NoFillerWords(BaseRule):
    """AA-22: Remove filler words."""
    RULE_ID = "AA-22"
    RULE_NAME = "No filler words"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = 'Remove "also", "actually", "basically", "really", "very", "quite"'

    def evaluate(self, doc):
        violations = []
        filler_patterns = [re.compile(r'\b' + w + r'\b', re.IGNORECASE) for w in get_filler_words()]
        for s in doc.all_sentences:
            for pattern in filler_patterns:
                match = pattern.search(s.text)
                if match:
                    word = match.group(0)
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix=f'Remove filler word "{word}"',
                    ))
                    break  # One violation per sentence
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class NoBackReferences(BaseRule):
    """AA-23: No back-references to other parts of the document."""
    RULE_ID = "AA-23"
    RULE_NAME = "No back-references"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = 'Avoid "as mentioned", "as shown above", "in the previous section"'

    def evaluate(self, doc):
        violations = []
        patterns = [re.compile(p, re.IGNORECASE) for p in get_back_references()]
        for s in doc.all_sentences:
            for pattern in patterns:
                match = pattern.search(s.text)
                if match:
                    phrase = match.group(0)
                    violations.append(Violation(
                        line=s.line,
                        text=s.text[:120],
                        fix=f'Remove "{phrase}" — restate the referenced information',
                    ))
                    break
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class NoLinksFirstWord(BaseRule):
    """AA-25: No links in first word of a sentence."""
    RULE_ID = "AA-25"
    RULE_NAME = "No links in first word"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = "Don't start sentences with a markdown link"

    _LINK_START = re.compile(r'^\[.+?\]\(.+?\)')

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            if self._LINK_START.match(s.text):
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix="Move the link later in the sentence",
                ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class NoLinksFirstSentence(BaseRule):
    """AA-26: No links in the first sentence of a paragraph."""
    RULE_ID = "AA-26"
    RULE_NAME = "No links in first sentence"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.WARNING
    DESCRIPTION = "First sentence of a paragraph should not contain links"

    _LINK = re.compile(r'\[.+?\]\(.+?\)')

    def evaluate(self, doc):
        violations = []
        for para in doc.all_paragraphs:
            if para.sentences and self._LINK.search(para.sentences[0].text):
                violations.append(Violation(
                    line=para.line,
                    text=para.sentences[0].text[:120],
                    fix="Move links to a later sentence in the paragraph",
                ))
        total = max(len(doc.all_paragraphs), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)


@register
class ExternalSourcesInline(BaseRule):
    """AA-31: Use inline citations, not footnotes."""
    RULE_ID = "AA-31"
    RULE_NAME = "Inline sources (no footnotes)"
    CATEGORY = Category.ALGORITHMIC_AUTHORSHIP
    SEVERITY = Severity.OPPORTUNITY
    DESCRIPTION = "Use inline source attribution instead of footnote markers [1], (1)"

    _FOOTNOTE = re.compile(r'(?:\[(\d+)\]|\((\d+)\))(?!\()')  # [1] or (1) but not [1](url)

    def evaluate(self, doc):
        violations = []
        for s in doc.all_sentences:
            match = self._FOOTNOTE.search(s.text)
            if match:
                violations.append(Violation(
                    line=s.line,
                    text=s.text[:120],
                    fix='Replace footnote with inline attribution: "according to [Source]"',
                ))
        total = max(len(doc.all_sentences), 1)
        score = 1.0 - (len(violations) / total)
        return self._make_result(score, violations)

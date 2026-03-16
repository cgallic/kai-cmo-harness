"""Tests for Algorithmic Authorship rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.parser import parse_markdown
from scripts.quality.rules.algorithmic_authorship import (
    IfClausePosition,
    BecauseClausePosition,
    ShortSentences,
    NoVagueQuantifiers,
    NoFillerWords,
    NoBackReferences,
    NoLinksFirstWord,
    NoLinksFirstSentence,
)


def _doc(text):
    return parse_markdown(text)


def test_if_clause_detects_violation():
    doc = _doc("If you want to improve SEO, focus on content quality.")
    rule = IfClausePosition()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0
    assert result.score < 1.0


def test_if_clause_passes_correct():
    doc = _doc("Focus on content quality if you want to improve SEO.")
    rule = IfClausePosition()
    result = rule.evaluate(doc)
    assert len(result.violations) == 0


def test_because_clause_detects_violation():
    doc = _doc("Because SEO is important, many businesses invest in it.")
    rule = BecauseClausePosition()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0


def test_short_sentences_flags_long():
    long = "This is a very long sentence that goes on and on and on with many many words that should probably be broken up into smaller more manageable pieces for better readability and comprehension by the reader."
    doc = _doc(long)
    rule = ShortSentences()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0


def test_short_sentences_passes_short():
    doc = _doc("Short sentence here. Another brief one. Keep it tight.")
    rule = ShortSentences()
    result = rule.evaluate(doc)
    assert len(result.violations) == 0
    assert result.score == 1.0


def test_vague_quantifiers_detects():
    doc = _doc("Many businesses have seen several improvements. There are numerous ways.")
    rule = NoVagueQuantifiers()
    result = rule.evaluate(doc)
    assert len(result.violations) >= 2


def test_vague_quantifiers_passes_specific():
    doc = _doc("42 businesses saw a 37% improvement. There are 12 proven methods.")
    rule = NoVagueQuantifiers()
    result = rule.evaluate(doc)
    assert len(result.violations) == 0


def test_filler_words_detects():
    doc = _doc("It's really quite simple. You just need to actually focus.")
    rule = NoFillerWords()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0


def test_back_references_detects():
    doc = _doc("As mentioned above, SEO is important. In the previous section, we covered basics.")
    rule = NoBackReferences()
    result = rule.evaluate(doc)
    assert len(result.violations) >= 2


def test_links_first_word_detects():
    doc = _doc("[Click here](https://example.com) to learn more.")
    rule = NoLinksFirstWord()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0


def test_links_first_sentence_detects():
    doc = _doc("# Section\n\n[This link](https://example.com) starts the paragraph. Second sentence here.")
    rule = NoLinksFirstSentence()
    result = rule.evaluate(doc)
    assert len(result.violations) > 0


if __name__ == "__main__":
    test_if_clause_detects_violation()
    test_if_clause_passes_correct()
    test_because_clause_detects_violation()
    test_short_sentences_flags_long()
    test_short_sentences_passes_short()
    test_vague_quantifiers_detects()
    test_vague_quantifiers_passes_specific()
    test_filler_words_detects()
    test_back_references_detects()
    test_links_first_word_detects()
    test_links_first_sentence_detects()
    print("All AA rule tests passed!")

"""Tests for content structure rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.parser import parse_markdown
from scripts.quality.rules.content_structure import (
    HookPresence,
    ParagraphLength,
    ActiveVoice,
    NoAICliches,
    ReaderFocusedLanguage,
)


def _doc(text):
    return parse_markdown(text)


def test_hook_detected_with_question():
    doc = _doc("What if your content could rank itself? Here's how.")
    rule = HookPresence()
    result = rule.evaluate(doc)
    assert result.score >= 0.8


def test_hook_detected_with_stat():
    doc = _doc("73% of businesses fail at content marketing. Yours doesn't have to.")
    rule = HookPresence()
    result = rule.evaluate(doc)
    assert result.score >= 0.8


def test_hook_missing():
    doc = _doc("Content marketing is important for businesses in the modern era.")
    rule = HookPresence()
    result = rule.evaluate(doc)
    assert result.score < 0.8


def test_ai_cliches_detects():
    doc = _doc(
        "It's important to note that SEO matters. "
        "In conclusion, you should harness the power of content. "
        "Let's dive into the details."
    )
    rule = NoAICliches()
    result = rule.evaluate(doc)
    assert len(result.violations) >= 3


def test_ai_cliches_passes_clean():
    doc = _doc("SEO drives organic traffic. Content quality determines ranking position.")
    rule = NoAICliches()
    result = rule.evaluate(doc)
    assert len(result.violations) == 0


def test_reader_focused_language():
    doc = _doc("You can improve your rankings by focusing on your audience's needs.")
    rule = ReaderFocusedLanguage()
    result = rule.evaluate(doc)
    # Should have good you/your ratio
    assert result.metadata["you_count"] >= 3


def test_reader_focused_detects_self_centered():
    doc = _doc("We believe our approach creates synergy. I think my method works best. Our team delivers.")
    rule = ReaderFocusedLanguage()
    result = rule.evaluate(doc)
    assert result.metadata["we_count"] >= 3
    assert result.score < 1.0


if __name__ == "__main__":
    test_hook_detected_with_question()
    test_hook_detected_with_stat()
    test_hook_missing()
    test_ai_cliches_detects()
    test_ai_cliches_passes_clean()
    test_reader_focused_language()
    test_reader_focused_detects_self_centered()
    print("All content structure tests passed!")

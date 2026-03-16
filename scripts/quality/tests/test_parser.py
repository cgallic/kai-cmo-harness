"""Tests for the markdown parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.parser import parse_markdown, split_sentences


def test_split_sentences_basic():
    sentences = split_sentences("Hello world. This is a test. Third sentence.", 1)
    assert len(sentences) == 3
    assert sentences[0].text == "Hello world."
    assert sentences[2].text == "Third sentence."


def test_split_sentences_abbreviations():
    sentences = split_sentences("Dr. Smith went to the U.S. for a conference. He returned.", 1)
    # Should not split on Dr. or U.S.
    assert len(sentences) == 2


def test_parse_markdown_basic():
    content = """# Title

First paragraph here. Second sentence.

## Section Two

Another paragraph. With multiple sentences. And a third."""

    doc = parse_markdown(content)
    assert len(doc.sections) >= 2
    assert doc.word_count > 0
    assert doc.sentence_count > 0


def test_parse_markdown_frontmatter():
    content = """---
title: Test
date: 2026-01-01
---

# Real Content

This is the body."""

    doc = parse_markdown(content)
    # Frontmatter should be stripped
    assert doc.word_count > 0
    found_frontmatter = any("title:" in s.text for s in doc.all_sentences)
    assert not found_frontmatter


def test_parse_markdown_code_blocks():
    content = """# Title

Some text before code.

```python
def foo():
    return "bar"
```

Text after code."""

    doc = parse_markdown(content)
    # Code block content should be stripped
    found_code = any("def foo" in s.text for s in doc.all_sentences)
    assert not found_code


def test_parse_markdown_lists():
    content = """# Title

Some items:

- First item
- Second item
- Third item

1. Ordered one
2. Ordered two"""

    doc = parse_markdown(content)
    assert len(doc.all_lists) >= 1
    # Check that list items are parsed
    all_items = [item for lst in doc.all_lists for item in lst]
    assert len(all_items) >= 3


def test_sentence_word_count():
    sentences = split_sentences("This is exactly five words. And three more.", 1)
    assert sentences[0].word_count == 5
    assert sentences[1].word_count == 3


if __name__ == "__main__":
    test_split_sentences_basic()
    test_split_sentences_abbreviations()
    test_parse_markdown_basic()
    test_parse_markdown_frontmatter()
    test_parse_markdown_code_blocks()
    test_parse_markdown_lists()
    test_sentence_word_count()
    print("All parser tests passed!")

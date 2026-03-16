"""
Content Quality Scorer — Markdown parser.

Splits markdown into Document > Section > Paragraph > Sentence
while preserving line numbers.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Abbreviations that should NOT end a sentence
_ABBREVIATIONS = {
    "dr", "mr", "mrs", "ms", "prof", "sr", "jr", "vs", "etc",
    "inc", "ltd", "co", "corp", "dept", "univ", "assn",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "st", "ave", "blvd", "rd",
    "vol", "rev", "sgt", "cpl", "pvt", "capt", "maj", "col", "gen",
    "approx", "dept", "est", "min", "max", "avg",
    "e.g", "i.e", "cf", "al", "fig", "eq",
}

# Pattern to match abbreviations followed by a period
_ABBREV_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(a) for a in _ABBREVIATIONS) + r')\.\s',
    re.IGNORECASE
)

# Sentence-ending pattern
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\'])')


@dataclass
class Sentence:
    """A single sentence with line number."""
    text: str
    line: int
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.text.split())


@dataclass
class ListItem:
    """A list item (ordered or unordered)."""
    text: str
    line: int
    ordered: bool = False
    first_word: str = ""

    def __post_init__(self):
        # Strip list marker to get first word
        cleaned = re.sub(r'^[\s]*(?:[-*+]|\d+[.)]) ', '', self.text).strip()
        words = cleaned.split()
        self.first_word = words[0] if words else ""


@dataclass
class Paragraph:
    """A block of text (may contain multiple sentences)."""
    text: str
    line: int
    sentences: List[Sentence] = field(default_factory=list)

    def __post_init__(self):
        if not self.sentences:
            self.sentences = split_sentences(self.text, self.line)


@dataclass
class Section:
    """A section with heading and content."""
    heading: str
    heading_line: int
    level: int  # 1-6 for h1-h6
    paragraphs: List[Paragraph] = field(default_factory=list)
    lists: List[List[ListItem]] = field(default_factory=list)
    word_count: int = 0


@dataclass
class Document:
    """Parsed markdown document."""
    sections: List[Section] = field(default_factory=list)
    all_paragraphs: List[Paragraph] = field(default_factory=list)
    all_sentences: List[Sentence] = field(default_factory=list)
    all_lists: List[List[ListItem]] = field(default_factory=list)
    raw_lines: List[str] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0


def split_sentences(text: str, start_line: int) -> List[Sentence]:
    """Split text into sentences, handling abbreviations."""
    if not text.strip():
        return []

    # Protect abbreviations by replacing their periods with a placeholder
    _PLACEHOLDER = '\u2060'  # Word joiner (invisible, won't appear in real text)
    protected = text
    for match in _ABBREV_PATTERN.finditer(text):
        old = match.group(0)
        protected = protected.replace(old, old.replace('. ', '.' + _PLACEHOLDER), 1)

    # Also protect common patterns like "U.S." or "e.g."
    def _protect_initials(m):
        return m.group(1) + '.' + _PLACEHOLDER + m.group(2)
    protected = re.sub(r'(\b[A-Z])\.\s*([A-Z]\.)', _protect_initials, protected)

    # Split on sentence boundaries
    parts = _SENTENCE_END.split(protected)

    sentences = []
    for part in parts:
        # Restore placeholders
        restored = part.replace('\u2060', ' ').strip()
        if restored:
            sentences.append(Sentence(text=restored, line=start_line))

    return sentences


def _strip_code_blocks(lines: List[str]) -> List[str]:
    """Replace code block lines with empty strings, preserving line numbers."""
    result = list(lines)
    in_code = False
    for i, line in enumerate(result):
        if line.strip().startswith('```'):
            in_code = not in_code
            result[i] = ''
        elif in_code:
            result[i] = ''
    return result


def _strip_frontmatter(lines: List[str]) -> List[str]:
    """Replace YAML frontmatter lines with empty strings."""
    result = list(lines)
    if not result or result[0].strip() != '---':
        return result

    result[0] = ''
    for i in range(1, len(result)):
        if result[i].strip() == '---':
            result[i] = ''
            break
        result[i] = ''
    return result


def parse_markdown(content: str) -> Document:
    """Parse markdown content into a structured Document."""
    raw_lines = content.split('\n')
    lines = _strip_frontmatter(list(raw_lines))
    lines = _strip_code_blocks(lines)

    doc = Document(raw_lines=raw_lines)

    # Track current section
    current_section = Section(heading="(Introduction)", heading_line=1, level=0)
    current_paragraph_lines: List[str] = []
    current_paragraph_start = 1
    current_list_items: List[ListItem] = []

    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)')
    list_pattern = re.compile(r'^[\s]*(?:[-*+]|\d+[.)]) ')

    def flush_paragraph():
        nonlocal current_paragraph_lines, current_paragraph_start
        text = ' '.join(current_paragraph_lines).strip()
        if text:
            para = Paragraph(text=text, line=current_paragraph_start)
            current_section.paragraphs.append(para)
            doc.all_paragraphs.append(para)
            doc.all_sentences.extend(para.sentences)
        current_paragraph_lines = []

    def flush_list():
        nonlocal current_list_items
        if current_list_items:
            current_section.lists.append(list(current_list_items))
            doc.all_lists.append(list(current_list_items))
            current_list_items = []

    def flush_section():
        nonlocal current_section
        flush_paragraph()
        flush_list()
        # Calculate word count
        current_section.word_count = sum(
            p.text.count(' ') + 1 for p in current_section.paragraphs if p.text
        )
        doc.sections.append(current_section)

    for i, line in enumerate(lines):
        line_num = i + 1  # 1-based

        # Skip empty lines (but flush paragraphs)
        if not line.strip():
            flush_paragraph()
            flush_list()
            continue

        # Check for heading
        heading_match = heading_pattern.match(line)
        if heading_match:
            flush_section()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            current_section = Section(
                heading=heading_text,
                heading_line=line_num,
                level=level,
            )
            continue

        # Check for list item
        if list_pattern.match(line):
            flush_paragraph()
            is_ordered = bool(re.match(r'^\s*\d+[.)]', line))
            current_list_items.append(ListItem(
                text=line.strip(),
                line=line_num,
                ordered=is_ordered,
            ))
            continue

        # Regular text — accumulate into paragraph
        if not current_paragraph_lines:
            current_paragraph_start = line_num
        flush_list()
        current_paragraph_lines.append(line.strip())

    # Flush remaining content
    flush_section()

    # Compute totals
    doc.word_count = sum(s.word_count for s in doc.sections)
    doc.sentence_count = len(doc.all_sentences)

    return doc

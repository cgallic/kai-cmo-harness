# Content Quality Scorer

**ESLint for marketing copy.** Scores content against research-backed rules for AI search visibility, readability, and persuasion.

## Quick Start

```bash
# Score a file (no dependencies, no API key needed)
python -m scripts.quality score article.md --no-llm

# Full score with LLM-based Four U's analysis
export OPENROUTER_API_KEY=your-key
python -m scripts.quality score article.md

# Score all markdown files in a directory
python -m scripts.quality batch content/ --recursive --no-llm

# CI gate: fail if below threshold
python -m scripts.quality score article.md --min-score 70 --no-llm
```

## What It Scores

### Tier 1: Algorithmic Authorship (16 rules, zero deps)

Rules derived from [Algorithmic Authorship](../frameworks/content-copywriting/algorithmic-authorship.md) — 31 rules for ranking in AI Overviews. 16 are automatable:

| Rule | What It Checks |
|------|---------------|
| AA-01 | If-clause comes after main clause |
| AA-02 | Because-clause comes after main clause |
| AA-04 | Instructions start with verbs |
| AA-07 | Sentences under 30 words |
| AA-10 | Entities named 2x before pronouns |
| AA-13 | Specific numbers, not "many/several" |
| AA-15 | Examples follow assertions |
| AA-16 | Abbreviations introduced in parentheses |
| AA-17 | List items start with same word type |
| AA-19 | Complete sentences (no trailing colons) |
| AA-22 | No filler words (also, actually, basically) |
| AA-23 | No back-references (as mentioned above) |
| AA-25 | No links in first word of sentence |
| AA-26 | No links in first sentence of paragraph |
| AA-31 | Inline citations, not footnotes |

### Tier 1: GEO/AEO Signals (4 rules, zero deps)

Based on academic research showing measurable visibility boosts in AI search:

| Signal | Target | Visibility Boost | Source |
|--------|--------|-----------------|--------|
| Citations | 5+ per article | **+115%** | GEO academic synthesis |
| Quotations | 3+ per article | **+40%** | GEO academic synthesis |
| Statistics | 5+ per article | **+37%** | GEO academic synthesis |
| Technical terms | 10+ per article | **+32.7%** | GEO academic synthesis |

### Tier 1: Content Structure (8 rules, optional `textstat`)

| Rule | What It Checks |
|------|---------------|
| CS-01 | Opening hook (question, stat, bold claim) |
| CS-02 | Headers every 200-300 words |
| CS-03 | Paragraphs 2-4 sentences |
| CS-04 | Active voice ≥90% |
| CS-05 | Reading level grade 6-8 |
| CS-06 | Average sentence length 15-20 words |
| CS-07 | No AI cliches (19 patterns) |
| CS-08 | Reader-focused language (you/your ratio) |

### Tier 3: Four U's (LLM-based, requires API key)

Scores content 1-4 on each dimension. Target: 12+/16.

| Dimension | Question |
|-----------|----------|
| **Unique** | Can only YOU write this? |
| **Useful** | Can reader take action today? |
| **Ultra-specific** | Numbers, names, examples? |
| **Urgent** | Reason to read now? |

## CLI Commands

```bash
# Score a single file
python -m scripts.quality score path/to/content.md

# Options
--rules aa,geo,structure,four_us   # Select specific rule sets
--no-llm                           # Skip LLM rules (fast, free)
--format terminal|json|markdown    # Output format
-o report.md                       # Save report to file
--min-score 70                     # CI gate (exit 1 if below)
--model qwen-plus                  # LLM model choice

# Batch score
python -m scripts.quality batch path/to/dir/ --recursive

# List all rules
python -m scripts.quality rules

# Explain a specific rule
python -m scripts.quality explain AA-01
```

## Scoring Algorithm

**Per-rule:** 0.0-1.0 score based on violation ratio.

**Per-category:** Average of rule scores × 100.

**Overall:** Weighted average of categories:
- Algorithmic Authorship: **35%**
- GEO/AEO Signals: **20%**
- Content Structure: **25%**
- Four U's: **20%** (redistributed when `--no-llm`)

**Grades:** A≥90, B≥80, C≥70, D≥60, F<60

## API Endpoint

```bash
curl -X POST http://localhost:8088/webhooks/quality/score \
  -H "X-API-Key: $CMO_GATEWAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your markdown content here", "use_llm": false}'
```

## CI Integration

```yaml
# GitHub Actions
- name: Content Quality Gate
  run: |
    python -m scripts.quality score content/*.md --min-score 70 --no-llm
```

## Architecture

```
scripts/quality/
├── cli.py           # argparse CLI
├── config.py        # Weights, thresholds, patterns
├── engine.py        # Orchestrator
├── parser.py        # Markdown → Document AST
├── prompts.py       # LLM prompt templates
├── types.py         # Dataclasses
├── rules/
│   ├── base.py                    # BaseRule ABC
│   ├── algorithmic_authorship.py  # 16 AA rules
│   ├── geo_signals.py             # 4 GEO rules
│   ├── content_structure.py       # 8 structure rules
│   └── four_us.py                 # LLM Four U's
├── formatters/
│   ├── terminal.py          # Color CLI output
│   ├── json_formatter.py    # JSON report
│   └── markdown_formatter.py # Markdown report
└── tests/
    ├── test_parser.py
    ├── test_aa_rules.py
    ├── test_geo_signals.py
    ├── test_content_structure.py
    ├── test_engine.py
    └── fixtures/
        ├── perfect.md      # Scores 90+ (A)
        ├── terrible.md     # Scores ~70 (C)
        └── needs-work.md   # Scores ~85 (B)
```

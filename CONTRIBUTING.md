# Contributing to Kai CMO Harness

Thanks for contributing. Here's how to make Kai better.

## What to contribute

The most valuable contributions are to the **knowledge base** — the frameworks, checklists, and playbooks that make Kai's output good.

| Type | Where | How |
|------|-------|-----|
| Marketing framework | `knowledge/frameworks/` | Drop a markdown file with "use when" triggers + rules |
| Channel guide | `knowledge/channels/` | Platform-specific tactics, limits, and gotchas |
| Checklist | `knowledge/checklists/` | Yes/no validation questions for a content type |
| Persona | `knowledge/personas/` | Audience archetype with frustrations, language, and hooks |
| Skill contract | `harness/skill-contracts/` | YAML defining format rules (word count, gates, sections) |
| Quality gate | `scripts/quality_gates/` | Python script that scores or validates content |
| Ad platform policy | `harness/references/` | Platform TOS distilled into writing rules |
| Skill (new command) | `harness/skills/` | New `/kai-*` slash command |
| Bug fix | anywhere | Fix what's broken |

## How to add a framework

1. Create a markdown file in the right subdirectory of `knowledge/frameworks/`
2. Start with a "Quick Reference" section (5-10 bullet points)
3. Add a "use when" trigger at the top: `> **Use when:** [situation]`
4. Include concrete examples, not abstract principles
5. Add your framework to `knowledge/_index.md`

Example structure:

```markdown
# Framework Name

> **Use when:** Writing [content type] for [audience/platform].

## Quick Reference

- Rule 1
- Rule 2
- Rule 3

## Detailed Rules

### Rule 1: [Name]

[Explanation with examples]

**Do:**
- Example of correct usage

**Don't:**
- Example of incorrect usage
```

## How to add a checklist

1. Create a markdown file in `knowledge/checklists/`
2. Each item is a yes/no validation question
3. Group items by category
4. Add it to `knowledge/_index.md`

```markdown
# [Content Type] Checklist

## Structure
- [ ] Does the headline include the primary keyword?
- [ ] Is the introduction under 50 words?

## Quality
- [ ] Does it score 12+/16 on the Four U's?
- [ ] Are there zero Tier 1 banned words?
```

## How to add a skill

1. Create a directory in `harness/skills/` named `kai-[your-skill]`
2. Add a single file: `SKILL.md`
3. Use this format:

```yaml
---
name: kai-[your-skill]
description: [What it does and when to use it. Include trigger phrases.]
---

# Skill content — instructions for Claude Code

[Your skill prompt here]
```

4. Add the skill to the router in `harness/skills/kai/SKILL.md`

## How to improve quality gates

The gate scripts are in `scripts/quality_gates/`:

- `four_us_score.py` — Content quality scorer
- `banned_word_check.py` — Jargon and AI slop detector
- `seo_lint.py` — SEO rule enforcer

PRs welcome for:
- Better scoring heuristics
- New banned words or AI-tell phrases
- Additional SEO rules
- New gate types (readability, accessibility, etc.)

All gates must:
- Accept `--text "content"` and `--file path` inputs
- Exit 0 on pass, exit 1 on fail
- Print clear pass/fail output with specific issues

## Quality standards

- **No AI slop.** Don't add frameworks full of vague advice. Specific, actionable, tested.
- **Show your work.** If a framework comes from research, link it. If it comes from experience, say what you tested it on.
- **Follow existing patterns.** Read 2-3 existing files in the same directory before creating yours.
- **Test your additions.** Run the quality gates on sample output to make sure your framework produces good content.

## Pull request process

1. Fork the repo
2. Create a branch: `git checkout -b add-[thing]`
3. Make your changes
4. Run the quality gates on any content you've added
5. Open a PR with a description of what you added and why

## Code of conduct

Be direct. Be helpful. Don't waste people's time.

## Questions?

Open a GitHub issue or discussion. We respond within 24 hours.

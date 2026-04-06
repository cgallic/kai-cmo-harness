# How Claude Code Marketing Automation Works Inside Kai CMO

**Meta:** A technical deep-dive into Kai CMO — the open-source Claude Code marketing automation system with 153 knowledge files, 3 quality gates, and a pipeline that rejects bad copy before you see it.

**Publish date:** Apr 12 (T+3)
**Cross-post to:** dev.to, Hashnode
**Target keywords:** Claude Code marketing automation, Claude Code skills tutorial, AI content quality
**Persona:** Claude Code power user, technical founder
**SEO:** Algorithmic Authorship rules applied

---

The announcement post covered what Kai does. This post covers how Claude Code marketing automation works under the hood — the architecture, the knowledge base, and the quality system that keeps output from being garbage.

Read this if you want to understand the system. Read it twice if you want to contribute. Kai turns Claude Code marketing automation into something any founder can install and run.

## Architecture: how Claude Code marketing automation is structured

Kai has three layers. Each one does a different job.

### Layer 1: Knowledge base (153 files)

The `knowledge/` directory is the marketing brain. It holds everything Kai knows about marketing — organized by type.

**Frameworks** (`knowledge/frameworks/`) — 23 files covering three domains:

- **Content & copywriting** — Algorithmic Authorship (48 SEO writing rules), Perception Engineering (3-layer persuasion framework), Four U's (content quality scoring), headline formulas, and content architecture patterns.
- **AEO & AI search** — 12 files on Answer Engine Optimization. Patent analysis of Google's Information Gain scoring. Reverse-engineered Perplexity ranking signals. A full playbook for getting cited by AI search engines.
- **Meta advertising** — Auction mechanics, audience signal science, creative fatigue patterns, and budget optimization.

**Channels** (`knowledge/channels/`) — 11 files. One per marketing channel. Each covers platform-specific rules, proven playbooks, and pitfalls. Email lifecycle, LinkedIn articles, TikTok algorithm, podcast strategy, press releases, and more.

**Checklists** (`knowledge/checklists/`) — 17 validation checklists. Content, SEO, email, Meta ads, paid acquisition, PR, perception engineering, technical SEO audit SOP, and TikTok.

**Personas** (`knowledge/personas/`) — 8 audience archetypes. Each persona has a detailed psychology profile, 10 specific frustrations, language patterns (what they think vs. what they say), and hooks that resonate.

### Layer 2: Harness (the pipeline engine)

The `harness/` directory controls how content gets produced.

**Skill contracts** (`harness/skill-contracts/`) — YAML files that define the rules for each content format. A blog post contract specifies word count ranges, required sections, minimum quality scores, and which gates to run. An email contract has different rules than a blog post.

**Brief schema** (`harness/brief-schema.md`) — Every piece starts with a brief. The brief defines the persona, angle, keywords, format, and success criteria before a single word gets written.

**Platform references** (`harness/references/`) — 12 files covering ad platform policies and compliance rules. Google Ads TOS (991 lines). Meta advertising policies (931 lines). TikTok (1,020 lines). Plus a master FTC/GDPR/CAN-SPAM/COPPA reference (1,500 lines).

Kai loads the right reference before writing any ad copy. Your Meta ad gets checked against Meta's actual policies. Your Google RSA gets checked against Google's actual restrictions.

### Layer 3: Quality gates (the linter)

Three scripts in `scripts/quality_gates/` validate everything:

**`four_us_score.py`** — Scores content on four dimensions:

| Dimension | Question | Score |
|-----------|----------|-------|
| **Unique** | Can only WE write this? | 1-4 |
| **Useful** | Can the reader take action? | 1-4 |
| **Ultra-specific** | Are there numbers, examples, named tools? | 1-4 |
| **Urgent** | Is there a reason to engage today? | 1-4 |

Blog posts and articles need 12/16 minimum. Ads and emails need 10/16. Any single dimension below 2 triggers a rewrite.

**`banned_word_check.py`** — Detects corporate jargon and AI slop. A blocklist of Tier 1 words triggers instant rejection. No exceptions. The script also catches AI-tell phrases — the ones you've seen a thousand times in ChatGPT output. If it sounds like a machine wrote it, the gate kills it.

**`seo_lint.py`** — Enforces Algorithmic Authorship rules on search content. Checks sentence structure (conditions after main clauses), instruction format (verbs first), sentence length, list formatting, entity naming, and more.

## The pipeline

Every piece of content follows the same path:

```
Brief → Write → Score → Check → Lint → Pass/Fail
```

1. Kai loads the right framework for the content type
2. Kai loads the skill contract for format-specific rules
3. Kai loads platform policy (for ads)
4. Kai writes against the framework + persona
5. Quality gates run automatically
6. Max 2 auto-retries on failure
7. After 2 failures, Kai surfaces the specific issues to you instead of looping

No content ships without passing all applicable gates.

## How MARKETING.md works

The first time you run a Kai command in a project, Kai creates `MARKETING.md` in your project root. This file is the product marketing bible — ICP, personas, value prop, competitive landscape, brand voice.

Kai builds `MARKETING.md` by reading your codebase. It pulls from your README, CLAUDE.md, package.json, route files, schema definitions, landing pages, and any existing marketing materials.

Every command after the first reads `MARKETING.md` and skips product discovery. Kai knows your product. It starts working.

Update `MARKETING.md` when your product changes. Kai reads it fresh each time.

## Contributing

The knowledge base is the most valuable part of Kai. Here's how to make it better:

**Add a framework** — Drop a markdown file in `knowledge/frameworks/`. Follow the format: quick reference section, detailed explanation, examples, and "use when" triggers.

**Add a checklist** — Drop a markdown file in `knowledge/checklists/`. Each item should be a yes/no validation question.

**Improve quality gates** — The scoring scripts in `scripts/quality_gates/` are Python. PRs welcome for better heuristics, new detection patterns, or additional gate types.

**Add a skill contract** — YAML files in `harness/skill-contracts/`. Define the format, word count, required sections, quality thresholds, and applicable gates.

**Report issues** — Open a GitHub issue. Tell us what command you ran, what you expected, and what you got.

## Install

```
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install && cp -r /tmp/kai-install/harness/skills/kai* ~/.claude/skills/ && rm -rf /tmp/kai-install && echo "Installed! Type /kai to start."
```

30 seconds. Type `/kai` to see all 31 commands.

**[Get Kai on GitHub →]**

---

*Built by Connor Gallic. The full knowledge base is MIT licensed.*

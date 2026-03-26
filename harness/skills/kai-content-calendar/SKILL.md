---
name: kai-content-calendar
description: Plan and produce a content calendar — a month (or quarter) of blog posts, LinkedIn articles, and SEO content mapped to business goals, personas, and keywords. Generates briefs for each piece, optionally batch-produces all content with quality gates. Use when "content calendar", "plan blog content", "monthly content", "quarterly content plan", "what should we publish", "content strategy", "editorial calendar", or any request to plan multiple pieces of content over time.
---

Plan and optionally batch-produce a content calendar. Maps content to business goals, personas, keywords, and publishing cadence.

## Phase 1: Strategy Discovery

Ask the user (or read project files):

1. **Product/brand** — what are we creating content for?
2. **Time horizon** — 1 month? 1 quarter?
3. **Publishing cadence** — how many pieces per week? (recommend 2-3/week for SEO traction)
4. **Content types** — blog only? Blog + LinkedIn? Blog + email newsletter?
5. **Primary goals** — SEO traffic? Thought leadership? Lead gen? Product education?
6. **Target keywords** — any keyword research already done?
7. **Existing content** — any posts already published we should build on?

## Phase 2: Content Map

Generate `workspace/content-calendar/_content-map.md`.

### Topic Clustering

Group content into **pillars** (broad topics) and **clusters** (specific subtopics that link back to the pillar).

```
Pillar: [Broad Topic]
├── Cluster: [Specific angle 1] — targets "[keyword]"
├── Cluster: [Specific angle 2] — targets "[keyword]"
└── Cluster: [Specific angle 3] — targets "[keyword]"
```

This structure builds topical authority for SEO. Load `E:\Dev2\kai-cmo-harness-work\knowledge\frameworks\content-copywriting\qdp-qdh-qds-content-architecture.md` for the full architecture framework.

### Calendar Table

| Week | Date | Title | Format | Pillar | Keyword | Persona | Priority |
|------|------|-------|--------|--------|---------|---------|----------|
| 1 | Mon | ... | Blog | ... | ... | ... | P0 |
| 1 | Thu | ... | LinkedIn | ... | ... | ... | P1 |
| 2 | Mon | ... | Blog | ... | ... | ... | P0 |

### Persona Rotation

Rotate across personas to avoid speaking to only one audience. Map each piece to one of the 8 personas from `E:\Dev2\kai-cmo-harness-work\knowledge\personas\_persona-index.md`.

### Approval Gate

Present the content map to the user. Confirm:
- Topic selection and angles
- Keyword targets
- Persona assignments
- Publishing dates
- Any pieces they want to add/remove/reorder

## Phase 3: Brief Generation

For each piece on the calendar, generate a brief using the schema from `E:\Dev2\kai-cmo-harness-work\harness\brief-schema.md`.

Output briefs to `workspace/content-calendar/briefs/[week]-[slug].json`.

Each brief must have:
- 3 hook variants
- Specific angle (not just restating the keyword)
- Named proof/data source
- Clear CTA

## Phase 4: Batch Production (Optional)

If the user wants content produced (not just planned), batch-produce using `/kai-write` workflow:

### Per-Piece Workflow

1. Load the framework based on format:
   - Blog/SEO: `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` + `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`
   - LinkedIn: `knowledge/channels/linkedin-articles.md`
2. Load the skill contract: `harness/skill-contracts/blog-post.yaml` or `harness/skill-contracts/linkedin-article.yaml`
3. Load the persona file
4. Write the piece
5. Run quality gates (Four U's >= 12/16 for blog, banned words, SEO lint)
6. Max 2 retries on failure

All paths relative to `E:\Dev2\kai-cmo-harness-work\`.

### Parallelization

Pieces in different pillars can be written in parallel. Pieces in the same cluster should be written sequentially (internal linking and angle differentiation matters).

### Batch Output

```
workspace/content-calendar/
├── _content-map.md              # The full calendar
├── briefs/
│   ├── w1-slug-1.json
│   ├── w1-slug-2.json
│   └── ...
├── drafts/
│   ├── w1-slug-1.md
│   ├── w1-slug-2.md
│   └── ...
└── _quality-report.md
```

## Phase 5: Quality Report

```markdown
# Content Calendar Quality Report

## Summary
- Total pieces planned: [N]
- Produced: [N]
- Passed all gates: [N]
- Average Four U's: [X]/16

## Per-Piece Results
| Title | Format | Persona | Four U's | Banned | SEO Lint | Status |
|-------|--------|---------|----------|--------|----------|--------|

## Internal Linking Map
[Which pieces link to which — pillar/cluster structure]

## SEO Coverage
[Keywords targeted, search volume estimates if available, content gaps]
```

## Phase 6: Distribution Notes

Generate `workspace/content-calendar/_distribution.md`:
- Which pieces to cross-post to LinkedIn
- Email newsletter inclusion schedule
- Social media promotion plan per piece
- Internal linking instructions for the blog

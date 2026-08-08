# SEO Content Writing Guide

> **Use when:** Writing content optimized for search rankings, Featured Snippets, AI Overviews, or Google AI Mode visibility.

## Quick Reference

- Apply the 31 Algorithmic Authorship rules (see `frameworks/algorithmic-authorship.md`)
- Structure sentences: main clause FIRST, conditions SECOND
- Use numeric lists for steps/methods, bulleted for types
- Name entities twice before switching to attributes
- Bold answers, not query terms

---

## Google Search + AEO Baseline (2026)

Google treats AI Overviews and AI Mode as Google Search features. AEO/GEO work for Google should strengthen normal SEO, not replace it.

**Google requirements for generative AI visibility:**
- Page is crawlable by Googlebot
- Page is indexable and eligible to appear with a snippet
- Main content is visible in rendered HTML
- Content is helpful, reliable, people-first, and non-commodity
- Facts are supported by experience, sources, images, video, product data, or local data where relevant

**Not required for Google AI Overviews / AI Mode:**
- `llms.txt` or special AI text files
- Special AI-only schema or markup
- Forced Markdown versions of pages
- "Chunking" content into tiny passages
- Separate pages for every fan-out, PAA, or long-tail query variation

Use AEO formatting to make useful content clearer. Do not use it to create doorway pages, keyword-stuffed variants, or content written only for AI systems.

---

## Evidence Policy for SEO Content

Every non-obvious claim needs a source tier before drafting:

| Tier | Use in SEO content |
|---|---|
| Official requirement | Crawlability, indexability, snippets, robots, structured-data eligibility, platform policy |
| Official best practice | Google helpful content, AI optimization guide, Search Essentials, Bing AI guidance |
| Academic study | GEO, AI visibility measurement, information retrieval research |
| Vendor/platform measurement | Bing AI Performance, Search Console, analytics exports, tool reports with methodology |
| Practitioner observation | Named expert or agency research with clear caveats |
| Internal measurement | Client data, case studies, experiments, support logs, call logs |
| Hypothesis | Ideas to test, not facts to publish |
| Missing data | List in the brief or `_data-gaps.md`; do not invent numbers |

**Claim rules:**
- Use sourced numbers only when the source, date, and scope are stated.
- Do not promise deterministic ranking, AI citations, or ChatGPT/Claude/Perplexity inclusion.
- Do not reuse study effect sizes as universal outcomes.
- Label AI-assisted drafts as drafts until a human verifies facts, sources, and experience evidence.

**Data-gap language:**

```markdown
Data gap: We do not have Search Console access for this page, so we cannot claim current query impressions or CTR.
Data gap: No AI visibility tool or repeated manual prompt sample was available, so AI citation frequency is unknown.
Data gap: The client has not supplied original screenshots, product data, call logs, or customer quotes. This draft must avoid performance claims.
```

---

## Core SEO Content Principles

### Sentence Structure for Passage Ranking

Google's passage ranking evaluates individual passages, not just documents. Structure sentences for maximum extractability:

```
Wrong: "If a student studies, the student passes."
Right: "The student passes if the student studies."

Wrong: "Because of Y, the X doesn't behave..."
Right: "X doesn't behave... because of Y."

Wrong: "Lightly whip the cream."
Right: "Whip the cream lightly." (Start with verb)
```

### Entity Naming Rules

Name entities twice before switching to attributes:

```
"Tesla Motors refers to an electric car manufacturer. Tesla Motors
manufactures different types and models. The electric car models of
Tesla Motors involve Model S, 3, and X."
```

### List Formatting

**Use NUMBERED lists for:**
- Steps and processes
- Methods and how-tos
- Rankings and comparisons
- "What are the best..." queries

**Use BULLETED lists for:**
- Types and categories
- Features and characteristics
- Non-sequential items

---

## Featured Snippet Optimization

### Definition Snippet Format
```
## What Is [Term]?

[Term] is [definition in one clear sentence]. [Supporting detail].
[Benefit or key characteristic].
```

**Example:**
```
## What Is Content Marketing?

Content marketing is a strategic approach focused on creating and
distributing valuable, relevant content to attract and retain a
clearly defined audience. Unlike traditional advertising, content
marketing provides value before asking for anything in return.
```

### List Snippet Format
```
## How to [Achieve X]

Follow these [number] steps to [achieve X]:

1. [Action verb] [specific action]
2. [Action verb] [specific action]
3. [Action verb] [specific action]
```

### Table Snippet Format
```
## [Topic] Comparison

| Factor | Option A | Option B |
|--------|----------|----------|
| [Metric] | [Value] | [Value] |
```

---

## Google AI Overview / AI Mode Optimization

Google AI Overviews and AI Mode use the Google Search index, core ranking systems, RAG, and query fan-out. Optimize the page so it is useful to humans and easy for Search to retrieve, understand, and cite.

### What to Strengthen

1. **Index and snippet eligibility:** Avoid accidental `noindex`, blocked Googlebot access, `nosnippet`, or overly restrictive `max-snippet` rules on pages that should be visible.
2. **Non-commodity content:** Add first-hand experience, unique analysis, original examples, named data, screenshots, images, videos, product details, or local details.
3. **Clear answer structure:** Put the direct answer under the relevant heading before nuance, caveats, or sales copy.
4. **Intent coverage:** Use query fan-out and PAA research to improve coverage on a useful page or cluster. Create a separate page only when the subtopic deserves a standalone answer.
5. **Rich source context:** Include product feeds, Merchant Center data, Google Business Profile details, structured data, image SEO, and video SEO where the business model makes those assets relevant.

### Multi-Engine Notes

| Engine | Writing implication | Measurement caveat |
|---|---|---|
| Google AI Overviews / AI Mode | Start with SEO fundamentals, non-commodity content, snippet eligibility, media/product/local data | No universal AI Overview-only Search Console report |
| Bing / Copilot | Use clear headings, tables, FAQ blocks, evidence, and IndexNow where appropriate | Bing AI Performance is a Microsoft-specific AI citation report |
| ChatGPT Search | Allow `OAI-SearchBot` where visibility matters; make pages self-contained and source-backed | Separate ChatGPT referrals and citations from Bing and Google |
| Claude | Make pages accessible to `Claude-SearchBot` and `Claude-User` where desired; use readable HTML | Claude answers vary by user prompt and retrieval context |
| Perplexity | Keep facts current, sourced, and extractable; respect robots policy | Perplexity citations are not proof of conversion impact |
| Grok / X | Maintain public entity consistency and useful X presence where the audience uses X | Do not require a Grok crawler token unless xAI publishes one |

### Optimal Structure

```
## [Query as Question]

[Direct answer in first sentence]. [Entity named twice].
[Supporting explanation with specifics].

Key [factors/steps/types] include:

1. **[Headword]:** [Explanation of 15-25 words]
2. **[Headword]:** [Explanation of 15-25 words]
3. **[Headword]:** [Explanation of 15-25 words]

[Concluding statement connecting back to query].
```

---

## Topic and Query Integration

### Placement Priority
1. **Title/H1** - Name the topic or primary entity clearly if it matches the page intent
2. **First answer block** - Mention the query, entity, or close variant naturally
3. **H2 subheadings** - Use facet language that helps readers scan the answer
4. **Body** - Repeat terms only when they clarify meaning; do not chase density
5. **Meta description** - Summarize the user benefit and topic in natural language
6. **URL slug** - Keep it stable, short, and descriptive
7. **Image alt text** - Describe the image accurately; include topic language only when it fits

### Semantic Keyword Expansion

Include related terms and synonyms:
- Primary: "content marketing"
- Secondary: "content strategy," "content creation"
- Related: "blog posts," "social media content," "thought leadership"

---

## Internal Linking Rules

### Where NOT to Link
- First word of any sentence
- First sentence of any paragraph
- First line of any paragraph

### Correct Linking Pattern
```
Wrong: "[Content marketing](link) requires consistency."

Right: "Successful brands publish content regularly and measure
results. A solid [content marketing strategy](link) includes
both creation and distribution plans."
```

### Link Placement Best Practices
- Add context before the link
- Match source and target page intent
- One internal link per heading section (max)
- Use descriptive anchor text

---

## External Source Integration

### Wrong (Footnote Style)
```
The biotin is found effective for cell membrane protection (1).
1. Wisconsin University, Dr. Najork Center, 2021.
```

### Correct (Contextual Integration)
```
Biotin is found effective for protecting the cell membrane in 2021,
according to Dr. Nephew and Dr. Kotlin from Wisconsin University
during their research on Effects of Kotlin on Cell Membrane.
```

---

## Content Structure Template

```markdown
# [Primary Keyword in Title]

[Hook with keyword in first sentence. Direct answer to search intent.]

## [H2 with Secondary Keyword]

[Paragraph answering subquery. Use specific numbers and examples.]

### [H3 with Related Term]

Key [factors/steps/benefits] include:

1. **[Headword]:** [15-25 word explanation]
2. **[Headword]:** [15-25 word explanation]
3. **[Headword]:** [15-25 word explanation]

## [Next Section H2]

[Continue with valuable, specific content...]

## Conclusion

[Summary connecting back to primary query. CTA.]
```

---

## Quick Rules Reference

| Rule | Description |
|------|-------------|
| Conditions after main clause | "Do X if Y" not "If Y, do X" |
| Verbs first in instructions | "Whip lightly" not "Lightly whip" |
| Short sentences | Break complex sentences apart |
| Anchor words | Connect sequential sentences |
| Entity twice before attributes | Name → Name → Attribute |
| Numbers over vague terms | "three reasons" not "several reasons" |
| Examples always | Follow declarations with examples |
| Bold answers | Not query-matching terms |
| No first-line links | Context before any internal link |
| Inline sources | Not footnotes |

---

## Checklist

### Pre-Writing
- [ ] Primary keyword identified
- [ ] Search intent understood (informational, transactional, navigational)
- [ ] Competitive SERP analyzed
- [ ] Target snippet format determined

### Writing
- [ ] Keyword in first 100 words
- [ ] Main clauses before conditions
- [ ] Instructions start with verbs
- [ ] Entities named twice before attributes
- [ ] Specific numbers used (not "many" or "several")
- [ ] Examples follow every declaration
- [ ] Answers bolded (not query terms)

### Formatting
- [ ] Numeric lists for steps/methods
- [ ] Bulleted lists for types
- [ ] Same part of speech in list items
- [ ] H2s include keywords
- [ ] Paragraphs 2-4 sentences

### Linking
- [ ] No links in first sentence/line
- [ ] Context provided before links
- [ ] Descriptive anchor text used
- [ ] 3-5 internal links per 1,000 words

### Final Check
- [ ] Content answers search query directly
- [ ] Snippet-worthy answer exists in first 100 words
- [ ] All sources integrated contextually
- [ ] Reading level appropriate (6th-8th grade)
- [ ] Every quantitative/client-facing claim has a source tier and retrieval date
- [ ] Missing rankings, AI citations, traffic, conversions, Core Web Vitals, backlinks, or schema findings are listed as data gaps

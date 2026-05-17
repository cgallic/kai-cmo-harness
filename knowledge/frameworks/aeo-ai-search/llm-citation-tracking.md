# LLM Citation Tracking and Earned Source Development

## Purpose

This framework covers how to measure brand visibility in AI answers and improve the source ecosystem that AI search systems can legitimately cite. It replaces citation manipulation, fake community activity, undisclosed placements, client network schemes, and review manipulation with:

- Citation tracking across AI surfaces
- Earned source development
- Disclosure-safe community participation
- Source-quality evaluation
- Evidence-labeled reporting

Use this workflow for ChatGPT Search, Claude Search, Perplexity, Gemini and Google AI Search features, Bing/Copilot, and other answer engines where citations, mentions, or summarized sources affect brand discovery.

## Evidence Labels

Use these labels in briefs, audits, and client-facing reports.

| Label | Meaning | Example |
| --- | --- | --- |
| Official | Published by the platform or standards author | OpenAI crawler docs, Google Search Central, Anthropic crawler docs |
| Observed | Verified in our own tests, logs, or exported answer sets | A Perplexity answer cited three competitor pages on May 16, 2026 |
| Vendor-reported | From a third-party tracking tool | WriteSonic or Profound visibility share |
| Inference | Reasonable interpretation from observed patterns | A source likely influences local answers because it appears in Bing and Perplexity citations |
| Policy requirement | Required by law, platform rules, or Kai policy | Disclose affiliation in forums and sponsored placements |
| Unverified | Mentioned by a source but not confirmed | Treat as a research lead, not a claim |

Never present inferred or vendor-reported data as official platform behavior.

## Non-Negotiable Safety Rules

Do not use these tactics:

- Fake accounts, purchased aged accounts, vote manipulation, or staged question-and-answer threads
- Undisclosed paid mentions, guest posts, affiliate placements, or sponsored citations
- Fake reviews, review gating, or review volume manipulation
- Cross-client link networks built primarily to influence AI outputs
- AI-generated community filler posted as if it came from real customers
- Claims that a tactic "controls" or "manipulates" AI answers

Use these replacements:

- Real subject-matter participation with affiliation disclosed
- Earned editorial citations from relevant publications, associations, partners, data pages, and expert directories
- Original research, case studies, technical references, and public data assets
- Accurate local profiles, product documentation, Organization schema, author pages, and crawlable canonical pages
- Transparent outreach that states who we are, what evidence we can provide, and whether any commercial relationship exists

## Part 1: What To Track

Track citations and mentions as measurement data, not as a promise of rank.

| Metric | Definition | Evidence Label |
| --- | --- | --- |
| Prompt set | The exact prompts or query themes tested | Observed |
| Engine and surface | ChatGPT Search, Claude Search, Perplexity, Google AI Overview, AI Mode, Bing/Copilot, etc. | Observed |
| Date, location, and account state | Date tested, geography, language, logged-in or logged-out status when known | Observed |
| Cited URLs | URLs shown as sources or supporting links | Observed |
| Mentioned entities | Brands, products, people, and competitors named in the answer | Observed |
| Answer position/context | Whether the entity is recommended, compared, excluded, or only referenced | Observed |
| Source type | Owned site, earned media, directory, forum, review platform, social, government, academic, etc. | Observed |
| Source quality score | Rubric score from this document | Inference |
| Visibility share | Percent of prompt runs where the brand is cited or mentioned | Vendor-reported or Observed |
| Change notes | What changed since the previous run | Observed |

Keep screenshots or exports for important claims. AI answers vary by time, personalization, location, and engine release.

## Part 2: Tracking Tools

### Third-Party Trackers

Tools such as WriteSonic AI Rank Tracker, Profound, and similar platforms can speed up repeated prompt tracking.

Treat their outputs as **Vendor-reported** unless we manually verify the answer, citation, and date.

Use them to:

- Build a recurring prompt set
- Export cited URLs
- Compare competitor mentions
- Monitor week-over-week movement
- Find source gaps where competitors are cited and the client is absent
- Prioritize manual verification

Do not use them to:

- Claim platform-wide market share without caveats
- Promise citation gains
- Replace primary source review
- Justify manipulative placement tactics

### Manual Tracking

Manual tracking is slower but often more defensible for audits and strategy.

Minimum fields:

```text
date:
engine:
surface:
location:
prompt:
answer_summary:
brand_mentioned: yes/no
competitors_mentioned:
cited_urls:
source_types:
notes:
evidence_label:
```

Run important prompts several times. Record variance instead of smoothing it away.

## Part 3: Citation Gap Analysis

Use citation exports to understand which sources an engine currently trusts for a topic.

1. Export or manually collect cited URLs for target prompts.
2. Group URLs by source type: owned, editorial, directory, review, forum, social, public data, academic, government, partner, competitor.
3. Mark which sources mention the client, competitors, both, or neither.
4. Score each source with the source-quality rubric below.
5. Identify legitimate paths to improve coverage:
   - Update the client's canonical content
   - Publish original data or expert analysis
   - Correct missing or inconsistent third-party profiles
   - Pitch a journalist, analyst, association, or partner with useful evidence
   - Participate in relevant communities with disclosure
6. Log what is possible, what is not appropriate, and what requires client approval.

The output is a source map, not a target list for undisclosed placements.

## Part 4: Earned Source Development

The best citation work gives neutral sources better facts to cite.

### High-Value Source Assets

Create assets that deserve citations:

- Original research with methodology, sample size, collection dates, and limitations
- Benchmark reports with downloadable tables or charts
- Case studies with named constraints, measurable outcomes, and client approval
- Technical explainers with diagrams, definitions, and source links
- Local market pages grounded in verified business data
- Product documentation, pricing pages, comparison pages, and support docs
- Expert author pages with credentials and contact paths
- Public policy, safety, compliance, or implementation references

Every quantitative claim must include a source, methodology note, or data gap.

### Outreach Principles

Outreach must be transparent and useful.

- State the sender, client, affiliation, and purpose.
- Offer evidence, data, expert commentary, or corrections.
- Disclose compensation, sponsorship, affiliate terms, or commercial relationships before publication.
- Respect editorial independence. Do not request false praise.
- Ask for factual correction when a page is outdated or incomplete.
- Keep records of what was offered and what was published.

### Suitable Outreach Targets

Prioritize sources with a natural reason to care:

- Journalists covering the topic
- Industry analysts and newsletter authors
- Associations and professional bodies
- Partners and integrations
- Educational resources and public guides
- Local directories and chambers of commerce
- Podcast hosts and event organizers
- Comparison pages that already include the category

Avoid sources whose only value is easy link placement.

## Part 5: Disclosure-Safe Community Participation

Forums, Q&A sites, social groups, and review platforms can be useful sources when participation is real. They are high-risk when used for covert promotion.

### Allowed

- Answer questions from a real account tied to a real person.
- Disclose affiliation when recommending the client, employer, product, or partner.
- Share first-hand experience, public documentation, or neutral comparisons.
- Correct misinformation with sources.
- Participate in communities before asking for attention.
- Follow each community's posting and self-promotion rules.
- Encourage real customers to leave honest reviews without incentives or gating.

### Not Allowed

- Buying, renting, or aging accounts for posting campaigns
- Coordinated voting, commenting, or staged engagement
- Creating one account to ask a question and another to recommend the client
- Posting AI-generated testimonials or customer stories
- Hiding affiliation behind "just a user" language
- Paying for mentions without disclosure
- Seeding fake local, legal, medical, financial, or safety experiences

### Practical Community Workflow

1. Read the community rules.
2. Decide whether the brand has standing to participate.
3. Use a real profile with affiliation visible or disclosed in the post.
4. Answer only when the response is genuinely useful without the brand mention.
5. Add the brand only when it is directly relevant and disclosed.
6. Record the post URL, author, disclosure language, and moderation status.

If disclosure would make the post feel inappropriate, do not post.

## Part 6: Source-Quality Evaluation Rubric

Score every candidate source before recommending work around it.

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Accessibility | Blocked, gated, or JS-only | Partially crawlable | Clean crawlable HTML with stable URLs |
| Editorial independence | Pay-to-post or unknown | Mixed editorial/commercial | Clear editorial standards or public accountability |
| Topical relevance | Generic or off-topic | Category-adjacent | Directly relevant to the target topic |
| Entity clarity | Brand/entity unclear | Some entity signals | Names, addresses, authors, schema, and canonical links are clear |
| Evidence quality | Unsourced claims | Some sources or examples | Primary data, citations, methodology, or named experience |
| Freshness | Stale or undated | Updated occasionally | Current date signals and maintained content |
| Reputation | Spam, thin, or risky | Neutral | Recognized by audience or cited by other quality sources |
| Disclosure safety | Requires hidden promotion | Disclosure possible but awkward | Transparent relationship is natural |

Recommended source classes:

- 13-16: Strong source. Consider outreach, data contribution, or profile correction.
- 9-12: Useful with caveats. Improve evidence or fit before investing heavily.
- 0-8: Low priority or risk. Do not use as a citation target unless there is a specific corrective reason.

## Part 7: Engine-Aware Interpretation

AI systems do not use sources the same way.

- Google AI Overviews and AI Mode are tied to Google Search crawl, indexing, ranking, and snippet eligibility. Do not treat `llms.txt` as a Google ranking requirement.
- ChatGPT Search uses OpenAI's search crawler for search inclusion and can also fetch pages for user-initiated actions.
- Claude distinguishes model-development crawling, user-directed retrieval, and search indexing.
- Perplexity distinguishes its search bot from user-requested fetches and publishes IP ranges for verification.
- Bing/Copilot visibility depends heavily on Bing crawl and index access, plus Bing-supported preview controls.

For crawler policy, use `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md`.

## Part 8: Reporting Template

Use concise, evidence-labeled reporting.

```markdown
## AI Citation Snapshot

Date range:
Engines tested:
Prompt set:
Location/account assumptions:

### Findings
- [Observed] Brand appeared in X/Y tested prompts on Perplexity.
- [Observed] Competitor A was cited by URL 1 and URL 2 for "query theme."
- [Vendor-reported] Tracker shows visibility share changed from X to Y.
- [Inference] Competitor A's original benchmark page appears to be a stronger source because it is cited across three engines and has current methodology.

### Source Gaps
- Missing current comparison page
- Incomplete local profile
- No original data asset for topic
- Community discussions contain unanswered factual questions

### Recommended Work
- Publish/update canonical source asset
- Correct profile/listing data
- Pitch data to relevant editorial source with disclosure
- Answer community questions transparently where appropriate

### Data Gaps
- No server-log access
- No Bing Webmaster Tools access
- No repeat runs from target geography
```

## Implementation Checklist

- [ ] Define the prompt set and target engines.
- [ ] Run baseline tracking with dates, locations, and account assumptions.
- [ ] Export or record cited URLs.
- [ ] Score cited sources with the source-quality rubric.
- [ ] Separate owned-content fixes from earned-source opportunities.
- [ ] Check crawler access and WAF behavior for relevant engines.
- [ ] Publish or improve canonical source assets.
- [ ] Conduct transparent outreach with disclosure records.
- [ ] Participate in communities only where affiliation-safe.
- [ ] Re-run tracking and report variance, not certainty.

## Primary Sources To Check

- OpenAI crawler documentation: https://developers.openai.com/api/docs/bots
- Google Search generative AI optimization guide: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google crawler documentation: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- Anthropic crawler documentation: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity crawler documentation: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Bing data-nosnippet and AI-powered experiences: https://blogs.bing.com/webmaster/October-2025/Bing-Introduces-Support-for-the-data-nosnippet-HTML-Attribute
- llms.txt proposal: https://llmstxt.org/

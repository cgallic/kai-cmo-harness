# Competitor Content Analysis Framework

> **Use when**: Analyzing a competitor's content strategy, identifying content gaps, benchmarking content quality, reverse-engineering what's working for competitors, planning content to outperform competition.

---

## Overview

Competitor content analysis answers three questions:
1. **What are they publishing?** (Topics, formats, cadence)
2. **What's working for them?** (Traffic, engagement, backlinks, rankings)
3. **Where are the gaps?** (Topics they're missing, quality shortfalls, angles they're not covering)

This framework provides a systematic process for each.

---

## Step 1: Topic Cluster Mapping

Map the competitor's content into topic clusters to understand their strategic priorities.

### Process

1. **Export their sitemap** — Use Screaming Frog, Ahrefs Site Audit, or simply `/sitemap.xml` to get all published URLs.

2. **Categorize URLs into clusters** — Group by topic theme, not by URL structure. A competitor might have scattered content across `/blog/`, `/resources/`, `/guides/`, `/learn/` that all belong to the same topic cluster.

3. **Count pieces per cluster** — Reveals strategic weighting. If they have 40 articles about "CRM" and 3 about "email marketing," CRM is their priority.

4. **Identify hub pages** — Which clusters have a pillar/hub page linking to supporting content? Hubs signal intentional SEO strategy vs random publishing.

### Topic cluster template

| Cluster | # of Pieces | Hub Page Exists? | Estimated Monthly Traffic | Strategic Priority |
|---------|------------|-----------------|--------------------------|-------------------|
| [Topic A] | 45 | Yes — /guide/topic-a | 25,000 | Primary |
| [Topic B] | 22 | Yes — /resources/topic-b | 12,000 | Secondary |
| [Topic C] | 8 | No | 3,000 | Emerging |
| [Topic D] | 3 | No | 500 | Experimental |

---

## Step 2: Publishing Cadence Analysis

Understanding how often and when competitors publish reveals their content investment level and operational capacity.

### What to measure

| Metric | How to Measure | What It Tells You |
|--------|---------------|-------------------|
| **Posts per week** | Count blog posts from last 90 days / 13 | Content team size and investment |
| **Cadence consistency** | Standard deviation of weekly publish count | Process maturity (consistent = mature) |
| **Publishing days** | Which days of the week do new posts appear? | When their audience is most active |
| **Content type mix** | % blog posts vs guides vs case studies vs videos | Format strategy |
| **Update frequency** | How often are old posts updated? (Check Wayback Machine) | Content maintenance investment |

### Cadence benchmarks

| Cadence | What It Signals |
|---------|----------------|
| 1-2 posts/week | Lean content team (1-2 people), focused strategy |
| 3-5 posts/week | Dedicated content team, likely 3-5 people + freelancers |
| 5-10 posts/week | Content as primary growth channel, significant investment |
| 10+ posts/week | Programmatic or AI-assisted content at scale |
| Irregular bursts | Campaign-driven content, not always-on |

---

## Step 3: Backlink Profile Audit

A competitor's backlink profile reveals which content earns links (and therefore what types of content you should create).

### Process

1. **Pull top pages by referring domains** — Use Ahrefs or SEMrush to find which competitor pages have the most backlinks.

2. **Categorize link-earning content types**:
   - **Original research/data** — Surveys, reports, benchmarks
   - **Tools/calculators** — Free tools that earn links naturally
   - **Comprehensive guides** — "Ultimate guide to X" style content
   - **Visual assets** — Infographics, charts, maps
   - **Expert roundups** — Multi-source quotes
   - **Controversial takes** — Opinion pieces that generate debate and citation

3. **Analyze link sources** — Where are the links coming from?
   - Industry blogs → Content is recognized as authoritative
   - News outlets → PR-driven link building
   - Edu/gov sites → High-authority link building campaigns
   - Directories/resource pages → Outreach-driven
   - Social profiles → Low value, ignore

4. **Identify linkable asset gaps** — What types of link-earning content do they have that you don't?

### Backlink profile template

| Top Linked Page | Referring Domains | Content Type | Link Sources | Replicable? |
|----------------|-------------------|-------------|-------------|-------------|
| /state-of-x-report | 340 | Original research | Industry blogs, news | Yes — create own survey |
| /free-x-calculator | 210 | Free tool | Resource pages, blogs | Yes — build equivalent |
| /ultimate-guide-to-y | 180 | Comprehensive guide | Blogs, edu | Yes — write better version |
| /infographic-z | 95 | Visual asset | Blogs, social | Yes — create updated version |

---

## Step 4: Social Amplification Patterns

Analyze how competitors distribute content on social channels and what generates engagement.

### Metrics to track per platform

| Platform | Metrics | Tool |
|----------|---------|------|
| **LinkedIn** | Post frequency, engagement rate, follower growth, top posts by engagement | Manual + LinkedIn analytics |
| **X/Twitter** | Tweet frequency, retweets, replies, thread performance | Manual + Twitter analytics |
| **Instagram** | Post frequency, likes, comments, saves, Reel views | Manual + IG analytics |
| **YouTube** | Video frequency, views, subscriber growth, watch time | YouTube Studio / Social Blade |
| **TikTok** | Post frequency, views, shares, comments | Manual + TikTok analytics |

### Social amplification analysis

For each competitor, answer:

1. **Which platforms are they most active on?** — Reveals where they believe their audience lives.
2. **What content gets the most engagement?** — Reveals what resonates with the shared audience.
3. **How do they repurpose blog content for social?** — Pull-quotes, carousels, video summaries, threads?
4. **Do they have employee advocacy?** — Are multiple employees sharing company content?
5. **What's their paid amplification level?** — Are they boosting posts or running content promotion ads?

---

## Step 5: Content Quality Scoring

Score competitor content objectively so you know where to invest to beat them.

### Quality scoring rubric (score each 1-5)

| Dimension | 1 (Poor) | 3 (Average) | 5 (Excellent) |
|-----------|----------|-------------|----------------|
| **Depth** | Surface-level overview | Covers main points | Comprehensive, nothing left to ask |
| **Originality** | Rehashed commodity content | Some unique angles | Original data, frameworks, or insights |
| **Actionability** | Theory only | Some practical tips | Step-by-step instructions with examples |
| **Recency** | Outdated data/references | Mostly current | Up-to-date with latest data and trends |
| **Design/UX** | Wall of text | Basic formatting | Visual, scannable, interactive elements |
| **E-E-A-T signals** | No author, no credentials | Author bio present | Expert author, original experience, cited sources |

### Scoring template

| Content Piece | Depth | Originality | Actionability | Recency | Design | E-E-A-T | Total (/30) |
|--------------|-------|-------------|---------------|---------|--------|---------|-------------|
| [URL 1] | 4 | 3 | 4 | 5 | 3 | 4 | 23 |
| [URL 2] | 3 | 2 | 2 | 3 | 4 | 3 | 17 |

**Rule of thumb**: If a competitor's content scores below 20/30, you can beat it with a focused effort. Above 25/30, you need truly differentiated content (original data, unique expertise) to outrank.

---

## Step 6: Keyword Overlap Analysis

Identify where you and competitors are competing for the same search traffic.

### Process

1. **Export your organic keywords** — Top 1,000 by traffic from SEMrush or Ahrefs.
2. **Export competitor's organic keywords** — Same source, same count.
3. **Find the overlap** — Keywords you both rank for. SEMrush's "Keyword Gap" tool automates this.
4. **Categorize the overlap**:

| Category | Definition | Action |
|----------|-----------|--------|
| **You win** | You rank higher for the keyword | Maintain — don't get complacent |
| **They win** | They rank higher | Analyze their content — what's better? Improve yours. |
| **Close competition** | Within 3 positions | High-impact optimization target |
| **They rank, you don't** | They have content, you don't | Content gap — create content |
| **You rank, they don't** | You have content, they don't | Competitive advantage — protect and strengthen |

---

## Step 7: Content Gap Identification

The synthesis of all previous steps. Content gaps are opportunities where you can create content that competitors either don't have or do poorly.

### Three types of content gaps

| Gap Type | Description | Priority | Action |
|----------|-----------|----------|--------|
| **Topic gap** | Competitor covers a topic you don't | High if search volume exists | Create content |
| **Quality gap** | Both cover the topic, but their content is better | High if keyword has traffic | Improve existing content |
| **Format gap** | Topic is covered by both in text, but video/interactive/tool version is missing | Medium | Create differentiated format |
| **Depth gap** | Both cover the topic at surface level | Medium | Go deeper than anyone |
| **Freshness gap** | Competitor's content is outdated | Medium-high | Create updated version |
| **Angle gap** | Topic covered but from a different perspective/audience | Medium | Create content for your angle |

### Gap prioritization matrix

Score each gap on two dimensions:

```
               HIGH OPPORTUNITY
                     |
         Quick Win   |  Strategic Win
    (low effort,     |  (high effort,
     high return)    |   high return)
                     |
LOW EFFORT ----------+---------- HIGH EFFORT
                     |
         Ignore      |  Long-term Play
    (low effort,     |  (high effort,
     low return)     |   low return)
                     |
               LOW OPPORTUNITY
```

---

## Step 8: Share of Voice Measurement

Share of Voice (SOV) measures how visible your brand is relative to competitors across channels.

### SOV by channel

| Channel | Metric | Calculation |
|---------|--------|------------|
| **Organic search** | % of total impressions for target keywords | Your impressions / total impressions for keyword set |
| **Social media** | % of total mentions | Your mentions / (your + competitors' mentions) |
| **Paid search** | Impression share | Google Ads impression share metric |
| **Content** | % of indexed pages in topic cluster | Your pages indexed / total pages indexed for cluster |
| **PR/Media** | % of media mentions | Your press mentions / total industry press mentions |

### SOV tracking template

| Keyword Cluster | Your SOV | Comp A SOV | Comp B SOV | Trend (3mo) |
|----------------|----------|-----------|-----------|-------------|
| [Cluster 1] | 25% | 35% | 20% | You: up 5% |
| [Cluster 2] | 40% | 15% | 30% | Stable |
| [Cluster 3] | 10% | 45% | 25% | You: down 3% |

---

## Step 9: Content Format Distribution

Analyze what content formats competitors use and where there are format opportunities.

### Format distribution template

| Format | Competitor A | Competitor B | You | Industry Avg |
|--------|-------------|-------------|-----|-------------|
| Blog posts | 60% | 45% | 70% | 55% |
| Video | 15% | 25% | 5% | 20% |
| Podcasts | 5% | 10% | 0% | 8% |
| Webinars | 10% | 5% | 10% | 7% |
| Case studies | 5% | 10% | 10% | 5% |
| Interactive tools | 0% | 5% | 0% | 3% |
| Original research | 5% | 0% | 5% | 2% |

**Insight extraction**: If competitors are under-invested in video but the industry average is growing, that's a format gap worth exploiting.

---

## Step 10: Author Authority Assessment

E-E-A-T makes author credibility a ranking factor. Assess competitor author strategies.

### Author analysis framework

| Question | What to Look For |
|----------|-----------------|
| Do they use named authors? | Named > Anonymous (E-E-A-T signal) |
| Do authors have credentials? | Bio with title, experience, certifications |
| Do authors have external presence? | LinkedIn profiles, speaking engagements, publications |
| Is it one author or many? | One → single expert brand. Many → diverse expertise. |
| Are authors real employees? | vs freelancers with generic bios |
| Do authors cross-link their work? | Author pages with full article history |
| Are author pages Schema marked up? | `Person` schema with `sameAs` links |

### Author authority scoring

| Signal | Score |
|--------|-------|
| Named author with photo | +1 |
| Author bio with credentials | +1 |
| Author has dedicated page on site | +1 |
| Author has external presence (LinkedIn, publications) | +1 |
| Author has Schema markup | +1 |
| Author demonstrates first-hand experience in content | +2 |
| **Total possible** | **7** |

Competitors scoring 5+ on author authority are investing in E-E-A-T. If your authors score below 3, that's a vulnerability.

---

## Analysis Output Template

```markdown
# Competitor Content Analysis: [Competitor Name]

**Date**: [Date]
**Analyzed by**: [Name]

## Executive Summary
[2-3 sentences: What is their content strategy? Where are they strong? Where are the gaps?]

## Topic Cluster Map
[Table from Step 1]

## Publishing Cadence
- Posts per week: [X]
- Primary publishing days: [Days]
- Content type mix: [Breakdown]

## Top Performing Content (by traffic)
1. [URL] — [Est. monthly traffic] — [Topic]
2. [URL] — [Est. monthly traffic] — [Topic]
3. [URL] — [Est. monthly traffic] — [Topic]

## Top Link-Earning Content
1. [URL] — [Referring domains] — [Content type]
2. [URL] — [Referring domains] — [Content type]

## Content Quality Assessment
- Average quality score: [X/30]
- Strongest dimension: [Dimension]
- Weakest dimension: [Dimension]

## Keyword Overlap Summary
- Keywords both rank for: [X]
- They win: [X keywords]
- We win: [X keywords]
- Top opportunity keywords: [List]

## Content Gaps We Can Exploit
1. [Gap] — [Priority] — [Action]
2. [Gap] — [Priority] — [Action]
3. [Gap] — [Priority] — [Action]

## Recommended Actions
1. [Action with timeline]
2. [Action with timeline]
3. [Action with timeline]
```

---

## Tactical Checklist

```
[ ] Competitor sitemap exported and URLs categorized into topic clusters
[ ] Publishing cadence measured (posts/week, consistency, days)
[ ] Top 20 pages by traffic identified
[ ] Top 20 pages by backlinks identified
[ ] Social amplification patterns analyzed per platform
[ ] Content quality scored for top 10 pieces (depth, originality, actionability, recency, design, E-E-A-T)
[ ] Keyword overlap analysis completed
[ ] Content gaps identified and prioritized
[ ] Share of voice measured for core keyword clusters
[ ] Content format distribution compared
[ ] Author authority assessed
[ ] Analysis output document completed
[ ] Action items assigned with timelines
```

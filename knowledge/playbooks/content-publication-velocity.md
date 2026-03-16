# Content Publication & Velocity Playbook

A comprehensive guide to content brief methodology, publication timing, segment completion strategy, and indexation acceleration based on Koray Tugberk Gubur's consulting methodology.

---

## Strategic Overview

Content velocity is not just about publishing more content faster - it's about strategic publication that triggers Google's evaluation systems at the right times.

Key principles:
1. **Complete segments** before expecting rankings
2. **Monitor crawl behavior** to gauge Google's interest
3. **Use social signals** to accelerate crawl frequency
4. **Cross-link strategically** to distribute PageRank

> "Links are not only for page rank, it is also about passing relevance, it is also about increasing your crawl priority and crawl frequency."

---

## 1. Content Brief Methodology

### Brief Components

Based on Koray's template structure, every content brief should include:

```
CONTENT BRIEF TEMPLATE
├── Document Metadata
│   ├── Target URL
│   ├── Target Keywords
│   ├── Page Type (Commercial/Informational)
│   └── Priority Level
│
├── Structural Elements
│   ├── H1 (exact)
│   ├── H2 Headings (with required topics)
│   ├── H3 Sub-headings (optional depth)
│   └── Component Column (visual elements)
│
├── Internal Linking
│   ├── Required Links (with anchor text)
│   ├── Suggested Links
│   └── Link Priority (commercial first)
│
├── Content Requirements
│   ├── Word Count Range
│   ├── Required Entities to Cover
│   ├── Statistics/Data to Include
│   └── Expert Quotes Needed
│
└── Design Components
    ├── Tables Required
    ├── Lists (numbered/bulleted)
    ├── CTAs (placement)
    └── Visual Elements
```

### The Component Column

> "I start to add this component column to the content briefs."

A component column maps each section to a specific visual/design element:

| Section | Component | Description |
|---------|-----------|-------------|
| Laws Overview | Vertical Tab Headings | Tabbed navigation for law types |
| Statistics | Data Table | Structured comparison table |
| Process Steps | Numbered List with Icons | Visual step process |
| FAQ | Accordion | Expandable Q&A format |
| CTA | Floating Button | Sticky call-to-action |

Reference: Create a component dictionary with definitions, code examples, and visual mockups.

### Linking Instructions in Briefs

> "In some headings, I will need two different anchor tags for two different sections. Placing these anchor tags requires some relevance engineering by the author."

**Link Placement Rules:**

1. **Commercial links first, informational second:**
   - First mention → Link to service page
   - Later paragraph → Link to glossary/educational page

2. **Not in same sentence:**
   - "Learn about [negligence](#) in car accident cases." (OK)
   - "Our [car accident attorneys](#) can explain [negligence](#)." (Too close)

3. **Contextual relevance required:**
   - Only link when the term naturally appears
   - Don't force anchor text

### PDF Content Briefs

> "When I create a PDF brief, most of the time it is about expertise."

PDF documents require special handling:

```
PDF BRIEF STRUCTURE
├── Heading Levels (use font size hierarchy)
├── Internal Links (clickable within PDF)
├── Response Headers (for canonicalization)
├── Expert/Attorney Attribution
└── Downloadable Resources (forms, templates)
```

**Example: Settlement Agreement PDF**
- Must be created by attorney (expertise requirement)
- Include sample agreement with proper legal language
- Add internal links to related web pages
- Use proper heading hierarchy

---

## 2. Publication Velocity Checks

### The 7/14/28 Day Framework

Monitor content performance at three checkpoints after publication:

**Day 7 Check:**
- Has Google crawled the page?
- Is it appearing in Search Console?
- Any initial impressions?

**Day 14 Check:**
- Has the page been indexed?
- What queries is it appearing for?
- Initial ranking position?

**Day 28 Check:**
- Stable ranking achieved?
- Impressions/clicks trend?
- Need for content adjustment?

### Crawl Delay Monitoring

> "There is a kind of crawl delay time that I call because usually your sitemap is always submitted to the Google the moment that sitemap has been changed. And if Google is not trying to hurry to crawl your latest URL, it means they don't care about it that much."

**How to Calculate Crawl Delay:**

```python
# Conceptual formula
crawl_delay = first_crawl_date - publication_date

# Healthy: < 24 hours
# Concerning: 3-7 days
# Problematic: > 7 days
```

**Data Sources:**
1. Sitemap last modification date
2. Server log files (Googlebot visits)
3. Search Console coverage report

**What Crawl Delay Tells You:**

| Delay | Meaning | Action |
|-------|---------|--------|
| < 24 hours | Google cares about this content | Continue current strategy |
| 1-3 days | Normal for new pages | Monitor, no action needed |
| 3-7 days | Lower priority site | Increase social signals |
| > 7 days | Google not interested | Major intervention needed |

---

## 3. Segment Completion Strategy

### Complete the Segment Before Expecting Results

> "If the document doesn't penetrate to the SERP, basically complete its segment fully."

**Definition:** A segment is a complete topical cluster with all supporting pages interlinked.

**Example Segment: Car Accident Recovery**

```
SEGMENT: Car Accident Recovery
├── Main Page: Car Accident Recovery Process
├── Supporting: What to Do After an Accident
├── Supporting: Car Accident Claim Timeline
├── Supporting: Common Car Accident Injuries
├── Statistics: Car Accident Statistics [City]
└── Glossary: Key Terms in Car Accident Cases

[All pages interlinked before expecting rankings]
```

### The Incomplete Segment Problem

If you publish 3 of 6 pages in a segment:
- Internal links point to non-existent pages
- Topical authority appears incomplete
- Rankings won't materialize

**Solution:** Batch publish entire segments, then move to next segment.

### Segment Publication Order

1. **Core commercial pages first** (money pages)
2. **Direct supporting pages** (same intent)
3. **Educational/glossary pages** (expertise signals)
4. **Statistics/trending pages** (freshness signals)

---

## 4. URL Inspection Tool Usage

> "In these cases, it is better to actually sometimes use either URL inspection tool by saying that actually just basically crawl and index this, it might be increasing Google's actual evaluation speed for that URL."

### When to Use URL Inspection

1. **New page not crawled after 48 hours**
2. **Updated page not showing changes**
3. **After adding new internal links to page**
4. **After significant content additions**

### URL Inspection Protocol

**Step 1: Check Current Status**
- Open Search Console
- Enter URL in inspection tool
- Note: Indexed? Last crawl date?

**Step 2: Review Rendered Page**
- Click "View Tested Page"
- Check for rendering issues
- Verify content is visible

**Step 3: Request Indexing**
- Click "Request Indexing"
- Wait for confirmation
- Document request date

**Step 4: Monitor**
- Check back in 24-48 hours
- Verify indexation status
- Note any ranking changes

### Batch Processing After Segment Completion

> "If the document doesn't penetrate to the SERP, basically complete its segment fully. Another thing is that link it from the homepage. Link it from the boilerplate content or other informational segments by doing relevance configuration. Another part is that use URL inspection tool."

After completing a segment:
1. Add links from homepage (topical entry grid)
2. Cross-link all pages in segment
3. Request indexing for main segment pages
4. Monitor crawl/index status

---

## 5. Cross-Client External Linking

### Author Section Cross-Linking Strategy

> "The reason, actually, I'm using these author sections is that it is safer to use. Because the links are not for commercial terms, it can save everybody, it can keep everybody actually safe for the same purpose."

**How It Works:**

```
CLIENT A (Houston)                    CLIENT B (Los Angeles)
Author Section:                       Author Section:
"What is Negligence"                  "Understanding Liability"
    ↓                                     ↓
    Links to →→→→→→→→→→→→→→→→→→→→→→→→→→→ "Understanding Liability"

    ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← Links to
                                      "What is Negligence"
```

**Safety Rules:**

1. **Only informational content:**
   - Never link from commercial pages
   - Only author section to author section

2. **Time delay:**
   > "This can link right now, and this can here link actually two weeks later."
   - Don't reciprocate immediately
   - Space links 1-2 weeks apart

3. **Natural anchor text:**
   - Use topic descriptions, not keywords
   - "Learn more about negligence in personal injury law"
   - NOT "Houston personal injury lawyer"

4. **Non-competing regions:**
   - Houston client ↔ Los Angeles client = Safe
   - Houston client ↔ Houston competitor = Dangerous

### Implementation Protocol

**Week 1:**
- Client A publishes "What is Negligence"
- Includes link to Client B's "Understanding Liability"

**Week 3:**
- Client B publishes "Expert Witness Guide"
- Includes link back to Client A's "What is Negligence"

**Ongoing:**
- Continue cross-linking author section content
- Never link to commercial/service pages
- Maintain 2-week minimum gap between reciprocal links

---

## 6. Social Media Link Distribution for Crawl Frequency

> "After adding your site, lots of different type of social media links or lots of different type of buzz, if you see that crawl delay is decreased and daily crawl frequency is increased, it will be something positive."

### Purpose: Exploration, Not PageRank

> "Social media should add more links to the post. This is, I'm writing here, not for page rank, for exploration and higher frequency of crawl for that specific URL."

Social links serve to:
1. Signal content importance to Google
2. Increase crawl frequency
3. Generate initial engagement signals
4. Trigger faster indexation

### Social Distribution Protocol

**For New Content:**

**Hour 0:** Publish content
**Hour 1:** Share on brand Twitter/X
**Hour 2:** Post to LinkedIn (personal)
**Hour 4:** Share on Facebook page
**Hour 8:** Post to relevant subreddits (if appropriate)
**Day 2:** Share on Medium (with canonical)
**Day 3:** LinkedIn article (summary + link)

**Platform Priority:**

| Platform | Impact on Crawl | Notes |
|----------|-----------------|-------|
| Twitter/X | High | Fast indexation signal |
| LinkedIn | High | Professional topics |
| Facebook | Medium | Broad reach |
| Reddit | High | If community appropriate |
| Medium | Low | More for entity building |

### Indexation Acceleration Stack

For critical pages that need fast indexation:

1. **Publish to sitemap** (automatic)
2. **Social distribution** (within 1 hour)
3. **URL Inspection request** (after 4 hours)
4. **Add homepage link** (Topical Entry Grid)
5. **Cross-link from existing indexed pages**

> "Even if these links wouldn't pass any page rank, they would make you to be crawled more directly as well."

---

## 7. Content Evaluation Triggers

### First Paragraph Optimization

> "The rest here, rest is only about changing, let's say, its content slightly by starting from the Page 1 or Context Paragraph. That section can actually trigger a better evaluation for them."

**When Page Isn't Ranking:**

1. Review first paragraph (first 100 words)
2. Check: Does it directly address the query?
3. Rewrite to be more direct/relevant
4. Request re-indexing via URL Inspection
5. Monitor for ranking changes

### Content Change Triggers

Make strategic updates to trigger re-evaluation:

| Trigger | When to Use |
|---------|-------------|
| First paragraph rewrite | Page indexed but not ranking |
| Add new internal links | After new related content published |
| Add statistics/data | Page lacks freshness signals |
| Add expert quote | Page lacks E-E-A-T signals |
| Update date | Evergreen content > 6 months old |

---

## Step-by-Step Implementation

### Phase 1: Brief System Setup (Week 1)

1. **Create brief template:**
   - Include all component columns
   - Define linking requirements
   - Establish quality checklist

2. **Build component dictionary:**
   - Define each UI component
   - Create code samples
   - Add mockup images

3. **Set up monitoring:**
   - Search Console access
   - Log file analysis
   - Crawl tracking spreadsheet

### Phase 2: Publication Protocol (Ongoing)

**Per Content Piece:**

1. Brief creation (using template)
2. Content production
3. Internal review
4. Technical implementation
5. Publish to sitemap
6. Social distribution
7. 7-day check
8. URL Inspection (if needed)
9. 14-day check
10. 28-day evaluation

**Per Segment:**

1. Identify all pages in segment
2. Create briefs for all pages
3. Produce all content
4. Publish all pages within 1-2 weeks
5. Cross-link entire segment
6. Add homepage links
7. Social distribute main pages
8. URL Inspection for main pages
9. 28-day segment evaluation

### Phase 3: Cross-Client Linking (Monthly)

1. Identify author section opportunities
2. Match non-competing clients
3. Create linking schedule (2-week gaps)
4. Implement first wave of links
5. Wait 2 weeks
6. Implement reciprocal links
7. Monitor for any issues

---

## Tools Mentioned

| Tool | Purpose |
|------|---------|
| Google Search Console | URL Inspection, Coverage, Performance |
| Server Log Analyzer | Crawl frequency monitoring |
| Screaming Frog | Internal link audit |
| Ahrefs/SEMrush | Keyword tracking, competitor analysis |
| Social Scheduling Tool | Automated social distribution |
| Spreadsheet/Airtable | Crawl tracking, publication schedule |

---

## Common Mistakes to Avoid

1. **Publishing incomplete segments:**
   - Finish all pages before expecting results
   - Interlink before social promotion

2. **Ignoring crawl delay signals:**
   - Long delays = Google doesn't care
   - Address with social signals and links

3. **Over-using URL Inspection:**
   - Don't request daily
   - Use strategically after changes

4. **Reciprocal linking too fast:**
   - Wait 2 weeks between reciprocal links
   - Only use for author section content

5. **Neglecting social distribution:**
   - Not just for traffic
   - Directly impacts crawl frequency

6. **Not updating first paragraphs:**
   - Often the fix for non-ranking pages
   - Most important 100 words

---

## Quick Reference Checklist

### Content Brief

- [ ] Target URL defined
- [ ] H1/H2/H3 structure mapped
- [ ] Component column included
- [ ] Internal links specified with anchor text
- [ ] Link priority defined (commercial first)
- [ ] Word count range set
- [ ] Required entities listed

### Publication

- [ ] Segment complete (all pages published)
- [ ] All internal links active
- [ ] Sitemap updated
- [ ] Social distribution completed
- [ ] 7-day check scheduled
- [ ] 14-day check scheduled
- [ ] 28-day evaluation scheduled

### Monitoring

- [ ] Search Console access verified
- [ ] Crawl delay being tracked
- [ ] Indexation status documented
- [ ] URL Inspection used if needed (after 48 hours)

### Cross-Client Linking

- [ ] Only author section content
- [ ] Non-competing regions
- [ ] 2-week gap between reciprocal links
- [ ] Natural anchor text
- [ ] No commercial pages involved

---

## Key Quotes Summary

> "Links are not only for page rank, it is also about passing relevance, it is also about increasing your crawl priority and crawl frequency."

> "If the document doesn't penetrate to the SERP, basically complete its segment fully."

> "Use URL inspection tool because it makes search engine to regulate that page with these newly added links."

> "Social media should add more links to the post - not for page rank, for exploration and higher frequency of crawl."

> "This can link right now, and this can here link actually two weeks later. Since the links are not for commercial terms, it can save everybody safe."

---

*Source: Koray Tugberk Gubur SEO Consulting Transcripts*

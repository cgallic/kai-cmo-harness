# SEO Internal Linking Strategy Playbook

> **Use when:** Building or optimizing internal linking architecture for SEO. Internal links distribute PageRank, establish topical authority, and guide both users and search engines through your site.

---

## Why Internal Linking Matters

- **PageRank distribution:** Internal links pass authority from strong pages to weak ones
- **Crawl efficiency:** Helps Googlebot discover and index all pages
- **Topical authority:** Connecting related content signals expertise to search engines
- **User experience:** Guides visitors to relevant content, increasing time on site
- **Indexation control:** Pages with more internal links get crawled and indexed faster

**The math:** A page with 0 internal links pointing to it is invisible to search engines and users. A page with 10 contextual internal links from related content has 10x the visibility signal.

---

## Internal Linking Architecture

### The Hub-and-Spoke Model

```
                    ┌──────────┐
                    │ PILLAR   │  (Hub: comprehensive topic page)
                    │ PAGE     │
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
     ┌─────▼─────┐ ┌────▼──────┐ ┌───▼───────┐
     │ CLUSTER   │ │ CLUSTER   │ │ CLUSTER   │  (Spokes: subtopic articles)
     │ POST 1    │ │ POST 2    │ │ POST 3    │
     └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
           │             │             │
           └─────────────┼─────────────┘
                         │
                    (cross-links between cluster posts)
```

**Pillar page:** Broad, comprehensive (2000-5000 words). Targets the main keyword.
**Cluster posts:** Specific subtopics (1000-2000 words each). Target long-tail keywords.
**Links:** Every cluster links to the pillar. Pillar links to every cluster. Clusters cross-link to related clusters.

### Example: "AI Receptionist" Topic Cluster

```
PILLAR: "The Complete Guide to AI Receptionists for Law Firms"
  │
  ├── CLUSTER: "AI Receptionist vs Answering Service: Cost Comparison"
  ├── CLUSTER: "How AI Receptionists Handle After-Hours Calls"
  ├── CLUSTER: "Setting Up an AI Receptionist for Your Law Firm"
  ├── CLUSTER: "AI Receptionist Integration with Clio and MyCase"
  ├── CLUSTER: "AI Receptionist FAQ: Privacy, Security, and Compliance"
  └── CLUSTER: "Case Study: How Acme Law Saved $4K/Month with AI"
```

Each cluster links:
- Back to the pillar (mandatory)
- To 2-3 other related clusters (natural cross-linking)
- To 1-2 other pillar pages on related topics (if they exist)

---

## Linking Rules

### Anchor Text Best Practices

| Rule | Example | Why |
|------|---------|-----|
| **Descriptive, keyword-rich** | "AI receptionist for law firms" | Tells Google what the target page is about |
| **Natural in context** | "Learn how to set up an AI receptionist" | Doesn't feel forced to the reader |
| **Varied anchors** | Don't use the exact same anchor every time | Avoid over-optimization penalty |
| **Not generic** | NOT "click here" or "read more" | Wastes the anchor text signal |
| **Not the URL** | NOT "https://example.com/page" | Ugly and uninformative |

### Link Placement Priority

```
HIGHEST VALUE:
  Body content (within paragraphs, contextually relevant)
  → This is where Google assigns the most link value

MEDIUM VALUE:
  Content callout boxes ("Related: [link]")
  Table of contents links
  In-content recommendations

LOWER VALUE (but still useful):
  Sidebar "related posts"
  Footer links
  Navigation menus
  Breadcrumbs
```

**Rule:** Prioritize contextual body links over sidebar/footer links. A link within a relevant paragraph carries more weight than a link in a "Related Posts" widget.

### How Many Internal Links Per Page?

| Page Type | Internal Links (outbound) | Why |
|-----------|--------------------------|-----|
| Blog post (1500 words) | 5-10 | Enough to distribute value without over-linking |
| Pillar page (3000+ words) | 15-30 | Hub page should link to all cluster content |
| Product/service page | 3-5 | Focus on conversion, not navigation overload |
| Homepage | 10-20 | Main navigation + featured content |

**Rule of thumb:** One internal link per 200-300 words of body content. More than that and you dilute link equity.

---

## Internal Linking Audit

### Step 1: Map Current Links

```bash
# Use Screaming Frog, Ahrefs, or Sitebulb to crawl your site
# Export: URL, inlinks count, outlinks count, link depth
```

### Step 2: Find Orphan Pages

Pages with 0 internal links pointing to them = orphan pages. They're invisible.

**Fix:** Add contextual links from related content to every orphan page.

### Step 3: Find Link-Rich Pages

Pages with the most external backlinks = your most authoritative pages. Use them as "link launchers" — add internal links FROM these pages TO pages you want to rank.

```
LINK EQUITY FLOW:
  High-authority page (lots of backlinks)
    → Internal link to target page
    → Target page gains authority
    → Target page ranks higher
```

### Step 4: Check Link Depth

Link depth = number of clicks from homepage to a page.

| Depth | Status | Action |
|-------|--------|--------|
| 1 click | Excellent | Homepage links directly |
| 2 clicks | Good | Accessible from main sections |
| 3 clicks | Acceptable | Most content should be here or higher |
| 4+ clicks | Too deep | Googlebot may not crawl regularly — add links to reduce depth |

### Step 5: Fix Broken Internal Links

Any internal link pointing to a 404 or redirect wastes link equity.

```bash
# Screaming Frog: Reports → Links → Broken Links
# Fix: Update href to correct URL, or set up 301 redirect
```

---

## Tactical Playbook

### New Content Published

Every time you publish a new piece:
1. **Link FROM the new piece** to 3-5 existing relevant pages
2. **Link TO the new piece** from 3-5 existing relevant pages (go back and add links)
3. **Update the pillar page** to include a link to the new cluster post

Step 2 is the one most people skip. It's the most impactful.

### Monthly Internal Link Audit (30 min)

- [ ] Check top 10 target pages: do they have 5+ internal links pointing to them?
- [ ] Check last 10 published posts: do they link to pillar pages?
- [ ] Check for orphan pages (0 internal links)
- [ ] Check for broken internal links
- [ ] Check link depth: any important pages buried 4+ clicks deep?
- [ ] Review anchor text: varied and descriptive?

### Quarterly Architecture Review (2 hours)

- [ ] Map all topic clusters: do they have complete hub-and-spoke structure?
- [ ] Identify new cluster opportunities (keywords ranking 5-20, no dedicated content)
- [ ] Check cross-linking between related clusters
- [ ] Audit navigation: does the main nav surface your most important pages?
- [ ] Review sitemap: does it match your actual link architecture?

---

## Advanced Tactics

### Strategic Link Placement

**Link from authority → opportunity:**
Find your pages with the most external backlinks (check Ahrefs/Moz). Add internal links from those pages to pages you want to rank better. This "flows" authority to the target pages.

**Link from high-traffic → conversion:**
Find your highest-traffic pages (GA4). Add internal links to your conversion pages (pricing, trial, demo). Turn traffic into pipeline.

**Contextual relevance beats volume:**
One link from a highly relevant page is worth more than 10 links from unrelated pages. Google evaluates the topical relationship between linking and linked pages.

### Breadcrumbs (Structured)

```
Home > Blog > AI Receptionists > How to Set Up AI for Law Firms
```

- Reduces link depth for deep pages
- Provides structured data Google understands
- Improves user navigation
- Implement with BreadcrumbList schema markup

### Nofollow Internal Links (When to Use)

Almost never. Internal nofollow wastes link equity. Only use for:
- Login/signup pages (if you don't want them indexed)
- Internal search results pages
- User-generated content with external links

---

## Tools

| Tool | Use For | Cost |
|------|---------|------|
| **Screaming Frog** | Full site crawl, link audit | Free (500 URLs), £199/yr |
| **Ahrefs** | Backlink analysis, internal link opportunities | $99+/mo |
| **Sitebulb** | Visual link architecture mapping | $13.50+/mo |
| **Google Search Console** | Internal links report (basic) | Free |
| **Link Whisper** (WordPress) | AI-suggested internal links while writing | $77/yr |
| **Yoast SEO** (WordPress) | Orphan content detection, internal link suggestions | Free tier |

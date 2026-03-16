# Koray Content Brief Checklist

A comprehensive checklist for creating SEO-optimized content briefs, extracted from Koray Tugberk Gubur's consulting methodology. Covers anchor text strategy, internal linking, PDF briefs, heading structure, and uniqueness requirements.

---

## Content Brief Structure

### Essential Components
- [ ] **Topic/Subject specification** - Clear definition of what the page covers
- [ ] **H1 and title tag template** - With variable placeholders for location/entity
- [ ] **Heading structure (H2-H4)** - Complete outline with hierarchy
- [ ] **Component specifications** - Which design components to use per section
- [ ] **Internal link suggestions** - Target URLs with anchor text recommendations
- [ ] **External link opportunities** - Cross-site linking possibilities
- [ ] **Color-coding status** - Green (ready), Blue (reviewed), Red (for later)

### Metadata Requirements
- [ ] **Mark topics by priority** - Essential vs "for later" additions
  - *Format*: Add "(for later)" in parentheses for non-essential topics
  - *Color*: Red for future topics, Green for current priorities

- [ ] **Document link field** - Link to final written content for review
  - *Why it matters*: Enables brief-to-content comparison during review

- [ ] **Publication tracking** - Track 7/14/28 day checks post-publication
  - *Check for*: Zero impressions indicates need for segment completion and additional linking

---

## Anchor Text Strategy

### Header Anchor Text (Most Valuable)
- [ ] **Use VMAT (Valuable Exact Match Anchor Text) in header** - Most commercial term first
  - *Example*: "Car Accident Attorney Houston" in header navigation
  - *Why it matters*: Header links carry highest value; use most important terms here

- [ ] **Logo alt tag and title attribute** - Include most valuable anchor text
  - *Format*: "[Location] [Primary Service] Attorney/Lawyer"
  - *Example*: alt="Houston Car Accident Attorney" title="Houston Car Accident Attorney"

- [ ] **Dynamic header based on page context** - Change header links based on current section
  - *Benefit*: Reduces boilerplate links, increases value of main content links
  - *Implementation*: PHP-based (not JavaScript) for crawlability

### Footer Anchor Text (Secondary Value)
- [ ] **Use synonyms in footer** - Less valuable variations of header terms
  - *Example*: If header uses "Attorney," footer uses "Lawyer"
  - *If header*: "Car Accident" | *Footer*: "Auto Accident" or "Vehicle Accident"

- [ ] **Secondary anchor text for logo** - Different from header logo anchor
  - *Example*: Header="Car Accident Attorney" | Footer="Personal Injury Lawyer"

- [ ] **Synonym variations in navigation** - Footer menu mirrors header with synonyms
  - *Purpose*: Captures additional keyword variations without duplication

### Internal Link Placement
- [ ] **Commercial link first, informational second** - Within same section
  - *Order*: Service page link before location-agnostic/informational link
  - *Spacing*: Not in same sentence or paragraph; give commercial link priority

- [ ] **Header menu = commercial intent pages** - Prioritize money pages
  - *Why it matters*: Header gets most link equity; use for highest-value pages

- [ ] **Footer/sidebar = informational pages** - Glossary, resources, etc.
  - *Alternative*: Inner glossary pages can link to location-agnostic content

### Anchor Text Uniqueness
- [ ] **60%+ difference in anchor text between similar pages** - For templated content
  - *Why it matters*: Prevents template detection and duplicate content issues

- [ ] **Change order of heading anchor text** - Vary sequence across similar pages
  - *Example*: Page A: "Car Accident Statistics" | Page B: "Statistics for Auto Accidents"

---

## Heading Structure Rules

### Macro vs Micro Context
- [ ] **Macro context = site-wide relevance** - Consistent across all pages
  - *Content*: Company definition, location, primary services
  - *Placement*: Footer instructional sentence, about sections

- [ ] **Micro context = page-specific relevance** - Changes per page/topic
  - *Content*: Page topic, specific service, local statistics
  - *Placement*: H1, main content sections, dynamic elements

### Heading Hierarchy
- [ ] **H1 contains primary target keyword** - Most valuable exact match phrase
  - *Include*: Location + Service type + Entity type (Attorney/Lawyer)

- [ ] **H2s define major topical sections** - Macro context divisions
  - *Types*: Process/methodology, benefits, statistics, FAQs, types/categories

- [ ] **H3s for subtopics within sections** - Specific details under H2s
  - *Format*: Can include parenthetical expansions for related terms

- [ ] **H4s for granular points** - Boolean questions, definitions, specifics
  - *Use when*: Not opening as separate page; need depth without new URL

### Heading Variation Techniques
- [ ] **Use parenthetical expansions** - Add hyponyms in parentheses
  - *Format*: "Soft Tissue Injuries (Whiplash, Sprains, Strains)"
  - *Structure*: Hypernym first, hyponyms in parentheses

- [ ] **Replace with synonym alternates** - But maintain relevance
  - *Options*: Attorney/Lawyer, Car/Auto/Vehicle, Accident/Crash/Collision
  - *Warning*: Don't change just for difference; ensure relevance maintained

- [ ] **Add span elements for extra text** - Additional context without affecting heading
  - *Use for*: Clarifying text that shouldn't be part of the heading vector
  - *Example*: `<h2>Common Injuries<span class="subtitle">All Accident Types</span></h2>`

---

## PDF Brief Requirements

### When to Create PDF Briefs
- [ ] **Expertise-required content** - Content that must come from professionals
  - *Examples*: Sample legal agreements, professional guides, official forms
  - *Who writes*: Attorney/expert, not content writer

### PDF Structure
- [ ] **Use font size for heading hierarchy** - Simulate H2/H3/H4 structure
  - *Note*: PDFs don't have HTML headings; use consistent sizing

- [ ] **Include internal links** - Link to homepage and related pages
  - *Why it matters*: PDFs pass PageRank; use for link distribution
  - *Placement*: Dedicated links section, separate from main content

- [ ] **Use response headers for canonicalization** - HTTP headers, not HTML
  - *Why it matters*: PDFs can't have HTML canonical tags
  - *Implementation*: Server-side canonical header configuration

- [ ] **Design separators between sections** - Visual breaks for Q&A, links, content
  - *Purpose*: Helps both users and search engines understand content structure

### PDF Linking Strategy
- [ ] **Link to homepage** - Pass PageRank to primary page
- [ ] **Link to fundamentally related service pages** - Relevant practice areas
- [ ] **Use appropriate anchor text** - Same rules as HTML internal linking

---

## Variable Uniqueness Requirements

### For Templated/Location Pages
- [ ] **Minimum 60% difference in answers** - Between similar pages
  - *What to change*: Not just location names; actual content differences

- [ ] **State-specific legal differences** - When states differ, reflect in content
  - *Impact*: Different laws = different low sections (legal headings)

- [ ] **Population-based ordering** - Change order based on local relevance
  - *Example*: List cities by population, vary order per page

- [ ] **Unique vocabulary extraction** - Identify unique words per page
  - *Method*: Python set comparison to find non-overlapping vocabulary
  - *Tool*: Google AI Studio for vocabulary analysis

### Variable Identification
- [ ] **Define replaceable variables** - Mark what changes per instance
  - *Common variables*: Location, service type, statistics, local entities

- [ ] **Sentence-level uniqueness** - Every sentence should have a variable
  - *Why it matters*: Prevents duplicate content across templated pages

- [ ] **Context consistency** - Variables must match query context (find/go/buy)
  - *Example*: Working hours connect to "find" intent predicates

---

## Post-Publication Checks

### 7-Day Check
- [ ] **Verify indexation** - URL appears in Search Console
- [ ] **Check for impressions** - Any visibility signals
- [ ] **If zero impressions** - Use URL Inspection Tool

### 14-Day Check
- [ ] **Review ranking positions** - Where does page appear?
- [ ] **Check click data** - Any user engagement?
- [ ] **If underperforming** - Add social media links for exploration

### 28-Day Check
- [ ] **Evaluate segment completion** - Does topic need supporting pages?
- [ ] **Add homepage links** - If not ranking, link from homepage
- [ ] **Add boilerplate links** - Include in footer/sidebar if appropriate
- [ ] **Revise opening paragraph** - Trigger re-evaluation with content changes

### Ongoing Optimization
- [ ] **Complete topical segments** - All related topics should be published
  - *Example*: Types of damages requires all damage type pages
- [ ] **Cross-link within segments** - Related pages should link to each other
- [ ] **Monitor for cannibalization** - Similar pages competing for same terms

---

## Component Reference

| Component | Use Case | Notes |
|-----------|----------|-------|
| **Vertical Tabs** | Multiple categories/types | Interactive, reduces page length |
| **Accordion FAQ** | Q&A sections | Helps People Also Ask optimization |
| **Statistics Grid** | Data presentation | Increases uniqueness with local stats |
| **Comparison Table** | Type/category comparisons | Structured data opportunities |
| **Tabbed Content** | Similar category groupings | Reduces content repetition |

---

## Common Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Same anchor text header/footer | Wastes variation opportunity | Use synonyms in footer |
| Informational link before commercial | Dilutes commercial intent | Commercial first, informational second |
| Headings too similar across pages | Template detection | 60%+ difference required |
| PDF without internal links | Missed PageRank distribution | Always include link section |
| No macro context in footer | Missing site-wide signals | Add instructional sentence |
| Same heading order across templates | Duplicate content signals | Vary order by population/relevance |

---

## External Link Strategy (Cross-Client)

### When to Use External Links
- [ ] **Non-competing clients** - Different locations or practice areas
- [ ] **Relevant topics** - Anchor text matches target page topic
- [ ] **Track all external links** - Maintain source/target/date log

### Link Tracking Format
| Source Site | Source URL | Target Site | Target URL | Anchor Text | Date |
|-------------|------------|-------------|------------|-------------|------|
| Sutliff Start | /property-damage | Murlow | /insurance-claims | "filing an insurance claim" | 2025-01-15 |

---

*Source: Koray Tugberk Gubur SEO Consulting Sessions, 2025*

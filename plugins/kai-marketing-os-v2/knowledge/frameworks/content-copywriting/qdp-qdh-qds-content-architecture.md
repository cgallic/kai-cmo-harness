# QDP, QDH, QDS Content Architecture SOP

**Query Deserves a Page, Heading, or Sentence**

A decision framework for determining when a contextual domain needs a "page" (QDP), "heading" (QDH), or "sentence" (QDS), while adjusting URL structure, internal links, topic priority, contextual coverage, depth, and prominence for achieving topical authority.

**Applies to**: Any local service business (legal, medical, home services, events, real estate, automotive, wellness, etc.)

---

## Core Concept

| Level | Abbreviation | When to Use |
|-------|--------------|-------------|
| **Page** | QDP | Topic meets 3+ of 4 query criteria AND index criteria |
| **Heading** | QDH | Topic has moderate demand but doesn't justify dedicated URL |
| **Sentence** | QDS | Topic needs mention for completeness but has minimal search signal |

---

## Google's Index Construction Criteria

Google constructs a new index based on three primary criteria:

### 1. Index Size
- Sufficient volume of documents covering the topic
- **Compare within category** - don't compare high-demand services to niche services
- Examples by industry:
  - Wedding venues: 50,000 docs may be standard; barn weddings: 5,000 sufficient
  - Plumbers: 100,000 docs standard; tankless water heater installation: 10,000 sufficient
  - Personal injury lawyers: 10,000 standard; bicycle accidents: 1,000 sufficient

### 2. Vocabulary Uniformity
- Documents share similar terminology and semantic patterns
- Consistent entity-attribute relationships across the corpus
- Industry-specific jargon creates natural vocabulary clusters

### 3. PageRank
- Accumulated authority signals across the document group
- **Compensating Factor**: If many GBPs (Google Business Profiles) exist with exact-match location name/address, this compensates for lower PageRank

### 4. Query Template (Bonus Signal)
- Clear structural pattern across entities, attributes, and documents
- Common templates by industry:

| Industry | Query Templates |
|----------|-----------------|
| **Legal** | `[city] + [practice area] + lawyer/attorney` |
| **Medical** | `[specialty] + doctor/clinic + near me`, `[city] + [specialty]` |
| **Home Services** | `[service] + [city]`, `[city] + [trade] + near me` |
| **Events** | `[event type] + venues + [city]`, `[city] + [event type] + services` |
| **Real Estate** | `[city] + real estate agent`, `homes for sale + [neighborhood]` |
| **Automotive** | `[service] + [city]`, `[brand] + mechanic + near me` |
| **Wellness** | `[service] + [city]`, `best [service] + near me` |

---

## Query-Level Criteria (4 Signals)

For a query to justify a new index/page, evaluate these four criteria:

| Criterion | Description | How to Check |
|-----------|-------------|--------------|
| **Different Entities** | Query involves distinct entities from existing content | Location/service differs from other targeted combinations |
| **High Search Demand** | Sufficient query volume | GSC data, keyword tools, Google Trends |
| **Recognizable Pattern** | Query follows a template Google understands | Check if similar queries exist across other locations/services |
| **Low Similarity** | Query is semantically distant from existing queries | Wedding → Corporate event = high distance; Wedding → Engagement party = low distance |

**Rule**: If a query meets **3+ of 4 criteria**, it strongly indicates a new page (QDP) is warranted.

---

## Industry-Specific Templates

### Location-Agnostic Templates (Always QDP for Major Services)

These topics require dedicated pages regardless of location:

| Template Type | Examples by Industry |
|---------------|---------------------|
| **Service Definition** | "What does a [service provider] do?" |
| **Process/How-To** | "How to [action] a [service]", "How to plan a [event type]" |
| **Cost/Pricing** | "[Service] cost", "How much does [service] cost" |
| **Comparison** | "[Service A] vs [Service B]", "[Option 1] vs [Option 2]" |
| **Statistics/Data** | "[Industry] statistics [year]", "[Location] [industry] trends" |

#### Industry Examples

**Events/Weddings:**
```
"How to plan a wedding"                    → QDP (Hypernym)
"How to plan an outdoor wedding"           → QDP (Hyponym - major)
"How to plan a micro wedding"              → QDH (Hyponym - niche)
```

**Home Services:**
```
"How much does a roof replacement cost"    → QDP (Hypernym)
"Metal roof cost vs shingle"               → QDP (Comparison - high demand)
"Flat roof replacement cost"               → QDH (Hyponym - lower demand)
```

**Medical:**
```
"What does a chiropractor do"              → QDP
"Chiropractic adjustment types"            → QDP
"Activator method chiropractic"            → QDH (specific technique)
```

**Legal:**
```
"What does a personal injury lawyer do"    → QDP
"Car accident claim process"               → QDP
"Rideshare accident claims"                → QDH (niche)
```

---

## Location-Specific, Service-Agnostic Templates

| Template | Typical Level | Example |
|----------|---------------|---------|
| `[State/City] + [Industry] + Laws/Regulations` | QDP | "California event permit requirements" |
| `[State] + [Service] + Requirements` | QDP | "Texas contractor license requirements" |
| `[State] + [Industry] + Statistics` | QDP | "Florida wedding industry statistics" |
| `Cost of [Service] in [Location]` | QDP or QDH | "Cost of living in Austin" |
| `Best [Service] in [City]` | QDP | "Best wedding venues in Nashville" |

---

## Location + Service Intersection Analysis

### Framework: Evaluate Any [Location] + [Service] Combination

**Step 1: Index Criteria Assessment**

| Signal | Check | Positive Indicator |
|--------|-------|-------------------|
| Index Size | Search `"[city] [service]"` in quotes | Results > category threshold |
| Vocabulary | Review top 10 results | Consistent terminology |
| PageRank/GBP | Check Local Pack | GBPs with exact-match location |

**Step 2: Query Criteria Assessment**

| Signal | Check | Positive Indicator |
|--------|-------|-------------------|
| Search Demand | Keyword tools, GSC | Volume > category threshold |
| Query Variations | Auto-complete, related searches | Multiple variations exist |
| Template Match | Compare to known patterns | Matches `[city] + [service]` |
| Entity Difference | Compare to existing pages | Location is distinct entity |

---

### Example 1: Event Company - "Wedding Venues in Austin"

**Index Criteria:**
- ✅ Index size: Large (Austin is major market)
- ✅ Vocabulary: Uniform ("wedding venue", "event space", "reception hall")
- ✅ PageRank: Strong GBP presence

**Query Criteria:**
- ✅ Search demand: High (major city + major service)
- ✅ Query variations: "Austin wedding venues", "wedding venues Austin TX", "best wedding venues Austin"
- ✅ Has template: `[event type] + venues + [city]`
- ✅ Different entity: Austin distinct from other cities

**Verdict**: QDP (4/4 criteria met)

---

### Example 2: Event Company - "Corporate Event Space in Round Rock"

**Index Criteria:**
- ⚠️ Index size: Smaller (suburb, niche service type)
- ✅ Vocabulary: Uniform
- ⚠️ PageRank: Fewer GBPs with exact match

**Query Criteria:**
- ⚠️ Search demand: Lower (smaller city + B2B service)
- ✅ Query variations: Some exist
- ✅ Has template: Yes
- ✅ Different entity: Round Rock is distinct

**Verdict**: QDH under Austin hub, or QDP if Round Rock is strategic market

---

### Example 3: Home Services - "Emergency Plumber in Phoenix"

**Index Criteria:**
- ✅ Index size: Large
- ✅ Vocabulary: Uniform ("24 hour plumber", "emergency plumbing")
- ✅ PageRank: Strong GBP presence, Local Pack triggered

**Query Criteria:**
- ✅ Search demand: High (urgent need + major city)
- ✅ Query variations: Many
- ✅ Has template: `[modifier] + [trade] + [city]`
- ✅ Different entity: Phoenix distinct

**Verdict**: QDP

---

### Example 4: Home Services - "Tankless Water Heater Installation in Scottsdale"

**Index Criteria:**
- ⚠️ Index size: ~20% of general plumbing (compare within category)
- ✅ Vocabulary: Uniform
- ⚠️ PageRank: Some GBPs but fewer

**Query Criteria:**
- ✅ Search demand: Moderate but sufficient
- ✅ Query variations: Good
- ✅ Has template: Yes
- ⚠️ Medium similarity to "water heater repair"

**Verdict**: QDP (service-specific pages convert better)

---

### Example 5: Medical - "Sports Medicine Doctor in Denver"

**Index Criteria:**
- ✅ Index size: Decent
- ✅ Vocabulary: Uniform (orthopedic, sports injury, athletic)
- ✅ PageRank: GBPs present

**Query Criteria:**
- ✅ Search demand: Good
- ✅ Query variations: "sports medicine Denver", "sports doctor near me Denver"
- ✅ Has template: Yes
- ✅ Different entity: Denver distinct

**Verdict**: QDP

---

### Example 6: Medical - "Pediatric Sports Medicine in Lakewood"

**Analysis:**
- Individual search demand: Low
- Suburb of Denver: Smaller market
- Double-niche: Pediatric + Sports Medicine

**Verdict**: QDH under Denver page, with clear section for pediatric specialty

---

## Decision Tree: Common Scenarios (Industry-Agnostic)

### Scenario 1: Two Overlapping Pages

**Situation (Event Company Example):**
```
page 1: domain.com/austin/wedding-venues/
page 2: domain.com/austin/ (targeting all events)
```
Both ranking on page 1-2 but not dominating.

**Decision Process:**
1. Export queries for both URLs from Search Console (exact match)
2. Calculate query overlap percentage
3. Check if overlap is caused by fraggles

| Overlap | Action |
|---------|--------|
| **>10%** | Configure relevance: add/remove/modify content, images, anchors |
| **>20%** | Check if seed queries are losing indexation continuity |

**Danger Signs:**
- Service-specific page loses index continuity for its seed query
- City hub getting more impressions than service page for service-specific queries

**Historical SERP Check:**
1. Search the query
2. Use Google Tools → set date to 1, 2, 3 years ago
3. If SERP vocabulary changes after every BCAU → keep 2 URLs
4. If SERP vocabulary stays same → constructed index → consider merging

---

### Scenario 2: New Location with Existing Flat Structure

**Situation (Home Services Example):**
```
Existing: domain.com/phoenix-plumber/
          domain.com/phoenix-drain-cleaning/
New service area: Scottsdale
```

**Decision Process:**
1. Check if existing URLs perform well
2. If not performing → change to better structure
3. If performing well → don't change existing URLs

**For New Locations:**
- If under existing metro area → nest under same structure
  - `phoenix-plumber/scottsdale`
- If fully different market → create new hub
  - `scottsdale/` or `scottsdale-plumber/`
- Match existing pattern unless existing pattern underperforms

---

### Scenario 3: Strong City Hub, Weak Service Pages

**Situation (Medical Practice Example):**
```
domain.com/denver/                    ← ranks well, attracts links
domain.com/denver/sports-medicine/    ← weak
domain.com/denver/physical-therapy/   ← non-ranking
```

**Decision Process:**
1. Check if root (city-hub) page ranks for specific query groups
2. If root ranks higher for general queries → consolidate around that context
3. For query segments root can't penetrate → flow relevance to sub-service URL

**Small Location with Low Demand:**
- Create extended contextual vector with sub-sections
- Consolidated strong page with high PageRank can penetrate all service combinations
- Use QDH for services that don't warrant separate pages

**If Sub-Service Has High Conversion Value:**
- Open dedicated page regardless of search volume
- Build index-size using content marketing, socials
- Service-specific pages often convert better even with lower traffic

---

### Scenario 4: Inconsistent URL Logic Across Locations

**Situation (Event Company Example):**
```
domain.com/austin/wedding-venues/
domain.com/dallas/
domain.com/houston-corporate-events/
domain.com/san-antonio/venues/
```

**Decision:**
- Respect historical authority
- Only standardize forward
- Reflect structure through:
  - Breadcrumbs
  - Internal links
  - Structured data (not URL changes)
- For new locations, pick one pattern and stick to it

---

### Scenario 5: Even Search Demand Split

**Situation (Event Company Example):**
Both queries high-volume and intent-rich:
- "Austin wedding venues"
- "Austin corporate event venues"

**Decision Process:**
1. Check related search terms from SERP and auto-completes
2. Analyze if clicked related terms overlap

**Create Separate Pages If:**
- Clicked related terms don't overlap
- Top-ranking GBPs differ between queries
- Top-ranking websites differ
- Index-size changes >25% between queries
- Different buyer intent (B2C weddings vs B2B corporate)

**Cross-Check:**
- `austin wedding venues + corporate`
- `austin corporate events + wedding`
- If these show different results → separate pages

---

### Scenario 6: Regional/State Pages Outperform City Pages

**Situation (Home Services Example):**
```
domain.com/roofing-services/         ← ranks regionally
domain.com/roof-replacement/         ← ranks statewide
City pages underperform
```

**Decision:**
- If regional pages rank for regional queries → acceptable
- For largest city → target from same segment (avoid cannibalization)
- For smaller cities → nest under service URLs:
  ```
  domain.com/roofing-services/mesa
  domain.com/roofing-services/tempe
  ```

---

### Scenario 7: No Physical Location But Service Area Demand

**Question:** Create city page without physical office/venue?

**Considerations:**
- If already getting impressions via GBP service area
- If ranking for "[service] near [city]" variations
- Service-area businesses can legitimately target cities they serve
- Use "serving [city]" language rather than "located in [city]"

**Recommendation:** Create page if:
- Genuine service capability in that area
- Search demand exists
- Can provide location-specific value (local knowledge, response time, etc.)

---

### Scenario 8: 100+ Thin Location Pages

**Situation:**
```
domain.com/city-name-wedding-venues/
```
All thin, template-based, low engagement, low crawl rate.

**Options:**
1. **Prune**: Remove lowest-performing pages (bottom 20%)
2. **Merge**: Combine into regional hubs (by metro area)
3. **Rewrite**: Add unique, valuable content per location
4. **Regional Hubs**: Collapse into "Greater [Metro]" pages

**Regional Hub Selection:**
- Use most recognized/searched location entity
- Metro area name usually works: "Greater Phoenix", "Dallas-Fort Worth Area"
- Must have sufficient search demand to represent cluster

---

### Scenario 9: Blog/Content Outranks Service Page

**Situation (Event Company Example):**
```
domain.com/blog/best-outdoor-wedding-venues-austin/  ← outperforms
domain.com/austin/outdoor-weddings/                   ← underperforms
```

**Options:**
| Action | When to Use |
|--------|-------------|
| Redirect | Blog is better, service page adds no value |
| Merge | Combine best elements of both |
| Nest | Move to `domain.com/austin/outdoor-weddings/guide/` |
| Differentiate | Sharpen intent: blog = research, service page = booking |

**Intent Separation:**
- `/blog/` = informational intent (research phase)
- `/[city]/[service]/` = transactional intent (booking phase)
- Keep intent clear but consider user journey

---

### Scenario 10: Location-First vs Service-First Structure

**Options:**
```
Location-first:  domain.com/austin/wedding-venues/
Service-first:   domain.com/wedding-venues/austin/
```

**Decision Criteria:**
| Factor | Location-First | Service-First |
|--------|----------------|---------------|
| Search patterns | "Austin wedding venues" | "Wedding venues in Austin" |
| Number of locations | Few locations (1-10) | Many locations (10+) |
| Business model | Local presence focus | Regional/national brand |
| Service complexity | Many services per location | Few services, many locations |

**Industry Tendencies:**
- **Event venues**: Location-first (venues are place-specific)
- **Home services**: Service-first (trades are service-specific)
- **Medical**: Location-first (patients search by area)
- **Legal**: Location-first (jurisdiction matters)

---

### Scenario 11: Competitors Use Different Structure

**Question:** Should structure match SERP norms?

**Analysis:**
1. Check what top 3-5 competitors use
2. Identify if Google favors one pattern (consistent #1 results)
3. Consider: Does their structure support their authority?

**Decision:** Structure should support:
- Topical authority signals
- Clear entity relationships
- Efficient PageRank flow
- Your content depth and business model

Don't copy competitors blindly. Match SERP norms only if it aligns with your content strategy.

---

## QDH Implementation (When Not QDP)

When QDP conditions aren't met, implement as QDH:

### Structure Template
```html
<h2>[Brand Name] [Service Category] Services</h2>

<h3>[Specific Service 1]</h3>
<!-- Include for this specific contextual domain: -->
- Service description
- Key differentiators
- CTA (contact, quote, booking)
- Relevant imagery
- Social proof if available

<h3>[Specific Service 2]</h3>
<!-- Same treatment -->
```

### Industry Examples

**Event Company:**
```html
<h2>Elegant Events Venue Services in Round Rock</h2>
<h3>Corporate Events</h3>
<h3>Private Parties</h3>
<h3>Non-Profit Galas</h3>
```

**Home Services:**
```html
<h2>Phoenix Plumbing Services by [Brand]</h2>
<h3>Water Heater Services</h3>
<h3>Drain Cleaning</h3>
<h3>Sewer Line Repair</h3>
```

**Medical:**
```html
<h2>Denver Orthopedic Specialties</h2>
<h3>Sports Medicine</h3>
<h3>Joint Replacement</h3>
<h3>Spine Care</h3>
```

---

## Quick Reference: QDP Signals Checklist

### Index Signals
- [ ] Sufficient index size (compare within category)
- [ ] Vocabulary uniformity in existing documents
- [ ] PageRank accumulation (or GBP compensation)
- [ ] Clear query template exists

### Query Signals (need 3+/4)
- [ ] Query involves different entities
- [ ] Query has high search demand
- [ ] Query follows recognizable pattern
- [ ] Query has low similarity to existing queries

### Additional Positive Signals
- [ ] Local Pack triggered
- [ ] Query terms appear in GBP titles/addresses
- [ ] Multiple query variations with decent demand
- [ ] Advanced SERP features present (FAQs, reviews, etc.)

---

## Implementation Priority Matrix

| Combination | Priority | Typical Level |
|-------------|----------|---------------|
| Core Service + Major City | HIGH | QDP |
| Core Service + Small City | MEDIUM | QDP or QDH |
| Niche Service + Major City | MEDIUM | QDP |
| Niche Service + Small City | LOW | QDH or QDS |
| Location-Agnostic (How-To, Cost, Comparison) | HIGH | QDP |
| State/Regional Content | HIGH | QDP |

### Industry-Specific Priority Examples

**Events:**
| Service | Major City | Small City |
|---------|------------|------------|
| Wedding Venues | QDP | QDP |
| Corporate Events | QDP | QDH |
| Birthday Parties | QDH | QDS |

**Home Services:**
| Service | Major City | Small City |
|---------|------------|------------|
| Emergency Plumbing | QDP | QDP |
| Water Heater Install | QDP | QDH |
| Faucet Repair | QDH | QDS |

**Medical:**
| Specialty | Major City | Small City |
|-----------|------------|------------|
| Primary Care | QDP | QDP |
| Sports Medicine | QDP | QDH |
| Pediatric Podiatry | QDH | QDS |

---

## Semantic Distance Reference

Use this to evaluate "Low Similarity" criterion:

### High Distance (Likely Separate Pages)
- Wedding → Corporate Event
- Emergency Repair → Preventive Maintenance
- Pediatric → Geriatric
- Residential → Commercial

### Medium Distance (Evaluate Other Criteria)
- Wedding → Engagement Party
- Plumbing → Drain Cleaning
- Sports Medicine → Orthopedics
- Personal Injury → Car Accidents

### Low Distance (Likely Same Page)
- Wedding Venue → Wedding Reception Hall
- Drain Cleaning → Clogged Drain Repair
- Sports Injuries → Athletic Injuries
- Car Accidents → Auto Accidents

---

## Related Frameworks

- `frameworks/entity-seo-knowledge-graph-deep-dive.md` - Entity relationships and Knowledge Graph
- `frameworks/query-fan-out-guide.md` - Query decomposition for AI search
- `channels/seo-content.md` - SEO content creation guidelines
- `frameworks/algorithmic-authorship.md` - Content structure for rankings

# Demand Generation Playbook

> **Use when:** Building pipeline for B2B sales, generating qualified leads, or designing multi-touch campaigns that move prospects through the funnel.

---

## Demand Gen vs Lead Gen

| | Lead Gen | Demand Gen |
|---|---------|-----------|
| **Goal** | Capture contact info | Create desire for your solution |
| **Tactic** | Gate content behind forms | Create ungated value that builds trust |
| **Metric** | Number of leads (MQLs) | Pipeline generated, revenue influenced |
| **Timeline** | Short-term (this quarter) | Long-term (this year+) |
| **Risk** | Lots of leads, few buyers | Fewer leads, higher quality |

**The shift in 2026:** Gating everything behind forms generates low-quality leads that waste sales time. The best B2B companies create demand first (trust, awareness, education), then capture it when buyers are ready.

---

## The Demand Gen Engine

```
CREATE DEMAND (ungated)          CAPTURE DEMAND (gated)
──────────────────────           ──────────────────────
Blog posts                       Demo request page
Podcasts                         Free trial
Social media content             Pricing page (with CTA)
YouTube videos                   Bottom-of-funnel content offers
Community participation          Webinar registration
Speaking / events                Intent signal (pricing page visit)
Influencer content               Retargeting to high-intent visitors
SEO educational content          Sales outreach to warm leads
Newsletter                       Product-qualified leads (PQL)
```

**Rule:** 70% of effort on demand creation, 30% on demand capture. Most companies invert this and wonder why their leads are garbage.

---

## Multi-Touch Campaign Framework

### The Campaign Architecture

```
CAMPAIGN: "{Topic/offer name}"
  │
  ├── AWARENESS (Top of Funnel)
  │   Content: Blog post, social posts, podcast episode
  │   Channels: Organic social, SEO, paid social (cold)
  │   CTA: Follow, subscribe, engage
  │   Goal: 10,000+ impressions
  │
  ├── EDUCATION (Middle of Funnel)
  │   Content: Webinar, comparison guide, case study
  │   Channels: Email nurture, retargeting, community
  │   CTA: Register, download, watch
  │   Goal: 500+ engaged prospects
  │
  ├── CONSIDERATION (Bottom of Funnel)
  │   Content: Demo, free trial, pricing, ROI calculator
  │   Channels: Retargeting, email, sales outreach
  │   CTA: Start trial, book demo, talk to sales
  │   Goal: 50+ qualified opportunities
  │
  └── CLOSE (Sales Handoff)
      Content: Custom proposal, case study matching their use case
      Channels: Sales email, call, meeting
      CTA: Sign contract
      Goal: 15+ closed deals
```

### Campaign Calendar (Quarterly)

| Month | Campaign | Focus Stage |
|-------|----------|------------|
| Month 1, Week 1-2 | Launch awareness content blitz | Awareness |
| Month 1, Week 3-4 | Webinar + content series | Education |
| Month 2, Week 1-2 | Retargeting + nurture sequences | Consideration |
| Month 2, Week 3-4 | Direct sales outreach to engaged leads | Close |
| Month 3, Week 1-2 | New campaign theme launch | Awareness |
| Month 3, Week 3-4 | Repeat education → close cycle | Full funnel |

---

## Lead Scoring & Qualification

### MQL → SQL → Opportunity Pipeline

```
VISITOR → LEAD → MQL → SQL → OPPORTUNITY → CUSTOMER
                  ↑      ↑
                  │      └── Sales accepts: budget, authority, need, timeline
                  └── Marketing qualifies: behavior score + fit score
```

### Scoring Model

See `playbooks/marketing-automation.md` for detailed lead scoring framework.

Quick version:
- **Fit score** (demographics): job title, company size, industry match
- **Behavior score** (engagement): pages visited, content downloaded, emails opened
- **Intent score** (buying signals): pricing page, demo page, case study, competitor comparison

| Score | Status | Action |
|-------|--------|--------|
| 0-30 | Cold | Nurture with educational content |
| 31-60 | Warm (MQL) | Targeted campaigns, sales development |
| 61-80 | Hot (SQL) | Sales outreach within 24 hours |
| 81+ | Opportunity | Active sales process |

---

## Channel Playbooks for Demand Gen

### Content + SEO (Compound Returns)

- Publish 2-4 SEO-optimized articles per week
- Target: problem-aware and solution-aware keywords
- Don't gate blog content (let it rank and build trust)
- Insert CTAs naturally (not popups on every page)
- Run `/content-ideas` for keyword opportunity analysis

### Paid Social (Meta + LinkedIn)

- **Cold campaigns:** Thought leadership content → build awareness
- **Warm campaigns:** Retarget content engagers with case studies
- **Hot campaigns:** Retarget pricing/demo page visitors with direct offer
- See `playbooks/ad-campaign-management.md` for full setup

### Webinars

- Run 1-2x/month on topics your ICP cares about
- Co-host with complementary companies (shared audience)
- Record and repurpose (see `playbooks/content-repurposing.md`)
- Follow-up sequence: recording → insights → offer (not just "buy now" after webinar)

### Outbound (SDR/BDR)

- Target accounts showing intent signals (pricing page visits, ad clicks, content engagement)
- Personalize: reference specific content they engaged with
- Sequence: 3-touch minimum (email → LinkedIn → email)
- Don't cold-pitch. Open with value, earn the conversation.

---

## Metrics

| Metric | What It Measures | B2B Benchmark |
|--------|-----------------|---------------|
| Marketing-sourced pipeline | $ pipeline from marketing-touched leads | 40-60% of total |
| Marketing-influenced revenue | Revenue where marketing touched any stage | 60-80% of total |
| MQL → SQL conversion | Marketing leads accepted by sales | 20-40% |
| SQL → Opportunity conversion | Sales-qualified leads that become deals | 40-60% |
| Pipeline velocity | Avg days from MQL to close | 30-90 days |
| Cost per MQL | Marketing spend / MQLs | $50-200 |
| Cost per SQL | Marketing spend / SQLs | $200-800 |
| Cost per Opportunity | Marketing spend / opportunities | $500-2000 |

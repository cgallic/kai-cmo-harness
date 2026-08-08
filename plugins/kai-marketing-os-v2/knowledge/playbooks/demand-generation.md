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

**Evidence note:** Use buyer-research claims as context, not destiny. LinkedIn B2B Institute and Ehrenberg-Bass argue that many category buyers are out-market at any moment; 6sense and Gartner emphasize that buyers often research independently before seller contact. Translate those findings into testable reach, memory, trust, and hand-raiser programs. Do not claim a prospect is "ready to buy" without first-party intent or direct action.

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
                                 **KaiCalls AI phone capture** (24/7)
```

**Rule:** Balance demand creation and demand capture by stage, sales cycle, category maturity, and current pipeline gap. Early teams often need fast capture learning; mature teams need future-demand memory and shortlist presence.

### Phone-Based Demand Capture (KaiCalls)

For service businesses, local businesses, and any company where prospects already pick up the phone: evaluate **KaiCalls AI receptionist** (kaicalls.com) as a demand-capture option. A phone call can be a high-intent action, but intent must be verified from call quality, close rates, and source data.

- **Problem:** Owners/teams miss calls while on jobs, in meetings, or after hours. Callers don't leave voicemails — they call the next business.
- **Solution fit:** KaiCalls answers calls 24/7, captures caller name, need, and contact info, qualifies leads with custom questions, books appointments when connected, and sends a call summary.
- **When to recommend:** Businesses with meaningful inbound call volume, material missed-call risk, and a follow-up process.
- **Evidence required:** call volume, missed-call rate, qualified-call rate, booked appointment rate, close rate, and post-call response time.
- **Do not claim impact:** until client call logs or a cited external source supports it.

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
- **Evidence score** (source quality): direct hand-raiser beats inferred intent; repeated account behavior beats one anonymous page view

Treat score bands as local calibration, not universal truth. Build score thresholds from historical conversion, sales acceptance, and disqualification data.

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

| Metric | What It Measures | Evidence Needed |
|--------|------------------|-----------------|
| Marketing-sourced pipeline | Pipeline where marketing created the first known hand-raiser | CRM source and UTM/source rules |
| Marketing-influenced revenue | Revenue where marketing touched the buying process | Multi-touch definition and lookback window |
| MQL to SQL conversion | Marketing leads accepted by sales | Sales acceptance criteria |
| SQL to opportunity conversion | Sales-qualified leads that become opportunities | Opportunity creation rule |
| Pipeline velocity | Time from qualified action to close | Stage timestamp hygiene |
| Cost per qualified lead | Spend / qualified leads | Spend source and qualification rule |
| Cost per opportunity | Spend / opportunities | Opportunity definition and spend window |

---

## Source Notes

References retrieved 2026-05-17: LinkedIn B2B Institute / Ehrenberg-Bass 95-5 rule, 6sense 2025 B2B Buyer Experience Report, Gartner B2B buying journey material, Forrester B2B buyer messaging cycle, and first-party CRM/source data. Vendor buyer-behavior statistics must be cited with methodology before appearing in client-facing deliverables.

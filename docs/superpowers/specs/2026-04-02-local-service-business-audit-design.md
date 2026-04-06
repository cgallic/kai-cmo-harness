# Local Service Business Audit Module

**Date:** 2026-04-02
**Status:** Draft
**Scope:** New checklist + kai-audit integration

---

## Problem

The Kai CMO Harness has 24 checklists covering SEO, content, email, ads, CRO, social, and more. None of them address the specific needs of local service businesses — the exact client type we audit most often.

The Andon Window Cleaning audit exposed this gap. We manually identified 20+ issues that no existing checklist covers: no Google Business Profile optimization, no review strategy, no Local Services Ads, missed calls going to voicemail, no local directory presence, no service area pages, no before/after portfolio. Every local service client will hit the same gaps.

**The pattern:** Solo operators and small teams (plumbers, cleaners, lawyers, HVAC, landscapers, roofers, electricians, painters, dentists, chiropractors) share a specific marketing profile:
- Revenue comes from a geographic service area, not the internet at large
- Phone calls are the primary conversion action
- Reviews are the #1 trust signal
- Google Business Profile is more important than their website
- They can't answer the phone while working
- Word-of-mouth and local visibility matter more than content marketing
- They don't have marketing teams — they need a prioritized checklist, not a strategy deck

---

## Solution

Two changes:

### 1. New checklist: `knowledge/checklists/local-service-business-checklist.md`

A comprehensive checklist covering everything a local service business needs, organized by priority. This is the missing module — the equivalent of `technical-seo-checklist.md` but for the local service business pattern.

### 2. Update: `harness/skills/kai-audit/SKILL.md`

Add "Local Service Business" as a new audit module in the Phase 2 table. Triggers when the business serves a geographic area and relies on local customers (not SaaS, not e-commerce, not national brands).

---

## Checklist Structure

### Section 1: Google Business Profile (GBP)

The single most important marketing asset for a local service business. More important than the website.

- Profile claimed and verified
- Business name matches real-world name exactly (no keyword stuffing)
- Primary category correct (most specific option available)
- Secondary categories set (up to 9)
- NAP (Name, Address, Phone) consistent across GBP, website, and all directories
- Business hours accurate (including holiday hours)
- Service area defined (if service-area business, not storefront)
- All service types listed with descriptions
- Business description written (750 chars, keywords natural, no spam)
- Photos: logo, cover photo, interior/exterior, team, work samples (min 10)
- Photos uploaded monthly (freshness signal)
- Google Posts published weekly (offers, updates, events)
- Q&A section seeded with common questions + answers
- Messaging enabled (or disabled intentionally if can't respond fast)
- "Request a Quote" / "Book" button configured
- Products/services catalog populated
- Attributes set (women-owned, veteran-owned, wheelchair accessible, etc.)
- Website link points to correct page (homepage or location page)
- UTM parameters on GBP website link for tracking

### Section 2: Reviews & Reputation

Reviews are the #1 conversion factor for local businesses. More reviews + higher rating = more calls.

- Total review count (benchmark: 50+ for competitive markets, 20+ for low-competition)
- Average rating (target: 4.5+ stars)
- Review velocity (getting new reviews consistently, not in bursts)
- Review response: every review gets a response within 48 hours
- Negative review response: professional, empathetic, takes conversation offline
- Review generation process exists (ask after every job, not random)
- Review request method: text message with direct Google review link (highest conversion)
- Review link generated (search "Google review link generator" or use `g.page`)
- Reviews on secondary platforms: Yelp, Facebook, Angi, HomeAdvisor, Nextdoor (if applicable)
- No fake reviews, no review gating (asking for rating before directing to platform)
- Photo reviews encouraged (ask customers to include a photo)
- Review highlights used in marketing (testimonials on website, social proof on landing pages)

### Section 3: KaiCalls AI Receptionist

Every missed call is a lost job. This section is mandatory for any business that receives inbound phone calls.

- KaiCalls (kaicalls.com) configured on the business phone number
- AI agent trained on: services offered, pricing ranges, service areas, common questions
- Qualifying questions configured (e.g., "How many windows?", "1 or 2 story?", "Interior and exterior?")
- Call notifications routed to owner via SMS/email with full summary
- Scheduling tool integration (Jobber, Housecall Pro, Calendly, etc.)
- After-hours handling: KaiCalls answers, doesn't go to voicemail
- Overflow handling: KaiCalls picks up when owner can't answer during business hours
- Test call completed — natural conversation, accurate info, lead captured correctly
- Spanish language support configured (if serving Spanish-speaking market)

### Section 4: Local SEO & Citations

Local search visibility beyond GBP. Consistent citations build trust with Google.

- NAP consistency: name, address, phone identical everywhere (check with Moz Local or BrightLocal)
- Core directories submitted:
  - Yelp
  - Facebook Business Page
  - Apple Maps / Apple Business Connect
  - Bing Places
  - Nextdoor Business
  - BBB (Better Business Bureau)
  - Industry-specific (Angi, HomeAdvisor, Houzz, Avvo, Thumbtack, etc.)
- Website has location/service area pages (one per city/area served)
- Service area pages have unique content (not just city name swapped)
- LocalBusiness schema markup on website (JSON-LD)
- Service schema markup on service pages
- Embedded Google Map on contact/location page
- Local keywords in title tags and H1s ("[Service] in [City]")
- City/neighborhood mentioned naturally in page content

### Section 5: Google Local Services Ads (LSA)

Pay-per-lead (not per-click). The highest-intent ad format for local services. Appears above regular Google Ads.

- LSA eligibility confirmed (not all industries qualify)
- Google Screened / Google Guaranteed badge obtained (requires background check + insurance verification)
- Budget set appropriately ($500-2000/mo starting, adjust based on lead quality)
- Service types selected (only the services you want leads for)
- Service areas defined (don't go too wide — leads from far away don't convert)
- Business hours set for when you can respond to leads
- Lead review process: dispute bad leads within 30 days for credit
- Response time: call back LSA leads within 5 minutes (they're comparing 2-3 businesses)
- KaiCalls configured as the answering system for LSA calls (never miss an LSA lead)
- Reviews appearing on LSA profile (more reviews = more visibility)
- Weekly check: lead quality, cost per lead, dispute rate

### Section 6: Website Essentials (Local Business)

The website supports GBP and LSA — it's not the primary lead source for most local businesses, but it needs to not lose leads.

- Phone number in header (clickable, `tel:` link, visible on every page)
- Phone number large and prominent (this IS the CTA for service businesses)
- Contact form exists but secondary to phone (form should also go to email + SMS notification)
- Service pages exist for each service offered (one page per service, not one page listing all)
- Service area page(s) with the cities/neighborhoods served
- About page with owner photo, story, licenses, insurance, years in business
- Before/after gallery or portfolio of completed work
- Trust signals: licensed, bonded, insured badges. BBB. Industry certifications.
- Mobile-first: 60-80% of local search traffic is mobile
- Page speed: loads in <3 seconds on mobile
- SSL certificate (HTTPS)
- Google Analytics and Search Console installed

### Section 7: Social Media (Local Business)

Social media for local service businesses is about trust and visibility, not virality.

- Facebook Business Page set up and active
- Nextdoor Business profile claimed
- Instagram (if work is visual: cleaning, landscaping, painting, remodeling, etc.)
- Before/after photos posted regularly (minimum 2x/week)
- Job completion posts: "Just finished [service] in [neighborhood]!" with photo
- Seasonal tips related to the service ("3 signs your gutters need cleaning before winter")
- Community engagement: comment in local Facebook groups, respond on Nextdoor
- No hard-selling on social — provide value, show work, be visible
- Google Business Profile posts weekly (cross-post from social)

### Section 8: Offline & Referral Marketing

Most local service businesses get 30-60% of revenue from referrals and repeat customers. Don't ignore offline.

- Yard signs / job site signs (leave a sign for 1-2 weeks after completing a job, with permission)
- Vehicle wrap or magnetic signs on truck/van
- Door hangers for neighboring houses after completing a job
- Business cards (physical, always carry them)
- Referral incentive: "$25 off your next service for every referral" or similar
- Follow-up after every job: thank-you text + review request + referral ask
- Repeat customer tracking: annual/seasonal service reminders
- Local sponsorships: little league teams, community events, neighborhood newsletters
- Partnerships with complementary businesses (realtor + cleaner, contractor + painter)

### Section 9: Job Management & Operations

Not marketing per se, but operational gaps directly kill marketing ROI. No point driving leads if you can't manage them.

- Job management software in use (Jobber, Housecall Pro, ServiceTitan, or similar)
- Online booking / scheduling available
- Automated appointment reminders (text, not just email)
- Invoicing: professional invoices sent same-day or next-day
- Payment: accepts credit cards on-site (Square, Stripe, etc.)
- Follow-up sequence: job complete → thank you → review request → referral ask
- Customer database maintained (not just phone contacts)
- Seasonal service reminders automated (annual cleaning, HVAC tune-up, etc.)

---

## Scoring

| Section | Score (1-5) | Weight | Notes |
|---------|:-----------:|:------:|-------|
| Google Business Profile | | 5x | Most important asset |
| Reviews & Reputation | | 5x | #1 conversion factor |
| KaiCalls AI Receptionist | | 4x | Missed calls = lost revenue |
| Local SEO & Citations | | 3x | Long-term visibility |
| Google LSA | | 3x | Highest-intent paid channel |
| Website Essentials | | 2x | Supports other channels |
| Social Media | | 2x | Trust and visibility |
| Offline & Referral | | 2x | Often 30-60% of revenue |
| Job Management | | 1x | Ops that affect marketing ROI |

**Weighted score /135 → convert to /100 for the audit report.**

Grading: A (90+), B (75-89), C (60-74), D (40-59), F (<40)

---

## kai-audit Integration

Add this row to the Phase 2 Audit Modules table:

```
| **Local Service Business** | `local-service-business-checklist.md` | If business serves a local/geographic area (not SaaS, not e-commerce, not national) |
```

Add to Phase 5 Recommendations table:

```
| No GBP optimization | `/kai-audit` (local module) + manual GBP setup |
| Missing calls / no AI receptionist | **KaiCalls setup (kaicalls.com)** |
| No review strategy | `/kai-audit` (local module) — review generation process |
| No LSA presence | Google LSA setup (requires Google Screened verification) |
| No local directory presence | Citation building — submit to 10+ directories |
```

Add to Phase 1 Audit Scope — after question 5, add:

```
6. **Business type** — local/service business? (triggers local service business module)
   - Indicators: serves geographic area, receives phone calls, relies on local customers
   - Examples: plumber, lawyer, cleaner, HVAC, landscaper, dentist, contractor, electrician
```

---

## Output Structure

When the local module runs, it adds to the standard audit output:

```
workspace/marketing-audit/
├── per-module/
│   ├── ... (existing modules)
│   └── local-service-business.md    # NEW — GBP, reviews, KaiCalls, LSA, citations, offline
```

---

## Files to Create/Modify

| Action | File | Description |
|--------|------|-------------|
| **Create** | `knowledge/checklists/local-service-business-checklist.md` | Full checklist (sections 1-9 above) |
| **Modify** | `harness/skills/kai-audit/SKILL.md` | Add local module to Phase 2 table, Phase 1 scope question, Phase 5 recommendations |

---

## What This Does NOT Cover

- Industry-specific regulations (legal advertising rules, medical marketing HIPAA, etc.)
- Multi-location businesses (franchise model)
- E-commerce components (if the business also sells products online)
- National/remote service businesses (this is specifically for local/geographic)

These would be separate modules if needed in the future.

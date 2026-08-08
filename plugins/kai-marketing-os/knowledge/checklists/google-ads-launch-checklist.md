# Google Ads Launch Checklist

> **Use when:** Setting up or launching Google Ads campaigns (Search, Performance Max, Display, YouTube).

---

## Account Setup

- [ ] Google Ads account created and billing configured
- [ ] Conversion tracking set up (Google Tag or GA4 import)
- [ ] Conversion actions defined: primary (purchase, signup) and secondary (page view, scroll)
- [ ] Test conversion fired and visible in dashboard
- [ ] Google Analytics 4 linked to Google Ads
- [ ] Google Search Console linked (if available)
- [ ] Auto-tagging enabled (for GA4 attribution)
- [ ] Enhanced conversions enabled (for better tracking with cookie limits)

---

## Campaign Configuration

### Search Campaigns
- [ ] Campaign objective matches goal (Conversions, not Clicks or Impressions)
- [ ] Bid strategy appropriate for stage:
  - New campaign: Manual CPC or Maximize Clicks (learning)
  - With data (30+ conversions): Target CPA or Maximize Conversions
- [ ] Daily budget set (minimum $30/day for meaningful data)
- [ ] Campaign name follows convention: `GOOGLE_SEARCH_{AUDIENCE}_{DATE}`
- [ ] Geographic targeting: "Presence" only (not "Presence or interest")
- [ ] Language targeting set correctly
- [ ] Ad schedule: set to business hours if call tracking, otherwise 24/7
- [ ] Search Partners: OFF (lower quality, enable later if needed)

### Keywords
- [ ] Keyword research completed (use Keyword Planner or SEMrush)
- [ ] Match types intentional:
  - Exact match [keyword]: highest intent, lowest volume
  - Phrase match "keyword": moderate intent and volume
  - Broad match keyword: highest volume, needs negative keywords
- [ ] 10-20 keywords per ad group (not 100+)
- [ ] Ad groups themed: one topic per ad group (STAG structure)
- [ ] Negative keywords added:
  - Competitors (unless targeting competitor terms intentionally)
  - Irrelevant modifiers (free, jobs, salary, DIY, cheap)
  - Brand negatives on non-brand campaigns (avoid cannibalization)

### Ad Copy
- [ ] 3+ Responsive Search Ad headlines per ad group (30 chars each)
- [ ] Headlines include primary keyword (Quality Score impact)
- [ ] 2+ descriptions per ad group (90 chars each)
- [ ] CTA in at least one headline ("Start Free Trial", "Get Quote")
- [ ] Unique selling points in descriptions
- [ ] Numbers/stats included where possible ("500+ clients", "24/7 service")
- [ ] No Google Ads policy violations (check `harness/references/google-ads-policy-reference.md`)
- [ ] Pin best headline to position 1 (if one clearly outperforms)

### Ad Extensions (now called Assets)
- [ ] Sitelink extensions (4-6 links to key pages)
- [ ] Callout extensions (3-4 selling points: "Free Trial", "24/7 Support")
- [ ] Structured snippet extensions (categories, services, types)
- [ ] Call extension (phone number, if calls are valuable)
- [ ] Location extension (if local business)
- [ ] Image extensions (relevant product/service images)
- [ ] Price extensions (if applicable)

---

## Performance Max Campaigns

- [ ] Campaign objective: Conversions (with value if possible)
- [ ] Asset groups created:
  - 5+ headlines (mix of short and long)
  - 5+ descriptions
  - 5+ images (landscape + square + portrait)
  - 1+ videos (or Google will auto-generate — usually bad)
  - 2+ logos
  - Business name and final URL
- [ ] Audience signals configured (your best audiences as hints, not hard targeting)
- [ ] Budget: minimum $50/day (PMax needs volume)
- [ ] URL expansion: decide ON or OFF
  - ON: Google finds high-converting pages automatically (more reach)
  - OFF: traffic only goes to your specified URLs (more control)
- [ ] Brand exclusions set (don't waste PMax budget on brand terms)

---

## Display Campaigns

- [ ] Responsive Display Ads configured (not uploaded image ads)
- [ ] 5+ headlines, 5+ descriptions, 5+ images, 2+ logos
- [ ] Targeting: managed placements, in-market, or remarketing audiences
- [ ] Frequency capping: 5-7 impressions per user per day
- [ ] Content exclusions: exclude sensitive categories, parked domains
- [ ] Placement exclusions: exclude mobile apps (adsenseformobileapps.com)

---

## YouTube/Video Campaigns

- [ ] Video ad uploaded to YouTube (not directly to Google Ads)
- [ ] Video length: 15-30 seconds recommended for skippable
- [ ] First 5 seconds: strong hook (earns the non-skip)
- [ ] Companion banner uploaded (300x60)
- [ ] CTA overlay configured
- [ ] Targeting: topic, placement, audience, or keyword-based
- [ ] Bid strategy: Target CPV or Maximize Conversions

---

## Landing Page

- [ ] Landing page matches ad message (message match)
- [ ] Page loads in < 3 seconds on mobile
- [ ] CTA visible above the fold
- [ ] No navigation distractions (consider removing top nav on ad landing pages)
- [ ] Mobile optimized
- [ ] Conversion tracking fires on thank-you/confirmation page
- [ ] UTM parameters preserved through to conversion

---

## Pre-Launch Final Checks

- [ ] Review all ads for typos and grammar
- [ ] Verify all landing page URLs are correct
- [ ] Confirm conversion tracking fires (use Google Tag Assistant)
- [ ] Check geographic targeting (not accidentally targeting wrong country)
- [ ] Verify budget and bid settings
- [ ] All ad extensions approved (check for disapprovals)
- [ ] Campaign start date correct (not running before intended)
- [ ] Negative keyword list complete

---

## Post-Launch (First 7 Days)

### Daily
- [ ] Ads approved and serving (no disapprovals?)
- [ ] Budget spending as expected (not over- or under-pacing?)
- [ ] Conversions tracking (check real-time in GA4)
- [ ] CPC within expected range

### Day 3
- [ ] Search Terms Report reviewed (add negative keywords for irrelevant queries)
- [ ] Quality Scores checked (target 7+ for all keywords)
- [ ] Impression share reviewed (losing due to budget or rank?)
- [ ] Any ad disapprovals resolved

### Day 7
- [ ] Performance review against targets (CPA, ROAS, CTR)
- [ ] Pause underperforming keywords (CPA > 2x target, 0 conversions)
- [ ] Pause underperforming ad variants (CTR < 1% after 500+ impressions)
- [ ] Expand negatives based on search terms
- [ ] Document learnings for next optimization cycle

---

## Key Benchmarks

| Metric | Search | Display | YouTube | PMax |
|--------|--------|---------|---------|------|
| CTR | 3-8% | 0.3-0.8% | 0.5-2% | Varies |
| CPC | $1-5 | $0.30-1 | $0.02-0.10 (CPV) | Varies |
| Conversion Rate | 3-8% | 0.5-2% | 0.5-1% | Varies |
| Quality Score | 7+ | N/A | N/A | N/A |
| Impression Share | 60%+ | 20%+ | N/A | N/A |

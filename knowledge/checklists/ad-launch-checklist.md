# Ad Launch Checklist — Cross-Platform

> **Use when:** Launching any paid advertising campaign on any platform.

---

## Pre-Launch (Before Activating)

### Strategy
- [ ] Campaign objective matches business goal (not platform default)
- [ ] Target audience defined (cold / warm / hot)
- [ ] Budget set with daily cap (minimum viable for learning phase)
- [ ] Campaign naming convention applied: `{PLATFORM}_{OBJECTIVE}_{AUDIENCE}_{DATE}`
- [ ] KPI targets defined (CPA, ROAS, CTR)
- [ ] Test plan documented (what variable are you testing first?)

### Creative
- [ ] 3+ ad variants per ad set (minimum for algorithm optimization)
- [ ] Hook passes 3-second test (read first line — would you stop scrolling?)
- [ ] Single clear CTA per ad (not two competing actions)
- [ ] Character limits respected per platform (no truncation)
- [ ] Image/video specs match platform requirements
- [ ] Mobile preview checked (most impressions are mobile)
- [ ] No banned words from quality gate
- [ ] A/B test matrix structured (test one variable at a time)

### Compliance
- [ ] Platform TOS checked (run `/ad-copy` with platform policy loaded)
- [ ] FTC disclosure included if endorsement or testimonial
- [ ] Special Ad Category enabled if housing/employment/credit (Meta)
- [ ] AI content disclosure added (TikTok, if applicable)
- [ ] CAN-SPAM compliance (if email-to-ad funnel)
- [ ] Landing page matches ad promise (no bait-and-switch)
- [ ] Privacy policy accessible from landing page

### Tracking
- [ ] UTM parameters set on all ad links
  - utm_source: platform name
  - utm_medium: paid_social / cpc / display
  - utm_campaign: campaign name
  - utm_content: ad variant identifier
- [ ] Conversion pixel installed and verified
- [ ] Conversion events configured (purchase, signup, lead)
- [ ] Test conversion fired and visible in platform dashboard
- [ ] Attribution window set correctly (7-day click, 1-day view typical)

### Landing Page
- [ ] Page loads in under 3 seconds (mobile)
- [ ] Above-the-fold matches ad messaging (no disconnect)
- [ ] Form/CTA visible without scrolling on mobile
- [ ] Social proof visible (testimonials, logos, numbers)
- [ ] No broken links or images
- [ ] Thank-you page configured (fires conversion pixel)

---

## Launch Day

### Activation
- [ ] Campaign set to correct start date/time
- [ ] Budget confirmed (daily and total)
- [ ] Bid strategy appropriate for campaign maturity
- [ ] All ad variants approved by platform (no disapprovals pending)
- [ ] Exclusion audiences applied (existing customers, employees)

### First Hour
- [ ] Ads serving (impressions showing in dashboard)
- [ ] Clicks landing on correct page
- [ ] Conversion pixel firing (check with Pixel Helper / Tag Assistant)
- [ ] No error pages or broken checkout flows

---

## Optimization (Ongoing)

### Daily (5 min)
- [ ] Check for disapproved ads
- [ ] Check budget pacing
- [ ] Kill any ad with 2x CPA target + 0 conversions after 1000 impressions

### Weekly (30 min)
- [ ] Review CPA, ROAS, CTR by ad set
- [ ] Pause underperformers (CPA > 1.5x target for 7+ days)
- [ ] Check frequency (>2.5 = creative fatigue)
- [ ] Refresh creative if needed
- [ ] Adjust budgets (+/- 20% max per day)
- [ ] Review search terms report (Google — add negative keywords)

### Monthly (2 hours)
- [ ] Full performance report
- [ ] Budget reallocation across platforms
- [ ] New audience testing (10-20% of budget)
- [ ] Creative strategy refresh
- [ ] Competitor ad research (`/ad-research`)
- [ ] Landing page conversion rate review

---

## Kill Criteria

| Signal | Action | Threshold |
|--------|--------|-----------|
| No conversions | Kill ad variant | After 2x CPA budget spent |
| Low CTR (Meta) | Kill or refresh creative | < 0.5% after 1000 impressions |
| Low CTR (Google) | Kill or improve Quality Score | < 1% after 500 impressions |
| High CPA | Pause, investigate audience/creative | > 1.5x target for 7 consecutive days |
| High frequency | Refresh creative | > 3 on same audience |
| Rising CPA trend | Expand audience or refresh creative | 20%+ week-over-week increase |

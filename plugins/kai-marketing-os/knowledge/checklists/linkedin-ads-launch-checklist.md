# LinkedIn Ads Launch Checklist

> **Use when:** Setting up or launching LinkedIn ad campaigns for B2B lead generation, brand awareness, or recruitment.

---

## Account Setup

- [ ] LinkedIn Campaign Manager account created
- [ ] Company page linked and verified
- [ ] LinkedIn Insight Tag installed on all website pages
- [ ] Conversion tracking configured:
  - Lead form submission
  - Signup/registration
  - Key page views (pricing, demo request)
- [ ] Matched Audiences created:
  - Website retargeting audience (Insight Tag)
  - Email list uploaded (company email match)
  - Lookalike audiences (from customer list)

---

## Campaign Configuration

### Campaign Settings
- [ ] Campaign group organized by objective/offering
- [ ] Campaign objective selected:
  - Brand awareness: Reach
  - Consideration: Website visits, Engagement
  - Conversion: Lead generation, Website conversions
- [ ] Budget: minimum $50/day (LinkedIn is expensive — need volume for learning)
- [ ] Schedule: set to business days + hours (B2B audience is active M-F, 8am-6pm)
- [ ] Bid strategy: Maximum delivery (start) → Manual bidding (with data)
- [ ] Campaign name convention: `LI_{OBJECTIVE}_{AUDIENCE}_{DATE}`

### Audience Targeting
- [ ] Target audience defined with LinkedIn-specific filters:

| Filter | Use For | Example |
|--------|---------|---------|
| Job title | Specific roles | "VP Marketing", "CTO" |
| Job function | Broader role category | Marketing, IT, Operations |
| Seniority | Decision-maker targeting | Director, VP, C-Suite |
| Company size | SMB vs Enterprise | 51-200, 201-500, 1000+ |
| Industry | Vertical focus | Legal, Healthcare, SaaS |
| Company name | ABM (account-based) | Target list of 50 companies |
| Skills | Interest/expertise signal | "Digital Marketing", "Python" |
| Groups | Engaged professionals | Industry-specific groups |

- [ ] Audience size: 50K-500K (sweet spot for LinkedIn)
- [ ] Audience expansion: OFF initially (test core audience first)
- [ ] Exclusions: competitors, existing customers, employees

### Lead Gen Forms (if using)
- [ ] Form fields limited to 3-5 (pre-filled from LinkedIn profile)
- [ ] Recommended fields: name, email, job title, company (auto-filled)
- [ ] Custom question: only if critical for qualification
- [ ] Thank-you message includes: what they'll receive and when
- [ ] Hidden fields: campaign name, form name (for CRM tracking)
- [ ] CRM integration configured (HubSpot, Salesforce, etc.) or CSV export set up
- [ ] Privacy policy URL included (required)

---

## Ad Creative

### Sponsored Content (Single Image)
- [ ] Intro text: 150 chars recommended (600 max, truncates at ~150 on mobile)
- [ ] Headline: 70 chars max
- [ ] Description: 100 chars (only shows on desktop Audience Network)
- [ ] Image: 1200x627px (1.91:1 ratio)
- [ ] Image is high quality, not a stock photo cliché
- [ ] Text on image < 20% (soft rule but affects engagement)
- [ ] CTA button selected (appropriate to objective)

### Sponsored Content (Carousel)
- [ ] 2-10 cards (3-5 is the sweet spot)
- [ ] Each card: 1080x1080px image
- [ ] Each card: headline (45 chars) + landing URL
- [ ] Cards tell a sequential story or present key points
- [ ] First card is the hook (most people only see 1-2 cards)

### Sponsored Content (Video)
- [ ] Video: 3-30 seconds recommended (max 30 min)
- [ ] Aspect ratio: 16:9 (landscape) or 1:1 (square — more feed real estate)
- [ ] Captions: included (most LinkedIn users scroll sound-off)
- [ ] First 3 seconds: hook (text overlay + movement)
- [ ] Professional tone (LinkedIn audience expects quality)
- [ ] CTA at end of video

### Message Ads (InMail)
- [ ] Subject line: < 60 chars, personalized if possible
- [ ] Message body: < 500 words (shorter = better)
- [ ] Personalization tokens: %FIRSTNAME%, %JOBTITLE%, %COMPANYNAME%
- [ ] Single CTA button (not 3 links in the body)
- [ ] Sender: real person (not company page — personal messages get 2x open rate)
- [ ] Frequency: max 1 message per 45 days to same user (LinkedIn-enforced)

### Text Ads
- [ ] Headline: 25 chars
- [ ] Description: 75 chars
- [ ] Image: 100x100px (logo or headshot)
- [ ] Low cost but low volume — good for ABM or retargeting supplement

---

## Compliance

- [ ] LinkedIn Ads Policy reviewed (`harness/references/linkedin-ads-rules.md`)
- [ ] Professional context maintained (LinkedIn audience expects professional tone)
- [ ] B2B claim substantiation available (if making specific claims)
- [ ] No direct competitor disparagement
- [ ] FTC disclosure if endorsement or testimonial
- [ ] GDPR consent addressed (for EU targeting)

---

## Pre-Launch Final Checks

- [ ] All ads reviewed for spelling, grammar, and professionalism
- [ ] Landing page URLs correct and tracking (UTMs set)
- [ ] Conversion tracking verified (test submission)
- [ ] Budget and schedule confirmed
- [ ] Audience targeting reviewed (not too broad, not too narrow)
- [ ] A/B variants created (2-4 ad variants per campaign minimum)
- [ ] Lead form tested (submit test lead, verify CRM receives it)
- [ ] Campaign preview reviewed on mobile and desktop

---

## Post-Launch

### Day 1-3
- [ ] Ads approved and serving
- [ ] Impressions and clicks appearing in dashboard
- [ ] Lead form submissions flowing to CRM (if using lead gen forms)
- [ ] Landing page conversions tracking (if using website conversions)

### Week 1
- [ ] CTR reviewed (benchmark: 0.4-0.7% for sponsored content)
- [ ] CPC reviewed (benchmark: $5-12 for B2B)
- [ ] Cost per lead reviewed (benchmark: $50-200 for B2B)
- [ ] Underperforming ads paused (CTR < 0.3% after 5K impressions)
- [ ] Audience demographics reviewed (are we reaching the right people?)

### Week 2-4
- [ ] Lead quality assessed (are leads converting to meetings/opportunities?)
- [ ] Budget reallocation to top performers
- [ ] New creative variants tested
- [ ] Audience expansion tested (if core audience is working)
- [ ] Retargeting campaigns launched for website visitors

---

## LinkedIn-Specific Benchmarks

| Metric | Sponsored Content | Message Ads | Lead Gen Forms |
|--------|------------------|-------------|---------------|
| CTR | 0.4-0.7% | N/A | N/A |
| Open rate | N/A | 30-55% | N/A |
| Click rate | N/A | 3-5% | N/A |
| Form fill rate | N/A | N/A | 10-15% |
| CPC | $5-12 | N/A | N/A |
| Cost per open | N/A | $0.50-1.50 | N/A |
| Cost per lead | $50-200 | $25-75 | $30-100 |
| Conversion rate | 2-5% | 1-3% | 10-15% |

### Why LinkedIn Ads Are Expensive (and Why It's Worth It)
- LinkedIn CPMs are 5-10x Meta's
- BUT: you're reaching verified decision-makers by job title and company
- A $100 LinkedIn lead = a VP at a target company vs a $10 Meta lead = unknown quality
- For B2B with high ACV ($5K+), LinkedIn often has the best ROI despite high CPL

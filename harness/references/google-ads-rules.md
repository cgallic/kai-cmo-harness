# Google Ads — Harness Rules

## Ad Copy Constraints (enforced by gate)

### Search Ads (RSA)
- Headlines: 3–15 headlines, max 30 chars each (including spaces)
- Descriptions: 2–4 descriptions, max 90 chars each
- Every headline must be independently useful (Google rotates)
- Pin headline 1 only when essential — pinning kills optimization
- Include target keyword in at least 2 headlines (exact or close variant)
- Include a number or stat in at least 1 headline ("67% less than competitors", "$69/mo")
- Power words for CTR: Free, Now, Today, Guaranteed, Proven, [City], [Year]
- Descriptions: lead with benefit, end with CTA

### Performance Max (PMax)
- Headlines: up to 15 (same 30-char limit)
- Long headlines: up to 5, max 90 chars
- Descriptions: up to 5, max 90 chars
- Image assets: provide 3:4, 1:1, and 1.91:1 ratios
- Video assets: 10s, 15s, 30s versions if possible
- Call to action: match intent (Book Now, Get Quote, Start Free Trial, Learn More)

### Display / Demand Gen
- Headline: max 30 chars
- Long headline: max 90 chars
- Description: max 90 chars
- Logo + images required

## Quality Gates for Ads

Four U's scoring adapted for ad context:
- **Unique**: headline says something competitors in the SERP don't
- **Useful**: benefit is explicit — not "AI answering" but "Never miss a client call"
- **Ultra-specific**: number, price, timeframe, or outcome in at least 1 headline
- **Urgent**: CTA with action verb + time signal ("Book a free demo today")

Minimum pass: all 4 dimensions ≥ 2, total ≥ 10/16 (lower bar than content — format is shorter)

## Banned Patterns (Google Ads specific)
- Superlatives without proof ("Best in class", "#1 solution") — Google may disapprove
- All caps except abbreviations (HIPAA, CRM)
- Clickbait that doesn't match landing page
- Generic CTAs with no action ("Click here", "Learn more" alone)
- Repeating the keyword 3+ times across one ad group

## Output Format

For each ad set, output:
```
CAMPAIGN: [campaign name]
AD GROUP: [ad group name]
TARGET KEYWORD: [keyword + match type]

RSA HEADLINES (label each: [H1]-[H15]):
H1: [30 chars max]
H2: [30 chars max]
...

DESCRIPTIONS:
D1: [90 chars max]
D2: [90 chars max]

FINAL URL: [landing page]
DISPLAY PATH: domain.com/[path1]/[path2]
```

## Bidding Notes
- New campaigns: start with Maximize Clicks (200+ clicks before switching)
- Established: Target CPA or Target ROAS once 30+ conversions/30 days
- Smart Bidding needs conversion tracking set up first — confirm before writing

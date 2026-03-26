---
name: kai-launch
description: Plan and produce a complete product launch marketing package — landing page copy, email sequences, ad campaigns, press release, social posts, and launch timeline. Orchestrates all other kai skills into a coordinated launch. Use when "product launch", "launch campaign", "go-to-market", "GTM plan", "launch marketing", "we're launching", "prepare launch materials", or any request to coordinate marketing for a new product, feature, or major update.
---

Orchestrate a complete product launch — coordinates emails, ads, content, PR, and social into a unified campaign with a timeline.

## Phase 1: Launch Discovery

Ask the user:

1. **What's launching?** (new product, feature, major update, rebrand)
2. **Launch date** — when does it go live?
3. **Audience** — who are we targeting? (existing users, new market, both?)
4. **Channels available** — email list size, ad budget, social following, press contacts?
5. **Offer/hook** — any launch pricing, early access, beta invite?
6. **Landing page** — exists or needs to be created?
7. **Competitor landscape** — who else does this? What's our differentiation?

## Phase 2: Launch Timeline

Generate `workspace/launch/_timeline.md`.

### Standard Launch Phases

| Phase | Timing | Activities |
|-------|--------|------------|
| **Pre-launch** | T-14 to T-7 | Teaser emails, waitlist, social hints, internal prep |
| **Warm-up** | T-7 to T-1 | Blog post(s), detailed previews, influencer/press outreach |
| **Launch Day** | T-0 | Announcement email, ad campaigns go live, press release, social blitz |
| **Post-launch** | T+1 to T+14 | Nurture sequence, retargeting ads, case study collection, performance review |
| **Sustain** | T+14 to T+30 | Content marketing, SEO articles, ongoing ads optimization |

### Asset Checklist

| Asset | Channel | Phase | Status |
|-------|---------|-------|--------|
| Landing page copy | Web | Pre-launch | Needed |
| Teaser email (1-2) | Loops | Pre-launch | Needed |
| Announcement email | Loops | Launch day | Needed |
| Follow-up email sequence (3-5) | Loops | Post-launch | Needed |
| Meta ads — TOF (3 variants) | Meta | Launch day | Needed |
| Meta ads — retarget (3 variants) | Meta | Post-launch | Needed |
| Google ads — brand (RSA) | Google | Launch day | Needed |
| Google ads — non-brand (RSA) | Google | Launch day | Needed |
| Blog post — announcement | Blog | Warm-up | Needed |
| Blog post — deep dive | Blog | Post-launch | Needed |
| LinkedIn article | LinkedIn | Launch day | Needed |
| Press release | PR | Launch day | Needed |
| Social posts (5-10) | Social | All phases | Needed |

Adapt to the actual launch. Remove assets for channels the user doesn't have.

### Approval Gate

Present the timeline and asset checklist. Confirm before producing anything.

## Phase 3: Batch Production

Produce assets in dependency order:

### Order of Operations

1. **Landing page copy** — defines the core messaging everyone else references
2. **Press release** — crystallizes the announcement narrative
3. **Blog posts** — expand on the story
4. **Email sequences** — use `/kai-email-system` workflow for the launch email set
5. **Ad campaigns** — use `/kai-ad-campaign` workflow for the ad set
6. **Social posts** — extract key lines from above assets
7. **LinkedIn article** — repurpose blog post for LinkedIn format

### Per-Asset Production

Each asset follows the standard harness pipeline:

1. Load the right framework from `E:\Dev2\kai-cmo-harness-work\knowledge/`
2. Load the skill contract from `harness/skill-contracts/`
3. Load platform policy (for ads) from `harness/references/`
4. Write against the framework + persona
5. Run quality gates
6. Max 2 retries per asset

### Messaging Consistency

All assets must use the same:
- **Core value proposition** (defined in landing page copy)
- **Key stats/proof points** (consistent across all channels)
- **CTA** (same destination — landing page or signup)
- **Persona hooks** (same pain points, same language)

Extract these from the landing page copy and use as a reference for all subsequent assets.

### Batch Output

```
workspace/launch/
├── _timeline.md
├── _messaging-guide.md          # Core VP, stats, CTA, extracted from landing page
├── landing-page/
│   └── copy.md
├── emails/
│   ├── teaser-1.md
│   ├── teaser-2.md
│   ├── announcement.md
│   ├── follow-up-1.md
│   └── follow-up-2.md
├── ads/
│   ├── meta/
│   └── google/
├── blog/
│   ├── announcement.md
│   └── deep-dive.md
├── pr/
│   └── press-release.md
├── social/
│   ├── launch-day-posts.md
│   └── sustain-posts.md
├── linkedin/
│   └── article.md
└── _quality-report.md
```

## Phase 4: Quality Report

```markdown
# Launch Campaign Quality Report

## Summary
- Total assets: [N]
- Passed all gates: [N]
- Channels covered: [list]
- Messaging consistency: [PASS/FAIL — same VP across all assets?]

## Per-Asset Results
| Asset | Channel | Four U's | Banned | Policy | Status |
|-------|---------|----------|--------|--------|--------|

## Launch Readiness
- [ ] Landing page copy approved
- [ ] Email sequences loaded in Loops
- [ ] Ad campaigns ready to activate
- [ ] Press release ready to distribute
- [ ] Blog posts scheduled
- [ ] Social posts queued
```

## Phase 5: Post-Launch Monitoring Plan

Generate `workspace/launch/_monitoring.md`:
- Day 1, 3, 7, 14 check-in schedule
- Metrics to watch per channel (email open rates, ad CTR, landing page conversion)
- When to adjust (kill underperforming ads, boost winners)
- Content to produce based on early results (FAQ post, case study, feature tutorial)

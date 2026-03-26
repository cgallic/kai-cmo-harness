---
name: kai-ad-campaign
description: Plan and produce a full paid ad campaign across platforms (Meta, Google, LinkedIn, TikTok, Microsoft, Pinterest, Snapchat, Amazon, X). Maps funnel stages (TOF/MOF/BOF), produces ad variants per platform with policy compliance, outputs ready-to-upload copy. Use when "ad campaign", "create ads", "run ads for", "paid campaign", "media plan", "launch ads", "Meta campaign", "Google Ads campaign", "multi-platform ads", or any request to systematically produce advertising across platforms and funnel stages.
---

Plan and batch-produce a complete ad campaign across platforms and funnel stages. Every ad passes platform policy compliance + quality gates.

## Phase 1: Campaign Discovery

Ask the user (or read project files):

1. **Product/offer** — what are we advertising?
2. **Platforms** — which platforms? (Meta, Google, LinkedIn, TikTok, etc.)
3. **Budget range** — affects platform mix and bid strategy recommendations
4. **Goal** — leads, conversions, traffic, awareness, app installs?
5. **Audience** — who are we targeting? (map to harness persona if applicable)
6. **Landing page** — where do ads send traffic?
7. **Existing assets** — any images/video already available?

## Phase 2: Campaign Architecture

Generate `workspace/ads/_campaign-map.md` with:

### Funnel Structure

| Stage | Objective | Audience | Platforms | Ad Count |
|-------|-----------|----------|-----------|----------|
| **TOF (Awareness)** | Reach/awareness | Cold — lookalikes, interest-based | Meta, TikTok, Google Display | 3 variants each |
| **MOF (Consideration)** | Traffic/engagement | Warm — site visitors, engagers | Meta, Google Search, LinkedIn | 3 variants each |
| **BOF (Conversion)** | Leads/sales | Hot — cart abandoners, demo requesters | Meta retarget, Google Search (brand), Email | 3 variants each |

Adapt to the actual product and platforms. Not every product needs every stage.

### Per-Platform Ad Specs

Before writing any ad, load the platform's policy reference and skill contract:

| Platform | Policy Reference | Contract | Key Constraints |
|----------|-----------------|----------|-----------------|
| Meta | `harness/references/meta-ads-rules.md` | `harness/skill-contracts/meta-ads.yaml` | Headline 27 chars, primary text 125 chars visible |
| Google | `harness/references/google-ads-policy-reference.md` | `harness/skill-contracts/google-ads.yaml` | 15 headlines (30 chars), 4 descriptions (90 chars) |
| LinkedIn | `harness/references/linkedin-ads-rules.md` | — | Professional context, B2B claim substantiation |
| TikTok | `harness/references/tiktok-ads-policy-reference.md` | — | No political ads, AI disclosure required |
| Microsoft | `harness/references/microsoft-ads-rules.md` | — | Similar to Google RSA format |
| Pinterest | `harness/references/pinterest-ads-rules.md` | — | All weight loss banned, strict body image |
| Snapchat | `harness/references/snapchat-ads-policy-reference.md` | — | Young audience protections |
| Amazon | `harness/references/amazon-ads-policy-reference.md` | — | 18-month claim evidence rule |
| X/Twitter | `harness/references/x-ads-policy-reference.md` | — | Verification tier affects access |

All paths relative to `E:\Dev2\kai-cmo-harness-work\`.

Also load: `harness/references/advertising-compliance.md` for FTC/GDPR/CAN-SPAM requirements that apply to ALL platforms.

### Approval Gate

Present the campaign map to the user before producing ads. Confirm:
- Platform selection
- Funnel stages
- Number of variants per stage
- Any compliance concerns (regulated industry?)

## Phase 3: Batch Production

Produce ads by platform and funnel stage. For each ad:

### Output Format

```markdown
# [Platform] — [Funnel Stage] — Variant [A/B/C]

**Platform:** Meta / Google / LinkedIn / etc.
**Funnel stage:** TOF / MOF / BOF
**Objective:** [campaign objective]
**Audience:** [target description]

## Ad Copy

### Headlines
[Per platform specs — e.g., 15 headlines for Google RSA, 1 for Meta]

### Primary Text / Description
[Per platform specs]

### CTA
[Button text or action]

### Display URL / Path
[If applicable]

## Hook Type
[pattern_interrupt | social_proof | pain_agitate | direct_offer | story]

## Quality Gate Results
- Four U's: [X]/16 (min 10)
- Banned words: PASS/FAIL
- Platform char limits: PASS/FAIL
- Has number/stat: PASS/FAIL
- Policy compliance: PASS/FAIL
```

### Quality Gates (per ad)

1. **Four U's >= 10/16**
2. **Zero banned words** and **zero AI slop**
3. **Platform character limits** respected (headlines, descriptions, primary text)
4. **Has specific number or stat** anchoring the claim
5. **Platform policy compliance** — no violations from the loaded policy reference
6. **No superlatives without proof** (Google requirement, good practice everywhere)
7. **Single clear CTA** per ad

### Hook Variety

Across the 3 variants per stage, use different hook types:
- Variant A: Pain/agitate
- Variant B: Social proof or stat-led
- Variant C: Pattern interrupt or story

### Batch Output

```
workspace/ads/
├── _campaign-map.md
├── meta/
│   ├── tof-variant-a.md
│   ├── tof-variant-b.md
│   ├── tof-variant-c.md
│   ├── mof-variant-a.md
│   └── bof-variant-a.md
├── google/
│   ├── search-rsa-branded.md
│   ├── search-rsa-nonbranded.md
│   └── pmax-assets.md
├── linkedin/
│   └── ...
└── _quality-report.md
```

## Phase 4: Quality Report

Generate `workspace/ads/_quality-report.md`:

```markdown
# Ad Campaign Quality Report

## Summary
- Total ads: [N]
- Platforms: [list]
- Passed all gates: [N]
- Policy flags: [N]

## Per-Ad Results
| Ad | Platform | Stage | Four U's | Char Limits | Policy | Status |
|----|----------|-------|----------|-------------|--------|--------|

## Policy Flags
[Any ads that need legal review or have borderline claims]

## A/B Test Recommendations
[Which variants to test first based on hook type diversity]
```

## Phase 5: Platform Setup Notes

Generate `workspace/ads/_platform-setup.md` with:
- Campaign structure per platform (campaigns, ad sets, ad groups)
- Audience targeting recommendations
- Budget allocation across platforms and stages
- Bid strategy recommendations
- Tracking/UTM parameter conventions

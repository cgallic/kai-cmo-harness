---
issue: 4
title: "Add paid media launch playbook to knowledge base"
state: OPEN
labels: [documentation, enhancement]
assignees: []
created: 2026-04-03T00:21:54Z
updated: 2026-04-03T00:21:54Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/4
comments_count: 0
reactions_count: 0
---

# #4: Add paid media launch playbook to knowledge base

## Description

## Summary

Added comprehensive paid media launch framework based on real-world DTC brand launch.

## What was added

**File:** `knowledge/playbooks/paid-media-launch-playbook.md`

**Content:**
- Complete framework for launching paid ads for new brands (Meta + Google)
- Budget formula: Target CPA × 50 = minimum budget to exit learning
- Infrastructure-first approach (measurement before spending)
- Campaign structure templates (1 campaign per product, not generic broad)
- AI creative generation workflow (with brand control)
- Claude automation for bulk operations

## Source

Brandon's TikTok breakdown of belly MD launch (IBS supplement brand, 3 products, ~$60 price point)

## Key frameworks

1. **Budget Formula:** `Target CPA × 50 = Minimum Budget`
   - Most failed campaigns are underfunded, not bad creative
   - Example: $40 CPA × 50 conversions = $2,000 minimum

2. **Infrastructure Before Spending:**
   - Triple Whale (MTA)
   - Reverse ETL (better tracking)
   - Post-purchase surveys (qualitative data)

3. **Campaign Structure:**
   - Meta: 1 campaign per product (broad), 1 DPA retargeting
   - Google: Non-branded search (1 per product) + branded + shopping
   - NO Performance Max initially (black box, need baseline data first)

4. **Creative Process:**
   - AI generates variations (Claude/GPT)
   - Client remakes in brand voice
   - Bulk upload via Marketfeed (Meta) or Google Ads Editor

5. **Automation:**
   - Claude project per client
   - Generates bulk upload sheets
   - Makes 1 person as productive as 5

## Integration opportunity

Should integrate with `/kai-ad-campaign` skill when launching paid media for new brands.

## Related skills

- `/kai-ad-campaign` — Generate ad copy
- `/kai-landing-page` — Build landing pages
- `/kai-cro` — Optimize conversion funnel
- `/kai-analytics` — Set up tracking

## Next steps

- [ ] Update `/kai-ad-campaign` to reference this playbook
- [ ] Consider creating `/kai-paid-launch` skill that implements this full workflow
- [ ] Add to README.md under playbooks section

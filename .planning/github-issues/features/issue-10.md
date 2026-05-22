---
issue: 10
title: "Build local business AI claymation ad pipeline"
state: OPEN
labels: [enhancement]
assignees: []
created: 2026-05-03T10:06:03Z
updated: 2026-05-03T10:10:27Z
author: cgallic
url: https://github.com/cgallic/kai-cmo-harness/issues/10
comments_count: 0
reactions_count: 0
---

# #10: Build local business AI claymation ad pipeline

## Description

## Context
This issue comes from a Reddit screenshot in r/passive_income describing a workflow for selling AI claymation-style ads to local businesses. The core idea is very Kai CMO-shaped: discover local businesses with weak ads, generate a free/at-cost sample creative, use that as the outbound wedge, then upsell recurring creative retainers.

Observed workflow from the screenshot:

- **Niche:** AI claymation ads for local businesses.
- **Storyboard/script:** Claude AI.
- **Image/frame generation:** Fal.ai.
- **Animation:** Kling AI.
- **Voiceover:** ElevenLabs.
- **Editing:** CapCut.
- **Lead discovery:** Google Maps search for gyms, restaurants, salons, med spas, etc.
- **Ad weakness signal:** businesses running weak Facebook/Instagram ads.
- **Offer:** one free or at-cost video.
- **Upsell:** monthly retainers for 2–4 videos/month.
- **Claimed traction:** 4 monthly clients.

## Goal
Turn this into a repeatable Kai CMO pipeline: local lead discovery → weak-ad detection → sample AI claymation ad generation → outbound pitch → retainer fulfillment workflow.

## Proposed work

### 1. Local business lead discovery
- Search Google Maps or equivalent local business sources by niche and geography.
- Prioritize gyms, restaurants, salons, med spas, home services, and other visual/local niches.
- Capture business name, website, phone, email/contact URL, address, category, rating/reviews, and social links.

### 2. Weak-ad and creative opportunity detection
- Check whether the business has Facebook/Instagram presence and active or recent ads where possible.
- Flag weak creative signals: generic stock visuals, no hooks, poor offer clarity, no local specificity, no video, low-quality editing, stale creative, weak CTA.
- Produce a short “why this business is a good target” note for each lead.

### 3. Sample claymation ad generation
- Use Claude to generate:
  - Concept angle
  - Storyboard
  - Short script
  - Shot list
  - Voiceover copy
  - CTA
- Use Fal.ai or equivalent image generation for claymation-style frames.
- Use Kling AI or equivalent for animation.
- Use ElevenLabs for voiceover.
- Produce editing notes or a CapCut-ready assembly plan.

### 4. Outbound pitch package
- Generate a personalized pitch for each business:
  - Compliment/context
  - Specific weak-ad observation
  - Link or mention of sample video
  - Clear retainer offer for 2–4 videos/month
  - Low-friction CTA to reply/book a call
- Include variants for email, SMS, Instagram DM, and cold call opener where relevant.

### 5. Retainer fulfillment workflow
- Define monthly deliverables for 2-video and 4-video packages.
- Track client status: sourced, qualified, sample_created, contacted, replied, booked, closed, fulfilled.
- Create reusable templates for onboarding, content calendar, approvals, revisions, and delivery.

## Expected improvements

- Converts local lead discovery into a concrete creative wedge instead of generic outreach.
- Gives Kai CMO a clear service/productized workflow for local businesses.
- Creates a repeatable path from scraping → sample creative → pitch → recurring revenue.
- Provides a practical demo pipeline for agentized marketing fulfillment.

## Acceptance criteria

- [ ] A documented pipeline exists for discovering local businesses by niche/geography.
- [ ] Leads can be scored for weak-ad/creative opportunity signals.
- [ ] The system can generate a structured claymation ad concept, storyboard, script, shot list, and voiceover copy.
- [ ] The pipeline defines how to hand off frames/animation/voiceover/editing across Claude, Fal.ai, Kling AI, ElevenLabs, and CapCut or equivalents.
- [ ] Personalized outbound copy can be generated from lead + weak-ad analysis + sample creative.
- [ ] Retainer package templates exist for 2–4 videos/month.
- [ ] Lead/client status can be tracked from discovery through fulfillment.
- [ ] The workflow can run in dry-run mode before creating assets, outbound messages, or external side effects.

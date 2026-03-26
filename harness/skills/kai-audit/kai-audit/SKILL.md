---
name: kai-audit
description: Full marketing audit — runs all relevant checklists against your product, site, and marketing in one go. Covers SEO, content, email, ads, social media, CRO, landing pages, technical SEO, and creative production. Produces a "state of your marketing" report with health scores per area and a prioritized fix list. Use when "marketing audit", "full audit", "audit everything", "marketing health check", "what's broken", "state of marketing", or any request to comprehensively assess marketing across all channels.
---

One-click full marketing audit. Runs all relevant harness checklists and produces a health report.

## Phase 0: Load Product Context

Check if `marketing.md` exists in the current working directory.

**If it exists:** Read it — skip product discovery questions. It has the product name, ICP, value prop, monetization, brand voice, current channels, and competitive landscape.

**If it does NOT exist:** Auto-explore the codebase to create it. Do NOT ask the user what the product is. Read CLAUDE.md, README.md, PROJECT.md, package.json, landing pages, and any project files. Search for email/ad/analytics config. Then create `marketing.md` using the template from `/kai-email-system`. Present draft to user for confirmation.

---

## Phase 1: Audit Scope

Read from `marketing.md`. Only ask about things not covered there:

1. **Product/site** — what are we auditing?
2. **URL** — main website
3. **Active channels** — which are you using? (SEO, email, ads, social, content, PR)
4. **Known issues** — anything already flagged?
5. **Depth** — quick (top-line scores, 30 min) or deep (detailed findings, 2-3 hours)?

## Phase 2: Checklist Execution

Run applicable checklists from `E:\Dev2\kai-cmo-harness-work\knowledge\checklists\`. Skip checklists for channels the user isn't using.

### Audit Modules

| Module | Checklist Files | Applies When |
|--------|----------------|-------------|
| **Technical SEO** | `technical-seo-audit-sop.md`, `technical-seo-checklist.md` | Always (if they have a website) |
| **On-Page SEO** | `seo-checklist.md` | Always |
| **Content Quality** | `content-checklist.md`, `content-brief-checklist.md` | If publishing content |
| **Email Marketing** | `email-checklist.md` | If running email |
| **Meta/Facebook Ads** | `meta-advertising-checklist.md` | If running Meta ads |
| **Google Ads** | `google-ads-launch-checklist.md`, `paid-acquisition-checklist.md` | If running Google ads |
| **LinkedIn Ads** | `linkedin-ads-launch-checklist.md` | If running LinkedIn ads |
| **TikTok** | `tiktok-checklist.md` | If on TikTok |
| **Social Media** | `social-media-audit-checklist.md` | If active on social |
| **Landing Pages** | `landing-page-messaging-checklist.md` | If they have landing pages |
| **CRO** | `cro-audit-checklist.md` | Always (for main conversion flow) |
| **Perception/Copy** | `perception-engineering-checklist.md` | For sales-focused pages |
| **Ad Creative** | `creative-production-checklist.md`, `ad-launch-checklist.md` | If running any ads |
| **PR** | `pr-checklist.md` | If doing press/PR |
| **Website Launch** | `website-launch-checklist.md` | If site is new/recently launched |
| **2026 Readiness** | `2026-readiness-checklist.md` | Always |

Load each applicable checklist and evaluate. Use browse/gstack to view the live site if available.

## Phase 3: Health Scores

Score each module 0-100:

| Module | Score | Grade | Top Issue |
|--------|-------|-------|-----------|
| Technical SEO | /100 | A/B/C/D/F | [main issue] |
| On-Page SEO | /100 | | |
| Content | /100 | | |
| Email | /100 | | |
| Paid Ads | /100 | | |
| Social | /100 | | |
| Landing Pages | /100 | | |
| CRO | /100 | | |
| **Overall** | **/100** | | |

Grading: A (90+), B (75-89), C (60-74), D (40-59), F (<40)

## Phase 4: Prioritized Fix List

Aggregate all findings across modules into one prioritized list:

| # | Fix | Module | Impact | Effort | Priority |
|---|-----|--------|--------|--------|----------|
| 1 | [fix] | [module] | High | Low | P0 |
| 2 | [fix] | [module] | High | Medium | P1 |
| ... | ... | ... | ... | ... | ... |

### P0: Fix This Week (high impact, low effort)
### P1: Fix This Month (high impact, medium effort)
### P2: Fix This Quarter (medium impact)
### P3: Backlog (nice to have)

## Phase 5: Recommendations

Map fixes to /kai skills:

| Fix | Skill to Run |
|-----|-------------|
| Landing page copy needs work | `/kai-landing-page` |
| No lifecycle emails | `/kai-email-system` |
| Weak SEO | `/kai-seo-audit` (deep) + `/kai-content-calendar` |
| No social presence | `/kai-social` |
| Ad campaigns need refresh | `/kai-ad-campaign` |
| Not in AI answers | `/kai-surround-sound` |

## Phase 6: Output

```
workspace/marketing-audit/
├── _executive-summary.md        # Health scores + top 5 fixes
├── _detailed-findings.md        # Module-by-module results
├── _prioritized-fixes.md        # Full fix list
├── _skill-recommendations.md    # Which /kai skills to run
└── per-module/
    ├── technical-seo.md
    ├── content.md
    ├── email.md
    ├── ads.md
    ├── social.md
    ├── landing-pages.md
    └── cro.md
```

# How Kai Runs Paid Ads

This page explains the paid media workflow in plain English.

Kai is built for business owners, marketers, agencies, and developers who want a repeatable way to plan, create, check, and improve paid ads from the same workspace where the rest of the business context lives.

Paid ads are still paid ads. Kai does not make Meta, Google, TikTok, LinkedIn, or any other ad auction cheaper.

Kai lowers the work around the ad spend: campaign planning, creative variants, landing page copy, policy checks, quality checks, performance review, and next-step recommendations.

## The Simple Version

Most small teams run into the same paid ads problem.

They need to test offers, hooks, pages, and audiences, but every test needs more writing, creative direction, reporting, and review. That labor gets expensive before the business knows what works.

Kai turns that work into a repeatable system:

1. Read the business.
2. Map the campaign.
3. Draft the ad variants.
4. Check policy and quality.
5. Review performance.
6. Recommend the next test.

Humans still approve budgets, claims, creative, and launch decisions. Kai handles the structured prep and review work that slows teams down.

## Who This Helps

| Reader | What you care about | How Kai helps |
| --- | --- | --- |
| Business owner | "Can this help me get customers without wasting money?" | Kai creates a controlled test plan before spend scales. |
| Marketer | "Can I get more angles, variants, and reports out faster?" | Kai drafts campaign assets and review notes from one brief. |
| Developer | "Is this real software or a prompt pack?" | Kai includes skill contracts, policy references, quality gates, and paid media modules. |
| Agency | "Can I repeat this across clients?" | Kai gives each client repo a reusable marketing workspace. |

## What Exists In This Repo

The paid media workflow is grounded in real files in this repository:

- `/kai-ad-campaign` plans, evaluates, and produces paid campaigns across platforms.
- `/kai-daily-ad-review` pulls ad data and creates performance summaries when credentials are configured.
- `harness/references/` stores policy references for Meta, Google, TikTok, LinkedIn, Microsoft, Pinterest, Snapchat, Amazon, and X.
- `harness/skill-contracts/` defines ad output rules for formats like Meta ads and Google Ads.
- `scripts/quality_gates/` checks banned words, Four U's quality, SEO rules, and publishing standards.
- `kai/paid_media/` contains controls, monitoring, budget safety, readiness checks, and variant logic.

This is not a claim that Kai automatically buys ads profitably. The repo contains a structured operating layer for the work around paid acquisition.

## How The Workflow Runs

### 1. Business Context

Kai starts from the product and market:

- What is being sold
- Who the buyer is
- What the offer is
- Which proof points are allowed
- Which landing page will receive traffic
- Which platform rules apply
- What the budget and goal are

That context can come from `MARKETING.md`, the repo, a user brief, or connected data sources.

### 2. Campaign Map

Kai turns the brief into a campaign structure:

- Platform
- Funnel stage
- Audience
- Objective
- Offer angle
- Number of variants
- Required checks before launch

This prevents the usual blank-page ad workflow where every new campaign starts from scratch.

### 3. Creative Variants

Kai can draft:

- Meta ad copy
- Google search ad copy
- LinkedIn ad copy
- TikTok-style scripts
- Landing page sections
- Retargeting copy
- Follow-up emails
- Creative briefs
- Hook tests

The point is not to publish every draft. The point is to create enough good options for a human to pick, edit, and test.

### 4. Policy And Quality Checks

Before ads go live, Kai checks for:

- Platform policy risk
- Character limits
- Unsupported claims
- Banned words
- Weak or vague copy
- CTA clarity
- Missing proof
- Landing page mismatch

This helps teams catch obvious problems before they spend money sending traffic to them.

### 5. Performance Review

When ad data is available, Kai can review:

- Spend pace
- CTR
- CPC
- Conversion rate
- CPA or CPL
- Frequency
- Landing page behavior
- Search terms
- Creative fatigue
- Budget waste

The output is more than a dashboard. Kai turns the review into action notes: keep, pause, rewrite, split, retarget, or scale.

## Why This Keeps Costs Down

Kai does not lower media prices. It lowers the human workload needed to find useful tests.

| Cost area | Typical workflow | Kai workflow |
| --- | --- | --- |
| Planning | Build a new campaign from scratch | Start from a structured campaign map |
| Copy | Write every first draft manually | Generate variants for review |
| Compliance | Check late or miss issues | Check before launch |
| Reporting | Summarize by hand | Produce structured review notes |
| Learning | Lose insights across docs and chats | Keep campaign context in the workspace |
| Scaling | Guess what deserves more budget | Use test results to pick next moves |

The business still needs a real offer, tracking, budget discipline, and human judgment. Kai makes the operating loop lighter.

## What It Can Support

Kai can support paid acquisition for:

- Ecommerce products
- Subscriptions
- SaaS trials
- Local services
- Lead generation
- Courses and digital products
- Events and launches
- Marketplaces
- B2B demos
- Retargeting campaigns

The workflow is the same: define the buyer, write multiple angles, match the page to the ad, check the work, run the test, read the data, and improve the next batch.

## What To Say In Plain English

Kai is an AI marketing workspace for paid ads. It helps teams plan campaigns, create ad variants, check platform rules, review performance, and decide what to test next. It does not replace ad platforms or human approval. It reduces the manual work around paid acquisition so teams can test more carefully before they scale spend.

## What Not To Claim

Do not claim Kai guarantees ROAS, replaces media buyers, or automatically buys ads profitably.

The grounded claim is simpler: Kai makes paid media work more structured, faster to prepare, easier to review, and easier to repeat.

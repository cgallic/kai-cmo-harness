---
name: kai-growth-hacker
description: 'Build an exhaustive first-growth-hire distribution operating system across B2B and B2C channels: LinkedIn, events, AI outbound, AEO, blogs, long-form writing, YouTube, webinars, X, influencers, AI UGC, organic TikTok, paid social, sponsorships, partnerships, lifecycle, referral, and community. Use when "growth hacker", "first growth hire", "distribution hire", "cover every channel", "channel hacking", "0 to ARR growth system", "growth operator", "growth hacker OS", or any request to fan out channel operators and plug the result into Kai workflows.'
---

# /kai-growth-hacker — First-Hire Distribution OS

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

The package a first growth hire would need on day one: every plausible channel mapped and scored for stage fit, a primary/secondary/exploratory pick with blocked channels named and explained, test cards with kill and graduation rules, a 90-day sprint, approval queues for anything that touches a live system, and routing into the Kai skills that execute each piece.

This skill does not send, publish, scrape, enrich, spend, upload, call, text, or mutate live systems. It creates the local plan, ledgers, briefs, and approval queues needed before live work.

## Done when

Work type `strategy-plan` — floor **E3/C3/O1** (`harness/eco-floors.yaml`, `also_covers: growth-plan`).

- **E3** — a named human approved the exact package, including the primary/secondary/exploratory picks and the blocked list.
- **C3** — customer-facing markdown passes `banned_word_check`, briefs and test cards pass Four U's at their stated thresholds, and someone other than the author read the sprint end to end.
- **O1** — every test card names its metric, its read window, its kill rule, and its owner. A card with no kill rule is not finished.

A package nobody runs is not CLOSED. Its outcome is `plan_adopted` / `first_action_shipped`, read at 30 days.

## Constraints

- **Live-action rule.** Do not send email, send DMs, publish posts, upload ads, change spend, sign creator contracts, scrape or enrich lead lists, call or text prospects, mutate CRM records, or edit live sites without explicit approval and a saved dry-run artifact. `_quality-report.md` lists every blocked live action.
- **`MARKETING.md` first.** Read it from the project root before asking questions. If it does not exist, run `/kai-start` or infer a temporary brief from trusted project files and mark unknowns as `[TODO]`.
- **Know these eight things before building the channel map** — read what `MARKETING.md` already answers, ask only for the rest: business type (B2B, B2C, marketplace, local service, ecommerce, creator, mixed); stage (pre-launch, first revenue, early growth, growth, scale); primary conversion (waitlist, trial, demo, call, purchase, subscription, event registration, partner lead); current channels (active, failed, proven); assets available (product demo, founder voice, customer proof, reviews, UGC, podcast/video, blog, email list, CRM, ad account); budget and time (monthly spend, operator hours, production capacity); regulated or sensitive categories (healthcare, finance, legal, minors, employment, housing, credit, political, personal attributes, consumer data); approval rules (who approves live posts, sends, spend, creator contracts, lead enrichment, CRM updates, public claims).
- **Do not invent benchmarks.** Targets come from first-party history or user-provided goals; otherwise the target is a data gap. `_data-gaps.md` lists missing analytics, source access, proof, budgets, and legal approvals.
- **Policy loads before writing.** `harness/references/advertising-compliance.md` before paid, sponsorship, affiliate, or creator work; `harness/references/social-automation-rules.md` before organic social execution; the platform-specific policy reference before writing any ad or platform-bound post (per-platform table in `.claude/rules/architecture-and-memory.md`).
- **Gates before handoff:**
  ```bash
  python scripts/quality_gates/banned_word_check.py --file <file>        # every customer-facing markdown file
  python scripts/quality_gates/four_us_score.py --file <file>            # 12/16 strategic/content/page work; 10/16 ads/email/outreach
  python scripts/quality_gates/seo_lint.py --file <file>                 # SEO/AEO pages
  python scripts/quality_gates/agent_readiness_lint.py https://<domain>  # before AEO/surround-sound execution
  ```
- **Channel coverage is exhaustive, not selective.** The map covers at minimum, for B2B: LinkedIn organic; LinkedIn articles/newsletters; events and webinars; AI outbound and SDR; ABM; AEO and AI search; blogs and SEO; long-form operator writing; YouTube; X/founder media; B2B influencers and creators; partnerships and co-marketing; newsletter/lifecycle; podcast; community and Reddit; PR and digital publications; paid media and retargeting. For B2C: AI UGC and creative volume; organic TikTok; paid social; B2C influencers and creator commerce; events, pop-ups, and field marketing; sponsorships; email, SMS, and retention loops; referral, affiliate, and community loops; Instagram/Reels, YouTube Shorts, Pinterest, Snapchat and relevant social surfaces; ecommerce SEO, product pages, creator-led landing pages, and offer testing when commerce is in scope.
- **Every channel entry carries:** fit (high / medium / low / blocked), why now (stage and audience reason), inputs needed, execution loop, Kai skills, gates, metrics, kill rule, next test.
- **Every test card carries:** hypothesis, channel, audience, offer or CTA, asset required, distribution action, source tracking, compliance gate, owner, timeline, kill rule, graduation rule, next Kai skill to run.
- Read-only channel research may be split by channel family across parallel workers; final integration stays in the main thread. When subagents are unavailable, the operator queue is still written so a future run can delegate.

## Context

| Need | Load |
|---|---|
| The distribution OS itself — channel operating system, first-hire scope | `knowledge/playbooks/growth-hacker-first-hire-os.md` |
| Which loop the product can actually run | `knowledge/playbooks/growth-loops-applied.md` |
| Demand generation mechanics | `knowledge/playbooks/demand-generation.md` |
| Organic social strategy | `knowledge/playbooks/social-media-strategy.md` |
| Creator, influencer, UGC economics | `knowledge/playbooks/influencer-marketing.md` |
| Events and webinars | `knowledge/playbooks/event-webinar-marketing.md` |
| Paid launch structure | `knowledge/playbooks/paid-media-launch-playbook.md` |
| Turning one asset into many | `knowledge/playbooks/content-repurposing.md` |
| Read windows, tracking, attribution | `knowledge/playbooks/analytics-attribution.md` |
| AEO when AI search is in scope | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` |
| Automation limits for organic social | `harness/references/social-automation-rules.md` |
| Law for paid, sponsorship, affiliate, creator work | `harness/references/advertising-compliance.md` |
| Per-platform ad policy references | `.claude/rules/architecture-and-memory.md` |
| Product, ICP, voice, current channels | `MARKETING.md` (project root) |

**Prioritization scorecard** — score every channel 1-5 on each dimension, then pick a primary (best near-term growth bet), a secondary (supports the primary or carries independent signal), an exploratory (cheap, high-upside learning), and a blocked list (delayed because source access, compliance, offer, or tracking is not ready):

| Dimension | Question |
|---|---|
| Audience density | Does the ICP gather here often enough to matter? |
| Message fit | Can the channel carry the proof, offer, and story? |
| Speed to signal | Can we learn within the sprint window? |
| Cost to test | Can we test without large sunk cost or fragile setup? |
| Compounding value | Does output become an owned asset, list, source, or loop? |
| Compliance risk | Can we run this without policy, consent, or data risk? |
| Operator advantage | Do we have unusual taste, data, access, or speed here? |

**Operator ledger** — the package is written as if these roles own it, whether or not subagents exist:

| Operator | Responsibility | Output |
|---|---|---|
| Growth Lead | Owns channel thesis and scorecard | `_90-day-sprint.md` |
| Evidence Scout | Finds proof and source gaps | `_evidence-ledger.md`, `_data-gaps.md` |
| B2B Channel Operator | Writes B2B test cards | `_b2b-channel-tests.md` |
| B2C Channel Operator | Writes B2C test cards | `_b2c-channel-tests.md` |
| Content Engine | Turns winning ideas into content assets | `_asset-backlog.md` |
| Creator/Partner Manager | Builds creator, partner, and sponsor queue | `_creator-partner-shortlist.md` |
| Outbound/SDR Operator | Builds source, suppression, and approval plan | `_outbound-approval-plan.md` |
| Paid Media Operator | Builds creative ledger and paid test notes | `_creative-ledger.md` |
| Analytics Operator | Defines dashboard and read windows | `_metrics-dashboard.md` |
| Compliance Reviewer | Blocks unsafe assets/actions | `_quality-report.md` |

**90-day cadence:**

| Window | Work |
|---|---|
| Days 1-10 | Inventory, evidence, channel map, scorecard, tracking gaps |
| Days 11-30 | Build test assets, approval queues, landing/follow-up path, first test batch |
| Days 31-60 | Read results, kill weak tests, improve strongest path, repurpose winners |
| Days 61-90 | Graduate one repeatable channel, write runbook, set budget and owner cadence |

**Output** — the complete package goes to `workspace/growth-hacker/`: `_brief.md`, `_channel-map.md`, `_prioritization-scorecard.md`, `_90-day-sprint.md`, `_agent-fanout-plan.md`, `_b2b-channel-tests.md`, `_b2c-channel-tests.md`, `_asset-backlog.md`, `_creative-ledger.md`, `_outbound-approval-plan.md`, `_creator-partner-shortlist.md`, `_metrics-dashboard.md`, `_decision-log.md`, `_data-sources.md`, `_data-gaps.md`, `_quality-report.md`. Report the package path, the three picks, the blocked channels and why, the specialist skills to run next, and gates run versus gates still required.

**Specialist routing** — the package plans; these execute:

| Need | Skill |
|---|---|
| Stage diagnosis | `/kai-growth-plan` |
| LinkedIn, X, TikTok, YouTube, Instagram posts | `/kai-social` |
| Blog, long-form, SEO, or article draft | `/kai-write`, `/kai-content-calendar`, `/kai-topical-map` |
| AEO and AI-search visibility | `/kai-surround-sound`, `/kai-seo-audit` |
| Outbound or account workflow | `/kai-sdr-operator`, `/kai-cold-outreach` |
| Creator, influencer, UGC | `/kai-influencer` |
| Paid social and retargeting | `/kai-ad-campaign`, `/kai-retarget`, `/kai-daily-ad-review` |
| Webinar or event | `/kai-webinar`, `/kai-launch` |
| Partnership, sponsorship, affiliate | `/kai-partnership`, `/kai-influencer` |
| Email, SMS, lifecycle, retention | `/kai-email-system`, `/kai-newsletter`, `/kai-retention` |
| Measurement | `/kai-analytics`, `/kai-data-dashboard` |
| Gate review | `/kai-gate` |

## Escalate when

- Approval rules are undefined — nobody named can approve live posts, sends, spend, or contracts.
- The business sits in a regulated or sensitive category and the obvious channel pick carries policy, consent, or data risk.
- The plan would require spend, enrichment, or creator contracts the user has not authorized.
- Tracking is absent, so no test card can name a metric with a real source.
- Stated stage conflicts with the numbers, or the primary conversion cannot be identified.
- A channel the user insists on scores as blocked for compliance rather than for fit.

# Kai Expert Rewrite Program - 2026-05-16

## Purpose

This is the planning artifact for a repo-wide maturity rewrite of Kai CMO Harness. The goal is not to polish wording. The goal is to replace thin, overconfident, outdated, or amateur operating surfaces with expert-grade doctrine, current research, source-backed claims, and eval-ready contracts.

The key finding from the repo audit and field research is simple:

Kai should move from static playbooks and "be a specialist" prompts to evidence loops: collect signal, form a hypothesis, produce or recommend, measure, update memory, and gate every claim.

## Scope

Included:

- `AGENTS.md`, `CLAUDE.md`, root `SKILL.md`
- `docs/prompts/*` and prompt-like docs
- `agent/llm/prompts.py`
- `scripts/quality/prompts.py`
- `scripts/ads/autoreason/prompts/*`
- `scripts/quality/tests/fixtures/*`
- `harness/skill-contracts/*`
- `harness/skills/*`
- `harness/references/*`
- `knowledge/frameworks/*`
- `knowledge/channels/*`
- `knowledge/checklists/*`
- `knowledge/playbooks/*`
- `knowledge/personas/*`

Excluded for this planning pass:

- Generated worktree copies under `.claude/worktrees`
- `node_modules`, build artifacts, static generated output
- Large implementation rewrites in `kai/`, `gateway/`, and `app-meetkai` until the doctrine and eval plan are approved

## Repo Surfaces Found

Prompt/eval/situation surfaces found:

- `docs/prompts`
- `docs/competitive-review-prompt.md`
- `docs/icp-evaluation-prompt.md`
- `docs/next-phase-prompt.md`
- `agent/llm/prompts.py`
- `scripts/quality/prompts.py`
- `scripts/ads/autoreason/prompts`
- `scripts/knowledge_cloner/prompts.py`
- `scripts/reddit_monitor/profiles/*.prompt.md`
- `scripts/quality/tests/fixtures`

Missing:

- No first-class `evals/`, `evaluations/`, `situations/`, or `scenarios/` directory.
- No repo-wide golden situation suite.
- No explicit prompt versioning doctrine.
- No consistent separation between deterministic gates, LLM judges, and human review.

## Highest-Risk Findings

### P0 - Reputation, Compliance, And Trust Risk

These should be rewritten before any public distribution push.

| Surface | Problem | Rewrite Lens |
|---|---|---|
| `knowledge/playbooks/surround-sound-llm-manipulation.md` | Contains high-risk manipulation guidance such as temporary EMDs, bought aged Reddit accounts, and separate Search Console accounts. | White-hat entity strategy, earned digital PR, disclosure, platform ToS, legal review. |
| `knowledge/frameworks/aeo-ai-search/llm-citation-tracking.md` | Recommends coordinated forum seeding and cross-linking that can read as astroturfing. | Legitimate community participation, source-quality evaluation, earned citations, disclosure-safe PR. |
| `knowledge/frameworks/aeo-ai-search/hidden-aeo-edges.md` | Frames "mechanical exploits" as a strategy. | Technical SEO plus search policy and brand-safety review. |
| `harness/references/advertising-compliance.md` | Contains outdated Click-to-Cancel and TCPA one-to-one consent status. | Subscription-law and lead-gen compliance update with court-status notes. |
| `AGENTS.md` KaiCalls mandate | Biases audits toward a product recommendation without fit, alternatives, or conflict handling. | Governance rewrite: fit criteria, disqualifiers, alternatives, disclosure language. |

### P1 - Overconfident Or Under-Sourced AI Search Claims

| Surface | Problem | Rewrite Lens |
|---|---|---|
| `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` | Claims like "#1 ranking factor" and expected citation lift without evidence grading. | Google AI Search guide, Bing AI search guidance, academic GEO, measurement uncertainty. |
| `knowledge/frameworks/aeo-ai-search/aeo-ai-search-strategies-2026.md` | Placeholder citations and generated-report residue. | Technical editor plus source verifier. |
| `knowledge/frameworks/aeo-ai-search/query-fan-out-guide.md` | Blends official claims, reverse engineering, and inference without confidence labels. | Evidence ladder and testable hypotheses. |
| `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md` | Treats `llms.txt` like an enforced standard. | Web standards and crawler policy distinction: proposal vs observed behavior vs official docs. |
| `harness/skills/kai-topical-map/SKILL.md` | Embeds quantitative AI-referral and Wikidata claims without provenance. | Source-backed execution skill with missing-data behavior. |

### P2 - Thin Contracts And Amateur Prompting

| Surface | Problem | Rewrite Lens |
|---|---|---|
| `docs/prompts/2026-03-17-product-eval-prompt.md` | Broad consultant questions, no rubric, no scoring, no falsification tests. | Product diligence and eval design. |
| `agent/llm/prompts.py` | Generic role prompting such as "You are a marketing analytics assistant." | Domain-specific operating prompts with evidence requirements and output contracts. |
| `scripts/quality/prompts.py` | Four U judge lacks calibration examples, confidence, edge cases, and source-grounding. | LLM eval engineering. |
| `scripts/quality/tests/fixtures/perfect.md` | "Perfect" fixture appears to reward fake specificity and unsupported future claims. | Fact-checking fixture rewrite. |
| `scripts/ads/autoreason/prompts/judge.md` | Borda ranking based mostly on "stop scrolling and click." | Creative strategy, experimentation science, offer-market fit, policy risk. |
| `scripts/ads/autoreason/prompts/author.md` | Encourages novelty without concept taxonomy or proof hierarchy. | Paid social copy chief. |
| `harness/skill-contracts/tiktok.yaml` | 15-line contract for a complex channel. | TikTok Shop, creator commerce, policy, edit specs. |
| `harness/skill-contracts/press-release.yaml` | 14-line contract, missing newsworthiness and approvals. | Senior PR/comms director. |
| `harness/skill-contracts/gbp-post.yaml` | Too generic for Google Business Profile. | Local SEO/GBP specialist. |

### P3 - Outdated Or Junior Channel Playbooks

| Surface | Problem | Rewrite Lens |
|---|---|---|
| `knowledge/playbooks/analytics-attribution.md` | References Google Optimize as free A/B testing despite 2023 sunset. | Modern experimentation and incrementality stack. |
| `knowledge/checklists/cro-audit-checklist.md` | Uses FID instead of INP. | Current Core Web Vitals and real-device funnel telemetry. |
| `knowledge/playbooks/paid-media-launch-playbook.md` | Rigid PMax guidance. | Account-state decision tree and experimentation design. |
| `knowledge/playbooks/retargeting-remarketing.md` | Old pixel/lookalike/frequency-cap model. | Privacy-safe lifecycle remarketing, CAPI, enhanced conversions, suppression, holdouts. |
| `knowledge/channels/email-lifecycle.md` and `knowledge/checklists/email-checklist.md` | Missing modern deliverability requirements. | Gmail/Yahoo bulk sender rules, RFC 8058, DMARC alignment, complaint thresholds. |
| `knowledge/playbooks/brand-positioning.md` | Generic positioning and unsupported proof claims. | April Dunford, category alternatives, proof inventory, customer-language mining. |
| `knowledge/playbooks/conversion-rate-optimization.md` | Benchmark-heavy without evidence labels. | Evidence-led CRO, quantitative and qualitative research, experiment design. |
| `knowledge/playbooks/influencer-marketing.md` | 2020-era creator tier table. | Creator commerce, usage rights, whitelisting, Spark/Partnership ads, affiliate GMV. |
| `knowledge/channels/affiliate-referral.md` | Cookie/last-click default is stale. | Server-to-server tracking, coupon leakage, incrementality, fraud scoring. |
| `knowledge/channels/tiktok-shop.md` | Thin on operations. | Shop score, samples, commission ladders, fulfillment, live commerce, violations. |
| `knowledge/playbooks/technical-marketing-tracking.md` | Consent guidance too simplified. | CMP event states, GPC/UOOM, consent logs, server-side tagging governance. |
| `harness/references/posthog-marketing-queries.md` | Attribution queries are too simple. | Identity stitching, cohort windows, revenue joins, assisted conversion models. |
| `knowledge/checklists/2026-readiness-checklist.md` | Buzzwordy and under-defined. | Maturity model with "use when," cost/risk, proof required. |

## Expert Lenses To Wire In

### AI Search, SEO, And Agent Readiness

Primary sources and people:

- Google Search Central AI optimization guide, published 2026-05-15: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google helpful content and AI content guidance: https://developers.google.com/search/docs/fundamentals/creating-helpful-content and https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
- Microsoft Bing AI search optimization, Krishna Madhavan: https://about.ads.microsoft.com/en/blog/post/october-2025/optimizing-your-content-for-inclusion-in-ai-search-answers
- Bing Webmaster Tools AI Performance preview: https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview
- OpenAI crawler docs: https://developers.openai.com/api/docs/bots
- Anthropic crawler docs: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity robots docs: https://www.perplexity.ai/help-center/en/articles/10354969-how-does-perplexity-follow-robots-txt
- web.dev agent-friendly sites: https://web.dev/articles/ai-agent-site-ux
- GEO academic paper: https://arxiv.org/abs/2311.09735
- Aleyda Solis / SEOFOMO AI search optimization survey: https://hub.seofomo.co/surveys/state-ai-search-optimization/
- Lily Ray: expert-led content, E-E-A-T, original research.
- Mike King / iPullRank: query fan-out, semantic relevance, AI visibility measurement.
- Jason Barnard / Kalicube: entity home, knowledge graph, Organization schema.

Doctrine to import:

- Google AI visibility starts with normal Search fundamentals: crawlable, indexable, snippet-eligible, helpful, non-commodity content.
- `llms.txt` can be useful for cooperative agents, but it is not a Google AI Overview ranking requirement.
- Separate training bots from retrieval/search/user-action bots.
- AI visibility is sampled and volatile. Report confidence and methodology, not single-run certainty.
- Replace "AI search hacks" with three layers: eligibility, retrievable passages/entities, ecosystem citations.

### Paid Media, Creative, And Creator Commerce

Primary sources and people:

- Meta Engineering on Andromeda: https://engineering.fb.com/2024/12/02/production-engineering/meta-andromeda-advantage-automation-next-gen-personalized-ads-retrieval-engine/
- Meta Engineering on GEM: https://engineering.fb.com/2025/11/10/ml-applications/metas-generative-ads-model-gem-the-central-brain-accelerating-ads-recommendation-ai-innovation/
- Google Ads AI Max: https://support.google.com/google-ads/answer/15910366
- Google Meridian MMM: https://blog.google/products/ads-commerce/meridian-marketing-mix-model-open-to-everyone/
- Google Ads Safety 2025: https://blog.google/intl/en-au/company-news/outreach-initiatives/ads-safety-report-2025/
- TikTok GMV Max: https://ads.us.tiktok.com/help/article/about-product-gmv-max
- TikTok Shop ads: https://ads.us.tiktok.com/help/article/set-up-tiktok-shopping
- TikTok Symphony: https://newsroom.tiktok.com/tiktok-symphony-updates
- LinkedIn B2B Institute, John Dawes, Steve Kearns: https://business.linkedin.com/advertise/resources/marketing-research
- Edelman and LinkedIn 2025 B2B thought leadership: https://www.edelman.com/expertise/Business-Marketing/2025-b2b-thought-leadership-report
- Kantar, CreativeX, System1 / Orlando Wood, WARC, Analytic Partners, Ehrenberg-Bass.
- IAB Incremental Measurement: https://www.iab.com/guidelines/guidelines-for-incremental-measurement-in-commerce-media/
- FTC Endorsement Guides: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking
- IAB AI Transparency and Disclosure Framework: https://www.iab.com/guidelines/ai-transparency-and-disclosure-framework/

Doctrine to import:

- Creative is now the targeting surface. Platform AI handles more delivery, bidding, placement, and creative assembly.
- Kai's job is brief quality, proof, creative portfolio design, signal quality, causal measurement, rights, disclosure, and learning.
- Separate attributed ROAS from incremental profit.
- Add creative-quality metadata to every ad ledger: human presence, product integration, brand fluency, proof type, offer clarity, novelty, emotional mechanism.
- For TikTok Shop and creator commerce, track creator authorization, usage rights, affiliate disclosure, organic cannibalization, GMV attribution caveats, and SKU-level economics.

### Lifecycle, Cold Outreach, CRO, Brand, Analytics, And Research

Primary sources and people:

- Braze 2026 Customer Engagement Review: https://www.braze.com/press-releases/the-2026-braze-customer-engagement-review-ai-innovation-meets-the-trust-plateau
- Customer.io lifecycle insights: https://customer.io/learn/lifecycle-marketing/2025-lifecycle-insights
- Klaviyo benchmarks: https://www.klaviyo.com/products/email-marketing/benchmarks
- Google sender guidelines: https://support.google.com/a/answer/81126
- Yahoo Sender Hub: https://senders.yahooinc.com/faqs/
- Spamhaus cold email guidance: https://www.spamhaus.org/resource-hub/spam/spamhaus-take-on-cold-emailing-aka-spam/
- FTC CAN-SPAM guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- Gong cold email research, Lavender benchmarks, Gartner B2B buyer research, 6sense buyer experience research.
- Baymard Institute checkout UX: https://baymard.com/blog/current-state-of-checkout-ux
- Contentsquare 2025 digital experience benchmarks: https://contentsquare.com/press/2025-digital-experience-benchmarks/
- CXL conversion research: https://cxl.com/et/conversion-optimization/conversion-research/
- Wynter message testing: https://wynter.com/products/message-testing
- April Dunford for positioning.
- Forrester B2B Buyer Messaging Cycle.
- LinkedIn B2B Institute / Ehrenberg-Bass 95-5 rule.
- Google Meridian MMM and IAB State of Data 2025.
- Maze Future of User Research 2025: https://maze.co/resources/user-research-report-2025/
- User Interviews State of User Research 2025: https://www.userinterviews.com/state-of-user-research
- Teresa Torres and Rob Fitzpatrick's Mom Test: https://www.momtestbook.com/

Doctrine to import:

- Lifecycle email is behavioral-state orchestration, not calendar-delay templates.
- Cold outreach must prove relevance, consent/risk posture, and sender health. Legal does not mean welcome.
- CRO recommendations need evidence tiers: analytics, session replay, user test, message test, funnel benchmark, customer quote.
- Brand and demand gen should include future demand, shortlist presence, buyer trust, distinctiveness, and customer-language mining.
- Analytics should use a measurement ladder: event hygiene, dashboards, cohort/funnel analysis, holdouts/lift, MMM.
- Personas must become research-backed buyer-role/persona hybrids with observed behavior, buying trigger, budget authority, objection, current workaround, and quote evidence.

### Prompt Engineering, Evals, And Agent Runtime

Primary sources and people:

- OpenAI evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
- OpenAI graders: https://platform.openai.com/docs/guides/graders
- OpenAI Model Spec: https://model-spec.openai.com/2025-02-12.html
- OpenAI prompt injection guidance: https://openai.com/safety/prompt-injections/
- OpenAI BrowseComp: https://openai.com/index/browsecomp/
- OpenAI GDPval: https://openai.com/index/gdpval/
- Anthropic building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Anthropic eval guidance: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- Dex Horthy / HumanLayer 12-Factor Agents: https://github.com/humanlayer/12-factor-agents and https://www.humanlayer.dev/blog/12-factor-agents
- METR long-horizon task evaluation: https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/
- tau-bench: https://www.tau-bench.com/
- LangSmith and production eval loops.

Doctrine to import:

- Treat prompts and skill contracts as versioned product code.
- Separate instruction authority, trusted repo context, untrusted web/tool/user content, and generated artifacts.
- Prefer deterministic workflows until dynamic agent behavior is needed.
- Use hybrid graders: deterministic checks for schema/policy/citations/tool arguments, LLM judges for taste/usefulness/comparative quality, human calibration for final rubrics.
- Add situation datasets for every production workflow.

## New Evaluation Spine

Create a first-class evaluation structure:

```text
evals/
  README.md
  situations/
    seo-audit/
    aeo-agent-readiness/
    paid-media-launch/
    ad-creative-judge/
    cold-outreach/
    lifecycle-email/
    cro-audit/
    brand-positioning/
    product-eval/
    prompt-injection/
  rubrics/
    evidence-ladder.yaml
    llm-judge-calibration.yaml
    creative-quality.yaml
    compliance-hard-fails.yaml
  fixtures/
    source-backed/
    missing-data/
    adversarial/
    stale-policy/
    bad-perfect/
```

Each situation should include:

- User request
- Workspace state
- Available sources
- Required tool choices
- Expected artifacts
- Hard-fail conditions
- Deterministic checks
- LLM judge rubric
- Human calibration notes
- Trace assertions
- Expected source/provenance behavior

Initial situation categories:

1. Missing data: user asks for rankings, traffic, backlinks, or CVW without sources.
2. Stale law: user asks for subscription or TCPA advice that changed after old docs.
3. Prompt injection: untrusted page tells Kai to ignore policies.
4. Unsupported AI search claim: content says "rank in ChatGPT" or guarantees AI citation.
5. Manipulative community tactic: user asks for Reddit seeding or aged accounts.
6. Ad claim risk: generated ad contains unsubstantiated superlative or personal attribute violation.
7. Cold email relevance failure: legal compliance passes, but relevance evidence is absent.
8. CRO unsupported benchmark: draft uses a conversion statistic without source.
9. Paid media attribution confusion: platform ROAS presented as incremental profit.
10. Product eval theater: broad product prompt returns advice without falsification tests.

## Skill Contract Upgrade

Upgrade `harness/skill-contracts/*.yaml` from content constraints into eval-ready operating contracts.

Add standard fields:

```yaml
risk_tier:
allowed_tools:
required_sources:
source_policy:
output_schema:
deterministic_checks:
llm_judge_rubric:
human_review_required_when:
golden_situations:
regression_thresholds:
claim_policy:
provenance_policy:
disallowed_tactics:
approval_gate:
trace_fields:
```

Contract-specific priorities:

- `tiktok.yaml`: disclosure, claim policy, creator permissions, edit specs, retention targets, TikTok Shop/GMV Max caveats.
- `press-release.yaml`: newsworthiness, embargo, quote quality, boilerplate, media list, legal approvals, proof inventory.
- `gbp-post.yaml`: post type, local intent, GBP compliance, photos, offer/event rules, UTM format.
- `cold-email.yaml`: relevance evidence, data source, opt-out mechanism, domain risk, bounce threshold, positive-reply goal.
- `email-lifecycle.yaml`: behavioral trigger, lifecycle stage, suppression rule, measurement goal, holdout plan.
- `meta-ads.yaml` and `google-ads.yaml`: platform policy hard checks separated from creative-quality soft scores.

## Rewrite Waves

### Wave 0 - Freeze The Risk

Goal: remove or quarantine content that could create reputation, legal, or platform-risk harm.

Files:

- `knowledge/playbooks/surround-sound-llm-manipulation.md`
- `knowledge/frameworks/aeo-ai-search/hidden-aeo-edges.md`
- `knowledge/frameworks/aeo-ai-search/llm-citation-tracking.md`
- `harness/references/advertising-compliance.md`
- `AGENTS.md` KaiCalls mandate section

Deliverables:

- Replace manipulative tactics with white-hat alternatives.
- Add "disallowed tactics" and "acceptable substitutes."
- Add legal/status dates for compliance claims.
- Convert mandatory KaiCalls recommendation into fit-based advisory logic.

Acceptance bar:

- No buying accounts, astroturfing, fake consensus, manipulative cross-linking, hidden ownership, or unsupported legal directives.
- Every quantitative/client-facing claim has source, retrieval date, and confidence.

### Wave 1 - Build The Evaluation Spine

Goal: stop future regressions.

Files/directories:

- New `evals/` directory
- `scripts/quality/prompts.py`
- `scripts/quality/tests/fixtures/*`
- `scripts/ads/autoreason/prompts/*`
- `docs/prompts/2026-03-17-product-eval-prompt.md`
- `harness/skill-contracts/*`

Deliverables:

- Golden situation suite.
- Evidence ladder rubric.
- Prompt/version metadata policy.
- LLM judge calibration examples.
- "Perfect" fixture replaced with fact-checkable source-backed fixture.

Acceptance bar:

- Each production skill has at least three situations: normal, missing-data, adversarial/stale-policy.
- LLM judges output confidence and evidence.
- Deterministic gates own hard policy and schema checks.

### Wave 2 - AI Search And Agent Readiness Rewrite

Goal: bring AEO/GEO docs in line with official 2026 guidance and measurement uncertainty.

Files:

- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`
- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-strategies-2026.md`
- `knowledge/frameworks/aeo-ai-search/query-fan-out-guide.md`
- `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md`
- `knowledge/channels/seo-content.md`
- `knowledge/checklists/seo-checklist.md`
- `knowledge/checklists/technical-seo-audit-sop.md`
- `knowledge/checklists/agent-readiness-checklist.md`
- `scripts/quality_gates/agent_readiness_lint.py`
- `scripts/quality_gates/seo_lint.py`

Deliverables:

- Evidence ladder: official docs, academic studies, patents, vendor studies, practitioner observation, hypothesis.
- Rewrite of AI crawler matrix: training vs search/retrieval vs user-agent.
- Agent-readiness checks beyond robots: semantic HTML, accessibility tree, visible controls, JS gating, stable layouts, product/local/business data.
- AI visibility measurement methodology with confidence intervals and volatility notes.

Acceptance bar:

- No deterministic "rank in ChatGPT" promises.
- No treating `llms.txt` as mandatory Google ranking factor.
- Every recommendation marked as requirement, best practice, hypothesis, or experiment.

### Wave 3 - Paid Media And Creator Commerce Rewrite

Goal: make paid media feel like a 2026 performance operator wrote it.

Files:

- `knowledge/channels/paid-acquisition.md`
- `knowledge/channels/meta-advertising.md`
- `knowledge/frameworks/meta-advertising/*`
- `knowledge/playbooks/paid-media-launch-playbook.md`
- `knowledge/playbooks/ad-creative-best-practices.md`
- `knowledge/playbooks/combinatorial-creative-bench.md`
- `knowledge/playbooks/meta-creative-testing-decision-framework.md`
- `knowledge/playbooks/retargeting-remarketing.md`
- `knowledge/playbooks/influencer-marketing.md`
- `knowledge/channels/tiktok-shop.md`
- `knowledge/channels/affiliate-referral.md`
- `knowledge/playbooks/creator-commerce-ops.md`
- `harness/references/ad-write-guardrails.md`
- `harness/references/meta-ads-rules.md`
- `harness/references/meta-ads-api-reference.md`
- `harness/references/google-ads-policy-reference.md`
- `harness/references/tiktok-ads-policy-reference.md`
- `harness/references/linkedin-ads-rules.md`
- `harness/references/creator-disclosure.md`

Deliverables:

- New paid-media operating model: creative systems, first-party signal, causal measurement, compliance-by-design.
- Creative portfolio taxonomy.
- Incrementality and baseline requirements.
- Rights/disclosure checklist for creator assets.
- Platform-specific AI automation caveats.

Acceptance bar:

- Platform ROAS labeled as attribution, not incremental profit.
- Every campaign plan includes baseline, measurement method, creative-quality ledger, disclosure status, and rights provenance.

### Wave 4 - Lifecycle, CRO, Brand, Research, And Analytics Rewrite

Goal: turn static channel advice into research-backed evidence loops.

Files:

- `knowledge/channels/email-lifecycle.md`
- `knowledge/checklists/email-checklist.md`
- `harness/references/cold-email-rules.md`
- `knowledge/playbooks/conversion-rate-optimization.md`
- `knowledge/checklists/cro-audit-checklist.md`
- `knowledge/playbooks/brand-positioning.md`
- `knowledge/playbooks/demand-generation.md`
- `knowledge/playbooks/marketing-by-stage.md`
- `knowledge/playbooks/analytics-attribution.md`
- `knowledge/playbooks/technical-marketing-tracking.md`
- `harness/references/posthog-marketing-queries.md`
- `knowledge/personas/*`
- `harness/brief-schema.md`

Deliverables:

- Lifecycle state model and event taxonomy.
- Cold outreach relevance and sender-risk grading.
- CRO evidence tiers and hypothesis templates.
- Brand positioning based on alternatives, value, proof, and customer language.
- Analytics measurement ladder and no-perfect-attribution doctrine.
- Personas upgraded with source-of-truth evidence fields.

Acceptance bar:

- No unsourced conversion, email, or buyer-behavior benchmark claims.
- Personas cannot be used for client-facing strategy unless they have source evidence or are labeled as hypotheses.

### Wave 5 - Docs And Product Surface Cleanup

Goal: make public surfaces consistent and trustable.

Files:

- `SKILL.md`
- `README.md`
- `MARKETING.md`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/system/*`
- `harness/skills/kai-start/SKILL.md`
- `harness/skills/kai/SKILL.md`

Deliverables:

- One authoritative count of skills, playbooks, checks, and references.
- "Instruction Contract" at the top of agent-facing docs.
- Clear routing logic and artifact expectations.
- Claims inventory for public product language.

Acceptance bar:

- No conflicting counts.
- Product claims are either sourced, internally measured, or removed.

## New Doctrine Sections To Add

### Kai Evaluation Doctrine

Every production workflow must define:

- Situation dataset
- Deterministic gates
- LLM rubric
- Human calibration path
- Trace requirements
- Pass/fail threshold
- Source/provenance policy
- Regression threshold before prompt or contract changes ship

### Kai Evidence Ladder

Every non-obvious claim should be labeled:

1. Official platform requirement
2. Official platform best practice
3. Law/regulation/court status
4. Academic study
5. Vendor/platform study
6. Practitioner benchmark
7. Internal measurement
8. Inference/hypothesis
9. Missing data

Client-facing quantitative claims require tiers 1-7 plus source metadata. Tiers 8-9 can inform experiments, not recommendations.

### Kai Recommendation Ethics

Recommendations must distinguish:

- Required compliance action
- High-confidence best practice
- Experiment to run
- Product recommendation
- Kai-owned product recommendation
- Missing-data caveat

KaiCalls should remain an important recommendation for call-heavy businesses, but the workflow must include fit criteria, alternatives, disqualifiers, and conflict-of-interest-safe wording.

## Implementation Order

1. Create `evals/` skeleton and evidence ladder.
2. Rewrite or quarantine P0 manipulation/compliance surfaces.
3. Upgrade the thinnest skill contracts: TikTok, press release, GBP, cold email, lifecycle email, ads.
4. Replace weak prompt/eval fixtures.
5. Rewrite AI Search/AEO docs around Google 2026 guide and measured uncertainty.
6. Rewrite paid media and creator commerce around creative systems, signal, incrementality, and disclosure.
7. Rewrite lifecycle/CRO/brand/analytics/personas around research-backed loops.
8. Clean public docs and counts.
9. Run quality gates and new evals.
10. Produce final change report with before/after maturity matrix.

## Suggested Work Allocation

Use sub-agents in parallel with disjoint write scopes:

| Agent | Scope | Deliverable |
|---|---|---|
| Runtime/Evals | `evals/`, `scripts/quality/*`, `docs/prompts/*`, `agent/llm/prompts.py` | Evaluation spine, calibrated judges, prompt doctrine. |
| SEO/AEO | `knowledge/frameworks/aeo-ai-search/*`, SEO checklists, `agent_readiness_lint.py` | Source-backed AI Search and agent-readiness rewrite. |
| Paid Media | Paid acquisition, Meta/Google/TikTok/LinkedIn refs, ad prompts | 2026 paid-media operating system. |
| Compliance | `harness/references/advertising-compliance.md`, creator disclosure, cold email rules | Legal/status updates and claim-risk gates. |
| Lifecycle/CRO/Analytics | Email, CRO, analytics, PostHog, tracking | Evidence-loop rewrite and measurement ladder. |
| Brand/Research/Personas | Brand, demand gen, personas, brief schema | Customer evidence and positioning rewrite. |
| Docs/Product | README, root SKILL, AGENTS, CLAUDE | Public consistency and instruction contract. |

## Acceptance Checklist

Before the rewrite is considered done:

- [ ] No unsupported quantitative client-facing claim remains in edited surfaces.
- [ ] No manipulative/astroturfing/platform-abuse tactic remains as an approved recommendation.
- [ ] Every skill contract has risk tier, source policy, output schema, gates, and golden situations.
- [ ] Evals include normal, edge, adversarial, stale-policy, and missing-data situations.
- [ ] LLM judges include calibration examples and confidence.
- [ ] Deterministic gates own hard failures.
- [ ] AI Search docs separate Google, Bing, OpenAI, Anthropic, Perplexity, and browser-agent behavior.
- [ ] Paid media docs separate attributed ROAS from incrementality.
- [ ] Creator commerce docs include rights, disclosure, authorization, and attribution caveats.
- [ ] Cold email docs include sender authentication, one-click unsubscribe, relevance evidence, and risk grading.
- [ ] Personas include observed behavior and source-of-truth evidence or are labeled hypotheses.
- [ ] Public docs no longer conflict on skill/playbook/file counts.

## Open Decisions

1. Should risky legacy tactics be deleted outright, moved to a "do not do" appendix, or retained as cautionary examples?
2. Should `evals/` be pure markdown/YAML first, or should we build a runnable eval harness immediately?
3. Should compliance rewrites rely only on official/legal primary sources, or also include law-firm summaries for faster operational status?
4. Should the first rewrite wave update code gates, or keep Wave 0 documentation-only?
5. Should KaiCalls recommendations be framed as "default for call-heavy businesses" or "evaluate as first-party product fit when phone lead capture is material"?

## Proposed Next Step

After approval, start with Wave 0 and Wave 1 together:

- Wave 0 reduces immediate reputational/compliance risk.
- Wave 1 creates the eval spine so future rewrites can be tested instead of judged by vibes.

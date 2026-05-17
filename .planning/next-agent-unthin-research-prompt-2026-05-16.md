# Next Agent Prompt - Research And Unthin Kai Content

You are continuing work in `E:\Dev2\kai-cmo-harness-work`.

The previous run created the planning artifact `.planning/expert-rewrite-program-2026-05-16.md`, completed Wave 0/Wave 1 risk reduction, and added the first `evals/` spine. Your task is to continue with deeper research and content unthinning.

Do not treat "unthin" as "make longer." Treat it as: add expert operating detail, current research, decision trees, examples, source tiers, failure modes, measurement methods, and eval-ready acceptance criteria.

## Non-Negotiables

- Use sub-agents. Split research and writing into disjoint scopes.
- Do not revert or overwrite unrelated dirty worktree changes.
- Use PowerShell fallback if `rg` fails with the Windows app-bundled permission issue:

```powershell
Get-ChildItem -LiteralPath .\target-folder -Recurse -File | Select-String -Pattern 'search term'
```

- Prefer primary/current sources: official platform docs, court opinions/regulator docs, academic papers, original benchmark reports, platform engineering blogs, and respected practitioner research.
- Every quantitative or client-facing claim must have a source, retrieval date, evidence tier, and confidence label.
- Missing data must be called out as missing data, not replaced with guesses.
- Do not add manipulative tactics, astroturfing, bought accounts, fake consensus, hidden ownership, or ToS-abuse as recommendations. If relevant, preserve them only as explicit "do not do" examples.
- Keep edits scoped. Avoid broad refactors unless needed for the task.
- Run targeted validation after edits: YAML parse checks, `git diff --check`, prompt compatibility tests, and any relevant existing tests.

## Current State To Know

Recently changed:

- `evals/` was created with rubrics and seven golden situations.
- `harness/skill-contracts/tiktok.yaml`, `press-release.yaml`, `gbp-post.yaml`, `cold-email.yaml`, and `email-lifecycle.yaml` were upgraded into eval-ready contracts.
- `knowledge/playbooks/surround-sound-llm-manipulation.md`, `knowledge/frameworks/aeo-ai-search/hidden-aeo-edges.md`, `llm-citation-tracking.md`, and `ai-crawlers-technical-reference.md` were rewritten for safety and evidence discipline.
- `harness/references/advertising-compliance.md` was updated for Click-to-Cancel and TCPA vacatur status.
- `scripts/quality/prompts.py`, `scripts/ads/autoreason/prompts/author.md`, `scripts/ads/autoreason/prompts/judge.md`, and `scripts/quality/tests/fixtures/perfect.md` were upgraded.

There were pre-existing unrelated dirty files before that run. Inspect `git status --short` and avoid claiming all dirty files as yours.

## Orchestrator Task

Start by reading:

- `.planning/expert-rewrite-program-2026-05-16.md`
- `.planning/next-agent-unthin-research-prompt-2026-05-16.md`
- `evals/README.md`
- `AGENTS.md`

Then launch sub-agents for the scopes below. Keep write scopes disjoint. Tell every worker: "You are not alone in the codebase; do not revert or overwrite others' changes."

Your deliverable is an implemented Wave 2/Wave 3/Wave 4 slice plus a concise final report:

- Files changed
- Research sources used
- What was unthinned
- Validation run
- Remaining gaps

## Sub-Agent 1 - AI Search, SEO, And Agent Readiness

Write scope:

- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`
- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-strategies-2026.md`
- `knowledge/frameworks/aeo-ai-search/query-fan-out-guide.md`
- `knowledge/channels/seo-content.md`
- `knowledge/checklists/seo-checklist.md`
- `knowledge/checklists/technical-seo-audit-sop.md`
- `knowledge/checklists/agent-readiness-checklist.md`
- `scripts/quality_gates/agent_readiness_lint.py`
- `scripts/quality_gates/seo_lint.py`
- Related tests only if needed.

Research sources to use:

- Google AI Search guidance, especially the May 15, 2026 AI optimization guide.
- Google helpful content and AI content guidance.
- Bing AI search optimization and Bing Webmaster AI Performance.
- OpenAI, Anthropic, Perplexity crawler docs.
- web.dev agent-friendly site guidance.
- GEO academic paper and newer AI visibility measurement papers.
- Aleyda Solis / SEOFOMO, Lily Ray, Mike King, Jason Barnard where useful.

Unthin by adding:

- Evidence ladder for every recommendation.
- Difference between Google AI Overviews/AI Mode, Bing/Copilot, ChatGPT, Claude, Perplexity, Grok/X, and browser agents.
- Measurement uncertainty and sampling guidance.
- Passage retrievability, entity clarity, source quality, and schema guidance.
- Agent-readiness checks beyond robots: semantic HTML, accessibility tree, visible controls, stable layouts, JS gating, critical data not trapped in images/PDFs/tabs.
- Concrete audit output examples and data-gap language.

Acceptance bar:

- No deterministic "rank in ChatGPT" promises.
- No treating `llms.txt` as a Google ranking factor.
- No unsupported citation-lift claims.
- Lints/tests added or updated if code behavior changes.

## Sub-Agent 2 - Paid Media, Creative Systems, And Creator Commerce

Write scope:

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

Research sources to use:

- Meta Engineering Andromeda and GEM.
- Google Ads AI Max, PMax controls, Meridian MMM, Ads Safety reports.
- TikTok GMV Max, TikTok Shop Ads, Smart+, Symphony, creator/affiliate policy.
- LinkedIn B2B Institute, Edelman/LinkedIn B2B thought leadership.
- Kantar, CreativeX, System1 / Orlando Wood, WARC, Analytic Partners, Ehrenberg-Bass.
- IAB incremental measurement.
- FTC Endorsement Guides and IAB AI transparency/disclosure.

Unthin by adding:

- 2026 paid-media operating model: creative systems, first-party signal, incrementality, compliance-by-design.
- Creative portfolio taxonomy: hooks, proof types, product cues, distinctiveness, audience state, offer stage.
- Creative-quality ledger fields.
- Incrementality decision tree: platform ROAS vs lift test vs geo test vs MMM vs directional proxy.
- Creator-commerce ops: rights windows, Spark/Partnership ads, affiliate authorization, disclosure evidence, SKU economics, sample ops, organic cannibalization, GMV Max caveats.
- Platform-specific AI automation caveats and control surfaces.

Acceptance bar:

- Platform ROAS is not presented as incremental profit.
- Every creator/UGC recommendation includes rights and disclosure checks.
- No universal PMax/Advantage+/GMV Max advice without account-state decision logic.

## Sub-Agent 3 - Lifecycle Email, Cold Outreach, CRO, Brand, Analytics, And Research

Write scope:

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

Research sources to use:

- Braze, Customer.io, Klaviyo benchmarks, Validity/Litmus.
- Google sender guidelines, Yahoo Sender Hub, Spamhaus, FTC CAN-SPAM.
- Gong, Lavender, Gartner B2B buying research, 6sense.
- Baymard, Contentsquare, CXL, Wynter.
- April Dunford, Forrester B2B messaging, LinkedIn B2B Institute / Ehrenberg-Bass 95-5 rule.
- Google Meridian, IAB State of Data, privacy measurement sources.
- Maze, User Interviews, Teresa Torres, Rob Fitzpatrick.

Unthin by adding:

- Lifecycle state model: subscribed lifecycle, transactional, cold outbound, retention, winback.
- Event taxonomy, suppression logic, preference centers, holdouts, deliverability monitoring.
- Cold outreach relevance evidence, sender risk grading, one-click unsubscribe, authentication, complaint thresholds.
- CRO evidence tiers, hypothesis format, guardrail metrics, sample-size caution, qualitative research before recommendation.
- Positioning workflow based on alternatives, unique capability, value, proof, best-fit customer, customer-language mining.
- Analytics measurement ladder: event hygiene, dashboards, cohorts/funnels, holdouts/lift, MMM.
- Personas with observed behavior, buying trigger, budget authority, objection, current workaround, interview quote/source.

Acceptance bar:

- No unsourced conversion, email, deliverability, or buyer-behavior benchmark claims.
- No "perfect attribution" promise.
- Personas clearly distinguish evidence-backed insights from hypotheses.

## Sub-Agent 4 - Eval Expansion And Contracts

Write scope:

- `evals/**`
- `harness/skill-contracts/*.yaml` not already upgraded, especially:
  - `blog-post.yaml`
  - `landing-page.yaml`
  - `meta-ads.yaml`
  - `google-ads.yaml`
  - `linkedin-article.yaml`
  - `email.yaml`
  - `review-response.yaml`
  - `review-request-sequence.yaml`
  - `call-script.yaml`
  - `voice-gate.yaml`

Do not edit the five already-upgraded contracts unless needed for consistency and you coordinate with the orchestrator.

Unthin by adding:

- More golden situations:
  - AI Search measurement volatility
  - `llms.txt` misconception
  - PMax account-state decision
  - creator rights/disclosure failure
  - cold outreach relevance failure
  - CRO unsupported benchmark
  - brand positioning without customer research
  - persona invented from vibes
  - attribution overclaim
  - PR quote/newsworthiness failure
- Contract schema consistency across formats.
- Regression thresholds and required deterministic checks.
- Hard-fail catalogs for compliance and provenance.

Acceptance bar:

- All YAML parses.
- Every production content contract has `risk_tier`, `required_sources`, `source_policy`, `deterministic_checks`, `llm_judge_rubric`, `golden_situations`, and `trace_fields`.

## Sub-Agent 5 - Product Docs And Governance

Write scope:

- `AGENTS.md`
- `CLAUDE.md`
- `SKILL.md`
- `README.md`
- `MARKETING.md`
- `harness/skills/kai/SKILL.md`
- `harness/skills/kai-start/SKILL.md`
- `docs/system/*`

Unthin by adding:

- One authoritative skill/playbook/checklist count.
- "Instruction Contract" with authority order, trusted vs untrusted content, source requirements, when to browse, when to gate, when to ask, and when to stop.
- Recommendation ethics doctrine:
  - required compliance action
  - high-confidence best practice
  - experiment to run
  - product recommendation
  - Kai-owned product recommendation
  - missing-data caveat
- Fit-based KaiCalls recommendation logic with alternatives, disqualifiers, and conflict-safe wording.
- Evaluation doctrine: every workflow needs situations, deterministic gates, LLM rubric, human calibration, trace requirements, and pass/fail threshold.

Acceptance bar:

- No conflicting counts.
- No commercially biased "always recommend" language without fit/disclosure.
- Agent-facing instructions are operational, not just promotional.

## Research Output Requirements For Every Sub-Agent

Each sub-agent final response must include:

- Changed files.
- Top sources used with URLs and retrieval date.
- Claims added or removed.
- Sections unthinned.
- Any remaining source gaps.
- Validation run.

## Final Orchestrator Validation

After merging worker changes, run:

```powershell
git diff --check
```

Parse YAML:

```powershell
Get-ChildItem -LiteralPath evals,harness\skill-contracts -Recurse -File -Include *.yaml,*.yml | ForEach-Object {
  python -c "import sys,yaml; yaml.safe_load(open(sys.argv[1], encoding='utf-8')); print(sys.argv[1])" $_.FullName
}
```

Run targeted tests:

```powershell
python -m py_compile .\scripts\quality\prompts.py
python -m scripts.quality.tests.test_engine
python -m scripts.ads.autoreason.test_brand_lock
```

Run additional tests only for code touched by the new wave.

## Final Report Shape

Use this structure:

```markdown
## Completed

- ...

## Research Sources

- ...

## Changed Files

- ...

## Validation

- ...

## Remaining Gaps

- ...

## Recommended Next Wave

- ...
```

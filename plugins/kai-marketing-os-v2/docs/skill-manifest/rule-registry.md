# Kai Skill Manifest Rule Registry

This registry gives canonical manifest pages stable rule IDs for citing Kai methodology across `harness/skills/kai-*`.

These IDs are manifest-level stable citation IDs derived from documented local sources. They are not upstream framework IDs, and source files should not be rewritten to imply they originally carried these IDs. Cite the ID in manifest pages, then cite the source file and section named in this registry.

## Namespace Scheme

| Namespace | Manifest area | Primary local sources |
|---|---|---|
| `AA-*` | Algorithmic Authorship and SEO passage structure | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`, `scripts/quality_gates/seo_lint.py` |
| `FU-*` | Four U's quality scoring | `knowledge/frameworks/content-copywriting/four-us-framework.md`, `scripts/quality_gates/four_us_score.py`, `harness/skills/kai-gate/SKILL.md` |
| `PE-*` | Perception Engineering | `knowledge/frameworks/content-copywriting/perception-engineering.md`, `knowledge/checklists/perception-engineering-checklist.md` |
| `QDQ-*` | QDP/QDH/QDS content architecture | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` |
| `AEO-*` | AEO, AI search, and agent-readiness | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`, `knowledge/checklists/agent-readiness-checklist.md`, `scripts/quality_gates/agent_readiness_lint.py` |
| `PROV-*` | Audit and quantitative claim provenance | `harness/references/audit-data-provenance.md`, `scripts/quality_gates/audit_provenance_lint.py` |
| `POL-*` | Advertising policy, compliance, and write-access controls | `harness/references/advertising-compliance.md`, `harness/references/ad-write-guardrails.md`, platform policy references |
| `VG-*` | Voice gate and mechanical content quality | `harness/skill-contracts/voice-gate.yaml`, `harness/skills/kai-gate/SKILL.md`, `harness/skills/kai-write/SKILL.md`, `scripts/quality_gates/banned_word_check.py` |
| `TASTE-*` | Design taste and AI interface quality | `harness/skills/kai-taste/SKILL.md` |

## Algorithmic Authorship Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `AA-001` | manifest | Put condition clauses after the main clause. Write "Do X if Y" and "X happens because Y" instead of opening with "If" or "Because" when the sentence still reads naturally. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 1", "Rule 2", checklist |
| `AA-002` | manifest | Prefer certain, declarative sentences over conditional future phrasing when the claim can be stated directly. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 3" |
| `AA-003` | manifest | Start instruction sentences with the verb, then place modifiers after the action. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 4" |
| `AA-004` | manifest | Use numbered lists for steps, methods, comparisons, and ordered processes. Use bullets for types, categories, and unordered sets. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 5" |
| `AA-005` | manifest | Keep sentences short and split compound explanations into separate sentences when the average sentence length exceeds roughly 20 words. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 7"; `scripts/quality_gates/seo_lint.py` - sentence length check |
| `AA-006` | manifest | Repeat anchor terms between sequential sentences so each passage is self-contained and easy to extract. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 8" |
| `AA-007` | manifest | Name an entity twice before switching to attributes, shorthand, or pronouns. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 10" and "Rule 11" |
| `AA-008` | manifest | Replace vague quantifiers with numeric values, counts, named examples, or declared missing data. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 13" and "Rule 21" |
| `AA-009` | manifest | Follow each declaration with an example, evidence note, or concrete instance. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 15" |
| `AA-010` | manifest | Bold the answer span, not the query-matching term, when emphasis is used for search-oriented content. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 20" |
| `AA-011` | manifest | Do not place internal links in the first word, first sentence, or first line of a paragraph. Establish context before linking. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 25", "Rule 26", "Rule 27", "Rule 28" |
| `AA-012` | manifest | Integrate external sources inside the sentence that uses them. Do not leave source context only in footnotes. | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` - "Rule 31" |

## Four U's Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `FU-001` | manifest | Score every publishable content artifact on Unique, Useful, Ultra-specific, and Urgent, with each dimension rated 1-4. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "Scoring Your Content"; `harness/skills/kai-gate/SKILL.md` - "Four U's Score" |
| `FU-002` | manifest | Unique means the artifact is not interchangeable with competitor content because it contains specific experience, proprietary data, a contrarian frame, brand voice, or a combination others have not connected. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "1. UNIQUE" |
| `FU-003` | manifest | Useful means the reader can take action immediately through steps, templates, checklists, tools, resources, or clear "do this, then this" guidance. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "2. USEFUL" |
| `FU-004` | manifest | Ultra-specific means the artifact contains exact numbers, named tools, real examples, timeframes, outcomes, or other concrete details. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "3. ULTRA-SPECIFIC" |
| `FU-005` | manifest | Urgent means the artifact gives the reader a reason to act today, such as a current change, deadline, consequence of delay, event window, or quantified loss. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "4. URGENT" |
| `FU-006` | manifest | The default publishing threshold is 12/16 for blog, SEO, and article content, and 10/16 for ads and email. Any single U below 2 should block or force revision. | `knowledge/frameworks/content-copywriting/four-us-framework.md` - "Target"; `scripts/quality_gates/four_us_score.py` - `MIN_TOTAL`, `MIN_SINGLE`; `harness/skills/kai-gate/SKILL.md` - "Thresholds" |

## Perception Engineering Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `PE-001` | manifest | Before persuasion, identify the cached prediction or identity label that explains the subject's current refusal, hesitation, or avoidance. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Core Principle: Active Inference"; checklist |
| `PE-002` | manifest | Use Perception-layer moves to destabilize the old explanation loop before installing a new action path. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Layer 1: PERCEPTION" |
| `PE-003` | manifest | Use "as if" framing when a subject needs to simulate a new identity without triggering direct resistance. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "The As If Shift" |
| `PE-004` | manifest | Reframe failure as data acquisition when avoidance is driven by status threat or judgment. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Failure-to-Data Reframe" |
| `PE-005` | manifest | Shift the context genre when facts alone will not change behavior. Move the interaction from Exam, Boardroom, or Crisis into a more useful genre such as Lab when experimentation is needed. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Layer 2: CONTEXT", "Genre-Shifting" |
| `PE-006` | manifest | Engineer friction deliberately: add cognitive load to unwanted paths and remove friction from desired paths. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Choice Architecture (Friction Design)" |
| `PE-007` | manifest | Use Permission-layer moves to reduce imagined penalties through future pacing, authority framing, or double binds that keep choices inside the desired action path. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Layer 3: PERMISSION" |
| `PE-008` | manifest | Do not use Perception Engineering to push decisions that harm the audience. The ethical use case is overcoming irrational blocks, improving user experience, or clarifying useful choices. | `knowledge/frameworks/content-copywriting/perception-engineering.md` - "Ethical Note" |

## QDP/QDH/QDS Content Architecture Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `QDQ-001` | manifest | Classify a topic as QDP, QDH, or QDS before assigning URL, heading, or sentence treatment. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Core Concept" |
| `QDQ-002` | manifest | Use QDP when a topic meets at least three of four query criteria and index criteria support a dedicated page. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Core Concept", "Query-Level Criteria" |
| `QDQ-003` | manifest | Use QDH when demand or intent exists but the topic does not justify a dedicated URL. Place it as a clear section under the stronger parent page. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Core Concept", examples |
| `QDQ-004` | manifest | Use QDS when the topic is needed for completeness but has minimal independent search signal. Cover it in a sentence or short passage. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Core Concept" |
| `QDQ-005` | manifest | Evaluate index construction through index size, vocabulary uniformity, PageRank or GBP compensation, and query-template evidence. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Google's Index Construction Criteria" |
| `QDQ-006` | manifest | Evaluate query-level demand through different entities, search demand, recognizable pattern, and low similarity to existing queries. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Query-Level Criteria (4 Signals)" |
| `QDQ-007` | manifest | For overlapping URLs, inspect Search Console query overlap and historical SERP vocabulary before merging, splitting, or relevance-configuring pages. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Scenario 1: Two Overlapping Pages" |
| `QDQ-008` | manifest | Respect historically performing URL structures. Standardize forward through breadcrumbs, internal links, and structured data when rewriting old URL logic would risk authority loss. | `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` - "Scenario 4: Inconsistent URL Logic Across Locations" |

## AEO And Agent-Readiness Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `AEO-001` | manifest | Attach an evidence tier to every AEO recommendation. Use Tier 1 for official requirements, Tier 2 for official guidance, Tier 3 for academic research, Tier 4 for patents or system disclosures, Tier 7 for internal measurement, Tier 8 for hypothesis, and Tier 9 for missing data. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Evidence Ladder" |
| `AEO-002` | manifest | Treat AI visibility as multi-engine. Build a provider matrix for Google, ChatGPT/OpenAI, Claude/Anthropic, Perplexity, Bing/Copilot, and Grok/X before changing crawl policy. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "The 6 Operating Principles", "Provider Access Matrix" |
| `AEO-003` | manifest | Treat Google AI Overview and AI Mode work as SEO grounded in normal crawlability, indexability, snippet eligibility, and quality systems. Do not present `llms.txt`, special AI schema, or forced chunking as Google requirements. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Google AI work is still SEO"; `knowledge/checklists/agent-readiness-checklist.md` - "llms.txt Entrypoint" |
| `AEO-004` | manifest | Add non-commodity value through original data, expert review, firsthand experience, public datasets, local/product details, or clearer synthesis. Do not publish longer paraphrases of the top results. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Information Gain and Non-Commodity Value" |
| `AEO-005` | manifest | Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Passage retrievability beats page bloat", "Evidence-Rich Passage Design" |
| `AEO-006` | manifest | Use entity clarity controls: consistent names, entity homes, author pages, Organization/Product/Article schema where visible content supports it, and third-party corroboration. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Entity clarity reduces ambiguity"; `knowledge/checklists/agent-readiness-checklist.md` - "Entity & Schema Signaling" |
| `AEO-007` | manifest | Report AI visibility as probabilistic. Measure citations, mentions, answer absorption, referrals, clicks, and conversions with method notes and confidence. Do not guarantee inclusion or ranking in AI assistants. | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` - "Measurement is probabilistic"; `scripts/quality_gates/seo_lint.py` - AI search overclaim checks |
| `AEO-008` | manifest | Agent-readiness audits must pass all P0 crawler, machine-readable docs, and non-JS content checks before site-level AEO or surround-sound planning proceeds. | `knowledge/checklists/agent-readiness-checklist.md` - "Scoring", "Provider Crawler Access Policy", "Machine-Readable Docs", "Content Not Hidden Behind JS" |
| `AEO-009` | manifest | Publish product capabilities, ICP, primary actions, integration surface, auth model, pricing model, approval flow, and run lifecycle in plain text where agents can read them. | `knowledge/checklists/agent-readiness-checklist.md` - "Capability Signaling" |
| `AEO-010` | manifest | Do not hide critical facts inside images, videos, PDFs, canvases, accordions, modals, or client-side rendering without equivalent visible text. | `knowledge/checklists/agent-readiness-checklist.md` - "Machine-Readable Docs", "Content Not Hidden Behind JS" |

## Provenance Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `PROV-001` | manifest | Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings. | `harness/references/audit-data-provenance.md` - "Data Modes" |
| `PROV-002` | manifest | Default to `sales_external` when private access is not confirmed. Use only public crawls, public SERP observation, public schema/robots/sitemap data, PageSpeed Insights, and approved third-party APIs. | `harness/references/audit-data-provenance.md` - "Data Modes" |
| `PROV-003` | manifest | Use `onboarding_connected` only after the client has signed and granted access to connected sources such as GSC, GA4, GBP, ad accounts, CRM, call tracking, analytics exports, or owner data. | `harness/references/audit-data-provenance.md` - "Data Modes", "Sales vs Onboarding Data" |
| `PROV-004` | manifest | Use `internal_demo` only for sample-data demonstrations, and label the output as not client-ready. | `harness/references/audit-data-provenance.md` - "Data Modes" |
| `PROV-005` | manifest | Run `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>` before using numbers in data-backed workflows. | `harness/references/audit-data-provenance.md` - "Collection Rule", "Gate" |
| `PROV-006` | manifest | Every finding and quantitative claim must carry a source tier. Tier 4 inference or hypothesis is not score-eligible unless explicitly labeled as hypothesis and excluded from scoring. | `harness/references/audit-data-provenance.md` - "Source Tiers", "Required Finding Shape" |
| `PROV-007` | manifest | Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date. | `harness/references/audit-data-provenance.md` - "Hard Rules" |
| `PROV-008` | manifest | Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics. | `harness/references/audit-data-provenance.md` - "Collection Rule", "Required Output Files", "Hard Rules" |
| `PROV-009` | manifest | Audit folders must include `_data-sources.md`, `_data-gaps.md`, `kai-data.json`, `audit-data.json`, executive summary, detailed findings, and prioritized fixes. | `harness/references/audit-data-provenance.md` - "Required Output Files" |
| `PROV-010` | manifest | Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before audit or deck handoff. | `harness/references/audit-data-provenance.md` - "Gate"; `scripts/quality_gates/audit_provenance_lint.py` |

## Policy And Paid-Media Control Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `POL-001` | manifest | Load the platform policy reference before writing ad copy or creating paid-media payloads for that platform. | `harness/skills/kai-ad-campaign/SKILL.md` - "Phase 2: Campaign Strategy"; platform files under `harness/references/` |
| `POL-002` | manifest | All advertising claims must be truthful, non-misleading, and evidence-based before the ad runs. Specific support claims such as "clinically proven" require the exact level of evidence stated. | `harness/references/advertising-compliance.md` - "FTC: Truth in Advertising & Substantiation" |
| `POL-003` | manifest | Disclose material connections before or alongside endorsements. Disclosures must be clear, conspicuous, and visible in the medium where the endorsement appears. | `harness/references/advertising-compliance.md` - "FTC: Endorsement & Disclosure Rules" |
| `POL-004` | manifest | Health and wellness claims require competent and reliable scientific evidence. Anecdotes, expert opinion alone, animal studies alone, or disclaimers cannot substitute for substantiation. | `harness/references/advertising-compliance.md` - "FTC: Health & Wellness Claims" |
| `POL-005` | manifest | Paid-media evaluation starts read-only. Pull, validate, flag, recommend, and produce dry-run payloads without mutating campaigns. | `harness/references/ad-write-guardrails.md` - "Default Mode" |
| `POL-006` | manifest | No paid-media write action should auto-execute. Human approval is required for creating, publishing, pausing, activating, bid changes, budget changes, targeting changes, asset uploads, and keyword mutations. | `harness/references/ad-write-guardrails.md` - "Write Access Rule" |
| `POL-007` | manifest | New ads and campaigns must be created in `PAUSED` or draft state. Activation is a separate action with separate approval. | `harness/references/ad-write-guardrails.md` - "Write Access Rule"; `harness/skills/kai-ad-campaign/SKILL.md` - API execution notes |
| `POL-008` | manifest | Every paid-media mutation must include account allowlist data, target IDs, dry-run preview or before/after diff, evidence, platform policy result, audit log, measurement label, creative-quality ledger row, rights/disclosure evidence, and automation control review when applicable. | `harness/references/ad-write-guardrails.md` - "Required Pre-Flight" |
| `POL-009` | manifest | Budget increases default to a maximum of 20 percent, bid increases default to a maximum of 10 percent, and single budget changes default to a maximum of `$100` unless brand policy is stricter. | `harness/references/ad-write-guardrails.md` - "Spend Guardrails" |
| `POL-010` | manifest | Block paid-media mutation when evidence, measurement label, rights/disclosures, before/after diff, rollback instructions, account allowlist, or cap compliance is missing. Also block create/upload actions that set status to `ACTIVE`. | `harness/references/ad-write-guardrails.md` - "Blockers" |

## Voice Gate And Mechanical Quality Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `VG-001` | manifest | Run content-gate before voice-gate. Voice-gate complements mechanical checks and should not re-litigate items already handled by content-gate. | `harness/skill-contracts/voice-gate.yaml` - `source_policy`, `llm_judge_rubric`; `harness/skills/kai-write/SKILL.md` - "Step 4: Quality Gate" |
| `VG-002` | manifest | Voice-gate requires a readable draft path and a voice guide path. Missing required sources should block the review and request sources. | `harness/skill-contracts/voice-gate.yaml` - `required_sources`, `source_policy`, `deterministic_checks` |
| `VG-003` | manifest | Voice-gate verdicts are PASS, HOLD, or FAIL. PASS requires no high issues and no more than three medium issues; FAIL applies to three or more high issues or any hard-rule violation. | `harness/skill-contracts/voice-gate.yaml` - `verdict_policy` |
| `VG-004` | manifest | Voice-gate findings must be concrete, line-locatable, severity-calibrated, and traceable to the loaded voice guide, persona source, or content-gate report. | `harness/skill-contracts/voice-gate.yaml` - `llm_judge_rubric`, `claim_policy`, `provenance_policy` |
| `VG-005` | manifest | Tier 1 banned words and AI slop phrases hard-block publishable content until rewritten. Examples include "leverage", "utilize", "synergy", "in conclusion", and "in today's rapidly evolving". | `scripts/quality_gates/banned_word_check.py` - `TIER1`; `harness/skills/kai-gate/SKILL.md` - "Banned Word Check" |
| `VG-006` | manifest | Binary cliche patterns such as "X, not Y", "isn't X - it's Y", "Here's the thing", "I'll be honest", "Let that sink in", and "Hot take" fail the voice-pattern check unless they appear in comments or code fences. | `harness/skills/kai-gate/SKILL.md` - "Voice Pattern Check"; `harness/skills/kai-write/SKILL.md` - "Step 4: Quality Gate" |
| `VG-007` | manifest | Format-specific quality gates from the relevant skill contract must be applied after Four U's, banned-word, AI-slop, and voice-pattern checks. | `harness/skills/kai-write/SKILL.md` - "Step 4: Quality Gate"; `harness/skill-contracts/*.yaml` |
| `VG-008` | manifest | When a piece fails quality gates, fix the specific issues and re-score. Stop after two retry cycles and surface remaining failures. | `harness/skills/kai-write/SKILL.md` - "Step 4: Quality Gate" |

## Taste Rules

| ID | Level | Manifest rule text | Source file/section |
|---|---|---|---|
| `TASTE-001` | manifest | Treat taste as a control system that converts stochastic model output into reliable user outcomes with minimal correction cost. Taste remains subordinate to function. | `harness/skills/kai-taste/SKILL.md` - "Design Taste: Engineering Framework" |
| `TASTE-002` | manifest | Score generative AI interfaces on three pillars: Deterministic-Stochastic Balance, Interaction Density, and Visual Cohesion. | `harness/skills/kai-taste/SKILL.md` - "The Three Pillars" |
| `TASTE-003` | manifest | For Deterministic-Stochastic Balance, identify where entropy enters the pipeline, where output must be reproducible, and where structured outputs or tool calls should anchor reliability. | `harness/skills/kai-taste/SKILL.md` - "The Three Pillars", "Audit Mode Protocol", "Design Checklist" |
| `TASTE-004` | manifest | For Interaction Density, measure affordances per cognitive load unit and reduce the cost per useful outcome through progressive disclosure, cheap correction, and persistent artifacts. | `harness/skills/kai-taste/SKILL.md` - "The Three Pillars", "North Star Metrics", "Design Checklist" |
| `TASTE-005` | manifest | For Visual Cohesion, require component grammar, semantic structure before styling, protected affordances, consistent tokens, and generated output that fits the surrounding UI. | `harness/skills/kai-taste/SKILL.md` - "The Three Pillars", "Design Checklist" |
| `TASTE-006` | manifest | Scan every taste audit for the eight failure modes: stochastic over-constraint, density paralysis, cohesion rigidity, oracle polish, affordance collapse, interaction ceremony, trust distortion, and metric gaming. | `harness/skills/kai-taste/SKILL.md` - "Failure Modes" |
| `TASTE-007` | manifest | Use measurable proxies for taste, including refinement velocity, correction density, kinetic friction, time-to-value, correction effort, dismissal rate, and clarification burden. | `harness/skills/kai-taste/SKILL.md` - "North Star Metrics" |
| `TASTE-008` | manifest | In audit mode, identify the subject, score each pillar from 1-10, scan failure modes, measure available metrics, output a scorecard, and prioritize fixes as P0/P1/P2. | `harness/skills/kai-taste/SKILL.md` - "Audit Mode Protocol" |
| `TASTE-009` | manifest | In design mode, define the taste contract as testable constraints before building: reproducible zones, creative zones, hard constraints, verbosity ceiling, citation rules, formatting grammar, and interaction rules. | `harness/skills/kai-taste/SKILL.md` - "Design Mode Protocol" |
| `TASTE-010` | manifest | Instrument taste as a feedback loop and pair every optimization metric with a counter-metric to avoid metric gaming. | `harness/skills/kai-taste/SKILL.md` - "Failure Modes", "Design Mode Protocol" |

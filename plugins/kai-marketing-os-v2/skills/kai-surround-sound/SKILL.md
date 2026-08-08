---
name: kai-surround-sound
description: LLM brand manipulation — build a consensus web so ChatGPT, Claude, Perplexity, and Google AI Overviews mention your brand when people ask about your category. Uses surround sound methodology, entity SEO, and LLM citation science. Use when "get mentioned in AI", "LLM brand presence", "surround sound", "AI search visibility", "Perplexity ranking", "ChatGPT mentions", "AI Overview inclusion", "entity authority", "brand mentions in AI", or any request to influence how AI systems perceive and recommend your brand.
---

# /kai-surround-sound — Consensus Web for AI Answers

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

An audit of where the brand currently appears across the sources LLMs retrieve from — and where competitors appear instead — plus a sequenced plan to close that gap, starting with the brand's own domain. The deliverable states, with evidence, whether the site is legible to AI crawlers and browser agents, what the brand's presence looks like per source type, what content and placements would change it, and what to re-test weekly.

Surround-sound spend on a site agents cannot read dead-ends. Own-domain readiness is the gate, not a footnote.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`).

- **E3** — a named human approved the exact delivered files, and every quantitative claim resolves to a collector source in the audit data folder.
- **C4** — the Kai Data Provenance Rule is satisfied and `banned_word_check` plus `audit_provenance_lint` pass. Presence and competitor-presence claims cite the query run, the model or surface, and the date.
- **O1** — every P0 action names the metric it targets, with a baseline, a threshold, and an owner. Mention rate on the monitoring query set is the usual metric; record the pre-state before shipping anything.

## Constraints

**Kai Data Provenance Rule (non-negotiable).** Load `harness/references/audit-data-provenance.md` before writing findings. Declare `sales_external`, `onboarding_connected`, or `internal_demo`, run the collector before writing, and cite a collector source for every quantitative or client-facing claim.

```bash
python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>
```

```bash
python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir
```

- **Never invent** AI Overview visibility, citation counts, mention rates, rankings, traffic, review counts, backlinks, Domain Rating, or competitor presence. An untested query is a data gap. Record the surface, the exact prompt, and the date for every presence claim — AI answers are non-deterministic and undated results are not evidence.
- **Agent-readiness gate.** Run the checklist against the primary domain before planning outbound work. Any P0 failure blocks the rest of the plan.

```bash
python scripts/quality_gates/agent_readiness_lint.py https://<their-domain>
```

| Check | Report |
|---|---|
| `/robots.txt` explicit AI bot rules | Pass/Partial/Fail + what's there |
| `/llms.txt` entrypoint exists and valid | Pass/Partial/Fail + url or missing |
| Markdown mirrors of core docs | Pass/Partial/Fail + sample url |
| Content not JS-gated (`curl` test) | Pass/Partial/Fail + what renders |
| Capability signaling in plain text | Pass/Partial/Fail + missing fields |
| `Organization` + product JSON-LD | Pass/Partial/Fail + what's present |

Treat `llms.txt` as useful for cooperative agents, not a Google AI Overview ranking requirement.

- **No astroturfing.** Forum participation, reviews, listicle inclusion, and guest content are earned and disclosed. No sock puppets, no bought accounts, no undisclosed paid placement, no fabricated reviews or case studies, no hidden ownership of "third-party" properties. Material connections are disclosed per `harness/references/creator-disclosure.md`.
- **Platform rules bind.** Reddit, Quora, HN, G2, Capterra, and Product Hunt each have self-promotion and vendor-participation policies; follow them rather than routing around them. See `harness/references/reddit-organic-posting-rules.md` and `harness/references/social-automation-rules.md`.
- **Read `MARKETING.md` from the project root before asking the user anything.** If it does not exist, build it from the codebase — README, manifests, landing pages, route files, analytics and email config — and confirm the draft.
- **No live publishing or account mutation** without human approval. Content produced by this plan routes through `/kai-content-calendar` and its own gates.

**Prestige pulse weights** — the scoring used to compare the brand's footprint against the top three competitors:

| Mention type | Pulses |
|---|---|
| Forum post mentioning brand | 1 |
| Third-party review | 3 |
| "Best of" list inclusion | 5 |
| Wikipedia mention | 10 |
| Academic citation | 10 |

## Context

Five things must be known before the audit starts: the brand or product AI should mention, the category phrase people would actually ask about, current AI presence (tested, not assumed), which competitors are named when the brand is not, and what content assets already exist — blog, social, press, directories, forums.

| Need | Load |
|---|---|
| Surround-sound method | `knowledge/playbooks/surround-sound-llm-manipulation.md` |
| Measuring citations and mentions | `knowledge/frameworks/aeo-ai-search/llm-citation-tracking.md` |
| Entity establishment and knowledge graph | `knowledge/frameworks/aeo-ai-search/entity-seo-knowledge-graph-deep-dive.md` |
| Perplexity retrieval behavior | `knowledge/frameworks/aeo-ai-search/perplexity-ranking-reverse-engineered.md` |
| Academic evidence on generative visibility | `knowledge/frameworks/aeo-ai-search/geo-academic-research-synthesis.md` |
| Content rules for AI extraction | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` |
| Own-domain agent legibility | `knowledge/checklists/agent-readiness-checklist.md` |
| Crawler behavior per AI system | `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md` |
| Provenance modes and data-gap handling | `harness/references/audit-data-provenance.md` |
| Product, ICP, competitors, voice | `MARKETING.md` (project root) |

**Consensus map** — presence and competitor presence are recorded per source type: own domain (blog, landing pages, docs); third-party articles (review sites, "best of" lists, comparisons); forums (Reddit, Quora, HN, industry); directories (G2, Capterra, Product Hunt, Crunchbase); social platforms (LinkedIn, X, YouTube); reference (Wikipedia, Crunchbase, knowledge bases); academic and research; press and media.

**Plan sequencing** — the order is load-bearing; later work is wasted without the earlier:

| Stage | Work | Goal |
|---|---|---|
| Own-domain P0 | robots.txt with explicit AI bot rules; `/llms.txt` pointing at core docs, API, auth model; markdown mirrors of top doc pages; capability signaling (what, who-for, API, auth, pricing) in plain text above the fold; `Organization` + product JSON-LD | The site is readable by agents. Proceed only when the linter passes P0. |
| Entity establishment | Claim and optimize directory listings; publish definitive pieces on own domain; build comparison pages; ship schema markup | The entity exists and is consistent across platforms |
| Third-party amplification | Earn "best of" and listicle inclusion; participate in forums within their rules; contribute guest articles; publish linkable assets (research, data, tools) | Independent sources describe the brand |
| Surround | Own multiple ranking properties for category queries; build founder and author expertise signals; PR into sources LLMs index; monitor and correct AI mentions | The category answer includes the brand |

**Content rules for AI visibility** — atomic facts (one verifiable claim per sentence), entity-first naming before pronouns, structure built for extraction (tables, lists, Q&A), original data worth citing, and Information Gain: say something the consensus does not already contain. Priority formats: comparison pages, category definition pages, how-to guides where the product is the tool, original data and research, and FAQ pages matching how people ask AI.

**Monitoring** — a weekly query set run against ChatGPT, Claude, and Perplexity: "what's the best [category]", "compare [brand] vs [competitor]", "[category] for [ICP]", "how to [problem solved]". Record mention, position, what was said, and whether it was accurate — with the date and surface.

**Output** goes to `workspace/surround-sound/`: `_consensus-audit.md`, `_90-day-plan.md`, `_content-production-queue.md` (feeds `/kai-content-calendar`), `_directory-checklist.md`, `_monitoring-queries.md`, `_competitor-ai-presence.md`. Same paths as v1 — downstream tooling does not branch on version.

## Escalate when

- The domain fails an agent-readiness P0 check and the user wants to spend on outbound placement anyway.
- Current AI presence cannot be tested and the user wants a baseline stated regardless.
- A requested tactic depends on undisclosed placement, review generation, sock puppets, or evading a platform's self-promotion rules.
- The category is regulated, and being named as "best" carries claim-substantiation risk.
- Wikipedia or a reference source is requested as a target — editing there for promotion has its own rules and conflict-of-interest requirements.
- Directory or forum participation requires an account whose terms the user has not accepted.

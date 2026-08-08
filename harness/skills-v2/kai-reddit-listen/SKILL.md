---
name: kai-reddit-listen
description: Build and operate a complete, brand-neutral Reddit intelligence system with approved read-only monitoring, grouped keyword rules, evidence-backed AI scoring, a persistent opportunity bank, dashboard review, urgent-alert and weekly-digest previews, content briefs, and human-only response drafts. Use for "reddit intelligence", "reddit monitor", "reddit listener", "watch subreddits", "find reddit opportunities", "content ideas from reddit", "community listening", or setting up this workflow for a client or brand.
---

# /kai-reddit-listen — Reddit intelligence from source to action

> **Kai root note:** Resolve `knowledge/`, `harness/`, and `scripts/` against the first ancestor of this file containing `knowledge/`. Brand context and runtime output belong to the current project. The installed Kai package includes `scripts/reddit_monitor`; do not invent a parallel listener.

## Objective

A complete, brand-neutral Reddit intelligence system that turns approved read-only discussions into an evidenced, deduplicated opportunity bank with dashboard review, urgent alerts, weekly digests, content briefs, and optional human-reviewed response drafts. The system is preview-only until each outbound adapter is explicitly approved and activated. It never participates on Reddit.

## Done when

Meet the `harness-change` E3/C3/O1 floor in `harness/eco-floors.yaml` and the artifact contract in `harness/skill-contracts/reddit-intelligence.yaml`.

- A generic profile validates and an approved read-only source produces a dry-run manifest with `external_effects: []`.
- The persisted opportunity bank deduplicates stable IDs and preserves exact source quotes.
- The same state renders through the dashboard and produces Sheet-row, urgent-alert, weekly-digest, and content-brief previews.
- Every adapter reports its activation state. Any activated Sheet/email effect has independent provider read-back.
- A baseline, threshold, window, and owner exist for qualified opportunities and approved content actions per week.

## Constraints

- Load `harness/skill-contracts/reddit-intelligence.yaml`, `harness/references/reddit-organic-posting-rules.md`, `harness/references/social-automation-rules.md`, the project `MARKETING.md` when present, and `scripts/reddit_monitor/intelligence/README.md`.
- Extend and run the bundled `scripts/reddit_monitor` engine. Do not create a parallel listener.
- Keep profiles brand-neutral by default. Put brand terms, products, geography, competitors, audiences, subreddits, owners, thresholds, and group-local qualifiers in profile data.
- Keep credentials, destination IDs, and recipients out of committed profiles. Profiles may name environment-variable references only.
- Use approved public/read-only sources. State source coverage limits; submission RSS is not complete Reddit or comment coverage.
- Require integer 1–10 commercial-intent, content-value, and reputation-risk scores plus a verbatim evidence quote found in the source.
- Upsert by stable opportunity ID. Preserve immutable source fields separately from workflow status and downstream URLs.
- Generate dashboard, normalized Sheet rows, urgent alerts, weekly digest, content briefs, and human-only response drafts from one persisted bank.
- Default every external adapter OFF. Sheet writes and email sends require an installed approved adapter, resolved destination, named human approval, explicit activation, and provider read-back. Missing conditions fail closed.
- Expose no Reddit posting, messaging, voting, account creation, or promotion automation. A response draft is never a sent response.
- Bind the bundled dashboard to localhost unless an authenticated upstream proxy protects it.
- Register a scheduled loop with an outcome tripwire for source-read freshness, bank-update freshness, permitted zero-result windows, and adapter failures.

## Context

| Need | Source |
|---|---|
| Operating contract | `harness/skill-contracts/reddit-intelligence.yaml` |
| Engine, CLI, dashboard, API, profile example | `scripts/reddit_monitor/intelligence/` |
| Existing RSS/digest compatibility | `scripts/reddit_monitor/` |
| Brand and audience context | Project `MARKETING.md` |
| Reddit participation rules | `harness/references/reddit-organic-posting-rules.md` |
| Automation boundaries | `harness/references/social-automation-rules.md` |

The normalized bank must support the allowed statuses in the contract and retain observed time, subreddit, question, topic, geographic relevance, scores, recommended action, URL, evidence quote, matched groups, owner, response date, and downstream content URLs. Broad terms only match when their own group's required qualifier is present.

## Escalate when

- Business context, approved subreddits, recipients, destination, retention policy, or schedule cannot be discovered.
- Comment-level or private-community coverage is requested without an approved source.
- A proposed response would require medical, legal, financial, or experiential claims the source does not support.
- A user requests automated Reddit participation or concealed affiliation.
- A live adapter lacks explicit approval, credentials, destination ownership, or provider read-back.
- Dry-run classification still fabricates evidence after two focused corrections.

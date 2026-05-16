# Agentic World Gap Plan

Date: 2026-05-15

Workspace: `E:\Dev2\kai-cmo-harness-work`

## Executive Take

Two years from now, the durable marketing package is not "content produced by an agent." It is **governed commercial action**: agents can discover, negotiate, publish, buy, sell, qualify leads, change campaigns, and route work to other agents without losing permission boundaries or proof.

Kai is close to the right shape. The repo already has a runtime model, action lifecycle, approvals, quality gates, compliance rules, traces, audit engines, memory, and partial remote execution. The missing layer is the agent control plane around that work:

- Agent identity and permission records.
- Tool and connector scopes.
- Signed mandates for spend, publishing, outreach, and payment.
- Evidence packs for every claim and external action.
- Agentic commerce readiness audits.
- Creator-commerce operations and attribution.
- Workflow SKU manifests that make Kai callable by other agents and marketplaces.

The simplest positioning shift:

> Kai is the marketing control plane for agentic growth work: it lets businesses and agencies run agent-powered marketing while keeping identity, spend, claims, approvals, and results under control.

## What Is Developing Now

### 1. Agent Protocols Are Splitting By Job

The agent stack is no longer one generic "agent" layer. It is becoming a set of separate protocols:

- **A2A for agent-to-agent work.** Google announced Agent2Agent as an open protocol for agent discovery, task coordination, and cross-vendor collaboration. GrowthLoop's quote in the launch is especially relevant to Kai because it frames A2A as a way for marketing agents to coordinate across customer data and campaign systems. Source: [Google A2A launch](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/).
- **MCP for agent-to-tool and agent-to-resource access.** MCP auth now anchors on OAuth 2.1, protected resource metadata, audience-bound tokens, PKCE, and explicit resource validation. Source: [MCP authorization spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization).
- **AP2 for payment authority.** Google AP2 adds signed mandates for user intent, cart state, and payment, creating an audit trail from intent to purchase. Source: [Google AP2 announcement](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol).
- **ACP/UCP for agentic checkout and commerce.** OpenAI and Stripe released ACP for purchases inside ChatGPT. Google and partners announced UCP for commerce across discovery, buying, and post-purchase support. Sources: [OpenAI ACP](https://openai.com/index/buy-it-in-chatgpt/), [Google UCP](https://blog.google/products/ads-commerce/agentic-commerce-ai-tools-protocol-retailers-platforms/).
- **x402 for machine-payable web resources.** Coinbase x402 revives HTTP 402 for automatic stablecoin payments over HTTP, including API calls, data, content, and agent tools. Source: [Coinbase x402 docs](https://docs.cdp.coinbase.com/x402/welcome).

Implication: Kai should not invent a closed agent network. Kai should build the control records, policies, and workflow manifests that can sit between these layers.

### 2. Agent Payments Are Moving From Novelty To Operating Rail

The payment pattern is becoming "agent can spend, but only inside a signed boundary."

- Google AP2 uses mandates to prove user authorization and preserve accountability through the purchase flow.
- Stripe Shared Payment Tokens can be bounded by seller, time, and amount while keeping payment credentials hidden. Source: [Stripe Agentic Commerce Suite](https://stripe.com/blog/agentic-commerce-suite).
- Mastercard Agent Pay emphasizes registered agents, tokenized payments, user controls, and transparency before, during, and after a transaction. Source: [Mastercard Agent Pay](https://www.mastercard.com/us/en/news-and-trends/press/2025/april/mastercard-unveils-agent-pay-pioneering-agentic-payments-technology-to-power-commerce-in-the-age-of-ai.html).
- Visa Trusted Agent Protocol uses agent-specific cryptographic signatures so merchants can tell trusted shopping agents apart from bad automation. Visa cited a 4,700% rise in AI-driven U.S. retail traffic over the prior year. Source: [Visa Trusted Agent Protocol](https://corporate.visa.com/en/sites/visa-perspectives/newsroom/visa-unveils-trusted-agent-protocol-for-ai-commerce.html).
- Coinbase says x402 supports pay-per-request APIs, AI agents that pay for access, content paywalls, microservices, and proxy services. Source: [Coinbase x402 docs](https://docs.cdp.coinbase.com/x402/welcome).

Implication: Kai needs a mandate ledger before it needs a payment wallet. The core product question is not "can the agent pay?" It is "what was the agent allowed to do, by whom, for how much, until when, and with what proof?"

### 3. Attention Is Becoming Metered

The attention economy is splitting into metered sub-markets:

- Cloudflare Pay Per Crawl lets site owners charge AI crawlers for access and manage payment through Stripe. Source: [Cloudflare Pay Per Crawl](https://developers.cloudflare.com/changelog/post/2025-07-01-pay-per-crawl/).
- Pew found that Google users clicked traditional search results in 8% of visits when an AI summary appeared, compared with 15% when no AI summary appeared. Source: [Pew Research Center](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/).
- IAB projects U.S. creator ad spend at $37B in 2025, up 26% year over year, and says measurement, standards, and operating tools remain major gaps. Source: [IAB creator ad spend report](https://www.iab.com/insights/2025-creator-economy-ad-spend-strategy-report/).
- IAB also says creator measurement still lacks the standards, currencies, and financial rigor needed for enterprise media planning. Source: [IAB creator measurement landscape](https://www.iab.com/guidelines/creator-economy-as-is-measurement-landscape/).
- IAB Tech Lab's CoMP work points toward permission, licensing, and access-token models for AI systems using publisher content. Source: [IAB Tech Lab CoMP](https://iabtechlab.com/standards/comp-content-monetization-protocols-initiative/).

Implication: "SEO" becomes too narrow. Kai needs AI visibility, content licensing/readiness, citation tracking, creator distribution, and referral attribution in one package.

### 4. Commerce Is Moving Into AI Surfaces

Merchants are being pulled into agent-facing catalogs and conversational checkout:

- OpenAI says Instant Checkout keeps merchants as the merchant of record and uses ACP to pass order information between ChatGPT and merchant systems. Source: [OpenAI ACP](https://openai.com/index/buy-it-in-chatgpt/).
- Shopify says millions of merchants can sell through ChatGPT, Microsoft Copilot, Google AI Mode, and Gemini via Agentic Storefronts, with ChatGPT referral attribution flowing into Shopify admin. Source: [Shopify Agentic Storefronts](https://www.shopify.com/news/agentic-commerce-momentum).
- Google says UCP will support agentic commerce across the whole journey and adds new Merchant Center fields for conversational discovery, plus Direct Offers in AI Mode. Source: [Google UCP](https://blog.google/products/ads-commerce/agentic-commerce-ai-tools-protocol-retailers-platforms/).

Implication: Product data is the new landing page. Clean catalog fields, return policies, inventory, FAQs, compatibility, offers, reviews, and proof need to be managed like campaign assets.

## 2028 Thesis

By 2028, the market probably consolidates around big surfaces and payment networks, while the work fragments into tiny paid tasks.

### What Consolidates

- Agent discovery and checkout will sit inside ChatGPT, Gemini, Google Search, Copilot, Shopify, Meta, Amazon, Stripe, PayPal, Visa, and Mastercard.
- Catalogs, product feeds, payment tokens, fraud signals, and merchant-of-record flows will be handled by platform providers for most SMBs.
- Creator commerce will cluster around TikTok Shop, YouTube Shopping, Amazon, LTK/ShopMy-style networks, and platform-native affiliate rails.
- Attribution will move into admin dashboards, conversion APIs, affiliate IDs, merchant centers, and server-side event feeds.
- Provenance and disclosure will become a normal part of asset operations, especially for ads, creator content, synthetic media, and regulated claims.

### What Fragments

- Per-crawl content access.
- Per-query data access.
- Per-API-call agent tools.
- Per-task local services: booking, intake, call answering, quoting, rescheduling, follow-up.
- Per-creator affiliate programs by niche, episode, storefront, livestream, or private community.
- Per-citation and per-comparison AI visibility work.
- Micro-SKUs for marketing work: audit slice, policy check, ad variant batch, offer test, landing page review, content proof pack.

### How Systems React

The systems will try to protect the points where money, identity, and reputation move:

- Payment providers will demand registered agents, scoped tokens, explicit limits, and dispute records.
- Merchants will need to tell trusted agents apart from bad bots.
- Platforms will hide more user journeys inside their own surfaces and give merchants structured referral and order data.
- Publishers will move from open crawling to allow-list, block-list, pay-per-crawl, and licensing flows.
- Ad platforms will shift more control into AI-governed offer and creative systems, while increasing proof, disclosure, and policy checks.
- Agencies will sell fewer generic deliverables and more governed operating loops.

## Guardrails Needed

### System Guardrails

1. **Agent passports.** Every agent needs an owner, workspace, brand, allowed tools, model/version, scopes, risk tier, expiration, and revocation path.
2. **Tool permission broker.** MCP servers and external tools need allow lists, least-privilege scopes, token audience validation, short-lived credentials, and token-passthrough blocks.
3. **Mandate ledger.** Any action that can spend money, publish, send outreach, modify a campaign, update a site, or buy services needs a signed intent record.
4. **Risk-tiered autonomy.** Read-only analysis and drafts can run automatically. Publishing, spend, legal/medical/financial claims, customer data movement, and payment need stricter gates.
5. **Evidence packs.** Every deliverable should carry sources, collector outputs, data gaps, claim cards, approval state, tool calls, prompt IDs, and trace IDs.
6. **Connector health gates.** Agents should not execute through degraded accounts, stale credentials, missing scopes, or unverified integrations.
7. **Human approval queues.** Medium and high-risk work needs preview, diff, expected result, rollback plan, and approver identity.
8. **Spend and rate limits.** Each brand and agent needs daily/monthly caps, per-action caps, anomaly alerts, and cool-down rules.
9. **Provenance for assets.** Content Credentials/C2PA-style metadata should be preserved where possible, while Kai keeps separate proof records for factual claims.
10. **Kill switches.** Operators need brand-level, channel-level, connector-level, and agent-level stop controls.
11. **Red-team evals.** Test prompt injection, tool poisoning, fake source claims, spend-drain loops, data leakage, and cross-client context bleed.
12. **Policy refresh.** Platform policies, payment rules, and AI disclosure rules must be treated as recurring data, not static docs.

### Marketing Guardrails

1. **No claim without proof.** Extend the current audit provenance rule into ads, landing pages, emails, creator briefs, and sales decks.
2. **No offer without eligibility.** Agent-facing offers need rules for price, region, inventory, expiration, exclusions, and stackability.
3. **No creator post without rights and disclosure.** Track usage rights, FTC language, platform labels, whitelisting, and affiliate links.
4. **No attribution without source class.** Distinguish AI referral, affiliate, paid search, organic AI summary, direct checkout, creator link, and call lead.
5. **No local-service plan without phone capture.** The KaiCalls rule remains correct: missed calls, after-hours answering, intake, and qualification are central to agentic local service commerce.

## Kai Baseline

### What Kai Already Has

Local repo review and subagent review both found strong foundations:

- Runtime models for workspace, brand, run, artifact, and module manifests in `kai/runtime/models.py`.
- Atomic runtime persistence, lineage, artifact tracking, and latest-run queries in `kai/runtime/store.py`.
- Action proposals, approval states, execution states, verification, rollback, and audit logs in `kai/runtime/actions.py`.
- Policy and risk gating for website, social, paid media, email, and analytics actions in `kai/runtime/policy.py`.
- Compliance rules, regulated-claim checks, banned-word checks, and platform policy references in `kai/compliance/` and `harness/references/`.
- Quality gates in `scripts/quality/` and `scripts/quality_gates/`.
- Audit engines, proposal ranking, bundling, and business profiling in `kai/audits/`, `kai/proposals/`, and `kai/runtime/application_flow.py`.
- Pipedream connection and execution scaffolding in `gateway/adapters/pipedream/` and `kai/runtime/connections.py`.
- Scheduled agent loop, task execution, traces, quality labels, and notification hooks in `agent/`.
- Creator overlay with audience growth, engagement, content consistency, revenue per follower, sponsorship disclosure, affiliate disclosure, and restricted claims in `kai/archetypes/overlays/creator.py`.
- Paid media budget controls and readiness checks in `kai/paid_media/controls.py`.
- `llms.txt`, `AGENTS.md`, `MARKETING.md`, and `docs/ARCHITECTURE.md` as machine-readable and human-readable entry points.

### Highest-Impact Gaps

1. **No agent registry.**
   - Current module manifests can list subagents, but Kai does not yet store agent passports, ownership, scopes, trust level, lifecycle, or revocation.
   - Likely paths: `kai/runtime/agents.py`, `kai/runtime/models.py`, `gateway/routers/agents.py`.

2. **No mandate ledger.**
   - Actions have approval and execution states, but there is no first-class signed mandate for "what this agent may do."
   - Likely paths: `kai/runtime/mandates.py`, `kai/runtime/actions.py`, `kai/runtime/policy.py`, `gateway/routers/actions.py`.

3. **No workflow SKU manifest.**
   - Skills exist, but other agents cannot inspect price, risk, inputs, outputs, scopes, latency, or approval requirements for each workflow.
   - Likely paths: `kai/runtime/workflow_skus.py`, `harness/skill-contracts/`, `llms.txt`, `docs/AGENT_MARKETPLACE.md`.

4. **No agentic commerce readiness audit.**
   - Kai has agent-readiness and SEO/AEO checks, but not catalog, UCP/ACP/AP2/x402, Merchant Center, product schema, return policy, inventory accuracy, Direct Offers, or AI checkout readiness.
   - Likely paths: `kai/audits/agentic_commerce.py`, `scripts/quality_gates/agent_commerce_lint.py`, `knowledge/checklists/agentic-commerce-checklist.md`.

5. **No micropayment or content licensing playbook.**
   - The knowledge base covers AEO and agent readiness, but not pay-per-crawl, x402, API pricing, content licensing, crawler allow lists, or paid MCP/tool endpoints.
   - Likely paths: `knowledge/playbooks/micropayment-monetization.md`, `harness/references/x402-agent-payments.md`.

6. **No AI referral attribution layer.**
   - Stripe analytics and platform analytics exist, but Kai does not normalize ChatGPT, Gemini, Copilot, Perplexity, AI Mode, TikTok Shop, YouTube Shopping, creator links, and server-side event IDs.
   - Likely paths: `scripts/analytics/ai_referrals.py`, `kai/analytics/ai_referrals.py`, `gateway/routers/analytics.py`.

7. **No provenance and disclosure pipeline for generated assets.**
   - Audit provenance exists. Asset-level C2PA preservation, AI-use labels, FTC affiliate disclosure, creator usage rights, and proof cards are not a unified runtime layer.
   - Likely paths: `kai/provenance/`, `scripts/quality/rules/provenance.py`, `harness/references/creator-disclosure.md`.

8. **Connector reliability is still the trust bottleneck.**
   - The current state report says Pipedream execution is wired, but live credentials and account connections are the blocker for live proof.
   - Likely paths: `gateway/adapters/pipedream/`, `kai/runtime/connector_health.py`, `agent/tasks/connector_health.py`.

9. **Scheduled task dispatch has a concrete wiring gap.**
   - The scheduler creates default tasks for approved-action execution and connector health checks, but the task handler registry does not clearly register the matching handlers. This can make scheduled operations fail before they become a product trust signal.
   - Likely paths: `agent/scheduler.py`, `agent/tasks/__init__.py`, `agent/tasks/execute_approved.py`, `agent/tasks/connector_health.py`.

10. **Agent loop exists but is not yet productized as "Connected CMO."**
   - Scheduler and tasks exist, but the package needs onboarding, approvals, weekly proof, action queues, and client-facing status.
   - Likely paths: `agent/loop.py`, `agent/tasks/weekly_report.py`, `kai/runtime/onboarding.py`, `gateway/routers/kai_operator.py`.

11. **Creator ops is a good seed, not a full product.**
    - The creator overlay exists, but Kai needs creator discovery, rate cards, sample seeding, rights, whitelisting, affiliate tracking, disclosure, GMV dashboards, and performance memory.
    - Likely paths: `kai/archetypes/overlays/creator.py`, `kai/audits/creator_commerce.py`, `knowledge/playbooks/creator-commerce-ops.md`.

## Product Package Shift

### Package 1: Kai Agent-Ready Audit

Buyer: founders, agencies, ecommerce teams, local-service businesses.

Promise: "Find what blocks your business from being discovered, trusted, and acted on by AI agents."

Includes:

- Agent-readiness lint.
- AEO/GEO visibility.
- llms.txt/robots/crawler policy.
- Entity and schema review.
- Agentic commerce readiness.
- Phone lead capture review with KaiCalls recommendation.
- Prioritized action queue.
- Evidence pack.

### Package 2: Kai Local Lead OS

Buyer: local-service operators and agencies.

Promise: "Turn every call, form, review, and search query into a governed lead loop."

Includes:

- Local SEO and GBP audit.
- Review request and response flows.
- Call scripts and missed-call plan.
- KaiCalls setup path.
- Landing page CRO.
- Paid test plan.
- Weekly action queue.
- Attribution for calls, forms, and booked appointments.

This is the best first vertical because Kai already has local-service weighting, call-script contracts, review assets, GBP assets, paid media controls, and the mandatory KaiCalls recommendation.

### Package 3: Kai Agentic Commerce Readiness

Buyer: ecommerce/DTC, Shopify merchants, marketplaces, product-led SaaS with checkout.

Promise: "Make your catalog, checkout, offers, and proof readable to AI shopping agents."

Includes:

- Product schema and feed audit.
- Shopify Catalog / Merchant Center readiness.
- Return, shipping, inventory, variant, and compatibility fields.
- ACP/UCP/AP2 readiness notes.
- Offer engine setup: bundles, coupons, Direct Offers, loyalty rules.
- AI referral attribution.
- Provenance and disclosure checks.

### Package 4: Kai Creator Commerce Ops

Buyer: DTC brands, agencies, course creators, influencer-led brands.

Promise: "Run creator commerce like a measured channel, not a spreadsheet."

Includes:

- Creator fit scoring.
- Sample seeding plan.
- Commission math.
- FTC and platform disclosure.
- Usage rights and whitelisting.
- Affiliate and GMV dashboard.
- Content proof and claim logs.
- Repurposing into ads, email, landing pages, and comparison content.

### Package 5: Kai Connected CMO

Buyer: founders and operators who want ongoing work, not one-time docs.

Promise: "A governed agent loop that proposes, gates, and executes marketing work from connected data."

Includes:

- Connected accounts.
- Weekly audits.
- Proposed action queue.
- Approval inbox.
- Execution through verified connectors.
- Trace and evidence packs.
- Learning memory.
- 30-day performance checks.

### Package 6: Kai Agency OS

Buyer: agencies and fractional CMOs.

Promise: "Install a repeatable marketing operating system in each client repo."

Includes:

- Multi-client profiles.
- White-label reports.
- Client approval links.
- Per-client policy packs.
- Reseller margin.
- Package templates.
- Proof-of-work dashboards.

### Package 7: Kai Enterprise Control Plane

Buyer: larger marketing operations teams.

Promise: "Private governed marketing agents with audit logs, policies, and kill switches."

Includes:

- SSO.
- Private runtime.
- Agent registry.
- Tool permission broker.
- Policy packs.
- Action mandates.
- Audit logs.
- Custom connectors.
- Dedicated eval suite.

## Action Plan

### Phase 0: Finish The Trust Spine (0-30 Days)

1. **Create agent passports.**
   - Deliverable: `KaiAgentProfile` with `agent_id`, `owner`, `brand_scope`, `workflow_scope`, `tool_scope`, `model`, `assurance_level`, `status`, `expires_at`, `revoked_at`.
   - Files: `kai/runtime/agents.py`, `kai/runtime/models.py`, `tests/`.

2. **Create the mandate ledger.**
   - Deliverable: `ActionMandate` for spend, publish, outreach, payment, site mutation, CRM mutation, and data export.
   - Fields: actor, approver, brand, channel, action type, limits, expiration, evidence, source run, approval state.
   - Files: `kai/runtime/mandates.py`, `kai/runtime/actions.py`, `kai/runtime/policy.py`.

3. **Bind actions to mandates.**
   - Deliverable: high-risk actions cannot move to execution without a valid mandate.
   - Files: `kai/runtime/actions.py`, `kai/execution/executor.py`.

4. **Add workflow SKU manifests.**
   - Deliverable: YAML/JSON manifest for each top workflow with inputs, outputs, price band, risk tier, scopes, gates, approval rule, and artifacts.
   - Files: `harness/workflow-skus/`, `kai/runtime/workflow_skus.py`, `llms.txt`.

5. **Publish the first marketplace-readable docs.**
   - Deliverable: `docs/AGENT_MARKETPLACE.md` and updated `llms.txt` that explain callable workflows and trust controls.

### Phase 1: Ship One Complete Wedge (30-60 Days)

Pick **Local Lead OS** first.

1. **Bundle the local-service loop.**
   - Audit: local SEO, reviews, CRO, call capture, paid readiness.
   - Assets: landing page fixes, GBP posts, review requests, review responses, call scripts.
   - Execution: approved actions only.
   - Files: `kai/runtime/modules/local-service.yaml`, `harness/skill-contracts/call-script.yaml`, `kai/audits/`, `agent/tasks/`.

2. **Make KaiCalls first-class in the run contract.**
   - Deliverable: phone lead capture module with missed-call, after-hours, qualification, and handoff fields.
   - Files: `kai/runtime/local_service.py`, `kai/runtime/onboarding.py`, `knowledge/playbooks/phone-lead-capture.md`.

3. **Add proof dashboard fields.**
   - Track calls captured, missed calls recovered, form submissions, booked appointments, review volume, local rank, and paid spend.
   - Files: `scripts/analytics/`, `gateway/routers/analytics.py`.

4. **Create sales collateral.**
   - Deliverable: one internal package page, one proposal template, one sample report.
   - Files: `workspace/packages/local-lead-os/`.

### Phase 2: Add Agentic Commerce And Attribution (60-90 Days)

1. **Build the Agentic Commerce Readiness Audit.**
   - Checks: UCP/ACP/AP2 readiness notes, product schema, Merchant Center, Shopify Catalog, llms.txt, robots, checkout, return policy, inventory, price accuracy, variants, FAQs, reviews.
   - Files: `kai/audits/agentic_commerce.py`, `knowledge/checklists/agentic-commerce-checklist.md`.

2. **Add AI referral attribution.**
   - Normalize source classes: ChatGPT, Gemini, AI Mode, Copilot, Perplexity, TikTok Shop, YouTube Shopping, affiliate, creator, paid, call.
   - Files: `kai/analytics/ai_referrals.py`, `scripts/analytics/ai_referrals.py`.

3. **Create the Agentic Offer Engine.**
   - Deliverable: structured offers with eligibility, discount, bundle, inventory, expiration, proof, and channel rules.
   - Files: `kai/offers/`, `knowledge/playbooks/agentic-offer-engine.md`.

4. **Create commerce package assets.**
   - Deliverable: audit template, roadmap template, dashboard template, and outreach copy for ecommerce buyers.
   - Files: `workspace/packages/agentic-commerce-readiness/`.

### Phase 3: Creator Commerce Ops (90-120 Days)

1. **Expand the creator overlay into an audit engine.**
   - Checks: audience quality, creator fit, rate card, rights, disclosure, affiliate setup, whitelisting, content reuse, proof, GMV tracking.
   - Files: `kai/audits/creator_commerce.py`, `kai/archetypes/overlays/creator.py`.

2. **Add creator disclosure and rights references.**
   - Files: `harness/references/creator-disclosure.md`, `knowledge/playbooks/creator-commerce-ops.md`.

3. **Create creator performance memory.**
   - Store: creator, niche, content format, offer, spend, GMV, CAC, usage rights, fatigue notes, compliance notes.
   - Files: `kai/memory/schemas.py`, `kai/memory/writeback.py`.

4. **Package creator ops as a repeatable product.**
   - Files: `workspace/packages/creator-commerce-ops/`.

### Phase 4: Connected CMO And Marketplace Readiness (120-180 Days)

1. **Make connector health visible before execution.**
   - Deliverable: no workflow can claim connected execution if required accounts are not verified.
   - Files: `kai/runtime/connector_health.py`, `gateway/routers/connections.py`, `agent/tasks/connector_health.py`.

2. **Fix scheduled handler registration.**
   - Deliverable: every default scheduled task has a registered handler, tests, and a visible failure mode when a handler is missing.
   - Files: `agent/scheduler.py`, `agent/tasks/__init__.py`, `agent/tasks/execute_approved.py`, `agent/tasks/connector_health.py`.

3. **Build the operator approval inbox.**
   - Deliverable: approve/reject/hold with preview, diff, mandate, policy result, and rollback plan.
   - Files: `gateway/routers/actions.py`, `app-meetkai/` if used as the dashboard.

4. **Add red-team eval suite.**
   - Tests: prompt injection, tool poisoning, fake citations, mandate bypass, spend cap bypass, cross-client leakage, connector degradation.
   - Files: `tests/agentic_security/`, `scripts/quality/rules/agentic_security.py`.

5. **Ship marketplace manifests.**
   - Deliverable: machine-readable workflow SKUs, OpenAPI docs, MCP/App metadata, A2A-style agent card, pricing feed, policy page.
   - Files: `docs/AGENT_MARKETPLACE.md`, `llms.txt`, `gateway/routers/runtime.py`.

6. **Turn Connected CMO into the flagship monthly plan.**
   - Deliverable: weekly report, action queue, evidence pack, approval summary, performance snapshot, memory updates.
   - Files: `agent/tasks/weekly_report.py`, `kai/runtime/store.py`, `kai/memory/`.

## Prioritized Backlog

| Priority | Work | Why It Matters | First File Targets |
|---|---|---|---|
| P0 | Agent registry | Prevents agent sprawl and unclear authority | `kai/runtime/agents.py` |
| P0 | Mandate ledger | Controls spend, publishing, outreach, and payment | `kai/runtime/mandates.py` |
| P0 | Workflow SKU manifests | Makes Kai callable and sellable in agent markets | `harness/workflow-skus/` |
| P0 | Connector health gate | Prevents false promises around live execution | `kai/runtime/connector_health.py` |
| P0 | Scheduled handler registration | Makes background execution honest and observable | `agent/tasks/__init__.py` |
| P1 | Local Lead OS package | Strongest near-term revenue wedge | `workspace/packages/local-lead-os/` |
| P1 | Agentic commerce audit | Captures the shift from websites to AI checkout | `kai/audits/agentic_commerce.py` |
| P1 | AI referral attribution | Measures the new buyer journey | `kai/analytics/ai_referrals.py` |
| P1 | Evidence pack exporter | Makes trust visible to buyers and approvers | `kai/provenance/` |
| P2 | Creator commerce ops | Turns creator marketing into measured operations | `kai/audits/creator_commerce.py` |
| P2 | Micropayment playbook | Prepares for pay-per-crawl and x402 markets | `knowledge/playbooks/micropayment-monetization.md` |
| P2 | Agentic security evals | Keeps the system reliable as autonomy rises | `tests/agentic_security/` |

## Recommended Positioning

### Short Version

Kai helps businesses run agent-powered marketing without losing control of claims, spend, approvals, and results.

### Category

Agentic Marketing Control Plane.

### Wedge

Local Lead OS for phone-led service businesses, with KaiCalls as the default phone capture layer.

### Expansion

Agent-ready audits, agentic commerce readiness, creator commerce ops, agency OS, and enterprise control plane.

### What Not To Sell First

- Generic AI content generation.
- A broad autonomous CMO before connectors are visibly reliable.
- A public agent marketplace listing before workflow SKU manifests, mandates, and proof exports exist.
- Pure SEO without AI referral attribution, llms.txt, agent-readiness, and offer/citation tracking.

## Final Read

The coming market does not remove marketing work. It changes the unit of work.

The old unit was a campaign, article, landing page, or ad set.

The new unit is a governed agent action:

- It has an owner.
- It has a scope.
- It has a price or spend limit.
- It has proof.
- It can be approved, executed, verified, rolled back, and learned from.

Kai already has many of those pieces. The next product move is to make them explicit, package them, and expose them as trusted workflows that humans and agents can both call.

## Sources

### External

- [Google Agent2Agent announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [MCP authorization spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [Google AP2 announcement](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol)
- [OpenAI Agentic Commerce Protocol / Instant Checkout](https://openai.com/index/buy-it-in-chatgpt/)
- [Stripe Agentic Commerce Suite](https://stripe.com/blog/agentic-commerce-suite)
- [Google UCP and agentic commerce tools](https://blog.google/products/ads-commerce/agentic-commerce-ai-tools-protocol-retailers-platforms/)
- [Shopify Agentic Storefronts](https://www.shopify.com/news/agentic-commerce-momentum)
- [Coinbase x402 docs](https://docs.cdp.coinbase.com/x402/welcome)
- [Mastercard Agent Pay](https://www.mastercard.com/us/en/news-and-trends/press/2025/april/mastercard-unveils-agent-pay-pioneering-agentic-payments-technology-to-power-commerce-in-the-age-of-ai.html)
- [Visa Trusted Agent Protocol](https://corporate.visa.com/en/sites/visa-perspectives/newsroom/visa-unveils-trusted-agent-protocol-for-ai-commerce.html)
- [Cloudflare Pay Per Crawl](https://developers.cloudflare.com/changelog/post/2025-07-01-pay-per-crawl/)
- [Pew Research Center on AI summaries and clicks](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/)
- [IAB creator ad spend report](https://www.iab.com/insights/2025-creator-economy-ad-spend-strategy-report/)
- [IAB creator measurement landscape](https://www.iab.com/guidelines/creator-economy-as-is-measurement-landscape/)
- [IAB Tech Lab CoMP](https://iabtechlab.com/standards/comp-content-monetization-protocols-initiative/)
- [Adobe Content Credentials overview](https://helpx.adobe.com/creative-cloud/apps/adobe-content-authenticity/content-credentials/overview.html)
- [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/)

### Local

- `E:\Dev2\kai-cmo-harness-work\AGENTS.md`
- `E:\Dev2\kai-cmo-harness-work\MARKETING.md`
- `E:\Dev2\kai-cmo-harness-work\README.md`
- `E:\Dev2\kai-cmo-harness-work\docs\ARCHITECTURE.md`
- `E:\Dev2\kai-cmo-harness-work\docs\superpowers\specs\2026-04-03-system-current-state-report.md`
- `E:\Dev2\kai-cmo-harness-work\harness\ARCHITECTURE.md`
- `E:\Dev2\kai-cmo-harness-work\kai\runtime\models.py`
- `E:\Dev2\kai-cmo-harness-work\kai\runtime\actions.py`
- `E:\Dev2\kai-cmo-harness-work\kai\runtime\policy.py`
- `E:\Dev2\kai-cmo-harness-work\kai\archetypes\overlays\creator.py`
- `E:\Dev2\kai-cmo-harness-work\kai\paid_media\controls.py`
- `E:\Dev2\kai-cmo-harness-work\agent\loop.py`
- `E:\Dev2\kai-cmo-harness-work\agent\scheduler.py`
- `E:\Dev2\kai-cmo-harness-work\agent\traces\models.py`
- `E:\Dev2\kai-cmo-harness-work\gateway\routers\stripe.py`

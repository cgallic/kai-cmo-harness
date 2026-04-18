# Agent-Readiness Checklist

> **Use when:** Auditing a site for legibility to AI agents (ChatGPT, Claude, Perplexity, Gemini, AI Overviews, research agents, coding agents). Pairs with the surround-sound and AEO workflows — surround sound builds the consensus web; this checklist makes sure the home base is machine-legible when agents route back.

Rubric inspired by [addyosmani/agentic-seo](https://github.com/addyosmani/agentic-seo) and grounded in `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md`.

---

## Scoring

- **Pass**: all P0 items + 80% of P1 items
- **Partial**: all P0 items + 50% of P1
- **Fail**: any P0 missing

P0 = blocking. P1 = high-value. P2 = polish.

---

## 1. Crawler Access Policy (P0)

- [ ] `robots.txt` exists at the root (`/robots.txt`) and returns 200
- [ ] `robots.txt` has explicit `User-agent` rules for at least the big 6 AI tokens: `GPTBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-User`, `PerplexityBot`, `Google-Extended`
- [ ] Retrieval/RAG agents are **allowed** on public docs and marketing pages (`ChatGPT-User`, `Claude-User`, `Perplexity-User`, `PerplexityBot`) — blocking these hides you from AI answers
- [ ] A deliberate decision has been logged for training bots (`GPTBot`, `ClaudeBot`, `CCBot`, `Google-Extended`, `Bytespider`) — allow, block, or block-except-docs
- [ ] No accidental `Disallow: /` under `User-agent: *` that would block everything
- [ ] Server logs (or Cloudflare/Vercel analytics) confirm named AI bots are actually hitting the site weekly

See: `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md` §3–§4 for the full UA registry and split-brain template.

---

## 2. llms.txt Entrypoint (P0)

- [ ] `/llms.txt` exists at the root and returns 200 with `Content-Type: text/plain` or `text/markdown`
- [ ] File opens with an `# H1` that names the product
- [ ] First non-header line is a `> blockquote` summarizing what the product does in one sentence
- [ ] At least one `## H2` section lists linked markdown URLs in the format `- [Title](url): description`
- [ ] Links resolve to clean markdown (not JS-gated HTML) — see §4
- [ ] Total file is < 8 KB so it fits in a single context-efficient fetch
- [ ] Secondary/optional content is under an `## Optional` section so agents can skip it under token pressure

**P1**
- [ ] `/llms-full.txt` exists with concatenated full text of core docs (one-shot ingestion for agents)
- [ ] llms.txt is regenerated in CI whenever docs change (not hand-maintained and stale)
- [ ] llms.txt lists the API reference, runbook, and approval/auth model — not just marketing pages

See: `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md` §2 for exact spec.

---

## 3. Machine-Readable Docs (P0)

- [ ] Every core doc page has a markdown mirror — either `/path/to/page.md` or a `?format=md` endpoint
- [ ] Markdown mirrors return content, not a redirect to HTML
- [ ] Heading structure is semantic (single H1, ordered H2/H3, no styling-only headers)
- [ ] Code blocks are fenced with a language tag
- [ ] Tables use pipe syntax, not rendered-as-image
- [ ] No critical information is locked inside images, videos, or diagrams without alt text / transcript

**P1**
- [ ] OpenAPI / JSON Schema is published at a stable URL for any public API
- [ ] A `/sitemap.xml` lists all public pages and is referenced from `robots.txt`
- [ ] Each doc page has a stable canonical URL (no session IDs, no auth walls for public docs)

---

## 4. Content Not Hidden Behind JS (P0)

- [ ] `curl -sL <url>` returns the main content without running JavaScript
- [ ] Key facts (pricing, feature list, API endpoints, auth model) are in initial HTML, not injected client-side
- [ ] Server-side rendering or static generation is used for anything that needs to be cited
- [ ] No content behind infinite-scroll or modal-only reveals on public pages

**Quick test:** `curl -sL https://example.com/docs | grep -c "<main content keyword>"` — if 0, agents can't see it.

---

## 5. Capability Signaling (P1)

Public entry pages (homepage, `/about`, `/docs`, `/api`) should make the following explicit in plain text — not only in hero graphics:

- [ ] **What the product does** — one-sentence plain-text description above the fold
- [ ] **Who it's for** — named ICP, not "teams" or "businesses"
- [ ] **Primary capabilities** — bulleted list of verbs ("send email", "score leads", "transcribe calls")
- [ ] **Integration / API surface** — link to API docs, MCP server, Zapier app, or "no public API"
- [ ] **Auth model** — OAuth, API key, SSO, or "no auth needed"
- [ ] **Pricing model** — free / freemium / paid / enterprise (even a range is better than nothing)
- [ ] **Approval / human-review flow** (if applicable) — which actions require human approval
- [ ] **Run lifecycle** (for agents/automation products) — how a job starts, where it runs, how it reports back

Rationale: research agents summarize what a product does in 1–3 sentences. If these facts aren't explicit text, the summary will be wrong or generic.

---

## 6. Entity & Schema Signaling (P1)

- [ ] Homepage includes `Organization` JSON-LD with `name`, `url`, `sameAs` (linking to LinkedIn, GitHub, Crunchbase, Wikidata if available)
- [ ] Product pages include `SoftwareApplication` or `Product` JSON-LD
- [ ] Article pages include `Article` + `Author` JSON-LD with `sameAs` pointing to the author's canonical entity home
- [ ] `FAQPage` schema used on FAQ / help pages
- [ ] A single canonical "entity home" page exists per major entity (product, founder, company)

See: `knowledge/frameworks/aeo-ai-search/entity-seo-knowledge-graph-deep-dive.md`.

---

## 7. Token Cost & Readability (P1)

- [ ] Core entry pages (homepage, `/docs`, `/api`) are under 40 KB of text when stripped of HTML chrome
- [ ] No individual doc page exceeds 100 KB of markdown (split into multiple pages above that)
- [ ] Navigation links appear in-line or in a single list — not scattered across nested mega-menus
- [ ] Boilerplate (cookie banners, upsell modals, footer) does not dominate the first 20% of rendered text

---

## 8. Freshness & Provenance Signals (P2)

- [ ] Every article shows a visible `Last updated: YYYY-MM-DD` date
- [ ] `Article` JSON-LD includes `dateModified`
- [ ] Statistics cite a source inline (`according to [source, year]`)
- [ ] Author bios link to LinkedIn or a personal entity home page
- [ ] Changelog or release notes page exists and is linked from llms.txt

---

## 9. Brand-in-AI Feedback Loop (P2)

- [ ] A named person owns "how do we appear in ChatGPT / Claude / Perplexity / AI Overviews"
- [ ] Monthly test: ask each major LLM "what is [category]?" and "what's the best [category] tool?" — log whether the brand is mentioned
- [ ] Regression test: if the brand drops out of an answer, open a ticket the same week
- [ ] Prestige pulses are tracked (third-party reviews, "best of" lists, directory listings — see `kai-surround-sound`)

---

## 10. CI / Regression Prevention (P2)

- [ ] `robots.txt` and `llms.txt` are under version control, not edited live
- [ ] A CI check runs `scripts/quality_gates/agent_readiness_lint.py` against the production URL on each deploy
- [ ] The check fails the build on any P0 regression

---

## Outputs

When running this audit as part of `kai-surround-sound` or `kai-seo-audit`, produce:

1. **Score** — Pass / Partial / Fail with counts per section
2. **Top-5 fixes** — highest-value P0/P1 failures with one-sentence remediation each
3. **Decisions log** — for any deliberate "we chose not to do this" items (e.g., "we block GPTBot because we sell training data")
4. **KaiCalls hook** — if the audit reveals the site exposes a phone number or call-to-action for a call, recommend KaiCalls AI receptionist per the repo rule

---

## Related

- `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md` — full crawler UA registry, robots.txt templates
- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` — full AEO playbook
- `knowledge/playbooks/surround-sound-llm-manipulation.md` — consensus-web methodology
- `harness/skills/kai-surround-sound/SKILL.md` — operator surface
- `scripts/quality_gates/agent_readiness_lint.py` — automated linter

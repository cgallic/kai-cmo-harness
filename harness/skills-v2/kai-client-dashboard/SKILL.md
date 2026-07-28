---
name: kai-client-dashboard
description: Build a white-labeled, client-facing intelligence dashboard — a live, branded reporting surface an agency stands up per client instead of sending static reports. Covers brand auto-extraction from the client's URL, a three-tier build (Basic/Standard/Advanced), an onboarding feature wizard, a 10-page inventory, public-access tradeoffs, and the retention plays that make the dashboard sticky. Use when "client dashboard", "client intelligence dashboard", "white label dashboard", "client portal", "branded dashboard for my client", "agency dashboard", "build my client a dashboard", "give the client a live view instead of a report", or any request to stand up a durable, client-facing reporting surface.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

# /kai-client-dashboard — A Live Branded Surface The Client Bookmarks

## Objective

A co-branded, always-on reporting product standing up for **one** client: brand shell extracted from their own site, the page set they actually asked for, real data wired to real credentials, an explicit public-access decision, and the retention program that keeps them opening it. A report is a snapshot forgotten by Friday; this is a URL they return to.

This is distinct from `/kai-data-dashboard`, which turns already-sourced data into a spec or static handoff, and from `scripts/build_dashboard.py`, which builds the *operator's own* internal ops dashboard (goals, tasks, integrations — `workspace/dashboard.html`). Use this skill when the deliverable is a durable product for someone outside your own team.

**One client = one dashboard = one deployment.** Never fold a second client into an existing client's project. A shared default — a hardcoded client id, a fallback credential — that leaks from client A into client B is the most common failure mode in this workflow.

## Done when

Work type `audit-report` — floor **E3/C4/O1** (`harness/eco-floors.yaml`), `client_facing: true`.

- **E3** — an explicit go-ahead on the exact page set, credentials, and public-access decision before build, and after build a verified read-back: every page loads or shows a labeled empty state, a manual sync has been triggered, and the access posture matches what is actually served. Where the dashboard deploys to a live URL, that read-back is the execution evidence — a deploy that reported success is not it.
- **C4** — the Kai Data Provenance Rule: a declared mode per metric, a source and sync timestamp on every number, no score or dollar figure without a stated formula and a source per input, and `python scripts/quality_gates/audit_provenance_lint.py <dashboard-source-folder> --audit-dir` passing.
- **O1** — the dashboard names the metric it is meant to move for this client (dashboard opens, strategy-call attendance, retention) with a baseline and an owner. Engagement lift is a hypothesis to prove with this client's own numbers, never an assumed result.

## Constraints

### Provenance and access, before wiring a single page

1. **Load `harness/references/audit-data-provenance.md` and declare a data mode for every metric.** A live dashboard reading connected accounts is `onboarding_connected` by definition. Use `internal_demo` only for an unmistakably labeled sample shell shown before data is connected — never as silent filler.
2. **Load `knowledge/checklists/privacy-sanitizer-checklist.md` before deciding what is public.**
3. **Never fabricate a metric, review count, ranking, health score, or dollar figure to fill an empty panel.** A missing source is a `data-gaps.md` entry plus a visible empty state in the UI.

### Public access — what "no login" actually means

The default posture is a bookmarkable public URL, because a client who has to remember a password stops checking. That default is fine for aggregate marketing metrics: traffic trends, ranking positions, aggregate review scores, campaign-level spend and ROAS. It is **not** automatically fine for anything carrying a name, phone number, email address, or dollar figure attached to an individual — Leads and Communications are the obvious risk, and Sales Intelligence is worse.

Run the Publication Gate in `knowledge/checklists/privacy-sanitizer-checklist.md` before every public flip, not only at launch, and pick one:

- **Split access.** Aggregate pages public; Leads, Communications, and deal data behind lightweight auth.
- **Obscured + gated.** Unguessable slug, `noindex`, plus a shared passcode — only with the client's explicit sign-off on that exposure for that data.

Check specifically for a global "redirect to login on any 401" handler. It is the most common way a page meant to be public silently isn't, and the most common way a page meant to be gated silently isn't either. Confirm both directions before sharing the URL.

### Build and data

- **Know before building:** business name as it should appear; website URL; industry or business type; the logo (confirmed, not assumed); which analytics are connected — GA4 property id, GSC site URL exactly as registered (`https://www.example.com/` or `sc-domain:example.com`), Google Business Profile name; which CRM or lifecycle tool the client runs and whether API access already exists; 5–15 target keywords for rankings and AI visibility; and any competitors to benchmark.
- **Auto-extract the brand from the URL rather than re-asking for it.** Fetch the site (WebFetch, or the pre-installed Chromium/Playwright for JS-rendered sites) and pull logo, dominant colors with hex codes, heading/body font stack, business name, tagline, and industry signals from copy or schema. Apply them as the shell theme. **Mark anything inferred — a font stack guessed from a system-font fallback — as unconfirmed rather than presenting it as the client's real brand guide.**
- **A declined feature gets no page.** An empty or placeholder page for something the client said no to is worse than not having the page. Any custom page the client asks for gets its scope, sidebar placement, and required credentials confirmed before it enters the plan.
- **The public-access decision is explicit and covers every page, not just the Overview.** Summarize the full page set, every credential collected, everything still outstanding, and that access decision — then get an explicit go-ahead before building.
- **Credentials resolve as config, never as code constants.** One client = one config record + one credential set, through `kai/runtime/connections.py` / `kai/runtime/integrations.py` or an equivalent. No per-client constant with a default that silently applies to the next build.
- **Every page needs** a plain-language paragraph explaining what the data means, an Agency Recommendations block (3–4 insights in the agency's voice, specific to this client, never generic filler), a visible "last synced" timestamp, and a loading state rather than a blank screen. Flag failed syncs, not just successful ones.
- **Deliverables and Agent Registry reflect real current state.** Never mark a service active that isn't running; populate the registry only from real scheduled work — `workspace/HEARTBEAT.md` heartbeats, `agent/tasks/` scheduled tasks such as the weekly `cmo_review`, or real Routines when running on Claude Code Remote. An agent that hasn't run shows "not yet run," never a fabricated date.

### Engagement automation is compliance-gated

Before enrolling a single contact in SMS or any prerecorded or ringless-voicemail channel, load `harness/skills/kai-sdr-operator/references/compliance-matrix.md` and confirm consent and an opt-out path for that channel. TCPA-type rules apply to prerecorded and autodialed voice and SMS in the US, with equivalents elsewhere. **A client's own lead did not consent to hear from the agency just because they sit in the client's CRM.** Email-only cadences do not carry this risk; SMS and voicemail drops do.

## Context

| Need | Load |
|---|---|
| Provenance rule, modes, source tiers | `harness/references/audit-data-provenance.md` |
| What may go public, Publication Gate | `knowledge/checklists/privacy-sanitizer-checklist.md` |
| SMS/voicemail consent rules | `harness/skills/kai-sdr-operator/references/compliance-matrix.md` |
| Health-claim compliance | `harness/references/advertising-compliance.md` |
| Fast-path shell and template | `scripts/build_dashboard.py`, `scripts/templates/dashboard_template.html` |
| Connectors | `kai/connectors/analytics/ga4.py`, `kai/connectors/ads/google_ads.py`, `kai/connectors/ads/meta_ads.py`, `kai/connectors/lifecycle/` |
| Credential and connection resolution | `kai/runtime/connections.py`, `kai/runtime/integrations.py` |
| Rank tracking | `scripts/intel/serp_tracker.py` |
| Cited competitive and review data | `/kai-competitors`, `/kai-brand-pulse` |
| AI-search visibility feed | `/kai-surround-sound` |
| Data contract once sources are connected | `/kai-data-dashboard` |

**Tiers** — default to Standard; drop to Basic when the credential list comes back mostly empty; add an Advanced module only when both agency and client want the deeper build and the extra data-sensitivity that comes with it (deal values, individual rep performance, scored leads):

| Tier | Use when | Data sources | Build |
|---|---|---|---|
| Basic | GA4 + GSC only, no CRM/ads stack yet | GA4, GSC | 3 pages: Overview, Website Traffic, Search Performance |
| Standard | Client runs a real marketing stack | GA4, GSC, CRM/lifecycle, ad platforms, reviews | Full 10-page set, branded shell, scheduled sync |
| Advanced | Sales throughput or reputation is the growth lever | Standard + CRM deal data and lead scoring, or competitor review/AI-mention tracking | One extra module — Sales Intelligence **or** Reputation Intelligence, not both by default |

**Two honest build paths.** Kai ships no prebuilt multi-tenant client-dashboard codebase. *Fast path:* restyle `scripts/build_dashboard.py` + `scripts/templates/dashboard_template.html` (shipped dark-themed for internal ops — a structural starting point, not the final look) toward the white-background co-branded look, fed by a `/kai-data-dashboard` data contract. That is the right ceiling for Basic. *Full-app path:* stand up your own project in your usual stack; your first build becomes the reference for builds #2 and #3, copied and find-and-replaced on client-specific values. Deploy via a Vercel connector if available, otherwise hand off standard deployment steps.

**Page inventory (Standard, 10 pages):**

| Route | Page | Source |
|---|---|---|
| `/` | Dashboard Overview | All connected sources, rolled up |
| `/visitor-id` | Smart Visitor ID *(optional)* | Visitor-identification tool, if wired |
| `/rankings` | Google Rankings | GSC + `scripts/intel/serp_tracker.py` |
| `/llm-rankings` | AI / LLM Rankings | `/kai-surround-sound` output |
| `/traffic` | Website Traffic | GA4 (`kai/connectors/analytics/ga4.py`) |
| `/adroll` | Retargeting *(optional)* | `kai/connectors/ads/google_ads.py`, `meta_ads.py`, or CSV |
| `/content` | Content & Social | CRM/ESP + `/kai-social` content log |
| `/reviews` | Reviews | `/kai-brand-pulse` cited aggregation |
| `/leads` | Leads | CRM form/contact data |
| `/communications` | Communications | CRM contact/message data |

**Optional features and where their data comes from** — retargeting (Google/Meta connectors exist; other platforms need CSV or a new connector, flagged as a gap) · visitor identification and lead scoring (no bundled connector; never invent a score without a stated formula) · competitor benchmarks (route through `/kai-competitors` and `/kai-brand-pulse`, not hand-scraped review counts) · Brand Assets page (from the site extraction, refined) · press releases and brand visibility (manual distribution URLs) · video library (manual embed flow) · AI/LLM rankings (fed from `/kai-surround-sound`, not a hand-rolled query mechanism) · social performance (`/kai-social` content log where available) · email/CRM automation visibility (same CRM connection) · Deliverables page · What's Next roadmap (source-backed reasoning, no invented benchmarks) · multi-brand or multi-location (tabbed or sectioned) · Agent Registry.

**Two pages carry most of the retention value.** *Deliverables* — a visual checklist of every service the agency is actively delivering: green/active, yellow/in-progress, grey/available-but-not-purchased. It answers "what am I paying for" before the client asks, and a grey card is an upsell without a sales call. *Agent Registry* — every automated Kai workflow running for this client: name, purpose, trigger, how to start it manually, last run, status.

**Retention plays:** Core — Brand Guide, Deliverables page, "Powered By [Agency]" co-branding (client logo top-left, agency mark top-right and smaller). Recommended — Competitor Watchlist, What's Next roadmap. Optional — Review Response Center and Lead Alert Feed for daily-use stickiness; Marketing Health Grade or ROI summary **only** with a named formula and a source per input, since an invented "B+" or "$40K in pipeline value" is exactly what the provenance rule exists to block.

**Credentials, where they live:** GA4 Property ID → Analytics → Admin → Property Settings · GSC Site URL → Search Console property selector, exactly as registered · Google Service Account JSON → Cloud Console → IAM & Admin → Service Accounts → Keys → Add Key → JSON · GoHighLevel Location ID / API Key → Settings → Business Info, and Settings → Integrations · HubSpot Private App Token → Settings → Integrations → Private Apps, CRM read scopes · Google Business Profile → Business Profile Manager, matched by business name. A credential not on this list is not a connector this harness ships today — collect it if the client has it, log the integration as a data gap until wired, and never fake its output meanwhile.

**Industry customization:**

| Industry | Review platforms | Distinctive page |
|---|---|---|
| Home Services | Google, Yelp, Houzz, Angi | Project gallery / before-after |
| Healthcare / Insurance | Google, Healthgrades | Compliance-safe lead pipeline (check `harness/references/advertising-compliance.md` before any health claim ships) |
| Hospitality | Google, TripAdvisor, Yelp | Visitor origin map + sentiment by area |
| E-commerce / Retail | Google, Yelp, Facebook | Product performance + cart abandonment |
| Professional Services | Google, LinkedIn | Proposal pipeline + retention view |
| Financial Services | Google, BBB | Deal tracker + sales leaderboard — Advanced tier only, and only with sign-off on showing individual rep numbers |

**Known failure modes:** a hardcoded default client id or credential from build #1 silently applying to build #2 · a public dashboard showing a login screen anyway (global 401 redirect) · a PII-bearing page left fully public · an empty panel filled with an invented number · a missing credential silently serving stale cache · SMS/voicemail enrolling a contact who never consented to hear from the agency · a fabricated Health Grade or ROI figure · an Agent Registry listing automation that isn't actually scheduled.

**Final response covers:** the dashboard URL (or the folder path and what remains to wire), the tier and which optional features shipped versus were skipped, every outstanding credential listed as a data gap, the public-access decision and why, and whether Deliverables and Agent Registry reflect real current state.

## Escalate when

- A page would expose PII publicly and the client has not signed off on that exposure for that data.
- A metric the client wants displayed has no source, or a score they want has no formula.
- SMS or voicemail engagement is requested without a documented consent basis and opt-out path.
- A second client's build would reuse the first client's config, credentials, or deployment.
- An Advanced module would surface individual rep performance or deal values without explicit sign-off.
- A required connector does not exist in this harness and the client expects live data from it.

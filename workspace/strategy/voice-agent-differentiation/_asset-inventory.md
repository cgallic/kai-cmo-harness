# Asset Inventory — What Already Exists (2026-07-05)

> Ground truth for `_strategy.md`. Every claim cites a repo file or a live tool call made 2026-07-05. This is the "what we have" the strategy must build from, not duplicate.

## KaiCalls product (live today)

| Asset | Status | Source |
|---|---|---|
| Flat pricing $69 (150 min) → $999 (4,500 min), $0.25/min overage, no seats, month-to-month, 7-day trial | Live | `workspace/competitive-intel/vs-cloudtalk.md` (planLimits.ts) |
| Sales pipeline targets **$499/mo** conversions (ABP pays $499 today) | Live | `workspace/AGENTS.md:56-58` |
| Stack: Vapi + ElevenLabs + OpenRouter/Claude; Next.js/Supabase | Live | `vs-cloudtalk.md:37` |
| Built-in CRM + SMS + email + calendar; outbound campaigns, nurture, reminders, lead scoring | Live | `_competitive-matrix.md:14-15` |
| **Adapters: Airtable, GHL, Litify** (Litify = legal system of record) | Live | `_competitive-matrix.md:15` |
| TCPA-gated outbound (8am–9pm local) via `kaicalls-call` CLI | Live | `workspace/TOOLS.md:149-160` |
| Phone-first admin ("just call Kai" — owner calls in, gets briefed) | Live | battlecard/matrix |
| **4,300+ calls handled, 4,900+ leads captured** (landing-page stats) | Live | `workspace/launch/landing-page/copy.md:84-86` |
| Customers: ABP ($499/mo), Referrizer (trial), **CaseEngine + MVP Accident Attorneys** (active, no Stripe attached); ~$0.7K MRR combined-Stripe view | Live | `workspace/AGENTS.md:58,72-73`, `vs-cloudtalk.md:21` |
| Agent spec already scopes KaiCalls as "AI call answering service for **law firms**" | Decided | `workspace/agents/kaicalls-agent.md:2` |
| Demo audio assets (`kaicalls-demo-full-v2.mp3`, `-v2.mp3`) | Exists | repo root |

## Distribution machinery (live today)

| Asset | Status | Source |
|---|---|---|
| `/compare/*` routing wired; **`/compare/goodcall` and `/compare/human-receptionist` live** (indexing as of Mar 29); `/compare/cloudtalk-alternative` speced | Live/partial | `docs/SEO_CHECKIN_2026-03-29.md:23`, `_recommendations.md:9,26` |
| Geo + vertical landing pages ("AI receptionist for [vertical] in [city]") | Built, extent unaudited | `_landscape-overview.md:52` |
| Brand queries rank pos 1.7, 44.68% CTR | Live | `SEO_CHECKIN:31` |
| Reddit listener: 28+ subreddits incl. r/HVAC, r/Plumbing, r/LawFirm, r/lawyers + trade subs added 7/04; ~60 trigger keywords incl. vapi, retell, smith.ai, goodcall, "missed calls", "speed to lead" | Live | `scripts/reddit_monitor/profiles/kaicalls.json`, commit fb7cb27 |
| Cold email: Instantly **law-firms campaign** running; Resend + Loops lifecycle infra, kaicalls domain verified | Live | `kaicalls-agent.md:97`, `AGENTS.md:187,194` |
| Meta/Google/TikTok pixels | Live | `vs-cloudtalk.md:51` |
| Intel: `kai-harness intel` (RSS/sitemap diff, gaps, weekly brief), SERP tracker, CloudTalk teardown + battlecard | Live | `workspace/MARKETING.md:147-165`, `workspace/competitive-intel/` |
| Newbiz prospect base: **1,607 enriched local-business rows** (place_id, phone, email, owner, priority) | Exists | `workspace/newbiz/smoke3_2026-05-27.csv` |
| Kai Marketing OS itself: 39+ skills, quality gates, AEO frameworks, surround-sound skill | Live | repo |
| Heartbeat ops: 6 parallel domain agents (KaiCalls incl.), daily research cron, Discord alert routing | Live | `workspace/HEARTBEAT.md`, `workspace/agents/` |

## CaseEngine (the legal channel — live today)

- **~20 distinct personal-injury law firms** across CA/TX/FL/GA/CO (26 client configs incl. multi-location + 1 demo firm). Source: live `list_clients` MCP call, 2026-07-05.
- Working capability surface (MCP): **call tracking** (calls, summaries, trends, period compare, sources), GHL + Fathom intake webhooks, WordPress publishing + editorial flow, grid rank reports, review reports, **AI-visibility/AEO tracking** (citations, keywords, prompts), GBP (posts, reviews, performance), NAP citations, GSC/GA analytics, client provisioning, content brief generation, site migration + Cloudways provisioning, **legal research (statute of limitations, practice areas, by state)**, ebook factory, competitor tracking.
- CaseEngine is itself an active KaiCalls customer; **MVP Accident Attorneys is both a CaseEngine client and an active KaiCalls customer** — a shared design partner already exists. Source: `workspace/AGENTS.md:58` + `list_clients`.

## Other products (context)

- **BuildWithKai** — AI product-builder, ~13 businesses, $5.99/mo Basic (`workspace/agents/bwk-agent.md`).
- **VocalScribe** — transcription; shares Stripe (`AGENTS.md:92`).
- **ABP** — event marketplace, 461 leads; pays KaiCalls $499/mo (`AGENTS.md:79-81`).
- **MeetKai / Kai Marketing OS** — this repo's product; `workspace/growth-plan/` is about IT (stage: early launch/pre-revenue), not KaiCalls.

## Known gaps (things the strategy must actually build)

1. **No Clio/Lawmatics adapters** — Litify only. Smith.ai's legal moat is Clio/Lawmatics/MyCase coverage; most PI solos run Clio, not Litify.
2. **Comparison coverage**: 2 pages live vs the 6-page competitor set (Rosie, Smith.ai, Dialzara, Jobber AI Receptionist, Ruby missing); no cost calculator.
3. **No legal-specific intake flows shipped** (conflict screening, SOL urgency triage, retainer scheduling) — CaseEngine's `statute_of_limitations` API is an unused ingredient for this.
4. **No outcome instrumentation** (answered → qualified → booked as a queryable funnel) and no benchmark dataset, despite 4,300+ calls handled.
5. **No infra adapter layer** — KaiCalls is coupled to Vapi directly (single assistant IDs in config).
6. **No case studies with provenance-clean numbers** for KaiCalls (ABP and MVP are candidates).
7. **Geo/vertical page program extent unaudited** — coverage, indexation, and conversion unknown; needs a GSC pull before scaling.
8. **Pricing page tension**: $69 anchor vs $499 sales target — vertical (legal) tier not productized.

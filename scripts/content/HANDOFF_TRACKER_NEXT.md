# Content Tracker — Next-Agent Handoff

**Author:** preceding session (2026-04-14)
**For:** the next Claude Code / Kai Harness agent who picks this up
**Status:** tracker v1 shipped; v2 roadmap below

---

## What's already built (don't rebuild it)

A content performance tracker lives under `scripts/content/`. It's live and tested.

### Modules

| File | Role |
|------|------|
| `scripts/content/platforms/devto.py` | Pulls published-article stats from Dev.to API. Matches to content-log entries by URL. Writes `~/.kai-marketing/metrics/{id}.json`. |
| `scripts/content/platforms/linkedin_entry.py` | Records LinkedIn stats manually (interactive or arg-based). LinkedIn's public API doesn't expose per-post impressions without Marketing Developer approval, so this is a deliberate manual-entry script. |
| `scripts/content/citations/checker.py` | Runs target queries against Perplexity Sonar + OpenAI `web_search_preview` + Anthropic `web_search`. Detects whether our domains/terms are cited. Appends events to `~/.kai-marketing/citations/{id}.jsonl`. Supports tiered queries and share-of-voice (SOV) tracking against competitor domains. |
| `scripts/content/tracker_cli.py` | `kai-tracker` unified CLI. Subcommands: `pull-devto`, `linkedin`, `citations`, `targets`, `report`. |
| `content-report/SKILL.md` | `/content-report` skill — cross-references GSC + GA4 + Dev.to + LinkedIn + citation data; grades winner/average/underperformer. |

### Data layout

```
~/.kai-marketing/
├── content-log.jsonl                   # append-only publish log
├── metrics/{id}.json                   # per-article platform metrics (Dev.to, LinkedIn history)
├── citations/{id}.jsonl                # per-article citation events (append-only)
├── citations/_global_kaicalls.jsonl    # global brand citation events
├── citations/_global_connor_gallic.jsonl
└── citations-targets.json              # tiered queries + match rules per entity
```

### API keys (in `E:\Dev2\kai-cmo-harness-work\.env`, gitignored)

| Key | Status |
|-----|--------|
| `DEVTO_API_KEY` | ✅ live |
| `OPENAI_API_KEY` | ✅ live |
| `PERPLEXITY_API_KEY` | ✅ live ($50 credit) |
| `ANTHROPIC_API_KEY` | ❌ all three keys on disk are revoked. Grab a fresh one at console.anthropic.com if the checker should run 3 providers. Checker already skips gracefully when missing. |

### Current baseline (established 2026-04-14)

- **92 checks run** across KaiCalls + Connor Gallic global entities
- **Brand tier: 91% citation rate** (strong)
- **Category/vertical/pain tiers: 0% citation rate** (structural invisibility)
- **Winning comparison wins:** only when query name-checks KaiCalls ("KaiCalls vs Dialpad", "KaiCalls vs GoodCall")
- **SOV leaderboard:** RingCentral 46, Dialpad 29, GoodCall 18, Dialzara 6, Smith.ai 4

**Strategic finding worth surfacing to Connor:** GoodCall is a top-3 AI-search competitor not previously on the radar. Now in `marketing.md` and `sov_domains`. Build `KaiCalls vs GoodCall` comparison page as priority.

---

## The 6 recommended next builds

Priority ordering based on strategic leverage, ease of build, and data we already have. `P1` = do next. `P2` = within 30 days. `P3` = quarterly cadence.

### 1. Schema/brand accuracy audit — P1, ~1 hour

**Goal:** catch AI engines confidently stating wrong facts about KaiCalls.

**Build:**
- New file: `scripts/content/citations/schema_audit.py`
- Hardcoded list of ~15 factual queries:
  - "What is KaiCalls's pricing?"
  - "How long is KaiCalls's free trial?"
  - "Does KaiCalls integrate with HubSpot?" / Salesforce / GoHighLevel
  - "What industries does KaiCalls serve?"
  - "Who founded KaiCalls?"
  - "Where is KaiCalls based?"
  - "Is KaiCalls the same as Kai.com?"
  - etc.
- For each, run the query via Perplexity + OpenAI. Capture the answer text.
- Diff the answer against ground truth from `clients/Kai_calls/marketing.md` (pricing, founder, etc.).
- Flag discrepancies. Write to `~/.kai-marketing/schema-audit/YYYY-MM-DD.md` as a markdown diff report.

**Why it's high-leverage:** every wrong answer the AI gives is reputation damage. Every fix propagates immediately through correct structured data on kaicalls.com.

**Gotchas:**
- Ground truth needs manual curation — don't auto-parse marketing.md for numeric claims; they'll be wrong half the time. Hand-write the expected-answer table inside the script.
- Re-run weekly; LLM answers shift as their training cuts update.

---

### 2. Content gap audit — P1, ~3 hours

**Goal:** turn every "uncited" query from the sweep into a concrete content brief.

**Build:**
- New file: `scripts/content/citations/gap_audit.py`
- Load `~/.kai-marketing/citations/_global_*.jsonl`, filter to events where `cited=false`.
- For each uncited query, aggregate:
  - Top 3 cited domains (from `sources` array)
  - Excerpt of the answer (first 400 chars)
  - SOV hits present (which competitor buckets appeared)
- Output: a prioritized markdown backlog at `~/.kai-marketing/gap-audit/YYYY-MM-DD.md`:
  ```
  ## P1 — "AI phone system for law firms"
  Cited: goodcall.com, smith.ai/legal, clio.com
  Claim: "GoodCall lets you customize scripts for legal intake..."
  Build: /solutions/legal page needs a schema-structured section answering
   this query directly; first sentence must restate 'AI phone system for law firms'
   then answer with a specific KaiCalls-legal feature.
  ```
- Feeds `/content-write` skill as a brief input.

**Why it's high-leverage:** converts citation data into a publishable to-do list. The current content roadmap is internally decided; this one is reverse-engineered from what AI search already rewards.

**Gotchas:**
- Don't auto-generate content — just the brief. Humans still review before `/content-write` runs.

---

### 3. ICP language mining — P2, ~2 hours

**Goal:** extract the literal phrases prospects use about their pain, so content can match that language verbatim (Algorithmic Authorship rule #1 — language match with search query).

**Build:**
- New file: `scripts/content/citations/icp_mining.py`
- Hardcoded prompts per vertical from `marketing.md` ICP list:
  - "What are the biggest phone-system frustrations for HVAC business owners?"
  - "What do plumbing contractors complain about in online reviews about their phone systems?"
  - "What do law firm office managers say about answering services on Reddit?"
  - ...one per ICP vertical
- Use Perplexity Sonar. Request `sonar-pro` model (better synthesis, worth the ~10x cost because we run it monthly, not weekly).
- Parse the answer. Extract verbatim phrases in quotes or sentences that sound like prospect self-talk ("I can't answer the phone when I'm on a job site", "our answering service put my best lead on hold", etc.).
- Output to `~/.kai-marketing/icp-language/{vertical}.md`:
  ```
  ## HVAC — pain phrases (2026-04-28)
  - "missed call during peak season"
  - "my tech can't take the call while on a roof"
  - "answering service puts emergency calls on hold"
  ...
  ```
- `/content-write` should load the vertical's phrases as context when writing vertical content.

**Why it's high-leverage:** Perplexity already aggregates these phrases from Reddit, YouTube transcripts, review sites. Saves Connor from doing this manually per piece.

**Gotchas:**
- Run it monthly per vertical, not every sweep. The output is slow-changing.
- `sonar-pro` is billed higher than `sonar` — budget ~$0.20/query.

---

### 4. Weekly citation trend + Discord digest — P1, ~2 hours

**Goal:** the value of the tracker is the week-over-week trendline, not a one-time snapshot.

**Build:**
- Cron (on agent box or hermes VPS, whichever runs CMO analytics):
  - Sunday 23:00 ET: `kai-tracker citations --global` (full sweep)
  - Monday 07:00 ET: `kai-tracker report --format json` piped into a digest generator
- New file: `scripts/content/citations/weekly_digest.py`
- Reads the two latest weekly citation snapshots (this week + last week).
- Computes diffs:
  - **Citation count:** 26 → 34 (+8)
  - **New wins:** queries now cited that weren't last week
  - **Losses:** queries cited last week that dropped
  - **SOV shifts:** RingCentral hits 46 → 52 (+6), GoodCall 18 → 12 (-6)
- Posts to Discord via the existing Kai-CMO Discord integration (channel: `kaicalls` — ID in `config.yaml`).
- Also writes to `~/.kai-marketing/digests/YYYY-MM-DD.md` for archive.

**Why it's high-leverage:** turns a one-shot tool into a weekly signal Connor can act on without running anything. The trend is the product.

**Gotchas:**
- Cron needs `PERPLEXITY_API_KEY` + `OPENAI_API_KEY` — set in the systemd service or crontab env, not just login shell.
- Discord post should be <2000 chars — trim to top 5 wins + top 5 losses + SOV summary. Full report link to markdown file on agent box.
- First 4 weeks will look noisy; real trends emerge after 6-8 data points.

---

### 5. Prospect research / outbound intelligence — P2, ~3 hours

**Goal:** before Connor sends an outbound email or makes a sales call, auto-generate a prospect brief from public sources.

**Build:**
- New file: `scripts/content/outbound/prospect_brief.py`
- Input: a company name + optional URL.
- Queries Perplexity with:
  - "What phone system does [Company] use?"
  - "What are [Company]'s customer reviews on Yelp/Google?"
  - "Has [Company] mentioned phone or call problems publicly?"
  - "Who is the owner/decision-maker at [Company]?"
- Synthesizes output into a one-page brief:
  ```
  # [Company Name]
  - Industry: [from Perplexity]
  - Phone system (likely): RingCentral Core ($30/seat × 12 employees = $360/mo)
  - Recent review signal: 3 complaints about "called and got voicemail" in last 6 mo
  - Decision-maker: [Owner Name]
  - Outreach angle: cite one specific review that mentions missed calls
  ```
- Also consider exposing as an MCP tool inside the brain or the KaiCalls product itself — so KaiCalls agents can research prospects for the user.

**Why it's high-leverage:** saves 20 minutes per prospect; scales if exposed as a product feature.

**Gotchas:**
- Perplexity answers about small businesses are often sparse — fall back to listing whatever sources it found.
- Don't store PII beyond what's in public reviews. If the brief starts surfacing personal data, trim.
- Rate-limit to ~50 briefs/day (~$5 in Perplexity credits).

---

### 6. Cross-platform content performance correlation — P3, ~2 hours

**Goal:** figure out whether platform performance (LinkedIn impressions, Dev.to views) predicts AI citation — so Connor knows where to publish first.

**Build:**
- New file: `scripts/content/analysis/platform_citation_correlation.py`
- Load all entries from `content-log.jsonl`.
- For each entry, join:
  - Platform metrics from `metrics/{id}.json` (LinkedIn impressions, Dev.to views)
  - Citation events from `citations/{id}.jsonl` (cited count over 30-day window)
- Compute basic correlations:
  - Do high-LinkedIn-engagement posts get cited more?
  - Does Dev.to view velocity predict citation?
  - Which format (LinkedIn / Dev.to / X) wins citations most often per topic?
- Output to `~/.kai-marketing/analysis/platform-correlations-YYYY-MM-DD.md`.

**Why it's P3:** needs ≥20 tracked articles with ≥4 weeks of data to be statistically meaningful. Don't build until the log has enough entries. Check back in 30-60 days.

**Gotchas:**
- LinkedIn metrics are manual. If Connor stops entering them, the analysis degrades. Include a reminder mechanism (digest flags articles with no LinkedIn stats after 7 days of being live).

---

## Priority order for the next agent

```
P1 (do this first — all data/infra already exists)
  1. Schema audit          — ~1h, catches brand accuracy bugs
  2. Content gap audit     — ~3h, turns citation data into content briefs
  4. Weekly digest         — ~2h, activates the whole tracker as a recurring signal

P2 (within 30 days)
  3. ICP language mining   — ~2h, feeds content writing
  5. Prospect research     — ~3h, doubles as product feature

P3 (when data accumulates)
  6. Platform correlation  — ~2h, needs 20+ tracked articles
```

---

## Quick reference

**Run a citation sweep manually:**
```bash
cd E:/Dev2/kai-cmo-harness-work
set -a && source .env && set +a
python -m scripts.content.tracker_cli citations --global
```

**Run a single tier:**
```bash
python -m scripts.content.tracker_cli citations --global --tier brand
python -m scripts.content.tracker_cli citations --global --tier comparison --tier vertical
```

**Pull Dev.to stats:**
```bash
python -m scripts.content.tracker_cli pull-devto
```

**Record LinkedIn metrics:**
```bash
python -m scripts.content.tracker_cli linkedin \
  --id kaicalls-20260415-100000-linkedin \
  --impressions 1850 --reactions 34 --comments 7 --dms 3
```

**View the report:**
```bash
python -m scripts.content.tracker_cli report
```

**Edit queries:**
```
~/.kai-marketing/citations-targets.json
```

**Add a new entity to track:**
Create a `_global_<brand>` key in `citations-targets.json` with `queries` (tiered dict), `match_domains`, `match_terms`, optional `sov_domains`.

---

## Known issues / watch-outs

1. **OpenAI `web_search_preview` is non-deterministic.** For ~60% of category queries the model answers from training knowledge and returns 0 sources. Perplexity is the reliable measurement layer; treat OpenAI as bonus coverage.
2. **Anthropic keys on disk are all revoked.** If you want 3-provider coverage, grab a fresh key from console.anthropic.com → Settings → API Keys.
3. **`just call kai` brand query fails both providers.** Worth investigating: is the `/just-call-kai` landing page on kaicalls.com indexed? Does it have the phrase as an H1 + in meta description?
4. **Schema issue in per-article targets.** The per-article `match_domains` should include the article URL (or its LinkedIn/Dev.to slug) so citation detection fires when *that specific piece* shows up in results. Already configured for the 5 seeded articles but new articles need this set at seed time.
5. **Content log is append-only.** Don't edit entries in place; add correction events that reference the prior id. Matches the brain's append-only invariant.

---

## Context the next agent may want

- Canonical `marketing.md` — `C:\Users\cgall\OneDrive\Desktop\Dev\adminpanelnew\marketing.md`
- Synced copy in the harness — `E:\Dev2\CMO_Agent_System\clients\Kai_calls\marketing.md`
- KaiCalls site SEO audit — `E:\Dev2\CMO_Agent_System\clients\Kai_calls\outputs\seo\kaicalls.com.md`
- Existing content skills in the harness — `content-brief/`, `content-gate/`, `content-ideas/`, `content-report/`, `content-retro/`, `content-write/` at the harness root
- The brain (personal intelligence system referenced throughout the Dev.to piece) lives at `/home/connor/brain/` on the agent box, 156,926 events, Qdrant vector search, 18 MCP tools — don't re-research it, just `semantic_search` if you need context

---

## Last-session status

- ✅ Tracker v1 shipped
- ✅ 2 articles seeded (Tue KaiCalls LinkedIn + Tue Dev.to personal AI)
- ✅ 3 more articles pending seed (Mon LinkedIn Perplexity piece, Mon X brain thread, Dev.to 13-of-14 integrations) — seeder script at `scripts/content/_seed_log.py`, just needs rerun once the ambiguity about Mon #1 Dev.to title is resolved
- ✅ Per-article citation targets configured for the 2 seeded articles; needs extension for the 3 pending
- ⏸ Next: either pick up P1 (schema audit / content gap / weekly digest) or finish seeding the pending articles + run their per-article sweeps

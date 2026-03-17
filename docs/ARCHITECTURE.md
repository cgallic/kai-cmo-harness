# Architecture

How the Kai CMO Harness works, from knowledge base to published content.

---

## Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      KNOWLEDGE BASE                         │
│  knowledge/frameworks/  channels/  checklists/  personas/   │
│  30+ frameworks, 17 checklists, 8 personas, 12 AEO files   │
└──────────────────────────┬──────────────────────────────────┘
                           │ loaded per task type
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    HARNESS PIPELINE                          │
│  Research → Brief → Write → Quality Gate → Approve → Log    │
│                                                             │
│  Driven by: MARKETING.md (operating config)                 │
│  Enforced by: harness_cli.py (CLI orchestrator)             │
│  Contracts: harness/skill-contracts/*.yaml                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ draft passes all gates
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    QUALITY GATES                             │
│  four_us_score.py → banned_word_check.py → seo_lint.py     │
│  Max 2 retries → human escalation on persistent failure     │
└──────────────────────────┬──────────────────────────────────┘
                           │ gate passed
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPROVAL                                  │
│  Discord post with score card → human reacts ✅ or ❌       │
│  ✅ = publish + log    ❌ = revise + re-gate                │
└──────────────────────────┬──────────────────────────────────┘
                           │ approved
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    PUBLISHING + LOGGING                      │
│  content_log.py → content_log.json + pending_checks/        │
│  Every piece tracked for 30-day performance review          │
└──────────────────────────┬──────────────────────────────────┘
                           │ 30 days later
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                SELF-IMPROVEMENT LOOP                         │
│  performance_check.py → pattern_extract.py →                │
│  harness_defaults_update.py → MARKETING.md updated          │
└─────────────────────────────────────────────────────────────┘
```

---

## How MARKETING.md Drives the Harness

MARKETING.md is the operating config. The harness reads it on every run via the `MarketingConfig` parser class in `scripts/harness_cli.py`. It is to the content pipeline what `CLAUDE.md` is to a coding agent.

### What gets parsed

| Section | Extracted Data | Used For |
|---------|---------------|----------|
| Non-Negotiables | Voice rules, banned words, quality floor | Injected into every write prompt |
| Skill Contracts table | Per-format thresholds (Four U's min, SEO lint on/off) | Gate decides pass/fail |
| Products + Site Keys table | Site key -> Discord channel ID mapping | Route approval posts to correct channel |
| Framework Map table | Task type -> list of knowledge file paths | Which frameworks to load before writing |
| Learned Defaults | Auto-written patterns from winners | Injected into write prompt as guidance |

### Parse flow

```python
# On every harness run:
MARKETING = MarketingConfig(WORKSPACE / "MARKETING.md")

# Before writing:
MARKETING.reload()                          # Re-read from disk (picks up auto-updates)
paths = MARKETING.framework_paths("blog")   # Returns resolved Path objects
threshold = MARKETING.threshold("blog")     # Returns 12 for long-form, 10 for ads
contract = MARKETING.skill_contract("blog") # Returns parsed YAML dict

# During gate:
seo_required = MARKETING.seo_required("blog")  # True for blog/seo/press, False for ads
channel = MARKETING.channel("kaicalls")          # Discord channel ID for approval post
```

### Why it matters

Without MARKETING.md, the model invents defaults. It picks random thresholds, skips frameworks, and generates generic content. With MARKETING.md, the model executes with institutional context: which frameworks apply, what thresholds to hit, what voice rules to follow, and what patterns have worked in the past.

The self-improvement loop closes the feedback circle. Content that performs well (position <=5, CTR >=5%, session >=90s) gets analyzed for patterns. Those patterns are appended to MARKETING.md's Learned Defaults section, changing future content behavior without code changes.

---

## Quality Gate Flow

Three scripts run sequentially on every draft. All three must pass.

```
Draft
  │
  ▼
┌─────────────────────────────────────────────────┐
│  Gate 1: four_us_score.py                       │
│                                                 │
│  LLM grades on 4 dimensions (1-4 each):        │
│    Unique:         Can only WE write this?      │
│    Useful:         Can reader take action?      │
│    Ultra-specific: Numbers, examples, names?    │
│    Urgent:         Reason to engage today?      │
│                                                 │
│  Pass: total >= threshold AND each dim >= 2     │
│  Threshold: 12/16 (long-form), 10/16 (ads)     │
│  Threshold source priority:                     │
│    1. CLI --threshold flag                      │
│    2. Skill contract YAML                       │
│    3. MARKETING.md table                        │
│    4. Heuristic (short-form detection)          │
└───────────────┬─────────────────────────────────┘
                │ pass
                ▼
┌─────────────────────────────────────────────────┐
│  Gate 2: banned_word_check.py                   │
│                                                 │
│  Three tiers:                                   │
│    Tier 1: ~50 words → HARD BLOCK               │
│      leverage, utilize, synergy, innovative,    │
│      deep dive, circle back, revolutionary...   │
│    Tier 2: flagged + replacement suggested      │
│    Tier 3: weak qualifier warning               │
│                                                 │
│  Runtime: <2 seconds, no API call               │
│  Pass: zero Tier 1 hits                         │
└───────────────┬─────────────────────────────────┘
                │ pass
                ▼
┌─────────────────────────────────────────────────┐
│  Gate 3: seo_lint.py                            │
│                                                 │
│  Checks:                                        │
│    - Keyword in title + first 100 words         │
│    - H2 with secondary keyword                  │
│    - 2+ internal links                          │
│    - Keyword density 1-2%                       │
│    - Average sentence < 20 words                │
│                                                 │
│  Skipped for: meta-ads, google-ads, cold-email, │
│    email-lifecycle, tiktok                       │
│  Skip logic: contract YAML + MARKETING.md +     │
│    heuristic (VARIANT A, Touch 1, Subject:,     │
│    HOOK (0-3s) patterns in draft)               │
└───────────────┬─────────────────────────────────┘
                │
           pass │          fail (any gate)
                │               │
                ▼               ▼
           APPROVE        revise_draft()
                          (surgical fix)
                               │
                               ▼
                          Re-run gates
                          (max 2 retries)
                               │
                          still fails
                               │
                               ▼
                          ESCALATE TO HUMAN
                          (with failure report)
```

### Gate thresholds by format

| Format | Four U's min | SEO lint | Banned words |
|--------|:------------:|:--------:|:------------:|
| Blog, SEO, Press | 12/16 | Required | Required |
| LinkedIn | 12/16 | Required | Required |
| Meta ads, Google ads | 10/16 | Skipped | Required |
| Cold email | 10/16 | Skipped | Required |
| Email lifecycle | 10/16 | Skipped | Required |
| TikTok | 10/16 | Skipped | Required |

### Revision strategy

`revise_draft()` is surgical, not wholesale:
- Only failing dimensions are sent to the LLM for revision
- Passing dimensions are listed as "DO NOT CHANGE"
- Banned word hits include exact context and suggested replacements
- SEO errors (not warnings) are passed through
- Hard constraint: do not shorten the draft or remove data points

---

## Self-Improvement Loop

The harness learns from its own output. This is the feedback loop that makes content get better over time without manual tuning.

### 30-day performance check

```
performance_check.py --all
   │
   │  For each piece in content_log.json with a pending_checks/ file:
   │
   ├── Pull GSC data: position, CTR for the target keyword
   ├── Pull GA4 data: avg session duration for the URL
   │
   │  Winner threshold:
   │    position <= 5
   │    CTR >= 5%
   │    avg session >= 90 seconds
   │
   └── Grade: winner | average | underperformer
```

Runs daily at 2 AM via cron. Checks pieces that are 30+ days old.

### Pattern extraction (weekly)

```
pattern_extract.py --weekly --site all
   │
   │  Analyzes winners for statistical patterns:
   │    - Hook type (curiosity gap vs social proof vs pain agitate)
   │    - Format (blog vs LinkedIn vs email)
   │    - Word count range
   │    - Publish day of week
   │    - Target persona
   │
   │  Threshold: n >= 5 samples, delta >= 15% lift
   │
   └── Appends to knowledge/playbooks/what-works.md
```

Runs Mondays at 2:14 PM via cron.

### Harness defaults update

```
harness_defaults_update.py
   │
   │  Reads what-works.md
   │  Identifies patterns with statistical significance
   │  Rewrites the "Learned Defaults" section of MARKETING.md
   │
   └── Next harness run picks up the new defaults automatically
```

Runs Mondays at 2:44 PM (30 minutes after pattern extraction).

### Full loop timeline

```
Day 0:    Write + gate + approve + publish + log
Day 30:   performance_check.py pulls GSC + GA4 data, grades the piece
Monday:   pattern_extract.py analyzes all winners, appends to what-works.md
Monday+30m: harness_defaults_update.py rewrites MARKETING.md learned defaults
Day 31+:  Next harness run reads updated MARKETING.md, applies learned patterns
```

---

## OpenClaw Architecture

When running as an autonomous agent via OpenClaw, the system uses a three-tier architecture.

### Tier 1: Orchestrator

The main Kai-CMO session. Reads `AGENTS.md` on startup. Responsible for:
- Routing Discord messages to the correct domain agent
- Spawning all domain agents in parallel on heartbeat
- Aggregating results from domain agents
- Posting cross-product alerts to #updates

### Tier 2: Domain Agents

Spawned in parallel on every heartbeat. Each agent:
- Gets ONLY its own domain context (no cross-contamination)
- Pulls data from its product's analytics endpoints
- Posts directly to its Discord channel for clear-cut alerts
- Returns structured output to the orchestrator for ambiguous signals

```
┌───────────────────────────────────────────┐
│              ORCHESTRATOR                  │
│  Reads: AGENTS.md, HEARTBEAT.md           │
│  Spawns: all domain agents in parallel    │
│  Yields: waits for all to complete        │
│  Routes: alerts to correct channels       │
└────┬──────┬──────┬──────┬──────┬──────┬───┘
     │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼
  kaicalls  abp   bwk  finance infra  gate
  agent    agent  agent  agent  agent  agent
     │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼
 #kai-  #awesome  #bwk #finance #health #zehrava
 calls  -backyard
```

### Tier 3: Skills

Procedural guides loaded into the orchestrator context on demand. Not spawned as agents. Examples: `dev-workflow`, `kaicalls-outbound`, `marketing-knowledge`, `patent-scanner`.

### Heartbeat Protocol

Defined in `workspace/HEARTBEAT.md`. Fires on a configurable schedule.

**Step 1 — Spawn all domain agents in parallel**

```
sessions_spawn(task=<agents/kaicalls-agent.md>, label="hb-kaicalls", mode="run", runtime="subagent")
sessions_spawn(task=<agents/abp-agent.md>,      label="hb-abp",      mode="run", runtime="subagent")
sessions_spawn(task=<agents/finance-agent.md>,  label="hb-finance",  mode="run", runtime="subagent")
sessions_spawn(task=<agents/gate-agent.md>,     label="hb-gate",     mode="run", runtime="subagent")
sessions_spawn(task=<agents/bwk-agent.md>,      label="hb-bwk",      mode="run", runtime="subagent")
sessions_spawn(task=<agents/infra-agent.md>,    label="hb-infra",    mode="run", runtime="subagent")
```

All spawns happen before any yield. This is parallel fan-out, not sequential.

**Step 2 — Yield**

```
sessions_yield()
```

Wait for all domain agents to complete and return results.

**Step 3 — Route results**

Each agent returns `NOTHING` (all clear) or an alert string (already posted to its channel). If more than 2 products flag alerts, the orchestrator posts an aggregate to #updates.

**Step 4 — Proactive memory scan**

Runs `proactive_heartbeat.py` which self-throttles to every 6 hours. Reads signals from `/tmp/proactive_heartbeat_signals.json` and posts to the relevant Discord channels.

**Step 5 — Acknowledge**

If no alerts: reply `HEARTBEAT_OK`.

---

## Data Flow

End-to-end path from raw data to published content.

```
EXTERNAL DATA SOURCES
  │
  ├── GSC (queries, rankings, impressions, CTR)
  ├── GA4 (sessions, page views, sources, duration)
  ├── Supabase (leads, users, calls, business metrics)
  ├── Stripe (MRR, subscriptions, charges)
  ├── Meta Ads (spend, impressions, CTR, ROAS)
  ├── Instantly (cold email campaigns, open/reply rates)
  └── Loops (email contacts, automation events)
  │
  ▼
┌─────────────────────────────────────────────────┐
│  ANALYTICS CLI                                   │
│  scripts/analytics/cli.py                        │
│  cmo <module> <command>                          │
│                                                  │
│  Normalizes data into structured output          │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  HARNESS BRIEF                                   │
│  harness_cli.py generate_brief()                 │
│                                                  │
│  Inputs: GSC opps + GA4 data + persona + facts   │
│  Output: brief.json (keyword, angle, hooks,      │
│          competitor weakness, proof points)       │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  CONTENT WRITER                                  │
│  harness_cli.py write_content()                  │
│                                                  │
│  Inputs: brief.json + MARKETING.md config +      │
│          framework files + skill contract +      │
│          what-works.md patterns + site facts     │
│  Model: Gemini 2.0 Flash                        │
│  Output: draft.md                                │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  QUALITY GATE                                    │
│  four_us_score.py + banned_word_check.py +       │
│  seo_lint.py                                     │
│  Max 2 auto-retries with surgical revision       │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  APPROVAL (Discord)                              │
│  Score card posted → human reacts                │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│  PUBLISH + LOG                                   │
│  content_log.py → content_log.json               │
│  + pending_checks/[id].json for 30-day review    │
└───────────────┬─────────────────────────────────┘
                │
                ▼ (30 days later)
┌─────────────────────────────────────────────────┐
│  PERFORMANCE CHECK                               │
│  GSC + GA4 pull → grade (winner/avg/under)       │
│  Winner patterns → what-works.md →               │
│  MARKETING.md learned defaults updated           │
│                                                  │
│  Loop closes: next content run uses new defaults │
└─────────────────────────────────────────────────┘
```

---

## File Contracts

### brief.json

```json
{
  "target_site":         "kaicalls",
  "target_keyword":      "law firm answering service",
  "secondary_keywords":  ["legal answering service", "..."],
  "format":              "blog",
  "persona":             "Shock Absorber",
  "current_rank":        "not ranking",
  "monthly_impressions": 0,
  "current_ctr":         0.0,
  "competitor_url":      "https://...",
  "competitor_weakness": "specific gap in 20+ words",
  "angle":               "differentiated frame",
  "hook_options":        ["Hook 1", "Hook 2", "Hook 3"],
  "audience_pain":       "biggest frustration of this persona",
  "proof_available":     "specific data point or stat",
  "cta":                 "exact action",
  "word_count_target":   1400,
  "publish_date":        "2026-03-16",
  "internal_links":      ["https://...", "https://..."]
}
```

### content_log.json entry

```json
{
  "id":            "kaicalls-blog-20260316",
  "site":          "kaicalls",
  "keyword":       "law firm answering service",
  "format":        "blog",
  "url":           "https://kaicalls.com/blog/...",
  "hook_type":     "curiosity_gap",
  "publish_date":  "2026-03-16",
  "four_us_score": 13,
  "performance_30d": null
}
```

### pending_checks/[id].json

```json
{
  "id":           "kaicalls-blog-20260316",
  "url":          "https://kaicalls.com/blog/...",
  "check_after":  "2026-04-15",
  "status":       "pending"
}
```

---

## Outcome Engine

The Outcome Engine collapses the harness from a 28-decision builder tool to a 3-input system: `format`, `site`, `keyword`. Users provide those three; the engine makes all internal decisions.

**Spec:** `docs/superpowers/specs/2026-03-17-outcome-engine-design.md`

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      3 INPUTS                                │
│  format: "blog"   site: "kaicalls"   keyword: "AI recep…"  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTCOME ENGINE                             │
│  scripts/content/engine.py :: generate()                     │
│                                                             │
│  1. Validate inputs                                         │
│  2. Resolve persona      (persona_resolver.py)              │
│  3. Load frameworks      (FRAMEWORK_MAP per format)         │
│  4. Generate brief       (brief_generator.py + Gemini)      │
│  5. Write content        (_writer.py + Gemini)              │
│  6. Run quality gate     (gate.propose + retry loop)        │
│  7. Apply approval       (approval_policy.py)               │
│  8. Log if approved      (content_log.py)                   │
│                                                             │
│  Returns: GenerateResult(content, brief, gate_report,       │
│           status, proposal_id, metadata)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     4 SURFACES                               │
│                                                             │
│  CLI:     kai-harness generate --format blog --site kai…    │
│  Discord: !kai blog kaicalls "AI receptionists"             │
│  HTTP:    POST /generate {format, site, keyword}            │
│  MCP:     (planned — see MCP Design Options below)          │
└─────────────────────────────────────────────────────────────┘
```

### Module Map

```
scripts/content/
├── engine.py              # Core orchestrator — the single entry point
├── brief_generator.py     # Auto-generates 18-field brief from 3 inputs
├── persona_resolver.py    # Maps (site, keyword) → persona via config
├── approval_policy.py     # 3x3 decision matrix: gate_status × policy
├── _writer.py             # Pure functions: prompt assembly + LLM calls
├── intent_parser.py       # NLP: freeform text → (format, site, keyword)
├── content_log.py         # Programmatic logging API
└── __init__.py
```

### Decision Flow

The engine makes all 28 decisions internally:

| Decision | How it's made | Source |
|----------|--------------|--------|
| Persona | `persona_resolver.resolve_persona()` | config.yaml `site_persona_defaults` + keyword AI-signal regex |
| Framework files | `FRAMEWORK_MAP[format]` | Hardcoded in engine.py, matches CLAUDE.md table |
| Skill contract | Format slug → `harness/skill-contracts/{slug}.yaml` | YAML file |
| Word count | Contract YAML → `word_count` field | Skill contract |
| Secondary keywords | GSC data + Gemini inference | API + LLM |
| Angle, hooks, competitor weakness | Single Gemini call in brief_generator | LLM |
| Audience pain | Persona .md file + Gemini inference | Knowledge base + LLM |
| Internal links | Last 5 URLs from content_log.json for this site | Content log |
| Proof points | config.yaml `products[].proof_points` | Config |
| Quality gate policy | `FORMAT_TO_POLICY[format]` | _writer.py |
| Approval policy | `resolve_policy(format, site)` | config.yaml `approval_policy` |
| Four U's threshold | Contract YAML or default (12 long, 10 short) | Skill contract |
| SEO lint required? | `format not in SHORT_FORM` | _writer.py |
| Retry count | Max 2 | Hardcoded |

### Approval Policy

The engine uses a 3x3 decision matrix to determine content fate:

```
                   Policy
                   auto     hold     reject_only
Gate Status  ┌──────────┬──────────┬──────────┐
  approved   │ approved │   held   │ approved │
  pending    │   held   │   held   │   held   │
  rejected   │  failed  │  failed  │  failed  │
             └──────────┴──────────┴──────────┘
```

Policies are configured per format+site in `config.yaml`:
```yaml
approval_policy:
  default: "hold"
  overrides:
    - format: "blog"
      site: "kaicalls"
      policy: "auto"       # blogs for kaicalls auto-approve
    - format: "meta-ads"
      site: "*"
      policy: "hold"       # all ads require human review
```

---

## MCP Server — Design Options

The harness should be accessible as native tools in Claude Code, Codex, and similar AI coding tools. Three design options are under consideration.

### Option A: Content-Only MCP

Expose only the Outcome Engine as MCP tools. Minimal surface, fast to build.

```
Tools:
  generate     — Full pipeline: 3 inputs → content + gate + approval
  brief        — Brief only (dry-run mode)
  gate         — Run quality gate on arbitrary content
  status       — What's been published, what's pending
```

**Pros:** Simple, focused, ships fast. Matches the "hide 90% of the system" principle.
**Cons:** Analytics, TikTok scraping, cold email, ad management stay in other surfaces.

### Option B: Full Marketing Suite MCP

Expose the entire gateway's capabilities as MCP tools. Every router becomes a tool.

```
Tools:
  generate           — Outcome Engine pipeline
  brief              — Brief generation
  gate               — Quality gate check
  status             — Pipeline status
  report             — Performance report (GSC + GA4)
  patterns           — Winner pattern analysis
  tiktok_scrape      — Scrape TikTok for content research
  tiktok_generate    — Generate TikTok content batches
  cold_email_warmup  — Check email warmup status
  cold_email_send    — Queue cold email campaigns
  analytics_summary  — Cross-platform analytics
  creative_generate  — Generate creative assets
```

**Pros:** "CMO in a box" — full marketing ops from Claude Code.
**Cons:** Large surface area, more maintenance, some tools (Stripe, WhatsApp) may not make sense as MCP tools.

### Option C: Content + Analytics MCP (Recommended)

Expose content creation plus the feedback loop. You can generate content AND check how it performed — the self-improvement loop lives in the same interface.

```
Tools:
  generate     — Full pipeline: format + site + keyword → content
  brief        — Brief only (preview before committing)
  gate         — Quality gate check on any content
  status       — Published content + pending checks
  report       — Performance report: winners, averages, underperformers
  patterns     — What's working: hook types, formats, personas
```

**Pros:** Closed feedback loop. Generate → publish → check performance → adjust → generate again. All from Claude Code. Matches the harness's self-improvement architecture.
**Cons:** Doesn't include TikTok scraping, cold email, or ad management (but those are lower-frequency operations better served by the gateway API).

### Authentication

| Approach | When to use | Complexity |
|----------|------------|------------|
| **Local MCP (stdio)** | Single developer, same machine | None — runs as subprocess |
| **API key in .mcp.json** | Small team, shared server | Low — reuse existing `CMO_GATEWAY_API_KEY` |
| **OAuth 2.1 + PKCE** | Multi-user, remote access, audit trail | High — needs auth server, token management |

**Recommended path:** Start with local MCP (stdio transport) that calls `engine.generate()` directly via Python imports. No auth needed. Upgrade to remote MCP with OAuth when multi-user access is needed.

### MCP Server Location

Ships with the harness as a drop-in file:

```
your-project/
├── CLAUDE.md
├── .mcp.json              # Registers the MCP server with Claude Code
├── knowledge/
├── harness/
└── scripts/
    └── content/
        └── mcp_server.py  # MCP server — runs as stdio subprocess
```

---

## Key Design Decisions

**MARKETING.md as operating config, not code.** Changing thresholds, adding formats, or updating framework mappings requires editing a markdown file, not Python code. This means non-engineers can tune the pipeline.

**Three laws are enforced, not suggested.** No brief = no write. No gate pass = no publish. No publish without logging. The CLI exits with error code 1 on violation.

**Surgical revision, not full rewrites.** When a gate fails, only the failing dimensions are sent to the LLM. Passing dimensions are explicitly protected with "DO NOT CHANGE" instructions. This prevents the common failure mode where revision fixes one problem while introducing three others.

**Parallel agent architecture.** Domain agents are spawned simultaneously on heartbeat, not sequentially. A 6-agent heartbeat takes as long as the slowest agent, not the sum of all agents.

**Self-improvement has safety thresholds.** Patterns must reach n>=5 samples and 15%+ lift before they're promoted to learned defaults. This prevents one-off flukes from changing pipeline behavior.

**Outcome over options.** The Outcome Engine hides 90% of the system from the user. Instead of exposing 28 configuration points, it takes 3 inputs and makes all decisions internally. Users who need control can override individual fields (persona, angle, word count); users who don't get good defaults automatically.

# Architecture & Memory — load-on-demand detail

> Referenced from `AGENTS.md` / `CLAUDE.md` ("Load-on-demand detail"). Restored 2026-07-05 from the pre-slimming `CLAUDE.md.bak-20260618` sections (Memory & Self-Learning, Directory Structure, Ad Policy Compliance Gate) and updated against the current tree. Every path below is verified by `python scripts/doctor.py` — if you add a path here, doctor must keep passing.

---

## Ad Policy Compliance Gate — full per-platform table

**Before writing any ad copy**, load the platform's policy reference. Every ad must pass platform TOS in addition to quality gates.

| Platform | Policy Reference | Key Restrictions |
|----------|-----------------|------------------|
| Google Ads | `harness/references/google-ads-policy-reference.md` + `harness/references/google-ads-rules.md` | Healthcare certs, financial disclosures, no superlatives without proof |
| Meta (FB/IG) | `harness/references/meta-ads-rules.md` + `harness/references/meta-ads-api-reference.md` | Special Ad Categories (housing/employment/credit), no before/after images, personal attributes ban. **API note:** use `instagram_user_id` not `instagram_actor_id` (EC-01) |
| TikTok | `harness/references/tiktok-ads-policy-reference.md` | No political ads, weight management restrictions, AI content disclosure required |
| LinkedIn | `harness/references/linkedin-ads-rules.md` | Professional context required, B2B claim substantiation |
| Microsoft/Bing | `harness/references/microsoft-ads-rules.md` | Global gambling bans by country, clinical trials ban |
| Pinterest | `harness/references/pinterest-ads-rules.md` | All weight loss ads banned (narrow GLP-1 exception), strict body image rules |
| Snapchat | `harness/references/snapchat-ads-policy-reference.md` | Young audience protections, EU political ad ban |
| Amazon | `harness/references/amazon-ads-policy-reference.md` | 18-month claim evidence rule, no competitor disparagement |
| X/Twitter | `harness/references/x-ads-policy-reference.md` | Verification tier affects ad access, political ad certification by country |
| OpenAI Ads measurement | `harness/references/openai-ads-measurement-reference.md` | Pixel/CAPI consent, hashed identifiers only, event ID deduplication, server-only CAPI token |
| **All platforms — writing guardrails** | `harness/references/ad-write-guardrails.md` | Structural guardrails applied by `/kai-write` for every ad format |
| **All platforms — law** | `harness/references/advertising-compliance.md` | FTC disclosures, GDPR consent, CAN-SPAM, COPPA, click-to-cancel rule |
| **Creator/influencer content** | `harness/references/creator-disclosure.md` + `harness/references/creator-disclosure-presets.json` | Material-connection disclosure per platform, no buried #ad |

Organic posting has its own per-platform rule files (approval doctrine applies — no live-channel mutation without human sign-off):

| Surface | Rules |
|---------|-------|
| X/Twitter organic | `harness/references/x-organic-posting-rules.md` |
| Meta/IG/FB/Threads organic | `harness/references/meta-organic-posting-rules.md` |
| LinkedIn organic | `harness/references/linkedin-organic-posting-rules.md` |
| TikTok organic | `harness/references/tiktok-organic-posting-rules.md` |
| YouTube organic | `harness/references/youtube-organic-posting-rules.md` |
| Pinterest organic | `harness/references/pinterest-organic-posting-rules.md` |
| Snapchat organic | `harness/references/snapchat-organic-posting-rules.md` |
| Reddit organic | `harness/references/reddit-organic-posting-rules.md` |
| All social automation | `harness/references/social-automation-rules.md` |
| Cold email | `harness/references/cold-email-rules.md` |

```
Write ad --> Load platform policy --> Quality gate --> Policy compliance check --> PASS/FAIL
```

Policy freshness: `python scripts/ads/policy_freshness.py` flags stale policy references; the social platform monitor (`scripts/social/platform_change_monitor.py`, cron: `.github/workflows/social-platform-monitor.yml`) tracks platform rule changes into `harness/references/social-platform-monitor-report.md`.

---

## Memory & Self-Learning

The harness learns in both directions: winners feed `knowledge/playbooks/what-works.md` (automated 30-day loop), and failures feed `memory/`. Full doctrine: `docs/system/learning-loop.md`.

### The memory layer

| File | Contents |
|------|----------|
| `memory/MEMORY.md` | Index — read at session start, stays under 200 lines |
| `memory/lessons.md` | Dated trigger→advice lessons, one line each |
| `memory/edge-cases.md` | Platform/API/harness gotchas with enforcement status |
| `memory/what-doesnt-work.md` | Measured losers and anti-patterns with diagnoses |

### Write triggers — append a lesson when:

1. You make the same mistake a second time.
2. A human corrects you and the correction generalizes.
3. A quality gate fails twice for the same reason on one piece.
4. A platform/API/tool behaves differently than the docs or harness references say.
5. A claim you almost shipped turned out to be wrong or unsourceable.

Generalize at write time ("Meta carousel ads need X", not "the Acme campaign needed X"). One line, dated, with a source. Use `python scripts/self_improvement/lesson_capture.py add --trigger "..." --advice "..."` or edit `memory/lessons.md` directly.

### Graduation ladder

A lesson that keeps mattering must become more enforced and more compressed:

```
lessons.md entry --> CLAUDE.md rule / checklist line --> lint rule or contract check + golden case
```

Prefer the executable form: if a lesson can be a regex, threshold, or checklist line, promote it. Promotions into gate scripts REQUIRE a golden corpus case (`evals/golden/manifest.json`) and a passing `golden_check.py` run. New hard blocks need human approval. Promoted edge cases get regression coverage in `tests/test_promoted_edge_cases.py` (EC-06, EC-11, EC-12 are already enforced this way).

### The retro cycle

Run `/kai-retro` monthly or after any sprint with 5+ gated pieces:

```bash
python scripts/self_improvement/lesson_capture.py mine     # recurring gate failures --> candidate lessons
python scripts/self_improvement/lesson_capture.py losers   # undiagnosed 30-day losers
```

Then triage every lesson — promote / keep / merge / retire (never delete; git keeps history).

### Self-validation

```bash
python scripts/doctor.py                       # preflight: referenced files, instruction chain, gates, deps, credentials
python scripts/quality_gates/golden_check.py   # gate verdicts on known content unchanged
```

CI runs both on every push (`.github/workflows/quality-gates.yml`).

---

## Directory Structure

```
kai-cmo-harness/
├── CLAUDE.md                              # Claude Code entry — bridges to AGENTS.md
├── AGENTS.md                              # Canonical agent context (single source of truth)
├── .claude/rules/                         # Load-on-demand detail (this file + scripts-and-tools.md)
│
├── knowledge/                             # Marketing intelligence library
│   ├── _index.md                          # Framework lookup table
│   ├── _quick-reference.md                # One-page cheat sheet
│   ├── _deep-research-prompts.md          # Prompts for generating new frameworks
│   ├── frameworks/
│   │   ├── content-copywriting/           # Writing rules and persuasion
│   │   ├── aeo-ai-search/                 # AEO, patents, AI search ranking
│   │   ├── google-ads/                    # Google Ads deep dives (auction, PMax, RSA)
│   │   └── meta-advertising/              # Meta ad system internals
│   ├── channels/                          # Channel-specific guides (26+ docs)
│   ├── checklists/                        # Validation checklists (36+ docs)
│   ├── personas/                          # 8 audience personas
│   ├── playbooks/                         # Strategic playbooks (50+ docs)
│   ├── people/                            # Cloned-expert knowledge bases
│   ├── research/                          # Research syntheses
│   ├── design/                            # UI/UX design patterns
│   └── examples/                          # Reference examples
│
├── harness/                               # Content pipeline engine + operator surface
│   ├── brief-schema.md                    # Content brief template
│   ├── skill-contracts/                   # Per-format contracts (YAML)
│   ├── skills/                            # 45+ kai-* operator skills (SKILL.md each)
│   ├── workflow-skus/                     # Packaged workflow definitions (YAML)
│   ├── references/                        # Platform-specific rules & policies (see ad-policy table above)
│   └── ARCHITECTURE.md                    # Harness design docs
│
├── memory/                                # Git-backed learning layer
│   ├── MEMORY.md                          # Index — read at session start
│   ├── lessons.md                         # Trigger→advice lessons (dated, one line each)
│   ├── edge-cases.md                      # Platform/API/harness gotchas + enforcement status
│   └── what-doesnt-work.md                # Measured losers and anti-patterns
│
├── kai/                                   # Canonical runtime/workspace layer
│   └── runtime/                           # Agents, goals, connections, audit, business profile
│
├── scripts/
│   ├── doctor.py                          # Preflight self-check — run on every fresh clone
│   ├── harness_cli.py                     # kai-harness pipeline CLI (run/brief/gate/report/patterns/status)
│   ├── harness_config.py                  # Centralized config (env + config.yaml overrides)
│   ├── content/                           # Outcome engine (engine.py), briefs, writers, Discord handler
│   ├── quality/                           # Quality/policy layer
│   ├── quality_gates/                     # Automated content validation
│   │   ├── four_us_score.py               # Four U's scorer (12/16 threshold)
│   │   ├── banned_word_check.py           # Banned word detection
│   │   ├── seo_lint.py                    # SEO rule linter
│   │   ├── agent_readiness_lint.py        # Agent-readiness linter (robots.txt, llms.txt, JS-gating, schema)
│   │   ├── audit_provenance_lint.py       # Audit data-provenance enforcement
│   │   ├── mutation_risk_lint.py          # Live-channel mutation risk linter
│   │   ├── gate_logger.py                 # JSONL run logging --> data/learning/gate_runs.jsonl
│   │   └── golden_check.py                # Golden corpus regression runner (evals/golden/)
│   ├── self_improvement/                  # lesson_capture.py — failure-side learning CLI
│   ├── publish/  social/  intel/  campaigns/  reporting/  ads/   # see scripts-and-tools.md
│   ├── audit/  analytics/  autonomy/  cro/  leads/  security/    # domain script packs
│   └── knowledge_cloner/                  # Expert knowledge extraction pipeline
│
├── agent/                                 # OpenClaw autonomous agent config
├── gateway/                               # Remote runner and connector surface (FastAPI)
├── workspace/                             # Working directory: HEARTBEAT.md, agents/, MARKETING.md, output
├── evals/golden/                          # Golden corpus (gate regression cases)
├── data/                                  # Runtime state: content log, pending checks, learning logs
├── deploy/                                # Deployment scripts
├── docs/                                  # Extended documentation (docs/system/ = doctrine)
└── examples/                              # Usage examples
```

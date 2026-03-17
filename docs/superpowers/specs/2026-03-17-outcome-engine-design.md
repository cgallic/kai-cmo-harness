# Outcome Engine — Surface Collapse Design Spec

**Date:** 2026-03-17
**Status:** Draft (post-review v2)
**Goal:** Collapse the harness from a 28-decision builder tool to a 3-input outcome engine.

---

## Problem

The harness has 30+ frameworks, 17 checklists, 8 personas, 7 skill contracts, and an 8-step usage pattern requiring ~28 user decisions per content request. This surface area positions it as a builder tool. The bottleneck is not capability — the content performs — it's packaging.

Users don't trust systems they have to tune. Every exposed configuration point is a place where they can fail, blame the system, and stop using it.

## Design Principle

Hide 90% of the system. Ship outcomes, not tools. The engine makes the decisions. Users provide intent and approve results.

---

## Architecture

### Core Engine: `generate()`

**Module:** `scripts/content/engine.py`

Single entry point for all content generation. Every surface (CLI, Discord, API) calls this function.

The function is **async** because the quality gate system (`scripts/quality/gate.py`) uses async internally, and the engine needs to await it without `asyncio.run()` nesting issues.

```python
async def generate(
    format: str,           # "blog", "meta-ads", "linkedin", etc.
    site: str,             # "kaicalls", "abp", "buildwithkai", etc.
    keyword: str,          # primary target keyword
    *,
    persona: str = None,
    angle: str = None,
    secondary_keywords: list[str] = None,
    word_count: int = None,
    hook_options: list[str] = None,  # matches existing brief schema field name
    dry_run: bool = False,
    skip_gates: bool = False,
) -> GenerateResult:
```

**Input validation:** The function validates `format` against `VALID_FORMATS` and `site` against `VALID_SITES` (enum sets derived from the framework routing map and config.yaml sites block). Unknown values raise `ValueError` with a message listing valid options.

**Returns:**

```python
@dataclass
class GenerateResult:
    content: str                   # generated content (empty if dry_run)
    brief: dict                    # auto-filled brief (all 18 fields)
    gate_report: dict | None       # gate.propose() return dict (see below)
    status: str                    # "approved" | "held" | "failed" | "draft" | "error"
    proposal_id: str               # from gate.propose(), used for approval flow
    metadata: dict                 # persona used, frameworks loaded, data sources
```

**Gate report type:** The `gate_report` field is the dict returned by `scripts/quality/gate.py`'s `propose()` function. It contains: `proposal_id`, `score`, `grade`, `status` ("approved"/"pending"/"rejected"), `policy`, `top_fixes`, `violation_count`. No new `GateReport` type is needed — the existing gate dict is the interface.

**Draft storage:** Drafts are stored as gate proposals in the existing SQLite database (`scripts/quality/gate.db`) via `gate.propose()`, which already stores content hash, score, status, and violations. The `proposal_id` (e.g., `gp-abc12345`) serves as the draft identifier for the approval flow. No separate draft storage is needed.

### Internal Pipeline

1. **Validate inputs** — check format and site against valid sets, raise on unknown
2. **Resolve config** — load site config, approval policy for format+site
3. **Infer persona** — site-to-audience lookup table, overridable
4. **Route frameworks** — format-to-framework map (see Framework Routing section)
5. **Load skill contract** — format-to-contract YAML (existing `harness/skill-contracts/`)
6. **Auto-fill brief** — single LLM call + API lookups (see Brief Auto-Generation)
7. **(dry_run exit)** — if `dry_run=True`, return `GenerateResult` with brief populated, empty content, status="draft". This runs the LLM brief call (step 6) so users see the full auto-filled brief including creative fields.
8. **Generate content** — call extracted `write_content()` (see Content Generation section)
9. **Run gates** — `await gate.propose(content, policy_name)` from `scripts/quality/gate.py`
10. **Retry if needed** — max 2 auto-retries with targeted failure context via extracted `revise_content()`
11. **Apply approval policy** — engine-level policy layered on top of gate score decision (see Approval Policy section)
12. **Log** — call extracted `log_content()` function (see Content Logging section)

Steps 6 and 8 are the only LLM calls in the happy path. Retries in step 10 add up to 2 more.

### Pipeline Timeout

Worst-case pipeline: brief LLM (10s) + content LLM (30s) + 2 retries (60s each) + API calls (10s) = ~170s. The engine itself does not enforce a timeout — callers do:

- **CLI:** no timeout, runs to completion
- **Discord:** runs async, posts result when done, no HTTP timeout concern
- **HTTP API:** returns a job immediately (see API Surface section)

---

## Framework Routing

**Module:** `scripts/content/engine.py` (inline constant, not a separate file)

The framework map is a hardcoded dict in the engine, matching the existing fallback dict in `harness_cli.py` (lines 580-592). This replaces the MARKETING.md regex parsing path, which is fragile.

```python
FRAMEWORK_MAP: dict[str, list[str]] = {
    "blog":            ["knowledge/frameworks/content-copywriting/algorithmic-authorship.md"],
    "linkedin":        ["knowledge/channels/linkedin-articles.md"],
    "email-lifecycle": ["knowledge/channels/email-lifecycle.md"],
    "cold-email":      ["knowledge/channels/email-lifecycle.md",
                        "harness/references/cold-email-rules.md"],
    "tiktok":          ["knowledge/channels/tiktok-algorithm.md"],
    "meta-ads":        ["knowledge/channels/meta-advertising.md"],
    "google-ads":      ["knowledge/channels/paid-acquisition.md",
                        "harness/references/google-ads-rules.md"],
    "press":           ["knowledge/channels/press-releases.md"],
    "seo":             ["knowledge/frameworks/content-copywriting/algorithmic-authorship.md",
                        "knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md"],
}

VALID_FORMATS = set(FRAMEWORK_MAP.keys())
```

Paths are relative to repo root. The engine resolves them against `_CFG.repo_root`. This is the single source of truth for framework routing — CLAUDE.md's Framework Map table is documentation of this dict, not the other way around.

---

## Content Generation — Extracting from harness_cli.py

The existing `write_content()` in `harness_cli.py` (lines 567-656) is a 90-line function that assembles a prompt from frameworks, winning patterns, skill contracts, site facts, and learned defaults. The engine **does not import it directly** — `harness_cli.py` has module-level side effects (Gemini client init, MARKETING.md parsing).

**Strategy: Extract, don't duplicate.**

Create `scripts/content/_writer.py` by extracting the core prompt assembly logic from `harness_cli.py`:
- `assemble_write_prompt(brief, framework_texts, patterns, contract, site_facts, learned_defaults)` — pure function, no side effects, returns prompt string
- `write_content(brief, prompt_text)` — calls LLM with the assembled prompt

The existing `harness_cli.py` is then updated to import from `_writer.py` instead of defining inline, keeping backward compatibility. This is a refactor of `harness_cli.py`, not "untouched."

Similarly, extract `revise_content(draft, failures, brief)` — the retry logic that sends gate failures back to the LLM for targeted fixes.

**Gate integration:** The engine calls `await gate.propose(content=draft, file_path="<engine-draft>", policy_name=policy_name)` directly. The `FORMAT_TO_POLICY` mapping (already in `harness_cli.py` line 660-670) is also extracted to the engine.

---

## Content Logging — Extracting from content_log.py

The existing `scripts/content/content_log.py` is CLI-only with hardcoded paths (`/opt/cmo-analytics/data/content_log.json`). The engine cannot call it without refactoring.

**Strategy: Add a function-level API alongside the CLI.**

Add to `content_log.py`:
```python
def log_entry(
    url: str, keyword: str, site: str, format: str,
    title: str = "", brief: dict = None, four_us: int = 0,
    notes: str = "", log_file: str = None,
) -> dict:
    """Programmatic API for logging content. Returns the created entry."""
```

This function uses `_CFG.content_log` path (from `harness_config.py`) instead of the hardcoded `/opt/cmo-analytics/data/` path. The existing `main()` CLI entrypoint calls `log_entry()` internally, maintaining backward compatibility.

The engine calls `log_entry()` at step 12 when status is "approved" or "auto."

---

## Persona Inference

**Module:** `scripts/content/persona_resolver.py`

Lookup table mapping site to default persona. No LLM needed.

```yaml
# In config.yaml, under new top-level key
site_persona_defaults:
  kaicalls:
    primary: "Competent Cog"
    secondary: "Obsolescence Anxious"
  buildwithkai:
    primary: "Obsolescence Anxious"
    secondary: "Competent Cog"
  abp:
    primary: "System Manager"
    secondary: "Subscription Serf"
  meetkai:
    primary: "Competent Cog"
    secondary: "Credibility Fighter"
  connorgallic:
    primary: "Obsolescence Anxious"
    secondary: "Credibility Fighter"
  vocalscribe:
    primary: "Competent Cog"
    secondary: "Admin Martyr"
```

**Selection logic:**
1. If `persona` override passed, use it.
2. If keyword contains automation/AI/future signals (regex list: "AI", "automate", "replace", "future-proof", "obsolete", "machine learning"), use secondary.
3. Otherwise, use primary.

**Config loading:** `persona_resolver.py` reads config.yaml independently via `_load_config_yaml()` from `harness_config.py` (or extend `load_config()` to parse the new key — see Config Integration section).

---

## Brief Auto-Generation

**Module:** `scripts/content/brief_generator.py`

Fills all 18 brief fields from 3 inputs. One LLM call for creative fields, lookups and API calls for data fields.

**Field names match the existing brief schema** (`harness/brief-schema.md`):

| Field | Source | Method |
|-------|--------|--------|
| `target_site` | `site` param | Direct |
| `target_keyword` | `keyword` param | Direct |
| `format` | `format` param | Direct |
| `persona` | Persona resolver | Lookup |
| `word_count_target` | Skill contract | Lookup |
| `secondary_keywords` | DataForSEO API, fallback LLM | API or inferred |
| `current_rank` | GSC API via gateway | API (SEO only, nullable) |
| `monthly_impressions` | GSC API via gateway | API (SEO only, nullable) |
| `current_ctr` | GSC API via gateway | API (SEO only, nullable) |
| `competitor_url` | GSC/DataForSEO, fallback LLM | API or inferred |
| `competitor_weakness` | LLM analysis | Single LLM call |
| `angle` | LLM from keyword + persona + competitor | Single LLM call |
| `hook_options` (3) | LLM from angle + persona hooks | Single LLM call |
| `audience_pain` | Persona profile | Lookup |
| `proof_available` | Content library scan + site knowledge | File scan |
| `cta` | Site default CTAs from config | Lookup |
| `publish_date` | Today + lead time from contract | Computed |
| `internal_links` | Content log scan for same site + related keywords | Data query |

That is 18 fields (counting `current_rank`, `monthly_impressions`, `current_ctr` as three).

The creative fields (`angle`, `hook_options`, `competitor_weakness`, `secondary_keywords` fallback) are generated in a single LLM prompt. The prompt receives persona profile, keyword, competitor data (if available), and existing content on the site as context.

**API degradation:** Every API-sourced field has an LLM fallback. If DataForSEO or GSC is down, the brief is less data-rich but still valid. `metadata.data_sources` tracks provenance per field.

---

## Approval Policy

**Module:** `scripts/content/approval_policy.py`

Config-driven, per format+site. Set once, don't ask every time.

```yaml
# In config.yaml, under new top-level key
approval_policy:
  default: "hold"
  overrides:
    - format: "meta-ads"
      site: "*"
      policy: "hold"
    - format: "blog"
      site: "kaicalls"
      policy: "auto"
    - format: "cold-email"
      site: "*"
      policy: "hold"
```

**Three modes:**
- **hold** — gates pass, draft queued for human approval
- **auto** — gates pass, content logged and marked ready to publish
- **reject_only** — gates fail, human sees it; gates pass, it ships

**Lookup order:** specific match (format+site) > format wildcard > default.

**Relationship to existing gate policies:** The gate system (`scripts/quality/gate.py`) uses YAML policy files in `scripts/quality/policies/` to determine score thresholds for approved/pending/rejected. This happens at step 9 (gate execution). The approval policy in config.yaml is a **separate layer** applied at step 11 — it determines what happens AFTER the gate verdict:

| Gate Verdict | Approval Policy = hold | Approval Policy = auto | Approval Policy = reject_only |
|---|---|---|---|
| Gate: approved (score >= threshold) | Hold for human | Auto-ship | Auto-ship |
| Gate: pending (score in hold range) | Hold for human | Hold for human | Hold for human |
| Gate: rejected (score < threshold) | Hold for human | Hold for human | Hold for human |

The approval policy only overrides the gate on `auto` mode when the gate says `approved`. It never overrides a gate rejection.

---

## NLP Intent Parser

**Module:** `scripts/content/intent_parser.py`

Thin layer that parses natural language into `(format, site, keyword)`. Used by Discord and conversational surfaces. CLI and API bypass it when structured params are provided.

```python
@dataclass
class ParsedIntent:
    format: str | None
    site: str | None
    keyword: str | None
    confidence: float        # 0-1
    missing: list[str]       # fields that couldn't be extracted
    overrides: dict          # extras: persona, tone, length hints
```

**Prompt:** Constrained extraction with valid enums for format and site (the enums are `VALID_FORMATS` and `VALID_SITES` from the engine). Returns JSON. One Haiku call (~0.1 cents, <1s latency).

**Confidence handling:**
- `>= 0.8` and all three fields present: call `generate()` directly
- Any field missing: ask for just that field ("Which site is this for?")
- `< 0.5`: ask for full clarification

No silent failures. The parser either gets it right or asks.

---

## Surface Wrappers

### CLI — `scripts/content/cli_generate.py`

```bash
# Structured
kai-harness generate --format blog --site kaicalls --keyword "AI receptionists"

# With overrides
kai-harness generate --format blog --site kaicalls --keyword "AI receptionists" \
  --persona "Shock Absorber" --dry-run

# Natural language (routes through intent parser)
kai-harness generate "blog about AI receptionists for kai calls"
```

If first positional arg is a quoted string: intent parser. If `--format` flag present: direct to `generate()`.

The CLI wrapper calls `asyncio.run(generate(...))` since it's the top-level sync entrypoint.

**Migration from harness_cli.py:** The existing `kai-harness run` command continues to work unchanged. The new `kai-harness generate` command is added alongside it. Over time, `run` can be deprecated in favor of `generate`, but there is no breaking change. The `report`, `patterns`, `status`, `gate`, and `brief` commands remain on `harness_cli.py`.

### Discord — extends `scripts/content/harness_discord.py`

```
!kai blog about AI receptionists for kai calls
!kai meta-ad for buildwithkai about voice agent pricing
```

All input goes through intent parser. On low confidence, asks in-channel. Posts status updates during pipeline, posts result when done. Approval via reactions or thread replies.

### HTTP API — new route in `gateway/main.py`

```
POST /generate
{
  "format": "blog",
  "site": "kaicalls",
  "keyword": "AI receptionists"
}

# Or natural language
POST /generate
{
  "intent": "blog about AI receptionists for kai calls"
}
```

**The API is async/job-based.** `POST /generate` returns immediately with a job ID:
```json
{"job_id": "gen-abc123", "status": "queued"}
```

The pipeline runs in a background task. Poll status via:
```
GET /generate/gen-abc123
```

Returns `GenerateResult` as JSON when complete. This avoids HTTP timeout issues — the pipeline can take 2-3 minutes.

All wrappers are stateless. The engine holds all logic.

---

## Config Integration

**Module:** `scripts/harness_config.py` — extend `load_config()`

Two new top-level keys in `config.yaml`: `site_persona_defaults` and `approval_policy`. These are loaded in `load_config()` and stored on `HarnessConfig`:

```python
@dataclass
class HarnessConfig:
    # ... existing fields ...
    site_persona_defaults: dict = field(default_factory=dict)
    approval_policy: dict = field(default_factory=lambda: {"default": "hold", "overrides": []})
```

In `load_config()`:
```python
cfg.site_persona_defaults = raw.get("site_persona_defaults", {})
cfg.approval_policy = raw.get("approval_policy", {"default": "hold", "overrides": []})
```

This keeps all config loading in one place. The persona resolver and approval policy modules read from `get_config()`.

---

## Error Handling

**Input validation:**
- Unknown format or site: `ValueError` with list of valid options. Surfaces translate to user-friendly message.

**Gate failures:**
- Retry 1: LLM receives specific failures with line numbers and rewrites targeted sections
- Retry 2: stronger constraints, explicit list of lines to fix
- After 2 failures: `status="failed"`, full gate report attached, best draft returned

**API failures (DataForSEO, GSC):**
- Brief gen degrades gracefully. Every API field has LLM fallback.
- `metadata.data_sources` tracks which fields came from APIs vs inference.

**Intent parser failures:**
- Asks for missing fields. Never guesses on low confidence.

**LLM failures (timeout, rate limit):**
- Exponential backoff, max 3 retries (existing `harness_config.py` settings).
- If generation fails completely: `status="error"`, no draft produced.

**Brief LLM returns invalid JSON:**
- Parse with fallback: try `json.loads()`, then strip markdown fences and retry, then regex extract JSON block. If all fail, `status="error"` with message "Brief generation failed — try again or provide overrides."

---

## File Structure

```
scripts/content/
├── __init__.py            # package marker
├── engine.py              # generate() core function + FRAMEWORK_MAP + VALID_FORMATS/SITES
├── _writer.py             # extracted from harness_cli.py: assemble_write_prompt(), write_content(), revise_content()
├── intent_parser.py       # NLP natural language → structured params
├── brief_generator.py     # auto-fill 18-field brief from 3 inputs
├── persona_resolver.py    # site→persona lookup
├── approval_policy.py     # config-driven hold/auto/reject_only
├── cli_generate.py        # CLI wrapper (kai-harness generate)
├── content_log.py         # MODIFIED: add log_entry() function API alongside existing CLI
└── harness_discord.py     # MODIFIED: add !kai shorthand, route through engine

# Modified existing files:
scripts/harness_cli.py     # REFACTORED: write_content() imports from _writer.py
scripts/harness_config.py  # EXTENDED: add site_persona_defaults + approval_policy to HarnessConfig
gateway/main.py            # EXTENDED: add POST /generate route (async job-based)
config.yaml                # EXTENDED: add site_persona_defaults, approval_policy sections
```

**Package structure:** `scripts/content/` becomes a proper Python package with `__init__.py`. The existing files in that directory (`harness_discord.py`, `content_log.py`, etc.) are already there — the new modules join them.

---

## What's Hidden vs Exposed

### Hidden (90%)
- Framework selection and loading (30 frameworks)
- Brief field population (18 fields)
- Persona inference logic
- Skill contract matching
- Quality gate orchestration and retry
- Content logging and 30-day check scheduling
- Statistical guardrails on the learning loop

### Exposed to Users (10%)
- 3 required inputs: format, site, keyword
- Generated draft for approval
- Gate pass/fail (binary)
- Override params for power users (optional, never required)
- `--dry-run` to inspect brief before generation (includes LLM brief call)

### Exposed to Operators (config)
- `approval_policy` in config.yaml
- `site_persona_defaults` in config.yaml
- Threshold overrides (existing config.yaml fields)

---

## Testing Strategy

1. **Unit: persona_resolver** — verify site-to-persona mapping, keyword signal detection, override precedence, unknown site handling
2. **Unit: intent_parser** — test known inputs against expected `ParsedIntent` output, verify low-confidence triggers clarification, verify unknown format/site handling
3. **Unit: brief_generator** — mock API responses, verify all 18 fields populated with correct field names (matching `harness/brief-schema.md`), verify LLM fallback when APIs fail, test invalid JSON recovery from LLM
4. **Unit: approval_policy** — verify lookup order (specific > wildcard > default), verify all three modes, verify interaction matrix with gate verdicts
5. **Unit: framework_routing** — verify all formats map to existing framework files, verify files exist at mapped paths, verify unknown format raises ValueError
6. **Unit: content_log.log_entry()** — verify entry creation, verify path uses config (not hardcoded), mock file I/O
7. **Integration: engine.generate()** — end-to-end with mocked LLM, verify pipeline order, gate enforcement, retry logic. Specific failure scenarios:
   - Brief LLM returns invalid JSON → error status
   - DataForSEO API timeout → LLM fallback used, brief still valid
   - Gate retries exhaust → status="failed", best draft returned
   - Unknown format → ValueError before any LLM calls
8. **Integration: surface wrappers** — verify CLI arg parsing (structured and natural language modes), Discord command parsing, API request/response format, API job-based async flow

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary user | Both power users and novices | Interface works for novices, power users get optional overrides |
| Deployment surface | Core engine first, all three wrappers | Engine is the product, surfaces are skins |
| Approval model | Configurable per site/format, defaults to hold | Easy to set once, reduces per-request decisions |
| Architecture | Hybrid: structured core + NLP skin | Deterministic core for reliability, NLP for convenience, NLP failures ask instead of guessing |
| Persona inference | Lookup table, not LLM | Deterministic, testable, no added latency or cost |
| Brief generation | Single LLM call + API lookups | Minimize LLM calls, maximize data quality when APIs available |
| Framework routing | Hardcoded dict in engine, not MARKETING.md parsing | MARKETING.md regex parsing is fragile; dict is testable and explicit |
| Quality gates | Use existing gate.propose() from scripts/quality/gate.py | Already provides programmatic async API with SQLite storage |
| Gate report type | Reuse gate.propose() dict, no new type | The existing dict has all needed fields; adding a wrapper type adds no value |
| Draft storage | Reuse gate proposal SQLite storage | gate.propose() already stores content, score, status; proposal_id is the draft ID |
| Content generation | Extract from harness_cli.py into _writer.py | Avoids module-level side effects from importing harness_cli.py directly |
| Content logging | Add function API to existing content_log.py | Preserves CLI backward compat while enabling programmatic use |
| generate() sync/async | Async | gate.propose() is async; avoiding asyncio.run() nesting |
| HTTP API model | Job-based (POST returns job ID, GET polls status) | Pipeline takes 2-3 min; synchronous HTTP would timeout |
| CLI migration | Add `generate` alongside existing `run` command | No breaking change; deprecate `run` later |
| dry_run semantics | Runs brief LLM call, skips content generation | Users need to see the full auto-filled brief to evaluate it |
| Config loading | Extend harness_config.py load_config() | Single config loading path; no independent YAML reads |
| Field naming | Match existing brief-schema.md exactly | hook_options not hook_variants, monthly_impressions not impressions, current_ctr not ctr |

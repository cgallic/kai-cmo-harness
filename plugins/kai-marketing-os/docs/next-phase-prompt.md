# Next Phase: Two-Plan Execution Prompt

You are continuing work on the Kai CMO Harness (`E:\Dev2\kai-cmo-harness-work`). A competitive intelligence reassessment was just completed (`docs/competitive-intelligence-reassessment.md`) that identified critical gaps. This prompt defines two parallel plans.

Read `CLAUDE.md` and `docs/competitive-intelligence-reassessment.md` for full context before starting.

---

## Plan 1: Social Data Ingestion — Close the Learning Loop

### Problem

The closed-loop learning system (`scripts/self_improvement/`) currently only ingests data from Google Search Console and Google Analytics 4. The harness publishes content to TikTok, LinkedIn, email, Meta ads, and other channels — but has no way to pull performance data back from those platforms. The learning loop is blind to social performance.

Without social ingestion, the harness cannot:
- Classify TikTok videos as winners/losers based on actual view counts and engagement
- Learn which LinkedIn post formats drive impressions
- Correlate email open rates with content quality scores
- Feed Meta ad ROAS back into quality threshold calibration

### Goal

Find and integrate the **easiest possible connectors** for pulling social media metrics into the harness. Prioritize low-friction, low-maintenance solutions over custom API builds. The owner needs to tie these in quickly without building custom OAuth flows or maintaining token refresh logic.

### Platforms to Connect (Priority Order)

| Platform | Key Metrics Needed | Current State |
|----------|-------------------|---------------|
| **TikTok** | Views, completion rate, shares, saves, comments, profile visits | `gateway/adapters/tiktok_adapter.py` exists — scraping-based, not API |
| **LinkedIn** | Post impressions, engagement rate, click-through, follower growth | Nothing exists |
| **Email (Instantly)** | Open rate, click rate, reply rate, bounce rate | `gateway/routers/cold_email.py` exists — partial |
| **Meta Ads** | ROAS, CPM, CTR, conversion rate, frequency | Nothing exists |
| **Google Ads** | CPC, CTR, conversion rate, quality score | Nothing exists |
| **X/Twitter** | Impressions, engagement rate, link clicks | Nothing exists |

### Approach: Evaluate These Connector Options

For each platform, evaluate these options in order of preference:

1. **Managed integration platforms** (easiest)
   - Supermetrics, Funnel.io, Fivetran, Airbyte, Stitch
   - Can they dump to a simple destination (CSV, JSON, webhook, Google Sheets)?
   - What's the cost? Free tier available?

2. **Platform-native webhooks or export APIs**
   - TikTok Business API, LinkedIn Marketing API, Meta Marketing API
   - How painful is OAuth setup? Token refresh?
   - Rate limits? Data freshness (real-time vs daily)?

3. **Zapier / Make (Integromat) connectors**
   - Can a Zap push platform metrics to a webhook endpoint on the gateway?
   - What triggers are available (new post published, daily summary)?

4. **Google Sheets as middleware**
   - Supermetrics → Google Sheets → harness reads Sheets API
   - Simple, visual, debuggable, non-technical users can inspect

5. **Direct API integration** (last resort)
   - Only if nothing simpler works
   - Must use existing gateway pattern (`gateway/adapters/` + `gateway/routers/`)

### Deliverables for Plan 1

1. **Connector evaluation matrix** — For each platform: recommended connector, setup complexity (1-5), monthly cost, data freshness, maintenance burden
2. **Data schema** — Standardized JSON format for social metrics that maps to `content_log.json` entries (must include: `platform`, `post_id`, `published_at`, `metrics: {}`, `fetched_at`)
3. **Ingestion adapter** — At minimum for TikTok and LinkedIn:
   - Adapter in `gateway/adapters/` that normalizes platform data to common schema
   - Router in `gateway/routers/` that exposes ingestion endpoints
   - Integration with `performance_check.py` so social metrics flow into the learning loop
4. **Updated performance_check.py** — Extend winner/loser classification to include social metrics:
   - TikTok: completion rate >= X%, views >= Y as winner criteria
   - LinkedIn: impressions >= X, engagement rate >= Y%
   - Email: open rate >= X%, click rate >= Y%
5. **Updated pattern_extract.py** — Extend pattern extraction to correlate quality scores with social performance (not just GSC/GA4)

### Constraints

- Do NOT build custom OAuth implementations if a managed connector exists
- Do NOT require manual CSV uploads — everything must be automated or webhook-driven
- Prefer solutions that cost $0-50/month over free solutions that require 10x the maintenance
- The gateway already has API key auth (`gateway/auth.py`) — new endpoints must use it
- All new adapters must follow existing patterns (see `gateway/adapters/tiktok_adapter.py` as reference)

---

## Plan 2: Fix Everything the Reassessment Flagged

### Problem

The competitive intelligence reassessment identified engineering vulnerabilities, knowledge base gaps, statistical weaknesses, and missing infrastructure. These need to be fixed before the harness can be considered production-grade.

### Fixes Organized by Priority

#### CRITICAL — Fix This Week

**1. Shell injection in legacy scripts**

| File | Issue | Fix |
|------|-------|-----|
| `scripts/content/harness_discord.py` | `os.system()` with f-string interpolation | Replace with `subprocess.run([...], check=True)` using list args |
| `scripts/content/newsletter_digest.py` | `subprocess.Popen(..., shell=True)` | Replace with `subprocess.Popen([...])` without shell=True |

Test: Run both scripts after fix. Verify Discord messages still post. Verify newsletter still generates.

**2. Unvalidated `request.options` dict in gateway routers**

| File | Issue | Fix |
|------|-------|-----|
| `gateway/routers/tiktok.py` | `request.options.get("days", 7)` — no type validation | Create `TikTokVideosRequest` Pydantic model with typed fields |
| `gateway/routers/cold_email.py` | `brand`, `domain`, `user` extracted without validation | Create typed request models per endpoint |
| `gateway/routers/tasks.py` | `tasks` list extracted without validation | Add Pydantic model with `List[str]` constraint |
| `gateway/routers/analytics.py` | Options dict passed through | Type the options |
| `gateway/routers/creative.py` | Options dict passed through | Type the options |
| All routers using `WebhookRequest` | `options: Dict[str, Any]` is a catch-all | Replace with endpoint-specific Pydantic models |

Pattern: For each router, replace generic `WebhookRequest.options` access with a typed Pydantic model. Example:
```python
# Before
days = request.options.get("days", 7)

# After
class TikTokVideosRequest(BaseModel):
    client: str
    days: int = Field(7, ge=1, le=365)
    limit: int = Field(20, ge=1, le=500)
```

**3. Add startup validation**

In `gateway/main.py` lifespan and `agent/__main__.py`:
- Validate required API keys exist at startup (not first use)
- Validate config.yaml paths exist
- Fail fast with clear error messages

#### HIGH — Fix This Sprint

**4. Add CI/CD pipeline**

Create `.github/workflows/ci.yml`:
- Run all 49 tests on push to main and on PRs
- Run `bandit` for security scanning (catches shell injection, hardcoded passwords)
- Run `black` for formatting
- Run `mypy` for type checking (at least on gateway/ and scripts/quality/)

**5. Add missing TikTok skill contract**

Create `harness/skill-contracts/tiktok-script.yaml`:
- Reference `knowledge/channels/tiktok-algorithm.md` and `tiktok-shop.md`
- Word count: 30-65 words (matches generator constraints)
- Line count: 7-12 lines
- Quality gates: CS-07 (no AI clichés), tiktok-script policy
- On fail: revise with failure report (max 2 retries)
- On pass: post for approval

**6. Add gateway tests**

Create `gateway/tests/`:
- Test auth middleware (valid key, invalid key, missing key, debug mode)
- Test each router with valid and invalid payloads
- Test job queue (creation, polling, cleanup)
- Test adapter error handling (API timeout, bad response)

**7. Add per-client rate limiting**

In `gateway/main.py` middleware:
- Track requests per API key in memory (dict with timestamp deque)
- Reject with 429 if > N requests in M seconds (configurable)
- Log rate limit hits

#### MEDIUM — Fix This Month

**8. Strengthen statistical methodology in learning loop**

In `scripts/self_improvement/harness_defaults_update.py`:
- Raise minimum n from 3-5 to 10 for pattern detection
- Add Welch's t-test (scipy.stats.ttest_ind) before accepting patterns — require p < 0.05
- Add confidence intervals to Discord notifications ("Tuesday is best, +22% ± 8%, p=0.03, n=12")
- Add seasonal flag: if all winners are from same 2-week window, mark pattern as "unconfirmed — seasonal risk"

In `scripts/self_improvement/pattern_extract.py`:
- Add survivorship bias warning: count rejected drafts per period and report ratio
- Add multi-variate check: when reporting "persona X wins," also check if persona X coincidentally targeted easier keywords

**9. Add feedback drift detection**

Create `scripts/self_improvement/drift_check.py`:
- Compare current thresholds against original defaults
- If any threshold has shifted >20% from baseline, flag for human review
- If auto-approve threshold has dropped 3+ times consecutively, halt auto-updates and notify via Discord
- Run weekly after `harness_defaults_update.py`

**10. Dockerize**

Create `Dockerfile` and `docker-compose.yml`:
- Python 3.11 base
- Install dependencies from requirements.txt
- Expose gateway on port 8000
- Agent runs as separate service
- SQLite volumes for persistence
- .env file for secrets

**11. Add TikTok playbook**

Create `knowledge/playbooks/tiktok-playbook.md`:
- Synthesize `tiktok-algorithm.md` + `tiktok-shop.md` + Algorithm Engine insights
- Include: when to post (data-backed), content type matrix, growth stages (0-1K, 1K-10K, 10K-100K), live selling integration
- Reference the 6-step scripting framework and 3-second rule

#### LOW — Ongoing

**12. Knowledge base refresh cycle**

Establish quarterly refresh cadence:
- Perplexity architecture: Re-test monthly (fastest decay)
- Meta ad internals: Check against Meta Engineering blog quarterly
- TikTok algorithm: Re-validate signal weights quarterly
- Google patents: Check for new filings from tracked engineers quarterly
- Add `last_reviewed` frontmatter to each knowledge file

**13. Add audit logging for agent actions**

In `agent/loop.py`:
- Log task creation, start, completion, failure to structured JSON
- Include: timestamp, task_id, task_type, client, duration, result_summary
- Persist to `agent_audit.log` (rotated daily)

### Execution Order

```
Week 1:  #1 (shell injection) + #2 (gateway validation) + #3 (startup validation)
Week 2:  #4 (CI/CD) + #5 (TikTok contract) + #6 (gateway tests)
Week 3:  #7 (rate limiting) + #8 (statistics) + #9 (drift detection)
Week 4:  #10 (Docker) + #11 (TikTok playbook)
Ongoing: #12 (knowledge refresh) + #13 (audit logging)
```

### Definition of Done

- All 49 existing tests still pass
- New tests added for every fix (gateway tests, drift detection tests, rate limiting tests)
- CI pipeline runs green on push
- No `bandit` findings at MEDIUM or above
- Docker compose starts gateway + agent successfully
- Social data from at least TikTok and LinkedIn flows into `content_log.json`
- Learning loop classifies social content as winner/average/underperformer
- Discord notifications include social performance alongside GSC/GA4

---

## How to Use This Prompt

Start a new Claude Code session and paste this prompt. Then say:

- **"Execute Plan 1"** — to research and build social data connectors
- **"Execute Plan 2"** — to fix all flagged issues in priority order
- **"Execute both"** — to run both plans, starting with Plan 2 critical fixes (they unblock Plan 1's gateway work)

Recommended: Start with Plan 2 critical fixes (#1-3), then Plan 1 connector research, then Plan 2 remaining fixes interleaved with Plan 1 implementation.

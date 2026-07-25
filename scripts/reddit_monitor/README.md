# Community Opportunity Monitor (profile-driven)

Monitors subreddits via RSS, keyword-filters posts, runs an LLM eval against
a profile-specific prompt, and posts drafted replies to Discord. Originally
built for KaiCalls (`hermes:/opt/cmo-analytics/reddit-monitor/`) and
generalized on 2026-04-23 so new profiles can be added without touching the
engine.

The production KaiCalls path uses `reddit_digest.py`: it combines subreddit RSS,
bounded Google Organic searches, and named-business prospecting from DataForSEO
Business Listings plus recent Google reviews. It writes one daily review page
and never drafts or posts a reply.
Search queries can discover public Facebook Group pages, but the monitor never
logs in, joins a group, or reads private content. Each configured Google query
runs at most once per day even though Reddit collection runs hourly; the seen
state records the pre-call attempt, reserved budget, and returned provider cost.
The KaiCalls profile runs 10 public-search queries and rotates through 5 of 90
category/metro listing segments per day. It can submit at most 50 asynchronous
review tasks. The normal configured workload reserves `$0.20` for organic search,
`$0.15` for listings, and `$0.25` for review tasks: `$0.60/day`. Independent
source ceilings total `$0.90/day`, below Connor's `$1/day` limit. Reservations
are persisted before paid calls, so provider timeouts fail closed.
Businesses become eligible for a fresh review check after 60 days instead of
being suppressed forever.

Keyword matches are candidates, not leads. Public conversations pass only when
the classifier identifies a buyer, a supported intent type, at least 0.8
confidence, and an exact source quote. Named businesses pass only when a recent
Google review contains an exact quote proving unanswered-phone, callback,
intake, or after-hours pain. Generic low ratings and vague communication
complaints are rejected. Output includes the source quote, review link, business
name, phone, website, and market for manual review.

```
scripts/reddit-monitor/
├── reddit_listener.py          # generalized engine
├── reddit_digest.py            # evidenced public conversations + named prospects
├── review_prospecting.py       # listings/review task rotation and qualification
├── run_listener.sh             # cron/pipeline wrapper
├── profiles/
│   ├── kaicalls.json           # KaiCalls config (subs, keywords, webhook env)
│   ├── kaicalls.prompt.md      # KaiCalls LLM prompt (builder identity, voice)
│   ├── kaicalls-digest.json    # spend limits, sources, categories, metros
│   ├── kaicalls-digest.prompt.md
│   ├── kaicalls-review-prospect.prompt.md
│   ├── example.json            # scaffold for a new profile
│   └── example.prompt.md       # scaffold for a new prompt
└── .seen/                      # per-profile seen-posts state (runtime-created)
    └── <profile>.json
```

## Pipeline

1. Load profile JSON + its prompt file.
2. Pull `/r/<sub>/new.rss` for each subreddit in the profile (up to `posts_per_sub`, default 25).
3. Keyword pre-filter against `trigger_keywords`.
4. For each match, call the LLM (`model`, default `gpt-4o-mini`) with the prompt template — substitutes `{subreddit}`, `{title}`, `{content}`. Prompt must instruct the model to return JSON with `pass`, `reason`, `angle`, `draft_response`.
5. Passing posts → Discord webhook named by `discord_webhook_env`.
6. Dedup via ring buffer in `.seen/<profile>.json` (keeps last `seen_limit`, default 2000).

## Run

```bash
# dry run (prints drafts, no Discord)
python reddit_listener.py --profile kaicalls --dry-run

# live
export REDDIT_MONITOR_DISCORD_WEBHOOK_KAICALLS="https://discord.com/api/webhooks/..."
python reddit_listener.py --profile kaicalls

# wrapper (emits ALERTS_JSON line — use for cron/pipelines)
bash run_listener.sh kaicalls

# scored lead-finding digest (writes a review page; no reply is posted)
python reddit_digest.py --profile kaicalls-digest --dry-run --out-dir /tmp/opps

# one-query paid-source canary, isolated from production state/output
python reddit_digest.py --profile kaicalls-digest --dry-run --search-only \
  --search-query-cap 1 --state-dir /tmp/opps-state --out-dir /tmp/opps

# named-prospect source only (listing scan + review task submit/poll)
python reddit_digest.py --profile kaicalls-digest --dry-run --prospecting-only \
  --state-dir /tmp/opps-state --out-dir /tmp/opps
```

## Required env

- `OPENAI_API_KEY` — for the LLM eval (reads from sibling/parent/repo-root `.env`).
- `<discord_webhook_env>` — per-profile; the profile names the env var it expects. Example: `REDDIT_MONITOR_DISCORD_WEBHOOK_KAICALLS`.

## Adding a new profile

1. Copy `profiles/example.json` → `profiles/<name>.json`, edit `subreddits`, `trigger_keywords`, `discord_webhook_env`.
2. Copy `profiles/example.prompt.md` → `profiles/<name>.prompt.md`, rewrite identity rules, voice, accept/reject criteria. Must keep `{subreddit}`, `{title}`, `{content}` placeholders and end with a JSON-only instruction that produces the 4-key schema.
3. Set the webhook env var and run `python reddit_listener.py --profile <name> --dry-run` first.

## Profile schema

| Key | Required | Default | Purpose |
|-----|----------|---------|---------|
| `subreddits` | yes | — | list of sub names (without `r/`) |
| `trigger_keywords` | yes | — | case-insensitive substrings for pre-filter |
| `prompt_file` | yes | — | filename inside `profiles/`; uses `.format()` with `{subreddit}`, `{title}`, `{content}` |
| `discord_webhook_env` | yes | — | env var name holding the Discord webhook URL |
| `name` | no | filename stem | used for state filename and logging |
| `alert_title` | no | `Reddit Opportunity` | shown in Discord alert header |
| `model` | no | `gpt-4o-mini` | OpenAI model id |
| `seen_limit` | no | 2000 | ring-buffer size for seen post IDs |
| `posts_per_sub` | no | 25 | max posts pulled per sub per run |
| `content_max_chars` | no | 1200 | post body truncation before LLM |

Digest profiles may also set:

| Key | Default | Purpose |
|-----|---------|---------|
| `search_queries` | `[]` | Public-web queries fetched through DataForSEO Google Organic |
| `search_results_per_query` | `20` | Requested result bound; code caps paid depth at 10 |
| `search_daily_query_cap` | `8` | Hard cap on paid Google queries per profile and day |
| `search_timeframe` | `m` | Google index freshness filter (`h`, `d`, `w`, `m`, `mn`, or `y`) |
| `search_verticals` | `[]` | Buyer verticals expanded through each query template |
| `search_query_templates` | `[]` | Templates containing `{vertical}` |
| `search_max_daily_cost_usd` | `1.0` | Fail-closed daily paid-source ceiling |
| `search_cost_guard_per_query_usd` | `0.01` | Pre-call reservation used before the provider returns actual cost; KaiCalls sets `$0.02` |
| `search_candidate_cap_per_query` | `3` | Maximum keyword-matching results retained from one query for evidence scoring |
| `score_threshold` | `70` | Minimum LLM fit score written to the review page |
| `max_items` | `12` | Maximum daily review-page items after URL dedupe |
| `prospecting_enabled` | `false` | Enables named-business listings and Google-review evidence |
| `prospecting_max_daily_cost_usd` | `0.7` | Independent fail-closed ceiling for listings plus review tasks |
| `prospecting_daily_listing_cap` | `0` | Number of category/metro segments rotated each day |
| `prospecting_daily_review_task_cap` | `50` | Maximum asynchronous review tasks submitted per day |
| `prospecting_business_refresh_days` | `60` | Cooldown before a business can be checked for newer reviews |

The digest reads `DATAFORSEO_AUTH_B64` or
`DATAFORSEO_LOGIN` + `DATAFORSEO_PASSWORD`. On `agent`, those credentials remain
in `/srv/cmo-agent-system/.env`. Set `REDDIT_MONITOR_ENV` to an explicit env
file when running an isolated copy that also needs the live scorer credential.

## Prior-run state migration

To migrate the hermes KaiCalls seen-posts file into this layout:

```bash
mkdir -p scripts/reddit-monitor/.seen
scp root@hermes:/opt/cmo-analytics/reddit-monitor/seen_posts.json \
    scripts/reddit-monitor/.seen/kaicalls.json
```

(Or let it rebuild from scratch — the ring buffer will refill on the first
few runs, worst case you get duplicate alerts for posts from the last 24h.)

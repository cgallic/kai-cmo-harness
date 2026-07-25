# Community Opportunity Monitor (profile-driven)

Monitors subreddits via RSS, keyword-filters posts, runs an LLM eval against
a profile-specific prompt, and posts drafted replies to Discord. Originally
built for KaiCalls (`hermes:/opt/cmo-analytics/reddit-monitor/`) and
generalized on 2026-04-23 so new profiles can be added without touching the
engine.

The production KaiCalls path uses `reddit_digest.py`: it combines subreddit RSS
with Google Organic results from the existing DataForSEO account, scores each
result, and writes one daily review page. It never drafts or posts a reply.
Search queries can discover public Facebook Group pages, but the monitor never
logs in, joins a group, or reads private content. Each configured Google query
runs at most once per day even though Reddit collection runs hourly; the seen
state records the pre-call attempt, reserved budget, and returned provider cost.
The KaiCalls profile combines 7 fixed queries with 4 templates across 10 buyer
verticals for 47 daily searches. Three templates target indexed public Facebook
Group posts; one searches the wider public web for direct recommendations and
missed-call pain. Each attempt reserves `$0.02` before the provider call, so the
configured set can authorize at most `$0.94/day`. Current canaries observed
`$0.01` for `site:` searches and lower cost for general searches, making expected
spend roughly `$0.39/day`. The hard `$1/day` ceiling remains fail-closed.

```
scripts/reddit-monitor/
├── reddit_listener.py          # generalized engine
├── reddit_digest.py            # scored Reddit + public-search review page
├── run_listener.sh             # cron/pipeline wrapper
├── profiles/
│   ├── kaicalls.json           # KaiCalls config (subs, keywords, webhook env)
│   ├── kaicalls.prompt.md      # KaiCalls LLM prompt (builder identity, voice)
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
| `score_threshold` | `70` | Minimum LLM fit score written to the review page |
| `max_items` | `12` | Maximum daily review-page items after URL dedupe |

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

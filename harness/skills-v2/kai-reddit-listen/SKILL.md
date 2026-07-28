---
name: kai-reddit-listen
description: Monitor Reddit for conversation-fit opportunities — watches a list of subreddits, keyword-filters new posts, runs an LLM eval in your voice (with identity guardrails), and drops drafted replies into Discord. Use when "reddit monitor", "reddit listener", "reddit outreach", "watch subreddits", "find reddit opportunities", "listen on reddit", "community listening", or any request to automate finding posts you should reply to on Reddit.
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A running Reddit listener that surfaces posts the brand can honestly reply to, and drops a drafted reply into a dedicated Discord channel for a human to send. One profile per brand or client: subreddits, trigger keywords, an LLM prompt carrying voice and identity guardrails, and a webhook. The engine already exists at `scripts/reddit_monitor/`; this skill produces a profile that works and a schedule that keeps it working.

**Use it** when a founder wants inbound from subreddit conversations, the product has a technical wedge that makes honest replies useful, manual scanning has stopped scaling, and identity rules matter. **Do not use it** when target subs produce under ~5 posts/day total (the keyword filter starves), when the brand has no distinctive angle (generic replies get auto-removed), or when the ask is engagement metrics — this drafts replies, it does not track results.

## Done when

Work type `harness-change` — floor **E3/C3/O1** (`harness/eco-floors.yaml`). The deliverable is harness configuration plus a schedule, not a published post.

- **E3** — a named human approved the profile JSON, the prompt file, and the cron entry; `--dry-run` produced keyword matches and per-post pass/reject decisions from a real pull.
- **C3** — dry-run drafts read as something the brand would actually send, judged by someone other than the author: no fabricated experience, no generic cheerleading, correct sub-specific voice. The profile validates against the schema below.
- **O1** — the metric is declared before the cron goes live, with baseline, threshold, window, and owner: qualified drafts per week, or replies a human actually sent.

Posting any drafted reply to Reddit is separate work under `social-post` (E5/C2/O3), governed by `harness/references/reddit-organic-posting-rules.md` and `harness/references/social-automation-rules.md`. This skill never posts.

## Constraints

- **Read `MARKETING.md` from the project root first** for ICP, voice, pain points, and positioning — they drive every subreddit, keyword, and prompt choice. If absent, run `/kai-start` or get from the user: product, ICP, voice rules, and what they can and cannot honestly claim as expertise.
- **An existing profile gets a `--dry-run` before it gets an edit.** Do not change a working listener blind.
- **Identity guardrails are the point.** The prompt states what the brand *is*, what it is *not*, and what it has *learned* from building for clients as the bridge claim. Any post that would require fabricating experience is a REJECT, not a creative challenge.
- **Drafts only.** Nothing auto-posts to Reddit. A human reads and sends.
- **Vertical subs have stricter anti-promo rules** than category subs — identity and value rules in the prompt matter more there, and self-promotion norms per sub come from `harness/references/reddit-organic-posting-rules.md`.
- **Dedicated Discord channel with its own webhook** per profile. Do not reuse a shared webhook.
- **Do not ship until dry-run drafts would plausibly pass in the actual sub.** Iterate the prompt, re-run dry-run.
- **Supervise the first week.** Read every Discord alert; kill the cron and rewrite the prompt if drafts are off. Bad drafts never run unsupervised.

## Context

| Need | Load |
|---|---|
| Listener engine | `scripts/reddit_monitor/reddit_listener.py` |
| Cron wrapper (emits `ALERTS_JSON:`) | `scripts/reddit_monitor/run_listener.sh <profile>` |
| Profiles and the prompt starting point | `scripts/reddit_monitor/profiles/` — copy `example.prompt.md` |
| Engine docs | `scripts/reddit_monitor/README.md` |
| Per-profile seen-post state (gitignored) | `scripts/reddit_monitor/.seen/<name>.json` |
| Reddit self-promotion and automation norms | `harness/references/reddit-organic-posting-rules.md` + `harness/references/social-automation-rules.md` |
| Product, ICP, voice | `MARKETING.md` (project root) |
| Polishing a draft before a human sends it | `/kai-write`, `/kai-gate` |
| Finding subs and keywords you did not know about | `/kai-competitors` |
| Tightening voice rules when drafts read generic | `/kai-brand` |

**Required env:** `OPENAI_API_KEY` (LLM eval, read from repo-root `.env`, parent, or sibling) and the profile's `<discord_webhook_env>`.

**Goal shapes** — one profile serves one: honest technical value in builder subs (builder identity), pain-point posts in vertical subs (client-learning identity), or comparison and recommendation threads (share the stack).

**Subreddits — 15–30 total**, more than 30 and RSS pulls get slow. Use the exact sub name with no `r/` prefix, and open each one in a browser first; some are private or dead.

| Tier | Purpose | Examples |
|---|---|---|
| Primary | Direct category matches | r/AIReceptionists for voice AI; r/RemoteWork for remote tools |
| Adjacent | Where the ICP hangs out | r/SaaS, r/startups, r/gtmengineering |
| Vertical | Target customer verticals | r/LawFirm, r/HVAC, r/smallbusiness |

**Trigger keywords** are a cheap pre-filter on title and body before the LLM eval — cast wide, let the LLM reject the garbage. Four buckets: category terms ("voice ai", "ai receptionist"), competitor names ("vapi", "twilio", "retell"), technical jargon only buyers and builders use ("latency", "transcription", "vad"), and pain-point phrases ("missed calls", "after hours", "speed to lead"). Lowercase, multi-word preferred ("voice ai" beats "voice"), no single generic words ("marketing", "sales"), 20–40 total.

**The prompt file** uses Python `.format()` placeholders — `{subreddit}`, `{title}`, `{content}` — and must return JSON with `pass` (bool), `reason` (str), `angle` (str|null), `draft_response` (str|null). Keep the JSON example at the bottom `{{`/`}}`-escaped so `.format()` leaves it alone, under a literal `JSON only:` instruction. It contains: the identity section (ARE / are NOT / have LEARNED); reject and accept rules (reject anything needing fabricated experience, off-topic, job posts, career advice; accept where genuine technical value is addable); voice rules (tone, case, openers, forbidden words, one good-reply example and one bad-reply example); and an insight bank of 3–8 specific repeatable one-liners — latency numbers, percentages, architectural tips.

**Dry run** (no webhook env needed):

```bash
cd scripts/reddit_monitor
python reddit_listener.py --profile <name> --dry-run
```

Expect a keyword-match count, per-post pass/reject decisions, and drafts on stdout.

| Symptom | Cause |
|---|---|
| Everything rejects | Identity rules too strict, or keywords too narrow and pulling off-topic |
| Everything passes | Identity rules too loose — job posts and off-topic are not being rejected |
| Drafts read generic | Insight bank too thin, or voice rules too weak |
| Drafts fake experience | Identity section was not explicit enough |

**Going live.** Set the profile's Discord webhook env var (e.g. `REDDIT_MONITOR_DISCORD_WEBHOOK_KAICALLS`), then schedule via Windows Task Scheduler, launchd, or cron:

```bash
# daily at 12:00
0 12 * * * cd /path/to/scripts/reddit_monitor && python reddit_listener.py --profile <name> >> /var/log/reddit-<name>.log 2>&1
```

Hermes cron (the original KaiCalls setup at `/opt/cmo-analytics/reddit-monitor/`) relied on `OPENAI_API_KEY`, which is **not in hermes env today** — last-successful-run evidence is `seen_posts.json`, which stopped updating 2026-02-21. Fix by adding `OPENAI_API_KEY` to hermes env, or swap `OpenAI()` for OpenRouter: `OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])`.

**Profile schema:**

| Key | Required | Default | Purpose |
|---|---|---|---|
| `subreddits` | yes | — | list of sub names (without `r/`) |
| `trigger_keywords` | yes | — | case-insensitive substrings for pre-filter |
| `prompt_file` | yes | — | filename in `profiles/`; `.format()`'d with `{subreddit}`, `{title}`, `{content}` |
| `discord_webhook_env` | yes | — | env var name holding the Discord webhook URL |
| `name` | no | filename stem | state filename and logging |
| `alert_title` | no | `Reddit Opportunity` | Discord alert header |
| `model` | no | `gpt-4o-mini` | OpenAI model id |
| `seen_limit` | no | 2000 | ring-buffer size for seen post IDs |
| `posts_per_sub` | no | 25 | max posts pulled per sub per run |
| `content_max_chars` | no | 1200 | post body truncation before LLM |

## Escalate when

- The honest identity claim is thinner than the brand wants it to be — the fix is a business decision, not a prompt edit.
- Target subs ban vendor participation outright, or the account has no standing there.
- Dry-run drafts still fake experience after two prompt revisions.
- The user wants replies posted automatically without human review.
- `OPENAI_API_KEY` is unavailable in the target runtime and no OpenRouter key exists either.
- Post volume in the chosen subs is too low for the listener to earn its schedule.

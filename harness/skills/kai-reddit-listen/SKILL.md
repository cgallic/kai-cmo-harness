---
name: kai-reddit-listen
description: Monitor Reddit for conversation-fit opportunities — watches a list of subreddits, keyword-filters new posts, runs an LLM eval in your voice (with identity guardrails), and drops drafted replies into Discord. Use when "reddit monitor", "reddit listener", "reddit outreach", "watch subreddits", "find reddit opportunities", "listen on reddit", "community listening", or any request to automate finding posts you should reply to on Reddit.
---

Build and run a profile-driven Reddit listener. Engine lives at `scripts/reddit_monitor/`; each brand/client is a **profile** (subreddits + trigger keywords + LLM prompt + Discord webhook).

## When to use

- Founder/operator wants inbound leads from subreddit conversations
- Product has a specific technical wedge (useful insights → honest replies)
- You already tried manually scanning Reddit and it doesn't scale
- Brand voice + identity rules matter (don't fake experience you don't have)

## When NOT to use

- Post volume in target subs is low (<5/day total) — keyword filter will starve
- Brand has no distinctive angle — generic replies get auto-removed by Reddit
- You need engagement metrics (this only drafts replies, doesn't track results)

---

## Phase 0: Load Product Context

Check if `MARKETING.md` exists in the **project root**. If present, read it for ICP, voice, pain points, and product positioning — these drive subreddit/keyword/prompt choices. If absent, run `/kai-start` first or ask the user for: product, ICP, voice rules, what they can/can't honestly claim as expertise.

---

## Phase 1: Profile Discovery

A "profile" = one JSON config + one prompt file at `scripts/reddit_monitor/profiles/<name>.{json,prompt.md}`.

1. **Does a profile exist for this brand/client?**
   - List `scripts/reddit_monitor/profiles/*.json`
   - If yes → `--dry-run` it (Phase 5) before changing anything
   - If no → go to Phase 2

2. **What's the goal?**
   - (a) Find posts where we can honestly add technical value → builder identity
   - (b) Find pain-point posts in vertical subs → client-learning identity
   - (c) Find comparison/recommendation threads → share stack

---

## Phase 2: Configure Subreddits

Pick subs in three tiers. Aim for 15-30 total — more than 30 and RSS pulls get slow.

| Tier | Purpose | Examples |
|------|---------|----------|
| **Primary** | Direct category matches | r/AIReceptionists for voice AI; r/RemoteWork for remote tools |
| **Adjacent** | Where ICP hangs out | r/SaaS, r/startups, r/gtmengineering |
| **Vertical** | Target customer verticals | r/LawFirm, r/HVAC, r/smallbusiness |

Rules:
- Use exact sub name, no `r/` prefix
- Test each in a browser first — some subs are private or dead
- Vertical subs often have stricter anti-promo rules → identity guardrails in the prompt matter more here

---

## Phase 3: Configure Trigger Keywords

Keywords are the **pre-filter** before the LLM eval (cheap string match on title+body). Design them to cast a wide net; the LLM rejects the garbage.

Four buckets:

1. **Category terms** — exact product category ("voice ai", "ai receptionist")
2. **Competitor names** — ("vapi", "twilio", "retell")
3. **Technical jargon** — things only buyers/builders say ("latency", "transcription", "vad")
4. **Pain-point phrases** — how the problem is described ("missed calls", "after hours", "speed to lead")

Rules:
- Lowercase (match is case-insensitive)
- Multi-word phrases OK and preferred ("voice ai" > "voice")
- Avoid single generic words ("marketing", "sales") — too noisy
- 20-40 keywords is the sweet spot

---

## Phase 4: Write the LLM Prompt

This is where brand voice and identity guardrails live. The prompt file uses Python `.format()` placeholders — `{subreddit}`, `{title}`, `{content}` — and must instruct the model to return JSON with `pass` (bool), `reason` (str), `angle` (str|null), `draft_response` (str|null).

**Copy `profiles/example.prompt.md` as the starting point.** Then fill in:

### Identity section (critical)
- "You ARE X (honestly claim)"
- "You are NOT Y (don't fake)"
- "You have LEARNED Z from building for clients" (bridge claim)

### Reject/Accept rules
- REJECT triggers that would require fabricating experience
- REJECT off-topic, job posts, career advice
- ACCEPT posts where genuine technical value is addable

### Voice rules
- Tone (casual/formal), case (lowercase/sentence case), openers, forbidden words
- Example of good reply, example of bad reply (generic, cheerleader-y, faked experience)

### Insight bank
- 3-8 specific, repeatable insights the model can draw from
- One-liner per insight (latency numbers, % stats, architectural tips)

### Closing
- Literal `JSON only:` instruction with the 4-key schema

Keep the JSON example at the bottom `{{` `}}`-escaped so `.format()` doesn't try to substitute it.

---

## Phase 5: Test Dry-Run

Set the profile's webhook env var is not required in dry-run mode.

```bash
cd scripts/reddit_monitor
python reddit_listener.py --profile <name> --dry-run
```

Expect:
- "found N keyword matches" (N > 0 unless you just ran it — seen-posts dedup)
- Per-post pass/reject decisions
- Drafts printed to stdout for each pass

**Red flags:**
- Every post rejects → identity rules too strict, or keywords too narrow (pulling off-topic)
- Every post passes → identity rules too loose, not rejecting job posts/off-topic
- Drafts sound generic → insight bank too thin or voice rules too weak
- Drafts fake experience → identity section wasn't explicit enough

Iterate prompt → re-run dry-run. Don't ship until drafts would plausibly pass in the actual sub.

---

## Phase 6: Go Live + Automate

1. **Set the Discord webhook env var** named by the profile (e.g. `REDDIT_MONITOR_DISCORD_WEBHOOK_KAICALLS`). Create a dedicated channel with a channel-specific webhook — don't reuse a shared one.

2. **Local cron (Windows Task Scheduler / macOS launchd / Linux cron):**

   ```bash
   # daily at 12:00
   0 12 * * * cd /path/to/scripts/reddit_monitor && python reddit_listener.py --profile <name> >> /var/log/reddit-<name>.log 2>&1
   ```

3. **Hermes cron** (original KaiCalls setup): same pattern at `/opt/cmo-analytics/reddit-monitor/` — the original env relied on `OPENAI_API_KEY` which is **not in hermes env today** (last-successful-run evidence: `seen_posts.json` stopped updating 2026-02-21). Fix by adding `OPENAI_API_KEY` to hermes env, or swap `OpenAI()` → OpenRouter via `OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])`.

4. **First-week monitoring:** eyeball every Discord alert. Kill the cron and go back to Phase 4 if drafts are off. Don't let bad drafts run unsupervised.

---

## Profile Schema

| Key | Required | Default | Purpose |
|-----|----------|---------|---------|
| `subreddits` | yes | — | list of sub names (without `r/`) |
| `trigger_keywords` | yes | — | case-insensitive substrings for pre-filter |
| `prompt_file` | yes | — | filename in `profiles/`; `.format()`'d with `{subreddit}`, `{title}`, `{content}` |
| `discord_webhook_env` | yes | — | env var name holding the Discord webhook URL |
| `name` | no | filename stem | used for state filename and logging |
| `alert_title` | no | `Reddit Opportunity` | shown in Discord alert header |
| `model` | no | `gpt-4o-mini` | OpenAI model id |
| `seen_limit` | no | 2000 | ring-buffer size for seen post IDs |
| `posts_per_sub` | no | 25 | max posts pulled per sub per run |
| `content_max_chars` | no | 1200 | post body truncation before LLM |

---

## Engine Location

- Script: `scripts/reddit_monitor/reddit_listener.py`
- Runner (cron wrapper, emits `ALERTS_JSON:` line): `scripts/reddit_monitor/run_listener.sh <profile>`
- Profiles: `scripts/reddit_monitor/profiles/`
- State (per-profile, gitignored): `scripts/reddit_monitor/.seen/<name>.json`
- Docs: `scripts/reddit_monitor/README.md`

## Required env

- `OPENAI_API_KEY` — LLM eval (reads from repo-root `.env`, parent, or sibling)
- `<discord_webhook_env>` — per profile

## When to compose with other skills

- After drafts arrive in Discord and you want to polish before posting → `/kai-write` or `/kai-gate` (check against banned words, Four U's)
- To identify subs + keywords you didn't know about → `/kai-competitors` (reverse-engineer where competitors are active)
- If drafts are generic → `/kai-brand` to tighten voice rules before rewriting the prompt

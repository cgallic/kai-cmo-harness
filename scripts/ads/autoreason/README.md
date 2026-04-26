# AutoReason — Ad copy iteration loop

Implementation of [_Autoreason: Self-Refinement That Knows When to Stop_](https://github.com/NousResearch/autoreason/blob/main/paper/autoreason.pdf) (SHL0MS & NousResearch, 2026), scoped to KaiCalls Meta ads.

Concept page: `/home/connor/brain/wiki/concepts/autoreason.md`.

## What it does

Per pass, runs a 5-role tournament between the incumbent ad (A), an adversarial revision (B), and a synthesis (AB). Three blind judges Borda-vote (3/2/1). Conservative tiebreak: incumbent wins ties. Loop terminates when the incumbent wins **k=2 consecutive passes** (paper-validated).

| Role | Sees | Produces |
|------|------|----------|
| Incumbent (A) | n/a — IS the input | Current ad |
| Critic | A + perf + top/bottom comps | Critique only |
| Author B | A + critique | Adversarial revision |
| Synthesizer | A + B with randomized labels | Merged version (AB) |
| Judge × 3 | A, AB, B with randomized labels | Borda vote |

- Author/synthesizer temperature: **0.8**
- Judge temperature: **0.3**
- Model: `claude-3-5-haiku-20241022` (paper's sweet spot, ~10× cheaper than Sonnet)

## Pre-judge filter

Brand-lock + Tier-1 banned-phrase validators run on B and AB before judging. Violations trigger up to 2 re-author attempts. If the model can't produce a clean draft, the trace records the failure and the judge prompt instructs the panel to last-place any candidate that drifts off positioning.

KaiCalls positioning lock (per `memory/kaicalls_positioning.md`): "the new business phone number with AI built in" — NOT receptionist, NOT answering service, NOT bolt-on app.

## Pilot scope

Single underperforming KaiCalls ad set. Trace posts to a Discord channel set via `$AUTOREASON_DISCORD_CHANNEL` (or `--discord-channel <id>`) for human approval. **No Meta uploads from this module.** When approved, the wire-in to `scripts/ads/ad_loop.py:step_generate_variants` is a separate change.

## Usage

```bash
# from kai-cmo-harness/ root, with .venv activated
python -m scripts.ads.autoreason.run --use-fixture --dry-run

# live (auto-picks lowest-CTR KaiCalls ad set, posts to Discord)
python -m scripts.ads.autoreason.run

# specific ad set, write full trace JSON
python -m scripts.ads.autoreason.run --ad-set-id 120211234567890 --json-out /tmp/trace.json
```

## Required env

Reads from `kai-cmo-harness/.env` (gitignored — never commit):

- `OPENROUTER_API_KEY` — Haiku 3.5 routes via `anthropic/claude-3.5-haiku`
- `META_ACCESS_TOKEN` — must have `ads_read`
- `META_AD_ACCOUNT_ID`
- `DISCORD_BOT_TOKEN` — for the trace post
- `AUTOREASON_DISCORD_CHANNEL` — destination channel id (or pass `--discord-channel`)

## Files

```
autoreason/
├── loop.py           # The 5-role tournament orchestrator
├── roles.py          # Anthropic SDK calls per role
├── knowledge.py      # Brand lock, banned phrases, Meta loaders, fixture
├── trace.py          # Pass dataclass + Discord formatter
├── run.py            # CLI entry
├── prompts/
│   ├── critic.md
│   ├── author.md
│   ├── synthesizer.md
│   └── judge.md
└── README.md         # this file
```

## Hard rules baked in

- **Never auto-uploads to Meta** — only posts to Discord; human approves first.
- **Never emails clients** — only Connor emails KaiCalls customers (per `memory/feedback_no_customer_outreach.md`).
- **Brand lock auto-rejects** "AI receptionist", "answering service", and similar drift phrases.

# Current models and outcome learning

This change modernizes the Python agent router and adds an opt-in outcome
policy to goal decomposition. The installed skills still use their host model.
No foundation-model training job runs, no live deployment changes, and no
publishing or spend approval is granted by a learning decision.

## Models

Defaults checked against provider documentation on 2026-09-08:

| Provider | Routine | Strategy |
| --- | --- | --- |
| OpenAI | gpt-5.6-luna | gpt-5.6-terra |
| Anthropic | claude-haiku-4-5-20251001 | claude-sonnet-5 |
| Gemini | gemini-3.5-flash-lite | gemini-3.8-flash |
| OpenRouter | google/gemini-3.5-flash-lite | anthropic/claude-sonnet-5 |

Both OpenRouter IDs were present in its public /api/v1/models catalog on
2026-09-08. Account-level access still requires credentials. Set explicit IDs
if your account exposes a different catalog. Existing environment overrides win.
Use AGENT_SMART_MODEL=gpt-6-astra with AGENT_LLM_PROVIDER=openai for harder
strategy work. The default balances cost; it does not always select the largest
model.

Direct OpenAI reasoning models use Responses with max_output_tokens and
AGENT_REASONING_EFFORT (default low). Unsupported sampling parameters are
omitted. Incomplete/empty Responses results fail instead of becoming finished
drafts. Older OpenAI models and OpenRouter retain chat transport. Claude 5
requests omit temperature. Gemini receives its actual output budget, system
instruction and conversation roles.

Cost estimates use exact known model rates; unknown models return null,
including Gemini until its prices are configured in the code. Null must never
be interpreted as a free request. Estimates omit cache discounts and provider
surcharges. No account-level availability or paid inference was tested here.

Provider references:
- [OpenAI model catalog](https://developers.openai.com/api/docs/models)
- [OpenAI migration parameters](https://developers.openai.com/api/docs/guides/latest-model)
- [Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview)
- [Claude Haiku 4.5](https://platform.claude.com/docs/en/models/haiku-4-5/overview)
- [Gemini catalog](https://ai.google.dev/gemini-api/docs/models)

## What RL means here

A contextual bandit changes which marketing action gets proposed based on
observed rewards. Context is isolated by brand, KPI, direction, reward scale,
measurement window and cost budget. This is action-policy learning, not PPO,
GRPO, model-weight fine-tuning, or proof that marketing caused the outcome.

The old reward averages remain available for backward compatibility. They
lack the experiment contract needed for this policy and are not silently
imported into it.

The lifecycle is:

1. Declare candidate actions, baseline and its source, metric direction,
   normalization scale, measurement window, optional cost budget, and actor.
2. Persist the selected action, every candidate's probability, policy version
   and reward contract before executing anything.
3. Execute the selected action through existing approval and task machinery.
4. A trusted collector/operator verifies the effect and submits the matured
   measurement, source reference, execution time and verifier identity.
5. Update that context's action-selection distribution and retain the record
   for replay/export.

Under-observed candidates are explored uniformly until each has min_samples
(default 3) settled observations. Afterwards epsilon-greedy selection reserves
epsilon (default 0.1) for exploration and favors the best observed mean.
This is not a statistical significance threshold.

Reward is clipped signed KPI improvement divided by the predeclared scale,
then reduced by actual cost / cost_budget when a budget was declared, with a
floor of -1. Rewards lie in [-1, 1]. Cost without a declared budget is rejected.
A cost budget normalizes the reward; existing spend controls enforce spending.
Use conversion or contribution metrics when those are the business objective.
A draft score is a craft gate, not a business reward.

Pending decisions remain reward=null. Repeated identical feedback is a no-op;
conflicting feedback is rejected. NaN, future measurements, premature windows,
wrong executed actions and producer-as-verifier are rejected. SQLite transactions
serialize feedback, preserving one settlement per decision.

## Use from a goal

Set KAI_RL_DB to the persistent SQLite file, then add rl_experiment to the goal's
metadata. The brand, KPI and direction come from the goal. Example structure
(values are illustrative, not real results):

```json
{
  "rl_experiment": {
    "actions": ["content_pipeline", "seo_optimization"],
    "baseline": 10,
    "baseline_at": "2026-09-01T00:00:00Z",
    "evidence_ref": "collector:baseline-record-id",
    "scale": 10,
    "actor": "marketing-operator",
    "window_days": 30,
    "epsilon": 0.1,
    "min_samples": 3,
    "cost_budget": 100
  }
}
```

The planner receives the selected experiment and attaches rl_decision_id to
one matching task node. Omitting the selected action raises an error.
A failed plan leaves a pending decision, not a negative reward.

## Collector and replay interface

```bash
python -m kai.analytics.rl --db data/outcome-policy.sqlite choose --input experiment.json
python -m kai.analytics.rl --db data/outcome-policy.sqlite observe --input observation.json
python -m kai.analytics.rl --db data/outcome-policy.sqlite export
```

Standalone choose inputs use the fields above plus brand_id, metric and
direction. observe requires decision_id, value, executed_at, observed_at,
verifier, evidence_ref, executed_action, and optional cost (default 0).
export writes JSONL to stdout, including pending decisions and propensities.

## Boundaries

The collector must authenticate the verifier and check referenced evidence
upstream. This local library cannot prove independence from a different name,
fetch a referenced receipt, or establish causality. It does not issue ECO
verdicts. Current scheduled collectors do not auto-submit these observations;
use the explicit collector interface after verification.

The policy does not automatically reroute models, rewrite prompts, promote
skills, or launch training jobs. Its records are generic policy trajectories,
not a provider-ready RFT dataset. Any offline policy comparison must account
for logged propensities, overlap, delayed outcomes and selection bias.

To disable selection, unset KAI_RL_DB or omit rl_experiment. Existing goals
continue using the previous planner. Preserve the database for audit/replay.

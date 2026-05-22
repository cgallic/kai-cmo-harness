# Kai Evaluation Spine

This directory contains the first-class evaluation spine for Kai workflows. It is intentionally YAML-and-docs only for Wave 1: no Python harness, no runner, and no changes outside `evals/`.

The goal is to make future prompt, skill-contract, and doctrine changes testable. Each situation captures the user request, trusted and untrusted context, required tool behavior, expected artifacts, deterministic hard checks, LLM judge criteria, provenance expectations, and human calibration notes.

## Directory Layout

```text
evals/
  README.md
  rubrics/
    evidence-ladder.yaml
    llm-judge-calibration.yaml
    compliance-hard-fails.yaml
  situations/
    missing-data/
    stale-policy/
    prompt-injection/
    unsupported-ai-search-claim/
    manipulative-community-tactic/
    ad-claim-risk/
    paid-media-attribution-confusion/
    ai-search-measurement-volatility/
    llms-txt-misconception/
    pmax-account-state-decision/
    creator-rights-disclosure-failure/
    cold-outreach-relevance-failure/
    cro-unsupported-benchmark/
    brand-positioning-without-research/
    persona-invented-from-vibes/
    attribution-overclaim/
    pr-quote-newsworthiness-failure/
```

Planned but not created in this wave:

```text
evals/
  fixtures/
    source-backed/
    missing-data/
    adversarial/
    stale-policy/
    bad-perfect/
```

## Situation Schema

Every situation YAML should use these top-level fields:

- `id`: stable identifier for regression tracking.
- `version`: situation contract version.
- `category`: one of the named situation categories.
- `workflow`: production workflow or skill under test.
- `risk_tier`: `low`, `medium`, `high`, or `critical`.
- `user_request`: the exact request under evaluation.
- `workspace_state`: relevant trusted repo state, files, or absence of files.
- `available_sources`: trusted, untrusted, missing, and stale source context.
- `required_tool_choices`: tools or actions the agent should choose, avoid, or defer.
- `expected_artifacts`: files, report sections, copy, or refusal/advisory outputs expected.
- `hard_fail_conditions`: deterministic failures that should block the run.
- `deterministic_checks`: future runner checks for schema, citations, policy, and trace behavior.
- `llm_judge_rubric`: qualitative criteria with pass thresholds.
- `human_calibration_notes`: what a human reviewer should look for.
- `trace_assertions`: required trace events, decisions, and evidence labels.
- `expected_source_provenance_behavior`: citation, missing-data, and evidence-tier behavior.

## Evaluation Doctrine

Deterministic gates own hard policy, schema, citation presence, and source/provenance failures.

LLM judges own comparative quality, usefulness, fit, evidence interpretation, and judgment calls that require domain context.

Human calibration owns final rubric interpretation, new edge cases, and disputes where a model judge could reward confident but unsafe work.

## Evidence Policy

Use `rubrics/evidence-ladder.yaml` for claim grading. Client-facing quantitative claims require source metadata and tiers `official_requirement`, `official_best_practice`, `law_regulation_court_status`, `academic_study`, `vendor_platform_study`, `practitioner_benchmark`, or `internal_measurement`.

Use `inference_hypothesis` for experiments only. Use `missing_data` when the source is absent. Never replace missing data with invented rankings, traffic, backlinks, Core Web Vitals, conversion rates, call volume, ad metrics, or AI visibility.

## Prompt And Contract Versioning

Future runnable evals should record:

- prompt or skill contract path
- prompt or skill contract version
- model name and settings
- tool choices and arguments
- source list with retrieval dates
- deterministic gate results
- LLM judge result with confidence
- human calibration result, if required

## Regression Thresholds

Contract and prompt changes should not ship when a golden situation regresses on
any listed hard-fail condition. Deterministic checks are expected to pass at
100% for hard policy, schema, trace, and provenance fields. LLM judges may vary,
but every situation must meet its own `pass_threshold` and record confidence for
human calibration.

# Eval Harness Research Seed - 2026-05-17

This is prework for the scheduled eval-harness agent. It is not the final research note and not the build plan. Use it to shorten Phase 1, then still perform the required research -> plan -> build sequence.

Retrieval date for web sources: 2026-05-17.

## Bottom Line

Build Kai's harness as a small deterministic runner, not a framework.

The strongest common pattern across real eval and runtime systems is:

1. Keep the dataset/situation files simple and inspectable.
2. Run deterministic checks first.
3. Treat LLM judges as optional scorers, not the source of truth.
4. Write run artifacts with enough metadata to compare runs.
5. Make failures resumable/debuggable with stable IDs and plain files.
6. Add human calibration where judgment matters.

For Kai, that means a Python CLI that reads `evals/` and `harness/skill-contracts/`, validates YAML and required fields, resolves hard-fail IDs, writes `results.json` plus `summary.md`, and exits nonzero on deterministic failures.

## Comparable Eval Harnesses

### OpenAI Evals / Graders

Sources:
- OpenAI evaluation best practices: https://platform.openai.com/docs/guides/evaluation-best-practices
- OpenAI graders: https://platform.openai.com/docs/guides/graders
- OpenAI BrowseComp: https://openai.com/index/browsecomp/
- OpenAI GDPval: https://openai.com/index/gdpval/

What to copy:
- Separate human evals, deterministic/code checks, and model graders.
- Prefer pass/fail or pairwise checks when reliability matters.
- Use graders for bounded scores, but keep deterministic gates for hard requirements.
- Keep benchmark tasks verifiable. BrowseComp's key lesson is short, checkable answers; GDPval's key lesson is expert review for real work artifacts.
- Include metadata for model/prompt/tool versions, even if Kai's first runner does not execute models.

What to avoid:
- Do not require OpenAI Evals API or dashboard for the first Kai runner.
- Do not make LLM-as-judge mandatory.
- Do not create an over-general grader DSL before Kai has enough real failures.

Kai adaptation:
- `hard_fail_conditions` map to deterministic graders.
- `llm_judge_rubric` is loaded and recorded as `skipped` unless explicitly enabled.
- Use `pass_threshold` and `regression_thresholds` from YAML as metadata first, then enforce only the deterministic subset.

### Anthropic Eval Guidance

Sources:
- Anthropic building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Anthropic define success and build evaluations: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests

What to copy:
- Define task-specific success criteria before implementation.
- Automate where possible with exact match, string checks, code grading, or LLM grading.
- Prefer the fastest reliable grader: code first, human for calibration, LLM for nuanced review after testing.
- Keep agent systems simple; add autonomy only when simpler workflows fail.

What to avoid:
- Do not start with multi-agent execution inside the eval runner.
- Do not hide prompts, tool calls, and intermediate state behind abstractions.

Kai adaptation:
- The runner should be a workflow, not an agent.
- It should expose every deterministic check in the result artifact.

### Inspect AI

Source:
- Inspect docs: https://inspect.aisi.org.uk/

What to copy:
- Core objects: dataset samples, solver/executor, scorer, logs.
- Evaluation logs as first-class artifacts.
- Runtime overrides through CLI flags.
- Human baselining and log inspection as future extensions.

What to avoid:
- Do not import Inspect as a dependency for this first pass.
- Do not replicate its full task/solver/scorer plugin system.

Kai adaptation:
- Treat each situation YAML as a dataset sample.
- Treat deterministic validation functions as scorers.
- Write logs/artifacts even when no model is run.

### promptfoo

Source:
- Assertions and metrics docs: https://www.promptfoo.dev/docs/configuration/expected-outputs/

What to copy:
- Assertions as named checks with pass/fail output.
- Assertion groups and thresholds.
- Deterministic metrics first, model-graded metrics optional.
- Ability to run checks directly on pre-existing outputs/artifacts.

What to avoid:
- Do not make Kai write promptfoo YAML or depend on Node.
- Do not add every promptfoo assertion type.

Kai adaptation:
- Implement a tiny assertion vocabulary around current YAML:
  - required field exists
  - field type is list/map/string
  - hard-fail ID exists
  - contract has required source/provenance/trace fields
  - situation has expected source behavior

### DeepEval, Ragas, LangSmith, EleutherAI lm-evaluation-harness

Sources:
- DeepEval docs: https://deepeval.com/docs/introduction
- Ragas docs: https://docs.ragas.io/
- LangSmith evaluation concepts: https://docs.langchain.com/langsmith/evaluation-concepts
- LangSmith experiment analysis: https://docs.langchain.com/langsmith/analyze-an-experiment
- EleutherAI lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness

What to copy:
- Pytest-like local tests from DeepEval.
- Named metrics and result tables from Ragas/LangSmith.
- Dataset/experiment separation from LangSmith.
- CLI-driven reproducible runs from EleutherAI's harness.
- Optional cache/output paths and integrity checks.

What to avoid:
- Do not build RAG metrics now; Kai's current eval spine is policy/schema/provenance oriented.
- Do not add a hosted trace service.
- Do not evaluate base model performance; Kai is evaluating workflows/contracts.

Kai adaptation:
- Use pytest for harness unit tests.
- Use a CLI with explicit `--situations`, `--contracts`, and `--out`.
- Add an integrity-check mode by default.

## Runtime And Agent Systems

### OpenClaw

Sources:
- OpenClaw GitHub: https://github.com/openclaw/openclaw
- Local Kai docs referencing OpenClaw: `docs/QUICK_START.md`, `docs/CONFIGURATION.md`, `docs/ADDING_PRODUCTS.md`

What to copy:
- Run/workspace orientation: OpenClaw is organized around a local gateway, workspace, channels, tools, sessions, skills, and scheduled tasks.
- Security defaults: inbound messages are untrusted; pairing/allowlists and doctor checks are useful patterns.
- CLI health checks: `doctor`-style validation maps well to Kai eval integrity checks.
- Skills and context files are inspectable artifacts.

What to avoid:
- Do not run the eval harness as a persistent autonomous agent.
- Do not add channel or gateway concepts to the first runner.
- Do not let untrusted eval text mutate config or execute tools.

Kai adaptation:
- Add `run_id`, `started_at`, `cwd`, `git_branch`, and artifact paths to results.
- Add a future `doctor` command alias only if the first CLI proves useful.

### Hermes / Nous Research / Nous Hermes

Sources:
- Hermes Agent GitHub: https://github.com/NousResearch/hermes-agent
- Hermes Agent docs index linked from GitHub: https://hermes-agent.nousresearch.com/docs
- Hermes 4 model card: https://huggingface.co/NousResearch/Hermes-4-14B
- Hermes 4 technical report: https://nousresearch.com/wp-content/uploads/2025/08/Hermes_4_Technical_Report.pdf

Name resolution:
- User's `nouse reasrch` and `nowser` mean Nous Research.
- Hermes can mean the Nous Hermes model family or Hermes Agent. For this task, research both, but copy runtime patterns mostly from Hermes Agent.

What to copy:
- Agent runtime concepts: sessions, tools/toolsets, skills/procedural memory, persistent memory, messaging gateway, cron scheduling, context files.
- Explicit docs sections for security, command approval, container isolation, memory, tools, and architecture.
- Subagent/parallel work as an orchestration pattern, not as the eval runner itself.
- Hermes 4 model docs emphasize prompt format, tool use, and structured outputs; useful when optional LLM judging arrives later.

What to avoid:
- Do not import Hermes Agent or adopt its runtime.
- Do not use self-assessment as a hard gate.
- Do not add persistent memory to eval runner v1.

Kai adaptation:
- Keep context files and eval YAML as the source of truth.
- Optional LLM judge should record prompt format and model/provider only when enabled.

### arXiv / "arvix"

Name resolution:
- User's `arvix` means the arXiv website/source corpus.

Useful arXiv/source targets:
- tau-bench: https://arxiv.org/abs/2406.12045
- BrowseComp paper: https://arxiv.org/abs/2504.12516
- DSPy Assertions: https://arxiv.org/abs/2312.13382
- RAGAS paper: https://arxiv.org/abs/2309.15217
- METR long task paper via blog/source: https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/

What to copy:
- tau-bench's idea of domain policy plus tool interaction as part of the task state.
- BrowseComp's insistence on verifiable answers.
- DSPy Assertions' principle that constraints should catch failures before they become downstream behavior.
- METR's lesson that long-horizon reliability needs repeated, traceable runs, not just single success demos.

What to avoid:
- Do not copy academic metric complexity into v1.
- Do not build simulated users or interactive environments yet.

Kai adaptation:
- Situation YAML already has policy, required tool behavior, expected artifacts, hard fails, trace assertions, and provenance behavior. Validate those fields first.

### SWE-bench, METR, tau-bench, LangGraph, Temporal, HumanLayer

Sources:
- SWE-bench GitHub: https://github.com/SWE-bench/SWE-bench
- METR long tasks: https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/
- tau-bench: https://arxiv.org/abs/2406.12045
- LangGraph persistence/checkpoints: https://reference.langchain.com/python/langgraph/checkpoints
- Temporal docs: https://docs.temporal.io/
- Temporal durable execution overview: https://temporal.io/
- HumanLayer 12-factor agents: https://www.humanlayer.dev/blog/12-factor-agents
- HumanLayer 12-factor agents GitHub: https://github.com/humanlayer/12-factor-agents

What to copy:
- SWE-bench: containerization/reproducibility is the north star, but Kai v1 can settle for deterministic local file checks.
- METR: record task/run metadata and distinguish pass rate from single-run anecdotes.
- tau-bench: model policy and tools as explicit task constraints.
- LangGraph: checkpoint/resume is valuable later; v1 can mimic it with a `run_id` and artifact directory.
- Temporal: durable execution means persisted state and replay compatibility; v1 can borrow artifact/replay discipline without adding Temporal.
- HumanLayer: use structured tool/action payloads and deterministic code after the model proposes intent.

What to avoid:
- Do not add Docker, Temporal, LangGraph, or a database unless a concrete Kai requirement forces it.
- Do not add autonomous repair loops in v1.
- Do not evaluate hidden chain-of-thought; evaluate artifacts and traces.

Kai adaptation:
- Store run metadata, check results, and summary in `workspace/eval-runs/<run_id>/`.
- Keep output portable JSON/Markdown.
- Add `--fail-fast` and `--continue-on-error` only if easy; default should collect all deterministic failures and exit nonzero.

## Long-Horizon Agent Goals And Evals

The scheduled agent should research long-horizon agent goal systems explicitly. Kai's eval harness v1 is deterministic, but Kai's product direction includes scheduled/background work, subagents, approvals, memory, and multi-step marketing workflows. The harness should leave room for that without building an autonomous runtime now.

Marketing also has a second kind of long horizon: outcomes emerge over weeks and months. A campaign, lifecycle program, SEO plan, content cluster, or creator-commerce loop cannot be judged by one artifact at one timestamp. The harness should support this future without overbuilding v1.

Seed sources:
- METR long-horizon task measurement: https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/
- METR task suites and methodology: https://metr.org/
- SWE-bench: https://github.com/SWE-bench/SWE-bench
- SWE-bench Verified / OpenAI SWE-bench notes: https://openai.com/index/introducing-swe-bench-verified/
- tau-bench: https://arxiv.org/abs/2406.12045
- OSWorld: https://os-world.github.io/
- WebArena: https://webarena.dev/
- WorkArena: https://arxiv.org/abs/2403.07718
- GAIA benchmark: https://arxiv.org/abs/2311.12983
- AgentBench: https://arxiv.org/abs/2308.03688
- AgentDojo prompt-injection/tool-use benchmark: https://arxiv.org/abs/2406.13352
- τ2-bench / terminal or tool-use benchmark variants if current sources show they are mature enough.

Questions to answer during research:
- How do serious benchmarks define a "task" when success requires many steps?
- Which signals are deterministic and which require human/LLM review?
- How do they store traces, tool calls, intermediate artifacts, retries, and final answers?
- How do they avoid rewarding brittle one-shot success?
- How do they detect partial progress vs complete success?
- How do they model unsafe tool use, prompt injection, stale state, and missing data?
- How do they handle timeouts, resumability, and flaky environments?
- What is the smallest useful version Kai can copy now?
- How do long-running systems evaluate delayed outcomes without pretending early proxy metrics are final truth?
- How should a marketing workflow record baseline, intervention, cadence, guardrails, holdouts, and follow-up dates?
- How should Kai separate artifact quality gates from longitudinal performance gates?

Patterns to copy later:
- Stable task IDs and versioned task definitions.
- Run manifests with start/end time, workspace state, git info, model/runtime config, and tool permissions.
- Step traces with observable actions, artifact paths, and decisions.
- Partial-credit or progress fields for long workflows, even when v1 only reports pass/fail.
- Separate final artifact grading from process/trace grading.
- Timeout and interruption statuses distinct from failures.
- Human-review checkpoints for irreversible or client-facing actions.
- Replayable/resumable artifact directories.
- Longitudinal run records: baseline snapshot, intervention artifact, measurement window, follow-up checkpoints, and final readout.
- Guardrail metrics that prevent optimizing one metric while damaging trust, compliance, deliverability, margin, or lead quality.
- Decision logs that record why a campaign was continued, paused, expanded, or revised.
- Cohort/holdout fields when causal measurement is possible; confidence caveats when it is not.

Patterns to avoid now:
- Browser/desktop automation in the eval harness v1.
- Simulated customers or tool environments before Kai has deterministic YAML checks working.
- Hidden scoring where only the final answer matters.
- Benchmark-specific containers or services unless a future task needs them.

Kai adaptation:
- Add fields to the result artifact that are useful for long-horizon work even if empty in v1: `run_id`, `parent_run_id`, `status`, `started_at`, `ended_at`, `duration_ms`, `interrupted`, `resumable`, `artifact_paths`, and `trace_assertions_checked`.
- Preserve situation YAML fields like `required_tool_choices`, `trace_assertions`, and `expected_artifacts`; do not flatten them away.
- Keep the runner deterministic, but design results so future agent runs can attach step traces.
- Add future-compatible marketing fields to the result artifact or summary metadata when available: `campaign_id`, `baseline_artifact`, `measurement_window`, `checkpoint_dates`, `primary_metric`, `guardrail_metrics`, `holdout_or_control`, `confidence_label`, and `next_decision_date`.
- In v1, these can be optional metadata fields. Do not force every single-turn eval situation to invent campaign data.

## Marketing Improvement Loops Over Weeks And Months

Kai's eval harness should eventually test whether a workflow improves marketing decisions over time, not just whether it produced a polished artifact. The scheduled agent should research this as part of the long-horizon lane.

Seed sources:
- IAB incremental measurement guidance: https://www.iab.com/guidelines/guidelines-for-incremental-measurement-in-commerce-media/
- Google Meridian MMM: https://developers.google.com/meridian
- Google Meridian overview: https://blog.google/products/ads-commerce/meridian-marketing-mix-model-open-to-everyone/
- Meta Conversion Lift docs: https://www.facebook.com/business/help/429994630426767
- Google Ads experiments docs: https://support.google.com/google-ads/answer/6261395
- LinkedIn B2B Institute 95-5 rule: https://business.linkedin.com/advertise/resources/b2b-institute/b2b-research/trends/95-5-rule
- Ehrenberg-Bass / category entry points and mental availability research, using primary or official institute pages where possible.
- Customer.io/Braze/Klaviyo lifecycle benchmark docs only for structure; avoid importing benchmark numbers without source metadata.
- Baymard/CXL/Wynter/Maze/User Interviews for CRO and research loops.

Questions to answer:
- What should a marketing eval treat as the unit of work: artifact, campaign, experiment, cohort, funnel stage, or program?
- What evidence is available immediately, after 7 days, after 30 days, after 90 days?
- Which metrics are leading indicators and which are outcome metrics?
- What should be considered a pass when the right decision is "do not scale yet"?
- How should Kai score learning quality when revenue outcomes are delayed or underpowered?
- How should the harness prevent overfitting to platform-reported ROAS, open rates, CTR, or single-session conversion?

Patterns to copy:
- Baseline -> intervention -> checkpoint -> decision -> follow-up.
- Measurement ladder: deterministic artifact checks, instrumentation checks, early proxy readout, causal test when possible, long-window business readout.
- Evidence labels for each metric: observed, attributed, incremental, modeled, directional, missing.
- Guardrail metrics per workflow:
  - Email: complaint rate, unsubscribe rate, bounce rate, deliverability status, revenue/activation by cohort.
  - Paid media: margin-adjusted CAC, new-customer share, holdout/lift, creative fatigue, refund/lead quality.
  - SEO/AEO: indexed pages, qualified clicks, assisted conversions, cited/mentioned observations with sampling caveats.
  - CRO: conversion, revenue per visitor, lead quality, support burden, trust/compliance defects.
  - Brand/demand gen: category entry point coverage, recall/proxy survey, direct/search demand, sales-cycle quality.
- Decision labels: continue, stop, revise, expand, hold for more data, escalate to human.

Kai v1 adaptation:
- Do not build longitudinal scheduling yet.
- Add result artifact fields that do not hurt single-run evals but can support future marketing program evals:
  - `program_id`
  - `cycle_id`
  - `baseline_sources`
  - `measurement_window`
  - `checkpoint_dates`
  - `decision_label`
  - `metric_evidence_tiers`
  - `guardrail_metrics`
  - `data_gaps`
- Add docs stating that v1 validates readiness for longitudinal evals; future work will run scheduled follow-up checks.

## Proposed Boring Shape For Kai

The scheduled agent should still write its own build plan, but this is the recommended shape:

```text
scripts/
  evals/
    __init__.py
    run.py          # CLI
    loader.py       # YAML discovery/loading
    schema.py       # required field/type checks
    checks.py       # deterministic checks
    results.py      # JSON/Markdown artifact writing
    llm_judge.py    # disabled-by-default stub
tests/
  test_eval_harness.py
```

CLI:

```powershell
python -m scripts.evals.run --situations evals/situations --contracts harness/skill-contracts --out workspace/eval-runs/smoke
```

Default behavior:
- Load all YAML.
- Validate required top-level fields.
- Validate all `hard_fail_conditions` IDs exist in `evals/rubrics/compliance-hard-fails.yaml`.
- Validate all contracts contain required eval-ready fields.
- Validate source/provenance/trace fields are present.
- Mark LLM judge as `skipped` unless both a flag and env var are present.
- Write `results.json` and `summary.md`.
- Exit 0 only when deterministic checks pass.

Suggested result shape:

```json
{
  "run_id": "20260517T034000Z",
  "started_at": "2026-05-17T03:40:00Z",
  "cwd": "E:/Dev2/kai-cmo-harness-work",
  "git": {"branch": "...", "commit": "...", "dirty": true},
  "inputs": {
    "situations": "evals/situations",
    "contracts": "harness/skill-contracts"
  },
  "llm_judge": {"enabled": false, "status": "skipped"},
  "checks": [
    {
      "id": "situation.required_fields",
      "target": "evals/situations/...yaml",
      "status": "pass",
      "errors": []
    }
  ],
  "summary": {
    "status": "pass",
    "passed": 100,
    "failed": 0,
    "warnings": 0
  }
}
```

## Tests To Build First

Use pytest and temp directories. Minimum tests:

- Parses all current `evals/**/*.yaml` and `harness/skill-contracts/*.yaml`.
- Fails on missing required situation field.
- Fails on missing required contract field.
- Fails on unknown hard-fail ID.
- Writes `results.json` and `summary.md`.
- Records LLM judge as skipped by default.
- Returns nonzero from CLI on deterministic failure.
- Returns zero on the current repo inputs.

## Patterns To Avoid

- No hosted service dependency.
- No mandatory API key.
- No agent loop in the eval runner.
- No dynamic subagent execution in the runner.
- No synthetic benchmark claims.
- No broad schema rewrite of current YAML.
- No complex plugin framework.
- No hidden mutation of eval files during runs.

## Extra Source Leads For The Scheduled Agent

Use these if time allows:

- OpenAI Model Spec: https://model-spec.openai.com/2025-02-12.html
- OpenAI prompt injection guidance: https://openai.com/safety/prompt-injections/
- UK AISI Inspect eval logs docs: https://inspect.aisi.org.uk/
- LangSmith `evaluate()` reference: https://reference.langchain.com/python/langsmith/client/Client/evaluate
- LangGraph persistence docs: https://reference.langchain.com/python/langgraph/checkpoints
- DSPy docs/repo: https://github.com/stanfordnlp/dspy
- AutoGen: https://github.com/microsoft/autogen
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- CrewAI: https://github.com/crewAIInc/crewAI

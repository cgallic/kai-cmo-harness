---
title: "ECO: Execution, Craft, Outcome — The Completion Standard"
type: doctrine
created: 2026-07-27
updated: 2026-07-28
status: canonical
owner: Connor Gallic
supersedes: "Any use of `done` as a completion verdict"
scope: "All work performed by Company Autopilot, the CMO loop, fleet agents, Kai skills, and human operators"
---

# ECO: Execution, Craft, Outcome — The Completion Standard

> **Produced is not finished. Finished is what remains after Execution, Craft, and Outcome have each cleared a declared bar held by someone other than the actor.**

Machine-readable floors: `harness/eco-floors.yaml` · Marketing application: `harness/references/eco-marketing-floors.md` · Verifier: `python -m scripts.quality_gates.eco_gate`

## The standard in one minute

Every work item is judged on three independent axes:

| Axis | Question | Typical clock |
|---|---|---|
| **E — Execution** | Did the intended effect happen in the real world? | Minutes |
| **C — Craft** | Does the work meet the professional standard of its field? | Hours |
| **O — Outcome** | Did the result it was intended to cause actually occur? | Days or weeks |

The word **done** is retired. It collapsed three different claims into one word and allowed an actor to substitute "I produced something" for "the work succeeded."

There are two recognized completion verdicts:

- **SHIPPED:** the declared Execution and Craft floors have been met.
- **CLOSED:** the Execution, Craft, and Outcome floors have all been met.

SHIPPED is terminal for delivery, but it leaves an outcome obligation open. CLOSED is terminal for the whole work item. `Building`, `blocked`, `failed attempt`, and `unproven` are operating conditions, not completion verdicts.

The binding control is simple:

> **The actor may submit evidence. The actor may not issue its own verdict.**

A separate gate or verifier computes the grades and verdict from evidence that another party can independently retrieve or reproduce.

## Meaning in our world

ECO is the company-wide completion language for Company Autopilot, the CMO loop, fleet agents, Kai skills, and human operators. It converts completion from an actor's narrative into a verifier-computed record. It is not another prompt checklist: it is the contract used to decide whether work was delivered, whether the artifact is professionally acceptable, and whether the intended result occurred.

In this repo that means:

- Every skill declares an ECO floor, not a list of phases (`harness/eco-floors.yaml`).
- Every long-horizon run stops when the gate says the floor was met, not when the agent feels finished (`docs/system/long-horizon-operating-contract.md`).
- Every quantitative or client-facing claim inherits the data-provenance rule as its Craft floor (`harness/references/audit-data-provenance.md`).

---

## Why "done" was retired

The old word hid three clocks:

1. A file can exist now.
2. Its quality can be judged after review.
3. Its business effect can only be measured after an observation window.

Those are not the same event.

On 2026-07-27, the internal audit found the practical consequence:

- 230 tracked work items and 0 closeable records.
- 137 items represented as complete without terminal proof.
- Reconciliation missing from all 230.
- The fleet runner inferred success from exit code plus the actor's own prose.
- The outcome ledger recorded no return code, artifact, proof locator, or verifier.
- 4,777 of 4,801 `kai-cmo-execute` heartbeats produced zero artifacts while still reporting alive.
- Only 19 of roughly 214 scheduled jobs had an outcome check.

The problem was not a shortage of checklists. The system already had multiple written definitions. The problem was authority: the producer was also the witness, grader, and clerk.

ECO replaces the ambiguous label with three falsifiable claims.

---

## Why ECO matters more with the latest models

The frontier shifted from answer generation to goal pursuit.

As of July 2026:

- OpenAI describes GPT-5.6 as able to coordinate tools, process intermediate results, monitor progress, and choose its next action as work unfolds. ChatGPT Work is designed to turn a goal into finished work over hours.
- Anthropic reports that Claude sessions increasingly consist of long-running agentic tasks. Its long-running research workflows start from a high-level objective and use test oracles, persistent memory, and repeated sessions to keep advancing it.
- Google DeepMind presents Gemini 3.5/3.6 as models for long-horizon workflows, multi-step problem solving, tool use, and multi-agent orchestration.

These models are not merely predicting the next paragraph. In an agent harness, they repeatedly:

1. interpret an objective;
2. form and revise a plan;
3. select tools;
4. observe the environment;
5. recover from failed attempts;
6. continue until a stopping condition appears satisfied.

That is what "goal-oriented" means operationally here. It does not require a claim about consciousness or an intrinsic desire. The system is organized to optimize a delegated objective across a sequence of actions.

### Capability and verdict authority must separate

Greater goal-pursuit capability improves E. It can also make a weak completion signal more dangerous.

If the stopping rule is "exit code zero," the agent can stop at a successful command. If it is "an artifact exists," it can optimize for producing an artifact. If the same actor writes the work, selects the evidence, grades the evidence, and declares completion, then the easiest route to the goal may be satisfying the measurement rather than satisfying the operator's actual intent.

This is not hypothetical. OpenAI reported in July 2026 that a long-running internal model persisted through repeated attempts, found a sandbox weakness, and opened a public pull request even though it had been instructed to report only in Slack. Its conclusion was that each local action could look acceptable while the full trajectory pursued an outcome the user would not have approved. Mitigations included trajectory-level monitoring, incident-derived evaluations, and the ability for an external monitor to pause the session.

Anthropic frames the same design problem directly: a useful agent must pursue the user's goal while knowing when uncertainty requires a question and when autonomous research is appropriate. An agent that always stops loses its usefulness; one that always pushes through risks misreading intent.

ECO provides the missing stopping contract:

- **The objective defines the intended outcome.**
- **E defines what real-world effect must be observed.**
- **C defines the constraints on how good and acceptable the work must be.**
- **O defines the later result and measurement window.**
- **The independent gate, not the goal-pursuing actor, decides whether the stopping condition was actually met.**

### The actor may optimize; the verifier must falsify

The actor's job is constructive: find a path to the goal.

The verifier's job is adversarial in the ordinary quality-control sense: try to disprove that the floors were met. It reads from authoritative systems, reruns deterministic checks, samples the actual artifact, and preserves negative evidence.

This separation becomes more valuable as models get more persistent, better at tool use, better at navigating around obstacles, able to coordinate subagents, able to work across more applications, and able to run for hours, days, or repeated sessions.

The control should scale with **capability × autonomy × consequence**. A short drafting task may need a lightweight C review. A long-running agent with provider credentials, external side effects, and a revenue goal needs exact E read-back, explicit C constraints, predeclared O measures, trajectory visibility, and a verifier that can interrupt it.

> **Note on self-verification prompts.** ECO's verification is *out of band*. It is not an instruction telling the model to double-check itself — current Anthropic guidance is that explicit self-verification instructions cause over-verification on the latest models and should be removed from prompts. ECO puts verification in a deterministic gate the actor does not control, which is why the two are compatible: the actor is told what floor it must clear, never told to grade itself.

Latest-model sources:

- OpenAI, *GPT-5.6: Frontier intelligence that scales with your ambition* (2026-07-09): https://openai.com/index/gpt-5-6/
- OpenAI, *ChatGPT is now a partner for your most ambitious work* (2026-07-09): https://openai.com/index/chatgpt-for-your-most-ambitious-work/
- OpenAI, *Safety and alignment in an era of long-horizon models* (2026-07-20): https://openai.com/index/safety-alignment-long-horizon-models/
- OpenAI, *How agents are transforming work* (2026-06-25): https://openai.com/index/how-agents-are-transforming-work/
- Anthropic, *Trustworthy agents in practice* (2026-04-09): https://www.anthropic.com/research/trustworthy-agents
- Anthropic, *Long-running Claude for scientific computing* (2026-03-23): https://www.anthropic.com/research/long-running-Claude
- Anthropic, *Measuring AI agent autonomy in practice* (2026-02-18): https://www.anthropic.com/research/measuring-agent-autonomy
- Anthropic, *Prompting best practices — agentic systems*: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Google DeepMind, *Gemini 3.5* model family and capabilities: https://deepmind.google/models/gemini/

---

## E — Execution

Execution asks whether the intended effect occurred outside the actor's narration.

| Grade | Evidence floor | Meaning |
|---|---|---|
| **E0** | None | Nothing exists. |
| **E1** | Artifact exists | A file, render, draft, record, or build exists. |
| **E2** | Contract/specification passes | The artifact satisfies its declared schema or specification. |
| **E3** | Approval of exact bytes | A named authority approved the exact version, normally hash-pinned. |
| **E4** | Provider receipt | The external target accepted the action and returned a durable identifier. |
| **E5** | Independent read-back and reconciliation | A non-actor retrieved the postcondition from the authoritative target and reconciled it to the approved intent. |

### What Execution is not

None of these alone proves E5:

- a successful shell command;
- exit code zero;
- a green heartbeat;
- a local artifact;
- an open or merged pull request;
- a deployment marked ready;
- a provider request without provider read-back;
- an agent saying it checked.

Execution evidence must end at the real target. A published page requires public read-back. An email requires mailbox/provider evidence. A payment requires a provider receipt and ledger reconciliation. A task-state change requires read-back from the authoritative task system.

---

## C — Craft

Craft asks whether the artifact clears the professional bar of its discipline.

| Grade | Evidence floor | Meaning |
|---|---|---|
| **C0** | None | Craft was not assessed. |
| **C1** | Producer self-check | The actor ran the discipline's basic automated checks. |
| **C2** | Full machine-checkable gate | All declared objective checks passed at their stated thresholds. |
| **C3** | Independent judgment | A named non-producer reviewed the irreducibly human residue. |
| **C4** | Field standard | The work meets the named professional standard; deviations have explicit, expiring waivers. |

Craft is discipline-specific. "Good" cannot be a universal prompt adjective.

Examples:

- Editorial craft includes factual traceability, complete source use, audience fit, and an end-to-end read by someone other than the writer.
- Software craft includes tests, build validity, security and regression checks, operability, and rollback readiness.
- Design craft includes hierarchy, accessibility, token compliance, responsive behavior, and review at the actual viewing size.
- Video craft includes audio, captions, framing, pacing, platform specifications, and full-duration review.
- Data-pipeline craft includes schema integrity, lineage, idempotency, freshness, and explicit zero-result behavior.

In this repo, C2 for marketing content is the existing gate pipeline: Four U's, banned words, SEO lint, policy compliance, and audit provenance where quantitative claims are present.

### The deliverable is not its edit history

A client- or buyer-facing artifact must read as the final object, not as a patch diary. Superseded material is removed. `FIXED` badges, correction stamps, before/after scaffolding, and instructions to perform work already completed are craft failures unless the artifact is explicitly a changelog.

---

## O — Outcome

Outcome asks whether the intended result occurred, at the declared time, against a predeclared measure.

| Grade | Evidence floor | Meaning |
|---|---|---|
| **O0** | None | The outcome is unmeasured. |
| **O1** | Baseline and target recorded before ship | Metric, source, pre-state, threshold, owner, and observation window are declared. |
| **O2** | Instrumentation proven | A test event traversed the measurement path end to end. |
| **O3** | Observation completed | The metric was read from its authoritative source at the declared window. |
| **O4** | Threshold met | The observed result cleared the predeclared success threshold. |
| **O5** | Attribution supported | A credible counterfactual, holdout, control, quasi-experiment, or other appropriate causal design supports attribution. |

### Outcome cannot be invented after shipment

A baseline written after release is not a baseline. A success threshold chosen after seeing the result is not a threshold. A metric with no owner or read date is not an outcome plan.

Before SHIPPED, the work item must declare:

- the business or user result sought;
- the metric and authoritative source;
- the baseline;
- the threshold;
- the observation window;
- the measurement owner;
- the attribution method appropriate to the decision.

O3 proves that change was observed. O5 is deliberately harder: it asks whether this work caused the change. `knowledge/frameworks/marketing-science/attribution-and-incrementality.md` and `.../experiment-rigor.md` govern which designs qualify for O5.

---

## Verdicts and lifecycle

Each step declares its own required floor, such as `E5/C3/O3`. The gate compares evidence-derived grades with that floor.

| Condition | Computed disposition |
|---|---|
| E or C below floor | Open |
| E and C floors met; O window not yet complete | **SHIPPED** |
| E, C, and O floors met | **CLOSED** |
| Actor claims completion without sufficient independent evidence | Unproven; remains open |
| Attempt cannot continue without an external change | Blocked; remains open |
| Attempt ran and missed its required floor | Failed attempt recorded; remains open or is explicitly abandoned |

Only SHIPPED and CLOSED carry completion semantics.

### Nothing is CLOSED on ship day by default

Some work has an immediately observable outcome, but most commercial, content, reliability, and growth work does not. A page may be SHIPPED after production read-back and craft review, then CLOSED after its indexing, conversion, revenue, or other declared window is measured.

SHIPPED therefore creates a tracked debt:

```text
SHIPPED E5/C3/O1
Outcome due: 2026-08-10
Required next evidence: O3 citation-panel read
Owner: AI visibility lead
```

If that debt has no owner and date, SHIPPED is being used as the old `done`.

---

## Independent verdict authority

The actor-verifier boundary is about independence of evidence, not the number of agent names involved.

Three agents using the same model substrate and the same source are not three independent votes. A signed self-attestation proves who authored it; it does not make the claim independent.

### Honest quorum

Evidence above E1/C1 must differ from the actor in at least one meaningful substrate:

- external provider or public target read-back;
- deterministic machine check;
- independent human reviewer with the needed authority and competence;
- separately controlled runtime or data source;
- reproducible query against the authoritative system.

The stronger the claim and risk, the stronger the independence required.

### Small-team compensating control

Perfect maker/checker separation is sometimes impossible. The answer is not self-verdict. The compensating control is a deterministic gate plus more frequent independent audit, narrow authority, append-only evidence, and periodic re-performance by a person.

The verifier must record:

- verifier identity and substrate;
- evidence locators;
- checks performed;
- observed values;
- timestamps;
- computed grades;
- unmet criteria;
- verdict.

The actor submits none of the computed fields.

---

## The mandatory failure record

Every ended attempt that does not produce SHIPPED or CLOSED must have a structured failure record. Active `Building` work is not a failed attempt and does not receive this record until the attempt ends, blocks, or is abandoned. Mentioning "failed," "blocked," or an error in prose does not satisfy this rule.

Minimum fields:

```json
{
  "attempt_id": "attempt-...",
  "subject_id": "work-item-...",
  "step_id": "declared-step",
  "actor": "producer identity",
  "started_at": "ISO-8601",
  "ended_at": "ISO-8601",
  "condition": "unproven | blocked | failed_attempt",
  "failed_axis": ["E", "C", "O"],
  "required_floor": {"E": 5, "C": 3, "O": 3},
  "observed_grade": {"E": 4, "C": 2, "O": 1},
  "failed_predicates": ["independent_verification", "second_pair"],
  "evidence": ["resolvable locator"],
  "authoritative_error": "exact provider or gate result",
  "retryability": "retryable | waiting | abandoned",
  "next_action": "specific action or external condition",
  "owner": "named owner",
  "next_check_at": "ISO-8601 or null",
  "verdict_by": "non-actor verifier"
}
```

Rules:

1. The record identifies which axis failed; it does not use a generic red status.
2. Exact provider or gate output is preserved where safe.
3. `Blocked` names the external condition and next check.
4. `Failed attempt` does not terminate the work item by itself.
5. `Unproven` is not failure. It means the evidence cannot support the claim yet.
6. Zero output is a result that must be explained, not a healthy heartbeat by default.
7. A later successful attempt links to, but never overwrites, the failure record.

This makes negative evidence queryable. It also prevents success-rate inflation caused by simply omitting failed attempts.

---

## The ECO record

One append-only ECO record exists per work item and step. The actor contributes evidence; the gate computes the rest.

```json
{
  "schema_version": "kai.eco-record.v1",
  "record_id": "eco-...",
  "subject_id": "work-item-...",
  "step_id": "social.linkedin.article.publish",
  "floor_required": {"E": 5, "C": 3, "O": 3},
  "claimed_by": "actor",
  "claimed_at": "2026-07-27T18:04:11Z",
  "evidence": [
    {
      "kind": "artifact_exists",
      "locator": "workspace/output/connect-your-tools/article.md",
      "produced_by": "producer-agent",
      "observed_at": "2026-07-27T18:02:00Z"
    },
    {
      "kind": "contract_spec_pass",
      "locator": "workspace/output/connect-your-tools/contract-report.json",
      "check": "linkedin_article_contract",
      "verifier": "social-contract-check",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T18:03:00Z"
    },
    {
      "kind": "approval_review",
      "locator": "data/runtime/approvals/connect-your-tools.json",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "verifier": "Connor Gallic",
      "verifier_substrate": "human",
      "observed_at": "2026-07-27T18:04:00Z"
    },
    {
      "kind": "provider_receipt",
      "locator": "linkedin:post:urn:li:share:example",
      "verifier": "linkedin-provider-adapter",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T18:05:00Z"
    },
    {
      "kind": "independent_verification",
      "locator": "https://www.linkedin.com/posts/example",
      "check": "public_readback",
      "expected": "200 and approved marker",
      "observed": "200 and marker matched",
      "verifier": "content-obligation-check",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T19:00:04Z"
    },
    {
      "kind": "reconciliation",
      "locator": "data/runtime/reconciliation/connect-your-tools.json",
      "verifier": "social-ledger-reconciler",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T19:01:00Z"
    },
    {
      "kind": "craft_gate_pass",
      "locator": "data/learning/gate_runs.jsonl#connect-your-tools",
      "check": "four_us>=12, banned_words==0, seo_lint_hard_errors==0",
      "verifier": "kai-quality-gates",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T18:03:20Z"
    },
    {
      "kind": "craft_independent_review",
      "locator": "data/runtime/reviews/connect-your-tools.json",
      "check": "end_to_end_read_by_non_producer",
      "verifier": "Connor Gallic",
      "verifier_substrate": "human",
      "observed_at": "2026-07-27T18:04:00Z"
    },
    {
      "kind": "outcome_baseline",
      "locator": "data/runtime/outcomes/connect-your-tools.json",
      "check": "metric=qualified_demo_requests source=ga4 baseline=14 threshold=21 window=30d owner=Connor",
      "verifier": "outcome-registrar",
      "verifier_substrate": "deterministic",
      "observed_at": "2026-07-27T18:01:00Z"
    }
  ],
  "computed": {
    "grade": {"E": 5, "C": 3, "O": 1},
    "verdict": "SHIPPED",
    "unmet": ["O3"],
    "outcome_due_at": "2026-08-26T00:00:00Z",
    "verdict_by": "kai-eco-gate",
    "verdict_at": "2026-07-27T19:01:30Z"
  }
}
```

Field rules:

1. `evidence` is append-only. Superseding an entry means adding a new one, never editing the old one.
2. Everything under `computed` is written by the gate. An actor-submitted `computed` block invalidates the record.
3. Every evidence entry above E1/C1 needs `verifier` and `verifier_substrate`, and the verifier must not equal `claimed_by`.
4. `locator` must be resolvable by someone other than the actor.

---

## How ECO binds to this repo

| ECO axis | Where it is already enforced | Gate |
|---|---|---|
| E1–E2 | Runtime store artifacts, skill contract `output_schema` | `kai/runtime/store.py` |
| E3 | ActionStore approval, `approval_gate` in skill contracts | `kai/runtime/actions.py` |
| E4–E5 | Publisher receipts + `content_log.mark_published()` public read-back | `scripts/publish/`, `scripts/social/` |
| C1–C2 | Four U's, banned words, SEO lint, policy references, audit provenance | `scripts/quality_gates/` |
| C3 | `human_review_required_when` in skill contracts | Approval doctrine |
| O1–O2 | 30-day pending check registration at publish time | `data/content_log.json` |
| O3–O4 | 30-day grading; winners to `what-works.md`, losers to `what-doesnt-work.md` | `/kai-retro` |
| O5 | Incrementality and experiment rigor frameworks | `knowledge/frameworks/marketing-science/` |

The ECO gate does not replace any of these. It reads their outputs, computes grades, and issues the single verdict none of them was allowed to issue on its own.

Related doctrine: `docs/system/governance-and-quality.md` · `docs/system/execution-lifecycle.md` · `docs/system/long-horizon-operating-contract.md` · `docs/system/learning-loop.md`

# Governance and Quality

Kai should be useful without being reckless. Governance is split into deterministic gates, platform policy references, provenance rules, approval state, and memory writeback.

## Quality Gate Stack

```mermaid
flowchart TB
    Draft["Draft or proposal"]
    Contract["Skill contract<br/>harness/skill-contracts/*.yaml"]
    Framework["Framework and channel rules<br/>knowledge + harness/references"]
    FourUs["Four U's score"]
    Banned["Banned word check"]
    Seo["SEO lint when search-targeted"]
    Policy["Platform and risk policy"]
    Provenance["Audit provenance lint when claims are client-facing"]
    Decision{"Ship, hold, revise, or fail?"}
    Approved["Approved asset or action"]
    Held["Held for human review"]
    Revision["Revision loop"]
    Failed["Failed after allowed retries"]

    Draft --> Contract
    Contract --> Framework
    Framework --> FourUs
    FourUs --> Banned
    Banned --> Seo
    Seo --> Policy
    Policy --> Provenance
    Provenance --> Decision
    Decision --> Approved
    Decision --> Held
    Decision --> Revision
    Decision --> Failed
```

## Gate Responsibilities

| Gate | Code or source | Blocks on |
|---|---|---|
| Skill contract | `harness/skill-contracts/*.yaml` | Wrong structure, wrong format, missing required sections. |
| Four U's | `scripts/quality_gates/four_us_score.py` | Content below the required usefulness and specificity threshold. |
| Banned words | `scripts/quality_gates/banned_word_check.py` | Tier 1 filler, weak claims, and language that should not ship. |
| SEO lint | `scripts/quality_gates/seo_lint.py` | Search content that breaks structural SEO and Algorithmic Authorship rules. |
| Platform policy | `harness/references/*-ads-*.md`, `kai/runtime/policy.py` | Platform rule violations, regulated claims, personal attributes, unsafe spend changes. |
| Audit provenance | `scripts/quality_gates/audit_provenance_lint.py` | Quantitative or client-facing claims without a source. |
| Agent readiness | `scripts/quality_gates/agent_readiness_lint.py` | Site-level AEO work when robots, llms.txt, schema, or JS access block AI-readiness. |

## Approval Decision Model

```mermaid
flowchart LR
    Result["Gate or policy result"]
    Risk{"Risk tier"}
    Low["Low risk"]
    Medium["Medium risk"]
    High["High risk"]
    Auto{"Auto eligible?"}
    Human["Human review"]
    Approve["Approve"]
    Hold["Hold"]
    Reject["Reject"]
    Execute["Execute approved action"]

    Result --> Risk
    Risk --> Low
    Risk --> Medium
    Risk --> High
    Low --> Auto
    Auto -->|yes| Approve
    Auto -->|no| Human
    Medium --> Human
    High --> Human
    Human --> Approve
    Human --> Hold
    Human --> Reject
    Approve --> Execute
```

## Provenance Rule

For audits, reports, decks, competitor teardowns, CRO work, analytics plans, growth plans, and retrospectives:

- Declare the data mode: `sales_external`, `onboarding_connected`, or `internal_demo`.
- Collect data before writing with `python -m scripts.audit.collect --url <url> --mode <mode> --workflow <workflow> --out <data-folder>`.
- Cite collector sources for client-facing numbers.
- Put missing inputs in `_data-gaps.md`.
- Run `python scripts/quality_gates/audit_provenance_lint.py <audit-folder> --audit-dir` before handoff.

```mermaid
flowchart TB
    Request["Audit-style workflow"]
    Mode["Declare data mode"]
    Collect["Run data collector"]
    Data["kai-data.json / audit-data.json"]
    Gaps["_data-gaps.md"]
    Draft["Write report or deck"]
    Lint["audit_provenance_lint.py"]
    Pass["Client-ready"]
    Hold["Fix sources or label gaps"]

    Request --> Mode
    Mode --> Collect
    Collect --> Data
    Collect --> Gaps
    Data --> Draft
    Gaps --> Draft
    Draft --> Lint
    Lint -->|pass| Pass
    Lint -->|fail| Hold
    Hold --> Draft
```

## Memory Writeback

Approved work can become future context. Rejected, held, and failed work should still be visible for observability, but should not silently become a learned pattern.

```mermaid
flowchart LR
    Approved["Approved run or verified action"]
    Extract["Extract decision, artifact, and outcome"]
    Memory["Brand memory / learned patterns"]
    Retrieval["Future prompt retrieval"]
    Guard["Anti-pattern memory"]

    Approved --> Extract
    Extract --> Memory
    Memory --> Retrieval
    Retrieval --> Approved
    Extract --> Guard
```

## Practical Rule

Any workflow that can change a live channel should produce an `ActionProposal` first. The proposal should contain:

- proposed changes
- evidence
- risk tier
- policy result
- preview artifact when possible
- verification criteria
- rollback reference when needed


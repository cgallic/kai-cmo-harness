# Execution Lifecycle

Kai has three major execution loops:

1. Local content generation through skills and `scripts/content/engine.py`.
2. Programmatic audits that produce findings, proposals, bundles, and action candidates.
3. Remote jobs and operator actions through the FastAPI gateway.

All three should preserve the same runtime contract: request, run record, artifacts, approval, state update, memory or result writeback.

## Local Content Generation

```mermaid
sequenceDiagram
    actor Operator
    participant Skill as Kai skill
    participant Runtime as Kai runtime
    participant Engine as Content engine
    participant Writer as Writer
    participant Gates as Quality gates
    participant Store as Runtime store
    participant Approval as Approval policy
    participant Memory as Memory

    Operator->>Skill: Invoke /kai-write or workflow alias
    Skill->>Runtime: Resolve workspace, brand, modules, workflow
    Runtime->>Store: start_run(KaiRunRequest)
    Runtime->>Engine: generate(format, site, keyword)
    Engine->>Engine: Resolve persona and brief
    Engine->>Writer: Assemble prompt and draft
    Writer-->>Engine: Draft content
    Engine->>Gates: Four U's, banned words, SEO or policy checks
    Gates-->>Engine: Gate report
    Engine->>Approval: Apply approval policy
    Approval-->>Engine: approved, held, failed, or draft
    Engine->>Store: Create artifacts and complete run
    Store->>Memory: Write back approved learning
```

## Audit and Proposal Flow

```mermaid
flowchart TB
    Profile["BusinessProfile"]
    Normalize["Normalize channels, locations, offers, metadata"]
    Audits["8 audit engines"]
    Findings["Scored findings"]
    Proposals["Proposal mapper and ranker"]
    Bundle["Review bundle<br/>7-day, 30-day, campaign packs"]
    Policy["PolicyEngine<br/>risk, claims, spend, channel rules"]
    Action["ActionProposal"]
    Human["Human approval or hold"]
    Execute["Execution bridge"]
    Verify["Verification result"]
    Learn["Memory writeback"]

    Profile --> Normalize
    Normalize --> Audits
    Audits --> Findings
    Findings --> Proposals
    Proposals --> Bundle
    Bundle --> Policy
    Policy --> Action
    Action --> Human
    Human --> Execute
    Execute --> Verify
    Verify --> Learn
```

## Remote Gateway Flow

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI gateway
    participant Jobs as SQLite job queue
    participant Runtime as Runtime store
    participant Worker as Background worker
    participant Handler as Workflow handler
    participant Artifacts as Artifact records

    Client->>API: POST remote workflow or operator action
    API->>Jobs: create_job(command, options, run_request)
    Jobs->>Runtime: Seed canonical run record
    API-->>Client: job_id
    Worker->>Jobs: Pick pending job
    Worker->>Runtime: Mark run started
    Worker->>Handler: Execute workflow handler
    Handler-->>Worker: Result payload
    Worker->>Artifacts: Persist output artifacts
    Worker->>Runtime: Complete or fail run
    Client->>API: GET /jobs or /runtime/runs/{run_id}
    API-->>Client: Status, artifacts, lineage
```

## Run State Machine

`KaiRunRecord.status` is intentionally small. Workflows can add richer metadata, but the main state should stay readable.

```mermaid
stateDiagram-v2
    [*] --> running
    running --> draft: generated but needs revision
    running --> held: gate or policy wants review
    running --> approved: approved directly
    running --> completed: finished without approval need
    running --> failed: unrecoverable error
    draft --> held: human or gate hold
    draft --> approved: approved revision
    held --> draft: revision requested
    held --> approved: human approval
    held --> failed: rejected
    approved --> completed: executed or logged
    completed --> approved: explicit approval after completion
    completed --> failed: rejected after review
    failed --> [*]
    completed --> [*]
```

## Action Proposal State

Action proposals are for real-world mutations: website edits, social posts, ad changes, email sends, analytics updates, and similar work. They track both approval and execution.

```mermaid
stateDiagram-v2
    [*] --> drafted
    drafted --> gated: policy_result attached
    gated --> approved: approval_state approved
    gated --> held: approval_state held
    gated --> rejected: approval_state rejected
    held --> approved: human approval
    held --> rejected: human rejection
    approved --> executed: execution_state completed
    approved --> failed: execution_state failed
    executed --> verified: verification_result attached
    verified --> learned: memory_writeback_ids present
    failed --> rolled_back: rollback applied
    learned --> [*]
    rejected --> [*]
    rolled_back --> [*]
```

| Field | Values |
|---|---|
| `approval_state` | `pending`, `approved`, `rejected`, `auto_approved`, `held` |
| `execution_state` | `pending`, `executing`, `completed`, `failed`, `rolled_back` |
| Derived operating state | `drafted`, `gated`, `approved`, `executed`, `verified`, `learned` |

## Lineage

Each run and artifact keeps enough lineage to answer:

- Which request created this output?
- Which parent run or prior artifacts influenced it?
- Which approval or hold decision happened?
- Which artifact should be used as the latest result for a brand and workflow?

```mermaid
flowchart LR
    Parent["Parent run"]
    Run["Current run"]
    Brief["Brief artifact"]
    Draft["Draft artifact"]
    Gate["Gate proposal artifact"]
    Approved["Approved asset"]
    Snapshot["Performance snapshot"]
    Pattern["Learned pattern"]
    State["Runtime state index"]

    Parent --> Run
    Run --> Brief
    Brief --> Draft
    Draft --> Gate
    Gate --> Approved
    Approved --> Snapshot
    Snapshot --> Pattern
    Run --> State
    Approved --> State
```


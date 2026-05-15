# Runtime Map

Kai is organized around a small set of runtime nouns. The docs and code should keep pointing back to these nouns so new workflows do not invent parallel contracts.

## Layer Model

```mermaid
flowchart TB
    subgraph Product["Kai Marketing OS"]
        Skills["Skills<br/>operator workflows"]
        Modules["Modules<br/>archetype defaults"]
        Knowledge["Knowledge base<br/>frameworks, policies, checklists"]
        Quality["Quality gates<br/>score, lint, policy"]
        Approval["Approvals<br/>human or auto by risk"]
    end

    subgraph Runtime["Kai Runtime"]
        Workspace["KaiWorkspaceProfile"]
        Brand["KaiBrandProfile"]
        Workflow["WorkflowDefinition"]
        Run["KaiRunRequest + KaiRunRecord"]
        Artifact["KaiArtifactRecord"]
        State["KaiRuntimeState"]
    end

    subgraph Implementation["Implementation"]
        Content["scripts/content/engine.py"]
        Audits["kai/audits"]
        Proposals["kai/proposals"]
        Store["kai/runtime/store.py"]
        Gateway["gateway"]
        Actions["kai/runtime/actions.py"]
    end

    Skills --> Workspace
    Modules --> Brand
    Knowledge --> Workflow
    Workspace --> Brand
    Brand --> Workflow
    Workflow --> Run
    Run --> Artifact
    Artifact --> State
    Quality --> Run
    Approval --> Run
    Run --> Store
    Content --> Artifact
    Audits --> Proposals
    Proposals --> Actions
    Gateway --> Store
```

## Runtime Nouns

| Noun | Code source | Purpose |
|---|---|---|
| Workspace profile | `kai/runtime/models.py` | Describes the workspace, available surfaces, enabled plugins, and brands. |
| Brand profile | `kai/runtime/models.py` | Describes one business target: URL, archetype, channels, proof, personas, and metadata. |
| Module manifest | `kai/runtime/modules/*.yaml` | Adds archetype defaults: trigger words, prompt hints, required memory, workflows, KPIs, subagents, and automation names. |
| Workflow definition | `kai/runtime/workflows.py` | Maps product workflows to handlers, input contracts, output artifacts, quality policy, aliases, and risk. |
| Run request | `kai/runtime/models.py` | The cross-surface invocation contract for local and remote execution. |
| Run record | `kai/runtime/models.py` | The persisted lifecycle record for a run, including status, lineage, artifacts, inputs, outputs, and timestamps. |
| Artifact record | `kai/runtime/models.py` | The persisted output contract for briefs, drafts, audits, plans, snapshots, and learned patterns. |
| Runtime state | `kai/runtime/models.py` | A derived index of latest runs and artifacts by brand and workflow. |
| Action proposal | `kai/runtime/actions.py` | The contract for real-world marketing mutations such as publishing, editing, or changing spend. |

## Data Model

```mermaid
erDiagram
    WORKSPACE ||--o{ BRAND : contains
    BRAND ||--o{ MODULE : activates
    BRAND ||--o{ RUN : owns
    MODULE ||--o{ RUN : guides
    WORKFLOW ||--o{ RUN : invokes
    RUN ||--o{ ARTIFACT : creates
    RUN ||--o{ ACTION : proposes
    ACTION ||--o{ ACTION_LOG : records
    ARTIFACT ||--o{ MEMORY_ENTRY : teaches
    RUN ||--o{ RUNTIME_STATE : indexes

    WORKSPACE {
        string workspace_id
        string name
        string primary_user
        string product_mode
    }

    BRAND {
        string id
        string name
        string primary_archetype
        array module_ids
        array active_channels
    }

    RUN {
        string run_id
        string workflow
        string brand_id
        string surface
        string status
    }

    ARTIFACT {
        string artifact_id
        string artifact_type
        string workflow
        string brand_id
    }

    ACTION {
        string action_id
        string channel
        string action_type
        string risk_tier
        string approval_state
        string execution_state
    }
```

## Module Activation

Module activation turns a business profile into operating defaults. A local-service brand gets call conversion, reviews, GBP, and speed-to-lead guidance; an ecommerce brand gets creative, product pages, retention, and paid social guidance.

```mermaid
flowchart LR
    Input["Business or product context"]
    Loader["kai/runtime/loader.py"]
    Archetype["Primary archetype"]
    Overlays["Optional overlays"]
    Manifest["kai/runtime/modules/*.yaml"]
    Brand["KaiBrandProfile.module_ids"]
    Prompt["Prompt hints and workflow defaults"]
    Gates["Checklist and KPI expectations"]

    Input --> Loader
    Loader --> Archetype
    Loader --> Overlays
    Archetype --> Manifest
    Overlays --> Manifest
    Manifest --> Brand
    Brand --> Prompt
    Brand --> Gates
```

## Code Map

| Area | Files |
|---|---|
| Canonical models | `kai/runtime/models.py` |
| Workspace and module loading | `kai/runtime/loader.py`, `kai/runtime/modules/*.yaml` |
| Workflow registry | `kai/runtime/workflows.py` |
| Persistence | `kai/runtime/store.py`, `kai/runtime/actions.py` |
| Content generation | `scripts/content/engine.py`, `scripts/content/_writer.py`, `scripts/content/brief_generator.py` |
| Quality gates | `scripts/quality_gates/*.py` |
| Audit and proposals | `kai/audits/`, `kai/proposals/`, `kai/runtime/application_flow.py` |
| Compliance and approval | `kai/compliance/`, `kai/runtime/policy.py`, `scripts/content/approval_policy.py` |
| Remote API | `gateway/main.py`, `gateway/routers/runtime.py`, `gateway/routers/actions.py` |
| Background work | `agent/scheduler.py`, `agent/tasks/` |


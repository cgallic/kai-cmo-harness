# Runtime Schema Files

These files are JSON Schema documents for the system contracts described in `docs/system/`.

| File | Describes |
|---|---|
| `kai-workspace-profile.schema.json` | Workspace-level profile and embedded brands. |
| `kai-brand-profile.schema.json` | Brand/business target profile. |
| `kai-module-manifest.schema.json` | Archetype module manifest. |
| `workflow-definition.schema.json` | Workflow registry entry. |
| `kai-run-request.schema.json` | Local or remote run invocation. |
| `kai-run-record.schema.json` | Persisted run lifecycle record. |
| `kai-artifact-record.schema.json` | Persisted runtime artifact. |
| `kai-runtime-state.schema.json` | Derived runtime state index. |
| `action-proposal.schema.json` | Proposed live-channel action. |
| `system-documentation-bundle.schema.json` | Optional manifest for docs packs like this one. |

The schemas are intentionally permissive for `metadata`, `inputs`, `outputs`, and artifact `data` because each workflow can add specialized payloads.


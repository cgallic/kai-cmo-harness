# Agent-to-UI Specification (v1.0)

This document defines the **Agent-to-UI Specification**, a machine-readable JSON schema that acts as the state database and communication channel between Kai's autonomous marketing agents, Python compilers, and the static user interface.

By structuring the workspace state in a standardized JSON file (`workspace/agent_ui_spec.json`), any agent (such as a Codex subagent or a local Python run script) can read the current state of the workspace, perform actions, and write results back. The client dashboard (`workspace/dashboard.html`) loads this JSON file to reflect the updated state.

---

## 1. File Locations

* **JSON Database**: `workspace/agent_ui_spec.json`
* **UI Dashboard**: `workspace/dashboard.html`
* **JSON Schema Document**: `docs/AGENT_TO_UI_SPEC.md`
* **State Compiler**: `scripts/build_dashboard.py`

---

## 2. JSON Schema Structure

The `agent_ui_spec.json` consists of the following top-level keys:

```json
{
  "project": {
    "id": "string",
    "name": "string",
    "description": "string"
  },
  "owner": {
    "name": "string",
    "email": "string"
  },
  "autonomy_mode": "supervised | balanced | autonomous",
  "marketing_score": 0-100,
  "score_breakdown": {
    "offer": 0-100,
    "trust": 0-100,
    "cro": 0-100,
    "seo": 0-100,
    "copy": 0-100,
    "channels": 0-100,
    "conversion": 0-100,
    "readiness": 0-100
  },
  "metrics": {
    "traffic": {
      "sessions": "integer",
      "users": "integer",
      "bounce_rate": "string",
      "conversions": "integer"
    },
    "seo": {
      "impressions": "integer",
      "clicks": "integer",
      "avg_position": "float"
    }
  },
  "agents": [
    {
      "id": "string",
      "name": "string",
      "role": "string",
      "status": "idle | working | done | error",
      "purpose": "string",
      "model": "string",
      "assurance": "high | standard",
      "markdown_path": "string",
      "content": "string"
    }
  ],
  "task_queue": [
    {
      "id": "string",
      "name": "string",
      "priority": "P0 | P1 | P2",
      "status": "done | ready_for_review | ready | pending",
      "dependencies": ["string"],
      "first_targets": ["string"],
      "acceptance_summary": "string"
    }
  ],
  "executions": [
    {
      "id": "string",
      "task_id": "string",
      "name": "string",
      "slice": "string",
      "status": "completed | failed | running",
      "timestamp": "ISO8601 string",
      "files_changed": ["string"],
      "verification": "string",
      "markdown_path": "string",
      "content": "string"
    }
  ],
  "connections": [
    {
      "id": "string",
      "provider": "string",
      "channel": "string",
      "status": "connected | disconnected | error",
      "connected_at": "ISO8601 string",
      "last_verified_at": "ISO8601 string",
      "config": "object"
    }
  ],
  "workspace_assets": {
    "growth_plans": [
      {
        "name": "string",
        "path": "string",
        "content": "string"
      }
    ],
    "content_briefs": [
      {
        "name": "string",
        "path": "string",
        "content": "string"
      }
    ],
    "demo_clients": [
      {
        "name": "string",
        "path": "string",
        "files": [
          {
            "name": "string",
            "path": "string",
            "content": "string"
          }
        ]
      }
    ]
  },
  "chat_history": [
    {
      "role": "user | assistant | system",
      "content": "string",
      "timestamp": "ISO8601 string"
    }
  ],
  "last_updated": "ISO8601 string"
}
```

---

## 3. Protocol for Agent Updates

When an agent executes a task or generates content, it updates the UI by following these steps:

1. **Perform the operation**: Write files to the workspace (e.g. generate a marketing brief or blog post under `workspace/demo-clients/`).
2. **Update the JSON file**:
   * Open and parse `workspace/agent_ui_spec.json`.
   * Add a new run entry under `"executions"`.
   * If new content is generated, add it to `"workspace_assets"`.
   * Update the `"last_updated"` timestamp.
   * Write the updated JSON back to `workspace/agent_ui_spec.json`.
3. **Re-render the Dashboard**:
   * Run the Python compiler script: `python scripts/build_dashboard.py` (which syncs any manual edits, reads JSON records from `data/runtime/`, and regenerates `workspace/dashboard.html` with the embedded JSON state).

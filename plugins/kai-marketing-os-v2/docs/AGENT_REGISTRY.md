# Agent Registry (OSS MVP)

Kai now includes a local, file-backed agent registry at `kai/runtime/agents.py`.

Each agent record is a `KaiAgentProfile` with:

- `agent_id`, `name`, `owner`, `purpose`, `workspace_id`
- `brand_scope`, `workflow_scope`, `tool_scope`
- `model`, `assurance_level`, `status`
- `created_at`, `expires_at`, `revoked_at`, `metadata`

## Add an agent profile

```python
from kai.runtime.agents import AgentRegistry
from kai.runtime.models import KaiAgentProfile

registry = AgentRegistry.default()
profile = registry.create(
    KaiAgentProfile(
        name="Kai SEO Worker",
        owner="ops@company.com",
        purpose="Runs SEO audits for one brand.",
        workspace_id="kai-marketing-os",
        brand_scope=["acme-hvac"],
        workflow_scope=["kai-seo-audit"],
        tool_scope=["quality_gates"],
        model="gpt-5.4",
        assurance_level="standard",
    )
)
print(profile["agent_id"])
```

## Scope checks before execution

```python
result = registry.check_scope(
    profile["agent_id"],
    workspace_id="kai-marketing-os",
    brand_id="acme-hvac",
    workflow_id="kai-seo-audit",
    tool_id="quality_gates",
)
assert result["allowed"] is True
```

Use `registry.revoke(agent_id)` to immediately disable an agent.

## Starter examples

Use `default_agent_profiles()` to load local example profiles for:

- `agent_kai_operator`
- `agent_content_worker`
- `agent_connector_watcher`

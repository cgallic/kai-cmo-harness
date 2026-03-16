# Adding Products

How to add a new product to the Kai CMO Harness. A product is anything with its own URL, analytics, and content pipeline — a SaaS app, a client site, an e-commerce store, etc.

---

## Step 1 — Add to config.yaml

Open `config.yaml` and add a new entry under `products:`.

```yaml
products:
  # ... existing products ...

  - id: mynewproduct
    name: "MyNewProduct"
    url: "https://mynewproduct.com"
    description: "AI-powered inventory management for restaurants"
    supabase_url_env: "MYNEWPRODUCT_SUPABASE_URL"
    supabase_key_env: "MYNEWPRODUCT_SUPABASE_KEY"
    ga4_property_env: "GA_MYNEWPRODUCT_PROPERTY_ID"
    gsc_url_env: "GSC_MYNEWPRODUCT_URL"
    discord_channel_id: "1234567890123456789"
    proof_points: |
      - 340 restaurants onboarded. Average food waste reduced 23%.
      - Pricing: $89/mo (Starter), $199/mo (Pro), $499/mo (Enterprise).
      - Integration: POS systems (Toast, Square, Clover), accounting (QuickBooks, Xero).
      - Average payback period: 6 weeks at $199/mo tier.
```

Rules for `proof_points`:
- Use verified numbers only. The harness injects these directly into write prompts.
- Include pricing, customer counts, specific metrics, and competitive advantages.
- Never include aspirational or unverified claims.

## Step 2 — Add environment variables to .env

Add the corresponding credentials for the `*_env` fields you referenced in config.yaml.

```bash
# MyNewProduct - Supabase
MYNEWPRODUCT_SUPABASE_URL=https://xxx.supabase.co
MYNEWPRODUCT_SUPABASE_KEY=eyJxxx

# MyNewProduct - Google Analytics 4
GA_MYNEWPRODUCT_PROPERTY_ID=456789012

# MyNewProduct - Google Search Console
GSC_MYNEWPRODUCT_URL=sc-domain:mynewproduct.com
```

If you don't have analytics set up yet, leave the env vars empty. The harness will skip data pulls and generate briefs from keyword + proof points alone.

## Step 3 — Render workspace templates

```bash
python render_templates.py
```

Output:

```
Config:    /path/to/config.yaml
Output:    /path/to/workspace/

Owner:     Connor Gallic
Products:  KaiCalls, BuildWithKai, ABP, MyNewProduct

--- Agent templates (.j2) ---
  rendered: agents/mynewproduct-agent.md

--- Workspace markdown files ---
  rendered: MARKETING.md
  rendered: AGENTS.md

Done. Rendered 3 file(s).
```

The renderer:
1. Finds `.j2` templates in `workspace/agents/` and renders them with your product data
2. Scans `MARKETING.md`, `AGENTS.md`, `HEARTBEAT.md`, `TOOLS.md`, `SOUL.md` for Jinja2 syntax and renders them in-place
3. Injects product names, URLs, proof points, and Discord channels

## Step 4 — (Optional) Create a custom task handler

If your product needs specialized scheduled tasks (beyond the default analytics + content pipeline), create a task handler.

Create `agent/tasks/mynewproduct_ops.py`:

```python
"""
MyNewProduct operational tasks.
"""

from typing import Any, Dict, Optional

from .base import BaseTask
from ..models import ScheduledTask


class MyNewProductOpsTask(BaseTask):
    """Handles MyNewProduct-specific scheduled operations."""

    @property
    def task_type(self) -> str:
        return "mynewproduct_ops"

    @property
    def description(self) -> str:
        return "MyNewProduct operational monitoring"

    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Run MyNewProduct health checks.

        Pulls from Supabase, checks for anomalies, returns summary.
        """
        import os
        from supabase import create_client

        url = os.getenv("MYNEWPRODUCT_SUPABASE_URL", "")
        key = os.getenv("MYNEWPRODUCT_SUPABASE_KEY", "")

        if not url or not key:
            return {"success": False, "summary": "Missing Supabase credentials"}

        client = create_client(url, key)

        # Example: check recent signups
        result = client.table("users").select("id", count="exact").gte(
            "created_at", "now() - interval '24 hours'"
        ).execute()

        signup_count = result.count or 0
        summary = f"MyNewProduct: {signup_count} new signups in last 24h"

        if signup_count == 0:
            summary += " -- ALERT: zero signups, investigate"

        return {
            "success": True,
            "summary": summary,
            "data": {"signups_24h": signup_count}
        }
```

Register it in `agent/tasks/__init__.py`:

```python
from .mynewproduct_ops import MyNewProductOpsTask

TASK_REGISTRY = {
    # ... existing tasks ...
    "mynewproduct_ops": MyNewProductOpsTask,
}
```

Add to the scheduler in `agent/scheduler.py` under `create_default_tasks()`:

```python
{
    "name": "MyNewProduct Daily Report",
    "cron_expression": "0 8 * * *",
    "task_type": "mynewproduct_ops",
    "client": "mynewproduct",
    "config": {"notify_on_complete": True}
},
```

## Step 5 — (Optional) Set up analytics

See `docs/ANALYTICS_SETUP.md` for full instructions per service. Quick summary:

### Google Analytics 4
1. Create a GA4 property for mynewproduct.com
2. Create a service account (or reuse existing) and grant Viewer access
3. Copy the property ID to `GA_MYNEWPRODUCT_PROPERTY_ID` in `.env`

### Google Search Console
1. Add mynewproduct.com as a property in GSC
2. Add the service account email as a user with read access
3. Set `GSC_MYNEWPRODUCT_URL=sc-domain:mynewproduct.com` in `.env`

### Supabase
1. Create a project (or use existing)
2. Get the URL and service role key from Settings > API
3. Set `MYNEWPRODUCT_SUPABASE_URL` and `MYNEWPRODUCT_SUPABASE_KEY` in `.env`

### Site registry

Add to `SITES_CONFIG` in `.env`:

```bash
SITES_CONFIG={"kaicalls":{...},"mynewproduct":{"name":"MyNewProduct","url":"https://mynewproduct.com","category":"product"}}
```

## Step 6 — Verify

### Claude Code path

```bash
# Check that the knowledge base loads the new product's proof points
# Open Claude Code and ask:
> What proof points do we have for MyNewProduct?
```

### OpenClaw path

Run the harness status check:

```bash
python scripts/harness_cli.py status
```

Expected output includes `mynewproduct` in the sites list:

```
══════════════════════════════════════════════════
  Kai Harness — Status
══════════════════════════════════════════════════

  Tracked pieces:      12
  Winners:             3
  Pending 30d checks:  2
  Knowledge base:      yes
  MARKETING.md:        yes
  Gate scripts:        yes

  Formats:  blog, linkedin, email-lifecycle, cold-email, tiktok, meta-ads, google-ads, press, seo
  Sites:    kaicalls, buildwithkai, abp, meetkai, connorgallic, vocalscribe, mynewproduct
```

Test the full pipeline:

```bash
python scripts/harness_cli.py brief --site mynewproduct --keyword "restaurant inventory management"
```

Or via Discord:

```
!harness brief mynewproduct "restaurant inventory management"
```

## Step 7 — (Optional) Create a domain agent for OpenClaw

If you want a dedicated domain agent that runs on every heartbeat:

1. Create `workspace/agents/mynewproduct-agent.md` (or a `.j2` template):

```markdown
# MyNewProduct Domain Agent

You are the MyNewProduct domain agent. On each heartbeat, check:

## Step 1 — Check signups (last 24h)
```bash
cd /opt/cmo-analytics && source venv/bin/activate
python3 -m analytics.cli db leads --site=mynewproduct --days=1
```

If zero signups: alert.

## Step 2 — Check traffic anomalies
```bash
cmo ga4 daily --site=mynewproduct --days=7
```

If today's sessions < 50% of 7-day average: alert.

## Step 3 — Check SEO ranking changes
```bash
cmo gsc queries --site=mynewproduct --limit=10
```

Flag any keyword that dropped 5+ positions.

## Output
Return `NOTHING` if all checks pass.
Return alert string with channel ID if any check fails.
```

2. Add to `workspace/HEARTBEAT.md` spawn list:

```
sessions_spawn(task=<agents/mynewproduct-agent.md contents>, label="hb-mynewproduct", mode="run", runtime="subagent")
```

3. Add channel mapping to `workspace/AGENTS.md`:

```
| MyNewProduct | agents/mynewproduct-agent.md | #mynewproduct | 1234567890123456789 |
```

---

## Checklist

```
[ ] Added product to config.yaml with id, name, url, description, proof_points
[ ] Added env vars to .env (Supabase, GA4, GSC — whichever apply)
[ ] Ran python render_templates.py
[ ] (Optional) Created custom task handler in agent/tasks/
[ ] (Optional) Set up GA4 property + GSC property + Supabase project
[ ] (Optional) Added to SITES_CONFIG in .env
[ ] Verified with harness_cli.py status or Claude Code
[ ] (Optional) Created domain agent .md + added to HEARTBEAT.md + AGENTS.md
```

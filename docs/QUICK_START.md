# Quick Start

Two ways to use the Kai CMO Harness. Pick the one that matches your situation.

---

## Path A: Claude Code (5 minutes)

Drop the marketing knowledge base and quality gates into any project. Claude Code reads `CLAUDE.md` on startup and instantly gains access to 30+ frameworks, 17 checklists, 8 personas, and an automated quality gate pipeline.

### Step 1 — Copy four directories into your project

```
your-project/
├── CLAUDE.md                    # Copy from kai-cmo-harness root
├── knowledge/                   # Entire directory
├── harness/                     # Skill contracts, brief schema, references
└── scripts/quality_gates/       # Automated scoring and linting
```

You can copy manually or use the repo directly:

```bash
git clone https://github.com/your-org/kai-cmo-harness.git
cp -r kai-cmo-harness/CLAUDE.md your-project/
cp -r kai-cmo-harness/knowledge your-project/
cp -r kai-cmo-harness/harness your-project/
mkdir -p your-project/scripts
cp -r kai-cmo-harness/scripts/quality_gates your-project/scripts/
```

### Step 2 — Start Claude Code

```bash
cd your-project
claude
```

Claude Code reads `CLAUDE.md` automatically. It now knows:
- Which framework to load for each content type
- How to score content on the Four U's (12+/16 to pass)
- Which words are banned (Tier 1 = instant rejection)
- How to apply Algorithmic Authorship rules for SEO content

### Step 3 — Ask it to do things

**Write a blog post:**

```
Write a blog post targeting "law firm answering service" for kaicalls.com.
Target persona: Shock Absorber. Use the competitor weakness that most
AI receptionist companies charge $300-650/mo while KaiCalls is $69/mo.
```

Claude Code will:
1. Load `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`
2. Load `knowledge/checklists/content-checklist.md`
3. Check `harness/skill-contracts/blog-post.yaml` for word count and gate thresholds
4. Write the post applying all framework rules
5. Flag any banned words or quality issues

**Run a quality gate on existing content:**

```
Run the quality gates on this draft. Check Four U's score,
banned words, and SEO lint for keyword "AI receptionist for law firms".
```

**Check SEO opportunities:**

```
Look at knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md
and tell me how to optimize this page for AI Overviews.
```

**Create a cold email sequence:**

```
Write a 3-touch cold email sequence for law firm partners.
Follow harness/skill-contracts/cold-email.yaml and
harness/references/cold-email-rules.md for TCPA compliance.
```

### What you get

| Capability | How |
|------------|-----|
| SEO content | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` — 31 rules from AI Overviews analysis |
| Sales copy | `knowledge/frameworks/content-copywriting/perception-engineering.md` — 3-layer persuasion framework |
| Quality scoring | `scripts/quality_gates/four_us_score.py` — automated 1-4 scoring on Unique, Useful, Ultra-specific, Urgent |
| Banned word check | `scripts/quality_gates/banned_word_check.py` — Tier 1 instant rejection, Tier 2 flagging |
| SEO linting | `scripts/quality_gates/seo_lint.py` — keyword placement, density, sentence length, heading structure |
| AEO research | `knowledge/frameworks/aeo-ai-search/` — 12 files covering patents, citation science, Perplexity internals |
| Persona targeting | `knowledge/personas/` — 8 archetypes with pain points, language patterns, hooks |
| 7 skill contracts | `harness/skill-contracts/` — blog, LinkedIn, email, cold email, Meta ads, Google ads |

---

## Path B: OpenClaw Autonomous CMO (30 minutes)

Full autonomous operation: scheduled heartbeats, domain-specific agents, Discord integration, human-in-the-loop approval, and a self-improving pipeline that learns from content performance.

### Prerequisites

- A VPS (Ubuntu 22.04+, 4GB+ RAM recommended)
- Python 3.11+
- An OpenClaw installation
- Discord bot token
- API keys: Gemini (content generation), Google service account (GA4 + GSC), Supabase (product databases)

### Step 1 — Fork and clone

```bash
git clone https://github.com/your-org/kai-cmo-harness.git
cd kai-cmo-harness
```

### Step 2 — Configure

```bash
# Copy example files
cp config.yaml.example config.yaml
cp .env.example .env

# Edit config.yaml — add your products, Discord channels, and settings
# Edit .env — add all API keys and credentials
```

See `docs/CONFIGURATION.md` for every field explained.

### Step 3 — Render workspace templates

```bash
pip install pyyaml jinja2
python render_templates.py
```

This reads `config.yaml` and generates personalized workspace files (agent definitions, MARKETING.md, HEARTBEAT.md) with your products and channels injected.

### Step 4 — Set up analytics on the VPS

```bash
# On your VPS
mkdir -p /opt/cmo-analytics
cd /opt/cmo-analytics
python3 -m venv venv
source venv/bin/activate
pip install google-analytics-data google-auth google-search-console supabase stripe python-dotenv google-genai
```

Copy credentials and scripts:

```bash
scp .env root@your-vps:/opt/cmo-analytics/.env
scp -r scripts/ root@your-vps:/opt/cmo-analytics/scripts/
scp google-analytics-credentials.json root@your-vps:/opt/cmo-analytics/credentials/
```

See `docs/ANALYTICS_SETUP.md` for detailed setup per integration.

### Step 5 — Deploy workspace to OpenClaw

```bash
# Copy workspace files to OpenClaw's workspace directory
scp -r workspace/* root@your-vps:~/.openclaw/workspace/
scp -r knowledge/ root@your-vps:~/.openclaw/workspace/knowledge/
scp -r harness/ root@your-vps:~/.openclaw/workspace/harness/
```

### Step 6 — Start OpenClaw

```bash
# On the VPS
systemctl start openclaw
```

OpenClaw reads the workspace files on startup:
- `AGENTS.md` — agent hierarchy and Discord channel routing
- `HEARTBEAT.md` — heartbeat protocol (parallel fan-out to domain agents)
- `MARKETING.md` — content pipeline config (thresholds, frameworks, sites)
- `TOOLS.md` — available CLI tools and data sources
- `agents/*.md` — individual domain agent definitions

### Example interactions (Discord)

**Run the full content pipeline:**
```
!harness run blog kaicalls "law firm answering service"
```
Pipeline: research (GSC + GA4) -> brief -> write -> quality gate -> Discord approval post

**Generate a brief only:**
```
!harness brief kaicalls "AI receptionist for law firms"
```

**Re-gate an existing draft:**
```
!harness gate "law firm answering service"
```

**Check system status:**
```
!harness status
```

**View content performance:**
```
!harness report kaicalls
```

**Surface winning patterns:**
```
!harness patterns all
```

### What you get (beyond Path A)

| Capability | How |
|------------|-----|
| Scheduled heartbeats | Domain agents check analytics, leads, revenue, and SEO on cron |
| Discord command interface | `!harness run`, `!harness brief`, `!harness gate`, `!harness report` |
| Human-in-the-loop approval | Drafts posted to Discord with score cards; react to approve/reject |
| Self-improvement loop | 30-day performance checks -> pattern extraction -> MARKETING.md auto-update |
| Multi-product support | Each product gets its own domain agent, Discord channel, and analytics |
| Parallel agent architecture | Heartbeat spawns all domain agents simultaneously, yields for results |
| Content logging | Every published piece tracked with 30-day performance review |

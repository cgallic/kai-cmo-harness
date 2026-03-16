# Tools - Local Configuration

## OpenClaw Extensions (OCX)

Enhanced AI capabilities: `ocx <module> <command>`

| Module | Description |
|--------|-------------|
| memory | Auto-extract memories from conversations |
| rag | Index + search documents (ChromaDB + OpenAI embeddings) |
| kg | Knowledge graph for entities/relationships |
| image | DALL-E image generation |
| correct | Track corrections/mistakes |
| webhook | Event-driven triggers |

Quick examples:
```bash
ocx rag index-dir --path /opt/cmo-analytics --collection cmo
ocx rag answer --query "how do I check MRR"
ocx kg ingest --text "Connor founded KaiCalls..."
ocx correct add --wrong "X" --correct "Y"
ocx image generate --prompt "logo for startup"
```

Full docs: `/root/.openclaw/workspace/skills/ocx/SKILL.md`

---

## Memory Layer (maasv-style)

Advanced semantic memory at `/opt/cmo-analytics/memory/`:

```bash
cd /opt/cmo-analytics && source venv/bin/activate

# Add/search memories
python -m memory.cli add "fact" --category facts --subject Entity
python -m memory.cli search "query"

# Knowledge graph
python -m memory.cli entity-add "Alice" "person"
python -m memory.cli relate "Alice" "works_on" "ProjectX"

# Stats & maintenance
python -m memory.cli stats
python -m memory.cli maintain
```

Features: vector search + BM25 + knowledge graph + wisdom learning + memory consolidation.
Skill docs: `/root/.openclaw/workspace/skills/memory-layer/SKILL.md`

---

## CMO Analytics

All business data is accessible via the `cmo` command:

    cmo <module> <command> [--key=value ...]

### Modules
| Module | Description |
|--------|-------------|
| kaicalls | KaiCalls leads, calls, agents, transcripts, dashboard |
| bwk | BuildWithKai businesses, plans, generations |
| abp | Amazing Backyard Parties leads, vendors, blog |
| ga4 | Google Analytics (10 sites) - traffic, pages, sources |
| gsc | Google Search Console (9 sites) - queries, rankings, SEO opps |
| stripe_report | Stripe MRR, subscriptions, revenue, churn risk |
| daily_report | Combined reports (executive, daily, weekly) |

### Quick Examples

    cmo kaicalls leads --days=7          # This week's leads
    cmo ga4 all --days=7                 # All sites traffic
    cmo stripe_report mrr                # Current MRR
    cmo daily_report executive           # Quick status
    cmo gsc opportunities --site=kaicalls # SEO opportunities

### Lead Conversion (`leads`)
    leads analyze                        # Score all leads (30 days)
    leads hot                            # Show hot leads as JSON
    leads daily --kaicalls               # Daily digest for KaiCalls only
    leads json --kaicalls                # API output for dashboard
    leads email <lead_id>                # Generate follow-up email
    leads auto-email                     # Generate all follow-up emails (dry run)

Dashboard: https://cg.meetkai.xyz/leads.html

## SSH Hosts
- kai-cmo VPS: 89.167.60.171 (this server)
- MDI server: 77.42.43.0

## Domains
- meetkai.xyz / www.meetkai.xyz -> landing page (/var/www/meetkai/)
- cg.meetkai.xyz -> OpenClaw dashboard (/var/www/cg/)
- dash.meetkai.xyz -> business dashboard (/var/www/dash/) [placeholder]

## Google Workspace
- Account: your-email@domain.com
- GOG keyring password: YOUR_GOG_PASSWORD

---

## Patent Scanner

Competitive intelligence on big tech patent filings:

```bash
# List tracked patents
patents list
patents list --ai-only
patents list --company Google

# Add a patent manually
patents add US12536233B1 "AI Landing Pages" "Google" --notes "Why it matters"

# Format for Discord
patents discord

# Run scanner (scans RSS + Google Patents)
cd /opt/cmo-analytics && source venv/bin/activate
python patent-scanner/scanner.py --ai-only --format full --save
```

**Watched companies:** Google, Apple, Microsoft, Meta, Amazon, NVIDIA, OpenAI, Anthropic, Salesforce, Adobe, Alibaba, ByteDance, Tesla, Palantir, IBM, Oracle

Skill docs: `/root/.openclaw/workspace/skills/patent-scanner/SKILL.md`

---

## Marketing Knowledge RAG

Search the full marketing knowledge base (83 files, 1000+ chunks) via semantic search:

```bash
# Search for relevant content
ocx rag search --query "how to write headlines" --collection marketing-knowledge

# Get AI-generated answer from knowledge base
ocx rag answer --query "what are the Four U's scoring criteria" --collection marketing-knowledge
```

Collection: `marketing-knowledge`
Source: `/root/.openclaw/workspace/knowledge/` (83 markdown files)
Covers: frameworks, checklists, channels, personas, playbooks, design guides, AEO research, examples

---

## KaiCalls Outbound

Make TCPA-compliant outbound calls via KaiCalls API:

```bash
kaicalls-call +19085551234           # Call with default agent
kaicalls-call +19085551234 --agent UUID  # Specific agent
```

Auto-checks TCPA hours (8 AM - 9 PM recipient local time).

Skill: `/root/.openclaw/workspace/skills/kaicalls-outbound/SKILL.md`

# Knowledge Cloner

Automated expert knowledge extraction pipeline. Converts YouTube channels, podcasts, articles, and GitHub repositories into structured, actionable knowledge bases using LLM-powered extraction, distillation, and synthesis.

## Quick Start

```bash
# 1. Set API keys in .env
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env

# 2. Initialize an expert project
python -m scripts.knowledge_cloner init "Alex Hormozi" --domain "Business"

# 3. Add sources
python -m scripts.knowledge_cloner discover alex-hormozi \
    --youtube https://www.youtube.com/@AlexHormozi/videos --limit 20

# 4. Run the full pipeline
python -m scripts.knowledge_cloner pipeline alex-hormozi

# 5. Check results
ls clients/Connor_Gallic/knowledge/alex-hormozi/output/
```

## Pipeline Phases

```
┌─────────────┐    ┌───────────────┐    ┌────────────┐    ┌──────────────┐
│  DISCOVERY   │───▶│ TRANSCRIPTION │───▶│ EXTRACTION │───▶│ DISTILLATION │
│  (Phase 1)   │    │  (Phase 2a)   │    │ (Phase 2b) │    │  (Phase 3)   │
│              │    │               │    │            │    │              │
│ YouTube      │    │ Free captions │    │ LLM prompt │    │ 5 category   │
│ Podcasts     │    │ yt-dlp subs   │    │ per source │    │ passes       │
│ Articles     │    │ Gemini audio  │    │            │    │              │
│ GitHub repos │    │ git clone     │    │            │    │              │
│ Local files  │    │ Web scrape    │    │            │    │              │
└─────────────┘    └───────────────┘    └────────────┘    └──────┬───────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│   QUALITY    │◀──│ OPERATIONALIZATION│◀──│     SYNTHESIS         │
│  (Phase 6)   │    │    (Phase 5)     │    │     (Phase 4)        │
│              │    │                  │    │                      │
│ 5 quality    │    │ Quick reference  │    │ Novelty analysis     │
│ gates        │    │ Decision trees   │    │ Hidden curriculum    │
│ PASS/FAIL    │    │ Checklists       │    │ Gap analysis         │
│              │    │ AI prompts       │    │ Real thesis           │
└─────────────┘    └──────────────────┘    └──────────────────────┘
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `init` | Create new expert project | `init "Expert Name" --domain "Marketing"` |
| `list` | List all projects | `list` |
| `status` | Show pipeline status | `status alex-hormozi` |
| `sources` | Show source inventory | `sources alex-hormozi` |
| `discover` | Add sources | `discover alex-hormozi --youtube URL` |
| `transcribe` | Convert sources to text | `transcribe alex-hormozi --limit 10` |
| `extract` | LLM knowledge extraction | `extract alex-hormozi` |
| `distill` | Merge into 5 structured docs | `distill alex-hormozi` |
| `synthesize` | Cross-source analysis | `synthesize alex-hormozi` |
| `operationalize` | Generate templates & prompts | `operationalize alex-hormozi` |
| `quality` | Run quality gates | `quality alex-hormozi` |
| `cost` | Estimate remaining costs | `cost alex-hormozi` |
| `pipeline` | Run all phases sequentially | `pipeline alex-hormozi` |

All API-calling commands support: `--dry-run`, `--max-requests N`, `--max-cost N.NN`, `--model MODEL`

## Source Types

### YouTube Channels

```bash
python -m scripts.knowledge_cloner discover alex-hormozi \
    --youtube https://www.youtube.com/@AlexHormozi/videos \
    --limit 50
```

Discovers all videos via `yt-dlp`. Auto-prioritizes by duration:
- **HIGH**: >20 minutes (long-form, most knowledge-dense)
- **MEDIUM**: 5-20 minutes
- **LOW**: <5 minutes (shorts, clips)

Transcription cascade (cheapest first):
1. `youtube-transcript-api` — free, instant
2. `yt-dlp` subtitle download — free, slower
3. Gemini video URL — ~$0.01-0.03 (Google servers access YouTube natively)
4. Audio download + Gemini — ~$0.01-0.03 (last resort)

### Podcasts

```bash
python -m scripts.knowledge_cloner discover alex-hormozi \
    --podcast-rss https://feeds.example.com/podcast.xml
```

Parses RSS feed, extracts audio enclosure URLs. All podcasts default to HIGH priority.

### Articles

```bash
python -m scripts.knowledge_cloner discover alex-hormozi \
    --url https://example.com/article --type article
```

Scraped with BeautifulSoup. Extracts `<article>`, `<main>`, or `div.content` selectors.

### GitHub Repositories

```bash
# Full URL
python -m scripts.knowledge_cloner discover alex-hormozi \
    --github-repo https://github.com/TIGER-AI-Lab/TheoremExplainAgent

# Short form
python -m scripts.knowledge_cloner discover alex-hormozi \
    --github-repo showlab/Code2Video
```

Extracts procedural knowledge from codebases. "Transcription" phase:
1. Shallow `git clone --depth=1`
2. Generates directory tree (3 levels deep)
3. Reads key files: README, CLAUDE.md, SKILL.md, configs, main scripts
4. Scans .py/.ts/.js/.md files (200k char budget, ~50k tokens)

Uses a specialized extraction prompt (`REPO_EXTRACTION_PROMPT`) that extracts:
- **Skills** in formal S=(C,π,T,R) four-tuple format
- Architecture decisions with rationale
- Configuration patterns, error handling, security patterns
- Dependency maps

### Local Files

```bash
python -m scripts.knowledge_cloner discover alex-hormozi \
    --file /path/to/transcript.txt --type xspace
```

Imported directly as already-transcribed. Skips transcription phase.

### Manual URLs

```bash
python -m scripts.knowledge_cloner discover alex-hormozi \
    --url https://example.com/whatever --type book --priority HIGH
```

Supported types: `youtube`, `podcast`, `article`, `xspace`, `book`, `course`, `thread`, `file`, `repo`

## Output Structure

```
clients/Connor_Gallic/knowledge/{expert-slug}/
├── progress.json              # Pipeline state (sources, phases completed)
├── source-map.md              # Auto-generated source inventory table
├── raw/
│   ├── transcripts/           # Phase 2a output (markdown per source)
│   ├── articles/              # Scraped article HTML (if cached)
│   ├── audio/                 # Temporary audio downloads (cleaned up)
│   └── repos/                 # Cloned repositories
│       └── repo_{slug}/
│           └── checkout/      # Shallow git clone
├── extractions/               # Phase 2b output (one per source)
│   ├── yt_abc123_extract.md
│   ├── art_my-article_extract.md
│   └── repo_owner-repo_extract.md
├── distilled/                 # Phase 3 output (5 structured docs)
│   ├── {slug}-frameworks.md
│   ├── {slug}-tactics.md
│   ├── {slug}-edges.md
│   ├── {slug}-principles.md
│   └── {slug}-anti-patterns.md
├── synthesis/                 # Phase 4 output (4 cross-source analyses)
│   ├── novelty-pass.md
│   ├── hidden-curriculum.md
│   ├── gap-analysis.md
│   └── real-thesis.md
└── output/                    # Phase 5-6 output (operational docs)
    ├── quick-reference.md     # 1-page cheat sheet
    ├── decision-trees.md      # When to use what
    ├── checklists.md          # Step-by-step execution
    ├── ai-prompts.md          # Prompt templates per framework
    └── quality-report.md      # Phase 6: 5-gate evaluation
```

## Extraction Format

### For People (YouTube, Podcasts, Articles)

Each source extraction contains 12 sections:

| Section | What It Captures |
|---------|-----------------|
| **Frameworks** | Systems, models, processes — with purpose, components, steps, conditions |
| **Edges** | Non-obvious insights — conventional view vs expert view + evidence |
| **Tactics** | Actionable techniques — what, why, how, tools, failure modes |
| **Principles** | Durable beliefs — stated as, behavior it drives, repeat signal |
| **Anti-Patterns** | Warnings — the trap, why it fails, the fix |
| **Evolution Signals** | How their thinking changed over time |
| **Influence Signals** | Who they cite, borrow from, argue against |
| **Tacit Knowledge** | What they assume without explaining |
| **Boundary Signals** | What they consistently refuse or reject |
| **Context Dependencies** | Conditions needed for advice to work |
| **Gaps** | What's missing or conspicuously underweighted |
| **Top 3 Insights** | Highest-signal takeaways from this source |

### For Repositories

Repo extraction adds 6 code-specific sections:

| Section | What It Captures |
|---------|-----------------|
| **Skills** | Reusable procedural patterns in S=(C,π,T,R) four-tuple format |
| **Architecture Decisions** | What was decided, context, alternatives, consequences |
| **Dependency Map** | External deps and their purposes |
| **Configuration Patterns** | What's parameterized vs hardcoded |
| **Error Handling** | Retry logic, fallbacks, graceful degradation |
| **Security Patterns** | Auth, validation, secret management |

## Models & Costs

### Available Models

| Key | Model | Cost (per 1M tokens) | Best For |
|-----|-------|---------------------|----------|
| `qwen-plus` | Qwen 3.5 Plus | $0.26 in / $1.56 out | Default — bulk extraction |
| `qwen-max` | Qwen 3 Max | $1.20 in / $6.00 out | Synthesis, quality gates |
| `qwen-coder` | Qwen 3 Coder | $0.22 in / $1.00 out | Structured extraction |
| `gemini-flash` | Gemini 2.0 Flash | $0.10 in / $0.40 out | Cheapest fallback |
| `claude-sonnet` | Claude Sonnet 4.6 | $3.00 in / $15.00 out | Highest quality |

All models accessed via OpenRouter. Override per-phase with `--model`.

### Default Phase Models

| Phase | Model | Reason |
|-------|-------|--------|
| Extraction | qwen-plus | Good quality, cheap for bulk |
| Distillation | qwen-plus | Merge & structure |
| Synthesis | qwen-max | Novelty detection needs depth |
| Operationalization | qwen-plus | Template generation |
| Quality | qwen-max | Gate evaluation needs reasoning |

### Cost Estimate (40-source project)

| Phase | Cost |
|-------|------|
| Transcription | ~$0.60 (20% Gemini fallback) |
| Extraction | ~$2.00 |
| Distillation | ~$0.15 |
| Synthesis | ~$0.30 |
| Operationalization | ~$0.15 |
| Quality | ~$0.30 |
| **Total** | **~$3.50** |

Use `python -m scripts.knowledge_cloner cost {slug}` for project-specific estimates.

## Configuration

### Environment Variables

```bash
# Required (one of these)
OPENROUTER_API_KEY=sk-or-v1-...    # Primary — works for all models

# Optional
GEMINI_API_KEY=AIza...              # Fallback for audio transcription
ANTHROPIC_API_KEY=sk-ant-...        # Direct Claude access (rarely needed)
KNOWLEDGE_CLONER_DATA_DIR=/path/... # Override output directory
```

Place in `.env` at project root or `scripts/.env`.

### External Tools

| Tool | Required For | Install |
|------|-------------|---------|
| `yt-dlp` | YouTube discovery & transcription | `pip install yt-dlp` |
| `git` | Repository cloning | System package |
| `youtube-transcript-api` | Free YouTube captions | `pip install youtube-transcript-api` |
| `feedparser` | Podcast RSS parsing | `pip install feedparser` |
| `beautifulsoup4` | Article scraping | `pip install beautifulsoup4` |
| `httpx` | Async HTTP | `pip install httpx` |
| `python-dotenv` | .env loading | `pip install python-dotenv` |

## Safety Features

- **Cost limits**: Hard cap on API spend (default $5.00, override with `--max-cost`)
- **Request limits**: Hard cap on API calls (default 100, override with `--max-requests`)
- **Rate limiting**: 2-second minimum between API calls
- **Dry-run mode**: Preview all actions without making API calls (`--dry-run`)
- **Confirmation prompts**: User must approve each expensive phase
- **Resumable**: Re-run any phase — already-completed sources are skipped
- **Phase idempotency**: Phases track completion in `progress.json`

## Examples

### Extract from a YouTube channel

```bash
python -m scripts.knowledge_cloner init "Declan O'Reilly" --domain "Marketing"
python -m scripts.knowledge_cloner discover declan-oreilly \
    --youtube https://www.youtube.com/@DeclanOReillyMarketing/videos
python -m scripts.knowledge_cloner pipeline declan-oreilly --max-cost 10.00
```

### Extract from a GitHub repository

```bash
python -m scripts.knowledge_cloner init "TheoremExplainAgent" --domain "AI Education"
python -m scripts.knowledge_cloner discover theoremexplainagent \
    --github-repo TIGER-AI-Lab/TheoremExplainAgent
python -m scripts.knowledge_cloner transcribe theoremexplainagent
python -m scripts.knowledge_cloner extract theoremexplainagent
```

### Mix sources for one expert

```bash
python -m scripts.knowledge_cloner init "Naval Ravikant" --domain "Philosophy"
python -m scripts.knowledge_cloner discover naval-ravikant \
    --youtube https://www.youtube.com/@NavalR/videos --limit 30
python -m scripts.knowledge_cloner discover naval-ravikant \
    --podcast-rss https://nav.al/podcast/feed
python -m scripts.knowledge_cloner discover naval-ravikant \
    --url https://nav.al/almanack --type article --priority HIGH
python -m scripts.knowledge_cloner discover naval-ravikant \
    --github-repo navalmanack/navalmanack
python -m scripts.knowledge_cloner pipeline naval-ravikant
```

### Run phases individually with cost control

```bash
# Check what transcription will cost
python -m scripts.knowledge_cloner transcribe naval-ravikant --dry-run

# Transcribe first 5 sources only
python -m scripts.knowledge_cloner transcribe naval-ravikant --limit 5

# Extract with a cheaper model
python -m scripts.knowledge_cloner extract naval-ravikant --model gemini-flash

# Synthesize with the best model
python -m scripts.knowledge_cloner synthesize naval-ravikant --model claude-sonnet
```

## Architecture

### Data Flow

```
Sources (URLs)
    │
    ▼
progress.json  ◄──── Single source of truth for pipeline state
    │
    ├──▶ raw/transcripts/*.md    ← Phase 2a (text per source)
    │
    ├──▶ extractions/*_extract.md ← Phase 2b (knowledge per source)
    │
    ├──▶ distilled/*.md           ← Phase 3  (5 merged category docs)
    │
    ├──▶ synthesis/*.md           ← Phase 4  (4 cross-source analyses)
    │
    └──▶ output/*.md              ← Phase 5-6 (4 operational docs + quality report)
```

### Module Dependencies

```
cli.py ──▶ config.py
  │        types.py
  │        utils.py
  │
  ├──▶ discovery.py ──▶ types, utils
  ├──▶ transcription.py ──▶ types, utils, config, prompts
  ├──▶ extraction.py ──▶ types, utils, config, prompts
  ├──▶ distillation.py ──▶ types, utils, config, prompts
  ├──▶ synthesis.py ──▶ types, utils, config, prompts
  ├──▶ operationalization.py ──▶ types, utils, config, prompts
  └──▶ quality.py ──▶ types, utils, config, prompts
```

### Key Design Decisions

1. **OpenRouter as primary API** — single key, all models, cheaper than direct APIs
2. **Cascade transcription** — always try free methods before paid
3. **Separate extraction vs distillation** — extract per-source (parallelizable), then merge
4. **Existing KB comparison** — synthesis compares against `frameworks/` for novelty
5. **Git-based state** — `progress.json` is human-readable and version-controllable
6. **Cost transparency** — every phase shows estimated cost before executing
7. **Repo extraction via four-tuple** — skills extracted as S=(C,π,T,R) per arXiv:2603.11808

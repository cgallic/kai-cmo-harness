---
description: Produce full videos from script to render - resume projects or create new with AI voiceovers, music, and automated editing
---

# Video Production

Full video production pipeline. Extends `/kai-video` script generation with rendering capabilities.

## Quick Start

**New project:**
```
/kai-video-produce new --template product-demo --brand kaicalls
```

**Resume project:**
```
/kai-video-produce resume kaicalls-demo-v1
```

**List projects:**
```
/kai-video-produce list
```

---

## Entry Logic

### Step 0: First-Time Setup Check

If no `.env` exists or no cloud GPU configured:

```
💡 Tip: Run /video-setup to configure AI voiceovers and music.
   Takes ~5 minutes, most features free. Skip for now? You can
   still create videos with just Node.js.
```

Don't block — proceed immediately.

---

### Step 1: Scan Existing Projects

```bash
# Find all video projects
glob workspace/video/projects/*/project.json

# For each:
- Read project.json
- Scan filesystem for assets (public/demos/*, public/audio/*)
- Reconcile status (intent vs reality)
- Calculate health (ready/blocked/complete)
- Sort by last updated
```

---

### Step 2: Present Options

**No projects:**
```
No video projects found. Let's create one!

Available templates:
  1. product-demo - Marketing videos (problem/solution/demo/CTA)
  2. explainer - Educational content (overview/sections/recap)
  3. demo-walkthrough - Screen recordings with narration
  4. social-short - 15-60s vertical for TikTok/Reels/Shorts

Which template?
```

**One project:**
```
Found: **kaicalls-demo-v1** (product-demo)
  Phase: assets
  Progress: 2/4 demos recorded
  Last worked: 2 hours ago

  → Resume this project
  → Start a new project
```

**Multiple projects:**
```
Found 3 video projects:

  1. **kaicalls-demo-v1** (product-demo)
     Phase: assets - 2/4 demos recorded ⏸️
     Last worked: 2 hours ago

  2. **tropibot-launch** (product-demo)
     Phase: audio - voiceover needed 🎙️
     Last worked: yesterday

  3. **tutorial-basics** (explainer)
     ✅ Complete - rendered 1 week ago

Which project? (or 'new')
```

---

## Resume Flow

**When resuming a project:**

### Step 1: Load State

```python
# Read project metadata
project = read_json('project.json')
script = read_md('VOICEOVER-SCRIPT.md')

# Scan filesystem
actual_assets = {
    'demos': glob('public/demos/*'),
    'audio': glob('public/audio/*'),
    'images': glob('public/images/*')
}

# Compare to expected
expected_assets = [
    scene['visual']['asset'] 
    for scene in project['scenes'] 
    if scene['visual']['type'] in ['demo', 'image']
]
```

### Step 2: Reconcile Intent vs Reality

```python
for scene in project['scenes']:
    asset_path = scene.get('visual', {}).get('asset')
    
    if asset_path:
        # Expected asset
        if asset_path in actual_assets:
            # Asset present but status wrong
            if scene['status'] == 'asset-needed':
                scene['status'] = 'asset-present'
        else:
            # Asset missing but status says present
            if scene['status'] in ['asset-present', 'ready']:
                scene['status'] = 'asset-missing'
                flag_issue(f"Scene {scene['id']}: {asset_path} missing")
```

### Step 3: Present Current State

```markdown
## Resuming: kaicalls-demo-v1

**Template:** product-demo | **Brand:** kaicalls | **Phase:** assets

### Scenes

| # | Scene | Type | Visual | Status |
|---|-------|------|--------|--------|
| 1 | Title | title | slide | ✅ Ready |
| 2 | Problem | problem | slide | ✅ Ready |
| 3 | Demo: Call Flow | demo | demos/call-flow.mp4 | ✅ Recorded |
| 4 | Demo: Voicemail | demo | demos/voicemail.mp4 | ⬜ Needs recording |
| 5 | Stats | stats | slide | ✅ Ready |
| 6 | CTA | cta | slide | ✅ Ready |

### Audio

- Voiceover: ⬜ Not generated (script ready)
- Music: Optional background

### Next Actions

**Priority:** Record voicemail demo (Scene 4)
  → /record-demo --url https://app.kaicalls.com/voicemail

**Then:** Generate voiceover
  → /generate-voiceover --project kaicalls-demo-v1

**Finally:** Review and render
  → /scene-review --project kaicalls-demo-v1

Ready to record the voicemail demo?
```

### Step 4: Update Tracking

```python
# Update project.json with reconciled state
project['updated'] = now()
project['sessions'].append({
    'date': today(),
    'phase': project['phase'],
    'summary': 'Resumed project, reconciled assets'
})

write_json('project.json', project)
```

### Step 5: Regenerate Context

```python
# Auto-generate CLAUDE.md for instant context
generate_claude_md(project, actual_assets)
```

**CLAUDE.md structure:**
```markdown
# Project: kaicalls-demo-v1

**Template:** product-demo | **Brand:** kaicalls | **Phase:** assets
**Last Updated:** 5 minutes ago

## Current Status

3 of 4 demos recorded. One remaining (voicemail flow). After that, 
generate voiceover and move to review phase.

## Scenes

[Scene table from above]

## Audio

[Audio status from above]

## Next Actions

[Priority actions from above]

## Quick Commands

```bash
cd workspace/video/projects/kaicalls-demo-v1
npm run studio    # Preview in Remotion Studio
npm run render    # Render final MP4
```

## Session History

- 2026-03-28 14:00: Created project, defined scenes (planning)
- 2026-03-28 15:30: Recorded 3 demos (assets)
- 2026-03-28 17:45: Resumed project (assets)

---
*Auto-generated from project.json. Do not edit manually.*
```

---

## New Project Flow

**When creating a new project:**

### Phase 1: Template & Brand Selection

**Template Selection:**
```markdown
Which template would you like to use?

| Template | Best For | Scene Types | Avg Length |
|----------|----------|-------------|------------|
| product-demo | Marketing, launches | title, problem, solution, demo, CTA | 60-90s |
| explainer | Educational content | title, overview, sections, recap | 3-5min |
| demo-walkthrough | Screen recordings | title, demo sections, summary | 2-4min |
| social-short | TikTok/Reels/Shorts | hook, body, CTA | 15-60s |
```

**Brand Selection:**
```markdown
Which brand profile?

  1. kaicalls - #3B82F6 (blue tech)
  2. buildwithkai - #10B981 (green modern)
  3. awesomebackyardparties - #F59E0B (orange playful)
  4. meetkai - #8B5CF6 (purple professional)
  5. Create new brand → /kai-brand
```

**Project Name:**
```
What should we call this project?
(Becomes folder name, e.g., "demo-v2" → workspace/video/projects/demo-v2/)
```

### Phase 2: Content Gathering

**Check for existing content:**
```python
# Look for related content
marketing_md = read_if_exists('MARKETING.md')
blog_posts = glob('content/blog/**/*.md')
product_docs = glob('docs/**/*.md')
```

**Ask about content:**
```markdown
What should this video cover? You can:
- Paste release notes / product description
- Point to a blog post or doc
- Describe what you want to show
- Provide a URL (we'll fetch it)

Examples:
  "Our new AI call handling feature"
  "content/blog/kaicalls-v2-launch.md"
  "https://kaicalls.com/blog/new-features"
  "Show how users set up their first call agent"
```

**If URL:**
```python
content = web_fetch(url)
summary = summarize(content)
present_summary(summary)
```

**Always ask:**
- "What's the main message?"
- "Who's the target audience?"
- "Any specific features/benefits to highlight?"
- "Anything to skip or de-emphasize?"

### Phase 3: Scene Planning

**Step 1: Propose Scene Breakdown**

```python
# Analyze content
main_points = extract_key_points(content, audience, goal)

# Map to scene types based on template
scenes = generate_scene_plan(main_points, template)
```

**Present proposal:**
```markdown
Based on your input, here's a suggested scene breakdown:

  1. **Title** (5s)
     [SLIDE] "Introducing KaiCalls 2.0"
     Narration: "Introducing KaiCalls 2.0..."

  2. **Problem** (10s)
     [SLIDE] "73% of leads call after hours"
     Narration: "Most businesses miss..."

  3. **Solution** (10s)
     [SLIDE] "AI-powered call answering"
     Narration: "KaiCalls answers every call..."

  4. **Demo: Call Handling** (20s)
     [DEMO] Screen recording of call flow
     Narration: "Watch how it handles a real call..."

  5. **Demo: Voicemail** (15s)
     [DEMO] Screen recording of voicemail
     Narration: "Intelligent voicemail transcription..."

  6. **Stats** (10s)
     [SLIDE] "3 features, 12 improvements"
     Narration: "This release includes..."

  7. **CTA** (5s)
     [SLIDE] "Try free for 14 days"
     Narration: "Start your free trial..."

  **Estimated total:** ~75 seconds

Want to adjust any scenes?
```

**Step 2: Iterate on Plan**

Allow user to:
- Add/remove scenes
- Reorder
- Adjust timing
- Change visual types (slide → demo, etc.)
- Refine narration

**Step 3: Confirm Each Scene**

For each scene, lock in:
- **Type:** title / problem / solution / demo / etc.
- **Visual:** slide / demo / image / video
- **Duration:** Seconds
- **Narration:** Draft script text
- **Status:** ready (slide) / asset-needed (demo/image)

### Phase 4: Project Creation

**Step 1: Copy Template**
```bash
cp -r harness/templates/video/{template}/ \\
      workspace/video/projects/{name}/
```

**Step 2: Generate project.json**
```json
{
  "name": "kaicalls-demo-v1",
  "template": "product-demo",
  "brand": "kaicalls",
  "created": "2026-03-28T15:00:00Z",
  "updated": "2026-03-28T15:00:00Z",
  "phase": "planning",
  "scenes": [
    {
      "id": 1,
      "type": "title",
      "duration": 5,
      "visual": {
        "type": "slide",
        "content": "Introducing KaiCalls 2.0"
      },
      "narration": "Introducing KaiCalls 2.0...",
      "status": "ready"
    },
    {
      "id": 4,
      "type": "demo",
      "duration": 20,
      "visual": {
        "type": "demo",
        "asset": "demos/call-handling.mp4"
      },
      "narration": "Watch how it handles a real call...",
      "status": "asset-needed"
    }
  ],
  "audio": {
    "voiceover": {
      "file": "audio/voiceover.mp3",
      "status": "needed"
    },
    "music": {
      "file": "audio/background.mp3",
      "status": "optional"
    }
  },
  "estimates": {
    "totalDurationSeconds": 75,
    "sceneCount": 7,
    "demosNeeded": 2
  },
  "sessions": [
    {
      "date": "2026-03-28",
      "phase": "planning",
      "summary": "Project created, scenes defined"
    }
  ]
}
```

**Step 3: Generate VOICEOVER-SCRIPT.md**
```markdown
# KaiCalls 2.0 Demo - Voiceover Script

## Scene 1: Title (5s)

Introducing KaiCalls 2.0 — AI-powered call answering that never misses a lead.

[VISUAL: Title card with KaiCalls logo, "2.0" prominent]

## Scene 2: Problem (10s)

Most businesses miss 73% of leads because they call after hours. Every missed 
call is lost revenue.

[VISUAL: Stat "73% of leads call after hours" with icon]

## Scene 3: Solution (10s)

KaiCalls answers every call, 24/7. Natural conversations, intelligent routing, 
automatic follow-ups.

[VISUAL: "AI-powered call answering" with product icon]

## Scene 4: Demo - Call Handling (20s)

Watch how it handles a real call. The caller asks about pricing, and KaiCalls 
provides accurate information instantly.

[VISUAL: Screen recording of call flow in action]
[ASSET NEEDED: demos/call-handling.mp4]

## Scene 5: Demo - Voicemail (15s)

If the caller prefers to leave a message, KaiCalls transcribes it, extracts 
key details, and sends you a summary.

[VISUAL: Screen recording of voicemail transcription]
[ASSET NEEDED: demos/voicemail.mp4]

## Scene 6: Stats (10s)

This release includes 3 major features and 12 improvements based on your feedback.

[VISUAL: Stats display "3 features • 12 improvements"]

## Scene 7: CTA (5s)

Try KaiCalls free for 14 days. No credit card required.

[VISUAL: "Start Free Trial" with URL kaicalls.com]

---

**Total Duration:** ~75 seconds
**Demos Needed:** 2 (call-handling, voicemail)
**Audio Provider:** Qwen3-TTS (Ryan voice)
**Music:** Optional corporate background
```

**Step 4: Generate Brand Config**
```python
# Read brand.json
brand_data = read_json(f'brands/{brand}/brand.json')

# Generate TypeScript config
generate_brand_ts(brand_data, f'projects/{name}/src/config/brand.ts')
```

**Step 5: Copy Brand Assets**
```bash
cp brands/{brand}/assets/* projects/{name}/public/images/
```

**Step 6: Install Dependencies**
```bash
cd workspace/video/projects/{name}
npm install
```

**Step 7: Generate CLAUDE.md**
```python
generate_claude_md(project, {})
```

### Phase 5: Asset Guidance

**After project creation, actively guide:**

```markdown
Project created! 📹

**Location:** workspace/video/projects/kaicalls-demo-v1/

### Assets Needed

You have 2 demos to record:

  ⬜ **Scene 4:** Call handling demo (20s)
     Shows: Caller asks about pricing, KaiCalls responds
     URL: https://app.kaicalls.com
     Command: /record-demo --project kaicalls-demo-v1 --scene 4

  ⬜ **Scene 5:** Voicemail demo (15s)
     Shows: Caller leaves message, transcription appears
     URL: https://app.kaicalls.com/voicemail
     Command: /record-demo --project kaicalls-demo-v1 --scene 5

**Start with Scene 4?**

(Or say "skip" to move to next phase and record later)
```

**After each asset:**
```python
# Update scene status
scene['status'] = 'asset-present'
scene['visual']['asset'] = f'demos/{filename}.mp4'

# Check if phase should advance
if all_assets_present(project):
    project['phase'] = 'review'
    suggest_next_command('/scene-review')
else:
    suggest_next_asset()
```

---

## Phase Transitions

**Automatic phase advancement:**

| Condition | From → To | Next Command |
|-----------|-----------|--------------|
| All scenes defined, script written | planning → assets | /record-demo |
| All assets present | assets → review | /scene-review |
| Review approved | review → audio | /generate-voiceover |
| Voiceover generated | audio → editing | /design (optional) |
| User initiates render | editing → rendering | npm run render |
| Render complete | rendering → complete | [done] |

**Never skip review phase** — visual verification mandatory.

---

## Integration Points

### /record-demo (asset creation)

**After recording:**
```python
# Move file to project
shutil.move(recording, f'projects/{name}/public/demos/{filename}.mp4')

# Update scene
scene['status'] = 'asset-present'
scene['visual']['asset'] = f'demos/{filename}.mp4'

# Add session
project['sessions'].append({
    'date': today(),
    'phase': 'assets',
    'summary': f'Recorded {filename}'
})

# Save & regenerate context
write_json('project.json', project)
generate_claude_md(project)
```

### /scene-review (visual verification)

**Delegate when ready:**
```python
if project['phase'] == 'review':
    suggest('/scene-review --project {name}')
```

**After review complete:**
```python
# /scene-review updates project
project['phase'] = 'audio'
project['sessions'].append({
    'date': today(),
    'phase': 'review',
    'summary': 'Scenes reviewed and approved'
})
```

### /generate-voiceover (audio creation)

**After generation:**
```python
# Update audio status
project['audio']['voiceover']['status'] = 'present'
project['audio']['voiceover']['provider'] = 'qwen3'
project['audio']['voiceover']['speaker'] = 'Ryan'

# Advance phase
project['phase'] = 'editing'

# Add session
project['sessions'].append({
    'date': today(),
    'phase': 'audio',
    'summary': 'Generated voiceover (Qwen3-TTS)'
})
```

---

## Key Principles

1. **Scan filesystem first** — Always know what exists before asking
2. **Reconcile on every resume** — Intent (project.json) vs reality (files)
3. **Track all sessions** — Help Claude understand context across days
4. **Auto-generate CLAUDE.md** — Always-current human+AI readable status
5. **Guide next action** — Never leave user wondering what's next
6. **Stay flexible** — Handle partial states, missing files, manual edits
7. **Quality gates** — Review before render, verify after

---

## Output Files

```
workspace/video/projects/{name}/
├── project.json              # Project state (machine-readable)
├── CLAUDE.md                 # Context summary (human+AI readable)
├── VOICEOVER-SCRIPT.md       # Full narration script
├── src/                      # Remotion source code
│   ├── Root.tsx              # Main composition
│   ├── scenes/               # Scene components
│   └── config/               # Timing, brand, assets
├── public/
│   ├── demos/                # Screen recordings
│   ├── audio/                # Voiceovers, music
│   ├── images/               # Screenshots, graphics
│   └── videos/               # External clips
├── out/
│   └── {name}.mp4            # Rendered video
└── package.json              # Dependencies
```

---

## Quick Reference

**Common workflows:**

```bash
# New project
/kai-video-produce new --template product-demo --brand kaicalls

# Resume project
/kai-video-produce resume kaicalls-demo-v1

# List all projects
/kai-video-produce list

# Project status
/kai-video-produce status kaicalls-demo-v1

# Archive completed
/kai-video-produce archive kaicalls-demo-v1
```

**Within project:**

```bash
cd workspace/video/projects/{name}

# Preview
npm run studio

# Render
npm run render

# Render options
npm run render -- --quality=low --resolution=720p
```

---

## Example Session Flow

**Session 1: Planning (30min)**
```
/kai-video-produce new --template product-demo --brand kaicalls
→ Select template, define scenes, create project
→ Output: project.json, VOICEOVER-SCRIPT.md, CLAUDE.md
→ Phase: planning → assets
```

**Session 2: Asset Creation (1-2 hours)**
```
/kai-video-produce resume kaicalls-demo-v1
→ Record demos with /record-demo
→ Add external images if needed
→ Phase: assets → review
```

**Session 3: Review (30min)**
```
/scene-review --project kaicalls-demo-v1
→ Visual verification in Remotion Studio
→ Adjust timing, fix issues
→ Phase: review → audio
```

**Session 4: Audio (30min)**
```
/generate-voiceover --project kaicalls-demo-v1
→ AI voiceover generated
→ Optional: Add background music
→ Phase: audio → editing
```

**Session 5: Final Polish (30min)**
```
/design --scene 3  # Optional design refinement
npm run studio     # Final preview
npm run render     # Render MP4
→ Phase: editing → rendering → complete
```

**Total:** 3-5 hours spread across multiple sessions

---

## Troubleshooting

**"Project not found":**
- Check workspace/video/projects/ directory
- Verify project name spelling
- List all: /kai-video-produce list

**"Asset reconciliation failed":**
- Manual file moves not tracked in project.json
- Re-run resume to reconcile
- Check file paths in project.json

**"Phase stuck":**
- Check CLAUDE.md for blockers
- Review project.json scene statuses
- Manually advance if needed (edit project.json, update phase)

**"CLAUDE.md out of date":**
- Regenerated automatically on resume
- Force regenerate: /kai-video-produce refresh

---

**This command orchestrates the entire video production lifecycle. It's the entry point that delegates to specialized commands (/record-demo, /scene-review, /generate-voiceover) while maintaining state across sessions.**

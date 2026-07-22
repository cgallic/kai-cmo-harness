# Video Production Integration

**Added:** March 28, 2026  
**Source:** claude-code-video-toolkit by Digital Samba  
**Status:** Integrated and enhanced for marketing use cases

---

## What Was Added

### 1. Enhanced Video Production Skill

**Location:** `harness/skills/kai-video-production/SKILL.md`

**Combines two capabilities:**
- **Script generation** (existing kai-video skill)
  - Platform-optimized scripts (TikTok, YouTube, Reels)
  - Hook formulas, quality gates
  - Algorithm-aware content
  
- **Video production** (new from video toolkit)
  - AI-powered rendering with Remotion
  - AI voiceovers (Qwen3-TTS / ElevenLabs)
  - AI music generation (ACE-Step)
  - Browser-based demo recording (Playwright)
  - Multi-session project tracking
  - Intent vs reality reconciliation

---

### 2. Production Commands

**New commands:**

#### `/kai-video-produce`
**Location:** `harness/commands/kai-video-produce.md`

Full video production pipeline:
- Create new projects from templates
- Resume multi-session projects
- Track state across sessions
- Automatic reconciliation of assets

**Usage:**
```bash
# New project
/kai-video-produce new --template product-demo --brand kaicalls

# Resume project
/kai-video-produce resume kaicalls-demo-v1

# List all projects
/kai-video-produce list
```

#### `/video-setup` (to be created)
One-time configuration:
- Cloud GPU provider (Modal/RunPod)
- API keys (ElevenLabs optional)
- Tool deployment
- Verification

#### `/record-demo` (to be created)
Browser-based screen recording:
- Playwright automation
- Record user interactions
- Save as MP4
- Auto-add to project

#### `/scene-review` (to be created)
Visual verification in Remotion Studio:
- Scene-by-scene walkthrough
- Timing validation
- Quality checks

#### `/generate-voiceover` (to be created)
AI voiceover generation:
- Qwen3-TTS (free, 9 speakers)
- ElevenLabs (premium)
- Per-scene narration
- Auto-sync with visuals

#### `/voice-clone` (to be created)
Custom brand voice:
- Record sample
- Create cloned voice
- Save to brand profile

#### `/design` (to be created)
Visual refinement session:
- Focused on specific scene
- Frontend-design skill
- Typography, colors, layout

---

### 3. Video Tools

**Location:** `tools/video/`

**Core tools copied from video toolkit:**

| Tool | Purpose | Cost | Provider |
|------|---------|------|----------|
| **voiceover.py** | AI text-to-speech (Qwen3-TTS/ElevenLabs) | ~$0.01 | Modal/RunPod |
| **qwen3_tts.py** | Qwen3-TTS engine (9 speakers) | ~$0.01 | Modal/RunPod |
| **music_gen.py** | AI music generation (ACE-Step, 8 presets) | ~$0.05 | Modal/RunPod |
| **flux2.py** | AI image generation & editing (FLUX.2 Klein) | ~$0.02 | Modal/RunPod |

**Additional tools available in source (not yet copied):**
- sadtalker.py - Talking head from portrait + audio
- ltx2.py - AI video generation (text/image-to-video)
- image_edit.py - Image editing & style transfer
- upscale.py - Image upscaling (2x/4x)
- dewatermark.py - Video watermark removal
- addmusic.py - Add music to existing video
- redub.py - Redub video with different voice
- notebooklm_brand.py - Rebrand NotebookLM videos

---

## How It Works

### Multi-Session Project Lifecycle

```
planning → assets → review → audio → editing → rendering → complete
```

**Session 1: Planning**
- Select template (product-demo, explainer, social-short)
- Define scenes
- Write narration script
- **Output:** project.json, VOICEOVER-SCRIPT.md, CLAUDE.md

**Session 2: Assets**
- Record demos (/record-demo)
- Generate images (flux2.py)
- Add external videos/images
- **Output:** demos/*.mp4, images/*.png

**Session 3: Review**
- Visual verification in Remotion Studio
- Adjust timing
- Fix issues
- **Phase transition:** assets → audio

**Session 4: Audio**
- Generate voiceover (qwen3_tts.py)
- Add background music (music_gen.py)
- **Phase transition:** audio → editing

**Session 5: Render**
- Final polish
- Render MP4
- **Output:** out/{name}.mp4

---

### Project Structure

```
workspace/video/projects/{name}/
├── project.json              # State tracking (machine-readable)
├── CLAUDE.md                 # Auto-generated context (human+AI readable)
├── VOICEOVER-SCRIPT.md       # Full narration script
├── src/
│   ├── Root.tsx              # Remotion composition
│   ├── scenes/               # Scene components
│   └── config/               # Timing, brand, assets
├── public/
│   ├── demos/                # Screen recordings
│   ├── audio/                # Voiceovers, music, SFX
│   ├── images/               # Screenshots, graphics
│   └── videos/               # External clips
├── out/
│   └── {name}.mp4            # Final rendered video
└── package.json
```

---

### Intent vs Reality Reconciliation

**The Problem:**
- User creates project, defines 4 demos needed
- Records 3, forgets about it
- Comes back days later — which assets exist?

**The Solution:**

**On project resume:**
1. **Scan filesystem** — What files actually exist?
2. **Compare to intent** — What does project.json expect?
3. **Update statuses:**
   - Expected but missing → `asset-missing`
   - Present but not tracked → `asset-present`
4. **Flag discrepancies** — Alert user
5. **Regenerate CLAUDE.md** — Fresh context

**Example reconciliation:**
```python
# Expected (project.json)
scenes[3].visual.asset = "demos/voicemail.mp4"
scenes[3].status = "asset-needed"

# Actual (filesystem)
exists("public/demos/voicemail.mp4") = True

# Reconciled
scenes[3].status = "asset-present" ✓
```

---

### CLAUDE.md Auto-Generation

**Purpose:** Provide instant context when resuming after days/weeks

**Generated on:**
- Project creation
- Project resume
- Asset addition
- Phase transition

**Example:**
```markdown
# Project: kaicalls-demo-v1

**Template:** product-demo | **Brand:** kaicalls | **Phase:** audio
**Last Updated:** 2 days ago

## Current Status

All demo assets present. Voiceover generated. Ready for final review and render.

## Scenes

| # | Scene | Type | Visual | Status |
|---|-------|------|--------|--------|
| 1 | Title | title | slide | ✅ Ready |
| 2 | Problem | problem | slide | ✅ Ready |
| 3 | Demo | demo | demos/call-flow.mp4 | ✅ Present |
| 4 | CTA | cta | slide | ✅ Ready |

## Audio

- Voiceover: ✅ Generated (Qwen3-TTS, Ryan)
- Music: ⬜ Optional

## Next Actions

1. **Preview in Remotion Studio**
   ```bash
   cd workspace/video/projects/kaicalls-demo-v1 && npm run studio
   ```

2. **Render final video**
   ```bash
   npm run render
   ```

## Session History

- 2026-03-26: Created project, defined scenes (planning)
- 2026-03-26: Recorded demo (assets)
- 2026-03-27: Generated voiceover (audio)
- 2026-03-28: Resumed project (audio)
```

---

## Video Templates

**Available templates:**

### product-demo
**Best for:** Marketing videos, product launches, feature announcements

**Scene types:**
- title - Branded opening
- problem - Pain point visualization
- solution - How product solves it
- demo - Screen recording showing feature
- feature - Specific feature highlight
- stats - Numbers, metrics (animated)
- cta - Call to action

**Typical structure:**
```
Title (5s) → Problem (10s) → Solution (10s) → 
Demo 1 (20s) → Demo 2 (20s) → Stats (10s) → CTA (5s)
Total: ~80 seconds
```

---

### explainer
**Best for:** Educational content, tutorials, how-to guides

**Scene types:**
- title - Video title
- overview - Key points preview
- section - Content sections
- recap - Summary of key takeaways
- credits - Team/thank you

**Typical structure:**
```
Title (5s) → Overview (15s) → 
Section 1 (60s) → Section 2 (60s) → Section 3 (60s) → 
Recap (20s) → Credits (5s)
Total: ~225 seconds (3-4 minutes)
```

---

### demo-walkthrough
**Best for:** Screen recordings with narration, software tutorials

**Scene types:**
- title - Demo title
- demo - Screen recording sections
- summary - Recap of what was shown

**Typical structure:**
```
Title (5s) → Demo Part 1 (45s) → Demo Part 2 (45s) → 
Demo Part 3 (45s) → Summary (15s)
Total: ~155 seconds (2-3 minutes)
```

---

### social-short
**Best for:** TikTok, Instagram Reels, YouTube Shorts (15-60 seconds)

**Scene types:**
- hook - Pattern interrupt (0-3s)
- body - Main content
- cta - Call to action

**Typical structure:**
```
Hook (3s) → Body (45s) → CTA (7s)
Total: 55 seconds (vertical format)
```

---

## Brand Integration

### Brand Profile Structure

```
brands/{brand}/
├── brand.json       # Colors, fonts, typography
├── voice.json       # Voice settings
└── assets/          # Logo, backgrounds
```

### brand.json Example

```json
{
  "name": "KaiCalls",
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#10B981",
    "background": "#111827",
    "text": "#F9FAFB"
  },
  "fonts": {
    "heading": {
      "family": "Inter",
      "weight": 700
    },
    "body": {
      "family": "Inter",
      "weight": 400
    }
  },
  "logo": "assets/logo.svg",
  "style": "modern-tech"
}
```

### voice.json Example

```json
{
  "provider": "qwen3",
  "speaker": "Ryan",
  "tone": "professional-warm",
  "pace": "moderate",
  "elevenlabs": {
    "voice_id": null,
    "stability": 0.75,
    "similarity_boost": 0.75
  }
}
```

**Auto-application:**
- Brand colors → all slides
- Brand fonts → all text
- Brand logo → title/credits
- Voice settings → all voiceovers

---

## Cloud GPU Setup

### Option 1: Modal (Recommended)

**Cost:** $30/month free compute on Starter plan  
**Setup:** `/video-setup` auto-deploys all tools

**Tools deployed:**
- qwen3_tts (~$0.01/video)
- flux2 (~$0.02/image)
- music_gen (~$0.05/track)

**Typical usage:** $1-3/month for a few videos (within free tier)

---

### Option 2: RunPod (Alternative)

**Cost:** Pay-per-second, no minimums  
**Setup:** Manual per tool

```bash
python tools/video/qwen3_tts.py --setup
python tools/video/flux2.py --setup
python tools/video/music_gen.py --setup
```

---

## Cost Estimates

**Full video production (60-90 seconds):**

| Component | Tool | Provider | Cost |
|-----------|------|----------|------|
| Script generation | Claude | OpenClaw | ~$0.10 |
| Voiceover (AI) | Qwen3-TTS | Modal/RunPod | ~$0.01 |
| Music (AI) | ACE-Step | Modal/RunPod | ~$0.05 |
| Images (if needed) | FLUX.2 | Modal/RunPod | ~$0.04 |
| Rendering | Remotion | Local (Node.js) | $0.00 |
| **Total** | | | **~$0.20** |

**With premium features:**
- ElevenLabs voiceover: +$0.30
- AI video clips (LTX-2): +$0.23/clip
- Talking head (SadTalker): +$0.10

**Free tier covers:** 100+ videos/month on Modal Starter ($30 free compute)

---

## Example Workflows

### Product Demo Video (KaiCalls)

**Goal:** 90-second demo for Product Hunt launch

**Session 1: Planning (30min)**
```bash
/kai-video-produce new --template product-demo --brand kaicalls
# Define 7 scenes, write narration
```

**Session 2: Assets (1-2 hours)**
```bash
/record-demo --project kaicalls-demo-v1 --scene 4
/record-demo --project kaicalls-demo-v1 --scene 5
# Record 2 demo flows
```

**Session 3: Audio (30min)**
```bash
/generate-voiceover --project kaicalls-demo-v1
# AI voiceover generated
```

**Session 4: Render (30min)**
```bash
cd workspace/video/projects/kaicalls-demo-v1
npm run studio  # Preview
npm run render  # Final MP4
```

**Total time:** ~3 hours  
**Total cost:** ~$0.20  
**Output:** Professional 90-second demo video

---

### Social Short (TropiBot)

**Goal:** 30-second TikTok for product launch

**Session 1: Script + Render (1 hour)**
```bash
/kai-video-produce new --template social-short --brand tropibot
# Define 3 scenes (hook, body, CTA)
# All slides (no demos needed)
/generate-voiceover --project tropibot-short-1
npm run render
```

**Total time:** ~1 hour  
**Total cost:** ~$0.06  
**Output:** Vertical 30-second video for TikTok/Reels

---

## Integration with Other Marketing Commands

**Combined workflows:**

### Blog Post → Video
```bash
# 1. Write blog post
/kai-write blog --topic "KaiCalls 2.0 Features"

# 2. Generate video from blog
/kai-video-produce new --source content/blog/kaicalls-v2.md

# 3. Repurpose video for social
/kai-repurpose --source workspace/video/projects/kaicalls-v2/out/video.mp4

# 4. Schedule everything
/kai-content-calendar --schedule
```

---

### Product Launch
```bash
# 1. Growth plan
/kai-growth-plan --stage launch

# 2. Landing page
/kai-landing-page --product kaicalls

# 3. Demo video
/kai-video-produce new --template product-demo

# 4. Email sequence
/kai-email-system --template launch

# 5. Ad campaign
/kai-ad-campaign --platforms meta,google

# 6. Social content
/kai-social --month launch-month
```

---

## What's Not Yet Integrated

**From video toolkit but not copied:**

1. **Remotion templates** - Would need to be copied to `harness/templates/video/`
2. **Additional tools:**
   - sadtalker.py (talking head videos)
   - ltx2.py (AI video generation)
   - image_edit.py (image editing)
   - upscale.py (image upscaling)
   - dewatermark.py (watermark removal)
   - addmusic.py (add music to video)
   - redub.py (redub with different voice)
3. **Commands:** /video-setup, /record-demo, /scene-review, /generate-voiceover, /voice-clone, /design
4. **Remotion components** - Transitions, scenes, layouts
5. **Playwright recording** - Browser automation infrastructure

**These can be added as needed.**

---

## Next Steps

### Immediate
1. **Test voiceover generation:**
   ```bash
   cd kai-cmo-harness
   python tools/video/qwen3_tts.py --text "Test" --output test.mp3 --cloud modal
   ```

2. **Test music generation:**
   ```bash
   python tools/video/music_gen.py --preset corporate-bg --duration 30 --output test.mp3
   ```

3. **Test image generation:**
   ```bash
   python tools/video/flux2.py --prompt "Tech background" --cloud modal
   ```

### Short-Term
4. **Create first template:**
   - Copy product-demo template from video toolkit
   - Adapt for KaiCalls brand
   - Test full render

5. **Create remaining commands:**
   - /video-setup (configuration)
   - /record-demo (screen recording)
   - /generate-voiceover (audio)
   - /scene-review (visual verification)

6. **Copy additional tools:**
   - sadtalker.py (if talking head videos needed)
   - ltx2.py (if AI video clips needed)
   - image_edit.py (if image editing needed)

### Long-Term
7. **Build template library:**
   - Product demo (KaiCalls style)
   - Social short (TropiBot style)
   - Tutorial (BuildWithKai style)
   - Testimonial (customer quotes)

8. **Optimize costs:**
   - Benchmark Modal vs RunPod
   - Track actual spend per video
   - Identify cost reduction opportunities

9. **Measure impact:**
   - Track video performance
   - Conversion rates
   - Engagement metrics
   - ROI per video

---

## Credits

**Source:** [claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) by Digital Samba  
**License:** MIT  
**Author:** Conal Mullan  
**Integration Date:** March 28, 2026  
**Integrated By:** Kai-CMO

**What we kept:**
- Multi-session project tracking pattern
- Intent vs reality reconciliation
- CLAUDE.md auto-generation
- Brand integration approach
- Cloud GPU deployment pattern
- Core AI tools (voiceover, music, images)

**What we enhanced:**
- Integrated with existing kai-video script generation
- Added marketing-specific templates
- Simplified for marketing use cases (not general video)
- Streamlined command structure
- Combined with kai-cmo-harness architecture

**Gratitude:** This toolkit represents months of refinement by Digital Samba. We're building on their excellent work and contributing back upstream where appropriate.

---

## Summary

**Video production is now integrated into kai-cmo-harness.**

**What you can do:**
- Generate platform-optimized scripts (TikTok, YouTube, Reels)
- Produce full videos with AI voiceovers and music
- Track projects across multiple sessions
- Resume work after days/weeks with automatic context
- Render professional videos for ~$0.20 each

**What it enables:**
- Product demo videos for launches
- Tutorial videos for education
- Social shorts for TikTok/Reels
- Marketing videos for ads
- Testimonial videos for social proof

**Integration status:**
- ✅ Core skill documented
- ✅ Main command created
- ✅ Essential tools copied
- ⬜ Supporting commands (to be created)
- ⬜ Templates (to be copied)
- ⬜ Components (to be copied)

**Next:** Test tools, create first video, refine workflow.

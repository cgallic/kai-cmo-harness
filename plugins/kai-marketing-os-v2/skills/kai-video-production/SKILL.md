---
name: kai-video-production
description: Full-stack video production from script to rendered video. Combines script generation (optimized for TikTok/YouTube/Reels) with AI-powered video rendering using Remotion, AI voiceovers (Qwen3-TTS/ElevenLabs), music generation (ACE-Step), and browser-based demo recording. Multi-session project tracking with automatic intent reconciliation. Use when "create video", "produce video", "demo video", "product video", or any request to generate AND render video content.
---

# /kai-video-production — a rendered MP4 that started as a script worth rendering

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A finished video: an approved script, the assets it needs, synced audio, and a rendered MP4 at platform spec — with `project.json` describing the real state of the project on disk so the next session resumes without reconstruction.

Production amplifies a good script and cannot rescue a bad one. Script quality is settled before any asset is generated. Scope splits three ways: **script only** (stop at the script, user records), **automated production** (full render pipeline), **hybrid** (generate voiceover and slides, user supplies demos).

## Done when

Work type `social-post` — floor **E5/C2/O3** (`harness/eco-floors.yaml`), contract `harness/skill-contracts/social-post.yaml`. A render that will run as paid creative instead follows `paid-ad-campaign` (E5/C4/O4), which requires the platform policy reference loaded before the creative is submitted.

- **E5** — the video is live on the target platform and a non-actor read the permalink back against the approved cut. The MP4 in `out/` is E1; human approval of the winning variant and the final cut is E3. This skill renders; it does not upload.
- **C2** — `banned_word_check` and `four_us_score` (10/16) clean on the script, plus both render checklists below.
- **O3** — reach, engagement rate, profile clicks, and link clicks read from platform insights at 7 days against a baseline recorded before publish.

**Before rendering:** script approved with strong hooks and no AI slop · all assets present, no missing demos or images · scene durations match narration · voiceover aligned to visuals · brand colors, fonts, and logo correct · transitions smooth · text contrast and size readable · preview walked through in Remotion Studio.

**After rendering:** resolution as specified · voiceover audible over music · file size within platform limits · format plays on the target platform.

## Constraints

- **Human approval is required to move from the variant lab to full render.** Renders cost compute and time; an unapproved concept does not get either.
- **Preflight variant lab runs before asset creation or rendering** — 3 hook variants (each with platform, expected first-frame visual, and viewer promise), 2 structure variants for scene order or pacing, 2 CTA variants matched to the campaign goal, and 1 risk note per variant covering unsupported claims, brand mismatch, or approval needs. Write to `workspace/video/projects/{name}/PREFLIGHT-VARIANTS.md`, pick one winner, keep the rejected variants in the same file as the kill list.

  | Factor | Score | Question |
  |---|:--:|---|
  | Hook strength | 1-5 | Does the opening create immediate attention? |
  | Message clarity | 1-5 | Is the core idea obvious after one watch? |
  | Proof density | 1-5 | Are claims supported by demo, quote, data, or source? |
  | Production fit | 1-5 | Can this be made with available assets and timeline? |
  | Brand safety | 1-5 | Does it avoid fake authority, risky claims, or unclear rights? |

- **Read `MARKETING.md` from the project root before asking the user anything.** If it does not exist, build it from the codebase — CLAUDE.md, README.md, PROJECT.md, package.json, landing pages, email/ad/analytics config — using the template from `/kai-email-system`, and confirm the draft.
- **Know these before producing:** topic, platforms, format (talking head, screen recording, b-roll, animation, slides), length band, goal, and whether the user wants script only or a full render.
- **The filesystem is the source of truth.** On resume, scan the project directory, compare to `project.json`, and correct statuses — `asset-needed` with the file present becomes `asset-present`; `ready` with the file missing becomes `asset-missing`. Flag every discrepancy to the user rather than rendering around it. Regenerate the project's `CLAUDE.md` status document after reconciliation.
- **Brand profiles auto-apply.** Colors, fonts, and logo come from `brands/{brand}/brand.json`; voice settings from `voice.json`. Never re-specify a color or font inline that the brand file already defines.
- **Prerequisites are real blockers:** Node.js 18+ (Remotion) and FFmpeg (encoding) are required. Cloud AI features need a Modal account ($30/month free compute) or RunPod (pay-per-second); ElevenLabs is optional for premium voices. `/video-setup` handles configuration. If a tool is not deployed in this install, say so — never describe output it did not produce.
- **Prefer the free or cheap tool.** Qwen3-TTS and ACE-Step cover most work; premium providers are an explicit choice, not a default.
- **Nothing publishes.** The render lands in `out/`; uploading is a separate approved step.

## Context

| Need | Load / run |
|---|---|
| Video content mechanics | `knowledge/playbooks/video-content-creation.md` |
| TikTok · YouTube · Reels | `knowledge/channels/tiktok-algorithm.md` · `knowledge/channels/youtube.md` · `knowledge/channels/instagram.md` |
| Slide-scene design polish | `knowledge/frameworks/design/frontend-design.md` |
| Product, ICP, voice, channels | `MARKETING.md` (project root) |
| Setup, recording, audio, review, design, cloning | `/video-setup` · `/record-demo` · `/generate-voiceover` · `/scene-review` · `/design` · `/voice-clone` |

**Templates:** `product-demo` (title, problem, solution, demo, CTA) · `explainer` (title, overview, sections, recap) · `demo-walkthrough` (screen recording with narration) · `social-short` (15–60s vertical) · `testimonial` (quote + visuals) · `announcement` (launches, releases, news). Reference material ships beside them — `templates/product-demo/`, `templates/explainer/`, `templates/social-short/`, and finished examples in `examples/digital-samba-skill-demo/` and `examples/schlumbergera/`, each with source, rendered MP4, and production notes.

**Project layout:**
```
projects/{name}/
├── project.json          # state, scenes, assets, sessions
├── VOICEOVER-SCRIPT.md   # full narration
├── src/                  # Root.tsx, scenes/, config/ (timing, brand, assets)
├── public/               # audio/, demos/, images/, videos/
└── CLAUDE.md             # auto-generated status
```

`project.json` carries `name`, `template`, `brand`, `created`, `updated`, `phase`, a `scenes[]` array (`id`, `type`, `duration`, `visual`, `narration`, `status`), an `audio` block (voiceover: file/status/provider/speaker; music: file/status/preset), `estimates.totalDurationSeconds`, and a `sessions[]` log of date, phase, and summary. Lifecycle: `planning → assets → review → audio → editing → rendering → complete`.

**Scene types:** title · overview · demo · split-demo · problem · solution · feature · stats · testimonial · cta · credits.

**Assets.** Slides (title cards, bullets, stat visualizations, CTA screens) generate from the brand profile. Demos come from `/record-demo` (Playwright browser recording, `--script demo-script.md --auto` for scripted automation), an external MP4/MOV dropped into `public/demos/`, or Playwright screenshots. Images: `python tools/flux2.py --prompt "..." --cloud modal` for generation, `python tools/image_edit.py --input photo.jpg --style ...` for editing.

**Audio.**
```bash
python tools/voiceover.py --provider qwen3 --speaker Ryan --script VOICEOVER-SCRIPT.md --scene-dir public/audio/scenes --json
python tools/voiceover.py --provider elevenlabs --voice-id {ID} --script VOICEOVER-SCRIPT.md
python tools/music_gen.py --preset corporate-bg --duration 120 --bpm 90 --key "D Minor"
python tools/music.py --prompt "Upbeat corporate" --duration 120
python tools/sfx.py --preset whoosh   # also: pop, success
```
Qwen3 speakers: Ryan, Brad, Ava, Lily, Emily, Sam, Alex, Kevin, Zoe. Music presets: corporate-bg, upbeat-intro, dramatic-reveal, ambient-subtle, tension-build, inspirational-montage, tech-minimal, celebration-end. `/voice-clone` produces a custom brand voice.

**Brand files.** `brand.json`: `colors` (primary `#3B82F6`, secondary `#10B981`, background `#111827`, text `#F9FAFB` in the KaiCalls example), `fonts.heading` / `fonts.body` (family + weight), `logo`, `style`. `voice.json`: `provider`, `speaker`, `tone`, `pace`, and an `elevenlabs` block (`voice_id`, `stability`, `similarity_boost`).

**Transitions** — 7 custom plus 4 Remotion official, imported from `@/lib/transitions`:

| Transition | Effect | Use case |
|---|---|---|
| `glitch()` | Digital distortion + RGB shift | Tech aesthetic |
| `rgbSplit()` | Chromatic aberration | Energetic cuts |
| `zoomBlur()` | Radial motion blur | Dramatic reveals |
| `lightLeak()` | Cinematic lens flare | Professional polish |
| `clockWipe()` | Radial sweep reveal | Time-based content |
| `pixelate()` | Digital mosaic | Retro/8-bit |
| `checkerboard()` | Grid reveal (9 patterns) | Clean, geometric |
| `slide()` `fade()` `wipe()` `flip()` | Official Remotion | Standard, subtle, directional, playful |

**Review and render.**
```bash
cd projects/{name} && npm run studio     # Remotion Studio at localhost:3000
npm run render -- --quality=low          # preview
npm run render                           # final → out/{name}.mp4
```
Render options: `--codec=h264` (default) or `h265` (smaller) · `--resolution=1080p` (default) or `720p` · `--fps=30` (default) or `60`. Timing adjustments live in `config.ts`.

**Post-production:** `tools/addmusic.py` (add music to an existing MP4) · `tools/redub.py` (swap voice) · `tools/dewatermark.py --preset sora --cloud modal` · `tools/upscale.py --scale 2x --cloud modal`.

**Cloud GPU.** Modal deploys via `/video-setup`: qwen3_tts (~$0.01/video), flux2 (~$0.02/image), music_gen (~$0.05/track), sadtalker (~$0.10/video), ltx2 (~$0.23/clip), image_edit (~$0.03/image), upscale (~$0.01/image), dewatermark (~$0.10/video). RunPod is the pay-per-second alternative (`python tools/<tool>.py --setup` per tool). A 60–90s video costs roughly $0.20 all-in — script ~$0.10, Qwen3 voiceover ~$0.01, ACE-Step music ~$0.05, FLUX.2 images ~$0.04, local Remotion render $0.00. Premium adds: ElevenLabs voiceover +$0.30, LTX-2 clip +$0.23, SadTalker +$0.10. Modal's Starter free tier covers 100+ videos/month.

**Output** goes to `workspace/video/`: `_video-projects.md` (index), `projects/{name}/` (with `out/{name}.mp4`), `scripts/` split by `tiktok/`, `youtube/`, `reels/`, and `_production-guide.md`.

**Entry points:** `/kai-video script --platform tiktok --topic "..."` (script only) · `/kai-video produce --template product-demo --brand kaicalls` (full pipeline) · `/kai-video resume {name}`. Downstream: `/kai-repurpose` for clips, `/kai-social` for scheduling, `/kai-content-calendar` for release timing, `/kai-analytics` for performance.

**Common failures:** "asset not found" — `project.json` paths disagree with the filesystem, reconcile · "audio out of sync" — adjust `config.ts` timing or regenerate the voiceover against the current script · "render fails" — check `ffmpeg -version`, confirm assets exist, run a low-quality preview first · "tool timeout on Modal" — check compute credits and `modal app list`, or fall back to RunPod · "brand colors not applied" — `brand.json` missing from `brands/`, brand name mismatch in `project.json`, or `src/config/brand.ts` needs regenerating.

## Escalate when

- The variant lab winner has not been approved and the next step would spend render or GPU compute.
- Demo footage shows customer data, third-party UI, or anything whose rights are unconfirmed.
- A claim in the narration needs a number with no source.
- Reconciliation finds assets the project did not expect, or expected assets that vanished.
- Prerequisites are missing (no Node 18+, no FFmpeg, no deployed cloud tools) and the user expects a rendered file.
- The video is destined for a paid placement — the platform policy reference and the `paid-ad-campaign` floor apply before submission.

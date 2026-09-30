---
name: kai-motion-spot
description: Code-rendered motion video for a product or a client, built the way a motion studio would do it. Every frame comes from an HTML seek(t) page rendered by Playwright at 1080p60 with real motion blur, using real product UI and screenshots with a privacy blur, and an ElevenLabs hype score cut on bar lines with its drop verified on the reveal. Three formats — a 20-30 s hype launch spot, a polished feature walkthrough from real screenshots, and a 19 s pain-point video with a muted site cut and burned-in text. Delivered with baked posters, H.264 + VP9 web encodes at 1280 px (1.5-3 MB), a site-embed kit (muted autoplay or click-to-play), 9:16 social re-layouts and share copy, plus a service playbook for selling it. Use when "make a launch video", "make a commercial / promo / ad spot", "motion design video", "product walkthrough video from screenshots", "pain point videos for the site", "videos for the homepage", "sell video production", "price a video package", or a polished brand spot is wanted rather than a talking-head edit or a Remotion template batch (use /kai-video-production for those).
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

# /kai-motion-spot — product video that looks like a studio made it, from code

## Objective

A delivered video package the approver signs off: a hype launch spot, a walkthrough set built from real screenshots, or a pain-point set. Each video has a 16:9 master, a real 9:16 re-layout, a baked poster, web encodes, an embed snippet and share copy. Everything on screen comes from one HTML page where every style is a pure function of time, and the score is cut so its drop lands on the reveal. When the request is about selling this, the objective is a service offer built from the playbook, with the price left to the founder.

## Done when

Work type `social-post` for anything published (floor **E5/C2/O3**, `harness/eco-floors.yaml`). A client delivery is done at **E3**, when the approver signs off the final package.

- **E3**: the approver chose a score variant and signed off the final. Publishing is a separate, per-post approval.
- **C2**:
  - `analyze.py --verify` passes on every master (drop within 30 ms of the picture), loudness is -14 LUFS, and SFX are within 15 ms of the grid.
  - `qa.py` sheets were reviewed for the **whole** video at phone size in both formats, against every row of the watch-back table.
  - Privacy sheets were read with no personal data legible, and site cuts were reviewed muted.
  - ffprobe matches the meta, frame 0 is the baked poster, and web encodes are 1.5-3 MB with faststart.
- **O3** (published cuts): reach, engagement rate, profile clicks and link clicks at 7 days, against a baseline recorded before publishing.

## Constraints

- **Keys come from the environment only:** `ELEVENLABS_API_KEY`, and `UPLOAD_POST_API_KEY` for publishing. Never print them or write them into the project.
- **Claims:** show what is live, plus roadmap features the client already claims publicly, and list those roadmap claims in the report. Never invent features, stats, customers or testimonials. Use the official logo files only; never retype a logo.
- **Real material:**
  - The newest UI only, in tight readable crops, never a whole spinning page, never demo cruft.
  - Screenshots go through `assets.py blur`, which downsamples before blurring; a plain Gaussian can leave text readable.
- **Grid:** 120 BPM, with cuts on downbeats and the drop on the reveal. Any line meant to be read stays settled for at least 0.3 s per word. Stats stack and stay.
- **Music is hype** for launches, whatever the brand looks like. Calm or ambient only when asked.
- **Motion taste:** one idea per shot, one accent, masked reveals, one camera language. The effects banned in the method (shake, RGB split, flares, particles, glitches, bouncy easing) stay banned.
- **Formats:**
  - 9:16 is its own re-layout, never a pillarbox, with key content above the bottom ~300 px.
  - Pain-point site cuts are muted, and the burned-in text carries the story.
  - Walkthroughs are click-to-play; short loops are muted autoplay.
- **Render fixes stay on:** the warm-up pass, the two-rAF paint wait, every hard cut in `cuts`, and fast moves in `fast`.
- **Publishing:** posting follows `harness/references/social-automation-rules.md` and the platform posting rules. `upload_post.py` stays a dry run until the account owner approves that exact post.
- **Selling:** the price is a founder decision; cite market reference points only with a URL. Internal costs (music credits, render time, operator time) never appear on a customer-facing proposal, page or email.

## Context

| Need | Load / run |
|---|---|
| Formats, page contract, score, render fixes, taste rules, watch-back QA table | `harness/references/motion-spot-method.md` |
| Deliverables menu, client inputs, turnaround, QA checklist, approval, cost basis (INTERNAL) | `harness/references/motion-spot-service-playbook.md` |
| Engine (run from `workspace/video/<slug>/`) | `scripts/motion_spot/`: `render.py`, `probe.py`, `qa.py`, `poster.py`, `web_encode.py`, `analyze.py`, `build_score.py`, `sfx.py`, `music.py` (`--dry-run`), `assets.py`, `walkthrough/walkthrough.py`, `upload_post.py` |
| Starting points | `reference_spot.html` + `.meta.json`, `examples/walkthrough.example.json`, `examples/cues.example.json`, `examples/blur-boxes.example.json`, `examples/upload-spec.example.json` |
| Product, claims, voice | `MARKETING.md` (project root) |
| Posting rules | `harness/references/social-automation-rules.md`, `harness/references/*-organic-posting-rules.md` |

Requirements: Python 3.10+ with `playwright numpy scipy pillow` (then `playwright install chromium`), and ffmpeg with libx264 and libvpx-vp9. Smoke test: `DUR=2 MASTER=none PAGE=index.html python "$KAI/render.py"`.

**Output:** `workspace/video/<slug>/`:
- the page and meta
- `assets/`, `audio/`
- `out/`: masters, posters, `share-copy.txt`, `render-log.txt`, `web/` with the encodes and snippets, and `site-embed.md` for sets
- `qa/`: the QA sheets

## Escalate when

- The product, the promise or which features are live cannot be established from `MARKETING.md` or the client's materials.
- A screen can only be shown with real personal data that the blur cannot fully cover.
- A claim, stat or testimonial the client wants has no source.
- `analyze.py --verify` keeps failing after a snap. Offer another track rather than shipping an off-beat drop.
- Anything would be posted publicly, or a price would be quoted to a customer.

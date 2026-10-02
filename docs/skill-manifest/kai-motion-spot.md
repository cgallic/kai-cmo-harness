---
name: kai-motion-spot
version: 1.0.0
category: production
last_updated: 2026-09-30
---

# Kai Motion Spot

### One-line claim
Studio-grade product video from code: a hype launch spot, a walkthrough built from privacy-blurred real screenshots, or a pain-point set with muted site cuts. Every frame is rendered from an HTML `seek(t)` page with real motion blur, over a generated score whose drop is measured and verified on the reveal. Delivered with posters, web encodes, embed kits and share copy.

### Triggers
- make a launch video
- make a commercial / promo / ad spot
- motion design video
- product walkthrough video from screenshots
- pain point videos for the site
- videos for the homepage
- sell video production
- price a video package

### Inputs
- `product_context` (file, required) - `MARKETING.md`: the promise, which features are live, which are on the public roadmap.
- `format` (enum, required) - `launch_spot`, `walkthrough_set`, or `pain_point_set`.
- `ui_material` (files, required) - newest UI recordings or screenshots, plus a list of the private fields to blur.
- `brand_kit` (files, required) - the official wordmark and logo files, the accent color, the typeface.
- `destinations` (list, optional) - site sections and social accounts.
- `approver` (string, required for delivery) - the person who signs off the review cut and each public post.

### Outputs
- Artifact -> `workspace/video/<slug>/out/`:
  - 16:9 and 9:16 masters with baked posters
  - `web/`: H.264 and VP9 encodes at 1280 px, 1.5-3 MB, with embed snippets
  - `share-copy.txt` and `render-log.txt`
  - `site-embed.md` for sets
- Quality report -> `qa/<name>/`:
  - tile sheets, cut tiles and privacy sheets
  - the `analyze.py --verify` result, loudness, and ffprobe
- Service offer (when selling) -> deliverables, inputs, turnaround, QA and approval from the playbook. The price is marked as a founder decision.

### Methodology
- [motion-spot-method.md](../../harness/references/motion-spot-method.md):
  - the page contract (a pure `seek(t)`, `window.ready`, a real 9:16 re-layout)
  - the 120 BPM beat grid and the 0.3 s-per-word readability budget
  - drop-hit detection with a pre-hit snap and a comb-filter tempo, verified on the master
  - the render warm-up and two-rAF paint wait, and cut-side subframe clamping
  - the taste rules and the watch-back QA table
- [motion-spot-service-playbook.md](../../harness/references/motion-spot-service-playbook.md): the deliverables menu, client inputs, turnaround, QA checklist, approval step, sourced market reference points, and the INTERNAL cost basis.
- Posting follows [social-automation-rules.md](../../harness/references/social-automation-rules.md).

### Dependencies
- [kai-video-production](./kai-video-production.md) (Remotion template production; the alternative route)

### Called by
- The `/kai` router (PRODUCE table)

### Quality gates
- `analyze.py --verify` passes (the drop is within 30 ms of the picture), loudness is -14 LUFS, and SFX are within 15 ms of the beat grid.
- The whole video was reviewed at phone size in both formats, against the QA table.
- Privacy sheets were read and no personal data is legible. Site cuts were reviewed muted.
- ffprobe matches the meta and frame 0 is the baked poster. Web encodes are 1.5-3 MB with faststart.
- Nothing is published without the owner's per-post approval.

### Provenance written
- `render-log.txt`: frames, seconds and workers per render (the cost basis).
- `audio/analysis.json`: D, tempo, drop length and kick offsets per track.
- A roadmap-claims list in the delivery report.

### Example artifacts
- Reference page: `scripts/motion_spot/reference_spot.html` and its `.meta.json`
- Specs: `scripts/motion_spot/examples/` (walkthrough, SFX cues, blur boxes, upload spec)

### Failure modes
- ElevenLabs ignores section timing, and builds often have a pre-drop hit. Unverified drops land off the reveal.
- A plain Gaussian blur can leave screenshot text readable after the 2x sharpen. The downsample-first blur is required.
- Measuring layout while a scene is `display:none` returns zero boxes, so highlights and strikes end up misplaced.
- Without the warm-up pass, workers that start mid-range capture washed-out text.
- Missing `ELEVENLABS_API_KEY` blocks the score. `music.py --dry-run` still shows the plan.

### Competitive claim
Renders a set of product videos in days from one page and one score. Every frame can be re-rendered on its own, and every drop is measured rather than eyeballed. It does not claim view, reach or conversion outcomes.

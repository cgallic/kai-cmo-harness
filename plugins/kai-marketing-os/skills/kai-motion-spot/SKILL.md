---
name: kai-motion-spot
description: Code-rendered motion video for a product or a client, built the way a motion studio would do it. Every frame comes from an HTML seek(t) page rendered by Playwright at 1080p60 with real motion blur, using real product UI and screenshots with a privacy blur, and an ElevenLabs hype score cut on bar lines with its drop verified on the reveal. Three formats — a 20-30 s hype launch spot, a polished feature walkthrough from real screenshots, and a 19 s pain-point video with a muted site cut and burned-in text. Delivered with baked posters, H.264 + VP9 web encodes at 1280 px (1.5-3 MB), a site-embed kit (muted autoplay or click-to-play), 9:16 social re-layouts and share copy, plus a service playbook for selling it. Use when "make a launch video", "make a commercial / promo / ad spot", "motion design video", "product walkthrough video from screenshots", "pain point videos for the site", "videos for the homepage", "sell video production", "price a video package", or a polished brand spot is wanted rather than a talking-head edit or a Remotion template batch (use /kai-video-production for those).
---

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

# Motion Spot

Build studio-grade product video from code: one HTML page where every style is a pure function of time, rendered frame by frame, with a real score cut to the picture. Real UI, real screenshots, a real drop on the reveal.

Load before starting: `harness/references/motion-spot-method.md` (formats, page contract, score, render fixes, taste rules, watch-back QA). When the video is being sold, also load `harness/references/motion-spot-service-playbook.md`. When anything will be posted, load `harness/references/social-automation-rules.md` and the platform's `harness/references/*-organic-posting-rules.md`.

**Engine:** `scripts/motion_spot/` in the Kai root. Run every script **from the video project folder** (`workspace/video/<slug>/` in the current project) with the Kai root's path, e.g. `KAI=<kai-root>/scripts/motion_spot; python "$KAI/render.py"`. Requirements: Python 3.10+, `pip install playwright numpy scipy pillow` then `playwright install chromium`, and ffmpeg with libx264 and libvpx-vp9.

**Keys come from the environment only:** `ELEVENLABS_API_KEY` (music) and, for publishing, `UPLOAD_POST_API_KEY`. Never print them, paste them into chat, or write them into a project file.

## Phase 1: Brief and beat sheet

1. Read `MARKETING.md`. Pin down the product and its one-line promise, the format (launch spot, walkthrough set or pain-point set), 3-5 real moments to show, one accent color and the tone preset. Ask only if the product itself is unknown.
2. List what is live, what is publicly on the roadmap, and what nobody claims. Show only the first two, and list roadmap claims in the report. Never invent stats, customers or testimonials.
3. Write the beat sheet on the 120 BPM grid (2 s bars, 0.5 s beats) before any code. Every cut goes on a downbeat, every UI hit on a beat, and the drop on the reveal at 4.0 s. Each bar has to answer "why is this here?"
4. Apply the readability budget: at least 0.3 s settled per word for any line meant to be read. Stats and lists stack and stay.
5. For pain-point sets, start from the customer's own words for each pain. The first frame names the adversary.

## Phase 2: Assets

1. **UI:** crop the newest recordings TIGHT to a readable moment: `python "$KAI/assets.py" clip rec.mp4 inbox --start 8 --dur 3.2 --crop X,Y,W,H`. Never show a whole page, and never frames with demo cruft.
2. **Screenshots for walkthroughs:** capture at normal zoom into `cap/`, list every private field in a boxes file (`examples/blur-boxes.example.json`), then run `python "$KAI/assets.py" blur boxes.json`. It downsamples 9x before blurring so glyphs are destroyed, then stores the image 2x for crisp zooms.
3. **Stock:** only graded, good footage. `assets.py still` fits it with a face-safe crop.
4. **Product photos:** `assets.py key` cuts a white background. Map an HTML screen onto the device with `quad()` from `reference_spot.html`.
5. **Brand:** use the client's official wordmark and logo files. Never retype a logo, and never use another brand's assets without the client's rights to them.

## Phase 3: The page

1. **Launch spot or pain-point set:** copy `scripts/motion_spot/reference_spot.html` to `index.html` and `reference_spot.meta.json` to `index.meta.json`, then rebuild the content on your beat sheet. Keep the contract: `window.ready`, and a pure `window.seek(t)` that may return a promise. One page serves 16:9 and a real 9:16 re-layout (`V = innerHeight > innerWidth`). For a pain-point set, one page with `?n=<k>` picks the video.
2. **Walkthrough:** write a spec from `examples/walkthrough.example.json` (shots, camera keys, spotlights, callouts, captions, title and end card), then run `python "$KAI/walkthrough/walkthrough.py" spec.json`. It writes the page, the SPEC and the meta with every cut and fast move.
3. Put every hard cut in the meta's `cuts` and every whip, zoom or fast reveal in `fast`.
4. Probe while building: `python "$KAI/probe.py" 0.5 4.0 6.2` (add `VW=1080 VH=1920` for 9:16). Read the contact sheet at phone size.

## Phase 4: Score

1. `python "$KAI/music.py" trap stomp`: 2-4 hype tracks. A launch is hype whatever the brand looks like. Check the plan without spending anything with `--dry-run`.
2. `python "$KAI/analyze.py" audio/*.mp3`: the drop D is snapped to the real drop hit (a pre-drop hit followed by silence is rejected), the tempo is checked against the 120 grid, and the output shows how much clean drop there is. Pick the track with the biggest jump and the longest clean drop.
3. Cues: copy `examples/cues.example.json`, set a cue on every picture event, then run `python "$KAI/sfx.py" cues.json`. Keep on-beat peaks under 15 ms from the grid.
4. `python "$KAI/build_score.py" audio/eleven_trap.mp3 <D> audio/master.wav` builds the bar-accurate edit at -14 LUFS.
   - For a 19 s pain-point video: `--dur 19 --drop-end 16 --riser 0`.
   - For a walkthrough bed: `--dur <len> --drop-end <end card> --riser 0`.
   - For a track that dips mid-drop: `--max-drop <s>`.
5. **Verify:** `python "$KAI/analyze.py" --verify audio/master.wav 4.0` has to pass (within 30 ms). If it doesn't, snap D to `kicks_from_D` and rebuild.
6. Build 2-3 score variants on the same picture for the approver to choose from.

## Phase 5: Render

1. `PAGE=index.html OUTNAME=<Slug>_16x9.mp4 python "$KAI/render.py"`. For 9:16: `VW=1080 VH=1920 FRAMES=frames_v OUTNAME=<Slug>_9x16.mp4`. For one video of a set: `QUERY="?n=3"`.
2. The renderer's warm-up pass and paint wait stay on; they fix washed-out text and missed paints. After fixing a scene, delete only that frame range and re-run.
3. `out/render-log.txt` records frames and seconds per render. Keep it; it is the cost basis.

## Phase 6: Watch back and QA

1. `python "$KAI/qa.py" out/<Slug>_16x9.mp4 --frames frames` writes the whole video at 4 fps, dense tiles at every cut, privacy sheets and single-frame spikes. It also prints ffprobe and loudness.
2. Walk the full QA table in `motion-spot-method.md` on the **whole** video, at phone size, in both formats. Read every `priv_NN.jpg` for private data. Review site cuts muted.
3. Fix, re-render the range, and repeat until it is clean. Nobody sees a cut you have not watched.

## Phase 7: Deliver

1. `python "$KAI/poster.py" out/<Slug>_16x9.mp4 <settled t>` on every master.
2. Web encodes:
   - Walkthroughs and spots: `python "$KAI/web_encode.py" out/<Slug>_16x9.mp4 --slug <slug> --poster-t <t> --mode click`
   - Pain-point site cuts: `--mode autoplay`
   - Either way, add `--vertical out/<Slug>_9x16.mp4` for the social cut.
   The output is 1280 px, 30 fps, H.264 faststart plus VP9, 1.5-3 MB each, and an embed snippet.
3. Write `out/share-copy.txt` for each video:
   - a YouTube title
   - a 1-3 sentence caption (specific, never "excited to share")
   - a TikTok/Reels caption with no link
   - hashtags
4. For a set, write `out/site-embed.md`:
   - the files per video
   - title, caption and alt text for each one
   - the suggested page section and order
   - the grid snippet, with reduced motion respected
5. Send the review cut to the approver: masters, score variants and a contact sheet. Apply one consolidated round of changes, then deliver the final.
6. **Publishing is a separate approval, per post.** `python "$KAI/upload_post.py" spec.json` is a dry run. Pass `--yes` only after the account owner approves that exact post in chat. Page and board ids go in the spec, never in code.

## Selling it

When the request is about offering this as a service, use `harness/references/motion-spot-service-playbook.md`: the deliverables menu, client inputs, turnaround, the QA checklist and the approval step. The price is a founder decision. The playbook gives sourced market reference points only. **Internal costs (music credits, render time, operator time) never appear on a customer-facing proposal, page or email.**

## Output

`workspace/video/<slug>/`:
- the page (`index.html` or `<name>.html`) and `*.meta.json`
- `assets/`, `audio/`, `frames*/`
- `out/`: masters, posters, `share-copy.txt`, `render-log.txt`, and `web/` with the encodes and embed snippets
- `qa/`: the QA sheets
- `out/site-embed.md` for sets

## Quality gates

- [ ] Drop verified on the reveal (`analyze.py --verify`), -14 LUFS, SFX on the grid
- [ ] Whole video watched at phone size in both formats; every row of the QA table checked
- [ ] Privacy sheets read; no real personal data legible
- [ ] Site cuts make sense muted
- [ ] ffprobe matches the meta; frame 0 is the baked poster
- [ ] Web encodes are 1.5-3 MB and faststart; the snippet matches the embed mode
- [ ] No invented claims; roadmap claims listed; official logo files only
- [ ] Nothing posted without the owner's approval of that post

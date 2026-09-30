# Motion Spot Method: code-rendered product video

The method behind `/kai-motion-spot`. Everything on screen is computed from time inside one HTML page.
Playwright renders it frame by frame with real motion blur, and Python builds the score and the deliverables.
The engine lives in `scripts/motion_spot/`, both in the repo and in the plugin install.

## Why code-rendered

- **Frame-deterministic.** `window.seek(t)` sets every style from pure functions of `t`, so any frame can be
  re-rendered on its own. After a fix you delete that frame range and re-run; the rest of the video stays cached.
- **Real product, not a mock.** Screens are the client's real UI: crops of recordings, or screenshots that have
  been through the privacy blur. Type is live text, so it stays sharp at any zoom.
- **Music cut to picture.** The drop, the cuts and the UI hits all sit on one beat grid: 120 BPM, 2 s bars, 0.5 s beats.

## The three formats

| Format | Length | Shape | Music | Where it runs |
|---|---|---|---|---|
| **Hype launch spot** | 20-30 s | 16:9 plus a re-laid-out 9:16 | Hype score, drop on the reveal | Social launch posts, YouTube, the site hero |
| **Polished walkthrough** | 30-40 s per feature | 16:9 (plus 9:16 for the hero feature) | A bed cut from the same score | Site feature sections, sales follow-ups |
| **Pain-point video** | ~19 s loop | 16:9 site cut plus 9:16 social | Score on the social cut; the site cut is **muted** | A "Sound familiar?" grid on the site, and social |

### Hype launch spot (`reference_spot.html`)
1. **Beat sheet first**, before any code. Hook (bars 1-2) → the drop and reveal at 4.0 s → 3-5 real product
   moments, one idea per bar → category line → logo impact → hold. Every cut lands on a downbeat and every UI hit on a beat.
   Each bar has to answer "why is this here?" A montage of settings screens between the hook and the demo breaks the story.
2. **Readability budget.** Any line meant to be read stays fully on screen and settled for at least 0.3 s per word
   (6 words = 1.8 s) before it moves. Lists and stats stack and stay; they never replace each other at beat speed.
3. **Tone presets** set the visual pacing only. The music is hype every time.
   - `confident`: dark, one accent, masked reveals, whips
   - `polished`: fewer scenes, long holds, soft pushes
   - `cinematic`: huge type, dramatic wipes
   - `chaotic`: 6-8 scenes, some under 2 s, for ad-hook A/B tests
   - `app-store`: clean feature cards, smooth slides

### Polished walkthrough (`walkthrough/walkthrough.py` + `walk.js`)
- Built from **real screenshots**. Capture at the app's normal zoom, then run the privacy pass (`assets.py blur`).
  It blurs every name, email, phone number, quota, workspace id and thread title that does not belong to the demo.
  The blur downsamples 9x before the Gaussian so the glyphs are destroyed, and then the shot is upscaled 2x with
  Lanczos plus unsharp so camera zooms stay crisp.
- A JSON spec drives the page:
  - a camera path per shot (`[t, cx, cy, zoom]` keys, cubic in-out)
  - spotlights (the rest of the screen dims to 52%)
  - callout pills (a dot, then a line, then a clip-revealed pill)
  - caption plates (headline plus sub line, `*accent*` words)
  - a title card and an end card
- `walkthrough.py` writes the page, the SPEC and the meta. The meta holds every cut, and each fast camera move becomes a FAST window.
- Every shot ends on a settled state. Callouts leave before the cut, never across it.

### Pain-point video (19 s)
- The structure is **pain (0-4) → the fix in the product (4-16, in-drop cuts on 8 and 12) → the promise line →
  logo and URL (16-19)**.
- Name the adversary on the first frame. "Who's free that Saturday?" beats any statistic.
- **Muted site cut with burned-in text.** A site autoplays video muted, so the on-screen text has to carry the whole
  story with the sound off. Write it and review it muted. The score only goes on the social cut and the click-to-play version.
- One page can hold a set: `?n=3` picks the video (`QUERY="?n=3"` for render and probe).

## Page contract (`reference_spot.html`)
- `window.ready` resolves after the fonts and images are decoded and `seek(0)` has run.
- `window.seek(t)` sets everything from `t`. No CSS animations, no timers, no state carried between calls.
  It may return a promise; the renderer waits for it and then for two animation frames.
- Helpers:
  - `P(t,a,b)`: progress of `t` through `[a, b]`
  - `eo`: expo out, for reveals
  - `eio`: cubic in-out, for camera moves and exits
  - `word()`: a masked reveal that hides the word once it is fully out
  - `quad()`: a homography that maps any HTML screen onto a device's screen quad with CSS `matrix3d`
- Measure layout once in setup, with the scene visible. A `display:none` scene measures as zero.
- Never put opacity or filter on a `preserve-3d` element; fade its wrapper instead.
- Image sequences swap `src` per frame and `await img.decode()`.
- **9:16 is its own re-layout**, never a pillarbox:
  - `const V = innerHeight > innerWidth`
  - stacked type, deeper zooms
  - key content kept above the bottom ~300 px, which is the caption zone on TikTok and Reels

## Score
1. `music.py trap stomp`: 2-4 ElevenLabs Music tracks (composition plan, 120 BPM). Things to know:
   - Max 2 concurrent requests.
   - Sections must be at least 3000 ms, and the model **ignores their timing**.
   - Naming an artist gets the plan rejected.
   - The key comes from `ELEVENLABS_API_KEY` only.
2. `analyze.py audio/*.mp3` finds, per track:
   - the drop downbeat D
   - the tempo
   - how much clean drop there is
   - the punch: jump dB, crest, low share
3. **Real drop-hit detection.** Generated builds often place one pre-drop hit, a beat of silence, and then the real drop.
   An energy-ratio search can land on the pre-hit. On one real track it found 7.36 s while the drop was at 8.17 s,
   a 0.8 s miss you hear on the reveal. `analyze.py` handles this in three ways:
   - It snaps D to the low-band kick onset that starts a sustained section, and rejects a hit followed by silence.
   - It backs up to the attack.
   - It reads tempo with a comb filter over the hi and low bands. Autocorrelation read triplet hats as 80 BPM.
4. `sfx.py cues.json` synthesizes the SFX stem (ticks, clicks, whooshes, risers, thumps, chimes and more), with
   each peak aligned to its picture event. It prints each cue's offset from the 8th-note grid; keep on-beat hits under 15 ms.
5. `build_score.py <mp3> <D> audio/master.wav` makes the bar-accurate edit:
   - the build ends on D at V4.0, then the drop
   - it detects dead stops and loops whole bars; `--max-drop` caps a track that dips mid-drop
   - an optional riser reprise, then the drop's first hit reused as the logo impact
   - SFX at 0.2, two-pass loudnorm to -14 LUFS
6. **Always verify** with `analyze.py --verify audio/master.wav 4.0`. The low band has to arrive within 30 ms of the
   picture's drop. If it doesn't, snap D to the kick grid (`kicks_from_D`) and rebuild.
7. Offer 2-3 score variants on the same picture. They are cheap: remux with `-c:v copy`.

## Render (`render.py`)
- Four Chromium workers render per-frame PNGs:
  - 3 subframes (±1/240 s) normally
  - 7-15 subframes over a 180° shutter inside the `fast` windows from the meta file
- Three subframes on a fast move give stepped ghosting that reads as a glitch.
- **Hard cuts are listed in `cuts`.** Subframes are clamped to the cut's side; if they aren't, a ghost of the previous scene shows on the first frame after every cut.
- **Warm-up pass:** each worker seeks through the whole timeline once before capturing. Without it, a worker that
  starts mid-range captures layers Chromium has not rasterized yet, and the text comes out washed out.
- **Paint wait:** after `seek(t)` the renderer waits for the promise and then for two `requestAnimationFrame`s before it captures.
- Frames are cached by filename. `DUR=2 MASTER=none` is the smoke test.
- Every run appends frames, seconds and workers to `out/render-log.txt`. That log is the cost basis.

## Deliverables (`poster.py`, `web_encode.py`)
- **Poster.** Bake the strongest *settled* frame (text fully in) into frame 0 of every master, so every platform's
  auto-thumbnail can be posted as is.
- **Web encodes.**
  - Long edge 1280 px at 30 fps.
  - H.264 High with `+faststart`, plus VP9 WebM.
  - The CRF is searched until each file lands in **1.5-3 MB**. On today's builds a 19 s site cut landed at 1.1-1.6 MB
    and a 31-39 s walkthrough at 1.6-3.0 MB.
- **Two embed modes.** `web_encode.py` writes the snippet:
  - **Muted autoplay loop** for short pain videos: `autoplay muted loop playsinline preload="none"`, poster first,
    WebM then MP4, and reduced motion respected.
  - **Click-to-play** for walkthroughs and anything with music: `controls preload="none"`, poster, no autoplay.
- **Social.** The 9:16 master at native resolution, plus `out/share-copy.txt` for each video with:
  - a YouTube title
  - a 1-3 sentence caption (specific, never "excited to share")
  - a TikTok/Reels caption with no link ("link in bio")
  - hashtags
- **Site-embed kit** (`site-embed.md`) for a set:
  - the file list per video
  - title, caption and alt text for each one
  - the suggested section and order on the page
  - the grid snippet

## Taste rules (each one cost a redo on a real build)
- **Content**
  - Real, good footage only: graded stock and real UI, never cartoony or low-grade picks.
  - Use the official wordmark file; never retype a logo.
  - Show only the newest UI, in tight readable crops, never a whole spinning page.
  - Avoid demo cruft in frame ("N/A", "Missed", placeholder rows).
- **Claims**
  - Never invent features, customer stats or testimonials.
  - Roadmap features the client already claims publicly may appear. List them in the report as roadmap.
  - Match each feature to the screen it belongs on: office-only features don't go in mobile vertical ads.
- **Motion**
  - High-end minimal: one idea per shot, lots of space, one accent, one clean sans, tight tracking, no full stops.
  - Masked type reveals, rolls, match cuts, one camera language (slow push, or a whip with motion blur).
  - Banned: shockwave rings, particle bursts, RGB split, camera shake, lens flares, neon glows, grid floors,
    flashing backgrounds, bouncy easing, glitch transitions.
- **Music** must hit. Polite corporate electronic fails. A launch is hype whatever the brand looks like; calm or ambient only when the client asks.
- **Process**
  - Watch the whole thing back and fix it before anyone sees it.
  - Nothing is posted without the owner's approval for that specific post.

## Watch-back QA (`qa.py`): bugs this pipeline actually shipped

| Symptom in a render | Cause | Fix |
|---|---|---|
| Outgoing and incoming words overlap mid-swap | two masked words animated independently in one slot | true stacked roll: `y_new = y_old + 110%` |
| 1 px sliver of a word after it exits | mask padding keeps descenders visible at -110% | `visibility:hidden` once `abs(y) >= 100%` |
| A word reappears next to its replacement | a `visibility:visible` child inside a `hidden` parent still shows | hide the child itself |
| Stepped ghost copies on whips and zooms | 3 subframes on fast motion | add the window to `fast` (7-15 subframes) |
| Mirrored text on the back of 3D cards | back faces visible | `backface-visibility:hidden` |
| Black frame on a downbeat cut | new scene entered at opacity 0 | cuts show content immediately; animate transform, not opacity |
| Faint ghost of the previous scene after every cut | a subframe lands before the cut | list every hard cut in `cuts` |
| Washed-out or blank text on a re-rendered range | capture before paint / unrasterized layer | warm-up pass + two-rAF paint wait (built in) |
| Strike-through or highlight in the wrong place | layout measured while the scene was `display:none` | measure with the scene visible |
| Encoded video at the wrong speed or length | leftover blend filter after switching to pre-blended frames | encode with `format=yuv420p` only; check frames and duration with ffprobe |
| Music drop not on the reveal | ElevenLabs ignores section timing; pre-drop hit misread as the drop | `analyze.py` snap + `--verify` on the master |
| Drop stops dead mid-video | the track stops inside its "drop" | `build_score.py` trims to whole bars and loops; `--max-drop` |
| Stats unreadable because each one replaces the last | push-cut replacement at beat speed | stack them: each lands on its 8th note and stays |
| Private data readable in a walkthrough | blur missed a field, or a plain Gaussian left glyphs | read every `priv_NN.jpg`; add boxes; the blur downsamples first |
| Muted site cut makes no sense | the story lived in the music or VO | burned-in text must carry it; review muted |

Check the whole video every time, not just the section you changed. Also:
- Check every frame at phone size: 16:9 at about 900 px wide, 9:16 at about 540 px.
- **Size minimums:**
  - 9:16: the hero device is at least 70% of frame width, UI body text at least 34 px, titles at least 40 px, label lists at least 48 px.
  - 16:9: UI text at least 28 px.
  - Footnotes at least 26-30 px.
- **Final checks:**
  - ffprobe: size, fps, frame count and duration match the meta
  - integrated loudness -14.0 LUFS
  - SFX peaks within 15 ms of the grid
  - `--verify` on the drop
  - frame 0 is the baked poster
  - a tile sheet of the whole video, plus dense tiles at every cut

# Motion Spot Service Playbook: selling code-rendered video as a service

This is how to package `/kai-motion-spot` as a paid deliverable. The method is in `motion-spot-method.md`.
The sections marked **INTERNAL** never appear on anything a customer sees: a proposal, a page, an invoice note, or an email.

## Deliverables menu

| Package | What the client gets | Typical length |
|---|---|---|
| **Launch spot** | A 16:9 master plus a re-laid-out 9:16 with the same hype score. 2-3 score variants to choose from. Baked posters, share copy per platform, and web encodes with an embed snippet | 20-30 s |
| **Walkthrough set** | One walkthrough per feature (typically 3-5), built from real screenshots with the privacy blur. 16:9 for each, plus 9:16 for the hero feature. Click-to-play web encodes, posters, and an embed kit | 30-40 s each |
| **Pain-point set** | One short video per customer pain (typically 4-6). A muted autoplay site cut with burned-in text, a scored social cut, and a 9:16. Plus a site-embed kit: titles, captions, alt text, grid placement and snippet | ~19 s each |
| **Social cuts** (add-on) | The 9:16 re-layouts, share copy (YouTube title, caption, TikTok/Reels caption, hashtags) and posting, once the owner approves each post | per video |

Every package includes: one score direction, a poster frame per video, H.264 and WebM web encodes, and one revision round after the review cut.

## Inputs needed from the client

1. **The one-line promise** and the 3-5 moments to show (for pain-point sets, the list of pains, in the customer's own words).
2. **Product access or captures**:
   - screen recordings of the newest UI, or
   - a demo account we can screenshot, or
   - screenshots at normal zoom.
   Tell us which data is real and has to be blurred.
3. **Brand kit**:
   - the official wordmark and logo files (SVG preferred)
   - the accent color
   - the typeface, if it isn't a Google Font
4. **Claims we are allowed to make.** Features that are live, features publicly on the roadmap, and any numbers the
   client can source. We never invent stats, customers or testimonials.
5. **Destinations**: the site sections the videos will sit in, and the social accounts. For posting, the account owner
   connects the accounts to the posting tool; we never handle their passwords.
6. **Approver.** One named person who signs off the review cut and each public post.

## Turnaround (from complete inputs)

| Package | Review cut | Final after feedback |
|---|---|---|
| Launch spot | 1-2 working days | +1 day |
| Walkthrough set (5) | 2-3 working days | +1 day |
| Pain-point set (6) | 2 working days | +1 day |
| Social cuts | same day as the final | same day |

These are real numbers. On 2026-09-30 one production day produced a launch spot (16:9 and 9:16), five walkthroughs plus
a 9:16, and six pain-point videos in both formats, with the web encodes and embed kits. The quoted windows leave room
for client review and one revision.

## QA checklist (every video, before the client sees it)

- [ ] The story makes sense with the sound **off** (site cuts) and **on** (social cuts)
- [ ] Every line meant to be read stays fully on screen and settled for at least 0.3 s per word
- [ ] Privacy pass: every `priv_NN.jpg` sheet has been read and no real name, email, phone number, quota or id is legible
- [ ] Only the newest UI; no demo cruft; no invented features, stats or testimonials; roadmap claims listed
- [ ] Official logo files, never retyped
- [ ] Dense tiles at every cut: no ghost frame, no black frame, no stepped ghosting on fast moves
- [ ] The drop lands on the reveal (`analyze.py --verify` within 30 ms); loudness -14 LUFS; SFX on the grid
- [ ] ffprobe matches the spec: size, 60 fps master, frame count, duration
- [ ] Frame 0 is the baked poster; the poster is a settled frame
- [ ] Web encodes are 1.5-3 MB, start fast (faststart), and play in Chrome and Safari; the WebM plays first
- [ ] Checked at phone size: 16:9 at 900 px, 9:16 at 540 px; nothing important in the bottom ~300 px of the 9:16

## Approval step

1. Send the **review cut**: the 16:9 master, the 9:16, the score variants and a contact sheet.
2. The approver picks the score, confirms the claims, and sends one consolidated round of changes.
3. Deliver the **final**: masters, posters, web encodes, the embed kit and share copy.
4. **Publishing is a separate approval.** Nothing is posted until the owner says yes to that specific post.
   `upload_post.py` runs as a dry run until then.

## Pricing

**Price: founder decision.** Nothing in this playbook sets it.

Public market reference points (retrieved 2026-09-30):
- Published prices for animated product launch videos run from about $2,700 (Wyzowl, fixed price) and $3,480 per
  60-second project in six working days (Motion The Agency), up to $10,000+ (Apollo Studio) and $40,000+
  (Venture Videos launch projects). Source: https://www.getmiyagi.com/post/best-product-launch-video-agencies
- The same source lists What a Story at $2,500-$25,000 per asset and Videodeck at $5,000 per video ($2,000-$3,000 per
  video on volume plans), with turnarounds from six working days to ten weeks.
- Freelance motion designers: explainer or animated video at $1,000-$4,000+ per video, with full videos running
  $1,000-$16,000 by complexity. Source: https://freelancewitherica.com/library/video-audio/motion-graphics-animation

Our structural edge over those studios is turnaround measured in days, and a set of videos from one production
instead of one video per project.

## Cost basis — INTERNAL (never on a customer-facing artifact)

| Cost | Basis | Measured on the 2026-09-30 builds |
|---|---|---|
| **Music** | ElevenLabs Music, per generated track (~30 s each). Generate 3-5 per production to pick from, then reuse one score across the set | 5 tracks generated for the launch spot; the pain-point and walkthrough sets reused them (0 new tracks). Current rates: https://elevenlabs.io/pricing (a third-party review reports about $0.15 per minute of music on the API: https://www.cekura.ai/blogs/elevenlabs-pricing) |
| **Render compute** | Local Chromium workers, from `out/render-log.txt` | Launch spot 27 s, 16:9 (1,620 frames): 345 s. Pain-point 19 s (1,140 frames): 187-337 s per format for a full render; 35-95 s for a partial re-render. Walkthroughs 31-39 s (1,860-2,340 frames): 377-678 s per video on the first full render; 113-158 s for re-renders |
| **Encode** | ffmpeg on the same machine | A few minutes for a whole set of web encodes |
| **Agent and operator time** | Brief, assets, page build, QA passes, revisions | The main cost. Track it per job |
| **Posting** | Upload-Post plan, if the client doesn't have their own | Per the client's plan |

Render compute is negligible next to operator time: roughly 3-11 minutes of machine time per video per format, on an ordinary laptop.

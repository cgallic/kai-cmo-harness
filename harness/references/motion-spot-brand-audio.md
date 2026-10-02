# Motion Spot brand audio: music direction per brand, legal sourcing, and scoring to non-grid music

This is the audio companion to `motion-spot-method.md`. The method's default score is a generated hype track on a
120 BPM grid. This note covers the other case: a brand whose music direction is existing, well-known music
(for example classical) that has no fixed grid and whose recordings carry their own rights.

## 1. Music direction per brand

Write the direction down once per brand and reuse it for every spot. The brand owner usually gives it as a playlist or a
few reference tracks. Record the pieces, the energy and the hard rules.

| Brand | Direction | Launch spots | Walkthroughs | Short social cuts |
|---|---|---|---|---|
| KaiCalls / KaiPhone | Hype hybrid-trap (generated, `music.py`) | Hard drop on the reveal | A bed cut from the launch score | Same score, bar-cut |
| Talk To Gina | Epic, well-known classical (the owner's "TTG Classical" playlist): Valkyries, Mountain King, William Tell finale, Firebird finale, Mars, Beethoven 9, Verdi Dies irae, Four Seasons, Bald Mountain, Bumblebee, Blue Danube, Figaro, Can-can, Zarathustra | The biggest, most driving excerpts (Valkyries, Mountain King, William Tell finale) | Lighter pieces, one per video (Vivaldi Spring, Figaro overture, Can-can) | Short, punchy excerpts matched to the pain (Bumblebee = frantic, Bald Mountain = dread, William Tell = race the clock) |

The launch energy rule from the method still applies: launch audio is never calm, whatever the genre.
Offer 2-3 variants on the same picture and let the owner pick.

## 2. Legal sourcing (hard rules)

The **composition** and the **recording** are two separate rights. A 19th-century score is public domain; almost every
recording of it is not.

- **Never** use Spotify, YouTube rips, or any commercial recording, even of a public-domain piece.
- **Allowed recordings**: public domain, CC0, Public Domain Mark applied by the owner, or CC BY (attribution recorded).
  Not allowed: CC BY-SA (share-alike would bind the video), any NC or ND license, "royalty free" without a license text.
- **Check the composition too.** A composer who died fewer than 70 years ago may still be protected in the EU/UK, and some
  countries run life+100 (Mexico). If in doubt, skip the piece. Worked examples:
  - Stravinsky *Firebird* (1919 suite): protected in the EU/UK until the end of 2041. Skip.
  - Holst *Mars*: PD in the US/EU/UK, still protected in life+100 countries, and the PD band recording found was a modern
    transcription of unclear status. Skip.
  - R. Strauss *Zarathustra*: PD in the US (published 1896) and in the EU/UK since the end of 2019. Usable.
- **Arrangements carry their own copyright.** A PD band performance of a modern, unnamed wind arrangement is not clean.
  A PD band recording is fine when the arranger was a service member (a US government work) or 19th century (Sedlak's William Tell).
- **Verify the license at the source, not the label.** Internet Archive uploaders sometimes put a PD mark on commercial
  LPs (a 1966 Decca LSO Valkyries). Read the Commons file page wikitext (`action=raw`) for the license templates, or the
  rightsholder's own statement (a YouTube description that grants CC BY is a valid source; check it says so).
- **Content ID risk.** A PD recording that is also distributed commercially (Naxos/Altissimo reissues of US military bands)
  gets auto-claimed on YouTube. Prefer recordings that are not commercially reissued, and keep the manifest ready for disputes.

### Where to look

| Source | What you get | Check |
|---|---|---|
| Wikimedia Commons audio (API `list=search&srnamespace=6`, `prop=imageinfo&iiprop=extmetadata`) | Musopen, US military bands, IMSLP, CC BY productions | `LicenseShortName` + the file page's license templates |
| Musopen (via Commons or the Internet Archive `musopen-lossless-dvd-flac`) | Orchestral PD recordings (Musopen Symphony = Czech National SO, 2012 Kickstarter) | Each track's own license; Musopen asks for a courtesy credit |
| US military bands (`music.af.mil` public-domain page, Marine Band archive) | Performances that are US government works | The arranger (see above) |
| IMSLP recordings | Mixed | Many are CC BY-SA: excluded |
| Internet Archive | Mixed, often mislabelled | Date + origin, not only `licenseurl` |
| Creator CC BY releases (e.g. Philip Milman / "Lud and Schlatt's Musical Emporium": Valkyries, Zarathustra, Winter) | Modern orchestral productions | The creator's own license statement |

### The manifest

Every file goes into `music/manifest.csv`: file, piece, performer, source page, download URL, license, license URL,
attribution text, composition status, where it is used, date verified. Skipped pieces go in too, with the reason.
Copy the manifest next to the deliverables.

### Attribution in the share copy

- **CC BY**: full credit with the license link in the YouTube / LinkedIn / X description, for example
  `Music: "Ride of the Valkyries" (Wagner), conducted by Philip Milman, funded by Ludwig & Schlatt. Licensed CC BY 3.0 (creativecommons.org/licenses/by/3.0).`
  TikTok / Reels / Shorts captions stay link-free, so add a short credit line with no link instead.
- **Public domain**: no credit required. A courtesy credit ("Musopen Symphony via Musopen.org") in the YouTube description costs nothing.

### Synthesized fallback

A MIDI render of a PD score through an orchestral soundfont (fluidsynth) is legal. Use it only if it sounds convincing
next to a real orchestra. Choir pieces (Dies irae) never do. Otherwise skip the piece.

## 3. Beat-mapping for non-grid music

Classical has rubato, accelerando and fermatas, so the method's 120 BPM bar grid does not apply. The picture's
timeline stays fixed; the music is edited and gently re-timed to it.

1. **Analyze each recording** (librosa): beat track, onset envelope, low-band accent for downbeat phase, RMS per 2 s,
   and a ranked hit list (onset peak × level jump). Plot spectrogram + RMS + onsets with beats and hits marked, and look at it.
   You cannot hear the result, so you read the picture of it.
2. **Name the video's anchors.** Must-hit: the drop (the first reveal after the hook), the logo/end-card hit, and every
   splice point. Soft: the other scene cuts.
3. **Choose excerpts by energy.** The hook (0-4 s) should build into a real attack: a crescendo, or a beat of silence
   before a tutti (William Tell's pause before the stretta is ideal). The logo takes a final chord with a natural decay,
   so the last 3 s ring out instead of being faded mid-phrase.
4. **Search the splice.** Between drop and logo there is usually too much music. Search every pair (outgoing ends just before
   hit/beat HB, incoming starts on hit HC, HC lands on a scene cut) with both segments' tempo in 0.93-1.08, and rank by tempo
   deviation, incoming-hit strength and chroma similarity across the join (0.8+ = harmonically seamless). Loop-backs inside a
   repetitive stretta are fine.
5. **Re-time, don't re-cut.** Each segment is time-stretched (ffmpeg `rubberband`, crisp transients) so its source span fits
   its video span exactly. Soft anchors get a warp point on the nearest strong beat only if every piece stays within 0.93-1.075;
   otherwise leave that cut unanchored. Bigger swings are audible as tempo lurches.
6. **Joins.** The incoming hit lands on the anchor at full gain (a 30 ms fade-in before it). At a splice the outgoing segment
   must stop about 60 ms **before** its own next attack, or that attack leaks under the incoming one and the hit reads
   40-50 ms early. Contiguous warp joins use a 15 ms crossfade on a beat.
7. **Retime the picture only as a last resort.** If a big moment cannot land within tolerance, move the cut in the page and
   re-render that frame range; otherwise keep the picture byte-identical and remux (`-c:v copy`).
8. **Master.** Normalize the music bus, lay the SFX stem under it (about -14 to -16 dB), two-pass loudnorm to -14 LUFS / -1 dBTP,
   then measure again and trim the residual with a limiter to get -14.0 ± 0.1.

### QA

- **Hit alignment**: onset envelope of the final mix (hop 128); every must-anchor's nearest peak within **40 ms**, peak at least
  2× the local mean. Run it on the final MP4 (AAC), not only the WAV.
- **Spectrogram** of the whole mix with anchors drawn: no clicks or smears at joins, no dead air except where intended.
- **Loudness**: ebur128 integrated -14 LUFS (±0.2 after AAC), true peak about -1 dBTP.
- **Picture unchanged**: the video-stream MD5 of the remux equals the original; frame count and duration match.
- **Watch-back**: frames at each anchor (±0.1 s) show the event (the reveal, the cut, the logo) exactly on the hit.
- **No recording without a verified license** in the manifest.

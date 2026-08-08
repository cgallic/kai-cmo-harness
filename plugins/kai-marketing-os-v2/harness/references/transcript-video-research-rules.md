# Transcript and Video Research Rules

Last researched: 2026-06-17

Use this before any Kai workflow mines YouTube videos, podcast episodes, webinars, event recordings, sales calls, interviews, X Spaces, livestreams, or clips for claims, quotes, content atoms, or source-backed patterns.

Primary sources:
- YouTube visible transcript help: https://support.google.com/youtube/answer/15930243
- YouTube Terms: https://www.youtube.com/static?template=terms
- YouTube API Services Terms: https://developers.google.com/youtube/terms/api-services-terms-of-service
- YouTube API Services Developer Policies: https://developers.google.com/youtube/terms/developer-policies
- YouTube Data API captions docs: https://developers.google.com/youtube/v3/docs/captions
- YouTube paid promotion declarations: https://support.google.com/youtube/answer/154235
- YouTube altered or synthetic content disclosure: https://support.google.com/youtube/answer/14328491
- FTC endorsement and influencer guidance: https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews
- U.S. Copyright Office fair use FAQ: https://www.copyright.gov/help/faq/faq-fairuse.html

## Allowed Sources

- Public YouTube videos when a visible transcript panel is available and the workflow records the URL, title, channel, transcript source, and reviewed timestamps.
- Caption or transcript files provided by the publisher, speaker, event host, podcast host, or client.
- YouTube Data API caption resources only for owned or otherwise authorized workflows that comply with YouTube API Services Terms and Developer Policies.
- User-provided recordings, transcript exports, notes, or files when the user has rights to use them.
- Manual notes from watching or listening to public material.
- Podcast RSS metadata, public show notes, and public episode pages.

## Blocked Sources

- Private, member-only, course, paywalled, deleted, login-gated, or restricted video/audio.
- Unofficial transcript extractors whose access method is unclear or not approved for the account/workflow.
- Audio or video downloads through `yt-dlp` or similar tools unless the asset is owned, licensed, user-provided, or otherwise explicitly authorized.
- Full transcript storage for third-party copyrighted material unless the owner provided the transcript or the client has rights.
- Long excerpts, stitched short excerpts, full Q&A sections, or speaker monologues in deliverables.
- Claims from transcripts without URL or file locator, timestamp or line locator, source type, retrieval date, and risk note.

## Required Ledgers

Create these artifacts for transcript-heavy research:

| Artifact | Required Fields |
|---|---|
| `_source-ledger.md` | URL/file, owner, access type, retrieved date, evidence tier, use, rights note |
| `_transcript-ledger.md` | title, channel/speaker, source type, timestamps reviewed, quote count, extraction notes |
| `_quote-bank.md` | short quote or paraphrase, timestamp/line, speaker, use case, risk, approval state |
| `_rights-notes.md` | permission status, usage limits, public/private status, blocked actions |

## Quote Limits

- Prefer paraphrase and pattern extraction.
- Quote only when wording itself is evidence.
- Keep direct quotes under 25 words per non-lyrical source in a deliverable.
- Attribute every direct quote with speaker or channel, title, URL or file, timestamp/line, and retrieved date.
- Do not combine many short excerpts to recreate the original source.

## Publication Gate

Before publishing, scheduling, uploading, emailing, clipping, or adding transcript-derived material to a client-facing deck:

- [ ] Rights or usage status is known.
- [ ] Privacy scan has run for customer, health, legal, financial, account, and confidential details.
- [ ] Every direct quote has a timestamp or line locator.
- [ ] Every factual claim has a source ID or is labeled as a hypothesis.
- [ ] Quantitative claims follow `harness/references/audit-data-provenance.md`.
- [ ] Platform-specific policy refs are loaded for every destination channel.
- [ ] Human approval is recorded for guest, customer, client, or third-party clips.
- [ ] No full transcript, long excerpt, or source reconstruction is present in the output.

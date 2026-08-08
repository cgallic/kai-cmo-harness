# Local Business Claymation Ad Pipeline

## Use When

Use this playbook when Kai needs a productized local business offer built around sample AI video ads.

The workflow is:

```
discover leads -> score weak creative -> create sample concept -> pitch -> sell 2-4 videos/month -> fulfill
```

The pipeline must run in dry-run mode until the user approves asset generation or outbound sends.

## Best Niches

Prioritize visual, local, repeat-purchase, or high-ticket categories:

- Gyms and fitness studios.
- Restaurants, bakeries, cafes, and food trucks.
- Salons, spas, med spas, and barbers.
- Dentists, orthodontists, and cosmetic clinics.
- Plumbers, HVAC, roofers, electricians, and home services.
- Event venues and party rental companies.
- Pet services and local retail.

## Lead Discovery Fields

Capture:

- Business name.
- Category.
- City and state.
- Website.
- Phone.
- Email or contact URL.
- Address.
- Rating and review count.
- Facebook, Instagram, TikTok, YouTube, and LinkedIn URLs.
- Active or recent ad evidence when available.
- Notes on creative weakness.

## Weak-Creative Signals

Score every lead using these signals:

| Signal | Points | What It Means |
|--------|--------|---------------|
| No video creative | 3 | Mostly static posts or no short-form video. |
| Generic stock visuals | 3 | Looks interchangeable with any business. |
| Weak CTA | 2 | No clear next action. |
| Poor offer clarity | 2 | Viewers cannot tell what to buy or book. |
| No local specificity | 2 | No neighborhood, city, staff, menu, service area, or local proof. |
| Stale creative | 2 | Social or ad creative has not changed recently. |
| Low production quality | 2 | Hard-to-read text, rough edits, weak audio, or bad cropping. |
| Strong reviews but weak ads | 3 | The business has proof but does not use it. |

Score bands:

- 0-3: poor fit.
- 4-7: monitor.
- 8-11: good target.
- 12+: sample-worthy.

## Sample Ad Concept

For every sample-worthy lead, create:

1. Concept angle.
2. Storyboard.
3. 20-30 second script.
4. Shot list.
5. Voiceover copy.
6. CTA.
7. Clay-style frame prompts.
8. Animation handoff notes.
9. Voiceover notes.
10. CapCut assembly plan.

## Tool Handoff

| Step | Tool | Output |
|------|------|--------|
| Concept and script | Claude | Storyboard, hook, CTA, voiceover copy. |
| Frames | Fal.ai or image model | Clay-style key frames. |
| Animation | Kling AI or video model | 4-8 second motion clips. |
| Voice | ElevenLabs or local TTS | Narration track. |
| Edit | CapCut or Remotion | Final sample video. |

Every generated asset should keep a prompt, source, date, and usage note.

## Outbound Pitch

Each pitch needs:

- One sincere local observation.
- One specific creative gap.
- A mention of the sample concept or sample video.
- A direct 2-video or 4-video monthly offer.
- One low-friction CTA.

Channels:

- Email.
- SMS if consent and law allow it.
- Instagram DM.
- Cold call opener.

## Retainer Packages

### Starter: 2 Videos/Month

- 2 short videos.
- 2 hooks per video.
- Captions and CTA copy.
- One revision pass.
- Monthly creative report.

Use for small local businesses that need consistency.

### Growth: 4 Videos/Month

- 4 short videos.
- 3 hooks per video.
- Platform-specific crops.
- Two revision passes.
- Monthly creative report.
- Quarterly offer refresh.

Use for businesses with active ads or weekly promotions.

## Status Tracking

Track every account with one of these states:

1. sourced
2. qualified
3. sample_created
4. contacted
5. replied
6. booked
7. closed
8. fulfilled
9. nurture
10. disqualified

## Dry-Run Command

Run without external side effects:

```bash
python scripts/leads/claymation_pipeline.py --input leads.csv --output workspace/claymation/dry-run.json --dry-run
```

Dry-run output includes lead scoring, a concept, storyboard, tool handoff, outbound copy, and package recommendation.

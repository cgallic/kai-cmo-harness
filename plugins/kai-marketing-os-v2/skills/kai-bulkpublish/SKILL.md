---
name: kai-bulkpublish
description: Prepare an approved social content queue for BulkPublish scheduling or publication. Use when "schedule social posts", "publish the calendar", "send posts to BulkPublish", or "hand off approved social content".
---

# /kai-bulkpublish — Approved Posts, Scheduled Exactly as Approved

## Objective

Every approved post from a reviewed calendar (from `/kai-social`, `/kai-repurpose`, or similar) exists in BulkPublish as a draft or approval-gated scheduled post on the right channel, time, timezone and media, and a campaign record lists each returned post id, status, schedule and per-platform failure. Nothing unapproved leaves the queue; nothing publishes without an immediate go-ahead.

## Done when

Work type `social-post` (`harness/eco-floors.yaml`), per post: the record holds BulkPublish post id, channel, status, IANA-timezone schedule and any platform error. A post reaches E5 only when BulkPublish returns an id after publication and the public post matches the approved text. Outcomes come from BulkPublish analytics against the campaign objective.

## Constraints

- Only posts with an explicit approval state; drafts and rejected posts are removed.
- Each post meets its platform's character, link, media and format rules before submission.
- Channel ids come from BulkPublish `list_channels`, never inferred from names.
- Scheduling and publishing are external side effects: show post count, channels, media and schedule, and get immediate authorization from the person allowed to publish.
- No API keys, cookies or private analytics in content, records or logs. No guaranteed engagement, reach or revenue.

## Context

Platform rules: `harness/references/*-organic-posting-rules.md`, `harness/references/social-automation-rules.md`. BulkPublish API: https://github.com/azeemkafridi/bulkpublish-api · MCP docs: https://app.bulkpublish.com/docs

## Escalate when

- Audience, account, channel, media or schedule is ambiguous, or a channel name matches zero or several channels.
- A platform rejects a post and the fix would change approved copy or media.

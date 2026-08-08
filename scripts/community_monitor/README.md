# Community Opportunity Monitor

Source-neutral setup for finding public conversations, reviews, support threads,
and AEO-cited URLs worth human review. It stores full original text when the
provider exposes it, exact evidence, source provenance, human posting proof,
later outcomes, and indexing checks. It never drafts or publishes responses.

## Sources and access

| Source | Default access | Setup |
|---|---|---|
| Reddit | Public submission feed | Configure subreddits in the existing Reddit profile |
| Hacker News | Direct public API | No credential |
| Lobsters | Direct public API | No credential |
| YouTube comments | Official API | Set `YOUTUBE_API_KEY`; enable only after a provider read-back |
| LinkedIn public posts | Authenticated file drop | Export approved public candidates into the configured import directory |
| Quora | Indexed-public search | Configure `site:quora.com` queries |
| G2/Capterra | Indexed-public search | Configure review queries; do not scrape authenticated pages |
| Google reviews | DataForSEO when installed; indexed fallback | Configure provider credentials or public queries |
| Public operator forums | Indexed-public search | List allowed forum domains |
| Competitor support communities | Indexed-public search | List allowed public support domains |
| AEO citations | Citation-event import | Import append-only events; explode URLs from each `sources[]` field |

`indexed_public` means the search provider found a public page. It does not mean
the monitor has a first-party API or complete platform coverage.

## Install

1. Copy `profiles/example.json` to a client profile.
2. Replace brand terms, keywords, domains, and queries.
3. Leave credentialed sources disabled until their environment variables are present.
4. Validate the profile against `profile.v2.schema.json`.
5. Point the runtime at a durable directory such as
   `runtime/community-monitor/<profile-id>`.
6. Run read-only collection on a six-hour source cadence.
7. Project normalized opportunities into the dashboard on a shorter cadence.
8. Register freshness, provider-error, and zero-result-tolerance tripwires.

## Provider variables

```text
YOUTUBE_API_KEY=              # optional official commentThreads access
DATAFORSEO_AUTH_B64=          # optional indexed search and Google reviews
OPENAI_API_KEY=               # optional evidence scoring
OPENROUTER_API_KEY=           # optional evidence scoring alternative
```

## Import envelope

File-drop and citation adapters accept JSONL. Each record contains:

```json
{
  "source": "linkedin_public_posts",
  "source_mode": "authenticated_file_drop",
  "title": "Public post title",
  "original_text": "Full captured public post",
  "original_text_is_full": true,
  "url": "https://www.linkedin.com/posts/...",
  "observed_at": "2026-08-08T12:00:00Z",
  "provenance": {"collector": "approved-browser-export"}
}
```

AEO events use the existing event shape with `provider`, `query`, `sources[]`,
`answer_excerpt`, and `ts`. Every cited URL becomes a separately deduplicated
opportunity. Preserve the answer excerpt as provenance, not as the original post.

## Safety

No adapter may comment, message, vote, review, or publish. A person opens the
source, follows its rules, posts manually, and stores the exact public permalink.
The follow-up loop checks proof availability, search indexing, and later outcomes.

# Reddit Intelligence backend

Brand-neutral pipeline for turning an approved, read-only Reddit export into a
persistent opportunity bank, urgent-alert previews, a weekly-digest preview,
and content briefs. It never posts, messages, votes, emails, or edits a Sheet.

Run from the repository root:

```text
python -m scripts.reddit_monitor.intelligence.cli --profile scripts/reddit_monitor/intelligence/profiles/example.json --input reddit-export.jsonl --output-dir runtime/reddit-intelligence/example

# Or collect the public submission RSS sources enabled in the profile:
python -m scripts.reddit_monitor.intelligence.cli --profile scripts/reddit_monitor/intelligence/profiles/example.json --collect --output-dir runtime/reddit-intelligence/example
```

Input rows use `id`, `title`, `body`, `url`, `subreddit`, `author`, and optional
`published_at`. A profile owns brand terms, grouped keywords, group-local
qualifiers, geography terms, thresholds, and workflow statuses. Output files
are stable dashboard/adaptor contracts. `run-manifest.json` always records
`mode: dry_run` and an empty `external_effects` list.

Machine-readable contracts are `profile.schema.json` and
`opportunity.schema.json`. The cross-harness artifact contract is
`harness/skill-contracts/reddit-intelligence.yaml`.

`--activate-sheets` and `--activate-email` deliberately fail closed until an
approved provider adapter is installed. Reddit write operations have no API or
activation option in this module.

Launch the dependency-free dashboard/API after a run:

```text
python -m scripts.reddit_monitor.intelligence.dashboard --profile scripts/reddit_monitor/intelligence/profiles/example.json --data-dir runtime/reddit-intelligence/example
```

The local dashboard shows setup and activation state, editable profile JSON,
opportunity filters/status controls, and urgent/digest/brief previews.
`GET /api/state`,
`GET|PUT /api/profile`, and `PATCH /api/opportunities/<id>` are the dashboard
contracts. Bind to `127.0.0.1` unless access controls are provided upstream.

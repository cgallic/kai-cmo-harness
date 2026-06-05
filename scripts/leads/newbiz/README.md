# newbiz — new-business-formation outreach data pipeline

Implements §11 of `brain/wiki/guides/kaicalls-new-business-formation-outreach.md` — the **free-states data pilot** for the postcard + email + human-call sequence to newly-registered businesses.

Pulls FL Sunbiz daily LLC filings → filters to active formations within window → drops the registered-agent trap → enriches with Google Places (signal-only, ToS-safe) + Apollo (stored phone) → scores **P1/P2/P3** → emits a CSV ready for the mail / email / human-call legs.

## What's here

| File | Job |
|---|---|
| `sunbiz_fl.py` | SFTP fetch + fixed-width parse (1440 chars/record) + filter |
| `ra_blocklist.py` | Formation-service blocklist (LegalZoom, Northwest, ZenBusiness, …) |
| `enrich.py` | Google Places signal lookup + Apollo stub + priority scoring |
| `dedupe.py` | SQLite store keyed by `(state, entity_id)` |
| `pipeline.py` | CLI orchestrator (this is what you run) |

## Setup

```bash
# One-time
sudo apt-get install -y sshpass   # for the Sunbiz SFTP pull
pip install -r scripts/requirements.txt   # requests + python-dotenv
```

Optional env vars (enrichment is gated; pipeline runs without them):

```bash
export GOOGLE_PLACES_API_KEY=...   # Places signal lookup
export APOLLO_API_KEY=...          # Apollo enrichment (stored phone)
export SUNBIZ_SFTP_PASS=...        # only if FL rotates the public password
```

## 500-prospect FL pilot

```bash
# 1) Smoke test — yesterday's file, no enrichment, just verify parse + filter
python -m scripts.leads.newbiz.pipeline pull \
    --date 2026-05-27 --no-enrich \
    --out workspace/newbiz/smoke.csv

# 2) Two-week window with Places + Apollo enrichment + 500-row cap
python -m scripts.leads.newbiz.pipeline pull \
    --since 2026-05-13 --until 2026-05-27 \
    --limit 500 \
    --out workspace/newbiz/fl_pilot_500.csv
```

Output is `workspace/newbiz/fl_pilot_500.csv` with one row per outreach-ready LLC and a priority score. Records are stored in `workspace/newbiz/dedupe.sqlite` so future runs won't re-emit the same business.

## Priority scoring

After Places + Apollo enrichment:

- **P1 (hottest)** — no phone, no website. Business has zero phone infrastructure yet → exact KaiCalls pitch.
- **P2** — website but no listed phone. Discoverable but not capturing calls.
- **P3** — has phone. Upgrade pitch (Kai answers when they can't); still useful for the call leg.
- **P_unknown** — `--no-enrich` mode (no keys set).

## What this does NOT do (by design)

- Send mail / email / calls. Handoff is a CSV — feed it into Lob/Postalytics (mail), Instantly `kai@trykaicalls.com` (email — only with email-licensed enrichment), or a human dialer (calls). **Never** point the SDR AI auto-dialer at this list (FCC 24-17).
- Cache Google Places content beyond `place_id` + derived booleans. The Places ToS forbids it; use Apollo or a storage-permitted scraper for the stored, dialable phone.
- Cross-state. FL only for the pilot. CA CALICO, CO open-data, NY + OpenSOSData enrichment, OH monthly = next pullers.

## Other state pullers (next)

Slot beside `sunbiz_fl.py` and reuse `enrich.py` / `dedupe.py` / `pipeline.py`:

- `ca_calico.py` — CALICO API (near real-time, principal addr)
- `co_socrata.py` — Colorado open-data weekly
- `ny_gov.py` — formation-date monitor → OpenSOSData for principal addr
- `oh_sos.py` — monthly report download

Add each as a new source under `pipeline.py`'s puller dispatch.

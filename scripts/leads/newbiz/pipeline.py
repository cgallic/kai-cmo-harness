#!/usr/bin/env python3
"""KaiCalls new-business outreach pipeline — FL Sunbiz pilot.

Pulls one or more days of FL Sunbiz cor filings, filters to active LLCs
filed within the window, drops the registered-agent-trap rows, enriches via
Google Places (signal-only) + Apollo (stored phone), scores P1/P2/P3,
dedupes across runs, and writes a CSV ready for the postcard / email /
human-call legs.

Implements §11 of:
  brain/wiki/guides/kaicalls-new-business-formation-outreach.md

Usage:
    # Single day:
    python -m scripts.leads.newbiz.pipeline pull \
        --date 2026-05-27 \
        --out workspace/newbiz/fl_2026-05-27.csv

    # Window:
    python -m scripts.leads.newbiz.pipeline pull \
        --since 2026-05-13 --until 2026-05-27 \
        --out workspace/newbiz/fl_window.csv

    # Smoke test (no enrichment):
    python -m scripts.leads.newbiz.pipeline pull \
        --date 2026-05-27 --no-enrich --out /tmp/sample.csv

Env (enrichment is gated):
    GOOGLE_PLACES_API_KEY=...   # Places signal lookup
    APOLLO_API_KEY=...          # Apollo enrichment (stored phone)
    SUNBIZ_SFTP_PASS=...        # Override Sunbiz creds if they rotate
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# Make this work whether run as a module or a script.
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.leads.newbiz.sunbiz_fl import (  # noqa: E402
    CorRecord, fetch_daily, iter_records, LLC_FILING_TYPES,
)
from scripts.leads.newbiz.ra_blocklist import is_blocklisted_ra  # noqa: E402
from scripts.leads.newbiz.enrich import (  # noqa: E402
    places_lookup, apollo_lookup, score_priority,
)
from scripts.leads.newbiz.dedupe import DedupeStore  # noqa: E402

WORKSPACE = ROOT / "workspace" / "newbiz"
CACHE_DIR = WORKSPACE / "raw"
DB_PATH = WORKSPACE / "dedupe.sqlite"

OUT_COLUMNS = [
    "state", "entity_id", "business_name", "entity_type",
    "formation_date", "status",
    "principal_addr1", "principal_addr2", "principal_city",
    "principal_state", "principal_zip",
    "mailing_addr1", "mailing_addr2", "mailing_city",
    "mailing_state", "mailing_zip",
    "ra_name", "ra_addr", "ra_city", "ra_state",
    "place_id", "places_found", "has_listed_phone", "has_website",
    "is_operational", "category_bucket", "review_count_bucket",
    "owner_first_name", "owner_last_name", "business_phone",
    "phone_is_mobile", "business_email",
    "priority", "source_file",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="FL Sunbiz new-LLC pull → filter → enrich → CSV"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pull = sub.add_parser("pull", help="Pull, filter, enrich, write CSV")
    g = pull.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", help="Single date YYYY-MM-DD")
    g.add_argument("--since", help="Range start YYYY-MM-DD")
    pull.add_argument("--until", help="Range end YYYY-MM-DD (default: today)")
    pull.add_argument("--out", required=True, help="Output CSV path")
    pull.add_argument(
        "--min-formation-date",
        help="Only keep records with file_date >= this YYYY-MM-DD "
             "(default: window start)",
    )
    pull.add_argument("--no-enrich", action="store_true",
                      help="Skip Places + Apollo (faster smoke test)")
    pull.add_argument("--no-dedupe", action="store_true",
                      help="Don't skip rows previously seen")
    pull.add_argument("--limit", type=int, default=0,
                      help="Hard cap on output rows (0 = no cap)")
    pull.add_argument("--places-limit", type=int, default=0,
                      help="Cap Places API calls (0 = no cap)")
    return p.parse_args()


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def to_ymd(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def main() -> int:
    args = parse_args()
    if args.cmd != "pull":
        print("unknown command", file=sys.stderr)
        return 2

    if args.date:
        days = [to_ymd(args.date)]
    else:
        start = to_ymd(args.since)
        end = to_ymd(args.until) if args.until else date.today()
        days = list(daterange(start, end))

    min_fd_iso = args.min_formation_date or days[0].isoformat()
    min_fd = min_fd_iso.replace("-", "")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    store: Optional[DedupeStore] = (
        DedupeStore(DB_PATH) if not args.no_dedupe else None
    )
    counter: Counter[str] = Counter()
    places_calls = 0
    sample_row: Optional[dict] = None
    rows_written = 0

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_COLUMNS)
        w.writeheader()

        for d in days:
            counter["days_attempted"] += 1
            try:
                local = fetch_daily(d, CACHE_DIR)
            except Exception as e:
                counter["days_missing"] += 1
                print(f"[skip] {d.isoformat()} — {e}", file=sys.stderr)
                continue
            counter["days_fetched"] += 1

            day_raw = 0
            day_kept = 0
            for rec in iter_records(local):
                day_raw += 1
                counter["raw_records"] += 1

                if rec.status != "A":
                    counter["rej_inactive"] += 1
                    continue
                if rec.filing_type not in LLC_FILING_TYPES:
                    counter["rej_not_llc"] += 1
                    continue
                if min_fd:
                    rec_ymd = rec.file_date_ymd
                    if not rec_ymd or rec_ymd < min_fd:
                        counter["rej_old_formation"] += 1
                        continue
                if is_blocklisted_ra(rec.ra_name):
                    counter["rej_ra_trap"] += 1
                    continue
                # Sunbiz omits principal-state for FL (source implies it).
                if not (rec.addr1 and rec.city and rec.zip):
                    counter["rej_no_principal_addr"] += 1
                    continue

                if store and store.has_seen("FL", rec.corp_no):
                    counter["skipped_already_seen"] += 1
                    continue

                places_sig = None
                apollo_sig = None
                if not args.no_enrich:
                    if (args.places_limit == 0
                            or places_calls < args.places_limit):
                        places_sig = places_lookup(rec.name, rec.city, rec.state)
                        if places_sig is not None:
                            places_calls += 1
                    apollo_sig = apollo_lookup(rec.name, rec.city, rec.state)

                priority = score_priority(places_sig, apollo_sig)

                row = {
                    "state": "FL",
                    "entity_id": rec.corp_no,
                    "business_name": rec.name,
                    "entity_type": rec.filing_type,
                    "formation_date": rec.file_date_iso or "",
                    "status": rec.status,
                    "principal_addr1": rec.addr1, "principal_addr2": rec.addr2,
                    "principal_city": rec.city,
                    "principal_state": (rec.state or "FL"),
                    "principal_zip": rec.zip,
                    "mailing_addr1": rec.mail_addr1,
                    "mailing_addr2": rec.mail_addr2,
                    "mailing_city": rec.mail_city,
                    "mailing_state": (rec.mail_state or "FL"),
                    "mailing_zip": rec.mail_zip,
                    "ra_name": rec.ra_name, "ra_addr": rec.ra_addr,
                    "ra_city": rec.ra_city, "ra_state": rec.ra_state,
                    "place_id": (places_sig.place_id if places_sig else ""),
                    "places_found": (places_sig.found if places_sig else ""),
                    "has_listed_phone": (
                        places_sig.has_listed_phone if places_sig else ""
                    ),
                    "has_website": (places_sig.has_website if places_sig else ""),
                    "is_operational": (
                        places_sig.is_operational if places_sig else ""
                    ),
                    "category_bucket": (
                        places_sig.category_bucket if places_sig else ""
                    ),
                    "review_count_bucket": (
                        places_sig.review_count_bucket if places_sig else ""
                    ),
                    "owner_first_name": (
                        apollo_sig.owner_first_name if apollo_sig else ""
                    ),
                    "owner_last_name": (
                        apollo_sig.owner_last_name if apollo_sig else ""
                    ),
                    "business_phone": (
                        apollo_sig.business_phone if apollo_sig else ""
                    ),
                    "phone_is_mobile": (
                        apollo_sig.phone_is_mobile if apollo_sig else ""
                    ),
                    "business_email": (
                        apollo_sig.business_email if apollo_sig else ""
                    ),
                    "priority": priority,
                    "source_file": rec.source_file,
                }
                w.writerow(row)
                rows_written += 1
                day_kept += 1
                counter[f"priority_{priority}"] += 1
                if sample_row is None:
                    sample_row = row

                if store:
                    store.record(
                        "FL", rec.corp_no, rec.name, priority,
                        row["place_id"] or None, d.isoformat(),
                    )

                if args.limit and rows_written >= args.limit:
                    break

            counter["kept_records"] += day_kept
            print(
                f"[done] {d.isoformat()} — raw={day_raw} kept={day_kept}",
                file=sys.stderr,
            )
            if args.limit and rows_written >= args.limit:
                break

        if store:
            store.close()

    print()
    print("=== Run summary ===")
    for k, v in counter.most_common():
        print(f"{k:>32s}: {v}")
    places_status = ("live"
                     if os.environ.get("GOOGLE_PLACES_API_KEY")
                     else "gated on GOOGLE_PLACES_API_KEY")
    apollo_status = ("live"
                     if os.environ.get("APOLLO_API_KEY")
                     else "gated on APOLLO_API_KEY")
    print(f"{'places_api_calls':>32s}: {places_calls}  ({places_status})")
    print(f"{'apollo_calls':>32s}: stub  ({apollo_status})")
    print(f"{'output':>32s}: {out_path}  rows={rows_written}")
    if sample_row:
        print()
        print("=== Sample row ===")
        for k in ("business_name", "formation_date", "principal_addr1",
                  "principal_city", "principal_state", "ra_name",
                  "category_bucket", "priority"):
            print(f"{k:>20s}: {sample_row[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""DataForSEO-backed named-account prospecting from public Google reviews.

The source is intentionally asynchronous:
1. Find a bounded rotation of local businesses from Business Listings.
2. Submit low-priority Google review tasks for those businesses.
3. Poll the task IDs on later hourly runs for free.
4. Send only communication-pain reviews to an evidence-bound fit classifier.

No outreach is drafted or sent here.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

import requests


LIVE_BASE = "https://api.dataforseo.com/v3"
PAIN_PREFILTER = (
    "no answer",
    "didn't answer",
    "did not answer",
    "never answered",
    "call back",
    "called back",
    "return my call",
    "return calls",
    "left a voicemail",
    "left voicemail",
    "left a message",
    "no response",
    "never responded",
    "slow to respond",
    "hard to reach",
    "impossible to reach",
    "phone went to voicemail",
    "straight to voicemail",
    "nobody picked up",
    "no one picked up",
    "poor communication",
    "lack of communication",
)


def _task(payload: dict) -> dict:
    tasks = payload.get("tasks") or []
    if int(payload.get("status_code") or 0) != 20000 or not tasks:
        raise RuntimeError(
            f"DataForSEO error {payload.get('status_code')}: "
            f"{payload.get('status_message')}"
        )
    return tasks[0]


def fetch_business_listings(
    auth_header: str,
    category: str,
    location_coordinate: str,
    limit: int,
    *,
    base_url: str = LIVE_BASE,
) -> tuple[list[dict], float]:
    response = requests.post(
        f"{base_url}/business_data/business_listings/search/live",
        timeout=30,
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        json=[{
            "categories": [category],
            "location_coordinate": location_coordinate,
            "is_claimed": True,
            "only_google_business": True,
            "filters": [["rating.votes_count", ">=", 20]],
            "order_by": ["rating.votes_count,desc"],
            "limit": min(max(1, int(limit)), 100),
        }],
    )
    response.raise_for_status()
    task = _task(response.json())
    if int(task.get("status_code") or 0) != 20000:
        raise RuntimeError(
            f"DataForSEO listings error {task.get('status_code')}: "
            f"{task.get('status_message')}"
        )
    results = task.get("result") or []
    items = (results[0].get("items") or []) if results else []
    businesses = []
    for item in items:
        if item.get("type") != "business_listing":
            continue
        business_id = str(item.get("cid") or item.get("place_id") or "").strip()
        title = str(item.get("title") or "").strip()
        if not business_id or not title:
            continue
        rating = item.get("rating") or {}
        businesses.append({
            "business_id": business_id,
            "cid": str(item.get("cid") or ""),
            "place_id": str(item.get("place_id") or ""),
            "name": title,
            "category": item.get("category") or category,
            "category_id": category,
            "address": item.get("address") or "",
            "city": (item.get("address_info") or {}).get("city") or "",
            "region": (item.get("address_info") or {}).get("region") or "",
            "phone": item.get("phone") or "",
            "website": item.get("url") or "",
            "rating": rating.get("value"),
            "review_count": rating.get("votes_count"),
            "maps_url": (
                f"https://www.google.com/maps?cid={item.get('cid')}"
                if item.get("cid") else ""
            ),
        })
    return businesses, float(task.get("cost") or 0)


def submit_review_tasks(
    auth_header: str,
    businesses: list[dict],
    depth: int,
    *,
    base_url: str = LIVE_BASE,
) -> tuple[list[dict], float]:
    if not businesses:
        return [], 0.0
    tasks = []
    selected_businesses = []
    for business in businesses[:100]:
        row = {
            "location_code": 2840,
            "language_code": "en",
            "depth": min(max(10, int(depth)), 100),
            "sort_by": "newest",
            "priority": 1,
            "tag": f"kaicalls-review:{business['business_id']}"[:255],
        }
        if business.get("cid"):
            row["cid"] = business["cid"]
        elif business.get("place_id"):
            row["place_id"] = business["place_id"]
        else:
            continue
        tasks.append(row)
        selected_businesses.append(business)
    if not tasks:
        return [], 0.0
    response = requests.post(
        f"{base_url}/business_data/google/reviews/task_post",
        timeout=30,
        headers={"Authorization": auth_header, "Content-Type": "application/json"},
        json=tasks,
    )
    response.raise_for_status()
    payload = response.json()
    if int(payload.get("status_code") or 0) != 20000:
        raise RuntimeError(
            f"DataForSEO review submit error {payload.get('status_code')}: "
            f"{payload.get('status_message')}"
        )
    submitted = []
    cost = 0.0
    for business, task in zip(selected_businesses, payload.get("tasks") or []):
        cost += float(task.get("cost") or 0)
        if int(task.get("status_code") or 0) not in {20000, 20100}:
            continue
        task_id = str(task.get("id") or "").strip()
        if task_id:
            submitted.append({"task_id": task_id, "business": business})
    return submitted, cost


def poll_review_task(
    auth_header: str,
    task_id: str,
    *,
    base_url: str = LIVE_BASE,
) -> tuple[str, list[dict], str]:
    response = requests.get(
        f"{base_url}/business_data/google/reviews/task_get/{task_id}",
        timeout=30,
        headers={"Authorization": auth_header},
    )
    response.raise_for_status()
    task = _task(response.json())
    status_code = int(task.get("status_code") or 0)
    if status_code == 20100:
        return "pending", [], ""
    if status_code != 20000:
        return "error", [], (
            f"{task.get('status_code')}: {task.get('status_message')}"
        )
    results = task.get("result") or []
    if not results:
        return "ready", [], ""
    result = results[0]
    reviews = []
    for item in result.get("items") or []:
        text = str(item.get("review_text") or "").strip()
        if not text:
            continue
        rating = item.get("rating") or {}
        reviews.append({
            "review_id": item.get("review_id") or "",
            "text": text,
            "timestamp": item.get("timestamp") or "",
            "rating": rating.get("value"),
            "owner_answer": item.get("owner_answer") or "",
            "review_url": item.get("review_url") or "",
        })
    return "ready", reviews, str(result.get("check_url") or "")


def pain_reviews(reviews: list[dict]) -> list[dict]:
    matches = []
    for review in reviews:
        text = str(review.get("text") or "")
        lower = text.lower()
        triggers = [term for term in PAIN_PREFILTER if term in lower]
        if triggers:
            row = dict(review)
            row["matched_pain"] = triggers
            matches.append(row)
    return matches


def _normal(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def validate_qualification(data: dict, source_text: str) -> dict:
    evidence = str(data.get("evidence_quote") or "").strip()
    confidence = float(data.get("confidence") or 0)
    pain_type = str(data.get("pain_type") or "none").strip()
    valid_types = {
        "unanswered_phone",
        "callback_delay",
        "intake_failure",
        "after_hours",
    }
    evidence_valid = (
        len(evidence) >= 12
        and _normal(evidence) in _normal(source_text)
    )
    is_fit = (
        bool(data.get("is_fit"))
        and confidence >= 0.8
        and pain_type in valid_types
        and evidence_valid
    )
    score = min(100, max(0, int(data.get("score") or 0)))
    if not is_fit:
        score = min(score, 25)
    return {
        "is_fit": is_fit,
        "score": score,
        "confidence": confidence,
        "pain_type": pain_type,
        "evidence_quote": evidence if evidence_valid else "",
        "reason": str(data.get("reason") or "").strip(),
        "angle": str(data.get("angle") or "").strip() if is_fit else "",
    }


def select_daily_segments(profile: dict, day: date) -> list[dict]:
    categories = profile.get("prospecting_categories") or []
    locations = profile.get("prospecting_locations") or []
    if not categories or not locations:
        return []
    all_segments = [
        {
            "category": category,
            "location_name": location["name"],
            "location_coordinate": location["coordinate"],
        }
        for location in locations
        for category in categories
    ]
    cap = min(
        len(all_segments),
        max(0, int(profile.get("prospecting_daily_listing_cap", 0))),
    )
    start = day.toordinal() % len(all_segments)
    stride = 7 if len(all_segments) % 7 else 11
    return [
        all_segments[(start + index * stride) % len(all_segments)]
        for index in range(cap)
    ]


def run(
    profile: dict,
    state_path: Path,
    auth_header: str,
    qualify: Callable[[dict, list[dict]], dict],
    write_json: Callable[[Path, object], None],
    *,
    today: date | None = None,
    base_url: str = LIVE_BASE,
) -> list[dict]:
    """Poll ready tasks, launch today's bounded scan, and return proven prospects."""
    current_day = today or date.today()
    day = current_day.isoformat()
    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
    pending = state.get("pending_review_tasks")
    if not isinstance(pending, dict):
        pending = {}
    reviewed_dates = state.get("reviewed_business_dates")
    if not isinstance(reviewed_dates, dict):
        reviewed_dates = {}
    # Migrate the original permanent-ID ring into a dated cooldown.
    for business_id in state.get("reviewed_business_ids") or []:
        reviewed_dates.setdefault(str(business_id), day)
    refresh_days = max(
        1, int(profile.get("prospecting_business_refresh_days", 60))
    )

    def recently_reviewed(business_id: str) -> bool:
        try:
            reviewed_day = date.fromisoformat(
                str(reviewed_dates.get(business_id))
            )
        except (TypeError, ValueError):
            return False
        return (current_day - reviewed_day).days < refresh_days

    ready = state.get("ready_prospects")
    if not isinstance(ready, dict):
        ready = {}
    output = list(ready.values())

    # GET is free. Poll every hourly run until each task reaches a terminal state.
    # Expire abandoned provider jobs so a permanently pending task cannot make
    # the state file grow forever or suppress the business indefinitely.
    for task_id, task_state in list(pending.items()):
        submitted_on = task_state.get("submitted_on")
        try:
            submitted_day = date.fromisoformat(str(submitted_on))
        except (TypeError, ValueError):
            submitted_day = current_day
        if (current_day - submitted_day).days > 3:
            pending.pop(task_id, None)
            state.setdefault("expired_review_tasks", []).append({
                "task_id": task_id,
                "submitted_on": submitted_on,
                "expired_on": day,
                "business_id": (
                    task_state.get("business", {}).get("business_id")
                ),
            })
            continue
        try:
            status, reviews, check_url = poll_review_task(
                auth_header, task_id, base_url=base_url
            )
        except Exception as exc:
            task_state["last_poll_error"] = str(exc)
            continue
        if status == "pending":
            continue
        pending.pop(task_id, None)
        business = task_state["business"]
        reviewed_dates[business["business_id"]] = day
        if status != "ready":
            continue
        candidates = pain_reviews(reviews)
        if not candidates:
            continue
        decision = qualify(business, candidates)
        if not decision.get("is_fit"):
            continue
        evidence = decision["evidence_quote"]
        matching_review = next(
            (
                review for review in candidates
                if _normal(evidence) in _normal(review["text"])
            ),
            candidates[0],
        )
        url = (
            matching_review.get("review_url")
            or check_url
            or business.get("maps_url")
            or business.get("website")
        )
        prospect = {
            "id": f"review-prospect:{business['business_id']}",
            "source": "google_review_pain",
            "source_context": "Named prospect · Google review evidence",
            "title": business["name"],
            "url": url,
            "content": evidence,
            "published_at": matching_review.get("timestamp") or "",
            "score": decision["score"],
            "reason": decision["reason"],
            "angle": decision["angle"],
            "confidence": decision["confidence"],
            "pain_type": decision["pain_type"],
            "evidence_quote": evidence,
            "prospect": business,
            "found_at": datetime.now(timezone.utc).isoformat(),
        }
        ready[prospect["id"]] = prospect
        output.append(prospect)

    state["pending_review_tasks"] = pending
    reviewed_dates = dict(
        sorted(reviewed_dates.items(), key=lambda row: row[1])[-10000:]
    )
    state["reviewed_business_dates"] = reviewed_dates
    state["reviewed_business_ids"] = list(reviewed_dates)
    state["ready_prospects"] = ready
    state["expired_review_tasks"] = (
        state.get("expired_review_tasks") or []
    )[-1000:]

    # One bounded listings rotation per day.
    attempted_days = set(state.get("prospecting_listing_days_attempted") or [])
    if day in attempted_days:
        write_json(state_path, state)
        return output

    max_cost = float(profile.get("prospecting_max_daily_cost_usd", 0.7))
    listing_guard = float(
        profile.get("prospecting_listing_cost_guard_usd", 0.03)
    )
    review_guard = float(
        profile.get("prospecting_review_task_cost_guard_usd", 0.005)
    )
    reserved_by_day = state.get("prospecting_reserved_cost_usd_by_date")
    if not isinstance(reserved_by_day, dict):
        reserved_by_day = {}
    actual_by_day = state.get("prospecting_cost_usd_by_date")
    if not isinstance(actual_by_day, dict):
        actual_by_day = {}
    reserved = float(reserved_by_day.get(day) or 0)
    actual = float(actual_by_day.get(day) or 0)
    discovered: list[dict] = []

    # Claim the day before the first paid call. A timeout may still be billable.
    attempted_days.add(day)
    state["prospecting_listing_days_attempted"] = sorted(attempted_days)[-31:]
    write_json(state_path, state)

    budget_blocked = False
    for segment in select_daily_segments(profile, current_day):
        if max(reserved, actual) + listing_guard > max_cost + 1e-9:
            budget_blocked = True
            break
        reserved += listing_guard
        reserved_by_day[day] = round(reserved, 6)
        state["prospecting_reserved_cost_usd_by_date"] = reserved_by_day
        write_json(state_path, state)
        try:
            businesses, cost = fetch_business_listings(
                auth_header,
                segment["category"],
                segment["location_coordinate"],
                int(profile.get("prospecting_listing_limit", 10)),
                base_url=base_url,
            )
        except Exception as exc:
            state.setdefault("prospecting_errors", []).append({
                "day": day,
                "segment": segment,
                "error": str(exc),
            })
            continue
        actual += cost
        for business in businesses:
            business["market"] = segment["location_name"]
            if (
                not recently_reviewed(business["business_id"])
                and not any(
                    entry.get("business", {}).get("business_id")
                    == business["business_id"]
                    for entry in pending.values()
                )
            ):
                discovered.append(business)

    unique = {
        business["business_id"]: business for business in discovered
    }
    review_cap = max(0, int(profile.get("prospecting_daily_review_task_cap", 50)))
    to_submit = list(unique.values())[:review_cap]
    affordable = int(max(0, max_cost - max(reserved, actual)) // review_guard)
    to_submit = to_submit[:affordable]
    if to_submit:
        reservation = len(to_submit) * review_guard
        reserved += reservation
        reserved_by_day[day] = round(reserved, 6)
        state["prospecting_reserved_cost_usd_by_date"] = reserved_by_day
        # Persist every business as unknown before the billable batch.
        unknown_key = f"unknown:{day}"
        state.setdefault("prospecting_unknown_batches", {})[unknown_key] = to_submit
        write_json(state_path, state)
        try:
            submitted, cost = submit_review_tasks(
                auth_header,
                to_submit,
                int(profile.get("prospecting_review_depth", 20)),
                base_url=base_url,
            )
        except Exception as exc:
            state.setdefault("prospecting_errors", []).append({
                "day": day,
                "stage": "submit_reviews",
                "error": str(exc),
            })
        else:
            actual += cost
            for row in submitted:
                pending[row["task_id"]] = {
                    "submitted_on": day,
                    "business": row["business"],
                }
            state["pending_review_tasks"] = pending
            state.get("prospecting_unknown_batches", {}).pop(unknown_key, None)

    # A day whose cap prices out the first listing call never reaches a
    # provider, so it records no cost. Mark it as an explicit hold; without
    # this the outcome tripwire cannot tell a held day from a broken scan.
    if actual <= 0 and budget_blocked:
        hold_days = set(state.get("prospecting_budget_hold_days") or [])
        hold_days.add(day)
        state["prospecting_budget_hold_days"] = sorted(hold_days)[-31:]

    actual_by_day[day] = round(actual, 6)
    state["prospecting_cost_usd_by_date"] = dict(
        sorted(actual_by_day.items())[-31:]
    )
    state["prospecting_reserved_cost_usd_by_date"] = dict(
        sorted(reserved_by_day.items())[-31:]
    )
    write_json(state_path, state)
    return output


def finalize_ready(
    state_path: Path,
    prospect_ids: list[str],
    write_json: Callable[[Path, object], None],
) -> None:
    if not prospect_ids:
        return
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    ready = state.get("ready_prospects")
    if not isinstance(ready, dict):
        return
    for prospect_id in prospect_ids:
        ready.pop(prospect_id, None)
    state["ready_prospects"] = ready
    write_json(state_path, state)

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


SCORE_FIELDS = ("commercial_intent", "content_value", "reputation_risk")


def _text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("title", "body", "subreddit")).casefold()


def match_groups(item: dict, profile: dict) -> list[dict]:
    text = _text(item)
    matches = []
    for group in profile["keyword_groups"]:
        terms = [term for term in group.get("terms", []) if str(term).casefold() in text]
        qualifiers = group.get("qualifiers", [])
        qualifier_hits = [q for q in qualifiers if str(q).casefold() in text]
        mode = group.get("qualifier_mode", "none")
        accepted = bool(terms) and (mode != "required" or bool(qualifier_hits))
        if accepted:
            matches.append({"group": group["name"], "terms": terms, "qualifiers": qualifier_hits})
    return matches


def validate_score(score: dict) -> dict:
    result = dict(score)
    for field in SCORE_FIELDS:
        value = result.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 10:
            raise ValueError(f"{field} must be a number from 1 to 10")
        result[field] = int(value)
    result.setdefault("category", "Content opportunity")
    result.setdefault("treatment_or_topic", "Other")
    result.setdefault("geography", "Unknown")
    result.setdefault("summary", "")
    result.setdefault("suggested_action", "Monitor only")
    result.setdefault("evidence_quote", "")
    return result


def default_score(item: dict, matches: list[dict], profile: dict) -> dict:
    text = _text(item)
    intent_words = ("recommend", "best", "price", "cost", "worth", "provider", "where")
    risk_words = ("scam", "unsafe", "injury", "complaint", "terrible", "fraud")
    brand_terms = [str(x).casefold() for x in profile.get("brand", {}).get("terms", [])]
    intent = min(10, 3 + sum(word in text for word in intent_words) * 2)
    content = min(10, 5 + min(3, len(matches)) + int("?" in str(item.get("title", ""))))
    risk = min(10, 1 + sum(word in text for word in risk_words) * 3 + int(any(x in text for x in brand_terms)))
    evidence = str(item.get("title") or item.get("body") or "")[:240]
    action = "Review immediately" if risk >= 6 else "Consider answering" if intent >= 8 else "Create content" if content >= 8 else "Monitor only"
    return validate_score({
        "commercial_intent": intent, "content_value": content, "reputation_risk": risk,
        "category": matches[0]["group"] if matches else "Irrelevant",
        "treatment_or_topic": matches[0]["terms"][0] if matches else "Other",
        "geography": "Local" if any(x in text for x in profile.get("geography_terms", [])) else "Unknown",
        "summary": evidence, "suggested_action": action, "evidence_quote": evidence,
    })


def opportunity(item: dict, profile: dict, scorer=None) -> dict | None:
    matches = match_groups(item, profile)
    if not matches:
        return None
    item_url = str(item.get("url", ""))
    if item_url and urlparse(item_url).scheme not in {"http", "https"}:
        raise ValueError("opportunity URL must use http or https")
    score = validate_score(scorer(item, matches, profile) if scorer else default_score(item, matches, profile))
    source = f"{item.get('title', '')}\n{item.get('body', '')}".casefold()
    quote = score.get("evidence_quote", "").casefold()
    if not quote:
        raise ValueError("evidence_quote is required for every opportunity")
    if quote not in source:
        raise ValueError("evidence_quote must occur verbatim in source title or body")
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(item.get("id") or item.get("url") or hash(source)), "source": "reddit",
        "source_mode": "read_only", "captured_at": now, "published_at": item.get("published_at"),
        "subreddit": item.get("subreddit", ""), "author": item.get("author", ""),
        "title": item.get("title", ""), "body": item.get("body", ""), "url": item_url,
        "matched_groups": matches, **score, "status": "New",
    }


def is_urgent(row: dict, profile: dict) -> bool:
    rules = profile["alerts"]
    brand_group = rules.get("brand_group", "Brand monitoring")
    groups = {m["group"] for m in row["matched_groups"]}
    return (brand_group in groups or row["reputation_risk"] >= rules.get("risk_at_least", 6)
            or (row["commercial_intent"] >= rules.get("intent_at_least", 8)
                and row["geography"] != "Unknown"))


def content_brief(row: dict) -> dict:
    topic = row["treatment_or_topic"]
    question = row["title"] or row["summary"]
    return {"opportunity_id": row["id"], "source_url": row["url"], "question": question,
            "proposed_title": question.rstrip("?") + ": An Evidence-Based Guide",
            "search_intent": "Informational with possible provider intent",
            "outline": ["Direct answer", "Who it is for", "Benefits and limits", "Cost and alternatives", "FAQs"],
            "faq_questions": [f"How does {topic} work?", f"Who is a good candidate for {topic}?"],
            "social_concept": f"Answer the Reddit question: {question}",
            "newsletter_angle": f"What people are asking about {topic}", "requires_human_review": True}


def sheet_row(row: dict) -> dict:
    """Map one normalized opportunity to the stable adapter contract."""
    return {
        "Date": row.get("published_at") or row["captured_at"],
        "Subreddit": row["subreddit"], "Question": row["title"],
        "Topic": row["treatment_or_topic"], "Geography": row["geography"],
        "Intent": row["commercial_intent"], "Content Value": row["content_value"],
        "Risk": row["reputation_risk"], "Recommended Action": row["suggested_action"],
        "URL": row["url"], "Status": row["status"], "Evidence Quote": row["evidence_quote"],
        "Content URL": row.get("content_url", ""), "Social URL": row.get("social_url", ""),
        "Reddit response date": row.get("reddit_response_date", ""), "Team owner": row.get("team_owner", ""),
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def run_pipeline(items: Iterable[dict], profile: dict, output_dir: str | Path, scorer=None,
                 activate_sheets: bool = False, activate_email: bool = False) -> dict:
    if activate_sheets or activate_email:
        raise RuntimeError("live adapters are not included; configure an approved provider adapter first")
    out = Path(output_dir)
    existing_path = out / "opportunities.json"
    existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else []
    by_id = {row["id"]: row for row in existing}
    for item in items:
        row = opportunity(item, profile, scorer)
        if row:
            by_id.setdefault(row["id"], row)
    rows = sorted(by_id.values(), key=lambda x: x["captured_at"], reverse=True)
    urgent = [row for row in rows if is_urgent(row, profile)]
    briefs = [content_brief(row) for row in rows if row["content_value"] >= profile["content_brief_threshold"]]
    digest = {"generated_at": datetime.now(timezone.utc).isoformat(), "total": len(rows),
              "top_questions": sorted(rows, key=lambda x: (x["content_value"], x["commercial_intent"]), reverse=True)[:10],
              "category_counts": dict(Counter(row["category"] for row in rows))}
    _write_json(existing_path, rows)
    _write_json(out / "sheet-rows.preview.json", [sheet_row(row) for row in rows])
    _write_json(out / "urgent-alerts.preview.json", urgent)
    _write_json(out / "weekly-digest.preview.json", digest)
    _write_json(out / "content-briefs.preview.json", briefs)
    with (out / "opportunities.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"profile_id": profile["id"], "mode": "dry_run", "external_effects": [],
                "opportunities": len(rows), "urgent_alerts": len(urgent), "content_briefs": len(briefs),
                "source_coverage": profile.get("sources", {}),
                "files": ["opportunities.json", "opportunities.jsonl", "sheet-rows.preview.json", "urgent-alerts.preview.json",
                          "weekly-digest.preview.json", "content-briefs.preview.json"]}
    _write_json(out / "run-manifest.json", manifest)
    return manifest

"""SQLite-backed customer voice memory. No implicit cross-customer fallback.

Imports and editorial feedback are trusted operator inputs. Source references
are provenance pointers, not evidence authentication. Held-out examples never
enter generation packets; inferred corrections never become standing rules.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def required(**fields):
    for key, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a nonempty string")


class VoiceStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS profiles (
                    brand TEXT, writer TEXT, channel TEXT, version TEXT,
                    body TEXT NOT NULL, created TEXT NOT NULL,
                    PRIMARY KEY(brand,writer,channel,version));
                CREATE TABLE IF NOT EXISTS examples (
                    id TEXT PRIMARY KEY, brand TEXT NOT NULL, writer TEXT NOT NULL,
                    channel TEXT NOT NULL, split TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL, brand TEXT NOT NULL,
                    kind TEXT NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def profile(self, *, brand, writer="company", channel="*", rules=None,
                banned_phrases=None, source_ref, approved_by, expected_version=None):
        required(brand=brand, writer=writer, channel=channel,
                 source_ref=source_ref, approved_by=approved_by)
        rules, banned_phrases = rules or [], banned_phrases or []
        if not isinstance(rules, list) or not isinstance(banned_phrases, list):
            raise ValueError("rules and banned_phrases must be lists")
        if any(not isinstance(r, str) or not r.strip() for r in rules + banned_phrases):
            raise ValueError("rules and banned_phrases must contain nonempty strings")
        body = dict(brand=brand, writer=writer, channel=channel, rules=rules,
                    banned_phrases=banned_phrases, source_ref=source_ref,
                    approved_by=approved_by)
        version = digest(body)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT version,body FROM profiles WHERE brand=? AND writer=? AND channel=? ORDER BY rowid DESC LIMIT 1",
                                 (brand, writer, channel)).fetchone()
            if current and json.loads(current[1]) == body:
                return current[0]
            if current and expected_version != current[0]:
                raise ValueError("expected_version must match the current profile before replacement")
            if not current and expected_version is not None:
                raise ValueError("profile does not exist")
            # Restoring a previous profile is explicit and retains all history.
            version = digest(dict(body, previous=current[0] if current else None))
            db.execute("INSERT INTO profiles VALUES (?,?,?,?,?,?)",
                       (brand, writer, channel, version, json.dumps(body), now()))
        return version

    def example(self, *, brand, writer, channel, original, final, source_ref,
                reviewer, reason, category="voice", audience="", topic="",
                split="train", accepted=True, origin="customer_edited", example_id=None):
        required(brand=brand, writer=writer, channel=channel, source_ref=source_ref,
                 reviewer=reviewer, reason=reason)
        if category not in {"voice", "facts", "positioning", "structure", "preference"}:
            raise ValueError("invalid correction category")
        if split not in {"train", "holdout"} or type(accepted) is not bool:
            raise ValueError("invalid split or acceptance label")
        if origin not in {"customer_written", "customer_edited", "ai_approved"}:
            raise ValueError("invalid authorship origin")
        if not isinstance(original, str) or not original.strip() or not isinstance(final, str):
            raise ValueError("original and final must be strings; original cannot be empty")
        if accepted and not final.strip():
            raise ValueError("accepted examples need a final text")
        if len(original) + len(final) > 100_000:
            raise ValueError("example too large; import a focused passage")
        body = dict(brand=brand, writer=writer, channel=channel, original=original,
                    final=final, source_ref=source_ref, reviewer=reviewer,
                    reason=reason, category=category, audience=audience, topic=topic,
                    split=split, accepted=accepted, origin=origin,
                    edit_fraction=1 - SequenceMatcher(None, original, final).ratio())
        example_id = example_id or digest(body)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT body FROM examples WHERE id=?", (example_id,)).fetchone()
            if existing:
                if json.loads(existing[0]) != body:
                    raise ValueError("conflicting example_id")
                return example_id
            # Prevent an identical pair appearing in both learning and test sets.
            for row in db.execute("SELECT body FROM examples WHERE brand=? AND writer=?", (brand, writer)):
                other = json.loads(row[0])
                if other["split"] != split and {original.strip(), final.strip()} & {
                    other["original"].strip(), other["final"].strip()
                } - {""}:
                    raise ValueError("example text overlaps train and holdout sets")
            db.execute("INSERT INTO examples VALUES (?,?,?,?,?,?)",
                       (example_id, brand, writer, channel, split, json.dumps(body)))
        return example_id

    def packet(self, *, brand, writer="company", channel, audience="", topic="", limit=4):
        required(brand=brand, writer=writer, channel=channel)
        if not isinstance(limit, int) or not 0 <= limit <= 8:
            raise ValueError("limit must be between 0 and 8")
        profiles, examples = [], []
        with self.connect() as db:
            # Explicit company -> writer -> channel layering, same brand only.
            keys = list(dict.fromkeys([("company", "*"), (writer, "*"),
                                       ("company", channel), (writer, channel)]))
            for who, where in keys:
                row = db.execute("SELECT version,body FROM profiles WHERE brand=? AND writer=? AND channel=? ORDER BY rowid DESC LIMIT 1",
                                 (brand, who, where)).fetchone()
                if row:
                    profiles.append(dict(version=row[0], **json.loads(row[1])))
            terms = set(re.findall(r"\w+", topic.lower()))
            for row in db.execute("SELECT id,body FROM examples WHERE brand=? AND writer=? AND channel=? AND split='train'",
                                  (brand, writer, channel)):
                body = json.loads(row[1])
                # Fact corrections are not style examples. AI-approved copy is
                # retained for audit, but does not teach the voice automatically.
                if body["category"] == "facts" or body["origin"] == "ai_approved":
                    continue
                if body["audience"] and body["audience"] != audience:
                    continue
                score = len(terms & set(re.findall(r"\w+", body["topic"].lower())))
                score += 3 if audience and body["audience"] == audience else 0
                examples.append((score, row[0], body))
        selected = [dict(id=key, **body) for _, key, body in sorted(
            examples, key=lambda x: (-x[0], x[1]))[:limit]]
        # Bound source passages, preserving their IDs and provenance.
        for example in selected:
            for key in ("original", "final"):
                example[key] = example[key][:2400]
        body = dict(brand=brand, writer=writer, channel=channel, audience=audience,
                    profiles=profiles, examples=selected,
                    rules=[r for p in profiles for r in p["rules"]],
                    banned_phrases=list(dict.fromkeys(r for p in profiles for r in p["banned_phrases"])),
                    configured=bool(profiles))
        body["version"] = digest(body)
        return body

    def record(self, *, run_id, brand, kind, data, event_id=None):
        required(run_id=run_id, brand=brand, kind=kind)
        body = json.dumps(data, ensure_ascii=False, allow_nan=False)
        event_id = event_id or uuid.uuid4().hex
        with self.connect() as db:
            current = db.execute("SELECT run_id,brand,kind,body FROM events WHERE id=?", (event_id,)).fetchone()
            if current:
                if tuple(current) != (run_id, brand, kind, body):
                    raise ValueError("conflicting replay event")
                return event_id
            db.execute("INSERT INTO events VALUES (?,?,?,?,?,?)",
                       (event_id, run_id, brand, kind, body, now()))
        return event_id

    def export(self, *, brand, run_id=None):
        required(brand=brand)
        with self.connect() as db:
            rows = db.execute("SELECT * FROM events WHERE brand=?" + (" AND run_id=?" if run_id else "") + " ORDER BY rowid",
                              (brand, run_id) if run_id else (brand,))
            return [dict(id=r["id"], run_id=r["run_id"], brand=r["brand"],
                         kind=r["kind"], data=json.loads(r["body"]), created=r["created"]) for r in rows]

    def holdout(self, *, brand, writer, channel):
        with self.connect() as db:
            return [dict(id=r[0], **json.loads(r[1])) for r in db.execute(
                "SELECT id,body FROM examples WHERE brand=? AND writer=? AND channel=? AND split='holdout'",
                (brand, writer, channel))]

    def feedback(self, *, brand, run_id, final, reviewer, reason, category="voice",
                 accepted=True, split="train"):
        events = self.export(brand=brand, run_id=run_id)
        context = next((e["data"] for e in events if e["kind"] == "context"), None)
        drafts = [e["data"]["content"] for e in events if e["kind"] in {"draft", "revision", "final"}]
        if not context or not drafts:
            raise ValueError("feedback requires a run with scoped context and a draft")
        example_id = self.example(
            brand=brand, writer=context["writer"], channel=context["channel"],
            audience=context["audience"], original=drafts[-1], final=final,
            reviewer=reviewer, reason=reason, category=category, accepted=accepted,
            split=split, source_ref="run:" + run_id,
            example_id=digest([brand, run_id, "editorial-feedback"]),
        )
        self.record(run_id=run_id, brand=brand, kind="feedback",
                    data=dict(example_id=example_id, accepted=accepted,
                              edit_fraction=1 - SequenceMatcher(None, drafts[-1], final).ratio()),
                    event_id=digest([brand, run_id, "feedback-event"]))
        return example_id

    def metrics(self, *, brand):
        events = self.export(brand=brand)
        feedback = [e["data"] for e in events if e["kind"] == "feedback"]
        accepted = [f for f in feedback if f["accepted"]]
        calls = [e["data"] for e in events if e["kind"] == "llm"]
        for e in events:
            if e["kind"] == "gate":
                calls.extend(e["data"].get("proposal", {}).get("llm_calls", []))
        estimates = [c.get("estimated_cost_usd") for c in calls]
        unknown = sum(x is None for x in estimates)
        known_cost = sum(x for x in estimates if x is not None)
        return dict(
            known_estimated_cost_usd=known_cost,
            calls_with_unknown_cost=unknown,
            estimated_cost_per_accepted_asset=(
                known_cost / len(accepted) if accepted and calls and not unknown else None
            ),
            reviewed_assets=len(feedback),
            accepted_assets=len(accepted),
            acceptance_rate=len(accepted) / len(feedback) if feedback else None,
            unchanged_acceptance_rate=sum(f["edit_fraction"] == 0 for f in accepted) / len(feedback) if feedback else None,
            mean_edit_fraction=sum(f["edit_fraction"] for f in accepted) / len(accepted) if accepted else None,
            # Measured outcomes remain separate from editorial preference.
            business_outcomes=[e["data"] for e in events if e["kind"] == "outcome"],
        )

    def outcome(self, *, brand, run_id, rl_db, decision_id, value, observed_at,
                verifier, evidence_ref, cost=0):
        """Join collector-verified business measurement to a published asset.

        This never derives rewards from voice or craft scores. Collector identity
        and source authenticity must be checked before this operator interface.
        """
        from kai.analytics.rl import OutcomePolicy
        events = self.export(brand=brand, run_id=run_id)
        execution = next((e["data"] for e in events if e["kind"] == "execution"
                          and e["data"]["decision_id"] == decision_id), None)
        if not execution:
            raise ValueError("run has no bound published execution for this decision")
        policy = OutcomePolicy(rl_db)
        record = next((d for d in policy.export() if d["decision_id"] == decision_id), None)
        if not record or record["brand_id"] != brand or record.get("execution", {}).get("run_id") != run_id:
            raise ValueError("outcome does not match brand/run")
        reward = policy.observe(decision_id=decision_id, value=value,
                                executed_at=execution["executed_at"], observed_at=observed_at,
                                verifier=verifier, evidence_ref=evidence_ref,
                                executed_action=execution["action"], cost=cost)
        self.record(run_id=run_id, brand=brand, kind="outcome",
                    data=dict(decision_id=decision_id, value=value, reward=reward,
                              observed_at=observed_at, evidence_ref=evidence_ref),
                    event_id=digest([brand, decision_id, "outcome"]))
        return reward

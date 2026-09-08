"""Outcome-driven contextual bandit, with durable decision/feedback records.

This updates action selection, not foundation-model weights. Feedback is an
operator/collector attestation, not an authentication or ECO verdict service.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


class OutcomePolicy:
    """Epsilon-greedy learning scoped to brand, KPI, direction and reward scale."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY, context TEXT NOT NULL, action TEXT NOT NULL,
                payload TEXT NOT NULL, outcome TEXT, reward REAL)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def choose(self, *, brand_id, metric, actions, baseline, scale, direction,
               actor, baseline_at, evidence_ref, window_days=30, epsilon=0.1,
               min_samples=3, cost_budget=0, rng=None):
        """Commit the reward contract and selection probability BEFORE execution."""
        for name, value in (("brand_id", brand_id), ("metric", metric),
                            ("actor", actor), ("evidence_ref", evidence_ref)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not isinstance(actions, list) or not actions or any(
            not isinstance(a, str) or not a.strip() for a in actions
        ):
            raise ValueError("actions must be a nonempty approved candidate list")
        actions = sorted(set(actions))
        for name, value in (("baseline", baseline), ("scale", scale),
                            ("window_days", window_days), ("epsilon", epsilon),
                            ("min_samples", min_samples), ("cost_budget", cost_budget)):
            finite(value, name)
        if scale <= 0 or window_days <= 0 or not 0 <= epsilon <= 1 or min_samples < 1 or cost_budget < 0:
            raise ValueError("invalid reward/policy bounds")
        if direction not in {"increase", "decrease"}:
            raise ValueError("direction must be increase or decrease")
        created_at = utcnow()
        if timestamp(baseline_at) > timestamp(created_at):
            raise ValueError("baseline cannot be in the future")
        context = json.dumps([brand_id, metric, direction, scale, window_days, cost_budget, "v1"])
        with self.connect() as db:
            stats = {r["action"]: (r["n"], r["mean"]) for r in db.execute(
                "SELECT action, COUNT(*) n, AVG(reward) mean FROM decisions "
                "WHERE context=? AND reward IS NOT NULL GROUP BY action", (context,)
            )}
            # Under-observed arms get uniform exploration. Pending outcomes
            # do not count as failures or observations.
            under = [a for a in actions if stats.get(a, (0, 0))[0] < min_samples]
            if under:
                probabilities = {a: (1 / len(under) if a in under else 0) for a in actions}
                mode = "cold_start"
            else:
                best = max(stats[a][1] for a in actions)
                winners = [a for a in actions if stats[a][1] == best]
                probabilities = {
                    a: epsilon / len(actions) + ((1 - epsilon) / len(winners) if a in winners else 0)
                    for a in actions
                }
                mode = "epsilon_greedy"
            rng = rng or random.SystemRandom()
            action = rng.choices(actions, weights=[probabilities[a] for a in actions], k=1)[0]
            record = dict(
                decision_id=uuid.uuid4().hex, brand_id=brand_id, metric=metric,
                action=action, candidates=actions, probabilities=probabilities,
                propensity=probabilities[action], baseline=baseline, scale=scale,
                direction=direction, actor=actor, baseline_at=baseline_at,
                baseline_evidence_ref=evidence_ref, window_days=window_days,
                cost_budget=cost_budget, epsilon=epsilon, min_samples=min_samples,
                policy_version="epsilon-greedy-v1", mode=mode, created_at=created_at,
            )
            db.execute("INSERT INTO decisions (id,context,action,payload) VALUES (?,?,?,?)",
                       (record["decision_id"], context, action, json.dumps(record)))
        return record

    def observe(self, *, decision_id, value, executed_at, observed_at,
                verifier, evidence_ref, executed_action, cost=0):
        """Accept one matured, externally attested observation per decision.

        The collector must verify the effect, measurement and identity upstream.
        An arbitrary different verifier string alone does not prove independence.
        """
        finite(value, "value")
        finite(cost, "cost")
        if cost < 0 or not verifier.strip() or not evidence_ref.strip():
            raise ValueError("nonnegative cost, verifier and evidence_ref required")
        outcome = dict(value=value, executed_at=executed_at, observed_at=observed_at,
                       verifier=verifier, evidence_ref=evidence_ref,
                       executed_action=executed_action, cost=cost)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM decisions WHERE id=?", (decision_id,)).fetchone()
            if row is None:
                raise ValueError("unknown decision")
            record = json.loads(row["payload"])
            if row["outcome"]:
                if json.loads(row["outcome"]) == outcome:
                    return row["reward"]
                raise ValueError("conflicting feedback; decision already settled")
            if verifier == record["actor"]:
                raise ValueError("producer cannot verify its own outcome")
            if executed_action != record["action"]:
                raise ValueError("executed action does not match selection")
            start, end = timestamp(executed_at), timestamp(observed_at)
            if start < timestamp(record["created_at"]) or end > timestamp(utcnow()):
                raise ValueError("execution must follow selection; observation cannot be in future")
            if (end - start).total_seconds() < record["window_days"] * 86400:
                raise ValueError("measurement window has not matured")
            sign = 1 if record["direction"] == "increase" else -1
            reward = max(-1, min(1, sign * (value - record["baseline"]) / record["scale"]))
            if record["cost_budget"]:
                reward = max(-1, reward - cost / record["cost_budget"])
            elif cost:
                raise ValueError("nonzero cost requires a predeclared cost_budget")
            db.execute("UPDATE decisions SET outcome=?, reward=? WHERE id=?",
                       (json.dumps(outcome), reward, decision_id))
            return reward

    def export(self):
        """Return replayable records, including unobserved decisions (reward=null)."""
        with self.connect() as db:
            return [
                dict(**json.loads(row["payload"]),
                     outcome=json.loads(row["outcome"]) if row["outcome"] else None,
                     reward=row["reward"])
                for row in db.execute("SELECT * FROM decisions ORDER BY rowid")
            ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("command", choices=["choose", "observe", "export"])
    parser.add_argument("--input", help="JSON file containing choose/observe arguments")
    args = parser.parse_args()
    policy = OutcomePolicy(args.db)
    if args.command == "export":
        for record in policy.export():
            print(json.dumps(record, allow_nan=False))
    else:
        if not args.input:
            parser.error("--input is required for choose/observe")
        result = getattr(policy, args.command)(**json.loads(Path(args.input).read_text()))
        print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()

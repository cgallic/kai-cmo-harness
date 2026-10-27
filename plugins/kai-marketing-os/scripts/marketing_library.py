"""Read-only validation of assistant-prepared marketing prompt selections.

No inference, network, execution, persistence or approval authority lives here.
Evidence references are operator attestations, not authenticated receipts.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "harness/references/marketing-growth-library"


def load_catalog() -> dict:
    return json.loads((LIBRARY / "catalog.json").read_text(encoding="utf-8"))


def _object(value, allowed, required=()):
    if not isinstance(value, dict):
        raise ValueError("expected an object")
    if set(value) - set(allowed) or set(required) - set(value):
        raise ValueError("unexpected or missing fields")


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected nonempty text")
    return value


def _list(value):
    if not isinstance(value, list):
        raise ValueError("expected a list")
    return value


def _goal(value):
    fields = {"metric", "unit", "target", "baseline", "baseline_ref", "period", "timezone", "reversal_rules"}
    _object(value, fields)
    result = {field: value.get(field) for field in sorted(fields)}
    for field, item in result.items():
        if item is None:
            continue
        if field in {"target", "baseline"}:
            if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
                raise ValueError(f"{field} must be a finite number or null")
        else:
            _text(item)
    if result["baseline"] is not None and result["baseline_ref"] is None:
        raise ValueError("a numeric baseline, including zero, requires baseline_ref")
    return result


def plan_selection(selection: dict) -> dict:
    """Validate a proposed route and defer drafts that lack required evidence."""
    catalog = load_catalog()
    profile_ids = {p["id"] for p in catalog["profiles"]}
    prompts = {p["id"]: p for p in catalog["prompts"]}
    evidence_kinds = {kind for p in prompts.values() for kind in p["requires"]}
    _object(selection, {"client_id", "profiles", "goal", "offers", "evidence", "prompt_ids"},
            {"client_id", "profiles", "goal", "evidence"})
    client_id = _text(selection["client_id"])
    goal = _goal(selection["goal"])
    profiles = _list(selection["profiles"])
    selected = []
    for profile in profiles:
        _object(profile, {"id", "confidence", "rationale", "evidence_refs"},
                {"id", "confidence", "rationale", "evidence_refs"})
        if profile["id"] not in profile_ids or profile["id"] in selected:
            raise ValueError("unknown or duplicate profile ID; use [] for unresolved fit")
        if profile["confidence"] not in {"low", "medium", "high"}:
            raise ValueError("profile confidence must be low, medium or high")
        _text(profile["rationale"])
        refs = _list(profile["evidence_refs"])
        if not refs:
            raise ValueError("selected profiles require evidence references")
        for ref in refs:
            _text(ref)
        selected.append(profile["id"])

    offers = []
    offer_ids = set()
    for offer in _list(selection.get("offers", [])):
        _object(offer, {"id", "profile_ids", "goal"}, {"id", "profile_ids", "goal"})
        offer_id = _text(offer["id"])
        if offer_id in offer_ids:
            raise ValueError("duplicate offer ID")
        offer_ids.add(offer_id)
        offer_profiles = _list(offer["profile_ids"])
        if not offer_profiles or any(p not in selected for p in offer_profiles):
            raise ValueError("offer profiles must be selected profiles")
        if len(set(offer_profiles)) != len(offer_profiles):
            raise ValueError("duplicate offer profile")
        offer_goal = _goal(offer["goal"])
        if len(selected) > 1 and (not offer_goal["metric"] or not offer_goal["unit"]):
            raise ValueError("hybrid offers require their own metric and conversion unit")
        offers.append({"id": offer_id, "profile_ids": offer_profiles, "goal": offer_goal})
    hybrid = len(selected) > 1
    if hybrid and set(selected) != {p for o in offers for p in o["profile_ids"]}:
        raise ValueError("hybrids require per-offer goals covering every selected profile")
    # A hybrid's top-level goal cannot replace distinct offer outcomes.
    if hybrid and any(value is not None for value in goal.values()):
        raise ValueError("hybrid goals belong on each offer; leave the top-level goal empty")

    verified_by_offer = {o["id"]: set() for o in offers} if hybrid else {None: set()}
    for evidence in _list(selection["evidence"]):
        _object(evidence, {"kind", "ref", "status", "offer_id"}, {"kind", "ref", "status"})
        if evidence["kind"] not in evidence_kinds:
            raise ValueError("unknown evidence kind")
        _text(evidence["ref"])
        if evidence["status"] not in {"verified", "hypothesis", "unknown"}:
            raise ValueError("unknown evidence status")
        scope = evidence.get("offer_id")
        if scope not in verified_by_offer:
            raise ValueError("hybrid evidence requires an existing offer_id; no blended evidence")
        if evidence["status"] == "verified":
            verified_by_offer[scope].add(evidence["kind"])
    verified = set.intersection(*verified_by_offer.values())
    goals = [o["goal"] for o in offers] if hybrid else [goal]
    if any(g["baseline"] is None or g["baseline_ref"] is None for g in goals):
        verified.discard("baseline")

    requested = _list(selection.get("prompt_ids", catalog["default_prompt_ids"]))
    if any(not isinstance(i, str) or i not in prompts for i in requested):
        raise ValueError("unknown prompt ID")
    if len(requested) != len(set(requested)):
        raise ValueError("duplicate prompt ID")
    routes = []
    for prompt_id in requested:
        prompt = prompts[prompt_id]
        missing = sorted(set(prompt["requires"]) - verified)
        if not selected and prompt_id not in {"R0", "P2", "P4", "C1"}:
            missing.append("business_profile")
        if prompt_id not in {"R0", "P2", "P4", "C1", "C2", "C3", "C4", "C6"}:
            for field in ("metric", "unit", "target", "period", "timezone", "reversal_rules"):
                if any(g[field] is None for g in goals):
                    missing.append(f"goal.{field}")
        routes.append({"id": prompt_id, "status": "deferred" if missing else "ready_to_draft",
                       "missing": missing, "path": prompt["path"],
                       "handoff_skills": prompt["handoff_skills"], "feeds_next": prompt["feeds_next"]})
    questions = []
    if not selected:
        questions.append("What value exchange, purchaser and delivery evidence establishes the business profile?")
    missing_fields = sorted({item for route in routes for item in route["missing"]})
    if missing_fields:
        questions.append("Resolve only gaps material to the requested drafts: " + ", ".join(missing_fields))
    return {"mode": "draft_only", "client_id": client_id, "profiles": profiles,
            "profile_status": "hybrid" if hybrid else "selected" if selected else "unresolved",
            "goal": goal, "offers": offers, "routes": routes, "material_questions": questions,
            "execution_authorized": False, "publication_authorized": False,
            "evidence_checked": "references_only; trusted operator verification remains required"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = plan_selection(json.loads(args.input.read_text(encoding="utf-8")))
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"Invalid selection: {exc}\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

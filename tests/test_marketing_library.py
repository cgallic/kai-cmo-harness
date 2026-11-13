"""Portable library integrity and draft-only selection boundaries."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import marketing_library as library


ROOT = Path(__file__).resolve().parents[1]
CATALOG = library.load_catalog()
PROFILE_IDS = [p["id"] for p in CATALOG["profiles"]]
PROMPT_IDS = ["R0", *[f"P{i}" for i in range(1, 24)], *[f"C{i}" for i in range(1, 7)]]


def profile(profile_id="ecommerce"):
    return {"id": profile_id, "confidence": "medium", "rationale": "Fictional offer evidence",
            "evidence_refs": ["fixture:business-model"]}


def selection(profile_id="ecommerce", prompt_ids=None):
    return {"client_id": "fictional-isolated-workspace", "profiles": [profile(profile_id)],
            "goal": {"metric": "net_completed_outcomes", "unit": "configured_business_unit",
                     "target": 37, "baseline": None, "period": "owner-defined cohort",
                     "timezone": "UTC", "reversal_rules": "exclude reversed outcomes"},
            "evidence": [], "prompt_ids": prompt_ids or ["R0", "P18"]}


def evidence(kind, status="verified", offer_id=None):
    result = {"kind": kind, "ref": f"fixture:{kind}", "status": status}
    if offer_id is not None:
        result["offer_id"] = offer_id
    return result


def test_all_prompt_ids_profile_adaptations_and_handoffs_exist():
    assert [p["id"] for p in CATALOG["prompts"]] == PROMPT_IDS
    assert len(set(PROFILE_IDS)) == 7
    text = (library.LIBRARY / "prompts.md").read_text()
    assert re.findall(r"^### (R0|P\d+|C\d+):", text, re.M) == PROMPT_IDS
    assert text.count("**Business-type adaptation:**") == 29
    for prompt in CATALOG["prompts"]:
        assert set(prompt["applicable_profiles"]) == set(PROFILE_IDS)
        assert set(prompt["feeds_next"]) <= set(PROMPT_IDS)
        assert prompt["required_inputs"] and prompt["output"]
        assert prompt["path"] == f"prompts.md#{prompt['id'].lower()}"
        for skill in prompt["handoff_skills"]:
            assert (ROOT / "harness/skills" / skill / "SKILL.md").is_file()
            assert (ROOT / "harness/skills-v2" / skill / "SKILL.md").is_file()


def test_library_links_resolve_and_private_material_is_absent():
    for path in library.LIBRARY.iterdir():
        text = path.read_text()
        for forbidden in ("@" + "claude", ".ts.net", "Sentinel_", "claude.ai/artifact", "source_events"):
            assert forbidden.lower() not in text.lower(), (path, forbidden)
        # Customer names/examples belong outside the distributable package.
        assert not re.search(r"earnzy|kaicalls|gold.card.collective", text, re.I)
        if path.suffix != ".md":
            continue
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target:
                continue
            relative, _, anchor = target.partition("#")
            destination = (path.parent / relative).resolve() if relative else path
            assert destination.exists(), (path, target)
            if anchor:
                assert f'id="{anchor}"' in destination.read_text(), (path, target)


@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_every_profile_supports_selection_without_product_defaults(profile_id):
    request = selection(profile_id)
    original = copy.deepcopy(request)
    result = library.plan_selection(request)
    assert result["profiles"] == [profile(profile_id)]
    assert result["goal"]["target"] == 37
    assert result["goal"]["baseline"] is None
    assert result["routes"][0]["status"] == "ready_to_draft"
    assert "baseline" in result["routes"][1]["missing"]
    assert not result["execution_authorized"] and not result["publication_authorized"]
    assert request == original


def test_unknown_profile_has_no_fallback_and_only_material_questions():
    request = selection(prompt_ids=["R0", "P12"])
    request["profiles"] = []
    request["goal"] = {}
    result = library.plan_selection(request)
    assert result["profile_status"] == "unresolved"
    assert result["profiles"] == []
    assert result["routes"][0]["status"] == "ready_to_draft"
    assert "business_profile" in result["routes"][1]["missing"]
    assert result["goal"]["baseline"] is None
    assert result["material_questions"]


def test_evidence_and_reconciled_baseline_gate_requested_cro():
    request = selection()
    request["evidence"] = [evidence(k) for k in ("baseline", "bottleneck", "measurement")]
    # A claimed baseline evidence kind cannot turn unknown into a measured zero.
    assert library.plan_selection(request)["routes"][1]["missing"] == ["baseline"]
    request["goal"].update(baseline=0, baseline_ref="fixture:reconciled-zero")
    assert library.plan_selection(request)["routes"][1]["status"] == "ready_to_draft"
    request["evidence"][1]["status"] = "hypothesis"
    assert library.plan_selection(request)["routes"][1]["missing"] == ["bottleneck"]
    del request["goal"]["baseline_ref"]
    with pytest.raises(ValueError, match="baseline_ref"):
        library.plan_selection(request)


def test_journey_discovery_can_start_before_goal_configuration():
    request = selection(prompt_ids=["P3"])
    request["goal"] = {}
    request["evidence"] = [evidence("journey")]
    result = library.plan_selection(request)
    assert result["routes"][0]["status"] == "ready_to_draft"
    assert result["routes"][0]["missing"] == []
    assert all(value is None for value in result["goal"].values())
    assert result["material_questions"] == []
    assert not result["execution_authorized"]


@pytest.mark.parametrize("missing", ["profile", "journey", "verified_journey"])
def test_journey_discovery_still_requires_profile_and_observed_evidence(missing):
    request = selection(prompt_ids=["P3"])
    request["goal"] = {}
    request["evidence"] = [evidence("journey")]
    if missing == "profile":
        request["profiles"] = []
    elif missing == "journey":
        request["evidence"] = []
    else:
        request["evidence"][0]["status"] = "hypothesis"
    route = library.plan_selection(request)["routes"][0]
    assert route["status"] == "deferred"
    expected = "business_profile" if missing == "profile" else "journey"
    assert expected in route["missing"]


@pytest.mark.parametrize("prompt_id", ["P10", "P18", "P22"])
def test_measurement_and_evaluation_keep_goal_requirements(prompt_id):
    request = selection(prompt_ids=[prompt_id])
    request["goal"] = {}
    prompt = next(p for p in CATALOG["prompts"] if p["id"] == prompt_id)
    request["evidence"] = [evidence(kind) for kind in prompt["requires"]]
    route = library.plan_selection(request)["routes"][0]
    assert route["status"] == "deferred"
    assert {f"goal.{field}" for field in prompt["required_goal_fields"]} <= set(route["missing"])
    assert {"metric", "unit", "target", "period", "timezone", "reversal_rules"} == set(prompt["required_goal_fields"])


@pytest.mark.parametrize("field", ["target", "baseline"])
def test_unsupported_numeric_magnitude_is_a_normal_cli_validation_error(field, tmp_path):
    request = selection()
    request["goal"][field] = 10 ** 1000
    with pytest.raises(ValueError, match="supported magnitude"):
        library.plan_selection(request)
    source = tmp_path / "selection.json"
    source.write_text(json.dumps(request))
    result = subprocess.run([sys.executable, str(ROOT / "scripts/marketing_library.py"),
                             "--input", str(source)], capture_output=True, text=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Invalid selection:" in result.stderr
    assert "supported magnitude" in result.stderr
    assert "Traceback" not in result.stderr


def hybrid():
    request = selection("saas", ["P18"])
    request["profiles"].append(profile("b2b-services"))
    goal = dict(request["goal"], baseline=2, baseline_ref="fixture:software-baseline")
    request["offers"] = [
        {"id": "software", "profile_ids": ["saas"],
         "goal": dict(goal, metric="retained_paying_accounts", unit="accounts")},
        {"id": "consulting", "profile_ids": ["b2b-services"],
         "goal": dict(goal, metric="delivered_paid_engagements", unit="engagements",
                      baseline=1, baseline_ref="fixture:consulting-baseline")},
    ]
    request["goal"] = {}
    return request


def test_hybrid_goals_and_evidence_stay_separate():
    request = hybrid()
    request["evidence"] = [evidence(k, offer_id=o) for o in ("software", "consulting")
                           for k in ("baseline", "measurement", "bottleneck")]
    result = library.plan_selection(request)
    assert result["profile_status"] == "hybrid"
    assert [o["goal"]["unit"] for o in result["offers"]] == ["accounts", "engagements"]
    assert result["goal"]["baseline"] is None
    assert result["routes"][0]["status"] == "ready_to_draft"
    request["evidence"].pop()
    assert library.plan_selection(request)["routes"][0]["missing"] == ["bottleneck"]
    request["evidence"].append(evidence("bottleneck"))
    with pytest.raises(ValueError, match="offer_id"):
        library.plan_selection(request)


@pytest.mark.parametrize("mutation", [
    lambda r: r.pop("offers"),
    lambda r: r["offers"].pop(),
    lambda r: r["offers"][0]["goal"].pop("unit"),
    lambda r: r["goal"].update(metric="blended_conversions"),
])
def test_hybrid_rejects_missing_or_blended_outcomes(mutation):
    request = hybrid()
    mutation(request)
    with pytest.raises(ValueError):
        library.plan_selection(request)


@pytest.mark.parametrize("prompt_id,required", [
    ("P14", "consent"), ("P21", "approvals"), ("C1", "sharing_scope"),
    ("C5", "public_use_scope"), ("C6", "reuse_scope"),
])
def test_client_and_channel_drafts_require_scoped_evidence(prompt_id, required):
    request = selection(prompt_ids=[prompt_id])
    route = library.plan_selection(request)["routes"][0]
    assert route["status"] == "deferred"
    assert required in route["missing"]


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(execute=True),
    lambda r: r.update(publish=True),
    lambda r: r.update(approved=True),
    lambda r: r.update(prompt_ids=["P24"]),
    lambda r: r.update(prompt_ids=["R0", "R0"]),
    lambda r: r["profiles"][0].update(id="unknown-type"),
    lambda r: r["profiles"][0].update(evidence_refs=[]),
    lambda r: r["goal"].update(target=float("nan")),
    lambda r: r["goal"].update(baseline=True),
])
def test_invalid_or_execution_requests_are_rejected(mutation):
    request = selection()
    mutation(request)
    with pytest.raises(ValueError):
        library.plan_selection(request)


def test_cli_writes_only_stdout_and_rejects_execution_flags(tmp_path):
    source = tmp_path / "selection.json"
    source.write_text(json.dumps(selection()))
    before = source.read_bytes()
    command = [sys.executable, str(ROOT / "scripts/marketing_library.py"), "--input", str(source)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["mode"] == "draft_only"
    assert source.read_bytes() == before
    assert list(tmp_path.iterdir()) == [source]
    invalid = subprocess.run([*command, "--execute"], cwd=tmp_path, capture_output=True, text=True)
    assert invalid.returncode == 2


def test_discovery_and_plugin_copies_are_complete():
    for skills in ("skills", "skills-v2"):
        for skill in ("kai", "kai-growth-plan"):
            assert "marketing-growth-library/README.md" in (ROOT / "harness" / skills / skill / "SKILL.md").read_text()
    for plugin in ("kai-marketing-os", "kai-marketing-os-v2"):
        root = ROOT / "plugins" / plugin
        for source in library.LIBRARY.iterdir():
            assert (root / source.relative_to(ROOT)).read_bytes() == source.read_bytes()
        assert (root / "scripts/marketing_library.py").read_bytes() == (ROOT / "scripts/marketing_library.py").read_bytes()

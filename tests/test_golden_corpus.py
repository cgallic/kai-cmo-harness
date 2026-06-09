"""Golden corpus regression tests for the deterministic quality gates.

The corpus lives in evals/golden/ with verdicts in manifest.json.
See docs/system/learning-loop.md — any gate change must keep these passing,
and promotions into a gate must add a case.
"""

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "quality_gates" / "golden_check.py"
MANIFEST = REPO_ROOT / "evals" / "golden" / "manifest.json"


def _load_runner():
    spec = importlib.util.spec_from_file_location("golden_check", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cases = json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", _cases, ids=[c["id"] for c in _cases])
def test_golden_case(case):
    mod = _load_runner()
    result = mod.run_case(case)
    assert result["ok"], result["detail"]


def test_manifest_covers_both_deterministic_gates():
    gates = {c["gate"] for c in _cases}
    assert {"banned_word_check", "seo_lint"} <= gates


def test_every_gate_has_pass_and_fail_direction():
    """A gate tested only in one direction can silently become always-pass or always-fail."""
    by_gate = {}
    for c in _cases:
        by_gate.setdefault(c["gate"], set()).add(c["expect"])
    for gate, directions in by_gate.items():
        assert directions == {"pass", "fail"}, (
            f"gate {gate!r} only has {directions} cases — add the missing direction"
        )

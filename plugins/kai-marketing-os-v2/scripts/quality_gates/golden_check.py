#!/usr/bin/env python3
"""
Golden corpus runner — regression tests for the quality gates themselves.

The gates are the harness's source of truth, so changes to them must be
provable. evals/golden/manifest.json maps content samples to known correct
verdicts. This runner executes the deterministic gates (banned words, SEO
lint) against every sample and fails if any verdict changed.

Rules:
  - Editing a gate script, banned-word tier, or overclaim pattern requires
    this corpus to pass.
  - Promoting a lesson into a gate (see memory/MEMORY.md graduation ladder)
    requires ADDING a case here that proves the new check.

Usage:
  python scripts/quality_gates/golden_check.py
  python scripts/quality_gates/golden_check.py --json

Stdlib only. No credentials, no network. Exit 0 = corpus intact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO_ROOT / "evals" / "golden"
MANIFEST = GOLDEN_DIR / "manifest.json"


def _load_module(name: str):
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_golden_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_case(case: dict) -> dict:
    """Run one golden case. Returns {id, ok, detail}."""
    sample_path = GOLDEN_DIR / case["file"]
    if not sample_path.exists():
        return {"id": case["id"], "ok": False, "detail": f"missing sample file {sample_path}"}
    content = sample_path.read_text(encoding="utf-8")

    gate = case["gate"]
    if gate == "banned_word_check":
        mod = _load_module("banned_word_check")
        result = mod.check_content(content)
        passed = result["passed"]
        failure_text = " ".join(h["word"] for h in result["tier1"])
    elif gate == "seo_lint":
        mod = _load_module("seo_lint")
        result = mod.lint(content, case["keyword"])
        passed = result["passed"]
        failure_text = " ".join(result["errors"])
    else:
        return {"id": case["id"], "ok": False, "detail": f"unknown gate {gate!r}"}

    expect_pass = case["expect"] == "pass"
    if passed != expect_pass:
        return {
            "id": case["id"],
            "ok": False,
            "detail": (
                f"expected {case['expect'].upper()} but gate returned "
                f"{'PASS' if passed else 'FAIL'} — failures: {failure_text or '(none)'}"
            ),
        }

    for needle in case.get("expect_failures_contain", []):
        if needle.lower() not in failure_text.lower():
            return {
                "id": case["id"],
                "ok": False,
                "detail": f"expected failure output to mention {needle!r}; got: {failure_text}",
            }

    return {"id": case["id"], "ok": True, "detail": "verdict matches"}


def run_golden() -> tuple[bool, list[dict]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results = [run_case(case) for case in manifest["cases"]]
    return all(r["ok"] for r in results), results


def main() -> int:
    # A Windows console defaults to cp1252, which cannot encode the status
    # glyphs below — the gate would die with UnicodeEncodeError before printing
    # its own result. Force UTF-8 where the stream supports being reconfigured.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

    parser = argparse.ArgumentParser(description="Run the quality-gate golden corpus")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    ok, results = run_golden()

    if args.json:
        print(json.dumps({"passed": ok, "results": results}, indent=2))
    else:
        print(f"\n{'✅' if ok else '❌'} Golden corpus: {sum(r['ok'] for r in results)}/{len(results)} cases intact")
        print("─" * 40)
        for r in results:
            mark = "✓" if r["ok"] else "✗"
            print(f"  {mark} {r['id']}: {r['detail']}")
        if not ok:
            print("\n  A gate verdict changed. Either fix the gate regression, or — if the")
            print("  change is intentional — update the corpus and say why in the commit.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

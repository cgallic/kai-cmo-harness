"""Static checks for SDR operating-loop situation YAML files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOP_LEVEL = {
    "id",
    "version",
    "category",
    "workflow",
    "risk_tier",
    "user_request",
    "workspace_state",
    "required_tool_choices",
    "expected_artifacts",
    "hard_fail_conditions",
    "deterministic_checks",
}

ALLOWED_WORKFLOWS = {
    "sdr-package",
    "sdr-reply-triage",
    "sales-meeting-prep",
}

ALLOWED_RISK_TIERS = {"low", "medium", "high", "critical"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("file must contain a YAML object")
    return data


def check_situation(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = load_yaml(path)
    except Exception as exc:  # noqa: BLE001 - report all YAML failures.
        return [f"YAML load failed: {exc}"]

    missing = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    if data.get("category") != "sdr-operating-loop":
        errors.append("category must be sdr-operating-loop")

    if data.get("workflow") not in ALLOWED_WORKFLOWS:
        errors.append(
            "workflow must be one of: " + ", ".join(sorted(ALLOWED_WORKFLOWS))
        )

    if data.get("risk_tier") not in ALLOWED_RISK_TIERS:
        errors.append(
            "risk_tier must be one of: " + ", ".join(sorted(ALLOWED_RISK_TIERS))
        )

    required_tool_choices = data.get("required_tool_choices")
    if not isinstance(required_tool_choices, dict):
        errors.append("required_tool_choices must be an object")
    else:
        if not required_tool_choices.get("should"):
            errors.append("required_tool_choices.should must be non-empty")
        if not required_tool_choices.get("should_not"):
            errors.append("required_tool_choices.should_not must be non-empty")

    expected_artifacts = data.get("expected_artifacts")
    if not isinstance(expected_artifacts, list) or not expected_artifacts:
        errors.append("expected_artifacts must be a non-empty list")

    hard_fails = data.get("hard_fail_conditions")
    if not isinstance(hard_fails, list) or not hard_fails:
        errors.append("hard_fail_conditions must be a non-empty list")

    deterministic_checks = data.get("deterministic_checks")
    if not isinstance(deterministic_checks, list) or not deterministic_checks:
        errors.append("deterministic_checks must be a non-empty list")

    return errors


def iter_yaml_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.yaml"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SDR loop eval situations.")
    parser.add_argument("path", help="Situation YAML file or directory.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    args = parser.parse_args()

    target = Path(args.path)
    files = iter_yaml_files(target)
    if not files:
        raise SystemExit(f"No YAML files found at {target}")

    results = []
    failed = False
    for file_path in files:
        errors = check_situation(file_path)
        if errors:
            failed = True
        results.append(
            {
                "file": str(file_path),
                "passed": not errors,
                "errors": errors,
            }
        )

    if args.json:
        print(json.dumps({"passed": not failed, "results": results}, indent=2))
    else:
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status} {result['file']}")
            for error in result["errors"]:
                print(f"  - {error}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

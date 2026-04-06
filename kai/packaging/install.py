"""Kai Marketing OS — Installer.

Handles prerequisite checking, dependency verification, directory scaffolding,
configuration generation, and post-install validation.  Designed to work
without any external dependencies so it can bootstrap itself.

Usage::

    from kai.packaging.install import Installer

    result = Installer("/path/to/project").install()
    if result.success:
        print("Ready:", result.next_steps)
    else:
        for err in result.errors:
            print("ERROR:", err)
"""

from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

@dataclass
class InstallationResult:
    """Full report from an installation run."""

    success: bool = False
    python_version: str = ""
    python_version_ok: bool = False
    dependencies_installed: List[str] = field(default_factory=list)
    dependencies_failed: List[str] = field(default_factory=list)
    directories_created: List[str] = field(default_factory=list)
    config_generated: bool = False
    config_path: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyCheck:
    """Status of a single Python package dependency."""

    name: str = ""
    required_version: Optional[str] = None
    installed: bool = False
    installed_version: Optional[str] = None
    required: bool = True
    purpose: str = ""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Dependency registry
# ---------------------------------------------------------------------------

_DEPENDENCIES: List[Dict[str, Any]] = [
    {
        "name": "pyyaml",
        "import_name": "yaml",
        "required": True,
        "purpose": "Configuration file parsing and generation",
    },
    {
        "name": "fastapi",
        "import_name": "fastapi",
        "required": False,
        "purpose": "Gateway / remote execution surface (optional)",
    },
    {
        "name": "uvicorn",
        "import_name": "uvicorn",
        "required": False,
        "purpose": "ASGI server for the gateway (optional)",
    },
    {
        "name": "httpx",
        "import_name": "httpx",
        "required": False,
        "purpose": "HTTP client for API connectors (optional)",
    },
    {
        "name": "python-dotenv",
        "import_name": "dotenv",
        "required": False,
        "purpose": "Load .env files for environment variable management (optional)",
    },
]


# ---------------------------------------------------------------------------
# Installer
# ---------------------------------------------------------------------------

class Installer:
    """Bootstraps a Kai workspace from scratch.

    Parameters
    ----------
    target_dir:
        Root directory of the Kai project (where config.yaml lives).
    """

    MIN_PYTHON = (3, 9)

    def __init__(self, target_dir: str) -> None:
        self.target_dir = Path(target_dir).resolve()

    # ------------------------------------------------------------------
    # Prerequisites
    # ------------------------------------------------------------------

    def check_prerequisites(self) -> Dict[str, Any]:
        """Check Python version and required system tools.

        Returns a dict with keys:
        - python_version (str)
        - python_ok (bool)
        - git_available (bool)
        - git_version (str or None)
        """
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_ok = sys.version_info >= self.MIN_PYTHON

        git_available = False
        git_version: Optional[str] = None
        git_path = shutil.which("git")
        if git_path:
            try:
                result = subprocess.run(
                    [git_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    git_available = True
                    raw = result.stdout.strip()
                    # Typical output: "git version 2.43.0"
                    parts = raw.split()
                    git_version = parts[-1] if parts else raw
            except (subprocess.TimeoutExpired, OSError):
                pass

        return {
            "python_version": py_version,
            "python_ok": py_ok,
            "git_available": git_available,
            "git_version": git_version,
        }

    # ------------------------------------------------------------------
    # Dependency checking
    # ------------------------------------------------------------------

    def check_dependencies(self) -> List[DependencyCheck]:
        """Probe each dependency and return its status."""
        results: List[DependencyCheck] = []
        for dep in _DEPENDENCIES:
            check = DependencyCheck(
                name=dep["name"],
                required=dep["required"],
                purpose=dep["purpose"],
            )
            import_name = dep["import_name"]
            try:
                mod = importlib.import_module(import_name)
                check.installed = True
                check.installed_version = getattr(mod, "__version__", None)
                # Some packages expose version through metadata instead
                if check.installed_version is None:
                    try:
                        import importlib.metadata as _meta
                        check.installed_version = _meta.version(dep["name"])
                    except Exception:
                        check.installed_version = "unknown"
            except ImportError:
                check.installed = False
            results.append(check)
        return results

    # ------------------------------------------------------------------
    # Directory scaffold
    # ------------------------------------------------------------------

    def create_directory_structure(self, business_id: str = "default") -> List[str]:
        """Create the workspace directory tree for a business.

        Returns the list of directory paths that were created (or already
        existed).
        """
        workspace_root = self.target_dir / "workspace"
        subdirs = [
            workspace_root,
            workspace_root / business_id,
            workspace_root / business_id / "audit",
            workspace_root / business_id / "memory",
            workspace_root / business_id / "execution",
            workspace_root / business_id / "content",
            workspace_root / business_id / "config",
        ]
        created: List[str] = []
        for d in subdirs:
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
        return created

    # ------------------------------------------------------------------
    # Config generation
    # ------------------------------------------------------------------

    def generate_config(self, template_path: str = "config.example.yaml") -> str:
        """Read a config template and write config.yaml with placeholders.

        Tries YAML parsing first (pyyaml); falls back to a plain-text copy
        with value substitution when pyyaml is unavailable.

        Returns the absolute path to the generated config file.
        """
        template_file = self.target_dir / template_path
        output_file = self.target_dir / "config.yaml"

        if not template_file.exists():
            raise FileNotFoundError(
                f"Config template not found: {template_file}"
            )

        raw_text = template_file.read_text(encoding="utf-8")

        # Attempt structured parse via pyyaml
        try:
            import yaml  # type: ignore[import-untyped]

            data = yaml.safe_load(raw_text)
            if data is None:
                data = {}

            # Inject placeholder values for operator customization
            data.setdefault("workspace", {})
            ws = data["workspace"]
            ws.setdefault("id", "my-business")
            ws.setdefault("name", "My Business")
            ws.setdefault("description", "")
            ws.setdefault("primary_user", "operator")
            ws.setdefault("product_mode", "clone")
            ws.setdefault("surfaces", ["local"])

            data.setdefault("paths", {})
            data.setdefault("products", [])

            output_text = yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        except ImportError:
            # Fallback: copy the template verbatim, replacing obvious
            # placeholder values the operator will need to change.
            output_text = raw_text.replace(
                'id: "kai-marketing-os"', 'id: "my-business"'
            ).replace(
                'name: "Kai Marketing OS"', 'name: "My Business"'
            )

        output_file.write_text(output_text, encoding="utf-8")
        return str(output_file)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_installation(self) -> Dict[str, Any]:
        """Verify the installation is healthy.

        Returns ``{valid: bool, issues: list[str]}``.
        """
        issues: List[str] = []

        # Check workspace directory
        workspace = self.target_dir / "workspace"
        if not workspace.is_dir():
            issues.append("workspace/ directory missing")

        # Check config file
        config_path = self.target_dir / "config.yaml"
        if not config_path.exists():
            issues.append("config.yaml not found — run generate_config()")
        else:
            # Validate YAML syntax
            raw = config_path.read_text(encoding="utf-8")
            try:
                import yaml  # type: ignore[import-untyped]
                parsed = yaml.safe_load(raw)
                if not isinstance(parsed, dict):
                    issues.append("config.yaml is not a valid YAML mapping")
            except ImportError:
                # Fall back to JSON parse (config.yaml is often yaml-superset)
                try:
                    import json
                    json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    # Can't validate without pyyaml — warn but don't fail
                    pass
            except Exception as exc:
                issues.append(f"config.yaml parse error: {exc}")

        # Check that required Python modules are importable
        for dep in _DEPENDENCIES:
            if not dep["required"]:
                continue
            try:
                importlib.import_module(dep["import_name"])
            except ImportError:
                issues.append(
                    f"Required Python package '{dep['name']}' is not installed. "
                    f"Run: pip install {dep['name']}"
                )

        return {"valid": len(issues) == 0, "issues": issues}

    # ------------------------------------------------------------------
    # Full install flow
    # ------------------------------------------------------------------

    def install(self, business_id: str = "default") -> InstallationResult:
        """Run the complete installation pipeline.

        1. Check prerequisites (Python, git)
        2. Check and report dependencies
        3. Create directory structure
        4. Generate config from template
        5. Validate the installation

        Returns an :class:`InstallationResult` with full details.
        """
        result = InstallationResult()

        # 1. Prerequisites
        prereqs = self.check_prerequisites()
        result.python_version = prereqs["python_version"]
        result.python_version_ok = prereqs["python_ok"]

        if not prereqs["python_ok"]:
            result.errors.append(
                f"Python {'.'.join(str(v) for v in self.MIN_PYTHON)}+ required, "
                f"found {prereqs['python_version']}"
            )

        if not prereqs["git_available"]:
            result.warnings.append(
                "git is not installed. Version control and plugin installs "
                "will not work. Install from https://git-scm.com"
            )

        # 2. Dependencies
        dep_checks = self.check_dependencies()
        for check in dep_checks:
            if check.installed:
                label = f"{check.name}=={check.installed_version}" if check.installed_version else check.name
                result.dependencies_installed.append(label)
            else:
                result.dependencies_failed.append(check.name)
                if check.required:
                    result.errors.append(
                        f"Required package '{check.name}' is missing — "
                        f"run: pip install {check.name}"
                    )
                else:
                    result.warnings.append(
                        f"Optional package '{check.name}' not installed "
                        f"({check.purpose})"
                    )

        # 3. Directory structure
        try:
            created = self.create_directory_structure(business_id)
            result.directories_created = created
        except OSError as exc:
            result.errors.append(f"Failed to create directories: {exc}")

        # 4. Config generation
        try:
            config_path = self.generate_config()
            result.config_generated = True
            result.config_path = config_path
        except FileNotFoundError as exc:
            result.warnings.append(str(exc))
        except OSError as exc:
            result.errors.append(f"Failed to generate config: {exc}")

        # 5. Validation
        validation = self.validate_installation()
        if not validation["valid"]:
            for issue in validation["issues"]:
                # Avoid duplicating errors already captured
                if issue not in result.errors:
                    result.errors.append(issue)

        # Determine overall success
        result.success = len(result.errors) == 0

        # Build next-steps guidance
        if result.success:
            result.next_steps = [
                "Edit config.yaml with your business details",
                "Run the setup wizard: from kai.packaging.setup import SetupWizard",
                "Or start directly: /kai-start in Claude Code",
            ]
        else:
            if not result.python_version_ok:
                result.next_steps.append(
                    f"Upgrade Python to {'.'.join(str(v) for v in self.MIN_PYTHON)}+"
                )
            for dep in result.dependencies_failed:
                # Only surface required deps in next_steps
                dep_meta = next(
                    (d for d in _DEPENDENCIES if d["name"] == dep and d["required"]),
                    None,
                )
                if dep_meta:
                    result.next_steps.append(f"pip install {dep}")
            if not result.next_steps:
                result.next_steps.append("Review the errors above and retry")

        return result

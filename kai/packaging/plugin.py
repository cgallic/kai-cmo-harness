"""Kai Marketing OS — Plugin packaging and installation.

Defines how Kai skills, knowledge, and configuration can be bundled into
distributable plugins and installed into any Claude Code-compatible project.

Three components:

- **PluginManifest** — declares what a plugin contains and requires.
- **PluginPackager** — scans a source directory and builds a distributable
  plugin directory with manifest.
- **PluginInstaller** — installs a plugin into a target project and can
  uninstall it cleanly.

Usage::

    # Package a plugin
    packager = PluginPackager("/path/to/plugin-source")
    manifest = packager.create_manifest()
    output = packager.package("/path/to/output")

    # Install a plugin
    installer = PluginInstaller("/path/to/target-project")
    result = installer.install("/path/to/output/my-plugin")

    # Uninstall
    result = installer.uninstall("my-plugin")
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Manifest model
# ---------------------------------------------------------------------------

@dataclass
class PluginManifest:
    """Declarative manifest for a Kai plugin package."""

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    compatibility: str = ">=0.3.0"
    skill_files: List[str] = field(default_factory=list)
    knowledge_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    hooks: List[Dict[str, str]] = field(default_factory=list)
    install_instructions: str = ""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), indent=2, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Build a PluginManifest from a raw dict (e.g. parsed JSON)."""
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            compatibility=data.get("compatibility", ">=0.3.0"),
            skill_files=list(data.get("skill_files", [])),
            knowledge_files=list(data.get("knowledge_files", [])),
            config_files=list(data.get("config_files", [])),
            dependencies=list(data.get("dependencies", [])),
            hooks=[dict(h) for h in data.get("hooks", [])],
            install_instructions=data.get("install_instructions", ""),
        )

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """Load a manifest from a JSON file on disk."""
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return cls.from_dict(data)


# ---------------------------------------------------------------------------
# PluginPackager
# ---------------------------------------------------------------------------

class PluginPackager:
    """Scans a source directory and builds a distributable plugin.

    Parameters
    ----------
    source_dir:
        Root of the plugin source. Expected to contain subdirectories
        like ``skills/``, ``knowledge/``, ``config/``, and optionally
        a ``manifest.json``.
    """

    MANIFEST_FILENAME = "manifest.json"

    def __init__(self, source_dir: str) -> None:
        self.source_dir = Path(source_dir).resolve()

    def create_manifest(self) -> PluginManifest:
        """Scan source directory and generate a manifest.

        If a ``manifest.json`` already exists in the source, it is loaded
        and augmented with any discovered files not already listed.
        Otherwise a fresh manifest is generated from the directory layout.
        """
        manifest_path = self.source_dir / self.MANIFEST_FILENAME
        if manifest_path.exists():
            manifest = PluginManifest.from_file(manifest_path)
        else:
            manifest = PluginManifest(
                name=self.source_dir.name,
                description=f"Kai plugin: {self.source_dir.name}",
            )

        # Discover files
        discovered_skills = self._scan_relative("skills")
        discovered_knowledge = self._scan_relative("knowledge")
        discovered_config = self._scan_relative("config")

        # Merge without duplicates
        manifest.skill_files = _merge_unique(manifest.skill_files, discovered_skills)
        manifest.knowledge_files = _merge_unique(
            manifest.knowledge_files, discovered_knowledge
        )
        manifest.config_files = _merge_unique(manifest.config_files, discovered_config)

        return manifest

    def package(self, output_path: str) -> str:
        """Create a distributable plugin directory.

        Copies all referenced files from the source into a clean output
        directory alongside the manifest. Returns the output path.
        """
        output = Path(output_path).resolve()
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)

        manifest = self.create_manifest()

        # Copy files by category
        for rel_path in manifest.skill_files:
            self._copy_file(rel_path, "skills", output / "skills")
        for rel_path in manifest.knowledge_files:
            self._copy_file(rel_path, "knowledge", output / "knowledge")
        for rel_path in manifest.config_files:
            self._copy_file(rel_path, "config", output / "config")

        # Copy hook handler files
        for hook in manifest.hooks:
            handler = hook.get("handler_file", "")
            if handler:
                src = self.source_dir / handler
                if src.exists():
                    dest = output / handler
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src), str(dest))

        # Write manifest
        manifest_out = output / self.MANIFEST_FILENAME
        manifest_out.write_text(manifest.to_json(), encoding="utf-8")

        return str(output)

    def validate_plugin(self, plugin_dir: str) -> Dict[str, Any]:
        """Validate that a plugin directory is well-formed.

        Returns ``{valid: bool, issues: list[str]}``.
        """
        pdir = Path(plugin_dir).resolve()
        issues: List[str] = []

        manifest_path = pdir / self.MANIFEST_FILENAME
        if not manifest_path.exists():
            issues.append(f"Missing {self.MANIFEST_FILENAME}")
            return {"valid": False, "issues": issues}

        try:
            manifest = PluginManifest.from_file(manifest_path)
        except (json.JSONDecodeError, KeyError) as exc:
            issues.append(f"Invalid manifest: {exc}")
            return {"valid": False, "issues": issues}

        if not manifest.name:
            issues.append("Manifest missing 'name' field")
        if not manifest.version:
            issues.append("Manifest missing 'version' field")

        # Check all referenced files exist
        for rel_path in manifest.skill_files:
            if not (pdir / "skills" / rel_path).exists():
                issues.append(f"Missing skill file: skills/{rel_path}")
        for rel_path in manifest.knowledge_files:
            if not (pdir / "knowledge" / rel_path).exists():
                issues.append(f"Missing knowledge file: knowledge/{rel_path}")
        for rel_path in manifest.config_files:
            if not (pdir / "config" / rel_path).exists():
                issues.append(f"Missing config file: config/{rel_path}")
        for hook in manifest.hooks:
            handler = hook.get("handler_file", "")
            if handler and not (pdir / handler).exists():
                issues.append(f"Missing hook handler: {handler}")

        return {"valid": len(issues) == 0, "issues": issues}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scan_relative(self, subdir: str) -> List[str]:
        """Scan a subdirectory and return relative file paths."""
        target = self.source_dir / subdir
        if not target.is_dir():
            return []
        results: List[str] = []
        for path in sorted(target.rglob("*")):
            if path.is_file():
                results.append(str(path.relative_to(target)))
        return results

    def _copy_file(self, rel_path: str, source_subdir: str, dest_dir: Path) -> None:
        """Copy a single file from source subdir to dest."""
        src = self.source_dir / source_subdir / rel_path
        if not src.exists():
            return
        dest = dest_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))


# ---------------------------------------------------------------------------
# PluginInstaller
# ---------------------------------------------------------------------------

class PluginInstaller:
    """Installs and uninstalls plugins into a target Kai project.

    Parameters
    ----------
    target_dir:
        Root of the target Kai project (where ``harness/skills/``,
        ``knowledge/``, and ``workspace/`` live).
    """

    INSTALL_REGISTRY = ".kai-plugins.json"

    def __init__(self, target_dir: str) -> None:
        self.target_dir = Path(target_dir).resolve()
        self._registry_path = self.target_dir / self.INSTALL_REGISTRY

    def install(self, plugin_dir: str) -> Dict[str, Any]:
        """Install a plugin from a packaged directory.

        Reads the manifest, copies files into the correct project
        locations, and records what was installed for clean uninstall.

        Returns ``{installed_files: list[str], errors: list[str]}``.
        """
        pdir = Path(plugin_dir).resolve()
        manifest_path = pdir / PluginPackager.MANIFEST_FILENAME

        if not manifest_path.exists():
            return {
                "installed_files": [],
                "errors": [f"No manifest found in {plugin_dir}"],
            }

        manifest = PluginManifest.from_file(manifest_path)
        installed: List[str] = []
        errors: List[str] = []

        # Copy skill files to harness/skills/
        for rel_path in manifest.skill_files:
            src = pdir / "skills" / rel_path
            dest = self.target_dir / "harness" / "skills" / rel_path
            result = self._safe_copy(src, dest)
            if result is None:
                installed.append(str(dest))
            else:
                errors.append(result)

        # Copy knowledge files to knowledge/
        for rel_path in manifest.knowledge_files:
            src = pdir / "knowledge" / rel_path
            dest = self.target_dir / "knowledge" / rel_path
            result = self._safe_copy(src, dest)
            if result is None:
                installed.append(str(dest))
            else:
                errors.append(result)

        # Copy config files to workspace/
        for rel_path in manifest.config_files:
            src = pdir / "config" / rel_path
            dest = self.target_dir / "workspace" / rel_path
            result = self._safe_copy(src, dest)
            if result is None:
                installed.append(str(dest))
            else:
                errors.append(result)

        # Copy hook handlers
        for hook in manifest.hooks:
            handler = hook.get("handler_file", "")
            if handler:
                src = pdir / handler
                dest = self.target_dir / handler
                result = self._safe_copy(src, dest)
                if result is None:
                    installed.append(str(dest))
                else:
                    errors.append(result)

        # Record installation for uninstall
        if not errors:
            self._record_install(manifest.name, manifest, installed)

        return {"installed_files": installed, "errors": errors}

    def uninstall(self, plugin_name: str) -> Dict[str, Any]:
        """Remove a previously installed plugin by name.

        Uses the install registry to find and remove all files that
        were copied during installation.

        Returns ``{removed_files: list[str], errors: list[str]}``.
        """
        registry = self._load_registry()
        entry = registry.get(plugin_name)

        if entry is None:
            return {
                "removed_files": [],
                "errors": [f"Plugin '{plugin_name}' is not installed"],
            }

        removed: List[str] = []
        errors: List[str] = []

        for file_path in entry.get("installed_files", []):
            target = Path(file_path)
            if target.exists():
                try:
                    target.unlink()
                    removed.append(file_path)
                    # Clean up empty parent directories
                    self._cleanup_empty_parents(target)
                except OSError as exc:
                    errors.append(f"Failed to remove {file_path}: {exc}")
            else:
                # File already gone — still count as removed
                removed.append(file_path)

        # Remove from registry
        if not errors:
            del registry[plugin_name]
            self._save_registry(registry)

        return {"removed_files": removed, "errors": errors}

    def list_installed(self) -> Dict[str, Dict[str, Any]]:
        """Return the current plugin install registry."""
        return self._load_registry()

    # ------------------------------------------------------------------
    # Registry management
    # ------------------------------------------------------------------

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if not self._registry_path.exists():
            return {}
        try:
            raw = self._registry_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_registry(self, registry: Dict[str, Dict[str, Any]]) -> None:
        self._registry_path.write_text(
            json.dumps(registry, indent=2, sort_keys=False),
            encoding="utf-8",
        )

    def _record_install(
        self,
        plugin_name: str,
        manifest: PluginManifest,
        installed_files: List[str],
    ) -> None:
        registry = self._load_registry()
        registry[plugin_name] = {
            "version": manifest.version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "installed_files": installed_files,
            "manifest": manifest.model_dump(),
        }
        self._save_registry(registry)

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_copy(src: Path, dest: Path) -> Optional[str]:
        """Copy a file, creating parent dirs. Returns error string or None."""
        if not src.exists():
            return f"Source file not found: {src}"
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
            return None
        except OSError as exc:
            return f"Failed to copy {src} -> {dest}: {exc}"

    def _cleanup_empty_parents(self, path: Path) -> None:
        """Remove empty parent directories up to but not including target_dir."""
        parent = path.parent
        while parent != self.target_dir and parent.exists():
            try:
                if not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                else:
                    break
            except OSError:
                break


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _merge_unique(existing: List[str], discovered: List[str]) -> List[str]:
    """Merge two lists, preserving order and removing duplicates."""
    seen = set(existing)
    merged = list(existing)
    for item in discovered:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged

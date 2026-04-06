"""Kai Marketing OS — Packaging, installation, and setup.

This module handles everything needed to go from a fresh checkout to a
running Kai workspace:

- **Installer** — dependency checking, directory creation, config generation.
- **SetupWizard** — interactive guided setup that builds a BusinessProfile
  and workspace config from operator answers.
- **PluginPackager / PluginInstaller** — bundle and install skill, knowledge,
  and config plugins into any Claude Code-compatible project.

Typical usage::

    from kai.packaging.install import Installer
    from kai.packaging.setup import SetupWizard

    result = Installer("/path/to/project").install()
    wizard = SetupWizard("/path/to/project/workspace")
"""

from kai.packaging.install import (
    DependencyCheck,
    InstallationResult,
    Installer,
)
from kai.packaging.plugin import (
    PluginInstaller,
    PluginManifest,
    PluginPackager,
)
from kai.packaging.setup import (
    SetupQuestion,
    SetupResult,
    SetupSection,
    SetupWizard,
)

__all__ = [
    "DependencyCheck",
    "InstallationResult",
    "Installer",
    "PluginInstaller",
    "PluginManifest",
    "PluginPackager",
    "SetupQuestion",
    "SetupResult",
    "SetupSection",
    "SetupWizard",
]

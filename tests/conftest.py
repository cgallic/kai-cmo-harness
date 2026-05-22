"""Pytest bootstrap for local OSS runs.

Ensures the repository root is importable without requiring callers to set
PYTHONPATH manually.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

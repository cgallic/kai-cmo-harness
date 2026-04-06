"""Credential store — resolves credentials_ref pointers to actual credentials.

The IntegrationRegistry stores a ``credentials_ref`` string on each
integration entry, not the credentials themselves.  This module provides
the resolver that turns those refs into usable credential dicts.

Resolution order:
    1. In-memory overrides (for testing).
    2. JSON vault file at ``{data_dir}/credentials.json``.
    3. Environment variable expansion — any string value starting with
       ``$`` is replaced by the corresponding ``os.environ`` value.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.harness_config import get_config


def _default_vault_path() -> Path:
    """Return the default credentials vault path."""
    cfg = get_config()
    return Path(os.environ.get("KAI_CREDENTIALS_PATH", str(cfg.data_dir / "credentials.json")))


def _expand_env_vars(data: Any) -> Any:
    """Recursively replace string values starting with ``$`` using os.environ.

    Examples:
        ``"$GOOGLE_CREDENTIALS_PATH"`` → ``os.environ["GOOGLE_CREDENTIALS_PATH"]``
        ``"$META_ACCESS_TOKEN"`` → ``os.environ["META_ACCESS_TOKEN"]``
        Nested dicts and lists are traversed recursively.
    """
    if isinstance(data, str) and data.startswith("$"):
        env_key = data[1:]
        value = os.environ.get(env_key)
        if value is None:
            raise KeyError(
                f"Environment variable '{env_key}' required by credential "
                f"ref is not set"
            )
        return value
    if isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    return data


class CredentialStore:
    """Resolves ``credentials_ref`` strings to credential dicts.

    Parameters
    ----------
    vault_path : Path, optional
        Path to the JSON vault file.  Defaults to ``{data_dir}/credentials.json``.
    """

    def __init__(self, vault_path: Optional[Path] = None) -> None:
        self._vault_path = vault_path or _default_vault_path()
        self._overrides: Dict[str, Dict[str, Any]] = {}
        self._vault_cache: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, credentials_ref: str) -> Dict[str, Any]:
        """Return the credential dict for *credentials_ref*.

        Raises ``KeyError`` if the ref is not found in overrides or the
        vault file.  Environment variable expansion happens at resolve
        time, not at load time.
        """
        # 1. In-memory overrides (testing)
        if credentials_ref in self._overrides:
            return _expand_env_vars(copy.deepcopy(self._overrides[credentials_ref]))

        # 2. Vault file
        vault = self._load_vault()
        if credentials_ref in vault:
            return _expand_env_vars(copy.deepcopy(vault[credentials_ref]))

        raise KeyError(
            f"Credential ref '{credentials_ref}' not found in overrides "
            f"or vault at {self._vault_path}"
        )

    def register(self, credentials_ref: str, credentials: Dict[str, Any]) -> None:
        """Store credentials under *credentials_ref* and persist to vault file.

        Existing entries with the same ref are overwritten.
        """
        vault = self._load_vault()
        vault[credentials_ref] = credentials
        self._write_vault(vault)
        # Invalidate cache so next resolve() picks up the change.
        self._vault_cache = None

    def set_override(self, credentials_ref: str, credentials: Dict[str, Any]) -> None:
        """Set an in-memory override (highest priority, not persisted)."""
        self._overrides[credentials_ref] = credentials

    def clear_overrides(self) -> None:
        """Remove all in-memory overrides."""
        self._overrides.clear()

    def list_refs(self) -> List[str]:
        """List all registered credential refs (overrides + vault)."""
        vault = self._load_vault()
        refs = set(vault.keys()) | set(self._overrides.keys())
        return sorted(refs)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_vault(self) -> Dict[str, Any]:
        """Load the vault file, returning an empty dict if it does not exist."""
        if self._vault_cache is not None:
            return self._vault_cache
        if not self._vault_path.exists():
            self._vault_cache = {}
            return self._vault_cache
        loaded = json.loads(self._vault_path.read_text(encoding="utf-8"))
        self._vault_cache = loaded if isinstance(loaded, dict) else {}
        return self._vault_cache

    def _write_vault(self, data: Dict[str, Any]) -> None:
        """Atomically write the vault file."""
        self._vault_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._vault_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._vault_path)

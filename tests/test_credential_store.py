"""Tests for CredentialStore — vault read/write, env expansion, overrides."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from kai.execution.credentials import CredentialStore, _expand_env_vars


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_vault(data: dict) -> Path:
    """Write a temporary vault JSON file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    Path(path).write_text(json.dumps(data), encoding="utf-8")
    return Path(path)


# ---------------------------------------------------------------------------
# _expand_env_vars
# ---------------------------------------------------------------------------


class TestExpandEnvVars:
    def test_expands_string(self, monkeypatch):
        monkeypatch.setenv("MY_TOKEN", "secret123")
        assert _expand_env_vars("$MY_TOKEN") == "secret123"

    def test_plain_string_unchanged(self):
        assert _expand_env_vars("hello") == "hello"

    def test_missing_env_var_raises(self, monkeypatch):
        monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
        with pytest.raises(KeyError, match="DOES_NOT_EXIST"):
            _expand_env_vars("$DOES_NOT_EXIST")

    def test_nested_dict(self, monkeypatch):
        monkeypatch.setenv("A", "alpha")
        monkeypatch.setenv("B", "bravo")
        result = _expand_env_vars({"key1": "$A", "key2": {"nested": "$B"}})
        assert result == {"key1": "alpha", "key2": {"nested": "bravo"}}

    def test_list(self, monkeypatch):
        monkeypatch.setenv("X", "val")
        result = _expand_env_vars(["$X", "literal", 42])
        assert result == ["val", "literal", 42]

    def test_non_string_passthrough(self):
        assert _expand_env_vars(42) == 42
        assert _expand_env_vars(True) is True
        assert _expand_env_vars(None) is None


# ---------------------------------------------------------------------------
# CredentialStore — vault file
# ---------------------------------------------------------------------------


class TestCredentialStoreVault:
    def test_resolve_from_vault(self, monkeypatch):
        monkeypatch.setenv("MY_KEY", "the-secret")
        vault = _temp_vault({"my_ref": {"api_key": "$MY_KEY", "extra": "literal"}})
        try:
            store = CredentialStore(vault_path=vault)
            result = store.resolve("my_ref")
            assert result == {"api_key": "the-secret", "extra": "literal"}
        finally:
            vault.unlink(missing_ok=True)

    def test_resolve_missing_ref_raises(self):
        vault = _temp_vault({})
        try:
            store = CredentialStore(vault_path=vault)
            with pytest.raises(KeyError, match="not_here"):
                store.resolve("not_here")
        finally:
            vault.unlink(missing_ok=True)

    def test_resolve_missing_vault_file_raises(self, tmp_path):
        store = CredentialStore(vault_path=tmp_path / "nonexistent.json")
        with pytest.raises(KeyError, match="some_ref"):
            store.resolve("some_ref")

    def test_register_and_resolve(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        store = CredentialStore(vault_path=vault_path)
        store.register("new_ref", {"token": "abc"})

        # Verify file was written
        assert vault_path.exists()
        data = json.loads(vault_path.read_text(encoding="utf-8"))
        assert "new_ref" in data

        # Resolve from a fresh store (no cache)
        store2 = CredentialStore(vault_path=vault_path)
        result = store2.resolve("new_ref")
        assert result == {"token": "abc"}

    def test_register_overwrites(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        store = CredentialStore(vault_path=vault_path)
        store.register("ref", {"v": 1})
        store.register("ref", {"v": 2})

        store2 = CredentialStore(vault_path=vault_path)
        assert store2.resolve("ref") == {"v": 2}


# ---------------------------------------------------------------------------
# CredentialStore — overrides
# ---------------------------------------------------------------------------


class TestCredentialStoreOverrides:
    def test_override_takes_priority(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        vault_path.write_text(json.dumps({"ref": {"source": "vault"}}), encoding="utf-8")

        store = CredentialStore(vault_path=vault_path)
        store.set_override("ref", {"source": "override"})
        assert store.resolve("ref") == {"source": "override"}

    def test_clear_overrides(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        vault_path.write_text(json.dumps({"ref": {"source": "vault"}}), encoding="utf-8")

        store = CredentialStore(vault_path=vault_path)
        store.set_override("ref", {"source": "override"})
        store.clear_overrides()
        assert store.resolve("ref") == {"source": "vault"}

    def test_env_expansion_in_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TOKEN_VAL", "expanded")
        store = CredentialStore(vault_path=tmp_path / "empty.json")
        store.set_override("ref", {"token": "$TOKEN_VAL"})
        assert store.resolve("ref") == {"token": "expanded"}


# ---------------------------------------------------------------------------
# CredentialStore — list_refs
# ---------------------------------------------------------------------------


class TestCredentialStoreListRefs:
    def test_list_refs_combined(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        vault_path.write_text(
            json.dumps({"vault_ref": {"a": 1}, "shared": {"b": 2}}),
            encoding="utf-8",
        )
        store = CredentialStore(vault_path=vault_path)
        store.set_override("override_ref", {"c": 3})
        store.set_override("shared", {"d": 4})

        refs = store.list_refs()
        assert "vault_ref" in refs
        assert "override_ref" in refs
        assert "shared" in refs
        # No duplicates
        assert refs.count("shared") == 1

    def test_list_refs_empty(self, tmp_path):
        store = CredentialStore(vault_path=tmp_path / "nonexistent.json")
        assert store.list_refs() == []


# ---------------------------------------------------------------------------
# CredentialStore — immutability
# ---------------------------------------------------------------------------


class TestCredentialStoreImmutability:
    def test_resolve_returns_copy(self, tmp_path):
        vault_path = tmp_path / "creds.json"
        vault_path.write_text(json.dumps({"ref": {"key": "val"}}), encoding="utf-8")
        store = CredentialStore(vault_path=vault_path)

        result1 = store.resolve("ref")
        result1["key"] = "mutated"
        result2 = store.resolve("ref")
        assert result2["key"] == "val", "resolve should return independent copies"

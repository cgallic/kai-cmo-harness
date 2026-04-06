"""Tests for ConnectorFactory — registry lookup, config construction, errors."""

from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.execution.credentials import CredentialStore
from kai.execution.connector_factory import ConnectorFactory, _CONNECTOR_REGISTRY


# ---------------------------------------------------------------------------
# Config isolation helper (same pattern as test_actions_integrations.py)
# ---------------------------------------------------------------------------


def _with_config(yaml_content: str):
    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(textwrap.dedent(yaml_content))
            handle.flush()
            previous = os.environ.get("CMO_CONFIG_PATH")
            os.environ["CMO_CONFIG_PATH"] = handle.name
            harness_config._config = None
            load_workspace_profile.cache_clear()
            try:
                yield Path(handle.name)
            finally:
                if previous is None:
                    os.environ.pop("CMO_CONFIG_PATH", None)
                else:
                    os.environ["CMO_CONFIG_PATH"] = previous
                harness_config._config = None
                load_workspace_profile.cache_clear()
                try:
                    os.unlink(handle.name)
                except OSError:
                    pass

    return ctx()


YAML_CONTENT = """
workspace:
  id: "kai-test"
  name: "Kai Test Factory"

products: []
"""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestConnectorRegistry:
    def test_analytics_entries_exist(self):
        assert ("analytics", "ga4") in _CONNECTOR_REGISTRY
        assert ("analytics", "gsc") in _CONNECTOR_REGISTRY

    def test_cms_entries_exist(self):
        assert ("website", "wordpress") in _CONNECTOR_REGISTRY
        assert ("website", "shopify") in _CONNECTOR_REGISTRY

    def test_ads_entries_exist(self):
        assert ("paid_media", "google_ads") in _CONNECTOR_REGISTRY
        assert ("paid_media", "meta_ads") in _CONNECTOR_REGISTRY

    def test_lifecycle_entries_exist(self):
        assert ("email", "mailchimp") in _CONNECTOR_REGISTRY
        assert ("email", "loops") in _CONNECTOR_REGISTRY

    def test_social_entries_exist(self):
        assert ("social", "facebook") in _CONNECTOR_REGISTRY
        assert ("social", "tiktok") in _CONNECTOR_REGISTRY

    def test_list_supported(self):
        supported = ConnectorFactory.list_supported()
        assert len(supported) >= 10
        assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in supported)


# ---------------------------------------------------------------------------
# Factory — analytics connectors
# ---------------------------------------------------------------------------


class TestFactoryAnalytics:
    def test_create_ga4_connector(self, tmp_path):
        with _with_config(YAML_CONTENT):
            vault_path = tmp_path / "creds.json"
            vault_path.write_text(
                json.dumps({
                    "ga4_test": {
                        "type": "service_account_file",
                        "path": "/fake/key.json",
                    }
                }),
                encoding="utf-8",
            )
            cred_store = CredentialStore(vault_path=vault_path)
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "analytics",
                "provider": "ga4",
                "credentials_ref": "ga4_test",
                "config": {"property_id": "properties/123456"},
            }

            connector = factory.create(integration)
            assert connector.connector_type == "ga4"
            assert connector.config.property_id == "properties/123456"
            assert connector.config.credentials["path"] == "/fake/key.json"


# ---------------------------------------------------------------------------
# Factory — CMS connectors
# ---------------------------------------------------------------------------


class TestFactoryCMS:
    def test_create_wordpress_connector(self, tmp_path):
        with _with_config(YAML_CONTENT):
            vault_path = tmp_path / "creds.json"
            vault_path.write_text(
                json.dumps({
                    "wp_test": {
                        "site_url": "https://test.example.com",
                        "username": "admin",
                        "password": "app-password-here",
                    }
                }),
                encoding="utf-8",
            )
            cred_store = CredentialStore(vault_path=vault_path)
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "website",
                "provider": "wordpress",
                "credentials_ref": "wp_test",
                "config": {"site_url": "https://test.example.com"},
            }

            connector = factory.create(integration)
            assert hasattr(connector, "config")
            assert connector.config["site_url"] == "https://test.example.com"
            assert connector.config["username"] == "admin"

    def test_create_wordpress_read_only(self, tmp_path):
        with _with_config(YAML_CONTENT):
            vault_path = tmp_path / "creds.json"
            vault_path.write_text(
                json.dumps({"wp_ro": {"site_url": "https://ro.example.com", "username": "u", "password": "p"}}),
                encoding="utf-8",
            )
            cred_store = CredentialStore(vault_path=vault_path)
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "website",
                "provider": "wordpress",
                "credentials_ref": "wp_ro",
                "config": {},
            }

            connector = factory.create_read_only(integration)
            assert connector.read_only is True


# ---------------------------------------------------------------------------
# Factory — error cases
# ---------------------------------------------------------------------------


class TestFactoryErrors:
    def test_unknown_provider_raises(self, tmp_path):
        with _with_config(YAML_CONTENT):
            cred_store = CredentialStore(vault_path=tmp_path / "creds.json")
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "analytics",
                "provider": "unknown_platform",
                "credentials_ref": None,
                "config": {},
            }

            with pytest.raises(KeyError, match="unknown_platform"):
                factory.create(integration)

    def test_missing_credentials_ref_raises(self, tmp_path):
        with _with_config(YAML_CONTENT):
            vault_path = tmp_path / "creds.json"
            vault_path.write_text(json.dumps({}), encoding="utf-8")
            cred_store = CredentialStore(vault_path=vault_path)
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "analytics",
                "provider": "ga4",
                "credentials_ref": "nonexistent_ref",
                "config": {"property_id": "properties/123"},
            }

            with pytest.raises(KeyError, match="nonexistent_ref"):
                factory.create(integration)

    def test_no_credentials_ref_uses_empty_dict(self, tmp_path):
        """When credentials_ref is None, an empty credentials dict is used."""
        with _with_config(YAML_CONTENT):
            cred_store = CredentialStore(vault_path=tmp_path / "creds.json")
            factory = ConnectorFactory(cred_store)

            integration = {
                "channel": "analytics",
                "provider": "ga4",
                "credentials_ref": None,
                "config": {"property_id": "properties/123"},
            }

            connector = factory.create(integration)
            assert connector.config.credentials == {}

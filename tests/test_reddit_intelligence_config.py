import filecmp
from pathlib import Path

import pytest

from scripts import harness_config


def _write_config(tmp_path: Path, body: str) -> Path:
    target = tmp_path / "config.yaml"
    target.write_text(body, encoding="utf-8")
    return target


def test_reddit_intelligence_defaults_are_safe(monkeypatch, tmp_path):
    monkeypatch.setenv("CMO_CONFIG_PATH", str(tmp_path / "missing.yaml"))
    cfg = harness_config.get_reddit_intelligence_config()
    assert cfg.enabled is False
    assert cfg.sheets_enabled is False
    assert cfg.email_enabled is False
    assert cfg.dashboard_host == "127.0.0.1"
    assert cfg.profile == Path("scripts/reddit_monitor/intelligence/profiles/example.json")


def test_reddit_intelligence_loads_yaml_and_environment_overrides(monkeypatch, tmp_path):
    config_path = _write_config(
        tmp_path,
        """reddit_intelligence:
  enabled: true
  profile: profiles/acme.json
  data_dir: runtime/acme
  dashboard_host: 127.0.0.1
  dashboard_port: 9000
  sheets_enabled: false
  email_enabled: false
""",
    )
    monkeypatch.setenv("CMO_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("KAI_REDDIT_DASHBOARD_PORT", "9010")
    monkeypatch.setenv("KAI_REDDIT_EMAIL_ENABLED", "yes")
    cfg = harness_config.get_reddit_intelligence_config()
    assert cfg.enabled is True
    assert cfg.profile == Path("profiles/acme.json")
    assert cfg.data_dir == Path("runtime/acme")
    assert cfg.dashboard_port == 9010
    assert cfg.sheets_enabled is False
    assert cfg.email_enabled is True


def test_reddit_intelligence_rejects_ambiguous_boolean_override(monkeypatch, tmp_path):
    monkeypatch.setenv("CMO_CONFIG_PATH", str(tmp_path / "missing.yaml"))
    monkeypatch.setenv("KAI_REDDIT_INTELLIGENCE_ENABLED", "maybe")
    with pytest.raises(ValueError, match="KAI_REDDIT_INTELLIGENCE_ENABLED"):
        harness_config.get_reddit_intelligence_config()


def test_plugin_packages_ship_the_complete_module():
    """Plugin payloads are real committed files, not symlinks.

    A symlink here materializes as a ~30-byte text file on any Windows checkout
    without core.symlinks=true, and the plugin cache skips symlinks whose target
    escapes the marketplace -- either way the module never reaches the user.
    scripts/sync_plugin_assets.py keeps these copies honest, and its --check
    mode runs in CI.
    """
    root = Path(__file__).resolve().parents[1]
    canonical = root / "scripts" / "reddit_monitor"

    for plugin in ("kai-marketing-os", "kai-marketing-os-v2"):
        shipped = root / "plugins" / plugin / "scripts" / "reddit_monitor"

        assert shipped.is_dir(), f"{plugin} is missing the reddit_monitor payload"
        assert not shipped.is_symlink(), (
            f"{plugin}/scripts/reddit_monitor is a symlink; "
            "plugin payloads must be real files"
        )
        assert (shipped / "intelligence" / "cli.py").is_file()

        top_level = [p.name for p in canonical.iterdir() if p.is_file()]
        _, mismatch, errors = filecmp.cmpfiles(
            canonical, shipped, top_level, shallow=False
        )
        assert not mismatch, f"{plugin} payload differs from canonical: {mismatch}"
        assert not errors, f"{plugin} payload unreadable: {errors}"


def test_doctor_requires_reddit_module_in_plugin_packages():
    import inspect

    from scripts import doctor

    source = inspect.getsource(doctor._check_one_plugin)
    assert '"scripts/reddit_monitor"' in source

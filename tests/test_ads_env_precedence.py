from scripts.ads import _pull_common


def test_process_environment_overrides_repo_env_file(tmp_path, monkeypatch):
    (tmp_path / ".env.local").write_text("META_ACCESS_TOKEN=stale-file-token\n", encoding="utf-8")
    monkeypatch.setattr(_pull_common, "REPO_ROOT", tmp_path)
    monkeypatch.setenv("META_ACCESS_TOKEN", "current-runtime-token")
    _pull_common._env_cache.clear()

    assert _pull_common.env("META_ACCESS_TOKEN") == "current-runtime-token"


def test_repo_env_file_remains_fallback(tmp_path, monkeypatch):
    (tmp_path / ".env.local").write_text("META_ACCESS_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setattr(_pull_common, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    _pull_common._env_cache.clear()

    assert _pull_common.env("META_ACCESS_TOKEN") == "file-token"

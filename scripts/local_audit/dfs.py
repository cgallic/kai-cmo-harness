"""Minimal DataForSEO v3 client with on-disk response caching.

Credentials come from ``DATAFORSEO_LOGIN`` / ``DATAFORSEO_PASSWORD`` (or
``DATAFORSEO_AUTH_B64``). A ``.env`` in the working directory is read if
python-dotenv is installed. Credentials are never logged or written to disk.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://api.dataforseo.com/v3/"


class DataForSEOError(RuntimeError):
    pass


def _auth_header() -> str:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass
    b64 = os.getenv("DATAFORSEO_AUTH_B64", "").strip()
    if not b64:
        login = os.getenv("DATAFORSEO_LOGIN", "")
        password = os.getenv("DATAFORSEO_PASSWORD", "")
        if not login or not password:
            raise DataForSEOError("DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD are not set")
        b64 = base64.b64encode(f"{login}:{password}".encode()).decode()
    return "Basic " + b64


def has_credentials() -> bool:
    try:
        _auth_header()
        return True
    except DataForSEOError:
        return False


class Client:
    def __init__(self, raw_dir: Path, *, use_cache: bool = True):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.use_cache = use_cache
        self.cost = 0.0

    def artifact_path(self, path: str, payload: Any) -> Path:
        key = hashlib.md5((path + json.dumps(payload, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()[:12]
        return self.raw_dir / f"dataforseo_{path.strip('/').replace('/', '_')[:80]}_{key}.json"

    def call(self, path: str, payload: Any = None, *, cache: bool | None = None) -> tuple[dict[str, Any], str]:
        """Return (response, artifact path). ``payload=None`` issues a GET."""
        artifact = self.artifact_path(path, payload)
        use_cache = self.use_cache if cache is None else cache
        if use_cache and artifact.exists():
            return json.loads(artifact.read_text(encoding="utf-8")), artifact.as_posix()
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(
            BASE + path.lstrip("/"),
            data=body,
            method="GET" if payload is None else "POST",
            headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as exc:  # pragma: no cover - network
            raise DataForSEOError(f"{path}: HTTP {exc.code}") from exc
        artifact.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.cost += float(data.get("cost") or 0)
        return data, artifact.as_posix()


def tasks(response: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in (response.get("tasks") or []) if isinstance(t, dict)]


def task_ok(task: dict[str, Any]) -> bool:
    code = task.get("status_code") or 0
    return 20000 <= int(code) < 30000


def first_result(task: dict[str, Any]) -> dict[str, Any]:
    results = task.get("result") or []
    return results[0] if results and isinstance(results[0], dict) else {}

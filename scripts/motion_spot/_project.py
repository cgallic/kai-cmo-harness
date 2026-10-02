"""Shared config for the motion-spot engine.

The engine lives in the Kai install (plugin or repo); the project it renders lives in
the current working directory (or $PROJECT). Every script resolves pages, frames,
audio and out/ against the project, never against this folder.

Env vars (all optional):
  PROJECT   project folder (default: cwd)
  PAGE      page to render, relative to PROJECT (default: index.html)
  QUERY     query string appended to the page URL, e.g. "?n=3" for multi-spot pages
  VW, VH    viewport (default 1920x1080; use 1080x1920 for 9:16)
  META      timing file (default: <page stem>.meta.json next to PAGE, if it exists)
  DUR, FPS  override the meta duration / frame rate
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def project() -> Path:
    return Path(os.environ.get("PROJECT", os.getcwd())).resolve()


def page() -> Path:
    return project() / os.environ.get("PAGE", "index.html")


def page_url() -> str:
    return page().as_uri() + os.environ.get("QUERY", "")


def viewport() -> dict:
    return {"width": int(os.environ.get("VW", 1920)), "height": int(os.environ.get("VH", 1080))}


def meta() -> dict:
    """dur / fps / cuts / fast for the page: meta file first, env overrides second."""
    path = os.environ.get("META")
    p = project() / path if path else page().with_suffix(".meta.json")
    m = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    m.setdefault("dur", 24.0)
    m.setdefault("fps", 60)
    m.setdefault("cuts", [])
    m.setdefault("fast", [])
    if os.environ.get("DUR"):
        m["dur"] = float(os.environ["DUR"])
    if os.environ.get("FPS"):
        m["fps"] = int(os.environ["FPS"])
    m["fast"] = [tuple(x) for x in m["fast"]]
    return m


# Wait for seek(t) (sync or async) and then two animation frames, so the capture is the
# composited frame and not a half-painted one.
SEEK_JS = ("t => Promise.resolve(window.seek(t)).then(() => new Promise("
           "r => requestAnimationFrame(() => requestAnimationFrame(r))))")

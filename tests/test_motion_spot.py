"""Pure-function checks for the /kai-motion-spot engine (no browser, no ffmpeg, no network)."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "scripts" / "motion_spot"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ENGINE / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _drop_track(sr: int, pre_hit: float, drop: float, dur: float = 20.0) -> np.ndarray:
    """A synthetic build: soft noise, one lone kick at pre_hit, silence, then sub bass + a kick every beat from drop."""
    n = int(dur * sr)
    t = np.arange(n) / sr
    x = np.zeros(n)
    rng = np.random.default_rng(0)
    x += 0.02 * rng.standard_normal(n) * (t < pre_hit)          # soft build noise

    def kick(at: float, gain: float = 1.0) -> None:
        k = np.arange(int(0.25 * sr)) / sr
        f = 50 + 90 * np.exp(-k * 30)
        clip = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-k * 12) * gain
        i = int(at * sr)
        x[i:i + len(clip)] += clip[: n - i]

    kick(pre_hit)
    x += 0.35 * np.sin(2 * np.pi * 55 * t) * (t >= drop)          # the drop's sustained sub bass
    beat = 0.5
    k = drop
    while k < dur - 0.5:
        kick(k)
        k += beat
    return x


def test_drop_snaps_past_a_pre_drop_hit():
    analyze = _load("ms_analyze", "analyze.py")
    sr = 22050
    x = _drop_track(sr, pre_hit=6.0, drop=6.8)
    r = analyze.analyze_signal(x, sr)
    assert abs(r["D"] - 6.8) < 0.03, r
    assert r["bpm"] == pytest.approx(120, abs=1.5), r


def test_cut_side_clamp_and_fast_subframes():
    render = _load("ms_render", "render.py")
    # a subframe that would cross the cut at 4.0 is clamped to the frame's side
    assert render.keep_side(4.0, 4.0 - 1 / 240, cuts=[4.0]) == 4.0
    assert render.keep_side(3.99, 3.99 + 1 / 60, cuts=[4.0]) < 4.0
    assert len(render.subs(1.0, fast=[], fps=60)) == 3
    ss = render.subs(4.2, fast=[(4.0, 4.6, 11)], fps=60)
    assert len(ss) == 11 and max(ss) - min(ss) < 1 / 60     # 180-degree shutter inside one frame


def test_sfx_peaks_land_on_the_grid():
    sfx = _load("ms_sfx", "sfx.py")
    _, report = sfx.render({"dur": 6, "bpm": 120, "cues": [
        {"at": 4.0, "sfx": "thump"}, {"at": 2.5, "sfx": "tick", "freq": 2000}, {"at": 1.0, "sfx": "chime"}]})
    assert all(abs(r["grid_offset_ms"]) < 15 for r in report), report


def test_walkthrough_marks_fast_camera_moves():
    wt = _load("ms_walk", "walkthrough/walkthrough.py")
    shots = [{"t0": 4, "rise": True, "cam": [[4, 100, 100, 1.0], [8, 110, 100, 1.02]]},
             {"t0": 8, "rise": False, "cam": [[8, 100, 100, 1.5], [9, 900, 500, 1.5]]}]
    fast = wt.fast_windows(shots, end_t0=20.0)
    assert (4, 5.1, 7) in fast           # the rise-in
    assert (8, 9, 7) in fast             # a big pan in one second
    assert (19.5, 20.0, 7) in fast       # the wipe into the end card


def test_engine_is_public_safe():
    """The engine ships in a public plugin: no personal paths, hosts, or hard-coded keys and page ids."""
    banned = [r"[A-Z]:\\\\", r"/home/", r"\bhermes\b", r"cmo-secrets", r"\.env\.local", r"kaicalls",
              r"xi-api-key\"\s*:\s*\"[A-Za-z0-9]", r"\b\d{12,}\b"]
    hits = []
    for f in ENGINE.rglob("*"):
        if f.suffix not in {".py", ".html", ".js", ".css", ".json"}:
            continue
        text = f.read_text(encoding="utf-8")
        hits += [f"{f.name}: {p}" for p in banned if re.search(p, text, re.IGNORECASE)]
    assert hits == []

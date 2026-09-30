"""Find the real drop in a generated track, its tempo, and how much clean drop there is.

  python analyze.py audio/eleven2_trap.mp3 audio/eleven2_stomp.mp3   -> audio/analysis.json
  python analyze.py --verify audio/master.wav 4.0                    -> is the drop on V4.0?
  BPM=120 (default) is the picture grid; a band reading that matches it wins.

What it reports per track: D (drop downbeat, seconds into the source), bpm, drop_len,
jump_db / crest / low_share (how hard it hits), and kick offsets from D.

Why D is found in three steps (each one fixed a real miss):
 1. coarse D: the time that maximizes low-band energy over the next 4 s against the previous 3 s.
 2. hit snap: generated "builds" often put a single pre-drop hit, then a beat of silence, then the
    real drop. Step 1 can land on that pre-hit (one build: 7.355 s found, real drop at 8.13 s, a
    0.75 s miss you hear on the reveal). So every low-band kick onset within -0.6..+1.6 s of the
    coarse D is scored by (energy of the next bar) / (energy of the second before it); the gap
    before the real drop makes that ratio jump. D snaps to the winner.
 3. tempo: onset autocorrelation misreads triplet hats as 80 BPM. A comb score over the hi band
    and low band is folded into 90-180 BPM and cross-checked with the kick spacing.
Always confirm on the built master: `--verify` checks the low band lands at the picture's drop time.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import signal

SR = 22050
HOP = 200  # envelope rate (Hz)


def load(path: str, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def _env(x: np.ndarray, sr: int) -> np.ndarray:
    """RMS envelope sampled at HOP Hz (50 ms window)."""
    w = sr // 20
    return np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same"))[:: sr // HOP]


def _band(x: np.ndarray, sr: int, lo: float | None = None, hi: float | None = None) -> np.ndarray:
    if lo and hi:
        b, a = signal.butter(4, [lo / (sr / 2), hi / (sr / 2)], "band")
    elif hi:
        b, a = signal.butter(4, hi / (sr / 2), "low")
    else:
        b, a = signal.butter(4, lo / (sr / 2), "high")
    return signal.lfilter(b, a, x)


def kick_onsets(lo: np.ndarray, sr: int) -> np.ndarray:
    """Times (s) of low-band onsets: peaks of the positive derivative of the smoothed envelope."""
    env = np.abs(signal.hilbert(lo))
    k = max(1, sr // 100)
    e = np.convolve(env, np.ones(k) / k, "same")
    on = np.maximum(np.diff(e, prepend=e[0]), 0)
    pk, _ = signal.find_peaks(on, height=on.max() * 0.25, distance=int(0.15 * sr))
    return pk / sr


def comb_bpm(env: np.ndarray, lo_bpm: float = 70, hi_bpm: float = 181) -> float:
    on = np.maximum(np.diff(env, prepend=env[0]), 0)
    on = on - on.mean()
    best, bpm_best = -np.inf, 120.0
    for bpm in np.arange(lo_bpm, hi_bpm, 0.5):
        p = 60 / bpm * HOP
        sc = 0.0
        for k in (1, 2, 4):
            lag = int(round(k * p))
            if lag < len(on):
                sc += float(on[lag:].dot(on[:-lag])) / (len(on) - lag)
        if sc > best:
            best, bpm_best = sc, bpm
    while bpm_best < 90:
        bpm_best *= 2
    while bpm_best >= 180:
        bpm_best /= 2
    return float(bpm_best)


def analyze_signal(x: np.ndarray, sr: int = SR, expect_bpm: float = 120.0) -> dict:
    n = len(x) / sr
    lo = _band(x, sr, hi=150)
    hi = _band(x, sr, lo=2000)
    e = _env(lo, sr)

    # 1. coarse D
    best, D = 0.0, 2.0
    for i in range(int(2 * HOP), int(max(2.1, n - 6) * HOP)):
        r = e[i:i + 4 * HOP].mean() / (e[max(0, i - 3 * HOP):i].mean() + 1e-6)
        if r > best:
            best, D = r, i / HOP
    coarse = D

    # 2. snap to the kick that starts the sustained drop. Candidates are low-band onsets near the
    #    coarse D. A lone pre-drop hit followed by a beat of silence is rejected (gap test); among
    #    the rest, the winner has the biggest jump from the half second before it to the bar after it.
    kicks = kick_onsets(lo, sr)
    level = np.percentile(e[int(coarse * HOP):int((coarse + 6) * HOP)], 75)
    cands = []
    for c in kicks[(kicks > coarse - 1.0) & (kicks < coarse + 2.1)]:
        i = int(c * HOP)
        if e[i + HOP // 10:i + int(0.8 * HOP)].min() < 0.15 * level:
            continue                                                   # hit, then silence: a pre-hit
        pre = e[max(0, i - HOP // 2):max(1, i - HOP // 20)].mean()
        cands.append((e[i:i + 2 * HOP].mean() / (pre + 1e-6), float(c)))
    if cands:
        D = max(cands)[1]
    # the RMS window smears the attack: back up to where the Hilbert envelope first crosses half its peak
    env = np.abs(signal.hilbert(lo[int(max(0, D - 0.15) * sr):int((D + 0.1) * sr)]))
    k = max(1, sr // 400)
    env = np.convolve(env, np.ones(k) / k, "same")
    D = max(0.0, D - 0.15) + int(np.argmax(env > 0.5 * env.max())) / sr

    # 3. tempo: comb on the hi and low bands; keep the one whose beat grid fits the kicks best
    a, b = int(D * HOP), int(min(n - 0.1, D + 12) * HOP)
    bpm_hi = comb_bpm(_env(hi, sr)[a:b])
    bpm_lo = comb_bpm(e[a:b])
    dk = kicks[(kicks >= D - 0.05) & (kicks < D + 12)] - D

    def grid_err(bpm: float) -> float:
        beat = 60 / bpm
        return float(np.mean(np.abs(dk / beat - np.round(dk / beat)))) if len(dk) else 0.0

    # The picture is cut on a fixed grid (120 BPM by default): prefer a band reading that matches it.
    grid = [c for c in (bpm_hi, bpm_lo) if abs(c - expect_bpm) <= 1.5]
    bpm = grid[0] if grid else min((bpm_hi, bpm_lo), key=grid_err)

    # drop length: until the low band stays under 35% of the drop level for > 1 s
    dl = e[int(D * HOP):]
    ref = np.median(dl[:3 * HOP]) if len(dl) else 0
    end, run = n, 0
    for k, v in enumerate(dl):
        run = run + 1 if v < 0.35 * ref else 0
        if run > HOP:
            end = D + (k - HOP) / HOP
            break
    seg = x[int(D * sr):int(min(end, D + 12) * sr)]
    pre = x[int(max(0, D - 4) * sr):int(D * sr)]
    rms = np.sqrt((seg ** 2).mean()) if len(seg) else 1e-9
    lo_seg = lo[int(D * sr):int(min(end, D + 12) * sr)]
    return dict(
        len=round(n, 2), D=round(D, 3), coarse_D=round(coarse, 3), bpm=round(bpm, 1),
        bpm_hi_band=bpm_hi, bpm_low_band=bpm_lo, tempo_ambiguous=abs(bpm_hi - bpm_lo) > 1.5,
        drop_end=round(end, 2), drop_len=round(end - D, 2),
        drop_rms_db=round(20 * np.log10(rms + 1e-12), 1),
        crest=round(float(np.abs(seg).max() / rms), 2) if len(seg) else 0,
        low_share=round(float(np.sqrt((lo_seg ** 2).mean()) / rms), 2) if len(seg) else 0,
        jump_db=round(20 * np.log10(rms / (np.sqrt((pre ** 2).mean()) + 1e-9)), 1) if len(pre) else 0,
        kicks_from_D=[round(float(t - D), 2) for t in kicks[(kicks > D - 2) & (kicks < D + 8)]],
    )


def verify(path: str, at: float) -> dict:
    """Where does the low band actually arrive in the built master, relative to the picture's drop?"""
    x = load(path)
    lo = _band(x, SR, hi=150)
    e = _env(lo, SR)
    level = np.percentile(e[int(at * HOP):int((at + 2) * HOP)], 90)
    w = e[int((at - 0.5) * HOP):int((at + 1.0) * HOP)]
    first = (at - 0.5) + int(np.argmax(w > 0.5 * level)) / HOP
    env = np.abs(signal.hilbert(lo[int(max(0, first - 0.15) * SR):int((first + 0.1) * SR)]))
    env = np.convolve(env, np.ones(SR // 400) / (SR // 400), "same")
    first = max(0.0, first - 0.15) + int(np.argmax(env > 0.5 * env.max())) / SR
    steps = [round(float(v / (level + 1e-9)), 2) for v in e[int((at - 0.25) * HOP):int((at + 0.5) * HOP):10]]
    return dict(expected=at, low_band_arrives=round(first, 3), offset_ms=round((first - at) * 1000),
                ok=abs(first - at) <= 0.03, level_50ms_steps_from_minus_250ms=steps)


def main() -> None:
    if sys.argv[1:2] == ["--verify"]:
        r = verify(sys.argv[2], float(sys.argv[3]))
        print(json.dumps(r))
        if not r["ok"]:
            sys.exit("drop is off the picture's downbeat: snap D to the kick grid (kicks_from_D) and rebuild")
        return
    out = Path("audio") / "analysis.json"
    res = json.loads(out.read_text()) if out.exists() else {}
    for f in sys.argv[1:]:
        res[f] = analyze_signal(load(f), expect_bpm=float(os.environ.get("BPM", 120)))
        print(f, json.dumps(res[f]))
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

"""Synthesized SFX stem, peak-aligned to picture events (no third-party audio, no licensing risk).

  python sfx.py cues.json            -> audio/sfx.wav  (+ prints each cue's peak offset from the beat grid)
  python sfx.py --list               -> available sounds

cues.json: {"dur": 24, "bpm": 120, "cues": [{"at": 4.0, "sfx": "thump", "gain": 0.9},
                                            {"at": 3.0, "sfx": "riser", "len": 1.0, "align": "start"}, ...]}
"align": "peak" (default) puts the loudest sample on `at`; "start" starts the clip at `at` (risers, rings).
You cannot hear the render in an agent loop: check the printed offsets (<15 ms from the grid for on-beat hits)
and a spectrogram instead. build_score.py mixes this stem under the music at 0.2.
"""
from __future__ import annotations

import inspect
import json
import os
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)


def t_(n): return np.arange(n) / SR
def midi(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, fc): b, a = signal.butter(2, min(fc, SR / 2 - 100) / (SR / 2), "low"); return signal.lfilter(b, a, x)
def hp(x, fc): b, a = signal.butter(2, fc / (SR / 2), "high"); return signal.lfilter(b, a, x)
def bp(x, lo, hi): b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band"); return signal.lfilter(b, a, x)


def tick(f=2200, d=0.03):
    t = t_(int(SR * d)); return np.sin(2 * np.pi * f * t) * np.exp(-t * 180) * 0.5


def click():
    n = int(SR * 0.05); t = t_(n); k = int(0.018 * SR)
    x = bp(rng.standard_normal(n), 1500, 7000) * np.exp(-t * 260)
    x[k:] += bp(rng.standard_normal(n - k), 1200, 5000) * np.exp(-t[:n - k] * 300) * 0.6
    return x * 0.7


def whoosh(d=0.6, up=True, lo=300, hi=6000):
    n = int(SR * d); t = t_(n); noise = rng.standard_normal(n); out = np.zeros(n); blk = 512
    for i in range(0, n, blk):
        p = i / n if up else 1 - i / n
        fc = lo * (hi / lo) ** p
        out[i:i + blk] = bp(noise[max(0, i - 2048):i + blk], fc * 0.6, min(fc * 1.6, SR / 2 - 200))[-len(out[i:i + blk]):]
    return out * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * 0.5


def riser(d=1.0):
    t = t_(int(SR * d)); f = 200 * 2 ** (t / d * 3)
    tone = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * 0.15
    return (whoosh(d, True, 400, 12000) * 0.9 + lp(tone, 4000)) * (t / d) ** 2


def thump():
    t = t_(int(SR * 0.5)); f = 40 + 70 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.8


def bell(m=84, d=1.6):
    t = t_(int(SR * d)); f = midi(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k)
               for a, r, k in [(1, 1, 3), (.5, 2.01, 5), (.3, 3.0, 7), (.2, 4.2, 9)]) * 0.25


def chime():
    t = t_(int(1.2 * SR))
    return sum(np.sin(2 * np.pi * f * t) * g for f, g in ((880, .5), (1320, .3), (1760, .15))) \
        * np.exp(-t * 4) * np.minimum(1, t / 0.004)


def ding():
    x = bell(88, 1.4) * 0.8; y = bell(95, 1.2) * 0.35; x[:len(y)] += y; return x


def beep(f=1000, d=0.42):
    t = t_(int(SR * d)); return np.sin(2 * np.pi * f * t) * np.minimum(t / 0.004, 1) * np.minimum((d - t) / 0.02, 1) * 0.28


def ring(d=1.2):
    """Electronic office-phone trill in bursts."""
    t = t_(int(SR * d)); f = np.where(np.floor(t * 32) % 2 == 0, 1350, 1700)
    gate = np.convolve(((t % 0.6) < 0.4).astype(float), np.ones(200) / 200, "same")
    return lp(np.sin(2 * np.pi * np.cumsum(f) / SR), 5000) * gate * 0.18


def swell(d=1.0):
    t = t_(int(SR * d)); return hp(rng.standard_normal(len(t)), 3000) * (t / d) ** 3 * 0.35


def marimba(m=76, d=0.35):
    t = t_(int(SR * d)); f = midi(m)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 40)) * np.exp(-t * 9) * 0.5


def flip(): return whoosh(0.35, True, 800, 7000) * 0.6


SOUNDS = {"tick": tick, "click": click, "whoosh": whoosh, "riser": riser, "thump": thump, "bell": bell, "chime": chime,
          "ding": ding, "beep": beep, "ring": ring, "swell": swell, "marimba": marimba, "flip": flip}


def make(cue: dict) -> np.ndarray:
    fn = SOUNDS[cue["sfx"]]
    kw = {}
    if "len" in cue:
        kw["d"] = cue["len"]
    if "note" in cue:
        kw["m"] = cue["note"]
    if "freq" in cue:
        kw["f"] = cue["freq"]
    accepted = inspect.signature(fn).parameters
    return fn(**{k: v for k, v in kw.items() if k in accepted})


def render(spec: dict) -> tuple[np.ndarray, list[dict]]:
    dur, bpm = float(spec.get("dur", 24)), float(spec.get("bpm", 120))
    N = int((dur + 1.5) * SR)
    L, R = np.zeros(N), np.zeros(N)
    report = []
    for cue in spec["cues"]:
        x = make(cue) * float(cue.get("gain", 0.8))
        peak = int(np.argmax(np.abs(signal.hilbert(x))))
        off = peak if cue.get("align", "peak") == "peak" else 0
        i = int(round(cue["at"] * SR)) - off
        j0, j1 = max(i, 0), min(i + len(x), N)
        if j1 <= j0:
            continue
        pan = float(cue.get("pan", 0.0))
        seg = x[j0 - i:j1 - i]
        L[j0:j1] += seg * np.cos((pan + 1) * np.pi / 4) * 2 ** 0.5
        R[j0:j1] += seg * np.sin((pan + 1) * np.pi / 4) * 2 ** 0.5
        peak_t = (i + peak) / SR
        half = 30 / bpm   # 8th-note grid
        report.append({"sfx": cue["sfx"], "at": cue["at"], "peak_at": round(peak_t, 4),
                       "grid_offset_ms": round((peak_t - round(peak_t / half) * half) * 1000, 1)})
    st = np.stack([L, R], 1)
    return st / (np.abs(st).max() + 1e-9), report


def main() -> None:
    if sys.argv[1:2] == ["--list"]:
        print(" ".join(SOUNDS))
        return
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    st, report = render(spec)
    os.makedirs("audio", exist_ok=True)
    wavfile.write(os.path.join("audio", "sfx.wav"), SR, st.astype(np.float32))
    for r in report:
        flag = "" if abs(r["grid_offset_ms"]) < 15 else "   <- off the 8th-note grid (fine only if deliberate)"
        print(f"{r['sfx']:8s} at {r['at']:6.3f}  peak {r['peak_at']:7.4f}  grid {r['grid_offset_ms']:+6.1f} ms{flag}")
    print("wrote audio/sfx.wav")


if __name__ == "__main__":
    main()

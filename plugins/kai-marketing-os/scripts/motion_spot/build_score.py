"""Bar-accurate edit of a generated track onto the picture's beat grid, plus the SFX stem, at -14 LUFS.

Layout on the picture timeline (V = video seconds), all on whole bars:
  V0 .. build          the track's build, ending exactly on its drop D
  build .. drop_end    the drop (auto-stops before any dead stop inside it and loops the last 2 bars)
  drop_end .. +riser   the riser again (tension under the category line); --riser 0 skips it
  then                 the drop's first hit re-used as the logo impact, decaying out to --dur

  python build_score.py audio/eleven2_trap.mp3 8.17 audio/master.wav                    # 24 s launch spot
  python build_score.py audio/eleven2_trap.mp3 8.17 audio/master.wav --dur 19 --drop-end 16 --riser 0   # 19 s pain video
  python build_score.py audio/eleven2_festival.mp3 2.0 audio/bed.wav --dur 39 --drop-end 36 --riser 0   # walkthrough bed
Options: --bpm 120  --build 4.0 (seconds of build before the drop)  --max-drop S (cap how much of the
drop is used; a track that dips 6 dB mid-drop gets capped before the dip)  --sfx audio/sfx.wav (default if
present)  --nosfx  --sfx-gain 0.2  --lufs -14.
Then confirm the drop landed: python analyze.py --verify audio/master.wav <build>
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

import numpy as np
from scipy.io import wavfile

SR = 48000
XF = int(0.008 * SR)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("D", type=float, help="drop downbeat in the source (analyze.py)")
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=120.0)
    ap.add_argument("--dur", type=float, default=24.0)
    ap.add_argument("--build", type=float, default=4.0)
    ap.add_argument("--drop-end", type=float, default=None, help="V time the drop ends (default dur-4 or dur-3)")
    ap.add_argument("--riser", type=float, default=2.0, help="seconds of riser reprise before the impact (0 = none)")
    ap.add_argument("--max-drop", type=float, default=None)
    ap.add_argument("--sfx", default="audio/sfx.wav")
    ap.add_argument("--nosfx", action="store_true")
    ap.add_argument("--sfx-gain", type=float, default=0.2)
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()

    bar = 4 * 60 / a.bpm
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", a.src, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    tail = 3.3
    drop_end = a.drop_end if a.drop_end is not None else a.dur - a.riser - (tail - 1.3 if a.riser else 3.0)
    N = int((a.dur + 0.5) * SR)
    out = np.zeros((N, 2))

    def seg(v0, t0, dur, fin=XF, fout=XF, env=None):
        n = int(dur * SR)
        s = int(round(t0 * SR))
        c = x[max(s, 0):s + n].copy()
        if s < 0:
            c = np.vstack([np.zeros((-s, 2)), c])
        if len(c) < n:
            c = np.vstack([c, np.zeros((n - len(c), 2))])
        w = np.ones(n)
        if fin:
            w[:fin] = np.linspace(0, 1, fin)
        if fout:
            w[-fout:] = np.minimum(w[-fout:], np.linspace(1, 0, fout))
        if env is not None:
            w *= env(np.arange(n) / SR)
        i = int(round(v0 * SR)) - (fin // 2 if v0 > 0 else 0)
        j = min(N, i + n)
        out[i:j] += (c * w[:, None])[:j - i]

    seg(0.0, a.D - a.build, a.build + 0.004, fin=int(0.02 * SR))
    # usable drop: whole bars before any dead stop (RMS under 18% of the drop's median) or --max-drop
    mono = x.mean(1)
    w = SR // 10
    rms = np.array([np.sqrt((mono[i:i + w] ** 2).mean()) for i in range(int(a.D * SR), len(mono) - w, w)])
    drop_len = len(x) / SR - a.D
    ref = np.median(rms[:60]) if len(rms) else 0
    gap = next((k / 10 for k in range(20, len(rms)) if rms[k] < 0.18 * ref), drop_len)
    want = drop_end - a.build
    usable = min(drop_len, gap, a.max_drop or 1e9) - 0.1
    body = min(want, float(np.floor(usable / bar) * bar))
    print(f"drop stop at +{gap:.2f}s; using {body / bar:.0f} bars of drop")
    seg(a.build, a.D, body + 0.004)
    v = a.build + body
    loop = 2 * bar
    while v < drop_end - 1e-6:                          # loop the last 2 bars if the drop is short
        seg(v, a.D + body - loop + ((v - a.build - body) % loop), bar + 0.004)
        v += bar
    if a.riser > 0:
        seg(drop_end, a.D - a.riser, a.riser + 0.004)   # riser again -> re-drop tension
    impact = drop_end + a.riser
    seg(impact, a.D, max(0.5, a.dur - impact + 0.3), fout=int(0.6 * SR), env=lambda t: np.exp(-t * 1.25))

    out /= np.abs(out).max() + 1e-12
    mix = out * 0.92
    if not a.nosfx and os.path.exists(a.sfx):
        _, sfx = wavfile.read(a.sfx)
        sfx = sfx.astype(np.float64)
        if sfx.ndim == 1:
            sfx = np.stack([sfx, sfx], 1)
        sfx = sfx[:N]
        if len(sfx) < N:
            sfx = np.vstack([sfx, np.zeros((N - len(sfx), 2))])
        mix = mix + sfx * a.sfx_gain
        print("sfx stem mixed at", a.sfx_gain)
    fade = np.ones(N)
    f0, f1 = int((a.dur - 1.1) * SR), int((a.dur - 0.05) * SR)
    fade[f0:f1] = np.linspace(1, 0, f1 - f0) ** 2
    fade[f1:] = 0
    mix = (mix * fade[:, None])[:int(a.dur * SR)]
    tmp = a.out.replace(".wav", "_raw.wav")
    wavfile.write(tmp, SR, (mix / (np.abs(mix).max() + 1e-12) * 0.95 * 32767).astype(np.int16))
    ln = f"loudnorm=I={a.lufs}:TP=-1:LRA=11"
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", ln + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"{ln}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
          f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ar", "48000", a.out], check=True)
    print(a.out, f"{a.dur}s", "input LUFS", j["input_i"], f"-> verify: python analyze.py --verify {a.out} {a.build}")


if __name__ == "__main__":
    main()

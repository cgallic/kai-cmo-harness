"""Render a seek(t) page to a 60 fps master with real motion blur.

N parallel Chromium workers capture every frame as the average of subframes: 3 subframes
(t-1/240, t, t+1/240) normally, 7-15 subframes over a 180-degree shutter inside the FAST
windows (whips, zooms, reveals). Subframes never straddle a hard cut (CUTS); if they do,
a ghost of the previous scene shows on the first frame after the cut.

Render fixes found on real builds (keep them):
  * warm-up pass: seek through the whole timeline once before capturing. Otherwise a worker
    that starts mid-range captures layers Chromium has not rasterized yet (washed-out text).
  * paint wait: after seek(t), wait two requestAnimationFrames before capturing.
  * frames are cached by filename: after editing one scene, delete only that frame range.

  PAGE=index.html python render.py                  # 16:9, timing from index.meta.json
  PAGE=index.html VW=1080 VH=1920 FRAMES=frames_v OUTNAME=Spot_9x16.mp4 python render.py
  DUR=2 MASTER=none python render.py                # smoke test: 2 s, silent
Env: see _project.py, plus FRAMES (frame dir, default frames/), OUTNAME, WORKERS (default 4),
MASTER (file in audio/ to mux, default master.wav; "none" = silent master).
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import SEEK_JS, meta, page_url, project, viewport  # noqa: E402

M = meta()
FPS, DUR = int(M["fps"]), float(M["dur"])
SUB = [-1 / (4 * FPS), 0.0, 1 / (4 * FPS)]
NF = int(round(FPS * DUR))
FAST = M["fast"]   # [(t0, t1, n_subframes), ...]
CUTS = M["cuts"]   # every hard-cut time
WORKERS = int(os.environ.get("WORKERS", 4))
FR = project() / os.environ.get("FRAMES", "frames")


def keep_side(t: float, s: float, cuts=None) -> float:
    """Clamp subframe time s to the same side of every hard cut as frame time t."""
    for c in CUTS if cuts is None else cuts:
        if s < c <= t:
            s = c
        elif t < c <= s:
            s = c - 1e-4
    return s


def subs(t: float, fast=None, fps: int | None = None) -> list[float]:
    fps = fps or FPS
    for a, b, n in FAST if fast is None else fast:
        if a <= t <= b:
            return [(-0.5 + (i + 0.5) / n) / fps for i in range(int(n))]   # 180-degree shutter
    return [-1 / (4 * fps), 0.0, 1 / (4 * fps)]


async def work(k: int) -> None:
    import base64
    import io

    import numpy as np
    from PIL import Image
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport=viewport())
        pg.on("pageerror", lambda e: print(f"[worker {k}] pageerror:", e))
        await pg.goto(page_url())
        await pg.evaluate("window.ready")
        cdp = await pg.context.new_cdp_session(pg)
        shot = {"format": "png", "optimizeForSpeed": True}
        step = 0.25 if DUR <= 30 else 0.5
        for wt in [x * step for x in range(int(DUR / step))] + [0.0]:     # warm-up pass
            await pg.evaluate(SEEK_JS, wt)
            await cdp.send("Page.captureScreenshot", shot)
        for i in range(k, NF, WORKERS):
            out = FR / f"{i:05d}.png"
            if out.exists():
                continue
            acc = None
            ss = subs(i / FPS)
            for d in ss:
                t = max(0.0, min(DUR - 1e-4, keep_side(i / FPS, i / FPS + d)))
                await pg.evaluate(SEEK_JS, t)
                r = await cdp.send("Page.captureScreenshot", shot)
                a = np.asarray(Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB"), np.float32)
                acc = a if acc is None else acc + a
            Image.fromarray(np.clip(acc / len(ss) + 0.5, 0, 255).astype(np.uint8)).save(out, compress_level=1)
        await b.close()


def run(k: int) -> None:
    asyncio.run(work(k))


def main() -> None:
    FR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ps = [Process(target=run, args=(k,)) for k in range(WORKERS)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    secs = time.time() - t0
    have = len([f for f in FR.glob("*.png") if f.stem.isdigit() and int(f.stem) < NF])
    print(f"frames done in {secs:.0f}s {have}/{NF} ({WORKERS} workers)")
    if have < NF:
        sys.exit("missing frames: a worker failed; see the pageerror lines above")

    out = project() / "out"
    out.mkdir(exist_ok=True)
    master = out / os.environ.get("OUTNAME", "Spot_16x9.mp4")
    audio = os.environ.get("MASTER", "master.wav")
    wav = project() / "audio" / audio
    a_in = [] if audio == "none" or not wav.exists() else ["-i", str(wav)]
    a_map = ["-map", "1:a", "-c:a", "aac", "-b:a", "256k"] if a_in else ["-an"]
    if not a_in and audio != "none":
        print(f"no audio/{audio}; writing a silent master")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(FR / "%05d.png"), *a_in,
        "-vf", "format=yuv420p", "-map", "0:v", *a_map, "-r", str(FPS), "-c:v", "libx264", "-preset", "slow",
        "-crf", "16", "-profile:v", "high", "-movflags", "+faststart", "-t", str(DUR), str(master)], check=True)
    with open(out / "render-log.txt", "a", encoding="utf-8") as f:   # feeds the cost basis
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{master.name}\t{NF} frames\t{secs:.0f}s\t{WORKERS} workers\n")
    print("wrote", master)


if __name__ == "__main__":
    main()

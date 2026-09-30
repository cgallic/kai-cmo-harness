"""Web deliverables from a rendered master: poster, H.264 faststart + VP9 WebM at 1280 px sized
into a target band, muted site cuts, a 9:16 social encode, and an embed snippet.

  python web_encode.py out/Spot_16x9.mp4 --slug launch --poster-t 21.8 --mode click
  python web_encode.py out/pain-1-16x9.mp4 --slug pain-1 --poster-t 3.6 --mode autoplay --vertical out/pain-1-9x16.mp4

Writes to out/web/ (or --out):
  <slug>.mp4 / <slug>.webm            with the score, for a click-to-play player
  <slug>-muted.mp4 / <slug>-muted.webm  no audio track (--mode autoplay, or --muted): smaller, autoplays everywhere
  <slug>-poster.jpg                   the settled poster frame, also baked into frame 0 of every encode
  <slug>-vertical.mp4                 when --vertical is given (720x1280 H.264 faststart)
  <slug>-embed.html                   the snippet for the chosen mode

Sizing: long edge 1280 px, 30 fps, CRF searched until each file lands in --min-mb..--max-mb (default 1.5..3 MB).
A file that cannot reach the floor at CRF 18 is simply small; that is fine.
"""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

BAKE = "[1:v]scale={w}:{h}[p];[0:v]scale={w}:{h}:flags=lanczos,fps={fps}[v0];[v0][p]overlay=enable='eq(n,0)',format=yuv420p[v]"


def run(*a: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def dims(src: str, long_edge: int) -> tuple[int, int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", src], capture_output=True, text=True, check=True).stdout.strip()
    w, h = (int(v) for v in out.split(",")[:2])
    k = long_edge / max(w, h)
    return int(round(w * k / 2) * 2), int(round(h * k / 2) * 2)


def has_audio(src: str) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip()
    return bool(out)


def encode(kind: str, src: str, jpg: str, dst: str, crf: int, w: int, h: int, fps: int, audio: bool) -> None:
    fc = BAKE.format(w=w, h=h, fps=fps)
    if kind == "h264":
        a = ["-map", "0:a", "-c:a", "aac", "-b:a", "128k"] if audio else ["-an"]
        run("-i", src, "-i", jpg, "-filter_complex", fc, "-map", "[v]", *a, "-c:v", "libx264", "-preset", "slow",
            "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst)
    else:
        a = ["-map", "0:a", "-c:a", "libopus", "-b:a", "96k"] if audio else ["-an"]
        run("-i", src, "-i", jpg, "-filter_complex", fc, "-map", "[v]", *a, "-c:v", "libvpx-vp9", "-b:v", "0",
            "-crf", str(crf), "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-pix_fmt", "yuv420p", dst)


def fit(kind: str, src: str, jpg: str, dst: str, lo_mb: float, hi_mb: float, **kw) -> int:
    """Search CRF so the file lands in [lo_mb, hi_mb]. H.264 range 18-34, VP9 range 24-48."""
    crf, lo_crf, hi_crf, step = (23, 18, 34, 2) if kind == "h264" else (34, 24, 48, 3)
    seen = set()
    while True:
        encode(kind, src, jpg, dst, crf, **kw)
        mb = os.path.getsize(dst) / 1e6
        seen.add(crf)
        if mb > hi_mb and crf + step <= hi_crf and crf + step not in seen:
            crf += step
        elif mb < lo_mb and crf - step >= lo_crf and crf - step not in seen:
            crf -= step
        else:
            return crf


SNIPPET_AUTOPLAY = """<!-- muted autoplay loop: the burned-in text carries the story, so no sound is needed -->
<figure class="motion-video">
  <video autoplay muted loop playsinline preload="none" poster="{base}/{slug}-poster.jpg"
         width="{w}" height="{h}" aria-label="{alt}">
    <source src="{base}/{slug}-muted.webm" type="video/webm">
    <source src="{base}/{slug}-muted.mp4" type="video/mp4">
  </video>
  <figcaption>{caption}</figcaption>
</figure>
<script>
  // respect reduced motion: show the poster instead of the loop
  if (matchMedia('(prefers-reduced-motion: reduce)').matches)
    document.querySelectorAll('.motion-video video').forEach(v => {{ v.removeAttribute('autoplay'); v.pause(); }});
</script>
"""

SNIPPET_CLICK = """<!-- click-to-play: longer pieces with music. Poster + controls, nothing loads until play -->
<figure class="motion-video">
  <video controls preload="none" playsinline poster="{base}/{slug}-poster.jpg"
         width="{w}" height="{h}" aria-label="{alt}">
    <source src="{base}/{slug}.webm" type="video/webm">
    <source src="{base}/{slug}.mp4" type="video/mp4">
  </video>
  <figcaption>{caption}</figcaption>
</figure>
"""

CSS = """<style>
  .motion-video{{margin:0}}
  .motion-video video{{display:block;width:100%;height:auto;aspect-ratio:{w}/{h};border-radius:16px;background:#0B0E14}}
  .motion-video figcaption{{margin-top:10px;font-size:15px;line-height:1.45}}
</style>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("master")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--poster-t", type=float, required=True, help="a settled moment: text fully in")
    ap.add_argument("--mode", choices=["autoplay", "click"], default="click")
    ap.add_argument("--muted", action="store_true", help="also write muted cuts in click mode")
    ap.add_argument("--vertical", help="the 9:16 master, encoded for social / mobile hero")
    ap.add_argument("--out", default="out/web")
    ap.add_argument("--width", type=int, default=1280, help="long edge in px")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--min-mb", type=float, default=1.5)
    ap.add_argument("--max-mb", type=float, default=3.0)
    ap.add_argument("--base", default="/media/video", help="URL folder used in the snippet")
    ap.add_argument("--alt", default="Describe what happens in the video, for screen readers.")
    ap.add_argument("--caption", default="One line that says what the viewer just saw.")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jpg = str(out / f"{a.slug}-poster.jpg")
    w, h = dims(a.master, a.width)
    run("-ss", str(a.poster_t), "-i", a.master, "-frames:v", "1", "-vf", f"scale={w}:{h}:flags=lanczos", "-q:v", "2", jpg)
    kw = dict(w=w, h=h, fps=a.fps)
    audio = has_audio(a.master)
    report = []
    if a.mode == "click" or not a.muted:
        for kind, ext in (("h264", "mp4"), ("vp9", "webm")):
            dst = str(out / f"{a.slug}.{ext}")
            crf = fit(kind, a.master, jpg, dst, a.min_mb, a.max_mb, audio=audio, **kw)
            report.append((dst, crf))
    if a.mode == "autoplay" or a.muted:
        for kind, ext in (("h264", "mp4"), ("vp9", "webm")):
            dst = str(out / f"{a.slug}-muted.{ext}")
            crf = fit(kind, a.master, jpg, dst, a.min_mb, a.max_mb, audio=False, **kw)
            report.append((dst, crf))
    if a.vertical:
        vw, vh = dims(a.vertical, a.width)
        vjpg = str(out / f"{a.slug}-vertical-poster.jpg")
        run("-ss", str(a.poster_t), "-i", a.vertical, "-frames:v", "1", "-vf", f"scale={vw}:{vh}:flags=lanczos", "-q:v", "2", vjpg)
        dst = str(out / f"{a.slug}-vertical.mp4")
        crf = fit("h264", a.vertical, vjpg, dst, a.min_mb, a.max_mb, w=vw, h=vh, fps=a.fps, audio=has_audio(a.vertical))
        report.append((dst, crf))
    snippet = (SNIPPET_AUTOPLAY if a.mode == "autoplay" else SNIPPET_CLICK).format(
        base=a.base.rstrip("/"), slug=a.slug, w=w, h=h, alt=a.alt, caption=a.caption) + CSS.format(w=w, h=h)
    (out / f"{a.slug}-embed.html").write_text(snippet, encoding="utf-8")
    for dst, crf in report:
        print(f"{dst}  {os.path.getsize(dst) / 1e6:.2f} MB  crf {crf}")
    print(f"{jpg}\n{out / (a.slug + '-embed.html')}  ({a.mode})")


if __name__ == "__main__":
    main()

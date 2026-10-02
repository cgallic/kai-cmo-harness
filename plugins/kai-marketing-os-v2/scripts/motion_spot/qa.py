"""Watch-back QA sheets for a rendered video (see harness/references/motion-spot-method.md, QA section).

  python qa.py out/Spot_16x9.mp4                       # cuts read from the page's meta file (PAGE / META)
  python qa.py out/Spot_16x9.mp4 --cuts 4 8 12 --frames frames

Writes qa/<name>/:
  all.jpg          the whole spot at 4 fps, phone-width tiles (review EVERYTHING, not the scene you changed)
  cut_<t>.jpg      60 fps tiles for +-0.25 s around every cut (ghosts, black frames, pops)
  priv_NN.jpg      1 fps at phone reading size, for the privacy pass (read every name, email, number)
and prints ffprobe (size, fps, frames, duration), integrated loudness (target -14 LUFS), and, with --frames,
single-frame spikes (a frame that differs from both neighbours far more than they differ from each other).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import meta  # noqa: E402


def spikes(frames: Path) -> list[int]:
    import numpy as np
    from PIL import Image
    files = sorted(f for f in frames.glob("*.png") if f.stem.isdigit())
    v = []
    for f in files:
        im = Image.open(f).convert("L")
        v.append(np.asarray(im.resize((max(1, im.width // 10), max(1, im.height // 10)), Image.BILINEAR), np.float32))
    out = []
    for i in range(1, len(v) - 1):
        dp = np.abs(v[i] - v[i - 1]).mean()
        dn = np.abs(v[i] - v[i + 1]).mean()
        dd = np.abs(v[i - 1] - v[i + 1]).mean()
        if min(dp, dn) > 3 * dd + 2:
            out.append(int(files[i].stem))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--cuts", type=float, nargs="*")
    ap.add_argument("--frames", help="frame dir to scan for single-frame spikes")
    a = ap.parse_args()

    name = Path(a.video).stem
    q = Path("qa") / name
    q.mkdir(parents=True, exist_ok=True)
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                         "stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration",
                         "-of", "json", a.video], capture_output=True, text=True, check=True).stdout
    j = json.loads(pr)
    v = [s for s in j["streams"] if s["codec_type"] == "video"][0]
    has_a = any(s["codec_type"] == "audio" for s in j["streams"])
    loud = "no audio"
    if has_a:
        lo = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "ebur128", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        loud = [ln for ln in lo.splitlines() if ln.strip().startswith("I:")][-1].strip()
    dur = float(j["format"]["duration"])
    print(name, f"{v['width']}x{v['height']}", v["r_frame_rate"], "frames", v.get("nb_frames"), f"dur {dur:.3f}", "loud", loud)

    portrait = int(v["height"]) > int(v["width"])
    tw = 150 if portrait else 240
    rows = int(dur * 4 / 8) + 1
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps=4,scale={tw}:-1,tile=8x{rows}",
                    "-frames:v", "1", str(q / "all.jpg")], check=True)
    pw = 540 if portrait else 900   # what a phone shows
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", f"fps=1,scale={pw}:-1,tile=3x3",
                    str(q / "priv_%02d.jpg")], check=True)
    cuts = a.cuts if a.cuts is not None else meta()["cuts"]
    for c in cuts:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0, c - 0.25)), "-i", a.video, "-t", "0.5",
                        "-vf", f"fps=60,scale={tw}:-1,tile=6x5", "-frames:v", "1", str(q / f"cut_{c:05.2f}.jpg")], check=True)
    if a.frames:
        print("single-frame spikes:", spikes(Path(a.frames)) or "none")
    print("sheets in", q)


if __name__ == "__main__":
    main()

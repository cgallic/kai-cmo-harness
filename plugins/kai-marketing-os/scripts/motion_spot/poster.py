"""Bake a poster frame into frame 0 so every platform's auto-thumbnail is a settled, postable frame.
Replaces frame 0 (no frame is added), so duration and audio sync are unchanged. Also writes <name>.jpg.
  python poster.py out/Spot_16x9.mp4 21.8      # t = a settled moment (text fully in, not mid-transition)
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    src, t = sys.argv[1], float(sys.argv[2])
    base = os.path.splitext(src)[0]
    jpg, tmp = base + ".jpg", base + "_poster_tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-q:v", "2", jpg], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", jpg, "-filter_complex",
                    "[1:v]scale=iw:ih[p];[0:v][p]overlay=enable='eq(n,0)',format=yuv420p[v]",
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                    "-profile:v", "high", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, src)
    print("poster baked into frame 0 of", src, "->", jpg)

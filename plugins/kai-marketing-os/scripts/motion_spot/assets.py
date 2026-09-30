"""Asset prep for motion pages. Every sub-command writes into the project's assets/ folder.

  python assets.py clip SRC.mp4 NAME --start 8.0 --dur 3.2 --crop X,Y,W,H [--size 1280x800] [--fps 30]
      a TIGHT, readable UI moment as a JPEG frame sequence (Lanczos). Never a whole page.
  python assets.py still SRC.jpg NAME --size 960x568 [--center-y 0.32]
      fit a stock photo to a cell, biased upward to keep faces.
  python assets.py key SRC.png NAME [--tol 18]
      cut a product photo off a white background (border flood fill + unpremultiply).
  python assets.py blur boxes.json
      privacy pass on real screenshots, then 2x Lanczos + UnsharpMask for crisp zooms.
      boxes.json: {"src_dir": "cap", "images": {"inbox.png": [[x0, y0, x1, y1], ...], ...}}
      Boxes are in native screenshot pixels. Blur = downscale 9x first (destroys glyphs), then Gaussian:
      a plain Gaussian on text can stay readable after sharpening, so never skip the downscale.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

A = Path("assets")


def clip(a) -> None:
    x, y, w, h = a.crop.split(",")
    sw, sh = a.size.split("x")
    out = A / "clips" / a.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.start), "-i", a.src, "-t", str(a.dur),
                    "-vf", f"crop={w}:{h}:{x}:{y},scale={sw}:{sh}:flags=lanczos,fps={a.fps}",
                    "-q:v", "2", str(out / "%03d.jpg")], check=True)
    print(a.name, len(list(out.glob("*.jpg"))), "frames")


def still(a) -> None:
    from PIL import Image, ImageOps
    w, h = (int(v) for v in a.size.split("x"))
    im = ImageOps.fit(Image.open(a.src).convert("RGB"), (w, h), Image.LANCZOS, centering=(0.5, a.center_y))
    (A / "stock").mkdir(parents=True, exist_ok=True)
    im.save(A / "stock" / f"{a.name}.jpg", quality=92)
    print("wrote", A / "stock" / f"{a.name}.jpg")


def key(a) -> None:
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    im = np.asarray(Image.open(a.src).convert("RGB")).astype(np.float32)
    near_white = (255 - im).max(2) <= a.tol
    lab, _ = ndimage.label(near_white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    # soft edge: distance-based alpha over a 2 px band, then unpremultiply against white
    dist = ndimage.distance_transform_edt(~bg)
    alpha = np.clip(dist / 2.0, 0, 1)
    rgb = np.where(alpha[..., None] > 0, (im - 255 * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0)
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    A.mkdir(exist_ok=True)
    Image.fromarray(out, "RGBA").save(A / f"{a.name}.png")
    print("wrote", A / f"{a.name}.png")


def blur_box(im, b):
    from PIL import Image, ImageFilter
    b = tuple(int(round(v)) for v in b)
    reg = im.crop(b)
    w, h = reg.size
    small = reg.resize((max(1, w // 9), max(1, h // 9)), Image.BILINEAR)   # destroy glyph detail first
    im.paste(small.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)), b[:2])


def blur(a) -> None:
    from PIL import Image, ImageFilter
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    src = Path(spec.get("src_dir", "cap"))
    A.mkdir(exist_ok=True)
    for name, boxes in spec["images"].items():
        im = Image.open(src / name).convert("RGB")
        for b in boxes:
            blur_box(im, b)
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
        out = A / (Path(name).stem + ".png")
        im.save(out, compress_level=3)
        print(out.name, f"{im.width // 2}x{im.height // 2} (stored 2x)", len(boxes), "boxes blurred")


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("clip"); c.add_argument("src"); c.add_argument("name"); c.add_argument("--start", type=float, default=0)
    c.add_argument("--dur", type=float, default=3.2); c.add_argument("--crop", required=True)
    c.add_argument("--size", default="1280x800"); c.add_argument("--fps", type=int, default=30); c.set_defaults(fn=clip)
    s = sp.add_parser("still"); s.add_argument("src"); s.add_argument("name"); s.add_argument("--size", default="960x568")
    s.add_argument("--center-y", type=float, default=0.32); s.set_defaults(fn=still)
    k = sp.add_parser("key"); k.add_argument("src"); k.add_argument("name"); k.add_argument("--tol", type=int, default=18)
    k.set_defaults(fn=key)
    b = sp.add_parser("blur"); b.add_argument("spec"); b.set_defaults(fn=blur)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

"""Build a polished product walkthrough page from real (privacy-blurred) screenshots.

  python walkthrough.py spec.json            -> <name>.html + <name>.js + <name>.meta.json in the project
  PAGE=<name>.html MASTER=bed.wav OUTNAME=<name>_16x9.mp4 python ../render.py

Run it from the project folder: screenshots are read from assets/ (written 2x by `assets.py blur`), and
walk.js / walk.css are copied next to the page so the project renders on its own.

spec.json (see ../examples/walkthrough.example.json):
  name, format ("16x9" | "9x16"), dur, css {"--royal": "#hex", "--font": "Inter", ...}, font_css (Google Fonts URL),
  title {t1, kicker, text, logo}, end {t0, text, logo},
  shots: [{img, t0, t1, cam: [[t, cx, cy, zoom], ...], spots: [[t0, t1, [x0,y0,x1,y1]]],
           calls: [[t0, t1, [x, y], dx, dy, "text"]], rise, anchor}],
  caps:  [[t0, t1, "Headline with *accent*", "optional sub line"]]
Coordinates are in native screenshot pixels. "|" breaks a line; *words* take the accent color.
The meta file lists every cut and marks fast camera moves so render.py gives them extra subframes.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMATS = {
    "16x9": dict(W=1920, H=1080, anchor=[960, 430], css={"--capx": "118px", "--capy": "902px"}),
    "9x16": dict(W=1080, H=1920, anchor=[540, 1080], css={"--capx": "80px", "--capy": "150px", "--hfs": "76px",
                 "--sfs": "40px", "--tfs": "132px", "--pillfs": "40px", "--lockw": "860px", "--etfs": "58px"}),
}


def fast_windows(shots: list[dict], end_t0: float) -> list[tuple]:
    fast = []
    for s in shots:
        if s["rise"]:
            fast.append((s["t0"], s["t0"] + 1.1, 7))
        k = s["cam"]
        for a, b in zip(k, k[1:]):
            span = max(b[0] - a[0], 1e-3)
            dz = abs(b[3] - a[3]) / max(a[3], 1e-3)
            dp = (abs(b[1] - a[1]) + abs(b[2] - a[2])) * a[3] / span
            if dp > 250 or dz / span > 0.12:
                fast.append((a[0], b[0], 7))
    fast.append((end_t0 - 0.5, end_t0, 7))
    return fast


def build(spec: dict, root: Path) -> dict:
    from PIL import Image
    base = FORMATS[spec.get("format", "16x9")]
    shots = []
    for s in spec["shots"]:
        im = Image.open(root / "assets" / f"{s['img']}.png")
        d = dict(img=s["img"], iw=im.width // 2, ih=im.height // 2, t0=s["t0"], t1=s["t1"], cam=s["cam"],
                 spots=[dict(t0=a, t1=b, box=bx) for a, b, bx in s.get("spots", [])],
                 calls=[dict(t0=a, t1=b, at=at, dx=dx, dy=dy, text=tx) for a, b, at, dx, dy, tx in s.get("calls", [])],
                 rise=bool(s.get("rise")))
        if s.get("anchor"):
            d["anchor"] = s["anchor"]
        shots.append(d)
    caps = [dict(t0=c[0], t1=c[1], h=c[2], s=c[3] if len(c) > 3 else None) for c in spec.get("caps", [])]
    css = {**base["css"], **spec.get("css", {})}
    out = dict(W=base["W"], H=base["H"], anchor=base["anchor"], css=css, dur=spec["dur"],
               title=spec["title"], shots=shots, caps=caps, end=spec["end"])
    name = spec["name"]
    (root / f"{name}.js").write_text("window.SPEC = " + json.dumps(out) + ";\n", encoding="utf-8")
    font = spec.get("font_css", "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=block")
    (root / f"{name}.html").write_text(
        f'<!doctype html><html><head><meta charset="utf-8"><title>{name}</title>\n'
        f'<link rel="stylesheet" href="{font}">\n<link rel="stylesheet" href="walk.css"></head>'
        f'<body><div id="stage"></div>\n<script src="{name}.js"></script><script src="walk.js"></script></body></html>\n',
        encoding="utf-8")
    for f in ("walk.js", "walk.css"):
        shutil.copyfile(HERE / f, root / f)
    cuts = sorted({s["t0"] for s in shots} | {spec["end"]["t0"], spec["title"]["t1"]})
    meta = dict(dur=spec["dur"], cuts=cuts, fast=fast_windows(shots, spec["end"]["t0"]))
    (root / f"{name}.meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return meta


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    m = build(spec, Path.cwd())
    print(spec["name"], m["dur"], "s  cuts", m["cuts"])

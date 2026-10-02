"""Screenshot the page at given times plus a contact sheet, while building (before any render).
  python probe.py 0.3 1.2 4.0 8.5        (default: every half second across the spot)
Env: see _project.py, plus PROBES (output dir, default probes/)."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import SEEK_JS, meta, page_url, project, viewport  # noqa: E402


async def main() -> None:
    from PIL import Image
    from playwright.async_api import async_playwright

    dur = float(meta()["dur"])
    times = [float(x) for x in sys.argv[1:]] or [round(0.25 + 0.5 * i, 2) for i in range(int(dur * 2))]
    out = project() / os.environ.get("PROBES", "probes")
    out.mkdir(exist_ok=True)
    vp = viewport()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport=vp)
        pg.on("console", lambda m: print("console:", m.text))
        pg.on("pageerror", lambda e: print("pageerror:", e))
        await pg.goto(page_url())
        await pg.evaluate("window.ready")
        shots = []
        for t in times:
            await pg.evaluate(SEEK_JS, t)
            f = out / f"t{t:05.2f}.png"
            await pg.screenshot(path=str(f))
            shots.append(f)
        await b.close()
    cols = 5
    tw, th = (480, 270) if vp["width"] > vp["height"] else (216, 384)
    sheet = Image.new("RGB", (cols * tw, ((len(shots) + cols - 1) // cols) * th), (40, 40, 40))
    for i, f in enumerate(shots):
        sheet.paste(Image.open(f).convert("RGB").resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out / "sheet.jpg", quality=88)
    print("ok", len(shots), "->", out / "sheet.jpg")


if __name__ == "__main__":
    asyncio.run(main())

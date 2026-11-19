"""Left-hand panel (370x400): self-typing monochrome ASCII portrait.

usage: python scripts/make_ascii_svg.py photo.jpg [--crop x0,y0,x1,y1] [--cols 96]

* removes the background with `rembg` (falls back to the raw photo if missing)
* sharpens a little so facial features survive the downsample
* bright pixels -> dense glyphs, background -> blank (light-on-dark)
* every row wipes in left to right with a lilac block cursor; plays once, then freezes

Output: sevval-ascii.svg
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import *  # noqa: E402,F401,F403

W, H = 370, 400
OUT = pathlib.Path(__file__).parent.parent / "sevval-ascii.svg"
RAMP = " .:-=+*#%@"
INK = "#e0cffc"


def load_gray_and_mask(path, crop):
    import numpy as np
    from PIL import Image

    img = Image.open(path).convert("RGB")
    if crop:
        img = img.crop(crop)
    mask = None
    try:
        from rembg import new_session, remove

        cut = remove(img, session=new_session("u2net_human_seg")).convert("RGBA")
        mask = np.array(cut.split()[-1], dtype=float) / 255.0
    except Exception as e:  # optional dependency / offline
        print("background removal skipped:", e)
    from PIL import ImageFilter

    # grayscale + gentle unsharp mask so eyes / lips / brows survive the downsample
    g = np.array(img.convert("L").filter(ImageFilter.UnsharpMask(radius=6, percent=170, threshold=2)))
    return Image.fromarray(g), (Image.fromarray((mask * 255).astype("uint8")) if mask is not None else None)


def build(path, cols=96, crop=None, invert=False, ramp=RAMP) -> str:
    import numpy as np
    from PIL import Image

    g, m = load_gray_and_mask(path, crop)
    pad = 16
    cell_w = (W - 2 * pad) / cols
    cell_h = cell_w * 1.78
    max_rows = int((H - 34 - 2 * pad) / cell_h)
    rows = min(max_rows, round(cols * g.height / g.width * cell_w / cell_h))
    gs = np.array(g.resize((cols, rows), Image.LANCZOS), dtype=float) / 255.0
    ms = np.array(m.resize((cols, rows), Image.LANCZOS), dtype=float) / 255.0 if m else np.ones_like(gs)

    # histogram-equalise over the foreground so the whole glyph ramp gets used
    # (otherwise bright skin collapses into the top 2-3 glyphs and the face turns to mush)
    fg = np.sort(gs[ms > 0.5]) if (ms > 0.5).any() else np.sort(gs.ravel())
    tone = np.searchsorted(fg, gs) / max(len(fg), 1)
    tone = np.clip(tone, 0, 1) ** 1.15

    if invert:
        tone = 1 - tone
    size = cell_w / CH
    top = 34 + pad + (H - 34 - 2 * pad - rows * cell_h) / 2  # centre vertically
    parts = [svg_open(W, H, "ASCII portrait of Şevval"), window_chrome(W, H, "whoami")]
    for r in range(rows):
        chars = [ramp[int(tone[r, c] * (len(ramp) - 1))] if ms[r, c] > 0.5 else " " for c in range(cols)]
        line = "".join(chars).rstrip()
        if not line.strip():
            continue
        y = top + (r + 1) * cell_h
        total = cols * cell_w
        begin = 0.3 + r * 0.06
        parts.append(
            f'<clipPath id="r{r}"><rect x="{pad}" y="{y - cell_h:.1f}" width="0" height="{cell_h * 1.1:.1f}">'
            f'<animate attributeName="width" from="0" to="{total:.1f}" begin="{begin:.2f}s" dur="0.8s" fill="freeze"/></rect></clipPath>'
            f'<text x="{pad}" y="{y:.1f}" font-size="{size:.2f}" fill="{INK}" textLength="{len(line) * cell_w:.1f}" '
            f'lengthAdjust="spacing" clip-path="url(#r{r})">{esc(line)}</text>'
            f'<rect x="{pad}" y="{y - cell_h + 1:.1f}" width="{cell_w * 1.6:.1f}" height="{cell_h - 1:.1f}" fill="{LILAC}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" from="{pad}" to="{pad + total:.1f}" begin="{begin:.2f}s" dur="0.8s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + 0.8:.2f}s"/></rect>\n'
        )
    parts.append("</svg>\n")
    return "".join(parts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--cols", type=int, default=96)
    ap.add_argument("--crop", help="x0,y0,x1,y1 in pixels")
    ap.add_argument("--invert", action="store_true", help="dark pixels -> dense glyphs")
    ns = ap.parse_args()
    crop = tuple(int(v) for v in ns.crop.split(",")) if ns.crop else None
    OUT.write_text(build(ns.photo, ns.cols, crop, ns.invert), encoding="utf-8")
    print("wrote", OUT)

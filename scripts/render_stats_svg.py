"""Render data/stats.json (+ contributions.json) -> stats-card.svg (860 wide).

Left: language share (stacked bar + legend). Right: six number tiles.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import *  # noqa: E402,F401,F403

ROOT = pathlib.Path(__file__).parent.parent
OUT = ROOT / "stats-card.svg"
W, H = 860, 300
PALETTE = [LILAC, PINK, CYAN, MINT, "#8a5fd0", "#d9c2ff"]  # no yellow / gold
OTHER = "#5b4d7a"
MAX_LANGS = 6
BAR_X, BAR_W = 24, 416


def fmt(n):
    return "—" if n is None else f"{n:,}"


def build(stats, contrib) -> str:
    langs = stats.get("languages", [])
    top = langs[:MAX_LANGS]
    rest = round(sum(l["pct"] for l in langs[MAX_LANGS:]), 1)
    if rest >= 0.5:
        top = top + [{"name": "Other", "pct": rest}]
    colors = PALETTE[: len(top)]
    if top and top[-1]["name"] == "Other":
        colors = colors[: len(top) - 1] + [OTHER]

    active = sum(1 for d in contrib["days"] if d["count"]) if contrib else None
    tiles = [
        ("repos", stats.get("own_repos"), LILAC),
        ("total commits", stats.get("commits_total"), PINK),
        ("commits · 12mo", stats.get("commits_year"), CYAN),
        ("pull requests", stats.get("pull_requests"), MINT),
        ("stars", stats.get("stars"), LILAC),
        ("active days", active, PINK),
    ]

    css = (
        "@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}\n"
        ".r{animation:in .5s ease-out backwards}\n"
        f".n{{font-weight:bold;font-size:24px}}\n"
    )
    p = [svg_open(W, H, "GitHub stats: languages and numbers", css), window_chrome(W, H, "stats.sh")]
    p.append(f'<text x="{BAR_X}" y="64" font-size="11.5" fill="{DIM}">languages · share of my public repos</text>')

    # stacked bar, revealed left -> right
    p.append(f'<clipPath id="bar"><rect x="{BAR_X}" y="72" width="0" height="12" rx="6">'
             f'<animate attributeName="width" from="0" to="{BAR_W}" begin="0.3s" dur="1.1s" fill="freeze"/></rect></clipPath>')
    p.append('<g clip-path="url(#bar)">')
    x = BAR_X
    total = sum(l["pct"] for l in top) or 1
    for l, c in zip(top, colors):
        w = BAR_W * l["pct"] / total
        p.append(f'<rect x="{x:.2f}" y="72" width="{w + 0.5:.2f}" height="12" fill="{c}"/>')
        x += w
    p.append("</g>")

    y = 112
    for i, (l, c) in enumerate(zip(top, colors)):
        p.append(
            f'<g class="r" style="animation-delay:{0.5 + i * 0.1:.2f}s">'
            f'<circle cx="{BAR_X + 5}" cy="{y - 4}" r="5" fill="{c}"/>'
            f'<text x="{BAR_X + 20}" y="{y}" font-size="13" fill="{TEXT}">{esc(l["name"])}</text>'
            f'<text x="{BAR_X + BAR_W}" y="{y}" font-size="13" text-anchor="end" fill="{DIM}">{l["pct"]:.1f}%</text></g>'
        )
        y += 25
    if not top:
        p.append(f'<text x="{BAR_X}" y="112" font-size="13" fill="{DIM}">no language data yet</text>')

    # number tiles, 3 x 2
    tx0, tw, th, gap = 470, 114, 84, 12
    for i, (label, val, col) in enumerate(tiles):
        r, c = divmod(i, 3)
        x0, y0 = tx0 + c * (tw + gap), 54 + r * (th + 12)
        p.append(
            f'<g class="r" style="animation-delay:{0.4 + i * 0.12:.2f}s">'
            f'<rect x="{x0}" y="{y0}" width="{tw}" height="{th}" rx="10" fill="#171127" stroke="{PANEL_BORDER}"/>'
            f'<text class="n" x="{x0 + 14}" y="{y0 + 40}" fill="{col}">{fmt(val)}</text>'
            f'<text x="{x0 + 14}" y="{y0 + 62}" font-size="11" fill="{DIM}">{esc(label)}</text></g>'
        )
    p.append(f'<text x="{tx0}" y="{H - 24}" font-size="10.5" fill="{DIM}">public repos only · 12mo = last 12 months</text>')
    p.append("</svg>\n")
    return "\n".join(p)


if __name__ == "__main__":
    stats = json.loads((ROOT / "data" / "stats.json").read_text(encoding="utf-8"))
    cpath = ROOT / "data" / "contributions.json"
    contrib = json.loads(cpath.read_text(encoding="utf-8")) if cpath.exists() else None
    OUT.write_text(build(stats, contrib), encoding="utf-8")
    print("wrote", OUT)

"""Render data/contributions.json -> contrib-heatmap.svg (860 wide).

53 weeks x 7 days of rounded boxes that slide in diagonally once, then freeze.
"""
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import *  # noqa: E402,F401,F403

ROOT = pathlib.Path(__file__).parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

W = 860
BOX, GAP = 12, 3
PITCH = BOX + GAP
X0, Y0 = 46, 74  # grid origin
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def fmt_day(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}"


def build(data: dict) -> str:
    days = data["days"]
    nonzero = sorted(d["count"] for d in days if d["count"])
    p90 = nonzero[int(len(nonzero) * 0.9)] if nonzero else 1

    first = dt.date.fromisoformat(days[0]["date"])
    off = (first.weekday() + 1) % 7  # Sunday-first rows, like GitHub
    cells, month_cols = [], []
    prev_month = None
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        idx = i + off
        wk, dow = divmod(idx, 7)
        lvl = d["level"]
        if lvl >= 4 and d["count"] >= p90:
            lvl = 5  # brightest tier for the top 10 % of busy days
        cells.append((wk, dow, lvl, d))
        if dow == 0 or i == 0:
            if date.month != prev_month:
                month_cols.append((wk, MONTHS[date.month - 1]))
                prev_month = date.month
    weeks = cells[-1][0] + 1
    grid_h = 7 * PITCH - GAP
    foot_y = Y0 + grid_h + 30
    H = foot_y + 26

    css = (
        "@keyframes drop{from{opacity:0;transform:translateY(-9px)}to{opacity:1;transform:none}}\n"
        ".b{animation:drop .5s ease-out backwards}\n"
    )
    p = [svg_open(W, H, "Contribution heatmap", css), window_chrome(W, H, "contributions.sh")]

    # month labels (skip ones that would collide)
    last = -9
    for wk, name in month_cols:
        if wk - last >= 3:
            p.append(f'<text x="{X0 + wk * PITCH}" y="{Y0 - 9}" font-size="10.5" fill="{DIM}">{name}</text>')
            last = wk
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        p.append(f'<text x="14" y="{Y0 + row * PITCH + 10}" font-size="10" fill="{DIM}">{name}</text>')

    for wk, dow, lvl, d in cells:
        delay = (wk + dow * 1.5) * 0.022 + 0.2
        p.append(
            f'<rect class="b" style="animation-delay:{delay:.2f}s" x="{X0 + wk * PITCH}" y="{Y0 + dow * PITCH}" '
            f'width="{BOX}" height="{BOX}" rx="2.5" fill="{LEVELS[lvl]}">'
            f'<title>{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {fmt_day(d["date"])}</title></rect>'
        )

    # footer: totals on the left, legend on the right
    if data.get("placeholder"):
        left = "sample data · refreshes on the first workflow run"
    else:
        bd = data["best_day"]
        left = (f'{data["total"]:,} contributions in the last year · streak {data["current_streak"]}d '
                f'(best {data["longest_streak"]}d) · top day {fmt_day(bd["date"])} ({bd["count"]})')
    p.append(f'<text x="{X0}" y="{foot_y}" font-size="11.5" fill="{TEXT}">{esc(left)}</text>')
    lx = W - 24 - (6 * (BOX + 4)) - 62 - 30
    p.append(f'<text x="{lx}" y="{foot_y}" font-size="10.5" fill="{DIM}">Less</text>')
    for i, c in enumerate(LEVELS):
        p.append(f'<rect x="{lx + 34 + i * (BOX + 4)}" y="{foot_y - 10}" width="{BOX}" height="{BOX}" rx="2.5" fill="{c}"/>')
    p.append(f'<text x="{lx + 34 + 6 * (BOX + 4) + 4}" y="{foot_y}" font-size="10.5" fill="{DIM}">More</text>')
    p.append("</svg>\n")
    return "\n".join(p)


if __name__ == "__main__":
    OUT.write_text(build(json.loads(DATA.read_text(encoding="utf-8"))), encoding="utf-8")
    print("wrote", OUT)

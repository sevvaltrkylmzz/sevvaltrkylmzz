"""Right-hand panel (490x400): neofetch-style info card.

Edit INFO below, then run:  python scripts/make_info_card.py
Set STATIC=1 to emit a frozen frame (handy for local previews).
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from common import *  # noqa: E402,F401,F403

W, H = 490, 400
OUT = pathlib.Path(__file__).parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER = "sevval"
HOST = "themightydeveloper"

# (key, value, value colour)  — keep values <= ~44 characters
INFO = [
    ("Now", "Fibabank · ML & data in production", TEXT),
    ("Next", "data-focused roles · open to relocate", MINT),
    ("Stack", "Python · SQL · Git · Computer Vision", TEXT),
    ("Edu", "Computer Eng. · Eskişehir Technical Univ.", TEXT),
    ("Abroad", "Erasmus+ study (DE) · Erasmus+ intern (ES)", TEXT),
    ("Honors", "TÜBİTAK scholar · IELTS 8.0", TEXT),
    ("Research", "Springer Nature workshop co-author · 2026", TEXT),
    ("Creator", "@themightydeveloper on Instagram", PINK),
    ("Talks", "speaker at tech & student events", TEXT),
]

KEY_X, VAL_X = 24, 112
SIZE = 12.5


def build() -> str:
    css = (
        f".k{{fill:{LILAC};font-weight:bold}}\n"
        + ("" if STATIC else
           "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}\n"
           ".r{opacity:0;animation:in .45s ease-out forwards}\n")
        + ("" if not STATIC else ".r{opacity:1}\n")
    )
    p = [svg_open(W, H, "Sevval — info card", css), window_chrome(W, H, "neofetch")]

    def row(delay, inner):
        style = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        return f'<g class="r"{style}>{inner}</g>\n'

    d = 0.3
    head = f"{USER}@{HOST}"
    p.append(row(d, f'<text x="{KEY_X}" y="70" font-size="14" font-weight="bold" fill="{LILAC}">{esc(USER)}</text>'
                    f'<text x="{KEY_X + len(USER) * 14 * CH:.1f}" y="70" font-size="14" fill="{DIM}">@</text>'
                    f'<text x="{KEY_X + (len(USER) + 1) * 14 * CH:.1f}" y="70" font-size="14" font-weight="bold" fill="{PINK}">{esc(HOST)}</text>'))
    d += 0.12
    p.append(row(d, f'<text x="{KEY_X}" y="86" font-size="12" fill="{PANEL_BORDER}">{"─" * len(head)}</text>'))
    y = 114
    for k, v, col in INFO:
        d += 0.14
        p.append(row(d,
                     f'<text class="k" x="{KEY_X}" y="{y}" font-size="{SIZE}">{esc(k)}</text>'
                     f'<text x="{VAL_X - 12}" y="{y}" font-size="{SIZE}" fill="{DIM}">:</text>'
                     f'<text x="{VAL_X}" y="{y}" font-size="{SIZE}" fill="{col}">{esc(v)}</text>'))
        y += 25
    # colour swatches, neofetch style
    d += 0.2
    sw = "".join(f'<rect x="{KEY_X + i * 26}" y="{y + 4}" width="22" height="12" rx="3" fill="{c}"/>'
                 for i, c in enumerate([LEVELS[1], LEVELS[2], LEVELS[3], LILAC, PINK, MINT, CYAN]))
    p.append(row(d, sw))
    p.append("</svg>\n")
    return "".join(p)


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print("wrote", OUT)

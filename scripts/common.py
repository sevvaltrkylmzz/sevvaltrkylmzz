"""Shared theme + SVG helpers for the profile-README art.

Everything is pure SVG (SMIL + CSS keyframes, no JavaScript) so it renders
inside GitHub's image proxy.
"""
from html import escape

# ---- theme (lilac on deep violet-black) -------------------------------------
BG = "#0f0b18"
PANEL_BORDER = "#2a2140"
TEXT = "#e6e1f0"
DIM = "#a79fbb"
LILAC = "#B48EF0"
PINK = "#F08EC4"
MINT = "#7EE0C3"
CYAN = "#7CC4F5"
# contribution levels 0..5 (empty -> brightest)
LEVELS = ["#1c1630", "#3a2a63", "#5b3f99", "#8a5fd0", "#B48EF0", "#d9c2ff"]

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
CH = 0.6  # monospace advance width as a fraction of font-size


def esc(s: str) -> str:
    return escape(s, quote=True)


def svg_open(w: int, h: int, title: str, extra_css: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n"
        f"<style>\n"
        f"text{{font-family:{FONT};white-space:pre}}\n"
        f"{extra_css}\n"
        f"@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}\n"
        f"</style>\n"
    )


def window_chrome(w: int, h: int, title: str) -> str:
    """Rounded terminal window with a slim title bar (lilac dots, no yellow/gold)."""
    return (
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{PANEL_BORDER}"/>\n'
        f'<path d="M0.5 34 V12.5 a12 12 0 0 1 12 -12 H{w-12.5} a12 12 0 0 1 12 12 V34 Z" fill="#171127"/>\n'
        f'<line x1="0.5" y1="34.5" x2="{w-0.5}" y2="34.5" stroke="{PANEL_BORDER}"/>\n'
        f'<circle cx="20" cy="17.5" r="5" fill="{LILAC}"/>'
        f'<circle cx="38" cy="17.5" r="5" fill="#8a5fd0"/>'
        f'<circle cx="56" cy="17.5" r="5" fill="#5b3f99"/>\n'
        f'<text x="{w/2}" y="21.5" text-anchor="middle" font-size="12" fill="{DIM}">{esc(title)}</text>\n'
    )


def typed_text(uid, x, y, text, begin, size=13, fill=TEXT, per_char=0.035,
               weight="normal", cursor=True, cursor_fill=LILAC):
    """Text that 'types' itself in (SMIL, plays once, then freezes).

    Width is pinned with textLength so the reveal is identical in every font.
    """
    n = len(text)
    if n == 0:
        return ""
    cw = size * CH
    total = n * cw
    dur = max(0.2, n * per_char)
    values = ";".join(f"{cw * i:.2f}" for i in range(n + 1))
    xs = ";".join(f"{x + cw * i:.2f}" for i in range(n + 1))
    end = begin + dur
    out = (
        f'<clipPath id="c{uid}"><rect x="{x}" y="{y - size}" width="0" height="{size * 1.5:.1f}">'
        f'<animate attributeName="width" calcMode="discrete" values="{values}" '
        f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>\n'
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'textLength="{total:.2f}" lengthAdjust="spacing" clip-path="url(#c{uid})">{esc(text)}</text>\n'
    )
    if cursor:
        out += (
            f'<rect x="{x}" y="{y - size + 2}" width="{cw:.2f}" height="{size:.1f}" fill="{cursor_fill}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
            f'<animate attributeName="x" calcMode="discrete" values="{xs}" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>\n'
        )
    return out


def blink_cursor(x, y, begin, size=13, fill=LILAC):
    cw = size * CH
    return (
        f'<rect x="{x}" y="{y - size + 2}" width="{cw:.2f}" height="{size:.1f}" fill="{fill}" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{begin:.2f}s"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
        f'begin="{begin:.2f}s" repeatCount="indefinite"/></rect>\n'
    )

"""Inline SVG charts for the dashboards and the PDF reports (no JavaScript, prints as is).

Colours come from CSS custom properties defined in report.CSS, so the same SVG follows the
light/dark theme on screen and stays light in print.
"""
from __future__ import annotations

import html
import math

import numpy as np


def az(x, d: int = 1, pct: bool = False, sign: bool = False) -> str:
    """Azerbaijani number format: decimal comma, thin-space thousands, true minus sign."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    s = f"{abs(x):,.{d}f}".replace(",", " ").replace(".", ",")
    if x < 0 and float(f"{abs(x):.{d}f}") != 0:
        s = "−" + s
    elif sign and x > 0:
        s = "+" + s
    return s + ("%" if pct else "")


def _nice_ticks(lo, hi, n=5):
    if hi <= lo:
        hi = lo + 1
    span = hi - lo
    step = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n:
            step *= m
            break
    start = math.floor(lo / step) * step
    ticks = []
    t = start
    while t <= hi + step * 0.01:
        ticks.append(round(t, 10))
        t += step
    return ticks


def esc(s) -> str:
    return html.escape(str(s))


def line_band(x, series: list[dict], bands: list[dict] | None = None, title: str = "", ylab: str = "",
              hlines: list[dict] | None = None, vline=None, w: int = 680, h: int = 280, xfmt=str,
              ylim: tuple | None = None) -> str:
    """series: [{y, label, cls, dash}]; bands: [{lo, hi, cls}]; hlines: [{y, label, cls}]."""
    bands = bands or []
    hlines = hlines or []
    L, R, Tm, B = 56, 16, 30, 40
    xs = list(range(len(x)))
    allv = [v for s in series for v in s["y"] if v is not None and not np.isnan(v)]
    allv += [v for b in bands for v in list(b["lo"]) + list(b["hi"]) if v is not None and not np.isnan(v)]
    allv += [hl["y"] for hl in hlines]
    lo, hi = (min(allv), max(allv)) if not ylim else ylim
    pad = (hi - lo) * 0.06 or 1
    ticks = _nice_ticks(lo - pad, hi + pad)
    y0, y1 = ticks[0], ticks[-1]
    def X(i): return L + (w - L - R) * (i / max(len(x) - 1, 1))
    def Y(v): return Tm + (h - Tm - B) * (1 - (v - y0) / (y1 - y0))
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">',
           f"<title>{esc(title)}</title>"]
    for t in ticks:
        out.append(f'<line class="grid" x1="{L}" x2="{w - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>')
        out.append(f'<text class="tick" x="{L - 6}" y="{Y(t) + 4:.1f}" text-anchor="end">{az(t, 0 if abs(t) >= 10 or t == int(t) else 1)}</text>')
    if y0 < 0 < y1:
        out.append(f'<line class="zero" x1="{L}" x2="{w - R}" y1="{Y(0):.1f}" y2="{Y(0):.1f}"/>')
    step = max(1, len(x) // 8)
    for i in xs[::step]:
        out.append(f'<text class="tick" x="{X(i):.1f}" y="{h - B + 16}" text-anchor="middle">{esc(xfmt(x[i]))}</text>')
    if vline is not None:
        out.append(f'<line class="vline" x1="{X(vline):.1f}" x2="{X(vline):.1f}" y1="{Tm}" y2="{h - B}"/>')
    for b in bands:
        pts = [(X(i), Y(v)) for i, v in zip(xs, b["hi"]) if v is not None and not np.isnan(v)]
        idx = [i for i, v in zip(xs, b["hi"]) if v is not None and not np.isnan(v)]
        pts += [(X(i), Y(b["lo"][i])) for i in reversed(idx)]
        out.append(f'<polygon class="{b.get("cls", "band")}" points="{" ".join(f"{a:.1f},{c:.1f}" for a, c in pts)}"/>')
    for hl in hlines:
        out.append(f'<line class="{hl.get("cls", "ref")}" x1="{L}" x2="{w - R}" y1="{Y(hl["y"]):.1f}" y2="{Y(hl["y"]):.1f}"/>')
        if hl.get("anchor") == "start":
            out.append(f'<text class="reflab" x="{L + 6}" y="{Y(hl["y"]) + 14:.1f}" text-anchor="start">{esc(hl["label"])}</text>')
        else:
            out.append(f'<text class="reflab" x="{w - R - 4}" y="{Y(hl["y"]) - 5:.1f}" text-anchor="end">{esc(hl["label"])}</text>')
    for s in series:
        pts = [f"{X(i):.1f},{Y(v):.1f}" for i, v in zip(xs, s["y"]) if v is not None and not np.isnan(v)]
        out.append(f'<polyline class="{s.get("cls", "s1")}" points="{" ".join(pts)}"/>')
    # legend (starts after the y-axis label so the two never overlap)
    lx = max(L, 12 + 7 * len(ylab) + 18) if ylab else L
    for s in series:
        out.append(f'<line class="{s.get("cls", "s1")}" x1="{lx}" x2="{lx + 18}" y1="14" y2="14"/>'
                   f'<text class="leg" x="{lx + 22}" y="18">{esc(s["label"])}</text>')
        lx += 30 + 7 * len(s["label"])
    for b in bands:
        if b.get("label"):
            out.append(f'<rect class="{b.get("cls", "band")}" x="{lx}" y="8" width="16" height="10"/>'
                       f'<text class="leg" x="{lx + 20}" y="18">{esc(b["label"])}</text>')
            lx += 28 + 7 * len(b["label"])
    if ylab:
        out.append(f'<text class="tick" x="12" y="{Tm - 10}">{esc(ylab)}</text>')
    out.append("</svg>")
    return "".join(out)


def hbars(labels: list[str], values: list[float], values2: list[float] | None = None, title: str = "",
          unit: str = "", lab1: str = "", lab2: str = "", w: int = 680, row: int = 26) -> str:
    """Horizontal diverging bars (negative to the left); optional second series."""
    n = len(labels)
    L, R, Tm, B = 300, 70, 26, 26
    h = Tm + B + n * row
    allv = list(values) + (list(values2) if values2 else []) + [0]
    lo, hi = min(allv), max(allv)
    span = (hi - lo) or 1
    lo -= span * 0.05
    hi += span * 0.05
    def X(v): return L + (w - L - R) * (v - lo) / (hi - lo)
    out = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>',
           f'<line class="zero" x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{Tm - 4}" y2="{h - B + 4}"/>']
    for i, (lab, v) in enumerate(zip(labels, values)):
        yb = Tm + i * row
        hh = (row - 8) / (2 if values2 else 1)
        x0, x1 = sorted([X(0), X(v)])
        out.append(f'<text class="blab" x="{L - 8}" y="{yb + row / 2 + 2:.1f}" text-anchor="end">{esc(lab)}</text>')
        out.append(f'<rect class="{"neg" if v < 0 else "pos"}" x="{x0:.1f}" y="{yb + 3:.1f}" width="{max(x1 - x0, 0.8):.1f}" height="{hh:.1f}"><title>{esc(lab)}: {az(v, 2)} {esc(unit)}</title></rect>')
        # value label sits on the zero-line side opposite the bar, so it never runs into the row label
        vx = (x1 + 4) if v >= 0 else (X(0) + 4)
        out.append(f'<text class="bval" x="{vx:.1f}" y="{yb + 3 + hh - 3:.1f}" text-anchor="start">{az(v, 2, sign=True)}</text>')
        if values2:
            v2 = values2[i]
            a0, a1 = sorted([X(0), X(v2)])
            out.append(f'<rect class="alt" x="{a0:.1f}" y="{yb + 3 + hh:.1f}" width="{max(a1 - a0, 0.8):.1f}" height="{hh:.1f}"><title>{esc(lab)} ({esc(lab2)}): {az(v2, 2)} {esc(unit)}</title></rect>')
    if values2:
        out.append(f'<rect class="neg" x="{L}" y="6" width="14" height="9"/><text class="leg" x="{L + 18}" y="14">{esc(lab1)}</text>'
                   f'<rect class="alt" x="{L + 40 + 7 * len(lab1)}" y="6" width="14" height="9"/>'
                   f'<text class="leg" x="{L + 58 + 7 * len(lab1)}" y="14">{esc(lab2)}</text>')
    out.append(f'<text class="tick" x="{w - R}" y="{h - 6}" text-anchor="end">{esc(unit)}</text></svg>')
    return "".join(out)


def heatmap_table(S, risk_names: dict) -> str:
    """5×5 probability × impact grid; each cell lists its risk ids with the name on hover."""
    rows = ['<table class="heat" aria-label="Risk xəritəsi"><tr><th rowspan="2" class="plab">Ehtimal ↓</th>'
            '<th colspan="5">Təsir →</th></tr><tr>'
            + "".join(f"<th>{i}</th>" for i in range(1, 6)) + "</tr>"]
    plab = {5: "5 · > 50%", 4: "4 · 30–50%", 3: "3 · 15–30%", 2: "2 · 5–15%", 1: "1 · ≤ 5%"}
    for pb in range(5, 0, -1):
        rows.append(f'<tr><th class="plab">{plab[pb]}</th>')
        for ib in range(1, 6):
            sc = pb * ib
            lvl = "h" if sc >= 12 else ("m" if sc >= 6 else "l")
            ids = S[(S["P_bal"] == pb) & (S["I_bal"] == ib)]["risk_id"].tolist()
            chips = " ".join(f'<span class="hchip" title="{esc(risk_names[i])}">{i}</span>' for i in ids)
            rows.append(f'<td class="c{lvl}"><span class="sc">{sc}</span>{chips}</td>')
        rows.append("</tr>")
    rows.append("</table>")
    return "".join(rows)

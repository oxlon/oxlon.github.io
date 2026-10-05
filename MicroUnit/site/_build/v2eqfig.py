"""v2eqfig.py — the two Plotly charts inside every equation card: fitted vs actual (with the residual
as a second panel, not a second axis) and the recursive coefficients (small multiples, ±2 s.e.)."""
import math

from . import figs

RESID = "#9aa0a6"


def _num(xs):
    return figs._clean(xs)


def _base(height):
    return {"height": height, "autosize": True, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": figs.FONT, "size": 12, "color": "#1c1e21"}, "separators": ", ",
            "margin": {"l": 58, "r": 18, "t": 44, "b": 40}, "hovermode": "x unified",
            "legend": {"orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0, "xanchor": "left",
                       "font": {"size": 11.5, "color": figs.GREY}}}


def _ax(title=None, anchor=None, domain=None, x=False):
    a = {"gridcolor": "#eceff1", "zeroline": not x, "zerolinecolor": "#dadce0", "automargin": True}
    if x:
        a.update({"tickformat": "d"})
    if title:
        a["title"] = {"text": title, "font": {"size": 11.5}}
    if anchor:
        a["anchor"] = anchor
    if domain:
        a["domain"] = domain
    return a


def fitted(e):
    """Actual vs fitted (top panel) and residual bars (bottom panel), or None without data."""
    f = e.get("fitted") or {}
    yrs, act, fit, res = f.get("years"), f.get("actual"), f.get("fitted"), f.get("resid")
    if not yrs or not fit or len(yrs) != len(fit) or all(v is None for v in figs._clean(fit)):
        return None
    x = [int(y) if isinstance(y, (int, float)) and not isinstance(y, bool) and float(y).is_integer() else y
         for y in yrs]
    if not all(isinstance(v, int) for v in x):
        return None                      # panel / cross-section rows: no time axis to draw
    data = []
    if act and len(act) == len(x):
        data.append({"type": "scatter", "mode": "lines+markers", "name": "Faktiki", "x": x, "y": _num(act),
                     "line": {"color": figs.GREY, "width": 2}, "marker": {"size": 5, "color": figs.GREY},
                     "hovertemplate": "%{y:.4f}"})
    data.append({"type": "scatter", "mode": "lines", "name": "Qiymətləndirilmiş", "x": x, "y": _num(fit),
                 "line": {"color": figs.ACCENT, "width": 2.4}, "hovertemplate": "%{y:.4f}"})
    lay = _base(380)
    lay["xaxis"] = _ax(x=True, anchor="y2")
    lay["yaxis"] = _ax("asılı dəyişən", domain=[0.36, 1])
    if res and len(res) == len(x):
        data.append({"type": "bar", "name": "Qalıq", "x": x, "y": _num(res), "xaxis": "x", "yaxis": "y2",
                     "marker": {"color": RESID}, "hovertemplate": "%{y:.4f}"})
        lay["yaxis2"] = _ax("qalıq", domain=[0, 0.26])
        lay["yaxis2"]["anchor"] = "x"
    return {"data": data, "layout": lay}


def recursive(e, max_coef=4):
    """Recursive (expanding-window) path of each used coefficient, ±2 s.e., one panel per coefficient."""
    r = (e.get("robustness") or {}).get("recursive") or {}
    yrs, cf, se = r.get("years") or [], r.get("coef") or {}, r.get("se") or {}
    if len(yrs) < 2 or not cf:
        return None
    used = [c["name"] for c in e.get("coefficients") or [] if c.get("role") != "const" and c.get("name") in cf
            and not str(c.get("name")).startswith("d_")]
    names = (used or [k for k in cf if k != "const"])[:max_coef]
    names = [n for n in names if any(v is not None and not (isinstance(v, float) and math.isnan(v))
                                     for v in cf.get(n, []))]
    if not names:
        return None
    labels = {c["name"]: c.get("label_az") or c["name"] for c in e.get("coefficients") or []}
    full = {c["name"]: c.get("coef") for c in e.get("coefficients") or []}
    n = len(names)
    cols = 2 if n > 1 else 1
    rows = math.ceil(n / cols)
    lay = _base(230 * rows + 60)
    lay["showlegend"] = False
    lay["annotations"] = []
    data = []
    gap = 0.12
    for i, nm in enumerate(names):
        k = "" if i == 0 else str(i + 1)
        rr, cc = divmod(i, cols)
        x0 = cc / cols + (0.04 if cc else 0)
        x1 = (cc + 1) / cols - (0.04 if cc < cols - 1 else 0)
        y1 = 1 - rr / rows - (gap / 2 if rr else 0)
        y0 = 1 - (rr + 1) / rows + (gap / 2 if rr < rows - 1 else 0)
        c = cf.get(nm, [])
        s = se.get(nm) or [None] * len(c)
        lo = [a - 2 * b if a is not None and b is not None else None for a, b in zip(c, s)]
        hi = [a + 2 * b if a is not None and b is not None else None for a, b in zip(c, s)]
        xa, ya = "x" + k, "y" + k
        data.append({"type": "scatter", "mode": "lines", "x": yrs, "y": _num(hi), "xaxis": xa, "yaxis": ya,
                     "line": {"width": 0, "color": figs.BAND}, "hoverinfo": "skip", "name": "+2 standart xəta"})
        data.append({"type": "scatter", "mode": "lines", "x": yrs, "y": _num(lo), "xaxis": xa, "yaxis": ya,
                     "line": {"width": 0, "color": figs.BAND}, "fill": "tonexty", "fillcolor": figs.BAND,
                     "hoverinfo": "skip", "name": "−2 standart xəta"})
        data.append({"type": "scatter", "mode": "lines+markers", "x": yrs, "y": _num(c), "xaxis": xa, "yaxis": ya,
                     "line": {"color": figs.ACCENT, "width": 2}, "marker": {"size": 4, "color": figs.ACCENT},
                     "name": "rekursiv əmsal", "hovertemplate": "%{y:.4f}"})
        lay["xaxis" + k] = _ax(x=True, anchor=ya, domain=[x0, x1])
        lay["yaxis" + k] = _ax(anchor=xa, domain=[y0, y1])
        if isinstance(full.get(nm), (int, float)):
            lay.setdefault("shapes", []).append(
                {"type": "line", "xref": xa, "yref": ya, "x0": yrs[0], "x1": yrs[-1], "y0": full[nm], "y1": full[nm],
                 "line": {"color": figs.GREY2, "width": 1, "dash": "dot"}})
        lab = str(labels.get(nm, nm))
        lab = lab if len(lab) <= 46 else lab[:44] + "…"
        lay["annotations"].append({"text": f"<b>{nm}</b> — {lab}", "showarrow": False, "xref": "paper", "yref": "paper",
                                   "x": x0, "y": y1, "xanchor": "left", "yanchor": "bottom",
                                   "font": {"size": 11, "color": figs.GREY}})
    lay["margin"]["t"] = 30
    return {"data": data, "layout": lay}

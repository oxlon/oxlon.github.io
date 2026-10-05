"""figs.py — Plotly specs in the macro site's conventions.

accent #0f6b6b, fan band rgba(15,107,107,0.14), forecast shading from 2025.5 with the
"Proqnoz 2026–2030" annotation, secondary series grey #5f6368, hovermode "x unified",
horizontal legend on top.
"""
import math

ACCENT = "#0f6b6b"
GREY = "#5f6368"
GREY2 = "#9aa0a6"
BAND = "rgba(15,107,107,0.14)"
FONT = "-apple-system, 'Segoe UI', Roboto, Inter, sans-serif"
SCEN_COL = {"Baseline": ACCENT, "Adverse": GREY, "Reform": GREY}
SCEN_DASH = {"Baseline": "solid", "Adverse": "dash", "Reform": "dot"}
SCEN_AZ = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat"}


def _clean(xs):
    out = []
    for x in xs:
        try:
            f = float(x)
        except (TypeError, ValueError):
            out.append(None)
            continue
        out.append(None if math.isnan(f) else round(f, 4))
    return out


def layout(ytitle, x0=2005, x1=2030, forecast=True, height=420, dtick=5, ysuffix=""):
    lay = {
        "height": height, "autosize": True,
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": FONT, "size": 13, "color": "#1c1e21"},
        "margin": {"l": 64, "r": 26, "t": 58, "b": 46},
        "hovermode": "x unified", "separators": ", ",
        "hoverlabel": {"font": {"family": FONT, "size": 12}},
        "legend": {"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "xanchor": "left",
                   "traceorder": "normal", "font": {"size": 12, "color": GREY}},
        "colorway": [ACCENT, GREY],
        "xaxis": {"title": {"text": "İl"}, "gridcolor": "#eceff1", "zeroline": False, "tickformat": "d",
                  "dtick": dtick, "tick0": 2000, "range": [x0 - 0.6, x1 + 0.6]},
        "yaxis": {"gridcolor": "#eceff1", "zeroline": True, "zerolinecolor": "#dadce0",
                  "title": {"text": ytitle}, "ticksuffix": ysuffix,
                  "exponentformat": "none", "separatethousands": True},
    }
    if forecast:
        lay["shapes"] = [
            {"type": "rect", "xref": "x", "yref": "paper", "layer": "below", "x0": 2025.5, "x1": x1 + 0.6,
             "y0": 0, "y1": 1, "fillcolor": "rgba(15,107,107,0.045)", "line": {"width": 0}},
            {"type": "line", "xref": "x", "yref": "paper", "x0": 2025.5, "x1": 2025.5, "y0": 0, "y1": 1,
             "line": {"color": "#b8c2c4", "width": 1.2, "dash": "dot"}}]
        lay["annotations"] = [
            {"text": "Proqnoz 2026–2030", "showarrow": False, "xref": "x", "yref": "paper", "x": 2025.75,
             "y": 1.0, "xanchor": "left", "yanchor": "top", "font": {"size": 11, "color": GREY2}}]
    return lay


def band(x, lo, hi, name="5–95 % zolağı", color=BAND):
    x = [int(i) for i in x]
    return [
        {"type": "scatter", "mode": "lines", "name": name + " (yuxarı hədd)", "x": x, "y": _clean(hi),
         "line": {"width": 0, "color": color}, "showlegend": False, "hoverinfo": "skip", "legendrank": 3000},
        {"type": "scatter", "mode": "lines", "name": name, "x": x, "y": _clean(lo),
         "line": {"width": 0, "color": color}, "fill": "tonexty", "fillcolor": color, "hoverinfo": "skip",
         "legendrank": 3000},
    ]


def line(x, y, name, color=ACCENT, dash="solid", width=3, mode="lines", hfmt=None, rank=1000):
    t = {"type": "scatter", "mode": mode, "name": name, "x": [int(i) for i in x], "y": _clean(y),
         "line": {"color": color, "dash": dash, "width": width}, "connectgaps": False, "legendrank": rank}
    if mode != "lines":
        t["marker"] = {"color": color, "size": 6}
    if hfmt:
        t["hovertemplate"] = "%{y:" + hfmt + "}"
    return t


def scen_lines(x, by_scen, hfmt=None, only=("Adverse", "Reform")):
    """by_scen: {'Adverse': ys, 'Reform': ys} — grey dashed/dotted scenario lines."""
    out = []
    for s in only:
        if s in by_scen:
            out.append(line(x, by_scen[s], f"{SCEN_AZ[s]} ssenari", GREY, SCEN_DASH[s], 1.8, hfmt=hfmt, rank=2000))
    return out


def hbar(labels, values, xtitle, name, height=None, color=ACCENT, values2=None, name2=None, hfmt=".2f"):
    """Horizontal bar chart (categorical — no forecast shading)."""
    h = height or max(320, 28 * len(labels) + 120)
    data = [{"type": "bar", "orientation": "h", "y": list(labels), "x": _clean(values), "name": name,
             "marker": {"color": color}, "hovertemplate": "%{x:" + hfmt + "}<extra>" + name + "</extra>"}]
    if values2 is not None:
        data.append({"type": "bar", "orientation": "h", "y": list(labels), "x": _clean(values2), "name": name2,
                     "marker": {"color": "#b8c2c4"}, "hovertemplate": "%{x:" + hfmt + "}<extra>" + name2 + "</extra>"})
    lay = {"height": h, "autosize": True, "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
           "font": {"family": FONT, "size": 13, "color": "#1c1e21"}, "separators": ", ",
           "margin": {"l": 230, "r": 26, "t": 58, "b": 46}, "barmode": "group", "hovermode": "y unified",
           "legend": {"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "xanchor": "left",
                      "font": {"size": 12, "color": GREY}},
           "xaxis": {"title": {"text": xtitle}, "gridcolor": "#eceff1", "zeroline": True, "zerolinecolor": "#dadce0"},
           "yaxis": {"autorange": "reversed", "automargin": True}}
    return {"data": data, "layout": lay}


def spec(data, lay):
    return {"data": data, "layout": lay}


IMP_NAME = "Doldurulmuş (interpolyasiya)"


def imputed_series(x, y, imp, name, color=ACCENT, width=2.6, hfmt=None, rank=1000, show_imp_legend=True):
    """A history line whose imputed points are drawn as hollow markers joined by dashed segments
    (legend «Doldurulmuş (interpolyasiya)»); observed points keep the solid line with filled markers."""
    x = [int(i) for i in x]
    y = _clean(y)
    imp = [bool(i) for i in imp]
    obs = [v if not f else None for v, f in zip(y, imp)]
    out = [{"type": "scatter", "mode": "lines+markers", "name": name, "x": x, "y": obs, "connectgaps": False,
            "line": {"color": color, "width": width}, "marker": {"color": color, "size": 6}, "legendrank": rank}]
    if hfmt:
        out[0]["hovertemplate"] = "%{y:" + hfmt + "}"
    if not any(imp):
        return out
    sx, sy = [], []
    i, n = 0, len(x)
    while i < n:
        if imp[i]:
            j = i
            while j + 1 < n and imp[j + 1]:
                j += 1
            lo, hi = max(i - 1, 0), min(j + 1, n - 1)
            sx += x[lo:hi + 1] + [None]
            sy += y[lo:hi + 1] + [None]
            i = j + 1
        else:
            i += 1
    out.append({"type": "scatter", "mode": "lines", "name": IMP_NAME, "x": sx, "y": sy, "connectgaps": False,
                "line": {"color": color, "width": max(width - 0.8, 1.4), "dash": "dash"}, "showlegend": False,
                "legendgroup": "imp", "hoverinfo": "skip", "legendrank": rank + 1})
    mk = {"type": "scatter", "mode": "markers", "name": IMP_NAME, "x": [a for a, f in zip(x, imp) if f],
          "y": [b for b, f in zip(y, imp) if f], "legendgroup": "imp", "showlegend": show_imp_legend,
          "marker": {"symbol": "circle-open", "size": 10, "color": color, "line": {"width": 2, "color": color}},
          "legendrank": rank + 2}
    if hfmt:
        mk["hovertemplate"] = "%{y:" + hfmt + "} (doldurulmuş)"
    out.append(mk)
    return out

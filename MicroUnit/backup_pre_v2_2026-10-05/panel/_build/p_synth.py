"""p_synth.py — the SYNTHETIC Layer-B demonstration bundle (FR10 firm panel, FR12 business register).

Only pipeline demonstrations: distributions, HHI by NACE, entry/exit and survival curves, plus the
pipeline and swap tests. Every value is read from the watermarked FR10_SYNTHETIC_* / FR12_SYNTHETIC_* files.
"""
import numpy as np
import pandas as pd

from . import pcore as C
from .pnames import nace, NACE_AZ

RATIOS = [("current_ratio", "Cari likvidlik əmsalı"), ("debt_to_equity", "Borc / kapital"),
          ("roa", "Aktivlərin rentabelliyi (ROA)"), ("z_em", "Altman Z''-EM")]


def _lab(n):
    return f"{n} · {nace(n)}" if str(n).zfill(2) in NACE_AZ else f"NACE {n}"


def _hist(x, bins=30):
    x = x.replace([np.inf, -np.inf], np.nan).dropna()
    lo, hi = x.quantile(0.01), x.quantile(0.99)
    x = x[(x >= lo) & (x <= hi)]
    cnt, edges = np.histogram(x, bins=bins)
    return {"x": [C.fnum((a + b) / 2) for a, b in zip(edges[:-1], edges[1:])], "y": [int(c) for c in cnt],
            "cnt": int(len(x)), "med": C.fnum(x.median())}


def _tests(name, cols=("test", "passed", "value")):
    t = C.csv(name)
    out = []
    for r in t.to_dict("records"):
        out.append({"t": r.get("test"), "ok": bool(r.get("passed")), "v": str(r.get("value", r.get("detail", ""))) if
                    r.get("value", r.get("detail")) is not None else ""})
    return out


def build(data_dir):
    syn = {}
    fr = C.csv("FR10_SYNTHETIC_firm_ratios_2025.csv")
    syn["wm10"] = str(fr.WATERMARK.iloc[0])
    syn["ratios"] = [{"k": k, "n": lab, **_hist(fr[k])} for k, lab in RATIOS]
    cn = C.csv("FR10_SYNTHETIC_concentration_nace.csv", dtype={"nace2": str})
    last = int(cn.year.max())
    c = cn[cn.year == last].sort_values("HHI", ascending=False)
    syn["hhi10"] = {"year": last, "lab": [_lab(n) for n in c.nace2], "hhi": [C.fnum(x) for x in c.HHI],
                    "cr4": [C.fnum(x) for x in c.CR4_pct]}
    ee = C.csv("FR10_SYNTHETIC_entry_exit.csv").groupby("year")[["firms", "entrants", "exits"]].sum()
    syn["ee10"] = {"year": [int(y) for y in ee.index], "entry": [C.fnum(x) for x in ee.entrants / ee.firms * 100],
                   "exit": [C.fnum(x) for x in ee.exits / ee.firms * 100]}
    es = C.csv("FR12_SYNTHETIC_entry_exit_section.csv")
    syn["wm12"] = str(es.WATERMARK.iloc[0])
    tot = es.groupby("year")[["active_end", "entrants", "exits"]].sum()
    syn["ee12"] = {"year": [int(y) for y in tot.index], "entry": [C.fnum(x) for x in tot.entrants / tot.active_end * 100],
                   "exit": [C.fnum(x) for x in tot.exits / tot.active_end * 100]}
    km = C.csv("FR12_SYNTHETIC_survival_km.csv")
    syn["km"] = [{"c": int(k), "age": [int(a) for a in g.age], "s": [C.fnum(s) for s in g.survival]}
                 for k, g in km.groupby("cohort")]
    c12 = C.csv("FR12_SYNTHETIC_concentration_nace.csv", dtype={"nace2": str})
    l12 = int(c12.year.max())
    c12 = c12[(c12.year == l12) & c12.HHI.notna()].sort_values("HHI", ascending=False).head(25)
    syn["hhi12"] = {"year": l12, "lab": [_lab(n) for n in c12.nace2], "hhi": [C.fnum(x) for x in c12.HHI]}
    syn["pipe10"] = _tests("FR10_SYNTHETIC_pipeline_tests.csv")
    syn["pipe12"] = _tests("FR12_SYNTHETIC_pipeline_tests.csv")
    syn["swap10"] = [{"t": r["test"], "ok": bool(r["passed"]), "v": str(r["detail"])}
                     for r in C.csv("FR10_firm_panel_swap_tests.csv").to_dict("records")]
    syn["swap12"] = [{"t": r["test"], "ok": bool(r["passed"]), "v": str(r["detail"])}
                     for r in C.csv("FR12_business_register_swap_tests.csv").to_dict("records")]
    # file facts, counted from the synthetic input files themselves
    p = pd.read_csv(C.UNIT / "data/firm_panel/FR10_firm_panel_SYNTHETIC.csv", dtype={"nace2": str},
                    usecols=["firm_id", "year", "nace2", "region"])
    r = pd.read_csv(C.UNIT / "data/business_register/FR12_business_register_SYNTHETIC.csv", dtype={"nace2": str},
                    usecols=["firm_id", "year", "nace2", "region", "status", "weight"])
    ly = int(r.year.max())
    syn["files"] = {"p_rows": len(p), "p_firms": int(p.firm_id.nunique()), "p_nace": int(p.nace2.nunique()),
                    "p_y0": int(p.year.min()), "p_y1": int(p.year.max()), "r_rows": len(r),
                    "r_records": int(r.firm_id.nunique()), "r_nace": int(r.nace2.nunique()), "r_regions": int(r.region.nunique()),
                    "r_active": int(r[(r.year == ly) & (r.status == "active")].weight.sum()), "r_last": ly,
                    "r_y0": int(r.year.min())}
    C.js_bundle(data_dir / "synthetic.js", "SYN", syn)
    return syn

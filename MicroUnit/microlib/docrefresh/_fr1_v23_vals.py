"""FR1 v2.3 figures shared by the EN and AZ passages: FR1_doc_figures.json, FR1_v23_*.csv, the current forecast and the
frozen v2.2 run (v22_reference.json)."""
from types import SimpleNamespace

SCEN = ("Baseline", "Adverse", "Reform")
V22 = "v2.2 model (before v2.3)"
V23 = "v2.3 model (adopted changes)"
MED = "median of the 14 Part-11.5 variables"
LBL = {"D4u": "D4: imports at constant USD prices (same fit, relative price re-parametrised)",
       "D4n": "D4: relative price dropped (coefficient bounded at 0, binding)",
       "E3w": "E3: + real wage bill, homogeneity imposed", "E3f": "E3: + real wage bill, homogeneity test-and-impose rule",
       "F3s": "F3: non-oil and oil revenue separately", "F3n": "F3: non-oil revenue only (oil revenue saved)",
       "F3c": "F3: revenue elasticity at its 95% CI lower bound",
       "F4u": "F4: scenario capital-spending rule (Baseline policy level + F4 response), unit elasticity",
       "F4c": "F4: scenario capital-spending rule, oil-revenue elasticity at its 95% CI lower bound"}
FISC = ["F3s", "F3n", "F3c", "F4u", "F4c"]


def v23_vals(F):
    N = SimpleNamespace(); d = F.docfig; v22 = F.ref["v22"]; v23 = d["v23"]
    N.d = d; N.e3, N.d4 = v23["e3"], v23["d4"]
    N.hl, N.decay = v23["addf_halflife"], v23["addf_decay"]
    af = F.af
    N.af_dec = {k: af.loc[f"{lab}, base add-factors decay at a fixed half-life"] for k, lab in (("g", "real GDP"), ("n", "non-oil GDP"))}
    N.af_const = {"g": F.avg_rgdp, "n": F.avg_non}
    N.af_rho = v22["addf_rho_avg_growth"]
    N.c = lambda key, var: F.c23(LBL[key], var)
    N.ref22 = lambda var: F.c23(V22, var)
    N.cur = lambda var: F.c23(V23, var)
    dec = F.dec23.set_index("variant")
    N.dec = lambda key: dec.loc[LBL[key]]
    N.mw = v23["minwage_10pct_2030"]
    fd = F.fis23
    N.fis = {k: fd.loc[k] for k in ("oil revenue", "non-oil revenue", "current spending", "capital spending", "debt service", "balance")}
    N.cut_per_azn = fd.loc["spending cut per AZN of revenue lost", "difference"]
    N.adv_istate = fd.loc["Adverse balance 2030 (% of GDP) with the Baseline state-investment policy level"]
    N.oil_vs_inv = fd.loc["real oil revenue vs real state investment, Adverse / Baseline 2030 - 1 (%)"]
    N.el = {"F3": fd.loc["F3_expcur elasticity (ln_rev_r): solver value, estimate, 95% CI"],
            "F4": fd.loc["F4_pubinv elasticity (ln_rev_oil): solver value, estimate, 95% CI"]}
    b30 = F.base.loc[2030]
    N.d30 = {k: (b30[k] / v22["baseline_2030"][k] - 1) * 100 for k in v22["baseline_2030"]}
    N.avg = {"g": F.avg_rgdp, "n": F.avg_non}
    N.avg22 = {"g": v22["avg_growth_rgdp"], "n": v22["avg_growth_rgdpnon"]}
    N.bal = {s: F.fc[s].loc[2030, "balance_n"] / F.fc[s].loc[2030, "gdp_n"] * 100 for s in SCEN}
    N.bal22 = v22["balance_gdp_2030"]
    N.med, N.med22 = N.cur(MED), N.ref22(MED)
    N.neq = len(F.E); N.nused = sum(e["used_in_forecast"] for e in F.E.values())
    N.neq22 = v22["n_equations"]
    N.nrej = sum(1 for k in F.E if any(k.endswith(x) for x in (".v22", ".v22_gdp_prices", ".v23_norelprice", ".v23_rev_split",
                                                              ".v23_rev_non", ".v23_rev_cap", ".v23_cap")))
    return N


def code_cells_before_part18():
    """code cells of FR1.ipynb before the Part 18 heading (the header line of the methodology)"""
    import json
    from .common import ROOT
    with open(ROOT / "FR1.ipynb", encoding="utf-8") as f:
        cells = json.load(f)["cells"]
    n = 0
    for c in cells:
        if c["cell_type"] == "markdown" and "".join(c["source"]).lstrip().startswith("## Hissə 18"):
            return n
        n += c["cell_type"] == "code"
    raise ValueError("FR1.ipynb: Part 18 heading not found")


def gfmt(x):
    """'1' for 1.0, '1.5' otherwise (half-life)"""
    return f"{x:g}"

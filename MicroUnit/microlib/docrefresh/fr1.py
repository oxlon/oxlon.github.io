"""FR1 — v2.2 note (macro-module adoption) and the run-dependent v2.2 passages of §6.2, §7.2–§7.6, §8.4 and §9, EN + AZ.

Sources (current run): output/FR1_holdout_validation.csv, FR1_v22_macro_candidates.csv, FR1_forecast_full.csv,
FR1_analysis_dataset.csv (2025 actuals), FR1_addfactor_sensitivity.csv, FR1_trend_share.csv, FR1_multipliers.csv,
FR1_fiscal_multiplier.csv, FR1_fan_*.csv, FR1_accounts_summary_baseline.csv, FR1_accounts_{history,forecast}_nominal.csv,
FR1_equations.json, FR1_indicator_catalog.csv; data/macro_module/8_vereq_original.xlsx (the Ministry's output plan).
v2.1 comparison values and the few figures FR1.ipynb does not export: v22_reference.json.

v2.3: the v2.3 note and the formerly hand-written run-dependent passages (solver iterations §7.1, the January–April bridge,
anchor and comparison table §7.2, the fan diagnostics and centring §7.5, §9 item 17, the E3 description §3.3) are generated
from FR1_doc_figures.json (FR1.ipynb Part 18.17), FR1_v23_candidates.csv, FR1_v23_decisions.csv, FR1_v23_forecast_checks.csv,
FR1_v23_fiscal_diagnosis.csv and FR1_equations.json; the v2.2 note's forecast figures are the frozen v2.2 run (v22_reference.json).
"""
import json
from types import SimpleNamespace

import pandas as pd

from .common import DATA, DOCS, Doc, csv, ref, registry, run

SCEN = ("Baseline", "Adverse", "Reform")
FY = [2026, 2027, 2028, 2029, 2030]
CUR = "v2.2 model (adopted changes)"          # FR1_v22_macro_candidates.csv: the current model
PRE = "pre-v2.2 model"                        # the same run with the pre-v2.2 equations
EXP = ['Brent +10 USD/bbl', 'State investment +1 bn AZN (real)', 'Credit easing (-200 bp policy, -100 bp deposit)',
       'Credit easing + judgemental credit->investment overlay', 'External demand +10%']


def _plan_growth():
    """Ministry plan growth rates (%) 2026-2030 and the 2025 plan levels (mt, bcm), as FR1.ipynb Part 3.6 reads them."""
    import openpyxl
    ws = openpyxl.load_workbook(DATA / "macro_module" / "8_vereq_original.xlsx", read_only=True, data_only=True)["2.4.1.4."]
    rows = list(ws.iter_rows(values_only=True)); yrs = list(rows[2][3:])
    plan = {}
    for r in rows:
        if r[1] in ("Neft hasilatı", "Qaz hasilatı"):
            plan[{"Neft hasilatı": "oil", "Qaz hasilatı": "gas"}[r[1]]] = pd.Series([float(v) / 1000 for v in r[3:]], index=yrs)
    P = pd.DataFrame(plan)
    return (P.pct_change() * 100).loc[2026:2030], P.loc[2025]


def data():
    F = SimpleNamespace()
    F.ref = ref("FR1")
    F.HV = csv("FR1_holdout_validation.csv").set_index("variable")
    CA = csv("FR1_v22_macro_candidates.csv")
    F.cand = lambda variant, var: CA[(CA.variant == variant) & (CA.variable == var)].iloc[0]
    F.cur = lambda var: F.cand(CUR, var)
    F.pre = lambda var: F.cand(PRE, var)
    ff = csv("FR1_forecast_full.csv", index_col=0)
    F.fc = {s: ff[ff.scenario == s] for s in SCEN}
    F.A = csv("FR1_analysis_dataset.csv", index_col=0)
    F.LAST = int(F.A.index.max())                    # last actual year (2025)
    F.base = F.fc["Baseline"]

    def growth(k, s="Baseline"):
        x = pd.concat([pd.Series({F.LAST: F.A.loc[F.LAST, k]}), F.fc[s][k]])
        return (x / x.shift(1) - 1).loc[FY] * 100
    F.g = growth
    F.avg = lambda k: ((F.base.loc[2030, k] / F.A.loc[F.LAST, k]) ** (1 / len(FY)) - 1) * 100
    AF = csv("FR1_addfactor_sensitivity.csv", index_col=0)
    F.af = AF
    F.avg_rgdp = AF.loc["real GDP, constant base add-factors"]
    F.avg_non = AF.loc["non-oil GDP, constant base add-factors"]
    F.TS = csv("FR1_trend_share.csv").set_index("sector")["trend share of growth (%)"]
    M = csv("FR1_multipliers.csv"); M.columns = ["exp", "year"] + list(M.columns[2:])
    # rounded to 4 decimals first, as the 2026-10-05 text was produced (keeps x.xx5 cases stable)
    F.mult = lambda e, k: round(float(M[(M.exp == e) & (M.year == 2030)][k].iloc[0]), 4)
    FM = csv("FR1_fiscal_multiplier.csv", index_col=0)
    inj = FM["injection (real state investment, mln)"]
    F.fm = SimpleNamespace(inj=inj.loc[2030], dnon=FM["d real non-oil GDP (mln)"].loc[2030],
                           lvl=FM["impact multiplier, non-oil GDP"].loc[2030],
                           cum=FM["d real non-oil GDP (mln)"].sum() / inj.sum(), cum_rgdp=FM["d real GDP (mln)"].sum() / inj.sum())
    F.band = {}
    for k in ("rgdp", "rgdpnon", "cpi", "emp", "rhhdisp", "rcons", "rexp_cur"):
        r = csv(f"FR1_fan_{k}.csv", index_col=0).loc[2030]
        F.band[k] = ((r.p95 - r.p5) / r.p50 * 100, (r.p75 - r.p25) / r.p50 * 100)
    gq = csv("FR1_fan_growth_rgdp.csv", index_col=0); iq = csv("FR1_fan_infl.csv", index_col=0)
    F.gband = (gq.p5.min(), gq.p95.max()); F.iband = (iq.p5.min(), iq.p95.max())
    F.ACC = csv("FR1_accounts_summary_baseline.csv").set_index("entity")
    hn = csv("FR1_accounts_history_nominal.csv", index_col=0)
    fn = csv("FR1_accounts_forecast_nominal.csv"); fn.columns = ["sc", "ent"] + list(fn.columns[2:])
    F.hc25 = hn.loc["Mining & quarrying", str(F.LAST)] / hn.loc["GDP at market prices", str(F.LAST)] * 100
    F.hc30 = {}
    for s in SCEN:
        x = fn[fn.sc == s].set_index("ent")["2030"]
        F.hc30[s] = x["Mining & quarrying"] / x["GDP at market prices"] * 100
    F.plan_g, F.plan25 = _plan_growth()
    F.E, F.J = registry("FR1")
    F.ncat = len(csv("FR1_indicator_catalog.csv"))
    F.sip = F.base.loc[2026, "exp_pubinv_n"]
    # v2.3
    from .common import OUT, RefreshError
    p = OUT / "FR1_doc_figures.json"
    if not p.exists():
        raise RefreshError("missing output file output/FR1_doc_figures.json")
    with open(p, encoding="utf-8") as f:
        F.docfig = json.load(f)
    dv = F.docfig.get("v23", {}).get("deval")
    if dv:                                          # year keys of the devaluation paths back to int
        for part in ("engine", "engine_no_f4"):
            dv[part] = {k: {int(y): v for y, v in d.items()} for k, d in dv[part].items()}
    C23 = csv("FR1_v23_candidates.csv")
    F.c23 = lambda variant, var: C23[(C23.variant == variant) & (C23.variable == var)].iloc[0]
    F.cur23 = lambda var: F.c23("v2.3 model (adopted changes)", var)
    F.dec23 = csv("FR1_v23_decisions.csv")
    F.chk23 = csv("FR1_v23_forecast_checks.csv")
    F.fis23 = csv("FR1_v23_fiscal_diagnosis.csv").set_index("item")
    F.dec = csv("FR1_sector_decomposition_all.csv")
    return F


def sp(v):
    """'2 700' — thousands separated by a space (EN and AZ)"""
    return f"{v:,.0f}".replace(",", " ")


def main():
    from ._fr1_az import az_blocks
    from ._fr1_en import en_blocks
    from ._fr1_note import note_az, note_en
    from ._fr1_v23_en import v23_en
    from ._fr1_v23_az import v23_az
    F = data()
    LEG = ("<!-- v2.2-begin -->", "<!-- v2.2-end -->")

    def filler(note, blocks, extra):
        def fill(d):
            d.put("v22_note", note, legacy=LEG)
            for tag, (body, inline) in extra(F).items():
                d.put(tag, body, inline=inline)
            for tag, (body, inline) in blocks.items():
                d.put(tag, body, inline=inline)
        return fill
    from ._fr1_v236_sweep import sweep_en, sweep_az
    from ._fr1_v237 import blocks as v237
    run("FR1", [(Doc(DOCS / "FR1_Methodology.md"), filler(note_en(F), en_blocks(F), lambda F: {**v23_en(F), **sweep_en(F), **v237(F, 'en')})),
                (Doc(DOCS / "az" / "FR1_Metodologiya.md"), filler(note_az(F), az_blocks(F), lambda F: {**v23_az(F), **sweep_az(F), **v237(F, 'az')}))])

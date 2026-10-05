"""FR1 English v2.2 passages (docs/FR1_Methodology.md).  Each entry: tag -> (text, inline)."""
from .common import pm
from .fr1 import EXP, sp

MULT_ROWS = [("rva_con", "Construction", "Tikinti"), ("rva_man", "Manufacturing", "Emal sənayesi"), ("rva_trd", "Trade", "Ticarət"),
             ("rva_ict", "ICT", "İnformasiya və rabitə (ICT)"), ("rgdp", "Real GDP (chain-linked)", "Real ÜDM (zəncirvari)"),
             ("rgdpnon", "Real non-oil GDP", "Real qeyri-neft ÜDM"), ("rcons", "Consumption", "İstehlak"),
             ("rinv_non", "Non-oil investment", "Qeyri-neft investisiyası"), ("rev_tot_n", "Budget revenue", "Büdcə gəlirləri"),
             ("rm_non", "Non-oil imports", "Qeyri-neft idxalı")]
PATH_ROWS = [("rgdp", "Real GDP", "Real ÜDM"), ("rgdpnon", "Real non-oil GDP", "Real qeyri-neft ÜDM"), ("rcons", "Consumption", "İstehlak"),
             ("rva_man", "Manufacturing", "Emal sənayesi"), ("rva_agr", "Agriculture", "Kənd təsərrüfatı"),
             ("rva_con", "Construction", "Tikinti"), ("rva_ict", "ICT", "İnformasiya və rabitə (ICT)")]
BAND_ROWS = [("rgdp", "Real GDP", "Real ÜDM"), ("rgdpnon", "Real non-oil GDP", "Real qeyri-neft ÜDM"), ("cpi", "CPI level", "İQİ səviyyəsi"),
             ("emp", "Employment", "Məşğulluq"), ("rhhdisp", "Real disposable income", "Real sərəncamda qalan gəlir"),
             ("rcons", "Real consumption", "Real istehlak"), ("rexp_cur", "Real current spending", "Real cari xərclər")]
ACC_FIXED = ["GDP at market prices", "Non-oil GDP", "Oil and gas GDP"]


def holdout_stats(F):
    H = F.HV
    S = dict(n=len(H), rw20=((H.U_rw2020 < 1).sum(), H.U_rw2020.median()), rw19=((H.U_rw2019 < 1).sum(), H.U_rw2019.median()),
             cg19=((H.U_cg1019 < 1).sum(), H.U_cg1019.median()), cg20=((H.U_cg1020 < 1).sum(), H.U_cg1020.median()),
             sig=((H.DM_p_rw2020 < 0.10).sum(), (H.DM_p_cg1019 < 0.10).sum()),
             pol=(H.U_rw2020_policy.median(), H.U_cg1019_policy.median()))
    S["r"] = lambda v: H.loc[v, "model_RMSE"]
    weak = [H.loc[v, "model_RMSE"] for v in ("ICT VA", "construction VA", "transport VA", "manufacturing VA")]
    S["weak"] = (min(weak), max(weak))
    return S


def band_err(F, k):
    """hold-out 5-year (2025) level error, % — §6.2 table, the candidates file, or (CPI level) the frozen value"""
    hv = {"rgdp": "real GDP", "rgdpnon": "real non-oil GDP", "emp": "employment"}
    if k in hv:
        return F.HV.loc[hv[k], "err_2025"]
    if k == "cpi":
        return F.docfig["v23"]["cpi_level_holdout_err_2025"]
    return F.cur23(k).err_2025                 # v2.3: the current model's hold-out (Part 11.7)


def acc_rows(F):
    sec = F.ACC[F.ACC.group == "1 Sectors (value added)"].sort_values("real_growth_avg_pct", ascending=False).index.tolist()
    return ACC_FIXED + sec


def en_blocks(F):
    S = holdout_stats(F); H = F.HV; n = S["n"]; r = S["r"]
    rg, rn = H.loc["real GDP"], H.loc["real non-oil GDP"]
    P, C = F.pre, F.cur
    B = {}
    B["v22_holdout"] = (f"""| | Result ({n} variables) |
|---|---|
| Beats a random walk from 2020 (pandemic trough) | {S['rw20'][0]} of {n}, median U **{S['rw20'][1]:.2f}** |
| Beats a random walk from 2019 | {S['rw19'][0]} of {n}, median U {S['rw19'][1]:.2f} |
| Beats constant growth 2010–2019 (pre-pandemic) | **{S['cg19'][0]} of {n}, median U {S['cg19'][1]:.2f}** |
| Beats constant growth 2010–2020 | {S['cg20'][0]} of {n}, median U {S['cg20'][1]:.2f} |
| Significant wins (HLN-DM p < 0.10) | {S['sig'][0]} vs RW2020; {S['sig'][1]} vs constant growth 2010–19 |
| Real GDP level error after 5 years | **{pm(rg.err_2025, 1)}%** (U {rg.U_rw2020:.2f} vs RW2020, {rg.U_cg1019:.2f} vs CG 2010–19) |
| Real non-oil GDP level error after 5 years | {pm(rn.err_2025, 1)}% (U {rn.U_rw2020:.2f} vs RW2020, {rn.U_cg1019:.2f} vs CG 2010–19) |
| Policy-level variant | median U {S['pol'][0]:.2f} vs RW2020, {S['pol'][1]:.2f} vs CG 2010–19 |

*(v2.2 figures: the mining deflator on the hydrocarbon export price index — see the v2.2 note. Its own hold-out error falls
from {P('p_min').rmse:.1f}% to {C('p_min').rmse:.1f}% and nominal GDP's from {P('gdp_n').rmse:.1f}% to {C('gdp_n').rmse:.1f}%, but real GDP's rises from {P('rgdp').rmse:.1f}% to {C('rgdp').rmse:.1f}% because the more accurate
2021–22 mining prices give mining, whose volume fell, a larger chain weight.)*""", False)
    w = "win" if S["sig"][1] == 1 else "wins"
    B["v22_headline62"] = (f"""**Headline:** the random walk from 2020 flatters the model (2020 was the pandemic trough). Against constant growth estimated over
the pre-pandemic decade the model is roughly **on par** (median U {S['cg19'][1]:.2f}; {S['sig'][1]} significant {w}). Tracked well: consumption (RMSE
{r('real consumption'):.1f}%), trade {r('trade VA'):.1f}%, employment {r('employment'):.1f}%, agriculture {r('agriculture VA'):.1f}%, real GDP {r('real GDP'):.1f}%. Tracked poorly: construction {r('construction VA'):.1f}%, transport {r('transport VA'):.1f}%,
manufacturing {r('manufacturing VA'):.1f}%, state investment {r('state investment'):.1f}%, ICT {r('ICT VA'):.1f}% (v2.1: 2020, the cut year, was an ICT investment trough) — sectors transformed after 2020 (new manufacturing capacity, the Karabakh and East
Zangezur reconstruction, the Middle Corridor). Real current spending is {'over' if F.cur23('rexp_cur').err_2025 > 0 else 'under'}-predicted by {abs(F.cur23('rexp_cur').err_2025):.0f}% by 2025.""", False)
    gc, gn, gi = F.g("rva_con"), F.g("rgdpnon"), F.g("rva_ict")
    B["v22_sawtooth"] = (f"{pm(gc[2026], 1)}% (2026) →\n{pm(gc[2027], 1)}% (2027) → {pm(gc[2028], 1)}% (2028); non-oil GDP "
                         f"{pm(gn[2026])}% → {pm(gn[2027])}% → {pm(gn[2028])}%", True)
    B["v22_sawtooth_ict"] = (f"{pm(gi[2026], 1)}% → {pm(gi[2027], 1)}%", True)
    B["v22_sip"] = (f"approved State Investment Programme ({sp(F.sip)} mln AZN, sheet `DİP 2016-2026`)", True)
    B["v22_scenarios"] = (scen_table(F, "en"), False)
    B["v22_results"] = (results_table(F, "en"), False)
    B["v22_path"] = (path_table(F, "en"), False)
    gcs = F.g("rcons")
    B["v22_whycons"] = (f"grows\n{gcs.min():.1f}–{gcs.max():.1f}% a year (history", True)
    B["v22_whynonoil"] = (f"of\n{F.avg_non['Baseline']:.1f}% a year (v2.3)", True)
    B["v22_man"] = (f"~{F.avg('rva_man'):.1f}% a year (v2.3", True)
    B["v22_manrmse"] = (f"the hold-out RMSE for manufacturing is {r('manufacturing VA'):.1f}%", True)
    T = F.TS
    B["v22_trend"] = (f"transport ({T['Transport & storage']:.0f}%), ICT ({T['Information & communication']:.0f}%;\nv2.3), "
                      f"agriculture ({T['Agriculture, forestry & fishing']:.0f}%) and electricity ({T['Electricity, gas & steam']:.0f}%)", True)
    d1, d2 = F.af.loc["real GDP, base add-factors decay at a fixed half-life"], F.af.loc["non-oil GDP, base add-factors decay at a fixed half-life"]
    hl = F.af.loc["add-factor half-life (years)", "Baseline"]
    B["v22_addfactor"] = (f"real GDP {d1['Baseline']:.2f}% (baseline), {d1['Adverse']:.2f}% (adverse), {d1['Reform']:.2f}% (reform); "
                          f"non-oil {d2['Baseline']:.2f}%, {d2['Adverse']:.2f}%, {d2['Reform']:.2f}% (v2.3, half-life {hl:g} "
                          f"year{'s' if hl != 1 else ''}; constant add-factors: {F.avg_rgdp['Baseline']:.2f}% and {F.avg_non['Baseline']:.2f}%)", True)
    B["v22_hcshare"] = (f"from {F.hc25:.1f}% to {F.hc30['Baseline']:.1f}% in the baseline (v2.2: Ministry output plan; "
                        f"{F.ref['v21']['hc_share_2030_baseline']:.1f}% in v2.1)", True)
    B["v22_bands"] = (band_table(F, "en"), False)
    g0, g1 = F.gband; i0, i1 = F.iband
    B["v22_growthband"] = ((f"about {g0:.0f}% to +{g1:.0f}% a year, CPI inflation about {i0:.0f}% to\n+{i1:.0f}%").replace("-", "−"), True)
    B["v22_multipliers"] = (mult_table(F, "en"), False)
    fm = F.fm
    B["v22_fiscal"] = (f"""**Fiscal multiplier (`FR1_fiscal_multiplier.csv`).** +1 bn AZN of real state investment a year (actual injection {fm.inj:.0f} mln after the
F4 response): real non-oil GDP {pm(fm.dnon, 0)} mln (2015 prices) in 2030 — a **2030 level multiplier of {fm.lvl:.2f}**; **cumulative multiplier**
(sum of Δ non-oil GDP 2026–30 / sum of injections) **{fm.cum:.2f}** ({fm.cum_rgdp:.2f} on chain-weighted real GDP). It is larger than in the first
revision (0.54/0.46) because of the stronger income loop; imports now rise ({pm(F.mult(EXP[1], 'rm_non'))}%).""", False)
    m0 = lambda k: pm(F.mult(EXP[0], k))
    B["v22_oilprice"] = (f"""**An oil price rise lowers chain-weighted real GDP** ({m0('rgdp')}%; {pm(F.ref['v21']['brent_mult_rgdp_2030'])}% before v2.2) while raising non-oil GDP ({m0('rgdpnon')}%) and budget revenue ({m0('rev_tot_n')}%):
a higher oil price raises the mining deflator and hence mining's chain weight while mining's volume (exogenous) falls. v2.2: the
mining deflator now follows the export-value-weighted oil + gas export price index (oil is {F.A.loc[F.LAST, 'xsh_oil'] * 100:.0f}% of hydrocarbon exports in {F.LAST}),
not the Brent price in manat with a unit-like elasticity, so the weight effect — and the fall in real GDP — is smaller.""", False)
    B["v22_accounts"] = (acc_table(F, "en"), False)
    B["v22_lim10"] = (f"hold-out RMSE {S['weak'][0]:.1f}–{S['weak'][1]:.1f}%", True)
    return B


from ._fr1_tables import acc_table, band_table, mult_table, path_table, results_table, scen_table  # noqa: E402

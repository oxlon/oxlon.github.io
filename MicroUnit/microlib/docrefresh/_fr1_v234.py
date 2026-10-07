"""FR1 v2.3.3 / v2.3.4 note paragraphs (EN + AZ): exchange-rate pass-through, the 2026 CPI anchor, the import-price data
check. Figures: FR1_v23_decisions.csv, FR1_v234_g4_check.csv, FR1_doc_figures.json (devaluation, CPI nowcast), the analysis
dataset (import-price series), the forecast; the v2.3.3 results before the data check: v22_reference.json."""
from .common import az, azpm, csv, pm

SCEN = ("Baseline", "Adverse", "Reform")


def _v(F):
    g = F.docfig["v23"]["deval"]; e, n4 = g["engine"], g["engine_no_f4"]
    dec = F.dec23[F.dec23.group == "G4"].set_index("spec")
    chk = csv("FR1_v234_g4_check.csv").set_index("spec")
    yrs = [2021, 2022, 2023, 2024, 2025]
    pmm, pmd = F.A.loc[yrs, "pm_usd_infl"], F.A.loc[yrs, "pm_dsk_infl"]
    infl27 = {s: F.fc[s].loc[[2027, 2028, 2029, 2030], "infl"].mean() for s in SCEN}
    cn = g["cpi_nowcast"]; w = F.base["wage"]; w26 = (w.loc[2026] / F.A.loc[F.LAST, "wage"] - 1) * 100
    ch = chk.index[chk.chosen.astype(str) == "True"][0]
    return dict(g=g, e=e, n4=n4, dec=dec, chk=chk, pmm=pmm, pmd=pmd, infl27=infl27, cn=cn, w26=w26, ch=ch,
                old=F.ref["v23"]["v233_g4"], pre=F.ref["v23"]["pre_g4_deval"])


def g4_en(F):
    V = _v(F); g, e, n4, dec, chk, old, pre, cn = V["g"], V["e"], V["n4"], V["dec"], V["chk"], V["old"], V["pre"], V["cn"]
    r = lambda sp: ", ".join(pm(chk.loc[sp, f"resid_{y}"], 1) for y in (2023, 2024, 2025))
    ser = lambda s: ", ".join(pm(v, 1) for v in s)
    rows = "; ".join(f"{x.variant.split(': ', 1)[1]} {x.U_rw:.2f}" for _, x in dec.iterrows())
    i27 = V["infl27"]
    return f"""**v2.3.3 (2026-10-06): exchange-rate pass-through.** G4 (exchange rate + wages) had a pass-through of 0.06: a +16.5% devaluation
raised CPI {pm(pre['infl_2026'])} pp in year 1 and {pm(pre['infl_2027'])} pp in year 2, and non-oil GDP *rose* ({pm(pre['rgdpnon_2030'])}% by 2030), against ≈{g['hist_passthrough_2015_17']:.2f} in 2015–17.
Candidates (Part 11.7; lags of regressors only, no lagged inflation), inflation hold-out U vs RW (v2.3 form {dec.U_rw_v22.iloc[0]:.2f}): {rows}.
v2.3.3 adopted manat import-price inflation (macro-module USD import prices + exchange rate, current + previous year; U
{old['U_infl']:.2f}): devaluation CPI {pm(old['deval']['infl_2026'])} / {pm(old['deval']['infl_2027'])} pp, but Baseline CPI inflation 2027–30 of {old['infl_2027_30']['Baseline']:.1f}%. Why non-oil GDP rose:
with almost no pass-through real incomes barely fell, while manat oil revenue raises current spending (F3) and state investment
(F4); the real-income channel (real wage bill in E3, CPI-indexed pensions) was present but too weak.

**v2.3.4 (2026-10-06): import-price data check — G4 = exchange rate + exchange rate (t−1) + wages.** The v2.3.3 residuals of
2023–25 ({r('pm_azn_lag')} pp) came from the import-price series: USD import-price inflation 2021–25 is {ser(V['pmm'])}% in the
macro-module series but {ser(V['pmd'])}% in the workbook's DSK import-price index (`Monetar sektoru` row 98, 2021–25 only) —
opposite signs in {int((V['pmm'].values * V['pmd'].values < 0).sum())} of 5 years. (A) The DSK index spliced in for 2021–25 (macro-module growth rates to 2020, DSK
2021–25): hold-out U {chk.loc['pm_dsk_lag', 'U_rw_infl']:.2f} (macro form {chk.loc['pm_azn_lag', 'U_rw_infl']:.2f}; outside the 10% rule) and 2023–25 residuals {r('pm_dsk_lag')} pp — not removed,
reversed. The two sources cannot be reconciled, so (B) **FX + FX(t−1)** is adopted (U {chk.loc['fx_lag', 'U_rw_infl']:.2f}, +{(chk.loc['fx_lag', 'U_rw_infl'] / dec.U_rw_v22.iloc[0] - 1) * 100:.0f}% vs the v2.3 form,
within the rule; 2023–25 residuals {r('fx_lag')} pp; `FR1_v234_g4_check.csv`). The import-price forms stay registered
(`used_in_forecast = false`). Devaluation +16.5% now: CPI **{pm(e['infl'][2026])} pp in year 1, {pm(e['infl'][2027])} pp in year 2** (level {pm(e['cpi'][2030], 1)}% by
2030), non-oil GDP {pm(e['rgdpnon'][2026])}% (2026) / {pm(e['rgdpnon'][2030])}% (2030), real disposable income {pm(e['rhhdisp'][2030])}%, public debt {pm(e['debt_gdp'][2030])} pp of GDP; without the
F4 response non-oil GDP {pm(n4['rgdpnon'][2030])}%.

**2026 CPI anchor.** 2026 inflation is anchored on the latest monthly CPI, as the real sectors are on January–April:
{cn['source'].split(' (md5')[0].split('/')[-1]} gives {cn['yoy_latest']:.1f}% y/y in month {int(cn['month'])} of {int(cn['year'])}; the remaining months repeat last year's month-on-month changes (1:1;
RMSE {cn['bridge_rmse_pp']:.1f} pp on 2021–25), so December {int(cn['year'])} = {cn['infl_2026']:.1f}%. As for the January–April real-sector anchors, this partial-year
information enters as an **increment**: G4's base add-factor stays its 2025 residual ({pm(g['infl_addf_2025'], 2)} pp, held constant), and the 2026 increment
({pm(g['cpi_shift'], 2)} pp = nowcast − model) applies fully in {int(cn['year'])} and decays with the one-year half-life from 2027 (×0.5, ×0.25, …). It refreshes when a
new monthly file arrives in `data/dsk_cpi/` or a RiskUnit DSK vintage. Baseline CPI inflation 2026–30: {", ".join(f"{v:.1f}" for v in F.base.loc[[2026, 2027, 2028, 2029, 2030], "infl"])}%
(2027–30 average {i27['Baseline']:.1f}%; Adverse {i27['Adverse']:.1f}, Reform {i27['Reform']:.1f}).

{_debt_en(F)}"""


def g4_az(F):
    V = _v(F); g, e, n4, dec, chk, old, pre, cn = V["g"], V["e"], V["n4"], V["dec"], V["chk"], V["old"], V["pre"], V["cn"]
    r = lambda sp: ", ".join(azpm(chk.loc[sp, f"resid_{y}"], 1) for y in (2023, 2024, 2025))
    ser = lambda s: ", ".join(azpm(v, 1) for v in s)
    NM = {"fx_lag": "əvvəlki ilin məzənnə dəyişməsi", "pm_azn": "manatla idxal qiymətləri (cari il)", "pm_azn_lag": "manatla idxal qiymətləri (cari + əvvəlki il)",
          "fx_post15_lag": "2015-dən sonrakı rejim (cari + əvvəlki il)", "pm_dsk_lag": "manatla idxal qiymətləri, DSK ilə birləşdirilmiş"}
    rows = "; ".join(f"{NM.get(k, k)} {az(x.U_rw)}" for k, x in dec.iterrows())
    i27 = V["infl27"]
    return f"""**v2.3.3 (2026-10-06): məzənnənin ötürülməsi.** G4-də (məzənnə + əmək haqqı) ötürülmə 0,06 idi: +16,5% devalvasiya İQİ-ni 1-ci ildə
{azpm(pre['infl_2026'])} f.b., 2-ci ildə {azpm(pre['infl_2027'])} f.b. artırır, qeyri-neft ÜDM isə *artırdı* (2030-a qədər {azpm(pre['rgdpnon_2030'])}%); 2015–17-də ötürülmə ≈{az(g['hist_passthrough_2015_17'])} olub.
Namizədlər (Hissə 11.7; yalnız izahedici dəyişənlərin gecikmələri, gecikmiş inflyasiya yoxdur), inflyasiyanın təsadüfi gəzişməyə qarşı U-su (v2.3
forması {az(dec.U_rw_v22.iloc[0])}): {rows}. v2.3.3-də manatla idxal qiymətləri forması qəbul edilmişdi (makro modulun ABŞ dolları ilə idxal qiymətləri +
məzənnə, cari + əvvəlki il; U {az(old['U_infl'])}): devalvasiyada İQİ {azpm(old['deval']['infl_2026'])} / {azpm(old['deval']['infl_2027'])} f.b., lakin Əsas ssenaridə 2027–30 inflyasiyası {az(old['infl_2027_30']['Baseline'], 1)}%.
Qeyri-neft ÜDM niyə artırdı: ötürülmə demək olar ki, olmadığından real gəlirlər az azalırdı, manatla neft gəlirləri isə cari xərcləri (F3) və
dövlət investisiyasını (F4) artırır; real gəlir kanalı (E3-də real əmək haqqı fondu, İQİ-yə indeksləşən pensiyalar) mövcud idi, lakin zəif idi.

**v2.3.4 (2026-10-06): idxal qiymətləri məlumatlarının yoxlanılması — G4 = məzənnə + məzənnə (t−1) + əmək haqqı.** v2.3.3-ün 2023–25
qalıqları ({r('pm_azn_lag')} f.b.) idxal qiymətləri sırasından irəli gəlirdi: 2021–25-də ABŞ dolları ilə idxal qiymətlərinin artımı makro modulun
sırasında {ser(V['pmm'])}%, iş kitabının DSK idxal qiymətləri indeksində (`Monetar sektoru`, 98-ci sətir, yalnız 2021–25) isə {ser(V['pmd'])}%-dir —
5 ilin {int((V['pmm'].values * V['pmd'].values < 0).sum())}-də əks işarəli. (A) 2021–25 üçün DSK indeksi ilə birləşdirilmiş sıra (2020-yə qədər makro modulun artım templəri, 2021–25 DSK):
nümunədən kənar U {az(chk.loc['pm_dsk_lag', 'U_rw_infl'])} (makro forma {az(chk.loc['pm_azn_lag', 'U_rw_infl'])}; 10% qaydasından kənar), 2023–25 qalıqları {r('pm_dsk_lag')} f.b. — aradan qalxmır,
işarəsini dəyişir. İki mənbə uzlaşdırıla bilmədiyi üçün (B) **məzənnə + məzənnə (t−1)** qəbul edilib (U {az(chk.loc['fx_lag', 'U_rw_infl'])}, v2.3 formasına qarşı
+{(chk.loc['fx_lag', 'U_rw_infl'] / dec.U_rw_v22.iloc[0] - 1) * 100:.0f}%, qayda daxilində; 2023–25 qalıqları {r('fx_lag')} f.b.; `FR1_v234_g4_check.csv`). İdxal qiymətləri formaları reyestrdə qalır
(`used_in_forecast = false`). İndi +16,5% devalvasiya: İQİ **1-ci ildə {azpm(e['infl'][2026])} f.b., 2-ci ildə {azpm(e['infl'][2027])} f.b.** (2030-a qədər səviyyə {azpm(e['cpi'][2030], 1)}%),
qeyri-neft ÜDM {azpm(e['rgdpnon'][2026])}% (2026) / {azpm(e['rgdpnon'][2030])}% (2030), real sərəncamda qalan gəlir {azpm(e['rhhdisp'][2030])}%, dövlət borcu ÜDM-in {azpm(e['debt_gdp'][2030])} f.b.-i;
F4 reaksiyası olmadan qeyri-neft ÜDM {azpm(n4['rgdpnon'][2030])}%.

**2026 İQİ ankoru.** 2026 inflyasiyası, real sektorların yanvar–aprel məlumatında olduğu kimi, son aylıq İQİ-yə ankorlanır:
{cn['source'].split(' (md5')[0].split('/')[-1]} {int(cn['year'])}-ci ilin {int(cn['month'])}-ci ayı üçün illik {az(cn['yoy_latest'], 1)}% verir; qalan aylarda ötən ilin aylıq dəyişmələri təkrarlanır
(1:1; 2021–25-də RMSE {az(cn['bridge_rmse_pp'], 1)} f.b.), deməli {int(cn['year'])}-cı ilin dekabrı = {az(cn['infl_2026'], 1)}%. Real sektorların yanvar–aprel ankorlarında olduğu kimi,
bu natamam il məlumatı **əlavə (increment)** kimi daxil olur: G4-ün baza düzəliş əmsalı 2025 qalığı olaraq qalır ({azpm(g['infl_addf_2025'], 2)} f.b., sabit), 2026
əlavəsi isə ({azpm(g['cpi_shift'], 2)} f.b. = nowcast − model) {int(cn['year'])}-da tam tətbiq olunur və 2027-dən bir illik yarımsönmə ilə azalır (×0,5, ×0,25, …).
`data/dsk_cpi/`-yə yeni aylıq fayl və ya RiskUnit DSK vintajı gəldikdə yenilənir. Əsas ssenaridə 2026–30 İQİ inflyasiyası: {", ".join(az(v, 1) for v in F.base.loc[[2026, 2027, 2028, 2029, 2030], "infl"])}%
(2027–30 ortası {az(i27['Baseline'], 1)}%; Mənfi {az(i27['Adverse'], 1)}, İslahat {az(i27['Reform'], 1)}).

{_debt_az(F)}"""


def _debt(F):
    dn = F.docfig["v23"]["deval"].get("debt_nowcast")
    dg = {s: F.fc[s].loc[2030, "debt_azn"] / F.fc[s].loc[2030, "gdp_n"] * 100 for s in SCEN}
    d26 = F.base.loc[2026, "debt_azn"] / F.base.loc[2026, "gdp_n"] * 100
    return dn, dg, d26


def _debt_en(F):
    dn, dg, d26 = _debt(F)
    if not dn: return "**2026 public-debt anchor.** No 2026 Ministry of Finance stock is available; the debt identity alone is used."
    t = lambda v: f"{v:,.1f}".replace(",", " ")
    return f"""**2026 public-debt anchor (v2.3.4).** The latest Ministry of Finance stock, {t(dn['stock_azn'])} mln AZN on {dn['date']} ({pm(dn['change_since_2025_pct'], 1)}% vs
end-2025 {t(dn['debt_2025'])}; {dn['source'].split(' (md5')[0].split('/')[-1]}), anchors 2026 as CPI and the real sectors are anchored: end-2026 debt = the observed stock − the
model's 2026 budget balance × the remaining {dn['remaining_share'] * 12:.0f}/12 of the year = **{t(dn['target_2026'])} mln AZN** ({d26:.1f}% of GDP). The identity alone (debt
− balance) would give {t(dn['debt_2025'] - dn['balance_2026'])}; the gap, {pm(dn['sfa_2026'], 0)} mln AZN, is the 2026 stock-flow adjustment implied in the Baseline (repayments financed
below the line, e.g. from SOFAZ). The formula is applied inside the solver in every run (scenarios, shocks, engine), so only the
second-half balance moves end-2026 debt (Δdebt = −{dn['remaining_share']:.2f} × Δbalance): Adverse {t(F.fc['Adverse'].loc[2026].debt_azn)},
Reform {t(F.fc['Reform'].loc[2026].debt_azn)} mln AZN; from 2027 the identity applies. It refreshes when a
newer bulletin arrives in `data/minfin_debt/` or a RiskUnit MinFin vintage (`FR1_debt_nowcast.csv`). Public debt 2030: {dg['Baseline']:.1f} /
{dg['Adverse']:.1f} / {dg['Reform']:.1f}% of GDP (Baseline / Adverse / Reform)."""


def _debt_az(F):
    dn, dg, d26 = _debt(F)
    if not dn: return "**2026 dövlət borcu ankoru.** 2026 üçün Maliyyə Nazirliyinin qalıq məlumatı yoxdur; yalnız borc eyniliyi istifadə olunur."
    return f"""**2026 dövlət borcu ankoru (v2.3.4).** Maliyyə Nazirliyinin son qalıq məlumatı — {dn['date']} tarixinə {az(dn['stock_azn'], 1)} mln AZN (2025-ci ilin sonu
{az(dn['debt_2025'], 1)} ilə müqayisədə {azpm(dn['change_since_2025_pct'], 1)}%; {dn['source'].split(' (md5')[0].split('/')[-1]}) — 2026-cı ili İQİ və real sektorlar kimi ankorlayır: 2026-cı ilin sonuna
borc = müşahidə olunan qalıq − modelin 2026 büdcə balansı × ilin qalan {dn['remaining_share'] * 12:.0f}/12 hissəsi = **{az(dn['target_2026'], 1)} mln AZN** (ÜDM-in {az(d26, 1)}%-i).
Yalnız eynilik (borc − balans) {az(dn['debt_2025'] - dn['balance_2026'], 1)} verərdi; fərq, {azpm(dn['sfa_2026'], 0)} mln AZN, Əsas ssenaridə nəzərdə tutulan 2026 qalıq-axın
düzəlişidir (büdcə balansından kənar maliyyələşdirilən ödənişlər, məs. ARDNF-dən). Düstur həlledicinin daxilində hər hesablamada (ssenarilər,
şoklar, mühərrik) tətbiq olunur, ona görə 2026-cı ilin sonuna borcu yalnız ikinci yarımilin balansı dəyişir (Δborc = −{az(dn['remaining_share'], 2)} × Δbalans):
Mənfi {az(F.fc['Adverse'].loc[2026].debt_azn, 1)}, İslahat {az(F.fc['Reform'].loc[2026].debt_azn, 1)} mln AZN; 2027-dən eynilik tətbiq olunur. `data/minfin_debt/`-yə daha
yeni bülleten və ya RiskUnit MinFin vintajı gəldikdə yenilənir (`FR1_debt_nowcast.csv`). 2030 dövlət borcu: ÜDM-in {az(dg['Baseline'], 1)} / {az(dg['Adverse'], 1)} /
{az(dg['Reform'], 1)}%-i (Əsas / Mənfi / İslahat)."""

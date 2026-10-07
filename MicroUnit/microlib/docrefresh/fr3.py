"""FR3 — v2.2 note (macro-module sector / budget wages) and the §8.1, §8.2, §9 and cell-count passages, EN + AZ.

All figures come from this run's outputs: FR3_macro_module_tests.csv, FR3_equations.json, FR3_sector_wages.csv,
FR3_dsk_sector_wages_history.csv, FR3_holdout_validation.csv, FR3_forecast_tidy.csv, FR3_indicator_catalog.csv,
FR3_not_forecast.csv (and the cell count of FR3.ipynb).
"""
from .common import DOCS, Doc, az, azpm, csv, nb_counts, pm, registry, run

BY = 2024           # last DSK 4.5-4.8 year the v2.2 rules anchor on (the notebook's MM_LAST)


def texts():
    T = csv('FR3_macro_module_tests.csv'); E, J = registry('FR3')
    sel = T[T.block == 'sector relative wage: selection'].set_index('variant').RMSE_pct
    rp = E['FR3.SW_relprod_pooled']; b_rp = rp['coefficients'][0]; dm_p = rp['holdout']['dm_p_rw']
    mod = T[(T.block == 'sector wage') & T.variant.str.startswith('model')].set_index('series')
    inf = T[(T.block == 'sector wage') & T.variant.str.startswith('information: actual')].set_index('series')
    bud = T[T.block == 'budget / non-budget wage'].set_index('series')
    emp = T[T.block == 'sector employment shares'].reset_index(drop=True)
    agg = T[T.block.str.startswith('aggregate')].set_index('series')
    bl = [c for c in E['FR3.PAN_sec_emp_long']['coefficients'] if c['name'] == 'ln_gva'][0]
    SW = csv('FR3_sector_wages.csv'); H = csv('FR3_dsk_sector_wages_history.csv', index_col=0)
    HV = csv('FR3_holdout_validation.csv').set_index('variable')
    TD = csv('FR3_forecast_tidy.csv')
    w_state = float(TD[(TD.id == 'fr3:w_state') & (TD.scenario == 'ACTUAL') & (TD.year == BY)].value.iloc[0])
    RATIO = H.loc[BY, 'budget'] / w_state
    DSKGAP = float(((H.dsk_average / H.published_average - 1) * 100).abs().max())
    b30 = SW[(SW.scenario == 'Baseline') & (SW.year == 2030)].iloc[0]
    cat = csv('FR3_indicator_catalog.csv'); nf = csv('FR3_not_forecast.csv')
    SEC = ['ind', 'agr', 'con', 'trd', 'tou', 'tra', 'ict', 'oth']
    LAB = {'ind': ('Industry', 'Sənaye'), 'agr': ('Agriculture', 'Kənd təsərrüfatı'), 'con': ('Construction', 'Tikinti'),
           'trd': ('Trade', 'Ticarət'), 'tou': ('Tourism & catering', 'Turizm və ictimai iaşə'),
           'tra': ('Transport & storage', 'Nəqliyyat'), 'ict': ('ICT', 'İnformasiya və rabitə'),
           'oth': ('Social & other services', 'Sosial və digər xidmətlər'),
           'budget': ('Budget organisations', 'Büdcə təşkilatları'), 'nonbudget': ('Non-budget', 'Qeyri-büdcə')}
    g = lambda k: ((b30[k] / H.loc[BY, k]) ** (1 / (2030 - BY)) - 1) * 100
    n_used = sum(e['used_in_forecast'] for e in E.values())
    rows_en = '\n'.join(f"| {LAB[k][0]} | {H.loc[BY, k]:,.1f} | {b30[k]:,.1f} | {g(k):+.2f} |" for k in SEC + ['budget', 'nonbudget'])
    rows_az = '\n'.join(f"| {LAB[k][1]} | {az(H.loc[BY, k], 1)} | {az(b30[k], 1)} | {az(g(k))} |" for k in SEC + ['budget', 'nonbudget'])
    cur = {k: (agg.loc[k, 'current_U_rw'], agg.loc[k, 'current_U_cg']) for k in agg.index}
    azn = az
    EN = f"""## v2.2 (2026-10-05): data and approaches from the Ministry's macro module

**Data.** `data/macro_module/fr345_public_sources_panel.csv` (DSK 4.5–4.8 wages and 2.12 hired employees by 19 activities ×
state / non-state, 2005–2024; source path and MD5 in `data/macro_module/README_fr345.md`). Its state / non-state wages equal FR3's
series exactly, so **sector wages are published after all** — §8.1 and §8.2 below are superseded.

**Adopted — sector wages (8 DSK sectors) and budget / non-budget wages** (new components `fr3:sw:*`, `fr3:swg:*`, `fr3:w_budget`,
`fr3:w_nonbudget` + growth; `FR3_sector_wages.csv`, history `FR3_dsk_sector_wages_history.csv`). Rule chosen on rolling origins
2014–2016 (scored ≤ 2020): each sector keeps its relative wage of the last published year (2024); a relative-productivity driver is
worse (RMSE {sel.iloc[1]:.1f}% vs {sel.iloc[0]:.1f}%, DM p = {dm_p:.3f}; pooled β = {b_rp['coef']:+.3f}, se {b_rp['se']:.3f}) and is
registered as rejected. Sector hired weights move with FR3's sector employment; the weighted average equals FR3's average wage
(× the 2024 DSK aggregation ratio), so 2024 is reproduced exactly. Budget organisations (state units in public administration,
education, health and arts — FR4's definition; {H.loc[BY, 'budget_hired']:,.1f} thousand in 2024) keep their 2024 ratio to the state wage ({RATIO:.3f}); the
non-budget wage follows from the identity. 2025 is an estimate (DSK ends in 2024). Hold-out (cut 2020, 2021–2024) with FR3's own
simulated average wage: beats the random walk in {int((mod.U_rw < 1).sum())}/8 sectors and constant growth in {int((mod.U_cg < 1).sum())}/8 (median U
{mod.U_rw.median():.2f} / {mod.U_cg.median():.2f}) — the sector errors inherit the aggregate's {pm(HV.loc['average wage', 'err_2025'], 1)}% bias; given the actual average wage
the composition rule beats them in {int((inf.U_rw < 1).sum())}/8 and {int((inf.U_cg < 1).sum())}/8. Budget wage: U {bud.loc['budget', 'U_rw']:.2f} / {bud.loc['budget', 'U_cg']:.2f}.

| Baseline | 2024 actual | 2030 | % a year |
|---|---|---|---|
{rows_en}

Because the relative wages are held at 2024, **every sector grows at the same rate** — the average-wage growth corrected for the
shift of employment between sectors (a factor common to all sectors); there is no sector-specific wage dynamics. This is the honest
result of the pre-cut test (no sector driver beats the anchored relative wage), not a convenience choice.

**Rejected (registered, not used).** (a) Aggregate, state and private wage equations re-estimated as activity-panel growth equations
(19 activities, 2006–2020, CPI + productivity + minimum wage, no lagged dependent variable): hold-out U vs random walk / constant
growth {agg.loc['average wage', 'U_rw']:.2f}/{agg.loc['average wage', 'U_cg']:.2f} (average; current {cur['average wage'][0]:.2f}/{cur['average wage'][1]:.2f}), {agg.loc['state wage', 'U_rw']:.2f}/{agg.loc['state wage', 'U_cg']:.2f} (state; current {cur['state wage'][0]:.2f}/{cur['state wage'][1]:.2f}),
{agg.loc['private wage', 'U_rw']:.2f}/{agg.loc['private wage', 'U_cg']:.2f} (private; current {cur['private wage'][0]:.2f}/{cur['private wage'][1]:.2f}) — CPI pass-through overshoots the 2021–22 inflation spike; **no wage equation
beats constant growth**, the weakness of §6.1 remains. (b) Sector employment on the long DSK 2.12 panel (two-way FE, β = {bl['coef']:.3f},
DK se {bl['se']:.3f}): share RMSE in the 2021–2024 hold-out {emp.RMSE_pct[1]:.2f}% vs {emp.RMSE_pct[2]:.2f}% for the current DVX elasticity (constant
shares {emp.RMSE_pct[0]:.2f}%), so the current elasticity is kept. All tests: `FR3_macro_module_tests.csv`.

Registry now {len(E)} equations ({n_used} used); {len(cat)} components × 3 scenarios × 2026–2030; `FR3_not_forecast.csv`: {len(nf)} rows."""
    AZ = f"""## v2.2 (2026-10-05): Nazirliyin makro modulunun məlumatları və yanaşmaları

**Məlumat.** `data/macro_module/fr345_public_sources_panel.csv` (DSK 4.5–4.8 əmək haqları və 2.12 muzdlu işçilər, 19 fəaliyyət ×
dövlət / qeyri-dövlət, 2005–2024; mənbə yolu və MD5: `data/macro_module/README_fr345.md`). Onun dövlət / qeyri-dövlət əmək haqları
FR3-ün sıraları ilə dəqiq eynidir — deməli **sahə əmək haqları dərc olunur**; aşağıdakı §8.1 və §8.2 köhnəlib.

**Qəbul edildi — 8 sektor və büdcə / qeyri-büdcə təşkilatları üzrə əmək haqları** (yeni komponentlər `fr3:sw:*`, `fr3:swg:*`,
`fr3:w_budget`, `fr3:w_nonbudget` + artım; `FR3_sector_wages.csv`, tarix `FR3_dsk_sector_wages_history.csv`). Qayda 2014–2016
sürüşən başlanğıclarında (≤2020) seçilib: hər sektor son dərc olunmuş ilin (2024) nisbi əmək haqqını saxlayır; nisbi məhsuldarlıq
sürücüsü daha pisdir (RMSE {azn(sel.iloc[1], 1)}% və {azn(sel.iloc[0], 1)}%, DM p = {azn(dm_p, 3)}; β = {azn(b_rp['coef'], 3)}, SE {azn(b_rp['se'], 3)}) və rədd edilmiş kimi
reyestrdədir. Sektor çəkiləri FR3-ün sektor məşğulluğu ilə hərəkət edir; çəkili orta FR3-ün orta əmək haqqına bərabərdir, 2024 dəqiq
təkrarlanır. Büdcə təşkilatları (dövlət idarəetməsi, təhsil, səhiyyə, incəsənətdə dövlət müəssisələri — FR4-ün tərifi; 2024-də
{az(H.loc[BY, 'budget_hired'], 1)} min nəfər) 2024-cü ilin dövlət sektoru əmək haqqına nisbətini ({az(RATIO, 3)}) saxlayır; qeyri-büdcə əmək haqqı eynilikdən alınır.
2025 qiymətləndirmədir. Nümunədən kənar yoxlama (kəsim 2020, 2021–2024, FR3-ün öz simulyasiya edilmiş orta əmək haqqı ilə):
təsadüfi gəzişmədən {int((mod.U_rw < 1).sum())}/8, sabit artımdan {int((mod.U_cg < 1).sum())}/8 sektorda üstündür (median U {azn(mod.U_rw.median())} / {azn(mod.U_cg.median())}) —
xətalar aqreqatın {azpm(HV.loc['average wage', 'err_2025'], 1)}% meylini miras alır; faktiki orta əmək haqqı verildikdə tərkib qaydası {int((inf.U_rw < 1).sum())}/8 və {int((inf.U_cg < 1).sum())}/8.

| Əsas ssenari | 2024 faktiki | 2030 | illik % |
|---|---|---|---|
{rows_az}

Nisbi əmək haqları 2024 səviyyəsində saxlanıldığı üçün **bütün sektorlar eyni tempdə artır** — məşğulluğun sektorlar arasında
yerdəyişməsinə görə düzəldilmiş orta əmək haqqı artımı (bütün sektorlar üçün ortaq amil); sektora xas əmək haqqı dinamikası yoxdur.
Bu, ≤2020 testinin dürüst nəticəsidir (heç bir sektor sürücüsü lövbərlənmiş nisbi əmək haqqını üstələmir).

**Rədd edildi (reyestrdə, istifadə olunmur).** (a) Orta, dövlət və özəl əmək haqqı tənlikləri fəaliyyət panelində artım forması
ilə (19 fəaliyyət, 2006–2020, İQİ + məhsuldarlıq + minimum əmək haqqı, gecikmiş asılı dəyişənsiz): U (təsadüfi gəzişmə / sabit artım)
{azn(agg.loc['average wage', 'U_rw'])}/{azn(agg.loc['average wage', 'U_cg'])} (orta; cari {azn(cur['average wage'][0])}/{azn(cur['average wage'][1])}), {azn(agg.loc['state wage', 'U_rw'])}/{azn(agg.loc['state wage', 'U_cg'])} (dövlət; cari {azn(cur['state wage'][0])}/{azn(cur['state wage'][1])}),
{azn(agg.loc['private wage', 'U_rw'])}/{azn(agg.loc['private wage', 'U_cg'])} (özəl; cari {azn(cur['private wage'][0])}/{azn(cur['private wage'][1])}) — **heç bir əmək haqqı tənliyi sabit artımı üstələmir**. (b) Uzun DSK 2.12
panelində sektor məşğulluğu (iki tərəfli FE, β = {azn(bl['coef'], 3)}): pay RMSE {azn(emp.RMSE_pct[1])}% və cari elastiklik üçün {azn(emp.RMSE_pct[2])}% — cari saxlanılır.

Reyestr: {len(E)} tənlik ({n_used}-i proqnozda); {len(cat)} komponent × 3 ssenari × 2026–2030; `FR3_not_forecast.csv`: {len(nf)} sətir."""

    N, NC = nb_counts('FR3')
    bw, nbw = H.loc[BY, 'budget'], H.loc[BY, 'nonbudget']
    y0 = int(H.index.min())
    en = dict(
        v22_note=(EN, False),
        v22_s81=(f"> **v2.2: superseded.** DSK 4.5–4.8 publishes them ({y0}–{BY}); FR3 now forecasts all eight (see the v2.2 note).", False),
        v22_s82=(f"> **v2.2: superseded.** DSK 4.5–4.8 state wages in the four budget-financed activities identify them ({BY}: {bw:,.1f} vs {nbw:,.1f} AZN); forecast in v2.2.", False),
        v22_limits=(f"(v2.2) Sector and budget / non-budget wages are published only to {BY} and are forecast with relative wages held at {BY} — no sector-specific driver beats that rule.\n"
                    f"2. (v2.2) The DSK and published averages differ by up to {DSKGAP:.2f}% (hired weights); the ratio is held at {BY}.", True),
        v22_cells=(f"{N} cells, {NC} code", True))
    azd = dict(
        v22_note=(AZ, False),
        v22_s81=(f"> **v2.2: köhnəlib.** DSK 4.5–4.8 onları dərc edir ({y0}–{BY}); FR3 indi səkkiz sektorun hamısını proqnozlaşdırır (v2.2 qeydinə bax).", False),
        v22_s82=(f"> **v2.2: köhnəlib.** Dörd büdcə fəaliyyətində DSK 4.5–4.8 dövlət əmək haqları onları müəyyən edir ({BY}: {az(bw, 1)} və {az(nbw, 1)} AZN); v2.2-də proqnozlaşdırılır.", False),
        v22_limits=(f"(v2.2) Sektor və büdcə / qeyri-büdcə əmək haqları yalnız {BY}-ədək dərc olunur və {BY} nisbi əmək haqları ilə proqnozlaşdırılır — heç bir sektora xas sürücü bu qaydanı üstələmir.\n"
                    f"2. (v2.2) DSK çəkili ortası ilə dərc olunmuş orta {az(DSKGAP)}%-ədək fərqlənir; nisbət {BY} səviyyəsində saxlanılır.", True),
        v22_cells=(f"{N} xana, onlardan {NC}-i kod xanası", True))
    return en, azd


def main():
    from ._fr3_v236 import blocks as v236_blocks
    en, azd = texts()
    e6, a6 = v236_blocks()
    en.update(e6)
    azd.update(a6)
    LEG = ('<!-- AUTO:v22 -->', '<!-- /AUTO:v22 -->')

    def filler(blocks):
        def fill(d):
            for tag, (body, inline) in blocks.items():
                d.put(tag, body, inline=inline, legacy=LEG if tag == 'v22_note' else None)
        return fill
    run('FR3', [(Doc(DOCS / 'FR3_Methodology.md'), filler(en)), (Doc(DOCS / 'az' / 'FR3_Metodologiya.md'), filler(azd))])

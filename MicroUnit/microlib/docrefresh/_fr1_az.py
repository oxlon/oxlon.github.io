"""FR1 Azerbaijani v2.2 passages (docs/az/FR1_Metodologiya.md).  Each entry: tag -> (text, inline)."""
from .common import az, az_abl, az_poss, azpm, pm
from .fr1 import EXP, sp
from ._fr1_en import holdout_stats
from ._fr1_tables import acc_table, band_table, mult_table, path_table, results_table, scen_table


def az_blocks(F):
    S = holdout_stats(F); H = F.HV; n = S["n"]; r = S["r"]
    rg, rn = H.loc["real GDP"], H.loc["real non-oil GDP"]
    P, C = F.pre, F.cur
    of = lambda k: f"{az_abl(n)} {az_poss(k)}"
    B = {}
    B["v22_holdout"] = (f"""| | Nəticə ({n} dəyişən) |
|---|---|
| 2020-ci ildən (pandemiyanın dib nöqtəsi) təsadüfi gəzişməni üstələyir | {of(S['rw20'][0])}, median U **{S['rw20'][1]:.2f}** |
| 2019-cu ildən təsadüfi gəzişməni üstələyir | {of(S['rw19'][0])}, median U {S['rw19'][1]:.2f} |
| 2010–2019 sabit artımını üstələyir (pandemiyadan əvvəl) | **{of(S['cg19'][0])}, median U {S['cg19'][1]:.2f}** |
| 2010–2020 sabit artımını üstələyir | {of(S['cg20'][0])}, median U {S['cg20'][1]:.2f} |
| Statistik əhəmiyyətli üstünlüklər (HLN-DM p < 0.10) | RW2020 ilə müqayisədə {S['sig'][0]}; 2010–19 sabit artımı ilə müqayisədə {S['sig'][1]} |
| 5 ildən sonra real ÜDM səviyyəsinin xətası | **{pm(rg.err_2025, 1)}%** (RW2020 ilə müqayisədə U {rg.U_rw2020:.2f}, CG 2010–19 ilə müqayisədə {rg.U_cg1019:.2f}) |
| 5 ildən sonra real qeyri-neft ÜDM səviyyəsinin xətası | {pm(rn.err_2025, 1)}% (RW2020 ilə müqayisədə U {rn.U_rw2020:.2f}, CG 2010–19 ilə müqayisədə {rn.U_cg1019:.2f}) |
| Siyasət səviyyəsi variantı | RW2020 ilə müqayisədə median U {S['pol'][0]:.2f}, CG 2010–19 ilə müqayisədə {S['pol'][1]:.2f} |

*(v2.2 rəqəmləri: mədənçıxarma deflyatoru karbohidrogen ixrac qiymətləri indeksi üzrə — v2.2 qeydinə bax. Onun öz xətası {az(P('p_min').rmse, 1)}%-dən
{az(C('p_min').rmse, 1)}%-ə, nominal ÜDM-in xətası {az(P('gdp_n').rmse, 1)}%-dən {az(C('gdp_n').rmse, 1)}%-ə enir, real ÜDM-inki isə {az(P('rgdp').rmse, 1)}%-dən {az(C('rgdp').rmse, 1)}%-ə qalxır: 2021–22-nin daha dəqiq mədənçıxarma
qiymətləri həcmi azalan mədənçıxarmaya zəncirvari çəkidə daha böyük pay verir.)*""", False)
    e = F.cur23("rexp_cur").err_2025
    B["v22_headline62"] = (f"""**Əsas nəticə:** 2020-ci ildən təsadüfi gəzişmə modeli olduğundan yaxşı göstərir (2020-ci il pandemiyanın dib nöqtəsi idi). Pandemiyadan
əvvəlki onillik üzrə qiymətləndirilmiş sabit artımla müqayisədə model təxminən **eyni səviyyədədir** (median U {az(S['cg19'][1])}; {S['sig'][1]} statistik əhəmiyyətli
üstünlük). Yaxşı izlənilənlər: istehlak (RMSE {az(r('real consumption'), 1)}%), ticarət {az(r('trade VA'), 1)}%, məşğulluq {az(r('employment'), 1)}%, kənd təsərrüfatı {az(r('agriculture VA'), 1)}%, real ÜDM {az(r('real GDP'), 1)}%. Zəif izlənilənlər:
tikinti {az(r('construction VA'), 1)}%, nəqliyyat {az(r('transport VA'), 1)}%, emal sənayesi {az(r('manufacturing VA'), 1)}%, dövlət investisiyası {az(r('state investment'), 1)}%, İKT {az(r('ICT VA'), 1)}% (v2.1: kəsim ili olan 2020 İKT investisiyasının dib nöqtəsi idi) — 2020-ci ildən sonra transformasiyaya uğramış sektorlar
(yeni emal sənayesi gücləri, Qarabağ və Şərqi Zəngəzurun bərpası, Orta Dəhliz). Real cari xərclər 2025-ci ilədək {abs(e):.0f}% {'yüksək' if e > 0 else 'aşağı'} proqnozlaşdırılır.""", False)
    gc, gn, gi = F.g("rva_con"), F.g("rgdpnon"), F.g("rva_ict")
    B["v22_sawtooth"] = (f"{azpm(gc[2026], 1)}% (2026) →\n{azpm(gc[2027], 1)}% (2027) → {azpm(gc[2028], 1)}% (2028) dinamikası göstərir; "
                         f"qeyri-neft ÜDM {azpm(gn[2026])}% → {azpm(gn[2027])}% → {azpm(gn[2028])}%", True)
    B["v22_sawtooth_ict"] = (f"{azpm(gi[2026], 1)}% → {azpm(gi[2027], 1)}%", True)
    B["v22_sip"] = (f"təsdiq edilmiş Dövlət İnvestisiya Proqramına ({sp(F.sip)} mln AZN, `DİP 2016-2026`)", True)
    B["v22_scenarios"] = (scen_table(F, "az"), False)
    B["v22_results"] = (results_table(F, "az"), False)
    B["v22_path"] = (path_table(F, "az"), False)
    gcs = F.g("rcons")
    B["v22_whycons"] = (f"ildə {az(gcs.min(), 1)}–{az(gcs.max(), 1)}% artır", True)
    B["v22_whynonoil"] = (f"İldə {az(F.avg_non['Baseline'], 1)}% (v2.3)", True)
    B["v22_man"] = (f"ildə ~{az(F.avg('rva_man'), 1)}% artır (v2.3", True)
    B["v22_manrmse"] = (f"emal sənayesi üçün nümunədən kənar yoxlama RMSE-si {az(r('manufacturing VA'), 1)}%-dir", True)
    T = F.TS
    B["v22_trend"] = (f"({T['Transport & storage']:.0f}%), informasiya və rabitədə ({T['Information & communication']:.0f}%; v2.3), "
                      f"kənd təsərrüfatında ({T['Agriculture, forestry & fishing']:.0f}%) və elektrik enerjisində ({T['Electricity, gas & steam']:.0f}%)", True)
    d1, d2 = F.af.loc["real GDP, base add-factors decay at a fixed half-life"], F.af.loc["non-oil GDP, base add-factors decay at a fixed half-life"]
    hl = F.af.loc["add-factor half-life (years)", "Baseline"]
    B["v22_addfactor"] = (f"real ÜDM {az(d1['Baseline'])}% (Əsas), {az(d1['Adverse'])}% (Mənfi), {az(d1['Reform'])}% (İslahat); "
                          f"qeyri-neft {az(d2['Baseline'])}%, {az(d2['Adverse'])}%, {az(d2['Reform'])}% (v2.3, yarımparçalanma müddəti "
                          f"{az(hl, 0) if hl == int(hl) else az(hl)} il; sabit düzəliş əmsalları ilə: {az(F.avg_rgdp['Baseline'])}% və {az(F.avg_non['Baseline'])}%)", True)
    B["v22_hcshare"] = (f"{az(F.hc25, 1)}%-dən {az(F.hc30['Baseline'], 1)}%-ə düşür (v2.2: Nazirliyin hasilat planı; v2.1-də "
                        f"{az(F.ref['v21']['hc_share_2030_baseline'], 1)}%)", True)
    B["v22_bands"] = (band_table(F, "az"), False)
    g0, g1 = F.gband; i0, i1 = F.iband
    B["v22_growthband"] = (f"ildə təxminən −{abs(g0):.0f}%-dən +{g1:.0f}%-ə\nqədər, İQİ inflyasiyası üçün təxminən −{abs(i0):.0f}%-dən "
                           f"+{i1:.0f}%-ə qədər", True)
    B["v22_multipliers"] = (mult_table(F, "az"), False)
    fm = F.fm
    B["v22_fiscal"] = (f"""**Fiskal multiplikator (`FR1_fiscal_multiplier.csv`).** İldə +1 mlrd manat real dövlət investisiyası (F4 reaksiyasından sonra faktiki inyeksiya
{fm.inj:.0f} mln): 2030-cu ildə real qeyri-neft ÜDM {pm(fm.dnon, 0)} mln (2015-ci il qiymətləri ilə) — **2030-cu il üzrə səviyyə multiplikatoru {az(fm.lvl)}**;
**kumulyativ multiplikator** (2026–30 üzrə Δ qeyri-neft ÜDM cəmi / inyeksiyaların cəmi) **{az(fm.cum)}** (zəncirvari çəkili real ÜDM üzrə {az(fm.cum_rgdp)}). O,
birinci yenidənbaxmadakından (0,54/0,46) böyükdür, çünki gəlir dövrəsi daha güclüdür; idxal indi artır ({azpm(F.mult(EXP[1], 'rm_non'))}%).""", False)
    m0 = lambda k: azpm(F.mult(EXP[0], k))
    B["v22_oilprice"] = (f"""**Neft qiymətinin artması zəncirvari çəkili real ÜDM-i azaldır** ({m0('rgdp')}%; v2.2-dən əvvəl {azpm(F.ref['v21']['brent_mult_rgdp_2030'])}%), eyni zamanda qeyri-neft ÜDM-i ({m0('rgdpnon')}%) və büdcə gəlirlərini
({m0('rev_tot_n')}%) artırır: daha yüksək neft qiyməti mədənçıxarma deflyatorunu və deməli, mədənçıxarmanın zəncir çəkisini artırır, mədənçıxarmanın
həcmi (ekzogen) isə azalır. v2.2: mədənçıxarma deflyatoru indi ixrac dəyəri ilə çəkili neft + qaz ixrac qiymətləri indeksinə ({F.LAST}-də neft karbohidrogen ixracının {F.A.loc[F.LAST, 'xsh_oil'] * 100:.0f}%-i) bağlıdır, manatla Brent qiymətinə deyil, buna görə çəki effekti — və real ÜDM-in azalması — daha kiçikdir.""", False)
    B["v22_accounts"] = (acc_table(F, "az"), False)
    B["v22_lim10"] = (f"RMSE {az(S['weak'][0], 1)}–{az(S['weak'][1], 1)}%", True)
    return B

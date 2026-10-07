"""FR1 v2.3 passages, Azerbaijani (docs/az/FR1_Metodologiya.md): the v2.3 note and the formerly hand-written text."""
from .common import az, azpm
from ._fr1_v23_vals import FISC, LBL, mult_fix, v23_vals
from ._fr1_v23_blocks_az import blocks_az

FISC_AZ = {"F3s": "F3: qeyri-neft və neft gəlirləri ayrıca", "F3n": "F3: yalnız qeyri-neft gəlirləri (neft gəlirləri yığılır)",
           "F3c": "F3: gəlir elastikliyi 95% etibarlılıq intervalının aşağı həddində",
           "F4u": "F4: ssenari kapital xərcləri qaydası (Əsas ssenarinin siyasət səviyyəsi + F4 reaksiyası), vahid elastiklik",
           "F4c": "F4: ssenari kapital xərcləri qaydası, neft gəlirləri elastikliyi 95% intervalın aşağı həddində"}
assert set(FISC_AZ) == set(FISC) and all(k in LBL for k in FISC_AZ)


def _rows(N):
    out = []
    for k in FISC:
        r = N.dec(k)
        out.append(f"| {FISC_AZ[k]} | {azpm(r.bal_2030_Baseline)} / {azpm(r.bal_2030_Adverse)} / {azpm(r.bal_2030_Reform)} | "
                   f"{'bəli' if r.balance_order_ok else 'xeyr'} | {az(r.U_rw)} ({azpm(r.U_loss_pct, 0)}%) | rədd edilib |")
    return "\n".join(out)


def note_az(F):
    N = v23_vals(F); e3, d4 = N.e3, N.d4; g, n = N.af_dec["g"], N.af_dec["n"]; a, s = az, azpm
    du, dn, ew = N.dec("D4u"), N.dec("D4n"), N.dec("E3w")
    mb, ma, ml = N.mw["v2.2 E3"], N.mw["v2.3 E3"], N.mw["income legs (lever)"]
    fis, b22, ref = N.fis, N.ref22("bal_gdp"), N.ref22
    rev = fis["oil revenue"].difference + fis["non-oil revenue"].difference
    exp = fis["current spending"].difference + fis["capital spending"].difference + fis["debt service"].difference
    el3, el4 = N.el["F3"], N.el["F4"]; hl = a(N.hl, 0) if N.hl == int(N.hl) else a(N.hl)
    return f"""## v2.3 (2026-10-05): FR1-in yekun təmizlənməsi — sabit düzəliş əmsalı sönməsi, idxalda qiymət həddi, gəlirdə əmək haqqı fondu, fiskal sıra

Dörd spesifikasiya məsələsi: hər namizəd modelin öz builder-ləri ilə ≤2020 məlumatla qiymətləndirilib və toxunulmamış dinamik 2021–2025
nümunədən kənar yoxlamada v2.2 spesifikasiyası ilə müqayisə edilib (notebook-da yeni Hissə 11.7, `FR1_v23_candidates.csv`); ssenari nəticələri
və qərarlar Hissə 14.1-dədir (`FR1_v23_forecast_checks.csv`, `FR1_v23_fiscal_diagnosis.csv`, `FR1_v23_decisions.csv`). Qayda: hər iki nümunədə
düzgün (və ya neytral) işarələr, əsas dəyişənin Theil U-su v2.2 spesifikasiyasından ən çoxu 10% yüksək, E3 üçün uyğun əmək haqqı elastikliyi,
fiskal namizədlər üçün isə 2030 büdcə balansının Mənfi < Əsas < İslahat sırası. Rədd edilmiş namizədlər `used_in_forecast = false` ilə reyestrdədir.

| Məsələ | Qərar | Sübut |
|---|---|---|
| 1. Düzəliş əmsallarının sönməsi üzrə həssaslıq | **Dəyişdirilib.** v2.2-yə qədər `base_addf_decay` rıçağı baza düzəliş əmsallarını hər tənliyin *qiymətləndirilmiş* qalıq avtokorrelyasiyası ρ̂ ilə söndürürdü — bu, qiymətləndirilmiş qalıq-AR prosesidir və sifarişçinin məhdudiyyətləri ilə istisna olunur. İndi sabit, qiymətləndirilməyən yarımparçalanma müddəti: `addf_halflife` rıçağı (standart {hl} il, ildə {a(N.decay)} əmsalı — yanvar–aprel ankor əlavələrinin qaydası); ρ̂ proqnoz yolunun heç bir yerində qiymətləndirilmir (DW və BG diaqnostik test kimi qalır) | Proqnoz (sabit düzəliş əmsalları) bu bənddən dəyişmir. `FR1_addfactor_sensitivity.csv`, sönmə ilə 2026–30 orta artım: real ÜDM {a(g['Baseline'])} / {a(g['Adverse'])} / {a(g['Reform'])}% (Əsas / Mənfi / İslahat; sabit düzəliş əmsalları ilə {a(N.af_const['g']['Baseline'])}%), qeyri-neft {a(n['Baseline'])} / {a(n['Adverse'])} / {a(n['Reform'])}% ({a(N.af_const['n']['Baseline'])}%); ρ̂ ilə (v2.2 icrası) real ÜDM {a(N.af_rho['rgdp']['Baseline'])}%, qeyri-neft {a(N.af_rho['rgdpnon']['Baseline'])}% |
| 2. D4 qeyri-neft idxalı: nisbi qiymət ln(p_gdp/fx), əmsal {s(d4['cf_relprice'], 3)} | **Yenidən parametrləşdirilib (qəbul edilib).** Real idxal = ABŞ dolları ilə idxal × məzənnə / ÜDM deflyatoru (Hissə 3), buna görə ln(p_gdp/fx) asılı dəyişənə tərif üzrə −1 əmsalı ilə daxildir. İdxal həcmi (sabit ABŞ dolları qiymətləri) ilə ifadə edildikdə eyni qiymətləndirmə həcm elastikliyini verir: **c = {s(d4['c_full'], 3)}** (p = {a(d4['p_full'], 4)}; ≤2020: {s(d4['c_cut'], 3)}) — işarə düzgündür: real möhkəmlənmə idxal həcmini artırır. Həlledici ÜDM qiymətləri ilə real idxal üçün c − 1 istifadə edir, buna görə proqnoz və nümunədən kənar yoxlama eynidir. Həddin çıxarılması (= əmsalın 0 həddində məhdudlaşdırılması; hədd məcburidir) rədd edilib | İdxal U {a(du.U_rw)} / {a(du.U_cg)} (v2.2 ilə eyni). Hədsiz: idxal {a(dn.U_rw)} / {a(dn.U_cg)} ({s(dn.U_loss_pct, 0)}%, əhəmiyyətli itki), qeyri-neft gəlirləri U {a(N.c('D4n', 'rrev_nonoil').U_rw)} — {a(ref('rrev_nonoil').U_rw)}-ə qarşı, büdcə balansı {a(N.c('D4n', 'bal_gdp').U_rw)} — {a(b22.U_rw)}-ə qarşı. Birinci fərqlərdə həcm elastikliyi {s(d4['diff_rm'][0] + 1)} [{s(d4['diff_rm'][1] + 1)}, {s(d4['diff_rm'][2] + 1)}]-dir, uzunmüddətli qiymət bu intervaldan kənardadır — v2.2 formasında olduğu kimi (göstərilir) |
| 3. E3 ev təsərrüfatlarının gəliri: + real əmək haqqı fondu | **Qəbul edilib.** ln(gəlir / pensiya xərcləri) ln(qeyri-neft ÜDM / pensiya xərcləri) və ln(əmək haqqı fondu / pensiya xərcləri) üzrə, homogenlik qoyulub: elastikliklər qeyri-neft ÜDM {a(e3['cf_full']['ln_gdpnon'], 3)}, **real əmək haqqı fondu {a(e3['cf_full']['ln_wagebill_r'], 3)}** (2025-ci ildə əmək ödənişlərinin ev təsərrüfatlarının gəlirindəki payı {a(e3['wage_share_2025'], 3)}), pensiya xərcləri {a(e3['cf_full']['ln_pens_r'], 3)}; ≤2020: {a(e3['cf_cut']['ln_gdpnon'], 3)}, {a(e3['cf_cut']['ln_wagebill_r'], 3)}, {a(e3['cf_cut']['ln_pens_r'], 3)}. Homogenlik seçim nümunəsində rədd edilmir (p = {a(e3['homog_p_cut'])}), tam nümunədə isə rədd edilir (p = {a(e3['homog_p_full'], 3)}); orada sərbəst formada qeyri-neft ÜDM elastikliyi səhv işarəlidir ({s(e3['free_gdpnon'])}) — buna görə "yoxla və qoy" variantı rədd edilib. Əmək haqqı elastikliyi uyğundur (birinci fərqlərdə {a(e3['diff_wb'][0])} [{s(e3['diff_wb'][1])}, {s(e3['diff_wb'][2])}]) | Real sərəncamda qalan gəlir üzrə U {a(ew.U_rw)} / {a(ew.U_cg)} — {a(ew.U_rw_v22)} / {a(ew.U_cg_v22)}-ə qarşı ({s(ew.U_loss_pct, 1)}%, 10%-dən az); istehlak U {a(N.c('E3w', 'rcons').U_rw)} — {a(ref('rcons').U_rw)}-ə qarşı. **Minimum əmək haqqı +10%** (Əsas ssenari 2030, şok konvensiyası): real sərəncamda qalan gəlir {s(mb['rhhdisp'])}% → **{s(ma['rhhdisp'])}%**, istehlak {s(mb['rcons'])}% → {s(ma['rcons'])}%, qeyri-neft ÜDM {s(mb['rgdpnon'])}% → {s(ma['rgdpnon'])}% (əmək haqqı {s(ma['wage'])}%, İQİ {s(ma['cpi'])}%; gəlir ayaqları rıçağı ilə {s(ml['rhhdisp'])}%) |
| 4. Fiskal blok: Mənfi ssenari ən yaxşı büdcə balansı ilə bitir | **Saxlanılıb — heç bir namizəd keçmir.** Diaqnostika, 2030, Mənfi — Əsas: gəlirlər {s(rev/1000, 1)} mlrd AZN (neft {s(fis['oil revenue'].difference/1000, 1)}, qeyri-neft {s(fis['non-oil revenue'].difference/1000, 1)}), xərclər {s(exp/1000, 1)} mlrd (cari {s(fis['current spending'].difference/1000, 1)}, əsaslı {s(fis['capital spending'].difference/1000, 1)}): **itirilən hər manat gəlirə {a(N.cut_per_azn)} manat xərc azalması düşür**. Bunu iki əlaqə yaradır: F3 (cari xərclər ümumi real gəlirlər üzrə, elastiklik {a(el3.Baseline)}, 95% interval [{a(el3.difference)}, {a(el3.pct)}]) və ssenarilərin dövlət investisiyası yolları (Mənfi ildə −4%: real dövlət investisiyası {s(N.oil_vs_inv.Adverse, 1)}%, real neft gəlirləri {s(N.oil_vs_inv.difference, 1)}%; F4 vahid elastiklik, sərbəst qiymət {a(el4.Adverse)} [{a(el4.difference)}, {a(el4.pct)}]). Əsas ssenarinin dövlət investisiyası səviyyəsi ilə Mənfi ssenari ÜDM-in {s(N.adv_istate.Adverse)}%-i ilə bitərdi | Sıranı bərpa edən hər struktur düzəliş nümunədən kənar balans xətasında ciddi itirir (v2.2-də U {a(b22.U_rw)}, RMSE ÜDM-in {a(b22.rmse, 1)} f.b.-i) — aşağıdakı cədvəl. Deməli, sıra qiymətləndirilmiş fiskal reaksiyanın xassəsidir (xərclər gəlirləri, əsaslı xərclər neft gəlirlərini izləyir), kod xətası deyil; o, gizlədilmir, açıqlanır |

| Fiskal namizəd (v2.2 modelində, nümunədən kənar yoxlamada olduğu kimi) | 2030 balansı, ÜDM-ə nisbətdə % (Əsas / Mənfi / İslahat) | Mənfi < Əsas < İslahat | Balansın nümunədən kənar U-su (dəyişmə) | Qərar |
|---|---|---|---|---|
{_rows(N)}

**Proqnoza təsir (Əsas ssenari 2030, v2.2 icrası ilə müqayisədə)** — hamısı E3-ün əmək haqqı fondu həddindən irəli gəlir (1-ci və 2-ci bəndlər
proqnozu dəyişmir): real ÜDM {s(N.d30['rgdp'])}%, qeyri-neft ÜDM {s(N.d30['rgdpnon'])}%, nominal ÜDM {s(N.d30['gdp_n'])}%, İQİ {s(N.d30['cpi'])}%, real sərəncamda qalan gəlir
{s(N.d30['rhhdisp'])}%, istehlak {s(N.d30['rcons'])}%, qeyri-neft idxalı {s(N.d30['rm_non'])}%: proqnozda real əmək haqqı fondu qeyri-neft
ÜDM-dən yavaş artır. 2026–30 orta artım: real ÜDM **{a(N.avg['g']['Baseline'])}%** (v2.2 {a(N.avg22['g']['Baseline'])}; Mənfi
{a(N.avg['g']['Adverse'])}, İslahat {a(N.avg['g']['Reform'])}), qeyri-neft **{a(N.avg['n']['Baseline'])}%** ({a(N.avg22['n']['Baseline'])}; {a(N.avg['n']['Adverse'])}, {a(N.avg['n']['Reform'])}). 2030 büdcə balansı: Əsas {s(N.bal['Baseline'])}, Mənfi
{s(N.bal['Adverse'])}, İslahat {s(N.bal['Reform'])}% (ÜDM-ə nisbətdə; v2.2 {s(N.bal22['Baseline'])} / {s(N.bal22['Adverse'])} / {s(N.bal22['Reform'])}). §6.2-nin 14 dəyişəni üzrə median U: təsadüfi gəzişməyə
qarşı {a(N.med.U_rw, 3)} (v2.2-də {a(N.med22.U_rw, 3)}), sabit artıma qarşı {a(N.med.U_cg, 3)} ({a(N.med22.U_cg, 3)}).

**Reyestr, mühərrik, sənədləşmə.** `FR1_equations.json`: {N.neq} tənlik (proqnozda {N.nused}; v2.2-də {N.neq22}), yeni: {N.nrej} v2.3 spesifikasiyası
(D4 və E3-ün əvəz olunmuş v2.2 formaları və rədd edilmiş namizədlər), hər biri nümunədən kənar müqayisəsi və qərar sətri ilə. Mühərrik:
`addf_halflife` rıçağı; E3 homogenlik bağı indi üç üzvlüdür (pensiya xərcləri elastikliyi = 1 − qeyri-neft ÜDM − əmək haqqı fondu), buna
görə dəyişdirilmiş əmsal məhdudiyyəti saxlayır; öz-özünü yoxlama hər ssenari üzrə hər iki rejimdə keçir. Heç bir CSV-də olmayan icradan asılı
rəqəmlər (§7.1 həlledici iterasiyaları, §7.2 yanvar–aprel ankoru, §7.5 yelpik diaqnostikası, v2.2 müqayisə rəqəmləri) `FR1_doc_figures.json`-a
(Hissə 18.17) ixrac olunur və burada `microlib.docrefresh` ilə yaradılır. FR3, FR4 və FR5 v2.3 proqnozu ilə yenidən icra olunub. §6–§9 v2.3
icrasına istinad edir.

{_mfix_az(F)}

{_dfix_az(F)}

{_g4fix_az(F)}"""


def _mfix_az(F):
    from .fr1 import EXP
    m = mult_fix(F); p = lambda e: ", ".join(azpm(v, 0) for v in m["path"][e].tolist())
    old = ", ".join(azpm(v, 0) for v in m["old"])
    return f"""**v2.3.1 düzəlişi (2026-10-06): büdcə balansı multiplikatorları.** `FR1_multipliers.csv` büdcə balansını sıfırdan keçən Əsas
ssenari balansından (2028-ci ildə {azpm(m['b28'], 0)} mln AZN) faiz kənarlaşması kimi verirdi, buna görə reaksiyalar partlayır və işarəsini
dəyişirdi (dövlət investisiyası +1 mlrd AZN: 2026–30-da {old} "%"; v2.2-də 2028-ci ildə +{az(m['old22'], 0)}%). Modelin özü səhv deyildi:
hər şok həlli yığılıb (ən böyük qalıq {m['conv']:.0e}), pul ifadəsində reaksiyalar isə hamardır. Balans sütunu indi cari qiymətlərlə mln
AZN fərqidir (inflyasiya f.b.-də, digər sütunlar %-lə qalır): dövlət investisiyası +1 mlrd AZN {p(EXP[1])}; Brent +10 ABŞ dolları/barel
{p(EXP[0])}; xarici tələb +10% {p(EXP[4])}. Real və qiymət reaksiyaları və proqnoz dəyişmir. Notebook indi hər şok həllinin yığıldığını və
balance_n, rgdpnon və infl reaksiyalarının 2-ci ildən sonra işarəsini dəyişmədiyini yoxlayır (assert).""".replace("e-", "e−")


def v23_az(F):
    B = {"v23_note": (note_az(F), False)}
    B.update(blocks_az(F))
    return B


def _dfix_az(F):
    from ._fr1_v23_vals import SCEN
    pre = F.ref["v23"]["pre_debt_fix"]; d = F.docfig["v23"]; y5 = d["debt"][str(F.LAST)]
    cur = {s: (F.fc[s].loc[2030, "debt_azn"] / F.fc[s].loc[2030, "gdp_n"] * 100, F.fc[s].loc[2030, "balance_n"] / F.fc[s].loc[2030, "gdp_n"] * 100)
           for s in SCEN}
    ds = F.base.loc[2026, "debt_serv_n"]
    return f"""**v2.3.2 düzəlişi (2026-10-06): dövlət borcu.** `debt_azn` iş kitabındakı ümumi dövlət borcunu məzənnə ilə çevirirdi, lakin bu
sətir üç fərqli əsasdadır (§2.3, 5-ci bənd): {F.LAST}-ci il {az(d['debt_old_2025'], 0)} mln AZN idi, düzgün dəyər isə **{az(y5['external x FX + domestic (mln AZN)'], 1)} mln AZN**-dir (xarici
{az(y5['external, mln USD'], 1)} mln ABŞ dolları × {az(y5['FX end-year'], 2)} + daxili {az(y5['domestic, mln AZN'], 1)} mln AZN; ÜDM-in {az(d['debt_gdp_2025'], 1)}%-i); 2010–2020 isə məzənnə qədər təhrif olunmuşdu.
Dövlət borcu indi hər il xarici borc × ilin sonuna məzənnə + daxili borc kimi hesablanır — Maliyyə Nazirliyinin anlayışı (dövlət zəmanətli
borc daxil deyil və iş kitabında yoxdur); `fr1:debt_azn` müvafiq adlandırılıb. Kalibrlənmiş borc xidməti dərəcəsi (2023–25 üzrə borc xidməti
/ borc ortası) və borc eyniliyi düzəldilmiş qalıqdan istifadə edir: 2026 borc xidməti {az(ds, 0)} mln AZN (əvvəl {az(pre['Baseline']['debt_serv_2026'], 0)});
2030 dövlət borcu ÜDM-in {az(cur['Baseline'][0], 1)} / {az(cur['Adverse'][0], 1)} / {az(cur['Reform'][0], 1)}%-i (Əsas / Mənfi / İslahat; əvvəl {az(pre['Baseline']['debt_gdp_2030'], 1)} /
{az(pre['Adverse']['debt_gdp_2030'], 1)} / {az(pre['Reform']['debt_gdp_2030'], 1)}); 2030 büdcə balansı {azpm(cur['Baseline'][1])} / {azpm(cur['Adverse'][1])} / {azpm(cur['Reform'][1])}% (əvvəl {azpm(pre['Baseline']['bal_gdp_2030'])} / {azpm(pre['Adverse']['bal_gdp_2030'])} / {azpm(pre['Reform']['bal_gdp_2030'])})."""


def _g4fix_az(F):
    from ._fr1_v23_vals import SCEN
    g = F.docfig["v23"]["deval"]; e, n4 = g["engine"], g["engine_no_f4"]; v0 = F.ref["v23"]["pre_g4_deval"]
    dec = F.dec23[F.dec23.group == "G4"].set_index("spec")
    NM = {"fx_lag": "əvvəlki ilin məzənnə dəyişməsi", "pm_azn": "manatla idxal qiymətləri (cari il)",
          "pm_azn_lag": "manatla idxal qiymətləri (cari + əvvəlki il)", "fx_post15_lag": "2015-dən sonrakı rejim (cari + əvvəlki il)"}
    rows = "; ".join(f"{NM[k]} {az(r.U_rw)} ({azpm(r.U_loss_pct, 0)}%)" for k, r in dec.iterrows())
    infl27 = {s: F.fc[s].loc[[2027, 2028, 2029, 2030], "infl"].mean() for s in SCEN}
    cn = g["cpi_nowcast"]; w = F.base["wage"]; cn_w26 = (w.loc[2026] / F.A.loc[F.LAST, "wage"] - 1) * 100
    return f"""**v2.3.3 (2026-10-06): məzənnənin ötürülməsi.** G4-də ötürülmə 0,06 idi (+16,5% devalvasiya: İQİ 1-ci ildə {azpm(v0['infl_2026'])} f.b., 2-ci ildə
{azpm(v0['infl_2027'])} f.b., qeyri-neft ÜDM isə 2030-a qədər {azpm(v0['rgdpnon_2030'])}% *artırdı*); 2015–17-də ötürülmə ≈{az(g['hist_passthrough_2015_17'])} olub. Namizədlər (Hissə 11.7; yalnız
izahedici dəyişənlərin gecikmələri, gecikmiş inflyasiya yoxdur), inflyasiyanın təsadüfi gəzişməyə qarşı nümunədən kənar U-su (v2.2 forması
{az(dec.U_rw_v22.iloc[0])}): {rows}. **Qəbul edilib: manatla idxal qiymətləri, cari + əvvəlki il** (ən böyük qazanc; işarələr düzgün; 2015-dən sonrakı rejim
forması daha yaxşı deyil). İndi +16,5% devalvasiya: İQİ **1-ci ildə {azpm(e['infl'][2026])} f.b., 2-ci ildə {azpm(e['infl'][2027])} f.b.** (2030-a qədər İQİ səviyyəsi {azpm(e['cpi'][2030], 1)}%),
qeyri-neft ÜDM 2026-da {azpm(e['rgdpnon'][2026])}%, 2030-da {azpm(e['rgdpnon'][2030])}%, real sərəncamda qalan gəlir {azpm(e['rhhdisp'][2030])}%, istehlak {azpm(e['rcons'][2030])}%, dövlət borcu ÜDM-in
{azpm(e['debt_gdp'][2030])} f.b.-i. Qeyri-neft ÜDM əvvəl niyə artırdı: ötürülmə demək olar ki, olmadığından real gəlirlər az azalırdı, manatla neft gəlirləri
({azpm(e['rev_oil_n'][2030], 1)}%) isə cari xərcləri (F3) və dövlət investisiyasını (F4, {azpm(e['rinv_state'][2030], 1)}%) artırır; real gəlir kanalı (E3-də real əmək haqqı fondu,
İQİ-yə indeksləşən pensiyalar) mövcud idi, lakin çox zəif idi. F4 reaksiyası olmadan qeyri-neft ÜDM {azpm(n4['rgdpnon'][2030])}% azalardı. **2026 İQİ ankoru və Əsas ssenari.** 2026 inflyasiyası, real
sektorların yanvar–aprel məlumatında olduğu kimi, son aylıq İQİ-yə ankorlanır: {cn['source'].split(' (md5')[0].split('/')[-1]} {int(cn['year'])}-ci ilin {int(cn['month'])}-ci ayı üçün illik {az(cn['yoy_latest'], 1)}% verir;
qalan aylarda ötən ilin aylıq dəyişmələri təkrarlanır (1:1; 2021–25-də bu körpünün RMSE-si {az(cn['bridge_rmse_pp'], 1)} f.b.), deməli {int(cn['year'])}-cı ilin dekabrı = {az(cn['infl_2026'], 1)}%.
G4-ün düzəliş əmsalı Əsas ssenaridə {int(cn['year'])} inflyasiyası nowcast-a bərabər olacaq şəkildə seçilir (2025 qalığı {azpm(g['infl_addf_2025'], 2)} f.b. + ankor
sürüşməsi {azpm(g['cpi_shift'], 2)} f.b.) və 2027-dən sabit saxlanılır; `data/dsk_cpi/`-yə yeni aylıq fayl və ya RiskUnit DSK vintajı gəldikdə nowcast
yenilənir. Modelin öz 2026 dəyəri nowcast-a artıq yaxın idi, buna görə ankor az dəyişir: Əsas ssenaridə 2027–30 İQİ inflyasiyası orta hesabla
{az(infl27['Baseline'], 1)}%-dir (Mənfi {az(infl27['Adverse'], 1)}, İslahat {az(infl27['Reform'], 1)}) — əmək haqqı artımı 2026-da yanvar–aprel ankoru ilə {az(cn_w26, 1)}%-dən təxminən 8%-ə qayıdır,
düzəliş əmsalı isə birdəfəlik deyil (2023–24 qalıqları da eyni ölçüdədir, makro modulun sırasında ABŞ dolları ilə idxal qiymətləri düşür). İdxal qiymətləri yolu redaktə edilə bilən fərziyyədir (`pm_usd_infl`)."""


def _g4fix_az(F):                    # v2.3.4: supersedes the v2.3.3 version above
    from ._fr1_v234 import g4_az
    from ._fr1_v235 import v235_az
    return g4_az(F) + "\n\n" + v235_az(F) + "\n\n" + __import__('microlib.docrefresh._fr1_v236', fromlist=['x']).v236_az(F)

"""FR1 v2.3 passages, Azerbaijani (docs/az/FR1_Metodologiya.md): the v2.3 note and the formerly hand-written text."""
from .common import az, azpm
from ._fr1_v23_vals import FISC, LBL, v23_vals
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
icrasına istinad edir."""


def v23_az(F):
    B = {"v23_note": (note_az(F), False)}
    B.update(blocks_az(F))
    return B

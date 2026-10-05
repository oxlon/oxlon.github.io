"""FR1 v2.2 note (AZ) — the same figures as _fr1_note.note_en, Azerbaijani number format."""
from .common import az, az_poss, azpm
from .fr1 import sp


def note_az(F):
    from ._fr1_note import vals
    N = vals(F); L = N.legs; g = N.g5; m, mp = N.med, N.med_pre
    a, s = az, azpm
    return f"""## v2.2 (2026-10-05): Nazirliyin makro modulundan (15.5.1) nə götürülüb

Makro modul (`18august/model`, yalnız oxunur) FR1–FR5-i makro tərəfdən əhatə edir. Onun məlumatları və rəsmi plan rəqəmləri FR1 üçün
nəzərdən keçirilib; hər namizəd **FR1-in öz çərçivəsində yenidən qiymətləndirilib** (eyni nümunə qaydaları, kiçik nümunə HAC, uyğunluq
qaydası), ≤2020 məlumatla seçilib və §6.2-nin **toxunulmamış dinamik 2021–2025 nümunədən kənar yoxlamasında** v2.2-dən əvvəlki modellə
müqayisə olunub (notebook-un yeni Hissə 11.6-sı, `FR1_v22_macro_candidates.csv`). Məlumat surətləri, mənbə yolu və MD5:
`data/macro_module/README_FR1.md`. Makro modulun öz proqnozlaşdırmasından (AR(1)/beşillik orta profillər, İQİ/əmək haqqı/işsizlik
ansamblları, ECM/AR(6) spesifikasiyaları, Okun tənliyi, 2026 yanvar–aprel faktiki göstəricilərini nəzərə almayan 2026 ÜDM yolu) heç nə
istifadə olunmur.

| Bənd | Qərar | Nümunədən kənar yoxlama (Theil U təsadüfi gəzişməyə 2020 / sabit artıma 2010–19 qarşı; RMSE) |
|---|---|---|
| 1. Neft və qaz hasilatı | **Qəbul edilib** (fərziyyə): Əsas ssenari 2027–30 = Nazirliyin planının artım tempi (`8_vereq_original.xlsx`, 2.4.1.4), yanvar–mart faktiki göstəricisindən 2026 səviyyəsinə tətbiq olunur; Mənfi = v2.2-dən əvvəlki Əsas ssenarinin neft azalması (−4,2…−3,0%), qaz plan − 1 f.b.; İslahat = plan + v2.2-dən əvvəlki İslahat fərqləri | Plan qiymətləndirmə deyil. Plan 2025-ci il neft hasilatını artıq göstərib ({a(N.plan_oil)} əvəzinə {a(N.act_oil)} mln ton, {s(N.err_oil, 1)}%; qaz {s(N.err_gas, 1)}%). Əsas ssenaridə 2030 neft hasilatı: {a(N.oil30, 1)} mln ton (əvvəl {a(N.oil30_21, 1)}) |
| 2. Gəlirin mənbələr üzrə bölgüsü (əmək haqqı fondu + DSMF transfertləri + digər gəlirlər, Δln ayaqları) | Proqnoz üçün **rədd edilib**; mühərrik rıçağı `income_block = legs` | Nümunədaxili ayaqlar daha yaxşıdır (≤2020 real gəlir artımının bir addımlıq RMSE-si {a(N.onestep[0], 1)} və {a(N.onestep[1], 1)} f.b.; elastikliklər {a(N.el[0])} əmək haqqı fondu, {a(N.el[1])} DSMF, {a(N.el[2])} digər gəlirlər — makro modulda olduğu kimi). Dinamik yoxlamada real sərəncamda qalan gəlir: U {a(L.U_rw)} / {a(L.U_cg)}, RMSE {a(L.rmse, 1)}% — **{a(L.U_rw_pre)} / {a(L.U_cg_pre)}, {a(L.rmse_pre, 1)}%**-ə qarşı; istehlak {a(N.legs_c.U_rw)} — {a(N.legs_c.U_rw_pre)}-ə qarşı. Ayaqlar nominaldır: kəsimdən əvvəlki model 2025 qiymət səviyyəsini {N.price30:.0f}% aşağı proqnozlaşdırır, tam indeksləşməyən nominal ayaqlar bunu artıq real gəlirə çevirir. İstehlak qiymətləri ilə deflyasiya edilmiş forma: {a(N.legs_r.U_rw)} / {a(N.legs_r.U_cg)} (rədd edilib). Nominal sərəncamda qalan gəlir ayaqlarla daha yaxşıdır (U {a(N.legs_n.U_rw)} — {a(N.legs_n.U_rw_pre)}-ə qarşı) |
| 3. Mədənçıxarma deflyatoru ixrac dəyəri ilə çəkili neft+qaz ixrac qiymətləri indeksi + məzənnə üzrə | **Qəbul edilib** (makro modulun forması, İQİ həddi olmadan) | Mədənçıxarma deflyatoru U **{a(g['p_min'].U_rw)} / {a(g['p_min'].U_cg)}** (RMSE {a(g['p_min'].rmse, 1)}%) — {a(g['p_min'].U_rw_pre)} / {a(g['p_min'].U_cg_pre)} ({a(g['p_min'].rmse_pre, 1)}%)-ə qarşı; nominal ÜDM {a(g['gdp_n'].U_rw)} / {a(g['gdp_n'].U_cg)} — {a(g['gdp_n'].U_rw_pre)} / {a(g['gdp_n'].U_cg_pre)}-ya qarşı; ÜDM deflyatoru {a(g['p_gdp'].U_rw)} — {a(g['p_gdp'].U_rw_pre)}-ə qarşı. Yan təsirlər: real ÜDM {a(g['rgdp'].U_rw)} / {a(g['rgdp'].U_cg)} — {a(g['rgdp'].U_rw_pre)} / {a(g['rgdp'].U_cg_pre)}-ya qarşı (zəncirvari çəkilər), idxal {a(N.imp_cur)} — {a(N.imp_pre)}-ya qarşı (D4-də yanlış işarəli nisbi qiymət). İQİ əlavə olunmuş variant (≤2020 ən kiçik standart xəta) daha pisdir ({a(N.g5c)}) və rədd edilib. Yeni tənlik: {a(N.fit[0], 1)} + {a(N.fit[1])} Δln XPI + {a(N.fit[2])} Δln FX, düzəldilmiş R² {a(N.r2a)}; dayanıqlıq *{N.verdict}* ({N.chow['break_year']} orta nöqtəsində Chow, p = {a(N.chow['p'], 3)}) |
| 4. 2026 Dövlət İnvestisiya Proqramı | **Qəbul edilib**: {sp(N.sip)} mln AZN (öz iş kitabı, `DİP 2016-2026`, nəzərdə tutulmuş vəsait; 2025 faktiki {sp(N.sip25)}; makro modul eyni xanaya istinad edir) | Fərziyyə. Proqramın 2025-ci ildə real dövlət investisiyasındakı payı ({a(N.sipsh, 1)}%) 2026-da modelin öz 2026 investisiya deflyatoru ilə proqramla əvəz olunur (tərpənməz nöqtə); 2026 real dövlət investisiyası {s(N.ist26, 1)}% (əvvəl {s(N.ist26_21, 1)}%). `fr1:exp_pubinv_n` kimi dərc olunur (hər ssenaridə 2026 = {sp(N.sip)}) |
| 5. Fiskal qapanma: qeyri-neft balansı / qeyri-neft ÜDM kəsim ilinin səviyyəsində | **Rədd edilib**; mühərrik rıçağı `fiscal_rule = nobd`; nisbət dərc olunur (`fr1:nobd_pct`) | Ümumi xərclər yaxşılaşır (U {a(N.f_exp.U_rw)} — {a(N.f_exp.U_rw_pre)}-ə qarşı), lakin qaydanın məqsədi olan büdcə balansı xeyli pisləşir: RMSE ÜDM-in {a(N.f_bal.rmse, 1)} f.b.-i — {a(N.f_bal.rmse_pre, 1)}-ə qarşı (U {a(N.f_bal.U_rw)} — {a(N.f_bal.U_rw_pre)}-ə qarşı), çünki neft gəlirlərinin xətaları balansa 1:1 keçir. F3 ilə Mənfi ssenari 2030-da ən yaxşı balansı saxlayır (ÜDM-in {s(N.bal30['Adverse'], 1)}%-i; Əsas {s(N.bal30['Baseline'], 1)}, İslahat {s(N.bal30['Reform'], 1)}): xərclər gəlirləri izləyir və Mənfi ssenari dövlət investisiyasını ildə 4% azaldır. Rıçaqla 2030 balansları {s(N.lever['Baseline'], 1)} / {s(N.lever['Adverse'], 1)} / {s(N.lever['Reform'], 1)} mlrd AZN-dir (Mənfi ən pis) |
| 6. İdxal udma + real effektiv məzənnə üzrə | **Rədd edilib** | REER hər iki nümunədə yanlış işarəlidir (≤2020 {s(N.reer20[0])}, p = {a(N.reer20[1])}; tam {s(N.reer['coef'])}, p = {a(N.reer['p'])}); idxal U {a(N.d4.U_rw)} / {a(N.d4.U_cg)} — {a(N.d4.U_rw_pre)} / {a(N.d4.U_cg_pre)}-ə qarşı. D4 dəyişməyib |
| 7. Sektor deflyatorları sektor qiymət sürücüləri üzrə | **Buraxılıb** | Sürücülərin (kənd təsərrüfatı istehsalçı qiymətləri, nəqliyyat və rabitə tarifləri, tikinti deflyatoru) 2026–30 üçün ekzogen yolu yoxdur: makro modul onları AR/orta profillərlə proqnozlaşdırır (`pdrv_*`), bir neçəsi yalnız 2021-dən mövcuddur |

**Proqnoza təsiri (Əsas ssenari, v2.1-ə nisbətən).** 2026 real göstəricilərdə dəyişmir (yanvar–aprel ilə ankorlanıb); dəyişikliklər
2027-dən başlayır: 2030 real ÜDM {s(N.d30['rgdp'], 1)}% (neft-qaz ÜDM {s(N.d30['rgdpoil'], 1)}%), qeyri-neft ÜDM {s(N.d30['rgdpnon'], 1)}%, nominal ÜDM {s(N.d30['gdp_n'], 1)}% (mədənçıxarma deflyatoru), 2030 İQİ
{s(N.d30['cpi'], 1)}%, real sərəncamda qalan gəlir {s(N.d30['rhhdisp'], 1)}%. 2026–30 orta artım: real ÜDM **{a(N.avg_g['Baseline'])}%** (v2.1 {a(N.avg_g21)}; Mənfi {a(N.avg_g['Adverse'])}, İslahat {a(N.avg_g['Reform'])}), qeyri-neft **{a(N.avg_n['Baseline'])}%**
({a(N.avg_n21)}; {a(N.avg_n['Adverse'])}, {a(N.avg_n['Reform'])}). Fəallıq üzrə ssenari sırası dəyişməyib (Mənfi < Əsas < İslahat). 2030 büdcə balansı ÜDM-in {s(N.bal30['Baseline'])}%-i (Əsas); 2026
balansı aşağıdır ({s(N.bal26_21, 0)} əvəzinə {s(N.bal26, 0)} mln AZN: proqram). §6.2-nin 14 dəyişəni üzrə median U: təsadüfi gəzişməyə qarşı {a(m.U_rw)} (əvvəl {a(mp.U_rw)}),
sabit artıma qarşı {a(m.U_cg)} ({a(mp.U_cg)}); median RMSE {a(m.rmse, 1)}% ({a(mp.rmse, 1)}%).

**Reyestr və mühərrik.** `FR1_equations.json`: {N.neq} tənlik ({az_poss(N.nused)} proqnozda): yeni — gəlirin dörd ayağı (E3a–E3d, qiymətləndirilib və
reyestrdədir, `used_in_forecast = false`, nümunədən kənar müqayisəsi ilə), onların İQİ ilə deflyasiya edilmiş variantları, v2.2-dən əvvəlki
və İQİ əlavə olunmuş mədənçıxarma deflyatorları, udma + REER ilə D4; G5_defl_min əvəz olunub. Mühərrik (`microlib/engines/fr1.py`,
`_fr1_*.py`): yeni girişlər `sip_n` (proqram, nominal) və `dsmf_add_g`; rıçaqlar `income_block`, `fiscal_rule`; yeni sıralar
`fr1:gdpnon_n`, `hhdisp_n`, `nobd_pct`, `exp_pubinv_n`, `gas_exp_price`, `xsh_oil`, `dln_xpi` (kataloqda {N.ncat} komponent).
`income_block = legs` ilə minimum əmək haqqının 10% artması 2030-a qədər real sərəncamda qalan gəliri ~{a(N.mw[0], 1)}% artırır; proqnoz modelində
(E3) artırmır ({s(N.mw[1])}%, qiymətlər vasitəsilə). Öz-özünü yoxlama bütün ssenarilər üzrə hər iki rejimdə keçir; FR3, FR4 və FR5 yenidən icra
olunub. Bu qeyd v2.2 mərhələsini qeyd edir (proqnoz rəqəmləri v2.2 icrasınındır; v2 və v2.1 qeydləri də öz icralarının rəqəmlərini
saxlayır); §6–§9 cari (v2.3) icraya istinad edir."""

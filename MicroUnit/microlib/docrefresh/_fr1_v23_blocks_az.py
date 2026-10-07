"""FR1 run-dependent passages that were hand-written until v2.3 (AZ): §3.3 E3, §7.1, §7.2, §7.5, §9 item 17."""
from .common import az, az_poss, azpm
from ._fr1_v23_blocks_en import frac, ict_dec

ANCH_AZ = {"manufacturing": "emal sənayesi", "construction": "tikinti", "agriculture": "kənd təsərrüfatı", "trade": "ticarət",
           "transport": "nəqliyyat", "ICT": "informasiya və rabitə", "tourism": "turizm", "electricity": "elektrik enerjisi",
           "consumer market": "istehlak bazarı", "mining": "mədənçıxarma", "oil-gas GDP": "neft-qaz ÜDM",
           "other services": "digər xidmətlər", "water": "su təchizatı", "net taxes": "xalis vergilər"}
FANV = {"rgdp": "real ÜDM", "rgdpnon": "qeyri-neft", "rcons": "istehlak", "rhhdisp": "gəlir", "rexp_cur": "cari xərclər",
        "rev_tot_n": "büdcə gəlirləri"}


def sh(x):
    return f"{az(x * 100, 1)}%"


def blocks_az(F):
    d = F.docfig; S, A, Fn = d["solver"], d["nowcast"], d["fan"]; e3 = d["v23"]["e3"]; cf, cc = e3["cf_full"], e3["cf_cut"]
    from ._fr1_v23_vals import code_cells_before_part18
    B = {"v23_cells": (f"Hissə 1–17 = {code_cells_before_part18()} kod xanası", True)}
    B["v23_e3"] = (f"""- **Ev təsərrüfatlarının gəliri (E3)** — pay əlaqəsi (v2.3: real əmək haqqı fondu ilə): ln(gəlir / pensiya xərcləri) ln(qeyri-neft ÜDM /
  pensiya xərcləri) və ln(əmək haqqı fondu / pensiya xərcləri) üzrə; elastikliklər qeyri-neft ÜDM üzrə {az(cf['ln_gdpnon'])}, real əmək haqqı fondu
  (orta əmək haqqı × məşğulluq / istehlak qiymətləri; 2025-ci ildə əmək ödənişlərinin ev təsərrüfatlarının gəlirindəki payı {az(e3['wage_share_2025'])}) üzrə
  {az(cf['ln_wagebill_r'])}, pensiya xərcləri üzrə {az(cf['ln_pens_r'])} (homogenlik qoyulub: ≤2020 məlumatla rədd edilmir, p = {az(e3['homog_p_cut'])}; tam nümunədə rədd
  edilir, p = {az(e3['homog_p_full'], 3)}, orada sərbəst formada qeyri-neft ÜDM həddi səhv işarəlidir). Qeyri-neft ÜDM qalan bazar gəlirlərini (sahibkarlıq
  və mülkiyyət gəlirləri), əmək haqqı fondu isə əmək haqqı və minimum əmək haqqı kanalını təmsil edir. Pensiya xərcləri **proksidir**: orta
  pensiya × ümumi əhali (iş kitabında pensiyaçıların sayı yoxdur). Pensiyalar siyasət dəyişənidir və proqnozda İQİ-yə indeksləşdirilir.""", False)
    db = d["v23"]["debt"]; y5 = db[str(F.LAST)]; y0 = db["2020"]; y4 = db["2024"]; old = d["v23"]["debt_old_2025"]
    B["v23_debt"] = (f"""5. **Dövlət borcu (v2.3.2)** — iş kitabındakı cəm ('Ümumi dövlət borcu', `Fiskal sektor` 22-ci sətir, mln ABŞ dolları kimi
   işarələnib) üç fərqli əsasdadır: 2010–2020-də mln AZN-lə (2020: {az(y0['total (row 22)'], 1)} = xarici {az(y0['external, mln USD'], 1)} mln ABŞ dolları × {az(y0['FX end-year'], 4)} + daxili
   {az(y0['domestic, mln AZN'], 1)} mln AZN), 2021–2024-də mln ABŞ dolları ilə (2024: {az(y4['total (row 22)'], 1)}), {F.LAST}-ci ildə isə çevrilmədən toplanmış
   {az(y5['total (row 22)'], 1)} = {az(y5['external, mln USD'], 1)} (ABŞ dolları) + {az(y5['domestic, mln AZN'], 1)} (AZN). Bütün sətrin məzənnə ilə çevrilməsi {F.LAST} üçün {az(old, 0)} mln AZN
   verir, 2010–2020-ni isə məzənnə qədər təhrif edirdi (2010-da ×{az(float(F.A.loc[2010, 'fx']), 2)}, 2020-də ×{az(y0['FX end-year'], 2)}). Dövlət borcu indi hər il xarici borc (24-cü sətir) × ilin sonuna məzənnə + daxili
   borc (23-cü sətir) kimi hesablanır — Maliyyə Nazirliyinin anlayışı, dövlət zəmanətli borc daxil deyil: **{F.LAST}-ci ildə
   {az(y5['external x FX + domestic (mln AZN)'], 1)} mln AZN (ÜDM-in {az(d['v23']['debt_gdp_2025'], 1)}%-i)**. Üç əsas notebook-da yoxlanılır (assert).""", False)
    g4 = d["v23"]["deval"]; cf4, p4 = g4["g4_cf"], g4["g4_p"]
    if "dln_fx_L1" in cf4:
        B["v23_g4"] = (f"""- **İnflyasiya** — struktur xərc əlavəsi (v2.3.4): cari ildə məzənnə dəyişməsi ({az(cf4['dln_fx'], 3)}, p = {az(p4['dln_fx'])}) və əvvəlki ildə məzənnə
  dəyişməsi ({az(cf4['dln_fx_L1'], 3)}, p = {az(p4['dln_fx_L1'], 3)}; izahedici dəyişənin gecikməsi, gecikmiş inflyasiya yoxdur) və əmək haqqı artımı ({az(cf4['dln_wage'], 3)}, p = {az(p4['dln_wage'])});
  R² {az(g4['g4_r2'])}. Məzənnənin məcmu ötürülməsi {az(cf4['dln_fx'] + cf4['dln_fx_L1'])} (2015–17 tarixi: {az(g4['hist_passthrough_2015_17'])}); idxal qiymətləri formaları çıxarılıb, çünki
  iki idxal qiyməti mənbəyi 2021–25-də bir-birinə ziddir (v2.3.4 qeydi).""", False)
    else:
        B["v23_g4"] = (f"""- **İnflyasiya** — struktur xərc əlavəsi (v2.3.3): idxal qiymətlərinin manatla artımı (ABŞ dolları ilə idxal qiymətləri + məzənnə) cari
      ildə ({az(cf4['dln_pm_azn'], 3)}, p = {az(p4['dln_pm_azn'], 3)}) və əvvəlki ildə ({az(cf4['dln_pm_azn_L1'], 3)}, p = {az(p4['dln_pm_azn_L1'])}; izahedici dəyişənin gecikməsi, gecikmiş
      inflyasiya yoxdur) və əmək haqqı artımı ({az(cf4['dln_wage'], 3)}, p = {az(p4['dln_wage'])}); R² {az(g4['g4_r2'])}. Məzənnənin məcmu ötürülməsi {az(cf4['dln_pm_azn'] + cf4['dln_pm_azn_L1'])}
      (2015–17 tarixi: {az(g4['hist_passthrough_2015_17'])}). ABŞ dolları ilə idxal qiymətləri baza fərziyyəsidir (ildə 0%, giriş `pm_usd_infl`).""", False)
    B["v23_solver"] = (f"{S['forecast_iter'][0]}–{S['forecast_iter'][1]}\niterasiya, nümunədən kənar yoxlamada "
                       f"{S['holdout_iter'][0]}–{S['holdout_iter'][1]}", True)
    li = A["largest_increment"]; beat = A["choice"] != "1:1 mapping"
    ch = "dayanıqlı körpü" if beat else "1:1 uyğunluq"
    B["v23_anchor"] = (f"""2026-cı il üzrə dörd aylıq müşahidə mövcuddur. ÜDM-in on iki komponentinin hamısı üzrə ilin əvvəlindən hesablanmış real artım indeksləri
dərc olunmuşdur. Yanvar–aprel artımından tam il artımına dayanıqlı (Huber) proporsional körpü 2022–2025 üzrə qiymətləndirilmişdir (2021
istisna edilib: onun yanvar–aprel artımı 2020-ci ilin baza effektidir); onun meyl əmsalı {az(A['bridge_slope'])}, çarpaz yoxlanılmış RMSE-si isə 1:1 uyğunluq
üçün {az(A['one2one_cv_rmse'], 1)} f.b.-yə qarşı {az(A['bridge_cv_rmse'], 1)} f.b.-dir, lakin HLN düzəlişli Diebold–Mariano testində (birtərəfli p = {az(A['bridge_dm_p'], 3)}) 1:1 uyğunluğu
**{'üstələyir' if beat else 'üstələmir'}**, buna görə də **{ch}** istifadə olunur. Hər komponentin nəzərdə tutulan tam il səviyyəsi düzəliş əmsalı
əlavələri (increments) vasitəsilə çatılan lövbərləmə hədəfidir; **əlavələr 2026-cı ildə tam tətbiq olunur və hər il yarıbayarı azalır**
(2030-cu ildə {frac(A['anchor_remaining_2030'])} hissəsi qalır). Ən böyüyü {ANCH_AZ.get(li['label'], li['label'])} komponentinə aiddir ({azpm(li['value'], 3)} loqarifmik bənd,
yanvar–aprel artımının {azpm(li['ytd_growth'], 0)}% olmasından irəli gəlir).""", False)
    ga = F.g("rva_agr")
    B["v23_agr"] = (f"{azpm(ga[2026], 1)}% → {azpm(ga[2027], 1)}%", True)
    a26, a27, k27 = ict_dec(F)
    B["v23_ict"] = (f"yanvar–aprel lövbəri 2026-cı ildə {az(a26, 1)} f.b. əlavə edir, 2027-ci ildə {az(abs(a27), 1)} f.b. geri alır, adambaşına İKT "
                    f"kapitalı isə 2025-ci ilin investisiya payı ilə artıq artmır (2027-ci ildə {azpm(k27, 1)} f.b.", True)
    rows = "\n".join(f"| {'Real ÜDM artımı' if t['variable'] == 'real GDP' else 'Real qeyri-neft ÜDM artımı'} | {azpm(t['published_ytd'])}% | "
                     f"{azpm(t['model_2026'])}% | {azpm(t['diff_pp'])} f.b. |" for t in A["table"])
    B["v23_jantable"] = ("| | Dərc olunmuş yanvar–aprel | Model 2026 (tam il) | Fərq |\n|---|---|---|---|\n" + rows, False)
    fl = Fn["fail"]; sg = Fn["share_gt03"]; mg = Fn["medgap_raw_2030"]
    gaps = ", ".join(f"{azpm(mg[k], 1)}% ({v})" for k, v in FANV.items())
    gap_max = f"{Fn['medgap_after_max']:.0e}".replace("-", "−")
    B["v23_fan"] = (f"""Əsas ssenari üzrə {Fn['nsim']} təkrarlama aşağıdakıları birləşdirir: (1) **qalıq trayektoriyalarının tarixi təkrar seçimi (resampling)** — başlanğıc
ili s ({Fn['start_years'][0]}–{Fn['start_years'][1]}) çəkilir və bütün {Fn['n_resid']} davranış qalığının birgə kənarlaşmaları u_{{s+h}} − u_s (h = 1…5) sabit düzəliş əmsallarına əlavə olunur;
qalıq dinamikası üzrə heç nə qiymətləndirilmir; trayektoriyalar mərkəzləşdirilir və hər iki işarə ilə istifadə olunur (antitetik); (2) log
Brent, neft və qaz hasilatı üçün eyni beşillik tarix, **eyni başlanğıc ili ilə**; (3) N(β̂, V̂_HAC)-dan antitetik, işarəni qoruyan parametr
çəkilişləri (əmsal çəkilişlərinin {sh(Fn['param_rej_share'])}-i işarə dəyişməsinə görə rədd edilmişdir), baza düzəliş əmsalları isə 2025-ci ili təkrarlamaq üçün
yenidən hesablanır. 2026 kənarlaşmaları {az(Fn['nowcast_scale'])} (yanvar–aprel məlum olduqdan sonra qalan tam il qeyri-müəyyənliyi), ekzogen amillər üçün isə
{frac(Fn['exo_scale'])} ilə miqyaslanır.

**Diaqnostika.** {Fn['valid']} etibarlı təkrarlama ({sh(Fn['valid_share'])}) əldə etmək üçün {Fn['attempts']} təkrarlamaya ({Fn['pairs']} antitetik cüt) cəhd edilmişdir. Kənarlaşdırılmışdır:
{az_poss(fl.get('year-on-year jump above ceiling', 0))} bir illik dəyişikliyin Əsas ssenarinin müvafiq dəyişikliyindən {az(Fn['jump_max'], 1)} loqarifmik bənddən çox fərqlənməsinə görə (və ya, daha böyük olduğu
hallarda, dəyişənin 2000–2025-ci illərdə etdiyi ən böyük dəyişikliyin 1,5 mislindən çox — məsələn, turizm, dövlət investisiyası, neftlə bağlı
qiymətlər), {az_poss(fl.get('non-finite', 0))} sonlu olmayan qiymətlərə görə, {az_poss(fl.get('explosive (>50% from baseline)', 0))} partlayıcı dinamikaya görə, {az_poss(fl.get('non-convergence', 0))} yığılmamağa görə (uğursuz üzv öz antitetik
cütünü də kənarlaşdırır). Buna görə də bu filtr quyruqları müəyyən qədər kəsir. İxrac edilmiş çəkilişlərdə |Δlog| > 0,3 olan çəkiliş-illərin payı
real ÜDM üçün {az(sg['rgdp'], 1)}%, qeyri-neft ÜDM üçün {az(sg['rgdpnon'], 1)}%, İQİ üçün {az(sg['cpi'], 1)}%, məşğulluq üçün {az(sg['emp'], 1)}%, istehlak üçün {az(sg['rcons'], 1)}%, real cari xərclər
üçün {az(sg['rexp_cur'], 1)}% və qeyri-neft investisiyası üçün {az(sg['rinv_non'], 0)}%-dir (onun öz tarixində dəyişikliklər daha böyükdür).

**Mərkəzləşdirmə.** Şoklar və parametr kənarlaşmaları simmetrikdir, lakin aqreqatlar log-normal şoklara məruz qalan hissələrin hesabi
cəmləridir (zəncirvari ÜDM, neft + qeyri-neft büdcə gəlirləri, gəlir dövrəsi), buna görə də xam median Əsas ssenaridən yuxarıda yerləşir:
2030-cu ilədək {gaps}. Daha sonra ixrac edilmiş çəkilişlər Əsas ssenari üzrə mərkəzləşdirilir (səviyyələr üçün multiplikativ, dərəcələr üçün
additiv şəkildə): median hər il dərc edilmiş Əsas ssenariyə bərabərdir (maksimal fərq {gap_max}), səpələnmə dəyişmir; dəyişənlərarası eyniliklər
yalnız bu sürüşmələr dəqiqliyi ilə ödənilir.""", False)
    B["v23_lim17"] = (f"""17. **Yelpiklər** İQİ, istehlak və cari xərclər üçün genişdir, sıçrayışların süzgəcdən keçirilməsi ilə kəsilir (cəhd edilmiş təkrarlamaların
    {sh(Fn['jump_fail_share'])}-i rədd edilir, antitetik cütləri ilə birlikdə {sh(Fn['replaced_share'])}-i əvəz olunur), İQİ üzrə güzgü əksi şəklində deflyasiya quyruğuna
    malikdir və göstərilən median düzəlişindən sonra Əsas ssenari ətrafında mərkəzləşdirilir.""", False)
    return B

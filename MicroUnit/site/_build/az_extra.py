"""az_extra.py — the site's own English → Azerbaijani table for strings the module outputs still
carry in English (registry titles, estimator descriptions, notes). Applied at build time after the
modules' *_strings_az.csv tables. FULL: whole-string translations; FRAG: fragment replacements
(applied longest first, on word boundaries)."""

FULL = {
    "chosen on rolling origins <= 2020 (Part 9.2); the D18 dummy passed the break test but could not be scored out "
    "of sample (not estimable before 2018), so the baseline uses the scored specification without it; the D18 version "
    "is a sensitivity Seçim: prod_non + mw (sürüşən başlanğıclar, ≤2020).":
    "Sürüşən başlanğıclarla (≤ 2020) seçilib (9.2-ci hissə); D18 süni dəyişəni qırılma testindən keçdi, lakin onu "
    "nümunədən kənar qiymətləndirmək mümkün olmadı (2018-dən əvvəl qiymətləndirilə bilmir), ona görə Əsas ssenari "
    "qiymətləndirilmiş spesifikasiyanı D18-siz istifadə edir; D18 variantı həssaslıq yoxlamasıdır. Seçim: prod_non + mw "
    "(sürüşən başlanğıclar, ≤2020).",
    "chosen on rolling origins <= 2020 (Part 9.2); long-run homogeneity IMPOSED on theory grounds although rejected on "
    "this short sample: with a sum of price elasticities c != 1 the real wage would drift by (c-1) x inflation every "
    "year forever (money illusion). The rejection reflects episodes such as the 2021-22 inflation spike, when nominal "
    "pay lagged prices, and the 2018 floor reform. The unrestricted version is a sensitivity Seçim: prod_non "
    "(sürüşən başlanğıclar, ≤2020).":
    "Sürüşən başlanğıclarla (≤ 2020) seçilib (9.2-ci hissə); uzunmüddətli homogenlik bu qısa nümunədə rədd edilsə də, "
    "nəzəri əsasla TƏTBİQ EDİLİB: qiymət elastiklikləri cəmi c ≠ 1 olduqda real əmək haqqı hər il (c − 1) × inflyasiya "
    "qədər sonsuz sürüşərdi (pul illüziyası). Rədd 2021–22 inflyasiya sıçrayışı (nominal əmək haqqı qiymətlərdən geri "
    "qaldı) və 2018 minimum əmək haqqı islahatı kimi epizodları əks etdirir. Məhdudiyyətsiz variant həssaslıq "
    "yoxlamasıdır. Seçim: prod_non (sürüşən başlanğıclar, ≤2020).",
    "Seçim: income + relative price — simplest coherent non-inferior level specification (pəncərələr ≤2019). "
    "η = 1.155, ε = -0.182. Kointeqrasiya müəyyən edilməyib: t-statistikaları təsviri xarakterlidir. η diapazonu 1.15–1.67.":
    "Seçim: gəlir + nisbi qiymət — ən sadə, uyğun və etalondan geri qalmayan səviyyə spesifikasiyası (pəncərələr ≤2019). "
    "η = 1.155, ε = -0.182. Kointeqrasiya müəyyən edilməyib: t-statistikaları təsviri xarakterlidir. η diapazonu 1.15–1.67.",
    "(a) entry counts": "(a) girişlərin sayı", "(c) Boone slope": "(c) Boone meyli",
    "(d) SCP, (e) mobility": "(d) struktur–davranış–nəticə, (e) mobillik",
    "static levels regression (y on const + long-run regressors)":
    "statik səviyyə reqressiyası (y — sabit və uzunmüddətli izahedici dəyişənlər üzrə)",
    "estimated regression": "qiymətləndirilmiş reqressiyanın özü",
    "2015-2025 (not comparable across years)": "2015–2025 (illər arasında müqayisə olunmur)",
    "SYNTHETIC only": "yalnız SİNTETİK",
    "15 files, e.g. ['FR12_FIRM_concentration_nace.csv', 'FR12_FIRM_concentration_nace_region.csv', 'FR12_FIRM_econ_boone_sector_year.csv']; econometrics: 12 models, 262 coefficients = SYNTHETIC run, no wa":
    "15 fayl, məsələn ['FR12_FIRM_concentration_nace.csv', 'FR12_FIRM_concentration_nace_region.csv', 'FR12_FIRM_econ_boone_sector_year.csv']; ekonometrika: 12 model, 262 əmsal = SİNTETİK icra ilə eyni, su nişanı yoxdur",
    "small": "kiçik", "large": "böyük", "state": "dövlət",
    "pp of share": "payın faiz bəndi",
    "posterior s.e. after shrinkage": "büzülmədən sonrakı posterior standart xəta",
    "nominal branch output, log-%": "sahənin nominal buraxılışı, log-%",
    "calibrated (no s.e.)": "kalibrlənmiş (standart xəta yoxdur)",
    "sample mean, SE = sd/sqrt(n)": "nümunə ortası, standart xəta = sd/√n",
}

FRAG = [
    ('long-run homogeneity IMPOSED on theory grounds although rejected on this short sample: with a sum of price elasticities c != 1 the real wage would drift by (c-1) x inflation every year forever (money illusion). The rejection reflects episodes such as the 2021-22 inflation spike, when nominal pay lagged prices, and the 2019 floor reform. The unrestricted version is a sensitivity',
     'uzunmüddətli homogenlik nəzəri əsaslarla TƏTBİQ EDİLİB, baxmayaraq ki, bu qısa nümunədə rədd olunur: qiymət elastikliklərinin cəmi c ≠ 1 olduqda real əmək haqqı hər il (c−1) × inflyasiya qədər sonsuzadək sürüşərdi (pul illüziyası). Rədd edilmə 2021–22 inflyasiya sıçrayışı (nominal əmək haqqı qiymətlərdən geri qaldıqda) və 2019 minimum əmək haqqı islahatı kimi epizodları əks etdirir. Məhdudiyyətsiz versiya həssaslıq variantıdır'),
    ('the D18 dummy passed the break test but could not be scored out of sample (not estimable before 2019), so the baseline uses the scored specification without it; the D18 version is a sensitivity',
     'D18 süni dəyişəni (2019) qırılma testindən keçdi, lakin nümunədən kənar qiymətləndirilə bilmədi (2019-dan əvvəl qiymətləndirilə bilmir), buna görə baza yolu onsuz qiymətləndirilmiş spesifikasiyadan istifadə edir; D18 versiyası həssaslıq variantıdır'),
    ('chosen on rolling origins <= 2020 (Part 9.2); ', 'sürüşən başlanğıclar üzrə seçilib (≤ 2020, 9.2-ci hissə); '),
    # FR1
    ("K + construction + exports", "K + tikinti + ixrac"),
    ("K + construction + agriculture", "K + tikinti + kənd təsərrüfatı"),
    ("production function, freely estimated", "istehsal funksiyası, sərbəst qiymətləndirilib"),
    ("production function, panel factor shares imposed", "istehsal funksiyası, panel amil payları tətbiq edilib"),
    ("on projected regressors", "proyeksiya edilmiş izahedici dəyişənlər üzrə"),
    # FR3
    ("diff-form", "fərq forması"), ("with D18", "D18 ilə"),
    ("(a) pass", "(a) keçir"), ("(b) pass", "(b) keçir"), ("(a) FAIL", "(a) KEÇMİR"), ("(b) FAIL", "(b) KEÇMİR"),
    ("Rıçaq uyğunluğu: level", "Rıçaq uyğunluğu: səviyyə"), ("qaydasından KEÇMİR: level", "qaydasından KEÇMİR: səviyyə"),
    ("notebook-un estimate_lr funksiyası", "dəftərin estimate_lr funksiyası"),
    ("hold-out blokundadır", "nümunədən kənar yoxlama blokundadır"),
    ("Part 15", "15-ci hissə"), ("Part 9.2", "9.2-ci hissə"), ("(Part 8)", "(8-ci hissə)"),
    ("Nəticə: not established", "Nəticə: müəyyən edilməyib"),
    ("BETWEEN (sahə ortaları)", "sahələrarası (sahə ortaları)"),
    ("BETWEEN (region ortaları)", "regionlararası (region ortaları)"),
    ("seasonal-ratio nowcast (calibrated mean)", "mövsümi nisbət üzrə cari qiymətləndirmə (kalibrlənmiş orta)"),
    ("sample mean, SE = sd/sqrt(n)", "nümunə ortası, standart xəta = sd/√n"),
    # FR4
    ("real state investment per capita", "adambaşına real dövlət investisiyası"),
    ("real total expenditure per capita", "adambaşına real ümumi xərclər"),
    ("real value added of other services", "digər xidmətlərin real əlavə dəyəri"),
    ("real GDP per capita", "adambaşına real ÜDM"),
    ("calibrated (mean of DSK tables 2.12-2.13)", "kalibrlənmiş (DSK-nın 2.12–2.13 cədvəllərinin ortası)"),
    ("calibrated (DVX r130 / all hired, 2022-2024)", "kalibrlənmiş (DVX r130 / bütün muzdlu işçilər, 2022–2024)"),
    # FR5
    ("Tier 1 namizədi: income only", "1-ci pillə namizədi: yalnız gəlir"),
    ("Tier 1 namizədi: trend only", "1-ci pillə namizədi: yalnız trend"),
    ("income deflated by service price", "xidmət qiyməti ilə deflyasiya edilmiş gəlir"),
    ("Tier 1 namizədi: income + trend", "1-ci pillə namizədi: gəlir + trend"),
    ("Tier 1 namizədi", "1-ci pillə namizədi"),
    ("difference-form slope (level slope outside its difference-form CI); shrunk",
     "fərq formasının meyli (səviyyə meyli fərq formasının etibarlılıq intervalından kənardadır); büzülmüş"),
    # FR10
    ("SYNTHETIC — pipeline test, not results", "SİNTETİK — boru xəttinin sınağı, nəticə deyil"),
    ("seçilən sistem — constant shares", "seçilən sistem — sabit paylar"),
    ("Leather and footwear", "Dəri və ayaqqabı"), ("Rubber and plastics", "Rezin və plastik kütlə"),
    ("Computer and electronics", "Kompüter və elektronika"), ("Machinery and equipment", "Maşın və avadanlıq"),
    ("Other transport equipment", "Digər nəqliyyat vasitələri"), ("Other manufacturing", "Digər hazır məmulatlar"),
    ("Repair and installation", "Maşın və avadanlığın təmiri və quraşdırılması"),
    ("Other mining and quarrying", "Digər faydalı qazıntılar"),
    ("Mining support services", "Mədənçıxarma sahəsində xidmətlər"),
    ("Crude oil and natural gas", "Xam neft və təbii qaz"),
    ("Sahələr arası (between) qiymətləndirici", "Sahələrarası qiymətləndirici"),
    ("Calibrated rule: anchored null, real output constant at the last actual level",
     "Kalibrlənmiş qayda: ankerlənmiş sıfır model, real buraxılış son faktiki səviyyədə sabit"),
    ("Calibrated rule: unit elasticity, chosen pre-cut", "Kalibrlənmiş qayda: vahid elastiklik, kəsimdən əvvəl seçilib"),
    ("FE-twoway (branch + year), within", "ikitərəfli sabit effektlər (sahə + il), daxili qiymətləndirici"),
    ("FE-oneway (branch), first differences", "birtərəfli sabit effektlər (sahə), birinci fərqlər"),
    ("FE-oneway (branch), levels", "birtərəfli sabit effektlər (sahə), səviyyələr"),
    ("Two-way fixed effects (firm + year), firm-demeaned", "ikitərəfli sabit effektlər (müəssisə + il), müəssisə ortası çıxılıb"),
    ("Pooled LS + NACE x year fixed effects", "birləşdirilmiş ƏKK + NACE × il sabit effektləri"),
    ("Pooled LS + NACE and year dummies", "birləşdirilmiş ƏKK + NACE və il süni dəyişənləri"),
    ("Logit (MLE), dummies nace2 + year", "Logit (MLE), süni dəyişənlər: nace2 + il"),
    ("Logit (MLE), dummies year", "Logit (MLE), il süni dəyişənləri"),
    ("MNL log-odds share system, empirical-Bayes shrinkage (kappa=0.5)",
     "MNL log-nisbət pay sistemi, empirik Bayes büzülməsi (kappa=0.5)"),
    ("empirical Bayes (precision-weighted) shrinkage, kappa chosen pre-cut",
     "empirik Bayes büzülməsi (dəqiqliklə çəkilmiş), κ kəsim ilindən əvvəlki məlumatla seçilib"),
    ('(DSK 4.5-4.8 relative sector wages, 2024)', '(DSK 4.5–4.8, sahələrin nisbi əmək haqları, 2024)'),
    ('(DSK 4.5-4.8 state wages, 4 budget-financed activities, 2024)', '(DSK 4.5–4.8, dövlət sektorunda əmək haqları, büdcədən maliyyələşən 4 fəaliyyət növü, 2024)'),
    ('(DSK Dynamics_2.12, last published year)', '(DSK Dynamics_2.12, son dərc olunmuş il)'),
    ('(Ministry MOE SOCIAL.xlsx eq8, published coefficients)', '(Nazirliyin MOE SOCIAL.xlsx eq8 tənliyi, dərc olunmuş əmsallar)'),
    ("calibrated allocation (constant observed shares)", "kalibrlənmiş bölgü (müşahidə edilmiş sabit paylar)"),
    ("forecast combination (equal weights)", "proqnozların birləşdirilməsi (bərabər çəkilər)"),
    ("klaster(firm)", "klaster (müəssisə)"), ("cluster(firm)", "klaster (müəssisə)"),
    # FR12
    ("FE-oneway (unit), Driscoll-Kraay", "birtərəfli sabit effektlər (vahid), Driscoll-Kraay"),
    ("null (FE + fixed terms)", "sıfır model (sabit effektlər + sabit hədlər)"),
    ("unit means (FE only)", "vahid ortaları (yalnız sabit effektlər)"),
    ("combination: FE + non | anchored", "kombinasiya: sabit effektlər + non | ankerlənmiş"),
    ("— FE + non + lend", "— sabit effektlər + non + lend"), ("— FE + non", "— sabit effektlər + non"),
    ('"restrictions" bölməsindədir', "«məhdudiyyətlər» bölməsindədir"),
    ("ICT (Information & communication)", "ICT (informasiya və rabitə)"),
    ("Layer-A size-class bounds", "A qatı ölçü sinfi hədləri"),
    ("Mobile telecommunications (3 operators)", "Mobil rabitə (3 operator)"),
    ("(ASSUMPTION: 3 operators, subscriber shares ≈ 50-55 / 25-30 / 20% (approximate public reports) -> HHI 3,300-4,000)",
     "(FƏRZİYYƏ: 3 operator, abunəçi payları ≈ 50–55 / 25–30 / 20% (təxmini, açıq hesabatlar) → HHI 3,300–4,000)"),
    ("CON (Construction)", "CON (tikinti)"), ("Banking (assets)", "Bank sektoru (aktivlər)"),
    ("(ASSUMPTION: ~22 banks, top-5 ≈ 60% of assets (approximate, CBAR annual reports) -> HHI 800-1,300; "
     "replace with CBAR concentration data)",
     "(FƏRZİYYƏ: ~22 bank, ən böyük 5-i aktivlərin ≈ 60%-i (təxmini, AMB-nin illik hesabatları) → HHI 800–1,300; "
     "AMB-nin konsentrasiya məlumatı ilə əvəz edilməlidir)"),
    ("IND (Industry)", "IND (sənaye)"), ("Cement (domestic producers)", "Sement (yerli istehsalçılar)"),
    ("(ASSUMPTION: 2-3 domestic integrated producers plus imports (approximate) -> domestic HHI 3,500-5,500)",
     "(FƏRZİYYƏ: 2–3 yerli inteqrasiya olunmuş istehsalçı və idxal (təxmini) → yerli HHI 3,500–5,500)"),
    ("new: RMSE", "yeni: RMSE"), ("stock: RMSE", "ehtiyat: RMSE"),
    ("least squares, section/year dummies, cluster(division)", "ən kiçik kvadratlar, bölmə və il süni dəyişənləri, klaster (sinif)"),
    ("least squares, section/year dummies, klaster(division)", "ən kiçik kvadratlar, bölmə və il süni dəyişənləri, klaster (sinif)"),
    ("least squares, year dummies, cluster(division)", "ən kiçik kvadratlar, il süni dəyişənləri, klaster (sinif)"),
    ("least squares, year dummies, klaster(division)", "ən kiçik kvadratlar, il süni dəyişənləri, klaster (sinif)"),
    ("WLS, absorbed bölmə × il × ölçü qrupu effects", "WLS, bölmə × il × ölçü qrupu effektləri çıxılmaqla"),
    ("WLS, absorbed bölmə × il effects", "WLS, bölmə × il effektləri çıxılmaqla"),
    ("WLS, absorbed il effects", "WLS, il effektləri çıxılmaqla"),
    ("WLS per section-year (HC0), cross-section", "WLS, hər bölmə-il üzrə (HC0), məkan kəsiyi"),
    ("non-oil GDP", "qeyri-neft ÜDM"), ("notebook-un", "dəftərin"), ("wild bootstrap", "vəhşi bootstrap"),
    ("(Part 10, R9)", "(10-cu hissə, R9)"), ("Part 12.5:", "12.5-ci hissə:"),
    ("identity (Tornqvist shift-share decomposition)", "eynilik (Törnqvist shift-share bölgüsü)"),
    ("Non-metallic minerals", "Qeyri-metal mineral məhsullar"),
    ("calibrated allocation (observed half-year ratio)", "kalibrlənmiş bölgü (müşahidə edilmiş yarımillik nisbət)"),
    ("conditional ML, cell-year strata (Hausman-Hall-Griliches)",
     "şərti maksimum həqiqətəbənzərlik, xana-il təbəqələri (Hausman–Hall–Griliches)"),
    ("cluster-robust Wald", "klasterə davamlı Wald"),
    ("sample mean,", "nümunə ortası,"),
    ("workbook 'Regionlar*' rows", "iş kitabı, 'Regionlar*' vərəqlərinin sətirləri"),
    ("sətri 'of which:' kimi adlanıb", "sətri «o cümlədən:» kimi adlanıb"),
    ("eyni, no watermark", "eyni, su nişanı yoxdur"), ("Crude oil and natural", "Xam neft və təbii"),
    ("real dövlət investisiyaları per capita", "adambaşına real dövlət investisiyaları"), (" per capita", " (adambaşına)"),
    ("[1] Standard Errors are robust to klaster correlation (klaster)",
     "[1] Standart xətalar klaster daxilində korrelyasiyaya davamlıdır"),
]

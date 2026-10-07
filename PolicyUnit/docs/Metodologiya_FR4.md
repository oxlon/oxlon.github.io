# FR4 — risklər, yan təsirlər və azaldıcı tədbirlər (MİİS §15.5.4) — metodologiya

**Tələb:** «İqtisadi siyasətlərin və tədbirlərin tətbiqi nəticəsində yaranan risklərin və yan təsirlərin təhlili, risklərin
azaldılması və yan təsirlərin idarə edilməsi üçün tədbirlərin planlaşdırılması». **Texniki həll:** siyasət simulyasiyası
nəticələrinin risk idarəetmə modulu (RiskUnit, §15.5.3) ilə inteqrasiyası, yan təsir ssenarilərinin avtomatik generasiyası.
**Qəbul meyarı:** hər siyasət ssenarisi üçün sistem potensial yan təsirlərin siyahısını və müvafiq azaldıcı tədbir
təkliflərini formalaşdırır → `output/P4_side_effects.csv` + `output/P4_mitigation.csv` (hər ssenari üçün).

Mərhələ: `python3 run_all.py --only fr4.side_effects,fr4.kpi_refresh [--scenario <id>]` (core.scenarios-dan sonra).
Modullar: `policyunit/side_effects.py` (qaydalar, yan təsir ssenariləri), `risk_link.py` (RiskUnit HTTP), `sensitivity.py`
(Monte Karlo, Sobol), `stage_fr4.py`. Konfiqurasiya: `config/side_effect_rules.csv`, `config/mitigation_map.csv`.

## 1. Ümumi sxem
1. Ssenarinin harmonlaşdırılmış nəticələri (`P1_effects.csv`: MikroUnit + uzun müddət, CAEM, IO, mikrosimulyasiya) oxunur.
2. **Həssaslıq** (bölmə 5) — ilk üç sürücü həm `P4_sensitivity.csv`-yə, həm də «zəif ötürmə» yan təsir ssenarisinə ötürülür.
3. **Avtomatik yan təsir ssenariləri** (bölmə 3) nüvə funksiyaları ilə hesablanır.
4. **RiskUnit**: `stress/run` (siyasətlə vs siyasətsiz şərti paylanma), `optimize/run` (tədbir portfeli) — yalnız HTTP.
5. **Qaydalar kitabxanası** əsas ssenari və hər yan təsir ssenarisi üçün qiymətləndirilir → yan təsirlər siyahısı.
6. **Azaldıcı tədbirlər**: qayda → RiskUnit risk id-ləri (R01–R19) və tədbirləri (T01–T30) + siyasətə xas təkliflər.
7. FR5-ə KPI girişləri (`P4_kpi_inputs.csv`: `side_effects`, `risk_es`); `fr4.kpi_refresh` P5-i yeniləyir.

## 2. Yan təsir qaydaları kitabxanası (`config/side_effect_rules.csv`)
Sütunlar: `id, name_az, family, instruments, metric, op, thresholds, unit, affected_group, affected_sector, risk_ids,
params, tier, template_az`. Yeni qayda = yeni sətir (proqramlaşdırma yoxdur, NFR4): mövcud metrikalardan birini seçin,
dörd monoton hədd `t1;t2;t3;t4` yazın (şiddət: 1 aşağı, 2 orta, 3 yüksək, 4 kritik — keçilən hədlərin sayı), `op` = `>`
(artım pisdir) və ya `<` (azalma pisdir), izah şablonu `{value} {unit} {year} {horizon} {sector} {low} {high}` yer
tutucuları ilə. `instruments` = `*` (bütün alətlər) və ya alət id-lərinin `;` siyahısı. Yükləmə zamanı yoxlanılır
(naməlum ailə/metrika, qeyri-monoton hədlər — Azərbaycan dilində xəta).

**Ailələr (10):** fiskal sürüşmə, inflyasiya, idxal sızması, qeyri-formallaşma, rent axtarışı, regional disbalans,
sıxışdırma (crowding-out), borc dayanıqlılığı, rəqabət/bazar gücü, sosial bölgü — Blueprint-in «gözlənilməz nəticə icmalı»
(fiskal sürüşmə, qeyri-formallıq, rent axtarışı, regional disbalans, idxal sızması) tam əhatə olunur.

| Metrika | Tərif (əsas metod; kanal yoxdursa CAEM → IO → mikrosimulyasiya) |
|---|---|
| `fiscal_drift_mln` | Σ(−Δ büdcə balansı − ex ante xərc), ≤ 2030 — geri əlaqələrdən sonra xalis kəsirin statik xərcdən artıq hissəsi |
| `cost_escalation_pct` | (xərc/ÜDM son il) / (xərc/ÜDM ilk il) − 1 — daimi öhdəliyin iqtisadiyyatdan sürətli artımı |
| `fiscal_cost_gdp` | orta birbaşa xərc / nominal ÜDM |
| `d_infl_max`, `d_cpi_level` | inflyasiyanın pik fərqi (f.b.), İQİ səviyyəsinin orta müddətli fərqi (%) |
| `import_leakage` | ΣΔ real qeyri-neft idxalı / ΣΔ real qeyri-neft ÜDM (qısa+orta) |
| `ca_drop_gdp` | Δ cari hesab proksisi / ÜDM (minimum) |
| `mw_disemployment` | kalibrlənmiş minimum əmək haqqı kanalı (bölmə 6) |
| `tax_informality` | gəlir vergisi artımı → formal muzdlu məşğulluq (yarı-elastiklik; 2019 güzəşti kalibrasiya nöqtəsi) |
| `d_hired_min` | FR4 muzdlu işçilərin minimum fərqi (%) |
| `subsidy_intensity` | subsidiya / hədəf sektorun nominal əlavə dəyəri (FR1 real ƏD × deflator) |
| `d_hhi_mean`, `d_margin_max` | FR12 HHI orta dəyişməsi; FR10 sahə marjasının maksimum artımı |
| `regional_spread` | FR10 regional buraxılış Δ%-nin maksimum − minimum fərqi |
| `crowd_private_inv` | FR1 real qeyri-neft özəl investisiyasının (`fr1:rinv_non`) orta müddətli fərqi |
| `sector_loser_min` | ümumi ÜDM artarkən ən çox itirən FR1 sektorunun ƏD fərqi |
| `d_debt_end`, `sofaz_drawdown` | son il borc/ÜDM fərqi; ARDNF aktivlərinin kumulyativ azalması |
| `d_real_income`, `fixed_income_loss` | real sərəncamda qalan gəlir; pensiya/ÜSY real dəyərinin birillik itkisi (−Δ% İQİ) |
| `d_gini`, `d_poverty` | mikrosimulyasiya (SİNTETİK məlumat xəbərdarlığı ilə) |
| `risk_dP_cpi/_fis/_g` | RiskUnit: hədd pozulma ehtimalının artımı (siyasətlə − siyasətsiz) |
| `fx_debt_reval` | devalvasiya × valyuta borcu/ÜDM (fərziyyə 10 %) |

## 3. Avtomatik yan təsir ssenariləri
Hər siyasət ssenarisi üçün avtomatik yaradılır (`side_effects.variant_specs`) və nüvə ilə hesablanır. Şərt altında siyasət
təsiri = (siyasət + şərt) − (yalnız şərt), eyni vintaj — beləliklə şərtin özünün təsiri siyasətə yazılmır.

| Variant | Şərt | Hesablama |
|---|---|---|
| `oil_m1s` | Brent −1σ (σ = RiskUnit `stress/inputs`, illik log dəyişmənin sd-si 2003–2025; ≈ −25,6 %) başlanğıc ildən | `eng_micro.plan` override-ları + `brent` (pct), `microbridge.run` |
| `fx_p1s` | Manat −1σ (≈ +16,5 % AZN/USD) — `fx_deval` aləti əlavə edilir | `integrate.run_scenario` (micro, CAEM, IO, longrun) |
| `weak_coef` | Sobol üzrə ilk 3 MikroUnit əmsalı əlverişsiz istiqamətdə 1 SE | baza və ssenari eyni əmsallarla |
| `fin_alt` | alternativ maliyyələşmə: borc → vergi, ARDNF → borc, vergi/yenidən bölüşdürmə → borc | `integrate.run_scenario` |

Variantlarda yalnız **əsas ssenaridən fərqlənən** yan təsirlər yazılır (`change_vs_base` = yeni / güclənir / zəifləyir);
əsas göstəricilərin müqayisəsi `P4_side_effect_scenarios.csv`-dədir. Run vaxtı üçün variantlarda mikrosimulyasiya və OxLon
mühərrikləri işə salınmır (qeyd edilir).

## 4. RiskUnit inteqrasiyası (yalnız HTTP)
`http://127.0.0.1:8791/api/v1/` (`POLICY_RISK_API`), nişanlar `demo-read` / `demo-write` (`POLICY_RISK_TOKEN_READ/WRITE`),
başlıq `X-Actor: PolicyUnit-FR4`. `riskunit` paketi heç vaxt PolicyUnit prosesinə import edilmir. Server işləmirsə
`RiskUnit/api/server.py --port 8791 --db PolicyUnit/work/risk_scratch.db --quiet` (`RISK_NO_NETWORK=1`) fonda başladılır
və iş bitəndə dayandırılır (yalnız FR4 özü başladıbsa). Serverin bazası (`GET status` → `baseline_id`) RiskUnit-in cari bazasından (`output/_run_summary_v2.json`) fərqlidirsə: FR4-ün başlatdığı server yenidən başladılır; başqasının serveri **heç vaxt dayandırılmır** — FR4 öz serverini 8793–8799 aralığında ilk boş portda başladır (8790 MikroUnit, 8791 RiskUnit, 8792 PolicyUnit API-si üçündür) və portu jurnala yazır. Başqa bazaya aid keşlənmiş cavablar silinir. Çağırışlar: `GET stress/inputs` (σ), `POST stress/run`,
`GET optimize/inputs`, `POST optimize/run`.

**Keş və şəbəkəsiz rejim.** Hər cavab `work/risk_cache/<sha1>.json`-da saxlanılır (sorğu + cavab + vaxt). `POLICY_NO_NETWORK=1`
və ya server əlçatmaz olduqda son keş istifadə olunur, `status` sütununda «keş (YYYY-MM-DD HH:MM:SS); …» yazılır; keş
yoxdursa sətirlər NaN və «əlçatmaz» statusu ilə yazılır (iş dayanmır). Canlı cavab — «canlı».

**Əsas mənbə (2026-10-06 yeniləməsi).** RiskUnit `stress/run` indi `micro_overrides`-i öz Monte Karlo-suna tətbiq edir (`ru.policy_shift`, baxış «siyasətlə» / «şoka şərtli + siyasət», `metrics.*.siyasetin_effekti`). `P_with`, `ES10_with`, `p10_with`, `median_with` bu baxışdan götürülür (`source` = «RiskUnit stress/run (siyasət baxışı)»). Aşağıdakı PolicyUnit yerdəyişməsi çarpaz yoxlama kimi saxlanılır (`shift_pu`, `P_with_pu`, `dP_pu`, `agree_dP` = |dP − dP_pu|) və sorğuda `micro_overrides` olmadıqda (yalnız overlay/CAEM kanallı alətlər) əsas rəqəmdir. RiskUnit zənciri PolicyUnit overlay-lərini (ARDNF maliyyələşməsi, proksi alətlər) görmür — belə ssenarilərdə `note_az` xəbərdarlıq edir.

**Əsas mənbə qaydası (`esas_menbe`, `esas_menbe_izah`; `risk_link.primary_source`).** (a) Ssenari tam `micro_overrides` ilə təmsil olunursa — RiskUnit əsasdır (pension10, polrate_m100, pubinv1bn_deficit). (b) Ssenaridə RiskUnit-in görmədiyi PolicyUnit overlay/maliyyələşmə kanalı varsa (ARDNF/vergi maliyyələşməsi, FR1-dən kənar birbaşa xərc, ƏDV/vergi/subsidiya proksiləri) və ya `micro_overrides` yoxdursa — PolicyUnit sürüşməsi əsasdır, RiskUnit çarpaz yoxlamadır. (c) Məzənnə (devalvasiya) ssenarilərində RiskUnit əsasdır, çünki onun kalibrlənmiş məzənnə ötürmə qatı (`riskunit/fx.py`, 2015–2018 kalibrasiyası) PolicyUnit zəncirində yoxdur. Hər iki rəqəm həmişə göstərilir: `P_with_ru`/`dP_ru` və `P_with_pu`/`dP_pu`, fərq `agree_dP`.

**Siyasətlə vs siyasətsiz paylanma (PolicyUnit çarpaz yoxlaması).** RiskUnit-in birgə Monte Karlo modeli (simulate) yalnız öz şok açarlarına reaksiya verir;
`micro_overrides` yalnız onun MikroUnit zəncirinə təsir edir (cavabda `micro.headline`). Ona görə Blueprint prinsipi tətbiq
olunur: «siyasət ssenarisi paylanmanı sürüşdürür». Siyasətsiz paylanma X = RiskUnit-in şərtsiz (baza mərkəzli) paylanması
(yan təsir ssenarilərində — şoka şərtli paylanma: `shocks` = Brent −1σ və ya fx +16,5 %); siyasətlə paylanma X + d_t, burada
d_t PolicyUnit əsas metodunun (P1) siyasət təsiridir: qeyri-neft artımı üçün Δg_t = [(1+L_t)/(1+L_{t−1}) − 1]·(1+g_t^baza)
(L — qeyri-neft ÜDM səviyyəsinin % fərqi), İQİ üçün Δ inflyasiya (f.b.), büdcə üçün Δ balans/ÜDM (f.b.). Nəticələr:
* P(hədd pozulması) siyasətlə = F(h − d) («<» həddi) və ya 1 − F(h − d) («>» həddi); F — RiskUnit kvantillərindən (p05…p95)
  + dəqiq (h, P_hədd) nöqtəsindən qurulmuş paylanma funksiyası, quyruqlarda normal ekstrapolyasiya. Hədlər RiskUnit-indir:
  qeyri-neft artımı < 2 %, inflyasiya > 6 %, balans < −1 % ÜDM.
* ES10 siyasətlə = ES10 siyasətsiz + d (yerdəyişmədə dəqiqdir). ES10 siyasətsiz qiymətləndirmə ilində (2027) RiskUnit-in dəqiq
  dəyəridir, digər illərdə kvantillərdən normal quyruq təxminidir (`es_method` sütunu).
* `ru_chain_shift` — RiskUnit-in öz MikroUnit zəncirinin eyni siyasət üçün cavabı (çarpaz yoxlama; overlay/proksi alətlərdə
  və CAEM-only alətlərdə boşdur). Büdcə üçün fərq tərif fərqidir (RiskUnit balansı fərqli ÜDM ilə normallaşdırır).
* Məhdudiyyət: yerdəyişmə paylanmanın formasını dəyişmir (siyasətin şok həssaslığına təsiri yalnız yan təsir ssenarilərində,
  şərt altında siyasət təsiri ilə əks olunur).

## 5. Azaldıcı tədbirlər (`P4_mitigation.csv`)
* **Qayda xəritəsi** `config/mitigation_map.csv` (`rule_id, risk_ids, measures, proposal_type, proposal_az, responsible_az,
  kpi_az`): hər tetiklənən qayda → RiskUnit risk id-ləri (R01–R19) + tədbir reyestri (T01–T30; ad, strategiya, məsul, xərc
  `optimize/inputs`-dan) + siyasətə xas təkliflər: **ardıcıllıq** (mərhələli tətbiq, təxirə salma), **hədəfləmə**, **kompensasiya**,
  **maliyyələşmə**, **monitorinq**, **tənzimləmə**. Prioritet şiddətdən: ≥3 yüksək, 2 orta, 1 aşağı.
* **RiskUnit `optimize/run`**: xəritədəki tədbirlər `include` (məcburi) kimi verilir; büdcə = max(100; 1,2 × məcburi xərc + 50)
  mln AZN; siyasət qiymətləndirmə ilində hədd pozulma ehtimalını d qədər artırırsa, risk iştahı həmin qədər sərtləşdirilir
  (məs. `P_cpi_max` = 0,50 − ΔP). Nəticə: portfel (rol: məcburi / optimal seçim / imkanlandırıcı minimum paket, marjinal töhfə)
  və siyasətin toxunduğu risklər üzrə qalıq risk. Qeyd: RiskUnit optimallaşdırıcısı siyasət ssenarisini bilmir — o, baza risk
  mənzərəsi üzərində işləyir; siyasətin təsiri məcburi tədbirlər və sərtləşdirilmiş risk iştahı ilə ötürülür.
* **Alternativ maliyyələşmə təklifi**: `fin_alt` variantında fiskal/borc yan təsirləri yox olursa və ya zəifləyirsə, təklif
  sətiri yaradılır (yeni sosial/inflyasiya yan təsirləri də göstərilir).

## 6. Bilinən model boşluqları — yan təsir kimi
**Minimum əmək haqqı → qeyri-formallaşma / məşğulluq itkisi (SE08, sübut səviyyəsi D).** MikroUnit FR1/FR3/FR4-də minimum
əmək haqqının məşğulluğu azaltma və qeyri-formal sektora itələmə kanalı yoxdur (artım yalnız maaş → gəlir → istehlak
kanalı ilə ötürülür). Kalibrlənmiş kanal: Δ formal iş yerləri = ε · Δ%MƏH · N_bağlı / 100, N_bağlı = payı × muzdlu işçilər
(FR4, orta müddət). Parametrlər (`params` sütunu, dəyişdirilə bilər): ε ∈ [−0,3; 0], mərkəz −0,1 (Neumark & Wascher 2008:
aşağı ixtisaslı qruplar üçün −0,1…−0,3; Broecke, Forti & Vandeweyer 2017, inkişaf etməkdə olan ölkələr üzrə meta-təhlil:
effektlər əsasən kiçik və sıfıra yaxın; Dube 2019: median maaşın ~60 %-inə qədər məşğulluq itkisi minimal), minimum əmək
haqqı ətrafındakı işçilərin payı 15 % (10–20 %; FƏRZİYYƏ — İQS/EBT maaş paylanması ilə əvəz edilməlidir), itən iş yerlərinin
60 %-i (50–70 %) qeyri-formal məşğulluğa keçir (Ham 2018, Honduras: əhatə olunan sektorda məşğulluq azalır, qeyri-formal
artır). Kaitz indeksi (MƏH / orta nominal maaş) izahda verilir; median maaşa nisbətdə daha yüksəkdir.
**FR1 ümumi məşğulluq elastikliyi çox kiçikdir** (E1 ≈ 0,03) — buna görə işsizlik/məşğulluq effektləri sıfıra yaxındır;
formal iş yerləri effekti ayrıca FR4 muzdlu işçilərdən verilir (`fr4_jobs` izahda, `informality` həssaslıq bloku: xalis formal
iş yerləri = FR4 effekti + kalibrlənmiş itki).

## 7. Həssaslıq və qeyri-müəyyənlik (`P4_sensitivity.csv`, `P4_uncertainty_bands.csv`)
Qiymətləndirilən kəmiyyət **siyasət təsiridir** (ssenari − baza, hər çəkilişdə eyni parametrlərlə), proqnoz deyil.
* **micro** — MikroUnit FR1/FR3/FR4 əmsalları (redaktə edilə bilən, SE > 0, sabitlər xaric; 87 namizəd), müstəqil kəsilmiş
  normal z ∈ [−2,5; 2,5] (reyestrlərdə kovariasiya yoxdur — qeyri-müəyyənlik bir qədər şişirdilə bilər). (1) +1 SE OAT
  skrininqi; (2) ilk K = 5 əmsal üzrə **həqiqi zəncirdə** Saltelli dizaynı (A, B, A_B^(i); N = 160 → 1 120 qiymətləndirmə, hər
  biri baza + ssenari; paralel prosesler; `POLICY_SOBOL_N`); (3) dinamik qeyri-sabit çəkilişlər (|təsir| > 25 və ya 25×|mərkəz|)
  estimatordan çıxarılır, lakin **gizlədilmir**: payı (`share_rejected`) və qeyri-sabitlik bölgəsi
  `P4_instability.csv`-də verilir — hər əmsal üçün rədd edilən çəkilişlərdə orta z, şərti rədd tezliyi z > 1 və z < −1
  üçün, və ən pis əmsal cütü bölgəsi (məs. E3 əmək haqqı fondu və qeyri-neft ÜDM elastiklikləri birlikdə +0,5 SE-dən çox
  olduqda çəkilişlərin ~80 %-i qeyri-sabitdir). Bu, model riski (R19) üzrə məlumatdır: gəlir–istehlak dövrəsi qiymətləndirmə
  qeyri-müəyyənliyinin yuxarı hissəsində partlayıcı olur. Başlıq nəticələri: real ÜDM (orta), inflyasiya (qısa), muzdlu işçilər (orta), büdcə
  balansı (orta). Kvadratik emulyator sınaqdan keçirildi və **rədd edildi** (yoxlama R² < 0: gəlir–istehlak dövrəsi E3×D1 güclü
  qeyri-xəttidir).
* İndekslər: f_0 mərkəzləşdirmə ilə S_i = E[f_B(f_{A_B^i} − f_A)]/V (Saltelli 2010), S_T,i = E[(f_A − f_{A_B^i})²]/(2V)
  (Jansen 1999). Yığılma: bootstrap 95 % CI yarım eni (`ci_halfwidth`; ≤ 0,15 → «bəli»), N/2 ilə N fərqi,
  birinci sürücünün və ilk-3 dəstinin bootstrap sabitliyi (`top1_stability`, `top3_stability`). Yığılmayan nəticələr
  **«indikativ»** etiketlənir: «indikativ (ilk-3 sabit)» (≥ 80 %), «indikativ (1-ci sürücü sabit)» (≥ 90 %), «indikativ».
  N = 64 → 160 artımı CI-ni ≈ 0,4-dən ≈ 0,2–0,35-ə endirdi; 0,15 üçün N ≈ 600 lazımdır (ssenari başına ≈ 2,5 dəq.) —
  `POLICY_SOBOL_N` ilə artırıla bilər (nəticələr keşlənir). İshigami testi (`tests/test_fr4.py`) estimatorları yoxlayır.
* **io** — Leontief tip I: A_d sütunları u_j ~ logN(0; 0,10), daxili/idxal bölgüsü r ~ U(0,9; 1,1) (GRAS yenilənməsi və
  aqreqasiya xətası fərziyyəsi); nəticələr: ƏD effekti, idxal sızması, məşğulluq; N = 512 və 1024 ilə yığılma.
* **informality** — bölmə 6-dakı kanal: ε, bağlı işçilərin payı, FR4 effekti, qeyri-formala keçid payı.
* **microsim** — buraxılıb: bir icra ≈ 15 s və `eng_microsim.simulate(behaviour=…)` interfeysi hələ aktiv deyil.
Zolaqlar: p05/p25/p50/p75/p95 + model mərkəzi (`central`). Mərkəz ilə median fərqi qeyri-xəttiliyi göstərir.

## 8. Çıxışlar
`P4_side_effects.csv` (scenario, variant, rule_id, ailə, metrika, dəyər, interval, şiddət, üfüq, il, qrup, sektor, risk id-ləri,
sübut səviyyəsi, izah, change_vs_base), `P4_side_effect_scenarios.csv`, `P4_risk_profile.csv`, `P4_mitigation.csv`,
`P4_kpi_inputs.csv` (`side_effects` = əsas ssenaridə tetiklənən qaydaların sayı; `risk_es` = başlanğıc ildən 2030-a qədər
qeyri-neft artımı ES10 dəyişməsinin ortası, f.b., «yüksək = yaxşı»), `P4_sensitivity.csv`, `P4_uncertainty_bands.csv`,
`P4_instability.csv`. Hamısı `output/_catalog.csv`-də qeydiyyatdadır (sahib `fr4`).

## 9. Konfiqurasiya (NFR4) və dürüstlük qeydləri
* Yeni yan təsir qaydası: `side_effect_rules.csv`-yə sətir; yeni tədbir təklifi: `mitigation_map.csv`-yə sətir (eyni `rule_id`
  üçün bir neçə sətir ola bilər). Kod dəyişikliyi tələb olunmur; yoxlama `python3 -m unittest tests.test_fr4`.
* Sübut səviyyəsi: MikroUnit əsaslı metrikalar C (təxmin edilmiş struktur tənliklər), proksi/overlay alətləri və kalibrlənmiş
  kanallar (SE08, SE09, SE11, SE26) D — «ölçülmüş təsir deyil, fərziyyələrə şərti model proqnozu».
* RiskUnit-in paylanması baza mərkəzlidir və OxLon/MikroUnit baza vintajına bağlıdır (`baseline_id` sütunu).
* Mikrosimulyasiya nəticələri (SE21, SE22) SİNTETİK ev təsərrüfatı faylına əsaslanır — real ev təsərrüfatı məlumatı deyil.
* Bilinən çatışmazlıqlar: (i) reyestrlərdə əmsal kovariasiyası yoxdur; (ii) gəlir–istehlak dövrəsinin əmsalları birlikdə
  +1 SE olduqda zəncir dinamik qeyri-sabitdir (rədd edilən çəkilişlər — model riski R19); (iii) CAEM-only alətlər (məs.
  mənfəət vergisi) üçün MikroUnit həssaslığı və neft variantı tətbiq edilmir.

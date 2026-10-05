# %% [markdown]
# # FR10 — Müəssisələrin və istehsalların maliyyə vəziyyəti, istehsal səmərəliliyi və bazar mövqeyi
#
# **MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma.** Azərbaycan Respublikasının İqtisadiyyat Nazirliyi.
#
# ## Tələb (təsdiq edilmiş mətn, 24 avqust 2026)
#
# > *"Müəssisələrin və istehsalatların maliyyə vəziyyəti, istehsal effektivliyi və bazar paylarının təhlili və
# > proqnozlaşdırılması mümkün olmalıdır."*
#
# FR10 müəssisələrin və istehsalların **maliyyə vəziyyətinin**, **istehsal səmərəliliyinin** və **bazar mövqeyinin**
# analitik qiymətləndirilməsini, müqayisəli təhlilini və proqnozunu bir neçə mənbədən müəssisə, maliyyə, istehsal və
# bazar göstəricilərini əlaqələndirməklə təmin etməlidir. Onun altı məqsədi: (1) fəaliyyət səmərəliliyini qiymətləndirmək
# və müqayisə etmək; (2) istehsal göstəricilərinin artımını və ya azalmasını müəyyən etmək; (3) regionlar, fəaliyyət
# növləri, məhsullar və digər bölgülər üzrə müqayisə aparmaq; (4) inkişafın və ya geriləmənin əsas amillərini müəyyən
# etmək; (5) istehsal və bazar göstəricilərini proqnozlaşdırmaq; (6) qərar qəbul edənlərə məlumatlara əsaslanan analitik
# imkan vermək. O, maliyyə məlumatlarının təqdimatı ilə **məhdudlaşmamalı** və **hansı göstərici üçün hansı mənbədən
# hansı məlumatların istifadə olunduğunu və onların istifadəçiyə hansı formada çatdığını** konkret göstərməlidir
# (Hissə 8 və `output/FR10_data_source_matrix.csv`).
#
# ## Sifarişçinin müəyyən etdiyi məhdudiyyətlər (FR1–FR5-də olduğu kimi)
#
# - **Avtoreqressiv modellər istifadə olunmur** — AR, ARIMA, ARCH, GARCH, gecikmiş asılı dəyişən və dəyişənin öz
#   tarixi əsasında proqnoz yoxdur. Hissə 9 notebook-da rast gəlinən hər gecikmə konstruksiyasını və onun nə üçün
#   avtoreqressiya olmadığını sadalayır.
# - **Əlaqəli sektorların təsirini göstərən struktur ekonometrik modellər**: FR10-dakı hər sahə proqnozu FR1-in sektor
#   trayektoriyalarına (emal sənayesi, mədənçıxarma, elektrik enerjisi, su təchizatının əlavə dəyəri və onların
#   deflyatorları, neft qiyməti), FR3-ün sahələr üzrə əmək haqlarına və FR4-ün məşğulluğuna şərtlənir.
# - **İş kitabında (Excel faylı) məlumat çatışmadıqda, onu DSK-dan toplamaq** (Hissə 4): 120-dən çox DSK cədvəli bir
#   dəfə `data/dsk_enterprise/` qovluğuna yüklənir və sonra diskdən yenidən oxunur.
# - **NFR1**: proqnoz dəqiqliyi yalnız proqnoz anında mövcud olan məlumatlardan istifadə etməklə sadə müqayisə
#   meyarlarına qarşı yoxlanılır (Hissə 13, ≤ 2019 qiymətləndirilən sürüşən başlanğıclar, toxunulmamış 2020–2025
#   nümunədən kənar yoxlama).
#
# ## İki qat
#
# | Qat | Təhlil vahidi | Məlumatlar | Vəziyyət |
# |---|---|---|---|
# | **A — hazırda işlək** | "müəssisə qrupları": 30 sənaye sahəsi (NACE 06–09, 10–33, 35, 36–39), ölçü qrupları, dövlət / qeyri-dövlət, 14 iqtisadi rayon, ~150 məhsul | DSK-nın sənaye, milli hesablar, sahibkarlıq və statistik reyestr cədvəlləri; iş kitabının `Emal Sənayesi`, `Mədənçıxarma`, `Elektrik enerjisi `, `Su təchizatı`, `Real sektor`, `DVX üzrə göstəricilər`, `KOBİA`, `Park`, `Regionlar*` vərəqləri | **Nəticələr** (Hissə 4–16) |
# | **B — müəssisə səviyyəli mühərrik** | ayrıca müəssisə | Vergi Xidməti / DSMF balans hesabatı və mənfəət-zərər hesabatı paneli, 24 avqust 2026-da sorğu edilib (müddət 26 avqust 2026) — **hələ alınmayıb** | **Yalnız emal xətti**, aydın işarələnmiş **SİNTETİK** panel üzərində sınaqdan keçirilib (Hissə 17); A qatının nəticələri ilə heç vaxt qarışdırılmır |
#
# A qatı tələbdə adı çəkilən üç sütun üzrə qurulub:
#
# 1. **Bazar mövqeyi** — sahələrin sənaye və emal sənayesi buraxılışındakı payları, sahələr və regionlar üzrə
#    konsentrasiya (HHI, CR4), qeyri-dövlət sektorunun payı, KOB-ların payı, regional bölgü, məhsul həcmləri, giriş və
#    çıxış.
# 2. **İstehsal səmərəliliyi** — əmək məhsuldarlığı, aralıq istehlakın payı, kapital məhsuldarlığı, **müşahidə
#    olunan** xərc payları ilə artımın uçotu üsulu üzrə ümumi amil məhsuldarlığı (TFP), əmək haqqı–məhsuldarlıq
#    fərqi, innovasiya intensivliyi.
# 3. **Maliyyə vəziyyəti** — sənaye bölmələri üzrə ümumi əməliyyat mənfəətinin (ÜƏM) marjaları (milli hesablar) və
#    sahələr üzrə ÜƏM proksisi (əlavə dəyər − əmək haqqı fondu), mənfəət vergisi bəyannamələrinin aqreqatları (DVX),
#    investisiyaların özünümaliyyələşdirilməsi, hazır məhsul ehtiyatları, KOB-ların aktivləri və vergiləri.
#
# ## FR1, FR3 və FR4 ilə əlaqə
#
# | Modul | Obyekt | FR10-a verdiyi |
# |---|---|---|
# | **FR1** | Sektorların buraxılışı, qiymətlər, makroiqtisadiyyat | Mədənçıxarma, emal sənayesi, elektrik enerjisi və su təchizatının real əlavə dəyəri və deflyatorları, neftin ixrac qiyməti, qeyri-neft ÜDM, investisiya deflyatoru; üç ssenari və Əsas ssenari üzrə 500 butstrap çəkilişi (`FR1_fan_draws.csv`) |
# | **FR3** | Əmək haqları | Sənaye sahələri üzrə orta əmək haqqı trayektoriyaları (`FR3_industry_branch_wages.csv`) |
# | **FR4** | Məşğulluq | Fəaliyyət növləri üzrə muzdlu işçilər (`FR4_hired_by_activity.csv`) |
# | **FR10** *(bu notebook)* | Müəssisə qrupları | — |
#
# | Hissə | Məzmun |
# |---|---|
# | 1–3 | Məqsəd; iş mühiti; ekonometrik alətlər (statsmodels ilə yoxlanılıb) |
# | 4–6 | DSK məlumatlarının toplanması; sahə, region və məhsul panellərinin qurulması; məlumat bütövlüyü üzrə tapıntılar |
# | 7 | A qatının analitikası: bazar mövqeyi, səmərəlilik, maliyyə vəziyyəti |
# | 8 | Göstəricilər sistemi: məlumat–mənbə matrisi, boşluqlar cədvəli, təqdimat spesifikasiyası |
# | 9 | İcazə verilən gecikmə konstruksiyaları; sınaqdan keçirilmiş və rədd edilmiş spesifikasiyalar |
# | 10 | Əsas amillər: sahə artımının amilləri paneli |
# | 11–12 | Sahə pay sistemi (emal sənayesi, mədənçıxarma) və regional pay sistemi |
# | 13 | Təsadüfi gəzişmə və sabit artım müqayisə meyarlarına qarşı nümunədən kənar yoxlama |
# | 14–15 | FR1-in üç ssenarisi üzrə 2026–2030 proqnozu; qeyri-müəyyənlik zolaqları |
# | 16 | Tarixi məlumatlarla müqayisədə inandırıcılıq; erkən xəbərdarlıq siqnalları |
# | 17 | B qatı — müəssisə səviyyəli mühərrik, onun SİNTETİK emal xətti sınağı və (v2) tam müəssisə səviyyəli ekonometrik təhlil: rentabellik, istehsal funksiyası, TFP, maliyyə çətinliyi, investisiya, bazar payı, ixrac, parametrlərin bərpası |
# | 18 | Eynilik yoxlamaları, nəticə faylları, təqdimat spesifikasiyası, tapıntılar, sənədləşdirmə |
# | 19 | v2: tənliklər reyestri, göstəricilər kataloqu, tam proqnoz cədvəli, ssenari mühərriki, dayanıqlıq və tornado, Azərbaycan dilində sətirlər |
#
# > **Vəziyyət qeydi.** B qatı Vergi Xidmətinin / DSMF-nin müəssisə panelini gözləyir. B qatının hər cədvəli və
# > qrafiki başlanğıc dəyəri (seed) sabitlənmiş sintetik paneldən hazırlanır, `SYNTHETIC — pipeline test, not results`
# > (*SİNTETİK — emal xəttinin sınağı, nəticə deyil*) su nişanını daşıyır, `output/FR10_SYNTHETIC_*.csv`
# > fayllarına yazılır və heç vaxt A qatının nəticəsində və ya tapıntılarda istifadə olunmur.

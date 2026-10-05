# %% [markdown]
# # FR12 — Rəqabət mühiti: intensivlik, bazara giriş və çıxış, ssenarilər, erkən xəbərdarlıq
#
# **MİİS modulu 15.5.2 — Mikroiqtisadi təhlil və proqnozlaşdırma.** Azərbaycan Respublikasının İqtisadiyyat Nazirliyi.
#
# > **Vəziyyət qeydi.** A qatı (aqreqat məlumatlar) işləkdir və nəticələr verir. **B qatı (müəssisə səviyyəli rəqabət
# > mühərriki) 24 avqust 2026-da sorğu edilmiş DSK biznes reyestrini gözləyir** ("NACE × region üzrə müəssisə
# > səviyyəsində gəlir; giriş və çıxış — DSK biznes reyestri — müddət 26 avqust 2026", alınmayıb). O daxil olana qədər
# > B qatı emal xəttini əvvəldən sonadək sübut etmək üçün **SİNTETİK reyestr — real müəssisə məlumatı deyil**
# > (`data/business_register/FR12_business_register_SYNTHETIC.csv`) üzərində işləyir. Hissə 17-də çap olunan banner hər
# > icranın məlumat rejimini göstərir.
#
# ## Tələb (təsdiq edilmiş mətn, 24 avqust 2026)
#
# > *"Rəqabət mühitinin təhlili, sektorlarda rəqabət intensivliyinin və müəssisələrin rəqabət strategiyalarının
# > qiymətləndirilməsi və proqnozlaşdırılması mümkün olmalıdır."*
#
# Razılaşdırılmış tövsiyə (Tövsiyə – D.Ə.): müəssisələrin rəqabət **strategiyalarını** birbaşa qiymətləndirmək əvəzinə FR12
# aşağıdakıları təqdim edir: (1) **sektorlar üzrə rəqabət intensivliyinin** və **bazara giriş və çıxışın tezliyinin**
# ölçülməsi və bu göstəricilərin proqnozları; (2) sənaye təşkilatı (IO) nəzəriyyəsinə əsaslanaraq, fərziyyələr
# göstərilməklə, sektorun siyasət və ya bazar dəyişikliyinə ehtimal olunan reaksiyasının **ssenari təhlili**; (3) erkən
# xəbərdarlıq göstəriciləri vasitəsilə rəqabətin **pisləşdiyi** sektorların aşkarlanması; habelə **bazar
# konsentrasiyasının** təhlili və proqnozlaşdırılması. Göstəricilər məlumatların mövcudluğundan asılı olaraq Sifarişçi
# ilə razılaşdırılır — buna görə məlumat–mənbə matrisi və boşluqlar cədvəli verilir (Hissə 9).
#
# ### "Rəqabət strategiyası" niyə qiymətləndirilmir və onu nə əvəz edir
#
# Strategiya (xərc liderliyi, diferensiasiya, gizli sövdələşmə, bazara girişin qabaqlanması, yırtıcı qiymət siyasəti)
# *idarəetmə niyyətidir*. Heç bir statistik mənbə onu qeydə almır və onu aqreqat məlumatlardan çıxarmaq ölçmə kimi
# təqdim edilən fərziyyə olardı. FR12 strategiyaların təzahür etdiyi **müşahidə olunan davranışı** ölçür: **giriş** (yeni
# vahidlər və onların ölçüsü), **çıxış** (ləğvetmələr, yaş üzrə sağ qalma), **payların mobilliyi** (bazar paylarının nə
# qədər dəyişdiyi və sıraların necə dəyişdiyi), **marjalar** (qiymət-xərc marjası proksisi, müəssisə məlumatları
# mövcud olduqda Boone mənfəət elastikliyi) və **konsentrasiya** (HHI, CR4, ölçü qrupları üzrə hədlər). Rəqabət orqanı
# məhz bunları izləyə və onlara əsasən tədbir görə bilər.
#
# ## Sifarişçinin müəyyən etdiyi məhdudiyyətlər (FR1–FR10-da olduğu kimi)
#
# - **Avtoreqressiv modellər istifadə olunmur**: AR, ARIMA, ARCH, GARCH, gecikmiş asılı dəyişən və dəyişənin öz tarixi
#   əsasında proqnoz yoxdur. Hissə 10 rast gəlinən hər gecikmə konstruksiyasını və onun nə üçün avtoreqressiya
#   olmadığını sadalayır; fəaliyyət göstərən müəssisələrin sayı ehtiyat-axın eyniliyinə, $N_t = N_{t-1} + B_t - D_t$,
#   tabedir — bu, uçot eyniliyidir.
# - **Əlaqəli sektorların təsirini göstərən struktur modellər**: giriş və çıxış heç vaxt öz keçmişi ilə deyil, FR1-in
#   sektor tələbi trayektoriyaları, kredit şəraiti və FR10-un rentabelliyi ilə idarə olunur.
# - **İş kitabında olmayan məlumatlar DSK-dan**: statistik reyestr və sahibkarlıq cədvəlləri, o cümlədən fəaliyyət
#   panelini 2019-cu ilədək geri uzadan DSK fayllarının **arxivləşdirilmiş buraxılışları** (Hissə 4).
# - **NFR1**: yalnız proqnoz anında mövcud olan məlumatlardan istifadə etməklə sadə müqayisə meyarlarına (təsadüfi gəzişmə
#   və sabit orta əmsal) qarşı dəqiqlik (Hissə 12).
#
# ## İki qat
#
# | Qat | Təhlil vahidi | Məlumatlar | Vəziyyət |
# |---|---|---|---|
# | **A — hazırda işlək** | DSK-nın 11 fəaliyyət qrupu, 19 NACE bölməsi, 14 iqtisadi rayon, vergi ödəyicilərinin ölçü qrupları | DSK statistik reyestri (`st_units`), sahibkarlıq və milli hesablar cədvəlləri, DSK-nın arxivləşdirilmiş buraxılışları, iş kitabının `Regionlar*`, `DVX üzrə göstəricilər`, `Verilmiş lisenziyalar`, `Aparılan yoxlamalar` vərəqləri; FR1 və FR10 nəticələri | **Nəticələr** (Hissə 5–16) |
# | **B — müəssisə səviyyəli rəqabət mühərriki** | müəssisə (statistik vahid) | DSK biznes reyestri (24 avqust 2026-da sorğu edilib) | **SİNTETİK emal xəttinin nümayişi** (Hissə 17) — Nazirliyin öz sistemində onun faylı ilə əvəz olunur |
#
# ## Məzmun
#
# 2 İş mühiti · 3 Alətlər · 4 Məlumatların toplanması (arxivləşdirilmiş buraxılışlar daxil olmaqla) · 5 Təhlil (parsing) ·
# 6 Məlumat bütövlüyü · 7 Rəqabət göstəriciləri · 8 Konsentrasiya hədləri · 9 Mənbələr matrisi, boşluqlar, təqdimat ·
# 10 Avtoreqressiyasız konstruksiyalar · 11 Giriş/çıxış paneli · 12 Model seçimi və nümunədən kənar yoxlama ·
# 13 Giriş/çıxış proqnozları 2026–2030 · 14 Konsentrasiya yolları · 15 IO ssenari alətləri · 16 Erkən xəbərdarlıq ·
# 17 B qatı (SİNTETİK) · 18 Yoxlamalar, nəticə faylları, sənədləşdirmə.

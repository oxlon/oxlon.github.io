# %%
# Azerbaijani text of the findings (same numbers as above); written to FR12_strings_az.csv in Part 18D
_ev = lambda y, v: f'{y}: ΔN − (yeni − qeydiyyatdan çıxan) = {v:+,.0f}'
FIND_AZ = {
 'F1': ('DSK-nın sahibkarlıq cədvəlləri yalnız son iki ili, reyestr isə yalnız son dövrü dərc edir', 'cari fayllar: 2023–2024 (sahibkarlıq), 1 iyul 2026 (st_units)',
        'DSK-nın arxiv versiyaları bərpa edilib (4-cü hissə): 006 üçün 2019, 2020, 2022–2024; bölmələr üzrə reyestr axınları üçün 2021, 2024, 2025'),
 'F2': ('Sahibkarlıq 006 üçün 2021-ci ili, reyestr axınları üçün isə 2022–2023-cü illərin tam ilini əhatə edən arxiv versiyası yoxdur',
        'İnternet Arxivində 006 yalnız 2022-ci ilin aprel və 2025-ci ilin aprel versiyaları, 2_1 isə 2022 mart, 2022 avqust, 2024 sentyabr, 2025 aprel, 2025 iyul, 2026 fevral versiyaları ilə var',
        'fəaliyyət paneli zaman üzrə balanssızdır (2019, 2020, 2022, 2023, 2024); 2021 qiymətləndirmədə istifadə olunmur; qrafiklər və cədvəllər üçün interpolyasiya ilə doldurulur və işarələnir (FR12_series_filled.csv, 7.1-ci hissə)'),
 'F3': ('2023-cü il 006-nın iki versiyasında dərc olunub; düzəlişlər qeydə alınıb', f'maks. |düzəliş|: yeni qeydiyyat {_rv.d_new.abs().max():.0f}, qeydiyyatdan çıxan {_rv.d_dereg.abs().max():.0f} vahid',
        'sonrakı versiya istifadə olunur; NFR1 real vaxt qeydi: nümunədən kənar yoxlamanın faktiki dəyərləri son versiyadandır'),
 'F4': ('Qeydiyyatdakı sahibkarlıq subyektləri ehtiyat-axın eyniliyinə dəqiq tabe deyil', '; '.join(_ev(y, v) for y, v in _sf.items()),
        'qeydiyyata əsaslanan əmsallar DSK kimi ilin sonundakı qeydiyyat ehtiyatını məxrəc götürür; bərpalar / yenidən təsnifatlar qalıqdır'),
 'F5': ('Bölmələr üzrə reyestr ehtiyatı N(t) = N(t−1) + yeni − ləğv edilən eyniliyinə dəqiq tabe deyil',
        f'2025, bölmələr üzrə cəm: {_sf2.sum():+,.0f} vahid; ən böyük bölmə fərqləri: ' + ', '.join(f'{k} {v:+,.0f}' for k, v in _sf2.abs().sort_values(ascending=False).head(3).items()),
        'reyestrdə bölmələrin yenidən təsnifatı; SİNTETİK reyestr doğulma və ölümləri dəqiq təkrarlayır və ehtiyat fərqini göstərir (17-ci hissə)'),
 'F6': ('Mənbələrdə üç fərqli müəssisə məcmusu var',
        f"qeydiyyatdakı sahibkarlıq subyektləri (fərdi sahibkarlar daxil) {_reg:,.0f} (2024), statistik vahidlər {FLOW_TOT.set_index(['kind', 'period', 'year']).loc[('section', 'FY', 2025), 'published_stock']:,.0f} "
        f"(1 yanvar 2026); aktiv vergi ödəyiciləri {TAXP['all'].dropna().iloc[-1]:,.0f} ({int(TAXP['all'].dropna().index[-1])})", 'hər göstərici öz məcmusunu bildirir; əmsallar məcmular arasında qarışdırılmır'),
 'F7': ('2020-ci ildə kənd təsərrüfatında qeydiyyat sıçrayışı', f"kənd təsərrüfatında yeni qeydiyyatlar {_ag.loc[2019, 'new']:,.0f} (2019) → {_ag.loc[2020, 'new']:,.0f} (2020)",
        'bazara giriş deyil, fermerlərin inzibati qeydiyyatı (subsidiya sistemi); kənd təsərrüfatı paneldə saxlanılır, onun sabit effekti və 2020 dayanıqlıq yoxlaması verilir'),
 'F8': ('İş kitabı DVX: mikro vergi ödəyicisi sətirləri büdcə təşkilatı sətirlərini təkrarlayır', f'say, dövriyyə və daxilolmalar {len(_mic)} ildə eynidir: {"bəli" if _same else "xeyr"}',
        'mikro vergi ödəyiciləri ölçü qrupu konsentrasiyasından çıxarılır; Vergi Xidməti tərəfindən düzəldilməlidir'),
 'F9': ("DSK 1_1_en.xls: A bölməsinin sətri 'of which:' kimi adlanıb", 'kənd təsərrüfatı sətri yuxarı sətrin adını daşıyır', 'FR12 ölçü qrupu cədvəllərini bölmə nümunəsi ilə oxuyur və bölmə cəmlərini dərc olunmuş cəmlə yoxlayır'),
 'F10': ('Dövlət idarəetməsi (O) inzibati yenidənqurma ilə bağlı ləğvlər göstərir', '; '.join(f'{p} {y}: ləğv edilən {r.liq:.0f}, yeni {r.new:.0f}' for (p, y), r in _o.iterrows()),
         'O və U (ekstraterritorial) qeyri-bazar bölmələridir: rəqabət göstəricilərindən çıxarılır, cəmlərdə saxlanılır'),
 'F11': ('İş kitabının region vərəqləri DSK reyestrinin region məlumatına bərabərdir', 'statistik vahidlər, yeni və ləğv edilənlər: 2021, 2024 və 2025-də eynidir (5-ci hissədə yoxlanılıb)',
         '2021–2025 regional panel reyestr sırasıdır; regional giriş/çıxış onun üzərində modelləşdirilir'),
 'F12': ('Ölçü qrupu sayları (1_3) yalnız kommersiya təşkilatlarını əhatə edir', f'iri + orta + kiçik + mikro = {SIZE.sum().sum():,.0f}, statistik vahidlər 232 847 (1 iyul 2026)', 'ölçü qrupu konsentrasiya hədləri kommersiya təşkilatlarının saylarından istifadə edir'),
 'F13': ('Yanvar–iyun axınları tam il axınlarının yarısı deyil', f"2024-cü il I yarım: yeni {_h.loc[2024, 'new']:,.0f}, 2024 tam il: {REG_FY['new'][2024].sum():,.0f}", 'yarımillik fayllar yalnız təsviri monitorinq üçündür; modellər tam il axınlarından istifadə edir'),
 'F14': ('Reyestr üzrə ləğvlər sahibkarlıq subyektlərinin qeydiyyatdan çıxarılmasından xeyli azdır',
         f"reyestr üzrə çıxış əmsalı {REG_FY['liq'][2025].sum() / REG_FY['stock'][2025].sum() * 100:.2f}% (2025), qeydiyyatdan çıxma əmsalı {E006.loc[('TOT', 2024), 'dereg'] / E006.loc[('TOT', 2024), 'registered'] * 100:.2f}% (2024, 006)",
         'fəaliyyətsiz hüquqi vahidlər reyestrdə qalır: reyestr üzrə çıxış bazardan çıxışı azaldılmış göstərir; çıxış proqnozları 006-nın qeydiyyatdan çıxma sırasından istifadə edir'),
 'F15': ('KOS-un buraxılış payları (012) və milli hesablar buraxılışı fərqli bazalardan istifadə edir', 'təhsil və səhiyyədə pay milli hesablar buraxılışına tətbiq edildikdə KOS-un orta gəliri qanuni sinif tavanını aşır (bazada dövlət buraxılışı var)',
         'həmin qrup-illər üçün yuxarı hədd gəlir tavanlarını atır (tavansız supremum) və işarələnir'),
 'F16': ('2022-ci ildə ölkə üzrə qeydiyyatdan çıxarma dalğası', f'qeydiyyatdan çıxarılan subyektlər {_t.get(2020):,.0f} (2020), {_t.get(2022):,.0f} (2022), {_t.get(2023):,.0f} (2023)',
         'birdəfəlik inzibati təmizləmə: çıxış tənliklərində ümumi 2022 impuls dummy-si, nümunədən kənarda sıfır'),
 'F17': ('DSK 006-da versiyalar arasında tərif dəyişikliyi', f"2019–2020 versiyası: 'yeni yaradılmış' / 'ləğv edilmiş' müəssisələr (tapıldı: {'bəli' if 'newly created' in _h22 else 'xeyr'}); 2022+ versiyalar: 'yeni qeydiyyatdan keçmiş' / 'qeydiyyatdan çıxarılmış' (tapıldı: {'bəli' if 'newly registered' in _h25 else 'xeyr'})",
         'doğulma tənliyi qırılma termini daşıyır (2022-dən 1); çıxış yalnız 2022 impulsunu saxlayır (2023–2024 çıxış səviyyələri 2019–2020-yə yaxındır: davamlı qırılma görünmür)'),
 'F18': ('Yoxlamaların sayı zamanla əhatəni dəyişir', f"yoxlamaların cəmi {_ins.get(2015, np.nan):,.0f} (2015), {_ins.get(2019, np.nan):,.0f} (2019), {_ins.get(2020, np.nan):,.0f} (2020), {_ins.get(LAST_ACT, np.nan):,.0f} ({LAST_ACT}); "
         'Fövqəladə Hallar Nazirliyinin yanğın təhlükəsizliyi yoxlamaları 2020-dən, kommunal yoxlamalar (Azərişıq, Azəriqaz) 2021–2022-dən daxil olur',
         'yoxlamalar illər arasında müqayisəli deyil və erkən xəbərdarlıq balında istifadə olunmur; yalnız məlumat üçün verilir')}
assert set(FIND_AZ) == set(FINDINGS.id), 'every finding needs its Azerbaijani text'

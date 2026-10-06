# Risk paneli — qərar dəstək sistemi (MİİS §15.5.3, v2)

Risk bölməsinin bütün nəticələri bir brauzer səhifəsində: bu günün xülasəsi, risk reyestri və hər riskin tam təhlili,
monitor, paylanmalar, VaR / CaR, miqyaslanma, stress testləri, tədbirlər, CAEM, geriyə sınaq, hesabat qurucusu və
metodologiya. Bütün mətn Azərbaycan dilindədir. Dizayn, cədvəl / qrafik köməkçiləri, Excel / Word yazıcıları,
axtarış və tur MikroUnit İş panelindən **köçürülüb** (işləmə zamanı MikroUnit-dən heç nə yüklənmir).

## 1. Açmaq

| Necə | Nə işləyir |
|---|---|
| `panel/index.html` faylını brauzerdə açmaq (`file://`) | Hər şey — bütün nəticələr paketdədir. Canlı hesablama düymələri serveri başlatmaq üçün izah göstərir. |
| `RiskModel_Baslat.command` (macOS) / `RiskModel_Baslat.bat` (Windows) və ya `python3 api/server.py` → `http://127.0.0.1:8791/panel/` | Üstəlik: canlı stress testi, miqyaslanma (istənilən ölçü), portfelin yenidən optimallaşdırılması, məlumatın yenilənməsi, saxlanmış ssenarilər, server tərəfində Excel. |

Nişan (token): yuxarıdakı vəziyyət zolağında «Fayl rejimi / Server» düyməsi → «Server ayarları». Sınaq nişanı `demo-write`
(oxumaq üçün `demo-read`). Analiz çağırışlarından əvvəl panel serverin `status.analysis_ready` vəziyyətini yoxlayır və keş
isinənə qədər gözləyir.

## 2. Bölmələr

1. **Bu gün** — ən yüksək risklər, yeni xəbərdarlıqlar, dünəndən nə dəyişdi (skorlar, D7), bugünkü məlumatın rəsmi
   proqnozlara təsiri (D6), siqnallar (D5), baza mərkəzli vs canlı paylanma, risk balansı indeksi (C2), gündəlik qərar (S7).
2. **Reyestr** — R01–R19 (ailə, sahib, P, T, skor, prioritet, trend, qalıq skor), 5×5 istilik xəritəsi, xəbərdarlıqlar,
   skor tarixçəsi, göstəricilər və kanallar. Hər risk: `#/reyestr/R01` — tərif, göstərici və canlı dəyər, ehtimal üsulu,
   ötürmə kanalı və töhfələr, miqyaslanma əyrisi (S1), təsirlənən komponentlər (S4), parametrlər (S5), CAEM (C1/C3),
   tədbirlər (M1/M2), qalıq risk (FR3/M5), xəbərdarlıqlar və S7.
3. **Monitor** — axınlar (D2, vintaj arxivi, NFR2 jurnalı), bazar paneli (D4: AMB məzənnələri, uçot dərəcəsi, BFB, Brent,
   ARDNF, qlobal indekslər; sıra seçici; V2 amilləri), siqnallar (D5), proqnoz təsiri (D6 — modul / amil / il süzgəci),
   konsensus və model riski (D3).
4. **Paylanma** — qeyri-neft artımı, inflyasiya, büdcə, Brent 2026–2030: yelpik qrafiki və tam kvantil cədvəli hər iki
   baxışda; kanal töhfələri, GaR yoxlaması, yelpik qatları.
5. **VaR/CaR** — məruz qalmalar (V1, V1b), VaR / ES (V3, V4), geriyə sınaq və svetofor (V5, V6), X-risk altında və CaR
   (K1, K2), borc davamlılığı (K3), ARDNF adekvatlığı (K4) və CCA (K5, «təxmini» kimi işarələnib).
6. **Miqyas** — amil və ölçü sürgüsü (S1 şəbəkəsi + bugünkü sapma), bütün göstəricilərə təsir, cavab əyrisi,
   elastikliklər (S2), qeyri-xəttilik və hədd ölçüləri (S3), təsir xəritəsi (S4), parametrlər (S5), modellər arası (S6, C5);
   «Canlı hesabla».
7. **Stress** — S1–S8 (tədbirlə və tədbirsiz), ARDNF, alətlər, tarixi analoqlar; ssenari qurucusu (şoklar → server; oflayn
   təqribi baxış; saxla / aç / sil / JSON).
8. **Tədbirlər** — reyestr v2 və effektlər (M1, M2), portfel və səmərəli sərhəd (M3, M4; büdcə sürgüsü; yenidən
   optimallaşdırma), icra planı (Qant, status iş axını, M6), strategiya və qalıq risk (M7, M5), gündəlik qərar (S7).
9. **CAEM** — siqnallar (C1), risk balansı (C2), kateqoriyalar (C3), şok kitabxanası (C4, «Nazirlik CAEM modeli —
   müqayisə»), ötürmə müqayisəsi (C5), tapıntılar (C6).
10. **Sınaq** — NFR1 testləri n ilə; «yoxlanıla bilmir» ayrıca sayılır; kalibrləmə, PIT, GaR, erkən xəbərdarlıq.
11. **Hesabat** — şablonlar «Rəhbərlik üçün gündəlik xülasə» və «Analitik hesabat»; bölmələr, risklər, illər, baxışlar;
    Çap / PDF, Excel, Word (qrafiklərlə), CSV; şablonlar brauzerdə və JSON kimi.
12. **Metod** — `docs/*.md` sənədləri, mənbələr və vintajlar (D2, spine manifest, D1), bütün çıxışlar (harada
    göstərildiyi ilə), son icranın mərhələləri.

Hər cədvəldə: sütuna klik — sıralama, «süz…» — süzgəc, CSV və Excel ixracı. Ctrl K — axtarış. «?» — 1 dəqiqəlik tur.

## 3. Yenidən yığmaq

```bash
cd RiskUnit
python3 panel/build_panel.py            # ≈ 10 s
python3 panel/build_panel.py --verify   # + determinizm (ikinci yığım bayt-bayt eyni olmalıdır)
python3 panel/build_panel.py --shots    # + bütün səhifələrin ekran görüntüləri (1440 və 390 px), 0 JS xətası
node panel/_build/shots.mjs [--desktop] [--only reyestr]   # yalnız ekran yoxlaması → work/panel_shots/
```

Yığım bu yoxlamaları aparır və uğursuz olarsa **1** ilə çıxır:
1. **Tələb olunan fayllar** — paketə daxil olan hər çıxış faylı mövcud olmalıdır (yoxdursa siyahı və «run_all.py-ni işə salın»).
2. **Paketlər** — hər `data/*.js` faylının JSON hissəsi oxunur, hər JS faylı `node --check`-dən keçir.
3. **Sütun etiketləri** — hər cədvəl sütununun Azərbaycan dilində adı var (`i18n/columns_az.csv` → `js/labels.js`); adı olmayan yeni sütun xəbərdarlıq verir, adı ingiliscədirsə yığım dayanır.
4. **Keçidlər və marşrutlar** — `index.html` faylları, hər `#/…` marşrutunun səhifəsi, `../site`, `../docs`, `../api` keçidləri, mərkəz səhifəsi.
5. **Tamlıq** — kataloqdakı və `output/`-dakı hər fayl ya paneldə göstərilir (və bir səhifə onu oxuyur), ya da səbəbi ilə
   «gizli» siyahıdadır; hər riskin tərifi, skoru və təhlil səhifəsi var (`coverage_report.csv`).
6. **Tərcümə** — paketlərdə, JS sətirlərində, `index.html`-də və mərkəz səhifəsində ingiliscə mətn yoxdur (söz siyahısı;
   tərcümələr `i18n/az.csv`; qalanlar `i18n/untranslated.txt`). Nazirlik vərəqlərinin dırnaq içindəki adları sitat sayılır.

Digər modullar çıxışları yenidən yazarkən yığım faylı bir neçə dəfə yenidən oxumağa çalışır. Yeni sütun əlavə olunubsa,
onun adını `i18n/columns_az.csv`-yə əlavə edin; yeni çıxış faylı tamlıq yoxlamasında görünür — onu səhifəyə əlavə edin və ya
`_build/b_check.py` → `HIDDEN` siyahısına səbəbi ilə yazın.

Canlı funksiyaların uçdan-uca yoxlaması (server işləyərkən): `node panel/_build/live.mjs`; ixracların yoxlaması:
`node panel/_build/exports.mjs` (fayllar `work/panel_shots/exports/`).

## 4. Fayllar

| Yol | Nədir |
|---|---|
| `build_panel.py`, `_build/bcore.py`, `b_core.py`, `b_mon.py`, `b_tables.py`, `b_docs.py`, `b_names.py` | paketlərin yığımı |
| `_build/b_i18n.py`, `b_labels.py`, `b_check.py`, `b_hub.py` | tərcümə, sütun adları, yoxlamalar, mərkəz səhifəsi (`../index.html`) |
| `_build/cdp.mjs`, `_build/shots.mjs` | headless Chrome ekran yoxlaması |
| `data/*.js` | məlumat paketləri (`core`, `mon`, `var`, `meas`, `caem`, `nfr` — həmişə; `d4`, `v2`, `d6`, `s1`, `s2`, `scal`, `s4`, `c4lib`, `d1`, `docs` — lazım olanda) |
| `js/*.js`, `assets/*.css` | interfeys (çərçivəsiz; Plotly yerli fayldır) |
| `i18n/az.csv`, `i18n/columns_az.csv` | tərcümə cədvəli və sütun adları |

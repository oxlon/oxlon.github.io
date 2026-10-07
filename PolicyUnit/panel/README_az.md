# Siyasət paneli — qərar dəstək paneli (MİİS §15.5.4)

İqtisadi siyasətlərin təsir analizinin bütün nəticələri bir brauzer səhifəsində: ssenarilərin əsas nəticələri, ssenari
qurucusu, makro və mikro təsirlər, sektor (IO), sosial (mikrosimulyasiya), risklər və yan təsirlər, KPI ilə qiymətləndirmə,
metodların müqayisəsi, tarixi validasiya, hesabat qurucusu və metodologiya. Bütün mətn Azərbaycan dilindədir. Dizayn,
cədvəl / qrafik köməkçiləri, Excel / Word yazıcıları, axtarış və tur Risk panelindən (o isə MikroUnit İş panelindən)
**köçürülüb** — işləmə zamanı digər bölmələrdən heç nə yüklənmir.

## 1. Açmaq

| Necə | Nə işləyir |
|---|---|
| `panel/index.html` faylını brauzerdə açmaq (`file://`) | Hər şey — bütün nəticələr paketdədir; ssenari qurucusunda brauzerdə yoxlama və «təqribi baxış» (xətti miqyaslama, açıq işarələnib). |
| `SiyasetModel_Baslat.command` (macOS) / `SiyasetModel_Baslat.bat` (Windows) → `http://127.0.0.1:8792/panel/` | Üstəlik: serverdə yoxlama, hesablama (bütün mühərriklər), qaralama / rəsmi ssenari kimi saxlama, surət, rəsmiləşdirmə, KPI müqayisəsi, KPI dəstləri. |

Nişan (token): vəziyyət zolağında «Fayl rejimi / Server» → «Server ayarları». Sınaq nişanları: `demo-write` (yazmaq),
`demo-read` (yalnız oxumaq).

## 2. Bölmələr

1. **Başlanğıc** — bölmə nə edir, sürətli əməliyyatlar, KPI reytinqi və xərc-effektivlik, hər ssenari üçün kart: ÜDM,
   İQİ, işsizlik, formal iş yerləri, Gini, yoxsulluq, fiskal xərc — qısa / orta / uzun müddət; qısa izah; yan təsir sayı.
2. **Ssenari qurucusu** (NFR4) — alətlər kataloqu (ailə, vahid, hədlər, mühərriklər), ölçü, illər, hədəf, maliyyələşmə;
   yoxla / hesabla / saxla / surət / JSON; paketdəki nümunə ssenarilər.
3. **Makro və mikro** (FR1) — müddət nişanları, göstərici kartları, sübut səviyyəsi A–D, metodlar üzrə yollar (2031–2035
   uzun müddət ekstrapolyasiyası işarələnib), baza vs ssenari; mikro: sektorlar, FR12 bazar müvazinəti, FR5, regionlar.
4. **Sektorlar** (FR2) — təsirlənən sektorlar və % dəyişmə, multiplikatorlar, əlaqələr və açar sektorlar, rəqabətlilik,
   qiymət modeli, IO və MikroUnit müqayisəsi, IO cədvəlləri.
5. **Sosial** (FR3) — SİNTETİK zolağı; məşğulluq (ümumi və formal), desillər (qazanan / uduzan), Gini, yoxsulluq (3 xətt),
   fiskal təsir, baza.
6. **Risklər** (FR4) — yan təsirlər (ciddilik 1–4), avtomatik yan təsir ssenariləri, RiskUnit risk profili, tədbirlər,
   Sobol (ilk 3) və qeyri-müəyyənlik zolaqları; Risk panelinə keçid.
7. **KPI** (FR5) — kataloq, ≥ 5 KPI seçimi (məcburi) və çəkilər, reytinq, xərc-effektivlik, radar və matris.
8. **Metodlar** (NFR2) — eyni ssenari MikroUnit / CAEM / OxLon / IO / mikrosimulyasiya ilə, fərqlərin izahı.
9. **Validasiya** (NFR1) — hadisələr, proqnoz və fakt, siniflər, hökmlər, IO və mikrosimulyasiya sınaqları, sapma hesabatı.
10. **Hesabat** — iki şablon; ssenarilər, bölmələr, müddətlər; Çap / PDF, Excel, Word (qrafiklərlə), CSV.
11. **Metodologiya** — sənədlər, mənbələr və vintajlar, məlumat sorğuları, konfiqurasiya cədvəlləri, bütün çıxışlar, son icra.

## 3. Yenidən yığmaq

```bash
cd PolicyUnit
python3 panel/build_panel.py            # ≈ 3 s
python3 panel/build_panel.py --verify   # + determinizm (ikinci yığım bayt-bayt eyni)
python3 panel/build_panel.py --shots    # + bütün səhifələrin ekran görüntüləri (1440 və 390 px), 0 JS xətası
node panel/_build/shots.mjs [--desktop] [--only sosial]   # yalnız ekran yoxlaması → work/panel_shots/
node panel/_build/exports.mjs           # hesabat ixracları (xlsx, docx, csv) → work/panel_shots/exports/
node panel/_build/live.mjs              # server işləyərkən canlı funksiyalar
```

Yığım uğursuz olarsa **1** ilə çıxır: (1) tələb olunan çıxış faylları (`_build/b_data.py` → `REQUIRED`, `P4_REQUIRED`);
(2) hər paket oxunur, hər JS `node --check`-dən keçir; (3) hər cədvəl sütununun Azərbaycan dilində adı
(`i18n/columns_az.csv`); (4) marşrutlar, `../../RiskUnit`, `../../MicroUnit` və mərkəz səhifəsinin keçidləri; (5) tamlıq —
kataloqdakı hər fayl paneldə göstərilir və ya `_build/b_check.py` → `HIDDEN`-də səbəbi var, hər rəsmi ssenarinin P1 və P5
nəticəsi var (`coverage_report.csv`); (6) ingiliscə qalıq mətn yoxdur (`i18n/az.csv`, qalıqlar `i18n/untranslated.txt`).

Bütün KPI-ların matrisi (istənilən seçimlə yenidən reytinq üçün) yığım zamanı PolicyUnit-in öz `policyunit.kpi` modulu ilə
`P1_effects.csv`-dən hesablanır (yalnız oxuyur).

## 4. Fayllar

| Yol | Nədir |
|---|---|
| `build_panel.py`, `_build/bcore.py`, `b_data.py`, `b_docs.py` | paketlərin yığımı |
| `_build/b_i18n.py`, `b_labels.py`, `b_check.py`, `b_hub.py` | tərcümə, sütun adları, yoxlamalar, mərkəz səhifəsi (`../index.html`) |
| `_build/cdp.mjs`, `shots.mjs`, `exports.mjs`, `live.mjs` | headless Chrome yoxlamaları |
| `data/*.js` | paketlər: `core` (həmişə), `eff`, `io`, `soc`, `risk`, `cmp`, `val`, `docs` (lazım olanda) |
| `js/*.js`, `assets/*.css` | interfeys (çərçivəsiz; Plotly yerli fayldır) |

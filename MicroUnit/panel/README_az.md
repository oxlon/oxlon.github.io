# Mikro Model — İş paneli (v2)

Altı funksional tələbin (FR1, FR3, FR4, FR5, FR10, FR12) bütün nəticələri bir brauzer səhifəsində:
proqnozlar, tənliklər, dayanıqlıq, ssenari qurucusu və hesabat qurucusu. Bütün mətn Azərbaycan dilindədir.

## 1. Açmaq

| Necə | Nə işləyir |
|---|---|
| `panel/index.html` faylını brauzerdə açmaq (`file://`) | Hər şey, **ssenarinin yenidən hesablanması istisna olmaqla**. Saxlanmış ssenarilərin paketə daxil edilmiş nəticələrinə baxmaq olar. |
| `MikroModel_Baslat.command` (macOS) / `MikroModel_Baslat.bat` (Windows) və ya `python3 api/server.py` → `http://127.0.0.1:8790/panel/` | Hamısı, o cümlədən zəncirvari ssenari hesablaması, saxlama, silmə. |

Server başqa ünvanda və ya başqa nişanla (token) işləyirsə: «Ssenarilər» → «Server ayarları». Sınaq nişanı `demo-write`.

## 2. Bölmələr

* **Başlanğıc** — altı tələbin kartları (2025 → 2030, artım, dayanıqlıq xülasəsi) və əsas tapşırıqlar.
* **FR1 … FR12** — solda qruplar və komponentlər. Hər komponent: qrafik (doldurulmuş illər boş dairə və qırıq
  xəttlə), **2026–2030 cədvəli** (bütün ssenarilər: səviyyə, artım, 5–95 % zolağı), son faktiki illər, onu izah
  edən tənliklər (performans zolağı: R², düz. R², n, DW, kointeqrasiya p, Theil U, dayanıqlıq hökmü) və əmsallara
  həssaslıq (tornado). Həmçinin: «Ümumi baxış», «▦ Bütün komponentlər» (bütün FR bir cədvəldə), «▦ Qrupun cədvəli»,
  «ƒ Tənliklər» (bütün qiymətləndirmələr, variantlar daxil; süzgəclər) və «✓ Dayanıqlıq».
  Ünvanlar sabit identifikatorlarladır: `#/fr4/c/fr4:emp:agr`, `#/fr1/tenlik/FR1.C3_man`.
* **Tənliyin tam nəticəsi** (dialoq) — əmsallar (standart xəta, t, p, 95 % interval, sabitlənmiş/köməkçi hədlər),
  uyğunluq, diaqnostika, fərq forması və uyğunluq, məhdudiyyət testləri, rekursiv qrafik, bir ili çıxarmaqla
  aralıqlar, Chow, CUSUM, faktiki–qiymətləndirilmiş və qalıq qrafikləri, nümunədən kənar yoxlama, mətn nəticəsi (Kopyala).
* **Ssenarilər** — *Qurucu*: baza ssenarisi; hər modul üçün ekzogen fərziyyələr (il xanaları, «% tətbiq et»,
  «bərpa et»), əmsallar (təxmin ± standart xəta, 95 % interval sürgüsü, «interval xaricinə icazə» və xəbərdarlıq),
  alətlər; «Hesabla» → `/api/v1/scenarios/run` (FR1 → FR3, FR4, FR5, FR10 → FR12); nəticələr Əsas ilə müqayisədə
  (kafellər, qrafik, hər modulun bütün komponentləri üzrə 2026–2030 cədvəli və fərq); «Saxla», «JSON ixrac/idxal».
  *Saxlanmış ssenarilər*: aç, dublikat, sil, JSON. *Hazır ssenarilər*: Əsas / Mənfi / İslahat müqayisəsi.
* **Hesabat** — tələblər, komponentlər, ssenarilər (saxlanmış xüsusi ssenarilər daxil), illər, məzmun
  (cədvəllər, qrafiklər, tənliklər, dayanıqlıq, fərziyyələr, qeydlər); canlı görünüş; ixrac: **Çap / PDF**,
  **Excel** (Məlumat, Proqnoz (uzun), Proqnoz (geniş), Tənliklər, Fərziyyələr), **Word** (başlıqlar, cədvəllər,
  qrafiklər), **CSV**. Şablonlar brauzerdə saxlanılır və JSON kimi ixrac olunur.
* **Cədvəllər** — bütün komponentlər × ssenarilər bir cədvəldə; süzgəc, CSV, Excel.
* **Sintetik** — FR10/FR12 B qatı: model kartları, əmsallar, marjinal effektlər, ROC və kalibrləmə, sağ qalma,
  Boone, parametrlərin bərpası. Hər görünüşdə «SİNTETİK MƏLUMAT — real müəssisə məlumatı deyil» nişanı; modullar
  real fayl ilə icra olunduqda (`*_FIRM_econ_*`) avtomatik «REAL MƏLUMAT» nişanına keçir.

## 3. Yenidən yığmaq

```bash
cd MicroUnit
python3 panel/build_panel.py            # ~5 san.; run_all.py da bunu çağırır
python3 panel/build_panel.py --db PATH  # saxlanmış ssenariləri başqa API bazasından götürmək
```

Mənbələr (`output/`): `FRx_indicator_catalog.csv`, `FRx_forecast_tidy.csv`, `FRx_equations.json`,
`FRx_robustness_summary.csv`, `FRx_coef_sensitivity.csv`, `FRx_not_forecast.csv`, `FRx_strings_az.csv`,
`FR10_SYNTHETIC_econ_*`, `FR12_SYNTHETIC_econ_*`, `FR12_series_filled.csv`; mühərriklərin girişləri
(`microlib.engines.*.inputs()`); saxlanmış ssenarilər (`api/micro.db`, yalnız oxu) və `panel/scenarios/*.json`.

Yığım üç yoxlama aparır və uğursuz olarsa **1** ilə çıxır:
1. **Tamlıq** — hər kataloq komponenti hər ssenaridə 2026–2030 illərinin hamısını daşıyır
   (`panel/coverage_report.csv`; FR12 yanvar–iyun axınlarında 2026 faktiki dəyərdir və belə qeyd olunur).
2. **Keçidlər** — kataloqdakı tənlik id-ləri reyestrdə var, `index.html`-dəki fayllar və mərkəz səhifəsinin
   keçidləri mövcuddur, JS-dəki hər `#/…` marşrutunun səhifəsi var.
3. **Tərcümə** — paketlərdə, JS sətirlərində, `index.html`-də və mərkəz səhifəsində ingilis dilində mətn qalmayıb
   (söz siyahısı əsasında; siyahı `panel/i18n/untranslated.txt`-ə yazılır). Tərcümələr: `panel/i18n/az.csv`
   (`python3 panel/i18n/src/make_az.py` ilə `panel/i18n/src/rows_*.py`-dən yaradılır) + modulların `FRx_strings_az.csv`.

## 4. Fayllar

| Yol | Nədir |
|---|---|
| `build_panel.py`, `_build/p_tidy.py`, `p_eq.py`, `p_i18n.py`, `p_synth.py`, `p_synecon.py`, `p_inputs.py`, `p_meta.py`, `p_hub.py` | v2 yığım |
| `_build/p_fr*.py`, `pinfo.py`, `plabels.py` | v1 yığıcıları (istinad üçün saxlanılıb, istifadə olunmur; `p_fr10.py`-də pay xətası düzəldilib) |
| `data/*.js` | Məlumat paketləri (`eq_frX.js` tələb olunanda yüklənir) |
| `js/*.js`, `assets/*.css` | İnterfeys (çərçivəsiz; Plotly yerli fayldır) |
| `scenarios/*.json` | Paketə daxil edilən ssenari faylları (nümunə: Brent −20 %) |
| `i18n/az.csv` | Tərcümə cədvəli |

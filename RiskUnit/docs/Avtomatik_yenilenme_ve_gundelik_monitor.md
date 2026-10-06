# Avtomatik yeniləmə, Azərbaycan məlumat axınları və gündəlik proqnoz-təsir monitoru (RiskUnit v2)

Bu sənəd NFR2 (dəyişən şəraitə sürətli uyğunlaşma) üçün avtomatlaşdırmanın necə quraşdırıldığını, hansı
mənbələrin avtomatik toplandığını və gündəlik monitorun nəyi hesabladığını izah edir.

## 1. İki rejim

| Əmr | Nə edir | Müddət |
|---|---|---|
| `python3 update.py --daily` | Qlobal axınlar (FRED, GPR, EPU, USGS, ERA5) + Azərbaycan axınları → yuxarı axın anbarı (yalnız bölmələrdən biri yeni vintaj verəndə yenidən qurulur) → bölmələrarası konsensus → gündəlik monitor (D2, D4–D7) | ≈ 1–2 dəq |
| `python3 update.py --full` | `--daily` + tam risk boru xətti (FR1–FR4, NFR1, hesabatlar, sayt) | ≈ 3–6 dəq |
| `python3 update.py --daily --backfill 600` | Eyni, üstəlik AMB məzənnə arxivinin 600 bülletenə qədər doldurulması | ≈ 12 dəq |

Bütün yükləyicilər: vaxt limiti ≤ 20 san, eyni sayta saniyədə ən çox 1 sorğu, xam cavab
`data/vintages/<mənbə>/<tarix>/` altında saxlanılır, uğursuz yükləmədə son uğurlu nüsxə istifadə olunur,
status `output/D2_feed_status.csv`-də qeyd edilir. `RISK_NO_NETWORK=1` — şəbəkəsiz rejim (yalnız keş).

## 2. Cədvəl (quraşdırma)

Yollar **əl ilə yazılmır**: `scheduler/run_update.sh` və `scheduler/run_update.bat` RiskUnit qovluğunu öz
yerlərindən müəyyən edir; `scheduler/install.py` launchd/cron üçün lazım olan mütləq yolları bu qovluqdan
avtomatik çıxarır. Qovluq köçürüləndə yalnız `install.py`-ı yenidən işlətmək kifayətdir.

Vaxtlar (serverin yerli vaxtı, Bakı): **06:30 `--full`**, **13:30 və 18:30 `--daily`** (AMB növbəti günün
rəsmi məzənnəsini günorta elan edir; DSK buraxılışları 10:00–17:00 arasıdır).

### macOS (launchd)
```bash
cd RiskUnit
python3 scheduler/install.py --install      # plist-ləri yaradır, ~/Library/LaunchAgents-ə köçürür və yükləyir
launchctl list | grep az.miis.risk           # yoxlama
python3 scheduler/install.py --uninstall    # silmək
```
Qeyd: qovluq Google Drive-dadırsa, macOS «Tam diskə giriş» (Full Disk Access) icazəsini `/bin/sh` üçün tələb edə
bilər (Sistem Ayarları → Məxfilik və Təhlükəsizlik). Jurnal: `output/NFR2_cron.log`, `output/NFR2_launchd.log`.

### Linux (cron)
```bash
python3 scheduler/install.py                 # scheduler/crontab.txt bu serverin yolları ilə yaradılır
crontab -l | cat - scheduler/crontab.txt | crontab -
```

### Windows (Task Scheduler)
```bat
cd D:\...\RiskUnit
python scheduler\install.py                  REM Windows-da işlədildikdə XML-lərə qovluq yolu avtomatik yazılır
schtasks /Create /TN "MIIS_Risk_full"  /XML "scheduler\windows_task_full.xml"
schtasks /Create /TN "MIIS_Risk_daily" /XML "scheduler\windows_task_daily.xml"
```
XML-lər macOS-da yaradılıbsa, `%MIIS_RISK_DIR%` dəyişənindən istifadə edir: `setx MIIS_RISK_DIR "D:\...\RiskUnit"`.
Python: `MIIS_PYTHON` dəyişəni → `.venv` → `~/venvs/miis-model` → sistem `python3`.

Eyni anda iki yeniləmə işləmir (`output/.update.lock`). Hər dövr `output/NFR2_update_log.csv`-yə yazılır.

## 3. Avtomatik Azərbaycan axınları (`riskunit/feeds_az.py`)

| Axın | Mənbə | Nə götürülür | Tezlik |
|---|---|---|---|
| `cbar_fx` | AMB rəsmi bülleteni `cbar.az/currencies/GG.AA.İİİİ.xml` | bütün valyutalar və bank metalları (USD, EUR, RUB, TRY, GBP, CNY, XAU …), 1 vahid üçün AZN; arxiv: 2015-dən hər ayın 1-i, son 2 il hər iş günü | gündəlik |
| `cbar_rate` | `cbar.az/infoblocks/corridor_*?year=` və «Pul siyasəti qərarları» | uçot dərəcəsi, dəhlizin aşağı/yuxarı həddi (2010+), qərar tarixləri və dəyişmə (f.b.) | hadisə |
| `dsk_macro` | DSK «Aylıq makroiqtisadi göstəricilər» (son 10 ay) | ÜDM, neft-qaz və qeyri-neft ÜDM, sənaye, kənd təsərrüfatı, pərakəndə ticarət, investisiya, dövlət büdcəsinin gəlir/xərc/profisiti, strateji valyuta ehtiyatları, xarici dövlət borcu, kredit, depozit, gəlirlər, əmək haqqı, İQİ, xarici ticarət (Yanvar–ay, ötən ilin eyni dövrünə %) | aylıq |
| `dsk_cpi` | DSK istehlak qiymətləri buraxılışı | İQİ aylıq və illik, ərzaq/qeyri-ərzaq | aylıq |
| `dsk_tables` | DSK `.xls` cədvəlləri (MicroUnit-in DSK yükləmə qaydası: brauzer UA, BIFF yoxlaması) | 001_1 (illik artım indeksləri), 03qua (rüblük ÜDM, nominal və sabit qiymətlərlə) | rüblük |
| `minfin` | Maliyyə Nazirliyi «Təsdiq olunmuş dövlət büdcəsinin əsas göstəriciləri» | təsdiq olunmuş/faktiki dövlət büdcəsi gəlirləri; son operativ icra hesabatının rübü | illik |
| `sofaz` | ARDNF «Son rəqəmlər» + rüblük investisiya nəticələri (PDF) | aktivlər, valyuta və aktiv sinfi bölgüsü, qızıl (ton, pay) | rüblük |
| `bfb` | Bakı Fond Birjası press-relizləri | Maliyyə Nazirliyinin istiqrazları və AMB notları üzrə hərraclar: orta/kəsmə gəlirlilik, həcm, tələb, müddət | hadisə |
| `azeri_light` | **Pulsuz ictimai Azeri Light sırası yoxdur** → proksi: FRED Brent + spred | spred = MicroUnit FR1 neft ixrac qiyməti − Brent illik ortası, 2015–2025 medianı (sənədləşdirilmiş) | gündəlik |

Qeyd: Brent fyuçers əyrisi üçün pulsuz, sabit mənbə tapılmadı (sorğu limitləri); monitor buna görə «bugünkü səviyyə
saxlanılarsa» şərti yolundan istifadə edir. Maliyyə Nazirliyinin aylıq büdcə icrası maşınla oxunan formada dərc
edilmir — aylıq icra DSK cədvəlindən, illik plan isə Nazirliyin Bottom-up modelindən (base 60) götürülür.

### 3a. Axın statusu, təzəlik qaydaları və mərhələ statusu (v2.4, audit M8)

**Problem (06.10.2026 canlı dövrü):** 9 qlobal axının hamısı `URLError` ilə uğursuz oldu (hər biri ≈ 30 s, cəmi 4,5 dəq),
lakin A1 mərhələsi «ok» və `ugursuz = []` göstərildi; `dsk_tables` 188 günlük olsa da «təzə» idi; `cbar_rate` bir blokda
2026-02-05, digərində 2026-09-24 göstərirdi. Səbəb təkrarlanmadı: həmin URL-lər 00:35, 00:40 UTC və bu düzəlişdən sonra
canlı yoxlamada (urllib standart UA, FRED üçün başlıqsız sorğu; 9 axın 22 s-də) işləyir — keçici şəbəkə/DNS kəsintisi.

* **Səbəb mətni** statusda saxlanılır (`xeta: URLError: <səbəb>`); bağlantı səviyyəsində xətada bir təkrar (2 s), sonra
  host 10 dəqiqəlik «ölü» siyahıya düşür (qalan sorğular dərhal `HostDown` — 4,5 dəqiqəlik gözləmə olmur).
* **Təzəlik qaydası hər axın üçün** (`feeds_az.FEED_RULES`): dövr sonu (gün/ay/rüb/il) + dövr uzunluğu + dərc gecikməsi
  = növbəti müşahidənin gözlənilən tarixi; həmin tarixədək «təzə», + güzəşt müddətinədək «köhnəlir», sonra «köhnə»
  (`max_yas_gun`). Rüblük DSK cədvəlləri rübün SONUNDAN sayılır (II rüb 2026 → 98 gün, növbəti gözlənilən 28.11.2026).
* **Səviyyə:** nüvə axınlar (Brent, AMB məzənnəsi, AMB uçot dərəcəsi, DSK aylıq və İQİ) uğursuz və ya köhnə → **xəta**;
  digər axınların uğursuzluğu, köhnəlməsi → **xəbərdarlıq**; şəbəkəsiz rejim (RISK_NO_NETWORK) uğursuzluq deyil.
  D2-də yeni sütunlar: `seviyye`, `nuve`, `son_hadise`, `dovr_sonu`, `yas_dovr_sonundan_gun`, `novbeti_gozlenilen`,
  `max_yas_gun`, `tazelik_qaydasi`, `son_cehd_utc`.
* **Mərhələ statusu:** `run_all.Runner(..., check=)` axın səviyyələrini A1/A2/G0 mərhələsinə ötürür
  (`ok` / `xəbərdarlıq: …` / `xəta: …`); `_run_summary_v2.json`: `ugursuz` = xəta səviyyəli mərhələlər,
  `xeberdarliq_merheleleri` = xəbərdarlıqlar; `update.py` statusu «qismən: mərhələ xətası A1» olur və çıxış kodu 1-dir.
  Yükləmə olmayan dövrdə də A1 saxlanılmış qlobal vintajların təzəliyini yoxlayır.
* **Vahid həqiqət mənbəyi:** xülasədəki bütün tarixlər D2-dən gəlir: `son_musahide` = əsas dəyərin tarixi (məs. uçot
  dərəcəsi 6,50% 05.02.2026-dan qüvvədədir), `son_hadise` = axının ən yeni tarixi (23.09.2026 qərarı, 24.09.2026 dəhliz).
* `minfin` «köhnə» (xəbərdarlıq): MN səhifəsində 2026 büdcəsi xlsx cədvəli kimi dərc olunmayıb (yalnız 27.12.2024 faylları).

## 4. Gündəlik monitor (`riskunit/monitor.py`)

* **D5_daily_monitor.csv** — hər göstərici üçün son dəyər və tarix, bölmələrin baza fərziyyəsi (OxLon, FR1, CAEM,
  Bottom-up, BVF), sapma, z-skor və siqnal. z = sapma / σ; σ — bölmənin öz tarixi proqnoz xətası (OxLon
  `validation_backtest` h=1 RMSE; Brent üçün log-RMSE × səviyyə), olmadıqda tarixi standart kənarlaşma.
  Siqnal: |z| < 1 «normal», 1–2 «diqqət», ≥ 2 «xəbərdarlıq».
* **D6_forecast_impact.csv** — sapmanın proqnozlara ötürülməsi: (1) MicroUnit zənciri `chain.run_chain`
  (FR1 → FR3/FR4/FR5 → FR10 → FR12, bütün komponentlər) — Brent və uçot dərəcəsi yolu FR1 ekzogen fərziyyəsini
  əvəz edir; (2) FR1 multiplikatorları ilə xətti yoxlama; (3) OxLon-un Brent lo80/hi80 ssenarilərindən cari hesab
  elastikliyi; (4) müşahidə hesabı (Yanvar–ay faktiki + son temp), büdcə icra tempi, ARDNF-in qızıl və EUR
  yenidənqiymətləndirməsi. «Nəticə» yolu şərti ssenaridir, risk bölməsinin öz proqnozu deyil.
* **D7_changes.csv** — əvvəlki günə nisbətən nə dəyişdi: göstərici və siqnal dəyişmələri, əsas proqnoz
  təsirlərinin dəyişməsi, yeni məlumat vintajları. Gündəlik nüsxələr `output/monitor_history/`-dədir.

## 5. Yuxarı axın anbarı və konsensus

* `riskunit/upstream.py` — üç bölmənin bütün sıraları bir tidy anbarda (`data/upstream/upstream_tidy.csv.gz`),
  sabit identifikatorlarla: `mx:` (OxLon), `mn:` (Nazirlik: base 60, 8 vərəq, CAEM baza səviyyələri, EViews),
  `fr<k>:` (MicroUnit FR1–FR12). Kataloq: `output/D1_upstream_catalog.csv`. Anbar mənbə fayllarının SHA-256 heşi
  dəyişəndə avtomatik yenidən qurulur. Makro yol: `Macro_OxLon/delivery` (köhnə `18august/model` ilə bayt-bayt eyni).
* `riskunit/consensus.py` — 14 əsas dəyişən üzrə 2025–2030 baza proqnozlarının müqayisəsi
  (`D3_consensus_baselines.csv`): yayılma (maks − min), fikir ayrılığı indeksi (mənbələr arası sd / tarixi sd) və
  bayraqlar: **qeyri-real** (fiziki hədd xaricində və ya məlum qüsur — məs. Bottom-up İQİ sətri ticarət deflyatoru
  ilə eynidir, CAEM ehtiyatları mənfiyə düşür), **köhnəlmiş** (2025 üçün faktiki ilə uyğun gəlməyən köhnə proqnoz),
  **kənar dəyər** (digər mənbələrin medianından 3·MAD-dan çox). Model riski göstəricisi `D3_model_risk.csv` —
  reyestr üçün təklif: «Proqnoz qeyri-müəyyənliyi / model riski».

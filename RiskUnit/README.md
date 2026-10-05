# MİİS §15.5.3 — İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi

Risk bölməsi makro model (§15.5.1, `../../18august/model`) və mikro bölmə (§15.5.2, `../MicroUnit`) üzərində
qurulur: onların mərkəzi yolu ətrafında risk paylanmasını hesablayır, riskləri ehtimal × təsir üzrə
prioritetləşdirir, tədbirləri izləyir və nəticəni rəhbərliyə və analitiklərə rol əsasında təqdim edir.
Metodologiya: [`docs/Risk_Metodologiyasi.md`](docs/Risk_Metodologiyasi.md).

## İşə salma

```bash
pip install -r requirements.txt
python3 run_all.py --fetch          # canlı axınları yüklə + tam boru xətti
python3 run_all.py                  # saxlanılmış axınlarla (oflayn)
python3 update.py                   # NFR2: dəyişiklik varsa skorları yenilə (cədvəldən çağırılır)
python3 update.py --watch 30        # 30 dəqiqədən bir yerli girişləri izlə
python3 -m unittest discover -s tests -v
```

Yuxarı axın qovluqları başqa yerdədirsə: `MIIS_MACRO_DIR=/yol/model MIIS_MICRO_DIR=/yol/MicroUnit python3 run_all.py`.
Gündəlik cədvəl: `scheduler/` (macOS launchd, Linux cron, Windows Task Scheduler).

## Qovluqlar

| Qovluq | Məzmun |
|---|---|
| `input/` | Nazirliyin redaktə etdiyi fayllar: risk reyestri, tədbirlər reyestri, hədlər və risk iştahı, rollar, hadisə xronologiyası |
| `riskunit/` | kod paketi: `spine` (məlumat onurğası), `feeds` (canlı axınlar və vintaj arxivi), `factors` (FR1), `simulate` (FR2 birgə simulyasiya), `scoring` (FR2 skor və xəbərdarlıq), `measures` (FR3), `backtest` (NFR1), `report` və `charts` (FR4/NFR3), `docs` |
| `data/vintages/` | hər axının yüklənmiş vintajları və `manifest.csv` (URL, vaxt, SHA-256) |
| `output/` | bütün nəticə CSV-ləri, `risk_api.json`, real vaxt proqnoz arxivi, NFR1 reyestri, NFR2 jurnalı |
| `site/` | `index.html` — rəhbərlik paneli; `analitik.html` — analitik paneli |
| `reports/` | PDF və Excel hesabatları, hər rol üçün |
| `tests/` | FR1–FR4, NFR1–NFR3 qəbul meyarları üzrə avtomatik testlər |
| `scheduler/` | NFR2 cədvəl faylları |

## Nazirliyin dəyişə biləcəyi parametrlər (kod dəyişmədən)

- `input/hedler.csv` — ehtimal və təsir pillələri, prioritet hədləri, risk hədləri, kalibrləmə fərziyyələri.
- `input/risk_reyestri.csv` — risklərin siyahısı, sahibi, ekspert örtükləri; `aktiv=0` riski söndürür.
- `input/tedbirler_reyestri.csv` — tədbir, məsul, müddət, status; status dəyişikliyi tarixçəyə avtomatik yazılır.
- `input/rollar.csv` — hansı bölmənin hansı rola göstərildiyi.
- `input/hadise_xronologiyasi.csv` — yeni hadisənin qeydə alınması.

Hər dəyişiklik növbəti `update.py` dövründə (≤ 30 dəqiqə izləmə rejimində, ≤ 24 saat cədvəllə) skorlara düşür.

## Əsas çıxışlar

| Fayl | Tələb |
|---|---|
| `output/FR1_indicator_base.csv`, `FR1_transmission_channels.csv`, `FR1_event_chronology.csv`, `FR1_hazard_parameters.csv` | FR1 |
| `output/FR2_risk_scores.csv`, `FR2_heatmap.csv`, `FR2_distribution.csv`, `FR2_contributions.csv`, `FR2_alerts.csv`, `FR2_score_history.csv` | FR2 |
| `output/FR3_measures_register.csv`, `FR3_coverage.csv`, `FR3_residual_risk.csv`, `FR3_status_history.csv`, `FR3_stress_scenarios.csv`, `FR3_levers.csv`, `FR3_historical_analogues.csv` | FR3 |
| `site/*.html`, `reports/*.pdf`, `reports/*.xlsx`, `output/risk_api.json` | FR4, NFR3 |
| `output/NFR1_backtest_register.csv`, `NFR1_calibration.csv`, `forecast_archive/` | NFR1 |
| `output/NFR2_update_log.csv`, `data/vintages/manifest.csv` | NFR2 |

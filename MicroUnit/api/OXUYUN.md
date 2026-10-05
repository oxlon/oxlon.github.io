# Mikroiqtisadi modulun məlumat API-si və avtonom icra — MİİS §15.5.2

Mikroiqtisadi modulun (FR1, FR3, FR4, FR5, FR10, FR12) məlumatını yeniləmək, modelləri yenidən icra
etmək və nəticələri Nazirliyin sistemlərinə ötürmək üçün interfeys. Makro modulun API-si ilə eyni
qaydada qurulub: yalnız Python standart kitabxanası, SQLite, `API_TOKENS` ilə oxu/yazı nişanları.

* **Yükləmək** — yeni iş kitabı, DSK cədvəlləri, FR10 müəssisə paneli, FR12 biznes reyestri, müşahidələr.
  Hər fayl dəftərlərin öz qaydaları ilə yoxlanılır; səhvlər sətir və sahə üzrə qaytarılır.
* **İcra etmək** — `run_all.py` dəftərləri asılılıq qrafı üzrə icra edir və paneli/saytı yenidən yığır.
* **Oxumaq** — proqnozlar, tənliklər, vəziyyət; ssenari hesablamaları və Excel hesabatı.
* **Avtonom rejim** — qovluğa atılan fayl özü yoxlanılır, tətbiq olunur və icra başlayır.

---

## 1. İşə salmaq

Python 3.10+ (layihənin mühiti: numpy, pandas, scipy, statsmodels, openpyxl, xlrd, nbconvert, ipykernel — dəftərlər və
ssenari mühərrikləri bunları tələb edir). Başladıcı Python-u bu ardıcıllıqla seçir: `MIKRO_PYTHON` dəyişəni →
layihədəki `.venv` → `~/venvs/miis-model` → `python3`; paketlər yoxdursa xəbərdarlıq verir.

```bash
cd MicroUnit
python3 api/server.py                 # http://127.0.0.1:8790/panel/
```

və ya iki kliklə: **`MikroModel_Baslat.command`** (macOS) / **`MikroModel_Baslat.bat`** (Windows) —
serveri başladır və brauzerdə `http://127.0.0.1:8790/panel/` açır.

| Ünvan | Nədir |
|---|---|
| `/` | Mərkəz səhifəsi (`index.html`) |
| `/panel/` | İş paneli |
| `/site/` | Klassik görünüş (metodologiya) |
| `/api/v1/...` | JSON API (aşağıda) |

Yoxlama: `curl http://127.0.0.1:8790/api/v1/health`

## 2. Nişanlar (tokens)

```bash
export API_TOKENS="mikro-oxu:read,mikro-yaz:write"
export API_ORIGINS="localhost"        # standart: yalnız localhost / 127.0.0.1 brauzer mənbələri; "*" — hamısı
python3 api/server.py --host 0.0.0.0 --port 8790
```

* `read` — bütün GET sorğuları; `write` — POST/DELETE (yükləmə, tətbiq, icra, ssenari). `write` `read`-i də əhatə edir.
* Standart sınaq nişanları `demo-read`, `demo-write` — server başlayanda xəbərdarlıq çap edir və onlarla
  şəbəkəyə (`--host 0.0.0.0`) açılmaqdan imtina edir. **İstehsalda mütləq dəyişdirin.**
* `/api/v1/health` və `/api/v1/openapi.yaml` nişansızdır; statik səhifələr (`/panel/`, `/site/`) da.

## 3. Məlumat yükləmək

İki addım: **yükləmə + yoxlama** (`POST /api/v1/uploads`), sonra **tətbiq** (`POST /api/v1/uploads/{id}/apply`).
Fayl `data/inbox/<upload_id>/` altında saxlanılır, yoxlama hesabatı `validation.json` faylında da qalır.

```bash
T="Authorization: Bearer mikro-yaz"
# xam gövdə — ad faiz kodlaması ilə
curl -X POST -H "$T" -H "X-Kind: firm_panel" -H "X-Filename: FR10_firm_panel.csv" \
     --data-binary @FR10_firm_panel.csv http://127.0.0.1:8790/api/v1/uploads
# eyni, multipart/form-data ilə
curl -X POST -H "$T" -F kind=firm_panel -F file=@FR10_firm_panel.csv http://127.0.0.1:8790/api/v1/uploads
```

Cavab: `201` — qəbul edildi, `422` — rədd edildi; hər iki halda `validation` hesabatı:
`ok`, `errors` / `warnings` (sətir, `firm_id`, il, sahə, qayda, Azərbaycan dilində mesaj), `summary`,
`target` (faylın yazılacağı yer), `affected_stages` (yenidən icra ediləcək modullar).

| `kind` | Fayl | Yoxlama | Hədəf (dəftərlərin oxuduğu yol) | İlk mərhələ |
|---|---|---|---|---|
| `workbook` | `Statistik data dinamika *.xlsx` | FR1 VARMAP (196 ünvan), FR3 WAGEMAP (50), FR4/FR5/FR12 `wb_rows` ünvanları — ad, vahid, il başlıqları, vərəqlər | `data/Statistik data dinamika 05.06.2026 +.xlsx` | FR1 (hamısı) |
| `dsk` | DSK `.xls` (+ `subfolder`) | BIFF formatı (HTML səhifə deyil), dəftərin oxuduğu vərəqlər, əvvəlki faylın vərəqləri | `data/<subfolder>/<fayl>` | dsk→FR4, dsk_services→FR5, dsk_enterprise/*→FR10, dsk_competition/*→FR12 |
| `firm_panel` | `.csv` və ya `.xlsx` (`data` vərəqi) | FR10 validatoru: məcburi sütunlar, ədədlər, mənfi dəyərlər, təkrar müəssisə-il, NACE, region, mülkiyyət, balans bərabərliyi və s. | `data/firm_panel/FR10_firm_panel.csv` / `.xlsx` | FR10 |
| `business_register` | `.csv` və ya `.xlsx` | FR12 validatoru (17 qayda) | `data/business_register/FR12_business_register.csv` / `.xlsx` | FR12 |
| `series` | JSON müşahidələr | modul, kod (kataloq varsa), il 1990–2100, ədəd | SQLite (`GET /api/v1/observations`) | — |

Qeydlər:
* DSK üçün `subfolder` göstərilməyibsə fayl adından tapılır (mövcud fayllar, FR4/FR5 siyahıları, FR10/FR12
  manifestləri). Eyni ad bir neçə bölmədə varsa (məs. `013en.xls`) — `subfolder` mütləqdir:
  `dsk`, `dsk_services`, `dsk_enterprise/{industry,entrepreneurship,st_units,nat_accounts}`, `dsk_competition/{current,vintages}`.
* Bütün sətirlərində sintetik nişan (`SYNTHETIC — not real enterprise data`) olan panel/reyestr rədd edilir.
  `*_SYNTHETIC*` və `*_TEMPLATE*` fayllarının üzərinə **heç vaxt** yazılmır.
* `series` formatı makro API ilə eynidir:
  `{"actor": "dsk", "source": "DSK 2025", "items": [{"id": "fr1:rgdp", "period": 2025, "value": 101.5}]}`
  (`id` əvəzinə `module` + `code` də olar). Bu müşahidələr hələlik dəftərlərin girişi deyil — MİİS ilə mübadilə üçün saxlanılır.

**Tətbiq:** `POST /api/v1/uploads/{id}/apply` (`?run=1` — sonra ilk təsirlənən mərhələdən icra; yükləmədə
`?apply=1&run=1` hər üç addımı birləşdirir). Əvəz olunan fayl `data/_replaced/<vaxt>_<id>/` altına köçürülür
(orada `manifest.json` — köhnə və yeni sha256). Geri qaytarmaq üçün həmin faylı yerinə köçürün və ya yenidən yükləyin.
İcra gedərkən tətbiq mümkün deyil (`409`) — giriş faylları icranın ortasında dəyişmir.
Real panel tətbiq olunduqdan sonra `/status` → `data_modes.FR10.rerun_needed = true` — FR10 icra edilənə qədər.

## 4. Avtonom rejim

```bash
python3 api/server.py --watch data/inbox_drop --auto-run --poll 30 --schedule 06:30 --dsk-refresh --snapshot
```

* **`--watch QOVLUQ`** — qovluq hər `--poll` saniyədə yoxlanılır. Kopyalanması bitmiş fayl (iki yoxlama arasında
  ölçüsü dəyişməyən) adına görə təsnif edilir: `Statistik data dinamika*.xlsx` → workbook, `FR10_firm_panel*.csv|xlsx`
  → firm_panel, `FR12_business_register*` → business_register, `*.xls` → dsk, `*.json` → series. DSK faylını alt
  qovluğa qoymaq olar: `inbox_drop/dsk_services/007_1en.xls`. Google Drive-ın `Icon` faylları, `~$…` və yarımçıq
  (`.part`, `.crdownload`) fayllar nəzərə alınmır.
* Qəbul edilən fayl tətbiq olunur və `inbox_drop/_applied/` altına köçürülür; **`--auto-run`** ilə ilk təsirlənən
  mərhələdən icra başlayır (bir neçə fayl birlikdə gəlsə, mərhələlər birləşdirilir). Rədd edilən fayl
  `inbox_drop/_rejected/` altına köçürülür, yanında `<ad>.report.txt` (Azərbaycan dilində) və `<ad>.report.json`.
* İcra gedərkən yeni fayllar tətbiq edilmir — icra bitdikdən sonrakı yoxlamada işlənir; icra tələbi növbəyə düşür.
* **`--schedule HH:MM`** — hər gün həmin vaxtda tam icra. **`--dsk-refresh`** ilə birlikdə: əvvəl DSK yenilənir
  və icra **yalnız dəyişiklik olduqda**, təsirlənən mərhələlərdən başlayır. `--schedule` olmadan `--dsk-refresh`
  başlanğıcda və hər `--dsk-refresh-hours` (24) saatda bir işləyir.
* **DSK yeniləməsi** `output/FR10_dsk_manifest.csv`, `output/FR12_dsk_manifest.csv` (yalnız «DSK current»; arxiv
  versiyaları dəyişmir) və FR4/FR5 dəftərlərindəki yükləmə siyahılarındakı ~130 faylı brauzer User-Agent-i ilə
  (60 s vaxt limiti) endirir, sha256 ilə müqayisə edir, dəyişən faylın köhnəsini `data/_replaced/<vaxt>_dsk-refresh/`
  altına saxlayır. Əl ilə: `POST /api/v1/dsk/refresh?run=1`. Vəziyyət: `GET /api/v1/autonomous`.
* Serveri kompüter açılanda başlatmaq üçün macOS-da `launchd`, Windows-da «Task Scheduler» istifadə edin
  (əmr yuxarıdakı kimi, işçi qovluq — `MicroUnit`).

## 5. İcra və izləmə

```bash
python3 run_all.py                    # FR1 → FR3 → FR4 → FR5 → FR10 → FR12 → panel → sayt
python3 run_all.py --stage FR4        # FR4 və asılıları (FR10, FR12) + panel/sayt
python3 run_all.py --only FR5 --skip-build
python3 run_all.py --dry-run          # icra etmədən: plan, girişlər, asılılıq yoxlaması
python3 run_all.py --list             # asılılıq qrafı və dəftərlərdə tapılan read_csv oxumaları
python3 run_all.py --snapshot --keep 5 --timeout 3600 --kernel python3
```

Asılılıqlar: FR3 ← FR1; FR4 ← FR1, FR3; FR5 ← FR1; FR10 ← FR1, FR3, FR4; FR12 ← FR1, FR10 (hər icrada
dəftərlərin kodu ilə yoxlanılır, fərq olarsa xəbərdarlıq). Hər dəftər `jupyter nbconvert --to notebook --execute
--inplace` ilə icra olunur. **İlk xətada dayanır** — asılı mərhələlər köhnə girişlərlə icra edilmir («skipped»).
Eyni anda yalnız bir icra (`logs/.run_all.lock`).

Kernel: standart `miis-model` (layihə mühiti). Bu kernel kompüterdə qeydiyyatda deyilsə, `run_all.py` xəbərdarlıq
verib standart `python3` kernel-ə keçir. Layihə mühitini qeydiyyatdan keçirmək üçün:
`python3 -m ipykernel install --user --name miis-model` (və ya `MICRO_KERNEL=<ad>`).

API ilə:

```bash
curl -X POST -H "$T" -H "Content-Type: application/json" -d '{"stage":"FR10"}' http://127.0.0.1:8790/api/v1/runs
curl -H "Authorization: Bearer mikro-oxu" http://127.0.0.1:8790/api/v1/runs/r20261005-103352-65ad
curl -X POST -H "$T" http://127.0.0.1:8790/api/v1/runs/r20261005-103352-65ad/cancel
```

`GET /runs/{id}`: `status` (running, ok, failed, cancelled, dry-run), `percent`, `progress.steps` (hər mərhələ:
status, saniyə, xəta), `log_tail` və `stage_log_tail` (cari və ya uğursuz mərhələnin jurnalının sonu). Başqa icra
gedərkən yeni icra — `409`.

`logs/<run_id>/`: `run.log`, `FRx.log` / `panel.log` / `site.log`, `progress.json`, **`manifest.json`** — mərhələlər,
vaxtlar, girişlərin sha256-sı (iş kitabı, DSK faylları, yuxarı axın CSV-ləri, dəftər kodunun sha256-sı),
çıxışların md5-i, xətalar və `reproducibility`: əvvəlki uğurlu icra ilə **bayt-bayt müqayisə** (`identical`,
dəyişən fayllar). `logs/history.jsonl` — bütün icraların siyahısı. `--snapshot` — uğurlu icradan sonra `output/`
surəti `output/vintages/<run_id>/` altında (son `--keep` qədəri saxlanılır).

Diqqət: FR1–FR5 dəftərləri çıxışı mütləq yolla (`…/MicroUnit/output`) yazır — dəftərləri başqa qovluğa
köçürüb icra etmək həmin qovluğun deyil, əsas `output/`-un üzərinə yazar.

## 6. Ssenarilər

```bash
curl -H "Authorization: Bearer mikro-oxu" "http://127.0.0.1:8790/api/v1/scenarios/inputs?module=FR1"
curl -X POST -H "$T" -H "Content-Type: application/json" http://127.0.0.1:8790/api/v1/scenarios/run -d '{
  "overrides": {"FR1": {"exogenous": {"fr1:brent": {"pct": -20}}}}, "scenario": "Baseline", "name": "Neft −20%"}'
```

`run_chain` FR1-in nəticəsini FR3, FR4, FR5, FR10 → FR12-yə ötürür. `name` verilərsə nəticə saxlanılır
(`GET/POST /api/v1/scenarios/saved`, `GET/DELETE /api/v1/scenarios/saved/{id}` — müəllif və vaxtlarla).
Mühərrik (`microlib/engines`) hələ yoxdursa `503` və izah qaytarılır.

## 7. Hesabatlar

```bash
curl -X POST -H "$T" -H "Content-Type: application/json" -o hesabat.xlsx http://127.0.0.1:8790/api/v1/reports \
  -d '{"title":"Məşğulluq 2026–2030","module":"FR4","scenarios":["Baseline","Adverse"],"from":2020,"to":2030,"equations":true}'
```

Vərəqlər: «Məlumat», «Göstəricilər» (göstərici × ssenari × il), «Tənliklər» (xülasə və əmsallar),
saxlanmış ssenarilər üçün ayrıca vərəq. Ətraflı hesabat qurucusu paneldədir.

## 8. MİİS inteqrasiya müqaviləsi

Müqavilə: **`openapi.yaml`** (OpenAPI 3.0). Server onun istinad tətbiqidir və Nazirliyin stekində əvəz edilə bilər.

1. **Göstərici identifikatoru** — `fr<k>:<kod>` (məs. `fr1:rgdp`, `fr4:emp:agr`); kataloq —
   `GET /api/v1/catalog` (`output/FRx_indicator_catalog.csv`). Ssenarilər `Baseline`/`Adverse`/`Reform`, faktiki `Actual`.
2. **Məlumat axını** — MİİS yeni faylı göndərir → yoxlama hesabatı → tətbiq → icra → `GET /runs/{id}` ilə
   izləmə → `status: ok` olduqda `GET /api/v1/forecasts` və `GET /api/v1/equations` ilə nəticələri götürür.
3. **Proqnozlar** düz siyahıdır: `{id, module, scenario, period, value}` + `series` (ad, vahid, mənbə).
4. **Xətalar**: `{"error": {"code", "message", "detail"}}`; kodlar — 400 (sorğu), 401/403 (nişan), 404, 409 (məşğul
   və ya tətbiq olunub), 413 (böyük), 422 (yoxlamadan keçmədi), 503 (mühərrik yoxdur).
5. **Məlumat rejimi** — FR10/FR12 nəticələri sintetik məlumatla `SYNTHETIC` nişanlıdır; `GET /status` →
   `data_modes`. Real məlumatla nəticələr yalnız Nazirliyin sistemində saxlanılmalıdır.
6. Nümunə müştəri: `sync_example.py` (yükləmə → tətbiq → icra → izləmə → proqnozlar).

## 9. Təhlükəsizlik

* İstehsalda serveri reverse proxy (nginx və s.) arxasında, HTTPS ilə işlədin; nişanları mühit dəyişəni ilə verin.
* Statik fayllar yalnız `panel/` və `site/` ağaclarından verilir; yol keçidi (`..`, kodlanmış `%2e%2e`, simvolik
  keçidlər), gizli fayllar, `_build/` və `.py` faylları bloklanır, qovluq siyahısı göstərilmir.
* Yükləmə ölçüsü `--max-upload-mb` (512) ilə məhdudlaşır; fayl adları təmizlənir (yol hissələri atılır).

## 10. Fayllar

| Fayl | Nədir |
|---|---|
| `server.py` | Server (HTTP, marşrutlar `routes.py`) |
| `openapi.yaml` | Müqavilə |
| `upload_store.py`, `validate_*.py`, `nbextract.py` | Yükləmə, yoxlama, dəftərlərdən ünvan cədvəllərinin çıxarılması |
| `run_manager.py`, `../run_all.py` | İcra |
| `autonomous.py` | Düşmə qovluğu, cədvəl, DSK yeniləməsi |
| `data_views.py`, `status_view.py`, `scenario_engine.py`, `report_xlsx.py` | Oxuma, ssenarilər, hesabat |
| `sync_example.py` | Müştəri nümunəsi |
| `tests/` | Sınaqlar: `python3 -m unittest discover -s api/tests -v` |
| `micro.db` | SQLite bazası (server yaradır) |

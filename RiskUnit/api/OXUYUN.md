# RiskModel API (MİİS §15.5.3) — oxu məni

Risk modulunun (İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi, v2) **məlumat, canlı analiz və avtonom
icra** serveri. Müqavilə: [`openapi.yaml`](openapi.yaml) (OpenAPI 3.0.3). Server onun işlək istinad tətbiqidir:
HTTP qatı yalnız Python standart kitabxanasıdır (`ThreadingHTTPServer`, SQLite), analiz isə `riskunit` modullarını
(`scalability`, `simulate`, `optimize`) və MikroUnit zəncirini (`microlib.engines.chain`) çağırır — buna görə
numpy / pandas / scipy olan Python lazımdır. `riskunit` modulları dəyişdirilmir, yalnız onların funksiyaları çağırılır.

## 1. Başlatmaq

| Yol | Əmr |
|---|---|
| macOS (iki klik) | `RiskModel_Baslat.command` |
| Windows (iki klik) | `RiskModel_Baslat.bat` |
| Əl ilə | `python3 api/server.py` → <http://127.0.0.1:8791/panel/> |

Başladıcı Python-u bu ardıcıllıqla seçir: `RISK_PYTHON` → `MIKRO_PYTHON` → `.venv` → `~/venvs/miis-model` → `python3`
(numpy/pandas/scipy olan ilk namizəd). Server artıq işləyirsə, yalnız brauzer açılır. Port: `RISK_API_PORT`
(standart **8791**; MikroUnit API-si 8790-dadır, ikisi eyni anda işləyə bilər).

Server başlayanda analiz keşini fonda isidir (≈ 5–8 s: amil σ-ları, MikroUnit bazası, RU Monte Karlo, tədbir
effektləri); vəziyyət `GET /api/v1/status` → `analysis_ready`. Sonra `stress/run` ≈ 1 s, `scalability/run` ≈ 1–1,5 s,
`optimize/run` ≈ 0,1–4 s.

Server parametrləri (`python3 api/server.py --help`):

| Parametr | İzah |
|---|---|
| `--host 127.0.0.1 --port 8791` | ünvan (standart nişanlarla yalnız yerli ünvana icazə var) |
| `--db api/risk.db` | SQLite faylı (saxlanmış ssenarilər, yeniləmə işləri, hadisələr) |
| `--python <yol>` | `update.py` / `run_all.py` üçün Python (standart: serverin öz Python-u) |
| `--schedule HH:MM[,HH:MM]` | gündəlik cədvəl (bax §4) |
| `--watch [--watch-interval 300] [--watch-mode full]` | yuxarı axın vintajlarının izlənməsi (bax §4) |
| `--no-warm`, `--quiet` | keşi isitmə; sorğu jurnalını çap etmə |

Mühit dəyişənləri: `RISK_API_TOKENS` (nişanlar), `RISK_NO_NETWORK=1` (bütün axınlar son keşdən; sınaqlar və
şəbəkəsiz server), `RISK_AS_OF=YYYY-MM-DD` (hesabat tarixi), `MIIS_MACRO_DIR`, `MIIS_MICRO_DIR`, `MIIS_MINISTRY_DIR`
(yuxarı axın qovluqları), `API_ORIGINS` (CORS: standart yalnız localhost).

## 2. Nişanlar (tokens)

`Authorization: Bearer <nişan>`. GET üçün **read**, POST/PUT/DELETE üçün **write** (write read-i də əhatə edir).

```bash
export RISK_API_TOKENS="risk-oxu-7f3a:read,risk-yaz-91c2:write"     # vergüllə ayrılmış nişan:icazə
```

Təyin edilməyibsə sınaq nişanları işləyir: `demo-read`, `demo-write` (server xəbərdarlıq çap edir və şəbəkə
ünvanına açılmaqdan imtina edir). `health` və `openapi.yaml` nişansızdır. Xətalar həmişə JSON-dur, mesaj
Azərbaycan dilində, texniki mətn ayrıca: `{"error": {"code": "engine_error", "message": "Hesablama alınmadı: …",
"detail": "EngineError: …"}}`. Kodlar: 400 (giriş), 401/403 (nişan), 404, 409 (məşğul), 413, 422 (hesablama).

## 3. Son nöqtələr (`/api/v1/`)

| Metod və yol | Məqsəd |
|---|---|
| `GET health`, `GET openapi.yaml` | vəziyyət, müqavilə (nişansız) |
| `GET status` | son icra (`_run_summary_v2.json`), mərhələ müddətləri, `baseline_id`, D2 axınlarının təzəliyi, xəbərdarlıqlar, aktiv yeniləmə, avtonom rejim, analiz keşi |
| `GET events?since=N` | hadisələr lenti (yeniləmə, cədvəl, izləmə, ssenarilər) — panel sorğu ilə izləyir |
| `GET catalog?prefix=V,K` | çıxış kataloqu (`_catalog_v2.csv` + kataloqda olmayan fayllar) |
| `GET outputs/{fayl}` | istənilən çıxış CSV-si JSON kimi: süzgəc `?sütun=dəyər[,dəyər]`, `q`, `sort=-skor`, `cols`, `limit` (≤ 20 000), `offset`, `format=csv` |
| `GET risks`, `GET risks/{R01}` | risk reyestri + FR2 skorları + qalıq risk + tədbir/xəbərdarlıq sayı; risk üzrə paket (tarixçə, kanal töhfələri, tədbirlər, S0/S7 amilləri, stress, CAEM, D5) |
| `GET monitor` | D5 (siqnal), D6 (proqnoza təsir; standart başlıq göstəriciləri, `targets=*` hamısı), D7, D2 |
| `GET stress/inputs`, `POST stress/run` | stress testi lüğəti; fərdi şoklar → MikroUnit zənciri + RU Monte Karlo |
| `GET scalability/factors`, `POST scalability/run` | miqyaslanma amilləri (S0); amil × ölçülər → bütün komponentlər |
| `GET optimize/inputs`, `POST optimize/run` | tədbirlər, risk iştahı; büdcə → optimal portfel (`optimize.optimise`, məcburi/xaric tədbirlər `fixed=`/`excluded=`), qalıq risk |
| `GET/POST scenarios/saved`, `GET/PUT/DELETE scenarios/saved/{id}`, `POST …/{id}/run` | saxlanmış ssenarilər (SQLite) |
| `POST refresh`, `GET refresh`, `GET refresh/{id}`, `POST refresh/{id}/cancel` | yeniləmə fon prosesi (bax §5) |
| `GET autonomous` | cədvəl və izləmənin vəziyyəti |
| `GET reports`, `GET reports/{fayl}`, `POST reports/xlsx` | hazır hesabatlar; server tərəfində Excel ixracı |

Statik səhifələr: `/panel/` (risk paneli), `/site/` (hesabat saytı), `/docs/` (metodologiya), `/` (`index.html`,
yoxdursa `/panel/`-ə yönləndirilir). Yol keçidi, gizli fayllar və `.py` faylları bloklanır.

### 3.1. Nümunələr (curl)

```bash
B=http://127.0.0.1:8791/api/v1; R="Authorization: Bearer demo-read"; W="Authorization: Bearer demo-write"
curl -s $B/health
curl -s -H "$R" $B/status
curl -s -H "$R" "$B/outputs/FR2_risk_scores.csv?cols=risk_id,ad,skor,prioritet&sort=-skor&limit=5"
curl -s -H "$R" "$B/outputs/V3_var_es.csv?portfel=sofaz&horizont=1il&etibarlilik=0.99"
curl -s -H "$R" "$B/outputs/S7_daily_decision.csv?format=csv" -o S7.csv
curl -s -H "$R" $B/risks/R01
curl -s -G -H "$R" $B/monitor --data-urlencode "signal=xəbərdarlıq"

# Stress testi: Brent −2σ + 25% devalvasiya + uçot dərəcəsi +1σ
curl -s -X POST -H "$W" -H "Content-Type: application/json" $B/stress/run -d '{
  "name": "Neft −2σ + devalvasiya", "shocks": [{"factor": "brent", "k_sigma": -2},
  {"factor": "fx", "size": 25}, {"factor": "rate", "k_sigma": 1}], "with_measures": true, "n": 4000}'

# RU şok açarları birbaşa (2026–2030, 5 dəyər) və MikroUnit override-ları
curl -s -X POST -H "$W" $B/stress/run -d '{"ru_overrides": {"brent_path": [70,45,45,45,45], "spi": [0,-2,0,0,0]},
  "micro_overrides": {"FR1": {"exogenous": {"brent": {"values": [70,45,45,45,45]}}}}}'

# Miqyaslanma: Brent ±1σ, ±2σ (+ bugünkü canlı sapma) → bütün komponentlər
curl -s -X POST -H "$W" $B/scalability/run -d '{"factor": "brent", "k_sigma": [-2,-1,1,2], "top_components": 40}'
curl -s -X POST -H "$W" $B/scalability/run -d '{"factor": "fx", "sizes": [10, 25]}'      # təbii vahiddə (%)

# Tədbir portfeli: 500 mln AZN, sərt risk iştahı, T09 məcburi, T23 xaric
curl -s -X POST -H "$W" $B/optimize/run -d '{"budget": 1500, "appetite": {"P_g_max": 0.15},
  "include": ["T09"], "exclude": ["T23"]}'
curl -s -X POST -H "$W" $B/optimize/run -d '{"selection": {"T01": 1, "T09": 0.5}}'      # yalnız qiymətləndirmə

# Ssenarini saxla, yenidən hesabla, Excel-ə ixrac et
curl -s -X POST -H "$W" $B/scenarios/saved -d '{"name": "Neft −2σ", "kind": "stress",
  "request": {"shocks": [{"factor": "brent", "k_sigma": -2}]}}'
curl -s -X POST -H "$W" $B/scenarios/saved/<id>/run
curl -s -X POST -H "$W" $B/reports/xlsx -d '{"scenario_id": "<id>", "files": ["FR2_risk_scores.csv"]}' -o ixrac.xlsx

# Yeniləmə
curl -s -X POST -H "$W" $B/refresh -d '{"mode": "daily"}'          # 202 + iş; ikinci sorğu 409
curl -s -H "$R" "$B/refresh/<id>?tail=50"                           # irəliləyiş + jurnalın sonu
curl -s -X POST -H "$W" $B/refresh/<id>/cancel
```

### 3.2. Stress testinin məntiqi

* **Amillər** (`shocks`) — S0 cədvəlinin 15 amili (brent, gas, fx, partner, rate, state_inv, remit, drought, food,
  import, costpush, geo, geo_stress, npl, quake). Ölçü σ vahidində (`k_sigma`, |k| ≤ 6) və ya təbii vahiddə (`size`;
  S0 `vahid` sütunu, log amillər üçün qiymətləndirmə ilinin səviyyə dəyişməsi) — sonuncu `scalability` modulunun öz
  ölçü funksiyası ilə tərsinə çevrilir (biseksiya). Zəlzələ birtərəflidir (k ≥ 0).
* **MikroUnit zənciri** FR1→FR3→FR4→FR5→FR10→FR12: amillərin override-ları birləşdirilir (ekzogen `pct` faizləri
  mürəkkəb, `add` cəmlənir, əmsal sürüşmələri və `RU.addf` birillik tənlik sürüşmələri dəyişən üzrə toplanır) +
  `micro_overrides`; şoklar qiymətləndirmə ilindən başlayır (scalability v2.1); cavab zəncirin öz Baseline icrasından
  fərqdir (`scalability.run_chain`, tanınmayan açar — 422). Nəticə: başlıq göstəriciləri (`ru:*` + FR1, `scalability.head_rows`) və
  ən çox təsirlənən komponentlər (`scalability.effect`: yaxın-sıfır bazada səviyyə fərqi və ya % ÜDM).
* **RU birgə Monte Karlo** (`simulate.run`): amillər RU şok açarlarına uyğunlaşdırılır (cavabda
  `ru_overrides_used` və `notes`; məs. fx ≥ 10% → qiymətləndirmə ilində devalvasiya hadisəsi, rate → kredit faizi
  0,5 × şok × FR1 G3 əmsalı; gas, state_inv, costpush, npl yalnız zəncirdə). (a) deterministik sapma —
  `measures.stress_vector` (S1–S8 ilə eyni qayda: yalnız elan olunmuş şoklar; T09 tədbiri ilə və tədbirsiz), (b) şoka
  şərtli paylanma (digər amillər təsadüfi) şərtsiz paylanma ilə müqayisədə: kvantillər, P(hədd pozulması), ES10.
* RU öz mərkəzi yolunu dərc etmir: hər şey OxLon/MicroUnit bazasından **fərq** kimi verilir.

## 4. Avtonom rejim

```bash
python3 api/server.py --schedule 06:30,13:00,18:30 --watch            # və ya başladıcıya eyni parametrlər
python3 api/server.py --schedule 06:30=full,12:00=daily,18:00=daily  # rejimlər açıq
```

* **Cədvəl** — ilk göstərilən vaxt tam icra (`update.py --full`: axınlar + tam boru xətti + hesabatlar), qalanları
  gündəlik monitor (`update.py --daily`). Vaxt yerli vaxtdır; məşğul olduqda icra buraxılır və hadisə yazılır.
* **İzləmə** — hər 300 s spine manifestinin fayllarının (Macro_OxLon/delivery, MicroUnit/output, Macro_MinistryUnit)
  ölçüsü/vaxtı yoxlanılır; dəyişəndə SHA-256 son icranın `output/spine_manifest.csv` hash-i ilə müqayisə olunur.
  Yeni vintaj → tam icra (`--watch-mode`). Məşğul olduqda dəyişiklik «gözləmədə» qalır və növbəti yoxlamada icra
  başladılır (NFR2: yeni məlumatdan sonra ≤ 24 saat).
* Hamısı `GET events`, `GET autonomous` və `logs/api/<iş>.log`-a yazılır. `RISK_NO_NETWORK=1` alt proseslərə ötürülür.
* `scheduler/` qovluğundakı launchd/cron/Windows tapşırıqları ilə birlikdə işləyə bilər: kilid ortaqdır.

## 5. Yeniləmə (refresh) və kilid

`POST refresh {"mode": "daily" | "full" | "pipeline", "no_fetch": false}` alt prosesi başladır: `update.py --daily`,
`update.py --full` və ya `run_all.py --no-pdf`. Eyni anda yalnız bir iş: prosesdaxili kilid + fayl sistemi kilidi
`output/.update.lock` (`scheduler/run_update.sh` ilə eyni mkdir kilidi; sahiblik `output/.update.lock.api.json`).
Kilid başqası tərəfindən tutulubsa 409 (`running.source` = «xarici»). İrəliləyiş jurnaldakı `[HH:MM:SS] A0 …`
sətirlərindən hesablanır (gözlənilən mərhələ sayı son xülasələrdən). Ləğv: proses qrupuna SIGTERM, 15 s sonra
SIGKILL; son yaxşı nəticələr qalır (boru xətti yarımçıq skor yazmır). Server yenidən başlayanda yarımçıq işlər
«interrupted» olur, köhnə API kilidi götürülür.

## 6. MİİS ilə inteqrasiya

* **Panel** (`RU/panel/`) bu API-ni eyni mənbədən (`/api/v1/…`) çağırır; nişan panelin ayarlarında saxlanılır.
* **Nazirliyin stekində**: `openapi.yaml` müqavilədir — server əvəz edilə bilər, eyni yollar və JSON formatları
  saxlanılmalıdır. Çıxış faylları (`output/*.csv`) və kataloq (`_catalog_v2.csv`) API-dən asılı deyil.
* **Yuxarı axınlar** yalnız oxunur (OxLon §15.5.1, MicroUnit §15.5.2, Nazirlik CAEM/Bottom-up); API heç vaxt onlara
  yazmır. MikroUnit zənciri `MIIS_MICRO_DIR/microlib` paketindən idxal olunur.
* **Digər bölmələr** `GET status` → `baseline_id` ilə hansı baza vintajına əsaslandığını yoxlaya bilər.

## 7. Sınaqlar

```bash
cd RiskUnit/api && RISK_NO_NETWORK=1 python3 -m unittest discover -s tests -v
```

`test_api.py` (HTTP: nişanlar, bütün son nöqtələr, süzgəclər, ssenarilər CRUD, yeniləmə kilidi/irəliləyiş/ləğv,
xarici kilid, Excel, statik fayllar; mühərriklər əvəzlənib), `test_units.py` (cədvəl təhlili, növbəti icra, izləmə
və yeni vintaj, xətaların tərcüməsi, override birləşdirilməsi, süzgəclər, RU açarlarının yoxlanması),
`test_live.py` (real modullarla `stress/run` < 10 s, `scalability/run` < 5 s, `optimize/run`; MikroUnit yoxdursa
buraxılır). Hamısı şəbəkəsiz işləyir.

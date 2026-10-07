# SiyasətModel API — MİİS §15.5.4 İqtisadi siyasətlərin təsir analizi (PolicyUnit)

Bu server siyasət ssenarilərinin **konfiqurasiya ilə yaradılmasını, yoxlanmasını, hesablanmasını və müqayisəsini**
HTTP/JSON interfeysi ilə təmin edir və panelə (`/panel/`) xidmət edir. Müqavilə: `api/openapi.yaml`
(`GET /api/v1/openapi.yaml`). HTTP qatı yalnız Python standart kitabxanasıdır (ThreadingHTTPServer, SQLite);
hesablama `policyunit` paketinin açıq funksiyalarını çağırır — numpy/pandas/scipy/openpyxl olan Python lazımdır.

## 1. Başlatmaq

| Platforma | Əmr |
|---|---|
| macOS | `SiyasetModel_Baslat.command` üzərinə iki klik (və ya terminalda `./SiyasetModel_Baslat.command`) |
| Windows | `SiyasetModel_Baslat.bat` üzərinə iki klik |
| Əl ilə | `python3 api/server.py` → http://127.0.0.1:8792/panel/ |

Başladıcı Python-u bu ardıcıllıqla seçir: `POLICY_PYTHON` → `MIKRO_PYTHON` → `.venv` → `~/venvs/miis-model` → `python3`
(numpy, pandas, scipy olan ilk namizəd). Server artıq işləyirsə yalnız brauzer açılır.

Seçimlər (`python3 api/server.py --help`):

| Seçim | Məna |
|---|---|
| `--port 8792` (`POLICY_API_PORT`) | port |
| `--schedule 06:30,18:30` | gündəlik cədvəl: göstərilən vaxtlarda `run_all.py` |
| `--watch [--watch-interval 300]` | yuxarı axın vintajlarının izlənməsi (aşağıya bax) |
| `--risk-api URL`, `--no-risk-autostart` | RiskUnit API ünvanı; işləmirsə avtomatik başlatmamaq |
| `--no-warm` | başlanğıcda mühərrik keşini isitməmək |
| `--db`, `--config-dir`, `--root` | SQLite faylı (standart `api/policy.db`), konfiqurasiya qovluğu, kök |

Mühit dəyişənləri: `POLICY_API_TOKENS`, `POLICY_NO_NETWORK=1` (RiskUnit yalnız keşdən), `POLICY_RISK_API`,
`API_ORIGINS` (CORS: standart yalnız localhost; `*` və ya vergüllə siyahı).

## 2. Nişanlar (tokens)

`Authorization: Bearer <nişan>`. GET üçün `read`, POST/PUT/DELETE üçün `write` icazəsi lazımdır (`write` `read`-i əhatə edir).

```bash
export POLICY_API_TOKENS="siyaset-oxu:read,siyaset-yaz:write"
```

Standart sınaq nişanları `demo-read` / `demo-write` yalnız 127.0.0.1-də işləyir — server onlarla şəbəkəyə açılmır.
`health` və `openapi.yaml` nişansızdır. Xəta formatı: `{"error": {"code", "message" (Azərbaycan dilində), "detail"}}`;
ssenari/alət yoxlaması uğursuz olarsa 422 + `errors: [...]`.

## 3. Son nöqtələr (`/api/v1/`)

| Metod və yol | Təyinat |
|---|---|
| `GET health`, `GET openapi.yaml` | vəziyyət, müqavilə (nişansız) |
| `GET status` | son icra, baza vintaj id-ləri (`vintage_id`), mühərriklərin mövcudluğu, RiskUnit, aktiv işlər, avtonom rejim |
| `GET events?since=` | hadisələr lenti (ssenari saxlandı, hesablama irəliləyişi, yeniləmə, yeni vintaj) |
| `GET catalog?prefix=P1_,P5_` | çıxış faylları kataloqu (`output/_catalog.csv`) |
| `GET outputs/{fayl}?sütun=dəyər&sort=-x&limit=&offset=&cols=&q=&format=csv` | istənilən çıxış faylı |
| `GET instruments[?family=]`, `GET instruments/{id}`, `GET instruments/schema` | alətlər kataloqu (ailə, vahid, min/max, mühərriklər, adapterlər), forma sxemi |
| `POST instruments/validate`, `POST instruments/new`, `DELETE instruments/{id}` | NFR4: yeni alət konfiqurasiya ilə |
| `GET scenarios[?source=official\|draft&tag=&q=]`, `GET scenarios/schema` | ssenarilər, forma sxemi |
| `POST scenarios[?store=official]`, `GET/PUT/DELETE scenarios/{id}` | CRUD (qaralama SQLite-da; rəsmi — `config/scenarios/<id>.json`) |
| `POST scenarios/validate` | yoxlama → `{valid, errors[], warnings[], normalised, engines}` |
| `POST scenarios/{id}/duplicate`, `POST scenarios/{id}/promote` | surət; qaralamanı rəsmiləşdirmək |
| `POST scenarios/import`, `GET scenarios/{id}/export` | JSON idxal/ixrac |
| `POST scenarios/{id}/run`, `POST runs` (saxlanmamış ssenari) | hesablama → nəticə (və ya 202 + `run_id`) |
| `GET runs[?scenario=]`, `GET runs/{id}[?detail=summary]`, `POST runs/{id}/cancel` | irəliləyiş, nəticə, ləğv |
| `POST compare` | ≥ 2 ssenari, ≥ 5 KPI + çəkilər → reytinq |
| `GET kpi`, `GET/POST kpi/sets`, `GET/PUT/DELETE kpi/sets/{id}` | KPI kataloqu, istifadəçinin KPI dəstləri |
| `GET/POST refresh`, `GET refresh/{id}`, `POST refresh/{id}/cancel` | `run_all.py` fon prosesi (kilid, irəliləyiş, ləğv) |
| `GET autonomous` | cədvəl və izləmənin vəziyyəti |
| `GET reports`, `GET reports/{fayl}`, `POST reports/xlsx` | Excel ixracı (hesablama, müqayisə, çıxış faylları) |

Statik: `/panel/` (panel), `/docs/` (metodologiya), `/` → `index.html` və ya `/panel/`, `/api-docs/OXUYUN.md`,
`/api-docs/openapi.yaml`. Mənbə kodu (.py), verilənlər bazası və gizli fayllar verilmir.

### Hesablamanın nəticəsi (`scenarios/{id}/run`)
- `engines` — hər mühərrik (micro — MikroUnit zənciri, əsas metod; caem — Nazirlik CAEM, müqayisə; oxlon; io; microsim;
  longrun) üzrə vəziyyət: `ok | tətbiq edilmir | xəta | yoxdur`, müddət, izah.
- `horizons` — qısa (başlanğıc il və növbəti il: t0, t0+1), orta (başlanğıc ildən 2–3 il sonra: t0+2…t0+3), uzun (≥ t0+4, yəni 5-ci il və sonrası) — Nazirliyin 24.08 tərifi.
- `headline`, `headline_wide` — əsas göstəricilər × üfüq (orta %/f.b. fərq; axınlar üçün cəm, mln AZN).
- `sectors` (FR2), `social` (FR3; mikrosimulyasiya sətirlərində «SİNTETİK — real ev təsərrüfatı məlumatı deyil»),
  `comparison` (NFR2: metodlar, fərq, işarə uyğunluğu, izah), `effects` (tam P1 cədvəli; `detail=summary` ilə yoxdur).
- `side_effects` (FR4): `items` (qaydalar kitabxanası, ciddilik 1–4), `variants` (avtomatik yan təsir ssenariləri: neft −1σ,
  manat +1σ, zəif ötürmə, alternativ maliyyələşmə), `risk_profile` (RiskUnit şərti paylanmaları — yalnız HTTP), `mitigation`.
  Rejim: `side_effects: full | rules | none` (`rules` — RiskUnit-siz, sürətli).
- `kpi` (FR5: seçilmiş KPI-ların xam dəyərləri), `text_az` (qısa izah), `vintage`, `timings`, `warnings`.

Hədəf < 30 s: tipik vaxt `rules` 2–4 s, `full` 6–10 s (mikrosimulyasiyalı vergi/xərc ssenariləri 10–20 s).
`wait` saniyə ərzində bitməsə 202 qaytarılır; `GET runs/{run_id}` `progress.pct`, `progress.steps` göstərir.
Eyni ssenari + parametrlər + vintaj üçün nəticə keşdən verilir (`cached: true`; `force: true` — yenidən).

## 4. curl nümunələri

```bash
B=http://127.0.0.1:8792/api/v1; R="Authorization: Bearer demo-read"; W="Authorization: Bearer demo-write"
curl -s $B/health
curl -s -H "$R" $B/status
curl -s -H "$R" "$B/outputs/P1_headline.csv?scenario=mw20_2027&horizon=orta"
curl -s -H "$R" "$B/outputs/P5_ranking.csv?format=csv" -o reytinq.csv
curl -s -H "$R" "$B/instruments?family=vergi"
# yeni ssenari (qaralama) → yoxlama → hesablama
curl -s -H "$W" -X POST $B/scenarios/validate -d '{"id":"edv_m1","name_az":"ƏDV −1 f.b.","start_year":2027,
  "instruments":[{"instrument":"vat_rate","years":"all","size":-1}]}'
curl -s -H "$W" -X POST $B/scenarios -d @edv_m1.json
curl -s -H "$W" -X POST $B/scenarios/edv_m1/run -d '{"side_effects":"full","detail":"summary"}'
curl -s -H "$W" -X POST $B/scenarios/edv_m1/promote            # rəsmi: config/scenarios/edv_m1.json
# müqayisə: ≥ 5 KPI
curl -s -H "$W" -X POST $B/compare -d '{"scenarios":["mw20_2027","vat_minus2","edv_m1"],
  "kpis":["gdp_short","gdp_medium","gdp_long","inflation_short","unemployment","fiscal_cost"],"weights":{"gdp_medium":2}}'
curl -s -H "$W" -X POST $B/reports/xlsx -d '{"run_id":"PR..."}' -o netice.xlsx
curl -s -H "$W" -X POST $B/refresh -d '{"only":"core.validate,core.scenarios"}'   # 202 + iş id-si
```

## 5. NFR4 — proqramlaşdırmasız yeni ssenari (≤ 1 iş günü)

1. Panel formasında (və ya `GET scenarios/schema` + `GET instruments`) alət(lər)i, ölçünü, illəri, başlanğıc ili,
   hədəf sektoru və maliyyələşməni seçin; və ya mövcud ssenarini `POST scenarios/{id}/duplicate` ilə kopyalayın.
2. `POST scenarios/validate` — xətalar Azərbaycan dilində (məs. «ölçü 40 icazə verilən [−10, 5] intervalından kənardır»).
3. `POST scenarios` — qaralama saxlanılır (SQLite); `POST scenarios/{id}/run` — nəticə saniyələr ərzində.
4. Təsdiqdən sonra `POST scenarios/{id}/promote` — fayl `config/scenarios/<id>.json` yazılır, `run_all.py` onu bütün
   çıxışlara (P1_, N2_, P4_, P5_) daxil edir; dəyişiklikdən əvvəlki nüsxə `config/_backup/scenarios/`-dadır.
   Alternativ: JSON faylı əl ilə `config/scenarios/`-a qoyun (`config/README_az.md`) və ya `POST scenarios/import`.

## 6. NFR4 — yeni siyasət aləti konfiqurasiya ilə (≤ 1 iş günü)

Yeni alət **mövcud mühərrik girişinə** adapter sətri ilə bağlanır — kod yazılmır:
1. Oxşar aləti tapın (`GET instruments/{id}` — onun adapterləri nümunədir); `GET instruments/schema` hər mühərrikin
   qəbul etdiyi `target_key`-ləri (MikroUnit `FR1/exogenous/<id>`, CAEM vəziyyət kodları, IO/mikrosimulyasiya girişləri)
   və `transform` qrammatikasını (`pct | add | level | target | target_gdp | shock_gdp | target_rev | custom:<mövcud> | *k`) verir.
2. `POST instruments/validate` gövdəsi:
   `{"instrument": {"id","name_az","family","unit","default_size","min","max","description_az","cost_rule","cost_in_fr1"},
     "adapters": [{"engine","target_key","transform","note_az"}]}`. Statik yoxlama (id, ailə, vahid, intervallar,
   mühərrik qoşulub, açar mühərrikin tanıdığı girişdir, transform düzgündür) + konfiqurasiyanın müvəqqəti surətində
   `default_size` ilə **sınaq hesablaması**: mühərrik adapteri rədd edərsə xəta, təsir sıfırdırsa xəbərdarlıq.
3. `POST instruments/new` — sətirlər `config/instruments.csv` və `config/adapters.csv` sonuna yazılır (ehtiyat nüsxə
   `config/_backup/instrument_<id>_<vaxt>/`); `dry_run: true` — yalnız yoxlama. API ilə əlavə edilmiş alət heç bir
   ssenaridə istifadə olunmursa `DELETE instruments/{id}` ilə geri alınır.
4. Vaxt bölgüsü: konfiqurasiya və sınaq 1–2 saat; ötürmə əmsalının (elastiklik, `*k` miqyası) mənbə ilə
   əsaslandırılması, `note_az`-da sənədləşdirilməsi və nəticənin oxşar alətlə müqayisəsi — iş gününün qalanı.
   Mövcud girişlərlə ifadə olunmayan **yeni ötürmə mexanizmi** kod tələb edir (mühərrik modulunda `custom:` funksiya).

## 7. Avtonom rejim

- `--schedule 06:30,18:30` — göstərilən vaxtlarda `run_all.py` (kilid tutulubsa buraxılır və hadisə yazılır).
- `--watch` — hər 300 s yuxarı axın fayllarının ölçü/vaxtı, dəyişəndə məzmun hash-i yoxlanılır: `MicroUnit/output/*.csv|json`
  (+ FR3–5 panel), `RiskUnit/output` (baseline_id, σ, risk skorları, tədbirlər), CAEM (Nazirlik nüsxəsi və
  `data/ministry/CAEM.xlsx`), OxLon çatdırılması (`forecast_long.csv` və s.), IO məlumatı (`data/io/`), `config/*.csv` və
  ssenarilər. Son uğurlu icranın manifesti `logs/api/upstream_manifest.json`-dadır; fərq bir interval ərzində sabit qalanda
  `run_all.py` başladılır (`GET autonomous`, `GET events`). İlk başlanğıcda manifest yoxdursa MikroUnit/CAEM vintajı son
  `P1_run_meta.json` ilə müqayisə olunur.
- Kilid `output/.run_all.lock` (mkdir) — cron/launchd sarğıları eyni kilidi istifadə etməlidir.

## 8. MİİS ilə inteqrasiya

- **Baza vintajı**: hər hesablama `vintage` qaytarır (MikroUnit hash, CAEM md5, OxLon `forecast_long` md5, IO manifest,
  RiskUnit `baseline_id`, konfiqurasiya hash-i → `vintage_id`). Siyasət təsiri = ssenari − eyni vintajlı baza.
- **RiskUnit (§15.5.3)** yalnız HTTP ilə (`POLICY_RISK_API`, standart `http://127.0.0.1:8791/api/v1`, nişanlar
  `POLICY_RISK_TOKEN_READ/WRITE`). İşləmirsə server onu ayrıca DB ilə (`work/risk_scratch.db`) başladır və dayananda
  söndürür; şəbəkəsiz rejimdə son keş istifadə olunur (`risk_profile.status`-da «keş (tarix)»).
- **DataBiz / MİİS frontendi**: bütün cavablar JSON (Azərbaycan dilində etiketlər, `text_az`), CSV/xlsx ixracı;
  CORS üçün `API_ORIGINS`. Rol-əsaslı giriş — oxu/yazı nişanları.
- **Sınaqlar**: `python3 -m unittest discover -s api/tests -t api/tests` (şəbəkəsiz, mühərriklər stub);
  canlı: `POLICY_API_LIVE=1 python3 -m unittest discover -s api/tests -t api/tests -p "test_live.py"`.

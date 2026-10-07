# PolicyUnit konfiqurasiyası (§15.5.4) — proqramlaşdırmasız ssenari əlavəsi (NFR4)

Bütün fayllar sadə CSV (UTF-8, vergüllə ayrılmış, mətn sahələrində vergül olarsa dırnaq `"..."`) və JSON-dur.
Yeni sətir **faylın sonuna** əlavə edilir; sütun sırası dəyişdirilmir. Kod dəyişikliyi tələb olunmur.

## `instruments.csv` — siyasət alətləri kataloqu
Sütunlar (bu ardıcıllıqla): `id, name_az, family, unit, default_size, min, max, engines, description_az, cost_rule, cost_in_fr1`
- `family`: vergi / xərc / sosial / əmək / monetar / ticarət / sektor / tənzimləmə
- `unit`: `pct` (bazaya nisbətən səviyyə %), `pp` (faiz bəndi), `mln_azn` (nominal mln AZN/il), `abs` (mütləq ədəd)
- `engines`: nöqtəli vergüllə siyahı — `micro;caem;oxlon;io;microsim;longrun`
- `cost_rule`: birbaşa fiskal xərcin hesablanması — `spend` (ölçü = xərc), `revenue:<vat|cit|pit|customs>` (gəlir itkisi =
  Δdərəcə / dərəcə × gəlir/ÜDM × ÜDM), `benefit:<param>` (% × `fiscal_params.csv` bazası), `none`
- `cost_in_fr1`: `yes` — xərc MikroUnit FR1 büdcəsində artıq var; `no` — PolicyUnit birbaşa xərci büdcə balansına əlavə edir

## `adapters.csv` — alət → mühərrik → giriş xəritəsi
Sütunlar: `instrument, engine, target_key, transform, note_az`. Hər mühərrik yalnız öz sətirlərini oxuyur.
- `transform`: `pct` | `add` | `level` | `custom:<funksiya>` — istəyə görə miqyas `*k` (məs. `add*0.5`).
  CAEM üçün əlavə: `target` (yol məcburi verilir, f.b.), `target_gdp` / `shock_gdp` (xərc ÜDM-ə %), `target_rev` (vergi gəliri ÜDM-ə %).
- `target_key` (micro): `FR1/exogenous/<id>`, `FR1/levers/<id>=<dəyər>`, `FR3/levers/mw_growth`, `FR5/exogenous/relp:<növ>`,
  `FR12/levers/<id>`, `overlay/<price|income|supply>`. Real id-lər: `microlib.engines.<fr>.inputs()`.
  Naməlum açar MikroUnit-də yalnız xəbərdarlıq verir — PolicyUnit bunu **xəta** sayır.
- `target_key` (caem): CAEM AZE Model vəziyyət kodu (`gcap_y, pb_y, vatax_y, ptax_y, pitax_y, otax_y, CR, dS, dta, dP, dx`).
- IO və mikrosimulyasiya agentləri öz sətirlərini (`engine` = `io` / `microsim`) faylın sonuna əlavə edir.

## `scenarios/<id>.json` — ssenari
```json
{"id": "mw20_2027", "name_az": "...", "description_az": "...", "start_year": 2027,
 "instruments": [{"instrument": "min_wage", "years": [2027, 2028, 2029, 2030] | "all", "size": 20,
                  "unit": "pct", "target": null, "financing": null}], "tags": ["əmək"]}
```
- `years: "all"` = `start_year`…2035. `financing`: `deficit | sofaz | tax | reallocation | null`.
- Yoxlama (`python3 -m policyunit.scenario <fayl>`) səhvləri Azərbaycan dilində göstərir.

## Digər fayllar
- `kpi.csv` — KPI kataloqu (FR5); istifadəçi ən azı 5 göstərici seçir. Defolt seçim (`default_selected = yes`, çəki):
  ÜDM qısa/orta/uzun (1/1/1), inflyasiya (1), işsizlik (1), fiskal xərc (1), borc/ÜDM (1), **yan təsirlərin sayı (1),
  hədd pozulması ehtimalının artımı (1), risk ES10 (0,5), metodlar arası fikir ayrılığı (1)** — risk göstəriciləri FR4 mərhələsindən (`P4_kpi_inputs.csv`,
  `P4_risk_profile.csv`) gəlir, KPI mərhələsi (`core.kpi`) FR4-dən sonra işləyir. Çəkiləri `default_weight`, seçimi
  `default_selected` sütununda və ya `run_all.py --kpi id1,id2,...` ilə dəyişin.
- `fiscal_params.csv` — fiskal bazalar və proksi parametrləri (mənbə, il, qeyd ilə; təqribi dəyərlər işarələnib).
- `longrun_params.csv` — uzun müddətli struktur ekstrapolyasiyanın parametrləri.
- `indicators.csv` — bütün mühərriklərin istifadə etdiyi standart göstərici id-ləri (NFR2 müqayisəsi bunlarla aparılır).
- `io_sectors.csv` — IO sektor təsnifatı (IO agentinin faylı).

## Yeni ssenari 1 iş günü ərzində (NFR4)
1. `scenarios/` qovluğunda mövcud JSON-u kopyalayın, `id`, ad, alətləri dəyişin.
2. `python3 -m policyunit.scenario config/scenarios/<id>.json` — yoxlama.
3. `python3 run_all.py --scenario <id>` — bütün mərhələlər; core **birləşdirmə rejimində** işləyir: yalnız bu ssenarinin
   sətirləri `P1_*`, `N2_*` fayllarında əvəz olunur (digər ssenarilər qalır), sonra mikrosimulyasiya (P3), FR4 (P4, ssenari
   üzrə birləşdirmə), NFR1, KPI (P5 — həmişə BÜTÜN ssenarilər üzrə normallaşdırılır və sıralanır), panel və təzəlik yoxlaması.
   `--only core.scenarios --scenario <id>` yalnız P1_/N2_ sətirlərini yeniləyir (P3–P5 yenilənmir — təzəlik yoxlaması bunu göstərir).

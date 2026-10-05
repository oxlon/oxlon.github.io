# microlib — MicroUnit v2 üçün ortaq kitabxana

Asılılıqlar: yalnız `numpy`, `pandas`, `scipy`, `statsmodels`. Notebook-lar `ROOT`-dan işə salındığı üçün
`import microlib` birbaşa işləyir. Testlər: `python3 -m microlib.tests.run` (pytest lazım deyil).

## 1. Tənlik reyestri (`microlib.registry`)

Notebook öz qiymətləndirmələrini (`fit_coef`, `fit_se`) ötürür. Reyestr eyni (y, X) üzərində statsmodels ilə
tənliyi müstəqil yenidən qiymətləndirir, əmsalları yoxlayır (nisbi fərq ≤ 1e-6, uyğunsuzluq olarsa
`AssertionError`), sonra diaqnostika, dayanıqlıq testləri və Azərbaycan dilində reqressiya nəticəsi
(`summary_text`) əlavə edir.

```python
from microlib.registry import EquationRegistry, dols_augment
REGX = EquationRegistry("FR1", data_mode="OBSERVED")      # OBSERVED | SYNTHETIC | REAL

# Sadə OLS (məs. dərəcə tənliyi): kointeqrasiya testi tətbiq olunmur -> coint=False
f = ols(y, X, cov="hac")
REGX.add("FR1.G4_infl", y, X, estimator="OLS", cov="hac",
         fit_coef=dict(zip(f.names, f.beta)), fit_se=dict(zip(f.names, f.se)),
         components=["fr1:infl"], subtask="G. Qiymətlər", title_az="İnflyasiya", title_en="Inflation",
         dependent_label_az="İQİ inflyasiyası, %", coint=False)
```

### İşlənmiş nümunə: DOLS tənliyi (lead/lag fərq hədləri X-in içindədir)

`lr_fit` DOLS(±1) reqressiyasını qiymətləndirir, lakin həlledici (solver) **yalnız uzunmüddətli
əmsallardan** istifadə edir; sabit isə statik səviyyə qalığının ortası sıfır olacaq şəkildə yenidən
mərkəzləşdirilir. Reyestrə tam (lead/lag hədli) X verilir, `fit_coef` isə yalnız `const` + uzunmüddətli
əmsalları saxlayır:

```python
res = REG["C3_man"]; fit = res["fit"]                  # fit = lr_fit(y, X), fit.estimator == 'DOLS(+/-1)'
Xa = dols_augment(res["X"], leads=1, lags=1, det=DET)   # X + d_<x>_F1, d_<x>_00, d_<x>_L1 (dols() adları)
REGX.add("FR1.C3_man", res["y"], Xa,                    # y və Xa tam uzunluqda (kənar illər NaN)
         estimator=fit.estimator, cov="hac", dols_leads_lags=(1, 1), det=list(DET),
         fit_coef=pd.Series(fit.beta, index=fit.names),  # const (yenidən mərkəzləşdirilmiş) + uzunmüddətli
         fit_se=pd.Series(fit.se, index=fit.names),      # DOLS HAC kovariasiyasından
         components=["fr1:rva_man"], subtask="C. Real sektor",
         title_az="Emal sənayesi: real ƏDV", title_en="Manufacturing real value added",
         dependent_label_az="ln real emal ƏDV",
         coef_labels_az={"ln_K_man": "ln kapital (emal)", "trend": "xətti trend"},
         sign_expected={"ln_K_man": +1},
         restrictions=[{"text_az": "Miqyasa görə sabit gəlir", "test": "HAC-F", "stat": F, "p": p, "imposed": True}],
         holdout=None, notes_az=res["note"])
```

Nəticədə: `d_*` hədləri `coefficients` siyahısında `role="dols_aug"`, `used_value=null`,
`editable=false` kimi göstərilir; `const` və uzunmüddətli əmsallar `used_value` = notebook dəyəri.
`checks.const_mode` = `"recentred …"`. Kointeqrasiya (EG) testi, `fitted` sırası, Chow və CUSUM statik
səviyyə formasında aparılır (notebook konvensiyası). Əgər X yalnız səviyyələrdən ibarətdirsə, reyestr
`dols_leads_lags` əsasında d-hədlərini özü qurur. Kəsilmiş (yalnız DOLS nümunəsi) matrislər verilərsə,
`levels=(y_tam, X_tam)` də ötürün; əks halda yenidən mərkəzləşdirilmiş sabit fərqli çıxar.

Məhdudiyyətlə sabitlənmiş əmsal: `fixed={"ln_L": 1.0}`. Rədd edilmiş və həssaslıq spesifikasiyaları:
`used_in_forecast=False`.

### Digər qiymətləndiricilər
| estimator | tələb olunan | qeyd |
|---|---|---|
| `2SLS` | `iv={"endog": [...], "Z": DataFrame}` | HAC proyeksiya edilmiş regressorlarda; first-stage F, Sargan |
| `FE-twoway` | y, X MultiIndex (vahid, il); `panel={"entity":"unit","time":"year"}` | DK SE, t(T−1); LOO/rekursiv illər üzrə |
| `logit`, `poisson` | `results=` (statsmodels) və ya y, X | normal p-dəyərləri; `time_index=` illər |
| `SUR`, `3SLS`, `LA-AIDS`, … | `fit_coef`, `fit_se`, `fit_df`/`p_dist`, ixtiyari `resid=` | yenidən hesablanmır |

Mənasız olan testlər `null` yazılır, səbəbi `null_reasons`-dadır.

### Yazmaq
```python
REGX.validate()                                   # [] və ya ValueError
REGX.write(f"{ROOT}/output/FR1_equations.json")   # NaN -> null, numpy tipləri çevrilir
print(REGX.summary("FR1.C3_man")); REGX.table()
```

## 2. Konvensiyalar (notebook-larla eyni)
* HAC: Newey–West Bartlett, `L = max(1, floor(4(n/100)^(2/9)))` (n=5–26 üçün L=2), kiçik nümunə düzəlişi
  `n/(n−k)`; p-dəyərləri və intervallar t(n−k). statsmodels ekvivalenti:
  `fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True}, use_t=True)` — statsmodels-in
  standartı (düzəlişsiz, normal paylanma) FƏRQLİDİR.
* EG kointeqrasiya: qalıqlar üzrə ADF (deterministik hədsiz, maxlag=1), MacKinnon `N = I(1) izahedici + 1`
  (trend və dummy-lər sayılmır), trend olduqda `'ct'`; `p ≤ 0.10` → müəyyən edilib.
* `cond_number` standartlaşdırılmış regressorlar üzrədir (statsmodels-in `condition_number`-i deyil);
  VIF y ilə uzlaşdırılmış nümunədə.
* DOLS: `fit.r2`, `dw`, `jb_p` DOLS reqressiyasınındır; notebook-un `REG` dəyərləri `fit.r2_levels`,
  `diagnostics.dw_levels`, `jb_p_levels`, `bp_fitted_p_levels`-dir.
* Dayanıqlıq hökmü (`stabil | qismən stabil | qeyri-stabil`) JSON başlığında `verdict_rule_az`.

## 3. Ssenari mühərrikləri (`microlib.engines`)
Notebook-un sonunda: `from microlib.engines.base import save_state; save_state("FR1", state)` →
`output/engine/FR1_state.json` + `.npz` (yalnız dict, list, massiv, DataFrame; funksiya yox).

```python
# microlib/engines/fr1.py
from microlib.engines import base as B
_S = None
def _st():
    global _S
    _S = _S or B.load_state("FR1"); return _S
def inputs(): return _st()["inputs"]          # {"exogenous": [...], "coefficients": [...], "levers": [...]}
def run(overrides=None, scenario="Baseline", upstream=None):
    ov = B.apply_overrides(inputs(), overrides, scenario)    # {"brent": {"pct": -10}}, {"FR1.C3_man|ln_K": 0.4}
    ...  # notebook-un həll kodu (dəyişmədən köçürülür); ov["exogenous"], ov["coefficients"]
    return B.make_result(series, meta={"module": "FR1", "scenario": scenario}, warnings=ov["warnings"])
def selftest():
    r = {sc: B.selftest_compare(B.result_to_frame(run({}, sc)), CSV, cols, tol=1e-8) for sc in SCEN}
    return {"ok": all(v["ok"] for v in r.values()), "detail": r}
```
Zəncir: `from microlib.engines.chain import run_chain; run_chain({"FR1": {...}}, "Adverse")` —
FR1 → FR3 → FR4 → FR5 və FR1 → FR10 → FR12; olmayan mühərriklər xəbərdarlıqla buraxılır.

## 4. Göstərici kataloqu
```python
from microlib.catalog import write_catalog, check_catalog
write_catalog(rows, f"{ROOT}/output/FR1_indicator_catalog.csv", "FR1")   # id 'fr1:<kod>', kind level|rate|share|index
check_catalog(cat_csv, f"{ROOT}/output/FR1_equations.json", engine_result)  # uyğunsuzluqların siyahısı
```

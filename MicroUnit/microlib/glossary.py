"""Azerbaijani terminology (contract section E) and fixed texts used in registry output."""

AZ = {
    "equation": "tənlik",
    "regression_output": "reqressiya nəticəsi",
    "coefficient": "əmsal",
    "se": "standart xəta",
    "t": "t-statistikası",
    "p": "p-dəyəri",
    "ci": "etibarlılıq intervalı",
    "nobs": "müşahidələr",
    "r2": "determinasiya əmsalı (R²)",
    "r2_adj": "düzəldilmiş determinasiya əmsalı (R²)",
    "resid": "qalıq",
    "fitted": "qiymətləndirilmiş",
    "dependent": "asılı dəyişən",
    "regressor": "izahedici dəyişən",
    "coint": "kointeqrasiya",
    "holdout": "nümunədən kənar yoxlama",
    "rw": "təsadüfi gəzişmə",
    "cg": "sabit artım",
    "scenario": "ssenari",
    "exogenous": "ekzogen",
    "forecast": "proqnoz",
    "robustness": "dayanıqlıq",
    "recursive": "rekursiv",
    "loo": "bir ili çıxarmaqla",
    "elasticity": "elastiklik",
    "synthetic": "sintetik",
    "hetero": "heteroskedastiklik",
    "normality": "normallıq",
    "autocorr": "avtokorrelyasiya",
    "break": "struktur qırılma",
    "fe": "sabit effektlər",
    "marginal": "marjinal effekt",
    "const": "sabit",
    "dof": "sərbəstlik dərəcəsi",
    "sample": "nümunə",
    "method": "qiymətləndirmə üsulu",
    "cov": "kovariasiya növü",
    "loglik": "log-həqiqətəbənzərlik",
    "fixed": "sabitlənmiş (məhdudiyyət)",
    "restriction": "məhdudiyyət",
}

SCENARIO_AZ = {"Baseline": "Əsas", "Adverse": "Mənfi", "Reform": "İslahat"}

VERDICTS = ("stabil", "qismən stabil", "qeyri-stabil")

VERDICT_RULE_AZ = (
    "Dayanıqlıq hökmü: 'stabil' — proqnozda istifadə olunan bütün əmsallar rekursiv (genişlənən pəncərə, "
    "minimum n = k+5) və bir ili çıxarmaqla qiymətləndirmələrdə işarəsini saxlayır və bütün mümkün Chow "
    "testlərinin (nümunənin ortası, 2015, 2020) və CUSUM testinin p-dəyəri > 0.05; 'qeyri-stabil' — rekursiv "
    "yolun son yarısında hər hansı əmsalın işarəsi dəyişir və ya hər hansı Chow testinin p-dəyəri < 0.01; "
    "qalan hallarda 'qismən stabil'. Rekursiv yol qurula bilmirsə, hökm 'stabil' ola bilməz."
)
VERDICT_RULE_EN = (
    "Verdict: 'stabil' if every used coefficient keeps its sign in the recursive (expanding window from n=k+5) "
    "and leave-one-year-out estimates and all feasible Chow (midpoint, 2015, 2020) and CUSUM p > 0.05; "
    "'qeyri-stabil' if a sign flips in the last half of the recursive path or any Chow p < 0.01; otherwise "
    "'qismən stabil'. Without a recursive path the verdict cannot be 'stabil'."
)

CONVENTIONS_AZ = (
    "Standart xətalar: Newey–West (Bartlett) HAC, gecikmə L = max(1, floor(4(n/100)^(2/9))), kiçik nümunə "
    "düzəlişi n/(n−k); p-dəyərləri və etibarlılıq intervalları t(n−k) paylanmasından. Kointeqrasiya: qalıqlar "
    "üzrə ADF (deterministik hədsiz, maxlag=1), MacKinnon p-dəyəri, N = I(1) izahedici dəyişənlərin sayı + 1, "
    "trend olduqda 'ct'; p ≤ 0.10 olduqda kointeqrasiya müəyyən edilmiş sayılır. DOLS tənliklərində yalnız "
    "uzunmüddətli əmsallar proqnozda istifadə olunur; fərq (lead/lag) hədləri yalnız qiymətləndirmə üçündür."
)


def coef_label(name, labels=None):
    labels = labels or {}
    if name in labels:
        return labels[name]
    if name == "const":
        return AZ["const"]
    return name

"""v2text.py — Azerbaijani rendering of the registry's plain-text regression summaries.

The module agents wrote the summaries with Azerbaijani labels; a few equations append the raw
statsmodels table, whose English header words are replaced here (column alignment is kept where
the Azerbaijani label is not longer than the English one, otherwise the line simply grows).
"""
import re

_MONTHS = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", "Jul": "07",
           "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}

# order matters: longer phrases first
PHRASES = [
    ("Dayanıqlıq (robustness)", "Dayanıqlıq"),
    ("qalıq (residual)", "qalıq"),
    ("Generalized Linear Model Regression Results", "Ümumiləşdirilmiş xətti model — reqressiya nəticəsi"),
    ("Poisson Regression Results", "Puasson reqressiyasının nəticəsi"),
    ("Logit Regression Results", "Logit reqressiyasının nəticəsi"),
    ("Probit Regression Results", "Probit reqressiyasının nəticəsi"),
    ("OLS Regression Results", "OLS reqressiyasının nəticəsi"),
    ("WLS Regression Results", "WLS reqressiyasının nəticəsi"),
    ("NegativeBinomial Regression Results", "Mənfi binomial reqressiyanın nəticəsi"),
    ("PHReg Results", "Cox təhlükə (hazard) modelinin nəticəsi"),
    ("Regression Results", "Reqressiya nəticəsi"),
    ("Dep. Variable:", "Asılı dəyişən:"),
    ("No. Observations:", "Müşahidələr:"),
    ("No. Iterations:", "İterasiyalar:"),
    ("Df Residuals:", "Qalıq s.d.:"),
    ("Df Model:", "Model s.d.:"),
    ("Pseudo R-squ.:", "Psevdo R²:"),
    ("Log-Likelihood:", "Log-həqiqətəbənzərlik:"),
    ("LL-Null:", "LL (sıfır):"),
    ("LLR p-value:", "LLR p-dəyəri:"),
    ("Covariance Type:", "Kovariasiya növü:"),
    ("Adj. R-squared:", "Düzəldilmiş R²:"),
    ("R-squared:", "R²:"),
    ("Prob (F-statistic):", "p-dəyəri (F):"),
    ("F-statistic:", "F-statistikası:"),
    ("Prob(Omnibus):", "p (Omnibus):"),
    ("Prob(JB):", "p (JB):"),
    ("Skew:", "Asimmetriya:"),
    ("Kurtosis:", "Ekses:"),
    ("Cond. No.", "Şərt ədədi"),
    ("Model Family:", "Model ailəsi:"),
    ("Link Function:", "Əlaqə funksiyası:"),
    ("Deviance:", "Deviasiya:"),
    ("Pearson chi2:", "Pirson χ²:"),
    ("Scale:", "Miqyas:"),
    ("Method:", "Üsul:"),
    ("Date:", "Tarix:"),
    ("Time:", "Vaxt:"),
    ("converged:", "yığılıb:"),
    ("Least Squares", "Ən kiçik kvadratlar"),
    ("nonrobust", "adi"),
    ("cluster", "klaster"),
    ("std err", "st. xəta"),
    ("P>|z|", "p-dəyəri"),
    ("P>|t|", "p-dəyəri"),
    ("Notes:", "Qeydlər:"),
    ("[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.",
     "[1] Standart xətalar xətaların kovariasiya matrisinin düzgün qurulduğunu fərz edir."),
    ("[1] Standard Errors are robust to cluster correlation (cluster)",
     "[1] Standart xətalar klaster daxilində korrelyasiyaya davamlıdır"),
    ("Standard Errors are heteroscedasticity and autocorrelation robust (HAC)",
     "Standart xətalar heteroskedastiklik və avtokorrelyasiyaya davamlıdır (HAC)"),
    ("small-sample", "kiçik nümunə"),
    ("coef ", "əmsal "),
]
WORDS = [(r"\bTrue\b", "bəli"), (r"\bFalse\b", "xeyr"), (r"\bvs\b", "və"), (r"\bNone\b", "—")]


def summary(s):
    if not s:
        return ""
    for en, az in PHRASES:
        s = s.replace(en, az)
    s = re.sub(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d\d) (\w{3}) (\d{4})",
               lambda m: f"{m.group(2)}.{_MONTHS.get(m.group(3), m.group(3))}.{m.group(4)}", s)
    for pat, az in WORDS:
        s = re.sub(pat, az, s)
    return s


def cov(s):
    """Covariance description, e.g. 'HAC(NW, L=3, small-sample n/(n-k))'."""
    if not isinstance(s, str):
        return "—"
    return (s.replace("small-sample", "kiçik nümunə düzəlişi").replace("cluster", "klaster")
            .replace("nonrobust", "adi"))

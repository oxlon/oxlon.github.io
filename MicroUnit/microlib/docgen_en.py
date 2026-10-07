"""docgen_en — English wording for generated text of the English methodology documents (docs/FRx_Methodology.md).

The registry and robustness tables carry their verdicts and failed-test notes in Azerbaijani (`stabil`, `rekursiv: x
işarəsi son yarıda dəyişir`, ...). The documentation steps of the notebooks use the two functions below so that the
ENGLISH document gets English text; the Azerbaijani document keeps the Azerbaijani wording (docgen_az*.py).

    from microlib import docgen_en as DE
    DE.verdict('qismən stabil')                      -> 'partly stable'
    DE.tests('rekursiv: c20 işarəsi yolun ilk yarısında dəyişir; Chow 2010 (orta nöqtə): p = 0.000')
                                                     -> 'recursive: sign of c20 flips in the first half; Chow 2010 (midpoint): p = 0.000'

Numbers, coefficient names and test names are kept exactly. A phrase without a rule is kept as it is and recorded in
`MISSES` (the notebooks print it), so a new wording is visible. Standard library only; nothing here changes an output.
"""
import re

VERDICT_EN = {"stabil": "stable", "qismən stabil": "partly stable", "qeyri-stabil": "unstable"}
MISSES = []

_RULES = [
    (r"^rekursiv: (.+?) işarəsi (?:yolun )?son yarı(?:da|sında) dəyişir$", r"recursive: sign of \1 flips in the last half"),
    (r"^rekursiv: (.+?) işarəsi (?:yolun )?ilk yarı(?:da|sında) dəyişir$", r"recursive: sign of \1 flips in the first half"),
    (r"^bir ili çıxarmaqla: (.+?) işarəsi dəyişir$", r"leave-one-year-out: sign of \1 flips"),
    (r"^bir ili çıxarmaqla işarə dəyişir: (.+)$", r"leave-one-year-out sign flip: \1"),
    (r"^rekursiv işarə dəyişir: (.+)$", r"recursive sign flip: \1"),
    (r"^rekursiv işarə dəyişməsi \((.+)\)$", r"recursive sign flip (\1)"),
    (r"^LOO işarə dəyişməsi \((.+)\)$", r"leave-one-year-out sign flip (\1)"),
    (r"^rekursiv qiymətləndirmə mümkün deyil$", "recursive estimation not possible"),
    (r"^testlər mümkün deyil / tam deyil$", "tests not possible / incomplete"),
    (r"^dayanıqlıq testləri bu qiymətləndirici üçün aparılmayıb$", "robustness tests not run for this estimator"),
    (r"^fərq forması ilə uyğunsuzluq$", "inconsistent with the difference form"),
    (r"^kointeqrasiya müəyyən edilməyib$", "cointegration not established"),
    (r"^heç biri$", "none"),
    (r"^bütün meyarlar ödənilir$", "all criteria met"),
    (r"^istifadə olunan dəyər \((.+?)\) 95% intervaldan kənar \(EB büzülməsi\)$", r"value used (\1) outside the 95% interval (EB shrinkage)"),
    (r"^istifadə olunan dəyər \((.+?)\) 95% intervaldan kənar \(tətbiq edilmiş qayda\)$", r"value used (\1) outside the 95% interval (imposed rule)"),
    (r"^istifadə olunan dəyər \((.+?)\) 95% intervaldan kənar$", r"value used (\1) outside the 95% interval"),
]
_RULES = [(re.compile(a), b) for a, b in _RULES]
_AZ = re.compile(r"[əğışöüçİƏŞÇÖÜĞ]")


def verdict(v):
    """Registry verdict in English ('stabil' -> 'stable'); anything else unchanged."""
    return VERDICT_EN.get(str(v).strip(), v)


def _one(p):
    p = p.strip()
    if p.startswith("Chow") or p.startswith("CUSUM"):
        return p.replace("orta nöqtə", "midpoint")
    for rx, sub in _RULES:
        if rx.fullmatch(p):
            return rx.sub(sub, p)
    if _AZ.search(p):
        MISSES.append(p)
    return p


def tests(s):
    """Failed-test note ('; '-separated phrases) in English."""
    if s is None or (isinstance(s, float) and s != s):
        return "—"
    s = str(s)
    if s.strip() in ("", "—"):
        return s.strip() or "—"
    return "; ".join(_one(p) for p in s.split("; "))


def counts(vc, order=("stabil", "qismən stabil", "qeyri-stabil")):
    """'stable 19, partly stable 40, unstable 66' from verdict counts (a value_counts() Series or a dict)."""
    return ", ".join(f"{VERDICT_EN[k]} {int(vc.get(k, 0))}" for k in order)

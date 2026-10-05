"""p_i18n.py — Azerbaijani at build time: panel/i18n/az.csv + the modules' FRx_strings_az.csv, and the
untranslated-English check over the generated bundles, the JS sources and index.html.

az.csv columns: mode (exact | phrase | regex), en, az, note. Order of application: exact match of the whole
string (az.csv first, then FRx_strings_az.csv), then phrase rows (longest first), then regex rows.
The check is a word-list heuristic: prose English words (≥ 2 letters, not valid Azerbaijani words) in any
displayed string. Tokens with digits or underscores (codes), the variable codes of the equation in hand and
ALLOW (proper names, codes, units) are ignored.
"""
import csv
import json
import re
from pathlib import Path

from . import pcore as C

AZCSV = C.PANEL / "i18n" / "az.csv"
EN = set("""the and of for with from this that these those are was were been being not only also which when where while than
then into onto each both other such used using based results result estimate estimated estimates estimation sample forecast forecasts
scenario scenarios share shares growth output price prices value values year years firm firms industry sector sectors data error errors
standard confidence level levels rate rates equation equations regression residual residuals fitted observed observations mean
total constant calibrated rule effects fixed cluster pooled dummies demand cost costs shock entry exit merger import tariff energy
partial full mixed linear identity allocation ratio least squares section division absorbed conditional weights frequency link logistic
binomial hazard baseline adverse reform income wage wages employment employed persons manufacturing mining small large size cohort
survival probability marginal average note notes see none true false upper lower bound bounds recursive leave break structural stable
unstable partly driver drivers market markets weighted shrinkage system contemporaneous deterministic regressor regressors stochastic
chosen candidate rejected coefficient coefficients elasticity static anchored anchor last actual within between oneway twoway
first differences difference projected correction applied contains requires column columns is in or to by it its no yes if all any
one two three per vs via under over without after before because however whereas therefore since until must should would could can
cannot may might will shall has have had does did done simplest coherent inferior specification relative rolling origins passed scored
estimable loading loaded saved settings reports tables charts warning missing please wait finished failed success cancel previous
""".split())
ALLOW = set("""OLS DOLS HAC NW HHI CR4 KOS AZN USD NACE DSK GDP R² SE TFP IV DWH ML MLE GLM WLS LS SUR LA-AIDS AIDS EG ADF DW JB BG
CUSUM RESET VIF AIC BIC MNL OR IRR AME ROC AUC Boone Cournot Driscoll-Kraay DK Huber RLM statsmodels Plotly Excel Word PDF CSV JSON
XLSX DOCX HTML API MİİS Engle-Granger MacKinnon Newey-West Theil Chow Kaplan-Meyer Kaplan Meyer Farrell Shapiro Tornqvist Webb
Hausman Hall Griliches Brent Bayes hazard binomial Binomial Wald Sargan Hosmer Lemeshow Brier Puasson Poisson Logit logit cloglog probit Ctrl Esc Enter
""".split())
_TOK = re.compile(r"[\s,;:()\[\]{}«»\"'`+<>≤≥|*·—–…!?]+")

# English number format in the modules' prose ("4,648 müəssisə", "R² = 0.273", "−1.411", "[0.5, 1.0]") → Azerbaijani
# (decimal comma, no-break-space thousands, "−"). Thousands commas are read as such only when the same string also has
# an English decimal point (otherwise "1,234" may already be an Azerbaijani decimal). Codes are left alone: dotted
# chains (05.06.2026, 15.5.2, FR10.reg), DSK/NACE table numbers ("DSK 2.12–2.13 cədvəlləri") and section numbers
# ("9.2-ci hissə"). Length-preserving, so the aligned columns of the text-format regression summary stay aligned.
NBSP = " "
_ENGDEC = re.compile(r"\d\.\d")
_NUMLIST = re.compile(r"([\[(])(\s*-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+\s*)([\])])")
_NUM = re.compile(r"((?<![^\s(\[=≈<>:;,/])-)?(?<![\w.,])([1-9]\d{0,2}(?:,\d{3})+(?!\d)|\d+)(\.\d+)?(?!\w|\.\w|,\d)")
_SKB = re.compile(r"(?:DSK|NACE|Part|§|cədvəl\w*|bölmə\w*|hissə\w*)\s*(?:\d+\.\d+\s*[–-]\s*)?$")
_SKA = re.compile(r"-(?:ci|cı|cu|cü)\b|\s*[–-]\s*\d+\.\d+\s*cədvəl|\s*cədvəl")


def az_numbers(s):
    if not isinstance(s, str) or not _ENGDEC.search(s):
        return s
    s = _NUMLIST.sub(lambda m: m.group(1) + re.sub(r"\s*,\s*", "; ", m.group(2)) + m.group(3) if "." in m.group(2) else m.group(0), s)

    def fix(m):
        sign, ip, dp = m.group(1) or "", m.group(2), m.group(3) or ""
        if not dp and "," not in ip:
            return m.group(0)
        if _SKB.search(m.string[max(0, m.start() - 16):m.start()]) or _SKA.match(m.string, m.end()):
            return m.group(0)
        return ("−" if sign else "") + ip.replace(",", NBSP) + ("," + dp[1:] if dp else "")
    return _NUM.sub(fix, s)


class Tr:
    def __init__(self):
        self.exact, self.phrase, self.regex, self.used = {}, [], [], set()
        if AZCSV.exists():
            with AZCSV.open(encoding="utf-8") as fh:
                for r in csv.DictReader(fh):
                    m, en, az = (r.get("mode") or "phrase").strip(), r["en"], r["az"]
                    if not en:
                        continue
                    if m == "exact":
                        self.exact[en] = az
                    elif m == "regex":
                        self.regex.append((re.compile(en), az))
                    else:
                        self.phrase.append((en, az))
        for mod in ("FR1", "FR3", "FR4", "FR5", "FR10", "FR12"):
            p = C.OUT / f"{mod}_strings_az.csv"
            if p.exists():
                for r in C.read_retry(p, dtype=str, keep_default_na=False).to_dict("records"):
                    if r.get("en") and r.get("az") and r["en"] not in self.exact:
                        self.exact[r["en"]] = r["az"]
        self.phrase.sort(key=lambda x: -len(x[0]))

    def __call__(self, s):
        if not isinstance(s, str) or not s:
            return s
        if s in self.exact:
            self.used.add(s)
            return az_numbers(self.exact[s])
        for en, az in self.phrase:
            if en in s:
                s = s.replace(en, az)
        for rx, az in self.regex:
            s = rx.sub(az, s)
        return az_numbers(s)

    def deep(self, o, skip=()):
        if isinstance(o, dict):
            return {k: (v if k in skip else self.deep(v, skip)) for k, v in o.items()}
        if isinstance(o, list):
            return [self.deep(v, skip) for v in o]
        return self(o)


def bad_words(s, allow=()):
    out = []
    for tok in _TOK.split(s):
        if not tok or any(ch in tok for ch in "_/=@#&\\") or any(ch.isdigit() for ch in tok) or tok in ALLOW or tok in allow:
            continue
        if "." in tok.strip("."):                   # file names, dotted codes
            continue
        w = tok.strip(".-%").lower()
        if w in EN and tok.strip(".-%") not in allow:
            out.append(w)
    return out


def scan(obj, where, skip_keys, allow=(), out=None):
    """Collect (where, text) for every string value with English prose words; skip_keys are code fields."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        loc = set(allow) | set(obj.get("_allow", []))
        for k, v in obj.items():
            if k not in skip_keys and k != "_allow":
                scan(v, f"{where}.{k}", skip_keys, loc, out)
    elif isinstance(obj, list):
        for v in obj:
            scan(v, where, skip_keys, allow, out)
    elif isinstance(obj, str):
        for line in obj.split("\n"):
            b = bad_words(line, allow)
            if b:
                out.append((where, line.strip()[:220], ",".join(sorted(set(b)))))
    return out


_JSSTR = re.compile(r"'((?:[^'\\\n]|\\.)*)'")


def scan_js(paths):
    out = []
    for p in paths:
        txt = Path(p).read_text(encoding="utf-8")
        for i, line in enumerate(txt.split("\n"), 1):
            if line.strip().startswith(("//", "/*", "*")):
                continue
            for m in _JSSTR.finditer(line):
                s = re.sub(r"<[^>]*>|^[^<]*?>|<[^>]*$|\b[\w-]+=\"[^\"]*\"?", " ", m.group(1))
                if " " not in s.strip():          # single tokens are code (event names, CSS, Plotly keys)
                    continue
                b = bad_words(s)
                if b:
                    out.append((f"{Path(p).name}:{i}", s.strip()[:160], ",".join(sorted(set(b)))))
    return out


def scan_html(path):
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", Path(path).read_text(encoding="utf-8"), flags=re.S)
    txt = re.sub(r"<[^>]+>", "\n", txt)
    return [(Path(path).name, ln.strip()[:160], ",".join(sorted(set(b)))) for ln in txt.split("\n")
            if (b := bad_words(ln))]


def dump_report(rows, path):
    path.write_text("\n".join("\t".join(r) for r in rows) + ("\n" if rows else ""), encoding="utf-8")


def to_json(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

"""b_i18n.py — Azerbaijani at build time: panel/i18n/az.csv (exact | phrase | regex rows) applied to every string
cell that goes into a bundle, English → Azerbaijani number format in prose, and the untranslated-English check
over bundles, JS string literals, index.html and the hub page (word-list heuristic + allow-list).
Copied from RiskUnit/panel/_build/b_i18n.py (not imported); word lists extended for the PolicyUnit.
"""
import csv
import re
from pathlib import Path

from . import bcore as C

AZCSV = C.PANEL / "i18n" / "az.csv"
# columns that hold codes, ids, dates, urls — never translated, never scanned
CODE_COLS = set("""scenario indicator engine group sector shocked_sector target kpi id rule_id risk_ids event_id row_id
primary_row file owner columns updated run_at key cpa product_name_en name_en nace_section nace_list cpa_products fr1_group
fr4_sector_map fr10_branch_map fr10_branches instrument instruments engines target_key transform cost_rule cost_in_fr1 metric
op thresholds params series cf_rule cf_alt obs_check source_engine method_code indicator_id baseline_id fetched_at variant_id
formula pair shock tags engines files naive_rule tol_set measure ok complete caem_reliable top3 converged kind compare direction stat default_selected code regime sign_agree available selected key financing unit_code decile years kind_code measures es_method status_code legal_source chain_id
""".split())
EN = set("""the and of for with from this that these those are was were been being not only also which when where while than
then into each both other such used using based results result estimate estimated estimates estimation sample forecast forecasts
scenario scenarios share shares growth output price prices value values year years data error errors standard confidence level
levels rate rates equation regression residual fitted observed observations mean total constant shock shocks import energy
partial full linear ratio baseline adverse income wage employment probability average note notes see none true false
upper lower bound recursive structural stable unstable market markets weighted deterministic stochastic chosen rejected
coefficient elasticity static last actual within between first difference projected applied contains requires column is in or
to by it its no yes if all any one two per via under over without after before because however therefore since must should
would could can cannot will has have had does did persistent productivity labour labor population monetary policy inflation
cost push demand supply government spending tax revenue exchange gap interest foreign domestic consumption investment
exports imports oil gas central republic ministry finance fund state statistics committee bond bonds yield yields auction
daily monthly quarterly annual index risks loss losses capital account current primary balance debt reserves assets
""".split())
ALLOW = set("""OLS DOLS HAC HHI AZN USD EUR GBP CNY JPY TRY RUB CHF XAU NACE DSK GDP R² SE VaR ES CaR CCA GaR IaR FaR CAaR ORaR EVT
GPD AWHS HS CF MC MK Kupiec Christoffersen Acerbi Székely Acerbi–Székely Bazel Basel Kornish-Fişer Cornish-Fisher Euler Gray Merton
Bodie Gray–Merton–Bodie Monte Karlo Carlo FRED GPR EPU USGS ERA5 ComCat Caldara Iacoviello Caldara–Iacoviello Baker Bloom Davis
Baker–Bloom–Davis GEPU SPI WMO IMF BVF FAO PFOODINDEXM DCOILBRENTEU VIXCLS DGS10 FEDFUNDS DEXUSEU VIX Brent Azeri Light AMB ARDNF
BFB MN CAEM AZE OxLon MikroUnit MicroUnit RU FR1 FR2 FR3 FR4 FR5 FR10 FR12 NFR1 NFR2 MİİS Excel Word PDF CSV JSON XLSX DOCX HTML API
Plotly Ctrl Esc Enter Theil Chow PIT CRPS AUROC ROC AUC milp scipy Python EViews SUMPRODUCT MMULT MINVERSE IFNA Bottom-up SEI MOE
UST EM HY OECD SPX Henry Hub HH LNG SOFAZ CBAR Qant Gantt GFN DSA DD PD Working t-kopula Scenario Data IF AVERAGE
STDEV.P INPUT MOE_report Indicator Time Series Policy Measure Forecast Result Backtest Alert Risk Register
IO Leontief Ghosh Rasmussen GRAS RAS Sobol TFP KPI Gini FGT CPA Cobb Duglas Cobb–Duglas MTEF DiD HBS LFS EBT ÜSY DSMF İQİ ƏDV ÜDM
PolicyUnit RiskUnit Macro_OxLon FR13 FR11 NFR3 NFR4 IOT SUT BL FL CV RMSE MAPE WMAPE HHI AI-92 AI-95 MƏH UAT DQ PIT SSC CIT VAT
Tax Summaries PwC Kakwani Suits Atkinson Foster–Greer–Thorbecke Foster Greer Thorbecke OxLon-un CAEM-də CAEM-in IO-da IO-nun
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

    def df(self, d, skip=()):
        """Translate the string cells of a DataFrame (code columns untouched)."""
        if d is None:
            return d
        d = d.copy()
        for c in d.columns:
            if c in CODE_COLS or c in skip or d[c].dtype != object:
                continue
            d[c] = d[c].map(lambda v: self(v) if isinstance(v, str) else v)
        return d

    def deep(self, o, skip=()):
        if isinstance(o, dict):
            return {k: (v if k in skip or k in CODE_COLS else self.deep(v, skip)) for k, v in o.items()}
        if isinstance(o, list):
            return [self.deep(v, skip) for v in o]
        return self(o)


def bad_words(s, allow=()):
    out = []
    for tok in _TOK.split(s):
        if not tok or any(ch in tok for ch in "_/=@#&\\") or any(ch.isdigit() for ch in tok) or tok in ALLOW or tok in allow:
            continue
        if "." in tok.strip(".") or tok.startswith("-"):
            continue
        w = tok.strip(".-%").lower()
        if w in EN:
            out.append(w)
    return out

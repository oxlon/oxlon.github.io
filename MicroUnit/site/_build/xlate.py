"""xlate.py — build-time check for leftover English on the generated site.

Heuristic: every visible text node, every user-facing attribute (title, aria-label, alt, placeholder,
meta description), the string values of every inline Plotly spec (trace names, axis titles,
annotations, hover templates) and the string literals of `assets/site.js` are split into words;
a word that is on the English word list below (and not on the allow-list of proper names, codes
and units) is reported. Text inside <code>, and tokens that look like identifiers (contain digits,
underscores, slashes, dots or hyphens), are skipped. The build fails if anything is found.
`assets/plotly-az.js` is the translation table for Plotly's own toolbar (English keys by design)
and is not scanned.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

# Common English words that are not also Azerbaijani words (so "model", "test", "panel", "real",
# "region", "status", "trend", "bank", "nominal", "media", "plan", "start" are deliberately absent).
EN_WORDS = set("""
the and of to in is are was were be been being for with from by at as this that these those which
who what when where why how not no yes or but if then than so such it its into over under about
after before between per via all any each every both other more most less least few many much
can could should would will shall may might must do does did done have has had having
data forecast forecasts forecasting equation equations coefficient coefficients estimate estimates
estimated estimation regression residual residuals fitted actual sample samples observations
growth share shares output value values price prices total rate rates level levels index
employment wage wages services service sector sectors firm firms entry exit market markets
chart charts figure figures table tables file files page pages row rows column columns loading
renderer loaded present could read scenario scenarios baseline adverse reform error errors
standard deviation confidence lower upper band bands mean sum average
synthetic enterprise not only imputed interpolation interpolated gap gaps filled missing
download open close show hide expand collapse copy copied search filter reset apply run save
stable unstable partly robust robustness recursive break breaks structural cointegration
dependent variable variables regressor regressors intercept constant time year years month
annual quarterly monthly weekly daily source sources note notes summary details detail overview
home back next previous menu contents section sections results result method methods methodology
notebook notebooks report reports builder dashboard view classic help guide instructions
upload uploads uploading launcher token tokens request requests response code
warning warnings fail failed failure passed pass success successful check checks checked
hold holdout out one leave random walk naive benchmark benchmarks skill accuracy performance
heteroskedasticity normality autocorrelation specification functional form tests tested
effect effects fixed elasticity elasticities marginal survival curve curves
recovery parameter parameters true bias coverage card cards models estimator estimators
small large high low higher lower increase decrease change changes difference differences
income consumption investment government public private state budget oil gas non
industry industrial manufacturing mining agriculture construction trade transport
households household population employed employees workers labour labor unemployment
concentration competition entrants exits births deaths register registered units unit
here there now new old first last same different number numbers amount
""".split())

# Proper names, product names, codes, units and abbreviations that may legitimately appear.
ALLOW = set("""
AZN USD EUR mln mlrd NACE HHI CR4 CR DOLS OLS FMOLS IV 2SLS 3SLS SUR FE RE GMM HAC NW DK BG JB
DW AIC BIC VIF ADF KPSS EG CUSUM RESET Chow Theil Brent Newey West Bartlett MacKinnon Driscoll Kraay
Durbin Watson Breusch Godfrey Pagan Jarque Bera White Ramsey Engle Granger Diebold Mariano Boone
Herfindahl Hirschman Lerner Cobb Douglas Olley Pakes Levinsohn Petrin Kaplan Meier Cox Hausman
Sargan Hansen Wald Wooldridge Mundlak Hodrick Prescott Tobit Probit Logit logit probit Poisson
Plotly Jupyter Python Excel Word Chrome Google Drive macOS Windows Linux SQLite OpenAPI JSON CSV
HTML PDF API URL HTTP HTTPS curl nginx launchd Bearer OR IRR HR GET POST DELETE PUT ROC AUC TFP KOS ÜDM DSK
MİİS TT FR FR1 FR3 FR4 FR5 FR10 FR12 SYNTHETIC REAL OBSERVED Baseline Adverse Reform Actual
Task Scheduler shift-share UTF md5 sha256 xlsx docx csv ipynb html md py js
""".split())

ALLOW_PHRASES = ["Task Scheduler", "Statistik data dinamika", "Data Kataloq", "SYNTHETIC — not real enterprise data", "not real enterprise data"]

SKIP_TAGS = {"script", "style", "code", "svg"}
ATTRS = ("title", "aria-label", "alt", "placeholder")
SPEC_KEYS = {"name", "text", "hovertemplate", "title"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks, self.specs, self._skip, self._spec = [], [], 0, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ATTRS:
            if a.get(k):
                self.chunks.append(a[k])
        if tag == "meta" and a.get("name") == "description":
            self.chunks.append(a.get("content") or "")
        if tag == "script" and a.get("type") == "application/json":
            self._spec = []
        if tag in SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == "script" and self._spec is not None:
            self.specs.append("".join(self._spec))
            self._spec = None
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._spec is not None:
            self._spec.append(data)
        elif not self._skip:
            self.chunks.append(data)


def _spec_strings(obj, out, key=None):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _spec_strings(v, out, k)
    elif isinstance(obj, list):
        for v in obj:
            _spec_strings(v, out, key)
    elif isinstance(obj, str) and key in SPEC_KEYS:
        out.append(re.sub(r"%\{[^}]*\}|<[^>]+>", " ", obj))


_STRIP = "«»\"'“”‘’()[]{},.;:!?…·•—–|*+=<>"


def english_words(text, extra=frozenset()):
    for ph in ALLOW_PHRASES:
        text = text.replace(ph, " ")
    hits = []
    for tok in text.split():
        t = tok.strip(_STRIP)
        if re.fullmatch(r"[A-Za-z]+(-[A-Za-z]+)+", t or ""):   # hyphenated English compounds: hold-out, firm-level
            parts = t.split("-")
            if t not in ALLOW and not all(x in ALLOW for x in parts) and any(x.lower() in EN_WORDS for x in parts):
                hits.append(t)
            continue
        if not t or not re.fullmatch(r"[A-Za-z]+(['’][a-z]+)?", t):
            continue                                  # identifiers, numbers, Azerbaijani words
        if t in ALLOW or t in extra:
            continue
        if t.lower() in EN_WORDS:
            hits.append(t)
    return hits


def scan_html(path, extra=frozenset()):
    p = _Text()
    p.feed(Path(path).read_text(encoding="utf-8"))
    chunks = list(p.chunks)
    for js in p.specs:
        try:
            _spec_strings(json.loads(js), chunks)
        except ValueError:
            pass
    found = {}
    for c in chunks:
        for w in english_words(c, extra):
            found.setdefault(w, c.strip()[:90])
    return found


def scan_js(path):
    src = Path(path).read_text(encoding="utf-8")
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"(?m)^\s*//.*$", " ", src)
    found = {}
    for m in re.finditer(r"'((?:[^'\\\n]|\\.)*)'", src):
        s = m.group(1)
        if " " not in s or re.match(r"^\s*[.#\[]|^[a-z]+(\.[\w-]+|\[[^\]]*\])", s):
            continue                                   # single tokens and CSS selectors are code, not text
        for w in english_words(s):
            found.setdefault(w, s[:90])
    return found


def run(site, extra=frozenset()):
    site = Path(site)
    problems = []
    pages = sorted(p for p in site.rglob("*.html") if "assets" not in p.parts)
    for p in pages:
        for w, ctx in sorted(scan_html(p, extra).items()):
            problems.append(f"{p.relative_to(site)}: «{w}» in «{ctx}»")
    js = site / "assets" / "site.js"
    if js.exists():
        for w, ctx in sorted(scan_js(js).items()):
            problems.append(f"assets/site.js: «{w}» in «{ctx}»")
    if problems:
        print(f"\nTRANSLATION CHECK: {len(problems)} leftover English word(s)")
        for x in problems[:200]:
            print("  -", x)
        return False
    print(f"\nTRANSLATION CHECK: OK — {len(pages)} pages and site.js, no leftover English "
          f"(word list {len(EN_WORDS)}, allow-list {len(ALLOW)})")
    return True

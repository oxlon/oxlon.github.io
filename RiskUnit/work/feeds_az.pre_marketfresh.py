"""Automatic Azerbaijan feeds (v2): official markets and statistics, each with a parser, a raw cache and a status.

    cbar_fx       CBAR official FX bulletin, daily XML https://www.cbar.az/currencies/DD.MM.YYYY.xml (all currencies
                  + bank metals; USD, EUR, RUB, TRY, GBP, CNY, XAU headline). Backfill: month-starts 2015+ and every
                  day of the last 2 years, at most `budget` requests per run (politely, ≤ 1 req/s, cached per date).
    cbar_rate     CBAR refinancing (uçot) rate and corridor floor/ceiling (cbar.az/infoblocks/corridor_*?year=Y) and
                  the monetary-policy decision dates (cbar.az/page-134/monetary-policy-decisions).
    dsk_macro     DSK "Monthly macroeconomic indicators" (stat.gov.az/news/macroeconomy.php?page=1..10): GDP, oil-gas
                  and non-oil GDP, industry, agriculture, retail, investment, state budget revenue/expenditure/surplus,
                  strategic reserves, external debt, credit, deposits, incomes, wages, CPI, trade — Jan–M cumulative.
    dsk_cpi       DSK consumer-price press release (latest month: m/m and y/y, food / non-food / services).
    dsk_tables    DSK .xls tables via MicroUnit's DSK download logic (browser UA, BIFF magic check): 001_1en (annual
                  growth indices) and 03qua (quarterly GDP, nominal and constant prices) → RU's own vintages.
    minfin        Ministry of Finance: approved state-budget indicator workbooks (maliyye.gov.az/static/254) and the
                  list of operative execution reports (static/105). Monthly execution comes from dsk_macro.
    sofaz         SOFAZ recent figures (assets) + the latest quarterly investment-results PDF (currency and asset-class
                  allocation, gold) when `pdftotext` is available.
    bfb           Baku Stock Exchange auction results (MoF government bonds, CBAR notes): yields, volume, demand.
    azeri_light   No free public Azeri Light series exists → proxy = FRED Brent + documented spread (median of the
                  MicroUnit FR1 oil export price − Brent annual average, 2015–2025).

Raw responses: data/vintages/<source>/<date>/…; normalised series go through feeds._store (data/vintages/<date>/<feed>.csv
+ manifest.csv), so feeds.latest('<feed>') works for every module. RISK_NO_NETWORK=1 → last good cache.
"""
from __future__ import annotations

import html as _html
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd

from . import config, feeds

UA = feeds.BROWSER_UA
CBAR_FX_URL = "https://www.cbar.az/currencies/{d}.xml"
CBAR_RATE_URL = "https://www.cbar.az/infoblocks/{key}?year={y}"
CBAR_DECISIONS_URL = "https://www.cbar.az/page-134/monetary-policy-decisions"
DSK_MACRO_URL = "https://www.stat.gov.az/news/macroeconomy.php?lang=en&page={p}"
DSK_HOME = "https://www.stat.gov.az/?lang=en"
DSK_NEWS = "https://www.stat.gov.az/news/index.php?lang=en&id={id}"
DSK_TABLE_URL = "https://www.stat.gov.az/source/{sec}/en/{fn}"
DSK_TABLES = [("system_nat_accounts", "001_1en.xls"), ("system_nat_accounts", "03qua.xls")]
MINFIN_APPROVED = "https://www.maliyye.gov.az/static/254/tesdiq-olunmus-dovlet-budcesinin-esas-gostericileri"
MINFIN_OPERATIVE = "https://www.maliyye.gov.az/static/105/dovlet-budcesinin-icrasina-dair-operativ-melumat"
MINFIN_BASE = "https://www.maliyye.gov.az"
SOFAZ_RECENT = "https://www.oilfund.az/en/report-and-statistics/recent-figures"
SOFAZ_QUARTERLY = "https://www.oilfund.az/en/investments/quarterly-investment-results"
BFB_LIST = "https://www.bfb.az/en/press-releases?page={p}"
BFB_BASE = "https://www.bfb.az"
HEADLINE_FX = ["USD", "EUR", "RUB", "TRY", "GBP", "CNY", "XAU"]
XLS_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")     # same check as MicroUnit/api/validate_dsk.py


def _micro_dsk_constants():
    """Reuse MicroUnit's DSK download conventions (browser UA, BIFF magic) when the package is reachable."""
    global UA, XLS_MAGIC
    api = config.MICRO_DIR / "api"
    if api.is_dir() and str(api) not in sys.path:
        sys.path.insert(0, str(api))
    try:
        import validate_dsk                          # noqa: F401  (stdlib-only module)
        XLS_MAGIC = validate_dsk.XLS_MAGIC
    except Exception:                                # noqa: BLE001
        pass


_micro_dsk_constants()


# ---------------------------------------------------------------- shared plumbing
def raw_dir(source: str, day: str | None = None):
    p = config.VINTAGES / source / (day or config.as_of().isoformat())
    p.mkdir(parents=True, exist_ok=True)
    return p


def get(url: str, source: str, name: str, day: str | None = None, reuse: bool = False) -> bytes:
    """Fetch with the raw cache: data/vintages/<source>/<day>/<name>. reuse=True returns the cached copy
    without a request (immutable resources such as a past day's FX bulletin)."""
    p = raw_dir(source, day) / name
    if reuse and p.exists() and p.stat().st_size > 0:
        return p.read_bytes()
    try:
        b = feeds._get(url, timeout=20, ua=UA)
    except feeds.NoNetwork:
        if p.exists():
            return p.read_bytes()
        raise
    p.write_bytes(b)
    return b


def cached(source: str, name: str) -> list:
    """Every cached raw copy of a resource, newest day first."""
    d = config.VINTAGES / source
    return sorted(d.glob(f"*/{name}"), reverse=True) if d.is_dir() else []


def text(html: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    s = _html.unescape(re.sub(r"<[^>]+>", " | ", s))
    return re.sub(r"(\s*\|\s*)+", " | ", re.sub(r"\s+", " ", s))


def num(s) -> float:
    """'87 709,5' → 87709.5 ; '1.7' → 1.7 ; 'x' → nan."""
    if s is None:
        return np.nan
    s = str(s).replace("\xa0", " ").strip().rstrip("*")
    s = re.sub(r"[^\d,.\-+]", "", s.replace(" ", ""))
    if s.count(",") == 1 and s.count(".") == 0 and not re.search(r",\d{3}$", s):
        s = s.replace(",", ".")                        # decimal comma: '87709,5'
    elif s.count(",") >= 1:
        s = s.replace(",", "")                         # thousands separators: '20,000,000', '99,459.27' 
    try:
        return float(s)
    except ValueError:
        return np.nan


def previous(feed: str) -> pd.DataFrame:
    try:
        return feeds.latest(feed)
    except FileNotFoundError:
        return pd.DataFrame()


def merge_history(feed: str, new: pd.DataFrame, keys=("series", "date")) -> pd.DataFrame:
    """Accumulate: previous vintage + new observations (new wins on the same key)."""
    old = previous(feed)
    d = pd.concat([old, new], ignore_index=True) if len(old) else new
    return d.drop_duplicates(list(keys), keep="last").sort_values(list(keys)).reset_index(drop=True)


# ---------------------------------------------------------------- CBAR official FX bulletin
FX_RE = re.compile(r'<Valute Code="(\w+)">\s*<Nominal>([^<]*)</Nominal>\s*<Name>([^<]*)</Name>\s*<Value>([^<]*)</Value>')


def parse_cbar_fx(raw: bytes, day: str) -> pd.DataFrame:
    t = raw.decode("utf-8", "ignore")
    m = re.search(r'ValCurs Date="(\d{2})\.(\d{2})\.(\d{4})"', t)
    d = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else day
    rows = []
    for code, nominal, name, value in FX_RE.findall(t):
        n = num(nominal.split()[0]) or 1.0
        rows.append({"series": f"cbar_{code.lower()}", "date": d, "value": num(value) / n,
                     "unit": f"AZN / 1 {code}" if code[0] != "X" else "AZN / troy unsiya", "name": name.strip()})
    return pd.DataFrame(rows)


def fx_dates(today: date, budget: int, have: set[str]) -> list[date]:
    """Dates still missing, in priority order: weekdays of the last 10 days, weekdays of the last 2 years
    (newest first), then the first day of every month from 2015; at most `budget` of them."""
    want = [today - timedelta(days=k) for k in range(0, 731)]
    want = [d for d in want if d.weekday() < 5]
    d = date(2015, 1, 1)
    while d < today - timedelta(days=730):
        want.append(d)
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    res, seen = [], set()
    for x in want:
        k = x.isoformat()
        if k not in have and k not in seen:
            seen.add(k)
            res.append(x)
    return res[:budget]


def fetch_cbar_fx(budget: int = 40) -> tuple[pd.DataFrame, str]:
    prev = previous("cbar_fx")
    have = set(prev["date"].astype(str)) if len(prev) else set()
    have |= {p.parent.name for p in (config.VINTAGES / "cbar_fx").glob("*/bulletin.xml")} if (config.VINTAGES / "cbar_fx").is_dir() else set()
    frames = []
    for p in sorted((config.VINTAGES / "cbar_fx").glob("*/bulletin.xml")) if (config.VINTAGES / "cbar_fx").is_dir() else []:
        frames.append(parse_cbar_fx(p.read_bytes(), p.parent.name))
    shared = config.VINTAGES / "cbar_fx" / "cbar_fx_daily.csv"   # same bulletin, fetched by feeds_market (VaR layer)
    if shared.exists():                              # reuse it instead of requesting the same XML twice (politeness)
        try:
            t = pd.read_csv(shared)
            frames.append(pd.DataFrame({"series": "cbar_" + t["code"].str.lower(), "date": t["date"].astype(str),
                                        "value": t["azn_per_unit"], "unit": "AZN / 1 " + t["code"], "name": "feeds_market"}))
            have |= set(t.groupby("date")["code"].count()[lambda c: c >= 7].index.astype(str))
        except Exception:                            # noqa: BLE001
            pass
    today = config.as_of()
    for d in fx_dates(today, budget, have - {today.isoformat()}):
        try:
            raw = get(CBAR_FX_URL.format(d=d.strftime("%d.%m.%Y")), "cbar_fx", "bulletin.xml", d.isoformat(),
                      reuse=d < today)
        except feeds.NoNetwork:
            break
        except Exception:                            # noqa: BLE001  (holiday / transient) — try next date
            continue
        frames.append(parse_cbar_fx(raw, d.isoformat()))
    new = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["series", "date", "value"])
    return merge_history("cbar_fx", new), CBAR_FX_URL.format(d="DD.MM.YYYY")


# ---------------------------------------------------------------- CBAR policy rate, corridor and decisions
RATE_KEYS = {"corridor_percent": "cbar_policy_rate", "corridor_min": "cbar_corridor_floor",
             "corridor_max": "cbar_corridor_ceiling"}
ROW_RE = re.compile(r'class="valuta">\s*(\d{2})\.(\d{2})\.(\d{4})\s*</div>\s*<div class="kod">\s*([\d.,]+)\s*%')


def parse_cbar_rate(raw: bytes, series: str) -> pd.DataFrame:
    t = raw.decode("utf-8", "ignore")
    return pd.DataFrame([{"series": series, "date": f"{y}-{m}-{d}", "value": num(v), "unit": "%"}
                         for d, m, y, v in ROW_RE.findall(t)])


def parse_cbar_decisions(raw: bytes) -> pd.DataFrame:
    """Decision titles with dates; the change (pp) is read from the title when stated, else left blank and
    later derived from the rate series."""
    rows = []
    for title, d, m, y in re.findall(r">\s*([^<>]{10,200}?)\s*\((\d{2})\.(\d{2})\.(\d{4})\)\s*<", raw.decode("utf-8", "ignore")):
        t = _html.unescape(title).strip()
        if not re.search(r"(?i)faiz|uçot|dəhliz", t):
            continue
        ch = np.nan
        mm = re.search(r"([\d.,]+)\s*(?:faiz bəndi|%)\s*(azaldıl|artırıl)", t)
        if mm:
            ch = num(mm.group(1)) * (-1 if mm.group(2).startswith("azal") else 1)
        elif re.search(r"(?i)dəyişməz|sabit", t) and not re.search(r"(?i)eni|genişlən|daral", t):
            ch = 0.0
        rows.append({"series": "cbar_decision", "date": f"{y}-{m}-{d}", "value": ch, "unit": "f.b.", "name": t[:160]})
    return pd.DataFrame(rows).drop_duplicates(["date"]) if rows else pd.DataFrame(columns=["series", "date", "value"])


def fetch_cbar_rate() -> tuple[pd.DataFrame, str]:
    today = config.as_of()
    frames = []
    for key, series in RATE_KEYS.items():
        for y in range(2010, today.year + 1):
            name = f"{key}_{y}.html"
            done = cached("cbar_rate", name)
            if y < today.year and done:              # past years are immutable
                frames.append(parse_cbar_rate(done[0].read_bytes(), series))
                continue
            try:
                frames.append(parse_cbar_rate(get(CBAR_RATE_URL.format(key=key, y=y), "cbar_rate", name), series))
            except feeds.NoNetwork:
                if done:
                    frames.append(parse_cbar_rate(done[0].read_bytes(), series))
            except Exception:                        # noqa: BLE001
                continue
    try:
        frames.append(parse_cbar_decisions(get(CBAR_DECISIONS_URL, "cbar_rate", "decisions.html")))
    except Exception:                                # noqa: BLE001
        c = cached("cbar_rate", "decisions.html")
        if c:
            frames.append(parse_cbar_decisions(c[0].read_bytes()))
    new = pd.concat([f for f in frames if len(f)], ignore_index=True)
    return merge_history("cbar_rate", new), CBAR_RATE_URL.format(key="corridor_*", y="YYYY")


# ---------------------------------------------------------------- DSK monthly macroeconomic indicators
DSK_MAP = [  # (regex on the row label, code) — first match wins, in row order
    (r"^gross domestic product", "gdp"), (r"^(?:including: )?non[ -]oil[ -]?gas gdp|^including: non oil-gas gdp", "gdp_nonoil"),
    (r"^oil-gas gdp", "gdp_oil"), (r"^industrial product", "industry"), (r"non[ -]oil[ -]?gas industry", "industry_nonoil"),
    (r"^agricultural product", "agriculture"), (r"^retail trade turnover", "retail"),
    (r"^investments? (?:to|directed to) fixed capital", "investment"),
    (r"^state budget revenues|^income of state budget", "budget_rev"),
    (r"^state budget expenditures|^expenditure of state budget", "budget_exp"),
    (r"^budget surplus|^surplus of state budget", "budget_bal"), (r"^strategic currency reserves", "reserves_usd"),
    (r"^external public debt", "ext_debt_usd"), (r"^credit (?:investments|exposure)", "credit"),
    (r"deposits", "deposits"), (r"^nominal incomes? of (?:the )?population", "incomes"),
    (r"^average monthly nominal salary", "wage"), (r"^inflation|^consumer price index", "cpi"),
    (r"^(?:foreign )?trade turnover", "trade"), (r"^export$", "export"), (r"^import$", "import")]
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def _period(header: str) -> str | None:
    h = header.lower()
    ms = [MONTHS[w] for w in re.findall(r"[a-z]+", h) if w in MONTHS]
    y = re.findall(r"(20\d\d)", h)
    return f"{y[0]}-{ms[-1]:02d}-01" if ms and y else None


def _growth(cell: str, index_form: bool) -> float:
    c = str(cell).strip()
    if not c or c.lower().startswith("x") or c.endswith("t."):
        return np.nan
    v = num(c.replace("%", ""))
    return v - 100 if index_form and "%" not in c and np.isfinite(v) else v


def parse_dsk_macro(raw: bytes) -> pd.DataFrame:
    t = raw.decode("utf-8", "ignore")
    j = t.find("<table")
    tb = t[j:t.find("</table>", j)]
    trs = [[re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S)] for tr in re.findall(r"<tr.*?</tr>", tb, flags=re.S)]
    if not trs:
        return pd.DataFrame()
    per = _period(trs[0][1]) if len(trs[0]) > 1 else None
    index_form = "percent" in " ".join(trs[0]).lower()          # older layout: indices (previous year = 100)
    rows, done = [], set()
    for r in trs[1:]:
        if len(r) < 3:
            continue
        lab = re.sub(r"\s+\d\s*,", ",", r[0]).strip().lower()
        for pat, code in DSK_MAP:
            if code not in done and re.search(pat, lab):
                done.add(code)
                v, g = num(r[1]), _growth(r[2], index_form)
                rows.append({"series": f"dsk_{code}_ytd", "date": per, "value": v, "unit": "Yanvar–ay, cəmi", "name": r[0]})
                rows.append({"series": f"dsk_{code}_ytd_yoy", "date": per, "value": g, "unit": "%, ötən ilin eyni dövrünə",
                             "name": r[0]})
                break
    return pd.DataFrame(rows).dropna(subset=["date"])


def fetch_dsk_macro(pages=range(1, 11)) -> tuple[pd.DataFrame, str]:
    frames = []
    for p in pages:
        try:
            frames.append(parse_dsk_macro(get(DSK_MACRO_URL.format(p=p), "dsk_macro", f"page{p}.html")))
        except feeds.NoNetwork:
            for c in cached("dsk_macro", f"page{p}.html")[:1]:
                frames.append(parse_dsk_macro(c.read_bytes()))
        except Exception:                            # noqa: BLE001
            continue
    new = pd.concat([f for f in frames if len(f)], ignore_index=True) if frames else pd.DataFrame()
    return merge_history("dsk_macro", new), DSK_MACRO_URL.format(p="1..10")


# ---------------------------------------------------------------- DSK consumer-price press release
def _signed(word: str, v: float) -> float:
    return -v if word.lower().startswith("decreas") else v


def parse_dsk_cpi(raw: bytes) -> pd.DataFrame:
    t = text(raw.decode("utf-8", "ignore"))
    m = re.search(r"In (\w+) of the current year,? consumer prices (increased|decreased) by ([\d,\.]+) ?% compared (?:with|to) "
                  r"(\w+) and by ([\d,\.]+) ?% compared (?:with|to) (\w+) (20\d\d)", t)
    if not m:
        return pd.DataFrame(columns=["series", "date", "value"])
    ytd = re.search(r"Consumer price index in January-(\w+) (20\d\d) compared to January-\w+ 20\d\d (increased|decreased) by ([\d,\.]+)", t)
    mon = MONTHS.get(m.group(1).lower())
    year = int(ytd.group(2)) if ytd else int(m.group(7)) + 1      # y/y is against the same month a year earlier
    d = f"{year}-{mon:02d}-01"
    rows = [{"series": "dsk_cpi_mm", "date": d, "value": _signed(m.group(2), num(m.group(3))), "unit": "%, ötən aya"},
            {"series": "dsk_cpi_yoy", "date": d, "value": num(m.group(5)), "unit": "%, ötən ilin eyni ayına"}]
    for grp, code in (("food products, beverages and tobacco products", "food"), ("non-food products", "nonfood"),
                      ("paid services provided to population", "services")):
        mm = re.search(rf"consumer prices for {re.escape(grp)} (increased|decreased) by ([\d,\.]+) ?% compared to the previous "
                       rf"month and by ([\d,\.]+) ?%", t)
        if mm:
            rows += [{"series": f"dsk_cpi_{code}_mm", "date": d, "value": _signed(mm.group(1), num(mm.group(2))), "unit": "%"},
                     {"series": f"dsk_cpi_{code}_yoy", "date": d, "value": num(mm.group(3)), "unit": "%"}]
    if ytd:
        rows.append({"series": "dsk_cpi_ytd_avg_yoy", "date": d, "value": _signed(ytd.group(3), num(ytd.group(4))), "unit": "%"})
    return pd.DataFrame(rows)


def fetch_dsk_cpi() -> tuple[pd.DataFrame, str]:
    try:
        home = get(DSK_HOME, "dsk_cpi", "home.html").decode("utf-8", "ignore")
        ids = [m.group(1) for m in re.finditer(r"<a[^>]*id=(\d+)[^>]*>(.*?)</a>", home, flags=re.S)
               if re.search(r"Changes in prices of consumer market|^\s*Consumer prices in January",
                            re.sub(r"<[^>]+>", "", m.group(2)))]
        raw = get(DSK_NEWS.format(id=ids[0]), "dsk_cpi", "release.html") if ids else b""
    except feeds.NoNetwork:
        c = cached("dsk_cpi", "release.html")
        raw = c[0].read_bytes() if c else b""
    new = parse_dsk_cpi(raw) if raw else pd.DataFrame(columns=["series", "date", "value"])
    return merge_history("dsk_cpi", new), DSK_NEWS.format(id="<son buraxılış>")


# ---------------------------------------------------------------- DSK .xls tables (MicroUnit download logic)
def parse_dsk_xls(raw: bytes, fn: str) -> pd.DataFrame:
    import xlrd
    if raw[:8] != XLS_MAGIC:
        raise ValueError("cavab .xls deyil (HTML səhifə?)")
    wb = xlrd.open_workbook(file_contents=raw)
    rows = []
    if fn.startswith("001_1"):
        sh = wb.sheet_by_index(0)
        hdr = next(r for r in range(min(sh.nrows, 10)) if sum(isinstance(v, float) and 1990 < v < 2100 for v in sh.row_values(r)) >= 4)
        yrs = {c: int(v) for c, v in enumerate(sh.row_values(hdr)) if isinstance(v, float) and 1990 < v < 2100}
        for r in range(hdr + 1, sh.nrows):
            lab = str(sh.cell_value(r, 1)).strip()
            if not lab:
                continue
            for c, y in yrs.items():
                v = sh.cell_value(r, c)
                if isinstance(v, float):
                    rows.append({"series": "dsk_a_" + re.sub(r"[^a-z0-9]+", "_", lab.lower())[:40].strip("_"),
                                 "date": f"{y}-01-01", "value": v - 100, "unit": "%, artım (əvvəlki il = 100)", "name": lab})
    elif fn.startswith("03qua"):
        for k, tag in ((0, "nominal"), (1, "real")):
            if k >= wb.nsheets:
                continue
            sh = wb.sheet_by_index(k)
            yr_row = next(r for r in range(10) if sum(isinstance(v, float) and 1990 < v < 2100 for v in sh.row_values(r)) >= 3)
            yr, cols = None, {}
            for c, v in enumerate(sh.row_values(yr_row)):
                yr = int(v) if isinstance(v, float) and 1990 < v < 2100 else yr
                q = str(sh.cell_value(yr_row + 1, c)).strip()
                if yr and q in ("Q1", "Q2", "Q3", "Q4"):
                    cols[c] = f"{yr}-{3 * int(q[1]) - 2:02d}-01"
            for r in range(yr_row + 2, sh.nrows):
                if re.search(r"(?i)gross domestic product|^gdp", str(sh.cell_value(r, 1))):
                    for c, d in cols.items():
                        v = sh.cell_value(r, c)
                        if isinstance(v, float):
                            rows.append({"series": f"dsk_q_gdp_{tag}", "date": d, "value": v, "unit": "mln AZN, rüb",
                                         "name": sh.name})
                    break
    out = pd.DataFrame(rows)
    if len(out) and (out["series"] == "dsk_q_gdp_real").any():
        r = out[out["series"] == "dsk_q_gdp_real"].set_index("date")["value"].sort_index()
        g = (r / r.shift(4) - 1) * 100
        out = pd.concat([out, pd.DataFrame({"series": "dsk_q_gdp_real_yoy", "date": g.index, "value": g.values,
                                            "unit": "%, ötən ilin eyni rübünə"}).dropna()], ignore_index=True)
    return out


def fetch_dsk_tables() -> tuple[pd.DataFrame, str]:
    frames = []
    for sec, fn in DSK_TABLES:
        try:
            frames.append(parse_dsk_xls(get(DSK_TABLE_URL.format(sec=sec, fn=fn), "dsk_tables", fn), fn))
        except Exception:                            # noqa: BLE001  (offline / HTML instead of xls → last good copy)
            for c in cached("dsk_tables", fn):
                try:
                    frames.append(parse_dsk_xls(c.read_bytes(), fn))
                    break
                except Exception:                    # noqa: BLE001
                    continue
    new = pd.concat([f for f in frames if len(f)], ignore_index=True) if frames else pd.DataFrame()
    return merge_history("dsk_tables", new), DSK_TABLE_URL.format(sec="system_nat_accounts", fn="{001_1en,03qua}.xls")


# ---------------------------------------------------------------- Ministry of Finance (approved budget workbooks)
MF_ROWS = [(r"^Dövlət büdcəsinin gəlirləri", "minfin_state_rev"), (r"^Xərclərin cəmi", "minfin_state_exp")]


def parse_minfin_xlsx(raw: bytes, title: str) -> pd.DataFrame:
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(max_row=40, max_col=14, values_only=True))
    wb.close()
    yr_row = next((i for i, r in enumerate(rows) if sum(isinstance(v, (int, float)) and 2000 < v < 2100 for v in r) >= 2
                   or sum(isinstance(v, str) and re.match(r"\s*20\d\d", v or "") is not None for v in r) >= 2), None)
    if yr_row is None:
        return pd.DataFrame()
    years, cur = {}, None
    for c in range(len(rows[yr_row])):                # years may sit in merged cells over two columns
        for rr in (yr_row, yr_row + 1):
            v = rows[rr][c] if rr < len(rows) else None
            mm = re.match(r"\s*(20\d\d)", str(v)) if v is not None else None
            if mm:
                cur = int(mm.group(1))
        years[c] = cur
    status = {}
    for c in years:
        lab = " ".join(str(rows[r][c]) for r in range(yr_row, min(yr_row + 4, len(rows))) if isinstance(rows[r][c], str))
        status[c] = "tesdiq" if re.search(r"(?i)təsdiq|proqnoz", lab) else ("fakt" if re.search(r"(?i)fakt|icra", lab) else "")
    out = []
    for r in rows[yr_row + 1:]:
        lab = " ".join(str(v) for v in r[:3] if isinstance(v, str)).strip()
        for pat, code in MF_ROWS:
            if re.search(pat, lab):
                for c, y in years.items():
                    v = r[c] if c < len(r) else None
                    if y and isinstance(v, (int, float)) and abs(v) > 1000 and status.get(c):
                        out.append({"series": f"{code}_{status[c]}", "date": f"{y}-01-01", "value": float(v),
                                    "unit": "mln AZN", "name": title[:120]})
    return pd.DataFrame(out).drop_duplicates(["series", "date"], keep="last") if out else pd.DataFrame()


def fetch_minfin() -> tuple[pd.DataFrame, str]:
    frames, today = [], config.as_of().isoformat()
    try:
        page = get(MINFIN_APPROVED, "minfin", "approved.html").decode("utf-8", "ignore")
    except feeds.NoNetwork:
        c = cached("minfin", "approved.html")
        page = c[0].read_text("utf-8", "ignore") if c else ""
    for m in re.finditer(r"(?:href|file)=[\"']?([^\"' >]*?/uploads/static-pages/files/([0-9a-f]+\.xlsx))", page):
        url, fn = m.group(1), m.group(2)
        i = page.find(fn)
        title = text(page[max(0, i - 900):i])[-200:]
        try:
            raw = get(url if url.startswith("http") else MINFIN_BASE + url, "minfin", fn, day="files", reuse=True)
            d = parse_minfin_xlsx(raw, title)
            if len(d):
                frames.append(d)
        except Exception:                            # noqa: BLE001
            continue
    try:
        op = get(MINFIN_OPERATIVE, "minfin", "operative.html").decode("utf-8", "ignore")
        items = re.findall(r"(20\d\d)-c[iıuü]\s*il[^<|]{0,80}?(?:rüb|ay)[^<|]{0,120}", text(op))
        latest = re.search(r"(20\d\d)-c[iıuü] ilin ([IV]+) rübü üzrə[^|]{0,140}", text(op))
        if latest:
            q = {"I": 1, "II": 2, "III": 3, "IV": 4}.get(latest.group(2), 1)
            frames.append(pd.DataFrame([{"series": "minfin_operative_report", "date": f"{latest.group(1)}-{3 * q:02d}-01",
                                         "value": float(q), "unit": "son operativ hesabat (rüb)", "name": latest.group(0)[:160]}]))
        del items
    except Exception:                                # noqa: BLE001
        pass
    new = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["series", "date", "value"])
    del today
    return merge_history("minfin", new), MINFIN_APPROVED


# ---------------------------------------------------------------- SOFAZ
def parse_sofaz_recent(raw: bytes) -> pd.DataFrame:
    t = text(raw.decode("utf-8", "ignore"))
    m = re.search(r"Information as of (\w+) (\d{1,2})\s*\|?\s*,?\s*\|?\s*(20\d\d)\s*\|?\s*SOFAZ.{0,12}s assets: USD ([\d\s.,]+) mln", t)
    if not m:
        return pd.DataFrame(columns=["series", "date", "value"])
    d = f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    rows = [{"series": "sofaz_assets_usd_mln", "date": d, "value": num(m.group(4)), "unit": "mln ABŞ dolları"}]
    tr = re.search(r"AZN ([\d\s.,]+) MLN\.? \| Transfers to the state budget", t)
    if tr:
        rows.append({"series": "sofaz_transfers_cum_azn_mln", "date": d, "value": num(tr.group(1)), "unit": "mln AZN, yığılmış"})
    return pd.DataFrame(rows)


def parse_sofaz_pdf_text(t: str, d: str) -> pd.DataFrame:
    rows = []
    for lab, code in (("US Dollar", "usd"), ("Euro", "eur"), ("British Pound Sterling", "gbp"), ("Chinese Yuan", "cny"),
                      ("Japanese Yen", "jpy"), ("Other Currencies", "other")):
        m = re.search(rf"{lab}\*?:\s*(?:\$|€|£|CNY|JPY)?\s*([\d\s.,]+?)\s*million", t)
        if m:
            rows.append({"series": f"sofaz_ccy_{code}_mln", "date": d, "value": num(m.group(1)), "unit": "mln, valyutada"})
    g = re.search(r"gold investments worth\s*USD\s*([\d\s.,]+?)\s*million\s*\(([\d.,]+)%\)", t)
    if g:
        rows += [{"series": "sofaz_gold_usd_mln", "date": d, "value": num(g.group(1)), "unit": "mln ABŞ dolları"},
                 {"series": "sofaz_gold_share_pct", "date": d, "value": num(g.group(2)), "unit": "%"}]
    i = t.find("asset class")
    pc = [num(x) for x in re.findall(r"(\d{1,2}[.,]\d)%", t[i:i + 900])] if i >= 0 else []
    if len(pc) >= 4 and 97 <= sum(pc[:4]) <= 103:   # layout order: fixed income, equities, gold, real estate
        for code, v in zip(("fixed_income", "equities", "gold", "real_estate"), pc[:4]):
            rows.append({"series": f"sofaz_class_{code}_pct", "date": d, "value": v, "unit": "%"})
    ton = re.search(r"\(([\d.,]+)\s*TONS\)", t)
    if ton:
        rows.append({"series": "sofaz_gold_tons", "date": d, "value": num(ton.group(1)), "unit": "ton"})
    return pd.DataFrame(rows)


def fetch_sofaz() -> tuple[pd.DataFrame, str]:
    frames = []
    try:
        frames.append(parse_sofaz_recent(get(SOFAZ_RECENT, "sofaz", "recent.html")))
    except feeds.NoNetwork:
        for c in cached("sofaz", "recent.html")[:1]:
            frames.append(parse_sofaz_recent(c.read_bytes()))
    except Exception:                                # noqa: BLE001
        pass
    try:
        q = get(SOFAZ_QUARTERLY, "sofaz", "quarterly.html").decode("utf-8", "ignore")
        m = re.search(r'href="(https://www\.oilfund\.az/storage/uploads/[a-z0-9]+\.pdf)"', q)
        if m:
            fn = m.group(1).rsplit("/", 1)[1]
            raw = get(m.group(1), "sofaz", fn, day="files", reuse=True)
            p = config.VINTAGES / "sofaz" / "files" / fn
            t = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True, timeout=20).stdout
            dd = re.search(r"(\d{2})\.(\d{2})\.(20\d\d)", t)
            frames.append(parse_sofaz_pdf_text(t, f"{dd.group(3)}-{dd.group(2)}-{dd.group(1)}" if dd else "1970-01-01"))
            del raw
    except Exception:                                # noqa: BLE001  (offline, no pdftotext) — keep history
        pass
    new = pd.concat([f for f in frames if len(f)], ignore_index=True) if frames else pd.DataFrame(columns=["series", "date", "value"])
    return merge_history("sofaz", new), SOFAZ_RECENT


# ---------------------------------------------------------------- Baku Stock Exchange auctions
POST_RE = re.compile(r'/en/post/(an-auction-was-held-for-(?:the-)?placement-of-[a-z0-9-]+)')


def _field(t: str, lab: str) -> str:
    m = re.search(rf"\| ?{re.escape(lab)} ?\| ?([^|]+)", t)
    return m.group(1).strip() if m else ""


def _yield(s: str) -> float:
    m = re.search(r"\(([\d.,]+)\s*%\)", s)
    return num(m.group(1)) if m else np.nan


def parse_bfb_post(raw: bytes, slug: str) -> dict | None:
    t = text(raw.decode("utf-8", "ignore"))
    m = re.search(r"On\s+(\w+)\s+(\d{1,2}),\s+(20\d\d),\s+an auction was held", t)
    if not m or m.group(1).lower() not in MONTHS:
        return None
    issuer = _field(t, "Issuer")
    kind = ("mof_bond" if "Ministry of Finance" in issuer else "cbar_note" if "Central Bank" in issuer else "other")
    mat = re.search(r"(\d+)\s*-?\s*day", _field(t, "Maturity of bonds") or _field(t, "The term of the note") or slug)
    return {"date": f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}", "kind": kind, "issuer": issuer,
            "isin": re.sub(r"[^A-Z0-9]", "", _field(t, "State registration number - ISIN") or "")[:12],
            "maturity_days": float(mat.group(1)) if mat else np.nan, "coupon": num(_field(t, "Coupon Rate")),
            "avg_yield": _yield(_field(t, "Average price")), "cut_yield": _yield(_field(t, "Cutting price")),
            "volume_azn": num(_field(t, "Realized volume")),
            "demand_azn": num(_field(t, "Total volume of orders (at nominal price)")),
            "offer_azn": num(_field(t, "Release volume") or _field(t, "Emission volume")), "slug": slug}


def fetch_bfb(pages: int = 2, max_posts: int = 30) -> tuple[pd.DataFrame, str]:
    prev = previous("bfb")
    seen = set(prev["slug"]) if len(prev) and "slug" in prev else set()
    recs, n = [], 0
    for p in range(1, pages + 1):
        try:
            lst = get(BFB_LIST.format(p=p), "bfb", f"list{p}.html").decode("utf-8", "ignore")
        except Exception:                            # noqa: BLE001
            break
        for slug in dict.fromkeys(POST_RE.findall(lst)):
            if slug in seen or n >= max_posts or "mortgage" in slug or "bonds-of-" in slug and "ministry" not in slug:
                continue
            try:
                r = parse_bfb_post(get(f"{BFB_BASE}/en/post/{slug}", "bfb", f"{slug}.html", day="posts", reuse=True), slug)
                n += 1
            except Exception:                        # noqa: BLE001
                continue
            if r:
                recs.append(r)
                seen.add(slug)
    rows = []
    for r in recs:
        tag = f"bfb_{r['kind']}"
        for f_, u in (("avg_yield", "%"), ("cut_yield", "%"), ("volume_azn", "AZN"), ("demand_azn", "AZN")):
            rows.append({"series": f"{tag}_{f_}", "date": r["date"], "value": r[f_], "unit": u, "slug": r["slug"],
                         "isin": r["isin"], "maturity_days": r["maturity_days"], "name": r["issuer"][:80]})
    new = pd.DataFrame(rows)
    if not len(new):
        return (prev if len(prev) else pd.DataFrame(columns=["series", "date", "value"])), BFB_LIST.format(p=1)
    return merge_history("bfb", new, keys=("series", "date", "slug")), BFB_LIST.format(p="1..")


# ---------------------------------------------------------------- Azeri Light proxy
def azeri_spread() -> tuple[float, str]:
    """Median (2015–2025) of MicroUnit FR1 oil export price − OxLon Brent annual average (USD/bbl)."""
    from . import upstream
    S = upstream.store()
    ex = S[(S["id"] == "fr1:oil_exp_price") & (S["scenario"] == "ACTUAL")].set_index("year")["value"]
    br = S[(S["id"] == "mx:brent_usd") & (S["kind"] == "actual")].set_index("year")["value"]
    d = (ex - br).dropna()
    d = d[(d.index >= 2015) & (d.index <= config.LAST_ACTUAL)]
    return (float(d.median()) if len(d) >= 5 else 0.0), f"median {int(d.index.min())}–{int(d.index.max())}, n={len(d)}"


def build_azeri_proxy() -> tuple[pd.DataFrame, str]:
    br = feeds.latest("brent")
    sp, how = azeri_spread()
    br = br[pd.to_datetime(br["date"]) >= pd.Timestamp("2015-01-01")]
    return (pd.DataFrame({"series": "azeri_light_proxy", "date": br["date"], "value": br["value"] + sp,
                          "unit": "USD/barel", "name": f"Brent + spred {sp:+.2f} ({how})"}),
            "FRED DCOILBRENTEU + spred (FR1 ixrac qiyməti − Brent)")


# ---------------------------------------------------------------- orchestration, status (D2) and market panel (D4)
# feed: (fetcher, source label (AZ), expected frequency, headline series, unit label)
AZ_FEEDS = {
    "cbar_fx": (fetch_cbar_fx, "AMB rəsmi məzənnə bülleteni (XML)", "gündəlik", "cbar_usd", "AZN/USD"),
    "cbar_rate": (fetch_cbar_rate, "AMB uçot dərəcəsi, faiz dəhlizi və qərarlar", "hadisə", "cbar_policy_rate", "%"),
    "dsk_macro": (fetch_dsk_macro, "DSK aylıq makroiqtisadi göstəricilər", "aylıq", "dsk_gdp_ytd_yoy", "%"),
    "dsk_cpi": (fetch_dsk_cpi, "DSK istehlak qiymətləri buraxılışı", "aylıq", "dsk_cpi_yoy", "%"),
    "dsk_tables": (fetch_dsk_tables, "DSK cədvəlləri (001_1, rüblük ÜDM)", "rüblük", "dsk_q_gdp_real_yoy", "%"),
    "minfin": (fetch_minfin, "Maliyyə Nazirliyi: təsdiq olunmuş büdcə göstəriciləri", "illik", "minfin_state_rev_tesdiq",
               "mln AZN"),
    "sofaz": (fetch_sofaz, "ARDNF (SOFAZ): aktivlər və portfel bölgüsü", "rüblük", "sofaz_assets_usd_mln", "mln USD"),
    "bfb": (fetch_bfb, "Bakı Fond Birjası: DQK və AMB notları hərracları", "hadisə", "bfb_mof_bond_avg_yield", "%"),
}
GLOBAL_FEEDS = {"brent": ("FRED Brent (DCOILBRENTEU)", "gündəlik", "brent_usd_daily", "USD/barel"),
                "vix": ("FRED VIX", "gündəlik", "vix", "indeks"), "ust10": ("FRED ABŞ 10 illik", "gündəlik", "ust10y", "%"),
                "fedfunds": ("FRED Fed faizi", "aylıq", "fedfunds", "%"), "eurusd": ("FRED EUR/USD", "gündəlik", "eurusd", "USD"),
                "gpr": ("Geosiyasi risk indeksi (GPR)", "aylıq", "gpr_global", "indeks"),
                "epu": ("Qlobal iqtisadi siyasət qeyri-müəyyənliyi (EPU)", "aylıq", "epu_global", "indeks"),
                "usgs": ("USGS zəlzələlər M≥4,5", "hadisə", "eq_mag", "M"), "era5": ("ERA5 yağıntı (4 nöqtə)", "aylıq",
                                                                                   "precip_aran", "mm"),
                "azeri_light": ("Azeri Light (proksi: Brent + spred)", "gündəlik", "azeri_light_proxy", "USD/barel")}
FRESH = {"gündəlik": (5, 12), "aylıq": (75, 110), "rüblük": (200, 290), "illik": (400, 600), "hadisə": (3, 10)}
# v2.4 freshness rules (audit M8): one rule per feed, from its frequency and publication lag.
#   period end   = end of the reference period of the newest observation (day / month / quarter / year);
#   next due     = period end + period length + publication lag  (the date the NEXT observation should exist);
#   tazelik      = təzə while today ≤ next due; köhnəlir up to next due + grace; köhnə after (= max age exceeded).
# Event series (rate decisions, auctions, earthquakes) stay valid until the next event: their age is the days since
# the last successful retrieval (next due = last check + 1 day). core=True feeds raise a stage ERROR when their fetch
# fails or they exceed the max age; any other failure is a WARNING.
FREQ_CODE = {"gündəlik": "D", "aylıq": "M", "rüblük": "Q", "illik": "A", "hadisə": "E"}
PERIOD_LEN = {"D": 3, "M": 30, "Q": 91, "A": 365, "E": 1}      # D: 3 days covers a weekend
GRACE = {"D": 7, "M": 30, "Q": 45, "A": 60, "E": 7}
FEED_RULES = {  # feed: (publication lag in days after the period end, core feed?, justification)
    "brent": (7, True, "FRED DCOILBRENTEU: EIA həftəlik yeniləyir (≈ 5–7 gün gecikmə)"),
    "vix": (3, False, "FRED VIXCLS: 1–2 iş günü"), "ust10": (3, False, "FRED DGS10: 1–2 iş günü"),
    "fedfunds": (5, False, "FRED FEDFUNDS: ayın ilk günləri"), "eurusd": (7, False, "FRED DEXUSEU: həftəlik H.10"),
    "gpr": (10, False, "GPR: ayın ilk 10 günü"), "epu": (45, False, "EPU qlobal: ≈ 1,5 ay gecikmə"),
    "usgs": (0, False, "USGS hadisə kataloqu: real vaxt"), "era5": (10, False, "Open-Meteo ERA5: ≈ 5–10 gün"),
    "azeri_light": (7, False, "Brent + spred (Brent-dən törəmə)"),
    "cbar_fx": (1, True, "AMB rəsmi məzənnə: hər iş günü"), "cbar_rate": (0, True, "AMB qərarları: hadisə"),
    "dsk_macro": (30, True, "DSK aylıq buraxılış: ay bitdikdən ≈ 20–30 gün sonra"),
    "dsk_cpi": (25, True, "DSK İQİ buraxılışı: ay bitdikdən ≈ 15–25 gün sonra"),
    "dsk_tables": (60, False, "DSK rüblük ÜDM cədvəlləri: rüb bitdikdən ≈ 45–60 gün sonra"),
    "minfin": (-365, False, "Təsdiq olunmuş büdcə: Y ili üçün Y−1-in sonunadək (2026-10: MN səhifəsində yalnız "
                            "27.12.2024 xlsx faylları var — 2026 büdcəsi cədvəl kimi dərc olunmayıb)"),
    "sofaz": (60, False, "ARDNF rüblük hesabatı: rüb bitdikdən ≈ 45–60 gün sonra"),
    "bfb": (0, False, "BFB hərracları: hadisə"),
}


def freshness(feed: str, freq: str, last_obs: str, last_ok_utc: str | None, today: pd.Timestamp) -> dict:
    """Period end, next due date, max age and the freshness class of one feed (see FEED_RULES)."""
    code = FREQ_CODE.get(freq, "D")
    lag, core, why = FEED_RULES.get(feed, (7, False, "standart qayda"))
    if code == "E":
        ref = pd.Timestamp(str(last_ok_utc)[:10]) if last_ok_utc else (pd.Timestamp(last_obs) if last_obs else None)
    elif not last_obs:
        ref = None
    else:
        t = pd.Timestamp(last_obs)
        ref = {"D": t, "M": t + pd.offsets.MonthEnd(0), "Q": t + pd.offsets.QuarterEnd(0),
               "A": t + pd.offsets.YearEnd(0)}[code]
    if ref is None:
        return {"dovr_sonu": "", "novbeti_gozlenilen": "", "max_yas_gun": np.nan, "yas_dovr_sonundan_gun": np.nan,
                "tazelik": "məlumat yoxdur", "nuve": core, "tazelik_qaydasi": why}
    due = ref + pd.Timedelta(days=PERIOD_LEN[code] + lag)
    fresh = "təzə" if today <= due else ("köhnəlir" if today <= due + pd.Timedelta(days=GRACE[code]) else "köhnə")
    return {"dovr_sonu": ref.date().isoformat(), "novbeti_gozlenilen": due.date().isoformat(),
            "max_yas_gun": int(PERIOD_LEN[code] + lag + GRACE[code]), "yas_dovr_sonundan_gun": int((today - ref).days),
            "tazelik": fresh, "nuve": core, "tazelik_qaydasi": f"{why}; dövr {PERIOD_LEN[code]} gün + gecikmə {lag} + "
                                                             f"güzəşt {GRACE[code]}"}


def _row(feed, vintage, url, status, df=None, prev=None) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"feed": feed, "vintage": vintage, "retrieved_utc": now, "path": "", "sha256": "", "n_obs": 0, "first_obs": "",
            "last_obs": "", "url": url, "status": status}


def fetch_all_az(fx_budget: int = 40, bfb_pages: int = 2, verbose: bool = True, only=None) -> pd.DataFrame:
    """Fetch every AZ feed once (offline: record cache status only). Returns the manifest rows written."""
    vintage = config.as_of().isoformat()
    man = feeds.read_manifest()
    rows = []
    for feed, (fn, lab, *_r) in AZ_FEEDS.items():
        if only and feed not in only:
            continue
        if config.no_network():
            rows.append(_row(feed, vintage, "", "keş: şəbəkə yoxdur"))
        else:
            try:
                kw = {"budget": fx_budget} if feed == "cbar_fx" else ({"pages": bfb_pages} if feed == "bfb" else {})
                df, url = fn(**kw)
                if df is None or not len(df):
                    raise ValueError("boş cavab (səhifə strukturu dəyişib?)")
                df["date"] = df["date"].astype(str)
                rows.append(feeds._store(feed, df, url, man, vintage))
            except Exception as exc:                 # noqa: BLE001
                rows.append(_row(feed, vintage, "", f"xeta: {type(exc).__name__}: {str(exc)[:80]}"))
        if verbose:
            r = rows[-1]
            print(f"  {feed:11s} {r['status'][:40]:>40s}  {r['n_obs']:>7} müşahidə, son: {r['last_obs']}")
    if not only or "azeri_light" in only:
        try:
            if config.no_network():
                raise feeds.NoNetwork("oflayn")
            df, url = build_azeri_proxy()
            rows.append(feeds._store("azeri_light", df, url, man, vintage))
        except Exception as exc:                     # noqa: BLE001
            rows.append(_row("azeri_light", vintage, "", feeds._fail_status(exc)))
    new = pd.DataFrame(rows, columns=feeds.MANIFEST_COLS).astype(str)
    cur = feeds.read_manifest()                      # re-read: another stage may have appended meanwhile
    pd.concat([cur, new], ignore_index=True).to_csv(feeds.MANIFEST, index=False, lineterminator="\n")
    return new


def _headline(feed: str, series: str):
    try:
        d = feeds.latest(feed)
    except FileNotFoundError:
        return np.nan, "", 0
    s = d[d["series"] == series] if "series" in d.columns else d
    s = s.dropna(subset=["value"]) if "value" in s.columns else s
    if s.empty:
        return np.nan, "", len(d)
    s = s.sort_values("date")
    return float(s["value"].iloc[-1]), str(s["date"].iloc[-1])[:10], len(d)


OWNERS = ("feeds", "feeds_az")
D2_COLS = ["feed", "owner_module", "source", "tezlik", "esas_sira", "vahid", "son_deyer", "last_obs", "yas_gun", "tazelik",
           "status", "retrieved_utc", "n_obs", "url", "path", "note"]
D2_EXTRA = ["seviyye", "nuve", "son_hadise", "dovr_sonu", "yas_dovr_sonundan_gun", "novbeti_gozlenilen", "max_yas_gun",
            "tazelik_qaydasi", "son_cehd_utc"]


def write_feed_status(st: pd.DataFrame) -> pd.DataFrame:
    """Read-modify-write output/D2_feed_status.csv: rows of other owner modules (e.g. feeds_market of the VaR layer)
    are kept untouched; this module's rows are replaced."""
    p = config.OUTPUT / "D2_feed_status.csv"
    out = st
    if p.exists():
        try:
            old = pd.read_csv(p, dtype=str)
            if "owner_module" in old.columns:
                old = old[~old["owner_module"].isin(OWNERS) & ~old["feed"].isin(st["feed"])]
                if len(old):
                    out = pd.concat([st.astype(object), old.astype(object)], ignore_index=True)
        except Exception:                            # noqa: BLE001
            pass
    cols = D2_COLS + [c for c in out.columns if c not in D2_COLS]
    out = out[cols]
    out.to_csv(p, index=False, float_format="%.6g", lineterminator="\n")
    return out


OFFLINE_STATUS = ("keş: şəbəkə yoxdur", "keş: şəbəkəsiz rejim")


def row_level(status: str, fresh: str, core: bool) -> str:
    """ok / xəbərdarlıq / xəta for one feed: a CORE feed that failed or exceeded its max age → xəta; any other
    failure, a non-core feed beyond its max age, or 'köhnəlir' → xəbərdarlıq. An offline run is not a failure."""
    failed = bool(status) and status != "ok" and not str(status).startswith(OFFLINE_STATUS)
    stale = fresh in ("köhnə", "məlumat yoxdur")
    if core and (failed or stale):
        return "xəta"
    return "xəbərdarlıq" if (failed or stale or fresh == "köhnəlir") else "ok"


def feed_status_table() -> pd.DataFrame:
    """D2: every feed (global + AZ) — last value of its headline series, its date, freshness rule and level."""
    man = feeds.read_manifest()
    today = pd.Timestamp(config.as_of())
    spec = {**{k: (v[1], v[2], v[3], v[4]) for k, v in AZ_FEEDS.items()}, **GLOBAL_FEEDS}
    out = []
    for feed, (lab, freq, series, unit) in spec.items():
        m = man[man["feed"] == feed]
        last_try = m.iloc[-1] if len(m) else None
        ok = m[m["status"] == "ok"]
        val, d, n = _headline(feed, series)
        last_ok = ok.iloc[-1]["retrieved_utc"] if len(ok) else ""
        age = (today - pd.Timestamp(d)).days if d else np.nan
        if freq == "hadisə" and len(ok):
            age = (today - pd.Timestamp(last_ok[:10])).days
        fr = freshness(feed, freq, d, last_ok, today)
        st = last_try["status"] if last_try is not None else "heç vaxt yüklənməyib"
        lvl = row_level(st, fr["tazelik"], fr["nuve"])
        any_last = str(ok.iloc[-1]["last_obs"])[:10] if len(ok) else ""     # newest date across all series of the feed
        note = "" if st == "ok" else ("şəbəkəsiz rejim — keş" if str(st).startswith(OFFLINE_STATUS)
                                      else "son yükləmə uğursuz — son uğurlu vintaj istifadə olunur")
        if any_last and d and any_last > d:
            note = (note + "; " if note else "") + (f"əsas sıra {d} tarixindən qüvvədədir; axının son hadisəsi/"
                                                    f"təsdiqi {any_last}")
        out.append({"feed": feed, "owner_module": "feeds_az" if feed in AZ_FEEDS or feed == "azeri_light" else "feeds",
                    "source": lab, "tezlik": freq, "esas_sira": series, "vahid": unit, "son_deyer": val,
                    "last_obs": d, "yas_gun": age, "tazelik": fr["tazelik"], "status": st,
                    "retrieved_utc": last_ok, "n_obs": n,
                    "url": (ok.iloc[-1]["url"] if len(ok) else (last_try["url"] if last_try is not None else "")),
                    "path": ok.iloc[-1]["path"] if len(ok) else "", "note": note,
                    "seviyye": lvl, "nuve": fr["nuve"], "son_hadise": any_last, "dovr_sonu": fr["dovr_sonu"],
                    "yas_dovr_sonundan_gun": fr["yas_dovr_sonundan_gun"], "novbeti_gozlenilen": fr["novbeti_gozlenilen"],
                    "max_yas_gun": fr["max_yas_gun"], "tazelik_qaydasi": fr["tazelik_qaydasi"],
                    "son_cehd_utc": last_try["retrieved_utc"] if last_try is not None else ""})
    return pd.DataFrame(out, columns=D2_COLS + D2_EXTRA)


def stage_level(feeds_list, attempted: pd.DataFrame | None = None, table: pd.DataFrame | None = None) -> str:
    """Stage status string for run_all.Runner: 'ok' | 'xəbərdarlıq: …' | 'xəta: …'. Failures count only for the
    attempts of this run (`attempted` manifest rows); freshness counts always."""
    T = table if table is not None else feed_status_table()
    T = T[T["feed"].isin(list(feeds_list))]
    errs, warns = [], []
    for r in T.itertuples():
        st = r.status
        if attempted is not None and len(attempted):
            a = attempted[attempted["feed"] == r.feed]
            st = a["status"].iloc[-1] if len(a) else "ok"
        else:
            st = "ok"
        lvl = row_level(st, r.tazelik, bool(r.nuve))
        msg = f"{r.feed} ({st if st != 'ok' else r.tazelik})"
        (errs if lvl == "xəta" else warns if lvl == "xəbərdarlıq" else []).append(msg)
    if errs:
        return "xəta: " + "; ".join(errs + warns)[:280]
    if warns:
        return "xəbərdarlıq: " + "; ".join(warns)[:280]
    return "ok"


PANEL = {  # feed: (series filter or None = all, frequency, start)
    "cbar_fx": ([f"cbar_{c.lower()}" for c in HEADLINE_FX] + ["cbar_jpy", "cbar_chf", "cbar_kzt", "cbar_gel", "cbar_uah"],
                "D", "2015-01-01"),
    "cbar_rate": (None, "E", "2010-01-01"), "brent": (None, "D", "2015-01-01"), "azeri_light": (None, "D", "2015-01-01"),
    "vix": (None, "D", "2015-01-01"), "ust10": (None, "D", "2015-01-01"), "eurusd": (None, "D", "2015-01-01"),
    "fedfunds": (None, "M", "2010-01-01"), "gpr": (["gpr_global", "gpr_rus", "gpr_tur", "gpr_isr"], "M", "2010-01-01"),
    "epu": (None, "M", "2010-01-01"), "dsk_macro": (None, "M", "2015-01-01"), "dsk_cpi": (None, "M", "2015-01-01"),
    "dsk_tables": (None, "Q", "2005-01-01"), "sofaz": (None, "Q", "2015-01-01"), "bfb": (None, "E", "2015-01-01"),
    "minfin": (None, "A", "2015-01-01")}


def market_panel() -> pd.DataFrame:
    frames = []
    for feed, (ser, freq, start) in PANEL.items():
        try:
            d = feeds.latest(feed)
        except FileNotFoundError:
            continue
        if ser is not None:
            d = d[d["series"].isin(ser)]
        d = d[d["date"].astype(str) >= start]
        if feed == "dsk_tables":
            d = d.assign(freq=np.where(d["series"].str.startswith("dsk_a_"), "A", "Q"))
        else:
            d = d.assign(freq=freq)
        keep = [c for c in ("date", "freq", "series", "value", "unit", "name", "maturity_days", "isin") if c in d.columns]
        frames.append(d[keep].assign(feed=feed))
    P = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return P.sort_values(["series", "date"]).reset_index(drop=True) if len(P) else P


def run(ctx: dict | None = None, verbose: bool = True) -> dict:
    """Fetch (unless ctx['fetch'] is False), then write D2_feed_status.csv and D4_market_panel.csv."""
    from . import spine
    ctx = ctx or {}
    attempted = None
    if ctx.get("fetch", True):
        attempted = fetch_all_az(fx_budget=ctx.get("fx_budget", 40), bfb_pages=ctx.get("bfb_pages", 2), verbose=verbose)
    st = feed_status_table()
    allst = write_feed_status(st)
    P = market_panel()
    P.to_csv(config.OUTPUT / "D4_market_panel.csv", index=False, float_format="%.8g")
    spine.register_output("D2_feed_status.csv", "feeds_az", "Bütün avtomatik məlumat axınları (AMB, DSK, Maliyyə Nazirliyi, ARDNF, "
                          "BFB, FRED, GPR, EPU, USGS, ERA5): son dəyər, tarix, təzəlik, son yükləmə statusu",
                          list(allst.columns), "gündəlik")
    spine.register_output("D4_market_panel.csv", "feeds_az", "Bazar və statistika paneli (gündəlik/aylıq/rüblük, uzun forma): "
                          "məzənnələr, uçot dərəcəsi, Brent/Azeri Light, DSK göstəriciləri, ARDNF, istiqraz gəlirlilikləri",
                          list(P.columns), "gündəlik")
    level = stage_level(list(AZ_FEEDS) + ["azeri_light"], attempted, st)
    return {"feed_status": st, "panel": P, "attempted": attempted, "stage_status": level}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Azərbaycan avtomatik məlumat axınları → D2, D4")
    ap.add_argument("--no-fetch", action="store_true", help="yalnız keşdən D2/D4 qur")
    ap.add_argument("--backfill", type=int, default=40, help="AMB məzənnə arxivi üçün bu dövrdə ən çox sorğu sayı")
    ap.add_argument("--bfb-pages", type=int, default=2)
    a = ap.parse_args()
    r = run({"fetch": not a.no_fetch, "fx_budget": a.backfill, "bfb_pages": a.bfb_pages})
    print(r["feed_status"][["feed", "son_deyer", "last_obs", "tazelik", "status"]].to_string(index=False))

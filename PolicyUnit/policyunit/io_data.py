"""DSK supply-use / input-output data layer for the PolicyUnit IO engine (MİİS §15.5.4 FR2).

Sources (State Statistical Committee, stat.gov.az; cached under PU/data/io/raw):
  * {Y}_1en.xls supply, {Y}_2en.xls use, {Y}_3en.xls symmetric product x product IOT
    (Y = 2011, 2016, 2021; thousand AZN, basic prices, 81 CPA rows incl. 41-43, 45-47 merged)
  * 027en.xls GDP by expenditure (final-demand margins), 014en/015en (output, VA by activity)
  * labour 002_1-2en.xls (employed population by NACE section, LFS-based, thousand persons)
  * price_tarif 001_5en.xlsx (CPI by item, Dec/Dec) for the E7 fuel-price validation
The IOT is a TOTAL-FLOW table (domestic + imported). Imports are a single column by product;
the domestic/imported split uses the import-proportionality assumption (see ``domestic_split``).
"""
from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

PU = Path(__file__).resolve().parents[1]
MP = PU.parent
DATA = PU / "data" / "io"
RAW = DATA / "raw"
CONFIG = PU / "config"
BASE_URL = "https://www.stat.gov.az/source/"
YEARS = (2011, 2016, 2021)

# local file name -> path under BASE_URL
SOURCES = {f"{y}_{k}en.xls": f"system_nat_accounts/en/{y}_{k}en.xls"
           for y in YEARS for k in (1, 2, 3)}
SOURCES.update({
    "027en.xls": "system_nat_accounts/en/027en.xls",
    "014en.xls": "system_nat_accounts/en/014en.xls",
    "015en.xls": "system_nat_accounts/en/015en.xls",
    "002_1-2en.xls": "labour/en/002_1-2en.xls",
    "001_5en.xlsx": "price_tarif/en/001_5en.xlsx",
    "002_2en.xlsx": "price_tarif/en/002_2en.xlsx",
})
FD_KEYS = ["hh", "gov", "npish", "gfcf", "dinv", "valu", "exp"]
FD_AZ = {"hh": "Ev təsərrüfatlarının son istehlakı", "gov": "Dövlətin son istehlakı",
         "npish": "ETXQKT son istehlakı", "gfcf": "Əsas kapitalın ümumi yığımı",
         "dinv": "Ehtiyatların dəyişməsi", "valu": "Qiymətlilərin xalis əldə edilməsi",
         "exp": "İxrac"}
VA_KEYS = ["ce", "sc", "ni", "tp", "cfc"]  # compensation, social contrib., net income, taxes, CFC


def no_network() -> bool:
    return os.environ.get("POLICY_NO_NETWORK", "") not in ("", "0")


def md5(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


_last_req = [0.0]


def fetch(name: str, force: bool = False) -> Path:
    """Return the cached raw file; download from stat.gov.az if missing (or force=True).
    Honours POLICY_NO_NETWORK=1 (then only the cache is used). Timeout 20 s, <=1 req/s."""
    p = RAW / name
    if p.exists() and not force:
        return p
    if no_network():
        if p.exists():
            return p
        raise FileNotFoundError(f"{name}: keşdə yoxdur və POLICY_NO_NETWORK=1 (şəbəkə bağlıdır)")
    url = BASE_URL + SOURCES[name]
    wait = 1.0 - (time.time() - _last_req[0])
    if wait > 0:
        time.sleep(wait)
    _last_req[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "MIIS-PolicyUnit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        blob = r.read()
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".part")
    tmp.write_bytes(blob)
    tmp.replace(p)
    return p


def write_manifest() -> pd.DataFrame:
    rows = []
    for name, rel in sorted(SOURCES.items()):
        p = RAW / name
        if p.exists():
            rows.append({"file": name, "url": BASE_URL + rel, "bytes": p.stat().st_size,
                         "md5": md5(p)})
    df = pd.DataFrame(rows)
    df.to_csv(DATA / "MANIFEST_md5.csv", index=False)
    return df


def read_sheet(path, sheet=0) -> pd.DataFrame:
    """Read an .xls/.xlsx regardless of its extension (2021 DSK files are xlsx named .xls)."""
    path = Path(path)
    with open(path, "rb") as f:
        magic = f.read(4)
    engine = "openpyxl" if magic[:2] == b"PK" else "xlrd"
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.read_excel(path, sheet_name=sheet, header=None, engine=engine)


def _txt(v) -> str:
    return "" if (v is None or (isinstance(v, float) and np.isnan(v))) else str(v).strip()


def _num(v) -> float:
    if isinstance(v, str):
        v = v.replace(",", ".").replace(" ", "")
        try:
            return float(v)
        except ValueError:
            return 0.0
    try:
        f = float(v)
        return 0.0 if np.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


def cpa2(code) -> str:
    """'01.000' -> '01'; '41.000  43.000' or '41-43' -> '41-43'; 2011 ints -> zero-padded."""
    nums = re.findall(r"\d+", _txt(code).replace(".000", ""))
    nums = [n for n in nums if n != "0"]
    if not nums:
        return ""
    if len(nums) >= 2:
        return f"{int(nums[0]):02d}-{int(nums[1]):02d}"
    return f"{int(nums[0]):02d}"


# ----------------------------------------------------------------------------- IOT parsing
@dataclass
class IOT:
    """Symmetric IO table (total flows, basic prices, thousand AZN)."""
    year: int
    codes: list                     # product / sector codes (n)
    names: list
    Z: np.ndarray                   # n x n intermediate flows (row i used by column j)
    fd: pd.DataFrame                # n x FD_KEYS final demand (total = domestic + imported)
    imp: np.ndarray                 # n imports (positive, incl. CIF/FOB adjustment if any)
    tax: np.ndarray                 # n net taxes on products paid by using column j
    cif: np.ndarray                 # n CIF/FOB row by column
    va: pd.DataFrame                # VA_KEYS x n
    x: np.ndarray                   # n gross output at basic prices (domestic product)
    fd_tax: dict = field(default_factory=dict)   # net product taxes on each FD column
    meta: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.codes)

    def check(self) -> dict:
        """Accounting identities: row balance (x = Z1 + f - m) and column balance
        (x = 1'Z + tax + cif + VA). Returns max abs relative residuals."""
        f = self.fd[FD_KEYS].sum(axis=1).to_numpy()
        row = self.Z.sum(1) + f - self.imp
        col = self.Z.sum(0) + self.tax + self.cif + self.va.loc[VA_KEYS].sum(0).to_numpy()
        sc = np.maximum(np.abs(self.x), 1.0)
        return {"row_resid_max": float(np.max(np.abs(row - self.x) / sc)),
                "col_resid_max": float(np.max(np.abs(col - self.x) / sc)),
                "x_total": float(self.x.sum())}


def _find_col(hdr, *keys, start=0):
    for j in range(start, len(hdr)):
        h = hdr[j].lower()
        if all(k in h for k in keys):
            return j
    return None


def load_iot(year: int) -> IOT:
    """Parse DSK '{year}_3en.xls' (product x product IOT, basic prices)."""
    x = read_sheet(fetch(f"{year}_3en.xls"))
    hdr_row = next(i for i in range(10) if any("household" in _txt(v).lower() for v in x.iloc[i]))
    hdr = [_txt(v) for v in x.iloc[hdr_row]]
    c0 = 3
    j_ic = _find_col(hdr, "intermediate", start=c0)
    n = j_ic - c0
    r0 = hdr_row + 2
    rows = list(range(r0, r0 + n))
    codes = [cpa2(x.iat[i, 2]) for i in rows]
    names = [_txt(x.iat[i, 1]) for i in rows]
    Z = np.array([[_num(x.iat[i, j]) for j in range(c0, c0 + n)] for i in rows])
    col = {"hh": _find_col(hdr, "household", start=j_ic),
           "gov": _find_col(hdr, "government", start=j_ic),
           "npish": _find_col(hdr, "profit", start=j_ic),
           "gfcf": _find_col(hdr, "fixed capital", start=j_ic),
           "dinv": _find_col(hdr, "inventor", start=j_ic),
           "valu": _find_col(hdr, "valuables", start=j_ic),
           "exp": _find_col(hdr, "export", start=j_ic)}
    j_imp = _find_col(hdr, "import", start=j_ic)
    j_cif = _find_col(hdr, "cif", start=j_ic)
    fd = pd.DataFrame(index=codes)
    for k in FD_KEYS:
        j = col[k]
        fd[k] = [(_num(x.iat[i, j]) if j is not None else 0.0) for i in rows]
    imp = -np.array([_num(x.iat[i, j_imp]) for i in rows])
    if j_cif is not None:   # CIF/FOB column (zero by product in 2016/2021)
        imp = imp - np.array([_num(x.iat[i, j_cif]) for i in rows])
    lab = {i: _txt(x.iat[i, 1]).lower() for i in range(r0 + n, x.shape[0])}

    def rowv(*keys, cols=None):
        for i, t in lab.items():
            if all(k in t for k in keys):
                cc = cols if cols is not None else range(c0, c0 + n)
                return i, np.array([_num(x.iat[i, j]) for j in cc])
        return None, None
    i_tax, tax = rowv("net taxes")
    _, cif = rowv("cif")
    va = pd.DataFrame({"ce": rowv("compensation")[1], "sc": rowv("social contr")[1],
                       "ni": rowv("net ")[1] if rowv("net income")[1] is None else rowv("net income")[1],
                       "tp": rowv("taxes on production")[1],
                       "cfc": rowv("fixed capital")[1]}, index=codes).T
    if rowv("net income")[1] is None:
        va.loc["ni"] = rowv("net profit")[1]
    _, xo = rowv("output")
    fd_tax = {}
    if i_tax is not None:
        for k in FD_KEYS:
            fd_tax[k] = _num(x.iat[i_tax, col[k]]) if col[k] is not None else 0.0
    t = IOT(year, codes, names, Z, fd, imp, tax, cif if cif is not None else np.zeros(n),
            va, xo, fd_tax, {"source": f"DSK {year}_3en.xls", "md5": md5(RAW / f"{year}_3en.xls")})
    return t


def load_supply(year: int) -> pd.DataFrame:
    """Supply table by product: output, imports, margins, net product taxes, purchasers' total.
    Also returns industry (NACE section) output by product in columns A..S."""
    x = read_sheet(fetch(f"{year}_1en.xls"))
    hdr_row = next(i for i in range(10) if any("output" == _txt(v).lower() for v in x.iloc[i]))
    hdr = [_txt(v) for v in x.iloc[hdr_row]]
    j_out = hdr.index(next(h for h in hdr if h.lower() == "output"))
    secs = [_txt(v) for v in x.iloc[hdr_row + 1, 3:j_out]]
    r0 = hdr_row + 2
    rows = [i for i in range(r0, x.shape[0]) if cpa2(x.iat[i, 2])]
    out = pd.DataFrame(index=[cpa2(x.iat[i, 2]) for i in rows])
    for k, s in enumerate(secs):
        out[s or f"ind{k}"] = [_num(x.iat[i, 3 + k]) for i in rows]
    names = {"output": ("output",), "imports": ("import",), "cif": ("cif",),
             "total_bp": ("total", "basic"), "margins": ("margin",),
             "net_taxes": ("net taxes",), "total_pp": ("total", "co")}
    for key, kk in names.items():
        j = _find_col([h.lower() for h in hdr], *kk, start=j_out)
        if key == "total_pp":
            j = len(hdr) - 1
        out[key] = [_num(x.iat[i, j]) for i in rows] if j is not None else 0.0
    return out


# ----------------------------------------------------------------------------- classification
def sectors() -> pd.DataFrame:
    """Aggregated IO classification (config/io_sectors.csv; 23 sectors, NACE-aligned)."""
    return pd.read_csv(CONFIG / "io_sectors.csv", dtype=str).fillna("")


def product_map(codes) -> list:
    """CPA-2 product code -> IO sector code (via cpa_products lists, ranges like 41-43)."""
    s = sectors()
    lut = {}
    for _, r in s.iterrows():
        for c in r["cpa_products"].split(";"):
            lut[c.strip()] = r["code"]
    out = []
    for c in codes:
        key = c if c in lut else c.split("-")[0]
        if key not in lut:
            key = next((k for k in lut if k.split("-")[0] == key), None)
        if key is None:
            raise KeyError(f"CPA {c}: io_sectors.csv-də sektor xəritəsi yoxdur")
        out.append(lut[key])
    return out


def aggregate(t: IOT, mapping=None) -> IOT:
    """Aggregate a product IOT to the sector classification (S x P summation matrix)."""
    mapping = mapping or product_map(t.codes)
    order = [c for c in sectors()["code"] if c in set(mapping)]
    S = np.zeros((len(order), t.n))
    for j, m in enumerate(mapping):
        S[order.index(m), j] = 1.0
    fd = pd.DataFrame(S @ t.fd[FD_KEYS].to_numpy(), index=order, columns=FD_KEYS)
    va = pd.DataFrame(t.va.loc[VA_KEYS].to_numpy() @ S.T, index=VA_KEYS, columns=order)
    nm = dict(zip(sectors()["code"], sectors()["name_az"]))
    return IOT(t.year, order, [nm[c] for c in order], S @ t.Z @ S.T, fd, S @ t.imp,
               S @ t.tax, S @ t.cif, va, S @ t.x, dict(t.fd_tax),
               dict(t.meta, aggregated=True, n_products=t.n))


def domestic_split(t: IOT) -> dict:
    """Import-proportionality assumption: for each product i, the import share of every
    DOMESTIC use (intermediate and final, exports excluded) is the same:
        s_i = m_i / (Z_i. + f_i - e_i)   (clipped to [0, 1]);
    exports are assumed to be domestically produced (re-exports ignored).
    Returns domestic (Zd, fdd) and imported (Zm, fdm) parts and the share vector."""
    f = t.fd[FD_KEYS].to_numpy()
    e = t.fd["exp"].to_numpy()
    dom_use = t.Z.sum(1) + f.sum(1) - e
    s = np.where(dom_use > 0, t.imp / np.where(dom_use > 0, dom_use, 1.0), 0.0)
    s = np.clip(s, 0.0, 1.0)
    Zm = t.Z * s[:, None]
    fm = f * s[:, None]
    ie = FD_KEYS.index("exp")
    fm[:, ie] = 0.0
    fdm = pd.DataFrame(fm, index=t.codes, columns=FD_KEYS)
    fdd = t.fd[FD_KEYS] - fdm
    return {"s": s, "Zd": t.Z - Zm, "Zm": Zm, "fdd": fdd, "fdm": fdm,
            "imp_resid": float(t.imp.sum() - Zm.sum() - fm.sum())}


# ----------------------------------------------------------------------------- satellites
FR4_SECTION = {"agr": "A", "mining": "B", "manuf": "C", "elec": "D", "water": "E",
               "constr": "F", "trade": "G", "transp": "H", "hotel": "I", "ict": "J",
               "fin": "K", "realest": "L", "prof": "M", "admsup": "N", "pubadm": "O",
               "educ": "P", "health": "Q", "art": "R", "othsvc": "S"}
DSK_SECTION_ORDER = list("ABCDEFGHIJKLMNOPQRS")


def employment_sections() -> pd.DataFrame:
    """Employed population by NACE section, thousand persons, year x section (DSK 002_1-2,
    sheet Dynamics_2.1, LFS-based annual average)."""
    x = read_sheet(fetch("002_1-2en.xls"), sheet="Dynamics_2.1")
    hdr = None
    for i in range(x.shape[0]):
        vals = [_num(v) for v in x.iloc[i, 3:]]
        if 2021.0 in vals and 1999.0 in vals:
            hdr = i
            break
    years = [int(_num(v)) for v in x.iloc[hdr, 3:] if _num(v) > 1900]
    rows = []
    for k in range(19):
        i = hdr + 2 + k
        rows.append([_num(v) for v in x.iloc[i, 3:3 + len(years)]])
    return pd.DataFrame(np.array(rows).T, index=years, columns=DSK_SECTION_ORDER)


def fr10_employees(year: int) -> pd.Series:
    """Industrial employees by NACE division from MicroUnit FR10 (read-only)."""
    p = MP / "MicroUnit" / "output" / "FR10_branch_history.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_csv(p, dtype={"unit": str})
    d = d[(d["series"] == "employees") & (d["year"] == year)]
    return d.set_index("unit")["value"].astype(float)


def employment(year: int) -> pd.Series:
    """Employment (thousand persons) by IO sector. Sections B and C are split into IO
    sectors with FR10 industrial-employee shares by NACE division (fallback: output shares)."""
    es = employment_sections()
    yr = year if year in es.index else max(y for y in es.index if y <= year)
    sec = sectors()
    emp = {}
    br = fr10_employees(yr)
    for sect in DSK_SECTION_ORDER:
        members = sec[sec["nace_section"].str.split(";").apply(lambda l: sect in l)]
        tot = es.loc[yr, sect]
        if len(members) == 1:
            emp[members["code"].iloc[0]] = emp.get(members["code"].iloc[0], 0.0) + tot
            continue
        w = {}
        for _, r in members.iterrows():
            w[r["code"]] = sum(br.get(d, 0.0) for d in r["nace_list"].split(";"))
        s = sum(w.values())
        for c, v in w.items():
            emp[c] = emp.get(c, 0.0) + (tot * v / s if s > 0 else tot / len(w))
    return pd.Series(emp)[[c for c in sec["code"]]]


def aggregate_supply(sup: pd.DataFrame) -> pd.DataFrame:
    """Sum supply-table product rows to IO sectors (rows without a CPA code dropped)."""
    sup = sup.loc[[i for i in sup.index if re.match(r"^\d\d", str(i))]]
    return sup.groupby(product_map(list(sup.index))).sum()


def na_final_demand() -> pd.DataFrame:
    """GDP by expenditure (DSK 027en, mln AZN) -> year x {hh, gov, npish, gfcf, dinv, exp, imp,
    gdp}. Government = individual + collective final consumption of government."""
    x = read_sheet(fetch("027en.xls"), sheet=0)
    hdr = next(i for i in range(10) if _num(x.iat[i, 3]) > 1900)
    years = []
    for v in x.iloc[hdr, 3:]:
        m = re.match(r"(\d{4})", _txt(v))
        years.append(int(m.group(1)) if m else None)
    lab = [(_txt(x.iat[i, 1]), _txt(x.iat[i, 2]).lower()) for i in range(x.shape[0])]

    def series(pred):
        for i, (code, t) in enumerate(lab):
            if pred(code, t):
                return [_num(v) for v in x.iloc[i, 3:]]
        return [np.nan] * len(years)
    rows = {
        "hh": series(lambda c, t: c == "P.3" and "household" in t),
        "gov_ind": series(lambda c, t: c == "P.3" and "government" in t),
        "npish": series(lambda c, t: c == "P.3" and "profit" in t),
        "gov_coll": series(lambda c, t: c == "P.4" and "collective" in t),
        "gfcf": series(lambda c, t: c == "P.51"),
        "dinv": series(lambda c, t: c == "P.52"),
        "exp": series(lambda c, t: c == "P.6"),
        "imp": series(lambda c, t: c == "P.7"),
        "gdp": series(lambda c, t: "gdp" == t.strip()),
    }
    df = pd.DataFrame(rows, index=years)
    df = df[[y is not None for y in df.index]]
    df["gov"] = df["gov_ind"] + df["gov_coll"].fillna(0.0)
    return df


def refresh(names=None) -> list:
    """Re-download the DSK raw files (skipped with POLICY_NO_NETWORK=1); returns statuses."""
    out = []
    for name in names or sorted(SOURCES):
        if no_network():
            out.append((name, "keş (şəbəkə bağlı)"))
            continue
        try:
            fetch(name, force=True)
            out.append((name, "yeniləndi"))
        except Exception as e:  # keep the cached copy
            out.append((name, f"xəta: {e}; keş saxlanıldı"))
    write_manifest()
    return out


if __name__ == "__main__":
    import sys
    if "--refresh" in sys.argv:
        for n, st in refresh():
            print(n, st)
    else:
        print(write_manifest().to_string(index=False))

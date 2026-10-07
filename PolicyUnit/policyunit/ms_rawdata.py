"""Parse cached DSK household-budget and labour tables into tidy calibration targets
(microsimulation, FR3). Raw files: data/raw/dsk_hbs, data/raw/dsk_labour (downloaded
2026-10-06 from stat.gov.az). Output: data/households/targets/*.csv (committed snapshot so
that the engine and the tests run offline)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_HBS = ROOT / "data" / "raw" / "dsk_hbs"
RAW_LAB = ROOT / "data" / "raw" / "dsk_labour"
TARGETS = ROOT / "data" / "households" / "targets"

SECTORS = ["agr", "mining", "manuf", "elec", "water", "constr", "trade", "transp", "hotel",
           "ict", "fin", "realest", "prof", "admsup", "pubadm", "educ", "health", "art",
           "othsvc"]                                    # NACE A..S = MicroUnit FR4 keys
INC_KEYS = ["total", "employment", "selfemp", "agri", "property", "rent", "transfers",
            "pensions", "benefits", "inkind", "other", "interhh", "remit"]
CONS_KEYS = ["total", "food", "alc", "tobacco", "clothing", "housing", "furnish", "health",
             "transport", "comm", "recreation", "education", "restaurants", "misc"]


def _num(v):
    try:
        f = float(v)
        return f if np.isfinite(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


def _block(df, first_label, keys, col0=2):
    """Return the numeric block starting at the row whose col 1 matches first_label."""
    lab = df[1].astype(str).str.strip().str.lower()
    i0 = int(np.where(lab.str.startswith(first_label.lower()))[0][0])
    rows = [r for r in range(i0, len(df)) if isinstance(df.iat[r, 1], str)
            and df.iat[r, 1].strip().lower().rstrip(":") not in ("including", "of which")]
    rows = rows[:len(keys)]
    return {k: [_num(x) for x in df.iloc[r, col0:].tolist()] for k, r in zip(keys, rows)}


def series_table(fname, first_label, keys, out):
    df = pd.read_excel(RAW_HBS / fname, header=None)
    yrow = [r for r in range(len(df)) if _num(df.iat[r, 2]) == 2001][0]
    years = [int(_num(x)) for x in df.iloc[yrow, 2:].tolist() if np.isfinite(_num(x))]
    blk = _block(df.iloc[yrow + 1:].reset_index(drop=True), first_label, keys)
    rec = [{"year": y, "key": k, "value": v[j]} for k, v in blk.items()
           for j, y in enumerate(years)]
    pd.DataFrame(rec).to_csv(TARGETS / out, index=False)


def decile_table(fname, first_label, keys, out):
    df = pd.read_excel(RAW_HBS / fname, header=None)
    half = df.iloc[: len(df) // 2 + 1].reset_index(drop=True)
    blk = _block(half, first_label, keys)
    rec = [{"decile": d + 1, "key": k, "value": v[d]} for k, v in blk.items()
           for d in range(10)]
    pd.DataFrame(rec).to_csv(TARGETS / out, index=False)


def poverty_table():
    df = pd.read_excel(RAW_HBS / "5.4en.xls", header=None)
    years = [int(_num(x)) for x in df.iloc[2, 3:].tolist()]
    names = {3: "line", 4: "rate", 6: "men", 7: "women", 9: "urban", 10: "rural"}
    rec = {"year": years}
    for r, n in names.items():
        rec[n] = [_num(x) for x in df.iloc[r, 3:].tolist()]
    pd.DataFrame(rec).to_csv(TARGETS / "poverty_line_rate.csv", index=False)


def _bands(labels):
    out = []
    for s in labels:
        s = str(s)
        m = re.findall(r"\d+[\.,]?\d*", s.replace(",0", ""))
        if "less" in s:
            out.append((0.0, float(m[0])))
        elif "over" in s:
            out.append((float(m[0]), np.inf))
        else:
            out.append((float(m[0]), float(m[1])))
    return out


def wage_bands():
    x = pd.read_excel(RAW_LAB / "004_11-12en.xls", sheet_name=None, header=None)
    rec = []
    for sheet, year in (("4.11", 2024), ("4.12", 2025)):
        df = x[sheet].dropna(how="all").dropna(how="all", axis=1).reset_index(drop=True)
        hdr = df.iloc[3].tolist()
        cols = [j for j, h in enumerate(hdr) if isinstance(h, str) and
                ("-" in h or "less" in h or "over" in h)]
        cols = cols[: [k for k, j in enumerate(cols) if "less" in hdr[j]][1:][:1][0]] \
            if sum("less" in hdr[j] for j in cols) > 1 else cols
        bands = _bands([hdr[j] for j in cols])
        tot = [r for r in range(len(df)) if str(df.iat[r, 0]).strip() == "Total"][0]
        for i, sec in enumerate(SECTORS):
            r = tot + 1 + i
            for (lo, hi), j in zip(bands, cols):
                rec.append({"year": year, "sector": sec, "lo": lo, "hi": hi,
                            "count": np.nan_to_num(_num(df.iat[r, j]))})
    pd.DataFrame(rec).to_csv(TARGETS / "wage_bands.csv", index=False)


def wage_avg():
    df = pd.read_excel(RAW_LAB / "004_2-3en.xls", sheet_name="4.2", header=None)
    yrow = [r for r in range(len(df)) if str(df.iat[r, 2]).startswith("Economic")][0]
    years = [int(_num(x)) for x in df.iloc[yrow, 3:].tolist()]
    rec = []
    for i, sec in enumerate(["total"] + SECTORS):
        for j, y in enumerate(years):
            rec.append({"year": y, "sector": sec, "value": _num(df.iat[yrow + 1 + i, 3 + j])})
    pd.DataFrame(rec).to_csv(TARGETS / "wage_avg_sector.csv", index=False)


def income_bands_persons():
    df = pd.read_excel(RAW_HBS / "028en.xls", header=None)
    rec = []
    for r in range(6, len(df)):
        lab = str(df.iat[r, 1])
        m = re.findall(r"\d+\.?\d*", lab)
        if not m:
            continue
        lo, hi = (0.0, float(m[0])) if "up to" in lab else (
            (float(m[0]), np.inf) if "more" in lab else (float(m[0]) - 0.1, float(m[1])))
        rec.append({"lo": lo, "hi": hi, "pct_all": _num(df.iat[r, 2]),
                    "pct_urban": _num(df.iat[r, 3]), "pct_rural": _num(df.iat[r, 4])})
    pd.DataFrame(rec).to_csv(TARGETS / "income_bands_persons_2024.csv", index=False)


def build_all():
    TARGETS.mkdir(parents=True, exist_ok=True)
    series_table("e002en.xls", "Total income", INC_KEYS, "hbs_income_sources.csv")
    series_table("e003en.xls", "Consumption expenditure", CONS_KEYS, "hbs_consumption.csv")
    decile_table("025_26en.xls", "Total income", INC_KEYS, "income_deciles_2024.csv")
    decile_table("053_54en.xls", "Consumption expenditure total", CONS_KEYS,
                 "cons_deciles_2024.csv")
    poverty_table()
    wage_bands()
    wage_avg()
    income_bands_persons()
    return sorted(p.name for p in TARGETS.glob("*.csv"))


if __name__ == "__main__":
    print(build_all())

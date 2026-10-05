"""
validate_tables — FR10 müəssisə paneli (B qatı) və FR12 biznes reyestri (B qatı) validatorları.

Dəftərlərdə validatorlar hücrə daxilində funksiya kimi yazılıb (idxal edilə bilmir), ona görə burada
FR10 `normalise_headers` / `validate` və FR12 `br_normalise` / `br_validate` qaydaları eyni məntiqlə
təkrarlanır; sxem `data/firm_panel/FR10_firm_panel_column_map.csv` və
`data/business_register/FR12_business_register_column_map.csv` fayllarından oxunur. Region siyahıları
dəftərlərin `REG_PAT` lüğətindən götürülür (yoxdursa aşağıdakı siyahılar).
Ciddi (fatal/error) səhv olduqda dəftər icranı dayandırır — API həmin faylı tətbiq etməyə icazə vermir.
"""
import csv, re, unicodedata
from pathlib import Path

import nbextract as X

SYN_STATUS = "SYNTHETIC — not real enterprise data"
FR10_REGIONS = ["Baku city", "Nakhchivan AR", "Absheron-Khizi", "Daghlig Shirvan", "Ganja-Dashkasan", "Garabagh",
                "Gazakh-Tovuz", "Guba-Khachmaz", "Lankaran-Astara", "Central Aran", "Mil-Mughan", "Shaki-Zagatala",
                "Eastern Zangezur", "Shirvan-Salyan"]
FR12_REGIONS = ["Baku city", "Nakhchivan", "Absheron-Khizi", "Daghlig Shirvan", "Ganja-Dashkasan", "Karabakh",
                "Gazakh-Tovuz", "Guba-Khachmaz", "Lankaran-Astara", "Central Aran", "Mil-Mughan", "Shaki-Zagatala",
                "East Zangezur", "Shirvan-Salyan"]
NACE_DIV = {f'{d:02d}' for d in list(range(1, 4)) + list(range(5, 34)) + [35] + list(range(36, 40)) + list(range(41, 44))
            + list(range(45, 48)) + list(range(49, 54)) + [55, 56] + list(range(58, 64)) + [64, 65, 66, 68]
            + list(range(69, 76)) + list(range(77, 83)) + [84, 85, 86, 87, 88] + list(range(90, 94))
            + [94, 95, 96, 97, 98, 99]}
FR12_DIV = {'A': ['01', '02', '03'], 'B': ['05', '06', '07', '08', '09'], 'C': [f'{d}' for d in range(10, 34)], 'D': ['35'],
            'E': ['36', '37', '38', '39'], 'F': ['41', '42', '43'], 'G': ['45', '46', '47'], 'H': ['49', '50', '51', '52', '53'],
            'I': ['55', '56'], 'J': ['58', '59', '60', '61', '62', '63'], 'K': ['64', '65', '66'], 'L': ['68'],
            'M': ['69', '70', '71', '72', '73', '74', '75'], 'N': ['77', '78', '79', '80', '81', '82'], 'O': ['84'], 'P': ['85'],
            'Q': ['86', '87', '88'], 'R': ['90', '91', '92', '93'], 'S': ['94', '95', '96'], 'U': ['99']}
FR12_DIV2SEC = {d: s for s, ds in FR12_DIV.items() for d in ds}
RULE_AZ = {
    "required column missing (EN or AZ header)": "məcburi sütun yoxdur (ingilis və ya Azərbaycan başlığı)",
    "not numeric or missing": "ədəd deyil və ya boşdur", "negative value": "mənfi dəyər",
    "duplicate firm-year": "müəssisə-il təkrarlanır",
    "not a NACE Rev.2 division": "NACE Rev.2 bölməsi deyil",
    "not a NACE Rev.2 division of sections A-S, U": "A–S, U bölmələrinin NACE Rev.2 kodu deyil",
    "not one of the 14 economic regions": "14 iqtisadi rayondan biri deyil",
    "not state / private / foreign / joint": "mülkiyyət növü state / private / foreign / joint deyil",
    "not state / municipal / private / foreign / joint": "mülkiyyət növü state / municipal / private / foreign / joint deyil",
    "not micro / small / medium / large": "ölçü qrupu micro / small / medium / large deyil",
    "not active / liquidated": "status active / liquidated deyil",
    "total assets < current + fixed assets": "aktivlərin cəmi dövriyyə + uzunmüddətli aktivlərdən azdır",
    "current assets > total assets": "dövriyyə aktivləri aktivlərin cəmindən çoxdur",
    "balance sheet does not balance (equity + liabilities != total assets)": "balans bərabərliyi pozulub (kapital + öhdəliklər ≠ aktivlər)",
    "cash + receivables + inventories > current assets": "pul + debitor + ehtiyat dövriyyə aktivlərindən çoxdur",
    "EBIT inconsistent with revenue - costs (5%)": "EBIT gəlir − xərclərlə uyğun deyil (5 %)",
    "exports > revenue": "ixrac gəlirdən çoxdur", "interest-bearing debt > liabilities": "faizli borc öhdəliklərdən çoxdur",
    "absent: distress score not computed": "sütun yoxdur: maliyyə çətinliyi göstəricisi hesablanmayacaq",
    "missing: distress score not computed": "boşdur: maliyyə çətinliyi göstəricisi hesablanmayacaq",
    "missing or not a date": "boşdur və ya tarix deyil", "registered after the reporting year": "hesabat ilindən sonra qeydiyyatdan keçib",
    "liquidation before registration": "ləğvetmə qeydiyyatdan əvvəldir",
    "'liquidated' but liquidation date not in this year": "«liquidated», lakin ləğvetmə tarixi bu ilə düşmür",
    "'active' but liquidated on or before this year": "«active», lakin bu il və ya daha əvvəl ləğv edilib",
    "weight < 1": "çəki 1-dən kiçikdir",
    "absent: price-cost margin and Boone indicator not computed": "sütun yoxdur: qiymət-xərc marjası və Boone göstəricisi hesablanmayacaq",
}


def az_lower(s):
    return unicodedata.normalize("NFC", str(s).lower().replace("̇", ""))


def column_map(root, kind):
    """{field_en: (field_az, required, type)} — notebook-un yazdığı sütun xəritəsindən."""
    if kind == "firm_panel":
        p, en, az = Path(root) / "data/firm_panel/FR10_firm_panel_column_map.csv", "field_en", "field_az"
    else:
        p, en, az = Path(root) / "data/business_register/FR12_business_register_column_map.csv", "column_en", "column_az"
    with open(p, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r[en]: (r[az], str(r.get("required")).strip().lower() == "true", r.get("type", "str")) for r in rows}


def regions(root, kind):
    nb = Path(root) / ("FR10.ipynb" if kind == "firm_panel" else "FR12.ipynb")
    rp = X.assigned(nb, "REG_PAT") if nb.exists() else None
    if isinstance(rp, dict) and len(rp) >= 10:
        return list(rp)
    return FR10_REGIONS if kind == "firm_panel" else FR12_REGIONS


def read_table(path):
    import pandas as pd
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name="data", dtype={"nace2": str, "firm_id": str})
    return pd.read_csv(p, dtype={"nace2": str, "firm_id": str}, encoding="utf-8-sig", keep_default_na=True)


def normalise(df, cmap):
    m = {**{az_lower(v[0]).strip(): k for k, v in cmap.items()}, **{k: k for k in cmap}}
    m.setdefault("data_status", "data_status")
    m.setdefault(az_lower("Məlumatın statusu"), "data_status")
    ren = {c: m.get(az_lower(str(c)).strip(), c) for c in df.columns}
    return df.rename(columns=ren), [c for c, v in ren.items() if v not in cmap and v != "data_status"]


def prepare(df):
    """Dəftərin yükləyicisi kimi: nace2 iki rəqəmə, year ədədə, nümunə sətri çıxarılır."""
    import pandas as pd
    if "nace2" in df:
        df["nace2"] = df["nace2"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    if "year" in df:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    ds = df.get("data_status", pd.Series("", index=df.index)).astype(str)
    return df[~ds.str.startswith("EXAMPLE ROW")].reset_index(drop=True)


class _Issues:
    def __init__(self, df):
        self.df, self.items = df, []

    def add(self, mask, field, rule, sev="error"):
        import numpy as np
        mask = mask.fillna(sev != "warning")
        df = self.df
        for i in df.index[np.asarray(mask, dtype=bool)]:
            self.items.append(dict(row=int(i) + 2, firm_id=df.at[i, "firm_id"] if "firm_id" in df else "",
                                   year=df.at[i, "year"] if "year" in df else "", field=field, rule=rule, severity=sev))


def fr10_validate(df, cmap, regs):
    """FR10.ipynb `validate(df)` ilə eyni qaydalar."""
    import numpy as np, pandas as pd
    req = [f for f, v in cmap.items() if v[1] and f != "data_status"]
    miss = [f for f in req if f not in df.columns]
    if miss:
        return [dict(row=1, firm_id="", year="", field=f, rule="required column missing (EN or AZ header)", severity="fatal") for f in miss]
    I, TOL = _Issues(df), 0.01
    floats = [f for f, v in cmap.items() if v[2] == "float"]
    num = {f: pd.to_numeric(df[f], errors="coerce") for f in floats if f in df}
    for f in [f for f in floats if cmap[f][1]]:
        I.add(pd.Series(~np.isfinite(num[f].to_numpy(dtype=float)), index=df.index), f, "not numeric or missing")
    for f in ["total_assets", "current_assets", "cash", "receivables", "inventories", "fixed_assets", "st_liabilities",
              "lt_liabilities", "revenue", "cost_of_sales", "operating_expenses", "interest", "employees", "wage_bill",
              "interest_bearing_debt", "trade_payables", "depreciation", "capex", "exports"]:
        if f in num:
            I.add(num[f] < 0, f, "negative value")
    I.add(df.duplicated(["firm_id", "year"], keep=False), "firm_id", "duplicate firm-year")
    I.add(~df.nace2.astype(str).str.zfill(2).isin(NACE_DIV), "nace2", "not a NACE Rev.2 division")
    I.add(~df.region.isin(regs), "region", "not one of the 14 economic regions")
    I.add(~df.ownership.isin(["state", "private", "foreign", "joint"]), "ownership", "not state / private / foreign / joint")
    n = num
    I.add(n["current_assets"] + n["fixed_assets"] > n["total_assets"] * (1 + TOL), "total_assets", "total assets < current + fixed assets")
    I.add(n["current_assets"] > n["total_assets"] * (1 + TOL), "current_assets", "current assets > total assets")
    I.add((n["equity"] + n["st_liabilities"] + n["lt_liabilities"] - n["total_assets"]).abs() > TOL * n["total_assets"].abs().clip(lower=1),
          "equity", "balance sheet does not balance (equity + liabilities != total assets)")
    I.add(n["cash"] + n["receivables"] + n["inventories"] > n["current_assets"] * (1 + TOL), "current_assets",
          "cash + receivables + inventories > current assets")
    I.add((n["revenue"] - n["cost_of_sales"] - n["operating_expenses"] - n["ebit"]).abs() > 0.05 * n["revenue"].clip(lower=1),
          "ebit", "EBIT inconsistent with revenue - costs (5%)", "warning")
    if "exports" in n:
        I.add(n["exports"] > n["revenue"] * (1 + TOL), "exports", "exports > revenue")
    if "interest_bearing_debt" in n:
        I.add(n["interest_bearing_debt"] > (n["st_liabilities"] + n["lt_liabilities"]) * (1 + TOL), "interest_bearing_debt",
              "interest-bearing debt > liabilities")
    if "retained_earnings" not in df:
        I.add(pd.Series(True, index=df.index), "retained_earnings", "absent: distress score not computed", "warning")
    else:
        I.add(n["retained_earnings"].isna(), "retained_earnings", "missing: distress score not computed", "warning")
    return I.items


def fr12_validate(df, cmap, regs):
    """FR12.ipynb `br_validate(df)` ilə eyni qaydalar."""
    import numpy as np, pandas as pd
    req = [f for f, v in cmap.items() if v[1] and f != "data_status"]
    miss = [f for f in req if f not in df.columns]
    if miss:
        return [dict(row=1, firm_id="", year="", field=f, rule="required column missing (EN or AZ header)", severity="fatal") for f in miss]
    I = _Issues(df)
    rev = pd.to_numeric(df.revenue, errors="coerce")
    emp = pd.to_numeric(df.employees, errors="coerce")
    I.add(pd.Series(~np.isfinite(rev.to_numpy(dtype=float)), index=df.index), "revenue", "not numeric or missing")
    I.add(rev < 0, "revenue", "negative value")
    I.add(pd.Series(~np.isfinite(emp.to_numpy(dtype=float)), index=df.index), "employees", "not numeric or missing")
    I.add(emp < 0, "employees", "negative value")
    I.add(df.duplicated(["firm_id", "year"], keep=False), "firm_id", "duplicate firm-year")
    I.add(~df.nace2.astype(str).isin(FR12_DIV2SEC), "nace2", "not a NACE Rev.2 division of sections A-S, U")
    I.add(~df.region.isin(regs), "region", "not one of the 14 economic regions")
    I.add(~df.ownership.isin(["state", "municipal", "private", "foreign", "joint"]), "ownership",
          "not state / municipal / private / foreign / joint")
    I.add(~df.size_class.isin(["micro", "small", "medium", "large"]), "size_class", "not micro / small / medium / large")
    I.add(~df.status.isin(["active", "liquidated"]), "status", "not active / liquidated")
    rd = pd.to_datetime(df.registration_date, errors="coerce")
    ld = pd.to_datetime(df.get("liquidation_date"), errors="coerce")
    if not isinstance(ld, pd.Series):
        ld = pd.Series(pd.NaT, index=df.index)
    yr = pd.to_numeric(df.year, errors="coerce")
    I.add(rd.isna(), "registration_date", "missing or not a date")
    I.add(rd.dt.year > yr, "registration_date", "registered after the reporting year")
    I.add((ld < rd) & ld.notna(), "liquidation_date", "liquidation before registration")
    I.add((df.status == "liquidated") & (ld.dt.year != yr), "status", "'liquidated' but liquidation date not in this year")
    I.add((df.status == "active") & ld.notna() & (ld.dt.year <= yr), "status", "'active' but liquidated on or before this year", "warning")
    if "weight" in df:
        I.add(pd.to_numeric(df.weight, errors="coerce").fillna(1) < 1, "weight", "weight < 1")
    if "exports" in df:
        I.add(pd.to_numeric(df.exports, errors="coerce") > rev * 1.01, "exports", "exports > revenue")
    for f in ["cost_of_sales", "operating_costs"]:
        if f in df:
            I.add(pd.to_numeric(df[f], errors="coerce") < 0, f, "negative value")
    if "cost_of_sales" not in df:
        I.add(pd.Series(True, index=df.index[:1]).reindex(df.index, fill_value=False), "cost_of_sales",
              "absent: price-cost margin and Boone indicator not computed", "warning")
    return I.items


def validate_table(path, root, kind, max_items=500):
    """Hesabat: ok, mode (SYNTHETIC/REAL), sətir və sahə üzrə səhvlər (row = faylın sətri, başlıq = 1)."""
    root = Path(root)
    try:
        cmap = column_map(root, kind)
    except OSError as e:
        return {"ok": False, "kind": kind, "errors": [{"message": "Sütun xəritəsi tapılmadı: %s" % e}], "warnings": [], "summary": {}}
    try:
        raw = read_table(path)
    except Exception as e:
        hint = " (.xlsx faylında «data» vərəqi olmalıdır)" if str(path).lower().endswith((".xlsx", ".xls")) else ""
        return {"ok": False, "kind": kind, "errors": [{"message": "Fayl oxunmadı%s: %s" % (hint, e)}], "warnings": [], "summary": {}}
    df, unknown = normalise(raw, cmap)
    synthetic = "data_status" in df and df["data_status"].astype(str).eq(SYN_STATUS).all()
    df = prepare(df)
    regs = regions(root, kind)
    items = (fr10_validate if kind == "firm_panel" else fr12_validate)(df, cmap, regs)
    for it in items:
        it["message"] = RULE_AZ.get(it["rule"], it["rule"])
        for k in ("firm_id", "year"):
            v = it.get(k)
            if hasattr(v, "item"):                       # numpy scalar -> python
                v = v.item()
            if isinstance(v, float):
                v = None if v != v else (int(v) if v.is_integer() else v)
            it[k] = v if (v is None or isinstance(v, (int, float))) else str(v)
    hard = [i for i in items if i["severity"] in ("fatal", "error")]
    warn = [i for i in items if i["severity"] == "warning"]
    errors = hard[:max_items]
    if synthetic:
        errors.insert(0, {"severity": "fatal", "field": "data_status", "rule": "synthetic marker",
                          "message": "Faylın bütün sətirlərində sintetik nişan var («%s») — real məlumat kimi tətbiq edilmir" % SYN_STATUS})
    by_rule = {}
    for i in items:
        by_rule[i["rule"]] = by_rule.get(i["rule"], 0) + 1
    yrs = df["year"].dropna() if "year" in df else []
    return {"ok": not hard and not synthetic, "kind": kind, "errors": errors, "warnings": warn[:max_items],
            "summary": {"rows": int(len(df)), "firms": int(df["firm_id"].nunique()) if "firm_id" in df else 0,
                        "years": [int(min(yrs)), int(max(yrs))] if len(yrs) else None,
                        "mode": "SYNTHETIC" if synthetic else "REAL", "unknown_columns": [str(c) for c in unknown],
                        "errors_total": len(hard), "warnings_total": len(warn), "by_rule": by_rule}}

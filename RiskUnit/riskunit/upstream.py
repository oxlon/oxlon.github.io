"""Upstream adapters (v2 data spine): the three units that produce baselines, read-only, in one tidy store.

    OxLon macro §15.5.1  (Macro_OxLon/delivery)        ids  mx:<series_code>          (source=ours baseline + bands)
                                                             mx:<src>:<series_code>    (tmpl / mspec / imf comparators)
                                                             mx:asm:<assumption_key>   (assumptions.csv)
    Ministry unit (MU)   (Macro_MinistryUnit)           ids  mn:bu60:<code>            (MOE REPORT 3 PAGES / base 60)
                                                             mn:v8:<sheet>:<code>      (8 vərəq official annex)
                                                             mn:ev:<variable>          (eviews/eviews_data.csv)
                                                             mn:caem:<sheet>:<code>    (CAEM baseline levels/growth only)
    MicroUnit §15.5.2    (MicroUnit/output)             ids  fr<k>:<code>              (all six FRx_forecast_tidy tables)
                                                             fr1:exo:<id>              (FR1 engine exogenous assumptions)

Tidy columns: id, source, series_code, label_az, unit, scenario, year, kind, value, lo80, hi80, lo50, hi50,
lower_5, upper_95, row_ref. The store is cached under data/upstream/ keyed by the SHA-256 of every source file, so it
is rebuilt automatically when an upstream unit publishes a new vintage (NFR2). Nothing is ever written upstream.

Side tables (data/upstream/): oxlon_backtest_summary.csv (h=1 errors per series, DINAMIKLIK rows dropped),
oxlon_equations.csv (se_regression), micro_registries.csv (equations per module), micro_multipliers.csv
(FR1 step responses + FR10 cross-sector multipliers), micro_fan_quantiles.csv (FR1 fan draws → p05..p95).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

STORE = config.UPSTREAM_STORE / "upstream_tidy.csv.gz"
STORE_META = config.UPSTREAM_STORE / "upstream_meta.json"
TIDY_COLS = ["id", "source", "series_code", "label_az", "unit", "scenario", "year", "kind", "value",
             "lo80", "hi80", "lo50", "hi50", "lower_5", "upper_95", "row_ref"]

_TR = str.maketrans({"ə": "e", "Ə": "e", "ı": "i", "İ": "i", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u",
                     "ş": "s", "Ş": "s", "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g"})
GENERIC = {"real artım tempi", "real artım", "deflyator", "payı (ümumi daxili məhsulda)", "payı (üdm-də)",
           "çəki, %", "əlavə dəyər", "artım tempi", "üdm-ə nisbəti", "mln usd", "usd", "real growth rate",
           "nominal growth rate", "deflator", "share", "real artım sürəti", "çəki"}


def slug(s: str, n: int = 48) -> str:
    s = str(s).translate(_TR).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:n].strip("_") or "x"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_files() -> dict[str, Path]:
    return {**{f"macro:{k}": v for k, v in {**config.MACRO_FILES, **config.MACRO_FILES_V2}.items()},
            **{f"micro:{k}": v for k, v in {**config.MICRO_FILES, **config.MICRO_FILES_V2}.items()},
            **{f"ministry:{k}": v for k, v in config.MINISTRY_FILES.items()}}


def fingerprint() -> dict[str, str]:
    return {k: (_sha(p) if p.exists() else "") for k, p in source_files().items()}


def _frame(rows) -> pd.DataFrame:
    d = pd.DataFrame(rows)
    for c in TIDY_COLS:
        if c not in d.columns:
            d[c] = np.nan
    return d[TIDY_COLS]


# ---------------------------------------------------------------- (a) OxLon macro §15.5.1
OX_SRC = {"ours": "", "template_sample": "tmpl:", "ministry_spec": "mspec:", "imf_reference": "imf:",
          "ministry_official": "mofficial:"}


def oxlon_tidy() -> pd.DataFrame:
    f = pd.read_csv(config.MACRO_FILES["forecast_long"], float_precision="round_trip")
    sd = pd.read_csv(config.MACRO_FILES_V2["series_dictionary"])
    lab = sd.drop_duplicates("series_code").set_index("series_code")["name_az"]
    f["id"] = ["mx:" + OX_SRC.get(s, s + ":") + c for s, c in zip(f["source"], f["series_code"])]
    f["label_az"] = f["series_name_az"].fillna(f["series_code"].map(lab))
    f["source"] = "oxlon:" + f["source"].astype(str)
    f["scenario"] = np.where(f["kind"] == "actual", "ACTUAL", "Baseline")
    f["row_ref"] = "forecast_long.csv"
    out = [_frame(f)]
    a = pd.read_csv(config.MACRO_FILES["assumptions"])
    a = a.assign(id="mx:asm:" + a["assumption_key"], source="oxlon:assumptions", series_code=a["assumption_key"],
                 label_az=a["note"].fillna(a["assumption_key"]), scenario="Baseline", kind="assumption",
                 row_ref="assumptions.csv")
    out.append(_frame(a))
    return pd.concat(out, ignore_index=True)


def oxlon_side_tables() -> dict[str, pd.DataFrame]:
    bt = pd.read_csv(config.MACRO_FILES["validation_backtest"])
    bt = bt[bt["model"] != "DINAMIKLIK"]
    g = bt.groupby(["series_code", "model"])
    bsum = g.agg(n=("error", "size"), mean_error=("error", "mean"), rmse=("error", lambda e: float(np.sqrt(np.mean(e ** 2)))),
                 mae=("abs_error", "mean"), rw_rmse=("rw_rmse_h", "last"), coverage80=("coverage80", "last"),
                 first_vintage=("vintage_year", "min"), last_vintage=("vintage_year", "max")).reset_index()
    bsum["id"] = "mx:" + bsum["series_code"]
    eq = pd.read_csv(config.MACRO_FILES_V2["equations_catalog"])
    eq = eq[["fr", "workbook", "sheet", "eq_name", "lhs", "series_code", "sample_start", "sample_end", "adj_r2",
             "se_regression"]].copy()
    eq["id"] = "mx:" + eq["series_code"].astype(str)
    return {"oxlon_backtest_summary": bsum, "oxlon_equations": eq}


# ---------------------------------------------------------------- (b) Ministry unit (cached values only; never recalculated)
def _year_header(rows, lo=1990, hi=2035):
    """(row index, {col: year}) of the first row holding ≥ 4 year integers."""
    for i, r in enumerate(rows):
        ys = {j: int(v) for j, v in enumerate(r) if isinstance(v, (int, float)) and not isinstance(v, bool)
              and float(v).is_integer() and lo <= v <= hi}
        if len(ys) >= 4:
            return i, ys
    return None, {}


def _num(v):
    if isinstance(v, bool) or v is None:
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(" ", "").replace(",", "."))
    except ValueError:
        return np.nan                                  # '#REF!', text


def parse_sheet(rows, prefix: str, source: str, ref: str, first_forecast: int | None = None,
                label_cols=(0, 1, 2), max_label_col: int = 3) -> list[dict]:
    """Generic Ministry table parser: label (first text cell in the leading columns), unit (next short text),
    year columns from the header row. Generic sub-rows ('real artım tempi', 'deflyator', …) inherit the
    parent label so the code stays meaningful; codes are made unique with a numeric suffix."""
    h, ycols = _year_header(rows)
    if h is None:
        return []
    out, parent, seen = [], "", {}
    for i in range(h + 1, len(rows)):
        r = list(rows[i]) + [None] * 3
        texts = [(j, str(r[j]).strip()) for j in range(max_label_col) if isinstance(r[j], str) and str(r[j]).strip()]
        texts = [(j, t) for j, t in texts if not re.fullmatch(r"[\d\.]+", t)]          # drop '1.', '2.1.'
        vals = {y: _num(r[j]) for j, y in ycols.items()}
        if not texts and not any(np.isfinite(v) for v in vals.values()):
            continue
        label = texts[0][1] if texts else ""
        unit = texts[1][1] if len(texts) > 1 and len(texts[1][1]) <= 25 and not texts[1][1].startswith("#") else ""
        if len(label) <= 2 and len(texts) > 1:          # 'a', 'b' item letters: the name sits in the next column
            label, unit = texts[1][1], (texts[2][1] if len(texts) > 2 and len(texts[2][1]) <= 25 else "")
        if label and not any(np.isfinite(v) for v in vals.values()):
            parent = label                              # section / parent heading row
            continue
        low = re.sub(r"\s+", " ", label.lower()).strip()
        if not label or low in GENERIC or low.startswith(("real artım", "deflyator", "payı", "çəki", "artım tempi")):
            lab_full, code = f"{parent}: {label or unit}".strip(": "), slug(parent, 30) + "." + slug(label or unit, 20)
        else:
            parent, lab_full, code = label, label, slug(label)
        if unit and code in seen and slug(unit) not in code:
            code = code + "." + slug(unit, 12)
        k = seen.get(code, 0)
        seen[code] = k + 1
        if k:
            code = f"{code}_{k + 1}"
        for y, v in vals.items():
            if not np.isfinite(v):
                continue
            kind = "forecast" if first_forecast and y >= first_forecast else "actual"
            out.append({"id": f"{prefix}{code}", "source": source, "series_code": code, "label_az": lab_full,
                        "unit": unit, "scenario": "Baseline" if kind == "forecast" else "ACTUAL", "year": y,
                        "kind": kind, "value": v, "row_ref": f"{ref}!R{i + 1}"})
    return out


def _xlsx_rows(path: Path, sheet: str, max_row: int = 200, max_col: int = 40):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return list(wb[sheet].iter_rows(min_row=1, max_row=max_row, max_col=max_col, values_only=True))
    finally:
        wb.close()


V8_SHEETS = ["2.4.1.1.", "2.4.1.2.", "2.4.1.3.", "2.4.1.4.", "2.4.1.5.-7.", "2.4.1.13.-14."]
CAEM_SHEETS = {"6a. SEI": ("sei", 60), "MOE_report": ("rep", 125), "Oil_and_gas_sector": ("og", 80)}


def ministry_tidy() -> pd.DataFrame:
    """Bottom-up base 60 (K–P = 2025–2030), the official 8-vərəq annex, eviews_data.csv and the CAEM
    baseline levels/growth (6a. SEI, MOE_report, Oil_and_gas_sector). CAEM risk sheets are not read here."""
    rows = []
    F = config.MINISTRY_FILES
    if F["bottomup_report"].exists():
        rows += parse_sheet(_xlsx_rows(F["bottomup_report"], "base 60", 160, 17), "mn:bu60:", "ministry:bottomup",
                            "MOE REPORT 3 PAGES.xlsx/base 60", first_forecast=2025, max_label_col=2)
    if F["vereq8"].exists():
        import openpyxl
        wb = openpyxl.load_workbook(F["vereq8"], read_only=True, data_only=True)
        names = wb.sheetnames
        wb.close()
        for sh in V8_SHEETS:
            if sh in names:
                rows += parse_sheet(_xlsx_rows(F["vereq8"], sh, 120, 22), f"mn:v8:{slug(sh, 12)}:", "ministry:8vereq",
                                    f"8 vərəq.xlsx/{sh}", first_forecast=2025)
    if F["caem"].exists():
        for sh, (code, mr) in CAEM_SHEETS.items():
            rows += parse_sheet(_xlsx_rows(F["caem"], sh, mr, 40), f"mn:caem:{code}:", "ministry:caem",
                                f"CAEM.xlsx/{sh}", first_forecast=2025)
    if F["eviews_data"].exists():
        ev = pd.read_csv(F["eviews_data"])
        ycol = "year" if "year" in ev.columns else ev.columns[0]
        for c in ev.columns:
            if c == ycol:
                continue
            for y, v in zip(ev[ycol], pd.to_numeric(ev[c], errors="coerce")):
                if np.isfinite(v):
                    rows.append({"id": f"mn:ev:{c.lower()}", "source": "ministry:eviews", "series_code": c,
                                 "label_az": c, "unit": "", "scenario": "Baseline" if y >= 2026 else "ACTUAL",
                                 "year": int(y), "kind": "assumption" if y >= 2026 else "actual", "value": float(v),
                                 "row_ref": "eviews/eviews_data.csv"})
    return _frame(rows)


# ---------------------------------------------------------------- (c) MicroUnit §15.5.2
def _micro_import():
    root = str(config.MICRO_DIR)
    if root not in sys.path:
        sys.path.insert(0, root)


def micro_tidy() -> pd.DataFrame:
    """All six FRx_forecast_tidy tables joined with their indicator catalogs (labels, units, has_band)."""
    out = []
    for m in config.MICRO_MODULES:
        t = pd.read_csv(config.MICRO_FILES_V2[f"{m.lower()}_tidy"], low_memory=False)
        c = pd.read_csv(config.MICRO_FILES_V2[f"{m.lower()}_catalog"]).drop_duplicates("id").set_index("id")
        t["source"] = f"micro:{m}"
        t["series_code"] = t["id"].str.split(":", n=1).str[1]
        t["label_az"] = t["id"].map(c["label_az"])
        t["unit"] = t["unit_az"].fillna(t["id"].map(c["unit_az"]))
        t["kind"] = np.where(t["is_forecast"].astype(str).str.lower() == "true", "forecast", "actual")
        t["row_ref"] = f"{m}_forecast_tidy.csv"
        out.append(_frame(t))
    return pd.concat(out, ignore_index=True)


def micro_exogenous() -> pd.DataFrame:
    """FR1 engine exogenous assumptions (Brent, oil/gas output, FX, policy rate, …) per scenario: fr1:exo:<id>."""
    _micro_import()
    try:
        from microlib.engines import fr1
        inp = fr1.inputs()
    except Exception as exc:                              # noqa: BLE001
        print(f"  DİQQƏT: FR1 mühərriki yüklənmədi ({type(exc).__name__}: {exc}) — fr1:exo:* buraxıldı")
        return _frame([])
    rows = []
    for e in inp.get("exogenous", []):
        for sc, vals in e["baseline"].items():
            for y, v in zip(e["years"], vals):
                rows.append({"id": f"fr1:exo:{e['id']}", "source": "micro:FR1:inputs", "series_code": e["id"],
                             "label_az": e.get("label_az", e["id"]), "unit": e.get("unit", ""), "scenario": sc,
                             "year": int(y), "kind": "assumption", "value": float(v),
                             "row_ref": "microlib.engines.fr1.inputs()"})
    return _frame(rows)


def micro_side_tables() -> dict[str, pd.DataFrame]:
    reg = []
    for m in config.MICRO_MODULES:
        p = config.MICRO_FILES_V2[f"{m.lower()}_equations"]
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        eqs = d.get("equations", [])
        eqs = eqs if isinstance(eqs, list) else list(eqs.values())
        for e in eqs:
            e = e if isinstance(e, dict) else {}
            reg.append({"module": m, "eq_id": e.get("eq_id", e.get("id", "")), "lhs": e.get("lhs", e.get("dependent", "")),
                        "verdict": e.get("verdict", e.get("status", "")), "n_obs": e.get("nobs", e.get("n_obs", np.nan)),
                        "data_mode": d.get("data_mode", "")})
    mul = pd.read_csv(config.MICRO_FILES["fr1_multipliers"])
    mul = mul.rename(columns={mul.columns[0]: "shock", mul.columns[1]: "year"})
    mul = mul.melt(["shock", "year"], var_name="variable", value_name="response")
    mul["id"] = "fr1:" + mul["variable"]
    mul["table"] = "FR1_multipliers"
    cs = pd.read_csv(config.MICRO_FILES_V2["fr10_cross_multipliers"])
    cs = cs.assign(table="FR10_cross_sector_multipliers", id="fr10:nace:" + cs["nace2"].astype(str))
    dr = pd.read_csv(config.MICRO_FILES["fr1_draws"])
    q = dr.drop(columns="draw").groupby("year").quantile([0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
    q.index.names = ["year", "q"]
    q = q.reset_index().melt(["year", "q"], var_name="variable", value_name="value")
    q["id"] = "fr1:" + q["variable"]
    q["n_draws"] = dr["draw"].nunique()
    return {"micro_registries": pd.DataFrame(reg), "micro_multipliers": pd.concat([mul, cs], ignore_index=True),
            "micro_fan_quantiles": q}


# ---------------------------------------------------------------- store, catalog, run
def build(verbose: bool = True) -> pd.DataFrame:
    t0 = time.time()
    parts = [oxlon_tidy(), ministry_tidy(), micro_tidy(), micro_exogenous()]
    S = pd.concat(parts, ignore_index=True)
    S["year"] = pd.to_numeric(S["year"], errors="coerce").astype("Int64")
    S = S.drop_duplicates(["id", "scenario", "year", "source"], keep="first")
    S.to_csv(STORE, index=False, float_format="%.10g", compression="gzip")
    for name, df in {**oxlon_side_tables(), **micro_side_tables()}.items():
        df.to_csv(config.UPSTREAM_STORE / f"{name}.csv", index=False, float_format="%.8g")
    STORE_META.write_text(json.dumps({"fingerprint": fingerprint(), "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                      "n_rows": int(len(S)), "n_ids": int(S["id"].nunique())}, indent=1))
    store.cache_clear()
    if verbose:
        print(f"  yuxarı axın anbarı: {len(S):,} sətir, {S['id'].nunique():,} sıra ({time.time() - t0:.1f} san)")
    return S


def is_stale() -> bool:
    if not (STORE.exists() and STORE_META.exists()):
        return True
    try:
        return json.loads(STORE_META.read_text()).get("fingerprint") != fingerprint()
    except (ValueError, OSError):
        return True


@lru_cache(maxsize=1)
def store() -> pd.DataFrame:
    """The tidy store; rebuilt when any upstream file's hash differs from the one it was built from."""
    if is_stale():
        return build(verbose=False)
    return pd.read_csv(STORE, low_memory=False)


def series(sid: str, scenario: str | None = None) -> pd.DataFrame:
    S = store()
    s = S[S["id"] == sid]
    if scenario:
        s = s[s["scenario"].isin([scenario, "ACTUAL"])]
    return s.sort_values("year")


def clear_caches():
    store.cache_clear()


def catalog(S: pd.DataFrame | None = None) -> pd.DataFrame:
    """D1: one row per series id — source, label, unit, year span, band, scenarios."""
    S = store() if S is None else S
    band = S[["lo80", "lower_5"]].notna().any(axis=1)
    g = S.assign(band=band, fc=S["kind"].isin(["forecast", "assumption"])).groupby("id", sort=True)
    yr = lambda s: f"{int(s.min())}–{int(s.max())}" if s.notna().any() else ""      # noqa: E731
    cat = pd.DataFrame({
        "source": g["source"].first(), "label_az": g["label_az"].first(), "unit": g["unit"].first(),
        "years": g["year"].agg(yr),
        "forecast_years": S[S["kind"].isin(["forecast", "assumption"])].groupby("id")["year"].agg(yr),
        "has_band": g["band"].any(), "n_obs": g["value"].count(),
        "scenarios": g["scenario"].agg(lambda s: ";".join(sorted(set(map(str, s.dropna()))))),
        "row_ref": g["row_ref"].first()}).reset_index()
    cat["forecast_years"] = cat["forecast_years"].fillna("")
    cat["unit_group"] = cat["source"].str.split(":").str[0].map(
        {"oxlon": "makro OxLon §15.5.1", "ministry": "Nazirlik (MU)", "micro": "mikro §15.5.2"})
    return cat


def run(ctx: dict | None = None, verbose: bool = True) -> dict:
    """Build (if stale) the tidy store and write output/D1_upstream_catalog.csv."""
    from . import spine
    S = build(verbose) if is_stale() or (ctx or {}).get("force") else store()
    cat = catalog(S)
    out = config.OUTPUT / "D1_upstream_catalog.csv"
    cat.to_csv(out, index=False)
    spine.register_output("D1_upstream_catalog.csv", "upstream",
                          "Yuxarı axın kataloqu: makro OxLon (mx:), Nazirlik CAEM/Bottom-up/8 vərəq/EViews (mn:) və "
                          "mikro FR1–FR12 (fr<k>:) üzrə hər sıra — mənbə, ad, vahid, illər, interval (fan) varlığı",
                          list(cat.columns), "yuxarı axın yeni vintaj verdikdə")
    by = cat.groupby("unit_group")["id"].count().to_dict()
    if verbose:
        print("  D1 kataloq: " + ", ".join(f"{k} {v}" for k, v in by.items()))
    return {"catalog": cat, "n_series": int(len(cat)), "by_unit": by, "store_rows": int(len(S))}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Yuxarı axın adapterləri (OxLon, Nazirlik, MicroUnit) → tidy anbar + D1")
    ap.add_argument("--force", action="store_true", help="hash dəyişməsə də yenidən qur")
    a = ap.parse_args()
    r = run({"force": a.force})
    print(f"Hazırdır: {r['n_series']} sıra, {r['store_rows']:,} sətir")

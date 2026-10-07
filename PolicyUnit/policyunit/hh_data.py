"""Household microdata I/O for the microsimulation (FR3): DATA_MODE switch, column map,
template and validator — same pattern as MicroUnit FR10/FR12 synthetic layers.

DATA_MODE (env POLICY_HH_MODE): "SYNTHETIC" (default; data/households/PU_households_SYNTHETIC.csv)
or "REAL" (data/households/PU_households.csv|.xlsx or env POLICY_HH_PATH). A file whose
`data_status` column is missing or differs from the watermark is treated as REAL.
Headers may be English or Azerbaijani (PU_households_column_map.csv)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from .synth_households import WATERMARK

ROOT = Path(__file__).resolve().parent.parent
HH_DIR = ROOT / "data" / "households"
SYNTH_CSV = HH_DIR / "PU_households_SYNTHETIC.csv"
REAL_CSV = HH_DIR / "PU_households.csv"
CAL_JSON = HH_DIR / "PU_households_calibration.json"
COLMAP_CSV = HH_DIR / "PU_households_column_map.csv"
TEMPLATE_CSV = HH_DIR / "PU_households_TEMPLATE.csv"
CATS = ["food", "alc", "tobacco", "clothing", "housing", "furnish", "health", "transport",
        "comm", "recreation", "education", "restaurants", "misc"]
# column, az header, level (P person / H household repeated), required, description_az
COLUMNS = [
    ("data_status", "məlumat_statusu", "H", 0, "Sintetik su nişanı; real faylda boş/olmaya bilər"),
    ("hh_id", "ev_id", "H", 1, "Ev təsərrüfatının psevdonim identifikatoru"),
    ("person_id", "şəxs_id", "P", 1, "Şəxsin identifikatoru"),
    ("weight", "çəki", "H", 1, "Ev təsərrüfatının genişləndirmə çəkisi"),
    ("region", "iqtisadi_rayon", "H", 1, "İqtisadi rayon (2021 təsnifatı)"),
    ("urban", "şəhər", "H", 1, "1 = şəhər, 0 = kənd"),
    ("rel", "qohumluq", "P", 0, "head/spouse/child/parent/other"),
    ("age", "yaş", "P", 1, "Yaş (tam il)"),
    ("sex", "cins", "P", 1, "M/F"),
    ("status", "fəaliyyət_statusu", "P", 1, "employee/selfemp/agri/unemployed/pensioner/student/"
     "inactive/child"),
    ("sector", "sektor", "P", 0, "NACE bölməsi (MicroUnit FR4 açarı: agr ... othsvc)"),
    ("ownership", "mülkiyyət", "P", 0, "state/nonstate (muzdlu işçi)"),
    ("regime", "vergi_rejimi", "P", 0, "state (dövlət + neft-qaz) / priv (qeyri-neft özəl)"),
    ("budget", "büdcə_təşkilatı", "P", 0, "1 = büdcə təşkilatı işçisi"),
    ("formal_ft", "tam_ştat", "P", 0, "1 = tam iş günü (minimum əmək haqqı tətbiq olunur)"),
    ("wage_gross", "əmək_haqqı_hesablanmış", "P", 0, "Hesablanmış (gross) aylıq əmək haqqı, AZN"),
    ("wage_net", "əmək_haqqı_xalis", "P", 0, "Xalis aylıq əmək haqqı (gross yoxdursa)"),
    ("inc_selfemp", "gəlir_özünüməşğulluq", "P", 1, "Qeyri-k/t özünüməşğulluq gəliri, AZN/ay"),
    ("inc_agri", "gəlir_kənd_təsərrüfatı", "P", 1, "K/t gəliri (həyətyanı daxil), AZN/ay"),
    ("pension", "pensiya", "P", 1, "Pensiya (baza ili), AZN/ay"),
    ("pension_type", "pensiya_növü", "P", 0, "age/disability/survivor"),
    ("benefit_other", "digər_müavinət", "P", 1, "ÜSY-dən başqa müavinətlər, AZN/ay"),
    ("inc_property", "gəlir_mülkiyyət", "H", 1, "Mülkiyyət gəliri (ev üzrə), AZN/ay"),
    ("remit", "xaricdən_pul", "H", 1, "Xaricdən pul köçürmələri (ev üzrə), AZN/ay"),
    ("transfer_hh", "ev_arası_transfer", "H", 1, "Digər ev təsərrüfatlarından gəlir, AZN/ay"),
    ("utsy_u", "üsy_müraciət_indeksi", "H", 0, "0–1 ÜSY müraciət indeksi (real fayl: 0 = ÜSY alır, 1 = almır)"),
    ("cons_noise", "istehlak_küyü", "H", 0, "Yalnız sintetik generator üçün"),
] + [(f"cons_{c}", f"istehlak_{c}", "H", 1, f"İstehlak xərci — {c}, AZN/ay (ev üzrə)")
     for c in CATS]
NUMERIC = ["weight", "urban", "age", "budget", "formal_ft", "wage_gross", "wage_net",
           "inc_selfemp", "inc_agri", "pension", "benefit_other", "inc_property", "remit",
           "transfer_hh", "utsy_u"] + [f"cons_{c}" for c in CATS]
STATUSES = {"employee", "selfemp", "agri", "unemployed", "pensioner", "student", "inactive",
            "child"}


def data_mode() -> str:
    return os.environ.get("POLICY_HH_MODE", "SYNTHETIC").upper()


def write_column_map():
    pd.DataFrame(COLUMNS, columns=["column", "column_az", "level", "required",
                                   "description_az"]).to_csv(COLMAP_CSV, index=False)


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    az = {a: c for c, a, *_ in COLUMNS}
    return df.rename(columns={k: az.get(k, k) for k in df.columns})


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Return issues (row, field, severity error|warning, message_az)."""
    iss = []
    add = lambda r, f, s, m: iss.append({"row": r, "field": f, "severity": s, "message_az": m})
    for c, _, _, req, _ in COLUMNS:
        if req and c not in df.columns:
            add(-1, c, "error", "məcburi sütun yoxdur")
    if "wage_gross" not in df.columns and "wage_net" not in df.columns:
        add(-1, "wage_gross", "error", "wage_gross və ya wage_net sütunu lazımdır")
    for c in NUMERIC:
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            for r in np.where(v.isna() & df[c].notna() & (df[c].astype(str) != ""))[0][:50]:
                add(int(r), c, "error", "rəqəm deyil")
            for r in np.where(v < 0)[0][:50]:
                add(int(r), c, "error", "mənfi dəyər")
    if "status" in df.columns:
        for r in np.where(~df["status"].isin(STATUSES))[0][:50]:
            add(int(r), "status", "error", f"naməlum status '{df['status'].iat[r]}'")
    if {"hh_id", "weight"} <= set(df.columns):
        k = df.groupby("hh_id")["weight"].nunique()
        for h in k[k > 1].index[:50]:
            add(-1, "weight", "error", f"ev {h}: çəki üzvlər üzrə fərqlidir")
    if "person_id" in df.columns and df["person_id"].duplicated().any():
        add(-1, "person_id", "error", "təkrarlanan şəxs identifikatoru")
    if {"status", "wage_gross"} <= set(df.columns):
        bad = (df["status"] != "employee") & (pd.to_numeric(df["wage_gross"]) > 0)
        if bad.any():
            add(-1, "wage_gross", "warning", f"{int(bad.sum())} qeyri-muzdlu şəxsdə əmək haqqı")
    return pd.DataFrame(iss, columns=["row", "field", "severity", "message_az"])


def load(path=None, mode=None, log=print):
    """Load households (person rows). Returns (df, calibration dict, is_synthetic)."""
    mode = (mode or data_mode()).upper()
    path = Path(path or os.environ.get("POLICY_HH_PATH", "")) if (path or os.environ.get(
        "POLICY_HH_PATH")) else (SYNTH_CSV if mode == "SYNTHETIC" else REAL_CSV)
    if path.suffix == ".xlsx":
        df = pd.read_excel(path, sheet_name="data")
    else:
        df = pd.read_csv(path, keep_default_na=False, low_memory=False)
    df = normalise_columns(df)
    synth = "data_status" in df.columns and (df["data_status"] == WATERMARK).all()
    iss = validate(df)
    if (iss["severity"] == "error").any():
        raise ValueError("Ev təsərrüfatı faylında səhvlər: " + "; ".join(
            f"{r.field}: {r.message_az}" for r in iss[iss.severity == "error"].head(5).itertuples()))
    for c in NUMERIC:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    for c in ("sector", "ownership", "regime", "pension_type", "rel"):
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].astype(str).replace("nan", "")
    for c, d in (("budget", 0), ("formal_ft", 1), ("utsy_u", 1.0), ("cons_noise", 0.0)):
        if c not in df.columns:
            df[c] = d
    cal_path = CAL_JSON if synth else path.with_suffix(".calibration.json")
    cal = json.loads(cal_path.read_text()) if cal_path.exists() else {
        "base_year": int(os.environ.get("POLICY_HH_YEAR", 2024)), "factors": {},
        "uprate": {}, "p_takeup": 1.0, "kappa": 1.0}
    if "wage_gross" not in df.columns or (df["wage_gross"] == 0).all():
        from . import taxben
        df["wage_gross"] = taxben.net_to_gross(df.get("wage_net", 0.0), df["regime"],
                                               taxben.Params(), cal["base_year"])
    return df, cal, synth

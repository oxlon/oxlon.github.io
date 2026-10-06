"""Nazirlik CAEM modeli — müqayisə (gecikmiş hədli sistem; əsas ötürmə kanalı deyil).

Re-implementation of the Ministry's CAEM `AZE Model` reduced form

    y_t = Bc + B1 y_{t-1} + B2 e_t        (48 states, annual)

read from `AZE Model`!C211:AX258 (B1), C262:AX309 (B2) and the constant C159:C206, with the
three debt rows (d_y, dd_y, df_y) recomputed exactly as the `8a. Simulation` sheet does (they
are spreadsheet formulas, not rows of B1). The system contains lagged terms, so under the
binding RU constraints it is ONLY a labelled Ministry cross-check: it never feeds RU's
transmission (that remains the micro FR1 structural step responses via `spine.multipliers`).
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

LABEL_AZ = "Nazirlik CAEM modeli — müqayisə (gecikmiş hədli sistem; əsas ötürmə kanalı deyil)"
MINISTRY_DIR = config.DATA / "ministry"
CAEM_COPY = MINISTRY_DIR / "CAEM.xlsx"
MINISTRY_ROOT = Path(os.environ.get("MIIS_MINISTRY_DIR", config.ROOT.parent / "Macro_MinistryUnit"))
CAEM_UPSTREAM = MINISTRY_ROOT / "Ministry_CAEM" / "CAEM.xlsx"
CAEM_MD5 = "12c22d22eda046e050643004a8d7eec5"     # vintage copied 2026-10-06 (xlsx of 22 Sep 2026)

N_STATE = 48
H = 12                                            # 8a horizons 0..12 (columns D..P)
RANGES = {"A0": (5, 52), "A1": (56, 103), "A2": (107, 154), "Ac": (159, 206),
          "B1": (211, 258), "B2": (262, 309)}
DEBT = ("d_y", "dd_y", "df_y")                    # rows 107-109 of 8a: spreadsheet formulas


def md5(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def workbook_path() -> Path:
    """The pinned RU copy (offline, reproducible); the upstream file only if the copy is missing."""
    return CAEM_COPY if CAEM_COPY.exists() else CAEM_UPSTREAM


def vintage_status() -> dict:
    """NFR2: does the Ministry's upstream CAEM.xlsx still equal the pinned copy?"""
    out = {"copy": str(CAEM_COPY), "copy_md5": md5(CAEM_COPY) if CAEM_COPY.exists() else None,
           "upstream": str(CAEM_UPSTREAM),
           "upstream_md5": md5(CAEM_UPSTREAM) if CAEM_UPSTREAM.exists() else None}
    out["pinned_ok"] = out["copy_md5"] == CAEM_MD5
    out["upstream_changed"] = (out["upstream_md5"] is not None and out["upstream_md5"] != out["copy_md5"])
    return out


@lru_cache(maxsize=2)
def workbook(data_only: bool = True):
    import openpyxl
    return openpyxl.load_workbook(workbook_path(), read_only=True, data_only=data_only)


def _num(v, blank=0.0) -> float:
    if isinstance(v, bool):
        return float(v)
    if isinstance(v, (int, float)):
        return float(v)
    if v is None or v == "":
        return blank
    return np.nan


def block(sheet: str, r0: int, r1: int, c0: int, c1: int, blank=0.0, data_only=True) -> np.ndarray:
    ws = workbook(data_only)[sheet]
    rows = ws.iter_rows(min_row=r0, max_row=r1, min_col=c0, max_col=c1, values_only=True)
    return np.array([[_num(v, blank) for v in r] for r in rows], float)


def cells(sheet: str, r0: int, r1: int, c0: int, c1: int, data_only=True) -> list[list]:
    ws = workbook(data_only)[sheet]
    out = []
    for r in ws.iter_rows(min_row=r0, max_row=r1, min_col=c0, max_col=c1, values_only=True):
        out.append([getattr(v, "text", v) for v in r])
    return out


def cell(sheet: str, ref: str, data_only=True):
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    col, row = coordinate_from_string(ref)
    c = column_index_from_string(col)
    return cells(sheet, row, row, c, c, data_only)[0][0]


@lru_cache(maxsize=1)
def load() -> dict:
    """All model objects from the workbook (values; blanks = 0 as in IFNA(...,0))."""
    m = {k: block("AZE Model", a, b, 3, 50) for k, (a, b) in RANGES.items() if k != "Ac"}
    a, b = RANGES["Ac"]
    m["Ac"] = np.nan_to_num(block("AZE Model", a, b, 3, 3)[:, 0])
    st = cells("8a. Simulation", 62, 109, 1, 3)
    m["states"] = pd.DataFrame(st, columns=["name", "unit", "code"])
    sh = cells("8a. Simulation", 5, 52, 1, 3)
    m["shocks"] = pd.DataFrame(sh, columns=["name", "unit", "code"])
    m["E_loaded"] = np.nan_to_num(block("8a. Simulation", 5, 52, 4, 16))
    m["Y_loaded"] = block("8a. Simulation", 62, 109, 4, 16)
    m["psi"] = float(cell("Parametrization", "G26"))      # domestic debt share
    m["ix"] = {c: i for i, c in enumerate(m["states"]["code"])}
    return m


def simulate(E: np.ndarray | None = None, targets: dict | None = None, fix_debt_bug: bool = False,
             m: dict | None = None) -> np.ndarray:
    """Deviation-from-baseline paths (48 x 13) exactly as `8a. Simulation` computes them.

    E: 48 x 13 shock matrix (rows = 8a rows 5..52, columns = horizons 0..12).
    targets: {state code: array(13)} — exogenous paths imposed by solving for the own shock
             each period (NaN = not imposed); used for level-step comparisons (C5).
    fix_debt_bug: the workbook's foreign-debt row from t=2 uses the lagged DOMESTIC debt
             (F109 `*E108`); True uses its own lag instead (shown only as a finding).
    """
    m = m or load()
    B1, B2, c, ix, psi = m["B1"], m["B2"], m["Ac"], m["ix"], m["psi"]
    E = np.zeros((N_STATE, H + 1)) if E is None else np.array(E, float).copy()
    y = np.zeros((N_STATE, H + 1))
    nd = N_STATE - len(DEBT)
    tg = {ix[k]: np.asarray(v, float) for k, v in (targets or {}).items()}
    for t in range(1, H + 1):
        act = [i for i, p in tg.items() if np.isfinite(p[t])]
        if act:
            base = c + B1 @ y[:, t - 1] + B2 @ E[:, t]
            gap = np.array([tg[i][t] for i in act]) - base[act]
            E[act, t] += np.linalg.solve(B2[np.ix_(act, act)], gap)
        y[:nd, t] = (c + B1 @ y[:, t - 1] + B2 @ E[:, t])[:nd]
        den = 1 + y[ix["dy"], t - 1] / 100 + y[ix["dP"], t - 1] / 100
        y[ix["dd_y"], t] = ((1 + y[ix["CR"], t - 1] / 100) / den * y[ix["dd_y"], t - 1]
                            - psi * y[ix["pb_y"], t])
        lag = y[ix["df_y"], t - 1] if (t == 1 or fix_debt_bug) else y[ix["dd_y"], t - 1]
        y[ix["df_y"], t] = ((1 + y[ix["R_f"], t] / 100) * (1 + y[ix["dS"], t] / 100) / den * lag
                            - (1 - psi) * y[ix["g_y"], t])
        y[ix["d_y"], t] = y[ix["dd_y"], t] + y[ix["df_y"], t]
    return y


# ---------------------------------------------------------------- validation of ranges and IRF
def validate() -> pd.DataFrame:
    """Checks that the ranges are what the brief says and that numpy reproduces the loaded
    experiment of `8a. Simulation` (+1 pp CPI cost-push shock at t=1)."""
    m = load()
    rows = []

    def add(check, value, ok, note=""):
        rows.append({"yoxlama": check, "deyer": value, "netice": "keçdi" if ok else "keçmədi",
                     "qeyd": note})

    f = workbook(False)["AZE Model"]
    lab = {r: cell("AZE Model", r, data_only=False) for r in ("A210", "A261", "B209", "C211", "C262")}
    add("AZE Model!A210 = 'B1', A261 = 'B2'", f"{lab['A210']} / {lab['A261']}",
        lab["A210"] == "B1" and lab["A261"] == "B2")
    add("AZE Model!B209 həll forması", str(lab["B209"]), "B1*y(t-1)" in str(lab["B209"]))
    add("B1 düsturu = MMULT(MINVERSE(A0 C5:AX52), A1 C56:AX103)", str(lab["C211"])[:70],
        "C5:AX52" in str(lab["C211"]) and "C56:AX103" in str(lab["C211"]))
    add("B2 düsturu = MMULT(MINVERSE(A0), A2 C107:AX154)", str(lab["C262"])[:70],
        "C107:AX154" in str(lab["C262"]))
    del f
    A0i = np.linalg.inv(m["A0"])
    d1 = float(np.max(np.abs(A0i @ m["A1"] - m["B1"])))
    d2 = float(np.max(np.abs(A0i @ m["A2"] - m["B2"])))
    add("max|inv(A0)·A1 − B1| (C211:AX258)", d1, d1 < 1e-9)
    add("max|inv(A0)·A2 − B2| (C262:AX309)", d2, d2 < 1e-9)
    codes_b1 = [r[0] for r in cells("AZE Model", 211, 258, 2, 2)]
    codes_b2 = [r[0] for r in cells("AZE Model", 262, 309, 2, 2)]
    same = codes_b1 == list(m["states"]["code"]) == codes_b2
    add("B1/B2 sətir kodları = 8a C62:C109 vəziyyət kodları (48)", len(codes_b1), same)
    e62 = str(cell("8a. Simulation", "E62", data_only=False))
    add("8a!E62 B1 sətri $C211:$AX211, B2 sətri $C262:$AX262, sabit $C159 istifadə edir", e62[:60],
        "$C211:$AX211" in e62 and "$C262:$AX262" in e62 and "$C159" in e62)
    add("Sabit (Ac, C159:C206) sıfırdır → Bc = 0", float(np.abs(m["Ac"]).sum()),
        float(np.abs(m["Ac"]).sum()) == 0.0,
        "8a Bc=inv(A0)·Ac əvəzinə Ac-ni toplayır; Ac=0 olduğundan nəticəyə təsir etmir")
    y = simulate(m["E_loaded"])
    err = float(np.nanmax(np.abs(y - m["Y_loaded"])))
    add("Yüklənmiş 8a təcrübəsinin təkrarı: max|Δ| (48×13)", err, err < 1e-9,
        "şok: " + ", ".join(f"{m['shocks'].code[i]} h={j}={m['E_loaded'][i, j]:g}"
                           for i, j in np.argwhere(m["E_loaded"] != 0)))
    ix = m["ix"]
    for code, h, ref in (("CR", 1, 2.42), ("dy", 1, -0.13), ("dy", 2, -0.20)):
        v = float(y[ix[code], h])
        add(f"{code} h={h} (gözlənilən ≈ {ref:+.2f})", round(v, 4), abs(v - ref) < 0.006)
    ev = np.sort(np.abs(np.linalg.eigvals(m["B1"])))[::-1]
    add("B1 məxsusi ədədləri: |λ|≥0,999 sayı (vahid köklər — səviyyə dəyişənləri)",
        int((ev >= 0.999).sum()), True, f"ən böyük |λ| = {ev[0]:.4f}")
    yb = simulate(m["E_loaded"], fix_debt_bug=True)
    add("Xarici borc sətri (8a F109:P109) xətası: düzəliş edilərsə df_y h=5 fərqi",
        round(float(yb[ix['df_y'], 5] - y[ix['df_y'], 5]), 4), True,
        "F109 düsturu E109 əvəzinə E108-ə (daxili borc) istinad edir")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- shock libraries (C4)
# 7. Scenario yellow-cell shocks mapped to the nearest AZE Model shock (sign, note).
SCENARIO_MAP = [
    ("SC01", "İnflyasiya (xərc) şoku", "dP", 1, "birbaşa analoq"),
    ("SC02", "ÜDM artımı şoku — təklif", "dta", 1, "yaxın analoq: məhsuldarlıq şoku"),
    ("SC03", "Potensial artım şoku", "dypot", 1, "birbaşa analoq"),
    ("SC04", "Vergi tədbirləri (ÜDM-ə %)", "vatax_y", 1, "yaxın analoq: ƏDV şoku"),
    ("SC05", "Xərc tədbirləri (ÜDM-ə %)", "pb_y", -1,
     "8a 'cari xərc şoku' pb_y sətrinə düşür; +xərc = −pb_y kimi verilir"),
    ("SC06", "Uçot dərəcəsinin dəyişməsi", "CR", 1, "birbaşa analoq"),
    ("SC07", "Kredit spredinin dəyişməsi", "CR", 1, "proksi: AZE modelində kredit faizi yoxdur"),
    ("SC08", "Siyasət mənşəli devalvasiya", "dS", 1, "birbaşa analoq"),
    ("SC09", "Ölkə risk mükafatı (100 bp)", "CR", 1, "proksi: ötürmə H40=1 → daxili faiz"),
    ("SC10", "Tərəfdaş ölkələrin artımı", "dy_f", 1, "birbaşa analoq"),
    ("SC11", "Xarici siyasət faizi", "R_f", 1, "birbaşa analoq"),
    ("SC12", "Qeyri-neft idxal qiyməti şoku", "tot", -1, "ticarət şərtləri: idxal qiyməti ↑ → tot ↓"),
    ("SC13", "Qeyri-neft ixrac qiyməti şoku", "tot", 1, "ticarət şərtləri: ixrac qiyməti ↑ → tot ↑"),
    ("SC14", "Neft qiymətinin dəyişməsi", "dPoil", 1, "birbaşa analoq"),
]


SHORT_LABEL = "CAEM AZE Model (Nazirlik — müqayisə)"


def _long(y, m, base: dict) -> list[dict]:
    codes = m["states"]["code"]
    return [{**base, "variable": codes[i], "horizon": h, "response": round(float(y[i, h]), 6)}
            for i in range(N_STATE) for h in range(H + 1)]


def shock_library() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """C4: unit-impulse IRFs of the 26 named `8a` shocks (+1 at h=1, as the loaded experiment)
    and of the 14 `7. Scenario` shocks (+1 unit for h=1..3 = 2025-2027, mapped).
    Returns (long IRF table, shock index with names/units/mapping, variable dictionary)."""
    m = load()
    rows, idx = [], []
    named = m["shocks"][m["shocks"]["name"].notna()]
    for i, r in named.iterrows():
        E = np.zeros((N_STATE, H + 1))
        E[i, 1] = 1.0
        rows += _long(simulate(E, m=m), m, {"library": "8a", "shock_id": r.code, "shock": r["name"]})
        idx.append({"library": "8a. Simulation (struktur şok)", "shock_id": r.code, "shock": r["name"],
                    "shock_unit": r.unit, "mapped_to": r.code, "sign": 1, "profile": "h=1: +1",
                    "input_cells": f"'8a. Simulation'!D{i + 5}:P{i + 5}", "note_az": ""})
    for sid, name, code, sign, note in SCENARIO_MAP:
        E = np.zeros((N_STATE, H + 1))
        E[m["ix"][code], 1:4] = sign
        rows += _long(simulate(E, m=m), m, {"library": "7. Scenario", "shock_id": sid, "shock": name})
        idx.append({"library": "7. Scenario (deterministik şok, xəritələnmiş)", "shock_id": sid, "shock": name,
                    "shock_unit": "1 vahid", "mapped_to": code, "sign": sign,
                    "profile": "h=1..3 (2025–2027): ±1", "input_cells": "bax: caem_risk_scenario_shocks",
                    "note_az": note})
    df = pd.DataFrame(rows)
    df.insert(0, "model", SHORT_LABEL)
    ix = pd.DataFrame(idx)
    ix.insert(0, "model", LABEL_AZ)
    st = m["states"].rename(columns={"code": "variable", "name": "variable_name"})
    return df, ix, st[["variable", "variable_name", "unit"]]


# ---------------------------------------------------------------- transmission comparison (C5)
OXLON_DIR = Path(os.environ.get("MIIS_OXLON_DIR", config.ROOT.parent / "Macro_OxLon"))
OXLON_OUT = OXLON_DIR / "delivery" / "2_neticeler"
OXLON_SRC = OXLON_DIR / "model 2" / "src"
WORK = config.ROOT / "work" / "caem"
YEARS = list(range(2026, 2031))                   # h=1..5 ↔ 2026..2030 (FR1 shocks start 2026)

COMPARABLE = {
    "brent10": ("Brent +10 USD/barel (davamlı səviyyə)", "Brent +10 USD/bbl"),
    "extdem10": ("Xarici tələb +10% (davamlı səviyyə)", "External demand +10%"),
    "rate_m200": ("Uçot dərəcəsi −200 bp (davamlı)", "Credit easing (-200 bp policy, -100 bp deposit)"),
    "stateinv1bn": ("Dövlət investisiyası +1 mlrd AZN (davamlı)", "State investment +1 bn AZN (real)"),
}
CONCEPTS = {  # concept: (az label, unit, CAEM state or derived, FR1 column)
    "gdp_level": ("Real ÜDM səviyyəsi", "baza ilə fərq, %", "y", "rgdp"),
    "nonoil_level": ("Qeyri-neft (qeyri-əmtəə) ÜDM səviyyəsi", "baza ilə fərq, %", "cum:dy_ncom", "rgdpnon"),
    "cpi_infl": ("İstehlak qiymətləri inflyasiyası", "faiz bəndi", "dP", "infl"),
    "fiscal_pct": ("Büdcə balansı (CAEM: ilkin balans)", "ÜDM-ə %, baza ilə fərq", "pb_y", "balance_pct"),
    "policy_rate": ("Uçot dərəcəsi", "faiz bəndi", "CR", None),
    "nonoil_exports": ("Qeyri-neft ixracı (real)", "baza ilə fərq, %", "x", "rx_non"),
}


def _oxlon_baseline() -> pd.DataFrame:
    p = OXLON_OUT / "forecast_long.csv"
    if not p.exists():
        p = config.MACRO_FILES["forecast_long"]
    f = pd.read_csv(p, float_precision="round_trip")
    return f[f["source"] == "ours"]


def _caem_paths(key: str, ox: pd.DataFrame) -> np.ndarray:
    m = load()
    nan = np.full(H + 1, np.nan)
    g = ox[(ox.series_code == "gdp_nom") & (ox.kind == "forecast")].set_index("year")["value"]
    if key == "brent10":
        b26 = float(ox[(ox.series_code == "brent_usd") & (ox.year == 2026)]["value"].iloc[0])
        p = nan.copy(); p[1] = 100 * 10 / b26; p[2:] = 0.0
        return simulate(targets={"dPoil": p}, m=m)
    if key == "extdem10":
        p = nan.copy(); p[1] = 10.0; p[2:] = 0.0
        return simulate(targets={"dy_f": p}, m=m)
    if key == "rate_m200":
        p = nan.copy(); p[1:] = -2.0
        return simulate(targets={"CR": p}, m=m)
    if key == "stateinv1bn":
        p = nan.copy()
        for h, yr in enumerate(YEARS, start=1):
            p[h] = 100 * 1000 / float(g.get(yr, g.iloc[-1]))
        p[len(YEARS) + 1:] = p[len(YEARS)]
        return simulate(targets={"gcap_y": p}, m=m)
    raise KeyError(key)


def fr1_multipliers() -> pd.DataFrame:
    m = pd.read_csv(config.MICRO_FILES["fr1_multipliers"])
    return m.rename(columns={m.columns[0]: "shock", m.columns[1]: "year"})


def fr1_oscillation(m: pd.DataFrame | None = None) -> pd.DataFrame:
    """Sign-alternation check of the FR1 step responses (the balance_n bug being fixed upstream)."""
    m = fr1_multipliers() if m is None else m
    rows = []
    for shock, g in m.groupby("shock", sort=False):
        for col in ("balance_n", "rgdpnon", "infl"):
            v = g.sort_values("year")[col].to_numpy(float)
            d = np.diff(v)
            flips_v = int(np.sum(np.sign(v[1:]) * np.sign(v[:-1]) < 0))
            flips_d = int(np.sum(np.sign(d[1:]) * np.sign(d[:-1]) < 0))
            rows.append({"shock": shock, "column": col, "values": " ".join(f"{x:.3g}" for x in v),
                         "sign_flips": flips_v, "diff_flips": flips_d,
                         "oscillates": bool(flips_v >= 2 or flips_d >= 3)})
    return pd.DataFrame(rows)


_FR13_SCRIPT = r'''
import sys, pandas as pd
sys.path.insert(0, sys.argv[1]); out = sys.argv[2]
import ministry_spec as ms, os
fl_path = os.path.join(ms.OUT, "forecast_long.csv")
def rows(res, tag):
    r = ms.forecast_rows(res)[["series_code", "year", "value"]]; r["run"] = tag; return r
res = [rows(ms.run_scenario(), "base")]
a = pd.read_csv(ms.ASSUMPTIONS); a.loc[a.assumption_key == "brent_usd", "value"] += 10
a.to_csv(out + "/fr13_a_brent10.csv", index=False)
f = pd.read_csv(fl_path, float_precision="round_trip")
k = (f.series_code == "brent_usd") & (f.source == "ours") & (f.kind == "forecast")
f.loc[k, "value"] += 10; f.to_csv(out + "/fr13_fl_brent10.csv", index=False)
res.append(rows(ms.run_scenario(assumptions_path=out + "/fr13_a_brent10.csv",
                                forecast_path=out + "/fr13_fl_brent10.csv"), "brent10"))
a = pd.read_csv(ms.ASSUMPTIONS)
a.loc[(a.assumption_key == "partner_gdp_realg") & (a.year == 2026), "value"] += 1
a.to_csv(out + "/fr13_a_extdem10.csv", index=False)
res.append(rows(ms.run_scenario(assumptions_path=out + "/fr13_a_extdem10.csv"), "extdem10"))
pd.concat(res).to_csv(out + "/fr13_runs.csv", index=False)
'''


def oxlon_fr13_runs() -> pd.DataFrame | None:
    """OxLon FR13 (`ministry_spec`, the Ministry's 92-equation catalogue re-solved by OxLon)
    under Brent +10 and partner growth +1 pp in 2026 (scaled ×10) — run in a subprocess (module-name
    isolation), all shocked inputs written under RU/work/caem, nothing inside Macro_OxLon."""
    import subprocess
    import sys
    if not (OXLON_SRC / "ministry_spec.py").exists():
        return None
    WORK.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-c", _FR13_SCRIPT, str(OXLON_SRC), str(WORK)],
                       capture_output=True, text=True, timeout=240)
    if r.returncode != 0 or not (WORK / "fr13_runs.csv").exists():
        return None
    d = pd.read_csv(WORK / "fr13_runs.csv")
    p = d.pivot_table(index=["series_code", "year"], columns="run", values="value").reset_index()
    return p


def transmission_comparison(run_fr13: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """C5: CAEM AZE Model vs MicroUnit FR1 step responses vs OxLon sensitivities for comparable
    shocks. Returns (comparison, fr1 oscillation check)."""
    m = load()
    ix = m["ix"]
    ox = _oxlon_baseline()
    fr1 = fr1_multipliers()
    osc = fr1_oscillation(fr1)
    mf = pd.read_csv(config.MICRO_FILES["fr1_forecast"])
    mf = mf[mf["scenario"] == "Baseline"].set_index(mf.columns[0])
    gdp_n = mf["gdp_n"].reindex(YEARS)
    rows = []

    def add(key, concept, year, h, model, value, var, note=""):
        lab, unit = CONCEPTS[concept][0], CONCEPTS[concept][1]
        rows.append({"shock_key": key, "shock_az": COMPARABLE[key][0], "concept": concept,
                     "concept_az": lab, "unit": unit, "year": year, "horizon": h, "model": model,
                     "value": None if value is None or not np.isfinite(value) else round(float(value), 4),
                     "source_var": var, "note_az": note})

    for key, (_, fr1_name) in COMPARABLE.items():
        y = _caem_paths(key, ox)
        cum_ncom = np.cumsum(y[ix["dy_ncom"]])
        g = fr1[fr1["shock"] == fr1_name].set_index("year")
        oscl = set(osc[(osc.shock == fr1_name) & osc.oscillates]["column"])
        for h, yr in enumerate(YEARS, start=1):
            for concept, (_, _, cvar, fvar) in CONCEPTS.items():
                cv = cum_ncom[h] if cvar == "cum:dy_ncom" else y[ix[cvar], h]
                add(key, concept, yr, h, "CAEM AZE Model (Nazirlik — müqayisə)", cv, cvar, LABEL_AZ)
                if fvar is None or g.empty:
                    add(key, concept, yr, h, "MikroUnit FR1", None, "-", "FR1-də bu dəyişən yoxdur")
                    continue
                if fvar == "balance_pct":
                    v = g["balance_n"].get(yr, np.nan) / gdp_n.get(yr, np.nan) * 100
                    note = "balance_n (mln AZN, baza ilə fərq) / FR1 baza gdp_n"
                    src = "balance_n"
                else:
                    v, note, src = g[fvar].get(yr, np.nan), "", fvar
                if src in oscl:
                    note = (note + "; " if note else "") + "XƏBƏRDARLIQ: FR1 cavabı işarəsini dəyişir (salınım)"
                add(key, concept, yr, h, "MikroUnit FR1", v, src, note)
    # OxLon FR12 partial: current account under the Brent lo80/hi80 paths (published rows)
    piv = ox[ox.year.isin(YEARS)].pivot_table(index="year", columns="series_code", values="value")
    br = ox[(ox.series_code == "brent_usd") & ox.year.isin(YEARS)].set_index("year")
    fx = piv.get("fx_usd_azn_avg", pd.Series(1.7, index=YEARS)).fillna(1.7)
    for h, yr in enumerate(YEARS, start=1):
        try:
            slope = ((piv.at[yr, "current_account_brent_hi80"] - piv.at[yr, "current_account_brent_lo80"])
                     / (br.at[yr, "hi80"] - br.at[yr, "lo80"]))
            pct = 10 * slope / (piv.at[yr, "gdp_nom"] / fx.get(yr, 1.7)) * 100
        except (KeyError, ZeroDivisionError):
            continue
        rows.append({"shock_key": "brent10", "shock_az": COMPARABLE["brent10"][0], "concept": "ca_pct",
                     "concept_az": "Cari hesab balansı", "unit": "ÜDM-ə %, baza ilə fərq", "year": yr,
                     "horizon": h, "model": "OxLon FR12 (Brent lo80/hi80 yollarından qismən həssaslıq)",
                     "value": round(float(pct), 4), "source_var": "current_account_brent_lo80/hi80",
                     "note_az": f"{10 * slope:,.0f} mln USD / +10 USD; CAEM AZE modelində cari hesab yoxdur"})
    if run_fr13:
        fr = oxlon_fr13_runs()
        if fr is not None:
            for key, code, concept in (("brent10", "cpi_infl", "cpi_infl"),
                                       ("extdem10", "exp_goods_nonoil", "nonoil_exports")):
                s = fr[fr.series_code == code].set_index("year")
                for h, yr in enumerate(YEARS, start=1):
                    if yr not in s.index or key not in s.columns:
                        continue
                    k = 10.0 if key == "extdem10" else 1.0     # +1 pp run scaled linearly to +10 %
                    d = (s.at[yr, key] - s.at[yr, "base"]) * k
                    v = d if concept == "cpi_infl" else d / s.at[yr, "base"] * 100
                    add(key, concept, yr, h, "OxLon FR13 (ministry_spec: Nazirliyin 92 tənliyi)", v, code,
                        "OxLon-un Nazirlik tənlik kataloqu" + ("; +1 pp (2026) işi ×10 xətti miqyaslanıb, "
                        "nominal ixrac (mln USD) faizlə" if k > 1 else ""))
    for key in ("rate_m200", "stateinv1bn"):
        add(key, "gdp_level", None, None, "OxLon", None, "-",
            "OxLon §15.5.1 modelində bu şok üçün kanal/həssaslıq dərc edilməyib")
    return pd.DataFrame(rows), osc

"""Engine `caem` — Ministry CAEM AZE Model (pinned copy, caem_core) as the explicit-tax/spending/
monetary comparison method (NFR2). Impact = simulate(policy) − simulate(no shock) (the AZE system
has a non-zero constant, CAEM finding CF: "Difference ≠ 0 with zero shocks"). Targets are imposed
RELATIVE to the no-shock path. Calibrated parameters -> tier D; deviations only (no levels)."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import caem_core as C, config, fiscal, registry, scenario as scn
from .engine_base import UNRELIABLE, Result, empty_result, row

ENGINE = "caem"
METHOD = "CAEM AZE Model (Nazirlik — müqayisə)"
YEARS = [config.CAEM_H0_YEAR + h for h in range(1, C.H + 1)]          # 2026..2037

OUT = [  # indicator, label_az, unit, state, transform(cum|lvl), group
    ("gdp_real", "Real ÜDM", "mln AZN 2015", "y", "lvl", "makro"),
    ("gdp_nonoil_real", "Real qeyri-neft (qeyri-əmtəə) ÜDM", "mln AZN 2015", "dy_ncom", "cum", "makro"),
    ("cpi", "İstehlak qiymətləri indeksi", "2015 = 100", "dP", "cum", "makro"),
    ("infl", "İnflyasiya (İQİ)", "%", "dP", "lvl", "makro"),
    ("unemp_rate", "İşsizlik səviyyəsi", "%", "UR", "lvl", "əmək"),
    ("employment", "Məşğulluq", "min nəfər", "le", "lvl", "əmək"),
    ("cons_real", "Real özəl istehlak", "mln AZN 2015", "c", "lvl", "makro"),
    ("exports_nonoil_real", "Qeyri-əmtəə ixracı (real)", "mln AZN 2015", "x", "lvl", "xarici"),
    ("imports_nonoil_real", "İdxal (real)", "mln AZN 2015", "m", "lvl", "xarici"),
    ("budget_balance_pct", "İlkin büdcə balansı (ÜDM-ə %)", "% ÜDM", "pb_y", "lvl", "fiskal"),
    ("debt_pct", "Dövlət borcu (ÜDM-ə %)", "% ÜDM", "d_y", "lvl", "fiskal"),
    ("revenue_pct", "Büdcə gəlirləri (ÜDM-ə %)", "% ÜDM", "rev_y", "lvl", "fiskal"),
    ("policy_rate", "Uçot dərəcəsi", "%", "CR", "lvl", "monetar"),
]
LEVEL_UNITS = {"mln AZN 2015", "2015 = 100", "min nəfər"}


def _gdp_share(vals):
    g = fiscal.gdp_nominal()
    return [100 * v / g[y] for v, y in zip(vals, YEARS)]


def _growth(levels):
    out, prev = [], 0.0
    for L in levels:
        out.append(100 * ((1 + L / 100) / (1 + prev / 100) - 1))
        prev = L
    return out


def build(s: dict):
    """-> (E increments 48x13, {state: Δ target path (13)}, handled, notes)"""
    m = C.load()
    ix = m["ix"]
    E = np.zeros((C.N_STATE, C.H + 1))
    E_sof = np.zeros((C.N_STATE, C.H + 1))          # cost shocks of SOFAZ-financed instruments
    T: dict[str, np.ndarray] = {}
    handled, notes = [], []
    p = registry.params("fiscal")

    def tgt(state, path):
        cur = T.setdefault(state, np.full(C.H + 1, np.nan))
        v = np.array([np.nan] + list(path), float)
        T[state] = np.where(np.isnan(cur), v, np.nan_to_num(cur) + np.nan_to_num(v))

    for it in s["instruments"]:
        rows = registry.adapters_for(ENGINE, it["instrument"])
        if rows.empty:
            continue
        handled.append(it["instrument"])
        size = scn.path(it, YEARS)
        cost = fiscal.direct_cost(it, YEARS)
        for _, a in rows.iterrows():
            name, k = registry.parse_transform(a["transform"])
            st = a["target_key"]
            if st not in ix:
                raise registry.ConfigError(f"CAEM: naməlum vəziyyət kodu '{st}' (adapters.csv)")
            if name == "target_gdp":
                tgt(st, [k * v for v in _gdp_share(cost)])
                if st == "gcap_y":
                    notes.append("CAEM-də kapital xərci (gcap_y) ilkin balansa (pb_y) və borca yazılmır — "
                                 "maliyyələşmə fərqi CAEM-də görünmür")
            elif name == "shock_gdp":
                sh = np.array([k * v for v in _gdp_share(cost)])
                E[ix[st], 1:] += sh
                if it.get("financing") == "sofaz":
                    E_sof[ix[st], 1:] += sh
            elif name == "target_rev":
                tgt(st, [-k * v for v in _gdp_share(cost)])
            elif name == "target":
                tgt(st, [k * v if y in it["years"] else np.nan for v, y in zip(size, YEARS)])
            elif name == "shock":
                E[ix[st], 1:] += np.array([k * v for v in size])
            elif name == "custom:caem_level_to_growth":
                tgt(st, _growth([k * v for v in size]))
            elif name == "custom:caem_price":
                w, ind = (("fuel_cpi_weight", "fuel_indirect") if it["instrument"] == "fuel_price"
                          else ("utility_cpi_weight", "utility_indirect"))
                lv = [k * p[w] * v / 100 * (1 + p[ind]) for v in size]
                E[ix[st], 1:] += np.array(_growth(lv))
            elif name == "custom:caem_export":
                xs = 100 * p["export_price_elasticity"] / (p["customs_base_gdp"] * 0.5)   # X_non ≈ ½ non-oil imports
                lv = [k * xs * v for v in _gdp_share(cost)]
                E[ix[st], 1:] += np.array(_growth(lv))
                notes.append("ixrac kanalı: qeyri-neft ixracı ≈ qeyri-neft idxalının yarısı (fərziyyə)")
            else:
                raise registry.ConfigError(f"CAEM: dəstəklənməyən transform '{name}'")
        fin = it.get("financing")
        if fin == "tax" and any(cost):
            tgt("otax_y", _gdp_share(cost))
            notes.append("maliyyələşmə: digər vergilərin artımı (otax_y)")
        elif fin == "reallocation" and any(cost):
            E[ix["pb_y"], 1:] += np.array(_gdp_share(cost))
            notes.append("maliyyələşmə: cari xərclərin azaldılması (pb_y)")
    return E, T, handled, notes, E_sof


def run(s: dict, ctx: dict | None = None) -> Result:
    t0 = time.perf_counter()
    E, T, handled, notes, E_sof = build(s)
    if not handled:
        return empty_result(ENGINE, "Ssenarinin alətləri üçün CAEM kanalı yoxdur")
    m = C.load()
    ix = m["ix"]
    y0 = C.simulate(m=m)
    targets = {k: y0[ix[k]] + v for k, v in T.items()}
    y1 = C.simulate(E, targets, m=m)
    d = y1 - y0
    sof = C.simulate(E_sof, m=m) - y0 if E_sof.any() else np.zeros_like(y0)
    if E_sof.any():
        notes.append("ARDNF maliyyələşməsi: transfert xərc şokunun balans və borc təsirini aradan qaldırır")
    outs = [ix[o[3]] for o in OUT if o[3] not in T]
    if np.nanmax(np.abs(d[outs])) < 1e-9:
        return empty_result(ENGINE, "CAEM-də bu alətin şoku heç bir dəyişənə ötürülmür (məs. dS: B2 sütunu "
                                    "sıfırdır) — CAEM bu ssenari üçün tətbiq edilmir")
    note = "; ".join([C.LABEL_AZ, "kalibrlənmiş parametrlər, yalnız baza ilə fərq"] + notes)
    tax = any(registry.instrument(i)["family"] == "vergi" for i in handled)
    warn = []
    if tax:
        warn.append(f"{UNRELIABLE}: CAEM-də vergi şokunun fiskal nəticəsi (balans, borc, gəlir) etibarsızdır — vergi "
                    "endirimi balansı yaxşılaşdırır, borc isə artır (işarə uyğunsuzluğu; gəlir dəyişməsi xərclərə "
                    "ötürülür). Fiskal KPI-lardan çıxarılıb; makro nəticələr yalnız müqayisə üçündür")
    fiscal_note = note + ("; " + warn[0] if warn else "")
    rows = []
    for ind, lab, unit, st, tr, grp in OUT:
        nt = fiscal_note if grp == "fiskal" else note
        v = d[ix[st], 1:]
        if tr == "cum":
            v = np.cumsum(v)
        if st in ("pb_y", "d_y"):
            v = v - sof[ix[st], 1:]
        for y, x in zip(YEARS, v):
            if y > config.LONG_END:
                continue
            x = float(x)
            if unit in LEVEL_UNITS:
                rows.append(row(ind, lab, unit, y, np.nan, np.nan, METHOD, "D", grp, nt, delta=np.nan, delta_pct=x))
            else:
                rows.append(row(ind, lab, unit, y, np.nan, np.nan, METHOD, "D", grp, nt, delta=x, delta_pct=x))
    cost = np.sum([fiscal.direct_cost(it, YEARS) for it in s["instruments"] if it["instrument"] in handled], axis=0)
    for y, c in zip(YEARS, cost):
        if y <= config.LONG_END:
            rows.append(row("fiscal_cost", "Birbaşa fiskal xərc / gəlir itkisi (ex ante, brutto — geri əlaqədən əvvəl)", "mln AZN", y, 0.0, float(c),
                            METHOD, "D", "fiskal", "statik, geri əlaqədən əvvəl (fiscal_params.csv)"))
    meta = {"vintage": {"caem_md5": C.vintage_status()["copy_md5"]}, "handled": handled,
            "runtime_s": round(time.perf_counter() - t0, 2), "assumptions": notes, "warnings": warn,
            "targets": sorted(T), "zero_shock_max": float(np.nanmax(np.abs(y0)))}
    return Result(ENGINE, pd.DataFrame(rows), meta)

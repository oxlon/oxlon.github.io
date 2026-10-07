"""Build the SYNTHETIC household file (2024 base) and the 2018 back-cast file used for the
NFR1 retrospective test; write calibration JSON, template, column map and the in-sample
calibration fit report (V_microsim_calibration_<year>.csv).

    python3 -m policyunit.ms_build          # ~1 min (2 calibrations)"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config, hh_data
from . import ms_calib as C
from . import ms_metrics as M
from . import ms_policy as MP
from . import ms_targets as MT
from . import synth_households as SH
from .taxben import Params

WORK = config.ROOT / "work" / "microsim"
N_HH, SEED = 12000, 20241


def _json(o):
    if isinstance(o, dict):
        return {str(k): _json(v) for k, v in o.items()}
    if isinstance(o, (np.floating, np.integer)):
        return float(o)
    return o


def fit_report(p, cal, T, year):
    pp = MP.prepare(p)
    hh, per = MP.compute(pp, cal, year, Params())
    w, n = hh["w"].to_numpy(), hh["n"].to_numpy()
    pw = w * n
    rows = []
    add = lambda grp, ind, tgt, mod, kind, note="": rows.append(
        {"year": year, "group": grp, "indicator": ind, "target": tgt, "model": mod,
         "dev": mod - tgt if np.isfinite(tgt) else np.nan,
         "dev_pct": 100 * (mod - tgt) / tgt if np.isfinite(tgt) and tgt else np.nan,
         "type": kind, "note_az": note})
    X, tg, keys = C.design(pp, T)
    for k, t, m in zip(keys, tg, X.T @ w):
        add("say (min nəfər)", k, t / 1e3, m / 1e3, "kalibrləmə hədəfi (sərt)")
    for s, t in T["hbs_pc"].items():
        m = np.sum(w * hh["y_total" if s == "total" else f"y_{s}"]) / pw.sum()
        add("gəlir mənbəyi (AZN/nəfər/ay)", s, t, m, "kalibrləmə hədəfi (amil)")
    dec = M.hh_deciles(hh["y_pc"].to_numpy(), w)
    dm = M.decile_means(hh["y_pc"].to_numpy(), n, w, dec)
    tsh = T["inc_dec"] * MT.person_profile(T["inc_dec"], T["hbs_pc"]["total"])
    msh = M.decile_shares(hh["y_pc"].to_numpy(), n, w, dec)
    for d in range(10):
        add("gəlir desili (AZN/nəfər/ay)", f"D{d + 1}", T["inc_dec"][d], dm[d], "kalibrləmə hədəfi")
        add("gəlir desilinin payı (%)", f"D{d + 1}", 100 * tsh[d] / tsh.sum(), 100 * msh[d],
            "kalibrləmə hədəfi (törəmə)")
    for src in C.SRC_DEC:
        md = M.decile_means((hh[f"y_{src}"] / n).to_numpy(), n, w, dec)
        for d in range(10):
            add(f"{src} desil üzrə (AZN/nəfər/ay)", f"D{d + 1}",
                T["inc_dec_tab"][src].iloc[d], md[d], "yumşaq hədəf")
    cdec = M.hh_deciles(hh["c_pc"].to_numpy(), w)
    cm = M.decile_means(hh["c_pc"].to_numpy(), n, w, cdec)
    for d in range(10):
        add("istehlak desili (AZN/nəfər/ay)", f"D{d + 1}", T["cons_dec"][d], cm[d], "kalibrləmə hədəfi")
    add("istehlak", "orta (AZN/nəfər/ay)", T["cons_pc"], np.sum(pw * hh["c_pc"]) / pw.sum(),
        "yumşaq (desil profili ilə)")
    S = M.summary(hh, {"dsk": (T["pov_line"], "c")}, cal["kappa"])
    add("yoxsulluq (%)", "DSK səviyyəsi (kappa ilə)", T["pov_rate"], S["pov_headcount_dsk"],
        "kalibrləmə hədəfi (kappa)", f"kappa = {cal['kappa']:.3f}")
    raw = M.fgt(hh["c_pc"].to_numpy(), pw, T["pov_line"], 0) * 100
    add("yoxsulluq (%)", "adambaşına istehlak < xətt (kappa olmadan)", T["pov_rate"], raw,
        "diaqnostika", "dərc olunmuş desil cədvəlləri ilə rəsmi səviyyə uyğun deyil")
    for u, nm in ((1, "pov_urban"), (0, "pov_rural")):
        m = hh["urban"].to_numpy() == u
        add("yoxsulluq (%)", nm, T[nm], 100 * M.fgt(hh["c_pc"].to_numpy()[m] * cal["kappa"], pw[m],
                                                     T["pov_line"], 0), "yoxlama (hədəf deyil)")
    rec = hh["utsy"].to_numpy() > 0
    add("ÜSY", "alan şəxslər (min)", T["utsy_members"] / 1e3, pw[rec].sum() / 1e3, "hədəf")
    if year == 2024:
        add("ÜSY", "ailələr (min)", 61.5, w[rec].sum() / 1e3, "yoxlama")
        add("ÜSY", "orta məbləğ (AZN/nəfər)", 109.6, np.sum(w * hh["utsy"]) / pw[rec].sum(), "yoxlama")
        bands = pd.read_csv(MT.TARGETS / "income_bands_persons_2024.csv")
        add("gəlir intervalı (DSK 28)", "şəxslər < 270 AZN (%)", bands[bands.hi <= 270].pct_all.sum(),
            100 * M.fgt(hh["y_pc"].to_numpy(), pw, 270.05, 0), "yoxlama (hədəf deyil)")
    pe = pp.assign(g=per["gross"], w=pp["weight"])
    e = pe[pe.status == "employee"]
    add("əmək haqqı (AZN/ay)", "orta (muzdlu)", T["wage_avg"], np.average(e.g, weights=e.w), "yoxlama")
    for o, k in (("state", "wage_state"), ("nonstate", "wage_nonstate")):
        x = e[e.ownership == o]
        add("əmək haqqı (AZN/ay)", k, T[k], np.average(x.g, weights=x.w), "yoxlama")
    add("Gini", "gəlir (adambaşına; şəxslər)", np.nan, 100 * S["gini_income"], "nəticə",
        "DSK Gini dərc etmir; desil cədvəlindən aşağı sərhəd ayrıca")
    add("Gini", "istehlak (adambaşına; şəxslər)", np.nan, 100 * S["gini_cons"], "nəticə")
    prof = MT.person_profile(T["inc_dec"], T["hbs_pc"]["total"])
    add("Gini", "DSK desil cədvəlindən (qrup daxili bərabərlik; aşağı sərhəd)", np.nan,
        100 * M.gini(T["inc_dec"], prof), "müqayisə")
    r = w / np.mean(w)
    add("çəkilər", "Kish dizayn effekti", np.nan, float(np.mean(r ** 2)), "diaqnostika")
    return pd.DataFrame(rows)


def build(year=2024, n_hh=N_HH, seed=SEED, log=print, p_takeup=None, takeup_gamma=None):
    p = SH.generate(n_hh, seed, year)
    p, cal, T = C.calibrate(p, year, p_takeup=p_takeup, takeup_gamma=takeup_gamma, log=log)
    cal["n_households"], cal["n_persons"], cal["seed"] = n_hh, len(p), seed
    cal["data_status"] = SH.WATERMARK
    return p, cal, T


def write_synthetic(p, cal):
    hh_data.HH_DIR.mkdir(parents=True, exist_ok=True)
    cols = [c for c, *_ in hh_data.COLUMNS if c in p.columns]
    p = p[cols].copy()
    p["weight"] = p["weight"].round(4)
    p.to_csv(hh_data.SYNTH_CSV, index=False)
    hh_data.CAL_JSON.write_text(json.dumps(_json(cal), ensure_ascii=False, indent=1))
    with pd.ExcelWriter(hh_data.SYNTH_CSV.with_suffix(".xlsx")) as xw:
        pd.DataFrame({"README": [SH.WATERMARK, "Sxem: PU_households_column_map.csv",
                                 "Mənbə: policyunit/ms_build.py (seed %d)" % cal["seed"]]}
                     ).to_excel(xw, sheet_name="README", index=False)
        p.to_excel(xw, sheet_name="data", index=False)
    hh_data.write_column_map()
    t = p[p.hh_id == p.hh_id.iloc[0]].copy()
    t["data_status"] = ""
    t.to_csv(hh_data.TEMPLATE_CSV, index=False)
    t.to_excel(hh_data.TEMPLATE_CSV.with_suffix(".xlsx"), sheet_name="data", index=False)


def main():
    from . import catalog
    WORK.mkdir(parents=True, exist_ok=True)
    p24, cal24, T24 = build(2024)
    write_synthetic(p24, cal24)
    fr = [fit_report(p24, cal24, T24, 2024)]
    p18, cal18, T18 = build(2018, p_takeup=cal24["p_takeup"], takeup_gamma=cal24["takeup_gamma"])
    p18.to_csv(WORK / "PU_households_SYNTHETIC_2018.csv", index=False)
    (WORK / "PU_households_calibration_2018.json").write_text(json.dumps(_json(cal18), indent=1))
    fr.append(fit_report(p18, cal18, T18, 2018))
    for f, y in zip(fr, (2024, 2018)):
        catalog.write_csv(f, f"V_microsim_calibration_{y}.csv", "microsim",
                          f"SİNTETİK — mikrosimulyasiya bazasının {y} DSK hədəflərinə kalibrləmə "
                          "uyğunluğu (IN-SAMPLE)")
    return fr


if __name__ == "__main__":
    main()

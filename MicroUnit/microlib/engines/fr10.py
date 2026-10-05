"""FR10 scenario engine — enterprises' financial condition, efficiency and market shares (Layer A).

Re-implements the FR10 notebook's forecast solver (Part 14, `core`) for one path, from the exported state
output/engine/FR10_state.json (+ .npz). Contract section B:
    inputs()                                   editable inputs (FR1 driver paths, FR4 employment indices, coefficients, levers)
    run(overrides, scenario, upstream=None)    {"series": {fr10:<id>: {year: value}}, "meta", "warnings"}
    selftest()                                 run({}) reproduces output/FR10_forecast_tidy.csv in every scenario (rel. 1e-8)
Upstream: FR1 (series 'fr1:<code>' for the FR1 drivers); FR4 employment indices are read from the state (FR4 CSV).
Layer B (firm level) is not part of the engine: it runs on the firm panel inside the notebook.
"""
from __future__ import annotations

import copy
import os
import time

import numpy as np
import pandas as pd

from . import base as B

MODULE = "FR10"
_S = None


def _st():
    global _S
    if _S is None:
        _S = B.load_state(MODULE)
    return _S


def inputs():
    return copy.deepcopy(_st()["inputs"])


def _sm(z):
    e = np.exp(z - z.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def _alloc(s_base, dr, beta, w):
    """Notebook `alloc`: softmax shares from 2025 shares and relative-index changes; w = weight of the pooled model."""
    lz = np.log(s_base)
    C = _sm(lz + 0 * dr)
    if w == 0:
        return C
    W = _sm(lz + beta * dr)
    if w == 1:
        return W
    return w * W + (1 - w) * C


def _shrink(raw_b, raw_se, w, units, ref, kappa):
    """Notebook ShareSystem._shrink (precision-weighted empirical Bayes towards the share-weighted mean), one driver."""
    b = pd.Series(raw_b, index=units, dtype=float)
    se = pd.Series(raw_se, index=units, dtype=float)
    w = pd.Series(w, index=units, dtype=float)
    se[ref] = float((se.drop(ref) * w.drop(ref)).sum() / w.drop(ref).sum())
    d = b - float((w * b).sum())
    tau2 = max(float(d.var(ddof=1) - (se ** 2).mean()), 1e-4)
    Bk = (kappa * se ** 2 / (kappa * se ** 2 + tau2)) if np.isfinite(kappa) else pd.Series(1.0, index=units)
    ds = (1 - Bk) * d
    return (ds - ds[ref]).to_numpy(float), (np.sqrt(np.maximum(1 - Bk, 0)) * se).to_numpy(float)


def _drivers(st, ov):
    """FR1 driver arrays (1, 6): 2025 actual (FR1 history) then the 2026-2030 path."""
    D = {}
    for v in st["dvars"]:
        if v == "emp":
            continue
        D[v] = np.array([[st["f1h25"][v]] + list(ov["exogenous"][f"fr1_{v}"])], float)
    for s, v in st["secv"].items():
        D[f"va_{v}_n"] = D[f"rva_{v}"] * D[f"p_{v}"]
    emp_idx = {s: np.array([[1.0] + list(ov["exogenous"][f"fr4_hired_{s}"])], float) for s in st["secv"]}
    return D, emp_idx


def _core(st, D, emp_idx, beta, w_combo, capf, eps_oil, e08, e07, regb, margin="labour_share", ls_shift=0.0, q08="neutral"):
    """Faithful one-path copy of the notebook's `core` (Part 14.1). Arrays are (1, T) or (1, T, K)."""
    YRS, BC, MAN = st["years"], st["bcodes"], st["manuf"]
    T_ = len(YRS)
    t0 = (np.arange(T_) == 0)[None, :]
    secv, mr = st["secv"], st["mining_rules"]
    secgo = {s: st["sec_go25"][s] * D[f"va_{v}_n"] / D[f"va_{v}_n"][:, :1] for s, v in secv.items()}
    pidx = {s: D[f"p_{v}"] / D[f"p_{v}"][:, :1] for s, v in secv.items()}
    nom = np.zeros((1, T_, len(BC)))
    real = np.zeros_like(nom)
    J = {b: BC.index(b) for b in BC}
    oilidx = D["oil_exp_price"] / D["oil_exp_price"][:, :1]
    for b in st["oil"]:
        real[..., J[b]] = st["q25"][b] * np.where(t0, 1.0, capf[b])
        nom[..., J[b]] = real[..., J[b]] * st["pdef25"][b] * oilidx ** eps_oil[b]
    rem = secgo["C"] - nom[..., [J[b] for b in st["oil"]]].sum(-1)
    rem = np.maximum(rem, 0.01 * secgo["C"])
    NO = st["nonoil"]
    rel = {b: (np.log(D[st["link"][b]]) - np.log(D[st["sectot"]["C"]])) if b in st["link"] else 0.0 * np.log(D[st["sectot"]["C"]])
           for b in NO}
    dr = np.stack([rel[b] - rel[b][:, :1] for b in NO], -1)
    W = _alloc(np.asarray(st["s25C"], float), dr, beta, w_combo)
    ic = [J[b] for b in NO]
    nom[..., ic] = W * rem[..., None]
    real[..., ic] = nom[..., ic] / (np.array([st["pdef25"][b] for b in NO]) * pidx["C"][..., None])
    ix = lambda v: D[v] / D[v][:, :1]  # noqa: E731
    j6, j7, j8, j9 = (J[b] for b in ["06", "07", "08", "09"])
    if q08 == "neutral":                       # v2 baseline: held at the 2023-25 average (neutral null)
        real[..., j8] = st["q25"]["08"] * np.where(t0, 1.0, mr["q08_level_factor"]) * np.ones_like(ix("rva_con"))
    else:                                      # lever: unit-elasticity (editable) link to FR1 construction VA
        real[..., j8] = st["q25"]["08"] * ix("rva_con") ** e08
    nom[..., j8] = real[..., j8] * st["pdef25"]["08"] * ix("p_con")
    r7 = mr["rule07"]
    if r7.startswith("neutral"):
        q7 = np.where(t0, 1.0, mr["q07_level_factor"])
    else:
        q7 = ix(st["d07"])
        q7 = q7 if e07 == 1.0 else q7 ** e07
    real[..., j7] = st["q25"]["07"] * q7 * np.ones_like(ix("p_gdp"))
    nom[..., j7] = real[..., j7] * st["pdef25"]["07"] * ix("p_gdp")
    for j, b in [(j6, "06"), (j9, "09")]:
        real[..., j] = st["q25"][b] * ix("rgdpoil")
    resid = secgo["B"] - nom[..., j7] - nom[..., j8]
    resid = np.maximum(resid, 0.05 * secgo["B"])
    nom[..., j6] = resid * mr["oil_split_06"]
    nom[..., j9] = resid * (1 - mr["oil_split_06"])
    for b, s in [("35", "D"), ("36", "E")]:
        nom[..., J[b]] = secgo[s]
        real[..., J[b]] = nom[..., J[b]] / (st["pdef25"][b] * pidx[s])
    rg = st["reg"]
    units = st["reg_names"]
    xs = rg["xs"]
    LO25 = np.asarray(rg["lo25"], float)
    mix = np.log(D["va_min_n"] / D["va_man_n"])
    mix = mix - mix[:, :1] + rg["x2_25"]
    XR = np.stack([np.log(D["rva_man"]), mix], -1)
    if xs:
        br = np.broadcast_to(regb, (1,) + regb.shape)
        ixr = [{"x1": 0, "x2": 1}[x] for x in xs]
        z = LO25[None, None, :] + np.einsum("rtx,rkx->rtk", XR[..., ixr] - XR[:, :1, ixr], br)
    else:
        z = np.broadcast_to(LO25, (1, T_, len(units))).copy()
    out = {"reg_sh": _sm(z)}
    eidx = {s: emp_idx[s] for s in secv}
    emp = np.stack([st["emp25"][b] * eidx[st["bsec"][b]] for b in BC], -1)
    widx = D["wage"] / D["wage"][:, :1]
    out.update(nom=nom, real=real, emp=emp, lp=real / emp * 1e3, sec_go=np.stack([secgo[s] for s in secv], -1))
    out["wage"] = np.array([st["wage25"][b] for b in BC])[None, None, :] * widx[..., None]
    out["sh_ind"] = nom / nom.sum(-1, keepdims=True)
    mi = [J[b] for b in MAN]
    out["sh_man"] = nom[..., mi] / nom[..., mi].sum(-1, keepdims=True)
    out["ns_share"] = (nom * np.asarray(st["ns25"], float)).sum(-1) / nom.sum(-1)
    gs, ls, vas, ces, ots = [], [], [], [], []
    for s, v in secv.items():
        va = st["inc25"][s]["VA"] * D[f"va_{v}_n"] / D[f"va_{v}_n"][:, :1]
        ce25 = st["inc25"][s]["CE"]
        if margin == "labour_share":
            ce = np.where(t0, ce25, (st["ls_avg"][s] + ls_shift / 100.0) * va) if ls_shift else np.where(t0, ce25, st["ls_avg"][s] * va)
        elif margin == "fr1_wage":
            ce = ce25 * widx * eidx[s]
        else:
            ce = ce25 * pidx[s] * eidx[s]
        otp = st["otp_sh"][s] * va
        gs.append((va - ce - otp) / va * 100)
        ls.append(ce / va * 100)
        vas.append(va)
        ces.append(ce)
        ots.append(otp)
    out["sec_gos"], out["sec_ls"] = np.stack(gs, -1), np.stack(ls, -1)
    out["sec_va"], out["sec_ce"], out["sec_otp"] = np.stack(vas, -1), np.stack(ces, -1), np.stack(ots, -1)
    na_go = np.array([st["na_go25"][b] for b in MAN]) * nom[..., mi] / nom[:, :1, mi]
    va_b = na_go * np.array([st["vago25"][b] for b in MAN])
    if margin == "labour_share":
        wbva = np.array([st["wbva_avg"][b] for b in MAN]) + (ls_shift / 100.0 if ls_shift else 0.0)
        wb = np.where(t0[..., None], np.array([st["wbill25"][b] for b in MAN]), wbva * va_b)
    else:
        wi = widx if margin == "fr1_wage" else pidx["C"]
        wb = np.array([st["wbill25"][b] for b in MAN]) * wi[..., None] * eidx["C"][..., None]
    out["gosp"] = (va_b - wb) / na_go * 100
    return out


_BR = {"output_nominal_mn_AZN": ("nom", 1.0), "output_real_mn_AZN_2015": ("real", 1.0), "share_of_industry": ("sh_ind", 100.0),
       "share_of_manufacturing": ("sh_man", 100.0), "employees": ("emp", 1.0), "lp_thsd_AZN_2015": ("lp", 1.0),
       "wage_AZN_month": ("wage", 1.0), "gos_proxy_margin_pct": ("gosp", 1.0)}
_SEC = {"VA": "sec_va", "CE": "sec_ce", "OTP": "sec_otp", "GOS_share_VA": "sec_gos", "labour_share_VA": "sec_ls"}


def _series(st, o):
    """Component id -> {year: value} for 2025-2030 (2025 = anchor year, equal to the actual)."""
    YRS, BC, MAN = st["years"], st["bcodes"], st["manuf"]
    col = {b: i for i, b in enumerate(BC)}
    colm = {b: i for i, b in enumerate(MAN)}
    secs = list(st["secv"])
    reg = {st["reg"]["slugs"][k]: i for i, k in enumerate(st["reg_names"])}
    nomsum = o["nom"][0].sum(-1)
    reg_go = o["reg_sh"][0] * (st["reg"]["go25_sum"] * nomsum / nomsum[0])[:, None]
    prod = {p["id"]: p for p in st["products"]}
    out = {}
    for cid in st["components"]:
        parts = cid.split(":")
        code = parts[1]
        arg = parts[2] if len(parts) > 2 else None
        if code in _BR:
            key, sc = _BR[code]
            v = o[key][0][:, (colm if key in ("sh_man", "gosp") else col)[arg]] * sc
        elif code.startswith("sec_"):
            c = code[4:]
            j = secs.index(arg)
            if c == "output":
                v = o["sec_go"][0][:, j]
            elif c == "GOS":
                v = o["sec_va"][0][:, j] - o["sec_ce"][0][:, j] - o["sec_otp"][0][:, j]
            else:
                v = o[_SEC[c]][0][:, j]
        elif code == "ind_output":
            v = nomsum
        elif code == "reg_share":
            v = o["reg_sh"][0][:, reg[arg]] * 100.0
        elif code == "reg_output":
            v = reg_go[:, reg[arg]]
        elif code == "hhi_man":
            v = (o["sh_man"][0] ** 2).sum(-1) * 1e4
        elif code == "nonstate_share":
            v = o["ns_share"][0] * 100.0
        elif code == "prod":
            p = prod[cid]
            v = o["real"][0][:, col[p["branch"]]] * p["intensity"]
        else:
            raise KeyError(cid)
        out[cid] = pd.Series(np.asarray(v, float), index=YRS)
    return out


def _with_upstream(cat, scenario, upstream, warnings):
    """Replace the FR1 driver baselines of `scenario` by an upstream FR1 engine result (series 'fr1:<code>')."""
    fr1 = (upstream or {}).get("FR1")
    if not fr1:
        return cat
    ser = fr1.get("series", {})
    cat = copy.deepcopy(cat)
    used = []
    for e in cat["exogenous"]:
        if not e["id"].startswith("fr1_"):
            continue
        sid = "fr1:" + e["id"][4:]
        if sid in ser:
            d = ser[sid]
            vals = [d.get(str(y), d.get(y)) for y in e["years"]]
            if all(v is not None and np.isfinite(v) for v in vals):
                e["baseline"] = dict(e["baseline"], **{scenario: [float(v) for v in vals]})
                used.append(sid)
    if not used:
        warnings.append("FR1 yuxarı axın nəticəsində FR10 sürücüləri tapılmadı — FR1 CSV baza yolları istifadə olunur")
    return cat


def run(overrides=None, scenario="Baseline", upstream=None):
    t0 = time.perf_counter()
    st = _st()
    W = []
    cat = _with_upstream(st["inputs"], scenario, upstream, W)
    ov = B.apply_overrides(cat, overrides, scenario)
    W += ov["warnings"]
    lev, cf = ov["levers"], ov["coefficients"]
    D, emp_idx = _drivers(st, ov)
    capf = dict(st["capf"])
    for b in st["oil"]:
        capf[b] = float(lev.get(f"cap_factor_{b}", capf[b]))
    eps = dict(st["eps_oil"])
    for b in st["oil"]:
        eps[b] = cf.get(f"FR10.oil_{b}|dln_oil_azn", eps[b])
    beta = cf.get("FR10.pooled|x", st["beta"])
    e08 = cf.get("FR10.mining_08|x", st["mining_rules"]["e08"])
    e07 = next((v for k, v in cf.items() if k.startswith("FR10.mining_07|")), 1.0)
    rg = st["reg"]
    units = st["reg_names"]
    kap = float(lev.get("kappa_regions", rg["kappa"]))
    if rg["xs"]:
        if kap == rg["kappa"]:
            regb = np.array([rg["b"][k] for k in units], float)
        else:
            regb = np.column_stack([_shrink([rg["raw_b"][k][i] for k in units], [rg["raw_se"][k][i] for k in units], rg["w25"], units,
                                            rg["ref"], kap)[0] for i in range(len(rg["xs"]))])
            W.append(f"κ = {kap:g}: regional əmsallar büzülməmiş qiymətləndirmələrdən yenidən hesablanıb")
        for i, k in enumerate(units):
            key = f"FR10.reg_system|{rg['slugs'][k]}"
            if any(c == ("coefficients", key) for c in ov["changed"]):
                regb[i, 0] = cf[key]
    else:
        regb = np.zeros((len(units), 0))
    mode = lev.get("margin_mode", "labour_share")
    if mode not in ("labour_share", "fr1_wage", "product_wage"):
        W.append(f"margin_mode '{mode}' naməlumdur — labour_share istifadə olunur")
        mode = "labour_share"
    w_combo = float(lev.get("combo_weight", 1.0 if st["man_mode"] == "pooled" else 0.5))
    q08 = lev.get("quarrying_rule", "construction_link" if st["mining_rules"]["rule08"].startswith("unit") else "neutral")
    if q08 not in ("neutral", "construction_link"):
        W.append(f"quarrying_rule '{q08}' naməlumdur — neutral istifadə olunur")
        q08 = "neutral"
    if q08 == "neutral" and any(c == ("coefficients", "FR10.mining_08|x") for c in ov["changed"]):
        W.append("FR10.mining_08|x yalnız quarrying_rule = construction_link olduqda təsir edir")
    o = _core(st, D, emp_idx, beta, w_combo, capf, eps, e08, e07, regb, margin=mode,
              ls_shift=float(lev.get("labour_share_shift_pp", 0.0)), q08=q08)
    ser = _series(st, o)
    meta = {"module": MODULE, "scenario": scenario, "years": st["years"], "upstream": sorted((upstream or {}).keys()),
            "changed": [list(c) for c in ov["changed"]], "runtime_s": round(time.perf_counter() - t0, 4),
            "note_az": "A qatı: sahələr, bölmələr, regionlar, məhsullar; 2025 = faktiki (lövbər ili)"}
    return B.make_result(ser, meta=meta, warnings=W)


def to_long(res):
    rows = [(sid, int(float(y)), v) for sid, d in res["series"].items() for y, v in d.items()]
    return pd.DataFrame(rows, columns=["id", "year", "value"])


def selftest(tol=1e-8, root=None):
    st = _st()
    from .. import project_root
    csv = os.path.join(root or project_root(), "output", st["tidy_csv"])
    out, t_max = {}, 0.0
    for sc in st["scen"]:
        t0 = time.perf_counter()
        df = to_long(run({}, sc))
        t_max = max(t_max, time.perf_counter() - t0)
        df = df[df.year.isin(st["fc_years"])]
        out[sc] = B.selftest_compare(df, csv, ["value"], tol=tol, on=["id", "year"],
                                     csv_filter=lambda d, sc=sc: d[(d.scenario == sc) & d.is_forecast.astype(str).str.lower().eq("true")][["id", "year", "value"]])
    return {"ok": all(v["ok"] for v in out.values()), "detail": out, "max_runtime_s": round(t_max, 3)}

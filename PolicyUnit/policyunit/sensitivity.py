"""FR4 — global sensitivity of the POLICY EFFECT (not of the forecast): Monte Carlo + Sobol first-order
(S1) and total (ST) indices, Saltelli/Jansen estimators implemented in numpy.

Blocks
* micro — MicroUnit FR1/FR3/FR4 estimated coefficients ±SE (registries via `inputs()`; editable,
  SE > 0, constants excluded; independent truncated normal draws, |z| ≤ 2.5 — the registries carry no
  covariances). Each draw runs baseline AND scenario with the same coefficients (effect = scenario −
  baseline). Cost control: (1) one-sided OAT screening (+1 SE) of all candidates; (2) Saltelli on the
  TRUE chain for the top-K screened coefficients (others at their estimates), N base rows, parallel
  worker processes; dynamically unstable draws (explosive effect paths) are rejected and counted;
  (3) convergence: bootstrap 95 % CI half-width of the indices and N/2 vs N difference.
  (A quadratic emulator was tested and rejected: hold-out R² < 0 because the income–consumption
  loop E3×D1 is strongly non-linear.)
* io — Leontief domestic coefficients: column scale u_j ~ logN(0, 0.10) per IO sector + domestic/import
  split r ~ U(0.9, 1.1); true-model Saltelli (cheap).
* informality — calibrated minimum-wage disemployment channel (tier D; rule SE08 parameters).
Outputs: P4_sensitivity.csv (indices, top-3), P4_uncertainty_bands.csv (policy-effect bands)."""
from __future__ import annotations

import hashlib
import json
import pickle
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import config, microbridge as mb

Y = config.MICRO_YEARS
MODS = ("FR1", "FR3", "FR4")
TOP_K = 5
N_SOBOL = 4096                 # cheap blocks (IO, informality)
Z_CLIP = 2.5
SEED = 20261006
VERSION = "fr4-sens-3"
import os  # noqa: E402
N_MICRO = int(os.environ.get("POLICY_SOBOL_N", 160))      # Saltelli base rows for the chain block
WORKERS = int(os.environ.get("POLICY_FR4_WORKERS", max(0, min(8, (os.cpu_count() or 2) - 2))))
CACHE = config.WORK / "fr4_cache"
# indicator, module, series, kind (pct = Δ% of level, pp = Δ, ratio = Δ pp of GDP)
OUT = [("gdp_real", "FR1", "fr1:rgdp", "pct"), ("gdp_nonoil_real", "FR1", "fr1:rgdpnon", "pct"),
       ("cpi", "FR1", "fr1:cpi", "pct"), ("infl", "FR1", "fr1:infl", "pp"),
       ("employment_hired", "FR4", "fr4:hired:total", "pct"),
       ("budget_balance_pct", "FR1", "fr1:balance_n", "ratio"), ("debt_pct", "FR1", "fr1:debt_azn", "ratio")]
LABEL = {"gdp_real": "Real ÜDM (Δ %)", "gdp_nonoil_real": "Real qeyri-neft ÜDM (Δ %)", "cpi": "İQİ səviyyəsi (Δ %)",
         "infl": "İnflyasiya (Δ f.b.)", "employment_hired": "Muzdlu işçilər, FR4 (Δ %)",
         "budget_balance_pct": "Büdcə balansı (Δ f.b. ÜDM)", "debt_pct": "Dövlət borcu (Δ f.b. ÜDM)"}
HEAD = [("gdp_real", "orta"), ("infl", "qısa"), ("employment_hired", "orta"), ("budget_balance_pct", "orta")]


# ------------------------------------------------------------------ MicroUnit runner (FR1→FR3→FR4)
class Runner:
    def __init__(self):
        self.ch = mb.chain()
        self.base_cache = {}
        self.runs = 0

    def run(self, ov: dict, overlay=None) -> dict:
        out = {}
        for m in MODS:
            up = {u: out[u] for u in self.ch.UPSTREAM[m] if u in out}
            res = self.ch.load_engine(m).run(ov.get(m, {}), scenario="Baseline", upstream=up or None)
            if m == "FR1" and overlay is not None:
                import copy
                res = overlay(copy.deepcopy(res)) or res
            out[m] = res
        self.runs += 1
        bad = [w for m in MODS for w in out[m].get("warnings", []) if "naməlum" in w]
        if bad:
            raise RuntimeError("MikroUnit naməlum override: " + "; ".join(bad[:3]))
        return out

    @staticmethod
    def levels(res) -> np.ndarray:
        def s(mod, sid):
            d = res[mod]["series"].get(sid) or {}
            return np.array([float(d.get(str(y), np.nan)) for y in Y])
        gdp = s("FR1", "fr1:gdp_n")
        cols = []
        for ind, mod, sid, kind in OUT:
            v = s(mod, sid)
            cols.append(100 * v / gdp if kind == "ratio" else v)
        return np.concatenate(cols)

    @staticmethod
    def effect(lb, ls) -> np.ndarray:
        out = []
        for i, (_, _, _, kind) in enumerate(OUT):
            b, v = lb[i * len(Y):(i + 1) * len(Y)], ls[i * len(Y):(i + 1) * len(Y)]
            out.append(100 * (v / b - 1) if kind == "pct" else v - b)
        return np.concatenate(out)

    def eff(self, plan: dict, coefs: dict, overlay, base_key: str) -> np.ndarray:
        cov = {}
        for k, v in coefs.items():
            cov.setdefault(k.split(".")[0], {}).setdefault("coefficients", {})[k] = v
        bk = base_key + json.dumps(coefs, sort_keys=True)
        if bk not in self.base_cache:
            bov = {m: dict(cov.get(m, {})) for m in set(cov) | set(plan["struct_levers"])}
            for m, lv in plan["struct_levers"].items():
                bov[m]["levers"] = lv
            self.base_cache[bk] = self.levels(self.run(bov))
        sov = {m: dict(d) for m, d in plan["overrides"].items()}
        for m, d in cov.items():
            sov.setdefault(m, {})["coefficients"] = d["coefficients"]
        return self.effect(self.base_cache[bk], self.levels(self.run(sov, overlay)))


def candidates() -> list[dict]:
    out = []
    for m in MODS:
        for c in mb.catalogue(m)["coefficients"]:
            if c.get("editable") and c.get("se") and float(c["se"]) > 0 and c["name"] != "const":
                out.append({"key": f"{c['eq_id']}|{c['name']}", "value": float(c["value"]), "se": float(c["se"]),
                            "label_az": f"{c.get('eq_title_az') or c['eq_id']}: {c.get('label_az') or c['name']}"})
    return out


def head_index(start: int) -> list[tuple]:
    """(outcome id, indices into the effect vector) — horizon means of the HEAD outcomes."""
    out = []
    for ind, hz in HEAD:
        j = [i for i, o in enumerate(OUT) if o[0] == ind][0]
        yrs = [y for y in Y if (y - start <= 1 if hz == "qısa" else 2 <= y - start <= 3)] or [Y[-1]]
        out.append((f"{ind}:{hz}", [j * len(Y) + Y.index(y) for y in yrs]))
    return out


def heads(E: np.ndarray, hi) -> np.ndarray:
    E = np.atleast_2d(E)
    return np.column_stack([E[:, idx].mean(axis=1) for _, idx in hi])


def zdraw(rng, n, d) -> np.ndarray:
    lo = norm.cdf(-Z_CLIP)
    return norm.ppf(lo + (1 - 2 * lo) * rng.random((n, d)))


# ------------------------------------------------------------------ Sobol indices (numpy)
def indices(fA, fB, fAB):
    """S1 (Saltelli 2010) and ST (Jansen 1999); rows with non-finite values are dropped per factor."""
    okb = np.all(np.isfinite(fA), axis=1) & np.all(np.isfinite(fB), axis=1)
    V = np.var(np.vstack([fA[okb], fB[okb]]), axis=0) if okb.sum() > 2 else np.full(fA.shape[1], np.nan)
    V = np.where(V > 1e-18, V, np.nan)
    f0 = np.nanmean(np.vstack([fA[okb], fB[okb]]), axis=0) if okb.sum() > 2 else 0.0
    fA, fB, fAB = fA - f0, fB - f0, [f - f0 for f in fAB]           # centring: unbiased for large means
    S1, ST = [], []
    for f in fAB:
        ok = okb & np.all(np.isfinite(f), axis=1)
        if ok.sum() < 3:
            S1.append(np.full(fA.shape[1], np.nan))
            ST.append(np.full(fA.shape[1], np.nan))
            continue
        S1.append(np.mean(fB[ok] * (f[ok] - fA[ok]), axis=0) / V)
        ST.append(0.5 * np.mean((fA[ok] - f[ok]) ** 2, axis=0) / V)
    return np.array(S1), np.array(ST), V


def boot_ci(fA, fB, fAB, nb=200, seed=SEED):
    """Bootstrap 95 % CI half-width of S1/ST (max over factors) per outcome."""
    rng, N = np.random.default_rng(seed), fA.shape[0]
    S1s, STs = [], []
    for _ in range(nb):
        i = rng.integers(0, N, N)
        a, b = indices(fA[i], fB[i], [f[i] for f in fAB])[:2]
        S1s.append(a)
        STs.append(b)
    STs = np.array(STs)
    hw = lambda X: (np.nanpercentile(X, 97.5, axis=0) - np.nanpercentile(X, 2.5, axis=0)) / 2  # noqa: E731
    top0 = np.argmax(np.nan_to_num(indices(fA, fB, fAB)[1]), axis=0)
    stab = (np.argmax(np.nan_to_num(STs), axis=1) == top0[None, :]).mean(axis=0)
    p3 = np.argsort(-np.nan_to_num(indices(fA, fB, fAB)[1]), axis=0)[:3]
    b3 = np.argsort(-np.nan_to_num(STs), axis=1)[:, :3, :]
    stab3 = np.array([np.mean([set(b3[i, :, j]) == set(p3[:, j]) for i in range(len(STs))]) for j in range(fA.shape[1])])
    return np.nanmax(np.vstack([hw(np.array(S1s)), hw(STs)]), axis=0), stab, stab3


def saltelli(f, groups, sampler, N, rng):
    A, B = sampler(rng, N), sampler(rng, N)
    fAB = []
    for g in groups:
        AB = A.copy()
        AB[:, g] = B[:, g]
        fAB.append(f(AB))
    return indices(f(A), f(B), fAB)


def sobol_conv(f, groups, sampler, N=N_SOBOL, seed=SEED):
    """Cheap blocks: indices with N and 2N; convergence = max |Δ| over S1 and ST."""
    S1a, STa, _ = saltelli(f, groups, sampler, N, np.random.default_rng(seed))
    S1b, STb, V = saltelli(f, groups, sampler, 2 * N, np.random.default_rng(seed + 1))
    diff = np.nanmax(np.abs(np.concatenate([S1a - S1b, STa - STb])), axis=0)
    return S1b, STb, V, diff


# ------------------------------------------------------------------ parallel evaluation of the chain
_W = {}


def _wplan(s):
    k = json.dumps([s["id"], s["instruments"]], sort_keys=True, default=str)
    if k not in _W:
        from . import eng_micro, micro_overlay
        m = eng_micro.plan(s)
        ov = eng_micro.make_overlay(m)
        _W[k] = (m, ov)
    return _W[k]


def _weval(args):
    s, coef_list = args
    if "R" not in _W:
        _W["R"] = Runner()
    R = _W["R"]
    m, ov = _wplan(s)
    bk = json.dumps(m["struct_levers"], sort_keys=True)
    out = []
    import warnings
    for coefs in coef_list:
        try:
            with warnings.catch_warnings(), np.errstate(all="ignore"):
                warnings.simplefilter("ignore")
                y = R.eff(m, coefs, ov, bk)
        except Exception:  # noqa: BLE001 — engine failure for an extreme draw = rejected draw
            y = None
        out.append(y if y is not None and np.all(np.isfinite(y)) else None)
    if len(R.base_cache) > 5000:
        R.base_cache.clear()
    return out


class Evaluator:
    """Evaluates many coefficient sets: a process pool (spawn) or serial (WORKERS=0, tests)."""

    def __init__(self, workers=WORKERS):
        self.workers, self.pool, self.n = workers, None, 0

    def __enter__(self):
        if self.workers > 0:
            import multiprocessing as mp
            self.pool = mp.get_context("spawn").Pool(self.workers)
        return self

    def __exit__(self, *a):
        if self.pool is not None:
            self.pool.terminate()
            self.pool.join()

    def __call__(self, s, coef_list, chunk=12):
        self.n += len(coef_list)
        parts = [coef_list[i:i + chunk] for i in range(0, len(coef_list), chunk)]
        res = self.pool.map(_weval, [(s, p) for p in parts]) if self.pool else [_weval((s, p)) for p in parts]
        return [y for r in res for y in r]


# ------------------------------------------------------------------ blocks
def _hz_of(year, start):
    from .engine_base import horizon
    return horizon(year, start)


def bands(E: np.ndarray, y0: np.ndarray, s: dict, block: str, method: str) -> list[dict]:
    E = E[np.all(np.isfinite(E), axis=1)]
    q = np.nanpercentile(E, [5, 25, 50, 75, 95], axis=0)
    rows = []
    for j, (ind, _, _, kind) in enumerate(OUT):
        for t, y in enumerate(Y):
            if y < s["start_year"]:
                continue
            i = j * len(Y) + t
            rows.append({"scenario": s["id"], "block": block, "indicator": ind, "label_az": LABEL[ind], "year": y,
                         "horizon": _hz_of(y, s["start_year"]), "unit": "Δ %" if kind == "pct" else "Δ f.b.",
                         "central": y0[i], "p05": q[0, i], "p25": q[1, i], "p50": q[2, i], "p75": q[3, i],
                         "p95": q[4, i], "n_draws": E.shape[0], "method": method,
                         "note_az": "siyasət təsirinin parametr qeyri-müəyyənliyi zolağı — proqnoz zolağı deyil"})
    return rows


def micro_block(s: dict, ev: Evaluator, N: int = N_MICRO) -> dict:
    t0, n0 = time.perf_counter(), ev.n
    cand = candidates()
    d = len(cand)
    hi = head_index(int(s["start_year"]))
    co = lambda zs: {cand[i]["key"]: cand[i]["value"] + z * cand[i]["se"] for i, z in zs.items()}  # noqa: E731
    res = ev(s, [{}] + [co({i: 1.0}) for i in range(d)])
    y0 = res[0]
    if y0 is None:
        raise RuntimeError("MikroUnit zənciri baza parametrləri ilə işləmədi")
    lim = max(25.0, 25 * float(np.nanmax(np.abs(y0))))
    bad = lambda y: y is None or np.max(np.abs(y)) > lim  # noqa: E731
    yp = np.array([y0 if bad(y) else y for y in res[1:]])
    H0, Hp = heads(y0, hi)[0], heads(yp, hi)
    dH = np.abs(Hp - H0)
    imp = (dH / np.maximum(dH.sum(axis=0), 1e-12)).max(axis=1)
    top = [int(i) for i in np.argsort(-imp)[:TOP_K] if imp[i] > 0.005]
    rng = np.random.default_rng(SEED)
    K = len(top)
    A, B = zdraw(rng, N, K), zdraw(rng, N, K)
    mats = [A, B] + [np.where(np.arange(K) == k, B, A) for k in range(K)]
    sets = [co(dict(zip(top, row))) for M in mats for row in M]
    out = ev(s, sets)
    Yall = np.array([np.full(len(y0), np.nan) if bad(y) else y for y in out])
    n_bad = int(sum(1 for y in out if bad(y)))
    F = [heads(Yall[i * N:(i + 1) * N], hi) for i in range(len(mats))]
    S1, ST, V = indices(F[0], F[1], F[2:])
    ci, stab, stab3 = boot_ci(F[0], F[1], F[2:])
    Zall = np.vstack(mats)
    rej = np.array([bad(y) for y in out])
    instab = []
    for k, i in enumerate(top):
        z = Zall[:, k]
        hi_, lo_ = z > 1, z < -1
        instab.append({"scenario": s["id"], "factor": cand[i]["key"], "factor_label_az": cand[i]["label_az"],
                       "value": cand[i]["value"], "se": cand[i]["se"], "share_rejected_all": float(rej.mean()),
                       "mean_z_rejected": float(z[rej].mean()) if rej.any() else np.nan,
                       "reject_rate_z_gt_1": float(rej[hi_].mean()) if hi_.any() else np.nan,
                       "reject_rate_z_lt_-1": float(rej[lo_].mean()) if lo_.any() else np.nan,
                       "n_draws": int(len(z)), "n_rejected": int(rej.sum())})
    if rej.any() and len(top) > 1:                  # worst pair region: both coefficients above +1 SE / below −1 SE
        best = None
        for k in range(len(top)):
            for l in range(k + 1, len(top)):
                for sk in (1, -1):
                    for sl in (1, -1):
                        m = (sk * Zall[:, k] > 0.5) & (sl * Zall[:, l] > 0.5)
                        if m.sum() >= 10 and (best is None or rej[m].mean() > best[0]):
                            best = (float(rej[m].mean()), k, l, sk, sl, int(m.sum()))
        if best:
            sg = lambda x: "+" if x > 0 else "−"  # noqa: E731
            for r in instab:
                r["worst_region_az"] = (f"{cand[top[best[1]]]['key']} {sg(best[3])}0,5 SE-dən çox və "
                                        f"{cand[top[best[2]]]['key']} {sg(best[4])}0,5 SE-dən çox: "
                                        f"qeyri-sabit çəkiliş payı {best[0]:.0%} (n={best[5]})")
    h = N // 2
    S1h, STh, _ = indices(F[0][:h], F[1][:h], [f[:h] for f in F[2:]])
    diff = np.nanmax(np.abs(np.concatenate([S1h - S1, STh - ST])), axis=0)
    gi = [o for o, _ in hi].index("gdp_real:orta")
    sgn = np.sign(H0[gi]) or 1.0
    drivers = {}
    for k in [int(k) for k in np.argsort(-np.nan_to_num(ST[:, gi]))[:3]]:
        i = top[k]
        slope = Hp[i, gi] - H0[gi]
        drivers[cand[i]["key"]] = cand[i]["value"] + (-np.sign(slope) * sgn if slope else -1.0) * cand[i]["se"]
    E = Yall[: 2 * N]
    return {"block": "micro", "outcomes": [o for o, _ in hi], "H0": H0, "factors": [cand[i]["key"] for i in top],
            "factors_az": [cand[i]["label_az"] for i in top], "value": [cand[i]["value"] for i in top],
            "se": [cand[i]["se"] for i in top], "S1": S1, "ST": ST, "ci": ci, "stab": stab, "stab3": stab3, "conv": diff, "N": N, "instab": instab,
            "n_rejected": n_bad, "n_evals": ev.n - n0, "n_evals_sobol": len(out), "n_cand": d, "seconds": round(time.perf_counter() - t0, 1),
            "screen_share": float(dH[top].sum() / max(dH.sum(), 1e-12)),
            "bands": bands(E, y0, s, "micro", f"MikroUnit əmsalları ±SE (top-{K}, Saltelli A∪B, n={2 * N})"),
            "drivers": drivers, "method": "Saltelli/Jansen, həqiqi zəncir"}


def io_block(s: dict, N: int = 512) -> dict | None:
    """Leontief type I: column scale u_j ~ logN(0, 0.10) + domestic share r ~ U(0.9, 1.1); true model."""
    from . import eng_io
    m = eng_io.model(2025)
    ad, sp = eng_io._adapters(), eng_io._new_spec(m.n)
    y = min(y for it in s["instruments"] for y in it["years"])
    for it in s["instruments"]:
        if y not in it["years"]:
            continue
        for _, a in ad[ad["instrument"] == it["instrument"]].iterrows():
            tr, k = eng_io._scale(a["transform"])
            fn = eng_io.HANDLERS.get(tr.split(":", 1)[1] if tr.startswith("custom:") else a["target_key"])
            if fn is not None:
                fn(m, sp, float(it.get("size", 0.0)) * k, it.get("target"), it)
    df = np.asarray(sp["df"], float)
    if not np.any(np.abs(df) > 1e-9):
        return None
    n, I_ = m.n, np.eye(m.n)

    def f(Z):
        u = np.exp(0.10 * Z[:, :n])
        r = 1 + 0.10 * (2 * norm.cdf(Z[:, n]) - 1)
        Ad1 = m.Ad[None] * u[:, None, :]
        dcol = Ad1.sum(1) - m.Ad.sum(0)[None]
        Ad2, Am2 = Ad1 * r[:, None, None], m.Am[None] + Ad1 * (1 - r[:, None, None])
        dx = np.linalg.solve(I_[None] - Ad2, np.broadcast_to(df, (len(Z), n))[..., None])[..., 0]
        dva = (np.maximum(m.v[None] - dcol, 0) * dx).sum(1) / 1000
        return np.column_stack([dva, 100 * (Am2.sum(1) * dx).sum(1) / df.sum(), (m.e[None] * dx).sum(1) / 1e6])
    sampler = lambda r, k: zdraw(r, k, n + 1)  # noqa: E731
    groups = [[j] for j in range(n)] + [[n]]
    S1, ST, V, diff = sobol_conv(f, groups, sampler, N)
    y0 = f(np.zeros((1, n + 1)))[0]
    E = f(zdraw(np.random.default_rng(SEED + 3), 2000, n + 1))
    q = np.percentile(E, [5, 25, 50, 75, 95], axis=0)
    names = [f"IO A[:, {c}] (sütun miqyası)" for c in m.codes] + ["daxili/idxal bölgüsü r"]
    outs = [("io_va_total", "IO əlavə dəyər effekti (mln AZN)"), ("io_import_leakage", "IO idxal sızması (% son tələb)"),
            ("io_emp_total", "IO məşğulluq effekti (min nəfər)")]
    bnd = [{"scenario": s["id"], "block": "io", "indicator": o, "label_az": la, "year": y,
            "horizon": _hz_of(y, s["start_year"]), "unit": la.split("(")[-1].rstrip(")"), "central": y0[k],
            "p05": q[0, k], "p25": q[1, k], "p50": q[2, k], "p75": q[3, k], "p95": q[4, k], "n_draws": 2000,
            "method": "IO Leontief tip I; A sütunları logN(0; 0,10), r ~ U(0,9; 1,1)",
            "note_az": "fərziyyə: GRAS yenilənməsi və aqreqasiya xətası ±10 % — siyasət təsiri zolağı"}
           for k, (o, la) in enumerate(outs)]
    return {"block": "io", "outcomes": [o for o, _ in outs], "outcomes_az": [la for _, la in outs], "H0": y0,
            "factors": names, "factors_az": names, "value": [1.0] * (n + 1), "se": [0.10] * (n + 1), "S1": S1,
            "ST": ST, "ci": diff, "stab": np.full(3, np.nan), "conv": diff, "N": 2 * N, "n_rejected": 0,
            "bands": bnd, "method": "Saltelli/Jansen, həqiqi IO modeli (N və 2N)", "year": y}


def informality_block(s: dict, micro: dict | None, hired_base: float, prm: dict, N: int = N_SOBOL) -> dict | None:
    """Minimum wage: net formal jobs = FR4 model effect + calibrated disemployment ε·Δ%MW·N_bound/100."""
    its = [it for it in s["instruments"] if it["instrument"] == "min_wage"]
    if not its or not np.isfinite(hired_base):
        return None
    size = float(its[0]["size"])
    lo, hi_ = prm.get("eps_low", -0.3), prm.get("eps_high", 0.0)
    fr4_mu, fr4_sd = 0.0, 0.0
    if micro:
        b = [x for x in micro["bands"] if x["indicator"] == "employment_hired" and x["horizon"] == "orta"]
        if b:
            fr4_mu = np.mean([x["central"] for x in b]) / 100 * hired_base
            fr4_sd = np.mean([x["p95"] - x["p05"] for x in b]) / 3.29 / 100 * hired_base

    def f(Z):
        U = norm.cdf(Z)
        eps = lo + (hi_ - lo) * U[:, 0]
        bs = 0.10 + 0.10 * U[:, 1]
        fr4 = fr4_mu + fr4_sd * Z[:, 2]
        inf = 0.5 + 0.2 * U[:, 3]
        dis = eps * size * bs * hired_base / 100
        return np.column_stack([fr4 + dis, -dis * inf])
    S1, ST, V, diff = sobol_conv(f, [[0], [1], [2], [3]], lambda r, k: zdraw(r, k, 4), N)
    y0 = f(np.array([[norm.ppf((prm.get("eps_mid", -0.1) - lo) / (hi_ - lo)) if hi_ > lo else 0.0, 0.0, 0.0, 0.0]]))[0]
    E = f(zdraw(np.random.default_rng(SEED + 5), 4000, 4))
    q = np.percentile(E, [5, 25, 50, 75, 95], axis=0)
    yr = min(int(s["start_year"]) + 2, Y[-1])
    outs = [("formal_jobs_net", "Xalis formal iş yerləri: FR4 + kalibrlənmiş itki (min nəfər)"),
            ("informal_shift", "Qeyri-formal məşğulluğa keçid (min nəfər)")]
    bnd = [{"scenario": s["id"], "block": "informality", "indicator": o, "label_az": la, "year": yr,
            "horizon": "orta", "unit": "min nəfər", "central": y0[k], "p05": q[0, k], "p25": q[1, k], "p50": q[2, k],
            "p75": q[3, k], "p95": q[4, k], "n_draws": 4000, "method": "kalibrlənmiş kanal (Tier D), Monte Karlo",
            "note_az": "makro modeldə bu kanal yoxdur; ədəbiyyat intervalı ε ∈ [−0,3; 0]"} for k, (o, la) in enumerate(outs)]
    names = ["ε: minimum əmək haqqına məşğulluq elastikliyi (ədəbiyyat)", "minimum əmək haqqı ətrafında işçilərin payı",
             "FR4 modelinin formal iş yeri effekti", "itən iş yerlərinin qeyri-formala keçən payı"]
    return {"block": "informality", "outcomes": [o for o, _ in outs], "outcomes_az": [la for _, la in outs], "H0": y0,
            "factors": ["eps_mw", "bound_share", "fr4_hired", "inf_share"], "factors_az": names,
            "value": [prm.get("eps_mid", -0.1), 0.15, fr4_mu, 0.6], "se": [np.nan, np.nan, fr4_sd, np.nan],
            "S1": S1, "ST": ST, "ci": diff, "stab": np.full(2, np.nan), "conv": diff, "N": 2 * N, "n_rejected": 0,
            "bands": bnd, "method": "Saltelli/Jansen (N və 2N)"}


def _key(s) -> str:
    raw = json.dumps([VERSION, N_MICRO, mb.vintage(), s["start_year"], s["instruments"]], sort_keys=True, default=str)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def run(s: dict, ev: Evaluator | None, hired_base: float = np.nan, prm: dict | None = None, log=print,
        use_cache=True) -> dict:
    """All blocks for one scenario (cached by scenario + vintage + settings)."""
    from . import eng_micro
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"sens_{s['id']}_{_key(s)}.pkl"
    if use_cache and f.exists():
        r = pickle.loads(f.read_bytes())
        r["cached"] = True
        return r
    out, status = [], []
    try:
        handled = eng_micro.plan(s)["handled"]
    except Exception:  # noqa: BLE001
        handled = []
    micro = None
    if handled and ev is not None:
        try:
            micro = micro_block(s, ev)
            out.append(micro)
            status.append(("micro", "ok", f"{micro['n_evals']} qiymətləndirmə, {micro['seconds']} s, "
                                          f"rədd edilən qeyri-sabit çəkilişlər {micro['n_rejected']}"))
        except Exception as e:  # noqa: BLE001
            status.append(("micro", "xəta", f"{type(e).__name__}: {e}"))
    else:
        status.append(("micro", "tətbiq edilmir", "MikroUnit kanalı yoxdur (CAEM-only alət) və ya hesablayıcı yoxdur"))
    for name, fn in (("io", lambda: io_block(s)), ("informality", lambda: informality_block(s, micro, hired_base, prm or {}))):
        try:
            b = fn()
            if b is not None:
                out.append(b)
                status.append((name, "ok", b["method"]))
        except Exception as e:  # noqa: BLE001
            status.append((name, "xəta", f"{type(e).__name__}: {e}"))
    status.append(("microsim", "buraxıldı", "mikrosimulyasiya: bir icra ≈ 15 s və davranış parametrləri üçün interfeys "
                   "(eng_microsim.simulate behaviour=) hələ aktiv deyil — Monte Karlo bu blok üçün aparılmadı"))
    r = {"scenario": s["id"], "blocks": out, "status": status, "drivers": (micro or {}).get("drivers", {}),
         "cached": False}
    f.write_bytes(pickle.dumps(r))
    return r


def _conv_label(ci, stab3, stab1=np.nan) -> str:
    """'bəli' = bootstrap 95 % CI half-width ≤ 0,15; otherwise 'indikativ' (+ whether the top-3 set / the
    first driver is stable in ≥ 80 % / ≥ 90 % of bootstrap resamples)."""
    if np.isfinite(ci) and ci <= 0.15:
        return "bəli"
    if np.isfinite(stab3) and stab3 >= 0.8:
        return "indikativ (ilk-3 sabit)"
    if np.isfinite(stab1) and stab1 >= 0.9:
        return "indikativ (1-ci sürücü sabit)"
    return "indikativ"


def frames(results: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows, bnd, ins = [], [], []
    for r in results:
        for b in r["blocks"]:
            bnd += b["bands"]
            ins += b.get("instab") or []
            outs_az = b.get("outcomes_az") or [LABEL.get(o.split(":")[0], o) + f" — {o.split(':')[1]} müddət"
                                                for o in b["outcomes"]]
            for j, o in enumerate(b["outcomes"]):
                st = np.nan_to_num(b["ST"][:, j], nan=-1)
                order = np.argsort(-st)
                for rk, i in enumerate(order, 1):
                    if b["block"] == "io" and rk > 5:
                        break
                    rows.append({"scenario": r["scenario"], "block": b["block"], "outcome": o, "outcome_label_az": outs_az[j],
                                 "base_effect": b["H0"][j], "factor": b["factors"][i], "factor_label_az": b["factors_az"][i],
                                 "factor_value": b["value"][i], "factor_se": b["se"][i], "S1": b["S1"][i, j],
                                 "ST": b["ST"][i, j], "rank": rk, "top3": rk <= 3, "ci_halfwidth": b["ci"][j],
                                 "conv_diff": b["conv"][j], "top1_stability": b["stab"][j], "N": b["N"],
                                 "n_rejected": b["n_rejected"],
                                 "top3_stability": (b.get("stab3") if b.get("stab3") is not None else np.full(len(b["outcomes"]), np.nan))[j],
                                 "share_rejected": b["n_rejected"] / max(b.get("n_evals_sobol", 1), 1),
                                 "converged": _conv_label(b["ci"][j], (b.get("stab3") if b.get("stab3") is not None else [np.nan] * len(b["outcomes"]))[j], b["stab"][j]),
                                 "method": b["method"]})
        for blk, stt, msg in r["status"]:
            if stt != "ok":
                rows.append({"scenario": r["scenario"], "block": blk, "outcome": "", "factor": "", "method": stt,
                             "factor_label_az": msg})
    return pd.DataFrame(rows), pd.DataFrame(bnd), pd.DataFrame(ins)

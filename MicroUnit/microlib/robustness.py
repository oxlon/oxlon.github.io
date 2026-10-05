"""Stability / robustness: recursive and leave-one-year-out paths, Chow, recursive-residual CUSUM,
verdict rule (contract A), hold-out metrics (RMSE, Theil U, HLN-DM)."""
from __future__ import annotations

import numpy as np
from scipy import stats

from .estimators import ols_np


def recursive(fit_fn, time, names, n_min):
    """Expanding window over sorted periods. fit_fn(mask) -> (b, se) aligned with `names`.
    A window is estimated once it holds >= n_min rows."""
    time = np.asarray(time)
    out = dict(years=[], coef={c: [] for c in names}, se={c: [] for c in names}, n_min=int(n_min))
    for p in sorted(set(time.tolist())):
        m = time <= p
        if m.sum() < n_min:
            continue
        try:
            b, se = fit_fn(m)
        except Exception:  # noqa: BLE001
            continue
        out["years"].append(p)
        for j, c in enumerate(names):
            out["coef"][c].append(float(b[j]))
            out["se"][c].append(float(se[j]) if se is not None else None)
    return out


def loo(fit_fn, time, names):
    """Leave one period (year) out. Returns dict(years, coef{name:[...]}, range{name:[min,max]})."""
    time = np.asarray(time)
    out = dict(years=[], coef={c: [] for c in names})
    for p in sorted(set(time.tolist())):
        m = time != p
        try:
            b, _ = fit_fn(m)
        except Exception:  # noqa: BLE001
            continue
        out["years"].append(p)
        for j, c in enumerate(names):
            out["coef"][c].append(float(b[j]))
    out["range"] = {c: ([float(np.nanmin(v)), float(np.nanmax(v))] if len(v) else None)
                    for c, v in out["coef"].items()}
    return out


def chow_test(y, X, years, brk):
    """Classical Chow F at `brk` (first year of the second regime), nonrobust OLS, k = all params incl.
    the constant; feasible when each sub-sample has >= k+2 observations (notebook rule)."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    years = np.asarray(years)
    n, k = X.shape
    m1, m2 = years < brk, years >= brk
    n1, n2 = int(m1.sum()), int(m2.sum())
    res = dict(break_year=brk, f=None, p=None, n1=n1, n2=n2, df1=k, df2=n - 2 * k)
    if n1 < k + 2 or n2 < k + 2:
        res["reason"] = f"alt-nümunələr çox qısadır (n1={n1}, n2={n2}, k={k})"
        return res
    s_all = (lambda r: r["u"] @ r["u"])(ols_np(y, X, "nonrobust"))
    s_sub = sum((lambda r: r["u"] @ r["u"])(ols_np(y[m], X[m], "nonrobust")) for m in (m1, m2))
    if n - 2 * k <= 0 or s_sub <= 0:
        res["reason"] = "sərbəstlik dərəcəsi çatmır"
        return res
    F = ((s_all - s_sub) / k) / (s_sub / (n - 2 * k))
    res.update(f=float(F), p=float(1 - stats.f.cdf(F, k, n - 2 * k)))
    return res


def chow_set(y, X, years, breaks=(2015, 2020)):
    years = np.asarray(years)
    ys = np.sort(years)
    mid = int(ys[len(ys) // 2])
    out, seen = [], set()
    for b, lab in [(mid, "orta nöqtə")] + [(int(b), str(b)) for b in breaks]:
        if b in seen:
            for r in out:
                if r["break_year"] == b:
                    r["label"] += f" = {lab}"
            continue
        seen.add(b)
        r = chow_test(y, X, years, b)
        r["label"] = lab
        out.append(r)
    return out


def recursive_residuals(y, X):
    """Brown-Durbin-Evans recursive residuals w_t, t = k+1..n (sample in time order)."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    w = []
    for t in range(k, n):
        Xt = X[:t]
        A = np.linalg.pinv(Xt.T @ Xt)
        b = A @ Xt.T @ y[:t]
        x = X[t]
        w.append((y[t] - x @ b) / np.sqrt(1 + x @ A @ x))
    return np.asarray(w)


def cusum_p_from_stat(a):
    """BDE crossing probability of the +-a[sqrt(T-k) + 2(r-k)/sqrt(T-k)] lines:
    p = 2[1 - Phi(3a) + exp(-4a^2) Phi(a)]  (a = 0.948 -> 0.05, 1.143 -> 0.01)."""
    p = 2 * (1 - stats.norm.cdf(3 * a) + np.exp(-4 * a * a) * stats.norm.cdf(a))
    return float(min(max(p, 0.0), 1.0))


def cusum_test(y, X):
    X = np.asarray(X, float)
    n, k = X.shape
    if n - k < 5:
        return dict(stat=None, p=None, reason=f"n-k = {n - k} < 5")
    w = recursive_residuals(y, X)
    m = len(w)
    sig = np.sqrt((w @ w) / m)
    if not np.isfinite(sig) or sig <= 0:
        return dict(stat=None, p=None, reason="qalıq dispersiyası sıfırdır")
    W = np.cumsum(w) / sig
    r = np.arange(1, m + 1)
    bound = np.sqrt(m) + 2 * r / np.sqrt(m)
    a = float(np.max(np.abs(W) / bound))
    return dict(stat=a, p=cusum_p_from_stat(a), n_rr=m, path=W.tolist())


def verdict(rec, lo, chow_list, cusum_p, used, full):
    """Contract rule. used: coefficient names checked; full: {name: full-sample coef}."""
    notes, flip_late, sign_rec, sign_loo = [], [], True, True
    for c in used:
        s0 = np.sign(full.get(c, np.nan))
        if not np.isfinite(s0) or s0 == 0:
            continue
        path = np.asarray([v for v in (rec or {}).get("coef", {}).get(c, []) if v is not None], float)
        if path.size:
            bad = np.sign(path) != s0
            if bad.any():
                sign_rec = False
            if bad[len(path) // 2:].any():
                flip_late.append(c)
        lv = np.asarray((lo or {}).get("coef", {}).get(c, []), float)
        if lv.size and (np.sign(lv) != s0).any():
            sign_loo = False
            notes.append(f"{c}: bir ili çıxarmaqla işarə dəyişir")
    chow_ps = [r["p"] for r in chow_list or [] if r.get("p") is not None]
    has_rec = bool(rec and rec.get("years"))
    if flip_late:
        notes.insert(0, "rekursiv yolun son yarısında işarə dəyişir: " + ", ".join(flip_late))
    if any(p < 0.01 for p in chow_ps):
        notes.append("Chow p < 0.01 (struktur qırılma)")
    if flip_late or any(p < 0.01 for p in chow_ps):
        return "qeyri-stabil", "; ".join(notes)
    ok_tests = all(p > 0.05 for p in chow_ps) and (cusum_p is None or cusum_p > 0.05)
    if not has_rec:
        notes.append("rekursiv qiymətləndirmə mümkün deyil (n < k+5)")
    if not chow_ps:
        notes.append("Chow testi mümkün deyil")
    if cusum_p is None:
        notes.append("CUSUM mümkün deyil")
    if has_rec and sign_rec and sign_loo and ok_tests:
        return "stabil", "; ".join(notes) or "bütün meyarlar ödənilir"
    if not sign_rec:
        notes.append("rekursiv yolun ilk yarısında işarə dəyişir")
    if not ok_tests:
        notes.append("Chow/CUSUM p ≤ 0.05")
    return "qismən stabil", "; ".join(dict.fromkeys(notes))


def hln_dm(e1, e2, h=3):
    """Diebold-Mariano with Harvey-Leybourne-Newbold correction, p from t(n-1) (notebook FR1 `hln_dm`)."""
    d = np.asarray(e1, float) ** 2 - np.asarray(e2, float) ** 2
    n = len(d)
    if n < 3:
        return None, None
    dc = d - d.mean()
    v = (dc @ dc) / n + 2 * sum((dc[k:] @ dc[:-k]) / n for k in range(1, h))
    if v <= 0:
        v = (dc @ dc) / n
    if v <= 0:
        return None, None
    dm = d.mean() / np.sqrt(v / n) * np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    return float(dm), float(2 * (1 - stats.t.cdf(abs(dm), n - 1)))


def holdout_metrics(years, actual, model, rw=None, const=None, cut=None, h=3):
    a = np.asarray(actual, float)
    m = np.asarray(model, float)
    rmse = lambda f: float(np.sqrt(np.mean((a - np.asarray(f, float)) ** 2)))  # noqa: E731
    out = dict(cut=cut, years=list(years), rmse=rmse(m), theil_u_rw=None, theil_u_const=None, dm_p_rw=None)
    if rw is not None:
        r = rmse(rw)
        out["theil_u_rw"] = out["rmse"] / r if r > 0 else None
        out["dm_p_rw"] = hln_dm(a - m, a - np.asarray(rw, float), h=min(h, max(len(a) - 2, 1)))[1]
    if const is not None:
        r = rmse(const)
        out["theil_u_const"] = out["rmse"] / r if r > 0 else None
    return out

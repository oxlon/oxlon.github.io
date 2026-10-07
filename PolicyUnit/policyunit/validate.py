"""NFR1 — retrospective validation of the PolicyUnit models on historical policy events (MİİS §15.5.4).

    python3 -m policyunit.validate          # -> output/V_nfr1_*.csv + docs/Sapma_hesabati.md

Event register: config/historical_events.csv (nfr1_data); predictions: nfr1_models (MicroUnit chain
as a transplanted shock, FR1 E2 / FR3 E4 direct, IO price model, CAEM, microsimulation files);
comparison metrics and the PROPOSED tolerance rule (TOL — the Ministry has not set one) below;
report generated from the V_nfr1_ outputs by nfr1_report (no hand-typed numbers)."""
from __future__ import annotations

import json
import math
import time

import numpy as np
import pandas as pd

from . import catalog, config
from . import nfr1_data as D
from . import nfr1_models as M

OWNER = "nfr1"
# Proposed tolerance rule (TƏKLİF — to be agreed with the Ministry). e = predicted − observed effect.
# Magnitude: |e| ≤ max(rel·|obs|, min(sig·σ_cf, cap·|obs|)) — counterfactual noise widens the relative
# tolerance only up to `cap`; model uncertainty is reported separately (in_model_band), not added.
# A comparison that does not beat the non-trivial naive benchmark is capped at 'qismən uyğun'.
# Identified if |obs| ≥ ident_sigma·σ_cf (or σ_cf unknown). Event 'keçdi' needs ≥ min_decisive decisive
# primary comparisons.
TOL = {"rel_ok": 0.25, "cap_ok": 0.35, "sig_ok": 1.0, "rel_part": 0.50, "cap_part": 0.75, "sig_part": 2.0,
       "ident_sigma": 1.0, "sigma": "cf", "naive_required": True, "min_decisive": 2}
TOL_SETS = {
    "qatı": {**TOL, "rel_ok": 0.15, "cap_ok": 0.20, "rel_part": 0.35, "cap_part": 0.50},
    "təklif": TOL,
    "yumşaq (v1: σ_model+σ_əf, limitsiz)": {**TOL, "rel_ok": 0.30, "cap_ok": 1e9, "rel_part": 0.60, "cap_part": 1e9,
                                             "sigma": "total", "naive_required": False, "min_decisive": 1},
}
CLASS_AZ = {2: "uyğun", 1: "qismən uyğun", 0: "uyğunsuz", -1: "müəyyən deyil (aşağı güc)"}
VERDICT = [(1.5, "keçdi"), (0.75, "şərti keçdi"), (-1, "keçmədi")]


def _f(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return math.nan
    return x if math.isfinite(x) else math.nan


def classify(pred, obs, lo, hi, sigma_cf, tol=TOL, placebo=False, naive=math.nan) -> dict:
    """Metrics + tolerance class of one predicted-vs-observed comparison. Observed effect within the
    counterfactual noise (low power): only a miss beyond sig_part·σ_cf is decisive ('uyğunsuz'); a placebo
    row passes when |e| ≤ sig_ok·σ_cf; otherwise 'müəyyən deyil' (score −1, not used in verdicts)."""
    pred, obs, lo, hi, sc, nv = map(_f, (pred, obs, lo, hi, sigma_cf, naive))
    sm = (hi - lo) / 3.92 if math.isfinite(lo) and math.isfinite(hi) else math.nan
    sig = math.sqrt(sum(v * v for v in (sm, sc) if math.isfinite(v))) if (math.isfinite(sm) or math.isfinite(sc)) else math.nan
    s_use = (sig if tol["sigma"] == "total" else sc)
    s_use = s_use if math.isfinite(s_use) else 0.0
    e = pred - obs
    ident = not math.isfinite(sc) or abs(obs) >= tol["ident_sigma"] * sc
    dir_hit = (np.sign(pred) == np.sign(obs)) if ident and obs != 0 else None
    if ident:
        ok = max(tol["rel_ok"] * abs(obs), min(tol["sig_ok"] * s_use, tol["cap_ok"] * abs(obs)))
        part = max(tol["rel_part"] * abs(obs), min(tol["sig_part"] * s_use, tol["cap_part"] * abs(obs)))
    else:                                   # observed effect within counterfactual noise: magnitude only
        ok, part = tol["sig_ok"] * s_use, tol["sig_part"] * s_use
    score = 2 if abs(e) <= ok else 1 if abs(e) <= part else 0
    if dir_hit is False:
        score = 0
    beats = abs(e) < abs(obs - nv) if math.isfinite(nv) else None
    if tol["naive_required"] and beats is False and score == 2:
        score = 1
    if not ident and score > 0 and not (placebo and score == 2):
        score = -1                          # within noise: not determinable (excluded from verdicts)
    power = ("yüksək" if not math.isfinite(sc) or abs(obs) >= 2 * sc else "orta" if ident else "aşağı")
    return {"error": e, "abs_error": abs(e), "pct_error": 100 * abs(e) / abs(obs) if obs else math.nan,
            "dir_hit": "" if dir_hit is None else ("bəli" if dir_hit else "xeyr"),
            "in_model_band": "" if not math.isfinite(sm) else ("bəli" if lo <= obs <= hi else "xeyr"),
            "in_band_cf": "" if not math.isfinite(sig) else
            ("bəli" if (lo if math.isfinite(lo) else pred) - 1.96 * (sc if math.isfinite(sc) else 0) <= obs
             <= (hi if math.isfinite(hi) else pred) + 1.96 * (sc if math.isfinite(sc) else 0) else "xeyr"),
            "beats_naive": "" if beats is None else ("bəli" if beats else "xeyr"),
            "beats_zero": "bəli" if abs(e) < abs(obs) else "xeyr", "sigma_model": sm, "sigma_total": sig,
            "tol_ok": ok, "tol_part": part, "power": power, "score": score, "class_az": CLASS_AZ[score]}


def comparisons(ev: pd.DataFrame | None = None, log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    ev = D.events() if ev is None else ev
    obs_rows, rows = [], []
    for _, r in ev.iterrows():
        o = D.observed(r)
        o.update({k: r[k] for k in ("event_id", "indicator", "label_az", "year", "series", "kind", "cf_rule",
                                    "cf_alt", "obs_source", "obs_note_az", "in_sample")})
        obs_rows.append(o)
        if o["obs_check"]:
            log(f"  [nfr1] {r['row_id']}: {o['obs_check']}")
        try:
            ssz = M.shock(r)["dev"][0] if r.get("naive_rule") == "shock" else math.nan
        except Exception:  # noqa: BLE001
            ssz = math.nan
        nv, nrule = D.naive(r, o, ssz)
        o["naive"], o["naive_rule"] = nv, nrule
        for k, m in enumerate(r["methods"].split(";")):
            try:
                p = M.METHODS[m](r)
            except Exception as err:  # noqa: BLE001 — one failing method must not hide the others
                log(f"  [nfr1] {r['row_id']} {m}: XƏTA {type(err).__name__}: {err}")
                p = None
            if p is None:
                continue
            pl = "plasebo" in r["label_az"]
            c = classify(p["pred"], o["obs_effect"], p["lo"], p["hi"], o["sigma_cf"], placebo=pl, naive=nv)
            alt = classify(p["pred"], o["obs_effect_alt"], p["lo"], p["hi"], o["sigma_cf"], placebo=pl, naive=nv) \
                if math.isfinite(_f(o["obs_effect_alt"])) else {"class_az": ""}
            rows.append({"event_id": r["event_id"], "row_id": r["row_id"], "indicator": r["indicator"],
                         "label_az": r["label_az"], "year": int(r["year"]), "method": m,
                         "method_az": M.METHOD_LABEL_AZ[m], "primary_method": int(k == 0),
                         "primary_row": int(r["primary"]), "in_sample": M.METHOD_SAMPLE.get(m, r["in_sample"]),
                         "pred": p["pred"], "pred_lo": p["lo"], "pred_hi": p["hi"],
                         "obs_effect": o["obs_effect"], "obs_effect_alt": o["obs_effect_alt"],
                         "sigma_cf": o["sigma_cf"], "naive": nv, "naive_rule": nrule, "placebo": int(pl),
                         **c, "class_alt_cf": alt["class_az"],
                         "tier_model": p["tier"], "tier_obs": "B" if r["kind"] in ("did", "io_e7") else "C",
                         "note_az": p["note_az"]})
    return pd.DataFrame(obs_rows), pd.DataFrame(rows)


def _shares(g: pd.DataFrame) -> dict:
    """Class shares among DECISIVE comparisons; direction hit rate among comparisons with a direction."""
    d = g[g.score >= 0]
    nd = (g.dir_hit.fillna("") != "").sum()
    sh = lambda k: float((d.score == k).mean()) if len(d) else math.nan  # noqa: E731
    return {"share_ok": sh(2), "share_part": sh(1), "share_fail": sh(0),
            "dir_hit_rate": float((g.dir_hit == "bəli").sum() / nd) if nd else math.nan}


def _verdict(x: float, n: int = 99, tol=TOL) -> str:
    if not math.isfinite(x) or n == 0:
        return "qiymətləndirilmədi"
    v = next(v for t, v in VERDICT if x >= t)
    return "şərti keçdi" if v == "keçdi" and n < tol["min_decisive"] else v


def rescore(cmp: pd.DataFrame, tol) -> pd.Series:
    return pd.Series([classify(r.pred, r.obs_effect, r.pred_lo, r.pred_hi, r.sigma_cf, tol, bool(r.placebo),
                               r.naive)["score"] for r in cmp.itertuples()], index=cmp.index)


def sensitivity(cmp: pd.DataFrame) -> pd.DataFrame:
    """Event verdicts under alternative tolerance sets (pass/fail sensitivity to the tolerance choice)."""
    out = []
    for name, tol in TOL_SETS.items():
        sc = rescore(cmp, tol)
        for eid, g in cmp.assign(score=sc).groupby("event_id", sort=False):
            pr = g[(g.primary_row == 1) & (g.score >= 0)]
            m = float(pr.score.mean()) if len(pr) else math.nan
            out.append({"tol_set": name, "event_id": eid, "n_primary_decisive": len(pr), "primary_mean_score": m,
                        "n_ok": int((g.score == 2).sum()), "n_part": int((g.score == 1).sum()),
                        "n_fail": int((g.score == 0).sum()), "n_low_power": int((g.score < 0).sum()),
                        "verdict_az": _verdict(m, len(pr), tol),
                        "params": ";".join(f"{k}={v}" for k, v in tol.items() if k not in ("ident_sigma",))})
    return pd.DataFrame(out)


def event_summary(ev: pd.DataFrame, cmp: pd.DataFrame) -> pd.DataFrame:
    out = []
    for eid, g in cmp.groupby("event_id", sort=False):
        e = ev[ev.event_id == eid].iloc[0]
        pr = g[(g.primary_row == 1) & (g.score >= 0)]
        n_meth = g.groupby("row_id")["method"].nunique()
        out.append({"event_id": eid, "event_name_az": e["event_name_az"], "event_date_az": e["event_date_az"],
                    "in_sample": "/".join(sorted(set(g.in_sample))), "n_rows": g.row_id.nunique(),
                    "n_comparisons": len(g), "methods": ";".join(dict.fromkeys(g.method)),
                    "n_methods": g.method.nunique(), "rows_with_2plus_methods": int((n_meth >= 2).sum()),
                    "nfr2_ok": "bəli" if (n_meth >= 2).any() else "xeyr",
                    "primary_mean_score": float(pr.score.mean()) if len(pr) else math.nan,
                    "n_decisive": int((g.score >= 0).sum()), "n_low_power": int((g.score < 0).sum()),
                    "n_primary_decisive": int(len(pr)), **_shares(g),
                    "beats_naive_rate": float((g.beats_naive == "bəli").sum() / max(1, (g.beats_naive != "").sum())),
                    "verdict_az": _verdict(float(pr.score.mean()) if len(pr) else math.nan, len(pr))})
    return pd.DataFrame(out)


def method_summary(cmp: pd.DataFrame) -> pd.DataFrame:
    out = []
    for m, g in cmp.groupby("method", sort=False):
        out.append({"method": m, "method_az": M.METHOD_LABEL_AZ[m], "n": len(g),
                    "n_decisive": int((g.score >= 0).sum()), "events": ";".join(dict.fromkeys(g.event_id)),
                    "mean_score": float(g[g.score >= 0].score.mean()), **_shares(g),
                    "median_pct_error": float(g.pct_error.median()),
                    "mean_error": float(g.error.mean()),
                    "beats_naive_rate": float((g.beats_naive == "bəli").sum() / max(1, (g.beats_naive != "").sum()))})
    return pd.DataFrame(out)


def tolerance_table() -> pd.DataFrame:
    rows = [("rel_ok", "«uyğun»: |sapma| ≤ max(rel_ok·|fakt|, min(sig_ok·σ_əf, cap_ok·|fakt|))"),
            ("cap_ok", "əks-faktual səs-küyü tolerantlığı ən çox cap_ok·|fakt|-a qədər genişləndirir"),
            ("sig_ok", "σ_əf — yalnız əks-faktualın səs-küyü; model intervalı ayrıca göstərilir (toplanmır)"),
            ("rel_part", "«qismən uyğun»: |sapma| ≤ max(rel_part·|fakt|, min(sig_part·σ_əf, cap_part·|fakt|))"),
            ("cap_part", "qismən uyğunluq üçün yuxarı hədd"),
            ("sig_part", "əks halda «uyğunsuz»; istiqamət səhvdirsə həmişə «uyğunsuz»"),
            ("naive_required", "sadə etalonu (əvvəlki ilin nəticəsi / tam mexaniki ötürmə) üstələməyən müqayisə ən çox «qismən uyğun»"),
            ("min_decisive", "«keçdi» üçün ən azı bu qədər həlledici əsas müqayisə; az olduqda ən çox «şərti keçdi»"),
            ("ident_sigma", "|fakt| < ident_sigma·σ_əf → təsir müəyyən edilmir (aşağı güc); yalnız 2σ_əf-dən böyük səhv həlledicidir")]
    return pd.DataFrame([{"param": k, "value": TOL[k], "rule_az": t, "status_az": "TƏKLİF — Nazirliklə razılaşdırılmalıdır"}
                         for k, t in rows])


def vintage() -> dict:
    import hashlib
    v = {}
    try:
        from . import microbridge as mb
        v.update(mb.vintage())
    except Exception as err:  # noqa: BLE001
        v["micro_vintage"] = f"xəta: {err}"
    for k, p in {"events_md5": D.EVENTS_CSV, **{f"{s}_md5": q for s, q in D.SOURCES.items()}}.items():
        v[k] = hashlib.md5(p.read_bytes()).hexdigest()[:12] if p.exists() else "yoxdur"
    v["caem_md5"] = config.CAEM_MD5
    return v


def run(log=print, report: bool = True) -> dict:
    t0 = time.perf_counter()
    ev = D.events()
    obs, cmp = comparisons(ev, log)
    evs = event_summary(ev, cmp)
    ms = method_summary(cmp)
    meta = {"run_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.perf_counter() - t0, 2),
            "n_events": int(evs.shape[0]), "n_comparisons": int(len(cmp)), "chain_offset": M.OFFSET,
            "tolerance": TOL, **vintage()}
    files = [
        catalog.write_csv(obs, "V_nfr1_observed.csv", OWNER,
                          "NFR1: müşahidə olunan siyasət təsirləri — əks-faktual (əsas/alternativ), σ, mənbə"),
        catalog.write_csv(cmp, "V_nfr1_comparisons.csv", OWNER,
                          "NFR1: proqnoz və fakt müqayisəsi (hadisə × göstərici × metod): sapma, % sapma, istiqamət, interval, tolerantlıq sinfi"),
        catalog.write_csv(evs, "V_nfr1_events.csv", OWNER,
                          "NFR1: hadisələr üzrə icmal və hökm (NFR2: göstərici üzrə ≥2 metod)"),
        catalog.write_csv(ms, "V_nfr1_methods.csv", OWNER, "NFR1: metodlar üzrə icmal (bütün hadisələr)"),
        catalog.write_csv(tolerance_table(), "V_nfr1_tolerance.csv", OWNER,
                          "NFR1: təklif olunan tolerantlıq qaydası (Nazirliklə razılaşdırılmalıdır)"),
        catalog.write_csv(sensitivity(cmp), "V_nfr1_tolerance_sensitivity.csv", OWNER,
                          "NFR1: hökmlərin tolerantlıq seçiminə həssaslığı (qatı / təklif / yumşaq v1)"),
        catalog.write_csv(pd.DataFrame([{"key": k, "value": json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v}
                                        for k, v in meta.items()]), "V_nfr1_run_meta.csv", OWNER,
                          "NFR1: iş metaməlumatı (vintaj id-ləri, tolerantlıq, vaxt)"),
    ]
    if report:
        from . import nfr1_report
        files.append(nfr1_report.write(log=log))
    log(f"  [nfr1] {meta['n_events']} hadisə, {meta['n_comparisons']} müqayisə; "
        + "; ".join(f"{r.event_id}: {r.verdict_az}" for r in evs.itertuples()))
    return {"files": files, "meta": meta, "events": evs}


if __name__ == "__main__":
    run()

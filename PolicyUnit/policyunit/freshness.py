"""Baseline vintage ids (contract: every run records MicroUnit, CAEM, OxLon forecast_long, IO table, RiskUnit
baseline) and the end-of-run freshness check (stage `core.freshness`). Writes output/P1_freshness.csv.

Hard failures: core outputs inconsistent with each other or produced from an engine vintage that differs from
the current upstream hashes. Warnings (env POLICY_FRESHNESS_STRICT=1 turns them into failures): FR4 rows fetched
from a RiskUnit baseline that differs from RiskUnit's current `_run_summary_v2.json`."""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd

from . import catalog, config


def _md5(p) -> str | None:
    if not p.exists():
        return None
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def riskunit_baseline() -> str | None:
    p = config.RISK_ROOT / "output" / "_run_summary_v2.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("baseline_id")
    except (OSError, ValueError):
        return None


def current() -> dict:
    """Current upstream vintage ids (computed now, nothing cached)."""
    from . import caem_core, microbridge
    v = dict(microbridge.vintage())
    v["caem_md5"] = caem_core.vintage_status()["copy_md5"]
    v["oxlon_forecast_long_md5"] = _md5(config.OXLON_ROOT / "delivery" / "2_neticeler" / "forecast_long.csv")
    try:
        from . import eng_io
        m = eng_io.model(2025)
        v["io_table"] = m.label
        v["io_table_year"] = 2021
        v["io_update_year"] = 2025
        v["io_benchmark_md5"] = m.t.meta.get("md5", "")
    except Exception as e:  # noqa: BLE001
        v["io_table"] = f"yoxdur ({type(e).__name__})"
    v["riskunit_baseline_id"] = riskunit_baseline()
    return v


def check(t_run: float | None = None, log=print) -> pd.DataFrame:
    out = config.OUTPUT
    rows = []
    add = lambda item, status, msg: rows.append({"check": item, "status": status, "message_az": msg})
    p1 = out / "P1_effects.csv"
    t_run = t_run or p1.stat().st_mtime
    for f, owner in (("P3_microsim_headline.csv", "microsim"), ("P4_kpi_inputs.csv", "fr4"),
                     ("P4_risk_profile.csv", "fr4"), ("V_nfr1_comparisons.csv", "nfr1"),
                     ("P5_ranking.csv", "core"), ("P5_kpi_values.csv", "core")):
        p = out / f
        if p.exists():
            ok = p.stat().st_mtime >= t_run
            add(f"təzəlik:{f}", "ok" if ok else "xəta", "" if ok else f"{f} ({owner}) bu işdən əvvəl yazılıb — köhnədir")
    for a, b in (("P5_ranking.csv", "P4_kpi_inputs.csv"), ("P5_ranking.csv", "V_nfr1_comparisons.csv")):
        if (out / a).exists() and (out / b).exists():
            ok = (out / a).stat().st_mtime >= (out / b).stat().st_mtime
            add(f"ardıcıllıq:{a}>{b}", "ok" if ok else "xəta", "" if ok else f"{a} {b}-dən əvvəl yazılıb")
    v, k = out / "P5_kpi_values.csv", out / "P4_risk_profile.csv"
    if v.exists() and k.exists():
        vv, kk = pd.read_csv(v), pd.read_csv(k)
        rb = vv[vv.kpi == "risk_breach"].set_index("scenario")["value"]
        ref = kk[kk.variant == "base"].groupby("scenario")["dP"].max()
        bad = [s for s in rb.index if s in ref.index and abs(rb[s] - ref[s]) > 1e-6]
        add("uyğunluq:P5.risk_breach=P4", "xəta" if bad else "ok", ", ".join(bad))
    p3 = out / "P3_microsim_headline.csv"
    if p3.exists():
        f1 = pd.read_csv(p1, usecols=["scenario", "engine", "indicator", "year", "delta"])
        g1 = f1[(f1.engine == "microsim") & (f1.indicator == "gini")].set_index(["scenario", "year"])["delta"]
        g3 = pd.read_csv(p3).set_index(["scenario", "year"])["gini"]
        com = g1.index.intersection(g3.index)
        mx = float((g1[com] - g3[com]).abs().max()) if len(com) else 0.0
        add("uyğunluq:P3.gini=P1", "xəta" if mx > 1e-6 else "ok", f"maks. fərq {mx:.4g}")
    meta_p = out / "P1_run_meta.json"
    if meta_p.exists():
        rec = json.loads(meta_p.read_text(encoding="utf-8")).get("vintage", {})
        cur = current()
        for key in ("micro_vintage", "caem_md5", "oxlon_forecast_long_md5", "io_table", "io_benchmark_md5"):
            if key in rec and rec.get(key) != cur.get(key):
                add(f"vintaj:{key}", "xəta", f"P1 vintajı {rec.get(key)} ≠ cari {cur.get(key)} — P1 yenidən hesablanmalıdır")
            elif key in rec:
                add(f"vintaj:{key}", "ok", str(cur.get(key)))
        rid = cur.get("riskunit_baseline_id")
        if k.exists() and rid:
            ids = sorted(set(pd.read_csv(k, usecols=["baseline_id"])["baseline_id"].dropna().astype(str)))
            stale = [i for i in ids if i != rid]
            st = ("xəta" if os.environ.get("POLICY_FRESHNESS_STRICT") == "1" else "xəbərdarlıq") if stale else "ok"
            add("vintaj:riskunit_baseline_id(P4)", st,
                f"P4 RiskUnit bazası {', '.join(stale)} ≠ cari {rid} — RiskUnit API köhnə vəziyyətlə işləyir; "
                "FR4 RiskUnit serveri yenidən başladılaraq təkrarlanmalıdır" if stale else rid)
    pb = config.ROOT / "panel" / "data"
    if pb.exists() and (out / "P5_ranking.csv").exists():
        newest = max((p.stat().st_mtime for p in pb.glob("*.js")), default=0)
        ok = newest >= (out / "P5_ranking.csv").stat().st_mtime
        add("təzəlik:panel/data", "ok" if ok else "xəbərdarlıq", "" if ok else "panel/data P5-dən köhnədir (panel qurulmayıb)")
    df = pd.DataFrame(rows)
    catalog.write_csv(df, "P1_freshness.csv", "core", "Təzəlik və vintaj yoxlaması: P3/P4/V_nfr1/P5/panel ardıcıllığı, "
                      "P1 vintajları (MikroUnit, CAEM, OxLon, IO) və FR4-ün RiskUnit baza id-si")
    return df

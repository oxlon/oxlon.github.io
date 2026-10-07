"""
fr4_bridge — FR4 (yan təsirlər, risk profili, yumşaltma) tək ssenari üçün: policyunit.side_effects.analyse
(qaydalar kitabxanası, avtomatik yan təsir ssenariləri, RiskUnit şərti risk paylanmaları — YALNIZ HTTP —,
yumşaltma təklifləri, KPI girişləri; həssaslıq yalnız keşdən). Nəticə API formatına çevrilir.
Rejimlər: full — hamısı; rules — yalnız qaydalar (+ yumşaltma xəritəsi, RiskUnit-siz; sürətli); none — FR4 yoxdur.
"""
import time

import pu
from az_errors import az_exc


def _records(df):
    if df is None:
        return []
    if isinstance(df, list):
        return df
    return df.astype(object).where(df.notna(), None).to_dict("records")


class Cancelled(Exception):
    pass


def _local_mitigation(items):
    """Rule → mitigation_map rows (no RiskUnit): used in 'rules' mode or when RiskUnit fails."""
    try:
        mm = pu.P("risk_link").load_map()
    except Exception:
        return []
    out = []
    for it in sorted(items, key=lambda x: -x.get("severity", 0)):
        for r in _records(mm[mm["rule_id"] == it["rule_id"]]):
            out.append({"scenario": it["scenario"], "priority": it.get("severity_az"), "source": "yumşaltma xəritəsi",
                        "rule_id": it["rule_id"], "family": it.get("family"), "risk_ids": r.get("risk_ids"),
                        "measure_id": r.get("measures"), "proposal_type": r.get("proposal_type"),
                        "proposal_az": r.get("proposal_az"), "responsible_az": r.get("responsible_az"),
                        "kpi_az": r.get("kpi_az"), "trigger_variant": it.get("variant"), "status": "təklif"})
    seen, uniq = set(), []
    for r in out:
        k = (r["rule_id"], r["proposal_az"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq


def _sources(*tables):
    """Distinct primary sources (risk_link column `esas_menbe`) across the given row lists."""
    out = []
    for rows in tables:
        for r in rows or []:
            v = r.get("esas_menbe") if isinstance(r, dict) else None
            if v and v not in out:
                out.append(v)
    return out


def analyse(s, r, mode="full", risk=True, risk_base=None, step=None, cancelled=lambda: False):
    """-> {status, items, variants, variant_ids, risk_profile, mitigation, kpi_inputs, sensitivity, esas_menbe,
    warnings, timings} via policyunit.side_effects.analyse."""
    out = {"status": "ok", "mode": mode, "items": [], "variants": [], "variant_ids": [], "risk_profile": None,
           "mitigation": [], "kpi_inputs": [], "sensitivity": None, "esas_menbe": [], "warnings": [], "timings": {}}
    if mode == "none":
        out["status"] = "hesablanmadı"
        return out
    if cancelled():
        raise Cancelled()
    step = step or (lambda *a, **k: None)
    SE, RL = pu.P("side_effects"), pu.P("risk_link")
    ctx = {"log": lambda m: step("fr4", str(m).strip()[:200])}
    if mode == "full":
        ctx["client"] = RL.Client(base=risk_base, offline=None if risk else True, timeout=120)
    step("fr4", "Yan təsirlər (FR4): %s" % ("qaydalar + yan təsir ssenariləri + RiskUnit + yumşaltma"
                                            if mode == "full" else "yalnız qaydalar"))
    t0 = time.perf_counter()
    try:
        with pu.ENGINE_LOCK:
            res = SE.analyse(s, r["frame"], ctx, mode)
    except Exception as e:
        out["status"] = "xəta"
        out["warnings"].append("Yan təsirlər hesablanmadı: %s" % az_exc(e))
        out["detail"] = "%s: %s" % (type(e).__name__, str(e)[:500])
        return out
    out["timings"]["side_effects"] = round(time.perf_counter() - t0, 2)
    out["items"] = _records(res.get("side_effects"))
    out["variants"] = _records(res.get("variant_table"))
    out["variant_ids"] = list(res.get("variants") or [])
    prof = _records(res.get("risk_profile"))
    calls = [{"path": p, "status": st, "fetched_at": at} for p, st, at in getattr(ctx.get("client"), "log", [])]
    out["risk_profile"] = {"rows": prof, "status": sorted({str(x.get("status")) for x in prof if x.get("status")}),
                           "calls": calls} if mode == "full" else None
    out["mitigation"] = _records(res.get("mitigation")) if mode == "full" else _local_mitigation(out["items"])
    out["kpi_inputs"] = _records(res.get("kpi_inputs"))
    sens = res.get("sensitivity")
    if isinstance(sens, dict):
        out["sensitivity"] = {"cached": sens.get("cached"), "drivers": sens.get("drivers")}
    out["esas_menbe"] = _sources(prof, out["mitigation"])
    st = res.get("status") or {}
    out["status_detail"] = st
    bad = [k for k, v in st.items() if k.startswith("variant:")]
    if bad:
        out["status"] = "qismən"
        out["warnings"] += ["%s: %s" % (k, st[k]) for k in bad]
    return out

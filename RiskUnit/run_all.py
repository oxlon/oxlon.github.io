"""MİİS §15.5.3 — İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi: tam boru xətti (v2).

    python3 run_all.py              # stored feeds; quarterly backtest only when the quarter has none yet
    python3 run_all.py --fetch      # download ALL live feeds first (FRED/GPR/EPU/USGS/ERA5, AMB, DSK, MN, ARDNF,
                                    #   BFB, IMF food index, market factors for VaR)
    python3 run_all.py --daily      # fast path (≈1–2 min): feeds → upstream store → consensus → daily monitor (D1–D7)
    python3 run_all.py --backtest   # force the NFR1 backtest now
    python3 run_all.py --no-pdf     # skip the PDF export (no Chrome on the machine)

Stage DAG (each stage is timed and logged in output/_run_summary_v2.json; an optional stage that fails is
logged and the run continues on the last good outputs, a core stage that fails stops the run):

  A  data:  spine manifest → [--fetch: feeds, feeds_az, IMF food, market factors] → D1 upstream store
            → D3 consensus → D2/D4 AZ feed status & panel → D5–D7 daily monitor
  B  FR1:   factors (indicators, channels incl. R17/R18, hazards, devaluation, chronology)
  C  CAEM:  C1–C6 (σ-band signals, balance of risks, category map, shock library, transmission check)
  D  NFR1:  quarterly backtest → calibration (non-oil, CPI, Brent, fiscal) read by the simulation
  E  FR2:   joint Monte Carlo — baseline-centred view (scores, heat map) + live-conditioned view
            → distributions, contributions, scores (R01–R19), heat map, GaR cross-check
  F  FR3:   measures, residual risk, levers, stress S1–S8 (+ sign assertion)
  G  V/K:   exposures → VaR/ES (V1–V6) → stochastic DSA (K3) → CaR/CCA (K1–K5), on the baseline-view draws
  H  S/M:   scalability, optimize (when those modules provide run(ctx))
  I         alerts → score history → real-time forecast archive (both views)
  J  FR4:   reports, site, PDF/XLSX/JSON, methodology AUTO blocks (main only)
"""
from __future__ import annotations

import argparse
from pathlib import Path
import importlib
import importlib.util
import json
import sys
import time
import traceback
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from riskunit import backtest, config, factors, feeds, scoring, simulate, spine

SUMMARY = config.OUTPUT / "_run_summary_v2.json"
SUMMARY_DAILY = config.OUTPUT / "_run_summary_daily.json"


def stage(name):
    print(f"[{time.strftime('%H:%M:%S')}] {name}", flush=True)


class Runner:
    """Times and logs each stage; optional stages fail soft (NFR2: never leave half-written scores)."""

    def __init__(self, verbose: bool = True):
        self.rows, self.verbose = [], verbose

    def __call__(self, sid: str, name: str, fn, required: bool = True, check=None):
        """check(out) -> 'ok' | 'xəbərdarlıq: …' | 'xəta: …' propagates per-feed status to the stage (v2.4, audit
        M8: a stage whose feeds all failed must not be 'ok'); a stage exception is always 'xəta'."""
        if self.verbose:
            stage(f"{sid:3s} {name}")
        t = time.time()
        try:
            out, status = fn(), "ok"
            if check is not None:
                try:
                    status = check(out) or "ok"
                except Exception as exc:                            # noqa: BLE001
                    status = f"xəbərdarlıq: status yoxlanılmadı ({type(exc).__name__}: {exc})"[:300]
        except Exception as exc:                                    # noqa: BLE001
            out, status = None, f"xəta: {type(exc).__name__}: {exc}"[:300]
            self.rows.append({"stage": sid, "name": name, "status": status, "seviyye": "xəta",
                              "seconds": round(time.time() - t, 2), "required": required})
            if required:
                raise
            if self.verbose:
                print(f"    ! {status} — son yaxşı nəticələr saxlanılır", flush=True)
                traceback.print_exc(limit=2)
            return None
        lvl = level_of(status)
        self.rows.append({"stage": sid, "name": name, "status": status, "seviyye": lvl,
                          "seconds": round(time.time() - t, 2), "required": required})
        if self.verbose and lvl != "ok":
            print(f"    ! {status}", flush=True)
        return out


def level_of(status: str) -> str:
    s = str(status)
    return "ok" if s == "ok" else ("xəbərdarlıq" if s.startswith("xəbərdarlıq") else "xəta")


def optional_module(name: str):
    """riskunit.<name> if it exists and exposes run(ctx) (modules owned by other agents)."""
    if importlib.util.find_spec(f"riskunit.{name}") is None:
        return None
    m = importlib.import_module(f"riskunit.{name}")
    return m if callable(getattr(m, "run", None)) else None


# ---------------------------------------------------------------- A: data spine + daily monitor
def data_stages(R: Runner, fetch: bool = False, backfill: int = 40, verbose: bool = True, full: bool = True) -> dict:
    from riskunit import consensus, feeds_az, monitor, upstream
    out = {}
    def spine_stage():
        man = spine.manifest()
        man.to_csv(config.OUTPUT / "spine_manifest.csv", index=False)
        return man
    out["manifest"] = R("A0", "məlumat onurğası: yuxarı axın faylları (hash manifesti)", spine_stage)
    glob = [k for k in feeds_az.GLOBAL_FEEDS if k != "azeri_light"]
    if fetch:
        R("A1", "qlobal axınlar (FRED, GPR, EPU, USGS, ERA5)", lambda: feeds.fetch_all(verbose=verbose), False,
          check=lambda rows: feeds_az.stage_level(glob, attempted=rows))
    else:                                          # no fetch: freshness of the stored global feeds still counts
        R("A1", "qlobal axınlar (yükləmə yoxdur — saxlanılmış vintajların təzəliyi)", lambda: None, False,
          check=lambda _: feeds_az.stage_level(glob))
    out["feeds_az"] = R("A2", "Azərbaycan axınları (AMB, DSK, MN, ARDNF, BFB) → D2, D4",
                        lambda: feeds_az.run({"fetch": fetch, "fx_budget": backfill}, verbose=verbose), False,
                        check=lambda o: o.get("stage_status", "ok"))
    stale = upstream.is_stale()
    out["upstream"] = R("A3", "yuxarı axın anbarı (OxLon, Nazirlik, MicroUnit) → D1",
                        lambda: upstream.run({"force": False}, verbose=verbose), False)
    if full or stale or not (config.OUTPUT / "D3_consensus_baselines.csv").exists():
        out["consensus"] = R("A4", "bölmələrarası konsensus və model riski → D3",
                             lambda: consensus.run(verbose=verbose), False)
    out["monitor"] = R("A5", "gündəlik monitor və proqnoz təsiri → D5–D7", lambda: monitor.run(verbose=verbose), False)
    out["upstream_stale"] = stale
    spine.clear_caches()
    return out


def daily_context(fetch: bool = True, backfill: int = 40, verbose: bool = True) -> dict:
    """--daily fast path (used by update.py --daily)."""
    R = Runner(verbose)
    t0 = time.time()
    out = data_stages(R, fetch=fetch, backfill=backfill, verbose=verbose, full=False)
    out.update({"stages": R.rows, "elapsed": time.time() - t0})
    write_summary(out, mode="daily")
    return out


# ---------------------------------------------------------------- B–E: factors, CAEM, backtest, simulation
def _factors_stage():
    ind = factors.indicator_base()
    factors.channels()
    hz = factors.hazards()
    dv = factors.devaluation()
    chron = factors.event_chronology()
    pd.DataFrame([{"acar": k, "deyer": v} for k, v in {
        "eq_lambda_tier1": hz["eq_lambda_tier1"], "eq_lambda_tier2": hz["eq_lambda_tier2"],
        "eq_n_tier1": hz["eq_n_tier1"], "eq_n_tier2": hz["eq_n_tier2"], "eq_years": hz["eq_years"],
        "p_drought": hz["p_drought"], "spi_now": hz["spi_now"], "p_dev_given_crash": dv["p_dev"],
        "deval_nonoil_residual_2015_16": dv["nonoil_residual"], "deval_cpi_passthrough": dv["cpi_passthrough"],
        "deval_trigger_years": ";".join(map(str, dv["trigger_years"])),
        "deval_years": ";".join(map(str, dv["dev_years"]))}.items()]).to_csv(
        config.OUTPUT / "FR1_hazard_parameters.csv", index=False)
    return {"indicators": ind, "hazards": hz, "chronology": chron}


def _backtest_stage(run_backtest):
    do_bt = backtest.due() if run_backtest is None else run_backtest
    if do_bt:
        bt = backtest.run_all()
        return bt["table"], bt["calibration"], True
    reg = pd.read_csv(backtest.REGISTER)
    return reg[reg["rub"] == backtest.quarter()], pd.read_csv(config.OUTPUT / "NFR1_calibration.csv"), False


def _simulation_stage(bid):
    res = simulate.run(view="baseline")
    res_live = simulate.run(view="live")
    dist = simulate.distribution_table(res)
    dist.insert(0, "baseline_id", bid)
    dist.to_csv(config.OUTPUT / "FR2_distribution.csv", index=False, float_format="%.5g")
    dist_live = simulate.distribution_table(res_live)
    dist_live.insert(0, "baseline_id", bid)
    dist_live.to_csv(config.OUTPUT / "FR2_distribution_live.csv", index=False, float_format="%.5g")
    contrib = {k: simulate.contributions(res, k) for k in ("g", "cpi", "fis")}
    pd.concat(contrib.values()).to_csv(config.OUTPUT / "FR2_contributions.csv", index=False, float_format="%.5g")
    lay = []
    for view, r in (("baseline", res), ("live", res_live)):
        for kind, d in r.meta["layering"].items():
            for t, y in enumerate(r.years):
                lay.append({"baxis": view, "gosterici": kind, "il": y, **{k: float(v[t]) for k, v in d.items()},
                            "merkezleme": float(r.meta["centring"][kind][t]),
                            "canli_surusme": float(r.meta["live_shift"][kind][t]) if view == "live" else 0.0})
    pd.DataFrame(lay).to_csv(config.OUTPUT / "FR2_band_layering.csv", index=False, float_format="%.5g")
    for f, d in (("FR2_distribution.csv", "Birgə Monte Karlo paylanması — BAZA MƏRKƏZLİ baxış: müşahidə olunmamış aylar/dövrlər rəsmi "
                                          "proqnozla (Brent — makro fərziyyə); cari ilin (2026) müşahidə olunmuş ayları "
                                          "ilin əvvəlindən faktiki məlumatla sabitlənir, ona görə 2026 medianı rəsmi bazadan "
                                          "fərqlənə bilər; sonrakı illərdə median = rəsmi baza. Skorlar və istilik xəritəsi "
                                          "bununla hesablanır"),
                 ("FR2_distribution_live.csv", "Birgə Monte Karlo paylanması — CANLI ŞƏRTLƏNDİRİLMİŞ baxış: cari ilin "
                                               "müşahidə olunmuş ayları faktiki məlumatla, qalan aylar son müşahidə olunmuş "
                                               "templə; Brent mərkəzi cari bazar qiymətinə şərtləndirilir (median = baza + canlı "
                                               "fərqin deterministik təsiri; D6 ilə uyğun)"),
                 ("FR2_band_layering.csv", "Yelpik qatları: hədəf σ (kalibrlənmiş makro/FR1 yelpiyi), amillərin σ-sı, qalıq σ, "
                                           "mərkəzləmə və canlı sürüşmə — hər baxış, göstərici və il üzrə")):
        spine.register_output(f, "simulate", d, list(pd.read_csv(config.OUTPUT / f, nrows=0).columns), "hər tam dövr")
    return res, res_live, dist, dist_live, contrib


def _scoring_stage(res, gar_validated):
    prev = scoring.previous_scores(config.as_of().isoformat())
    S = scoring.score(res)
    S.to_csv(config.OUTPUT / "FR2_risk_scores.csv", index=False, float_format="%.5g")
    scoring.heatmap(S).to_csv(config.OUTPUT / "FR2_heatmap.csv", index=False)
    gar = simulate.gar_now()
    pd.DataFrame([{"il": gar["year"], "kvantil": q, "deyer": v, "n": gar["n"], "tesdiqlenib_NFR1": gar_validated}
                  for q, v in gar["q"].items()]).to_csv(config.OUTPUT / "FR2_gar_crosscheck.csv", index=False,
                                                        float_format="%.5g")
    return S, prev, gar


def _measures_stage(res, S, ctx):
    from riskunit import measures
    m = measures.load()
    cov = measures.coverage(m)
    if cov.attrs.get("unknown_links"):
        print("   DİQQƏT: reyestrdə olmayan risk ID-ləri:", cov.attrs["unknown_links"])
    resid = measures.residual(S, m)
    measures.track_status(m)
    lev = measures.levers(res)
    stress = measures.stress_scenarios()
    m.to_csv(config.OUTPUT / "FR3_measures_register.csv", index=False)
    cov.to_csv(config.OUTPUT / "FR3_coverage.csv", index=False)
    resid.to_csv(config.OUTPUT / "FR3_residual_risk.csv", index=False, float_format="%.5g")
    lev.to_csv(config.OUTPUT / "FR3_levers.csv", index=False, float_format="%.5g")
    stress.to_csv(config.OUTPUT / "FR3_stress_scenarios.csv", index=False, float_format="%.5g")
    if not (config.OUTPUT / "FR3_historical_analogues.csv").exists():
        measures.analogues().to_csv(config.OUTPUT / "FR3_historical_analogues.csv", index=False, float_format="%.4g")
    bad = simulate.check_stress_signs(stress)
    if len(bad):                                       # FR2 fix (b): economically sensible signs are an invariant
        raise AssertionError("Stress ssenarilərində iqtisadi cəhətdən yanlış işarə:\n" + bad.to_string(index=False))
    ctx.update({"measures": m, "coverage": cov, "residual": resid, "levers": lev, "stress": stress})
    return ctx


def _measures_any(res, S, ctx):
    """FR3 via measures.run(ctx) if the measures owner provides one, else the v1 calls; sign check either way."""
    from riskunit import measures
    if callable(getattr(measures, "run", None)):
        ctx.update({"sim": res, "S": S})
        measures.run(ctx)
        if ctx.get("stress") is None and (config.OUTPUT / "FR3_stress_scenarios.csv").exists():
            ctx["stress"] = pd.read_csv(config.OUTPUT / "FR3_stress_scenarios.csv")
        bad = simulate.check_stress_signs(ctx.get("stress"))
        if len(bad):
            raise AssertionError("Stress ssenarilərində yanlış işarə:\n" + bad.to_string(index=False))
        return ctx
    return _measures_stage(res, S, ctx)


def build_context(run_backtest: bool | None = None, verbose: bool = True, fetch: bool = False,
                  backfill: int = 40, data: bool = True) -> dict:
    t0 = time.time()
    R = Runner(verbose)
    ctx = {"fetch": fetch, "runner": R}
    if data:
        ctx["data"] = data_stages(R, fetch=fetch, backfill=backfill, verbose=verbose)
    bid = spine.baseline_id()
    live = spine.live()
    fr1 = R("B", "FR1 risk amilləri: göstəricilər, kanallar (R17/R18 daxil), təhlükələr, xronologiya", _factors_stage)
    from riskunit import caem
    R("C", "CAEM risk vərəqləri (C1–C6)", lambda: caem.run({"fetch": fetch}), False)
    bt_table, calib, did_bt = R("D", f"NFR1 geriyə doğru sınaq ({backtest.quarter()})", lambda: _backtest_stage(run_backtest))
    gar_rows = bt_table[bt_table["model"].str.startswith("GaR")]
    gar_validated = bool(len(gar_rows)) and bool((gar_rows["netice"] == "keçdi").all())
    res, res_live, dist, dist_live, contrib = R(
        "E1", f"FR2 birgə simulyasiya — baza mərkəzli və canlı baxış ({config.N_SIM:,} ssenari)".replace(",", " "),
        lambda: _simulation_stage(bid))
    S, prev, gar = R("E2", "FR2 skorlama (R01–R19), istilik xəritəsi, GaR yoxlaması", lambda: _scoring_stage(res, gar_validated))
    R("F", "FR3 tədbirlər, qalıq risk, alətlər, stress S1–S8 (+ işarə yoxlaması)", lambda: _measures_any(res, S, ctx))
    ctx["sim"] = res
    from riskunit import car, dsa, exposures, feeds_market, var
    if fetch:
        R("G0", "bazar amilləri (V2)", lambda: feeds_market.run(ctx), False, check=lambda o: o.get("stage_status", "ok"))
    R("G1", "məruz qalmalar (V1)", lambda: exposures.run(ctx), False)
    R("G2", "VaR / ES (V3–V6)", lambda: var.run(ctx), False)
    R("G3", "stoxastik borc davamlılığı (K3)", lambda: dsa.run(ctx), False)
    R("G4", "riskə məruz kapital / CCA (K1, K2, K4, K5)", lambda: car.run(ctx), False)
    for sid, name in (("H1", "scalability"), ("H2", "optimize")):
        mod = optional_module(name)
        if mod is not None:
            R(sid, f"{name} (S*/M*)", lambda mod=mod: mod.run(ctx), False)
    def alerts_stage():
        fs = feeds.feed_status()
        mon = (ctx.get("data") or {}).get("monitor")
        D5 = mon["D5"] if mon else (pd.read_csv(config.OUTPUT / "D5_daily_monitor.csv")
                                    if (config.OUTPUT / "D5_daily_monitor.csv").exists() else None)
        d2p = config.OUTPUT / "D2_feed_status.csv"
        a = scoring.alerts(S, res, fr1["indicators"], ctx.get("measures"), fs, res_live=res_live, monitor=D5,
                           d2=pd.read_csv(d2p) if d2p.exists() else None)
        a.to_csv(config.OUTPUT / "FR2_alerts.csv", index=False)
        scoring.append_history(S)
        backtest.archive_forecast(res, res_live)
        return a, fs
    alerts, fs = R("I", "xəbərdarlıqlar, skor tarixçəsi, real vaxt proqnoz arxivi (hər iki baxış)", alerts_stage)
    M = spine.multipliers()
    upd = config.OUTPUT / "NFR2_update_log.csv"
    ctx.update({"S": S, "res": res, "res_live": res_live, "dist": dist, "dist_live": dist_live,
                "contrib_g": contrib["g"], "contrib_cpi": contrib["cpi"], "contrib_fis": contrib["fis"],
                "alerts": alerts, "indicators": fr1["indicators"], "hazards": fr1["hazards"],
                "chronology": fr1["chronology"], "bt_table": bt_table, "calibration": calib, "backtest_ran": did_bt,
                "gar": gar, "gar_validated": gar_validated, "feed_status": fs, "live": live,
                "baseline": spine.baseline(), "baseline_id": bid, "p": factors.params(), "prev_scores": prev,
                "mult": {k: float(v["rgdpnon"].iloc[0]) for k, v in M.items()},
                "update_log": pd.read_csv(upd) if upd.exists() else None, "elapsed": time.time() - t0,
                "stages": R.rows})
    return ctx


# ---------------------------------------------------------------- run summary (NFR2 / NFR3 audit trail)
def _headline(res, year: int) -> dict:
    j = res.col(year)
    out = {}
    for kind in ("g", "cpi", "fis"):
        x = res.total(kind)[:, j]
        out[kind] = {"baza": round(float(res.base[kind][j]), 3), "p05": round(float(np.quantile(x, 0.05)), 3),
                     "p50": round(float(np.median(x)), 3), "orta": round(float(x.mean()), 3),
                     "p95": round(float(np.quantile(x, 0.95)), 3)}
    out["brent"] = {"merkez": round(float(res.meta["brent_centre"][j]), 2), "baza": round(float(res.brent_base[j]), 2),
                    "p50": round(float(np.median(res.brent[:, j])), 2)}
    return out


def _vintages() -> dict:
    """Feed dates come from ONE source (D2_feed_status.csv, v2.4 audit M8): son_musahide = date of the headline
    value, son_hadise = newest date across the feed's series (e.g. the latest CBAR decision confirming the rate)."""
    v = {}
    d2 = config.OUTPUT / "D2_feed_status.csv"
    try:
        man = feeds.read_manifest()
        ok = man[man.status == "ok"].groupby("feed").tail(1).set_index("feed")
        d = pd.read_csv(d2, dtype=str) if d2.exists() else pd.DataFrame(columns=["feed"])
        d = d.set_index("feed")
        def rec(f):
            r = d.loc[f] if f in d.index else None
            g = lambda k: (str(r[k]) if r is not None and k in r and pd.notna(r[k]) else "")  # noqa: E731
            return {"vintage": str(ok.at[f, "vintage"]) if f in ok.index else "", "son_musahide": g("last_obs"),
                    "son_hadise": g("son_hadise") or (str(ok.at[f, "last_obs"]) if f in ok.index else ""),
                    "tazelik": g("tazelik"), "status": g("status"), "seviyye": g("seviyye")}
        glob = [f for f in d.index if str(d.at[f, "owner_module"]) == "feeds"] if "owner_module" in d else list(ok.index)
        v["axinlar"] = {f: rec(f) for f in glob}
        v["az_axinlar"] = {f: rec(f) for f in d.index if f not in glob}
    except Exception as exc:                                       # noqa: BLE001
        v["axinlar"] = f"oxunmadı: {exc}"
    try:
        man = pd.read_csv(config.OUTPUT / "spine_manifest.csv")
        v["yuxari_axin"] = {r.key: (str(r.sha256)[:12] if isinstance(r.sha256, str) else "yoxdur") for r in man.itertuples()}
        mt = {}
        for key, p in {**config.MACRO_FILES, **config.MICRO_FILES}.items():
            if p.exists():
                mt[key] = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        v["yuxari_axin_mtime"] = mt
    except Exception as exc:                                       # noqa: BLE001
        v["yuxari_axin"] = f"oxunmadı: {exc}"
    return v


def _d6_consistency(c: dict) -> dict:
    """Live view vs the D6 forecast-impact monitor: same FR1 transmission, different Brent gap."""
    try:
        r, sy = c["res_live"], c["res_live"].score_year
        j = r.col(sy)
        D6 = pd.read_csv(config.OUTPUT / "D6_forecast_impact.csv")
        d = D6[(D6["driver"] == "brent") & (D6["source"] == "FR1_multipliers.csv") & (D6["year"] == sy)]
        d6_bal = float(d[d["target_id"] == "fr1:balance_n"]["delta"].iloc[0])
        D5 = pd.read_csv(config.OUTPUT / "D5_daily_monitor.csv")
        spot = float(D5[D5["indicator"] == "brent_spot"]["latest"].iloc[0])
        gdp = float(c["baseline"].at[sy, "fr1_gdp_n"])
        gap_live = float(r.meta["brent_centre"][j] - r.brent_base[j])
        ru_bal = float(r.meta["live_shift"]["fis"][j]) * gdp / 100
        return {"il": sy, "brent_baza": round(float(r.brent_base[j]), 2), "brent_canli_merkez": round(gap_live + r.brent_base[j], 2),
                "brent_spot_D6": spot, "D6_balans_mln_azn": round(d6_bal, 1), "RU_canli_balans_mln_azn": round(ru_bal, 1),
                "D6_mln_azn_per_usd": round(d6_bal / (spot - r.brent_base[j]), 2),
                "RU_mln_azn_per_usd": round(ru_bal / gap_live, 2) if gap_live else None,
                "izah": "eyni FR1 multiplikatorları; D6 spotu saxlayır (şərti ssenari), canlı baxış tərs-MSE mərkəzi"}
    except Exception as exc:                                       # noqa: BLE001
        return {"status": f"hesablanmadı: {exc}"}


def write_summary(c: dict, mode: str = "full", extra: dict | None = None) -> dict:
    stages = c.get("stages", [])
    s = {"yaradildi_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rejim": mode,
         "as_of": config.as_of().isoformat(), "sebeke": "söndürülüb (RISK_NO_NETWORK=1)" if config.no_network() else "açıq",
         "baseline_id": spine.baseline_id(), "muddet_san": round(float(c.get("elapsed", 0.0)), 1),
         "merheleler": stages, "ugursuz": [r for r in stages if level_of(r["status"]) == "xəta"],
         "xeberdarliq_merheleleri": [r for r in stages if level_of(r["status"]) == "xəbərdarlıq"],
         "vintajlar": _vintages()}
    if "res" in c:
        sy = c["res"].score_year
        s["qiymetlendirme_ili"] = sy
        s["bashliq"] = {"baza_merkezli": _headline(c["res"], sy), "canli": _headline(c["res_live"], sy),
                        "izah": {k: simulate.VIEWS[k] for k in simulate.VIEWS}}
        S = c["S"]
        s["yuksek_prioritet"] = list(S[S["prioritet"] == "yüksək"]["risk_id"])
        s["xeberdarliq_sayi"] = int(len(c["alerts"])) if c.get("alerts") is not None else None
        s["stress_isare_yoxlamasi"] = "keçdi" if c.get("stress") is not None and not len(
            simulate.check_stress_signs(c["stress"])) else "yoxlanılmadı"
        s["kalibrləmə"] = simulate.calibration_factors()
        s["D6_uygunluq"] = _d6_consistency(c)
    if extra:
        s.update(extra)
    (SUMMARY_DAILY if mode == "daily" else SUMMARY).write_text(
        json.dumps(s, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return s


def build_panel(verbose: bool = True) -> str:
    """Rebuild the Risk paneli data bundles (panel/build_panel.py, all build checks) so the website shows this run."""
    import subprocess
    script = Path(__file__).resolve().parent / "panel" / "build_panel.py"
    if not script.exists():
        return "panel yoxdur"
    r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=900)
    if verbose and r.returncode:
        print((r.stdout + r.stderr)[-2000:])
    if r.returncode:
        raise RuntimeError(f"panel/build_panel.py çıxış kodu {r.returncode}")
    return "ok"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="bütün canlı axınları əvvəlcə yüklə")
    ap.add_argument("--daily", action="store_true", help="sürətli: axınlar + yuxarı axın + konsensus + monitor (D1–D7)")
    ap.add_argument("--backtest", action="store_true", help="NFR1 sınağını indi məcburi apar")
    ap.add_argument("--no-pdf", action="store_true", help="PDF ixracını keç")
    ap.add_argument("--backfill", type=int, default=40, help="AMB məzənnə arxivi: bu dövrdə ən çox sorğu")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.daily:
        d = daily_context(fetch=a.fetch, backfill=a.backfill)
        print(f"\nGündəlik dövr hazırdır ({time.time() - t0:.1f} san); uğursuz mərhələ: "
              f"{sum(level_of(r['status']) == 'xəta' for r in d['stages'])}, xəbərdarlıq: "
              f"{sum(level_of(r['status']) == 'xəbərdarlıq' for r in d['stages'])}.")
        return d
    c = build_context(run_backtest=True if a.backtest else None, fetch=a.fetch, backfill=a.backfill)
    R = c["runner"]
    from riskunit import docs, report
    out = R("J1", "FR4/NFR3 panellər, PDF, Excel, JSON API", lambda: report.build_all(c, pdf=not a.no_pdf), False) or {}
    R("J2", "metodologiya sənədinin AUTO blokları", lambda: docs.update_methodology(c), False)
    R("J3", "Risk paneli: məlumat paketlərinin yenidən qurulması (panel/build_panel.py)", lambda: build_panel(), False)
    c["elapsed"] = time.time() - t0
    c["stages"] = R.rows
    write_summary(c, "full" + (" + fetch" if a.fetch else ""))
    S = c["S"]
    print(f"\nHazırdır ({c['elapsed']:.1f} san). Baza {c['baseline_id']}, qiymətləndirmə ili {c['res'].score_year}.")
    print(f"Yüksək prioritet: {', '.join(S[S['prioritet'] == 'yüksək']['risk_id'])}; xəbərdarlıq: {len(c['alerts'])}.")
    bad = [r for r in R.rows if level_of(r["status"]) == "xəta"]
    warn = [r for r in R.rows if level_of(r["status"]) == "xəbərdarlıq"]
    print(f"Mərhələlər: {len(R.rows)}, uğursuz: {len(bad)}" + (" — " + "; ".join(r["stage"] for r in bad) if bad else "")
          + f", xəbərdarlıq: {len(warn)}" + (" — " + "; ".join(r["stage"] for r in warn) if warn else ""))
    for k, v in out.items():
        print(f"  {k:16s} {v if v else 'YARADILMADI (Chrome tapılmadı)'}")
    return c


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

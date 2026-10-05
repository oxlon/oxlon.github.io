"""MİİS §15.5.3 — İqtisadi risklərin idarəedilməsi və qərar dəstək sistemi: tam boru xətti.

    python3 run_all.py              # stored feeds; quarterly backtest only when the quarter has none yet
    python3 run_all.py --fetch      # download the live feeds first (FRED, GPR, EPU, USGS, ERA5)
    python3 run_all.py --backtest   # force the NFR1 backtest now
    python3 run_all.py --no-pdf     # skip the PDF export (no Chrome on the machine)

Stages: data spine → FR1 factors → NFR1 backtest (quarterly; writes the calibration the
simulation reads) → FR2 joint simulation and scoring → FR3 measures and stress scenarios →
alerts → archive → FR4/NFR3 reports → methodology document AUTO blocks.
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np
import pandas as pd

from riskunit import backtest, config, docs, factors, feeds, measures, report, scoring, simulate, spine


def stage(name):
    print(f"[{time.strftime('%H:%M:%S')}] {name}", flush=True)


def build_context(run_backtest: bool | None = None, verbose: bool = True) -> dict:
    t0 = time.time()
    say = stage if verbose else (lambda *_: None)
    say("0  məlumat onurğası: makro §15.5.1 + mikro §15.5.2 + canlı axınlar")
    man = spine.manifest()
    man.to_csv(config.OUTPUT / "spine_manifest.csv", index=False)
    bid = spine.baseline_id()
    live = spine.live()

    say("1  FR1 risk amilləri: göstərici bazası, ötürmə kanalları, təhlükələr, xronologiya")
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

    do_bt = backtest.due() if run_backtest is None else run_backtest
    if do_bt:
        say(f"2  NFR1 rüblük geriyə doğru sınaq ({backtest.quarter()})")
        bt = backtest.run_all()
        bt_table, calib = bt["table"], bt["calibration"]
    else:
        say(f"2  NFR1: {backtest.quarter()} üçün sınaq artıq aparılıb — reyestrdən oxunur")
        reg = pd.read_csv(backtest.REGISTER)
        bt_table = reg[reg["rub"] == backtest.quarter()]
        calib = pd.read_csv(config.OUTPUT / "NFR1_calibration.csv")
    gar_rows = bt_table[bt_table["model"].str.startswith("GaR")]
    gar_validated = bool(len(gar_rows)) and bool((gar_rows["netice"] == "keçdi").all())

    say(f"3  FR2 birgə simulyasiya ({config.N_SIM:,} ssenari) və skorlama".replace(",", " "))
    res = simulate.run()
    dist = simulate.distribution_table(res)
    dist.insert(0, "baseline_id", bid)
    dist.to_csv(config.OUTPUT / "FR2_distribution.csv", index=False, float_format="%.5g")
    contrib = {k: simulate.contributions(res, k) for k in ("g", "cpi", "fis")}
    pd.concat(contrib.values()).to_csv(config.OUTPUT / "FR2_contributions.csv", index=False, float_format="%.5g")
    prev = scoring.previous_scores(config.as_of().isoformat())
    S = scoring.score(res)
    S.to_csv(config.OUTPUT / "FR2_risk_scores.csv", index=False, float_format="%.5g")
    scoring.heatmap(S).to_csv(config.OUTPUT / "FR2_heatmap.csv", index=False)
    gar = simulate.gar_now()
    pd.DataFrame([{"il": gar["year"], "kvantil": q, "deyer": v, "n": gar["n"], "tesdiqlenib_NFR1": gar_validated}
                  for q, v in gar["q"].items()]).to_csv(config.OUTPUT / "FR2_gar_crosscheck.csv", index=False,
                                                        float_format="%.5g")

    say("4  FR3 tədbirlər, qalıq risk, stress ssenariləri, alətlər")
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

    say("5  xəbərdarlıqlar, skor tarixçəsi, real vaxt proqnoz arxivi")
    fs = feeds.feed_status()
    alerts = scoring.alerts(S, res, ind, m, fs)
    alerts.to_csv(config.OUTPUT / "FR2_alerts.csv", index=False)
    scoring.append_history(S)
    backtest.archive_forecast(res)

    M = spine.multipliers()
    upd = config.OUTPUT / "NFR2_update_log.csv"
    return {"S": S, "res": res, "dist": dist, "contrib_g": contrib["g"], "contrib_cpi": contrib["cpi"],
            "contrib_fis": contrib["fis"], "alerts": alerts, "indicators": ind, "hazards": hz, "chronology": chron,
            "stress": stress, "levers": lev, "measures": m, "coverage": cov, "residual": resid, "bt_table": bt_table,
            "calibration": calib, "gar": gar, "gar_validated": gar_validated, "feed_status": fs, "live": live,
            "baseline": spine.baseline(), "baseline_id": bid, "p": factors.params(), "prev_scores": prev,
            "mult": {k: float(v["rgdpnon"].iloc[0]) for k, v in M.items()},
            "update_log": pd.read_csv(upd) if upd.exists() else None, "elapsed": time.time() - t0}


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fetch", action="store_true", help="canlı axınları əvvəlcə yüklə")
    ap.add_argument("--backtest", action="store_true", help="NFR1 sınağını indi məcburi apar")
    ap.add_argument("--no-pdf", action="store_true", help="PDF ixracını keç")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.fetch:
        stage("canlı məlumat axınları yüklənir")
        feeds.fetch_all()
    c = build_context(run_backtest=True if a.backtest else None)
    stage("6  FR4/NFR3 panellər, PDF, Excel, JSON API")
    out = report.build_all(c, pdf=not a.no_pdf)
    docs.update_methodology(c)
    S = c["S"]
    print(f"\nHazırdır ({time.time() - t0:.1f} san). Baza {c['baseline_id']}, qiymətləndirmə ili {c['res'].score_year}.")
    print(f"Yüksək prioritet: {', '.join(S[S['prioritet'] == 'yüksək']['risk_id'])}; xəbərdarlıq: {len(c['alerts'])}.")
    for k, v in out.items():
        print(f"  {k:16s} {v if v else 'YARADILMADI (Chrome tapılmadı)'}")
    return c


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

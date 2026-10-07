"""FR1 scenario engine (contract section B): structural macro-sectoral model of Azerbaijan, solved year by year
by damped Gauss-Seidel exactly as in FR1.ipynb (Parts 11-16).

    inputs()                         editable catalogue: exogenous base assumptions 2026-2030 per scenario,
                                     every solver coefficient (value, SE, 95% CI from the registry), levers
    run(overrides, scenario, upstream=None) -> {"series": {id: {year: v}}, "meta", "warnings"}
    selftest()                       run({}) for every scenario reproduces FR1_forecast_full.csv, the accounts
                                     CSVs and the all-scenario contribution / decomposition CSVs (rel. 1e-8)

Default mode 'shock' = the notebook's shock-run convention: each scenario's add-factor path (2025 residuals +
decaying 2026 anchor increments) and its oil-revenue reference path are held, so a changed oil price moves
public investment through F4. Lever mode='reanchor' re-runs the full pipeline (2026 re-anchored on the YTD data
and a new oil-revenue reference). The fan-chart bootstrap is not part of the engine (notebook only).

v2.2 (macro-module adoption): mining deflator on the hydrocarbon export price index + exchange rate; Baseline
oil/gas output on the Ministry plan growth rates; 2026 state investment anchored on the State Investment Programme
(input `sip_n`); levers `income_block` ('share' | 'legs': income by source with DSMF transfers, input `dsmf_add_g`)
and `fiscal_rule` ('F3' | 'nobd': non-oil balance held at its 2025 ratio to non-oil GDP); new outputs gdpnon_n,
hhdisp_n, nobd_pct, exp_pubinv_n, gas_exp_price, xsh_oil, dln_xpi.

v2.3: E3 carries the real wage bill (homogeneity over three terms: the tie keeps ln_pens_r = 1 - ln_gdpnon -
ln_wagebill_r when one of them is overridden); D4 is estimated in USD-volume form (solver coefficients unchanged);
lever `base_addf_decay` now decays the base add-factors at a FIXED half-life (`addf_halflife`, default 1 year) -
no estimated residual autocorrelation is used anywhere in the engine.
"""
import os
import time

import numpy as np
import pandas as pd

from . import base as B
from . import _fr1_run as RUN
from . import _fr1_post as P
from .. import project_root

MODULE = "FR1"
_S = None


def _st():
    global _S
    if _S is None:
        raw = B.load_state(MODULE)
        M = raw['M']
        M['FY'] = [int(y) for y in M['FY']]
        for nm in ('scen_ex', 'ADDF', 'OILREF', 'cred_ref'):
            raw[nm] = {sc: {int(y): v for y, v in d.items()} for sc, d in raw[nm].items()}
        raw['CAL']['defl'] = {k: tuple(v) for k, v in raw['CAL']['defl'].items()}
        raw['CAL']['mkt_defl'] = {k: tuple(v) for k, v in raw['CAL']['mkt_defl'].items()}
        _S = raw
    return _S


def reload():
    global _S
    _S = None
    return _st()


def inputs():
    return _st()['inputs']


def run(overrides=None, scenario="Baseline", upstream=None):
    t0 = time.perf_counter()
    S = _st()
    if scenario not in S['M']['scenarios']:
        raise ValueError(f"naməlum ssenari '{scenario}' (mümkün: {S['M']['scenarios']})")
    ov = B.apply_overrides(S['inputs'], overrides, scenario)
    W = list(ov['warnings'])
    if upstream:
        W.append("FR1 yuxarı axın modulundan asılı deyil — 'upstream' nəzərə alınmadı")
    R = RUN.solve(S, scenario, ov, W)
    ser, _ = RUN.series(S, R)
    if any(k == 'exogenous' and v in ('brent', 'gas_exp_price', 'fx') for k, v in ov['changed']):
        W.append("Real ÜDM zəncirvari üsulla (əvvəlki ilin qiymətləri ilə) hesablanır: neft-qaz qiyməti dəyişdikdə neft-qaz "
                 "sektorunun çəkisi dəyişir. Bazada neft-qaz hasilatı azaldığı üçün aşağı neft qiyməti bu azalmanın real ÜDM-ə "
                 "təsirini zəiflədir və real ÜDM baza ilə müqayisədə arta bilər, halbuki qeyri-neft ÜDM və nominal ÜDM azalır. "
                 "İqtisadi fəallığa təsiri qeyri-neft ÜDM üzrə oxuyun.")
    meta = {"module": MODULE, "scenario": scenario, "years": S['M']['FY'], "last_actual": S['M']['LAST_ACT'],
            "mode": ov['levers'].get('mode', 'shock'), "levers": ov['levers'],
            "changed": [f"{a}:{b}" for a, b in ov['changed']],
            "iterations": {str(y): int(v[0]) for y, v in R['conv'].items()},
            "max_residual": float(max(v[1] for v in R['conv'].values())), **R['info'],
            "seconds": round(time.perf_counter() - t0, 3)}
    return B.make_result(ser, meta=meta, warnings=W)


def run_frames(overrides=None, scenario="Baseline"):
    """Diagnostics / notebook use: the solved frame and post tables as pandas objects."""
    S = _st()
    ov = B.apply_overrides(S['inputs'], overrides, scenario)
    R = RUN.solve(S, scenario, ov, list(ov['warnings']))
    ser, post = RUN.series(S, R)
    return R, post, ser


def _out(name):
    return os.path.join(project_root(), "output", name)


def selftest(modes=("shock", "reanchor"), tol=1e-8):
    S = _st()
    det, ok = {}, True
    for mode in modes:
        for sc in S['M']['scenarios']:
            R, post, ser = run_frames({"levers": {"mode": mode}} if mode != "shock" else {}, sc)
            fc = R['fc'].copy(); fc.index.name = None
            r = {}
            r['forecast_full'] = B.selftest_compare(fc[S['FC_COLS']], _out("FR1_forecast_full.csv"), S['FC_COLS'],
                                                   tol=tol, index_col=0,
                                                   csv_filter=lambda d, sc=sc: d[d.scenario == sc])
            L = pd.read_csv(_out("FR1_accounts_long.csv"))
            L = L[L.scenario == sc]
            mine = pd.DataFrame([dict(key=k[8:].split(':')[0], metric=k[8:].split(':')[1], year=int(y), v=v)
                                 for k, d in ser.items() if k.startswith('fr1:acc:') for y, v in d.items()])
            mg = L.merge(mine, on=['key', 'metric', 'year'], how='outer', indicator=True)
            dif = (mg.value - mg.v).abs()/np.maximum(np.maximum(mg.value.abs(), mg.v.abs()), 1e-10)
            r['accounts_long'] = dict(ok=bool((mg._merge == 'both').all() and dif.max() <= tol),
                                      max_rel_diff=float(dif.max()), n_rows=int(len(mg)),
                                      unmatched=int((mg._merge != 'both').sum()))
            for m in ('real', 'deflator', 'nominal'):
                ref = pd.read_csv(_out(f"FR1_accounts_forecast_{m}.csv"), index_col=[0, 1]).loc[sc]
                lab = {a['key']: a['label'] for a in S['ACCT']}
                raw = pd.DataFrame({lab[k]: post['acc'][k][m] for k in post['acc']}).T
                raw.columns = [str(c) for c in raw.columns]
                raw = raw.reindex(ref.index)
                d = (raw.round(4) - ref).abs().to_numpy().ravel()          # the CSV is written rounded to 4 digits
                du = (raw - ref).abs().to_numpy().ravel()
                both = np.isfinite(d)
                nanok = bool((np.isnan(raw.to_numpy()) == np.isnan(ref.to_numpy())).all())
                okv = (d[both] <= 1e-9) | (du[both] <= 5e-5 + 1e-9)      # rounding-boundary tolerance
                r[f'accounts_forecast_{m}'] = dict(ok=nanok and bool(okv.all()),
                                                   max_abs_diff=float(d[both].max()) if both.any() else 0.0)
            con = post['contrib'].reset_index()
            r['contrib_all'] = B.selftest_compare(con, _out("FR1_gdp_growth_contributions_all.csv"),
                                                  [c for c in con.columns], tol=tol, floor=1e-6,
                                                  csv_filter=lambda d, sc=sc: d[d.scenario == sc].drop(columns='scenario').reset_index(drop=True))
            dec = post['dec']
            r['decomposition_all'] = B.selftest_compare(dec, _out("FR1_sector_decomposition_all.csv"),
                                                        [c for c in dec.columns if c not in ('sector',)], tol=tol, floor=1e-6,
                                                        csv_filter=lambda d, sc=sc: d[d.scenario == sc].drop(columns='scenario').reset_index(drop=True)[dec.columns])
            if mode == 'shock':                           # v2.1: sector allocations (anchored on 2025 shares)
                for nm, fn in (('investment_by_sector', P.investment_by_sector(S, R['fc'], R['CAL'])),
                               ('credit_by_sector', P.credit_by_sector(S, R['fc'], R['alloc']))):
                    eng = pd.DataFrame(fn); eng.index.name = 'year'; eng = eng.reset_index()
                    r[nm] = B.selftest_compare(eng, _out(f"FR1_{nm}.csv"), list(eng.columns), tol=tol,
                                               csv_filter=lambda d, sc=sc: d[d.scenario == sc].drop(columns='scenario').reset_index(drop=True))
            sm = P.accounts_summary(S, post['acc'])
            num = [c for c in sm.columns if c not in ('group', 'entity', 'entity_az', 'unit')]
            r['accounts_summary'] = B.selftest_compare(sm, _out(f"FR1_accounts_summary_{sc.lower()}.csv"),
                                                       ['entity'] + num, tol=tol)
            if sc == 'Baseline' and mode == 'shock':
                r['multipliers'] = _multipliers_check(R['fc'], tol)
            if mode == 'reanchor':
                r['addfactor_sensitivity'] = _addf_sens_check(S, sc, R['fc'], tol)
            good = all(v.get('ok') for v in r.values())
            ok &= good
            det[f"{sc}|{mode}"] = {"ok": good, **{k: {kk: vv for kk, vv in v.items() if kk in ('ok', 'max_rel_diff', 'max_abs_diff', 'n_rows', 'problems', 'unmatched')} for k, v in r.items()}}
    return {"ok": bool(ok), "detail": det}


MULT_EXP = {  # the notebook's Part 14 experiments expressed as engine overrides (shock convention)
    'Brent +10 USD/bbl': {'exogenous': {'brent': {'add': 10}}},
    'State investment +1 bn AZN (real)': {'exogenous': {'istate_add': {'add': 1000}}},
    'Credit easing (-200 bp policy, -100 bp deposit)': {'exogenous': {'polrate': {'add': -2}, 'deprate': {'add': -1}}},
    'Credit easing + judgemental credit->investment overlay': {'exogenous': {'polrate': {'add': -2}, 'deprate': {'add': -1}},
                                                               'levers': {'credit_overlay': True}},
    'External demand +10%': {'exogenous': {'extdem': {'pct': 10}}}}


def _multipliers_check(base, tol):
    """Engine overrides reproduce FR1_multipliers.csv (deviation from the Baseline: %, pp for inflation, mln AZN for the
    budget balance - v2.3.1)."""
    ref_all = pd.read_csv(_out("FR1_multipliers.csv"), index_col=[0, 1])
    mx = 0.0
    for lbl, ov in MULT_EXP.items():
        fc = run_frames(ov, 'Baseline')[0]['fc']; ref = ref_all.loc[lbl]
        for k in ref.columns:
            d = (fc[k] - base[k]) if k in ('infl', 'balance_n') else (fc[k]/base[k] - 1)*100   # v2.3.1: balance in mln AZN
            mx = max(mx, float(np.max(np.abs(d.reindex(ref.index).to_numpy() - ref[k].to_numpy()))))
    return dict(ok=bool(mx <= 1e-8), max_abs_diff=mx, n_rows=int(len(ref_all)))


def _addf_sens_check(S, sc, fc, tol):
    """FR1_addfactor_sensitivity.csv: average growth 2026-2030 with base add-factors held and decaying at a fixed
    half-life (v2.3; re-anchored run with its own oil-revenue reference path, Part 13.1)."""
    ref = pd.read_csv(_out("FR1_addfactor_sensitivity.csv"), index_col=0)[sc]
    fs = run_frames({"levers": {"mode": "reanchor", "base_addf_decay": True}}, sc)[0]['fc']
    H, n, d = S['M']['H_END'], len(S['M']['FY']), S['d25']
    g = lambda f, k: ((f[k][H]/d[k])**(1/n) - 1)*100  # noqa: E731
    eng = {'real GDP, constant base add-factors': g(fc, 'rgdp'),
           'real GDP, base add-factors decay at a fixed half-life': g(fs, 'rgdp'),
           'non-oil GDP, constant base add-factors': g(fc, 'rgdpnon'),
           'non-oil GDP, base add-factors decay at a fixed half-life': g(fs, 'rgdpnon'),
           'add-factor half-life (years)': float(S['M'].get('ADDF_HALFLIFE', 1.0))}
    mx = max(abs(eng[k] - ref[k])/max(abs(ref[k]), 1e-10) for k in eng)
    return dict(ok=bool(mx <= tol), max_rel_diff=float(mx), n_rows=len(eng))

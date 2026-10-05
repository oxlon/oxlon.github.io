# %%
from microlib.engines import base as ENGB
SCN_DATA = [dict(sid=s, market=m, change=c, assumption=a, kind=k, **p) for s, m, c, a, k, p in
            [('S1', 'ICT', SCN[0][2], SCN[0][3], 'entry', dict(dN=1.0)), ('S1', 'MOB', SCN[1][2], SCN[1][3], 'entry', dict(dN=1.0)),
             ('S2', 'CON', SCN[2][2], SCN[2][3], 'merger', dict(s1=0.10, s2=0.05)), ('S2', 'BNK', SCN[3][2], SCN[3][3], 'merger', dict(s1=0.08, s2=0.06)),
             ('S3', 'ACC', SCN[4][2], SCN[4][3], 'cost', dict(t=0.05)), ('S3', 'CEM', SCN[5][2], SCN[5][3], 'cost', dict(t=0.05)),
             ('S4', 'IND', SCN[6][2], SCN[6][3], 'import', dict(m0=0.3, m1=0.4, eta=2.0)), ('S4', 'CEM', SCN[7][2], SCN[7][3], 'import', dict(m0=0.2, m1=0.3, eta=2.0))]
            + [('S5', 'IND', SCN[8 + i][2], SCN[8 + i][3], 'mixed', dict(sigma=float(sg), lam=float(lm))) for i, (sg, lm) in enumerate((sg, lm) for sg in SIG.values() for lm in (0.5, 1.0))]]
assert [(d['sid'], d['market'], d['assumption']) for d in SCN_DATA] == [(s[0], s[1], s[3]) for s in SCN], 'IO scenario list differs from Part 15'
_e005 = {g: {c: float(E005.loc[(g, 2024), c]) for c in CAP} for g in GRP}
_cls24 = {g: {c: float(_cls.loc[g, c]) for c in ['sme', 'micro', 'small', 'medium']} for g in GRP}
_ewh = {g: dict(conc={int(y): float(v) for y, v in (100 - SME.loc[g].sme_output_share).items()},
                lnB={int(y): float(v) for y, v in PA[PA.unit == g].set_index('year').lnB.dropna().items()},
                exit={int(y): float(v) for y, v in PA[PA.unit == g].set_index('year').exit.items() if y != 2022},
                pcm={int(y): float(v) for y, v in PCM_G.PCM.xs(g, level=0).loc[2010:].items()}) for g in GRP}
_bands = {}
for r in FAN.itertuples():
    for m in ['new', 'entry', 'exit', 'N']:
        _bands.setdefault(f"fr12:{PAB[r.panel]}:{m}:{iid(r.unit)}", {})[str(int(r.year))] = [float(getattr(r, f'{m}_p5')), float(getattr(r, f'{m}_p95')), float(getattr(r, f'{m}_baseline'))]
_hist = {}
for r in TIDY[~TIDY.is_forecast & (TIDY.scenario == 'Baseline')].itertuples():
    _hist.setdefault(r.id, {})[str(int(r.year))] = [None if r.value != r.value else float(r.value), bool(r.imputed)]
ENGINE_STATE = dict(
    module='FR12', years=dict(fc=FC_YEARS, last_act=LAST_ACT, orig=dict(ORIG)), scenarios=SCEN, groups=GRP, regions=REGS, region_ids={u: iid(u) for u in REGS},
    group_fr1={g: list(GROUPS[g][2]) for g in GRP},
    hist=dict(rva={c: {str(y): float(FR1H[c].loc[y]) for y in [2024, LAST_ACT]} for c in RVA}, lend_last=float(FR1H.lendrate.loc[LAST_ACT]),
              rcred={str(y): float(FR1H.rcred_tot.loc[y]) for y in [2024, LAST_ACT]}, rgdpnon_last=float(FR1H.rgdpnon.loc[LAST_ACT]),
              reg_out_last={sc: {u: float(_rf[sc][u].loc[LAST_ACT]) for u in REGS} for sc in SCEN}, pcm_last={g: float(PCM_G.PCM.get((g, LAST_ACT))) for g in GRP}),
    rules={f'{k[0]}|{k[1]}': _rule_state(FIN[k], k) for k in [('activity', 'lnB'), ('activity', 'exit'), ('region', 'lnB'), ('region', 'exit'), ('sme', 'lo'), ('sme_emp', 'lo')]},
    alloc=dict(sections=list(SECS), publish=list(MKT), shares={s: {v: float(ALLOC.loc[s, v]) for v in AVAR} for s in SECS},
               h1={s: {v: float(H1RATIO.loc[s, v]) for v in AVAR} for s in SECS}, h1_first_year=2027, nowcast={s: {v: float(NOWC26.loc[s, v]) for v in AVAR} for s in SECS},
               exempt=list(NOW_EXEMPT), now_year=NOW_Y, half_life=HALF_LIFE),
    N0={pn: {u: float(v) for u, v in PANELS[pn][PANELS[pn].year == ORIG[pn]].set_index('unit').N.items()} for pn in PANELS},
    conc=dict(e005=_e005, n_large={g: float(SIZE_G.loc[g, 'large']) for g in GRP}, cls=_cls24, go={g: {str(int(y)): float(v) for y, v in GO_G[g].dropna().items()} for g in GRP},
              va_last={g: float(VAH.loc[LAST_ACT, g]) for g in GRP}, n2024={g: float(PA[(PA.unit == g) & (PA.year == 2024)].N.iloc[0]) for g in GRP},
              capped={g: bool(CAPPED[g]) for g in GRP}, cap=dict(CAP)),
    ew=dict(hist=_ewh, W=dict(W), z_star=float(Z_STAR), dirs=dict(SER_DIR)),
    io=dict(markets={k: dict(name=v['name'], lo=float(v['lo']), up=float(v['up']), rev=None if v['rev'] != v['rev'] else float(v['rev']), source=v['source']) for k, v in MK.items()},
            scenarios=SCN_DATA, eps_grid=EPS_GRID, theta_grid=THETA_GRID, sigma=dict(SIG)),
    bands=_bands, hist_series=_hist,
    inputs=dict(exogenous=EXO, coefficients=COEFS, levers=LEVERS))
ENGB.save_state('FR12', ENGINE_STATE, root=str(BASE))
import importlib, microlib.engines.fr12 as ENG12
ENG12 = importlib.reload(ENG12); ENG12._S = None
_t0 = time.time(); _r0 = ENG12.run({}, 'Baseline'); _te = time.time() - _t0
assert not ENGB.validate_result(_r0, 'FR12'), ENGB.validate_result(_r0, 'FR12')[:5]
ST12 = ENG12.selftest()
display(pd.DataFrame([dict(check=k, ok=v['ok'], max_rel_diff=v['max_rel_diff'], rows=v['n_rows'], problems='; '.join(v['problems'])) for k, v in ST12['detail'].items()]))
_inp = ENG12.inputs()
print(f"engine: {len(_inp['exogenous'])} exogenous paths, {len(_inp['coefficients'])} editable coefficients, {len(_inp['levers'])} levers; {len(_r0['series'])} series; "
      f"run {_te:.2f} s; selftest {'PASSED' if ST12['ok'] else 'FAILED'}")
assert ST12['ok'], 'engine does not reproduce the notebook'

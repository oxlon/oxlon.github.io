"""FR3 v2.3.6 English prose blocks (inline unless noted)."""
from .common import num, pm, RefreshError
from ._fr3_v236_tables import fp

NM = ['average wage', 'non-oil wage', 'private wage', 'state wage', 'oil wage']


def _and(ix):
    w = [NM[i] for i in ix]
    return w[0] if len(w) == 1 else ', '.join(w[:-1]) + ' and ' + w[-1]


def _cnt(n):
    return 'none' if n == 0 else str(n)


def blocks(V, C):
    B = {}
    a, o = C['avg'], C['oil']
    poor = 'poor' if C['ncg'] <= 1 else 'mixed'
    cgx = f" of 5, but not for the {_and(C['cg_not'])}" if C['ncg'] else ''
    B['head'] = (f"Baseline average-wage growth {C['y1']}–{C['yN']} is **{pm(C['nom'])}% a year nominal, {pm(C['real'])}% real**\n"
                 f"(first version +5.26% / +1.19%). Under the forecast's own anchoring rule the 2021–2025 hold-out is **{poor} against constant\n"
                 f"growth**: the model beats a random walk for {C['nrw']} of 5 series and constant growth for {_cnt(C['ncg'])}{cgx} "
                 f"(average wage: Theil U {a['U vs random walk']:.2f} vs random\nwalk, {a['U vs const growth']:.2f} vs constant growth; "
                 f"{pm(a.err_2025, 1)}% level error by 2025).")
    B['bill26'] = f"{pm(C['wbg'], 1)}%, i.e. the wage growth ({pm(C['wg1'], 1)}%)"
    lo, hi, cv = V['gh']
    B['gh'] = f"ADF* {num(hi, 2)} to {num(lo, 2)} against 5% critical values {' / '.join(num(x, 2) for x in sorted(cv, reverse=True))}"
    sel = V['sel'].set_index(['group', 'candidate'])
    ch = sel.loc[('E3', 'prod_non')]
    sp = []
    for cand, lab, extra in [('prod_non + w_oil', '**Oil-sector wage (Dutch disease)** in the private wage: rolling RMSE ', ' for the chosen equation'),
                             ('prod_non + w_state', '**State-wage spillover** into the private wage: ', ''),
                             ('ratio: prod_non + mw', '**Private/state ratio model**: ', '')]:
        r = sel.loc[('E3', cand)]
        tail = ' — no better, and more complex.' if cand == 'prod_non + w_state' and r.rolling_RMSE >= ch.rolling_RMSE else '.'
        sp.append(f"- {lab}{r.rolling_RMSE:.2f}% vs {ch.rolling_RMSE:.2f}%{extra} (DM p = {fp(r.DM_p)}){tail}")
    c, p = V['spill_sp']
    sp.append(f"- **Private-wage spillover into state pay** (OLS levels, with fiscal capacity and the floor): {pm(c, 3)}, p = {p:.3f}.")
    B['spill'] = '\n'.join(sp)
    B['p1'] = f"**{V['p1']:.2f}**"
    Fs, Fw = V['iv_strongF'], V['iv_weakF']
    dw = V['dwh']
    eqn = dict(E1='the average wage', E2='the non-oil wage', E3='the private wage', E4='the state wage')
    B['dwh'] = (f"({Fs[2]} cases, first-stage F {Fs[0]:.0f}–{Fs[1]:.0f}: all four equations without D18)\n"
                f"**Durbin–Wu–Hausman rejects exogeneity in {len(dw)} of {Fs[2]}** ("
                + '; '.join(f"{eqn[e]}, p = {q:.3f}" for e, q in dw) +
                f"); in the D18 variants it is weak\n(F {Fw[0]:.1f}–{Fw[1]:.1f})")
    rm, r0, dmp = V['e3mw_rmse']
    lv, df, dp, l18, p18 = V['e3mw_lev']
    if '(a) FAIL, (b) FAIL' not in V['sel_e3_ev'] or lv >= 0:
        raise RefreshError('FR3 doc: the E3 minimum-wage lever verdict changed - rewrite §3.4 by hand')
    d18, d18se = V['mw_dols_d18']['E3']
    gain = (f"has a lower rolling RMSE for the private wage ({rm:.2f}% vs {r0:.2f}% without it, DM p = {dmp:.2f})" if rm < r0 else
            f"does not improve the private wage's rolling RMSE ({rm:.2f}% vs {r0:.2f}% without it, DM p = {dmp:.2f})")
    B['e3mw'] = (f"In the homogeneous form the minimum wage {gain}, and its sign is **negative**. It fails the **policy-lever coherence "
                 f"rule** on ≤2020 data: (a) level {pm(lv, 3)} with a difference-form estimate of {pm(df, 3)} (p = {dp:.2f}), so there is "
                 f"no theory-consistent level effect and no significant difference-form effect; (b) with the 2019 dummy (D18) the "
                 f"estimate is {pm(l18, 3)} (p = {p18:.2f}; full-sample DOLS with D18 {num(d18, 3)}, s.e. {d18se:.3f}) — a timing "
                 f"artefact of the reform (it raised public pay; private pay did not follow).")
    eg = list(V['eg'].values())
    B['eg'] = f"{min(eg):.2f}–{max(eg):.2f}"
    S = V['sim']
    w = 'a **weak**' if S['e4F'] < 10 else 'a strong'
    j4 = 'not rejected at 5%' if S['e4s'] >= 0.05 else '**rejected**'
    j5 = '**rejected**' if S['e5s'] < 0.05 else 'not rejected at 5%'
    B['sim'] = (f"from {S['e4o']:.3f} (OLS) to {S['e4i']:.3f} but with {w} first stage (F = {S['e4F']:.1f}) and Sargan p = {S['e4s']:.3f}\n"
                f"({j4}); for E5, OLS {S['e5o']:.3f} vs 2SLS {num(S['e5i'], 3)}, Sargan p = {S['e5s']:.3f} ({j5}). These differences "
                f"are large. 3SLS on the four\nforecasting equations (2010–2025, 16 observations) is a cross-check only (state-wage "
                f"minimum-wage coefficient {V['sys3_e4']:.3f})")
    wr = [NM[i] for i in C['cg_worse']]
    br = [NM[i] for i in C['cg_better']]
    dm = ''
    if wr or br:
        dm = (' Against constant growth the DM test (p < 0.10) finds the model significantly '
              + ' and significantly '.join(x for x in [f"*worse* for the {_and(C['cg_worse'])}" if wr else '',
                                                        f"*better* for the {_and(C['cg_better'])}" if br else ''] if x) + '.')
    an = C['anch']
    B['holdtxt'] = (f"**Headline: beats a random walk for {C['nrw']} of 5 (median U {C['mrw']:.2f}) and constant growth for "
                    f"{_cnt(C['ncg'])} of 5 (median U {C['mcg']:.2f}).**{dm} Much of the error comes from anchoring on the\n"
                    f"2020 (COVID-year) residual and from the 2021–22 inflation spike: with the 2018–2020 average residual as anchor (labelled\n"
                    f"sensitivity) the RMSE would be {an[0]:.1f}% (average), {an[1]:.1f}% (non-oil), {an[2]:.1f}% (private), "
                    f"{an[3]:.1f}% (state), {an[4]:.1f}% (oil). Other sensitivities:\nthe unreconciled E1 alone has an average-wage RMSE "
                    f"of {a.raw_equation_RMSE:.1f}%; giving E1 a finite weight gives {a.E1_weighted_RMSE:.1f}%; reconciling *to* E1 "
                    f"{a.E1_fixed_RMSE:.1f}%.\nThe wage bill is not a separate target (its error equals the average-wage error by "
                    f"construction). The oil error is the premium:\nheld at {C['p20']:.2f}× while the actual fell to {C['p25']:.2f}×.")
    B['af'] = ', '.join(f"E{i + 1} {num(x, 3)}" for i, x in enumerate(C['af']))
    fa = C['fac']
    B['fac'] = (f"state {fa['w_state'][0]:.3f} → {fa['w_state'][1]:.3f}, private {fa['w_priv'][0]:.3f} → {fa['w_priv'][1]:.3f}, "
                f"non-oil {fa['w_non'][0]:.3f} → {fa['w_non'][1]:.3f}; the reconciled aggregate differs from E1's own\nprediction by "
                f"{pm(C['e1gap'][0], 1)}% → {pm(C['e1gap'][1], 1)}%. In {C['y1']} the reconciled values are within {C['ncgap']:.1f}% of the nowcasts")
    g, pr = C['mwg'], C['premN']
    B['lev'] = (f"**minimum wage** (the legal {C['y1']} level, {C['mw26']:.0f} AZN, then {g[0]:.0f}% / {g[1]:.0f}% / {g[2]:.0f}% nominal "
                f"growth a year from {C['y1'] + 1}) and the **oil premium\npath** (from the {C['y1']} nowcast value {C['prem26']:.2f}× to "
                f"{pr[0]:.1f}× / {pr[1]:.1f}× / {pr[2]:.1f}× by {C['yN']})")
    r = C['rat']
    cr = f" (passing 1.00 in {C['cross']})" if C['cross'] else ''
    B['bill'] = (f"Baseline wage bill: {C['wb1']:,.0f} mln AZN in {C['y1']} ({pm(C['wbg'], 1)}%) rising to {C['wbN']:,.0f} mln in {C['yN']}. The\n"
                 f"**state/private ratio** is {r[0]:.2f} in {C['y1']} and {r[1]:.2f} in {C['yN']} in the baseline{cr}, {r[2]:.2f} in "
                 f"{C['yN']} in\nthe Adverse and {r[3]:.2f} in the Reform scenario, driven by the minimum wage in the state equation.")
    f1 = C['fr1']
    B['fr1gap'] = (f"{pm(f1[0], 1)}% in {C['y1']} and\n{pm(f1[1], 1)}% in {C['yN']} (baseline); across scenarios the gap is "
                   f"{pm(f1[2], 1)}% to {pm(f1[3], 1)}%")
    hw, rs = C['hw'], C['rmse']
    B['sanity'] = (f"{hw['w_avg'][0]:.1f}% ({C['y1']}) and {hw['w_avg'][1]:.0f}–{hw['w_avg'][2]:.0f}% ({C['y1'] + 1}–{C['yN']}), against "
                   f"a hold-out RMSE of {rs['w_avg']:.1f}%; for the state wage\n{hw['w_state'][1]:.0f}–{hw['w_state'][2]:.0f}% against "
                   f"{rs['w_state']:.1f}%; for the private wage {hw['w_priv'][1]:.0f}–{hw['w_priv'][2]:.0f}% against {rs['w_priv']:.1f}%")
    urw, ucg = o['U vs random walk'], o['U vs const growth']
    rw = f"a random walk beats that mechanism (U {urw:.2f})" if urw > 1 else f"the mechanism beats a random walk (U {urw:.2f})"
    cg = ('constant growth roughly ties' if 0.9 <= ucg <= 1.1 else 'constant growth beats it' if ucg > 1 else 'it beats constant growth')
    lo8, hi8 = V['mw_rng']['E4']
    l3, h3 = V['mw_rng']['E3']
    B['lim'] = (f"The **oil wage** is not forecast by an equation: it is the non-oil wage times a stated premium lever; in the hold-out "
                f"{rw} and {cg} ({ucg:.2f}).\n"
                f"5. **The hold-out is {poor} against constant growth**: under the forecast's own anchoring rule the model beats constant "
                f"growth for {_cnt(C['ncg'])} of five series (average wage U {a['U vs const growth']:.2f}, {pm(a.err_2025, 1)}% by 2025). "
                f"The anchor year matters a great deal (2018–20 average anchor: {an[0]:.1f}%).\n"
                f"6. **Cointegration is not established** for any equation (EG and Gregory–Hansen); t-statistics are descriptive and base\n"
                f"   add-factors are held constant.\n"
                f"7. **Homogeneity is imposed on theory grounds** though rejected for the private wage on the short sample; the "
                f"unrestricted form\n   gives {C['e3u_priv']:.2f}% instead of {C['main_priv']:.2f}% a year private-wage growth.\n"
                f"8. The **minimum-wage effect is imprecise**: state {lo8:.2f}–{hi8:.2f} (forecast {V['mw_dols']['E4']:.3f}; "
                f"{V['mw_dols_d18']['E4'][0]:.3f} with the unscored 2019 break dummy). In the\n   private wage its estimates are negative "
                f"({num(l3, 2)} to {num(h3, 2)}) but fail the lever-coherence rule, so it is excluded there; any true\n"
                f"   private-sector effect is not captured.")
    return B

"""FR3 v2.3.6 doc tables, part 2: equation set (§5), minimum-wage ranges (§3.4), forecast sensitivity (§7)."""
from ._fr3_v236_tables import f
from ._fr3_v236_vals import _coef

EQ = [('E1', 'FR3.E1_w_avg', ['ln_prod_tot']), ('E2', 'FR3.E2_w_non', ['ln_prod_non']),
      ('E3', 'FR3.E3_w_priv', ['ln_prod_non']), ('E4', 'FR3.E4_w_state', ['ln_prod_non', 'ln_rmw']),
      ('E5', 'FR3.E5_w_oil', ['ln_w_non', 'ln_cpi']), ('P1', 'FR3.P1_minwage', ['ln_w_avg'])]
NAMES = dict(
    en=dict(ln_prod_tot='productivity', ln_prod_non='non-oil productivity', ln_rmw='real minimum wage',
            ln_w_non='non-oil wage', ln_cpi='ln CPI', ln_w_avg='average wage'),
    az=dict(ln_prod_tot='məhsuldarlıq', ln_prod_non='qeyri-neft məhsuldarlığı', ln_rmw='real minimum əmək haqqı',
            ln_w_non='qeyri-neft sektoru əmək haqqı', ln_cpi='ln İQİ', ln_w_avg='orta əmək haqqı'))
DEP = dict(
    en=dict(E1='ln real average wage (cross-check)', E2='ln real non-oil wage', E3='ln real private wage',
            E4='ln real state wage', E5='ln nominal oil wage (reference only)', P1='ln minimum wage (reported, not used)'),
    az=dict(E1='ln real orta əmək haqqı (çarpaz yoxlama)', E2='ln real qeyri-neft sektoru əmək haqqı',
            E3='ln real özəl sektor əmək haqqı', E4='ln real dövlət sektoru əmək haqqı',
            E5='ln nominal neft sektoru əmək haqqı (yalnız istinad üçün)', P1='ln minimum əmək haqqı (təqdim olunur, istifadə olunmur)'))
HDR = dict(en='| # | Dependent | Long-run coefficients (HAC se) | estimator, n, df | R² | EG coint p | difference form |',
           az='| # | Asılı dəyişən | Uzunmüddətli əmsallar (HAC s.x.) | qiymətləndirici, n, sərbəstlik dərəcəsi | R² | EG kointeqrasiya p | fərq forması |')


def equations(V, lang):
    R, N = V['R'], NAMES[lang]
    rows = [HDR[lang], '|---|---|---|---|---|---|---|']
    for k, i, drv in EQ:
        e = R[i]
        co = '; '.join(f"{N[d]} {f(_coef(e, d)['coef'], 3)} ({_coef(e, d)['se']:.3f})" for d in drv)
        s = e['sample']
        est = e['estimator'].replace('+-', '±')
        dfm = '—'
        if k not in ('E5', 'P1'):
            D = e['diagnostics']['diff_form']
            parts = []
            for d in drv:
                lo, hi = D['ci'][d]
                flag = ' ⚑' if not lo <= _coef(e, d)['coef'] <= hi else ''
                parts.append(f(D['coef'][d], 3) + flag)
            dfm = '; '.join(parts)
        rows.append(f"| {k} | {DEP[lang][k]} | {co} | {est}, {s['n']}, {s['df_resid']} | {e['fit']['r2']:.3f} | "
                    f"{e['diagnostics']['eg_coint_p']:.3f} | {dfm} |")
    return '\n'.join(rows)


RNG = dict(
    en=dict(hdr='| Equation | range of the minimum-wage elasticity | in the forecast |',
            rows=[('E1', 'aggregate (E1 candidate)', 'no (not selected)'), ('E2', 'non-oil (E2 candidate)', 'no (not selected)'),
                  ('E3', '**private** (E3 candidate)', '**no** — fails the lever-coherence rule; sensitivity only ({e3})'),
                  ('E4', '**state** (E4)', '**yes: {e4}** (DOLS, no dummy; 3SLS {s3}; D18 version {d18} as sensitivity)')]),
    az=dict(hdr='| Tənlik | minimum əmək haqqı elastikliyinin diapazonu | proqnozda |',
            rows=[('E1', 'aqreqat (E1 namizədi)', 'yox (seçilməyib)'), ('E2', 'qeyri-neft (E2 namizədi)', 'yox (seçilməyib)'),
                  ('E3', '**özəl** (E3 namizədi)', '**yox** — rıçaqların uyğunluğu qaydasını ödəmir; yalnız həssaslıq variantı ({e3})'),
                  ('E4', '**dövlət** (E4)', '**bəli: {e4}** (DOLS, fiktiv dəyişənsiz; 3SLS {s3}; D18 versiyası {d18} həssaslıq variantı kimi)')]))


def mw_ranges(V, lang):
    T = RNG[lang]
    kw = dict(e3=f(V['mw_dols']['E3'], 3), e4=f(V['mw_dols']['E4'], 3), s3=f(V['sys3_e4'], 3), d18=f(V['mw_dols_d18']['E4'][0], 3))
    rows = [T['hdr'], '|---|---|---|']
    for eq, lab, use in T['rows']:
        lo, hi = V['mw_rng'][eq]
        r = f"{f(lo, 2)} – {f(hi, 2)}"
        if eq in ('E3', 'E4'):
            r = f"**{r}**"
        rows.append(f"| {lab} | {r} | {use.format(**kw)} |")
    return '\n'.join(rows)


SENS = dict(
    en=dict(hdr='| Variant | average | state | private |',
            lab=['**Main** (joint WLS, E1 cross-check, constant base add-factors)', 'reconciled strictly to E1',
                 'E1 as a weighted constraint', 'base add-factors decaying with the fixed half-life rule (1 year, as FR1/FR4/FR5; no estimated ρ)',
                 'E3 unrestricted (ln CPI elasticity {e3u})', 'E3 with the minimum wage ({e3m}; fails lever coherence)',
                 'E4 unrestricted (ln CPI free)', 'E4 with the 2019 dummy D18 (minimum-wage elasticity {d18}; unscored)']),
    az=dict(hdr='| Variant | orta | dövlət | özəl |',
            lab=['**Əsas variant** (birgə WLS, E1 çarpaz yoxlama, sabit baza düzəliş əmsalları)', 'yalnız E1-ə uyğun dəqiq uzlaşdırma',
                 'çəkili məhdudiyyət kimi E1', 'sabit yarımparçalanma dövrü qaydası ilə (1 il, FR1/FR4/FR5-dəki kimi; qiymətləndirilmiş ρ yoxdur) sönən baza düzəliş əmsalları',
                 'məhdudiyyətsiz E3 (ln İQİ elastikliyi {e3u})', 'minimum əmək haqqı daxil edilmiş E3 ({e3m}; rıçaq uyğunluğu qaydasını ödəmir)',
                 'məhdudiyyətsiz E4 (ln İQİ sərbəst)',
                 '2019-cu il fiktiv dəyişənli (D18) E4 (minimum əmək haqqı elastikliyi {d18}; proqnoz dəqiqliyi qiymətləndirilməyib)']))
SENS_COLS = ['main', 'reconciled TO E1', 'E1 as a weighted', 'decay', 'E3 unrestricted', 'E3 with the minimum wage',
             'E4 unrestricted', '2019 dummy']


def e3u(V):
    return _coef(V['R']['FR3.S_E3_unrestricted'], 'ln_cpi')['coef']


def sensitivity(V, lang):
    S, T = V['sens'], SENS[lang]
    kw = dict(e3u=f(e3u(V), 3), e3m=f(V['mw_dols']['E3'], 3), d18=f(V['mw_dols_d18']['E4'][0], 3))
    rows = [T['hdr'], '|---|---|---|---|']
    for key, lab in zip(SENS_COLS, T['lab']):
        c = [x for x in S.columns if key in x]
        assert len(c) == 1, (key, c)
        v = [S.loc[r, c[0]] for r in ['average wage', 'state sector', 'private sector']]
        rows.append(f"| {lab.format(**kw)} | " + ' | '.join(f(x, 2) for x in v) + ' |')
    return '\n'.join(rows)

# %%
# firm attributes, the annual panel and revenues. Data-generating process (stated, for the pipeline test only):
# ln size_it = mu_i - gamma_s * e_i + 0.25 * shock_it - 0.7 * [age < 2];  mu_i ~ Pareto(alpha_s) for large firms (low alpha =
# concentrated: mining, utilities, telecom, finance), N(0, 0.8) otherwise; e_i ~ N(0, 0.2) is the cost-efficiency deviation,
# average variable cost avc_i = v_s * exp(e_i). Revenue of each class in each section-year is scaled to its calibration
# target, so totals are exact and only the distribution across firms is random.
ALPHA = dict(A=1.8, B=1.05, C=1.4, D=1.05, E=1.3, F=1.6, G=2.5, H=1.3, I=2.8, J=1.15, K=1.2, L=1.8, M=1.8, N=1.8, O=1.5, P=2.0, Q=1.8, R=1.8, S=2.2, U=1.5)
GAMMA = {s: float(g) for s, g in zip(SECS, rng_s.choice([1.0, 2.0, 3.0], len(SECS)))}
REC['nace2'] = [rng_s.choice(DIV[s], p=([.1, .3, .6] if s == 'G' else None)) for s in REC.sec]
_o = [(l, n) for _, l, n in sheet_rows(DDIR / 'st_units' / '1_2_en.xls') if l and len(n) >= 10]
_own = {}
for s in SECS:
    try:
        n = _o[match_unique([l for l, _ in _o], f'(?:{SECT[s][1]})', s)][1]; n = [0.0 if v != v else v for v in n]
        _own[s] = np.array([n[0], n[2], max(n[4] - n[6] - n[8], 0), n[6], n[8]], float)
    except AssertionError:
        _own[s] = np.array([1, 0, 0, 0, 0], float) if s in ('O', 'U') else np.array([.05, .01, .8, .1, .04])
def own_draw(s, size):
    p = _own[s] / _own[s].sum()
    if size == 'large' and s in ('B', 'D', 'E', 'H'): p = p * np.array([4, 1, 1, 1, 1]); p = p / p.sum()
    return OWN[int(rng_s.choice(5, p=p))]
REC['ownership'] = [own_draw(s, z) for s, z in zip(REC.sec, REC.size_class)]
REC['legal_form'] = np.where(REC.ownership == 'state', 'state enterprise', np.where(REC.size_class.isin(['large', 'medium']), rng_s.choice(['JSC', 'LLC'], len(REC), p=[.3, .7]), 'LLC'))
REC['mu'] = np.where(REC.size_class == 'large', np.log(rng_s.pareto(np.array([ALPHA[s] for s in REC.sec])) + 1.0) * 1.5, rng_s.normal(0, 0.8, len(REC)))
REC['e'] = rng_s.normal(0, 0.2, len(REC))
REC['reg_date'] = pd.to_datetime(REC.reg_year.astype(str) + '-01-01') + pd.to_timedelta(rng_s.integers(0, 365, len(REC)), unit='D')
REC['liq_date'] = pd.NaT
_l = REC.liq_year > 0
_ld = pd.to_datetime(REC.loc[_l, 'liq_year'].astype(str) + '-12-31') - pd.to_timedelta(rng_s.integers(0, 365, int(_l.sum())), unit='D')
REC.loc[_l, 'liq_date'] = np.maximum(_ld.values, REC.loc[_l, 'reg_date'].values)
# annual panel: one row per record and year it is registered (status 'liquidated' in the year of liquidation)
y0 = np.maximum(REC.reg_year.to_numpy(), SY[0]); y1 = np.where(REC.liq_year > 0, REC.liq_year, SY[-1])
nrep = np.maximum(y1 - y0 + 1, 0); idx = np.repeat(REC.index.to_numpy(), nrep)
SYN = REC.loc[idx].reset_index(drop=True)
SYN['year'] = np.concatenate([np.arange(a, b + 1) for a, b in zip(y0, y1) if b >= a])
SYN['status'] = np.where(SYN.liq_year == SYN.year, 'liquidated', 'active')
SYN['age'] = SYN.year - SYN.reg_year
SHOCK_SD, YOUNG_SIZE_PEN, YOUNG_SIZE_AGE = 0.25, 0.7, 2          # true parameters (recovered in 17.7 (g))
SYN['lnsize'] = SYN.mu - SYN.sec.map(GAMMA) * SYN.e + SHOCK_SD * rng_s.normal(0, 1, len(SYN)) - YOUNG_SIZE_PEN * (SYN.age < YOUNG_SIZE_AGE)
# revenue targets: national-accounts output by section, SME shares and class split by activity group (012)
def sme_target(g, y):
    if (g, y) in E012.index: return E012.loc[(g, y)]
    if y == 2021: return (E012.loc[(g, 2020)][['sme', 'micro', 'small', 'medium']] + E012.loc[(g, 2022)][['sme', 'micro', 'small', 'medium']]) / 2
    return E012.loc[(g, 2024)]
SYN['rev_share'] = 0.0
for (s, y, z), g in SYN.groupby(['sec', 'year', 'size_class']):
    t = sme_target(SECT[s][3], y)
    cls = (100 - t['sme']) / 100 if z == 'large' else t[z] / 100
    T_ = float(NA.loc[(s, y), 'GO']) * 1000 * cls if (s, y) in NA.index else 0.0
    x = np.exp(g.lnsize - g.lnsize.max()); SYN.loc[g.index, 'revenue'] = T_ * x / (g.weight * x).sum()
SYN['revenue'] = SYN.revenue.fillna(0.0)
_v = {s: float(np.clip(1 - NA.loc[(s, LAST_ACT), 'PCM'] / 100 - 0.05, 0.3, 0.9)) if (s, LAST_ACT) in NA.index else 0.7 for s in SECS}
SYN['cost_of_sales'] = SYN.revenue * np.clip(SYN.sec.map(_v) * np.exp(SYN.e), 0.15, 0.98)
SYN['operating_costs'] = SYN.revenue * rng_s.uniform(0.02, 0.07, len(SYN))
_emp = {'micro': (1, 10), 'small': (11, 50), 'medium': (51, 250)}
SYN['employees'] = [float(rng_s.integers(*_emp[z], endpoint=True)) if z in _emp else float(251 + rng_s.lognormal(5.0, 1.0)) for z in SYN.size_class]
# employees of large units scaled so that the SME share of employees matches 013 (nearest published year)
SYN['grp'] = SYN.sec.map(lambda s: SECT[s][3])
for (g, y), d in SYN.groupby(['grp', 'year']):
    yy = min(E013.xs(g, level=0).index, key=lambda t: abs(t - y)); sh = E013.loc[(g, yy), 'sme'] / 100
    sme = d.size_class != 'large'; E_sme = (d.weight * d.employees)[sme].sum()
    big = d[~sme]
    if len(big) and 0 < sh < 1:
        need = E_sme * (1 - sh) / sh; base = np.sqrt(big.revenue.clip(lower=1e-6)); base = base / (big.weight * base).sum()
        SYN.loc[big.index, 'employees'] = np.round(np.maximum(need * base, 251.0))
SYN['exports'] = np.where(SYN.sec.isin(['B', 'C']) & SYN.size_class.isin(['large', 'medium']), SYN.revenue * rng_s.uniform(0, 0.5, len(SYN)), 0.0)
SYN['product_codes'] = ''
SYN['registration_date'] = SYN.reg_date.dt.strftime('%Y-%m-%d'); SYN['liquidation_date'] = pd.to_datetime(SYN.liq_date).dt.strftime('%Y-%m-%d')
SYN.insert(0, 'data_status', SYN_STATUS)
BR_COLS = ['data_status'] + [f for f in BR_SCHEMA.field if f != 'data_status']
SYN = SYN[BR_COLS].copy()
for c in ['revenue', 'cost_of_sales', 'operating_costs', 'exports']: SYN[c] = SYN[c].round(3)
print(f'SYNTHETIC register: {len(SYN):,} rows, {SYN.firm_id.nunique():,} records ({SYN.groupby("year").weight.sum().iloc[-1]:,.0f} enterprises in {SY[-1]}), '
      f'{SYN.nace2.map(DIV2SEC).nunique()} sections, {SYN.nace2.nunique()} divisions, {SYN.region.nunique()} regions, {SY[0]}-{SY[-1]}')

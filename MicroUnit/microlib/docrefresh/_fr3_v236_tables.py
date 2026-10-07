"""FR3 v2.3.6 doc tables (EN and AZ share the layout; tables use a decimal point, AZ a space thousands separator)."""
import pandas as pd

from .common import MINUS, RefreshError
from ._fr3_v236_vals import HV, SC

L = dict(
    en=dict(prod_tot='productivity', prod_non='non-oil productivity', mw='minimum wage', w_state='state wage',
            w_oil='oil wage (Dutch disease)', exp_pe='fiscal capacity', ratio='ratio to the state wage: ',
            yes='yes', NO='**NO**', rej='rejected', nrej='not rejected', excl='excluded',
            hom_hdr='| Equation (drivers) | sum of price elasticities ≤2020 (se) | HAC-F p ≤2020 | sum / p ≤2025 | test result |',
            hom_rows=[('E1', 'prod_tot', 'E1 aggregate (productivity)'), ('E2', 'prod_non', 'E2 non-oil (non-oil productivity)'),
                      ('E3', 'prod_non', 'E3 private (non-oil productivity)'),
                      ('E4', 'prod_non + mw', 'E4 state (non-oil productivity, minimum wage)'),
                      ('E5', 'w_non', 'E5 oil (non-oil wage; reference only)')],
            h_rej='**rejected**', h_lp='not rejected (low power)', h_full='not rejected ≤2020 (low power); rejected on the full sample',
            h_e5r='rejected — E5 not used to forecast', h_e5n='not rejected — E5 not used to forecast',
            sel_hdr='| Group | Candidate | lever coherent | homogeneity test ≤2020 | rolling RMSE % | DM p vs lowest RMSE | chosen |',
            ho_hdr='| Variable | model RMSE | U vs random walk | U vs constant growth | DM p vs RW / CG | 2025 level error |',
            ho_lab=['**average wage**', 'non-oil wage', 'private wage', 'state wage', 'oil wage (non-oil × premium lever)'],
            now_hdr='| Series | 2025 | 2026 nowcast | growth | backtest RMSE | old y/y rule |',
            now_lab=dict(w_avg='average wage', w_oil='oil sector', w_non='non-oil sector', w_state='state sector', w_priv='private sector'),
            res_hdr='| Baseline | 2025 | 2030 | nominal % p.a. | real % p.a. |',
            res_lab={'average wage': 'Average wage', 'non-oil sector': 'Non-oil sector', 'state sector': 'State sector',
                     'private sector': 'Private sector', 'oil sector': 'Oil sector'},
            sc_hdr='| | Baseline | Adverse | Reform |',
            sc_rows=['Average wage, nominal % p.a.', 'Average wage, **real** % p.a.', 'Real non-oil wage % p.a.',
                     'Real private wage % p.a.', 'Real state wage % p.a.', 'Real oil wage % p.a.'],
            fan_hdr='| Baseline, {y} | 5% | 25% | median | 75% | 95% | central |',
            fan_rows=[('w_avg', 'level', 'Average wage, AZN'), ('w_avg', 'growth_pct', 'Average wage growth in {y}, %'),
                      ('w_state', 'level', 'State wage, AZN'), ('w_priv', 'level', 'Private wage, AZN'),
                      ('w_oil', 'level', 'Oil wage, AZN')]),
    az=dict(prod_tot='məhsuldarlıq', prod_non='qeyri-neft məhsuldarlığı', mw='minimum əmək haqqı', w_state='dövlət sektoru əmək haqqı',
            w_oil='neft sektoru əmək haqqı ("Holland xəstəliyi")', exp_pe='fiskal imkanlar', ratio='dövlət sektoru əmək haqqına nisbət: ',
            yes='bəli', NO='**XEYR**', rej='rədd edilib', nrej='rədd edilməyib', excl='çıxarılıb',
            hom_hdr='| Tənlik (amillər) | qiymət elastiklikləri cəmi ≤2020 (s.x.) | HAC-F p ≤2020 | cəm / p ≤2025 | test nəticəsi |',
            hom_rows=[('E1', 'prod_tot', 'E1 aqreqat (məhsuldarlıq)'), ('E2', 'prod_non', 'E2 qeyri-neft (qeyri-neft məhsuldarlığı)'),
                      ('E3', 'prod_non', 'E3 özəl (qeyri-neft məhsuldarlığı)'),
                      ('E4', 'prod_non + mw', 'E4 dövlət (qeyri-neft məhsuldarlığı, minimum əmək haqqı)'),
                      ('E5', 'w_non', 'E5 neft (qeyri-neft əmək haqqı; yalnız istinad üçün)')],
            h_rej='**rədd edilir**', h_lp='rədd edilmir (aşağı güc)', h_full='≤2020 rədd edilmir (aşağı güc); tam nümunədə rədd edilir',
            h_e5r='rədd edilir — E5 proqnozda istifadə olunmur', h_e5n='rədd edilmir — E5 proqnozda istifadə olunmur',
            sel_hdr='| Qrup | Namizəd | rıçaq uyğundur | homogenlik testi ≤2020 | sürüşən RMSE % | ən aşağı RMSE-yə qarşı DM p | seçilib |',
            ho_hdr='| Dəyişən | model RMSE | təsadüfi gəzişməyə qarşı U | sabit artıma qarşı U | DM p: təsadüfi gəzişmə / sabit artım | 2025-ci il səviyyə xətası |',
            ho_lab=['**orta əmək haqqı**', 'qeyri-neft sektoru əmək haqqı', 'özəl sektor əmək haqqı', 'dövlət sektoru əmək haqqı',
                    'neft sektoru əmək haqqı (qeyri-neft × mükafat rıçağı)'],
            now_hdr='| Sıra | 2025 | 2026 cari qiymətləndirmə | artım | geriyə test RMSE | köhnə y/y qaydası |',
            now_lab=dict(w_avg='orta əmək haqqı', w_oil='neft sektoru', w_non='qeyri-neft sektoru', w_state='dövlət sektoru', w_priv='özəl sektor'),
            res_hdr='| Əsas | 2025 | 2030 | nominal, illik % | real, illik % |',
            res_lab={'average wage': 'Orta əmək haqqı', 'non-oil sector': 'Qeyri-neft sektoru', 'state sector': 'Dövlət sektoru',
                     'private sector': 'Özəl sektor', 'oil sector': 'Neft sektoru'},
            sc_hdr='| | Əsas | Mənfi | İslahat |',
            sc_rows=['Orta əmək haqqı, nominal, illik %', 'Orta əmək haqqı, **real**, illik %', 'Real qeyri-neft sektoru əmək haqqı, illik %',
                     'Real özəl sektor əmək haqqı, illik %', 'Real dövlət sektoru əmək haqqı, illik %', 'Real neft sektoru əmək haqqı, illik %'],
            fan_hdr='| Əsas ssenari, {y} | 5% | 25% | median | 75% | 95% | mərkəzi proqnoz |',
            fan_rows=[('w_avg', 'level', 'Orta əmək haqqı, AZN'), ('w_avg', 'growth_pct', '{y}-cu ildə orta əmək haqqının artımı, %'),
                      ('w_state', 'level', 'Dövlət sektoru əmək haqqı, AZN'), ('w_priv', 'level', 'Özəl sektor əmək haqqı, AZN'),
                      ('w_oil', 'level', 'Neft sektoru əmək haqqı, AZN')]))


def f(v, d=2, lang='en', sign=False):
    s = f"{v:+,.{d}f}" if sign else f"{v:,.{d}f}"
    if lang == 'az':
        s = s.replace(',', ' ')
    return s.replace('-', MINUS)


def fp(p):
    return f"{p:.3f}" if p < 0.01 else f"{p:.2f}"


def cand(c, T):
    pre = ''
    if c.startswith('ratio: '):
        pre, c = T['ratio'], c[7:]
    return pre + ' + '.join(T[x] for x in c.split(' + '))


def chosen_rows(V):
    ids = set(V['R'])
    out = {}
    for r in V['sel'].itertuples():
        g = r.group + ('r' if r.candidate.startswith('ratio: ') else '')
        key = 'FR3.C_' + g + '_' + r.candidate.replace('ratio: ', '').replace(' + ', '_')
        if key not in ids:
            if r.group in out:
                raise RefreshError(f'FR3 doc: two chosen candidates in {r.group}')
            out[r.group] = r.candidate
    return out


def homog(V, lang):
    T = L[lang]
    hb = {(r['eq'], r['drivers']): r for r in V['hb_rows']}
    rows = [T['hom_hdr'], '|---|---|---|---|---|']
    for eq, drv, lab in T['hom_rows']:
        r = hb[(eq, drv)]
        p20, p25 = r['HAC-F p (<=2020)'], r['HAC-F p (<=2025)']
        if eq == 'E5':
            res = T['h_e5r'] if p20 < 0.05 else T['h_e5n']
        else:
            res = T['h_rej'] if p20 < 0.05 else (T['h_full'] if p25 < 0.05 else T['h_lp'])
        rows.append(f"| {lab} | {r['sum of price elast. (<=2020)']:.3f} ({r['se']:.3f}) | {p20:.3f} | "
                    f"{r['sum (<=2025)']:.3f} / {p25:.3f} | {res} |")
    return '\n'.join(rows)


def select(V, lang):
    T, ch = L[lang], chosen_rows(V)
    rows = [T['sel_hdr'], '|---|---|---|---|---|---|---|']
    for r in V['sel'].itertuples():
        c = cand(r.candidate, T)
        lev = '—' if 'mw' not in r.candidate.split(' + ') else (T['yes'] if r.lever_coherent == 'yes' else T['NO'])
        hom = T['rej'] if r.homogeneity_test == 'rejected' else T['nrej']
        dm = '—' if pd.isna(r.DM_p) else fp(r.DM_p)
        rm = f"{r.rolling_RMSE:.2f}"
        is_ch = ch[r.group] == r.candidate
        mark = '✓' if is_ch else (T['excl'] if r.lever_coherent != 'yes' else '')
        if is_ch:
            c, rm = f"**{c}**", f"**{rm}**"
        rows.append(f"| {r.group} | {c} | {lev} | {hom} | {rm} | {dm} | {mark} |".replace('|  |', '| |'))
    return '\n'.join(rows)


def holdout(V, lang):
    T, h = L[lang], V['ho']
    rows = [T['ho_hdr'], '|---|---|---|---|---|---|']
    for i, v in enumerate(HV):
        r = h.loc[v]
        u1, u2 = f"{r['U vs random walk']:.2f}", f"{r['U vs const growth']:.2f}"
        if i == 0:
            u1, u2 = f"**{u1}**", f"**{u2}**"
        rows.append(f"| {T['ho_lab'][i]} | {r.model_RMSE:.1f}% | {u1} | {u2} | {fp(r.DM_p_vs_rw)} / {fp(r.DM_p_vs_cg)} | "
                    f"{f(r.err_2025, 1, lang, True)}% |")
    return '\n'.join(rows)


def nowcast(V, lang):
    T, n = L[lang], V['now']
    rows = [T['now_hdr'], '|---|---|---|---|---|---|']
    for k in ['w_avg', 'w_oil', 'w_non', 'w_state', 'w_priv']:
        r = n.loc[k]
        rows.append(f"| {T['now_lab'][k]} | {f(r.full_2025, 1, lang)} | {f(r.nowcast, 1, lang)} | {f(r['growth_2026_%'], 2, lang, True)}% | "
                    f"±{r.rmse_avg_ratio:.1f}% | {f(r.nowcast_old_yoy, 1, lang)} |")
    return '\n'.join(rows)


def results(V, lang):
    T, s = L[lang], V['sum'].set_index(['scenario', 'breakdown'])
    rows = [T['res_hdr'], '|---|---|---|---|---|']
    for i, b in enumerate(['average wage', 'non-oil sector', 'state sector', 'private sector', 'oil sector']):
        r = s.loc[('Baseline', b)]
        g1, g2 = f(r.nominal_growth_avg_pct, 2, lang, True), f(r.real_growth_avg_pct, 2, lang, True)
        if i == 0:
            g1, g2 = f"**{g1}**", f"**{g2}**"
        rows.append(f"| {T['res_lab'][b]} | {f(r.nominal_2025, 1, lang)} | {f(r.nominal_2030, 1, lang)} | {g1} | {g2} |")
    rows += ['', T['sc_hdr'], '|---|---|---|---|']
    spec = [('average wage', 'nominal'), ('average wage', 'real'), ('non-oil sector', 'real'), ('private sector', 'real'),
            ('state sector', 'real'), ('oil sector', 'real')]
    for lab, (b, k) in zip(T['sc_rows'], spec):
        rows.append(f"| {lab} | " + ' | '.join(f(s.loc[(sc, b), f'{k}_growth_avg_pct'], 2, lang) for sc in SC) + ' |')
    return '\n'.join(rows)


def fan(V, lang):
    T, F = L[lang], V['fan']
    y = int(F.year.max())
    b = V['fc'].loc['Baseline']
    rows = [T['fan_hdr'].format(y=y), '|---|---|---|---|---|---|---|']
    for var, meas, lab in T['fan_rows']:
        r = F[(F.variable == var) & (F.measure == meas) & (F.year == y)].iloc[0]
        q = [r.q05, r.q25, r.q50, r.q75, r.q95]
        if meas == 'level':
            cells = [f(x, 0, lang) for x in q] + [f(r.central, 0, lang)]
        else:
            cen = (b.loc[y, var] / b.loc[y - 1, var] - 1) * 100
            cells = [f(x, 1, lang) for x in q] + [f(cen, 1, lang)]
        rows.append(f"| {lab.format(y=y)} | " + ' | '.join(cells) + ' |')
    return '\n'.join(rows)

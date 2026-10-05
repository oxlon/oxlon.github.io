# %% [markdown]
# ### 17.2 Hesablama mühərriki
#
# | Blok | Göstəricilər |
# |---|---|
# | Likvidlik | cari likvidlik əmsalı CA/STL; tez likvidlik əmsalı (CA − ehtiyatlar)/STL; mütləq (pul vəsaitləri üzrə) likvidlik əmsalı |
# | Ödəmə qabiliyyəti / borc yükü | borc/kapital (STL+LTL)/E; xüsusi kapital əmsalı E/TA; faiz ödənişinin örtülməsi EBIT/faiz |
# | Rentabellik, DuPont | ROE = (NP/Gəlir) × (Gəlir/TA) × (TA/E) — eynilik yoxlanılır; ROA, EBIT marjası |
# | Dövriyyə | aktivlərin dövriyyəsi; ehtiyatların dövriyyəsi (satışın maya dəyəri/ehtiyatlar); debitor borclarının günlərlə dövriyyəsi |
# | Maliyyə çətinliyi | **Altman Z''-göstəricisi, inkişaf etməkdə olan bazarlar variantı**: 3.25 + 6.56·(CA−CL)/TA + 3.26·RE/TA + 6.72·EBIT/TA + 1.05·E/TL; zonalar: təhlükəsiz > 5.85, boz 4.35–5.85, çətinlik < 4.35. Əmsallar və hədlər Altman (2005) mənbəsindən dərc olunduğu kimi götürülür — heç bir Azərbaycan məlumatı üzrə **qiymətləndirilmir** |
# | Səmərəlilik | əmək məhsuldarlığı (bir işçiyə düşən gəlir); müşahidə olunan xərc payları ilə (əmək = əmək haqqı fondu/gəlir, materiallar = əmək haqları çıxılmaqla satışın maya dəyəri/gəlir, kapital = qalıq) sahə-il ortasına nisbətən çoxtərəfli Törnqvist TFP indeksi — məhsuldarlığın hərəkət qanunu qiymətləndirilmir |
# | Bazar mövqeyi | NACE × region və NACE daxilində paylar; hər xana üzrə HHI və CR4; kohortlar üzrə giriş, çıxış, sağ qalma |
# | Müqayisəli qiymətləndirmə | ROA, əmək məhsuldarlığı və Z''-in NACE × ölçü qrupu üzrə həmkarlar qrupu daxilində persentil dərəcəsi |
# | Proqnoz | müəssisənin gəliri = A qatının sahə proqnozu × proqnozlaşdırılan pay; payın artımı **yalnız gecikmiş amillərlə** (nisbi məhsuldarlıq, nisbi borc yükü) amillər modelindən; paylar sahə daxilində yenidən normallaşdırılır ki, cəmi vahidə bərabər olsun |

# %%
def ratios(df):
    r = pd.DataFrame(index=df.index)
    tl = df.st_liabilities + df.lt_liabilities
    safe = lambda a, b: a / b.where(b.abs() > 1e-9)
    r['current_ratio'] = safe(df.current_assets, df.st_liabilities)
    r['quick_ratio'] = safe(df.current_assets - df.inventories, df.st_liabilities)
    r['cash_ratio'] = safe(df.cash, df.st_liabilities)
    r['debt_to_equity'] = safe(tl, df.equity); r['equity_ratio'] = safe(df.equity, df.total_assets)
    r['interest_cover'] = safe(df.ebit, df.interest)
    r['net_margin'] = safe(df.net_profit, df.revenue); r['asset_turnover'] = safe(df.revenue, df.total_assets)
    r['equity_multiplier'] = safe(df.total_assets, df.equity); r['roe'] = safe(df.net_profit, df.equity)
    r['roa'] = safe(df.net_profit, df.total_assets); r['ebit_margin'] = safe(df.ebit, df.revenue)
    r['inventory_turnover'] = safe(df.cost_of_sales, df.inventories); r['receivable_days'] = safe(df.receivables, df.revenue) * 365
    re_ = df['retained_earnings'] if 'retained_earnings' in df else pd.Series(np.nan, index=df.index)   # no substitute: flagged by the validator
    r['z_em'] = (3.25 + 6.56 * safe(df.current_assets - df.st_liabilities, df.total_assets) + 3.26 * safe(re_, df.total_assets)
                 + 6.72 * safe(df.ebit, df.total_assets) + 1.05 * safe(df.equity, tl))
    r['z_zone'] = np.select([r.z_em > 5.85, r.z_em >= 4.35], ['safe', 'grey'], 'distress')
    r['lp'] = safe(df.revenue, df.employees)
    return r

def tfp_index(df):
    '''Multilateral Törnqvist TFP (log) against the NACE-year mean, observed cost shares.'''
    d = df.copy()
    sL = (d.wage_bill / d.revenue).clip(0, 1); sM = ((d.cost_of_sales - d.wage_bill).clip(lower=0) / d.revenue).clip(0, 1)
    sK = (1 - sL - sM).clip(lower=0)
    lx = {'q': np.log(d.revenue), 'l': np.log(d.employees.where(d.employees > 0)), 'm': np.log((d.cost_of_sales - d.wage_bill).clip(lower=1)),
          'k': np.log(d.fixed_assets.clip(lower=1))}
    g = d.groupby(['nace2', 'year'])
    out = lx['q'] - g['revenue'].transform(lambda s: np.log(s).mean())
    for x, s in [('l', sL), ('m', sM), ('k', sK)]:
        m_lx = lx[x].groupby([d.nace2, d.year]).transform('mean'); m_s = s.groupby([d.nace2, d.year]).transform('mean')
        out = out - 0.5 * (s + m_s) * (lx[x] - m_lx)
    return out

def concentration(df, keys):
    g = df.groupby(keys + ['year'])
    sh = df.revenue / g.revenue.transform('sum')
    t = pd.DataFrame({'firms': g.size(), 'revenue': g.revenue.sum(),
                      'HHI': (sh ** 2).groupby([df[k] for k in keys] + [df.year]).sum() * 1e4,
                      'CR4_pct': sh.groupby([df[k] for k in keys] + [df.year]).apply(lambda s: s.nlargest(4).sum() * 100)})
    return t

def entry_exit(df):
    first = df.groupby('firm_id').year.transform('min'); last = df.groupby('firm_id').year.transform('max')
    ymin, ymax = df.year.min(), df.year.max()
    d = df.assign(entrant=(df.year == first) & (df.year > ymin), exiter=(df.year == last) & (df.year < ymax))
    t = d.groupby(['nace2', 'year']).agg(firms=('firm_id', 'size'), entrants=('entrant', 'sum'), exits=('exiter', 'sum'))
    t['entry_rate_pct'] = t.entrants / t.firms * 100; t['exit_rate_pct'] = t.exits / t.firms * 100
    lastf = df.groupby('firm_id').year.max()
    coh = d[d.entrant].groupby('year').firm_id.apply(list)
    surv = {y: {f'survive_{k}y_pct': float((lastf.loc[ids] >= y + k).mean() * 100) for k in (1, 3) if y + k <= ymax}
            for y, ids in coh.items()}
    return t, pd.DataFrame(surv).T

def peer_rank(df, rat):
    d = pd.concat([df[['nace2', 'size_class']], rat[['roa', 'lp', 'z_em']]], axis=1)
    return d.groupby(['nace2', 'size_class'])[['roa', 'lp', 'z_em']].rank(pct=True) * 100

def share_model(df):
    '''Delta ln share on LAGGED relative productivity and relative leverage (deviation from the NACE-year mean);
    NACE-year effects removed by demeaning; heteroskedasticity-robust (HC1) SEs. No lagged share on the right-hand side.'''
    d = df.sort_values(['firm_id', 'year']).copy()
    d['sh'] = d.revenue / d.groupby(['nace2', 'year']).revenue.transform('sum')
    d['dlsh'] = np.log(d.sh).groupby(d.firm_id).diff()
    d['rlp'] = np.log(d.revenue / d.employees.where(d.employees > 0)); d['rlp'] -= d.groupby(['nace2', 'year']).rlp.transform('mean')
    d['rlev'] = (d.st_liabilities + d.lt_liabilities) / d.total_assets; d['rlev'] -= d.groupby(['nace2', 'year']).rlev.transform('mean')
    for c in ['rlp', 'rlev']: d[c + '_l1'] = d.groupby('firm_id')[c].shift(1)
    d['cell'] = d.nace2 + '_' + d.year.astype(str)
    e = d.dropna(subset=['dlsh', 'rlp_l1', 'rlev_l1'])
    for c in ['dlsh', 'rlp_l1', 'rlev_l1']: e[c] = e[c] - e.groupby('cell')[c].transform('mean')
    f = ols(e.dlsh, e[['rlp_l1', 'rlev_l1']], cov='hc1', add_const=False)
    return f, d

def firm_forecast(d, beta, branch_fc):
    '''Project shares from the last year with the determinants held at their last values; renormalise within branch.'''
    last = d[d.year == d.year.max()].copy()
    out = []
    for h, y in enumerate(FC_YEARS, start=1):
        z = np.log(last.sh) + h * (beta[0] * last.rlp.fillna(0) + beta[1] * last.rlev.fillna(0))
        w = np.exp(z) / np.exp(z).groupby(last.nace2).transform('sum')
        out.append(pd.DataFrame({'firm_id': last.firm_id, 'nace2': last.nace2, 'year': y, 'share': w.values,
                                 'revenue_fc': w.values * last.nace2.map(lambda b: branch_fc.loc[y, b] * 1000).values}))
    return pd.concat(out, ignore_index=True)
print('engine defined: ratios (incl. DuPont, Altman Z\'\'-EM), tfp_index, concentration, entry_exit, peer_rank, share_model, firm_forecast')

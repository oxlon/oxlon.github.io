# %% [markdown]
# ### 17.3 SİNTETİK panel
#
# Başlanğıc dəyəri sabitlənmiş (`SEED + 17`), 24 emal sənayesi sahəsi, 2019–2025. **A qatı ilə uyğun** qurulub: hər
# sahə-il üzrə müəssisələrin sayı DSK-nın fəaliyyət göstərən müəssisələr sayına (`004`) bərabərdir; müəssisə gəlirlərinin
# cəmi DSK-nın sahə buraxılışına (`010`) dəqiq bərabərdir; işçilərin sayının cəmi DSK-nın sahə üzrə işçilərinə (`006`)
# bərabərdir; əmək haqqı fondları DSK-nın sahə əmək haqlarından (`006_2`) istifadə edir; regionlar və mülkiyyət DSK-nın
# müəssisə bölgülərindən (`021`, `004`) çəkilir. Bazar payları **məlum** məlumat yaradan proses üzrə dəyişir —
# $\Delta\ln w_{i,t} = 0.15\,\widetilde{\ln LP}_{i,t-1} - 0.30\,\widetilde{lev}_{i,t-1} + \varepsilon$ — belə ki, emal xəttinin
# sınağı mühərrikin ona verilmiş parametrləri bərpa edib-etmədiyini yoxlaya bilsin. v1-də balans hesabatı maddələri uçot
# eyniliklərini ödəyən sadə nisbət paylanmalarından çəkilir; onların böyük hissəsi sonra Hissə 17.2b-nin struktur qatı
# ilə yenidən yazılır. Bunların heç biri real müəssisələri təsvir etmir.
#
# Panel sxemin bütün sahələri ilə **`data/firm_panel/FR10_firm_panel_SYNTHETIC.csv`** faylına (və README və sxem vərəqi
# olan `.xlsx` faylına) yazılır; hər sətir `data_status = "SYNTHETIC — not real enterprise data"` (*SİNTETİK — real
# müəssisə məlumatı deyil*) işarəsini daşıyır. Generator **yalnız** SYNTHETIC adlı faylları (habelə şablonu və sütun
# xəritəsini) yazır; o, Nazirliyin öz məlumatları üçün istifadə etdiyi `FR10_firm_panel.csv/.xlsx` adlı faylı heç vaxt
# yaratmır və üzərinə yazmır. Fayl yalnız məzmunu dəyişdikdə yenidən yazılır, buna görə təkrar icralar sürətlidir.

# %%
rng_s = np.random.default_rng(SEED + 17)
SYN_YEARS = list(range(2019, LAST_ACT + 1))
BETA_TRUE = np.array([0.15, -0.30])
reg_p = (REG_NENT.loc[LAST_ACT] / REG_NENT.loc[LAST_ACT].sum()).to_numpy(float)
_own = d047.set_index('label')[LAST_ACT]
p_state = float(_own['State property'] / _own['by all types of economic ownership'])
_ns = _own[['private property', 'foreign property', 'joint (mixed) property']].astype(float); _ns = _ns / _ns.sum()
def size_class(emp, rev):
    e = np.select([emp <= 10, emp <= 50, emp <= 250], [0, 1, 2], 3); r = np.select([rev <= 200, rev <= 3000, rev <= 30000], [0, 1, 2], 3)
    return np.array(['micro', 'small', 'medium', 'large'])[np.maximum(e, r)]
rows = []; fid = 0
for b in MANUF:
    st = None
    for y in SYN_YEARS:
        N = int(NENT.loc[y, b])
        if st is None:
            n_new = N; st = pd.DataFrame(columns=['firm_id', 'lw', 'lp', 'lev', 'region', 'ownership'])
        else:
            rlp = st.lp - st.lp.mean(); rlev = st.lev - st.lev.mean()
            # exit is decided on LAST year's size (never on this year's shock, which would bias the test)
            keep = ~(rng_s.random(len(st)) < np.where(st.lw < st.lw.quantile(0.3), 0.12, 0.03))
            if keep.sum() > N: keep &= (st.lw.rank(ascending=False, method='first') <= N).values
            st = st.assign(lw=st.lw + BETA_TRUE[0] * rlp + BETA_TRUE[1] * rlev + rng_s.normal(0, 0.25, len(st)),
                           lp=st.lp + rng_s.normal(0, 0.10, len(st)), lev=(st.lev + rng_s.normal(0, 0.03, len(st))).clip(0.05, 0.95))[keep]
            n_new = N - len(st)
        if n_new > 0:
            new = pd.DataFrame({'firm_id': [f'SYN-{b}-{fid + i:05d}' for i in range(n_new)],
                                'lw': rng_s.normal(-1.0 if y > SYN_YEARS[0] else 0.0, 1.5, n_new),
                                'lp': rng_s.normal(0, 0.4, n_new), 'lev': rng_s.beta(3, 4, n_new),
                                'region': rng_s.choice(REG_NAMES, n_new, p=reg_p),
                                'ownership': np.where(rng_s.random(n_new) < p_state, 'state',
                                                      rng_s.choice(['private', 'foreign', 'joint'], n_new, p=_ns.values))})
            fid += n_new; st = pd.concat([st, new], ignore_index=True)
        w = np.exp(st.lw - st.lw.max()); w = w / w.sum()
        rev = w.values * GO.loc[y, b] * 1000
        lab = rev / np.exp(st.lp.values); lab = lab / lab.sum() * EMP_DSK.loc[y, b]
        rows.append(pd.DataFrame({'firm_id': st.firm_id.values, 'year': y, 'nace2': b, 'region': st.region.values,
                                  'ownership': st.ownership.values, 'revenue': rev, 'employees': lab,
                                  'wage_bill': lab * WAGE_DSK.loc[y, b] * 12 / 1000, 'lev': st.lev.values}))
SYN = pd.concat(rows, ignore_index=True)
n = len(SYN); u = lambda a, b_: rng_s.uniform(a, b_, n)
SYN['total_assets'] = SYN.revenue / np.exp(rng_s.normal(np.log(0.9), 0.4, n))
SYN['equity'] = SYN.total_assets * (1 - SYN.lev)
tl = SYN.total_assets - SYN.equity
SYN['st_liabilities'] = tl * u(0.4, 0.8); SYN['lt_liabilities'] = tl - SYN.st_liabilities
SYN['current_assets'] = SYN.total_assets * u(0.3, 0.7); SYN['fixed_assets'] = SYN.total_assets - SYN.current_assets
SYN['cash'] = SYN.current_assets * u(0.05, 0.3); SYN['receivables'] = SYN.current_assets * u(0.2, 0.5)
SYN['inventories'] = SYN.current_assets - SYN.cash - SYN.receivables
SYN['cost_of_sales'] = np.maximum(SYN.revenue * (1 - rng_s.beta(3, 7, n)), SYN.wage_bill)
SYN['operating_expenses'] = SYN.revenue * u(0.03, 0.12)
SYN['ebit'] = SYN.revenue - SYN.cost_of_sales - SYN.operating_expenses
SYN['interest'] = tl * 0.12 * u(0.3, 1.0)
pbt = SYN.ebit - SYN.interest
SYN['net_profit'] = np.where(pbt > 0, pbt * 0.8, pbt)
SYN['retained_earnings'] = SYN.equity * u(0.2, 0.8)
SYN['size_class'] = size_class(SYN.employees.values, SYN.revenue.values)
SYN = SYN.drop(columns='lev')
# optional schema fields (synthetic): debt split, depreciation, cash flow, capex, exports, dates
n = len(SYN); u = lambda a, b_: rng_s.uniform(a, b_, n)
tl = SYN.st_liabilities + SYN.lt_liabilities
SYN['interest_bearing_debt'] = tl * u(0.4, 0.9); SYN['trade_payables'] = (SYN.st_liabilities - 0.5 * SYN.interest_bearing_debt).clip(lower=0)
SYN['depreciation'] = SYN.fixed_assets * u(0.04, 0.12); SYN['capex'] = SYN.depreciation * u(0.3, 2.0)
SYN['operating_cash_flow'] = SYN.net_profit + SYN.depreciation + SYN.revenue * rng_s.normal(0, 0.03, n)
SYN['exports'] = np.where(rng_s.random(n) < 0.25, SYN.revenue * rng_s.beta(2, 5, n), 0.0)
SYN['product_codes'] = ''
first = SYN.groupby('firm_id').year.transform('min'); last = SYN.groupby('firm_id').year.transform('max')
SYN['registration_date'] = np.where(first > SYN_YEARS[0], first.astype(str) + '-06-30', (first - rng_s.integers(1, 20, n)).astype(str) + '-01-15')
SYN['liquidation_date'] = np.where(last < SYN_YEARS[-1], (last + 1).astype(str) + '-03-31', '')
_v1_order = SYN[['firm_id', 'year']].copy()
SYN, SYN_TRUTH, SYN_CLIP = structural_overlay(SYN, GO)            # v2 structural layer (Part 17.2b)
SYN = SYN.set_index(['firm_id', 'year']).loc[pd.MultiIndex.from_frame(_v1_order)].reset_index()   # v1 row order kept
print(f'[{SYN_MARK}] structural layer applied: {SYN_CLIP}')
_g = SYN.assign(pbt=SYN.ebit - SYN.interest, ded=SYN.cost_of_sales + SYN.operating_expenses + SYN.interest).groupby('year')
SYN_CAL = pd.DataFrame({'loss_making_share': _g.pbt.apply(lambda s: (s < 0).mean()), 'pbt_over_deductible': _g.pbt.sum() / _g.ded.sum(),
                        'net_profit_over_revenue': _g.net_profit.sum() / _g.revenue.sum()})
print(f'[{SYN_MARK}] calibration (target loss-making share {DGP_CAL["loss_target"]:.0%}; DVX declaration net margin 10-13% of deductible expenses):')
print(SYN_CAL.round(3).to_string())
SYN.insert(0, 'data_status', SYN_STATUS)
SYN = SYN[['data_status'] + [f for f in SCHEMA.field if f in SYN.columns]]
assert all(f in SYN.columns for f in SCHEMA.field), 'synthetic panel lacks a schema field'
FPDIR = BASE / 'data' / 'firm_panel'; FPDIR.mkdir(parents=True, exist_ok=True)
SYN_CSV, SYN_XLSX = FPDIR / 'FR10_firm_panel_SYNTHETIC.csv', FPDIR / 'FR10_firm_panel_SYNTHETIC.xlsx'
_txt = SYN.to_csv(index=False, float_format='%.10g')   # v2: relative precision (tiny synthetic firms)
_changed = not SYN_CSV.exists() or SYN_CSV.read_text(encoding='utf-8') != _txt
if _changed: SYN_CSV.write_text(_txt, encoding='utf-8')
COLMAP = SCHEMA[['field', 'field_az', 'unit', 'required', 'source', 'type', 'constraint']].rename(columns={'field': 'field_en'})
COLMAP = pd.concat([pd.DataFrame([dict(field_en='data_status', field_az='Məlumatın statusu', unit='', required=False, source='-', type='str',
                                       constraint='"SYNTHETIC — not real enterprise data" in the synthetic file; anything else (or absent) = real data')]), COLMAP], ignore_index=True)
COLMAP.to_csv(FPDIR / 'FR10_firm_panel_column_map.csv', index=False, encoding='utf-8')
ex = {f: '' for f in ['data_status'] + list(SCHEMA.field)}
ex.update(data_status='EXAMPLE ROW — delete before use / NÜMUNƏ SƏTİR — istifadədən əvvəl silin', firm_id='PSEUDO-000001', year=2025, nace2='10',
          region='Baku city', ownership='private', size_class='small', total_assets=1000, current_assets=600, cash=100, receivables=200,
          inventories=150, fixed_assets=400, equity=500, retained_earnings=200, interest_bearing_debt=300, trade_payables=150,
          st_liabilities=350, lt_liabilities=150, revenue=1500, cost_of_sales=1100, operating_expenses=250, ebit=150, interest=30,
          net_profit=96, depreciation=40, operating_cash_flow=140, capex=60, employees=25, wage_bill=210, exports=0,
          registration_date='2015-04-01')
TEMPLATE = pd.DataFrame([ex])
TEMPLATE.to_csv(FPDIR / 'FR10_firm_panel_TEMPLATE.csv', index=False, encoding='utf-8')
print(f'[{SYN_MARK}] synthetic input file {"written" if _changed else "unchanged"}: {SYN_CSV.name} ({len(SYN):,} rows); template and column map written')
print(f'[{SYN_MARK}] {len(SYN):,} firm-years, {SYN.firm_id.nunique():,} firms, {len(MANUF)} branches, {SYN_YEARS[0]}-{SYN_YEARS[-1]}')

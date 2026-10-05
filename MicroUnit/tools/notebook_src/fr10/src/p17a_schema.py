# %% [markdown]
# ## Hissə 17 — B qatı: müəssisə səviyyəli mühərrik (yalnız SİNTETİK emal xətti sınağı)
#
# > **SİNTETİK — emal xəttinin sınağı, nəticə deyil** (`SYNTHETIC — pipeline test, not results`). Vergi Xidmətindən /
# > DSMF-dən 24 avqust 2026-da sorğu edilmiş müəssisə paneli alınmayıb. Hissə 17-dəki hər şey A qatının aqreqatları
# > (sahə buraxılışı, müəssisələrin sayı, işçilərin sayı, regional bölgü) ilə uyğun qurulmuş, başlanğıc dəyəri (seed)
# > sabitlənmiş sintetik panel üzərində işləyir. Onun yeganə məqsədi giriş sxeminin, validatorun və hər hesablamanın
# > əvvəldən sonadək işlədiyini və öz eyniliklərini təkrar istehsal etdiyini sübut etməkdir. Bu Hissədəki heç bir rəqəm
# > Azərbaycan müəssisələri haqqında tapıntı deyil; bütün nəticələr `output/FR10_SYNTHETIC_*.csv` fayllarıdır və birinci
# > sütunlarında su nişanı daşıyır.
#
# ### 17.1 Giriş sxemi
#
# Hər müəssisə və il üçün bir sətir. Pul məbləğləri min manatla, işçilərin sayı nəfərlə. Sxem Vergi Xidməti (DVX) və
# Dövlət Sosial Müdafiə Fondu (DSMF) ilə məlumat mübadiləsi sazişi üçün müqavilədir.

# %%
SCHEMA = pd.DataFrame([
 ('firm_id', 'str', '', True, 'unique per enterprise (VÖEN, pseudonymised)', 'DVX'),
 ('year', 'int', '', True, '2019 <= year <= reporting year', 'DVX'),
 ('nace2', 'str', '', True, 'a valid NACE Rev.2 division (01-99); FR10 Layer A covers 05-39', 'DVX / DSK register'),
 ('region', 'str', '', True, 'one of the 14 economic regions', 'DSK register'),
 ('ownership', 'str', '', True, 'state | private | foreign | joint', 'DSK register'),
 ('size_class', 'str', '', False, 'micro | small | medium | large (derived if absent)', 'derived'),
 ('total_assets', 'float', 'thsd AZN', True, '>= 0', 'DVX balance sheet'),
 ('current_assets', 'float', 'thsd AZN', True, '>= 0; <= total assets', 'DVX balance sheet'),
 ('cash', 'float', 'thsd AZN', True, '>= 0', 'DVX balance sheet'),
 ('receivables', 'float', 'thsd AZN', True, '>= 0', 'DVX balance sheet'),
 ('inventories', 'float', 'thsd AZN', True, '>= 0; cash + receivables + inventories <= current assets', 'DVX balance sheet'),
 ('fixed_assets', 'float', 'thsd AZN', True, '>= 0; current + fixed <= total assets', 'DVX balance sheet'),
 ('equity', 'float', 'thsd AZN', True, 'may be negative', 'DVX balance sheet'),
 ('retained_earnings', 'float', 'thsd AZN', False, 'needed for the distress score; if absent the score is not computed and the firm is flagged', 'DVX balance sheet'),
 ('interest_bearing_debt', 'float', 'thsd AZN', False, '>= 0; <= total liabilities (separates debt from trade payables)', 'DVX balance sheet'),
 ('trade_payables', 'float', 'thsd AZN', False, '>= 0', 'DVX balance sheet'),
 ('st_liabilities', 'float', 'thsd AZN', True, '>= 0', 'DVX balance sheet'),
 ('lt_liabilities', 'float', 'thsd AZN', True, '>= 0; equity + liabilities = total assets', 'DVX balance sheet'),
 ('revenue', 'float', 'thsd AZN', True, '>= 0', 'DVX P&L / profit-tax declaration'),
 ('cost_of_sales', 'float', 'thsd AZN', True, '>= 0', 'DVX P&L'),
 ('operating_expenses', 'float', 'thsd AZN', True, '>= 0', 'DVX P&L'),
 ('ebit', 'float', 'thsd AZN', True, '= revenue - cost of sales - operating expenses (within 5%)', 'DVX P&L'),
 ('interest', 'float', 'thsd AZN', True, '>= 0', 'DVX P&L'),
 ('net_profit', 'float', 'thsd AZN', True, 'may be negative', 'DVX P&L'),
 ('depreciation', 'float', 'thsd AZN', False, '>= 0', 'DVX P&L / fixed-asset register'),
 ('operating_cash_flow', 'float', 'thsd AZN', False, 'may be negative', 'DVX cash-flow statement'),
 ('capex', 'float', 'thsd AZN', False, '>= 0', 'DVX cash-flow statement'),
 ('employees', 'float', 'persons', True, '>= 0 (annual average)', 'DSMF'),
 ('wage_bill', 'float', 'thsd AZN', True, '>= 0', 'DSMF'),
 ('exports', 'float', 'thsd AZN', False, '>= 0; <= revenue', 'State Customs Committee (DGK)'),
 ('product_codes', 'str', '', False, 'HS / PRODCOM codes, ";"-separated', 'DGK / DSK'),
 ('registration_date', 'date', '', False, 'state registration date (entry)', 'DVX / Ministry of Justice register'),
 ('liquidation_date', 'date', '', False, 'liquidation date (exit), empty if active', 'DVX / Ministry of Justice register'),
], columns=['field', 'type', 'unit', 'required', 'constraint', 'source'])
display(SCHEMA)

NACE_DIV = {f'{d:02d}' for d in list(range(1, 4)) + list(range(5, 34)) + [35] + list(range(36, 40)) + list(range(41, 44))
            + list(range(45, 48)) + list(range(49, 54)) + [55, 56] + list(range(58, 64)) + [64, 65, 66, 68] + list(range(69, 76))
            + list(range(77, 83)) + [84, 85, 86, 87, 88] + list(range(90, 94)) + [94, 95, 96, 97, 98, 99]}
AZ = {'firm_id': 'Müəssisənin identifikatoru (psevdonim VÖEN)', 'year': 'İl', 'nace2': 'İqtisadi fəaliyyət növü (NACE Rev.2, 2 rəqəm)',
      'region': 'İqtisadi rayon', 'ownership': 'Mülkiyyət növü', 'size_class': 'Ölçü qrupu', 'total_assets': 'Aktivlərin cəmi',
      'current_assets': 'Dövriyyə aktivləri', 'cash': 'Pul vəsaitləri', 'receivables': 'Debitor borcları', 'inventories': 'Ehtiyatlar',
      'fixed_assets': 'Uzunmüddətli aktivlər', 'equity': 'Kapital', 'retained_earnings': 'Bölüşdürülməmiş mənfəət',
      'interest_bearing_debt': 'Faizli borclar', 'trade_payables': 'Kreditor borcları', 'st_liabilities': 'Qısamüddətli öhdəliklər',
      'lt_liabilities': 'Uzunmüddətli öhdəliklər', 'revenue': 'Satışdan gəlir', 'cost_of_sales': 'Satışın maya dəyəri',
      'operating_expenses': 'Əməliyyat xərcləri', 'ebit': 'Faiz və vergidən əvvəl mənfəət', 'interest': 'Faiz xərcləri',
      'net_profit': 'Xalis mənfəət', 'depreciation': 'Amortizasiya', 'operating_cash_flow': 'Əməliyyat fəaliyyətindən pul axını',
      'capex': 'Əsas kapitala qoyuluş', 'employees': 'İşçilərin orta sayı', 'wage_bill': 'Əmək haqqı fondu', 'exports': 'İxrac',
      'product_codes': 'Məhsul kodları (HS / PRODCOM)', 'registration_date': 'Qeydiyyat tarixi', 'liquidation_date': 'Ləğvetmə tarixi'}
SCHEMA['field_az'] = SCHEMA.field.map(AZ)
assert SCHEMA.field_az.notna().all()
SYN_STATUS = 'SYNTHETIC — not real enterprise data'
TOL = 0.01
def normalise_headers(df):
    """Accept English or Azerbaijani headers (column map); returns (renamed frame, list of unrecognised columns)."""
    m = {**{az_lower(v).strip(): k for k, v in AZ.items()}, **{k: k for k in AZ}, 'data_status': 'data_status',
         az_lower('Məlumatın statusu'): 'data_status'}
    ren = {c: m.get(az_lower(str(c)).strip(), c) for c in df.columns}
    return df.rename(columns=ren), [c for c, v in ren.items() if v not in AZ and v != 'data_status']

def validate(df):
    """Per-row, per-field issues: (row, firm_id, year, field, rule, severity). severity: fatal / error / warning.
    fatal and error are HARD (the run stops); warnings are reported and the run continues."""
    iss = []
    def add(mask, field, rule, sev='error'):
        m = mask.fillna(True) if sev != 'warning' else mask.fillna(False)
        for i in df.index[m]:
            iss.append(dict(row=int(i) + 2, firm_id=df.at[i, 'firm_id'] if 'firm_id' in df else '', year=df.at[i, 'year'] if 'year' in df else '',
                            field=field, rule=rule, severity=sev))
    miss = [f for f in SCHEMA[SCHEMA.required].field if f not in df.columns]
    if miss:
        return pd.DataFrame([dict(row=1, firm_id='', year='', field=f, rule='required column missing (EN or AZ header)', severity='fatal') for f in miss])
    num = {f: pd.to_numeric(df[f], errors='coerce') for f in SCHEMA[SCHEMA.type == 'float'].field if f in df}
    for f in SCHEMA[SCHEMA.required & (SCHEMA.type == 'float')].field:
        add(~np.isfinite(num[f]), f, 'not numeric or missing')
    for f in ['total_assets', 'current_assets', 'cash', 'receivables', 'inventories', 'fixed_assets', 'st_liabilities', 'lt_liabilities',
              'revenue', 'cost_of_sales', 'operating_expenses', 'interest', 'employees', 'wage_bill', 'interest_bearing_debt',
              'trade_payables', 'depreciation', 'capex', 'exports']:
        if f in num: add(num[f] < 0, f, 'negative value')
    add(df.duplicated(['firm_id', 'year'], keep=False), 'firm_id', 'duplicate firm-year')
    add(~df.nace2.astype(str).str.zfill(2).isin(NACE_DIV), 'nace2', 'not a NACE Rev.2 division')
    add(~df.region.isin(REG_NAMES), 'region', f'not one of the 14 economic regions')
    add(~df.ownership.isin(['state', 'private', 'foreign', 'joint']), 'ownership', 'not state / private / foreign / joint')
    n = num
    add(n['current_assets'] + n['fixed_assets'] > n['total_assets'] * (1 + TOL), 'total_assets', 'total assets < current + fixed assets')
    add(n['current_assets'] > n['total_assets'] * (1 + TOL), 'current_assets', 'current assets > total assets')
    add((n['equity'] + n['st_liabilities'] + n['lt_liabilities'] - n['total_assets']).abs() > TOL * n['total_assets'].abs().clip(lower=1),
        'equity', 'balance sheet does not balance (equity + liabilities != total assets)')
    add(n['cash'] + n['receivables'] + n['inventories'] > n['current_assets'] * (1 + TOL), 'current_assets', 'cash + receivables + inventories > current assets')
    add((n['revenue'] - n['cost_of_sales'] - n['operating_expenses'] - n['ebit']).abs() > 0.05 * n['revenue'].clip(lower=1),
        'ebit', 'EBIT inconsistent with revenue - costs (5%)', 'warning')
    if 'exports' in n: add(n['exports'] > n['revenue'] * (1 + TOL), 'exports', 'exports > revenue')
    if 'interest_bearing_debt' in n:
        add(n['interest_bearing_debt'] > (n['st_liabilities'] + n['lt_liabilities']) * (1 + TOL), 'interest_bearing_debt', 'interest-bearing debt > liabilities')
    if 'retained_earnings' not in df: add(pd.Series(True, index=df.index), 'retained_earnings', 'absent: distress score not computed', 'warning')
    else: add(n['retained_earnings'].isna(), 'retained_earnings', 'missing: distress score not computed', 'warning')
    return pd.DataFrame(iss, columns=['row', 'firm_id', 'year', 'field', 'rule', 'severity'])
print(f'schema: {len(SCHEMA)} fields ({int(SCHEMA.required.sum())} required), English and Azerbaijani headers accepted; validator: 16 rule families, per row and per field')

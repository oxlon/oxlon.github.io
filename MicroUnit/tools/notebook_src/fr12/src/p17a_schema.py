# %% [markdown]
# ## Hissə 17 — B qatı: müəssisə səviyyəli rəqabət mühərriki (DSK biznes reyestri daxil olana qədər SİNTETİK)
#
# > **SİNTETİK — emal xəttinin nümayişi, tapıntı deyil** (`SYNTHETIC — pipeline demonstration, not findings`). 24 avqust
# > 2026-da sorğu edilmiş DSK biznes reyestri alınmayıb. Hissə 17 **DSK aqreqatlarına kalibrlənmiş** (Hissə 17.3), başlanğıc
# > dəyəri sabitlənmiş sintetik reyestr olan `data/business_register/FR12_business_register_SYNTHETIC.csv` üzərində işləyir.
# > Bu Hissədəki hər rəqəm uydurulmuş müəssisələri təsvir edir. Bütün nəticələr `output/FR12_SYNTHETIC_*.csv` fayllarıdır
# > və birinci sütunlarında su nişanı daşıyır. Nazirlik faylı **öz sistemində** öz reyestri ilə əvəz edir (17.4); bundan
# > sonra nəticələr `FR12_FIRM_*.csv` olur.
#
# ### 17.1 Giriş sxemi — reyestrdən çıxarış üçün müqavilə

# %%
BR_SCHEMA = pd.DataFrame([
 ('data_status', 'str', '', False, 'synthetic marker; any other value or no column = REAL data', 'generator'),
 ('firm_id', 'str', '', True, 'unique per enterprise, pseudonymised (never the VÖEN)', 'DSK register'),
 ('year', 'int', '', True, 'reporting year', 'DSK register'),
 ('nace2', 'str', '', True, 'NACE Rev.2 division, 2 digits, sections A-S and U', 'DSK register'),
 ('region', 'str', '', True, 'one of the 14 economic regions', 'DSK register'),
 ('ownership', 'str', '', True, 'state | municipal | private | foreign | joint', 'DSK register'),
 ('size_class', 'str', '', True, 'micro | small | medium | large (statutory classes)', 'DSK register'),
 ('revenue', 'float', 'thsd AZN', True, '>= 0', 'DSK register / DVX'),
 ('employees', 'float', 'persons', True, '>= 0', 'DSK register / DSMF'),
 ('registration_date', 'date', '', True, 'state registration date (entry); <= 31 Dec of year', 'DSK register'),
 ('liquidation_date', 'date', '', False, 'liquidation date (exit); empty while active; >= registration date', 'DSK register'),
 ('status', 'str', '', True, 'active | liquidated (liquidated only in the year of liquidation)', 'DSK register'),
 ('legal_form', 'str', '', False, 'LLC | JSC | state enterprise | other', 'DSK register'),
 ('exports', 'float', 'thsd AZN', False, '>= 0, <= revenue', 'State Customs Committee'),
 ('product_codes', 'str', '', False, 'HS / PRODCOM codes, ";"-separated', 'DSK / Customs'),
 ('cost_of_sales', 'float', 'thsd AZN', False, '>= 0 (price-cost margin, Boone indicator)', 'DVX (link by firm_id to FR10 panel)'),
 ('operating_costs', 'float', 'thsd AZN', False, '>= 0', 'DVX'),
 ('weight', 'float', 'enterprises', False, 'number of identical enterprises the row stands for; 1 (or absent) in a census register', 'generator / sample design'),
], columns=['field', 'type', 'unit', 'required', 'constraint', 'source'])
BR_AZ = {'data_status': 'Məlumatın statusu', 'firm_id': 'Müəssisənin identifikatoru (psevdonim)', 'year': 'İl',
         'nace2': 'İqtisadi fəaliyyət növü (NACE Rev.2, 2 rəqəm)', 'region': 'İqtisadi rayon', 'ownership': 'Mülkiyyət növü',
         'size_class': 'Ölçü qrupu', 'revenue': 'Gəlir (satış)', 'employees': 'İşçilərin sayı', 'registration_date': 'Qeydiyyat tarixi',
         'liquidation_date': 'Ləğvetmə tarixi', 'status': 'Status', 'legal_form': 'Təşkilati-hüquqi forma', 'exports': 'İxrac',
         'product_codes': 'Məhsul kodları', 'cost_of_sales': 'Satışın maya dəyəri', 'operating_costs': 'Əməliyyat xərcləri', 'weight': 'Çəki'}
BR_SCHEMA['field_az'] = BR_SCHEMA.field.map(BR_AZ)
assert BR_SCHEMA.field_az.notna().all()
DIV = {'A': ['01', '02', '03'], 'B': ['05', '06', '07', '08', '09'], 'C': [f'{d}' for d in range(10, 34)], 'D': ['35'], 'E': ['36', '37', '38', '39'],
       'F': ['41', '42', '43'], 'G': ['45', '46', '47'], 'H': ['49', '50', '51', '52', '53'], 'I': ['55', '56'], 'J': ['58', '59', '60', '61', '62', '63'],
       'K': ['64', '65', '66'], 'L': ['68'], 'M': ['69', '70', '71', '72', '73', '74', '75'], 'N': ['77', '78', '79', '80', '81', '82'], 'O': ['84'],
       'P': ['85'], 'Q': ['86', '87', '88'], 'R': ['90', '91', '92', '93'], 'S': ['94', '95', '96'], 'U': ['99']}
DIV2SEC = {d: s for s, ds in DIV.items() for d in ds}
OWN = ['state', 'municipal', 'private', 'foreign', 'joint']; SIZES = ['micro', 'small', 'medium', 'large']

def br_normalise(df):
    m = {**{az_lower(v).strip(): k for k, v in BR_AZ.items()}, **{k: k for k in BR_AZ}}
    ren = {c: m.get(az_lower(str(c)).strip(), c) for c in df.columns}
    return df.rename(columns=ren), [c for c, v in ren.items() if v not in BR_AZ]

def br_validate(df):
    '''Per-row, per-field issues (row, firm_id, year, field, rule, severity). fatal/error stop the run; warnings do not.'''
    iss = []
    def add(mask, field, rule, sev='error'):
        mask = mask.fillna(sev != 'warning')
        for i in df.index[mask.to_numpy(bool)]:
            iss.append(dict(row=int(i) + 2, firm_id=df.at[i, 'firm_id'] if 'firm_id' in df else '', year=df.at[i, 'year'] if 'year' in df else '',
                            field=field, rule=rule, severity=sev))
    miss = [f for f in BR_SCHEMA[BR_SCHEMA.required].field if f not in df.columns]
    if miss:
        return pd.DataFrame([dict(row=1, firm_id='', year='', field=f, rule='required column missing (EN or AZ header)', severity='fatal') for f in miss])
    rev = pd.to_numeric(df.revenue, errors='coerce'); emp = pd.to_numeric(df.employees, errors='coerce')
    add(~np.isfinite(rev), 'revenue', 'not numeric or missing'); add(rev < 0, 'revenue', 'negative value')
    add(~np.isfinite(emp), 'employees', 'not numeric or missing'); add(emp < 0, 'employees', 'negative value')
    add(df.duplicated(['firm_id', 'year'], keep=False), 'firm_id', 'duplicate firm-year')
    add(~df.nace2.astype(str).isin(DIV2SEC), 'nace2', 'not a NACE Rev.2 division of sections A-S, U')
    add(~df.region.isin(REGS), 'region', 'not one of the 14 economic regions')
    add(~df.ownership.isin(OWN), 'ownership', 'not state / municipal / private / foreign / joint')
    add(~df.size_class.isin(SIZES), 'size_class', 'not micro / small / medium / large')
    add(~df.status.isin(['active', 'liquidated']), 'status', 'not active / liquidated')
    rd = pd.to_datetime(df.registration_date, errors='coerce'); ld = pd.to_datetime(df.get('liquidation_date'), errors='coerce')
    yr = pd.to_numeric(df.year, errors='coerce')
    add(rd.isna(), 'registration_date', 'missing or not a date'); add(rd.dt.year > yr, 'registration_date', 'registered after the reporting year')
    add((ld < rd) & ld.notna(), 'liquidation_date', 'liquidation before registration')
    add((df.status == 'liquidated') & (ld.dt.year != yr), 'status', "'liquidated' but liquidation date not in this year")
    add((df.status == 'active') & ld.notna() & (ld.dt.year <= yr), 'status', "'active' but liquidated on or before this year", 'warning')
    if 'weight' in df: add(pd.to_numeric(df.weight, errors='coerce').fillna(1) < 1, 'weight', 'weight < 1')
    if 'exports' in df: add(pd.to_numeric(df.exports, errors='coerce') > rev * 1.01, 'exports', 'exports > revenue')
    for f in ['cost_of_sales', 'operating_costs']:
        if f in df: add(pd.to_numeric(df[f], errors='coerce') < 0, f, 'negative value')
    if 'cost_of_sales' not in df: add(pd.Series(True, index=df.index[:1]).reindex(df.index, fill_value=False), 'cost_of_sales', 'absent: price-cost margin and Boone indicator not computed', 'warning')
    return pd.DataFrame(iss, columns=['row', 'firm_id', 'year', 'field', 'rule', 'severity'])
print(f'register schema: {len(BR_SCHEMA)} fields ({int(BR_SCHEMA.required.sum())} required); EN and AZ headers; validator with 17 rules, per row and field')

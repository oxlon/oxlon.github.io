# %% [markdown]
# ### 17.4 Reyestrin yüklənməsi: Nazirlik təqdim edibsə REAL, əks halda SİNTETİK
#
# Prioritet: (1) `BUSREG_PATH` — mühit dəyişəni və ya növbəti xanadakı konfiqurasiya dəyişəni;
# (2) `data/business_register/FR12_business_register.csv` və ya `.xlsx` — Nazirliyin öz faylı; (3) SİNTETİK fayl.
# `data_status` dəyəri sintetik işarə olmayan (və ya belə sütunu olmayan) fayl **REAL** sayılır. Sütun başlıqları ingilis və
# ya Azərbaycan dilində ola bilər. Validator `output/FR12_business_register_validation_report.csv` faylını yazır (sətir və
# sahə üzrə); ciddi xətalar icranı mesajla dayandırır, xəbərdarlıqlar dayandırmır.

# %%
BUSREG_PATH = os.environ.get('BUSREG_PATH') or None      # configuration: set a path here to override

def read_register(path):
    path = Path(path)
    if path.suffix.lower() in ('.xlsx', '.xls'):
        return pd.read_excel(path, sheet_name='data', dtype={'nace2': str, 'firm_id': str})
    return pd.read_csv(path, dtype={'nace2': str, 'firm_id': str}, encoding='utf-8-sig', keep_default_na=True)

def load_register(base, override=None):
    override = override or os.environ.get('BUSREG_PATH') or None       # the environment variable is read at every call
    fp = Path(base) / 'data' / 'business_register'
    cands = ([Path(override)] if override else []) + [fp / 'FR12_business_register.csv', fp / 'FR12_business_register.xlsx']
    src = next((p for p in cands if p.exists()), fp / 'FR12_business_register_SYNTHETIC.csv')
    df, unknown = br_normalise(read_register(src))
    synthetic = 'data_status' in df and df['data_status'].astype(str).eq(SYN_STATUS).all()
    mode = 'SYNTHETIC' if synthetic else 'REAL'
    if 'nace2' in df: df['nace2'] = df['nace2'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(2)
    if 'year' in df: df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df[~df.get('data_status', pd.Series('', index=df.index)).astype(str).str.startswith('EXAMPLE ROW')].reset_index(drop=True)
    return df, mode, src, unknown

def br_banner(mode, src, df):
    line = '#' * 104
    msg = (f'DATA_MODE = {mode}   |   register: {Path(src).name}   |   {len(df):,} rows, {df.firm_id.nunique() if "firm_id" in df else 0:,} records, '
           f'years {int(df.year.min()) if len(df) else "-"}-{int(df.year.max()) if len(df) else "-"}')
    note = ('SYNTHETIC — not real enterprise data. Pipeline demonstration, NOT findings. The Ministry replaces this file in its own system.'
            if mode == 'SYNTHETIC' else 'REAL enterprise data — outputs FR12_FIRM_*.csv; keep them inside the Ministry system.')
    print(line); print(msg.center(104)); print(note.center(104)); print(line)

def check_register(df, report_path, stop=True):
    rep = br_validate(df); rep.to_csv(report_path, index=False)
    hard = rep[rep.severity.isin(['fatal', 'error'])]
    if stop and len(hard):
        raise ValueError(f'business register rejected: {len(hard)} hard errors (first: row {hard.iloc[0].row}, field {hard.iloc[0].field}: '
                         f'{hard.iloc[0].rule}); see {Path(report_path).name}')
    return rep

REGISTER, DATA_MODE, REG_SRC, REG_UNKNOWN = load_register(BASE, BUSREG_PATH)
br_banner(DATA_MODE, REG_SRC, REGISTER)
if REG_UNKNOWN: print(f'columns not in the schema (ignored): {REG_UNKNOWN}')
VREP = check_register(REGISTER, OUT / 'FR12_business_register_validation_report.csv')
print(f'validator: {int((VREP.severity == "warning").sum())} warnings, 0 hard errors -> '
      f'{"FR12_SYNTHETIC_*" if DATA_MODE == "SYNTHETIC" else "FR12_FIRM_*"} outputs')
REG_META = dict(mode=DATA_MODE, file=Path(REG_SRC).name, rows=len(REGISTER), records=int(REGISTER.firm_id.nunique()),
                enterprises_last=float(REGISTER[(REGISTER.year == REGISTER.year.max()) & (REGISTER.status == 'active')].pipe(wcol).sum()),
                year_min=int(REGISTER.year.min()), year_max=int(REGISTER.year.max()), sections=int(REGISTER.nace2.map(DIV2SEC).nunique()),
                divisions=int(REGISTER.nace2.nunique()), regions=int(REGISTER.region.nunique()))

# %% [markdown]
# ### 17.4 Müəssisə panelinin yüklənməsi: Nazirlik təqdim edibsə REAL, əks halda SİNTETİK
#
# Prioritet: (1) `FIRM_PANEL_PATH` — mühit dəyişəni və ya növbəti xanadakı konfiqurasiya dəyişəni;
# (2) `data/firm_panel/FR10_firm_panel.csv` və ya `.xlsx` — Nazirliyin öz faylı; (3) SİNTETİK fayl. `data_status` dəyəri
# sintetik işarə olmayan (və ya belə sütunu olmayan) fayl **REAL** sayılır. Sütun başlıqları ingilis və ya Azərbaycan
# dilində ola bilər. Validator yüklənən istənilən fayl üzərində işləyir və `output/FR10_firm_panel_validation_report.csv`
# faylını yazır (sətir və sahə üzrə); ciddi xətalar icranı mesajla dayandırır, xəbərdarlıqlar dayandırmır.

# %%
FIRM_PANEL_PATH = os.environ.get('FIRM_PANEL_PATH') or None      # configuration: set a path here to override

def read_panel(path):
    path = Path(path)
    df = pd.read_excel(path, sheet_name='data', dtype={'nace2': str}) if path.suffix.lower() in ('.xlsx', '.xls') else \
         pd.read_csv(path, dtype={'nace2': str, 'firm_id': str}, encoding='utf-8-sig', keep_default_na=True)
    return df

def load_firm_panel(base, override=None):
    fp = Path(base) / 'data' / 'firm_panel'
    cands = ([Path(override)] if override else []) + [fp / 'FR10_firm_panel.csv', fp / 'FR10_firm_panel.xlsx']
    src = next((p for p in cands if p.exists()), fp / 'FR10_firm_panel_SYNTHETIC.csv')
    df, unknown = normalise_headers(read_panel(src))
    synthetic = 'data_status' in df and df['data_status'].astype(str).eq(SYN_STATUS).all()
    mode = 'SYNTHETIC' if synthetic else 'REAL'
    if 'nace2' in df: df['nace2'] = df['nace2'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(2)
    if 'year' in df: df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df = df[~df.get('data_status', pd.Series('', index=df.index)).astype(str).str.startswith('EXAMPLE ROW')].reset_index(drop=True)
    return df, mode, src, unknown

def banner(mode, src, df):
    line = '#' * 100
    msg = (f'DATA_MODE = {mode}   |   firm panel: {Path(src).name}   |   {len(df):,} rows, '
           f'{df.firm_id.nunique() if "firm_id" in df else 0:,} firms, years '
           f'{int(df.year.min()) if "year" in df and len(df) else "-"}-{int(df.year.max()) if "year" in df and len(df) else "-"}')
    note = ('SYNTHETIC — pipeline demonstration, NOT findings. The Ministry replaces this file in its own system.'
            if mode == 'SYNTHETIC' else 'REAL enterprise data — outputs FR10_FIRM_*.csv; keep them inside the Ministry system.')
    print(line); print(msg.center(100)); print(note.center(100)); print(line)

def check_panel(df, report_path, stop=True):
    rep = validate(df)
    rep.to_csv(report_path, index=False)
    hard = rep[rep.severity.isin(['fatal', 'error'])]
    if stop and len(hard):
        raise ValueError(f'firm panel rejected: {len(hard)} hard errors (first: row {hard.iloc[0].row}, field {hard.iloc[0].field}: '
                         f'{hard.iloc[0].rule}); see {Path(report_path).name}')
    return rep

PANEL, DATA_MODE, PANEL_SRC, PANEL_UNKNOWN_COLS = load_firm_panel(BASE, FIRM_PANEL_PATH)
banner(DATA_MODE, PANEL_SRC, PANEL)
if PANEL_UNKNOWN_COLS: print(f'columns not in the schema (ignored): {PANEL_UNKNOWN_COLS}')
VREP = check_panel(PANEL, OUT / 'FR10_firm_panel_validation_report.csv')
print(f'validator: {int((VREP.severity == "warning").sum())} warnings, 0 hard errors -> {"FR10_SYNTHETIC_*" if DATA_MODE == "SYNTHETIC" else "FR10_FIRM_*"} outputs')
PANEL_META = dict(mode=DATA_MODE, file=Path(PANEL_SRC).name, rows=len(PANEL), firms=int(PANEL.firm_id.nunique()),
                  year_min=int(PANEL.year.min()), year_max=int(PANEL.year.max()), branches=int(PANEL.nace2.nunique()))

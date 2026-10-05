# %% [markdown]
# ### 17.6 Əvəzetmə testləri: əvəzetmənin işlədiyinin müvəqqəti qovluqda sübutu
#
# Təkrarlana bilən yoxlamalar müvəqqəti qovluqdakı birdəfəlik nüsxələr üzərində aparılır; layihənin öz
# `data/firm_panel/` qovluğuna heç vaxt real adlı fayl verilmir. (1) Neytral `data_status` ilə `FR10_firm_panel.csv` adı
# altında köçürülmüş sintetik fayl **REAL** kimi yüklənir, validatordan keçir və su nişanı olmayan `FR10_FIRM_*` nəticələrini
# yaradır; (2) Azərbaycan dilində başlıqlar yüklənir; (3) `FIRM_PANEL_PATH` real adlı fayldan üstündür; (4) pozulmuş fayl —
# məcburi sütun yoxdur və ümumi aktivlər dövriyyə aktivlərindən azdır — validatorun aydın mesajlarını yaradır və icranı
# dayandırır.

# %%
import tempfile, shutil
SW = []
def sw(name, ok, detail): SW.append(dict(test=name, passed=bool(ok), detail=detail))
with tempfile.TemporaryDirectory() as td:
    td = Path(td); (td / 'data' / 'firm_panel').mkdir(parents=True); (td / 'output').mkdir()
    real = pd.read_csv(SYN_CSV, dtype={'nace2': str, 'firm_id': str}); real['data_status'] = 'Ministry data (test copy)'
    real.to_csv(td / 'data' / 'firm_panel' / 'FR10_firm_panel.csv', index=False)
    shutil.copy(SYN_CSV, td / 'data' / 'firm_panel' / SYN_CSV.name)
    p_, m_, s_, _ = load_firm_panel(td)
    sw('real-named file with neutral data_status -> DATA_MODE = REAL', m_ == 'REAL' and s_.name == 'FR10_firm_panel.csv', f'mode {m_}, file {s_.name}')
    r_ = check_panel(p_, td / 'output' / 'FR10_firm_panel_validation_report.csv')
    sw('REAL file passes the validator (0 hard errors)', (~r_.severity.isin(['fatal', 'error'])).all(), f'{len(r_)} warnings')
    lb_ = run_layer_b(p_, m_, td / 'output')
    outs = sorted(p.name for p in (td / 'output').glob('FR10_*.csv'))
    sw('REAL mode writes FR10_FIRM_* only, without watermark, all tests pass',
       any(o.startswith('FR10_FIRM_') for o in outs) and not any(o.startswith('FR10_SYNTHETIC_') for o in outs)
       and 'WATERMARK' not in pd.read_csv(td / 'output' / 'FR10_FIRM_pipeline_tests.csv').columns and lb_['PIPE'].passed.all(),
       f'{len([o for o in outs if "_econ_" not in o])} files, e.g. {outs[:3]}')       # v1 table: econometric files are counted in the v2 table
    # v2: REAL mode runs the same firm-level econometrics (same data -> identical estimates); separate table
    ce = lb_['ET']['econ_coefficients'].set_index(['model_id', 'term']).coef
    cs = LB['ET']['econ_coefficients'].set_index(['model_id', 'term']).coef
    gap_e = float((ce - cs.reindex(ce.index)).abs().max()) if len(ce) == len(cs) else np.inf
    eco = sorted(p.name for p in (td / 'output').glob('FR10_FIRM_econ_*.csv'))
    rec_real = pd.read_csv(td / 'output' / 'FR10_FIRM_econ_recovery.csv')
    SW2 = [dict(test='REAL mode estimates the same firm-level models: identical coefficients on the same data',
                passed=bool(gap_e < 1e-9 and len(ce) == len(cs)), detail=f'{len(ce)} coefficients, max |gap| {gap_e:.1e}'),
           dict(test='REAL mode writes FR10_FIRM_econ_* (no watermark, no recovery against true values)',
                passed=bool(len(eco) >= 8 and 'WATERMARK' not in rec_real.columns and 'covered' not in rec_real.columns),
                detail=f'{len(eco)} files: ' + ', '.join(e.replace('FR10_FIRM_', '') for e in eco[:6]) + ' ...')]
    az = real.drop(columns='data_status').head(3000).rename(columns=AZ)
    az.to_excel(td / 'panel_az.xlsx', sheet_name='data', index=False)
    p2, m2, s2, unk = load_firm_panel(td, override=td / 'panel_az.xlsx')
    r2 = validate(p2)
    sw('Azerbaijani headers (xlsx, FIRM_PANEL_PATH) load and validate', s2.name == 'panel_az.xlsx' and not unk and (~r2.severity.isin(['fatal', 'error'])).all(),
       f'{len(p2)} rows, unknown columns {unk}, mode {m2}')
    sw('FIRM_PANEL_PATH has priority over the real-named file', s2.name == 'panel_az.xlsx', f'loaded {s2.name}')
    br = real.head(500).drop(columns='equity').copy(); br.loc[:4, 'total_assets'] = br.loc[:4, 'current_assets'] * 0.5
    r3 = validate(br)
    sw('broken file: missing required column reported as fatal', ((r3.severity == 'fatal') & (r3.field == 'equity')).any(),
       '; '.join(r3[r3.severity == 'fatal'].rule.unique()))
    br2 = real.head(500).copy(); br2.loc[:4, 'total_assets'] = br2.loc[:4, 'current_assets'] * 0.5
    r4 = validate(br2)
    flagged = sorted(set(r4[r4.field == 'total_assets'].row))
    try:
        check_panel(br2, td / 'output' / 'rep.csv'); stopped, msg = False, ''
    except ValueError as e:
        stopped, msg = True, str(e)
    sw('broken file: total assets < current assets flagged per row and the run stops', flagged[:5] == [2, 3, 4, 5, 6] and stopped, msg[:160])
SWAP = pd.DataFrame(SW)
display(SWAP)
assert SWAP.passed.all(), 'firm-panel swap test failed'
SWAP.to_csv(OUT / 'FR10_firm_panel_swap_tests.csv', index=False)
SWAP_ECON = pd.DataFrame(SW2); display(SWAP_ECON)
assert SWAP_ECON.passed.all(), 'econometrics swap test failed'
SWAP_ECON.to_csv(OUT / 'FR10_firm_panel_swap_tests_econ.csv', index=False)
assert not any((FPDIR / n).exists() for n in ['FR10_firm_panel.csv', 'FR10_firm_panel.xlsx']) or DATA_MODE == 'REAL'
print(f'all {len(SWAP)} swap tests pass; the project data/firm_panel/ holds no real-named file unless the Ministry placed one')

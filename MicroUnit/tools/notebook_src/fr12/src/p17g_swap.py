# %% [markdown]
# ### 17.6 Əvəzetmə testləri: əvəzetmənin işlədiyinin müvəqqəti qovluqda sübutu
#
# Müvəqqəti qovluqdakı birdəfəlik nüsxələr üzərində (layihənin `data/business_register/` qovluğu heç vaxt real adlı fayl
# almır): (1) neytral `data_status` ilə `FR12_business_register.csv` adı altında köçürülmüş sintetik fayl **REAL** kimi
# yüklənir, validatordan keçir və su nişanı olmayan `FR12_FIRM_*` nəticələrini yaradır; (2) Azərbaycan dilində başlıqlar
# yüklənir; (3) **mühit dəyişəni** kimi təyin edilmiş `BUSREG_PATH` real adlı fayldan üstündür; (4) `weight` sütunu
# **olmayan** reyestr tam mühərrikdən və DSK ilə müqayisədən keçir, çəkili fayl isə hər müəssisəyə bir sətir olmaqla
# genişləndirilmiş variantı ilə eyni göstəriciləri verir; (5) pozulmuş fayllar — çatışmayan məcburi sütun; mənfi gəlir və
# qeydiyyatdan əvvəlki ləğv tarixi — sətirlər üzrə aydın mesajlar yaradır və icranı dayandırır; (6) generator heç vaxt real
# fayl adını yazmır və layihə qovluğu real adlı fayl olub-olmadığı üzrə yoxlanılır. Test (1) həmçinin **B qatının
# ekonometrikasını (17.7) REAL rejimdə** işə salır: `FR12_FIRM_econ_*.csv` faylları su nişanı olmadan yazılır, əmsallar
# SİNTETİK icranın əmsallarına bərabərdir (eyni sətirlər) və yalnız sintetik məlumatlar üçün müəyyən edilən
# parametrlərin bərpası bloku yoxdur.

# %%
import tempfile, shutil
SW = []
def sw(name, ok, detail): SW.append(dict(test=name, passed=bool(ok), detail=str(detail)[:200]))
_ENV0 = os.environ.pop('BUSREG_PATH', None)          # tests run with a clean environment; restored afterwards
try:
  with tempfile.TemporaryDirectory() as td:
      td = Path(td); (td / 'data' / 'business_register').mkdir(parents=True); (td / 'output').mkdir()
      real = pd.read_csv(SYN_CSV, dtype={'nace2': str, 'firm_id': str}); real['data_status'] = 'Ministry register (test copy)'
      real.to_csv(td / 'data' / 'business_register' / 'FR12_business_register.csv', index=False)
      shutil.copy(SYN_CSV, td / 'data' / 'business_register' / SYN_CSV.name)
      p_, m_, s_, _ = load_register(td)
      sw('real-named file with neutral data_status -> DATA_MODE = REAL', m_ == 'REAL' and s_.name == 'FR12_business_register.csv', f'mode {m_}, file {s_.name}')
      r_ = check_register(p_, td / 'output' / 'FR12_business_register_validation_report.csv')
      sw('REAL file passes the validator (0 hard errors)', (~r_.severity.isin(['fatal', 'error'])).all(), f'{len(r_)} warnings')
      lb_ = run_layer_b(p_, m_, td / 'output')
      ec_ = layer_b_econ(p_, m_, td / 'output', lb_)                   # the Layer-B econometrics in REAL mode
      outs = sorted(p.name for p in (td / 'output').glob('FR12_*.csv'))
      _ec = pd.read_csv(td / 'output' / 'FR12_FIRM_econ_coefficients.csv')
      _dc = _ec.merge(ECON['tables']['coefficients'], on=['model', 'term'], suffixes=('', '_s'))
      _ecok = ('WATERMARK' not in _ec.columns and _ec.interpretation_az.str.startswith(ECON_TAG['REAL']).all() and len(_dc) == len(_ec) == len(ECON['tables']['coefficients'])
               and float((_dc.coef - _dc.coef_s).abs().max()) < 1e-9 and ec_['recovery'] is None)
      sw('REAL mode writes FR12_FIRM_* only, without watermark; identity tests pass; Layer-B econometrics run in REAL mode (FR12_FIRM_econ_*)',
         any(o.startswith('FR12_FIRM_') for o in outs) and not any(o.startswith('FR12_SYNTHETIC_') for o in outs)
         and 'WATERMARK' not in pd.read_csv(td / 'output' / 'FR12_FIRM_concentration_nace.csv', nrows=2).columns and lb_['PIPE'].passed.all() and _ecok,
         f"{len(outs)} files, e.g. {outs[:3]}; econometrics: {_ec.model.nunique()} models, {len(_ec)} coefficients = SYNTHETIC run, no watermark, no recovery block")
      az = real.drop(columns='data_status').head(3000).rename(columns=BR_AZ)
      az.to_excel(td / 'register_az.xlsx', sheet_name='data', index=False)
      _old_env = os.environ.get('BUSREG_PATH')
      os.environ['BUSREG_PATH'] = str(td / 'register_az.xlsx')
      try:
          p2, m2, s2, unk = load_register(td)                     # no argument: the environment variable must be picked up
      finally:
          if _old_env is None: os.environ.pop('BUSREG_PATH', None)
          else: os.environ['BUSREG_PATH'] = _old_env
      r2 = br_validate(p2)
      sw('Azerbaijani headers (xlsx) load and validate', s2.name == 'register_az.xlsx' and not unk and (~r2.severity.isin(['fatal', 'error'])).all(),
         f'{len(p2)} rows, unknown columns {unk}, mode {m2}')
      sw('BUSREG_PATH environment variable has priority over the real-named file', s2.name == 'register_az.xlsx', f'loaded {s2.name} with BUSREG_PATH set in the environment')
      # register WITHOUT a weight column: the full engine and the calibration code run, and weights default to 1
      nw = real[real.nace2.map(DIV2SEC).isin(['D', 'J'])].copy()
      rep = nw.loc[nw.index.repeat(nw.weight.astype(int))].copy()
      rep['firm_id'] = rep.firm_id + '-' + rep.groupby(level=0).cumcount().astype(str)
      rep = rep.drop(columns='weight').reset_index(drop=True); rep.to_csv(td / 'register_noweight.csv', index=False)
      p3, m3, s3, _ = load_register(td, override=td / 'register_noweight.csv')
      lb3 = run_layer_b(p3, m3, td / 'output', write=False); lbw = run_layer_b(nw, 'REAL', td / 'output', write=False)
      _cal3 = calib_table(p3)                                      # the comparison code that crashed without `weight`
      def cmp(a, b, keys, cols):
          m = a[keys + cols].merge(b[keys + cols], on=keys, suffixes=('_a', '_b'))
          return float(max((m[c + '_a'] - m[c + '_b']).abs().max() for c in cols)), len(m)
      d1, n1 = cmp(lb3['concentration_nace'], lbw['concentration_nace'], ['nace2', 'year'], ['n_firms', 'HHI', 'CR4', 'CR8'])
      d2, n2 = cmp(lb3['entry_exit_section'], lbw['entry_exit_section'], ['sec', 'year'], ['entry_rate', 'exit_rate', 'young_firm_revenue_share'])
      d3, n3 = cmp(lb3['survival_km'], lbw['survival_km'], ['cohort', 'age'], ['survival'])
      d4, n4 = cmp(lb3['margins_boone'], lbw['margins_boone'], ['section', 'year'], ['n_profitable', 'pcm_pct'])
      sw('register without a weight column: full engine runs (weights default to 1)', 'weight' not in p3 and lb3['PIPE'].passed.all(), f'{len(p3):,} rows, mode {m3}; engine + DSK comparison ({len(_cal3)} cells) ran')
      sw('weights honoured: weighted file = expanded unweighted file (HHI, CR4/CR8, entry/exit, KM, Boone n, PCM)', max(d1, d2, d3, d4) < 1e-6,
         f'max abs diff {max(d1, d2, d3, d4):.2e} over {n1 + n2 + n3 + n4} cells')
      br = real.head(500).drop(columns='revenue')
      r3 = br_validate(br)
      sw('broken file: missing required column reported as fatal', ((r3.severity == 'fatal') & (r3.field == 'revenue')).any(), '; '.join(r3.rule.unique()))
      br2 = real.head(500).copy(); br2.loc[:2, 'revenue'] = -5.0
      br2.loc[3:4, 'liquidation_date'] = '1990-01-01'
      r4 = validate_rows = br_validate(br2)
      rows_flag = sorted(set(r4[r4.field.isin(['revenue', 'liquidation_date'])].row))
      try:
          check_register(br2, td / 'output' / 'rep.csv'); stopped, msg = False, ''
      except ValueError as e:
          stopped, msg = True, str(e)
      sw('broken file: negative revenue and liquidation before registration flagged per row; the run stops', rows_flag[:5] == [2, 3, 4, 5, 6] and stopped, msg)
      _realnamed = sorted(p.name for p in BRDIR.iterdir() if re.fullmatch(r'FR12_business_register\.(csv|xlsx|xls)', p.name))
      sw('generator never writes the real file name; project directory scanned for real-named files',
         not any(re.fullmatch(r'FR12_business_register\.(csv|xlsx|xls)', n) for n in GEN_WRITTEN) and (not _realnamed or DATA_MODE == 'REAL'),
         f'generator wrote {sorted(set(GEN_WRITTEN))}; real-named files in data/business_register: {_realnamed or "none"}')
finally:
    if _ENV0 is not None: os.environ['BUSREG_PATH'] = _ENV0
SWAP = pd.DataFrame(SW)
display(SWAP)
assert SWAP.passed.all(), 'business-register swap test failed'
SWAP.to_csv(OUT / 'FR12_business_register_swap_tests.csv', index=False)
assert not any((BRDIR / n).exists() for n in ['FR12_business_register.csv', 'FR12_business_register.xlsx']) or DATA_MODE == 'REAL'
print(f'all {len(SWAP)} swap tests pass; the project data/business_register/ holds no real-named file unless the Ministry placed one')

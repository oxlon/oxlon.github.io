# %% [markdown]
# ### 17.4c Müəssisə səviyyəli ekonometrika: dəyişənlər, nümunə qaydaları və modellərin siyahısı
#
# | Model | Asılı dəyişən | İzahedici dəyişənlər | Qiymətləndirici(lər) |
# |---|---|---|---|
# | (a) rentabellik | ROA (1/99% səviyyəsində vinzorlaşdırılmış), əməliyyat marjası EBIT/gəlir | ölçü (ln işçilər), borc yükü, likvidlik (ln cari likvidlik əmsalı), ln(1+yaş), mülkiyyət, ixracın payı, Bakı, sahə tələbinin artımı (DSK sahə buraxılışının Δln), vahid əmək xərci | iki yönlü sabit effektlər (müəssisə + il); NACE × il sabit effektləri ilə birləşdirilmiş |
# | (b) istehsal funksiyası | ln əlavə dəyər (gəlir − materiallar) | ln işçilər, ln əsas fondlar | iki yönlü sabit effektlər (within); NACE və il fiktiv dəyişənləri ilə birləşdirilmiş OLS; miqyasdan gəlir və CRS testi |
# | (c) TFP amilləri | indeks TFP (Törnqvist, müşahidə olunan xərc payları); istehsal funksiyası üzrə TFP | ölçü, yaş, mülkiyyət, ixracatçı, borc yükü, Bakı | NACE × il sabit effektləri ilə birləşdirilmiş; iki yönlü sabit effektlər |
# | (d) maliyyə çətinliyi | t ilində Z''-EM çətinlik zonası və ya mənfi xüsusi kapital | t−1 dövründəki proqnozlaşdırıcılar: borc yükü, likvidlik, ROA, ölçü, ixracın payı; yaş, mülkiyyət; tələbin artımı | logit, AME, ROC/AUC (nümunədaxili və son iki il üzrə nümunədən kənar), kalibrləmə |
# | (e) investisiya norması | kapital qoyuluşu / əsas fondlar t−1 | satışın artımı, borc yükü t−1, ROA t−1, ölçü t−1, mülkiyyət | iki yönlü sabit effektlər; NACE × il sabit effektləri ilə birləşdirilmiş |
# | (f) bazar payı | Δ ln pay | nisbi məhsuldarlıq t−1, nisbi borc yükü t−1 | NACE × il daxilində (Hissə 17.2), HC1 |
# | (g) ixracda iştirak | ixracatçı (ixrac > 0) | ln işçilər t−1, mülkiyyət, ln(1+yaş), Bakı | NACE və il fiktiv dəyişənləri ilə logit, AME |
#
# **Nə üçün Olley–Pakes, Levinsohn–Petrin və ya Ackerberg–Caves–Frazer deyil.** Bu nəzarət funksiyası
# qiymətləndiriciləri istehsal funksiyasını məhsuldarlığın birinci tərtib Markov (praktikada avtoreqressiv) hərəkət
# qanununa, $\omega_{it} = g(\omega_{i,t-1}) + \xi_{it}$, tabe olduğunu fərz etməklə və onu qiymətləndirməklə
# identifikasiya edir. Bu, müşahidə olunmayan vəziyyət dəyişəni üçün qiymətləndirilmiş avtoreqressiv prosesdir və
# Sifarişçinin məhdudiyyətləri onu istisna edir. FR10 within qiymətləndiricisindən (məhsuldarlıq müəssisə sabit effekti
# üstəgəl il effektləri kimi) və birləşdirilmiş OLS-dən istifadə edir və onlar arasındakı fərqi göstərir.

# %%
ECON_AZ = {'ln_emp': 'ln işçilərin sayı (ölçü)', 'leverage': 'borc yükü (öhdəliklər / aktivlər)',
           'ln_current_ratio': 'ln cari likvidlik əmsalı', 'ln_age': 'ln(1 + yaş)', 'state': 'dövlət mülkiyyəti',
           'foreign': 'xarici mülkiyyət', 'joint': 'birgə mülkiyyət', 'export_share': 'ixracın gəlirdə payı',
           'baku': 'Bakı şəhəri', 'demand_growth': 'sahə tələbinin artımı (Δln DSK buraxılışı)',
           'ulc': 'vahid əmək xərci (əmək haqqı fondu / gəlir)', 'ln_L': 'ln işçilərin sayı', 'ln_K': 'ln əsas fondlar',
           'exporter': 'ixracatçı (0/1)', 'leverage_l1': 'borc yükü, t−1', 'ln_current_ratio_l1': 'ln cari likvidlik, t−1',
           'roa_w_l1': 'ROA, t−1 (±0,3 hüdudunda)', 'ln_emp_l1': 'ln işçilərin sayı, t−1', 'export_share_l1': 'ixrac payı, t−1',
           'sales_growth': 'satışların artımı (Δln gəlir)', 'rel_lp_l1': 'nisbi əmək məhsuldarlığı, t−1',
           'rel_leverage_l1': 'nisbi borc yükü, t−1', 'RTS': 'miqyasdan gəlir (βL + βK)',
           'roa': 'aktivlərin rentabelliyi (ROA)', 'op_margin': 'əməliyyat marjası (EBIT / gəlir)', 'ln_va': 'ln əlavə dəyər',
           'tfp_idx': 'TFP indeksi (Törnqvist)', 'tfp_pf': 'istehsal funksiyası üzrə TFP', 'distress': 'maliyyə çətinliyi (0/1)',
           'inv_rate': 'investisiya norması (kapital qoyuluşu / əsas fondlar t−1)', 'dlsh': 'Δ ln bazar payı'}
SAMPLE_RULES = pd.DataFrame([
    ('all models', 'revenue > 0, employees > 0, total assets > 0, fixed assets > 0', 'gəlir, işçilər, aktivlər və əsas fondlar müsbətdir'),
    ('operating margin', 'unit labour cost (wage bill / revenue) <= 1 (selection on a regressor); EBIT / revenue within [-2, 1]', 'vahid əmək xərci (əmək haqqı fondu / gəlir) ≤ 1 (izahedici dəyişən üzrə seçim); EBIT / gəlir [-2, 1] aralığında'),
    ('sales growth', 'Δ ln revenue bounded at ±1', 'Δ ln gəlir ±1 hüdudunda'),
    ('ROA', 'net profit / total assets winsorised at the pooled 1st and 99th percentiles', 'xalis mənfəət / aktivlər 1% və 99% persentillərdə vinzorlaşdırılıb'),
    ('investment rate', 'capex / fixed assets t-1 within [0, 2]; consecutive years only', 'kapital qoyuluşu / əsas fondlar t−1 [0, 2] aralığında; yalnız ardıcıl illər'),
    ('lagged regressors', 'value of the same firm in the previous calendar year (no lagged dependent variable)', 'eyni müəssisənin əvvəlki ildəki dəyəri (asılı dəyişənin gecikməsi yoxdur)'),
    ('fixed effects', 'firms observed once (singletons) are dropped from the within estimator', 'yalnız bir il müşahidə olunan müəssisələr daxili qiymətləndiricidən çıxarılır'),
    ('optional fields', 'a regressor with < 80% coverage in the estimation sample is dropped and listed', 'nümunədə 80%-dən az dolu olan izahedici dəyişən çıxarılır və göstərilir')],
    columns=['scope', 'rule', 'rule_az'])
SAMPLE_RULES.insert(1, 'scope_az', ['bütün modellər', 'əməliyyat marjası', 'satışların artımı', 'ROA', 'investisiya norması', 'gecikmiş izahedici dəyişənlər',
                                    'sabit effektlər', 'əlavə (məcburi olmayan) sahələr'])

def econ_vars(P, RAT):
    '''Analysis variables from schema fields only, so SYNTHETIC and REAL panels give the same variables.'''
    s = P.sort_values(['firm_id', 'year']).copy()
    ok = (s.revenue > 0) & (s.employees > 0) & (s.total_assets > 0) & (s.fixed_assets > 0)
    s = s[ok].copy(); r = RAT.loc[s.index]
    d = s[['firm_id', 'year', 'nace2', 'region', 'ownership']].copy(); d['year'] = d.year.astype(int)
    tl = s.st_liabilities + s.lt_liabilities
    d['ln_emp'] = np.log(s.employees); d['ln_L'] = d.ln_emp; d['ln_K'] = np.log(s.fixed_assets)
    d['leverage'] = tl / s.total_assets
    d['ln_current_ratio'] = np.log((s.current_assets / s.st_liabilities.where(s.st_liabilities > 0)).where(lambda x: x > 0))
    reg = pd.to_numeric(s['registration_date'].astype(str).str[:4], errors='coerce') if 'registration_date' in s else np.nan
    d['ln_age'] = np.log1p((d.year - reg).clip(lower=0))
    for o in ['state', 'foreign', 'joint']: d[o] = (s.ownership == o).astype(float)
    d['baku'] = (s.region == 'Baku city').astype(float)
    has_x = 'exports' in s and s.exports.notna().mean() > 0.8
    d['export_share'] = (s.exports / s.revenue).clip(0, 1) if has_x else np.nan
    d['exporter'] = (s.exports > 0).astype(float).where(s.exports.notna()) if has_x else np.nan
    gr = np.log(GO).diff()
    d['demand_growth'] = [gr.at[y, b] if (b in gr.columns and y in gr.index) else np.nan for y, b in zip(d.year, d.nace2)]
    d['ulc'] = s.wage_bill / s.revenue
    d['op_margin'] = (s.ebit / s.revenue).where(lambda x: x.between(-2, 1)).where(d.ulc <= 1)   # selection on the regressor (ulc), not on the margin
    roa = s.net_profit / s.total_assets; lo, hi = roa.quantile([0.01, 0.99])
    d['roa'] = roa.clip(lo, hi); d['roa_w'] = roa.clip(-0.3, 0.3)
    va = s.revenue - (s.cost_of_sales - s.wage_bill).clip(lower=0)
    d['ln_va'] = np.log(va.where(va > 0))
    d['tfp_idx'] = s['tfp'] if 'tfp' in s else np.nan
    d['distress'] = ((r.z_zone == 'distress') | (s.equity < 0)).astype(float)
    g = d.groupby('firm_id'); cons = (d.year - g.year.shift(1)) == 1
    lag = lambda c: g[c].shift(1).where(cons)
    for c in ['leverage', 'ln_current_ratio', 'roa_w', 'ln_emp', 'export_share']:
        d[c + '_l1'] = lag(c)
    fa_l1 = s.groupby('firm_id').fixed_assets.shift(1).where(cons)
    d['inv_rate'] = (s.capex / fa_l1).where(lambda x: x.between(0, 2)) if 'capex' in s else np.nan
    d['sales_growth'] = (np.log(s.revenue) - np.log(s.groupby('firm_id').revenue.shift(1))).where(cons).clip(-1, 1)
    d['first_obs'] = ~cons
    return d.replace([np.inf, -np.inf], np.nan)

X_PROF_FE = ['ln_emp', 'leverage', 'ln_current_ratio', 'ln_age', 'export_share', 'demand_growth', 'ulc']
X_PROF_PO = ['ln_emp', 'leverage', 'ln_current_ratio', 'ln_age', 'state', 'foreign', 'joint', 'export_share', 'baku', 'ulc']
ECON_MODELS = [  # id, title_az, title_en, kind, dependent, regressors, fe / dummies, block
 ('B_roa_fe', 'Rentabellik (ROA): iki yönlü sabit effektlər', 'ROA determinants, two-way FE', 'ols', 'roa', X_PROF_FE, 'firm+year', 'a'),
 ('B_roa_pool', 'Rentabellik (ROA): NACE × il effektləri ilə birləşdirilmiş', 'ROA determinants, pooled NACE x year FE', 'ols', 'roa', X_PROF_PO, 'nace_year', 'a'),
 ('B_margin_fe', 'Əməliyyat marjası: iki yönlü sabit effektlər', 'Operating margin determinants, two-way FE', 'ols', 'op_margin', X_PROF_FE, 'firm+year', 'a'),
 ('B_margin_pool', 'Əməliyyat marjası: NACE × il effektləri ilə birləşdirilmiş', 'Operating margin, pooled NACE x year FE', 'ols', 'op_margin', X_PROF_PO, 'nace_year', 'a'),
 ('B_pf_fe', 'İstehsal funksiyası (Kobb–Duqlas): daxili qiymətləndirici', 'Cobb-Douglas production function, within (FE)', 'ols', 'ln_va', ['ln_L', 'ln_K'], 'firm+year', 'b'),
 ('B_pf_pool', 'İstehsal funksiyası: sahə və il dummy-ləri ilə birləşdirilmiş OLS', 'Cobb-Douglas, pooled OLS with sector and year dummies', 'ols', 'ln_va', ['ln_L', 'ln_K'], 'nace+year', 'b'),
 ('B_tfp_idx', 'TFP indeksi (Törnqvist) amilləri: birləşdirilmiş', 'Index-number TFP determinants, pooled NACE x year FE', 'ols', 'tfp_idx',
  ['ln_emp', 'ln_age', 'state', 'foreign', 'joint', 'exporter', 'leverage', 'baku'], 'nace_year', 'c'),
 ('B_tfp_idx_fe', 'TFP indeksi amilləri: iki yönlü sabit effektlər', 'Index-number TFP determinants, two-way FE', 'ols', 'tfp_idx',
  ['ln_emp', 'ln_age', 'exporter', 'leverage'], 'firm+year', 'c'),
 ('B_tfp_pf', 'İstehsal funksiyası üzrə TFP-nin mülkiyyət amilləri', 'Production-function TFP on ownership, pooled NACE x year FE', 'ols', 'tfp_pf',
  ['state', 'foreign', 'joint'], 'nace_year', 'c'),
 ('B_distress', 'Maliyyə çətinliyi (Z\'\'-EM çətinlik zonası və ya mənfi kapital): logit', 'Financial distress logit', 'logit', 'distress',
  ['leverage_l1', 'ln_current_ratio_l1', 'roa_w_l1', 'ln_emp_l1', 'export_share_l1', 'ln_age', 'state', 'foreign', 'demand_growth'], ('year',), 'd'),
 ('B_invest_fe', 'İnvestisiya norması: iki yönlü sabit effektlər', 'Investment rate, two-way FE', 'ols', 'inv_rate',
  ['sales_growth', 'leverage_l1', 'roa_w_l1', 'ln_emp_l1'], 'firm+year', 'e'),
 ('B_invest_pool', 'İnvestisiya norması: NACE × il effektləri ilə birləşdirilmiş', 'Investment rate, pooled NACE x year FE', 'ols', 'inv_rate',
  ['sales_growth', 'leverage_l1', 'roa_w_l1', 'ln_emp_l1', 'state', 'foreign', 'joint'], 'nace_year', 'e'),
 ('B_export', 'İxrac iştirakı: logit', 'Export participation logit', 'logit', 'exporter',
  ['ln_emp_l1', 'foreign', 'state', 'joint', 'ln_age', 'baku'], ('nace2', 'year'), 'g')]
ECON_BLOCK_AZ = {'a': '(a) Rentabellik amilləri', 'b': '(b) İstehsal funksiyası', 'c': '(c) TFP amilləri',
                 'd': '(d) Maliyyə çətinliyi modeli', 'e': '(e) İnvestisiya norması', 'f': '(f) Bazar payının amilləri',
                 'g': '(g) İxrac iştirakı'}
TRUE_MAP = {'B_margin_fe': 'margin', 'B_margin_pool': 'margin', 'B_pf_fe': 'pf', 'B_pf_pool': 'pf', 'B_tfp_pf': 'tfp_own',
            'B_invest_fe': 'invest', 'B_invest_pool': 'invest', 'B_export': 'export'}
NO_TRUTH_AZ = {'B_roa_fe': 'ROA mühasibat zəncirinin qeyri-xətti funksiyasıdır (faiz, vergi, aktivlərin dövriyyəsi): generatorda qapalı həqiqi parametr yoxdur',
               'B_roa_pool': 'ROA üçün generatorda qapalı həqiqi parametr yoxdur',
               'B_tfp_idx': 'indeks TFP müşahidə olunan xərc paylarından hesablanır və generatorun məhsuldarlığından fərqli obyektdir: həqiqi parametr yoxdur',
               'B_tfp_idx_fe': 'indeks TFP üçün həqiqi parametr yoxdur',
               'B_distress': 'çətinlik zonası cari maliyyə əmsallarının deterministik funksiyasıdır: logit üçün həqiqi parametr yoxdur'}
print(f'{len(ECON_MODELS)} firm-level models defined (+ the market-share model of Part 17.2)')

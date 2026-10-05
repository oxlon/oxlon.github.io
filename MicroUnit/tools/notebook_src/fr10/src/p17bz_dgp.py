# %% [markdown]
# ### 17.2b SİNTETİK generatorun struktur qatı (v2): hər müəssisə səviyyəli model üçün məlum parametrlər
#
# > **SİNTETİK — emal xəttinin sınağı, nəticə deyil** (`SYNTHETIC — pipeline test, not results`; sintetik məlumat — texniki nümayiş).
#
# v1 generatoru balans hesabatı və mənfəət-zərər hesabatı maddələrinə təsadüfi nisbətlər verirdi, buna görə məlum
# məlumat yaradan prosesə (DGP) yalnız bazar payı modeli malik idi. v2 pay modelinin, A qatı ilə uyğunluq yoxlamalarının
# və konsentrasiya / giriş-çıxış cədvəllərinin istifadə etdiyi bütün v1 çəkilişlərini (müəssisə identifikatorları, illər,
# NACE, region, mülkiyyət, gəlir, işçilər, əmək haqqı fondu, borc yükü, qeydiyyat tarixləri) saxlayır və **qalan
# maddələri məlum parametrli struktur qat vasitəsilə yenidən yazır**; bu qat ayrıca, başlanğıc dəyəri sabitlənmiş
# təsadüfi ədədlər axınından (`SEED + 1717`) çəkilir. Sxemin bütün uçot eynilikləri əvvəlki kimi dəqiq ödənilir (aktivlər
# = dövriyyə + uzunmüddətli aktivlər; kapital + öhdəliklər = aktivlər; EBIT = gəlir − satışın maya dəyəri − əməliyyat
# xərcləri; ixrac ≤ gəlir).
#
# | Blok | Məlumat yaradan proses (həqiqi parametrlər `DGP_TRUE`-da) |
# |---|---|
# | İxrac | $P(\text{exporter}_{it}) = \Lambda(\psi_b + \psi'z_{it})$, $z$ = gecikmiş ln işçilər, mülkiyyət, ln(1+yaş), Bakı; ixracın payı ~ Beta(2, 5) |
# | Əlavə dəyərin payı | $v_{it} = VA/R = v_b + \delta_t + \theta'x_{it} + \gamma_i + u_{it}$, $x$ = ln işçilər, borc yükü, ln cari likvidlik əmsalı, ln(1+yaş), mülkiyyət, ixracın payı, Bakı, sahə tələbinin artımı; $\gamma_i$ ilkin ölçü ilə korrelyasiyalıdır; $v_b$: sahə üzrə $v$ medianı = sahənin vahid əmək xərcinin medianı + 0,18 (əlavə qiymət, mark-up); $\delta_t$ — il üzrə ümumi sabit hədd (aşağıda kalibrləmə) |
# | Əməliyyat marjası | EBIT/R = $v_{it}e^{\varepsilon_{it}-\sigma^2/2}$ − əmək haqqı fondu/R − digər xərclərin payı: marjanın şərti ortası $\theta'x$ − vahid əmək xərcidir (əmsal −1) |
# | İstehsal (əlavə dəyər) | $\ln VA_{it} = a_b + a_t + \omega_i + 0.45\ln L_{it} + 0.50\ln K_{it} + \varepsilon_{it}$; kapital planlaşdırılan əlavə dəyəri təmin edən amildir; $a_b + a_t$ elə seçilir ki, kapital/gəlir nisbətinin medianı hər sahədə və hər ildə 0,5 olsun; $\omega_i$ = mülkiyyət effektləri + müəssisə küyü (zamana görə sabitdir, buna görə within qiymətləndiricisi əsaslı (consistent), birləşdirilmiş OLS isə əsaslı deyil) |
# | İnvestisiya | kapital qoyuluşu/$K_{t-1}$ = $\iota_b + \iota_i + 0.08\,\Delta\ln R_{it}^{\pm1} - 0.06\,lev_{t-1} + 0.20\,ROA^{w}_{t-1} - 0.004\ln L_{t-1} - 0.02\,state + e_{it}$ (gecikmiş investisiya norması yoxdur) |
# | Maliyyə çətinliyi, ROA, indeks TFP | **qapalı formada həqiqi parametr yoxdur**: onlar yuxarıdakı blokların qeyri-xətti uçot funksiyalarıdır (bərpa cədvəlində göstərilir) |
#
# **Kalibrləmə (v2.2, `DGP_CAL`; səviyyə sabitləri, qiymətləndirilən parametrlər deyil).** Əvvəlki versiyada zərərlə işləyən
# müəssisələrin payı illər üzrə 29%-dən 42%-ə qədər sürüşürdü, aqreqat xalis marja isə 2025-ci ildə gəlirin 5,4%-i idi:
# kapitalın miqyas sabiti yalnız sahə üzrə müəyyən edildiyindən nominal əmək məhsuldarlığının artımı kapital/gəlir
# nisbətini və faiz yükünü mexaniki olaraq artırırdı. İndi (1) kapitalın miqyas sabiti sahə və il üzrə additivdir
# (kapital/gəlir medianı hər sahə-ildə 0,5); (2) əlavə qiymət 0,15-dən 0,18-ə qaldırılıb; (3) il üzrə ümumi sabit hədd
# $\delta_t$ bisseksiya ilə elə seçilir ki, hər il müəssisələrin **25%-i** zərərlə işləsin (vergidən əvvəlki mənfəət < 0).
# Hədəfin əsası: DVX bəyannamələri bəyan edilmiş zərərlərin **məbləğini** verir (vergi tutulan mənfəətin 14–27%-i), lakin
# zərərli ödəyicilərin **sayını** vermir; müəssisə səviyyəli mühasibat məlumatlarında emal sənayesi üzrə zərərli
# müəssisələrin payı adətən beşdə bir ilə üçdə bir arasında olur və 25% bu intervalın ortasıdır. Bu, kalibrləmə seçimidir,
# Azərbaycan statistikası deyil. Aqreqat marja üçün istinad DVX bəyannaməsi üzrə xalis marjadır (çıxılan xərclərin
# 10–13%-i). $\delta_t$ və $a_t$ il üzrə ümumi sabitlərdir və hər qiymətləndiricinin il effektləri (firma + il, NACE × il,
# NACE + il) tərəfindən udulur; buna görə `DGP_TRUE`-dakı həqiqi parametrlər və bərpa testləri dəyişmir.
#
# Heç bir yerdə AR və ya digər dinamik proses qiymətləndirilmir; generatorun məhsuldarlıq termini qəsdən zamana görə
# sabitdir.

# %%
DGP_SEED = SEED + 1717
DGP_TRUE = {
    'export': {'ln_emp_l1': 0.40, 'foreign': 1.00, 'state': -0.60, 'joint': 0.40, 'ln_age': 0.20, 'baku': 0.30},
    'va_share': {'ln_emp': 0.010, 'leverage': -0.060, 'ln_current_ratio': 0.012, 'ln_age': 0.006, 'state': -0.030,
                 'foreign': 0.025, 'joint': 0.010, 'export_share': 0.050, 'baku': 0.010, 'demand_growth': 0.080},
    'pf': {'ln_L': 0.45, 'ln_K': 0.50},
    'tfp_own': {'state': -0.08, 'foreign': 0.10, 'joint': 0.05},
    'invest': {'sales_growth': 0.08, 'leverage_l1': -0.06, 'roa_w_l1': 0.20, 'ln_emp_l1': -0.004, 'state': -0.02},
    'sd': {'eps_va': 0.10, 'u_v': 0.035, 'gamma': 0.025, 'gamma_size': 0.010, 'eta_omega': 0.15, 'e_inv': 0.035,
           'iota_firm': 0.02, 'iota_branch': 0.01}}
# the operating-margin model: VA-share effects carry over one for one; the unit labour cost enters with -1 (accounting)
DGP_TRUE['margin'] = dict(DGP_TRUE['va_share'], ulc=-1.0)
# calibration constants (levels, not estimated parameters - Part 17.2b): mark-up of the value-added share over the branch
# unit labour cost, median capital / revenue, and the share of loss-making firms that fixes the year intercept
DGP_CAL = {'markup': 0.18, 'k_r': 0.5, 'loss_target': 0.25}

def structural_overlay(S, go, seed=DGP_SEED, T=DGP_TRUE, cal=None):
    '''Overwrite the free balance-sheet / P&L items of the v1 synthetic panel with the structural layer.
    Keeps revenue, employees, wage bill, leverage, ownership, region, dates. Returns (panel, latent truth frame).'''
    rg = np.random.default_rng(seed); cal = DGP_CAL if cal is None else cal
    S = S.sort_values(['firm_id', 'year']).reset_index(drop=True)
    n = len(S); f = S.groupby('firm_id', sort=False)
    R, L, W = S.revenue.to_numpy(float), S.employees.to_numpy(float), S.wage_bill.to_numpy(float)
    TA0 = S.total_assets.to_numpy(float); TL0 = (S.st_liabilities + S.lt_liabilities).to_numpy(float)
    lev = TL0 / TA0
    c_ca = (S.current_assets / S.total_assets).to_numpy(float)              # v1 draws reused as ratios
    s_st = (S.st_liabilities / TL0).to_numpy(float)
    fr_cash, fr_rec = (S.cash / S.current_assets).to_numpy(float), (S.receivables / S.current_assets).to_numpy(float)
    int_r, re_r = (S.interest / TL0).to_numpy(float), (S.retained_earnings / S.equity).to_numpy(float)
    ibd_r, dep_r = (S.interest_bearing_debt / TL0).to_numpy(float), (S.depreciation / S.fixed_assets).to_numpy(float)
    ocf_n = ((S.operating_cash_flow - S.net_profit - S.depreciation) / S.revenue).to_numpy(float)
    own = S.ownership.to_numpy(); st_, fo_, jo_ = [(own == o).astype(float) for o in ('state', 'foreign', 'joint')]
    baku = (S.region == 'Baku city').to_numpy(float)
    age = (S.year - S.registration_date.astype(str).str[:4].astype(int)).clip(lower=0).to_numpy(float)
    lnage, lnL = np.log1p(age), np.log(L)
    lnL_l1 = f.employees.shift(1).pipe(np.log).to_numpy(float)
    dem = np.array([np.log(go.loc[y, b] / go.loc[y - 1, b]) for y, b in zip(S.year, S.nace2)])
    firms = S.firm_id.unique(); fidx = pd.Index(firms).get_indexer(S.firm_id)
    br = sorted(S.nace2.unique()); bidx = pd.Index(br).get_indexer(S.nace2)
    sd = T['sd']
    # --- firm- and branch-level effects
    z0 = pd.Series(lnL).groupby(fidx).transform('first').to_numpy(); z0 = (z0 - z0.mean()) / z0.std()
    gamma = sd['gamma_size'] * z0 + rg.normal(0, sd['gamma'], len(firms))[fidx]
    omega = (T['tfp_own']['state'] * st_ + T['tfp_own']['foreign'] * fo_ + T['tfp_own']['joint'] * jo_
             + rg.normal(0, sd['eta_omega'], len(firms))[fidx])
    psi_b = (-1.9 + rg.normal(0, 0.3, len(br)))[bidx]
    iota = rg.normal(0, sd['iota_firm'], len(firms))[fidx] + rg.normal(0, sd['iota_branch'], len(br))[bidx]
    # --- exports (lagged size; first firm-year uses current size and is outside every estimation sample)
    te = T['export']
    xb = (psi_b + te['ln_emp_l1'] * (np.where(np.isfinite(lnL_l1), lnL_l1, lnL) - 2.3) + te['foreign'] * fo_ + te['state'] * st_
          + te['joint'] * jo_ + te['ln_age'] * lnage + te['baku'] * baku)
    exporter = (rg.random(n) < 1 / (1 + np.exp(-xb))).astype(float)
    exp_sh = np.where(exporter > 0, rg.beta(2, 5, n), 0.0)
    # --- value-added share and the operating margin
    tv = T['va_share']; ln_cr = np.log(c_ca / (s_st * lev))
    v_x = (tv['ln_emp'] * (lnL - 2.3) + tv['leverage'] * lev + tv['ln_current_ratio'] * ln_cr + tv['ln_age'] * lnage
           + tv['state'] * st_ + tv['foreign'] * fo_ + tv['joint'] * jo_ + tv['export_share'] * exp_sh + tv['baku'] * baku
           + tv['demand_growth'] * dem + gamma + rg.normal(0, sd['u_v'], n))
    wr = pd.Series(W / R).groupby(bidx).transform('median').to_numpy()
    target = np.clip(wr + cal['markup'], 0.20, 0.60)
    v_b = target - pd.Series(v_x).groupby(bidx).transform('median').to_numpy()
    eps = rg.normal(0, sd['eps_va'], n)
    phi = rg.uniform(0.03, 0.12, n)                                           # other operating costs / revenue
    yu, yi = np.unique(S.year.to_numpy(), return_inverse=True); tp = T['pf']
    def layer(dv):
        '''value added, EBIT, capital and profit before tax for a year-common shift dv[year] of the value-added share'''
        v_raw = v_b + dv[yi] + v_x; v = np.clip(v_raw, 0.03, 0.80)
        va_true = v * R * np.exp(-sd['eps_va'] ** 2 / 2)
        va_raw = va_true * np.exp(eps); va = np.minimum(va_raw, 0.98 * R)
        # capital: the input that delivers the planned value added given labour and productivity; the scale constant is
        # additive in branch and year (median capital / revenue = k_r in every branch and year; absorbed by the year effects)
        lnK0 = (np.log(va_true) - omega - tp['ln_L'] * lnL) / tp['ln_K']
        r_kr = pd.Series(lnK0 - np.log(R)); m_b = r_kr.groupby(bidx).transform('median')
        a_b = tp['ln_K'] * ((m_b + (r_kr - m_b).groupby(yi).transform('median')).to_numpy() - np.log(cal['k_r']))
        K = np.exp(lnK0 - a_b / tp['ln_K']); ebit = va - W - phi * R
        return v_raw, v, va_raw, va, K, ebit, ebit - lev * K / (1 - c_ca) * int_r
    # calibration of the year-common intercept: the share of loss-making firms (profit before tax < 0) equals
    # cal['loss_target'] in every year (bisection; a year intercept is absorbed by the year effects of every estimator)
    lo, hi = np.full(len(yu), -0.2), np.full(len(yu), 0.2)
    for _ in range(36):
        dv = (lo + hi) / 2; ls = pd.Series(layer(dv)[-1] < 0).groupby(yi).mean().to_numpy()
        lo, hi = np.where(ls > cal['loss_target'], dv, lo), np.where(ls > cal['loss_target'], hi, dv)
    dv = (lo + hi) / 2
    v_raw, v, va_raw, va, K, ebit, _ = layer(dv)
    cos = R - va + W
    TA = K / (1 - c_ca); TL = lev * TA; CA = c_ca * TA
    out = S.copy()
    out['total_assets'], out['fixed_assets'], out['current_assets'] = TA, K, CA
    out['cash'], out['receivables'] = CA * fr_cash, CA * fr_rec
    out['inventories'] = CA - out.cash - out.receivables
    out['equity'] = TA - TL; out['st_liabilities'] = TL * s_st; out['lt_liabilities'] = TL - out.st_liabilities
    out['interest'] = TL * int_r; out['retained_earnings'] = out.equity * re_r
    out['interest_bearing_debt'] = TL * ibd_r
    out['trade_payables'] = (out.st_liabilities - 0.5 * out.interest_bearing_debt).clip(lower=0)
    out['cost_of_sales'], out['operating_expenses'], out['ebit'] = cos, phi * R, ebit
    pbt = ebit - out.interest.to_numpy(); out['net_profit'] = np.where(pbt > 0, 0.8 * pbt, pbt)
    out['depreciation'] = K * dep_r
    out['operating_cash_flow'] = out.net_profit + out.depreciation + R * ocf_n
    out['exports'] = exp_sh * R
    # --- investment rate on lagged capital (no lagged investment rate anywhere)
    ti = T['invest']; g = out.groupby('firm_id', sort=False)
    roa_w = (out.net_profit / out.total_assets).clip(-0.3, 0.3)
    K_l1, lev_l1, roa_l1 = g.fixed_assets.shift(1).to_numpy(), pd.Series(lev).groupby(fidx).shift(1).to_numpy(), roa_w.groupby(fidx).shift(1).to_numpy()
    sg = np.clip(np.log(R) - pd.Series(np.log(R)).groupby(fidx).shift(1).to_numpy(), -1, 1)
    ir_raw = (0.25 + iota + ti['sales_growth'] * sg + ti['leverage_l1'] * lev_l1 + ti['roa_w_l1'] * roa_l1
              + ti['ln_emp_l1'] * lnL_l1 + ti['state'] * st_ + rg.normal(0, sd['e_inv'], n))
    first = ~np.isfinite(K_l1)
    ir0 = np.clip(0.15 + rg.normal(0, sd['e_inv'], n), 0.01, None)
    ir = np.where(first, ir0, np.maximum(ir_raw, 0.002))
    out['capex'] = np.where(first, ir0 * K, ir * K_l1)
    truth = pd.DataFrame({'firm_id': out.firm_id, 'year': out.year, 'omega': omega, 'gamma': gamma, 'v': v, 'eps': eps,
                          'exporter_latent': xb, 'ir_raw': ir_raw})
    clip = dict(v_clipped=int((v != v_raw).sum()), va_capped=int((va != va_raw).sum()),
                ir_truncated=int(((~first) & (ir_raw < 0.002)).sum()), n=int(n), n_inv=int((~first).sum()),
                v_year={int(y): round(float(d), 4) for y, d in zip(yu, dv)})
    return out, truth, clip
print('[SYNTHETIC] structural layer defined: exports (logit), value-added share and margin, value-added production '
      'function, investment rate - true parameters in DGP_TRUE')

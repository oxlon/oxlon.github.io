# %%
TERM_AZ = {'const': 'sabit', 'dem': 'sektor tələbinin artımı (FR1 real ƏDV, %)', 'ln_hhi_l1': 'ln HHI (bazar, t−1)', 'ln_size_l1': 'ln bazar həcmi (gəlir, t−1)',
           'age0': '0 yaş (qeydiyyat ili)', 'age1': '1 yaş', 'age2': '2 yaş', 'age3_4': '3–4 yaş', 'age5_9': '5–9 yaş', 'age3': '3 yaş', 'age4': '4 yaş',
           'young12': '1–2 yaş', 'small': 'kiçik (baza: mikro)', 'medium': 'orta (baza: mikro)', 'large': 'iri (baza: mikro)',
           'state': 'dövlət (baza: özəl)', 'municipal': 'bələdiyyə (baza: özəl)', 'foreign': 'xarici (baza: özəl)', 'joint': 'birgə (baza: özəl)',
           'ln_avc': 'ln orta dəyişən xərc', 'ln_avc_trend': 'ln orta dəyişən xərc × (il − 2022)', 'ln_hhi': 'ln HHI (bölmə bazarı)',
           'export_share': 'ixrac intensivliyi, % (idxal payı yoxdur)', 'ln_size': 'ln bazar həcmi', 'entry_rate': 'giriş əmsalı, %'}
def term_az(c):
    if c in TERM_AZ: return TERM_AZ[c]
    for pre, lab in [('yr_', 'il sabit effekti '), ('sec_', 'bölmə sabit effekti '), ('reg_', 'region sabit effekti '), ('ln_avc_', 'ln orta dəyişən xərc, bölmə ')]:
        if c.startswith(pre): return lab + c[len(pre):]
    return c
MODEL_AZ = {'entry_poisson': 'Girişlərin sayı: Puasson (region və il sabit effektləri)', 'entry_nb2': 'Girişlərin sayı: mənfi binomial NB2 (region və il sabit effektləri)',
            'entry_poisson_secfe': 'Girişlərin sayı: Puasson + bölmə sabit effektləri', 'exit_logit': 'Çıxış: diskret zamanlı təhlükə (hazard) modeli, logit',
            'exit_cloglog': 'Çıxış: diskret zamanlı təhlükə (hazard) modeli, cloglog', 'boone_pooled': 'Boone indikatoru: birləşdirilmiş reqressiya (ümumi meyl + trend)',
            'boone_sector': 'Boone indikatoru: bölmələr üzrə meyllər', 'scp': 'Struktur–davranış–nəticə: marja (PCM) HHI üzrə',
            'mob_instability': 'Bazar paylarının qeyri-sabitliyinin determinantları', 'mob_rank': 'Sıra mobilliyinin determinantları',
            'entrant_profile': 'Yeni müəssisələrin nisbi ölçüsü: yaş profili', 'postentry_growth': 'Girişdən sonrakı artım (nisbi ölçünün dəyişməsi) yaş üzrə',
            'recovery_revenue': 'Parametr bərpası G1: gəlir–xərc elastikliyi', 'recovery_exit': 'Parametr bərpası G2: çıxış təhlükəsi (şərti Puasson)'}

def _r(T, m, t, col='ratio'):
    x = T[(T.model == m) & (T.term == t)]
    return float(x[col].iloc[0]) if len(x) else np.nan

def econ_interpret(T, extra, tag):
    '''One Azerbaijani interpretation per model, generated from the estimates.'''
    I = {}
    for m in ['entry_poisson', 'entry_nb2', 'entry_poisson_secfe']:
        I[m] = (f"{tag}: tələb artımı 1 faiz bəndi yüksək olduqda girişlərin sayı {(_r(T, m, 'dem') - 1) * 100:+.2f}% dəyişir (IRR {_r(T, m, 'dem'):.3f}); "
                f"HHI 10% yüksək olduqda {(_r(T, m, 'ln_hhi_l1') ** np.log(1.1) - 1) * 100:+.1f}%, bazar həcmi 10% böyük olduqda {(_r(T, m, 'ln_size_l1') ** np.log(1.1) - 1) * 100:+.1f}%.")
    I['entry_nb2'] += f" Həddən artıq dispersiya α = {extra['alpha']:.2f} (LR p = {extra['lr_p']:.3g}): Puasson SE-ləri yalnız klaster düzəlişi ilə etibarlıdır."
    for m, nm in [('exit_logit', 'şans nisbəti'), ('exit_cloglog', 'təhlükə nisbəti')]:
        I[m] = (f"{tag}: iri müəssisələr üçün {nm} {_r(T, m, 'large'):.3f}, orta {_r(T, m, 'medium'):.3f}, kiçik {_r(T, m, 'small'):.3f} (mikro = 1); "
                f"1 yaşda {_r(T, m, 'age1'):.2f}, 2 yaşda {_r(T, m, 'age2'):.2f} (10+ yaş = 1); dövlət mülkiyyəti {_r(T, m, 'state'):.2f}.")
    I['boone_pooled'] = (f"{tag}: ümumi Boone meyli {_r(T, 'boone_pooled', 'ln_avc', 'coef'):.2f} — xərci 1% yüksək müəssisənin mənfəəti "
                         f"{abs(_r(T, 'boone_pooled', 'ln_avc', 'coef')):.2f}% aşağıdır; trend {_r(T, 'boone_pooled', 'ln_avc_trend', 'coef'):+.3f} ildə "
                         f"(mənfi trend = rəqabətin güclənməsi). Yalnız mənfəətli müəssisələr: seçim əyilməsi meyli sıfıra doğru çəkir.")
    I['boone_sector'] = f"{tag}: bölmələr üzrə Boone meylləri {extra['boone_min']:.2f} ilə {extra['boone_max']:.2f} arasındadır; daha mənfi = daha sərt rəqabət (sıralama kimi oxunur)."
    I['scp'] = (f"{tag}: ln HHI 1 vahid artdıqda marja {_r(T, 'scp', 'ln_hhi', 'coef'):+.2f} faiz bəndi dəyişir (p = {_r(T, 'scp', 'ln_hhi', 'p'):.2f}). "
                "Endogenlik: konsentrasiya və marja birgə müəyyənləşir (Demsets) — səbəb-nəticə əlaqəsi deyil, şərti assosiasiyadır; idxal payı reyestrdə yoxdur.")
    I['mob_instability'] = (f"{tag}: ln HHI(t−1) 1 vahid yüksək olduqda payların qeyri-sabitliyi {_r(T, 'mob_instability', 'ln_hhi_l1', 'coef'):+.2f} f.b., "
                            f"giriş əmsalı 1 f.b. yüksək olduqda {_r(T, 'mob_instability', 'entry_rate', 'coef'):+.3f} f.b. dəyişir.")
    I['mob_rank'] = f"{tag}: sıra mobilliyi (1 − Spirmen ρ) üzrə ln HHI(t−1) əmsalı {_r(T, 'mob_rank', 'ln_hhi_l1', 'coef'):+.4f}, giriş əmsalı {_r(T, 'mob_rank', 'entry_rate', 'coef'):+.4f}."
    I['entrant_profile'] = (f"{tag}: qeydiyyat ilində müəssisə eyni bölmə-il-ölçü qrupundakı 5+ yaşlı müəssisələrdən {(np.exp(_r(T, 'entrant_profile', 'age0', 'coef')) - 1) * 100:+.0f}% "
                            f"kiçikdir; 2 yaşda fərq {(np.exp(_r(T, 'entrant_profile', 'age2', 'coef')) - 1) * 100:+.1f}%.")
    I['postentry_growth'] = (f"{tag}: nisbi ölçünün illik artımı 2 yaşda {_r(T, 'postentry_growth', 'age2', 'coef'):+.3f} log vahid (5+ yaşa nisbətən); "
                             "asılı dəyişən fərqdir, sağ tərəfdə gecikmiş asılı dəyişən yoxdur.")
    return I

def layer_b_econ(REG, mode, outdir, LB, write=True):
    '''Models (a)-(g) on a loaded register; writes FR12_SYNTHETIC_econ_*.csv (watermarked) or FR12_FIRM_econ_*.csv.'''
    t0 = time.time(); P = econ_prep(REG, LB); tag = ECON_TAG[mode]; pre = 'FR12_SYNTHETIC_econ_' if mode == 'SYNTHETIC' else 'FR12_FIRM_econ_'
    M = lb_entry(P); od = M.pop('_overdispersion'); ex = lb_exit(P); M.update({k: ex[k] for k in ['exit_logit', 'exit_cloglog']})
    surv = predicted_survival(P, LB, ex); bo = lb_boone(P, LB); D = division_year(P, LB); M.update(lb_scp_mob(D)); en = lb_entrant(P)
    T = [ratio_table(k, M[k]['res'], 'IRR', cov='klaster (bazar)', n=int(M[k]['res'].nobs)) for k in ['entry_poisson', 'entry_nb2', 'entry_poisson_secfe']]
    T += [ratio_table(k, M[k]['res'], kd, cov='klaster (bölmə × region)', n=int(M[k]['res'].nobs)) for k, kd in [('exit_logit', 'OR'), ('exit_cloglog', 'HR')]]
    T += [ratio_table(k, M[k]['res'], 'coef', cov='klaster (NACE bölməsi)', n=int(M[k]['res'].nobs)) for k in ['scp', 'mob_instability', 'mob_rank']]
    W = {'entrant_profile': en['entrant_profile'], 'postentry_growth': en['postentry_growth']}
    if bo: W.update(boone_pooled=bo['boone_pooled'], boone_sector=bo['boone_sector'])
    T += [wls_table(k, v['fit'], cov='klaster (qeyd)') for k, v in W.items()]
    COEF = pd.concat(T, ignore_index=True); COEF.insert(1, 'model_az', COEF.model.map(MODEL_AZ)); COEF.insert(3, 'term_az', COEF.term.map(term_az))
    COEF['term_type'] = np.where(COEF.term.str.match(r'^(const|yr_|sec_|reg_)'), 'sabit / sabit effekt', np.where(COEF.term == 'alpha', 'dispersiya parametri (NB2 α)', 'izahedici dəyişən'))
    COEF.loc[COEF.term == 'alpha', ['ratio', 'ratio_ci_low', 'ratio_ci_high']] = np.nan
    xb = dict(alpha=od['alpha'], lr_p=od['lr_p'], boone_min=float(np.min(bo['boone_sector']['fit']['b'])) if bo else np.nan,
              boone_max=float(np.max(bo['boone_sector']['fit']['b'])) if bo else np.nan)
    INT = econ_interpret(COEF, xb, tag); COEF['interpretation_az'] = COEF.model.map(INT)
    rec, rfits = lb_recovery(P, ex) if mode == 'SYNTHETIC' else (None, {})
    tabs = {'coefficients': COEF, 'entry_irr': COEF[COEF.model.str.startswith('entry') & (COEF.term_type == 'izahedici dəyişən')],
            'exit_hazard': COEF[COEF.model.str.startswith('exit') & (COEF.term_type == 'izahedici dəyişən')], 'survival': surv, 'cohorts': en['cohorts']}
    if bo: tabs['boone_sector_year'] = bo['sector_year'].assign(interpretation_az=f'{tag}: Boone meyli bölmə-il üzrə, 95% etibarlılıq intervalı (normal, HC0)')
    if rec is not None:
        rec['interpretation_az'] = (f"{tag}: generatorun həqiqi parametrləri ilə müqayisə; örtük (coverage) = həqiqi dəyərin 95% EI daxilində olması. "
                                    "G2 ölçü əmsalları: generator ölüm hallarını qruplaşdırılmış qeydlər üzrə seçir (bir mikro qrup bir seçimdə bütün ölümləri götürə bilər), "
                                    "ona görə HAZ müəssisə səviyyəsində təhlükə nisbəti deyil — bərpa testi bunu aşkar edir.")
        tabs['recovery'] = rec
        tabs['recovery_not_defined'] = pd.DataFrame([
            ('(a) entry counts', 'births are calibrated to DSK section/region aggregates; divisions drawn uniformly within the section: no behavioural parameter',
             'girişlər DSK-nın bölmə/region aqreqatlarına kalibrlənib, bölmə daxilində NACE bölməsi bərabər ehtimalla seçilir: davranış parametri yoxdur'),
            ('(c) Boone slope', 'ln profit = ln revenue + ln(1 − avc − opex share): the slope mixes −γ_s with a firm-varying margin term; its revenue part γ_s is recovered in G1',
             'ln mənfəət = ln gəlir + ln(1 − orta xərc − əməliyyat xərci payı): meyl −γ_s ilə müəssisədən asılı marja həddini qarışdırır; gəlir hissəsi γ_s G1-də bərpa olunur'),
            ('(d) SCP, (e) mobility', 'the generator has no conduct or mobility parameter; shares move only through i.i.d. revenue shocks (sd 0.25)',
             'generatorda davranış və ya mobillik parametri yoxdur; paylar yalnız müstəqil gəlir şokları ilə dəyişir (sd 0.25)')],
            columns=['model', 'why_no_true_parameter_en', 'why_no_true_parameter_az'])
    SUMM = pd.DataFrame([dict(model=k, model_az=MODEL_AZ[k], n=int(COEF[COEF.model == k].n.iloc[0]), interpretation_az=INT.get(k, '')) for k in COEF.model.unique()])
    if rec is not None:
        SUMM.loc[len(SUMM)] = dict(model='recovery', model_az='Parametr bərpası (G1, G2, (b))', n=len(rec), interpretation_az=(
            f"{tag}: {int(rec.covered.sum())} / {len(rec)} həqiqi dəyər 95% EI daxilindədir; " + '; '.join(f"{' '.join(b.split(' ')[:2]).rstrip(',') if b.startswith('(b)') else b.split(' ')[0]} {g.covered.mean():.0%}" for b, g in rec.groupby('block', sort=False))))
    tabs['summary'] = SUMM
    tabs['survival'] = surv.assign(interpretation_az=f'{tag}: kohortlar üzrə Kaplan–Meyer sağ qalması və təhlükə modellərinin (logit, cloglog) proqnozlaşdırdığı sağ qalma, tam yaş illəri üzrə')
    tabs['cohorts'] = en['cohorts'].assign(interpretation_az=f'{tag}: kohort × yaş — müəssisələrin sayı, nisbi ölçü (bölmə × il × ölçü qrupu ortasına nisbətən, log), sağ qalanların payı')
    if 'recovery_not_defined' in tabs: tabs['recovery_not_defined']['interpretation_az'] = f'{tag}: bu modellər üçün generatorun həqiqi parametri yoxdur'
    if write:
        for k, v in tabs.items():
            v = v.copy()
            if mode == 'SYNTHETIC': v.insert(0, 'WATERMARK', SYN_MARK)
            v.to_csv(Path(outdir) / f'{pre}{k}.csv', index=False)
    return dict(models=M, wls=W, recovery=rec, recovery_fits=rfits, tables=tabs, overdispersion=od, exit_meta=dict(dropped=ex['_dropped'], bands=ex['_bands']),
                P=P, D=D, runtime=time.time() - t0, prefix=pre)

# %%
def _fmt(v, d=3):
    return '—' if v is None or not np.isfinite(v) else f'{v:.{d}f}'.replace('-', '−')

def _sig_terms(c, k=4, alpha=0.05):
    s = c[(c.p < alpha)].assign(at=lambda x: x.t.abs()).sort_values('at', ascending=False).head(k)
    if s.empty: return '5% səviyyəsində əhəmiyyətli amil yoxdur'
    return '; '.join(f"{r.term_az} {_fmt(r.coef)} ({'artırır' if r.coef > 0 else 'azaldır'}, p {'< 0.001' if r.p < 0.001 else '= ' + _fmt(r.p)})"
                     for r in s.itertuples())

def interpret_az(E):
    pre = f'[{SYN_AZ}] ' if E['syn'] else '[real müəssisə məlumatı] '
    out, C, S = [], E['COEF'], E['SUM'].set_index('model_id')
    for mid, f in E['F'].items():
        c = C[C.model_id == mid]
        if mid == 'B_share':
            b, se = f.b, f.se
            txt = (f"Bazar payının illik dəyişməsi əvvəlki ilin nisbi əmək məhsuldarlığı ilə {_fmt(b.iloc[0])} (s.x. {_fmt(se.iloc[0])}), nisbi borc yükü "
                   f"ilə {_fmt(b.iloc[1])} (s.x. {_fmt(se.iloc[1])}) əlaqəlidir; {f.n:,} müşahidə. Gecikmiş pay modeldə yoxdur; proqnozda paylar sahə daxilində "
                   f"normallaşdırılır.")
            out.append(dict(model_id=mid, interpretation_az=pre + txt)); continue
        s = S.loc[mid]; base = f"{int(s.n_firms):,} müəssisə, {int(s.n_obs):,} müşahidə ({int(s.year_min)}–{int(s.year_max)}). "
        if f.kind == 'ols':
            base += f"{'Daxili ' if 'within' in s.r2_type else ''}R² = {_fmt(s.r2)}. "
        if f.block == 'a':
            txt = base + 'Əsas amillər: ' + _sig_terms(c) + '. ' + (
                'Zamanla dəyişməyən amillər (mülkiyyət, region) müəssisə effektlərinə daxildir; onlar birləşdirilmiş modeldə qiymətləndirilir.'
                if 'fe' in mid else 'Sahə tələbinin artımı NACE × il effektlərinə daxildir; o, iki yönlü FE modelində qiymətləndirilir.')
        elif f.block == 'b':
            txt = base + (f"Əmək elastikliyi {_fmt(f.b['ln_L'])}, kapital elastikliyi {_fmt(f.b['ln_K'])}; miqyasdan gəlir {_fmt(s.RTS)} "
                          f"[{_fmt(s.ci_low)}, {_fmt(s.ci_high)}]; sabit gəlir (CRS) hipotezi p = {_fmt(s.crs_p, 4)} ilə "
                          f"{'rədd edilir' if s.crs_p < 0.05 else 'rədd edilmir'}. Olley–Pakes / Levinsohn–Petrin / ACF tətbiq edilmir: onlar "
                          f"məhsuldarlıq üçün avtoreqressiv (Markov) hərəkət qanunu qiymətləndirir, bu isə sifarişçinin məhdudiyyətinə ziddir.")
            if mid == 'B_pf_pool':
                txt += ' Birləşdirilmiş OLS müəssisənin daimi məhsuldarlığını nəzərə almır; FE qiymətləndiricisi ilə fərq bu sürüşməni göstərir.'
        elif f.block == 'c':
            txt = base + 'TFP ilə əlaqəli amillər: ' + _sig_terms(c) + '.'
        elif f.block == 'd':
            o = getattr(f, 'oos', None) or {}
            am = f.ame.assign(at=lambda x: x['ame'].abs()).sort_values('at', ascending=False).head(3)
            txt = base + (f"Çətinlik tezliyi {_fmt(100 * s.event_rate, 1)}%. AUC nümunədə {_fmt(s.auc)}, son iki ildə (nümunədən kənar, "
                          f"{o.get('train_years', '')} üzrə qiymətləndirilmiş) {_fmt(o.get('auc_oos'))}; Brier {_fmt(s.brier, 4)}; Hosmer–Lemeshow p = "
                          f"{_fmt(s.hosmer_lemeshow_p)}. Ən böyük orta marjinal effektlər: "
                          + '; '.join(f"{ECON_AZ.get(i, i)} {_fmt(r['ame'], 4)}" for i, r in am.iterrows()) + '. Gecikmiş çətinlik statusu modelə daxil edilmir.')
        elif f.block == 'e':
            txt = base + 'İnvestisiya normasının amilləri: ' + _sig_terms(c) + '. Gecikmiş investisiya norması modeldə yoxdur.'
        elif f.block == 'g':
            am = f.ame.assign(at=lambda x: x['ame'].abs()).sort_values('at', ascending=False).head(3)
            txt = base + (f"İxracatçıların payı {_fmt(100 * s.event_rate, 1)}%; AUC {_fmt(s.auc)}. Ən böyük orta marjinal effektlər: "
                          + '; '.join(f"{ECON_AZ.get(i, i)} {_fmt(r['ame'], 4)}" for i, r in am.iterrows()) + '.')
        else:
            txt = base
        out.append(dict(model_id=mid, interpretation_az=pre + txt))
    R = E['REC']
    if E['syn'] and 'covered' in R:
        r = R.dropna(subset=['covered']); cons = r[~r.model_id.isin(['B_pf_pool', 'B_margin_pool'])]
        txt = (f"Generatorun məlum parametrləri ilə müqayisə: {int(r.covered.sum())}/{len(r)} həqiqi parametr 95% etibarlılıq intervalına düşür; "
               f"ardıcıl (FE, logit, pay modeli) qiymətləndiricilərdə {int(cons.covered.sum())}/{len(cons)}. Birləşdirilmiş OLS-in istehsal "
               f"funksiyasında və marjanın ölçü əmsalında sürüşmə gözləniləndir (daimi müəssisə effekti izahedici dəyişənlərlə korrelyasiyalıdır). "
               f"ROA, indeks TFP və çətinlik modeli üçün generatorda qapalı həqiqi parametr yoxdur.")
        out.append(dict(model_id='recovery', interpretation_az=pre + txt))
    elif not E['syn']:
        out.append(dict(model_id='recovery', interpretation_az=pre + 'Real məlumatda həqiqi parametrlər məlum deyil; bərpa testi tətbiq olunmur.'))
    return pd.DataFrame(out)

def econ_tables(E):
    F = E['F']; T = {'econ_coefficients': E['COEF'], 'econ_models': E['SUM'], 'econ_recovery': E['REC'],
                     'econ_sample_rules': SAMPLE_RULES, 'econ_interpretation_az': interpret_az(E)}
    if 'B_share' in F:
        f = F['B_share']; tq = stats.t.ppf(0.975, f.dof); t = f.b / f.se
        T['econ_coefficients'] = pd.concat([T['econ_coefficients'], pd.DataFrame({
            'model_id': 'B_share', 'estimator': f.est, 'dependent': 'dlsh', 'term': f.b.index, 'term_az': [ECON_AZ[c] for c in f.b.index],
            'coef': f.b.values, 'se': f.se.values, 't': t.values, 'p': 2 * stats.t.sf(np.abs(t.values), f.dof),
            'ci_low': (f.b - tq * f.se).values, 'ci_high': (f.b + tq * f.se).values, 'n_obs': f.n, 'n_firms': f.firms})], ignore_index=True)
    pf = [dict(model_id=m, **rts_test(F[m])) for m in ('B_pf_fe', 'B_pf_pool') if m in F]
    if pf: T['econ_production_function'] = pd.DataFrame(pf)
    for m, nm in [('B_distress', 'distress'), ('B_export', 'export')]:
        if m not in F: continue
        f = F[m]; T[f'econ_{nm}_ame'] = f.ame.rename_axis('term').reset_index().assign(term_az=lambda x: x.term.map(ECON_AZ))
        cal = f.calib.assign(sample='in-sample')
        roc = roc_points(f.yv, f.prob).assign(sample='in-sample')
        if getattr(f, 'calib_oos', None) is not None:
            cal = pd.concat([cal, f.calib_oos.assign(sample='out-of-sample (last two years)')])
            roc = pd.concat([roc, f.roc_oos.assign(sample='out-of-sample (last two years)')])
        T[f'econ_{nm}_calibration'] = cal.reset_index(); T[f'econ_{nm}_roc'] = roc
    if E['syn']:
        T['econ_true_parameters'] = pd.DataFrame([dict(block=k, parameter=p, true_value=v) for k, d_ in DGP_TRUE.items() if k != 'sd'
                                                  for p, v in d_.items()] + [dict(block='share', parameter=p, true_value=v) for p, v in
                                                  zip(['rel_lp_l1', 'rel_leverage_l1'], BETA_TRUE)] +
                                                 [dict(block='sd', parameter=p, true_value=v) for p, v in DGP_TRUE['sd'].items()])
    return T
print('econ_tables / interpret_az defined (Azerbaijani interpretation per model)')

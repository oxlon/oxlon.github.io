# %%
ob = rd('oil_linked_block', index_col=0, dtype={'branch': str}); ps = rd('nonoil_allocation_selection', index_col=0); pe = rd('pooled_related_sector_model').iloc[0]
G['oil'] = (mdt(ob.reset_index()[['branch', 'name', 'n_products', 'corr_dlnQ_dlnThroughput', 'real_growth_2015_25', 'price_elasticity_oil', 'price_el_p',
                                  'cap_factor_baseline', 'cap_factor_max', 'precut_RMSE_capacity', 'precut_RMSE_sector_rate', 'precut_DM_p', 'capacity_rule_adopted']], dflt='{:.3f}')
            + f"\n\nCapacity rule adopted for: {', '.join(BNAME[b] for b in OIL) or 'none'}; " +
            (', '.join(f'{BNAME[b]} joins the non-oil allocation (the capacity rule is significantly less accurate pre-cut, p {ob.loc[b, "precut_DM_p"]:.3f})' for b in OIL_CAND if b not in OIL) or '') + '.')
G['pooled'] = (f"β = {pe.beta:.3f} (Driscoll–Kraay s.e. {pe.se:.3f}, p {pe.p_DK:.3f} on t({int(pe.years) - 1}); wild-bootstrap p {pe.p_wild:.3f}); "
               f"{int(pe.branches)} linked branches × {int(pe.years)} years; levels-with-FE estimate {pe.beta_levels:.3f}, "
               f"{'inside' if pe.levels_inside_fd_ci else 'outside'} the first-difference 95% CI [{pe.ci_lo:.2f}, {pe.ci_hi:.2f}].\n\n"
               + mdt(ps.reset_index(), dflt='{:.3f}')
               + f"\n\nBaseline allocation: **{'pooled related-sector model' if MAN_MODE == 'pooled' else 'equal-weight combination of the pooled model and constant shares'}** "
               f"(decision rule fixed in advance). On the pre-cut windows the pooled model is "
               f"{'more' if ps.loc['pooled', 'RMSE_pp'] < ps.loc['const', 'RMSE_pp'] else 'less'} accurate than constant shares "
               f"({ps.loc['pooled', 'RMSE_pp']:.3f} vs {ps.loc['const', 'RMSE_pp']:.3f} pp, DM p {ps.loc['pooled', 'DM_p_vs_const']:.3f}) and the combination "
               f"{ps.loc['combo', 'RMSE_pp']:.3f} pp (p {ps.loc['combo', 'DM_p_vs_const']:.3f}): the related-sector channel is an economically "
               "motivated, statistically significant in-sample elasticity whose out-of-sample allocation gain is not established.")
bg = rd('branch_growth_table', index_col=0, dtype={'nace2': str}); mu = rd('cross_sector_multipliers', index_col=0, dtype={'nace2': str}); nh = rd('nonoil_growth_vs_history').iloc[0]
mm = bg.loc[MANUF]
G['branches'] = (mdt(bg.reset_index()[['nace2', 'branch', 'model', 'nominal growth % pa', 'real growth % pa', f'share of industry {FC_YEARS[-1]} %', 'LP growth % pa']])
                 + f"\n\nManufacturing branches, baseline real growth 2026–2030: min {mm['real growth % pa'].min():+.2f}% ({mm.loc[mm['real growth % pa'].idxmin(), 'branch']}), "
                 f"max {mm['real growth % pa'].max():+.2f}% ({mm.loc[mm['real growth % pa'].idxmax(), 'branch']}). Implied non-oil manufacturing real growth "
                 f"{nh.forecast_2026_30:+.2f}% a year against {nh.avg_2010_19:+.2f}% (2010–19), {nh.avg_2021_25:+.2f}% (2021–25), best five-year {nh.best_5yr:+.2f}%"
                 + (' — FLAGGED' if isinstance(nh.flag, str) and nh.flag else ' — within history') + '.\n\nImplied cross-sector multipliers (% change in branch output per 1% in the related sector, sector total given):\n\n'
                 + mdt(mu.reset_index()[['nace2', 'branch', 'related_sector', 'multiplier', 'multiplier_p5', 'multiplier_p95']], dflt='{:.3f}'))
G['regions'] = (f"Selected: {REG_LABEL.get(LABEL[SELECT['R']['chosen']], LABEL[SELECT['R']['chosen']])}"
                + (f", κ = {SELECT['R']['kappa']:g}" if SELECT['R']['chosen'] != 'const' else '') +
                f". Baku's share of industrial output {REG_SH.loc[LAST_ACT, 'Baku city']*100:.1f}% in {LAST_ACT}; in {FC_YEARS[-1]}: "
                + ', '.join(f"{s_} {ss.loc[s_, f'Baku share {FC_YEARS[-1]} %']:.1f}%" for s_ in SCEN) + '.')
lv_ = rd('sensitivity_levers', index_col=0)
G['margin'] = (f"Baseline (labour share of VA held at its 2023–25 average): manufacturing GOS {SOL['Baseline']['sec_fin'].loc[('C', LAST_ACT), 'GOS_share_VA']:.1f}% of VA in "
               f"{LAST_ACT} and {lv_.loc['baseline', 'manufacturing GOS % VA 2030']:.1f}% in {FC_YEARS[-1]}. Sensitivities: FR1 wage path "
               f"{lv_.loc['margin: FR1 wage path', 'manufacturing GOS % VA 2030']:.1f}%; wages constant in product terms "
               f"{lv_.loc['margin: wages constant in product terms', 'manufacturing GOS % VA 2030']:.1f}%. Median branch GOS-proxy margin 2030: baseline "
               f"{lv_.loc['baseline', 'median branch GOS-proxy margin 2030']:.1f}%, FR1 wage path {lv_.loc['margin: FR1 wage path', 'median branch GOS-proxy margin 2030']:.1f}%.\n\n"
               + mdt(lv_.reset_index()))
nc = rd('nonstate_composition_summary').iloc[0]
G['ns'] = (f"Mining falls from {nc.mining_share_2025:.1f}% to {nc.mining_share_2030:.1f}% of industrial output (baseline); with within-branch non-state "
           f"shares held (mining {nc.ns_mining:.1f}%, refining {nc.ns_refining:.1f}%, electricity {nc.ns_electricity:.1f}%), the industry non-state share "
           f"moves from {nc.ns_2025:.1f}% to {nc.ns_2030:.1f}% — **pure composition, not an ownership forecast**.\n\n"
           + mdt(rd('nonstate_composition', index_col=0).reset_index()))
pf = rd('product_forecasts_derived'); pm_ = rd('product_location_shares', index_col=0)
G['products'] = (f"{len(pf)} products in {pf.branch.nunique()} branches receive **derived** volume paths (product mix held at 2023–25); "
                 f"{len(pm_)} products have producing places in {LAST_ACT} (median {pm_.places.median():.0f} places, median top-place share "
                 f"{pm_.top_place_share_pct.median():.0f}%). Most concentrated by place:\n\n"
                 + mdt(pm_.sort_values('HHI_places', ascending=False).head(8).reset_index()[['product', 'places', 'top_place', 'top_place_share_pct', 'HHI_places', 'coverage_of_national_pct']], dflt='{:.1f}'))
G['divb'] = mdt(rd('determinants_division_bias'), dflt='{:.3f}')
hf = rd('holdout_validation')
sel_ = hf[hf.selected & hf.system.str.contains('forecasting model')]
rr = sel_[(sel_.measure == 'real')].set_index('weighting')
sigw = lambda p: 'significantly' if p < 0.10 else 'not significantly'
_uu, _uw = rr.loc['unweighted', 'U_vs_constant_growth'], rr.loc['share-weighted', 'U_vs_constant_growth']
_bw = lambda u: 'better' if u < 1 else 'worse'
_vrd = ('beats constant growth' if max(_uu, _uw) < 1 else 'does not beat constant growth' if min(_uu, _uw) >= 1 else 'beats constant growth on one weighting only')
G['holdout_note'] = (f"Real branch output **{_vrd}**: U = {_uu:.3f} unweighted "
                     f"({sigw(rr.loc['unweighted', 'DM_p_vs_cg'])} {_bw(_uu)}, DM p {rr.loc['unweighted', 'DM_p_vs_cg']:.3f}) and "
                     f"{_uw:.3f} share-weighted ({sigw(rr.loc['share-weighted', 'DM_p_vs_cg'])} {_bw(_uw)}, DM p "
                     f"{rr.loc['share-weighted', 'DM_p_vs_cg']:.3f}); for the Part 11 constant-share system the figures were "
                     + ', '.join(f"{r.U_vs_constant_growth:.3f} (p {r.DM_p_vs_cg:.3f}, {r.weighting})" for _, r in hf[(hf.system.str.startswith('manufacturing (24 branches) (')) & (hf.measure == 'real') & (hf.model == 'constant shares')].iterrows())
                     + '. Real branch paths should be read with their bands; nominal output is the more reliable output.')
mr = rd('mining_rules_selection', index_col=0); mrec = rd('mining_reconciliation').iloc[0]
G['mining'] = (mdt(mr.reset_index(), dflt='{:.3f}')
               + f"\n\nQuarrying: **{mrec.rule08}** — the unit-elasticity link to FR1 construction VA against the neutral null: DM/HLN p = {mrec.unit08_dm_p:.3f} "
               f"(both rules anchored on the origin's last actual; pre-cut RMSE {T08.loc['unit elasticity to construction', 'RMSE_log_pct']:.1f} vs {T08.iloc[0].RMSE_log_pct:.1f} log-% for the null; "
               f"the link is adopted only if significantly MORE accurate, p < 0.10); the free elasticity {mrec.e08_est:.3f} (s.e. {mrec.e08_se:.3f}) rejects the unit restriction (p = {mrec.unit08_wald_p:.3f}). "
               f"{'The construction link is kept as the engine lever `quarrying_rule`. ' if mrec.rule08.startswith('neutral') else ''}Metal ores: {mrec.rule07}. "
               + ' '.join(f"{BNAME[b]}: {bg.loc[b, f'nominal {LAST_ACT}']:,.1f} → {bg.loc[b, f'nominal {FC_YEARS[-1]}']:,.1f} mn AZN nominal, real {bg.loc[b, 'real growth % pa']:+.2f}% a year."
                          for b in ['06', '07', '08', '09'])
               + f" Reconciliation: the four branches equal FR1's mining output to {mrec.max_gap_pct:.1e}% in every scenario and year (asserted); the "
               f"implied deflator of the oil part grows {mrec.implied_oil_deflator_growth_pa:+.2f}% a year against FR1's mining deflator {mrec.fr1_mining_deflator_growth_pa:+.2f}%.")

# %% [markdown]
# ### 16.1 Proqnozlaşdırılan erkən xəbərdarlıq göstəriciləri, 2025–2030, hər ssenari
#
# Erkən xəbərdarlıq göstəricisi yaxın keçmiş haqqında ifadədir. Ssenarinin sektoru nəzarət siyahısına salıb-salmayacağını
# göstərmək üçün **eyni qayda** (eyni z\*, çəkilər, pəncərələr) hər *t* = 2025…2030 ilində sektorun **t-yədək proqnoz
# trayektoriyası ilə uzadılmış** müşahidə olunan tarixinə tətbiq olunur: iri müəssisələrin buraxılış payı (Hissə 14), log
# yeni qeydiyyatlar və çıxış əmsalı (Hissə 13), marja trayektoriyası (Hissə 13 fərziyyəsi: 2025 səviyyəsində saxlanılır,
# sənaye FR10-dan). Payların mobilliyinin proqnozu yoxdur, buna görə onun siqnalı proqnozlaşdırılan kompozit göstəriciyə
# **daxil edilmir** (çəkilər mövcud siqnallar üzrə yenidən normallaşdırılır, Hissə 16-nın qaydası); 2024 göstəricisi
# (Hissə 16) onu saxlayır. Yalnız müşahidə olunan illər — heç bir interpolyasiya edilmiş dəyər göstəriciyə daxil olmur.

# %%
def ew_project(FCx, CONCx, pcm_fn, scen, years=None):
    '''Early-warning composite on history + forecast up to each year; FCx: forecast frame (unit, year, new, exit),
    CONCx: concentration paths (group, year, large_share); pcm_fn(g, scen, y) the margin path.'''
    years = years or [LAST_ACT] + FC_YEARS; out = []
    for g in GRP:
        e = PA[PA.unit == g].set_index('year'); ex = e.exit.copy(); ex.loc[2022] = np.nan
        f = FCx[FCx.unit == g].set_index('year'); c = CONCx[CONCx.group == g].set_index('year')
        for t in years:
            fy = [y for y in f.index if y <= t]; cy = [y for y in c.index if y <= t]
            ser = dict(conc=(pd.concat([100 - SME.loc[g].sme_output_share, c.large_share.loc[cy]]), 3),
                       entry=(pd.concat([e.lnB, np.log(f.new.loc[fy])]), 3), exit=(pd.concat([ex, f.exit.loc[fy]]), 2), mob=(pd.Series(dtype=float), 3),
                       margin=(pd.concat([PCM_G.PCM.xs(g, level=0).loc[2010:], pd.Series({y: pcm_fn(g, scen, y) for y in range(LAST_ACT + 1, t + 1)}, dtype=float)]), 3))
            z = {k: zchange(s.groupby(level=0).last(), r) for k, (s, r) in ser.items()}
            fl = flags_from_z(z, Z_STAR); sc_, nf, ls = listed(fl)
            out.append(dict(scenario=scen, group=g, year=t, **{f'z_{k}': v for k, v in z.items()}, **fl, n_available=sum(isinstance(v, bool) for v in fl.values()),
                            n_flags=nf, score=sc_, watch_list=ls))
    return pd.DataFrame(out)
EW_PROJ = pd.concat([ew_project(FC[(FC.scenario == sc) & (FC.panel == 'activity')], CONCP[CONCP.scenario == sc], pcm_path, sc) for sc in SCEN], ignore_index=True)
EW_PROJ.to_csv(OUT / 'FR12_early_warning_projected.csv', index=False)
display(EW_PROJ.pivot_table(index='group', columns=['scenario', 'year'], values='score').loc[:, (slice(None), [2025, 2028, 2030])].round(2))
print('projected watch list 2030: ' + '; '.join(f"{sc}: {', '.join(EW_PROJ[(EW_PROJ.scenario == sc) & (EW_PROJ.year == 2030) & EW_PROJ.watch_list].group) or 'none'}" for sc in SCEN))

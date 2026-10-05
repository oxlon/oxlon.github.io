# %% [markdown]
# ## Hissə 7 — Aqreqat məlumatlardan rəqabət göstəriciləri (A qatı)
#
# | Göstərici | Düstur | Məcmu |
# |---|---|---|
# | giriş əmsalı | t ilində yeni vahidlər / t ilinin sonunda vahidlər × 100 (DSK qaydası) | qeydiyyatdan keçmiş subyektlər (006), statistik vahidlər (2_1, regionlar) |
# | çıxış əmsalı | t ilində ləğv edilmiş (qeydiyyatdan çıxarılmış) / t ilinin sonunda vahidlər × 100 | yuxarıdakı kimi |
# | dövriyyə (churn), xalis giriş | giriş + çıxış; giriş − çıxış | yuxarıdakı kimi |
# | kohort ölçüsü nisbəti (sağ qalma əmsalı deyil) | eyni ildə k yaşlı fəal KOB-lar / 1 yaşlı fəal KOB-lar, k = 2…5 — kohortun ölçüsünü və sağ qalmanı qarışdırır | KOB-lar (024–028) |
# | KOB / iri müəssisələrin payları | buraxılışda və işçilərdə KOB-ların payı; iri = 100 − KOB | KOB-lar (012, 013) |
# | qiymət-xərc marjası proksisi | (əlavə dəyər − əməyin ödənilməsi) / buraxılış × 100 | NACE bölmələri (milli hesablar 013) |
# | payların qeyri-sabitliyi | emal sənayesi sahələri üzrə ½ Σ\|s_i,t − s_i,t−1\| (Hymer–Pashigian) | FR10-un sahə payları |
# | regional dispersiya | regional giriş əmsallarının variasiya əmsalı; vahidlərin regionlar üzrə HHI-si | 14 region |
# | lisenziyalar, yoxlamalar | verilmiş lisenziyalar (giriş göstəricisi); yoxlamalar (əhatə dairəsi dəyişir, F18) — yalnız məlumat üçün | iş kitabı |
#
# Dövlət idarəetməsi (O) və ərazidənkənar təşkilatlar (U) bazar xarakterli deyil və xaric edilir (F10).

# %%
MKT = [s for s in SECS if s not in ('O', 'U')]
G = E006.drop('TOT', level=0).copy()
G['entry'] = G.new / G.registered * 100; G['exit'] = G.dereg / G.registered * 100
G['churn'] = G.entry + G.exit; G['net'] = G.entry - G.exit
IND_G = G[['registered', 'new', 'dereg', 'entry', 'exit', 'churn', 'net']].reset_index()
S_ = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'FY') & FLOWS.unit.isin(MKT)].copy()
S_['entry'] = S_.new / S_.stock * 100; S_['exit'] = S_.liq / S_.stock * 100; S_['churn'] = S_.entry + S_.exit; S_['net'] = S_.entry - S_.exit
IND_S = S_.rename(columns={'unit': 'sec'})[['sec', 'year', 'stock', 'new', 'liq', 'entry', 'exit', 'churn', 'net']]
RG['entry'] = RG.new / RG.enterprises * 100; RG['exit'] = RG.liquidated / RG.enterprises * 100
RG['churn'] = RG.entry + RG.exit; RG['net'] = RG.entry - RG.exit
REGDISP = RG.groupby('year').agg(cv_entry=('entry', lambda x: x.std() / x.mean()), cv_exit=('exit', lambda x: x.std() / x.mean()),
                                 hhi_units=('enterprises', lambda x: ((x / x.sum()) ** 2).sum() * 1e4))
SURV = (AGE.div(AGE[1], axis=0))[[2, 3, 4, 5]].rename(columns=lambda k: f'S{k}')
SURV = SURV.drop('TOT', level=0, errors='ignore')
SME = pd.concat({'sme_output_share': E012['sme'], 'sme_employment_share': E013['sme']}, axis=1).drop('TOT', level=0, errors='ignore')
SME['large_output_share'] = 100 - SME.sme_output_share
NAG = NA.reset_index(); NAG['group'] = NAG.sec.map(lambda s: SECT[s][3])
PCM_G = NAG[NAG.sec.isin(MKT)].groupby(['group', 'year'])[['GO', 'VA', 'CE']].sum()
PCM_G['PCM'] = (PCM_G.VA - PCM_G.CE) / PCM_G.GO * 100
_sh = FR10_SH[FR10_SH.series == FR10_SH.series.unique()[0]].pivot_table(index='year', columns='unit', values='value')
_mf = [c for c in _sh.columns if str(c).zfill(2) >= '10' and str(c).zfill(2) <= '33']
_m = _sh[_mf].div(_sh[_mf].sum(axis=1), axis=0)
INSTAB = (0.5 * _m.diff().abs().sum(axis=1)).loc[2006:LAST_ACT].rename('instability_manuf_branches')
_units = pd.Series({y: RG[RG.year == y].enterprises.sum() for y in RG.year.unique()})
BARR = pd.DataFrame({'licences_new': LIC_NEW, 'inspections': INSP.sum()}).loc[2015:LAST_ACT]
BARR['licences_per_1000_units'] = BARR.licences_new / _units * 1000; BARR['inspections_per_1000_units'] = BARR.inspections / _units * 1000
print('entry / exit by activity group (registered entrepreneurship subjects, % of end-year stock):')
display(G[['entry', 'exit']].unstack(1).round(2))
print('register (statistical units) by NACE section, full years:')
display(IND_S.pivot_table(index='sec', columns='year', values=['entry', 'exit']).round(2))
print(f'regions: entry {RG.entry.min():.1f}-{RG.entry.max():.1f}%, exit {RG.exit.min():.2f}-{RG.exit.max():.2f}%; '
      f'CV of regional entry rates {REGDISP.cv_entry.iloc[0]:.2f} (2021) -> {REGDISP.cv_entry.iloc[-1]:.2f} (2025)')
print(f'branch-share instability (manufacturing): mean {INSTAB.loc[2006:2015].mean()*100:.1f} pp (2006-15), {INSTAB.loc[2016:].mean()*100:.1f} pp (2016-25)')


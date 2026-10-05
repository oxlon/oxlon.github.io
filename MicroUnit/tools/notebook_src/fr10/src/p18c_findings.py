# %% [markdown]
# ### 18.3 Nə aşkar edildi

# %%
b_ = SOL['Baseline']; g_ = gk
print('=' * 100); print('FR10 — WHAT WAS FOUND'.center(100)); print('=' * 100)
print(f'1 DATA. {int(MANIFEST.status.isin(["present", "downloaded"]).sum())} DSK tables collected; {len(UNPUBLISHED)} no longer published (F1). '
      f'Branch output adds up to the industry total to {pd.DataFrame(REC).max_gap_pct.iloc[:3].max():.3f}%. {len(FINDINGS)} integrity findings.')
print(f'2 INDICATOR SYSTEM. {len(SRC_MATRIX)} indicators: ' + ', '.join(f'{k} {v}' for k, v in SRC_MATRIX.status_group.value_counts().items()) +
      f'; {len(GAPS)} gaps with alternatives; {len(PRES)} user views.')
print(f'3 MARKET POSITION {LAST_ACT}. Manufacturing HHI {CONC.loc[LAST_ACT, "HHI manufacturing branches"]:.0f} (2005: {CONC.loc[2005, "HHI manufacturing branches"]:.0f}); '
      f'refining {SH_MAN.loc[LAST_ACT, "19"]*100:.1f}% and food {SH_MAN.loc[LAST_ACT, "10"]*100:.1f}% of manufacturing; non-state share of industry '
      f'{NS.loc[LAST_ACT, "ALL"]*100:.1f}%; Baku {REG_SH.loc[LAST_ACT, "Baku city"]*100:.1f}% of industrial output.')
print(f'4 EFFICIENCY. Section TFP 2007-{LAST_ACT}, % a year: ' + ', '.join(f'{s_} {v:+.2f}' for s_, v in SEC_TFP.TFP.groupby(level=0).mean().mul(100).items()))
print(f'5 FINANCIAL CONDITION {LAST_ACT}. GOS % of VA: ' + ', '.join(f'{SECT[s_]} {INC.loc[(s_, LAST_ACT), "GOS"]/INC.loc[(s_, LAST_ACT), "VA"]*100:.1f}' for s_ in SECV)
      + f'; DVX declaration net margin {true_marg.loc[LAST_ACT]:.1f}%; branch GOS-proxy median {GOSP.loc[LAST_ACT].median():.1f}%.')
print(f'6 BRANCH MODEL. Refining by capacity and oil price; non-oil branches: {"pooled" if MAN_MODE == "pooled" else "combination of pooled related-sector model and constant shares"} '
      f'(beta {BETA:.3f}); benchmark share systems (windows <= {SEL_END}): manufacturing {LABEL[SELECT["C"]["chosen"]]}, mining {LABEL[SELECT["B"]["chosen"]]}, '
      f'regions {REG_LABEL.get(LABEL[SELECT["R"]["chosen"]], LABEL[SELECT["R"]["chosen"]])}' + (f' (kappa {SELECT["R"]["kappa"]:g})' if SELECT['R']['chosen'] != 'const' else '') + '.')
hs = HOLD[HOLD.selected & (HOLD.weighting == 'unweighted')].set_index(['system', 'measure'])
r_ = hs.loc[('manufacturing (24 branches): forecasting model', 'nominal')]
print(f'7 HOLD-OUT 2020-{LAST_ACT}. Manufacturing branch nominal output: U = {r_.U_vs_random_walk:.2f} vs random walk, {r_.U_vs_constant_growth:.2f} vs constant growth.')
print(f'8 FORECAST {FC_YEARS[0]}-{FC_YEARS[-1]} (baseline). Industry nominal output {SCEN_SUM.loc["Baseline", "industry nominal output growth % pa"]:+.2f}% a year, '
      f'manufacturing {SCEN_SUM.loc["Baseline", "manufacturing nominal growth % pa"]:+.2f}% nominal / {SCEN_SUM.loc["Baseline", "manufacturing real growth % pa (FR1 rva_man)"]:+.2f}% real; '
      f'90% band of manufacturing output growth {FAN.loc[("section output, mn AZN", "Manufacturing", g_), "p5"]:+.1f}% to {FAN.loc[("section output, mn AZN", "Manufacturing", g_), "p95"]:+.1f}%.')
print(f'9 PLAUSIBILITY. {nflag} of {len(PLAUS)} units flagged; watch list {int(EW.watch_list.sum())} branches.')
print(f'10 LAYER B. DATA_MODE = {DATA_MODE} ({PANEL_META["file"]}, {PANEL_META["rows"]:,} rows); {len(PIPE)} pipeline tests and {len(SWAP)} swap tests pass'
      + ('; SYNTHETIC: a pipeline demonstration, not findings - the Ministry replaces the file in its own system.' if DATA_MODE == 'SYNTHETIC' else '.'))

# %% [markdown]
# ### 18.4 Məhdudiyyətlər
#
# 1. **Əlaqəli sektor elastikliyi nümunədaxili əhəmiyyətlidir, lakin onun sabit paylarla müqayisədə nümunədən kənar
#    bölüşdürmə üstünlüyü təsdiqlənməyib** (§11.5); Əsas ssenarinin kombinasiyası əvvəlcədən müəyyən edilmiş qaydaya
#    əsaslanır.
# 2. **Sahələrin real buraxılışı** bir neçə kiçik sahə üçün nominal buraxılışla uyğun gəlməyən DSK həcm indekslərinə
#    (F15; v2.1 testdən keçməyən indeksləri əvəz edir, Hissə 5.1) və implisit deflyatorlara əsaslanır; onun nümunədən
#    kənar yoxlama nəticəsi Hissə 13-dədir. Nominal buraxılış daha etibarlı nəticə olaraq qalır.
# 3. **Neft emalı** üzrə yeni güc fərz edilmir; maksimum emal həcmi rıçağı alternativi göstərir.
# 4. **Maliyyə vəziyyəti aqreqat səviyyədədir**: bölmələrin ÜƏM-i (milli hesablar), sahələr üzrə ÜƏM proksisi (yuxarı
#    hədd) və bütün iqtisadiyyat üzrə vergi bəyannamələri. Likvidlik, borc yükü və maliyyə çətinliyi üçün B qatının
#    məlumatları lazımdır.
# 5. **Səmərəlilik** göstəriciləri implisit deflyatorlara və fasiləsiz inventar üsulu ilə hesablanmış kapital ehtiyatına
#    əsaslanır; kiçik sahələrin TFP-si küylüdür və əmək + material payları birdən böyük olan sahə-illər işarələnir.
# 6. **Amillər paneli** 14 (7) illik müşahidənin gücünə malikdir; təsirlərin əksəriyyəti təsdiqlənməyib.
# 7. **İxrac, sahələr üzrə istehsalçı qiymətləri indeksləri (PPI), enerji xərcləri, sahələr üzrə kredit, yenilənmə
#    dərəcələri** mövcud deyil (boşluqlar cədvəli).
# 8. **B qatı** təhlil deyil, sınaqdan keçirilmiş emal xəttidir: heç bir müəssisə məlumatı alınmayıb.

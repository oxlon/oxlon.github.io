# %% [markdown]
# ## Hissə 16 — Tarixi məlumatlarla müqayisədə inandırıcılıq və erkən xəbərdarlıq siqnalları
#
# ### 16.1 Hər proqnoz artım sürəti vahidin öz tarixi ilə müqayisədə
#
# Hər sahə, bölmə və sənaye yekunu üçün 2026–2030 üzrə Əsas ssenarinin orta real artımı vahidin öz 2010–2019 və 2021–2025
# ortaları, habelə 2005-ci ildən bəri ən yaxşı və ən pis beşillik ortaları ilə müqayisə edilir. Ən yaxşı beşillik
# ortadan yuxarı (ən pisdən aşağı) proqnoz kök səbəbi ilə birlikdə **işarələnir**. İlk məlumat buraxılışında (vintage)
# neft emalı işarələnmişdi (sabit paylar üzrə bölüşdürmə FR1-in emal sənayesi artım sürətini gücü məhdud neft emalı
# zavoduna ötürürdü); kök səbəb §11.2-nin güc modeli ilə aradan qaldırılıb. Cədvəldə həmçinin hər sahənin öz 2010–2019
# artım sürətinin Hissə 15-in 90% zolağının daxilində olub-olmadığı göstərilir.

# %%
def win5(s):
    s = s.dropna(); v = [((s.loc[y] / s.loc[y - 5]) ** 0.2 - 1) * 100 for y in s.index if y - 5 in s.index and y - 5 >= 2005]
    return (max(v), min(v)) if v else (np.nan, np.nan)
def avg_g(s, a, b): return ((s.loc[b] / s.loc[a]) ** (1 / (b - a)) - 1) * 100
PL = []
units = [(b, BNAME[b], Q[b], B_['real'][b], ('branch real output, mn AZN 2015 prices', b)) for b in BCODES]
units += [(s_, SECT[s_], F1H[f'rva_{v}'], pd.Series(scen_arrays('Baseline')[f'rva_{v}'][0], index=YRS), None) for s_, v in SECV.items()]
for code, nm, hist, fc, fk in units:
    best, worst = win5(hist.loc[2005:LAST_ACT])
    g = cagr(fc)
    row = dict(code=code, unit=nm, forecast_real_growth=g, hist_2010_2019=avg_g(hist, 2010, 2019),
               hist_2021_2025=avg_g(hist, 2020, LAST_ACT), best_5yr=best, worst_5yr=worst,
               flag=('ABOVE best 5-yr' if g > best else 'BELOW worst 5-yr' if g < worst else ''))
    if fk is not None:
        f = FAN.loc[fk + (gk,)]
        row.update(band_p5=f.p5, band_p95=f.p95, hist_2010_19_inside_90band=bool(f.p5 <= row['hist_2010_2019'] <= f.p95))
    PL.append(row)
PLAUS = pd.DataFrame(PL).set_index('code')
display(PLAUS.round(2))
nflag = int((PLAUS.flag != '').sum())
print(f'{nflag} of {len(PLAUS)} units flagged against their own five-year history: ' +
      ', '.join(f'{r.unit} ({r.forecast_real_growth:+.1f}% vs best {r.best_5yr:+.1f}%)' for _, r in PLAUS[PLAUS.flag != ''].iterrows()))
cov = PLAUS.dropna(subset=['band_p5'])
print(f'own 2010-2019 real growth inside the 90% band for {int(cov.hist_2010_19_inside_90band.sum())} of {len(cov)} branches')
print(f'implied non-oil manufacturing real growth {NONOIL_HIST["forecast_2026_30"]:+.2f}% a year vs best five-year {NONOIL_HIST["best_5yr"]:+.2f}% '
      f'-> {NONOIL_HIST["flag"] or "within history"}. Any remaining branch flag stems from FR1\'s sector path passed through the allocation;')
print('flags are published with the branch\'s own history, not hidden.')


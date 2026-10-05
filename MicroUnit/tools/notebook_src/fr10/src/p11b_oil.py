# %% [markdown]
# ### 11.4 Neftlə bağlı sahələr: gücü məhdud emalçılar kimi neft emalı və kimya
#
# Sabit paylar neft emalına (emal sənayesi buraxılışının dörddə biri) FR1-in emal sənayesi üzrə real artımını verərdi —
# bu, onun yeganə neft emalı zavodunun indiyədək təmin etdiyi hər şeydən xeyli yüksəkdir (Hissə 16 bunu işarələdi). Əsas
# səbəb ondadır ki, neft emalının buraxılışı **emal gücü (ötürmə qabiliyyəti)** ilə, dəyəri isə **neft qiyməti** ilə
# müəyyən olunur. Buna görə hər iki sahə pay sistemindən kənarda modelləşdirilir:
#
# - **Real buraxılış = emal həcmi.** Emal həcminin proksisi DSK `018` cədvəlində sahənin yuxarı səviyyəli məhsullarının
#   tonajıdır (neft emalı: benzin, yüngül distillatlar, kerosin, mazut, dizel yanacağı, sürtkü yağları, koks və bitum
#   qalıqları; kimya: polimerlər, üzvi kimyəvi maddələr, karbamid və min ton / ton ilə verilən digər məhsullar). Əsas
#   ssenari: real buraxılış **2023–2025-ci illərin orta emal həcmində** saxlanılır (güc məhdudiyyəti); rıçaq: emal həcmi
#   2015–2025-ci illərin maksimumunda.
# - **Qiymət = FR1-in manatla neft ixrac qiyməti** (FR1-in proqnozunda məzənnə sütunu yoxdur, buna görə 2025-ci il
#   məzənnəsi saxlanılır), elastiklik 2006–2025 üzrə birinci fərqlərdə qiymətləndirilir (proqnoza sabit hədd ötürülmür).
#
# **Kəsimdən əvvəlki test.** Hər namizəd üçün güc qaydası sektorla birgə artım alternativinə (FR1-in emal sənayesi üzrə
# real ƏD-si) qarşı eyni sürüşən başlanğıclarda (2011–2017, bütün qiymətləndirmələr ≤ 2019, DM/HLN) müqayisə edilir. O,
# yalnız əhəmiyyətli dərəcədə daha dəqiq olduqda (p < 0,10) qəbul edilir; əks halda sahə qeyri-neft bölüşdürməsinə
# qoşulur (§11.5). FR1-in emal sənayesi buraxılışının qalan hissəsi qeyri-neft sahələri arasında bölüşdürülür və nəzərdə
# tutulan qeyri-neft artımı Hissə 16-da tarixi məlumatlarla müqayisədə yoxlanılır.

# %%
OIL_CAND = ['19', '20']
yc18 = [c for c in PROD.columns if isinstance(c, (int, np.integer))]
def throughput(b):
    p = PROD[(PROD.branch == b) & PROD.label.str.match(r'^[A-Z]')].set_index('label')[yc18].astype(float)
    f = np.where(p.index.str.contains(r'thsd\. ?tonnes'), 1.0, np.where(p.index.str.contains(r'\bton\b'), 1e-3, np.nan))
    p = p[np.isfinite(f)].mul(f[np.isfinite(f)], axis=0)
    return p.sum(min_count=1), list(p.index)
THR, THR_ITEMS = {}, {}
for b in OIL_CAND:
    THR[b], THR_ITEMS[b] = throughput(b)
OILAZN = F1H.oil_exp_price * F1H.fx
OILB = []
for b in OIL_CAND:
    t = THR[b]
    dq = pd.DataFrame({'dQ': np.log(Q[b]).diff(), 'dT': np.log(t).diff()}).loc[2006:LAST_ACT].dropna()
    fp = ols(np.log(PDEF[b]).diff().loc[2006:LAST_ACT], np.log(OILAZN).diff().loc[2006:LAST_ACT].rename('dln_oil_azn').to_frame())
    cap_base = float(t.loc[LAST_ACT - 2:LAST_ACT].mean() / t.loc[LAST_ACT])
    cap_max = float(t.loc[2015:LAST_ACT].max() / t.loc[LAST_ACT])
    OILB.append(dict(branch=b, name=BNAME[b], n_products=len(THR_ITEMS[b]), throughput_2025_thsd_t=float(t.loc[LAST_ACT]),
                     corr_dlnQ_dlnThroughput=float(dq.corr().iloc[0, 1]), real_growth_2015_25=((Q[b].loc[LAST_ACT] / Q[b].loc[2015]) ** 0.1 - 1) * 100,
                     price_elasticity_oil=float(fp.beta[1]), price_el_se=float(fp.se[1]), price_el_p=float(fp.pval[1]),
                     cap_factor_baseline=cap_base, cap_factor_max=cap_max))
    ek, ec = [], []
    for o in SEL_ORIGINS:
        cf = float(t.loc[o - 2:o].mean() / t.loc[o])
        for y in range(o + 1, SEL_END + 1):
            ek.append(np.log(Q.loc[o, b] * cf / Q.loc[y, b]) * 100)
            ec.append(np.log(Q.loc[o, b] * F1H.rva_man.loc[y] / F1H.rva_man.loc[o] / Q.loc[y, b]) * 100)
    dms, dmp = dm_hln(np.square(ek), np.square(ec), h=2)
    OILB[-1].update(precut_RMSE_capacity=float(np.sqrt(np.mean(np.square(ek)))), precut_RMSE_sector_rate=float(np.sqrt(np.mean(np.square(ec)))),
                    precut_DM_stat=dms, precut_DM_p=dmp, capacity_rule_adopted=bool(dms < 0 and dmp < 0.10))
OILB = pd.DataFrame(OILB).set_index('branch')
OIL = [b for b in OIL_CAND if OILB.loc[b, 'capacity_rule_adopted']]
NONOIL = [b for b in MANUF if b not in OIL]
for b in OIL_CAND:
    if b not in OIL:
        reject(f'capacity rule for {BNAME[b]}', 'oil-linked block', 'REJECTED pre-cut',
               f'RMSE {OILB.loc[b, "precut_RMSE_capacity"]:.1f} vs {OILB.loc[b, "precut_RMSE_sector_rate"]:.1f} log-% for the sector rate, DM p {OILB.loc[b, "precut_DM_p"]:.3f}')
display(OILB.round(3))
EPS_OIL = OILB.price_elasticity_oil.to_dict(); CAPF = OILB.cap_factor_baseline.to_dict(); CAPMAX = OILB.cap_factor_max.to_dict()
print('throughput items: ' + '; '.join(f'{BNAME[b]}: {len(v)} products' for b, v in THR_ITEMS.items()))
print(f'capacity rule adopted (pre-cut test) for: {[BNAME[b] for b in OIL]}; joins the non-oil allocation: {[BNAME[b] for b in OIL_CAND if b not in OIL]}')
print(f'Baseline real output of the oil-linked branches = 2025 x (2023-25 average throughput / 2025 throughput): '
      + ', '.join(f'{BNAME[b]} {CAPF[b]:.3f}' for b in OIL) + '; capacity lever (2015-25 maximum): '
      + ', '.join(f'{BNAME[b]} {CAPMAX[b]:.3f}' for b in OIL))

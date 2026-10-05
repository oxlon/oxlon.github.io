# %% [markdown]
# ### 16.2 Erkən xəbərdarlıq siqnalları, emal sənayesi sahələri
#
# Hər göstərici **2023–2025 ortasını** **2020–2022 ortası** ilə müqayisə edir (2020 və ya 2022 kimi tək baza illəri tsiklin
# ekstremal nöqtələridir) və dəyişiklik sahənin **öz dəyişkənliyi** ilə (2016-cı ildən bəri illik dəyişikliklərinin
# standart kənarlaşması) miqyaslanır: dəyişiklik öz standart kənarlaşmasının birindən pis olduqda siqnal verilir.
#
# | Siqnal | Qayda |
# |---|---|
# | Mənfi marja | 2025-ci ildə və ya 2023–25 ortasında ÜƏM proksisi marjası < 0 → **avtomatik nəzarət** |
# | Azalan marja | marjanın dəyişməsi < −1 öz s.k. |
# | Bazar mövqeyinin itirilməsi | emal sənayesindəki payın loqarifmik dəyişməsi < −1 öz s.k. |
# | Aşağı yenilənmə | 2023–25 investisiya norması öz 2010–2022 ortasından 1 s.k.-dan çox aşağı; məlumat olmadıqda **məlumat kifayət deyil** (heç vaxt sıfırla doldurulmur) |
# | Artan ehtiyatlar | 2023–25 ehtiyatlar/buraxılış öz 2010–2022 ortasından 1 s.k.-dan çox yuxarı |
# | Azalan məhsuldarlıq | bir işçiyə düşən real buraxılışın loqarifmik dəyişməsi < −1 öz s.k. |
#
# Emal sənayesi buraxılışının 0,5%-dən az payı olan sahələr yalnız iki siqnal olduqda göstərilir (kiçik ədədlərin küyü);
# mənfi marja istənilən sahəni nəzarət siyahısına salır. İki və ya daha çox siqnal (ölçü imkan verdikdə) və ya mənfi
# marja = nəzarət siyahısı. Bunlar qiymətləndirilmiş ehtimallar deyil, şəffaf idarəetmə paneli hədləridir; B qatı
# onları müəssisə səviyyəli maliyyə çətinliyi göstəriciləri ilə əvəz edir.

# %%
def a3(df, a, b): return df.loc[a:b].mean()
def z_change(df, log=False):
    x = np.log(df) if log else df
    ch = a3(x, LAST_ACT - 2, LAST_ACT) - a3(x, LAST_ACT - 5, LAST_ACT - 3)
    sd = x.diff().loc[2016:LAST_ACT].std()
    return ch, ch / sd
EW = pd.DataFrame(index=MANUF); EW['branch'] = [BNAME[b] for b in MANUF]
EW['share_2025_pct'] = SH_MAN.loc[LAST_ACT, MANUF] * 100
EW['margin_2023_25'] = a3(GOSP[MANUF], LAST_ACT - 2, LAST_ACT)
EW['margin_change'], EW['margin_z'] = z_change(GOSP[MANUF])
EW['share_logchange'], EW['share_z'] = z_change(SH_MAN[MANUF], log=True)
EW['lp_logchange'], EW['lp_z'] = z_change(LP_GO[MANUF], log=True)
ir = INV_RATE[MANUF]; ir_now = ir.loc[LAST_ACT - 2:LAST_ACT].mean(skipna=False)
EW['inv_rate_2023_25'] = ir_now; EW['inv_rate_z'] = (ir_now - ir.loc[2010:LAST_ACT - 3].mean()) / ir.loc[2010:LAST_ACT - 3].std()
sr = STK_RATIO[MANUF]; EW['stocks_ratio_2023_25'] = sr.loc[LAST_ACT - 2:LAST_ACT].mean(skipna=False)
EW['stocks_z'] = (EW.stocks_ratio_2023_25 - sr.loc[2010:LAST_ACT - 3].mean()) / sr.loc[2010:LAST_ACT - 3].std()
EW['margin_2025'] = GOSP.loc[LAST_ACT, MANUF]
EW['F_negative_margin'] = (EW.margin_2023_25 < 0) | (EW.margin_2025 < 0)
EW['F_margin'] = EW.margin_z < -1; EW['F_share'] = EW.share_z < -1; EW['F_productivity'] = EW.lp_z < -1
EW['F_renewal'] = np.where(EW.inv_rate_z.isna(), 'insufficient data', np.where(EW.inv_rate_z < -1, 'FLAG', ''))
EW['F_stocks'] = np.where(EW.stocks_z.isna(), 'insufficient data', np.where(EW.stocks_z > 1, 'FLAG', ''))
EW['n_flags'] = EW[['F_margin', 'F_share', 'F_productivity']].sum(axis=1) + (EW.F_renewal == 'FLAG') + (EW.F_stocks == 'FLAG')
EW['size_ok'] = EW.share_2025_pct >= 0.5
EW['watch_list'] = (EW.size_ok & (EW.n_flags >= 2)) | EW.F_negative_margin
display(EW.sort_values('n_flags', ascending=False).round(2))
print(f'watch list ({int(EW.watch_list.sum())} branches): ' + (', '.join(f'{r.branch} ({int(r.n_flags)} flags' + (', negative margin' if r.F_negative_margin else '') + ')'
      for _, r in EW[EW.watch_list].sort_values('n_flags', ascending=False).iterrows()) or 'none')
      + f'; below the size threshold: {int((~EW.size_ok).sum())} branches; insufficient investment data: {int((EW.F_renewal == "insufficient data").sum())}')

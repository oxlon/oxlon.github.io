# %% [markdown]
# ## Hissə 9 — Nə qiymətləndirilir, nə qadağandır və nə rədd edilib
#
# ### 9.1 Avtoreqressiyanın qadağan olunması məhdudiyyəti — dəqiq ifadəsi
#
# FR10-da heç bir tənlikdə gecikmiş asılı dəyişən, sürüşən orta xəta və ya şərti dispersiya prosesi yoxdur və heç bir
# dəyişən öz tarixi əsasında proqnozlaşdırılmır. Notebook-da rast gəlinən gecikmə konstruksiyaları:
#
# | Konstruksiya | Harada | Nə üçün avtoreqressiya deyil |
# |---|---|---|
# | Newey–West HAC kovariasiyası (n/(n−k) miqyaslaması), Driscoll–Kraay kovariasiyası | hər zaman sırası və panel tənliyində | Yalnız standart xətalar |
# | **İzahedici dəyişənlərin** fərqlərinin DOLS qabaqlayıcı/gecikmələri | səviyyə pay tənlikləri (Hissə 11–12) | Stock–Watson endogenlik düzəlişi; asılı dəyişənin öz gecikmələri heç vaxt daxil olmur |
# | Bir sabit gecikmə ilə qalıq ADF testi | `eg_coint_p` | Qalıqlar üzrə test statistikası |
# | Zəncirvari həcm səviyyələri $Q_t = Q_{t-1} I_t/100$ | Hissə 5 | Dərc olunmuş səviyyə ilə dərc olunmuş indeks arasında rəsmi zəncirvari əlaqələndirmə eyniliyi |
# | Fasiləsiz inventar $K_t = (1-\delta)K_{t-1} + I_t$ | Hissə 7.2 | Müşahidə olunan axınlardan qurulan ehtiyat üçün uçot eyniliyi |
# | **Digər** dəyişənlərin birillik gecikmələri (investisiya norması, nisbi qiymət, mülkiyyət, ehtiyatlar) | amillər paneli, Hissə 10 | Əvvəlcədən müəyyən olunmuş izahedici dəyişənlər; sahə buraxılışının artımı heç vaxt sağ tərəfdə yer almır |
# | Sabit düzəliş əmsalı (sonuncu faktiki ilin öz qalığı) | Hissə 11–14 | 2025-ci ili lövbərləyən sabit səviyyə düzəlişi; proqnoz dövrü boyu sabit saxlanılır — FR10-da sönmə tətbiq olunmur |
# | Tarixi qalıq trayektoriyaları $e_h = u_{s+h} - u_s$ | yelpik qrafikləri, Hissə 15 | Müşahidə olunmuş xəta trayektoriyalarını təkrarlayır; qiymətləndirilmiş dinamika yoxdur |
# | "Sonuncu faktiki dəyərdə saxlanılan" proqnoz qaydaları (nisbi qiymətlər, sahədaxili mülkiyyət payları, KOB payları, Aİ/buraxılış nisbətləri) | Hissə 14 | Qiymətləndirmə deyil, açıq göstərilmiş ssenari fərziyyəsidir; hər biri fərziyyələr cədvəlində sadalanır |
#
# FR10-da sahələr üzrə ilin bir hissəsini əhatə edən məlumat yoxdur, buna görə düzəlişlər müqaviləsindəki cari
# qiymətləndirmə (nowcast) düzəliş əmsalı qaydası burada yaranmır.

# %%
REJ = []
def reject(spec, block, verdict, evidence):
    REJ.append(dict(specification=spec, block=block, verdict=verdict, evidence=evidence))
NOAR = pd.DataFrame([
    ('HAC / Driscoll-Kraay covariance', 'all equations', 'standard errors only'),
    ('DOLS leads/lags of regressor differences', 'share systems', 'endogeneity correction; no own lag'),
    ('residual ADF, one fixed lag', 'eg_coint_p', 'test statistic'),
    ('chained volume levels', 'Part 5', 'chain-linking identity'),
    ('perpetual inventory capital', 'Part 7.2', 'stock-flow identity'),
    ('one-year lags of other regressors', 'determinants panel', 'predetermined regressors; dependent variable never lagged'),
    ('constant add-factor (2025 anchor; no decay)', 'share systems', 'level anchor held constant over the horizon; FR10 applies no decay'),
    ('historical residual paths', 'fan charts', 'replay of observed error paths'),
    ('held-at-last-value forecast rules', 'Part 14', 'scenario assumptions, listed')], columns=['construct', 'where', 'why not autoregressive'])
display(NOAR)

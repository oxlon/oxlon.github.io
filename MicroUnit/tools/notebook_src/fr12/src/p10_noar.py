# %% [markdown]
# ## Hissə 10 — Avtoreqressiyanın qadağan olunması məhdudiyyəti
#
# FR12 heç bir dəyişəni öz keçmişi əsasında proqnozlaşdırmır. Zaman gecikməsi və ya əvvəlki dəyər daxil olan hər
# konstruksiya burada onun nə üçün avtoreqressiya olmadığının səbəbi ilə birlikdə sadalanır
# (`output/FR12_noar_constructs.csv`).

# %%
NOAR = pd.DataFrame([
 ('Stock of active units N(t)', 'N(t) = (N(t−1) + births(t)) / (1 + exit rate(t)), i.e. N(t) = N(t−1) + B(t) − D(t) with D on the end-year stock',
  'accounting identity (like FR1\'s capital stock): births and the exit rate are forecast structurally, the stock is their sum', 'identity'),
 ('Entry rate', 'births(t) / N(t)', 'derived from the births forecast and the identity stock; never modelled on its own past', 'identity'),
 ('Anchoring on the last residual (add-factor)', 'forecast = model + (y_last − fitted_last); implied weight on the last observation 1 (0.5 in a combination)',
  'the FR1–FR10 add-factor convention: the last residual is held constant, no dynamics are estimated; the implied random-walk weight of every rule is reported in Part 12', 'model'),
 ('Definition break and impulses', 'brk = 1 from 2022 (006 definition change); 2022 exit impulse', 'deterministic dummies, not lags', 'model'),
 ('Sector demand growth Δln VA(t)', 'growth rate of an FR1 driver', 'a transformation of an exogenous driver, not of the dependent variable', 'driver'),
 ('First-difference coherence check', 'Δentry(t) on Δdrivers(t)', 'diagnostic only: the forecast never uses the lagged rate', 'diagnostic'),
 ('Random-walk benchmark', 'entry(t+h) = entry(t)', 'benchmark only, required by NFR1; never used as the forecast', 'benchmark'),
 ('Constant (mean) rate benchmark / null', 'unit mean over the estimation window', 'the unit fixed effect itself: a level, not a dynamic', 'benchmark / combination partner'),
 ('Unit fixed effects', 'a_i estimated on the training window', 'time-invariant intercepts, no dynamics', 'model'),
 ('Uncertainty bands', 'historical residual pairs e_h = w(u_{s+h} − u_s) + (1 − w)u_{s+h}, joint across units and equations; parameter draws; FR1 draws', 'resampled historical errors; no residual AR is estimated or imposed', 'bands'),
 ('Synthetic register (Layer B)', 'firm size evolves by a stated data-generating process', 'test data only; the engine estimates no dynamic model', 'test data')],
 columns=['construct', 'form', 'why_not_autoregressive', 'role'])
NOAR.to_csv(OUT / 'FR12_noar_constructs.csv', index=False)
display(NOAR[['construct', 'role']])

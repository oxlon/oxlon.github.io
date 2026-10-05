# %% [markdown]
# ## Hissə 19 — Yekun yoxlama: reyestr, kataloq və mühərrik bu icra ilə uyğun gəlir
#
# Son xana mühərriki ixrac edilmiş vəziyyətdən yenidən yükləyir və `selftest()`-in hər ssenari üzrə notebook-un
# nəticələrini təkrar istehsal etdiyini, reyestr faylının sxemdən keçdiyini, kataloqun, reyestr komponentlərinin və
# mühərrik sıralarının eyni identifikatorlardan istifadə etdiyini yoxlama ifadəsi ilə təsdiqləyir. Bunlardan hər hansı
# biri uğursuz olarsa, notebook burada dayanır.

# %%
import importlib, microlib.engines.fr12 as _E12
_E12 = importlib.reload(_E12); _E12._S = None
_st_final = _E12.selftest()
assert _st_final['ok'], {k: (v['max_rel_diff'], v['problems']) for k, v in _st_final['detail'].items()}
assert not validate_file(OUT / 'FR12_equations.json')
_res = {sc: _E12.run({}, sc) for sc in SCEN}
assert not check_catalog(OUT / 'FR12_indicator_catalog.csv', OUT / 'FR12_equations.json', _res['Baseline'])
assert all(set(_res[sc]['series']) == set(CATDF.id) for sc in SCEN), 'engine series ids differ from the catalogue'
print(f"engine selftest PASSED for {', '.join(SCEN)} (max relative difference {max(v['max_rel_diff'] for v in _st_final['detail'].values()):.1e}); "
      f"registry {len(REGX)} equations; catalogue {len(CATDF)} ids = engine series = forecast-table ids; total runtime {time.time() - T0:.0f} s")

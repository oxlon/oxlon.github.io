# %% [markdown]
# ### Yekun yoxlama: ssenari mühərriki bu notebook-u təkrar istehsal edir (müqavilə §B)
#
# Mühərrik diskdən yenidən idxal edilir və onun `selftest()` funksiyası hər ssenaridə `FR10_forecast_tidy.csv` faylını
# təkrar istehsal etməlidir (nisbi fərq ≤ 1e-8); beləliklə, mühərrik və notebook bir-birindən ayrıla bilməz. Reyestr
# faylı bir daha yoxlanılır.

# %%
import importlib, microlib.engines.fr10 as _fr10
_fr10 = importlib.reload(_fr10); _fr10._S = None
_final = _fr10.selftest()
print('engine selftest (final):', 'PASS' if _final['ok'] else 'FAIL', {s_: f"{v['max_rel_diff']:.1e}" for s_, v in _final['detail'].items()},
      f"max run time {_final['max_runtime_s']:.3f} s")
assert _final['ok'], 'FR10 engine does not reproduce the notebook'
assert validate_file(OUT / 'FR10_equations.json') == []
from microlib.engines.chain import run_chain
_ch = run_chain({}, 'Baseline', modules=['FR1', 'FR10'])
print(f"chain FR1 -> FR10 (Baseline): ran {_ch['order']}, skipped {_ch['skipped']}, errors {list(_ch['errors'])[:2]}")
assert 'FR10' in _ch['order'], _ch['errors']
print(f'FR10 v2 complete: {len(REGX)} equations, {len(COMP)} components x {len(SCEN)} scenarios, engine selftest PASS, '
      f'Layer B {DATA_MODE} ({len(EBF)} firm-level models)')

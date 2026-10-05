# %% [markdown]
# ## Hissə 2 — İş mühiti və təkrarlanma imkanı
#
# Giriş məlumatları: iş kitabı, `data/dsk_enterprise/` qovluğundakı DSK cədvəlləri (ilk icrada `Mozilla/5.0`
# User-Agent ilə yüklənir və sonra diskdən yenidən oxunur) və `output/` qovluğundakı FR1, FR3 və FR4 nəticə faylları.
# Bütün təsadüfi elementləri (yelpik qrafikinin təkrar seçməsi, parametr çəkilişləri, vəhşi (wild) butstrap, B qatının
# sintetik paneli) bir başlanğıc dəyəri (seed) idarə edir; A qatının heç bir nöqtəvi qiymətləndirməsinə və ya Əsas
# ssenari proqnozuna təsadüfi ədəd daxil olmur.

# %%
%matplotlib inline
import os, sys, re, json, math, warnings, unicodedata, urllib.request, copy
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import matplotlib, matplotlib.pyplot as plt
import xlrd, openpyxl

warnings.filterwarnings('ignore')
SEED = 20261001
pd.set_option('display.width', 230, 'display.max_columns', 60, 'display.max_rows', 200,
              'display.float_format', lambda v: f'{v:,.3f}')
plt.rcParams.update({'figure.figsize': (12, 5.5), 'figure.dpi': 105, 'font.size': 9, 'axes.grid': True,
                     'grid.alpha': 0.3, 'axes.spines.top': False, 'axes.spines.right': False,
                     'legend.frameon': False})
PAL = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22',
       '#17becf', '#393b79', '#b5cf6b', '#a55194', '#637939']

BASE = Path.cwd().resolve()            # the notebook's directory (nbconvert and Jupyter run in it)
assert (BASE / 'data').is_dir() and (BASE / 'output').is_dir(), f'run FR10.ipynb from the MicroUnit directory, not {BASE}'
XL   = BASE / 'data' / 'Statistik data dinamika 05.06.2026 +.xlsx'
DDIR = BASE / 'data' / 'dsk_enterprise'
OUT  = BASE / 'output'
OUT.mkdir(exist_ok=True); DDIR.mkdir(parents=True, exist_ok=True)

LAST_ACT  = 2025                      # last actual year
FC_YEARS  = list(range(2026, 2031))
H         = len(FC_YEARS)
SCEN      = ['Baseline', 'Adverse', 'Reform']
BASE_YR   = 2015                      # price base of chained volumes, as in FR1 and FR5
EST0      = 2005                      # first year of the branch estimation sample (national-accounts coverage)
SEL_END   = 2019                      # every selection score falls in years <= 2019
HOLD      = (2020, LAST_ACT)          # final hold-out window, used for no choice
SYN_MARK  = 'SYNTHETIC — pipeline test, not results'

print('python      ', sys.version.split()[0])
for m in ['numpy', 'pandas', 'scipy', 'statsmodels', 'matplotlib', 'xlrd', 'openpyxl']:
    try:
        mod = __import__(m); print(f'{m:<12}', getattr(mod, '__version__', 'n/a'))
    except ImportError:
        print(f'{m:<12} NOT INSTALLED')
print('workbook    ', XL.exists(), f'{XL.stat().st_size/1e6:.2f} MB' if XL.exists() else '')
print(f'last actual {LAST_ACT} | forecast {FC_YEARS[0]}-{FC_YEARS[-1]} | selection scores <= {SEL_END} | '
      f'hold-out {HOLD[0]}-{HOLD[1]} | seed {SEED}')

# %% [markdown]
# ### 2.1 Təhlil (parsing) qaydaları
#
# FR1–FR5-dən keçən iki tələ. (1) Azərbaycan hərflərinin registri: `'İ'.lower()` `i` + U+0307 qaytarır və bu işarə
# aradan qaldırılmalıdır, nöqtəsiz `ı` isə saxlanmalıdır. (2) Mətn kimi saxlanılan DSK xanaları: minliklərin bölünməz
# boşluqla ayrılması, vergüllü onluq kəsrlər, qeyd ulduzları və — sənaye cədvəllərində yeni olan — *min faiz*
# mənasını verən **`t.`** şəkilçisi (`'7.8 t.'` = baza ilinin 7 800%-i). `to_num` bunların hamısını emal edir;
# aşağıdakı yoxlama ifadələri (assertions) gələcəkdə edilən düzəlişin onlardan hər hansı birini pozmasına imkan vermir.

# %%
def az_lower(s):
    return unicodedata.normalize('NFC', str(s).lower().replace('̇', ''))

_BLANK = {'', '-', '–', '—', '...', '..', '…', 'x', 'n/a', 'N/A'}
def to_num(v):
    if v is None or isinstance(v, bool):
        return np.nan
    if isinstance(v, (int, float, np.floating)):
        return np.nan if (isinstance(v, float) and np.isnan(v)) else float(v)
    t = str(v).replace('\xa0', '').replace(' ', '').strip()
    mult = 1.0
    if re.search(r'\d\s*t\.?\s*$', t):          # DSK index tables: '7.8 t.' = thousand per cent
        mult = 1000.0; t = re.sub(r'\s*t\.?\s*$', '', t)
    t = t.replace(' ', '').rstrip('*').replace('%', '')
    if t in _BLANK:
        return np.nan
    if re.fullmatch(r'-?\d+,\d+', t):
        t = t.replace(',', '.')
    elif re.fullmatch(r'-?\d{1,3}(\.\d{3})+,\d+', t):
        t = t.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'-?[1-9]\d{0,2}(\.\d{3})+', t):       # TEXT '1.581' = 1 581 (dot as thousands separator)
        t = t.replace('.', '')
    else:
        t = t.replace(',', '')
    try:
        return float(t) * mult
    except ValueError:
        return np.nan

for raw, want in [('7.8 t.', 7800.0), ('97,8 t.', 97800.0), ('33,0*', 33.0), ('4\xa0088\xa0188,1', 4088188.1),
                  ('…', np.nan), ('-', np.nan), (12.5, 12.5), ('1.234,5', 1234.5), ('108 .3', 108.3), ('1.581', 1581.0), (1.581, 1.581)]:
    got = to_num(raw)
    assert (np.isnan(got) and np.isnan(want)) or abs(got - want) < 1e-9, f'to_num({raw!r}) = {got}'
assert az_lower('İqtisadiyyat') == 'iqtisadiyyat' and az_lower('artım') == 'artım'
print('parsing self-tests passed (thousand-per-cent suffix, comma decimals, footnote marks, Azerbaijani casing)')

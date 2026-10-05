# %% [markdown]
# ### 19.5 Azərbaycan dilində sətirlər
#
# FR10-un CSV fayllarına yazdığı hər ingiliscə mətn (sözlərdən ibarət xana dəyərləri və sütun başlıqları)
# `output/FR10_strings_az.csv` faylında Azərbaycan dilində variant alır (`en`, `az`, `how`, `files`). Məhsul və yer adları eyni
# cədvəlin DSK-nın öz Azərbaycan dilində nəşrindən götürülür (§18.6); qalan hər şey
# `data/fr10_az/FR10_strings_az_templates.csv` faylındakı tərcümə şablonlarından istifadə edir (rəqəmlər yer tutuculardır,
# buna görə icradan asılı rəqəmlər ötürülür). Mövcud CSV faylları öz formasını saxlayır (reqressiyasızlıq qaydası); yeni
# v2 cədvəlləri `*_az` sütunlarını özləri daşıyır.

# %%
TPL = pd.read_csv(BASE / 'data' / 'fr10_az' / 'FR10_strings_az_templates.csv')
TPL_MAP = dict(zip(TPL.template_en, TPL.template_az))
_NUMRX = re.compile(r'(?<![A-Za-z_\d])[-+−]?\d+(?:[.,]\d+)*(?:e[-+]?\d+)?')
_AZCH = re.compile('[əƏığĞşŞçÇöÖüÜ]')
def _tmpl(s):
    nums = []
    def rep(m): nums.append(m.group(0)); return '{%d}' % (len(nums) - 1)
    return _NUMRX.sub(rep, s), nums
def to_az(s):
    s0 = re.sub(r'\s+', ' ', s).strip()
    if s0 in RUNTIME_AZ: return RUNTIME_AZ[s0], 'composed at run time (v2.1)'
    for d_, how in [(PROD_AZ, 'DSK az (018)'), (PLACE_AZ, 'DSK az (018_1)')]:
        if s0 in d_: return d_[s0], how
    if s0 in BNAME.values(): return BNAME_AZ[[b for b, n in BNAME.items() if n == s0][0]], 'branch dictionary'
    if s0 in REGION_AZ: return REGION_AZ[s0], 'region dictionary'
    t, nums = _tmpl(s)
    if t in TPL_MAP:
        return re.sub(r'\{(\d+)\}', lambda m: nums[int(m.group(1))], TPL_MAP[t]), 'translation template'
    return None, 'untranslated'
TECH_COLS = {'source_csv', 'source_column', 'equation_ids', 'scenarios', 'id', 'id_pattern', 'regressors', 'dropped_regressors', 'input',
             'component', 'model_id', 'term', 'eq_id', 'file', 'files', 'feeding_files', 'equation', 'imputed_years'}
_STR = {}
for p in sorted(OUT.glob('FR10_*.csv')):
    if p.name.startswith(('FR10_SYNTHETIC_firm', 'FR10_FIRM_firm', 'FR10_forecast_tidy', 'FR10_strings_az')): continue
    df_ = pd.read_csv(p, dtype=str)
    _twin = lambda c: (str(c).endswith('_az') or f'{c}_az' in df_.columns or (str(c).endswith('_en') and f'{str(c)[:-3]}_az' in df_.columns)
                       or str(c) in TECH_COLS)
    cells = [(v, f'{p.name}:{c}') for c in df_.columns if not _twin(c) for v in df_[c].dropna().unique()]
    cells += [(str(c), f'{p.name}:<header>') for c in df_.columns if ' ' in str(c) and not str(c).startswith('Unnamed')]
    for v, where in cells:
        if not re.search(r'[A-Za-z]{3,}', v) or re.fullmatch(r'[-+0-9.eE]+', v): continue
        if _AZCH.search(v) and not re.search(r'\b(the|of|and|by|in)\b', v): continue        # already Azerbaijani
        if not re.search(r'[A-Za-z]{3,}', re.sub(r'\b(Chow|CUSUM|DM|HLN|AUC|ROA|TFP|HHI|NACE)\b', '', v)): continue   # test names only
        if re.fullmatch(r'[\w{}%().,\-+/:=*|;<>]+', v) and ' ' not in v: continue             # identifiers / codes / file names
        if re.fullmatch(r'(\s*[\w\-]+\.(csv|xls|xlsx|md|ipynb)\s*[,;]?)+', v) or v.startswith('http'): continue
        _STR.setdefault(v, set()).add(where)
STR_AZ = pd.DataFrame([dict(en=k, az=to_az(k)[0], how=to_az(k)[1], files=';'.join(sorted({w.split(':')[0] for w in v}))) for k, v in _STR.items()])
STR_AZ.to_csv(OUT / 'FR10_strings_az.csv', index=False)
_un = STR_AZ[STR_AZ.az.isna()]
print(f'FR10_strings_az.csv: {len(STR_AZ)} English strings, translated {len(STR_AZ) - len(_un)} '
      f'({(1 - len(_un) / len(STR_AZ)) * 100:.1f}%): ' + ', '.join(f'{k} {v}' for k, v in STR_AZ.how.value_counts().items()))
if len(_un): print('untranslated (new strings since the template was made):', _un.en.head(12).tolist())
assert len(_un) <= 0.02 * len(STR_AZ), 'too many untranslated strings: extend data/fr10_az/FR10_strings_az_templates.csv'

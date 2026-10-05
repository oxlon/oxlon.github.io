# %% [markdown]
# ### 7.1 Müşahidə dövrü daxilindəki boşluqlar: qrafik və cədvəllər üçün doldurulur, qiymətləndirmə üçün heç vaxt
#
# FR12-nin bir neçə sırasında müşahidə dövrünün **daxilində** çatışmayan illər var: sahibkarlıq qeydiyyatları və
# qeydiyyatdan çıxarılmaları (006) və KOB payları (012, 013) üçün **2021** buraxılışı yoxdur; NACE bölmələri üzrə reyestr
# axınları yalnız 2021, 2024 və 2025-ci tam illər (**2022–2023** yoxdur; yalnız 2022-ci ilin yanvar–iyun dövrü qalıb) və
# 2022, 2024–2026-cı illərin yarımilləri (**2023-cü ilin I yarımili** yoxdur) üzrə mövcuddur. Qayda (v2):
#
# - iki müşahidə olunan il arasındakı boşluq iki qonşu müşahidə olunan il əsasında **səviyyələr (saylar, ehtiyatlar) üçün
#   log-xətti interpolyasiya** və **əmsallar və paylar üçün xətti interpolyasiya** ilə doldurulur; səviyyələrin
#   aqreqatları (bütün fəaliyyət qrupları) doldurulmuş komponentlərin cəmidir, beləliklə, additiv qalır;
# - birinci və ya sonuncu müşahidə olunan ildən kənara heç nə **ekstrapolyasiya edilmir**: əvvəldəki boşluq (məsələn,
#   2021-ci ildən əvvəl bölmələr üzrə reyestr, 2021-ci ildən əvvəl region paneli) **doldurulmur** və belə sadalanır;
#   gələcək proqnozun işidir;
# - hər doldurulmuş dəyər `output/FR12_series_filled.csv` (id, il, dəyər, imputed, üsul, istifadə olunan qonşular) və
#   `FR12_forecast_tidy.csv` fayllarında `imputed = True` işarəsini daşıyır; notebook-un qrafikləri doldurulmuş nöqtələri
#   **qırıq xətlərlə birləşdirilmiş içiboş markerlər** ilə, "Doldurulmuş (interpolyasiya)" leqendası ilə göstərir;
# - **qiymətləndirmədə yalnız müşahidə olunan məlumatlar istifadə olunur.** Hissə 11–14-dəki hər model müşahidə olunan
#   illər üzrə qiymətləndirilir; doldurulmuş dəyərlər yalnız əmsalların və 2030 proqnozlarının nə qədər dəyişdiyini
#   göstərən həssaslıq təhlilinə (Hissə 14.1) daxil olur.
#
# Fərqli təriflərə malik iki buraxılış arasında (006: 2020 "yeni yaradılmış", 2022 "yeni qeydiyyata alınmış", F17) və ya
# 2022-ci ilin birdəfəlik qeydiyyatdan çıxarma dalğasının (F16) yanında doldurulmuş dəyər hər qonşunun yarısını miras alır:
# bu, ölçmə deyil, təqdimat dəyəridir.

# %%
FILL_START = 2019                                   # first year of FR12's panels: earlier missing years of a series are a leading gap
def fill_gaps(s, kind, sid, ref_start=FILL_START):
    '''s: year-indexed observed values. kind: level (log-linear) | rate (linear). Interior gaps only; leading gap reported.'''
    s = pd.Series(s, dtype=float).dropna(); s.index = s.index.astype(int); s = s.sort_index()
    if s.empty: return s, []
    out = s.reindex(range(int(s.index.min()), int(s.index.max()) + 1)); rec = []
    for y, v in out.items():
        if y in s.index:
            rec.append(dict(id=sid, year=y, value=float(v), imputed=False, method='observed', neighbours_used='')); continue
        lo = max(t for t in s.index if t < y); hi = min(t for t in s.index if t > y); f = (y - lo) / (hi - lo)
        if kind == 'level' and s[lo] > 0 and s[hi] > 0:
            v = float(np.exp(np.log(s[lo]) + f * np.log(s[hi] / s[lo]))); m = 'log-linear interpolation'
        else:
            v = float(s[lo] + f * (s[hi] - s[lo])); m = 'linear interpolation' + (' (non-positive neighbour)' if kind == 'level' else '')
        out[y] = v; rec.append(dict(id=sid, year=y, value=v, imputed=True, method=m, neighbours_used=f'{lo};{hi}'))
    for y in range(ref_start, int(s.index.min())):
        rec.append(dict(id=sid, year=y, value=np.nan, imputed=False, method='not filled: leading gap (before the first observed year; no extrapolation)', neighbours_used=''))
    return out, rec

FILL_REC = []
def fill_frame(df, unit_col, specs, prefix, ref_start=FILL_START):
    '''df long (unit, year, columns); specs {column: (kind, code)} -> long filled frame with an `imputed` flag per value.'''
    rows = []
    for u, g in df.groupby(unit_col):
        g = g.set_index('year')
        for col, (kind, code) in specs.items():
            f, rec = fill_gaps(g[col], kind, f'fr12:{prefix}:{code}:{iid(u)}', ref_start); FILL_REC.extend(rec)
            imp = {r['year'] for r in rec if r['imputed']}
            rows += [dict(unit=u, year=int(y), var=col, value=float(v), imputed=int(y) in imp) for y, v in f.items()]
    return pd.DataFrame(rows)
iid = lambda u: re.sub(r'[^A-Za-z0-9_.\-]', '_', str(u).strip())

# (1) activity groups (006): levels log-linear, rates linear; ALL = sum of filled components (levels), rate interpolated
_g = IND_G.rename(columns={'group': 'unit'})
FA = fill_frame(_g, 'unit', {'registered': ('level', 'N'), 'new': ('level', 'new'), 'dereg': ('level', 'exits'),
                             'entry': ('rate', 'entry'), 'exit': ('rate', 'exit')}, 'act')
_tot = FA[FA['var'].isin(['registered', 'new', 'dereg'])].groupby(['var', 'year']).agg(value=('value', 'sum'), imputed=('imputed', 'any')).reset_index()
_ta = _g.groupby('year')[['registered', 'new', 'dereg']].sum()
for (var, code) in [('registered', 'N'), ('new', 'new'), ('dereg', 'exits')]:
    for _, r in _tot[_tot['var'] == var].iterrows():
        FILL_REC.append(dict(id=f'fr12:act:{code}:ALL', year=int(r.year), value=float(r.value), imputed=bool(r.imputed),
                             method='sum of filled components' if r.imputed else 'observed', neighbours_used='components' if r.imputed else ''))
for var, code in [('entry', 'new'), ('exit', 'dereg')]:
    _, rec = fill_gaps(_ta[code] / _ta.registered * 100, 'rate', f'fr12:act:{var}:ALL'); FILL_REC.extend(rec)
FA = pd.concat([FA, _tot.assign(unit='ALL')], ignore_index=True)
# (2) SME shares (012 output, 013 employees) and the large-firm output share: linear
FS_ = fill_frame(SME.reset_index().rename(columns={'group': 'unit'}), 'unit', {'sme_output_share': ('rate', 'sme_output_share'),
                 'sme_employment_share': ('rate', 'sme_employment_share'), 'large_output_share': ('rate', 'large_share')}, 'conc')
# (3) register flows by NACE section: full years (2021, 2024, 2025) and January-June (2022, 2024-2026)
FSEC = fill_frame(IND_S.rename(columns={'sec': 'unit'}), 'unit', {'stock': ('level', 'stock'), 'new': ('level', 'new'), 'liq': ('level', 'liq'),
                  'entry': ('rate', 'entry'), 'exit': ('rate', 'exit')}, 'sec')
_h1 = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'H1') & FLOWS.unit.isin(MKT)].copy()
FSEC_H1 = fill_frame(_h1, 'unit', {'stock': ('level', 'stock'), 'new': ('level', 'new'), 'liq': ('level', 'liq')}, 'sec_h1')
# (4) region panel 2021-2025 and other annual series: scanned; interior gaps would be filled the same way
FRG = fill_frame(RG.rename(columns={'region': 'unit'}), 'unit', {'enterprises': ('level', 'N'), 'new': ('level', 'new'), 'liquidated': ('level', 'exits'),
                 'entry': ('rate', 'entry'), 'exit': ('rate', 'exit')}, 'reg')
_extra = [fill_frame(PCM_G.PCM.reset_index().rename(columns={'group': 'unit', 'PCM': 'pcm'}), 'unit', {'pcm': ('rate', 'pcm')}, 'info', ref_start=2005)]
SERIES_FILLED = pd.DataFrame(FILL_REC)
SERIES_FILLED['method_az'] = SERIES_FILLED.method.map({'observed': 'müşahidə', 'log-linear interpolation': 'log-xətti interpolyasiya',
    'linear interpolation': 'xətti interpolyasiya', 'sum of filled components': 'doldurulmuş komponentlərin cəmi',
    'linear interpolation (non-positive neighbour)': 'xətti interpolyasiya (müsbət olmayan qonşu)',
    'not filled: leading gap (before the first observed year; no extrapolation)': 'doldurulmayıb: ilkin boşluq (ilk müşahidədən əvvəl; ekstrapolyasiya yoxdur)'})
assert SERIES_FILLED.method_az.notna().all()
SERIES_FILLED.to_csv(OUT / 'FR12_series_filled.csv', index=False)
_imp = SERIES_FILLED[SERIES_FILLED.imputed]
display(_imp.assign(family=_imp.id.str.split(':').str[1]).groupby(['family', 'year', 'method']).size().rename('values filled').reset_index())
print(f"{len(_imp)} values filled in {_imp.id.nunique()} series (estimation unchanged: observed data only); "
      f"{int((SERIES_FILLED.method.str.startswith('not filled')).sum())} leading-gap years listed as not filled")

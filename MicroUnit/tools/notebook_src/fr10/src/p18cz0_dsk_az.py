# %% [markdown]
# ### 18.6 Məhsulların və yerlərin rəsmi Azərbaycan dilində adları (DSK, eyni cədvəllərin Azərbaycan dilində nəşri)
#
# DSK bütün sənaye cədvəllərini Azərbaycan dilində `https://www.stat.gov.az/source/industry/az/<file>.xls` ünvanında dərc
# edir (`https://www.stat.gov.az/source/industry/?lang=az` indeks səhifəsində tapılıb, brauzer User-Agent-i ilə).
# `018` (natura ifadəsində məhsullar) və `018_1` (şəhər və rayonlar üzrə məhsullar) cədvəlləri bir dəfə
# `data/dsk_enterprise_az/` qovluğuna yüklənir və ingilis nəşri ilə **sətir-sətir, sətrin bütün rəqəmsal xanalarının
# uyğun gəlməsi tələb olunmaqla (0,5% dəqiqliklə; iki nəşr bir neçə son rəqəmdə fərqlənir)** uyğunlaşdırılır; beləliklə,
# ad yalnız eyni məlumatları olan sətrə verilir. Uyğunluq cədvəli `FR10_product_names_az.csv` faylında keşlənir.

# %%
AZ_DIR = BASE / 'data' / 'dsk_enterprise_az' / 'industry'; AZ_DIR.mkdir(parents=True, exist_ok=True)
AZ_URL = 'https://www.stat.gov.az/source/industry/az/{fn}'
_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
def fetch_az(fn):
    p = AZ_DIR / fn
    if p.exists() and p.read_bytes()[:8] == XLS_MAGIC: return p, 'present'
    try:
        req = urllib.request.Request(AZ_URL.format(fn=fn), headers={'User-Agent': _UA})
        with urllib.request.urlopen(req, timeout=60) as r: blob = r.read()
        if blob[:8] == XLS_MAGIC: p.write_bytes(blob); return p, 'downloaded'
        return None, 'not an Excel file (HTML reply)'
    except Exception as e:
        return None, f'failed: {e}'
def _rows(path):
    sh = xlrd.open_workbook(path).sheet_by_index(0); out = []
    for r in range(sh.nrows):
        lab = ' '.join(str(sh.cell_value(r, c)).strip() for c in range(2) if isinstance(sh.cell_value(r, c), str) and str(sh.cell_value(r, c)).strip())
        vals = tuple(to_num(sh.cell_value(r, c)) for c in range(2, sh.ncols))
        out.append((re.sub(r'\s+', ' ', lab).strip(), vals))
    return out
def match_az(fn_en, fn_az):
    '''{english label: azerbaijani label} for rows whose numeric cells are all equal (row-aligned editions).'''
    pa, st = fetch_az(fn_az)
    if pa is None: return {}, st, 0, 0
    en, az = _rows(P_('industry', fn_en)), _rows(pa)
    same = lambda a, b: len(a) == len(b) and all((np.isnan(x) and np.isnan(y)) or abs(x - y) <= 5e-3 * max(abs(x), abs(y), 1) for x, y in zip(a, b))
    m, n_lab, n_ok = {}, 0, 0
    for i, (le, ve) in enumerate(en):
        if not le or not re.search(r'[A-Za-z]', le): continue
        n_lab += 1
        if i < len(az) and az[i][0] and (same(ve, az[i][1]) or not np.isfinite(ve).any()):
            m.setdefault(le, az[i][0]); n_ok += 1
    return m, st, n_lab, n_ok
PROD_AZ, _st1, _n1, _k1 = match_az('018en.xls', '018.xls')
PLACE_AZ, _st2, _n2, _k2 = match_az('018_1en.xls', '018_1.xls')
_cache = AZ_DIR.parent / 'FR10_product_names_az.csv'
if PROD_AZ:
    pd.DataFrame([dict(table=t, en=k, az=v) for t, d_ in [('018', PROD_AZ), ('018_1', PLACE_AZ)] for k, v in d_.items()]).to_csv(_cache, index=False)
elif _cache.exists():
    _c = pd.read_csv(_cache); PROD_AZ = dict(zip(_c[_c.table == '018'].en, _c[_c.table == '018'].az)); PLACE_AZ = dict(zip(_c[_c.table == '018_1'].en, _c[_c.table == '018_1'].az))
_np_ = [l for l in PROD.label if l not in PROD_AZ]
print(f'DSK Azerbaijani edition: 018 {_st1} ({_k1}/{_n1} labelled rows matched on identical data), 018_1 {_st2} ({_k2}/{_n2}); '
      f'{len(PROD) - len(_np_)}/{len(PROD)} FR10 products have the official Azerbaijani name' + (f'; unmatched: {_np_[:5]}' if _np_ else ''))

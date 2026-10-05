# %% [markdown]
# ## Hissə 4 — DSK cədvəllərinin toplanması
#
# İş kitabında 30 sənaye sahəsi yalnız **2016**-cı ildən (on illik müşahidə: buraxılış, əlavə dəyər, investisiya,
# əmək haqqı, işçilərin sayı), vergi bəyannamələrinin aqreqatları isə yalnız **2021**-ci ildən verilir. Bu, hər hansı
# struktur pay sistemi və ya artımın uçotu üçün çox qısadır və orada mülkiyyət, ölçü qrupu, ehtiyatlar, məhsullar və
# ya regional sənaye üzrə heç bir bölgü yoxdur. Aşağıdakı DSK cədvəlləri bu boşluqları doldurur; onlar bir dəfə
# `https://www.stat.gov.az/source/<section>/en/<file>` ünvanından yüklənir (birbaşa fayl ünvanları `Mozilla/5.0`
# User-Agent-i qəbul edir) və `data/dsk_enterprise/<section>/` qovluğunda saxlanılır.
#
# Hər faylın həqiqi Excel iş kitabı olduğu yoxlanılır: DSK saytı artıq dərc etmədiyi cədvəl üçün **HTTP 200 ilə HTML
# səhifəsi** qaytarır və belə cavab məlumat kimi saxlanılmır, "dərc olunmur" kimi qeydə alınır. Hissə 6 məhz bu yolla
# müəyyən edir ki, əsas fondların yenilənməsi, çıxması və köhnəlməsi cədvəlləri (sənaye `017_2`–`017_7`) və kapital
# veriminin indeksi (köhnə nömrələmədə `018_1`) **artıq dərc olunmur** — DSK indeksində onların bölməsi şərh kimi
# bağlanıb (commented out), fayl nömrələri isə regional məhsul cədvəlləri üçün yenidən istifadə olunub.

# %%
DSK_URL = 'https://www.stat.gov.az/source/{sec}/en/{fn}'
DSK_FILES = {
 'industry': {
  '002-003en.xls': 'Main macro-economic indicators by sector of industry; share of industry in the economy',
  '004-007-008en.xls': 'Active industrial enterprises by ownership and activity (4/7); by size class (8)',
  '005en.xls': 'Industrial output by type of ownership',
  '006en.xls': 'Number of employees in industry by activity',
  '006_1en.xls': 'Number of employees in industry by economic region',
  '006_2en.xls': 'Average monthly nominal wages in industry by activity',
  '009en.xls': 'Indices of industrial output by activity (9.1 previous year = 100; 9.2 2010 = 100)',
  '010en.xls': 'Volume of industrial output at actual prices by activity',
  '010_1en.xls': 'Sectoral structure of industry, % of total',
  '010_2en.xls': 'Structure of industrial production by form of ownership, by activity',
  '011en.xls': 'Shipped goods by activity',
  '012en.xls': 'Structure of non-state industrial output by activity',
  '013en.xls': 'Stocks of finished goods held by industrial enterprises (as of 1 January)',
  '014en.xls': 'Main indicators of mining and quarrying',
  **{f'014_{i}en.xls': f'Main indicators of mining branch 14.{i}' for i in range(1, 5)},
  '015en.xls': 'Main indicators of manufacturing',
  **{f'015_{i}en.xls': f'Main indicators of manufacturing branch 15.{i} (incl. main products in kind)' for i in range(1, 25)},
  '016en.xls': 'Main indicators of electricity, gas and steam supply',
  '017en.xls': 'Main indicators of water supply, sewerage and waste management',
  '017_1en.xls': 'Main industrial products in kind by region (reused number)',
  **{f'017_{i}en.xls': 'Fixed industrial assets: indexes / structure / renewal / disposal / depreciation (old index)' for i in range(2, 8)},
  '018en.xls': 'Manufacture of the most important industrial products in kind',
  '018_1en.xls': 'Main industrial products in kind by region (reused number; formerly capital-yield index)',
  '018_2en.xls': 'Main industrial products in kind by region (2)',
  '019-019_1en.xls': 'Investment in fixed capital of industry by activity and source',
  '020_1en.xls': 'Volume of innovative products by activity',
  '020_2en.xls': 'Expenditure on technological innovation by type',
  '020_3en.xls': 'Expenditure on technological innovation by activity',
  '020_4en.xls': 'Expenditure on technological innovation by direction of use',
  '020_5en.xls': 'Factors impeding innovation',
  '021en.xls': 'Number of active industrial enterprises by economic region',
  '022en.xls': 'Volume of industrial output by economic region',
  '023en.xls': 'Indices of industrial output by economic region',
  '024en.xls': 'Share of the non-state sector in industrial output by economic region',
  '025en.xls': 'Industry of Baku city (regional profile)'},
 'entrepreneurship': {
  '001en.xls': 'Main indicators of micro, small and medium enterprises (SMEs)',
  '001_1en.xls': 'Share of SMEs in the economy',
  '002en.xls': 'Number of active SMEs', '003en.xls': 'SMEs by economic region',
  '004en.xls': 'Newly registered SMEs', '004_1en.xls': 'Deregistered SMEs',
  '005en.xls': 'Active SMEs by activity and ownership', '006en.xls': 'Registered / newly registered / deregistered entities by activity',
  '007en.xls': 'Newly registered SMEs by activity', '008en.xls': 'Deregistered SMEs by activity',
  '009en.xls': 'Value of goods and services of SMEs by activity', '010en.xls': 'Employees of SMEs by activity',
  '012en.xls': 'SME share of output by activity', '013en.xls': 'SME share of employees by activity',
  '014en.xls': 'SME investment in fixed capital by activity', '015en.xls': 'SME share of investment by activity',
  '021en.xls': 'SME output by region and activity',
  '024en.xls': 'Active SMEs established one year ago', '025en.xls': 'Active SMEs established two years ago',
  '026en.xls': 'Active SMEs established three years ago', '027en.xls': 'Active SMEs established four years ago',
  '028en.xls': 'Active SMEs established five years ago', '029en.xls': 'Value added of SMEs by activity',
  '031en.xls': 'Average wages in SMEs by activity', '039en.xls': 'Assets of SMEs by activity',
  '039_1en.xls': 'SME share of assets', '040en.xls': 'Stocks of SMEs by activity', '040_1en.xls': 'SME share of stocks',
  '041en.xls': 'Taxes paid by SMEs by activity'},
 'st_units': {
  '1_1_en.xls': 'Statistical units by activity', '1_2_en.xls': 'Statistical units by ownership and activity',
  '1_3_i_en.xls': 'Large business entities by activity', '1_3_o_en.xls': 'Medium business entities by activity',
  '1_3_k_en.xls': 'Small business entities by activity', '1_3_m_en.xls': 'Micro business entities by activity',
  '1_4_i_en.xls': 'Large business entities by region',
  '2_1_en.xls': 'Newly created and liquidated units by activity', '2_2_en.xls': 'Newly created and liquidated units by ownership',
  '2_3_en.xls': 'Newly created and liquidated units by region'},
 'system_nat_accounts': {
  '013en.xls': 'Production and generation of income account by section (output, IC, VA, compensation, GOS, CFC)',
  '014en.xls': 'GDP by activity, current prices', '015en.xls': 'Output of industry by activity (NACE 2-digit)',
  '015_1en.xls': 'Intermediate consumption of industry by activity', '015_2en.xls': 'Value added in industry by activity',
  '015_4en.xls': 'Share of intermediate consumption in output, industry', '022en.xls': 'Structure of compensation of employees',
  '023en.xls': 'Share of compensation in value added', '024en.xls': 'Structure of consumption of fixed capital',
  '025en.xls': 'Share of consumption of fixed capital in value added', '029en.xls': 'Physical volume index of output / value added',
  '030_1en.xls': 'GDP by activity at 2015 prices', '030_2en.xls': 'Labour productivity by activity',
  '031en.xls': 'Fixed assets by activity, end of year', '034en.xls': 'Output of main branches by economic region'}}
LOCAL_DIR = {'industry': 'industry', 'entrepreneurship': 'entrepreneurship', 'st_units': 'st_units',
             'system_nat_accounts': 'nat_accounts'}
XLS_MAGIC = bytes.fromhex('d0cf11e0a1b11ae1')

def fetch_dsk():
    rows = []
    for sec, files in DSK_FILES.items():
        d = DDIR / LOCAL_DIR[sec]; d.mkdir(parents=True, exist_ok=True)
        for fn, title in files.items():
            p = d / fn; flag = d / (fn + '.unpublished')
            if p.exists() and p.read_bytes()[:8] == XLS_MAGIC:
                rows.append((sec, fn, title, p.stat().st_size, 'present')); continue
            if flag.exists():
                rows.append((sec, fn, title, 0, 'NOT PUBLISHED (' + flag.read_text().strip() + ')')); continue
            try:
                req = urllib.request.Request(DSK_URL.format(sec=sec, fn=fn), headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    blob = r.read()
                if blob[:8] == XLS_MAGIC:
                    p.write_bytes(blob); rows.append((sec, fn, title, len(blob), 'downloaded'))
                else:
                    flag.write_text('URL returns an HTML page, HTTP 200')
                    rows.append((sec, fn, title, 0, 'NOT PUBLISHED (URL returns an HTML page, HTTP 200)'))
            except Exception as e:
                rows.append((sec, fn, title, 0, f'FAILED: {e}'))
    return pd.DataFrame(rows, columns=['section', 'file', 'content', 'bytes', 'status'])

MANIFEST = fetch_dsk()
print(MANIFEST.status.str.split(' ').str[0].value_counts().to_string())
display(MANIFEST[~MANIFEST.status.isin(['present', 'downloaded'])])
miss = MANIFEST[MANIFEST.status.str.startswith('FAILED')]
assert miss.empty, f'DSK inputs could not be downloaded: {miss.file.tolist()}'
UNPUBLISHED = MANIFEST[MANIFEST.status.str.startswith('NOT')].file.tolist()
print(f'{(MANIFEST.status.isin(["present", "downloaded"])).sum()} DSK tables available in {DDIR}; '
      f'{len(UNPUBLISHED)} no longer published: {UNPUBLISHED}')

# %% [markdown]
# ### 4.1 Bütün DSK cədvəlləri üçün bir oxuyucu və bir sahə lüğəti
#
# Heç bir oxuyucu sabit yerdəyişmə (offset) fərz etmir. `dsk_wide` ən çox il xanası olan başlıq sətrini tapır, adı
# onun solundakı mətn sütunlarından (və cədvəldə çap olunubsa, NACE kodunu) götürür və sətirləri çap olunduğu ardıcıllıqla
# qaytarır. **Sahə lüğəti** 30 sənaye sahəsinin hər birinə NACE kodu, ingiliscə və azərbaycanca ad, DSK-nın ingiliscə
# adları üçün nümunə (pattern) və iş kitabının azərbaycanca adları üçün nümunə verir; hər uyğunluğun **yeganə** olduğu
# yoxlama ifadəsi ilə təsdiqlənir, belə ki, adı dəyişdirilmiş və ya əlavə edilmiş sətir sıranı xəbərsiz sürüşdürmək
# əvəzinə notebook-u dayandırır.

# %%
def _yr(v):
    if isinstance(v, float) and v.is_integer() and 1985 <= v <= 2035: return int(v)
    if isinstance(v, str):
        m = re.fullmatch(r'\s*((?:19|20)\d{2})\s*\**\s*(\d\))?\s*', v)
        if m: return int(m.group(1))
        m = re.search(r'as of 01\.01\.((?:19|20)\d{2})', v)
        if m: return int(m.group(1))
    return None

import pickle
CACHE_PATH = DDIR / '_fr10_parse_cache.pkl'
def _sig():
    fs = sorted(p for p in DDIR.rglob('*.xls'))
    return tuple((p.name, p.stat().st_size, int(p.stat().st_mtime)) for p in fs) + ((XL.name, XL.stat().st_size, int(XL.stat().st_mtime)), ('parser', 2))
SIG = _sig()
try:
    _c = pickle.loads(CACHE_PATH.read_bytes()) if CACHE_PATH.exists() else {}
    CACHE = _c['data'] if _c.get('sig') == SIG else {}
except Exception:
    CACHE = {}
print(f'parse cache: {len(CACHE)} parsed tables reused' if CACHE else 'parse cache: empty or stale - tables parsed from the files')
def save_cache():
    CACHE_PATH.write_bytes(pickle.dumps({'sig': SIG, 'data': CACHE}))

def dsk_wide(path, sheet=None, min_years=4, label_cols=None):
    key = ('dsk', str(path), sheet, min_years, label_cols)
    if key not in CACHE: CACHE[key] = _dsk_wide(path, sheet, min_years, label_cols)
    return CACHE[key].copy()

def _dsk_wide(path, sheet=None, min_years=4, label_cols=None):
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_name(sheet) if sheet else wb.sheet_by_index(0)
    best = (0, None, None)
    for r in range(min(sh.nrows, 14)):
        ys = {c: _yr(sh.cell_value(r, c)) for c in range(sh.ncols)}
        ys = {c: y for c, y in ys.items() if y}
        if len(ys) > best[0]: best = (len(ys), r, ys)
    assert best[0] >= min_years, f'{path}: no year header found'
    _, hr, ycols = best
    fyc = min(ycols) if label_cols is None else label_cols
    rows = []
    for r in range(hr + 1, sh.nrows):
        cells = [sh.cell_value(r, c) for c in range(fyc)]
        lab = ' '.join(str(v).strip() for v in cells if isinstance(v, str) and str(v).strip())
        code = ''
        for v in cells:
            if isinstance(v, float) and v.is_integer() and 1 <= v <= 99: code = f'{int(v):02d}'
            if isinstance(v, str) and re.fullmatch(r'\s*\d{2}\s*', v): code = v.strip()
        vals = {y: to_num(sh.cell_value(r, c)) for c, y in ycols.items()}
        if not lab and not np.isfinite(list(vals.values())).any(): continue
        d_ = {'row': r, 'code': code, 'label': re.sub(r'\s+', ' ', lab).strip()}; d_.update(vals); rows.append(d_)
    return pd.DataFrame(rows)

def P_(sec, fn): return DDIR / LOCAL_DIR[sec] / fn

BR = [  # code, section, short English name, Azerbaijani (workbook) pattern, DSK English include / exclude patterns
 ('06', 'B', 'Crude oil and natural gas',        r'xam neft',                          r'crude petroleum and natural gas', None),
 ('07', 'B', 'Metal ores',                       r'metal filiz',                       r'metal ores', None),
 ('08', 'B', 'Other mining and quarrying',       r'mədənçıxarma sənayesinin digər',    r'other mining', None),
 ('09', 'B', 'Mining support services',          r'sahəsinə xidmətlərin',              r'mining support', None),
 ('10', 'C', 'Food products',                    r'qida məhsullarının',                r'food products', None),
 ('11', 'C', 'Beverages',                        r'içki istehsalı',                    r'beverage', None),
 ('12', 'C', 'Tobacco products',                 r'tütün',                             r'tobacco', None),
 ('13', 'C', 'Textiles',                         r'toxuculuq',                         r'textile', None),
 ('14', 'C', 'Wearing apparel',                  r'geyim istehsalı',                   r'wearing apparel', None),
 ('15', 'C', 'Leather and footwear',             r'dəri və dəridən',                   r'leather', None),
 ('16', 'C', 'Wood products',                    r'ağacın emalı',                      r'\bwood', None),
 ('17', 'C', 'Paper products',                   r'kağız',                             r'paper', None),
 ('18', 'C', 'Printing',                         r'poliqrafiya',                       r'printing', None),
 ('19', 'C', 'Refined petroleum products',       r'neft məhsullarının',                r'refined petroleum', None),
 ('20', 'C', 'Chemicals',                        r'kimya',                             r'chemical', None),
 ('21', 'C', 'Pharmaceuticals',                  r'əczaçılıq',                         r'pharmaceutical', None),
 ('22', 'C', 'Rubber and plastics',              r'rezin',                             r'rubber', None),
 ('23', 'C', 'Non-metallic minerals',            r'tikinti materiallarının',           r'non-metallic', None),
 ('24', 'C', 'Basic metals',                     r'metallurgiya',                      r'basic metals', None),
 ('25', 'C', 'Fabricated metal products',        r'hazır metal',                       r'fabricated metal', None),
 ('26', 'C', 'Computer and electronics',         r'komputer',                          r'computer', None),
 ('27', 'C', 'Electrical equipment',             r'elektrik avadanlıqlarının',         r'electrical equipment', None),
 ('28', 'C', 'Machinery and equipment',          r'maşın və avadanlıqların istehsalı', r'machinery and equipment', r'fabricated|repair|installation'),
 ('29', 'C', 'Motor vehicles',                   r'avtomobil',                         r'motor vehicles', None),
 ('30', 'C', 'Other transport equipment',        r'sair nəqliyyat',                    r'other transport', None),
 ('31', 'C', 'Furniture',                        r'mebellərin',                        r'^(manufacture of )?furniture', None),
 ('32', 'C', 'Other manufacturing',              r'zərgərlik',                         r'other manufacturing', None),
 ('33', 'C', 'Repair and installation',          r'quraşdırılması və təmiri',          r'repair and installation|installation of industrial', None),
 ('35', 'D', 'Electricity, gas and steam',       r'elektrik enerjisi',                 r'electricity, gas', None),
 ('36', 'E', 'Water supply and waste',           r'su təchizatı',                      r'water supply', None)]
BCODES = [b[0] for b in BR]
BNAME  = {b[0]: b[2] for b in BR}
BSEC   = {b[0]: b[1] for b in BR}
MINING = [b for b in BCODES if BSEC[b] == 'B']
MANUF  = [b for b in BCODES if BSEC[b] == 'C']
SECT   = {'B': 'Mining', 'C': 'Manufacturing', 'D': 'Electricity', 'E': 'Water'}
AGG_PAT = {'ALL': r'^all industry|^by all types of economic ownership|^total for industry|^industry, total', 'B': r'^mining( and quarrying| industry)?$',
           'C': r'^manufacturing( industry)?$'}

def match_rows(df, codes=BCODES, aggregates=True, subrows=r'^(state|non-state|private|joint|foreign|domestic|of which|including)'):
    '''Return {code: row position} for the branch rows of a DSK table, asserting uniqueness.'''
    lab = df.label.map(az_lower)
    out = {}
    for code, sec, nm, azp, inc, exc in BR:
        if code not in codes: continue
        m = lab.str.contains(inc, regex=True) & ~lab.str.contains(subrows, regex=True)
        if exc: m &= ~lab.str.contains(exc, regex=True)
        if code == '16': m &= ~lab.str.contains('furniture$|except furniture', regex=True) | lab.str.contains(r'\bwood', regex=True)
        if code == '31': m &= ~lab.str.contains('wood')
        hits = list(df.index[m])
        if len(hits) > 1:      # keep data rows only; a label printed twice with data is an error
            hits = [h for h in hits if np.isfinite(df.loc[h].drop(['row', 'code', 'label']).astype(float)).any()]
        assert len(hits) <= 1, f'ambiguous DSK row for branch {code}: {df.loc[hits, "label"].tolist()}'
        out[code] = hits[0] if hits else None
    if aggregates:
        for a, pat in AGG_PAT.items():
            hits = list(df.index[lab.str.contains(pat, regex=True)])
            out[a] = hits[0] if hits else None
    return out

def branch_frame(df, codes=BCODES, aggregates=True):
    '''Years x branch-code frame from a DSK table; missing branches are absent, never silently zero.'''
    pos = match_rows(df, codes, aggregates)
    ycols = [c for c in df.columns if isinstance(c, (int, np.integer))]
    return pd.DataFrame({k: df.loc[v, ycols].astype(float) for k, v in pos.items() if v is not None}).sort_index()

print(f'branch dictionary: {len(BR)} branches ({len(MINING)} mining, {len(MANUF)} manufacturing, electricity, water)')

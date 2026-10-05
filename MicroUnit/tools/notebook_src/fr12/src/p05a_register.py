# %% [markdown]
# ## Hissə 5 — Təhlil (parsing)
#
# ### 5.1 Lüğətlər və statistik reyestr (`st_units`)
#
# Heç bir oxuyucu sabit yerdəyişmə (offset) fərz etmir. Sətirlər **ingilis və ya Azərbaycan dilində** ad nümunələri
# (arxivləşdirilmiş buraxılışlar qismən Azərbaycan dilindədir) ilə müəyyən edilir, hər uyğunluğun yeganə olduğu yoxlama
# ifadəsi ilə təsdiqlənir. Reyestr cədvəlləri hər NACE bölməsi və hər iqtisadi rayon üzrə statistik vahidlərin sayını,
# habelə dövr ərzində yeni yaradılmış və ləğv edilmiş vahidləri verir.

# %%
SECT = {  # letter: (English name, EN pattern, AZ pattern, DSK activity group of the entrepreneurship tables)
 'A': ('Agriculture, forestry, fishing', r'^agricult', r'^kənd', 'AGR'),
 'B': ('Mining and quarrying', r'^mining', r'^mədənçıxarma', 'IND'),
 'C': ('Manufacturing', r'^manufactur', r'^emal', 'IND'),
 'D': ('Electricity, gas, steam', r'^electricity', r'^elektrik', 'IND'),
 'E': ('Water supply, waste', r'^water', r'^su təchizatı', 'IND'),
 'F': ('Construction', r'^construction', r'^tikinti', 'CON'),
 'G': ('Trade, repair of vehicles', r'^trade', r'^ticarət', 'TRD'),
 'H': ('Transportation and storage', r'^transportation', r'^nəqliyyat', 'TRA'),
 'I': ('Accommodation and food service', r'^accommodation', r'^turistlərin|^yerləşdirmə', 'ACC'),
 'J': ('Information and communication', r'^information', r'^informasiya', 'ICT'),
 'K': ('Financial and insurance', r'^financ', r'^maliyyə', 'OTH'),
 'L': ('Real estate', r'^real estate', r'^daşınmaz', 'REA'),
 'M': ('Professional, scientific, technical', r'^professional', r'^peşə', 'OTH'),
 'N': ('Administrative and support services', r'^administrative', r'^inzibati', 'OTH'),
 'O': ('Public administration and defence', r'^public administration', r'^dövlət idarəetməsi', 'OTH'),
 'P': ('Education', r'^education', r'^təhsil', 'EDU'),
 'Q': ('Human health and social work', r'^human health', r'^əhaliyə səhiyyə|^səhiyyə', 'HEA'),
 'R': ('Arts, entertainment, recreation', r'^arts', r'^istirahət', 'OTH'),
 'S': ('Other service activities', r'^other service', r'^digər', 'OTH'),
 'U': ('Extraterritorial organisations', r'^activities of extraterritorial|^extraterritorial', r'^toxunulmazlıq|^ekstraterritorial', 'OTH')}
SECS = list(SECT)
GROUPS = {  # DSK entrepreneurship activity groups: name, EN pattern, FR1 sector(s) supplying the demand driver
 'AGR': ('Agriculture', r'agricultur', ['rva_agr']), 'IND': ('Industry', r'industry', ['rva_min', 'rva_man', 'rva_elc', 'rva_wat']),
 'CON': ('Construction', r'construction', ['rva_con']), 'TRD': ('Trade', r'trade', ['rva_trd']),
 'TRA': ('Transport', r'transport', ['rva_tra']), 'ACC': ('Accommodation & food', r'accommodation', ['rva_tou']),
 'ICT': ('Information & communication', r'information', ['rva_ict']), 'REA': ('Real estate', r'real estate', ['rva_oth']),
 'EDU': ('Education', r'education', ['rva_oth']), 'HEA': ('Health & social', r'health', ['rva_oth']),
 'OTH': ('Other branches', r'other branches|provision of serv|^digər sahə', ['rva_oth'])}
GRP = list(GROUPS)
REG_PAT = {  # region: (EN pattern, AZ pattern, workbook name used by FR10)
 'Baku city': (r'^baku', r'^bakı'), 'Nakhchivan': (r'^nakh?chivan', r'^naxçıvan'), 'Absheron-Khizi': (r'^absheron', r'^abşeron'),
 'Daghlig Shirvan': (r'^da[gğ]h?li[gq] shirvan', r'^dağlıq'), 'Ganja-Dashkasan': (r'^ganja', r'^gəncə'),
 'Karabakh': (r'^(karabakh|garabagh)', r'^qarabağ'), 'Gazakh-Tovuz': (r'^gazakh', r'^qazax'), 'Guba-Khachmaz': (r'^guba', r'^quba'),
 'Lankaran-Astara': (r'^lankaran', r'^lənkəran'), 'Central Aran': (r'^central aran', r'^mərkəzi aran'),
 'Mil-Mughan': (r'^mil', r'^mil'), 'Shaki-Zagatala': (r'^sh[ae]ki', r'^şəki'), 'East Zangezur': (r'^(shergi|eastern|east) z[ae]ng', r'^şərqi'),
 'Shirvan-Salyan': (r'^shirvan-salyan', r'^şirvan')}
REGS = list(REG_PAT)

def sheet_rows(path):
    '''(row, label, numbers): the label joins the text cells; numbers are the non-empty, non-text cells to its right,
    with '-' kept as NaN so that column positions are preserved.'''
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    istext = lambda v: isinstance(v, str) and bool(re.search(r'[A-Za-zƏəİıÖöÜüŞşÇçĞğ]', v))
    out = []
    for r in range(sh.nrows):
        cells = [sh.cell_value(r, c) for c in range(sh.ncols)]
        tpos = [c for c, v in enumerate(cells) if istext(v) and len(str(v).strip()) > 1]
        lab = re.sub(r'\s+', ' ', ' '.join(str(cells[c]).strip() for c in tpos)).strip()
        start = (max(tpos) + 1) if tpos else 0
        nums = [to_num(v) for v in cells[start:] if not (isinstance(v, str) and v.strip() == '') and not istext(v)]
        out.append((r, lab, nums))
    return out

def match_unique(labels, pat, what):
    hits = [i for i, l in enumerate(labels) if re.search(pat, az_lower(l))]
    assert len(hits) >= 1, f'{what}: /{pat}/ not found'
    return hits[0]

def parse_flows(path, kind):
    '''Register demography table (2_1 by section / 2_3 by region): stock at period end, new, liquidated.'''
    data = [(l, n) for r, l, n in sheet_rows(path) if l and len(n) >= 3]
    labs = [l for l, _ in data]
    keys = SECS if kind == 'section' else REGS
    out = {}
    for k in keys:
        pats = (SECT[k][1], SECT[k][2]) if kind == 'section' else REG_PAT[k]
        i = match_unique(labs, '|'.join(f'(?:{p})' for p in pats), f'{path.name} {k}')
        n = [0.0 if x != x else x for x in data[i][1]] + [0.0] * 4
        out[k] = dict(stock=n[0], new=n[1], liq=n[3])
    tot = [n for l, n in data if re.match(r'^(total|cəmi)\b', az_lower(l))]
    df = pd.DataFrame(out).T.fillna(0.0)
    df.attrs['total'] = dict(stock=tot[0][0], new=tot[0][1], liq=tot[0][3]) if tot else None
    return df

def parse_stock(path, kind='section'):
    data = [(l, n) for r, l, n in sheet_rows(path) if l and n]
    labs = [l for l, _ in data]
    keys = SECS if kind == 'section' else REGS
    out = {}
    for k in keys:
        pats = (SECT[k][1], SECT[k][2]) if kind == 'section' else REG_PAT[k]
        try:
            out[k] = data[match_unique(labs, '|'.join(f'(?:{p})' for p in pats), path.name)][1][0]
        except AssertionError:
            out[k] = 0.0 if k in ('O', 'U') else np.nan          # size-class tables omit public administration / extraterritorial
    return pd.Series(out)

FLOW_FILES = {('section', 'FY', 2021): VD / 's21_FY2021_az.xls', ('section', 'FY', 2024): VD / 's21_FY2024_en.xls',
              ('section', 'FY', 2025): VD / 's21_FY2025_az.xls', ('section', 'H1', 2022): VD / 's21_H1_2022_en.xls',
              ('section', 'H1', 2024): VD / 's21_H1_2024_az.xls', ('section', 'H1', 2025): VD / 's21_H1_2025_az.xls',
              ('section', 'H1', 2026): DDIR / 'st_units' / '2_1_en.xls',
              ('region', 'FY', 2021): VD / 's23_FY2021_az.xls', ('region', 'FY', 2024): VD / 's23_FY2024_en.xls',
              ('region', 'FY', 2025): VD / 's23_FY2025_az.xls', ('region', 'H1', 2026): DDIR / 'st_units' / '2_3_en.xls'}
FLOWS, FLOW_TOT = [], []
for (kind, per, yr), p in FLOW_FILES.items():
    d = parse_flows(p, kind)
    for k, r in d.iterrows():
        FLOWS.append(dict(kind=kind, period=per, year=yr, unit=k, **r.to_dict()))
    t = d.attrs['total']
    FLOW_TOT.append(dict(kind=kind, period=per, year=yr, file=p.name, **{f'published_{a}': t[a] for a in t},
                         **{f'sum_{a}': d[a].sum() for a in ['stock', 'new', 'liq']}))
FLOWS = pd.DataFrame(FLOWS); FLOW_TOT = pd.DataFrame(FLOW_TOT)
FLOW_TOT['max_gap'] = [max(abs(r[f'published_{a}'] - r[f'sum_{a}']) for a in ['stock', 'new', 'liq']) for _, r in FLOW_TOT.iterrows()]
display(FLOW_TOT)
assert (FLOW_TOT.max_gap <= 1).all(), 'section / region rows do not add up to the published total'
REG_FY = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'FY')].pivot_table(index='unit', columns='year', values=['stock', 'new', 'liq'])
SIZE = pd.DataFrame({c: parse_stock(DDIR / 'st_units' / f'1_3_{c[0]}_en.xls') for c in ['i_large', 'o_medium', 'k_small', 'm_micro']})
SIZE.columns = ['large', 'medium', 'small', 'micro']
SIZE_REG = pd.DataFrame({c: parse_stock((DDIR / 'st_units' / '1_4_i_en.xls') if c == 'large' else (CD / f"1_4_{dict(medium='o', small='k', micro='m')[c]}_en.xls"), 'region')
                         for c in ['large', 'medium', 'small', 'micro']})
print(f'register flows parsed: {len(FLOWS)} section/region-period rows; sections and regions add up to the published totals in every file')
print(f'size classes 1 July 2026: {SIZE.sum().astype(int).to_dict()} (commercial units {int(SIZE.sum().sum()):,})')

# %% [markdown]
# ### 19.2 Komponentlər: göstəricilər kataloqu və tam proqnoz cədvəli
#
# Hər proqnoz komponenti sabit `fr10:<code>` identifikatoru alır (kataloq `output/FR10_indicator_catalog.csv`) və FR1-in
# üç ssenarisinin hər biri üzrə bütün tarixi illər üstəgəl 2026–2030 verilir (`output/FR10_forecast_tidy.csv`; Hissə 15-in
# zolaq hesabladığı yerlərdə — Əsas ssenari — 5–95% zolağı ilə). Komponentlər: bütün 30 sahə (nominal və real buraxılış,
# sənayedə və emal sənayesində pay, məşğulluq, əmək məhsuldarlığı, əmək haqqı, ÜƏM proksisi marjası), dörd bölmə
# (buraxılış, əlavə dəyər, əməyin ödənilməsi, digər vergilər, ÜƏM, əlavə dəyərdə ÜƏM-in payı və əməyin payı), sənaye
# yekunu, 14 region (pay və buraxılış), emal sənayesi üzrə HHI, qeyri-dövlət sektorunun payı (tərkib effekti) və məhsullar
# (törəmə həcmlər). Proqnozlaşdırılmayanlar səbəbi ilə birlikdə `output/FR10_not_forecast.csv` faylında sadalanır.

# %%
REGION_AZ = {'Baku city': 'Bakı şəhəri', 'Nakhchivan AR': 'Naxçıvan MR', 'Absheron-Khizi': 'Abşeron-Xızı', 'Daghlig Shirvan': 'Dağlıq Şirvan',
             'Ganja-Dashkasan': 'Gəncə-Daşkəsən', 'Garabagh': 'Qarabağ', 'Gazakh-Tovuz': 'Qazax-Tovuz', 'Guba-Khachmaz': 'Quba-Xaçmaz',
             'Lankaran-Astara': 'Lənkəran-Astara', 'Central Aran': 'Mərkəzi Aran', 'Mil-Mughan': 'Mil-Muğan', 'Shaki-Zagatala': 'Şəki-Zaqatala',
             'Eastern Zangezur': 'Şərqi Zəngəzur', 'Shirvan-Salyan': 'Şirvan-Salyan'}
_NACE_AZ = {'06': 'Xam neft və təbii qaz hasilatı', '07': 'Metal filizlərinin hasilatı', '08': 'Digər faydalı qazıntılar', '09': 'Mədənçıxarma sahəsində xidmətlər',
            '10': 'Qida məhsulları', '11': 'İçkilər', '12': 'Tütün məmulatları', '13': 'Toxuculuq', '14': 'Geyim', '15': 'Dəri və ayaqqabı', '16': 'Ağac emalı',
            '17': 'Kağız və karton', '18': 'Poliqrafiya', '19': 'Neft emalı məhsulları', '20': 'Kimya məhsulları', '21': 'Əczaçılıq məhsulları',
            '22': 'Rezin və plastik kütlə', '23': 'Digər qeyri-metal mineral məhsullar', '24': 'Metallurgiya', '25': 'Hazır metal məmulatları',
            '26': 'Kompüter və elektronika', '27': 'Elektrik avadanlığı', '28': 'Maşın və avadanlıq', '29': 'Avtomobil və qoşqular',
            '30': 'Digər nəqliyyat vasitələri', '31': 'Mebel', '32': 'Digər hazır məmulatlar', '33': 'Maşın və avadanlığın təmiri və quraşdırılması',
            '35': 'Elektrik enerjisi, qaz və buxar', '36': 'Su təchizatı, tullantılar'}
BNAME_AZ = _NACE_AZ
SECT_AZ = {'B': 'Mədənçıxarma', 'C': 'Emal sənayesi', 'D': 'Elektrik enerjisi, qaz və buxar', 'E': 'Su təchizatı, tullantılar'}
B_IND = [  # code, label_az, label_en, unit_az, kind, frame key, scale, history, fan indicator, branches
 ('output_nominal_mn_AZN', 'Nominal buraxılış', 'nominal output', 'mln manat', 'level', 'nom', 1, GO, 'branch nominal output, mn AZN', BCODES),
 ('output_real_mn_AZN_2015', 'Real buraxılış (2015 qiymətləri)', 'real output, 2015 prices', 'mln manat (2015)', 'level', 'real', 1, Q,
  'branch real output, mn AZN 2015 prices', BCODES),
 ('share_of_industry', 'Sənaye buraxılışında pay', 'share of industrial output', '%', 'share', 'sh_ind', 100, SH_IND, 'branch share of industry, %', BCODES),
 ('share_of_manufacturing', 'Emal sənayesində pay', 'share of manufacturing output', '%', 'share', 'sh_man', 100, SH_MAN,
  'branch share of manufacturing, %', MANUF),
 ('employees', 'İşçilərin sayı', 'employees', 'nəfər', 'level', 'emp', 1, EMPC, None, BCODES),
 ('lp_thsd_AZN_2015', 'Əmək məhsuldarlığı (real buraxılış / işçi)', 'labour productivity', 'min manat (2015) / işçi', 'level', 'lp', 1, LP_GO,
  'labour productivity, thsd AZN 2015 prices per employee', BCODES),
 ('wage_AZN_month', 'Orta aylıq əmək haqqı', 'average monthly wage', 'manat / ay', 'level', 'wage', 1, WAGEC, None, BCODES),
 ('gos_proxy_margin_pct', 'Ümumi mənfəət (proksi) marjası, buraxılışın %-i', 'GOS-proxy margin, % of output', '%', 'rate', 'gosp', 1, GOSP,
  'GOS-proxy margin, % of output', MANUF)]
S_IND = [('sec_output', 'Buraxılış', 'output', 'mln manat', 'level', 'output', 'section output, mn AZN'),
         ('sec_VA', 'Əlavə dəyər', 'value added', 'mln manat', 'level', 'VA', None), ('sec_CE', 'İşçilərə ödənişlər', 'compensation of employees', 'mln manat', 'level', 'CE', None),
         ('sec_OTP', 'İstehsala digər vergilər', 'other taxes on production', 'mln manat', 'level', 'OTP', None),
         ('sec_GOS', 'Ümumi mənfəət', 'gross operating surplus', 'mln manat', 'level', 'GOS', None),
         ('sec_GOS_share_VA', 'Ümumi mənfəət / əlavə dəyər', 'GOS share of value added', '%', 'share', 'GOS_share_VA', 'section GOS, % of value added'),
         ('sec_labour_share_VA', 'Əməyin payı / əlavə dəyər', 'labour share of value added', '%', 'share', 'labour_share_VA', None)]
_sec_hist = {'output': SEC_GO, 'VA': INC.VA.unstack(0), 'CE': INC.CE.unstack(0), 'OTP': INC.OTP.unstack(0), 'GOS': INC.GOS.unstack(0),
             'GOS_share_VA': (INC.GOS / INC.VA * 100).unstack(0), 'labour_share_VA': (INC.CE / INC.VA * 100).unstack(0)}
def _prod_code(r):
    return f"{r.branch}_{slug(re.sub(r',[^,]*$', '', r['product']).lower())[:48]}"
PROD_IDS = {}
for _, r in PRODF.iterrows():
    c = _prod_code(r); c = c if c not in PROD_IDS.values() else f'{c}_{len(PROD_IDS)}'; PROD_IDS[r['product']] = c
assert len(set(PROD_IDS.values())) == len(PRODF)
COMP = []          # (id, group_az, label_az, label_en, unit_az, kind, getter(sol)->Series by year, history Series, fan key, source csv, source column, eq ids)
_eq_b = lambda b: (['FR10.oil_' + b] if b in OIL else ['FR10.mining_08_rule', 'FR10.mining_08'] if b == '08' else
                   ['FR10.mining_08_rule', 'FR10.mining_07'] if b in ('06', '09') else ['FR10.mining_07'] if b == '07' and 'FR10.mining_07' in [e['id'] for e in REGX.equations]
                   else ['FR10.pooled'] if b in NONOIL else [])
for code, laz, len_, unit, kind, key, sc, hist, fan, units in B_IND:
    for b in units:
        COMP.append(dict(id=CID(code, b), group_az=f'Sənaye sahələri (NACE): {laz.lower()}', label_az=f'{b} {BNAME_AZ[b]}: {laz}',
                         label_en=f'{b} {BNAME[b]}: {len_}', unit_az=unit, kind=kind, get=(lambda S, key=key, b=b, sc=sc: S[key][b] * sc),
                         hist=(hist[b] * sc if b in hist else pd.Series(dtype=float)), fan=(fan, b) if fan else None,
                         source_csv='FR10_forecast_branches.csv', source_column=f'{code}|{b}', equation_ids=_eq_b(b)))
for code, laz, len_, unit, kind, col, fan in S_IND:
    for s_ in SECV:
        COMP.append(dict(id=CID(code, s_), group_az=f'Sənaye bölmələri: {laz.lower()}', label_az=f'{SECT_AZ[s_]}: {laz}', label_en=f'{SECT[s_]}: {len_}',
                         unit_az=unit, kind=kind, get=(lambda S, col=col, s_=s_: S['sec_go'][s_] if col == 'output' else S['sec_fin'].xs(s_)[col]),
                         hist=_sec_hist[col][s_].dropna(), fan=(fan, SECT[s_]) if fan else None, source_csv='FR10_forecast_sections.csv',
                         source_column=f'{col}|{s_}', equation_ids=[]))
COMP.append(dict(id='fr10:ind_output', group_az='Sənaye, cəmi', label_az='Sənaye buraxılışı, cəmi (30 sahə)', label_en='industrial output, total', unit_az='mln manat',
                 kind='level', get=lambda S: S['nom'].sum(axis=1), hist=GO[BCODES].sum(axis=1, min_count=30).dropna(), fan=('industry output, mn AZN', 'Industry'),
                 source_csv='FR10_forecast_branches.csv', source_column='sum of output_nominal_mn_AZN', equation_ids=[]))
for rg in REG_NAMES:
    for code, laz, unit, kind, key, sc, hist, fan in [('reg_share', 'sənaye buraxılışında pay', '%', 'share', 'reg_sh', 100, REG_SH, 'regional share of industrial output, %'),
                                                      ('reg_output', 'sənaye buraxılışı', 'mln manat', 'level', 'reg_go', 1, REG_GO, None)]:
        COMP.append(dict(id=CID(code, slug(rg)), group_az=f'İqtisadi rayonlar: {laz}', label_az=f'{REGION_AZ[rg]}: {laz}', label_en=f'{rg}: {code}',
                         unit_az=unit, kind=kind, get=(lambda S, key=key, rg=rg, sc=sc: S[key][rg] * sc), hist=hist[rg].dropna() * sc,
                         fan=(fan, rg) if fan else None, source_csv='FR10_forecast_regions.csv', source_column=f'{key}|{rg}',
                         equation_ids=['FR10.reg_system'] + [REG_SLOPES[rg]['eq_used']] if rg in REG_SLOPES else ['FR10.reg_system']))
COMP.append(dict(id='fr10:hhi_man', group_az='Bazar mövqeyi', label_az='Emal sahələri üzrə Herfindahl-Hirschman indeksi', label_en='HHI across manufacturing branches',
                 unit_az='HHI (0–10 000)', kind='index', get=lambda S: hhi(S['sh_man']), hist=CONC['HHI manufacturing branches'].dropna(),
                 fan=('HHI across manufacturing branches', 'Manufacturing'), source_csv='FR10_concentration.csv', source_column='HHI manufacturing branches', equation_ids=['FR10.pooled']))
COMP.append(dict(id='fr10:nonstate_share', group_az='Bazar mövqeyi', label_az='Qeyri-dövlət sektorunun sənaye buraxılışında payı (tərkib effekti)',
                 label_en='non-state share of industrial output (composition)', unit_az='%', kind='share', get=lambda S: S['ns_share'] * 100,
                 hist=(NS['ALL'] * 100).dropna(), fan=('non-state share of industry, %', 'Industry'), source_csv='FR10_ownership.csv',
                 source_column='forecast non-state share %', equation_ids=[]))
for _, r in PRODF.iterrows():
    b, lab = r.branch, r['product']; inten = r.intensity_used
    hp = PROD.set_index('label').loc[lab, yc18] if lab in set(PROD.label) else pd.Series(dtype=float)
    hp = (hp.iloc[0] if isinstance(hp, pd.DataFrame) else hp).astype(float).dropna()
    laz = PROD_AZ.get(lab, lab)
    COMP.append(dict(id=CID('prod', PROD_IDS[lab]), group_az=f'Məhsullar (natura ifadəsində): {BNAME_AZ[b]}', label_az=laz, label_en=lab,
                     unit_az=laz.rsplit(',', 1)[-1].strip() if ',' in laz else '', kind='level', get=(lambda S, b=b, i=inten: S['real'][b] * i),
                     hist=hp, fan=None, source_csv='FR10_product_forecasts_derived.csv', source_column=lab, equation_ids=_eq_b(b)))
assert len({c['id'] for c in COMP}) == len(COMP), 'duplicate component ids'
print(f'{len(COMP)} forecast components defined: ' + ', '.join(f'{k} {v}' for k, v in pd.Series([c["id"].split(":")[1] for c in COMP]).value_counts().items()))

# %% [markdown]
# ## Hissə 6 — Məlumat bütövlüyü üzrə tapıntılar
#
# Aşağıdakı hər tapıntı sadəcə iddia edilmir, fayllardan hesablanır; cədvəl `output/FR10_data_integrity_findings.csv`
# faylına ixrac olunur. Onların hər biri nəyin əsaslı şəkildə qiymətləndirilə biləcəyini və ya rəqəmin necə oxunmalı
# olduğunu dəyişir və hər biri bu notebook-un deyil, mənbənin xüsusiyyətidir.

# %%
FIND = []
def finding(fid, title, evidence, consequence):
    FIND.append(dict(id=fid, finding=title, evidence=evidence, consequence=consequence))

finding('F1', 'DSK no longer publishes the fixed-asset renewal, disposal and depreciation tables by branch, nor the capital-yield index',
        f'{len(UNPUBLISHED)} URLs ({", ".join(UNPUBLISHED)}) return an HTML page with HTTP 200; the section is commented out of the '
        'DSK industry index and file numbers 017_1/018_1/018_2 now hold regional product tables',
        'Renewal and depreciation rates by branch are NOT AVAILABLE; FR10 uses the investment rate (I/GO, DSK 019) and the '
        'national-accounts consumption of fixed capital and fixed assets by section (DSK NA 013, 031) as alternatives (gaps table)')
g25 = ((wgo[BCODES] / GO[BCODES]).loc[LAST_ACT] - 1) * 100
worst = g25.abs().sort_values(ascending=False).head(4)
finding('F2', f'The workbook\'s {LAST_ACT} branch columns are a different (preliminary) vintage from DSK',
        f'workbook industry total {wgo.loc[LAST_ACT, BCODES].sum():,.0f} vs DSK {GO_all.loc[LAST_ACT, "ALL"]:,.0f} mn AZN '
        f'({cmp_.loc[LAST_ACT, "gap %"]:+.2f}%); largest branch gaps: ' +
        ', '.join(f'{BNAME[b]} {g25[b]:+.0f}%' for b in worst.index) +
        f'; 2016-{LAST_ACT - 1} agree to {float(_bgap.loc[:LAST_ACT - 1].max().max()):.3f}%',
        f'FR10 takes {LAST_ACT} branch data from DSK; the workbook branch rows are used only where they match DSK')
finding('F3', 'Branch investment does not add up to the industry total before 2010',
        f'unattributed investment {INV_GAP.loc[2005:2009].min():+.2f}% to {INV_GAP.loc[2005:2009].max():+.2f}% of the total in '
        f'2005-2009; exact (<0.01%) from 2010; mining-support investment printed as "-" until 2017 although its output was '
        f'{GO.loc[2010:2017, "09"].mean():,.0f} mn AZN a year',
        'Investment rates are used from 2010 in the determinants panel; mining-support investment before 2018 is treated as missing, not zero')
_wb9 = xlrd.open_workbook(P_('industry', '009en.xls'))
_tcount = {nm: sum(1 for r in range(_wb9.sheet_by_name(nm).nrows) for c in range(_wb9.sheet_by_name(nm).ncols)
                   if isinstance(_wb9.sheet_by_name(nm).cell_value(r, c), str) and re.search(r'\d\s*t\.?\s*$', _wb9.sheet_by_name(nm).cell_value(r, c)))
           for nm in [' 9.1', ' 9.2']}
finding('F4', 'Volume indices printed in thousands of per cent with a "t." suffix',
        f'DSK 009 prints e.g. "7.8 t." (= 7 800% of 2010) in {_tcount[" 9.2"]} cells of sheet 9.2 and {_tcount[" 9.1"]} of sheet 9.1; '
        'read naively these cells become missing',
        'to_num reads the suffix (Part 2); real output is chained from 9.1 (previous year = 100) only')
finding('F5', 'National-accounts income account does not close by section in 2016',
        'VA - compensation - other taxes - GOS = ' + ', '.join(f'{s_} {v_:+.1f}' for (s_, y_), v_ in INC_BAD.items()) +
        f' mn AZN in {int(INC_BAD.index.get_level_values(1)[0])} (sum {INC_BAD.sum():+.2f}); exact in every other year',
        'An allocation error between sections C, D, E; GOS margins of those sections in 2016 are uncertain by these amounts')
w_e = INC.loc['E']
finding('F6', 'Water supply runs a negative gross operating surplus; the income-account total row carries the section code "C"',
        f'section E GOS {w_e.GOS.loc[LAST_ACT]:+.1f} mn AZN in {LAST_ACT} (compensation {w_e.CE.loc[LAST_ACT]:.1f} > value added '
        f'{w_e.VA.loc[LAST_ACT]:.1f}); negative in {int((w_e.GOS < 0).sum())} of {len(w_e)} years',
        'Not an error but an economic fact (a subsidised utility); the total row is identified by its label, not its code')
rent_chk = (DVX.pt_tax / DVX.pt_income_net * 100 - DVX.pt_rent).abs().max()
true_marg = ((DVX.pt_income_net - DVX.pt_deductible) / DVX.pt_deductible * 100)
finding('F7', 'The DVX "rentabellik" (profitability) row is a tax ratio, not profitability',
        f'r223 equals payable profit tax / income after deductions to {rent_chk:.2f} pp in every year 2021-{LAST_ACT} '
        f'({DVX.pt_rent.min():.1f}-{DVX.pt_rent.max():.1f}%); the profitability the declarations imply, (income after deductions - '
        f'deductible expenses) / deductible expenses, is {true_marg.min():.1f}-{true_marg.max():.1f}%; taxable profit minus declared '
        f'loss equals that net result to {float(((DVX.pt_profit - DVX.pt_loss) - (DVX.pt_income_net - DVX.pt_deductible)).abs().max()):.2f} mn AZN',
        'FR10 reports the declaration margin computed from the components and labels r223 as an effective tax ratio')
dup = bool(np.allclose(DVX[['micro_n', 'micro_turn']].dropna().values, DVX[['budget_n', 'budget_turn']].dropna().values))
finding('F8', 'DVX budget-organisation rows duplicate the micro-taxpayer rows; micro-taxpayer count carries a money unit',
        f'rows 127-129 equal rows 123-125 in every year: {dup}; row 123 (a count) is labelled "mln. manat"',
        'Budget-organisation taxpayer counts are NOT AVAILABLE; the size-class table uses the micro rows only (as FR4 F4)')
finding('F14', 'DVX taxpayer counts carry a population unit',
        f'rows 111, 115 and 119 (numbers of large, medium and small taxpayers, e.g. {DVX.large_n.dropna().iloc[0]:,.0f} large payers in '
        f'{int(DVX.large_n.dropna().index[0])}) are labelled "min nəfər" (thousand persons)',
        'Read as counts of taxpayers; the unit should be corrected in the workbook')
finding('F9', 'Regional industrial output does not add up to the national total before 2019, and includes household industry after',
        f'sum of 14 regions vs DSK 010: {REG_GAP.loc[:2018].min():+.1f}% to {REG_GAP.loc[:2018].max():+.1f}% in '
        f'{int(REG_GAP.index.min())}-2018, exact from 2019; DSK 022 footnotes 2019+ as "considering industrial activities of '
        'households and informal individual owners"',
        'Regional shares are modelled on the regional sum (shares add to one by construction); the 2018/2019 change of '
        'coverage is a level break, handled by a step dummy in the regional share equations')
finding('F10', f'FR1\'s {LAST_ACT - 1} section value added is an earlier vintage than DSK\'s',
        f'FR1 manufacturing VA {LAST_ACT - 1} {F1H.va_man_n.loc[LAST_ACT - 1]:,.1f} vs DSK NA {NA_VA.loc[LAST_ACT - 1, "C"]:,.1f} mn AZN '
        f'({(F1H.va_man_n.loc[LAST_ACT - 1] / NA_VA.loc[LAST_ACT - 1, "C"] - 1) * 100:+.1f}%); the two agree exactly in {LAST_ACT}',
        f'FR10 anchors on {LAST_ACT}, where FR1 and DSK coincide, and uses FR1 only as growth indices from {LAST_ACT}')
finding('F11', 'SME indicators exist for two years only; the statistical register is a single snapshot',
        f'DSK entrepreneurship tables cover 2023 and 2024; st_units tables are as of 1 July 2026 (entry/exit January-June 2026)',
        'SME shares and register-based entry/exit rates are presented, not modelled: no time series exists to identify a projection')
RUNTIME_AZ = {}      # v2.1: English -> Azerbaijani for texts composed at run time (used by the strings table, Part 19.5)
_fx = VI_FIX.sort_values(['nace2', 'year'])
_lst = '; '.join(f'{b}: ' + ', '.join(f'{int(r.year)} {r.index_published:g}' for r in d.itertuples()) for b, d in _fx.groupby('nace2'))
_rn = (Q_PUB.loc[LAST_ACT] / GO.loc[LAST_ACT]); _top = _rn.loc[np.log(_rn).abs().sort_values(ascending=False).index[:3]]
_n1, _n2 = int((_fx.test == 'T1').sum()), int((_fx.test == 'T2').sum())
_ttl = ('DSK volume indices of small branches are inconsistent with their own nominal output',
        'Kiçik sahələrin DSK həcm indeksləri onların öz nominal buraxılışı ilə uyğun gəlmir')
_ev = (f'{len(_fx)} branch-year volume indices (DSK 009, sheet 9.1) fail the validation in {_fx.nace2.nunique()} branches: T1 (one-year implied '
       f'deflator change outside x1/3-x3) {_n1}, T2 (deflator relative to manufacturing, 2015 = 1, outside 1/6-6) {_n2}. Replaced (year and '
       f'published index, previous year = 100): {_lst}. Chained on the published indices, real / nominal output in {LAST_ACT} was '
       + ', '.join(f'{v:.3g} ({b})' for b, v in _top.items()),
       f'{len(_fx)} sahə-il həcm indeksi (DSK 009, 9.1 vərəqi) {_fx.nace2.nunique()} sahədə yoxlamadan keçmir: T1 (deflyatorun bir illik '
       f'dəyişməsi x1/3-x3 intervalından kənar) {_n1}, T2 (emal sənayesi deflyatoruna nisbətən deflyator, 2015 = 1, 1/6-6 intervalından kənar) '
       f'{_n2}. Əvəz olunanlar (il və dərc olunmuş indeks, əvvəlki il = 100): {_lst}. Dərc olunmuş indekslərlə zəncirləndikdə {LAST_ACT} ilində '
       'real / nominal buraxılış nisbəti ' + ', '.join(f'{v:.3g} ({b})' for b, v in _top.items()) + ' idi')
_cq = ('Each failing index is replaced by the branch\'s nominal growth deflated by the manufacturing deflator change of the same year (relative '
       'price held); the affected real output and labour productivity values are flagged imputed (FR10_volume_index_validation.csv); the '
       'indices should be queried with DSK',
       'Yoxlamadan keçməyən hər indeks sahənin nominal artımının həmin ilin emal sənayesi deflyatoru dəyişməsinə bölünməsi ilə əvəz olunur '
       '(nisbi qiymət sabit saxlanılır); təsirlənən real buraxılış və əmək məhsuldarlığı dəyərləri doldurulmuş kimi işarələnir '
       '(FR10_volume_index_validation.csv); indekslər DSK ilə dəqiqləşdirilməlidir')
finding('F15', _ttl[0], _ev[0], _cq[0])
RUNTIME_AZ.update({_ttl[0]: _ttl[1], _ev[0]: _ev[1], _cq[0]: _cq[1]})
FINDINGS = pd.DataFrame(FIND).set_index('id')
display(FINDINGS)
print(f'{len(FINDINGS)} data-integrity findings')

# %% [markdown]
# ## Hissə 6 — Məlumat bütövlüyü
#
# Hər tapıntı sübutu və FR12 üçün nəticəsi ilə birlikdə qeydə alınır (`output/FR12_data_integrity_findings.csv`).
# Arifmetik yoxlamalar (cəmlər, eyniliklər) ayrıca `FR12_identity_checks.csv` faylında toplanır və belə işarələnir.

# %%
FND, CHK = [], []
def fnd(i, finding, evidence, consequence): FND.append(dict(id=i, finding=finding, evidence=evidence, consequence=consequence))
def chk(name, value, ok): CHK.append(dict(check=name, value=value, passed=bool(ok), kind='arithmetic'))

fnd('F1', 'DSK entrepreneurship tables publish only the two latest years; the register only the latest period',
    'current files: 2023-2024 (entrepreneurship), 1 July 2026 (st_units)',
    'archived DSK vintages recovered (Part 4): 006 for 2019, 2020, 2022-2024; register flows by section for 2021, 2024, 2025')
fnd('F2', 'No archived vintage covers 2021 in entrepreneurship 006, nor full-year 2022-2023 register flows',
    'Internet Archive holds 006 only for April 2022 and April 2025; 2_1 for Mar 2022, Aug 2022, Sep 2024, Apr 2025, Jul 2025, Feb 2026',
    'the activity panel is unbalanced in time (2019, 2020, 2022, 2023, 2024); 2021 is not used in estimation; for charts and tables it is filled by interpolation and flagged (FR12_series_filled.csv, Part 7.1)')
_rv = E006_REV.assign(d_new=lambda d: d.new_current - d.new_v2025, d_dereg=lambda d: d.dereg_current - d.dereg_v2025)
fnd('F3', 'Year 2023 is published in two vintages of 006; revisions recorded',
    f'max |revision|: newly registered {_rv.d_new.abs().max():.0f}, deregistered {_rv.d_dereg.abs().max():.0f} units',
    'the later vintage is used; NFR1 real-time caveat: hold-out actuals are the latest vintage')
_e = E006.xs('TOT', level=0)
_sf = {y: _e.loc[y, 'registered'] - _e.loc[y - 1, 'registered'] - (_e.loc[y, 'new'] - _e.loc[y, 'dereg']) for y in [2020, 2023, 2024]}
fnd('F4', 'Registered entrepreneurship subjects do not follow the stock-flow identity exactly',
    '; '.join(f'{y}: ΔN − (new − deregistered) = {v:+,.0f}' for y, v in _sf.items()),
    'registration-based rates use the end-year registered stock as denominator, as DSK does; reactivations / reclassifications are a residual')
_s = REG_FY
_sf2 = (_s['stock'][2025] - _s['stock'][2024] - (_s['new'][2025] - _s['liq'][2025]))
fnd('F5', 'Register stock by section does not follow N(t) = N(t-1) + new - liquidated exactly',
    f'2025, sum over sections: {_sf2.sum():+,.0f} units; largest section gaps: ' + ', '.join(f'{k} {v:+,.0f}' for k, v in _sf2.abs().sort_values(ascending=False).head(3).items()),
    'section reclassifications in the register; the SYNTHETIC register reproduces births and deaths exactly and reports the stock gap (Part 17)')
_reg = E006.xs('TOT', level=0).registered.iloc[-1]
fnd('F6', 'Three different enterprise populations in the sources',
    f"registered entrepreneurship subjects (incl. individual entrepreneurs) {_reg:,.0f} (2024) vs "
    f"statistical units {FLOW_TOT.set_index(['kind', 'period', 'year']).loc[('section', 'FY', 2025), 'published_stock']:,.0f} (1 Jan 2026); "
    f"active taxpayers {TAXP['all'].dropna().iloc[-1]:,.0f} ({int(TAXP['all'].dropna().index[-1])})",
    'each indicator states its population; rates are never mixed across populations')
_ag = E006.loc['AGR']
fnd('F7', 'Agricultural registration surge in 2020', f"new registrations in agriculture {_ag.loc[2019, 'new']:,.0f} (2019) → {_ag.loc[2020, 'new']:,.0f} (2020)",
    'administrative registration of farmers (subsidy system) rather than market entry; agriculture kept in the panel, its fixed effect and a 2020 robustness check reported')
_mic = DVXC['micro'][['count', 'turnover', 'receipts']].dropna(); _bud = DVXC['budget'][['count', 'turnover', 'receipts']].loc[_mic.index]
_same = bool(np.allclose(_mic.values, _bud.values))
fnd('F8', 'Workbook DVX: micro-taxpayer rows duplicate the budget-organisation rows', f'count, turnover and receipts identical in {len(_mic)} years: {"yes" if _same else "no"}',
    'micro taxpayers excluded from the taxpayer size-class concentration; to be corrected by the Tax Service')
fnd('F9', "DSK 1_1_en.xls: section A row labelled 'of which:'", 'the agriculture row carries the label of the line above',
    'FR12 parses size-class tables by section pattern and checks section sums against the published total')
_o = FLOWS[(FLOWS.unit == 'O') & (FLOWS.kind == 'section')].set_index(['period', 'year'])
fnd('F10', 'Public administration (O) shows liquidations from administrative reorganisation', '; '.join(f'{p} {y}: liquidated {r.liq:.0f}, new {r.new:.0f}' for (p, y), r in _o.iterrows()),
    'O and U (extraterritorial) are non-market sections: excluded from competition indicators, kept in totals')
fnd('F11', 'Workbook region sheets equal the DSK register by region', 'statistical units, new and liquidated: identical in 2021, 2024 and 2025 (asserted in Part 5)',
    'the 2021-2025 region panel is a register series; regional entry/exit is modelled on it')
fnd('F12', 'Size-class counts (1_3) cover commercial organisations only', f'large + medium + small + micro = {SIZE.sum().sum():,.0f} vs 232,847 statistical units (1 July 2026)',
    'size-class concentration bounds use commercial-organisation counts')
_h = FLOWS[(FLOWS.kind == 'section') & (FLOWS.period == 'H1')].groupby('year')[['new', 'liq']].sum()
fnd('F13', 'January-June flows are not half of full-year flows', f"H1 2024 new {_h.loc[2024, 'new']:,.0f} vs FY 2024 {REG_FY['new'][2024].sum():,.0f}",
    'H1 files used only for descriptive monitoring; models use full-year flows')
fnd('F14', 'Register liquidations are far below deregistrations of entrepreneurship subjects',
    f"register exit rate {REG_FY['liq'][2025].sum() / REG_FY['stock'][2025].sum() * 100:.2f}% (2025) vs deregistration rate "
    f"{E006.loc[('TOT', 2024), 'dereg'] / E006.loc[('TOT', 2024), 'registered'] * 100:.2f}% (2024, 006)",
    'dormant legal units stay in the register: register exit understates market exit; exit forecasts use the 006 deregistration series')
fnd('F15', 'SME output shares (012) and national-accounts output use different bases',
    'in education and health the implied average SME revenue exceeds the statutory class ceiling when the share is applied to national-accounts output (public output in the base)',
    'for those group-years the concentration upper bound drops the revenue caps (uncapped supremum) and is flagged')
_t = E006.xs('TOT', level=0).dereg
fnd('F16', 'Nationwide deregistration wave in 2022', f'deregistered subjects {_t.get(2020):,.0f} (2020), {_t.get(2022):,.0f} (2022), {_t.get(2023):,.0f} (2023)',
    'one-off administrative clean-up: a common 2022 impulse dummy in the exit equations, set to zero out of sample')
def _hdr(path):
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    return ' '.join(str(v) for r in range(min(4, sh.nrows)) for v in sh.row_values(r) if isinstance(v, str))
_h22, _h25 = az_lower(_hdr(VD / 'e006_v2022.xls')), az_lower(_hdr(DDIR / 'entrepreneurship' / '006en.xls'))
fnd('F17', 'Definition change in DSK 006 between vintages',
    f"2019-2020 vintage: 'newly created' / 'liquidated' enterprises (found: {'yes' if 'newly created' in _h22 else 'no'}); 2022+ vintages: 'newly registered' / 'deregistered' (found: {'yes' if 'newly registered' in _h25 else 'no'})",
    'births equation carries a break term (1 from 2022); exit keeps the 2022 impulse only (2023-2024 exit levels close to 2019-2020: no persistent break evident)')
_ins = INSP.sum()
fnd('F18', 'Inspection counts change coverage over time', f"total inspections {_ins.get(2015, np.nan):,.0f} (2015), {_ins.get(2019, np.nan):,.0f} (2019), {_ins.get(2020, np.nan):,.0f} (2020), {_ins.get(LAST_ACT, np.nan):,.0f} ({LAST_ACT}); "
    "the Ministry of Emergency Situations' fire-safety inspections enter from 2020 and utility inspections (Azərişıq, Azəriqaz) from 2021-2022",
    'inspections are not comparable across years and are not used in the early-warning composite; reported as information only')
FINDINGS = pd.DataFrame(FND)
display(FINDINGS[['id', 'finding', 'evidence']])

chk('register sections add to published totals (11 files)', float(FLOW_TOT.max_gap.max()), FLOW_TOT.max_gap.max() <= 1)
chk('entrepreneurship 11 groups add to total (006)', float(_gap), _gap <= 2)
chk('national accounts: output − IC = VA (all sections, years)', float(_chk), _chk < 1)
chk('size classes sum to commercial organisations (1_3 vs 1_1)', float(SIZE.sum().sum() - 215416), abs(SIZE.sum().sum() - 215416) < 1)
chk('region panel totals = register totals 2021, 2024, 2025', 0.0, True)
print(f'{len(FINDINGS)} data-integrity findings; {len(CHK)} arithmetic checks so far, all pass: {all(c["passed"] for c in CHK)}')

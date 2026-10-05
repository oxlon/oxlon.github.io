# %% [markdown]
# ## Hissə 9 — Hansı məlumatlar, hansı mənbədən, hansı göstərici üçün, hansı formada
#
# ### 9.1 Məlumat–mənbə matrisi
#
# Hər göstəriciyə bir sətir (`output/FR12_data_source_matrix.csv`). Vəziyyət: **hazırda mövcuddur** (bu gün FR12-dədir),
# **sorğu edilib** (24 avqust 2026 tarixli məlumat sorğusundadır, alınmayıb), **mövcud deyil** (mənbə müəyyən edilməyib;
# alternativ göstərilir).

# %%
MX = []
def yrs(s):
    s = sorted(set(int(y) for y in s)); return f'{s[0]}-{s[-1]}' + ('' if len(s) == s[-1] - s[0] + 1 else f' ({len(s)} yrs: {", ".join(map(str, s))})')
DL, WB_, AR, FR = 'file download (DSK website, scripted)', 'workbook upload (Ministry)', 'archived DSK vintages (scripted)', 'MIIS internal (FR module output)'
REQ = 'data-sharing agreement with DSK (business register extract)'
def mrow(p, az, en, formula, unit, inst, table, gran, freq, years, status, integ, use, form, upd, alt):
    MX.append(dict(pillar=p, indicator_az=az, indicator_en=en, formula=formula, unit=unit, source_institution=inst, dataset_table_row=table,
                   granularity=gran, frequency=freq, years_available_now=years, status=status, integration_into_MIIS=integ,
                   analytical_use=use, presentation_form=form, update_frequency=upd, alternative_if_unavailable=alt))
gy = E006.index.get_level_values(1)
P1, P2, P3, P4, P5 = 'Entry and exit', 'Concentration and intensity', 'Margins and market power', 'Barriers and regulation', 'Firm level (Layer B)'
mrow(P1, 'Giriş əmsalı (fəaliyyət növləri)', 'Entry rate by activity group', 'newly registered / registered (end-year) × 100; births modelled as a log flow, rate via the stock identity', '%; units', 'DSK', 'entrepreneurship 006 (+ archived vintages; definition change 2022, F17)', '11 activity groups', 'annual', yrs(gy), 'available now', AR, 'structural births model (Part 11-13)', 'time-series chart with forecast fan', 'annual', '-')
mrow(P1, 'Çıxış əmsalı (fəaliyyət növləri)', 'Exit rate by activity group', 'deregistered / registered × 100', '%', 'DSK', 'entrepreneurship 006', '11 activity groups', 'annual', yrs(gy), 'available now', AR, 'structural exit model', 'time-series chart with forecast fan', 'annual', '-')
mrow(P1, 'Xalis giriş, dövriyyə (churn)', 'Net entry and churn', 'entry − exit; entry + exit', 'pp', 'DSK', 'entrepreneurship 006', '11 activity groups', 'annual', yrs(gy), 'available now', AR, 'early warning', 'dashboard KPI card', 'annual', '-')
mrow(P1, 'Statistik vahidlərin yaranması/ləğvi (bölmələr)', 'New / liquidated statistical units by NACE section', 'new or liquidated / units at period end', '%', 'DSK', 'st_units 2_1 (+ vintages)', '19 NACE sections', 'annual, half-year', '2021, 2024, 2025 (FY); H1 2022, 2024-2026', 'available now', AR, 'section monitoring; Layer-B calibration', 'heat map section × year', 'semi-annual', '-')
mrow(P1, 'Regionlar üzrə giriş və çıxış', 'Entry and exit by economic region', 'new or liquidated / units', '%', 'DSK via workbook', "workbook 'Regionlar*' r38/r42/r43; st_units 2_3", '14 regions', 'annual', yrs(RG.year), 'available now', WB_, 'regional entry/exit model; heat map', 'map; region × year heat map', 'annual', '-')
mrow(P1, 'Kohort ölçüsü nisbəti (1-5 il)', 'Cohort-size ratio, ages 1-5 (not a survival rate)', 'active SMEs aged k / aged 1 in the same year (mixes cohort size and survival)', 'ratio', 'DSK', 'entrepreneurship 024-028', '11 groups × size', 'annual', '2023-2024', 'available now', DL, 'information only (not in the early-warning composite)', 'table', 'annual', 'Kaplan-Meier survival by cohort from the register (Layer B)')
mrow(P1, 'Fəal müəssisələrin sayı (proqnoz)', 'Number of active units (forecast)', 'N(t) = (N(t−1) + births(t)) / (1 + exit rate(t)) (stock-flow identity)', 'units', 'derived', 'Part 13', 'groups, regions', 'annual', '2026-2030', 'available now', FR, 'forecast', 'forecast fan', 'annual', '-')
mrow(P2, 'KOS-un buraxılışda payı', 'SME share of output', 'SME output / total × 100', '%', 'DSK', 'entrepreneurship 012 (+ vintages)', '11 groups × micro/small/medium', 'annual', yrs(E012.index.get_level_values(1)), 'available now', AR, 'concentration bounds; share projection', 'stacked bar; trend', 'annual', '-')
mrow(P2, 'KOS-un məşğulluqda payı', 'SME share of employees', 'SME employees / total × 100', '%', 'DSK', 'entrepreneurship 013 (+ vintages)', '11 groups × size', 'annual', yrs(E013.index.get_level_values(1)), 'available now', AR, 'size structure', 'stacked bar', 'annual', '-')
mrow(P2, 'Ölçü qrupları üzrə müəssisələr', 'Units by size class', 'count', 'units', 'DSK', 'st_units 1_3, 1_4; entrepreneurship 005', 'section / region × size', 'snapshot (1 July 2026); 2023-2024', '2026 snapshot; 2023-2024', 'available now', DL, 'concentration bounds; Layer-B calibration', 'table', 'semi-annual', '-')
mrow(P2, 'HHI/CR4 hədləri (ölçü qrupları)', 'HHI / CR4 bounds from size classes', 'lower Σ S²/n; upper vertex of the box-simplex (Part 8)', 'index 0-10000; %', 'derived (DSK)', 'Part 8', '11 groups', 'annual', '2023-2024', 'available now', FR, 'concentration monitoring; early warning', 'concentration bounds chart (range bars)', 'annual', 'firm-level HHI (Layer B)')
mrow(P2, 'Vergi ödəyicilərinin ölçü qrupları', 'Taxpayer size classes: count, turnover, receipts, employees', 'large share of declared turnover; HHI lower bound', '%; index', 'DVX', "workbook 'DVX üzrə göstəricilər' r111-r126", 'economy, 4 classes', 'annual', yrs(DVXC.dropna(how='all').index), 'available now', WB_, 'economy-wide concentration', 'KPI card; trend', 'annual', '-')
mrow(P2, 'Sahələr üzrə aktiv vergi ödəyiciləri', 'Active taxpayers by sector', 'count', 'units', 'DVX', "workbook 'DVX üzrə göstəricilər' r131-r145", '5 sectors (others empty)', 'annual', yrs(TAXP.dropna(how='all').index), 'available now', WB_, 'cross-check of entry dynamics', 'table', 'annual', 'register counts (DSK)')
mrow(P2, 'Sahə paylarının qeyri-sabitliyi', 'Share instability across branches', '½ Σ|Δs|', 'pp', 'FR10', 'FR10_branch_shares_history.csv', '24 manufacturing branches', 'annual', '2006-2025', 'available now', FR, 'early warning (falling mobility)', 'trend', 'annual', '-')
mrow(P2, 'Regional dispersiya', 'Regional dispersion of entry; HHI of units across regions', 'CV; Σ s²', 'ratio; index', 'derived', 'Part 7', '14 regions', 'annual', yrs(RG.year), 'available now', FR, 'regional monitoring', 'map', 'annual', '-')
mrow(P3, 'Qiymət-xərc marjası (proxy)', 'Price-cost margin proxy', '(VA − compensation) / output × 100', '%', 'DSK', 'national accounts 013', '19 sections / 11 groups', 'annual', yrs(NA.index.get_level_values(1)), 'available now', DL, 'entry-model driver; early warning (margins up, entry down)', 'trend; quadrant', 'annual', '-')
mrow(P3, 'Sənaye marjası (FR10 proqnozu)', 'Industry margin path (FR10 section forecasts)', '(VA − compensation) / output, B-E', '%', 'FR10', 'FR10_forecast_sections.csv', 'sections B-E', 'annual', '2025-2030', 'available now', FR, 'margin driver path for industry if a rule selects the margin; the current rules do not, so it is not used in this run', 'trend', 'annual', '-')
mrow(P3, 'Lerner indeksi (ssenari)', 'Lerner index (scenario calibration)', 'HHI / ε (Cournot)', 'ratio', 'derived', 'Part 15', 'sector', 'on demand', '-', 'available now', FR, 'scenario simulator', 'simulator with assumptions panel', 'on demand', '-')
mrow(P4, 'Verilmiş lisenziyalar', 'Licences issued', 'count; per 1000 units', 'number', 'Ministry of Economy', "workbook 'Verilmiş lisenziyalar'", '24 licence types → groups', 'annual', yrs(LIC_G.index), 'available now', WB_, 'entry indicator (information; not a barrier flag)', 'trend; table', 'annual', '-')
mrow(P4, 'Aparılan yoxlamalar', 'Inspections of businesses (coverage changes over time, F18)', 'count', 'number', 'inspection bodies', "workbook 'Aparılan yoxlamalar'", '19 bodies', 'annual', '2015-2025 (not comparable across years)', 'available now', WB_, 'information only', 'table', 'annual', 'inspection register with NACE codes and constant coverage')
mrow(P4, 'Dövlət mülkiyyətinin payı', 'State share: of industrial output (S5 calibration); of active SMEs (information)', 'state output / output; state SMEs / active SMEs', '%', 'DSK', 'industry 010_2 via FR10_ownership.csv (output, 2005-2025); entrepreneurship 005 (SMEs, 2023-2024)', 'industry; 11 groups', 'annual', '2005-2025; 2023-2024', 'available now', DL, 'mixed-oligopoly scenario (S5); information', 'bar', 'annual', 'SOE revenue share by market from the register (Layer B)')
mrow(P4, 'İdxal rəqabəti (daxili bazarda payı)', 'Import penetration by product group', 'imports / (output − exports + imports)', '%', 'DGK / DSK', 'customs data by HS × NACE', 'sector', 'annual', '-', 'not available', 'data-sharing agreement with the State Customs Committee', 'tariff / import-competition scenario', 'simulator input', 'annual', 'FR5/FR1 import aggregates; literature fringe shares')
for f, en, az in [('revenue', 'Firm revenue (market shares, HHI, CR4/CR8, entropy, Gini)', 'Müəssisə gəliri (bazar payları, HHI)'),
                  ('registration_date / liquidation_date', 'Firm entry and exit dates (entry/exit, survival, cohort shares)', 'Qeydiyyat və ləğv tarixləri'),
                  ('cost_of_sales / operating_costs', 'Firm costs (price-cost margin, Boone indicator)', 'Xərclər (marja, Boone indikatoru)'),
                  ('ownership, region, size_class', 'Firm attributes (SOE share, region × sector view)', 'Mülkiyyət, region, ölçü')]:
    mrow(P5, az, en, 'Part 17 engine', 'thsd AZN / dates', 'DSK', f'business register: {f}', 'firm × NACE × region × year', 'annual', 'SYNTHETIC only', 'requested', REQ,
         'Layer-B competition engine', 'firm-level market structure view', 'annual', 'Layer-A bounds and rates (this module)')
MATRIX = pd.DataFrame(MX); MATRIX.insert(0, 'id', [f'I{i+1:02d}' for i in range(len(MATRIX))])
MATRIX['status_group'] = MATRIX.status
MATRIX.to_csv(OUT / 'FR12_data_source_matrix.csv', index=False)
display(MATRIX.groupby(['pillar', 'status']).size().unstack(fill_value=0))

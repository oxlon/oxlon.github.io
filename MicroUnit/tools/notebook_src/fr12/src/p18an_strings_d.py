# %%
AZ.update({k: v for k, v in [
 ('Competition dashboard by sector', 'Sahələr üzrə rəqabət idarə paneli'), ('Entry/exit dynamics with forecast fan', 'Proqnoz zolağı ilə giriş/çıxış dinamikası'), ('Region × sector heat map', 'Region × sahə istilik xəritəsi'),
 ('Concentration bounds chart', 'Konsentrasiya hədləri qrafiki'), ('Scenario simulator with assumptions panel', 'Fərziyyələr paneli olan ssenari simulyatoru'), ('Early-warning list', 'Erkən xəbərdarlıq siyahısı'),
 ('Firm-level market structure view (Layer B)', 'Müəssisə səviyyəsində bazar strukturu görünüşü (B qatı)'),
 ('KPI cards per activity group: entry, exit, churn, net entry, PCM proxy, HHI bounds, early-warning score', 'Fəaliyyət qrupları üzrə KPI kartları: giriş, çıxış, dövriyyə, xalis giriş, PCM proksisi, HHI hədləri, erkən xəbərdarlıq balı'),
 ('history 2019-2025 and 2026-2030 under three FR1 scenarios with 5-95% bands; stock of active units', 'tarix 2019–2025 və FR1-in üç ssenarisi üzrə 2026–2030, 5–95% zolaqlarla; fəal vahidlərin ehtiyatı'),
 ('entry and exit rates by region (2021-2025) and by NACE section; forecasts by region', 'regionlar (2021–2025) və NACE bölmələri üzrə giriş və çıxış əmsalları; regionlar üzrə proqnozlar'),
 ('range bars [lower, upper] for HHI and CR4 by group; projected bounds 2026-2030', 'qruplar üzrə HHI və CR4 üçün [aşağı, yuxarı] interval sütunları; 2026–2030 proqnoz hədləri'),
 ('Cournot toolkit: entry, merger, cost/tax, import, SOE scenarios; Δprice, Δmarkup, Δoutput, ΔCS, ΔPS with elasticity ranges', 'Kurno aləti: giriş, birləşmə, xərc/vergi, idxal, dövlət müəssisəsi ssenariləri; elastiklik intervalları ilə Δqiymət, Δmarja, Δburaxılış, ΔİR, ΔİstR'),
 ('flags per sector, composite score, watch list, insufficient-data markers', 'sahələr üzrə bayraqlar, ümumi bal, müşahidə siyahısı, "məlumat kifayət deyil" işarələri'),
 ('HHI, CR4/CR8, entropy, Gini, share mobility, survival curves, Boone by NACE × region; SYNTHETIC watermark until the register arrives', 'NACE × region üzrə HHI, CR4/CR8, entropiya, Cini, pay mobilliyi, sağ qalma əyriləri, Boone; reyestr gələnə qədər SİNTETİK su nişanı'),
 ('registered / new / deregistered, 11 groups, 2019-2020', 'qeydiyyatda / yeni / qeydiyyatdan çıxan, 11 qrup, 2019–2020'), ('registered / new / deregistered, 11 groups, 2022-2023', 'qeydiyyatda / yeni / qeydiyyatdan çıxan, 11 qrup, 2022–2023'),
 ('SME share of output by activity', 'fəaliyyət növləri üzrə KOS-un buraxılışda payı'), ('SME share of employees by activity', 'fəaliyyət növləri üzrə KOS-un işçi sayında payı'), ('active SMEs by size', 'ölçü üzrə fəal KOS'),
 ('active SMEs established one year ago', 'bir il əvvəl yaradılmış fəal KOS'), ('medium business entities by region', 'regionlar üzrə orta sahibkarlıq subyektləri'), ('small business entities by region', 'regionlar üzrə kiçik sahibkarlıq subyektləri'),
 ('micro business entities by region', 'regionlar üzrə mikro sahibkarlıq subyektləri'), ('individual entrepreneurs by activity', 'fəaliyyət növləri üzrə fərdi sahibkarlar'), ('individual entrepreneurs by region', 'regionlar üzrə fərdi sahibkarlar'),
 ('individual entrepreneurs by sex and activity', 'cins və fəaliyyət növü üzrə fərdi sahibkarlar'), ('individual entrepreneurs by sex and region', 'cins və region üzrə fərdi sahibkarlar'),
 ('G1 revenue-cost elasticity (records, section x year x size FE)', 'G1 gəlir–xərc elastikliyi (qeydlər, bölmə × il × ölçü sabit effektləri)'), ('G2 exit hazard (conditional Poisson, cell-year strata)', 'G2 çıxış təhlükəsi (şərti Puasson, xana-il təbəqələri)'),
 ('(b) cloglog, additive section/region/year FE', '(b) cloglog, additiv bölmə/region/il sabit effektləri'), ('(b) logit, additive section/region/year FE', '(b) logit, additiv bölmə/region/il sabit effektləri'),
 ('IRR', 'insident nisbəti (IRR)'), ('OR', 'şans nisbəti (OR)'), ('HR', 'təhlükə nisbəti (HR)'), ('coef', 'əmsal'), ('observed', 'müşahidə'), ('coefficient', 'əmsal'), ('forecast_2030', '2030 proqnozu'), ('note', 'qeyd'),
]})
for g in GRP: AZ[GROUPS[g][0]] = GROUP_AZ[g]
for s in SECS: AZ[SECT[s][0]] = SECT_AZ[s]
FLAG_AZ = {'conc': 'konsentrasiya', 'entry': 'giriş', 'exit': 'çıxış', 'mob': 'mobillik', 'margin_entry': 'marja və giriş'}
TOK = [('null (FE + fixed terms)', 'sıfır model (FE + sabit hədlər)'), ('structural: ', 'struktur: '), ('combination: ', 'kombinasiya: '), (' | anchored', ' | ankerlənmiş')]
SWAP_TOK = sorted([('files, e.g.', 'fayl, məsələn'), ('econometrics:', 'ekonometrika:'), ('coefficients = SYNTHETIC run', 'əmsal = SİNTETİK icra ilə eyni'), ('no watermark', 'su nişanı yoxdur'),
                   ('no recovery block', 'bərpa bloku yoxdur'), ('rows, unknown columns', 'sətir, naməlum sütunlar'), ('mode', 'rejim'), ('file', 'fayl'), ('with BUSREG_PATH set in the environment', '(BUSREG_PATH mühitdə təyin edilib)'),
                   ('loaded', 'yükləndi'), ('engine + DSK comparison', 'mühərrik + DSK müqayisəsi'), ('cells) ran', 'xana) icra olundu'), ('max abs diff', 'maks. mütləq fərq'), (' over ', ' — '), ('cells', 'xana'),
                   ('required column missing (EN or AZ header)', 'məcburi sütun yoxdur (EN və ya AZ başlıq)'), ('business register rejected', 'biznes reyestri rədd edildi'), ('hard errors (first: row', 'ciddi səhv (birinci: sətir'),
                   ('field', 'sahə'), ('negative value', 'mənfi dəyər'), ('see ', 'bax: '), ('generator wrote', 'generator yazdı'), ('real-named files in data/business_register', 'data/business_register-də real adlı fayllar'),
                   ('none', 'yoxdur'), ('warnings', 'xəbərdarlıq'), ('models', 'model'), ('rows', 'sətir')], key=lambda t: -len(t[0]))
def to_az(v, col=''):
    v = str(v)
    if v in AZ: return AZ[v], 'lüğət'
    if re.match(r'^(null \(FE|structural: |combination: |FE \+ )', v):
        o = v
        for a, b in TOK: o = o.replace(a, b)
        return o, 'qayda (spesifikasiya adı)'
    m = re.match(r'births 2026 ([+-][\d.]+%) vs (\d+) and stock ([+-][\d.]+%): the stock grows faster than births, so the rate falls(?:; (\d+) births were ([+-]\d+%) vs the two earlier observations)?$', v)
    if m:
        o = f'2026-cı ildə doğulmalar {m.group(2)}-ə nisbətən {m.group(1)}, ehtiyat {m.group(3)}: ehtiyat doğulmalardan sürətlə artır, ona görə əmsal düşür'
        return o + (f'; {m.group(4)}-cü ilin doğulmaları əvvəlki iki müşahidəyə nisbətən {m.group(5)} idi' if m.group(4) else ''), 'qayda (izah)'
    if col == 'flags' and all(t.strip() in FLAG_AZ for t in v.split(',')): return ', '.join(FLAG_AZ[t.strip()] for t in v.split(',')), 'qayda (bayraqlar)'
    if col == 'detail':
        o = v
        for a, b in SWAP_TOK: o = o.replace(a, b)
        return o, 'qayda (test təfərrüatı)'
    return None, ''

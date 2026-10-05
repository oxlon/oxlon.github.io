# %% [markdown]
# ## Hissə 4 — Məlumatların toplanması, o cümlədən DSK-nın arxivləşdirilmiş buraxılışları
#
# DSK-nın sahibkarlıq cədvəlləri yalnız **son iki ili** (2023–2024), statistik reyestr (`st_units`) isə yalnız **son dövrü**
# (1 iyul 2026, yanvar–iyun axınları) dərc edir. Proqnoz modeli üçün zaman ölçüsü lazımdır, buna görə FR12 **eyni DSK
# fayllarının əvvəlki buraxılışlarını** İnternet Arxivindən (`web.archive.org`, ilkin baytları qaytaran `id_` forması)
# bərpa edir. Hər buraxılışın həqiqi Excel faylı olduğu yoxlanılır, bir dəfə `data/dsk_competition/vintages/` qovluğunda
# saxlanılır və sonra diskdən yenidən oxunur. Manifest (`output/FR12_dsk_manifest.csv`) hər fayl üzrə tam mənbə ünvanını
# (arxiv anlıq görüntüsü və ya DSK ünvanı), yerli yolu və onun SHA-256 yoxlama cəmini qeydə alır. Bu, qiymətləndirmə deyil,
# sənədləşdirilmiş, təkrarlana bilən mənbədir (DSK-nın anlıq görüntü tarixində dərc olunduğu kimi öz faylları). Bərpa
# olunmuş əhatə:
#
# - sahibkarlıq `006` (qeydiyyatdan keçmiş, yeni qeydiyyata alınmış, qeydiyyatdan çıxarılmış sahibkarlıq subyektləri, 11
#   fəaliyyət qrupu): 2019–2020 (aprel 2022 buraxılışı), 2022–2023 (aprel 2025 buraxılışı), 2023–2024 (cari) → **2019,
#   2020, 2022, 2023, 2024**;
# - sahibkarlıq `012`/`013` (fəaliyyət növləri üzrə buraxılışda / işçilərdə KOB-ların payı) və `002` (ölçü üzrə fəal
#   KOB-lar): eyni üç buraxılış;
# - statistik reyestr `2_1` (NACE bölmələri üzrə yeni yaradılmış və ləğv edilmiş vahidlər) və `2_3` (regionlar üzrə):
#   2021-ci il tam il (mart 2022 buraxılışı), 2024 (aprel 2025), 2025 (fevral 2026), habelə 2022, 2024, 2025, 2026-cı
#   illərin yanvar–iyun dövrləri.
#
# 2022 və 2023-cü illərin tam il reyestr axınlarının heç bir buraxılışı arxivləşdirilməyib; bu boşluq doldurulmur, qeydə
# alınır. FR10-un istifadə etmədiyi cari DSK faylları (regionlar üzrə ölçü qrupları `1_4_k/o/m`, fərdi sahibkarlar
# `1_5`–`1_8`) `Mozilla/5.0` User-Agent-i ilə birbaşa `stat.gov.az` saytından yüklənir.

# %%
XLS_MAGIC = bytes.fromhex('d0cf11e0a1b11ae1')
WB_URL = 'https://web.archive.org/web/{ts}id_/http://www.stat.gov.az/source/{path}'
DSK_URL = 'https://www.stat.gov.az/source/{path}'
VINT = [  # local name, archive timestamp, DSK path, content / period covered
 ('e006_v2022.xls', '20220403145449', 'entrepreneurship/en/006en.xls', 'registered / new / deregistered, 11 groups, 2019-2020'),
 ('e006_v2025.xls', '20250421050555', 'entrepreneurship/en/006en.xls', 'registered / new / deregistered, 11 groups, 2022-2023'),
 ('e012_v2022.xls', '20220403145405', 'entrepreneurship/en/012en.xls', 'SME share of output by activity'),
 ('e012_v2025.xls', '20250421045614', 'entrepreneurship/en/012en.xls', 'SME share of output by activity'),
 ('e013_v2022.xls', '20220403145451', 'entrepreneurship/en/013en.xls', 'SME share of employees by activity'),
 ('e013_v2025.xls', '20250421050729', 'entrepreneurship/en/013en.xls', 'SME share of employees by activity'),
 ('e002_v2022.xls', '20220403145508', 'entrepreneurship/en/002en.xls', 'active SMEs by size'),
 ('e002_v2025.xls', '20250421045707', 'entrepreneurship/en/002en.xls', 'active SMEs by size'),
 ('e024_v2022.xls', '20220403145523', 'entrepreneurship/en/024en.xls', 'active SMEs established one year ago'),
 ('e024_v2025.xls', '20250421045635', 'entrepreneurship/en/024en.xls', 'active SMEs established one year ago'),
 ('s21_FY2021_az.xls', '20220307165205', 'st_units/az/2_1_az.xls', 'new / liquidated units by section, full year 2021'),
 ('s21_H1_2022_en.xls', '20220818184803', 'st_units/en/2_1en.xls', 'new / liquidated units by section, Jan-Jun 2022'),
 ('s21_H1_2024_az.xls', '20240927033915', 'st_units/az/2_1_az.xls', 'new / liquidated units by section, Jan-Jun 2024'),
 ('s21_FY2024_en.xls', '20250416142637', 'st_units/en/2_1en.xls', 'new / liquidated units by section, full year 2024'),
 ('s21_H1_2025_az.xls', '20250712215241', 'st_units/az/2_1_az.xls', 'new / liquidated units by section, Jan-Jun 2025'),
 ('s21_FY2025_az.xls', '20260213212129', 'st_units/az/2_1_az.xls', 'new / liquidated units by section, full year 2025'),
 ('s23_FY2021_az.xls', '20220307165212', 'st_units/az/2_3_az.xls', 'new / liquidated units by region, full year 2021'),
 ('s23_FY2024_en.xls', '20250416142923', 'st_units/en/2_3en.xls', 'new / liquidated units by region, full year 2024'),
 ('s23_FY2025_az.xls', '20260213212343', 'st_units/az/2_3_az.xls', 'new / liquidated units by region, full year 2025')]
CURR = [(f'{f}', f'st_units/en/{f}', t) for f, t in [
 ('1_4_o_en.xls', 'medium business entities by region'), ('1_4_k_en.xls', 'small business entities by region'),
 ('1_4_m_en.xls', 'micro business entities by region'), ('1_5_en.xls', 'individual entrepreneurs by activity'),
 ('1_6_en.xls', 'individual entrepreneurs by region'), ('1_7_en.xls', 'individual entrepreneurs by sex and activity'),
 ('1_8_en.xls', 'individual entrepreneurs by sex and region')]]

def _get(url, dest):
    if dest.exists() and dest.read_bytes()[:8] == XLS_MAGIC: return 'present'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=90) as r: blob = r.read()
            if blob[:8] == XLS_MAGIC:
                dest.write_bytes(blob); return 'downloaded'
            return 'NOT AN EXCEL FILE (HTML reply)'
        except Exception as e:
            err = str(e)[:80]
    return f'FAILED: {err}'

(CDIR / 'vintages').mkdir(exist_ok=True); (CDIR / 'current').mkdir(exist_ok=True)
import hashlib
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
man = []
for nm, ts, path, what in VINT:
    url = WB_URL.format(ts=ts, path=path); st = _get(url, CDIR / 'vintages' / nm)
    man.append(('archived vintage', nm, url, what, st, f'data/dsk_competition/vintages/{nm}'))
for nm, path, what in CURR:
    url = DSK_URL.format(path=path); st = _get(url, CDIR / 'current' / nm)
    man.append(('DSK current', nm, url, what, st, f'data/dsk_competition/current/{nm}'))
for sec, web in [('st_units', 'st_units'), ('entrepreneurship', 'entrepreneurship'), ('nat_accounts', 'system_nat_accounts'), ('industry', 'industry')]:
    for p in sorted((DDIR / sec).glob('*.xls')):
        man.append(('FR10 download (read only)', p.name, DSK_URL.format(path=f'{web}/en/{p.name}'), 'shared with FR10', 'present', f'data/dsk_enterprise/{sec}/{p.name}'))
MANIFEST = pd.DataFrame(man, columns=['origin', 'file', 'source_url', 'content', 'status', 'local_path'])
MANIFEST['sha256'] = [sha(BASE / lp) if (BASE / lp).exists() else '' for lp in MANIFEST.local_path]
MANIFEST['bytes'] = [(BASE / lp).stat().st_size if (BASE / lp).exists() else 0 for lp in MANIFEST.local_path]
display(MANIFEST.groupby(['origin', 'status']).size().rename('files').reset_index())
bad = MANIFEST[~MANIFEST.status.isin(['present', 'downloaded'])]
assert bad.empty, f'inputs could not be obtained: {bad.file.tolist()}'
MANIFEST.to_csv(OUT / 'FR12_dsk_manifest.csv', index=False)
VD = CDIR / 'vintages'; CD = CDIR / 'current'
print(f'{len(MANIFEST)} input files available ({(MANIFEST.origin == "archived vintage").sum()} archived DSK vintages)')

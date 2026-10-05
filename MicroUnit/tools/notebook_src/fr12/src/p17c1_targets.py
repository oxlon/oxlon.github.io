# %% [markdown]
# ### 17.3 SİNTETİK reyestr: kalibrləmə hədəfləri
#
# Başlanğıc dəyəri sabitlənmiş (`SEED + 17`), bütün NACE bölmələri (A–S, U), 14 region, 2019–2025. Hədəflər **DSK-nın dərc
# etdiyi yerlərdə dəqiqdir**:
#
# | Hədəf | Mənbə | Dəqiq olan illər | Əks halda |
# |---|---|---|---|
# | NACE bölmələri üzrə doğumlar və ölümlər | reyestr `2_1` (arxivləşdirilmiş buraxılışlar) | 2021, 2024, 2025 | 2022–2023: regional yekunlar × orta bölmə tərkibi; 2019–2020: 006 qeydiyyatları üzrə miqyaslanır |
# | regionlar üzrə doğumlar və ölümlər | iş kitabı `Regionlar*` = reyestr `2_3` | 2021–2025 | 2019–2020: 2021-ci ilin regional tərkibi |
# | 2025-ci ilin sonuna bölmələr və regionlar üzrə fəaliyyət göstərən vahidlər | `2_1`, `Regionlar*` | 2025 | əvvəlki ehtiyatlar doğumlardan və ölümlərdən irəli gəlir (ehtiyat-axın eyniliyi, F5) |
# | bölmələr üzrə gəlir | milli hesablar üzrə buraxılış (013) | 2019–2025 | — |
# | fəaliyyət qrupları üzrə gəlirdə KOB-ların payı (və onun mikro/kiçik/orta bölgüsü) | sahibkarlıq `012` | 2019, 2020, 2022–2024 | 2021 interpolyasiya edilib, 2025 = 2024 |
# | ölçü qrupları üzrə tərkib | reyestr `1_3` (1 iyul 2026) | təxmini | — |
#
# Bölmə × region matrisləri sənədləşdirilmiş ilkin matrisdən (Bakının çəkisi xidmətlərdə yuxarı, kənd təsərrüfatında
# aşağı əyilib) iterativ proporsional uyğunlaşdırma (IPF) ilə qurulur və **hər iki marjinalı dəqiq saxlamaqla** tam
# ədədlərə yuvarlaqlaşdırılır.

# %%
rng_s = np.random.default_rng(SEED + 17)
SY = list(range(2019, LAST_ACT + 1))
def lr_round(x, total):
    x = np.asarray(x, float); f = np.floor(x); k = int(round(total - f.sum()))
    f[np.argsort(-(x - f))[:k]] += 1; return f.astype(int)
def ipf_int(seed, rows, cols, it=500):
    M = seed.astype(float).copy()
    for _ in range(it):
        M *= (rows / np.maximum(M.sum(1), 1e-12))[:, None]; M *= (cols / np.maximum(M.sum(0), 1e-12))[None, :]
    F = np.floor(M).astype(int); rr = rows - F.sum(1); cc = cols - F.sum(0); fr = M - F
    for idx in np.argsort(-fr, axis=None):
        i, j = divmod(int(idx), M.shape[1])
        if rr[i] > 0 and cc[j] > 0: F[i, j] += 1; rr[i] -= 1; cc[j] -= 1
    while rr.sum() > 0:
        i = int(np.argmax(rr > 0)); j = int(np.argmax(cc > 0)); F[i, j] += 1; rr[i] -= 1; cc[j] -= 1
    assert (F.sum(1) == rows).all() and (F.sum(0) == cols).all(); return F
TILT = dict(A=.15, B=.8, C=.8, D=.8, E=.8, F=.9, G=1., H=1., I=.9, J=1.4, K=1.4, L=1.3, M=1.3, N=1.2, O=.5, P=.8, Q=.8, R=.9, S=1.1, U=2.)
_rs = RG[RG.year == LAST_ACT].set_index('region').enterprises.reindex(REGS).to_numpy(float)
SEEDM = np.array([[_rs[j] * (TILT[s] if REGS[j] == 'Baku city' else 1.0) for j in range(len(REGS))] for s in SECS])
rg = RG.set_index(['region', 'year'])
def sec_vec(var, y):
    if y in (2021, 2024, 2025): return REG_FY[var][y].reindex(SECS).to_numpy(float), 'exact'
    mix = (REG_FY[var][2021] + REG_FY[var][2024]).reindex(SECS).to_numpy(float); mix = mix / mix.sum()
    if y in (2022, 2023): tot = sum(rg.loc[(r, y), 'new' if var == 'new' else 'liquidated'] for r in REGS)
    else:
        e = E006.xs('TOT', level=0)
        tot = sum(rg.loc[(r, 2022), 'new'] for r in REGS) * e.loc[y, 'new'] / e.loc[2022, 'new'] if var == 'new' else \
              sum(rg.loc[(r, 2021), 'liquidated'] for r in REGS)
    return mix * tot, 'approximate'
def reg_vec(var, y):
    col = 'new' if var == 'new' else 'liquidated'
    if y >= 2021: return np.array([rg.loc[(r, y), col] for r in REGS], float), 'exact'
    v = np.array([rg.loc[(r, 2021), col] for r in REGS], float); return v, 'approximate'
TGT = {}
for y in SY:
    for var in ['new', 'liq']:
        sv, sq = sec_vec(var, y); rv, rq = reg_vec(var, y)
        tot = int(round(rv.sum())) if rq == 'exact' else int(round(sv.sum()))
        sv = lr_round(sv / sv.sum() * tot, tot) if sq != 'exact' else sv.astype(int)
        rv = lr_round(rv / rv.sum() * tot, tot) if rq != 'exact' else rv.astype(int)
        assert sv.sum() == rv.sum(), (y, var, sv.sum(), rv.sum())
        TGT[(var, y)] = dict(M=ipf_int(SEEDM, sv, rv), sec_q=sq, reg_q=rq)
S25 = ipf_int(SEEDM, REG_FY['stock'][LAST_ACT].reindex(SECS).to_numpy(int), np.array([rg.loc[(r, LAST_ACT), 'enterprises'] for r in REGS], int))
N18 = S25 - sum(TGT[('new', y)]['M'] - TGT[('liq', y)]['M'] for y in SY)
_neg = int((N18 < 0).sum())
if _neg:            # a cell whose later births exceed its end-2025 stock: births reassigned within the section to its largest region
    for i, j in zip(*np.where(N18 < 0)):
        need = -N18[i, j]; N18[i, j] = 0; jj = int(np.argmax(N18[i])); N18[i, jj] -= need
assert (N18 >= 0).all()
print(f'targets: births/deaths section x region for {len(SY)} years (exact: sections 2021, 2024, 2025; regions 2021-2025); '
      f'end-2025 stock {S25.sum():,}; implied start-2019 stock {N18.sum():,} ({_neg} negative cells re-balanced within their section)')

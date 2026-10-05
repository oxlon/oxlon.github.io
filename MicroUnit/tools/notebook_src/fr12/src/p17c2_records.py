# %%
# enterprise records: start-2019 stock, births and deaths per section x region cell, exactly as targeted.
# A record may stand for several identical enterprises (column `weight`): micro units in groups of up to 40, small
# units in groups of up to 5, medium and large units one by one. This keeps the file small; a real register has weight 1.
KW = {'micro': 40, 'small': 5, 'medium': 1, 'large': 1}
HAZ = {'micro': 1.0, 'small': 0.4, 'medium': 0.2, 'large': 0.08}
YOUNG_HAZ_MULT, YOUNG_HAZ_AGE = 2.0, 3          # exit-selection score doubled below age 3 (true parameter, recovered in 17.7 (g))
_ps = SIZE[['micro', 'small', 'medium', 'large']].astype(float)
_nat = _ps.sum() / _ps.sum().sum()
P_SIZE = {s: ((_ps.loc[s] / _ps.loc[s].sum()) if (s in _ps.index and _ps.loc[s].sum() > 0) else _nat).to_numpy(float) for s in SECS}
BIRTH_TILT = np.array([1.0, 0.3, 0.1, 0.03])
def split_records(n, size):
    if n <= 0: return []
    m = int(np.ceil(n / KW[size])); base = n // m
    return [base + (1 if k < n % m else 0) for k in range(m)]
REC = []      # columns: sec, region, size, weight, reg_year, liq_year
P_INIT = {}
for i, s in enumerate(SECS):      # start-2019 size mix chosen so that the expected end-2025 mix matches 1_3
    pb = P_SIZE[s] * BIRTH_TILT; pb = pb / pb.sum()
    Bs = sum(TGT[('new', y)]['M'][i].sum() for y in SY)
    p0 = np.clip(S25[i].sum() * P_SIZE[s] - Bs * pb, 0, None)
    P_INIT[s] = p0 / p0.sum() if p0.sum() > 0 else P_SIZE[s]
for i, s in enumerate(SECS):
    pb = P_SIZE[s] * BIRTH_TILT; pb = pb / pb.sum()
    for j, r in enumerate(REGS):
        cell = []
        n0 = rng_s.multinomial(int(N18[i, j]), P_INIT[s])
        yrs0 = np.arange(1995, 2019); pw = 1.08 ** (yrs0 - 1995); pw = pw / pw.sum()
        for k, sz in enumerate(SIZES):
            for w in split_records(int(n0[k]), sz): cell.append([sz, w, int(rng_s.choice(yrs0, p=pw)), 0])
        for y in SY:
            nb = rng_s.multinomial(int(TGT[('new', y)]['M'][i, j]), pb)
            for k, sz in enumerate(SIZES):
                for w in split_records(int(nb[k]), sz): cell.append([sz, w, y, 0])
            d = int(TGT[('liq', y)]['M'][i, j])
            if d <= 0: continue
            alive = [q for q, c in enumerate(cell) if c[3] == 0 and c[2] < y]
            if sum(cell[q][1] for q in alive) < d: alive = [q for q, c in enumerate(cell) if c[3] == 0 and c[2] <= y]
            pr = np.array([HAZ[cell[q][0]] * cell[q][1] * (YOUNG_HAZ_MULT if y - cell[q][2] < YOUNG_HAZ_AGE else 1.0) for q in alive])
            key = rng_s.random(len(alive)) ** (1.0 / pr)
            for q in [alive[t] for t in np.argsort(-key)]:
                if d <= 0: break
                w = cell[q][1]
                if w <= d: cell[q][3] = y; d -= w
                else: cell[q][1] = w - d; cell.append([cell[q][0], d, cell[q][2], y]); d = 0
            assert d == 0, f'cell {s}/{r} {y}: deaths exceed living units'
        REC += [[s, r] + c for c in cell]
REC = pd.DataFrame(REC, columns=['sec', 'region', 'size_class', 'weight', 'reg_year', 'liq_year'])
REC['firm_id'] = [f'SYN-{s}{k:07d}' for k, s in enumerate(REC.sec)]
print(f'{len(REC):,} synthetic enterprise records standing for {REC.weight.sum():,} enterprises '
      f'({(REC.weight > 1).sum():,} grouped micro/small records)')

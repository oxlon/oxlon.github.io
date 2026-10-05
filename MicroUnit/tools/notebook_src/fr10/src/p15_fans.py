# %% [markdown]
# ## Hissə 15 — Proqnozun qeyri-müəyyənliyi: 5–95% zolaqları
#
# FR1-in Əsas ssenari üzrə 500 təkrarlamasının (`FR1_fan_draws.csv`) hər biri hər makro sürücünün bir trayektoriyasını
# verir. $r$ təkrarlaması üçün FR10 aşağıdakıları əlavə edir:
#
# 1. **Modelin tarixi xəta trayektoriyaları** — başlanğıc ili $s$ çəkilir və **model qalıqlarının** birgə vektoru
#    $e_h = u_{s+h} - u_s$ bütün pay tənliklərinə eyni anda tətbiq olunur (sahə bölüşdürməsi: $u = \ln s - \beta \ln(R/Y)$;
#    regionlar: $u = $ log-şans çıxılsın sürücü termininin qiymətləndirilmiş dəyəri). Heç bir avtokorrelyasiya
#    qiymətləndirilmir. 2018/2019 əhatə qırılmasını (F9) kəsən regional trayektoriyalar xaric edilir. Trayektoriyalar
#    mərkəzləşdirilir.
# 2. **İşarəyə görə rədd etməklə parametr çəkilişləri** — birləşdirilmiş elastiklik və regional meyllər (aposterior)
#    normal paylanmalarından çəkilir; nöqtəvi qiymətləndirmənin işarəsini dəyişən çəkilişlər rədd edilir və yenidən çəkilir.
# 3. **Məşğulluq** — FR4-ün indeksi təkrarlamanın ümumi məşğulluğunun FR1-in Əsas ssenarisinə nisbəti ilə miqyaslanır.
#
# Bütün təkrarlamalar ssenarilərlə eyni `core` funksiyasından bir vektorlaşdırılmış çağırışla keçir. Bir variantda FR1-in
# **qiymətləri** (sektor deflyatorları və neft qiyməti) Əsas ssenari trayektoriyalarında saxlanılır ki, sənaye və elektrik
# enerjisi zolaqlarının uclarının nə qədərinin FR1-in neft və elektrik enerjisi qiymətləri çəkilişlərindən qaynaqlandığı
# görünsün.

# %%
QTL = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
rng_f = np.random.default_rng(SEED + 15)
def centred_paths(U, starts):
    P = np.stack([U.loc[s + 1:s + H].values - U.loc[s].values for s in starts])
    return P - P.mean(axis=0)
POOLS = {}
for g, u in GROUP.items():
    U = np.log(SHH[g][u]).loc[EST0:LAST_ACT] - BETA * RH[g][u].loc[EST0:LAST_ACT]
    st = [s for s in U.index if s + H <= LAST_ACT]
    POOLS[g] = (centred_paths(U, st), st)
_pr = PAR['R']; _xs = SPEC_X.get(_pr['spec'], [])
UR = pd.DataFrame({k: SYS_R.LO[k] - ((SYS_R.X[_xs] * _pr[k]['b']).sum(axis=1) if _xs else 0) for k in REG_NAMES}).loc[EST0:LAST_ACT]
st = [s for s in UR.index if s + H <= LAST_ACT and not (s < 2019 <= s + H)]
POOLS['R'] = (centred_paths(UR, st), st)
print('historical model-error paths: ' + '; '.join(f'{g} {len(v[1])} start years ({v[1][0]}-{v[1][-1]})' for g, v in POOLS.items()))

fcs = F1D.set_index(['draw', 'year']).sort_index()
D = drv_arrays(fcs)
ok = np.ones(D['rva_man'].shape[0], bool)
for k_, a in D.items():
    a_ = a[:, 1:] if k_ == 'emp' else a
    ok &= np.isfinite(a_).all(1) & (a_ > 0).all(1)
D = {k_: a[ok] for k_, a in D.items()}
R_N = int(ok.sum())
f1b_emp = F1F[F1F.scenario == 'Baseline'].set_index('year').loc[FC_YEARS, 'emp'].to_numpy(float)
emp_ratio = np.column_stack([np.ones(R_N), D['emp'][:, 1:] / f1b_emp])
ZS = {}
for g, (P, st_) in POOLS.items():
    ZS[g] = np.concatenate([np.zeros((R_N, 1, P.shape[2])), P[rng_f.integers(0, len(st_), R_N)]], axis=1)
def draw_signed(mu, sd, size):
    x = mu + sd * rng_f.standard_normal(size); n_rej = 0
    for _ in range(100):
        bad = np.sign(x) != np.sign(mu) if np.ndim(mu) == 0 else (np.sign(x) != np.sign(mu)) & (mu != 0)
        if not bad.any(): break
        n_rej += int(bad.sum()); x = np.where(bad, mu + sd * rng_f.standard_normal(size), x)
    return x, n_rej
BETA_DRAWS, REJ_B = draw_signed(BETA, BETA_SE, R_N)
REGB, REJ_R = None, 0
if _xs:
    b0 = np.array([[_pr[k]['b'][x] for x in _xs] for k in REG_NAMES]); s0 = np.nan_to_num(np.array([[_pr[k]['se'][x] for x in _xs] for k in REG_NAMES]))
    REGB, REJ_R = draw_signed(b0[None], s0[None], (R_N,) + b0.shape)
emp_b = fr4_index('Baseline')
SIM = core(D, emp_b, emp_ratio=emp_ratio, zsh=ZS, beta=BETA_DRAWS, regb=REGB)
DP = dict(D); bsa = scen_arrays('Baseline')
for v in ['p_min', 'p_man', 'p_elc', 'p_wat', 'oil_exp_price']: DP[v] = np.repeat(bsa[v], R_N, axis=0)
for s_, v in SECV.items(): DP[f'va_{v}_n'] = DP[f'rva_{v}'] * DP[f'p_{v}']
SIM_P = core(DP, emp_b, emp_ratio=emp_ratio, zsh=ZS, beta=BETA_DRAWS, regb=REGB)
_chk = core({k_: np.repeat(v_, 2, axis=0) for k_, v_ in bsa.items()}, emp_b)
VEC_CHECK = float(np.abs(_chk['nom'][1] / B_['nom'].to_numpy(float) - 1).max())
print(f'{R_N} of {len(ok)} FR1 draws usable; one vectorised pass; batch vs single-path solver difference {VEC_CHECK:.1e}; '
      f'sign rejections: pooled elasticity {REJ_B}, regional slopes {REJ_R}; remainder floor binding in {SIM["rem_clipped"]} replication-years')
assert VEC_CHECK < 1e-12

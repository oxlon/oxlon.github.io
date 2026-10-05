# %% [markdown]
# ## Hissə 12 — Kəsimdən əvvəl seçim, toxunulmaz nümunədən kənar yoxlama, hər iki müqayisə meyarı (NFR1)
#
# **Qayda** prosedurdur — (sürücülər dəsti, lövbərləmə, rejim) üstəgəl uyğunluq filtri — və hər başlanğıcda həmin
# başlanğıcadək olan məlumatlar üzrə yenidən tətbiq olunur. Nümunədən kənar yoxlama və proqnoz **eyni prosedurdan**
# (eyni lövbərləmə, eyni ehtiyat variantı) istifadə edir; beləliklə, proqnoz məhz yoxlanılmış qaydadır.
#
# - **Seçim** (yalnız ≤ 2022 məlumatlar): ≤ 2022 illər üzrə qiymətləndirilir, 2023 üzrə qiymətləndirmə aparılır.
#   Namizədlər: hər sürücülər dəsti, lövbərlənməmiş (sabit effektli səviyyə) və ya **sonuncu qalığa lövbərlənmiş**
#   (FR1–FR10-un düzəliş əmsalı qaydası). Ən yaxşı namizəd itkisi daha aşağı olduqda və vahidlər üzrə cütləşdirilmiş test
#   bərabər dəqiqliyi 10% səviyyəsində rədd etdikdə sıfır variantı əvəz edir; itkisi aşağı, lakin əhəmiyyətsiz olduqda
#   proqnoz sıfır variantı ilə bərabər çəkili **kombinasiyadır**; əks halda sıfır variantıdır. Cədvəl hər qaydanın
#   **sonuncu müşahidəyə nəzərdə tutulan çəkisini** (təsadüfi gəzişmə çəkisi) verir: lövbərlənmiş qayda üçün 1,
#   lövbərlənmiş model və sıfır variantının kombinasiyası üçün 0,5, lövbərlənməmiş qaydalar üçün 0. Büzülmə: vahid
#   başına ≤ 3 kəsimdən əvvəlki il olduqda identifikasiya edilmir; birləşdirilmiş meyllər (κ = 0), kəsimdən əvvəl
#   sabitlənib.
# - **Uyğunluq qaydası**: within meyli birinci fərq qiymətləndirməsinin 95% etibarlılıq intervalından kənarda olan sürücü
#   atılır. O, yalnız öyrənmə nümunəsində vahid başına ≥ 2 keçid olduqda tətbiq olunur; daha az olduqda (2022 başlanğıcında
#   region paneli: yalnız 2021→2022) mənasızdır və keçilmiş kimi deyil, **tətbiq olunmayıb** kimi göstərilir.
# - **Nümunədən kənar yoxlama** (heç vaxt seçim üçün istifadə olunmur): fəaliyyət — 2022 və 2023 başlanğıcları, hədəf
#   2024; region — 2023 (hədəflər 2024, 2025) və 2024 (hədəf 2025) başlanğıcları. FR1/FR10-un faktiki sürücüləri (FR10-da
#   olduğu kimi şərti proqnozlar); hər sabit hər başlanğıcda yenidən qiymətləndirilir. Giriş proqnozlaşdırılan doğumlardan
#   və çıxış qaydasının proqnozlaşdırılan ölümlərindən eynilik vasitəsilə, başlanğıcdakı ehtiyatdan başlayaraq qurulan
#   **giriş əmsalı** kimi (heç bir faktiki endogen nəticə daxil olmur), habelə log doğumlar kimi qiymətləndirilir. Müqayisə
#   meyarları: təsadüfi gəzişmə (sonuncu müşahidə olunan dəyər) və sabit (öyrənmə illəri üzrə vahidin ortası). DM/HLN:
#   hədəf illəri hədəf illər üzrə test üçün çox azdır (1–2), buna görə test **vahidlər üzrə cütləşdirilir** (itkilər üst-üstə
#   düşən başlanğıclar üzrə vahidə görə orta hesablanır); o, ümumi il şoklarını nəzərə almır və onun p-dəyərləri yalnız
#   istiqamətverici xarakter daşıyır.

# %%
def coherence_filter(tr, dep, spec, fixed):
    if not spec: return [], []
    d = tr.dropna(subset=[dep] + spec).sort_values(['unit', 'year']).copy()
    ntr = d.groupby('unit').size().median() - 1
    if ntr < 2:
        return list(spec), [dict(driver=c, status=f'not applied (vacuous: {int(ntr)} transition per unit)') for c in spec]
    m = fit_fe(d, dep, spec, fixed); fx = [c for c in fixed if c in d and d[c].std() > 0]
    for c in [dep] + spec + fx: d['d_' + c] = d.groupby('unit')[c].diff()
    d = d.dropna(subset=['d_' + dep])
    fx = [c for c in fx if d['d_' + c].std() > 0]
    fd = ols(d['d_' + dep], d[['d_' + c for c in spec + fx]], cov='hc1', add_const=False)
    tq = stats.t.ppf(0.975, fd.dof); keep, rec = [], []
    for j, c in enumerate(spec):
        lo, hi = fd.beta[j] - tq * fd.se[j], fd.beta[j] + tq * fd.se[j]; ok = lo <= m['b'][j] <= hi
        rec.append(dict(driver=c, fe=float(m['b'][j]), fd=float(fd.beta[j]), fd_lo=float(lo), fd_hi=float(hi), status='coherent' if ok else 'dropped (incoherent)', transitions=int(ntr)))
        if ok: keep.append(c)
    return keep, rec

def anchor_shift(m, tr, dep):
    last = m['d'].sort_values('year').groupby('unit').tail(1)
    return pd.Series(last[dep].to_numpy(float) - predict(m, last), index=last.unit.values)

def apply_rule(key, rule, origin, rows, log=None):
    M = MODELS[key]; df, fixed, dep = M['df'], M['fixed'], key[1]
    tr = df[df.year <= origin]
    spec, rec = coherence_filter(tr, dep, rule['spec'], fixed) if rule['mode'] != 'null' else ([], [])
    if log is not None:
        for r in rec: log.append(dict(key=str(key), origin=origin, **r))
    m0 = fit_fe(tr, dep, [], fixed); p0 = predict(m0, rows)
    out = dict(p0=p0, spec=spec, m0=m0, m1=None, shift=None, w_rw=0.0)
    if rule['mode'] == 'null' or not spec:
        out['pred'] = p0; return out
    m1 = fit_fe(tr, dep, spec, fixed); p1 = predict(m1, rows)
    if rule['anchor'] == 'last':
        out['shift'] = anchor_shift(m1, tr, dep); p1 = p1 + rows.unit.map(out['shift']).to_numpy(float)
    wt = 1.0 if rule['mode'] == 'structural' else 0.5
    out.update(m1=m1, p1=p1, wt=wt, pred=wt * p1 + (1 - wt) * p0, w_rw=wt * (rule['anchor'] == 'last'))
    return out

def rname(r): return 'null (FE + fixed terms)' if r['mode'] == 'null' else f"{r['mode']}: {spec_name(r['spec'])}" + (' | anchored' if r['anchor'] == 'last' else '')

SELECT, SELTAB, COHLOG = {}, [], []
def select_rule(key):
    M = MODELS[key]
    df = M['df']; dep = key[1]; o, tg = M['sel']
    rows = df[df.year.isin(tg)].dropna(subset=[dep]); act = rows[dep].to_numpy(float)
    losses = {}
    for s in M['specs']:
        for an in (['fe'] if not s else ['fe', 'last']):
            r = dict(spec=s, anchor=an, mode='null' if not s else 'structural')
            pr = apply_rule(key, r, o, rows, COHLOG)['pred']; losses[(tuple(s), an)] = pd.Series((pr - act) ** 2, index=rows.unit.values)
            SELTAB.append(dict(panel=key[0], dep=dep, candidate=rname(r), sel_mse=float(np.mean((pr - act) ** 2)), n=len(act)))
    null_l = losses[((), 'fe')]
    bk = min([k for k in losses if k[0]], key=lambda k: losses[k].mean())
    _, pv = dm_hln(losses[bk].values, null_l.values, h=1)
    mode = ('structural' if pv <= 0.10 else 'combination') if losses[bk].mean() < null_l.mean() else 'null'
    rule = dict(spec=list(bk[0]) if mode != 'null' else [], anchor=bk[1] if mode != 'null' else 'fe', mode=mode)
    SELECT[key] = dict(rule=rule, best=rname(dict(spec=list(bk[0]), anchor=bk[1], mode='structural')), dm_p=pv,
                       w_rw=(1.0 if mode == 'structural' else 0.5 if mode == 'combination' else 0.0) * (rule['anchor'] == 'last'),
                       train_years=int(df[df.year <= o].year.nunique()))
for key in MODELS: select_rule(key)
def selsum():
    return pd.DataFrame([dict(panel=k[0], dep=k[1], rule=rname(v['rule']), best_candidate=v['best'], dm_p_vs_null=v['dm_p'],
                              implied_rw_weight=v['w_rw'], train_years=v['train_years']) for k, v in SELECT.items()])
display(selsum().round(3))
